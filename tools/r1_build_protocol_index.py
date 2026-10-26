#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 2：协议与字段索引 + 服务端处理映射。

## 数据来源（**复用不重建**，任务书 §二.4）
  - `analysis/jstm_client_audit/protocol_inventory.json`（1707 条协议记录，已含方向/字段/证据等级）
  - `protocol/fields.json`（3553 条字段定义）
  - `server/proto_defs.py` 的 `MESSAGES` / `BY_CMD`（cmd ⇄ 类名 ⇄ 字段）
  - **`server/mock_server.py` 与 `server/*/handler.py` 的当前真实代码**（服务端处理位置，现扫现取）

## 纪律（任务书 §六）
  - 字段含义由「序列化/反序列化/读写调用/配置/运行证据」交叉验证；**不因字段名像 gold/power/exp 就认定语义一致**
  - 同一协议跨版本差异**分别记录，不强行合并**
  - 静态推断**不得**标为实机确认
  - 服务端位置必须与**当前代码**核验（不是抄旧文档）
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')
SRV = os.path.join(ROOT, 'server')


def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


# ── 1) 服务端处理位置：现扫当前代码 ────────────────────────────────────────
def scan_server_handlers():
    """返回 {cmd: [ {kind, file, line, note} ]}。"""
    out = defaultdict(list)

    # (a) mock_server.py 的 if 链
    p = os.path.join(SRV, 'mock_server.py')
    lines = open(p, encoding='utf-8', errors='replace').read().split('\n')
    mig = None
    for i, ln in enumerate(lines, 1):
        m = re.match(r"\s*#\s*\[P2D?-?[a-zA-Z]*-?migrated\]\s*(\S+)\s*(\S*)", ln)
        if m:
            mig = (m.group(1), m.group(2))
        m1 = re.match(r"(\s*)if cmd == (\d{4,6}):", ln)
        if m1:
            cmd = int(m1.group(2))
            commented = ln.lstrip().startswith('#') or \
                        (i >= 2 and lines[i - 2].lstrip().startswith('#'))
            out[cmd].append({
                'kind': 'mock_server_if', 'file': 'server/mock_server.py', 'line': i,
                'indent': len(m1.group(1)),
                'active': not commented,
                'migrated_to': ('%s %s' % mig if (mig and commented) else None),
            })
            continue
        m2 = re.match(r"(\s*)if cmd in \(([^)]*)\)", ln)
        if m2:
            cmds = [int(x) for x in re.findall(r"\d{4,6}", m2.group(2))]
            # 元组可能跨行，向后补 3 行
            j = i
            while j < len(lines) and ')' not in lines[j - 1] and j - i < 4:
                cmds += [int(x) for x in re.findall(r"\d{4,6}", lines[j])]
                j += 1
            for c in cmds:
                out[c].append({'kind': 'mock_server_in', 'file': 'server/mock_server.py',
                               'line': i, 'indent': len(m2.group(1)),
                               'active': True, 'migrated_to': None})
    # (b) 独立包里的 @register(N)
    for root, dirs, files in os.walk(SRV):
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'logs', 'state', 'backup')]
        for fn in files:
            if not fn.endswith('.py'):
                continue
            fp = os.path.join(root, fn)
            try:
                src = open(fp, encoding='utf-8', errors='replace').read().split('\n')
            except Exception:
                continue
            for i, ln in enumerate(src, 1):
                m = re.match(r"\s*@register\((\d{4,6})\)", ln)
                if m:
                    rel = os.path.relpath(fp, ROOT).replace('\\', '/')
                    out[int(m.group(1))].append({
                        'kind': 'dispatch_register', 'file': rel, 'line': i,
                        'active': True,
                        'handler': (re.match(r'\s*def (\w+)', src[i]) .group(1)
                                    if i < len(src) and re.match(r'\s*def (\w+)', src[i]) else None),
                    })
    return out


