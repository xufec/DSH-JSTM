"""在 1.4.9 APK 全部 .luac 里找"某个 TDUP 常量表以某前缀字符串为键"的位置。

用来定位枚举定义（如 MissionType = { MIS_ZHU = 1, ... }）。

用法：python tools/find_enum_table.py MIS_
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_bytes  # noqa: E402

APK = r'anzbao\jstm.apk'


def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else 'MIS_'
    z = zipfile.ZipFile(APK)
    names = [n for n in z.namelist()
             if n.startswith('assets/src/') and n.endswith('.luac')]
    for n in names:
        try:
            r = parse_bytes(z.read(n))
        except Exception:
            continue
        for i, pt in enumerate(r.protos):
            for c in pt.kgc:
                if not isinstance(c, TableConst):
                    continue
                keys = [str(k) for k, _ in (c.hash or [])]
                hit = [k for k in keys if k.startswith(prefix)]
                if len(hit) >= 3:
                    print('%-64s proto#%-4d 表内 %d 个 %s* 键'
                          % (n, i, len(hit), prefix))
                    print('     %s' % {str(k): v for k, v in (c.hash or [])})


if __name__ == '__main__':
    main()
