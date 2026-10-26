#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绝世唐门 1.4.9 —— 最小回环服务器（minimal loop server）

唯一目标：让 **登录 → 角色 → 进场景 → 任务 → 战斗 → 结算 → 掉落进包** 这条最小玩法回环
    可运行、可自检、可复现；并回答"这条回环**最少**需要哪些命令、哪些字段、哪些真值"。

它不是 `server/mock_server.py` 的替代品（那是 16k 行的全量实现），而是它的**最小子集**：
只实现回环必需的命令；其余命令一律走 **按协议规格生成的通用应答**（结构永不出错），
没有任何 SC 定义的命令**不回包**（本项目纪律：CS-only 回包会把客户端推进未知分支）。

── 数据来源（全部原版/已确证，绝不编造）──────────────────────────────────
  protocol/fields.json        3553 条协议字段定义（从 APK cmd_resolve_*.luac 提取）
  server/mission_config.json  846 条任务（从 config_mission.luac 提取）
  server/item_config.json     3535 件物品（从 config_item.luac 提取）
  server/config.json          已确证的运行配置（服务器列表 / 测试怪 / 角色默认值）

── 标注纪律（沿用本项目红线：不把推测写成已确认）──────────────────────────
  [APK]       原版数据（协议定义 / 配置表）
  [DOC]       本项目文档里用**实机证据**确证过的语义
  [TEST_ONLY] **占位值** —— APK 里确实没有这份数据（如怪物 HP/攻防/经验），
              只为了让回环跑起来；换真值的位置在 MON_STATS / KILL_REWARD
  [UNKNOWN]   未确证 ⇒ 不实现（而不是猜）

用法：
    python server/minloop/min_loop_server.py                  # 8099 / 9099（避开参考服 8080/9000）
    python server/minloop/min_loop_server.py --http 8080 --game 9000
    python server/minloop/selftest.py                         # 离线回环自检（不依赖客户端）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socketserver
import sqlite3
import struct
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Windows 控制台默认 GBK：日志里的 ⇒ / 中文标点会直接抛 UnicodeEncodeError
# （本项目踩过同类坑）⇒ 一进模块就把标准流切成 UTF-8，并留 errors='replace' 兜底。
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(HERE)                 # .../DSH/server
ROOT = os.path.dirname(SERVER_DIR)                 # .../DSH

# ─────────────────────────────────────────────────────────────────────────────
# 线格式（[DOC] 由真机流量反推并用 tools/decode_frames.py 验证，边界 100% 对齐）
#     [u32 大端 payload_len][u16 大端 cmd][body]
#     payload_len = 2 + len(body)         字符串 = [u16 大端 长度][utf-8 字节]
# ⚠ 客户端短消息尾部会带"定长缓冲区残留" ⇒ 只按协议定义读前 N 字节，忽略多余尾部
# ─────────────────────────────────────────────────────────────────────────────


def w_u8(v):
    return struct.pack('>B', int(v) & 0xFF)


def w_u16(v):
    return struct.pack('>H', int(v) & 0xFFFF)


def w_u32(v):
    return struct.pack('>I', int(v) & 0xFFFFFFFF)


def w_str(s):
    b = ('' if s is None else str(s)).encode('utf-8')
    return w_u16(len(b)) + b


def pack_frame(cmd, body=b''):
    payload = w_u16(cmd) + body
    return w_u32(len(payload)) + payload


class FrameParser(object):
    """增量解帧：返回 [(cmd, body)]，不足一帧就留在缓冲里。"""

    def __init__(self):
        self.buf = b''

    def feed(self, data):
        self.buf += data
        out = []
        while len(self.buf) >= 6:
            ln = struct.unpack_from('>I', self.buf, 0)[0]
            cmd = struct.unpack_from('>H', self.buf, 4)[0]
            if ln < 2 or ln > (1 << 20):
                self.buf = b''
                break
            if len(self.buf) < 4 + ln:
                break
            out.append((cmd, self.buf[6:4 + ln]))
            self.buf = self.buf[4 + ln:]
        return out


# ─────────────────────────────────────────────────────────────────────────────
# 协议规格（唯一真源：[APK] protocol/fields.json）
# ─────────────────────────────────────────────────────────────────────────────

INT_WIDTH = {'uint8': 1, 'int8': 1, 'bool': 1, 'uint16': 2, 'int16': 2,
             'uint32': 4, 'int32': 4, 'float': 4, 'double': 8}


def field_width(t):
    """整数字段宽度；string/未识别 → -1（变长或按 1 字节兜底）。"""
    t = (t or '').lower()
    if t.startswith('string'):
        return -1
    if t.startswith('d|') or t.startswith('dsc'):
        return -1                      # 未展开的子结构引用 ⇒ 只写空计数
    return INT_WIDTH.get(t, 1)


class Spec(object):
    """按 cmd 提供权威 CS/SC 字段列表。"""

    def __init__(self, path=None):
        self.path = path or os.path.join(ROOT, 'protocol', 'fields.json')
        self.cs, self.sc = {}, {}
        raw = json.load(open(self.path, encoding='utf-8'))
        for _k, v in raw.items():
            try:
                cmd = int(v.get('cmd'))
            except (TypeError, ValueError):
                continue
            d = (v.get('dir') or '').lower()
            if d == 'cs':
                self.cs.setdefault(cmd, v.get('fields') or [])
            elif d == 'sc':
                self.sc.setdefault(cmd, v.get('fields') or [])
        self.n_cs, self.n_sc = len(self.cs), len(self.sc)

    # ---- 编码 -------------------------------------------------------------
    def _enc_fields(self, fields, values):
        out = b''
        for f in fields or []:
            if not isinstance(f, dict):
                continue
            name = f.get('name') or ''
            items = f.get('items') or []
            if items:                                   # 子表：u16 计数 + N 条
                rows = values.get(name) or []
                out += w_u16(len(rows))
                for r in rows:
                    out += self._enc_fields(items, r if isinstance(r, dict) else {})
                continue
            w = field_width(f.get('type'))
            if w == -1:
                out += w_str(values.get(name, ''))
            else:
                v = values.get(name, 0)
                try:
                    v = int(v or 0)
                except (TypeError, ValueError):
                    v = 0
                signed = (f.get('type') or '').lower().startswith('int')
                out += int(v).to_bytes(w, 'big', signed=signed)
        return out

    def encode_sc(self, cmd, values=None):
        """按权威 SC 编码；`code`/`result` 缺省给 1（TRUE=成功，[DOC] 客户端判据）。"""
        fields = self.sc.get(int(cmd))
        if not fields:
            return None                                  # 无 SC 定义 ⇒ 调用方不应答
        v = dict(values or {})
        if fields and isinstance(fields[0], dict):
            fn = (fields[0].get('name') or '')
            if fn in ('code', 'result') and fn not in v:
                v[fn] = 1
        return self._enc_fields(fields, v)

    def has_sc(self, cmd):
        return bool(self.sc.get(int(cmd)))

    def read_cs(self, cmd, body):
        """按 CS 规格从 body 读字段（忽略尾部残留）。"""
        out = {}
        o = 0
        for f in self.cs.get(int(cmd)) or []:
            if not isinstance(f, dict):
                continue
            name = f.get('name') or ''
            if f.get('items'):
                n = struct.unpack_from('>H', body, o)[0] if len(body) >= o + 2 else 0
                out[name] = n
                break
            w = field_width(f.get('type'))
            if w == -1:
                n = struct.unpack_from('>H', body, o)[0] if len(body) >= o + 2 else 0
                out[name] = body[o + 2:o + 2 + n].decode('utf-8', 'replace')
                o += 2 + n
            else:
                if len(body) < o + w:
                    break
                out[name] = int.from_bytes(body[o:o + w], 'big',
                                           signed=(f.get('type') or '').lower().startswith('int'))
                o += w
        return out


# ─────────────────────────────────────────────────────────────────────────────
# 持久化（最小 4 表；自己的库，绝不碰参考服的 state/roles.db）
# ─────────────────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles(
  rid INTEGER PRIMARY KEY, srv_id TEXT, name TEXT, lev INTEGER, sex INTEGER, career INTEGER,
  exp INTEGER, gold INTEGER, coin INTEGER, coupon INTEGER, hero_exp INTEGER,
  scene_id INTEGER, x INTEGER, y INTEGER, dir INTEGER, updated_at INTEGER);