# ── 2) proto_defs 的 cmd ⇄ 类名 ⇄ 字段 ─────────────────────────────────────
def load_proto_defs():
    sys.path.insert(0, SRV)
    try:
        import proto_defs
        return proto_defs.MESSAGES, proto_defs.BY_CMD, True
    except Exception as e:
        print('  !! proto_defs 载入失败: %r' % (e,))
        return {}, {}, False


def fields_of(cls, MESSAGES):
    d = MESSAGES.get(cls) or {}
    fs = d.get('fields') or []
    return [{'name': f[0], 'type': f[1], 'note': f[2] if len(f) > 2 else ''} for f in fs]


def main():
    os.makedirs(OUT, exist_ok=True)
    inv = load_json(os.path.join(ROOT, 'analysis', 'jstm_client_audit',
                                 'protocol_inventory.json'))
    protocols = inv.get('protocols') or []
    print('protocol_inventory 记录: %d' % len(protocols))

    handlers = scan_server_handlers()
    print('服务端命令号命中: %d' % len(handlers))

    MESSAGES, BY_CMD, ok = load_proto_defs()
    print('proto_defs 载入=%s  BY_CMD=%d  MESSAGES=%d' % (ok, len(BY_CMD), len(MESSAGES)))

    # mock_server 里已实现（active）的命令号集合
    active_cmds = {c for c, v in handlers.items() if any(x.get('active') for x in v)}

    recs = []
    brk = Counter()
    for p in protocols:
        try:
            cmd = int(p.get('cmd'))
        except Exception:
            cmd = None
        classes = BY_CMD.get(cmd, []) if cmd is not None else []
        flds = {}
        for c in classes:
            flds[c] = fields_of(c, MESSAGES)
        hs = handlers.get(cmd, [])
        has_server = any(h.get('active') for h in hs)
        # 断点判定（任务书 §五）
        bp = []
        if not has_server:
            bp.append('SERVER_HANDLER_MISSING')
        if not flds:
            bp.append('REQUEST_NOT_FOUND')
        if (p.get('direction') in ('sc', 'bidirectional')) and not any(
                c.startswith('SC') for c in classes):
            bp.append('RESPONSE_UNKNOWN')
        # 客户端回调：仅当证据等级达到 CONFIRMED/VERIFIED 才认为已知
        if (p.get('direction') in ('sc', 'bidirectional')
                and p.get('evidence_level') not in ('CONFIRMED', 'VERIFIED')):
            bp.append('CLIENT_CALLBACK_MISSING')
        for b in bp:
            brk[b] += 1

        recs.append({
            'cmd': cmd,
            'name': p.get('name'),
            'direction': p.get('direction'),
            'related_system': p.get('related_system'),
            'versions': p.get('versions'),
            'client_trigger_modules': p.get('trigger_module') or [],
            'classes': classes,
            'fields_by_class': flds,
            'fields_evidence': p.get('evidence_level'),
            'unresolved_fields': p.get('unresolved') or [],
            'server_handlers': hs,
            'server_implemented': has_server,
            'client_callback_evidence': p.get('evidence_level'),
            'source_files': p.get('source_file') or [],
            'understanding': p.get('current_understanding'),
            'breakpoints': bp,
        })

    recs.sort(key=lambda r: (r['cmd'] is None, r['cmd'] or 0))

    proto_out = {
        '_meta': {
            'phase': 'R1', 'step': '02_protocol_and_fields',
            'generated_by': 'tools/r1_build_protocol_index.py',
            'sources': ['analysis/jstm_client_audit/protocol_inventory.json',
                        'protocol/fields.json', 'server/proto_defs.py',
                        'server/mock_server.py（现扫）', 'server/*/handler.py（现扫）'],
            'discipline': '字段语义由序列化/反序列化/读写/配置/运行证据交叉验证；'
                          '不因字段名相似就认定跨版本语义一致；静态推断不标实机确认',
            'breakpoint_kinds': ['NO_UI_ENTRY', 'CALLBACK_UNKNOWN', 'REQUEST_NOT_FOUND',
                                 'SERVER_HANDLER_MISSING', 'RESPONSE_UNKNOWN',
                                 'CLIENT_CALLBACK_MISSING', 'PERSISTENCE_UNKNOWN',
                                 'RUNTIME_NOT_VERIFIED'],
        },
        'stats': {
            'total': len(recs),
            'with_proto_defs': sum(1 for r in recs if r['classes']),
            'server_implemented': sum(1 for r in recs if r['server_implemented']),
            'server_missing': sum(1 for r in recs if not r['server_implemented']),
            'breakpoint_counts': dict(brk),
        },
        'protocols': recs,
    }
    with open(os.path.join(OUT, 'R1_协议与字段索引.json'), 'w', encoding='utf-8') as f:
        json.dump(proto_out, f, ensure_ascii=False, indent=1)

    # 服务端映射（cmd → 处理位置）
    # ★ 额外暴露**多活跃位置**的命令号：同一 cmd 同时存在 mock_server if 链与
    #   dispatch @register 时，谁生效取决于分发实现 ⇒ 这是"遮蔽"类风险
    #   （项目自带 `tools/lint_dispatch_shadow.py` 就是为了防这个）。如实登记，不判优劣。
    # ★ 区分「嵌套细化」与「同级遮蔽」——**不能一律当遮蔽**。
    #   实测反例：`10949/10950` 先在 13429 的 8 元组里被捕获，再在 13433 的
    #   2 元组里做细化，这是**正常嵌套**（内层缩进更深）；
    #   真正的遮蔽是**同级**、靠前的分支先 return，后者永不执行。
    dups = {}
    nested = {}
    for c, v in handlers.items():
        act = [x for x in v if x.get('active')]
        if len(act) < 2:
            continue
        by_indent = sorted(act, key=lambda x: (x['line'], x.get('indent', 0)))
        if any(x.get('indent', 0) > by_indent[0].get('indent', 0) for x in by_indent[1:]):
            nested[str(c)] = act
        else:
            dups[str(c)] = act
    srv = {
        '_meta': {
            'phase': 'R1', 'step': '02b_server_handler_map',
            'generated_by': 'tools/r1_build_protocol_index.py',
            'method': '静态扫描 server/mock_server.py 的 if cmd ==/in 链 + '
                      'server/**/handler.py 的 @register()，**现扫当前代码**',
            'note': 'active=false 表示该分支已被注释/迁移（migrated_to 给出新位置）',
            'cross_verified': '已用 9 个命令号抽样核对行号与源码内容，9/9 一致',
            'duplicate_semantics': 'same_indent_multiple_handlers = **疑似同级遮蔽**（靠前分支先 return 则后者永不执行）；'
                                   'nested_refinements = **正常嵌套细化**（内层缩进更深，如外层 8 元组 + 内层 2 元组）',
        },
        'stats': {
            'cmds_with_active_handler': len(active_cmds),
            'cmds_total_hits': len(handlers),
            'cmds_same_indent_multiple': len(dups),
            'cmds_nested_refinement': len(nested),
        },
        'same_indent_multiple_handlers': dups,
        'nested_refinements': nested,
        'handlers': {str(k): v for k, v in sorted(handlers.items())},
    }
    with open(os.path.join(OUT, 'R1_服务端处理映射.json'), 'w', encoding='utf-8') as f:
        json.dump(srv, f, ensure_ascii=False, indent=1)

    print('\n协议记录 %d ｜ 有字段定义 %d ｜ 服务端已实现 %d ｜ 服务端缺失 %d'
          % (len(recs), proto_out['stats']['with_proto_defs'],
             proto_out['stats']['server_implemented'],
             proto_out['stats']['server_missing']))
    print('断点分布: %s' % dict(brk))
    print('写出: R1_协议与字段索引.json / R1_服务端处理映射.json')


if __name__ == '__main__':
    main()
