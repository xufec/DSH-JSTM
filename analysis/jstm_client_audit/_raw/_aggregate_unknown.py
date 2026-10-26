# -*- coding: utf-8 -*-
"""PHASE C0 只读审计聚合脚本：从既有 JSON 聚合所有未确认条目。"""
import json, os, re, collections

BASE = r'C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit'
OUT  = os.path.join(BASE, '_raw', '_aggregated_unknown.json')

def L(name): return json.load(open(os.path.join(BASE, name), encoding='utf-8'))

sm   = L('systems_master.json')
ui   = L('ui_inventory.json')
di   = L('data_inventory.json')
pi   = L('protocol_inventory.json')
csm  = L('client_server_matrix.json')
vdm  = L('version_diff_matrix.json')
rct  = L('reference_capability_table.json')

result = {}

# ============ 1. systems_master ============
sys_list = sm['systems']
sm_unk = {
    'present_in_1_3_0_UNKNOWN':  [s['system_id'] for s in sys_list if s['present_in_1_3_0']=='UNKNOWN'],
    'present_in_1_4_9_UNKNOWN':  [s['system_id'] for s in sys_list if s['present_in_1_4_9']=='UNKNOWN'],
    'present_in_1_4_11_UNKNOWN':  [s['system_id'] for s in sys_list if s['present_in_1_4_11']=='UNKNOWN'],
    'current_project_status_UNKNOWN': [s['system_id'] for s in sys_list if s['current_project_status']=='UNKNOWN'],
    'evidence_NOT_CONFIRMED': [
        {'system_id': s['system_id'], 'system_name': s['system_name'], 'confidence': s['confidence']}
        for s in sys_list if s['confidence'] not in ('CONFIRMED',)
    ],
    # 55 unmapped protocol tokens: systems_master.protocols 引用但 fields.json/cmd_table 均无
    # 这些 cmd 在 protocol_inventory._meta.supplemented_cmds 里
    'supplemented_cmds': pi['_meta'].get('supplemented_cmds', []),
    # 方向不一致
    'direction_mismatches': pi['_meta'].get('systems_master_direction_mismatches', []),
}
# 找出哪些系统引用了 supplemented_cmds
supp = set(pi['_meta'].get('supplemented_cmds', []))
sm_unk['supplemented_by_system'] = collections.defaultdict(list)
for s in sys_list:
    for pid in s.get('protocol_ids', []):
        m = re.match(r'CS_(\d+)', pid) or re.match(r'SC_(\d+)', pid)
        if m and m.group(1) in supp:
            sm_unk['supplemented_by_system'][s['system_id']].append(pid)
sm_unk['supplemented_by_system'] = dict(sm_unk['supplemented_by_system'])
result['systems_master'] = sm_unk

# ============ 2. ui_inventory ============
entries = ui['entries']
ui_b = [{'ui_name': e['ui_name'], 'module': e['module'], 'system_id': e['system_id'],
         'system_name': e['system_name'], 'client_entry_luac': e['client_entry_luac'],
         'restore_difficulty': e.get('restore_difficulty','?'), 'confidence': e.get('confidence','?')}
        for e in entries if e['status']=='B']
ui_c = [{'ui_name': e['ui_name'], 'module': e['module'], 'system_id': e['system_id'],
         'system_name': e['system_name'], 'evidence': e.get('evidence','')}
        for e in entries if e['status']=='C']
ui_d = [{'ui_name': e['ui_name'], 'module': e['module'], 'system_id': e['system_id'],
         'system_name': e['system_name'], 'evidence': e.get('evidence','')}
        for e in entries if e['status']=='D']
ui_a = [{'ui_name': e['ui_name'], 'module': e['module'], 'system_id': e['system_id'],
         'system_name': e['system_name']}
        for e in entries if e['status']=='A']
result['ui_inventory'] = {
    'A_verified': ui_a,
    'B_unverified': ui_b,
    'C_icon_only': ui_c,
    'D_removed_1_4_11': ui_d,
    'counts': {'A': len(ui_a), 'B': len(ui_b), 'C': len(ui_c), 'D': len(ui_d)},
}

# ============ 3. data_inventory ============
unconfirmed_ids = di['unconfirmed_items']
unconfirmed_detail = []
for r in di['records']:
    if r['data_id'] in unconfirmed_ids or r.get('parse_confidence','') != 'VERIFIED':
        unconfirmed_detail.append({
            'data_id': r['data_id'],
            'name': r.get('name',''),
            'parse_confidence': r.get('parse_confidence',''),
            'missing_information': r.get('missing_information',''),
            'evidence': r.get('evidence',''),
        })
result['data_inventory'] = {
    'unconfirmed_ids': unconfirmed_ids,
    'unconfirmed_detail': unconfirmed_detail,
    'count': len(unconfirmed_ids),
}

# ============ 4. protocol_inventory ============
protos = pi['protocols']
# has_unresolved = 759
with_unresolved = [p for p in protos if p.get('unresolved')]
# no_fields = 73
no_fields = [p for p in protos if not p.get('fields')]
# ev_INFERENCE = 55
inference = [p for p in protos if p.get('evidence_level')=='INFERENCE']
# related_system UNKNOWN
sys_unknown = [p for p in protos if p.get('related_system')=='UNKNOWN']
# 实机 CS 带 rid 与 fields 冲突（13 条）——从 unresolved 文本里找
rid_conflict = [p for p in protos if any('rid' in str(u).lower() for u in p.get('unresolved',[]))]
result['protocol_inventory'] = {
    'total': len(protos),
    'with_unresolved_count': len(with_unresolved),
    'no_fields_count': len(no_fields),
    'inference_count': len(inference),
    'related_system_UNKNOWN_count': len(sys_unknown),
    'no_fields_samples': [{'cmd': p['cmd'], 'name': p.get('name',''), 'direction': p.get('direction','')} for p in no_fields[:20]],
    'inference_cmds': [{'cmd': p['cmd'], 'name': p.get('name','')} for p in inference],
    'unresolved_reason_examples': [{'cmd': p['cmd'], 'name': p.get('name',''), 'unresolved': p.get('unresolved',[])[:3]} for p in with_unresolved[:15]],
}

