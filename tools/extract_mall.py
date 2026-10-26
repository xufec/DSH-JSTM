"""从 1.4.9 的 config_mall.luac 提取商城商品表 → JSON。

字段来源：逐项从字节码 `TDUP` 常量读出（不是猜的）：
    id, item_bid, pay_type, type, bind, price, guild_lev,
    limit_week, limit_day_cli, cli_tag

与 `SC_12801.xs_list` 的对应（协议字段 → 本表字段）：
    id           ← id
    item_bid     ← item_bid
    bind         ← bind
    pay_type     ← pay_type          ★ 原版的"支付类型"
    old_price    ← （本表没有）        ⇒ 默认 0
    price        ← price
    type         ← type
    ico          ← （本表没有）        ⇒ 默认 0
    left_time    ← （本表没有）        ⇒ 默认 0
    can_buy_num  ← （本表没有）        ⇒ 默认 0

用法：python tools/extract_mall.py [apk] [out.json]
"""
import json
import sys
import zipfile

sys.path.insert(0, 'tools')
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

FIELDS = ['id', 'item_bid', 'pay_type', 'type', 'bind', 'price',
          'guild_lev', 'limit_week', 'limit_day_cli', 'cli_tag']


def extract(apk_path):
    z = zipfile.ZipFile(apk_path)
    r = parse_bytes(z.read('assets/src/config/config_mall.luac'))
    pt = r.protos[0]

    rows = []
    seen = set()
    for w in pt.bc:
        if OPS[w & 0xff] != 'TDUP':
            continue
        c = kidx(pt, (w >> 16) & 0xffff)
        h = dict(getattr(c, 'hash', []) or [])
        if 'item_bid' not in h or 'id' not in h:
            continue
        key = (h.get('id'), h.get('item_bid'), h.get('price'))
        if key in seen:
            continue
        seen.add(key)
        rows.append({k: h.get(k) for k in FIELDS})

    rows.sort(key=lambda x: (x.get('id') or 0))
    return rows


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    out = sys.argv[2] if len(sys.argv) > 2 else r'server\mall_config.json'
    rows = extract(apk)
    print('提取商品数:', len(rows))
    pts = sorted({r.get('pay_type') for r in rows if isinstance(r.get('pay_type'), int)})
    print('pay_type 取值:', pts, '   ← ★ 真实取值，之前的 {"1","2"} 映射不完整')
    print('抽样:')
    for r in rows[:6]:
        print('   id=%-6s item_bid=%-7s pay_type=%-3s type=%-4s price=%-8s bind=%s'
              % (r.get('id'), r.get('item_bid'), r.get('pay_type'),
                 r.get('type'), r.get('price'), r.get('bind')))
    json.dump(rows, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', out)


if __name__ == '__main__':
    main()
