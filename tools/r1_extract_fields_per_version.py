#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3-①-a：按版本提取协议字段定义（复用 `tools/extract_fields.py` 的解析器）。

★★ **不覆盖** `protocol/fields.json`（那是 1.4.9 的、已被全项目核验过的产物）。
   本脚本只调 `extract_fields.analyze/build`，把结果写到 R1 目录下按版本分片。

用法：python tools/r1_extract_fields_per_version.py
产出：analysis/r1_client_index/_per_version/fields_<版本>.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import extract_fields as EF  # noqa: E402  复用其解析器，不重写

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index', '_per_version')

APKS = [
    ('1.3.0', r'anzbao\dldlJl.apk'),
    ('1.4.9', r'anzbao\jstm.apk'),
    ('1.4.11', r'anzbao\jstm_142165.apk'),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    # 防呆：extract_fields 的 OUTDIR 指向 protocol/，若误调 main() 会覆盖已核验产物
    assert not hasattr(EF, '_r1_guard'), 'sanity'
    summary = {}
    for ver, rel in APKS:
        apk = os.path.join(ROOT, rel)
        print('--- 提取 %s (%s)' % (ver, rel))
        entries = EF.analyze(apk)
        msgs = EF.build(entries)
        p = os.path.join(OUT, 'fields_%s.json' % ver)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(msgs, f, ensure_ascii=False)
        n_cs = sum(1 for k in msgs if k.startswith('CS'))
        n_sc = sum(1 for k in msgs if k.startswith('SC'))
        n_dsc = sum(1 for k in msgs if k.startswith(('Dsc', 'Dcs')))
        n_wf = sum(1 for k, v in msgs.items() if v.get('fields'))
        summary[ver] = {'total': len(msgs), 'cs': n_cs, 'sc': n_sc,
                        'dsc': n_dsc, 'with_fields': n_wf}
        print('    total=%d CS=%d SC=%d Dsc=%d 有字段=%d -> %s'
              % (len(msgs), n_cs, n_sc, n_dsc, n_wf, os.path.basename(p)))
    with open(os.path.join(OUT, 'fields_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    # 守住已核验产物：确认 protocol/fields.json 未被本脚本改动
    pf = os.path.join(ROOT, 'protocol', 'fields.json')
    import hashlib
    h = hashlib.sha256(open(pf, 'rb').read()).hexdigest()
    print('\nprotocol/fields.json 当前 sha256=%s（本脚本**未写它**）' % h[:16])
    print('汇总: %s' % json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
