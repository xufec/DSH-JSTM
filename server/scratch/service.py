# -*- coding: utf-8 -*-
"""scratch.service —— 刮刮乐（16651/16652）。

★ 证据等级（逐项标注，勿升级）：
  · 帧结构：**CONFIRMED** —— `protocol/fields.json`
      SC_16651{code,msg,remain_sec,cash_reward,card_list{index,card_id,gold,status},
               item_list{bid,num},item_effect_list{bid,effect_1,effect_2},client_reward}
      SC_16652{code,msg,index,status}
  · 规则与常量：**CONFIRMED** —— `server/cfg/config_scratch_card.json`
      `item_bid=28031`（刮卡道具）、`item={28031,1}`（每刮一次消耗 1 个）、
      `card_num=3`（3 张相同卡开奖）、`max_reward_id=6`、`ScratchCardRes=[null,card1..card6]`、
      `reward_time_list={1,999},{2,999},{3,999},{4,999},{5,2},{6,1}`（各档**可获得次数上限**）、
      `notice_reward_ids="6,5,4"`（需公告的档位）、`holiday_rule`（官方规则文本）
  · 客户端行为：**CONFIRMED** —— 反汇编 `game/scratcher/scratcher_view.luac` proto#17：
      `setData(card_list, cash_reward)`：`cash_reward~=0` ⇒ **清空全部格子（开奖重置）**；
      否则逐个 `itemList[card.index]:setData(card)`，`card.status~=0` ⇒ 该格可见（已刮开）。
  · ★ **各档钻石数值（100/200/300/500/1000/2000）：STRONG_INFERENCE** ——
      只出现在 `holiday_rule` 的**文本**里（全 cfg 无对应数值表，已全量搜索确认）。
      这是 APK 内的官方文案，**不是编造**，但属文本而非表 ⇒ 单点可替换（见 TIER_GOLD）。
  · **盘面张数**：服务端决定（客户端按 `card_list` 动态建格）⇒ 取 `card_num=3`
      （与"每消耗一个道具必定会刮出 3 张相同的卡"一致）⇒ **INFERENCE**，单点可替换。
"""

import json
import os
import random
import time

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.normpath(os.path.join(HERE, '..', 'cfg', 'config_scratch_card.json'))

# ★ 单点可替换：各档钻石数值（来源 = config_scratch_card.holiday_rule 官方文本；
#   无对应数值表 ⇒ STRONG_INFERENCE）。若日后拿到数值表，只改这一行。
TIER_GOLD = {1: 100, 2: 200, 3: 300, 4: 500, 5: 1000, 6: 2000}

_cfg = None


def scratch_cfg():
    global _cfg
    if _cfg is not None:
        return _cfg
    val = {}
    try:
        with open(CFG, encoding='utf-8') as f:
            j = json.load(f)
        for _k, v in (j.get('ScratchCardConst') or {}).items():
            h = v.get('hash') or {}
            if h.get('label'):
                val[h['label']] = h.get('val')
        _cfg = {
            'item_bid': int(val.get('item_bid') or 28031),
            'card_num': int(val.get('card_num') or 3),
            'max_reward_id': int(val.get('max_reward_id') or 6),
            'caps': _parse_caps(val.get('reward_time_list')),
            'notice': str(val.get('notice_reward_ids') or ''),
        }
        log('server.log', 'scratch cfg: item=%s card_num=%s caps=%s'
            % (_cfg['item_bid'], _cfg['card_num'], _cfg['caps']))
    except Exception as e:
        log('server.log', '!! config_scratch_card load failed: %r' % (e,))
        _cfg = {'item_bid': 28031, 'card_num': 3, 'max_reward_id': 6, 'caps': {}, 'notice': ''}
    return _cfg


def _parse_caps(s):
    """`"{1,999},{2,999},{5,2},{6,1}"` → {1:999, 2:999, 5:2, 6:1}。"""
    out = {}
    for part in str(s or '').replace('{', '').replace('}', '').split('),'):
        p = part.replace('(', '').split(',')
        if len(p) >= 2:
            try:
                out[int(p[0])] = int(p[1])
            except Exception:
                pass
    return out


