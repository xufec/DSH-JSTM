#!/usr/bin/env python3
"""扫描 1.4.9 APK 全部 assets/src/**/*.luac，找出 `RegisterProtocal(<cmd>, '<handler>')`。

## 已证实的模式

反汇编 assets/src/game/battle/battle_ctrl.luac proto#0，可以看到：

    KSHORT A=? D=20002        ; CMD
    KSTR   A=? D=?...         ; 'scFightStart'（handler 名）
    GGET   A=? D=...          ; RegisterProtocal
    CALL   ...

即 **KSHORT(cmd) ... KSTR(handler) ... CALL** 的三元组。本脚本按
“KSHORT 数字落在 10000..40000 -> 其后 6 条指令内出现 KSTR 字符串 ->
该 proto 同时出现 RegisterProtocal/registerProtocal” 来识别。

【硬约束】只读 anzbao/jstm.apk（1.4.9, com.shiyue.dldl.ewan.qihoo）。

用法：
    python tools/find_register_protocal.py                 # 全部
    python tools/find_register_protocal.py 10500 10501 ...  # 只看这些 CMD
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

APK = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')
BANNED = ('142165', 'dldlJl')


def op(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else ''


def scan(rd, entry, want=None):
    out = []
    try:
        r = parse_bytes(rd)
    except Exception:
        return out
    for i, pt in enumerate(r.protos):
        ss = set(pt.strings)
        reg = any(s in ss for s in ('RegisterProtocal', 'registerProtocal',
                                    'RegisterProtocol', 'registProtocal',
                                    'registerProtocals'))
        if not reg:
            continue
        bc = pt.bc
        for j, w in enumerate(bc):
            if op(w) != 'KSHORT':
                continue
            cmd = (w >> 16) & 0xffff
            if not (10000 <= cmd <= 40000):
                continue
            if want and cmd not in want:
                continue
            h = None
            for k in range(j + 1, min(j + 8, len(bc))):
                if op(bc[k]) == 'KSTR':
                    v = kidx(pt, (bc[k] >> 16) & 0xffff)
                    if isinstance(v, str) and not re.fullmatch(r'[\d.]+', v):
                        h = v
                        break
                if op(bc[k]) in ('CALL', 'RET0', 'RET1'):
                    break
            out.append((cmd, h, entry, i, j))
    return out


def main():
    want = set(int(x) for x in sys.argv[1:] if x.isdigit()) or None
    z = zipfile.ZipFile(APK)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    allhits = []
    for n in names:
        if any(b in n for b in BANNED):
            continue
        allhits += scan(z.read(n), n, want)
    allhits.sort(key=lambda t: (t[0], t[2]))
    # 按 CMD 聚合
    by = {}
    for cmd, h, entry, pi, bi in allhits:
        by.setdefault(cmd, []).append((h, entry, pi, bi))
    print('共 %d 个 (CMD, handler) 命中点，覆盖 %d 个 CMD' % (len(allhits), len(by)))
    for cmd in sorted(by):
        print('CMD %-6d' % cmd)
        seen = set()
        for h, entry, pi, bi in by[cmd]:
            key = (h, entry)
            if key in seen:
                continue
            seen.add(key)
            print('    %-28s %s  proto#%d bc#%d' % (h, entry, pi, bi))


if __name__ == '__main__':
    main()
