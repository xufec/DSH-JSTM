"""从 1.4.9 的 config_item_gift.luac 提取「礼包 → 内容」表 → JSON（**覆盖三张表**）。

该文件含三张配置表：
    Config.ItemGift      —— 普通礼包
    Config.ItemNewGift   —— 新版礼包（**30010 这类在这里**）
    Config.SelectGift    —— 自选礼包

结构（从字节码 TDUP 常量直读，不是猜的）：
    [None, <gift_bid>, <item_bid>, <num>]

用法：python tools/extract_item_gift.py [apk] [out.json]
"""
import json
import sys
import zipfile

sys.path.insert(0, 'tools')
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

SRC = 'assets/src/config/config_item_gift.luac'


def extract(apk_path):
    z = zipfile.ZipFile(apk_path)
    r = parse_bytes(z.read(SRC))
    out = {}
    n_arr = 0
    for pt in r.protos:
        for w in pt.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            c = kidx(pt, (w >> 16) & 0xffff)
            arr = getattr(c, 'array', None) or []
            if len(arr) < 4:
                continue
            gift, item, num = arr[1], arr[2], arr[3]
            if not (isinstance(gift, int) and isinstance(item, int)):
                continue
            n_arr += 1
            out.setdefault(str(gift), []).append([int(item), int(num or 1)])
    return out, n_arr


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    dst = sys.argv[2] if len(sys.argv) > 2 else r'server\item_gift.json'
    d, n = extract(apk)
    print('扫描到内容行:', n)
    print('礼包数:', len(d))
    for b in ('30010', '33001', '36531', '1', '100'):
        if b in d:
            print('  %-7s -> %s' % (b, d[b][:8]))
        else:
            print('  %-7s -> (\u65e0)' % b)
    json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
    print('已写出', dst)


if __name__ == '__main__':
    main()
