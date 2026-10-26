# -*- coding: utf-8 -*-
"""
PHASE C1 — 系统恢复总表生成脚本（只读审计 + 生成初稿）

输入（全部只读，禁止修改）:
  analysis/jstm_client_audit/systems_master.json        (124 系统)
  analysis/jstm_client_audit/client_server_matrix.json (124 系统)
  analysis/jstm_client_audit/ui_inventory.json          (391 界面)
  analysis/jstm_client_audit/protocol_inventory.json  (1707 协议, 流式聚合, 不整体入上下文)

输出:
  docs/C1_系统恢复总表.md

用法:
  python tools/jstm_audit/gen_c1_status_table.py
"""
import json, os, re, collections

ROOT = r"C:\Users\xu\Desktop\DSH"
AUDIT = os.path.join(ROOT, "analysis", "jstm_client_audit")
OUT = os.path.join(ROOT, "docs", "C1_系统恢复总表.md")

# ---- E 类（尚无可靠证据）名单: C0 unknown_inventory 证据级 UNKNOWN 的 9 个系统 ----
E_LIST = {
    "SYS_GROWTH_006",   # 魂骨
    "SYS_GROWTH_007",   # 增幅
    "SYS_CORE_008",     # 红点
    "SYS_CORE_009",     # UI 状态
    "SYS_UNKNOWN_001",  # 丹药战
    "SYS_UNKNOWN_002",  # 运营活动
    "SYS_UNKNOWN_004",  # 染色
    "SYS_EQUIP_005",    # 装备洗练
    "SYS_FRIEND_006",   # 伙伴培养消耗
}

def load(name):
    with open(os.path.join(AUDIT, name), encoding="utf-8") as f:
        return json.load(f)

def cell(text, limit=140):
    """压缩单元格文本: 去管道符/换行, 截断。"""
    if text is None:
        return "UNKNOWN"
    if isinstance(text, list):
        text = "; ".join(str(x) for x in text)
    text = str(text).replace("|", "/").replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "UNKNOWN"
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return text

