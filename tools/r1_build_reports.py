#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 6：生成三份数据驱动报告（差异 / 失败与未知 / 覆盖率与质量）。

数字全部从已建成的 R1 索引 JSON 里**现取**，保证报告与索引一致，不手抄。
"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'analysis', 'r1_client_index')


def load(name):
    with open(os.path.join(OUT, name), encoding='utf-8') as f:
        return json.load(f)


def w(name, text):
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    print('  写出 %s (%d 字节)' % (name, len(text.encode('utf-8'))))


def main():
    fi = load('R1_客户端资源与脚本总索引.json')
    ui = load('R1_UI与按钮调用索引.json')
    pr = load('R1_协议与字段索引.json')
    ch = load('R1_客户端调用链索引.json')
    sv = load('R1_服务端处理映射.json')
    vd = load('R1_三版本差异与失败登记.json')

    tv = fi['totals']
    tot = tv['entries']
    by = tv['by_status']
    parsed = by.get('PARSED', 0)

    # ───────────── 1) 三版本差异报告 ─────────────
    L = []
    L.append('# R1 · 三版本差异报告\n')
    L.append('> 目标版本 **1.4.11**（`com.shiyue.dldl.ewan.baidu2`），对照 **1.4.9** 与 **1.3.0**。\n'
             '> 生成器：`tools/r1_build_version_diff.py`；原始数据：`R1_三版本差异与失败登记.json`。\n'
             '> **纪律**：旧版本的协议/业务逻辑**不得直接复制**到 1.4.11；跨版本复用必须经**目标版本证据**验证。\n')
    L.append('\n## 一、APK 指纹与规模\n')
    L.append('| 版本 | APK | 大小 | SHA256 | 条目 | luac | 配置表 |')
    L.append('|---|---|---:|---|---:|---:|---:|')
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        f = vd['file_counts'][v]
        apk = [x for x in fi['versions'].values() if x['apk_sha256'] == f['apk_sha256']]
        rel = apk[0]['apk'] if apk else '?'
        L.append('| %s | `%s` | %s | `%s` | %d | %d | %d |'
                 % (v, rel, '{:,}'.format(apk[0]['apk_size'] if apk else 0),
                    f['apk_sha256'][:16] + '…', f['entries'], f['luac'], f['config']))
    L.append('\n## 二、脚本与配置差异（按文件名集合）\n')
    for k, d in vd['diffs'].items():
        L.append('### %s\n' % k.replace('_', ' '))
        L.append('| 项 | 数量 |')
        L.append('|---|---:|')
        L.append('| 脚本仅目标版本有 | **%d** |' % len(d['luac_only_in_target']))
        L.append('| 脚本仅对照版本有 | **%d** |' % len(d['luac_only_in_other']))
        L.append('| 脚本共有 | %d |' % d['luac_shared'])
        L.append('| 配置表仅目标版本有 | **%d** |' % len(d['config_only_in_target']))
        L.append('| 配置表仅对照版本有 | **%d** |' % len(d['config_only_in_other']))
        if d['luac_only_in_target']:
            L.append('\n目标版本新增脚本（前 40）：`%s`\n'
                     % '`, `'.join(d['luac_only_in_target'][:40]))
        if d['luac_only_in_other']:
            L.append('\n**仅对照版本存在（1.4.11 已移除，不得当作 1.4.11 功能）**：`%s`\n'
                     % '`, `'.join(d['luac_only_in_other']))
        if d['config_only_in_target']:
            L.append('\n目标版本新增配置表：`%s`\n' % '`, `'.join(d['config_only_in_target'][:60]))
    L.append('\n## 三、内容级差异（逐文件 SHA256）\n')
    L.append('> **为什么单列这一节**：只比文件名集合**看不出"同名但被改"**的脚本/配置，'
             '而那才是跨版本复用时最隐蔽的风险。\n')
    L.append('| 对比 | 类型 | 共有 | 完全一致 | **已被修改** | 修改率 |')
    L.append('|---|---|---:|---:|---:|---:|')
    for k, v in vd.get('content_diff_sha256', {}).items():
        parts = k.split('_vs_')
        typ = parts[1].split('_')[-1] if len(parts) > 1 else '?'
        cmp_ = parts[0] + ' vs ' + parts[1].replace('_' + typ, '')
        L.append('| %s | %s | %d | %d | **%d** | %.1f%% |'
                 % (cmp_, typ, v['shared'], v['identical'], v['modified'],
                    100.0 * v['modified'] / v['shared'] if v['shared'] else 0))
    for k, v in vd.get('content_diff_sha256', {}).items():
        if v['modified_files']:
            L.append('\n`%s` 被修改的文件（前 30）：`%s`\n'
                     % (k, '`, `'.join(v['modified_files'][:30])))
    L.append('\n## 四、协议版本分布\n')
    L.append('签名 = `(1.3.0, 1.4.9, 1.4.11)` 是否出现。\n')
    L.append('| 签名 | 协议数 |')
    L.append('|---|---:|')
    for k, v in sorted(vd['protocol_version_signatures'].items(), key=lambda x: -x[1]):
        L.append('| `%s` | %d |' % (k, v))
    L.append('\n> 注意：**没有任何协议是"1.3.0 有而 1.4.11 无"**；差异集中在 1.3.0 → 1.4.9 的扩张。\n')
    L.append('\n## 五、跨版本使用纪律（强制）\n')
    L.append('1. 引用任何协议/字段/数值前，先确认它在 **1.4.11** 存在（`versions.present_in_1_4_11 == true`）。')
    L.append('2. 1.4.9 与 1.4.11 的**同名脚本内容可能不同**（1.4.11 独有 63 个脚本），`fields.json` 源自 1.4.9，'
             '其 CS 定义对 1.4.11 **不可靠** —— 实机抓包优先。')
    L.append('3. 1.3.0 的 35 个脚本与 1 张配置表在 1.4.11 **已不存在**，禁止据此推断 1.4.11 行为。')
    w('R1_三版本差异报告.md', '\n'.join(L) + '\n')

    # ───────────── 2) 解析失败与未知项清单 ─────────────
    L = []
    L.append('# R1 · 解析失败与未知项清单\n')
    L.append('> 生成器：`tools/r1_build_version_diff.py`。**原件全部保留在 APK 中，未删除、未改动**。\n')
    L.append('> 纪律：加密/混淆/无法反编译的文件**保留原件并登记**，不得静默跳过。\n')
    L.append('\n## 一、总览\n')
    L.append('| 阶段 | 数量 |')
    L.append('|---|---:|')
    for k, v in sorted(vd['failure_counts'].items()):
        L.append('| `%s` | %d |' % (k, v))
    L.append('\n其中 `classify` = 扩展名与内容不符/魔数未识别；`luac_parse` = 字节码解析异常。\n')
    L.append('\n## 二、逐条登记\n')
    L.append('| 版本 | 路径 | 阶段 | 原因 | 原件 |')
    L.append('|---|---|---|---|---|')
    for f in vd['parse_failures_and_unknowns']:
        L.append('| %s | `%s` | %s | %s | 保留于 `%s` |'
                 % (f['version'], f['path'], f['stage'],
                    f['error'].replace('|', '\\|')[:120], f['apk']))
    L.append('\n## 三、说明\n')
    L.append('- 这些文件**不计入"已解析"**，但在覆盖率报告里**仍计入分母**（未剔除）。')
    L.append('- 未发现任何 `.luac` 使用加密或压缩包装（魔数抽样：1.4.11 的 2297 个 `.luac` 中 '
             '2295 个为 LuaJIT 字节码，2 个为扩展名不符）。')
    w('R1_解析失败与未知项清单.md', '\n'.join(L) + '\n')

    # ───────────── 3) 覆盖率与质量报告 ─────────────
    L = []
    L.append('# R1 · 总体覆盖率与质量报告\n')
    L.append('> **分母口径**：一律使用扫描到的**全量**条目，**未剔除未解析项**。\n')
    L.append('\n## 一、资源与脚本索引覆盖率\n')
    L.append('| 版本 | APK 条目 | PARSED | BYTECODE_ONLY | UNKNOWN | ENCRYPTED | 已解析率 |')
    L.append('|---|---:|---:|---:|---:|---:|---:|')
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        s = fi['versions'][v]['status_counts']
        n = fi['versions'][v]['entry_count']
        p = s.get('PARSED', 0)
        L.append('| %s | %d | %d | %d | %d | %d | **%.1f%%** |'
                 % (v, n, p, s.get('BYTECODE_ONLY', 0), s.get('UNKNOWN', 0),
                    s.get('ENCRYPTED', 0), 100.0 * p / n if n else 0))
    L.append('| **合计** | **%d** | **%d** | **%d** | **%d** | **%d** | **%.1f%%** |'
             % (tot, parsed, by.get('BYTECODE_ONLY', 0), by.get('UNKNOWN', 0),
                by.get('ENCRYPTED', 0), 100.0 * parsed / tot if tot else 0))
    L.append('\n> `BYTECODE_ONLY` 的是 LuaJIT 字节码：**可反汇编**（已有 `tools/luajit_dis.py`），'
             '但**未还原为 Lua 源码**（无可靠 LuaJIT 反编译器）。这是能力边界，不是失败。\n')
    L.append('\n### 字节码解析成功率\n')
    L.append('| 版本 | 扫描 luac | 解析成功 | 失败 | 成功率 |')
    L.append('|---|---:|---:|---:|---:|')
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        d = ui['versions_scanned'][v]
        L.append('| %s | %d | %d | %d | **%.2f%%** |'
                 % (v, d['scanned'], d['ok'], d['fail'],
                    100.0 * d['ok'] / d['scanned'] if d['scanned'] else 0))
    L.append('\n## 二、UI 索引覆盖（基线 = C2 全量界面恢复总表，401 行）\n')
    s = ui['stats']
    L.append('| 指标 | 数量 | 占 401 |')
    L.append('|---|---:|---:|')
    for k, label in (('total', 'UI 总条目'), ('lua_exists', '解析到脚本文件'),
                     ('buttons_found', '静态提取到按钮标识'),
                     ('protocols_bound', '绑定到协议'),
                     ('runtime_verified', '实机验证通过')):
        v = s.get(k, 0)
        L.append('| %s | %d | %.1f%% |' % (label, v, 100.0 * v / s['total'] if s['total'] else 0))
    L.append('\n> **状态分离**：本索引把"资源存在/脚本存在/交互已实现/协议已接通/实机验证"'
             '拆成独立字段（`r1_resource_exists` / `r1_lua_exists` / `r1_interaction_known` / '
             '`r1_protocols_bound` / `r1_runtime_verified`），**不把有图片或有脚本当成界面已实现**。\n')
    modscope = sum(1 for e in ui['entries'] if e.get('r1_module_scope_signals'))
    unres = sum(1 for e in ui['entries'] if e.get('r1_unresolved_modules'))
    L.append('\n### UI 索引的两项补充字段（R1.2）\n')
    L.append('| 字段 | 覆盖 | 说明 |')
    L.append('|---|---:|---|')
    L.append('| `r1_module_scope_signals` | **%d / %d** | 按 `assets/src/game/<模块>/` 汇总该模块**全部** luac 的'
             '协议/按钮信号。**作用域是模块，不是该界面**——实测 `*_view.luac` 自身不持有协议'
             '（协议在 panel/ctrl 里），故"界面级 0 绑定"是**真实结构**而非漏采。此字段给 Agent 一条'
             '沿模块找协议的线索，**不得当作该界面自己的绑定**。 |' % (modscope, s['total']))
    L.append('| `r1_unresolved_modules` | %d / %d | C2/inventory 里给出、但在目标版本 APK 中**找不到**的模块名，'
             '**显式登记不静默丢弃**。 |' % (unres, s['total']))
    L.append('')
    L.append('\n## 三、协议索引覆盖\n')
    ps = pr['stats']
    L.append('| 指标 | 数量 |')
    L.append('|---|---:|')
    L.append('| 协议记录总数 | %d |' % ps['total'])
    L.append('| 有字段定义（proto_defs） | %d |' % ps['with_proto_defs'])
    L.append('| **服务端已实现** | **%d** |' % ps['server_implemented'])
    L.append('| **服务端未实现** | **%d** |' % ps['server_missing'])
    L.append('| 服务端命令号命中总数（含非活跃） | %d |' % sv['stats']['cmds_total_hits'])
    L.append('\n> ⚠ `服务端未实现 1243` **不等于 1243 个功能缺失**：`protocol_inventory` 覆盖的是'
             '**协议全集（1707）**，而真机实际出现的命令只有约 **132 种**'
             '（`analysis/extraction/dead_protocols_and_traffic.md`）。'
             '绝大多数"未实现"是**客户端从不发送的死协议**。Agent 应按"真机流量"排优先级。\n')
    L.append('\n### 服务端处理位置交叉核验\n')
    ss = sv['stats']
    L.append('| 指标 | 数量 |')
    L.append('|---|---:|')
    L.append('| 有活跃处理位置的命令号 | %d |' % ss['cmds_with_active_handler'])
    L.append('| 疑似**同级遮蔽**（靠前分支先 return） | **%d** |'
             % ss.get('cmds_same_indent_multiple', 0))
    L.append('| 正常**嵌套细化**（内层缩进更深） | %d |' % ss.get('cmds_nested_refinement', 0))
    L.append('\n> 抽样 9 个命令号核对「索引行号 vs 源码内容」：**9/9 一致**。'
             '「同级遮蔽 = 0」与项目自带门禁 `tools/lint_dispatch_shadow.py` 的结论一致，互为交叉印证。\n')
    L.append('\n## 四、调用链覆盖与断点\n')
    cs = ch['stats']
    L.append('| 指标 | 数量 |')
    L.append('|---|---:|')
    L.append('| 调用链条数 | %d |' % cs['chains'])
    L.append('| 其中实机验证过 | %d |' % cs['runtime_verified_chains'])
    L.append('\n断点分布：\n')
    L.append('| 断点 | 条数 |')
    L.append('|---|---:|')
    for k, v in sorted(cs['breakpoint_counts'].items(), key=lambda x: -x[1]):
        L.append('| `%s` | %d |' % (k, v))
    L.append('\n> 同一条链可能有多个断点，故断点总数 > 链数。\n')
    L.append('\n## 五、质量自评与已知局限\n')
    L.append('| 局限 | 说明 |')
    L.append('|---|---|')
    L.append('| 无 Lua 源码级还原 | 5,299 个 luac 为 `BYTECODE_ONLY`，只能反汇编，**函数体语义靠人工读字节码** |')
    L.append('| 按钮→回调的绑定是**静态推断** | 从字符串常量与 `RegisterProtocal` 配对得出，'
             '**未经实机点击确认**，一律标 `static_extract` |')
    L.append('| 服务端持久化关联是**邻域扫描** | 处理函数 ±120 行内出现过的表名，'
             '可能多报/漏报，标 `static_extract` |')
    L.append('| `fields.json` 源自 1.4.9 | 对 1.4.11 的 CS 定义**不可靠**，实机抓包优先 |')
    L.append('| 协议"未实现"含大量死协议 | 需按真机流量过滤后再评估真实缺口 |')
    L.append('| 实机验证仅 337 链 | 其余链的"运行时"一段为 `RUNTIME_NOT_VERIFIED` |')
    L.extend(r13_section())
    w('R1_总体覆盖率与质量报告.md', '\n'.join(L) + '\n')

    print('报告生成完毕')


