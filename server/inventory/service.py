# -*- coding: utf-8 -*-
"""inventory.service —— 背包/仓库/装备读路径（Phase 2c）。

迁移来源（mock_server.py）：
  BAG_MAIN / STORAGE_CODE      L5592 / L6290
  db_bag_get                   L5941–5951
  db_init_equip / db_equip_all L6194–6219
  db_store_init / db_store_get L6293–6317
  build_equip_items            L9194–9217
  build_bag_items              L9220–9240

写路径（db_bag_add/db_store_add/db_equip_put/take）本批保留在 mock_server，
Phase 后续再接 —— 本批只搬读路径以支撑 10502。
"""

import sqlite3

from core import runtime
from persistence.db import db_conn, db_release
from protocol.frame import w_u8, w_u16, w_u32, pack_frame

log = runtime.log

BAG_MAIN = 1          # 主背包 bag_code
STORAGE_CODE = 4      # BackPackConst.Bag_Code.STORAGE

# 背包初始容量。★ 依据 config.json 的 `volume_note`：
#   "各囊容量上限。用户要求'开放所有背包仓库空间' ⇒ 统一设为 200
#    （不是原版数值，是为可玩性做的**服务端级放宽**）"
# 2026-10-17：原实现默认 0（且 `bag_volume_default` 已从 config 删除）⇒ 新角色
#   **0 个格子**，配合"从不推 10510"就表现为用户报障的"缺格子/空格显示"。
BAG_VOLUME_DEFAULT = 200


def db_bag_get(rid, bag_code=BAG_MAIN):
    try:
        con = db_conn()
        con.row_factory = sqlite3.Row
        rows = con.execute('SELECT * FROM bag_items WHERE rid=? AND bag_code=? '
                           'ORDER BY pos', (rid, bag_code)).fetchall()
        db_release(con)
        return [dict(r) for r in rows]
    except Exception as e:
        log('tcp.log', '  !! db_bag_get failed: %r' % (e,))
        return []


def db_init_equip():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS equip_items (
        rid INTEGER, slot INTEGER, item_id INTEGER, bid INTEGER,
        hero_bid INTEGER, ctime INTEGER,
        PRIMARY KEY (rid, slot))""")
    con.commit()
    db_release(con)


def db_equip_all(rid):
    db_init_equip()
    con = db_conn()
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        'SELECT * FROM equip_items WHERE rid=? ORDER BY slot', (rid,))]
    con.row_factory = None
    db_release(con)
    return rows


# 装备槽上限。来源：config.json 的 `equip_type_slot`（100..110 → 1..11），
# 这里取 12 作为兜底上限（多留一格，避免"只差一格就换不了装"）。
EQUIP_SLOT_MAX = 12


def db_equip_free_slot(rid):
    """该角色身上**最小的空闲装备槽**（1..EQUIP_SLOT_MAX）；全满返回 0。

    ★ 2026-10-17 修：`mock_server.py` 的 10511（穿戴/换装）里调用了这个名字，但它
      **从未被定义过**（`NameError: db_equip_free_slot`），且那条路径当时还被上层的
      "slot is None ⇒ 拒绝"提前 return 拦死 —— 两处一起修。
    """
    used = set()
    for e in db_equip_all(rid):
        try:
            used.add(int(e.get('slot') or 0))
        except Exception:
            pass
    for s in range(1, EQUIP_SLOT_MAX + 1):
        if s not in used:
            return s
    return 0


def db_store_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS store_items (
        rid INTEGER, bag_code INTEGER, item_id INTEGER, bid INTEGER,
        pos INTEGER, quantity INTEGER, ctime INTEGER,
        PRIMARY KEY (rid, bag_code, item_id))""")
    con.commit()
    db_release(con)


def db_store_get(rid, bag_code=STORAGE_CODE):
    db_store_init()
    con = db_conn()
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(
        'SELECT * FROM store_items WHERE rid=? AND bag_code=? ORDER BY pos',
        (rid, bag_code))]
    con.row_factory = None
    db_release(con)
    return rows


