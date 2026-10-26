#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 4：客户端调用链索引（含断点标记）。

链路（任务书 §五）：
  UI → 按钮/事件 → Lua 回调 → 业务函数 → 协议封装 → 网络发送
     → 服务端分发 → 服务端处理函数 → 业务 Service → 数据读写
     → 响应/推送 → 客户端分发 → 客户端回调 → 数据模型 → UI 刷新

**断点**（无证据即断，不得填造）：
  NO_UI_ENTRY / CALLBACK_UNKNOWN / REQUEST_NOT_FOUND / SERVER_HANDLER_MISSING /
  RESPONSE_UNKNOWN / CLIENT_CALLBACK_MISSING / PERSISTENCE_UNKNOWN / RUNTIME_NOT_VERIFIED

数据来源全部为**已建成的 R1 索引 + 现扫 mock_server 代码**，不重复扫 APK。
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')
SRV = os.path.join(ROOT, 'server')

DB_TABLE_RE = re.compile(r"\b(role_assets|roles|role_attr|bag_items|store_items|equip_items|"
                         r"missions|reward_log|dungeon_progress|guaji_state|role_skills|"
                         r"role_heros|role_mail|mall_bought|role_wing|role_shenqi|role_mingge|"
                         r"role_fabao|role_lingshou|role_ride|role_runes|role_halo|role_buffs|"
                         r"role_title|role_gt|role_guild|role_friend|role_team|role_marry|"
                         r"role_jiebai|role_market\w*|role_invest|role_qifu|role_tree|role_build\w*|"
                         r"chengjiu_progress|daily_progress|daily_lingqu|sign_got|levgift_got|"
                         r"arena_state|arena_record|peakwar_state|race_state|role_form|role_scratch\w*|"
                         r"bag_volume|role_point|role_answer|role_chat|role_moments|role_fashion|"
                         r"role_yuanshen|role_boss_kill|role_market|role_halo_equip|role_friend_req|"
                         r"role_team_invite|role_marry_propose|role_build_learn)\b")


def db_tables_near(line_no, window=120):
    """在服务端处理函数附近扫数据库表名（静态关联，标 static_extract）。"""
    lines = db_tables_near.LINES
    lo = max(0, line_no - 1)
    hi = min(len(lines), line_no - 1 + window)
    blob = '\n'.join(lines[lo:hi])
    return sorted(set(DB_TABLE_RE.findall(blob)))


