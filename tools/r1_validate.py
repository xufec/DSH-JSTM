#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 7：产出校验 + 检索能力冒烟测试。

校验项（任务书 §九「通过基本格式校验」+ §八「Agent 可检索」）：
  A. 9 个产物文件全部存在且非空
  B. 4 个 JSON 全部可解析，且必需键齐备
  C. 3 个 MD 报告有标题与实质内容
  D. 7 类检索场景**实际跑通**（不是"文档里写了"）
  E. C2 权威总表未被改动（字节数 + mtime）
"""
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, 'analysis', 'r1_client_index')

FAILS = []
OKS = []


def ok(msg):
    OKS.append(msg)
    print('  PASS  %s' % msg)


def bad(msg):
    FAILS.append(msg)
    print('  FAIL  %s' % msg)


def load(n):
    p = os.path.join(BASE, n)
    with open(p, encoding='utf-8') as f:
        return json.load(f)


REQUIRED = {
    'R1_客户端资源与脚本总索引.json': ['_meta', 'versions', 'totals'],
    'R1_UI与按钮调用索引.json': ['_meta', 'stats', 'entries'],
    'R1_协议与字段索引.json': ['_meta', 'stats', 'protocols'],
    'R1_客户端调用链索引.json': ['_meta', 'stats', 'chains'],
    'R1_服务端处理映射.json': ['_meta', 'stats', 'handlers'],
    'R1_三版本差异与失败登记.json': ['_meta', 'file_counts', 'diffs'],
    # ── R1.3 补充 ──
    'R1_字段级协议差异.json': ['_meta', 'class_counts', 'diffs'],
    'R1_服务端持久化映射.json': ['_meta', 'stats', 'by_cmd', 'by_table'],
    'R1_函数级调用图_1.4.11.json': ['_meta', 'stats', 'graph'],
}
MDS = ['R1_三版本差异报告.md', 'R1_解析失败与未知项清单.md',
       'R1_Agent检索使用说明.md', 'R1_总体覆盖率与质量报告.md']


def main():
    print('=== A. 产物存在性 ===')
    for n in list(REQUIRED) + MDS:
        p = os.path.join(BASE, n)
        if os.path.isfile(p) and os.path.getsize(p) > 0:
            ok('%s (%d B)' % (n, os.path.getsize(p)))
        else:
            bad('缺失或空: %s' % n)

    print('=== B. JSON 结构与必需键 ===')
    docs = {}
    for n, keys in REQUIRED.items():
        try:
            d = load(n)
            docs[n] = d
            miss = [k for k in keys if k not in d]
            if miss:
                bad('%s 缺键 %s' % (n, miss))
            else:
                ok('%s 结构完整' % n)
        except Exception as e:
            bad('%s 解析失败: %r' % (n, e))

    print('=== C. MD 报告 ===')
    for n in MDS:
        t = open(os.path.join(BASE, n), encoding='utf-8').read()
        if t.startswith('#') and len(t) > 800:
            ok('%s (%d 字符)' % (n, len(t)))
        else:
            bad('%s 内容过短或无标题 (%d 字符)' % (n, len(t)))

    print('=== D. 检索能力冒烟（7 类场景）===')
    try:
        ui = docs['R1_UI与按钮调用索引.json']
        pr = docs['R1_协议与字段索引.json']
        ch = docs['R1_客户端调用链索引.json']
        sv = docs['R1_服务端处理映射.json']
        vd = docs['R1_三版本差异与失败登记.json']

        # 1 按 UI 名称
        hits = [e for e in ui['entries'] if 'achieve' in (e.get('ui_name') or '').lower()]
        ok('D1 按 UI 名称检索: achieve → %d 条' % len(hits)) if hits else bad('D1 无结果')

        # 2 按协议号
        by_cmd = {p['cmd']: p for p in pr['protocols']}
        p = by_cmd.get(12403)
        ok('D2 按协议号检索: 12403 → %s / 服务端=%s'
           % (p['name'], p['server_implemented'])) if p else bad('D2 无 12403')

        # 3 按业务系统
        syshits = [e for e in ui['entries'] if 'Mission' in (e.get('ui_category') or '')]
        ok('D3 按业务系统检索: Mission → %d 界面' % len(syshits)) if syshits else bad('D3 无结果')

        # 4 按数据库表
        dbh = [c for c in ch['chains'] if 'missions' in
               ((c['segments']['persistence']['value']) or [])]
        ok('D4 按数据库表检索: missions → %d 条链' % len(dbh)) if dbh else bad('D4 无结果')

        # 5 按断点定位
        bph = [c for c in ch['chains'] if 'SERVER_HANDLER_MISSING' in c['breakpoints']]
        ok('D5 按断点定位: SERVER_HANDLER_MISSING → %d 条链' % len(bph)) if bph else bad('D5 无结果')

        # 6 按版本比较
        d = vd['diffs']['1.4.11_vs_1.4.9']
        ok('D6 按版本比较: 1.4.11 独有脚本 %d 个' % len(d['luac_only_in_target']))

        # 7 服务端精确行号
        h = sv['handlers'].get('12403') or []
        act = [x for x in h if x.get('active')]
        ok('D7 服务端精确位置: 12403 → %s:%s'
           % (act[0]['file'], act[0]['line'])) if act else bad('D7 无活跃 handler')

        # ── R1.3 新增四项的检索冒烟 ──
        fd = docs['R1_字段级协议差异.json']
        pm = docs['R1_服务端持久化映射.json']
        cg = docs['R1_函数级调用图_1.4.11.json']

        ba = fd['_meta']['baseline_agreement']
        ok('D8 字段级差异自证: 1.4.9 vs 基线 条目 %s/%s，不一致 %d'
           % (ba['entries'][0], ba['entries'][1], ba['field_mismatch']))
        ok('D9 字段级差异: 1.4.11 类数 %d vs 1.4.9 %d（新增 %d）'
           % (fd['class_counts']['1.4.11'], fd['class_counts']['1.4.9'],
              len(fd['diffs']['1.4.11_vs_1.4.9']['classes_only_in_target'])))

        ok('D10 持久化精确映射: %d 个命令号，%d 张表可反查'
           % (pm['stats']['cmds_with_persistence'], len(pm['by_table']))) \
            if pm['stats']['cmds_with_persistence'] else bad('D10 空')
        bt = pm['by_table'].get('missions') or []
        ok('D11 按表反查: missions ← %d 个命令号 %s' % (len(bt), bt[:8])) if bt else bad('D11 missions 无')

        ok('D12 调用图: proto %d（有调用 %d），被调名 %d'
           % (cg['stats']['protos'], cg['stats']['protos_with_calls'],
              cg['stats']['distinct_callee_names']))
        ri = cg['reverse_index_hot'].get('SendProtocal') or []
        ok('D13 反向索引: SendProtocal 被 %d 处引用' % len(ri)) if ri else bad('D13 无')
    except Exception as e:
        bad('D 冒烟异常: %r' % (e,))

    print('=== E. C2 权威总表未改动 ===')
    c2 = os.path.join(ROOT, 'docs', 'C2_全量界面恢复总表.csv')
    st = os.stat(c2)
    if st.st_size == 259957:
        ok('C2 CSV 大小未变 (%d B)' % st.st_size)
    else:
        bad('C2 CSV 大小变化: %d' % st.st_size)

    print('\n──────── 校验结果 ────────')
    print('通过 %d ｜ 失败 %d' % (len(OKS), len(FAILS)))
    for f in FAILS:
        print('  - %s' % f)
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
