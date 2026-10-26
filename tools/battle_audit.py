"""Phase D 战斗系统审计：在 1.4.9 APK(anzbao/jstm.apk) 上做静态还原。

【硬约束】本工具只读 anzbao/jstm.apk（1.4.9, com.shiyue.dldl.ewan.qihoo）。
绝不读取 jstm_142165.apk（1.4.11）—— 该文件被显式列入黑名单，误用会直接报错。

用法：
    python tools/battle_audit.py files                     # 列出命中战斗关键词的 luac
    python tools/battle_audit.py defs  <asset路径>          # 方法名 -> proto 还原
    python tools/battle_audit.py strs  <asset路径> [regex]  # 字符串池
    python tools/battle_audit.py calls <asset路径> [regex]  # 外部调用序列
    python tools/battle_audit.py cmds  <asset路径>          # 该文件的 CMD 注册情况
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APK_149 = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')
BANNED = ('jstm_142165.apk', '142165')

from luajit_bc import ChildRef, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def open_apk():
    z = zipfile.ZipFile(APK_149)
    return z


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def read_asset(entry):
    z = open_apk()
    names = z.namelist()
    if entry not in names:
        key = 'assets/src/' + entry.lstrip('/')
        if key in names:
            entry = key
        else:
            cand = [n for n in names if n.endswith(entry)]
            if len(cand) == 1:
                entry = cand[0]
            else:
                raise SystemExit('!! 条目不存在: %s\n   候选: %s' % (entry, cand[:8]))
    return entry, z.read(entry)


def defs_of(pt):
    """[(name, child_idx, bc_idx, kind)] —— 与 tools/luac_defs.py 同一算法"""
    out = []
    bc = pt.bc
    for i, w in enumerate(bc):
        if op_name(w) != 'FNEW':
            continue
        d = (w >> 16) & 0xffff
        ch = kidx(pt, d)
        if not isinstance(ch, ChildRef):
            continue
        nm = None
        for j in range(i + 1, min(i + 6, len(bc))):
            w2 = bc[j]
            o2 = op_name(w2)
            if o2 == 'TSETS':
                a2 = (w2 >> 8) & 0xff
                c2 = (w2 >> 16) & 0xff
                v = kidx(pt, c2)
                if isinstance(v, str):
                    nm = (v, 'TSETS', a2, (w >> 8) & 0xff)
                break
            if o2 in ('TSETV', 'TSETB'):
                a2 = (w2 >> 8) & 0xff
                c2 = (w2 >> 16) & 0xff
                nm = (repr(kidx(pt, c2)), o2, a2, (w >> 8) & 0xff)
                break
            if o2 in ('FNEW', 'CALL', 'RET0', 'RET1'):
                break
        if nm:
            out.append((nm[0], ch.index, i, '%s(a=%d,fnew_a=%d)' % (nm[1], nm[2], nm[3])))
    return out


def calls_of(pt):
    """外部调用序列：GGET/GSET/TGETS/TGETV + CALL/MCALL 附近的名字"""
    out = []
    bc = pt.bc
    for i, w in enumerate(bc):
        op = op_name(w)
        if op in ('GGET', 'GSET'):
            c = (w >> 16) & 0xffff
            v = kidx(pt, c)
            if isinstance(v, str):
                out.append(('G', v, i))
        elif op in ('TGETS',):
            c = (w >> 16) & 0xff
            v = kidx(pt, c)
            if isinstance(v, str):
                out.append(('S', v, i))
        elif op in ('TGETV', 'TGETB'):
            c = (w >> 16) & 0xff
            v = kidx(pt, c)
            out.append(('V', repr(v), i))
    return out


def cmd_of(asset, data):
    """提取文件里出现的 CMD 数字（字符串常量 + 数字常量）"""
    r = parse_bytes(data)
    nums = set()
    strs = set()
    for pt in r.protos:
        for s in pt.strings:
            strs.add(s)
            if re.fullmatch(r'\d{4,5}', s):
                nums.add(int(s))
        for k in pt.knum:
            if isinstance(k, float) and k.is_integer() and 10000 <= k <= 40000:
                nums.add(int(k))
    return sorted(nums), strs


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    mode = sys.argv[1]

    if mode == 'files':
        z = open_apk()
        pat = re.compile(r'(?i)battle|fight|combat|skill|damage|hurt|dead|die|revive|drop|loot|inventory|bag|mon|attack|buff|effect')
        for n in sorted(z.namelist()):
            if n.endswith('.luac') and pat.search(n):
                print('%-78s %d' % (n, z.getinfo(n).file_size))
        return

    entry_arg = sys.argv[2]
    if any(b in entry_arg for b in BANNED):
        raise SystemExit('!! 拒绝对 1.4.11 包操作: %s' % entry_arg)
    entry, data = read_asset(entry_arg)
    r = parse_bytes(data)
    print('=== %s  (%d bytes, %d protos) ===' % (entry, len(data), len(r.protos)))

    if mode == 'defs':
        want = sys.argv[3] if len(sys.argv) > 3 else None
        total = 0
        for i, pt in enumerate(r.protos):
            ms = defs_of(pt)
            if not ms:
                continue
            total += len(ms)
            tag = ''
            if i == 0:
                tag = '   <- 模块根 (module table)'
            print('--- proto#%d (bc=%d) 定义 %d 个%s' % (i, len(pt.bc), len(ms), tag))
            for name, ci, bi, kind in ms:
                mark = '  <<<<' if (want and want in name) else ''
                print('    %-36s -> proto#%-4d bc=%-5d %s%s'
                      % (name, ci, len(r.protos[ci].bc), kind, mark))
        print('合计定义点: %d' % total)

    elif mode == 'strs':
        pat = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 else None
        seen = []
        for i, pt in enumerate(r.protos):
            for s in pt.strings:
                if pat is None or pat.search(s):
                    seen.append((i, s))
        print('命中 %d 条字符串常量:' % len(seen))
        for i, s in seen:
            print('  proto#%-5d %s' % (i, s if len(s) < 200 else s[:197] + '...'))

    elif mode == 'calls':
        pat = re.compile(sys.argv[3], re.I) if len(sys.argv) > 3 else None
        for i, pt in enumerate(r.protos):
            cs = calls_of(pt)
            if not cs:
                continue
            names = [v for _, v, _ in cs]
            if pat and not any(pat.search(x) for x in names):
                continue
            print('--- proto#%d (bc=%d)' % (i, len(pt.bc)))
            line = []
            for kind, v, idx in cs:
                line.append('%s:%s' % (kind, v))
            # 去重保序
            o, s = [], set()
            for x in line:
                if x not in s:
                    s.add(x)
                    o.append(x)
            for k in range(0, len(o), 6):
                print('     ' + '  '.join(o[k:k + 6]))

    elif mode == 'cmds':
        nums, strs = cmd_of(entry, data)
        print('文件内出现的 5 位数字常量: %s' % nums)
        hit = sorted(s for s in strs if re.fullmatch(r'\d{4,5}', s))
        print('文件内 %d 条纯数字字符串: %s' % (len(hit), hit[:200]))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
