"""C5-D：dump `config_item.luac` proto#0 的**字段名表** —— 判定位置数组里
哪一个下标才是物品 id（键 vs 内部 field[1] 谁权威）。

背景：`server/cfg/config_item.json` 里 **1116/3013** 条记录的键与其 `fields[1]`
不一致（例：键 41803 的记录自身 id=38081「魂骨重铸礼包」）。
两种可能：
  (a) 提取器配对错了（键不可信）→ 必须按内部 id 重建索引；
  (b) 键才是客户端 `Config.Item[bid]` 的索引，field[1] 是别的字段。
`proto#0` 是 schema 声明，字段名能直接定案。
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import parse_bytes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = [
    os.path.join(ROOT, 'anzbao', 'jstm.apk'),
    os.path.join(ROOT, 'anzbao', 'jstm_142165.apk'),
    os.path.join(ROOT, '_tmp_cfg', 'config_item.luac'),
]


def strings_of(pt):
    out = []
    for k in getattr(pt, 'kgc', []) or []:
        if isinstance(k, str):
            out.append(k)
    return out


def main():
    for p in CAND:
        if not os.path.exists(p):
            continue
        print('=== %s ===' % p)
        try:
            if p.endswith('.apk'):
                z = zipfile.ZipFile(p)
                blob = z.read('assets/src/config/config_item.luac')
                r = parse_bytes(blob)
            else:
                r = parse_bytes(open(p, 'rb').read())
        except Exception as e:
            print('  read failed: %r' % (e,))
            continue
        for i in range(min(3, len(r.protos))):
            pt = r.protos[i]
            ss = strings_of(pt)
            print('  proto#%d bc=%s kgc=%d strings=%d' % (i, getattr(pt, 'bc_len', '?'),
                                                          len(getattr(pt, 'kgc', []) or []), len(ss)))
            # 前 40 个非平凡字符串
            keep = [s for s in ss if len(s) > 1][:40]
            for j, s in enumerate(keep):
                print('      [%2d] %r' % (j, s))
        print()


if __name__ == '__main__':
    main()
