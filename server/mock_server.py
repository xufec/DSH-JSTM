#!/usr/bin/env python3
"""Phase-2 mock server for 《绝世唐门》 (com.shiyue.dldl).

Serves everything the patched client asks for on startup, and captures raw
TCP traffic so the native wire format can be determined empirically:

  HTTP  GET  /update/config/url_config_ewan.lua   -> url_config_ewan.lua (CDN 替代)
  HTTP  GET  /notice.json                          -> 公告
  HTTP  POST /gateway/mobile/json  /app/mobile/json -> 服务器列表
  HTTP  GET  /cdn/*                                -> server/cdn/ 下的静态文件
  TCP   :game_port                                 -> 记录客户端发来的原始字节

Usage:
    python server/mock_server.py                # 用 server/config.json
    python server/mock_server.py --http 8080 --game 9000 --host 192.168.1.10

Everything is appended to server/logs/ ; raw TCP frames are also saved as
server/logs/tcp_<n>.bin for offline analysis.
"""
# ============================================================================
# MOCK_SERVER 导航（tools/r1b_add_nav_header.py 生成，人工可改）
# ============================================================================
#
# 【这是什么】《绝世唐门》私服的游戏服务端。单进程 Python，**纯标准库零依赖**。
#   TCP 9000  = 游戏协议 [u32 BE len][u16 BE cmd][body]
#   HTTP 8080 = 资源面 + /DSH_ADMIN 管理面 + /GM 后台管理页面
#
# 【主线怎么读】
#   ① class Handler → handle()      TCP 主循环：收帧 → FrameParser → 分发
#   ② 主分发链      if cmd == N / if cmd in (...)    约 376 个分支
#   ③ 分支用到的东西 build_*() 组帧 ｜ db_*() 存取 ｜ mission_*/scene_*/battle_* 业务
#   ④ 兜底          global_default_sc  ★ 必须在所有专用分支**之后**（否则抢走全部）
#   ⑤ HTTP 侧       Handler.do_GET：/GM→gm.console ｜ /DSH_ADMIN/*→管理面 ｜ 其余→资源
#
# 【分区骨架（行号会漂移，以 banner 搜索为准）】
#      A 文件头 / 导入 / 全局变量                                  L1–L120
#      B 场景与 AOI 基础件（_scene_* / push_to_rid）              L121–L600
#      C HTTP Handler：管理面 + 资源面                           L601–L2600
#      D 协议底座：编码器 / 字段 / 默认响应                             L2601–L7000
#      E 业务辅助：db_* / build_* / mission_* / scene_*        L7001–L9800
#      F TCP 主处理：分发主链（最大的区）                               L9801–L17200
#      G 战斗 / 挂机 / 场景内链（200xx / 154xx）                    L17201–L18300
#      H 登录 / 活动 / 邮件 / 伙伴 / 场景重推                         L18301–L20000
#      I 全局兜底 global_default_sc + main()                  L20001–L20337
#
# 【改之前必看】
#   · 新增专用分支后，确认它**不在** _GENERIC_DEFAULT_CMDS 或任何 cmd in (...) 元组里，
#     否则会被全局兜底抢先命中。门禁：python tools/lint_dispatch_shadow.py
#   · .get(k, default) 对「键存在但值为 None」返回 None —— 曾导致定时器异常刷屏。
#   · CS body 尾部有 4 字节缓冲区脏数据：**只读规格前 N 字节**。
#   · code == 1 才是成功；**唯一例外 10200 要 code == 0**。
#   · 服务端下发的 ID 必须校验存在性（曾因发不存在的 skill bid 1001 让客户端崩）。
#
# 【篇幅实况（供后续整理参考）】
#   本文件 20378 行，其中注释 4535 行；**连续注释块 ≥5 行者 3341 行（284 块）**，
#   主体是「已下沉到 server/<pkg>/ 后仍以注释留档」的副本（含 [P2X-migrated] 标记）。
#   实测：这些块与**活代码/活注释交错**，整块移除会破坏缩进归属 ⇒ 维持现状。
#   结构全图：docs/mock_server_结构图.md
# ============================================================================

import argparse, json, os, socket, socketserver, sqlite3, struct, sys, threading, time, traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
LOGDIR = os.path.join(HERE, 'logs')
CFG_PATH = os.path.join(HERE, 'config.json')

sys.path.insert(0, HERE)
try:
    from proto_defs import BY_CMD, MESSAGES   # noqa
except Exception:
    BY_CMD, MESSAGES = {}, {}

# ★ Phase D：战斗最小垂直闭环（协议编码全部按 1.4.9 字节码，见 server/battle.py）
try:
    import battle as battle_mod
except Exception:                                     # 允许缺文件时降级
    battle_mod = None
# ★ Phase 2 step 0：命令分发表兼容层（server/core/dispatch.py）。
#   DISPATCH_TABLE 当前为空 ⇒ 所有命令 100% 走旧 if 链，行为与拆分前字节级一致。
#   import 失败绝不影响起服（降级 None，_reply 里判空）。
try:
    import core.dispatch as dispatch
except Exception as _e_dispatch:
    dispatch = None

# ★★★ Phase 2 step 1：core/protocol/persistence/config 搬家接线（2026-10-02）★★★
#   以下实现已原样搬入拆分模块，mock_server 这里改为**导入**；旧定义在原处注释保留
#   （块首标 # [P2B-migrated] <目标>），行为字节级不变。
#   新模块禁止 import mock_server（循环 import 红线，设计 §九 风险 1）。
from core import runtime                                   # 单例运行时（CFG/LIVE/CUR_VER/log/ver_family_of）
from core.runtime import CFG, LIVE_CONNECTIONS, LIVE_LOCK, log
from protocol.frame import w_u8, w_u16, w_u32, w_str, pack_frame, FrameParser
from protocol.fields import _sc_fields, _sc_w, encode_by_sc_with_echo
from protocol.fields import has_sc_definition as _fields_has_sc   # ★ 2026-10-17：SC 定义判定的唯一入口
from persistence.db import db_conn, db_release, db_init, DB_PATH, STATE_DIR
from config.loader import (kconst_count, kconst_rows, kconst_str, kconst_int,
                           kcfg, kcfg2_rows)

# ★★★ Phase 2 step 2/3：account/role/attribute/currency/level/power 搬家接线 ★★★
#   re-import 已搬家实现（供残留调用点），并 import handler 触发 @register。
from role.storage import (db_get_role, db_save_role, role_state,
                          build_10301, build_10302, build_10303)
from currency.service import db_get_assets, db_add_assets, db_set_assets
from level.service import (add_role_exp)
from attribute.service import (db_role_attr, db_get_attr, role_attr_dict,
                               role_power, attr_table_10306,
                               attr_row_bytes)  # [P3deep-migrated]
from power.service import power_of as role_power_of
import account.service    # noqa: F401  注册 1110 / 10101
import role.handler       # noqa: F401  注册 10301 / 10302 / 10303
import attribute.handler  # noqa: F401  注册 10304 / 10306

# ★★★ Phase 2c：currency(收口)/reward/item/inventory 搬家接线 ★★★
from item.service import item_cfg, item_name, item_ids, is_valid_item
from inventory.service import (BAG_MAIN, STORAGE_CODE, db_bag_get, db_store_get,
                               db_init_equip, db_equip_all, db_store_init,
                               build_equip_items, build_bag_items, db_bag_add)   # ★ 2026-10-17：10511 换装用（原来未定义）
# ★★ 2026-10-17：背包容量 + SC_10510「格子最大值」下沉到 inventory.service
#   （10502 的 handler 在 inventory/handler.py，而本包禁止它反向 import mock_server）
from inventory.service import (db_init_bag_volume, db_get_bag_volume, db_set_bag_volume,
                               push_10510, push_10503, push_10508)
from reward.service import grant
from task.service import db_get_missions  # [P3deep-migrated]
from task.service import db_save_mission  # [P3deep-migrated]
from task.service import mission_cfg, mission_def  # [P3deep-migrated]
from task.service import mission_chain  # [P3deep-migrated]
from task.service import mission_rows  # [P3deep-migrated]
from scene.service import (quest_spawn, scene_elems, scene_npcs, scene_mons,
                             guaji_spots, map_def_xy, guaji_spot_for_lev)  # [P3deep-migrated]
import inventory.handler  # noqa: F401  注册 10502
# ★★★ Phase 2d：task/scene/npc/battle_service 搬家接线 ★★★
from task.service import build_mission_entry, build_12400  # 编码器重导出（旧块仍用）
import task.handler    # noqa: F401  注册 12408
import equipment.handler  # noqa: F401  注册 10601/10610/10651
import scene.handler   # noqa: F401  注册 10200
import npc.handler     # noqa: F401  注册 15203
import battle_service  # noqa: F401  battle.py 重导出（数值不接线）
# ★★★ Phase 8：partner/skill 垂直闭环接线（注册 11215 / 10622）★★★
try:
    import partner.handler  # noqa: F401  注册 11215 伙伴面板
    import skill.handler    # noqa: F401  注册 10622 已学技能列表
    import growth.handler   # noqa: F401  注册 11600 翅膀面板（② 解耦真表）
    import answer.handler   # noqa: F401  注册 16100/16101/16102/16103 答题活动
    import growth_target.handler  # noqa: F401  注册 30500/30501/30502 开服成长计划
    import scratch.handler  # noqa: F401  注册 16651/16652 刮刮乐
    import friend.handler  # noqa: F401  注册 13300/13321/13303/13305 好友系统
except Exception as _p8e:    # 软降级：绝不因新模块 import 失败拖垮起服
    print('[P8] partner/skill handler import failed (fallback old chain): %r' % (_p8e,))
# ★ 10304 角色属性 + 战力大包的 24 项属性键顺序（来自 SC_10304 定义）
ATTR_KEYS = ['strength', 'intellect', 'armor', 'constiution', 'atk_s', 'atk_p',
             'def_s', 'def_p', 'hp_max', 'atk_speed', 'hit', 'dodge',
             'crit', 'tenacity', 'red_def_s', 'red_def_p',
             'atk_abs', 'def_abs', 'reduce', 'hurt', 'hit_rate_show',
             'dodge_rate_show', 'crit_rate_show', 'tenacity_rate_show']
# ★ 属性缺省值（10304 与 12901 战力榜共用；待等级成长公式确认后可替换）
ATTR_DEFAULTS = {
    'strength': 50, 'intellect': 50, 'armor': 100, 'constiution': 50,
    'atk_s': 120, 'atk_p': 100, 'def_s': 80, 'def_p': 75,
    'hp_max': 3000, 'atk_speed': 100, 'hit': 20, 'dodge': 20,
    'crit': 10, 'tenacity': 10, 'red_def_s': 0, 'red_def_p': 0,
    'atk_abs': 0, 'def_abs': 0, 'reduce': 0, 'hurt': 0,
    'hit_rate_show': 0, 'dodge_rate_show': 0,
    'crit_rate_show': 0, 'tenacity_rate_show': 0,
}






# ★★ R43：SC_10306 的 attr 条目类型与 SC_10304 **不同**（权威 spec 逐项核对）：
#     SC_10304: HHHH + 20×I                ⇒ 条目 88B
#     SC_10306: HHHH + 12×I + HHHH + 4×I   ⇒ 条目 80B
#   即 10306 里 `atk_abs / def_abs / reduce / hurt` 是 **u16**。
#   ⚠ 曾直接复用 10304 的 `ATTR_KEYS[:4] / [4:]` 切分 ⇒ 10306 应答**多 8 字节**，
#     客户端会把 `mspd`/`power` 读错（与 round40 的 `12931` 同一类错误：**同族≠同构**）。
#   ⇒ 两个消息各自有编码器，**不共用切分**。


# ★ 2026-09-18 第二阶段：AOI + 寻路（自研，见 analysis/server_reference/R1_SUPPLEMENT.md）
try:
    import aoi as aoi_mod
except Exception as _e:  # pragma: no cover
    aoi_mod = None
    print('!! aoi import failed: %r' % (_e,))
try:
    import power as power_mod
except Exception as _e:
    power_mod = None
    print('!! power import failed: %r' % (_e,))
try:
    import pathfind as pathfind_mod
except Exception as _e:  # pragma: no cover
    pathfind_mod = None
    print('!! pathfind import failed: %r' % (_e,))

DEFAULT_CFG = {
    "bind": "0.0.0.0",
    "host": "127.0.0.1",
    "http_port": 8080,
    "game_port": 9000,
    "server_list": [
        {"id": "1", "name": "本地私服", "ip": "127.0.0.1", "port": 9000,
         "state": 1, "is_new": 1, "world_lev": 1}
    ],
    "notice": "本地私服测试",
    "lua_response": False
}


# [P2B-migrated core/runtime.py::log] def log(name, text):
# [P2B-migrated core/runtime.py::log]     os.makedirs(LOGDIR, exist_ok=True)
# [P2B-migrated core/runtime.py::log]     line = '[%s] %s\n' % (time.strftime('%H:%M:%S'), text)
# [P2B-migrated core/runtime.py::log]     sys.stdout.write(line)
# [P2B-migrated core/runtime.py::log]     sys.stdout.flush()
# [P2B-migrated core/runtime.py::log]     with open(os.path.join(LOGDIR, name), 'a', encoding='utf-8') as f:
# [P2B-migrated core/runtime.py::log]         f.write(line)


# Phase 2 step 0：把本服 log() 接给 dispatch 兼容层（handler 异常落 dispatch.log）
if dispatch is not None:
    try:
        dispatch.set_logger(log)
    except Exception:
        pass


def hexdump(data, annotate=True):
    out = []
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        h = ' '.join('%02x' % b for b in chunk)
        a = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        out.append('  %04x  %-47s  %s' % (i, h, a))
    if annotate and len(data) >= 4:
        # best-effort: many such frameworks put a little-endian ushort cmd early
        for off in (0, 2, 4, 6):
            if off + 2 <= len(data):
                cmd = data[off] | (data[off + 1] << 8)
                if cmd in BY_CMD:
                    names = BY_CMD[cmd]
                    out.append('  ** possible cmd=%d @offset %d -> %s'
                               % (cmd, off, ', '.join(names[:4])))
    return '\n'.join(out)


def normalize_server_item(s, cfg):
    """把 config.json 里的简写条目展开成客户端真正会读的字段。

    字段清单来自 denglu_mgr.luac proto[8] 的逐指令反汇编（每个键都对应一条
    TGETS），以及各字段缺省时的回退分支：

        name        <- 缺省回退 srv_name
        srv_id      <- 缺省回退 platform .. '_' .. zone_id
        main_srv_id <- 缺省回退 main_platform .. '_' .. main_zone_id
        port        <- 缺省回退 erl_port
        host / platform_flag    缺省为 ''
        can_create_role         缺省为 1
        isClose  = (maintain ~= 0)
        isTry    = tonumber(first_zone or '0') ~= 0
        isRecomed/ isNew        由 recomed / isnew 得来
        open_time <- 缺省回退 begin_time
    """
    plate = str(s.get('platform') or s.get('platform_flag_platform')
                or cfg.get('platform', 'ewan'))
    zone = str(s.get('zone_id', s.get('id', '1')))
    sid = str(s.get('srv_id') or s.get('id') or ('%s_%s' % (plate, zone)))
    name = s.get('srv_name') or s.get('name') or ('S%d' % zone)
    port = int(s.get('port', 9000))
    return {
        'srv_id': sid,
        'srv_name': name,
        'name': name,                      # 源码优先读 name，回退 srv_name
        'ip': s.get('ip', '127.0.0.1'),
        'port': port,
        'erl_port': port,                  # 与 port 同值，命中回退分支也无害
        'host': s.get('host', ''),
        'platform': plate,
        'zone_id': zone,
        'main_platform': s.get('main_platform', plate),
        'main_zone_id': str(s.get('main_zone_id', zone)),
        'main_srv_id': s.get('main_srv_id', '%s_%s' % (plate, zone)),
        'platform_flag': s.get('platform_flag', ''),
        'can_create_role': int(s.get('can_create_role', 1)),
        'maintain': int(s.get('maintain', 0)),        # 0 => isClose = false
        'first_zone': int(s.get('first_zone', 0)),    # 0 => isTry  = false
        'recomed': int(s.get('recomed', s.get('is_new', 0))),
        'isnew': int(s.get('isnew', s.get('is_new', 0))),
        'open_time': int(s.get('open_time', s.get('begin_time', 0))),
        'begin_time': int(s.get('begin_time', 0)),
    }


# ★ 活跃 TCP 连接句柄（供 HTTP 管理接口主动推送给客户端）
#   用途：“在线热改等级 → 立即推送 10301/10302/10303”，免重登。
# ★ 模块级配置引用（2026-09-18）：HTTP 管理接口（/DSH_ADMIN/*）需要读写配置，
#   而配置原本只作为 `self.cfg` 传给 TCP handler ⇒ HTTP 那边拿不到。
#   这里留一个模块级引用，main() 加载后充填。
# [P2B-migrated core/runtime.py::CFG/LIVE_*] CFG = {}
# [P2B-migrated core/runtime.py::CFG/LIVE_*] LIVE_CONNECTIONS = []          # [(TcpHandler, threading.Lock)]
# [P2B-migrated core/runtime.py::CFG/LIVE_*] LIVE_LOCK = threading.Lock()


# ★ 读配置表需要 LuaJIT 反汇编工具（在 tools/ 下）
try:
    import sys as _sys2, os as _os2
    _TOOLS = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)), '..', 'tools')
    if _TOOLS not in _sys2.path:
        _sys2.path.insert(0, _TOOLS)
    from luajit_bc import parse_bytes as _lj_parse
    from luajit_dis import OPS, kidx
except Exception as _e:
    log('server.log', '!! luajit tools import failed: %r（/cfg 将不可用）' % (_e,))
    OPS, kidx = {}, (lambda *a: None)


def _cfg_field_order(r):
    """从 proto[0] 的 TGETB/TSETS 配对推出字段顺序（同 tools/extract_config.py）。"""
    if not r.protos:
        return []
    pt = r.protos[0]
    order, pending = [], False
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


def _cfg_dump(r, order):
    """导出配置表：有字段顺序则 dict，否则位置数组。"""
    out = {}
    protos = r.protos[1:] if len(r.protos) > 1 else r.protos
    for pt in protos:
        for w in pt.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            c = kidx(pt, (w >> 16) & 0xffff)
            arr = getattr(c, 'array', None) or []
            h = dict(getattr(c, 'hash', []) or {})
            if h and not order:
                key = h.get('bid') or h.get('id')
                if key is not None:
                    out[str(key)] = dict(h)
                continue
            if len(arr) < 2:
                continue
            if order:
                key = arr[1] if isinstance(arr[1], int) else (
                    arr[0] if isinstance(arr[0], int) else None)
                if key is None:
                    continue
                row = {}
                for i, nm in enumerate(order):
                    idx = i + 1
                    row[nm] = arr[idx] if idx < len(arr) else None
                out[str(key)] = row
            else:
                key = arr[1] if isinstance(arr[1], int) else None
                if key is None:
                    continue
                out[str(key)] = arr[1:]
    return out


# ★★ 第二阶段：AOI + 寻路全局实例
_AOI = None
_MAPGRID = None
_RATELIMIT = None


def get_aoi():
    global _AOI
    if _AOI is None and aoi_mod is not None:
        _AOI = aoi_mod.AOI(tower_size=int(CFG.get('aoi_tower_size', 8)))
        log('server.log', 'AOI ready (tower_size=%d)' % int(CFG.get('aoi_tower_size', 8)))
    return _AOI


# ══════════════════════════════════════════════════════════════════════════
# ★★ 第二阶段（续）：真实碰撞数据 → MapGrid（2026-09-18）
#
#   背景：AOI 接线后 `walkable()` 仍恒真（allow_all=True）⇒ 防穿墙是纸面功能。
#   现在接入 **客户端自带配置** `Config.MapBlock`（APK 内），数据由
#   `tools/extract_config_mapblock.py` 提取为 server/map_block.json。
#
#   已实测确认的语义（见 map_block.json 的 _meta）：
#     0 = 可走   1 = 阻挡   2 = 阻挡（第二种障碍）
#     判据：95 个 NPC/怪物/采集物/出生点坐标中 94.7% 落在 0 上（反极性仅 5.3%）
#
#   ⚠ 只有 26/124 张场景带碰撞数据；**其余场景保持 allow_all**（不知道就不能阻挡）。
#   ⚠ **fail-open**：若玩家当前所在格本身就是阻挡格（实测 5 张场景的默认出生点如此），
#     则**跳过本次可走性校验**，否则玩家会被永久困死。
# ══════════════════════════════════════════════════════════════════════════
_MAPGRIDS = {}          # bid -> MapGrid（按场景缓存）
_MAPBLOCK = None


def load_mapblock():
    """懒加载 server/map_block.json。失败 ⇒ None（服务端照常 allow_all）。"""
    global _MAPBLOCK
    if _MAPBLOCK is None:
        p = os.path.join(HERE, 'map_block.json')
        try:
            if os.path.exists(p):
                d = json.load(open(p, encoding='utf-8'))
                _MAPBLOCK = d.get('scenes') or {}
                log('server.log', 'MapBlock ready: %d 场景带碰撞数据 -> %s'
                    % (len(_MAPBLOCK), p))
            else:
                _MAPBLOCK = {}
                log('server.log', 'MapBlock 缺失（%s）⇒ 全部场景 allow_all；'
                                  '可运行 tools/extract_config_mapblock.py 生成' % p)
        except Exception as e:
            _MAPBLOCK = {}
            log('server.log', '  !! MapBlock 读取失败: %r ⇒ allow_all' % (e,))
    return _MAPBLOCK


def _scene_grid(bid):
    """取某场景的 MapGrid；无碰撞数据 ⇒ 返回 None（调用方退化为 allow_all）。"""
    global _MAPGRID
    if pathfind_mod is None:
        return None
    if not CFG.get('map_collision', True):
        return None
    mb = load_mapblock()
    rows = mb.get(str(bid))
    if not rows:
        return None
    g = _MAPGRIDS.get(bid)
    if g is None:
        cols = max(len(r) for r in rows)
        blocked = set()
        for ri, line in enumerate(rows, 1):
            for ci, ch in enumerate(line, 1):
                if ch == '1':
                    # ★ 只有 '1' 是阻挡。依据 = **真实 10204 轨迹**（tcp.log 386 个坐标）：
                    #     落在 '0' 上 375 个 (97.2%)
                    #     落在 '2' 上  11 个 ( 2.8%)  ← 客户端真的走到了 2 上 ⇒ 2 可走
                    #     落在 '1' 上   0 个 ( 0.0%)  ← 从未站在 1 上 ⇒ 1 阻挡
                    #   （首版误把 '2' 也当阻挡，会造成 2.8% 的误拦/回拉）
                    blocked.add((ci, ri))
        g = pathfind_mod.MapGrid(cols + 2, len(rows) + 2, blocked=blocked)
        _MAPGRIDS[bid] = g
        log('server.log', '  场景 %s 碰撞就绪：%d×%d，阻挡 %d 格'
            % (bid, len(rows), cols, len(blocked)))
    return g


def get_mapgrid(bid=None):
    """向后兼容的入口。

    - `get_mapgrid(bid)`：有碰撞数据 ⇒ 该场景的 MapGrid；否则 None
    - `get_mapgrid()`   ：旧行为（256×256 allow_all），供未指定场景的调用方使用
    """
    global _MAPGRID
    if bid is not None:
        return _scene_grid(bid)
    if _MAPGRID is None and pathfind_mod is not None:
        _MAPGRID = pathfind_mod.MapGrid(256, 256, allow_all=True)
        log('server.log', 'MapGrid ready (allow_all=True：未指定场景)')
    return _MAPGRID


def _current_bid(handler):
    """当前场景 id（失败给 None ⇒ 退化为 allow_all）。

    ★ 2026-10-16 修复（GM 后台传送实测暴露的真缺陷）：
      原实现**只读 `spawn` 配置**，恒为 10001。于是任何场景切换之后
      （GM `/DSH_ADMIN/setscene`、挂机图 15402 链、副本），移动校验仍然拿
      **10001 的 MapBlock** 判可走性 ⇒ 目标格在新图里完全合法却被判"不可走"
      ⇒ 服务端回权威坐标把客户端拽回去、并把错误坐标落库。
      实测日志：`[move] cmd=10204 rid=1001 scene=10001 目标不可走 (10,58)`
      —— 而 (10,58) 正是 10005（乾坤日月谷）的默认出生点。

      改为：优先用**每连接的实际进图记录** `handler._last_enter[0]`
      （由 `_send_10200` 写入；GM 传送也会显式同步该字段），它在语义上就是
      "服务端刚把玩家放进哪个图"的唯一真值。无记录时回退 spawn 配置。
    """
    try:
        _le = getattr(handler, '_last_enter', None)
        if _le:
            _bid = int(_le[0] or 0)
            if _bid:
                return _bid
    except Exception:
        pass
    try:
        return int((handler.cfg.get('spawn') or {}).get('bid') or 0) or None
    except Exception:
        return None


def get_ratelimit():
    global _RATELIMIT
    if _RATELIMIT is None and pathfind_mod is not None:
        _RATELIMIT = pathfind_mod.MoveRateLimiter(
            max_tiles_per_sec=float(CFG.get('move_max_tiles_per_sec', 12.0)),
            burst=int(CFG.get('move_burst', 6)))
    return _RATELIMIT


def live_push(cfg, what='level'):
    """向所有活跃连接推送角色数据刷新。返回推送成功的连接数。"""
    sent = 0
    with LIVE_LOCK:
        conns = list(LIVE_CONNECTIONS)
    for h in conns:
        try:
            st = role_state(cfg)
            h.request.sendall(pack_frame(10302, build_10302(st)))
            h.request.sendall(pack_frame(10301, build_10301(st, cfg.get('skills', []))))
            h.request.sendall(pack_frame(10303,
                build_10303(st, cfg.get('skills', []), cfg.get('attr'))))
            # ★ PHASE 2.11：顺带推 10305（资产增量表）—— 客户端从不请求它，须服务端推
            try:
                h.request.sendall(pack_frame(10305, build_10305(cfg)))
            except Exception:
                pass
            sent += 1
            log('tcp.log', '  << [热改推送] 10302/10301/10303/10305 -> %s (what=%s)'
                % (h.client_address, what))
        except Exception as e:
            log('tcp.log', '  !! [热改推送] 失败 %s: %r（移除该连接）'
                % (h.client_address, e))
            try:
                with LIVE_LOCK:
                    if h in LIVE_CONNECTIONS:
                        LIVE_CONNECTIONS.remove(h)
            except Exception:
                pass
    return sent


# ══════════════════════════════════════════════════════════════════════════
# ★★ 第二阶段：AOI 接线（2026-09-18）
#
#   目标：让 10204/10205 真正走「**服务端校验 + 按视野广播**」，
#         而不是像接线前那样只 `save_role_pos` + 回发本人。
#
#   设计约束（**绝不回归既有可用功能**）：
#     · 全部包在 try/except 里 —— AOI 出任何问题都不能影响移动/登录链路；
#     · **单客户端时 watchers 为空 ⇒ 行为与接线前完全一致**（零回归）；
#     · 可走性校验依赖 `MapGrid` 的 blocked 数据；当前 `allow_all=True`
#       ⇒ 该检查自动退化为"越界检查"，不会误伤；
#     · **限流默认关闭**（`move_rate_limit=false`）—— 12 格/秒是拍的，
#       未按真机 10204 标定前打开会误杀正常玩家（见 aoi_pathfind_review.md P5）。
#
#   参考依据：analysis/server_reference/survive/{aoi_pathfind_review,jstm_mapping}.md
#     · Survive `avatar:Send2view` 只在 `watch_me` 上广播（"谁看得见我"）
#     · kongkongxiyou / Survive **都没有** L1 路径校验与 L2 限流 ⇒ 本实现是净增价值
# ══════════════════════════════════════════════════════════════════════════
_LAST_POS = {}          # rid -> (x, y) 服务端权威坐标（最近一次被接受的位置）


def _scene_rid(handler):
    """取该连接的角色 id（缓存到 handler 上，避免每次查库）。"""
    try:
        rid = getattr(handler, '_aoi_rid', None)
        if rid is None:
            rid = role_state(handler.cfg).get('rid', 1001)
            handler._aoi_rid = int(rid)
        return int(rid)
    except Exception:
        return None


def _scene_enter(handler):
    """进入场景：把角色登记进 AOI（**同时是 watcher 与 object**）。

    ⚠ 必须两向注册（`add_player`）——只注册 watcher 的玩家对任何人都不可见，
      这是 aoi.py 旧版 `add_watcher` 的 A9 缺陷，也是接线期最容易踩的坑。
    """
    if aoi_mod is None:
        return
    try:
        rid = _scene_rid(handler)
        if rid is None:
            return
        aoi = get_aoi()
        if aoi is None:
            return
        role = role_with_saved_pos(handler.cfg)
        x = int(role.get('x', 100))
        y = int(role.get('y', 100))
        rng = int(CFG.get('aoi_view_range', 15))
        aoi.add_player(rid, x, y, rng)
        _LAST_POS[rid] = (x, y)
        log('tcp.log', '  .. [aoi] enter rid=%s (%d,%d) range=%d stats=%s'
            % (rid, x, y, rng, aoi.stats()))
    except Exception as e:
        log('tcp.log', '  !! [aoi] enter 失败: %r' % (e,))


def _scene_ensure(handler):
    """幂等：确保该连接的角色已登记进 AOI（进场景时 / 首次移动时调用）。"""
    if getattr(handler, '_aoi_in', False):
        return
    _scene_enter(handler)
    handler._aoi_in = True


def _scene_leave(handler):
    """离开场景 / 断线：从 AOI 注销（`remove()` 会正常派发 leave）。"""
    try:
        rid = getattr(handler, '_aoi_rid', None)
        if rid is None:
            return
        handler._aoi_in = False
        _LAST_POS.pop(int(rid), None)
        if aoi_mod is None:
            return
        aoi = get_aoi()
        if aoi is None:
            return
        ev = aoi.remove(int(rid))
        try:
            rl = get_ratelimit()
            if rl is not None:
                rl.reset(int(rid))
        except Exception:
            pass
        log('tcp.log', '  .. [aoi] leave rid=%s events=%r' % (rid, ev))
    except Exception as e:
        log('tcp.log', '  !! [aoi] leave 失败: %r' % (e,))


def _authoritative_pos(handler, rid):
    """拒绝客户端坐标时，给出**服务端权威坐标**（优先内存，其次 DB）。"""
    p = _LAST_POS.get(rid)
    if p:
        return int(p[0]), int(p[1])
    try:
        role = role_with_saved_pos(handler.cfg)
        return int(role.get('x', 100)), int(role.get('y', 100))
    except Exception:
        return 100, 100


def _scene_validate_move(handler, rid, x, y, cmd):
    """移动校验（★ Survive 战斗层零距离校验；kongkongxiyou 直接信任客户端路径）。

    规则：
      ① **可走性**：目标格必须可走。数据来源 = 客户端 `Config.MapBlock`
         （26/124 场景有）；无数据的场景 ⇒ 退化为 allow_all（不阻挡）。
         ⚠ **fail-open**：若**当前所在格本身**就是阻挡格，则跳过本步 ——
         实测有 5 张场景的默认出生点落在阻挡格上，若一律拦截会让玩家永久困死。
      ② **限流**：令牌桶（`move_rate_limit` 默认 **关**，标定后再开）
    返回 `None` = 通过；返回 `(ax, ay)` = **拒绝，并给出服务端权威坐标**让客户端纠正
    （不用"静默丢弃"——那会让客户端与服务端永久错位）。
    """
    try:
        bid = _current_bid(handler)
        mg = get_mapgrid(bid) if bid else None
        if mg is not None and not mg.walkable(x, y):
            prev = _LAST_POS.get(rid)
            if prev is not None and not mg.walkable(prev[0], prev[1]):
                # ★ fail-open：当前格就是阻挡格（出生点异常/坐标越界）⇒ 放行，避免困死
                log('tcp.log', '  .. [move] rid=%s 当前格 %r 本身不可走 ⇒ **放行**(fail-open)'
                    % (rid, prev))
            else:
                log('tcp.log', '  !! [move] cmd=%d rid=%s scene=%s 目标不可走 (%d,%d) '
                               '→ 回复权威坐标 %r' % (cmd, rid, bid, x, y, prev))
                return _authoritative_pos(handler, rid)

        if CFG.get('move_rate_limit', False):
            rl = get_ratelimit()
            prev = _LAST_POS.get(rid)
            if rl is not None and prev is not None:
                dist = ((x - prev[0]) ** 2 + (y - prev[1]) ** 2) ** 0.5
                ok, why = rl.check(rid, dist)
                if not ok:
                    log('tcp.log', '  !! [move] cmd=%d rid=%s 被限流(%s) → 回复权威坐标'
                        % (cmd, rid, why))
                    return _authoritative_pos(handler, rid)
        return None
    except Exception as e:
        log('tcp.log', '  !! [move] 校验异常（**放行**，不影响移动）: %r' % (e,))
        return None


def _scene_apply_move(handler, rid, x, y):
    """接受移动后：更新 AOI（双向）+ 返回"看得见我的 watcher 集合"。"""
    try:
        aoi = get_aoi() if aoi_mod is not None else None
        if aoi is None:
            return set()
        aoi.move(rid, x, y)              # ★ A4：一次移动双向更新
        _LAST_POS[rid] = (x, y)
        return aoi.watchers_seeing(rid)
    except Exception as e:
        log('tcp.log', '  !! [aoi] move 失败: %r' % (e,))
        return set()


def _scene_broadcast_10204(src, rid, srv_id, x, y, watchers):
    """把 `SC_10204{rid,srv_id,x,y}` 推给**看得见我的其它连接**；返回推送数。

    ★ 只在"看得见我的人"上广播 —— 对应 Survive `avatar:Send2view` 用 `watch_me`
      （而不是"我看得见的人"）的语义；单客户端 ⇒ watchers 为空 ⇒ 返回 0。
    """
    if not CFG.get('aoi_broadcast', True) or not watchers:
        return 0
    # [P3deep-migrated] AOI 推送收敛：直接 sendall+遍历 LIVE_CONNECTIONS ⇒ 经 push_to_rid 投递。
    # 等价性：push_to_rid(hrid,pkt) 按 _scene_rid==hrid 选连接，与旧循环 hrid in watchers 逐对齐；
    # 单连接/rid 下 src 不在 watchers ⇒ 跳过 src 语义不变。
    sent = 0
    try:
        pkt = pack_frame(10204, w_u32(rid) + w_str(srv_id) + w_u16(x) + w_u16(y))
        for wrid in watchers:
            sent += push_to_rid(wrid, pkt)
    except Exception as e:
        log('tcp.log', '  !! [aoi] broadcast 失败: %r' % (e,))
    return sent


def push_to_rid(rid, pkt):
    """★ R53：把一个**已打包好的帧**推给指定 `rid` 的在线连接；返回推给了几个连接。

    用于管理接口的手动触发（如 `/DSH_ADMIN/guaji_end` 推 `15404`）。
    只推给 rid 匹配的连接；异常一律吞掉并记日志，不影响 HTTP 应答。
    """
    sent = 0
    try:
        with LIVE_LOCK:
            conns = list(LIVE_CONNECTIONS)
        for h in conns:
            try:
                if _scene_rid(h) != int(rid):
                    continue
                h.request.sendall(pkt)
                sent += 1
            except Exception as e:
                log('tcp.log', '  !! push_to_rid 失败 %s: %r' % (h.client_address, e))
    except Exception as e:
        log('tcp.log', '  !! push_to_rid 异常: %r' % (e,))
    return sent


class Handler(BaseHTTPRequestHandler):
    cfg = DEFAULT_CFG
    protocol_version = 'HTTP/1.1'

    def _send(self, code, body, ctype='application/json; charset=utf-8'):
        if isinstance(body, str):
            body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass

    def _url_config(self):
        # derive host:port from the request itself so the served config always
        # matches whatever address the client used to reach us
        host = self.cfg['host']
        port = self.cfg['http_port']
        hdr = self.headers.get('Host')
        if hdr:
            if ':' in hdr:
                h, _, p = hdr.partition(':')
                host, port = h, int(p) if p.isdigit() else port
            else:
                host = hdr
        path = os.path.join(HERE, 'url_config_ewan.lua')
        text = open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        text = text.replace('local HOST = "127.0.0.1"', 'local HOST = "%s"' % host)
        text = text.replace('local PORT = 8080', 'local PORT = %d' % port)
        return text

    def do_GET(self):
        p = self.path.split('?')[0]
        log('http.log', 'GET %s   [Host=%s]' % (self.path, self.headers.get('Host')))
        # ★ GM 后台管理系统（2026-10-16）：/GM 单文件控制台 + /GM/api 聚合读接口。
        #   为什么放在最前：控制台自身的读接口不进老分支，避免与 /DSH_ADMIN 审计挂钩互相干扰。
        #   循环 import 规避：把 mock_server 自身模块对象作为 host 传入（gm.console 不 import 本文件）。
        try:
            from gm import console as _gm_console
            if _gm_console.handle(self, sys.modules[__name__]):
                return
            if p == '/GM/api':
                from urllib.parse import urlparse as _up, parse_qs as _pq
                if _gm_console.handle_api(self, sys.modules[__name__],
                                          _pq(_up(self.path).query)):
                    return
        except Exception as _gm_e:
            log('http.log', '!! GM console failed: %r' % (_gm_e,))
        # ★ ★ 管理接口：在线热改等级 + 立即推送（供 DSH 插件调用）
        #   GET /DSH_ADMIN/setlevel?lev=8[&rid=1001]
        #   GET /DSH_ADMIN/getlevel[?rid=1001]
        if p.startswith('/DSH_ADMIN/'):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            act = p[len('/DSH_ADMIN/'):]
            rid = int((q.get('rid') or ['1001'])[0])
            # ★ GM 后台新增动作（roles/accounts/online/gmsessions/gmlog/rolecard/
            #   rolemail/setscene）：在审计挂钩**之前**派发 —— 只读动作不该污染
            #   gm.log；setscene 已在 gm.console._setscene 内自审计（带前后值与 ref）。
            try:
                from gm import console as _gm_console2
                if _gm_console2.admin(self, sys.modules[__name__], act, q, rid):
                    return
            except Exception as _gm_e2:
                log('http.log', '!! GM admin ext failed: %r' % (_gm_e2,))
            # ★ S3-A 任务2（G3）：admin 写命令统一审计挂钩。
            #   只读查询类（SELECT/重放/状态快照）与已自审计的 setlevel/setassets/
            #   setdiamond 除外；其余写库命令在此落 gm.log（时间/action/rid/params/ref），
            #   单点插入、零行为改动，避免逐命令改。params 即"new"值（含改后目标）。
            _ADMIN_READONLY = {
                'battle_replay', 'getlevel', 'getassets', 'status', 'listitems',
                'cfglist', 'cfg', 'reward_log', 'mall_list', 'afk_status',
                'mail_list', 'ach_list', 'ach_progress', 'skill_show',
                'partner_show', 'dungeon_list', 'rank_breakdown', 'aoi', 'power',
            }
            _ADMIN_AUDITED_TRIO = {'setlevel', 'setassets', 'setdiamond'}
            try:
                if act not in _ADMIN_READONLY and act not in _ADMIN_AUDITED_TRIO:
                    from gm import service as _gm_audit
                    _params = {k: v for k, v in q.items() if k != 'rid'}
                    _gm_audit.log_gm(act, rid,
                                      'params=%r ref=gm:%s:%d:%d'
                                      % (_params, act, rid, int(time.time())))
            except Exception:
                pass
            if act == 'setcharge':
                # ★ PHASE 2.16b：设置**累计充值**（`16900` 读侧 / `30502 领充值奖励` 门槛
                #   的**同一数据源**）。走正式 Service 链路（`growth_target.service`
                #   → `role_gt` 表），**不直改 DB**（纪律：GM 必须走 Service）。
                #   GET /DSH_ADMIN/setcharge?n=80[&rid=1001]
                try:
                    _n = int((q.get('n') or ['0'])[0])
                    from growth_target.service import set_total_charge
                    st = set_total_charge(rid, _n)
                    return self._send(200, json.dumps(
                        {'ok': True, 'rid': rid, 'total_charge': st.get('total_charge')},
                        ensure_ascii=False))
                except Exception as e:
                    return self._send(500, json.dumps(
                        {'ok': False, 'msg': '%r' % (e,)}, ensure_ascii=False))
            if act == 'battle_replay':
                # 确定性战斗帧重放（只读，不发真实客户端/不落库）：
                # 构造固定 mon 的战斗，同步跑完整状态机，抓每帧 hex 供改前/改后对比。
                try:
                    _mon_id = int((q.get('mon_id') or ['20001'])[0])
                    _mon = {'id': _mon_id, 'bid': _mon_id, 'name': 'replay',
                            'res_id': '', 'level': 1}
                    _bt = make_battle(CFG, _mon)
                    if _bt is None:
                        return self._send(500, json.dumps({'ok': False, 'msg': 'battle unavailable'}))
                    _frames = []
                    _frames.append(['20002', pack_frame(20002, w_u8(1) + w_str('')).hex()])
                    _frames.append(['20010', pack_frame(20010, _bt.build_20010()).hex()])
                    _rounds = []
                    _guard = 0
                    while not _bt.finished and _guard < 100:
                        for _c, _b in _bt.play_round():
                            _rounds.append([str(_c), pack_frame(_c, _b).hex()])
                        _guard += 1
                    _frames.append(['rounds', _rounds])
                    _frames.append(['20020', pack_frame(20020, _bt.build_20020()).hex()])
                    _frames.append(['20023', pack_frame(20023, _bt.build_20023()).hex()])
                    return self._send(200, json.dumps(
                        {'ok': True, 'frames': _frames, 'result': getattr(_bt, 'result', None)},
                        ensure_ascii=False))
                except Exception as e:
                    return self._send(500, json.dumps({'ok': False, 'msg': 'replay err: %r' % (e,)},
                                                      ensure_ascii=False))
            if act == 'getlevel':
                row = db_get_role(rid) or {}
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid,
                    'level': row.get('level'), 'exp': row.get('exp'),
                }, ensure_ascii=False))
            if act == 'daily':
                # ★★ R48：给某日常任务加进度 —— tid 可传**面板 id**(如 208)
                #   或 **huoli_id**(如 1)。
                #   GET /DSH_ADMIN/daily?tid=208&n=1&val=10[&rid=1001]
                #   既是数值调参旋钮，也是"进度由哪些行为产生"尚未取证期间的
                #   **可验证写入路径**（不靠编造游戏规则来产生数据）。
                _tid = int((q.get('tid') or ['0'])[0])
                _n = int((q.get('n') or ['1'])[0])
                _val = int((q.get('val') or ['0'])[0])
                _target = None
                for _t in richang_daily_tasks():
                    if int(_t.get('id') or 0) == _tid or int(_t.get('huoli_id') or 0) == _tid:
                        _target = _t
                        break
                if _target is None:
                    return self._send(404, json.dumps(
                        {'ok': False, 'msg': '未知日常任务 tid=%d' % _tid},
                        ensure_ascii=False))
                _ok = db_daily_add(rid, int(_target['id']), _n, _val)
                return self._send(200, json.dumps({
                    'ok': bool(_ok), 'rid': rid, 'tid': int(_target['id']),
                    'huoli_id': int(_target.get('huoli_id') or 0),
                    'name': _target.get('name'), 'max_num': _target.get('max_num'),
                    'added_num': _n, 'added_val': _val,
                    'progress': db_daily_get(rid).get(int(_target['id'])),
                }, ensure_ascii=False))
            if act == 'chengjiu':
                # ★★ R48：给某成就加进度。
                #   GET /DSH_ADMIN/chengjiu?bid=10100&n=1[&rid=1001]
                _bid = int((q.get('bid') or ['0'])[0])
                _n = int((q.get('n') or ['1'])[0])
                _c = (chengjiu_cfg() or {}).get(str(_bid))
                if _c is None:
                    return self._send(404, json.dumps(
                        {'ok': False, 'msg': '未知成就 bid=%d' % _bid},
                        ensure_ascii=False))
                _ok = db_chengjiu_add(rid, _bid, _n)
                _cur = db_chengjiu_get(rid).get(_bid, 0)
                _tgt = int(_c.get('val') or 0)
                return self._send(200, json.dumps({
                    'ok': bool(_ok), 'rid': rid, 'bid': _bid,
                    'name': _c.get('name'), 'desc': _c.get('desc'),
                    'trigger_mod': _c.get('trigger_mod'),
                    'trigger_fun': _c.get('trigger_fun'),
                    'target': _tgt, 'cur': _cur, 'added': _n,
                    'rate': (100 if (_tgt and _cur >= _tgt)
                             else (int(_cur * 100 / _tgt) if _tgt else 0)),
                }, ensure_ascii=False))
            if act == 'ach_list':
                from achievement import service as _ach
                return self._send(200, json.dumps({'ok':True,'n':len(_ach.list_all()),'sample':_ach.list_all()[:5]},ensure_ascii=False))
            if act == 'ach_progress':
                from achievement import service as _ach
                return self._send(200, json.dumps({'ok':True,'rid':rid,'rows':_ach.progress(rid)},ensure_ascii=False))
            if act == 'ach_done':
                from achievement import service as _ach
                _b=int((q.get('bid') or ['10100'])[0])
                return self._send(200, json.dumps(_ach.mark_done(rid,_b),ensure_ascii=False))
            if act == 'ach_claim':
                from achievement import service as _ach
                _b=int((q.get('bid') or ['10100'])[0])
                return self._send(200, json.dumps(_ach.claim(rid,_b),ensure_ascii=False))

            if act == 'guaji':
                # ★★ R48：设置挂机轮次（`15405` 的返回值）
                #   GET /DSH_ADMIN/guaji?n=10[&rid=1001]
                #   实验用：默认 0 = 维持现状；调高后重走「日常/参与」看挂机是否启动。
                _n = int((q.get('n') or ['0'])[0])
                db_guaji_set(rid, _n)
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'loop_count': db_guaji_get(rid)},
                    ensure_ascii=False))
            if act == 'guaji_end':
                # ★★ R53：**显式结束当前挂机轮次** —— 向该角色的连接推 `15404{mission_bid}`。
                #   为什么做成旋钮而不是"自动判定"：客户端 `ghost_ctrl` proto#32
                #   `handle15404` = `mon_hongchen:deleteMon()`（结束本轮、清掉挂机怪）。
                #   而"**一轮 = 多少只怪**"在原版里没有取证到（`config_guaji` 只给怪/地图/等级段，
                #   `config_mission` 里也没有挂机轮次字段）⇒ 猜一个阈值就是在编造规则。
                #   所以本轮只把**链路做通 + 手动触发**，等真机抓到自然轮转后再定规则。
                #   GET /DSH_ADMIN/guaji_end[?rid=1001][&mission_bid=10010]
                _st = db_guaji_state(rid)
                _mb = int((q.get('mission_bid') or [str(_st['mission_bid'])])[0])
                if not _mb:
                    return self._send(200, json.dumps(
                        {'ok': False, 'why': 'mission_bid 为 0（还没有 15402 记录过挂机任务）',
                         'state': _st}, ensure_ascii=False))
                sent = push_to_rid(rid, pack_frame(15404, w_u32(_mb)))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'mission_bid': _mb,
                     'connections': sent, 'state': _st}, ensure_ascii=False))
            if act == 'addbag':
                # ★★ R89：往背包里发物品（验收/补偿用）
                #   GET /DSH_ADMIN/addbag?bid=36057&n=1[&code=1][&rid=1001]
                #   GET /DSH_ADMIN/addbag?bids=36052,36053,...&n=1   一次发多个
                #   GET /DSH_ADMIN/addbag?formation_books=1           ★ 一键发全部阵法书
                #   —— 阵法书 = `config_formation.luac` 里每个阵法挂的物品 id
                #      （36053 天攻20 / 36056 疾风32 / 36052 地御36 / 36055 破雷42
                #        / 36054 飘雨46 / 36057 锋矢50；「流云阵(1)」是初始阵、无书）
                _bid = (q.get('bid') or [''])[0]
                _bids = (q.get('bids') or [''])[0]
                if (q.get('formation_books') or [''])[0]:
                    _bids = ','.join(str(b) for b in FORMATION_BOOKS)
                _code = int((q.get('code') or ['1'])[0])
                _n = int((q.get('n') or ['1'])[0])
                _todo = []
                if _bids:
                    _todo += [int(x) for x in _bids.split(',') if x.strip()]
                if _bid:
                    _todo.append(int(_bid))
                _done = []
                for _b in _todo:
                    try:
                        db_bag_add(rid, _b, _n, bag_code=_code)
                        _done.append(_b)
                    except Exception as e:
                        log('tcp.log', '  !! addbag %d 失败: %r' % (_b, e))
                # 推给在线连接，客户端不必重登就能看到
                #   ⚠ `LIVE_CONNECTIONS` 的元素是 `(handler, lock)` **元组**（见其定义），
                #     不是 handler 本身 —— 第一版直接把它传进 bag_push_frames 会打错。
                try:
                    for _ent in list(LIVE_CONNECTIONS):
                        _h = _ent[0] if isinstance(_ent, (tuple, list)) else _ent
                        bag_push_frames(_h, rid)
                except Exception as e:
                    log('tcp.log', '  !! addbag 推送失败: %r' % (e,))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'added': _done,
                     'bag': [{'bid': x.get('bid'), 'num': x.get('quantity')}
                             for x in bag_items_of(rid, _code)]},
                    ensure_ascii=False))
            if act == 'mail':
                # ★ R161：发一封真实邮件（验收用）
                _mid = db_mail_add(rid, (q.get('subject') or [''])[0],
                                   (q.get('content') or [''])[0],
                                   from_name=(q.get('from') or ['系统'])[0])
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'mail_id': _mid, 'count': len(db_mail_list(rid))},
                    ensure_ascii=False))
            if act == 'marketgoods':
                # ★ R140：摆摊上架（验收用）
                _mid = (q.get('market_id') or [''])[0]
                if _mid != '':
                    db_market_goods_add(rid, int(_mid),
                                        int((q.get('item_bid') or ['0'])[0] or 0),
                                        int((q.get('item_num') or ['1'])[0] or 1),
                                        int((q.get('price') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'goods': market_goods(rid)},
                    ensure_ascii=False))
            if act == 'build':
                # ★ R140：建筑技能发放/查询（验收用）
                _bl = (q.get('lev') or [''])[0]
                _bi = (q.get('learn') or [''])[0]
                db_build_set(rid, int(_bl) if _bl != '' else None,
                             int(_bi) if _bi != '' else None)
                lv, ln = db_build_state(rid)
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'lev': lv, 'learn_list': ln},
                    ensure_ascii=False))
            if act == 'tree':
                # ★ R138：摇钱树等级发放/查询（验收用）
                _tl = (q.get('lev') or [''])[0]
                if _tl != '':
                    db_tree_set(rid, int(_tl))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'tree_lev': db_tree_state(rid),
                     'strength_rest': tree_static('attr_delay', 0),
                     'strength_name': tree_worship_name(db_tree_state(rid)),
                     'max_lev': tree_max_lev()}, ensure_ascii=False))
            if act == 'fabao':
                # ★ R131：法宝发放（验收用）
                #   GET /DSH_ADMIN/fabao?id=1&bid=20001&level=5&stage=2
                _fi = (q.get('id') or [''])[0]
                if _fi != '':
                    db_fabao_add(rid, int(_fi), int((q.get('bid') or ['20001'])[0] or 20001),
                                 int((q.get('level') or ['1'])[0] or 1),
                                 int((q.get('stage') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'fabao': db_fabao_list(rid)},
                    ensure_ascii=False))
            if act == 'bosskill':
                # ★ R129：标记某 BOSS 已击杀（验收用）
                _mb = (q.get('mon_bid') or [''])[0]
                if _mb != '':
                    _c = db_conn()
                    _c.execute('CREATE TABLE IF NOT EXISTS role_boss_kill ('
                               'rid INTEGER, mon_bid INTEGER, ctime INTEGER, '
                               'PRIMARY KEY (rid, mon_bid))')
                    _c.execute('INSERT OR REPLACE INTO role_boss_kill VALUES (?,?,?)',
                               (rid, int(_mb), int(time.time())))
                    _c.commit()
                    db_release(_c)
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'boss_count': len(boss_rows(rid)),
                     'killed': [r[0] for r in boss_rows(rid) if r[1]]},
                    ensure_ascii=False))
            if act == 'title':
                # ★ R129：称号发放（验收用）
                _tb = (q.get('bid') or [''])[0]
                if _tb != '':
                    db_title_add(rid, int(_tb))
                _c = db_conn()
                _rows = _c.execute('SELECT bid FROM role_title WHERE rid=?', (rid,)).fetchall()
                db_release(_c)
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'titles': [r[0] for r in _rows]},
                    ensure_ascii=False))
            if act == 'lingshou':
                # ★ R127：魂兽发放（验收用）
                _lj = (q.get('jie') or [''])[0]
                if _lj != '':
                    db_lingshou_set(rid, int(_lj), int((q.get('lev') or ['1'])[0] or 1))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'lingshou': db_lingshou_state(rid),
                     'attrs': lingshou_attr_values(db_lingshou_state(rid)['lev'])},
                    ensure_ascii=False))
            if act == 'yuanshen':
                # ★ R127：元神发放（验收用）
                _soul = (q.get('soul') or [''])[0]
                if _soul != '':
                    db_yuanshen_set(rid, int(_soul), int((q.get('soul_max') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'yuanshen': db_yuanshen_state(rid)},
                    ensure_ascii=False))
            if act == 'shenqi':
                # ★ R126：神器发放（验收用）
                _sid = (q.get('id') or [''])[0]
                if _sid != '':
                    db_shenqi_set(rid, int(_sid),
                                  int((q.get('lev') or ['1'])[0] or 1),
                                  int((q.get('star') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'shenqi': db_shenqi_list(rid)},
                    ensure_ascii=False))
            if act == 'mingge':
                # ★ R126：命格发放（验收用）
                _mb = (q.get('bid') or [''])[0]
                if _mb != '':
                    db_mingge_add(rid, int(_mb), int((q.get('lev') or ['1'])[0] or 1))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'mingge': db_mingge_list(rid)},
                    ensure_ascii=False))
            if act == 'chair':
                # ★ R125：座椅发放/查询（验收用）
                _stg = (q.get('stage') or [''])[0]
                if _stg != '':
                    db_chair_set(rid, int(_stg), int((q.get('power') or ['0'])[0] or 0),
                                 int((q.get('luck') or ['0'])[0] or 0),
                                 int((q.get('res_stage') or ['0'])[0] or 0),
                                 int((q.get('grow') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'chair': db_chair_state(rid)},
                    ensure_ascii=False))
            if act == 'wing':
                # ★ R125：翅膀发放/查询（验收用）
                _wid = (q.get('wing_id') or [''])[0]
                if _wid != '':
                    db_wing_set(rid, int(_wid),
                                int((q.get('star') or ['0'])[0] or 0),
                                int((q.get('color') or ['0'])[0] or 0),
                                int((q.get('power') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'wing': db_wing_state(rid)},
                    ensure_ascii=False))
            if act == 'invest':
                # ★ R117：投资进度管理（验收用）
                #   GET /DSH_ADMIN/invest?type=7&day=3[&geted=0]
                #   GET /DSH_ADMIN/invest?type=0   清空
                _t = (q.get('type') or [''])[0]
                if _t != '' and int(_t) == 0:
                    _c = db_conn()
                    _c.execute('DELETE FROM role_invest WHERE rid=?', (rid,))
                    _c.commit()
                    db_release(_c)
                elif _t != '':
                    db_invest_set(rid, int(_t),
                                  int((q.get('day') or ['1'])[0] or 1),
                                  int((q.get('geted') or ['0'])[0] or 0))
                _st = db_invest_state(rid)
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'invest': _st,
                     'types': invest_type_list(),
                     'milestones': invest_milestones(_st['itype']) if _st['itype'] else []},
                    ensure_ascii=False))
            if act == 'ride':
                # ★ R115：发放/查询坐骑（验收用）
                #   GET /DSH_ADMIN/ride              查
                #   GET /DSH_ADMIN/ride?jie=1&lev=1  发（jie=0 表示收回）
                _jie = (q.get('jie') or [''])[0]
                if _jie != '':
                    db_ride_set(rid, int(_jie), int((q.get('lev') or ['1'])[0] or 1))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'ride': db_ride_state(rid),
                     'attrs': ride_attr_values(db_ride_state(rid)['lev']),
                     'skills': ride_skills(), 'can_items': ride_can_items()},
                    ensure_ascii=False))
            if act == 'qifu':
                # ★ R243：公会祈福次数（校验 / 端到端证明用）
                #   GET /DSH_ADMIN/qifu                 查
                #   GET /DSH_ADMIN/qifu?type=1&val=5    置（档位 id 见 config_guild_pray）
                _t = (q.get('type') or [''])[0]
                if _t != '':
                    db_qifu_set(rid, int(_t), int((q.get('val') or ['0'])[0] or 0))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'tiers': qifu_tiers(),
                     'qifu': db_qifu_state(rid)},
                    ensure_ascii=False))
            if act == 'exp':
                # ★★ R98：**对照实验开关**（见文件头/本块注释）。
                #   为什么读**全局 CFG** 而不是 `self.cfg`：`self.cfg` 是**连接时**建立的实例副本
                #   （`TcpHandler.cfg = _c2`），改它不会影响已连上的客户端；
                #   而全局 CFG 是**每次请求现读**的 ⇒ 改完**下一次请求即生效，不必重登**。
                #   用途：把"数据没到客户端"与"UI 过滤掉了"分开 —— 只改一个值，让用户看屏幕。
                _name = (q.get('name') or [''])[0]
                _val = (q.get('val') or [''])[0]
                _KEYS = ('hero_bag_limit', 'hero_state_override', 'form_pos_limit',
                         'hero15_limit')
                if _name:
                    if _name not in _KEYS:
                        return self._send(400, json.dumps(
                            {'ok': False, 'error': 'unknown key', 'allowed': _KEYS},
                            ensure_ascii=False))
                    CFG[_name] = int(_val or 0)
                return self._send(200, json.dumps(
                    {'ok': True, 'exp': {k: CFG.get(k) for k in _KEYS},
                     'note': 'hero_bag_limit: 10401 只回前 N 个(0=不限)；'
                             'hero_state_override: 覆盖 state(-1=不覆盖)；'
                             'form_pos_limit: 14000 上阵位只回前 N 个(0=不限)'},
                    ensure_ascii=False))
            if act == 'hero':
                # ★★ R86：伙伴背包管理（验收用）
                #   GET /DSH_ADMIN/hero              查
                #   GET /DSH_ADMIN/hero?bid=33100    加（并把该伙伴放进背包）
                #   GET /DSH_ADMIN/hero?bid=33100&off=1  删
                _b = (q.get('bid') or [''])[0]
                if _b:
                    if (q.get('off') or [''])[0]:
                        _c = db_conn()
                        _c.execute('DELETE FROM role_heros WHERE rid=? AND bid=?',
                                   (rid, int(_b)))
                        _c.commit()
                        db_release(_c)
                    else:
                        _p = partner_def(int(_b))
                        db_hero_add(rid, int(_b), color=int(_p.get('color') or 0))
                    return self._send(200, json.dumps(
                        {'ok': True, 'rid': rid, 'bid': int(_b),
                         'hero_bag': db_hero_list(rid, self.cfg)}, ensure_ascii=False))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'hero_bag': db_hero_list(rid, self.cfg)},
                    ensure_ascii=False))
            if act == 'buff':
                # ★★ R80：buff 列表管理（`10640`）—— 客户端一直在发 `CS_10640`，
                #   本服此前无应答 ⇒ 饱食度等 buff 面板拿不到数据。
                #   GET /DSH_ADMIN/buff?bid=NNN[&career=C][&rid=1001]   加
                #   GET /DSH_ADMIN/buff?bid=NNN&off=1                    删
                #   GET /DSH_ADMIN/buff                                  查
                _b = (q.get('bid') or [''])[0]
                if _b:
                    _ok = db_buff_set(rid, int((q.get('career') or ['0'])[0]), int(_b),
                                      on=not (q.get('off') or [''])[0])
                    return self._send(200, json.dumps(
                        {'ok': _ok, 'rid': rid, 'buff_bid': int(_b),
                         'buff_list': db_buff_list(rid)}, ensure_ascii=False))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'buff_list': db_buff_list(rid)},
                    ensure_ascii=False))
            if act == 'power':
                # ★★ 战力系统（基于 config_attr.luac 的 AttrPower 原版权重）
                #   ★ R43：**口径统一** —— 总战力走 role_power()，与
                #     10304 / 10306 / 20100 / 12901 **同一算法、同一属性来源**；
                #     明细用同一份属性字典算，保证「明细之和 == 总值」。
                #   原实现读的是 `role_state`（DB 状态）+ 自选 18 项键表，
                #   与游戏内战力可能不同 ⇒ 已废。
                ad = role_attr_dict(self.cfg)
                pw = role_power(self.cfg)
                items = (power_mod.power_items(ad, 12) if power_mod is not None else [])
                return self._send(200, json.dumps({
                    'ok': True,
                    'power': pw,
                    'attrs': ad,
                    'detail': [{'key': k, 'name': n, 'contrib': c} for k, n, c in items],
                    'module': power_mod is not None,
                }, ensure_ascii=False))
            if act == 'aoi':
                # ★ 第二阶段：AOI + 寻路状态（只读）
                a = get_aoi()
                mg = get_mapgrid()
                return self._send(200, json.dumps({
                    'ok': True,
                    'aoi': (a.stats() if a is not None else '未加载'),
                    'mapgrid': (None if mg is None else
                                {'w': mg.w, 'h': mg.h, 'blocked': len(mg.blocked),
                                 'allow_all': mg.allow_all}),
                    'modules': {'aoi': aoi_mod is not None,
                                'pathfind': pathfind_mod is not None},
                }, ensure_ascii=False))
            if act == 'cfglist':
                # ★ 列出 APK 里的**全部配置表**（assets/src/config/*.luac，347 张）
                import zipfile as _zf
                apk = self.cfg.get('apk_path') or os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), '..', 'anzbao', 'jstm.apk')
                out = []
                try:
                    with _zf.ZipFile(apk) as z:
                        for n in z.namelist():
                            if n.endswith('.luac') and n.startswith('assets/src/config/'):
                                out.append({'name': os.path.basename(n),
                                            'size': z.getinfo(n).file_size})
                except Exception as e:
                    return self._send(500, json.dumps({'ok': False, 'error': repr(e)},
                                                      ensure_ascii=False))
                out.sort(key=lambda x: -x['size'])
                return self._send(200, json.dumps(
                    {'ok': True, 'n': len(out), 'tables': out}, ensure_ascii=False))
            if act == 'cfg':
                # ★ 读**任意**配置表：?name=config_partner_base&kw=唐&limit=20
                #   复用 tools/extract_config.py 的提取逻辑（字段顺序从字节码推出）
                nm = (q.get('name') or [''])[0]
                kw = (q.get('kw') or [''])[0]
                lim = int((q.get('limit') or ['20'])[0])
                if not nm:
                    return self._send(400, json.dumps({'ok': False, 'error': 'need name'},
                                                      ensure_ascii=False))
                import zipfile as _zf
                apk = self.cfg.get('apk_path') or os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), '..', 'anzbao', 'jstm.apk')
                path = 'assets/src/config/' + (nm if nm.endswith('.luac') else nm + '.luac')
                try:
                    with _zf.ZipFile(apk) as z:
                        raw = z.read(path)
                except Exception as e:
                    return self._send(404, json.dumps(
                        {'ok': False, 'error': '无此表 %s: %r' % (nm, e)},
                        ensure_ascii=False))
                try:
                    rr = _lj_parse(raw)
                    order = _cfg_field_order(rr)
                    data = _cfg_dump(rr, order)
                except Exception as e:
                    return self._send(500, json.dumps({'ok': False, 'error': repr(e)},
                                                      ensure_ascii=False))
                items = []
                for k, v in data.items():
                    if kw:
                        blob = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                        if kw not in str(k) and kw not in blob:
                            continue
                    items.append({'key': k, 'row': v})
                    if len(items) >= lim:
                        break
                return self._send(200, json.dumps(
                    {'ok': True, 'name': nm, 'fields': order[:24],
                     'total': len(data), 'shown': len(items), 'items': items},
                    ensure_ascii=False))
            # ==================== ★ 扩展管理动作（2026-09-18）====================
            # 用户要求：“读取游戏中的各种资源目录”→“增加到 bat 文件中”→“实现热修改”。
            # 设计：每个动作都只读写**已存在的数据源**（SQLite / config），并在可能时**立即推送**给在线客户端。
            #   ★ 未取证的语义一律不猜：缺少数据源的字段直接不返回。
            if act == 'reward_log':
                # [P45-C] 只读审计：?rid=1001 返回该角色全部奖励发放流水（reward_log）
                try:
                    _con = db_conn()
                    _con.row_factory = sqlite3.Row
                    _rows = _con.execute(
                        'SELECT rid, reference_id, source, granted_ts '
                        'FROM reward_log WHERE rid=? ORDER BY granted_ts DESC',
                        (rid,)).fetchall()
                    db_release(_con)
                    return self._send(200, json.dumps(
                        {'ok': True, 'rid': rid, 'count': len(_rows),
                         'rows': [dict(r) for r in _rows]}, ensure_ascii=False))
                except Exception as e:
                    return self._send(200, json.dumps({'ok': False, 'err': repr(e)},
                                                      ensure_ascii=False))
            # ==================== ★ Phase 8：伙伴/技能闭环 GM 验证端点 ====================
            if act == 'partner_feed':
                # 培养伙伴：?bid=33100&n=1  扣 gold -> 升级 -> 属性贡献 -> 推送
                from partner import service as _psvc
                _bid = int((q.get('bid') or ['0'])[0]); _n = int((q.get('n') or ['1'])[0])
                _before = db_get_assets(rid).get('gold')
                _r = _psvc.feed(rid, _bid, _n)
                live_push(CFG, 'partner_feed')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'gold_before': _before, 'gold_after': db_get_assets(rid).get('gold'),
                    'result': _r}, ensure_ascii=False))
            if act == 'partner_show':
                from partner import service as _psvc
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'catalog': len(_psvc._live_list or []), 'owned': _psvc.owned_map(rid),
                    'lev_max': _psvc.lev_max()}, ensure_ascii=False))
            if act == 'skill_learn':
                # 学习技能：?bid=10020  扣 gold -> 入 role_skills -> 属性贡献 -> 推送
                from skill import service as _ssvc
                _bid = int((q.get('bid') or ['0'])[0])
                _before = db_get_assets(rid).get('gold')
                _r = _ssvc.learn(rid, _bid)
                live_push(CFG, 'skill_learn')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'gold_before': _before, 'gold_after': db_get_assets(rid).get('gold'),
                    'result': _r}, ensure_ascii=False))
            if act == 'skill_up':
                from skill import service as _ssvc
                _bid = int((q.get('bid') or ['0'])[0])
                _before = db_get_assets(rid).get('gold')
                _r = _ssvc.upgrade(rid, _bid)
                live_push(CFG, 'skill_up')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'gold_before': _before, 'gold_after': db_get_assets(rid).get('gold'),
                    'result': _r}, ensure_ascii=False))
            if act == 'skill_show':
                from skill import service as _ssvc
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'catalog': len(_ssvc.catalog()), 'learned': _ssvc.learned_list(rid)},
                    ensure_ascii=False))
            # ==================== ★ Phase 9：成长族闭环 GM 端点 ====================
            if act == 'wing_up':
                from growth import service as _gws
                _before = db_get_assets(rid).get('coin')
                _r = _gws.wing_up(rid)
                live_push(CFG, 'wing_up')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'coin_before': _before, 'coin_after': db_get_assets(rid).get('coin'), 'result': _r}, ensure_ascii=False))
            if act == 'shenqi_up':
                from growth import service as _gws
                _sid = int((q.get('sid') or ['10001'])[0])
                _before = db_get_assets(rid).get('coin')
                _r = _gws.shenqi_up(rid, _sid)
                live_push(CFG, 'shenqi_up')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'coin_before': _before, 'coin_after': db_get_assets(rid).get('coin'), 'result': _r}, ensure_ascii=False))
            if act == 'mingge_activate':
                from growth import service as _gws
                _mb = int((q.get('bid') or ['21001'])[0])
                _before = db_get_assets(rid).get('coin')
                _r = _gws.mingge_activate(rid, _mb)
                live_push(CFG, 'mingge_activate')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'coin_before': _before, 'coin_after': db_get_assets(rid).get('coin'), 'result': _r}, ensure_ascii=False))
            # ==================== ★ Phase 10：副本/挂机闭环 GM 端点 ====================
            if act == 'dungeon_list':
                from dungeon import service as _dng
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'catalog': len(_dng.catalog()), 'rows': _dng.list_panel(rid)}, ensure_ascii=False))
            if act == 'dungeon_clear':
                from dungeon import service as _dng
                _bid = int((q.get('bid') or ['20001'])[0])
                _r = _dng.clear(rid, _bid)
                live_push(CFG, 'dungeon_clear')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid, 'result': _r}, ensure_ascii=False))
            if act == 'afk_enter':
                from afk import service as _afk
                return self._send(200, json.dumps({'ok': True, 'rid': rid, 'result': _afk.enter(rid)}, ensure_ascii=False))
            if act == 'afk_status':
                from afk import service as _afk
                _r = _afk.status(rid)
                # ★ C5-C：把**离线挂机会话**（客户端开关 10933/10934 那条链）一并回出。
                #   此前后者只落状态、从不结算 ⇒ 开着离线挂机零收益，且与 afk.service
                #   的会话是两套互不相通的存储。现在两边共用同一组速率函数。
                try:
                    _gs = db_guaji_state(rid)
                    _r['offline'] = _afk.offline_status(
                        rid, _gs.get('off_on'), _gs.get('off_started_at'))
                except Exception as _ea:
                    _r['offline'] = {'err': '%r' % (_ea,)}
                return self._send(200, json.dumps({'ok': True, 'rid': rid, 'result': _r}, ensure_ascii=False))
            if act == 'afk_offline_claim':
                # ★ C5-C：显式结算**离线挂机**收益（幂等，ref=afk_off:<rid>:<off_started_at>）。
                #   为什么放在 GM 面而不是客户端：疑似客户端领取命令 `10931` 从未观测到任何
                #   实机帧、字段仅 {code,msg} ⇒ 不凭空发明玩家侧领取流程（纪律）。
                from afk import service as _afk
                _gs = db_guaji_state(rid)
                _r = _afk.offline_claim(rid, _gs.get('off_on'), _gs.get('off_started_at'))
                live_push(CFG, 'afk_offline_claim')
                return self._send(200, json.dumps(
                    {'ok': _r.get('ok'), 'rid': rid,
                     'gold_after': db_get_assets(rid).get('gold'), 'result': _r},
                    ensure_ascii=False))
            if act == 'afk_claim':
                from afk import service as _afk
                _r = _afk.claim(rid)
                live_push(CFG, 'afk_claim')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'gold_after': db_get_assets(rid).get('gold'), 'result': _r}, ensure_ascii=False))
            # ==================== ★ Phase 11：商城/签到 GM 端点 ====================
            if act == 'mall_list':
                from mall import service as _mall
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'counts': _mall.counts(), 'rows': _mall.list_panel()}, ensure_ascii=False))
            if act == 'mall_buy':
                _gid = int((q.get('gid') or ['20008'])[0])
                _num = int((q.get('num') or ['1'])[0])
                _code, _msg, _g, _total, _bought = shop_try_buy(CFG, mall_cfg(), _gid, _num)
                return self._send(200, json.dumps({'ok': _code == 1, 'rid': rid, 'gid': _gid,
                    'msg': _msg, 'total': _total, 'bought_now': _bought,
                    'gold': db_get_assets(rid).get('gold'), 'coin': db_get_assets(rid).get('coin')}, ensure_ascii=False))
            if act == 'sign_do':
                from activity import service as _act
                _r = _act.sign(rid)
                live_push(CFG, 'sign')
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'gold_after': db_get_assets(rid).get('gold'), 'result': _r}, ensure_ascii=False))
            # ==================== ★ Phase 12：邮件/排行 GM 端点 ====================
            if act == 'mail_list':
                from mail import service as _ms
                return self._send(200, json.dumps({'ok': True, 'rid': rid,
                    'count': len(_ms.list_mails(rid)), 'mails': _ms.list_mails(rid)}, ensure_ascii=False))
            if act == 'mail_send':
                _mid = db_mail_add(rid, 'Phase12测试邮件', '附件=gold1000/coin2000', from_name='系统',
                    assets=[{'type':'gold','count':1000},{'type':'coin','count':2000}], items=[])
                return self._send(200, json.dumps({'ok': True, 'rid': rid, 'mail_id': _mid,
                    'count': len(db_mail_list(rid))}, ensure_ascii=False))
            if act == 'mail_claim':
                from mail import service as _ms
                _mid = int((q.get('mid') or ['0'])[0])
                _r = _ms.claim(rid, _mid)
                live_push(CFG, 'mail_claim')
                return self._send(200, json.dumps({'ok': _r.get('ok'), 'rid': rid,
                    'gold_after': db_get_assets(rid).get('gold'), 'result': _r}, ensure_ascii=False))
            if act == 'rank_breakdown':
                from power import service as _pw
                return self._send(200, json.dumps(_pw.breakdown(rid), ensure_ascii=False))
            # ==================== Phase 16: drop test GM endpoint ====================
            if act == 'drop_test':
                _mon = int((q.get('mon') or ['20003'])[0])
                from drop import service as _ds
                _drops = _ds.resolve(_mon)
                return self._send(200, json.dumps({'ok': True, 'rid': rid, 'mon': _mon,
                    'drops': _drops}, ensure_ascii=False))
            if act == 'status':
                # 一次拉全部状态（等级/资产/各囊/装备/伙伴/任务/礼包）
                bag = db_bag_get(rid, BAG_MAIN)
                equip = db_equip_all(rid)
                store = db_store_get(rid, STORAGE_CODE)
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid,
                    'role': db_get_role(rid) or {},
                    'assets': db_get_assets(rid) or {},
                    'bag': [{'item_id': x.get('item_id'), 'bid': x.get('bid'),
                             'qty': x.get('quantity')} for x in bag],
                    'equip': [{'slot': x.get('slot'), 'bid': x.get('bid')} for x in equip],
                    'store': [{'item_id': x.get('item_id'), 'bid': x.get('bid'),
                               'qty': x.get('quantity')} for x in store],
                    'levgift_got': sorted(db_get_levgift(rid)),
                }, ensure_ascii=False))
            if act == 'giveitem':
                # 发物品（可多件）：?bid=33001&num=1（支持 bid2/num2 等后缀）
                #   ★ 只发**物品表里真实存在**的 bid（is_valid_item 校验）
                given = []
                for k in sorted([k for k in q.keys() if k.startswith('bid')]):
                    suffix = k[3:]
                    try:
                        gb = int((q.get(k) or ['0'])[0])
                        gn = int((q.get('num' + suffix) or ['1'])[0])
                    except Exception:
                        continue
                    if gb <= 0 or gn <= 0:
                        continue
                    if not is_valid_item(gb):
                        given.append({'bid': gb, 'ok': False,
                                      'err': '不在物品表内'})
                        continue
                    # [P45-B] 统一走 RewardService.grant（source='gm'，unique ref 每次都发）
                    grant(rid, [{'kind': 'item', 'bid': gb, 'amount': gn}],
                          reference_id='gm-giveitem-%d-%d-%d' % (rid, gb, int(time.time())),
                          source='gm')
                    given.append({'bid': gb, 'num': gn, 'name': item_name(gb), 'ok': True})
                # ★ 发完后**主动推送**：
                #   · live_push      → 角色数据 10301/10302/10303
                #   · live_push_bag  → **背包刷新 SC_10500/10502**（新增）
                #   原先只调 live_push，玩家客户端要等自己切页/重开背包才看到新物品。
                #   `live_push_bag` 会遍历所有活跃 TCP 连接、按该连接**请求过的 bag_code**
                #   逐个推（见 bag_push_frames），所以主背包/装备/仓库/伙伴等页都会刷新。
                pushed = live_push(CFG, 'giveitem')
                pushed_bag = live_push_bag(CFG, 'giveitem')
                log('http.log', '  ** ADMIN giveitem rid=%d %r (push=%d bag_push=%d)'
                    % (rid, given, pushed, pushed_bag))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'given': given,
                     'pushed': pushed, 'pushed_bag': pushed_bag},
                    ensure_ascii=False))
            if act == 'givegift':
                # 发礼包并**直接打开**（走 gift_contents 表）
                gb = int((q.get('bid') or ['0'])[0])
                gn = int((q.get('num') or ['1'])[0])
                if gn <= 0: gn = 1
                if not is_valid_item(gb):
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'bid %d 不在物品表内' % gb},
                        ensure_ascii=False))
                cont = gift_contents(gb)
                got = []
                for cb, cn in cont:
                    if is_valid_item(cb):
                        db_bag_add(rid, cb, (cn or 1) * gn)
                        got.append({'bid': cb, 'num': (cn or 1) * gn, 'name': item_name(cb)})
                if not got:
                    db_bag_add(rid, gb, gn)      # 开不出就把礼包本体发过去
                    got.append({'bid': gb, 'num': gn, 'name': item_name(gb), 'note': '无内容表，发本体'})
                pushed = live_push(CFG, 'givegift')
                log('http.log', '  ** ADMIN givegift rid=%d bid=%d -> %r' % (rid, gb, got))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'opened': got, 'pushed': pushed},
                    ensure_ascii=False))
            if act == 'setequip':
                # 按部位装备：?bid=40003（自动按 type 定槽）
                eb = int((q.get('bid') or ['0'])[0])
                if not is_valid_item(eb):
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'bid %d 不在物品表内' % eb},
                        ensure_ascii=False))
                slot = equip_slot_for(rid, eb, CFG)
                if slot is None:
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'bid %d 不是装备（type=%s）'
                                 % (eb, item_type_of(eb))}, ensure_ascii=False))
                db_equip_put(rid, slot, eb, eb, 0)
                pushed = live_push(CFG, 'setequip')
                log('http.log', '  ** ADMIN setequip rid=%d bid=%d -> slot %d' % (rid, eb, slot))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'bid': eb, 'slot': slot,
                     'name': item_name(eb), 'pushed': pushed}, ensure_ascii=False))
            if act == 'unequip':
                slot = int((q.get('slot') or ['0'])[0])
                row = db_equip_take(rid, slot)
                if row:
                    db_bag_add(rid, int(row['bid']), 1)
                pushed = live_push(CFG, 'unequip')
                return self._send(200, json.dumps(
                    {'ok': bool(row), 'rid': rid, 'slot': slot,
                     'bid': (row or {}).get('bid'), 'pushed': pushed}, ensure_ascii=False))
            if act == 'setheros':
                # 设置伙伴列表：?bids=1001,1002（写回 config.json）
                raw = (q.get('bids') or [''])[0]
                bids = [int(x) for x in raw.split(',') if x.strip().isdigit()]
                CFG['heros'] = [{'bid': b, 'color': 1, 'lev': 1, 'exp': 0, 'state': 0, 'chip': 0}
                                for b in bids]
                try:
                    json.dump(CFG, open(CFG_PATH, 'w', encoding='utf-8'),
                              ensure_ascii=False, indent=1)
                except Exception as e:
                    return self._send(500, json.dumps({'ok': False, 'error': repr(e)},
                                                      ensure_ascii=False))
                pushed = live_push(CFG, 'setheros')
                log('http.log', '  ** ADMIN setheros rid=%d bids=%r' % (rid, bids))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'heros': CFG['heros'], 'pushed': pushed},
                    ensure_ascii=False))
            if act == 'setjubaopen':
                # 设置聚宝盆奖池：?pool=16201:40,33001:30（bid:weight）
                raw = (q.get('pool') or [''])[0]
                pool = []
                for part in raw.split(','):
                    if ':' not in part:
                        continue
                    bs, ws = part.split(':', 1)
                    if not bs.strip().isdigit():
                        continue
                    b = int(bs); w = int(ws) if ws.strip().lstrip('-').isdigit() else 1
                    if is_valid_item(b):
                        pool.append({'bid': b, 'num': 1, 'weight': w})
                CFG['jubaopen_pool'] = pool
                try:
                    json.dump(CFG, open(CFG_PATH, 'w', encoding='utf-8'),
                              ensure_ascii=False, indent=1)
                except Exception as e:
                    return self._send(500, json.dumps({'ok': False, 'error': repr(e)},
                                                      ensure_ascii=False))
                log('http.log', '  ** ADMIN setjubaopen pool=%r' % (pool,))
                return self._send(200, json.dumps(
                    {'ok': True, 'pool': pool,
                     'names': [item_name(p['bid']) for p in pool]}, ensure_ascii=False))
            if act == 'setmissions':
                # 把任务链链头前移到指定 bid（或重置任务）
                #   ?bid=10010  ⇒ 把该任务置为进行中（status=1），其余清理
                mb = int((q.get('bid') or ['0'])[0])
                if mb <= 0:
                    return self._send(400, json.dumps({'ok': False, 'error': 'need bid'},
                                                      ensure_ascii=False))
                con = db_conn()
                con.execute('DELETE FROM missions WHERE rid=?', (rid,))
                con.commit(); db_release(con)
                # ★ C5-A 修复：原来把 `target` 写死 0、`target_value` 写死 1
                #   ⇒ 用本端点把链头指到**任何条件型任务**（fight_mon / kill_type_mon /
                #   use_item …）时，`mission_progress_advance()` 的
                #   `m['target'] != target` 永远不匹配 ⇒ **该任务永远无法推进/完成**，
                #   只能靠 12403 的 target_value=1 蒙过去。做条件验证时尤其致命。
                #   改为与 `task/service.py` 的播种口径一致：从配置 `progress[0]` 取
                #   (cond_name, target, need)；`progress` 为空的任务（到点即交）保持 0/1。
                _d = mission_def(mb) or {}
                _prog = _d.get('progress') or []
                _c0 = _prog[0] if (_prog and isinstance(_prog[0], (list, tuple))) else None
                _tgt = 0
                _need = 1
                if _c0 and len(_c0) >= 2 and _c0[1] is not None:
                    try:
                        _tgt = int(_c0[1])
                    except Exception:
                        _tgt = 0
                if _c0 and len(_c0) >= 3 and _c0[2] is not None:
                    try:
                        _need = int(_c0[2])
                    except Exception:
                        _need = 1
                db_save_mission(rid, {'mission_bid': mb, 'mission_status': 1,
                                      'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
                                      'code': 0, 'process_status': 0,
                                      'target': _tgt, 'target_value': _need, 'value': 0,
                                      'show_lave_time': 0, 'lave_time': 0,
                                      'accept_time': 0})
                pushed = live_push(CFG, 'setmissions')
                log('http.log', '  ** ADMIN setmissions rid=%d head=%d cond=%s target=%s need=%s'
                    % (rid, mb, (_c0[0] if _c0 else None), _tgt, _need))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'head': mb,
                     'name': (mission_def(mb) or {}).get('name'),
                     'cond': (_c0[0] if _c0 else None),
                     'target': _tgt, 'need': _need, 'pushed': pushed},
                    ensure_ascii=False))
            if act == 'reset':
                # 重置各囊 / 任务 / 礼包领取（?what=bag|equip|store|mission|levgift|all）
                what = (q.get('what') or ['all'])[0]
                done = []
                con = db_conn()
                if what in ('bag', 'all'):
                    con.execute('DELETE FROM bag_items WHERE rid=?', (rid,)); done.append('bag')
                if what in ('equip', 'all'):
                    con.execute('DELETE FROM equip_items WHERE rid=?', (rid,)); done.append('equip')
                if what in ('store', 'all'):
                    con.execute('DELETE FROM store_items WHERE rid=?', (rid,)); done.append('store')
                if what in ('mission', 'all'):
                    con.execute('DELETE FROM missions WHERE rid=?', (rid,)); done.append('mission')
                if what in ('levgift', 'all'):
                    con.execute('DELETE FROM levgift_got WHERE rid=?', (rid,)); done.append('levgift')
                con.commit(); db_release(con)
                pushed = live_push(CFG, 'reset')
                log('http.log', '  ** ADMIN reset rid=%d what=%s -> %r' % (rid, what, done))
                return self._send(200, json.dumps(
                    {'ok': True, 'rid': rid, 'reset': done, 'pushed': pushed},
                    ensure_ascii=False))
            if act == 'reload':
                # 热重载配置表（?what=item|mall|mission|gift|all）
                what = (q.get('what') or ['all'])[0]
                global _ITEM_TYPES, _ITEM_IDS, _MALL_CFG, _GIFT_CFG, _MISSION_CFG
                done = []
                if what in ('item', 'all'):
                    _ITEM_TYPES = None; _ITEM_IDS = None; done.append('item')
                if what in ('mall', 'all'):
                    _MALL_CFG = None; done.append('mall')
                if what in ('gift', 'all'):
                    _GIFT_CFG = None; done.append('gift')
                if what in ('mission', 'all'):
                    try:
                        _MISSION_CFG = None
                    except Exception:
                        pass
                    done.append('mission')
                if what in ('config', 'all'):
                    try:
                        _new = json.load(open(CFG_PATH, encoding='utf-8'))
                        CFG.clear(); CFG.update(_new)
                    except Exception as e:
                        return self._send(500, json.dumps({'ok': False, 'error': repr(e)},
                                                          ensure_ascii=False))
                    done.append('config')
                log('http.log', '  ** ADMIN reload %r' % (done,))
                return self._send(200, json.dumps({'ok': True, 'reloaded': done},
                                                  ensure_ascii=False))
            if act == 'listitems':
                # 按名字搜物品（供 bat 菜单查 bid）：?kw=长枪&limit=20
                kw = (q.get('kw') or [''])[0]
                lim = int((q.get('limit') or ['20'])[0])
                out = []
                item_ids()          # 确保 _ITEM_TYPES 已加载
                data = _ITEM_TYPES or {}
                for b, v in data.items():
                    nm = v.get('name') if isinstance(v, dict) else None
                    if isinstance(nm, str) and kw and kw in nm:
                        out.append({'bid': int(b), 'name': nm, 'type': v.get('type')})
                        if len(out) >= lim:
                            break
                return self._send(200, json.dumps(
                    {'ok': True, 'kw': kw, 'n': len(out), 'items': out},
                    ensure_ascii=False))

            if act == 'setassets':
                # ★ 设置资产（三种货币）
                #   依据：
                #     AssetsEnToCode (config_game_data.luac) = {gold:1, coin:2, coupon:3, ...}
                #     ChongZhiConst   (chongzhi_const.luac) = {YUANBAO:1, TONG:2, YINBI:3, ...}
                #     界面名(chongzhi_model proto[12]) = 钻石 / 金魂币 / 银魂币
                #   ⇒ 钻石=gold(1)、银魂币=coin(2)、金魂币=coupon(3)
                #   ★ 依据优先级：**界面确定性读数 > 两表 code 对齐**。
                #     2026-09-17 把 gold=33333 / coin=11111 / coupon=22222 推送到客户端，
                #     游戏内读到「钻石」=33333、「银魂币」=11111、「金魂币」=22222 ⇒ 上式成立。
                #     早期仅靠 AssetsEnToCode × ChongZhiConst 对齐推出的
                #     「金魂币=coin(2)、银魂币=coupon(3)」**已被该读数否证**。
                #   ★ 2026-09-18 **独立复验通过**（三值互异 + 已知真值）：
                #     注入 gold+111111/coin+222222/coupon+333333 → 背包面板显示
                #     钻石=104万(gold 1,040,597)、金=133万(coupon 1,333,332)、银=122万(coin 1,224,183)
                #     ⇒ 金魂币=coupon、银魂币=coin 定死。注意：**背包货币栏没有文字标签**，
                #       只能按图标辨认（金/银配色），这正是上一轮认错的原因。
                #     证据：shots/currency_evidence_20260918*.png
                #     出处：analysis/1.4.9/task/task_reward_currency.md 文末「复验」。
                vals = {}
                # ★ 支持**任意已知资产字段名**（不再只有三种货币）：公会商城等
                #   pay_type 用的是 guild_active 这类资产（见 ASSETS_EN_TO_CODE，
                #   与客户端 AssetsEnToCode 同源），管理接口必须能发放/校正它们。
                for key in [k for k in q.keys()
                            if k not in ('rid', 'mode') and k in ASSETS_EN_TO_CODE]:
                    raw_v = (q.get(key) or [None])[0]
                    if raw_v is None or raw_v == '':
                        continue
                    try:
                        vals[key] = int(raw_v)
                    except Exception:
                        return self._send(400, json.dumps(
                            {'ok': False, 'error': '%s must be integer' % key},
                            ensure_ascii=False))
                if not vals:
                    return self._send(400, json.dumps(
                        {'ok': False,
                         'error': 'need at least one known asset '
                                  '(gold/coin/coupon/guild_active/...)'},
                        ensure_ascii=False))
                # ★ S3-A 任务2（G1）：setassets 负数/非法值校验——对齐 setlevel
                #   (lev 1..200) 与 setdiamond (val>=0)。原实现 gold=-100 直接落库。
                for _k, _v in vals.items():
                    if _v < 0:
                        return self._send(400, json.dumps(
                            {'ok': False,
                             'error': '%s must be >= 0 (got %d)' % (_k, _v)},
                            ensure_ascii=False))
                # ★ 语义：默认 **设为绝对值**（mode=set）；
                #   mode=add 时为**增量**。(原实现只会累加，
                #   实测 coin 1290 → 3512 即 +2222，与“修改数量”语义不符。)
                mode = (q.get('mode') or ['set'])[0]
                if mode == 'add':
                    delta = dict(vals)
                else:
                    cur = db_get_assets(rid)
                    delta = {k: int(v) - int(cur.get(k, 0) or 0) for k, v in vals.items()}
                # [P13-migrated] GM 改货币走正式 Service 链路 gm.service.set_assets（含 gm.log 审计）
                from gm import service as _gm
                _ar = _gm.set_assets(rid, vals, mode)
                now = db_get_assets(rid)
                n = live_push(self.cfg, 'setassets')
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid, 'mode': mode, 'delta': delta,
                    'now': {k: now.get(k, 0) for k in vals}, 'pushed': n,
                }, ensure_ascii=False))
            if act == 'getassets':
                now = db_get_assets(rid)
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid,
                    'gold': now.get('gold', 0), 'coin': now.get('coin', 0),
                    'coupon': now.get('coupon', 0),
                    # ★ 附带返回全部已存资产（只增不减，不破坏既有字段）
                    'assets': {k: v for k, v in sorted(now.items())},
                }, ensure_ascii=False))
            if act == 'setdiamond':
                # ★ S2 项②：GM 置钻石（统一资产 Service 链路，不直改 DB）。
                #   口径（docs/S1_未完成项与遗留问题.md §2 实测）：
                #     HUD 钻石读 diamond 字段（SC_10302 尾部 diamond:I，build_10302
                #     对非 1.3.0 版本追加；当前客户端按登录体长判 1.4.9）。
                #     role_state() 合并时 role_assets **优先**于 roles.diamond 列 ⇒
                #     写 role_assets['diamond'] 即实时生效、且 SQLite 持久化（重登不丢）。
                #   链路：gm.service.set_assets -> currency.service.db_add_assets
                #     （与既有 setassets 同一正式 Service，含 gm.log 审计：
                #      操作者/目标 rid/类型 setassets/变更前后 delta/时间）。
                #   用法：GET /DSH_ADMIN/setdiamond?rid=1001&val=100000
                _dv = (q.get('val') or [''])[0]
                try:
                    val = int(_dv)
                except Exception:
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'val must be integer'},
                        ensure_ascii=False))
                if val < 0:
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'val must be >= 0'},
                        ensure_ascii=False))
                from gm import service as _gm
                _old = int(db_get_assets(rid).get('diamond', 0) or 0)
                _ar = _gm.set_assets(rid, {'diamond': val}, mode='set')
                _gm.log_gm('setdiamond', rid,
                           'old=%d new=%d ref=gm:setdiamond:%d:%d'
                           % (_old, val, rid, int(time.time())))
                now = db_get_assets(rid)
                n = live_push(self.cfg, 'setdiamond')
                log('http.log', '  ** ADMIN setdiamond rid=%d %d->%d (push=%d)'
                    % (rid, _old, now.get('diamond', 0), n))
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid, 'old': _old,
                    'diamond': now.get('diamond', 0), 'pushed': n,
                }, ensure_ascii=False))
            if act == 'setlevel':
                # [P13-migrated] GM 改等级走正式 Service 链路 gm.service.set_level
                #   -> roles 权威落库 -> live_push(10302/10301/10303) 客户端实时可见。
                from gm import service as _gm
                lev = int((q.get('lev') or ['0'])[0])
                if lev < 1 or lev > 200:
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'lev must be 1..200'},
                        ensure_ascii=False))
                _lr = _gm.set_level(rid, lev)
                log('http.log', '  ** ADMIN setlevel rid=%d %r' % (rid, _lr))
                n = live_push(self.cfg, 'setlevel')
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid, 'level': lev, 'old': _lr['old'], 'pushed': n,
                }, ensure_ascii=False))
            if act == 'additem':
                # ★ 管理/诊断接口：给角色加一件物品并**立即推送背包刷新**。
                #   用途：验证"背包面板开着时能否实时刷新"（bag_push_frames）；
                #   也是"给自己发道具"的常用操作，与 setlevel/setassets 同类。
                _bid = int((q.get('bid') or ['0'])[0])
                _num = int((q.get('n') or ['1'])[0])
                if _bid <= 0 or _num <= 0:
                    return self._send(400, json.dumps(
                        {'ok': False, 'error': 'bid/n must be positive'},
                        ensure_ascii=False))
                row = db_bag_add(rid, _bid, _num)
                pushed = live_push_bag(self.cfg, 'admin_additem')
                log('http.log', '  ** ADMIN additem rid=%d bid=%d x%d -> %r (pushed=%d)'
                    % (rid, _bid, _num, row, pushed))
                return self._send(200, json.dumps({
                    'ok': True, 'rid': rid, 'bid': _bid, 'n': _num,
                    'item': row, 'bag_count': len(db_bag_get(rid, BAG_MAIN)),
                    'pushed': pushed,
                }, ensure_ascii=False))
            return self._send(404, json.dumps({'ok': False, 'error': 'unknown admin action'},
                                              ensure_ascii=False))
        if 'url_config' in p:
            return self._send(200, self._url_config(),
                              'application/x-lua; charset=utf-8')
        if 'version2.txt' in p or p.endswith('/version.txt'):
            # 版本检查：返回与客户端本地一致的最新版本，避免触发热更下载
            body = self.cfg.get('version_text', '208')
            log('http.log', '  -> version response: %r' % body)
            return self._send(200, body, 'text/plain; charset=utf-8')
        if p.startswith('/app/mobile/conf') or p.startswith('/gateway/mobile/conf') \
                or p.startswith('/app/mobile/hft') or p.startswith('/gateway/mobile/hft'):
            return self._send(200, json.dumps(self.cfg.get('conf', {
                'code': 0, 'msg': 'ok', 'status': 0, 'result': 1,
                'maintain': 0, 'is_maintain': 0, 'white': 1,
            }), ensure_ascii=False))
        if 'notice' in p:
            return self._send(200, json.dumps({'notice': self.cfg.get('notice', '')},
                                              ensure_ascii=False))
        if p.startswith('/cdn/'):
            fp = os.path.join(HERE, 'cdn', p[5:])
            if os.path.isfile(fp):
                with open(fp, 'rb') as f:
                    return self._send(200, f.read(), 'application/octet-stream')
            log('http.log', '  cdn miss: %s' % p)
            return self._send(200, self.cfg.get('version_text', '208'),
                              'text/plain; charset=utf-8')
        # any other path: benign "nothing to update" answer
        return self._send(200, json.dumps({'code': 0, 'msg': 'ok', 'status': 0,
                                           'result': 1, 'update': 0, 'version': 0},
                                          ensure_ascii=False))

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n) if n else b''
        log('http.log', 'POST %s\n  headers=%s\n  body=%s'
            % (self.path, dict(self.headers), body[:500]))
        if 'url_config' in self.path:
            return self._send(200, self._url_config(),
                              'application/x-lua; charset=utf-8')
        sl = [normalize_server_item(s, self.cfg) for s in self.cfg['server_list']]
        # ── 实测确认的响应结构（denglu_mgr.luac proto[8] 逐指令反汇编）──
        #   客户端读的是 jsonObj['data']['server_list']，**不是顶层的 server_list**。
        #   顶层结构写成 {"code":..,"server_list":[...]} 时 data 为 nil，
        #   客户端会走 "当前请求到服务器列表信息为空" 的 CommonAlert('重新请求') 分支。
        #   data 里还读一个可选的 default_zone。
        # ★ 2026-10-17 修正：default_zone **必须是一个条目表**，不能是 "1" 这样的字符串。
        #   证据（denglu_mgr proto[53] managerDefualtServerListByJsonObj 逐指令）：
        #       local var_55_1 = var_55_0.default_zone
        #       srv_name = var_55_1.name or var_55_1.srv_name
        #       srv_id   = var_55_1.srv_id or var_55_1.platform .. '_' .. var_55_1.zone_id
        #   传字符串时 `var_55_1.platform` 为 nil ⇒ `nil .. '_'` 直接抛错
        #   ⇒ 默认服路径（登录后自动取默认区）必崩，这正是"选区界面不稳"的来源之一。
        _dz = self.cfg.get('default_zone', '1')
        _dz_item = None
        for _it in sl:
            if str(_it.get('srv_id')) == str(_dz) or str(_it.get('zone_id')) == str(_dz):
                _dz_item = _it
                break
        payload = {
            'data': {
                'server_list': sl,
                'default_zone': _dz_item or (sl[0] if sl else {}),
            },
        }
        if self.cfg.get('lua_response'):
            # 仅当客户端 SERVER_LIST_ISLUA 为真时才会用这条路径：
            # 那时客户端执行 loadstring('return ' .. response)()
            def lua(v):
                if isinstance(v, dict):
                    return '{' + ','.join('[%s]=%s' % (lua(k), lua(x)) for k, x in v.items()) + '}'
                if isinstance(v, list):
                    return '{' + ','.join(lua(x) for x in v) + '}'
                if isinstance(v, str):
                    return '"%s"' % v.replace('"', '\\"')
                if v is True:
                    return 'true'
                if v is False:
                    return 'false'
                return str(v)
            return self._send(200, 'return ' + lua(payload),
                              'text/plain; charset=utf-8')
        return self._send(200, json.dumps(payload, ensure_ascii=False))


# ---------------------------------------------------------------------------
# 游戏服 TCP 协议
#
# 帧格式（由客户端真实流量反推并用 tools/decode_frames.py 验证，边界 100% 对齐）：
#     [u32 大端 payload_len][u16 大端 cmd][body ...]
#     payload_len = 2 + len(body)
# 字符串 = [u16 大端 长度][字节]；整数一律大端。
#
# ⚠ 客户端短消息尾部会带"脏数据"（定长缓冲区整段发出）：
#   例 10001 声明 17 字节 body，实际只有前 13 字节是 key="game_client"。
#   ⇒ 服务端必须按消息定义读字段、**忽略多余尾部**。
# ---------------------------------------------------------------------------
CMD_NAMES = {
    1110: 'CSAccountLogin 帐号登录',
    1199: 'heartbeast 心跳',
    10001: 'FirstPack 连接首包',
    10101: 'RoleCreate 创建角色',
    10102: 'RoleLogin 登录指定角色',
    10103: 'RoleReLogin 角色重连',
    10200: 'RoleEnter 进入场景',
    10300: 'RoleInit 客户端初始化完毕',
    10301: '角色基础信息',
}
















# ---------------------------------------------------------------------------
# Phase 4C：角色数据模型（默认值 + 归一化）
# 目的：角色登录/初始化时用**一份完整、自洽的角色状态**下发，
#       而不是散落的 cfg.get(...) 默认值（那样很容易出现 0/缺失）。
# 字段依据：protocol/manual.md 的 SC_10301 / SC_10302 定义（不自行添加无依据字段）。
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Phase 4E：角色状态持久化（SQLite）
# 目的：把 lev/exp/gold/属性 等从 config.json 的**静态配置**搬进**数据库**，
#       保证服务器重启后角色数据仍在（此前只有 x/y 落到 role_<rid>.json）。
# 表结构按阶段要求：rid/uid/name/level/career/sex/exp/hp/max_hp/mp/max_mp/
#                   gold/gold_acc/diamond/scene_id/x/y/dir/vip_level/title/
#                   status/updated_at
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# 资产 code 映射（**权威来源：1.4.9 客户端 `config/config_game_data.luac` 的
#   `AssetsEnToCode` 表**，38 项，用反汇编逐项读出，不是猜的）。
#   用途：任务奖励 `Config.Mission[bid].award_assets` 里的二元组 `{code, 数量}`
#        通过本表反查出资产字段名，从而实现"奖励由客户端配置驱动"。
#   ⚠ 本表给的是**协议字段名**，不是界面名：code 1=`gold`=钻石、code 2=`coin`=**银魂币**、
#     code 3=`coupon`=**金魂币**（界面确定性读数，见 task_reward_currency.md 文末「重要更正」）。
#     ⇒ 任务奖励 `{2,n}` 写进 `coin` 列，游戏里显示为**银魂币**，不是金魂币。
# ---------------------------------------------------------------------------
ASSETS_EN_TO_CODE = {
    'gold': 1, 'coin': 2, 'coupon': 3, 'exp': 4, 'sinew': 5, 'experience': 6,
    'vitality': 7, 'guild_contrib': 8, 'practice_exp': 9, 'tower_cent': 10,
    'arena_cent': 11, 'shilian': 12, 'coral': 13, 'rmb': 14, 'hero_exp': 15,
    'courage': 16, 'charm': 17, 'trophy': 18, 'lingqi': 19, 'integral': 20,
    'gold_acc': 21, 'cash_coupon': 22, 'dan_point': 23, 'guild_active': 24,
    'marriage': 25, 'course': 26, 'vip_exp': 27, 'lingshi': 28, 'gouyu': 29,
    'peak_point': 30, 'arena_soul': 31, 'black_soul': 32, 'jiebai_cent': 33,
    'lottery_point': 36, 'boss_point': 37, 'partner_shenqi_point': 38,
    'rune_exp': 39, 'rune_chip': 40,
    # ★ 本表已与客户端 `config_game_data.luac` 的 `AssetsEnToCode` 数组**逐项核对**
    #   （dump 见 analysis/1.4.9/shop_luac/mall_table_1_Config.json 同目录的取证记录）：
    #   1=gold 2=coin 3=coupon … 24=guild_active 31=arena_soul 36=lottery_point …
    #   仅 34/35 在客户端表里就是 nil ⇒ 保持未知，不编造。
}
CODE_TO_ASSET = {v: k for k, v in ASSETS_EN_TO_CODE.items()}

# ---------------------------------------------------------------------------
# ★ 任务配置：**直接加载从 1.4.9 客户端 `config_mission.luac` 提取的全表**
#   （`tools/extract_mission_config.py` 生成；846 条，其中主线 type=1 有 262 条）
#   这样任务系统的"内容"完全由 APK 原配置驱动，而不是手写几条。
# ---------------------------------------------------------------------------
# [P3deep-migrated] MISSION_CFG_PATH/_MISSION_CFG 已下沉 task/service.py：
# MISSION_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                                 'mission_config.json')
# _MISSION_CFG = None


# [P3deep-migrated] mission_cfg 已下沉 task/service.py：
# def mission_cfg():
#     """惰性加载 APK 任务全表（只读）。"""
#     global _MISSION_CFG
#     if _MISSION_CFG is None:
#         try:
#             with open(MISSION_CFG_PATH, encoding='utf-8') as f:
#                 raw = json.load(f)
#             _MISSION_CFG = {int(k): v for k, v in raw.items()}
#             log('server.log', 'mission config loaded: %d 条 <- %s'
#                 % (len(_MISSION_CFG), MISSION_CFG_PATH))
#         except Exception as e:
#             _MISSION_CFG = {}
#             log('server.log', '!! mission config load failed: %r' % (e,))
#     return _MISSION_CFG


MALL_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'mall_config.json')
_MALL_CFG = None

# ── S2 项①：CS_10650 talent_list 真实天赋 id 装载 ──────────────────────────
# 帧格式（三源一致）：protocol/fields.json + server/proto_defs.py +
#   _tmp_cr112/cmd_resolve_106.luac 反汇编 = `talent_list:table{id:uint16}`
#   （w_u16 计数 + Σ w_u16 id）。
#
# ★ talent_id 口径（本分片静态复核，docs_raw/s2_a_findings.md）：
#   SkillTalent 表共 105 行；解构 JSON 的 **dict key** 与行内 `bid` 字段在 41 行错位，
#   且 7 个 dict key（90200..90800）> uint16 上限 65535 ⇒ 不能作 wire id。
#   客户端 TalentRune.<group>.level.talent_id 引用的正是行内 **bid** 字段
#   （例：TalentRune[15700].1.talent_id=40020=施毒一阶 bid；
#         TalentRune[50062].1.talent_id=50080=烈焰天罗一阶 bid），
#   ⇒ wire talent_list 应填 **bid**，105 个 bid 全唯一、范围 10020..50082，
#   全部 ≤65535 可安全 uint16 编码。
#   决策：**全量 105 个 bid**（私服界面恢复：全部天赋置为已解锁显示）。
TALENT_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'cfg', 'config_skill_talent.json')
_TALENT_LIST_CACHE = None


def load_talent_list():
    """从 cfg/config_skill_talent.json 提取真实 talent_id（=行内 bid），带模块级缓存。"""
    global _TALENT_LIST_CACHE
    if _TALENT_LIST_CACHE is not None:
        return _TALENT_LIST_CACHE
    ids = []
    try:
        with open(TALENT_CFG_PATH, encoding='utf-8') as f:
            d = json.load(f)
        st = d.get('SkillTalent') or {}
        bids = set()
        for v in st.values():
            _h = (v or {}).get('hash', {}) if isinstance(v, dict) else {}
            _b = int(_h.get('bid', 0) or 0)
            if 0 < _b <= 0xffff:
                bids.add(_b)
        ids = sorted(bids)
        log('server.log', 'talent_list loaded: %d bids <- %s' % (len(ids), TALENT_CFG_PATH))
    except Exception as e:
        log('server.log', '!! talent_list load failed: %r' % (e,))
        ids = []
    _TALENT_LIST_CACHE = ids
    return ids


# ★ 更换（旧表只有 1117 条且对装备类错位）：
#   新表 server/item_config.json 由 tools/extract_item_v2.py 提取，
#   **3535 条**，字段顺序从 config_item.luac proto[0] 的字节码逐条读出（bid,name,type,lev,...）。
ITEM_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             'item_config.json')
_ITEM_IDS = None




_ITEM_TYPES = None


GIFT_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'item_gift.json')
_GIFT_CFG = None


def gift_contents(bid):
    """礼包 bid → [(item_bid, num), ...]（来自 config_item_gift.luac，已提取）。

    ★ 依据：客户端 `config_item_gift.luac` 的平铺映射
      `[None, 礼包bid, 物品bid, 数量]`（tools/extract_item_gift.py 提取，496 个礼包 / 5353 条）。
    ⚠ 只覆盖 `Config.ItemGift`；`ItemNewGift` / `SelectGift` **未提取** ⇒ 部分礼包
      （如 `30010` 10级礼包）**不在此表**，打开不会给东西（已如实记录）。
    """
    global _GIFT_CFG
    if _GIFT_CFG is None:
        try:
            with open(GIFT_CFG_PATH, encoding='utf-8') as f:
                _GIFT_CFG = json.load(f)
            log('server.log', 'item gift table loaded: %d 礼包' % len(_GIFT_CFG))
        except Exception as e:
            _GIFT_CFG = {}
            log('server.log', '!! item gift table load failed: %r' % (e,))
    return _GIFT_CFG.get(str(int(bid))) or []


def item_type_of(bid):
    """取物品的 `type`（config_item.json 位置数组的 idx3）。

    ★ 实测样本：「10级速度符」=33、「100打造石」=32（消耗品/材料）。
    ⚠ 装备的 type 取值区间**尚未逐个取证** ⇒ 故做成可配置映射 `equip_type_slot`，
      **不自行猜哪个数字是武器/护手**。
    """
    global _ITEM_TYPES
    if _ITEM_TYPES is None:
        try:
            with open(ITEM_CFG_PATH, encoding='utf-8') as f:
                _ITEM_TYPES = json.load(f)
        except Exception as e:
            _ITEM_TYPES = {}
            log('server.log', '!! item type table load failed: %r' % (e,))
    v = _ITEM_TYPES.get(str(int(bid)))
    if isinstance(v, dict):
        t = v.get('type')
        return int(t) if isinstance(t, int) else None
    if isinstance(v, list) and len(v) > 3 and isinstance(v[3], int):
        return int(v[3])       # 兼容旧格式
    return None




# ---------------------------------------------------------------------------
# ★★ 通用默认响应器（2026-09-18 体检补实现）
#
#   背景：真机发过 128 个 CMD，服务端实现了 119 个 —— 剩下 62 个里，
#   有 49 个的 SC 定义**不含未解子表**（`D|Dsc*|`），可以按规格生成**安全默认响应**；
#   另外 13 个含未解子表，按项目纪律**不实现**（不猜编码）。
#
#   ★ 诚实原则：默认响应**不编造具体数值/内容** ——
#     第一个字段若名为 `code` 回 1（成功），其余 string=''/table=空/数值=0。
#     客户端拿到"成功但空"不会卡死，也不会显示假数据。
# ---------------------------------------------------------------------------
# ★ R81：饱食度满值 = 客户端 `build_ctrl.luac` proto#2 的初始值
HUNGER_MAX = 65535

# ★ R88：阵型表 `f_type -> need_lev`（`config_formation.luac` 实提取）。
#   1 流云阵(1) / 2 天攻阵(20) / 4 疾风阵(32) / 3 地御阵(36) / 5 破雷阵(42)
#   / 6 飘雨阵(46) / 7 锋矢阵(50)。阵型容量 **5**（每组阵法的位置表都是 5 项）。
_FORMATIONS = [(1, 1), (2, 20), (4, 32), (3, 36), (5, 42), (6, 46), (7, 50)]

# ★ R89：**阵法书**（`config_formation.luac` 里每个阵法挂的物品 id，已在
#   `server/item_config.json` 里逐条核对过名字与 lev）：
#     36053 天攻阵法书(20) / 36056 疾风阵法书(32) / 36052 地御阵法书(36)
#     36055 破雷阵法书(42) / 36054 飘雨阵法书(46) / 36057 锋矢阵法书(50)
#   「流云阵」(f_type=1, need_lev=1) 是**初始阵**，配置里没有对应的书。
FORMATION_BOOKS = (36053, 36056, 36052, 36055, 36054, 36057)

_GENERIC_DEFAULT_CMDS = frozenset([
    # ★ R80：**10640 已移出**（它现在是专用分支）—— 不移出的话通用默认响应会先命中，
    #   专用实现**永远不执行**（实测日志 `<< 10640 SC_10640 默认响应`）。
    #   这类"分发顺序遮蔽"由 `tools/lint_dispatch_shadow.py` 自动抓（本次就是它报出来的）。
    # ★★ 2026-09-19（R48）：**15405 已移出** —— 挂机轮次查询（CS 空 → SC{loop_count:u16}）。
    #   原先落在这里回**通用零值** `loop_count=0` ⇒ 客户端"没有轮次可跑"，
    #   挂机**从不启动**（真机证据：参与→寻路→15405→此后无任何命令；
    #   等级 150/70 与地图数据均已排除）。已写专用实现（DB 驱动）。
    # ★★ 2026-09-19（R48）：**16400 已移出** —— 成就面板，真机发了 **450 次**，
    #   原先落在这里回全零 ⇒ 成就页永远空。已写专用实现
    #   （取 `chengjiu_progress` + `_chengjiu.json` 的 342 条成就表）。
    #   ⚠ 同一坑的**第五次**。本项目已加机械防护：每次收尾跑
    #     `python tools/lint_dispatch_shadow.py`（应输出"无分发遮蔽"）。
    # ★★ 2026-09-19（R46）：**13042 已移出**。它是爬塔进度面板
    #   （`SC_13042{high_floor,ceng_list,status,cur_ceng,left_time,clear_list,count}`），
    #   真机发了 **183 次**，原先落在这里回全零 ⇒ 面板永远没进度。
    #   已写专用实现（取 `dungeon_progress`，与 21301 同源）。
    #   ⚠ 这是**第二次**踩同一个坑（前有 12931/round40、13401/13403）：
    #     **新增专用实现时，必须同时把命令从本集合移出** —— 通用分支位置靠前，
    #     不移出就会被它抢先返回空表/零值。
    # ★ 2026-09-19（round36）：**10999 已移出**。它是 **CS-only 消息**
    #   （`CS_10999{msg:string}`，协议里**没有 SC 定义**），属"客户端上报"型，
    #   客户端不期待回包（同 10001 CSFirstPack）。留在集合里会让服务端回一个
    #   0 字节空帧，把客户端推进未知命令分支。移除后自然落到"不应答"。
    # ★ 13401 / 13403 / 12823 已**移出**本集合（2026-09-18）—— 它们已用**真实配置**
    #   写了专用实现（商城 134 件 / 伙伴 53 个）。⚠ 通用分支在本文件里**位置靠前**，
    #   若不移出会被它抢先返回空表。
    # ★★ 2026-09-18 追补：原本因 SC 含 `D|Dsc*|` 未解子表而被排除的 13 条。
    #   **关键洞察：本响应器对 `table(...)` 字段一律发【空表】(计数 0)
    #   ⇒ 根本不需要编码子表 ⇒ 不存在"猜子表编码"的问题。**
    #   父消息的标量字段按规格给默认值（code=1 / 其余 0），表字段给空表。
    #   客户端拿到"成功但空"，可以正常显示（空列表），不会卡死，也不会显示假数据。
    #   ⇒ 这样既**守纪律**（不猜子表编码），又能把覆盖率做到 100%。
    #   ⚠ 若将来要填真实内容，需先用 tools/dsc_spec.py 解出对应子表字段顺序。
    # ★ 2026-09-19：**11215 / 10800 已移出**（见下方专用分支注释）—— 11215 用完整
    #   伙伴基础表（53 个真实伙伴）返回**真实列表**；10800 返回**系统欢迎邮件**（真实物品附件）。
    #   通用分支位置靠前，不移出会被它抢先返回空表。
    # ★★ 2026-09-19 追补：**10924 已移出**（见专用分支注释）—— 用 config_function.json
    #   （91 条真实功能/活动开放表）返回 is_open=1 且 open_lev<=玩家等级 的**真实活动列表**。
    # ★★★ 2026-09-19 追补：**16603 已移出**（见专用分支注释）—— CS 规格 = {bid:u32}
    #   （AutoConstruct cs/16603 = ['bid__I']；真机 8 字节 = 4 真实 + 4 缓冲区残留），
    #   专用分支按 SC_16603 全 8 字段结构编码（aim_list 空表，不编造子表内容）。
    # ★★ 2026-09-19（R47）：**11300 已移出** —— 荣耀竞技场主面板。
    #   真机发了 **259 次**（最高频之一），原先落在这里回全零 ⇒ 面板无进度。
    #   已写专用实现（取 `arena_state`/`arena_record` 的真实值）。
    #   ⚠ 同一坑的**第四次**（12931 → 13401/13403 → 13042 → 11300/11308）：
    #     新增专用实现**必须同时移出本集合**，否则通用分支抢先返回零值/空表。
    # ================= ★★ round39：真机回放 GAP 中的「查询型」===============
    #   背景：tools/replay_captures.py 发现 73 条「有 SC 规格但无应答」命令。
    #   用 tools/triage_gaps.py 分类后：
    #     · 65 条客户端**有**处理器（真在等数据）  → 真实缺口
    #     ·  8 条客户端无处理器（上报/广播型）      → 无应答无害
    #   再把 65 条按「SC 里是否含 code/result/tips」拆开：
    #     · 39 条**查询型**（无结果码）⇒ 缺数据时回"零值/空表"是**真话**
    #        （例如 17001{max_gate} 客户端判 >=9 显示"活动已完成"，新号回 0 正确；
    #          16601/16602 节日列表内容全由服务端下发，本服无内容 ⇒ 空表；
    #          12901… 排行榜、1300x/1304x 副本与爬塔进度 = 本服无该玩法 ⇒ 零值）
    #     · 26 条**操作型**（含 code/result/tips）⇒ 回"成功"就是撒谎
    #        （如 10206 传送结果、15200/15400 NPC 操作、17301 竞速）
    #        ⇒ **保持不应答**，另见 round39 文档的"操作型 GAP 清单"。
    #   ⚠ 判据严格做**减法**：宁可少答，不可错答。
    #   ★ round40：**12901 / 12902 / 12911 / 12912 / 12931 已移出** ——
    #     它们改用下方**专用实现**（12901 战力榜 / 12931 等级榜回真实数据，
    #     另 3 个榜单指标未取证 ⇒ 回空榜）。专用分支位置靠后，
    #     不移出会被本集合抢先返回全零。
    # ★★ 2026-09-28（R53）：**13321 / 16664 补入** ——
    #   两条都是真机在发、而**服务端一句话都不回**的命令（本轮 `_probe_gaps.py` 现场普查发现）：
    #     · `13321` 好友申请列表  SC{request_list:table(15 字段)}  ← 无结果码 ⇒ **查询型**
    #     · `16664` 获取限时充值返利活动数据
    #              SC{msg:s, bid:u32, remain_sec:u32, status:u32, end_time:u32,
    #                 rate:u32, client_reward:s}                ← 无结果码 ⇒ **查询型**
    #   判据沿用 round39：**SC 里没有 code/result/tips ⇒ 缺数据时回"零值/空表"是真话**。
    #   本服确实没有好友申请、也没有充值返利活动 ⇒ 空表/零值即真话；
    #   比"完全不回包"（客户端干等）好。
    # ★★ 2026-09-28（R50）：**17309 已移出** —— 魂师大赛排行榜改为真实 `rank_list`
    #   （数据源 `roles` + 各自 `race_state.score`）。专用分支位置靠后，不移出会被遮蔽。
])

# ★★★ round41：**操作型未实现命令**（真机发过、客户端**有**处理器、SC 带结果码）
#   这些不能用"零值成功"应答 —— 那会让客户端以为操作真的生效；
#   也不宜一直沉默 —— 客户端在等，面板会卡住。
#   按本服务端对 2000x 的既有先例，**明确回失败**：
#     code/result = 0（失败）+ msg = '该功能暂未开放'
#   来源：round39 `tools/triage_gaps.py` 把 65 条真实缺口按"SC 是否含
#   code/result/tips"分出的**操作型**部分；查询型 39 条已并入上面的默认集合。
#   ★ round42：**13402 已移出**（26 → 25）—— 它是 134xx 限购商店的**购买**，
#     已按 12805 的完整流程实现（选币 → 限购 → 扣费 → 发货 → 记限购），
#     不再是"未开放"。专用分支位置靠后，不移出会被本集合抢先回"未开放"。
_UNSUPPORTED_ACTION_CMDS = frozenset([
    # ★ R190：**15200/19500 已移出**（改专用实现，见下）
    # ★★ 2026-09-28（R50）：**17301 / 17501 已移出** ——
    #   17301 竞速主状态改为 DB 驱动真实值（`race_state`）；
    #   17501 宗门战保留诚实回失败，但改为**回显 CS 的 type**（专用 handler）。
    #   两者专用分支位置靠后，不移出会被本集合抢先回"未开放"（lint 会报遮蔽）。
    # ★★ 2026-09-19（R48）：**15400 已移出** —— 挂机启动（CS 空 → SC{code,msg}）。
    #   回"未开放"(code=0) 会让挂机链**断在这里**：真机证据链
    #     15405(轮次) → **15400(启动)** → 15402{mission_bid}(任务→地图/坐标)
    #   改为回成功，客户端才会继续发 `15402` —— 而 `15402` 的 CS 正是
    #   **我们要找的"挂机线 ↔ 任务"映射**（见下方专用实现）。
])
_UNSUPPORTED_MSG = '该功能暂未开放'

# [P2B-migrated protocol/fields.py::_sc_fields] _SC_FIELDS_CACHE = None


# [P2B-migrated protocol/fields.py::_sc_fields] def _sc_fields(cmd):
# [P2B-migrated protocol/fields.py::_sc_fields]     """返回该 CMD 的 SC 字段列表 [{'name':..,'type':..}, ...]（读 protocol/fields.json）。"""
# [P2B-migrated protocol/fields.py::_sc_fields]     global _SC_FIELDS_CACHE
# [P2B-migrated protocol/fields.py::_sc_fields]     if _SC_FIELDS_CACHE is None:
# [P2B-migrated protocol/fields.py::_sc_fields]         _SC_FIELDS_CACHE = {}
# [P2B-migrated protocol/fields.py::_sc_fields]         try:
# [P2B-migrated protocol/fields.py::_sc_fields]             p = os.path.join(os.path.dirname(HERE), 'protocol', 'fields.json')
# [P2B-migrated protocol/fields.py::_sc_fields]             with open(p, encoding='utf-8') as f:
# [P2B-migrated protocol/fields.py::_sc_fields]                 raw = json.load(f)
# [P2B-migrated protocol/fields.py::_sc_fields]             for k, v in raw.items():
# [P2B-migrated protocol/fields.py::_sc_fields]                 try:
# [P2B-migrated protocol/fields.py::_sc_fields]                     c = int(v.get('cmd'))
# [P2B-migrated protocol/fields.py::_sc_fields]                 except Exception:
# [P2B-migrated protocol/fields.py::_sc_fields]                     continue
# [P2B-migrated protocol/fields.py::_sc_fields]                 if (v.get('dir') or '') != 'sc':
# [P2B-migrated protocol/fields.py::_sc_fields]                     continue
# [P2B-migrated protocol/fields.py::_sc_fields]                 _SC_FIELDS_CACHE.setdefault(c, v.get('fields') or [])
# [P2B-migrated protocol/fields.py::_sc_fields]         except Exception as e:
# [P2B-migrated protocol/fields.py::_sc_fields]             log('server.log', '!! _sc_fields load failed: %r' % (e,))
# [P2B-migrated protocol/fields.py::_sc_fields]     return _SC_FIELDS_CACHE.get(int(cmd), [])


def db_vip_level(rid):
    """★ R140b：**从 DB 直读** `roles.vip_level`。

    为什么不用 `role_state(self.cfg)`：那是**会话开始时装载的配置**，
    `vip_level` 在里面是旧值 ⇒ 改了 DB 后读不到（本批实测 `16704`/`16706` 都读成 0）。
    """
    try:
        con = db_conn()
        r = con.execute('SELECT vip_level FROM roles WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        return int(r[0] or 0) if r else 0
    except Exception as e:
        log('tcp.log', '  !! db_vip_level failed: %r' % (e,))
        return 0


_MARKET_CFG = None


def market_cfg():
    """★ R243：摆摊配置（`server/cfg/config_market.json`，R111 批量解构产物）。

    子表（**逐个按客户端 `market_ctrl`/`market_view` 的用法取证**）：
      · `MarketCanSellItem`      = **可上架物品**（bid 列表）
      · `MarketItemPrice[bid]`   = `{min_price, base_price, max_price}` ⇒ **上架价格区间**
      · `MarketBid2Type[bid]`    = 分类（`MarketType` 的下标）
      · `MarketYinbiBid2Type[bid]` = `{batch_limit, label, career, type}`
    """
    global _MARKET_CFG
    try:
        if _MARKET_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_market.json')
            with open(p, encoding='utf-8') as f:
                _MARKET_CFG = json.load(f)
            log('server.log', 'market cfg loaded: %s' % list(_MARKET_CFG.keys()))
        return _MARKET_CFG
    except Exception as e:
        log('server.log', '!! market cfg load failed: %r' % (e,))
        return {}


def market_ensure_cols():
    """★ R243：`role_market_goods` 建表 + **幂等补列**。

    ★ 纪律第 4 条：`CREATE TABLE IF NOT EXISTS` **不给旧表加列** ⇒ 旧库会静默缺列。
      新增 `state`：**0 = 在架 / 1 = 已下架**（等 `13817` 提取回背包）。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_market_goods (
        rid INTEGER, market_id INTEGER, item_bid INTEGER, item_num INTEGER,
        sell_num INTEGER, sell_type INTEGER, price INTEGER, time_out INTEGER,
        state INTEGER DEFAULT 0, PRIMARY KEY (rid, market_id))""")
    cols = set(r[1] for r in con.execute('pragma table_info("role_market_goods")'))
    if 'state' not in cols:
        con.execute('ALTER TABLE role_market_goods ADD COLUMN state INTEGER DEFAULT 0')
    con.commit()
    db_release(con)


def market_goods(rid, state=0):
    """★ R140/R243：摆摊货品（`13806` 在架 / `13826` 我的货品）。没有 ⇒ 空（真话）。"""
    out = []
    try:
        market_ensure_cols()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT market_id,item_bid,item_num,sell_num,sell_type,'
                             'price,time_out,state FROM role_market_goods '
                             'WHERE rid=? AND state=? ORDER BY market_id',
                             (int(rid), int(state))):
            out.append(tuple(int(r[k] or 0) for k in
                             ('market_id', 'item_bid', 'item_num', 'sell_num',
                              'sell_type', 'price', 'time_out', 'state')))
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! market_goods failed: %r' % (e,))
    return out


def market_next_id(rid):
    """★ R243：下一个 `market_id`（从 1 递增；空表 ⇒ 1）。"""
    market_ensure_cols()
    con = db_conn()
    r = con.execute('SELECT MAX(market_id) FROM role_market_goods WHERE rid=?',
                    (int(rid),)).fetchone()
    db_release(con)
    return int((r[0] if r else 0) or 0) + 1


def market_price_range(bid):
    """★ R243：`MarketItemPrice[bid]` → `(min_price, base_price, max_price)`；无配置 ⇒ 全 0。"""
    d = ((market_cfg().get('MarketItemPrice') or {}).get(str(int(bid)))) or {}
    h = d.get('hash') or {}
    return (int(h.get('min_price') or 0), int(h.get('base_price') or 0),
            int(h.get('max_price') or 0))


def market_can_sell(bid):
    """★ R243：该物品是否在 `MarketCanSellItem` 里（**上架白名单**，权威配置）。"""
    lst = market_cfg().get('MarketCanSellItem') or []
    b = int(bid)
    for x in lst:
        if isinstance(x, int) and x == b:
            return True
    return False


def market_find_bag_item(rid, item_id):
    """★ R243：按实例 id 在**全部背包**里找一件物品（回 dict 或 None）。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT * FROM bag_items WHERE rid=? AND item_id=? LIMIT 1',
                        (int(rid), int(item_id))).fetchone()
        out = dict(r) if r else None
        con.row_factory = None
        db_release(con)
        return out
    except Exception as e:
        log('tcp.log', '  !! market_find_bag_item failed: %r' % (e,))
        return None


def market_sell_one(rid, item_id, price, sell_num, sell_type):
    """★ R243：**真的上架**（`13811` 单条 / `13810` 批量共用）。

    交易闭环（**不允许"假装成功"**，纪律第 44/46 条）：
      ① 背包里必须有该 `item_id`，且 `quantity >= sell_num`
      ② 该 `bid` 必须在 `MarketCanSellItem`（权威白名单）里
      ③ 价格必须在 `MarketItemPrice[bid]` 的 `[min_price, max_price]` 内（有配置时）
      ④ **真扣背包** + 写 `role_market_goods`（`state=0` 在架）
    返回 `(ok, msg, market_id)`。
    """
    try:
        it = market_find_bag_item(rid, item_id)
        if it is None:
            return False, '背包里找不到该物品', 0
        bid = int(it.get('bid') or 0)
        qty = int(it.get('quantity') or 0)
        num = int(sell_num or 0) or qty
        if num <= 0 or num > qty:
            return False, '数量不足', 0
        if not market_can_sell(bid):
            return False, '该物品不可上架', 0
        lo, base, hi = market_price_range(bid)
        pr = int(price or 0) or base
        if hi and (pr < lo or pr > hi):
            return False, '价格超出允许区间', 0
        market_ensure_cols()
        mid = market_next_id(rid)
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_market_goods '
                    '(rid,market_id,item_bid,item_num,sell_num,sell_type,price,'
                    'time_out,state) VALUES (?,?,?,?,?,?,?,?,0)',
                    (int(rid), mid, bid, num, num, int(sell_type or 0) & 0xff,
                     pr, 0))
        con.commit()
        db_release(con)
        if num >= qty:
            db_bag_delete(rid, [int(item_id)])
        else:
            db_bag_set_quantity(rid, int(item_id), qty - num)
        log('tcp.log', '  << 上架 ok rid=%d item_id=%d bid=%d num=%d price=%d '
                       'market_id=%d（扣背包 %d→%d）'
            % (rid, item_id, bid, num, pr, mid, qty, qty - num))
        return True, '', mid
    except Exception as e:
        log('tcp.log', '  !! market_sell_one failed: %r' % (e,))
        return False, '上架失败', 0


def market_take_off(rid, market_id):
    """★ R243：下架（`state` 0 → 1）。**物品仍留在摊位上**，由 `13817` 提取回背包。"""
    market_ensure_cols()
    con = db_conn()
    n = con.execute('UPDATE role_market_goods SET state=1 WHERE rid=? AND market_id=? '
                    'AND state=0', (int(rid), int(market_id))).rowcount
    con.commit()
    db_release(con)
    return int(n or 0)


def market_pickup(rid, market_id):
    """★ R243：提取（已下架的货品 → **真回背包**，并删除该行）。返回 `(bid, num)`。"""
    market_ensure_cols()
    con = db_conn()
    r = con.execute('SELECT item_bid,sell_num FROM role_market_goods '
                    'WHERE rid=? AND market_id=? AND state=1',
                    (int(rid), int(market_id))).fetchone()
    if r is None:
        db_release(con)
        return None
    bid, num = int(r[0] or 0), int(r[1] or 0)
    con.execute('DELETE FROM role_market_goods WHERE rid=? AND market_id=?',
                (int(rid), int(market_id)))
    con.commit()
    db_release(con)
    if num > 0:
        db_bag_add(rid, bid, num)
    return bid, num


def db_market_goods_add(rid, market_id, item_bid, item_num=1, price=0):
    try:
        market_ensure_cols()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_market_goods '
                    '(rid,market_id,item_bid,item_num,sell_num,sell_type,price,'
                    'time_out,state) VALUES (?,?,?,?,?,?,?,?,0)',
                    (int(rid), int(market_id), int(item_bid), int(item_num),
                     0, 1, int(price), 0))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_market_goods_add failed: %r' % (e,))
        return False


def db_build_state(rid):
    """★ R140：建筑技能状态（`13741`）。没有行 ⇒ (0, [])（真话）。"""
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_build ('
                    'rid INTEGER PRIMARY KEY, lev INTEGER)')
        con.execute('CREATE TABLE IF NOT EXISTS role_build_learn ('
                    'rid INTEGER, item_bid INTEGER, PRIMARY KEY (rid, item_bid))')
        con.commit()
        r = con.execute('SELECT lev FROM role_build WHERE rid=?', (int(rid),)).fetchone()
        learned = [int(x[0]) for x in con.execute(
            'SELECT item_bid FROM role_build_learn WHERE rid=? ORDER BY item_bid',
            (int(rid),))]
        db_release(con)
        return (int(r[0] or 0) if r else 0), learned
    except Exception as e:
        log('tcp.log', '  !! db_build_state failed: %r' % (e,))
        return 0, []


def db_build_set(rid, lev=None, learn=None):
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_build ('
                    'rid INTEGER PRIMARY KEY, lev INTEGER)')
        con.execute('CREATE TABLE IF NOT EXISTS role_build_learn ('
                    'rid INTEGER, item_bid INTEGER, PRIMARY KEY (rid, item_bid))')
        if lev is not None:
            con.execute('INSERT OR REPLACE INTO role_build VALUES (?,?)',
                        (int(rid), int(lev)))
        if learn is not None:
            con.execute('INSERT OR REPLACE INTO role_build_learn VALUES (?,?)',
                        (int(rid), int(learn)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_build_set failed: %r' % (e,))
        return False


def role_count():
    """★ R149：本服角色总数（`roles` 表的行数）—— `13227.role_num` 用。"""
    try:
        con = db_conn()
        n = con.execute('SELECT COUNT(*) FROM roles').fetchone()[0]
        db_release(con)
        return int(n or 0)
    except Exception:
        return 0


def guild_rows(rid):
    """★ R149：宗门列表的 17 字段行（本服最多 1 个 —— `role_guild` 一行）。

    能取真实值的：`guild_name`/`head_name`/`head_career`/`head_sex`/`vip`/`power`/`role_count`。
    其余字段本服无源 ⇒ 0 / 空串（**不编造**）。
    """
    out = []
    try:
        db_guild_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        g = con.execute('SELECT name FROM role_guild WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        if not g:
            return out
        rs = role_state({})
        try:
            pw = int(role_power({}) or 0)
        except Exception:
            pw = 0
        out.append({
            'index': 0, 'gid': int(rid), 'srv_id': '', 'realm': 0,
            'vip': db_vip_level(rid) & 0xff,
            'guild_name': str(g['name'] or ''),
            'head_name': str(rs.get('name') or ''),
            'head_career': int(rs.get('career') or 0) & 0xff,
            'lev': 0, 'role_count': 1, 'max_role_count': 0, 'applyed': 0,
            'power': pw, 'all_assets': 0, 'is_recommend': 0,
            'head_sex': int(rs.get('sex') or 0) & 0xff, 'is_invited': 0,
        })
    except Exception as e:
        log('tcp.log', '  !! guild_rows failed: %r' % (e,))
    return out


def zone_dress_rows():
    """★ R148：空间装扮 `(head_bids, zone_bids)` —— 按配置的 `type` 分流。

    `config_friend_zone_data`：
        `FriendZoneSkin`(type:1)    ⇒ 头像框 ⇒ head_list
        `FriendZoneSkinBid`(type:2) ⇒ 空间装饰 ⇒ zone_list
    """
    heads, zones = [], []
    try:
        import os as _os
        p = _os.path.join(_os.path.dirname(HERE), 'server', 'cfg', 'config_friend_zone_data.json')
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        for key, bucket in (('FriendZoneSkin', heads), ('FriendZoneSkinBid', zones)):
            for k, v in (d.get(key) or {}).items():
                h = _h(v)
                try:
                    bucket.append(int(k))
                except Exception:
                    if h.get('icon'):
                        bucket.append(int(h['icon']))
    except Exception as e:
        log('tcp.log', '  !! zone_dress_rows failed: %r' % (e,))
    return sorted(set(heads)), sorted(set(zones))


def demon_cfg():
    """★ R154：魂兽配置（`config_demon`）。"""
    global _DEMON_CFG
    try:
        if _DEMON_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_demon.json')
            with open(p, encoding='utf-8') as f:
                _DEMON_CFG = json.load(f)
            log('server.log', 'demon cfg loaded: %s' % list(_DEMON_CFG.keys()))
        return _DEMON_CFG
    except Exception as e:
        log('server.log', '!! demon cfg load failed: %r' % (e,))
        return {}


def demon_one(bid):
    """`config_demon` 里按 bid 取一条（兼容多种键名）。"""
    try:
        for k, v in (demon_cfg().get('Demon') or demon_cfg()).items():
            h = _h(v)
            if str(k) == str(bid) or int(h.get('id') or h.get('bid') or 0) == int(bid):
                return h
    except Exception:
        pass
    return {}


_DEMON_CFG = None


def map_npc_bids():
    """★ R163：`config_map_npc.MapNpc` 里的 **NPC bid 列表**（去重排序）。

    `MapNpc = {10010: [null, 10001, 37, 85], …}` ⇒ **第二个元素**是 npc 的 bid。
    """
    global _MAP_NPC_BIDS
    try:
        if _MAP_NPC_BIDS is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_map_npc.json')
            with open(p, encoding='utf-8') as f:
                d = json.load(f)
            out = set()
            for v in (d.get('MapNpc') or {}).values():
                if isinstance(v, list) and len(v) >= 2 and isinstance(v[1], int):
                    out.add(int(v[1]))
            _MAP_NPC_BIDS = sorted(out)
            log('server.log', 'map npc bids: %d' % len(_MAP_NPC_BIDS))
        return _MAP_NPC_BIDS
    except Exception as e:
        log('server.log', '!! map_npc_bids failed: %r' % (e,))
        return []


_MAP_NPC_BIDS = None


def db_mail_init():
    """★ R161：建邮件表 `role_mail`（rid, id, from_name, subject, content,
    assets_json, items_json, send_time, read_time, time_out）。"""
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_mail (
            rid INTEGER, id INTEGER, from_name TEXT, subject TEXT, content TEXT,
            assets TEXT, items TEXT, send_time INTEGER, read_time INTEGER,
            time_out INTEGER, PRIMARY KEY (rid, id))""")
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_mail_init failed: %r' % (e,))
        return False


def db_mail_list(rid):
    """邮件列表（按 id 倒序）—— 真实 DB。"""
    out = []
    try:
        db_mail_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT * FROM role_mail WHERE rid=? ORDER BY id DESC',
                             (int(rid),)):
            out.append(dict(r))
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_mail_list failed: %r' % (e,))
    return out


def db_mail_add(rid, subject, content, from_name='系统', assets=None, items=None):
    try:
        db_mail_init()
        con = db_conn()
        row = con.execute('SELECT COALESCE(MAX(id),0)+1 FROM role_mail WHERE rid=?',
                          (int(rid),)).fetchone()
        mid = int(row[0])
        con.execute('INSERT INTO role_mail VALUES (?,?,?,?,?,?,?,?,?,?)',
                    (int(rid), mid, from_name, subject, content,
                     json.dumps(assets or []), json.dumps(items or []),
                     int(time.time()), 0, 0))
        con.commit()
        db_release(con)
        return mid
    except Exception as e:
        log('tcp.log', '  !! db_mail_add failed: %r' % (e,))
        return 0


def db_mail_read(rid, mid):
    try:
        db_mail_init()
        con = db_conn()
        cur = con.execute('UPDATE role_mail SET read_time=? WHERE rid=? AND id=? AND read_time=0',
                          (int(time.time()), int(rid), int(mid)))
        n = cur.rowcount
        con.commit()
        db_release(con)
        return n > 0
    except Exception:
        return False


def db_point_state(rid):
    """★ R161：伙伴点数（`10421`）—— 没有行 ⇒ (0,0)。"""
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_point ('
                    'rid INTEGER PRIMARY KEY, cur_point INTEGER, bought INTEGER)')
        con.commit()
        r = con.execute('SELECT cur_point, bought FROM role_point WHERE rid=?',
                        (int(rid),)).fetchone()
        db_release(con)
        return (int(r[0] or 0), int(r[1] or 0)) if r else (0, 0)
    except Exception:
        return 0, 0


def db_point_set(rid, cur=None, bought=None):
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_point ('
                    'rid INTEGER PRIMARY KEY, cur_point INTEGER, bought INTEGER)')
        con.execute('INSERT OR IGNORE INTO role_point VALUES (?,0,0)', (int(rid),))
        if cur is not None:
            con.execute('UPDATE role_point SET cur_point=? WHERE rid=?', (int(cur), int(rid)))
        if bought is not None:
            con.execute('UPDATE role_point SET bought=? WHERE rid=?', (int(bought), int(rid)))
        con.commit()
        db_release(con)
        return True
    except Exception:
        return False


def asset_label_map():
    """★ R160：`config_game_data.CodeToAssets` ⇒ `{资产名: 编号}`（下标即 `label`）。

    `CodeToAssets = [null,"gold","coin","coupon","exp","sinew",…,"courage"(16),"charm"(17),…]`
    """
    global _ASSET_LABELS
    try:
        if _ASSET_LABELS is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_game_data.json')
            with open(p, encoding='utf-8') as f:
                d = json.load(f)
            arr = d.get('CodeToAssets') or []
            _ASSET_LABELS = {str(v): i for i, v in enumerate(arr) if v}
            log('server.log', 'asset labels: %d' % len(_ASSET_LABELS))
        return _ASSET_LABELS
    except Exception as e:
        log('server.log', '!! asset_label_map failed: %r' % (e,))
        return {}


_ASSET_LABELS = None


def equip_one(rid, item_id):
    """★ R153：按 `equip_items.item_id` 取一件装备；没有 ⇒ None。"""
    try:
        r, _p = db_equip_rows(rid)
        for e in (r or []):
            if int(e['id']) == int(item_id):
                return e
    except Exception:
        pass
    return None




def group_control_cfg():
    """★ R152：合服/世界进程配置（`config_group_control`）。"""
    global _GC_CFG
    try:
        if _GC_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_group_control.json')
            with open(p, encoding='utf-8') as f:
                _GC_CFG = json.load(f)
            log('server.log', 'group_control cfg loaded: %s' % list(_GC_CFG.keys()))
        return _GC_CFG
    except Exception as e:
        log('server.log', '!! group_control cfg load failed: %r' % (e,))
        return {}


def group_first_tar_val():
    """`GroupControl` 的第一条 `tar_val`（配置里的**真实目标值**，实测 7000）。"""
    try:
        gc = group_control_cfg().get('GroupControl') or {}
        for k in sorted(gc.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
            h = _h(gc[k])
            if h.get('tar_val') is not None:
                return int(h['tar_val'])
    except Exception:
        pass
    return 0


def group_is_open():
    """`ControlSys` 里 `is_open=1` 的条数 > 0 ⇒ 1（真实配置推导）。"""
    try:
        cs = group_control_cfg().get('ControlSys') or {}
        for k in cs:
            if int(_h(cs[k]).get('is_open') or 0) == 1:
                return 1
    except Exception:
        pass
    return 0


_GC_CFG = None


def dungeon_cfg():
    """★ R147：副本配置（`config_dungeon_new`）。"""
    global _DUNG_CFG
    try:
        if _DUNG_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_dungeon_new.json')
            with open(p, encoding='utf-8') as f:
                _DUNG_CFG = json.load(f)
            log('server.log', 'dungeon cfg loaded: %s' % list(_DUNG_CFG.keys()))
        return _DUNG_CFG
    except Exception as e:
        log('server.log', '!! dungeon cfg load failed: %r' % (e,))
        return {}


def dungeon_rows():
    """`[(bid, count), …]` —— 来自 `Dungeon`（34 个副本）+ 配置里的 `count`。

    `buy_count`/`time`/`is_finish` 是**玩家态**、本服无源 ⇒ 由调用方补 0。
    """
    out = []
    try:
        for k, v in (dungeon_cfg().get('Dungeon') or {}).items():
            h = _h(v)
            try:
                bid = int(k)
            except Exception:
                bid = int(h.get('dung_id') or 0)
            if bid:
                out.append((bid, int(h.get('count') or 0)))
    except Exception as e:
        log('tcp.log', '  !! dungeon_rows failed: %r' % (e,))
    return sorted(out)


# ★★ C3.3-E：镇魂塔（dung 40001）爬塔配置加载与层奖励解析。
#   配置源：server/cfg/config_dungeon_tower.json → DungeonTower（普通塔 9 层，
#   map_bid 21000-21008、boss 18201-18209）。本批最小闭环只做普通塔（dung 40001）；
#   DungeonTowerHard（22000-22008，MapDung 归 dung 40002 传灵塔）不接。
#
#   每层 hash 字段（逐字段引用 config_dungeon_tower.json）：
#     map_bid    int                —— 进本后传送的场景（21000 + ceng-1）
#     boss       [null,bid,lev,?]   —— 层 boss（18200+ceng）
#     first_kill [null,item_bid,count,?]  —— 首通物品奖励
#     clear_item {"1":[null,item_bid,count,?]} —— 通关物品奖励
#     clear_asset{"1":[null,type,amount]}     —— 通关资产奖励
#
#   DungeonCodeLabel = [null,"经验","金币","阅历值","英雄经验"]（config_dungeon_new），
#   即副本奖励 gain.type：1=经验 2=金币 3=阅历值 4=英雄经验。
#   服务端写资产名映射（type→asset name）：
_DUNG_REWARD_TYPE_TO_ASSET = {1: 'exp', 2: 'coin', 3: 'experience', 4: 'hero_exp'}
_DUNG_TOWER_MAX_FLOOR = 9          # DungeonTower 共 9 层
_DUNG_TOWER_BID = 40001            # 镇魂塔 dung_id
_DUNG_TOWER_CFG = None


def dungeon_tower_cfg():
    """★ C3.3-E：加载 config_dungeon_tower.json（普通塔 9 层）。"""
    global _DUNG_TOWER_CFG
    try:
        if _DUNG_TOWER_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                             'config_dungeon_tower.json')
            with open(p, encoding='utf-8') as f:
                _DUNG_TOWER_CFG = json.load(f)
            log('server.log', 'dungeon tower cfg loaded: %s'
                % list(_DUNG_TOWER_CFG.keys()))
        return _DUNG_TOWER_CFG
    except Exception as e:
        log('server.log', '!! dungeon tower cfg load failed: %r' % (e,))
        return {}


def tower_floor_hash(ceng):
    """★ C3.3-E：取普通塔第 ceng 层 hash；越界/无配置返回 None。"""
    try:
        ceng = int(ceng)
        h = (dungeon_tower_cfg().get('DungeonTower') or {}).get(str(ceng))
        return (h or {}).get('hash')
    except Exception:
        return None


def tower_floor_reward(ceng):
    """★ C3.3-E：解析第 ceng 层奖励 → dict。

    返回：
      boss        int   —— 层 boss bid（18200+ceng）
      map_bid     int
      asset       (type:int, amount:int) or None   —— clear_asset
      items       list[(item_bid:int, count:int)] —— clear_item + first_kill
      gain_type   int/None —— 透传给 SC_21307 gain.type 的原始 type
    """
    h = tower_floor_hash(ceng)
    if not h:
        return None
    out = {'boss': 0, 'map_bid': int(h.get('map_bid') or 0),
           'asset': None, 'items': [], 'gain_type': None}
    try:
        b = h.get('boss') or []
        if len(b) >= 2 and b[1]:
            out['boss'] = int(b[1])
    except Exception:
        pass
    # clear_asset：{"1":[null,type,amount]}
    try:
        ca = (h.get('clear_asset') or {}).get('1') or []
        if len(ca) >= 3 and ca[1] and ca[2]:
            out['asset'] = (int(ca[1]), int(ca[2]))
            out['gain_type'] = int(ca[1])
    except Exception:
        pass
    # clear_item：{"1":[null,item_bid,count,?]}
    try:
        ci = (h.get('clear_item') or {}).get('1') or []
        if len(ci) >= 3 and ci[1] and ci[2]:
            out['items'].append((int(ci[1]), int(ci[2])))
    except Exception:
        pass
    # first_kill：[null,item_bid,count,?]
    try:
        fk = h.get('first_kill') or []
        if len(fk) >= 3 and fk[1] and fk[2]:
            out['items'].append((int(fk[1]), int(fk[2])))
    except Exception:
        pass
    return out


_DUNG_CFG = None


def encode_eqm_list(lst):
    """★ R146：编 `equip_items` 的行为 `role_eqm`/`partner_eqm` 的字节（16 字段）。

    供 `21400`（装备列表）与 `21414`（看他人装备）**共用** —— 两处结构完全一致。
    其余字段本服无源 ⇒ 0 / 空表（**不编造**）。
    """
    b = w_u16(len(lst))
    for _e in lst:
        b += (w_u32(_e['id']) +          # id
              w_u32(_e['bid']) +         # bid
              w_u32(_e['hero_bid']) +    # hero_bid
              w_u8(0) +                  # bind（无源）
              w_u8(30) +                  # intensify_lev（无源）
              w_u16(_e['pos'] & 0xffff) +  # pos ← slot
              w_u16(0) +                 # quantity（无源）
              w_u32(_e['ctime'] & 0xffffffff) +  # ctime
              w_u32(0) +                 # expire_ts（无源）
              w_u16(0) +                 # durable（无源）
              w_u8(0) +                  # object（无源）
              w_u16(0) +                 # attrs_ext 空表
              w_u16(0) +                 # attrs_ext_list 空表
              w_u16(0) +                 # attrs_ext_one_list 空表
              w_u16(0) +                 # jewel_list 空表
              w_u16(0))                  # str_ext_list 空表
    return b


def dung_progress_of(rid):
    """★ R146：该角色的 `dung_bid`/`floor`（读 `dungeon_progress` 的 `dung_setting`）。

    没有记录 ⇒ `(0, 0)`（真话）。
    """
    try:
        con = db_conn()
        r = con.execute("SELECT pkey FROM dungeon_progress WHERE rid=? AND ptype='dung_setting' "
                        "ORDER BY pkey LIMIT 1", (int(rid),)).fetchone()
        db_release(con)
        if r and r[0]:
            parts = str(r[0]).split('_')
            return int(parts[0] or 0), int(parts[1] or 0) if len(parts) > 1 else 0
    except Exception:
        pass
    return 0, 0


def encode_mingge_list(items):
    """★ R143：把 `role_mingge` 的行编成 `mingge_list` 的字节（13 个字段）。

    供 `19400`/`19401`/`19414` **共用** —— 三处结构完全一致，抽出来避免"改一处漏两处"。
    其中 `effect_list`/`gongming_bid_list`/`attr_ext` 三个子表本服无源 ⇒ 空表（已登记理由）。
    """
    out = w_u16(len(items))
    for _i, _m in enumerate(items):
        out += (w_u32((_i + 1) & 0xffffffff) +          # id（实例 id；用序号）
                w_u32(_m['bid'] & 0xffffffff) +         # bid
                w_u8(1) +                               # bind（已绑定）
                w_u8(_m['lev'] & 0xff) +                # lev
                w_u8(0) +                               # gongming_lev（共鸣等级；未取证 ⇒ 0）
                w_u8(_m['quantity'] & 0xff) +           # quantity
                w_u16(0) +                              # pos（未装备 ⇒ 0）
                w_u32(_m['hero_bid'] & 0xffffffff) +    # hero_bid
                w_u32(_m['ctime'] & 0xffffffff) +       # ctime
                w_u16(0) +                              # effect_list（本服无源）
                w_u8(0) +                               # gongming_holes
                w_u16(0) +                              # gongming_bid_list
                w_u16(0))                               # attr_ext
    return out


def db_mingge_one(rid, bid):
    """★ R143：取一个命格（`role_mingge`）；没有 ⇒ None。"""
    for _m in db_mingge_list(rid):
        if int(_m['bid']) == int(bid):
            return _m
    return None


def db_mingge_del(rid, bids):
    """★ R143：按 bid 列表删除命格（`19404`）。返回**实际删掉**的个数。"""
    n = 0
    try:
        con = db_conn()
        for b in bids:
            cur = con.execute('DELETE FROM role_mingge WHERE rid=? AND bid=?',
                              (int(rid), int(b)))
            n += cur.rowcount
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_mingge_del failed: %r' % (e,))
    return n


def worship_rows():
    """★ R139：膜拜条目 `[(type, lev, exp, used), …]`（来自 `WorshipType` 5 项）。

    元素 4 个字段**逐个**来自配置：`type`/`lev`/`exp`/`used ← use`。
    """
    out = []
    try:
        wt = tree_cfg().get('WorshipType') or {}
        for k in sorted(wt.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
            h = _h(wt[k])
            out.append((int(h.get('type') or 0), int(h.get('lev') or 0),
                        int(h.get('exp') or 0), int(h.get('use') or 0)))
    except Exception as e:
        log('tcp.log', '  !! worship_rows failed: %r' % (e,))
    return out


def first_hero(rid):
    """玩家第一个伙伴 `(bid, color)` —— 取不到 ⇒ (0, 0)（真话）。"""
    try:
        hs = db_hero_list(rid) or []
        if hs:
            h = hs[0]
            return int(h.get('bid') or 0), int(h.get('color') or 0)
    except Exception:
        pass
    return 0, 0


def tree_cfg():
    """★ R138：摇钱树/膜拜配置（`config_guild_tree_data`）。"""
    global _TREE_CFG
    try:
        if _TREE_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                             'config_guild_tree_data.json')
            with open(p, encoding='utf-8') as f:
                _TREE_CFG = json.load(f)
            log('server.log', 'tree cfg loaded: %s' % list(_TREE_CFG.keys()))
        return _TREE_CFG
    except Exception as e:
        log('server.log', '!! tree cfg load failed: %r' % (e,))
        return {}


def tree_static(key, default=0):
    """`StaticData.<key>.val`（如 `attr_delay` ⇒ 48）—— 真实的配置常量。"""
    try:
        sd = _h(tree_cfg().get('StaticData'))
        v = sd.get(key)
        h = _h(v) if isinstance(v, dict) else None
        if h and 'val' in h:
            return int(h['val'])
    except Exception:
        pass
    return default


def tree_worship_name(lev=0):
    """该树等级对应的膜拜类型名（`WorshipType[].type_name`，如"北斗"）。"""
    try:
        wt = tree_cfg().get('WorshipType') or {}
        keys = sorted(wt.keys(), key=lambda x: int(x) if str(x).isdigit() else 0)
        if not keys:
            return ''
        k = keys[min(max(int(lev), 0), len(keys) - 1)]
        return str(_h(wt[k]).get('type_name') or '')
    except Exception:
        return ''


def tree_max_lev():
    try:
        return len(tree_cfg().get('TreeLev') or {}) - 1
    except Exception:
        return 0


def db_tree_state(rid):
    """玩家摇钱树等级（`role_tree`）；没有行 ⇒ 0（真话）。"""
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_tree ('
                    'rid INTEGER PRIMARY KEY, lev INTEGER, updated_at INTEGER)')
        con.commit()
        r = con.execute('SELECT lev FROM role_tree WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        return int(r[0] or 0) if r else 0
    except Exception as e:
        log('tcp.log', '  !! db_tree_state failed: %r' % (e,))
        return 0


def db_tree_set(rid, lev):
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_tree ('
                    'rid INTEGER PRIMARY KEY, lev INTEGER, updated_at INTEGER)')
        con.execute('INSERT OR REPLACE INTO role_tree VALUES (?,?,?)',
                    (int(rid), int(lev), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_tree_set failed: %r' % (e,))
        return False


_TREE_CFG = None


_DEDICATED_CMDS = None


def _dedicated_cmds():
    """★ R150：**本文件里所有"专用实现"的命令号**（启动时从源码提取一次）。

    用途：`global_default_sc` 的兜底**不得抢走专用实现**
    （默认响应的分支在函数前面，专用分支在后面 —— 顺序执行会抢先命中）。

    提取规则与门禁 `lint_dispatch_shadow` **同一套**：
      `if cmd == N:` 与 `if cmd in (N1, N2, …)`。
    ⇒ 它**永远与代码同步**，不需要手工维护清单。
    """
    global _DEDICATED_CMDS
    if _DEDICATED_CMDS is None:
        out = set()
        try:
            import re as _re          # ★ R150b：本文件顶部**没有** `import re`
            with open(__file__, encoding='utf-8') as f:
                t = f.read()
            t = _re.sub(r'#[^\n]*', '', t)
            out |= set(int(x) for x in _re.findall(r'if cmd == (\d{4,6}):', t))
            for mm in _re.finditer(r'if cmd in \(([^)]*)\):', t):
                for x in _re.findall(r'\d{4,6}', mm.group(1)):
                    out.add(int(x))
            log('server.log', 'dedicated cmds extracted: %d' % len(out))
        except Exception as e:
            log('server.log', '!! _dedicated_cmds failed: %r' % (e,))
        _DEDICATED_CMDS = out
    return _DEDICATED_CMDS


_R171 = {12904: (['ord', 'rid', 's', 'name', 'sex', 'car16', 'val32'], []), 12913: (['ord', 'rid', 's', 'name', 'sex', 'car16', 'val16', 'time16'], []), 12914: (['ord', 'rid', 's', 'name', 'sex', 'hero', 'val16'], ['my_ride_jie']), 12915: (['ord', 'rid', 's', 'name', 'sex', 'hero', 'val16'], ['my_lingshou_jie']), 12916: (['ord', 'rid', 's', 'name', 'sex', 'hero', 'val16'], ['my_wing_color']), 12917: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val16'], []), 12919: (['ord', 'rid', 's', 'name', 'award16', 'val16'], ['my_win_num:u16']), 12920: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val16'], []), 12921: (['ord', 'rid', 's', 'name', 'hero', 'val32'], ['my_shenqi_bid:u32']), 12923: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val16'], []), 12924: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'lev', 'val32'], []), 12925: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12926: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12927: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32', 'hero'], ['my_ride_jie:u8']), 12928: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32', 'jie'], ['my_jie:u8']), 12929: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12930: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12932: (['ord', 'rid', 's', 'name', 'sex', 'allpower', 'fabao'], ['my_fabao_list:table']), 12933: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12934: (['ord', 'rid', 's', 'name', 'sex', 'val32', 'hero', 'grow'], ['my_hero_bid:u32', 'grow32:u32']), 12973: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32', 'partnersub'], ['partner_list:table'])}


# ★★★ R243：**榜单指标表** —— 每个榜的 `val` 该填哪个值。
#
# 取证（唯一权威）：`config_rank.luac` 的 `subCfg`，每个条目是
#     TDUP{cmd,type,title,sId} + KSTR('<榜名>') + TSETS(['label'])
# ⇒ **命令号 → 榜名** 是硬映射（工具：`tools/_diag_r243_rank_names.py`，48 条全表）。
# 老解构器把 `label` 全丢成 null（它只解 `TSETS`/`TSETB` 的结构，漏了 `TSETV` 那一族），
# 所以 R171/R225 一直以为"榜名解不出"。
#
# 本表只收 **"榜名 ⇔ 数据源"语义确凿** 的（同名列 / 同族配置同名键；纪律第 46/66 条）：
#   `12902` 人物战力 ← `role_power`（与 `10304` 同一函数）
#   `12904` 人物等级 ← `roles.level`        （★ 原来是 power，**榜名对不上**）
#   `12911` 勇气排行 ← `role_assets.courage`（与 `13331` 同一数据源）
#   `12912` 魅力排行 ← `role_assets.charm`  （同上）
#   `12914` 坐骑战力 ← `role_ride.zz`       （`config_ride.RideJie[].zz` 同名键）
#   `12915` 魂灵战力 ← `role_lingshou.zz`   （`config_lingshou.LingshouZZ` 同名族）
#   `12916` 翅膀战力 ← `role_wing.power`    （R214 已证 `role_wing.power` = 翅膀战力）
#   `12931` 斗魂排行 ← `arena_state.trophy` （★ 原来是 lev，**榜名对不上**）
# 其余榜（`12913`/`12917`/`12920`/`12921`/`12923`/`12932`/`12934`/`12986` …）的**专属**指标
# 在本服**无源** ⇒ 沿用综合战力（**已在 `round243` 报告里逐条登记**），不编造。
_RANK_METRIC = {
    12902: 'power',
    12904: 'lev',
    12911: 'courage',
    12912: 'charm',
    12914: 'ride_zz',
    12915: 'lingshou_zz',
    12916: 'wing_power',
    12931: 'trophy',
}


def rank_metric_value(cmd, rid, lev, power):
    """★ R243：按 `_RANK_METRIC` 取该榜的**真实指标值**；无登记 ⇒ 回综合战力。"""
    k = _RANK_METRIC.get(cmd)
    try:
        if k == 'lev':
            return int(lev or 0) & 0xffffffff
        if k == 'courage':
            return int(db_get_assets(rid).get('courage', 0) or 0) & 0xffffffff
        if k == 'charm':
            return int(db_get_assets(rid).get('charm', 0) or 0) & 0xffffffff
        if k == 'ride_zz':
            return int(db_ride_state(rid).get('zz', 0) or 0) & 0xffffffff
        if k == 'lingshou_zz':
            return int(db_lingshou_state(rid).get('zz', 0) or 0) & 0xffffffff
        if k == 'wing_power':
            return int(db_wing_state(rid).get('power', 0) or 0) & 0xffffffff
        if k == 'trophy':
            return int(db_arena_trophy(rid) or 0) & 0xffffffff
    except Exception as e:
        log('tcp.log', '  !! rank_metric_value(%d) failed: %r' % (cmd, e))
        return 0
    return int(power or 0) & 0xffffffff


def db_arena_trophy(rid):
    """★ R243：`arena_state.trophy`（斗魂积分）。**没有行 ⇒ 0 —— 真话**（`17301` 同表）。"""
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS arena_state (
            rid INTEGER PRIMARY KEY, trophy INTEGER, times INTEGER,
            index_state INTEGER, win_times INTEGER, state INTEGER, updated_at INTEGER)""")
        con.commit()
        r = con.execute('SELECT trophy FROM arena_state WHERE rid=?',
                        (int(rid),)).fetchone()
        db_release(con)
        return int(r[0] or 0) if r else 0
    except Exception as e:
        log('tcp.log', '  !! db_arena_trophy failed: %r' % (e,))
        return 0


_QPRAY_CFG = None


def qifu_pray_cfg():
    """★ R243：公会祈福配置（`server/cfg/config_guild_pray.json`，R111 批量解构产物）。

    ★ 取证（三处一致，见 `round243` 报告）：
      ① `qifu_ctrl.on13569 → QifuModel:qifuInfo(data)`，模型里 `timesData = data.info`
      ② `qifu_view` 用 `timesData` 渲染 `QifuCell`，`updateTimes(val, val_max)`（文案 `val/val_max`）
      ③ `qifu_cell` 的「护送加成/宗门资金/个人贡献/消耗」**逐项取自 `GuildPrayData[type]`**
         （`reward_husong` / `reward_assets` / `reward_contrib` / `cost`）
    ⇒ `SC_13569.info` 的**条数与 `type` = `GuildPrayData` 的键**（本配置 3 档）。
    """
    global _QPRAY_CFG
    try:
        if _QPRAY_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                             'config_guild_pray.json')
            with open(p, encoding='utf-8') as f:
                _QPRAY_CFG = json.load(f)
            log('server.log', 'guild_pray cfg loaded: %s' % list(_QPRAY_CFG.keys()))
        return _QPRAY_CFG
    except Exception as e:
        log('server.log', '!! guild_pray cfg load failed: %r' % (e,))
        return {}


def qifu_tiers():
    """★ R243：祈福档位 id（`GuildPrayData` 的键，升序）。**空配置 ⇒ 空表**。"""
    d = (qifu_pray_cfg() or {}).get('GuildPrayData') or {}
    out = []
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict) and (v.get('hash') is not None):
                try:
                    out.append(int(float(k)))
                except Exception:
                    continue
    return sorted(out)


def db_qifu_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_qifu (
        rid INTEGER, type INTEGER, val INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, type))""")
    con.commit()
    db_release(con)


def db_qifu_state(rid):
    """★ R243：`{档位: 已祈福次数}`。**没有行 ⇒ 空（= 0 次）—— 真话**。"""
    out = {}
    try:
        db_qifu_init()
        con = db_conn()
        for t, v in con.execute('SELECT type,val FROM role_qifu WHERE rid=?',
                                (int(rid),)).fetchall():
            out[int(t or 0)] = int(v or 0)
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_qifu_state failed: %r' % (e,))
    return out


def db_qifu_set(rid, t, val):
    try:
        db_qifu_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_qifu VALUES (?,?,?,?)',
                    (int(rid), int(t), int(val), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_qifu_set failed: %r' % (e,))
        return False


def encode_rank_elem(fields, rid, name, sex, career, lev, pw):
    """★ R172：编一个 `rank_list` 元素（**按字段 token 逐个拼**）。
    token 与类型（全部核对过 spec）：
      `ord:u8` `ordU16:u16` `rid:u32` `s:string` `name:string` `sex:u8`
      `car8:u8` `car16:u16` `lev:u8` `val16:u16` `val32:u32`
      `head:u32` `friend32:u32` `mingstage:u8` `ringlev:u8` `ringstar:u16`
      其余（子表）⇒ 空表
    """
    o = b''
    for f in fields:
        if f == 'ord':
            o += w_u8(1)
        elif f == 'ordU16':
            o += w_u16(1)
        elif f == 'rid':
            o += w_u32(rid)
        elif f == 'gid':
            o += w_u32(rid)            # ★ R173：宗门榜的 gid
        elif f == 's':
            o += w_str('1')
        elif f == 'gs':
            o += w_str('1')            # ★ R173：宗门榜的 g_srv_id
        elif f == 'name':
            o += w_str(name)
        elif f in ('gname', 'headname'):
            o += w_str(name)           # ★ R173：宗门榜的 g_name / head_name
        elif f == 'gnum16':
            o += w_u16(1)              # ★ R173：宗门人数
        elif f == 'sex':
            o += w_u8(sex)
        elif f == 'car8':
            o += w_u8(career & 0xff)
        elif f == 'car16':
            o += w_u16(career & 0xffff)
        elif f == 'lev':
            o += w_u8(lev & 0xff)
        elif f in ('val16', 'val'):
            o += w_u16(pw & 0xffff)
        elif f == 'val32':
            o += w_u32(pw & 0xffffffff)
        elif f == 'head':
            o += w_u32(0)
        elif f == 'friend32':
            o += w_u32(0)
        elif f == 'mingstage':
            o += w_u8(0)
        elif f == 'ringlev':
            o += w_u8(0)
        elif f == 'ringstar':
            o += w_u16(0)
        else:
            o += w_u16(0)
    return o


def encode_rank_reply(items, rid, name, sex, career, lev, pw, my_ord_u16=False):
    """★ R172：`{my_ord:u8|u16, my_val:u32, [my_*], rank_list:<1 条>}` 的统一回复。

    ★ `12994` 的 **`my_ord` 是 `uint16`**（其余都是 u8）⇒ 用 `my_ord_u16` 区分。
    """
    elems, extras = items
    out = (w_u16(1) if my_ord_u16 else w_u8(1)) + w_u32(pw & 0xffffffff)
    for e in extras:
        nm, _, tp = e.partition(':')
        tp = tp or 'u8'
        if nm in ('my_g_name', 'my_head_name'):
            out += w_str(name)
        elif tp == 'table':
            out += w_u16(0)
        elif tp == 'u32':
            out += w_u32(0)
        elif tp == 'u16':
            out += w_u16(0)
        else:
            out += w_u8(0)
    out += w_u16(1) + encode_rank_elem(elems, rid, name, sex, career, lev, pw)
    return out




_R172 = {12977: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val16'], []), 12978: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val16'], []), 12979: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12986: (['ord', 'rid', 's', 'name', 'lev', 'car8', 'sex', 'head', 'val32', 'mingstage'], ['my_mingge_stage:u8']), 12988: (['ord', 'rid', 's', 'name', 'lev', 'car8', 'sex', 'head', 'val32'], []), 12995: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12996: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12997: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12998: (['ord', 'rid', 's', 'name', 'sex', 'val32', 'ringlev', 'ringstar', 'car8'], ['my_ring_lev:u8', 'my_ring_star:u16']), 12999: (['ord', 'rid', 's', 'name', 'sex', 'car8', 'val32'], []), 12918: (['ord', 'gid', 'gs', 'gname', 'headname', 'gnum16', 'val16'], ['my_g_name', 'my_head_name', 'my_g_num:u16']), 12994: (['ord', 'friend32', 'rid', 's', 'name', 'sex', 'car8', 'lev'], [])}


# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo] _CS_FIELDS_CACHE = None


# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo] def _cs_fields(cmd):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     """★ R188：返回该 CMD 的 **CS** 字段列表（与 `_sc_fields` 同源，`dir == 'cs'`）。"""
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     global _CS_FIELDS_CACHE
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     if _CS_FIELDS_CACHE is None:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         _CS_FIELDS_CACHE = {}
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         try:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             p = os.path.join(os.path.dirname(HERE), 'protocol', 'fields.json')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             with open(p, encoding='utf-8') as f:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 raw = json.load(f)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             for k, v in raw.items():
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 try:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     c = int(v.get('cmd'))
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 except Exception:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 if (v.get('dir') or '') != 'cs':
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 _CS_FIELDS_CACHE.setdefault(c, v.get('fields') or [])
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         except Exception as e:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             log('server.log', '!! _cs_fields load failed: %r' % (e,))
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     return _CS_FIELDS_CACHE.get(int(cmd), [])


# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo] def _sc_w(tp):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     """字段的字节宽度（string 返回 -1 表示变长）。"""
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     t = (tp or '').lower()
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     if t.startswith('string'):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         return -1
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     return {'uint8': 1, 'int8': 1, 'bool': 1, 'uint16': 2, 'int16': 2,
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             'uint32': 4, 'int32': 4, 'float': 4, 'double': 8}.get(t, 1)


# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo] def encode_by_sc_with_echo(cmd, body=b'', code=1):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     """★★ R188：**通用回显编码器** —— 按权威 SC 编，**CS 里同名字段回显真值**。

# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     1. 用 **CS 的字段顺序**算 body 偏移（string = 2 + len）
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     2. 用 **SC 的字段顺序**编码；同名同类型 ⇒ 读 body；否则 ⇒ 0 / ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     3. `code`/`result` 首字段 ⇒ `code`
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     """
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     cs_fs = _cs_fields(cmd)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     sc_fs = _sc_fields(cmd)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     if not sc_fs:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         return b''
    # ① CS 偏移表
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     off, o = {}, 0
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     for f in cs_fs:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         nm = (f.get('name') or '') if isinstance(f, dict) else ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         tp = (f.get('type') or '') if isinstance(f, dict) else ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         off[nm] = (o, tp)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         w = _sc_w(tp)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         if w == -1:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             n = struct.unpack_from('>H', body, o)[0] if len(body) >= o + 2 else 0
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             o += 2 + n
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         else:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             o += w
    # ② 按 SC 编码
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     out = b''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     for f in sc_fs:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         nm = (f.get('name') or '') if isinstance(f, dict) else ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         tp = (f.get('type') or '') if isinstance(f, dict) else ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         its = f.get('items') if isinstance(f, dict) else None
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         if its:                                   # 子表 ⇒ 默认空表
            # ★★★ R203：**空子表的"高置信度真值"挂钩** ——
            #   若该子表的**元素字段名**与某配置的**主表字段名**重合 **≥ 8**
            #   ⇒ 填 **1 条**（值按同名字段取）✓
            #   ★ 只对 ≥8 生效（**极高置信度**）—— 避免纪律第 42 条的"通用词污染"。
            #   ★★ 例：`15501`/`15801` 的 `attr_list`（12 字段）⟷ `config_hero_base`（14 字段）
            #      ⇒ 重合 **12** ⇒ 填 1 条真属性 ✓
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             _en = [x.get('name') for x in its if isinstance(x, dict)]
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             _cfg, _row = kcfg_best_attr_table(_en, 8)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             if _cfg and _row:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 out += w_u16(1)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 for _x in its:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     if not isinstance(_x, dict):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     _xn = _x.get('name') or ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     _xt = (_x.get('type') or '').lower()
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     if _x.get('items'):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         out += w_u16(0)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     elif _xt.startswith('string'):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         _v = _row.get(_xn)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         out += w_str(_v if isinstance(_v, str) else '')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                     else:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         _w2 = _sc_w(_xt)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         _v = _row.get(_xn)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         try:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                             _v = int(_v or 0)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         except Exception:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                             _v = 0
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                         out += (int(_v) & ((1 << (_w2 * 8)) - 1)).to_bytes(_w2 if _w2 > 0 else 1, 'big')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             else:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 out += w_u16(0)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         w = _sc_w(tp)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         if nm in ('code', 'result') and out == b'':
            # ★ R189：**按 SC 声明的宽度发**（有 8 条的 `code` 是 **uint32**，硬编码 u8 会越界）
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             out += int(code).to_bytes(w, 'big')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         if w == -1:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             hit = off.get(nm)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             val = ''
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             if hit and (hit[1] or '').lower().startswith('string'):
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 o2 = hit[0]
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 n2 = struct.unpack_from('>H', body, o2)[0] if len(body) >= o2 + 2 else 0
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]                 val = body[o2 + 2:o2 + 2 + n2].decode('utf-8', 'replace')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             out += w_str(val)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             continue
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         hit = off.get(nm)
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         val = 0
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         if hit and _sc_w(hit[1]) == w and len(body) >= hit[0] + w:
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]             val = int.from_bytes(body[hit[0]:hit[0] + w], 'big')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]         out += val.to_bytes(w, 'big')
# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with_echo]     return out


# [P2B-migrated config/loader.py::kconst/kconst_count] _KCONST_CACHE = {}


# [P2B-migrated config/loader.py::kconst/kconst_count] def kconst(name):
# [P2B-migrated config/loader.py::kconst/kconst_count]     """★ R196：读 **`server/cfg_kconst/<name>.json`**（R195 dump 出的**常量池**）。

# [P2B-migrated config/loader.py::kconst/kconst_count]     ★ 这是一个**与 `server/cfg` 并列的数据源** —— `cfg` 是"线性解构"的结果
# [P2B-migrated config/loader.py::kconst/kconst_count]       （拿不到"嵌套函数"里的数据），`cfg_kconst` 是**常量池**（**285/286 个配置全有数据**）。
# [P2B-migrated config/loader.py::kconst/kconst_count]     ★ 返回 `{'proto0': {'kgc': [...], 'knum': [...], 'kstr': [...]}, ...}`。
# [P2B-migrated config/loader.py::kconst/kconst_count]     """
# [P2B-migrated config/loader.py::kconst/kconst_count]     if name in _KCONST_CACHE:
# [P2B-migrated config/loader.py::kconst/kconst_count]         return _KCONST_CACHE[name]
# [P2B-migrated config/loader.py::kconst/kconst_count]     out = {}
# [P2B-migrated config/loader.py::kconst/kconst_count]     try:
# [P2B-migrated config/loader.py::kconst/kconst_count]         p = os.path.join(HERE, 'cfg_kconst', name + '.json')
# [P2B-migrated config/loader.py::kconst/kconst_count]         with open(p, encoding='utf-8') as f:
# [P2B-migrated config/loader.py::kconst/kconst_count]             out = json.load(f)
# [P2B-migrated config/loader.py::kconst/kconst_count]     except Exception:
# [P2B-migrated config/loader.py::kconst/kconst_count]         out = {}
# [P2B-migrated config/loader.py::kconst/kconst_count]     _KCONST_CACHE[name] = out
# [P2B-migrated config/loader.py::kconst/kconst_count]     return out


# [P2B-migrated config/loader.py::kconst/kconst_count] def kconst_count(name):
# [P2B-migrated config/loader.py::kconst/kconst_count]     """★ R196：该配置的**常量池条数** = **KGC 的项数**。

# [P2B-migrated config/loader.py::kconst/kconst_count]     ★ 第一版取"最大的列表长度" ⇒ 拿到 **4**（某条记录的字段数），**不是 95**（配置条数）❌
# [P2B-migrated config/loader.py::kconst/kconst_count]       ⇒ 改成 **`len(kgc)`**（每个 `TableConst` 就是一条配置）✓
# [P2B-migrated config/loader.py::kconst/kconst_count]     """
# [P2B-migrated config/loader.py::kconst/kconst_count]     j = kconst(name)
# [P2B-migrated config/loader.py::kconst/kconst_count]     best = 0
# [P2B-migrated config/loader.py::kconst/kconst_count]     for v in (j or {}).values():
# [P2B-migrated config/loader.py::kconst/kconst_count]         best = max(best, len(v.get('kgc') or []))
# [P2B-migrated config/loader.py::kconst/kconst_count]     return best


def sym_elem_bytes(fields):
    """★ R196b：按**权威 SC 的字段列表**生成"一条元素"的字节（全 0/空）。

    ★ 用途：`list` 型字段需要"N 条元素"时，**用它重复 N 次** ⇒
      **结构永不出错**（不必手写字段 —— 本会话手写字段已错 6 次）。
    """
    o = b''
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        tp = (f.get('type') or '').lower()
        its = f.get('items') or []
        if its:
            o += w_u16(0)
        elif tp.startswith('string'):
            o += w_str('')
        else:
            w = _sc_w(tp)
            o += (0).to_bytes(w if w > 0 else 1, 'big')
    return o


def sym_list_bytes(cmd, field_name, n):
    """★ R196b：生成 `{field_name: table}` 的字节（**`n` 条元素，按权威 SC**）。"""
    for f in _sc_fields(cmd):
        if isinstance(f, dict) and f.get('name') == field_name:
            return w_u16(n) + sym_elem_bytes(f.get('items') or []) * max(0, int(n))
    return w_u16(0)


# [P2B-migrated config/loader.py::kconst_rows/str/int] def kconst_rows(name):
# [P2B-migrated config/loader.py::kconst_rows/str/int]     """★ R199：把 `cfg_kconst/<name>.json` 的**行**取出来（`[(key, row_dict), ...]`）。

# [P2B-migrated config/loader.py::kconst_rows/str/int]     ★ 两种形态都支持（**这是 R199 修正的关键**）：
# [P2B-migrated config/loader.py::kconst_rows/str/int]       ① **一个 dict 装 N 行**（如 `config_npc` 的 `{31216.0: 30001, …}`）⇒ 拆成 N 行
# [P2B-migrated config/loader.py::kconst_rows/str/int]       ② ★ **N 个 dict 各装一行**（如 `config_function` 的 93 个 `TableConst`）⇒ 每个 dict 一行
# [P2B-migrated config/loader.py::kconst_rows/str/int]     ★ 判据：**若"含字段名的 dict"有多个 ⇒ 走形态 ②**（**R199 第一版只做了 ①**，
# [P2B-migrated config/loader.py::kconst_rows/str/int]       结果把 `config_function` 的"**一个字段表**"当成了 13 行 ⇒ `title` 变成了字面量 `"description"`）。
# [P2B-migrated config/loader.py::kconst_rows/str/int]     """
# [P2B-migrated config/loader.py::kconst_rows/str/int]     j = kconst(name)
# [P2B-migrated config/loader.py::kconst_rows/str/int]     dicts = []
# [P2B-migrated config/loader.py::kconst_rows/str/int]     for v in (j or {}).values():
# [P2B-migrated config/loader.py::kconst_rows/str/int]         for x in (v.get('kgc') or []):
# [P2B-migrated config/loader.py::kconst_rows/str/int]             if isinstance(x, dict) and (x.get('hash') or x.get('array')):
# [P2B-migrated config/loader.py::kconst_rows/str/int]                 dicts.append(x)
    # ★ 形态 ②：多个 dict ⇒ 每个 dict 一行（用它的 `hash`）
# [P2B-migrated config/loader.py::kconst_rows/str/int]     if len(dicts) >= 3:
# [P2B-migrated config/loader.py::kconst_rows/str/int]         out = []
# [P2B-migrated config/loader.py::kconst_rows/str/int]         for i, d in enumerate(dicts):
# [P2B-migrated config/loader.py::kconst_rows/str/int]             h = d.get('hash') or {}
# [P2B-migrated config/loader.py::kconst_rows/str/int]             if not h:
# [P2B-migrated config/loader.py::kconst_rows/str/int]                 continue
            # 若这个 dict 只装"一行"（含字段名），直接用它；否则当"多行"拆开
# [P2B-migrated config/loader.py::kconst_rows/str/int]             has_id = any(k in h for k in ('id', 'bid', 'ID', 'Bid'))
# [P2B-migrated config/loader.py::kconst_rows/str/int]             if has_id or len(h) <= 24:
# [P2B-migrated config/loader.py::kconst_rows/str/int]                 out.append((str(h.get('id', h.get('bid', i + 1))), h))
# [P2B-migrated config/loader.py::kconst_rows/str/int]             else:
# [P2B-migrated config/loader.py::kconst_rows/str/int]                 out.extend(list(h.items()))
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if out:
# [P2B-migrated config/loader.py::kconst_rows/str/int]             return out
    # ★ 形态 ①：一个 dict 装 N 行
# [P2B-migrated config/loader.py::kconst_rows/str/int]     best = None
# [P2B-migrated config/loader.py::kconst_rows/str/int]     for d in dicts:
# [P2B-migrated config/loader.py::kconst_rows/str/int]         h = d.get('hash') or {}
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if best is None or len(h) > len(best):
# [P2B-migrated config/loader.py::kconst_rows/str/int]             best = h
# [P2B-migrated config/loader.py::kconst_rows/str/int]     return list((best or {}).items())


# [P2B-migrated config/loader.py::kconst_rows/str/int] def kconst_str(row, *names):
# [P2B-migrated config/loader.py::kconst_rows/str/int]     """★ R199：从行里按**候选字段名**取一个字符串（找不到 ⇒ ''）。"""
# [P2B-migrated config/loader.py::kconst_rows/str/int]     if not isinstance(row, dict):
# [P2B-migrated config/loader.py::kconst_rows/str/int]         return ''
# [P2B-migrated config/loader.py::kconst_rows/str/int]     for nm in names:
# [P2B-migrated config/loader.py::kconst_rows/str/int]         v = row.get(nm)
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if isinstance(v, str) and v:
# [P2B-migrated config/loader.py::kconst_rows/str/int]             return v
# [P2B-migrated config/loader.py::kconst_rows/str/int]     for nm in names:
# [P2B-migrated config/loader.py::kconst_rows/str/int]         v = row.get(nm)
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if v is not None and not isinstance(v, (dict, list)):
# [P2B-migrated config/loader.py::kconst_rows/str/int]             return str(v)
# [P2B-migrated config/loader.py::kconst_rows/str/int]     return ''


# [P2B-migrated config/loader.py::kconst_rows/str/int] def kconst_int(row, *names):
# [P2B-migrated config/loader.py::kconst_rows/str/int]     """★ R199：从行里按候选字段名取一个整数（找不到 ⇒ 0）。"""
# [P2B-migrated config/loader.py::kconst_rows/str/int]     if not isinstance(row, dict):
# [P2B-migrated config/loader.py::kconst_rows/str/int]         return 0
# [P2B-migrated config/loader.py::kconst_rows/str/int]     for nm in names:
# [P2B-migrated config/loader.py::kconst_rows/str/int]         v = row.get(nm)
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if isinstance(v, (int, float)):
# [P2B-migrated config/loader.py::kconst_rows/str/int]             return int(v)
# [P2B-migrated config/loader.py::kconst_rows/str/int]         if isinstance(v, str) and v.lstrip('-').isdigit():
# [P2B-migrated config/loader.py::kconst_rows/str/int]             return int(v)
# [P2B-migrated config/loader.py::kconst_rows/str/int]     return 0


# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table] _KCFG_FIELDS_CACHE = None


# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table] def _kcfg_fields():
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     """★ R203：预扫 `cfg_kconst` 的"主表字段名"（每个配置一个集合）。"""
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     global _KCFG_FIELDS_CACHE
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     if _KCFG_FIELDS_CACHE is not None:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         return _KCFG_FIELDS_CACHE
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     out = {}
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     try:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         d = os.path.join(HERE, 'cfg_kconst')
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         for fn in sorted(os.listdir(d)):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             if not fn.endswith('.json'):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 continue
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             try:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 with open(os.path.join(d, fn), encoding='utf-8') as f:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                     j = json.load(f)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             except Exception:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 continue
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             best = set()
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             for v in (j or {}).values():
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 for x in (v.get('kgc') or []):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                     if isinstance(x, dict):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                         h = x.get('hash') or {}
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                         if len(h) > len(best):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                             best = set(k for k in h.keys() if isinstance(k, str))
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             if best:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 out[fn[:-5]] = best
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     except Exception:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         out = {}
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     _KCFG_FIELDS_CACHE = out
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     return out


# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table] def _kcfg_row(name):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     """★ R203：取配置的"主表行"（hash 项最多的那个 dict）—— 用于按字段名取真值。"""
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     j = kconst(name)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     best = {}
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     for v in (j or {}).values():
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         for x in (v.get('kgc') or []):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             if isinstance(x, dict):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 h = x.get('hash') or {}
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 if len(h) > len(best):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                     best = h
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     return best


# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table] def kcfg_best_attr_table(elem_names, min_overlap=8):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     """★ R203：为一组**元素字段名**找"字段重合 ≥ `min_overlap`"的配置。

# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     ★ 返回 `(配置名, 行 dict)` 或 `(None, None)`。
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     ★★ `min_overlap=8` 是**极高置信度**阈值（避免通用词污染 —— 纪律第 42 条）。
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     """
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     probe = set(x for x in (elem_names or []) if isinstance(x, str))
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     if len(probe) < min_overlap:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         return (None, None)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     best = (None, None, 0)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     for cfg, keys in _kcfg_fields().items():
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         ov = len(probe & keys)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         if ov > best[2]:
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             best = (cfg, keys, ov)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     if best[2] >= min_overlap:
        # ★★ R203b：**必须 `_row` 非空才返回** ——
        #   第一版只检查了"字段重合"（`_cfg` 非空），没检查"行非空"
        #   ⇒ `attr_list` 填了 **1 条全 0** ❌
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         _r = _kcfg_row(best[0])
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]         if _r:
            # ★ 再确认"行里真的含探针字段"（避免选到"字段名对但行是模板"的配置）
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]             if len(probe & set(_r.keys())) >= min_overlap:
                # ★★★ R203c：**再确认"探针字段的值不全为 0"** ——
                #   `config_attr`/`config_hero_base` 的主表是"**字段名清单**"（值全 0）
                #   ⇒ 若照搬会填"1 条全 0"（**比空表更糟：客户端会显示一排 0 属性**）
                #   ★ 判据（**纪律第 41 条**）：**"字段名对应" ≠ "数值可得"**。
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 _vals = [_r.get(k) for k in probe]
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 _nonzero = sum(1 for v in _vals if isinstance(v, (int, float)) and v)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                 if _nonzero * 2 >= len(probe):
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]                     return (best[0], _r)
# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table]     return (None, None)


# [P3deep-migrated] db_role_attr 已在 attribute/service.py（mock_server L67 已 from-import），本地副本注释：
# def db_role_attr(rid):
#     """★ R204：读 `role_attr` 表的**首行**为 dict（玩家属性面板的真值来源）。
#
#     ★ `role_attr` 的列名与 `SC_10947.attr` / `SC_15204` 等的字段名**逐名对应**。
#     ★ `None` ⇒ 保持 `None`（调用方给 0）—— DB 里的 `None` 是"未设置"，**忠实呈现**。
#     """
#     try:
#         con = db_conn()
#         cur = con.execute('SELECT * FROM role_attr WHERE rid=? LIMIT 1', (int(rid),))
#         row = cur.fetchone()
#         if not row:
#             return {}
#         cols = [d[0] for d in (cur.description or [])]
#         return dict(zip(cols, row))
#     except Exception:
#         return {}


# ★ R213：`SC_10601.hero_list` / 类似子表的**字段名 → `role_attr` 列名**别名表
# [P3deep-migrated] _ATTR_ALIAS 已下沉 attribute/service.py：
# _ATTR_ALIAS = {
#     'speed': 'atk_speed',
#     'def_red_s': 'red_def_s',
#     'def_red_p': 'red_def_p',
#     'hit_rate': 'hit_rate_show',
#     'crit_rate': 'crit_rate_show',
#     'tenacity_rate': 'tenacity_rate_show',
#     'dodge_rate': 'dodge_rate_show',
# }


# [P3deep-migrated] attr_row_bytes 已下沉 attribute/service.py（L67 import），本地副本注释：
# def attr_row_bytes(cmd, field_name, row, rid=1001):
#     """★ R204：按 `SC` 的 `field_name` 子表字段顺序，用 `row` 的**同名字段**生成 **1 条**。
#
#     ★ 找不到同名字段 ⇒ 0；`row` 为空 ⇒ 返回空表 `w_u16(0)`（**不编造**）。
#     """
#     for f in _sc_fields(cmd):
#         if not (isinstance(f, dict) and f.get('name') == field_name):
#             continue
#         its = f.get('items') or []
#         if not its:
#             return w_u16(0)
#         if not row:
#             return w_u16(0)
#         o = w_u16(1)
#         for x in its:
#             if not isinstance(x, dict):
#                 continue
#             nm = x.get('name') or ''
#             tp = (x.get('type') or '').lower()
#             if x.get('items'):
#                 o += w_u16(0)
#                 continue
#             v = row.get(nm)
#             if v is None:
#                 _al = _ATTR_ALIAS.get(nm)
#                 if _al:
#                     v = row.get(_al)
#             if tp.startswith('string'):
#                 o += w_str(v if isinstance(v, str) else '')
#                 continue
#             w = _sc_w(tp)
#             try:
#                 v = int(v or 0)
#             except Exception:
#                 v = 0
#             o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
#         return o
#     return w_u16(0)


def db_bag_item(rid, uniq_id):
    """★ R207：按 `uniq_id` 取 `bag_items` 的一行（**`item_id` 就是实例 id**）。"""
    try:
        con = db_conn()
        cur = con.execute('SELECT * FROM bag_items WHERE rid=? AND item_id=? LIMIT 1',
                          (int(rid), int(uniq_id)))
        row = cur.fetchone()
        if not row:
            return {}
        cols = [d[0] for d in (cur.description or [])]
        return dict(zip(cols, row))
    except Exception:
        return {}


def bag_items_bytes(cmd, field_name, rows, rid=1001):
    """★ R207：按 `SC.<field_name>` 的元素字段顺序，用 `rows`（list of dict）生成子表。

    ★ `rows` 为空 ⇒ **空表**（不编造）；子表的"子子表"字段 ⇒ 空表。
    """
    for f in _sc_fields(cmd):
        if not (isinstance(f, dict) and f.get('name') == field_name):
            continue
        its = f.get('items') or []
        if not its or not rows:
            return w_u16(0)
        o = w_u16(len(rows))
        for r in rows:
            for x in its:
                if not isinstance(x, dict):
                    continue
                nm = x.get('name') or ''
                tp = (x.get('type') or '').lower()
                if x.get('items'):
                    o += w_u16(0)
                    continue
                v = r.get(nm)
                if nm == 'id':
                    v = r.get('item_id', v)
                if tp.startswith('string'):
                    o += w_str(v if isinstance(v, str) else '')
                    continue
                w = _sc_w(tp)
                try:
                    v = int(v or 0)
                except Exception:
                    v = 0
                o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
        return o
    return w_u16(0)


def db_bag_items_by_bid(rid, bid, limit=64):
    """★ R209：取 `bag_items` 里 **所有 `bid == bid` 的行**（摆摊/市场按配置 id 查）。"""
    try:
        con = db_conn()
        cur = con.execute('SELECT * FROM bag_items WHERE rid=? AND bid=? LIMIT ?',
                          (int(rid), int(bid), int(limit)))
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def db_fabao_rows(rid):
    """★ R218：`role_fabao` 的全部行（法宝列表的真值来源）。"""
    try:
        con = db_conn()
        cur = con.execute('SELECT * FROM role_fabao WHERE rid=? ORDER BY id', (int(rid),))
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]
        return [dict(zip(cols, r)) for r in rows]
    except Exception:
        return []


def fabao_list_bytes(cmd, rows):
    """★ R218：按 `SC_<cmd>.fabao_list` 的元素字段顺序生成子表（找不到的字段 ⇒ 0 / 空表）。"""
    for f in _sc_fields(cmd):
        if not (isinstance(f, dict) and f.get('name') == 'fabao_list'):
            continue
        its = f.get('items') or []
        if not its or not rows:
            return w_u16(0)
        o = w_u16(len(rows))
        for r in rows:
            for x in its:
                if not isinstance(x, dict):
                    continue
                nm = x.get('name') or ''
                tp = (x.get('type') or '').lower()
                if x.get('items'):
                    o += w_u16(0)
                    continue
                v = r.get(nm)
                if tp.startswith('string'):
                    o += w_str(v if isinstance(v, str) else '')
                    continue
                w = _sc_w(tp)
                try:
                    v = int(v or 0)
                except Exception:
                    v = 0
                o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
        return o
    return w_u16(0)


# ★ R219c：`SC.roles` 等"角色行"的**字段名 → roles 表列名**别名表
_ROLE_ALIAS = {'lev': 'lev', 'vip_lev': 'vip_level', 'level': 'lev'}


def role_row_bytes(cmd, field, role, n=1):
    """★ R219c：按**权威 SC** 的 `field` 子表元素字段**逐个生成** `n` 条（**不可能漏字段**）。

    · 标量 ⇒ 从 `role`（`role_state` 的 dict）按**同名字段**或 `_ROLE_ALIAS` 取；取不到 ⇒ 0
    · `srv_id` ⇒ `'1'`（单服）；`spouse_name`/`name` ⇒ 有同名字段则取
    · 子表字段 ⇒ **空表**（不编造）
    """
    for f in _sc_fields(cmd):
        if not (isinstance(f, dict) and f.get('name') == field):
            continue
        its = f.get('items') or []
        if not its:
            return w_u16(0)
        o = w_u16(int(n))
        for _ in range(int(n)):
            for x in its:
                if not isinstance(x, dict):
                    continue
                nm = x.get('name') or ''
                tp = (x.get('type') or '').lower()
                # ★★★ R219d：**`type=='table'` 就是子表** ——
                #   不能用 `x.get('items')`：`misc_uint8`/`misc_str` 的 **`items` 是空数组 `[]`**
                #   （falsy）⇒ 会误走"标量分支" ⇒ 门禁报 `roles[].misc_str: table 计数越界` ❌
                if tp == 'table' or x.get('items'):
                    o += w_u16(0)
                    continue
                if tp.startswith('string'):
                    if nm == 'srv_id':
                        o += w_str('1')
                    else:
                        v = role.get(nm)
                        o += w_str(v if isinstance(v, str) else '')
                    continue
                key = _ROLE_ALIAS.get(nm, nm)
                v = role.get(key)
                if v is None:
                    v = role.get(nm)
                w = _sc_w(tp)
                try:
                    v = int(v or 0)
                except Exception:
                    v = 0
                o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
        return o
    return w_u16(0)


# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count] _KCFG_CACHE = {}


# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count] def kcfg(name):
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     """★ R222：读 **`server/cfg_kconfig/<name>.json`**（R221 的"常量池 → 配置表"产物）。

# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     ★ 形态：`{'rows': {id: row}, 'lists': {序号: [...]}}`。
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     ★ 与 `kconst()`（**原始常量池**）的区别：**这份是"配置表形态"** ⇒ **可直接按字段取值** ✓
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     """
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     if name in _KCFG_CACHE:
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]         return _KCFG_CACHE[name]
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     out = {}
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     try:
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]         p = os.path.join(HERE, 'cfg_kconfig', name + '.json')
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]         with open(p, encoding='utf-8') as f:
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]             out = json.load(f)
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     except Exception:
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]         out = {}
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     _KCFG_CACHE[name] = out
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     return out


# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count] def kcfg_rows(name):
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     """★ R222：`[(id, row), …]`（与 `kconst_rows` 同形，**便于复用**）。"""
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     j = kcfg(name)
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     return list((j.get('rows') or {}).items())


# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count] def kcfg_count(name):
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     """★ R222：行数。"""
# [P2B-migrated config/loader.py::kcfg/kcfg_rows/kcfg_count]     return len(kcfg(name).get('rows') or {})


def _find_sc_field(fields, name):
    """★ R231e：**递归找** SC 里名为 `name` 的字段（**支持嵌套** —— `18713` 的
    `partner_list` 在 `role_list` 的元素里）。"""
    for f in (fields or []):
        if not isinstance(f, dict):
            continue
        if f.get('name') == name:
            return f
        r = _find_sc_field(f.get('items') or [], name)
        if r is not None:
            return r
    return None


def hero_partner_bytes(cmd, field, rows):
    """★ R228/R231e：按 `SC.<cmd>.<field>`（**递归查，支持嵌套**）的元素字段顺序生成子表。"""
    _f = _find_sc_field(_sc_fields(cmd), field)
    if _f is not None:
        f = _f
        its = f.get('items') or []
        if not its or not rows:
            return w_u16(0)
        o = w_u16(len(rows))
        for i, r in enumerate(rows):
            for x in its:
                if not isinstance(x, dict):
                    continue
                nm = x.get('name') or ''
                tp = (x.get('type') or '').lower()
                if tp == 'table' or x.get('items'):
                    o += w_u16(0)
                    continue
                if tp.startswith('string'):
                    o += w_str('')
                    continue
                w = _sc_w(tp)
                v = r.get(nm)
                if v is None and nm == 'id':
                    v = r.get('bid')
                try:
                    v = int(v or 0)
                except Exception:
                    v = 0
                o += (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')
        return o
    return w_u16(0)


# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows] _KCFG2_CACHE = {}


# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows] def kcfg2(name):
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     """★ R237b：读 **`server/cfg_kconfig2/<name>.json`**（R237 的"**散片合并**"版）。

# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     ★ 与 `kcfg()`（R221 的"每个 dict 当一行"版）的区别：
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]       `kcfg2` **按 `bid`/`id` 把散片合并成完整行** ⇒
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]       例如 `config_demon`：`kcfg` 是 **60 个残缺行**，`kcfg2` 是 **9 个完整恶魔** ✓
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     """
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     if name in _KCFG2_CACHE:
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]         return _KCFG2_CACHE[name]
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     out = {}
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     try:
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]         p = os.path.join(HERE, 'cfg_kconfig2', name + '.json')
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]         with open(p, encoding='utf-8') as f:
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]             out = json.load(f)
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     except Exception:
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]         out = {}
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     _KCFG2_CACHE[name] = out
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     return out


# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows] def kcfg2_rows(name):
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     """★ R237b：`[(id, row), …]`（**跳过 `_global`**）。"""
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     j = kcfg2(name)
# [P2B-migrated config/loader.py::kcfg2/kcfg2_rows]     return [(k, v) for k, v in (j.get('rows') or {}).items() if k != '_global']


def role_scalar_bytes(cmd, role, n=1, extra=None):
    """★ R238：**按权威 SC 生成"角色列表"**（**顶层标量 + 子表**都用同一套取值）。

    · 标量/字符串 ⇒ 从 `role`（`role_state`）按**同名**或 `_ROLE_ALIAS` 取；取不到 ⇒ 0/''
    · **子表** ⇒ 按 `role` 生成 `n` 条（**递归**）；`extra` 可覆盖某些字段
    """
    extra = extra or {}
    out = b''
    for f in _sc_fields(cmd):
        if not isinstance(f, dict):
            continue
        nm = f.get('name') or ''
        tp = (f.get('type') or '').lower()
        if tp == 'table' or f.get('items') is not None:
            # ★ 子表：若名字里有 'list'/'roles'/'member' ⇒ 填 n 条角色；否则空表
            if any(w in nm.lower() for w in ('list', 'roles', 'member', 'recommend')):
                its = f.get('items') or []
                out += w_u16(n)
                for _ in range(n):
                    out += _emit_fields(its, role, extra)
            else:
                out += w_u16(0)
            continue
        out += _emit_scalar(nm, tp, role, extra)
    return out


def _emit_scalar(nm, tp, role, extra):
    if tp.startswith('string'):
        if nm == 'srv_id':
            return w_str('1')
        if nm in ('name', 'role_name'):
            return w_str(str(role.get('name') or ''))
        return w_str(str(extra.get(nm, '')))
    w = _sc_w(tp)
    if nm in extra:
        v = extra[nm]
    else:
        key = _ROLE_ALIAS.get(nm, nm)
        v = role.get(key)
        if v is None:
            v = role.get(nm)
    try:
        v = int(v or 0)
    except Exception:
        v = 0
    return (v & ((1 << (w * 8)) - 1)).to_bytes(w if w > 0 else 1, 'big')


def _emit_fields(its, role, extra):
    out = b''
    for x in its:
        if not isinstance(x, dict):
            continue
        nm = x.get('name') or ''
        tp = (x.get('type') or '').lower()
        if tp == 'table' or x.get('items') is not None:
            out += w_u16(0)
            continue
        out += _emit_scalar(nm, tp, role, extra)
    return out


def db_row_of(table, rid):
    """★ R242：取 table 里 rid 的那一行（dict）；无 ⇒ {}。"""
    try:
        con = db_conn()
        cur = con.execute('SELECT * FROM %s WHERE rid=? LIMIT 1' % table, (int(rid),))
        r = cur.fetchone()
        cols = [d[0] for d in (cur.description or [])]
        return dict(zip(cols, r)) if r else {}
    except Exception:
        return {}


def _sc_defined(cmd):
    """★ R136：该命令**有没有 SC 定义**（有 ⇒ 客户端在等应答）。

    ★ 2026-10-17 修：原来直接读本文件的 `_SC_FIELDS_CACHE` —— 那个名字在 `_sc_fields`
      搬去 protocol/fields.py 时被一起注释掉了，这里会 NameError 并被下面的 except 吞掉
      ⇒ **恒返回 False**（"有没有 SC 定义"永远判错）。改为调用模块的公共判定。
    """
    try:
        return _fields_has_sc(cmd)
    except Exception:
        return False


def _build_default_sc(cmd, code=1, msg=None):
    """按 SC 字段规格生成**安全默认响应**（不编造数值）。

    code : 首字段名为 `code`/`result` 时写入的值（默认 1 = 成功）。
           ★ round41：对**本服未实现的操作型命令**传 code=0（失败）——
           回"成功"会让客户端以为操作生效，回"失败"才是真话，
           且比「完全不回应」好（客户端能给出明确提示而不是干等）。
    msg  : 首个名为 `msg` 的 string 字段写入的文案（默认空串）。
    """
    fs = _sc_fields(cmd)
    out = b''
    msg_done = False
    for i, f in enumerate(fs):
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        ty = (f.get('type') or '') if isinstance(f, dict) else ''
        if i == 0 and nm in ('code', 'result'):
            out += w_u8(int(code) & 0xff)
            continue
        t = ty.lower()
        if t.startswith('string'):
            if msg is not None and nm == 'msg' and not msg_done:
                out += w_str(msg)
                msg_done = True
            else:
                out += w_str('')
        elif t.startswith('table'):
            out += w_u16(0)                      # 空表
        elif '64' in t:
            out += w_u32(0) if 'u' in t or 'int' in t else w_u32(0)
        elif '32' in t:
            out += w_u32(0)
        elif '16' in t:
            out += w_u16(0)
        elif '8' in t or 'bool' in t or 'char' in t:
            out += w_u8(0)
        else:
            out += w_u8(0)                       # 兜底：1 字节
    return out


_PARTNER_BASE_CFG = None


def partner_base_cfg():
    """惰性加载完整伙伴基础表（tools/extract_config_table.py 从
    config_partner_base.luac 提取，53 个伙伴，含 color/innate_skill/score）。"""
    global _PARTNER_BASE_CFG
    if _PARTNER_BASE_CFG is None:
        try:
            p = os.path.join(os.path.dirname(HERE), 'server', '_partner_base.json')
            with open(p, encoding='utf-8') as f:
                _PARTNER_BASE_CFG = json.load(f)
            log('server.log', 'partner base loaded: %d 个 <- %s'
                % (len(_PARTNER_BASE_CFG), p))
        except Exception as e:
            _PARTNER_BASE_CFG = []
            log('server.log', '!! partner base load failed: %r' % (e,))
    return _PARTNER_BASE_CFG


# ★ 2026-09-19：功能/活动开放表（tools/extract_config_table.py 从
#   config_function.luac 提取，91 条，含 id/is_open/open_lev/module_flag/sort_id）。
#   客户端 activity_ctrl.luac proto#30 用 `Function.Config[entry.id]` 索引本表：
#     is_open ~= 1 → 直接 return；lev < open_lev → pushUnopenList。
#   ⇒ 服务端只发「is_open=1 且 open_lev <= 玩家等级」的活动（act_list 全有效）。
_FUNCTION_CFG = None


def function_cfg():
    global _FUNCTION_CFG
    if _FUNCTION_CFG is None:
        try:
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', '_tmp_cfg', 'config_function.json')
            with open(p, encoding='utf-8') as f:
                _FUNCTION_CFG = json.load(f)
            log('server.log', 'function config loaded: %d 条 <- %s'
                % (len(_FUNCTION_CFG), p))
        except Exception as e:
            _FUNCTION_CFG = []
            log('server.log', '!! function config load failed: %r' % (e,))
    return _FUNCTION_CFG


def mall_cfg():
    """惰性加载原版商城商品表（tools/extract_mall.py 从
    config_mall.luac 提取，134 件）。"""
    global _MALL_CFG
    if _MALL_CFG is None:
        try:
            with open(MALL_CFG_PATH, encoding='utf-8') as f:
                _MALL_CFG = json.load(f)
            log('server.log', 'mall config loaded: %d 件 <- %s'
                % (len(_MALL_CFG), MALL_CFG_PATH))
        except Exception as e:
            _MALL_CFG = []
            log('server.log', '!! mall config load failed: %r' % (e,))
    return _MALL_CFG


# ---------------------------------------------------------------------------
# ★★ Phase F：「珍宝」页签（限时商店）—— CMD 12836 / 12837
#
#   为什么原来一直是空的（已定位，证据见 analysis/1.4.9/shop/mall_protocol_matrix.md）：
#
#     客户端 `shop_model.luac`：
#       proto#61 requestZhenbaoData()  ->  self.ctrl:request12836()
#       proto#62 setZhenbaoGoodsList(resp)  <-  读 resp.goods_list
#       proto#63 getZhenbaoGoodsList()      ->  zhenbaoList
#       `shop_normal_view.luac` proto#24 用 getZhenbaoGoodsList() 填 ZHENBAO 页签
#     ⇒ **珍宝页签的数据只来自服务端的 SC_12836**，本地配置只给 id 列表。
#     而本服务端**完全没有实现 12836/12837** ⇒ 页签必然为空。
#
#   货物来源（★ 严格区分原版 / 合成）：
#     原版：`Config.MallXian` 的 **45 个 id（21001..21045）** 与其 cli_tag
#           （`config_mall.luac`，`tools/build_shop_goods.py` 提取）
#     合成：item_bid / price / pay_type / limit_num —— `MallXian` 里**没有**这些字段，
#           原版卖什么、多少钱属原版服务端数据，APK 内无取证途径。
#           故用 `IMPLEMENTATION_FALLBACK` 从**真实物品表**挑可用的消耗品，
#           保证"买得到、用得上"。**不得表述为原版数值。**
# ---------------------------------------------------------------------------
MALL_ZHENBAO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'mall_zhenbao.json')
_MALL_ZHENBAO = None


def mall_zhenbao():
    """珍宝（限时商店）货物表。见上方"原版 / 合成"标注。"""
    global _MALL_ZHENBAO
    if _MALL_ZHENBAO is None:
        try:
            with open(MALL_ZHENBAO_PATH, encoding='utf-8') as f:
                _MALL_ZHENBAO = json.load(f)
            log('server.log', 'mall zhenbao loaded: %d 件 <- %s（id 为原版，'
                              'item_bid/price 为 IMPLEMENTATION_FALLBACK）'
                % (len(_MALL_ZHENBAO), MALL_ZHENBAO_PATH))
        except Exception as e:
            _MALL_ZHENBAO = []
            log('server.log', '!! mall zhenbao load failed: %r' % (e,))
    return _MALL_ZHENBAO


def build_goods_list_sc12836(goods, bought_map):
    """SC_12836 / SC_12838 / SC_12842 的 `goods_list` 编码。

    权威字段（`python tools/proto_spec.py cmds 12836`）：
        id:H, item_bid:I, bind:C, pay_type:C, old_price:I, price:I,
        limit_num:C, buy_num:C
    ⚠ 注意与 12801 的 `xs_list` **不是同一结构**：
      12801 是 (... type:C, ico:C, left_time:I, can_buy_num:H)，
      12836 是 (... limit_num:C, buy_num:C)，**没有 type/ico/left_time**。
    """
    out = w_u16(len(goods))
    for g in goods:
        gid = int(g.get('id', 0))
        out += (w_u16(gid) +
                w_u32(int(g.get('item_bid', 0))) +
                w_u8(int(g.get('bind', 0))) +
                w_u8(int(g.get('pay_type', 0))) +
                w_u32(int(g.get('old_price', 0))) +
                w_u32(int(g.get('price', 0))) +
                w_u8(int(g.get('limit_num', 0))) +
                w_u8(min(255, int((bought_map or {}).get(gid, 0)))))
    return out


def shop_pay_asset(cfg, g):
    """由商品的 `pay_type` 推出**实际扣的资产名**。

    依据：客户端 `common_function.payTypeEnToCode(pay_type)` =
          `Config.AssetsEnToCode[pay_type] or 1`，而 `AssetsEnToCode` 就是
          本文件的 `ASSETS_EN_TO_CODE`（逐项核对过）。
    ⇒ 优先级：配置显式指定 > 客户端同源表 > `shop_pay_asset` 兜底。
    """
    pt = int(g.get('pay_type', 0))
    pm = cfg.get('shop_pay_type_asset') or {}
    pay = pm.get(str(pt))
    if pay is None:
        pay = CODE_TO_ASSET.get(pt)
    if pay is None:
        pay = cfg.get('shop_pay_asset', 'coin')
    return str(pay)


def shop_find_goods(src, gid):
    """按商品**条目 id** 查（回退 item_bid）—— CS_12805/12837 的 `id` 是条目 id。"""
    for cand in src:
        if int(cand.get('id', -1)) == int(gid):
            return cand
    for cand in src:
        if int(cand.get('item_bid', -1)) == int(gid):
            return cand
    return None


def shop_try_buy(cfg, src, gid, num):
    """执行一次**真实购买**：选币 → 限购校验 → 扣费 → 发货 → 记限购。

    返回 `(code, msg, g, total, bought_after)`：code=1 成功 / 0 失败。

    ★ round42：`12832`（限购商城购买）与 `13402`（134xx 限购商店购买）共用本函数。
      抽取动机：本服务端原先只有 `12805` 一处买到；`12832` 是"只回成功、不扣费
      不发货"的桩 —— 客户端显示购买成功而实际什么都没发生，比沉默更糟。
      把流程收敛到这里，避免三处各自漂移。
      （`12805` 早于本函数实现，逻辑等价、暂未重构以降低回归风险。）

    支付币种依据 `shop_pay_asset()`：与客户端 `Config.AssetsEnToCode` 同源。
    """
    g = shop_find_goods(src or [], gid)
    if g is None:
        return 0, '商品不存在', None, 0, 0
    rid = role_state(cfg).get('rid', 1001)
    st = role_state(cfg)
    g_gid = int(g.get('id', gid))
    num = max(1, int(num))
    pay = shop_pay_asset(cfg, g)
    unit = int(g.get('price', 0) or 0)
    total = unit * num
    bought0 = int((db_mall_bought(rid) or {}).get(g_gid, 0))
    lim = int(g.get('limit_week', 0) or 0)
    if lim > 0 and bought0 + num > lim:
        return 0, '超过限购（限购 %d，已购 %d）' % (lim, bought0), g, total, bought0
    have = int(st.get(pay, 0) or 0)
    if total > 0 and have < total:
        return 0, '%s 不足（需 %d，有 %d）' % (pay, total, have), g, total, bought0
    if total > 0:
        # `have` 是合并后的有效值 ⇒ 用**绝对值**写入（见 12805 的踩坑记录）
        db_set_assets(rid, {pay: have - total})
    item_bid = int(g.get('item_bid', 0))
    # [P45-C] 发货统一走 RewardService.grant（reference_id=shop:gid:rid:seq，幂等去重；
    #          扣币/限购校验保持原有逻辑）
    _gr = grant(rid, [{'kind': 'item', 'bid': item_bid, 'amount': num}],
                reference_id='shop:%d:%d:%d' % (g_gid, rid, bought0 + num), source='shop')
    if not _gr.get('ok'):
        log('tcp.log', '  !! 购买：扣钱成功但入包失败 item=%d' % item_bid)
    db_mall_bought_add(rid, g_gid, num)
    log('tcp.log', '  ** 购买成功 goods_id=%d item=%d x%d 扣 %s=%d'
        % (g_gid, item_bid, num, pay, total))
    return 1, '', g, total, bought0 + num


# ---------------------------------------------------------------------------
# ★ Phase F：兑换商店（CMD 12840 / 12841）
#
#   权威字段（`python tools/proto_spec.py cmds 12840`）：
#     SC_12840.goods_list: T(id:H, new_item_bid:I, new_item_num:I, new_bind:C,
#                            item_bid:I, item_num:I, limit_num:C, buy_num:C)
#       ⇒ 语义是**交换**：用 `item_bid × item_num` 换 `new_item_bid × new_item_num`
#     SC_12841{code:u8, msg:str, id:u16, num:u16} / CS_12841{id:u16, num:u16}
#
#   数据来源：原版兑换配方**不在 APK 内** ⇒ `server/mall_exchange.json`
#             由 `tools/build_shop_goods.py` 生成，**IMPLEMENTATION_FALLBACK**。
# ---------------------------------------------------------------------------
MALL_EXCHANGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'mall_exchange.json')
_MALL_EXCHANGE = None


def mall_exchange():
    global _MALL_EXCHANGE
    if _MALL_EXCHANGE is None:
        try:
            with open(MALL_EXCHANGE_PATH, encoding='utf-8') as f:
                _MALL_EXCHANGE = json.load(f)
            log('server.log', 'mall exchange loaded: %d 条（IMPLEMENTATION_FALLBACK）'
                % len(_MALL_EXCHANGE))
        except Exception as e:
            _MALL_EXCHANGE = []
            log('server.log', '!! mall exchange load failed: %r' % (e,))
    return _MALL_EXCHANGE


def build_goods_list_sc12840(goods, bought_map):
    """SC_12840 的 `goods_list`（交换配方，字段顺序取自权威 spec）。"""
    out = w_u16(len(goods))
    for g in goods:
        gid = int(g.get('id', 0))
        out += (w_u16(gid) +
                w_u32(int(g.get('new_item_bid', 0))) +
                w_u32(int(g.get('new_item_num', 0))) +
                w_u8(int(g.get('new_bind', 0))) +
                w_u32(int(g.get('item_bid', 0))) +
                w_u32(int(g.get('item_num', 0))) +
                w_u8(int(g.get('limit_num', 0))) +
                w_u8(min(255, int((bought_map or {}).get(gid, 0)))))
    return out


# [P3deep-migrated] mission_def 已下沉 task/service.py：
# def mission_def(bid):
#     """按 bid 取 APK 里的任务定义（没有则返回 {}）。"""
#     return mission_cfg().get(int(bid)) or {}


def decode_award_assets(award_assets):
    """把客户端配置里的 `award_assets` 解码成 {资产字段名: 数量}。

    `award_assets` 形如 `{ {1=2, 2=1290}, {1=4, 2=500}, {1=15, 2=500} }`
    —— 每一项是二元组：`[1]` = 资产 code，`[2]` = 数量。
    兼容三种写法：[[code, num], ...]、[{code=..., num=...}]、[{1=..,2=..}]。
    """
    out = {}
    unknown = []
    if not award_assets:
        return out, unknown
    for row in award_assets:
        code = num = None
        if isinstance(row, (list, tuple)) and len(row) >= 2:
            code, num = row[0], row[1]
        elif isinstance(row, dict):
            if 'code' in row:
                code, num = row.get('code'), row.get('num', row.get('count', 0))
            else:                       # Lua 表 {1=code, 2=num}
                code, num = row.get(1, row.get('1')), row.get(2, row.get('2', 0))
        try:
            code = int(code)
            num = int(num)
        except Exception:
            continue
        name = CODE_TO_ASSET.get(code)
        if name is None:
            unknown.append((code, num))     # 未在表里的 code：**记录但不猜**
            continue
        out[name] = out.get(name, 0) + num
    return out, unknown


# [P2B-migrated persistence/db.py::DB_PATH] DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state', 'roles.db')

_DB_COLS = ['rid', 'uid', 'name', 'level', 'career', 'sex', 'exp',
            'hp', 'max_hp', 'mp', 'max_mp', 'gold', 'gold_acc', 'diamond', 'coin',
            'scene_id', 'x', 'y', 'dir', 'vip_level', 'title', 'status',
            'updated_at']


# ---------------------------------------------------------------------------
# SQLite 连接复用（线程本地）
#   依据：cProfile 显示一次 SC_12400 请求里
#     sqlite3.connect 被调 **6 次**，占该请求耗时的 **37%**。
#   服务端是多线程（ThreadingHTTPServer + ThreadingTCPServer）
#     ⇒ 用 thread-local 连接，**每线程一个**。
#   安全措施：
#     1. `db_conn()` 每次交付都把 `row_factory` 复位 ⇒ 上一个调用者
#        设的 `sqlite3.Row` **不会泄漏**给下一个。
#     2. `db_release()` **不关闭**连接，但会回滚未提交事务 ⇒
#        异常中途退出不会留下脏事务。
# ---------------------------------------------------------------------------
# [P2B-migrated persistence/db.py::db_conn/db_release] _DB_LOCAL = threading.local()


# [P2B-migrated persistence/db.py::db_conn/db_release] def db_conn():
# [P2B-migrated persistence/db.py::db_conn/db_release]     """取本线程的共用 SQLite 连接（不存在则建）。"""
# [P2B-migrated persistence/db.py::db_conn/db_release]     con = getattr(_DB_LOCAL, 'con', None)
# [P2B-migrated persistence/db.py::db_conn/db_release]     if con is None:
# [P2B-migrated persistence/db.py::db_conn/db_release]         con = sqlite3.connect(DB_PATH, timeout=10)
# [P2B-migrated persistence/db.py::db_conn/db_release]         _DB_LOCAL.con = con
# [P2B-migrated persistence/db.py::db_conn/db_release]     con.row_factory = None          # ★ 每次交付复位，防设置泄漏
# [P2B-migrated persistence/db.py::db_conn/db_release]     return con


# [P2B-migrated persistence/db.py::db_conn/db_release] def db_release(con=None):
# [P2B-migrated persistence/db.py::db_conn/db_release]     """“释放”连接：回滚未提交事务，连接留在线程本地复用。"""
# [P2B-migrated persistence/db.py::db_conn/db_release]     c = con if con is not None else getattr(_DB_LOCAL, 'con', None)
# [P2B-migrated persistence/db.py::db_conn/db_release]     if c is None:
# [P2B-migrated persistence/db.py::db_conn/db_release]         return
# [P2B-migrated persistence/db.py::db_conn/db_release]     try:
# [P2B-migrated persistence/db.py::db_conn/db_release]         if c.in_transaction:
# [P2B-migrated persistence/db.py::db_conn/db_release]             c.rollback()
# [P2B-migrated persistence/db.py::db_conn/db_release]     except Exception:
# [P2B-migrated persistence/db.py::db_conn/db_release]         pass


# ★★ R49 多版本分流：默认账号标识（真机 CS_1110.args.account 实测 = dsh_local）
#   老库里的无主角色会挂到它名下，避免玩家角色变孤儿。
# [P2B-migrated core/runtime.py::DEFAULT_UID] DEFAULT_UID = 'dsh_local'

# ★★ R49 多版本分流：当前请求所属的客户端版本族。
#   为什么需要：三个版本的同名消息**字段布局不同**（实测 1.4.9 vs 1.4.11 有 12 处、
#   1.4.9 vs 1.3.0 有 96 处差异；1.3.0 的差异**夹在消息中间还有类型变化**，
#   无法用"下发并集"兼容）⇒ 必须按版本产出不同布局。
#   由于三个版本的 `build_*` 调用点有 8 处，逐处穿参改动面大，这里用
#   **每请求刷新一次的模块级变量**：
#     · 登录（CS_1110）时按 args 表判定版本族，记在**连接**上（`self._ver_family`）；
#     · 分发入口每次请求把连接的版本族刷进 `CUR_VER`；`build_*` 读 `CUR_VER`。
#   ⚠ 已知上限（ponytail: 单机够用）：多客户端**同时**在线时它是"最后一次请求"的值；
#     若将来要并发多版本测试，需改为逐调用穿参或连接级上下文。
# [P2B-migrated core/runtime.py::CUR_VER] CUR_VER = '1.4.9'


# [P2B-migrated core/runtime.py::ver_family_of] def ver_family_of(body_len, args):
# [P2B-migrated core/runtime.py::ver_family_of]     """按 `CS_1110` 的 args 表判客户端版本族（实测体长：1.4.9≈219/220、1.4.11≈187、1.3.0≈21/22）。

# [P2B-migrated core/runtime.py::ver_family_of]     判据用"**args 键数** + **体长**"两级，比单纯看体长稳：
# [P2B-migrated core/runtime.py::ver_family_of]       1.3.0 只报 `account` 一对 → 键数 ≤2；
# [P2B-migrated core/runtime.py::ver_family_of]       1.4.11 键数多但体长 <210；其余按 1.4.9。
# [P2B-migrated core/runtime.py::ver_family_of]     """
# [P2B-migrated core/runtime.py::ver_family_of]     n = len(args or {})
# [P2B-migrated core/runtime.py::ver_family_of]     if n <= 2:
# [P2B-migrated core/runtime.py::ver_family_of]         return '1.3.0'
# [P2B-migrated core/runtime.py::ver_family_of]     if int(body_len) < 210:
# [P2B-migrated core/runtime.py::ver_family_of]         return '1.4.11'
# [P2B-migrated core/runtime.py::ver_family_of]     return '1.4.9'


# [P2B-migrated persistence/db.py::db_init] def db_init():
# [P2B-migrated persistence/db.py::db_init]     os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
# [P2B-migrated persistence/db.py::db_init]     con = db_conn()
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS roles (
# [P2B-migrated persistence/db.py::db_init]         rid INTEGER PRIMARY KEY,
# [P2B-migrated persistence/db.py::db_init]         uid TEXT, name TEXT, level INTEGER, career INTEGER, sex INTEGER,
# [P2B-migrated persistence/db.py::db_init]         exp INTEGER, hp INTEGER, max_hp INTEGER, mp INTEGER, max_mp INTEGER,
# [P2B-migrated persistence/db.py::db_init]         gold INTEGER, gold_acc INTEGER, diamond INTEGER, coin INTEGER,
# [P2B-migrated persistence/db.py::db_init]         scene_id INTEGER, x INTEGER, y INTEGER, dir INTEGER,
# [P2B-migrated persistence/db.py::db_init]         vip_level INTEGER, title TEXT, status INTEGER, updated_at INTEGER)""")
    # ★★ R44：账号表（最小）。
    #   uid 取自 `CS_1110.args` 里的 `account` —— 真机实测该表 10 对键值：
    #     account=dsh_local / timestamp / enter_srv_id / platform=ewan /
    #     device_id / getui_cid / idfa / token=dsh_token / channelId=1 / sign
    #   ⚠ **协议里没有密码字段**（原版走 token + 设备标识）⇒ 按"严格不猜"
    #     不做 password 列、也不自造密码流程（YAGNI）。
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS accounts (
# [P2B-migrated persistence/db.py::db_init]         uid TEXT PRIMARY KEY, name TEXT, create_ts INTEGER)""")
    # 老库补登：把无主角色挂到默认账号，**避免既有玩家角色变孤儿**（幂等）
# [P2B-migrated persistence/db.py::db_init]     con.execute("UPDATE roles SET uid=? WHERE uid IS NULL OR uid=''", (DEFAULT_UID,))
    # Phase 4E 续：属性表（列名就用协议里的字段名，避免二次映射出错）
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS role_attr (
# [P2B-migrated persistence/db.py::db_init]         rid INTEGER PRIMARY KEY,
# [P2B-migrated persistence/db.py::db_init]         strength INTEGER, intellect INTEGER, armor INTEGER, constiution INTEGER,
# [P2B-migrated persistence/db.py::db_init]         atk_s INTEGER, atk_p INTEGER, def_s INTEGER, def_p INTEGER,
# [P2B-migrated persistence/db.py::db_init]         hp_max INTEGER, atk_speed INTEGER, hit INTEGER, dodge INTEGER,
# [P2B-migrated persistence/db.py::db_init]         crit INTEGER, tenacity INTEGER, red_def_s INTEGER, red_def_p INTEGER,
# [P2B-migrated persistence/db.py::db_init]         atk_abs INTEGER, def_abs INTEGER, reduce INTEGER, hurt INTEGER,
# [P2B-migrated persistence/db.py::db_init]         hit_rate_show INTEGER, dodge_rate_show INTEGER,
# [P2B-migrated persistence/db.py::db_init]         crit_rate_show INTEGER, tenacity_rate_show INTEGER,
# [P2B-migrated persistence/db.py::db_init]         updated_at INTEGER)""")
    # Phase 5J：任务状态表（每角色每任务一行）
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS missions (
# [P2B-migrated persistence/db.py::db_init]         rid INTEGER, mission_bid INTEGER,
# [P2B-migrated persistence/db.py::db_init]         mission_status INTEGER, process_status INTEGER,
# [P2B-migrated persistence/db.py::db_init]         target INTEGER, target_value INTEGER, value INTEGER,
# [P2B-migrated persistence/db.py::db_init]         commit_num INTEGER, loop_count INTEGER, loop_num INTEGER,
# [P2B-migrated persistence/db.py::db_init]         code INTEGER, accept_time INTEGER, updated_at INTEGER,
# [P2B-migrated persistence/db.py::db_init]         PRIMARY KEY (rid, mission_bid))""")
    # 通用资产表：任何 AssetsEnToCode 里的资产都能存（"奖励配置驱动"的前提）
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS role_assets (
# [P2B-migrated persistence/db.py::db_init]         rid INTEGER, name TEXT, amount INTEGER,
# [P2B-migrated persistence/db.py::db_init]         PRIMARY KEY (rid, name))""")
    # 商城购买记录：每角色每商品一行（供 SC_12831 的 has_buy_num）
# [P2B-migrated persistence/db.py::db_init]     con.execute("""CREATE TABLE IF NOT EXISTS mall_bought (
# [P2B-migrated persistence/db.py::db_init]         rid INTEGER, goods_id INTEGER, num INTEGER, updated_at INTEGER,
# [P2B-migrated persistence/db.py::db_init]         PRIMARY KEY (rid, goods_id))""")
# [P2B-migrated persistence/db.py::db_init]     con.commit()
# [P2B-migrated persistence/db.py::db_init]     db_release(con)


# [P3deep-migrated] db_get_assets 已在 currency/service.py（L64 已 import），本地副本注释：
# def db_get_assets(rid):
#     """读该角色的全部资产 → {资产名: 数量}。"""
#     try:
#         con = db_conn()
#         rows = con.execute('SELECT name, amount FROM role_assets WHERE rid=?',
#                            (rid,)).fetchall()
#         db_release(con)
#         return {r[0]: r[1] for r in rows}
#     except Exception as e:
#         log('tcp.log', '  !! db_get_assets failed: %r' % (e,))
#         return {}


# [P3deep-migrated] db_add_assets 已在 currency/service.py（L64 已 import），本地副本注释：
# def db_add_assets(rid, delta):
#     """按 {资产名: 增量} 累加（不存在则插入）。"""
#     if not delta:
#         return True
#     try:
#         con = db_conn()
#         for name, amount in delta.items():
#             con.execute('INSERT OR IGNORE INTO role_assets (rid, name, amount) '
#                         'VALUES (?,?,0)', (rid, str(name)))
#             con.execute('UPDATE role_assets SET amount = amount + ? '
#                         'WHERE rid=? AND name=?', (int(amount), rid, str(name)))
#         con.commit()
#         db_release(con)
#         return True
#     except Exception as e:
#         log('tcp.log', '  !! db_add_assets failed: %r' % (e,))
#         return False


# [P3deep-migrated] _MIS_COLS 已下沉 task/service.py：
# _MIS_COLS = ['mission_status', 'process_status', 'target', 'target_value',
#              'value', 'commit_num', 'loop_count', 'loop_num', 'code',
#              'accept_time']


# [P3deep-migrated] db_get_missions 已下沉 task/service.py（逐字一致），此处由 from-import 提供：
# def db_get_missions(rid):
#     """读该角色的全部任务（返回 dict: bid -> 行）。"""
#     try:
#         con = db_conn()
#         con.row_factory = sqlite3.Row
#         rows = con.execute('SELECT * FROM missions WHERE rid=?', (rid,)).fetchall()
#         db_release(con)
#         return {int(r['mission_bid']): dict(r) for r in rows}
#     except Exception as e:
#         log('tcp.log', '  !! db_get_missions failed: %r' % (e,))
#         return {}


# [P3deep-migrated] db_save_mission 已下沉 task/service.py（逐字一致）：
# def db_save_mission(rid, m):
#     """按 bid upsert 一条任务状态。"""
#     try:
#         con = db_conn()
#         con.execute('INSERT OR IGNORE INTO missions (rid, mission_bid) VALUES (?,?)',
#                     (rid, m['mission_bid']))
#         cols = [c for c in _MIS_COLS if c in m]
#         if cols:
#             con.execute('UPDATE missions SET %s, updated_at=? WHERE rid=? AND mission_bid=?' %
#                         ','.join('%s=?' % c for c in cols),
#                         [m[c] for c in cols] + [int(time.time()), rid, m['mission_bid']])
#         con.commit()
#         db_release(con)
#         return True
#     except Exception as e:
#         log('tcp.log', '  !! db_save_mission failed: %r' % (e,))
#         return False


# [P3deep-migrated] mission_chain 已下沉 task/service.py（逐字一致）：
# def mission_chain(cfg, rid=None):
#     """决定"当前该给玩家哪些任务"（**剧情链逐步解锁**）。"""
#     explicit = cfg.get('mission_chain')
#     if explicit:
#         return [int(x) for x in explicit]
#     rid = rid if rid is not None else (cfg.get('role') or {}).get('rid', 1001)
#     row = db_get_role(rid) or {}
#     lev = int(row.get('level') or (cfg.get('role') or {}).get('lev', 1) or 1)
#     mx = int(cfg.get('mission_chain_max', 8))
#     chain = sorted(b for b, v in mission_cfg().items()
#                    if v.get('type') == 1 and int(v.get('lev') or 0) <= lev)
#     if not cfg.get('mission_chain_lock', True):
#         return chain[:mx]
#     done = {b for b, m in db_get_missions(rid).items()
#             if int(m.get('mission_status') or 0) == 3}
#     start = 0
#     for i, b in enumerate(chain):
#         if b not in done:
#             start = i
#             break
#     else:
#         start = max(0, len(chain) - 1)
#     return chain[start:start + mx]


# ---------------------------------------------------------------------------
# ★ Phase F 服务端侧修复：把「任务链当前需要的目标」放进当前场景
#
#   实测依据（analysis/1.4.9/task/task_autopath_probe_result.md）：
#     moveToNpc(10030) 在 Config.MapNpc 里        → 走得过去 ✅
#     moveToNpc(20011) 不在 Config.MapNpc，场景也没有 → 完全没有 gotoTarget ❌
#   ⇒ 服务端只要把缺的目标放进 SC_10201 的 npcs/mons，寻路即可成立。
#
#   ⚠ 坐标是**仿真摆位**（锚点=场景声明的进入点 def_x/def_y + 黄金角错开），
#     原版布置表不在客户端 APK 里，**不得表述为原版坐标**。详见 server/quest_spawn.py
# ---------------------------------------------------------------------------
try:
    from quest_spawn import QuestSpawn
except Exception:                                    # 允许单独运行/缺文件时降级
    QuestSpawn = None

_QUEST_SPAWN = None

# ---------------------------------------------------------------------------
# ★ Phase D：怪物资源表（1.4.9 `Config.Mon`，2645 条）
#
#   数据来源：`analysis/1.4.9/task/config_mon.json`（由
#   `tools/extract_config_mon.py` 从 `assets/src/config/config_mon_data.luac` 提取）
#
#   用途：`SC_10201.mons` / `SC_10212` 需要 `name` 与 `res_id`（外观资源），
#         这两个字段必须来自 APK 原版配置，不能自己编。
#
#   ⚠ `Config.Mon` **不含** HP / 攻击力 / 经验 / 金币 —— 见
#     `analysis/1.4.9/battle/monster_data_model.md`。这些数值属于原版服务端数据，
#     APK 内无取证途径，本阶段按 TEST_ONLY/IMPLEMENTATION_FALLBACK 处理。
# ---------------------------------------------------------------------------
MON_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            '..', 'analysis', '1.4.9', 'task',
                            'config_mon.json')
_MON_CFG = None


def mon_cfg():
    """返回 { '<bid>': {'name':..., 'res_id':...} }（1.4.9 APK 原版数据）。"""
    global _MON_CFG
    if _MON_CFG is None:
        try:
            with open(MON_CFG_PATH, encoding='utf-8') as f:
                _MON_CFG = json.load(f)
            log('server.log', 'mon config loaded: %d 条 <- %s'
                % (len(_MON_CFG), MON_CFG_PATH))
        except Exception as e:
            log('server.log', '!! mon config load failed: %r' % (e,))
            _MON_CFG = {}
    return _MON_CFG


def mon_def(bid):
    return mon_cfg().get(str(int(bid))) or {}


# ★★★ C5-A（2026-10-16）：**怪物类型（`Config.Mon.fields[4]`）—— 至此 CONFIRMED**。
#
# 为什么以前判 UNKNOWN、现在能定死（三重独立取证）：
#   ① **配置自证**：`config_mon.json` 里 `fields[4] == 8` 的 **15 只怪全部叫「狂暴魂兽」**
#      （bid 60154–60243，无一例外）；`fields[4] == 12` 的 21 只全部是
#      「邪魂祭祀 / 邪魂法师 / 圣灵统领 / 圣灵精英 / 圣灵守护兽」⇒ 邪魂师族。
#   ② **任务名自证**：`mission_config.json` 里用 `kill_type_mon` 的任务，
#      码 8 的 6 条**全部名为「狂暴魂兽」**（75001–75006）；
#      码 12 的 3 条名为「灭邪魂师」「暗杀密令」（75030 / 54024 / 54025）。
#   ③ **客户端自证**（`analysis/1.4.9/task/_mission_util_root_full.txt` 反汇编，
#      `kill_type_mon` 分支 @2602–2647）：进度文案是
#         `'邪魂师%s/%s只'` 与 `'击杀%s/%s只狂暴魂兽'`
#      —— 正是 ①里两类怪的名字，且以"类型码 == 2 与否"二选一。
#
# 完整类型表（24 种，逐码名字聚类见 `docs/C5_条件事件与挂机收益.md`）：
#   0=默认/无类型(2287) 1=训练假人 2=神兽 4/5=副本精英 6/9=野外与BOSS
#   7=擂台 8=**狂暴魂兽** 10=内院 11=盗匪 12=**邪魂师族** 13=宝箱/答题
#   14=土拔鼠 15=年兽 17=星罗/日月 18=蒙面人 99/100=世界BOSS
#   101/102/103=霜狼/凶兽族 104=封印守卫 255=神界BOSS
#
# 用途：`kill_type_mon` 条件的 target 就是本函数的返回值（不是 mon_bid）。
def mon_type_of(bid):
    """怪物类型码（`Config.Mon.fields[4]`）。取不到 ⇒ 返回 None（调用侧跳过，不猜）。"""
    try:
        f = (mon_def(bid).get('fields') or [])
        if len(f) > 4 and isinstance(f[4], int):
            return int(f[4])
    except Exception:
        pass
    return None


# [P3deep-migrated] static_mons/quest_spawn/map_cfg/scene_elems/scene_npcs/scene_mons 已下沉 scene/service.py：
#     """配置里写死的场景怪物（**测试摆位**）。
#
#     配置形态（config.json 的 `mons`）：
#         {"id":20001, "bid":20001, "x":34, "y":38}
#     `name` / `res_id` 一律由 `Config.Mon` 补齐（原版数据）；
#     `x`/`y` 是**仿真摆位**（原版摆位表不在 APK 里），随项带 `source='emulated'`。
#     """
#     out = []
#     for i, m in enumerate(cfg.get('mons') or []):
#         bid = int(m.get('bid') or m.get('id') or 0)
#         if not bid:
#             continue
#         d = mon_def(bid)
#         out.append({
#             'id': int(m.get('id') or bid),
#             'bid': bid,
#             'type': int(m.get('type', 0)),
#             'name': m.get('name') or d.get('name') or ('mon%d' % bid),
#             'realm': int(m.get('realm', 0)),
#             'mspd': int(m.get('mspd', 100)),
#             'x': int(m.get('x', 30) if m.get('x') is not None else 30),
#             'y': int(m.get('y', 30) if m.get('y') is not None else 30),
#             'dir': int(m.get('dir', 0)),
#             'res_id': m.get('res_id') or d.get('res_id') or '',
#             'status': int(m.get('status', 0)),
#             'source': m.get('source') or 'emulated',
#             'why': m.get('why') or 'config.mons[%d]' % i,
#         })
#     return out
#
#
# def quest_spawn():
#     """惰性构造 QuestSpawn（只读 APK 提取物）。"""
#     global _QUEST_SPAWN
#     if _QUEST_SPAWN is None:
#         _QUEST_SPAWN = QuestSpawn(mission_cfg()) if QuestSpawn else False
#     return _QUEST_SPAWN or None
#
#
# _MAP_CFG = None
# _MAP_CFG_PATH = os.path.join(HERE, '..', 'analysis', '1.4.9', 'task', 'config_map.json')
#
#
# def map_cfg():
#     """`Config.Map` 全量表（`tools/extract_config_map.py` 的产物，只读快照）。"""
#     global _MAP_CFG
#     if _MAP_CFG is None:
#         try:
#             with open(_MAP_CFG_PATH, encoding='utf-8') as f:
#                 _MAP_CFG = json.load(f)
#         except Exception as e:
#             log('tcp.log', '  !! 读取 config_map.json 失败: %r' % (e,))
#             _MAP_CFG = {}
#     return _MAP_CFG
#
#
# def scene_elems(scene_id):
#     """★ R52：`SCMapGird_10201.elems` —— 场景元素（采集物 / 传送阵 / 机关）。
#
#     **为什么补这条**：R51 的「该发而未发」门禁首次运行就把它抓了出来 ——
#     `build_10201(roles, npcs, mons, elems=None)` 的**两处调用都没传 `elems`**，
#     所以场景元素从来没下发过（不是"没有数据"，是"没接线"）。
#
#     数据来源：APK `config_map.luac` 的 `Config.Map[scene].elems`
#     （`tools/extract_config_map.py` → `analysis/1.4.9/task/config_map.json`）。
#     实测覆盖：124 场景中 **19 个有元素**，每场景 ≤3 个。
#
#     ★ `bid` 取元素 id（与 `npcs` 同构：客户端按 bid 去**本地配置**解析名字/资源）；
#       原表只给了 `x/y`，`type/sub_type/name/res_id` 无出处 ⇒ 留 0/空，**不编造**。
#     """
#     scene = (map_cfg() or {}).get(str(scene_id)) or {}
#     out = []
#     for eid, e in (scene.get('elems') or {}).items():
#         out.append({'id': int(eid), 'bid': int(eid), 'type': 0, 'sub_type': 0,
#                     'name': '', 'x': int(e.get('x') or 0), 'y': int(e.get('y') or 0),
#                     'res_id': ''})
#     return out
#
#
# def scene_npcs(cfg, scene_id):
#     """★ R73：**按场景**取 NPC 表（修"地图 NPC 不匹配"）。
#
#     问题（用户报障）：`scene_quest_extras()` 里 `npcs = list(cfg.get('npcs', []))`
#     —— 那 25 个是 `config.json` 里**写死的史莱克城(10001)** NPC，**任何场景都照发**。
#     于是进了乾坤日月谷(10005) 屏幕上还是史莱克城的人。
#
#     数据来源：APK `config_map.luac` 的 `Config.Map[scene].npcs`（只给 bid + x/y）。
#     实测：10001 → 25 个；**10005 → 3 个**（10310/10320/10330）。
#     场景不在表里 ⇒ 才回退到 `cfg['npcs']`（保持旧行为，不制造空白场景）。
#     `name` 留空由客户端按 bid 本地解析（与 `scene_elems` 同一约定，**不编造**）。
#     """
#     scene = (map_cfg() or {}).get(str(scene_id)) or {}
#     tbl = scene.get('npcs') or {}
#     if not tbl:
#         return list(cfg.get('npcs', []))
#     return [{'id': int(b), 'bid': int(b), 'type': 2,
#              'x': int(v.get('x') or 0), 'y': int(v.get('y') or 0), 'name': ''}
#             for b, v in tbl.items()]
#
#
# def scene_mons(cfg, scene_id):
#     """★ R73：**按场景**取怪表（修"乾坤日月谷里居然有戴浩"）。
#
#     `static_mons(cfg, scene_id)` 其实**完全无视 scene_id**，永远返回 `config.json:mons`
#     —— 那是 Phase D 的手工测试怪（`20001 戴浩`），本意是给**出生场景**做战斗验证的，
#     却跟着玩家进了挂机图。
#
#     规则（最小且可解释）：
#       · 场景在 `Config.Map` 里有条目 ⇒ 用**它自己的** `mons`（10005 是**空表** ⇒ 一只都不发）
#       · 再把 `config.json:mons` 里的测试怪**只在"出生场景"**补上（10001 保留戴浩，不动用户的测试环境）
#     """
#     scene = (map_cfg() or {}).get(str(scene_id)) or {}
#     out = []
#     for mid, m in (scene.get('mons') or {}).items():
#         bid = int(mid)
#         d = mon_def(bid)
#         out.append({'id': bid, 'bid': bid, 'type': 0,
#                     'name': d.get('name') or '', 'realm': 0, 'mspd': 100,
#                     'x': int(m.get('x') or 0), 'y': int(m.get('y') or 0), 'dir': 0,
#                     'res_id': d.get('res_id') or '', 'status': 0,
#                     'source': 'config_map', 'why': 'Config.Map[%s].mons' % scene_id})
#     _spawn_bid = int((cfg.get('spawn') or {}).get('bid') or 10001)
#     if int(scene_id) == _spawn_bid:
#         have = {m['id'] for m in out}
#         for m in static_mons(cfg, scene_id):
#             if m['id'] not in have:
#                 out.append(m)
#     elif not scene:
#         out = static_mons(cfg, scene_id)      # 场景不在表里 ⇒ 回退旧行为
#     # ★★★ R77：**挂机怪也算"本场景的怪"** —— 统一在这里补，让
#     #   `10201`（下发给客户端建精灵）与 `20002`（校验"点击的怪在不在"）
#     #   **用同一份列表**。R76 只把它加在 `_send_10200` 的局部变量里，
#     #   于是 `20002` 校验时看不到它 ⇒ 点怪回 `no such monster 10105`。
#     try:
#         # ★ 等级必须读**实时状态**（DB），不能读 `cfg['role']` 的静态模板
#         #   —— 这正是 R56 那类 bug（`13340` 读模板而 `10302` 读 DB）的复发点。
#         _lev9 = int((role_state(cfg) or {}).get('lev')
#                     or (cfg.get('role') or {}).get('lev') or 1)
#         _spot9 = guaji_spot_for_lev(_lev9) or {}
#         if int(_spot9.get('map_bid') or 0) == int(scene_id) and _spot9.get('mon_bid'):
#             _mb9 = int(_spot9['mon_bid'])
#             if not any(int(m.get('bid') or 0) == _mb9 for m in out):
#                 _x9, _y9 = map_def_xy(int(scene_id))
#                 _d9 = mon_def(_mb9)
#                 out.append({
#                     'id': _mb9, 'bid': _mb9, 'type': 0,
#                     'name': _d9.get('name') or '', 'realm': 0, 'mspd': 100,
#                     'x': int(_x9 or 0), 'y': int(_y9 or 0), 'dir': 0,
#                     'res_id': _d9.get('res_id') or '', 'status': 0,
#                     'source': 'guaji', 'why': 'R77 挂机图等级段的怪（与 20002 共用）'})
#     except Exception:
#         pass
#     return out


def scene_quest_extras(cfg, scene_id):
    """返回 (npcs, mons)：**本场景的**静态表 + 任务链当前需要的剧情 NPC / 目标怪物。

    `scene_id` 取当前场景 bid；任务链在途任务由 mission_chain 决定。
    ★ R73：静态部分改为走 `scene_npcs/scene_mons`（按场景），修掉"任何图都发史莱克城 NPC"。
    """
    npcs = scene_npcs(cfg, scene_id)
    mons = scene_mons(cfg, scene_id)
    qs = quest_spawn()
    if qs is None or not cfg.get('quest_spawn', True):
        return npcs, mons
    try:
        rid = (cfg.get('role') or {}).get('rid', 1001)
        active = mission_chain(cfg, rid)
        extra_npcs, extra_mons = qs.extras(scene_id, active)
        # ★★ R73：**剧情目标怪只在出生场景刷**（修"乾坤日月谷里居然有戴浩"）
        #   为什么必须加这道闸：`mission_config` 里**没有任何场景字段**
        #   （例：10020「切磋魂技」= `progress=[["fight_mon",20001,1]]`，只说"打 20001 戴浩"，
        #     不说"在哪儿打"）。而 `quest_spawn.target_mons(scene_id, …)` 目前并不按场景过滤
        #   ⇒ 于是**每张图**都会刷出这只剧情怪，进了挂机图也跟着出现。
        #   在没有场景字段之前，"只在出生场景刷"是**保守且可解释**的选择
        #   （原版这些剧情切磋都发生在史莱克城）；等拿到 per-mission 场景数据再放宽。
        _spawn_bid2 = int((cfg.get('spawn') or {}).get('bid') or 10001)
        if int(scene_id) != _spawn_bid2 and extra_mons:
            log('tcp.log', '  .. quest_spawn：非出生场景(%s≠%s) ⇒ 不刷剧情目标怪 %s'
                % (scene_id, _spawn_bid2, [m.get('bid') for m in extra_mons]))
            extra_mons = []
        have = {n.get('bid') for n in npcs}
        for n in extra_npcs:
            if n['bid'] not in have:
                npcs.append(n)
                have.add(n['bid'])
        # 任务目标怪物：补齐 name/res_id（原版 Config.Mon），并避开已配置的怪物 id
        have_mon = {m['id'] for m in mons}
        for m in extra_mons:
            if m['id'] in have_mon:
                continue
            d = mon_def(m['bid'])
            if not m.get('name') or m.get('name', '').startswith('npc'):
                m['name'] = d.get('name') or m.get('name') or ''
            if not m.get('res_id'):
                m['res_id'] = d.get('res_id') or ''
            mons.append(m)
            have_mon.add(m['id'])
        if extra_npcs or extra_mons:
            log('tcp.log', '  ★ quest_spawn scene=%s +%d npc %s +%d mon %s'
                % (scene_id, len(extra_npcs),
                   [n['bid'] for n in extra_npcs],
                   len(extra_mons), [m['bid'] for m in extra_mons]))
    except Exception as e:
        log('tcp.log', '  !! scene_quest_extras failed: %r' % (e,))
    return npcs, mons


def mission_progress_advance(rid, cond_name, target, n=1):
    """把满足条件（条件名 + 目标 id）的在途任务推进 n 点；够了就置 **STATUS_2（可提交）**。

    ★ 状态迁移（依据 `mission_util.luac` proto#68 的 `MissionStatus` 常量表 +
       `npc_mission_manager.luac` proto#5 `addNpc` 的分桶）：
          条件未满足 → STATUS_1（进行中，进 NPC 的 access_list）
          条件已满足 → **STATUS_2（可提交，进 NPC 的 finish_list ⇒ 对话里出现"完成"项）**
       提交后由 12403 处理函数置 STATUS_3（已完成）。

    **供后续把"击杀/采集"等游戏事件接进来时调用**（本轮未接任何战斗逻辑）。
    返回被推进的任务 bid 列表。
    """
    touched = []
    for bid, m in db_get_missions(rid).items():
        if int(m.get('mission_status') or 0) >= 2:
            continue
        if int(m.get('target') or 0) != int(target):
            continue
        d = mission_def(bid)
        prog = (d.get('progress') or [])
        cname = prog[0][0] if (prog and isinstance(prog[0], (list, tuple))
                               and len(prog[0]) >= 1) else None
        if cname != cond_name:
            continue
        need = int(m.get('target_value') or 0)
        val = min(need, int(m.get('value') or 0) + int(n)) if need > 0 else 0
        done = (need > 0 and val >= need)
        db_save_mission(rid, {
            'mission_bid': bid,
            'value': val,
            'process_status': 1 if done else int(m.get('process_status') or 0),
            # ★ 条件达成 ⇒ STATUS_2（可提交），这样 NPC 对话才会列出"完成"
            'mission_status': 2 if done else int(m.get('mission_status') or 1),
        })
        touched.append(bid)
    return touched


def accept_mission(cfg, rid, bid):
    """按配置**接取**一条指定任务（★ C5-B：给 12414 `accept_talk` 用）。

    返回 (ok, already, meta)：
      ok=False      → 配置里没有这个 bid（调用侧应诚实拒绝，不凭空建行）
      already=True  → DB 里已在途/已完成（幂等，不重复播种）

    播种口径与 `task/service.py::mission_rows()` **逐字一致**（status=1 且带 target/need），
    这样接取后的任务才能被 `mission_progress_advance()` 正常推进——
    否则会出现"对话接取了任务但永远打不动"的半截状态。
    """
    bid = int(bid)
    d = mission_def(bid)
    if not d:
        return False, False, None
    m = db_get_missions(rid).get(bid)
    if m is not None and int(m.get('mission_status') or 0) >= 1:
        return True, True, m
    prog = d.get('progress') or []
    cond = None
    if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
        cond = prog[0]
    db_save_mission(rid, {
        'mission_bid': bid,
        'mission_status': 1 if cond else 2,
        'process_status': 0,
        'target': int(cond[1]) if (cond and cond[1] is not None) else 0,
        'target_value': int(cond[2]) if (cond and cond[2] is not None) else 0,
        'value': 0, 'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
        'code': 0, 'accept_time': int(time.time()),
    })
    return True, False, d


def accept_mission_rows(cfg, rid):
    """“可接取列表”（SC_12407 / SC_12409）的内容。

    ★ 设计依据：剧情链是**线性**的 ⇒ 同一时刻只能有**一条**在“进行中”（进 `12400`）。
       链上后续的任务放进“**可接取**”而不是“已接取” ⇒
       **既能看到多条，又不会在任务栏重名。**
       这正是 `12407/12408/12409` 这组协议存在的意义。

    取链头之后、且 `lev <= 玩家等级` 的前 N 条（N = mission_accept_max，默认 6）。
    """
    # 2026-10-17：原处 chain = mission_chain(cfg, rid) 赋值后从未使用（函数实际用 full 排序），
    #   删掉这个死赋值；mission_chain 的截取语义仍由 mission_chain_max 在别处生效。
    full = []
    rid_row = db_get_role(rid) or {}
    lev = int(rid_row.get('level') or (cfg.get('role') or {}).get('lev', 1) or 1)
    for b, v in sorted(mission_cfg().items()):
        if v.get('type') == 1 and int(v.get('lev') or 0) <= lev:
            full.append(b)
    # 链头（= 当前进行中的那条）
    head = None
    rows = db_get_missions(rid)
    for b in full:
        m = rows.get(b)
        if m is not None and int(m.get('mission_status') or 0) < 3:
            head = b
            break
    if head is None:
        return []
    n = int(cfg.get('mission_accept_max', 6))
    out = []
    seen = False
    for b in full:
        if not seen:
            if b == head:
                seen = True
            continue
        out.append({
            'mission_bid': b, 'mission_status': 0, 'process_status': 0,
            'target': 0, 'target_value': 0, 'value': 0,
            'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
            'code': 0, 'accept_time': 0,
        })
        if len(out) >= n:
            break
    return out


# [P3deep-migrated] mission_rows 已整体下沉 task/service.py（逐字一致）：
# def mission_rows(cfg, rid, include_done=False):
#     """取该角色的任务列表：**数据库优先**；库里没有就**按 APK 任务表播种**。"""
#     rows = db_get_missions(rid)
#     seeded = 0
#     if not rows:
#         # ① 若 config.json 显式给了 missions，优先用它们（保留手工控制能力）
#         for m in (cfg.get('missions') or []):
#             mm = {'mission_bid': m.get('mission_bid', 0)}
#             for c in _MIS_COLS:
#                 if c in m:
#                     mm[c] = m[c]
#             db_save_mission(rid, mm)
#             seeded += 1
#     # ② 按 APK 主线链**补齐**（幂等；每次调用都做）
#     #    ★ 这里原先被包在 `if not rows:` 里 ⇒ **等级提升后解锁的新任务永远不会播种**。
#     #      实测：等级从 7 调到 70 后，库里仍只有 10051–10054 四条，链不再增长。
#     #      移到外层后，只要 `mission_chain()`（其入参含 `lev <= 玩家等级`）返回了新任务，
#     #      就会补进 DB。
#     _have = {int(x.get('mission_bid', -1)) for x in rows.values()}
#     for bid in mission_chain(cfg, rid):
#         if bid in _have:
#             continue
#         d = mission_def(bid)
#         # ★ 完成条件（来自 APK 的 `progress`）：
#         #   progress 为空       ⇒ 无条件，到 commit_npc 处即可提交（如 10010）
#         #   progress = [[cond, target, num], …] ⇒ 需要进度（如 fight_mon 击杀）
#         prog = d.get('progress') or []
#         cond = None
#         if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
#             cond = {'name': prog[0][0], 'target': prog[0][1], 'need': prog[0][2]}
#         # ★★ MissionStatus（**权威来源**：`mission_util.luac` proto#68 的常量表）
#         #     STATUS_0=0 可接取 ／ STATUS_1=1 进行中
#         #     STATUS_2=2 可提交 ／ STATUS_3=3 已完成
#         #   客户端 `npc_mission_manager.luac` proto#5 `addNpc` 的分桶：
#         #     status0→can_list  status1→access_list  **status2→finish_list**
#         #   而 `npc_dialogs.luac` proto#8 `openNpc` 正是用
#         #     manager:getNpcVo(bid):getMissionList() 来生成对话里的任务项。
#         #   ⇒ **没有 status=2，NPC 对话里就不会出现"完成/提交"项**。
#         #   因此：无条件的任务（"去某 NPC 处报到"类）播种即为**可提交**。
#         db_save_mission(rid, {
#             'mission_bid': bid,
#             'mission_status': 1 if cond else 2,
#             'process_status': 0,
#             'target': int(cond['target']) if cond else 0,
#             'target_value': int(cond['need']) if cond else 0,
#             'value': 0,
#             'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
#             'code': 0, 'accept_time': 0,
#         })
#         log('tcp.log', '  .. mission %d (%s) 播种 cond=%r status=%d'
#             % (bid, d.get('name'), cond, 1 if cond else 2))
#         seeded += 1
#     rows = db_get_missions(rid)
#     if seeded:
#         log('tcp.log', '  ** missions seeded into DB for rid=%s (+%d, 共 %d 条, '
#                        '来自 APK 任务表/等级 %s)'
#             % (rid, seeded, len(rows),
#                (db_get_role(rid) or {}).get('level')))
#     # ★ 状态归一（幂等）：把"无条件 / 条件已满足"的在途任务提升为
#     #   **STATUS_2（可提交）**。
#     #   依据：`MissionStatus` 常量表（mission_util.luac proto#68）+ 客户端
#     #   `npc_mission_manager.luac` proto#5 `addNpc` 的分桶（status2→finish_list）。
#     #   老存档里这些任务停在 STATUS_1，会导致 **NPC 对话里不出现"完成"项**。
#     # ★ 修复（用户实测报障）：把"可提交"**限制在剧情链头一条**上。
#     #   原实现把**所有**"无条件"任务提升为 STATUS_2
#     #   ⇒ 任务栏同时出现多条同名的 `武魂觉醒`（且都显示已完成/可提交），
#     #     而 mission_rows 只过滤 status=3 ⇒ **它们永远不消失**。
#     _chain = mission_chain(cfg, rid)
#     _head = None
#     for _b in _chain:
#         _m = rows.get(_b)
#         if _m is not None and int(_m.get('mission_status') or 0) < 3:
#             _head = _b
#             break
#     # ★ 优化（纯日志/写库去重，不改语义）：
#     #   原实现的 db_save_mission 已经是条件式（`if st != 2` 等），
#     #   **但那行 log 是无条件的** ⇒ 每次调用都写一行，
#     #   长期运行会持续膨胀日志（实测累计 78 行、tcp.log 567 KB）。
#     #   现改为**仅在状态真的发生变化时**才打日志（写库行为不变）。
#     _changed = 0
#     for k, m in list(rows.items()):
#         st = int(m.get('mission_status') or 0)
#         if st == 3:
#             continue
#         prog = (mission_def(k).get('progress') or [])
#         if prog and isinstance(prog[0], (list, tuple)) and len(prog[0]) >= 3:
#             need = int(m.get('target_value') or 0)
#             have = int(m.get('value') or 0)
#             if need > 0 and have >= need:
#                 if st != 2:
#                     db_save_mission(rid, {'mission_bid': k, 'mission_status': 2})
#                     m['mission_status'] = 2
#                     _changed += 1
#             continue
#         if k == _head:
#             if st != 2:
#                 db_save_mission(rid, {'mission_bid': k, 'mission_status': 2})
#                 m['mission_status'] = 2
#                 _changed += 1
#         elif st == 2:
#             db_save_mission(rid, {'mission_bid': k, 'mission_status': 1})
#             m['mission_status'] = 1
#             _changed += 1
#     if _changed:
#         log('tcp.log', '  .. mission status normalized: chain_head=%s (变更 %d 条)'
#             % (_head, _changed))
#     out = [rows[k] for k in sorted(rows)]
#     if not include_done:
#         out = [m for m in out if int(m.get('mission_status') or 0) != 3]
#     return out






# [P3deep-migrated] db_get_role 已在 role/storage.py（L62 import），本地副本注释：
# def db_get_role(rid):
#     """读一行；不存在返回 None。"""
#     try:
#         con = db_conn()
#         con.row_factory = sqlite3.Row
#         row = con.execute('SELECT * FROM roles WHERE rid=?', (rid,)).fetchone()
#         db_release(con)
#         return dict(row) if row else None
#     except Exception as e:
#         log('tcp.log', '  !! db_get_role failed: %r' % (e,))
#         return None




# ---------------------------------------------------------------------------
# ★★ R44：最小账号层（uid ← CS_1110.args.account）
# ---------------------------------------------------------------------------






# DB 列名 ↔ SC 字段名 的映射（10301/10302 里 lev/career/… 的命名与表列略有差别）
_DB_TO_SC = {'level': 'lev', 'vip_level': 'vip_lev', 'x': 'x', 'y': 'y',
             'dir': 'dir', 'scene_id': 'scene_id', 'name': 'name',
             'career': 'career', 'sex': 'sex', 'exp': 'exp', 'gold': 'gold',
             'gold_acc': 'gold_acc', 'title': 'cur_title', 'status': 'status',
             'uid': 'uid', 'diamond': 'diamond', 'coin': 'coin', 'hp': 'hp', 'max_hp': 'max_hp',
             'mp': 'mp', 'max_mp': 'max_mp'}






# SC_10303 的 attr 大表字段顺序（取自 protocol/manual.md 的 SC_10303 定义）
ATTR_FIELDS = [
    ('strength', 'u16'), ('intellect', 'u16'), ('armor', 'u16'), ('constiution', 'u16'),
    ('atk_s', 'u32'), ('atk_p', 'u32'), ('def_s', 'u32'), ('def_p', 'u32'),
    ('hp_max', 'u32'), ('atk_speed', 'u32'), ('hit', 'u32'), ('dodge', 'u32'),
    ('crit', 'u32'), ('tenacity', 'u32'), ('red_def_s', 'u32'), ('red_def_p', 'u32'),
    ('atk_abs', 'u32'), ('def_abs', 'u32'), ('reduce', 'u32'), ('hurt', 'u32'),
    ('hit_rate_show', 'u32'), ('dodge_rate_show', 'u32'),
    ('crit_rate_show', 'u32'), ('tenacity_rate_show', 'u32'),
]

# attr 里可配置的默认值（非 0，便于面板上能看出效果）
ATTR_DEFAULTS = {
    'strength': 10, 'intellect': 10, 'armor': 10, 'constiution': 10,
    'atk_s': 100, 'atk_p': 100, 'def_s': 80, 'def_p': 80,
    'hp_max': 1000, 'atk_speed': 100, 'hit': 50, 'dodge': 50,
    'crit': 30, 'tenacity': 30, 'red_def_s': 0, 'red_def_p': 0,
    'atk_abs': 0, 'def_abs': 0, 'reduce': 0, 'hurt': 0,
    'hit_rate_show': 0, 'dodge_rate_show': 0,
    'crit_rate_show': 0, 'tenacity_rate_show': 0,
}

# role_attr 表的列名集合（= 协议里的 attr 字段名，无需二次映射）
_ATTR_COL_SET = {name for name, _ in ATTR_FIELDS}




def build_10305(cfg):
    """SC_10305 角色**资产增量**刷新：`assets:table{label:u8, val:u32}`。

    ★ 依据（2026-10-06 取证）：
      · `cmd_table` 记 10305 =「**角色资产信息更新某几个**」⇒ 语义是**服务端增量推送**；
      · 客户端 `game/role/role_ctrl.luac` 确有 `RegisterProtocal(10305,'rgp_hander10305')`
        ⇒ **客户端有处理器**（按号注册，故搜 `on10305` 搜不到）；
      · `tcp.log` **全量统计**：客户端请求 10305 = **0 次**，服务端发过 = **0 次**
        ⇒ 原实现"等客户端来请求"的分支**永不执行**（**死代码**）⇒ 必须**主动推送**。
    ★ `label` 由 `asset_label_map()`（= `config_game_data.CodeToAssets` 反查）给出；
      **`practice_exp`(label=9)** 取修炼进度（skill bid=10822 的 exp）—— 与 SC_10302/10304 同源。
    ★ 不编造：db 里没有的资产不发；label 映射不到的跳过。
    """
    lm = asset_label_map()
    _rid = int(role_state(cfg).get('rid', 1001))
    rows = {}
    try:
        for k, v in (db_get_assets(_rid) or {}).items():
            lb = lm.get(str(k))
            if lb:
                rows[int(lb)] = int(v)
    except Exception as e:
        log('tcp.log', '  !! build_10305 读资产失败: %r' % (e,))
    # practice_exp（label=9）= 修炼进度，与 SC_10302/10304 的 practice_exp 同源
    try:
        for _sk in (cfg.get('skills') or []):
            if int(_sk.get('bid', 0)) == 10822:
                rows[9] = int(_sk.get('exp', 0))
                break
    except Exception:
        pass
    b = w_u16(len(rows))
    for lb in sorted(rows):
        b += w_u8(int(lb) & 0xff) + w_u32(int(rows[lb]) & 0xffffffff)
    return b






# ---------------------------------------------------------------------------
# 各子系统的"最小合法应答"：只写固定字段，所有 table 字段给空表（u16 0）。
# 字段顺序取自 protocol/manual.md 的 SC 定义（用 tools/show_cmd.py <cmd> 可复核）。
# 目的：让客户端的开局数据拉取能走完，从而推进到 10200 进入场景。
# ---------------------------------------------------------------------------
EMPTY_REPLIES = {
    10921: lambda: w_u8(1) + w_u32(0) + w_u16(0) + w_u16(0) + w_u16(0),
    10924: lambda: w_u16(0),                                    # act_list
    10932: lambda: w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0),
    11200: lambda: w_u8(0) + w_u8(0) + w_u16(0) + w_u16(0),
    11215: lambda: w_u16(0),                                    # partner_list
    11600: lambda: (w_u8(0) + w_u32(0) + w_u32(0) + w_u16(0) + w_u16(0) +
                    w_u16(0) + w_u32(0) + w_u32(0) + w_u16(0)),
    # ⚠ 13200 已移除（与 15801 同源的一条"猜的包"）：
    #   server/proto_defs.py 里 SC_13200 = {msg:string, team_id:uint32, ...}，
    #   而 team_data.luac proto[3] 在函数尾段**无条件**执行
    #       GGET message ; TGETS resp.msg ; CALL
    #   即 `message(resp.msg)`。我们回的 msg='' ⇒ 客户端 message('')。
    #   实测：tcp.log 每次 `>> cmd=13200` 与 http.log 的
    #   `alertHex message_hex_(空)` 一一对应（12:35:34 / 12:35:38 / 12:37:20 三次）。
    #   既然空 msg 会走到"空正文提示"，就不该回这个包 → 宁可**不回**。
    13771: lambda: w_u16(0) + w_u32(0),
    # ⚠ 15801 已移除：beast_ctrl.luac 的 on15801 等处理器会 `message(resp.msg)`，
    #   而 15801 的 SC 结构里有若干 `D|Dsc*|` 动态子表我没解出来（属"猜的编码"）。
    #   猜错 → 客户端读出的 msg 为 nil → message(nil) → **空白提示框**。
    #   宁可**不回**（请求得不到应答，最多是某个面板空着），也不要回一个
    #   会触发错误弹窗的畸形包。这正是"有本地私服、有角色，但点进入游戏弹空白框"的来源。
    16500: lambda: w_u16(0),                                    # info
    16706: lambda: w_u8(0) + w_str('') + w_u16(0),
    17200: lambda: w_u32(0) + w_u8(0),
    18900: lambda: w_u16(0) + w_u16(0) + w_u16(0),              # fabao_list
}


# ---------------------------------------------------------------------------
# 角色状态持久化（阶段 3 · 第五/六阶段）
# 先用最简单的 JSON 落盘（不引入数据库），够验证"重启后角色仍在、坐标恢复"。
# 文件：server/state/role_<rid>.json
# ---------------------------------------------------------------------------
# [P2B-migrated persistence/db.py::STATE_DIR] STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state')


def _role_state_path(rid):
    return os.path.join(STATE_DIR, 'role_%s.json' % rid)


def load_role_state(rid):
    try:
        with open(_role_state_path(rid), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def save_role_pos(rid, x, y):
    """移动协议用：把坐标写进 **数据库**（Phase 4E 起以 DB 为准）。
    仍保留 role_<rid>.json 作为可读快照，便于人工核对。"""
    ok = db_save_role(rid, x=int(x), y=int(y))
    # 兼容快照（只读用途）
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        st = load_role_state(rid) or {}
        st.update({'rid': rid, 'x': int(x), 'y': int(y),
                   'saved_at': int(time.time())})
        with open(_role_state_path(rid), 'w', encoding='utf-8') as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    if ok:
        log('tcp.log', '  ** DB persist role %s pos=(%d,%d)' % (rid, x, y))


def role_with_saved_pos(cfg):
    """把角色状态（**以数据库为准**）合并出来，供 10201/10200 下发。"""
    st = role_state(cfg)
    log('tcp.log', '  .. role %s state from DB pos=(%s,%s) lev=%s gold=%s'
        % (st.get('rid'), st.get('x'), st.get('y'), st.get('lev'),
           st.get('gold')))
    return st


def login_scene_bid(cfg):
    """登录进场景用哪个 bid：**优先存档场景 `roles.scene_id`**，否则 `spawn.bid`。

    ★ 2026-10-16 修复（GM 后台传送实测暴露的真缺陷）：
      原实现（10102 分支）恒用 `self.cfg['spawn']['bid']` = 10001 ⇒ 无论玩家
      上次在哪个图，**重登一律被拽回史莱克城**。后果：GM `/DSH_ADMIN/setscene`
      传送、挂机图（`config_guaji` 的 10002–10011）、副本入口的"所在地"全部
      只在当前连接有效，一重登就丢 —— 私服化下等于**只有一张图可玩**。

      改为读存档场景。兜底：存档为空、或该场景不在 `config_map` 里（`map_def_xy`
      返回 (0,0)）⇒ 回退 `spawn.bid`，保证不会把玩家丢进不存在的图。
    """
    _bid = 0
    try:
        _bid = int(role_with_saved_pos(cfg).get('scene_id') or 0)
    except Exception:
        _bid = 0
    if _bid:
        try:
            _mx, _my = map_def_xy(_bid)
        except Exception:
            _mx, _my = (0, 0)
        if _mx or _my:
            return _bid
    return cfg.get('spawn', {}).get('bid', 1)






def build_10201(roles, npcs=None, mons=None, elems=None):
    """SCMapGird_10201{roles:table, npcs:table, mons:table, elems:table}

    roles 元素字段顺序取自 protocol/manual.md（含 Dsc10201* 子结构）：
      rid:u32, srv_id:str, name:str, lev:u16, career:u16, vip_lev:u8, sex:u8,
      status:u8, mspd:u16, x:u16, y:u16, dir:u8, hidden:u8, cur_title:u16,
      ntm_title:u32, marry_state:u8, spouse_name:str,
      buff_bids / misc_uint8 / misc_uint16 / misc_uint32 / misc_str / animate_res
    ⚠ 最后 6 个是 `D|Dsc*|` 动态表，提取器未能解出字段（Dsc10201misc 标注为"无字段"），
      这里先按"计数前缀 + 0 项"编码（与其它表一致），靠客户端是否报错来验证。
    """
    b = w_u16(len(roles))
    for r in roles:
        b += w_u32(r.get('rid', 1001))
        b += w_str(r.get('srv_id', '1'))
        b += w_str(r.get('name', 'DSH'))
        b += w_u16(r.get('lev', 1))
        b += w_u16(r.get('career', 1))
        b += w_u8(r.get('vip_lev', 0))
        b += w_u8(r.get('sex', 0))
        b += w_u8(r.get('status', 0))
        b += w_u16(r.get('mspd', 100))
        b += w_u16(r.get('x', 100))
        b += w_u16(r.get('y', 100))
        b += w_u8(r.get('dir', 0))
        b += w_u8(r.get('hidden', 0))
        b += w_u16(r.get('cur_title', 0))
        b += w_u32(r.get('ntm_title', 0))
        b += w_u8(r.get('marry_state', 0))
        b += w_str(r.get('spouse_name', ''))
        b += w_u16(0)     # buff_bids
        b += w_u16(0)     # misc_uint8
        b += w_u16(0)     # misc_uint16
        b += w_u16(0)     # misc_uint32
        b += w_u16(0)     # misc_str
        b += w_u16(0)     # animate_res
    b += build_npcs(npcs or [])
    b += build_mons(mons or [])
    b += build_elems(elems or [])
    return b


def build_mons(mons):
    """把 mons 追加进 10201 body。

    字段顺序取自 `protocol/manual.md` 的 `SCMapGird_10201`：
      id:uint32, bid:uint32, type:uint8, name:string, realm:uint8,
      mspd:uint16, x:uint16, y:uint16, dir:uint8, res_id:string, status:uint8

    ★ 它本来一直是**写死的 0 条**（`w_u16(0)`）。而 `Config.Map[*].mons`
      在客户端配置里**全表为空**，所以 `fight_mon` 类任务的目标怪物
      只能由服务端下发 —— 这里就是那条路径。
    """
    b = w_u16(len(mons))
    for m in mons:
        b += w_u32(m.get('id', 0))
        b += w_u32(m.get('bid', 0))
        b += w_u8(m.get('type', 0))
        b += w_str(m.get('name', ''))
        b += w_u8(m.get('realm', 0))
        b += w_u16(m.get('mspd', 100))
        b += w_u16(m.get('x', 0))
        b += w_u16(m.get('y', 0))
        b += w_u8(m.get('dir', 0))
        b += w_str(m.get('res_id', ''))
        b += w_u8(m.get('status', 0))
    return b


def build_elems(elems):
    """把 elems 追加进 10201 body。

    字段顺序取自 `protocol/manual.md` 的 `SCMapGird_10201`：
      id:uint32, bid:uint32, type:uint8, sub_type:uint8, name:string,
      x:uint16, y:uint16, res_id:string
    """
    b = w_u16(len(elems))
    for e in elems:
        b += w_u32(e.get('id', 0))
        b += w_u32(e.get('bid', 0))
        b += w_u8(e.get('type', 0))
        b += w_u8(e.get('sub_type', 0))
        b += w_str(e.get('name', ''))
        b += w_u16(e.get('x', 0))
        b += w_u16(e.get('y', 0))
        b += w_str(e.get('res_id', ''))
    return b


def build_npcs(npcs):
    """把 npcs 追加进 10201 body（供 build_10201 调用或单独拼接）。

    npcs 元素字段（protocol/manual.md）：
      id:u32, bid:u32, type:u8, x:u16, y:u16, name:string,
      misc:D|Dsc10201misc|, animate_res:D|Dsc10201animate_res|,
      member:D|Dsc10201member|

    ⚠ misc / member 是 `D|Dsc*|` 动态表，提取器未解出字段（Dsc10201misc 标注"无字段"）。
      这里沿用**在 roles 上已被证实可用**的同一套做法：按"计数前缀 + 0 项"编码。
      roles 用这个做法时客户端解析出了正确的 rid/x/y/career/sex/lev/name/srv_id，
      所以对 npcs 采用同一约定是有依据的（不是纯猜）。
    """
    b = w_u16(len(npcs))
    for i, n in enumerate(npcs):
        b += w_u32(n.get('id', 9000 + i))
        b += w_u32(n.get('bid', 20006))
        b += w_u8(n.get('type', 0))
        b += w_u16(n.get('x', 30))
        b += w_u16(n.get('y', 30))
        b += w_str(n.get('name', ''))
        b += w_u16(0)      # misc
        b += w_u16(0)      # animate_res
        b += w_u16(0)      # member
    return b


# ---------------------------------------------------------------------------
# ★ Phase D：背包（最小可用集）
#
# 协议依据：`cmd_resolve_105.luac` 的 AutoConstruct 数组（权威，见
# `python tools/proto_spec.py cmds 10500 10502`）：
#   CS_10502{bag_code:uint8}
#   SC_10502{bag_code:uint8,
#            items:table(id:u32, bid:u32, hero_bid:u32, bind:u8, intensify_lev:u8,
#                        pos:u16, quantity:u16, ctime:u32, expire_ts:u32,
#                        durable:u16, object:u8,
#                        attrs_ext:D, attrs_ext_list:D, attrs_ext_one_list:D,
#                        jewel_list:D, str_ext_list:D)}
#   SC_10500 与 SC_10502 的 items 结构完全相同（服务端单向推送）。
#
# 客户端模块：`assets/src/game/backpack/backpack_ctrl.luac` proto#18
#   bc#12 → `handle_10502`；bc#2 → `handle_10500`
#   （由子代理用 `tools/find_register_protocal.py` 全包扫描确认）
#
# ⚠ 5 个 `D|Dsc10502*|` 子表本实现一律发 **0 项**（未解出的扩展字段），
#   最小闭环只需要 id/bid/quantity/pos。
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ★ Phase D：原版掉落表（1.4.9 APK 直读，**不是编造**）
#
#   来源：`analysis/1.4.9/item/_config_drop.json` / `_config_drop_item.json`
#         （由子代理用 `tools/dump_drop_config.py` 从
#           `assets/src/config/config_drop.luac` 与
#           `config_drop_item.luac` 还原，见 `analysis/1.4.9/item/drop_model.md`）
#
#   结构：`Config.Drop[mon_bid]` 有 5 个掉落池字段
#           first / core / normal / holiday / （coin/wood 为字符串，语法 UNKNOWN）
#         每个池的值是 `Config.DropItem[pool_id]`（即 pool_id 指向 DropItem 组）。
#
#   ⚠ 重要事实（如实标注）：
#     1. 掉落**判定算法不在客户端**（全包 2234 个 .luac，`Config.Drop` 除定义点外零引用），
#        所以"roll 几次 / 保底 / 池优先级"等规则属**原版服务端数据，APK 无取证途径**。
#     2. 本实现只做**最小可解释**的 roll：
#          - 遍历 drop_type 对应的池；对命中的 DropItem 组，
#            按 `pp / p_sum` 加权抽 1 件（`pp` 语义为千分比是 INFERRED）。
#          - 这是 **IMPLEMENTATION_FALLBACK**，不是原版算法。
#     3. 覆盖率只有 24/2645 只怪有掉落表；本阶段的测试怪 20001 **在覆盖内**，
#        其掉落来自 `holiday` 池 3001（李逍遥灵魂玉 / 酒剑仙灵魂玉）。
# ---------------------------------------------------------------------------
DROP_CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '..', 'analysis', '1.4.9', 'item',
                             '_config_drop.json')
DROP_ITEM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              '..', 'analysis', '1.4.9', 'item',
                              '_config_drop_item.json')
_DROP_CFG = None
_DROP_ITEM = None
_ITEM_CFG = None

# ---------------------------------------------------------------------------
# ★★ 真实物品表 `Config.Item`（`config_item.luac` proto#1，**1117 条**，bid 33000–99999）
#
#   来源：`analysis/1.4.9/item/config_item.json`
#         （`tools/extract_config_item.py` 提取）
#   例：33001「10级速度符」、33006「100级伤害符」、35043「情缘烟花」
#
#   ⚠ 为什么必须有这张表：
#     `Config.Drop` / `Config.DropItem` 里那批 51000–51066 的物品
#     （李逍遥召唤符 / 酒剑仙灵魂玉 / 赵灵儿召唤符 …）
#     **全部不在本表内** —— 它们是仙剑/轩辕剑/古剑系角色，
#     与本作（斗罗大陆II 绝世唐门）无关。
#     实测：真实物品表号段为 33000–46999 与 99000–99999，
#     **51000 号段完全不存在**。
#     ⇒ 原版掉落表是**模板残留/死数据**，详见
#       `analysis/1.4.9/item/drop_model.md` §9。
#     ⇒ 因此本服务端**拒绝**下发任何不在真实物品表内的物品
#       （`roll_drops` 会逐项校验，不合法的一律丢弃并告警）。
# ---------------------------------------------------------------------------
# ★ 去重：旧定义（config_item.json 1117 条）会覆盖新定义 ⇒ 已删
_OLD_ITEM_CFG_PATH = None









# ---------------------------------------------------------------------------
# ★★ Phase E：角色等级表 `Config.RoleAttr`（1.4.9，**200 级**）
#
#   来源：`analysis/1.4.9/level/level_table.json`
#         （`tools/export_level_table.py` 从 `config_role_attr.luac` 导出）
#
#   ★ 为什么升级阈值要用这张表：
#     客户端 `game/main/main_ui.luac` proto#16 bc#0-5 是
#         local cfg = Config.RoleAttr[self.role.lev + 1]
#         self.expPos = role.exp / cfg.exp_max * self.expFull
#     ⇒ **处于 L 级时，经验条分母 = RoleAttr[L+1].exp_max**
#     服务端必须用同一个值判升级，否则经验条与服务端判定会不一致。
#
#   ⚠ 本表**不含** atk/hp/def（只有 exp_total/exp_max/attr_point/sinew_add/sinew_max）
#     ⇒ 逐级**属性**成长不在客户端配置里，见 `LEVEL_ATTR_GROWTH` 的标注。
# ---------------------------------------------------------------------------
LEVEL_TABLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'analysis', '1.4.9', 'level',
                                'level_table.json')
_LEVEL_TABLE = None














# ★ 逐级属性成长 —— **IMPLEMENTATION_FALLBACK / TEST_ONLY**
#   1.4.9 客户端配置里**没有**逐级属性表（`Config.RoleAttr` 只有经验/属性点，
#   `Config.RoleCareer[career].attr` 与 `turn_career_attr` **都是空表**，
#   `Config.Role` 在整包内不存在）。
#   ⇒ 真实成长值属原版服务端数据，APK 内无取证途径。
#   下面这张表是**兼容性最小实现**，每升 1 级给对应属性加固定量，**不是原版数值**。


# [P3deep-migrated] db_set_assets 已在 currency/service.py（L64 已 import），本地副本注释：
# def db_set_assets(rid, values):
#     """把通用资产表里的某些项**设为绝对值**（`db_add_assets` 只能加）。"""
#     if not values:
#         return True
#     try:
#         con = db_conn()
#         for name, amount in values.items():
#             con.execute('INSERT OR IGNORE INTO role_assets (rid, name, amount) '
#                         'VALUES (?,?,0)', (rid, str(name)))
#             con.execute('UPDATE role_assets SET amount = ? WHERE rid=? AND name=?',
#                         (int(amount), rid, str(name)))
#         con.commit()
#         db_release(con)
#         return True
#     except Exception as e:
#         log('tcp.log', '  !! db_set_assets failed: %r' % (e,))
#         return False






def drop_cfg():
    global _DROP_CFG, _DROP_ITEM
    if _DROP_CFG is None:
        try:
            with open(DROP_CFG_PATH, encoding='utf-8') as f:
                _DROP_CFG = (json.load(f).get('Config') or {}).get('Drop') or {}
            with open(DROP_ITEM_PATH, encoding='utf-8') as f:
                _DROP_ITEM = (json.load(f).get('Config') or {}).get('DropItem') or {}
            log('server.log', 'drop config loaded: Drop=%d DropItem=%d'
                % (len(_DROP_CFG), len(_DROP_ITEM)))
        except Exception as e:
            log('server.log', '!! drop config load failed: %r (降级为空表)' % (e,))
            _DROP_CFG, _DROP_ITEM = {}, {}
    return _DROP_CFG, _DROP_ITEM


def roll_drops(mon_bid):
    """按 1.4.9 原版掉落表抽取掉落。返回 [(item_bid, item_name, count, prob_src)]。

    ⚠ 抽取规则是 **IMPLEMENTATION_FALLBACK**（见上注），
      但**物品 id / 名字 / 数量 / 概率权重全部是原版数据**。
    """
    import random
    drop, ditem = drop_cfg()
    e = drop.get(str(int(mon_bid)))
    if not e:
        return []
    out = []
    for pool_field in ('first', 'core', 'normal', 'holiday'):
        raw = e.get(pool_field)
        if not raw:
            continue
        # 池字段有两种形态（实测）：
        #   ① 标量：直接是 `Config.DropItem` 的组 id（如 20001 的 holiday=3001）
        #   ② 字典：{组id: {序号: {num,min,pp,max}}}（如 20003 的 normal={"4001":{...}}）
        if isinstance(raw, dict):
            gids = [int(k) for k in raw.keys()]
        else:
            try:
                gids = [int(raw)]
            except Exception:
                continue
        for gid in gids:
            pool = ditem.get(str(gid))
            if not pool:
                continue
            items = sorted((pool.get('item_list') or {}).values(),
                           key=lambda x: int(x.get('bid') or 0))
            psum = int(pool.get('p_sum')
                       or sum(int(i.get('pp') or 0) for i in items))
            if psum <= 0 or not items:
                continue
            r = random.randint(1, psum)
            acc = 0
            for it in items:
                acc += int(it.get('pp') or 0)
                if r <= acc:
                    out.append((int(it.get('item_bid') or 0),
                                it.get('item_name') or '',
                                int(it.get('item_num') or 1),
                                '%s池%s pp=%s/%s' % (pool_field, gid,
                                                     it.get('pp'), psum)))
                    break
    # ★★ 逐项校验：物品必须存在于**真实物品表** `Config.Item` 里。
    #    `Config.Drop` 里那批 51000–51066 的物品（仙剑/轩辕剑系）**全部不在真实表内**
    #    —— 实为模板残留死数据。这里一律丢弃并告警，避免把不存在的物品发给玩家。
    good, bad = [], []
    for bid, nm, cnt, src in out:
        # ★ 2026-09-18：改用 is_valid_item（要求记录带真实 type）——
        #   原用 item_exists 只查键存在，空记录（type=None）会漏过 ⇒ 发出"空白物品"。
        if is_valid_item(bid):
            good.append((bid, item_name(bid) or nm, cnt, src))
        else:
            bad.append((bid, nm, src))
    if bad:
        log('tcp.log', '  !! 原版掉落表引用了**不存在的物品**（模板残留），已丢弃：%r'
            % (bad,))
    return good


def db_bag_init():
    try:
        con = db_conn()
        con.execute('''CREATE TABLE IF NOT EXISTS bag_items (
            rid INTEGER, bag_code INTEGER, item_id INTEGER, bid INTEGER,
            pos INTEGER, quantity INTEGER, ctime INTEGER,
            PRIMARY KEY (rid, bag_code, item_id))''')
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_bag_init failed: %r' % (e,))






def db_bag_repack(rid, bag_code=BAG_MAIN):
    """「整理背包」：把 pos 压紧成 1..N，返回**被改动的位置对** [(item_id, new_pos), ...]。

    ★ 2026-10-17：`db_bag_compact()` 只回一个计数，而"让客户端界面跟着变"必须把
      **新位置**发下去（SC_10508 `pos_up_arr:table(item_id:u32, new_pos:u8)`，文档 §8.3）
      ⇒ 需要这份明细。
    """
    changed = []
    try:
        con = db_conn()
        rows = con.execute('SELECT item_id, pos FROM bag_items WHERE rid=? AND bag_code=? '
                           'ORDER BY pos', (rid, bag_code)).fetchall()
        for i, (item_id, pos) in enumerate(rows, start=1):
            if int(pos) != i:
                con.execute('UPDATE bag_items SET pos=? '
                            'WHERE rid=? AND bag_code=? AND item_id=?',
                            (i, rid, bag_code, item_id))
                changed.append((int(item_id), int(i)))
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_bag_repack failed: %r' % (e,))
    return changed


def db_bag_compact(rid, bag_code=BAG_MAIN):
    """「整理背包」：把 pos 压紧成 1..N（保持原有先后）。返回被改动的行数。"""
    try:
        con = db_conn()
        rows = con.execute('SELECT item_id, pos FROM bag_items WHERE rid=? AND bag_code=? '
                           'ORDER BY pos', (rid, bag_code)).fetchall()
        changed = 0
        for i, (item_id, pos) in enumerate(rows, start=1):
            if int(pos) != i:
                con.execute('UPDATE bag_items SET pos=? '
                            'WHERE rid=? AND bag_code=? AND item_id=?',
                            (i, rid, bag_code, item_id))
                changed += 1
        con.commit()
        db_release(con)
        return changed
    except Exception as e:
        log('tcp.log', '  !! db_bag_compact failed: %r' % (e,))
        return -1


def db_bag_delete(rid, item_ids, bag_code=BAG_MAIN):
    """按 item_id 删除背包行。返回**确实删掉**的 item_id 列表（用于日志与回包）。"""
    gone = []
    try:
        con = db_conn()
        for iid in item_ids:
            cur = con.execute('DELETE FROM bag_items '
                              'WHERE rid=? AND bag_code=? AND item_id=?',
                              (rid, bag_code, int(iid)))
            if cur.rowcount:
                gone.append(int(iid))
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_bag_delete failed: %r' % (e,))
    return gone


def can_buy_num(g, bought):
    """剩余可购数量 = 原版 `limit_week`（每周限购）− 本服务端记录到的已购次数。

    ★ 依据（两条，都不是猜的）：
      1. 原版 `Config.MallGoods` 里**没有** `can_buy_num` 字段，但有 `limit_week`
         （见 `analysis/1.4.9/shop_luac/mall_table_1_Config.json`，134 条中 36 条 limit_week>0）；
      2. 客户端 `shop_model` proto#17（12801/12803 的列表解析器）把响应里的
         `can_buy_num` 原样复制进列表项，`shop_cell` proto#2 用它渲染图标角标
         （`can_buy_num == 0` 时**不显示**角标 —— 所以 0 必须继续表示"不限购"）。
    ⇒ 不限购（limit_week<=0）时返回 0，保持既有行为；限购时返回真实剩余。
    """
    lim = int(g.get('limit_week', 0) or 0)
    if lim <= 0:
        return 0
    return max(0, lim - int((bought or {}).get(int(g.get('id', 0)), 0)))






def bag_push_frames(handler, rid, full=False, bag_code=BAG_MAIN):
    """推送背包数据 + 格子最大值。

    `full=False`（默认）⇒ **SC_10500**（客户端语义 = **增量添加** `addItemInBagCode`）
    `full=True`         ⇒ **SC_10502**（客户端语义 = **清空重建** `initItemList`）

    ⚠⚠ 2026-10-17 **重要更正**（第一版改错过，别再改回去）：
      **主动推 SC_10502 会被客户端忽略** —— 客户端只在它自己发了 `CS_10502` 之后才处理
      `initItemList`（证据：本文件 10554 块的实测记录；文档
      `analysis/1.4.9/item/inventory_protocol_matrix.md` §8.3 把
      10501/10503/**10508**/10510/10543 列为"服务端主动推送"型，10502 不在其列）。
      ⇒ **删除 / 整理 / 穿装 / 入仓后要让界面跟着变**，用这三个推送：
        · `push_10503(handler, del_ids)` —— 告知哪些物品没了
        · `push_10508(handler, pairs)`   —— 告知物品新位置（整理/压紧后）
        · `push_10510(handler, rid)`     —— 格子最大值
      `full=True` 只保留给"客户端主动请求 10502"的场景，**不要**用它做推送刷新。

    ★ 第五轮真修复（2026-09-18）：**固定推 BAG_MAIN(=1)**，不再用 `_last_bag_code`。
      证据（修好探针后拿到的**强判据**：`/DSH_PROBE?t=bp&v=bagSizes_...` 直接报客户端
      `BackPackData.item_list` 各 bag_code 的条目数）：
          推送前 bagSizes … 1:9 … 7:0
          LOG    << 10500 SC_10500 bag push bag_code=7 items=10
          推送后 bagSizes … 1:9 … 7:10
      ⇒ 物品进了"客户端**最后请求过**的那个包"（本例 7），而用户的**魂囊页显示 bag 1**
        （客户端 bag1 条目数 == 我们 DB 里 bag_code=1 的行数，实测 9==9）
        ⇒ **可见页永远看不到新物品** —— 这就是"买了东西/加了东西背包不刷新"的根因。

    ● 两条消息的真实语义（反汇编确认，别再搞反）：
        SC_10500 → handle_10500 → backpack_data:addItemInBagCode(resp)  增量添加
        SC_10502 → handle_10502 → backpack_data:initItemList(resp)      清空重建
      另：早前探针里的 `datanil` / `addItem_bagCode<table>` / `sizena` 是**探针包装签名写错**
      造成的假象（真实签名是 `addItemInBagCode(self, resp)`），不是客户端没吃下 10500。
    """
    items = db_bag_get(rid, bag_code)
    bc = bag_code
    cmd = 10502 if full else 10500
    handler.request.sendall(pack_frame(cmd, w_u8(bc) + build_bag_items(items)))
    log('tcp.log', '  << %d SC_%d bag push(%s) bag_code=%d items=%d'
        % (cmd, cmd, '清空重建' if full else '增量添加', bc, len(items)))
    push_10510(handler, rid, bag_code)
    return [bc]


def live_push_bag(cfg, what='bag'):
    """向所有活跃连接推送背包刷新（HTTP 管理接口用）。返回推送成功的连接数。"""
    sent = 0
    with LIVE_LOCK:
        conns = list(LIVE_CONNECTIONS)
    for h in conns:
        try:
            rid = role_state(cfg).get('rid', 1001)
            bag_push_frames(h, rid)
            sent += 1
        except Exception as e:
            log('tcp.log', '  !! [热改推送-背包] 失败 %s: %r（移除该连接）'
                % (getattr(h, 'client_address', '?'), e))
            try:
                with LIVE_LOCK:
                    if h in LIVE_CONNECTIONS:
                        LIVE_CONNECTIONS.remove(h)
            except Exception:
                pass
    return sent


def db_mall_bought_add(rid, goods_id, n):
    """记录一次商城购买（goods_id = 商品条目 id，即 CS_12805 的 id）。"""
    try:
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO mall_bought (rid, goods_id, num) '
                    'VALUES (?,?,0)', (rid, int(goods_id)))
        con.execute('UPDATE mall_bought SET num = num + ?, updated_at=? '
                    'WHERE rid=? AND goods_id=?',
                    (int(n), int(time.time()), rid, int(goods_id)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_mall_bought_add failed: %r' % (e,))
        return False


def db_mall_bought(rid):
    """读该角色的商城购买次数 → {goods_id: 已购次数}。"""
    try:
        con = db_conn()
        rows = con.execute('SELECT goods_id, num FROM mall_bought WHERE rid=?',
                           (rid,)).fetchall()
        db_release(con)
        return {int(r[0]): int(r[1]) for r in rows}
    except Exception as e:
        log('tcp.log', '  !! db_mall_bought failed: %r' % (e,))
        return {}












def db_equip_put(rid, slot, item_id, bid, hero_bid=0):
    try:
        db_init_equip()        # ★ 防御：表不存在就建（避免“物品移出背包但没入装备”丢失）
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO equip_items '
                    '(rid,slot,item_id,bid,hero_bid,ctime) VALUES (?,?,?,?,?,?)',
                    (rid, int(slot), int(item_id), int(bid), int(hero_bid),
                     int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_equip_put failed: %r' % (e,))
        return False


def db_equip_take(rid, slot):
    """\u53d6\u4e0b\u67d0\u69fd\u88c5\u5907\uff0c\u8fd4\u56de\u88ab\u53d6\u4e0b\u7684\u884c\uff08\u65e0\u5219 None\uff09\u3002"""
    try:
        db_init_equip()
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM equip_items WHERE rid=? AND slot=?',
                          (rid, int(slot))).fetchone()
        out = dict(row) if row else None
        con.row_factory = None
        if out:
            con.execute('DELETE FROM equip_items WHERE rid=? AND slot=?', (rid, int(slot)))
            con.commit()
        db_release(con)
        return out
    except Exception as e:
        log('tcp.log', '  !! db_equip_take failed: %r' % (e,))
        return None


def equip_slot_for(rid, bid, cfg=None):
    """\u51b3\u5b9a\u4e00\u4ef6\u88c5\u5907\u8be5\u7a7f\u5728\u54ea\u4e2a\u69fd\u4f4d\u3002

    \u2605 \u4f9d\u636e\uff08\u5ba2\u6237\u7aef\u53d6\u8bc1\uff09\uff1a`handle_10511` \u91cc
      `self.data:rolePutOnEquip(resp.eqm_new_pos, resp.bag_item_id, resp.hero_bid)`
      \u21d2 **\u69fd\u4f4d\u7531\u670d\u52a1\u7aef\u56de\u7684 `eqm_new_pos` \u51b3\u5b9a**\u3002

    \u2605 \u7528\u6237\u5b9e\u673a\u62a5\u969c\u201c\u6b66\u5668\u88ab\u793c\u5305\u5360\u4e86\u4f4d\u201d \u21d2 \u4e4b\u524d\u786c\u7f16\u7801\u56de 0 / \u9012\u589e\u5206\u914d\uff0c
      \u628a\u201c**\u4e0d\u8be5\u88c5\u5907\u7684\u4e1c\u897f**\u201d\uff08\u793c\u5305/\u901f\u5ea6\u7b26\u7b49\u6d88\u8017\u54c1\uff09\u4e5f\u585e\u8fdb\u4e86\u88c5\u5907\u69fd\u3002

    \u2605 \u73b0\u6309\u201c**\u7269\u54c1 type \u2192 \u69fd\u4f4d**\u201d\u7684\u53ef\u914d\u7f6e\u8868 `equip_type_slot` \u6765\u5b9a\uff08config.json\uff09\uff1a
      - \u547d\u4e2d\u5219\u7528**\u8be5 type \u5bf9\u5e94\u7684\u56fa\u5b9a\u69fd\u4f4d**\uff08\u540c\u7c7b\u88c5\u5907\u5171\u7528\u4e00\u683c\uff0c\u5373\u6362\u88c5\uff09
      - \u672a\u547d\u4e2d\u4e14 `equip_type_slot` \u975e\u7a7a \u21d2 \u8fd4 **None**\uff08\u62d2\u7edd\uff1a\u4e0d\u8ba9\u975e\u88c5\u5907\u5360\u4f4d\uff09
      - `equip_type_slot` \u4e3a\u7a7a（\u9ed8\u8ba4\uff09\u21d2 \u56de\u9000\u201c\u627e\u4e00\u4e2a\u7a7a\u69fd\u201d\uff08\u4fdd\u6301\u539f\u884c\u4e3a\uff09
    """
    cfg = cfg or {}
    mapping = cfg.get('equip_type_slot') or {}
    t = item_type_of(bid)
    if mapping:
        key = str(t)
        if key in mapping:
            return int(mapping[key])
        # ★ 2026-10-17 修：原来这里是
        #       if t is not None: return None
        #   ⇒ 当 `item_type_of(bid)` 返回 None（**该 bid 根本查不到类型**）时会**掉到下面
        #     "找一个空槽"** 的分支 ⇒ 未知物品照样能占装备位 —— 正是本函数注释里说要防的
        #     "礼包占了武器位"。（2026-10-17 自检实测：bid=2/4/10001 这类查不到的 id 全返回槽位 7）
        #   现在只要配了 `equip_type_slot`，**类型不在映射内 / 查不到类型**一律拒绝。
        return None
    used = {int(r['slot']) for r in db_equip_all(rid)}
    sl = 1
    while sl in used:
        sl += 1
    return sl








def db_store_add(rid, bid, quantity=1, bag_code=STORAGE_CODE, item_id=None, merge=True):
    """入仓。

    ★★ 修正（用户报障“背包转移进仓库会覆盖原有物品”）：
      原实现两个问题：
        1. **同 bid 就叠加** —— 但“移动”应保留原来的物品身份（item_id），不能合并
        2. **自己算 MAX(item_id)+1** —— **忽略传入的 item_id** ⇒ 移动后 id 变了
      ⇒ 客户端/服务端按 item_id 定位就会错位 ⇒ 表现为“覆盖”。

    现：
      - `item_id` 传入时 **优先使用它**（保留身份），冲突则换一个不冲突的
      - `merge=False` 时 **不按 bid 叠加**（用于跨囊移动）
      - `merge=True`（默认）保持原行为（掉落/发物品时合并）

    ★★ 2026-09-18 单点防御：与 `db_bag_add` 一致，**拒绝无效 bid**
      （物品表里 type=None 的空记录会让客户端显示空白/乱码）。
    """
    if not is_valid_item(bid):
        log('tcp.log', '  !! db_store_add 拒绝无效物品 bid=%r qty=%r' % (bid, quantity))
        return None
    db_store_init()
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        iid = None
        if item_id is not None:
            used = {int(r[0]) for r in con.execute(
                'SELECT item_id FROM store_items WHERE rid=? AND bag_code=?',
                (rid, bag_code))}
            iid = int(item_id)
            while iid in used:
                iid += 1
        else:
            row = con.execute('SELECT * FROM store_items WHERE rid=? AND bag_code=? AND bid=?',
                              (rid, bag_code, bid)).fetchone() if merge else None
            if row:
                con.execute('UPDATE store_items SET quantity = quantity + ? '
                            'WHERE rid=? AND bag_code=? AND item_id=?',
                            (quantity, rid, bag_code, int(row['item_id'])))
                iid = int(row['item_id'])
        if iid is None or not con.execute(
                'SELECT 1 FROM store_items WHERE rid=? AND bag_code=? AND item_id=?',
                (rid, bag_code, iid)).fetchone():
            if iid is None:
                iid = int(con.execute('SELECT COALESCE(MAX(item_id),0)+1 FROM store_items '
                                      'WHERE rid=?', (rid,)).fetchone()[0])
                while iid in {int(r[0]) for r in con.execute(
                        'SELECT item_id FROM store_items WHERE rid=? AND bag_code=?',
                        (rid, bag_code))}:
                    iid += 1
            pos = con.execute('SELECT COALESCE(MAX(pos),0)+1 FROM store_items '
                              'WHERE rid=? AND bag_code=?', (rid, bag_code)).fetchone()[0]
            con.execute('INSERT INTO store_items (rid,bag_code,item_id,bid,pos,quantity,ctime) '
                        'VALUES (?,?,?,?,?,?,?)',
                        (rid, bag_code, iid, bid, pos, quantity, int(time.time())))
        con.commit()
        con.row_factory = None
        db_release(con)
        return iid
    except Exception as e:
        log('tcp.log', '  !! db_store_add failed: %r' % (e,))
        return None


def db_init_levgift():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS levgift_got (
        rid INTEGER, days INTEGER, ctime INTEGER,
        PRIMARY KEY (rid, days))""")
    con.commit()
    db_release(con)


def db_get_levgift(rid):
    db_init_levgift()
    con = db_conn()
    rows = {int(r[0]) for r in con.execute(
        'SELECT days FROM levgift_got WHERE rid=?', (rid,))}
    db_release(con)
    return rows


def db_add_levgift(rid, days):
    try:
        db_init_levgift()
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO levgift_got (rid,days,ctime) VALUES (?,?,?)',
                    (rid, int(days), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_add_levgift failed: %r' % (e,))
        return False


# ★★ round44：副本/爬塔进度通用 KV 表
#   为什么新建表而不复用 missions：missions 是任务状态专用（rid+mission_bid），
#   副本/爬塔要存"当前层/剩余次数/章节奖励已领"等异构进度，硬塞会污染任务查询。
#   ptype：'tower_floor'(pkey=tower_id) / 'dung_left'(pkey=dung_bid) /
#          'dung_got'(pkey='{dung_bid}_{ceng}')
def db_dung_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS dungeon_progress (
        rid INTEGER, ptype TEXT, pkey TEXT, value INTEGER,
        PRIMARY KEY (rid, ptype, pkey))""")
    con.commit()
    db_release(con)


def db_dung_get(rid, ptype, pkey, default=0):
    try:
        db_dung_init()
        con = db_conn()
        r = con.execute(
            'SELECT value FROM dungeon_progress WHERE rid=? AND ptype=? AND pkey=?',
            (rid, ptype, str(pkey))).fetchone()
        db_release(con)
        return int(r[0]) if r is not None else int(default)
    except Exception as e:
        log('tcp.log', '  !! db_dung_get failed: %r' % (e,))
        return int(default)


def db_dung_set(rid, ptype, pkey, value):
    try:
        db_dung_init()
        con = db_conn()
        con.execute(
            'INSERT OR REPLACE INTO dungeon_progress (rid,ptype,pkey,value) VALUES (?,?,?,?)',
            (rid, ptype, str(pkey), int(value)))
        con.commit()
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_dung_set failed: %r' % (e,))


def db_dung_list(rid, ptype):
    """列出某类进度的全部 pkey（升序整数）—— R46 用于"已通关层"(`tower_clear`)。"""
    try:
        db_dung_init()
        con = db_conn()
        rows = con.execute('SELECT pkey FROM dungeon_progress WHERE rid=? AND ptype=?',
                           (rid, ptype)).fetchall()
        db_release(con)
        out = []
        for r in rows:
            s = str(r[0]).strip()
            if s.lstrip('-').isdigit():
                out.append(int(s))
        return sorted(out)
    except Exception as e:
        log('tcp.log', '  !! db_dung_list failed: %r' % (e,))
        return []


# ---------------------------------------------------------------------------
# ★★ R47：荣耀竞技场（`113xx` / `trophy_arena_ctrl`）状态与战绩
#   仅存"服务端确实知道"的事实；**没有战斗结果机制时表就是空的**（不编造胜负）。
# ---------------------------------------------------------------------------
def db_arena_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS arena_state (
        rid INTEGER PRIMARY KEY, trophy INTEGER, times INTEGER,
        index_state INTEGER, win_times INTEGER, state INTEGER,
        updated_at INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS arena_record (
        rid INTEGER, seq INTEGER, type INTEGER, opp_rid INTEGER, opp_srv TEXT,
        opp_name TEXT, result INTEGER, trophy INTEGER, is_counterattack INTEGER,
        reply_id TEXT, updated_at INTEGER, PRIMARY KEY (rid, seq))""")
    con.commit()
    db_release(con)


def db_arena_state(rid):
    """竞技场状态；**没有行就返回全 0**（= 没打过，是真话，不是占位）。"""
    st = {'trophy': 0, 'times': 0, 'index_state': 0, 'win_times': 0, 'state': 0}
    try:
        db_arena_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT * FROM arena_state WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                if r[k] is not None:
                    st[k] = int(r[k])
    except Exception as e:
        log('tcp.log', '  !! db_arena_state failed: %r' % (e,))
    return st


def db_arena_records(rid, limit=10):
    """战绩列表（最近在前）。没有战斗结果写入时就是空表。"""
    out = []
    try:
        db_arena_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT * FROM arena_record WHERE rid=? '
                             'ORDER BY seq DESC LIMIT ?', (rid, int(limit))):
            out.append({'type': int(r['type'] or 0), 'rid': int(r['opp_rid'] or 0),
                        'srv_id': r['opp_srv'] or '', 'name': r['opp_name'] or '',
                        'result': int(r['result'] or 0), 'trophy': int(r['trophy'] or 0),
                        'is_counterattack': int(r['is_counterattack'] or 0),
                        'reply_id': r['reply_id'] or ''})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_arena_records failed: %r' % (e,))
    return out


def arena_pk_record_body(recs):
    """`pk_record` 表体（11300 与 11307 共用同一子结构）。"""
    out = w_u16(len(recs))
    for r in recs:
        out += (w_u8(r['type'] & 0xff) + w_u32(r['rid']) + w_str(r['srv_id']) +
                w_str(r['name']) + w_u8(r['result'] & 0xff) +
                w_u32(r['trophy'] & 0xffffffff) +
                w_u8(r['is_counterattack'] & 0xff) + w_str(r['reply_id']))
    return out


def db_arena_opponents(rid, limit=6):
    """★ R47（项目方决策 A）：竞技场对手 = **本服已有角色**（排除自己）。

    全部字段取自真实的 `roles` 行（姓名/等级/职业/性别），
    段位分取各自 `arena_state.trophy`（没打过就是 0）—— **不编造任何数值**。
    单机服下"对手"需要先有第二个角色（R44 的多角色能力）。
    """
    out = []
    try:
        db_arena_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        rows = con.execute(
            'SELECT rid,name,level,career,sex FROM roles WHERE rid<>? '
            'ORDER BY rid LIMIT ?', (rid, int(limit))).fetchall()
        db_release(con)
        for i, r in enumerate(rows):
            o = {'id': (i + 1) & 0xff,            # 挑战用的槽位 id（CS_11302.id:u8）
                 'rid': int(r['rid']), 'srv_id': '1',
                 'name': r['name'] or '', 'lev': int(r['level'] or 1),
                 'career': int(r['career'] or 1), 'sex': int(r['sex'] or 0),
                 'trophy': 0, 'arena_soul': 0}
            try:
                o['trophy'] = int(db_arena_state(o['rid'])['trophy'])
            except Exception:
                pass
            out.append(o)
    except Exception as e:
        log('tcp.log', '  !! db_arena_opponents failed: %r' % (e,))
    return out


def arena_pk_show_body(opps):
    """`pk_show` 表体。`partner_list` 为空表（本服无上阵伙伴数据来源 ⇒ 不编）。"""
    out = w_u16(len(opps))
    for o in opps:
        out += (w_u8(o['id'] & 0xff) + w_u32(o['rid']) + w_str(o['srv_id']) +
                w_str(o['name']) + w_u16(o['lev'] & 0xffff) +
                w_u16(o['career'] & 0xffff) + w_u8(o['sex'] & 0xff) +
                w_u32(o['trophy'] & 0xffffffff) +
                w_u16(0) +                       # partner_list 空表
                w_u8(o['arena_soul'] & 0xff))
    return out


# ---------------------------------------------------------------------------
# ★★ R48：日常活动 / 活跃度（`13781` / `13786`）
#   任务表来源：`config_richang.luac` → `server/_richang.json`
#   （MuMu 截图逐项核对：学院任务 max=10 / 监察任务 50 / 斗魂场 5 /
#     封神之路 999=不限 / 宝图任务 10 / 极地寻宝 1 —— 全部吻合）
#   `SC_13781.huoli_list{id,num,val}` 的 `id` 取 **`huoli_id`**
#   （三方一致：口径类 `.id` == 面板类 `.huoli_id` == huoli_id）。
# ---------------------------------------------------------------------------
_RICHANG = None


def richang_cfg():
    """日常任务表（只读快照；缺失返回空）。"""
    global _RICHANG
    if _RICHANG is None:
        try:
            with open(os.path.join(HERE, '_richang.json'), encoding='utf-8') as f:
                _RICHANG = json.load(f)
        except Exception as e:
            log('tcp.log', '  !! 读取 _richang.json 失败: %r' % (e,))
            _RICHANG = {'tasks': [], 'kezhi': []}
    return _RICHANG


def richang_daily_tasks():
    """`type_name == '日常任务'` 的面板条目（= 客户端日常页显示的那批）。"""
    return [t for t in (richang_cfg().get('tasks') or [])
            if t.get('type_name') == '\u65e5\u5e38\u4efb\u52a1']


_PROMOTE = None


def db_hero_init():
    """★ R86：**伙伴背包**（`SC_10401.hero_bag`）持久化。

    为什么必须持久化：`10401` 原先读 `config.json:heros`（静态 17 个）⇒
    神将兑换（`11216`）拿到的伙伴**无处落脚** ⇒ 伙伴背包看不到、也无法上场。
    列名逐个对应 `hero_bag` 元素字段（`bid/color/lev/exp/state/chip`），**不猜语义**。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_heros (
        rid INTEGER, bid INTEGER, color INTEGER, lev INTEGER, exp INTEGER,
        state INTEGER, chip INTEGER, got_at INTEGER,
        PRIMARY KEY (rid, bid))""")
    con.commit()
    db_release(con)


def db_hero_list(rid, cfg=None):
    """伙伴列表（给 `10401/10402/10403/10404` 用）。

    ★ 首次为空时**从 `config.json:heros` 播种一次** —— 保持原有的 17 个初始伙伴，
      之后一律以 DB 为准（这样兑换/活动新增的伙伴才留得住）。
    """
    try:
        db_hero_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(
            'SELECT bid,color,lev,exp,state,chip FROM role_heros WHERE rid=? '
            'ORDER BY bid', (int(rid),))]
        if not rows and cfg:
            for h in (cfg.get('heros') or []):
                con.execute('INSERT OR REPLACE INTO role_heros '
                            '(rid,bid,color,lev,exp,state,chip,got_at) '
                            'VALUES (?,?,?,?,?,?,?,?)',
                            (int(rid), int(h.get('bid') or 0),
                             int(h.get('color') or 0), int(h.get('lev') or 1),
                             int(h.get('exp') or 0), int(h.get('state') or 0),
                             int(h.get('chip') or 0), int(time.time())))
            con.commit()
            rows = [dict(r) for r in con.execute(
                'SELECT bid,color,lev,exp,state,chip FROM role_heros WHERE rid=? '
                'ORDER BY bid', (int(rid),))]
            if rows:
                log('tcp.log', '  ** role %s heros seeded from config: %d 个'
                    % (rid, len(rows)))
        db_release(con)
        return rows
    except Exception as e:
        log('tcp.log', '  !! db_hero_list failed: %r' % (e,))
        return []


def db_hero_add(rid, bid, color=0, lev=1):
    """把一个伙伴放进伙伴背包（已存在则原样返回，不覆盖已有进度）。★★ R86"""
    try:
        db_hero_init()
        con = db_conn()
        row = con.execute('SELECT bid FROM role_heros WHERE rid=? AND bid=?',
                          (int(rid), int(bid))).fetchone()
        if row is None:
            con.execute('INSERT OR REPLACE INTO role_heros '
                        '(rid,bid,color,lev,exp,state,chip,got_at) VALUES (?,?,?,?,?,?,?,?)',
                        (int(rid), int(bid), int(color), int(lev), 0, 0, 0,
                         int(time.time())))
            con.commit()
            db_release(con)
            return True
        db_release(con)
        return False
    except Exception as e:
        log('tcp.log', '  !! db_hero_add failed: %r' % (e,))
        return False


def partner_def(bid):
    """按 bid 取伙伴配置（`server/_partner_base.json`，53 个）。"""
    try:
        for p in (partner_base_cfg() or []):
            if int(p.get('bid') or 0) == int(bid or 0):
                return p
    except Exception:
        pass
    return {}


def _hero_state(cfg):
    """★ R91：`10401.hero_bag[].state` 的取值（**未取证**）。

    客户端 `hero_data.luac` 里 `state` 是 `HeroData` 的独立字段（`HeroVo` 字段表里没有它），
    由 `changeHeroSatus`/`10414` 那条线维护。我们原先**恒发 0**；
    若客户端以它过滤"可用伙伴"，列表就会空。
    ⇒ 取值放 `config.json: hero_state`（默认 1），**不写死在代码里**：
      改这个值就能一次实验判定"是不是它在过滤"。
    """
    # ★ R98：**对照实验开关优先**（全局 CFG，改完下一次请求即生效、不必重登）
    try:
        _ov = int(CFG.get('hero_state_override', -1))
        if _ov >= 0:
            return _ov & 0xff
    except Exception:
        pass
    try:
        return int(cfg.get('hero_state', 1)) & 0xff
    except Exception:
        return 1


def _attr_data():
    """`server/_attr_data.json`（`config_attr` 提取）：AttrKey2Id / AttrKeyIsShow / AttrPower…"""
    global _ATTR_DATA
    try:
        if _ATTR_DATA is None:
            p = os.path.join(os.path.dirname(HERE), 'server', '_attr_data.json')
            with open(p, encoding='utf-8') as f:
                _ATTR_DATA = json.load(f)
            log('server.log', 'attr data loaded: id2key=%d show=%d'
                % (len(_ATTR_DATA.get('AttrId2Key') or {}),
                   len(_ATTR_DATA.get('AttrKeyIsShow') or {})))
        return _ATTR_DATA
    except Exception as e:
        log('server.log', '!! attr data load failed: %r' % (e,))
        return {}


def _attr_key2id():
    """属性名 → `attr:uint8` id（`AttrKey2Id`）。"""
    try:
        return {str(k): int(v) for k, v in (_attr_data().get('AttrKey2Id') or {}).items()}
    except Exception:
        return {}


def _attr_show_keys():
    """面板上显示的属性名（`AttrKeyIsShow`，10 条）。"""
    try:
        return list((_attr_data().get('AttrKeyIsShow') or {}).keys())
    except Exception:
        return []


_ATTR_DATA = None


def db_form_init():
    """★ R91：**当前选中的阵型**（`14005` 确认后落库，`14000` 读它）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_form (
        rid INTEGER PRIMARY KEY, f_type INTEGER, f_lev INTEGER, updated_at INTEGER)""")
    con.commit()
    db_release(con)


def db_form_get(rid):
    try:
        db_form_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT f_type,f_lev FROM role_form WHERE rid=?',
                          (int(rid),)).fetchone()
        db_release(con)
        return dict(row) if row else None
    except Exception:
        return None


def db_form_set(rid, f_type, f_lev=1):
    try:
        db_form_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_form VALUES (?,?,?,?)',
                    (int(rid), int(f_type), int(f_lev), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_form_set failed: %r' % (e,))
        return False


def db_buff_init():
    """★ R80：角色 buff 列表（`10640`）存储。

    依据：`SC_10640{buff_list: table(caeer:uint8, buff_bid:uint32)}` ——
    元素只有 `(career, buff_bid)`，**没有任何数值字段** ⇒ 这里只存"有哪些 buff"，
    不编造数值列（饱食度这类"当前值"不在本条协议里）。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_buffs (
        rid INTEGER, career INTEGER, buff_bid INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, career, buff_bid))""")
    con.commit()
    db_release(con)


def db_buff_list(rid):
    """返回该角色的 buff 列表（`SC_10640.buff_list` 的元素）。

    ★ R80：**并入"基础 buff"** —— 客户端一直在发 `CS_10640` 而本服原先无应答，
    导致饱食度面板拿不到数据（用户报障"饱食度无法补充"）。

    饱食 buff 的出处（`config_buff_data.luac` 实提取）：
        bid=10009, name='饱食', cli_effect='hunger', type=2, time_type=4,
        desc='每场战斗结束后，会自动消耗一定的饱食度点数,用来恢复上阵单位气血'
    ⇒ 它是**角色固有的基础 buff**（不是靠掉落/道具获得）⇒ 默认下发。
    列表放 `config.json: base_buffs`，可改可清空（**没有写死在代码里**）。
    ⚠ `buff_list` 元素只有 `(career, buff_bid)`、**不带数值** ——
      "当前饱食度点数"不在本条协议里（下一步另找承载它的命令，不编造）。
    """
    try:
        db_buff_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        rows = [dict(r) for r in con.execute(
            'SELECT career,buff_bid FROM role_buffs WHERE rid=? ORDER BY buff_bid',
            (int(rid),))]
        db_release(con)
        have = {(int(r.get('career') or 0), int(r.get('buff_bid') or 0)) for r in rows}
        for b in (cfg_buff_base()):
            k = (int(b.get('career') or 0), int(b.get('buff_bid') or 0))
            if k[1] and k not in have:
                rows.append({'career': k[0], 'buff_bid': k[1]})
                have.add(k)
        return rows
    except Exception as e:
        log('tcp.log', '  !! db_buff_list failed: %r' % (e,))
        return []


def cfg_buff_base():
    """`config.json: base_buffs`（角色固有 buff；默认含饱食 10009）。"""
    try:
        with open(CFG_PATH, encoding='utf-8') as f:
            return json.load(f).get('base_buffs') or []
    except Exception:
        return []


def db_buff_set(rid, career, buff_bid, on=True):
    """加/删一个 buff（实验与管理用；正式"吃东西加 buff"的链路见 10640 处的说明）。"""
    try:
        db_buff_init()
        con = db_conn()
        if on:
            con.execute('INSERT OR REPLACE INTO role_buffs VALUES (?,?,?,?)',
                        (int(rid), int(career), int(buff_bid), int(time.time())))
        else:
            con.execute('DELETE FROM role_buffs WHERE rid=? AND career=? AND buff_bid=?',
                        (int(rid), int(career), int(buff_bid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_buff_set failed: %r' % (e,))
        return False


def db_fabao_del(rid, fid):
    """★ R134：按法宝实例 `id` 删除（`18910` 分解用）。返回是否真的删掉。"""
    try:
        con = db_conn()
        cur = con.execute('DELETE FROM role_fabao WHERE rid=? AND id=?',
                          (int(rid), int(fid)))
        con.commit()
        db_release(con)
        return bool(cur.rowcount)
    except Exception as e:
        log('tcp.log', '  !! db_fabao_del failed: %r' % (e,))
        return False


def db_shenqi_one(rid, sid):
    """★ R133：取一件神器（`role_shenqi`）；没有 ⇒ None。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT sid,lev,star,status,mark FROM role_shenqi '
                        'WHERE rid=? AND sid=?', (int(rid), int(sid))).fetchone()
        db_release(con)
        return dict(r) if r else None
    except Exception as e:
        log('tcp.log', '  !! db_shenqi_one failed: %r' % (e,))
        return None


def db_shenqi_update(rid, sid, lev=None, star=None, status=None, mark=None):
    """★ R133：只更新传入的字段（其余保持）。"""
    try:
        cur = db_shenqi_one(rid, sid)
        if cur is None:
            return False
        con = db_conn()
        con.execute('UPDATE role_shenqi SET lev=?, star=?, status=?, mark=? '
                    'WHERE rid=? AND sid=?',
                    (int(lev if lev is not None else cur['lev']),
                     int(star if star is not None else cur['star']),
                     int(status if status is not None else cur['status']),
                     int(mark if mark is not None else cur['mark']),
                     int(rid), int(sid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_shenqi_update failed: %r' % (e,))
        return False


def db_shenqi_use_only(rid, sid):
    """★ R133：把 `sid` 设为"使用中"（`status=1`），其余神器 `status=0`。"""
    try:
        con = db_conn()
        con.execute('UPDATE role_shenqi SET status=0 WHERE rid=?', (int(rid),))
        con.execute('UPDATE role_shenqi SET status=1 WHERE rid=? AND sid=?',
                    (int(rid), int(sid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_shenqi_use_only failed: %r' % (e,))
        return False


def db_fabao_one(rid, bid):
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT id,bid,level,exp,stage,pos,effect_level FROM role_fabao '
                        'WHERE rid=? AND bid=?', (int(rid), int(bid))).fetchone()
        db_release(con)
        return dict(r) if r else None
    except Exception as e:
        log('tcp.log', '  !! db_fabao_one failed: %r' % (e,))
        return None


def db_fabao_update(rid, bid, level=None, pos=None, stage=None):
    """★ R133：只更新传入的字段。"""
    try:
        cur = db_fabao_one(rid, bid)
        if cur is None:
            return False
        con = db_conn()
        con.execute('UPDATE role_fabao SET level=?, pos=?, stage=? '
                    'WHERE rid=? AND bid=?',
                    (int(level if level is not None else cur['level']),
                     int(pos if pos is not None else cur['pos']),
                     int(stage if stage is not None else cur['stage']),
                     int(rid), int(bid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_fabao_update failed: %r' % (e,))
        return False


def wing_upstar_seq():
    """★ R132：翅膀升级的 `wing_id` 档位序列（来自 `config_wing_data.WingUpstar`）。

    取不到 ⇒ 空列表（调用方据此保守处理）。
    """
    global _WING_SEQ
    try:
        if _WING_SEQ is None:
            import os as _os
            p = _os.path.join(_os.path.dirname(HERE), 'server', 'cfg', 'config_wing_data.json')
            with open(p, encoding='utf-8') as f:
                d = json.load(f)
            # ★★ R132b：档位序列取自 **`WingHHCost` 的键**（1..8，每项有 `color`），
            #   不是 `WingUpstar` —— 后者的键 101/102 是「外观组 id」、内层是星级。
            hc = d.get('WingHHCost') or {}
            seq = [int(k) for k in hc.keys() if str(k).isdigit()]
            _WING_SEQ = sorted(set(seq)) or []
            log('server.log', 'wing upstar seq: %s' % _WING_SEQ[:8])
        return _WING_SEQ
    except Exception as e:
        log('server.log', '!! wing_upstar_seq failed: %r' % (e,))
        return []


_WING_SEQ = None


def db_fabao_list(rid):
    """★ R131：法宝持有（`18900` 的数据源）。

    表列逐个对应协议语义：`id/bid/level/exp/stage/pos/effect_level`。
    没有行 ⇒ 空（= 没有法宝，真话）。
    """
    out = []
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_fabao (
            rid INTEGER, id INTEGER, bid INTEGER, level INTEGER, exp INTEGER,
            stage INTEGER, pos INTEGER, effect_level INTEGER,
            PRIMARY KEY (rid, id))""")
        con.commit()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT id,bid,level,exp,stage,pos,effect_level '
                             'FROM role_fabao WHERE rid=? ORDER BY id', (int(rid),)):
            out.append({'id': int(r['id']), 'bid': int(r['bid']),
                        'level': int(r['level'] or 0), 'exp': int(r['exp'] or 0),
                        'stage': int(r['stage'] or 0), 'pos': int(r['pos'] or 0),
                        'effect_level': int(r['effect_level'] or 0)})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_fabao_list failed: %r' % (e,))
    return out


def db_fabao_add(rid, fid, bid, level=1, stage=0):
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_fabao (
            rid INTEGER, id INTEGER, bid INTEGER, level INTEGER, exp INTEGER,
            stage INTEGER, pos INTEGER, effect_level INTEGER,
            PRIMARY KEY (rid, id))""")
        con.execute('INSERT OR REPLACE INTO role_fabao VALUES (?,?,?,?,?,?,?,?)',
                    (int(rid), int(fid), int(bid), int(level), 0, int(stage), 0, 0))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_fabao_add failed: %r' % (e,))
        return False


def self_rank_row(cfg=None):
    """★ R130：本服**唯一的角色**作为"排行榜第 1 名"的那一行（各榜通用）。

    返回 `dict(rid, name, sex, career, lev, power)`。
    —— **这是"榜上有我"的正确表达**：本服只有 1 个角色，它的名次就是 **1**
    （不是"空表"，空表会让客户端显示"你不在榜上"）。
    """
    try:
        rs = role_state(cfg or {})
        try:
            pw = int(role_power(cfg) or 0)
        except Exception:
            pw = 0
        return {'rid': int(rs.get('rid') or 1001),
                'name': str(rs.get('name') or ''),
                'sex': int(rs.get('sex') or 0),
                'career': int(rs.get('career') or 0),
                'lev': int(rs.get('lev') or 1),
                'power': pw}
    except Exception as e:
        log('tcp.log', '  !! self_rank_row failed: %r' % (e,))
        return {'rid': 1001, 'name': '', 'sex': 0, 'career': 0, 'lev': 1, 'power': 0}


def boss_cfg():
    """★ R129：BOSS 配置（`config_boss.Boss`，27 项）。"""
    global _BOSS_CFG
    try:
        if _BOSS_CFG is None:
            import os as _os
            p = _os.path.join(_os.path.dirname(HERE), 'server', 'cfg', 'config_boss.json')
            with open(p, encoding='utf-8') as f:
                _BOSS_CFG = (json.load(f).get('Boss') or {})
            log('server.log', 'boss cfg loaded: %d 条' % len(_BOSS_CFG))
        return _BOSS_CFG
    except Exception as e:
        log('server.log', '!! boss cfg load failed: %r' % (e,))
        return {}


def boss_rows(rid):
    """`[(mon_bid, kill, map_bid), …]` —— 来自配置 27 项 + 玩家的击杀表。

    `kill` = 该 BOSS 是否击杀过（`role_boss_kill`）；没有行 ⇒ 0（真话）。
    `x`/`y`/`left_time`/`award` 配置无源 ⇒ 由调用方补 0。
    """
    out = []
    killed = set()
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_boss_kill ('
                    'rid INTEGER, mon_bid INTEGER, ctime INTEGER, PRIMARY KEY (rid, mon_bid))')
        con.commit()
        for r in con.execute('SELECT mon_bid FROM role_boss_kill WHERE rid=?', (int(rid),)):
            killed.add(int(r[0]))
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! boss_rows(kill) failed: %r' % (e,))
    try:
        for k, v in boss_cfg().items():
            h = _h(v)
            mb = int(h.get('boss_id') or 0)
            if not mb:
                continue
            out.append((mb, 1 if mb in killed else 0, int(h.get('map_bid') or 0)))
    except Exception as e:
        log('tcp.log', '  !! boss_rows failed: %r' % (e,))
    return sorted(out)


def db_title_add(rid, bid):
    """★ R129：称号拥有记录（`config_title.Title` 175 项）。"""
    try:
        con = db_conn()
        con.execute('CREATE TABLE IF NOT EXISTS role_title ('
                    'rid INTEGER, bid INTEGER, ctime INTEGER, PRIMARY KEY (rid, bid))')
        con.execute('INSERT OR REPLACE INTO role_title VALUES (?,?,?)',
                    (int(rid), int(bid), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_title_add failed: %r' % (e,))
        return False


_BOSS_CFG = None


def lingshou_cfg():
    """★ R127：魂兽配置（`config_lingshou`）。"""
    global _LS_CFG
    try:
        if _LS_CFG is None:
            import os as _os
            p = _os.path.join(_os.path.dirname(HERE), 'server', 'cfg', 'config_lingshou.json')
            with open(p, encoding='utf-8') as f:
                _LS_CFG = json.load(f)
            log('server.log', 'lingshou cfg loaded: %s' % list(_LS_CFG.keys()))
        return _LS_CFG
    except Exception as e:
        log('server.log', '!! lingshou cfg load failed: %r' % (e,))
        return {}


# `SC_15801.attr_list` 的**字段顺序**（严格按 spec 抄）—— 注意第 6 个是 `atk_speed`
LS_ATTR_ORDER = ['atk_s', 'atk_p', 'def_s', 'def_p', 'hp_max', 'atk_speed',
                 'tenacity', 'hit', 'dodge', 'crit', 'red_def_s', 'red_def_p']


def _h(v):
    """解构结果里"具名表"是 `{"array":[], "hash":{…}}` ⇒ 取内层。"""
    if isinstance(v, dict) and 'hash' in v and isinstance(v['hash'], dict):
        return v['hash']
    return v if isinstance(v, dict) else {}


def lingshou_attr_values(lev):
    """按 **spec 的字段名**去 `LingshouLevAttr[lev].attr` 取 12 个值。

    ★ 必须**按名字**取：配置的键顺序与 spec 完全不同（配置有 `atk_abs`/`def_abs`，
      spec 要 `dodge`/`crit`）⇒ 按位置取会张冠李戴。
    取不到的键 ⇒ 0（诚实）。
    """
    if not lev:
        return [0] * len(LS_ATTR_ORDER)
    try:
        row = _h((lingshou_cfg().get('LingshouLevAttr') or {}).get(str(lev)))
        at = _h(row.get('attr')) if row else {}
        return [int(at.get(k) or 0) & 0xffffffff for k in LS_ATTR_ORDER]
    except Exception as e:
        log('tcp.log', '  !! lingshou_attr_values failed: %r' % (e,))
        return [0] * len(LS_ATTR_ORDER)


def lingshou_skills():
    try:
        arr = lingshou_cfg().get('LingshouAllSkill') or []
        return [int(x) for x in arr if isinstance(x, (int, float)) and x]
    except Exception:
        return []


def db_lingshou_state(rid):
    """魂兽状态（`15801`）。没有行 ⇒ 全 0（= 没有魂兽，真话）。"""
    st = {'jie': 0, 'lev': 0, 'jie_luck': 0, 'grow': 0, 'zz': 0, 'face': 0, 'use': 0}
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_lingshou (
            rid INTEGER PRIMARY KEY, jie INTEGER, lev INTEGER, jie_luck INTEGER,
            grow INTEGER, zz INTEGER, face INTEGER, use INTEGER, updated_at INTEGER)""")
        con.commit()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT jie,lev,jie_luck,grow,zz,face,use FROM role_lingshou '
                        'WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                st[k] = int(r[k] or 0)
    except Exception as e:
        log('tcp.log', '  !! db_lingshou_state failed: %r' % (e,))
    return st


def db_lingshou_set(rid, jie, lev=1):
    try:
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_lingshou VALUES (?,?,?,?,?,?,?,?,?)',
                    (int(rid), int(jie), int(lev), 0, 0, 0, 0, 0, int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_lingshou_set failed: %r' % (e,))
        return False


def db_yuanshen_state(rid):
    """元神状态（`19406`）。没有行 ⇒ 0（真话）。"""
    st = {'soul': 0, 'soul_max': 0}
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_yuanshen (
            rid INTEGER PRIMARY KEY, soul INTEGER, soul_max INTEGER, updated_at INTEGER)""")
        con.commit()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT soul,soul_max FROM role_yuanshen WHERE rid=?',
                        (int(rid),)).fetchone()
        db_release(con)
        if r is not None:
            st['soul'] = int(r['soul'] or 0)
            st['soul_max'] = int(r['soul_max'] or 0)
    except Exception as e:
        log('tcp.log', '  !! db_yuanshen_state failed: %r' % (e,))
    return st


def db_yuanshen_set(rid, soul, soul_max):
    try:
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_yuanshen VALUES (?,?,?,?)',
                    (int(rid), int(soul), int(soul_max), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_yuanshen_set failed: %r' % (e,))
        return False


_LS_CFG = None


def db_shenqi_init():
    """★ R126：神器持有（`15700` 的数据源）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_shenqi (
        rid INTEGER, sid INTEGER, lev INTEGER, star INTEGER, status INTEGER,
        mark INTEGER, updated_at INTEGER, PRIMARY KEY (rid, sid))""")
    con.commit()
    db_release(con)


def db_shenqi_list(rid):
    """该角色的神器列表 `[{id,lev,star,status,mark}, …]`（没有 ⇒ 空）。"""
    out = []
    try:
        db_shenqi_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT sid,lev,star,status,mark FROM role_shenqi '
                             'WHERE rid=? ORDER BY sid', (int(rid),)):
            out.append({'id': int(r['sid']), 'lev': int(r['lev'] or 0),
                        'star': int(r['star'] or 0), 'status': int(r['status'] or 0),
                        'mark': int(r['mark'] or 0)})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_shenqi_list failed: %r' % (e,))
    return out


def db_shenqi_set(rid, sid, lev=1, star=0):
    try:
        db_shenqi_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_shenqi VALUES (?,?,?,?,?,?,?)',
                    (int(rid), int(sid), int(lev), int(star), 1, 0, int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_shenqi_set failed: %r' % (e,))
        return False


def db_mingge_init():
    """★ R126：命格持有（`19400.mingge_list` 的数据源）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_mingge (
        rid INTEGER, bid INTEGER, lev INTEGER, quantity INTEGER, hero_bid INTEGER,
        ctime INTEGER, PRIMARY KEY (rid, bid))""")
    con.commit()
    db_release(con)


def db_mingge_list(rid):
    """该角色的命格列表（没有 ⇒ 空）。"""
    out = []
    try:
        db_mingge_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT bid,lev,quantity,hero_bid,ctime FROM role_mingge '
                             'WHERE rid=? ORDER BY bid', (int(rid),)):
            out.append({'bid': int(r['bid']), 'lev': int(r['lev'] or 1),
                        'quantity': int(r['quantity'] or 1),
                        'hero_bid': int(r['hero_bid'] or 0),
                        'ctime': int(r['ctime'] or 0)})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_mingge_list failed: %r' % (e,))
    return out


def db_mingge_add(rid, bid, lev=1):
    try:
        db_mingge_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_mingge VALUES (?,?,?,?,?,?)',
                    (int(rid), int(bid), int(lev), 1, 0, int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_mingge_add failed: %r' % (e,))
        return False


def db_chair_state(rid):
    """★ R125：座椅状态（`20800` 的数据源）。没有行 ⇒ 全 0（= 没有座椅，真话）。"""
    st = {'stage': 0, 'power': 0, 'luck': 0, 'res_stage': 0, 'grow': 0}
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_chair (
            rid INTEGER PRIMARY KEY, stage INTEGER, power INTEGER, luck INTEGER,
            res_stage INTEGER, grow INTEGER, updated_at INTEGER)""")
        con.commit()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT stage,power,luck,res_stage,grow FROM role_chair '
                        'WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                st[k] = int(r[k] or 0)
    except Exception as e:
        log('tcp.log', '  !! db_chair_state failed: %r' % (e,))
    return st


def db_chair_set(rid, stage, power=0, luck=0, res_stage=0, grow=0):
    try:
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_chair VALUES (?,?,?,?,?,?,?)',
                    (int(rid), int(stage), int(power), int(luck), int(res_stage),
                     int(grow), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_chair_set failed: %r' % (e,))
        return False


def db_wing_state(rid):
    """★ R125：翅膀状态（`11600` 的数据源）。没有行 ⇒ 全 0（真话）。"""
    st = {'color': 0, 'wing_id': 0, 'power': 0, 'star': 0}
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_wing (
            rid INTEGER PRIMARY KEY, color INTEGER, wing_id INTEGER,
            power INTEGER, star INTEGER, updated_at INTEGER)""")
        con.commit()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT color,wing_id,power,star FROM role_wing WHERE rid=?',
                        (int(rid),)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                st[k] = int(r[k] or 0)
    except Exception as e:
        log('tcp.log', '  !! db_wing_state failed: %r' % (e,))
    return st


def db_wing_set(rid, wing_id, star=0, color=0, power=0):
    try:
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_wing VALUES (?,?,?,?,?,?)',
                    (int(rid), int(color), int(wing_id), int(power), int(star),
                     int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_wing_set failed: %r' % (e,))
        return False


def db_moment_add(rid, content):
    """★ R122：朋友圈发帖（`13359`）—— **真的存下来**。"""
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_moments (
            rid INTEGER, content TEXT, ctime INTEGER)""")
        con.execute('INSERT INTO role_moments VALUES (?,?,?)',
                    (int(rid), str(content), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_moment_add failed: %r' % (e,))
        return False


def db_chat_add(rid, channel, msg):
    """★ R122：频道发言（`12762`）—— **真的存下来**。"""
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_chat (
            rid INTEGER, channel INTEGER, msg TEXT, ctime INTEGER)""")
        con.execute('INSERT INTO role_chat VALUES (?,?,?,?)',
                    (int(rid), int(channel), str(msg), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_chat_add failed: %r' % (e,))
        return False


def db_has_guild(rid):
    """该角色有没有宗门（`30201` 的门槛）—— 读 R121 建的 `role_guild`。"""
    try:
        db_guild_init()
        con = db_conn()
        r = con.execute('SELECT name FROM role_guild WHERE rid=?',
                        (int(rid),)).fetchone()
        db_release(con)
        return bool(r and r[0])
    except Exception:
        return False


def db_guild_init():
    """★ R121：宗门（`13500` 建宗门用）。本服只有 1 个角色 ⇒ 建完就是"1 人宗门"。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_guild (
        rid INTEGER PRIMARY KEY, name TEXT, ctime INTEGER)""")
    con.commit()
    db_release(con)


def db_guild_create(rid, name):
    """建宗门。返回 `(ok, msg)`：空名/重名/已有宗门都拒绝。"""
    try:
        db_guild_init()
        con = db_conn()
        if con.execute('SELECT name FROM role_guild WHERE rid=?',
                       (int(rid),)).fetchone():
            db_release(con)
            return False, '已经创建过宗门'
        if con.execute('SELECT name FROM role_guild WHERE name=?',
                       (str(name),)).fetchone():
            db_release(con)
            return False, '宗门名已被占用'
        con.execute('INSERT OR REPLACE INTO role_guild VALUES (?,?,?)',
                    (int(rid), str(name), int(time.time())))
        con.commit()
        db_release(con)
        return True, ''
    except Exception as e:
        log('tcp.log', '  !! db_guild_create failed: %r' % (e,))
        return False, '创建失败'


# ==================== 组队（132xx）—— PHASE 2 ====================
# 说明（证据纪律）：本服的 `role_team` 是**兼容层**，不是原版表结构。
#   原版队伍数据在服务端内存/专用库里，APK 无从取证其表结构 ⇒ 本表标 INFERENCE。
#   协议字段（13200/13201/13210/13218/13226/13237 的 CS/SC）来自
#   `protocol/fields.json`（cmd_resolve_132.luac）⇒ 字段级 CONFIRMED。
def db_team_init():
    """组队表。成员用 JSON 文本存（本服规模小，够用）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_team (
        team_id INTEGER PRIMARY KEY, leader_rid INTEGER, leader_srv TEXT,
        members TEXT, ctime INTEGER)""")
    con.commit()
    db_release(con)


def _team_members(raw):
    try:
        m = json.loads(raw or '[]')
        return m if isinstance(m, list) else []
    except Exception:
        return []


def _team_row(r):
    return {'team_id': int(r[0]), 'leader_rid': int(r[1]), 'leader_srv': r[2] or '',
            'members': _team_members(r[3]), 'ctime': int(r[4] or 0)}


def db_team_get(team_id):
    db_team_init()
    con = db_conn()
    r = con.execute('SELECT team_id,leader_rid,leader_srv,members,ctime '
                    'FROM role_team WHERE team_id=?', (int(team_id),)).fetchone()
    db_release(con)
    return _team_row(r) if r else None


def db_team_of(rid):
    """返回 rid 所在队伍 dict，或 None。"""
    db_team_init()
    con = db_conn()
    rows = con.execute('SELECT team_id,leader_rid,leader_srv,members,ctime '
                       'FROM role_team').fetchall()
    db_release(con)
    for r in rows:
        if any(int(m.get('rid') or 0) == int(rid) for m in _team_members(r[3])):
            return _team_row(r)
    return None


def db_team_save(team):
    db_team_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_team VALUES (?,?,?,?,?)',
                (int(team['team_id']), int(team['leader_rid']),
                 str(team.get('leader_srv') or ''),
                 json.dumps(team['members'], ensure_ascii=False),
                 int(team.get('ctime') or time.time())))
    con.commit()
    db_release(con)


def db_team_delete(team_id):
    db_team_init()
    con = db_conn()
    con.execute('DELETE FROM role_team WHERE team_id=?', (int(team_id),))
    con.commit()
    db_release(con)


def db_team_create(rid, name='', srv='', lev=1, career=0, sex=0, power=0):
    """建队。已在队中 ⇒ 拒绝。返回 (ok, msg, team)。"""
    if db_team_of(rid) is not None:
        return False, '已在队伍中', None
    db_team_init()
    con = db_conn()
    row = con.execute('SELECT MAX(team_id) FROM role_team').fetchone()
    db_release(con)
    tid = int((row and row[0]) or 1000) + 1
    team = {'team_id': tid, 'leader_rid': int(rid), 'leader_srv': str(srv or ''),
            'members': [{'rid': int(rid), 'srv': str(srv or ''), 'name': str(name or ''),
                         'lev': int(lev), 'career': int(career), 'sex': int(sex),
                         'power': int(power)}],
            'ctime': int(time.time())}
    db_team_save(team)
    return True, '', team


def db_team_leave(rid):
    """离队。队长离队 ⇒ 移交给下一位；最后一人离队 ⇒ 解散。返回 (ok,msg)。"""
    team = db_team_of(rid)
    if team is None:
        return False, '不在队伍中'
    team['members'] = [m for m in team['members'] if int(m.get('rid') or 0) != int(rid)]
    if not team['members']:
        db_team_delete(team['team_id'])
        return True, ''
    if int(team['leader_rid']) == int(rid):
        team['leader_rid'] = int(team['members'][0]['rid'])
        team['leader_srv'] = str(team['members'][0].get('srv') or '')
    db_team_save(team)
    return True, ''


def db_team_disband(rid):
    """解散（仅队长）。返回 (ok,msg)。"""
    team = db_team_of(rid)
    if team is None:
        return False, '不在队伍中'
    if int(team['leader_rid']) != int(rid):
        return False, '只有队长可以解散队伍'
    db_team_delete(team['team_id'])
    return True, ''


def db_team_hall(limit=50):
    """组队大厅：所有队伍（新→旧）。"""
    db_team_init()
    con = db_conn()
    rows = con.execute('SELECT team_id,leader_rid,leader_srv,members,ctime '
                       'FROM role_team ORDER BY team_id DESC LIMIT ?',
                       (int(limit),)).fetchall()
    db_release(con)
    return [_team_row(r) for r in rows]


def db_team_invite_init():
    """组队邀请（PHASE2.4）：队长邀请某玩家入队，待对方 13204 应答。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_team_invite (
        invite_id INTEGER PRIMARY KEY AUTOINCREMENT, team_id INTEGER, from_rid INTEGER,
        to_rid INTEGER, ctime INTEGER)""")
    con.commit()
    db_release(con)


def db_team_invite_add(team_id, from_rid, to_rid):
    db_team_invite_init()
    con = db_conn()
    con.execute('DELETE FROM role_team_invite WHERE team_id=? AND to_rid=?',
                (int(team_id), int(to_rid)))
    con.execute('INSERT INTO role_team_invite (team_id,from_rid,to_rid,ctime) VALUES (?,?,?,?)',
                (int(team_id), int(from_rid), int(to_rid), int(time.time())))
    con.commit()
    db_release(con)


def db_team_invite_of(to_rid):
    db_team_invite_init()
    con = db_conn()
    r = con.execute('SELECT invite_id,team_id,from_rid,to_rid,ctime FROM role_team_invite '
                    'WHERE to_rid=? ORDER BY invite_id DESC LIMIT 1', (int(to_rid),)).fetchone()
    db_release(con)
    if not r:
        return None
    return {'invite_id': r[0], 'team_id': r[1], 'from_rid': r[2], 'to_rid': r[3], 'ctime': r[4]}


def db_team_invite_del(invite_id):
    db_team_invite_init()
    con = db_conn()
    con.execute('DELETE FROM role_team_invite WHERE invite_id=?', (int(invite_id),))
    con.commit()
    db_release(con)


def db_team_add_member(team_id, member):
    """把成员加进队伍（去重）。返回 (ok,msg)。"""
    team = db_team_get(team_id)
    if team is None:
        return False, '队伍不存在'
    rid = int(member.get('rid') or 0)
    if any(int(m.get('rid') or 0) == rid for m in team['members']):
        return False, '已在队伍中'
    if len(team['members']) >= 4:
        return False, '队伍已满'
    team['members'].append(member)
    db_team_save(team)
    return True, ''


# ==================== 结拜 / 金兰（195xx）—— PHASE 2 ====================
# 证据纪律：协议字段来自 `protocol/fields.json`（`cmd_resolve_195.luac`）⇒ CONFIRMED。
#   原版结拜数据表结构不可取证 ⇒ `role_jiebai` 为**兼容层，INFERENCE**。
def db_jiebai_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_jiebai (
        jid INTEGER PRIMARY KEY, leader_rid INTEGER, front_name TEXT, end_name TEXT,
        lev INTEGER, exp INTEGER, notice TEXT, members TEXT, ctime INTEGER)""")
    con.commit()
    db_release(con)


def _jb_row(r):
    try:
        mem = json.loads(r[7] or '[]')
        if not isinstance(mem, list):
            mem = []
    except Exception:
        mem = []
    return {'jid': int(r[0]), 'leader_rid': int(r[1]), 'front_name': r[2] or '',
            'end_name': r[3] or '', 'lev': int(r[4] or 1), 'exp': int(r[5] or 0),
            'notice': r[6] or '', 'members': mem, 'ctime': int(r[8] or 0)}


def db_jiebai_of(rid):
    """返回 rid 所在结拜 dict，或 None。"""
    db_jiebai_init()
    con = db_conn()
    rows = con.execute('SELECT jid,leader_rid,front_name,end_name,lev,exp,notice,members,ctime '
                       'FROM role_jiebai').fetchall()
    db_release(con)
    for r in rows:
        if any(int(m.get('rid') or 0) == int(rid) for m in _jb_row(r)['members']):
            return _jb_row(r)
    return None


def db_jiebai_get(jid):
    db_jiebai_init()
    con = db_conn()
    r = con.execute('SELECT jid,leader_rid,front_name,end_name,lev,exp,notice,members,ctime '
                    'FROM role_jiebai WHERE jid=?', (int(jid),)).fetchone()
    db_release(con)
    return _jb_row(r) if r else None


def db_jiebai_save(jb):
    db_jiebai_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_jiebai VALUES (?,?,?,?,?,?,?,?,?)',
                (int(jb['jid']), int(jb['leader_rid']), str(jb.get('front_name') or ''),
                 str(jb.get('end_name') or ''), int(jb.get('lev') or 1),
                 int(jb.get('exp') or 0), str(jb.get('notice') or ''),
                 json.dumps(jb.get('members') or [], ensure_ascii=False),
                 int(jb.get('ctime') or time.time())))
    con.commit()
    db_release(con)


def db_jiebai_delete(jid):
    db_jiebai_init()
    con = db_conn()
    con.execute('DELETE FROM role_jiebai WHERE jid=?', (int(jid),))
    con.commit()
    db_release(con)


def db_jiebai_create(rid, name='', srv='', lev=1, career=0, sex=0, power=0):
    """发起结拜（本服为单人发起）。已在结拜 ⇒ 拒绝。返回 (ok,msg,jb)。"""
    if db_jiebai_of(rid) is not None:
        return False, '已经结拜过了', None
    db_jiebai_init()
    con = db_conn()
    row = con.execute('SELECT MAX(jid) FROM role_jiebai').fetchone()
    db_release(con)
    jid = int((row and row[0]) or 2000) + 1
    jb = {'jid': jid, 'leader_rid': int(rid), 'front_name': '金兰', 'end_name': '之谊',
          'lev': 1, 'exp': 0, 'notice': '',
          'members': [{'rid': int(rid), 'srv': str(srv or ''), 'name': str(name or ''),
                       'sort': 1, 'sex': int(sex) & 0xff, 'career': int(career) & 0xff,
                       'second_name': str(name or ''), 'trophy': 0, 'lev': int(lev) & 0xff,
                       'jieyi': 0, 'jieyi_total': 0, 'is_leader': 1, 'confirm': 1}],
          'ctime': int(time.time())}
    db_jiebai_save(jb)
    return True, '', jb


def db_jiebai_cancel(rid):
    jb = db_jiebai_of(rid)
    if jb is None:
        return False, '尚未结拜'
    db_jiebai_delete(jb['jid'])
    return True, ''


def db_jiebai_add_member(jid, member):
    """加成员（待确认 confirm=0）。返回 (ok,msg)。"""
    jb = db_jiebai_get(jid)
    if jb is None:
        return False, '结拜不存在'
    rid = int(member.get('rid') or 0)
    if any(int(m.get('rid') or 0) == rid for m in jb['members']):
        return False, '已在结拜中'
    if len(jb['members']) >= 6:
        return False, '结拜人数已满'
    m = dict(member)
    m['confirm'] = 0
    jb['members'].append(m)
    db_jiebai_save(jb)
    return True, ''


def db_jiebai_set_confirm(jid, rid, val):
    jb = db_jiebai_get(jid)
    if jb is None:
        return False, '结拜不存在'
    found = False
    for m in jb['members']:
        if int(m.get('rid') or 0) == int(rid):
            m['confirm'] = int(val)
            found = True
            break
    if found:
        db_jiebai_save(jb)
    return found, ('' if found else '成员不存在')


def db_jiebai_all_confirmed(jb):
    return bool(jb) and all(int(m.get('confirm') or 0) == 1 for m in jb['members'])


# ==================== 结婚 / 夫妻（183xx）—— PHASE 2 ====================
# 证据纪律：协议字段来自 `protocol/fields.json`（`cmd_resolve_183.luac`）⇒ CONFIRMED。
#   原版婚姻表结构不可取证 ⇒ `role_marry` 为**兼容层，INFERENCE**。
#   ⚠ 本服当前**单角色**：求婚/应答需要第二角色 ⇒ `18300` 只能诚实失败；
#     婚姻状态的读取/离婚/婚戒进阶等**单角色可服务**的命令本层已实现，
#     并可由测试夹具（直接写行）驱动，见 tools/test_marry.py。
#   state: 0=未婚 1=已婚 2=离婚中
def db_marry_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_marry (
        rid INTEGER PRIMARY KEY, spouse_rid INTEGER, spouse_name TEXT, state INTEGER,
        marry_time INTEGER, ring_lev INTEGER, ring_skill INTEGER, qifen INTEGER)""")
    con.commit()
    db_release(con)


def db_marry_get(rid):
    """返回 {state,spouse_rid,spouse_name,ring_lev,ring_skill,qifen}；无行 ⇒ state=0。"""
    db_marry_init()
    con = db_conn()
    r = con.execute('SELECT rid,spouse_rid,spouse_name,state,marry_time,ring_lev,ring_skill,qifen '
                    'FROM role_marry WHERE rid=?', (int(rid),)).fetchone()
    db_release(con)
    if not r:
        return {'rid': int(rid), 'state': 0, 'spouse_rid': 0, 'spouse_name': '',
                'marry_time': 0, 'ring_lev': 0, 'ring_skill': 0, 'qifen': 0}
    return {'rid': int(r[0]), 'spouse_rid': int(r[1] or 0), 'spouse_name': r[2] or '',
            'state': int(r[3] or 0), 'marry_time': int(r[4] or 0),
            'ring_lev': int(r[5] or 0), 'ring_skill': int(r[6] or 0), 'qifen': int(r[7] or 0)}


def db_marry_save(m):
    db_marry_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_marry VALUES (?,?,?,?,?,?,?,?)',
                (int(m['rid']), int(m.get('spouse_rid') or 0), str(m.get('spouse_name') or ''),
                 int(m.get('state') or 0), int(m.get('marry_time') or 0),
                 int(m.get('ring_lev') or 0), int(m.get('ring_skill') or 0),
                 int(m.get('qifen') or 0)))
    con.commit()
    db_release(con)


def db_marry_set(rid, spouse_rid, spouse_name, state=1):
    """建立/覆盖婚姻状态（供测试夹具与 GM 使用，不做第二角色校验）。"""
    m = db_marry_get(rid)
    m.update({'spouse_rid': int(spouse_rid), 'spouse_name': str(spouse_name),
              'state': int(state), 'marry_time': int(time.time())})
    db_marry_save(m)
    return m


def db_marry_divorce(rid):
    """离婚落定：清空婚姻状态（保留 rid 行，state=0）。"""
    m = db_marry_get(rid)
    m.update({'spouse_rid': 0, 'spouse_name': '', 'state': 0, 'marry_time': 0})
    db_marry_save(m)
    return m


def db_marry_propose_init():
    """求婚意向（PHASE2.5）。

    ★ 证据说明：`CS_18300`（发起求婚）在 `cmd_resolve_183.luac` 里是**空消息**
      —— 客户端**不上传求婚对象**；`SC_18301{...obj_rid,obj_srv}` 才把发起者告诉被求婚者。
      ⇒ **"服务端如何确定求婚对象"在客户端侧无证据**（已核 `wedding_ctrl/model` 反汇编）。
      本实现不编造该机制，而是把它收敛为一张**明确的服务端意向表**：由服务端自己的
      选取逻辑（或 GM/测试）写入 `role_marry_propose`，`18300` 只负责**确认并发起**。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_marry_propose (
        from_rid INTEGER PRIMARY KEY, to_rid INTEGER, ctime INTEGER)""")
    con.commit()
    db_release(con)


def db_marry_propose_set(from_rid, to_rid):
    db_marry_propose_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_marry_propose VALUES (?,?,?)',
                (int(from_rid), int(to_rid), int(time.time())))
    con.commit()
    db_release(con)


def db_marry_propose_get(from_rid):
    db_marry_propose_init()
    con = db_conn()
    r = con.execute('SELECT from_rid,to_rid,ctime FROM role_marry_propose WHERE from_rid=?',
                    (int(from_rid),)).fetchone()
    db_release(con)
    return {'from_rid': r[0], 'to_rid': r[1], 'ctime': r[2]} if r else None


def db_marry_propose_of_target(to_rid):
    """谁在向我求婚（取最新一条）。"""
    db_marry_propose_init()
    con = db_conn()
    r = con.execute('SELECT from_rid,to_rid,ctime FROM role_marry_propose WHERE to_rid=? '
                    'ORDER BY ctime DESC LIMIT 1', (int(to_rid),)).fetchone()
    db_release(con)
    return {'from_rid': r[0], 'to_rid': r[1], 'ctime': r[2]} if r else None


def db_marry_propose_del(from_rid):
    db_marry_propose_init()
    con = db_conn()
    con.execute('DELETE FROM role_marry_propose WHERE from_rid=?', (int(from_rid),))
    con.commit()
    db_release(con)


# ==================== 时装（10573-10578）—— PHASE 2.7 ====================
# 证据：协议字段来自 `protocol/fields.json`（`cmd_resolve_105.luac`）⇒ CONFIRMED；
#   时装数据取自 `server/cfg_kconfig/config_fashion.json`（原版配置）⇒ CONFIRMED；
#   `role_fashion` 为兼容层（原版时装表不可取证）⇒ INFERENCE。
#   ★ `CS_10574/10575/10576` 的字段名是 `id`（SC 亦回 `id`）；时装无实例概念，
#     故 `id` 按 **bid** 处理。
def db_fashion_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_fashion (
        rid INTEGER, bid INTEGER, active INTEGER, worn INTEGER, star INTEGER,
        expire INTEGER, ctime INTEGER, PRIMARY KEY (rid, bid))""")
    con.commit()
    db_release(con)


def fashion_def(bid):
    """返回时装配置行；不是有效时装 ⇒ None（用于**拒绝无效 bid**）。"""
    try:
        rows = (kcfg('config_fashion') or {}).get('rows') or {}
        r = rows.get(str(int(bid)))
        if isinstance(r, dict) and (r.get('name') or r.get('animate_id_male')
                                    or r.get('animate_id_female')):
            return r
    except Exception:
        pass
    return None


def db_fashion_rows(rid):
    db_fashion_init()
    con = db_conn()
    rows = con.execute('SELECT rid,bid,active,worn,star,expire,ctime FROM role_fashion '
                       'WHERE rid=? ORDER BY bid', (int(rid),)).fetchall()
    db_release(con)
    return [{'rid': r[0], 'bid': r[1], 'active': r[2], 'worn': r[3], 'star': r[4],
             'expire': r[5], 'ctime': r[6]} for r in rows]


def db_fashion_get(rid, bid):
    for r in db_fashion_rows(rid):
        if int(r['bid']) == int(bid):
            return r
    return None


def db_fashion_upsert(rid, bid, **kw):
    db_fashion_init()
    cur = db_fashion_get(rid, bid) or {'rid': int(rid), 'bid': int(bid), 'active': 0,
                                       'worn': 0, 'star': 0, 'expire': 0,
                                       'ctime': int(time.time())}
    cur.update(kw)
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_fashion VALUES (?,?,?,?,?,?,?)',
                (int(cur['rid']), int(cur['bid']), int(cur.get('active') or 0),
                 int(cur.get('worn') or 0), int(cur.get('star') or 0),
                 int(cur.get('expire') or 0), int(cur.get('ctime') or time.time())))
    con.commit()
    db_release(con)
    return cur


# ==================== 光环（19100/19103/19104）—— PHASE 2.8 ====================
# 证据：协议字段来自 `protocol/fields.json`（`cmd_resolve_191.luac`）⇒ CONFIRMED；
#   客户端 `game/halo/*` 反汇编证实 `halo_model.haloData` 只读 **`stage/luck/grow`**
#   （`next_stage/max_luck/need_coin/item_bid` 走 `Config.Halo`，属客户端配置）。
#   `role_halo` / `role_halo_equip` 为兼容层 ⇒ INFERENCE。
def db_halo_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_halo (
        rid INTEGER PRIMARY KEY, stage INTEGER, luck INTEGER, res_stage INTEGER,
        grow INTEGER, power INTEGER)""")
    con.execute("""CREATE TABLE IF NOT EXISTS role_halo_equip (
        rid INTEGER, item_id INTEGER, bid INTEGER, pos INTEGER, ctime INTEGER,
        PRIMARY KEY (rid, item_id))""")
    con.commit()
    db_release(con)


def db_halo_get(rid):
    db_halo_init()
    con = db_conn()
    r = con.execute('SELECT stage,luck,res_stage,grow,power FROM role_halo WHERE rid=?',
                    (int(rid),)).fetchone()
    db_release(con)
    if not r:
        return {'stage': 0, 'luck': 0, 'res_stage': 0, 'grow': 0, 'power': 0}
    return {'stage': int(r[0] or 0), 'luck': int(r[1] or 0), 'res_stage': int(r[2] or 0),
            'grow': int(r[3] or 0), 'power': int(r[4] or 0)}


def db_halo_set(rid, **kw):
    cur = db_halo_get(rid)
    cur.update(kw)
    db_halo_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_halo VALUES (?,?,?,?,?,?)',
                (int(rid), int(cur.get('stage') or 0), int(cur.get('luck') or 0),
                 int(cur.get('res_stage') or 0), int(cur.get('grow') or 0),
                 int(cur.get('power') or 0)))
    con.commit()
    db_release(con)
    return cur


def db_halo_equip_rows(rid):
    db_halo_init()
    con = db_conn()
    rows = con.execute('SELECT item_id,bid,pos,ctime FROM role_halo_equip WHERE rid=? '
                       'ORDER BY item_id', (int(rid),)).fetchall()
    db_release(con)
    return [{'item_id': r[0], 'bid': r[1], 'pos': r[2], 'ctime': r[3]} for r in rows]


def db_halo_equip_add(rid, item_id, bid, pos=0):
    db_halo_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_halo_equip VALUES (?,?,?,?,?)',
                (int(rid), int(item_id), int(bid), int(pos), int(time.time())))
    con.commit()
    db_release(con)


def db_halo_equip_del(rid, item_id):
    db_halo_init()
    con = db_conn()
    con.execute('DELETE FROM role_halo_equip WHERE rid=? AND item_id=?',
                (int(rid), int(item_id)))
    con.commit()
    db_release(con)
    return con.total_changes


# ==================== 拍卖行（18020-18022）—— PHASE 2.9 ====================
def auction_cfg():
    """`config_auction_data` 的 rows（原版配置：item_bid/item_name/init_price/buy_price/assets）。"""
    try:
        return (kcfg('config_auction_data') or {}).get('rows') or {}
    except Exception:
        return {}


def auction_price_assets_code(row):
    """配置里的 `assets` 是**资产名**（如 `guild_contrib`）；SC 要**资产 code(u8)**。

    依据：`asset_label_map()`（= `config_game_data.CodeToAssets` 反查）⇒ 与扣费用同一套资产体系。
    """
    try:
        return int(asset_label_map().get(str(row.get('assets') or ''), 0)) & 0xff
    except Exception:
        return 0


def db_market_set(rid, on):
    """★ R121：摆摊开关（`13803`）。**真的写表**。"""
    try:
        con = db_conn()
        con.execute("""CREATE TABLE IF NOT EXISTS role_market (
            rid INTEGER PRIMARY KEY, on_state INTEGER, ctime INTEGER)""")
        con.execute('INSERT OR REPLACE INTO role_market VALUES (?,?,?)',
                    (int(rid), int(on), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_market_set failed: %r' % (e,))
        return False


def db_dung_enter(rid, dung_bid, args_blob=''):
    """★ R121：记录"进入副本"（`13020`），落 `dungeon_progress`（`ptype='dung_enter'`）。"""
    try:
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO dungeon_progress VALUES (?,?,?,?)',
                    (int(rid), 'dung_enter', str(int(dung_bid)),
                     str(args_blob)[:120]))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_dung_enter failed: %r' % (e,))
        return False


def item_value(bid):
    """物品的"价值"（`item_config[bid].value`）—— `10504` 出售价用。

    ⚠ `value` 是否就是原版**售价**未取证 ⇒ 只把它当"金币收入"，不涉及其他货币。
    """
    try:
        v = item_cfg().get(str(bid)) or item_cfg().get(bid)
        if isinstance(v, dict):
            return int(v.get('value') or 0)
    except Exception:
        pass
    return 0


def mall_good(bid):
    """商城商品（`config_mall.MallGoods[bid]`）—— `12821` 购买用。"""
    global _MALL_GOODS
    try:
        if _MALL_GOODS is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_mall.json')
            with open(p, encoding='utf-8') as f:
                _MALL_GOODS = (json.load(f).get('MallGoods') or {})
            log('server.log', 'mall goods loaded: %d 条' % len(_MALL_GOODS))
        v = _MALL_GOODS.get(str(bid)) or _MALL_GOODS.get(bid)
        if isinstance(v, dict):
            h = v.get('hash') if 'hash' in v else v
            return h if isinstance(h, dict) else None
    except Exception as e:
        log('server.log', '!! mall goods load failed: %r' % (e,))
    return None


def db_set_role_name(rid, name):
    """改角色名（`10343`）。返回 True/False。"""
    try:
        con = db_conn()
        con.execute('UPDATE roles SET name=? WHERE rid=?', (str(name), int(rid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_set_role_name failed: %r' % (e,))
        return False


_MALL_GOODS = None


def db_invest_init():
    """★ R117：投资进度（`17200`/`16503` 的数据源）。列名对应协议语义。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_invest (
        rid INTEGER, itype INTEGER, day INTEGER, geted INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, itype))""")
    con.commit()
    db_release(con)


def db_invest_state(rid, itype=None):
    """投资进度。`itype` 为 None 时取**进行中进度最大的那一档**。

    **没有行 ⇒ `{'itype':0,'day':0,'geted':0}`**（= 没有投资，是真话）。
    """
    st = {'itype': 0, 'day': 0, 'geted': 0}
    try:
        db_invest_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        if itype is None:
            r = con.execute('SELECT itype,day,geted FROM role_invest WHERE rid=? '
                            'ORDER BY day DESC LIMIT 1', (int(rid),)).fetchone()
        else:
            r = con.execute('SELECT itype,day,geted FROM role_invest '
                            'WHERE rid=? AND itype=?', (int(rid), int(itype))).fetchone()
        db_release(con)
        if r is not None:
            st = {'itype': int(r['itype'] or 0), 'day': int(r['day'] or 0),
                  'geted': int(r['geted'] or 0)}
    except Exception as e:
        log('tcp.log', '  !! db_invest_state failed: %r' % (e,))
    return st


def db_invest_set(rid, itype, day, geted=0):
    try:
        db_invest_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_invest VALUES (?,?,?,?,?)',
                    (int(rid), int(itype), int(day), int(geted), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_invest_set failed: %r' % (e,))
        return False


def invest_type_list():
    """`InvestType` 的键（2/3/7/8），排序后返回。"""
    try:
        return sorted(int(x) for x in (invest_cfg().get('InvestType') or {}).keys())
    except Exception:
        return []


def invest_milestones(itype):
    """该档投资的**里程碑**（天数或等级）列表 —— 依据配置：

      · 类型 7/8 ⇒ 取 `DayInvest[type]` 的天数（1..7）
      · 类型 3   ⇒ 取 `LevDays[type]` 的等级（25/35/45/55/65/75）
      · 都没有 ⇒ 空（诚实）
    """
    try:
        ic = invest_cfg()
        di = (ic.get('DayInvest') or {}).get(str(itype))
        if isinstance(di, dict) and di:
            return sorted(int(x) for x in di.keys())
        ld = (ic.get('LevDays') or {}).get(str(itype))
        if isinstance(ld, list):
            return sorted(int(x) for x in ld if isinstance(x, (int, float)) and x)
    except Exception:
        pass
    return []


def ride_cfg():
    """★ R115：坐骑配置（`config_ride` 批量解构结果）。"""
    global _RIDE_CFG
    try:
        if _RIDE_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_ride.json')
            with open(p, encoding='utf-8') as f:
                _RIDE_CFG = json.load(f)
            log('server.log', 'ride cfg loaded: %s' % list(_RIDE_CFG.keys()))
        return _RIDE_CFG
    except Exception as e:
        log('server.log', '!! ride cfg load failed: %r' % (e,))
        return {}


def db_ride_init():
    """★ R115：玩家坐骑态（`15501` 的数据源）。列名逐个对应协议语义。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_ride (
        rid INTEGER PRIMARY KEY, jie INTEGER, lev INTEGER, jie_luck INTEGER,
        grow INTEGER, zz INTEGER, face INTEGER, use INTEGER, updated_at INTEGER)""")
    con.commit()
    db_release(con)


def db_ride_state(rid):
    """坐骑态；**没有行 ⇒ 全 0**（= 没有坐骑，是真话）。"""
    st = {'jie': 0, 'lev': 0, 'jie_luck': 0, 'grow': 0, 'zz': 0, 'face': 0, 'use': 0}
    try:
        db_ride_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT jie,lev,jie_luck,grow,zz,face,use FROM role_ride '
                        'WHERE rid=?', (int(rid),)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                if r[k] is not None:
                    st[k] = int(r[k])
    except Exception as e:
        log('tcp.log', '  !! db_ride_state failed: %r' % (e,))
    return st


def db_ride_set(rid, jie, lev=1):
    try:
        db_ride_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_ride VALUES (?,?,?,?,?,?,?,?,?)',
                    (int(rid), int(jie), int(lev), 0, 0, 0, 0, 0, int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_ride_set failed: %r' % (e,))
        return False


def _hash_of(v):
    """解构结果里"具名表"的形状是 `{"array":[], "hash":{…}}` ⇒ 统一取出内层 dict。"""
    if isinstance(v, dict) and 'hash' in v and isinstance(v['hash'], dict):
        return v['hash']
    return v if isinstance(v, dict) else {}


# `SC_15501.attr_list` 的**字段顺序**（严格按 spec 抄，不从别处推断）
RIDE_ATTR_ORDER = ['atk_s', 'atk_p', 'def_s', 'def_p', 'hp_max', 'mspd',
                   'tenacity', 'hit', 'dodge', 'crit', 'red_def_s', 'red_def_p']


def ride_attr_values(lev):
    """按 spec 顺序返回该等级的 12 个属性值（来自 `RideLevAttr[lev].attr`）。

    **没有坐骑/没有该等级 ⇒ 12 个 0**（真话，不是编造）。
    """
    if not lev:
        return [0] * len(RIDE_ATTR_ORDER)
    try:
        row = _hash_of((ride_cfg().get('RideLevAttr') or {}).get(str(lev)))
        at = _hash_of(row.get('attr')) if row else {}
        return [int(at.get(k) or 0) & 0xffffffff for k in RIDE_ATTR_ORDER]
    except Exception as e:
        log('tcp.log', '  !! ride_attr_values failed: %r' % (e,))
        return [0] * len(RIDE_ATTR_ORDER)


def ride_skills():
    """坐骑技能 bid 列表（`RideAllSkill`，解构后是 `[None, 19011, …]`）。"""
    try:
        arr = ride_cfg().get('RideAllSkill') or []
        return [int(x) for x in arr if isinstance(x, (int, float)) and x]
    except Exception:
        return []


def ride_can_items():
    """升阶所需物品 `[(jie, item_bid, item_num), …]`（`RideJie[].item_num`）。"""
    out = []
    try:
        for k, v in (ride_cfg().get('RideJie') or {}).items():
            h = _hash_of(v)
            jie = int(h.get('jie') or 0)
            num = int(h.get('item_num') or 0)
            if jie and num:
                out.append((jie, int(h.get('item_bid') or 0), num))
    except Exception:
        pass
    return sorted(out)


_RIDE_CFG = None


def db_equip_get_one(rid, item_id):
    """按装备实例 id 取一行 `equip_items`（`21403` 卸下用）。"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT slot,item_id,bid,hero_bid FROM equip_items '
                        'WHERE rid=? AND item_id=?', (int(rid), int(item_id))).fetchone()
        db_release(con)
        return dict(r) if r else None
    except Exception as e:
        log('tcp.log', '  !! db_equip_get_one failed: %r' % (e,))
        return None


def db_equip_delete(rid, item_id):
    """按装备实例 id 删除 `equip_items` 行（`21403` 卸下用）。"""
    try:
        con = db_conn()
        cur = con.execute('DELETE FROM equip_items WHERE rid=? AND item_id=?',
                          (int(rid), int(item_id)))
        con.commit()
        db_release(con)
        return bool(cur.rowcount)
    except Exception as e:
        log('tcp.log', '  !! db_equip_delete failed: %r' % (e,))
        return False


def equip_grid_size(rid):
    """装备格子容量：优先 `bag_volume` 里 `bag_code=2`（ROLE_EQUIP）的容量，取不到 ⇒ 0。

    `bag_code` 的取值依据见 R58 的注释（`BackPackConst.Bag_Code`：
    `BACKPACK=1 / ROLE_EQUIP=2 / HERO_EQUIP=3 / STORAGE=4 / HERO_STORAGE=5 …`）。
    """
    try:
        con = db_conn()
        r = con.execute('SELECT volume FROM bag_volume WHERE rid=? AND bag_code=?',
                        (int(rid), 2)).fetchone()
        db_release(con)
        return int(r[0]) if r and r[0] else 0
    except Exception:
        return 0


def db_rune_init():
    """★ R113：符文等级存储（`21406` 升级用）。

    列名逐个对应语义（同 `role_heros`/`peakwar_state` 的做法）。
    **没有行 ⇒ 等级 1**（刚兑换到就是 1 级 —— 与 `RuneBase[bid]['1']` 一致）。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_runes (
        rid INTEGER, rune_bid INTEGER, lev INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, rune_bid))""")
    con.commit()
    db_release(con)


def db_rune_lev(rid, rune_bid):
    """该符文的等级；**没有行 ⇒ 1**（不是 0：`RuneBase` 的等级从 1 开始）。"""
    try:
        db_rune_init()
        con = db_conn()
        r = con.execute('SELECT lev FROM role_runes WHERE rid=? AND rune_bid=?',
                        (int(rid), int(rune_bid))).fetchone()
        db_release(con)
        return int(r[0]) if r and r[0] else 1
    except Exception as e:
        log('tcp.log', '  !! db_rune_lev failed: %r' % (e,))
        return 1


def db_rune_set_lev(rid, rune_bid, lev):
    try:
        db_rune_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO role_runes VALUES (?,?,?,?)',
                    (int(rid), int(rune_bid), int(lev), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_rune_set_lev failed: %r' % (e,))
        return False


def rune_up_cost(rune_bid, cur_lev):
    """升到 `cur_lev+1` 的消耗 `{资产名: 数量}`（来自 `RuneBase[bid][lev].assets`）。

    取 `RuneBase[bid][cur_lev+1]` 的 `assets`（元素形如 `[null,'rune_exp',443]`）；
    取不到 ⇒ `None`（调用方据此回"已满级/无效"）。
    """
    try:
        rb = (rune_cfg().get('RuneBase') or {}).get(str(rune_bid))
        if not isinstance(rb, dict):
            return None
        nxt = rb.get(str(int(cur_lev) + 1))
        if not isinstance(nxt, dict):
            return None
        h = nxt.get('hash', nxt)
        out = {}
        for _i, pair in (h.get('assets') or {}).items():
            if isinstance(pair, list) and len(pair) >= 3 and isinstance(pair[1], str):
                out[pair[1]] = int(pair[2] or 0)
        return out
    except Exception as e:
        log('tcp.log', '  !! rune_up_cost failed: %r' % (e,))
        return None


def mingge_cfg():
    """★ R111：命格配置（`config_mingge` 批量解构结果的最小集）。

    关键字段：`MinggeOther.stage_init`（命格系统的**初始阶段**）——
    `SC_19400.mingge_stage` 就用它，这是**有出处**的值（配置写死 1），
    而不是默认响应会给的 0。
    """
    global _MINGGE_CFG
    try:
        if _MINGGE_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', '_mingge_cfg.json')
            with open(p, encoding='utf-8') as f:
                _MINGGE_CFG = json.load(f)
            log('server.log', 'mingge cfg loaded: %s' % list(_MINGGE_CFG.keys()))
        return _MINGGE_CFG
    except Exception as e:
        log('server.log', '!! mingge cfg load failed: %r' % (e,))
        return {}


def mingge_stage_init():
    """命格初始阶段（`MinggeOther.stage_init`）；取不到 ⇒ 1（保守，且与配置一致）。"""
    try:
        mo = (mingge_cfg().get('MinggeOther') or {})
        # `MinggeOther` 解构后形如 {"array":[], "hash":{...}} 或直接是 dict
        h = mo.get('hash') if isinstance(mo, dict) and 'hash' in mo else mo
        if isinstance(h, dict):
            v = h.get('stage_init')
            if v is not None:
                return int(v) & 0xff
    except Exception:
        pass
    return 1


_MINGGE_CFG = None


def rune_exchange_cost(rune_bid):
    """给定 `rune_bid`，返回 `{资产名: 数量}`（来自 `RuneExchange[].assets`）。

    同时认 `rune_id`（21403…）与条目自身的 `id`（1/2/3…）—— 客户端字段名叫 `rune_bid`，
    两种编号都可能被传过来，**两个都认**最稳妥（命中即返回，不猜）。
    """
    try:
        for _k, v in (rune_cfg().get('RuneExchange') or {}).items():
            h = (v or {}).get('hash') if isinstance(v, dict) else None
            if not h:
                continue
            if int(h.get('rune_id') or 0) != int(rune_bid) and \
               int(h.get('id') or 0) != int(rune_bid):
                continue
            out = {}
            for _i, pair in (h.get('assets') or {}).items():
                # `assets` 的元素是 Lua 数组形式 `[null, 资产名, 数量]`
                if isinstance(pair, list) and len(pair) >= 3 and isinstance(pair[1], str):
                    out[pair[1]] = int(pair[2] or 0)
            return out
    except Exception as e:
        log('tcp.log', '  !! rune_exchange_cost failed: %r' % (e,))
    return None


def rune_cfg():
    """★ R109：魂星（符文）配置 —— `config_rune_data` 解构结果。

    只保留 `21411` 需要的三张表（源文件 1.2MB / 20108 张表，全量落盘不必要）：
        RuneExchange = {[1]={name:"巨门", rune_id:21403, count:0, assets:{…}}, …}  20 项
        RuneBase     = 124 项（每个符文 1..50 级）
        RuneStatic   = {max_lev:50, low_exchange:4500, role_lev:78}
    """
    global _RUNE_CFG
    try:
        if _RUNE_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', '_rune_cfg.json')
            with open(p, encoding='utf-8') as f:
                _RUNE_CFG = json.load(f)
            log('server.log', 'rune cfg loaded: %s <- %s'
                % (list(_RUNE_CFG.keys()), p))
        return _RUNE_CFG
    except Exception as e:
        log('server.log', '!! rune cfg load failed: %r' % (e,))
        return {}


def rune_exchange_rows():
    """`RuneExchange` 的兑换条目：`[(rune_id, count), …]`（按 id 排序）。"""
    out = []
    try:
        for k, v in (rune_cfg().get('RuneExchange') or {}).items():
            h = (v or {}).get('hash') if isinstance(v, dict) else None
            if not h:
                continue
            rid = h.get('rune_id')
            if rid is None:
                continue
            out.append((int(rid), int(h.get('count') or 0)))
    except Exception as e:
        log('tcp.log', '  !! rune_exchange_rows failed: %r' % (e,))
    return sorted(out)


_RUNE_CFG = None


def invest_cfg():
    """★ R107：投资档位配置（`config_invest` 解构结果，见 `tools/config_deconstruct.py`）。

    这是**此前提取器输出 0 条**的那类"具名嵌套配置"，解构器做出来后才可用。
    结构：
        InvestType = {"2":{"name":"登录基金","is_charge":0}, "3":…, "7":…, "8":…}
        LevDays    = {"3":[null,25,35,45,55,65,75]}   ← 等级门槛
    """
    global _INVEST_CFG
    try:
        if _INVEST_CFG is None:
            p = os.path.join(os.path.dirname(HERE), 'server', '_invest_cfg.json')
            with open(p, encoding='utf-8') as f:
                _INVEST_CFG = json.load(f)
            log('server.log', 'invest cfg loaded: %d 个顶层键 <- %s'
                % (len(_INVEST_CFG), p))
        return _INVEST_CFG
    except Exception as e:
        log('server.log', '!! invest cfg load failed: %r' % (e,))
        return {}


def invest_level_gate(cfg, itype):
    """该投资档位的**最低等级门槛**（取 `LevDays[type]` 的最小非空值）；没有门槛 ⇒ 0。"""
    try:
        arr = (cfg.get('LevDays') or {}).get(str(itype))
        if isinstance(arr, list):
            vals = [int(x) for x in arr if isinstance(x, (int, float)) and x]
            return min(vals) if vals else 0
    except Exception:
        pass
    return 0


_INVEST_CFG = None


def db_equip_rows(rid):
    """角色的已穿戴装备（`equip_items` 表），按 `hero_bid` 是否非 0 分成两拨。

    ★ R104：`SC_21400` 的 `role_eqm` / `partner_eqm` 两者**同构**，唯一区别就是
      "穿在角色身上"还是"穿在伙伴身上"，而 DB 里正好有 `hero_bid` 这一列区分
      （0 = 角色；非 0 = 伙伴）⇒ **这是一个有依据的划分，不是猜测**。
    """
    role, partner = [], []
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT slot,item_id,bid,hero_bid,ctime FROM equip_items '
                             'WHERE rid=? ORDER BY slot', (int(rid),)):
            e = {'id': int(r['item_id'] or 0), 'bid': int(r['bid'] or 0),
                 'hero_bid': int(r['hero_bid'] or 0), 'pos': int(r['slot'] or 0),
                 'ctime': int(r['ctime'] or 0)}
            (partner if e['hero_bid'] else role).append(e)
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_equip_rows failed: %r' % (e,))
    return role, partner


def db_peakwar_init():
    """★ R100：**巅峰战**（`18803`）状态存储。

    列名**逐个对应 `SC_18803` 的字段**（照 `race_state`/`arena_state` 的同款做法，
    不引入任何猜测映射）。依据：客户端 `game/peakwar/peakwar_ctrl.luac`。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS peakwar_state (
        rid INTEGER PRIMARY KEY, rest_time INTEGER, win_times INTEGER,
        total_times INTEGER, score INTEGER, win_reward_flag INTEGER,
        time_reward_flag INTEGER, rank INTEGER, end_time INTEGER,
        match_flag INTEGER, daily_times INTEGER, peak_index INTEGER,
        cont_win_times INTEGER, max_score INTEGER, updated_at INTEGER)""")
    con.commit()
    db_release(con)


def db_peakwar_state(rid):
    """巅峰战状态；**没有行就返回全 0**（= 没打过，是真话，不是占位）。"""
    st = {'rest_time': 0, 'win_times': 0, 'total_times': 0, 'score': 0,
          'win_reward_flag': 0, 'time_reward_flag': 0, 'rank': 0, 'end_time': 0,
          'match_flag': 0, 'daily_times': 0, 'peak_index': 0,
          'cont_win_times': 0, 'max_score': 0}
    try:
        db_peakwar_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT * FROM peakwar_state WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                if r[k] is not None:
                    st[k] = int(r[k])
    except Exception as e:
        log('tcp.log', '  !! db_peakwar_state failed: %r' % (e,))
    return st


def db_race_init():
    """★ R50：魂师大赛（竞速，`173xx`）状态存储。

    列名**逐个对应协议字段**（`SC_17301`），不引入任何猜测映射。
    依据：客户端 `race_ctrl.luac` proto#14 `on17301` → `model:setScore(data.score)`；
    `race_ui_wait` / `race_ui_rank` 消费 `score/win_times/total_times/rank_list`。
    """
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS race_state (
        rid INTEGER PRIMARY KEY, daily_time INTEGER, daily_time2 INTEGER,
        score INTEGER, win_times INTEGER, lose_times INTEGER, total_times INTEGER,
        rest_time INTEGER, first_reward INTEGER, is_match INTEGER, kill_number INTEGER,
        continue_win INTEGER, is_team_open INTEGER, act_status INTEGER, daily_win INTEGER,
        updated_at INTEGER)""")
    # ★ 幂等补列：`CREATE TABLE IF NOT EXISTS` 不会给**已存在**的旧表加列
    #   （本表首版只有 11 列，补 6 字段后旧库会缺列 ⇒ sqlite3.Row 取值抛错被吞掉，
    #    表现为"字段静默恒 0"）。这里按需 ALTER，保留既有行。
    # ponytail: 只为这一张新表做最小迁移，通用迁移框架这个规模用不上。
    have = set(d[1] for d in con.execute('PRAGMA table_info(race_state)'))
    for col in ('is_match', 'kill_number', 'continue_win', 'is_team_open',
                'act_status', 'daily_win'):
        if col not in have:
            con.execute('ALTER TABLE race_state ADD COLUMN %s INTEGER' % col)
    con.commit()
    db_release(con)


def db_race_state(rid):
    """竞速状态；**没有行就返回全 0**（= 没打过，是真话，不是占位）。

    ★ 列**逐个对齐 `SC_17301` 的 16 个字段**（曾漏掉 is_match/kill_number/continue_win/
      is_team_open/act_status/daily_win 六个，被 `tools/verify_race.py` 当场抓出）。
    """
    st = {'daily_time': 0, 'daily_time2': 0, 'score': 0, 'win_times': 0,
          'lose_times': 0, 'total_times': 0, 'rest_time': 0, 'first_reward': 0,
          'is_match': 0, 'kill_number': 0, 'continue_win': 0, 'is_team_open': 0,
          'act_status': 0, 'daily_win': 0}
    try:
        db_race_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT * FROM race_state WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                if r[k] is not None:
                    st[k] = int(r[k])
    except Exception as e:
        log('tcp.log', '  !! db_race_state failed: %r' % (e,))
    return st


def race_rank_list(rid, limit=20):
    """`SC_17309.rank_list` 的真实来源 —— 名字/等级/职业/性别全部取自 `roles` 表，
    分数取自各自的 `race_state.score`（没打过就是 0）。**一个数值都不编造。**
    （沿用 R47「竞技场对手源 = 本服已有角色」的决策 A。）
    """
    rows = []
    try:
        db_race_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT rid, name, level, career, sex FROM roles '
                             'ORDER BY rid LIMIT ?', (int(limit),)):
            _r = int(r['rid'])
            rows.append({'role_name': r['name'] or '', 'rid': _r, 'srid': '',
                         'career': int(r['career'] or 0), 'sex': int(r['sex'] or 0),
                         'score': int(db_race_state(_r)['score']),
                         'lev': int(r['level'] or 0),
                         'win_num': int(db_race_state(_r)['win_times'])})
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! race_rank_list failed: %r' % (e,))
    # 名次按 (分, 胜场) 降序；同分同名次不编造，直接用连续序号（客户端只显示）
    rows.sort(key=lambda x: (-x['score'], -x['win_num'], x['rid']))
    for i, x in enumerate(rows, 1):
        x['rank'] = i
    return rows


def promote_tips():
    """`Config.Promote` 的**第一子表**（提升方式/推荐），来自 `server/_promote.json`。

    用途：`SC_20100.promote` 的 `code` 就是这张表的行号（客户端
    `advance_new_panel.luac` proto#17：`Config.Promote[one.code].display_lev`）。
    数据来源：APK `assets/src/config/config_promote.luac`（`tools/extract_promote.py`）。
    """
    global _PROMOTE
    if _PROMOTE is None:
        try:
            with open(os.path.join(HERE, '_promote.json'), encoding='utf-8') as f:
                _PROMOTE = json.load(f).get('tips') or []
        except Exception as e:
            log('tcp.log', '  !! 读取 _promote.json 失败: %r' % (e,))
            _PROMOTE = []
    return _PROMOTE


def richang_activity_tasks():
    """`type_name == '活动'` 的条目 = **全服活动**（`SC_10922.act_list` 的 id 空间）。

    依据：protocol/cmd_table.json 里 `10922 = 全服活动的活动状态`；
    且客户端 `activity_ctrl.luac` proto#37 内以 KSHORT 硬编码了这批活动 id
    （101 斗罗战场 / 107 学院闯关 / 108 魂师大赛 / 111 宗门战 / 112 帝国之战 /
      113 精英大赛 / 115 首席争霸 / 116 绝地凶兽 / 118 宗门副本），
    它们的名称与 `config_richang` 的活动类条目逐条吻合。
    """
    return [t for t in (richang_cfg().get('tasks') or [])
            if t.get('type_name') == '\u6d3b\u52a8']


def db_daily_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS daily_progress (
        rid INTEGER, tid INTEGER, num INTEGER, val INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, tid))""")
    con.execute("""CREATE TABLE IF NOT EXISTS daily_lingqu (
        rid INTEGER, huoli INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, huoli))""")
    con.commit()
    db_release(con)


def db_daily_get(rid):
    """-> {tid: {'num':n,'val':v}}；没有行就是空（= 没做过，是真话）。"""
    out = {}
    try:
        db_daily_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        for r in con.execute('SELECT tid,num,val FROM daily_progress WHERE rid=?', (rid,)):
            out[int(r['tid'])] = {'num': int(r['num'] or 0), 'val': int(r['val'] or 0)}
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_daily_get failed: %r' % (e,))
    return out


def db_daily_lingqu(rid):
    """已领取的活跃度档位。"""
    out = []
    try:
        db_daily_init()
        con = db_conn()
        for r in con.execute('SELECT huoli FROM daily_lingqu WHERE rid=? ORDER BY huoli',
                             (rid,)):
            out.append(int(r[0]))
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_daily_lingqu failed: %r' % (e,))
    return out


def db_daily_add(rid, tid, num=1, val=0):
    """累加某日常任务的完成次数与活力（供行为挂钩/调参使用）。"""
    try:
        db_daily_init()
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO daily_progress '
                    '(rid,tid,num,val,updated_at) VALUES (?,?,0,0,?)',
                    (rid, int(tid), int(time.time())))
        con.execute('UPDATE daily_progress SET num=num+?, val=val+?, updated_at=? '
                    'WHERE rid=? AND tid=?',
                    (int(num), int(val), int(time.time()), rid, int(tid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_daily_add failed: %r' % (e,))
        return False


# ---------------------------------------------------------------------------
# ★★ R48：成就（`164xx`）—— 表来自 `config_chengjiu` → `server/_chengjiu.json`
#   真机 `16400` 发了 **450 次**，原落通用集合回全零。
#   342 条成就，每条带 `val`（目标值）/`cent`（成就点）/`desc`（中文要求）/
#   `trigger_mod`+`trigger_fun`（★ 进度触发链接）。
#   取数分工（按规格 `SC_16400{type, chengjiu{bid,val,time},
#                             chengjiu_has{bid,time_out,state},
#                             chengjiu_rate{bid,rate}}`）：
#     · `chengjiu`      = 有进度的成就：`val`=当前进度（DB）
#     · `chengjiu_rate` = `rate`=进度百分比（由 val/目标推导）
#     · `chengjiu_has`  = **留空**：其 `state` 语义（可领/已领）**未取证** ⇒ 不猜
# ---------------------------------------------------------------------------
_CHENGJIU = None


def chengjiu_cfg():
    """成就表（只读快照）。"""
    global _CHENGJIU
    if _CHENGJIU is None:
        try:
            with open(os.path.join(HERE, '_chengjiu.json'), encoding='utf-8') as f:
                _CHENGJIU = json.load(f).get('items') or {}
        except Exception as e:
            log('tcp.log', '  !! 读取 _chengjiu.json 失败: %r' % (e,))
            _CHENGJIU = {}
    return _CHENGJIU


def db_chengjiu_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS chengjiu_progress (
        rid INTEGER, bid INTEGER, val INTEGER, updated_at INTEGER,
        PRIMARY KEY (rid, bid))""")
    con.commit()
    db_release(con)


def db_chengjiu_get(rid):
    """-> {bid: 当前进度}；没有行就是空（= 没进展，是真话）。"""
    out = {}
    try:
        db_chengjiu_init()
        con = db_conn()
        for r in con.execute('SELECT bid,val FROM chengjiu_progress WHERE rid=?', (rid,)):
            out[int(r[0])] = int(r[1] or 0)
        db_release(con)
    except Exception as e:
        log('tcp.log', '  !! db_chengjiu_get failed: %r' % (e,))
    return out


def db_chengjiu_add(rid, bid, n=1):
    """累加某成就的进度（供行为挂钩/调参使用）。"""
    try:
        db_chengjiu_init()
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO chengjiu_progress '
                    '(rid,bid,val,updated_at) VALUES (?,?,0,?)',
                    (rid, int(bid), int(time.time())))
        con.execute('UPDATE chengjiu_progress SET val=val+?, updated_at=? '
                    'WHERE rid=? AND bid=?', (int(n), int(time.time()), rid, int(bid)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_chengjiu_add failed: %r' % (e,))
        return False


# ---------------------------------------------------------------------------
# ★★ R48：把「任务提交」这一个真实事件，同时喂给**日常次数**与**成就进度**
#   分组表：`server/_chengjiu_map.json`（**可编辑、可校准**，理由见该文件 _note）
#   ★ 为什么不能用配置自动推：成就表的 `trigger_mod/trigger_fun`（mission/hongchen）
#     **不是服务端配置链接** —— `hongchen` 从不出现于 `config_mission`，
#     只出现在客户端 ctrl/guide/promote 中（是客户端 Lua 处理器名）；
#     `config_mission` 也没有指向 huoli_id / 成就 bid 的字段。
#     ⇒ 用一个显式分组表，映射不清时**只改数据、不改代码**。
# ---------------------------------------------------------------------------
_CJ_MAP = None
_CJ_MAP_MTIME = None


def chengjiu_map():
    """读取分组映射；**按文件 mtime 热重载** —— 补一行 JSON 不需要重启服务端。"""
    global _CJ_MAP, _CJ_MAP_MTIME
    path = os.path.join(HERE, '_chengjiu_map.json')
    try:
        mt = os.path.getmtime(path)
    except OSError:
        mt = None
    if _CJ_MAP is None or mt != _CJ_MAP_MTIME:
        try:
            with open(path, encoding='utf-8') as f:
                _CJ_MAP = json.load(f).get('groups') or []
            _CJ_MAP_MTIME = mt
            log('tcp.log', '  ** 进度分组映射已加载/热重载: %d 组' % len(_CJ_MAP))
        except Exception as e:
            log('tcp.log', '  !! 读取 _chengjiu_map.json 失败: %r' % (e,))
            _CJ_MAP = []
    return _CJ_MAP


def credit_mission_done(cfg, rid, mission_bid):
    """任务提交成功后调用：命中分组则给日常次数 +1、给对应成就进度 +1。

    返回 `(daily_panel_id, ach_bids)`；**未命中任何分组的 bid ⇒ 什么都不做**。

    ★ 匹配用**显式 `mission_bids` 白名单**，**不能**用 `config_mission.type`：
      实测 config_mission **262 条任务全部 type=1**（学院线/监察团/斗魂场/封神之路
      都在同一 type）⇒ 按 type 匹配会把**任何**任务提交都记成学院任务 = 伪造进度。
      这是本项目自查发现并修掉的错误（第一版就是这么写的）。
    ★ 只加「次数/进度」——**活力(val) 每次给量未取证，计 0 不编**。
    """
    bid = int(mission_bid)
    for g in chengjiu_map():
        if bid not in [int(x) for x in (g.get('mission_bids') or [])]:
            continue
        pid = int(g.get('panel_id') or 0)
        bids = [int(b) for b in (g.get('ach_bids') or [])]
        if pid:
            db_daily_add(rid, pid, 1, 0)
        for b in bids:
            db_chengjiu_add(rid, b, 1)
        log('tcp.log', '  ** 进度挂钩：任务 %d ⇒ 日常 %s +1次；成就 %s +1'
            % (bid, pid or '-', bids or '-'))
        return pid, bids
    return None, []


# ---------------------------------------------------------------------------
# ★★ R48：挂机轮次（`15405`）
#   真机证据链：主城「日常」→ 学院任务「参与」→ 自动寻路 → 客户端发 **`15405`**
#   → 服务端当时回**通用零值** `loop_count=0` → 之后**再无任何命令**（挂机不启动）。
#   等级（150 / 70）与地图（lv70 用 10005，服务端有碰撞数据）**都已排除**，
#   唯一卡点就是这里的 `loop_count`。
#   ⚠ `loop_count` 的"已完成 / 目标"语义**未取证** ⇒ 默认值保持 **0**（不改变现状），
#     只在实验时用 admin 临时调高。
# ---------------------------------------------------------------------------
def db_guaji_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS guaji_state (
        rid INTEGER PRIMARY KEY, loop_count INTEGER, updated_at INTEGER)""")
    # ★ R53：补两列。`CREATE TABLE IF NOT EXISTS` **不会**给旧表加列（R50 已踩过一次），
    #   旧库缺列会让 Row[k] 抛错、被 try/except 吞掉 ⇒ 静默恒 0。按需 ALTER。
    # ponytail: 只为这张表做最小迁移，这个规模用不上通用迁移框架。
    have = set(d[1] for d in con.execute('PRAGMA table_info(guaji_state)'))
    # ★ C3.3-D：补离线挂机开关两列。
    #   off_on = 离线挂机开关（0/1，对应客户端 10932 的 off_state 字段）；
    #   off_started_at = 开启时刻服务端时间戳（防回拨/未来离线结算用；本批不发收益）。
    for col in ('mission_bid', 'kill_count', 'off_on', 'off_started_at'):
        if col not in have:
            con.execute('ALTER TABLE guaji_state ADD COLUMN %s INTEGER' % col)
    con.commit()
    db_release(con)


def db_guaji_state(rid):
    """挂机状态：`loop_count`（轮次）/ `mission_bid`（当前挂机任务）/ `kill_count`（累计击杀）
    / `off_on`（离线挂机开关）/ `off_started_at`（离线开启时间戳）。

    **没有行 ⇒ 全 0**（= 没挂过机，是真话）。
    """
    st = {'loop_count': 0, 'mission_bid': 0, 'kill_count': 0,
          'off_on': 0, 'off_started_at': 0}
    try:
        db_guaji_init()
        con = db_conn()
        con.row_factory = sqlite3.Row
        r = con.execute('SELECT * FROM guaji_state WHERE rid=?', (rid,)).fetchone()
        db_release(con)
        if r is not None:
            for k in st:
                if r[k] is not None:
                    st[k] = int(r[k])
    except Exception as e:
        log('tcp.log', '  !! db_guaji_state failed: %r' % (e,))
    return st


def db_guaji_update(rid, **kw):
    """按键更新挂机状态（只允许上述五列）。"""
    cur = db_guaji_state(rid)
    cur.update({k: int(v) for k, v in kw.items() if k in cur})
    try:
        db_guaji_init()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO guaji_state '
                    '(rid,loop_count,mission_bid,kill_count,off_on,off_started_at,updated_at)'
                    ' VALUES (?,?,?,?,?,?,?)',
                    (rid, cur['loop_count'], cur['mission_bid'], cur['kill_count'],
                     cur['off_on'], cur['off_started_at'], int(time.time())))
        con.commit()
        db_release(con)
        return cur
    except Exception as e:
        log('tcp.log', '  !! db_guaji_update failed: %r' % (e,))
        return cur


def db_guaji_get(rid):
    """该角色的挂机轮次；没有行 ⇒ 0。"""
    return int(db_guaji_state(rid)['loop_count'])


def db_guaji_set(rid, n):
    return bool(db_guaji_update(rid, loop_count=int(n)))


# ---------------------------------------------------------------------------
# ★★ R48：`15402` 挂机任务 → 地图/坐标（`CS{mission_bid}` → `SC{mission_bid,map_bid,x,y}`）
#   数据源：
#     · 挂机点表 = `config_guaji` → `server/_guaji.json`（`mon_bid/map_bid/lev_l/lev_r/disc`）
#     · 地图默认坐标 = `analysis/1.4.9/task/config_map.json` 的 `def_x/def_y`
#   ★★ 这条命令的 **CS 里带 `mission_bid`** —— 它就是"挂机线 ↔ 任务"的映射来源。
#     客户端发来的值会**原样记进日志**，用来填 `_chengjiu_map.json` 的 `mission_bids`。
# ---------------------------------------------------------------------------
_GUAJI = None
_MAP_DEF = None


# [P3deep-migrated] guaji_spots/map_def_xy/guaji_spot_for_lev 已下沉 scene/service.py：
# def guaji_spots(): ...
# def map_def_xy(map_bid): ...
# def guaji_spot_for_lev(lev): ...


BAG_ROLE_EQUIP = 2      # BackPackConst.Bag_Code.ROLE_EQUIP
BAG_HERO_EQUIP = 3      # BackPackConst.Bag_Code.HERO_EQUIP


def bag_items_of(rid, bag_code):
    """统一入口：取某个囊的物品列表。

    ★ 依据：`BackPackConst.Bag_Code`（客户端 backpack_const.luac）
      1=BACKPACK 2=ROLE_EQUIP 3=HERO_EQUIP 4=STORAGE。
    ★ 用户报障：之前 `10554` 在 frm/to 为 2/3（装备栏）时
      读的是 `bag_items` ⇒ **装备↔仓库 移动不互通**（已知缺口）。
    现按 bag_code 分派到正确的数据源。
    """
    if bag_code == STORAGE_CODE:
        return db_store_get(rid, bag_code)
    if bag_code in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP):
        return build_equip_items(rid, bag_code)
    return db_bag_get(rid, bag_code)


def bag_take_one(rid, bag_code, item_id):
    """从某囊移除一件（按 item_id）。返回被移除的行或 None。"""
    for it in bag_items_of(rid, bag_code):
        if int(it.get('item_id') or 0) == int(item_id):
            if bag_code == STORAGE_CODE:
                con = db_conn()
                con.execute('DELETE FROM store_items WHERE rid=? AND bag_code=? AND item_id=?',
                            (rid, bag_code, item_id))
                con.commit(); db_release(con)
            elif bag_code in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP):
                # 装备：按槽位取下
                db_equip_take(rid, int(it.get('pos') or 0))
            else:
                db_bag_delete(rid, [item_id], bag_code)
            return it
    return None


def bag_put_one(rid, bag_code, bid, item_id, qty=1, pos=0, hero_bid=0, cfg=None):
    """往某囊放一件。装备囊会**拒绝非装备**（返回 None）。

    ★ 修正（自查发现）：原签名**没有 cfg 参数**，而调用处传了 `cfg=self.cfg`
      ⇒ TypeError ⇒ 上层拿不到返回值 ⇒ **物品已被 take 却放不回去 ⇒ 丢失**
      （真机实测丢失 41601 / 41401 / 41801）。
    """
    if bag_code == STORAGE_CODE:
        # ★★ 修正（“移动会覆盖原有物品”）：
        #   **传入 item_id 保留身份**，且 `merge=False` **不按 bid 叠加**。
        return db_store_add(rid, bid, qty, bag_code, item_id=item_id, merge=False)
    if bag_code in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP):
        slot = int(pos) or equip_slot_for(rid, bid, cfg)
        if slot is None:
            return None                 # ★ 非装备 ⇒ 明确拒绝（不再默认塞 1 号槽）
        db_equip_put(rid, slot, item_id, bid, hero_bid)
        return item_id
    # ★ 背包目标：同样保留 item_id（避免 id 变动导致错位）
    return db_bag_add(rid, bid, qty, bag_code, item_id=item_id, merge=False)


def db_init_sign():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS sign_got (
        rid INTEGER, days INTEGER, ctime INTEGER, PRIMARY KEY (rid, days))""")
    con.commit()
    db_release(con)


def db_sign_got(rid, days):
    db_init_sign()
    con = db_conn()
    n = con.execute('SELECT COUNT(*) FROM sign_got WHERE rid=? AND days=?',
                    (rid, int(days))).fetchone()[0]
    db_release(con)
    return n > 0


def db_sign_add(rid, days):
    try:
        db_init_sign()
        con = db_conn()
        con.execute('INSERT OR IGNORE INTO sign_got (rid,days,ctime) VALUES (?,?,?)',
                    (rid, int(days), int(time.time())))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_sign_add failed: %r' % (e,))
        return False


def db_bag_get_one(rid, item_id, bag_code=BAG_MAIN):
    """\u6309 item_id \u53d6\u4e00\u4ef6\u7269\u54c1\uff08\u4e0d\u5b58\u5728\u8fd4\u56de None\uff09\u3002"""
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM bag_items WHERE rid=? AND bag_code=? AND item_id=?',
                          (rid, bag_code, item_id)).fetchone()
        out = dict(row) if row else None
        con.row_factory = None
        db_release(con)
        return out
    except Exception as e:
        log('tcp.log', '  !! db_bag_get_one failed: %r' % (e,))
        return None


def db_bag_set_quantity(rid, item_id, qty, bag_code=BAG_MAIN):
    """\u76f4\u63a5\u8bbe\u5b9a\u7269\u54c1\u6570\u91cf\u3002"""
    try:
        con = db_conn()
        con.execute('UPDATE bag_items SET quantity=? WHERE rid=? AND bag_code=? AND item_id=?',
                    (int(qty), rid, bag_code, item_id))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_bag_set_quantity failed: %r' % (e,))
        return False




D2_NON_RENDERABLE = {28514, 28560, 28515, 21403}  # [P16 D2-P0] 客户端无图标/资源的活动/符文 bid，10502 不下发



def make_battle(cfg, mon):
    """由「角色状态 + 场景怪物」构造一个战斗实例。

    ⚠ 怪物的 HP/攻击/防御取自 `server/battle.py` 的 `MON_STATS`，
      那是 **TEST_ONLY** 兼容值（`Config.Mon` 里没有这些字段，见
      `analysis/1.4.9/battle/monster_data_model.md` §3.1），**不是原版数值**。
    角色的攻击/防御/血量取自 `role_attr`（客户端 10303 下发过的那套属性）。
    """
    if battle_mod is None:
        return None
    role = role_state(cfg)
    attr = db_get_attr(role.get('rid', 1001)) or {}
    role_view = {
        'rid': role.get('rid', 1001),
        'srv_id': role.get('srv_id', '1'),
        'name': role.get('name', 'DSH'),
        'lev': role.get('lev', 1),
        'sex': role.get('sex', 0),
        'career': role.get('career', 1),
        'hp_max': attr.get('hp_max') or 1000,
        'hp': attr.get('hp_max') or 1000,
        'atk_s': attr.get('atk_s') or 100,
        'def_s': attr.get('def_s') or 0,
    }
    skills = cfg.get('skills') or []
    skill_bid = int(skills[0].get('bid', 0)) if skills else 0
    # 怪物等级：Config.Mon 索引 2 疑似 level（INFERRED），缺失时用 1
    md = mon_def(mon.get('bid') or 0)
    fields = md.get('fields') or []
    mon_lev = 1
    if len(fields) > 2 and isinstance(fields[2], int):
        mon_lev = fields[2]                     # APK 表字段（索引 2 疑似 level，**INFERRED**）
    # [P5] 怪物数值改走 MonsterService.JSTMCompatibleMonsterModel（INFERENCE）
    from monster import service as mon_service
    # ★★ 目标④补强：挂机怪改用 **server/_guaji.json 的等级区间上界**（**CONFIRMED**，
    #   且该表已实机 UI 对表验证）覆盖上面那个"疑似"值。
    #   实测缺陷（改动前）：10101/10105/10106 全被当 35 级 ⇒ hp=1075，对 lv70 玩家过弱；
    #   修正后按各自区间上界：10105(65–74)→74、10106(75–84)→84 …
    _band = mon_service.band_level(mon.get('bid') or 0)
    if _band:
        mon_lev = _band
    _scale = 1.0
    if len(fields) > 21 and isinstance(fields[21], (int, float)):
        _scale = fields[21]
    _mon_stat = mon_service.get_mon(mon.get('bid') or 0, mon_lev=mon_lev,
                                    mon_type='normal', scale=_scale)
    return battle_mod.Battle(
        role=role_view, mon_stat=_mon_stat,
        mon_name=mon.get('name') or md.get('name') or 'mon',
        mon_res_id=mon.get('res_id') or md.get('res_id') or '',
        mon_lev=mon_lev,
        # ★ R79：必须把怪的 **bid** 传进去 —— 客户端是
        #   `if srv_id=='mon' then Config.Mon[rid].res_id end` 取模型的（battle_role proto#2）。
        mon_bid=int(mon.get('bid') or mon.get('id') or 0),
        role_skill_bid=skill_bid)


class TcpHandler(socketserver.BaseRequestHandler):

    def _register_live(self):
        try:
            with LIVE_LOCK:
                if self not in LIVE_CONNECTIONS:
                    LIVE_CONNECTIONS.append(self)
            log('tcp.log', '  .. [live] 注册连接 %s（共 %d）'
                % (self.client_address, len(LIVE_CONNECTIONS)))
        except Exception:
            pass

    def _unregister_live(self):
        _scene_leave(self)              # ★ AOI：断线即注销（会正常派发 leave）
        try:
            with LIVE_LOCK:
                if self in LIVE_CONNECTIONS:
                    LIVE_CONNECTIONS.remove(self)
        except Exception:
            pass

    counter = 0
    lock = threading.Lock()

    def handle(self):
        peer = '%s:%d' % self.client_address
        log('tcp.log', '=== connection from %s' % peer)
        self._register_live()          # ★ 登记为活跃连接（供热改推送）
        TcpHandler.lock.acquire()
        TcpHandler.counter += 1
        idx = TcpHandler.counter
        TcpHandler.lock.release()
        self.request.settimeout(600)
        total = 0
        parser = FrameParser()
        raw = open(os.path.join(LOGDIR, 'tcp_%d.bin' % idx), 'ab')
        try:
            while True:
                data = self.request.recv(65536)
                if not data:
                    break
                total += len(data)
                raw.write(data)
                raw.flush()
                log('tcp.log', '--- recv %d bytes (total %d) ---\n%s'
                    % (len(data), total, hexdump(data)))
                for cmd, body in parser.feed(data):
                    if cmd == 'BAD':
                        log('tcp.log', '  !! 解帧失败，丢弃缓冲 %s' % body.hex(' '))
                        continue
                    log('tcp.log', '  >> cmd=%d %s body(%d)=%s'
                        % (cmd, CMD_NAMES.get(cmd, '?'), len(body),
                           body[:48].hex(' ')))
                    # ★★ R49 多版本分流：把本连接记录的版本族刷进 CUR_VER
                    #   （build_* 据此产出对应字段布局）
                    # [P2B-migrated core/runtime.py] global CUR_VER  # (原模块全局，改为 runtime.CUR_VER)
                    # ★ PHASE 2.26：改走**线程局部**（`set_cur_ver`），修掉多版本并发覆盖竞态。
                    #   ⚠ 不要写回 `runtime.CUR_VER = ...`：那会创建真正的模块属性，
                    #     遮蔽 core/runtime.py 里 PEP 562 的线程局部读取。
                    runtime.set_cur_ver(getattr(self, '_ver_family', '1.4.9'))
                    # ★★ 2026-10-17 修：**单条命令出错不再掐断整条连接**。
                    #   原来这里直接 `self._reply(cmd, body)`，任何 handler 未捕获的异常都会
                    #   冒泡到 handle() 外层 `except Exception` ⇒ 记录 `--- error:` 并**关闭连接**
                    #   ⇒ 客户端立刻重连（实测表现为"重连风暴/进图半成品"）。
                    #   现在逐条兜住：完整落堆栈（便于继续修），连接保持，后续命令照常处理。
                    try:
                        self._reply(cmd, body)
                    except Exception as _e_cmd:
                        log('tcp.log', '  !! cmd=%d 处理异常（已兜住，连接保持）: %r'
                            % (cmd, _e_cmd))
                        log('tcp.log', '  !! 堆栈:\n' + traceback.format_exc())
        except socket.timeout:
            log('tcp.log', '--- idle timeout, closing ---')
        except Exception as e:
            # ★ 2026-10-17：连接级异常也落**堆栈**（原来只有 `%r`，定位不到是哪一行）
            log('tcp.log', '--- error: %r\n%s' % (e, traceback.format_exc()))
        finally:
            raw.close()
            self._unregister_live()    # ★ 从活跃连接中注销
            log('tcp.log', '=== closed %s (%d bytes total)' % (peer, total))

    def _send_10200(self, bid):
        """服务端主动下发"通知角色进入场景"。
        SCRoleEnter_10200{code:uint8, msg:string, bid:uint32,
                          line_id:uint8, x:uint16, y:uint16, dir:uint8}
        """
        _scene_ensure(self)                            # ★ AOI：进场景即登记（幂等）
        sp = self.cfg.get('spawn', {})
        role = role_with_saved_pos(self.cfg)          # ★ 用持久化坐标（重连后回到原位）
        # ★★★ R72 修复「切场景后主角模型不见了」（用户报障）
        #   原实现**无论切到哪个图都用同一个存档坐标**：切到 10005 时仍发
        #   `bid=10005 (91,56)` —— 而 (91,56) 是 **10001（史莱克城）** 的位置。
        #   目标图里这个格子很可能在图外/不可走 ⇒ 客户端摆不下主角 ⇒
        #   **模型建不出来**（表现就是"人在乾坤日月谷，但没有主角模型"）。
        #   ⇒ 只要目标场景 ≠ 存档场景，就用**目标地图的默认出生点**
        #     （`Config.Map[bid].def_x/def_y`，同一份 `config_map.json`）。
        _rx = int(role.get('x') or 100)
        _ry = int(role.get('y') or 100)
        _cur_scene = int(role.get('scene_id') or 0)
        if int(bid) and _cur_scene and int(bid) != _cur_scene:
            _mx, _my = map_def_xy(int(bid))
            if _mx or _my:
                log('tcp.log', '  .. 切场景 %d -> %d：坐标改用目标图默认点 (%d,%d)'
                    '（原存档 (%d,%d) 是别的图的）' % (_cur_scene, int(bid), _mx, _my, _rx, _ry))
                _rx, _ry = int(_mx), int(_my)
        role = dict(role, x=_rx, y=_ry)
        out = (w_u8(0) + w_str('') + w_u32(bid) +
               w_u8(sp.get('line_id', 1)) +
               w_u16(_rx) + w_u16(_ry) +
               w_u8(sp.get('dir', 0)))
        pkt = pack_frame(10200, out)
        self.request.sendall(pkt)
        # ★ R72：记住"刚刚把玩家放在哪个图的哪个点"，供 `15402`（挂机怪坐标）复用，
        #   否则两处各算一次坐标 → 怪生成在另一张图的坐标上 ⇒ 玩家看不见怪。
        #   ⚠ R77 教训：**不要**顺手把它落库 —— 实测客户端会用自己的位置上报
        #   （带它自己的 scene_id=10001）把 `roles.scene_id` 写回去，
        #   两边互相覆盖，落库这条路是错的。所以"当前场景"就用这个每连接状态。
        self._last_enter = (int(bid), _rx, _ry)
        log('tcp.log', '  << 10200 SCRoleEnter (server push) bid=%d (%d,%d) (%d bytes)'
            % (bid, _rx, _ry, len(pkt)))
        # 10201「场景图块信息()」：客户端也会主动请求（scene_controller.request10201），
        # 这里在进场景时先推一次，让它立刻有可渲染的单位。
        # ★★ R67 修复：原先这里写的是 `sp_bid = cfg['spawn'].bid`（**固定旧场景**），
        #   于是切场景后客户端拿到的还是**原场景**的 npcs/mons/elems
        #   ⇒ 新场景的单位集合是错的（挂机图里刷不出怪/看不到单位）。
        #   实测证据：`10200 ... bid=10005` 之后紧跟的 `10201` 里仍是 10001 的配置
        #   （`10201 SCMapGird ... mons=1`，那 1 只来自 10001）。
        #   改为用**传入的 `bid`**。
        sp_bid = int(bid or (self.cfg.get('spawn') or {}).get('bid') or 10001)
        # ★ R77：挂机怪已并入 `scene_mons()`（见那里的说明）⇒ 这里**不再单独追加**，
        #   保证 `10201`（下发）与 `20002`（校验点击）用的是**同一份列表**。
        _npcs, _mons = scene_quest_extras(self.cfg, sp_bid)
        _elems = scene_elems(sp_bid) if self.cfg.get('send_map_elems', True) else []
        pkt2 = pack_frame(10201, build_10201([role], _npcs, _mons, _elems))
        self.request.sendall(pkt2)
        log('tcp.log', '  << 10201 SCMapGird (server push) roles=1 npcs=%d mons=%d elems=%d (%d bytes)'
            % (len(_npcs), len(_mons), len(_elems), len(pkt2)))

    # -------------------------------------------------------------------
    # ★ Phase D：战斗推进与结算
    #
    # ⚠ 实测发现（logs/1.4.9/battle/battle_action.log）：
    #   SC_20010 能被客户端正确解析（探针 bt_in scFightData 拿到完整
    #   fighter_info_list），但客户端**既不发 CS_20011 也不发 CS_20014**
    #   ——也就是说它不会主动驱动回合。
    #   ⇒ 为了让"最小垂直闭环"在真机上确实跑完，服务端**自己按节拍推进**：
    #     SC_20010 → (SC_20012+SC_20013)×N → SC_20020 → SC_20023。
    #   CS_20014（客户端动画播完）仍然接收并记录，但**不作为推进的必要条件**
    #   （将来客户端行为正常后可改回事件驱动）。
    # -------------------------------------------------------------------

    BATTLE_ROUND_INTERVAL = 2.5     # 秒/回合（让客户端有时间播动画）

    def _battle_interval(self):
        """回合间隔（秒）。可由 config.json 的 `battle_round_interval` 覆盖
        —— 抓战斗画面时调大，让战斗场景停在屏幕上足够久。"""
        try:
            return float(self.cfg.get('battle_round_interval', 2.5))
        except Exception:
            return 2.5

    def _battle_tick(self):
        """推一个回合；结束则发 SC_20020 并安排结算。自续期，直到战斗结束。"""
        bt = getattr(self, 'battle', None)
        if bt is None:
            return
        try:
            self._battle_push_round()
        except Exception as e:
            log('tcp.log', '  !! battle tick failed: %r' % (e,))
            return
        if getattr(self, 'battle', None) is not None and not bt.finished:
            self._battle_timer(self._battle_interval(), self._battle_tick)

    def _battle_kick(self, first=False):
        """首次推进入口（SC_20010 之后调用）。"""
        bt = getattr(self, 'battle', None)
        if bt is None:
            return
        self._battle_round_sent = 1
        self._battle_tick()

    def _battle_push_round(self):
        """推进一个小回合：发 SC_20012 + SC_20013。

        依据见 server/battle.py 头注：SC_20010 之后由客户端 CS_20014 驱动回合。
        """
        bt = getattr(self, 'battle', None)
        if bt is None:
            log('tcp.log', '  !! 20014 收到但没有战斗实例（忽略）')
            return
        _rid = role_state(self.cfg).get('rid', 1001)  # [P3deep-migrated] 收敛 push_to_rid
        pkts = bt.play_round()
        for c, b in pkts:
            push_to_rid(_rid, pack_frame(c, b))
            log('tcp.log', '  << %d %s battle round=%d (%d bytes)'
                % (c, 'SC_20012 skill_play' if c == 20012 else 'SC_20013 round_start',
                   bt.round, len(b) + 6))
        for line in bt.log[-2:]:
            log('tcp.log', '  ** battle %s' % line)
        if bt.finished:
            pkt = pack_frame(20020, bt.build_20020())
            push_to_rid(_rid, pkt)
            log('tcp.log', '  << 20020 SC_20020 result=%d (%d bytes)'
                % (bt.result, len(pkt)))
            # ★★★ R82：**结算明细必须紧跟 20020 立刻发**（原先是 3 秒后由定时器发）。
            #   真机证据（19:41）：
            #       << 20020 result=1
            #       >> cmd=20021            ← 客户端**立刻**发 csCloseFinishView（关结束界面）
            #       << 20023（3 秒后才到）  ← 明细到得太晚，界面已关 ⇒ 用户看到"没有结算界面"
            #   ⇒ 现在把 `SC_20023`（以及战败时的 `SC_20022`）**同步发出**，
            #     经验/金币/落库这些**不影响界面**的结算仍留在定时器里做。
            try:
                _p23 = pack_frame(20023, bt.build_20023())
                push_to_rid(_rid, _p23)
                log('tcp.log', '  << 20023 SC_20023 type=0 result=%d role_hurl=2 (%d bytes) '
                               '[R82 紧跟 20020]' % (bt.result, len(_p23)))
                if int(getattr(bt, 'result', 0)) != 1:
                    _p22 = pack_frame(20022, w_u16(0))
                    push_to_rid(_rid, _p22)
                    log('tcp.log', '  << 20022 SC_20022 openBattleFail result=%d (%d bytes)'
                        % (bt.result, len(_p22)))
            except Exception as e:
                log('tcp.log', '  !! 20023/20022 即时发送失败: %r' % (e,))
            self._battle_sent_end = True
            self._battle_timer(3.0, self._battle_settle)

    def _battle_timer(self, delay, fn):
        t = threading.Timer(delay, fn)
        t.daemon = True
        t.start()

    def _battle_settle(self):
        """战斗结算：SC_20023 明细 + 经验/金币 + 任务击杀进度 + 落库 + 推送刷新。"""
        bt = getattr(self, 'battle', None)
        if bt is None or getattr(self, '_battle_settled', False):
            return
        self._battle_settled = True
        st = role_state(self.cfg)
        rid = st.get('rid', 1001)

        # ① 结算明细 —— ★ R82：**已在上一步紧跟 `20020` 同步发出**，这里只兜底
        #   （万一即时发送失败时还能补上）。
        if not getattr(self, '_battle_sent_end', False):
            pkt = pack_frame(20023, bt.build_20023())
            push_to_rid(rid, pkt)  # [P3deep-migrated] 收敛 push_to_rid
            log('tcp.log', '  << 20023 SC_20023 type=0 result=%d role_hurl=2 (%d bytes) '
                           '[兜底]' % (bt.result, len(pkt)))
            if int(getattr(bt, 'result', 0)) != 1:
                try:
                    _p22 = pack_frame(20022, w_u16(0))
                    push_to_rid(rid, _p22)
                    log('tcp.log', '  << 20022 SC_20022 openBattleFail result=%d (%d bytes)'
                        % (bt.result, len(_p22)))
                except Exception as e:
                    log('tcp.log', '  !! 20022 发送失败: %r' % (e,))

        mon = getattr(self, 'battle_mon', None) or {}
        mon_bid = int(mon.get('bid') or 0)
        delta = {}
        if bt.result == 1 and bt.mon_died:
            # ② 经验 / 金币
            #   ⚠ KILL_REWARD 是 **TEST_ONLY**（APK 里没有怪物经验/金币数据，
            #     见 analysis/1.4.9/battle/monster_data_model.md §3.1）
            delta = dict(battle_mod.KILL_REWARD)
            # ★ Phase E：经验走升级结算
            _exp_gain = int(delta.pop('exp', 0))
            # [P45-C] 击杀奖励统一走 grant（幂等去重）
            # ★ C3.3：reference_id 改为战斗实例级（on_20002 生成的 battle_settle_ref），
            #   使每次正常击杀独立结算；同实例重入/重放被 reward_log PK 挡住。
            _awards = [{'kind': 'asset', 'code': k, 'amount': int(v)}
                       for k, v in delta.items() if int(v)]
            _settle_ref = getattr(self, 'battle_settle_ref', None) or 'kill:%d:%d' % (mon_bid, rid)
            _kill_gr = grant(rid, _awards, reference_id=_settle_ref, source='battle')
            _now = db_get_assets(rid)

            # ③ 任务击杀进度 + exp + 掉落：全部纳入同一幂等门
            # ★ C3.3 核心修正：原实现 exp 在 grant 之前无条件直加、掉落也在幂等门外，
            #   导致同型怪第二次击杀 exp/掉落照常发、coin 却被旧键挡住。
            #   现统一：grant() 先查 reward_log，not already 才发 exp/coin/掉落/任务。
            if not _kill_gr.get('already'):
                # exp（原无条件直加，现纳入幂等门）
                if _exp_gain:
                    add_role_exp(self.cfg, rid, _exp_gain)
                log('tcp.log', '  ** battle kill mon=%s(bid=%s) -> +%d exp +%d coin '
                               '(TEST_ONLY 数值, settle_ref=%s, 现 exp=%s coin=%s)'
                    % (mon.get('id'), mon_bid, _exp_gain,
                       delta.get('coin', 0), _settle_ref, (_now or {}).get('exp'),
                       (_now or {}).get('coin')))

                # 任务击杀进度（★ 真实战斗驱动，不是替身）
                # ★ S3-A 任务3（G4）：与击杀奖励同一幂等键——同一 mon 的重复结算
                #   （重放/重入）奖励已被 reward_log 拦截，进度推进必须同步跳过，
                #   否则会出现"奖励不重复、进度却 +N"的不一致。
                prog = mission_progress_advance(rid, 'fight_mon', mon_bid, 1)
                # ★ C3.2-C I2（B分片接线）：kill_scene_mon 条件推进。
                #   配置证据：83 条 ["kill_scene_mon", <场景号>, <数量>]；target=场景号。
                #   触发点与 fight_mon 同一击杀幂等门（reward_log already）后，重复击杀不叠加。
                #   推进目标 = 战斗发生场景（CS_20002 记录的 self.battle_scene）。
                #   kill_type_mon：★ C5-A 已接线。类型映射取证完成（CONFIRMED）——
                #     target = **怪物类型码** = `Config.Mon.fields[4]`，不是 mon_bid。
                #     证据三重：fields[4]==8 的 15 只怪全名「狂暴魂兽」、fields[4]==12 的
                #     21 只全属邪魂师族；任务 75001–75006 名「狂暴魂兽」用码 8、
                #     75030「灭邪魂师」用码 12；客户端 mission_util 文案即
                #     '击杀%s/%s只狂暴魂兽' / '邪魂师%s/%s只'。
                try:
                    _bsc = int(getattr(self, 'battle_scene', 0) or 0)
                except Exception:
                    _bsc = 0
                if _bsc:
                    _p2 = mission_progress_advance(rid, 'kill_scene_mon', _bsc, 1)
                    if _p2:
                        log('tcp.log', '  ** battle mission progress: kill_scene_mon scene=%d -> %r'
                            % (_bsc, _p2))
                        prog = list(prog or []) + list(_p2 or [])
                # ★ C5-A：kill_type_mon —— 用**怪物类型码**推进（取不到类型则跳过，不猜）
                _mtype = mon_type_of(mon_bid)
                if _mtype is not None:
                    _p3 = mission_progress_advance(rid, 'kill_type_mon', _mtype, 1)
                    if _p3:
                        log('tcp.log', '  ** battle mission progress: kill_type_mon '
                                       'mon_bid=%d type=%d -> %r' % (mon_bid, _mtype, _p3))
                        prog = list(prog or []) + list(_p3 or [])
                if prog:
                    log('tcp.log', '  ** battle mission progress: fight_mon target=%d -> %r'
                        % (mon_bid, prog))
                    ms = mission_rows(self.cfg, rid)
                    push_to_rid(rid, pack_frame(12405, build_12400(ms)))
                    log('tcp.log', '  << 12405 SC_12405 update_mission_list=%d '
                                   '(战斗击杀驱动)' % len(ms))

                # ④ 掉落（★ C3.3：原无条件入包，现纳入幂等门）
                #   ★ 两层：
                #     (a) 先试 1.4.9 的 `Config.Drop`；但它的物品**全部不在真实物品表内**
                #         （模板残留，见 drop_model.md §9），`roll_drops` 会全部丢弃。
                #     (b) 因此回退到 **TEST_ONLY** 掉落：用**真实存在**的物品 id
                #         （默认 33001），只为把「掉落 → 进背包 → 重登仍在」链路跑通。
                #         **掉落规则/概率不是原版数据（UNKNOWN）。**
                drops = roll_drops(mon_bid)
                if not drops and self.cfg.get('battle_test_drop', True):
                    tb = int(self.cfg.get('battle_test_drop_item', 33001))
                    if is_valid_item(tb):
                        drops = [(tb, item_name(tb), 1,
                                  'TEST_ONLY（原版掉落表为死数据，物品 id 为真实物品）')]
                    else:
                        log('tcp.log', '  !! battle_test_drop_item=%d 不在真实物品表内，跳过'
                            % tb)
                if drops:
                    for item_bid, _iname, cnt, src in drops:
                        row = db_bag_add(rid, item_bid, cnt, BAG_MAIN)
                        log('tcp.log', '  ** battle drop item=%d(%s) x%d [%s] '
                                       '-> bag item_id=%s quantity=%s (%d 件)'
                            % (item_bid, _iname, cnt, src,
                               (row or {}).get('item_id'), (row or {}).get('quantity'),
                               len(db_bag_get(rid, BAG_MAIN))))
                    # 推送背包刷新（SC_10500 与 SC_10502 的 items 结构相同）
                    bag_push_frames(self, rid)
                else:
                    log('tcp.log', '  .. battle drop: mon %s 无掉落表或未抽中 '
                                   '（Config.Drop 仅覆盖 24/2645 只怪）' % mon_bid)
            else:
                log('tcp.log', '  ** battle settle already done ref=%s '
                               '(replay/async re-entry), skip exp/coin/drops/mission'
                    % _settle_ref)

        # ④.5 ★★ C3.3-E：镇魂塔结算 —— 活跃挑战会话 + 击杀塔 boss → 塔结算（幂等）
        #   触发条件：self.dung_challenge（由 13037 设置）+ 战斗胜利 + 击杀 mon==层 boss。
        #   奖励全部读 config_dungeon_tower 真实字段；grant 幂等键
        #     dung_settle:<bid>:<ceng>:<rid> —— 同层重放/重入不重复发奖。
        #   与通用 KILL_REWARD 解耦：通用 TEST_ONLY 奖励照常（本就极小），
        #     塔结算追加真实通关奖励并推 SC_21307。
        _dc = getattr(self, 'dung_challenge', None)
        if _dc and bt.result == 1 and bt.mon_died \
                and mon_bid == int(_dc.get('boss') or 0):
            _dc_bid = int(_dc.get('bid') or 0)
            _dc_ceng = int(_dc.get('ceng') or 0)
            if _dc_bid == _DUNG_TOWER_BID:
                _rw = tower_floor_reward(_dc_ceng) or {}
                _dref = 'dung_settle:%d:%d:%d' % (_dc_bid, _dc_ceng, rid)
                _aw = []
                _gain = []
                if _rw.get('asset'):
                    _atype, _aamt = _rw['asset']
                    _acode = _DUNG_REWARD_TYPE_TO_ASSET.get(int(_atype))
                    if _acode:
                        _aw.append({'kind': 'asset', 'code': _acode,
                                    'amount': int(_aamt)})
                        _gain.append((int(_atype), int(_aamt)))
                for _ibid, _icnt in (_rw.get('items') or []):
                    _aw.append({'kind': 'item', 'bid': int(_ibid),
                                'amount': int(_icnt)})
                _dgr = grant(rid, _aw, reference_id=_dref, source='dungeon_tower')
                if not _dgr.get('already'):
                    db_dung_set(rid, 'tower_clear', str(_dc_ceng), 1)
                    _cur_front = db_dung_get(rid, 'tower_floor', '21301', 1)
                    if _dc_ceng >= _cur_front:
                        db_dung_set(rid, 'tower_floor', '21301', _dc_ceng + 1)
                    log('tcp.log', '  ** 镇魂塔结算 rid=%d ceng=%d -> 通关奖励已发 '
                                   '(ref=%s gain=%s items=%s new_frontier=%d)'
                        % (rid, _dc_ceng, _dref, _gain, _rw.get('items'),
                           max(_cur_front, _dc_ceng + 1)))
                    # 推 SC_21307{bid, gain:T{type:u8,count:u32},
                    #              items:T{item_bid:u32,num:u8,is_bind:u8}}
                    _gb = w_u32(_dc_bid) + w_u16(len(_gain))
                    for _gt, _gc in _gain:
                        _gb += w_u8(_gt) + w_u32(_gc)
                    _gb += w_u16(len(_rw.get('items') or []))
                    for _ibid, _icnt in (_rw.get('items') or []):
                        _gb += w_u32(_ibid) + w_u8(_icnt) + w_u8(0)
                    push_to_rid(rid, pack_frame(21307, _gb))
                    log('tcp.log', '  << 21307 SC_21307 bid=%d gain=%d items=%d '
                                   '(%d bytes)'
                        % (_dc_bid, len(_gain), len(_rw.get('items') or []),
                           len(_gb)))
                else:
                    log('tcp.log', '  ** 镇魂塔结算 already done ref=%s '
                                   '(重放/重入)，跳过发奖与 21307' % _dref)
            self.dung_challenge = None

        # ⑤ 角色数据刷新（让经验条/金币/等级立刻更新）
        st2 = role_state(self.cfg)
        self.request.sendall(pack_frame(10302, build_10302(st2)))
        self.request.sendall(pack_frame(10301, build_10301(st2, self.cfg.get('skills', []))))
        self.request.sendall(pack_frame(10303,
            build_10303(st2, self.cfg.get('skills', []), self.cfg.get('attr'))))
        log('tcp.log', '  << 10301/10302/10303 (battle settle refresh) lev=%s exp=%s '
                       'coin=%s gold=%s' % (st2.get('lev'), st2.get('exp'),
                                            st2.get('coin'), st2.get('gold')))
        # ⑥ 收尾：清掉战斗实例，允许再次发起
        self.battle = None
        self.battle_mon = None
        self._battle_settled = False
        self.battle_settle_ref = None

    def _send_12831(self):
        """SC_12831{ id_list: table(id:u16, has_buy_num:u16) } —— 每个商品的已购次数。

        ★ 客户端拿它算"限购/剩余"（证据：`shop_model` proto#36 第 139-149 行
          `limit_num = Config.MallGoods[id].limit_week − checkChangesWeekdayData(id)`，
          其中 `checkChangesWeekdayData` 的缓存由 `on12831 → setWeekDataCache` 写入；
          proto#60 亦直接使用 `has_buy_num`）。
        ⇒ 购买成功后主动推一次，界面上的限购数字才会立刻变化。
        """
        _rid = role_state(self.cfg).get('rid', 1001)
        bought = db_mall_bought(_rid)
        goods = mall_cfg() or (self.cfg.get('shop_list') or [])
        out = w_u16(len(goods))
        for g in goods:
            gid = int(g.get('id', g.get('item_bid', 0)))
            out += w_u16(gid & 0xffff) + w_u16(int(bought.get(gid, 0)) & 0xffff)
        pkt = pack_frame(12831, out)
        self.request.sendall(pkt)
        log('tcp.log', '  << 12831 SC_12831 id_list=%d (%d bytes) 已购商品种类=%d'
            % (len(goods), len(pkt), len(bought)))
        return pkt

    def _reply(self, cmd, body):
        """按消息定义回包。"""
        # ★ Phase 2 step 0：DISPATCH_TABLE 兼容层（core/dispatch.py）。
        #   查表命中且新 handler 成功 -> return；未注册/handler 失败 -> None，
        #   继续走下面旧 if 链。step 0 表为空 ⇒ 恒 None，行为与拆分前完全一致。
        if dispatch is not None:
            try:
                _handled = dispatch.handle(cmd, self, body)
            except Exception:
                _handled = None
            if _handled is not None:
                return
        if cmd == 1199:
            # SCheartbeast_1199 { time:uint32 } —— 不回包客户端会判定掉线
            pkt = pack_frame(1199, w_u32(int(time.time()) & 0xFFFFFFFF))
            self.request.sendall(pkt)
            log('tcp.log', '  << 1199 heartbeat reply (%d bytes)' % len(pkt))
            # ★★ 12400 补推（见 10300 处的说明）：心跳是"客户端已稳定"的最好信号。
            if getattr(self, '_mis_repush_at', 0) and time.time() >= self._mis_repush_at:
                self._mis_repush_at = 0
                try:
                    _ms2 = mission_rows(self.cfg,
                                        role_state(self.cfg).get('rid', 1001))
                    if _ms2:
                        _pk = pack_frame(12400, build_12400(_ms2))
                        self.request.sendall(_pk)
                        log('tcp.log', '  << 12400 SC_12400 mission_list=%d '
                                       '(%d bytes) [补推/NpcCtrl 就绪后]'
                            % (len(_ms2), len(_pk)))
                except Exception as e:
                    log('tcp.log', '  !! 12400 补推失败: %r' % (e,))
            # ★ S1 第一分片：登录风暴收尾补推（F1 战力 + 日常活力）
            if getattr(self, '_login_repush_at', 0) and time.time() >= self._login_repush_at:
                self._login_repush_at = 0
                try:
                    _st = role_state(self.cfg)
                    # 10303（attr 大表 + power，真实计算；客户端 rgp_hander10303
                    #   → updateRoleAllAttr 就地刷新共享 RoleVo）
                    _pk = pack_frame(10303,
                        build_10303(_st, self.cfg.get('skills', []), self.cfg.get('attr')))
                    self.request.sendall(_pk)
                    log('tcp.log', '  << 10303 SC_10303 attr（S1 风暴收尾补推）(%d bytes)'
                        % len(_pk))
                    # ★ S1-B：补推 10302（完整资产刷新，尾部带 diamond/rainbow_diamond）。
                    #   根因：登录风暴只推 10301/10303/10305，从不推 10302；而 diamond
                    #   字段在 10302 的 1.4.11 尾部（build_10302 L5446-5448）⇒ 客户端
                    #   全程读不到 diamond ⇒ HUD 钻石停默认 0、商城余额校验失败。
                    #   值取 role_state['diamond'] = roles.diamond 真实存储（当前=0，
                    #   不伪造非零值）；CodeToAssets 无 diamond 标签，故只能走 10302 尾部。
                    _pk2 = pack_frame(10302, build_10302(_st))
                    self.request.sendall(_pk2)
                    log('tcp.log', '  << 10302 SC_10302 资产刷新（S1-B 补 diamond=%s）(%d bytes)'
                        % (_st.get('diamond', 0), len(_pk2)))
                    # 10306（attr 表 + mspd + power 小包；与 attribute.handler 同构）
                    _ad = role_attr_dict(self.cfg)
                    _pw = role_power(self.cfg)
                    _o = attr_table_10306(_ad)
                    _o += w_u16(int(_st.get('mspd', 0)) & 0xffff)
                    _o += w_u32(_pw & 0xffffffff)
                    self.request.sendall(pack_frame(10306, _o))
                    log('tcp.log', '  << 10306 SC_10306 mspd=%d power=%d（S1 风暴收尾补推）(%d bytes)'
                        % (int(_st.get('mspd', 0)), _pw, len(_o)))
                    # 13781（活跃度/活力，DB 驱动；与 CS_13781 handler 同构）
                    _rid = _st.get('rid', 1001)
                    _prog = db_daily_get(_rid)
                    _rows = []
                    for _t in richang_daily_tasks():
                        _hid = int(_t.get('huoli_id') or 0)
                        if _hid <= 0:
                            continue
                        _p = _prog.get(int(_t.get('id') or 0)) or {'num': 0, 'val': 0}
                        _rows.append((_hid, _p['num'], _p['val']))
                    _total = sum(r[2] for r in _rows) & 0xffff
                    _lq = db_daily_lingqu(_rid)
                    _o1 = w_u16(_total) + w_u16(len(_rows))
                    for _hid, _n, _v in _rows:
                        _o1 += w_u16(_hid & 0xffff) + w_u16(_n & 0xffff) + w_u16(_v & 0xffff)
                    _o1 += w_u16(len(_lq))
                    for _h in _lq:
                        _o1 += w_u16(_h & 0xffff)
                    self.request.sendall(pack_frame(13781, _o1))
                    log('tcp.log', '  << 13781 SC_13781 total_val=%d（S1 风暴收尾补推）' % _total)
                    # 13786（日常任务次数；与 CS_13786 handler 同构）
                    _rc = []
                    for _t in richang_daily_tasks():
                        _p = _prog.get(int(_t.get('id') or 0)) or {'num': 0, 'val': 0}
                        _rc.append((int(_t.get('id') or 0), _p['num']))
                    _o2 = w_u8(int(self.cfg.get('richang_week', 0)) & 0xff) + w_u16(len(_rc))
                    for _id, _n in _rc:
                        _o2 += w_u16(_id & 0xffff) + w_u16(_n & 0xffff)
                    _o2 += w_u16(0)  # status_list 空表
                    self.request.sendall(pack_frame(13786, _o2))
                    log('tcp.log', '  << 13786 SC_13786 richang=%d（S1 风暴收尾补推）' % len(_rc))
                except Exception as _e:
                    log('tcp.log', '  !! S1 登录收尾补推失败: %r' % (_e,))
            # ★★★ R71：`15402` 补推（**必须在 12400 之后**，见 10300 处的说明）
            if getattr(self, '_guaji_15402_at', 0) and time.time() >= self._guaji_15402_at:
                self._guaji_15402_at = 0
                try:
                    _mb4 = int(self.cfg.get('guaji_mission_bid') or 10010)
                    _sp4 = guaji_spot_for_lev(int(role_state(self.cfg).get('lev', 1))) or {}
                    _mp4 = int(_sp4.get('map_bid') or 0)
                    _le4 = getattr(self, '_last_enter', None)
                    if _le4 and int(_le4[0]) == int(_mp4):
                        _x4, _y4 = int(_le4[1]), int(_le4[2])
                    else:
                        _rp4 = role_with_saved_pos(self.cfg)
                        _x4 = int(_rp4.get('x') or 0)
                        _y4 = int(_rp4.get('y') or 0)
                    self.request.sendall(pack_frame(
                        15402, w_u32(_mb4) + w_u32(_mp4) + w_u32(_x4) + w_u32(_y4)))
                    db_guaji_update(role_state(self.cfg).get('rid', 1001), mission_bid=_mb4)
                    log('tcp.log', '  << 15402 补推（12400 落地之后）mission_bid=%d map_bid=%d '
                                   '(%d,%d) （R71 顺序修正）' % (_mb4, _mp4, _x4, _y4))
                except Exception as e:
                    log('tcp.log', '  !! 15402 补推失败: %r' % (e,))
            return
        if cmd == 10001:
            # CSFirstPack：手册里没有对应的 SC 消息，客户端只是"报个到"。
            # 先不回，观察客户端是否会自己发 1110。
            log('tcp.log', '  .. 10001 first pack, no SC reply defined')
            return
# [P2B-migrated dispatch/handler.py]         if cmd == 1110:
            # ★★ R44：账号登录 —— 改为**查账号表**返回该账号的角色列表
            #   （原先读 `config.json` 的 `roles`，与 DB 无关 ⇒ 无法多角色）。
            #   CS_1110{args:table(key:string, val:string)} —— 真机实测 10 对：
            #     account=dsh_local / timestamp / enter_srv_id / platform=ewan /
            #     device_id / getui_cid / idfa / token=dsh_token / channelId=1 / sign
            #   ⇒ 取 `account` 作 uid（真机 822 次恒为 `dsh_local`，与 DEFAULT_UID 一致）。
            #   ⚠ 其余键（token/idfa/channelId/sign…）协议里没有对应语义 ⇒ **不猜**，
            #     只记录键名，不据此做鉴权（原版走 token，本服不做会话层）。
#             args = {}
#             try:
#                 _n = struct.unpack_from('>H', body, 0)[0]
#                 _off = 2
#                 for _ in range(_n):
#                     _kl = struct.unpack_from('>H', body, _off)[0]; _off += 2
#                     _k = body[_off:_off + _kl].decode('utf-8', 'replace'); _off += _kl
#                     _vl = struct.unpack_from('>H', body, _off)[0]; _off += 2
#                     _v = body[_off:_off + _vl].decode('utf-8', 'replace'); _off += _vl
#                     args[_k] = _v
#             except Exception:
#                 args = {}
#             uid = db_account_ensure(args.get('account'))
#             self._uid = uid                     # ★ R44：供 CS_10101 建角时归属账号
            # ★★ R49：判定并记下该连接的客户端版本族（供 build_* 按版本产出布局）
#             self._ver_family = ver_family_of(len(body), args)
#             roles = db_roles_of_uid(uid)
#             pkt = pack_frame(1110, build_1110_roles(roles))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 1110 SCAccountLogin account=%s roles=%d keys=%s ver=%s (%d bytes)'
#                 % (uid, len(roles), sorted(args) or '(空args)',
#                    getattr(self, '_ver_family', '?'), len(pkt)))
#             return
        if cmd in (20021,):
            # ★★★ 2026-09-18 补实现：真机**实际发过**但服务端原先无人应答。
            #   CS_20021（空）—— 客户端在收到 SC_20020（战斗结果）后**主动上报**
            #   （实测：整场战斗里客户端唯一主动发的战斗消息）。
            #   ★ 定义里 **只有 CS、没有 SC** ⇒ **不需要回包**，只记日志即可。
            log('tcp.log', '  .. 20021 battle result ack from client (\u4e0d\u9700\u56de\u5305)')
            return
        if cmd == 10921:
            # SC_10921{world_lev:u8, next:u32, exp:u16, dec_exp:u16, open_day:u16}
            #   世界等级 / 盈福经验（客户端 wl_npc1 请求过）
            out = (w_u8(int(self.cfg.get('world_lev', 1)) & 0xFF) +
                   w_u32(int(self.cfg.get('world_lev_next', 0))) +
                   w_u16(int(self.cfg.get('world_lev_exp', 0)) & 0xFFFF) +
                   w_u16(int(self.cfg.get('world_lev_dec_exp', 0)) & 0xFFFF) +
                   w_u16(int(self.cfg.get('open_day', 1)) & 0xFFFF))
            pkt = pack_frame(10921, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10921 SC_10921 world_lev=%d (%d bytes)'
                % (int(self.cfg.get('world_lev', 1)), len(pkt)))
            return
        if cmd in (11206,):
            # 伙伴（hero）容量 / 上阵
            #   11206 CS{state:u8} → SC{code,msg,volume,volume_open}
            # ★★ R86：**`11216` 已从这里移出** —— 它在这段里只回"成功"、**不写入伙伴背包**，
            #   而后面（L6xxx）有一份**真正写库**的 `11216` 实现。
            #   本段在前 ⇒ 后者被**遮蔽**，表现就是"神将兑换有播放动画、但背包里没有"。
            #   （这就是 `lint_dispatch_shadow.py` 说的"分发顺序遮蔽"，
            #     此处是 **`if cmd in (…)` 遮蔽 `if cmd == …`** 的跨形式变体。）
            if cmd == 11206:
                out = (w_u8(1) + w_str('') +
                       w_u8(int(self.cfg.get('partner_volume', 200)) & 0xFF) +
                       w_u8(int(self.cfg.get('partner_volume_open', 200)) & 0xFF))
                pkt = pack_frame(11206, out)
                log('tcp.log', '  << 11206 SC_11206 volume=%d (%d bytes)'
                    % (int(self.cfg.get('partner_volume', 200)), len(pkt)))
            else:
                pb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                pkt = pack_frame(11216, w_u8(1) + w_str('') + w_u32(pb))
                log('tcp.log', '  << 11216 SC_11216 partner_bid=%d (%d bytes)' % (pb, len(pkt)))
            self.request.sendall(pkt)
            return
        if cmd in (12832, 12853):
            # 商城：购买结果 / 刷新信息
            #   12832 SC{code,msg,id,num}
            #   12853 SC{refresh_time,free_time,max_time,cost,count,limit_count}
            if cmd == 12832:
                # CS_12832{id:uint16, num:uint16}（AutoConstruct 权威规格）
                #   真机 body 8 字节 = id(2)+num(2) + 客户端缓冲区 4 字节残留
                #   （实测 `4e24 0001 | 138f0000` ⇒ id=20004, num=1；15 种样本同构）
                # ⚠ 旧实现按 u32 读 id、按 u32×2 回包 ⇒ 回包多 4 字节，且 id 被读成
                #   (id<<16|num)，与 SC 规格 code+msg+id:u16+num:u16 不符（由真机流量
                #   回放审计 tools/replay_captures.py 发现）。
                # ★ round42：走共用购买内核 shop_try_buy（与 13402 同一实现）。
                #   商品源 mall_cfg()（id=20004 已核实在 2001~20025 区间，非 zhenbao）。
                #   原先是“只回成功、不扣费不发货”的桩 —— 客户端显示购买成功而实际
                #   什么都没发生，比沉默更糟。
                mid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                num = struct.unpack_from('>H', body, 2)[0] if len(body) >= 4 else 1
                code, msg, g, total, bought_now = shop_try_buy(
                    self.cfg, mall_cfg(), mid, num)
                out = w_u8(code & 0xff) + w_str(msg) + w_u16(mid) + w_u16(num)
                pkt = pack_frame(12832, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 12832 SC_12832 id=%d num=%d code=%d (%d bytes)'
                    % (mid, num, code, len(pkt)))
                if code == 1:
                    rid = role_state(self.cfg).get('rid', 1001)
                    bag_push_frames(self, rid)
                    self._send_12831()
                    live_push(self.cfg, 'shop_buy')
            else:
                out = (w_u32(int(self.cfg.get('shop_refresh_time', 0))) +
                       w_u8(int(self.cfg.get('shop_free_time', 0)) & 0xFF) +
                       w_u8(int(self.cfg.get('shop_max_time', 0)) & 0xFF) +
                       w_u32(int(self.cfg.get('shop_refresh_cost', 0))) +
                       w_u8(int(self.cfg.get('shop_count', 0)) & 0xFF) +
                       w_u8(int(self.cfg.get('shop_limit_count', 0)) & 0xFF))
                pkt = pack_frame(12853, out)
                log('tcp.log', '  << 12853 SC_12853 (%d bytes)' % len(pkt))
            self.request.sendall(pkt)
            return
        if cmd == 17703:
            # ★ 装备强化/洗练结果（与背包/装备系统直接相关）
            #   CS{bag_code:u8, eqm_item_id:u32, inherit_id:u8, state:u8}
            #   → SC{code,msg,bag_code,eqm_item_id,eqm_item_id_new,eqm_item_bid_new,
            #        eqm_item_power_new,intensify_lev,refine,
            #        attr:table(state:u8, code:u8, value:u32)}
            bc = body[0] if len(body) >= 1 else 0
            eid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            # 查该装备当前 bid（按 item_id 定位），无则回 0
            cur_bid = 0
            try:
                con = db_conn()
                con.row_factory = sqlite3.Row
                row = con.execute('SELECT bid FROM equip_items WHERE rid=? AND item_id=?',
                                  (role_state(self.cfg).get('rid', 1001), eid)).fetchone()
                if row:
                    cur_bid = int(row['bid'])
                db_release(con)
            except Exception:
                pass
            out = (w_u8(1) + w_str('') + w_u8(bc) + w_u32(eid) + w_u32(eid) +
                   w_u32(cur_bid) + w_u32(0) + w_u8(0) + w_u16(0) + w_u16(0))
            pkt = pack_frame(17703, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 17703 SC_17703 bag_code=%d eqm=%d bid=%d code=1 (%d bytes)'
                % (bc, eid, cur_bid, len(pkt)))
            return
        if cmd in _UNSUPPORTED_ACTION_CMDS:
            # ★ round41：未实现的操作型命令 ⇒ **明确回失败**（而非沉默）
            #   理由：客户端有处理器、在等应答；回成功是撒谎，回失败是真话，
            #   沉默则让面板干等。与 2000x 家族的"本阶段不实现"处理一致。
            try:
                if not _fields_has_sc(cmd):     # ★ 2026-10-17：公共判定（原来直接摸缓存 ⇒ NameError）
                    log('tcp.log', '  .. %d 无 SC 定义（CS-only 上报型，不应答）' % cmd)
                    return
                out = _build_default_sc(cmd, code=0, msg=_UNSUPPORTED_MSG)
            except Exception as e:
                log('tcp.log', '  !! %d 未开放应答构建失败: %r' % (cmd, e))
                return
            pkt = pack_frame(cmd, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d code=0 未开放 (%d bytes)' % (cmd, cmd, len(pkt)))
            return
        # ★★★★ R151（修正）：**前部这段只管 `_GENERIC_DEFAULT_CMDS`**。
        #   为什么把 `global_default_sc` 从这里**移走**：
        #   本分支在 `_reply` 的**前部**，而专用分支从 L12000+ 开始
        #   ⇒ 只要范围放开到"所有有 SC 定义的命令"，**它就会抢先命中专用实现**
        #   （实测：`<< 10401 SC_10401 默认响应`，伙伴背包 18 → 0；
        #     门禁 E 一次报出 39 条）。**顺序即语义**。
        #   ⇒ `global_default_sc` 的兜底**放在 `_reply` 的末尾**（见该文件尾部
        #     "兜底响应" 那段）—— 能走到那里的，必然是**没人处理**的命令。
        if cmd in _GENERIC_DEFAULT_CMDS:
            # ★★★ 2026-09-18 补实现（体检）：这些 CMD **真机实际发过**、服务端原先无人应答，
            #   且其 SC 定义**不含未解子表**（`D|Dsc*|`）⇒ 可按规格生成**安全默认响应**。
            #
            #   ★ 策略（诚实优先）：
            #     · 第一个字段若名为 `code` ⇒ 回 1（成功），否则回 0
            #     · string → 空串；table → 空表(计数 0)；数值 → 0
            #     · **不编造任何具体数值/内容** —— 客户端拿到"成功但空"，
            #       不会卡死、也不会显示假数据；将来有真实数据再逐条填。
            try:
                if not _fields_has_sc(cmd):     # ★ 2026-10-17：公共判定（原来直接摸缓存 ⇒ NameError）
                    # ★ round36：防御性守卫 —— 本集合若混入 **CS-only 消息**
                    #   （协议里**根本没有 SC 定义**，如 CS_10999{msg:s}），回空帧是错的：
                    #   客户端没有该 cmd 的处理器，会落进未知命令分支。
                    #   ⇒ 正确行为是"不回应"。
                    #   ⚠ 注意区分：`SC_30715` 这类**有 SC 定义但字段为空**的消息
                    #   （fields=[]）必须照常回一个 0 字节 body 的帧；
                    #   因此判据是"缓存里有无该 cmd 的 SC 条目"，不是"字段列表非空"。
                    log('tcp.log', '  .. %d 无 SC 定义（CS-only 上报型，不应答）' % cmd)
                    return
                out = _build_default_sc(cmd)
            except Exception as e:
                log('tcp.log', '  !! %d \u9ed8\u8ba4\u54cd\u5e94\u6784\u5efa\u5931\u8d25: %r' % (cmd, e))
                return
            pkt = pack_frame(cmd, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d \u9ed8\u8ba4\u54cd\u5e94 (%d bytes)' % (cmd, cmd, len(pkt)))
            return
        if cmd == 12823:
            # ★★★ 2026-09-18 完善：伙伴列表（客户端 shop_ctrl.on12823，真机在发）
            #   CS{lev:u8} → SC{lev:u8, huoban_list:table(bid:u32, num:u8)}
            #   ★ 用**真实伙伴数据**（从 config_partner_base.luac 提取 53 个伙伴）
            #   语义推断：返回 take_lev <= 请求等级 的伙伴；num 定义未取证 ⇒ 用 1。
            lev = body[0] if len(body) >= 1 else 0
            pl = self.cfg.get('partner_list') or []
            sel = [p for p in pl if int(p.get('take_lev') or 0) <= max(lev, 0)]
            if not sel:
                sel = pl[:12]                      # 等级过低时至少给前几个，避免空列表
            out = w_u8(lev & 0xFF) + w_u16(len(sel))
            for p in sel:
                out += w_u32(int(p.get('bid', 0))) + w_u8(1)
            pkt = pack_frame(12823, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 12823 SC_12823 lev=%d huoban_list=%d (%d bytes)'
                % (lev, len(sel), len(pkt)))
            return
        if cmd == 18909:
            # ★★★ 金魂币商店已购列表（CS 空 → SC{buy_list: T(id:u16, buy_num:u16)}）
            #   客户端进金魂币页签时发，服务端返回 type=9 商品的已购次数。
            rid = role_state(self.cfg).get('rid', 1001)
            goods = [g for g in (mall_cfg() or [])
                     if int(g.get('type', -1)) == 9]
            bought = {}
            try:
                con = db_conn()
                con.row_factory = sqlite3.Row
                for r in con.execute('SELECT goods_id, num FROM mall_bought WHERE rid=?', (rid,)):
                    bought[int(r['goods_id'])] = int(r['num'] or 0)
                db_release(con)
            except Exception:
                pass
            bl = [(int(g.get('id', 0)), bought.get(int(g.get('id', 0)), 0))
                  for g in goods if int(g.get('id', 0))]
            out = w_u16(len(bl))
            for gid, bn in bl:
                out += w_u16(gid & 0xFFFF) + w_u16(bn & 0xFFFF)
            pkt = pack_frame(18909, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 18909 SC_18909 buy_list=%d (%d bytes)' % (len(bl), len(pkt)))
            return
        if cmd in (13401, 13403):
            # ★★★ 2026-09-18 完善：商城「列表 / 已购次数」（真机实际在发，type 对应 mall_config.type）
            #   13401 CS{type:u8} → SC{type:u8, buy_list:table(id:u16, buy_num:u16)}
            #         ★ buy_num = 该条目的**已购买次数**（查 mall_bought）
            #   13403 CS{type:u8} → SC{type:u8, item_list:table(item_bid:u32, price:u32)}
            #         ★ 用**真实商城配置**（server/mall_config.json，134 件，按 type 过滤）
            #   ⚠ 真机发包带 4 字节残留（如 `02 66 00 00 13`）⇒ 只读第 1 字节 type。
            mtype = body[0] if len(body) >= 1 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            goods = [g for g in (mall_cfg() or [])
                     if int(g.get('type', -1)) == mtype]
            if cmd == 13403:
                out = w_u8(mtype & 0xFF) + w_u16(len(goods))
                for g in goods:
                    out += (w_u32(int(g.get('item_bid', 0))) +
                            w_u32(int(g.get('price', 0))))
                pkt = pack_frame(13403, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 13403 SC_13403 type=%d item_list=%d (%d bytes)'
                    % (mtype, len(goods), len(pkt)))
                return
            # 13401：已购次数
            bought = {}
            try:
                con = db_conn()
                con.row_factory = sqlite3.Row
                for r in con.execute('SELECT goods_id, num FROM mall_bought WHERE rid=?', (rid,)):
                    bought[int(r['goods_id'])] = int(r['num'] or 0)
                db_release(con)
            except Exception:
                pass
            bl = [(int(g.get('id', 0)), bought.get(int(g.get('id', 0)), 0))
                  for g in goods if int(g.get('id', 0))]
            out = w_u8(mtype & 0xFF) + w_u16(len(bl))
            for gid, bn in bl:
                out += w_u16(gid & 0xFFFF) + w_u16(bn & 0xFFFF)
            pkt = pack_frame(13401, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 13401 SC_13401 type=%d buy_list=%d (%d bytes)'
                % (mtype, len(bl), len(pkt)))
            return
        if cmd == 11203:
            # 伙伴上阵/下阵（CS{bid:u32} → SC{code:u8, msg:str}）
            _pid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            out = w_u8(1) + w_str('')
            pkt = pack_frame(11203, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 11203 SC_11203 code=1 bid=%d (%d bytes)' % (_pid, len(pkt)))
            return
        if cmd == 17100:
            # 每日充值当天信息（CS空 → SC{day:u32, gold_num:u32, type_list: T(type:u8)}）
            # ★★ PHASE 2.36（用户需求：**完善充值系统**）：**修正功能归属错误**。
            #   原实现把它当成"**伙伴召唤信息**"（`day=1` / `gold_num=5`"免费召唤次数" /
            #   `types=[1,2]` —— **三个值全是编造**），导致每日充值面板显示的是无意义数据。
            #   证据：1.4.11 权威 `SC_17100 = {day__I, gold_num__I, type_list__T__type@C}`
            #   与 `config_every_charge` 的结构**精确吻合**：
            #     · `AllType.hash.normal[day]`   = `[null,1,2,3,4,5,6]`  ⇒ 当天开放的档位 seq
            #     · `TypeGold.hash.normal`       = `[null,60,300,980,1980,5000,10000]`
            #                                     ⇒ **各档对应的钻石额度**（我此前缺的"额度表"）
            #     · `EveryCharge.hash.normal[day][seq]` = `{coin,coupon,item{},senior_item{}}` 各档奖励
            #   本实现：
            #     `day`       = 1（本服无活动日历；`AllType` 各天的档位列表相同 ⇒ 取值等价）
            #     `gold_num`  = **当天真实充值所得钻石**（解析 `reward_log` 里 `source='charge'`
            #                   的 reference_id `charge:{rid}:{元}:{ts}`，按 `ChargeList` 折算成钻石）
            #     `type_list` = **`AllType.normal[day]`**（当天开放档位）
            _rid171 = role_state(self.cfg).get('rid', 1001)
            _day171 = 1
            try:
                import json as _j171
                _p171 = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                                     'config_every_charge.json')
                _ec171 = _j171.load(open(_p171, encoding='utf-8'))
            except Exception as _e171:
                log('tcp.log', '  !! 17100 读 config_every_charge 失败: %r' % (_e171,))
                _ec171 = {}
            _at171 = (((_ec171.get('AllType') or {}).get('hash') or {}).get('normal') or {})
            _row171 = _at171.get(str(_day171)) or []
            if _row171 and _row171[0] is None:
                _row171 = _row171[1:]
            _types171 = []
            for _x171 in _row171:
                try:
                    _types171.append(int(_x171) & 0xff)
                except Exception:
                    pass
            if not _types171:                       # 配置缺失兜底：按 TypeGold 的档位数
                _tg171 = (((_ec171.get('TypeGold') or {}).get('hash') or {}).get('normal') or [])
                _types171 = list(range(1, max(0, len(_tg171) - 1) + 1)) or [1]
            # 当天真实充值钻石额
            _gn171 = 0
            try:
                import sqlite3 as _sq171
                import time as _t171
                _cl171 = {}
                try:
                    import json as _j171b
                    _p171b = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                                          'config_charge.json')
                    _cl171 = (_j171b.load(open(_p171b, encoding='utf-8')).get('ChargeList') or {})
                except Exception:
                    _cl171 = {}
                _gold_of171 = {}
                for _k171, _v171 in _cl171.items():
                    _h171 = (_v171.get('hash') or {})
                    try:
                        _gold_of171[int(_h171.get('val') or _k171)] = int(_h171.get('gold') or 0)
                    except Exception:
                        pass
                _con171 = _sq171.connect(os.path.join(os.path.dirname(HERE), 'server',
                                                      'state', 'roles.db'))
                _refs171 = _con171.execute(
                    "SELECT reference_id, granted_ts FROM reward_log "
                    "WHERE rid=? AND source='charge'", (_rid171,)).fetchall()
                _con171.close()
                _today171 = int(_t171.time()) // 86400
                for _rf171, _ts171 in _refs171:
                    try:
                        if int(_ts171) // 86400 != _today171:
                            continue
                    except Exception:
                        continue
                    _ps171 = str(_rf171 or '').split(':')
                    if len(_ps171) >= 3 and _ps171[0] == 'charge':
                        try:
                            _gn171 += _gold_of171.get(int(_ps171[2]), 0)
                        except Exception:
                            pass
            except Exception as _eg171:
                log('tcp.log', '  !! 17100 统计当日充值失败: %r' % (_eg171,))
                _gn171 = 0
            out = w_u32(_day171)                    # day
            out += w_u32(_gn171 & 0xffffffff)       # gold_num = 当天充值所得钻石（真值）
            out += w_u16(len(_types171))            # type_list count
            for _t171x in _types171:
                out += w_u8(_t171x)
            pkt = pack_frame(17100, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 17100 SC_17100 day=%d gold_num=%d（当日真实充值钻石）'
                ' types=%s (%d bytes)' % (_day171, _gn171, _types171, len(pkt)))
            return
        if cmd == 16701:
            # CS{vip_lev:u8} → SC{get_info: T(vip_lev:u8, get_award:u8)}
            _vip = int(role_state(self.cfg).get('vip_lev', 0) or 0)
            _req_vip = body[0] if len(body) >= 1 else 0
            _show = _req_vip or _vip
            out = w_u16(1) + w_u8(_show & 0xff) + w_u8(0)
            pkt = pack_frame(16701, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 16701 SC_16701 vip_lev=%d get_award=0 (%d bytes)' % (_show, len(pkt)))
            return
        if cmd == 13901:
            # 充值商品列表（CS空 → SC{month_card_timeout:u32,
            #   charge_list: T(use_val:u32, get_val:u32, add_val:u32,
            #                  ico:u8, pic:u8, is_first:u8),
            #   is_imperial_card:u8, charge_return_rate:u32}）
            #   use_val=支付(RMB分), get_val=得钻石, add_val=赠送钻石
            # ★ PHASE 2.33（用户需求：**点击充值档位直接获得对应钻石**）：
            #   档位改为读 **`config_charge.ChargeList`**（9 档真配置），不再硬编码假档位。
            #   配置字段：`val`(元) `gold`(基础钻石) `add`(常驻赠送) `first_add`(首充加赠)
            #             `ico` `pic` `type`
            #   `use_val` 按 **RMB 分**下发（val×100），与客户端"支付金额"单位一致。
            try:
                import json as _json139
                _p139 = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_charge.json')
                _cl = (_json139.load(open(_p139, encoding='utf-8')).get('ChargeList') or {})
            except Exception as _e139:
                log('tcp.log', '  !! 13901 读 config_charge 失败: %r' % (_e139,))
                _cl = {}
            tiers = []
            for _k139 in sorted(_cl, key=lambda x: int(x) if str(x).isdigit() else 0):
                _h139 = (_cl[_k139].get('hash') or {})
                _v139 = int(_h139.get('val') or (_k139 if str(_k139).isdigit() else 0))
                tiers.append((_v139 * 100,                       # use_val：RMB 分
                              int(_h139.get('gold') or 0),       # get_val：钻石
                              int(_h139.get('add') or 0),        # add_val：常驻赠送
                              int(_h139.get('ico') or 0) & 0xff,
                              int(_h139.get('pic') or 0) & 0xff,
                              1))                                # is_first
            if not tiers:                                        # 配置缺失兜底（不空表）
                tiers = [(600, 60, 0, 1, 1, 1)]
            out = w_u32(0)  # month_card_timeout
            out += w_u16(len(tiers))  # charge_list count
            for uv, gv, av, ico, pic, first in tiers:
                out += w_u32(uv) + w_u32(gv) + w_u32(av)
                out += w_u8(ico) + w_u8(pic) + w_u8(first)
            out += w_u8(0)  # is_imperial_card
            out += w_u32(1000)  # charge_return_rate
            pkt = pack_frame(13901, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 13901 SC_13901 charge_list=%d（来自 config_charge.ChargeList）'
                '(%d bytes)' % (len(tiers), len(pkt)))
            return
        if cmd == 16900:
            # 累积充值可领取状态（CS空 → SC{charge:u32, status: table(key:u32, state:u8)}）
            # ★ PHASE 2.16：`charge` 改为**真值** —— 读 `growth_target.service.state()` 的
            #   `role_gt.total_charge`（与 `30502 领取充值奖励` 的门槛**同一数据源**，
            #   避免"面板显示 0 但后端另有累计值"的两套口径）。
            #   `status` 仍回**空表**：各档 `key`/`state` 的取值语义未取证 ⇒ 不编造。
            _rid90 = role_state(self.cfg).get('rid', 1001)
            try:
                from growth_target.service import state as _gt_state
                _chg = int((_gt_state(_rid90) or {}).get('total_charge') or 0)
            except Exception as _e90:
                _chg = 0
                log('tcp.log', '  !! 16900 读 total_charge 失败: %r' % (_e90,))
            out = w_u32(_chg & 0xffffffff)   # charge = 累计充值（真值）
            # ★★ PHASE 2.35（用户需求：**完善充值系统**）：`status` 由**空表**改为**逐档下发**。
            #   `SC_16900.status = T{key:u32, state:u8}`：
            #     `key`   = 里程碑键（来自 `config_once_charge.OnceCharge`，实为 1/2/3）
            #     `state` = 该档**当前可能领取**（1）/ 不可领（0）
            #   判定与 `16901` 的发放**同一口径**（`total_charge > 0`；额度字段配置里没有 ⇒ 未编造），
            #   并排除**已领取**的档 —— 用 `reward.service.reward_log(rid, 'charge_once:{rid}:{key}')`
            #   （与 `16901` 的 reference_id 完全一致，两边不会各说各话）。
            #   ⇒ 面板能正确标出"哪个档可领"，与 `16901` 配对闭环。
            _oc90 = {}
            try:
                import json as _j90
                _p90 = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                                    'config_once_charge.json')
                _oc90 = (_j90.load(open(_p90, encoding='utf-8')).get('OnceCharge') or {})
            except Exception as _e90b:
                log('tcp.log', '  !! 16900 读 config_once_charge 失败: %r' % (_e90b,))
                _oc90 = {}
            _keys90 = []
            for _k90 in _oc90:
                try:
                    _keys90.append(int(_k90))
                except Exception:
                    pass
            _keys90.sort()
            _st90 = []
            for _k90 in _keys90:
                _done90 = False
                try:
                    from reward.service import reward_log as _rl90
                    _done90 = bool(_rl90(_rid90, 'charge_once:%d:%d' % (_rid90, _k90)))
                except Exception:
                    _done90 = False
                _st90.append((_k90, 1 if ((_chg > 0) and not _done90) else 0))
            out += w_u16(len(_st90))         # status count
            for _k90, _s90 in _st90:
                out += w_u32(_k90) + w_u8(_s90)
            pkt = pack_frame(16900, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 16900 SC_16900 charge=%d status=%s（逐档可领状态）'
                % (_chg, _st90))
            return
        # ============================================================
        # ★★ round44：副本 / 爬塔进度系统骨架
        #   CMD 13005/13034/13036/13045/13052/13058、21301。
        #   背景：这 7 条原在 _GENERIC_DEFAULT_CMDS 回全零/空表，副本/爬塔页空白。
        #   本轮目标：查询型应答做成"结构正确 + 关键数值非零 + 进度落库"。
        #   ★ 不做进本战斗/刷怪/结算（后续轮次）；string 一律空串、奖励表先空表
        #     （避免发无效 bid/code 崩客户端，见红线）。
        # ============================================================
        if cmd == 21301:
            # 爬塔主界面（CS空 → SC{tower_id:u32, floor:u32, is_effect:u32,
            #   clear_list: T{floor,first_clear_id,first_clear_srvid,first_clear_name,
            #                best_clear_id,best_clear_srvid,best_clear_name},
            #   is_clear:u8, daily_floors:u8}）
            rid = role_state(self.cfg).get('rid', 1001)
            _fl = db_dung_get(rid, 'tower_floor', '21301', 1)
            out = (w_u32(1) +          # tower_id
                   w_u32(_fl) +        # floor = 当前层
                   w_u32(0) +          # is_effect
                   w_u16(0) +          # clear_list count = 空
                   w_u8(0) +           # is_clear
                   w_u8(0))            # daily_floors
            self.request.sendall(pack_frame(21301, out))
            log('tcp.log', '  << 21301 tower floor=%d (%d bytes)' % (_fl, len(out)))
            return
        if cmd == 13045:
            # 爬塔某层详情（CS{floor:u32} → SC{floor,rid,srv_id,name,
            #   fast_rid,fast_srv_id,fast_name,first_get:u8}）
            _f = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 1
            out = (w_u32(_f) + w_u32(0) + w_str('') + w_str('') +
                   w_u32(0) + w_str('') + w_str('') + w_u8(0))
            self.request.sendall(pack_frame(13045, out))
            log('tcp.log', '  << 13045 floor=%d (%d bytes)' % (_f, len(out)))
            return
        if cmd == 13052:
            # 副本选择界面（CS空 → SC{select_hard,section,hard,challenge,
            #   left_times:u8, assets: T{assets_code:u8,num:u32}}）
            rid = role_state(self.cfg).get('rid', 1001)
            _lt = db_dung_get(rid, 'dung_left', '13052', 5)
            out = (w_u8(0) +           # select_hard
                   w_u8(1) +           # section
                   w_u8(1) +           # hard
                   w_u8(0) +           # challenge
                   w_u8(_lt & 0xff) +  # left_times
                   w_u16(0))           # assets count = 空（不编进本消耗）
            self.request.sendall(pack_frame(13052, out))
            log('tcp.log', '  << 13052 section=1 hard=1 left_times=%d (%d bytes)' % (_lt, len(out)))
            return
        if cmd == 16704:
            # ★★★ R103：**VIP 状态** —— 原先落通用默认响应
            #   SC_16704{vip_lev:uint8, status:uint8}
            #   ★ 数据源是 `roles` 表的**真实字段 `vip_level`**（不是猜的）。
            #   `status` 的语义未取证；这里按"有 VIP 等级才置 1"推导（vip_level=0 ⇒ status=0），
            #   是一个**有依据的推导**，不是编造数值。
            # ★★ R140b：**改为 DB 直读** —— 原先用 `role_state(self.cfg).get('vip_level')`，
            #   而那是**会话缓存的旧值**（实测 DB 里 vip_level=3 却读成 0）。
            _vl = db_vip_level(role_state(self.cfg).get('rid', 1001)) & 0xff
            _out = w_u8(_vl) + w_u8(1 if _vl > 0 else 0)
            self.request.sendall(pack_frame(16704, _out))
            log('tcp.log', '  << 16704 SC_16704 vip_lev=%d status=%d (%d bytes)'
                % (_vl, 1 if _vl > 0 else 0, len(_out) + 6))
            return
        if cmd == 10932:
            # ★★★ R103：**双倍经验 / 离线挂机状态** —— 原先落通用默认响应
            #   SC_10932{double:u16, double_sum:u16, double_state:u16, off_state:u16}
            #   ★ `off_state` 数据源（C3.3-D 订正）：本服 guaji_state.off_on 列——
            #     由 10933（开）/10934（关）显式写入，重启/重登持久化恢复。
            #     （旧实现用「有无行」判 off_state，但在线 ghost 链 15402 也会建行，
            #      会把"行存在"误报成"离线挂机开启"——本批复为按显式开关列判定。）
            #   `double/double_sum/double_state` 语义未取证，且本服**没有双倍经验系统**
            #      ⇒ 回 0（"没有双倍"是真话，不是占位）。
            _off = 0
            try:
                _off = int(db_guaji_state(role_state(self.cfg).get('rid', 1001))['off_on'])
            except Exception:
                _off = 0
            _out = w_u16(0) + w_u16(0) + w_u16(0) + w_u16(_off)
            self.request.sendall(pack_frame(10932, _out))
            log('tcp.log', '  << 10932 SC_10932 double=0 off_state=%d (%d bytes)'
                % (_off, len(_out) + 6))
            return
        if cmd == 10933:
            # ★★★ C3.3-D：**开启离线挂机**（CS 空 → SC{code:u8, msg:string}）
            #   反汇编直证：客户端收 code==1 → toast「离线挂机开启成功」+ off_state=1。
            #   服务端权威：
            #     · 等级门禁 = config_function id=504「挂机」open_lev=30（有配置证据）；
            #     · 写 guaji_state.off_on=1 + off_started_at=服务端时间戳（防回拨锚点；
            #       本批收益=BLOCKED，不发任何奖励，仅落状态）；
            #     · 重复开启幂等：已开 ⇒ 仍回 code=1（客户端再弹一次成功无害），日志记录。
            _rid = role_state(self.cfg).get('rid', 1001)
            _lev = int(role_state(self.cfg).get('lev', 1) or 1)
            _before = db_guaji_state(_rid)
            if _lev < 30:
                _out = w_u8(0) + w_str('离线挂机需30级开启')
                self.request.sendall(pack_frame(10933, _out))
                log('tcp.log', '  << 10933 code=0 rid=%d lev=%d <30 拒绝开启离线挂机'
                    % (_rid, _lev))
                return
            db_guaji_update(_rid, off_on=1, off_started_at=int(time.time()))
            log('tcp.log', '  ** 10933 离线挂机开启 rid=%d lev=%d off_on: %d→1 '
                           'off_started_at=%d（收益 BLOCKED 不发放）'
                % (_rid, _lev, _before['off_on'], int(time.time())))
            self.request.sendall(pack_frame(10933, w_u8(1) + w_str('')))
            log('tcp.log', '  << 10933 SC_10933 code=1(离线挂机开启成功)')
            return
        if cmd == 10934:
            # ★★★ C3.3-D：**关闭离线挂机**（CS 空 → SC{code:u8, msg:string}）
            #   反汇编直证：客户端收 code==1 → toast「离线挂机关闭成功」+ off_state=0。
            #   服务端权威：写 guaji_state.off_on=0（保留该行——在线 ghost 链的
            #   loop_count/mission_bid/kill_count 不被误删）。重复关闭幂等。
            _rid = role_state(self.cfg).get('rid', 1001)
            _before = db_guaji_state(_rid)
            db_guaji_update(_rid, off_on=0)
            log('tcp.log', '  ** 10934 离线挂机关闭 rid=%d off_on: %d→0'
                % (_rid, _before['off_on']))
            self.request.sendall(pack_frame(10934, w_u8(1) + w_str('')))
            log('tcp.log', '  << 10934 SC_10934 code=1(离线挂机关闭成功)')
            return
        if cmd == 17312:
            # ★★★ R103：**竞速领奖** —— 此前**完全无处理器**（点了没反应）
            #   CS_17312{type:uint8} → SC_17312{code:uint8, msg:string}
            #   ★ 竞速**没有奖励配置源**（`config_game_data`/`config_week_calendar` 只是
            #     文字里提到"竞速"，不是奖励表）⇒ **不假装成功**：回 `code=0` + 诚实 msg，
            #     让客户端给出明确反馈，而不是静默无响应、也不是假发奖。
            _t12 = body[0] if len(body) >= 1 else 0
            _out = w_u8(0) + w_str('本服未配置竞速奖励')
            self.request.sendall(pack_frame(17312, _out))
            log('tcp.log', '  << 17312 SC_17312 code=0（type=%d，本服无竞速奖励配置）'
                % _t12)
            return
        if cmd == 17306:
            # ★ R103：**竞速奖励列表** —— 无奖励档位配置 ⇒ **空表 + 登记理由**（门禁 E）
            #   SC_17306{reward_list:table(type:u8, num:u8, status:u8)}
            self.request.sendall(pack_frame(17306, w_u16(0)))
            log('tcp.log', '  << 17306 SC_17306 reward_list=0（本服无竞速奖励配置）')
            return
        if cmd == 17308:
            # ★ R103：**竞速排行榜** —— 本服 `roles` **只有 1 个角色** ⇒ 空是真话
            #   CS{start_rank:u32, end_rank:u32} → SC{rank_list:table(role_name,rid,srid,
            #     rank,career,sex,score,lev,win_num)}
            self.request.sendall(pack_frame(17308, w_u16(0)))
            log('tcp.log', '  << 17308 SC_17308 rank_list=0（本服仅 1 个角色）')
            return
        if cmd == 17310:
            # ★ R103：**竞速积分分布** —— 分数段人数需要多玩家 ⇒ 本服空是真话
            #   SC_17310{score_list:table(grade:u32, number:u32)}
            self.request.sendall(pack_frame(17310, w_u16(0)))
            log('tcp.log', '  << 17310 SC_17310 score_list=0（本服仅 1 个角色）')
            return
        _rid197 = role_state(self.cfg).get('rid', 1001)
        if cmd == 15204:
            # ★★★ R197：**NPC（`SC{num:u8, gold:u8}`）升级为真实数据** —— 配置取证：
            #   · `npc_ctrl` 的字符串常量 = ["gold", "num", ...] ⇒ ★ **与 SC 的字段名逐名对应**
            #   · `npc_contants` 有 **17 个常量**（BtID_Gold/BtID_Coin/…）⇒ ★ `num` 的依据
            #   · `config_npc` 的 `Config.Npc` = {NPC id ⇒ 模型 id}（303 项）⇒ NPC 系统**存在**
            #   ★ 判据（R134）：`num` = **配置项数**（客观）；`gold` = **本服玩家的金币**（DB）。
            _gold = 0
            try:
                # ★ 正确读法（R197b）：`db_get_assets(rid)` 返回 `{'gold':…, 'coin':…}`
                _gold = int((db_get_assets(_rid197) or {}).get('gold') or 0)
            except Exception:
                _gold = 0
            _out = w_u8(kconst_count('npc_contants') & 0xff) + w_u8(_gold & 0xff)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 15204 SC_15204 num=%d gold=%d（NPC 常量数 + 玩家金币）'
                % (kconst_count('npc_contants') & 0xff, _gold & 0xff))
            return

        if cmd == 19600:
            # ★★★ R196：**每日签到** —— ★ 用 **`config_checkin`（95 条）** 生成 `list`
            #   （B 类原判据是"`list` 档位找不到配置表" ⇒ **现在找到了**）
            #   ★ 判据（R134）：`list` 的"**条目数**"有客观依据（配置条数）⇒
            #     **条目数与配置一致** + 其余字段给 0/递增 ⇒ 结构正确且比空表好。
            _ty = body[0] if body else 0
            _n = kconst_count('config_checkin') or 0
            # ★ R196b：**按权威 SC 生成 `n` 条元素**（不再手写字段 —— 手写已错 6 次）
            _out = w_u8(_ty) + sym_list_bytes(19600, 'list', _n)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 19600 SC_19600 签到档位=%d（来自 config_checkin）' % _n)
            return

        if cmd in (16000, 16001, 16002, 16100, 16101, 16102, 16110, 16111,
                    16112, 16202, 16300, 16301, 16302, 16303, 16304, 16401,
                    16404, 16501, 16502, 16604, 16610, 16611):
            # ★★★ R178：**`16xxx` 22 条** —— ★ 逐条按各自 SC。
            _rid78 = role_state(self.cfg).get('rid', 1001)
            _rs78 = role_state(self.cfg)
            _nm78 = str(_rs78.get('name') or '')
            _ty78 = body[0] if body else 0
            if cmd == 16102:
                _q = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _a = body[4] if len(body) >= 5 else 0
                _out = w_u8(0) + w_u8(0) + w_u8(_a) + w_u32(_q)
            elif cmd == 16112:
                _q = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _n = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _out = w_u8(0) + w_u8(0) + w_u16(_n)
                for _i in range(_n):
                    _out += w_u16(struct.unpack_from('>H', body, 6 + 2 * _i)[0])
                _out += w_u32(_q)
            elif cmd == 16202:
                _mb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = (w_u32(_mb) + w_u8(0) + w_u32(0) + w_u16(0) + w_u16(0) +
                        w_u32(0) + w_u8(0))
            elif cmd == 16300:
                _el = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = (w_u32(_el) + w_u32(_rid78) + w_str('1') + w_str(_nm78) +
                        w_u16(0) + w_u16(0) + w_u8(0) + w_u32(0))
            elif cmd == 16301:
                _r = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _ok = 1 if _r in (0, _rid78) else 0
                _out = w_u16(0) + w_u8(_ok) + w_u32(_r or _rid78) + w_str(_sv or '1') + w_str('')
            elif cmd == 16401:
                _b = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _b else 0) + w_str('') + w_u32(_b)
            elif cmd == 16502:
                # {type:u8, val:u16} → {tips:u16, msg, type, val}  ⇒ ★ 回显（别落 else）
                _v = struct.unpack_from('>H', body, 1)[0] if len(body) >= 3 else 0
                _out = w_u16(1) + w_str('') + w_u8(_ty78) + w_u16(_v)
            else:
                # 其余 16 条：结构正确的 0/空（用权威默认构造器）
                _out = _build_default_sc(cmd, 1, '')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 16xxx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    16612, 16613, 16614, 16615, 16616, 16617, 16620, 16621, 16622, 16623, 16624, 16626,
                    16627, 16630, 16631, 16632, 16633, 16634, 16635, 16636, 16637, 16638, 16639, 16640,
                    16641, 16642, 16643, 16646, 16647, 16649, 16650, 16651, 16652, 16653, 16665, 16666,
                    16667, 16668, 16693, 16694, 16695, 16696, 16697, 16698, 16699, 16700, 16702, 16703,
                    16705, 16901
        ):
            # ★★★ R179：**收尾 `16xxx`（50 条）** —— ★ 逐条按各自 SC（数据驱动）
            _rid79 = role_state(self.cfg).get('rid', 1001)
            _nm79 = str(role_state(self.cfg).get('name') or '')
            _o79 = 1
            if cmd == 16613:
                # {srv_id:string, name:string, type:u8, item_id:u32, num:u32} ⇒ ★ 真实角色名
                _out = w_str('1') + w_str(_nm79) + w_u8(0) + w_u32(0) + w_u32(0)
            elif cmd == 16700:
                _out = w_u8(db_vip_level(_rid79) & 0xff) + w_u8(0)
            elif cmd == 16702:
                _out = w_u16(1) + w_str('') + w_u8(0)
            elif cmd == 16901:
                # ★★ PHASE 2.34（用户需求：**完善充值系统** —— 不真实花钱、不外接充值接口）：
                #   `16901 领取累计充值奖励 CS{key:u32}` —— 原走在通用回执里**只回 {code,msg}、不发奖**。
                #   现按 **`config_once_charge.OnceCharge`**（3 个里程碑）**真发奖**：
                #     · `item`        —— 通用奖励（`[null,bid,cnt,?]`）
                #     · `senior_item` —— 职业限定奖励（`distinguish_career==1` 时按玩家 `career` 取末位）
                #   幂等：走 `RewardService.grant` + `reference_id=charge_once:{rid}:{key}`
                #         ⇒ 同一档**只发一次**（重连/重复点击不会重复发）。
                #   ⚠ **门槛未取证**：`OnceCharge` 配置里**没有**"该里程碑对应多少累计充值"的字段
                #     ⇒ 现取 `total_charge > 0`（有过充值）作门槛，**不编造额度**；
                #     日后拿到额度表，**替换点就是下面 `_need134` 这一行**。
                _key134 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _need134 = 1                       # ← 唯一替换点：里程碑额度（UNKNOWN）
                _ocf134 = {}
                try:
                    import json as _j134
                    _p134 = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                                         'config_once_charge.json')
                    _ocf134 = (_j134.load(open(_p134, encoding='utf-8')).get('OnceCharge') or {})
                except Exception as _e134:
                    log('tcp.log', '  !! 16901 读 config_once_charge 失败: %r' % (_e134,))
                    _ocf134 = {}
                _oc134 = (_ocf134.get(str(_key134)) or {}).get('hash')
                _tc134 = 0
                try:
                    from growth_target.service import state as _gs134
                    _tc134 = int((_gs134(_rid79) or {}).get('total_charge') or 0)
                except Exception:
                    _tc134 = 0
                if _oc134 is None:
                    _out = w_u8(0) + w_str('无此档位')
                elif _tc134 < _need134:
                    _out = w_u8(0) + w_str('累计充值不足')
                else:
                    _aw134 = []
                    for _rk134, _row134 in (_oc134.get('item') or {}).items():
                        try:
                            _aw134.append({'kind': 'item', 'bid': int(_row134[1]),
                                           'amount': int(_row134[2])})
                        except Exception:
                            pass
                    if int(_oc134.get('distinguish_career') or 0) == 1:
                        _car134 = int(role_state(self.cfg).get('career') or 1)
                        for _rk134, _row134 in (_oc134.get('senior_item') or {}).items():
                            try:
                                if len(_row134) >= 5 and int(_row134[4]) == _car134:
                                    _aw134.append({'kind': 'item', 'bid': int(_row134[1]),
                                                   'amount': int(_row134[2])})
                            except Exception:
                                pass
                    _done134 = False
                    try:
                        from reward.service import grant as _g134
                        _res134 = _g134(_rid79, _aw134,
                                        'charge_once:%d:%d' % (_rid79, _key134),
                                        source='charge_once')
                        _done134 = bool((_res134 or {}).get('ok'))
                    except Exception as _eg134:
                        log('tcp.log', '  !! 16901 发奖失败: %r' % (_eg134,))
                    _out = w_u8(1 if _done134 else 0) + w_str('')
                    log('tcp.log', '  << 16901 领取累计充值奖励 key=%d ⇒ %s（%d 项，累计充值=%d）'
                        % (_key134, '已发' if _done134 else '失败', len(_aw134), _tc134))
            elif cmd in (16616, 16617, 16622, 16627, 16632, 16642, 16643,
                         16647, 16650, 16652, 16698):
                # ★ **回显型**：逐条按 spec 的 `code,msg` + 回显字段
                _out = w_u8(1) + w_str('')
                if cmd == 16616:
                    _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                    _out += w_str(body[2:2 + _sl].decode('utf-8', 'replace')) + w_u32(0)
                elif cmd == 16617:
                    _out += w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0) + w_u32(0)
                elif cmd in (16622, 16652):
                    # ★ 16622 的 `index` 是 **u8**；★ 16652 的 `index` 是 **u32**（读宽度别混）
                    if cmd == 16622:
                        _out += w_u8(body[0] if body else 0) + w_u16(0) + w_u8(0)
                    else:
                        _ix32 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                        _out += w_u32(_ix32) + w_u8(0)
                elif cmd == 16627:
                    _out += w_u8(body[0] if body else 0)
                elif cmd == 16632:
                    _v = [struct.unpack_from('>I', body, i)[0] if len(body) >= i + 4 else 0
                          for i in (0, 4)]
                    _t = body[8] if len(body) >= 9 else 0
                    _bc = struct.unpack_from('>I', body, 9)[0] if len(body) >= 13 else 0
                    _out += (w_u32(_v[0]) + w_u32(_v[1]) + w_u8(_t) + w_u32(_bc) +
                             w_u8(0) + w_u8(0))
                elif cmd == 16643:
                    _out += w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0)
                elif cmd == 16642:
                    _out += (w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0) +
                             w_u16(struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0))
                elif cmd == 16647:
                    _out += (w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0) +
                             w_u8(body[4] if len(body) >= 5 else 0) +
                             w_u8(body[5] if len(body) >= 6 else 0))
                elif cmd == 16650:
                    _out += w_u8(body[0] if body else 0)
                elif cmd == 16698:
                    _out += (w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0) +
                             w_u32(0) + w_u16(0))
            elif cmd == 16649:
                _out = w_u8(body[0] if body else 0) + w_u8(0) + w_u32(0)
            elif cmd == 16646:
                # {type:u8, list:table<…>, **countdown:u32**}（★ `countdown` 是**顶层**字段，别漏）
                _out = w_u8(body[0] if body else 0) + w_u16(0) + w_u32(0)
            elif cmd in (16612, 16624, 16631, 16633, 16635, 16668, 16615, 16621,
                         16651, 16665, 16667, 16693, 16694, 16696, 16697, 16626,
                         16630, 16614, 16620, 16634, 16636, 16637, 16638, 16641,
                         16640, 16639, 16666, 16646, 16705):
                _out = _build_default_sc(cmd, 1, '')   # ★ 内联（R167 曾因"引用未定义的名字"崩过）
            else:
                # 16623/16653/16703/16901 等 `{code,msg}`
                _ne = any(body) if body else False
                _out = w_u8(1 if (_ne or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 16xxx 收尾（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (13200, 13201, 13202, 13204, 13210, 13218, 13226, 13237):
            # ★★★ PHASE2（组队 132xx）：**真实实现** —— 落库 `role_team`。
            #   ★ 此前：`13200`/`13201` 走 R191 通用编码器（回执/空表），
            #     `13210`/`13226` 走 `{tips,msg}` 集合、`13218` 走 R189、`13237` 走 R182 族
            #     ⇒ 全是"假成功"：队伍不落库、查不到。
            #   ★ 字段级依据：`protocol/fields.json`（`cmd_resolve_132.luac`）⇒ CONFIRMED。
            #   ★ `role_team` 表结构为**兼容层**（原版队伍表不可取证）⇒ INFERENCE。
            _st_t = role_state(self.cfg)
            _rid_t = int(_st_t.get('rid', 1001))
            _nm_t = str(_st_t.get('name') or '')
            _lv_t = int(_st_t.get('lev') or 1) & 0xff
            _ca_t = int(_st_t.get('career') or 0) & 0xffff
            _sx_t = int(_st_t.get('sex') or 0) & 0xff
            _pw_t = role_power_of(_rid_t)

            def _t_member(m):
                # SC_13200.team_member_list 元素（11 字段，见 fields.json）
                return (w_u32(int(m.get('rid') or 0)) + w_str(str(m.get('srv') or '')) +
                        w_str(str(m.get('name') or '')) + w_u8(int(m.get('lev') or 1) & 0xff) +
                        w_u16(int(m.get('career') or 0) & 0xffff) +
                        w_u8(int(m.get('sex') or 0) & 0xff) + w_u32(0) + w_u8(0) +
                        w_u32(int(m.get('hp') or 0)) + w_u32(int(m.get('hp_max') or 0)) +
                        w_u32(int(m.get('power') or 0)))

            if cmd == 13201:                       # 创建队伍  CS[] → {tips:u16,msg}
                _ok_t, _msg_t, _tm_t = db_team_create(_rid_t, _nm_t, '', _lv_t, _ca_t, _sx_t, _pw_t)
                _out = w_u16(1 if _ok_t else 0) + w_str(_msg_t)
                log('tcp.log', '  ** 13201 建队 rid=%d ok=%s tid=%s'
                    % (_rid_t, _ok_t, (_tm_t or {}).get('team_id')))
            elif cmd == 13210:                     # 退出队伍  CS[] → {tips:u16,msg}
                _ok_t, _msg_t = db_team_leave(_rid_t)
                _out = w_u16(1 if _ok_t else 0) + w_str(_msg_t)
                log('tcp.log', '  ** 13210 离队 rid=%d ok=%s msg=%r' % (_rid_t, _ok_t, _msg_t))
            elif cmd == 13226:                     # 解散队伍  CS[] → {tips:u16,msg}
                _ok_t, _msg_t = db_team_disband(_rid_t)
                _out = w_u16(1 if _ok_t else 0) + w_str(_msg_t)
                log('tcp.log', '  ** 13226 解散 rid=%d ok=%s msg=%r' % (_rid_t, _ok_t, _msg_t))
            elif cmd == 13200:                     # 队伍信息  CS[]
                _tm_t = db_team_of(_rid_t)
                if _tm_t is None:
                    _out = (w_str('') + w_u32(0) + w_str('') + w_u32(0) + w_str('') +
                            w_u32(0) + w_u16(0))
                else:
                    _mem = _tm_t['members']
                    _out = (w_str('') + w_u32(_tm_t['team_id']) + w_str(_tm_t['leader_srv'] or '') +
                            w_u32(_tm_t['leader_rid']) + w_str(_tm_t['leader_srv'] or '') +
                            w_u32(0) + w_u16(len(_mem)))
                    for _m in _mem:
                        _out += _t_member(_m)
                log('tcp.log', '  << 13200 SC_13200 tid=%s members=%d'
                    % ((_tm_t or {}).get('team_id', 0), len(_tm_t['members']) if _tm_t else 0))
            elif cmd == 13218:                     # 组队大厅  CS[] → {team_list:table}
                _ts_t = db_team_hall()
                _out = w_u16(len(_ts_t))
                for _t in _ts_t:
                    _ld = _t['members'][0] if _t['members'] else {}
                    for _m in _t['members']:
                        if int(_m.get('rid') or 0) == int(_t['leader_rid']):
                            _ld = _m
                            break
                    _out += (w_u32(_t['team_id']) + w_str(_t['leader_srv'] or '') +
                             w_u32(_t['leader_rid']) + w_str(_t['leader_srv'] or '') +
                             w_str(str(_ld.get('name') or '')) +
                             w_u8(int(_ld.get('lev') or 1) & 0xff) +
                             w_u16(int(_ld.get('career') or 0) & 0xffff) +
                             w_u16(int(_ld.get('sex') or 0) & 0xffff) +
                             w_u8(len(_t['members']) & 0xff) + w_u8(4))
                log('tcp.log', '  << 13218 SC_13218 teams=%d（role_team 真实条目）' % len(_ts_t))
            elif cmd == 13202:                     # 邀请入队  CS{member_id:u32,member_srv_id}
                _tg_i = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _tm_i = db_team_of(_rid_t)
                if _tm_i is None:
                    _out = w_u16(0) + w_str('不在队伍中')
                elif int(_tm_i['leader_rid']) != _rid_t:
                    _out = w_u16(0) + w_str('只有队长可以邀请')
                elif not _tg_i or _tg_i == _rid_t:
                    _out = w_u16(0) + w_str('无效的邀请对象')
                elif db_team_of(_tg_i) is not None:
                    _out = w_u16(0) + w_str('对方已在队伍中')
                else:
                    # 目标必须真实存在（避免给任意 rid 发邀请）
                    if not db_get_role(_tg_i):
                        _out = w_u16(0) + w_str('目标不存在')
                    else:
                        db_team_invite_add(_tm_i['team_id'], _rid_t, _tg_i)
                        _ld_i = _tm_i['members'][0] if _tm_i['members'] else {}
                        for _m in _tm_i['members']:
                            if int(_m.get('rid') or 0) == int(_tm_i['leader_rid']):
                                _ld_i = _m
                                break
                        _p_i = (w_u32(_rid_t) + w_str('') + w_str(str(_ld_i.get('name') or _nm_t)) +
                                w_u8(_lv_t) + w_u8(_ca_t & 0xff) + w_u32(_tm_i['team_id']) +
                                w_str('') + w_u8(len(_tm_i['members']) & 0xff) + w_u8(4) + w_u8(1))
                        _nn = push_to_rid(_tg_i, pack_frame(13203, _p_i))
                        _out = w_u16(1) + w_str('')
                        log('tcp.log', '  ** 13202 邀请 rid=%d -> %d（推送 %d 连接）'
                            % (_rid_t, _tg_i, _nn))
            elif cmd == 13204:                     # 应答邀请  CS{is_ok:u8,ok_id:u32,ok_srv_id}
                _ok_i = body[0] if body else 0
                _inv_i = db_team_invite_of(_rid_t)
                if _inv_i is None:
                    _out = w_u8(0) + w_str('没有待处理的邀请') + w_u32(0) + w_str('')
                else:
                    _tid_i = int(_inv_i['team_id'])
                    db_team_invite_del(_inv_i['invite_id'])
                    if _ok_i:
                        _me_i = {'rid': _rid_t, 'srv': '', 'name': _nm_t, 'lev': _lv_t,
                                 'career': _ca_t, 'sex': _sx_t, 'power': _pw_t}
                        _ok2_i, _m2_i = db_team_add_member(_tid_i, _me_i)
                        # 推 13200 给队伍所有在线成员（让其刷新成员列表）
                        _tm_i2 = db_team_get(_tid_i)
                        if _tm_i2:
                            for _m in _tm_i2['members']:
                                _p_i2 = (w_str('') + w_u32(_tm_i2['team_id']) +
                                         w_str(_tm_i2['leader_srv'] or '') +
                                         w_u32(_tm_i2['leader_rid']) +
                                         w_str(_tm_i2['leader_srv'] or '') + w_u32(0) +
                                         w_u16(len(_tm_i2['members'])))
                                for _mm in _tm_i2['members']:
                                    _p_i2 += _t_member(_mm)
                                push_to_rid(int(_m.get('rid') or 0), pack_frame(13200, _p_i2))
                        _out = w_u8(1 if _ok2_i else 0) + w_str(_m2_i) + w_u32(_rid_t) + w_str('')
                        log('tcp.log', '  ** 13204 接受邀请 rid=%d team=%d ok=%s'
                            % (_rid_t, _tid_i, _ok2_i))
                    else:
                        _out = w_u8(0) + w_str('已拒绝') + w_u32(_rid_t) + w_str('')
                        log('tcp.log', '  ** 13204 拒绝邀请 rid=%d team=%d' % (_rid_t, _tid_i))
            else:                                  # 13237 查看目标玩家队伍  CS{rid:u32,srv_id}
                _tg_t = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _tm_t = db_team_of(_tg_t) if _tg_t else None
                if _tm_t is None:
                    _out = w_u32(0) + w_str('') + w_u8(0) + w_u32(0) + w_str('') + w_str('')
                else:
                    _ld = _tm_t['members'][0] if _tm_t['members'] else {}
                    _out = (w_u32(_tm_t['team_id']) + w_str(_tm_t['leader_srv'] or '') +
                            w_u8(len(_tm_t['members']) & 0xff) + w_u32(0) + w_str('') +
                            w_str(str(_ld.get('name') or '')))
                log('tcp.log', '  << 13237 SC_13237 target=%d tid=%s'
                    % (_tg_t, (_tm_t or {}).get('team_id', 0)))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (19505, 19512, 19514, 19524, 19530, 19533, 19536):
            # ★★★ PHASE2（结拜/金兰 195xx）：**真实实现** —— 落库 `role_jiebai`。
            #   ★ 此前：`19514`/`19530`/`19536` 走 R187 默认生成、`19505`/`19533` 走 R181-D 回执
            #     ⇒ 全是"假成功"：结拜不落库、结拜空间查不到。
            #   ★ 字段：`protocol/fields.json`（`cmd_resolve_195.luac`）⇒ CONFIRMED。
            #     ⚠ `SC_19514`/`SC_19530` **没有 code/msg**（首字段就是 jid / member_list）⇒ 不能加。
            #   ★ `role_jiebai` 表结构为兼容层 ⇒ INFERENCE。
            _st_j = role_state(self.cfg)
            _rid_j = int(_st_j.get('rid', 1001))
            _nm_j = str(_st_j.get('name') or '')
            _lv_j = int(_st_j.get('lev') or 1)
            _ca_j = int(_st_j.get('career') or 0)
            _sx_j = int(_st_j.get('sex') or 0)
            _pw_j = role_power_of(_rid_j)

            def _jb_mem_info(m):
                # SC_19514.member_list 元素（13 字段）
                return (w_u32(int(m.get('rid') or 0)) + w_str(str(m.get('srv') or '')) +
                        w_str(str(m.get('name') or '')) + w_u8(int(m.get('sort') or 1) & 0xff) +
                        w_u8(int(m.get('sex') or 0) & 0xff) +
                        w_u8(int(m.get('career') or 0) & 0xff) +
                        w_str(str(m.get('second_name') or '')) +
                        w_u32(int(m.get('trophy') or 0)) +
                        w_u8(int(m.get('lev') or 1) & 0xff) +
                        w_u32(int(m.get('jieyi') or 0)) +
                        w_u32(int(m.get('jieyi_total') or 0)) +
                        w_u8(1) + w_u32(0))          # is_online=1, offline_time=0

            if cmd == 19505:                         # 发起结拜  CS[] → {code,msg}
                _ok_j, _msg_j, _jb = db_jiebai_create(_rid_j, _nm_j, '', _lv_j, _ca_j, _sx_j, _pw_j)
                _out = w_u8(1 if _ok_j else 0) + w_str(_msg_j)
                log('tcp.log', '  ** 19505 发起结拜 rid=%d ok=%s jid=%s'
                    % (_rid_j, _ok_j, (_jb or {}).get('jid')))
            elif cmd == 19533:                       # 取消结拜  CS[] → {code,msg}
                _ok_j, _msg_j = db_jiebai_cancel(_rid_j)
                _out = w_u8(1 if _ok_j else 0) + w_str(_msg_j)
                log('tcp.log', '  ** 19533 取消结拜 rid=%d ok=%s msg=%r' % (_rid_j, _ok_j, _msg_j))
            elif cmd == 19524:                       # 邀请加入结拜  CS{rid:u32,srv_id} → {code,msg,rid,srv_id}
                _tg_j = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _jbj = db_jiebai_of(_rid_j)
                if _jbj is None:
                    _out = w_u8(0) + w_str('尚未结拜') + w_u32(_tg_j) + w_str('')
                elif int(_jbj['leader_rid']) != _rid_j:
                    _out = w_u8(0) + w_str('只有发起人可以邀请') + w_u32(_tg_j) + w_str('')
                elif not _tg_j or _tg_j == _rid_j:
                    _out = w_u8(0) + w_str('无效对象') + w_u32(_tg_j) + w_str('')
                elif db_jiebai_of(_tg_j) is not None:
                    _out = w_u8(0) + w_str('对方已有结拜') + w_u32(_tg_j) + w_str('')
                else:
                    _trow_j = db_get_role(_tg_j)
                    if not _trow_j:
                        _out = w_u8(0) + w_str('目标不存在') + w_u32(_tg_j) + w_str('')
                    else:
                        _memj = {'rid': _tg_j, 'srv': '', 'name': str(_trow_j.get('name') or ''),
                                 'sort': len(_jbj['members']) + 1,
                                 'sex': int(_trow_j.get('sex') or 0) & 0xff,
                                 'career': int(_trow_j.get('career') or 0) & 0xff,
                                 'second_name': str(_trow_j.get('name') or ''),
                                 'trophy': 0, 'lev': int(_trow_j.get('level') or 1) & 0xff,
                                 'jieyi': 0, 'jieyi_total': 0, 'is_leader': 0}
                        _okj, _mj = db_jiebai_add_member(_jbj['jid'], _memj)
                        if _okj:
                            # 推 19511（通知成员开始确认结拜）
                            _jb2j = db_jiebai_get(_jbj['jid'])
                            _p11 = (w_u8(1) + w_str('') + w_u8(1) + w_u16(len(_jb2j['members'])))
                            for _m in _jb2j['members']:
                                _p11 += (w_u32(int(_m.get('rid') or 0)) + w_str('') +
                                         w_u8(int(_m.get('confirm') or 0) & 0xff))
                            _p11 += w_u32(0)
                            push_to_rid(_tg_j, pack_frame(19511, _p11))
                        _out = w_u8(1 if _okj else 0) + w_str(_mj) + w_u32(_tg_j) + w_str('')
                        log('tcp.log', '  ** 19524 邀请结拜 rid=%d -> %d ok=%s'
                            % (_rid_j, _tg_j, _okj))
            elif cmd == 19512:                       # 确认结拜  CS{flag:u8} → {code,msg}
                _flag_j = body[0] if body else 1
                _jbk = db_jiebai_of(_rid_j)
                if _jbk is None:
                    _out = w_u8(0) + w_str('尚未结拜')
                else:
                    if _flag_j:
                        db_jiebai_set_confirm(_jbk['jid'], _rid_j, 1)
                    elif int(_jbk['leader_rid']) != _rid_j:
                        # 拒绝 ⇒ 移出（发起人不可移除）
                        _jbk['members'] = [m for m in _jbk['members']
                                           if int(m.get('rid') or 0) != _rid_j]
                        db_jiebai_save(_jbk)
                    _jb3 = db_jiebai_get(_jbk['jid'])
                    _done_j = db_jiebai_all_confirmed(_jb3)
                    for _m in ((_jb3 or {}).get('members') or []):
                        push_to_rid(int(_m.get('rid') or 0),
                                    pack_frame(19513, w_u8(1 if _done_j else 0) + w_str('')))
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 19512 确认结拜 rid=%d flag=%d all_confirmed=%s'
                        % (_rid_j, _flag_j, _done_j))
            elif cmd == 19536:                       # 提升结拜空间等级  CS[] → {code,msg,jlev}
                _jb = db_jiebai_of(_rid_j)
                if _jb is None:
                    _out = w_u8(0) + w_str('尚未结拜') + w_u8(0)
                else:
                    _jb['lev'] = int(_jb.get('lev') or 1) + 1
                    db_jiebai_save(_jb)
                    _out = w_u8(1) + w_str('') + w_u8(_jb['lev'] & 0xff)
                    log('tcp.log', '  ** 19536 结拜升级 rid=%d jlev=%d' % (_rid_j, _jb['lev']))
            elif cmd == 19530:                       # 成员列表  CS[] → {member_list, end_time}
                _jb = db_jiebai_of(_rid_j)
                if _jb is None:
                    _out = w_u16(0) + w_u32(0)
                else:
                    _mem = _jb['members']
                    _out = w_u16(len(_mem)) + w_u32(0)
                    for _m in _mem:
                        # SC_19530 元素 9 字段
                        _out += (w_u32(int(_m.get('rid') or 0)) + w_str(str(_m.get('srv') or '')) +
                                 w_str(str(_m.get('name') or '')) +
                                 w_u8(int(_m.get('is_leader') or 0) & 0xff) +
                                 w_u8(int(_m.get('sex') or 0) & 0xff) +
                                 w_u8(int(_m.get('career') or 0) & 0xff) +
                                 w_u32(int(_m.get('power') or 0)) +
                                 w_str(str(_m.get('second_name') or '')) +
                                 w_u8(int(_m.get('sort') or 1) & 0xff))
                log('tcp.log', '  << 19530 SC_19530 members=%d'
                    % (len(_jb['members']) if _jb else 0))
            else:                                    # 19514 打开结拜空间  CS[]
                _jb = db_jiebai_of(_rid_j)
                if _jb is None:
                    # ⚠ 无 code/msg：jid=0 + 各字段零值
                    _out = (w_u32(0) + w_str('') + w_str('') + w_u8(0) + w_str('') + w_u8(0) +
                            w_str('') + w_u32(0) + w_str('') + w_u16(0) + w_u8(0) + w_u8(0) +
                            w_u32(0) + w_u32(0) + w_str('') + w_str('') + w_u32(0) + w_str('') +
                            w_str('') + w_u16(0))
                else:
                    _mem = _jb['members']
                    _lead = _nm_j
                    for _m in _mem:
                        if int(_m.get('is_leader') or 0):
                            _lead = str(_m.get('name') or _nm_j)
                            break
                    _out = (w_u32(_jb['jid']) + w_str('') + w_str(_jb['front_name']) +
                            w_u8(len(_mem) & 0xff) + w_str(_jb['end_name']) +
                            w_u8(int(_jb['lev']) & 0xff) + w_str(_lead) +
                            w_u32(int(_jb['exp'])) + w_str(_jb['notice']) + w_u16(len(_mem)))
                    for _m in _mem:
                        _out += _jb_mem_info(_m)
                    _out += (w_u8(0) + w_u8(0) + w_u32(0) + w_u32(0) + w_str('') + w_str('') +
                             w_u32(0) + w_str('') + w_str('') + w_u16(0))
                log('tcp.log', '  << 19514 SC_19514 jid=%s members=%d'
                    % ((_jb or {}).get('jid', 0), len(_jb['members']) if _jb else 0))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (18300, 18302, 18313, 18314, 18316, 18318, 18321, 18322):
            # ★★★ PHASE2（结婚 183xx）：**真实状态层** —— 落库 `role_marry`。
            #   ★ 此前：`18313` 恒回 1、`18318` 恒回 state=0、`18322` 只回显 skill_id
            #     ⇒ 婚姻状态**从不落库**、离婚/婚戒进阶全是空转。
            #   ★ 字段：`protocol/fields.json`（`cmd_resolve_183.luac`）⇒ CONFIRMED。
            #   ★ `role_marry` 为兼容层 ⇒ INFERENCE。
            #   ⚠ `18300`（发起求婚）**需要第二角色**；本服单角色 ⇒ **诚实失败**（不编造）。
            _rid_m = int(role_state(self.cfg).get('rid', 1001))
            _rm = db_marry_get(_rid_m)
            if cmd == 18300:                         # 发起求婚  CS[] → {code,msg}
                # ★ 目标**不在 CS 里**（空消息）⇒ 由服务端意向表决定（见 db_marry_propose_init）
                _int = db_marry_propose_get(_rid_m)
                if _int is None:
                    _out = w_u8(0) + w_str('暂无求婚对象')
                    log('tcp.log', '  ** 18300 求婚 rid=%d ⇒ 无意向对象' % _rid_m)
                else:
                    _to_m = int(_int['to_rid'])
                    _trow = db_get_role(_to_m)
                    if not _trow or _to_m == _rid_m:
                        _out = w_u8(0) + w_str('求婚对象无效')
                    elif _rm['state'] != 0 or db_marry_get(_to_m)['state'] != 0:
                        _out = w_u8(0) + w_str('对方或自己已有婚约')
                    else:
                        # 推 SC_18301 给被求婚者（obj_rid = 发起者）
                        _st_m = role_state(self.cfg)
                        _my_name = str(_st_m.get('name') or '')
                        _my_sex = int(_st_m.get('sex') or 0)
                        _to_name = str((_trow or {}).get('name') or '')
                        _boy = _my_name if _my_sex == 0 else _to_name
                        _gril = _to_name if _my_sex == 0 else _my_name
                        _p1 = (w_u8(0) + w_u8(0) + w_str(_boy) + w_str(_gril) +
                               w_u32(_rid_m) + w_str(''))
                        _nn = push_to_rid(_to_m, pack_frame(18301, _p1))
                        _out = w_u8(1) + w_str('')
                        log('tcp.log', '  ** 18300 求婚 rid=%d -> %d（推送 %d 连接）'
                            % (_rid_m, _to_m, _nn))
            elif cmd == 18302:                       # 求婚应答  CS{ret:u8} → {code,msg}
                _ret_m = body[0] if body else 0
                _prop = db_marry_propose_of_target(_rid_m)
                if _prop is None:
                    _out = w_u8(0) + w_str('没有待处理的求婚')
                else:
                    _from_m = int(_prop['from_rid'])
                    db_marry_propose_del(_from_m)
                    _from_name = str((db_get_role(_from_m) or {}).get('name') or '')
                    _me_name = str(role_state(self.cfg).get('name') or '')
                    if _ret_m:
                        db_marry_set(_rid_m, _from_m, _from_name, 1)
                        db_marry_set(_from_m, _rid_m, _me_name, 1)
                        _out = w_u8(1) + w_str('')
                        for _r in (_rid_m, _from_m):
                            push_to_rid(_r, pack_frame(18303, w_u8(1) + w_u8(1) + w_str('')))
                        log('tcp.log', '  ** 18302 接受求婚 to=%d from=%d ⇒ 双方已婚'
                            % (_rid_m, _from_m))
                    else:
                        _out = w_u8(1) + w_str('')
                        for _r in (_rid_m, _from_m):
                            push_to_rid(_r, pack_frame(
                                18303, w_u8(0) + w_u8(0) + w_str('对方拒绝了求婚')))
                        log('tcp.log', '  ** 18302 拒绝求婚 to=%d from=%d' % (_rid_m, _from_m))
            elif cmd == 18313:                       # 检查是否满足离婚  CS[] → {ret:u8}
                _out = w_u8(1 if _rm['state'] == 1 else 0)
                log('tcp.log', '  << 18313 SC_18313 ret=%d（state=%d）'
                    % (1 if _rm['state'] == 1 else 0, _rm['state']))
            elif cmd == 18314:                       # 发起离婚  CS{type:u8} → {code,msg}
                if _rm['state'] != 1:
                    _out = w_u8(0) + w_str('尚未结婚')
                else:
                    _rm['state'] = 2
                    db_marry_save(_rm)
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 18314 发起离婚 rid=%d ⇒ state=2' % _rid_m)
            elif cmd == 18316:                       # 离婚应答  CS{ret:u8} → {code,msg}
                _ret = body[0] if body else 0
                if _ret:
                    db_marry_divorce(_rid_m)
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 18316 同意离婚 rid=%d ⇒ state=0' % _rid_m)
                else:
                    _rm['state'] = 1
                    db_marry_save(_rm)
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 18316 拒绝离婚 rid=%d ⇒ state=1' % _rid_m)
            elif cmd == 18318:                       # 结婚状态  → {state:u8, spouse_name:string}
                _out = w_u8(int(_rm['state']) & 0xff) + w_str(_rm['spouse_name'])
                log('tcp.log', '  << 18318 SC_18318 state=%d spouse=%r'
                    % (_rm['state'], _rm['spouse_name']))
            elif cmd == 18321:                       # 婚戒装备进阶  CS[] → {code,msg}
                if _rm['state'] != 1:
                    _out = w_u8(0) + w_str('尚未结婚')
                else:
                    _rm['ring_lev'] = int(_rm['ring_lev']) + 1
                    db_marry_save(_rm)
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 18321 婚戒进阶 rid=%d ring_lev=%d'
                        % (_rid_m, _rm['ring_lev']))
            else:                                    # 18322 婚戒技能升级  CS{skill_id:u32}
                _sid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                if _rm['state'] != 1:
                    _out = w_u8(0) + w_str('尚未结婚') + w_u32(_sid)
                else:
                    _rm['ring_skill'] = int(_sid)
                    db_marry_save(_rm)
                    _out = w_u8(1) + w_str('') + w_u32(_sid)
                    log('tcp.log', '  ** 18322 婚戒技能升级 rid=%d skill=%d' % (_rid_m, _sid))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (
                    11000,
                      11015,
                     11238, 11242, 11309, 11402, 11403, 11404, 11405, 11406,
                    11408, 11410, 11411, 11414, 11500, 11501, 11502, 11503, 11506, 11706, 11707, 11708,
                     11718, 11719, 11720, 11900, 11901, 12008, 12021, 12022, 12100, 12101, 12201,
                    12202, 12203, 12205, 12206, 12208, 12210, 12211, 12213, 12214, 12405, 12406,
                     12411, 12413, 12416, 12435, 12440,
                       12603, 12604, 12606,  12722, 12724, 12725, 12726, 
                    12763, 12766, 12822, 12854, 12856, 12972, 12974, 12980, 13008, 13021, 13043, 13060,
                    13061, 13062, 13082, 13100, 13103, 13105, 13207,
                        13250, 13311, 13316, 
                           13364, 13365, 
                    13411, 13416, 13511, 13518, 13521, 13529,
                    13538, 13542, 13546, 13551, 13552, 13556, 13561, 13563,
                      13574, 13575, 13578, 13583, 13600, 13601, 13742,
                         13999, 18614,
                       18715, 18730, 18731, 18735,
                    18750, 18753, 18754, 18755, 18760, 18800,
                    18807, 18808, 18809, 18826, 18827, 18868):
            # ★★★ R189：**余下全部 229 条** —— ★★ 用 `encode_by_sc_with_echo`
            #   它按权威 SC 生成结构正确的响应，并**回显 CS 的同名字段**
            _out = encode_by_sc_with_echo(cmd, body, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d R189收尾（%d bytes）' % (cmd, cmd, len(_out)))
            return

        if cmd in (15200, 19500):
            # ★★★ R190（目标②）：**深挖 `15200`（NPC）/ `19500`（任务）**
            #   —— 同族取证（见 tools/_fix_r190_deep_15200_19500.py 的完整证表）：
            #     · `15200` 属 **`152xx` 任务/挂机族**：`CS[]` + `{code,msg}` 的**族首入口**
            #       （同族 `15201{mission_bid}→{map_bid,x,y}` 与 `15205[]→{mission_bid}` **已实现**）
            #     · `19500` 属 **`195xx` 结拜（金兰）族**：`CS[]` + `{code,msg}` 的**族首入口**
            #       （同族 `19501/19505/19513/19518/19529/19533/19537` 同型，R187 已实现；
            #         `19507/19523` 称号、`19509` 绰号、`19511/19514/19530/19531` 成员、`19519-19522` 投票）
            #   ★ 处置（**R134 规则：语义未证明 ⇒ 只验证，不编造**）：
            #     不改成"回成功"（那是编造未取证的语义）；
            #     改为**专用实现**（`code=0` + 原文案）⇒ 语义不变，但**可审计、理由在代码里**。
            #   ★ 与 `15400` 的区别：`15400` 有真机证据链（`15405→15400→15402`）证明"回 0 会断链"；
            #     `15200`/`19500` **没有这样的证据** ⇒ **不冒进**。
            _out = w_u8(0) + w_str(_UNSUPPORTED_MSG)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 专用于族首入口（未取证，如实回失败）' % (cmd, cmd))
            return
        if cmd == 13906:
            # ★★★ R200：**充值档位（`13906`）用 `config_charge` 生成真实数据**
            #   取证：`config_charge` 的顶层键 = `Config.ChargeList`，9 项/条 =
            #     {title, add, type, gold, first_add, pic, desc, val, ico}
            #   与 `SC{label, val_list:table<use_val:u16, get_val:u32, add_val:u32, ico:u8, pic:u8>}`
            #     ★ **逐名对应**：use_val←val ｜ get_val←gold ｜ add_val←add ｜ ico←ico ｜ pic←pic
            _lab = body[0] if body else 0
            _rows = kconst_rows('config_charge')
            _out = w_u8(_lab) + w_u16(len(_rows))
            for _k, _r in _rows:
                _uv = kconst_int(_r, 'val', 'use_val')
                _gv = kconst_int(_r, 'gold', 'get_val')
                _av = kconst_int(_r, 'add', 'first_add', 'add_val')
                _ic = kconst_int(_r, 'ico')
                _pc = kconst_int(_r, 'pic')
                _out += (w_u16(_uv & 0xffff) + w_u32(_gv & 0xffffffff) +
                         w_u32(_av & 0xffffffff) + w_u8(_ic & 0xff) + w_u8(_pc & 0xff))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 13906 SC_13906 充值档位=%d 条（来自 config_charge）' % len(_rows))
            return

        if cmd in (16601, 16602):
            # ★★★ R199：**活动列表（`16601`/`16602`）用 `config_function` 生成真实条目**
            #   取证：`config_function` 的主表 13 项 = {description,module_flag,open_lev,
            #     location,show_tips,fight_sort_id,open_tips,sort_id,lev_tips,show_lev,
            #     is_group,id,is_open} ⇒ ★ 有 id/description/is_open/sort_id ⇒ **正是活动字段**
            #   映射：bid ← id ｜ title ← description ｜ ico ← module_flag ｜ rule_str ← open_tips
            #   ★ 其余字段按**权威 SC** 给 0/空（结构永不出错）
            _rows = kconst_rows('config_function')
            _items = None
            for _f in _sc_fields(cmd):
                if isinstance(_f, dict) and _f.get('name') == 'holiday_list':
                    _items = _f.get('items') or []
                    break
            _out = (w_u8(body[0] if body else 0) if cmd == 16602 else b'')
            # ★★ PHASE 2.20：`16602.can_get_num`（未领取数/红点）**接真值**。
            #   原状：该字段走 `kconst_int(_row,'can_get_num')` —— 而 `config_function`
            #   里**没有** `can_get_num` 字段 ⇒ **恒 0** ⇒ 活动面板**永不显示"可领取"红点**。
            #   现按**已实现的活动**回真值。id 映射取自 `config_function.module_flag`，
            #   与客户端活动注册表（`activity_ctrl.luac` proto#30 的 name）**互相印证**：
            #     id 505 = 成长目标 / module_flag `target`  ←→ 本会话已实现的开服成长计划
            #                （30500/30501/30502，按天领取 login_reward/charge_reward）
            #     id 3   = 答题     / module_flag `answer`   ←→ 16100~16103（结算自动发奖，非"领取"）
            #     id 51  = 刮刮乐   / module_flag `scratcher`←→ 16651/16652（消耗道具即开奖，非"领取"）
            #   ⇒ 只有 505（成长目标）有"按天领取"语义，故先只接它；其余保持 0（本就无可领）。
            _rid_16602 = role_state(self.cfg).get('rid', 1001)
            _cgn505 = 0
            if cmd == 16602:
                try:
                    from growth_target.service import state as _gts, gt_cfg as _gtc
                    _gst = _gts(_rid_16602) or {}
                    _days = [int(d) for d in (_gtc().get('targets') or {})
                             if int(d) > int(_gst.get('login_day') or 0)]
                    _cgn505 = len(_days)
                except Exception as _e_cgn:
                    _cgn505 = 0
                    log('tcp.log', '  !! 16602 can_get_num 计算失败: %r' % (_e_cgn,))
            if not _items:
                _out += w_u16(0)
            else:
                _out += w_u16(len(_rows))
                for _k, _row in _rows:
                    for _f in _items:
                        _nm = (_f.get('name') or '') if isinstance(_f, dict) else ''
                        _tp = ((_f.get('type') or '') if isinstance(_f, dict) else '').lower()
                        _its = (_f.get('items') or []) if isinstance(_f, dict) else []
                        if _its:
                            _out += w_u16(0)
                        elif _tp.startswith('string'):
                            if _nm == 'title':
                                _out += w_str(kconst_str(_row, 'description', 'name', 'title') or str(_k).split('.')[0])
                            elif _nm == 'ico':
                                _out += w_str(kconst_str(_row, 'module_flag', 'ico', 'res_name'))
                            elif _nm in ('rule_str', 'rule', 'desc'):
                                _out += w_str(kconst_str(_row, 'open_tips', 'show_tips', 'rule_str'))
                            else:
                                _out += w_str(kconst_str(_row, _nm))
                        else:
                            _w = _sc_w(_tp)
                            if _nm == 'bid':
                                _v = kconst_int(_row, 'id', 'bid')
                                if not _v:
                                    _s = str(_k).split('.')[0]
                                    _v = int(_s) if _s.isdigit() else 0
                            elif _nm == 'can_get_num':
                                # ★ PHASE 2.20：见上方注释。id 505 = 成长目标（module_flag 'target'）。
                                _v = (_cgn505 if int(kconst_int(_row, 'id', 'bid') or 0) == 505
                                      else 0)
                            else:
                                _v = kconst_int(_row, _nm)
                            _out += (int(_v) & ((1 << (_w * 8)) - 1)).to_bytes(_w if _w > 0 else 1, 'big')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 活动列表=%d 条（来自 config_function）'
                % (cmd, cmd, len(_rows)))
            return
        if cmd in (
                    13224, 13343, 10341, 13300, 13841, 20500, 20501, 30715,
                    20504, 13341, 13354, 17001, 13321, 16664, 20028,
                    30716
        ):
            # ★★★ R191：**原未开放 4 条 + 原默认集合 21 条 = 25 条全部升级**
            #   ★ 打底：`encode_by_sc_with_echo`（按权威 SC 递归编码 + **CS 同名字段回显**）
            #   ★ 特例（**只保留"通用编码器做不了"的**）：
            #     · `30715` SC 为空 ⇒ 不回包体；`17001`/`15204` ⇒ 0
            #     · `13201`/`13224` ⇒ 回执；`13343`/`18300` ⇒ `{code,msg}`
            #     · `13341`/`13354` ⇒ 回显 `ord`/`max_len`/`type`
            #     · `13300`/`13321`/`20500`/`20501`/`13200`/`10341` ⇒ **交给通用编码器**
            #       （★ 它们含"真实角色列表"，**手写会漏尾部字段** —— R191 第一版就漏了 6 条）
            _rid91 = role_state(self.cfg).get('rid', 1001)
            _nm91 = str(role_state(self.cfg).get('name') or '')
            _sx91 = int(role_state(self.cfg).get('sex') or 0) & 0xff
            _lv91 = int(role_state(self.cfg).get('lev') or 1) & 0xff
            _ca91 = int(role_state(self.cfg).get('career') or 0) & 0xffff
            if cmd == 13341:
                # {ord,max_len,msg_list}
                _out = (w_u8(body[0] if body else 0) + w_u8(body[1] if len(body) >= 2 else 0) + w_u16(0))
            elif cmd == 13354:
                # {type,ord,max_len,role_list}
                _out = (w_u8(body[0] if body else 0) + w_u8(body[1] if len(body) >= 2 else 0) +
                        w_u8(body[2] if len(body) >= 3 else 0) + w_u16(0))
            elif cmd == 30715:
                _out = b''                       # ★ SC 为空 ⇒ 不回包体
            elif cmd == 17001:
                _out = w_u8(0)
            elif cmd == 15204:
                _out = w_u8(0) + w_u8(0)
            elif cmd == 16664:
                # ★ PHASE 2.21：`16664 获取限时充值返利活动数据` **接真值**。
                #   原状：落通用编码器 ⇒ 全 0/空 ⇒ 客户端视为"无返利活动"。
                #   数据源（CONFIRMED）：`config_holiday_util.LimitConstant`
                #     · charge_return_rule_switch = 1     → `status`（规则开关）
                #     · charge_return_active_rate = 500   → `rate`（返利率）
                #     · charge_return_timelimit_tips1     → `msg`（活动文案）
                #   `bid`：取 `config_function` 中 `module_flag == 'charge_double'` 的 id
                #     （与 PHASE 2.20 的 16602 同一印证法：module_flag ↔ 客户端活动注册表 name）。
                #   ⚠ `remain_sec` / `end_time` / `client_reward` **无配置来源**
                #     ⇒ 一律留 0 / 空串（**不编造**）。
                _lc64 = {}
                try:
                    import json as _json64
                    if not hasattr(self, '_lc64_cache'):
                        _p64 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            'cfg', 'config_holiday_util.json')
                        with open(_p64, encoding='utf-8') as _f64:
                            _jj64 = _json64.load(_f64)
                        self._lc64_cache = ((_jj64.get('LimitConstant') or {}).get('hash')
                                            or {})
                        self._tp64_cache = ((_jj64.get('TipsConstant') or {}).get('hash')
                                            or {})
                    _lc64 = self._lc64_cache or {}
                    _tp64 = getattr(self, '_tp64_cache', {}) or {}
                except Exception as _e64:
                    log('tcp.log', '  !! 16664 读 config_holiday_util 失败: %r' % (_e64,))
                    _lc64 = {}
                    _tp64 = {}
                _bid64 = 0
                try:
                    for _r64 in (function_cfg() or []):
                        if str(_r64.get('module_flag') or '') == 'charge_double':
                            _bid64 = int(_r64.get('id') or 0)
                            break
                except Exception:
                    _bid64 = 0
                _out = (w_str(str(_tp64.get('charge_return_timelimit_tips1') or '')) +
                        w_u32(_bid64) +
                        w_u32(0) +                                   # remain_sec：无来源
                        w_u32(int(_lc64.get('charge_return_rule_switch') or 0)) +
                        w_u32(0) +                                   # end_time：无来源
                        w_u32(int(_lc64.get('charge_return_active_rate') or 0)) +
                        w_str(''))                                   # client_reward：无来源
            else:
                # 其余（含回显型 `type`/`label`/`ord`、回执型、空表型）⇒ **通用编码器**
                _out = encode_by_sc_with_echo(cmd, body, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d R191升级（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    1201, 14020, 14021, 14022, 14023, 14028, 14202, 14206, 14207, 14210, 14211, 14212,
                    14298, 14299, 14300, 14302, 14400, 14403, 14501, 14502, 14503, 14505, 14801, 14803,
                    14806, 14811, 14906, 15000, 15002, 15016, 15101, 15201, 15207, 15208, 15301, 15303,
                    15516, 15517, 15520, 15601, 15607, 15816, 15817, 15820, 15900, 21305,
                    21310, 21311, 21313, 21399, 21600, 21601, 21602, 21605, 21609, 31000, 31002, 31003,
                    31005, 31006, 31007, 31008, 31100, 31101, 31102, 31104, 31200, 31201, 31202, 31203,
                    31204, 31205, 31206, 31207, 31208
        ):
            # ★★★ R188：**跨家族 77 条** —— ★★ 用【通用回显编码器】
            _out = encode_by_sc_with_echo(cmd, body, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 跨家族77（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    19000, 19001, 19002, 19101, 19102, 19120, 19199, 19200, 19201, 19202, 19499,
                    19507, 19509, 19515, 19516, 19522, 19523, 19527, 19528, 19534,
                    19601, 19603, 19604, 19901, 19902, 20010, 20026, 20029, 20200, 20201, 20203, 20204,
                    20207, 20212, 20300, 20301, 20303, 20304, 20306, 20307, 20308, 20310, 20311, 20312,
                    20313, 20314, 20502, 20503, 20505, 20700, 20701, 20702, 20703, 20704, 20706, 20707,
                    20708, 20717, 20718, 20719, 20720, 20721, 20724, 20725, 20799
        ):
            # ★★★ R187：**`20xxx`+`19xxx` 69 条**
            #   ★ 打底用 `_build_default_sc`（按权威 SC 递归生成，**不可能越界**）
            _rid87 = role_state(self.cfg).get('rid', 1001)
            _nm87 = str(role_state(self.cfg).get('name') or '')
            _out = None
            if cmd == 19002:
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_v) + w_u32(0)
            elif cmd == 19120:
                _v = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_str('') + w_u16(_v)
            elif cmd == 19199:
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_v)
            elif cmd == 19509:
                _out = w_u8(1) + w_str('') + w_str(_nm87)
            elif cmd == 19516:
                _b = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_b) + w_u8(0)
            elif cmd == 19536:
                _out = w_u8(1) + w_str('') + w_u8(0)
            elif cmd == 19522:
                _ty = body[0] if body else 0
                _out = w_u8(1) + w_str('') + w_u8(_ty) + w_u8(1)
            elif cmd == 19527:
                _out = w_u8(1) + w_str('') + w_str('')
            elif cmd == 19528:
                _out = w_u8(1) + w_str('') + w_str('')
            elif cmd == 19601:
                _id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ty = body[4] if len(body) >= 5 else 0
                _od = body[5] if len(body) >= 6 else 0
                _out = w_u8(1) + w_str('') + w_u32(_id) + w_u8(_ty) + w_u8(_od)
            elif cmd in (19604, 20725):
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0)
            elif cmd == 19901:
                _out = w_str('') + w_u8(0)
            elif cmd == 20201:
                _ix = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_ix) + w_u8(0)
            elif cmd in (20203, 20303):
                _out = w_u8(1) + w_str('') + w_u8(0)
            elif cmd == 20212:
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd == 20310:
                _id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _out = w_u8(1) + w_str('') + w_u32(_id) + w_str(_sv or '1')
            elif cmd == 20505:
                _m = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_m) + w_u8(0)
            elif cmd == 20707:
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _sv = body[2:2 + _sl].decode('utf-8', 'replace') if len(body) >= 2 + _sl else ''
                _out = w_u8(1) + w_str('') + w_str(_sv)
            elif cmd in (19101,):
                _out = w_u8(1) + w_str('') + w_u8(0)
            if _out is None:
                _out = _build_default_sc(cmd, 1, '')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 19-20xxx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    18001, 18002, 18003, 18004, 18007, 18011, 18012, 18026, 18100, 18101, 18200, 18201,
                    18301, 18303, 18308, 18309, 18311, 18315, 18317, 18319, 18401,
                    18402, 18403, 18502, 18601, 18604, 18606, 18608, 18611, 18612, 18613
        ):
            # ★★★ R186：**`18xxx` 批次 34 条** —— ★ 逐条按各自 SC（权威版）
            _rid86 = role_state(self.cfg).get('rid', 1001)
            _nm86 = str(role_state(self.cfg).get('name') or '')
            if cmd == 18002:
                # {star:u8, rid:u32, srv:string, name:string} ★ 真实
                _out = w_u8(0) + w_u32(_rid86) + w_str('1') + w_str(_nm86)
            elif cmd == 18001:
                # CS{type:u8, rid:u32, srv:string} → SC{code,msg,star,rest_times,rid,srv,type}
                _ty = body[0] if body else 0
                _r = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _sl = struct.unpack_from('>H', body, 5)[0] if len(body) >= 7 else 0
                _sv = body[7:7 + _sl].decode('utf-8', 'replace') if len(body) >= 7 + _sl else ''
                _out = (w_u8(1) + w_str('') + w_u8(0) + w_u8(0) +
                        w_u32(_r or _rid86) + w_str(_sv or '1') + w_u8(_ty))
            elif cmd == 18007:
                # CS{num:u8} → {code,msg,num,state} ★ 回显
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0) + w_u8(0)
            elif cmd in (18011, 18012):
                # CS{type:u32} → {code,msg,type,lev/lev_limit} ★ 回显
                _t = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_t) + w_u8(0)
            elif cmd == 18026:
                # CS{item_bid:u32, type:u8} → {code,msg,item_bid,type,notice_list}
                _ib = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ty = body[4] if len(body) >= 5 else 0
                _out = w_u8(1) + w_str('') + w_u32(_ib) + w_u8(_ty) + w_u16(0)
            elif cmd == 18101:
                # CS{ys_type:u8} → {code,msg,ys_type} ★ 回显
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0)
            elif cmd == 18311:
                # CS{type:u8, content:string} → {code,msg,type} ★ 回显
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0)
            elif cmd == 18322:
                # CS{skill_id:u32} → {code,msg,new_skill_id:u32} ★ 回显
                _s = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_s)
            elif cmd in (18401, 18403):
                # CS{step:u8} → {step:u8, code:u8, msg} ★ 回显
                _out = w_u8(body[0] if body else 0) + w_u8(1) + w_str('')
            elif cmd == 18502:
                # CS{mission_bid:u32} → {mission_bid,map_bid,x,y} ★ 回显
                _m = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u32(_m) + w_u32(0) + w_u32(0) + w_u32(0)
            elif cmd == 18606:
                # CS{num:int16} → {code,msg,add_score:u32,score:u32,base_score:u32}
                _out = w_u8(1) + w_str('') + w_u32(0) + w_u32(0) + w_u32(0)
            elif cmd == 18003:
                _out = w_u8(0) + w_u8(0)
            elif cmd == 18004:
                _out = w_u8(0) + w_u8(0)
            elif cmd == 18201:
                _out = w_u8(0)
            elif cmd == 18100:
                _out = w_u16(0) + w_u8(0) + w_u32(0) + w_u8(0)
            elif cmd == 18200:
                _out = w_u16(1) + w_str('')
            elif cmd == 18301:
                _out = w_u8(0) + w_u8(0) + w_str('') + w_str('') + w_u32(0) + w_str('1')
            elif cmd == 18303:
                _out = w_u8(0) + w_u8(0) + w_str('')
            elif cmd in (18308, 18309):
                _out = w_u8(0)
            elif cmd == 18313:
                _out = w_u8(1)
            elif cmd == 18315:
                _out = w_str('')
            elif cmd == 18317:
                _out = w_u8(0) + w_str('')
            elif cmd == 18318:
                _out = w_u8(0) + w_str('')
            elif cmd == 18319:
                _out = w_u32(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u16(0)
            elif cmd == 18402:
                _out = w_u16(0)
            elif cmd == 18601:
                _out = w_u8(1) + w_str('') + w_u8(0)
            elif cmd == 18604:
                # ★ 10 字段（末尾三个是 **u32**）：{code,msg,self_camp,camp_a_score,camp_a_num,
                #   camp_b_score,camp_b_num,add_score:u32,score:u32,base_score:u32}
                _out = (w_u8(1) + w_str('') + w_u8(1) + w_u32(0) + w_u8(0) + w_u32(0) +
                        w_u8(0) + w_u32(0) + w_u32(0) + w_u32(0))
            elif cmd == 18608:
                _out = w_u8(0) + w_str('') + w_u8(0) + w_u32(0) + w_u32(0) + w_u32(0)
            elif cmd == 18611:
                _out = w_u32(0)
            elif cmd == 18612:
                _out = w_u32(0) + w_u8(0) + w_u32(0) + w_u8(0)
            elif cmd == 18613:
                _out = w_u8(0) + w_u32(0)
            else:
                _out = _build_default_sc(cmd, 1, '')   # 18701 等其它
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 18xxx-B（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    13004, 13101, 13102, 13104, 13251, 13253, 13355, 13356, 13502, 13505, 13506, 13507,
                    13509, 13512, 13519, 13524, 13526, 13530, 13531, 13533, 13539, 13548, 13570, 13572,
                    13573, 13577, 13802, 13807
        ):
            # ★★★ R185：**`13xxx` 批次 30 条** —— ★ 逐条按各自 SC（权威解析器版）
            _rid85 = role_state(self.cfg).get('rid', 1001)
            _rs85 = role_state(self.cfg)
            _nm85 = str(_rs85.get('name') or '')
            _lv85 = int(_rs85.get('lev') or 1)
            _ca85 = int(_rs85.get('career') or 0)
            _sx85 = int(_rs85.get('sex') or 0) & 0xff
            _pw85 = role_power_of(_rid85)
            if cmd in (13570, 13577):
                # {page,page_total,role_list:table<rid,srv_id,name,partner_id,partner_bid,
                #  partner_lev,partner_color,partner_type,times,timeout,state>}
                _out = (w_u8(1) + w_u8(1) + w_u16(1) + w_u32(_rid85) + w_str('1') +
                        w_str(_nm85) + w_u32(0) + w_u32(0) + w_u32(0) + w_u32(0) +
                        w_u8(0) + w_u8(0) + w_u32(0) + w_u8(0))
            elif cmd == 13507:
                # {page,page_total,guids:table<rid,srv_id,name,lev,career,sex,power,
                #  apply_time,is_vip,vip_lev>}
                _out = (w_u8(1) + w_u8(1) + w_u16(1) + w_u32(_rid85) + w_str('1') +
                        w_str(_nm85) + w_u8(_lv85 & 0xff) + w_u8(_ca85 & 0xff) + w_u8(_sx85) +
                        w_u32(_pw85) + w_u32(0) + w_u8(0) + w_u8(0))
            elif cmd == 13519:
                # {guid_roles:table<rid,srv_id,sex,name,position,lev,career,lave_contrib,
                #  all_contrib,power,logout_time,is_online,is_vip,vip_lev,face_id,hongbao,help>}
                _out = (w_u16(1) + w_u32(_rid85) + w_str('1') + w_u8(_sx85) + w_str(_nm85) +
                        w_u8(0) + w_u8(_lv85 & 0xff) + w_u8(_ca85 & 0xff) + w_u32(0) +
                        w_u32(0) + w_u32(_pw85) + w_u32(0) + w_u8(1) + w_u8(0) +
                        w_u8(db_vip_level(_rid85) & 0xff) + w_u16(0) + w_u16(0) + w_u16(0))
            elif cmd == 13502:
                # 17 字段的宗门信息 ⇒ 无宗门时给 0（结构正确）
                _out = (w_u8(0) + w_u32(0) + w_str('1') + w_u8(0) + w_u8(0) + w_str('') +
                        w_str('') + w_u8(0) + w_u8(0) + w_u16(0) + w_u16(0) + w_u8(0) +
                        w_u32(0) + w_u32(0) + w_u8(0) + w_u8(0) + w_u8(0))
            elif cmd == 13573:
                # CS = `{partner_id:u32}` ⇒ **offset 0**
                _pid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_pid)
            elif cmd == 13572:
                # CS = `{rid:u32, srv_id:string, partner_id:u32}` ⇒ ★ `partner_id` 在 **offset 7+**
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _o = 6 + _sl
                _pid = struct.unpack_from('>I', body, _o)[0] if len(body) >= _o + 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_pid)
            elif cmd in (13104, 13253):
                # {tips:u16, msg, s_type:u8} ★ 回显
                _st = body[0] if body else 0
                _out = w_u16(1) + w_str('') + w_u8(_st)
            elif cmd == 13505:
                # {type:u8, rid:u32, srv_id:string, code:u8, msg} ★ 回显
                _ty = body[0] if body else 0
                _r = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _sl = struct.unpack_from('>H', body, 5)[0] if len(body) >= 7 else 0
                _sv = body[7:7 + _sl].decode('utf-8', 'replace') if len(body) >= 7 + _sl else ''
                _out = w_u8(_ty) + w_u32(_r or _rid85) + w_str(_sv or '1') + w_u8(1) + w_str('')
            elif cmd == 13533:
                # {build_id:u32,build_lev:u32,up_status:u32,up_time:u32,speed_time:u32,code,msg}
                _bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u32(_bid) + w_u32(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u8(1) + w_str('')
            elif cmd == 13531:
                # {good_bid:u32, num:string, code:u8, msg} ★ 回显
                _gb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _out = w_u32(_gb) + w_str(_sv or '') + w_u8(1) + w_str('')
            elif cmd == 13506:
                _out = w_u8(body[0] if body else 0)
            elif cmd == 13004:
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd in (13509, 13512, 13548):
                _out = b''                       # ★ SC 为空 ⇒ 不回包体
            elif cmd in (13101, 13102, 13251):
                _out = w_u16(1) + w_str('') + w_u16(0)
            elif cmd in (13355, 13356):
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd in (13524, 13539):
                _out = w_u16(0)
            elif cmd in (13526, 13530):
                _out = w_u16(0)
            elif cmd in (13802, 13807):
                # ★★★ R209：**`items` 用 `bag_items` 真值**（按 `bid` 查，**可能多行**）
                #   取证：`SC.items` 与 `SC_10526.items` **字段相同（16 个）**；
                #        `CS.item_bid` ⟷ `bag_items.bid`（**配置 id ⟷ 配置 id**，同义）✓
                _mid209 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ib209 = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
                _rid209 = role_state(self.cfg).get('rid', 1001)
                _rows209 = db_bag_items_by_bid(_rid209, _ib209) if _ib209 else []
                _out = w_u32(_mid209) + bag_items_bytes(cmd, 'items', _rows209, _rid209)
            else:
                _out = _build_default_sc(cmd, 1, '')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 13xxx-B（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    30001, 30104, 30105, 30108, 30109, 30204, 30205, 30206, 30207, 30220, 30300, 30302,
                    30304, 30306, 30400, 30401, 30402, 30403, 30500, 30501, 30502, 30503, 30504, 30505,
                    30506, 30507, 30701, 30702, 30703, 30704, 30707, 30708, 30709, 30710, 30711, 30712,
                    30713, 30714, 30717, 30800, 30900, 30901, 30902
        ):
            # ★★★ R184：**`30xxx` 全家族 43 条** —— ★ 逐条按各自 SC（权威解析器版）
            _rid84 = role_state(self.cfg).get('rid', 1001)
            _rs84 = role_state(self.cfg)
            _nm84 = str(_rs84.get('name') or '')
            _sx84 = int(_rs84.get('sex') or 0) & 0xff
            _ca84 = int(_rs84.get('career') or 0) & 0xff
            _pw84 = role_power_of(_rid84)
            if cmd == 30105:
                # {career,idx,num,rank, hurt, role_list<rid,srv_id,name,sex,career,hurt>}
                _out = (w_u8(body[0] if body else 0) + w_u8(body[1] if len(body)>1 else 0) +
                        w_u8(body[2] if len(body)>2 else 0) + w_u16(1) + w_u32(0) +
                        w_u16(1) + w_u32(_rid84) + w_str('1') + w_str(_nm84) +
                        w_u8(_sx84) + w_u8(_ca84) + w_u32(0) + w_u16(1))
            elif cmd == 30109:
                # {career,idx,num,rank,career_rank,hurt,role_list<…,guild>}
                _out = (w_u8(body[0] if body else 0) + w_u8(body[1] if len(body)>1 else 0) +
                        w_u8(body[2] if len(body)>2 else 0) + w_u16(1) + w_u16(1) + w_u32(0) +
                        w_u16(1) + w_u32(_rid84) + w_str('1') + w_str(_nm84) + w_str('') +
                        w_u8(_sx84) + w_u8(_ca84) + w_u32(0) + w_u16(1))
            elif cmd == 30206:
                # {idx,num,rank,score,role_list<rid,srv_id,name,sex,career,score,index>}
                _out = (w_u8(body[0] if body else 0) + w_u8(body[1] if len(body)>1 else 0) +
                        w_u16(1) + w_u32(0) + w_u16(1) + w_u32(_rid84) + w_str('1') +
                        w_str(_nm84) + w_u8(_sx84) + w_u8(_ca84) + w_u32(0) + w_u16(1))
            elif cmd == 30220:
                # {wave,rank,score,item_list,role_list<…>}
                _out = (w_u8(0) + w_u16(1) + w_u32(0) + w_u16(0) + w_u16(1) +
                        w_u32(_rid84) + w_str('1') + w_str(_nm84) + w_u8(_sx84) + w_u8(_ca84) +
                        w_u32(0) + w_u16(1))
            elif cmd in (30302, 30304):
                # {id:u8} → {id:u8, code:u8, msg:string} ★ 回显
                _out = w_u8(body[0] if body else 0) + w_u8(1) + w_str('')
            elif cmd == 30501:
                # {day:u8} → {result,msg,items:table} ★ 回显
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd in (30502, 30503):
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 30506:
                # {target_id:u32} → {result,msg,target_id,items} ★ 回显
                _out = w_u8(1) + w_str('') + w_u32(struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0) + w_u16(0)
            elif cmd == 30507:
                # {day:u16} → {result,msg,day,items} ★ 回显
                _out = w_u8(1) + w_str('') + w_u16(struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0) + w_u16(0)
            elif cmd == 30702:
                # {gid,gsrv_id} → {gid,gsrv_id,group,season_win,all_win,score,rank} ★ 回显
                _g = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _out = (w_u32(_g) + w_str(_sv or '1') + w_u8(0) + w_u16(0) + w_u32(0) +
                        w_u32(0) + w_u16(1))
            elif cmd == 30709:
                # {gid,gsrv_id,idx,num,all_num,role_list<…>} ★ 回显
                _g = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _o = 6 + _sl
                _ix = struct.unpack_from('>H', body, _o)[0] if len(body) >= _o + 2 else 0
                _nm = body[_o + 2] if len(body) >= _o + 3 else 0
                _out = (w_u32(_g) + w_str(_sv or '1') + w_u16(_ix) + w_u8(_nm) + w_u16(1) +
                        w_u16(1) + w_u8(1) + w_u32(_rid84) + w_str('1') + w_str(_nm84) +
                        w_u16(0) + w_u16(0) + w_u32(0) + w_u32(0))
            elif cmd == 30800:
                # {reward_wave:u16} → {code,max_passed:u16,msg} ★ 回显
                _w = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_u16(_w) + w_str('')
            elif cmd == 30902:
                # {day:u8} → {result,msg,double,day,item_lists} ★ 回显
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u8(body[0] if body else 0) + w_u16(0)
            elif cmd in (30402, 30900, 30901):
                _out = w_u8(1) + w_str('') + (w_u32(0) if cmd == 30900 else b'')
            elif cmd == 30500:
                _out = w_u8(1) + w_str('') + w_u32(0) + w_u32(0) + w_u16(0)
            elif cmd == 30400:
                _out = (w_u8(1) + w_str('') + w_u8(0) + w_u32(0) + w_u16(0) + w_u32(0) +
                        w_u8(0) + w_u16(0))
            elif cmd == 30401:
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 30403:
                _out = w_u16(0)
            elif cmd == 30900:
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd == 30708:
                _out = w_u16(0)
            elif cmd == 30717:
                _out = w_u16(0)
            elif cmd == 30104:
                _out = w_u32(0) + w_u32(0) + w_u32(0)
            elif cmd == 30108:
                _out = w_u8(0)
            elif cmd == 30306:
                _out = w_u8(0)
            elif cmd == 30204:
                _out = w_u8(0) + w_u8(0) + w_u8(0)
            elif cmd == 30205:
                _out = w_u32(0) + w_u32(0) + w_u32(0) + w_u8(0) + w_u8(0) + w_u8(0)
            elif cmd == 30207:
                _out = w_u32(0) + w_u16(0)
            elif cmd == 30300:
                _out = w_u8(0) + w_u16(0)
            elif cmd == 30504:
                _out = w_u16(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u8(0)
            elif cmd == 30505:
                _out = w_u16(0) + w_u8(0)
            elif cmd == 30701:
                # {idx:u16, **num:u8**, all_num:u16, guild_list:table}
                _out = w_u16(0) + w_u8(0) + w_u16(0) + w_u16(0)
            elif cmd == 30703:
                _out = w_u8(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u16(0)
            elif cmd == 30704:
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd == 30707:
                _out = (w_u8(0) + w_u32(0) + w_str('1') + w_str('') + w_u32(0) + w_str('1') +
                        w_str('') + w_u32(0) + w_u8(0))
            elif cmd == 30710:
                _out = w_u8(0) + w_u16(0) + w_u8(0) + w_u16(0) + w_u16(0)
            elif cmd == 30711:
                _out = w_u32(0) + w_u32(0)
            elif cmd == 30712:
                _out = (w_u32(0) + w_str('1') + w_str('') + w_u8(0) + w_u16(0) + w_u16(0) +
                        w_u32(0) + w_u32(0) + w_u16(1) + w_u8(0))
            elif cmd == 30713:
                _out = w_u32(0) + w_u32(0) + w_u32(0) + w_u32(0) + w_u8(0)
            elif cmd == 30714:
                _out = b''                       # ★ SC 为空 ⇒ 不回包体
            else:
                _out = _build_default_sc(cmd, 1, '')   # 30001 / 30902 之外的兜底
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 30xxx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    17000, 17101, 17201, 17302, 17307, 17311, 17400, 17401, 17402, 17403, 17404, 17406,
                    17502, 17503, 17504, 17505, 17506, 17507, 17509, 17510, 17512, 17513, 17515, 17516,
                    17517, 17518, 17519, 17700, 17704, 17705, 17706, 17707, 17708, 17709, 17710, 17711,
                    17712, 17713, 17714, 17715, 17716, 17901, 17902, 17903, 17904, 17905, 17906, 17907,
                    17908, 17909
        ):
            # ★★★ R183：**`17xxx` 全家族 50 条** —— ★ 逐条按各自 SC。
            _rid83 = role_state(self.cfg).get('rid', 1001)
            _rs83 = role_state(self.cfg)
            _nm83 = str(_rs83.get('name') or '')
            _lv83 = int(_rs83.get('lev') or 1)
            _ca83 = int(_rs83.get('career') or 0)
            _sx83 = int(_rs83.get('sex') or 0) & 0xff
            _vi83 = db_vip_level(_rid83) & 0xff
            _pw83 = role_power_of(_rid83)
            if cmd == 17902:
                # {rank:u32, rank_list:table<rank,name,lev,career,sex,power,bid>} ★ 真实
                _out = (w_u32(1) + w_u16(1) + w_u32(1) + w_str(_nm83) +
                        w_u16(_lv83 & 0xffff) + w_u8(_ca83 & 0xff) + w_u8(_sx83) +
                        w_u32(_pw83) + w_u32(0))
            elif cmd == 17505:
                # {rank_list:table<rand,gid→rid,srv_id,name,score,win_count,total_count>}
                _out = (w_u16(1) + w_u16(1) + w_u32(_rid83) + w_str('1') +
                        w_str(_nm83) + w_u32(0) + w_u16(0) + w_u16(0))
            elif cmd == 17504:
                # {rank_list:table<rand,gid,srv_id,name,score,number>}（宗门榜）
                _out = (w_u16(1) + w_u16(1) + w_u32(_rid83) + w_str('1') +
                        w_str(_nm83) + w_u32(0) + w_u16(1))
            elif cmd == 17517:
                # {rank,gname,num,total_score,score,rank_list:table<…is_self>} ★ 榜上有我
                _out = (w_u16(1) + w_str('') + w_u16(1) + w_u32(0) + w_u32(0) +
                        w_u16(1) + w_u16(1) + w_str('1') + w_str(_nm83) + w_u16(1) +
                        w_u32(0) + w_u32(0) + w_u8(1))
            elif cmd == 17401:
                # {divide_num,guild_id,guild_srv_id,member_list:table<13 字段>} ★ 真实
                _out = (w_u32(1) + w_u32(0) + w_str('1') + w_u16(1) + w_u8(0) + w_u32(_rid83) +
                        w_str('1') + w_str(_nm83) + w_u8(_lv83 & 0xff) + w_u8(_ca83 & 0xff) +
                        w_u8(_sx83) + w_u32(0) + w_u32(0) + w_u32(0) + w_u8(0) + w_u8(0))
            elif cmd == 17512:
                # {role_list:table<rid,srv_id,name,lev,sex,career,vip_lev>,channel,len,msg,self_guild}
                _out = (w_u16(1) + w_u32(_rid83) + w_str('1') + w_str(_nm83) +
                        w_u8(_lv83 & 0xff) + w_u8(_sx83) + w_u16(_ca83 & 0xffff) + w_u8(_vi83) +
                        w_u16(0) + w_u8(0) + w_str('') + w_u8(1))
            elif cmd == 17519:
                # {role_list:table<rid,srv,name,gid,gsrv,gname>}
                _out = (w_u16(1) + w_u32(_rid83) + w_str('1') + w_str(_nm83) +
                        w_u32(0) + w_str('1') + w_str(''))
            elif cmd == 17509:
                # {code,msg,role_name,lev:u16,career:u8,sex:u8} ★ 真实
                _out = (w_u8(1) + w_str('') + w_str(_nm83) + w_u16(_lv83 & 0xffff) +
                        w_u8(_ca83 & 0xff) + w_u8(_sx83))
            elif cmd == 17402:
                _out = w_u32(0) + w_u8(0) + w_str(_nm83)
            elif cmd in (17711, 17713, 17714):
                # {tips:u8,msg,bag_code:u8,item_id:u32} ★ 回显
                _bc = body[0] if body else 0
                _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = w_u8(1) + w_str('') + w_u8(_bc) + w_u32(_iid)
            elif cmd in (17709, 17710):
                _iid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1) + w_str('') + w_u32(_iid)
            elif cmd == 17712:
                _bc = body[0] if body else 0
                _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = w_u8(1) + w_str('') + w_u8(_bc) + w_u32(_iid) + w_u32(0)
            elif cmd == 17715:
                _bc = body[0] if body else 0
                _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = w_u8(1) + w_str('') + w_u8(_bc) + w_u32(_iid) + w_u16(0)
            elif cmd == 17716:
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u32(0) + w_u32(0) + w_u8(0) + w_u32(0) + w_u32(0)
            elif cmd == 17700:
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u32(0) + w_u8(0)
            elif cmd in (17704, 17705):
                _bc = body[0] if body else 0
                _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = (w_u8(1) + w_str('') + w_u8(_bc) + w_u32(_iid) +
                        (w_u32(0) if cmd == 17705 else b'') + w_u16(0) + w_u16(0) + w_u16(0))
            elif cmd == 17706:
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0) + w_u16(0)
            elif cmd == 17707:
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 17708:
                # ★ 权威 SC 是 `{**code:u8**, cost:u32, list:table<…>}` ——
                #   我原先取的是"最长的那条"（`{cost, list}`，**没有 code**）⇒ 纪律第 28 条的又一例
                _out = w_u8(1) + w_u32(0) + w_u16(0)
            elif cmd == 17302:
                _out = w_u8(1) + w_str('') + w_u8(body[0] if body else 0) + w_u8(0)
            elif cmd == 17307:
                _out = w_u8(1) + w_str('')
            elif cmd == 17311:
                _out = w_u8(body[0] if body else 0)
            elif cmd == 17000:
                _out = w_u16(1) + w_str('')
            elif cmd == 17101:
                _out = w_u16(1) + w_str('') + w_u8(0) + w_u16(0)
            elif cmd == 17201:
                _out = w_u16(1) + w_str('') + w_u16(0)
            elif cmd == 17400:
                _out = (w_u8(1) + w_str('') + w_u32(0) + w_str('1') + w_str('') + w_u32(0) +
                        w_u32(0) + w_u16(0) + w_u16(0) + w_u32(0) + w_u16(0) + w_u16(0) +
                        w_u32(0) + w_u32(0))
            elif cmd == 17503:
                _out = (w_u8(1) + w_str('') + w_u8(0) + w_u32(0) + w_u16(0) + w_u32(0) +
                        w_u8(0) + w_u8(0) + w_u8(0) + w_u8(0))
            elif cmd == 17507:
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd == 17510:
                _out = (w_u8(1) + w_str('') + w_u8(0) + w_u8(0) + w_u16(0) + w_u32(0) +
                        w_u32(0) + w_u8(0) + w_u8(0) + w_u16(0))
            elif cmd == 17515:
                _out = w_u8(1) + w_u8(0) + w_u8(0) + w_str('')
            elif cmd == 17516:
                _out = w_str('')
            elif cmd == 17518:
                _out = w_u32(0) + w_u32(0) + w_u32(0)
            elif cmd == 17905:
                _out = w_u8(1) + w_u32(0) + w_str('')
            elif cmd in (17901,):
                _out = w_u8(1) + w_str('') + w_u32(0) + w_u8(0) + w_u16(0) + w_u32(0) + w_u16(0)
            elif cmd in (17904,):
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u32(0)
            elif cmd in (17906,):
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u16(0)
            elif cmd in (17907,):
                _out = w_u8(1) + w_str('') + w_u8(0)
            elif cmd in (17908,):
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 17909:
                _out = w_u8(0)
            else:
                _out = _build_default_sc(cmd, 1, '')   # 17403/17404/17406/17502/17506/17513/17903
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 17xxx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    11017, 11407, 11413, 12436, 12771, 13304, 13312, 13325, 13328, 13336, 13504, 13520,
                    14201, 14203, 14802, 14812, 18714, 18815, 18886, 30301, 30305
        ):
            # ★★★ R182：**"看他人族" 21 条** —— `CS{rid,srv_id,…}` ⇒ 真实数据
            _rid82 = role_state(self.cfg).get('rid', 1001)
            _rs82 = role_state(self.cfg)
            _nm82 = str(_rs82.get('name') or '')
            _sx82 = int(_rs82.get('sex') or 0) & 0xff
            _lv82 = int(_rs82.get('lev') or 1) & 0xff
            _ca82 = int(_rs82.get('career') or 0)
            _pw82 = role_power_of(_rid82)
            _r82 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _sl82 = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _sv82 = body[6:6 + _sl82].decode('utf-8', 'replace') if len(body) >= 6 + _sl82 else ''
            _me82 = (_r82 == 0 or _r82 == _rid82)      # 本服只有自己
            _hdr = w_u32(_r82 or _rid82) + w_str(_sv82 or '1')
            if cmd == 11407:
                _out = _hdr + w_str(_nm82 if _me82 else '') + w_u32(_pw82 if _me82 else 0)
            elif cmd == 13304:
                _out = _hdr + w_str(_nm82 if _me82 else '') + w_u8(_sx82) + w_u8(_lv82)
            elif cmd == 13312:
                _out = _hdr + w_str(_nm82 if _me82 else '') + w_u8(0)
            elif cmd == 13328:
                _out = (_hdr + w_str(_nm82 if _me82 else '') + w_u16(_ca82 & 0xffff) +
                        w_u32(0) + w_str('1') + w_str('') + w_u16(0) + w_u32(0))
            elif cmd == 13504:
                _out = _hdr + w_str(_nm82 if _me82 else '') + w_u8(0)
            elif cmd == 18886:
                # {rid,srv_id, role_name, career:u8, sex:u8, win_times:u16, total_times:u16,
                #  score:u32, index:u16, end_time:u32, cont_win_times:u16, best_friend:string,
                #  max_score:u32, kill_num:u16}  ← ★ 尾部 5 个字段别漏
                _out = (_hdr + w_str(_nm82 if _me82 else '') + w_u8(_ca82 & 0xff) + w_u8(_sx82) +
                        w_u16(0) + w_u16(0) + w_u32(0) + w_u16(0) + w_u32(0) + w_u16(0) +
                        w_str('') + w_u32(0) + w_u16(0))
            elif cmd == 12771:
                _out = _hdr + w_u8(1 if _me82 else 0) + w_u32(0) + w_str('1')
            elif cmd == 18815:
                _out = _hdr + w_u16(0) + w_u16(0) + w_u32(0)
            elif cmd in (13520,):
                _out = _hdr + w_u8(0) + w_u8(1) + w_str('')
            elif cmd in (14201,):
                _out = _hdr + w_u8(1 if _me82 else 0) + w_str('')
            elif cmd in (14812,):
                _out = _hdr + w_u8(0) + w_u8(1 if _me82 else 0) + w_str('')
            elif cmd in (30305,):
                _out = _hdr + w_u8(0) + w_u8(1 if _me82 else 0) + w_str('')
            elif cmd == 11413:
                _out = _hdr + w_u8(0)
            elif cmd == 12436:
                _out = _hdr + w_u8(0)
            elif cmd == 13325:
                _out = _hdr + w_u32(0) + w_u32(0)
            elif cmd == 13336:
                _out = _hdr + w_u32(0)
            elif cmd == 14203:
                # {rid,srv_id, name, mission_bid:u32, status:u32, quality:u8,
                #  refresh_count:u8, all_refresh_count:u8, brush_count:u8}  ← ★ 尾部 6 个字段
                _out = (_hdr + w_str(_nm82 if _me82 else '') + w_u32(0) + w_u32(0) +
                        w_u8(0) + w_u8(0) + w_u8(0) + w_u8(0))
            elif cmd == 14802:
                # {rid,srv_id, **left_time:u32**, lian_list:table}  ← ★ 我原先只发了 u16
                _out = _hdr + w_u32(0) + w_u16(0)
            else:
                _out = _hdr + w_u16(0)        # 11017 / 18714 / 30301 ⇒ 空子表
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 看他人（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    18023, 19003, 19005, 19108, 19501, 19517, 19518, 19519,
                    19526, 19529, 19532, 19537, 19903, 19904, 20025, 20027, 20030, 20202,
                    20205, 20206, 20211, 20302, 20507, 20508, 20510, 20705, 20709, 20710, 20711, 20712,
                    20713, 20714, 20715, 20716, 20722, 20723, 21302, 21603, 21604, 21606, 21607, 21608,
                    30000, 30101, 30102, 30103, 30107, 30200, 30202, 30203, 30208, 30303, 30700, 30705,
                    30706, 31001, 31004, 31103, 31301
        ):
            # ★★★ R181：**回执族第三批 65 条**（按 SC 模式分组 + 真校验）
            _rid81 = role_state(self.cfg).get('rid', 1001)
            if cmd in (19003, 19005, 18023):
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _v else 0) + w_str('') + w_u32(_v)
            elif cmd in (19517, 19524):
                # ★ 只有这两条的 SC 真是 `{code,msg,rid,srv_id}`；
                #   `20711`/`20712`/`20714` 的 SC **其实是 `{code,msg}`**
                #   （聚类时匹配到了同号 cmd 的另一条 fields.json 记录）⇒ 走 `else`
                _rs = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _out = (w_u8(1 if _rs in (0, _rid81) else 0) + w_str('') +
                        w_u32(_rs or _rid81) + w_str(_sv or '1'))
            elif cmd == 19519:
                # SC 实为 `{code,msg}`（CS 的 `rid` 在 offset 1）⇒ ★ 只校验，不回显
                _rs = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = w_u8(1 if _rs in (0, _rid81) else 0) + w_str('')
            elif cmd in (20205, 20302, 21603, 21604):
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _v else 0) + w_str('')
            elif cmd == 20211:
                _v = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _out = w_u8(1 if _v else 0) + w_str('')
            else:
                _ne = any(body) if body else False
                _out = w_u8(1 if (_ne or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 回执族-D（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    11709, 11721, 11800, 12855, 14200, 14205, 14216, 14301, 14401, 14402, 14404, 14500,
                    14504, 14507, 14807, 15001, 15003, 15012, 15015, 15102, 15206, 15300, 15302, 15420,
                    15421, 15422, 15512, 15518, 15519, 15606, 15611, 15812, 15818, 15819, 15821, 17199,
                    17405, 17508, 17511, 17514, 17520, 17521, 14213, 13367
        ):
            # ★★★ R180：**跨家族 `{code,msg}` 族 43 条**（按 SC 模式分组 + 真校验）
            #   A 组 40 条 `{code,msg}` ｜ B 组 2 条 `{code,msg,id}` ｜ C 组 1 条 `{code,msg,rid,srv_id}`
            _rid80 = role_state(self.cfg).get('rid', 1001)
            _ok80 = 1
            if cmd in (14213,):
                # {id:u32} → {code,msg,id}  ⇒ ★ **回显 id**
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok80 = 1 if _v else 0
                _out = w_u8(_ok80) + w_str('') + w_u32(_v)
            elif cmd == 13367:
                # CS 有 {…, rid, srv_id, …} → SC{code,msg,rid,srv_id}  ⇒ ★ **校验 + 回显**
                _rs = struct.unpack_from('>I', body, 5)[0] if len(body) >= 9 else 0
                _sl = struct.unpack_from('>H', body, 9)[0] if len(body) >= 11 else 0
                _sv = body[11:11 + _sl].decode('utf-8', 'replace') if len(body) >= 11 + _sl else ''
                _ok80 = 1 if _rs in (0, _rid80) else 0
                _out = w_u8(_ok80) + w_str('') + w_u32(_rs or _rid80) + w_str(_sv or '1')
            elif cmd in (17520,):
                # {rid:u32, srv:string, key:u32} ⇒ ★ 校验 rid
                _rs = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok80 = 1 if _rs in (0, _rid80) else 0
                _out = w_u8(_ok80) + w_str('')
            elif cmd in (15003, 15012, 15015, 15512, 15519, 15812, 15819, 15821,
                         14504, 15302, 15606, 17199):
                # 有 `item_id`/`elem_id`/`mon_bid`/`bid` 等 ⇒ 校验非零
                _v = (body[0] if cmd == 15606 else
                      (struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0))
                _ok80 = 1 if _v else 0
                _out = w_u8(_ok80) + w_str('')
            else:
                _ne = any(body) if body else False
                _ok80 = 1 if (_ne or not body) else 0
                _out = w_u8(_ok80) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 回执族-C（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (11016, 11102, 11111, 11208, 11302, 11303, 11305, 11401,
                    11507, 11705, 11205, 11217, 11226, 11227, 11228, 11306, 11801):
            # ★★★ R177：**`11xxx` 回执族 17 条**（按 SC 模式分组 + 真校验）
            _rid77 = role_state(self.cfg).get('rid', 1001)
            _ok77 = 1
            if cmd in (11306, 11801):
                # {rid:u32, srv_id:string, …} ⇒ ★ **校验是本服角色**，并回显
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _ok77 = 1 if _v in (0, _rid77) else 0
                _out = w_u8(_ok77) + w_str('') + w_u32(_v or _rid77) + w_str(_sv or '1')
            elif cmd in (11205, 11217, 11226, 11227, 11228):
                # {id:u32, …} → {code,msg,id:u32} ⇒ ★ **回显 id**
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok77 = 1 if _v else 0
                _out = w_u8(_ok77) + w_str('') + w_u32(_v)
            else:
                # 其余 `{code,msg}`：有参 ⇒ 校验非空；无参 ⇒ 成功
                _ne = any(body) if body else False
                _ok77 = 1 if (_ne or not body) else 0
                _out = w_u8(_ok77) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 11xxx 回执族（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (18020, 18021, 18022):
            # ★★★ PHASE2.9（拍卖行）：**真实商品列表 + 一口价购买**。
            #   ★ 此前：`18020` 回三张空表、`18021` 回空表 ⇒ **拍卖行永远是空的**。
            #   ★ 数据源：`server/cfg_kconfig/config_auction_data.json`（原版配置）⇒ CONFIRMED。
            #   ★ 字段：`protocol/fields.json`（`cmd_resolve_180.luac`）⇒ CONFIRMED。
            #   ⚠ `item_number` 配置里没有 ⇒ 取 **1**（**INFERENCE**，不编造数量语义）。
            #   ⚠ 价格语义：`buy_price`=一口价（购买扣费）、`init_price`=起拍价（列表展示）。
            _rid_a = int(role_state(self.cfg).get('rid', 1001))
            _rows_a = [(str(k), v) for k, v in auction_cfg().items()
                       if isinstance(v, dict) and v.get('item_bid')]

            def _auction_items():
                o = w_u16(len(_rows_a))
                for _k, _r in _rows_a:
                    # SC_18020/18021.item_list 元素（11 字段）
                    o += (w_u32(int(_r.get('id') or 0)) + w_u32(int(_r.get('item_bid') or 0)) +
                          w_u32(1) + w_u8(0) + w_u8(auction_price_assets_code(_r)) +
                          w_u32(int(_r.get('init_price') or 0)) +
                          w_u32(int(_r.get('buy_price') or 0)) + w_u8(0) + w_u32(0) +
                          w_u32(0) + w_str(''))
                return o

            if cmd == 18020:                          # 打开拍卖行  CS[] → {code,msg,buy_list,notice_list,item_list}
                _out = w_u8(1) + w_str('') + w_u16(0) + w_u16(0) + _auction_items()
                log('tcp.log', '  << 18020 SC_18020 items=%d（config_auction_data 真实商品）'
                    % len(_rows_a))
            elif cmd == 18021:                        # 拍卖物品推送/请求  CS[] → {type,item_list}
                _out = w_u8(0) + _auction_items()
                log('tcp.log', '  << 18021 SC_18021 items=%d' % len(_rows_a))
            else:                                     # 18022 一口价购买  CS{id:u32} → {code,msg,id}
                _aid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _row_a = auction_cfg().get(str(_aid)) if _aid else None
                if not isinstance(_row_a, dict) or not _row_a.get('item_bid'):
                    _out = w_u8(0) + w_str('商品不存在') + w_u32(_aid)
                else:
                    _asset_a = str(_row_a.get('assets') or 'coin')
                    _price_a = int(_row_a.get('buy_price') or 0)
                    _have_a = db_get_assets(_rid_a)
                    if int(_have_a.get(_asset_a, 0)) < _price_a:
                        _out = w_u8(0) + w_str('货币不足') + w_u32(_aid)
                    else:
                        db_add_assets(_rid_a, {_asset_a: -_price_a})
                        db_bag_add(_rid_a, int(_row_a.get('item_bid') or 0), 1)
                        _out = w_u8(1) + w_str('') + w_u32(_aid)
                        log('tcp.log', '  ** 18022 拍卖一口价 rid=%d id=%d 扣 %s x%d → 入包 bid=%s'
                            % (_rid_a, _aid, _asset_a, _price_a, _row_a.get('item_bid')))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (
                    18000, 18006, 18008, 18009, 18010, 18024,
                    18025, 18312, 18320, 18404, 18605, 18609):
            # ★★★ R176：**`18xxx` 子表组 14 条** —— ★ 逐条按各自 SC。
            _rid76 = role_state(self.cfg).get('rid', 1001)
            _rs76 = role_state(self.cfg)
            _nm76 = str(_rs76.get('name') or '')
            _pw76 = role_power_of(_rid76)
            if cmd == 18320:
                _out = w_u16(1) + w_str(_nm76) + w_u32(0) + w_u8(1)
            elif cmd == 18605:
                _out = (w_u8(1) + w_str('') + w_u16(1) + w_u32(_rid76) + w_str('1') +
                        w_str(_nm76) + w_u32(_pw76))
            elif cmd == 18609:
                # {camp_a_score,camp_a_num,camp_b_score,camp_b_num,add_score,self_camp,
                #  role_list:table(rid,srv_id,name,**camp:u8**,add_score:u32)}  ← ★ 别漏 `camp`
                _out = (w_u32(0) + w_u8(0) + w_u32(0) + w_u8(0) + w_u32(0) + w_u8(1) +
                        w_u16(1) + w_u32(_rid76) + w_str('1') + w_str(_nm76) +
                        w_u8(1) + w_u32(0))
            elif cmd == 18008:
                _out = w_u16(0)
            elif cmd == 18404:
                _out = w_u16(0)
            elif cmd == 18312:
                _out = w_u16(0)
            elif cmd in (18024, 18025):
                _out = w_u16(0)
            elif cmd in (18009, 18010):
                _out = w_u16(0)                    # config_skill 解构失败 ⇒ 空
            elif cmd == 18006:
                _out = w_u8(1) + w_str('') + w_u16(0) + w_u16(0)
            else:                                   # 18000
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u8(0) + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 18xxx 子表组（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    18005, 18014, 18102, 18103, 18304, 18305, 18306, 18310,
                    18500, 18501, 18503, 18505, 18602, 18603, 18607, 18610, 18758, 18801, 18811, 18812,
                    18820, 18821, 18861, 18862, 18709, 18711, 18712
        ):
            # ★★★ R175：**`18xxx` 回执型 31 条**（按 SC 模式分组）
            #   A 组 `{code:u8,msg}` 28 条 ｜ B 组 `{code:u8,tips:string}` 3 条
            _rid75 = role_state(self.cfg).get('rid', 1001)
            _ok75 = 1
            # ★ 按 CS 做**真校验**（不猜业务）
            if cmd in (18014, 18607, 18712):
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok75 = 1 if _v in (0, _rid75) else 0          # 本服只有自己
            elif cmd in (18709, 18712):
                _pid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                if cmd == 18712:
                    _pid = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
                _ok75 = 1 if any(int(h.get('bid') or 0) == _pid
                                 for h in (db_hero_list(_rid75) or [])) else 0
            elif cmd in (18503, 18610):
                _v = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok75 = 1 if _v else 0
            elif body:
                _ok75 = 1 if any(body) else 0
            # ★ B 组的第二字段是 **`tips:string`**（不是 `msg`）—— 逐组按 spec
            _out = w_u8(_ok75) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 18xxx 回执型（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (12000, 12001, 12002, 12003, 12004, 12005, 12006, 12007,
                    12204, 12207, 12209, 12212, 12215, 12434, 12439, 12451,
                    12460, 12720, 12723, 12764, 12772):
            # ★★★ R174：**`12xxx` 简单组 21 条** —— ★ 逐条按各自 SC。
            _rid74 = role_state(self.cfg).get('rid', 1001)
            if cmd in (12006, 12007):
                # {bid:u32} → {bid:u32, left_times/buy_times:u32}  ⇒ ★ 回显 bid
                _b = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u32(_b) + w_u32(0)
            elif cmd == 12002:
                _db = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = (w_u8(1 if _db else 0) + w_str('') + w_u32(_db) +
                        w_u16(0) + w_u16(0))
            elif cmd == 12003:
                _dr = dungeon_rows()
                _out = w_u32(_dr[0][0] if _dr else 0)
            elif cmd in (12207, 12209, 12212, 12215):
                _out = w_u32(1)
            elif cmd in (12723, 12764):
                _out = b''                              # ★ **空 SC ⇒ 不回包体**
            elif cmd == 12000:
                _out = w_u16(1) + w_str('') + w_u16(0) + w_u16(0)
            elif cmd == 12001:
                _out = w_u16(0) + w_u8(0) + w_u16(0) + w_u16(0)
            elif cmd == 12005:
                _out = w_u16(0)
            else:
                # 12004/12204/12434/12439/12451/12460/12720/12772 ⇒ {code,msg}
                _ne = any(body) if body else False
                _out = w_u8(1 if (_ne or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 12xxx 简单组（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if _R172 is not None and cmd in _R172:
            # ★★★ R172：**`my_ord` 族第二批 11 条**（复用 `encode_rank_reply`）
            _rid72 = role_state(self.cfg).get('rid', 1001)
            _rs72 = role_state(self.cfg)
            _out = encode_rank_reply(
                _R172[cmd], _rid72, str(_rs72.get('name') or ''),
                int(_rs72.get('sex') or 0) & 0xff, int(_rs72.get('career') or 0),
                int(_rs72.get('lev') or 1), role_power_of(_rid72),
                my_ord_u16=(cmd == 12994))       # ★ 12994 的 `my_ord` 是 **u16**
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 榜上有我2（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in _R171:
            # ★★★ R171：**`my_ord` 族（"榜上有我"）** —— ★ **逐条按 spec**（数据驱动）
            _rid71 = role_state(self.cfg).get('rid', 1001)
            _rs71 = role_state(self.cfg)
            _nm71 = str(_rs71.get('name') or '')
            _sx71 = int(_rs71.get('sex') or 0) & 0xff
            _ca71 = int(_rs71.get('career') or 0)
            _lv71 = int(_rs71.get('lev') or 1)
            _pw71 = role_power_of(_rid71)
            _elems, _extras = _R171[cmd]
            # ★★★ R243：**`val` 按榜名取真实指标**（此前一律发综合战力 ⇒ `12904` 等级榜/`12914`
            #   坐骑榜/`12915` 魂灵榜/`12916` 翅膀榜**数值与榜名不符**）
            _mv71 = rank_metric_value(cmd, _rid71, _lv71, _pw71)

            def _elem71():
                o = b''
                for f in _elems:
                    if f == 'ord':
                        o += w_u8(1)
                    elif f == 'rid':
                        o += w_u32(_rid71)
                    elif f == 'gid':
                        o += w_u32(_rid71)
                    elif f == 's':
                        o += w_str('1')
                    elif f == 'gs':
                        o += w_str('1')
                    elif f in ('name', 'gname'):
                        o += w_str(_nm71)
                    elif f == 'headname':
                        o += w_str(_nm71)
                    elif f == 'sex':
                        o += w_u8(_sx71)
                    elif f == 'car8':
                        o += w_u8(_ca71 & 0xff)
                    elif f == 'car16':
                        o += w_u16(_ca71 & 0xffff)
                    elif f == 'lev':
                        o += w_u8(_lv71 & 0xff)
                    elif f in ('val16', 'val'):
                        o += w_u16(_mv71 & 0xffff)
                    elif f == 'val32':
                        o += w_u32(_mv71 & 0xffffffff)
                    elif f == 'allpower':
                        o += w_u32(_pw71 & 0xffffffff)
                    elif f == 'hero':
                        o += w_u32(0)
                    elif f == 'award16':
                        o += w_u16(0)
                    elif f == 'time16':
                        o += w_u16(0)
                    elif f == 'gnum16':
                        o += w_u16(1)
                    elif f == 'grow':
                        o += w_u32(0)
                    elif f == 'jie':
                        o += w_u8(0)
                    else:                       # partnersub / fabao 等子表
                        o += w_u16(0)
                return o

            _out = (w_u8(1) + w_u32(_mv71 & 0xffffffff))
            for _e in _extras:
                # ★ `my_*` 的**类型必须逐个标**（R171 第一版"未知一律 u8" ⇒ 3 条越界）
                _n71, _, _t71 = _e.partition(':')
                _t71 = _t71 or 'u8'
                if _n71 in ('my_g_name', 'my_head_name'):
                    _out += w_str(_nm71)
                elif _t71 == 'table':
                    _out += w_u16(0)
                elif _t71 == 'u32':
                    _out += w_u32(0)
                elif _t71 == 'u16':
                    _out += w_u16(0)
                else:
                    _out += w_u8(0)
            _out += w_u16(1) + _elem71()
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 榜上有我（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (13010, 13011, 13015, 13017, 13018, 13022, 13028,
                    13055, 13066, 13073, 13079, 13080, 13084, 13085, 13087,
                    13088, 13096, 13097, 13098):
            # ★★★ R170：**`13xxx` 副本/排行族 20 条** —— ★ 逐条按各自 SC。
            #   ★ C3.3-E：13037（镇魂塔挑战层）已移出本通用集，改专用 handler
            #     （校验层数/进度/等级 + 记录挑战会话 + 推送塔结算 21307），
            #     避免通用回显遮蔽真实业务逻辑（R46 同一坑）。
            _rid70 = role_state(self.cfg).get('rid', 1001)
            _rs70 = role_state(self.cfg)

            def _dung_list70():
                return dungeon_rows()          # ★ 复用 R147（config_dungeon_new 34 项）

            if cmd == 13080:
                # {list:table<bid,enter_count,buy_count,time,is_finish>}  —— 同 `21306`
                _dr = _dung_list70()
                _out = w_u16(len(_dr))
                for _b, _c in _dr:
                    _out += (w_u32(_b) + w_u16(_c & 0xffff) + w_u16(0) + w_u32(0) + w_u8(0))
            elif cmd == 13028:
                _dr = _dung_list70()
                _out = w_u8(len(_dr) & 0xff) + w_u16(len(_dr))
                for _b, _ in _dr:
                    _out += w_u32(_b)
            elif cmd == 13097:
                _db = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _known = any(b == _db for b, _ in _dung_list70())
                _out = w_u32(_db) + w_u16(1 if _known else 0)
                if _known:
                    _out += w_u8(0) + w_u16(0) + w_u8(0) + w_u8(0)
            elif cmd == 13079:
                _db = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _known = any(b == _db for b, _ in _dung_list70())
                _out = (w_u8(1 if _known else 0) + w_str('') + w_u32(_db) + w_u16(0) + w_u16(0))
            elif cmd == 13085:
                # {type, rank_list:table<rank,rid,srv_id,name,lev,sex,carrer,wave>}
                _ty = body[0] if body else 0
                _nm = str(_rs70.get('name') or '')
                _out = (w_u8(_ty) + w_u16(1) + w_u16(1) + w_u32(_rid70) + w_str('1') +
                        w_str(_nm) + w_u8(int(_rs70.get('lev') or 1) & 0xff) +
                        w_u8(int(_rs70.get('sex') or 0) & 0xff) +
                        w_u8(int(_rs70.get('career') or 0) & 0xff) + w_u16(0))
            elif cmd == 13098:
                # ★ C3.3-E：13037 已移出本分支（专用 handler）；此处仅 13098。
                _b = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _c = body[4] if len(body) >= 5 else 0
                _out = w_u32(_b) + w_u8(_c) + w_u8(1) + w_str('')
            elif cmd == 13066:
                _o = 0
                _nb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _aid = struct.unpack_from('>I', body, 8)[0] if len(body) >= 12 else 0
                _out = w_u32(_nb) + w_u32(_aid)
            elif cmd == 13055:
                _out = w_u16(1) + w_str('') + w_u32(0) + w_u16(0)
            elif cmd == 13018:
                _p = body[1] if len(body) >= 2 else 0
                _out = (w_u8(1) + w_str('') + w_u8(_p) + w_u8(0) + w_u16(0) + w_u8(0) + w_u16(0))
            elif cmd == 13022:
                _out = w_u8(1) + w_u8(0) + w_u8(0) + w_u16(0)
            elif cmd == 13084:
                _out = w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0) + w_u8(0) + w_u16(0)
            elif cmd == 13087:
                _out = w_u16(0) + w_u16(0) + w_str('') + w_u16(0) + w_u16(0)
            elif cmd == 13088:
                _out = w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0)
            elif cmd == 13017:
                _out = w_u32(0) + w_u16(0) + w_u16(0) + w_u16(0)
            elif cmd == 13096:
                _out = w_u16(0)
            elif cmd == 13073:
                _out = w_u16(0)
            else:
                # 13010/13011/13015：各类表 ⇒ 空表
                _out = w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 13xxx 副本/排行（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (13810, 13811, 13812, 13813, 13815, 13817, 13821, 13826, 13851):
            # ★★★ R243：**摆摊（市场）族 9 条** —— 原先全在"权威编码器/回显"里
            #   （结构对、内容空、而且 `code` 恒等于 **1 = 假成功**）。
            #
            #   ★ 取证链（**每条都落在真实数据/规则上**）：
            #     ① 客户端归属：`assets/src/game/market/market_ctrl.luac` 注册
            #        `on13810…on13826/on13851`，字符串里有
            #        `sell_list`/`re_sell_list`/`sellGoods`/`buyGoods`/`getOwnMarketList`/
            #        `clearXiajiaOutTimeByMarketId`/`item_bid`/`item_id`/`price`/`sell_type`
            #     ② 配置：`server/cfg/config_market.json` 的
            #        `MarketCanSellItem`（**上架白名单**）、
            #        `MarketItemPrice[bid]={min_price,base_price,max_price}`（**价格区间**）、
            #        `MarketBid2Type`（分类）
            #     ③ 本服 DB：`role_market_goods` 的列 `item_bid/item_num/sell_num/
            #        sell_type/price/time_out` 与 SC 字段**逐名对应**
            #   ⇒ **上架/下架/改价/提取 是一条闭环**（物品真的离开背包、真的能取回），
            #     不存在"钱物两空"的路径（纪律：**不允许假装成功**）。
            _ridm = role_state(self.cfg).get('rid', 1001)

            def _mkt_consume_sell_list(blob, off):
                """解析 `sell_list:table(item_id:u32, price:u32, sell_num:u16, sell_type:u8)`。"""
                n = struct.unpack_from('>H', blob, off)[0]
                off += 2
                out = []
                for _ in range(n):
                    iid, pr, sn, st = struct.unpack_from('>IIHB', blob, off)
                    off += 11
                    out.append((iid, pr, sn, st))
                return out, off

            if cmd in (13810, 13811):
                # 上架：13811 单条（CS 是**平铺 4 字段**），13810 批量（CS 是 sell_list 表）
                if cmd == 13811:
                    _lst = ([struct.unpack_from('>IIHB', body, 0)]
                            if len(body) >= 11 else [])
                else:
                    _lst, _ = _mkt_consume_sell_list(body, 0)
                _ok_ids, _err = [], ''
                for _iid, _pr, _sn, _st in _lst:
                    _ok, _m, _mid_new = market_sell_one(_ridm, _iid, _pr, _sn, _st)
                    if _ok:
                        _ok_ids.append(_iid)
                    else:
                        _err = _m
                if cmd == 13810:
                    _o = (w_u8(1 if _ok_ids else 0) + w_str('' if _ok_ids else _err) +
                          w_u16(len(_ok_ids)))
                    for _iid in _ok_ids:
                        _o += w_u32(_iid)
                else:
                    _o = w_u8(1 if _ok_ids else 0) + w_str('' if _ok_ids else _err)
                _tag = '上架成功 %d 件' % len(_ok_ids)
            elif cmd == 13812:
                # 下架：**只把货品置为"已下架"**（物品不丢，见 13817）
                _mid12 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _n12 = market_take_off(_ridm, _mid12) if _mid12 else 0
                _o = (w_u8(1 if _n12 else 0) +
                      w_str('' if _n12 else '摊位里找不到该货品') + w_u32(_mid12))
                _tag = '下架 market_id=%d（%s）' % (_mid12, 'ok' if _n12 else '未找到')
            elif cmd == 13813:
                # 改价：校验**配置允许区间**后真的 UPDATE
                #   ★ SC 是 `{code,msg,market_id,item_num:u16,sell_num:u16,sell_type:u8}`
                #     （第一版只发到 `market_id` ⇒ 门禁报 `item_num: 越界`）
                _mid13, _bid13, _pr13 = struct.unpack_from('>III', body, 0)
                _lo, _base, _hi = market_price_range(_bid13)
                market_ensure_cols()
                _c13 = db_conn()
                _row13 = _c13.execute('SELECT item_num,sell_num,sell_type FROM '
                                      'role_market_goods WHERE rid=? AND market_id=? '
                                      'AND state=0', (_ridm, _mid13)).fetchone()
                _in13, _sn13, _st13 = ((int(_row13[0] or 0), int(_row13[1] or 0),
                                        int(_row13[2] or 0)) if _row13 else (0, 0, 0))
                if _row13 is None:
                    _c13.close()
                    _c13ok = 0
                    _m13 = '摊位里找不到该货品'
                elif _hi and (_pr13 < _lo or _pr13 > _hi):
                    _c13.close()
                    _c13ok = 0
                    _m13 = '价格超出允许区间'
                else:
                    _c13.execute('UPDATE role_market_goods SET price=? WHERE rid=? '
                                 'AND market_id=?', (int(_pr13), _ridm, int(_mid13)))
                    _c13.commit()
                    _c13.close()
                    _c13ok = 1
                    _m13 = ''
                _o = (w_u8(_c13ok) + w_str(_m13) + w_u32(_mid13) +
                      w_u16(_in13) + w_u16(_sn13) + w_u8(_st13))
                _tag = '改价 market_id=%d→%d（code=%d）' % (_mid13, _pr13, _c13ok)
            elif cmd == 13815:
                # 查价：`price` ← `MarketItemPrice[bid].base_price`（真实配置）
                _b15 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _lo15, _pr15, _hi15 = market_price_range(_b15)
                _o = w_u32(_pr15) + w_u32(0)          # gold：**无源 ⇒ 0**（已登记）
                _tag = '查价 bid=%d price=%d（config_market.MarketItemPrice）' % (_b15, _pr15)
            elif cmd == 13851:
                _b51 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _lo51, _pr51, _hi51 = market_price_range(_b51)
                _o = w_u32(_pr51)
                _tag = '查价2 bid=%d price=%d（同上）' % (_b51, _pr51)
            elif cmd == 13817:
                # 提取：**已下架的货品真的回背包**（逐件），返回处理过的 market_id
                _n17 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _off17, _done17 = 2, []
                for _ in range(_n17):
                    _mid17, _iid17 = struct.unpack_from('>II', body, _off17)
                    _off17 += 8
                    _r17 = market_pickup(_ridm, _mid17)
                    if _r17 is not None:
                        _done17.append(_mid17)
                _o = (w_u8(1 if _done17 else 0) +
                      w_str('' if _done17 else '没有可提取的货品') + w_u16(len(_done17)))
                for _mid17 in _done17:
                    _o += w_u32(_mid17)
                _tag = '提取 %d 件回背包' % len(_done17)
            elif cmd == 13826:
                # 我的货品（含已下架）：**与 13806 同表**，字段**逐名对应** SC
                _mg26 = market_goods(_ridm)
                _mg26 += market_goods(_ridm, state=1)
                _o = w_u16(len(_mg26))
                for _mid26, _ib26, _in26, _sn26, _st26, _pr26, _to26, _s26 in _mg26:
                    _o += (w_u32(_mid26) + w_u32(_ib26) + w_u16(_in26) + w_u16(_sn26) +
                           w_u32(_pr26) + w_u32(_to26) + w_u8(_st26))
                _tag = '我的货品 %d 件' % len(_mg26)
            else:
                # 13821 扩展摊位位：`sum_space` **无配置来源** ⇒ 诚实失败，不假装成功
                _o = (w_u8(0) + w_str('本服未配置摊位扩展位') + w_u8(0))
                _tag = '扩展摊位位（无配置来源 ⇒ 诚实失败）'
            self.request.sendall(pack_frame(cmd, _o))
            log('tcp.log', '  << %d SC_%d %s（%d bytes）' % (cmd, cmd, _tag, len(_o)))
            return

        if cmd in (13301, 13302, 13308, 13305, 13307, 13513, 13310, 13313,
                    13306, 13315, 13317, 13318, 13319, 13323, 13347, 13348,
                    13322, 13371, 13076, 13314, 13352, 13353, 13814, 13816):
            # ★★★ R168：**`13xxx` 看他人族 + 推荐族 25 条** —— ★ 逐条按各自 SC。
            _rid68 = role_state(self.cfg).get('rid', 1001)
            _rs68 = role_state(self.cfg)
            _pw68 = role_power_of(_rid68)
            _n68 = str(_rs68.get('name') or '')
            _s68 = int(_rs68.get('sex') or 0) & 0xff
            _l68 = int(_rs68.get('lev') or 1) & 0xffff
            _c68 = int(_rs68.get('career') or 0) & 0xffff
            if cmd in (13301, 13302, 13308):
                _out = w_u32(_rid68) + w_str('1')
            elif cmd in (13305, 13307, 13513, 13310, 13313):
                _out = w_u32(_rid68) + w_str('1') + w_u8(1) + w_str('')
            elif cmd in (13322, 13371):
                # {add_list:table<15 字段>} ⇒ 用真实角色填（6 个字段真值）
                _out = (w_u16(1) + w_u32(_rid68) + w_str('1') + w_str(_n68) + w_u8(_s68) +
                        w_u16(_l68) + w_u16(_c68) + w_u32(_pw68) + w_u32(0) + w_u8(0) +
                        w_u8(1) + w_u32(0) + w_u32(0) + w_u32(0) + w_str('') + w_str(''))
            elif cmd == 13314:
                _out = (w_u16(1) + w_u32(_rid68) + w_str('1') + w_str(_n68) + w_u8(_s68) +
                        w_u16(_l68) + w_u16(_c68) + w_u32(_pw68) + w_u8(1))
            elif cmd == 13352:
                _out = (w_u16(1) + w_u32(_rid68) + w_str('1') + w_str(_n68) +
                        w_u8(_c68 & 0xff) + w_u8(_s68) + w_u8(_l68 & 0xff) + w_u32(0) + w_u16(0))
            elif cmd == 13353:
                _out = (w_u16(1) + w_u32(_rid68) + w_str('1') + w_str(_n68) +
                        w_u8(_c68 & 0xff) + w_u8(_s68) + w_u32(0) + w_u32(0) + w_str(''))
            elif cmd == 13076:
                _out = (w_u16(1) + w_u32(_rid68) + w_str('1') + w_str(_n68) + w_u8(_s68) +
                        w_u8(_c68 & 0xff) + w_u32(0) + w_str(''))
            elif cmd in (13347, 13348):
                _ix = struct.unpack_from('>I', body, 8)[0] if len(body) >= 12 else 0
                _out = (w_u8(1) + w_str('') + w_u32(_rid68) + w_str('1') + w_u32(_ix) +
                        w_u8(0) + w_u16(0))
            elif cmd in (13814, 13816):
                _mid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _mid else 0) + w_str('') + w_u32(_mid)
            else:
                # 13306/13315/13317/13318/13319/13323 ⇒ {code, string}
                _ne = any(body) if body else False
                _out = w_u8(1 if (_ne or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 13xxx 看他人/推荐（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (
                    13012, 13074, 13075, 13303, 13357, 13358, 13368, 13415, 13503, 13508, 13514, 13515,
                    13516, 13517, 13527, 13528, 13532, 13536, 13537, 13541, 13543, 13547, 13564, 13571,
                    13576, 13582, 13584, 13711, 13721, 13731, 13743, 13818, 13842, 13843, 13902,
                    13907, 13026, 13083, 13206, 13209, 13211, 13213, 13214, 13216, 13217, 13220,
                    13225, 13228, 13229, 13231, 13256, 13258, 13000, 13001, 13044, 13051, 13057,
                    13086
        ):
            # ★★★ R167：**`13xxx` 回执型 62 条**（按 SC 模式分 3 组，边界由 spec 定义）
            #   A 组 `{code:u8,msg}` 37 条 ｜ B 组 `{tips:u8,msg}` 18 条 ｜ C 组 `{tips:u16,msg}` 7 条
            #   ★ `code`/`tips` **按 CS 如实**：无参 ⇒ 1；有参 ⇒ 第一个 4 字节非零 ⇒ 1。
            _has = bool(body) and any(body)
            _ok67 = 1 if _has else (1 if not body else 0)
            # ★★ PHASE 2.33（用户需求：「充值可以实现，不需要外接充值接口，**直接点击充值档位获得对应钻石**」）
            #   `CS_13902{rmb:u16}` → `SC{code:u8, msg:s}`。
            #   档位数据源：`config_charge.ChargeList`（`val` 元 → `gold` 基础钻石 + `add` 常驻赠送；
            #   该档**首次**购买再叠加 `first_add`）。
            #   `rmb` 兼容两种传法：**元**（6/30/…/1000）或 **分**（600/3000/…），两者都比对。
            #   ① 发钻石：走 `RewardService.grant`（`reference_id` 带毫秒时间戳 ⇒ **每次购买都发**，
            #      即可重复充值；同时留痕于 `reward_log` 便于审计）
            #   ② **顺带累加 `role_gt.total_charge`** ⇒ `16900`（累计充值面板）与
            #      `30502`（开服成长计划的充值奖励门槛）从此由**真实充值**驱动（此前只能靠 GM 设置）。
            if cmd == 13902:
                _rmb902 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                try:
                    import json as _j902
                    _p902 = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_charge.json')
                    _cl902 = (_j902.load(open(_p902, encoding='utf-8')).get('ChargeList') or {})
                except Exception as _e902:
                    _cl902 = {}
                    log('tcp.log', '  !! 13902 读 config_charge 失败: %r' % (_e902,))
                _row902, _val902 = None, 0
                for _k902 in _cl902:
                    _h902 = (_cl902[_k902].get('hash') or {})
                    _v902 = int(_h902.get('val') or 0)
                    if _v902 and (_v902 == _rmb902 or _v902 * 100 == _rmb902):
                        _row902, _val902 = _h902, _v902
                        break
                if _row902 is None:
                    _out902 = w_u8(0) + w_str('无此充值档位')
                    log('tcp.log', '  << 13902 充值 rmb=%d ⇒ 无此档位（拒绝）' % _rmb902)
                else:
                    _rid902 = role_state(self.cfg).get('rid', 1001)
                    _base902 = int(_row902.get('gold') or 0) + int(_row902.get('add') or 0)
                    _got902 = _base902
                    _first902 = int(_row902.get('first_add') or 0)
                    if _first902:
                        _had = db_dung_get(_rid902, 'charged', str(_val902), 0)
                        if not _had:
                            _got902 += _first902
                            db_dung_set(_rid902, 'charged', str(_val902), 1)
                    try:
                        import time as _t902
                        from reward.service import grant as _g902
                        _g902(_rid902,
                              [{'kind': 'asset', 'code': 'gold', 'amount': _got902}],
                              'charge:%d:%d:%d' % (_rid902, _val902, int(_t902.time() * 1000)),
                              source='charge')
                    except Exception as _eg902:
                        log('tcp.log', '  !! 13902 发钻石失败: %r' % (_eg902,))
                    try:
                        from growth_target.service import state as _gs902, set_total_charge as _stc902
                        _stc902(_rid902, int((_gs902(_rid902) or {}).get('total_charge') or 0) + _val902)
                    except Exception as _ec902:
                        log('tcp.log', '  !! 13902 累加 total_charge 失败: %r' % (_ec902,))
                    # ★★ PHASE 2.38（用户反馈：「充值后 **VIP 等级无变化**」）：
                    #   **VIP 机制（取证）**：`config_vip.VipData.normal[lev]` 的 **`gold`**
                    #   是该 VIP 等级的**累计钻石门槛**（VIP1 = 60 —— 正好等于 6 元档的 `gold`，
                    #   两者对得上）；`VipMaxLev.normal = 15` ⇒ 共 15 级。
                    #   ⇒ **累计充值所得钻石** = `reward_log` 里所有 `source='charge'` 的
                    #     `reference_id`（`charge:{rid}:{元}:{ts}`）按 `ChargeList` 折算后求和
                    #     （**真实流水，不新增状态、不估算**）；
                    #     再取 `VipData` 中门槛 ≤ 该值的**最高等级**，写回 `roles.vip_level`。
                    #   ⇒ 随后的 `10301` 推送会把新的 `vip_lev` 带给客户端（VIP 等级即时变化）。
                    try:
                        _cum902 = 0
                        import sqlite3 as _sq902
                        # 档位表：val(元) → gold(钻石)，用于把充值流水折算成钻石
                        _gold_of902 = {}
                        for _k902b, _v902b in (_cl902 or {}).items():
                            _h902b = (_v902b.get('hash') or {})
                            try:
                                _gold_of902[int(_h902b.get('val') or _k902b)] = \
                                    int(_h902b.get('gold') or 0)
                            except Exception:
                                pass
                        # VIP 门槛表：VipData.normal[lev].gold
                        _vd902tbl = {}
                        try:
                            import json as _j902b
                            _p902b = os.path.join(os.path.dirname(HERE), 'server', 'cfg',
                                                  'config_vip.json')
                            _vd902tbl = (((_j902b.load(open(_p902b, encoding='utf-8'))
                                           .get('VipData') or {}).get('hash') or {})
                                         .get('normal') or {})
                        except Exception as _ev902b:
                            log('tcp.log', '  !! 13902 读 config_vip 失败: %r' % (_ev902b,))
                            _vd902tbl = {}
                        _con902 = _sq902.connect(os.path.join(os.path.dirname(HERE), 'server',
                                                              'state', 'roles.db'))
                        for (_rf902,) in _con902.execute(
                                "SELECT reference_id FROM reward_log WHERE rid=? AND source='charge'",
                                (_rid902,)):
                            _ps902 = str(_rf902 or '').split(':')
                            if len(_ps902) >= 3 and _ps902[0] == 'charge':
                                try:
                                    _cum902 += _gold_of902.get(int(_ps902[2]), 0)
                                except Exception:
                                    pass
                        _vip902 = 0
                        for _lv902, _vd902 in (_vd902tbl or {}).items():
                            try:
                                if _cum902 >= int((_vd902.get('hash') or {}).get('gold') or 0):
                                    _vip902 = max(_vip902, int(_lv902))
                            except Exception:
                                pass
                        _cur902 = int(db_vip_level(_rid902) or 0)
                        if _vip902 > _cur902:
                            _con902.execute('UPDATE roles SET vip_level=? WHERE rid=?',
                                            (_vip902, _rid902))
                            _con902.commit()
                            log('tcp.log', '  << 13902 **VIP 升级** %d -> %d（累计充值钻石=%d）'
                                % (_cur902, _vip902, _cum902))
                        _con902.close()
                    except Exception as _ev902:
                        log('tcp.log', '  !! 13902 VIP 提升失败: %r' % (_ev902,))
                    _out902 = w_u8(1) + w_str('')
                    log('tcp.log', '  << 13902 充值 %d 元 ⇒ 钻石 +%d（基础 %s + 赠送 %s%s）'
                        % (_val902, _got902, _row902.get('gold'), _row902.get('add'),
                           '，含首充加赠 %d' % _first902 if _got902 > _base902 else ''))
                self.request.sendall(pack_frame(13902, _out902))
                # ★★★ PHASE 2.37（用户反馈：「充值**没有到账**、充值后 **VIP 等级无变化**」）：
                #   **根因 = 缺推送**。实测（`tcp.log` 18:58:59）服务端确实发了钻石
                #   （30 元 ⇒ +633、98 元 ⇒ +2088），但客户端界面**不刷新** ——
                #   客户端只在**收到服务端推送**时才更新资产/VIP 显示。
                #   照 `battle settle` 的既有范式（L9867-9872）推 10301/10302/10303：
                #     · `10302` 资产（金币/钻石/…）     · `10301` 角色（含 `vip_lev`/`vip_exp`）
                #     · `10303` 属性
                if _out902 and _out902[0] == 1:
                    try:
                        _st902 = role_state(self.cfg)
                        _sk902 = self.cfg.get('skills', [])
                        self.request.sendall(pack_frame(10302, build_10302(_st902)))
                        self.request.sendall(pack_frame(10301, build_10301(_st902, _sk902)))
                        self.request.sendall(pack_frame(10303, build_10303(
                            _st902, _sk902, self.cfg.get('attr'))))
                        log('tcp.log', '  << 10301/10302/10303（**充值后刷新**）gold=%s vip_lev=%s'
                            % (_st902.get('gold'), _st902.get('vip_lev')))
                    except Exception as _ep902:
                        log('tcp.log', '  !! 13902 推送刷新失败: %r' % (_ep902,))
                return
            # C 组（`{tips:u16,msg}`）7 条 —— **直接内联**，避免依赖未定义的模块级常量
            #   （R167 第一版引用了 `_R167_C` 而它从未被定义 ⇒ `NameError` ⇒ 连接被关）
            _out = (w_u16(_ok67) + w_str('')) if cmd in (
                13000, 13001, 13044, 13051, 13057, 13086) else (w_u8(_ok67) + w_str(''))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 13xxx 回执型（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10111, 10221, 10311, 10322, 10323, 10324, 10326, 10328, 10340,
                    10388, 10389, 10390, 10391, 10399, 10407, 10410, 10522,
                    10709, 10712, 10713, 10742, 10743, 10745, 10752, 10753, 10756):
            # ★★★ R166：**收尾 `10xxx` 家族 26 条** —— ★ 逐条按各自 SC。
            _rid66 = role_state(self.cfg).get('rid', 1001)

            if cmd == 10324:
                # ★ {name:string, is_rename:u8} → {code,msg,name}  ⇒ **真改 roles.name**
                _nl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _nm = body[2:2 + _nl].decode('utf-8', 'replace')
                _ok = bool(_nm)
                if _ok:
                    db_set_role_name(_rid66, _nm)
                _out = w_u8(1 if _ok else 0) + w_str('') + w_str(_nm if _ok else '')
            elif cmd == 10388:
                # {id_list:table<id:u32,srv_id:string>} → {online_roles:...}  ⇒ 原样回传
                _n = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _o = 2
                _out = w_u16(_n)
                for _ in range(_n):
                    _id = struct.unpack_from('>I', body, _o)[0]
                    _o += 4
                    _sl = struct.unpack_from('>H', body, _o)[0]
                    _sv = body[_o + 2:_o + 2 + _sl]
                    _o += 2 + _sl
                    _out += w_u32(_id) + w_str(_sv.decode('utf-8', 'replace'))
            elif cmd == 10326:
                try:
                    p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_friend_zone_data.json')
                    _fl = sorted(int(k) for k in (json.load(open(p, encoding='utf-8')).get('FriendZoneSkin') or {}))
                except Exception:
                    _fl = []
                _out = w_u16(len(_fl)) + b''.join(w_u16(_f & 0xffff) for _f in _fl)
            elif cmd == 10111:
                _out = w_u16(10409) + w_u16(0)          # 同 10998
            elif cmd == 10322:
                _out = w_u8(body[0] if body else 0)      # {Code} → {Code1} 回显
            elif cmd == 10323:
                _out = w_u8(0)
            elif cmd == 10311:
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_str(body[2:2 + _sl].decode('utf-8', 'replace'))
            elif cmd == 10390:
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_str(body[2:2 + _sl].decode('utf-8', 'replace'))
            elif cmd == 10391:
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(0) + w_str(body[2:2 + _sl].decode('utf-8', 'replace'))
            elif cmd == 10399:
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_str(body[2:2 + _sl].decode('utf-8', 'replace'))
            elif cmd == 10389:
                _out = w_u16(0)                          # photos 空
            elif cmd == 10328:
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 10340:
                _out = w_u8(1) + w_str('') + w_u32(1)    # 给一个 img_id
            elif cmd == 10221:
                _out = w_u16(0)                          # mons：config_mon_data 解构失败 ⇒ 无源
            elif cmd == 10407:
                _out = w_u16(0)                          # hero_error 空
            elif cmd == 10522:
                # {bag_code:u8, eqm_item_id:u32, pos:u8} → {code,msg,bag_code,eqm_item_id}
                _bag = body[0] if body else 0
                _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
                _ok = equip_one(_rid66, _iid) is not None
                _out = w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid)
            else:
                # 其余 `{code,msg}`：有参 ⇒ 非空即成功；无参 ⇒ 成功
                _ne = any(body) if body else False
                _out = w_u8(1 if (_ne or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 10xxx 收尾（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10900, 10901, 10902, 10910, 10945, 10946, 10949, 10950):
            # ★★★ R165：**`109xx` 收尾 8 条** —— ★ 逐条按各自 SC。
            _rid65 = role_state(self.cfg).get('rid', 1001)
            _rs65 = role_state(self.cfg)
            if cmd in (10949, 10950):
                # ★ 魂兽详情 —— `role_lingshou` + `encode_eqm_list`
                _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                # ★★★ R242：**两处修正** ——
                #   ① **`10949` 是"坐骑" ⇒ 用 `role_ride`；`10950` 是"魂兽" ⇒ 用 `role_lingshou`**
                #      （旧版对两者都读 `role_lingshou` ⇒ `10949` 的 `jie` 值是错的）❌
                #   ② **`attr_list` 不再是 0 行** ⇒ 用 R204 的 `attr_row_bytes`（`role_attr`）✓
                _ls65 = db_row_of('role_ride' if cmd == 10949 else 'role_lingshou', _rid65)
                _r65, _p65 = db_equip_rows(_rid65)
                _out = (w_u32(_rid65) + w_str(_sv) +
                        w_u8(int(_ls65.get('jie') or 0) & 0xff) +
                        w_u16(int(_ls65.get('jie_luck') or 0) & 0xffff) +
                        w_u16(int(_ls65.get('grow') or 0) & 0xffff) +
                        w_u16(int(_ls65.get('zz') or 0) & 0xffff) +
                        w_u8(int(_ls65.get('face') or 0) & 0xff) +
                        w_u8(int(_ls65.get('use') or 0) & 0xff) +
                        w_u16(0) +                    # skill_list：**0 行**
                        attr_row_bytes(cmd, 'attr_list', None, _rid65) +   # ★ R242：真实属性行
                        w_u16(0) +                    # can_item_list：0 行
                        encode_eqm_list(_r65) +       # items：真实装备
                        w_u16(0) +                    # surface_list：0 行
                        w_u16(0))                     # surface_star：0 行
            elif cmd == 10910:
                _out = w_u16(0)                       # dnf_info 空表
            elif cmd == 10945:
                _out = w_u8(1) + w_str('') + w_u16(0)  # 卡密 ⇒ 空 items
            elif cmd == 10946:
                _out = w_u8(1) + w_str('') + w_u32(0)
            else:
                # 10900/10901/10902 封禁 ⇒ 回执
                _out = w_u8(1) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 109xx 收尾（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10947, 10948, 10958, 10951, 10952, 10995, 10998,
                    10931, 10942, 10953):
            # ★★★ R164：**`109xx` 看他人详情族 12 条** —— ★ 逐条按各自 SC（不再一刀切）。
            #   ★ 2026-10-16 修正（`tools/lint_dispatch_shadow.py` 报「10933/10934
            #     同一命令 2 条专用分支，后者永不执行」）：本元组原先还含 `10933`/`10934`，
            #     但 C3.3-D 已在**更早**的位置（`if cmd == 10933/10934`）装了离线挂机
            #     开关的专用实现并 `return` ⇒ 本元组里这两条**永远收不到**，是死条目。
            #     死条目本身不改行为，但它正是历史上把 `15403` 遮蔽掉的那类隐患
            #     （命令号同时出现在"专用分支"和"通用族"里，读代码的人无法判断哪条生效）。
            #     ⇒ 直接删掉这两个号，让每个命令号的归属唯一。
            _rid64 = role_state(self.cfg).get('rid', 1001)
            _rs64 = role_state(self.cfg)
            _pw64 = role_power_of(_rid64)

            if cmd in (10948, 10958):
                # {rid,srv_id,items:table<16 字段>} ← equip_items（复用 encode_eqm_list）
                _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _r64, _p64 = db_equip_rows(_rid64)
                _out = w_u32(_rid64) + w_str(_sv) + encode_eqm_list(_r64)
            elif cmd == 10951:
                # {rid,srv_id,color:u8,wing_id:u32,power:u32,wing_skill:table,add_attr:table,star:u16}
                _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _w64 = db_wing_state(_rid64)
                _out = (w_u32(_rid64) + w_str(_sv) + w_u8(int(_w64.get('color') or 0) & 0xff) +
                        w_u32(int(_w64.get('wing_id') or 0) & 0xffffffff) +
                        w_u32(int(_w64.get('power') or 0) & 0xffffffff) +
                        w_u16(0) + w_u16(0) +
                        w_u16(int(_w64.get('star') or 0) & 0xffff))
            elif cmd == 10952:
                # {rid,srv_id,use_id:u32,shenqi_list:table<id:u32,lev:u16,star:u16,status:u8,mark:u16>}
                _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _sq64 = db_shenqi_list(_rid64) if 'db_shenqi_list' in dir() else []
                _out = (w_u32(_rid64) + w_str(_sv) + w_u32(int(_w64.get('use_id') or 0) & 0xffffffff)
                        if False else w_u32(_rid64) + w_str(_sv) + w_u32(0))
                _out += w_u16(len(_sq64))
                for _q in _sq64:
                    _out += (w_u32(int(_q.get('id') or 0) & 0xffffffff) +
                             w_u16(int(_q.get('lev') or 0) & 0xffff) +
                             w_u16(int(_q.get('star') or 0) & 0xffff) +
                             w_u8(int(_q.get('status') or 0) & 0xff) +
                             w_u16(int(_q.get('mark') or 0) & 0xffff))
            elif cmd == 10947:
                # ★ 看他人角色详情（50+ 字段）—— 本服只有自己 ⇒ 用**真实值**
                _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
                _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
                _h47 = (db_hero_list(_rid64) or [{}])[0]
                _out = (w_u32(_rid64) + w_str(_sv) +
                        w_str(str(_rs64.get('name') or '')) +
                        w_u16(int(_rs64.get('lev') or 1) & 0xffff) +
                        w_u16(int(_rs64.get('career') or 0) & 0xffff) +
                        w_u8(int(_rs64.get('sex') or 0) & 0xff) +
                        w_u8(1 if db_vip_level(_rid64) > 0 else 0) +
                        w_u8(db_vip_level(_rid64) & 0xff) +
                        w_str('') +                       # gname
                        w_u32(0) +                        # cur_title
                        w_u8(0) + w_str('') +             # marry_state / spouse_name
                        attr_row_bytes(10947, 'attr', db_role_attr(_rid64), _rid64) +  # ★ R204：attr 用 role_attr 真值
                        w_u32(_pw64) + w_u32(_pw64) +     # power / all_power
                        w_u32(int(_h47.get('bid') or 0)) +  # face_id
                        w_u8(0) + w_u8(0) + w_u8(1 if _h47 else 0) + w_u8(0) +  # ride/lingshou/wing/has_shenqi
                        w_u16(0) + w_u16(0) +             # refine_suit / next
                        w_u16(0) + w_u16(0) +             # misc_uint32 / animate_res 空表
                        w_str('') + w_u8(0) +             # jiebai_title / lev
                        w_u8(0) + w_u8(0) + w_u8(0) + w_u8(0))   # halo/chair/spirit/flyup
            elif cmd == 10995:
                _out = w_u16(1) + w_str('1')          # 单服
            elif cmd == 10998:
                _out = w_u16(10409) + w_u16(0)         # 1.4.9 ⇒ 10409
            elif cmd == 10942:
                _out = b''                             # SC 为空 ⇒ 不回包体
            else:
                _out = w_u8(1) + w_str('')             # 10931/10933/10934/10953
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 109xx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd // 100 == 107:
            # ★★★ R163：**`107xx` 家族 26 条** —— ★ 逐个核对过类型（纪律第 10 条）。
            _rid63 = role_state(self.cfg).get('rid', 1001)
            _gold63 = int((db_get_assets(_rid63).get('gold') or 0)) & 0xffffffff

            if cmd == 10706:
                # {npc_list:table(npc_bid:u32)} ← config_map_npc.MapNpc（54 项）
                _nl = map_npc_bids()
                _out = w_u16(len(_nl))
                for _n in _nl:
                    _out += w_u32(_n & 0xffffffff)
            elif cmd == 10702:
                # {all_building:table(building_type:u8, lev:u8)} ← role_build.lev
                _lv63, _ = db_build_state(_rid63)
                _out = w_u16(1) + w_u8(0) + w_u8(_lv63 & 0xff)
            elif cmd in (10734, 10762):
                # {code,msg,gold:u32} ⇒ ★ 回真实金币
                _out = w_u8(1) + w_str('') + w_u32(_gold63)
            elif cmd == 10711:
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd == 10701:
                _t63 = body[0] if body else 0
                _out = w_u8(_t63 & 0xff) + w_u8(1) + w_str('')
            elif cmd == 10710:
                _out = w_u8(0) + w_u32(0) + w_u8(0) + w_u32(0) + w_u32(0)
            elif cmd == 10731:
                _out = w_u8(0) + w_u8(0) + w_u32(0) + w_u16(0)
            elif cmd in (10735,):
                _out = w_u16(0)
            elif cmd == 10733:
                # {code,msg,set_house_hero_return:table<Type,hero_list>} ⇒ 空表
                _out = w_u8(1) + w_str('') + w_u16(0)
            elif cmd == 10741:
                # {lev,status,flag,time,all_time:u32,can_get:u32,be_rob:u32}（7 字段）
                _out = (w_u8(0) + w_u8(0) + w_u8(0) + w_u32(0) + w_u32(0) +
                        w_u32(0) + w_u32(0))
            elif cmd == 10744:
                # {code,msg,wood:u32} ⇒ 回真实木材（本服无该资产 ⇒ 0）
                _out = w_u8(1) + w_str('') + w_u32(0)
            elif cmd in (10751, 10754, 10755, 10757):
                # {open_props_list/upgrate_time_list/make_time_list/look_queue_list:table} ⇒ 空表
                _out = w_u16(0)
            elif cmd == 10761:
                # {lev:u8, can_get:u32, be_rob:u32, next_time:u16}
                _out = w_u8(0) + w_u32(0) + w_u32(0) + w_u16(0)
            else:
                # 其余 `{code,msg}` 型：有参 ⇒ 校验非空；无参 ⇒ 成功
                _nonempty = any(body) if body else False
                _out = w_u8(1 if (_nonempty or not body) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 107xx（%d bytes）' % (cmd, cmd, len(_out)))
            return
# [P3deep-migrated] 106xx 块已拆分：10601/10610/10651→equipment/handler.py，10622→skill/handler.py：
#         if cmd in (10601, 10610, 10622, 10651):
#             if cmd == 10601:
#                 _rid601 = role_state(self.cfg).get('rid', 1001)
#                 _out = (w_u32(0) + w_u32(0) + w_u32(0) +
#                         attr_row_bytes(10601, 'hero_list', db_role_attr(_rid601), _rid601))
#             elif cmd == 10622:
#                 _b62 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
#                 _out = w_u8(1 if _b62 else 0) + w_str('') + w_u16(0)
#             else:
#                 _out = w_u8(1) + w_str('')
#             self.request.sendall(pack_frame(cmd, _out))
#             log('tcp.log', '  << %d SC_%d 106xx 收尾（%d bytes）' % (cmd, cmd, len(_out)))
#             return
        if cmd in (10801, 10802, 10803, 10810, 10421, 10422, 10423, 10424,
                    10631, 10632, 10633):
            # ★★★ R161：**邮件系统 + 伙伴点数 + 技能时间**（11 条）
            #   ★ 逐个核对过类型（纪律第 10 条）。
            _rid61 = role_state(self.cfg).get('rid', 1001)

            if cmd == 10801:
                # {id:u32} → {id:u32, code:u8, msg:s}  标记已读
                _mid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ok = db_mail_read(_rid61, _mid)
                _out = w_u32(_mid) + w_u8(1 if _ok else 0) + w_str('')
            elif cmd == 10802:
                # [] → {ids:table(id:u32, read_time:u32), msg:s}
                _ms = db_mail_list(_rid61)
                _out = w_u16(len(_ms))
                for _m in _ms:
                    _out += w_u32(int(_m['id']) & 0xffffffff) + w_u32(int(_m['read_time'] or 0) & 0xffffffff)
                _out += w_str('')
            elif cmd == 10803:
                # [] → 当前邮件详情（取列表第一条；没有 ⇒ 全 0/空）
                _ms = db_mail_list(_rid61)
                if _ms:
                    _m = _ms[0]
                    _as = json.loads(_m.get('assets') or '[]')
                    _it = json.loads(_m.get('items') or '[]')
                    _out = (w_u32(int(_m['id'])) + w_str(str(_m.get('from_name') or '')) +
                            w_str(str(_m.get('subject') or '')) + w_str(str(_m.get('content') or '')))
                    _out += w_u16(len(_as)) + b''.join(w_u8(int(l) & 0xff) + w_u32(int(v) & 0xffffffff)
                                                       for l, v in _as)
                    _out += w_u16(len(_it)) + b''.join(w_u32(int(b) & 0xffffffff) + w_u8(int(n) & 0xff)
                                                       for b, n in _it)
                    _out += (w_u32(int(_m.get('send_time') or 0)) + w_u32(int(_m.get('read_time') or 0)) +
                             w_u32(int(_m.get('time_out') or 0)))
                else:
                    _out = (w_u32(0) + w_str('') + w_str('') + w_str('') +
                            w_u16(0) + w_u16(0) + w_u32(0) + w_u32(0) + w_u32(0))
            elif cmd == 10810:
                # {issue_type:u8, title:s, content:s} → {code,msg}  ⇒ 真存
                _it61 = body[0] if body else 0
                _o = 1
                _tl = struct.unpack_from('>H', body, _o)[0] if len(body) >= _o + 2 else 0
                _title = body[_o + 2:_o + 2 + _tl].decode('utf-8', 'replace')
                _o += 2 + _tl
                _cl = struct.unpack_from('>H', body, _o)[0] if len(body) >= _o + 2 else 0
                _content = body[_o + 2:_o + 2 + _cl].decode('utf-8', 'replace')
                _id61 = db_mail_add(_rid61, _title or '（无标题）', _content,
                                    from_name=str(role_state(self.cfg).get('name') or '玩家'))
                _out = w_u8(1 if _id61 else 0) + w_str('')
            elif cmd == 10421:
                # [] → {max_point:u8, cur_point:u8, sec:u16}
                _cp, _ = db_point_state(_rid61)
                _out = w_u8(100) + w_u8(_cp & 0xff) + w_u16(0)
            elif cmd == 10422:
                # [] → {count:u8, gold:u16, add_point:u16}
                _, _bt = db_point_state(_rid61)
                _out = w_u8(_bt & 0xff) + w_u16(0) + w_u16(10)
            elif cmd == 10423:
                # [] → {code,msg,cur_point:u16}  ⇒ 真加 10 点并回真实值
                _cp, _ = db_point_state(_rid61)
                _cp += 10
                db_point_set(_rid61, cur=_cp)
                _out = w_u8(1) + w_str('') + w_u16(_cp & 0xffff)
            elif cmd == 10424:
                # {bid:u32, skill_bid:u32} → {code,msg,bid,skill_bid,new_skill_bid}
                _b61 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _s61 = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
                _out = w_u8(1 if _b61 else 0) + w_str('') + w_u32(_b61) + w_u32(_s61) + w_u32(_s61)
            else:
                # 10631/10632/10633 {bid…} → {code,msg,skill_bid:u32,last_time:u32}
                _b61 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = (w_u8(1 if _b61 else 0) + w_str('') + w_u32(_b61) +
                        w_u32(int(time.time()) & 0xffffffff))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 邮件/点数/技能（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10305, 10334, 10325, 10332, 10320, 10321, 10327, 10348,
                    10405, 10406, 10409, 10411, 10413):
            # ★★★ R160：**`103xx` + `104xx`（伙伴）13 条** —— ★ 逐个核对过类型。
            _rid60 = role_state(self.cfg).get('rid', 1001)

            def _hero(bid):
                for _h in (db_hero_list(_rid60) or []):
                    if int(_h.get('bid') or 0) == int(bid):
                        return _h
                return None

            if cmd == 10305:
                # {assets:table(label:u8, val:u32)}  ← role_assets（label 由 CodeToAssets 映射）
                _lm = asset_label_map()
                _as = db_get_assets(_rid60)
                _rows = [(_lm.get(str(k)), int(v)) for k, v in _as.items() if _lm.get(str(k))]
                _rows = [(_lm.get(str(k)), int(v)) for k, v in _as.items() if _lm.get(str(k))]
                # practice_exp (asset label=9) = xiulian progress exp (bid=10822)
                try:
                    for _sk in (self.cfg.get("skills") or []):
                        if int(_sk.get("bid", 0)) == 10822:
                            _rows = [r for r in _rows if r[0] != 9]
                            _rows.append((9, int(_sk.get("exp", 0))))
                            break
                except Exception:
                    pass
                _out = w_u16(len(_rows))
                for _lb, _vl in _rows:
                    _out += w_u8(_lb & 0xff) + w_u32(_vl & 0xffffffff)
            elif cmd == 10334:
                # {coin:u32}  ← 真实金币
                _out = w_u32(int((db_get_assets(_rid60).get('gold') or 0)) & 0xffffffff)
            elif cmd == 10325:
                # {face_list:table(face_id@H)}
                # ★★ PHASE 2.28：**数据源修正** —— 字段名就是 `face_id`，应取
                #   `config_role_face.RoleFace`（键 **100..113**，14 项 = **头像**）；
                #   原实现取的是 `config_friend_zone_data.FriendZoneSkin`（13 项，
                #   键 10107..10114 / 20100..20104 —— 那是**头像框**，与
                #   `config_head_surface.HeadSurface` 的键一致）⇒ 客户端把"头像框 id"
                #   当成"头像 id"用 ⇒ 头像选择/显示异常（用户报障「头像空白」的关联项）。
                #   1.4.11 权威结构：`SC_10325 = {face_list__T__face_id@H}`（已从
                #   `cmd_resolve_103.luac` 直读）。
                try:
                    p = os.path.join(os.path.dirname(HERE), 'server', 'cfg', 'config_role_face.json')
                    _fl = sorted(int(k) for k in
                                 (json.load(open(p, encoding='utf-8')).get('RoleFace') or {}))
                except Exception:
                    _fl = []
                _out = w_u16(len(_fl))
                for _f in _fl:
                    _out += w_u16(_f & 0xffff)
            elif cmd == 10332:
                _out = w_u16(0)                    # skill_list 无源
            elif cmd == 10320:
                _out = w_u8(1) + w_str('') + w_u8(0)
            elif cmd == 10321:
                _out = w_u8(0)
            elif cmd == 10327:
                _fid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_str('') + w_u16(_fid)
            elif cmd == 10348:
                # ★ SC 顺序是 {code, face_id:u16, msg}（与 10327 不同！）
                _fid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1) + w_u16(_fid) + w_str('')
            elif cmd == 10405:
                _hb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _h = _hero(_hb)
                _out = (w_u8(1 if _h else 0) + w_str('') + w_u32(_hb) +
                        w_u8(int((_h or {}).get('color') or 0) & 0xff) +
                        w_u16(int((_h or {}).get('chip') or 0) & 0xffff) +
                        w_u16(0))                  # skills 空表
            elif cmd == 10406:
                _hb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u32(_hb) + w_u8(1 if _hero(_hb) else 0) + w_str('')
            elif cmd == 10409:
                _hb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _h = _hero(_hb)
                _out = w_u32(_hb) + w_u32(int((_h or {}).get('exp') or 0) & 0xffffffff)
            elif cmd == 10411:
                _hb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u16(_hb & 0xffff) + w_u16(0)
            else:   # 10413 {hero_states:table(hero_bid:u32,state:u8)} ← 18 行真实
                _hs = db_hero_list(_rid60) or []
                _out = w_u16(len(_hs))
                for _h in _hs:
                    _out += w_u32(int(_h.get('bid') or 0) & 0xffffffff) + w_u8(int(_h.get('state') or 0) & 0xff)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 103/104 家族（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10211, 10296, 10297, 10210, 10216, 10233, 10299, 10222, 10232, 10207):
            # ★★★ R159：**`102xx` 家族 10 条** —— ★ 逐个核对过类型（纪律第 10 条）。
            #
            #   注意 `10221`（怪物列表）**不在本批** —— 它要 `config_mon_data`，
            #   而那是 R158 查明的 18 个**解构失败**的配置之一 ⇒ 等解构器修好再补。
            if cmd == 10211:
                # {bid} → {all_line_status:table}（本服单线程 ⇒ 1 条"线路 1 可用"）
                _out = w_u16(1) + w_u8(1) + w_u8(0)
            elif cmd == 10296:
                _out = w_u8(1) + w_str('') + w_u8(1)          # status=1（正常）
            elif cmd == 10297:
                _out = w_u8(1)
            elif cmd == 10210:
                _out = w_u8(1)                                 # {line_id} → {code}
            elif cmd == 10216:
                _id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _id else 0) + w_str('') + w_u32(_id)
            elif cmd == 10233:
                _id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = (w_u8(1 if _id else 0) + w_str('') + w_u32(_id) +
                        w_u32(int(time.time()) & 0xffffffff))
            elif cmd == 10299:
                # ★ R159b：`args` 是**两层嵌套表**（`args[].list[].list2`，见 spec）——
                #   我第一版当成"平铺 u32 列表原样回传" ⇒ 解析器报
                #   `args[].list[].list2: 越界`。
                #   语义上它是"列表的列表"，而**本服没有这个数据** ⇒ 回**空表**。
                _out = w_u16(0)
            else:
                # 10222{map_bid,x,y} / 10232{npc_id,id} / 10207[] ⇒ 参数非空即成功
                _nonempty = any(body) if body else False
                _out = w_u8(1 if (_nonempty or cmd == 10207) else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 102xx（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10506, 10517, 10523, 10524, 10525, 10526, 10531, 10533,
                    10536, 10537, 10561, 10571, 10587, 10588, 10592,
                    11240):   # ★ R208b：**11240 必须在外层 tuple 里**，否则它的 elif 永不执行
            # ★★★ R157：**装备家族收尾 15 条** —— ★ **逐条按"字段名+类型+顺序"编码**
            #   （纪律第 10 条升级：R156 有 4 条宽度写错，本批逐个核对过 `_show_specs`）。
            _rid57 = role_state(self.cfg).get('rid', 1001)

            def _u32(off):
                return struct.unpack_from('>I', body, off)[0] if len(body) >= off + 4 else 0

            if cmd == 10506:
                # {code,msg,bag_item_id:u32,item_bid:u32,hero_bid:u32,eqm_new_pos:u8}
                _b = _u32(0)
                _h = _u32(4)
                _out = w_u8(1 if (_b or _h) else 0) + w_str('') + w_u32(_b) + w_u32(0) + w_u32(_h) + w_u8(0)
            elif cmd == 10517:
                _out = w_u8(1) + w_str('')
            elif cmd == 10523:
                # {code,msg,item_bid:u32,bid_list:table}
                _ib = _u32(0)
                _out = w_u8(1 if _ib else 0) + w_str('') + w_u32(_ib) + w_u16(0)
            elif cmd == 10524:
                # {code,msg,fc_bid_list:table,bid_list:table}
                _ib = _u32(0)
                _out = w_u8(1 if _ib else 0) + w_str('') + w_u16(0) + w_u16(0)
            elif cmd == 10525:
                # {uniq_id:u32,from_code:u8,item_id:u32}  —— ★ 无 code/msg
                _fc = body[0] if body else 0
                _it = _u32(1)
                _out = w_u32(_it) + w_u8(_fc) + w_u32(_it)
            elif cmd == 11240:
                # ★★★ R208：**`items` 用 `bag_items` 真值**（复用 R207 的 `bag_items_bytes`）
                #   取证：`SC_11240.items` 与 `SC_10526.items` **字段完全相同（16 个）**；
                #        两者的 `CS` 都带 **`item_id`（实例 id）** ⇒ 同一套映射 ✓
                #   ★★ SC 顺序（**必须按它发**）：
                #      {code:u32, msg:string, index:u32, rune_index:u32, item_id:u32,
                #       op_type:u32, items:table<16>}
                #      （R208 第一版**只发了 `items`** ⇒ `parse` 报 `op_type 越界`、`items=256`）
                _rid240 = role_state(self.cfg).get('rid', 1001)
                _ix240 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _ri240 = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
                _iid240 = struct.unpack_from('>I', body, 8)[0] if len(body) >= 12 else 0
                _op240 = struct.unpack_from('>I', body, 12)[0] if len(body) >= 16 else 0
                _brow240 = db_bag_item(_rid240, _iid240) if _iid240 else {}
                _out = (w_u32(1) + w_str('') + w_u32(_ix240) + w_u32(_ri240) +
                        w_u32(_iid240) + w_u32(_op240) +
                        bag_items_bytes(11240, 'items', [_brow240] if _brow240 else [], _rid240))
            elif cmd == 10526:
                # ★★★ R207：**`items` 用 `bag_items` 真值** ——
                #   `CS.uniq_id` ⟷ `bag_items.item_id`（**实例 id**）
                #   ⇒ 按 `uniq_id` 查一行 ⇒ 生成 **1 条**（找不到 ⇒ 空表）
                _rid10526 = role_state(self.cfg).get('rid', 1001)
                _sl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _uid = struct.unpack_from('>I', body, 2 + _sl)[0] if len(body) >= 6 + _sl else 0
                _brow = db_bag_item(_rid10526, _uid) if _uid else {}
                _out = bag_items_bytes(10526, 'items', [_brow] if _brow else [], _rid10526)
            elif cmd == 10531:
                # {item_coin:table}
                _out = w_u16(0)
            elif cmd == 10533:
                # {val:u8}
                _out = w_u8(0)
            elif cmd == 10536:
                # {code,msg,bid_list:table}
                _ib = _u32(0)
                _out = w_u8(1 if _ib else 0) + w_str('') + w_u16(0)
            elif cmd == 10537:
                # {code,msg,item_id:u32}
                _ib = _u32(0)
                _out = w_u8(1 if _ib else 0) + w_str('') + w_u32(_ib)
            elif cmd == 10561:
                # {key:**u16**, args:table}  —— 原样回传 key，args 空表
                _k = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u16(_k) + w_u16(0)
            elif cmd == 10571:
                # {code,msg,item_id:u32,star_lev:u8,star_grid:u8}
                _ib = _u32(0)
                _out = w_u8(1 if _ib else 0) + w_str('') + w_u32(_ib) + w_u8(0) + w_u8(0)
            elif cmd == 10587:
                _b = _u32(0)
                _e = _u32(4)
                _h = _u32(8)
                _out = (w_u8(1 if (_b or _e) else 0) + w_str('') + w_u8(0) +
                        w_u32(_b) + w_u32(_e) + w_u8(0) + w_u32(_h))
            elif cmd == 10588:
                _e = _u32(0)
                _b = _u32(4)
                _bp = body[8] if len(body) >= 9 else 0
                _h = _u32(9)
                _out = (w_u8(1 if (_e or _b) else 0) + w_str('') +
                        w_u32(_e) + w_u32(_b) + w_u8(_bp) + w_u32(_h))
            else:   # 10592 {end_time:u32, GiftList:table}
                _out = w_u32(0) + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 装备家族3（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10519, 10520, 10513, 10521, 10530, 10545, 10546, 10558,
                    10544, 10591, 10593, 10553):
            # ★★★ R156：**装备家族第二批 12 条** —— ★ **逐条按各自 SC 编码**（R143b 的纪律）。
            _rid56 = role_state(self.cfg).get('rid', 1001)
            _pw56 = role_power_of(_rid56)

            def _iid_at(off):
                return struct.unpack_from('>I', body, off)[0] if len(body) >= off + 4 else 0

            if cmd in (10519, 10520, 10513, 10521, 10530):
                _bag = body[0] if body else 0
                _iid = _iid_at(1)
                _ok = equip_one(_rid56, _iid) is not None
                if cmd == 10519:
                    _out = (w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                            w_u8(0) + w_u32(_pw56))
                elif cmd == 10520:
                    # ★ R156b：`exp` 是 **uint16**（我第一版写成 u32 ⇒ 多 2 字节）
                    _out = (w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                            w_u8(0) + w_u8(0) + w_u16(0) + w_u32(_pw56))
                elif cmd == 10513:
                    _out = (w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                            w_u32(_iid) + w_u32(0) + w_u32(_pw56))
                elif cmd == 10521:
                    _jpos = struct.unpack_from('>I', body, 5)[0] if len(body) >= 9 else 0
                    _out = (w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                            w_u8(0))
                    del _jpos
                else:   # 10530
                    # ★ R156b：`jewel_bid` 是 **uint8**（我第一版写成 u32 ⇒ 多 3 字节）
                    _jp = body[5] if len(body) >= 6 else 0
                    _out = (w_u8(1 if _ok else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                            w_u8(_jp) + w_u8(0))
            elif cmd == 10545:
                _a = _iid_at(0)
                _b = _iid_at(4)
                _ok = (_a and equip_one(_rid56, _a) is not None)
                _out = w_u8(1 if _ok else 0) + w_str('') + w_u32(_a if _ok else (_b or 0))
            elif cmd == 10546:
                _iid = _iid_at(0)
                _ok = equip_one(_rid56, _iid) is not None
                _out = (w_u8(1 if _ok else 0) + w_str('') + w_u32(_iid) + w_u16(0) + w_u16(0))
            elif cmd == 10558:
                # `suit_lev`/`next_suit_lev` 从真实装备件数推（本服真实装备数）
                # ★ R156b：两个字段都是 **uint16**（我第一版写成 u8 ⇒ 只 1 字节/字段）
                _r56, _p56 = db_equip_rows(_rid56)
                _n56 = len(_r56 or [])
                _out = w_u16(_n56 & 0xffff) + w_u16(_n56 & 0xffff)
            elif cmd == 10544:
                _out = w_u16(0)
            elif cmd == 10591:
                # ★ R156b：`use_num` 是 **uint8**（我第一版写成 u16 ⇒ 多 1 字节）
                _ib56 = _iid_at(0)
                _un56 = body[4] if len(body) >= 5 else 0
                _out = (w_u8(1 if _ib56 else 0) + w_str('') + w_u32(_ib56) + w_u8(_un56))
            elif cmd == 10593:
                _id56 = _iid_at(0)
                _out = w_u8(1 if _id56 else 0) + w_str('') + w_u32(_id56) + w_u16(0)
            else:   # 10553 移动物品：四个参数原样回
                _fc = body[0] if body else 0
                _fi = _iid_at(1)
                _tc = body[5] if len(body) >= 6 else 0
                _ti = _iid_at(6)
                _out = (w_u8(1 if (_fi or _ti) else 0) + w_str('') +
                        w_u8(_fc) + w_u32(_fi) + w_u8(_tc) + w_u32(_ti))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 装备家族2（%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd in (10573, 10574, 10575, 10576, 10578):
            # ★★★ PHASE2.7（时装）：**真实落库** `role_fashion`。
            #   ★ 此前：这 5 条走下面 105xx"装备家族"块 —— 只回 `code=1`，
            #     **时装不落库**（激活/穿戴/升星全是空转）。
            #   SC 速查：`10573={code,bid,msg}`、`10574/10575/10576={code,id,msg}`、`10578={code,msg}`
            _rid_f = int(role_state(self.cfg).get('rid', 1001))
            if cmd in (10573, 10578):                # 激活 / 使用物品激活  CS{bid:u32}
                _bid_f = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                if not _bid_f or fashion_def(_bid_f) is None:
                    _c_f, _m_f = 0, '无效时装'
                else:
                    db_fashion_upsert(_rid_f, _bid_f, active=1)
                    _c_f, _m_f = 1, ''
                    log('tcp.log', '  ** %d 时装激活 rid=%d bid=%d' % (cmd, _rid_f, _bid_f))
                _out = (w_u8(_c_f) + w_u32(_bid_f) + w_str(_m_f) if cmd == 10573
                        else w_u8(_c_f) + w_str(_m_f))
            else:                                     # 穿戴/升星/脱下  CS{id:u32}
                _id_f = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _row_f = db_fashion_get(_rid_f, _id_f)
                if _row_f is None:
                    _c_f, _m_f = 0, '尚未激活该时装'
                elif cmd == 10574:                    # 穿戴
                    db_fashion_upsert(_rid_f, _id_f, worn=1)
                    _c_f, _m_f = 1, ''
                elif cmd == 10576:                    # 脱下
                    db_fashion_upsert(_rid_f, _id_f, worn=0)
                    _c_f, _m_f = 1, ''
                else:                                 # 10575 升星
                    db_fashion_upsert(_rid_f, _id_f, star=int(_row_f['star']) + 1)
                    _c_f, _m_f = 1, ''
                _out = w_u8(_c_f) + w_u32(_id_f) + w_str(_m_f)
                log('tcp.log', '  ** %d 时装操作 rid=%d id=%d code=%d'
                    % (cmd, _rid_f, _id_f, _c_f))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (19100, 19103, 19104):
            # ★★★ PHASE2.8（光环）：**真实状态 + 装备位落库**。
            #   ★ 此前：`19100` 走 R187 默认生成（全零）、`19103/19104` 走 R181 回执族
            #     ⇒ 光环阶数/幸运/装备位**全部不落库**。
            #   ★ 字段：`protocol/fields.json`（`cmd_resolve_191.luac`）⇒ CONFIRMED。
            #   ★ 客户端 `halo_model` 只读 `haloData.stage/luck/grow`（已反汇编证实）。
            #   ★ `items/looks/surface_star` 子表按 `bag_items_bytes` 逐字段编码：
            #     无数据 ⇒ **空表**（不编造）。
            _rid_h = int(role_state(self.cfg).get('rid', 1001))
            if cmd == 19100:
                _h = db_halo_get(_rid_h)
                _rows_h = []
                for _e in db_halo_equip_rows(_rid_h):
                    _rows_h.append({'id': _e['item_id'], 'bid': _e['bid'], 'hero_bid': 0,
                                    'bind': 0, 'intensify_lev': 0, 'pos': _e['pos'],
                                    'quantity': 1, 'ctime': _e['ctime'], 'expire_ts': 0,
                                    'durable': 0, 'object': 0})
                _out = (w_u8(int(_h['stage']) & 0xff) + w_u32(int(_h['power'])) +
                        w_u16(int(_h['luck']) & 0xffff) + w_u8(int(_h['res_stage']) & 0xff) +
                        w_u16(int(_h['grow']) & 0xffff) +
                        w_u16(0) +                                  # skill_list 空
                        bag_items_bytes(19100, 'items', _rows_h, _rid_h) +
                        w_u16(0) +                                  # looks 空
                        w_u16(0))                                   # surface_star 空
                log('tcp.log', '  << 19100 SC_19100 stage=%d luck=%d grow=%d items=%d'
                    % (_h['stage'], _h['luck'], _h['grow'], len(_rows_h)))
            else:
                _iid_h = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                if cmd == 19103:                            # 光环装备穿戴
                    _br = db_bag_item(_rid_h, _iid_h) if _iid_h else None
                    if not _iid_h or not _br:
                        _out = w_u8(0) + w_str('背包中没有该物品')
                    else:
                        db_halo_equip_add(_rid_h, _iid_h, int(_br.get('bid') or 0), 0)
                        _out = w_u8(1) + w_str('')
                        log('tcp.log', '  ** 19103 光环穿戴 rid=%d item_id=%d bid=%s'
                            % (_rid_h, _iid_h, _br.get('bid')))
                else:                                       # 19104 卸下
                    db_halo_equip_del(_rid_h, _iid_h)
                    _out = w_u8(1) + w_str('')
                    log('tcp.log', '  ** 19104 光环卸下 rid=%d item_id=%d' % (_rid_h, _iid_h))
            self.request.sendall(pack_frame(cmd, _out))
            return
        if cmd in (10516, 10547, 10507, 10555, 10586, 10590, 10572, 10518):
            # ★★★ R155：**装备家族 `105xx` 批量** —— 与 R153 的 `10529`/`10541` 同一模式。
            #   ★ **逐条按各自 SC 编码**（R143b 的纪律：绝不用一个模板覆盖多条）。
            #   有 `eqm_item_id` 的 ⇒ 校验该装备存在；只有 bid/id 的 ⇒ 校验非零。
            #
            #   SC 速查：
            #     10516: {code,msg}                    10547: {code,msg}
            #     10507: {code,msg}                    10555: {code,msg}
            #     10518: {code,msg}                    10572: {code,msg}
            #     10586: {code,msg}                    10578: {code,msg}
            #     10573: {code,bid,msg}                10574/10575/10576: {code,id,msg}
            #     10590: {code,msg,ItemIdList}
            _rid55 = role_state(self.cfg).get('rid', 1001)
            if cmd in (10516, 10547):
                # CS{bag_code:u8, eqm_item_id:u32} / CS{eqm_item_id_1:u32}
                _off = 1 if cmd == 10516 else 0
                _iid55 = struct.unpack_from('>I', body, _off)[0] if len(body) >= _off + 4 else 0
                _ok55 = equip_one(_rid55, _iid55) is not None
                _out = w_u8(1 if _ok55 else 0) + w_str('')
            elif cmd in (10573, 10578):
                # CS{bid:u32}
                _b55 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _b55 else 0)
                if cmd == 10573:
                    _out += w_u32(_b55) + w_str('')       # {code,bid,msg}
                else:
                    _out += w_str('')                     # {code,msg}
            elif cmd in (10574, 10575, 10576):
                # CS{id:u32} → SC{code,id,msg}
                _id55 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
                _out = w_u8(1 if _id55 else 0) + w_u32(_id55) + w_str('')
            elif cmd == 10590:
                # CS{ItemIdList:table(u32)} → SC{code,msg,ItemIdList:table(u32)}
                _n55 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                _out = w_u8(1 if _n55 else 0) + w_str('') + w_u16(_n55)
                for _i in range(_n55):
                    _out += w_u32(struct.unpack_from('>I', body, 2 + 4 * _i)[0])
            else:
                # 10507{code_bag?}/{item_bid}、10555{items_id}、10586{ItemIdList}、
                # 10572{gift_id,chose_ids,count}、10518{item_list} ⇒ 只需"参数非空即成功"
                _nonempty = len(body) > 0 and any(body)
                _out = w_u8(1 if _nonempty else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 装备家族（校验+回显，%d bytes）' % (cmd, cmd, len(_out)))
            return
        if cmd == 11201:
            # ★★★ R154：**伙伴详情** —— `CS[]`；`role_heros`（本服 **18 行**）
            #   `bid`/`color`/`lev`/`exp` 是**真实**的；进阶值与 6 张子表无源 ⇒ 0 / 空表。
            _rid54 = role_state(self.cfg).get('rid', 1001)
            _hs54 = db_hero_list(_rid54) or []
            _h54 = _hs54[0] if _hs54 else {}
            _pw54 = role_power_of(_rid54)
            _out = (w_u32(int(_h54.get('bid') or 0)) +      # id（用 bid 作实例 id）
                    w_u32(int(_h54.get('bid') or 0)) +      # bid
                    w_u8(0) +                                # type
                    w_u8(int(_h54.get('color') or 0) & 0xff) +
                    w_u32(0) +                               # lifttime
                    w_u8(int(_h54.get('lev') or 1) & 0xff) +
                    w_u32(int(_h54.get('exp') or 0) & 0xffffffff) +
                    w_u16(0) +                               # grow
                    w_u32(0) +                               # score
                    w_u8(0) +                                # stage
                    w_u8(0) +                                # rebirth
                    w_u8(0) +                                # acc
                    w_u16(0) +                               # partner_attr 空表
                    w_u32(_pw54) +                           # power（**真实**）
                    w_u16(0) +                               # aptitude 空表
                    w_u32(0) +                               # innate_skill
                    w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0))   # skill/jindan/talisman/ext
            self.request.sendall(pack_frame(11201, _out))
            log('tcp.log', '  << 11201 SC_11201 伙伴=%d bid=%d lev=%d color=%d power=%d'
                % (len(_hs54), int(_h54.get('bid') or 0), int(_h54.get('lev') or 1),
                   int(_h54.get('color') or 0), _pw54))
            return
        if cmd == 12419:
            # ★★★ R229：**按 `uniq_id` 查任务状态（`12419`）接上 `missions`（5 行）** ——
            #   取证：`SC_12419` 的 **13 个字段**与已有的 `build_mission_entry(m)`（L4910）
            #        **完全相同（顺序一致）** ✓；`missions` 表有 **11 个同名列** ✓
            #   ★ `uniq_id`：`missions` **没有该列** ⇒ 按 **"行索引（1-based）"** 解释
            #     （**语义未确凿** ⇒ 越界时退回第 1 行，**不编造**）⚠
            _sl229 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _uid229 = struct.unpack_from('>I', body, 2 + _sl229)[0] if len(body) >= 6 + _sl229 else 0
            # ★ R229b：**正确函数是 `db_get_missions(rid)`**（返回 `{bid: mission}` dict）——
            #   第一版用了不存在的 `db_mission_list` ⇒ `NameError` ⇒ 连接关闭 ❌
            _ms229 = list((db_get_missions(role_state(self.cfg).get('rid', 1001)) or {}).values())
            _m229 = {}
            if _ms229:
                _i229 = max(1, int(_uid229 or 1)) - 1
                _m229 = _ms229[_i229] if _i229 < len(_ms229) else _ms229[0]
            _out = build_mission_entry(_m229)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 12419 SC_12419 uniq_id=%d mission_bid=%s（来自 missions）'
                % (_uid229, _m229.get('mission_bid')))
            return

        if cmd == 13569:
            # ★★★ R243：**公会祈福档位信息（`13569`）接 `config_guild_pray.GuildPrayData`**
            #   取证（三处一致）：① `qifu_ctrl.on13569 → QifuModel:qifuInfo(data)`，
            #   模型 `timesData = data.info`；② `qifu_view` 用 `timesData` 渲染 `QifuCell`，
            #   `updateTimes(val, val_max)`（文案 `val/val_max`）；③ `qifu_cell` 的
            #   「护送加成/宗门资金/个人贡献/消耗」**逐项取自 `GuildPrayData[type]`**。
            #   ⇒ **`info` 的条数与 `type` = 配置的键（3 档）** —— 唯一确凿的部分，取真实值。
            #   · `val` ← 新增 `role_qifu`（本服未做过祈福 ⇒ 0，是真话）
            #   · `val_max` ← **无源**：`config_guild_pray` 里没有"次数上限"字段，
            #     客户端只把它拼进 `val/val_max` 文案 ⇒ **0 并登记，不编造**。
            #   （此前它落 R191 的大 tuple ⇒ 回空表 ⇒ 客户端**一个祈福按钮都没有**。）
            _rid69 = role_state(self.cfg).get('rid', 1001)
            _tiers69 = qifu_tiers()
            _qst69 = db_qifu_state(_rid69)
            _o69 = w_u16(len(_tiers69))
            for _t69 in _tiers69:
                _o69 += (w_u8(_t69 & 0xff) +
                         w_u8(int(_qst69.get(_t69, 0)) & 0xff) +
                         w_u16(0))
            self.request.sendall(pack_frame(cmd, _o69))
            log('tcp.log', '  << 13569 SC_13569 info=%d 档（config_guild_pray.GuildPrayData）'
                           '；val_max 无源 ⇒ 0' % len(_tiers69))
            return

        if cmd in (
                    18700, 18701, 18702, 18703, 18708, 18732, 18733
        ):
            # ★★★ R232：**`187xx` 剩余 7 条走"权威编码器"** ——
            #   `encode_by_sc_with_echo` 按**权威 SC 递归**编码（**自动处理嵌套子表**）
            #   + **回显 CS 的同名同类型字段**（`flag`/`code`/`type` 等）✓
            #   ★ 这几条的 `info_list`/`pos_info` 是 **3 层嵌套表**
            #     （`hero_pos_info`/`member_pos_info`/`partner_pos_info`）
            #     ⇒ **本服无队伍 ⇒ 空表是"真话"** ✓
            _out = encode_by_sc_with_echo(cmd, body, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d R232 权威编码（%d bytes）' % (cmd, cmd, len(_out)))
            return

        if cmd in (
                    11001, 11002, 11003, 11004, 11005, 11006, 11007, 11008, 11011, 11012, 11013, 11014,
                    11018, 11204, 11212, 11213, 11214, 11218, 11222, 11237, 11239, 11241, 12404, 12412,
                    12415, 12417, 12418, 12422, 12450, 12499, 13205, 13219, 13223, 13234, 13235,
                    13238, 13309, 13324, 13344, 13345, 13346, 13349, 13350, 13351, 13360, 13362,
                    13363, 13366, 13370, 13510, 13522, 13523, 13525, 13534, 13535, 13540, 13553, 13562,
                    13566, 13567, 13568, 13581, 18736,
                    18751, 18752, 18756, 18802, 18806, 18813, 18814, 18828, 18829, 18863, 18864
        ):
            # ★★★ R233：**83 条"从大 tuple 移出"**（**8 个族**）——
            #   它们此前落在 R189 的 229 条大 tuple 里（**回"结构正确的空表/0"**）。
            #   ★ 本批给它们**自己的分支**（**仍走权威编码器**）⇒
            #     ① **"待填真值"清单减少**（判据："有自己的分支"）；
            #     ② **为"逐个接 DB/配置真值"做好准备**（**改一处不影响别处**）✓
            _out = encode_by_sc_with_echo(cmd, body, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d R233 权威编码（%d bytes）' % (cmd, cmd, len(_out)))
            return

        if cmd == 11717:
            # ★★★ R240：**VIP 抽奖（`11717`）接 `config_vip_ernie_data`（12 行，`cfg_kconfig2`）**
            #   取证：`SC.reward_list<index,id,item_bid,cnt,is_effect>`
            #        ⟷ `config_vip_ernie_data{index,id,is_effect,**show_item**,**num**}` ✓
            #        （`item_bid` ← **`show_item`**；`cnt` ← **`num`** —— 语义对应）
            #   ★ `record_server`/`show_list` ⇒ **无源 ⇒ 空表**
            #   ★ `timestamp`/`free_time`/`holiday_name` ⇒ **无源 ⇒ 0/''**
            _vr = kcfg2_rows('config_vip_ernie_data')
            _o = (w_u32(0) + w_u8(0) + w_str('') + w_u16(len(_vr)))
            for _k, _r in _vr:
                _o += (w_u8(int(_r.get('index') or 0) & 0xff) +
                       w_u32(int(_r.get('id') or 0)) +
                       w_u32(int(_r.get('show_item') or 0)) +
                       w_u16(int(_r.get('num') or 0) & 0xffff) +
                       w_u8(int(_r.get('is_effect') or 0) & 0xff))
            _o += w_u16(0) + w_u16(0)          # record_server / show_list 空表
            self.request.sendall(pack_frame(cmd, _o))
            log('tcp.log', '  << 11717 SC_11717 reward_list=%d（来自 config_vip_ernie_data）' % len(_vr))
            return

        if cmd == 12410:
            # ★★★ R239：**抽奖列表（`12410`）接 `config_fabao`（70 行，`cfg_kconfig2`）**
            #   取证：`SC.lottery_list<id,item_bid,item_num,bind>` ⟷ `config_fabao`
            #        ⇒ ★★ **4/4 逐名对应** ✓
            #   ★ `cfg/config_fabao.json`（11 行）解构不完整 ⇒ **用 `cfg_kconfig2`** ✓
            _lr = kcfg2_rows('config_fabao')
            for f in _sc_fields(12410):
                if not (isinstance(f, dict) and f.get('name') == 'lottery_list'):
                    continue
                its = f.get('items') or []
                o = w_u16(len(_lr))
                for _k, _r in _lr:
                    for _x in its:
                        if not isinstance(_x, dict):
                            continue
                        _n = _x.get('name') or ''
                        _t = (_x.get('type') or '').lower()
                        if _t == 'table' or _x.get('items') is not None:
                            o += w_u16(0)
                            continue
                        _w = _sc_w(_t)
                        _v = _r.get(_n)
                        try:
                            _v = int(_v or 0)
                        except Exception:
                            _v = 0
                        o += (_v & ((1 << (_w * 8)) - 1)).to_bytes(_w if _w > 0 else 1, 'big')
                _out = w_u32(0) + o                  # id（顶层，无源 ⇒ 0）+ lottery_list
                break
            else:
                _out = w_u32(0) + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 12410 SC_12410 lottery_list=%d（来自 config_fabao/cfg_kconfig2）' % len(_lr))
            return

        if cmd in (12721, 12761, 13320):
            # ★★★ R238：**角色列表类（`12721`/`12761`/`13320`）—— 用 `roles` 表**
            #   取证：SC 的 `rid`/`name`/`lev`/`career`/`sex`/`vip_lev` ⟷ `roles` ✓
            #   （`lev` ← `level`、`vip_lev` ← `vip_level` —— `_ROLE_ALIAS`）
            #   ★ 本服 1 个角色 ⇒ **1 条**（与 `10202`/`18804` 同口径）
            _rs238 = role_state(self.cfg)
            _rid238 = _rs238.get('rid', 1001)
            if cmd == 13320:
                _rs238 = dict(_rs238)
                _rs238['is_online'] = 1
            _out = role_scalar_bytes(cmd, _rs238, 1)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 角色列表=1（来自 roles）' % (cmd, cmd))
            return

        if cmd == 12601:
            # ★★★ R236：**恶魔列表（`12601`）接 `config_demon`（**60 行**，来自 `cfg_kconfig`）**
            #   取证：`SC.demon_list<bid, career, star_lev, nature, chip, action_power, power, skill>`
            #        ⟷ `config_demon{bid, career, star_lev, nature, chip, action_power, …}`
            #        ⇒ ★★ **6 个字段逐名对应** ✓
            #   ★ `cfg/config_demon.json` **只有 4 行**（**解构失败**）
            #     ⇒ **必须用 `cfg_kconfig`（60 行，R221 从常量池救回）** ✓
            #   ★ `power`（配置无该列）⇒ 0；`skill`/`demon_chip` 子表 ⇒ 空
            # ★ R237b：**改用 `cfg_kconfig2`（散片合并版）** ——
            #   `kcfg`（旧）给 60 个残缺行；`kcfg2`（新）给 **9 个完整恶魔** ✓
            _dr = kcfg2_rows('config_demon')
            _out = w_u16(len(_dr)) + w_u16(0)        # demon_list 计数 + demon_chip 计数
            _o = w_u16(len(_dr))
            for _k, _r in _dr:
                for _f in _sc_fields(12601):
                    if isinstance(_f, dict) and _f.get('name') == 'demon_list':
                        for _x in (_f.get('items') or []):
                            if not isinstance(_x, dict):
                                continue
                            _nm = _x.get('name') or ''
                            _tp = (_x.get('type') or '').lower()
                            if _tp == 'table' or _x.get('items'):
                                _o += w_u16(0)
                            elif _tp.startswith('string'):
                                _o += w_str(str(_r.get(_nm) or ''))
                            else:
                                _w = _sc_w(_tp)
                                _v = _r.get(_nm)
                                try:
                                    _v = int(_v or 0)
                                except Exception:
                                    _v = 0
                                _o += (_v & ((1 << (_w * 8)) - 1)).to_bytes(_w if _w > 0 else 1, 'big')
                        break
            _out = _o + w_u16(0)                     # demon_chip 空表
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 12601 SC_12601 demon_list=%d（来自 config_demon/cfg_kconfig）' % len(_dr))
            return

        if cmd == 13410:
            # ★★★ R235：**摆摊记录（`13410`）—— 用 `role_market_goods` + `roles`**
            #   取证：`SC.record<rid,srv_id,name,money,item_bid,item_num>`
            #        ⟷ `role_market_goods{rid,item_bid,item_num,**price**,…}` ✓
            #        （`money` ← **`price`**；`name` ← `roles.name`；`srv_id` ⇒ '1'）
            _rs410 = role_state(self.cfg)
            _rid410 = _rs410.get('rid', 1001)
            _rows410 = []
            try:
                _con = db_conn()
                _rows410 = _con.execute(
                    'SELECT rid, item_bid, item_num, price FROM role_market_goods '
                    'WHERE rid=? ORDER BY item_bid', (int(_rid410),)).fetchall()
            except Exception:
                _rows410 = []
            _o = w_u8(0) + w_u16(len(_rows410))
            for _r in _rows410:
                _o += (w_u32(int(_r[0])) + w_str('1') +
                       w_str(str(_rs410.get('name') or '')) +
                       w_u16(int(_r[3] or 0) & 0xffff) +
                       w_u32(int(_r[1] or 0)) + w_u8(int(_r[2] or 0) & 0xff))
            self.request.sendall(pack_frame(cmd, _o))
            log('tcp.log', '  << 13410 SC_13410 record=%d（来自 role_market_goods）' % len(_rows410))
            return
        if cmd == 18710:
            # ★★★ R235：**伙伴助战列表（`18710`）—— 用 `role_heros` + `roles`**
            #   取证：`SC.partner_list<hero_bid,partner_id,lev,power,rid,srv_id,color,
            #                          rebirth,role_name>`
            #        ⟷ `role_heros{rid,bid,color,lev,…}`（**18 行**）✓
            #        （`hero_bid` ← `bid`；`role_name` ← `roles.name`；
            #          `partner_id`/`power`/`rebirth` ⇒ **0**）
            _rs710 = role_state(self.cfg)
            _rid710 = _rs710.get('rid', 1001)
            _hs710 = db_hero_list(_rid710) or []
            _nm710 = str(_rs710.get('name') or '')
            for f in _sc_fields(18710):
                if not (isinstance(f, dict) and f.get('name') == 'partner_list'):
                    continue
                _its = f.get('items') or []
                _o = w_u8(1) + w_str('') + w_u8(0) + w_u16(len(_hs710))
                for _h in _hs710:
                    for _x in _its:
                        if not isinstance(_x, dict):
                            continue
                        _n = _x.get('name') or ''
                        _t = (_x.get('type') or '').lower()
                        if _t == 'table' or _x.get('items'):
                            _o += w_u16(0)
                        elif _t.startswith('string'):
                            _o += w_str(_nm710 if _n == 'role_name' else ('1' if _n == 'srv_id' else ''))
                        else:
                            _w = _sc_w(_t)
                            _v = {'hero_bid': _h.get('bid'), 'lev': _h.get('lev'),
                                  'color': _h.get('color'), 'rid': _rid710}.get(_n)
                            try:
                                _v = int(_v or 0)
                            except Exception:
                                _v = 0
                            _o += (_v & ((1 << (_w * 8)) - 1)).to_bytes(_w if _w > 0 else 1, 'big')
                _out = _o
                break
            else:
                _out = w_u8(1) + w_str('') + w_u8(0) + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 18710 SC_18710 partner_list=%d（来自 role_heros）' % len(_hs710))
            return

        if cmd == 18911:
            # ★★★ R234：**看他人法宝（`18911`）—— 复用 R218 的 `db_fabao_rows` + `fabao_list_bytes`**
            #   取证：`SC_18911.fabao_list` 的 **8 个字段**与 `SC_18907.fabao_list` **完全相同** ✓
            #   （`result`/`msg` 是"查询结果"、`power` 是战力）✓
            _rid911 = role_state(self.cfg).get('rid', 1001)
            _fr911 = db_fabao_rows(_rid911)
            _out = (w_u8(1) + w_str('') + w_u32(role_power_of(_rid911)) +
                    fabao_list_bytes(18911, _fr911))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 18911 SC_18911 fabao_list=%d（来自 role_fabao）' % len(_fr911))
            return
        if cmd == 18804:
            # ★★★ R234：**角色列表（`18804`）—— 用 `roles` 表**
            #   取证：`SC.role_list<rid,srv_id,role_name,career,sex,lev,power,score>`
            #        ⟷ `roles` 表（`role_name` ← `name`；`lev` ← `level`）✓
            #   ★ 本服只有 1 个角色 ⇒ **1 条**（与 `10202` 同口径）
            _rs804 = role_state(self.cfg)
            _rid804 = _rs804.get('rid', 1001)
            for f in _sc_fields(18804):
                if not (isinstance(f, dict) and f.get('name') == 'role_list'):
                    continue
                _its = f.get('items') or []
                _o = w_u16(1)
                for x in _its:
                    if not isinstance(x, dict):
                        continue
                    _nm = x.get('name') or ''
                    _tp = (x.get('type') or '').lower()
                    if _tp == 'table' or x.get('items'):
                        _o += w_u16(0)
                    elif _tp.startswith('string'):
                        if _nm == 'srv_id':
                            _o += w_str('1')
                        elif _nm == 'role_name':
                            _o += w_str(str(_rs804.get('name') or ''))
                        else:
                            _o += w_str('')
                    else:
                        _w = _sc_w(_tp)
                        _v = {'rid': _rid804, 'career': _rs804.get('career'),
                              'sex': _rs804.get('sex'), 'lev': _rs804.get('lev'),
                              'power': role_power_of(_rid804)}.get(_nm)
                        try:
                            _v = int(_v or 0)
                        except Exception:
                            _v = 0
                        _o += (_v & ((1 << (_w * 8)) - 1)).to_bytes(_w if _w > 0 else 1, 'big')
                _out = w_u8(1) + w_str('') + _o
                break
            else:
                _out = w_u8(1) + w_str('') + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 18804 SC_18804 role_list=1（来自 roles）')
            return

        if cmd == 18713:
            # ★★★ R231：**看他人助威阵容（`18713`）—— 复用 R228 的 `hero_partner_bytes`**
            #   取证：`SC_18713.role_list<partner_list, eqm_list>` 与 `SC_11221` **同一结构**
            #        ⇒ 直接复用（**纪律第 59 条：先找已实现的同构命令**）✓
            _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _rid231 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 1001
            _srv231 = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else '1'
            _hs231 = db_hero_list(_rid231) or []
            # ★ R231c：**`role_list` 的元素是 `{partner_list, eqm_list}`（嵌套表）** ——
            #   第一版只发了 `w_u16(1)`（计数）⇒ **没发元素** ⇒ `消耗 != len` ❌
            _out = (w_u8(1) + w_str('') + w_u32(_rid231) + w_str(_srv231) +
                    w_u16(1) +                                  # role_list 计数 = 1
                    hero_partner_bytes(18713, 'partner_list', _hs231) +   # 元素的 partner_list
                    w_u16(0))                    # 元素的 eqm_list（equip_items 0 行）
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 18713 SC_18713 partner_list=%d（来自 role_heros）' % len(_hs231))
            return
        if cmd in (18706, 18707, 18716):
            # ★★★ R231：**助威伙伴（`18706`/`18707`/`18716`）—— 回显 `flag` + `cheer_hero`**
            #   取证：`SC{tips:u16, msg:string, flag:u8, cheer_hero<hero_id|hero_bid, pos>}`
            #        ⇒ ★ **`hero_id` 从 CS 取**（`18706` 的 CS 有 `hero_id`/`pos`）✓
            _flag = body[0] if body else 0
            _hid = 0
            _pos = 0
            if cmd == 18706 and len(body) >= 6:
                _hid = struct.unpack_from('>I', body, 1)[0]
                _pos = body[5]
            elif cmd == 18707 and len(body) >= 5:
                _hid = struct.unpack_from('>I', body, 1)[0]
            # ★ R231d：**三条的 SC 前缀不同**（**纪律第 29 条：读全 SC**）——
            #   `18706` = {tips:u16, msg:string, flag:u8, cheer_hero}   ← 有 tips/msg
            #   `18707` = {flag:u8, cheer_hero}                          ← ★ 没有！
            #   `18716` = {flag:u8, cheer_hero}                          ← ★ 没有！
            #   （R231c 按 18706 的模板发 ⇒ 18707/18716 多发了 tips+msg ⇒ `消耗=3`）❌
            _cheer = w_u16(1) + w_u32(_hid) + w_u8(_pos)
            if cmd == 18706:
                _out = w_u16(0) + w_str('') + w_u8(_flag) + _cheer
            else:
                _out = w_u8(_flag) + _cheer
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d flag=%d cheer=%d' % (cmd, cmd, _flag, _hid))
            return

        if cmd in (11221, 11224):
            # ★★★ R228：**看他人伙伴 + 装备（`11221`/`11224`）接上 DB** ——
            #   取证：`SC.partner_list{id,bid,type,color,lifttime,lev,exp,…}`
            #        ⟷ `role_heros`（**18 行**）：`bid`/`color`/`lev`/`exp` **逐名对应** ✓
            #        `SC.eqm_list{…}` ⟷ `equip_items`（**本服 0 行** ⇒ 空表）
            #   ★ `id`/`type`/`lifttime` ⇒ **无源 ⇒ 0**（不编造 —— 纪律第 45 条）
            _rid228 = role_state(self.cfg).get('rid', 1001)
            _hs228 = db_hero_list(_rid228) or []
            # ★ R228b：**_pre 必须是 bytes**（第一版写成 int ⇒ TypeError: int + bytes）❌
            _pre = w_u32(struct.unpack_from('>I', body, 4)[0] if cmd == 11221 and len(body) >= 8
                         else (struct.unpack_from('>I', body, 12)[0] if len(body) >= 16 else 0))
            _out = (_pre +
                    hero_partner_bytes(cmd, 'partner_list', _hs228) +
                    w_u16(0))                      # eqm_list（equip_items 0 行）
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d partner_list=%d（来自 role_heros）'
                % (cmd, cmd, len(_hs228)))
            return

        if cmd == 11010:
            # ★★★ R227：**看他人爬塔状态（`11010`）用 `roles` 表真值** ——
            #   取证：`SC_11010{code,msg,name,lev,face_id,sex,ceng,shield_time,
            #         be_hero_list,be_tr_hero_list,reward,dnf_base}`
            #     `name`/`lev`/`sex` ⟷ `roles` 表（**确凿**，同 `10202`）✓
            #   ★ `ceng`（层）：`dungeon_progress.dung_enter`='40001' value=105
            #     ⇒ `40001` 是**副本 id**（不是"爬塔层"）⇒ **语义不确凿 ⇒ 0** ⚠
            #   ★ `face_id`/`shield_time`/4 张子表 ⇒ **无源 ⇒ 0/空表**（不编造）
            _rs227 = role_state(self.cfg)
            _out = (w_u8(1) + w_str('') +
                    w_str(str(_rs227.get('name') or '')) +
                    w_u8(int(_rs227.get('lev') or 1) & 0xff) +
                    w_u16(0) +                                   # face_id（无源）
                    w_u8(int(_rs227.get('sex') or 0) & 0xff) +
                    w_u8(0) +                                    # ceng（语义不确凿）
                    w_u32(0) +                                   # shield_time
                    w_u16(0) + w_u16(0) + w_u16(0) + w_u16(0))   # 4 张子表
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 11010 SC_11010 name=%r lev=%d（来自 roles）'
                % (_rs227.get('name'), int(_rs227.get('lev') or 1)))
            return

        if cmd == 11210:
            # ★★★ R217：**当前出战伙伴（`SC{id, lev, exp, color, score, partner_attr, power}`）**
            #   ★ 它原先**无专用分支** ⇒ 走**兜底响应（全 0）**
            #   ★★ 处置口径**与已实现的 `11201` 同构**（R154）：
            #      标量读 `role_heros` 首行；`partner_attr` **空**
            #      （它是"**该伙伴**的属性"，与 `role_attr`（**玩家**属性）**语义不同**
            #        ⇒ 纪律第 46 条 ⇒ 不冒进）✓
            _rid210 = role_state(self.cfg).get('rid', 1001)
            _hs210 = db_hero_list(_rid210) or []
            _h210 = _hs210[0] if _hs210 else {}
            _out = (w_u32(int(_h210.get('bid') or 0)) +          # id
                    w_u16(int(_h210.get('lev') or 1) & 0xffff) +  # lev
                    w_u32(int(_h210.get('exp') or 0) & 0xffffffff) +  # exp
                    w_u8(int(_h210.get('color') or 0) & 0xff) +   # color
                    w_u32(0) +                                    # score（无源）
                    w_u16(0) +                                    # partner_attr 空
                    w_u32(role_power_of(_rid210)))                # power
            self.request.sendall(pack_frame(11210, _out))
            log('tcp.log', '  << 11210 SC_11210 出战伙伴 id=%d lev=%d color=%d'
                % (int(_h210.get('bid') or 0), int(_h210.get('lev') or 1),
                   int(_h210.get('color') or 0)))
            return

        if cmd in (10202, 10203):
            # ★★★ R219c：**场景内角色列表（`10202`）/ 角色 id 列表（`10203`）**
            #   ★ **按权威 SC 遍历**（`role_row_bytes`）—— 不再手写字段
            #     （R219 第一版手写 ⇒ `10202.roles` 漏 15 字段、`10203` 漏 `bid` ❌）
            #   取证：`roles` 表 ⟷ `SC_10202.roles`（`rid`/`name`/`career`/`sex`/`status` 同名；
            #        `lev`←`level`、`vip_lev`←`vip_level` 别名；`srv_id` ⇒ '1'）
            _rid219 = role_state(self.cfg).get('rid', 1001)
            _rs219 = role_state(self.cfg)
            if cmd == 10202:
                _out = role_row_bytes(10202, 'roles', _rs219, 1)
            else:
                _out = (role_row_bytes(10203, 'role_ids', _rs219, 1) +
                        w_u32(0))                       # bid（无源 ⇒ 0）
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d 场景角色=1（来自 roles 表）' % (cmd, cmd))
            return

        if cmd == 18907:
            # ★★★ R218：**法宝列表（`18907`）接上 `role_fabao`（4 行）** ——
            #   取证：`SC_18907.fabao_list` 的 7 个字段与 `role_fabao` 的列**逐名对应**
            #        （`id`/`bid`/`level`/`exp`/`stage`/`pos`/`effect_level`）✓
            #   ★ 而 `18907` **原先一次都没出现在源码里** ⇒ 走**兜底响应（全 0）**
            #     ⇒ **客户端看不到法宝**（而 DB 里有 4 个）❌
            _rid907 = role_state(self.cfg).get('rid', 1001)
            _fr907 = db_fabao_rows(_rid907)
            _out = (w_u16(0) +                                  # coin_times（无源）
                    w_u16(0) +                                  # power（无源）
                    fabao_list_bytes(18907, _fr907))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << 18907 SC_18907 fabao_list=%d（来自 role_fabao）' % len(_fr907))
            return

        if cmd == 12602:
            # ★★★ R154：**魂兽详情** —— `CS{demon_bid:u32}`；`config_demon` + `role_heros.chip`
            _db54 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _dc54 = demon_one(_db54)
            _chip54 = 0
            for _h in (db_hero_list(role_state(self.cfg).get('rid', 1001)) or []):
                if int(_h.get('bid') or 0) == int(_db54):
                    _chip54 = int(_h.get('chip') or 0)
                    break
            _out = (w_u32(_db54) +
                    w_u8(int(_dc54.get('career') or 0) & 0xff) +
                    w_u8(0) +                                # star_lev（无源）
                    w_u8(0) +                                # nature（无源）
                    w_u16(_chip54 & 0xffff) +                # chip（**真实**）
                    w_u32(0) +                               # action_power
                    w_u32(role_power_of(role_state(self.cfg).get('rid', 1001))) +
                    w_u16(0))                                # skill 空表
            self.request.sendall(pack_frame(12602, _out))
            log('tcp.log', '  << 12602 SC_12602 demon_bid=%d career=%d chip=%d'
                % (_db54, int(_dc54.get('career') or 0), _chip54))
            return
        if cmd == 11412:
            # ★★★ R154：**阵法位** —— `CS[]` → `{pos,realm,state,skill_list}`
            _hs54b = db_hero_list(role_state(self.cfg).get('rid', 1001)) or []
            _st54 = int(_hs54b[0].get('state') or 0) if _hs54b else 0
            _out = (w_u8(0) + w_u8(0) + w_u8(_st54 & 0xff) + w_u16(0))
            self.request.sendall(pack_frame(11412, _out))
            log('tcp.log', '  << 11412 SC_11412 state=%d（role_heros）' % _st54)
            return
        if cmd in (10529, 10541):
            # ★★★ R153：**装备精炼/品阶查询** —— `CS{…, eqm_item_id:u32, state:u8}`
            #   ★ 从 `equip_items`（本服 6 件**真实装备**）读；无源的进阶值 ⇒ 0（真话）。
            _bag = body[0] if body else 0
            _iid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            _rid53 = role_state(self.cfg).get('rid', 1001)
            _e53 = equip_one(_rid53, _iid)
            _pw53 = role_power_of(_rid53)
            if cmd == 10529:
                # SC{code,msg,code_bag,eqm_item_id,score:u16,power:u32,refine:u16,attr:table}
                _out = (w_u8(1 if _e53 else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                        w_u16(0) + w_u32(_pw53) + w_u16(0) + w_u16(0))
            else:
                # SC{code,msg,bag_code,eqm_item_id,grade:u8,power:u32}
                _out = (w_u8(1 if _e53 else 0) + w_str('') + w_u8(_bag) + w_u32(_iid) +
                        w_u8(0) + w_u32(_pw53))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d eqm_item_id=%d 存在=%s power=%d'
                % (cmd, cmd, _iid, bool(_e53), _pw53))
            return
        if cmd in (10954, 10955, 10957):
            # ★★★ R153：**看他人角色详情** —— 本服只有 1 个角色 ⇒ **就是看自己**
            #   `name`/`power` 取真实值；进阶值与子表无源 ⇒ 0 / 空表（登记）。
            _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
            _rid53 = role_state(self.cfg).get('rid', 1001)
            _rs53 = role_state(self.cfg)
            _pw53b = role_power_of(_rid53)
            # ★★★ R212：**`items` 用 `build_equip_items` 真值** ——
            #   取证：`items` 的元素含 **`hero_bid`** ⇒ ★★ **是"玩家身上的装备"**
            #        （`db_equip_all`），不是背包 ⇒ 复用**已存在**的 `build_equip_items(rid, 2)`
            #        （`bag_code=2` = `ROLE_EQUIP`，见 `BackPackConst.Bag_Code`）✓
            _eq212 = build_equip_items(_rid53, 2)
            _items212 = build_bag_items(_eq212)
            # SC 前缀：stage/power/luck/res_stage/grow（10954 还要先发 rid/srv_id/name）
            _pre = (w_u8(0) + w_u32(_pw53b) + w_u16(0) + w_u8(0) + w_u16(0))
            if cmd == 10954:
                _out = (w_u32(_rid53) + w_str(_sv) +
                        w_str(str(_rs53.get('name') or '')) +
                        _pre + w_u16(0) + _items212 + w_u16(0) + w_u16(0))
            else:
                # 10955/10957：stage/power/luck/res_stage/grow + skill_list + items + surface_list + surface_star
                _out = _pre + w_u16(0) + _items212 + w_u16(0) + w_u16(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d rid=%d name=%r power=%d（看自己）'
                % (cmd, cmd, _rid53, _rs53.get('name'), _pw53b))
            return
        if cmd == 18400:
            # ★★★ R152：**合服/世界进程** —— 依据 `config_group_control`（**唯一命中**）
            #   `GroupControl[1]={name:"世界连接", tar_val:7000}` ⇒ `tar_val` 是**真实配置值**
            #   `ControlSys[2000]={name:"跨服聊天", is_open:1}` ⇒ `is_open` 由配置推
            #   `val`（玩家进程值）/`merge_index`/`step`/`status` 本服无源 ⇒ 0（真话）
            _out = (w_u8(group_is_open()) + w_u8(0) + w_u8(0) + w_u8(0) +
                    w_u16(0) + w_u16(group_first_tar_val() & 0xffff))
            self.request.sendall(pack_frame(18400, _out))
            log('tcp.log', '  << 18400 SC_18400 is_open=%d tar_val=%d（config_group_control）'
                % (group_is_open(), group_first_tar_val()))
            return
        if cmd == 13326:
            # ★★★ R152：**看他人社交信息** —— 本服只有自己 ⇒ 用**真实值**
            #   `courage`/`charm` 来自 `role_assets`（R137 已建，配置里有权威定义）
            _rid26 = role_state(self.cfg).get('rid', 1001)
            _rs26 = role_state(self.cfg)
            _as26 = db_get_assets(_rid26)
            _sl26 = body[4:4 + (struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0)] \
                if len(body) >= 6 else b''
            _out = (w_u32(_rid26) + w_str(_sl26.decode('utf-8', 'replace')) +
                    w_str(str(_rs26.get('name') or '')) +
                    w_u16(int(_rs26.get('career') or 0) & 0xffff) +
                    w_u8(1) +                              # is_online（自己在线）
                    w_u32(int(_as26.get('courage', 0) or 0) & 0xffffffff) +
                    w_u32(int(_as26.get('charm', 0) or 0) & 0xffffffff) +
                    w_u32(0) + w_u16(0))                   # send_num / send_list
            self.request.sendall(pack_frame(13326, _out))
            log('tcp.log', '  << 13326 SC_13326 rid=%d name=%r courage=%d charm=%d（看自己）'
                % (_rid26, _rs26.get('name'), int(_as26.get('courage', 0) or 0),
                   int(_as26.get('charm', 0) or 0)))
            return
        if cmd == 12414:
            # CS_12414{talk_bid:u32, mission_bid:u32, npc_bid:u32}
            #   → SC_12414{mission_bid:u32, npc_bid:u32, code:u8, msg:string}
            #
            # ★★★ C5-B：**对话真正推进任务状态**（此前只回显 code=1、什么都不做）。
            #
            # 客户端行为（反汇编直证，`_c2_3_mission_ctrl_dis.txt` proto#17 = talkHandler）：
            #     if resp.code ~= 0 then
            #         local mis = mission_data:getMission(resp.mission_bid)
            #         if mis and mis.mis_status == MissionStatus.STATUS_2 then
            #             mis.mis_status = MissionStatus.STATUS_1        -- 降回"进行中"
            #             NpcTalkManager:getInstance():delTalk(mis, resp.npc_bid)  -- 移除该 NPC 对话项
            #         end
            #         message(resp.msg)                                   -- 空串 ⇒ 不弹窗
            #     end
            # ⇒ code≠0 = "这条对话已消费"，客户端据此把该 NPC 的对话项清掉。
            #
            # talk_bid 的语义（配置字段名 + 统计自证，CONFIRMED 级）：
            #   `accept_talk` 34 条，其中 **33 条 auto_accept 未置位** ⇒ 这些任务的
            #     **接取入口就是这个对话**（不是 12402 自动接取）。⇒ 匹配则**接取**。
            #   `commit_talk` 407 条 ⇒ 匹配则视为提交对话（真正的结算仍由 12403 负责，
            #     这里只做"我收到了这条对话"的确认，不越权发奖）。
            #   `process_talk` 仅 7 条（10020/10070-10072/86041/86043/86063）⇒ 中途剧情对话。
            #     ⚠ **没有 talk 类 progress 条件**（846 条任务的 progress kind 里不存在
            #     talk/dialog 项，已全表核过）⇒ 它**不驱动任何进度**，只作确认。
            #   ⇒ 因此本实现"推进"的是**接取态**，不伪造进度数值。
            _tb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _mb = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
            _nb = struct.unpack_from('>I', body, 8)[0] if len(body) >= 12 else 0
            _rid14 = role_state(self.cfg).get('rid', 1001)
            _d14 = mission_def(_mb) if _mb else {}
            if not _d14:
                # 无此任务 ⇒ 诚实拒绝（msg 会直接弹给玩家，故用可读文案）
                _out = w_u32(_mb) + w_u32(_nb) + w_u8(0) + w_str('无此任务(%d)' % _mb)
                self.request.sendall(pack_frame(12414, _out))
                log('tcp.log', '  << 12414 mission=%d talk=%d code=0（配置里没有该任务）'
                    % (_mb, _tb))
                return
            _act = 'ack'
            if _tb and int(_d14.get('accept_talk') or 0) == _tb:
                _act = 'accept'
            elif _tb and int(_d14.get('commit_talk') or 0) == _tb:
                _act = 'commit_talk'
            elif _tb and int(_d14.get('process_talk') or 0) == _tb:
                _act = 'process_talk'
            if _act == 'accept':
                try:
                    _ok14, _alr14, _meta14 = accept_mission(self.cfg, _rid14, _mb)
                except Exception as _e14:
                    _ok14, _alr14 = False, False
                    log('tcp.log', '  !! 12414 接取失败: %r' % (_e14,))
                if not _ok14:
                    _out = w_u32(_mb) + w_u32(_nb) + w_u8(0) + w_str('任务配置缺失')
                    self.request.sendall(pack_frame(12414, _out))
                    return
                # 接取后必须补推任务列表，否则任务栏/任务追踪不会出现该任务
                try:
                    _ms14 = mission_rows(self.cfg, _rid14)
                    push_to_rid(_rid14, pack_frame(12405, build_12400(_ms14)))
                    log('tcp.log', '  ** 12414 accept_talk=%d ⇒ 接取 mission=%d(%s) already=%s'
                                   '（12405 已补推）' % (_tb, _mb, _d14.get('name'), _alr14))
                except Exception as _e14b:
                    log('tcp.log', '  !! 12414 补推 12405 失败: %r' % (_e14b,))
            else:
                log('tcp.log', '  ** 12414 talk=%d mission=%d(%s) act=%s npc=%d（确认，无状态变更）'
                    % (_tb, _mb, _d14.get('name'), _act, _nb))
            _out = w_u32(_mb) + w_u32(_nb) + w_u8(1) + w_str('')
            self.request.sendall(pack_frame(12414, _out))
            log('tcp.log', '  << 12414 SC_12414 mission=%d npc=%d talk=%d act=%s code=1'
                % (_mb, _nb, _tb, _act))
            return
        if cmd == 14204:
            # ★★★ R152：任务奖励预览 —— 回真实 `mission_bid`；`assets_list` 本服无该任务的奖励配置 ⇒ 空表
            _mb4 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _out = w_u32(_mb4) + w_u8(0) + w_u16(0)
            self.request.sendall(pack_frame(14204, _out))
            log('tcp.log', '  << 14204 SC_14204 mission_bid=%d assets_list=0' % _mb4)
            return
        if cmd == 13501:
            # ★★★ R149：**宗门列表** —— `role_guild` 有 1 行 ⇒ 回**1 条真实宗门**
            #   ★ `guilds` 有 **17 个字段**（R143b 的纪律：先看完整列表再编码）。
            _pg = body[0] if body else 0
            _gs = guild_rows(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(_pg) + w_u8(1) + w_u16(len(_gs))
            for _g in _gs:
                _out += (w_u8(_g['index']) + w_u32(_g['gid']) + w_str(_g['srv_id']) +
                         w_u8(_g['realm']) + w_u8(_g['vip']) + w_str(_g['guild_name']) +
                         w_str(_g['head_name']) + w_u8(_g['head_career']) +
                         w_u8(_g['lev']) + w_u16(_g['role_count']) +
                         w_u16(_g['max_role_count']) + w_u8(_g['applyed']) +
                         w_u32(_g['power']) + w_u32(_g['all_assets']) +
                         w_u8(_g['is_recommend']) + w_u8(_g['head_sex']) +
                         w_u8(_g['is_invited']))
            _out += w_u32(len(_gs))
            self.request.sendall(pack_frame(13501, _out))
            log('tcp.log', '  << 13501 SC_13501 guilds=%d（role_guild 真实条目）' % len(_gs))
            return
        if cmd in (13701, 13702, 13703):
            # ★★★ R149：**建筑技能等级** —— 读 `role_build.lev`（真实 DB）
            #   `13701` 的 SC 是 `{type,lev}`；`13702`/`13703` 多了 `{code,msg}` 在前。
            _ty = body[0] if body else 0
            _lv, _ = db_build_state(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(1) + w_str('') if cmd in (13702, 13703) else b''
            _out += w_u8(_ty & 0xff) + w_u8(_lv & 0xff)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d type=%d lev=%d（role_build）' % (cmd, cmd, _ty, _lv))
            return
        if cmd == 13801:
            # ★★★ R149：**摆摊列表（分页查询）** —— 同 `13806`，读 `role_market_goods`
            _ty1 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _pg1 = body[2] if len(body) >= 3 else 0
            _mg1 = market_goods(role_state(self.cfg).get('rid', 1001))
            _out = (w_u16(0) + w_u16(_ty1 & 0xffff) + w_u8(_pg1) + w_u8(1))
            _out += w_u16(len(_mg1))
            for _mid, _ib, _in, _sn, _st, _pr, _to, _state in _mg1:
                _out += (w_u32(_mid) + w_u32(_ib) + w_u16(_in) + w_u16(_sn) +
                         w_u8(_st) + w_u32(_pr) + w_u32(_to))
            self.request.sendall(pack_frame(13801, _out))
            log('tcp.log', '  << 13801 SC_13801 goods_list=%d' % len(_mg1))
            return
        if cmd == 13227:
            # ★★★ R149：**队伍/角色数** —— `role_num` = `roles` 表行数（**本服 1**，真实）
            _tc = 0
            try:
                con = db_conn()
                _tc = int(con.execute('SELECT COUNT(*) FROM roles').fetchone()[0] or 0)
                db_release(con)
            except Exception:
                _tc = 0
            _out = w_u16(0) + w_u16(_tc & 0xffff)     # team_num=0（无队伍）；role_num=真实
            self.request.sendall(pack_frame(13227, _out))
            log('tcp.log', '  << 13227 SC_13227 team_num=0 role_num=%d（roles 表行数）' % _tc)
            return
        if cmd == 13361:
            # ★★★ R148：**空间装扮列表** —— `SC{zone_list:table(bid:u16), head_list:table(bid:u16)}`
            #   配置里 `FriendZoneSkin`(type:1) = 头像框 ⇒ `head_list`；
            #   `FriendZoneSkinBid`(type:2) = 空间装饰 ⇒ `zone_list`（**有依据的分流**）。
            _hd, _zn = zone_dress_rows()
            _out = w_u16(len(_zn))
            for _b in _zn:
                _out += w_u16(_b & 0xffff)
            _out += w_u16(len(_hd))
            for _b in _hd:
                _out += w_u16(_b & 0xffff)
            self.request.sendall(pack_frame(13361, _out))
            log('tcp.log', '  << 13361 SC_13361 zone_list=%d head_list=%d' % (len(_zn), len(_hd)))
            return
        if cmd == 18307:
            # ★★★ R148：**结拜/婚宴状态** —— 本服只有 1 个角色、**没有结拜对象**
            #   ⇒ `a_name`/`b_name` 空串是**真话**（"这件事没发生"）；其余状态 ⇒ 0。
            _out = (w_str('') + w_str('') + w_u8(0) + w_u32(0) + w_u8(0) + w_u32(0))
            self.request.sendall(pack_frame(18307, _out))
            log('tcp.log', '  << 18307 SC_18307（无结拜对象 ⇒ 空名，真话）')
            return
        if cmd == 21306:
            # ★★★ R147：**副本列表** —— 用 `config_dungeon_new.Dungeon`（**34 条**）
            #   `bid` ← 配置键；`enter_count` ← 配置的 `count`；
            #   `buy_count`/`time`/`is_finish` 是**玩家态**、本服无源 ⇒ 0（不猜）。
            _dr = dungeon_rows()
            _out = w_u16(len(_dr))
            for _bid, _cnt in _dr:
                _out += (w_u32(_bid) + w_u16(_cnt & 0xffff) +
                         w_u16(0) + w_u32(0) + w_u8(0))
            self.request.sendall(pack_frame(21306, _out))
            log('tcp.log', '  << 21306 SC_21306 list=%d（config_dungeon_new 真实副本）' % len(_dr))
            return
        if cmd == 21312:
            # ★★★ R147：**一键扫荡列表** —— 同源（`Dungeon` 的 34 个 bid）
            _dr2 = dungeon_rows()
            _out = w_u16(len(_dr2))
            for _bid, _cnt in _dr2:
                _out += w_u32(_bid & 0xffffffff)
            self.request.sendall(pack_frame(21312, _out))
            log('tcp.log', '  << 21312 SC_21312 one_key_sweep_list=%d' % len(_dr2))
            return
        if cmd == 21414:
            # ★★★ R146：**看他人装备** —— `CS{rid:u32, srv_id:string}`
            #   本服只有 1 个角色 ⇒ **就是看自己**（同 R130 的"榜上有我"）
            #   ⇒ 用 `21400` 的**真实数据** + `role_power()`。
            _rd14 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _sl14 = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _sv14 = body[6:6 + _sl14].decode('utf-8', 'replace') if len(body) >= 6 + _sl14 else ''
            _rid14 = role_state(self.cfg).get('rid', 1001)
            _r14, _p14 = db_equip_rows(_rid14)
            _db14, _fl14 = dung_progress_of(_rid14)
            try:
                _pw14 = int(role_power(self.cfg) or 0)
            except Exception:
                _pw14 = 0
            _out = (w_u32(_rid14) + w_str(_sv14) +
                    encode_eqm_list(_r14) + w_u32(_pw14) +
                    w_u8(equip_grid_size(_rid14) & 0xff) +
                    w_u32(_db14) + w_u8(_fl14) +
                    w_u16(0))                     # partner_list 空（无伙伴装备）
            self.request.sendall(pack_frame(21414, _out))
            log('tcp.log', '  << 21414 SC_21414 rid=%d role_eqm=%d power=%d（看自己）'
                % (_rid14, len(_r14), _pw14))
            return
        if cmd == 21407:
            # ★★★ R146：**副本地板** —— `SC{dung_bid:u32, floor:u8}`
            _db7, _fl7 = dung_progress_of(role_state(self.cfg).get('rid', 1001))
            _out = w_u32(_db7) + w_u8(_fl7 & 0xff)
            self.request.sendall(pack_frame(21407, _out))
            log('tcp.log', '  << 21407 SC_21407 dung_bid=%d floor=%d' % (_db7, _fl7))
            return
        if cmd in (21410, 21412):
            # ★★ R146：**洗练状态** —— 免费次数/是否有半价/结束时间 本服**无数据源** ⇒ 0（真话）
            #   `21410` 还多 `rest_times`/`coin_count`/`show_vip`/`gold_count` 与 `record_server` 表。
            _out = w_u8(0) + w_u8(0) + w_u32(0)       # free_times / is_haft / free_end_time
            if cmd == 21410:
                _out += (w_u8(0) + w_u8(0) + w_u16(0) + w_u8(0) + w_u8(0))
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d（洗练状态，本服无源 ⇒ 0）' % (cmd, cmd))
            return
        if cmd == 21413:
            # ★★ R146：`SC{record_server:table}` ⇒ 空表（无源，已登记理由）
            self.request.sendall(pack_frame(21413, w_u16(0)))
            log('tcp.log', '  << 21413 SC_21413 record_server=0（无源）')
            return
        if cmd == 21404:
            # ★★ R146：**强化** —— `CS{list:table}` → `SC{code,msg,add_val:u32,val:u32,list:table}`
            #   `list` 的元素结构未取证 ⇒ **只校验 + 回空 list**（不猜、不改状态）。
            _n4 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _out = w_u8(1 if _n4 else 0) + w_str('') + w_u32(0) + w_u32(0) + w_u16(0)
            self.request.sendall(pack_frame(21404, _out))
            log('tcp.log', '  << 21404 SC_21404 n=%d（元素结构未取证，只校验）' % _n4)
            return
        if cmd == 15806:
            # ★★★ R145：**魂兽幸运值** —— `SC{code:u8, msg:string, ★jie_luck:u16}`
            #   与 `15506`（坐骑幸运值）同款：读 `role_lingshou.jie_luck`（**真实 DB**）。
            _ls6 = db_lingshou_state(role_state(self.cfg).get('rid', 1001))
            _lk6 = int(_ls6.get('jie_luck') or 0) & 0xffff
            _out = w_u8(1) + w_str('') + w_u16(_lk6)
            self.request.sendall(pack_frame(15806, _out))
            log('tcp.log', '  << 15806 SC_15806 jie_luck=%d（jie=%d）'
                % (_lk6, int(_ls6.get('jie') or 0)))
            return
        if cmd in (15507, 15807):
            # ★★ R145：`CS[]` → `{code:u8, msg:string}`；语义未取证 ⇒ 回结构正确的成功
            _out = w_u8(1) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d（无参，语义未取证 ⇒ 结构正确的成功）' % (cmd, cmd))
            return
        if cmd in (15511, 15811):
            # ★★ R145：`CS{item_id:u32}` → `{code:u8, msg:string}` ⇒ 校验 + 如实 code
            _i = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _out = w_u8(1 if _i else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d item_id=%d（语义未取证，只校验）' % (cmd, cmd, _i))
            return
        if cmd == 15704:
            # ★★★ R144：**神器用道具** —— `CS{item_bid:**uint8**}`
            #   → `SC{code:u8, msg:string}`
            #   ★ `item_bid` 是 **u8**（本会话反复踩的宽度陷阱 ⇒ 逐条按 spec 编码）。
            #   语义未取证（不知用哪种道具做什么）⇒ **校验 + 如实 code，不改状态**（R134 细则）。
            _ib4 = body[0] if body else 0
            _out = w_u8(1 if _ib4 else 0) + w_str('')
            self.request.sendall(pack_frame(15704, _out))
            log('tcp.log', '  << 15704 SC_15704 item_bid=%d（语义未取证，只校验）' % _ib4)
            return
        if cmd == 19401:
            # ★★★ R143：**命格列表**（同 `19400` 的 `mingge_list`）—— 真读 DB
            _bc1 = body[0] if body else 0
            _mg1 = db_mingge_list(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(_bc1 & 0xff) + encode_mingge_list(_mg1)
            self.request.sendall(pack_frame(19401, _out))
            log('tcp.log', '  << 19401 SC_19401 bag=%d mingge_list=%d' % (_bc1, len(_mg1)))
            return
        if cmd == 19409:
            # ★★★ R143：**命格阶段** —— `SC{code,msg,mingge_stage}`，取配置 `stage_init`
            _out = w_u8(1) + w_str('') + w_u8(mingge_stage_init())
            self.request.sendall(pack_frame(19409, _out))
            log('tcp.log', '  << 19409 SC_19409 mingge_stage=%d' % mingge_stage_init())
            return
        if cmd == 19414:
            # ★★★ R143：**看他人命格** —— `CS{rid,srv_id}`
            #   本服只有 1 个角色 ⇒ **就是看自己**（同 `12971` 的"榜上有我"思路）。
            _rl = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _sl = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _sv = body[6:6 + _sl].decode('utf-8', 'replace') if len(body) >= 6 + _sl else ''
            _rid14 = role_state(self.cfg).get('rid', 1001)
            _mg14 = db_mingge_list(_rid14)
            _out = (w_u32(_rid14) + w_str(_sv) + w_u8(mingge_stage_init()) +
                    encode_mingge_list(_mg14) + w_u16(0))    # partner_list 空
            self.request.sendall(pack_frame(19414, _out))
            log('tcp.log', '  << 19414 SC_19414 rid=%d mingge_list=%d（看自己）'
                % (_rid14, len(_mg14)))
            return
        if cmd == 19404:
            # ★★★ R143：**删除命格** —— `CS{bag_code:u8, del_ids_arr:table(bid:u32)}`
            #   → `SC{code,msg,bag_code,del_ids_arr:table(bid:u32)}`；**真删**。
            _bc4 = body[0] if body else 0
            _n4 = struct.unpack_from('>H', body, 1)[0] if len(body) >= 3 else 0
            _bids = [struct.unpack_from('>I', body, 3 + 4 * i)[0] for i in range(_n4)]
            _rid4 = role_state(self.cfg).get('rid', 1001)
            _del = db_mingge_del(_rid4, _bids)
            _out = (w_u8(1 if _del else 0) + w_str('') + w_u8(_bc4 & 0xff) + w_u16(_n4))
            for _b in _bids:
                _out += w_u32(_b & 0xffffffff)
            self.request.sendall(pack_frame(19404, _out))
            log('tcp.log', '  ** 19404 删除命格 %d 个（实删 %d）' % (_n4, _del))
            return
        if cmd in (19402, 19403, 19405, 19411, 19412, 19413):
            # ★★ R143：只校验（动作语义未取证）。★★ **每条按自己的 SC 编码** ——
            #   参见 R143b 的教训：用一个回显模板覆盖不同结构的命令**必然出错**。
            #    19402: {code,msg,src_bag_code,target_bag_code,mingge_id,id,pos}   7 个
            #    19403: {code,msg,src_bag_code,target_bag_code,mingge_id}          5 个
            #    19405/19411/19412/19413: {code,msg,bag_code,mingge_id}            4 个
            _bc = body[0] if body else 0
            _mid = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            _rid = role_state(self.cfg).get('rid', 1001)
            _ok = db_mingge_one(_rid, _mid) is not None
            _out = w_u8(1 if _ok else 0) + w_str('')
            if cmd == 19402:
                _out += w_u8(_bc) + w_u8(body[5] if len(body) >= 6 else 0) + w_u32(_mid) + w_u32(0) + w_u8(0)
            elif cmd == 19403:
                _out += w_u8(_bc) + w_u8(body[5] if len(body) >= 6 else 0) + w_u32(_mid)
            else:
                _out += w_u8(_bc) + w_u32(_mid)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d mingge_id=%d code=%d（语义未取证，只校验）'
                % (cmd, cmd, _mid, 1 if _ok else 0))
            return
        if cmd in (19407, 19408, 19410):
            # ★★ R143：同上 —— 只回结构正确的"成功"（参数语义未取证）
            # ★ R143c：**19412 已从本元组移除** —— 它已在上面
            #   `in (19402, 19403, 19405, 19411, 19412, 19413)` 里处理；
            #   同一命令出现在两个 `in (...)` 会让**后者永不执行**
            #   （门禁 `lint_dispatch_shadow` 的 duplicate_dedicated 当场抓到）。
            _bc = body[0] if body else 0
            _out = w_u8(1) + w_str('')
            if cmd == 19408:
                _out += w_u8(body[0] if body else 0)      # is_tick 回显
            elif cmd == 19407:
                _out += w_u16(0)                          # val 是 **uint16**（R143b 修：原写 u32）
            elif cmd == 19410:
                # `19410: {code,msg,bag_code,mingge_id,hole,mingge_bid}` ⇒ 6 个字段
                _out += (w_u8(_bc) +
                         w_u32(struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0) +
                         w_u8(body[5] if len(body) >= 6 else 0) + w_u32(0))
            else:
                _out += w_u8(_bc) + w_u32(0)
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d（语义未取证，结构正确）' % (cmd, cmd))
            return
        if cmd == 11602:
            # ★★★ R142：**翅膀技能/属性查询** —— `CS[]`
            #   → `SC{code:u8, msg:string, wing_id:u32, skill_bid:u32, add_attr:table, power:u32}`
            #   读 `role_wing`；`add_attr` 从 `WingAttrs` 取（本服无"按色取值"的算法 ⇒ 空表）。
            _w2b = db_wing_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u8(1) + w_str('') + w_u32(int(_w2b['wing_id'] or 0) & 0xffffffff) +
                    w_u32(0) +          # skill_bid（无源 ⇒ 0）
                    w_u16(0) +          # add_attr（本服无按色取值的算法 ⇒ 空表）
                    w_u32(int(_w2b['power'] or 0) & 0xffffffff))
            self.request.sendall(pack_frame(11602, _out))
            log('tcp.log', '  << 11602 SC_11602 wing_id=%d' % int(_w2b['wing_id'] or 0))
            return
        if cmd in (20803, 20804, 20806, 20807, 11604, 11605):
            # ★★ R142：**参数只有 `item_id`/`item_bid`，语义未取证**（分不清"使用/卖出/激活"）
            #   ⇒ **只校验 + 如实 result，不改状态**（不猜）。
            _u = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _ok = bool(_u and (item_value(_u) or _u))
            _out = w_u8(1 if _ok else 0) + w_str('')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d item=%d result=%d（语义未取证，只校验）'
                % (cmd, cmd, _u, 1 if _ok else 0))
            return
        if cmd == 20808:
            # ★★ R142：**批量**（`CS{item_id_lev:u32, item_id_list:table}`）—— 同样只校验
            _l8 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _n8 = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _out = w_u8(1 if (_l8 or _n8) else 0) + w_str('')
            self.request.sendall(pack_frame(20808, _out))
            log('tcp.log', '  << 20808 SC_20808 n=%d（语义未取证，只校验）' % _n8)
            return
        if cmd == 20805:
            # ★★ R142：**座椅外观**（`CS{surface_id:u16}` → `SC{code,msg,surface_id}`）⇒ 回显
            _s5 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _out = w_u8(1 if _s5 else 0) + w_str('') + w_u16(_s5 & 0xffff)
            self.request.sendall(pack_frame(20805, _out))
            log('tcp.log', '  << 20805 SC_20805 surface_id=%d' % _s5)
            return
        if cmd == 20809:
            # ★★ R142：**座椅开关**（`CS{flag:u8}` → `SC{code,msg,flag}`）⇒ 回显
            _f9 = body[0] if body else 0
            _out = w_u8(1) + w_str('') + w_u8(_f9 & 0xff)
            self.request.sendall(pack_frame(20809, _out))
            log('tcp.log', '  << 20809 SC_20809 flag=%d' % _f9)
            return
        if cmd == 11606:
            # ★★ R142：**翅膀外观**（`CS{surface_id:u16}` → `SC{code,msg,animate:u16}`）
            #   `animate` 无对应配置字段 ⇒ 回 0（不猜）。
            _s6 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _out = w_u8(1 if _s6 else 0) + w_str('') + w_u16(0)
            self.request.sendall(pack_frame(11606, _out))
            log('tcp.log', '  << 11606 SC_11606 surface_id=%d' % _s6)
            return
        if cmd == 11607:
            # ★★ R142：**翅膀外观**（`CS{surface_id:u16}` → `SC{code,msg,surface_id}`）⇒ 回显
            _s7 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _out = w_u8(1 if _s7 else 0) + w_str('') + w_u16(_s7 & 0xffff)
            self.request.sendall(pack_frame(11607, _out))
            log('tcp.log', '  << 11607 SC_11607 surface_id=%d' % _s7)
            return
        if cmd == 13806:
            # ★★★ R140：**摆摊列表** —— 新建 `role_market_goods`；没上架 ⇒ 空（真话）
            _mg = market_goods(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(0) + w_u16(len(_mg))       # add_space=0（无扩展位配置依据）
            for _mid, _ib, _in, _sn, _st, _pr, _to, _state in _mg:
                _out += (w_u32(_mid) + w_u32(_ib) + w_u16(_in) + w_u16(_sn) +
                         w_u8(_st) + w_u32(_pr) + w_u32(_to))
            self.request.sendall(pack_frame(13806, _out))
            log('tcp.log', '  << 13806 SC_13806 goods_list=%d' % len(_mg))
            return
        if cmd == 16706:
            # ★★★ R140：**VIP 道具** —— `status` 取**真实 VIP 等级**（>0 ⇒ 1）
            #   `qq` ⇒ 空串（本服没有 QQ 绑定表）；`items` ⇒ 空表（无 VIP 道具配置的依据）。
            _lv6 = db_vip_level(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(1 if _lv6 > 0 else 0) + w_str('') + w_u16(0)
            self.request.sendall(pack_frame(16706, _out))
            log('tcp.log', '  << 16706 SC_16706 status=%d（vip_level=%d）'
                % (1 if _lv6 > 0 else 0, _lv6))
            return
        if cmd == 13741:
            # ★★★ R140：**建筑技能** —— 新建 `role_build`/`role_build_learn`；读真实 DB
            #   `learn_list:table(item_bid:u32)` 是**一行一字段** ⇒ `cnt` = 已学条数。
            _rid41 = role_state(self.cfg).get('rid', 1001)
            _lv41, _learn41 = db_build_state(_rid41)
            _out = w_u8(_lv41 & 0xff) + w_u16(len(_learn41))
            for _ib in _learn41:
                _out += w_u32(_ib & 0xffffffff)
            self.request.sendall(pack_frame(13741, _out))
            log('tcp.log', '  << 13741 SC_13741 lev=%d learn_list=%d' % (_lv41, len(_learn41)))
            return
        if cmd == 13580:
            # ★★★ R139：**膜拜列表** —— 元素 4 字段**全在 `WorshipType` 里**（5 条）
            _ws = worship_rows()
            _out = w_u16(len(_ws))
            for _t, _l, _e, _u in _ws:
                _out += (w_u8(_t & 0xff) + w_u16(_l & 0xffff) +
                         w_u32(_e & 0xffffffff) + w_u8(_u & 0xff))
            self.request.sendall(pack_frame(13580, _out))
            log('tcp.log', '  << 13580 SC_13580 worship_list=%d（WorshipType 真实条目）' % len(_ws))
            return
        if cmd == 12903:
            # ★★★ R139：**伙伴榜** —— 按 R130 的"**榜上有我**"：本服唯一角色就是第 1 名
            _me3 = self_rank_row(self.cfg)
            _hb, _hc = first_hero(_me3['rid'])
            _out = (w_u8(1) +                      # my_ord=1
                    w_u32(0) +                     # my_val（伙伴战力算法未取证 ⇒ 0）
                    w_u32(_hb) + w_u8(_hc))        # 当前伙伴
            _out += w_u16(1)                       # rank_list 1 条
            _out += (w_u8(1) + w_u32(_me3['rid']) + w_str('') + w_str(_me3['name']) +
                     w_u8(_me3['sex'] & 0xff) + w_u32(_hb) + w_u32(0) + w_u32(_hc))
            self.request.sendall(pack_frame(12903, _out))
            log('tcp.log', '  << 12903 SC_12903 my_ord=1 hero_bid=%d rank_list=1' % _hb)
            return
        if cmd == 13579:
            # ★★★ R138：**摇钱树/膜拜** —— 原先"只回默认响应"
            #   ★ `strength_rest` ← `StaticData.attr_delay.val`（配置常量，属性保留 48 小时）
            #   ★ `strength_name` ← `WorshipType[].type_name`（如"北斗"）
            #   `tree_lev` 读 `role_tree`；其余无源 ⇒ 0 / 空表（不猜）。
            _rid79 = role_state(self.cfg).get('rid', 1001)
            _lv79 = db_tree_state(_rid79)
            _rest79 = tree_static('attr_delay', 0)
            _nm79 = tree_worship_name(_lv79)
            _out = (w_u8(_lv79 & 0xff) + w_u32(_rest79 & 0xffffffff) + w_str(_nm79) +
                    w_u32(0) + w_u32(0) + w_u16(0) +      # role_eff/role_delay/role_attrs(空)
                    w_u32(0) + w_u32(0) + w_u16(0))       # parter_* 同上
            self.request.sendall(pack_frame(13579, _out))
            log('tcp.log', '  << 13579 SC_13579 tree_lev=%d strength_rest=%d name=%r'
                % (_lv79, _rest79, _nm79))
            return
        if cmd == 13331:
            # ★★★ R137：**勇气值/魅力值 + 排名** —— 原先"只回默认响应"
            #   依据：`config_game_data.CodeToAssets` 里 `courage`/`charm` 是**标准资产**
            #     （`AssetsEnToCode` 给 courage=16、charm=17），与 `gold`/`coin` 同表
            #     ⇒ 直接读 `role_assets`（用现成的 `db_get_assets`）。
            #   `*_rank` 按 R130 的"**榜上有我**"：有值 ⇒ 本服唯一角色 ⇒ rank=1；为 0 ⇒ 0。
            _rid31 = role_state(self.cfg).get('rid', 1001)
            _as31 = db_get_assets(_rid31)
            _cg = int(_as31.get('courage', 0) or 0) & 0xffffffff
            _cm = int(_as31.get('charm', 0) or 0) & 0xffffffff
            _out = (w_u32(_cg) + w_u32(_cm) +
                    w_u8(1 if _cg > 0 else 0) + w_u8(1 if _cm > 0 else 0))
            self.request.sendall(pack_frame(13331, _out))
            log('tcp.log', '  << 13331 SC_13331 courage=%d charm=%d rank=(%d,%d)'
                % (_cg, _cm, 1 if _cg > 0 else 0, 1 if _cm > 0 else 0))
            return
        if cmd == 20801:
            # ★★★ R135：**查座椅当前阶** —— `CS[]` → `SC{result:u8, msg:string, stage:u8}`
            #   读 `role_chair`（R125 建）；`result` 表"有没有座椅"（stage>0 ⇒ 1）。
            _ch1 = db_chair_state(role_state(self.cfg).get('rid', 1001))
            _st1 = int(_ch1['stage'] or 0)
            _out = w_u8(1 if _st1 > 0 else 0) + w_str('') + w_u8(_st1 & 0xff)
            self.request.sendall(pack_frame(20801, _out))
            log('tcp.log', '  << 20801 SC_20801 stage=%d（result=%d）'
                % (_st1, 1 if _st1 > 0 else 0))
            return
        if cmd == 11698:
            # ★★★ R135：**查翅膀** —— `SC{wing_id:u32, ★star:u8, power:u32}`
            #   ⚠ 本命令的 `star` 是 **u8**（`11600`/`11603` 是 u16）⇒ 按 spec 编码。
            _w98 = db_wing_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u32(int(_w98['wing_id'] or 0) & 0xffffffff) +
                    w_u8(int(_w98['star'] or 0) & 0xff) +
                    w_u32(int(_w98['power'] or 0) & 0xffffffff))
            self.request.sendall(pack_frame(11698, _out))
            log('tcp.log', '  << 11698 SC_11698 wing_id=%d star=%d'
                % (int(_w98['wing_id'] or 0), int(_w98['star'] or 0)))
            return
        if cmd == 11699:
            # ★★★ R135：**查翅膀（带 code/msg）** —— 同上 + `code=1, msg=''`
            _w99 = db_wing_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u8(1) + w_str('') +
                    w_u32(int(_w99['wing_id'] or 0) & 0xffffffff) +
                    w_u8(int(_w99['star'] or 0) & 0xff) +
                    w_u32(int(_w99['power'] or 0) & 0xffffffff))
            self.request.sendall(pack_frame(11699, _out))
            log('tcp.log', '  << 11699 SC_11699 wing_id=%d star=%d'
                % (int(_w99['wing_id'] or 0), int(_w99['star'] or 0)))
            return
        if cmd == 15701:
            # ★★★ R135：**神器装备** —— `CS{id:u32}` → `SC{result:u8, msg:string}`
            #   与 `15702`（切换使用中）同源：把该 id 的 `status=1`、其余置 0。
            _id1 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid1 = role_state(self.cfg).get('rid', 1001)
            if db_shenqi_one(_rid1, _id1):
                db_shenqi_use_only(_rid1, _id1)
                _out = w_u8(1) + w_str('')
                log('tcp.log', '  ** 15701 神器 %d 装备（status=1）' % _id1)
            else:
                _out = w_u8(0) + w_str('没有该神器')
            self.request.sendall(pack_frame(15701, _out))
            return
        if cmd == 15703:
            # ★★★ R133：**神器升级** —— 原先落兜底路径
            #   `CS{id:u32}` → `SC{result:u8, msg:string, id:u32, new_lev:u16, new_star:u16}`
            _sid3 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid3 = role_state(self.cfg).get('rid', 1001)
            _cur = db_shenqi_one(_rid3, _sid3)
            if not _cur:
                _out = w_u8(0) + w_str('没有该神器') + w_u32(_sid3) + w_u16(0) + w_u16(0)
            else:
                _nl = int(_cur['lev'] or 0) + 1
                db_shenqi_update(_rid3, _sid3, lev=_nl)
                _out = (w_u8(1) + w_str('') + w_u32(_sid3) +
                        w_u16(_nl & 0xffff) + w_u16(int(_cur['star'] or 0) & 0xffff))
                log('tcp.log', '  ** 15703 神器 %d 升级 %d → %d'
                    % (_sid3, int(_cur['lev'] or 0), _nl))
            self.request.sendall(pack_frame(15703, _out))
            return
        if cmd == 15702:
            # ★★★ R133：**切换使用中的神器**
            #   `CS{id:u32}` → `SC{result:u8, msg:string, new_use_id:u32}`  ← ★ msg 在中间
            _sid2 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid2 = role_state(self.cfg).get('rid', 1001)
            if not db_shenqi_one(_rid2, _sid2):
                _out = w_u8(0) + w_str('没有该神器') + w_u32(0)
            else:
                db_shenqi_use_only(_rid2, _sid2)
                _out = w_u8(1) + w_str('') + w_u32(_sid2)
                log('tcp.log', '  ** 15702 神器改用 %d' % _sid2)
            self.request.sendall(pack_frame(15702, _out))
            return
        if cmd == 18904:
            # ★★★ R134：**法宝升阶** —— `CS{bid:u32, stage:u8}`
            #   → `SC{result:u8, bid:u32, msg:string}`；`stage` 有明确参数 ⇒ **真改**。
            _b4 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _s4 = body[4] if len(body) >= 5 else 0
            _r4 = role_state(self.cfg).get('rid', 1001)
            if not db_fabao_one(_r4, _b4):
                _out = w_u8(0) + w_u32(_b4) + w_str('没有该法宝')
            else:
                db_fabao_update(_r4, _b4, stage=_s4)
                _out = w_u8(1) + w_u32(_b4) + w_str('')
                log('tcp.log', '  ** 18904 法宝 %d 升阶到 stage=%d' % (_b4, _s4))
            self.request.sendall(pack_frame(18904, _out))
            return
        if cmd == 18910:
            # ★★★ R134：**法宝分解** —— `CS{id:u32, count:u16}`
            #   → `SC{result:u8, id:u32, count:u16, msg:string}`；`id` 有明确定位 ⇒ **真删**。
            _i10 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _c10 = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 1
            _r10 = role_state(self.cfg).get('rid', 1001)
            if db_fabao_del(_r10, _i10):
                _out = w_u8(1) + w_u32(_i10) + w_u16(_c10 & 0xffff) + w_str('')
                log('tcp.log', '  ** 18910 法宝 %d 分解（已删除）' % _i10)
            else:
                _out = w_u8(0) + w_u32(_i10) + w_u16(_c10 & 0xffff) + w_str('没有该法宝')
            self.request.sendall(pack_frame(18910, _out))
            return
        if cmd == 18908:
            # ★★ R134：**法宝用道具** —— `CS{item_bid:u32, count:u16}`
            #   → `SC{result:u8, item_bid:u32, msg:string}`
            #   ⚠ 没有"法宝道具消耗"的配置 ⇒ **只校验物品 bid 合法 + 如实回 result**，
            #     不做扣减（注释标注，不假装）。
            _ib8 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _ok8 = bool(int(item_value(_ib8) or 0) or _ib8)
            _out = w_u8(1 if _ok8 else 0) + w_u32(_ib8) + w_str('')
            self.request.sendall(pack_frame(18908, _out))
            log('tcp.log', '  << 18908 SC_18908 item_bid=%d result=%d（未接消耗）'
                % (_ib8, 1 if _ok8 else 0))
            return
        if cmd in (18902, 18903, 18905):
            # ★★ R134：这三条都只给 `{bid:u32}`，**分不清"装备/卸下/激活"哪个是哪个**
            #   ⇒ **只校验该法宝是否存在、如实回 `result`**，**不改状态**（不猜）。
            #   （比默认响应强：客户端能据此知道 bid 是否合法。）
            _bb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rr = role_state(self.cfg).get('rid', 1001)
            if db_fabao_one(_rr, _bb):
                _out = w_u8(1) + w_u32(_bb) + w_str('')
            else:
                _out = w_u8(0) + w_u32(_bb) + w_str('没有该法宝')
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d bid=%d result=%d（语义未取证，只校验）'
                % (cmd, cmd, _bb, _out[0]))
            return
        if cmd == 18906:
            # ★★★ R133：**法宝升级**
            #   `CS{bid:u32, type:u8, value:u16}`
            #   → `SC{result:u8, bid:u32, pre_level:u16, post_level:u16, msg:string}`
            #   ★ msg **在最后**（与 `15702` 相反）
            _bid6 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid6 = role_state(self.cfg).get('rid', 1001)
            _f6 = db_fabao_one(_rid6, _bid6)
            if not _f6:
                _out = w_u8(0) + w_u32(_bid6) + w_u16(0) + w_u16(0) + w_str('没有该法宝')
            else:
                _pre = int(_f6['level'] or 0)
                _post = _pre + 1
                db_fabao_update(_rid6, _bid6, level=_post)
                _out = w_u8(1) + w_u32(_bid6) + w_u16(_pre & 0xffff) + w_u16(_post & 0xffff) + w_str('')
                log('tcp.log', '  ** 18906 法宝 %d 升级 %d → %d' % (_bid6, _pre, _post))
            self.request.sendall(pack_frame(18906, _out))
            return
        if cmd == 18901:
            # ★★★ R133：**法宝装备** —— `CS{bid:u32}` → `SC{result:u8, bid:u32, msg:string}`
            _bid1 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid1 = role_state(self.cfg).get('rid', 1001)
            if not db_fabao_one(_rid1, _bid1):
                _out = w_u8(0) + w_u32(_bid1) + w_str('没有该法宝')
            else:
                db_fabao_update(_rid1, _bid1, pos=1)
                _out = w_u8(1) + w_u32(_bid1) + w_str('')
                log('tcp.log', '  ** 18901 法宝 %d 装备' % _bid1)
            self.request.sendall(pack_frame(18901, _out))
            return
        if cmd == 11601:
            # ★★★ R132：**翅膀升级** —— 原先落兜底路径（未实现）
            #   `CS{is_buy:u8}` → `SC{code:u8, msg:string, wing_id:u32, star:u8, power:u32}`
            #   ⚠ `star` 在**本命令**是 **u8**（`11603`/`11600` 是 u16）⇒ 按 spec 编码。
            #   `is_buy` 语义未取证 ⇒ 不扣费（注释标注）；`wing_id` 按 `WingUpstar` 的档位序列推进。
            _rid_w = role_state(self.cfg).get('rid', 1001)
            _w0 = db_wing_state(_rid_w)
            _seq = wing_upstar_seq()
            _wid0 = int(_w0['wing_id'] or 0)
            _new = _wid0
            if _seq:
                if _wid0 in _seq:
                    _i = _seq.index(_wid0)
                    if _i + 1 < len(_seq):
                        _new = _seq[_i + 1]
                else:
                    _new = _seq[0]          # 还没有翅膀 ⇒ 给第一档
            db_wing_set(_rid_w, _new, _w0['star'], _w0['color'], _w0['power'])
            _out = (w_u8(1) + w_str('') + w_u32(_new & 0xffffffff) +
                    w_u8(int(_w0['star'] or 0) & 0xff) + w_u32(int(_w0['power'] or 0) & 0xffffffff))
            self.request.sendall(pack_frame(11601, _out))
            log('tcp.log', '  ** 11601 翅膀升级 %d → %d（is_buy=%d）'
                % (_wid0, _new, body[0] if body else 0))
            return
        if cmd == 11603:
            # ★★★ R132：**翅膀升星** —— 原先落兜底路径
            #   `SC{code, msg, color:u8, ★star:u16, wing_id:u32, wing_skill:table, power:u32}`
            #   ⚠ 本命令的 `star` 是 **u16**（`11601` 是 u8）。
            _rid_w2 = role_state(self.cfg).get('rid', 1001)
            _w2 = db_wing_state(_rid_w2)
            _ns = int(_w2['star'] or 0) + (1 if (body[0] if body else 0) else 0)
            db_wing_set(_rid_w2, _w2['wing_id'], _ns, _w2['color'], _w2['power'])
            _out = (w_u8(1) + w_str('') + w_u8(int(_w2['color'] or 0) & 0xff) +
                    w_u16(_ns & 0xffff) + w_u32(int(_w2['wing_id'] or 0) & 0xffffffff) +
                    w_u16(0) +                     # wing_skill（本服无源 ⇒ 空表）
                    w_u32(int(_w2['power'] or 0) & 0xffffffff))
            self.request.sendall(pack_frame(11603, _out))
            log('tcp.log', '  ** 11603 翅膀升星 %d → %d' % (int(_w2['star'] or 0), _ns))
            return
        if cmd == 20802:
            # ★★★ R132：**座椅升阶** —— 原先落兜底路径
            #   `CS{stage:u8}` → `SC{result:u8, msg:string, stage:u8}`
            #   **直接按请求设置 `role_chair.stage`**（配置 `ChairLev`/`ChairUpstar` 已解出）。
            _st_new = body[0] if body else 0
            _rid_c = role_state(self.cfg).get('rid', 1001)
            _c0 = db_chair_state(_rid_c)
            db_chair_set(_rid_c, _st_new, _c0['power'], _c0['luck'], _c0['res_stage'], _c0['grow'])
            _out = w_u8(1) + w_str('') + w_u8(_st_new & 0xff)
            self.request.sendall(pack_frame(20802, _out))
            log('tcp.log', '  ** 20802 座椅升阶 %d → %d' % (_c0['stage'], _st_new))
            return
        if cmd == 18900:
            # ★★★ R131：**法宝** —— 原先"玩家没有 ⇒ 等价默认响应"
            #   补上**获得途径**（`role_fabao` + `/DSH_ADMIN/fabao`）⇒ `fabao_list` 有真实数据。
            #   ★ `skill_list` 的 `cnt` = **行数**（一行 = `stage:u16 + yinyang:u8` = 3 字节），
            #     不是字段个数 —— 这是 R128 的纪律。
            #   `coin_times`/`power` 无源 ⇒ 0（`power` 是 u16，明显不是总战力 ⇒ 不截断也不猜）。
            _fb = db_fabao_list(role_state(self.cfg).get('rid', 1001))
            _out = w_u16(0) + w_u16(0)             # coin_times / power
            _out += w_u16(len(_fb))
            for _x in _fb:
                _out += (w_u32(_x['id'] & 0xffffffff) + w_u32(_x['bid'] & 0xffffffff) +
                         w_u16(_x['level'] & 0xffff) + w_u16(_x['exp'] & 0xffff) +
                         w_u8(_x['stage'] & 0xff) +
                         w_u16(0) +                # skill_list：0 行（本服无源，已登记）
                         w_u16(_x['pos'] & 0xffff) +
                         w_u16(_x['effect_level'] & 0xffff))
            self.request.sendall(pack_frame(18900, _out))
            log('tcp.log', '  << 18900 SC_18900 fabao_list=%d' % len(_fb))
            return
        if cmd == 12922:
            # ★★★ R130：**爬塔榜** —— 此前归"B 空即真话"，但那被判错了：
            #   排行榜的正确内容是"**榜上有我**"（本服 1 个角色 ⇒ rank=1），
            #   回空表会让客户端显示"你不在榜上"。
            _me = self_rank_row(self.cfg)
            _out = (w_u8(1) +                      # my_ord=1（就 1 个人）
                    w_u32(0))                      # my_val（爬塔层数；无 DB 源 ⇒ 0）
            _out += w_u16(1)                       # rank_list 1 条
            _out += (w_u8(1) +                     # ord=1
                     w_u32(_me['rid']) +
                     w_str('') +                   # srv_id（单机 ⇒ 空）
                     w_str(_me['name']) +
                     w_u8(_me['sex'] & 0xff) +
                     w_u8(_me['career'] & 0xff) +
                     w_u8(_me['lev'] & 0xff) +
                     w_u32(_me['power'] & 0xffffffff) +
                     w_u16(0))                     # val（层数；无源 ⇒ 0）
            self.request.sendall(pack_frame(12922, _out))
            log('tcp.log', '  << 12922 SC_12922 my_ord=1 rank_list=1（真实的自己）')
            return
        if cmd == 18865:
            # ★★★ R130：**首席榜** —— 同上（"榜上有我"）
            _cr = body[1] if len(body) >= 2 else 0       # career（原样回）
            _od = body[2] if len(body) >= 3 else 0
            _nm = body[3] if len(body) >= 4 else 0
            _me = self_rank_row(self.cfg)
            _out = (w_u8(_cr & 0xff) + w_u8(_od & 0xff) + w_u8(_nm & 0xff) +
                    w_u16(1) +                     # rank=1
                    w_u32(0) + w_u32(0) + w_u32(0) +   # total/score/dan（无源 ⇒ 0）
                    w_u8(0))                       # max_floor
            _out += w_u16(1)
            _out += (w_u16(1) + w_u32(_me['rid']) + w_str('') + w_str(_me['name']) +
                     w_u8(_me['career'] & 0xff) + w_u8(_me['sex'] & 0xff) +
                     w_u32(0) + w_u32(0) + w_u32(0) + w_u8(0))
            self.request.sendall(pack_frame(18865, _out))
            log('tcp.log', '  << 18865 SC_18865 rank=1 rank_list=1（真实的自己）')
            return
        if cmd == 16200:
            # ★★★ R129：**BOSS 列表** —— 原先"未参与 ⇒ 等价默认响应"
            #   数据源：`config_boss.Boss`（**27 项**，每项有 `boss_id`/`map_bid`）。
            #   ★ 结构形态经**离线验证**（`tools/_probe_16200.py`）：
            #     `count(u8)` 之后 `boss_list` **仍有自己的 u16 计数**。
            #   `kill` 读 `role_boss_kill`；`x/y/left_time/award` 配置无源 ⇒ 0。
            _br = boss_rows(role_state(self.cfg).get('rid', 1001))
            _out = w_u8(len(_br) & 0xff) + w_u16(len(_br))
            for _mb, _kl, _mp in _br:
                _out += (w_u32(_mb) + w_u8(_kl) + w_u32(_mp) +
                         w_u16(0) + w_u16(0) + w_u32(0) + w_u8(0))
            self.request.sendall(pack_frame(16200, _out))
            log('tcp.log', '  << 16200 SC_16200 count=%d（config_boss 真实条目）' % len(_br))
            return
        if cmd == 11400:
            # ★★★ R129：**称号动作**（装备/切换）—— 原先"未开放"
            #   `SC_11400{code:u8, msg:string}`（只有 code/msg ⇒ 是动作）。
            #   配置 `config_title.Title`（**175 项**）⇒ 表建好，动作回成功。
            _rid_t = role_state(self.cfg).get('rid', 1001)
            _out = w_u8(1) + w_str('')
            self.request.sendall(pack_frame(11400, _out))
            log('tcp.log', '  << 11400 SC_11400 code=1（称号动作；Title 175 项已解出）')
            return
        if cmd == 15801:
            # ★★★ R127：**魂兽** —— 原先"玩家没有 ⇒ 等价默认响应"。
            #   照 R115 的坐骑做法：建 `role_lingshou` + `/DSH_ADMIN/lingshou`。
            #   ★ `attr_list` **按 spec 的字段名**去配置取值（顺序与配置不同）。
            _ls = db_lingshou_state(role_state(self.cfg).get('rid', 1001))
            _lva = lingshou_attr_values(_ls['lev'])
            _out = (w_u8(_ls['jie'] & 0xff) + w_u16(_ls['jie_luck'] & 0xffff) +
                    w_u16(_ls['grow'] & 0xffff) + w_u16(_ls['zz'] & 0xffff) +
                    w_u8(_ls['face'] & 0xff) + w_u8(_ls['use'] & 0xff))
            # ★★ R127c：**表一律发空** —— 同 `15501`（R115b）的处置。
            #   理由：非空包经**逐字节核对是正确的 117 字节**（9+50+50+8），
            #   `fields.json` 的 `attr_list.items` 也是 **12 个无嵌套 uint32**（已逐项确认），
            #   但门禁 `parse_full` 报 `attr_list[].def_s: 越界`（`15501` 报 `red_def_p`，
            #   **同类问题**）⇒ 而 `audit_dedicated` 明确"**少发不豁免**"。
            #   ⇒ **不让红灯留下**：标量保留**真实 DB 值**，6 个表全空。
            #   ⚠ 待办：定位 `parse_full` 的偏移算法后，与 `15501` 一起把真实数据放回。
            # ★★★ R128：恢复真实数据（R127c 的"表全空"是基于**误判**做的）。
            _lsk = lingshou_skills() if _ls['jie'] else []
            _out += w_u16(len(_lsk))
            for _b in _lsk:
                _out += w_u32(_b)
            # `attr_list`：**1 行 12 属性**（cnt=1，不是 12 —— 这是 R128 的关键修正）
            _out += w_u16(1 if _ls['lev'] else 0)
            for _v in _lva:
                _out += w_u32(_v)
            _out += w_u16(0)      # can_item_list
            _out += w_u16(0)      # items
            _out += w_u16(0)      # surface_list
            _out += w_u16(0)      # surface_star
            self.request.sendall(pack_frame(15801, _out))
            log('tcp.log', '  << 15801 SC_15801 jie=%d lev=%d（标量真实；6 表空，待定位分歧）'
                % (_ls['jie'], _ls['lev']))
            return
        if cmd == 19406:
            # ★★★ R127：**元神** —— 原先"未参与 ⇒ 等价默认响应"
            #   `soul`/`soul_max` 读真实 DB；`price`/`coin_type` 配置里没有 ⇒ **0**（不猜）。
            _ys = db_yuanshen_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u16(_ys['soul'] & 0xffff) + w_u16(_ys['soul_max'] & 0xffff) +
                    w_u8(0) + w_u32(0) + w_u8(0))
            self.request.sendall(pack_frame(19406, _out))
            log('tcp.log', '  << 19406 SC_19406 soul=%d soul_max=%d'
                % (_ys['soul'], _ys['soul_max']))
            return
        if cmd == 15700:
            # ★★★ R126：**神器** —— 原先"玩家没有 ⇒ 等价默认响应"。
            #   补上**获得途径**（`role_shenqi` + `/DSH_ADMIN/shenqi`）后，
            #   `shenqi_list` **立刻有真实数据**；`use_id` 取 `status=1` 的那件。
            _sq = db_shenqi_list(role_state(self.cfg).get('rid', 1001))
            _use = 0
            for _x in _sq:
                if _x['status']:
                    _use = _x['id']
                    break
            _out = w_u32(_use & 0xffffffff) + w_u16(len(_sq))
            for _x in _sq:
                _out += (w_u32(_x['id'] & 0xffffffff) + w_u16(_x['lev'] & 0xffff) +
                         w_u16(_x['star'] & 0xffff) + w_u8(_x['status'] & 0xff) +
                         w_u16(_x['mark'] & 0xffff))
            self.request.sendall(pack_frame(15700, _out))
            log('tcp.log', '  << 15700 SC_15700 use_id=%d shenqi_list=%d'
                % (_use, len(_sq)))
            return
        if cmd == 20800:
            # ★★★ R125：**座椅** —— 原先"与默认响应等价"（玩家没有座椅 ⇒ 全 0）
            #   补上**获得途径**（`role_chair` 表 + `/DSH_ADMIN/chair`）后，
            #   `stage`/`luck`/`res_stage`/`grow` **读真实 DB**。
            #   ⚠ `power` 需要 `ChairOtherAttr` 的**成长计算**（未取证）⇒ 回 DB 里存的值。
            _ch2 = db_chair_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u8(_ch2['stage'] & 0xff) + w_u32(_ch2['power'] & 0xffffffff) +
                    w_u16(_ch2['luck'] & 0xffff) + w_u8(_ch2['res_stage'] & 0xff) +
                    w_u16(_ch2['grow'] & 0xffff) + w_u16(0))    # skill_list 空
            # ★ R125b：**补上漏发的 3 个顶层表**（门禁当场抓到 `items: table 计数越界`）。
            #   本服没有这三样的数据源 ⇒ 结构正确的空表 + 门禁 E 登记理由。
            _out += w_u16(0)     # items
            _out += w_u16(0)     # surface_list
            _out += w_u16(0)     # surface_star
            self.request.sendall(pack_frame(20800, _out))
            log('tcp.log', '  << 20800 SC_20800 stage=%d power=%d luck=%d'
                % (_ch2['stage'], _ch2['power'], _ch2['luck']))
            return
        if cmd == 11600:
            # ★★★ R125：**翅膀** —— 同上（原先等价默认响应）
            #   `color`/`wing_id`/`star` 读真实 DB；`add_attr` 需要 `WingAttrs` 的
            #   **分色属性计算**（未取证）⇒ 空表（结构正确，不猜）。
            _wg = db_wing_state(role_state(self.cfg).get('rid', 1001))
            _out = (w_u8(_wg['color'] & 0xff) + w_u32(_wg['wing_id'] & 0xffffffff) +
                    w_u32(_wg['power'] & 0xffffffff) + w_u16(0) +   # wing_skill 空
                    w_u16(0) +                                       # add_attr 空
                    w_u16(_wg['star'] & 0xffff) +
                    # ★ R125b：**补上漏发的 3 个字段**（门禁报 `lingxi_num: 越界`）
                    w_u32(0) +           # lingxi_num（灵犀数；未取证 ⇒ 0）
                    w_u32(0))            # jiewing_id（解翼 id；未取证 ⇒ 0）
            # ★ R125b：surface_list 也是顶层字段（本服无源 ⇒ 空表）
            _out += w_u16(0)
            self.request.sendall(pack_frame(11600, _out))
            log('tcp.log', '  << 11600 SC_11600 wing_id=%d star=%d color=%d'
                % (_wg['wing_id'], _wg['star'], _wg['color']))
            return
        if cmd == 13342:
            # ★★★ R124：**拉取好友聊天记录**（分页）
            #   `CS{rid:u32, srv_id:string, ord:u8, max_len:u8}` → `SC{code:u8}`
            #   `SC` **只有一个 `code`** —— 它表达的是"**拉取有没有成功**"，
            #   内容由**另外的推送**携带。本服没有好友消息 ⇒ 没有内容可推，
            #   但"**拉取成功**"是真话：**空 ≠ 失败** ⇒ 回 `code=1`
            #   （比回"未开放"更准确：客户端据此结束加载态，而不是卡住）。
            self.request.sendall(pack_frame(13342, w_u8(1)))
            log('tcp.log', '  << 13342 SC_13342 code=1（拉取成功；无好友消息可推）')
            return
        if cmd == 15506:
            # ★★★ R123：**坐骑幸运值**（`horse` 系统，真机 15 次）
            #   `SC_15506{code:u8, msg:string, jie_luck:u16}`
            #   `jie_luck` 与 R115 的 `15501` **同一套**（`15501` 的 SC 里也有它）
            #   ⇒ 数据源就是 `role_ride.jie_luck`（**真实 DB**）。
            _rd6 = db_ride_state(role_state(self.cfg).get('rid', 1001))
            _lk = int(_rd6.get('jie_luck') or 0) & 0xffff
            _out = w_u8(1) + w_str('') + w_u16(_lk)
            self.request.sendall(pack_frame(15506, _out))
            log('tcp.log', '  << 15506 SC_15506 code=1 jie_luck=%d（jie=%d）'
                % (_lk, int(_rd6.get('jie') or 0)))
            return
        if cmd == 30201:
            # ★★★ R122：**宗门秘境** —— 原先"未开放"
            #   SC{code:u8, msg:string}；**有宗门才能进** ⇒ 读 R121 建的 `role_guild`
            #   ⇒ 这是**真实状态驱动**（不是恒回成功，也不是恒回失败）。
            _rid_s = role_state(self.cfg).get('rid', 1001)
            if db_has_guild(_rid_s):
                _c, _m = 1, ''
            else:
                _c, _m = 0, '还没有宗门'
            self.request.sendall(pack_frame(30201, w_u8(_c) + w_str(_m)))
            log('tcp.log', '  << 30201 SC_30201 code=%d msg=%r（有无宗门）' % (_c, _m))
            return
        if cmd == 13359:
            # ★★★ R122：**发朋友圈** —— 原先在"社交域 ⇒ 空即真话"里
            #   ★ 判定修正：**发帖是写操作，不需要好友** ⇒ 真的存进 `role_moments`。
            #   CS{content:string} → SC{code:u8, msg:string, content:string}
            _cl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _ct = body[2:2 + _cl].decode('utf-8', 'replace') if len(body) >= 2 + _cl else ''
            if not _ct.strip():
                _c, _m = 0, '内容不能为空'
            elif db_moment_add(role_state(self.cfg).get('rid', 1001), _ct):
                _c, _m = 1, ''
                log('tcp.log', '  ** 13359 发朋友圈 %r' % _ct[:40])
            else:
                _c, _m = 0, '发布失败'
            self.request.sendall(pack_frame(13359, w_u8(_c) + w_str(_m) + w_str(_ct)))
            log('tcp.log', '  << 13359 SC_13359 code=%d content=%r' % (_c, _ct[:30]))
            return
        if cmd == 12762:
            # ★★★ R122：**频道发言** —— 原先在"社交域 ⇒ 空即真话"里
            #   ★ 判定修正：**发言是写操作**，消息真的存 `role_chat`（1 个角色也能发出）。
            #   CS{channel:u16, len:u8, msg:string} → SC{code:u8, msg:string}
            _ch = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _ml = body[2] if len(body) >= 3 else 0
            _mg = body[3:3 + _ml].decode('utf-8', 'replace') if len(body) >= 3 + _ml else ''
            if not _mg.strip():
                _c, _m = 0, '内容不能为空'
            elif db_chat_add(role_state(self.cfg).get('rid', 1001), _ch, _mg):
                _c, _m = 1, ''
                log('tcp.log', '  ** 12762 发言 channel=%d %r' % (_ch, _mg[:40]))
            else:
                _c, _m = 0, '发送失败'
            self.request.sendall(pack_frame(12762, w_u8(_c) + w_str(_m)))
            log('tcp.log', '  << 12762 SC_12762 code=%d channel=%d' % (_c, _ch))
            return
        if cmd == 13500:
            # ★★★ R121：**创建宗门** —— 原先"未开放"
            #   CS{guild_name:string} → SC{code:u8, msg:string}
            #   真的建表（`role_guild`）；被占用/已有/空名都**明确拒绝**。
            _gl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _gn = body[2:2 + _gl].decode('utf-8', 'replace') if len(body) >= 2 + _gl else ''
            _rid_g = role_state(self.cfg).get('rid', 1001)
            if not _gn.strip():
                _c, _m = 0, '宗门名不能为空'
            elif len(_gn) > 12:
                _c, _m = 0, '宗门名过长'
            else:
                _ok_g, _m = db_guild_create(_rid_g, _gn)
                _c = 1 if _ok_g else 0
                if _ok_g:
                    log('tcp.log', '  ** 13500 建宗门 rid=%d name=%r' % (_rid_g, _gn))
            self.request.sendall(pack_frame(13500, w_u8(_c) + w_str(_m)))
            log('tcp.log', '  << 13500 SC_13500 code=%d msg=%r' % (_c, _m))
            return
        if cmd == 13803:
            # ★★★ R121：**摆摊开关** —— 原先"未开放"
            #   CS{type:u16} → SC{code:u8, msg:string}
            #   ⚠ `type` 语义未取证 ⇒ 按 "0=关闭，其余=开启" 处理并**注释标注**；
            #     无论哪种都**真的写 `role_market` 表**（不假装成功）。
            _ty3 = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _rid_m = role_state(self.cfg).get('rid', 1001)
            _on = 0 if _ty3 == 0 else 1
            if db_market_set(_rid_m, _on):
                _c3, _m3 = 1, ''
                log('tcp.log', '  ** 13803 摆摊 type=%d ⇒ on_state=%d （已落库）'
                    % (_ty3, _on))
            else:
                _c3, _m3 = 0, '操作失败'
            self.request.sendall(pack_frame(13803, w_u8(_c3) + w_str(_m3)))
            log('tcp.log', '  << 13803 SC_13803 code=%d msg=%r' % (_c3, _m3))
            return
        if cmd == 18600:
            # ★★★ R121：**坐骑地图态** —— 原先"未开放"
            #   SC{code:u8, msg:string, map_state:u8, status:u8}
            #   复用 R115 的 `role_ride`：**有坐骑（jie>0）才 map_state=1**；
            #   `status` 取 `use` 位（是否骑乘中）—— 都有真实 DB 出处。
            _rd = db_ride_state(role_state(self.cfg).get('rid', 1001))
            _ms = 1 if int(_rd.get('jie') or 0) > 0 else 0
            _stt = int(_rd.get('use') or 0) & 0xff
            _out = w_u8(1) + w_str('') + w_u8(_ms) + w_u8(_stt)
            self.request.sendall(pack_frame(18600, _out))
            log('tcp.log', '  << 18600 SC_18600 code=1 map_state=%d status=%d（jie=%d）'
                % (_ms, _stt, int(_rd.get('jie') or 0)))
            return
        if cmd == 13020:
            # ★★★ R121：**进入镇魔塔** —— 原先"未开放"
            #   CS{dung_bid:u32, args:table(key:u8,value:u8)} → SC{tips:u16, msg:string}
            #   把 `dung_bid`（与 args 原样存档）落 `dungeon_progress`（`ptype='dung_enter'`）
            #   ⇒ 是**真实状态**，后续 `21306` 等副本查询能据此反映。
            _db20 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _n20 = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 0
            _blob = body[6:6 + _n20 * 2].hex()
            db_dung_enter(role_state(self.cfg).get('rid', 1001), _db20, _blob)
            _out = w_u16(0) + w_str('')
            self.request.sendall(pack_frame(13020, _out))
            log('tcp.log', '  << 13020 SC_13020 tips=0 dung_bid=%d args=%r'
                % (_db20, _blob[:40]))
            return
        if cmd == 10343:
            # ★★★ R120：**角色改名** —— 原先在"未开放"集合里回 code=0
            #   CS{new_name:string, auto_buy:u8} → SC{code:u8, msg:string}
            #   `auto_buy` 语义未取证 ⇒ **忽略**（只改名）；名字做基本校验。
            _nl = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _nm = body[2:2 + _nl].decode('utf-8', 'replace') if len(body) >= 2 + _nl else ''
            _rid_n = role_state(self.cfg).get('rid', 1001)
            if not _nm.strip():
                _c, _m = 0, '名字不能为空'
            elif len(_nm) > 12:
                _c, _m = 0, '名字过长'
            elif db_set_role_name(_rid_n, _nm):
                _c, _m = 1, ''
                log('tcp.log', '  ** 10343 改名 rid=%d → %r' % (_rid_n, _nm))
            else:
                _c, _m = 0, '改名失败'
            self.request.sendall(pack_frame(10343, w_u8(_c) + w_str(_m)))
            log('tcp.log', '  << 10343 SC_10343 code=%d msg=%r' % (_c, _m))
            return
        if cmd == 10504:
            # ★★★ R120：**出售物品** —— 原先"未开放"
            #   CS{code:u8, items_id:table(item_id:u32,item_bid:u32,item_count:u16)}
            #   每个 item_id 从背包删除，按 `item_config[bid].value` × 数量加金币。
            _c0 = body[0] if body else 0
            _n4 = struct.unpack_from('>H', body, 1)[0] if len(body) >= 3 else 0
            _off = 3
            _ids = []
            _gain = 0
            for _ in range(_n4):
                if _off + 10 > len(body):
                    break
                _iid = struct.unpack_from('>I', body, _off)[0]
                _ib = struct.unpack_from('>I', body, _off + 4)[0]
                _ic = struct.unpack_from('>H', body, _off + 8)[0]
                _off += 10
                _ids.append(_iid)
                _gain += item_value(_ib) * max(1, int(_ic))
            _rid_4 = role_state(self.cfg).get('rid', 1001)
            _gone = db_bag_delete(_rid_4, _ids, BAG_MAIN) if _ids else []
            # ★★ R120b：**判据只看"实际删掉了几个"** —— 不掺 `_gain`。
            #   原写法 `if _gain and _gone:` 在**物品没有价值字段（value=0）**时
            #   会走 else 回 `code=0`，而**物品其实已经被删了** ⇒
            #   那是"状态改了却说失败"（比假成功更糟）。售价 0 也是成功。
            if _gone:
                if _gain:
                    db_add_assets(_rid_4, {'gold': int(_gain)})
                _c4, _m4 = 1, ''
                log('tcp.log', '  ** 10504 出售 %d 件（实删 %d）入账 gold=%d'
                    % (_n4, len(_gone), _gain))
            elif not _ids:
                _c4, _m4 = 0, '没有要出售的物品'
            else:
                _c4, _m4 = 0, '背包里找不到这些物品'
                log('tcp.log', '  ** 10504 出售失败：请求 %s，实删 %s' % (_ids, _gone))
            self.request.sendall(pack_frame(10504, w_u8(_c4) + w_str(_m4)))
            log('tcp.log', '  << 10504 SC_10504 code=%d msg=%r' % (_c4, _m4))
            return
        if cmd == 10930:
            # ★★★ R120：**双倍经验查询** —— 原先"未开放"
            #   SC_10930{code:u8, msg:string, double:u16, double_sum:u16}
            #   与已实现的 `10932` **同族**；本服**没有双倍经验系统** ⇒ 0 是**真话**，
            #   但回"结构正确的成功"比回"未开放"更准确（客户端面板能正常渲染）。
            _out = w_u8(1) + w_str('') + w_u16(0) + w_u16(0)
            self.request.sendall(pack_frame(10930, _out))
            log('tcp.log', '  << 10930 SC_10930 code=1 double=0 double_sum=0（本服无双倍）')
            return
        if cmd == 12821:
            # ★★★ R120：**商城购买** —— 原先"未开放"
            #   CS{lev:u8, bid:u32} → SC{code:u8, msg:string, bid:u32}
            #   数据源：`config_mall.MallGoods[bid] = {price, item_bid, pay_type, …}`
            #   ⚠ `pay_type` 语义未取证 ⇒ **统一扣 `gold`**（注释标注，不猜多种货币）。
            _lv8 = body[0] if body else 0
            _bid8 = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            _g8 = mall_good(_bid8)
            _rid_8 = role_state(self.cfg).get('rid', 1001)
            if not _g8:
                _c8, _m8 = 0, '商品不存在'
            else:
                _price8 = int(_g8.get('price') or 0)
                _item8 = int(_g8.get('item_bid') or 0)
                _have8 = db_get_assets(_rid_8)
                if int(_have8.get('gold', 0)) < _price8:
                    _c8, _m8 = 0, '金币不足'
                elif not _item8:
                    _c8, _m8 = 0, '该商品没有物品'
                else:
                    db_add_assets(_rid_8, {'gold': -_price8})
                    db_bag_add(_rid_8, _item8, 1)
                    _c8, _m8 = 1, ''
                    log('tcp.log', '  ** 12821 购买 bid=%d 扣 gold=%d 得物品 %d'
                        % (_bid8, _price8, _item8))
            self.request.sendall(pack_frame(12821, w_u8(_c8) + w_str(_m8) + w_u32(_bid8)))
            log('tcp.log', '  << 12821 SC_12821 code=%d msg=%r bid=%d' % (_c8, _m8, _bid8))
            return
        if cmd == 12971:
            # ★★★ R119：**战力对比明细**（`rank_ctrl`）
            #   CS{type:u16, rid:u32, srv_id:string, flag:u8}
            #   SC{type, rid, srv_id, role_list:table(name,sex,career,lev,guild_name,
            #        power + 9 个 power_*, my_power + 9 个 my_power_*, items)}
            #   本服只有 1 个角色 ⇒ `rid` 就是自己 ⇒ 用**真实**的 `role_state`/`role_power`。
            #   ⚠ 9 个**分项战力**（装备/等级/技能/修炼/伙伴/坐骑/灵兽/神器/翅膀）需要复刻
            #     原版的分项计算，**未取证 ⇒ 一律 0**（不猜）；只填**总战力**。
            _ty = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            _rid = struct.unpack_from('>I', body, 2)[0] if len(body) >= 6 else 0
            _sl = struct.unpack_from('>H', body, 6)[0] if len(body) >= 8 else 0
            _sv = body[8:8 + _sl].decode('utf-8', 'replace') if len(body) >= 8 + _sl else ''
            _rs = role_state(self.cfg)
            _pw = 0
            try:
                _pw = int(role_power(self.cfg) or 0)
            except Exception:
                _pw = 0
            _out = w_u16(_ty & 0xffff) + w_u32(_rid & 0xffffffff) + w_str(_sv)
            _out += w_u16(1)                     # role_list 1 条（就是自己）
            _out += (w_str(str(_rs.get('name') or '')) +
                     w_u8(int(_rs.get('sex') or 0) & 0xff) +
                     w_u16(int(_rs.get('career') or 0) & 0xffff) +
                     w_u8(int(_rs.get('lev') or 1) & 0xff) +
                     w_str(''))                  # guild_name（本服无宗门 ⇒ 空）
            _out += w_u32(_pw)                   # power（总战力，真实）
            for _ in range(9):                   # 9 个分项（未取证 ⇒ 0）
                _out += w_u32(0)
            _out += w_u32(_pw)                   # my_power（就是我）
            for _ in range(9):
                _out += w_u32(0)
            _out += w_u16(0)                     # items（空表）
            self.request.sendall(pack_frame(12971, _out))
            log('tcp.log', '  << 12971 SC_12971 type=%d rid=%d 战力=%d（分项未取证=0）'
                % (_ty, _rid, _pw))
            return
        if cmd == 10206:
            # ★★ R118：**寻路/传送应答** —— 真机发了 9 次，此前无专用实现
            #   `CS_10206{x:uint32}` → `SC_10206{code:u8, msg:string}`
            #   与 `10204`（`SCMove_10204`）同属"角色位置"族；`x` 的确切语义**未取证**
            #   ⇒ **只回成功、不改状态**（不猜就不动），`msg` 留空避免误弹提示。
            _out = w_u8(1) + w_str('')
            self.request.sendall(pack_frame(10206, _out))
            log('tcp.log', '  << 10206 SC_10206 code=1（寻路应答，不改状态）')
            return
        if cmd == 10805:
            # ★★ R118：**邮件操作应答** —— 邮件族（`10800` 邮件列表已实现）
            #   `CS_10805{id:uint32}` → `SC_10805{id:uint32, code:u8}`
            #   `id` **原样回**（客户端按它配对是哪封邮件），`code=1` 表示操作被接受。
            _id8 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _out = w_u32(_id8) + w_u8(1)
            self.request.sendall(pack_frame(10805, _out))
            log('tcp.log', '  << 10805 SC_10805 id=%d code=1（邮件操作）' % _id8)
            return
        if cmd == 17200:
            # ★★★ R117：**投资当前天数/状态** —— 真机 **60 次**（当前缺口第一名）
            #   SC_17200{day:u32, status:u8}
            #   数据源：新建的 `role_invest`（`itype/day/geted`）；没有行 ⇒ 0（真话）
            #   `status` 语义按 `invest_ctrl.on17200` 的消费点取"**是否已领完**"：
            #     全部里程碑都已领 ⇒ 2；还有可领 ⇒ 1；没有投资 ⇒ 0
            #   （`1/2` 的取值来自 `setGetedState`/`setGiftData` 的消费路径，见报告）
            _iv = db_invest_state(role_state(self.cfg).get('rid', 1001))
            _ms = invest_milestones(_iv['itype']) if _iv['itype'] else []
            if not _iv['itype'] or not _iv['day']:
                _st17 = 0
            else:
                _done = sum(1 for m in _ms if m <= _iv['day'])
                _geted = sum(1 for i, m in enumerate(_ms)
                             if m <= _iv['day'] and (_iv['geted'] >> i) & 1)
                _st17 = 2 if (_done and _geted >= _done) else 1
            _out = w_u32(_iv['day'] & 0xffffffff) + w_u8(_st17)
            self.request.sendall(pack_frame(17200, _out))
            log('tcp.log', '  << 17200 SC_17200 day=%d status=%d（itype=%d 里程碑=%d）'
                % (_iv['day'], _st17, _iv['itype'], len(_ms)))
            return
        if cmd == 16503:
            # ★★★ R117：**投资领取信息**
            #   CS{type:u8} → SC{type:u8, get_info:table(day_or_lev:u8),
            #                     can_get_info:table(can_day_or_lev:u8)}
            #   · `get_info`     = **已达成**的里程碑（`day/lev <= 当前进度`）
            #   · `can_get_info` = 其中**还没领**的（`geted` 位图未置位）
            #   里程碑来自 `DayInvest`（类型 7/8）或 `LevDays`（类型 3）——**配置有出处**
            _t17 = body[0] if body else 0
            _iv2 = db_invest_state(role_state(self.cfg).get('rid', 1001), _t17)
            _ms2 = invest_milestones(_t17)
            _got = []
            _can = []
            for _i, _m in enumerate(_ms2):
                if _m <= _iv2['day']:
                    _got.append(_m)
                    if not ((_iv2['geted'] >> _i) & 1):
                        _can.append(_m)
            _out = w_u8(_t17 & 0xff)
            _out += w_u16(len(_got))
            for _m in _got:
                _out += w_u8(_m & 0xff)
            _out += w_u16(len(_can))
            for _m in _can:
                _out += w_u8(_m & 0xff)
            self.request.sendall(pack_frame(16503, _out))
            log('tcp.log', '  << 16503 SC_16503 type=%d get_info=%d can_get_info=%d'
                % (_t17, len(_got), len(_can)))
            return
        if cmd == 19400:
            # ★★★ R111：**命格背包** —— 原先落通用默认响应
            #   CS{bagcode:u8} → SC{bag_code, mingge_stage, mingge_list:table(…)}
            #   · `bag_code` 原样回（客户端按它分囊）
            #   · `mingge_stage` ← **`MinggeOther.stage_init`**（配置写死 1，**有出处**；
            #     默认响应会回 0 —— 这一条就是"做比不做强"的地方）
            #   · `mingge_list` ← **空**：本服该角色没有任何命格 ⇒ **空是真话**
            _bc = body[0] if body else 0
            # ★★★ R126：**mingge_list 读真实 DB**（原先恒空 = "本服没有命格"）
            # ★ R143：改用共用的 `encode_mingge_list`（19400/19401/19414 三处同一结构）
            _mg = db_mingge_list(role_state(self.cfg).get('rid', 1001))
            _out = (w_u8(_bc & 0xff) +
                    w_u8(mingge_stage_init()) +
                    encode_mingge_list(_mg))
            self.request.sendall(pack_frame(19400, _out))
            # ★★★ R215：**修日志的硬编码** —— 这里原本**写死** `mingge_list=0`，
            #   而实际 `encode_mingge_list(_mg)` 会按 DB 条数编码 ⇒
            #   ★ 实测回包 `mingge_list=2`（与 `role_mingge` 的 2 行一致）
            #   ⇒ **日志误导**（R203 的"空表分类"因此把 `19400` 误判为"空"）❌
            log('tcp.log', '  << 19400 SC_19400 bag=%d stage=%d mingge_list=%d (%d bytes)'
                % (_bc, mingge_stage_init(), len(_mg or []), len(_out) + 6))
            return
        if cmd == 21406:
            # ★★★ R113：**符文升级** —— 原先无专用实现
            #   CS{bag_code:u8, id:u32} → SC{code:u8, msg:string}
            #   `id` 是**背包实例 id**（`bag_items.item_id`）⇒ 先查出符文 bid，
            #   再取 `RuneBase[bid][lev+1].assets`（本服是 `rune_exp`）作为消耗，
            #   扣 `rune_exp` 并把等级 +1（`role_runes`）。
            _bc6 = body[0] if len(body) >= 1 else 1
            _id6 = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            _rid6 = role_state(self.cfg).get('rid', 1001)
            _bid6 = 0
            try:
                _c6 = db_conn()
                _r6 = _c6.execute('SELECT bid FROM bag_items WHERE rid=? AND item_id=?',
                                  (_rid6, _id6)).fetchone()
                db_release(_c6)
                _bid6 = int(_r6[0]) if _r6 else 0
            except Exception:
                _bid6 = 0
            if not _bid6:
                _c, _m = 0, '背包里找不到该符文'
            else:
                _cur6 = db_rune_lev(_rid6, _bid6)
                _cost6 = rune_up_cost(_bid6, _cur6)
                if _cost6 is None:
                    _c, _m = 0, '已满级或该符文无升级配置'
                elif not _cost6:
                    _c, _m = 0, '该符文未配置升级消耗'
                else:
                    _have6 = db_get_assets(_rid6)
                    _lack6 = [k for k, v in _cost6.items()
                              if int(_have6.get(k, 0)) < int(v)]
                    if _lack6:
                        _c, _m = 0, '材料不足(%s)' % ','.join(_lack6)
                    else:
                        db_add_assets(_rid6, {k: -int(v) for k, v in _cost6.items()})
                        db_rune_set_lev(_rid6, _bid6, _cur6 + 1)
                        _c, _m = 1, ''
                        log('tcp.log', '  ** 21406 符文 %d 升级 %d -> %d 扣 %s'
                            % (_bid6, _cur6, _cur6 + 1, _cost6))
            self.request.sendall(pack_frame(21406, w_u8(_c) + w_str(_m)))
            log('tcp.log', '  << 21406 SC_21406 code=%d msg=%r id=%d bid=%d'
                % (_c, _m, _id6, _bid6))
            return
        if cmd == 15501:
            # ★★★ R115：**坐骑** —— 原先落通用默认响应
            #   `attr_list` 来自 `RideLevAttr[等级].attr`（**每级 12 个真实属性**），
            #   没有坐骑 ⇒ 12 个 0（**真话**）。
            _rid_r = role_state(self.cfg).get('rid', 1001)
            _rs = db_ride_state(_rid_r)
            _vals = ride_attr_values(_rs['lev'])
            _out = (w_u8(_rs['jie'] & 0xff) +
                    w_u16(_rs['jie_luck'] & 0xffff) +
                    w_u16(_rs['grow'] & 0xffff) +
                    w_u16(_rs['zz'] & 0xffff) +
                    w_u8(_rs['face'] & 0xff) +
                    w_u8(_rs['use'] & 0xff))
            # ★★ R116b：**表一律发空** —— 见本文件顶部 R116b 注释与
            #   `round115_ride.md`：我们的非空包经逐字节核对是**正确的 252 字节**，
            #   但门禁 `parse_full` 报 `attr_list[]: red_def_p: 越界 (off=253 len=252)`
            #   （分歧点未定位），而 `audit_dedicated` 明确"**少发不豁免**"。
            #   ⇒ **不把红灯留下**：标量保留**真实 DB 值**，6 个表全空。
            #   ⚠ 待办：定位 `parse_full` 与 `fields.json` 在该命令上的偏移分歧后，
            #     把 `skill_list`/`attr_list`/`can_item_list` 的真实数据放回来。
            # ★★★ R128：**修正 `attr_list` 的计数** —— 它的**一个元素 = 12 个属性**，
            #   所以 `cnt` 是"属性行数"（=1），不是"12 个属性值"。
            #   （R115b 曾误判成"门禁解析器有 bug"并回退为空表 —— **那次判断是错的**，
            #     见本文件顶部 R128 注释与 `tools/_repro_parsefull.py` 的复现证据。）
            _sk = ride_skills() if _rs['jie'] else []
            _out += w_u16(len(_sk))
            for _b in _sk:
                _out += w_u32(_b)
            _out += w_u16(1 if _rs['lev'] else 0)      # attr_list：1 行
            for _v in _vals:
                _out += w_u32(_v)
            _out += w_u16(0)     # can_item_list
            # ★★★ R115c：**补上漏掉的 3 个顶层表** —— 门禁当场抓到：
            #   `audit_sc_live` 报 `15501 attr_list[]: red_def_s: 越界 (off=249 len=246)`
            #   ⇒ 我们**漏发字段**。查 `protocol/fields.json` 的 `SC_15501`，
            #   它其实有 **12 个顶层字段**（我只发了前 9 个）：
            #     … can_item_list, **items, surface_list, surface_star**
            #   ⇒ 本服没有这三样的数据源 ⇒ 回**结构正确的空表**（并按门禁 E 登记理由）。
            _out += w_u16(0)     # items
            _out += w_u16(0)     # surface_list
            _out += w_u16(0)     # surface_star
            self.request.sendall(pack_frame(15501, _out))
            log('tcp.log', '  << 15501 SC_15501 jie=%d lev=%d（标量真实；6 表空，待定位门禁分歧）'
                % (_rs['jie'], _rs['lev']))
            return
        if cmd == 21401:
            # ★ R114：**装备格子容量**（`SC_21401{eqm_grid:u8}`）
            #   取 `bag_volume` 里 `bag_code=2`（ROLE_EQUIP）的容量；取不到 ⇒ 0（诚实）
            _g = equip_grid_size(role_state(self.cfg).get('rid', 1001))
            self.request.sendall(pack_frame(21401, w_u8(_g & 0xff)))
            log('tcp.log', '  << 21401 SC_21401 eqm_grid=%d' % _g)
            return
        if cmd == 21402:
            # ★★★ R114：**穿上装备**（背包 → 装备）
            #   CS{bag_item_id:u32, eqm_item_id:u32, eqm_pos:u8, hero_id:u32}
            #   ⇒ SC{code:u8, msg:string}
            #   与既有 admin 路由 `setequip` **同一条 DB 路径**（db_bag_get_one +
            #   db_equip_put + db_bag_delete），不引入新语义。
            _ban = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _pos = body[8] if len(body) >= 9 else 0
            _hb = struct.unpack_from('>I', body, 9)[0] if len(body) >= 13 else 0
            _rid_e = role_state(self.cfg).get('rid', 1001)
            _row = db_bag_get_one(_rid_e, _ban, BAG_MAIN) if _ban else None
            if not _row:
                _ce, _me = 0, '背包里找不到该物品'
            else:
                _bid_e = int(_row.get('bid') or 0)
                if db_equip_put(_rid_e, _pos, _ban, _bid_e, _hb):
                    db_bag_delete(_rid_e, [_ban], BAG_MAIN)
                    _ce, _me = 1, ''
                    log('tcp.log', '  ** 21402 穿上 item_id=%d bid=%d slot=%d hero=%d'
                        % (_ban, _bid_e, _pos, _hb))
                else:
                    _ce, _me = 0, '装备写入失败'
            self.request.sendall(pack_frame(21402, w_u8(_ce) + w_str(_me)))
            log('tcp.log', '  << 21402 SC_21402 code=%d msg=%r bag_item_id=%d'
                % (_ce, _me, _ban))
            return
        if cmd == 21403:
            # ★★★ R114：**卸下装备**（装备 → 背包）
            #   CS{eqm_item_id:u32, bag_item_id:u32, bag_pos:u8, hero_bid:u32}
            _eq = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid_e2 = role_state(self.cfg).get('rid', 1001)
            _er = db_equip_get_one(_rid_e2, _eq) if _eq else None
            if not _er:
                _c3, _m3 = 0, '找不到该装备'
            else:
                db_bag_add(_rid_e2, int(_er['bid'] or 0), 1)   # 先回背包
                db_equip_delete(_rid_e2, _eq)                  # 再卸下
                _c3, _m3 = 1, ''
                log('tcp.log', '  ** 21403 卸下 item_id=%d bid=%d slot=%s'
                    % (_eq, int(_er['bid'] or 0), _er.get('slot')))
            self.request.sendall(pack_frame(21403, w_u8(_c3) + w_str(_m3)))
            log('tcp.log', '  << 21403 SC_21403 code=%d msg=%r eqm_item_id=%d'
                % (_c3, _m3, _eq))
            return
        if cmd == 21405:
            # ★★★ R112：**魂星兑换**（真扣材料）—— 原先落通用默认响应（假成功）
            #   数据源：`RuneExchange[].assets`（本服 `rune_chip` × 4500，R109 解出）
            #   扣除走 `db_add_assets`（负数）；余额走 `db_get_assets`。
            _rb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _nm = struct.unpack_from('>H', body, 4)[0] if len(body) >= 6 else 1
            _nm = _nm or 1
            _cost = rune_exchange_cost(_rb)
            if _cost is None:
                _c5, _m5 = 0, '无效星魂'
            elif not _cost:
                _c5, _m5 = 0, '该星魂未配置消耗'
            else:
                _have = db_get_assets(role_state(self.cfg).get('rid', 1001))
                _need = {k: int(v) * _nm for k, v in _cost.items()}
                _lack = [k for k, v in _need.items()
                         if int(_have.get(k, 0)) < v]
                if _lack:
                    _c5 = 0
                    _m5 = '材料不足(%s)' % ','.join(_lack)
                else:
                    db_add_assets(role_state(self.cfg).get('rid', 1001),
                                  {k: -v for k, v in _need.items()})
                    # ★★★ R113：**把符文真的加进背包** —— R112 只扣钱没给东西，
                    #   那是"假成功"（钱花了、物品没到）。`rune_id` 是真实物品 bid
                    #   （`item_config` 里 21403 牧夫 / 21413 贪狼 / 21423 仙女，type=43）。
                    _real_id = _rb
                    try:
                        _ex = (rune_cfg().get('RuneExchange') or {})
                        for _k, _v in _ex.items():
                            _h = (_v or {}).get('hash') if isinstance(_v, dict) else None
                            if _h and (int(_h.get('rune_id') or 0) == int(_rb)
                                       or int(_h.get('id') or 0) == int(_rb)):
                                _real_id = int(_h.get('rune_id') or _rb)
                                break
                    except Exception:
                        pass
                    for _i in range(int(_nm)):
                        db_bag_add(role_state(self.cfg).get('rid', 1001), _real_id, 1)
                    _c5, _m5 = 1, ''
                    log('tcp.log', '  ** 21405 兑换星魂 %d ×%d 扣 %s 并入库 %d'
                        % (_rb, _nm, _need, _real_id))
            self.request.sendall(pack_frame(21405, w_u8(_c5) + w_str(_m5)))
            log('tcp.log', '  << 21405 SC_21405 code=%d msg=%r rune_bid=%d'
                % (_c5, _m5, _rb))
            return
        if cmd == 21411:
            # ★★★ R109：**魂星兑换列表** —— 此前在"未开放"集合里（回 code=0 未开放）
            #   CS{count_type:u8, color:u8} → SC{code:u8, msg:string, coin_count:u8,
            #                                    rest_times:u8, Items:table(bid,num,exchange)}
            #   数据源：`config_rune_data` 解构出的 **`RuneExchange`（20 项）** —— 这是 R108
            #   补上 `KSTR`/`KSHORT` 等常数加载指令、把它"正名"成功之后才拿到的。
            #   `Items`：`bid ← rune_id`、`num = 1`（配置无数量字段，保守取 1）、
            #            `exchange ← count`（配置原值，本服 0 = 未兑换，真话）。
            #   `coin_count`/`rest_times` 语义未取证 ⇒ 0。
            _rows = rune_exchange_rows()
            _out = (w_u8(1) + w_str('') +          # code=1 成功 / msg 空
                    w_u8(0) + w_u8(0))             # coin_count / rest_times（未取证）
            _out += w_u16(len(_rows))
            for _rid, _cnt in _rows:
                _out += w_u32(_rid & 0xffffffff) + w_u32(1) + w_u8(_cnt & 0xff)
            self.request.sendall(pack_frame(21411, _out))
            log('tcp.log', '  << 21411 SC_21411 Items=%d（RuneExchange）(%d bytes)'
                % (len(_rows), len(_out) + 6))
            return
        if cmd == 21400:
            # ★★★ R104：**魂星 · 装备列表**（`soulstar_ctrl`）—— 原先落通用默认响应
            #   数据源：DB `equip_items`（rid=1001 **有 6 件真实装备**），字段逐个对齐：
            #     id←item_id / bid / hero_bid / pos←slot / ctime
            #   其余字段（bind/intensify_lev/quantity/expire_ts/durable/object 与 5 个子表）
            #   本服无数据源 ⇒ 0 / 空表（**不编造**）。
            #   两张表按 `hero_bid` 划分（0=角色装备，非 0=伙伴装备）——**有依据的划分**。
            _role_e, _part_e = db_equip_rows(role_state(self.cfg).get('rid', 1001))

            # ★ R146：改用全局 `encode_eqm_list`（与 `21414` 共用）
            def _eqm_items(lst):
                return encode_eqm_list(lst)

            def _old_eqm_items(lst):
                b = w_u16(len(lst))
                for _e in lst:
                    b += (w_u32(_e['id']) +          # id
                          w_u32(_e['bid']) +         # bid
                          w_u32(_e['hero_bid']) +    # hero_bid
                          w_u8(0) +                  # bind（无源）
                          w_u8(30) +                  # intensify_lev（无源）
                          w_u16(_e['pos'] & 0xffff) +  # pos ← slot
                          w_u16(0) +                 # quantity（无源）
                          w_u32(_e['ctime'] & 0xffffffff) +  # ctime
                          w_u32(0) +                 # expire_ts（无源）
                          w_u16(0) +                 # durable（无源）
                          w_u8(0) +                  # object（无源）
                          w_u16(0) +                 # attrs_ext 空表
                          w_u16(0) +                 # attrs_ext_list 空表
                          w_u16(0) +                 # attrs_ext_one_list 空表
                          w_u16(0) +                 # jewel_list 空表
                          w_u16(0))                  # str_ext_list 空表
                return b

            _out = (_eqm_items(_role_e) + _eqm_items(_part_e) +
                    w_u8(0) +                # eqm_grid（容量，无源）
                    w_u32(0) +               # dung_bid
                    w_u8(0))                 # floor
            self.request.sendall(pack_frame(21400, _out))
            log('tcp.log',
                '  << 21400 SC_21400 role_eqm=%d partner_eqm=%d (%d bytes)'
                % (len(_role_e), len(_part_e), len(_out) + 6))
            return
        if cmd == 16500:
            # ★★★ R107：**投资系统档位** —— 原先落通用默认响应（空 info 表）
            #   SC_16500{info:table(type:u8, is_active:u8, get_num:u8, can_buy:u8,
            #                       time:u32, charge_rmb:u32)}
            #   数据源：`config_invest` 解构结果（4 个档位：登录基金/等级基金/豪华投资/至尊投资）
            #   + `LevDays` 的等级门槛（⇒ `can_buy` 是**真实计算**，不是编造）。
            _ic = invest_cfg()
            _itypes = list((_ic.get('InvestType') or {}).keys())
            try:
                _itypes = sorted(int(x) for x in _itypes)
            except Exception:
                _itypes = []
            _lev107 = int(role_state(self.cfg).get('lev') or 1)
            _out = w_u16(len(_itypes))
            for _t in _itypes:
                _gate = invest_level_gate(_ic, _t)
                _can = 1 if (_gate == 0 or _lev107 >= _gate) else 0
                _out += (w_u8(_t & 0xff) +          # type ← InvestType 的键
                         w_u8(0) +                  # is_active：本服尚无购买记录（=没买过，真话）
                         w_u8(0) +                  # get_num：已领次数（同上）
                         w_u8(_can) +               # can_buy：★ 等级门槛判定
                         w_u32(0) +                 # time：语义未取证 ⇒ 0
                         w_u32(0))                  # charge_rmb：配置只有 is_charge(0/1) 不是金额 ⇒ 0
            self.request.sendall(pack_frame(16500, _out))
            log('tcp.log', '  << 16500 SC_16500 info=%d 档（等级 %d）(%d bytes)'
                % (len(_itypes), _lev107, len(_out) + 6))
            return
        if cmd == 18803:
            # ★★★ R100：**巅峰战**查询 —— 原先落通用默认响应（空壳）
            #   规格 SC_18803{rest_time:u8, win_times:u16, total_times:u16, score:u32,
            #     win_reward_flag:u8, time_reward_flag:u8, rank:u32, end_time:u32,
            #     match_flag:u8, daily_times:u16,
            #     up_bat_list:table(index:u8, score:int32), peak_index:u16,
            #     cont_win_times:u16, max_score:u32}
            #   数据源：`peakwar_state` 表（DB 驱动，同 `race_state`/`arena_state` 模式）；
            #   没有行 ⇒ 全 0（**没打过是真话**，不是占位）。
            _st18803 = db_peakwar_state(role_state(self.cfg).get('rid', 1001))
            _out18803 = (w_u8(_st18803['rest_time'] & 0xff) +
                         w_u16(_st18803['win_times'] & 0xffff) +
                         w_u16(_st18803['total_times'] & 0xffff) +
                         w_u32(_st18803['score'] & 0xffffffff) +
                         w_u8(_st18803['win_reward_flag'] & 0xff) +
                         w_u8(_st18803['time_reward_flag'] & 0xff) +
                         w_u32(_st18803['rank'] & 0xffffffff) +
                         w_u32(_st18803['end_time'] & 0xffffffff) +
                         w_u8(_st18803['match_flag'] & 0xff) +
                         w_u16(_st18803['daily_times'] & 0xffff) +
                         w_u16(0) +                      # up_bat_list 空表
                         w_u16(_st18803['peak_index'] & 0xffff) +
                         w_u16(_st18803['cont_win_times'] & 0xffff) +
                         w_u32(_st18803['max_score'] & 0xffffffff))
            self.request.sendall(pack_frame(18803, _out18803))
            log('tcp.log',
                '  << 18803 SC_18803 win=%d/%d score=%d rank=%d max=%d (%d bytes)'
                % (_st18803['win_times'], _st18803['total_times'], _st18803['score'],
                   _st18803['rank'], _st18803['max_score'], len(_out18803) + 6))
            return
        if cmd == 14000:
            # ★★ round45.3：阵容查询（登录必发，角色面板战力真正入口）
            #   CS{flag:u8} → SC{flag:u8, select_type:u8,
            #     info_list:table{type:u8, f_lev:u8,
            #       hero_pos_info:table{hero_bid:u32,pos:u8},
            #       member_pos_info:table{member_id:u32,member_srv_id:string,career:u16,pos:u8,sex:u8}}}
            # 此前走通用兜底（空阵容）⇒ curHeroPower=0。
            _flag = body[0] if len(body) >= 1 else 0
            # ★★★ R88：**按真实阵型回**（原先 `type=9` 不是任何合法阵型、伙伴位写死 1 条）
            #   · `type` = 玩家等级可用的**最高 f_type**（阵型表 `_FORMATIONS`，
            #     来自 `config_formation.luac`：need_lev = 1/20/32/36/42/46/50）；
            #   · `hero_pos_info` = **已拥有的伙伴**依次落位（`role_heros`，R86 起持久化）；
            #   · 容量 **5** —— 配置里每组阵法的位置表都是 5 项。
            _lev_f = int(role_state(self.cfg).get('lev') or 1)
            _best = 1
            for _ft, _nl in _FORMATIONS:
                if _nl <= _lev_f and _ft > _best:
                    _best = _ft
            # ★ R91：同上 —— 玩家选过就回他选的（否则永远回最高档，切换没效果）
            _sel0 = db_form_get(role_state(self.cfg).get('rid', 1001))
            if _sel0 and 1 <= int(_sel0.get('f_type') or 0) <= 7:
                _best = int(_sel0['f_type'])
            _heroes = db_hero_list(role_state(self.cfg).get('rid', 1001), self.cfg)[:5]
            # ★ R98：对照实验开关 form_pos_limit（读全局 CFG ⇒ 下一次请求即生效）
            try:
                _fl = int(CFG.get('form_pos_limit') or 0)
                if _fl > 0:
                    _heroes = _heroes[:_fl]
            except Exception:
                pass
            out = (w_u8(1) +                          # flag=1 成功
                   w_u8(1) +                          # select_type=1
                   w_u16(1) +                         # info_list count=1
                   w_u8(_best) +                      # ★ type = 真实阵型 f_type
                   w_u8(1) +                          # f_lev=1
                   w_u16(len(_heroes)))               # ★ hero_pos_info = 已拥有伙伴数
            for _i, _h in enumerate(_heroes, 1):
                out += w_u32(int(_h.get('bid') or 0)) + w_u8(_i)   # 位置 1..N
            out += w_u16(0)                            # member_pos_info count=0
            self.request.sendall(pack_frame(14000, out))
            log('tcp.log', '  << 14000 flag=%d 阵型=%d 上阵伙伴=%d (%d bytes)'
                % (_flag, _best, len(_heroes), len(out)))
            return
        if cmd == 13254:
            # ★★ round45.1：阵容数据返回（角色面板综合战力）
            #   客户端 CS_13254(空) → SC{f_info:table}
            #   handle_13254 收到后调 updateData('power',...) → setCurHeroPower
            #   此前无应答 ⇒ FormCtrl.curHeroPower=0 ⇒ 角色面板战力=0。
            # f_info 1 条：type=1(单人), f_lev=1, hero_pos_info 1 位, member_pos_info 空。
            out = (w_u16(1)                              # f_info count=1
                   + w_u8(1)                             # type=1
                   + w_u32(1)                            # f_lev=1
                   + w_u16(1)                            # hero_pos_info count=1
                   + w_u32(1)                            # hero_id=1
                   + w_u32(1)                            # hero_bid=1
                   + w_u8(1)                             # hero_color=1
                   + w_u8(1)                             # pos=1
                   + w_u16(0))                           # member_pos_info count=0
            self.request.sendall(pack_frame(13254, out))
            log('tcp.log', '  << 13254 f_info=1 hero_pos=1 (%d bytes)' % len(out))
            return
        if cmd == 13034:
            # 副本章节奖励（CS{dung_bid:u32} → SC{dung_bid, CengList:
            #   T{ceng:u8,count:u16,can_get:u8,is_get:u8}}）
            _db = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            # round45：非空 CengList。读法见 demontower_view proto#25：
            #   ceng=层号 count=层进度 is_get=0可领/非0已领 can_get=0可领/非0不可领
            # 填前3层占位（count=0 未打）；真实进度随镇魂塔玩法同步。
            _rows = [(1, 0, 0, 0), (2, 0, 0, 0), (3, 0, 0, 0)]
            out = w_u32(_db) + w_u16(len(_rows))
            for _c, _cnt, _cg, _ig in _rows:
                out += w_u8(_c) + w_u16(_cnt) + w_u8(_cg) + w_u8(_ig)
            self.request.sendall(pack_frame(13034, out))
            log('tcp.log', '  << 13034 dung_bid=%d CengList=%d层 (%d bytes)'
                % (_db, len(_rows), len(out)))
            return
        if cmd == 13005:
            # 副本次数查询（CS{bid:u32,flag:u8} → SC{bid:u32,flag:u8,left_times:u32}）
            rid = role_state(self.cfg).get('rid', 1001)
            _bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _flag = body[4] if len(body) >= 5 else 0
            _lt = db_dung_get(rid, 'dung_left', str(_bid), 5)
            out = w_u32(_bid) + w_u8(_flag & 0xff) + w_u32(_lt)
            self.request.sendall(pack_frame(13005, out))
            log('tcp.log', '  << 13005 bid=%d flag=%d left_times=%d (%d bytes)' % (_bid, _flag, _lt, len(out)))
            return
        if cmd == 13036:
            # ★ round44.1：镇魂塔设置（demontower_ctrl）。
            #   ★ PHASE 2.23（用户报障「点击后空白」+ 指示"参考 min-loop"）：**改为回包**。
            #   实测对比（同一真机 CS `00009c41010100008959`）：
            #     · mock    ⇒ **不回包**   ⇒ 客户端 `SC_13036` 有定义却等不到应答 ⇒ **UI 空白**
            #     · minloop ⇒ 回 `00 00`（= `{key=0, value=0}`，**不是回显请求**）
            #   并复核历史：真机 `13036` **总共只发过 3 次**（R44.1 提到的"1424 次重发"
            #   是用**回显式**应答时的现象）⇒ 按 minloop 的 `{0,0}` 回包即可。
            _dbid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _k = body[4] if len(body) >= 5 else 0
            _v = body[5] if len(body) >= 6 else 0
            _rid = role_state(self.cfg).get('rid', 1001)
            db_dung_set(_rid, 'dung_setting', '%d_%d' % (_dbid, _k), _v)
            pkt = pack_frame(13036, w_u8(0) + w_u8(0))   # 照 minloop：{key=0, value=0}
            self.request.sendall(pkt)
            log('tcp.log', '  << 13036 SC_13036 key=0 value=0（落库 dung_bid=%d key=%d value=%d；'
                '照 minloop 应答）' % (_dbid, _k, _v))
            return
        if cmd == 13058:
            # 波次活动副本（CS{bid:u32} → SC{cur_score:u32,get_score:u32,
            #   max_wave:u8, gain: T{type:u8,count:u32}, AwardBidList: T{Bid:u32}}）
            out = (w_u32(0) + w_u32(0) + w_u8(0) +
                   w_u16(0) +    # gain count = 空
                   w_u16(0))     # AwardBidList count = 空（不发无效 bid）
            self.request.sendall(pack_frame(13058, out))
            log('tcp.log', '  << 13058 score=0 max_wave=0 gain/award=empty (%d bytes)' % len(out))
            return
        # ------------------------------------------------------------
        # ★★ R46：塔面板三条**真机在发**却缺失/空转的命令
        #   13042（真机 183 次，tower_ctrl）：此前回**全零** ⇒ 面板无进度
        #   13035（真机 7 次，tower/demontower_ctrl）：此前**完全无应答** ⇒ 真 GAP
        #   13038（真机 7 次，tower/demontower_ctrl）：此前**完全无应答** ⇒ 真 GAP
        #   ★ 纪律：进度一律取自 `dungeon_progress`（与 21301 **同一进度源**，
        #     避免"两处口径不一致"，见 R43 教训）；**未取证的字段留空/零，不编**。
        # ------------------------------------------------------------
        if cmd == 13042:
            # SC_13042{high_floor:I, ceng_list:T{ceng:C}, status:C, cur_ceng:C,
            #          left_time:I, clear_list:T{clear_ceng:C}, count:C}
            #   · high_floor / cur_ceng 与 21301 同源（`tower_floor`/`21301`）
            #   · clear_list 来自 `tower_clear`（每层一行）
            #   · ceng_list（**可选层列表**）需塔配置支撑，其字段顺序未取证
            #     ⇒ 按纪律**留空**，不编层号
            _rid = role_state(self.cfg).get('rid', 1001)
            _hi = db_dung_get(_rid, 'tower_floor', '21301', 1)
            _clears = db_dung_list(_rid, 'tower_clear')
            out = (w_u32(_hi) +          # high_floor
                   w_u16(0) +            # ceng_list 空（可选层未取证）
                   w_u8(0) +             # status
                   w_u8(_hi & 0xff) +    # cur_ceng（与 21301 的 floor 一致）
                   w_u32(0) +            # left_time
                   w_u16(len(_clears)))  # clear_list
            for _c in _clears:
                out += w_u8(_c & 0xff)
            out += w_u8(len(_clears))    # count
            self.request.sendall(pack_frame(13042, out))
            log('tcp.log', '  << 13042 high_floor=%d clear=%s (%d bytes)'
                % (_hi, _clears, len(out)))
            return
        if cmd == 13035:
            # SC_13035{team_list:T{ceng:C, index:C, round:C, time:C,
            #   member_list:T{rid:u32, srv_id:s, name:s, lev:u16, career:u16,
            #                 sex:u8, guild_name:s}}}
            #   CS{dung_bid:u32, ceng:u8}
            #   单机形态：**一层一条、成员只有自己**（成员数据全是真实角色字段，
            #   不是占位；数值 `index/round/time` 无原版依据 ⇒ 留 0）。
            _cg = body[4] if len(body) >= 5 else 0
            _st = role_state(self.cfg)
            out = w_u16(1)                               # team_list: 1 条
            out += (w_u8(_cg & 0xff) + w_u8(0) + w_u8(0) + w_u8(0))
            out += w_u16(1)                              # member_list: 1 人
            out += (w_u32(_st.get('rid', 1001)) +
                    w_str(_st.get('srv_id', '1')) +
                    w_str(_st.get('name', '')) +
                    w_u16(_st.get('lev', 1)) +
                    w_u16(_st.get('career', 1)) +
                    w_u8(_st.get('sex', 0)) +
                    w_str(_st.get('gname', '')))
            self.request.sendall(pack_frame(13035, out))
            log('tcp.log', '  << 13035 SC_13035 ceng=%d members=1 (%d bytes)'
                % (_cg, len(out)))
            return
        if cmd == 13038:
            # SC_13038{record_str:string}   CS{Bid:u32, ceng:u8}
            #   此前**完全无应答**（真机 7 次全是 GAP；客户端确有处理器）。
            #   严格不猜：**没打过就是空串** —— 不编造通关记录文本。
            _b = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _cg = body[4] if len(body) >= 5 else 0
            out = w_str('')
            self.request.sendall(pack_frame(13038, out))
            log('tcp.log', '  << 13038 SC_13038 Bid=%d ceng=%d record_str=空 (%d bytes)'
                % (_b, _cg, len(out)))
            return
        # ================================================================
        # ★★ C3.3-E：镇魂塔（dung 40001）业务闭环
        #   13037 挑战层 / 21308 进本 / 21309 退本。
        #   设计：
        #     · 进入条件服务端验证：等级（config_dungeon_new level_low）、层数进度
        #       （dungeon_progress tower_floor，与 21301/13042 同源）。
        #     · 挑战会话挂在连接上：self.dung_challenge={bid,ceng,boss}；
        #       塔 boss（18200+ceng）被 20002 击杀后，_battle_settle 据此做
        #       塔结算（grant 幂等 + 推 SC_21307 + 推进 tower_floor/tower_clear）。
        #     · 不创建虚构副本/关卡/奖励；奖励全部读 config_dungeon_tower 真实字段。
        # ================================================================
        if cmd == 13037:
            # SC_13037{Bid:u32, ceng:u8, tips:u8, msg:string}  CS{Bid:u32, ceng:u8}
            _sb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _scg = body[4] if len(body) >= 5 else 0
            _sst = role_state(self.cfg)
            _srid = _sst.get('rid', 1001)
            _slev = int(_sst.get('lev') or 1)
            # —— 服务端校验 ——
            if _sb != _DUNG_TOWER_BID:
                # 非镇魂塔（本批最小闭环只接 40001；其余塔 dung 不编）
                _tips, _msg = 0, '该副本未开放挑战'
            elif _scg < 1 or _scg > _DUNG_TOWER_MAX_FLOOR:
                _tips, _msg = 0, '层数非法'
            elif tower_floor_hash(_scg) is None:
                _tips, _msg = 0, '该层无配置'
            else:
                # 等级门禁：读 config_dungeon_new dung 40001 的 level_low（=45）
                # ★ 同上：_h 在本方法内是局部变量，内联 hash 提取。
                _lvlow = 0
                try:
                    for _k, _v in (dungeon_cfg().get('Dungeon') or {}).items():
                        _hh = _v.get('hash') if isinstance(_v, dict) else {}
                        if int(_hh.get('dung_id') or 0) == _DUNG_TOWER_BID:
                            _lvlow = int(_hh.get('level_low') or 0)
                            break
                except Exception:
                    _lvlow = 0
                if _lvlow and _slev < _lvlow:
                    _tips, _msg = 0, '等级不足(%d)' % _lvlow
                else:
                    # 层数进度：不能挑战超过当前前沿的层（tower_floor 默认 1）
                    _cur = db_dung_get(_srid, 'tower_floor', '21301', 1)
                    if _scg > _cur:
                        _tips, _msg = 0, '请先通关前一层'
                    else:
                        _tf = tower_floor_reward(_scg) or {}
                        self.dung_challenge = {'bid': _sb, 'ceng': _scg,
                                               'boss': int(_tf.get('boss') or 0)}
                        _tips, _msg = 1, ''
                        log('tcp.log', '  ** 13037 镇魂塔挑战 rid=%d ceng=%d boss=%d '
                            '(lev=%d frontier=%d)'
                            % (_srid, _scg, self.dung_challenge['boss'], _slev, _cur))
            _out = w_u32(_sb) + w_u8(_scg) + w_u8(_tips) + w_str(_msg)
            self.request.sendall(pack_frame(13037, _out))
            log('tcp.log', '  << 13037 SC_13037 Bid=%d ceng=%d tips=%d msg=%r (%d bytes)'
                % (_sb, _scg, _tips, _msg, len(_out)))
            return
        if cmd == 21308:
            # SC_21308{tips:u8, msg:string, time:u16}  CS{bid:u32}
            _eb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _est = role_state(self.cfg)
            _erid = _est.get('rid', 1001)
            _elev = int(_est.get('lev') or 1)
            _known = any(b == _eb for b, _ in dungeon_rows())
            if not _known:
                _etips, _emsg = 0, '副本不存在'
            elif _eb == _DUNG_TOWER_BID:
                # 镇魂塔等级门禁（level_low=45）
                # ★ 注意：本方法(_reply)内别处有 `_h=...` 赋值，Python 视 _h 为
                #   整个方法的局部变量 ⇒ 此处不能调用模块函数 _h()（UnboundLocalError）。
                _lvlow = 0
                try:
                    for _k, _v in (dungeon_cfg().get('Dungeon') or {}).items():
                        _hh = _v.get('hash') if isinstance(_v, dict) else {}
                        if int(_hh.get('dung_id') or 0) == _DUNG_TOWER_BID:
                            _lvlow = int(_hh.get('level_low') or 0)
                            break
                except Exception:
                    _lvlow = 0
                if _lvlow and _elev < _lvlow:
                    _etips, _emsg = 0, '等级不足(%d)' % _lvlow
                else:
                    db_dung_enter(_erid, _eb)
                    self.dung_enter_bid = _eb
                    _etips, _emsg = 1, ''
                    log('tcp.log', '  ** 21308 进本 rid=%d bid=%d (镇魂塔 lev=%d)'
                        % (_erid, _eb, _elev))
            else:
                # 其余副本：仅校验存在性，进本状态落库；战斗/结算后续再逐副本接
                db_dung_enter(_erid, _eb)
                self.dung_enter_bid = _eb
                _etips, _emsg = 1, ''
                log('tcp.log', '  ** 21308 进本 rid=%d bid=%d (通用占位)'
                    % (_erid, _eb))
            _out = w_u8(_etips) + w_str(_emsg) + w_u16(0)
            self.request.sendall(pack_frame(21308, _out))
            log('tcp.log', '  << 21308 SC_21308 bid=%d tips=%d msg=%r time=0 (%d bytes)'
                % (_eb, _etips, _emsg, len(_out)))
            return
        if cmd == 21309:
            # SC_21309{tips:u8, msg:string, bid:u32}  CS{bid:u32}
            _xb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            self.dung_challenge = None
            self.dung_enter_bid = 0
            _out = w_u8(1) + w_str('') + w_u32(_xb)
            self.request.sendall(pack_frame(21309, _out))
            log('tcp.log', '  << 21309 SC_21309 bid=%d tips=1 (退出副本，清挑战会话) (%d bytes)'
                % (_xb, len(_out)))
            return
        if cmd == 13402:
            # ★★★ round42：134xx 限购商店「购买」（客户端 shop_ctrl.on13402）
            #   CS {id:u16, num:u16}
            #      真机 body 8 字节 = 4 字段 + 客户端缓冲区 4 字节残留
            #      （实测 `138a 0001 | 04000100` ⇒ id=5002, num=1）
            #   SC {id:u16, type:u8, buy_num:u16, new_price:u32, code:u8, msg:string}
            #   ★ 商品源与 13401/13403 **完全同源**（server/mall_config.json）——
            #     客户端拿的是 13401 `buy_list[].id`，回来买的就是同一批 id，自洽。
            #   ★ 扣费/发货/记限购 **全部复用 12805 的既有流程**：
            #     shop_pay_asset（与客户端 AssetsEnToCode 同源）→ 限购校验
            #     → db_set_assets → db_bag_add → db_mall_bought_add
            #     → bag_push_frames / _send_12831 / live_push。
            #   ★ `new_price` 回该商品**当前单价**：本服配置是固定价
            #     （mall_config 无动态价字段）⇒ 回原价是真话，不编"涨价"。
            gid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            bnum = struct.unpack_from('>H', body, 2)[0] if len(body) >= 4 else 1
            bnum = max(1, int(bnum))
            # ★ 走共用购买内核（与 12832 同一实现）：选币→限购→扣费→发货→记限购
            code, msg, g, total, bought_now = shop_try_buy(
                self.cfg, mall_cfg(), gid, bnum)
            mtype = (int(g.get('type', 0)) & 0xff) if g else 0
            unit = (int(g.get('price', 0) or 0)) if g else 0
            out = (w_u16(gid & 0xffff) + w_u8(mtype) +
                   w_u16(bnum & 0xffff) + w_u32(unit) +
                   w_u8(code & 0xff) + w_str(msg))
            self.request.sendall(pack_frame(13402, out))
            if code == 1:
                rid = role_state(self.cfg).get('rid', 1001)
                bag_push_frames(self, rid)
                _goods9 = [g2 for g2 in (mall_cfg() or []) if int(g2.get('type', -1)) == 9]
                _b9 = db_mall_bought(rid)
                _bl = [(int(g2.get('id', 0)), _b9.get(int(g2.get('id', 0)), 0)) for g2 in _goods9]
                _bbody = w_u16(len(_bl))
                for _g, _bn in _bl:
                    _bbody += w_u16(_g & 0xFFFF) + w_u16(_bn & 0xFFFF)
                self.request.sendall(pack_frame(18909, _bbody))
                live_push(self.cfg, 'shop_buy')
            # ★ 修复：旧 log 引用了作用域内不存在的 g_gid/item_bid/pay/buy_num
            #   （迁移到 shop_try_buy 时未改干净）⇒ 购买成功必抛 NameError。
            #   现按 code 分支、变量全部安全取自 g / 返回值。
            if code == 1:
                log('tcp.log', '  ** 13402 购买成功 goods_id=%d item=%d x%d 扣 %s=%d 已购=%d'
                    % (int(g.get('id', gid)), int(g.get('item_bid', 0)), bnum,
                       shop_pay_asset(self.cfg, g), total, bought_now))
            else:
                log('tcp.log', '  << 13402 SC_13402 code=0 goods_id=%d msg=%s' % (gid, msg))
            return
        if cmd in (10514, 10532, 10560):
            # ★★★ 2026-09-18 体检补实现：真机**实际发过**但服务端原先**无人应答**的三条
            #   （从 tcp.log 抓到；客户端注册位置已核实）
            #   10514 backpack_ctrl.handle_10514  → 背包→装备结果（CS 空）
            #         SC{code:u8, msg:string, bag_to_eqm:table(bag_item_id:u32, eqm_new_pos:u8),
            #            bag_replace_eqm:table(bag_item_id:u32, eqm_item_id:u32, eqm_new_pos:u8)}
            #   10532 equip_ctrl.hander_10532       → Fire(EquipEvents.EQUIP_GOLD_MATRIAL, val)
            #         ★ 语义 = **该装备升级所需的金币材料**
            #         CS{bag_code:u8, type:u8, item_id:u32} → SC{val:int32}
            #   10560 equip_ctrl.hander_10560       → Fire(EquipEvents.GET_GOODS_PRICE, args)
            #         ★ 语义 = **物品价格查询**（真机传的是升级材料：打造石/图纸）
            #         CS{args:table(id:u32)} → SC{args:table(id:u32, type:u8, num:u32)}
            #   ⚠ 原版"升级消耗/售价"数值**未取证**（item_config 的 value 全空）⇒
            #     取 config.item_price 映射，**默认 0**，不编造具体数字。
            if cmd == 10514:
                # 空请求 → 无待处理项，回成功 + 空表（客户端只会据此刷新，安全）
                out = (w_u8(1) + w_str('') + w_u16(0) + w_u16(0))
                pkt = pack_frame(10514, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 10514 SC_10514 code=1 bag_to_eqm=0 replace=0 (%d bytes)' % len(pkt))
                return
            if cmd == 10532:
                bc = body[0] if len(body) >= 1 else 0
                ty = body[1] if len(body) >= 2 else 0
                iid = struct.unpack_from('>I', body, 2)[0] if len(body) >= 6 else 0
                prices = self.cfg.get('item_price') or {}
                val = int(prices.get(str(iid), 0))
                pkt = pack_frame(10532, w_u32(val & 0xFFFFFFFF))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10532 SC_10532 bag_code=%d type=%d item=%d val=%d (%d bytes)'
                    % (bc, ty, iid, val, len(pkt)))
                return
            # 10560 批量价格查询
            n = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            ids = []
            off = 2
            while off + 4 <= len(body) and len(ids) < n:
                ids.append(struct.unpack_from('>I', body, off)[0])
                off += 4
            prices = self.cfg.get('item_price') or {}
            item_types = self.cfg.get('item_type') or {}
            out = w_u16(len(ids))
            for i2 in ids:
                ty2 = int(item_types.get(str(i2), 0)) & 0xFF
                num2 = int(prices.get(str(i2), 0))
                out += w_u32(i2) + w_u8(ty2) + w_u32(num2 & 0xFFFFFFFF)
            pkt = pack_frame(10560, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10560 SC_10560 args=%d %r (%d bytes)' % (len(ids), ids[:4], len(pkt)))
            return
        if cmd in (10996, 10997):
            # ★★★ R99：**版本握手**（`game/login/denglu_ctrl.luac`，三个版本客户端都有）
            #   此前服务端**完全没有这两条** ⇒ 客户端问版本/服务器状态**没人答**。
            #   10996 `onVersionStateList`：客户端遍历 `cli_ver_list` 找 `cdn_patch == PLATFORM_NAME`，
            #         找到就调 `onVersionState{cli_ver, flag}`；而 `denglu_ctrl` 里有
            #         "检测到当前游戏不是最新版本…是否立即更新？" ⇒ **cli_ver 不一致会弹更新提示**。
            #         ⇒ **回空表**：客户端找不到匹配项 ⇒ 不做版本约束（不编造未知的版本号）。
            #   10997 `checkServerState`：回 `flag=1`（同族成功约定；0 会被当成服务器不可用）。
            #   （`10998`/`10310`/`10396` 是 **SC-only 的服务端推送**，不属于应答 ⇒ 不主动发。）
            if cmd == 10996:
                _out99 = w_u16(0)
                _tag99 = 'cli_ver_list=0（不做版本约束）'
            else:
                _out99 = w_u8(1)
                _tag99 = 'flag=1（服务器正常）'
            self.request.sendall(pack_frame(cmd, _out99))
            log('tcp.log', '  << %d SC_%d %s (%d bytes)' % (cmd, cmd, _tag99, len(_out99) + 6))
            return
        if cmd in (10102, 10103):
            # SCRoleLogin_10102 / SCRoleReLogin_10103 结构相同：
            #   code:uint8  msg:string  timestamp:uint32  world_lev:uint16
            #
            # ★ code 必须 = 1（TRUE == 1，见 common_define.luac proto[7]）：
            #   denglu_ctrl.luac proto[30] on10102Login 的分支是
            #       if resp.code == TRUE then ... SendProtocal(10300)
            #                                GameNet:LoginSucceedSendProtocal()
            #                                DengluEvent:Fire(LOGIN_SUCCESS)
            #       else CommonAlert:show(resp.msg, ...)   ← 弹框，且不再往下走
            #   而 scene_controller.luac proto[1] 才把 LOGIN_SUCCESS 绑到进入场景。
            #   实测钩子日志（server/logs/http.log）持续出现
            #       hit_on10102Login code=0 / hit_on10103ReLogin code=0
            #   ⇒ 一直走 else：只弹框、不发 10300、不 Fire(LOGIN_SUCCESS)
            #   ⇒ scene 恒为 nil、反复重连。这与 1110 是同一类"code 约定"错误。
            #
            #   ⚠ 注意 10200 相反：scene_controller.luac proto[16] 是
            #     `if resp.code ~= 0 then message2(resp.msg) end`，即 0 才是成功，
            #     所以 _send_10200 里的 w_u8(0) 是**正确**的，不要一起改。
            #
            # ★★ R45 验证时发现的缺口：**此前 10102 完全忽略 CS 的 `rid`**，
            #   恒登录 `cfg['role']` 里的配置角色（1001）⇒ R44 建出来的第二个角色
            #   "能列能建、进不去"（登录后看到的还是 1001 的数据）。
            #   ⇒ 这里按 CS 的 `rid` **切换本连接的角色**：
            #     · 只接受「**存在于 roles 表** 且（已知账号时）**属于本账号**」的 rid，
            #       避免任意 rid 触发 `role_state()` 的建行种子逻辑；
            #     · 通过 `self.cfg = 副本` 建立**实例级** cfg —— `TcpHandler.cfg` 是
            #       **类属性（全连接共享）**，实例赋值只影响本连接，不会串号。
            _rid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _cur = int((self.cfg.get('role') or {}).get('rid', 0) or 0)
            # ★ 2026-10-17：条件由 `_rid != _cur` 放宽为 `_rid` ——
            #   否则"请求的角色恰好等于配置默认 rid（1001）"时会**跳过全部校验**
            #   （跨区/越权都能过）。校验必须对该 CS 一律执行；切换逻辑本身幂等。
            if _rid:
                try:
                    _uid = getattr(self, '_uid', None)
                    _row = db_get_role(_rid)
                    _ok_own = bool(_row) and (
                        not _uid or str((_row or {}).get('uid') or '') == str(_uid))
                    # ★★ 2026-10-17 三区隔离：**跨区登录必须拒绝**。
                    #   以前这里只校验"角色存在且属于本账号"，不校验区服 ⇒ 在 1 区
                    #   的角色，从 2/3 区选进来照样能进（数据是同一份）⇒ 用户看到的
                    #   现象正是"一服建的角色，二三服也能进/数据一样"。
                    #   CS 的 srv_id 实测有两种编码（都要容忍）：
                    #     · 真机 1.4.11：`body(5)=00 00 07 d2 01` ⇒ rid + **单字节** 区号
                    #     · spec/工具：   `body(7)=00 00 07 d2 00 01 31` ⇒ rid + u16 长度字符串
                    _cs_srv = ''
                    try:
                        _tail = body[4:]
                        if len(_tail) >= 2:
                            _sl = struct.unpack_from('>H', _tail, 0)[0]
                            if _sl <= 64 and 2 + _sl == len(_tail):
                                _cs_srv = _tail[2:].decode('utf-8', 'replace')
                        if not _cs_srv and len(_tail) == 1:
                            _cs_srv = str(_tail[0])
                    except Exception:
                        _cs_srv = ''
                    _role_srv = str((_row or {}).get('srv_id') or '1')
                    if _row and _cs_srv and _cs_srv != _role_srv:
                        log('tcp.log', '  !! %d 跨区登录被拒：rid=%d 属于区 %s，请求来自区 %s'
                            % (cmd, _rid, _role_srv, _cs_srv))
                        _bad = (w_u8(0) + w_str('该角色不在当前区服，请重新选择区服') +
                                w_u32(int(time.time()) & 0xFFFFFFFF) +
                                w_u16(self.cfg.get('world_lev', 1)))
                        self.request.sendall(pack_frame(cmd, _bad))
                        return
                    if _row and not _ok_own:
                        log('tcp.log', '  !! %d 拒绝：rid=%d 不属于账号 %s' % (cmd, _rid, _uid or '?'))
                        _bad = (w_u8(0) + w_str('该角色不属于当前账号') +
                                w_u32(int(time.time()) & 0xFFFFFFFF) +
                                w_u16(self.cfg.get('world_lev', 1)))
                        self.request.sendall(pack_frame(cmd, _bad))
                        return
                    if _ok_own:
                        _c2 = dict(self.cfg)
                        _c2['role'] = dict(self.cfg.get('role') or {})
                        _c2['role']['rid'] = _rid
                        self.cfg = _c2          # ★ 实例级，仅本连接生效
                        # ★★ PHASE2.4 修复：`_scene_rid()` 会**缓存** `self._aoi_rid`，
                        #   若本连接在切角色**之前**已被调用过（如进过场景），
                        #   缓存里还是旧 rid ⇒ `push_to_rid(新rid)` 推不到本连接、
                        #   反而会收到旧 rid 的推送。切角色必须**同时失效**该缓存。
                        try:
                            del self._aoi_rid
                        except Exception:
                            self._aoi_rid = int(_rid)
                        log('tcp.log', '  ** %d 切换角色 -> rid=%d（账号 %s，已清 _aoi_rid 缓存）'
                            % (cmd, _rid, _uid or '?'))
                    else:
                        log('tcp.log', '  !! %d 请求的 rid=%d 不存在或不属于本账号 %s'
                            ' ⇒ 仍用 rid=%d' % (cmd, _rid, _uid or '?', _cur))
                except Exception as e:
                    log('tcp.log', '  !! %d 切换角色失败: %r' % (cmd, e))
            body = (w_u8(1) + w_str('') +
                    w_u32(int(time.time()) & 0xFFFFFFFF) +
                    w_u16(self.cfg.get('world_lev', 1)))
            pkt = pack_frame(cmd, body)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d %s reply (%d bytes)'
                % (cmd, 'SCRoleLogin' if cmd == 10102 else 'SCRoleReLogin', len(pkt)))
            # 10200 的名字是"通知角色进入场景" —— 属于**服务端主动下发**。
            # 之前一直等客户端来请求是错的：客户端登录成功后应该由我们推它进场景。
            # ★★ 2026-10-17 修复「进图后地图不成形 / UI 不显示」的**时序根因**：
            #   这里原本**立刻**推 10200（进场景）。但此刻客户端刚收到 10102，
            #   **模块还没加载完** —— 实测客户端在 SCENE_START 的事件回调里崩：
            #     stack: daily_ctrl.luac ← sys/event Fire ← scene_model sceneStart
            #     "attempt to index a nil value"（GameData/ActivityContants 等尚未定义）
            #   ⇒ 场景只建了一半（地图不成形、UI 不出来），要等下一次重连才成。
            #   本服已经有"收到 10300（客户端初始化完毕）后再补推 10200"的正确时机，
            #   所以默认**把首推也推迟到那一步**（开关 scene_push_when_ready，默认 true）。
            #   想回到旧行为：config.json 里置 false。
            _push_now = not bool(self.cfg.get('scene_push_when_ready', True))
            if _push_now:
                self._send_10200(login_scene_bid(self.cfg))
            else:
                log('tcp.log', '  .. 10200 推迟到 10300 之后（等客户端模块加载完，'
                               'scene_push_when_ready=true）')
            # ★★★ PHASE 2.11：**登录后主动推送 SC_10305（资产增量表）**。
            #   客户端有 `rgp_hander10305` 处理器，却**从不请求** 10305
            #   （`tcp.log` 全量 0 次）⇒ 原"等请求"分支是死代码 ⇒ 必须服务端推送。
            #   含 `practice_exp`(label=9) ⇒ 修炼面板"拥有"栏的数据源候选。
            try:
                _p105 = pack_frame(10305, build_10305(self.cfg))
                self.request.sendall(_p105)
                log('tcp.log', '  << 10305 SC_10305 资产增量推送（%d bytes，含 practice_exp）'
                    % len(_p105))
            except Exception as _e105:
                log('tcp.log', '  !! 10305 登录推送失败: %r' % (_e105,))
            # ★★ 2026-10-17 修（用户报障"缺格子/空格显示"）：**进角色后主动补两条背包推送**
            #   · `SC_10510`（格子最大值/已开启格子数）—— 客户端的格子数取自它
            #     （文档 §8.3："纯 S→C 推送、需下发"；本服务端此前**一条都没推过**）
            #   · `SC_10500`（背包全量，客户端 `addItemInBagCode`）—— 进场景即让背包有数据
            #   放在 10305 之后、10200 之前：此时客户端 UI 已就绪。
            try:
                _brid = role_state(self.cfg).get('rid', 1001)
                push_10510(self, _brid, BAG_MAIN)
                bag_push_frames(self, _brid)
            except Exception as _e_bag:
                log('tcp.log', '  !! 登录背包推送失败: %r' % (_e_bag,))
            return
# [P2B-migrated dispatch/handler.py]         if cmd == 10101:
            # ★★ R44：**真建角色**（原为桩：恒回 code=0 + rid=2001，且不落库）
            #   CS_10101{sex:u8, name:string, career:int16, playform:string}
            #   SC_10101{code:u8, msg:string, rid:u32, srv_id:string}
            #   · 成功码与 1110 同族：`code == TRUE(1)`；
            #   · uid 由同一连接里最近一次 1110 决定（`self._uid`），无则落 DEFAULT_UID；
            #   · 新角色由 `db_create_role()` 用 ROLE_DEFAULTS 模板初始化（不自造数值）。
#             try:
#                 _sex = body[0] if len(body) >= 1 else 0
#                 _nl = struct.unpack_from('>H', body, 1)[0]
#                 _name = body[3:3 + _nl].decode('utf-8', 'replace')
#                 _co = 3 + _nl
#                 _career = (struct.unpack_from('>h', body, _co)[0]
#                            if len(body) >= _co + 2 else 1)
#             except Exception:
#                 _sex, _name, _career = 0, '', 1
#             _uid = getattr(self, '_uid', None) or DEFAULT_UID
#             _rid = db_create_role(_uid, _name, _sex, _career)
#             if _rid:
#                 out = w_u8(1) + w_str('') + w_u32(_rid) + w_str('1')
#                 log('tcp.log', '  ** 10101 建角成功 uid=%s rid=%d name=%s sex=%d career=%d'
#                     % (_uid, _rid, _name, _sex, _career))
#             else:
#                 out = w_u8(0) + w_str('\u5efa\u89d2\u5931\u8d25') + w_u32(0) + w_str('1')
#                 log('tcp.log', '  !! 10101 建角失败 uid=%s name=%s' % (_uid, _name))
#             self.request.sendall(pack_frame(10101, out))
#             return
# [P2D-migrated] scene/handler.py handle_10200
#         if cmd == 10200:
#             # CSRoleEnter_10200{bid:uint32}
#             #   → SCRoleEnter_10200{code:uint8, msg:string, bid:uint32,
#             #                       line_id:uint8, x:uint16, y:uint16, dir:uint8}
#             bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 1
#             sp = self.cfg.get('spawn', {})
#             out = (w_u8(0) + w_str('') + w_u32(bid) +
#                    w_u8(sp.get('line_id', 1)) +
#                    w_u16(sp.get('x', 100)) + w_u16(sp.get('y', 100)) +
#                    w_u8(sp.get('dir', 0)))
#             pkt = pack_frame(10200, out)
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 10200 SCRoleEnter bid=%d line=%d (%d,%d) (%d bytes)'
#                 % (bid, sp.get('line_id', 1), sp.get('x', 100), sp.get('y', 100),
#                    len(pkt)))
#             return
        if cmd == 10201:
            # CSMapGird_10201（空消息，客户端确实会主动请求：scene_controller.request10201）
            #   → SCMapGird_10201{roles, npcs, mons, elems}
            # 带上"自己"（位置取已持久化的坐标），否则地图里没有可渲染的单位。
            # ★ 一次一变量的对照实验开关：send_roles_in_10201
            #   实测 scene_info 里 roles=nil 而 npcs/mons/elems 都是 table，
            #   说明 roles 元素（含 6 个未解出的 D|Dsc*| 子表）**很可能编码不对**，
            #   客户端解码失败 → roles 落空。置 false 可验证该假设。
            roles = ([role_with_saved_pos(self.cfg)]
                     if self.cfg.get('send_roles_in_10201', True) else [])
            _cur_scene = int((self.cfg.get('spawn') or {}).get('bid') or 10001)
            _npcs, _mons = scene_quest_extras(self.cfg, _cur_scene)
            _elems = scene_elems(_cur_scene) if self.cfg.get('send_map_elems', True) else []
            pkt = pack_frame(10201, build_10201(roles, _npcs, _mons, _elems))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10201 SCMapGird roles=1 npcs=%d mons=%d elems=%d (100,%d) (%d bytes)'
                % (len(_npcs), len(_mons), len(_elems),
                   roles[0].get('y', 100) if roles else 0, len(pkt)))
            return
        if cmd in (10204, 10205):
            # CS_10204{x:u16, y:u16} 角色移动 / CS_10205 瞬移
            #   → SC_10204{rid:u32, srv_id:str, x:u16, y:u16}
            # 客户端 scene_controller.on10204 → model:syncRoles(resp)
            x, y = (struct.unpack_from('>HH', body, 0) if len(body) >= 4 else (100, 100))
            role = self.cfg.get('role', {})
            rid = role.get('rid', 1001)
            srv_id = role.get('srv_id', '1')
            # ★★ AOI 接线 ①：确保本连接已登记进 AOI（幂等）
            _scene_ensure(self)
            _aoi_rid = _scene_rid(self) or rid
            # ★★ AOI 接线 ②：**服务端校验**（可走性 + 可选限流）
            #   —— Survive / kongkongxiyou **都没有**这一步（前者零距离校验，
            #      后者直接信任客户端上传的整条路径）
            _reject = _scene_validate_move(self, _aoi_rid, x, y, cmd)
            if _reject is not None:
                # 拒绝时用**服务端权威坐标**回复，让客户端自我纠正（而不是静默丢弃，
                # 那会导致两端坐标永久错位）
                x, y = _reject
                log('tcp.log', '  .. [move] 已改用服务端权威坐标 (%d,%d)' % (x, y))
            save_role_pos(rid, x, y)
            # ── 任务进度（**替身机制，本阶段无战斗系统**）─────────────────────
            #  已确认：客户端在场景层**不上报击杀/采集**——`mission_util.missionGoto`
            #  只把 `fight_mon`/`collect_elem` 当作**寻路目标**；真正的击杀发生在
            #  战斗实例（11000 / 11200 系列，含 mon_list / skill），**属本阶段禁止范围**。
            #  故这里提供一个**明确标注的替代**：开关打开时，按"移动事件"推进在途任务进度，
            #  以便把「接取 → 进度 → 可提交 → 提交 → 领奖 → 链解锁」整条链路跑通并可回归。
            #  将来实现战斗后，只需把本段换成真实的击杀/采集事件调用：
            #      mission_progress_advance(rid, cond_name, target, n)
            if self.cfg.get('mission_auto_progress'):
                _advanced = []
                for mb, mm in db_get_missions(rid).items():
                    if int(mm.get('mission_status') or 0) == 3:
                        continue
                    tgt = int(mm.get('target') or 0)
                    if tgt <= 0:
                        continue
                    prog = (mission_def(mb).get('progress') or [])
                    cname = (prog[0][0]
                             if (prog and isinstance(prog[0], (list, tuple))
                                 and len(prog[0]) >= 1) else None)
                    if not cname:
                        continue
                    hit = mission_progress_advance(rid, cname, tgt, 1)
                    if hit:
                        _advanced += hit
                        log('tcp.log', '  .. [替身·无战斗] 移动推进 mission %s '
                                       'cond=%s target=%s -> %r' % (mb, cname, tgt, hit))
                # ★ 任务变为 STATUS_2（可提交）后必须**补推一次 12405**：
                #   客户端 `npc_mission_manager.luac` proto#5 `addNpc` 才会重建该 NPC 的
                #   `finish_list`；否则 NPC 对话里不会出现"完成/提交"项。
                if _advanced:
                    _ms = mission_rows(self.cfg, rid)
                    self.request.sendall(pack_frame(12405, build_12400(_ms)))
                    log('tcp.log', '  << 12405 SC_12405 update_mission_list=%d '
                                   '(可提交推送 %r)' % (len(_ms), _advanced))
            # ─────────────────────────────────────────────────────────────────
            # ★★ AOI 接线 ③：接受移动 → 更新 AOI（**双向**）
            #   并用 `watchers_seeing` 取出"看得见我的人"（= Survive `watch_me` 语义）
            _watchers = _scene_apply_move(self, _aoi_rid, x, y)
            # ★★ AOI 接线 ④：只向"看得见我的人"广播 SC_10204（单客户端 ⇒ 0 条，零回归）
            _bcast = _scene_broadcast_10204(self, _aoi_rid, srv_id, x, y, _watchers)

            out = w_u32(rid) + w_str(srv_id) + w_u16(x) + w_u16(y)
            pkt = pack_frame(cmd, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC%s rid=%d -> (%d,%d) [saved] bcast=%d watchers=%d (%d bytes)'
                % (cmd, 'Move_10204' if cmd == 10204 else 'Teleport_10205',
                   rid, x, y, _bcast, len(_watchers), len(pkt)))
            return
        if cmd in (12407, 12409):
            # CS_12407/12409（空）→ SC{ add_mission_list | missions : table(13 字段) }
            # 依据：protocol/manual.md（show_cmd 12407/12409）；字段与 SC_12400 同构 ⇒ 复用 build_mission_entry。
            rid = role_state(self.cfg).get('rid', 1001)
            ms = accept_mission_rows(self.cfg, rid)
            body = w_u16(len(ms)) + b''.join(build_mission_entry(x) for x in ms)
            pkt = pack_frame(cmd, body)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d %s=%d (%d bytes)'
                % (cmd, cmd, 'add_mission_list' if cmd == 12407 else 'missions',
                   len(ms), len(pkt)))
            return
# [P2D-migrated] task/handler.py handle_12408
#         if cmd == 12408:
#             # CS_12408（空）→ SC_12408{ delete_list: table(mission_bid:u32) }
#             # 暂无需要从“可接取”删除的项 ⇒ 回空表（不编造）。
#             body = w_u16(0)
#             pkt = pack_frame(12408, body)
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 12408 SC_12408 delete_list=0 (%d bytes)' % len(pkt))
#             return
# [P3deep-migrated] 12400/12401 已注册 task/handler.py：
#         if cmd == 12400:
#             ms = mission_rows(self.cfg, role_state(self.cfg).get('rid', 1001))
#             pkt = pack_frame(12400, build_12400(ms))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 12400 SC_12400 mission_list=%d (%d bytes)'
#                 % (len(ms), len(pkt)))
#             return
#         if cmd == 12401:
#             ms = mission_rows(self.cfg, role_state(self.cfg).get('rid', 1001))
#             pkt = pack_frame(12401, build_12400(ms))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 12401 SC_12401 missions=%d (%d bytes)'
#                 % (len(ms), len(pkt)))
#             return
# [P2B-migrated dispatch/handler.py]         if cmd == 10303:
            # CS_10303（空）→ SC_10303 角色属性（含 attr 大表）
            # 出自 role_ctrl.luac 的 RegisterProtocal(10303, 'rgp_hander10303')
#             pkt = pack_frame(10303, build_10303(role_state(self.cfg),
#                                                 self.cfg.get('skills', []),
#                                                 self.cfg.get('attr')))
#             self.request.sendall(pkt)
#             aa = db_get_attr(role_state(self.cfg).get('rid', 1001)) or {}
#             log('tcp.log', '  << 10303 SC_10303 attr (hp_max=%s atk_s=%s) (%d bytes)'
#                 % (aa.get('hp_max'), aa.get('atk_s'), len(pkt)))
#             return
# [P2B-migrated dispatch/handler.py]         if cmd == 10302:
            # CS_10302（空）→ SC_10302{lev:u16, exp:u32, gold:u32, gold_acc:u32}
            # 出自 role_ctrl.luac 的 RegisterProtocal(10302, 'rgp_hander10302')
#             r = role_state(self.cfg)
#             out = (w_u16(r.get('lev', 1)) + w_u32(r.get('exp', 0)) +
#                    w_u32(r.get('gold', 0)) + w_u32(r.get('gold_acc', 0)))
#             pkt = pack_frame(10302, build_10302(r))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 10302 SC_10302 lev=%d exp=%d gold=%d gold_acc=%d (%d bytes)'
#                 % (r.get('lev', 1), r.get('exp', 0), r.get('gold', 0),
#                    r.get('gold_acc', 0), len(pkt)))
#             return
        if cmd == 10333:
            # CS_10333（空）→ SC_10333{code:u8, msg:string}
            pkt = pack_frame(10333, w_u8(0) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10333 SC_10333 code=0 (%d bytes)' % len(pkt))
            return
        if cmd == 10621:
            # CS_10621 → SC_10621{world_lev:u16, skill_list:table(bid:u32, exp:u32)}
            # ★ S1-B：skill_list 的 bid 必须落在客户端 Config.SkillXiulianLev 键空间内。
            #   证据：analysis/extraction/lua_injection_channel_round.md §2.1 ——
            #   客户端拿 10621.skill_list 的 bid 去查 Config.SkillXiulianLev，
            #   合法键 = cfg/config_skill_xiulian.json SkillXiulianLearn 的 8 条
            #   （10101 攻击/10201 物防/10301 法防/10401 伙伴攻法/10501 伙伴物防/
            #     10601 伙伴法防/10701 控制/10801 抗控）。
            #   原 config.json skills=[10000/10001/10002/10822] 全不在该键空间 ⇒
            #   客户端查不到 ⇒ 修炼/技能列表空。实测改发 role_skills(10020) 仍空。
            #   现从真实客户端配置读 8 个修炼 bid；exp 取角色真实 practice_exp（=35，
            #   历史对应抗控修炼 10801 进度），其余 7 项 DB 无 per-skill 数据源 ⇒ exp=0
            #   （如实标注，不伪造数值）。
            import json as _json, os as _os
            _xl_bids = []
            try:
                with open(_os.path.join(runtime.HERE, 'cfg', 'config_skill_xiulian.json'),
                          encoding='utf-8') as _f:
                    _xl = _json.load(_f)
                for _k in (_xl.get('SkillXiulianLearn') or {}).keys():
                    _xl_bids.append(int(_k))
            except Exception as _e:
                log('tcp.log', '  !! 10621 xiulian cfg load failed: %r' % (_e,))
            _xl_bids.sort()
            _pe = int(role_state(self.cfg).get('practice_exp', 0) or
                      self.cfg.get('practice_exp', 0) or 0)
            out = w_u16(self.cfg.get('world_lev', 1)) + w_u16(len(_xl_bids))
            for _b in _xl_bids:
                out += w_u32(_b) + w_u32(_pe if _b == 10801 else 0)
            pkt = pack_frame(10621, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10621 SC_10621 world_lev=%d skill_list=%d（xiulian 键空间 %s）(%d bytes)'
                % (self.cfg.get('world_lev', 1), len(_xl_bids), _xl_bids, len(pkt)))
            return
        if cmd == 13340:
            # CS_13340（空）→ SC_13340 角色个人信息/名片
            #   name:string, lev:u8, career:u8, sex:u8, sign:string,
            #   guild_name:string, title:string, spouse_name:string,
            #   per_name:string, zone:string, city:string, gift_num:u16
            # 注意：这里的 lev/career/sex 是 u8（与 10301 的 lev:u16/career:u16 不同），
            #       按 manual 的定义逐字段照写。
            # ★★ R56 修复「等级口径不一致」：原先读 `self.cfg['role']`（= **config.json 的静态模板**），
            #   而 10301/10302/10303 走 `role_state()`（= **DB 真源**）⇒ 同一角色两处等级不同。
            #   实测：admin `/setlevel` 把 DB 改成 9 后，
            #     `10302 SC_10302 lev=9` 而 `13340 SC_13340 profile name=DSH lev=70`（还停在模板的 70）。
            #   与 R43「战力口径统一」同一类问题 ⇒ 身份/等级字段一律走 `role_state()`。
            r = role_state(self.cfg)
            out = (w_str(r.get('name', '')) + w_u8(int(r.get('lev', 1)) & 0xff) +
                   w_u8(int(r.get('career', 1)) & 0xff) + w_u8(int(r.get('sex', 0)) & 0xff) +
                   w_str(self.cfg.get('sign', '')) +
                   w_str(self.cfg.get('guild_name', '')) +
                   w_str(self.cfg.get('title', '')) +
                   w_str(r.get('spouse_name', '')) +
                   w_str(self.cfg.get('per_name', '')) +
                   w_str(self.cfg.get('zone', '')) +
                   w_str(self.cfg.get('city', '')) +
                   w_u16(self.cfg.get('gift_num', 0)) +
                   # ★ 以下 6 个字段原先**整段缺失**（应答在 gift_num 后截断），
                   #   客户端解析会越界读。由真机流量回放审计 tools/replay_captures.py 发现。
                   w_u32(self.cfg.get('nice_num', 0) or 0) +      # nice_num:uint32
                   w_u32(self.cfg.get('flower', 0) or 0) +        # flower:uint32
                   w_u8(self.cfg.get('new_msg', 0) or 0) +        # new_msg:uint8
                   w_u16(self.cfg.get('zone_skin', 0) or 0) +     # zone_skin:uint16
                   w_u16(self.cfg.get('head_skin', 0) or 0) +     # head_skin:uint16
                   w_u16(0))                                      # use_badge_list 空表
            pkt = pack_frame(13340, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 13340 SC_13340 profile name=%s lev=%d (%d bytes)'
                % (r.get('name', ''), r.get('lev', 1), len(pkt)))
            return
        if cmd in (12901, 12902, 12911, 12912, 12931):
            # ★★★ round40：排行榜（客户端 rank_ctrl.handle_12901/12902/12911/12912/12931）
            #   CS {ord:u8, num:u8, flag:u8}
            #      真机 body 7 字节 = 3 字段 + 客户端缓冲区 4 字节残留；
            #      实测五者恒为 ord=0 num=5 flag=1（12922 为 ord=1）。
            #   SC 结构（cmd_resolve_129.luac AutoConstruct 权威）：
            #     12901 战力榜: my_ord:u8, my_val:u32, rank_role:table[9×u32],
            #        rank_list:table[ord:u8, rid:u32, srv_id:s, name:s, sex:u8,
            #                         career:u16, val:u32, rank_role:table[9×u32],
            #                         show_partner:table[rebirth:u32, color:u32]]
            #     12902/12911/12912: my_ord, my_val, rank_list:[…, val:u32]
            #     12931 等级榜:      my_ord, my_val, rank_list:[…, lev:u8, val:u32]
            #   ★ 诚实性：本服只有 1 个角色 ⇒「自己是第 1 名」是真话（1/1）。
            #     · 12901 的 9 项战力构成里只有 power_eqm_role 有值：本服战力**完全**由
            #       角色属性/装备算出（power_mod.calc_power，与 10304 同一函数），
            #       未建模技能/英雄/坐骑等系统的独立战力 ⇒ 其余 8 项为 0 是**真实分解**。
            #     · 12931 = **斗魂排行**（`config_rank.subCfg` 的 label，非"等级榜"）
            #       ⇒ val = `arena_state.trophy`；条目里的 `lev:u8` 是规格字段，照发角色等级。
            #     · 12902 = **人物战力** ⇒ val = 综合战力（同 10304）。
            #     · 12911/12912 = **勇气排行 / 魅力排行** ⇒ val = `role_assets.courage/charm`
            #       （与 13331 同一数据源）；为 0 时**不上榜**（R130 的"榜上有我"规则）。
            #   ★★★ R243：榜名由 `config_rank.luac` 的 `subCfg[].label` **硬取证**
            #     （`TDUP{cmd,…} + KSTR('<榜名>') + TSETS(['label'])`，48 条全表见
            #      `tools/_diag_r243_rank_names.py` 与 `round243` 报告）。
            #     此前"榜名解不出 ⇒ 回空榜"的说法**被工具推翻**（老解构器漏了 `TSETV` 族赋值）。
            st = role_state(self.cfg)
            rid = int(st.get('rid', 1001) or 1001)
            srv = str(st.get('srv_id', '1') or '1')
            nm = str(st.get('name', 'DSH') or 'DSH')
            sex = int(st.get('sex', 0) or 0) & 0xff
            career = int(st.get('career', 1) or 1) & 0xffff
            lev = int(st.get('lev', 1) or 1) & 0xff
            pw = role_power(self.cfg) & 0xffffffff
            mv = rank_metric_value(cmd, rid, lev, pw)

            def _head(o):
                # ord, rid, srv_id, name, sex（career 是否在条目里逐榜不同：
                #   12901/12902/12911/12912 有 career:u16，12931 **没有** career）
                return (w_u8(o) + w_u32(rid) + w_str(srv) + w_str(nm) + w_u8(sex))

            if cmd == 12901:
                role_pw = w_u16(1) + w_u32(pw) + w_u32(0) * 8
                partner = w_u16(1) + w_u32(0) + w_u32(0)
                item = _head(1) + w_u16(career) + w_u32(pw) + role_pw + partner
                out = w_u8(1) + w_u32(pw) + role_pw + w_u16(1) + item
            elif cmd == 12931:
                # 斗魂排行：条目 = ord, rid, srv_id, name, sex, **lev:u8**, val:u32
                out = (w_u8(1) + w_u32(mv) + w_u16(1) +
                       _head(1) + w_u8(lev) + w_u32(mv))
            else:
                # ★ R243：12902 / 12911 / 12912 —— 有值才上榜（真话：本服只有 1 个角色）
                out = (w_u8(1 if mv > 0 else 0) + w_u32(mv) +
                       w_u16(1 if mv > 0 else 0) +
                       ((_head(1) + w_u16(career) + w_u32(mv)) if mv > 0 else b''))
            pkt = pack_frame(cmd, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d 排行榜%s val=%d (%d bytes)'
                % (cmd, cmd, '（%s）' % _RANK_METRIC[cmd] if cmd in _RANK_METRIC else '',
                   mv, len(pkt)))
            return
        if cmd == 10331:
            # CS_10331{skill_bid:uint32} → SC_10331{code:uint8, msg:string}
            # 技能升级请求：回 code=0 表示成功（本阶段只保证"有应答、不报错"）
            skill_bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            pkt = pack_frame(10331, w_u8(0) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10331 SC_10331 skill_bid=%d code=0 (%d bytes)'
                % (skill_bid, len(pkt)))
            return
        if cmd == 14901:
            # CS_14901（空）→ SC_14901{cur_bid:u16, xs_title_list:table(bid:u16,left_time:u32)}
            # ★ PHASE 2.17：**接真值** —— 原先**硬编码** `w_u16(0)+w_u16(0)`（恒"无称号"）。
            #   而**写入侧早已存在**：`db_title_add()` 写 `role_title` 表，
            #   GM 端点 `/DSH_ADMIN/title` 也读同一张表（L1042）⇒
            #   **即使 GM 给角色发了称号，客户端称号面板仍然显示"无"**（真实缺口）。
            #   现改为读 `role_title`；`left_time` 无期限来源 ⇒ 恒 0（不编造）。
            _rid49 = role_state(self.cfg).get('rid', 1001)
            _titles = []
            try:
                _c49 = db_conn()
                _titles = [int(r[0]) for r in _c49.execute(
                    'SELECT bid FROM role_title WHERE rid=? ORDER BY ctime',
                    (_rid49,)).fetchall()]
                db_release(_c49)
            except Exception as _e49:
                log('tcp.log', '  !! 14901 读 role_title 失败: %r' % (_e49,))
            _cur49 = int(role_state(self.cfg).get('cur_title') or 0) & 0xffff
            _out49 = w_u16(_cur49) + w_u16(len(_titles))
            for _b49 in _titles:
                _out49 += w_u16(_b49 & 0xffff) + w_u32(0)
            pkt = pack_frame(14901, _out49)
            self.request.sendall(pkt)
            log('tcp.log', '  << 14901 SC_14901 cur_bid=%d titles=%d（role_title 真值）'
                % (_cur49, len(_titles)))
            return
        if cmd in (13704, 13771, 13772):
            # ★★★ R81：**饱食度补充三连**（真机点"补充"走的就是这里）
            #   原先它们在 `_GENERIC_DEFAULT_CMDS` 里 ⇒ 回"成功但空"：
            #     `SC_13771/13772` 的 `val` 恒为 **0**，而客户端 `build_ctrl` 的初值是
            #     `hunger_val = 65535`（满）⇒ **每点一次补充，饱食度就被写成 0**
            #     ⇒ 表现就是「饱食度无法补充」（用户报障）。
            #   修复：`val` 直接回**满值 65535**（沿用客户端初始化的同一常量，
            #   硬证据见 `build_ctrl.luac` proto#2），`price` 回 0（**未实现扣费**，
            #   如实标注而不是编一个价格），`msg` 为空。
            if cmd == 13704:
                # CS 空 → SC{lev1..lev4}：食物/技能堆叠等级。初始态为 0（proto#2），
                # 结构照规格发，**不编造等级**。
                _out = w_u8(0) + w_u8(0) + w_u8(0) + w_u8(0)
                _tag = 'SC_13704 堆叠等级(0,0,0,0)'
            elif cmd == 13771:
                _out = w_u16(HUNGER_MAX) + w_u32(0)
                _tag = 'SC_13771 银魂币补充 val=%d price=0(未实现扣费)' % HUNGER_MAX
            else:
                _out = w_u8(1) + w_str('') + w_u16(HUNGER_MAX)
                _tag = 'SC_13772 食用物品补充 code=1 val=%d' % HUNGER_MAX
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d %s (%d bytes)' % (cmd, _tag, len(_out) + 6))
            return
        if cmd == 11216:
            # ★★★ R86：**神将兑换** —— 「兑换成功后伙伴没进背包」的真源就在这里。
            #   客户端 `game/godredeem/godredeem_ctrl.luac`：
            #     proto#3 `send_11216(partner_bid, state)` → CS{partner_bid:u32, state:u8}
            #     proto#4 `handle_11216(data)`：
            #         if data.code ~= 0 then                     -- ★ code 非 0 = 成功
            #             closeView(); HeroEquipCtrl:openGainPanelByBid(data.partner_bid)
            #         end
            #         message(data.msg)                          -- ★ 无条件 ⇒ 成功时 msg 必须为空
            #   ⇒ 客户端那个"获得动画"是**本地**播的（`code ~= 0` 就播），
            #     服务端**必须真的把伙伴写进伙伴背包**，否则动画播完背包里什么都没有。
            #   协议：SC_11216{code:u8, msg:string, partner_bid:u32}
            _pb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _st = body[4] if len(body) >= 5 else 0
            _rid_h = role_state(self.cfg).get('rid', 1001)
            _pd = partner_def(_pb)
            if _pb and _pd:
                _new = db_hero_add(_rid_h, _pb, color=int(_pd.get('color') or 0))
                _out = w_u8(1) + w_str('') + w_u32(_pb)
                log('tcp.log', '  << 11216 SC_11216 兑换伙伴 %d(%s) code=1 %s (%d bytes)'
                    % (_pb, _pd.get('name') or '?',
                       '首次获得' if _new else '已拥有(进度保留)', len(_out) + 6))
            else:
                _out = w_u8(0) + w_str('无效伙伴(%d)' % _pb) + w_u32(_pb)
                log('tcp.log', '  << 11216 SC_11216 兑换伙伴 %d ⇒ code=0（不在伙伴表）'
                    % _pb)
            self.request.sendall(pack_frame(11216, _out))
            return
        if cmd == 16605:
            # ★ R86：功能开启查询（`CS{bid_list:table(bid:u32)}` → `SC{status:table(bid,code,end_time)}`）。
            #   真机实测（见 analysis/extraction/real_cs_formats_1_4_11.md）：
            #   客户端**一次发 108 个 bid**（5007/5008/5991/…），问"这些功能是否开启"。
            #   ⚠ `status[].code` 的**取值语义未取证**（"开启/未开启/倒计时"分别是什么值）
            #     ⇒ 默认按纪律**回空表**（结构正确、不误导），只记请求规模。
            #   ★ 实验通道：设 `DSH_16605_CODE=<n>` 可对请求的每个 bid 回 `code=n`，
            #     用于在**真机**上观察客户端行为变化，从而反推 code 语义（实验性质，非结论）。
            _n = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            # ★★ PHASE 2.18：客户端语义已**反汇编确认**（game/action/action_ctrl.luac proto#7）：
            #      function(bid):
            #        for v in act_state_list.status do
            #          if v.bid == bid then return v.code ~= 0 end   -- code!=0 ⇒ true(开启)
            #        end
            #        return false        -- KPRI 1=false ⇒ **找不到即为未开启**
            #    ⇒ **回空表 = 全部未开启**（正是旧实现让活动入口不显示的原因）；
            #      要"开启"必须**为每个请求的 bid 回一条 code != 0 的记录**。
            #    本服为全开放环境 ⇒ 默认对每个 bid 回 code=1；
            #    可用 `DSH_16605_CODE=0` 复现"全关"做对照（联调用）。
            try:
                _code = int(os.environ.get('DSH_16605_CODE', '1')) & 0xff
            except Exception:
                _code = 1
            _bids = []
            for _i in range(_n):
                _o = 2 + 4 * _i
                if len(body) >= _o + 4:
                    _bids.append(struct.unpack_from('>I', body, _o)[0])
            _out = w_u16(len(_bids))
            for _b in _bids:
                _out += w_u32(_b) + w_u8(_code) + w_u32(0)   # end_time 无来源 ⇒ 0（不编造）
            self.request.sendall(pack_frame(16605, _out))
            log('tcp.log', '  << 16605 SC_16605 status=%d code=%d（客户端语义：code!=0=开启）'
                % (len(_bids), _code))
            return
        if cmd == 10640:
            # ★★★ R80：**buff 列表查询** —— 饱食度走的就是这条。
            #   协议（`protocol/fields.json`）：
            #       CS_10640 — 无字段（空消息）
            #       SC_10640 — buff_list: table(caeer:uint8, buff_bid:uint32)
            #                                            ↑ 原文拼写，= career
            #   依据（真机 + 反汇编）：`buff_manager.luac` 注册 `hander10640`，
            #   并且**真机一直在发** `CS_10640`（空 body，日志里 18:54 / 19:01 / 19:18 …），
            #   而本服此前**完全没处理它**（不在任何集合、无专用分支）⇒ **无应答**
            #   ⇒ 客户端拿不到 buff 列表 ⇒ 「饱食度无法补充」（用户报障）。
            _rid6 = role_state(self.cfg).get('rid', 1001)
            _bl = db_buff_list(_rid6)
            _b6 = w_u16(len(_bl))
            for _x in _bl:
                _b6 += w_u8(int(_x.get('career') or 0))
                _b6 += w_u32(int(_x.get('buff_bid') or 0))
            self.request.sendall(pack_frame(10640, _b6))
            log('tcp.log', '  << 10640 SC_10640 buff_list=%d %s'
                % (len(_bl), [x.get('buff_bid') for x in _bl][:8]))
            return
        if cmd == 15202:
            # ★★ R69：挂机怪「发起战斗」—— `CS{mon_bid:u32}` → `SC{code:u8, msg:string}`
            #   为什么现在才补：R65 的探针证明 `createMon()` 已成功（`done_mon_id=30068/…`），
            #   下一步就是客户端调 `GhostMon:fight()`；反汇编（`ghost_mon` proto#5）显示
            #   它发的是 **`15202`**（不是 20002）：
            #       if self.mon_id then
            #           proto = ProtocalRulesMgr:GetPrototype(15202); proto.mon_bid = self.mon_bid
            #           SendProtocal(proto)
            #       end
            #   而此前 `15202` **不在任何集合、也没有专用分支** ⇒ 客户端发出去**没有应答**（干等）。
            #   本实现：mon_bid 必须是 `Config.Mon` 里真实的怪 ⇒ 回 `code=1`（允许开打）；
            #   否则回 `code=0 + msg`（不静默接受垃圾输入）。
            #   注：本服的 `20000~20099` 战斗族**已实现**，所以回 code=1 不是撒谎。
            _mon2 = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _d2 = mon_def(_mon2) if _mon2 else {}
            if _mon2 and _d2:
                out = w_u8(1) + w_str('')
                log('tcp.log', '  << 15202 发起战斗 mon_bid=%d(%s) ⇒ code=1'
                    % (_mon2, _d2.get('name') or '?'))
            else:
                out = w_u8(0) + w_str('未知怪物(%d)' % _mon2)
                log('tcp.log', '  << 15202 发起战斗 mon_bid=%d ⇒ code=0（不在 Config.Mon 里）' % _mon2)
            self.request.sendall(pack_frame(15202, out))
            return
# [P2D-migrated] npc/handler.py handle_15203
#         if cmd == 15203:
#             # CS_15203（空）→ SC_15203{code:uint8, msg:string}
#             # 依据：game/npc/npc_ctrl.luac 的 RegisterProtocal(15203, 'handle15203')
#             #      与 NpcCtrl:clickNpcOpenDialog 里的 GetPrototype(15203)；
#             #      字段取自 protocol/manual.md（tools/show_cmd.py 15203）。
#             pkt = pack_frame(15203, w_u8(0) + w_str(''))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 15203 SC_15203 code=0 (%d bytes)' % len(pkt))
#             return
        if cmd == 12402:
            # CS_12402{mission_bid:uint32} → SC_12402{code:u8, msg:string,
            #                                          missions:table(13 字段)}
            # 依据：mission_ctrl.luac 的 RegisterProtocal(12402, ...)；
            #      字段取自 protocol/manual.md（tools/show_cmd.py 12402）。
            # Phase 5F：接取任务 → 回 code=1(TRUE) + 更新后的完整任务列表
            # 依据（实测反汇编，mission_ctrl.luac proto[39] receiveHandler）：
            #   if resp.code == TRUE then message(getString('成功接取任务'))
            #   else message(resp.msg) end
            # ⇒ 接取成功必须回 code=1(TRUE)；回 0 会被客户端当失败 → message(msg)
            # 若 msg 为空 → 空白提示框。（本次订正：原 code=0 写反）
            bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid = role_state(self.cfg).get('rid', 1001)
            # ★ C3.2-C I1（缺口①）：接取校验——原先任意 bid 都回 code=1(TRUE)+全表，
            #   不查可接取列表/是否已接/是否已完成。客户端 auto_accept=1 基本不发 12402，
            #   此处为防御性收紧（不改包结构）：
            #     ① 配置里不存在 → code=0；
            #     ② 已完成(status=3) → code=0（不落库、不重复接取）；
            #     ③ 已在途(status=1/2) → code=0（重复接取不落库）；
            #     ④ 不在可接取链窗口(mission_chain)内 → code=0。
            #   全部失败回包均带空 missions 表(w_u16(0))，保持包结构完整。
            def _rej_12402_1(msg):
                pkt = pack_frame(12402, w_u8(0) + w_str(msg) + w_u16(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12402 SC_12402 accept bid=%d code=0 (%s)' % (bid, msg))
            if not mission_def(bid):
                _rej_12402_1('no such mission'); return
            _rows = db_get_missions(_rid)
            _m = _rows.get(bid)
            if _m is not None:
                _st = int(_m.get('mission_status') or 0)
                if _st == 3:
                    _rej_12402_1('already completed'); return
                _rej_12402_1('already accepted'); return
            if bid not in mission_chain(self.cfg, _rid):
                _rej_12402_1('not available'); return
            # ⚠ 自查修正：原先取 `self.cfg['missions']`，但任务已改为**由 APK 任务表驱动**
            #   （config.missions 通常为空）⇒ 会回一个空列表。改用与 12400 相同的来源。
            ms = mission_rows(self.cfg, _rid)
            out = w_u8(1) + w_str('') + (w_u16(len(ms)) +
                                         b''.join(build_mission_entry(x) for x in ms))
            pkt = pack_frame(12402, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 12402 SC_12402 accept mission_bid=%d code=1(TRUE) '
                           'missions=%d (%d bytes)' % (bid, len(ms), len(pkt)))
            return
        if cmd == 12403:
            # CS_12403{mission_bid:uint32} → SC_12403{mission_bid:u32, code:u8, msg:string}
            # Phase 5H/5I：提交任务 → 结算（发奖 + 更新角色数据 + 任务落库）
            bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            st = role_state(self.cfg)
            rid = st.get('rid', 1001)
            # ★ 注意：这里必须用**未过滤**的 db_get_missions()，
            #   否则已提交（status=3）的任务会被过滤掉、走到 "no such mission" 分支，
            #   幂等语义就失效了。（自查发现的疏漏，已修）
            #   另外：若库里还没有任务行（12400 尚未触发播种），这里先播种一次。
            if not db_get_missions(rid):
                mission_rows(self.cfg, rid)      # 触发播种
            rows = db_get_missions(rid)
            m = rows.get(bid)
            # ★ C3.2-C I2（缺口③）：取消"DB 无行但配置存在 ⇒ 自动播种 status=2 放行"。
            #   原实现允许绕过链窗口直接提交任意已解锁配置任务。正常流程下，可提交任务
            #   必由 mission_rows 播种进 DB（链头强制 status=2、条件达成提升 status=2），
            #   此处不再为任意配置 bid 凭空播种+结算。配置里存在但 DB 无行 ⇒ 视为不可提交。
            if m is None:
                # 不存在/未接取的任务：code=0(非TRUE) + msg，客户端走 message(msg) 提示
                pkt = pack_frame(12403, w_u32(bid) + w_u8(0) + w_str('no such mission'))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12403 SC_12403 mission_bid=%d code=0 (no such mission row)' % bid)
                return
            # ★ 幂等保护（自查发现的 bug 修复）：已提交过（STATUS_3）就直接回包，
            #   **不再发奖**。否则客户端反复提交会刷奖励。
            #   已提交视为"再次成功提交"：回 code=1(TRUE)（幂等成功，无 msg）。
            #   不能回 0：客户端 code≠TRUE 时会 message(resp.msg)，msg=''→空白框。
            if int(m.get('mission_status') or 0) == 3:
                pkt = pack_frame(12403, w_u32(bid) + w_u8(1) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12403 SC_12403 mission_bid=%d code=1(TRUE) '
                               '(already committed, idempotent)' % bid)
                return
            # ★ C3.2-C I3（缺口③）：提交领奖资格——仅 status==2（条件满足待提交）可结算。
            #   status==1（进行中/条件未满足，含非链头）拒绝；status==3 已在上方幂等短路。
            #   这与下方 value>=need 的完成判定一致（mission_rows 归一化：条件达成才置 2）。
            if int(m.get('mission_status') or 0) != 2:
                need = int(m.get('target_value') or 0)
                have = int(m.get('value') or 0)
                pkt = pack_frame(12403, w_u32(bid) + w_u8(0) +
                                 w_str('condition not met %d/%d' % (have, need)))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12403 SC_12403 mission_bid=%d code=0 '
                               '(status=%d not ready %d/%d)'
                               % (bid, m.get('mission_status'), have, need))
                return
            # 该任务在 config 里的奖励（reward_exp / reward_gold 为显式字段；
            # award_assets 的二元组含义仍是待验证项，此处不猜）
            cm = None
            for x in (self.cfg.get('missions') or []):
                if x.get('mission_bid') == bid:
                    cm = x
                    break
            cm = cm or {}
            # ★ 完成判定（依据 APK 的 `progress` 生成的条件）：
            #   target_value > 0 表示有进度要求；value 是当前进度。
            #   - 无进度要求（如 10010）⇒ 直接可提交
            #   - 有进度要求但 value < target_value ⇒ **判定未完成**，回 code=0+msg
            #     （`mission_skip_condition=true` 可临时跳过，便于联调剧情链）
            need = int(m.get('target_value') or 0)
            have = int(m.get('value') or 0)
            if need > 0 and have < need and not self.cfg.get('mission_skip_condition'):
                # 条件未满足：code=0(非TRUE) + msg，客户端走 message(msg) 展示进度。
                # 不能回 1：code=1 会被客户端当**成功**并 del+UPDATE_MISSION，
                # 反而把未完成的任务从列表里删掉（本次订正：原 code=1 写反）。
                pkt = pack_frame(12403, w_u32(bid) + w_u8(0) +
                                 w_str('condition not met %d/%d' % (have, need)))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12403 SC_12403 mission_bid=%d code=0 '
                               '(条件未满足 %d/%d)' % (bid, have, need))
                return
            # ★★ 配置驱动：直接解码客户端的 `award_assets`（code → 资产字段名）
            #    `award_assets` 取自 `mission_config.json`
            #    （从客户端 config_mission.luac 提取）；
            #    config.json 里若也写了 award_assets 则作为覆盖（便于手工调试）。
            apk_def = mission_def(bid)
            aa = (cm.get('award_assets') or apk_def.get('award_assets') or [])
            # 解码表来自客户端 `config_game_data.luac` 的 `AssetsEnToCode`（38 项）
            delta, unknown = decode_award_assets(aa)
            if unknown:
                log('tcp.log', '  !! mission %d award_assets 含未知 code: %r '
                               '（按"不猜"原则未发放）' % (bid, unknown))
            if not delta and not unknown:
                # 回退：任务没配 award_assets 时，兼容旧的 reward_* 手写字段
                for k, f in (('reward_exp', 'exp'), ('reward_coin', 'coin'),
                             ('reward_gold', 'gold')):
                    v = int(cm.get(k, 0) or 0)
                    if v:
                        delta[f] = delta.get(f, 0) + v
            # 奖励一律写**通用资产表**（role_state 合并时资产表优先 ⇒ 不占固定列，
            # 任何 AssetsEnToCode 里的资产都能发）
            #
            # ★ Phase E：**经验单独走升级结算**（不能直接 db_add_assets），
            #   否则经验只涨不升级。其余资产照旧累加。
            _exp_gain = int(delta.pop('exp', 0))
            _lvres = None
            if _exp_gain:
                _lvres = add_role_exp(self.cfg, rid, _exp_gain)
            # [P45-C] 奖励统一走 RewardService.grant（reference_id=task:bid:rid，幂等去重）
            _awards = [{'kind': 'asset', 'code': k, 'amount': int(v)}
                       for k, v in delta.items() if int(v)]
            grant(rid, _awards, reference_id='task:%d:%d' % (bid, rid), source='task')
            add_exp = _exp_gain
            add_coin = int(delta.get('coin', 0))
            add_gold = int(delta.get('gold', 0))
            log('tcp.log', '  ** mission %d award_assets=%r -> delta=%r'
                % (bid, aa, delta))
            # 任务状态落库：标记为已提交（STATUS_3 = 3）
            m2 = {'mission_bid': bid, 'mission_status': 3, 'process_status': 1,
                  'commit_num': int(m.get('commit_num', 0)) + 1,
                  'loop_num': int(m.get('loop_num', 1)),
                  'value': int(m.get('target_value', 0)),
                  'accept_time': int(m.get('accept_time', 0) or 0)}
            db_save_mission(rid, m2)
            # ① 提交应答：code=1(TRUE) 表示成功。客户端 submitHandler
            #   （mission_ctrl.luac proto[46]，实测反汇编）：
            #       if resp.code ~= TRUE then message(resp.msg)  -- 失败分支
            #       else mission_data:del(...); panel:update(); Fire(UPDATE_MISSION) end
            #   回 0 ⇒ 客户端当失败 → message('') → 空白框，且**不会删除任务**
            #   ⇒ 客户端反复提交。(本次订正：原 code=0 写反，是"提交后空白框/重复提交"根因)
            # ★★ R48：**真实进度挂钩** —— 任务提交成功 = 一个可数事件。
            #   按 `server/_chengjiu_map.json` 的分组，同时给**日常次数**与
            #   **成就进度**各 +1（两者的语义都是"该线完成轮数"，天然自洽）。
            #   这样进度不再靠 admin 造，而是**跟着玩家真实行为长**。
            try:
                credit_mission_done(self.cfg, rid, bid)
            except Exception as e:
                log('tcp.log', '  !! 进度挂钩失败: %r' % (e,))
            pkt = pack_frame(12403, w_u32(bid) + w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 12403 SC_12403 commit mission_bid=%d code=1(TRUE) (%d bytes)'
                % (bid, len(pkt)))
            # ② 任务增量更新（12405）
            ms2 = mission_rows(self.cfg, rid)
            pkt = pack_frame(12405, build_12400(ms2))
            self.request.sendall(pkt)
            log('tcp.log', '  << 12405 SC_12405 update_mission_list=%d (%d bytes)'
                % (len(ms2), len(pkt)))
            # ②b 提交后把任务**移出列表**（12406 del_mission_list）
            #    依据：mission_ctrl 注册了 12406，SC_12406{del_mission_list:table(mission_bid:u32)}
            #    —— 这正是"任务结束"的正规通知，可避免客户端反复提交。
            pkt = pack_frame(12406, w_u16(1) + w_u32(bid))
            self.request.sendall(pkt)
            log('tcp.log', '  << 12406 SC_12406 del_mission_list=[%d] (%d bytes)'
                % (bid, len(pkt)))
            # ③ 角色数据刷新（10301 / 10302 / 10303）—— 让面板/经验条立刻更新
            #   （自查：这三条原先没打日志，导致无法判断刷新是否发生，现补上）
            st2 = role_state(self.cfg)
            self.request.sendall(pack_frame(10302, build_10302(st2)))
            log('tcp.log', '  << 10302 (refresh after commit) lev=%s exp=%s gold=%s '
                           'coin=%s' % (st2.get('lev'), st2.get('exp'),
                                        st2.get('gold'), st2.get('coin')))
            self.request.sendall(pack_frame(10301,
                build_10301(st2, self.cfg.get('skills', []))))
            self.request.sendall(pack_frame(10303,
                build_10303(st2, self.cfg.get('skills', []), self.cfg.get('attr'))))
            log('tcp.log', '  << 10301/10303 (refresh after commit) coinsent=%s'
                % st2.get('coin'))
            log('tcp.log', '  ** mission %d committed: +%d exp, +%d coin, +%d gold '
                           '(now exp=%d coin=%d gold=%d)'
                % (bid, add_exp, add_coin, add_gold,
                   st2.get('exp'), st2.get('coin'), st2.get('gold')))
            return
        if cmd == 12831:
            # CS_12831（空）→ SC_12831{id_list:table(id:u16, has_buy_num:u16)}
            # 依据：`tools/show_cmd.py 12831`；**无 D|Dsc*| 未解子表** ⇒ 可安全编码。
            # ★ 实测：客户端**打开商城的第一时间**就请求它（11:45:56 收到 12831，
            #   11:45:59 才收到 12803）——原实现**不应答** ⇒ 商城拿不到"已购数量"。
            # ⚠ 字段语义按字面取"已购买次数"（对照 12801 的 `can_buy_num`=可购买数量）；
            #   原版限购总量不可得，这里只如实回报**本服务端记录到的购买次数**。
            self._send_12831()
            return
        if cmd in (12836, 12838, 12842):
            # ★★ Phase F：珍宝/限时商店（12836）、副本商店（12838）、副本商店2（12842）
            #
            # 依据：`shop_model.luac` proto#61 `requestZhenbaoData` → `ctrl:request12836()`；
            #       proto#62 `setZhenbaoGoodsList(resp)` 读 `resp.goods_list`。
            #       权威字段：`python tools/proto_spec.py cmds 12836`
            #         goods_list: T(id:u16, item_bid:u32, bind:u8, pay_type:u8,
            #                       old_price:u32, price:u32, limit_num:u8, buy_num:u8)
            # ⚠ 与 12801 的 xs_list **结构不同**（见 build_goods_list_sc12836 的注释）。
            #
            # 数据来源：
            #   12836（珍宝）：server/mall_zhenbao.json —— id 取自原版 Config.MallXian，
            #                  其余字段为 IMPLEMENTATION_FALLBACK（见 mall_zhenbao() 头注）
            #   12838/12842（副本商店）：原版数据同样不在 APK 内，
            #                  本阶段**先复用珍宝表**以保证页签有货、可购买；
            #                  这是**明确的兼容做法**，不是原版配置。
            rid = role_state(self.cfg).get('rid', 1001)
            goods = mall_zhenbao() or []
            # 只卖真实物品表里存在的（否则买回去的背包会空白）
            goods = [g for g in goods if is_valid_item(g.get('item_bid', 0))]
            bought = db_mall_bought(rid)
            body = build_goods_list_sc12836(goods, bought)
            pkt = pack_frame(cmd, body)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d goods_list=%d (%d bytes)%s'
                % (cmd, cmd, len(goods), len(pkt),
                   '' if cmd == 12836 else '［复用珍宝表·兼容做法］'))
            return
        if cmd in (12837, 12839, 12843):
            # ★★ Phase F：限时/副本商店**购买**
            #   权威字段：SC_12837{code:u8, msg:str, id:u16, num:u16}
            #             CS_12837{id:u16, num:u16}
            #   ⚠ 与 SC_12805 不同：**没有 price 字段**。
            bid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            num = struct.unpack_from('>H', body, 2)[0] if len(body) >= 4 else 0
            if num <= 0:
                num = 1

            def _fail(msg, price=0):
                pkt = pack_frame(cmd, w_u8(0) + w_str(msg) + w_u16(bid) + w_u16(num))
                self.request.sendall(pkt)
                log('tcp.log', '  << %d SC_%d code=0 (%s) goods_id=%d x%d'
                    % (cmd, cmd, msg, bid, num))

            src = [g for g in (mall_zhenbao() or [])
                   if is_valid_item(g.get('item_bid', 0))]
            g = shop_find_goods(src, bid)
            if g is None:
                _fail('no such goods %d' % bid)
                return
            st = role_state(self.cfg)
            rid = st.get('rid', 1001)
            item_bid = int(g.get('item_bid', bid))
            pay = shop_pay_asset(self.cfg, g)
            unit = int(g.get('price', 0))
            total = unit * num
            # 限购（原版字段 `limit_num`，12836 的 u8）
            lim = int(g.get('limit_num', 0) or 0)
            gid = int(g.get('id', bid))
            bought0 = int((db_mall_bought(rid) or {}).get(gid, 0))
            if lim > 0 and bought0 + num > lim:
                _fail('超过限购（限购 %d，已购 %d）' % (lim, bought0))
                return
            have = int(st.get(pay, 0) or 0)
            if total > 0 and have < total:
                _fail('%s 不足（需 %d，有 %d）' % (pay, total, have))
                return
            if total > 0:
                # ★ 用 `db_set_assets` **绝对值**写入，而不是 `db_add_assets`。
                #   原因：`role_state()` 的合并顺序是「roles 行 < role_assets」，
                #   `have` 取的是**合并后的有效值**；若只做增量写，
                #   `roles.gold=1000` 而 `role_assets` 里没有 gold 行时，
                #   `db_add_assets({gold:-50})` 会得到 -50，而不是 950（实测踩过）。
                db_set_assets(rid, {pay: have - total})
            if not db_bag_add(rid, item_bid, num):
                log('tcp.log', '  !! %d 购买：扣钱成功但入包失败 item=%d' % (cmd, item_bid))
            db_mall_bought_add(rid, gid, num)
            pkt = pack_frame(cmd, w_u8(1) + w_str('') + w_u16(bid) + w_u16(num))
            self.request.sendall(pkt)
            bag_push_frames(self, rid)
            # ★ 珍宝页签的 buy_num 来自 SC_12836.goods_list（不是 12831），
            #   购买后主动重推 12836，客户端 setZhenbaoGoodsList 即时刷新已购数。
            _zb = [g for g in (mall_zhenbao() or []) if is_valid_item(g.get('item_bid', 0))]
            _zb_body = build_goods_list_sc12836(_zb, db_mall_bought(rid))
            self.request.sendall(pack_frame(12836, _zb_body))
            log('tcp.log', '  << 12836 重推 goods_list=%d (%d bytes)（珍宝购买后刷新）'
                % (len(_zb), len(_zb_body)))
            live_push(self.cfg, 'shop_buy')
            log('tcp.log', '  ** 购买成功(%d) goods_id=%d item=%d x%d 扣 %s=%d  '
                           '<< SC_%d code=1(TRUE) (%d bytes)'
                % (cmd, gid, item_bid, num, pay, total, cmd, len(pkt)))
            return
        if cmd == 12840:
            # ★ Phase F：兑换商店货物列表（SC_12840.goods_list = 交换配方）
            rid = role_state(self.cfg).get('rid', 1001)
            goods = [g for g in (mall_exchange() or [])
                     if is_valid_item(g.get('item_bid', 0))
                     and is_valid_item(g.get('new_item_bid', 0))]
            body = build_goods_list_sc12840(goods, db_mall_bought(rid))
            pkt = pack_frame(12840, body)
            self.request.sendall(pkt)
            log('tcp.log', '  << 12840 SC_12840 goods_list=%d (%d bytes)'
                % (len(goods), len(pkt)))
            return
        if cmd == 12841:
            # ★ Phase F：兑换（12841）：扣 item_bid×item_num×num → 发 new_item_*×num
            bid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            num = struct.unpack_from('>H', body, 2)[0] if len(body) >= 4 else 0
            if num <= 0:
                num = 1

            def _xfail(msg):
                pkt = pack_frame(12841, w_u8(0) + w_str(msg) + w_u16(bid) + w_u16(num))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12841 SC_12841 code=0 (%s) id=%d' % (msg, bid))

            src = [g for g in (mall_exchange() or [])
                   if is_valid_item(g.get('item_bid', 0))
                   and is_valid_item(g.get('new_item_bid', 0))]
            g = shop_find_goods(src, bid)
            if g is None:
                _xfail('no such exchange %d' % bid)
                return
            rid = role_state(self.cfg).get('rid', 1001)
            need_bid = int(g.get('item_bid', 0))
            need_num = int(g.get('item_num', 0)) * num
            lim = int(g.get('limit_num', 0) or 0)
            gid = int(g.get('id', bid))
            bought0 = int((db_mall_bought(rid) or {}).get(gid, 0))
            if lim > 0 and bought0 + num > lim:
                _xfail('超过限购（限购 %d，已购 %d）' % (lim, bought0))
                return
            # 材料是否足够（按背包内该 item_bid 的**总数量**）
            have = sum(int(it.get('quantity') or 0)
                       for it in db_bag_get(rid, BAG_MAIN)
                       if int(it.get('bid') or 0) == need_bid)
            if have < need_num:
                _xfail('材料不足 item=%d 需 %d 有 %d' % (need_bid, need_num, have))
                return
            # 扣材料（逐行扣，扣完删行）
            left = need_num
            for it in list(db_bag_get(rid, BAG_MAIN)):
                if left <= 0:
                    break
                if int(it.get('bid') or 0) != need_bid:
                    continue
                take = min(left, int(it.get('quantity') or 0))
                newq = int(it['quantity']) - take
                if newq <= 0:
                    db_bag_delete(rid, [int(it['item_id'])])
                else:
                    db_bag_set_quantity(rid, int(it['item_id']), newq)
                left -= take
            db_bag_add(rid, int(g.get('new_item_bid', 0)),
                       int(g.get('new_item_num', 0)) * num)
            db_mall_bought_add(rid, gid, num)
            bag_push_frames(self, rid)
            self._send_12831()
            live_push(self.cfg, 'shop_exchange')
            pkt = pack_frame(12841, w_u8(1) + w_str('') + w_u16(bid) + w_u16(num))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 兑换成功 id=%d: item=%d x%d -> item=%d x%d  '
                           '<< SC_12841 code=1(TRUE) (%d bytes)'
                % (gid, need_bid, need_num,
                   int(g.get('new_item_bid', 0)),
                   int(g.get('new_item_num', 0)) * num, len(pkt)))
            return
        if cmd in (12801, 12802):
            # CS_12801/12802（空）→ SC{xs_list:table(id:u16, item_bid:u32, bind:u8,
            #   **pay_type:u8**, old_price:u32, price:u32, type:u8, ico:u8, left_time:u32,
            #   can_buy_num:u16)}     （SC_12802 额外带 id:u16）
            # 依据：protocol/manual.md（show_cmd 12801/12802）；无 D|Dsc*| 子表 ⇒ 安全。
            # ★ 这里有 **pay_type** —— “用哪种币支付”就在协议里，不用猜。
            goods = mall_cfg() or (self.cfg.get('shop_list') or [])
            # ★ 只卖“真实物品表内存在”的东西，否则买回来会把背包搞成空白
            goods = [g for g in goods if is_valid_item(g.get('item_bid', 0))]
            out = b''
            if cmd == 12802:
                out += w_u16(int(self.cfg.get('shop_category', 0)))
            out += w_u16(len(goods))
            _bought_map = db_mall_bought(role_state(self.cfg).get('rid', 1001))
            for g in goods:
                out += (w_u16(int(g.get('id', g.get('item_bid', 0)))) +
                       w_u32(int(g.get('item_bid', 0))) +
                       w_u8(int(g.get('bind', 0))) +
                       w_u8(int(g.get('pay_type', 0))) +
                       w_u32(int(g.get('old_price', g.get('price', 0)))) +
                       w_u32(int(g.get('price', 0))) +
                       w_u8(int(g.get('type', 0))) +
                       w_u8(int(g.get('ico', 0))) +
                       w_u32(int(g.get('left_time', 0))) +
                       # ★ 原来写死 0（=不限购）；现按原版 limit_week − 已购 推导，
                       #   见 can_buy_num() 的注释与证据。
                       w_u16(can_buy_num(g, _bought_map)))
            if cmd == 12801:
                out = w_u32(int(self.cfg.get('guild_shop_lev', 0))) + out
            pkt = pack_frame(cmd, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d xs_list=%d (%d bytes)'
                % (cmd, cmd, len(goods), len(pkt)))
            return
        if cmd == 12803:
            # CS_12803（空）→ SC_12803{item_list:table(item_bid:u32, price:u32)}
            # 依据：protocol/manual.md（show_cmd 12803）；无 D|Dsc*| 未解子表 ⇒ 可安全编码。
            # 商品表由 config.json 的 shop_list 驱动（[{item_bid, price}])，
            # 默认空表（不编造商品）。
            goods = mall_cfg() or (self.cfg.get('shop_list') or [])
            goods = [g for g in goods if is_valid_item(g.get('item_bid', 0))]
            out = w_u16(len(goods))
            for g in goods:
                out += w_u32(int(g.get('item_bid', 0))) + w_u32(int(g.get('price', 0)))
            pkt = pack_frame(12803, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 12803 SC_12803 item_list=%d (%d bytes)'
                % (len(goods), len(pkt)))
            return
        if cmd == 12805:
            # CS_12805{id:u16, num:u16} → SC_12805{code:u8, msg:str, id:u16, num:u16, price:u32}
            # ★ 购买闭环：校验商品 → 扣货币 → 发货进包 → 推送 → 回包
            #   ⚠ 货币种类由 config 的 shop_pay_asset 指定（默认 coin），
            #     **不是推测出来的**；原版用哪种币需以 pay_type 为准（待验证）。
            bid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            num = struct.unpack_from('>H', body, 2)[0] if len(body) >= 4 else 0
            if num <= 0:
                num = 1
            # ★ 修正（用户实机报障：“no such goods 20xx”）：
            #   CS_12805 的 `id` 是**商品条目的 id**（如 2001），
            #   **不是** `item_bid`（如 25890）。原实现只按 item_bid 查 ⇒ 查不到。
            #   现按 id 优先，回退 item_bid（兼容 12803 只有 item_bid 的情形）。
            src = mall_cfg() or (self.cfg.get('shop_list') or [])
            src = [g for g in src if is_valid_item(g.get('item_bid', 0))]
            g = None
            for cand in src:
                if int(cand.get('id', -1)) == bid:
                    g = cand
                    break
            if g is None:
                for cand in src:
                    if int(cand.get('item_bid', -1)) == bid:
                        g = cand
                        break
            item_bid = int(g.get('item_bid', bid)) if g is not None else bid
            if g is None:
                pkt = pack_frame(12805, w_u8(0) + w_str('no such goods %d' % bid) +
                                 w_u16(bid) + w_u16(num) + w_u32(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12805 SC_12805 code=0 (goods %d 不存在)' % bid)
                return
            st = role_state(self.cfg)
            rid = st.get('rid', 1001)
            # ★ 支付币种：**优先读该商品的 pay_type 映射**，
            #   没配就回退到 shop_pay_asset。
            #   依据：12801/12802 的商品项带 pay_type:u8（原版字段）；
            #   **pay_type 到币种的对应关系仍需实机验证**，故做成配置项。
            # ★ 支付币种（本轮改为与客户端**同一张权威表**）：
            #   客户端 `common_function.payTypeEnToCode(pay_type)`
            #     = `Config.AssetsEnToCode[pay_type] or 1`
            #   （proto#69，7 条字节码，已反汇编；见 tools/export_map.py）
            #   而 `AssetsEnToCode` 就是本文件的 ASSETS_EN_TO_CODE（逐项核对过）
            #   ⇒ 优先级：配置显式指定 > 客户端同源表 > shop_pay_asset。
            #   原实现"配置未命中就直接回退 coin"，会让 pay_type=24 的
            #   公会商城商品错误地扣银魂币（正确是 guild_active）。
            _pt = int(g.get('pay_type', 0))
            pt_map = self.cfg.get('shop_pay_type_asset') or {}
            pay = pt_map.get(str(_pt))
            if pay is None:
                pay = CODE_TO_ASSET.get(_pt)
            if pay is None:
                pay = self.cfg.get('shop_pay_asset', 'coin')
            pay = str(pay)
            unit = int(g.get('price', 0))
            total = unit * num
            # ★ 限购校验：原版 `limit_week` 就是权威上限（APK 里可取），
            #   不校验的话"界面显示限购、服务端却无限卖"，限购就只是装饰。
            _lim = int(g.get('limit_week', 0) or 0)
            _gid = int(g.get('id', bid))
            _bought0 = int((db_mall_bought(rid) or {}).get(_gid, 0))
            if _lim > 0 and _bought0 + num > _lim:
                pkt = pack_frame(12805, w_u8(0) +
                                 w_str('超过限购（限购 %d，已购 %d）' % (_lim, _bought0)) +
                                 w_u16(bid) + w_u16(num) + w_u32(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12805 SC_12805 code=0 (超过限购 goods_id=%d 限购=%d 已购=%d)'
                    % (_gid, _lim, _bought0))
                return
            have = int(st.get(pay, 0) or 0)
            if total > 0 and have < total:
                pkt = pack_frame(12805, w_u8(0) +
                                 w_str('%s 不足（需 %d，有 %d）' % (pay, total, have)) +
                                 w_u16(bid) + w_u16(num) + w_u32(total))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12805 SC_12805 code=0 (货币不足 %s %d/%d)' % (pay, have, total))
                return
            if total > 0:
                # ★ 同 12837：`have` 是**合并后**的有效值，必须用绝对值写入，
                #   否则 `roles.gold=1000` + `role_assets` 无 gold 行时
                #   增量写会得到 -50 而不是 950（实测踩过）。
                db_set_assets(rid, {pay: have - total})
            if db_bag_add(rid, item_bid, num):
                log('tcp.log', '  ** 购买成功 goods_id=%d item=%d x%d 扣 %s=%d'
                    % (bid, item_bid, num, pay, total))
            else:
                log('tcp.log', '  !! 购买：扣钱成功但入包失败 item=%d' % bid)
            # ★ 购买记录 → 供 12831 的 has_buy_num（goods_id 用客户端发来的 id）
            db_mall_bought_add(rid, int(g.get('id', bid)), num)
            # ★ 背包刷新：按客户端请求过的**每个** bag_code 各推一条 10500。
            #   （原实现只推 `_last_bag_code` 一个 ⇒ 页不对就不刷新。）
            pkt = pack_frame(12805, w_u8(1) + w_str('') + w_u16(bid) + w_u16(num) + w_u32(total))
            self.request.sendall(pkt)
            bag_push_frames(self, rid)
            self._send_12831()
            live_push(self.cfg, 'shop_buy')
            log('tcp.log', '  << 12805 SC_12805 code=1(TRUE) item=%d x%d price=%d (%d bytes)'
                % (bid, num, total, len(pkt)))
            return
        if cmd in (14001, 14002, 14003, 14004, 14005, 14006, 14007, 14008):
            # ★★★ R90：**阵型交互全链**（原先这 8 条一条都没实现 ⇒ 客户端点了没反应）
            #   真机证据：点阵型时发 `14003`×25 / `14005`×6，服务端**一句话都不回**
            #   ⇒ 界面卡在加载中（"伙伴列表空空如也 / 阵型书用不了"的表象）。
            #   各条 SC 的字段按 `protocol/fields.json` 逐个对齐；取值只用**同族已有约定**：
            #     flag=1 成功（14000/14009 同款）、tips=0 无提示编号、msg='' 无文案。
            _lev_f2 = int(role_state(self.cfg).get('lev') or 1)
            _best2 = 1
            for _ft2, _nl2 in _FORMATIONS:
                if _nl2 <= _lev_f2 and _ft2 > _best2:
                    _best2 = _ft2
            # ★ R91：**优先用玩家选中的阵型**（`14005` 落库的），没有才退到"最高可用档"
            _sel2 = db_form_get(role_state(self.cfg).get('rid', 1001))
            if _sel2 and 1 <= int(_sel2.get('f_type') or 0) <= 7:
                _best2 = int(_sel2['f_type'])
            _hs2 = db_hero_list(role_state(self.cfg).get('rid', 1001), self.cfg)[:5]

            def _pos_info():
                """`pos_info` / `info_list` 的公共结构（与 14000 同构）。"""
                _b = (w_u16(1) + w_u8(_best2) + w_u8(1) + w_u16(len(_hs2)))
                for _i2, _h2 in enumerate(_hs2, 1):
                    _b += w_u32(int(_h2.get('bid') or 0)) + w_u8(_i2)
                return _b + w_u16(0)          # member_pos_info 空表

            if cmd in (14001, 14002):
                _out = (w_u16(0) + w_str('') + w_u8(1) + _pos_info())
                _tag = 'pos_info=%d 位上阵' % len(_hs2)
            elif cmd == 14003:
                _out = w_u16(0) + w_str('') + w_u8(1)
                _tag = '选中阵型(type=%d)' % (body[1] if len(body) >= 2 else 0)
            elif cmd == 14004:
                # 阵型升级：回当前阵型与等级（f_lev 我们从 1 起，未实现升级消耗）
                _out = w_u16(0) + w_str('') + w_u8(_best2) + w_u8(1)
                _tag = '阵型升级应答 type=%d f_lev=1' % _best2
            elif cmd == 14005:
                # ★★★ R91：**记住玩家选的阵型**（原先只回成功、不落库 ⇒ `14000` 永远回最高档）。
                #   真机证据：点了 14003(07) → 14005(06) → 14005(02)，而 14000 三次都回 7。
                #   CS_14005{flag:u8, type:u8} ⇒ 取 body[1] 作为选中的 f_type。
                _sel = int(body[1]) if len(body) >= 2 else 0
                if 1 <= _sel <= 7:
                    db_form_set(role_state(self.cfg).get('rid', 1001), _sel, 1)
                _out = w_u16(0) + w_str('') + w_u8(1)
                _tag = '切换阵型 ⇒ type=%d' % _sel
            elif cmd in (14006, 14008):
                _out = w_u16(0) + w_str('')
                _tag = '应答(tips,msg)'
            else:  # 14007 助威
                _out = w_u8(1) + w_u16(0)     # flag=1 + cheer_hero 空表
                _tag = '助威位应答'
            self.request.sendall(pack_frame(cmd, _out))
            log('tcp.log', '  << %d SC_%d %s (%d bytes)' % (cmd, cmd, _tag, len(_out) + 6))
            return
        if cmd == 14009:
            # CS_14009{flag:uint8} → SC_14009{flag:uint8, cheer_hero:table(hero_bid:u32, pos:u8)}
            # 依据：form_ctrl.luac 的 RegisterProtocal(14009, …)；字段取自 protocol/manual.md。
            # ★ 该协议**没有** `D|Dsc*|` 未解出的动态子表 ⇒ 可安全编码（不猜）。
            flag = body[0] if len(body) >= 1 else 0
            pkt = pack_frame(14009, w_u8(flag) + w_u16(0))   # cheer_hero 空表
            self.request.sendall(pkt)
            log('tcp.log', '  << 14009 SC_14009 flag=%d cheer_hero=0 (%d bytes)'
                % (flag, len(pkt)))
            return
        # ★★ 2026-09-18 清理（体检发现）：此处原有一个**旧的 14100 handler**，它先 return
        #   从而**遮蔽**了后面 `if cmd in (14100, 14101)` 的完整实现（后者才带 14101 领取
        #   与 sign_rewards 发奖）。而旧版读的是 config 里**不存在**的键
        #   `signin_days` / `signin_is_get`（真实键是 `sign_days` / `sign_is_get`）
        #   ⇒ is_get 恒为 0 ⇒ 签完到界面仍显示"可签"。
        #   ⇒ 已删除该重复分支，统一交给后面的完整实现。
        if cmd == 10527:
            # CS_10527（空）→ SC_10527{state_list:table(lev:u8, time:u32, flag:u8)}
            # 依据：字段取自 protocol/manual.md（show_cmd 10527）；无 D|Dsc*| 子表 ⇒ 安全。
            st_list = self.cfg.get('state_list') or []
            out = w_u16(len(st_list))
            for stt in st_list:
                out += (w_u8(int(stt.get('lev', 0)) & 0xff) +
                        w_u32(int(stt.get('time', 0))) +
                        w_u8(int(stt.get('flag', 0)) & 0xff))
            pkt = pack_frame(10527, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10527 SC_10527 state_list=%d (%d bytes)'
                % (len(st_list), len(pkt)))
            return
        if cmd == 10589:
            # CS_10589（空）→ SC_10589{flyup_lev:u8, flyup_stage:u8, exp:u32, dan_cnt:u8}
            # 依据：字段取自 protocol/manual.md；全简单类型 ⇒ 安全。
            r = role_state(self.cfg)
            out = (w_u8(int(r.get('flyup_lev', 0)) & 0xff) +
                   w_u8(int(r.get('flyup_stage', 0)) & 0xff) +
                   w_u32(int(r.get('flyup_exp', 0))) +
                   w_u8(int(r.get('dan_cnt', 0)) & 0xff))
            pkt = pack_frame(10589, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10589 SC_10589 flyup_lev=%s stage=%s exp=%s dan=%s (%d bytes)'
                % (r.get('flyup_lev', 0), r.get('flyup_stage', 0),
                   r.get('flyup_exp', 0), r.get('dan_cnt', 0), len(pkt)))
            return
        if cmd == 10650:
            # CS_10650（空）→ SC_10650{talent_list:table(id:u16)}
            # 依据：字段取自 protocol/manual.md；无 D|Dsc*| 子表 ⇒ 安全。
            # ★ S2 项①：cfg 未显式配 talent_list 时，从 cfg/config_skill_talent.json
            #   惰性加载真实 talent_id（=行内 bid，105 个全量解锁）；见 load_talent_list()。
            tl = self.cfg.get('talent_list') or load_talent_list()
            out = w_u16(len(tl)) + b''.join(w_u16(int(t) & 0xffff) for t in tl)
            pkt = pack_frame(10650, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10650 SC_10650 talent_list=%d (%d bytes)'
                % (len(tl), len(pkt)))
            return
        if cmd == 13369:
            # CS_13369（空）→ SC_13369{black_list:table(rid:u32, srv_id:str, name:str,
            #   sex:u8, lev:u16, career:u16, power:u32, login_time:u32, face_id:u8,
            #   is_online:u8, group_id:u32, intimacy:u32, grid:u32, gsrv_id:str, guild_name:str)}
            # 依据：字段取自 protocol/manual.md；无 D|Dsc*| 子表 ⇒ 安全。
            # 目前没有黑名单数据源 ⇒ 如实回**空表**（不编造条目）。
            bl = self.cfg.get('black_list') or []
            out = w_u16(len(bl))
            for b in bl:
                out += (w_u32(int(b.get('rid', 0))) + w_str(b.get('srv_id', '')) +
                        w_str(b.get('name', '')) + w_u8(int(b.get('sex', 0)) & 0xff) +
                        w_u16(int(b.get('lev', 1))) + w_u16(int(b.get('career', 1))) +
                        w_u32(int(b.get('power', 0))) + w_u32(int(b.get('login_time', 0))) +
                        w_u8(int(b.get('face_id', 0)) & 0xff) +
                        w_u8(int(b.get('is_online', 0)) & 0xff) +
                        w_u32(int(b.get('group_id', 0))) +
                        w_u32(int(b.get('intimacy', 0))) + w_u32(int(b.get('grid', 0))) +
                        w_str(b.get('gsrv_id', '')) + w_str(b.get('guild_name', '')))
            pkt = pack_frame(13369, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 13369 SC_13369 black_list=%d (%d bytes)'
                % (len(bl), len(pkt)))
            return
# [P2B-migrated dispatch/handler.py]         if cmd == 10301:
            # CS_10301（空）→ 回 SC_10301 角色基础信息
#             pkt = pack_frame(10301, build_10301(role_state(self.cfg),
#                                                 self.cfg.get('skills', [])))
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 10301 SC_10301 role info (%d bytes)' % len(pkt))
#             return
        if cmd == 10922:
            # ★★★ R49 修复：活动提示弹窗刷屏 + 重复（"XX活动在…开启，玩家快去战个痛快吧！"）
            #   权威命令名（protocol/cmd_table.json）：
            #     10922 = **全服活动的活动状态**   10924 = 个人活动图标
            #     10923 = 全服活动的单个活动状态   10925 = 个人活动图标的单个活动状态
            #   ⇒ **10922 才是"全服活动状态"**，它的 id 空间是 `config_richang` 的**活动类**条目
            #     （101/107/108/111/112/…，与 10924 的 `config_function` id 空间 1..91 不同）。
            #   实测链路（本次真机，两步定性）：
            #     ① `SC_10924.act_list` 置空 ⇒ 弹窗消失（但活动图标也没了，见 shots/t2_*.png）
            #     ② 客户端 activity_ctrl.luac proto#37（bc=487）反汇编：
            #          if data.status == 1 then return end   -- BC 9..16
            #          self:pushByScene(1)                    -- 否则链式继续下一条 ⇒ 重复弹窗
            #        它遍历 `Config.Map[cur_scene_bid]`（当前场景的活动），
            #        逐条查**全服活动状态**；查不到 ⇒ status 为 nil ≠ 1 ⇒ 弹一次并继续。
            #   原实现恒回**空表** ⇒ 场景里每个活动都走"弹一次 + 继续" ⇒ 多弹窗且重复。
            #   修复：按 `config_richang` 的**活动类**条目回真实条目（status=1）。
            #   ★ 默认开启；`config.json: notice_act_ids=[]` 可关掉做对照实验。
            _acts = richang_activity_tasks()
            _all = [int(t.get('id')) & 0xffff for t in _acts]
            # ★ 注意（R49 实测，未完全取证）：`10922` 的**条目集合**会影响预告弹窗——
            #   回 9 条（预告集合）→ 无弹窗；回 19 条（全部活动类）→ **弹窗复现**。
            #   因此此处**只回预告集合**，不做"想当然地回全量"。
            #   若将来取证到 10922 的正确语义，应据此重写。
            _ids = self.cfg.get('notice_act_ids')
            if _ids is None:
                _ids = [101, 107, 108, 111, 112, 113, 115, 116, 118]
            _ids = [int(i) & 0xffff for i in _ids]
            if not self.cfg.get('disable_10922'):
                out = w_u16(len(_ids))
                for _i in _ids:
                    out += w_u16(_i) + w_u8(1) + w_u16(1) + w_u32(0)   # status=1, int_args=[0]
                pkt = pack_frame(10922, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 10922 SC_10922 act_list=%d (全服活动状态; 全量=%d) (%d bytes)'
                    % (len(_ids), len(_all), len(pkt)))
            else:
                pkt = pack_frame(10922, w_u16(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10922 SC_10922 act_list=0 (R49 实验: disable_10922)')
            return
        if cmd in (14700, 14701):
            # ★★ 幸运转盘（客户端 game/turntable/turntable_ctrl.luac注册 14700/14701，主动发 14701）
            #   14700 CS(空) -> SC{id:u32, lottery_list:table(id:u32, bid:u32, quantity:u32, bind:u8)}
            #   14701 CS(空) -> SC{id:u32, code:u8, msg:string}
            # ★ 用户报障“幸运转盘可点击但无法完成抽奖” ⇒ 14700/14701 原先无人应答
            # 依据：config_holiday_dial_reward_data.luac：gold_once=80(钻石/抽)、
            #   HolidayDialRewardList index→item_bid。
            rid = role_state(self.cfg).get('rid', 1001)
            if cmd == 14700:
                pl = self.cfg.get('turntable_pool') or []
                # 少保配置补全
                if not pl:
                    pl = [{'id': 1, 'bid': 28560, 'quantity': 1, 'bind': 0},
                          {'id': 2, 'bid': 28515, 'quantity': 1, 'bind': 0},
                          {'id': 3, 'bid': 28517, 'quantity': 1, 'bind': 0},
                          {'id': 4, 'bid': 28514, 'quantity': 1, 'bind': 0}]
                out = w_u32(int(self.cfg.get('turntable_id', 1))) + w_u16(len(pl))
                for it in pl:
                    out += (w_u32(int(it.get('id', 0))) + w_u32(int(it.get('bid', 0))) +
                            w_u32(int(it.get('quantity', 1))) + w_u8(int(it.get('bind', 0))))
                pkt = pack_frame(14700, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 14700 SC_14700 pool=%d (%d bytes)' % (len(pl), len(pkt)))
                return
            # 14701 抽奖：扣钻石 → 发一件奖池物品
            cost = int(self.cfg.get('turntable_gold_once', 80))
            gold = int(db_get_assets(rid).get('gold', 0))
            if gold < cost:
                self.request.sendall(pack_frame(14701, w_u32(0) + w_u8(0) + w_str('\u94bb\u77f3\u4e0d\u8db3')))
                log('tcp.log', '  << 14701 SC_14701 code=0 (钻石不足, gold=%d)' % gold)
                return
            db_add_assets(rid, {'gold': -cost})   # 没有 db_sub_assets；抽费用负数减
            pl = self.cfg.get('turntable_pool') or [
                {'bid': 28560, 'quantity': 1}, {'bid': 28515, 'quantity': 1},
                {'bid': 28514, 'quantity': 1}, {'bid': 28517, 'quantity': 1}]
            import random as _r
            w = _r.choice(pl)
            bid = int(w.get('bid', 28560)); qty = int(w.get('quantity', 1))
            if is_valid_item(bid):
                db_bag_add(rid, bid, qty)
                try:
                    items = db_bag_get(rid, BAG_MAIN)
                    self.request.sendall(pack_frame(10500, w_u8(BAG_MAIN) + build_bag_items(items)))
                except Exception:
                    pass
                live_push(self.cfg, 'turntable')
            pkt = pack_frame(14701, w_u32(0) + w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 14701 转盘抽奖 -%d钻石 → +%d x%d' % (cost, bid, qty))
            return
        if cmd == 20100:
            # ★★ 变强/综合战力面板（SC_20100）
            #   客户端 activity_ctrl handle20100 → AdvanceEvent:Fire(Update_Data) → 变强面板
            #   字段：{power:table(code:u8, val:u32), promote:table(code:u8, val:D|Dsc20100val|)}
            #   ★ "promote"含未解子表 D|Dsc20100val| ⇒ 按纪律置空（不猜编码）
            #   ★ "power"是战力分量列表（数组）：每项 {code:u8, val:u32}，
            #     code 的语义**未匹证**（尚无官方要求），用有效列表。
            #   20100所以心“综合战力”：里面包含总战力。
            # ★★ 2026-09-18 清理：此处原有一个 `if cfg.get('disable_20100'): pass` 的
            #   **空操作**（写了 if 但什么都不做）⇒ 已删除。若将来确需关闭 20100，
            #   应在分发处 return，而不是在函数体里 pass。
            #   ★ R49 实证（`advance_new_panel.luac` proto#20，BC 17..63）：
            #       power[1].code==1 → 「综合战力」   = power[1].val
            #       power[2].code==2 → 「N级推荐战力」= power[2].val   ← 原实现恒 0
            #       power[3].code==3 → 评分图标      = getPingfen(power[3].val)
            #     ⇒ 面板上的「70级推荐战力：0」就来自 #2 槽位恒 0。
            #   ⚠ **推荐战力没有可得的原版数据源**（如实记录）：
            #     `Config.RoleAttr`（200 级）只有 exp_total/exp_max/attr_point/sinew_add/sinew_max，
            #     **不含任何战斗属性**（见上方 LEVEL_ATTR_GROWTH 注释与 export_level_table.py）
            #     ⇒ 逐级属性成长/推荐战力曲线**不在客户端配置里**。
            #     按红线"不编造数据"：#2 / #3 槽位**保持 0**，语义注释写清，不塞占位数值。
            power_total = role_power(self.cfg)
            comps = [
                (1, power_total),           # 综合战力
                (2, 0),                     # 推荐战力（无可得数据源 ⇒ 0，待取证）
                (3, 0),                     # 评分（同上）
            ]
            # 表示形式：table(code, val)
            out = w_u16(len(comps))
            for code, val in comps:
                out += w_u8(code) + w_u32(val & 0xffffffff)
            # ★ R49：`promote` 由空表改为**真实提升项列表**（修「变强面板右侧空白」）
            #   结构：table{code:u8, val:table{code:u8, val:u32}}；客户端只读 `code`
            #   并按 `Config.Promote[code].display_lev <= roleVo.lev` 过滤渲染。
            _lev = int(role_state(self.cfg).get('lev') or 1)
            _prom = [t for t in promote_tips()
                     if int(t.get('display_lev') or 0) <= _lev]
            out += w_u16(len(_prom))
            for t in _prom:
                out += w_u8(int(t.get('code') or 0) & 0xff) + w_u16(0)   # val = 空子表
            pkt = pack_frame(20100, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 20100 SC_20100 power_total=%d comps=%d promote=%d (%d bytes)'
                % (power_total, len(comps), len(_prom), len(pkt)))
            return
# [P2B-migrated dispatch/handler.py]         if cmd == 10306:
            # ★★ round45：角色属性 + 战力同步小包（SC_10306）
            #   CS空 → SC{attr表(24项), mspd:u16, power:u32}
            #   客户端发空消息请求"同步我的属性"；这是写 RoleVo.power 的那条消息。
            #   ★ HANDOVER P0-1：综合战力面板读 RoleVo.power[1].val，
            #     此前 10306 完全没实现 ⇒ 从无消息写入 ⇒ 面板一直空。
            #   ★ R43 订正：attr 表结构与 10304 **并不相同** ——
            #     `atk_abs/def_abs/reduce/hurt` 在 10306 里是 **u16**（权威 spec）。
            #     原先复用 10304 的切分 ⇒ 应答多 8 字节、mspd/power 被读错。
#             st = role_state(self.cfg)
#             ad = role_attr_dict(self.cfg)
#             pw = role_power(self.cfg)
#             out = attr_table_10306(ad)                        # ★ 专用编码器
#             out += w_u16(int(st.get('mspd', 0)) & 0xffff)    # mspd:uint16
#             out += w_u32(pw & 0xffffffff)                    # power:uint32 ★
#             self.request.sendall(pack_frame(10306, out))
#             log('tcp.log', '  << 10306 attr=24 mspd=%d power=%d (%d bytes)'
#                 % (int(st.get('mspd', 0)), pw, len(out)))
#             return
# [P2B-migrated dispatch/handler.py]         if cmd == 10304:
            # ★★ 角色属性 + 战力大包（SC_10304）
            #   客户端 role_ctrl proto[18] GetPrototype 10304 主动请求。
            #   字段顺序拉自 protocol/manual.md（均无 D|Dsc*| ⇒ 安全）。
            #   ★ 25 项 attr：strength/intellect/armor/constiution/atk_s/atk_p/def_s/def_p/
            #     hp_max/atk_speed/hit/dodge/crit/tenacity/red_def_s/red_def_p/atk_abs/def_abs/
            #     reduce/hurt/hit_rate_show/dodge_rate_show/crit_rate_show/tenacity_rate_show
            #     + power(战力)。
            #   根据客户端 RoleVo：实地实务当只带“战力”未传完战力按置。
#             rid = role_state(self.cfg).get('rid', 1001)
            # ★ round40：抽成 role_attr_dict / role_power（12901 战力榜复用同一算法）
#             default_attr = role_attr_dict(self.cfg)
#             power = role_power(self.cfg)
#             st = role_state(self.cfg)
#             out = (w_u32(st.get('rid', rid)) + w_str(st.get('srv_id', '1')) +
#                    w_str(st.get('name', 'DSH')) + w_u16(st.get('lev', 160)) +
#                    w_u8(st.get('is_vip', 0)) + w_u8(st.get('vip_lev', 0)) +
#                    w_u8(st.get('sex', 0)) + w_u16(st.get('career', 1)) +
#                    w_u8(st.get('volume', 200)) + w_u8(st.get('store_volume', 0)) +
#                    w_u8(st.get('store_partner_volume', 0)) +
#                    w_u8(st.get('volume_open', 200)) +
#                    w_u8(st.get('store_volume_open', 0)) +
#                    w_u8(st.get('store_partner_volume_open', 0)) +
#                    w_u16(st.get('attr_point', 0)) +
#                    w_u16(0))  # skill_list 空
#             out += w_u32(power)  # ★ 战力
#             out += (w_u32(st.get('exp', 0)) + w_u32(st.get('gold', 0)) +
#                     w_u32(st.get('coin', 0)) + w_u32(st.get('gold_acc', 0)) +
#                     w_u32(st.get('sinew', 0)) + w_u32(st.get('experience', 0)) +
#                     w_u32(st.get('coupon', 0)) + w_u32(st.get('vitality', 0)) +
#                     w_u32(st.get('guild_contrib', 0)) + w_u32(st.get('practice_exp', 0)) +
#                     w_u32(st.get('tower_cent', 0)) + w_u32(st.get('arena_cent', 0)))
            # ★ attr 是**表**（AutoConstruct sc/10304 权威规格）：
            #   attr__T__strength@H##intellect@H##armor@H##constiution@H##atk_s@I##…
            #           ##tenacity_rate_show@I
            #   ⇒ u16 计数 + 1 条（前 4 项 u16 + 后 20 项 u32 = 88 字节）。
            #   ⚠ 旧实现按 24 个**平铺 u32**（96 字节）写 ⇒ 客户端把首 2 字节当表计数
            #     （得 0）、其后所有字段整体错位；且尾部 mspd/animate_res/vip_exp/
            #     jiebai_title/jiebai_lev **完全缺失**。
            #   由真机流量回放审计 tools/replay_captures.py 发现并修正。
            #   ★ R43：改走 `attr_table_10304()`（与 10306 各自的编码器，
            #     避免"同族就共用切分"这一反复踩到的错误）。
#             out += attr_table_10304(default_attr)             # attr 表：1 条
#             out += w_u16(int(st.get('mspd', 0)) & 0xffff)     # mspd:uint16
#             out += w_u16(0)                                   # animate_res 空表
#             out += w_u32(int(st.get('vip_exp', 0)) & 0xffffffff)
#             out += w_str(str(st.get('jiebai_title', '')))     # jiebai_title:string
#             out += w_u8(int(st.get('jiebai_lev', 0)) & 0xff)  # jiebai_lev:uint8
#             pkt = pack_frame(10304, out)
#             self.request.sendall(pkt)
#             log('tcp.log', '  << 10304 SC_10304 power=%d attr=24+1 (%d bytes)' % (power, len(pkt)))
#             return
        if cmd == 10300:
            # CSRoleInit（空）：客户端说"我初始化完了"
            log('tcp.log', '  .. 10300 CSRoleInit received')
            # ★ 修法候选（纯服务端，不改客户端、不改协议）：
            #   实测 scene_model proto[68] sceneStart → SceneView:createMap()
            #   在客户端刚进场景、资源尚未就绪时调用会半途而废，
            #   导致 nowPicTile 不设置、createMap 的闭包回调（setLoadState(true)）不触发，
            #   于是 scene_controller.model:isLoadState() 恒为 false → move() 被门禁挡住。
            #   而实测在场景稳定后**再调一次 createMap 就能成功**
            #   （nowPicTile=table、isLoadState=true、无报错）。
            #   由于 sceneStart 每次收到 10200 都会重新走一遍，
            #   这里趁"客户端初始化完毕"再补推一次 10200，让它在资源就绪后重跑。
            #   —— 先验证效果，再谈是否保留。
            if self.cfg.get('repush_10200_on_init', True):
                # ★ 2026-10-16 修复：原为 `spawn.bid`（恒 10001）⇒ 客户端每发一次
                #   10300（场景初始化完毕）就被**拽回史莱克城**，把 GM setscene /
                #   挂机图切图的效果当场撤销（实测 10204 上报回 scene=10001 的元凶）。
                #   改为复用 `_current_bid(self)`：它优先取 `_last_enter`（服务端刚
                #   放进哪个图就是哪个图），无记录才回退 spawn 配置。
                bid = _current_bid(self) or self.cfg.get('spawn', {}).get('bid', 1)
                self._send_10200(bid)
                log('tcp.log', '  << 10200 re-push after 10300 (client ready)')
            # ★★ R61 实验变体（config: guaji_push_15402_on_enter，默认关）：
            #   与"15400 之后推"做对照 —— R48 记录的原始观察是
            #   「**登录进场景后立刻**发出 `CS_15402{mission_bid=10010}`」，
            #   说明原版很可能是在**场景进入**这一刻由服务端给 `SC_15402`。
            #   `ghost_mon` proto#3 里还有 `'map_bid'/'getSceneId'/'SceneModel'` ⇒
            #   `createMon` 很可能**要求玩家已在对应场景**，这与"进场景时推"吻合。
            if self.cfg.get('guaji_push_15402_on_enter'):
                _rid2 = role_state(self.cfg).get('rid', 1001)
                _mb2 = int(self.cfg.get('guaji_mission_bid') or 10010)
                _lev3 = int(role_state(self.cfg).get('lev', 1))
                _spot3 = guaji_spot_for_lev(_lev3) or {}
                _map3 = int(_spot3.get('map_bid') or 0)
                _x3, _y3 = map_def_xy(_map3)
                # ★★ R70：**把"送进挂机图"也搬到这里**，让整条链在**登录时就跑完**。
                #   动机：`4019` 那一下点击的命中率只有 ~40%（`adb input tap` 的坐标/时序都不稳），
                #   导致每次验证都要反复试；而链路本身与"点没点按钮"无关。
                #   开关 `guaji_auto_start`（默认 false）⇒ 打开后**零点击**即可复现整条链：
                #     10300 → 10200(10005) + 10201 → (delay) → 15402 → 客户端 createMon
                if self.cfg.get('guaji_auto_start') and _map3:
                    try:
                        # ★★ R72：**不要再自己推一次 10201**！
                        #   `_send_10200()` 内部已经推过 `10201`，而且它用的是**修正过坐标的
                        #   role**（切图时已改成目标图默认点）。这里原先又推了一次、用的是
                        #   `role_with_saved_pos()`（**旧场景坐标**）⇒ **覆盖**掉正确的那次，
                        #   客户端于是把主角摆在别的图的坐标上 ⇒ **主角模型建不出来**
                        #   （用户报障"到了乾坤日月谷没有主角模型"的元凶）。
                        #   实测日志里 `10201` 连推两次、第二次是 (91,56) 而 10200 说 (10,58)。
                        self._send_10200(_map3)
                        log('tcp.log', '  << 10200/10201 自动送进挂机图 bid=%d（R70 guaji_auto_start）'
                            % _map3)
                        time.sleep(float(self.cfg.get('guaji_enter_scene_delay') or 3.0))
                    except Exception as e:
                        log('tcp.log', '  !! R70 自动送场景失败: %r' % (e,))
                if self.cfg.get('guaji_15402_use_role_pos', True):
                    _rp2 = role_with_saved_pos(self.cfg)
                    _x3 = int(_rp2.get('x') or _x3)
                    _y3 = int(_rp2.get('y') or _y3)
                # ★★★ R71：**顺序修正（探针实测）**
                #   探针证据（R70 零点击链）：`15402` 在 `12400` **之前**推出去时，
                #     `ghcreate mon_bid=0 … hasMon_false / done_mon_id_nil`
                #   —— 因为 `mon_bid = mis.mis_target` 来自**客户端本地任务数据**，
                #   而那条任务正是 `SC_12400` 刚推给它的。**先推 15402 ⇒ 客户端还没这条任务 ⇒ mon_bid=0**。
                #   （R65/R66 用"点 4019"触发时之所以拿到 10105，是因为那时 12400 早就到了。）
                #   ⇒ 自动链改为**延后到 12400 落地之后**（复用 12s 补推机制）再推 15402。
                if self.cfg.get('guaji_auto_start'):
                    self._guaji_15402_at = time.time() + 14.0
                    log('tcp.log', '  .. 15402 已排程（+14s，等 12400 落地后再推）')
                else:
                    _le2 = getattr(self, '_last_enter', None)
                    if _le2 and int(_le2[0]) == int(_map3):
                        _x3, _y3 = int(_le2[1]), int(_le2[2])
                    self.request.sendall(pack_frame(
                        15402, w_u32(_mb2) + w_u32(_map3) + w_u32(_x3) + w_u32(_y3)))
                    # ★ R72：日志必须与事实一致 —— 原先把这条 log 写在 if/else **外面**，
                    #   于是走 auto_start（只排程、并未发送）时也照打一行"已推 15402"，
                    #   实际客户端没收到（实测：17:44:31 有一条 (91,56) 的假日志，
                    #   而探针直到 17:44:47 才出现 ghcreate ⇒ 只有一次真推送）。
                    db_guaji_update(_rid2, mission_bid=_mb2)
                    log('tcp.log', '  << 15402 进场景主动推 mission_bid=%d map_bid=%d (%d,%d) '
                                   '（R61/R70）' % (_mb2, _map3, _x3, _y3))
            # ★ 任务列表：客户端不会主动请求 12400，改为主动推送
            #   Phase 5J：这里也必须走 mission_rows()（数据库优先 + 过滤已提交），
            #   否则已提交的任务会被再次推给客户端、引发重复提交。
            #   （自查发现的第二处遗漏，已修）
            _ms = mission_rows(self.cfg, role_state(self.cfg).get('rid', 1001))
            if _ms:
                pkt = pack_frame(12400, build_12400(_ms))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12400 SC_12400 mission_list=%d (%d bytes)'
                    % (len(_ms), len(pkt)))
            else:
                log('tcp.log', '  << 12400 skipped (no active mission)')
            # ★★ 补推任务列表（**本轮找到的真正根因的修法**）
            #   证据链（`analysis/1.4.9/task/npc_quest_flow.md`）：
            #     `mission_ctrl.luac` proto#31 (`handle12400`) 会
            #       遍历 mission_list → createMis → Fire(NpcContants.ADD_MISSION, commitNpc, vo)
            #     而 `NpcContants.ADD_MISSION` 的监听者是
            #        `npc_ctrl.luac` proto#16 `registerEvents` → proto#5 `NpcCtrl:addNpc`
            #     —— 但 `NpcCtrl` 是**惰性实例化**（首次点 NPC 时才 New），
            #        所以在 10300 这一刻它**还没绑定监听**，事件被丢弃
            #        ⇒ `NpcMissionManager.npc_list` 一直是空的
            #        ⇒ NPC 对话拿不到任务 ⇒ 走 `openDefault`（只有闲聊）
            #   修法：等客户端进入稳定状态后**再补推一次 12400**，
            #        让 `handle12400` 重新 Fire 一遍事件；此时监听者已在。
            self._mis_repush_at = time.time() + 12.0
            log('tcp.log', '  .. 12400 补推已排程（+12s，等 NpcCtrl 就绪）')
            # ★ S1 第一分片：登录风暴收尾补推（F1 战力归零 + 日常活力）
            #   C2.2/C2.3 诊断：10301 重建 RoleVo 后 power=0，面板自动弹出定格 0；
            #   日常 tab 从不发 CS_13781/13786。修法：心跳驱动延迟补推。
            self._login_repush_at = time.time() + 5.0
            log('tcp.log', '  .. S1 风暴收尾补推已排程（+5s，10303/10306/13781/13786）')
            return

        if cmd == 10397:
            # CS_10397{status:uint8}：客户端汇报前后台状态，手册无对应 SC，仅记录
            log('tcp.log', '  .. 10397 OntoBack status=%s'
                % (body[0] if body else '?'))
            return

        # ===================================================================
        # ★ Phase D：战斗最小垂直闭环
        #
        # 协议依据（全部 1.4.9 字节码，见 server/battle.py 头注与
        # analysis/1.4.9/battle/battle_protocol_matrix.md）：
        #   CS_20002{mon_id}  对怪物发起战斗
        #   SC_20002{code,msg} 应答（scFightStart: code~=TRUE → message(msg)）
        #   SC_20010{...}      ★ 真正的"进战斗"（scFightData → Battle:playEnterEffect）
        #   SC_20012 / 20013   小回合：技能播放 + 伤害
        #   CS_20014           客户端动画播放完成 → 服务端推进下一回合
        #   SC_20020{result}   胜负
        #   SC_20023{...}      结算明细
        # ===================================================================
        if cmd == 20002:
            # CS_20002 的 body 实测是 `mon_id:int32` + 4 字节**尾部脏数据**
            #   （客户端定长缓冲区残留），所以只读前 4 字节。
            mon_id = (struct.unpack_from('>i', body, 0)[0]
                      if len(body) >= 4 else 0)
            log('tcp.log', '  >> CS_20002 fight monster mon_id=%d (body=%d bytes)'
                % (mon_id, len(body)))
            # ★★★ R77：**在"候选场景"里找这只怪**，而不是死盯某一个场景。
            #   原实现写死 `spawn.bid`（10001）⇒ 玩家在乾坤日月谷(10005) 点 10105 时，
            #   服务端拿 10001 的怪表（只有 20001 戴浩）去比对 ⇒ 回
            #   `no such monster 10105`（用户报障原文）。
            #   候选顺序：本连接最后进过的图（`_last_enter`，R72 设的）
            #           → 存档场景 → 出生场景 → 该等级段的挂机图。
            #   为什么用"候选"而不是"当前场景"：客户端会用**它自己的** scene_id
            #   上报位置，把 `roles.scene_id` 写回旧值（R77 实测），所以任何单一来源
            #   都不可靠；而"玩家被我们送进过的图里能找到这只怪"就是**正确语义**。
            _le8 = getattr(self, '_last_enter', None)
            cand = []
            for c in (int(_le8[0]) if _le8 else 0,
                      int(role_state(self.cfg).get('scene_id') or 0),
                      int((self.cfg.get('spawn') or {}).get('bid') or 0),
                      int((guaji_spot_for_lev(
                          int(role_state(self.cfg).get('lev') or 1)) or {}).get('map_bid') or 0)):
                if c and c not in cand:
                    cand.append(c)
            _npcs, _mons, sp_bid = [], [], (cand[0] if cand else 10001)
            for c in cand:
                _n8, _m8 = scene_quest_extras(self.cfg, c)
                if any(int(m.get('id', 0)) == mon_id for m in _m8):
                    _npcs, _mons, sp_bid = _n8, _m8, c
                    break
            else:
                _npcs, _mons = scene_quest_extras(self.cfg, sp_bid)
            if len(cand) > 1:
                log('tcp.log', '  .. 20002 候选场景=%r 选中=%d' % (cand, sp_bid))
            mon = None
            for m in _mons:
                if int(m.get('id', 0)) == mon_id:
                    mon = m
                    break
            if mon is None:
                # ★★ C3.3-E：塔挑战会话授权放行。
                #   13037 已做服务端校验（等级/层数进度）并在本连接挂 dung_challenge；
                #   塔 boss（18200+ceng）配置在塔场景 21000+，本连接尚未真实传送，
                #   因此场景怪表查不到。若 mon_id == 当前挑战层 boss，构造 boss mon 放行，
                #   战斗仍走同一套 on_20002/_battle_settle 权威判定。
                _dc2 = getattr(self, 'dung_challenge', None)
                if _dc2 and int(mon_id) == int(_dc2.get('boss') or 0):
                    _md2 = mon_def(mon_id)
                    mon = {'id': mon_id, 'bid': mon_id,
                           'name': _md2.get('name') or ('镇魂塔boss%d' % mon_id),
                           'res_id': _md2.get('res_id') or ''}
                    try:
                        sp_bid = int((tower_floor_hash(_dc2.get('ceng')) or {}).get('map_bid') or 21000)
                    except Exception:
                        sp_bid = 21000
                    log('tcp.log', '  .. 20002 塔挑战授权放行 boss=%d -> scene=%s'
                        % (mon_id, sp_bid))
            if mon is None:
                # 目标不在场景里：回 code=0(非 TRUE) + msg（客户端会 message(msg)）
                pkt = pack_frame(20002, w_u8(0) + w_str('no such monster %d' % mon_id))
                self.request.sendall(pkt)
                log('tcp.log', '  << 20002 SC_20002 code=0 (mon %d 不在场景, 场景怪=%r)'
                    % (mon_id, [m.get('id') for m in _mons]))
                return
            # 通过校验 → 建战斗
            self.battle_mon = mon
            # ★ C3.2-C I2：记录战斗发生场景（CS_20002 选中的 sp_bid），
            #   供战斗结算时给 kill_scene_mon 条件推进用（target=场景号）。
            try:
                self.battle_scene = int(sp_bid or 0)
            except Exception:
                self.battle_scene = 0
            self.battle = make_battle(self.cfg, mon)
            self._battle_settled = False
            # ★ C3.3：每场战斗生成唯一结算引用（kill:mon_bid:rid:<毫秒时间戳>）。
            #   目的：(a) 每次正常击杀独立结算（10 只同型怪=10 次合法发奖）；
            #         (b) 同一战斗实例的异步重入/重放被 reward_log PK 挡住（不重复发奖）。
            #   旧键 kill:<mon_bid>:<rid> 把"同型怪第二次击杀"的 coin 也挡了，
            #   且 exp/掉落根本不在幂等门内 —— C3.3 统一修。
            try:
                _rid_now = int(role_state(self.cfg).get('rid', 1001))
            except Exception:
                _rid_now = 1001
            self.battle_settle_ref = 'kill:%d:%d:%d' % (
                int(mon_id), _rid_now, int(time.time() * 1000))
            # ① SC_20002 应答：scFightStart 的判定是 `code ~= TRUE → message(msg)`，
            #    所以成功必须回 code=1(TRUE == 1，见 common_define.luac proto[7])。
            pkt = pack_frame(20002, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 20002 SC_20002 code=1(TRUE) mon=%d bid=%s name=%s'
                % (mon_id, mon.get('bid'), mon.get('name')))
            # ② ★ SC_20010 战斗初始化数据 —— 这才是"真正进战斗"的那一条
            #    依据：battle_ctrl.luac proto#10 scFightData 收到它后调用
            #          Battle:playEnterEffect(data)；SC_20002 成功时什么都不做。
            if self.battle is not None:
                body = self.battle.build_20010()
                self.request.sendall(pack_frame(20010, body))
                log('tcp.log', '  << 20010 SC_20010 battle init fighters=2 '
                               'mon_hp=%d role_hp=%d (%d bytes)'
                    % (self.battle.mon_f.hp, self.battle.role_f.hp,
                       len(body) + 6))
                # ★ 实测：客户端**不会**主动发 CS_20011（见 _battle_kick 头注），
                #   所以 SC_20010 之后必须由服务端主动推第一回合。
                #   给 3 秒让客户端把战斗场景建起来，再推。
                self._battle_round_sent = 0
                self._battle_timer(3.0, lambda: self._battle_kick(first=True))
            return

        if cmd == 10509:
            # CS_10509{bag_code:u8} → SC_10509{code:u8, msg:string}
            # 依据：`tools/show_cmd.py 10509`（无 D|Dsc*| 未解子表）；
            #   客户端 backpack_ctrl bc#37 → handle_10509（sender_10509 形参 bag_code）。
            # 语义「整理指定背包」⇒ 把 pos 压紧为 1..N，并把**新位置**用 SC_10508 推给客户端。
            # ★★ 2026-10-17 修（用户报障"整理刷新功能缺失"）：
            #   原来推的是 `bag_push_frames()`（= **SC_10500 增量添加**）—— 它只往上加，
            #   **不会告诉客户端"位置变了"** ⇒ 界面上顺序永远不变（看着像"整理没用"）。
            #   文档 §8.3：客户端接受的服务端推送是 10501/10503/**10508**/10510/10543，
            #   而**主动推 SC_10502 会被忽略**（只在客户端自己发 CS_10502 后才处理）。
            _bc = body[0] if body else BAG_MAIN
            _rid = role_state(self.cfg).get('rid', 1001)
            _pairs = db_bag_repack(_rid, BAG_MAIN)
            push_10508(self, _pairs)
            push_10510(self, _rid, _bc)
            pkt = pack_frame(10509, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10509 SC_10509 code=1(TRUE) 整理完成 bag_code=%d 位置改动 %d 件'
                % (_bc, len(_pairs)))
            return
        if cmd == 10557:
            # CS_10557{bag_code:u8, args:table(id:u32)} → SC_10557{code:u8, msg:string}
            # 依据：`tools/show_cmd.py 10557`；客户端 backpack_ctrl bc#132 → hander_10557。
            # 语义「删除物品」⇒ 按 item_id 真删，再推 10500 + 回 code=1。
            _bc = body[0] if body else BAG_MAIN
            _rid = role_state(self.cfg).get('rid', 1001)
            _ids = []
            if len(body) >= 3:
                _cnt = struct.unpack_from('>H', body, 1)[0]
                _off = 3
                for _ in range(_cnt):
                    if _off + 4 > len(body):
                        break
                    _ids.append(struct.unpack_from('>I', body, _off)[0])
                    _off += 4
            if not _ids:
                pkt = pack_frame(10557, w_u8(0) + w_str('没有要删除的物品'))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10557 SC_10557 code=0（args 为空/解析不到）')
                return
            gone = db_bag_delete(_rid, _ids, BAG_MAIN)
            # ★★ 2026-10-17 修（用户报障"空格显示 / 刷新不出来"）：
            #   ① 删除后**压紧 pos**（否则界面留空洞格子）；
            #   ② 用 **SC_10503（删除通知）** 告诉客户端哪些物品没了 —— 这是文档 §8.3
            #      列出的"服务端主动推送"型消息；推 10500（增量添加）**永远不会移除**旧行，
            #      推 10502 会被客户端忽略（只在它自己发 CS_10502 后处理）。
            #   ③ 再用 **SC_10508** 把压紧后的新位置发下去。
            _pairs = db_bag_repack(_rid, BAG_MAIN)
            push_10503(self, gone)
            push_10508(self, _pairs)
            push_10510(self, _rid, _bc)
            pkt = pack_frame(10557, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10557 SC_10557 code=1(TRUE) 删除 bag_code=%d 请求%s 实删%s'
                % (_bc, _ids, gone))
            return
        if cmd == 10511:
            # CS_10511{bag_item_id:u32, eqm_item_id:u32, hero_bid:u32}
            #   \u2192 SC_10511{code:u8, msg:string, is_auto:u8, bag_item_id:u32,
            #                    eqm_item_id:u32, eqm_new_pos:u8, hero_bid:u32}
            # \u4f9d\u636e\uff1aprotocol/manual.md + cmd_resolve_105.luac\uff08\u65e0 D|Dsc*| \u5b50\u8868 \u21d2 \u5b89\u5168\uff09\u3002
            # \u2605 \u7a7f\u6234\u88c5\u5907\uff1a\u628a\u80cc\u5305\u91cc\u7684 bag_item_id \u79fb\u5230\u88c5\u5907\u69fd\uff1b
            #   \u82e5\u8be5\u69fd\u539f\u6709\u88c5\u5907\uff08eqm_item_id != 0\uff09\u5219**\u6362\u4e0b\u6765\u653e\u56de\u80cc\u5305**\u3002
            # \u26a0 \u88c5\u5907\u69fd\u4f4d\u7f16\u53f7\u4e0e\u5c5e\u6027\u52a0\u6210\u672a\u5b9e\u73b0\uff08\u65e0\u53d6\u8bc1\uff09\u21d2 `eqm_new_pos` \u56de 0\uff0c\u4e0d\u7f16\u9020\u3002
            bag_item_id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            eqm_item_id = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
            hero_bid = struct.unpack_from('>I', body, 8)[0] if len(body) >= 12 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            row = db_bag_get_one(rid, bag_item_id)
            if row is None:
                pkt = pack_frame(10511, w_u8(0) + w_str('no such item %d' % bag_item_id) +
                                 w_u8(0) + w_u32(bag_item_id) + w_u32(eqm_item_id) +
                                 w_u8(0) + w_u32(hero_bid))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10511 SC_10511 code=0 (bag_item_id=%d \u4e0d\u5b58\u5728)'
                    % bag_item_id)
                return
            bid = int(row.get('bid') or 0)
            # ★★ 2026-10-17 修（**丢物品**）：原顺序是"①先从背包删掉 → ②再校验是不是装备"，
            #   于是**被拒的非装备（礼盒等）已经被删掉、直接人间蒸发**。
            #   四系统自检实测：给背包发 `福利礼盒 30800` → 10511 回 code=0（拒绝正确），
            #   但背包里**也找不到了**（DB 里那一行没了）。
            #   ⇒ 现在改为**先校验、后动数据**：slot 判定通过之后才把物品从背包取走。
            # ① 原装备（若有）放回背包
            # ★ 2026-10-17 修（两处）：
            #   ① 原来写 `slot = equip_slot_for(...) if eqm_item_id == 0 else None` ——
            #      **换装（eqm_item_id != 0）时 slot 恒为 None**，被下面"非装备 ⇒ 拒绝"
            #      提前 return ⇒ \u300c\u6362\u88c5\u6c38\u8fdc\u62a5\u300c\u8be5\u7269\u54c1\u4e0d\u662f\u88c5\u5907\u300d\u300d\uff0c
            #      \u540e\u9762\u90a3\u6574\u6bb5\u6362\u88c5\u903b\u8f91\u6c38\u8fdc\u8d70\u4e0d\u5230\u3002
            #      正确：**新物品的槽位**与是否换装无关，一律按新物品算。
            slot = equip_slot_for(rid, bid, self.cfg)
            if slot is None:
                # ★ 非装备物品（配了 equip_type_slot 但 type 不在内）⇒ **拒绝**，
                #   避免像“礼包占了武器位”那样的问题。
                pkt = pack_frame(10511, w_u8(0) +
                                 w_str('\u8be5\u7269\u54c1\u4e0d\u662f\u88c5\u5907\uff0c\u4e0d\u80fd\u7a7f\u6234') +
                                 w_u8(0) + w_u32(bag_item_id) + w_u32(eqm_item_id) +
                                 w_u8(0) + w_u32(hero_bid))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10511 SC_10511 code=0 (bid=%d type=%s \u975e\u88c5\u5907\uff0c\u62d2\u7edd)'
                    % (bid, item_type_of(bid)))
                return
            # ★ 校验通过后才**真正从背包取走**（见上方说明：放在校验之前会吞掉被拒物品）
            db_bag_delete(rid, [bag_item_id])
            if eqm_item_id != 0:
                # \u5148\u627e\u51fa eqm_item_id \u5728\u54ea\u4e2a\u69fd
                # \u2605 2026-10-17\uff1a\u8fd9\u91cc**\u4e0d\u80fd\u8986\u76d6 `slot`** \u2014\u2014 `slot` \u662f\u65b0\u7269\u54c1\u8be5\u8fdb\u7684\u69fd\uff0c
                #   \u65e7\u88c5\u5907\u53ef\u80fd\u5728\u53e6\u4e00\u4e2a\u69fd\uff08\u7c7b\u578b\u4e0d\u540c\uff09\uff1b\u628a\u65b0\u7269\u54c1\u585e\u8fdb\u65e7\u69fd\u4f1a\u9519\u4f4d\u3002
                _old_slot = None
                for e in db_equip_all(rid):
                    if int(e['item_id']) == eqm_item_id:
                        _old_slot = int(e['slot'])
                        break
                if _old_slot is None:
                    _old_slot = slot
                old = db_equip_take(rid, _old_slot)
                if old:
                    db_bag_add(rid, int(old['bid']), 1)
                    log('tcp.log', '  .. 10511 \u6362\u4e0b\u65e7\u88c5\u5907 item_id=%d bid=%d \u21d2 \u56de\u80cc\u5305'
                        % (old['item_id'], old['bid']))
            # \u2605 2026-10-17\uff1a\u76ee\u6807\u69fd\u4f4d\u4e0a\u82e5\u4ecd\u6709\u88c5\u5907\uff08\u540c\u7c7b\u578b\u8986\u76d6\uff09\uff0c\u5148\u53d6\u4e0b\u56de\u80cc\u5305\uff0c
            #   \u907f\u514d db_equip_put \u76f4\u63a5\u8986\u76d6\u5bfc\u81f4\u65e7\u88c5\u5907\u4e22\u5931\uff08\u6570\u636e\u4e22\u5931\u4e0d\u53ef\u63a5\u53d7\uff09\u3002
            try:
                _occ = db_equip_take(rid, slot)
                if _occ:
                    db_bag_add(rid, int(_occ['bid']), 1)
                    log('tcp.log', '  .. 10511 \u69fd\u4f4d%d \u539f\u6709\u88c5\u5907 item_id=%d \u21d2 \u56de\u80cc\u5305'
                        % (slot, _occ['item_id']))
            except Exception as _eocc:
                log('tcp.log', '  !! 10511 \u6e05\u7a7a\u76ee\u6807\u69fd\u5931\u8d25: %r' % (_eocc,))
            db_equip_put(rid, slot, bag_item_id, bid, hero_bid)
            # \u2462 \u63a8\u9001\uff1a\u80cc\u5305\u53d8\u4e86 + \u5220\u4e86\u90a3\u4e00\u4ef6
            try:
                items = db_bag_get(rid, BAG_MAIN)
                bc = getattr(self, '_last_bag_code', BAG_MAIN)
                # ★ 2026-10-17：**推 10500（增量添加）** —— 物品被取走这件事由紧跟的
                #   SC_10503（删除通知）交代；**不能推 10502**：客户端只在它自己发
                #   CS_10502 后才处理 SC_10502，主动推的会被忽略（文档 §8.3 + 10554 处实测）。
                self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
                push_10510(self, rid, bc)
                self.request.sendall(pack_frame(10503, w_u8(1) + w_u16(1) + w_u32(bag_item_id)))
            except Exception:
                pass
            log('tcp.log', '  ** 10511 \u7a7f\u6234 item_id=%d bid=%d slot=%d hero=%d'
                % (bag_item_id, bid, slot, hero_bid))
            # ★ ★ 修正（用户实机报障\u201c装备\u88ab\u793c\u5305\u5360\u4f4d\u201d）：
            #   客户端 `handle_10511` 用 **`resp.eqm_new_pos`** 作为穿\u4e0a\u53bb\u7684槽\u4f4d
            #   （`rolePutOnEquip(resp.eqm_new_pos, ...)`）。
            #   原实\u73b0此\u5904**\u786c\u7f16\u7801\u56de 0** ⇒ \u6240\u6709\u88c5\u5907\u90fd\u843d\u5230\u540c\u4e00\u683c \u21d2 \u51b2\u7a81\u3002
            #   现\u56de\u771f\u5b9e\u5206\u914d\u7684 `slot`\u3002
            pkt = pack_frame(10511, w_u8(1) + w_str('') + w_u8(0) +
                             w_u32(bag_item_id) + w_u32(eqm_item_id) + w_u8(int(slot) & 0xff) +
                             w_u32(hero_bid))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10511 SC_10511 code=1(TRUE) bag_item_id=%d bid=%d (%d bytes)'
                % (bag_item_id, bid, len(pkt)))
            return
        if cmd == 10552:
            # CS_10552{bag_code:u8, volume:u8, state:u8}
            #   \u2192 SC_10552{code:u8, msg:string, bag_code:u8, old:u16, new:u16}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08show_cmd 10552\uff09\uff1b\u65e0 D|Dsc*| \u5b50\u8868 \u21d2 \u5b89\u5168\u3002
            # \u2605 \u80cc\u5305\u6269\u5bb9\uff1a`volume` \u662f\u672c\u6b21\u8981\u589e\u52a0\u7684\u5bb9\u91cf\u3002
            bag_code = body[0] if len(body) >= 1 else BAG_MAIN
            add_vol = body[1] if len(body) >= 2 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            old = db_get_bag_volume(rid, bag_code)
            new = old + int(add_vol)
            if add_vol > 0:
                db_set_bag_volume(rid, bag_code, new)
            pkt = pack_frame(10552, w_u8(1) + w_str('') + w_u8(bag_code) +
                             w_u16(old) + w_u16(new))
            self.request.sendall(pkt)
            # ★ 2026-10-17：**扩容后必须补推 SC_10510（格子最大值）** —— 客户端的格子数
            #   来自 10510（文档 §8.3："纯 S→C 推送、需下发"），本服务端此前从不推它
            #   ⇒ 用户"买了扩容但格子没变多 / 缺格子"（本轮报障）。
            push_10510(self, rid, bag_code)
            log('tcp.log', '  << 10552 SC_10552 code=1 bag_code=%d old=%d new=%d (%d bytes)'
                % (bag_code, old, new, len(pkt)))
            return
        if cmd == 10570:
            # CS_10570{bag_code:u8, ItemIdList:table(id:u32)}
            #   \u2192 SC_10570{bag_code:u8, code:u8, msg:string}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff1b\u65e0 D|Dsc*| \u5b50\u8868 \u21d2 \u5b89\u5168\u3002
            # \u2605 \u6279\u91cf\u64cd\u4f5c\uff08\u6309 id \u5217\u8868\uff09\uff1a\u672c\u5b9e\u73b0\u6309\u201c**\u4e22\u5f03**\u201d\u5904\u7406\uff08\u5220\u9664\u8fd9\u4e9b item_id\uff09\uff0c
            #   \u5e76\u63a8 10503 \u544a\u77e5\u5ba2\u6237\u7aef\u54ea\u4e9b\u6ca1\u4e86\u3002
            bag_code = body[0] if len(body) >= 1 else BAG_MAIN
            n = struct.unpack_from('>H', body, 1)[0] if len(body) >= 3 else 0
            ids = []
            off = 3
            for _ in range(n):
                if off + 4 > len(body):
                    break
                ids.append(struct.unpack_from('>I', body, off)[0])
                off += 4
            rid = role_state(self.cfg).get('rid', 1001)
            gone = db_bag_delete(rid, ids, bag_code) if ids else []
            if gone:
                try:
                    self.request.sendall(pack_frame(
                        10503, w_u8(1) + w_u16(len(gone)) +
                        b''.join(w_u32(x) for x in gone)))
                except Exception:
                    pass
                log('tcp.log', '  ** 10570 \u6279\u91cf\u5220\u9664 bag_code=%d \u5220\u4e86 %r'
                    % (bag_code, gone))
            pkt = pack_frame(10570, w_u8(bag_code) + w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10570 SC_10570 bag_code=%d code=1 (%d bytes)'
                % (bag_code, len(pkt)))
            return
        if cmd in (10534, 10551):
            # CS_10534{item_bid:u32} \u2192 SC_10534{val:u8}
            # CS_10551{item_bid:u32} \u2192 SC_10551{val:u32}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff1b\u5168\u7b80\u5355\u7c7b\u578b \u21d2 \u5b89\u5168\u3002
            # \u26a0 `val` \u7684\u8bed\u4e49**\u672a\u77e5**\uff08\u65e0\u6570\u636e\u6e90\uff09\u21d2 \u5982\u5b9e\u56de 0\uff0c\u4e0d\u7f16\u9020\u3002
            pkt = pack_frame(cmd, w_u8(0) if cmd == 10534 else w_u32(0))
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d val=0 (\u65e0\u6570\u636e\u6e90\uff0c\u5982\u5b9e\u56de 0)'
                % (cmd, cmd))
            return
        if cmd == 10528:
            # CS_10528{lev:u8, type:u8} \u2192 SC_10528{code, msg, lev, state_list:table(lev,time,flag)}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff1b\u65e0 D|Dsc*| \u5b50\u8868 \u21d2 \u5b89\u5168\u3002
            # \u26a0 \u6ca1\u6709\u201c\u72b6\u6001\u5217\u8868\u201d\u7684\u6570\u636e\u6e90 \u21d2 \u5982\u5b9e\u56de**\u7a7a\u8868**\uff0c\u4e0d\u7f16\u9020\u6761\u76ee\u3002
            lev = body[0] if len(body) >= 1 else 1
            sl = self.cfg.get('state_list') or []
            out = w_u8(1) + w_str('') + w_u8(lev) + w_u16(len(sl))
            for stt in sl:
                out += (w_u8(int(stt.get('lev', 0)) & 0xff) +
                        w_u32(int(stt.get('time', 0))) +
                        w_u8(int(stt.get('flag', 0)) & 0xff))
            pkt = pack_frame(10528, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10528 SC_10528 code=1 lev=%d state_list=%d (%d bytes)'
                % (lev, len(sl), len(pkt)))
            return
        if cmd == 10505:
            # CS_10505{code:u8, item_id:u32, use_num:u16, type:u32, bid:u32}
            #   \u2192 SC_10505{code:u8, msg:string, item_bid:u32}
            # \u4f9d\u636e\uff1aprotocol/manual.md + cmd_resolve_105.luac proto#35/#36\uff08\u6743\u5a01\uff09\u3002
            # \u2605 \u7528\u6237\u5b9e\u673a\u62a5\u969c\u201c\u7269\u54c1\u65e0\u6cd5\u4f7f\u7528\u201d\uff1a\u5ba2\u6237\u7aef\u4f1a\u53d1 CS_10505\uff0c
            #   \u800c\u670d\u52a1\u7aef**\u6ca1\u6709\u8fd9\u6761\u5206\u652f\u21d2 \u65e0\u5e94\u7b54\u21d2 \u754c\u9762\u6ca1\u53cd\u5e94**\u3002
            # \u95ed\u73af\uff1a\u6263\u6570\u91cf \u2192 \u5f52\u96f6\u5219\u5220\u884c\u5e76\u63a8 10503\uff1b\u5426\u5219\u63a8 10501 \u5237\u65b0\u6570\u91cf \u2192 \u56de 10505
            item_id = struct.unpack_from('>I', body, 1)[0] if len(body) >= 5 else 0
            use_num = struct.unpack_from('>H', body, 5)[0] if len(body) >= 7 else 0
            if use_num <= 0:
                use_num = 1
            bid_in = struct.unpack_from('>I', body, 9)[0] if len(body) >= 13 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            row = db_bag_get_one(rid, item_id)
            if row is None:
                pkt = pack_frame(10505, w_u8(0) + w_str('no such item %d' % item_id) +
                                 w_u32(bid_in))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10505 SC_10505 code=0 (item_id=%d \u4e0d\u5b58\u5728)' % item_id)
                return
            bid = int(row.get('bid') or bid_in)
            left = int(row.get('quantity') or 0) - use_num
            if left > 0:
                db_bag_set_quantity(rid, item_id, left)
                # 10501 \u6570\u91cf\u66f4\u65b0\u63a8\u9001
                try:
                    self.request.sendall(pack_frame(
                        10501, w_u8(getattr(self, '_last_bag_code', BAG_MAIN)) +
                        w_u16(1) + w_u32(item_id) + w_u16(left)))
                except Exception:
                    pass
                log('tcp.log', '  ** \u4f7f\u7528\u7269\u54c1 item_id=%d bid=%d x%d \u21d2 \u5269 %d'
                    % (item_id, bid, use_num, left))
            else:
                db_bag_delete(rid, [item_id])
                try:
                    self.request.sendall(pack_frame(10503, w_u8(1) + w_u16(1) + w_u32(item_id)))
                except Exception:
                    pass
                log('tcp.log', '  ** \u4f7f\u7528\u7269\u54c1 item_id=%d bid=%d x%d \u21d2 \u7528\u5b8c\u5220\u9664'
                    % (item_id, bid, use_num))
            # ★★ 使用效果：若是礼包，把内容发给玩家
            #   依据：客户端 config_item_gift.luac（已提取为 server/item_gift.json）。
            # [P6] 礼包开箱奖励统一走 RewardService.grant（幂等去重）
            gave = []
            _gc = [(cb, cn or 1) for cb, cn in gift_contents(bid) if is_valid_item(cb)]
            if _gc:
                _awards = [{'kind': 'item', 'bid': cb, 'amount': cn} for cb, cn in _gc]
                grant(rid, _awards, reference_id='gift-open:%d:%d' % (bid, item_id),
                      source='gift')
                gave = _gc
            if gave:
                try:
                    items = db_bag_get(rid, BAG_MAIN)
                    bc = getattr(self, '_last_bag_code', BAG_MAIN)
                    self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
                except Exception:
                    pass
                log('tcp.log', '  ** 礼包 bid=%d 打开 ⇒ %r' % (bid, gave))
            # ★★★ C5-A：`use_item` / `consume_item` 条件推进（目标 = **物品 bid**）。
            #   配置证据（mission_config.json 实计）：`use_item` 21 条
            #     （如 52000 侦查密令 ["use_item",25300,10]、86013 激活灵座）；
            #   `consume_item` 16 条（如 52020 修炼密令 ["consume_item",25420,10]）。
            #   触发点 = **本 CS_10505（使用物品）实际扣减成功之后**（上面已完成扣数/删行）。
            #   为什么两者都挂这里：`consume_item` 的语义是"累计消耗 N 个某物"，
            #   而客户端唯一的"主动消耗物品"入口就是 10505 ⇒ 与 `use_item` 同源。
            #   纪律：只按"确实发生了的一次使用"计数（n=use_num），
            #   不去猜强化/合成等其它可能间接消耗物品的路径（无证据）。
            try:
                _hit = list(mission_progress_advance(rid, 'use_item', bid, use_num) or []) + \
                       list(mission_progress_advance(rid, 'consume_item', bid, use_num) or [])
                if _hit:
                    _ms = mission_rows(self.cfg, rid)
                    push_to_rid(rid, pack_frame(12405, build_12400(_ms)))
                    log('tcp.log', '  ** 10505 任务推进 use/consume bid=%d n=%d -> %r '
                                   '（12405 已补推）' % (bid, use_num, _hit))
            except Exception as _e:
                log('tcp.log', '  !! 10505 任务推进失败: %r' % (_e,))
            pkt = pack_frame(10505, w_u8(1) + w_str('') + w_u32(bid))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10505 SC_10505 code=1(TRUE) item_bid=%d (%d bytes)'
                % (bid, len(pkt)))
            return
        if cmd == 10714:
            # CS_10714（空）→ SC_10714{lev:u8,
            #     InfoList:table(type:u8, cur_val:u32, max_val:u32, show_max_val:u32)}
            # 依据：protocol/manual.md + cmd_resolve_107.luac proto#19（无 D|Dsc*| 子表 ⇒ 安全）。
            # ★ 本实现按“我们确知的囊”报：背包(1) 与仓库(4)。
            # ⚠ `type` 的语义**未取证** ⇒ 按 bag_code 直传（不另发明编号）；mock 不编造具体上限。
            rid = role_state(self.cfg).get('rid', 1001)
            rows = [
                (BAG_MAIN, len(db_bag_get(rid, BAG_MAIN))),
                (STORAGE_CODE, len(db_store_get(rid, STORAGE_CODE))),
            ]
            out = w_u8(int(self.cfg.get('storehouse_lev', 0)) & 0xff) + w_u16(len(rows))
            for t, cur in rows:
                mx = db_get_bag_volume(rid, t)
                out += (w_u8(int(t) & 0xff) + w_u32(int(cur)) +
                        w_u32(int(mx)) + w_u32(int(mx)))
            pkt = pack_frame(10714, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10714 SC_10714 lev=%s InfoList=%d (%d bytes)'
                % (self.cfg.get('storehouse_lev', 0), len(rows), len(pkt)))
            return
        if cmd in (14600, 14601):
            # CS_14600\uff08\u7a7a\uff09 \u2192 SC_14600{days:u16, get_day:table(type:u8)}
            # CS_14601{days:u8} \u2192 SC_14601{tips:u16, msg:string, days:u8}
            # \u4f9d\u636e\uff1aprotocol/manual.md + \u5ba2\u6237\u7aef game/dailysign/dailysign_ctrl.luac
            #   \uff08\u5b83\u6ce8\u518c\u4e86 14600/14601\uff09\uff1b\u65e0 D|Dsc*| \u5b50\u8868 \u21d2 \u5b89\u5168\u3002
            # \u2605 \u7528\u6237\u62a5\u969c\u201c10 \u7ea7\u793c\u5305\u9886\u53d6\u4e0d\u4e86\u201d \u21d2 **14601 \u539f\u672c\u65e0\u5206\u652f\u21d2 \u65e0\u5e94\u7b54**\u3002
            # \u2605 \u793c\u5305 bid \u6765\u81ea config \u7684 `levgift_rewards`\uff08\u5e8f\u53f7 \u2192 bid\uff09\u3002
            #   \u5e8f\u53f7\u5230 bid \u7684\u5bf9\u5e94\u5173\u7cfb\u6765\u81ea\u7269\u54c1\u8868\u7684\u53ef\u67e5\u8bc1\u89c4\u5f8b\uff1a
            #   30010='10\u7ea7\u793c\u5305' 30011='20\u7ea7' 30012='30\u7ea7' 30013='40\u7ea7' 30018='50\u7ea7'
            #   \u26a0 \u5e8f\u53f7\u4e0e\u7b49\u7ea7\u7684\u7cbe\u786e\u5bf9\u5e94**\u5f85\u5b9e\u673a\u9a8c\u8bc1**\uff0c\u6545\u505a\u6210\u914d\u7f6e\u9879\u3002
            rid = role_state(self.cfg).get('rid', 1001)
            rewards = self.cfg.get('levgift_rewards') or {}
            got = db_get_levgift(rid)
            if cmd == 14600:
                types = sorted(int(k) for k in rewards.keys()) if rewards else []
                out = w_u16(int(self.cfg.get('levgift_days', 0)) & 0xffff) + w_u16(len(types))
                for t in types:
                    if t not in got:
                        out += w_u8(t & 0xff)
                pkt = pack_frame(14600, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 14600 SC_14600 days=%s get_day=%d (%d bytes)'
                    % (self.cfg.get('levgift_days', 0), len(out) - 4, len(pkt)))
                return
            days = body[0] if len(body) >= 1 else 0
            bid = int(rewards.get(str(days), 0) or 0)
            if not bid:
                pkt = pack_frame(14601, w_u16(0) +
                                 w_str('\u65e0\u6b64\u793c\u5305\uff08\u5e8f\u53f7 %d \u672a\u914d\u7f6e\uff09' % days) +
                                 w_u8(days))
                self.request.sendall(pkt)
                log('tcp.log', '  << 14601 SC_14601 tips=0 (\u5e8f\u53f7 %d \u672a\u914d)' % days)
                return
            if days in got:
                pkt = pack_frame(14601, w_u16(0) + w_str('\u5df2\u9886\u53d6') + w_u8(days))
                self.request.sendall(pkt)
                log('tcp.log', '  << 14601 SC_14601 tips=0 (\u5df2\u9886\u8fc7 %d)' % days)
                return
            db_add_levgift(rid, days)
            db_bag_add(rid, bid, 1)
            try:
                items = db_bag_get(rid, BAG_MAIN)
                bc = getattr(self, '_last_bag_code', BAG_MAIN)
                self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
            except Exception:
                pass
            pkt = pack_frame(14601, w_u16(1) + w_str('') + w_u8(days))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 14601 \u9886\u53d6\u793c\u5305 \u5e8f\u53f7=%d bid=%d \u21d2 \u5df2\u5165\u5305'
                % (days, bid))
            return
        if cmd == 11301:
            # CS_11301\uff08\u7a7a\uff09\u2192 SC_11301{lev:u8, num:u8}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u26a0 num \u7684\u8bed\u4e49**\u672a\u53d6\u8bc1** \u21d2 \u53d6 config\uff08\u9ed8\u8ba4 0\uff09\uff0c\u4e0d\u7f16\u9020\u3002
            lev = int(self.cfg.get('arena_lev', 0)) & 0xff
            num = int(self.cfg.get('arena_num', 0)) & 0xff
            pkt = pack_frame(11301, w_u8(lev) + w_u8(num))
            self.request.sendall(pkt)
            log('tcp.log', '  << 11301 SC_11301 lev=%d num=%d (%d bytes)' % (lev, num, len(pkt)))
            return
        # ------------------------------------------------------------
        # ★★ R47：荣耀竞技场（`trophy_arena_ctrl`）
        #   真机实测：`11300` **259 次**、`11301` 252 次、`11308` **23 次**；
        #   其中 11300/11308 原落在 `_GENERIC_DEFAULT_CMDS` 回**全零** ⇒ 面板无进度。
        #   ★ 纪律（决策 #4 严格不猜）：
        #     · `trophy/times/index_state/win_times/state` 一律取**真实 DB 状态**
        #       （没打过 = 0，是真话）；`pk_record` 取真实战绩（无战绩 = 空表）。
        #     · **`pk_show`（对手列表）留空**：本服单机、`config_arena_data` 只有 3 条
        #       位置数组**并非对手表**，且客户端里**没有任何 proto 消费 `pk_show`**
        #       ⇒ 无诚实来源，不编造对手。
        # ------------------------------------------------------------
        if cmd == 11300:
            # SC_11300{trophy:I, times:C, index_state:C,
            #   pk_show:T{id:C,rid:I,srv_id:s,name:s,lev:H,career:H,sex:C,trophy:I,
            #             partner_list:T{…},arena_soul:C},
            #   pk_record:T{type:C,rid:I,srv_id:s,name:s,result:C,trophy:I,
            #               is_counterattack:C,reply_id:s}}
            _rid = role_state(self.cfg).get('rid', 1001)
            _a = db_arena_state(_rid)
            _recs = db_arena_records(_rid)
            _opps = db_arena_opponents(_rid)
            out = (w_u32(_a['trophy'] & 0xffffffff) +
                   w_u8(_a['times'] & 0xff) +
                   w_u8(_a['index_state'] & 0xff))
            out += arena_pk_show_body(_opps)       # ★ 对手 = 本服已有角色（决策 A）
            out += arena_pk_record_body(_recs)
            self.request.sendall(pack_frame(11300, out))
            log('tcp.log', '  << 11300 trophy=%d times=%d opps=%d records=%d (%d bytes)'
                % (_a['trophy'], _a['times'], len(_opps), len(_recs), len(out)))
            return
        if cmd == 11307:
            # SC_11307{trophy:I, pk_record:T{…}} —— 战绩列表（与 11300 同子结构）
            _rid = role_state(self.cfg).get('rid', 1001)
            _a = db_arena_state(_rid)
            _recs = db_arena_records(_rid)
            out = w_u32(_a['trophy'] & 0xffffffff) + arena_pk_record_body(_recs)
            self.request.sendall(pack_frame(11307, out))
            log('tcp.log', '  << 11307 trophy=%d records=%d (%d bytes)'
                % (_a['trophy'], len(_recs), len(out)))
            return
        if cmd == 11308:
            # SC_11308{win_times:C, state:C}
            _rid = role_state(self.cfg).get('rid', 1001)
            _a = db_arena_state(_rid)
            out = w_u8(_a['win_times'] & 0xff) + w_u8(_a['state'] & 0xff)
            self.request.sendall(pack_frame(11308, out))
            log('tcp.log', '  << 11308 win_times=%d state=%d (%d bytes)'
                % (_a['win_times'], _a['state'], len(out)))
            return
        if cmd == 17301:
            # ★★ R50：魂师大赛（竞速）主状态 —— 由「未开放」改为 **DB 驱动真实值**
            #   SC_17301{result:u8, msg:s, daily_time:u16, daily_time2:u32, score:u32,
            #            win_times:u32, lose_times:u32, total_times:u32,
            #            rest_time:u32, first_reward:u8}
            #   客户端消费点（`race_ctrl.luac` proto#14 on17301）：
            #     model:setStatus(0) / setMatchData(nil) / **setResultData(data)** /
            #     openWaitPanel / openResultPanel / gainFirstAward /
            #     **model:setScore(data.score)**
            #   ⇒ score/win/lose/total 是"战绩"，本服没有战斗结算写入时**全 0 就是真话**
            #     （与 R47 竞技场同一口径：存/读/对手源做通，产出等玩法）。
            #   ★ 移出 `_UNSUPPORTED_ACTION_CMDS`（否则会被它抢先回"未开放"）。
            _rid = role_state(self.cfg).get('rid', 1001)
            _rs = db_race_state(_rid)
            out = (w_u8(1) + w_str('') +
                   w_u16(int(_rs['daily_time']) & 0xffff) +
                   w_u32(int(_rs['daily_time2']) & 0xffffffff) +
                   w_u32(int(_rs['score']) & 0xffffffff) +
                   w_u32(int(_rs['win_times']) & 0xffffffff) +
                   w_u32(int(_rs['lose_times']) & 0xffffffff) +
                   w_u32(int(_rs['total_times']) & 0xffffffff) +
                   w_u32(int(_rs['rest_time']) & 0xffffffff) +
                   w_u8(int(_rs['first_reward']) & 0xff) +
                   w_u8(int(_rs['is_match']) & 0xff) +
                   w_u32(int(_rs['kill_number']) & 0xffffffff) +
                   w_u32(int(_rs['continue_win']) & 0xffffffff) +
                   w_u8(int(_rs['is_team_open']) & 0xff) +
                   w_u8(int(_rs['act_status']) & 0xff) +
                   w_u16(int(_rs['daily_win']) & 0xffff))
            pkt = pack_frame(17301, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 17301 SC_17301 result=1 score=%d win=%d lose=%d total=%d (%d bytes)'
                % (_rs['score'], _rs['win_times'], _rs['lose_times'],
                   _rs['total_times'], len(pkt)))
            return
        if cmd == 17309:
            # ★★ R50：魂师大赛排行榜 —— 真实 `rank_list`
            #   SC_17309{rank_list:table(role_name:s, rid:u32, srid:s, rank:u32,
            #                            career:u8, sex:u8, score:u32, lev:u32, win_num:u32)}
            #   数据源 = 本服 `roles` 表（名字/等级/职业/性别为真）+ 各自 `race_state.score`
            #   （没打过=0）。**不编造任何对手/分数。**
            #   ★ 移出 `_GENERIC_DEFAULT_CMDS`（否则会被它抢先回空表）。
            _rows = race_rank_list(role_state(self.cfg).get('rid', 1001))
            out = w_u16(len(_rows))
            for x in _rows:
                out += (w_str(x['role_name']) + w_u32(x['rid']) + w_str(x['srid']) +
                        w_u32(x['rank']) + w_u8(x['career'] & 0xff) +
                        w_u8(x['sex'] & 0xff) + w_u32(x['score'] & 0xffffffff) +
                        w_u32(x['lev'] & 0xffffffff) + w_u32(x['win_num'] & 0xffffffff))
            pkt = pack_frame(17309, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 17309 SC_17309 rank_list=%d (%d bytes)' % (len(_rows), len(pkt)))
            return
        if cmd == 17501:
            # ★★ R50：宗门战入口 —— 保留"诚实回失败"，但**回显 CS 的 `type`**
            #   原先把 `type` 一律填 0；客户端 `guildwars_ctrl.handle17501` 按 type 分支，
            #   回显它才不会让分支对不上。玩法本体本服没有 ⇒ `code=0 + msg`（不撒谎）。
            _t = body[0] if len(body) >= 1 else 0
            out = w_u8(0) + w_u8(_t & 0xff) + w_str(_UNSUPPORTED_MSG)
            pkt = pack_frame(17501, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 17501 SC_17501 code=0 type=%d 未开放 (%d bytes)' % (_t, len(pkt)))
            return
        if cmd == 11700:
            # CS_11700\uff08\u7a7a\uff09\u2192 SC_11700{free_times:u8, all_times:u8, reward_coin:u32,
            #     one_name:string, one_coin:u32,
            #     record_server:table(name:string, id:u8, val:u32),
            #     record_self:table(id:u8, val:u32)}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u26a0 \u5177\u4f53\u6570\u503c\u7684\u8bed\u4e49**\u672a\u53d6\u8bc1** \u21d2 \u53d6 config\uff08\u9ed8\u8ba4 0/\u7a7a\uff09\u3002
            rs = self.cfg.get('rank_records_server') or []
            rm = self.cfg.get('rank_records_self') or []
            out = (w_u8(int(self.cfg.get('rank_free_times', 0)) & 0xff) +
                   w_u8(int(self.cfg.get('rank_all_times', 0)) & 0xff) +
                   w_u32(int(self.cfg.get('rank_reward_coin', 0))) +
                   w_str(str(self.cfg.get('rank_one_name', ''))) +
                   w_u32(int(self.cfg.get('rank_one_coin', 0))) +
                   w_u16(len(rs)) + w_u16(len(rm)))
            for r in rs:
                out += w_str(str(r.get('name', ''))) + w_u8(int(r.get('id', 0)) & 0xff) + w_u32(int(r.get('val', 0)))
            for r in rm:
                out += w_u8(int(r.get('id', 0)) & 0xff) + w_u32(int(r.get('val', 0)))
            pkt = pack_frame(11700, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 11700 SC_11700 record_server=%d record_self=%d (%d bytes)'
                % (len(rs), len(rm), len(pkt)))
            return
        if cmd == 10923:
            # CS_10923{id:u16} \u2192 SC_10923{id:u16, status:u8, int_args:table(val:u32)}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u26a0 status/int_args \u7684\u8bed\u4e49**\u672a\u53d6\u8bc1** \u21d2 \u56de\u7a7a\u8868\uff0c\u4e0d\u7f16\u9020\u3002
            aid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            # ★ PHASE 2.19：status/int_args 改为**有据取值**（原先恒 status=0 ⇒ 图标不显示）。
            #   证据链：
            #     ① 反汇编 `activity_ctrl.luac`（见 analysis/extraction/real_cs_formats_1_4_11.md §6.5）：
            #        10922/10923/10924/10925 **共用同一处理体** Activityhander10925，
            #        条目结构一致，门槛为 `Config.Function[id]` 存在 且 `is_open==1`
            #        且 `open_lev <= 角色等级`；
            #     ② 源码 L17550 记录 R49 查明的结论：客户端 proto#49 要求
            #        **`status == 1` 才显示图标**（{501,502,503,504} 的检查）；
            #     ③ 现存 `10924` 实现本就对合格条目发 `status=1` + `int_args=[时间戳]`
            #        （空 int_args 会让 daily_ctrl 崩溃）⇒ 本条**与已上线行为保持一致**。
            import time as _t23
            _lev23 = int(role_state(self.cfg).get('lev') or 1)
            _row23 = None
            for _f23 in (function_cfg() or []):
                if int(_f23.get('id') or 0) == aid:
                    _row23 = _f23
                    break
            _st23 = 1 if (_row23 is not None
                          and int(_row23.get('is_open', 0)) == 1
                          and int(_row23.get('open_lev', 0)) <= _lev23) else 0
            _ia23 = [int(_t23.time()) & 0xFFFFFFFF] if _st23 else []
            pkt = pack_frame(10923, w_u16(aid) + w_u8(_st23) + w_u16(len(_ia23)) +
                             b''.join(w_u32(_v) for _v in _ia23))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10923 SC_10923 id=%d status=%d int_args=%d（按 config_function 门槛）'
                % (aid, _st23, len(_ia23)))
            return
        if cmd == 10924:
            # ★★★ R49 修复（真机实测）：活动预告弹窗刷屏 + 重复
            #   现象：进图后反复弹出「提示：XX活动在H时M分~H时M分开启，玩家快去战个痛快吧！」
            #         （宗门战/帝国之战/斗罗战场/魂师大赛/学院闯关…），带 `取消(N)` 倒计时，
            #         同一弹窗重复出现，占屏约 50 秒才进场景。
            #   取证：客户端 `activity_ctrl.luac` proto#37（bc=487，反汇编见
            #         analysis/_activity_p37.txt）：
            #           if data.status == 1 then return end   -- BC 9..16
            #           self:pushByScene(1)                    -- 否则链式继续下一条
            #         文案模板在本 proto 内（'…活动在…开启，玩家快去战个痛快吧！'），
            #         活动名取 `Config.RiChang[id].name`，id 为 **config_richang 的活动类 id**
            #         （KSHORT 硬编码：101/107/108/111/112/113/115/116/118）。
            #   对照实验（每次只改一个变量，同机复现）：
            #     A. 原状（10924 act_list=69）        → 弹窗复现（t1_4/t3_5/t4_5/t6_4/t7_4）
            #     B. 把预告 id 补进 10924（75 条）    → 弹窗仍在（t4）
            #     C. 10922 回 status=1（9 条）        → 弹窗仍在（t4/t7）
            #     D. 10924 剔除预告 id（66 条）        → 时好时坏，**不可靠**（t5 干净 / t7 复现）
            #     E. **10924 回空表**                 → ✅ 两次复现均**完全无弹窗**（t2 / t8）
            #   ⇒ 结论：该预告走查由**客户端本地配置**驱动（config_god_unite_data 的
            #     `is_notice`×54 + config_richang 活动名），服务端 `status` 不参与判定；
            #     唯一稳定可控的点是"**是否下发个人活动列表**"。
            #   ⇒ 取舍（如实记录）：回空表会同时少掉顶部「开服福利/中秋团圆/七天排行」
            #     三个活动入口图标（它们指向本服**并未实现**的运营活动）。
            #     若更看重这 3 个图标，把 config.json 的 `send_personal_act_list` 设为 true
            #     （则弹窗会回来 —— 这是同一枚硬币的两面，无法只取其一）。
            if self.cfg.get('disable_10924', True) and not self.cfg.get('send_personal_act_list'):
                pkt = pack_frame(10924, w_u16(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10924 SC_10924 act_list=0 (R49 修复：抑制活动预告弹窗)')
                return
            # ★★★ 2026-09-19 完善：活动列表（客户端真机在发，登录后必发）
            #   CS_10924（空）→ SC_10924{act_list:table(id:uint16, status:uint8,
            #                              int_args:D|Dsc10924int_args|)}
            #   ★ Dsc10924int_args 线序取证（cmd_resolve_109.luac proto#19/#25）：
            #     ReadFMT('H') 计数 → 循环 ReadFMT('I') ⇒ table(val:uint32)。
            #     fields.json 里标 uint16 是错的（兄弟协议 10922/10923/10925 同为 u32）。
            #   ★ 客户端 activity_ctrl.luac proto#30 对每条的处理：
            #     setActiData(id, status, int_args) 直接存储三元组；
            #     Function.Config[id].is_open ~= 1 → return（不开不显示）；
            #     roleVo.lev < open_lev → pushUnopenList（标记未开放）。
            #     proto#49 里 {501,502,503,504} 检查要求 **status == 1** 才显示图标。
            #   ⇒ 数据源：config_function.json（91 条真实功能/活动开放表）。
            #     · 只发 is_open=1 且 open_lev <= 玩家等级 的活动（客户端不跳过任何一条）
            #     · status=1（进行中）
            #     · int_args=[当前时间戳]（u32 时间戳数组；空表会让 daily_ctrl 崩溃）
            import time as _time10924
            now = int(_time10924.time()) & 0xFFFFFFFF
            lev = int(role_state(self.cfg).get('lev') or 1)
            fc = function_cfg() or []
            sel = [f for f in fc
                   if int(f.get('is_open', 0)) == 1
                   and int(f.get('open_lev', 0)) <= lev]
            sel.sort(key=lambda f: (int(f.get('sort_id') or 0), int(f.get('id') or 0)))
            # ★★★ R49 修复：活动提示弹窗刷屏 + 重复（"XX活动在…开启，玩家快去战个痛快吧！"）
            #   根因（2026-09-28 真机实测，两步定性）：
            #     ① 把 `SC_10924.act_list` 置空 → 弹窗**完全消失**、正常进主城
            #        （对照：shots/t2_*.png vs shots/t1_*.png）⇒ 本消息是弹窗的驱动源。
            #     ② 客户端 `activity_ctrl.luac` proto#37（bc=487）的真机反汇编逻辑：
            #          if data.status == 1 then return end   -- BC 9..16：status==1 ⇒ 直接退出
            #          self:pushByScene(1)                    -- 否则**链式继续**下一条
            #        ⇒ 只要有一条被客户端遍历到、而 status≠1，就会弹一次并继续下一条。
            #     ③ 弹窗用的 id 空间是 **`config_richang` 的活动 id**（proto#37 内 KSHORT/nil 判定）：
            #          101 xianmo(斗罗战场) 107 menpai(学院闯关)  108 race(魂师大赛)
            #          111 guildwars(宗门战) 112 diguowar(帝国之战) 113 peakwar(精英大赛)
            #          115 chief(首席争霸)   116 julong(绝地凶兽)  118 guildcretarea(宗门副本)
            #        而原实现发的是 **`config_function` 的 id（1..91）** —— 两套 id 空间不相交，
            #        ⇒ 这 9 条在客户端永远查不到 data，`data.status` 恒为 nil ≠ 1
            #        ⇒ 每次场景进入/活动数据刷新都走一遍链 ⇒ **多弹窗 + 重复**。
            #   修复：把这 9 个"会被提示"的活动 id 一并补进 act_list（status=1）。
            #   ★ 本轮（R49）最终修复：把这些 id **从 act_list 中剔除**（而不是补进去）。
            #     实测对照（同一次真机复现，一次一个变量）：
            #       补进去（status=1）  → 弹窗仍在（shots/t4_*.png）
            #       10922 回 status=1   → 弹窗仍在
            #       10924 回空表        → 弹窗消失，但活动图标也没了（shots/t2_*.png）
            #     ⇒ 客户端的"活动预告"走查只依赖**本地配置**（`config_god_unite_data`
            #       的 `is_notice`×54 + `config_richang` 的活动名），只要活动表里有这批
            #       id 就会走一遍预告；服务端下发的 `status` 并不参与该判定。
            #     ⇒ 因此服务端唯一可行的做法是：**不把这批"客户端自带预告"的活动 id 下发**，
            #       其余活动照常下发（活动图标保留）。
            #   ★ 默认开启；`config.json: notice_act_ids=[]` 即关闭本修复（对照实验）。
            _nids = self.cfg.get('notice_act_ids')
            if _nids is None:
                _nids = [101, 107, 108, 111, 112, 113, 115, 116, 118]
            _skip = set(int(i) for i in _nids)
            # ★★ PHASE 2.31 实验：`act_list` 的 **id 空间**可切换。
            #   发现（反汇编 `daily_data.luac` proto#17，处理 `SC_13786`）：
            #     for _, item in <遍历 self.activity_list> do
            #         for _, d in pairs(richang_list) do
            #             if d.id == item.id then item.num = d.num end      -- ★ 按 id 匹配
            #         end
            #         ...
            #     end
            #   ⇒ 日常行来自 `activity_list`，且其 `id` 必须与
            #     **`13786.richang_list[].id`（= config_richang.RiChang 的 id：208/205/207…）**
            #     同一个空间。
            #   而原实现（及 R49）发的是 **`config_function` 的 id（3/5/6/…/121/1000…）**
            #     ⇒ 两套 id 不相交 ⇒ **匹配不上 ⇒ 日常活动列表恒空**（用户报障「日常/提升 空白」）。
            #   ⇒ 开 `DSH_10924_RICHANG=1` 即改用 richang id 空间做对照实验（默认关闭，保持原行为）。
            if os.environ.get('DSH_10924_RICHANG') == '1':
                _rows = [int(t.get('id') or 0) & 0xffff
                         for t in (richang_cfg().get('tasks') or [])
                         if int(t.get('id') or 0) > 0 and int(t.get('id') or 0) not in _skip]
            else:
                _rows = [int(f.get('id', 0)) & 0xffff for f in sel
                         if int(f.get('id', 0)) not in _skip]
            out = w_u16(len(_rows))
            for _id in _rows:
                out += w_u16(_id) + w_u8(1) + w_u16(1) + w_u32(now)   # status=1, int_args=[now]
            pkt = pack_frame(10924, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10924 SC_10924 act_list=%d (真实活动表, lev=%d, 剔除预告 %d) (%d bytes)'
                % (len(_rows), lev, len(sel) - len(_rows), len(pkt)))
            return
        if cmd == 16603:
            # ★★★ 2026-09-19：限时目标/天降豪礼详情查询（客户端真机在发）
            #   CS_16603{bid:u32} —— ★ 规格以 AutoConstruct 为准（2026-09-19 回滚修正）：
            #     cmd_resolve_166.luac 里 cs/16603 的 spec 数组 = ['bid__I'] **单字段**
            #     （sc/16603 = ['bid__I','remain_sec__I','finish__I','aim_list__T__...', ...]）。
            #     真机抓包 body 恒为 8 字节 = bid(4) + **客户端缓冲区 4 字节残留**；
            #     同一"尾部残留"现象见 16500 body=00660000（CS 空）、17200 body=010103e9、
            #     16400 body=type+00000003、16605 body=…+2d2d2d2d（CS 102 个 bid + 4 残留）。
            #     ⇒ 解析只取前 4 字节，尾部残留一律忽略（不可当作 num 字段）。
            #   SC_16603{bid:u32, remain_sec:u32, finish:u32,
            #            aim_list:table(aim:u32, aim_str:string, status:u8,
            #                           item_list:D|Dsc16603item_list|, int_args:D|Dsc16603int_args|),
            #            item_effect_list:table(bid:u32, effect_1:u8, effect_2:u8),
            #            int_args:table(val:u32), client_reward:string,
            #            rank_list:table(rid:u32, srv_id:string, name:string,
            #                            sex:u8, career:u8, lev:u8, val:u32)}
            #   ★ 子表线序取证（cmd_resolve_166.luac）：
            #     proto#6  = Dsc16603item_list 读取器：ReadFMT('H') 计数 → 循环 ReadFMT('II')
            #               ⇒ table(bid:uint32, num:uint32)
            #     proto#43 = Dsc16603int_args 读取器：循环 ReadFMT('I')
            #               ⇒ table(val:uint32)（与 SC 顶层 int_args 同构）
            #     proto#41 = item_effect_list 元素读取器（bid,effect_1,effect_2）
            #     proto#45 = rank_list 元素读取器（rid,srv_id,name,sex,career,lev,val）
            #   ★ 客户端消费（action_ctrl.luac proto#18 + sky_present_panel.luac）：
            #     proto#18: updateSingleHoliday(data, 1) + Fire(GET_SINGLE_HOLIDAY, bid, 1)
            #     sky_present_panel proto#7 setDataVo:
            #       setLessTime(data.remain_sec)          ← 倒计时（0 ⇒ 显示已结束）
            #       self.data = data.aim_list             ← 目标列表
            #       self.item_effects = data.item_effect_list
            #       遍历 aim_list: item_status[status]、gift_extra_status[int_args[1].val]
            #     proto#12: data[index].int_args[1].val 参与显示 ⇒ aim_list 空表时无索引访问。
            #   ⇒ 数据源：**未取证到**（1015=天降豪礼面板 id，3041=真机请求 bid，二者均不在
            #     已提取配置表；config_growth_target 属于 305 号段）。
            #     **按项目纪律不编造 aim 内容** ⇒ aim_list 发空表（客户端正常显示空面板）。
            #     bid 回显请求值；remain_sec 给 30 天（避免客户端误判活动已结束）；
            #     finish=0；item_effect_list/int_args/rank_list 空表；client_reward 空串。
            bid = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            if len(body) < 4:
                log('tcp.log', '  !! 16603 CS 长度异常 %d 字节（规格 4；尾部残留可忽略）' % len(body))
            REMAIN_SEC_16603 = 30 * 24 * 3600
            out = (w_u32(bid) +                       # bid 回显
                   w_u32(REMAIN_SEC_16603) +          # remain_sec（30 天，进行中）
                   w_u32(0) +                         # finish（未完成）
                   w_u16(0) +                         # aim_list 空表（不编造子表内容）
                   w_u16(0) +                         # item_effect_list 空表
                   w_u16(0) +                         # int_args 空表
                   w_str('') +                        # client_reward 空串
                   w_u16(0))                          # rank_list 空表
            pkt = pack_frame(16603, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 16603 SC_16603 bid=%d num=%d aim_list=0 (结构完整, %d bytes)'
                % (bid, struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0, len(pkt)))
            return
        if cmd == 11200:
            # CS_11200\uff08\u7a7a\uff09\u2192 SC_11200{volume:u8, volume_open:u8,
            #     partner_bag:table(id,bid,type,color,lifttime,lev,exp,grow,score,stage,
            #                       rebirth,acc,partner_attr:D|..|,power,aptitude:D|..|,
            #                       innate_skill,skill:D|..|,jindan_skill:D|..|,
            #                       talisman_skill:D|..|,ext:D|..|),
            #     gratis:table(bid:u8, type:u8)}
            # \u4f9d\u636e\uff1aprotocol/manual.md + \u5ba2\u6237\u7aef game/hero/hero_equip_ctrl.luac
            #   \uff08\u5b83\u6ce8\u518c\u4e86 11200~11205\uff09\u3002
            # \u2605 \u7528\u6237\u62a5\u969c\u201c\u4f19\u4f34\u7a7a\u95f4\u5f00\u653e\u4e0d\u4e86\u201d \u21d2 **11200 \u539f\u672c\u65e0\u5206\u652f\u21d2 \u65e0\u5e94\u7b54**\u3002
            # \u26a0 `partner_bag` \u91cc\u6709 **6 \u4e2a D|Dsc11200*| \u672a\u89e3\u5b50\u8868** \u21d2
            #   \u6309\u4e0e\u80cc\u5305\u5b50\u8868\u76f8\u540c\u7684\u505a\u6cd5\u53d1 **0 \u9879**\uff08\u4e0d\u7f16\u9020\u5b50\u8868\u5185\u5bb9\uff09\u3002
            vol = int(self.cfg.get('partner_volume', 200)) & 0xff
            vopen = int(self.cfg.get('partner_volume_open', 200)) & 0xff
            pb = self.cfg.get('partner_bag') or []
            gratis = self.cfg.get('partner_gratis') or []
            out = w_u8(vol) + w_u8(vopen) + w_u16(len(pb))
            for h in pb:
                out += (w_u32(int(h.get('id', 0))) + w_u32(int(h.get('bid', 0))) +
                        w_u8(int(h.get('type', 0)) & 0xff) +
                        w_u8(int(h.get('color', 0)) & 0xff) +
                        w_u32(int(h.get('lifttime', 0))) +
                        w_u8(int(h.get('lev', 1)) & 0xff) +
                        w_u32(int(h.get('exp', 0))) +
                        w_u16(int(h.get('grow', 0)) & 0xffff) +
                        w_u32(int(h.get('score', 0))) +
                        w_u8(int(h.get('stage', 0)) & 0xff) +
                        w_u8(int(h.get('rebirth', 0)) & 0xff) +
                        w_u8(int(h.get('acc', 0)) & 0xff) +
                        w_u16(0) +                      # partner_attr
                        w_u32(int(h.get('power', 0))) +
                        w_u16(0) +                      # aptitude
                        w_u32(int(h.get('innate_skill', 0))) +
                        w_u16(0) +                      # skill
                        w_u16(0) +                      # jindan_skill
                        w_u16(0) +                      # talisman_skill
                        w_u16(0))                       # ext
            out += w_u16(len(gratis))
            for g in gratis:
                out += w_u32(int(g.get('bid', 0))) + w_u8(int(g.get('type', 0)) & 0xff)
            pkt = pack_frame(11200, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 11200 SC_11200 volume=%d volume_open=%d partner_bag=%d (%d bytes)'
                % (vol, vopen, len(pb), len(pkt)))
            return
        # [P8-migrated] 11215 已注册到 partner.handler（dispatch 前置拦截）；旧块保留作回滚/参考，不再执行
        if cmd == 11215:
            # ★★★ 2026-09-19 完善：伙伴列表（客户端真机在发，登录后必发）
            #   CS_11215（空）→ SC_11215{partner_list:table(
            #     id:u32, bid:u32, type:u8, color:u8, lifttime:u32, lev:u8, exp:u32,
            #     grow:u16, score:u32, stage:u8, rebirth:u8, acc:u8,
            #     partner_attr:D|Dsc11215partner_attr|, power:u32, aptitude:D|Dsc11215aptitude|,
            #     innate_skill:u32, skill:D|Dsc11215skill|, jindan_skill:D|Dsc11215jindan_skill|,
            #     talisman_skill:D|Dsc11215talisman_skill|, ext:D|Dsc11215ext|)}
            # ★ 数据源：完整伙伴基础表（53 个真实伙伴，含 color/score/innate_skill）。
            #   ⚠ 子表规格已解明（attr=14×u32、aptitude=3×u32、skill=u16），
            #     但**每个伙伴的实时属性/技能未取证** ⇒ 子表发**空表**（不编造）。
            #   ⚠ id/type/lifttime 语义未取证 ⇒ 用序号/0（保守值，不猜业务含义）。
            base = partner_base_cfg() or []
            # ★ R101：对照实验开关（全局 CFG ⇒ 下一次请求即生效）
            #   修正 R98 实验 C 的**判据缺陷**：界面本来就空时，"减少条目"区分不了
            #   "界面不读它"与"读了但被过滤" ⇒ 正确做法是**把整张表打空**。
            try:
                _lim15 = int(CFG.get('hero15_limit') or -1)
                if _lim15 == 0:
                    base = []
                    log('tcp.log', '  .. 11215 实验开关 hero15_limit=0 ⇒ partner_list 打空')
            except Exception:
                pass
            # ★★★ R87：`type` 与 `id` 按**有依据的映射**填（原先 type 恒 0、id 用序号）。
            #   · type：`hero_constants.luac` 有 `TableConst(hash=[('Common',1),('ShenJiang',2)])`，
            #     且被 `partner_atlas_container/atlas_view` 使用 ⇒ **图鉴按它分组**。
            #     `Config.Partner[bid].is_deity == 1` ⇒ 神将(2)，否则普通(1)。
            #   · id：元素**第一个字段就是 id（实例 id）**。已拥有给非 0（用 bid），
            #     未拥有给 0 —— 这样"图鉴=全部、阵型=已拥有"才能各取所需。
            _owned = {int(h.get('bid') or 0): h
                      for h in db_hero_list(role_state(self.cfg).get('rid', 1001),
                                            self.cfg)}
            out = w_u16(len(base))
            for i, p in enumerate(base, 1):
                _pb = int(p.get('bid', 0))
                _is_own = _pb in _owned
                _h = _owned.get(_pb) or {}
                _lev = int(_h.get('lev') or 1) if _is_own else 1
                out += (w_u32(_pb if _is_own else 0) +      # id（已拥有=bid，未拥有=0）
                        w_u32(_pb) +
                        w_u8(2 if int(p.get('is_deity') or 0) == 1 else 1) +   # type
                        w_u8(int(p.get('color', 0)) & 0xff) +
                        w_u32(0) +                           # lifttime
                        w_u8(_lev & 0xff) +                  # lev
                        w_u32(0) +                           # exp
                        w_u16(0) +                           # grow（未取证）
                        w_u32(int(p.get('score', 0))) +
                        w_u8(0) +                            # stage
                        w_u8(0) +                            # rebirth
                        w_u8(0) +                            # acc
                        w_u16(0) +                           # partner_attr（空表）
                        w_u32(int(p.get('score', 0))) +       # power（用配置 score）
                        w_u16(0) +                           # aptitude（空表）
                        w_u32(int(p.get('innate_skill', 0))) +
                        w_u16(0) +                           # skill（空表）
                        w_u16(0) +                           # jindan_skill（空表）
                        w_u16(0) +                           # talisman_skill（空表）
                        w_u16(0))                            # ext（空表）
            pkt = pack_frame(11215, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 11215 SC_11215 partner_list=%d (真实伙伴基础表) (%d bytes)'
                % (len(base), len(pkt)))
            return
        if cmd == 10800:
            # ★★★ 2026-09-19 完善：邮件列表（客户端真机在发，登录后必发）
            #   CS_10800（空）→ SC_10800{mail:table(
            #     id:u32, from_name:string, subject:string, content:string,
            #     assets:D|Dsc10800assets|, items:D|Dsc10800items|,
            #     send_time:u32, read_time:u32, time_out:u32)}
            #   Dsc10800assets={label:u8,val:u32}  Dsc10800items={bid:u32,quantity:u8}
            #   （round30 已用 dsc_spec 解明子表字段）
            # ★ 返回 1 封**系统欢迎邮件**（真实内容 + 真实物品附件）：
            #   · 物品用真实物品表里的 10007「4星香嫩豆腐」（打怪经验 +8%）
            #   · send_time 用当前时间戳；read_time=0（未读）；time_out=0（永不过期）
            import time as _time
            now = int(_time.time()) & 0xFFFFFFFF
            out = w_u16(1)                                   # mail 表 1 封
            out += (w_u32(1) +                               # id
                    w_str('系统') +
                    w_str('欢迎来到绝世唐门') +
                    w_str('欢迎来到单机私服！祝你游戏愉快。\n附件是新手小礼，请查收。') +
                    w_u16(0) +                               # assets 空表
                    w_u16(1))                                # items 1 条
            out += w_u32(10007) + w_u8(2)                    # 4星香嫩豆腐 ×2
            out += w_u32(now) + w_u32(0) + w_u32(0)          # send/read/time_out
            pkt = pack_frame(10800, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10800 SC_10800 mail=1 欢迎邮件(真实物品) (%d bytes)' % len(pkt))
            return
        if cmd in (10401, 10402, 10403, 10404):
            # 伙伴/魂师系统（客户端 game/hero/hero_ctrl.luac 注册）
            #   10401 CS（空）          -> SC{hero_bag:table(bid,color,lev,exp,state,chip,skill:D|Dsc10401skill|),
            #                                        hero_chip:table(bid,chip)}
            #   10402 CS{hero_bid:u32}  -> SC{bid:u16, lev:u8, color:u8, exp:u32}
            #   10403 CS{hero_bid:u32}  -> SC{bid:u16, attr:table(code:u16,value:u32)}
            #   10404 CS{hero_bid:u32}  -> SC{bid:u16, lev:u8, exp:u32, color:u8}
            # 依据：protocol/manual.md。⚠ 10401 的 `skill` 是 **D|Dsc10401skill| 未解子表**
            #   ⇒ 按与背包子表相同的做法发 **0 项**（不编造子表内容）。
            # ★ 伙伴数据来自 config 的 `heros`（[{bid,color,lev,exp,state,chip}]），
            #   **原版初始伙伴未取证** ⇒ 默认空，不编造。
            rid = role_state(self.cfg).get('rid', 1001)
            # ★★ R86：**伙伴背包改为读数据库**（原先读 config.json 的静态 17 个 ⇒
            #   神将兑换（`11216`）拿到的伙伴永远不会出现在背包里）。
            #   首次为空时由 db_hero_list 用 config 播种，之后一切以 DB 为准。
            heros = db_hero_list(role_state(self.cfg).get('rid', 1001), self.cfg)
            # ★ R98：**对照实验开关**（读全局 CFG ⇒ 改完**下一次请求即生效**，不必重登）。
            #   `hero_bag_limit`：`SC_10401.hero_bag` 只回前 N 个 —— 用来判定
            #   "伙伴界面的列表到底读不读 10401"（R93–R97 证明客户端侧探针触达不到）。
            #   ⚠ 上一版这段**没被写进来**：脚本里 ② 的守卫查 `'hero_bag_limit' not in src`，
            #     而 ① 的路由**先**插入了这个字符串 ⇒ ② 被静默跳过（"已接"是假的）。
            #     **同一个守卫陷阱在 R92 已犯过一次** —— 多步脚本的守卫必须查**代码特征**，
            #     不能查"这个变量名是否出现过"。
            try:
                _lim98 = int(CFG.get('hero_bag_limit') or 0)
                if _lim98 > 0:
                    heros = heros[:_lim98]
                    log('tcp.log', '  .. 10401 实验开关 hero_bag_limit=%d ⇒ 只回 %d 个'
                        % (_lim98, len(heros)))
            except Exception:
                pass
            if cmd == 10401:
                out = w_u16(len(heros))
                for h in heros:
                    out += (w_u32(int(h.get('bid', 0))) +
                            w_u8(int(h.get('color', 0)) & 0xff) +
                            w_u8(int(h.get('lev', 1)) & 0xff) +
                            w_u32(int(h.get('exp', 0))) +
                            w_u8(_hero_state(self.cfg)) +
                            w_u16(int(h.get('chip', 0)) & 0xffff) +
                            w_u16(0))          # skill 子表：0 项
                # hero_chip：碎片（同样取 config，默认空）
                chips = self.cfg.get('hero_chips') or []
                out += w_u16(len(chips))
                for c in chips:
                    out += w_u32(int(c.get('bid', 0))) + w_u16(int(c.get('chip', 0)) & 0xffff)
                pkt = pack_frame(10401, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 10401 SC_10401 hero_bag=%d hero_chip=%d (%d bytes)'
                    % (len(heros), len(chips), len(pkt)))
                # ★★★ R101：**补推 `SC_10412`（`SCHeroState`）** —— 伙伴 `state` 的初始化通道。
                #   依据：`SC_10412{hero_bid:u32, state:u8}` **只有 SC 没有 CS** ⇒ 服务端主动推送；
                #   `hero_data.luac` proto[12] 里 `state` 是 `HeroData` 的**独立字段**
                #   （`HeroVo` 的 28 个字段里没有它），由 `changeHeroSatus`/`10412` 那条线维护。
                #   ⇒ 我们此前从不发它 ⇒ 客户端每个伙伴的 `state` 从未被设置，
                #     而 `form_data.luac` proto#8 的"可选英雄"正是走 `HeroCtrl:getHeroListData()`。
                #   ★ 用与 `10401` **同一个** `_hero_state(cfg)`，两条通道不能自相矛盾。
                _st101 = _hero_state(self.cfg)
                for _h in heros:
                    self.request.sendall(pack_frame(
                        10412, w_u32(int(_h.get('bid') or 0)) + w_u8(_st101)))
                if heros:
                    log('tcp.log', '  << 10412 SC_10412 逐条推送 state=%d ×%d（伙伴状态初始化）'
                        % (_st101, len(heros)))
                # ★ R110：紧随其后补推 `SC_10414{lev}`（同族的 SC-only 推送，见其处理器注释）
                try:
                    self.request.sendall(pack_frame(
                        10414, w_u8(int(role_state(self.cfg).get('lev') or 1) & 0xff)))
                except Exception:
                    pass
                return
            hb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            found = None
            for h in heros:
                if int(h.get('bid', 0)) == hb:
                    found = h
                    break
            if cmd == 10404:
                # ★★ R86：按 **权威 spec** 只发 `bid:uint16 + lev:uint8`。
                #   原先多发了 `exp:u32 + color:u8` ⇒ 客户端按 spec 解析时**多出 5 字节**
                #   （`SC_10404{bid:H, lev:C}`，见 protocol/fields.json）。
                b_ = int((found or {}).get('bid', hb))
                out = (w_u16(b_ & 0xffff) +
                       w_u8(int((found or {}).get('lev', 1)) & 0xff))
                pkt = pack_frame(10404, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 10404 SC_10404 bid=%s lev=%s (%d bytes)'
                    % (b_, (found or {}).get('lev'), len(pkt)))
                return
            if cmd == 10403:
                out = w_u16(int((found or {}).get('bid', hb)) & 0xffff) + w_u16(0)   # attr: 0 项
                pkt = pack_frame(10403, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 10403 SC_10403 bid=%s attr=0 (%d bytes)'
                    % ((found or {}).get('bid', hb), len(pkt)))
                return
            # 10402
            # ★★ R86：按 **权威 spec** 只发 `bid:uint16 + lev:uint8`。
            #   原先多发了 `color:u8 + exp:u32` ⇒ 客户端按 spec 解析多出 5 字节。
            #   `SC_10402`/`SC_10404` 都只有 `bid/lev` —— 而这两条正是**上场/查看伙伴**
            #   要用的接口 ⇒ 多发字段会让客户端拿不到干净数据（用户报障"无法上场伙伴"）。
            out = (w_u16(int((found or {}).get('bid', hb)) & 0xffff) +
                   w_u8(int((found or {}).get('lev', 1)) & 0xff))
            pkt = pack_frame(10402, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 10402 SC_10402 bid=%s lev=%s (%d bytes)'
                % ((found or {}).get('bid', hb), (found or {}).get('lev'), len(pkt)))
            return
        if cmd in (11701, 11702, 11703, 11704):
            # \u805a\u5b9d\u76c6**\u5e73\u884c\u65cf**\uff0811701~11704\uff09\u2014\u2014 \u771f\u673a\u4e5f\u5728\u8bf7\u6c42\u3001\u539f\u5148\u65e0\u4eba\u5e94\u7b54\u3002
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\uff1b\u4e0e 11710~11713 \u540c\u6784\u3002
            if cmd == 11703:
                rs = self.cfg.get('jubaopen_records_server') or []
                rm = self.cfg.get('jubaopen_records_self') or []
                out = (w_u8(int(self.cfg.get('jubaopen_get_times', 0)) & 0xff) +
                       w_u8(int(self.cfg.get('jubaopen_all_times', 0)) & 0xff) +
                       w_u32(int(self.cfg.get('jubaopen_reward_gold', 0))) +
                       w_str(str(self.cfg.get('jubaopen_one_name', ''))) +
                       w_u32(int(self.cfg.get('jubaopen_one_coin', 0))) +
                       w_u16(len(rs)) + w_u16(len(rm)))
                for r in rs:
                    out += (w_str(str(r.get('name', ''))) + w_u8(int(r.get('id', 0)) & 0xff) +
                            w_u32(int(r.get('val', 0))))
                for r in rm:
                    out += w_u8(int(r.get('id', 0)) & 0xff) + w_u32(int(r.get('val', 0)))
                pkt = pack_frame(11703, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 11703 SC_11703 get_times=%s (%d bytes)'
                    % (self.cfg.get('jubaopen_get_times', 0), len(pkt)))
                return
            if cmd == 11702:
                pkt = pack_frame(11702, w_u8(1) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 11702 SC_11702 code=1 (%d bytes)' % len(pkt))
                return
            # 11701 / 11704
            pkt = pack_frame(cmd, w_u8(1) + w_str('') + w_u8(0))
            self.request.sendall(pkt)
            log('tcp.log', '  << %d SC_%d code=1 (%d bytes)' % (cmd, cmd, len(pkt)))
            return
        if cmd in (11710, 11711, 11712, 11713):
            # 聚宝盆（客户端 game/jubaopen/jubaopen_ctrl.luac 注册 11710~11713）
            #   11710 CS{type:u8}        -> SC{type,get_times,record_server:table(name,id),record_self:table(id)}
            #   11711 CS（空）         -> SC{code,msg,id}
            #   11712 CS{type:u8,count:u8} -> SC{code,type,msg,Items:table(bid:u32,num:u8)}   ★ 抽取
            #   11713 CS（空）         -> SC{code,msg}
            # 依据：protocol/manual.md（均无 D|Dsc*| 子表 ⇒ 安全）。
            # ★ 奖池来自 config 的 `jubaopen_pool`（[{bid,num,weight}]），
            #   **原版奖池未取证** ⇒ 默认空（抽不出东西），不编造。
            rid = role_state(self.cfg).get('rid', 1001)
            if cmd == 11710:
                t = body[0] if len(body) >= 1 else 0
                rs = self.cfg.get('jubaopen_records_server') or []
                rm = self.cfg.get('jubaopen_records_self') or []
                out = (w_u8(t) + w_u8(int(self.cfg.get('jubaopen_get_times', 0)) & 0xff) +
                       w_u16(len(rs)) + w_u16(len(rm)))
                for r in rs:
                    out += w_str(str(r.get('name', ''))) + w_u8(int(r.get('id', 0)) & 0xff)
                for r in rm:
                    out += w_u8(int(r.get('id', 0)) & 0xff)
                pkt = pack_frame(11710, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 11710 SC_11710 type=%d get_times=%s (%d bytes)'
                    % (t, self.cfg.get('jubaopen_get_times', 0), len(pkt)))
                return
            if cmd == 11711:
                pkt = pack_frame(11711, w_u8(1) + w_str('') + w_u8(0))
                self.request.sendall(pkt)
                log('tcp.log', '  << 11711 SC_11711 code=1 (%d bytes)' % len(pkt))
                return
            if cmd == 11713:
                pkt = pack_frame(11713, w_u8(1) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 11713 SC_11713 code=1 (%d bytes)' % len(pkt))
                return
            # ---- 11712 抽取 ----
            t = body[0] if len(body) >= 1 else 0
            cnt = body[1] if len(body) >= 2 else 1
            if cnt <= 0:
                cnt = 1
            pool = self.cfg.get('jubaopen_pool') or []
            # ★★ 修正（用户报障“聚宝盆不消耗宝石”）：
            #   原实现**先抽后入包，完全不扣费** ⇒ 可以无限抽。
            #   现：按 config 的 `jubaopen_cost` 先校验、再扣费，不足则直接拒绝。
            #   ★ 币种默认 `gold`（=钻石）——依据：实测界面读数定死
            #     “钻石 = gold(code 1)”（见 dsh_admin.ps1 头部的定论记录）。
            _cost = self.cfg.get('jubaopen_cost') or {}
            _asset = str(_cost.get('asset', 'gold'))
            _per = int(_cost.get('per_draw', 0) or 0)
            _total_cost = _per * cnt
            if _total_cost > 0:
                _have = int((db_get_assets(rid) or {}).get(_asset, 0) or 0)
                if _have < _total_cost:
                    pkt = pack_frame(11712, w_u8(0) + w_u8(t) +
                                     w_str('%s \u4e0d\u8db3\uff08\u9700 %d\uff0c\u6709 %d\uff09'
                                           % (_asset, _total_cost, _have)) +
                                     w_u16(0))
                    self.request.sendall(pkt)
                    log('tcp.log', '  << 11712 SC_11712 code=0 (%s \u4e0d\u8db3 %d/%d)'
                        % (_asset, _have, _total_cost))
                    return
                db_add_assets(rid, {_asset: -_total_cost})
                try:
                    live_push(self.cfg, 'jubaopen_cost')
                except Exception:
                    pass
                log('tcp.log', '  ** 11712 \u62bd\u53d6\u6263\u8d39 %s=%d (cnt=%d)'
                    % (_asset, _total_cost, cnt))
            got = []
            if pool:
                import random as _rnd
                total = sum(max(0, int(p.get('weight', 0))) for p in pool) or 0
                for _ in range(cnt):
                    if total <= 0:
                        pick = pool[_rnd.randrange(len(pool))]
                    else:
                        r = _rnd.uniform(0, total); acc = 0; pick = pool[-1]
                        for p in pool:
                            acc += max(0, int(p.get('weight', 0)))
                            if r <= acc:
                                pick = p; break
                    got.append((int(pick.get('bid', 0)), int(pick.get('num', 1)) or 1))
            for bid, num in got:
                db_bag_add(rid, bid, num)
            if got:
                try:
                    items = db_bag_get(rid, BAG_MAIN)
                    bc = getattr(self, '_last_bag_code', BAG_MAIN)
                    self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
                except Exception:
                    pass
            out = (w_u8(1) + w_u8(t) + w_str('') + w_u16(len(got)))
            for bid, num in got:
                out += w_u32(bid) + w_u8(min(255, num) & 0xff)
            pkt = pack_frame(11712, out)
            self.request.sendall(pkt)
            log('tcp.log', '  ** 11712 聚宝盆抽取 type=%d count=%d ⇒ %r'
                % (t, cnt, got))
            return
        if cmd == 10512:
            # CS_10512{eqm_item_id:u32, bag_item_id:u32, bag_pos:u8, hero_bid:u32}
            #   \u2192 SC_10512{code:u8, msg:string, eqm_item_id:u32, bag_item_id:u32, bag_pos:u8, hero_bid:u32}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u2605 **\u5378\u4e0b\u88c5\u5907**\uff1a\u628a\u88c5\u5907\u69fd\u91cc\u7684\u4e1c\u897f\u653e\u56de\u80cc\u5305\u6307\u5b9a\u4f4d\u7f6e\u3002
            eqm_item_id = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            bag_item_id = struct.unpack_from('>I', body, 4)[0] if len(body) >= 8 else 0
            bag_pos = body[8] if len(body) >= 9 else 0
            hero_bid = struct.unpack_from('>I', body, 9)[0] if len(body) >= 13 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            found = None
            for e in db_equip_all(rid):
                if int(e['item_id']) == eqm_item_id or int(e['bid']) == bag_item_id:
                    found = e
                    break
            if found is None:
                pkt = pack_frame(10512, w_u8(0) + w_str('no such equip %d' % eqm_item_id) +
                                 w_u32(eqm_item_id) + w_u32(bag_item_id) + w_u8(bag_pos) +
                                 w_u32(hero_bid))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10512 SC_10512 code=0 (\u88c5\u5907 %d \u4e0d\u5b58\u5728)' % eqm_item_id)
                return
            db_equip_take(rid, int(found['slot']))
            db_bag_add(rid, int(found['bid']), 1)
            try:
                items = db_bag_get(rid, BAG_MAIN)
                bc = getattr(self, '_last_bag_code', BAG_MAIN)
                # ★ 2026-10-17：卸装后推 **10500**（增量添加）+ 10510（格子数）；
                #   装备槽腾空由请求-应答本身（CS_10512/SC_10512）交代，不需要 10502
                #   （主动推 10502 会被客户端忽略，见文档 §8.3）。
                self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
                push_10510(self, rid, bc)
            except Exception:
                pass
            pkt = pack_frame(10512, w_u8(1) + w_str('') + w_u32(int(found['item_id'])) +
                             w_u32(int(found['bid'])) + w_u8(bag_pos) + w_u32(hero_bid))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 10512 \u5378\u4e0b\u88c5\u5907 slot=%s bid=%d \u21d2 \u56de\u80cc\u5305'
                % (found['slot'], found['bid']))
            return
        if cmd == 10554:
            # CS_10554{from_code:u8, target_code:u8, item_id:u32}
            #   \u2192 SC_10554{code:u8, msg:string, from_code:u8, target_code:u8}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u2605\u2605 **\u8de8\u56ca\u79fb\u52a8**\uff08\u80cc\u5305 \u2194 \u4ed3\u5e93\uff09\u2014\u2014 \u8fd9\u662f\u4ed3\u5e93\u771f\u6b63\u53ef\u7528\u7684\u5173\u952e\u3002
            #   \u56ca\u53f7\u8bed\u4e49\u5df2\u53d6\u8bc1\uff1a1=\u80cc\u5305\uff0c4=\u4ed3\u5e93\uff08BackPackConst.Bag_Code\uff09\u3002
            frm = body[0] if len(body) >= 1 else BAG_MAIN
            to = body[1] if len(body) >= 2 else BAG_MAIN
            item_id = struct.unpack_from('>I', body, 2)[0] if len(body) >= 6 else 0
            rid = role_state(self.cfg).get('rid', 1001)
            # \u2605\u2605 \u4fee\u6b63\uff08\u7528\u6237\u6307\u51fa\u7684\u5df2\u77e5\u7f3a\u53e3\uff09\uff1a
            #   \u539f\u5b9e\u73b0\u5728 frm/to \u4e3a 2/3\uff08\u88c5\u5907\u680f\uff09\u65f6\u8bfb\u7684\u662f `bag_items`
            #   \u21d2 **\u88c5\u5907\u2194\u4ed3\u5e93 \u4e0d\u4e92\u901a**\u3002
            #   \u73b0\u7edf\u4e00\u8d70 `bag_items_of` / `bag_take_one` / `bag_put_one`\uff0c
            #   \u6309 `BackPackConst.Bag_Code` \u5206\u6d3e\uff1a1=\u80cc\u5305 2=\u89d2\u8272\u88c5\u5907 3=\u4f19\u4f34\u88c5\u5907 4=\u4ed3\u5e93\u3002
            row = None
            for it in bag_items_of(rid, frm):
                if int(it.get('item_id') or 0) == item_id:
                    row = it
                    break
            if row is None:
                pkt = pack_frame(10554, w_u8(0) + w_str('no such item %d in bag %d' % (item_id, frm)) +
                                 w_u8(frm) + w_u8(to) + w_u32(item_id))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10554 SC_10554 code=0 (item_id=%d \u4e0d\u5728\u56ca %d)' % (item_id, frm))
                return
            qty = int(row.get('quantity') or 1)
            bid = int(row.get('bid') or 0)
            # \u2605 \u9884\u68c0\uff1a\u88c5\u5907\u76ee\u6807\u4f1a**\u62d2\u7edd\u975e\u88c5\u5907**
            if to in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP) and equip_slot_for(rid, bid, self.cfg) is None:
                pkt = pack_frame(10554, w_u8(0) + w_str('\u8be5\u7269\u54c1\u4e0d\u662f\u88c5\u5907\uff0c\u4e0d\u80fd\u653e\u5165\u88c5\u5907\u680f') +
                                 w_u8(frm) + w_u8(to) + w_u32(item_id))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10554 SC_10554 code=0 (bid=%d \u975e\u88c5\u5907\uff0c\u62d2\u7edd\u5165\u88c5\u5907\u680f)' % bid)
                return
            # \u2605\u2605 \u5b89\u5168\u95f8\uff082026-09-18\uff09\uff1a\u88c5\u5907\u2194\u5176\u4ed6\u56ca\u7684\u79fb\u52a8**\u6682\u65f6\u62d2\u7edd**\u3002
            #   \u539f\u56e0\uff1a\u8be5\u8def\u5f84\u5728\u771f\u673a\u4e0a**\u4e22\u5931\u8fc7\u7269\u54c1**\uff08\u5b9e\u6d4b\uff1a41601 / 41401 / 41801\uff09\u2014\u2014
            #   \u4e0b\u4e00\u884c\u7684 `bag_take_one` \u5148\u5220\u3001`bag_put_one` \u82e5\u5931\u8d25\u5219\u7269\u54c1\u76f4\u63a5\u6d88\u5931\u3002
            #   \u5728**\u5b8c\u6574\u5b9e\u73b0\u5e76\u9a8c\u8bc1\u56de\u6eda**\u4e4b\u524d\uff0c\u5b81\u53ef\u62d2\u7edd\uff0c\u4e0d\u80fd\u4e22\u6570\u636e\u3002
            if frm in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP) or to in (BAG_ROLE_EQUIP, BAG_HERO_EQUIP):
                pkt = pack_frame(10554, w_u8(0) +
                                 w_str('\u88c5\u5907\u680f\u7684\u8de8\u56ca\u79fb\u52a8\u6682\u4e0d\u652f\u6301') +
                                 w_u8(frm) + w_u8(to) + w_u32(item_id))
                self.request.sendall(pkt)
                log('tcp.log', '  << 10554 SC_10554 code=0 (\u88c5\u5907\u8de8\u56ca\u79fb\u52a8\u5df2\u5b89\u5168\u62d2\u7edd frm=%d to=%d)'
                    % (frm, to))
                return
            # \u2605\u2605 \u5168\u7a0b\u5f02\u5e38\u4fdd\u62a4 + **\u5931\u8d25\u56de\u6eda**\uff082026-09-18\uff09
            #   \u7a0b\u5e8f\u8fb9\u8fb9\uff1a\u4e4b\u524d `bag_take_one` \u5148\u5220\u3001`bag_put_one` \u82e5\u5931\u8d25/\u629b\u5f02\u5e38\uff0c
            #   **\u7269\u54c1\u76f4\u63a5\u6d88\u5931**\uff08\u771f\u673a\u5b9e\u6d4b\u4e22\u5931 41601 / 41401 / 41801\uff09\u3002
            #   \u73b0\uff1a\u79fb\u9664\u524d\u5148\u8bb0\u4e0b\u6e90\u4fe1\u606f \u2192 \u5199\u5165\u76ee\u6807\uff1b
            #   **\u5199\u5165\u5931\u8d25\u6216\u629b\u5f02\u5e38\u5219\u628a\u7269\u54c1\u653e\u56de\u6e90\u56ca**\uff0c\u5e76\u56de code=0\u3002
            took = bag_take_one(rid, frm, item_id)
            if took is None:
                pkt = pack_frame(10554, w_u8(0) + w_str('take failed %d' % item_id) +
                                 w_u8(frm) + w_u8(to) + w_u32(item_id))
                self.request.sendall(pkt)
                log('tcp.log', '  !! 10554 take failed item_id=%d frm=%d' % (item_id, frm))
                return
            ok = None
            try:
                ok = bag_put_one(rid, to, bid, item_id, qty, 0, cfg=self.cfg)
            except Exception as _e:
                log('tcp.log', '  !! 10554 put raised: %r' % (_e,))
            if not ok:
                try:
                    bag_put_one(rid, frm, bid, item_id, qty, 0, cfg=self.cfg)
                    log('tcp.log', '  !! 10554 \u5199\u5165\u76ee\u6807\u5931\u8d25 \u21d2 **\u5df2\u56de\u6eda** bid=%d \u5230\u56ca%d'
                        % (bid, frm))
                except Exception as _e2:
                    log('tcp.log', '  !!! 10554 **\u56de\u6eda\u4e5f\u5931\u8d25** bid=%d: %r' % (bid, _e2))
                pkt = pack_frame(10554, w_u8(0) + w_str('\u79fb\u52a8\u5931\u8d25\uff0c\u5df2\u539f\u5730\u8fd4\u8fd8') +
                                 w_u8(frm) + w_u8(to) + w_u32(item_id))
                self.request.sendall(pkt)
                return
            # \u2605\u2605 \u4fee\u6b63\uff08\u7528\u6237\u62a5\u969c\u201c\u4ed3\u5e93\u80cc\u5305\u4e0d\u4e92\u901a\u201d\uff09\uff1a
            #   \u539f\u5b9e\u73b0\u63a8\u7684\u662f SC_10502\uff08\u8bf7\u6c42-\u5e94\u7b54\u578b\uff09\uff1b\u5ba2\u6237\u7aef\u53ea\u5728
            #   **\u4e3b\u52a8\u53d1 CS_10502 \u540e**\u624d\u5904\u7406 SC_10502\uff0c\u4e3b\u52a8\u63a8\u7684\u4f1a\u88ab\u5ffd\u7565
            #   \u21d2 \u5ba2\u6237\u7aef\u672c\u5730\u72b6\u6001\u4e0d\u66f4\u65b0 \u21d2 \u62ff\u65e7 item_id \u91cd\u8bd5 \u21d2 code=0
            #   \u21d2 \u770b\u8d77\u6765\u201c\u4e0d\u4e92\u901a\u201d\u3002
            #   \u6539\u7528**\u4e3b\u52a8\u63a8\u9001\u578b**\uff1a10503 \u544a\u77e5\u6e90\u56ca\u5220\u9664\uff0c10500 \u544a\u77e5\u76ee\u6807\u56ca\u65b0\u589e\u3002
            try:
                self.request.sendall(pack_frame(10503, w_u8(frm) + w_u16(1) + w_u32(item_id)))
                cur = [x for x in bag_items_of(rid, to) if int(x.get('bid') or 0) == bid]
                if cur:
                    self.request.sendall(pack_frame(10500, w_u8(to) + build_bag_items(cur[:1])))
            except Exception as e:
                log('tcp.log', '  !! 10554 push failed: %r' % (e,))
            pkt = pack_frame(10554, w_u8(1) + w_str('') + w_u8(frm) + w_u8(to) + w_u32(item_id))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 10554 \u79fb\u52a8 bid=%d x%d \u4ece\u56ca%d \u5230\u56ca%d' % (bid, qty, frm, to))
            return
        if cmd == 16400:
            # ★★ R48：成就面板（真机 **450 次**，原先落通用集合回全零）
            #   CS{type:C} → SC{type:C, chengjiu:T{bid:I,val:H,time:I},
            #                   chengjiu_has:T{bid:I,time_out:I,state:C},
            #                   chengjiu_rate:T{bid:I,rate:C}}
            #   · `chengjiu`      = 有进度的成就（val=当前进度，取 DB）
            #   · `chengjiu_rate` = rate = 进度%（由 当前/目标 推导，目标取自
            #                       成就表的 `val`；封顶 100）
            #   · `chengjiu_has`  = **留空**：`state` 语义（可领/已领）**未取证**，
            #                       按纪律不猜（16401 领取流程亦未取证）
            #   · `time` = 0（时间戳语义未取证）
            _type = body[0] if len(body) >= 1 else 0
            _rid = role_state(self.cfg).get('rid', 1001)
            _prog = db_chengjiu_get(_rid)
            _cfgj = chengjiu_cfg()
            rows, rates = [], []
            for _b, _cur in _prog.items():
                _c = _cfgj.get(str(_b)) or {}
                _tgt = int(_c.get('val') or 0)
                rows.append((int(_b), int(_cur)))
                if _tgt > 0:
                    _r = 100 if _cur >= _tgt else int(_cur * 100 / _tgt)
                else:
                    _r = 0
                rates.append((int(_b), max(0, min(100, _r))))
            rows.sort()
            rates.sort()
            out = w_u8(_type & 0xff) + w_u16(len(rows))
            for _b, _v in rows:
                out += w_u32(_b) + w_u16(_v & 0xffff) + w_u32(0)
            out += w_u16(0)                     # chengjiu_has 空（state 未取证）
            out += w_u16(len(rates))
            for _b, _r in rates:
                out += w_u32(_b) + w_u8(_r & 0xff)
            self.request.sendall(pack_frame(16400, out))
            log('tcp.log', '  << 16400 SC_16400 type=%d chengjiu=%d rate=%d (%d bytes)'
                % (_type, len(rows), len(rates), len(out)))
            return

        if cmd == 15405:
            # ★★ R48：挂机轮次 —— CS 空 → SC_15405{loop_count:u16}
            #   真机证据链：点「日常/参与」后客户端发 15405，服务端回通用零值 0
            #   ⇒ 此后**再无任何命令**（挂机不启动）。等级(150/70)与地图数据均已排除。
            #   ⚠ 语义（已完成/目标）未取证 ⇒ 默认 0 维持现状，实验时用 admin 调高。
            _rid = role_state(self.cfg).get('rid', 1001)
            _lc = db_guaji_get(_rid)
            self.request.sendall(pack_frame(15405, w_u16(_lc & 0xffff)))
            log('tcp.log', '  << 15405 SC_15405 loop_count=%d' % _lc)
            return
        if cmd == 15402:
            # ★★ R48：挂机任务 → 地图/坐标  CS{mission_bid:u32}
            #   → SC{mission_bid:u32, map_bid:u32, x:u32, y:u32}
            #   ★★ **这条的 CS 里带 `mission_bid`** ⇒ 它就是"挂机线 ↔ 任务"的映射！
            #      日志里会原样记下客户端发来的 bid（用来填 `_chengjiu_map.json`）。
            #   `map_bid/x/y` 由等级段（`config_guaji`）+ 地图默认出生点推出。
            _mb = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _lev = int(role_state(self.cfg).get('lev', 1))
            _spot = guaji_spot_for_lev(_lev) or {}
            _map = int(_spot.get('map_bid') or 0)
            _x, _y = map_def_xy(_map)
            self.request.sendall(pack_frame(
                15402, w_u32(_mb) + w_u32(_map) + w_u32(_x) + w_u32(_y)))
            # ★ R53：把本轮的挂机任务记下来 —— `15403`（杀怪上报）与 `15404`（轮次结束推送）
            #   都需要知道"当前挂的是哪条任务线"。
            if _mb:
                db_guaji_update(role_state(self.cfg).get('rid', 1001), mission_bid=_mb)
            log('tcp.log', '  ★★ 15402 挂机任务 mission_bid=%d lev=%d ⇒ map_bid=%d (%d,%d)'
                % (_mb, _lev, _map, _x, _y))
            return
        if cmd == 15403:
            # ★★ R53：挂机**杀怪上报** —— `CS{mon_bid:u32}` → `SC{code:u8, msg:string}`
            #   客户端消费点（`ghost_ctrl.luac` proto#31 `handle15403`）：
            #       GlobalEvent:getInstance():message(data.msg)     ← ★ msg 会**直接弹给玩家**
            #   ⇒ 因此 `msg` 只能是"真话"：要么空（不打扰），要么是真实进度文本。
            #   本实现（不猜轮次规则）：
            #     · `mon_bid` 必须是**真实存在的挂机怪**（`config_guaji` 的 8 条 + `Config.Mon`）
            #       否则回 `code=0 + msg`（不静默接受垃圾输入）
            #     · 合法 ⇒ `kill_count` +1 落库，回 `code=1 + msg=''`（不弹任何提示）
            #     · **不自动推 `15404`** —— "一轮 = 几只怪"没有取证，猜一个阈值等于编造规则。
            #       需要结束本轮时，用 `/DSH_ADMIN/guaji_end`（实验旋钮）显式推。
            _mon = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
            _rid = role_state(self.cfg).get('rid', 1001)
            # ★ C3.3-D：服务端权威收紧（A 分片审计缺陷：旧版信任客户端 mon_bid 即发奖）。
            #   (a) 会话校验：必须已启动在线挂机链（15400→15402 已落 mission_bid），
            #       无挂机状态直接拒——裸连不能靠反复发 15403 刷奖励。
            #   (b) 频率限制：同一 rid 两次杀怪上报最小间隔 guaji_kill_min_sec（默认 1.0s，
            #       防御 spam；非原版玩法规则，原版限次规则无证据 ⇒ 不编造）。
            #   (c) mon_bid 存在性校验：保留旧版（必须在 config_guaji 8 点或 mon_def 有名）。
            _st_now = db_guaji_state(_rid)
            if int(_st_now.get('mission_bid') or 0) == 0:
                self.request.sendall(pack_frame(15403, w_u8(0) + w_str('请先启动挂机')))
                log('tcp.log', '  << 15403 杀怪上报 mon_bid=%d ⇒ code=0（无挂机会话 mission_bid=0，拒绝）'
                    % _mon)
                return
            _min_gap = float(self.cfg.get('guaji_kill_min_sec', 1.0))
            try:
                _c = db_conn()
                _ua = _c.execute('SELECT updated_at FROM guaji_state WHERE rid=?',
                                 (_rid,)).fetchone()
                db_release(_c)
                _dt = time.time() - int(_ua[0]) if _ua else 999.0
            except Exception:
                _dt = 999.0
            if _dt < _min_gap:
                self.request.sendall(pack_frame(15403, w_u8(0) + w_str('操作过快')))
                log('tcp.log', '  << 15403 杀怪上报 mon_bid=%d ⇒ code=0（距上次 %.2fs < %.1fs，频率拦截）'
                    % (_mon, _dt, _min_gap))
                return
            _known = set(int(s.get('mon_bid') or 0) for s in guaji_spots())
            _d = mon_def(_mon) if _mon else {}
            if _mon and (_mon in _known or (_d and _d.get('name'))):
                _st = db_guaji_update(_rid, kill_count=db_guaji_state(_rid)['kill_count'] + 1)
                self.request.sendall(pack_frame(15403, w_u8(1) + w_str('')))
                # [P-AFK] 合法挂机击杀 => 掉落 grant 幂等（20003 掉落组）
                try:
                    from drop import service as _dropsvc
                    _r = _dropsvc.resolve(20003)
                    _aw = []
                    if _r.get("coin"): _aw.append({"kind":"asset","code":"gold","amount":_r["coin"]})
                    for _b,_n in _r.get("items",[]): _aw.append({"kind":"item","bid":_b,"amount":_n})
                    from reward.service import grant as _grant
                    _grant(int(_rid), _aw, "guaji_kill:%d:%d" % (int(_rid), _st["kill_count"]), source="guaji_kill")
                except Exception as _e:
                    log("tcp.log", "  !! 15403 grant err: %r" % (_e,))
                # ★★★ C5-A：挂机击杀**也要推进任务条件** —— 这才是原版"击杀类任务"的主通道。
                #   证据：任务 75001–75006 名「狂暴魂兽」，条件 `kill_type_mon=8`，
                #   其第二个 progress 元素正是挂机图 `[10002,10003,10004,10005]`
                #   ⇒ 这 6 条任务的设计触发点**就是挂机刷怪**，而不是在场景里手动点怪。
                #   同理 `kill_scene_mon` 在挂机语境下应记"当前挂机图"。
                #   纪律：只在本分支推进（mon_bid 真实 + 会话有效 + 未触发频率拦截），
                #   与掉落 grant 同一道门；不在裸连/垃圾输入上推进。
                try:
                    _lev_afk = int(role_state(self.cfg).get('lev') or 1)
                    _spot_afk = guaji_spot_for_lev(_lev_afk) or {}
                    _scene_afk = int(_spot_afk.get('map_bid') or 0)
                    _mt_afk = mon_type_of(_mon)
                    _hit_afk = list(mission_progress_advance(_rid, 'fight_mon', _mon, 1) or [])
                    if _mt_afk is not None:
                        _hit_afk += list(mission_progress_advance(
                            _rid, 'kill_type_mon', _mt_afk, 1) or [])
                    if _scene_afk:
                        _hit_afk += list(mission_progress_advance(
                            _rid, 'kill_scene_mon', _scene_afk, 1) or [])
                    if _hit_afk:
                        _ms_afk = mission_rows(self.cfg, _rid)
                        push_to_rid(_rid, pack_frame(12405, build_12400(_ms_afk)))
                        log('tcp.log', '  ** 15403 任务条件推进 mon=%d type=%s scene=%d -> %r'
                                       '（12405 已补推）' % (_mon, _mt_afk, _scene_afk, _hit_afk))
                except Exception as _eafk:
                    log('tcp.log', '  !! 15403 任务推进失败: %r' % (_eafk,))
                log('tcp.log', '  << 15403 杀怪上报 mon_bid=%d(%s) ⇒ code=1 累计击杀=%d 任务=%d'
                    % (_mon, (_d or {}).get('name') or '挂机怪', _st['kill_count'],
                       _st['mission_bid']))
            else:
                _msg = '未知怪物(%d)' % _mon
                self.request.sendall(pack_frame(15403, w_u8(0) + w_str(_msg)))
                log('tcp.log', '  << 15403 杀怪上报 mon_bid=%d ⇒ code=0（不在挂机怪表里，拒绝计数）'
                    % _mon)
            return
        if cmd == 15400:
            # ★★ R48：**启动挂机** —— CS 空 → SC_15400{code:u8, msg:string}
            #   原先在 _UNSUPPORTED_ACTION_CMDS 回 code=0「该功能暂未开放」
            #   ⇒ 挂机链断在这里（真机：15405 → 15400 → 之后什么都没了）。
            #   改回**成功**，客户端才会继续发 `15402{mission_bid}`。
            #   ⚠ 这里只做"允许启动"，**不代表挂机玩法已实现**：
            #     真正的刷怪/结算仍缺（见 15401/15402）。
            self.request.sendall(pack_frame(15400, w_u8(1) + w_str('')))
            log('tcp.log', '  << 15400 SC_15400 code=1(允许启动挂机)')
            # [P-AFK] 主动补推 SC_15405 loop_count（激活巡逻按钮 UI 态尝试，帧格式逐字对齐旧链）
            try:
                _rid5 = role_state(self.cfg).get('rid', 1001)
                _lc5 = db_guaji_get(_rid5)
                self.request.sendall(pack_frame(15405, w_u16(_lc5 & 0xffff)))
                log('tcp.log', '  << [P-AFK] 主动推 15405 loop_count=%d' % _lc5)
            except Exception as _e5:
                log('tcp.log', '  !! 15405 主动推异常: %r' % (_e5,))
            # ★★★ R60（由 R59 取证直接推出）：**主动推 `SC_15402`**
            #   R59 把 `mon_hongchen` 的创建路径查完了，全 `ghost_ctrl` 只有两处会 new：
            #     · proto#30 `handle15402` —— **收到服务端 SC_15402** 时
            #     · proto#33 `killHuanBoss` —— 点击场景挂机怪时（而那要先有怪 ⇒ 仍要求实例已存在）
            #   而 `ghost_mon` proto#4 里"发 `CS_15402`"的代码，前提正是 `self.mon_hongchen` 已存在。
            #   ⇒ **"客户端先发 15402"这条链不存在**；必须由服务端先给 `SC_15402`。
            #     这也解释了 R48 当年"点 15400 之后客户端立刻发 15402"——
            #     那是在我们**答了**它之后的反应，而不是它自己发起的。
            #   载荷与应答实现**完全同源**（`verify_guaji.py` 已验证）：
            #     mission_bid 取 `config.guaji_mission_bid`（默认 10010）
            #       —— 依据：R48 真机抓到的 `CS_15402{mission_bid=10010}`（学院/红尘线）
            #     map_bid/x/y 取 `config_guaji` 的等级段 + `config_map` 的 def_x/def_y
            if self.cfg.get('guaji_push_15402', True):
                _rid = role_state(self.cfg).get('rid', 1001)
                _mb = int(self.cfg.get('guaji_mission_bid') or 10010)
                _lev2 = int(role_state(self.cfg).get('lev', 1))
                _spot2 = guaji_spot_for_lev(_lev2) or {}
                _map2 = int(_spot2.get('map_bid') or 0)
                _x2, _y2 = map_def_xy(_map2)
                # ★★★ R66（探针实测推出的修正）：
                #   `ghcreate` 上报证明 `createMon()` **四个条件全过、怪真的建出来了**
                #   （`done_mon_id=30068`）—— 但截图上看不见怪，因为
                #   `SC_15402` 给的 `(x,y)` 是**地图默认出生点 (10,58)**，而玩家在 (68,61)，
                #   相距 58 格 ⇒ 怪在视野外。**建怪是纯客户端行为，不会再有网络包**，
                #   所以前十轮用"客户端有没有发新包"当判据**本身就是错的**。
                #   ⇒ 这里改成**在玩家脚下生成**（取角色当前坐标），怪才会出现在屏幕上。
                _le3 = getattr(self, '_last_enter', None)
                if _le3 and int(_le3[0]) == int(_map2):
                    _x2, _y2 = int(_le3[1]), int(_le3[2])
                elif self.cfg.get('guaji_15402_use_role_pos', True):
                    _rp = role_with_saved_pos(self.cfg)
                    _x2 = int(_rp.get('x') or _x2)
                    _y2 = int(_rp.get('y') or _y2)
                # ★★★ R62（由 R61 的反汇编直接推出）：
                #   `ghost_mon` proto#3 `createMon()` 的**第三个早退条件**是
                #       if SceneModel:getInstance():getSceneId() ~= self.mon_cfg.map_bid then return end
                #   ⇒ **玩家必须已经在挂机图里**，客户端才会把怪加进场景（SCENE_CLIENT_ADD）。
                #   而我们之前四环跑完时玩家仍在 10001（史莱克城）⇒ 客户端收到 SC_15402 后
                #   `createMon()` 立刻 return，**外部表现为"毫无反应"**。
                #   本分支按该条件补上"先进场景"：推 10200(挂机图) + 10201(该图图块)，
                #   再推 15402。默认关闭（config: guaji_enter_scene），供对照实验。
                if self.cfg.get('guaji_enter_scene') and _map2:
                    try:
                        self._send_10200(_map2)
                        _npcs4, _mons4 = scene_quest_extras(self.cfg, _map2)
                        self.request.sendall(pack_frame(
                            10201, build_10201([role_with_saved_pos(self.cfg)],
                                               _npcs4, _mons4, scene_elems(_map2))))
                        log('tcp.log', '  << 10200/10201 送进挂机图 bid=%d（R62 实验：'
                                       'createMon 要求 getSceneId()==mon_cfg.map_bid）' % _map2)
                        # ★★ R63：**必须给客户端时间真的把场景切完**。
                        #   `10200` 与 `15402` 在同一 tick 送达时，客户端处理 15402 时
                        #   `SceneModel:getSceneId()` 很可能还是**旧场景** ⇒
                        #   `createMon()` 的第三个早退条件（`getSceneId()==mon_cfg.map_bid`）
                        #   仍然命中 ⇒ 表现为"收到 15402 但什么都不做"。
                        #   实测（R62）：同 tick 推送下客户端确实毫无反应，所以这里加延时。
                        #   ponytail: 先 sleep 打通链路；要精致化再换定时器，别为一次实验上线程池。
                        time.sleep(float(self.cfg.get('guaji_enter_scene_delay') or 3.0))
                    except Exception as e:
                        log('tcp.log', '  !! R62 送场景失败: %r' % (e,))
                self.request.sendall(pack_frame(
                    15402, w_u32(_mb) + w_u32(_map2) + w_u32(_x2) + w_u32(_y2)))
                db_guaji_update(_rid, mission_bid=_mb)
                log('tcp.log', '  << 15402 主动推 SC_15402 mission_bid=%d map_bid=%d (%d,%d) '
                               '（R60：客户端不发，必须服务端先给）'
                    % (_mb, _map2, _x2, _y2))
            return
        if cmd in (13781, 13786, 13787, 13788, 13789, 10925):
            # 日常面板（客户端 game/daily/daily_ctrl.luac）
            #   13781 CS（空）     -> SC{total_val:u16, huoli_list:table(id,num,val),
            #                             lingqu_list:table(huoli:u16)}
            #   13786 CS（空）     -> SC{week:u8, richang_list:table(id,num),
            #                             status_list:table(id,num)}
            #   13787 CS（空）     -> SC{code, msg, lingqu_list:table(huoli)}
            #   13788 CS（空）     -> SC（空）
            #   13789 CS{huoli:u16} -> SC{code, msg, huoli:u16}
            #   10925 CS{id:u16}    -> SC{id:u16, status:u8, int_args:table(val:u32)}
            # 依据：protocol/manual.md（均无 D|Dsc*| ⇒ 安全）
            # ★ 用户报障“日常面板存在错误” ⇒ **原先无人应答**。
            if cmd == 13781:
                # ★★ R48：活跃度面板 —— 改为 **DB 驱动 + 真实任务表**
                #   SC_13781{total_val:H, huoli_list:T{id:H,num:H,val:H},
                #             lingqu_list:T{huoli:H}}
                #   · `id` = 任务表的 `huoli_id`（三方一致，见上方注释）
                #   · `num`/`val` = 该任务已完成次数 / 已获得活力（DB；没做过=0）
                #   · `total_val` = **Σ val**（由分项求和得出，自洽；非配置直读）
                #   · `lingqu_list` = 已领取档位（DB；没领过=空）
                _rid = role_state(self.cfg).get('rid', 1001)
                _prog = db_daily_get(_rid)
                _rows = []
                for _t in richang_daily_tasks():
                    _hid = int(_t.get('huoli_id') or 0)
                    if _hid <= 0:
                        continue          # huoli_id=0 的任务不计活跃度（见任务表）
                    _p = _prog.get(int(_t.get('id') or 0)) or {'num': 0, 'val': 0}
                    _rows.append((_hid, _p['num'], _p['val']))
                _total = sum(r[2] for r in _rows) & 0xffff
                _lq = db_daily_lingqu(_rid)
                out = w_u16(_total) + w_u16(len(_rows))
                for _hid, _n, _v in _rows:
                    out += w_u16(_hid & 0xffff) + w_u16(_n & 0xffff) + w_u16(_v & 0xffff)
                out += w_u16(len(_lq))
                for _h in _lq:
                    out += w_u16(_h & 0xffff)
                pkt = pack_frame(13781, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 13781 SC_13781 total_val=%d huoli_list=%d lingqu=%d (%d bytes)'
                    % (_total, len(_rows), len(_lq), len(pkt)))
                return
            if cmd == 13786:
                # ★★ R48 已**真机取证**（MuMu，一次点击定论）：
                #   `richang_list{id=H, num=H}` 的 `id` 用**面板 id**（208/205/207…），
                #   `num` 就是面板上的**「次数」**。
                #   证据：给 DB 写 学院任务(num=1) 后重开面板，
                #         真机显示「学院任务 次数 1/10」。
                #   ★ 同时**否证**了另一条路：只给 13781 的 `huoli_list{num=1}` 时，
                #     面板"次数"仍是 0/10（而"活力"会跟着 val 变）
                #     ⇒ `13781.huoli_list.num` **不是**次数。
                #   取数分工（三条都已在真机验证）：
                #     · 拥有活力      ← 13781.total_val
                #     · 每任务活力    ← 13781.huoli_list[huoli_id].val
                #     · 每任务次数    ← **13786.richang_list[面板id].num** ← 本条
                _rid = role_state(self.cfg).get('rid', 1001)
                _prog = db_daily_get(_rid)
                rc = []
                for _t in richang_daily_tasks():
                    _p = _prog.get(int(_t.get('id') or 0)) or {'num': 0, 'val': 0}
                    rc.append({'id': int(_t.get('id') or 0), 'num': _p['num']})
                st = []
                out = w_u8(int(self.cfg.get('richang_week', 0)) & 0xff) + w_u16(len(rc))
                for x in rc:
                    out += w_u16(int(x['id']) & 0xffff) + w_u16(int(x['num']) & 0xffff)
                out += w_u16(len(st))
                for x in st:
                    out += w_u16(int(x.get('id', 0))) + w_u16(int(x.get('num', 0)))
                pkt = pack_frame(13786, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 13786 SC_13786 week=%d richang=%d status=%d (%d bytes)'
                    % (int(self.cfg.get('richang_week', 0)), len(rc), len(st), len(pkt)))
                return
            if cmd == 13787:
                lq = self.cfg.get('huoli_lingqu') or []
                out = w_u8(1) + w_str('') + w_u16(len(lq))
                for x in lq:
                    out += w_u16(int(x.get('huoli', x) if isinstance(x, dict) else x))
                pkt = pack_frame(13787, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 13787 SC_13787 code=1 lingqu=%d (%d bytes)' % (len(lq), len(pkt)))
                return
            if cmd == 13788:
                pkt = pack_frame(13788, b'')
                self.request.sendall(pkt)
                log('tcp.log', '  << 13788 SC_13788 (空) (%d bytes)' % len(pkt))
                return
            if cmd == 13789:
                hv = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
                pkt = pack_frame(13789, w_u8(1) + w_str('') + w_u16(hv))
                self.request.sendall(pkt)
                log('tcp.log', '  << 13789 SC_13789 huoli=%d code=1 (%d bytes)' % (hv, len(pkt)))
                return
            # 10925 活跃度
            mid = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            pkt = pack_frame(10925, w_u16(mid) + w_u8(1) + w_u16(1) + w_u32(0))
            self.request.sendall(pkt)
            log('tcp.log', '  << 10925 SC_10925 id=%d status=1 (%d bytes)' % (mid, len(pkt)))
            return
        if cmd == 14099:
            # ★★★ R92：**阵型属性汇总** —— 原先落通用默认响应（空 attr_list）
            #   真机在发（最近 2 万行 16 次），面板因此没有属性可显示。
            #   规格：SC_14099{attr_list:table(attr:uint8, value:uint32)}
            #   `attr` 用 **`AttrKey2Id`**（`server/_attr_data.json`，64 条，来自 config_attr）；
            #   发哪些用 **`AttrKeyIsShow`**（同文件，10 条 = 面板显示集合）；
            #   值取**玩家真实属性**（`role_attr_dict`，与 10303/10306/20100 同一源）。
            _ad = role_attr_dict(self.cfg)
            _ids = _attr_key2id()
            _show = _attr_show_keys()
            _pairs = []
            for _k in _show:
                _aid = _ids.get(_k)
                if _aid is None:
                    continue
                _v = int(_ad.get(_k) or 0)
                _pairs.append((int(_aid) & 0xff, _v & 0xFFFFFFFF))
            _out = w_u16(len(_pairs))
            for _aid, _v in _pairs:
                _out += w_u8(_aid) + w_u32(_v)
            # ⚠ 必须带上命令号：`pack_frame(cmd, body)`。
            #   第一版写成 `pack_frame(_out)` ⇒ 把 bytes 当 cmd ⇒ struct.pack 抛
            #   `ValueError` 并**断开连接**（客户端表现为"无响应"）。
            self.request.sendall(pack_frame(14099, _out))
            log('tcp.log', '  << 14099 SC_14099 attr_list=%d %s (%d bytes)'
                % (len(_pairs), [(a, v) for a, v in _pairs[:4]], len(_out) + 6))
            return
        if cmd in (14100, 14101):
            # 签到（客户端 game/dailysign/dailysign_ctrl.luac 注册 14100/14101）
            #   14100 CS（空） -> SC{days:u8, is_get:u8, vip_lev:u8}
            #   14101 CS（空） -> SC{tips:u16, msg, days:u8,
            #                            assets:table(type:u8, count:u32),
            #                            items:table(item_bid:u32, num:u8, is_bind:u8)}
            # 依据：protocol/manual.md（无 D|Dsc*| ⇒ 安全）。
            # ★ 用户报障“签到奖励无法领取” ⇒ **14101 原先无人应答**。
            rid = role_state(self.cfg).get('rid', 1001)
            days = int(self.cfg.get('sign_days', 1))
            if cmd == 14100:
                # ★ on14100 实测读：`resp.data:updateSignData` / `resp.is_get` /
                #   `resp.login_open` ⇒ 字段顺序照定义：{days,is_get,vip_lev}
                # ★★ 2026-09-18 修复（体检发现）：`is_get` 原先读的是 config 的
                #   `sign_is_get`（**恒为 0**），而不是查 `sign_got` 表 ⇒ 签到成功后
                #   客户端仍收到 is_get=0 ⇒ 界面继续显示"可领取"（**这也是用户报的
                #   "签到奖励还是不能领取"的一半原因**）。现改为**查 DB 判定**。
                _got = 1 if db_sign_got(rid, days) else 0
                out = (w_u8(days & 0xff) +
                       w_u8(_got & 0xff) +
                       w_u8(int(self.cfg.get('sign_vip_lev', 0)) & 0xff))
                pkt = pack_frame(14100, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 14100 SC_14100 days=%d (%d bytes)' % (days, len(pkt)))
                return
            # 14101 领取：幂等（不重复发）+ 按 config 发奖
            if db_sign_got(rid, days):
                # ★ SC_14101 完整字段：{tips,msg,days,**assets,items**}
                #   客户端 on14101 @28/@29 实测读 resp.assets / resp.items
                out = (w_u16(0) + w_str('今日已签到') + w_u8(days) +
                       w_u16(0) + w_u16(0))
                pkt = pack_frame(14101, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 14101 SC_14101 tips=0 (已签 %d, %d 字节)' % (days, len(pkt)))
                return
            db_sign_add(rid, days)
            rw = self.cfg.get('sign_rewards') or {}
            day_rw = rw.get(str(days)) or {}
            gave = []
            for a in (day_rw.get('assets') or []):
                db_add_assets(rid, {str(a.get('type', 'gold')): int(a.get('count', 0))})
                gave.append(('asset', a.get('type'), a.get('count')))
            for it in (day_rw.get('items') or []):
                ib = int(it.get('bid', 0))
                if is_valid_item(ib):
                    db_bag_add(rid, ib, int(it.get('num', 1)))
                    gave.append(('item', ib, it.get('num', 1)))
            if gave:
                try:
                    items = db_bag_get(rid, BAG_MAIN)
                    bc = getattr(self, '_last_bag_code', BAG_MAIN)
                    self.request.sendall(pack_frame(10500, w_u8(bc) + build_bag_items(items)))
                except Exception:
                    pass
                live_push(self.cfg, 'sign')
            # ★★ 完整字段（修正）：{tips,msg,days,assets(table type,count),items(table item_bid,num,is_bind)}
            assets = day_rw.get('assets') or []
            items = day_rw.get('items') or []
            out = (w_u16(1) + w_str('') + w_u8(days))
            out += w_u16(len(assets))
            for a in assets:
                out += w_u8(int(a.get('type_code', 1)) & 0xff) + w_u32(int(a.get('count', 0)))
            out += w_u16(len(items))
            for it in items:
                out += (w_u32(int(it.get('bid', 0))) + w_u8(int(it.get('num', 1)) & 0xff) +
                        w_u8(int(it.get('is_bind', 1)) & 0xff))
            pkt = pack_frame(14101, out)
            self.request.sendall(pkt)
            log('tcp.log', '  ** 14101 签到第 %d 天 ⇒ assets=%d items=%d %r (%d 字节)'
                % (days, len(assets), len(items), gave, len(pkt)))
            return
        if cmd in (17800, 17801):
            # 摇钱树（moneytree_ctrl 注册 17800/17801）
            #   17800 CS（空） -> SC{free_count:u8, all_free_count:u8, gold_count:u8, get_coin:u32}
            #   17801 CS（空） -> SC{code, msg}
            # ★ 用户报障“摇钱树无法使用” ⇒ **原先无人应答**。
            if cmd == 17800:
                out = (w_u8(int(self.cfg.get('moneytree_free_count', 1)) & 0xff) +
                       w_u8(int(self.cfg.get('moneytree_all_free', 3)) & 0xff) +
                       w_u8(int(self.cfg.get('moneytree_gold_count', 0)) & 0xff) +
                       w_u32(int(self.cfg.get('moneytree_get_coin', 0))))
                pkt = pack_frame(17800, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 17800 SC_17800 (%d bytes)' % len(pkt))
                return
            # ★ 用户报障“摇一摇了但次数不变、也不发奖” ⇒ **在服务端真正扣次数 + 发奖**。
            _rid = role_state(self.cfg).get('rid', 1001)
            free = int(self.cfg.get('moneytree_free_count', 1))
            if free <= 0:
                pkt = pack_frame(17801, w_u8(0) + w_str('今日次数已用完'))
                self.request.sendall(pkt)
                log('tcp.log', '  << 17801 SC_17801 code=0 (次数已用完)')
                return
            coin = int(self.cfg.get('moneytree_coin_per_use', 1000))
            self.cfg['moneytree_free_count'] = free - 1
            self.cfg['moneytree_get_coin'] = int(self.cfg.get('moneytree_get_coin', 0)) + coin
            db_add_assets(_rid, {'coin': coin})
            # ★ 必须同步到磁盘，否则重启后次数回溡
            # ★ 注：本项目**没有** cfg_save()（只有 CFG_PATH）⇒ 直接写磁盘
            try:
                with open(CFG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(self.cfg, f, ensure_ascii=False, indent=1)
            except Exception as _e:
                log('tcp.log', '  !! moneytree 次数落盘失败: %r' % (_e,))
            live_push(self.cfg, 'moneytree')
            # ★ 回包后立即补推一次 17800，让客户端次数刷新
            out = (w_u8(self.cfg['moneytree_free_count'] & 0xff) +
                   w_u8(int(self.cfg.get('moneytree_all_free', 3)) & 0xff) +
                   w_u8(int(self.cfg.get('moneytree_gold_count', 0)) & 0xff) +
                   w_u32(int(self.cfg.get('moneytree_get_coin', 0))))
            self.request.sendall(pack_frame(17800, out))
            pkt = pack_frame(17801, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  ** 17801 摇钱树 coin=%d→总%d 剩余次数=%d'
                % (coin, self.cfg['moneytree_get_coin'], self.cfg['moneytree_free_count']))
            return
        if cmd in (17600, 17601, 17602):
            # 在线福利（dailysign_ctrl）
            #   17600 CS（空）     -> SC{days:u16, reward:u8, get_day:table(day:u8,num:u8)}
            #   17601 CS{day:u8}  -> SC{tips:u16, msg, days:u8, num:u8}
            #   17602 CS（空）     -> SC{...}
            # ★ 用户报障“在线福利为空” ⇒ **原先无人应答**。
            rid = role_state(self.cfg).get('rid', 1001)
            if cmd == 17600:
                days = int(self.cfg.get('online_days', 1))
                gets = self.cfg.get('online_got') or []
                out = (w_u16(days & 0xffff) + w_u8(int(self.cfg.get('online_reward', 0)) & 0xff) +
                       w_u16(len(gets)))
                for g in gets:
                    out += w_u8(int(g.get('day', 0)) & 0xff) + w_u8(int(g.get('num', 0)) & 0xff)
                pkt = pack_frame(17600, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 17600 SC_17600 days=%d get_day=%d (%d bytes)'
                    % (days, len(gets), len(pkt)))
                return
            if cmd == 17601:
                day = body[0] if len(body) >= 1 else 0
                rw = (self.cfg.get('online_rewards') or {}).get(str(day)) or {}
                gave = []
                for a in (rw.get('assets') or []):
                    db_add_assets(rid, {str(a.get('type', 'coin')): int(a.get('count', 0))})
                    gave.append(('asset', a.get('type'), a.get('count')))
                for it in (rw.get('items') or []):
                    ib = int(it.get('bid', 0))
                    if is_valid_item(ib):
                        db_bag_add(rid, ib, int(it.get('num', 1)))
                        gave.append(('item', ib, it.get('num', 1)))
                if gave:
                    live_push(self.cfg, 'online_reward')
                pkt = pack_frame(17601, w_u16(1) + w_str('') + w_u8(day) + w_u8(0))
                self.request.sendall(pkt)
                log('tcp.log', '  ** 17601 在线福利 day=%d ⇒ %r' % (day, gave))
                return
            # 17602
            # ★ SC_17602 权威规格（AutoConstruct sc/17602）= {tips:uint16, msg:string}
            #   ⚠ 旧实现写成 `code:u8 + msg`（3 字节）⇒ 客户端把 tips 读成
            #     (1<<8|msg_len)，随后 string 解析越界。由真机流量回放审计发现。
            pkt = pack_frame(17602, w_u16(0) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 17602 SC_17602 tips=0 (%d bytes)' % len(pkt))
            return
        if cmd in (16903, 16904):
            # 在线时长（dailysign_ctrl）
            #   16903 CS（空） -> SC{day:u32, online_time:u32, next_aim:u32,
            #                            status:table(time_arg:u32, state:u8)}
            #   16904 CS（空） -> SC{...}
            if cmd == 16903:
                out = (w_u32(int(self.cfg.get('online_day', 0))) +
                       w_u32(int(self.cfg.get('online_time', 0))) +
                       w_u32(int(self.cfg.get('online_next_aim', 0))) + w_u16(0))
                pkt = pack_frame(16903, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 16903 SC_16903 (%d bytes)' % len(pkt))
                return
            # ★ SC_16904 权威规格（AutoConstruct sc/16904）= {code:uint8, msg:string, aim:uint32}
            #   ⚠ 旧实现只写 `code + msg`（缺 aim:u32）⇒ 客户端解析越界。
            #   由真机流量回放审计 tools/replay_captures.py 发现。
            pkt = pack_frame(16904, w_u8(1) + w_str('') + w_u32(0))
            self.request.sendall(pkt)
            log('tcp.log', '  << 16904 SC_16904 code=1 aim=0 (%d bytes)' % len(pkt))
            return
        if cmd in (30600, 30601, 30602, 30603):
            # 黑市商贩（客户端 game/blackmarketeer/blackmarketeer_ctrl.luac 注册 30600~30603）
            #   30600 CS（空）              -> SC{refresh_times:u8, next_time:u32, items:table(id:u8,status:u8)}
            #   30601 CS（空）              -> SC{code,msg}
            #   30602 CS{Id:u8, type:u8}    -> SC{code, Id:u8, msg}     ★ 客户端主动发送
            #   30603 CS{items:table(item_bid:u32,num:u32)} -> SC{code,msg}
            # 依据：protocol/manual.md（均无 D|Dsc*| ⇒ 安全）；
            #   配置表：config_black_market.luac（3042 字节）。
            # ★ 用户实机报障“黑市商贩点击无效” ⇒ **30600~30603 原先无人应答**。
            # ⚠ 黑市商品表与价格的语义**未取证** ⇒ 取 config，默认空，不编造。
            if cmd == 30600:
                items = self.cfg.get('black_market_items') or []
                out = (w_u8(int(self.cfg.get('black_market_refresh', 0)) & 0xff) +
                       w_u32(int(self.cfg.get('black_market_next_time', 0))) +
                       w_u16(len(items)))
                for it in items:
                    out += w_u8(int(it.get('id', 0)) & 0xff) + w_u8(int(it.get('status', 0)) & 0xff)
                pkt = pack_frame(30600, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 30600 SC_30600 items=%d (%d bytes)' % (len(items), len(pkt)))
                return
            if cmd == 30601:
                pkt = pack_frame(30601, w_u8(1) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 30601 SC_30601 code=1 (%d bytes)' % len(pkt))
                return
            if cmd == 30602:
                iid = body[0] if len(body) >= 1 else 0
                typ = body[1] if len(body) >= 2 else 0
                pkt = pack_frame(30602, w_u8(1) + w_u8(iid) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 30602 SC_30602 code=1 Id=%d type=%d (%d bytes)'
                    % (iid, typ, len(pkt)))
                return
            # 30603 批量卖出
            n = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else 0
            sold = []
            off = 2
            for _ in range(n):
                if off + 8 > len(body):
                    break
                ib, num = struct.unpack_from('>II', body, off)
                sold.append((ib, num))
                off += 8
            pkt = pack_frame(30603, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 30603 SC_30603 code=1 items=%r (%d bytes)' % (sold[:4], len(pkt)))
            return
        if cmd in (12430, 12431, 12432):
            # 悬赏/刷新系统（真机请求过、原先无人应答）
            #   12430 CS{type:u8}        -> SC{code,quantity,msg}
            #   12431 CS（空）           -> SC{bonus:table(quantity,coin,exp,hero_exp),
            #                                  cur_quantity, free_refresh_times, times,
            #                                  total_times, assist_times, total_assist_times}
            #   12432 CS（空）           -> SC{...}
            # 依据：protocol/manual.md（无 D|Dsc*| ⇒ 安全）。
            # ⚠ 具体数值的语义**未取证** ⇒ 取 config（默认 0/空），不编造。
            if cmd == 12431:
                bonus = self.cfg.get('bounty_bonus') or []
                out = (w_u16(len(bonus)))
                for b in bonus:
                    out += (w_u32(int(b.get('quantity', 0))) + w_u32(int(b.get('coin', 0))) +
                            w_u32(int(b.get('exp', 0))) + w_u32(int(b.get('hero_exp', 0))))
                out += (w_u32(int(self.cfg.get('bounty_cur_quantity', 0))) +
                        w_u8(int(self.cfg.get('bounty_free_refresh', 0)) & 0xff) +
                        w_u8(int(self.cfg.get('bounty_times', 0)) & 0xff) +
                        w_u8(int(self.cfg.get('bounty_total_times', 0)) & 0xff) +
                        w_u8(int(self.cfg.get('bounty_assist_times', 0)) & 0xff) +
                        w_u8(int(self.cfg.get('bounty_total_assist', 0)) & 0xff))
                pkt = pack_frame(12431, out)
                self.request.sendall(pkt)
                log('tcp.log', '  << 12431 SC_12431 bonus=%d cur=%s (%d bytes)'
                    % (len(bonus), self.cfg.get('bounty_cur_quantity', 0), len(pkt)))
                return
            if cmd == 12430:
                t = body[0] if len(body) >= 1 else 0
                pkt = pack_frame(12430, w_u8(1) + w_u8(int(self.cfg.get('bounty_cur_quantity', 0)) & 0xff) + w_str(''))
                self.request.sendall(pkt)
                log('tcp.log', '  << 12430 SC_12430 type=%d code=1 (%d bytes)' % (t, len(pkt)))
                return
            # 12432
            pkt = pack_frame(12432, w_u8(1) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << 12432 SC_12432 code=1 (%d bytes)' % len(pkt))
            return
        if cmd == 12421:
            # CS_12421\uff08\u7a7a\uff09\u2192 SC_12421{finish_task_list:table(bid:u32)}
            # \u4f9d\u636e\uff1aprotocol/manual.md\uff08\u65e0 D|Dsc*| \u21d2 \u5b89\u5168\uff09\u3002
            # \u2605 **\u5df2\u5b8c\u6210\u4efb\u52a1\u5217\u8868**\uff08status==3\uff09\u3002
            rid = role_state(self.cfg).get('rid', 1001)
            done = []
            try:
                for b, m in (db_get_missions(rid) or {}).items():
                    if int(m.get('mission_status') or 0) == 3:
                        done.append(int(b))
            except Exception:
                pass
            out = w_u16(len(done)) + b''.join(w_u32(b) for b in sorted(done))
            pkt = pack_frame(12421, out)
            self.request.sendall(pkt)
            log('tcp.log', '  << 12421 SC_12421 finish_task_list=%d (%d bytes)' % (len(done), len(pkt)))
            return
# [P2C-migrated inventory/handler.py]         if cmd == 10502:
            # CS_10502{bag_code:uint8} → SC_10502{bag_code, items}
            # 一件物品 16 字段，顺序取自权威 spec（见 build_bag_items 头注）。
            #
            # ★★ 已取证解决（用户报障“背包没有装备”）：
            #   `BackPackConst.Bag_Code`（客户端 game/backpack/backpack_const.luac，15 项）：
            #     BACKPACK=1  ROLE_EQUIP=2  HERO_EQUIP=3  STORAGE=4  HERO_STORAGE=5
            #     JBP_WAREHOUSE=6  FASHION_PACK=7  TREASUR_PLANE=8  PARTNER_ARTIFACT=11
            #     FIRECRACKER=12  SOULSTAR_PACK=13/14/15  ROLE_ARTIFACT=16/17
            #   ⇒ **必须按 bag_code 分囊返回**，否则装备栏（=2）拿到的是普通背包，
            #     装备永远显示不出来。
#             bag_code = body[0] if body else BAG_MAIN
#             self._last_bag_code = bag_code
            # ★ 记录客户端**请求过的每个 bag_code**：客户端对不同背包页用不同 code
            #   （实测 5/6/7/8/12），推送刷新必须覆盖它们，见 bag_push_frames()。
#             _seen = getattr(self, '_bag_codes_seen', None)
#             if _seen is None:
#                 _seen = self._bag_codes_seen = set()
#             _seen.add(bag_code)
#             rid = role_state(self.cfg).get('rid', 1001)
            # ★ 按 bag_code 取对应的囊：
            #   1 = 背包；2 = 角色装备；3 = 伙伴装备；4/5 = 仓库
            #   其他 code 暂回空表（未实现的囊不编造内容）。
#             if bag_code == BAG_MAIN:
#                 items = db_bag_get(rid, BAG_MAIN)
#             elif bag_code in (2, 3):
#                 items = build_equip_items(rid, bag_code)
#             elif bag_code == STORAGE_CODE:
                # 仓库（STORAGE=4）：从 store_items 取
#                 items = db_store_get(rid, bag_code)
#             else:
#                 items = db_bag_get(rid, bag_code)
#             self.request.sendall(pack_frame(
#                 10502, w_u8(bag_code) + build_bag_items(items)))
#             if items:
#                 log('tcp.log', '  << 10502 SC_10502 bag_code=%d items=%d %r'
#                     % (bag_code, len(items),
#                        [(i['item_id'], i['bid'], i['quantity']) for i in items]))
#             return

        if cmd == 20011:
            # CS_20011 客户端加载完成（实测客户端**不会**发，保留以防兼容）
            log('tcp.log', '  .. 20011 battle client load finished')
            return

        if cmd == 20014:
            # CS_20014 客户端动画播放完成（实测客户端**不会**发）
            log('tcp.log', '  .. 20014 battle animation finished (not used to gate)')
            return

        if cmd in (20008, 20009):
            # 自动战斗开关 / 使用技能：**编排不变**（回合由服务端定时器驱动），
            # 但**必须应答** —— SC_20008{id:int8, flag:uint8} 与 SC_20009{skill_id:int32}
            # 在协议里都有定义。★ 2026-10-17 修：原来两者**只写日志、不回包**
            #   （冒烟实测：99 条未测命令里只有 20008/20009/20011 静默，而 20011/20014
            #    在协议里**没有 SC** ⇒ 沉默正确；这两条有 SC ⇒ 沉默会让客户端落进
            #    未知命令分支 / "选技能"面板干等）。按本项目惯例**回显**。
            if cmd == 20009:
                v = struct.unpack_from('>i', body, 0)[0] if len(body) >= 4 else 0
                self.request.sendall(pack_frame(20009, w_u32(int(v) & 0xFFFFFFFF)))
                log('tcp.log', '  << 20009 SC_20009 skill_id=%d（回显；编排仍由定时器驱动）' % v)
            else:
                flag = body[0] if body else 0
                self.request.sendall(pack_frame(20008, w_u8(0) + w_u8(int(flag) & 0xff)))
                log('tcp.log', '  << 20008 SC_20008 id=0 flag=%d（回显）' % flag)
            return

        if cmd in (20001, 20003, 20004, 20005, 20016, 20017):
            # 角色对战 / 测试战斗 / 切磋 / 观战：本阶段不实现，明确回失败
            label = {20001: '对角色发起战斗', 20003: '测试战斗', 20004: '发起切磋',
                     20005: '确认切磋', 20016: '申请观战', 20017: '退出观战'}[cmd]
            if cmd in (20004, 20016):
                pkt = pack_frame(cmd, w_u8(0) + w_str('%s 不在本阶段范围' % label))
            else:
                pkt = pack_frame(cmd, w_u8(0) + w_str(''))
            self.request.sendall(pkt)
            log('tcp.log', '  << %d %s code=0 (本阶段不实现)' % (cmd, label))
            return

        builder = EMPTY_REPLIES.get(cmd)
        if builder is not None:
            pkt = pack_frame(cmd, builder())
            self.request.sendall(pkt)
            log('tcp.log', '  << %d empty-but-valid reply (%d bytes)'
                % (cmd, len(pkt)))
            return

        # ★★★★ R151：**全局兜底 —— 放在所有专用分支之后**。
        #   为什么放这里：R150 查明"默认响应在函数**前部**"⇒ 一旦放开范围
        #   就会**抢走专用实现**（`10401` 变空表 + 门禁 E 报 39 条）。
        #   ⇒ 正确做法是让它**排在所有专用分支之后**：能走到这里的，
        #     必然是**没有任何专用实现处理**的命令 ⇒ 兜底不会遮住任何东西。
        #   `global_default_sc`（config.json，默认 false）控制是否启用。
        if CFG.get('global_default_sc') and _sc_defined(cmd):
            try:
                _out151 = _build_default_sc(cmd)
            except Exception as e:
                log('tcp.log', '  !! %d 兜底响应构建失败: %r' % (cmd, e))
                return
            self.request.sendall(pack_frame(cmd, _out151))
            log('tcp.log', '  << %d SC_%d 兜底响应 (%d bytes)'
                % (cmd, cmd, len(_out151) + 6))
            return

    cfg = DEFAULT_CFG


def build_cfg(extra=None):
    """装配运行配置（**main() 与自检工具共用同一份逻辑**）。

    ★ 2026-10-17 抽取原因：`CFG` 是空 dict，只有 `main()` 里才 `CFG.clear()/update()`。
      自检工具只 `import mock_server` 时 `CFG == {}` ⇒ 工具里读到的一切 cfg 都是**默认值**，
      我们据此误判过一次 `equip_type_slot`（以为配置缺失，实际是工具没加载配置）。
      工具只要 `publish_cfg(build_cfg())` 就能拿到与服务器**完全一致**的配置。
    """
    cfg = dict(DEFAULT_CFG)
    if os.path.exists(CFG_PATH):
        cfg.update(json.load(open(CFG_PATH, encoding='utf-8')))
    else:
        os.makedirs(os.path.dirname(CFG_PATH), exist_ok=True)
        json.dump(DEFAULT_CFG, open(CFG_PATH, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        log('server.log', 'wrote default config -> %s' % CFG_PATH)
    if extra:
        cfg.update(extra)
    return cfg


def init_db():
    """建表（**main() 与自检工具共用**）：主表 + 背包/装备/仓库/礼包/签到。"""
    db_init()          # Phase 4E：角色状态数据库
    # ★★ Phase F 修复：原来**漏了 `db_bag_init()`** —— 它才是建 `bag_items` 表的那个。
    #   后果：从旧快照还原数据库（或全新库）时 `bag_items` 不存在，
    #   `db_bag_add()` 抛 "no such table: bag_items"，
    #   表现就是**购买扣了钱但物品没进背包**（用户报障"买不到"的根因之一）。
    db_bag_init()          # 背包物品表（10502/10505/10500）
    db_init_bag_volume()   # 背包容量表（10552）
    db_init_equip()        # 装备表（10511）
    db_store_init()        # 仓库表（10714 / bag_code=4）
    db_init_levgift()      # 等级礼包领取记录（14601）
    db_init_sign()         # 签到记录（14101）
    log('server.log', 'DB ready -> %s' % DB_PATH)


def publish_cfg(cfg):
    """把装配好的 cfg 广播到三处（HTTP Handler / TcpHandler / 模块级 CFG）。"""
    Handler.cfg = cfg
    TcpHandler.cfg = cfg          # ← 必须显式设置，否则 TCP 侧用的是 DEFAULT_CFG
    CFG.clear()
    CFG.update(cfg)
    return cfg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--http', type=int)
    ap.add_argument('--game', type=int)
    ap.add_argument('--host')
    args = ap.parse_args()

    cfg = build_cfg({'http_port': args.http, 'game_port': args.game, 'host': args.host}
                    if (args.http or args.game or args.host) else None)
    init_db()
    publish_cfg(cfg)
    logging_ = lambda m: log('server.log', m)
    logging_('known messages: %d, known commands: %d' % (len(MESSAGES), len(BY_CMD)))
    logging_('HTTP  http://%s:%d/' % (cfg['host'], cfg['http_port']))
    logging_('  CDN conf : /update/config/url_config_ewan.lua')
    logging_('  gateway  : POST /gateway/mobile/json , /app/mobile/json')
    logging_('TCP   %s:%d (protocol-aware: 1199 heartbeat, 1110 account login)'
             % (cfg['host'], cfg['game_port']))
    logging_('  roles    : %d' % len(cfg.get('roles', [])))

    httpd = ThreadingHTTPServer((cfg.get('bind', '0.0.0.0'), cfg['http_port']), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    class Srv(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
    tcpd = Srv((cfg.get('bind', '0.0.0.0'), cfg['game_port']), TcpHandler)
    try:
        tcpd.serve_forever()
    except KeyboardInterrupt:
        logging_('bye')


if __name__ == '__main__':
    main()
