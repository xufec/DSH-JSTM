"""从 1.4.9 的 config_item.luac 提取物品表 → JSON。

字段顺序**不是猜的**：从 `config_item.luac proto[0]` 的字节码逐条读出（权威）：
    @21 GGET 'Config' / TGETS 'ItemData' / TDUP ...
    @24 TGETB / TSETS 'bid'
    @26       TSETS 'name'
    @28       TSETS 'type'        ← ★ 装备部位（客户端 `equip_type` 就取这里）
    @30       TSETS 'lev'
    @32       TSETS 'bind_type'
    @34       TSETS 'quality'
    @36       TSETS 'grade'
    @38       TSETS 'overlap'
    ...

用法：python tools/extract_item_v2.py [apk] [out.json]
"""
import json
import sys
import zipfile

sys.path.insert(0, 'tools')
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

# 按 proto[0] 里 TGETB/TSETS 的**出现顺序**动态推出字段名（不写死）
ITEM_CFG = 'assets/src/config/config_item.luac'


def field_order(r):
    """从 proto[0] 的 `TGETB` + `TSETS` 配对里推出字段顺序。"""
    pt = r.protos[0]
    order = []
    pending = False
    for w in pt.bc:
        op = OPS[w & 0xff]
        if op == 'TGETB':
            pending = True
        elif op == 'TSETS':
            nm = kidx(pt, (w >> 16) & 0xff)
            if pending and isinstance(nm, str):
                order.append(nm)
            pending = False
    return order


def extract(apk_path):
    z = zipfile.ZipFile(apk_path)
    r = parse_bytes(z.read(ITEM_CFG))
    order = field_order(r)
    if not order or order[0] != 'bid':
        raise SystemExit('字段顺序推导失败: %r' % (order[:8],))

    # proto[1] 是数据体：逐条 TDUP 取 array
    data = {}
    for pt in r.protos[1:]:
        for w in pt.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            c = kidx(pt, (w >> 16) & 0xffff)
            arr = getattr(c, 'array', None) or []
            if len(arr) < 2:
                continue
            bid = arr[1] if isinstance(arr[1], int) else arr[0]
            if not isinstance(bid, int):
                continue
            row = {}
            for i, nm in enumerate(order):
                idx = i + 1          # arr[0] 是占位
                row[nm] = arr[idx] if idx < len(arr) else None
            data[str(bid)] = row
    return order, data


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    out = sys.argv[2] if len(sys.argv) > 2 else r'server\item_config.json'
    order, data = extract(apk)
    print('字段顺序:', order[:16])
    print('物品数  :', len(data))
    import collections
    c = collections.Counter(v.get('type') for v in data.values()
                            if isinstance(v.get('type'), int))
    print('type 分布:', dict(sorted(c.items())))
    # 抽样：看几个已知 bid
    for b in ('33001', '40001', '41001', '41211', '41401', '41601', '41801'):
        print('  bid=%-7s type=%-5s name=%r' % (b, (data.get(b) or {}).get('type'),
                                                (data.get(b) or {}).get('name')))
    json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('已写出', out)


if __name__ == '__main__':
    main()
