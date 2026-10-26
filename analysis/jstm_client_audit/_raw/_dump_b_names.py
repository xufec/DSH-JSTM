# -*- coding: utf-8 -*-
import json, os
BASE = r'C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit'
d = json.load(open(os.path.join(BASE,'_raw','_b_grouped.json'), encoding='utf-8'))
# Print B-class ui_names per system for the restoration doc
for sys in d['b_by_system']:
    print('### {} | {} | server={} | impl={} | ev={} | n={}'.format(
        sys['system_id'], sys['system_name'], sys['server_status'], sys['impl_status'], sys['evidence_tier'], sys['count']))
    for n in sys['ui_names']:
        print('   -', n)
