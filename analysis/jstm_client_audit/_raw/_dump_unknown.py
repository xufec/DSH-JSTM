# -*- coding: utf-8 -*-
import json
d = json.load(open(r'C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\_raw\_aggregated_unknown.json', encoding='utf-8'))
print('=== C class (27) ===')
for c in d['ui_inventory']['C_icon_only']:
    print('  {} | {} | {} | {}'.format(c['ui_name'], c['module'], c['system_id'], c['system_name']))
print()
print('=== D class (8) ===')
for c in d['ui_inventory']['D_removed_1_4_11']:
    print('  {} | {} | {} | {}'.format(c['ui_name'], c['module'], c['system_id'], c['system_name']))
print()
print('=== csm UNKNOWN 9 ===')
for c in d['client_server_matrix']['UNKNOWN_evidence_tier']:
    print('  {} | {} | {} | {}'.format(c['system_id'], c['system_name'], c['impl_status'], c['evidence_tier']))
print()
print('=== csm INFERENCE 17 ===')
for c in d['client_server_matrix']['INFERENCE_evidence_tier']:
    print('  {} | {} | {} | {}'.format(c['system_id'], c['system_name'], c['impl_status'], c['evidence_tier']))
print()
print('=== vdm UNKNOWN cells ===')
for c in d['version_diff_matrix']['UNKNOWN_cells']:
    print('  {} | {} | {}'.format(c['dimension'], c['column'], c.get('notes','')[:80]))
print()
print('=== rct UNKNOWN cells ===')
for c in d['reference_capability_table']['UNKNOWN_cells']:
    print('  {} | {} | {} | {}'.format(c['project'], c['dimension'], c['status'], c['evidence_level']))
print()
print('=== sm present_in UNKNOWN lists ===')
print('1.3.0 UNKNOWN:', d['systems_master']['present_in_1_3_0_UNKNOWN'])
print('1.4.9 UNKNOWN:', d['systems_master']['present_in_1_4_9_UNKNOWN'])
print('1.4.11 UNKNOWN:', d['systems_master']['present_in_1_4_11_UNKNOWN'])
print('current_project_status UNKNOWN:', d['systems_master']['current_project_status_UNKNOWN'])
print()
print('=== supplemented_by_system ===')
for k,v in d['systems_master']['supplemented_by_system'].items():
    print(' ', k, '->', v)
print()
print('=== sm confidence != CONFIRMED (first 30) ===')
for c in d['systems_master']['evidence_NOT_CONFIRMED'][:30]:
    print('  {} | {} | {}'.format(c['system_id'], c['system_name'], c['confidence']))
print('  ... total', len(d['systems_master']['evidence_NOT_CONFIRMED']))
