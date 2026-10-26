"""核查商城商品表：数量、type 分布、与客户端页签的对应关系。

数据来源（1.4.9）：
    analysis/1.4.9/shop_luac/config_mall.luac     <- 从 anzbao/jstm.apk 提取
    server/mall_config.json                       <- 服务端实际加载的商品表

客户端页签常量取自 `game/shop/shop_view.luac` proto#6 `updateTabBar`：
    NORMAL(常用) ZHENBAO(珍宝) EXCHANGE(试炼) GUILD(宗门) NPC
    YINBI(金魂币) HONOR(声望) JIFEN(积分) EXCOLLECT(兑换) WEEKDAY(热卖)

用法：python tools/audit_mall.py
"""
import collections
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MALL = os.path.join(ROOT, 'server', 'mall_config.json')
RAW = os.path.join(ROOT, 'analysis', '1.4.9', 'shop_luac',
                   'mall_table_1_Config.json')

TABS = ['NORMAL', 'ZHENBAO', 'EXCHANGE', 'GUILD', 'NPC',
        'YINBI', 'HONOR', 'JIFEN', 'EXCOLLECT', 'WEEKDAY']


def main():
    for label, p in (('server/mall_config.json', MALL),
                     ('analysis .../mall_table_1_Config.json', RAW)):
        if not os.path.exists(p):
            print('%-42s 不存在' % label)
            continue
        d = json.load(open(p, encoding='utf-8'))
        if isinstance(d, dict) and 'Config' in d:
            d = d['Config']
            if isinstance(d, dict) and len(d) == 1:
                d = list(d.values())[0]
        n = len(d)
        print('%-42s %d 条' % (label, n))

    if not os.path.exists(MALL):
        return 1
    goods = json.load(open(MALL, encoding='utf-8'))
    if isinstance(goods, dict):
        goods = list(goods.values())
    print('\n=== server/mall_config.json ===')
    print('商品数: %d' % len(goods))
    if not goods:
        return 1
    print('\n第一条完整字段:')
    g0 = goods[0]
    for k in sorted(g0):
        print('   %-16s %r' % (k, g0[k]))

    for field in ('type', 'pay_type', 'ico', 'bind'):
        c = collections.Counter(g.get(field) for g in goods)
        print('\n%s 分布: %s' % (field, dict(sorted(c.items(), key=lambda x: str(x[0])))))

    # type -> 页签 的候选对应（客户端页签常量顺序）
    print('\n客户端页签常量顺序: %s' % TABS)

    # 有效物品过滤后还剩多少（服务端会过滤）
    try:
        sys.path.insert(0, os.path.join(ROOT, 'server'))
        import mock_server as M
        M.DB_PATH = os.path.join(ROOT, 'server', 'state', 'roles.db')
        valid = [g for g in goods if M.is_valid_item(g.get('item_bid', 0))]
        print('\n经 is_valid_item 过滤后: %d / %d' % (len(valid), len(goods)))
        dropped = [g for g in goods if not M.is_valid_item(g.get('item_bid', 0))]
        if dropped:
            print('被丢弃的商品 item_bid（真实物品表里不存在）: %s'
                  % sorted({g.get('item_bid') for g in dropped})[:20])
    except Exception as e:
        print('\n(无法调用 mock_server 过滤: %r)' % (e,))
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