def main():
    sm = load("systems_master.json")["systems"]
    cm = load("client_server_matrix.json")["systems"]
    ui = load("ui_inventory.json")["entries"]
    prot = load("protocol_inventory.json")["protocols"]  # 2.2MB, 仅本机聚合, 不打印

    sm_by_id = {s["system_id"]: s for s in sm}
    cm_by_id = {c["system_id"]: c for c in cm}

    # ---- 聚合: 每系统界面状态集合 ----
    ui_status = collections.defaultdict(set)
    ui_paths = collections.defaultdict(list)
    for e in ui:
        sid = e.get("system_id")
        if not sid:
            continue
        ui_status[sid].add(e.get("status"))
        p = e.get("client_entry_luac")
        if p and p not in ui_paths[sid]:
            ui_paths[sid].append(p)

    # ---- 聚合: 每系统协议编号 (CS/SC) ----
    proto_cs = collections.defaultdict(list)
    proto_sc = collections.defaultdict(list)
    for p in prot:
        sid = p.get("related_system")
        if not sid or sid == "UNKNOWN" or sid not in sm_by_id:
            continue
        cmd = p.get("cmd")
        if p.get("direction") == "cs":
            proto_cs[sid].append(str(cmd))
        elif p.get("direction") == "sc":
            proto_sc[sid].append(str(cmd))

    # ---- 读取 unimplemented_systems.md 用于对照 ----
    with open(os.path.join(AUDIT, "unimplemented_systems.md"), encoding="utf-8") as f:
        unimpl_text = f.read()
    unimpl_ids = set(re.findall(r"SYS_[A-Z]+_\d+", unimpl_text))

    # ---- A-F 程序化初判 ----
    rows = []
    stats = collections.Counter()
    boundary = []  # (sid, cls, reason, note)
    for s in sm:
        sid = s["system_id"]
        c = cm_by_id.get(sid, {})
        impl = c.get("impl_status", "UNKNOWN")      # 已实现/部分实现/未实现
        tier = c.get("evidence_tier", "UNKNOWN")     # VERIFIED/CONFIRMED/STRONG_INFERENCE/INFERENCE/UNKNOWN
        us = ui_status.get(sid, set())

        # 判定优先级: E > A > B > C > F > D
        # E 严格按 C0 evidence_tier=UNKNOWN 的 9 系统（sm.confidence 为客户端识别轴，不作为 E 触发）
        if sid in E_LIST or tier == "UNKNOWN":
            cls, reason = "E", "C0 evidence_tier=UNKNOWN（unknown_inventory 名单）"
        elif impl == "已实现" and tier == "VERIFIED":
            cls, reason = "A", "已实现+VERIFIED"
        elif impl == "已实现":
            cls, reason = "B", f"已实现但证据={tier}（待实机/回归升 VERIFIED）"
        elif us & {"A", "B"}:
            cls, reason = "C", f"界面 A/B 类齐备但工程 impl={impl}"
        elif "D" in us:
            cls, reason = "F", "界面 D 类（已废弃/被替换）"
        else:
            cls, reason = "D", "仅资源/配置/协议证据，无完整 UI 无实现"

        stats[cls] += 1
        # 边界清单: B 类待升级、C 类有 A 类界面（优先恢复）、含 D 类界面的非 F 系统
        if cls == "B":
            boundary.append((sid, s.get("system_name", ""), "B", reason, "回归/实机取证后升 A"))
        if cls == "C" and "A" in us:
            boundary.append((sid, s.get("system_name", ""), "C", reason, "存在实机验证界面, 恢复优先级最高"))
        if "D" in us and cls != "F":
            boundary.append((sid, s.get("system_name", ""), cls, "界面含 D(废弃) 类", "人工复核是否真废弃"))

        rows.append((sid, s, c, us, cls, reason, impl, tier))

    # D 类界面归属核查（ui_inventory 仅 8 条 D）
    d_sids = {e.get("system_id") for e in ui if e.get("status") == "D"}
    for dsid in sorted(d_sids):
        dcls = next((r[5] for r in rows if r[0] == dsid), "?")
        dname = sm_by_id.get(dsid, {}).get("system_name", "")
        boundary.append((dsid, dname, dcls, "D 类界面归属系统（已被更高优先级类别覆盖）", "确认废弃界面是否影响主系统判定"))

    # ---- 写 Markdown ----
    L = []
    A = L.append
    A("# PHASE C1 — 系统恢复总表")
    A("")
    A("> 主版本: **1.4.11**（1.4.9 / 1.3.0 仅用于版本差异验证）。")
    A("> 骨架: C0 `systems_master.json` 124 系统 × client_server_matrix × ui_inventory(391) × protocol_inventory(1707) 融合生成。")
    A("> 本文件为只读审计产物：生成脚本 `tools/jstm_audit/gen_c1_status_table.py` 可重复生成；未修改 C0 任何既有文件。")
    A("")
    A("## 一、实施规范总纲（C1 第五步）")
    A("")
    A("1. **先定位，再动手**：实现前先定位已有代码 / 资源 / 协议 / 数据；先明确需求与证据，再决定是否实现；优先复用现有客户端结构与资源，不重造。")
    A("2. **先证据后实现**：不能确认的状态标 UNKNOWN / STRONG_INFERENCE 并注明原因；禁止仅凭文件名、协议字段或图标认定功能已实现。")
    A("3. **服务端单一实现**：服务端统一使用 `server/mock_server.py`，不建第二套服务端实现。")
    A("4. **业务逻辑收口**：货币 / 奖励 / 背包 / 属性 / 战斗业务逻辑统一走 Service 层。")
    A("5. **禁止绕过校验**：禁止直改数据库绕过业务校验。")
    A("6. **禁止编造**：禁止编造原版协议 / 剧情 / 道具属性 / 数值；一切推断必须显式标记（STRONG_INFERENCE / INFERENCE）。")
    A("7. **改前评估影响面**：修改前检查调用链与影响范围，避免破坏已有登录 / 地图 / 角色 / 任务功能。")
    A("8. **完成标准**：每阶段必须有可重复测试步骤、实际日志与验收结果；不以\"代码已生成\"为完成标准。")
    A("")
    A("## 二、状态分类（A-F）判定规则")
    A("")
    A("| 类别 | 含义 | 程序化初判规则 |")
    A("|---|---|---|")
    A("| A | 已验证可用 | `impl_status=已实现` 且 `evidence_tier=VERIFIED`，或 HANDOFF/tests 回归证实闭环 |")
    A("| B | 已实现未完整验证 | `impl_status=已实现` 但 `evidence_tier≠VERIFIED`（有 mock_server 行号/模块，缺实机或回归验证） |")
    A("| C | 客户端有界面业务不完整 | ui_inventory 有 A/B 类界面（模块+资源齐备）但 matrix `impl_status=部分实现/未实现` |")
    A("| D | 只有资源配置或协议证据 | ui_inventory C 类（仅图标）或仅 data/protocol 证据，无实现、无完整 UI |")
    A("| E | 尚未发现可靠证据 | C0 unknown_inventory 名单 9 系统或 `evidence_tier=UNKNOWN` / present_in 全 UNKNOWN |")
    A("| F | 暂不恢复或等待依赖完成 | ui_inventory D 类（已废弃/被替换）、或依赖系统缺失、或明确优先级低 |")
    A("")
    A("判定优先级（自上而下，先命中先归类）：E → A → B → C → F → D。边界冲突时以证据为准，判定理由见第六节清单。")
    A("")
    A("## 三、分类统计")
    A("")
    A("| 类别 | 系统数 | 说明 |")
    A("|---|---|---|")
    A(f"| A | {stats['A']} | 已验证可用 |")
    A(f"| B | {stats['B']} | 已实现待验证 |")
    A(f"| C | {stats['C']} | 有界面业务不完整 |")
    A(f"| D | {stats['D']} | 仅资源/协议证据 |")
    A(f"| E | {stats['E']} | 无可靠证据 |")
    A(f"| F | {stats['F']} | 暂不恢复/待依赖 |")
    A(f"| **合计** | **{sum(stats.values())}** | 应为 124 |")
    A("")

    # ---- 主表 ----
    A("## 四、系统恢复总表（124 系统全覆盖）")
    A("")
    A("列: ①system_id ②系统名称 ③类别 ④客户端版本 ⑤客户端入口/Lua/界面资源/配置 ⑥数据表/资源ID+证据来源 ⑦协议编号(CS/SC) ⑧工程实际实现状态(current_impl) ⑨A-F分类 ⑩依赖基础系统 ⑪服务端Service ⑫数据库持久化 ⑬已知问题/未确认 ⑭验收方法 ⑮证据等级")
    A("")
    header = "| system_id | 系统名称 | 类别 | 客户端版本 | 客户端入口/Lua/界面资源/配置 | 数据表/资源ID+证据来源 | 协议编号(CS/SC) | 工程实际实现状态 | 分类 | 依赖基础系统 | 服务端Service | 数据库持久化 | 已知问题/未确认 | 验收方法 | 证据等级 |"
    sep = "|" + "---|" * 15
    A(header)
    A(sep)

    # 按 system_id 排序输出
    for sid, s, c, us, cls, reason, impl, tier in sorted(rows, key=lambda r: r[0]):
        ver = (f"起于{s.get('first_seen_version','?')} "
               f"[1.3.0={s.get('present_in_1_3_0','?')}/1.4.9={s.get('present_in_1_4_9','?')}/1.4.11={s.get('present_in_1_4_11','?')}]")
        entry = (f"入口:{cell(s.get('client_entry'),60)}<br>"
                 f"Lua:{cell(s.get('lua_modules'),80)}<br>"
                 f"配置:{cell(s.get('config_files'),60)}<br>"
                 f"界面资源:{cell(s.get('ui_resources'),60)}<br>"
                 f"界面路径:{cell(ui_paths.get(sid,[]),100)}")
        data = (f"数据:{cell(s.get('data_ids'),60)}<br>"
                f"服务端逻辑:{cell(s.get('server_dependent_logic'),90)}<br>"
                f"证据:{cell(s.get('evidence'),90)}")
        cs = proto_cs.get(sid, [])
        sc = proto_sc.get(sid, [])
        prot_cell = (f"CS({len(cs)}):{cell(cs[:10],70)}<br>"
                     f"SC({len(sc)}):{cell(sc[:10],70)}<br>"
                     f"登记:{cell(s.get('protocol_ids'),80)}")
        impl_cell = f"{impl}<br>{cell(c.get('current_impl'),150)}"
        deps = cell(s.get("dependencies"), 80)
        svc = cell(c.get("server_authoritative"), 110)
        persist = c.get("persisted_data") or "否"
        issues = cell(s.get("missing_information"), 90) + "<br>" + cell(c.get("remaining"), 90)
        accept = cell(s.get("recommended_next_step"), 120)
        name = cell(s.get("system_name"), 40)
        A("| " + " | ".join([
            sid, name, cell(s.get("category"), 20), ver, entry, data, prot_cell,
            impl_cell, f"{cls}<br><sub>{cell(reason,50)}</sub>", deps, svc,
            cell(persist, 80), issues, accept, tier,
        ]) + " |")

    A("")
    A("## 五、与 C0 client_server_matrix / unimplemented_systems.md 对照")
    A("")
    A(f"- matrix 口径: 已实现 60 / 部分实现 29 / 未实现 35（合计 124）；证据档: VERIFIED 70 / CONFIRMED 14 / STRONG_INFERENCE 14 / INFERENCE 17 / UNKNOWN 9。")
    A(f"- 本总表 A-F 映射: A={stats['A']}（已实现∩VERIFIED）；B={stats['B']}（已实现∩非VERIFIED）；C+D+F≈部分实现29+未实现35=64，再按界面/证据细分；E={stats['E']}（=evidence_tier UNKNOWN 9 个）。")
    A(f"- unimplemented_systems.md 称 67 项，正文正则提取到 {len(unimpl_ids)} 个唯一 system_id（含跨节引用）；与 matrix 未实现35/部分实现29 的差异原因: 该 md 按\"待恢复项\"粒度（一系统可能拆多条），matrix 按系统粒度，口径不同不冲突，恢复排期时以本总表 C/D/F 类为准。")
    A(f"- F={stats['F']} 的说明: ui_inventory 全部 8 条 D 类界面分别归属 SYS_UNKNOWN_002（已归 E）与 SYS_ACT_009（系统本身已实现，D 条目为 1.3.0 已移除子界面，按 B 类处理）；C0 未发现\"依赖链缺失导致整体冻结\"的系统，故 F 类为 0，如后续 dependency_graph 证实依赖阻断再人工改判。")
    A("")

    A("## 六、边界判定清单（程序化初判 + 人工复核点）")
    A("")
    A("| system_id | 名称 | 初判 | 判定依据 | 复核动作 |")
    A("|---|---|---|---|---|")
    seen = set()
    for sid, nm, cls, reason, note in boundary:
        key = (sid, cls)
        if key in seen:
            continue
        seen.add(key)
        A(f"| {sid} | {cell(nm,30)} | {cls} | {cell(reason,80)} | {cell(note,60)} |")
    A("")
    A("人工复核原则: B 类系统安排实机/回归取证后升 A；C 类中存在 A 类实机界面者优先恢复；E 类 9 系统需先补证据（定位 lua/协议/配置）再决定是否恢复；凡含 D 类界面的非 F 系统需人工确认界面是否真废弃。")
    A("")

    A("## 七、输入来源（只读引用）")
    A("")
    for p in [
        "analysis/jstm_client_audit/systems_master.json",
        "analysis/jstm_client_audit/client_server_matrix.json",
        "analysis/jstm_client_audit/ui_inventory.json",
        "analysis/jstm_client_audit/protocol_inventory.json",
        "analysis/jstm_client_audit/unimplemented_systems.md",
        "analysis/jstm_client_audit/server_capability_needs.md",
        "analysis/jstm_client_audit/unknown_inventory.md",
        "analysis/jstm_client_audit/system_dependency_graph.md",
        "analysis/jstm_client_audit/_raw/consistency_report.txt",
    ]:
        A(f"- `{p}`")
    A("")

    A("## 八、自检记录")
    A("")
    A(f"- 系统行数 = {sum(stats.values())}（要求 124）。")
    A(f"- 表头列数 = 15（要求至少 14）。")
    A(f"- A-F 分布: A={stats['A']} B={stats['B']} C={stats['C']} D={stats['D']} E={stats['E']} F={stats['F']}。")
    A("- 未修改 analysis/、server/、tools 下任何既有文件；仅新建本 md 与生成脚本。")
    A("- protocol_inventory.json 经脚本内聚合映射（CS/SC 计数与 cmd 列表），未读入对话上下文。")
    A("")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("written:", OUT)
    print("stats:", dict(stats), "total:", sum(stats.values()))

if __name__ == "__main__":
    main()
