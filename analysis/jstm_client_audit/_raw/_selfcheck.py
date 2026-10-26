# -*- coding: utf-8 -*-
"""Self-check: verify the two deliverables are complete and well-formed."""
import os, re

BASE = r'C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit'
art  = r'C:\Users\xu\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode\workspace\.sessions\38447329590799362\agents\s_000EmXNseoA\artifacts'

for fname in ['unknown_inventory.md', 'ui_restoration_order.md']:
    p = os.path.join(BASE, fname)
    a = os.path.join(art, fname)
    txt = open(p, encoding='utf-8').read()
    print('===', fname, '===')
    print('  project path:', p, '| exists:', os.path.exists(p), '| size:', os.path.getsize(p))
    print('  artifact path:', a, '| exists:', os.path.exists(a), '| size:', os.path.getsize(a))
    # Count lines
    lines = txt.split('\n')
    print('  lines:', len(lines))
    # Count sections (## headers)
    sections = [l for l in lines if l.startswith('## ')]
    print('  ## sections:', len(sections))
    for s in sections:
        print('    ', s)
    print()

# Count unknown_inventory entries
ui_txt = open(os.path.join(BASE,'unknown_inventory.md'), encoding='utf-8').read()
# Count table rows in §1.1, §1.3, §1.4, §2.2, §2.3, §3, §5.1, §5.2, §6.1, §7, §9
# Just count rows starting with | SYS_ or | item_ etc
table_rows = [l for l in ui_txt.split('\n') if l.startswith('| SYS_') or l.startswith('| item_') or l.startswith('| skill_') or l.startswith('| attr_') or l.startswith('| role_') or l.startswith('| wing_') or l.startswith('| shenqi') or l.startswith('| formation') or l.startswith('| buff_') or l.startswith('| mon_') or l.startswith('| npc') or l.startswith('| map_') or l.startswith('| dungeon') or l.startswith('| mall_') or l.startswith('| answer') or l.startswith('| chivalrous') or l.startswith('| mahatma') or l.startswith('| yzxy') or l.startswith('| 10') or l.startswith('| 20')]
print('unknown_inventory table rows (approx entries):', len(table_rows))

# Count restoration queue entries
uro_txt = open(os.path.join(BASE,'ui_restoration_order.md'), encoding='utf-8').read()
phase_rows = [l for l in uro_txt.split('\n') if re.match(r'\| \d+\.\d+', l)]
print('ui_restoration_order queue entries:', len(phase_rows))
phases = [l for l in uro_txt.split('\n') if l.startswith('### 阶段')]
print('phases:', len(phases))
for p in phases:
    print('  ', p)
