# -*- coding: utf-8 -*-
"""Generate ui_restoration_order.md data: group B-class UI by system, cross-ref server status."""
import json, re, collections, os

BASE = r'C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit'
d = json.load(open(os.path.join(BASE, '_raw', '_aggregated_unknown.json'), encoding='utf-8'))
ui = json.load(open(os.path.join(BASE, 'ui_inventory.json'), encoding='utf-8'))

# server status map from server_capability_needs.md
scn = open(os.path.join(BASE, 'server_capability_needs.md'), encoding='utf-8').read()
pattern = re.compile(r'^###\s+(SYS_\w+)\s+(.+?)\s+—\s+【(.+?)】', re.M)
server_status = {}
for m in pattern.finditer(scn):
    server_status[m.group(1)] = m.group(3)

# csm impl_status
csm = json.load(open(os.path.join(BASE, 'client_server_matrix.json'), encoding='utf-8'))
impl_status = {s['system_id']: s.get('impl_status','?') for s in csm['systems']}
ev_tier = {s['system_id']: s.get('evidence_tier','?') for s in csm['systems']}

# group B entries by system_id
by_sys = collections.defaultdict(list)
for e in ui['entries']:
    if e['status'] == 'B':
        by_sys[e['system_id']].append(e)

# A entries
a_entries = [e for e in ui['entries'] if e['status']=='A']

print('=== A class 18 (reference baseline) ===')
for e in a_entries:
    print('  {} | {} | {} | {}'.format(e['ui_name'], e['module'], e['system_id'], e['system_name']))

print()
print('=== B class grouped by system ({} systems) ==='.format(len(by_sys)))
rows = []
for sid, lst in sorted(by_sys.items()):
    sv = server_status.get(sid, '?')
    im = impl_status.get(sid, '?')
    ev = ev_tier.get(sid, '?')
    names = [e['ui_name'] for e in lst]
    rows.append((sid, lst[0]['system_name'], sv, im, ev, len(lst), names))
    print('  {} | {} | server={} | impl={} | ev={} | n={}'.format(sid, lst[0]['system_name'][:30], sv, im, ev, len(lst)))

# Save for the md generator
out = {
    'a_entries': [{'ui_name':e['ui_name'],'module':e['module'],'system_id':e['system_id'],'system_name':e['system_name']} for e in a_entries],
    'b_by_system': [{'system_id':r[0],'system_name':r[1],'server_status':r[2],'impl_status':r[3],'evidence_tier':r[4],'count':r[5],'ui_names':r[6]} for r in rows],
}
json.dump(out, open(os.path.join(BASE,'_raw','_b_grouped.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
