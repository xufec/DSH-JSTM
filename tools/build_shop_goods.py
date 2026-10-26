"""Phase F：从 1.4.9 提取**全部 5 张商城表**，并生成服务端所需的货物文件。

## 背景（为什么原来的提取不完整）

`assets/src/config/config_mall.luac` 里 `Config` 有 **5 张表**：

    Config.MallGoods         110 条  —— 「常用」页签的货物（**含 item_bid / price / type**）
    Config.MallWeek           24 条  —— 「热卖/周商店」页签（type=20, limit_week）
    Config.MallXian           45 条  —— 「珍宝/限时」页签，**只有 {id, cli_tag}**
    Config.MallType            4 条  —— 等级区间 -> 商城 type 的映射
    Config.MallHuobanXishu    14 条  —— 伙伴系数

而 `server/mall_config.json` 里只有 **134 = MallGoods(110) + MallWeek(24)**，
**`MallXian` 从未被提取** —— 这正是「珍珍宝页签为空」在数据侧的成因之一
（另一侧成因是服务端**没有实现 12836**，见 `analysis/1.4.9/shop/mall_protocol_matrix.md`）。

## ★ 诚实标注：珍宝货物的内容是**合成的**

`MallXian` 只有 `{id, cli_tag}`，**没有 item_bid / price / pay_type** ——
也就是说**原版珍宝到底卖什么、卖多少钱，不在客户端 APK 里**（属原版服务端数据）。

因此本脚本生成 `server/mall_zhenbao.json` 时：

- **id 用原版**：严格取 `MallXian` 的 45 个 id（`21001..21045`）——
  这样客户端 `setZhenbaoGoodsList` 能按 id 关联到 `cli_tag`；**这部分是原版数据**。
- **item_bid / price / pay_type / bind / limit_num 是 `IMPLEMENTATION_FALLBACK`**：
  从**真实物品表 `Config.Item`** 里按确定性规则挑选**可使用的消耗品**，
  保证"买得到、用得上"，**但绝不声称是原版配置**。

用法：
    python tools/build_shop_goods.py            # 提取 + 生成 + 自检
    python tools/build_shop_goods.py --check    # 只自检，不写文件
"""
import argparse
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
SHOP_DIR = os.path.join(ROOT, 'analysis', '1.4.9', 'shop_luac')
LUAC = os.path.join(SHOP_DIR, 'config_mall.luac')
ALL_JSON = os.path.join(SHOP_DIR, '_mall_all.json')
SERVER_MALL = os.path.join(ROOT, 'server', 'mall_config.json')
SERVER_ZHENBAO = os.path.join(ROOT, 'server', 'mall_zhenbao.json')
ITEM_JSON = os.path.join(ROOT, 'analysis', '1.4.9', 'item', 'config_item.json')

# 可用于「珍宝」的真实物品类型（来自 config_item.json 的 idx3）：
#   31 = 食物/消耗品、32 = 打造石、33 = 各种符、35 = 变身丹/地图
USABLE_TYPES = (31, 32, 33, 35)


