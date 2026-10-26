#!/usr/bin/env python3
"""忠实还原 config_drop.luac / config_drop_item.luac 的嵌套表结构。

【硬约束】只处理调用方显式传入的 .luac 文件；本工具不自己打开 APK，
因此不可能误读 1.4.11（jstm_142165.apk）。传入文件应由
`tools/apk_extract_luac.py` 从 anzbao/jstm.apk (1.4.9) 提取。

## 为什么不能直接用 tools/extract_config_table.py

该工具用“最近一个数字常量”做启发式配键，对 config_drop.luac 这种
**KSHORT/KNUM 出现在 TDUP 之后**（字节码序列 TDUP ... KSHORT 20001 ; TSETV）
的文件会把键错配到嵌套子表上，并且会把 4 个空的子表全部丢掉。

## 本工具的做法

反汇编并**执行一个极简的解释器**，逐条模拟 LuaJIT 2.0 的常量装载与
表写入指令，从而得到和运行时完全一致的嵌套表。

操作数编码（LuaJIT 2.0，little-endian；本文件已用 config_drop_item.luac
的 TDUP 常量表逐字节验证）：
    BC 是 16 位小端：D&0xff = C（低字节），D>>8 = B（高字节）
        bc#5 TSETB A=4 D=769  -> C=1, B=3：reg4=TDUP 项结构，reg3=item_list
        bc#8 TSETS A=3 D=517  -> B=2, C=5：reg2 有 p_sum（外层 TDUP），C=5 是 'item_list'
        bc#9 KSHORT A=3 D=1001 ; bc#10 TSETV A=2 D=259 -> C=3, B=1
    规律：**A 是值/source 寄存器；B 是表寄存器；C 是键或数组下标**。
    TSETS  A=val, B=tbl, key=kgc[C]      -> tbl[key] = val
    TSETB  A=val, B=tbl, idx=C           -> tbl[C]  = val
    TSETV  A=val, B=tbl, key=val 寄存器  -> tbl[val] = val

用法：
    python tools/dump_drop_config.py <file.luac> [--json out.json] [--trace]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import ChildRef, TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def s16(x):
    x &= 0xffff
    return x - 0x10000 if x & 0x8000 else x


def u16(x):
    return x & 0xffff


class Sim:
    """极简 LuaJIT 解释器：只关心寄存器里的表/常量，把写操作记录成嵌套 dict。"""

    MAXREG = 256

    def __init__(self, pt):
        self.pt = pt
        self.reg = [None] * self.MAXREG
        self.globals = {}
        self.defs = []          # [(全局名, 表)]
        self.installs = []      # [(bc_index, 全局名, 表)]
        self.bsetv = []         # 无法还原的 TSETV 记录

    # ---------- 辅助 ----------
    def new_table(self, a, asize=0, hsize=0):
        t = {}
        self.reg[a] = t
        return t

    def tdup(self, a, tc):
        t = {}
        for k, v in (tc.hash or []):
            t[k] = v
        for i, v in enumerate(tc.array or [], start=1):
            t[i] = v
        self.reg[a] = t
        return t

    def val(self, a):
        return self.reg[a]

    def put(self, a, key, a_val):
        t = self.reg[a]
        if not isinstance(t, dict):
            raise RuntimeError('TSETS 目标寄存器 r%d 不是表 (实际 %r)' % (a, t))
        t[key] = self.val(a_val)

    # ---------- 主循环 ----------
    def run(self, trace=False):
        pt = self.pt
        bc = pt.bc
        for i, w in enumerate(bc):
            op = op_name(w)
            A = (w >> 8) & 0xff
            B = (w >> 24) & 0xff           # = (D>>8) 高字节
            C = (w >> 16) & 0xff           # = D&0xff 低字节
            D = (w >> 16) & 0xffff
            if trace:
                print('  i=%-4d %-8s A=%-3d B=%-3d C=%-3d D=%-6d r2=%s r3=%s'
                      % (i, op, A, B, C, D,
                         type(self.reg[2]).__name__, type(self.reg[3]).__name__))

            if op == 'TNEW':
                self.new_table(A, (D >> 11) & 0x1f, D & 0x7ff)
            elif op == 'TDUP':
                v = kidx(pt, u16(D))
                if isinstance(v, TableConst):
                    self.tdup(A, v)
                else:
                    self.new_table(A)
            elif op == 'TSETS':
                # A=值寄存器, B=表寄存器, C=kgc 常量索引（键）
                t = self.reg[B]
                if not isinstance(t, dict):
                    raise RuntimeError('TSETS@%d: 表寄存器 r%d 不是表 (%r)' % (i, B, t))
                t[kidx(pt, C)] = self.reg[A]
            elif op == 'TSETB':
                # A=值寄存器, B=表寄存器, C=数组下标
                t = self.reg[B]
                if not isinstance(t, dict):
                    raise RuntimeError('TSETB@%d: 表寄存器 r%d 不是表 (%r)' % (i, B, t))
                t[C] = self.reg[A]
            elif op == 'TSETV':
                # A=值寄存器, B=表寄存器, C=键寄存器
                t = self.reg[B]
                v = self.reg[A]
                k = self.reg[C]
                if isinstance(t, dict) and not isinstance(k, dict):
                    t[k] = v
                else:
                    self.bsetv.append((i, B, A, C, type(k).__name__))
            elif op == 'KSHORT':
                self.reg[A] = s16(D)
            elif op == 'KNUM':
                pos = len(pt.knum) - 1 - s16(D)
                self.reg[A] = pt.knum[pos] if 0 <= pos < len(pt.knum) else None
            elif op == 'KSTR':
                self.reg[A] = kidx(pt, u16(D))
            elif op == 'KCDATA':
                self.reg[A] = kidx(pt, u16(D))
            elif op == 'GGET':
                # 把全局当成一张 dict 来看待：这样 `Config.Xxx = {...}` 的
                # “先取全局、再 TSETS 挂子表、最后 GSET 回去”模式能完整还原。
                self.reg[A] = self.globals.setdefault(kidx(pt, u16(D)), {})
            elif op == 'GSET':
                nm = kidx(pt, u16(D))
                t = self.reg[A]
                self.globals[nm] = t
                self.installs.append((i, nm, t))
            elif op in ('CALL', 'CALLM', 'CALLMT', 'CALLT'):
                for r in range(A, A + max(B, 1)):
                    if r < self.MAXREG:
                        self.reg[r] = None
            elif op in ('RET0', 'RET1', 'RETM'):
                break
        return self.globals


def norm(v, seen=None, depth=0):
    if seen is None:
        seen = set()
    if isinstance(v, dict):
        if id(v) in seen:
            return '<cycle>'
        if depth > 12:
            return '<deep>'
        s2 = seen | {id(v)}
        out = {}
        for k, x in v.items():
            out[str(k)] = norm(x, s2, depth + 1)
        return out
    if isinstance(v, tuple) and v and v[0] == '__global__':
        return '<global %s>' % v[1]
    if isinstance(v, (TableConst, ChildRef)):
        return '<%s>' % type(v).__name__
    if isinstance(v, float) and v == int(v):
        return int(v)
    return v


def main():
    path = sys.argv[1]
    out = None
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
    trace = '--trace' in sys.argv
    r = parse_file(path)
    pt = r.protos[0]
    sim = Sim(pt)
    globs = sim.run(trace=trace)
    print('=== %s ===' % os.path.basename(path))
    print('protos=%d root bc=%d kgc=%d knum=%d'
          % (len(r.protos), len(pt.bc), len(pt.kgc), len(pt.knum)))
    print('全局安装点 %d 个：' % len(sim.installs))
    for bi, nm, t in sim.installs:
        n = len(t) if isinstance(t, dict) else type(t).__name__
        print('   bc#%-5d %-14s %s' % (bi, nm, ('dict(%d keys)' % n) if isinstance(t, dict) else n))
    if sim.bsetv:
        print('TSETV 键为表引用（不可 JSON 化）共 %d 处: %s'
              % (len(sim.bsetv), sim.bsetv[:10]))

    for nm, t in globs.items():
        if not isinstance(t, dict):
            continue
        keys = list(t.keys())
        numk = sorted(k for k in keys if isinstance(k, (int, float)))
        strk = sorted(k for k in keys if isinstance(k, str))
        print('\n### %s : %d 键' % (nm, len(keys)))
        if numk:
            print('   数字键(%d): %s' % (len(numk), numk[:60]))
        if strk:
            print('   字符串键(%d): %s' % (len(strk), strk[:40]))

    if out:
        data = {}
        for nm, t in globs.items():
            data.setdefault(nm, norm(t))
        json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('\n已写出 %s' % out)


if __name__ == '__main__':
    main()
