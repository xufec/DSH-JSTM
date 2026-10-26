# -*- coding: utf-8 -*-
"""partner.service —— 伙伴面板 + 培养（升级）闭环（Phase 8）。

两条真实闭环：
  1) 面板只读闭环：partner_list(11215) = 53 配置伙伴 × 已拥有 lev/exp（role_heros）。
     编码器与旧 if 链（mock_server L17417–17479）逐字段一致 ⇒ 帧长恒为
     2(header)+53×48 = 2546 body / 2552 整帧（与 tcp.log 基线一致）。
  2) 培养写闭环：feed(rid,bid) = 扣 gold(CurrencyService) → 加 exp → 按 PartnerLevUp
     升级（CONFIRMED exp_max）→ 属性贡献经 AttributeService.apply_delta →
     PowerService 重算 → 由调用方推送 10304/10502。

证据纪律：
  · PartnerLevUp / PartnerConstant / PartnerBase 均为 1.4.11 反构造 CONFIRMED。
  · 培养每次消耗 gold / 每次喂给 exp / 属性贡献系数 ⇒ 无配置真值，标 # INFERENCE 占位
    + 替换点（见 FEED_GOLD / FEED_EXP / _attr_growth_delta）。
"""

import json
import os

from core import runtime
from persistence.db import db_conn, db_release
from protocol.frame import w_u8, w_u16, w_u32

log = runtime.log

# ── 配置加载（惰性 + 进程内缓存）──────────────────────────────────────────
_LIVE_ORDER_PATH = os.path.join(runtime.HERE, '_partner_base.json')          # 53 标量+顺序
_RICH_PATH = os.path.join(runtime.HERE, 'cfg', 'config_partner_base.json')   # 成长曲线

_live_list = None       # [ {bid,name,score,color,is_deity,innate_skill,...}, ... ] 实机上屏顺序
_levup = None            # {int(lev): {'exp_max':int,'exp_total':int}}
_const = None            # {'lev_max':int, ...}

# # INFERENCE: 培养单次消耗/收益（config 无真值，替换点）。
#   原版伙伴培养吃"伙伴经验丹"道具，本单机服改用 gold 代替，便于闭环验证。
FEED_GOLD = 1000        # 每次培养扣 gold（INFERENCE）
FEED_EXP = 500          # 每次培养加 exp（INFERENCE）
# # INFERENCE: 每升 1 级伙伴折算给玩家的属性贡献系数（替换点，等 V8 实机标定）。
GROW_DELTA_RATIO = {'atk_s': 0.01, 'def_s': 0.01, 'hp_max': 0.02}


def _load():
    """惰性加载两份配置。幂等；失败降级为空，绝不影响起服。"""
    global _live_list, _levup, _const
    if _live_list is not None:
        return
    # 面板标量（实机已验证的 53 条顺序）
    try:
        with open(_LIVE_ORDER_PATH, encoding='utf-8') as f:
            _live_list = json.load(f) or []
    except Exception as e:
        _live_list = []
        log('server.log', '!! partner live order load failed: %r' % (e,))
    # 成长曲线（rich config）
    _levup = {}
    _const = {}
    try:
        with open(_RICH_PATH, encoding='utf-8') as f:
            d = json.load(f)
        for lv, vv in (d.get('PartnerLevUp') or {}).items():
            h = (vv or {}).get('hash') or {}
            try:
                _levup[int(lv)] = {'exp_max': int(h.get('exp_max') or 0),
                                   'exp_total': int(h.get('exp_total') or 0)}
            except Exception:
                pass
        cc = (d.get('PartnerConstant') or {}).get('hash') or {}
        for k, vv in cc.items():
            h = (vv or {}).get('hash') or {}
            try:
                _const[k] = int(h.get('val') or 0)
            except Exception:
                pass
    except Exception as e:
        log('server.log', '!! partner rich cfg load failed: %r' % (e,))


def lev_max():
    _load()
    return int(_const.get('lev_max') or 200)


def exp_max_for(lev):
    """该等级升到下一级所需 exp（CONFIRMED PartnerLevUp）；越界/缺省回退保守值。"""
    _load()
    row = _levup.get(int(lev))
    if row and row.get('exp_max'):
        return int(row['exp_max'])
    # # INFERENCE: 缺档回退（替换点）
    return 100 + int(lev) * 20


