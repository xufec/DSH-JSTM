#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 5：三版本差异（1.4.11 为主，对照 1.4.9 / 1.3.0）+ 解析失败与未知项清单。

纪律（任务书 §七）：
  - **不把旧版本的协议或业务逻辑直接复制到 1.4.11**；跨版本复用必须经目标版本证据验证
  - 差异**分别记录，不强行合并**
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')
PV = os.path.join(OUT, '_per_version')


def load(p, default=None):
    try:
        with open(p, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def main():
    shards = {v: load(os.path.join(PV, 'file_index_%s.json' % v)) for v in
              ('1.3.0', '1.4.9', '1.4.11')}
    scans = {v: load(os.path.join(PV, 'ui_luac_scan_%s.json' % v)) for v in
             ('1.3.0', '1.4.9', '1.4.11')}

    def luac_names(v):
        return {e['path'] for e in shards[v]['entries'] if e['category'] == 'lua_bytecode'}

    def base_names(v):
        return {os.path.basename(x) for x in luac_names(v)}

    def cfg_names(v):
        """配置表名 —— 注意：config_*.luac 在文件索引里 category 是 `lua_bytecode`
        （因为它确实是字节码），所以这里**按路径**取，不能按 category 取。"""
        return {os.path.basename(e['path']) for e in shards[v]['entries']
                if 'assets/src/config/' in e['path']}

    tgt = '1.4.11'
    diffs = {}
    for other in ('1.4.9', '1.3.0'):
        a, b = base_names(tgt), base_names(other)
        cfg_a, cfg_b = cfg_names(tgt), cfg_names(other)
        diffs['%s_vs_%s' % (tgt, other)] = {
            'luac_only_in_target': sorted(a - b),
            'luac_only_in_other': sorted(b - a),
            'luac_shared': len(a & b),
            'config_only_in_target': sorted(cfg_a - cfg_b),
            'config_only_in_other': sorted(cfg_b - cfg_a),
            'config_shared': len(cfg_a & cfg_b),
        }

    # ★★ 内容级差异（SHA256 比对）—— 原 R1 只比文件名集合，看不出"同名但被改"。
    #    这是**最有价值的一维**：新增/删除容易发现，**被改过的同名脚本**才是隐蔽风险。
    def hmap(v, pred):
        return {os.path.basename(e['path']): e['sha256']
                for e in shards[v]['entries'] if pred(e['path'])}

    content = {}
    for other in ('1.4.9', '1.3.0'):
        for label, pred in (('luac', lambda p: p.endswith('.luac')),
                            ('config', lambda p: 'assets/src/config/' in p)):
            ha, hb = hmap(tgt, pred), hmap(other, pred)
            shared = set(ha) & set(hb)
            mod = sorted(k for k in shared if ha[k] != hb[k])
            content['%s_vs_%s_%s' % (tgt, other, label)] = {
                'shared': len(shared),
                'identical': len(shared) - len(mod),
                'modified': len(mod),
                'modified_files': mod,
            }

    # 解析失败登记（**不得静默跳过、不得删原件**）
    failures = []
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        sc = scans.get(v) or {}
        for f in (sc.get('failures') or []):
            failures.append({'version': v, 'path': f['path'],
                             'stage': 'luac_parse', 'error': f['error'],
                             'original_preserved': True,
                             'apk': shards[v]['apk']})
        for e in shards[v]['entries']:
            if e['parse_status'] == 'UNKNOWN':
                failures.append({'version': v, 'path': e['path'], 'stage': 'classify',
                                 'error': e['parse_note'], 'original_preserved': True,
                                 'apk': shards[v]['apk']})
            elif e['parse_status'] == 'ENCRYPTED':
                failures.append({'version': v, 'path': e['path'], 'stage': 'decode',
                                 'error': e['parse_note'], 'original_preserved': True,
                                 'apk': shards[v]['apk']})

    # 协议跨版本
    pinv = load(os.path.join(ROOT, 'analysis', 'jstm_client_audit',
                             'protocol_inventory.json'), {})
    pv = Counter()
    proto_ver = []
    for p in (pinv.get('protocols') or []):
        vs = p.get('versions') or {}
        sig = (bool(vs.get('present_in_1_3_0')), bool(vs.get('present_in_1_4_9')),
               bool(vs.get('present_in_1_4_11')))
        pv[str(sig)] += 1
        if sig[2] and not sig[1]:
            proto_ver.append({'cmd': p.get('cmd'), 'name': p.get('name'),
                              'note': '仅 1.4.11 有（1.4.9 无）'})
        if sig[2] and not sig[0]:
            proto_ver.append({'cmd': p.get('cmd'), 'name': p.get('name'),
                              'note': '1.3.0 无、1.4.11 有'})

    out = {
        '_meta': {
            'phase': 'R1', 'step': '05_version_diff',
            'generated_by': 'tools/r1_build_version_diff.py',
            'target_version': tgt,
            'discipline': '旧版本证据不得直接复制到目标版本；跨版本复用须目标版本验证',
            'signature_order': '(present_in_1_3_0, present_in_1_4_9, present_in_1_4_11)',
            'content_diff_note': 'content_diff_sha256 用**逐文件 SHA256** 区分"同名且一致"与'
                                 '"同名但被改"——只比文件名集合会漏掉后者，而后者才是隐蔽风险',
        },
        'file_counts': {v: {'entries': shards[v]['entry_count'],
                            'luac': len(luac_names(v)),
                            'config': len(cfg_names(v)),
                            'status_counts': shards[v]['status_counts'],
                            'apk_sha256': shards[v]['apk_sha256']} for v in shards},
        'diffs': diffs,
        'content_diff_sha256': content,
        'protocol_version_signatures': dict(pv),
        'protocol_target_only': proto_ver,
        'parse_failures_and_unknowns': failures,
        'failure_counts': {'%s|%s' % k: v for k, v in
                           Counter((f['version'], f['stage']) for f in failures).items()},
    }
    p = os.path.join(OUT, 'R1_三版本差异与失败登记.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('三版本差异已算出；解析失败/未知登记 %d 条' % len(failures))
    for k, v in diffs.items():
        print('  %s: luac 仅目标 %d / 仅旧版 %d / 共有 %d | config 仅目标 %d / 仅旧版 %d'
              % (k, len(v['luac_only_in_target']), len(v['luac_only_in_other']),
                 v['luac_shared'], len(v['config_only_in_target']),
                 len(v['config_only_in_other'])))
    print('协议版本签名分布: %s' % dict(pv))
    print('写出: %s' % p)


if __name__ == '__main__':
    main()