# ============ 5. client_server_matrix ============
csm_sys = csm['systems']
csm_unknown_evidence = [
    {'system_id': s['system_id'], 'system_name': s['system_name'],
     'impl_status': s.get('impl_status',''), 'evidence_tier': s.get('evidence_tier',''),
     'current_impl': s.get('current_impl','')[:200], 'remaining': s.get('remaining','')[:200]}
    for s in csm_sys if s.get('evidence_tier')=='UNKNOWN'
]
csm_inference = [
    {'system_id': s['system_id'], 'system_name': s['system_name'],
     'impl_status': s.get('impl_status',''), 'evidence_tier': s.get('evidence_tier','')}
    for s in csm_sys if s.get('evidence_tier')=='INFERENCE'
]
result['client_server_matrix'] = {
    'UNKNOWN_evidence_tier': csm_unknown_evidence,
    'INFERENCE_evidence_tier': csm_inference,
    'UNKNOWN_count': len(csm_unknown_evidence),
    'INFERENCE_count': len(csm_inference),
}

# ============ 6. version_diff_matrix ============
vdm_unknown_cells = []
for sm_row in vdm['systems']:
    for col in ('v130','v149','v1411'):
        if sm_row.get(col) == 'UNKNOWN':
            vdm_unknown_cells.append({'dimension': sm_row.get('system', sm_row.get('dimension','?')),
                                      'column': col, 'evidence': sm_row.get('evidence',''),
                                      'notes': sm_row.get('notes','')[:200]})
for m in vdm['scan_metrics']:
    for col in ('v130','v149'):
        if m.get(col) == 'UNKNOWN':
            vdm_unknown_cells.append({'dimension': m['dimension'], 'column': col,
                                      'evidence': m.get('evidence',''),
                                      'notes': m.get('notes','')[:200]})
result['version_diff_matrix'] = {'UNKNOWN_cells': vdm_unknown_cells, 'count': len(vdm_unknown_cells)}

# ============ 7. reference_capability_table ============
rct_unknown = []
for proj_name, proj in rct['projects'].items():
    for dim, cell in proj.items():
        if cell.get('status')=='UNKNOWN' or cell.get('evidence_level')=='UNKNOWN':
            rct_unknown.append({'project': proj_name, 'dimension': dim,
                                 'status': cell.get('status',''),
                                 'evidence_level': cell.get('evidence_level',''),
                                 'implementation': cell.get('implementation','')[:200],
                                 'borrowable': cell.get('borrowable','')[:200]})
result['reference_capability_table'] = {'UNKNOWN_cells': rct_unknown, 'count': len(rct_unknown)}

# ============ server_capability_needs 解析（从 md 文本） ============
scn_path = os.path.join(BASE, 'server_capability_needs.md')
scn_text = open(scn_path, encoding='utf-8').read()
# 匹配 ### SYS_xxx Name — 【状态】
pattern = re.compile(r'^###\s+(SYS_\w+)\s+(.+?)\s+—\s+【(.+?)】', re.M)
scn_parsed = []
for m in pattern.finditer(scn_text):
    scn_parsed.append({'system_id': m.group(1), 'name': m.group(2).strip(), 'status': m.group(3)})
result['server_capability_needs'] = {
    'parsed': scn_parsed,
    '缺失': [x for x in scn_parsed if x['status']=='缺失'],
    '部分': [x for x in scn_parsed if x['status']=='部分'],
}

# 输出
json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('WROTE', OUT)
print('systems_master present_in_1_3_0 UNKNOWN:', len(sm_unk['present_in_1_3_0_UNKNOWN']))
print('systems_master present_in_1_4_9 UNKNOWN:', len(sm_unk['present_in_1_4_9_UNKNOWN']))
print('systems_master present_in_1_4_11 UNKNOWN:', len(sm_unk['present_in_1_4_11_UNKNOWN']))
print('systems_master confidence!=CONFIRMED:', len(sm_unk['evidence_NOT_CONFIRMED']))
print('supplemented_cmds:', len(sm_unk['supplemented_cmds']))
print('supplemented_by_system keys:', list(sm_unk['supplemented_by_system'].keys()))
print('ui counts:', result['ui_inventory']['counts'])
print('data unconfirmed:', result['data_inventory']['count'])
print('proto with_unresolved:', result['protocol_inventory']['with_unresolved_count'])
print('proto no_fields:', result['protocol_inventory']['no_fields_count'])
print('proto inference:', result['protocol_inventory']['inference_count'])
print('csm UNKNOWN:', result['client_server_matrix']['UNKNOWN_count'])
print('csm INFERENCE:', result['client_server_matrix']['INFERENCE_count'])
print('vdm UNKNOWN cells:', result['version_diff_matrix']['count'])
print('rct UNKNOWN cells:', result['reference_capability_table']['count'])
print('scn 缺失:', len(result['server_capability_needs']['缺失']))
print('scn 部分:', len(result['server_capability_needs']['部分']))