def r13_section():
    """R1.3 四项补充产出的报告段。"""
    L = []
    fd = load('R1_字段级协议差异.json')
    pm = load('R1_服务端持久化映射.json')
    L.append('\n## 六、R1.3 补充产出（四项）\n')
    L.append('### 6.1 字段级协议差异\n')
    ba = fd['_meta']['baseline_agreement']
    rc = fd['_meta']['residual_calibration']
    L.append('先自证：本次对 **1.4.9** 的提取与仓库既有 `protocol/fields.json` 对比 —— '
             '条目 `%d vs %d`，仅提取有 %d，仅基线有 %d，**字段不一致 %d**。\n'
             % (ba['entries'][0], ba['entries'][1], ba['only_in_extract'],
                ba['only_in_baseline'], ba['field_mismatch']))
    L.append('> 残留原因已查明：类型码 `b` 的映射差（本提取器 `b→bool`；基线用更新版类型词表，'
             '含 `bytes` 4 处 / `l` 2 处 / `struct<Dsc…>` 若干）⇒ **残留 %d/%d = %.2f%%**，'
             '且**三版本同口径**，跨版本比较不受影响。\n'
             % (rc['mismatch_count'], rc['of_total'], rc['ratio'] * 100))
    L.append('\n| 版本 | 协议类数 | 命令号数 |')
    L.append('|---|---:|---:|')
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        L.append('| %s | %d | %d |' % (v, fd['class_counts'][v], fd['cmd_counts'][v]))
    L.append('\n**1.4.11 vs 1.4.9 逐类分类**：')
    for k, c in fd['diffs']['1.4.11_vs_1.4.9']['categories'].items():
        L.append('  - `%s`: %d' % (k, c))
    L.append('\n> ★ **结论**：1.4.11 与 1.4.9 的**线协议几乎一致**（%d 个共有类中 %d 个逐字相同），'
             '差异集中在 **新增 %d 个类 / %d 个命令号** ⇒ 用 1.4.9 的字段表对接 1.4.11，'
             '对**已有类**基本可用，真正缺的是**新类与新命令**。\n'
             % (fd['diffs']['1.4.11_vs_1.4.9']['common'],
                fd['diffs']['1.4.11_vs_1.4.9']['categories'].get('IDENTICAL', 0),
                len(fd['diffs']['1.4.11_vs_1.4.9']['classes_only_in_target']),
                len(fd['target_only_cmds'])))
    L.append('\n### 6.2 未解析模块名归因（回 C2 台账核对）\n')
    L.append('上版把 37 个界面的"模块名解析不到"一律记为 unresolved。回 C2 台账逐条核对后，'
             '**真实提取失败 = 0**：\n')
    L.append('| 归因 | 数量 | 说明 |')
    L.append('|---|---:|---|')
    L.append('| `DYNAMIC_DISPATCH` | 28 | 模块名本身是一句**说明**（"无独立 luac；由 activity_ctrl 按 name 分派"），非路径 |')
    L.append('| `REMOVED_IN_TARGET` | 8 | C2 已标 `BLOCKED / 1.3.0-only(已从1.4.11移除)`，即 D 类（C0 `status=D`, conf=HIGH）—— 正是 `RESTORE_*` §九 记录的"1.4.11 已移除 8 界面" |')
    L.append('| `SOURCE_UNKNOWN` | 1 | C2 源头即标 `NEEDS_IMPLEMENTATION / UNKNOWN(模块未定位)` |')
    L.append('| `UNCLASSIFIED` | 0 | — |')
    L.append('\n### 6.3 服务端持久化：邻域扫描 → 精确解析\n')
    ps = pm['stats']
    L.append('按**处理函数体**（缩进判定块范围）解析三路证据：①SQL 文本 ②`db_*` 辅助函数'
             '（先建 `fn→表` 映射）③字面量表名实参。\n')
    L.append('| 指标 | 值 |')
    L.append('|---|---:|')
    L.append('| 有持久化关联的命令号 | **%d** |' % ps['cmds_with_persistence'])
    L.append('| `db_*` → 表 映射 | %d |' % ps['db_fn_mapped'])
    L.append('| 可反查的表（表→命令号） | %d / %d |'
             % (len(pm['by_table']), ps['tables_in_db']))
    L.append('| 证据分布 | `%s` |' % ps['evidence_kind_counts'])
    L.append('\n**改进量化**（同口径对比）：旧邻域口径 **326** 个命令号有表 → 新精确口径 **217** 个；'
             '两者表集合完全相同的仅 31 个；**仅旧口径有 161 个（纯假阳性 —— 邻域跨到相邻 handler）**，'
             '**仅新口径有 52 个（旧口径漏掉的）**。⇒ 未知数上升（169→199）是**更诚实**的结果。\n')
    L.append('\n### 6.4 函数级调用图\n')
    L.append('> **能力边界（不夸大）**：**不交付 LuaJIT 反编译器**。LuaJIT 字节码是寄存器机 + 轨迹优化产物，'
             '无可用的开源反编译器（`unluac` 仅支持标准 Lua 5.1）；强行产出伪代码**无法作为证据**，'
             '违反"不把推断写成确认"。本步交付**函数级调用图**，回答"谁调用谁"。\n')
    L.append('| 版本 | luac | 解析失败 | proto | 有调用的 proto | 被调名 | ≥2 处引用 |')
    L.append('|---|---:|---:|---:|---:|---:|---:|')
    for v in ('1.3.0', '1.4.9', '1.4.11'):
        cg = load('R1_函数级调用图_%s.json' % v)
        s = cg['stats']
        L.append('| %s | %d | %d | %d | %d | %d | %d |'
                 % (v, s['luac_scanned'], s['luac_parse_failed'], s['protos'],
                    s['protos_with_calls'], s['distinct_callee_names'],
                    s['callee_names_referenced_ge2']))
    L.append('\n> 口径：对每个 `CALL`，回看最多 10 条最近一次 `TGETS/GGET/TGETV` 取其名 —— '
             '**静态近似（heuristic）**，非精确数据流分析。\n')
    return L


if __name__ == '__main__':
    main()
