# -*- coding: utf-8 -*-
"""inventory.handler —— 背包命令（Phase 2c）。

注册命令：10502（背包/装备/仓库列表）。
迁移来源（mock_server.py _reply if 块 L18398–18436）。
"""

from core import runtime
from core.dispatch import register
from protocol.frame import w_u8, pack_frame
from role.storage import role_state
from inventory.service import (BAG_MAIN, STORAGE_CODE, db_bag_get, db_store_get,
                              build_equip_items, build_bag_items)
from inventory import service as svc

log = runtime.log


@register(10502)
def handle_10502(h, cmd, body):
    """CS_10502{bag_code} → SC_10502{bag_code, items}（按 bag_code 分囊）。"""
    bag_code = body[0] if body else BAG_MAIN
    h._last_bag_code = bag_code
    _seen = getattr(h, '_bag_codes_seen', None)
    if _seen is None:
        _seen = h._bag_codes_seen = set()
    _seen.add(bag_code)
    rid = role_state(h.cfg).get('rid', 1001)
    if bag_code == BAG_MAIN:
        items = db_bag_get(rid, BAG_MAIN)
    elif bag_code in (2, 3):
        items = build_equip_items(rid, bag_code)
    elif bag_code == STORAGE_CODE:
        items = db_store_get(rid, bag_code)
    else:
        items = db_bag_get(rid, bag_code)
    h.request.sendall(pack_frame(
        10502, w_u8(bag_code) + build_bag_items(items)))
    if items:
        log('tcp.log', '  << 10502 SC_10502 bag_code=%d items=%d %r'
            % (bag_code, len(items),
               [(i['item_id'], i['bid'], i['quantity']) for i in items]))
    else:
        log('tcp.log', '  << 10502 SC_10502 bag_code=%d items=0 (空)' % bag_code)
    # ★★ 2026-10-17 修（用户报障"缺格子/空格显示"）：**跟上一条 SC_10510**
    #   （格子最大值/已开启格子数）。客户端的格子数取自它，而本服务端此前
    #   **从未推送过 10510**（全量日志无一条）⇒ 面板只能按默认值画格子。
    #   放在 10502 之后：客户端每次打开/切囊都会来要 10502，顺带就拿到格子数。
    svc.push_10510(h, rid, bag_code)
