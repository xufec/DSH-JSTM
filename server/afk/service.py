# -*- coding: utf-8 -*-
"""afk 包 —— 挂机（AFK）状态 + 收益累积 + 幂等领取（Phase 10）。

禁止 `import mock_server`。
挂机进度持久化：复用 `dungeon_progress` KV 表（ptype='afk'）。
收益：exp/gold 随挂机时长累积；数值无配置真值 ⇒ # INFERENCE 替换点。
领取：RewardService.grant(reference_id='afk:<rid>:<session>') 幂等，重复领取被 reward_log 拦截。
"""

import json
import os
import time

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

# # INFERENCE：挂机每分钟收益（替换点，等挂机收益表实取）。
#
# ★ 2026-10-16（C5-C）**取证定案：收益速率表在客户端侧根本不存在**，因此这组值
#   **只能**是占位推断，永远不要当"原版真值"引用。已核过的范围：
#     · `config_guaji.luac`（1.4.11 原始字节码）可打印字符串只有
#       `mon_bid / disc / lev_l / map_bid / lev_r / show / GuajiInfo / GuajiMapList`
#       —— 1.3.0 版字节串完全一致，**两版都没有收益字段**；
#     · 4 份 `config_guaji.json` 变体（cfg / cfg.bak_r192 / cfg_kconfig / cfg_kconst）
#       同样只有 5–6 个字段；
#     · APK 全量配置清单（355 条 `assets/src/config/*`）中匹配 off/gua/hang/afk/live 的
#       只有 `config_guaji / config_live / config_richang / config_exchange`，
#       **不存在** `config_offline*` / `config_hangup*` / `config_afk*`；
#     · 字段名扫描 `per_min|exp_per|off_exp|guaji_exp|per_hour|hour_exp|min_exp|
#       award_per|off_award|off_reward|hangup`（全 server/**/*.json）→ 零命中；
#     · 实机挂机面板（`analysis/runtime_evidence/shots/afk_05_afkpanel.png` 等 3 张）
#       只显示 地图名/等级段/`双倍点数`/`自动巡逻`，**没有任何收益数值预览**。
#   ⇒ 结论：收益由**服务端权威**计算、客户端只渲染 ⇒ "在客户端配置里找收益表"是范畴错误。
#     要拿真值只能**真服抓包**（10932/10933/10934 开关帧 + 10931 领取回包）。
#
# ★ 因此这三个数改为**可从 config.json 覆盖**（见下方 `_rate()`）：
#   拿到真值后**只改配置、不动代码**；默认值仍是原占位，语义不变。
GOLD_PER_MIN = 200
EXP_PER_MIN = 100
# 单次挂机领取上限分钟数（防刷）。
MAX_MIN = 480


def _rate(key, default):
    """从运行配置取速率（C5-C 新增）。配置缺失/非法 ⇒ 回退占位默认值。

    为什么不是硬编码常量：占位值一定会在拿到真值后被替换，
    留一个**配置旋钮**就不必再改代码、也不会漏掉某一处调用点。
    """
    try:
        v = runtime.CFG.get(key)
        return int(v) if v is not None else int(default)
    except Exception:
        return int(default)


def gold_per_min():
    return _rate('afk_gold_per_min', GOLD_PER_MIN)


def exp_per_min():
    return _rate('afk_exp_per_min', EXP_PER_MIN)


def max_min():
    return _rate('afk_max_min', MAX_MIN)

_GUAJI = os.path.join(runtime.HERE, 'cfg', 'config_guaji.json')

def zones():
    """挂机地图列表（①c CONFIRMED：config_guaji.json GuajiInfo 8 区）。"""
    try:
        with open(_GUAJI, encoding='utf-8') as f:
            g = json.load(f).get('GuajiInfo') or {}
        out = []
        for k, v in g.items():
            h = (v or {}).get('hash') or v or {}
            out.append({'id': int(h.get('id') or k), 'name': h.get('name') or '',
                        'map_bid': int(h.get('map_bid') or 0)})
        return out
    except Exception as e:
        log('server.log', '!! guaji zones load failed: %r' % (e,))
        return []