def load_all():
    if not os.path.exists(ALL_JSON):
        print('!! 缺少 %s，请先运行 tools/dump_drop_config.py 提取 config_mall.luac' % ALL_JSON)
        return None
    return json.load(open(ALL_JSON, encoding='utf-8'))['Config']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    cfg = load_all()
    if cfg is None:
        return 1
    print('=== config_mall.luac 的 5 张表 ===')
    for k in sorted(cfg):
        v = cfg[k]
        print('   %-18s %d 项' % (k, len(v) if hasattr(v, '__len__') else 0))

    mg = cfg['MallGoods']
    mw = cfg['MallWeek']
    mx = cfg['MallXian']

    # ---------- ① 核对现有 mall_config.json ----------
    cur = json.load(open(SERVER_MALL, encoding='utf-8'))
    print('\n=== 现有 server/mall_config.json ===')
    print('   %d 条；MallGoods(%d) + MallWeek(%d) = %d'
          % (len(cur), len(mg), len(mw), len(mg) + len(mw)))
    cur_ids = {int(g.get('id', 0)) for g in cur}
    expect = {int(k) for k in mg} | {int(k) for k in mw}
    print('   id 集合是否等于 MallGoods ∪ MallWeek: %s'
          % ('是 ✅' if cur_ids == expect else
             ('否 ❌ 差集=%s' % sorted(cur_ids ^ expect)[:10])))

    # ---------- ② 生成珍宝货物 ----------
    items = json.load(open(ITEM_JSON, encoding='utf-8'))
    usable = []
    for bid, arr in items.items():
        if not (isinstance(arr, list) and len(arr) > 3):
            continue
        t = arr[3]
        nm = arr[2] if len(arr) > 2 else ''
        if isinstance(t, int) and t in USABLE_TYPES and isinstance(nm, str) and nm:
            usable.append((int(bid), nm, t))
    usable.sort()
    print('\n=== 真实物品表里可作货物的消耗品 ===')
    print('   类型 %s 共 %d 件（例：%s）'
          % (list(USABLE_TYPES), len(usable), [u[1] for u in usable[:4]]))

    xian_ids = sorted(int(k) for k in mx)
    if not usable:
        print('!! 没有可用消耗品，无法生成珍宝货物')
        return 1
    if len(usable) < len(xian_ids):
        print('   ⚠ 可用物品(%d) 少于珍宝槽位(%d)，将循环取用' % (len(usable), len(xian_ids)))

    zhenbao = []
    for i, gid in enumerate(xian_ids):
        bid, nm, t = usable[i % len(usable)]
        zhenbao.append({
            'id': gid,                    # ★ 原版 id（来自 Config.MallXian）
            'item_bid': bid,              # ⚠ FALLBACK
            'item_name': nm,              # 仅便于人工核对，不下发
            'pay_type': 1,                # ⚠ FALLBACK（1 = 元宝/钻石类，见 pay_type 说明）
            'bind': 1,
            'old_price': 0,
            'price': 50 + (i % 5) * 50,   # ⚠ FALLBACK
            'limit_num': 5,               # ⚠ FALLBACK（SC_12836.limit_num:C）
            'buy_num': 0,
            'cli_tag': (mx[str(gid)].get('cli_tag') or '') if str(gid) in mx else '',
            'source': 'IMPLEMENTATION_FALLBACK',
        })
    print('\n=== 生成珍宝货物 ===')
    print('   槽位 %d 个，id 取自原版 Config.MallXian（%d..%d）'
          % (len(zhenbao), xian_ids[0], xian_ids[-1]))
    print('   前 3 条: %s' % json.dumps(zhenbao[:3], ensure_ascii=False)[:400])
    print('   ⚠ item_bid / price / pay_type / limit_num 均为 IMPLEMENTATION_FALLBACK，'
          '**不是原版数值**')

    if a.check:
        print('\n(--check：未写文件)')
        return 0

    json.dump(zhenbao, open(SERVER_ZHENBAO, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('\n已写出 %s（%d 条）' % (SERVER_ZHENBAO, len(zhenbao)))

    # ---------- ③ 生成兑换商店货物（SC_12840）----------
    #   权威字段：id:H, new_item_bid:I, new_item_num:I, new_bind:C,
    #             item_bid:I, item_num:I, limit_num:C, buy_num:C
    #   = 「用 item_bid × item_num 换 new_item_bid × new_item_num」
    #   ⚠ 原版兑换配方不在 APK 内 ⇒ 同上标 IMPLEMENTATION_FALLBACK。
    EX_N = 20
    exchange = []
    for i in range(EX_N):
        give = usable[i % len(usable)]                 # 消耗
        get = usable[(i * 7 + 5) % len(usable)]        # 产出（错开取）
        exchange.append({
            'id': 22001 + i,                           # ⚠ 合成 id
            'item_bid': give[0], 'item_num': 10,       # ⚠ FALLBACK
            'new_item_bid': get[0], 'new_item_num': 1,  # ⚠ FALLBACK
            'new_bind': 1,
            'limit_num': 10, 'buy_num': 0,
            'give_name': give[1], 'get_name': get[1],   # 仅便于人工核对
            'source': 'IMPLEMENTATION_FALLBACK',
        })
    ex_path = os.path.join(ROOT, 'server', 'mall_exchange.json')
    json.dump(exchange, open(ex_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('已写出 %s（%d 条兑换配方）' % (ex_path, len(exchange)))
    print('   例: %s ×%d  ->  %s ×%d'
          % (exchange[0]['give_name'], exchange[0]['item_num'],
             exchange[0]['get_name'], exchange[0]['new_item_num']))
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
