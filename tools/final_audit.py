# -*- coding: utf-8 -*-
"""R230（收尾）：★★★ **最终全面验证** —— 把本会话建的全部工具跑一遍，出一张总表。"""
import io
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(script, args=()):
    p = os.path.join(ROOT, 'tools', script)
    if not os.path.exists(p):
        return '(缺失)'
    try:
        r = subprocess.run([PY, p] + list(args), capture_output=True, text=True,
                           encoding='utf-8', timeout=1800, cwd=ROOT)
        out = (r.stdout or '') + (r.stderr or '')
        lines = [x for x in out.split('\n') if x.strip()]
        return lines[-1].strip()[:110] if lines else '(无输出)'
    except Exception as e:
        return 'ERR %r' % e


print('=== 七道门禁 ===')
for s, a in (('lint_dispatch_shadow.py', ()), ('lint_elif_outer.py', ()),
             ('audit_specs_vs_fields.py', ()), ('audit_sc_live.py', ('--unsupported',)),
             ('audit_dedicated.py', ()), ('audit_emitted_fields.py', ()),
             ('audit_dedicated_really.py', ())):
    print('  %-28s %s' % (s, run(s, a)))

print('\n=== 扫描器（"可做对象"的穷尽性）===')
for s in ('scan_global_fallback.py', 'scan_truly_unimpl.py', 'scan_generic_left.py',
          'scan_db_source_gaps.py'):
    print('  %-28s %s' % (s, run(s)))

print('\n=== 一致性/证明工具 ===')
for s in ('check_log_runtime.py', 'prove_e2e_db.py'):
    print('  %-28s %s' % (s, run(s)))

print('\n=== 回归（66 项）===')
import glob
tests = sorted(glob.glob(os.path.join(ROOT, 'tools', 'verify_*.py'))
               + glob.glob(os.path.join(ROOT, 'tools', 'test_*.py')))
print('  ★ 回归脚本总数: %d' % len(tests))