def _kv_get(rid, ptype, pkey, default=0):
    con = db_conn()
    r = con.execute('SELECT value FROM dungeon_progress WHERE rid=? AND ptype=? AND pkey=?',
                    (int(rid), ptype, str(pkey))).fetchone()
    db_release(con)
    return int(r[0]) if r is not None else int(default)


def _kv_set(rid, ptype, pkey, value):
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
                (int(rid), ptype, str(pkey), int(value)))
    con.commit()
    db_release(con)


def enter(rid):
    """进入挂机会话：记录开始时间戳（已在挂机则不重置）。"""
    cur = _kv_get(rid, 'afk', 'start', 0)
    if cur:
        return {'ok': True, 'already': True, 'started_at': cur}
    now = int(time.time())
    _kv_set(rid, 'afk', 'start', now)
    _kv_set(rid, 'afk', 'claimed', 0)
    log('tcp.log', '  ** afk.enter rid=%d start=%d' % (rid, now))
    return {'ok': True, 'already': False, 'started_at': now}


def status(rid):
    start = _kv_get(rid, 'afk', 'start', 0)
    claimed = _kv_get(rid, 'afk', 'claimed', 0)
    mins = 0
    if start and not claimed:
        mins = max(0, min(max_min(), int((time.time() - start) // 60)))
    return {'start': start, 'claimed': bool(claimed), 'minutes': mins,
            'pending_gold': mins * gold_per_min(), 'pending_exp': mins * exp_per_min(),
            # ★ C5-C：把**实际生效的速率**一并回出，便于运维判断"当前用的是配置值还是默认占位"
            'rate': {'gold_per_min': gold_per_min(), 'exp_per_min': exp_per_min(),
                     'max_min': max_min(), 'source': 'config.json 或 # INFERENCE 默认占位'}}


def patrol_kills(rid, minutes=None):
    """任务1: 挂机巡逻模拟击杀最小闭环（服务端）。每分钟打1只 20003 掉落组。
    奖励经 grant 幂等 ref=afk_kill:<rid>:<start>。场景传送视觉待接，此处补结算。"""
    from reward.service import grant
    from drop import service as drop_svc
    start = _kv_get(rid, 'afk', 'start', 0)
    claimed = _kv_get(rid, 'afk', 'claimed', 0)
    if not start or claimed:
        return {'ok': False, 'err': 'no_session_or_claimed'}
    mins = minutes if minutes is not None else status(rid)['minutes']
    n = max(1, int(mins))
    awards = []
    for _ in range(n):
        r = drop_svc.resolve(20003)
        if r.get('coin'):
            awards.append({'kind': 'asset', 'code': 'gold', 'amount': r['coin']})
        for bid, num in r.get('items', []):
            awards.append({'kind': 'item', 'bid': bid, 'amount': num})
    ref = 'afk_kill:%d:%d' % (int(rid), start)
    res = grant(int(rid), awards, ref, source='afk_patrol')
    log('tcp.log', '  ** afk.patrol rid=%d kills=%d awards=%d already=%s ref=%s' % (rid, n, len(awards), res.get('already'), ref))
    return {'ok': True, 'kills': n, 'n_awards': len(awards), 'already': res.get('already')}

def claim(rid):
    """领取挂机收益（幂等）。已领过 ⇒ already=True，不重复发。"""
    from reward.service import grant

    st = status(rid)
    if not st['start']:
        return {'ok': False, 'err': 'not_in_afk'}
    if st['claimed']:
        return {'ok': False, 'err': 'already_claimed', 'minutes': 0}
    mins = st['minutes']
    if mins <= 0:
        return {'ok': False, 'err': 'no_elapsed', 'minutes': 0}

    awards = [{'kind': 'asset', 'code': 'gold', 'amount': mins * gold_per_min()},
              {'kind': 'asset', 'code': 'exp', 'amount': mins * exp_per_min()}]
    ref = 'afk:%d:%d' % (int(rid), st['start'])
    res = grant(int(rid), awards, ref, source='afk_claim')
    _kv_set(rid, 'afk', 'claimed', 1)
    log('tcp.log', '  ** afk.claim rid=%d mins=%d gold+%d exp+%d already=%s ref=%s'
        % (rid, mins, mins * gold_per_min(), mins * exp_per_min(), res.get('already'), ref))
    return {'ok': True, 'minutes': mins, 'gold': mins * gold_per_min(),
            'exp': mins * exp_per_min(), 'already': res.get('already')}


# ── C5-C：离线挂机会话（CS 10933 开 / 10934 关 那条链）──────────────────────
#
# ★ 为什么单独一组函数：本服**有两条互不相通的挂机状态**——
#     (a) `dungeon_progress` KV `ptype='afk'`：`afk.enter/status/claim` 这条链
#         （GM `/DSH_ADMIN/afk_*` 在用，客户端并**不**走）；
#     (b) `guaji_state.off_on / off_started_at`：客户端**离线挂机开关** 10933/10934 落的
#         （C3.3-D 实现，`off_started_at` 明确是"服务端时间戳、防回拨锚点"）。
#   以前 (b) 只存状态、**从不结算**——开着离线挂机也不产生任何收益，
#   而 (a) 的速率又是硬编码常量，两边口径还可能不一致。
#   现在：把 (b) 的时长算出来，**复用 (a) 的同一组速率函数**，并提供幂等结算。
#
# ⚠ 仍未取证 / 不编造的部分（保持 BLOCKED）：
#   · **速率真值**：见文件头 C5-C 取证定案，客户端侧不存在收益表 ⇒ 只能是占位推断；
#   · **客户端领取入口**：疑似 `10931`（字段仅 {code,msg}），未注册、未观测到任何帧
#     ⇒ **不实现**客户端领取，只在 GM/运维面提供显式结算，避免凭空发明玩家侧流程。


def offline_status(rid, off_on, off_started_at):
    """离线挂机会话的**累计**收益预览（只读，不发奖）。"""
    _on = int(off_on or 0)
    _st = int(off_started_at or 0)
    mins = 0
    if _on and _st:
        mins = max(0, min(max_min(), int((time.time() - _st) // 60)))
    return {'on': _on, 'started_at': _st, 'minutes': mins,
            'pending_gold': mins * gold_per_min(),
            'pending_exp': mins * exp_per_min(),
            'rate': {'gold_per_min': gold_per_min(), 'exp_per_min': exp_per_min(),
                     'max_min': max_min(),
                     'source': 'config.json 或 # INFERENCE 默认占位（客户端无收益表）'}}


def offline_claim(rid, off_on, off_started_at):
    """结算**一次**离线挂机收益（幂等）。

    幂等键 = `afk_off:<rid>:<off_started_at>`：同一段离线会话重复结算会被
    `reward_log` 主键挡住（`already=True`，不再发奖）。
    ⚠ 已知取舍：同一段 `off_started_at` 内**只结算一次**；玩家若"结算后继续离线"，
    需要先关再开（10934→10933）产生新的 `off_started_at` 才会重新计时。
    这是为避免"重复领取"而选的**保守**语义，原版真实语义未取证。
    """
    from reward.service import grant
    _on = int(off_on or 0)
    _st = int(off_started_at or 0)
    if not _on or not _st:
        return {'ok': False, 'err': 'no_offline_session'}
    mins = max(0, min(max_min(), int((time.time() - _st) // 60)))
    if mins <= 0:
        return {'ok': False, 'err': 'no_elapsed', 'minutes': 0}
    awards = [{'kind': 'asset', 'code': 'gold', 'amount': mins * gold_per_min()},
              {'kind': 'asset', 'code': 'exp', 'amount': mins * exp_per_min()}]
    ref = 'afk_off:%d:%d' % (int(rid), _st)
    res = grant(int(rid), awards, ref, source='afk_offline')
    log('tcp.log', '  ** afk.offline_claim rid=%d mins=%d gold+%d exp+%d already=%s ref=%s'
        % (rid, mins, mins * gold_per_min(), mins * exp_per_min(),
           res.get('already'), ref))
    return {'ok': True, 'minutes': mins, 'gold': mins * gold_per_min(),
            'exp': mins * exp_per_min(), 'already': res.get('already'), 'ref': ref}
