"""从 1.4.9 `cmd_resolve_*.luac` 还原**权威**消息定义（字段名 + 顺序 + 线格式）。

## 为什么这个工具是权威的（证据链）

反汇编 `cmd_resolve_200.luac` proto#0（= SC_20001）：

    TGETS  A=1 B=0 C=0   ; ['AutoConstruct']
    KSTR   A=3 D=1       ; 'sc'                      <- 方向
    KSHORT A=4 D=20001   ; 20001                     <- CMD
    TDUP   A=5 D=2       ; TableConst(array=[None,'code__C','msg__s'])
    CALL   A=1 D=261

⇒ 每个消息由 `AutoConstruct(dir, cmd, { '<字段名>__<格式字符>', ... })` 构造。
   **数组顺序就是字段顺序**（array 部分不会被 kidx 倒序），
   这与 `protocol/manual.md` 的 SC_20001{code:uint8, msg:string} 完全一致。

## 格式字符（LuaJIT ReadFMT）

    C=uint8  H=uint16  I=uint32
    c=int8   h=int16   i=int32
    s=string
    D|Xxx| = 计数前缀 + Xxx 结构数组

## 用法

    python tools/proto_spec.py cmds 20001 20002 20010 ...   # 查指定 CMD
    python tools/proto_spec.py list 200                        # 列出 2xx 号段全部消息
    python tools/proto_spec.py dsc SC_20010                    # 展开该消息引用的 Dsc 子结构
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import ChildRef, TableConst, parse_bytes  # noqa: E402

APK_149 = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')

FMT2TYPE = {
    'C': 'uint8', 'H': 'uint16', 'I': 'uint32',
    'c': 'int8', 'h': 'int16', 'i': 'int32',
    's': 'string',
}


def _op(w):
    return w & 0xff


# 用 luajit_dis 的 OPS 名称表
from luajit_dis import OPS, kidx  # noqa: E402


def parse_classes(data):
    """返回 [{dir, cmd, fields:[(name,fmt)], raw:[str], proto}]"""
    r = parse_bytes(data)
    out = []
    for i, pt in enumerate(r.protos):
        if len(pt.bc) < 5:
            continue
        d = None
        cmd = None
        table = None
        for j, w in enumerate(pt.bc):
            op = OPS[_op(w)] if _op(w) < len(OPS) else ''
            if op == 'KSTR':
                v = kidx(pt, (w >> 16) & 0xffff)
                if isinstance(v, str) and v in ('cs', 'sc'):
                    d = v
            elif op == 'KSHORT':
                v = (w >> 16) & 0xffff
                if 10000 <= v <= 40000:
                    cmd = v
            elif op == 'TDUP':
                v = kidx(pt, (w >> 16) & 0xffff)
                if isinstance(v, TableConst):
                    table = v
        if d is None or cmd is None:
            continue
        raw = [x for x in (table.array or []) if isinstance(x, str)] if table else []
        fields = []
        for s in raw:
            if '__' in s:
                nm, _, fm = s.rpartition('__')
                fields.append((nm, fm))
            else:
                fields.append((s, '?'))
        out.append({'dir': d, 'cmd': cmd, 'fields': fields, 'raw': raw,
                    'proto': i, 'flat': bool(table is None)})
    return out


def read_resolve(number, apk=APK_149):
    entry = 'assets/src/config/protocal/cmd_resolve_%s.luac' % number
    z = zipfile.ZipFile(apk)
    if entry not in z.namelist():
        return None
    return parse_classes(z.read(entry))


def fmt_ok(fm):
    """判断一个 fmt 串是否是合法的 ReadFMT 描述"""
    return bool(re.fullmatch(r'[CHIchis]*', fm or ''))


def show(cls, indent='  '):
    tag = '%s_%d' % (cls['dir'].upper(), cls['cmd'])
    if cls['flat']:
        print('%s%s  <无字段/空消息>' % (indent, tag))
        return
    print('%s%s' % (indent, tag))
    for nm, fm in cls['fields']:
        if fm in FMT2TYPE:
            t = FMT2TYPE[fm]
        elif fm.startswith('D|') or fm.startswith('struct<'):
            t = 'TABLE(%s)' % fm
        else:
            t = 'FMT(%s)' % fm
        print('%s    %-24s %s' % (indent, nm, t))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    mode = sys.argv[1]
    if mode == 'list':
        num = sys.argv[2]
        cls = read_resolve(num)
        if cls is None:
            print('!! 没有 cmd_resolve_%s.luac' % num)
            return
        print('=== cmd_resolve_%s.luac: %d 个消息类 ===' % (num, len(cls)))
        for c in cls:
            show(c)
        return

    if mode == 'cmds':
        want = set(int(x) for x in sys.argv[2:])
        z = zipfile.ZipFile(APK_149)
        names = sorted(n for n in z.namelist()
                       if n.startswith('assets/src/config/protocal/cmd_resolve_'))
        found = 0
        for n in names:
            for c in parse_classes(z.read(n)):
                if c['cmd'] in want:
                    found += 1
                    show(c, '')
                    print('     <- %s proto#%d' % (os.path.basename(n), c['proto']))
        print('命中 %d 个类 (查 %d 个 CMD)' % (found, len(want)))
        return

    if mode == 'dsc':
        # 展开给出消息引用的全部 Dsc 子结构（从同名 cmd_resolve 文件里找）
        z = zipfile.ZipFile(APK_149)
        allc = {}
        for n in z.namelist():
            if n.startswith('assets/src/config/protocal/cmd_resolve_'):
                try:
                    for c in parse_classes(z.read(n)):
                        allc.setdefault(c['cmd'], []).append((n, c))
                except Exception:
                    pass
        # 收集 fmt 引用
        seen = set()
        for target in sys.argv[2:]:
            m = re.fullmatch(r'(CS|SC)_(\d+)', target)
            if not m:
                continue
            num = m.group(2)
            for n, c in allc.get(int(num), []):
                for nm, fm in c['fields']:
                    for ref in re.findall(r'\|\s*([A-Za-z0-9_]+)\s*\|', fm):
                        if ref in seen:
                            continue
                        seen.add(ref)
                        print('--- %s (被 %s_%s.%s 引用)' % (ref, c['dir'].upper(), c['cmd'], nm))

        def dump_ref(prefix, depth=0):
            pad = '  ' * (depth + 1)
            for n in sorted(set(x[0] for x in sum(allc.values(), []))):
                pass
        # Dsc 结构不是独立类，直接在 proto 里找名字表
        for ref in sorted(seen):
            for n in sorted(z.namelist()):
                if not n.startswith('assets/src/config/protocal/cmd_resolve_'):
                    continue
                try:
                    r = parse_bytes(z.read(n))
                except Exception:
                    continue
                for i, pt in enumerate(r.protos):
                    ss = pt.strings
                    if ref in ss and len(ss) <= 12:
                        names = [s for s in ss if not s.startswith('D|')
                                 and s not in ('insert', 'table', 'ReadFMT')
                                 and not re.fullmatch(r'[CHIchis]+', s)
                                 and not s.startswith('H')]
                        fmts = [s for s in ss if re.fullmatch(r'[CHIchis]+', s)
                                and len(s) >= len(names)]
                        print('   %-40s names(raw kgc)=%s  fmt=%s'
                              % ('%s proto#%d' % (os.path.basename(n), i), names, fmts))
                        break
        return
    print(__doc__)


if __name__ == '__main__':
    main()