CREATE TABLE IF NOT EXISTS bag(
  item_id INTEGER PRIMARY KEY AUTOINCREMENT, rid INTEGER, bid INTEGER,
  quantity INTEGER, bind INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS missions(
  rid INTEGER, mission_bid INTEGER, status INTEGER, progress INTEGER,
  accept_time INTEGER, PRIMARY KEY(rid, mission_bid));
CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT);
"""


class Store(object):
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            self.db.executescript(SCHEMA)
            self.db.commit()

    # ---- 低层 -------------------------------------------------------------
    def ex(self, sql, args=()):
        with self.lock:
            cur = self.db.execute(sql, args)
            self.db.commit()
            return cur

    def one(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchone()

    def all(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchall()

    # ---- 角色 -------------------------------------------------------------
    def ensure_role(self, rid, srv_id, name, lev=1, sex=0, career=1):
        if not self.one('SELECT rid FROM roles WHERE rid=?', (rid,)):
            self.ex('INSERT INTO roles(rid,srv_id,name,lev,sex,career,exp,gold,coin,coupon,'
                    'hero_exp,scene_id,x,y,dir,updated_at) VALUES(?,?,?,?,?,?,0,0,0,0,0,10001,100,42,0,?)',
                    (rid, srv_id, name, lev, sex, career, int(time.time())))
        return self.role(rid)

    def role(self, rid):
        r = self.one('SELECT * FROM roles WHERE rid=?', (rid,))
        return dict(r) if r else None

    def set_role(self, rid, **kw):
        if not kw:
            return
        kw['updated_at'] = int(time.time())
        cols = ','.join('%s=?' % k for k in kw)
        self.ex('UPDATE roles SET %s WHERE rid=?' % cols, tuple(kw.values()) + (rid,))

    def add_assets(self, rid, gold=0, coin=0, coupon=0, exp=0, hero_exp=0):
        self.ex('UPDATE roles SET gold=gold+?,coin=coin+?,coupon=coupon+?,'
                'exp=exp+?,hero_exp=hero_exp+?,updated_at=? WHERE rid=?',
                (int(gold), int(coin), int(coupon), int(exp), int(hero_exp),
                 int(time.time()), rid))

    # ---- 背包 -------------------------------------------------------------
    def bag(self, rid):
        return [dict(r) for r in self.all('SELECT * FROM bag WHERE rid=? ORDER BY item_id', (rid,))]

    def bag_add(self, rid, bid, quantity=1, bind=0):
        row = self.one('SELECT * FROM bag WHERE rid=? AND bid=? AND bind=?', (rid, bid, bind))
        if row:
            self.ex('UPDATE bag SET quantity=quantity+? WHERE item_id=?',
                    (int(quantity), row['item_id']))
            return dict(self.one('SELECT * FROM bag WHERE item_id=?', (row['item_id'],)))
        cur = self.ex('INSERT INTO bag(rid,bid,quantity,bind) VALUES(?,?,?,?)',
                      (rid, int(bid), int(quantity), int(bind)))
        return dict(self.one('SELECT * FROM bag WHERE item_id=?', (cur.lastrowid,)))

    def bag_has(self, rid, bid, num):
        """背包里该 bid 的可计入总数（不区分 bind）——用于交物品前的**诚实校验**。"""
        r = self.one('SELECT COALESCE(SUM(quantity),0) AS n FROM bag WHERE rid=? AND bid=?',
                     (rid, int(bid)))
        return (int(r['n']) if r else 0) >= int(num)

    def bag_del(self, rid, bid, num):
        """从背包扣除 `num` 个该 bid（跨 bind 行扣减；数量不足返 False，**不做部分扣减**）。"""
        need = int(num)
        rows = self.all('SELECT * FROM bag WHERE rid=? AND bid=? ORDER BY item_id', (rid, int(bid)))
        if sum(int(r['quantity']) for r in rows) < need:
            return False
        for r in rows:
            if need <= 0:
                break
            q = int(r['quantity'])
            take = min(q, need)
            if take >= q:
                self.ex('DELETE FROM bag WHERE item_id=?', (r['item_id'],))
            else:
                self.ex('UPDATE bag SET quantity=quantity-? WHERE item_id=?', (take, r['item_id']))
            need -= take
        return True

    # ---- 任务 -------------------------------------------------------------
    def missions(self, rid):
        return [dict(r) for r in self.all('SELECT * FROM missions WHERE rid=? ORDER BY mission_bid',
                                          (rid,))]

    def mission_set(self, rid, bid, status, progress=0):
        self.ex('INSERT INTO missions(rid,mission_bid,status,progress,accept_time) '
                'VALUES(?,?,?,?,?) ON CONFLICT(rid,mission_bid) DO UPDATE SET '
                'status=excluded.status,progress=excluded.progress',
                (rid, int(bid), int(status), int(progress), int(time.time())))

    def mission_bump(self, rid, bid, delta=1):
        self.ex('UPDATE missions SET progress=progress+? WHERE rid=? AND mission_bid=?',
                (int(delta), rid, int(bid)))

    def mission_del(self, rid, bid):
        """删除一条已接任务（用于 `12404` 放弃任务）。"""
        self.ex('DELETE FROM missions WHERE rid=? AND mission_bid=?', (rid, int(bid)))


# ─────────────────────────────────────────────────────────────────────────────
# 原版数据（[APK] 配置表）
# ─────────────────────────────────────────────────────────────────────────────

# [TEST_ONLY] APK 里没有怪物 HP/攻防（见 report/jstm_privateserver_maturity_update.md：
#            `Config.MonData.hp_num` 7956 条里只有 27 条 >0 ⇒ 它不是战斗血量）。
#            换真值只改这里。
MON_STATS = {'hp_max': 2400, 'atk_s': 40, 'def_s': 10}


# ★ 2026-10-01（goal 50 轮 · round 19）：**发送时只带参考服实测的那两项属性**。
#   真机依据（参考服抓包，两处一致）：
#       logs/1.4.9/battle_chain_tcp.log:63、:?  →
#       `<< 10303 SC_10303 attr (hp_max=4321 atk_s=777) (192 bytes)`
#   ⇒ 参考服 `10303` 整帧 **192 字节**、`attr` 表里只有 **hp_max / atk_s** 两项；
#   而本服此前把 `attrs()` 的 **24 项**全发出去（帧 **2233 字节**），
#   这 24 项全部来自 `[TEST_ONLY]` 线性占位（APK 无逐级属性成长表）
#   ⇒ 等于**把 24 个编造数值当角色属性发给客户端**。
#   现改为：**内部仍算全部 24 项**（`power()`/战斗要用），但**只发参考服实测的这 2 项**，
#   既减少编造数据量、又与"客户端确实接受过的形态"一致。
#   诚实标注：这 2 项的**数值仍是 `[TEST_ONLY]`**（APK 无该数据），只是**项数与参考服一致**。
SENT_ATTRS = ('hp_max', 'atk_s')


def _sent_attrs(attrs):
    """**发送用**的属性表：按 `protocol/fields.json`，`SC_10303.attr` 是
    **「结构体表」**（每个 item 含 strength/intellect/…/hp_max/atk_s 共约 24 个字段，单项约 **176 字节**）。

    ★ 因此这里必须返回 **只有一个结构体的列表** `[{…}]`，而**不是**一个 24 键的字典 ——
      字典会被编码器逐键展开成**多行**（实测：24 键 ⇒ 帧 2233 字节 = 24×~88）。
    真机依据 `logs/1.4.9/battle_chain_tcp.log:63`
    （`<< 10303 SC_10303 attr (hp_max=4321 atk_s=777) (192 bytes)`）显示参考服只打印**一个属性块**。
    诚实标注：字段取值仍是 `[TEST_ONLY]`（APK 无逐级成长表）。
    """
    return [{k: attrs[k] for k in SENT_ATTRS if k in attrs}]

# ★ 2026-10-01（goal 50 轮 · round 7）：`KILL_REWARD` 已**停用** —— 击杀的 coin/wood
#   改为读 APK 的真实掉落配置（见 `apk_drop()`）。保留常量只为兼容旧引用，且明确标注不再使用。
KILL_REWARD = {'exp': 50, 'coin': 30}                      # [DEPRECATED] 不再用于击杀奖励
DROP_ITEM_BID = 33001                                       # [TEST_ONLY] 仅在"APK 配置确有物品掉落"时使用

# ---- APK 掉落配置（配置驱动，替换占位值） --------------------------------------
_APK_DROP_CACHE = None


def _apk_drop_path():
    """APK 掉落配置（由 `assets/src/config/config_drop.luac` 还原）在仓库中的位置。"""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(root, 'analysis', '1.4.9', 'item', '_config_drop.json')


def apk_drop(mon_bid):
    """返回 APK 里该怪物的掉落记录（dict）；找不到 ⇒ None（**不编造**）。"""
    global _APK_DROP_CACHE
    if _APK_DROP_CACHE is None:
        _APK_DROP_CACHE = {}
        try:
            with open(_apk_drop_path(), encoding='utf-8') as f:
                _APK_DROP_CACHE = json.load(f).get('Config', {}).get('Drop', {}) or {}
        except Exception:
            log('  !! 读取 APK 掉落配置失败:\n%s' % traceback.format_exc())
    return _APK_DROP_CACHE.get(str(mon_bid))


def parse_apk_num(v):
    """APK 配置里的数值形如 `"{1000}"` / `1000` ⇒ 取整数部分（取不到返 0，不猜）。"""
    if v is None:
        return 0
    m = re.search(r'-?\d+', str(v))
    return int(m.group(0)) if m else 0


def _drop_has_items(r):
    """该掉落记录是否**确有物品节**（20001 等 12 只怪三个节全空 ⇒ False）。"""
    for k in ('first', 'core'):
        if r.get(k):
            return True
    n = r.get('normal')
    if isinstance(n, dict) and any(n.values()):
        return True
    return False

# ---- 怪物真值表（外观资源 / 真名）----------------------------------------------
# ★ 2026-10-01：`SCMapGird_10201.mons` 的 item 里有 **`res_id:string`**（外观资源），
#   而我此前发的是**空串** ⇒ 客户端拿不到怪的外观；名字也用了自造的 `mon20001`。
#   真值来源 `analysis/1.4.9/task/config_mon.json`（例：20001 → name="戴浩", res_id="H32000"）。
_MON_CFG_CACHE = None


def mon_cfg(bid):
    """返回 `config_mon.json` 里该怪的真值（含 name/res_id）；查不到 ⇒ None（不编造）。"""
    global _MON_CFG_CACHE
    if _MON_CFG_CACHE is None:
        _MON_CFG_CACHE = {}
        path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'analysis', '1.4.9', 'task', 'config_mon.json'))
        try:
            with open(path, encoding='utf-8') as f:
                _MON_CFG_CACHE = json.load(f)
        except Exception:
            log('  !! 读取 config_mon.json 失败:\n%s' % traceback.format_exc())
    return _MON_CFG_CACHE.get(str(bid)) or _MON_CFG_CACHE.get(bid)


# ---- 真实物品来源：礼包内容表（`config_item_gift.luac` 还原）------------------------
# ★ 2026-10-01（goal 50 轮 · round 14）：`10505`（使用物品/开礼包）用**真值**实现，
#   数据源 = `server/item_gift.json`（`tools/extract_item_gift.py` 从
#   `assets/src/config/config_item_gift.luac` 还原）：496 礼包 / 5353 条内容，
#   其中 95.9% 的 bid 命中本作 `item_config.json`（其余约 4% 是小数字的**货币/经验码**）。
#   ⇒ 这条路径**不需要任何占位物**，进包环可以用真物品验证。
_ITEM_GIFT_CACHE = None
# 礼包内容里可能出现的小数字码（与任务 award_assets 同源）：1=gold 2=coin 3=coupon 4=exp 15=hero_exp
ASSET_CODE = {1: 'gold', 2: 'coin', 3: 'coupon', 4: 'exp', 15: 'hero_exp'}


def item_gift(bid):
    """返回该礼包的**真实**内容 `[[item_bid, num], …]`；不是礼包/查不到 ⇒ None（不编造）。"""
    global _ITEM_GIFT_CACHE
    if _ITEM_GIFT_CACHE is None:
        _ITEM_GIFT_CACHE = {}
        path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '..', 'item_gift.json'))
        try:
            with open(path, encoding='utf-8') as f:
                _ITEM_GIFT_CACHE = json.load(f)
        except Exception:
            log('  !! 读取礼包内容表失败:\n%s' % traceback.format_exc())
    v = _ITEM_GIFT_CACHE.get(str(bid))
    return v if v else None

# [TEST_ONLY] 伤害系数：参考服实测"lev70 打 2400 血怪约 3 回合、每击 ~772"，
#             这里按同一手感标定。它只是**手感标定旋钮**，不是原版数值。
DAMAGE_SCALE = 5

# [DOC] award_assets 的资产 code 语义（round31–42 用界面确定性读数复验过）
ASSET_CODE = {1: 'gold', 2: 'coin', 3: 'coupon', 4: 'exp', 15: 'hero_exp'}


class Data(object):
    def __init__(self):
        self.missions = json.load(open(os.path.join(SERVER_DIR, 'mission_config.json'),
                                       encoding='utf-8'))
        self.items = json.load(open(os.path.join(SERVER_DIR, 'item_config.json'),
                                    encoding='utf-8'))
        cfg = json.load(open(os.path.join(SERVER_DIR, 'config.json'), encoding='utf-8'))
        self.cfg = cfg
        self.mons = cfg.get('mons') or []
        self.server_list = cfg.get('server_list') or []
        self.default_roles = cfg.get('roles') or []
        self.npcs = self._load_npcs()

    def _load_npcs(self):
        """[APK] 起始场景 10001 的 NPC 摆位（项目已提取；过滤掉探针误抓的非数字条目）。"""
        for p in ('_mapnpc_10001.json', '_npcs_10001.json'):
            fp = os.path.join(SERVER_DIR, p)
            if not os.path.exists(fp):
                continue
            try:
                raw = json.load(open(fp, encoding='utf-8'))
            except Exception:
                continue
            out = []
            for n in raw:
                if isinstance(n.get('id'), int) and isinstance(n.get('bid'), int):
                    out.append({'id': n['id'], 'bid': n['bid'], 'type': n.get('type', 0),
                                'x': n.get('x', 0), 'y': n.get('y', 0),
                                'name': n.get('name') or ('npc%d' % n['bid'])})
            if out:
                return out
        return []

    def mission(self, bid):
        return self.missions.get(str(bid))

    def chain_head(self, lev):
        """[DOC] 任务来源必须由 APK 配置驱动：按 bid 升序 + lev ≤ 玩家等级 + 可自动接取。"""
        cands = [m for m in self.missions.values()
                 if int(m.get('lev') or 0) <= int(lev)
                 and int(m.get('type') or 0) in (0, 1, 2, 3, 4, 5)
                 and int(m.get('abandon_flag') or 0) == 0]
        cands.sort(key=lambda m: int(m.get('bid') or 0))
        return cands[0] if cands else None

    def item_ok(self, bid):
        return str(bid) in self.items


# ─────────────────────────────────────────────────────────────────────────────
# 最小回环服务器
# ─────────────────────────────────────────────────────────────────────────────

LOG_LOCK = threading.Lock()
LOG_PATH = None


def log(msg):
    line = '[%s] %s' % (time.strftime('%H:%M:%S'), msg)
    with LOG_LOCK:
        print(line, flush=True)
        if LOG_PATH:
            try:
                with open(LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(line + '\n')
            except OSError:
                pass


class Session(object):
    """一条 TCP 连接上的角色会话。"""

    def __init__(self, conn, addr, srv):
        self.conn = conn
        self.addr = addr
        self.srv = srv
        self.spec = srv.spec
        self.store = srv.store
        self.data = srv.data
        self.parser = FrameParser()
        self.rid = None
        self.role = None
        self.battle = None
        self.lock = threading.Lock()

    # ---- 收发 -------------------------------------------------------------
    def send(self, cmd, body=None, values=None, tag=''):
        if body is None:
            body = self.spec.encode_sc(cmd, values)
        if body is None:
            log('  .. %s %s 无 SC 定义 ⇒ 不应答' % (cmd, tag))
            return False
        frame = pack_frame(cmd, body)
        try:
            with self.lock:
                self.conn.sendall(frame)
        except OSError as e:
            log('  !! send %s 失败: %r' % (cmd, e))
            return False
        log('  << %s %-22s %d bytes' % (cmd, tag, len(frame)))
        return True

    def push_generic(self, cmd):
        """非回环命令：按权威 SC 出**结构正确**的应答（code=1，其余零值/空表）。"""
        if not self.spec.has_sc(cmd):
            log('  .. %s 无 SC 定义 ⇒ 不应答（CS-only）' % cmd)
            return False
        return self.send(cmd, values={}, tag='generic')

    # ---- 回环命令 ---------------------------------------------------------
    def on_10001(self, body):
        cs = self.spec.read_cs(10001, body)
        log('  >> 10001 CSFirstPack key=%r（无 SC 定义 ⇒ 不回包）' % cs.get('key'))

    def on_1199(self, body):
        self.send(1199, values={'time': int(time.time())}, tag='heartbeat')

    def on_10101(self, body):
        """创建角色（`CSRoleCreate_10101` = sex, name, career, playform ／ `SCRoleCreate_10101` = code, msg, rid, srv_id）。

        ★ 2026-10-01：本轮实现"自己创建角色"。
        ★★ code 约定（本轮反汇编确证，`denglu_ctrl.luac::on10101Create` proto#26 指令 0-2）：
            `if msg.code ~= 0 then → 失败分支（CREATE_ERROR / message(msg)）`
            ⇒ **成功必须回 `code = 0`**（与 `10200` 同族的例外；`10102/1110` 才是 `code == 1`）。
            本处此前回了 1 ⇒ 客户端当失败处理 ⇒ **用户"创建角色"永远不成功**。

        规则（不编造、可预期）：
          · `name` 不能为空、长度 1..12、**不能重名**（重名 ⇒ code=0 + 说明）；
          · `career` 取 1..8、`sex` 取 0/1（越界 ⇒ code=0）；
          · 成功 ⇒ **新建一行 roles**（新 rid = 现有最大 rid + 1，lev=1、场景与坐标取真值），
            回 `code=1 + rid + srv_id`，并**立刻重推一次 1110（角色列表）**让客户端列表刷新。
        """
        cs = self.spec.read_cs(10101, body)
        name = (cs.get('name') or '').strip()
        career = int(cs.get('career') or 0)
        sex = int(cs.get('sex') or 0)
        if not name or len(name) > 12:
            self.send(10101, values={'code': 1, 'msg': '名字不能为空且不超过 12 个字',
                                     'rid': 0, 'srv_id': ''}, tag='建角失败(名字非法)')
            return
        if not (1 <= career <= 8) or sex not in (0, 1):
            self.send(10101, values={'code': 1, 'msg': '职业或性别取值非法',
                                     'rid': 0, 'srv_id': ''},
                      tag='建角失败(career=%s sex=%s)' % (career, sex))
            return
        dup = self.store.one('SELECT rid FROM roles WHERE name=?', (name,))
        if dup:
            self.send(10101, values={'code': 1, 'msg': '该名字已被使用', 'rid': 0, 'srv_id': ''},
                      tag='建角失败(重名 %s)' % name)
            return
        row = self.store.one('SELECT COALESCE(MAX(rid),1000) AS m FROM roles')
        rid = (int(row['m']) if row else 1000) + 1
        d = self.data.default_roles[0] if self.data.default_roles else {}
        self.store.ensure_role(rid, str(cs.get('srv_id') or d.get('srv_id') or '1'), name, 1, sex, career)
        self.send(10101, values={'code': 0, 'msg': '', 'rid': rid, 'srv_id': '1'},
                  tag='建角成功 rid=%d name=%s career=%d sex=%d' % (rid, name, career, sex))
        # 立刻重推角色列表（客户端创建后会回到选角界面）
        try:
            self.send(1110, values={'code': 1, 'msg': '', 'roles': self.role_list(),
                                    'least_career': self.least_career()}, tag='建角后角色列表')
        except Exception:
            log('  !! 建角后重推 1110 异常:\n%s' % traceback.format_exc())

    def role_list(self):
        """账号下的角色列表（`SC_1110.roles`）。"""
        return [{'rid': r['rid'], 'srv_id': r['srv_id'], 'name': r['name'], 'lev': r['lev'],
                 'sex': r['sex'], 'career': r['career'], 'is_online': 0}
                for r in self.store.all('SELECT * FROM roles ORDER BY rid')]

    def least_career(self):
        """`SC_1110.least_career`：**还剩哪些职业可选**（位掩码，bit(career-1)）。

        ★ 本轮修正：此前恒发 **0** ⇒ 客户端会认为"没有可选职业"（创建角色界面可能因此不可用）。
          现按"已被占用的职业"清位：初始 0xFF（8 个职业都可选），每个已有角色清掉其职业位；
          全被占满时返回 0（诚实反映"没有可选职业"）。
        """
        mask = 0xFF
        for r in self.store.all('SELECT career FROM roles'):
            c = int(r['career']) if r else 0
            if 1 <= c <= 8:
                mask &= ~(1 << (c - 1)) & 0xFF
        return mask

    def on_1110(self, body):
        """[DOC] code 必须 = 1（TRUE）；回 0 会走 message(msg) 分支 ⇒ 空白提示框。"""
        cs = self.spec.read_cs(1110, body)
        args = cs.get('args') or {}
        account = args.get('account') if isinstance(args, dict) else None
        roles = []
        for r in self.store.all('SELECT * FROM roles ORDER BY rid'):
            roles.append({'rid': r['rid'], 'srv_id': r['srv_id'], 'name': r['name'],
                          'lev': r['lev'], 'sex': r['sex'], 'career': r['career'],
                          'is_online': 0})
        # ★ 2026-10-01 修（用户实测："直接登录、没有选区、不能自己创建角色"）：
        #   此前本处在"角色列表为空"时**自动捏一个默认角色**，于是客户端**永远至少有 1 个角色**
        #   ⇒ 选角/建角界面被跳过（很多客户端在"仅 1 个角色"时直接进游戏）。
        #   现在：**列表为空就如实回空列表**（`roles=[]`）⇒ 让客户端走它自己的"创建角色"流程。
        #   注：`ensure_role` 仍保留在 `on_10102` 作为兜底（若客户端直接请求某个 rid），
        #       但**不再由 1110 主动造角色**。
        if not roles:
            log('  .. 1110 该账号角色列表为空 ⇒ 如实回空（交给客户端走"创建角色"）')
        self.send(1110, values={'code': 1, 'msg': '', 'roles': roles,
                                'least_career': self.least_career()},
                  tag='SCAccountLogin account=%s roles=%d least_career=0x%02x'
                      % (account, len(roles), self.least_career()))

    def on_10102(self, body, cmd=10102):
        """登录指定角色 → 应答 + **主动推** 10200(进场景) / 10201(场景格子)。

        ★ 2026-10-01 **修复"无法进图"**：本函数现在同时服务 `10102` 与 `10103`。
        依据（参考服 `server/mock_server.py` 的实机注释，反汇编出处）：
            `10102`/`10103` 的 SC 结构**相同**，且 `on10102Login`/`on10103ReLogin` 都走
            `if resp.code == TRUE then … SendProtocal(10300); LoginSucceedSendProtocal();
             DengluEvent:Fire(LOGIN_SUCCESS)`；
            而 `scene_controller` 把 `LOGIN_SUCCESS` 绑到**进入场景**。
        此前 `10103` **不在 LOOP 里** ⇒ 只回通用应答（`code=1` 但结构零值），**且完全不推 `10200/10201`**
        ⇒ 客户端重连时走的是 `10103`：它会 fire `LOGIN_SUCCESS` 去进场景，**却拿不到任何场景数据**
        ⇒ 表现为"连上了、在心跳，但**进不了图**"（本会话 live11 现场复现：`scene_nil`、只有 `1199`）。
        """
        cs = self.spec.read_cs(cmd, body)
        rid = int(cs.get('rid') or 0)
        # ★ 2026-10-01 修（用户实测："创建后界面为空"）：
        #   此前 `rid` 无效（0 或不存在）时**静默兜底成默认角色**并推场景 ⇒
        #   客户端以为登录成功、实际却没有选定角色 ⇒ **界面一片空白**。
        #   现在：**rid 必须是已存在的角色**，否则如实拒绝（带 msg），让客户端回到选角界面。
        row = self.store.role(rid) if rid else None
        if row is None and not rid:
            # ★ rid=0（未选定角色）：客户端确实会这样发 ⇒ 自动选**第一个角色**（确定性、并记日志），
            #   否则一律拒绝会让玩家**进不了图**。多个角色时仍建议在界面上选（本处只是兜底）。
            first = self.store.one('SELECT * FROM roles ORDER BY rid LIMIT 1')
            if first:
                rid = int(first['rid'])
                row = first
                log('  .. %d 收到 rid=0 ⇒ 兜底选第一个角色 rid=%d（%s）'
                    % (cmd, rid, first['name']))
        if row is None:
            log('  !! %d 请求的 rid=%s 不存在 ⇒ 拒绝' % (cmd, rid))
            self.send(cmd, values={'code': 0, 'msg': '该角色不存在，请重新选择', 'timestamp': 0,
                                   'world_lev': 0},
                      tag='拒绝登录（rid=%s 不存在）' % rid)
            return
        self.rid = rid
        self.role = row
        self.send(cmd, values={'code': 1, 'msg': '', 'timestamp': int(time.time()),
                               'world_lev': 1}, tag='SCRoleLogin/ReLogin rid=%d cmd=%d' % (rid, cmd))
        self.push_10200()
        self.push_10201()

    def on_10103(self, body):
        """角色重连（与 `10102` 同构）—— 见 `on_10102` 的说明：**必须同样推场景数据**。"""
        return self.on_10102(body, cmd=10103)

    def _role_10201(self):
        r = self.role
        return {'rid': r['rid'], 'srv_id': r['srv_id'], 'name': r['name'], 'lev': r['lev'],
                'career': r['career'], 'vip_lev': 0, 'sex': r['sex'], 'status': 0,
                'mspd': 100, 'x': r['x'], 'y': r['y'], 'dir': r['dir'], 'hidden': 0,
                'cur_title': 0, 'ntm_title': 0, 'marry_state': 0, 'spouse_name': '',
                'buff_bids': [], 'misc_uint8': [], 'misc_uint16': [], 'misc_uint32': [],
                'misc_str': [], 'animate_res': []}

    def push_10200(self):
        """★ `10200` 是 `code==1 才是成功` 这条通则的**例外**：必须发 `code = 0`。

        依据（参考服 `server/mock_server.py` _send_10200 的实测注释，逐条有字节码出处）：
            scene_controller.luac proto[16] 写的是
                if resp.code ~= 0 then message2(resp.msg) end      ← **非 0 就报错**
            而 10102/10103 才是 `code == TRUE(1)` 才继续。
        本项目实测：早前 10200 发 1 ⇒ 客户端弹错误信息、**不真正进场景**
        （表现为 `view=no_scene_view_instance`、`sceneData.mapResCache=0`、sceneId 掉回 0）。
        参考服的 `w_u8(0)` 才是**正确**写法。
        """
        r = self.role
        self.send(10200, values={'code': 0, 'msg': '', 'bid': r['scene_id'], 'line_id': 0,
                                 'x': r['x'], 'y': r['y'], 'dir': r['dir']}, tag='进场景 push(code=0)')

    def push_10201(self):
        mons = []
        for m in self.data.mons:
            cf = mon_cfg(m['bid']) or {}
            # ★ 真名与外观资源取 config_mon.json 的真值；取不到才退回配置/占位，并记日志（不编造）
            nm = (m.get('name') or cf.get('name') or ('mon%d' % m['bid']))
            rid = cf.get('res_id') or ''
            if not rid:
                log('  .. 怪 %s 在 config_mon.json 里没有 res_id ⇒ 外观留空（不编造）' % m['bid'])
            mons.append({'id': int(m['id']), 'bid': int(m['bid']), 'type': int(m.get('type', 0)),
                         'name': nm, 'realm': 0, 'mspd': 100,
                         'x': int(m.get('x', 0)), 'y': int(m.get('y', 0)),
                         'dir': int(m.get('dir', 0)), 'res_id': rid, 'status': 0})
        npcs = [{'id': n['id'], 'bid': n['bid'], 'type': n['type'], 'x': n['x'], 'y': n['y'],
                 'name': n['name'], 'misc': [], 'animate_res': [], 'member': []}
                for n in self.data.npcs]
        self.send(10201, values={'roles': [self._role_10201()], 'npcs': npcs, 'mons': mons,
                                 'elems': []},
                  tag='SCMapGird roles=1 npcs=%d mons=%d elems=%d' % (len(npcs), len(mons), len(self.data.elems if hasattr(self.data, 'elems') else [])))

    def on_10300(self, body):
        """客户端初始化完毕 → 推角色四件套（10301 基础 / 10302 货币 / 10303 属性战力 / 10304）。

        ★ 2026-10-01（goal round 8）新增：**顺带推一次任务列表（SC 12400）**。
        依据（真机实测）：客户端已在场景内、且自己手里有任务数据
        （探针 `misVO bid_10000 accept_time_… is_track_1`、`misProg progress_table_n1_status_1`），
        但它的 `12400` 处理器**拿到的列表是 nil**（探针 `h12400=list_na_`），
        因为客户端**从不主动请求 12400**（服务端日志里 `>> 12400` 为 0）——
        它只在"任务面板被打开"时才发。⇒ 由服务端**主动补推**一次，
        让任务面板/任务条有内容，才可能触发后续 `12402`（接取）/`20002`（战斗）。
        """
        for cmd in (10301, 10302, 10303, 10304):
            self.send(cmd, values=self.role_values(), tag='角色信息 push')
        try:
            self.ensure_role()
            self.send(12400, values={'mission_list': self.visible_missions()},
                      tag='任务列表 push（补推，客户端不主动请求）')
        except Exception:
            log('  !! 任务列表补推异常:\n%s' % traceback.format_exc())

    def role_values(self):
        r = self.role
        attrs = self.attrs()
        return {
            'rid': r['rid'], 'srv_id': r['srv_id'], 'name': r['name'], 'lev': r['lev'],
            'is_vip': 0, 'vip_lev': 0, 'sex': r['sex'], 'career': r['career'],
            'face_id': 0, 'cur_title': 0, 'ntm_title': 0, 'gid': 0, 'gsrv_id': '',
            'position': 0, 'gname': '', 'mspd': 100,
            'volume': 100, 'store_volume': 100, 'store_partner_volume': 100,
            'volume_open': 0, 'store_volume_open': 0, 'store_partner_volume_open': 0,
            'exp_max': 999999, 'exp_total_nextlev': 999999, 'attr_point': 0, 'profit_exp': 0,
            'marry_state': 0, 'spouse_name': '', 'head_bid': 0, 'chat_bubble': 0,
            'skill_list': [{'bid': 10000}, {'bid': 10001}, {'bid': 10002}],   # [DOC] 必须是真技能 bid
            'buffs': [], 'animate_res': [], 'misc_uint8': [], 'misc_uint16': [],
            'misc_uint32': [], 'misc_str': [], 'spouse_rid': 0, 'spouse_srv_id': '',
            'insight_status': 0, 'jid': 0, 'j_srv_id': '', 'jlev': 0, 'j_title': '',
            'exp': r['exp'], 'gold': r['gold'], 'gold_acc': r['gold'], 'coin': r['coin'],
            'coupon': r['coupon'], 'sinew': 0, 'experience': 0, 'vitality': 0,
            'guild_contrib': 0, 'practice_exp': 0, 'tower_cent': 0, 'arena_cent': 0,
            'integral': 0, 'cash_coupon': 0, 'dan_point': 0, 'guild_active': 0,
            'marriage': 0, 'course': 0, 'vip_exp': 0, 'lingshi': 0, 'peak_point': 0,
            'black_soul': 0, 'lottery_point': 0, 'boss_point': 0,
            'partner_shenqi_point': 0, 'jiebai_cent': 0, 'rune_exp': 0, 'rune_chip': 0,
            'power': self.power(), 'attr': _sent_attrs(attrs),
            'jiebai_title': '', 'jiebai_lev': 0,
        }

    def attrs(self):
        """[TEST_ONLY] 等级线性成长 —— APK 里没有逐级属性成长表，换真值只改这里。"""
        lev = int(self.role['lev'])
        return {'strength': 10 + lev, 'intellect': 10 + lev, 'armor': 5 + lev // 2,
                'constiution': 10 + lev, 'atk_s': 20 + lev * 2, 'atk_p': 0,
                'def_s': 10 + lev, 'def_p': 0, 'hp_max': 1000 + lev * 50, 'atk_speed': 100,
                'hit': 100, 'dodge': 50, 'crit': 20, 'tenacity': 10, 'red_def_s': 0,
                'red_def_p': 0, 'atk_abs': 0, 'def_abs': 0, 'reduce': 0, 'hurt': 0,
                'hit_rate_show': 95, 'dodge_rate_show': 5, 'crit_rate_show': 5,
                'tenacity_rate_show': 5}

    def power(self):
        a = self.attrs()
        return int(a['atk_s'] * 4 + a['def_s'] * 3 + a['hp_max'] * 0.5)

    # ---- 移动 -------------------------------------------------------------
    def on_10204(self, body):
        """[DOC] 单点逐步上报；服务端落库后**回发给本人**（其它玩家/AOI 不在最小回环内）。"""
        cs = self.spec.read_cs(10204, body)
        x, y = int(cs.get('x') or 0), int(cs.get('y') or 0)
        self.store.set_role(self.rid, x=x, y=y)
        self.role['x'], self.role['y'] = x, y
        self.send(10204, values={'rid': self.rid, 'srv_id': self.role['srv_id'], 'x': x, 'y': y},
                  tag='move ack')

    # ---- 任务 -------------------------------------------------------------
    def mission_entry(self, m):
        bid = int(m['bid'])
        row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?',
                             (self.rid, bid))
        status = row['status'] if row else 0
        prog = row['progress'] if row else 0
        target, target_value = self.mission_target(m)
        return {'mission_bid': bid, 'mission_status': status, 'commit_num': 0,
                'loop_count': 0, 'loop_num': 1, 'code': 1, 'process_status': 0,
                'target': target, 'target_value': target_value, 'value': prog,
                'show_lave_time': 0, 'lave_time': 0,
                'accept_time': (row['accept_time'] if row else 0)}

    @staticmethod
    def mission_target(m):
        """[APK] 任务完成条件取自配置 `progress`。

        ★ 2026-10-01（goal 50 轮 · round 5）**修掉一个真实偏差**：
          此前只处理 `progress[0]` 是 **dict** 的情形，而 `server/mission_config.json` 里
          **实际是列表行**，例如任务 `10020`（切磋魂技）：
              "progress": [["fight_mon", 20001, 1], [0, 0, 20010, 0]]
          行语义 = `[类型名, 目标bid, 数量]` ⇒ 条件为「击杀怪物 **20001** ×1」。
          旧代码走 `return 0, 0` ⇒ **把"有条件的任务"误判成"无条件"**
          ⇒ 客户端一提交就成功、**不需要真去打怪**（破坏回环语义）。
          ⇒ 现在按列表行解析；非 `fight_mon` 的行语义未确证 ⇒ **不据此设门槛**（标 UNKNOWN，不猜）。
        """
        p = m.get('progress') or []
        if isinstance(p, list) and p:
            row = p[0]
            if isinstance(row, (list, tuple)) and len(row) >= 3 and isinstance(row[0], str):
                kind = row[0]
                if kind == 'fight_mon':
                    return int(row[1] or 0), int(row[2] or 1)
                log('  .. 任务 %s 的条件类型 %r 语义未确证 ⇒ 不设门槛' % (m.get('bid'), kind))
                return 0, 0
            if isinstance(row, dict):
                return (int(row.get('target') or row.get('bid') or 0),
                        int(row.get('value') or row.get('num') or 1))
        return 0, 0

    def visible_missions(self):
        """已接取的任务 + 当前链头（[DOC] 只给链头，避免"任务不消失"复发）。"""
        out = []
        for row in self.store.missions(self.rid):
            m = self.data.mission(int(row['mission_bid']))
            if m:
                out.append(self.mission_entry(m))
        head = self.data.chain_head(self.role['lev'])
        if head and not self.store.one('SELECT 1 FROM missions WHERE rid=? AND mission_bid=?',
                                       (self.rid, int(head['bid']))):
            out.append(self.mission_entry(head))
        return out

    def on_12400(self, body):
        self.send(12400, values={'mission_list': self.visible_missions()}, tag='任务列表')

    def on_12402(self, body):
        cs = self.spec.read_cs(12402, body)
        bid = int(cs.get('mission_bid') or 0)
        if not self.data.mission(bid):
            self.send(12402, values={'code': 0, 'msg': '任务不存在', 'missions': []},
                      tag='接取失败 bid=%d（配置里没有）' % bid)
            return
        self.store.mission_set(self.rid, bid, 1, 0)
        self.send(12402, values={'code': 1, 'msg': '', 'missions': [self.mission_entry(self.data.mission(bid))]},
                  tag='接取成功 bid=%d' % bid)
        self.send(12405, values={'update_mission_list': self.visible_missions()}, tag='任务补推')

    def on_12403(self, body):
        cs = self.spec.read_cs(12403, body)
        bid = int(cs.get('mission_bid') or 0)
        m = self.data.mission(bid)
        if not m:
            # 配置里没有这个 bid ⇒ **诚实拒绝**（不编造奖励）
            self.send(12403, values={'mission_bid': bid, 'code': 0, 'msg': '任务不存在'},
                      tag='提交失败 bid=%d（配置里没有）' % bid)
            return
        row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (self.rid, bid))
        if not row:
            # ★ 2026-10-01（goal round 11）真机实测：客户端会提交一条**服务端没记过"已接取"**的任务
            #   （`>> 12403 body=00 00 27 24 …` = bid **10020**，而它确实在 846 条配置里）。
            #   原因是客户端自己的任务状态先于服务端（它手里已有该任务）。
            #   ⇒ 做成**幂等**：补记"已接取"，再走正常提交；**奖励仍然只取配置里的真实 `award_assets`**，
            #     所以这不是"编造数据"，只是把状态对齐。
            self.store.mission_set(self.rid, bid, 1, 0)
            row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (self.rid, bid))
            log('  .. 12403 幂等补记已接取 bid=%d（客户端自认已接）' % bid)
        _t, need = self.mission_target(m)
        if need and int(row['progress']) < need:
            self.send(12403, values={'mission_bid': bid, 'code': 0,
                                     'msg': '条件未满足（%d/%d）' % (row['progress'], need)},
                      tag='条件未满足')
            return
        self.store.mission_set(self.rid, bid, 2, int(row['progress']))
        self.send(12403, values={'mission_bid': bid, 'code': 1, 'msg': ''}, tag='提交成功')
        # ★ 2026-10-01（goal 50 轮 · round 16）**补上参考服会推的两条**（此前漏了）：
        #   状态化回放发现：本服提交成功后只回 `12403`，而参考服在两次真机抓包里都推
        #   `12405`（update_mission_list）+ `12406`（del_mission_list=[该任务]）：
        #     `logs/1.4.9/task_chain_tcp.log:136-137`、`logs/1.4.9/battle_chain_tcp.log:633/663/709/866`
        #   字段名按 `protocol/fields.json`：`SC_12405.update_mission_list:table`、
        #   `SC_12406.del_mission_list:table(mission_bid:uint32)`。
        #   缺失的后果（候选）：任务列表不刷新、**已提交的任务不会从列表消失**。
        self.send(12405, values={'update_mission_list': self.visible_missions()},
                  tag='任务列表更新 push')
        self.send(12406, values={'del_mission_list': [{'mission_bid': bid}]},
                  tag='任务移除 push bid=%d' % bid)
        self.grant_award(m)
        # ★ 参考服提交后还会刷新角色/货币（真机日志 `logs/1.4.9/task_chain_tcp.log:138-139`：
        #   `<< 10302 (refresh after commit)` + `<< 10301/10303 (refresh after commit)`）
        #   ⇒ 本服补推 10301/10303，使客户端角色栏/战力栏随提交同步刷新（10302 由 grant_award 推）。
        self.send(10301, values=self.role_values(), tag='提交后角色刷新')
        self.send(10303, values=self.role_values(), tag='提交后战力刷新')

    def grant_award(self, m):
        """[APK] award_assets = [[asset_code, n], ...]，code 语义见 ASSET_CODE。"""
        got = {'gold': 0, 'coin': 0, 'coupon': 0, 'exp': 0, 'hero_exp': 0}
        for pair in (m.get('award_assets') or []):
            if not (isinstance(pair, (list, tuple)) and len(pair) >= 2):
                continue
            key = ASSET_CODE.get(int(pair[0]))
            if key:
                got[key] += int(pair[1])
        self.store.add_assets(self.rid, **got)
        self.role = self.store.role(self.rid)
        log('  ** 任务 %s 奖励 %s' % (m['bid'], got))
        self.send(10302, values=self.role_values(), tag='奖励后货币同步')

    # ---- 战斗 -------------------------------------------------------------
    def on_20002(self, body):
        """[DOC] 回合制：20002 → 20010(初始化) → 每回合 20012/20013 → 20020(胜负) → 20023(结算)。
        数值为 [TEST_ONLY]（APK 无怪物战斗数值）。"""
        cs = self.spec.read_cs(20002, body)
        mon_id = int(cs.get('mon_id') or 0)
        mon = next((m for m in self.data.mons if int(m['id']) == mon_id), None)
        if mon is None:
            self.send(20002, values={'code': 0, 'msg': '怪物不在场'}, tag='发起失败 mon_id=%d' % mon_id)
            return
        self.send(20002, values={'code': 1, 'msg': ''}, tag='发起战斗 mon=%s' % mon_id)
        a = self.attrs()
        role_f = {'id': 1000, 'rid': self.rid, 'srv_id': self.role['srv_id'],
                  'name': self.role['name'], 'lev': self.role['lev'], 'sex': self.role['sex'],
                  'career': self.role['career'], 'pos': 0, 'group': 1,
                  'hp_max': a['hp_max'], 'hp': a['hp_max'], 'anger': 0, 'is_auto': 1,
                  'animate_res': [], 'skills': [], 'specials': []}
        mon_f = {'id': 2000, 'rid': 0, 'srv_id': '', 'name': mon.get('name') or '怪物',
                 'lev': 1, 'sex': 0, 'career': 0, 'pos': 1, 'group': 2,
                 'hp_max': MON_STATS['hp_max'], 'hp': MON_STATS['hp_max'], 'anger': 0,
                 'is_auto': 1, 'animate_res': [], 'skills': [], 'specials': []}
        self.send(20010, values={'round': 1, 'round_wave': 1, 'wave_max': 1, 'wave_no': 1,
                                 'atk_formation_type': 0, 'atk_formation_lev': 0,
                                 'def_formation_type': 0, 'def_formation_lev': 0,
                                 'is_observer': 0, 'effect_id': '',
                                 'order_list': [{'id': 1000}, {'id': 2000}],
                                 'fighter_info_list': [role_f, mon_f]}, tag='战斗初始化')
        mon_hp = MON_STATS['hp_max']
        dmg = max(1, int(a['atk_s']) * DAMAGE_SCALE - MON_STATS['def_s'])
        rnd = 0
        while mon_hp > 0 and rnd < 30:
            rnd += 1
            mon_hp = max(0, mon_hp - dmg)
            died = 1 if mon_hp == 0 else 0
            self.send(20012, values={'round': rnd,
                                     'skill_play': [{'order': 1, 'user_id': 1000, 'skill_id': 10000,
                                                     'father_id': 0, 'father_skill_id': 0,
                                                     'passive_skill_id': 0, 'user_anger': 0,
                                                     'talk': '', 'notice': '',
                                                     'magic_play': [], 'summon_play': []}],
                                     'cooldown': []}, tag='回合%d 出手' % rnd)
            self.send(20013, values={'round': rnd, 'round_wave': 1, 'time': 0, 'wave_no': 1,
                                     'magic_play': [{'order': 1, 'target_anger': 0,
                                                     'target_id': 2000, 'source_id': 1000,
                                                     'hit': 1, 'hp_max': MON_STATS['hp_max'],
                                                     'hp': mon_hp, 'is_target_die': died,
                                                     'target_talk': '', 'magic_list': []}],
                                     'summon_play': [], 'order_list': [{'id': 1000}]},
                      tag='回合%d 伤害 -%d → 怪HP %d/%d' % (rnd, dmg, mon_hp, MON_STATS['hp_max']))
        self.send(20020, values={'result': 1}, tag='战斗结果=胜')
        self.send(20023, values={'type': 0, 'result': 1,
                                 'role_hurl_list': [{'rid': self.rid, 'srv_id': self.role['srv_id'],
                                                     'name': self.role['name'], 'group': 1,
                                                     'lev': self.role['lev'], 'sex': self.role['sex'],
                                                     'career': self.role['career'],
                                                     'hp_max': a['hp_max'], 'hp': a['hp_max'],
                                                     'hurt': 0, 'master_rid': 0, 'master_srv_id': '',
                                                     'id': 1000}],
                                 'val_list': [], 'msg': ''}, tag='结算')
        self.kill_reward(mon)

    def kill_reward(self, mon):
        """★ 2026-10-01（goal 50 轮 · round 7）改为**配置驱动**（替换掉 `[TEST_ONLY]` 占位值）。

        依据：`analysis/1.4.9/item/_config_drop.json`（由 `assets/src/config/config_drop.luac` 还原，
        29 条）里怪物 **20001** 的真实记录：
            {"mon_bid":20001, "drop_type":1, "coin":"{1000}", "wood":"{500}",
             "first":0, "core":0, "normal":{}, …}          ← 三个物品节**全空**
        并且 `analysis/1.4.9/item/drop_table.md:102` 明确把
        `20001 20002 20005 20006 20009 20010 20013 20014 20017 20018 20021 20022`
        列为"**三个掉落节全空（只有 coin/wood）**"。
        ⇒ 正确行为：**coin += 1000**、**不发任何物品**（我此前发的 `DROP_ITEM_BID` 与 +30 coin/+50 exp
           全是占位值，属**编造数据**，本轮纠正）。
        诚实标注：`wood=500` 在 APK 配置里真实存在，但本服 `roles` 表**没有 wood 列**
        ⇒ 本日志记下、**不落库**（标 UNKNOWN，不硬塞进别的货币字段）；
        经验值 `exp` 在客户端怪物配置里不存在（`server/config.json::mon_calibration_note` 已记）⇒ 不发。

        ⚠ **证据等级更正（goal 50 轮 · round 8，自我更正）**：
        上面这个 `coin="{1000}"` **不能称为"已验证的真实发放值"**。依据
        `analysis/1.4.9/item/drop_model.md:291`：「`Config.Drop`/`Config.DropItem` 是
        **服务端下发逻辑的客户端副本，客户端从不读取**」，该文档 §9.3 更明确写
        「**这批数据不能当作"绝世唐门 1.4.9 的掉落表"使用**」（其 29 个 `item_bid` 全在
        `51000`–`51066`，是别家 IP 的物品号池）。
        ⇒ 正确表述：这是**APK 配置表里的值**（目前唯一可得的口径），
        **不保证与服务端实际发放一致**；证据等级标 `[APK_CONFIG / 未实机验证]`。
        """
        r = apk_drop(int(mon['bid']))
        if r is None:
            log('  !! 怪物 %s 不在 APK 掉落配置里 ⇒ 不发击杀奖励（不编造）' % mon['bid'])
            return
        coin = parse_apk_num(r.get('coin'))
        wood = parse_apk_num(r.get('wood'))
        if coin:
            self.store.add_assets(self.rid, coin=coin)
        self.role = self.store.role(self.rid)
        log('  .. APK 掉落配置 怪物%s: coin=%s wood=%s drop_type=%s（wood 本服无字段 ⇒ 仅记录）'
            % (mon['bid'], coin, wood, r.get('drop_type')))
        if not _drop_has_items(r):
            log('  .. 怪物 %s 按 APK 配置**无物品掉落** ⇒ 不发明物（此前发的占位物已移除）' % mon['bid'])
            self.send(10302, values=self.role_values(), tag='击杀奖励同步(配置驱动)')
        else:
            item = self.store.bag_add(self.rid, DROP_ITEM_BID, 1, 0)
            self.send(10500, values={'bag_code': 1,
                                     'items': [{'id': item['item_id'], 'bid': item['bid'],
                                                'hero_bid': 0, 'bind': 0, 'intensify_lev': 0,
                                                'pos': 0, 'quantity': item['quantity'], 'ctime': 0,
                                                'expire_ts': 0, 'durable': 0, 'object': 0,
                                                'attrs_ext': [], 'attrs_ext_list': [],
                                                'attrs_ext_one_list': [], 'jewel_list': [],
                                                'str_ext_list': []}]},
                      tag='掉落进包 bid=%d' % item['bid'])
            self.send(10302, values=self.role_values(), tag='击杀奖励同步')
        # 反哺任务进度（[DOC] 实机日志：battle mission progress → [10020]）
        mon_bid = int(mon['bid'])
        for row in self.store.missions(self.rid):
            if int(row['status']) != 1:
                continue
            m = self.data.mission(int(row['mission_bid']))
            if not m:
                continue
            target, need = self.mission_target(m)
            if target == mon_bid or target == 0:
                self.store.mission_bump(self.rid, int(row['mission_bid']), 1)
                self.send(12400, values={'mission_list': self.visible_missions()},
                          tag='任务进度反哺 bid=%s' % row['mission_bid'])

    def on_12404(self, body):
        """放弃任务（`giveUpHandler`）。

        依据：`analysis/1.4.9/mission_protocol_verify.md:20,91` 与 `mission_status.md:77`
        —— `12404` 的中文名是**放弃任务**，CS `mission_bid:uint32` / SC `code,msg,mission_bid`（形状取自 `protocol/fields.json`）。
        ★ 参考服当时**不回包**（原文："当前不回包 = no-op；放弃功能暂无效，无报错"）。
          本服把它做成**真功能**（而不是回 `code=0` 的通用应答）：
          删掉该任务行 → 回 `code=1` → 推 `12406`（移除推送），与"提交后移除"用同一套语义。
        """
        cs = self.spec.read_cs(12404, body)
        bid = int(cs.get('mission_bid') or 0)
        row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (self.rid, bid))
        if not row:
            self.send(12404, values={'code': 0, 'msg': '未接取该任务', 'mission_bid': bid},
                      tag='放弃失败 bid=%d（未接取）' % bid)
            return
        self.store.mission_del(self.rid, bid)
        self.send(12404, values={'code': 1, 'msg': '', 'mission_bid': bid}, tag='放弃成功 bid=%d' % bid)
        self.send(12406, values={'del_mission_list': [{'mission_bid': bid}]},
                  tag='放弃后移除推送 bid=%d' % bid)

    def on_12414(self, body):
        """NPC 对话交任务（CS `talk_bid, mission_bid, npc_bid` ／ SC `mission_bid, npc_bid, code, msg`）。

        依据：`analysis/jstm_1.4.9/task_protocol.md:24`（形状）+ `protocol/fields.json`（权威形状）。
        `round152_gap_candidates.md:42` 记录该命令与 `config_guild_mission`/`config_mission_escort` 相关，
        但**语义细节未在本项目内确证** ⇒ 本服只做**与 `12403` 同义**的那一步（把已达条件的任务标记完成并发奖），
        其余情形一律**诚实拒绝**（`code=0` + 原因），不猜 NPC/护送语义。
        """
        cs = self.spec.read_cs(12414, body)
        bid = int(cs.get('mission_bid') or 0)
        npc = int(cs.get('npc_bid') or 0)
        m = self.data.mission(bid)
        row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (self.rid, bid))
        if not m or not row:
            self.send(12414, values={'mission_bid': bid, 'npc_bid': npc, 'code': 0,
                                     'msg': '未接取该任务'}, tag='12414 拒绝（未接取）')
            return
        _t, need = self.mission_target(m)
        if need and int(row['progress']) < need:
            self.send(12414, values={'mission_bid': bid, 'npc_bid': npc, 'code': 0,
                                     'msg': '条件未满足（%d/%d）' % (row['progress'], need)},
                      tag='12414 条件未满足')
            return
        self.store.mission_set(self.rid, bid, 2, int(row['progress']))
        self.send(12414, values={'mission_bid': bid, 'npc_bid': npc, 'code': 1, 'msg': ''},
                  tag='12414 完成 bid=%d' % bid)
        self.send(12405, values={'update_mission_list': self.visible_missions()}, tag='12414 任务列表更新')
        self.send(12406, values={'del_mission_list': [{'mission_bid': bid}]}, tag='12414 任务移除')
        self.grant_award(m)

    def on_12415(self, body):
        """交物品完成任务（CS `mission_bid, item_bid, item_num` ／ SC `mission_bid, item_bid, item_num, code, msg`）。

        形状依据：`analysis/jstm_1.4.9/task_protocol.md:25` + `protocol/fields.json`。
        ★ 纪律：**只在背包确有该物品且数量足够时**才扣减并完成；否则**诚实拒绝**（不凭空发完成、不部分扣减）。
        """
        cs = self.spec.read_cs(12415, body)
        bid = int(cs.get('mission_bid') or 0)
        item = int(cs.get('item_bid') or 0)
        num = int(cs.get('item_num') or 0) or 1
        m = self.data.mission(bid)
        row = self.store.one('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (self.rid, bid))
        if not m or not row:
            self.send(12415, values={'mission_bid': bid, 'item_bid': item, 'item_num': num,
                                     'code': 0, 'msg': '未接取该任务'}, tag='12415 拒绝（未接取）')
            return
        if not self.store.bag_has(self.rid, item, num):
            self.send(12415, values={'mission_bid': bid, 'item_bid': item, 'item_num': num,
                                     'code': 0, 'msg': '物品不足（需要 %d 个 bid=%d）' % (num, item)},
                      tag='12415 拒绝（物品不足）')
            return
        self.store.bag_del(self.rid, item, num)
        self.store.mission_set(self.rid, bid, 2, int(row['progress']))
        self.send(12415, values={'mission_bid': bid, 'item_bid': item, 'item_num': num,
                                 'code': 1, 'msg': ''}, tag='12415 完成 bid=%d（交 bid=%d x%d）' % (bid, item, num))
        self.send(10500, values={'bag_code': 1, 'items': []}, tag='12415 交物品后背包刷新')
        self.send(12405, values={'update_mission_list': self.visible_missions()}, tag='12415 任务列表更新')
        self.send(12406, values={'del_mission_list': [{'mission_bid': bid}]}, tag='12415 任务移除')
        self.grant_award(m)

    # ---- 使用物品 / 开礼包（10505）------------------------------------------
    # 依据：`analysis/jstm_1.4.9/inventory_protocol.md:15`
    #   CS 10505: code:uint8; item_id:uint32; use_num:uint16; type:uint32; bid:uint32
    #   SC 10505: code:uint8; msg:string; item_bid:uint32
    #   且该文档把 10505 标为**参考服已实现**（CS ✅ / SC ✅）。
    # ★ 内容取自**真实礼包表** `item_gift.json`（见模块顶部 `item_gift()`）：
    #   物品 bid 进背包并推 `10500`；内容里的小数字（1/2/3/4/15）是**货币/经验码** ⇒ 加货币、不建物品。
    #   不是礼包或查不到内容 ⇒ **诚实拒绝**（code=0），不编造产出。
    def on_10505(self, body):
        cs = self.spec.read_cs(10505, body)
        bid = int(cs.get('bid') or cs.get('item_id') or 0)
        gift = item_gift(bid)
        if not gift:
            self.send(10505, values={'code': 0, 'msg': '该物品无可确证的礼包内容', 'item_bid': bid},
                      tag='使用失败 bid=%d（礼包表里没有内容）' % bid)
            return
        got_items, got_assets = [], {}
        for pair in gift:
            if not (isinstance(pair, (list, tuple)) and len(pair) >= 2):
                continue
            code, num = int(pair[0]), int(pair[1] or 1)
            if code in ASSET_CODE:
                k = ASSET_CODE[code]
                got_assets[k] = got_assets.get(k, 0) + num
            else:
                got_items.append((code, num))
        pushed, skipped = [], []
        for code, num in got_items:
            # ★ 2026-10-01（goal 50 轮 · round 16）**照参考服的做法加过滤**：
            #   `analysis/1.4.9/partner_jubaopen_item_effects.md:93-99` 记录参考服实现为
            #       `for cb, cn in gift_contents(bid): if is_valid_item(cb): db_bag_add(...)`
            #   ⇒ **只在物品表里确有此 bid 时才进包**；查不到的**跳过并如实记录**，
            #     绝不为未知 bid 建背包行（那等于编造物品）。
            if not self.data.item_ok(code):
                skipped.append(code)
                continue
            it = self.store.bag_add(self.rid, code, max(1, num), 0)
            pushed.append({'id': it['item_id'], 'bid': it['bid'], 'hero_bid': 0, 'bind': 0,
                           'intensify_lev': 0, 'pos': 0, 'quantity': it['quantity'], 'ctime': 0,
                           'expire_ts': 0, 'durable': 0, 'object': 0, 'attrs_ext': [],
                           'attrs_ext_list': [], 'attrs_ext_one_list': [], 'jewel_list': [],
                           'str_ext_list': []})
        if skipped:
            log('  .. 礼包 %s 内容里有 %d 个 bid 不在本作物品表 ⇒ 跳过（不编造物品）: %s'
                % (bid, len(skipped), skipped[:6]))
        if got_assets:
            self.store.add_assets(self.rid, **got_assets)
            self.role = self.store.role(self.rid)
        if pushed:
            self.send(10500, values={'bag_code': 1, 'items': pushed},
                      tag='开礼包进包 bid=%d items=%d' % (bid, len(pushed)))
        if got_assets:
            self.send(10302, values=self.role_values(), tag='开礼包货币同步')
        self.send(10505, values={'code': 1, 'msg': '', 'item_bid': bid},
                  tag='开礼包成功 bid=%d（物品 %d / 货币 %s）' % (bid, len(pushed), got_assets or '—'))

    # ---- 背包 -------------------------------------------------------------
    # ★ 2026-10-01（goal 50 轮 · round 1）**对照 `analysis/1.4.9/bag_code_mapping.md` 修正错误**：
    #   该文档从客户端 `game/backpack/backpack_const.luac` 取证到权威的 `BackPackConst.Bag_Code`：
    #       **1 = 背包(主)** 、**2/3 = 角色/伙伴装备** 、**4 = 仓库**
    #   我此前的实现有两处**确凿的错**（文档里连参考项目犯过的同一个错都记了）：
    #     ① `bag_code` 默认取 **7**（编造值，文档取值域里没有 7 作为主背包）
    #     ② **对任何 bag_code 都回主背包内容** ⇒ 客户端请求 2（装备栏）时拿到普通背包物品，
    #        于是"装备栏看不到装备" ⇒ 正是该文档描述的现象。
    #   ⇒ 本轮：主背包=1；2/3/4 分别按语义回**各自的空表**（本服没有装备/仓库表 ⇒ 诚实回空，
    #     绝不再把主背包内容冒充装备栏）。
    def on_10502(self, body):
        cs = self.spec.read_cs(10502, body)
        code = int(cs.get('bag_code') or 1)
        BAG_MAIN, BAG_EQUIP, BAG_PARTNER_EQUIP, BAG_STORE = 1, 2, 3, 4
        if code == BAG_MAIN:
            items = [{'id': b['item_id'], 'bid': b['bid'], 'hero_bid': 0, 'bind': b['bind'],
                      'intensify_lev': 0, 'pos': 0, 'quantity': b['quantity'], 'ctime': 0,
                      'expire_ts': 0, 'durable': 0, 'object': 0, 'attrs_ext': [],
                      'attrs_ext_list': [], 'attrs_ext_one_list': [], 'jewel_list': [],
                      'str_ext_list': []} for b in self.store.bag(self.rid)]
            tag = '背包(主) items=%d' % len(items)
        elif code in (BAG_EQUIP, BAG_PARTNER_EQUIP):
            # 本服未实现装备表 ⇒ **诚实回空**（不再冒充主背包）
            items, tag = [], '装备栏 bag_code=%d（本服未实现内容 ⇒ 空；不冒充主背包）' % code
        elif code == BAG_STORE:
            items, tag = [], '仓库 bag_code=4（本服未实现内容 ⇒ 空）'
        else:
            items, tag = [], '未实现 bag_code=%d（本服取值域 1/2/3/4）' % code
        self.send(10502, values={'bag_code': code, 'items': items}, tag=tag)

    # ---- 分发 -------------------------------------------------------------
    LOOP = {10001: 'on_10001', 1199: 'on_1199', 1110: 'on_1110', 10101: 'on_10101', 10102: 'on_10102', 10103: 'on_10103',
            10300: 'on_10300', 10204: 'on_10204', 12400: 'on_12400', 12402: 'on_12402',
            12403: 'on_12403', 12404: 'on_12404', 12414: 'on_12414', 12415: 'on_12415', 20002: 'on_20002', 10502: 'on_10502',
            10505: 'on_10505'}

    # ★ 真机实测（2026-10-01 13:26，服务端日志有 `>> 10302` / `>> 10303`）：客户端登录后
    #   **会主动单独请求**这四条角色数据 ⇒ 必须回**真实角色数据**；回落成通用零值会让
    #   客户端拿到全 0 的角色/属性，后续"角色列表 → 进场景"走不下去。
    ROLE_QUERIES = (10301, 10302, 10303, 10304)

    def ensure_role(self):
        """角色查询可能早于 10102 到来 ⇒ 兜底取默认角色，避免 role=None。"""
        if self.role:
            return self.role
        d = self.data.default_roles[0] if self.data.default_roles else {}
        rid = self.rid if self.rid is not None else d.get('rid', 1001)
        self.rid = rid
        self.role = (self.store.role(rid)
                     or self.store.ensure_role(rid, d.get('srv_id', '1'), d.get('name', 'DSH'),
                                               d.get('lev', 1), d.get('sex', 0), d.get('career', 1)))
        return self.role

    def on_role_query(self, cmd):
        self.ensure_role()
        self.send(cmd, values=self.role_values(), tag='角色数据(客户端请求)')

    def handle(self, cmd, body):
        log('  >> %s body(%d)=%s' % (cmd, len(body), body[:24].hex(' ')))
        if cmd in self.ROLE_QUERIES:
            try:
                self.on_role_query(cmd)
            except Exception:
                log('  !! 角色查询 %s 异常:\n%s' % (cmd, traceback.format_exc()))
            return
        fn = self.LOOP.get(cmd)
        if fn:
            try:
                getattr(self, fn)(body)
            except Exception:
                log('  !! 回环处理 %s 异常:\n%s' % (cmd, traceback.format_exc()))
            return
        # 回环外：能用规格答复的就答复（诚实：结构正确、内容为零）
        self.push_generic(cmd)


class TcpHandler(socketserver.BaseRequestHandler):
    def handle(self):
        srv = self.server.srv
        sess = Session(self.request, self.client_address, srv)
        log('=== 连接 %s:%s' % self.client_address)
        try:
            while True:
                data = self.request.recv(4096)
                if not data:
                    break
                frames = sess.parser.feed(data)
                log('  -- recv %d bytes → %d 帧' % (len(data), len(frames)))
                if not frames:
                    # ★ 关键取证：字节到了但解不出帧 ⇒ 必须留痕（否则会误判成"客户端没发"）
                    log('  !! 未解帧的字节：%s' % data[:48].hex(' '))
                for cmd, body in frames:
                    sess.handle(cmd, body)
        except OSError as e:
            log('=== 断开 %s:%s %r' % (self.client_address[0], self.client_address[1], e))
        finally:
            log('=== 关闭 %s:%s' % self.client_address[:2])
            try:
                self.request.close()
            except OSError:
                pass


class TcpServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, addr, srv):
        self.srv = srv
        socketserver.ThreadingTCPServer.__init__(self, addr, TcpHandler)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP 网关（[DOC] server_list_protocol.md：客户端读 `data.server_list`）
# ─────────────────────────────────────────────────────────────────────────────

class Gateway(BaseHTTPRequestHandler):
    srv = None
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        log('HTTP %s %s' % (self.command, self.path))

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _server_list(self):
        """[DOC] 与参考服 `normalize_server_item()` **逐字段对齐**（那份是实机验证过的）。

        实机教训（2026-09-30 本次）：只给 `name/srv_id/ip/port/...` 时，客户端会
        **每 6 秒重发一次** `POST /gateway/mobile/json`（正是文档里"反复重请求"的症状）；
        补上 `srv_name`/`erl_port`/`main_srv_id`（= `platform_zone` 形式）等客户端真正读的键。
        """
        out = []
        plate = str(self.srv.data.cfg.get('platform', 'ewan'))
        for s in self.srv.data.server_list:
            zone = str(s.get('zone_id', s.get('id', '1')))
            sid = str(s.get('srv_id') or s.get('id') or ('%s_%s' % (plate, zone)))
            name = s.get('srv_name') or s.get('name') or ('S%s' % zone)
            port = int(s.get('port', self.srv.game_port))
            out.append({
                'srv_id': sid, 'srv_name': name, 'name': name,
                'ip': s.get('ip', '127.0.0.1'), 'port': port, 'erl_port': port,
                'host': s.get('host', ''), 'platform': plate, 'zone_id': zone,
                'main_platform': s.get('main_platform', plate),
                'main_zone_id': str(s.get('main_zone_id', zone)),
                'main_srv_id': s.get('main_srv_id', '%s_%s' % (plate, zone)),
                'platform_flag': s.get('platform_flag', ''),
                'can_create_role': int(s.get('can_create_role', 1)),
                'maintain': int(s.get('maintain', 0)),
                'first_zone': int(s.get('first_zone', 0)),
                'recomed': int(s.get('recomed', s.get('is_new', 0))),
                'isnew': int(s.get('isnew', s.get('is_new', 0))),
                'open_time': int(s.get('open_time', s.get('begin_time', 0))),
                'begin_time': int(s.get('begin_time', 0)),
                'world_lev': int(s.get('world_lev', 1)),
                'state': int(s.get('state', 1)),
            })
        # ★ 2026-10-01（goal round 4）实机反汇编定位到的那一处 nil：
        #   `denglu_mgr.luac` proto#8 在"第二处拼接"里做 `platform .. '_' .. zone_id`
        #   （指令 202-205），而它读的那张表**有 platform、没有 zone_id** ⇒
        #   `attempt to concatenate field 'zone_id' (a nil value)` ⇒ 整段列表消费中止。
        #   客户端在 proto#8 里还会读 `local_srv_id`（指令 58-65，来自 UserDefault）。
        #   ⇒ 对策：**把同一套标识放到每一层**（条目内 / data 内 / 顶层），
        #     任何一层去读 zone_id/platform/srv_id 都不会是 nil。
        zone = str(srv_default_zone(self.srv))
        one = out[0] if out else {}
        sid0 = one.get('srv_id', '1')
        return {
            # 顶层也放一份（客户端有"取顶层当 data 用"的回退分支）
            'srv_id': sid0, 'platform': plate, 'zone_id': zone,
            'main_platform': plate, 'main_zone_id': zone, 'main_srv_id': one.get('main_srv_id', ''),
            'local_srv_id': {'srv_id': sid0, 'platform': plate, 'zone_id': zone},
            'data': {
                'server_list': out,
                'default_zone': zone,
                # data 层同样补齐（proto#8 里有多处直接从上层表取标识）
                'srv_id': sid0, 'platform': plate, 'zone_id': zone,
                'main_platform': plate, 'main_zone_id': zone,
                'main_srv_id': one.get('main_srv_id', ''),
                'local_srv_id': {'srv_id': sid0, 'platform': plate, 'zone_id': zone},
            },
        }

    def do_GET(self):
        p = self.path.split('?')[0]
        if p in ('/gateway/mobile/json', '/app/mobile/json', '/gateway/mobile/json/'):
            self._json(self._server_list())
        elif p.startswith('/notice'):
            self._json({'data': {'notice': ''}})
        else:
            self._json({'ok': True, 'path': p, 'server': 'minloop'})

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n) if n else b''
        if body:
            # 记下请求体：判断客户端"重请求"是在问什么（本次实机取证用得上）
            log('HTTP POST %s body=%s' % (self.path, body[:200].decode('utf-8', 'replace')))
        self.do_GET()


def srv_default_zone(srv):
    return getattr(srv, 'default_zone', '1')


class Server(object):
    def __init__(self, http_port, game_port, db_path, bind='0.0.0.0', default_zone='1'):
        self.spec = Spec()
        self.data = Data()
        self.store = Store(db_path)
        self.http_port, self.game_port = http_port, game_port
        self.bind, self.default_zone = bind, default_zone

    def run(self):
        Gateway.srv = self
        h = ThreadingHTTPServer((self.bind, self.http_port), Gateway)
        t = TcpServer((self.bind, self.game_port), self)
        log('最小回环服务器启动：HTTP %s:%d / TCP %s:%d / DB %s'
            % (self.bind, self.http_port, self.bind, self.game_port, self.store.path))
        log('协议规格：CS %d 条 / SC %d 条；任务 %d 条；NPC %d 个；怪物 %d 只'
            % (self.spec.n_cs, self.spec.n_sc, len(self.data.missions),
               len(self.data.npcs), len(self.data.mons)))
        threading.Thread(target=h.serve_forever, daemon=True).start()
        t.serve_forever()


def main(argv=None):
    ap = argparse.ArgumentParser(description='绝世唐门 1.4.9 最小回环服务器')
    ap.add_argument('--http', type=int, default=8099)
    ap.add_argument('--game', type=int, default=9099)
    ap.add_argument('--bind', default='0.0.0.0')
    ap.add_argument('--db', default=os.path.join(HERE, 'minloop.db'))
    ap.add_argument('--zone', default='1')
    args = ap.parse_args(argv)
    global LOG_PATH
    LOG_PATH = os.path.join(HERE, 'minloop_server.log')
    Server(args.http, args.game, args.db, args.bind, args.zone).run()
    return 0


if __name__ == '__main__':
    sys.exit(main())