def main():
    # ★ R1.3-③：持久化改为**精确映射**（按处理函数体三路证据解析），
    #   不再用"handler 行后 120 行"的邻域扫描（会跨函数误捕/漏捕）。
    pmap = {}
    ppath = os.path.join(OUT, 'R1_服务端持久化映射.json')
    if os.path.exists(ppath):
        pmap = {str(k): v for k, v in
                (json.load(open(ppath, encoding='utf-8')).get('by_cmd') or {}).items()}
        print('已加载精确持久化映射: %d 个命令号' % len(pmap))
    else:
        print('!! 缺 R1_服务端持久化映射.json，回退邻域扫描')
        open(os.path.join(SRV, 'mock_server.py'), encoding='utf-8',
             errors='replace').read()  # noqa
        db_tables_near.LINES = open(os.path.join(SRV, 'mock_server.py'),
                                    encoding='utf-8', errors='replace').read().split('\n')
    ui = json.load(open(os.path.join(OUT, 'R1_UI与按钮调用索引.json'), encoding='utf-8'))
    proto = json.load(open(os.path.join(OUT, 'R1_协议与字段索引.json'), encoding='utf-8'))
    srv = json.load(open(os.path.join(OUT, 'R1_服务端处理映射.json'), encoding='utf-8'))

    # cmd → 协议记录
    by_cmd = {}
    for p in proto['protocols']:
        if p.get('cmd') is not None:
            by_cmd[p['cmd']] = p
    # cmd → 活跃服务端位置
    srv_cmds = {int(k): v for k, v in srv['handlers'].items()}

    chains = []
    bp_stat = Counter()
    n = 0
    for row in ui['entries']:
        ui_id = row['ui_id']
        regp = row.get('r1_register_protocal') or {}
        getp = row.get('r1_getprototype_cmds') or []
        # 该界面涉及的协议号 = 注册的（收）+ 主动查的（发）
        cmds = sorted(set([int(c) for c in regp.keys()] + [int(c) for c in getp
                                                           if isinstance(c, int)]))
        if not cmds:
            n += 1
            chains.append({
                'chain_id': 'CHAIN_%04d' % n, 'ui_id': ui_id,
                'ui_name': row.get('ui_name'), 'system': row.get('ui_category'),
                'cmd': None,
                # ★ 段结构必须**恒为同一组键**：消费方（Agent/脚本）会直接取
                #   `segments['persistence']` 等；缺键会 KeyError（本批校验即抓到）。
                #   未知一律给 None，不省略键。
                'segments': {
                    'ui': {'value': row.get('ui_name'),
                           'source': 'docs/C2_全量界面恢复总表.csv', 'evidence': 'C0/C2 台账'},
                    'button': {'value': row.get('r1_buttons_static') or None,
                               'source': 'luac 字符串常量', 'evidence': 'static_extract'},
                    'lua_callback': {'value': None, 'source': None, 'evidence': None},
                    'protocol': {'value': None, 'classes': [], 'source': None, 'evidence': None},
                    'server_handler': {'value': None, 'source': None, 'evidence': None},
                    'persistence': {'value': None, 'source': None, 'evidence': None},
                    'client_callback': {'value': None, 'evidence': None},
                },
                'breakpoints': ['NO_UI_ENTRY' if not row.get('r1_buttons_static')
                                else 'REQUEST_NOT_FOUND'],
                'runtime_verified': bool(row.get('r1_runtime_verified')),
            })
            bp_stat[chains[-1]['breakpoints'][0]] += 1
            continue
        for cmd in cmds:
            n += 1
            p = by_cmd.get(cmd)
            handlers = [h for h in (srv_cmds.get(cmd) or []) if h.get('active')]
            loc = None
            tables = []
            if handlers:
                h = handlers[0]
                loc = '%s:%s' % (h['file'], h['line'])
            # ★ 精确持久化：按命令号取（不再依赖 handler 位置邻域）
            tables = sorted(pmap.get(str(cmd), {}).keys())
            bps = []
            if not row.get('r1_buttons_static'):
                bps.append('NO_UI_ENTRY')
            if not regp.get(str(cmd)):
                bps.append('CALLBACK_UNKNOWN')
            if p is None or not p.get('fields_by_class'):
                bps.append('REQUEST_NOT_FOUND')
            if not handlers:
                bps.append('SERVER_HANDLER_MISSING')
            cls = (p or {}).get('classes') or []
            if not any(c.startswith('SC') for c in cls):
                bps.append('RESPONSE_UNKNOWN')
            if p and p.get('client_callback_evidence') not in ('CONFIRMED', 'VERIFIED'):
                bps.append('CLIENT_CALLBACK_MISSING')
            if handlers and not tables:
                bps.append('PERSISTENCE_UNKNOWN')
            if not row.get('r1_runtime_verified'):
                bps.append('RUNTIME_NOT_VERIFIED')
            for b in bps:
                bp_stat[b] += 1
            chains.append({
                'chain_id': 'CHAIN_%04d' % n,
                'ui_id': ui_id, 'ui_name': row.get('ui_name'),
                'system': row.get('ui_category'),
                'cmd': cmd,
                'segments': {
                    'ui': {'value': row.get('ui_name'),
                           'source': 'docs/C2_全量界面恢复总表.csv', 'evidence': 'C0/C2 台账'},
                    'button': {'value': (row.get('r1_buttons_static') or ['UNKNOWN'])[:6],
                               'source': 'luac 字符串常量', 'evidence': 'static_extract'},
                    'lua_callback': {'value': regp.get(str(cmd)), 'source': 'luac RegisterProtocal',
                                     'evidence': 'static_extract'},
                    'protocol': {'value': cmd, 'classes': cls,
                                 'source': 'protocol/fields.json + proto_defs.py',
                                 'evidence': (p or {}).get('fields_evidence')},
                    'server_handler': {'value': loc, 'source': 'server 现扫',
                                       'evidence': 'static_scan' if loc else None},
                    'persistence': {'value': tables or None,
                                    'source': 'R1_服务端持久化映射.json（按处理函数体三路证据精确解析）',
                                    'evidence': 'static_extract' if tables else None},
                    'client_callback': {'value': regp.get(str(cmd)),
                                        'evidence': (p or {}).get('client_callback_evidence')},
                },
                'breakpoints': bps,
                'runtime_verified': bool(row.get('r1_runtime_verified')),
            })

    out = {
        '_meta': {
            'phase': 'R1', 'step': '04_call_chains',
            'generated_by': 'tools/r1_build_call_chain_index.py',
            'sources': ['R1_UI与按钮调用索引.json', 'R1_协议与字段索引.json',
                        'R1_服务端处理映射.json', 'server/mock_server.py（现扫）'],
            'breakpoint_kinds': ['NO_UI_ENTRY', 'CALLBACK_UNKNOWN', 'REQUEST_NOT_FOUND',
                                 'SERVER_HANDLER_MISSING', 'RESPONSE_UNKNOWN',
                                 'CLIENT_CALLBACK_MISSING', 'PERSISTENCE_UNKNOWN',
                                 'RUNTIME_NOT_VERIFIED'],
            'discipline': '任何一段无证据即在该段留空并记断点；静态提取不标实机确认',
        },
        'stats': {'chains': len(chains), 'breakpoint_counts': dict(bp_stat),
                  'runtime_verified_chains': sum(1 for c in chains if c['runtime_verified'])},
        'chains': chains,
    }
    with open(os.path.join(OUT, 'R1_客户端调用链索引.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('调用链 %d 条；断点分布: %s' % (len(chains), dict(bp_stat)))
    print('其中实机验证过的链: %d' % out['stats']['runtime_verified_chains'])
    print('写出: R1_客户端调用链索引.json')


if __name__ == '__main__':
    main()