# ── role_heros 读写（独立实现，不 import mock_server）─────────────────────
def owned_map(rid):
    """该角色已拥有伙伴 {bid: {bid,color,lev,exp,state,chip}}。"""
    try:
        con = db_conn()
        rows = con.execute(
            'SELECT bid,color,lev,exp,state,chip FROM role_heros WHERE rid=? ORDER BY bid',
            (int(rid),)).fetchall()
        db_release(con)
        out = {}
        for r in rows or []:
            out[int(r[0])] = {'bid': int(r[0]), 'color': int(r[1] or 0),
                              'lev': int(r[2] or 1), 'exp': int(r[3] or 0),
                              'state': int(r[4] or 0), 'chip': int(r[5] or 0)}
        return out
    except Exception as e:
        log('tcp.log', '  !! partner.owned_map failed: %r' % (e,))
        return {}


def _set_hero_level(rid, bid, lev, exp):
    try:
        con = db_conn()
        con.execute('UPDATE role_heros SET lev=?, exp=? WHERE rid=? AND bid=?',
                    (int(lev), int(exp), int(rid), int(bid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! partner._set_hero_level failed: %r' % (e,))
        return False


# ── 闭环 1：面板编码器（与旧链逐字段一致）────────────────────────────────
def build_panel_11215(rid):
    """SC_11215 伙伴面板。

    ★ S2 项③（2026-10-15）docstring 误归因更正（依据 docs_raw/s2_a_findings.md §2.3）：
      旧版 PHASE 2.24 注释把「`volume:u8 + volume_open:u8 + partner_bag:table + gratis:table`」
      错挂为 **1.4.11 的 SC_11215 权威格式**。经 cmd_resolve_112.luac 字节码级反汇编
      （1.4.11 = proto #37；1.3.0 旁证）逐 proto 核对，该格式串实际注册在：
        · **SC_11200（伙伴仓库包，proto #0）** = volume:u8, volume_open:u8,
          partner_bag:table{id@I##bid@I##…6 个 D|Dsc11200*|…}, gratis:table{bid:u8,type:u8}；
        · **SC_11206（容量应答，proto #23）** = code:u8, msg:string, volume:u8, volume_open:u8。
      而 **SC_11215 = `partner_list:table{…}`，直接以表计数(u16)开头，三源
      （fields.json / proto_defs.py / 1.4.11 luac proto#37 / 1.3.0 luac）逐字段一致，
      无 volume/volume_open 前缀**。本客户端按登录体长启发式判 1.4.9（runtime.CUR_VER），
      1.3.0/1.4.9/1.4.11 三版 SC_11215 格式完全相同 ⇒ **不做版本分支**。
      旁证：客户端 `hero_equip_data.luac` 的 `storagePartnerList(data)` 按
      data.volume/volume_open/partner_bag/gratis 取值 —— 那是**读 11200 仓库包**，
      不是 11215 面板。
      ⇒ 本函数正确实现 = `w_u16(len(base)) + 行序列`（无前缀），与 S1-B 运行时结论一致；
        下方 S1-B 注释保留。volume/volume_open 前缀的实现见 mock_server.py 的 11200/11206 分支
        （本函数不发该前缀）。
    """
    _load()
    base = _live_list or []
    owned = owned_map(rid)
    # ★ S1-B 修正：本客户端为 1.4.9（runtime.CUR_VER='1.4.9'），其权威规格
    #   fields.json `SC_11215` = **`partner_list:table` 直接以表计数(u16)开头**，
    #   **没有** volume/volume_open 前缀。
    #   旧实现按 1.4.11 luac（`volume__C##volume_open__C##partner_bag__T`）补了
    #   w_u8(volume)+w_u8(volume_open) 两字节前缀 ⇒ 1.4.9 客户端把这两字节并进
    #   表计数、且后续每个条目整体错位 2 字节 ⇒ 解析越界 ⇒ LUA ERROR [11215]
    #   （经 CS_10999 上报）。实机帧长亦印证：注释基线 2552 body = 2+53×48，
    #   而旧码发 2554（多 2 字节前缀）⇒ 即此错位。
    #   修复：去掉 volume/volume_open 两字节，只发 w_u16(计数)，与 fields.json 对齐。
    out = w_u16(len(base))               # partner_list 表计数（1.4.9 规格，无前缀）
    for p in base:
        _pb = int(p.get('bid', 0))
        _is_own = _pb in owned
        _h = owned.get(_pb) or {}
        _lev = int(_h.get('lev') or 1) if _is_own else 1
        out += (w_u32(_pb if _is_own else 0) +      # id（已拥有=bid，未拥有=0）
                w_u32(_pb) +
                w_u8(2 if int(p.get('is_deity') or 0) == 1 else 1) +
                w_u8(int(p.get('color', 0)) & 0xff) +
                w_u32(0) +                           # lifttime
                w_u8(_lev & 0xff) +                  # lev
                w_u32(0) +                           # exp
                w_u16(0) +                           # grow
                w_u32(int(p.get('score', 0))) +      # score
                w_u8(0) + w_u8(0) + w_u8(0) +        # stage/rebirth/acc
                w_u16(0) +                           # partner_attr 空
                w_u32(int(p.get('score', 0))) +      # power
                w_u16(0) +                           # aptitude 空
                w_u32(int(p.get('innate_skill', 0))) +
                w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0))   # skill/jindan/talisman/ext 空
    return out


# ── 闭环 2：培养（升级）──────────────────────────────────────────────────
def _attr_growth_delta(up_levels, score):
    """# INFERENCE: 升 up_levels 级伙伴折算给玩家的属性增量（替换点，等 V8 标定）。

    无配置真值给出"每级伙伴 -> 玩家属性"映射，这里用 score 做规模的保守占位。
    """
    base = max(0, int(score or 0))
    return {
        'atk_s': int(base * GROW_DELTA_RATIO['atk_s']) * up_levels,
        'def_s': int(base * GROW_DELTA_RATIO['def_s']) * up_levels,
        'hp_max': int(base * GROW_DELTA_RATIO['hp_max']) * up_levels,
    }


def feed(rid, bid, times=1):
    """培养伙伴 times 次。返回结果 dict（供 handler / GM 端点用）。

    流程：校验拥有 → 幂等扣 gold(CurrencyService.db_add_assets 负数) → 加 exp →
    按 PartnerLevUp 连升 → 属性贡献 apply_delta → 返回 before/after。
    """
    from currency.service import db_get_assets, db_add_assets
    from attribute.service import apply_delta
    from power.service import power_of

    _load()
    bid = int(bid)
    times = max(1, int(times))
    owned = owned_map(rid)
    h = owned.get(bid)
    if not h:
        return {'ok': False, 'err': 'partner_not_owned', 'bid': bid}

    cost = FEED_GOLD * times
    assets = db_get_assets(rid)
    gold_now = int(assets.get('gold') or 0)
    if gold_now < cost:
        return {'ok': False, 'err': 'not_enough_gold', 'need': cost, 'have': gold_now}

    # 扣货币（CurrencyService，负数即消费；role_assets 幂等行）
    db_add_assets(rid, {'gold': -cost})

    lev = int(h['lev'])
    exp = int(h['exp']) + FEED_EXP * times
    lmax = lev_max()
    up = 0
    while lev < lmax:
        need = exp_max_for(lev)
        if exp < need:
            break
        exp -= need
        lev += 1
        up += 1
    _set_hero_level(rid, bid, lev, exp)

    # 属性贡献（INFERENCE）→ 重算战力
    delta = _attr_growth_delta(up, _score_of(bid))
    if up > 0 and delta:
        apply_delta(rid, delta)
    log('tcp.log', '  ** partner.feed rid=%d bid=%d x%d gold -%d lev %d->%d exp=%d up=%d'
        % (rid, bid, times, cost, h['lev'], lev, exp, up))
    return {'ok': True, 'bid': bid, 'gold_spent': cost, 'lev_before': h['lev'],
            'lev_after': lev, 'exp': exp, 'up_levels': up,
            'attr_delta': delta, 'power_after': power_of(rid)}


def _score_of(bid):
    _load()
    for p in (_live_list or []):
        if int(p.get('bid') or 0) == int(bid):
            return int(p.get('score') or 0)
    return 0


# ①c G2 CONFIRMED: 伙伴神器/符咒/羁绊消耗（config_partner_base.json）。
_PARTNER_CFG = os.path.join(runtime.HERE, 'cfg', 'config_partner_base.json')
def partner_shenqi_cost(lev):
    """伙伴神器金币消耗（CONFIRMED：L1=2400 L2=4400 L3=6400 L4=12000 L5=18000）。"""
    _t = {1:2400, 2:4400, 3:6400, 4:12000, 5:18000}
    return _t.get(int(lev), 18000)
def partner_talisman_cost(lev):
    """伙伴符咒 hc 消耗（CONFIRMED：L1=10000 L2=20000 L3=30000 L4=40000）。"""
    _t = {1:10000, 2:20000, 3:30000, 4:40000}
    return _t.get(int(lev), 40000)
FETTER_EXP_RATIO = 600   # ①c CONFIRMED 羁绊经验比（FetterConst.exp_ratio）
