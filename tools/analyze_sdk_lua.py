#!/usr/bin/env python3
"""Find the Lua prototype that builds the "初始化失败 / 重新连接 / 退出游戏" dialog.

The blocking dialog is built in Lua (game_start.luac holds 重新连接 + 退出游戏,
file_update.luac holds 请检查网络 next to sdkCallFunc).  This locates the protos
that own those constants and disassembles them.

usage:
  python tools/analyze_sdk_lua.py find <member> <needle...>
  python tools/analyze_sdk_lua.py dump <member> <proto_idx> [start] [count]
  python tools/analyze_sdk_lua.py kgc <member> <proto_idx>
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import disasm, OPS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')

NEEDLES = {
    'init_fail': '\u521d\u59cb\u5316\u5931\u8d25',
    'check_net': '\u8bf7\u68c0\u67e5\u7f51\u7edc',
    'reconnect': '\u91cd\u65b0\u8fde\u63a5',
    'exit_game': '\u9000\u51fa\u6e38\u620f',
    'tip': '\u63d0\u793a',
    'net_err': '\u7f51\u7edc\u5f02\u5e38',
    'sdkCallFunc': 'sdkCallFunc',
    'sdkBackInit': 'sdkBackInit',
    'sdkAlert': 'sdkAlert',
    'init': 'init',
    'login': 'login',
}


def expand(args):
    out = []
    for a in args:
        if a in NEEDLES:
            out.append(NEEDLES[a])
        elif '\\u' in a:
            out.append(a.encode('ascii', 'surrogateescape').decode('unicode_escape'))
        else:
            out.append(a)
    return out


def flat_strings(pt):
    """All strings reachable in a proto, including inside table constants."""
    out = list(pt.strings)
    for t in pt.tables:
        for v in list(t.array) + [v for _k, v in t.hash]:
            if isinstance(v, str):
                out.append(v)
    return out


def cmd_sdkscan(needle):
    """Walk every .luac and report protos that both mention sdkCallFunc and a
    command-name constant, so we can see which module issues which command."""
    z = zipfile.ZipFile(APK)
    for name in z.namelist():
        if not name.endswith('.luac'):
            continue
        try:
            r = parse_bytes(z.read(name))
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            ss = flat_strings(pt)
            if not any('sdkCallFunc' in s for s in ss):
                continue
            if needle and not any(needle in s for s in ss):
                continue
            print('==== %s proto#%d bc=%d params=%d' % (name, i, len(pt.bc), pt.numparams))
            for s in pt.strings:
                print('      %r' % (s if len(s) < 90 else s[:87] + '...'))


def cmd_find(member, needles):
    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read(member))
    print('== %s  protos=%d' % (member, len(r.protos)))
    for i, pt in enumerate(r.protos):
        ss = flat_strings(pt)
        for n in needles:
            if any(n in s for s in ss):
                print('  proto#%-5d bc=%-5d kgc=%-4d params=%d  hit=%r'
                      % (i, len(pt.bc), len(pt.kgc), pt.numparams, n))
                break


def cmd_kgc(member, idx):
    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read(member))
    pt = r.protos[idx]
    print('== %s proto#%d bc=%d kgc=%d params=%d framesize=%d'
          % (member, idx, len(pt.bc), len(pt.kgc), pt.numparams, pt.framesize))
    for i, c in enumerate(pt.kgc):
        print('  kgc[%-3d] %r' % (i, c))


def cmd_dump(member, idx, start, count):
    z = zipfile.ZipFile(APK)
    r = parse_bytes(z.read(member))
    pt = r.protos[idx]
    print('== %s proto#%d bc=%d kgc=%d' % (member, idx, len(pt.bc), len(pt.kgc)))
    for i in range(start, min(start + count, len(pt.bc))):
        ins = pt.bc[i]
        op = ins & 0xff
        name = OPS[op] if op < len(OPS) else 'OP_%d' % op
        # reuse luajit_dis.decode which prints constant annotations
    disasm(pt, start, count)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    if cmd == 'find':
        cmd_find(sys.argv[2], expand(sys.argv[3:]))
    elif cmd == 'sdkscan':
        cmd_sdkscan(expand([sys.argv[2]])[0] if len(sys.argv) > 2 else None)
    elif cmd == 'kgc':
        cmd_kgc(sys.argv[2], int(sys.argv[3]))
    elif cmd == 'dump':
        cmd_dump(sys.argv[2], int(sys.argv[3]),
                 int(sys.argv[4]) if len(sys.argv) > 4 else 0,
                 int(sys.argv[5]) if len(sys.argv) > 5 else 60)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