def db_scratch_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_scratch (
        rid INTEGER PRIMARY KEY, board_id INTEGER, cards TEXT, ts INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS role_scratch_tier (
        rid INTEGER, tier INTEGER, cnt INTEGER, PRIMARY KEY (rid, tier))""")
    con.commit()
    db_release(con)


def _board(rid):
    db_scratch_init()
    con = db_conn()
    r = con.execute('SELECT board_id,cards,ts FROM role_scratch WHERE rid=?',
                    (int(rid),)).fetchone()
    db_release(con)
    if not r:
        return {'board_id': 0, 'cards': [], 'ts': 0}
    try:
        cards = json.loads(r[1] or '[]')
    except Exception:
        cards = []
    return {'board_id': int(r[0] or 0), 'cards': cards if isinstance(cards, list) else [],
            'ts': int(r[2] or 0)}


def _save_board(rid, board_id, cards):
    db_scratch_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_scratch VALUES (?,?,?,?)',
                (int(rid), int(board_id), json.dumps(cards), int(time.time())))
    con.commit()
    db_release(con)


def _tier_cnt(rid, tier):
    db_scratch_init()
    con = db_conn()
    r = con.execute('SELECT cnt FROM role_scratch_tier WHERE rid=? AND tier=?',
                    (int(rid), int(tier))).fetchone()
    db_release(con)
    return int(r[0]) if r else 0


def _tier_add(rid, tier, n=1):
    db_scratch_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_scratch_tier VALUES (?,?,?)',
                (int(rid), int(tier), _tier_cnt(rid, tier) + int(n)))
    con.commit()
    db_release(con)


def _pick_tier(rid):
    """按 `reward_time_list` 上限挑一档（超限的档不再产出）。"""
    cfg = scratch_cfg()
    ok = [t for t in range(1, cfg['max_reward_id'] + 1)
          if _tier_cnt(rid, t) < int(cfg['caps'].get(t, 999))]
    if not ok:
        ok = [1]
    # 低档权重更高（规则文本未给概率 ⇒ 均匀取，仅保证可达；标 INFERENCE）
    return random.choice(ok)


def _bag_count(rid, bid):
    """背包中某 bid 的总数量（自持，避免依赖未搬迁的 helper）。"""
    try:
        con = db_conn()
        n = con.execute('SELECT COALESCE(SUM(quantity),0) FROM bag_items '
                        'WHERE rid=? AND bid=?', (int(rid), int(bid))).fetchone()[0]
        db_release(con)
        return int(n or 0)
    except Exception as e:
        log('tcp.log', '  !! scratch _bag_count failed: %r' % (e,))
        return 0


def _bag_consume(rid, bid, n):
    """扣减 n 个（不足则不动，返回 False）。逐行从后往前扣，扣空即删行。"""
    if _bag_count(rid, bid) < int(n):
        return False
    need = int(n)
    try:
        con = db_conn()
        rows = con.execute('SELECT item_id,quantity FROM bag_items WHERE rid=? AND bid=? '
                           'ORDER BY item_id', (int(rid), int(bid))).fetchall()
        for item_id, qty in reversed(rows):
            if need <= 0:
                break
            take = min(int(qty), need)
            left = int(qty) - take
            if left <= 0:
                con.execute('DELETE FROM bag_items WHERE rid=? AND item_id=?',
                            (int(rid), item_id))
            else:
                con.execute('UPDATE bag_items SET quantity=? WHERE rid=? AND item_id=?',
                            (left, int(rid), item_id))
            need -= take
        con.commit()
        db_release(con)
        return need == 0
    except Exception as e:
        log('tcp.log', '  !! scratch _bag_consume failed: %r' % (e,))
        return False


def new_board(rid):
    """开新盘（**消耗 1 个道具**）。返回 (ok, msg, cards)。"""
    cfg = scratch_cfg()
    if not _bag_consume(rid, cfg['item_bid'], 1):
        return False, '刮刮乐道具不足', []
    tier = _pick_tier(rid)
    gold = TIER_GOLD.get(tier, 0)
    cards = [{'index': i, 'card_id': tier, 'gold': gold, 'status': 0}
             for i in range(cfg['card_num'])]
    b = _board(rid)
    _save_board(rid, b['board_id'] + 1, cards)
    _tier_add(rid, tier, 1)
    log('tcp.log', '  ** 刮刮乐开新盘 rid=%d board=%d tier=%d gold=%d（耗道具 %d×1）'
        % (rid, b['board_id'] + 1, tier, gold, cfg['item_bid']))
    return True, '', cards


def scratch(rid, index):
    """刮开第 index 格。返回 (ok, msg, cards, done, cash_reward)。"""
    b = _board(rid)
    cards = b['cards']
    if not cards:
        ok, msg, cards = new_board(rid)
        if not ok:
            return False, msg, [], False, 0
    if index < 0 or index >= len(cards):
        return False, '格子无效', cards, False, 0
    if int(cards[index].get('status') or 0) != 0:
        return False, '该格已刮开', cards, False, 0
    cards[index]['status'] = 1
    _save_board(rid, b['board_id'] or 1, cards)
    done = all(int(c.get('status') or 0) == 1 for c in cards)
    cash = int(cards[0].get('gold') or 0) if done else 0
    if done:
        # 发奖（幂等：reference_id 带 board_id）
        from reward.service import grant
        grant(rid, [{'kind': 'asset', 'code': 'gold', 'amount': cash}],
              'scratch:%d:%d' % (int(rid), int(b['board_id'] or 1)), source='scratch')
        log('tcp.log', '  ** 刮刮乐开奖 rid=%d board=%s gold=%d' % (rid, b['board_id'], cash))
    return True, '', cards, done, cash


def take_reward(rid):
    """若盘面已全部刮开 ⇒ 返回 cash_reward 并清盘（客户端据此开奖并重置）。"""
    b = _board(rid)
    cards = b['cards']
    if cards and all(int(c.get('status') or 0) == 1 for c in cards):
        cash = int(cards[0].get('gold') or 0)
        _save_board(rid, 0, [])
        return cash, []
    return 0, cards
