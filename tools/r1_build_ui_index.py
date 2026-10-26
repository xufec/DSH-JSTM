#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 3：UI 与按钮调用索引（复用 C2 权威 ui_id + 从 luac 提取按钮/回调/协议）。

## 纪律（任务书 §四）
  - 以 `docs/C2_全量界面恢复总表.csv`（401 行，ui_id 形如 `SYS_QUEST_003_UI_001`）为**权威基线**，
    **保留现有 UI ID、列结构与状态枚举**，不重建一套互相冲突的 ID
  - **明确区分**：资源存在 / 脚本存在 / 入口可达 / 交互已实现 / 协议已接通 / 实机验证通过
    ⇒ 本索引用独立字段表达，不把"有图片"或"有脚本"当成"界面已实现"
  - 静态提取到的按钮/回调标 `static_extract`，**不得**标成实机确认
"""
import csv
import json
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')
C2_CSV = os.path.join(ROOT, 'docs', 'C2_全量界面恢复总表.csv')
UI_INV = os.path.join(ROOT, 'analysis', 'jstm_client_audit', 'ui_inventory.json')

APKS = [
    ('1.3.0', r'anzbao\dldlJl.apk'),
    ('1.4.9', r'anzbao\jstm.apk'),
    ('1.4.11', r'anzbao\jstm_142165.apk'),
]

BTN_RE = re.compile(r'(btn|button|_btn$|click|touch|tab|toggle|select)', re.I)
HANDLE_RE = re.compile(r'^(handle|sender?|on)[A-Za-z_]*\d{3,6}$|^handle\d+$|^sender?\d+$')
NET_RE = re.compile(r'^(SendProtocal|GetPrototype|RegisterProtocal|SendMsg)$')
NOISE = re.compile(r'^[\d\W_]*$')


def scan_luac(blob):
    """解析一个 luac：返回字符串、RegisterProtocal 配对、GetPrototype 协议号、按钮名。"""
    r = parse_bytes(blob)
    strings = []
    for pt in r.protos:
        for k in (getattr(pt, 'kgc', None) or []):
            if isinstance(k, str):
                strings.append(k)
    uniq = sorted(set(strings))
    reg = []          # [(cmd, handler)]
    getp = []         # [cmd]
    for pt in r.protos:
        bc = getattr(pt, 'bc', None) or []
        # 预解析每条指令的 (op, A, D)
        ops = []
        for w in bc:
            ops.append((OPS[w & 0xff], (w >> 8) & 0xff, (w >> 16) & 0xffff))
        for i, (op, a, d) in enumerate(ops):
            if op == 'KSTR':
                s = kidx(pt, d)
                if not isinstance(s, str):
                    continue
                # 向前 4 条找 KSHORT（命令号）
                for j in range(max(0, i - 4), i):
                    if ops[j][0] == 'KSHORT':
                        cmd = ops[j][2]
                        if 1000 <= cmd <= 999999:
                            reg.append((cmd, s))
                            break
            if op == 'KSHORT' and 1000 <= d <= 999999:
                # 向后 4 条看是否 GetPrototype（该协议被"发送/查询"）
                for j in range(i + 1, min(len(ops), i + 5)):
                    if ops[j][0] == 'KSTR':
                        s = kidx(pt, ops[j][1])
                        break
        # GetPrototype(N) 的调用点：找 TGETS 'GetPrototype' 之后最近的 KSHORT
        for i, (op, a, d) in enumerate(ops):
            if op == 'TGETS':
                s = kidx(pt, d)
                if s == 'GetPrototype':
                    for j in range(i + 1, min(len(ops), i + 6)):
                        if ops[j][0] == 'KSHORT' and 1000 <= ops[j][2] <= 999999:
                            getp.append(ops[j][2])
                            break
    # 归并 RegisterProtocal：cmd → 最像 handler 的字符串
    regmap = {}
    for cmd, s in reg:
        if re.match(r'^(handle|sender?|on)', s) and re.search(r'[A-Za-z]', s):
            regmap.setdefault(cmd, s)
    btns = sorted({s for s in uniq
                   if len(s) <= 40 and BTN_RE.search(s) and not NOISE.match(s)
                   and not s.startswith('assets/')})[:40]
    handlers = sorted({s for s in uniq if re.fullmatch(r'handle\d{3,6}|sender?\d{3,6}', s)})[:60]
    return {
        'protos': len(r.protos),
        'string_count': len(strings),
        'unique_string_count': len(uniq),
        'register_protocal': {str(k): v for k, v in sorted(regmap.items())},
        'getprototype_cmds': sorted(set(getp)),
        'buttons': btns,
        'handlers': handlers,
        'net_identifiers': sorted({s for s in uniq if NET_RE.match(s)}),
        'strings': uniq,
    }


def build_version_index(ver, rel):
    apk = os.path.join(ROOT, rel)
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.endswith('.luac')]
    idx = {}
    fails = []
    for i, n in enumerate(names):
        try:
            idx[n] = scan_luac(z.read(n))
        except Exception as e:
            fails.append({'path': n, 'error': repr(e)})
            idx[n] = None
        if (i + 1) % 400 == 0:
            print('    %s %d/%d' % (ver, i + 1, len(names)))
    z.close()
    return idx, fails


def main():
    os.makedirs(OUT, exist_ok=True)
    # ── 权威基线：C2 CSV ──
    with open(C2_CSV, encoding='utf-8-sig') as f:
        c2 = list(csv.DictReader(f))
    print('C2 权威界面行数: %d' % len(c2))
    inv = json.load(open(UI_INV, encoding='utf-8'))

    # ── 逐版本扫描 luac ──
    per_ver = {}
    for ver, rel in APKS:
        cache = os.path.join(OUT, '_per_version', 'ui_luac_scan_%s.json' % ver)
        if os.path.exists(cache):
            per_ver[ver] = json.load(open(cache, encoding='utf-8'))
            print('  复用缓存 %s' % cache)
            continue
        print('--- 扫描 %s luac ...' % ver)
        idx, fails = build_version_index(ver, rel)
        payload = {'index': {k: v for k, v in idx.items() if v},
                   'failures': fails,
                   'scanned': len(idx), 'ok': sum(1 for v in idx.values() if v)}
        with open(cache, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False)
        per_ver[ver] = payload
        print('    ok=%d fail=%d' % (payload['ok'], len(fails)))

    tgt = per_ver['1.4.11']['index']

    # 模块名 → luac 路径（同版本）
    by_basename = {}
    for p in tgt:
        by_basename.setdefault(os.path.basename(p), []).append(p)

    def signals_for(mods):
        agg = {'register_protocal': {}, 'getprototype_cmds': set(), 'buttons': set(),
               'handlers': set(), 'files': [], 'protos': 0, 'strings': 0,
               'unresolved_modules': []}
        for m in mods:
            m = (m or '').strip()
            if not m or m == 'UNKNOWN':
                continue
            cand = by_basename.get(m) or by_basename.get(m + '.luac')
            if not cand:
                base = m if m.endswith('.luac') else m + '.luac'
                cand = by_basename.get(base)
            if not cand:
                # ★ 记录**无法解析的模块名**（不静默丢弃）
                agg['unresolved_modules'].append(m)
                continue
            # ★ 同名多路径时全部纳入（原来只取第一个 ⇒ 漏信号）
            for p in cand:
                e = tgt.get(p)
                if not e or p in agg['files']:
                    continue
                agg['files'].append(p)
                agg['protos'] += e['protos']
                agg['strings'] += e['unique_string_count']
                for k, v in e['register_protocal'].items():
                    agg['register_protocal'].setdefault(k, v)
                agg['getprototype_cmds'] |= set(e['getprototype_cmds'])
                agg['buttons'] |= set(e['buttons'])
                agg['handlers'] |= set(e['handlers'])
        out = dict(agg)
        out['getprototype_cmds'] = sorted(out['getprototype_cmds'])
        out['buttons'] = sorted(out['buttons'])[:40]
        out['handlers'] = sorted(out['handlers'])[:60]
        out['files'] = sorted(set(out['files']))          # ★ 去重（原来有重复项）
        out['unresolved_modules'] = sorted(set(out['unresolved_modules']))
        return out

    # ★ 模块级作用域聚合：按 `assets/src/game/<模块>/` 汇总该模块**全部** luac 的信号。
    #   为什么需要：实测 `*_view.luac` 自身**不持有协议**（协议在 panel/ctrl 里），
    #   所以"界面级 0 绑定"是**真实结构**、不是漏采。模块级聚合给 Agent 一条
    #   找协议的可行路径，但**必须显式标注为模块作用域**，不得当成该界面自己的绑定。
    module_scope = {}
    for p, e in tgt.items():
        parts = p.split('/')
        if 'game' in parts:
            i = parts.index('game')
            if i + 1 < len(parts):
                mod = parts[i + 1]
                a = module_scope.setdefault(mod, {'register_protocal': {}, 'getprototype_cmds': set(),
                                                  'buttons': set(), 'handlers': set(), 'files': 0})
                a['files'] += 1
                for k, v in e['register_protocal'].items():
                    a['register_protocal'].setdefault(k, v)
                a['getprototype_cmds'] |= set(e['getprototype_cmds'])
                a['buttons'] |= set(e['buttons'])
                a['handlers'] |= set(e['handlers'])
    for mod, a in module_scope.items():
        a['getprototype_cmds'] = sorted(a['getprototype_cmds'])
        a['buttons'] = sorted(a['buttons'])[:80]
        a['handlers'] = sorted(a['handlers'])[:80]
    print('模块级作用域聚合: %d 个模块' % len(module_scope))

    uis = []
    stat = Counter()
    for row in c2:
        ui_id = row.get('ui_id')
        inv_e = next((e for e in inv['entries']
                      if e.get('ui_name') == row.get('ui_name')
                      and e.get('system_id') == row.get('client_version', '').split('=')[0]),
                     None)
        # 用 ui_name + 系统 匹配 inventory（inventory 无 ui_id）
        inv_e = inv_e or next((e for e in inv['entries']
                               if e.get('ui_name') == row.get('ui_name')), None)
        mods = []
        if inv_e:
            mods = list(inv_e.get('related_lua_modules') or [])
            entry = inv_e.get('client_entry_luac')
            if entry:
                mods = [os.path.basename(entry)] + mods
        if not mods:
            lp = (row.get('lua_paths') or '').split(';')
            mods = [os.path.basename(x) for x in lp if x.strip()]
        sig = signals_for(mods)

        # 六态分离字段（任务书 §四：不得混为一谈）
        lua_exists = bool(sig['files'])
        res_exists = bool((row.get('resource_paths') or '').strip() not in ('', 'UNKNOWN'))
        protos_connected = bool(sig['register_protocal']) or bool(sig['getprototype_cmds'])
        # 模块作用域信号（**显式标注作用域**，不得当作该界面自己的绑定）
        mod_name = None
        for p in sig['files']:
            parts = p.split('/')
            if 'game' in parts:
                i = parts.index('game')
                if i + 1 < len(parts):
                    mod_name = parts[i + 1]
                    break
        if mod_name is None and inv_e:
            mod_name = inv_e.get('module')
        msig = module_scope.get(mod_name) if mod_name else None
        # ★ 未解析归因（R1.3-②）：**不能一律当成"提取失败"**。
        #   实测回 C2 台账核对：10 个"完全无法解析"的界面里，
        #     8 个 C2 已标 `BLOCKED / 1.3.0-only(已从1.4.11移除)`（= D 类，C0 status=D, conf=HIGH），
        #        正是 `RESTORE_各模块复原设计方案.md` §九 记录的"1.4.11 已移除 8 界面"；
        #     1 个 `lua_paths=候选activity_ctrl(按name分派)` ⇒ 是**按名动态分派**，不是找不到；
        #     1 个 C2 本就标 `NEEDS_IMPLEMENTATION / UNKNOWN(模块未定位)`。
        #   ⇒ 归因后：真实提取失败 = **0**。
        _unres = sig['unresolved_modules']
        _ver = (row.get('client_version') or '')
        _unres_blob = ' '.join(_unres)
        if not _unres:
            _uclass = None
        elif '1.3.0-only' in _ver or '已从1.4.11移除' in _ver or '1.3.0' in _unres_blob:
            _uclass = 'REMOVED_IN_TARGET（C2 标 1.3.0-only；D 类；非提取失败）'
        elif '按 name 分派' in _unres_blob or '按name分派' in _unres_blob \
                or '无独立 luac' in _unres_blob or '按name分派' in (row.get('lua_paths') or ''):
            # ★ 实测 27 个界面都属这一类：C2/inventory 的"模块名"本身是一句**说明**
            #   （"无独立 luac；由 activity_ctrl.luac 按 name 分派"），不是路径 ⇒ 非提取失败
            _uclass = 'DYNAMIC_DISPATCH（模块名即说明文字；按名分派，无静态路径；非提取失败）'
        elif 'UNKNOWN' in _unres_blob or 'UNKNOWN' in (row.get('lua_paths') or ''):
            _uclass = 'SOURCE_UNKNOWN（C2 源头即标 UNKNOWN）'
        else:
            _uclass = 'UNCLASSIFIED（待人工核对 C2 台账）'
        rec = dict(row)
        rec.update({
            'ui_id': ui_id,
            'r1_lua_files_resolved': sig['files'],
            'r1_lua_exists': lua_exists,
            'r1_unresolved_modules': sig['unresolved_modules'],
            'r1_unresolved_class': _uclass,
            'r1_module': mod_name,
            'r1_module_scope_signals': ({
                'scope': 'MODULE（非该界面自身绑定！仅供 Agent 沿模块找协议的线索）',
                'register_protocal': msig['register_protocal'],
                'getprototype_cmds': msig['getprototype_cmds'],
                'handlers': msig['handlers'][:40],
                'files_in_module': msig['files'],
            } if msig else None),
            'r1_resource_exists': res_exists,
            'r1_buttons_static': sig['buttons'],
            'r1_handlers_static': sig['handlers'],
            'r1_register_protocal': sig['register_protocal'],
            'r1_getprototype_cmds': sig['getprototype_cmds'],
            'r1_protocols_bound': protos_connected,
            'r1_interaction_known': bool(sig['buttons']),
            'r1_runtime_verified': row.get('current_status') == 'VERIFIED_WORKING',
            'r1_evidence_kind': 'static_extract',
            'r1_luac_proto_count': sig['protos'],
            'r1_luac_unique_strings': sig['strings'],
        })
        uis.append(rec)
        stat['total'] += 1
        stat['lua_exists'] += 1 if lua_exists else 0
        stat['buttons_found'] += 1 if sig['buttons'] else 0
        stat['protocols_bound'] += 1 if protos_connected else 0
        stat['runtime_verified'] += 1 if rec['r1_runtime_verified'] else 0

    out = {
        '_meta': {
            'phase': 'R1', 'step': '03_ui_and_buttons',
            'generated_by': 'tools/r1_build_ui_index.py',
            'authoritative_baseline': 'docs/C2_全量界面恢复总表.csv（ui_id/列/状态枚举原样保留）',
            'enrichment_sources': ['analysis/jstm_client_audit/ui_inventory.json',
                                   'APK 内 .luac 字节码（RegisterProtocal / GetPrototype / 字符串常量）'],
            'six_state_separation': {
                'resource_exists': 'r1_resource_exists',
                'script_exists': 'r1_lua_exists',
                'interaction_implemented': 'r1_interaction_known（静态提取到按钮标识）',
                'protocol_connected': 'r1_protocols_bound',
                'runtime_verified': 'r1_runtime_verified（沿用 C2 current_status == VERIFIED_WORKING）',
            },
            'discipline': '静态提取一律标 static_extract，不得当作实机确认',
        },
        'stats': dict(stat),
        'versions_scanned': {v: {'scanned': p['scanned'], 'ok': p['ok'],
                                 'fail': len(p['failures'])} for v, p in per_ver.items()},
        'entries': uis,
    }
    with open(os.path.join(OUT, 'R1_UI与按钮调用索引.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('\nUI 条目 %d ｜ 解析到 luac %d ｜ 提取到按钮 %d ｜ 绑定协议 %d ｜ 实机验证 %d'
          % (stat['total'], stat['lua_exists'], stat['buttons_found'],
             stat['protocols_bound'], stat['runtime_verified']))
    print('写出: R1_UI与按钮调用索引.json')


if __name__ == '__main__':
    main()
