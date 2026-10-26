#!/usr/bin/env python3
"""带"跳转目标解析"的反汇编器（Phase E 取证用）。

与 `tools/luajit_dis.py` 的差别（本工具修正了两点，依据是 APK 自带的
LuaJIT 反编译器 `tools/ljd/ljd/` 的指令定义，而不是猜测）：

1. **IST / ISF 的被测寄存器在 C 域（bits16-23），不在 A 域。**
   `tools/ljd/ljd/bytecode/instructions.py`:
       IST = _IDef("IST", None, None, T_VAR, "if {D}")
       ISF = _IDef("ISF", None, None, T_VAR, "if not {D}")
   → A_type/B_type 均为 None，CD_type=T_VAR；`rawdump/code.py`
     `_set_instruction_operands` 对 3 参数指令取 `CD = (codeword>>16)&0xFF`。
   `tools/luajit_dis.py` 把 D 打印成 16 位，读起来像"立即数"，容易误判。

2. **JMP/分支目标的算术**：`T_JMP = operand - 0x8000`，且相对**下一条**指令
   （`tools/ljd/ljd/rawdump/code.py: _process_operand`）。
   本工具直接打印解析后的目标行号。

3. `<条件指令> ; JMP L` 的语义：**条件成立 → 跳到 L；条件不成立 → 落空（执行 JMP 的
   下一条）**。这是唯一的统一规则（对 IST/ISF 与比较族都成立），依据：
       `tools/ljd/ljd/ast/builder.py`:
           _COMPARISON_MAP[ISGE] = T_LESS_THEN   # "Mind the inversion"
           _COMPARISON_MAP[ISEQV] = T_NOT_EQUAL
           ...
           warp.false_target = destination ; warp.true_target = jump_addr + 1
       ⇒ ljd 构造出的"源码条件"是操作码名字的**取反**，而 destination 是 condition
         **为假**时的落点；两步合成后 = 操作码名字本身成立时跳转。
   本工具已用 5 个互相独立的函数交叉验证（config_role_attr `if not Config then`、
   role_ctrl#5 `if not v then v=0 end`、role_ctrl#13 卫语句、main_ui#16 四分
   支、role_calculate#2 的等级判定），结论一致。

用法：
    python analysis/1.4.9/level/_flow_dis.py <asset path> <proto#> [start] [count]
"""
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import parse_bytes, TableConst, ChildRef  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')

COND = set(['ISLT', 'ISGE', 'ISLE', 'ISGT', 'ISEQV', 'ISNEV', 'ISEQS', 'ISNES',
            'ISEQN', 'ISNEN', 'ISEQP', 'ISNEP', 'ISTC', 'ISFC', 'IST', 'ISF'])
PRIM = {0: 'nil', 1: 'false', 2: 'true'}


def jmp_target(pc, d):
    """T_JMP: operand - 0x8000，相对下一条指令。"""
    return pc + 1 + (d - 0x8000)


def operand_text(pt, op, w):
    A = (w >> 8) & 0xff
    C = (w >> 16) & 0xff
    B = (w >> 24) & 0xff
    D = (w >> 16) & 0xffff
    if op in ('TGETS', 'TSETS'):
        return 'A=r%d B=r%d C=%r' % (A, B, kidx(pt, C))
    if op in ('TGETV',):
        return 'A=r%d B=r%d C=r%d' % (A, B, C)
    if op in ('TSETV',):
        return 'A=r%d B=r%d k=r%d' % (A, B, C)
    if op in ('TSETB', 'TGETB'):
        return 'A=r%d B=r%d idx=%d' % (A, B, C)
    if op in ('KSTR', 'KCDATA', 'FNEW', 'TDUP', 'GGET', 'GSET'):
        return 'A=r%d K=%r' % (A, kidx(pt, D))
    if op == 'KNUM':
        pos = len(pt.knum) - 1 - D
        v = pt.knum[pos] if 0 <= pos < len(pt.knum) else None
        return 'A=r%d N=%r' % (A, v)
    if op == 'KSHORT':
        return 'A=r%d =%d' % (A, D if D < 0x8000 else D - 0x10000)
    if op == 'KPRI':
        return 'A=r%d =%s' % (A, PRIM.get(D, D))
    if op in ('JMP',):
        return '-> %d' % jmp_target((w >> 16) * 0, D)  # 调用方修正
    if op in ('IST', 'ISF'):
        return 'test r%d' % C
    if op in ('ISTC', 'ISFC'):
        return 'r%d = r%d' % (A, C)
    if op in COND:
        return 'r%d vs %s' % (A, ('r%d' % C) if op.endswith('V') else
                              (PRIM.get(C, C) if op.endswith('P') else
                               (repr(kidx(pt, C)) if op.endswith('S') else C)))
    return 'A=r%d B=r%d C=r%d D=%d' % (A, B, C, D)


def main():
    member = sys.argv[1]
    pi = int(sys.argv[2])
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 400
    if os.path.isfile(member):
        data = open(member, 'rb').read()
        label = member
    else:
        z = zipfile.ZipFile(APK)
        data = z.read(member)
        label = member
    r = parse_bytes(data)
    pt = r.protos[pi]
    print('=== %s proto#%d bc=%d params=%d ===' % (label, pi, len(pt.bc), pt.numparams))
    for i in range(start, min(start + count, len(pt.bc))):
        w = pt.bc[i]
        o = w & 0xff
        op = OPS[o] if o < len(OPS) else 'OP_%d' % o
        if op == 'JMP':
            tgt = jmp_target(i, (w >> 16) & 0xffff)
            print('  %4d  %-7s goto %d' % (i, op, tgt))
            continue
        txt = operand_text(pt, op, w)
        note = ''
        if op in COND and i + 1 < len(pt.bc):
            nw = pt.bc[i + 1]
            nop = OPS[nw & 0xff]
            if nop == 'JMP':
                tgt = jmp_target(i + 1, (nw >> 16) & 0xffff)
                note = '   ; 成立->%d  不成立->%d' % (tgt, i + 2)
        print('  %4d  %-7s %s%s' % (i, op, txt, note))


if __name__ == '__main__':
    main()