# ---------------------------------------------------------------------------
# 背包容量（bag_volume） + SC_10510「格子最大值」
#   2026-10-17 从 mock_server.py 下沉到这里：因为 **10502 的 handler 在
#   inventory/handler.py**，它需要"回包后顺带推 10510"；而本包有
#   "禁止 import mock_server（循环 import 红线）" 的约定 ⇒ 容量与推送都放这里。
# ---------------------------------------------------------------------------

def db_init_bag_volume():
    """背包容量表（每角色每囊一行）。"""
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS bag_volume (
        rid INTEGER, bag_code INTEGER, volume INTEGER,
        PRIMARY KEY (rid, bag_code))""")
    con.commit()
    db_release(con)


def bag_volume_default():
    """初始容量：优先 config 的 `bag_volume_default`，否则 BAG_VOLUME_DEFAULT(=200)。"""
    try:
        v = int((runtime.CFG or {}).get('bag_volume_default') or 0)
    except Exception:
        v = 0
    return v or BAG_VOLUME_DEFAULT


def db_get_bag_volume(rid, bag_code=BAG_MAIN):
    """读该角色该囊容量；没有行就按默认值建一行。

    ★ 2026-10-17：默认值由 0 改为 `bag_volume_default()/200`。原来默认 0 ⇒ 新角色
      **一个格子都没有**（配合"从不推 10510"就是用户看到的"缺格子/空格显示"）。
      依据 config.json `volume_note`（用户要求开放所有空间，统一 200）。
    """
    db_init_bag_volume()
    con = db_conn()
    con.row_factory = sqlite3.Row
    row = con.execute('SELECT volume FROM bag_volume WHERE rid=? AND bag_code=?',
                      (rid, bag_code)).fetchone()
    con.row_factory = None
    if row is None:
        default = bag_volume_default()
        con.execute('INSERT OR IGNORE INTO bag_volume (rid,bag_code,volume) VALUES (?,?,?)',
                    (rid, bag_code, default))
        con.commit()
        db_release(con)
        return default
    v = int(row[0] or 0)
    db_release(con)
    return v


def db_set_bag_volume(rid, bag_code, volume):
    try:
        db_init_bag_volume()
        con = db_conn()
        con.execute('INSERT OR REPLACE INTO bag_volume (rid,bag_code,volume) VALUES (?,?,?)',
                    (rid, bag_code, int(volume)))
        con.commit()
        db_release(con)
        return True
    except Exception as e:
        log('tcp.log', '  !! db_set_bag_volume failed: %r' % (e,))
        return False


def build_10510(rid, bag_code=BAG_MAIN):
    """SC_10510{code:u8, volume:u8, open_volume:u8} —— **背包格子最大值/已开启格子数**。

    ★★ 2026-10-17 修（用户报障"缺格子 / 空格显示 / 整理刷新缺失"）：
      本服务端**从来没有推送过 10510**（全量日志 grep 无一条 `<< 10510`），
      而客户端的格子数正是取自它（`cmd_resolve_105.luac` proto#44 → bc#42 `handle_10510`；
      文档 `analysis/1.4.9/item/inventory_protocol_matrix.md` §3.8：**无 CS，纯 S→C**，
      `volume`=当前容量、`open_volume`=已开启格子数，配套 `getRemainCellNum`）
      ⇒ 面板只能按默认值画格子，扩容后也不会变多。

    本服"开放所有背包空间" ⇒ `open_volume = volume`。字段是 u8 ⇒ 夹到 0..255。
    """
    try:
        vol = int(db_get_bag_volume(rid, bag_code) or 0)
    except Exception:
        vol = 0
    vol = max(0, min(255, vol))
    return w_u8(1) + w_u8(vol) + w_u8(vol)


def push_10510(handler, rid, bag_code=BAG_MAIN):
    """推送 SC_10510（格子最大值）。所有"背包数据/容量"变更后都要调它。"""
    try:
        pkt = pack_frame(10510, build_10510(rid, bag_code))
        handler.request.sendall(pkt)
        # 帧结构 [u32 len][u16 cmd][u8 code][u8 volume][u8 open_volume] ⇒ 取 7/8 字节
        # （第一版写成 pkt[6] 取到的是 code，日志里"volume/open=1"是错的，别被它误导）
        log('tcp.log', '  << 10510 SC_10510 bag_code=%d volume=%d open=%d (%d bytes)'
            % (bag_code, pkt[7] if len(pkt) > 7 else -1,
               pkt[8] if len(pkt) > 8 else -1, len(pkt)))
    except Exception as e:
        log('tcp.log', '  !! 10510 push failed: %r' % (e,))


# ---------------------------------------------------------------------------
# 主动推送型刷新：SC_10503（删除）/ SC_10508（位置）
#
# ★★ 2026-10-17 关键定论（项目已查证，别再改错方向 —— 我第一次就差点改错）：
#   文档 `analysis/1.4.9/item/inventory_protocol_matrix.md` §8.3 明确列出
#     **10501(数量) / 10503(删除) / 10508(位置) / 10510(格子数) / 10543(扩展字段)
#       都是"服务端主动推送、无需 CS"**
#   而 **`SC_10502` 是"请求-应答型"**：客户端只在它自己发了 `CS_10502` 之后才处理，
#   服务端**主动推的 10502 会被忽略**（证据：mock_server 10554 块里 R 轮次的实测记录
#   "原实现推的是 SC_10502 …主动推的会被忽略 ⇒ 客户端本地状态不更新"）。
#   ⇒ 所以"删除/整理让界面刷新"必须用 **10503 / 10508**，不是 10502。
# ---------------------------------------------------------------------------

def build_10503(del_ids, code=1):
    """SC_10503{code:u8, del_ids_arr:table(item_id:u32)} —— 告知客户端"这些物品没了"。"""
    ids = [int(x) for x in (del_ids or [])]
    out = w_u8(int(code) & 0xff) + w_u16(len(ids))
    for i in ids:
        out += w_u32(i & 0xFFFFFFFF)
    return out


def build_10508(pairs, code=1):
    """SC_10508{code:u8, pos_up_arr:table(item_id:u32, new_pos:u8)} —— 物品位置更新。

    `pairs` = [(item_id, new_pos), ...]。整理/删除后位置变了就要推它，
    否则客户端仍按旧位置摆格子 ⇒ 出现"空洞格子/顺序不对"。
    """
    ps = [(int(i), int(p) & 0xff) for i, p in (pairs or [])]
    out = w_u8(int(code) & 0xff) + w_u16(len(ps))
    for i, p in ps:
        out += w_u32(i & 0xFFFFFFFF) + w_u8(p)
    return out


def push_10503(handler, del_ids, code=1):
    """推送 SC_10503（删除通知）。没有要删的就跳过。"""
    ids = [int(x) for x in (del_ids or [])]
    if not ids:
        return False
    try:
        handler.request.sendall(pack_frame(10503, build_10503(ids, code)))
        log('tcp.log', '  << 10503 SC_10503 删除通知 ids=%r' % (ids,))
        return True
    except Exception as e:
        log('tcp.log', '  !! 10503 push failed: %r' % (e,))
        return False


def push_10508(handler, pairs, code=1):
    """推送 SC_10508（位置更新）。没有变化就跳过。"""
    ps = list(pairs or [])
    if not ps:
        return False
    try:
        handler.request.sendall(pack_frame(10508, build_10508(ps, code)))
        log('tcp.log', '  << 10508 SC_10508 位置更新 %d 件: %r' % (len(ps), ps[:6]))
        return True
    except Exception as e:
        log('tcp.log', '  !! 10508 push failed: %r' % (e,))
        return False


def build_equip_items(rid, bag_code):
    """把装备表转成 SC_10502.items 形状（bag_code=2/3 装备栏）。"""
    want_hero = 1 if bag_code == 3 else 0
    out = []
    for e in db_equip_all(rid):
        if int(e.get('hero_bid') or 0) > 0 and want_hero == 0:
            continue
        if int(e.get('hero_bid') or 0) == 0 and want_hero == 1:
            continue
        out.append({
            'item_id': int(e.get('item_id') or 0),
            'bid': int(e.get('bid') or 0),
            'hero_bid': int(e.get('hero_bid') or 0),
            'bind': 0, 'intensify_lev': 0,
            'pos': int(e.get('slot') or 0),
            'quantity': 1,
            'ctime': int(e.get('ctime') or 0),
            'expire_ts': 0, 'durable': 0, 'object': 0,
        })
    return out


def build_bag_items(items):
    """SC_10500/10502 的 items 数组（16 字段/件，顺序取自权威 spec）。"""
    b = w_u16(len(items))
    for it in items:
        b += w_u32(it.get('item_id', 0))
        b += w_u32(it.get('bid', 0))
        b += w_u32(it.get('hero_bid', 0))
        b += w_u8(it.get('bind', 0))
        b += w_u8(it.get('intensify_lev', 0))
        b += w_u16(it.get('pos', 0))
        b += w_u16(it.get('quantity', 0))
        b += w_u32(it.get('ctime', 0))
        b += w_u32(it.get('expire_ts', 0))
        b += w_u16(it.get('durable', 0))
        b += w_u8(it.get('object', 0))
        b += w_u16(0)     # attrs_ext
        b += w_u16(0)     # attrs_ext_list
        b += w_u16(0)     # attrs_ext_one_list
        b += w_u16(0)     # jewel_list
        b += w_u16(0)     # str_ext_list
    return b


# ---------------------------------------------------------------------------
# 写路径（Phase 4-5 / P45-B 从 mock_server.py L5968 逐字迁入）
# ---------------------------------------------------------------------------
import time as _time


def db_bag_add(rid, bid, quantity, bag_code=BAG_MAIN, item_id=None, merge=True):
    """加物品（原 mock_server L5968，逐字搬迁）。`merge=True` 同 bid 叠加；
    `merge=False` 新增独立条目并保留 item_id（跨囊移动）。

    ★ 单点防御：无效 bid 直接拒绝并记日志，返回 None（收敛唯一写入口）。
    """
    from item.service import is_valid_item
    try:
        if not is_valid_item(bid):
            log('tcp.log', '  !! db_bag_add 拒绝无效物品 bid=%r qty=%r bag_code=%r'
                % (bid, quantity, bag_code))
            return None
        con = db_conn()
        con.row_factory = sqlite3.Row
        row = con.execute('SELECT * FROM bag_items WHERE rid=? AND bag_code=? AND bid=?',
                          (rid, bag_code, bid)).fetchone() if merge else None
        if row is None:
            if item_id is None:
                nxt = con.execute('SELECT COALESCE(MAX(item_id),0)+1 FROM bag_items '
                                  'WHERE rid=? AND bag_code=?', (rid, bag_code)).fetchone()[0]
                item_id = int(nxt)
            pos = con.execute('SELECT COALESCE(MAX(pos),0)+1 FROM bag_items '
                              'WHERE rid=? AND bag_code=?', (rid, bag_code)).fetchone()[0]
            con.execute('INSERT INTO bag_items (rid,bag_code,item_id,bid,pos,quantity,ctime) '
                        'VALUES (?,?,?,?,?,?,?)',
                        (rid, bag_code, item_id, bid, pos, quantity, int(_time.time())))
        else:
            item_id = int(row['item_id'])
            con.execute('UPDATE bag_items SET quantity = quantity + ? '
                        'WHERE rid=? AND bag_code=? AND item_id=?',
                        (quantity, rid, bag_code, item_id))
        con.commit()
        out = con.execute('SELECT * FROM bag_items WHERE rid=? AND bag_code=? AND item_id=?',
                          (rid, bag_code, item_id)).fetchone()
        db_release(con)
        return dict(out) if out else None
    except Exception as e:
        log('tcp.log', '  !! db_bag_add failed: %r' % (e,))
        return None
