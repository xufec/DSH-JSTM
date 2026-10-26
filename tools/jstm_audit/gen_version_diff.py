# -*- coding: utf-8 -*-
"""
gen_version_diff.py — PHASE C0 三版本差异矩阵生成器（只读审计）

读取：
  1. analysis/version_compare/version_diff_matrix.json   （24 系统骨架，只读，不修改）
  2. analysis/jstm_client_audit/_raw/apk_scan_summary.json（三版本 APK zip 中央目录扫描，CONFIRMED）
  3. analysis/jstm_client_audit/_raw/apk_scan_{1_3_0,1_4_9,1_4_11}.json（逐版明细）
  4. server/item_config.json / mission_config.json / mall_config.json / partner_config.json
     （1.4.11 数值标准；本脚本实测计数）

输出（新建，不覆盖任何既有文件）：
  - analysis/jstm_client_audit/version_diff_matrix.json
  - analysis/jstm_client_audit/version_diff_matrix.md

纪律：
  * 不修改 analysis/version_compare/ 下任何文件；
  * 无证据的单元格保持 UNKNOWN；
  * 1.3.0 / 1.4.9 的 item/mission/mall/partner 逐条计数无证据 => UNKNOWN；
  * 版本差异必须落在证据文件上（每条单元格 notes 注明证据路径）。
"""
import json
import os
import io

ROOT = r"C:\Users\xu\Desktop\DSH"
SRC_MATRIX = os.path.join(ROOT, r"analysis\version_compare\version_diff_matrix.json")
RAW = os.path.join(ROOT, r"analysis\jstm_client_audit\_raw")
OUT_DIR = os.path.join(ROOT, r"analysis\jstm_client_audit")
SERVER = os.path.join(ROOT, "server")

VER_FILES = {
    "1.3.0": "apk_scan_1_3_0.json",
    "1.4.9": "apk_scan_1_4_9.json",
    "1.4.11": "apk_scan_1_4_11.json",
}
VKEY = {"1.3.0": "v130", "1.4.9": "v149", "1.4.11": "v1411"}


def load(p):
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def mb(n):
    return "%.1fMB" % (n / 1048576.0)


def main():
    skeleton = load(SRC_MATRIX)
    summary = load(os.path.join(RAW, "apk_scan_summary.json"))
    scans = {v: load(os.path.join(RAW, fn)) for v, fn in VER_FILES.items()}

    # ---- 扫描指标（直接读扫描 json，CONFIRMED）----
    m = {}
    for v, sc in scans.items():
        m[v] = {
            "apk_bytes": sc["apk_bytes"],
            "entries": sc["entries"],
            "assets_bytes": sc["assets_bytes"],
            "lua_total": sc["lua_total"],
            "game_modules": len(sc["game_modules"]),
            "config_tables": len(sc["config_tables"]),
            "cmd_resolve_files": len(sc["cmd_resolve"]),
            "ui_files": len(sc["ui_files"]),
            "ui_by_module": len(sc["ui_by_module"]),
            "res_categories": len(sc["res_categories"]),
            "now_version": next((p["value"] for p in sc["version_probe"]
                                 if p["key"] == "NOW_VERSION"), "UNKNOWN"),
        }

    # ---- 1.4.11 server 配置实测计数（VERIFIED，本脚本实测）----
    def top_len(name):
        return len(load(os.path.join(SERVER, name)))

    srv = {
        "item": top_len("item_config.json"),      # 3535
        "mission": top_len("mission_config.json"),  # 846
        "mall": top_len("mall_config.json"),      # 142
        "partner": top_len("partner_config.json"),  # 53
    }

    # ---- 复制既有 24 系统骨架，并按新证据更新 notes（值列不动，只补计数）----
    systems = []
    for row in skeleton["systems"]:
        r = dict(row)
        systems.append(r)

    def upd(name, notes=None, evidence=None):
        for r in systems:
            if r["system"] == name:
                if notes is not None:
                    r["notes"] = notes
                if evidence is not None:
                    r["evidence"] = evidence
                return r
        raise KeyError(name)

    upd("Lua模块", notes=(
        "三版均含完整 luac 模块族（1557 / 2234 / 2297 个，直接读 zip 中央目录，CONFIRMED）。"
        "game 模块目录数按新扫描口径：%d / %d / %d（CONFIRMED，apk_scan_*.json 的 game_modules 列表长度）；"
        "旧 inventory 的 92/116/119 为早期分文件提取口径，已被本口径取代。"
        "1.4.11 新增模块含大量 _ctrl/_panel/_view UI 模块；1.4.9 UI corpus 仅部分反编译（提取层面覆盖度，非 UI 不存在）。"
        % (m["1.3.0"]["game_modules"], m["1.4.9"]["game_modules"], m["1.4.11"]["game_modules"])))

    upd("cmd_resolve", notes=(
        "计数 %d / %d / %d（CONFIRMED，apk_scan_*.json 的 cmd_resolve 列表长度）。"
        "1.4.11 vs 1.3.0 新增 %d 个（cmd_resolve_187..191 等段；apk_scan_summary.json diff）；1.3.0 无独有 cmd_resolve。"
        "1.4.11 另有 server_cmds.json / protocalrulesmgr.luac（version_compare/1.4.11/inventory.md）。"
        % (m["1.3.0"]["cmd_resolve_files"], m["1.4.9"]["cmd_resolve_files"], m["1.4.11"]["cmd_resolve_files"],
           m["1.4.11"]["cmd_resolve_files"] - m["1.3.0"]["cmd_resolve_files"])))

    upd("config", notes=(
        "config_*.luac 计数 %d / %d / %d（CONFIRMED，apk_scan_*.json 的 config_tables 列表长度）。"
        "1.4.11 vs 1.3.0 独有表：auction/black_market/chair/chat_bubble/fashion/foot_print/holiday_*/mine/partner_fetter/score/shenqi 等；"
        "1.3.0 独有表仅 config_holiday.luac（1.4.11 拆为 config_holiday_* 系列=重命名/拆分）。"
        % (m["1.3.0"]["config_tables"], m["1.4.9"]["config_tables"], m["1.4.11"]["config_tables"])))

    upd("item", notes=(
        "三版均含 config_item.luac 及 fuse/gift/misc/type_name 族（存在性 CONFIRMED，apk_scan config_tables 清单）。"
        "1.4.11 条数=%d（VERIFIED，本脚本实测 server/item_config.json 顶层键数；HANDOFF 指明 server/ 服务 1.4.11 主目标）。"
        "1.3.0 / 1.4.9 逐条条数=UNKNOWN（仅存在性证据，禁止按 ID 连续性推测）。"
        "注：旧矩阵曾把 3535 记为 1.4.9，经 HANDOFF 归属判定纠正为 1.4.11。" % srv["item"]))

    upd("task", notes=(
        "三版均含 config_mission.luac + buffy/escort/help/kill_demon/loop/marry/treasure 族（存在性 CONFIRMED）。"
        "1.4.11 条数=%d（VERIFIED，server/mission_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。" % srv["mission"]))

    upd("partner", notes=(
        "1.3.0 含 hero 模块 + config_partner_base/misc/skill.luac；1.4.11 新增 fetter/score/shenqi（共6表，存在性 CONFIRMED）。"
        "1.4.11 条数=%d（VERIFIED，server/partner_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。" % srv["partner"]))

    upd("shop", notes=(
        "三版均含 config_mall.luac/config_shop.luac/config_market.luac（存在性 CONFIRMED）。"
        "1.4.11 mall 条数=%d（VERIFIED，server/mall_config.json 实测）。1.3.0 / 1.4.9 条数=UNKNOWN。" % srv["mall"]))

    upd("UI", notes=(
        "UI 文件计数 %d / %d / %d（CONFIRMED，apk_scan_*.json 的 ui_files 列表长度）；"
        "UI 覆盖模块数 ui_by_module=%d / %d / %d。"
        "1.3.0 独有 UI 文件：dungeon/gaolaozhuang/glz_main_ui、friend/friend_view 等；"
        "1.4.9 UI corpus 仅部分反编译（提取层面覆盖度，非 UI 不存在）。"
        % (m["1.3.0"]["ui_files"], m["1.4.9"]["ui_files"], m["1.4.11"]["ui_files"],
           m["1.3.0"]["ui_by_module"], m["1.4.9"]["ui_by_module"], m["1.4.11"]["ui_by_module"])))

    upd("resources", notes=(
        "assets 未压缩字节 %s / %s / %s（CONFIRMED，apk_scan_summary.json versions.*.assets_bytes，直接读 zip）；"
        "APK 压缩包体积 %s / %s / %s。单资产文件清单未逐一枚举=UNKNOWN。"
        % (mb(m["1.3.0"]["assets_bytes"]), mb(m["1.4.9"]["assets_bytes"]), mb(m["1.4.11"]["assets_bytes"]),
           mb(m["1.3.0"]["apk_bytes"]), mb(m["1.4.9"]["apk_bytes"]), mb(m["1.4.11"]["apk_bytes"]))))

    upd("assets", notes=(
        "总条目 %d / %d / %d（CONFIRMED，apk_scan_summary.json versions.*.entries，直接读 zip 中央目录）。"
        "单个资产文件清单未逐一枚举。" % (m["1.3.0"]["entries"], m["1.4.9"]["entries"], m["1.4.11"]["entries"])))

    upd("system entry", notes=(
        "config_function.luac 入口三版均为 91（id-count，VERIFIED）；game 模块数 %d / %d / %d（CONFIRMED）。存在性 CONFIRMED。"
        % (m["1.3.0"]["game_modules"], m["1.4.9"]["game_modules"], m["1.4.11"]["game_modules"])))

    # ---- 新增扫描指标维度 ----
    def row(name, key, unit_fmt, evidence, note_tmpl):
        return {
            "dimension": name,
            "kind": "scan_metric",
            "v130": unit_fmt(m["1.3.0"][key]),
            "v149": unit_fmt(m["1.4.9"][key]),
            "v1411": unit_fmt(m["1.4.11"][key]),
            "delta_1411_vs_130": "%+d" % (m["1.4.11"][key] - m["1.3.0"][key]),
            "evidence": evidence,
            "notes": note_tmpl,
        }

    metrics = [
        row("APK 体积", "apk_bytes", mb, "CONFIRMED",
            "zip 文件字节数；证据 apk_scan_summary.json versions.*.apk_bytes。"),
        row("APK 条目总数", "entries", lambda n: str(n), "CONFIRMED",
            "zip 中央目录条目数；证据 apk_scan_*.json。"),
        row("assets 字节数(未压缩)", "assets_bytes", mb, "CONFIRMED",
            "assets/ 条目未压缩字节合计；证据 apk_scan_summary.json。"),
        row("luac 文件总数", "lua_total", lambda n: str(n), "CONFIRMED",
            "assets/src/**.luac 计数；证据 apk_scan_*.json。"),
        row("game 模块目录数", "game_modules", lambda n: str(n), "CONFIRMED",
            "assets/src/game/ 下模块目录数（新扫描口径，取代旧 inventory 92/116/119 提取口径）；证据 apk_scan_*.json game_modules。"),
        row("config 表数(config_*.luac)", "config_tables", lambda n: str(n), "CONFIRMED",
            "证据 apk_scan_*.json config_tables 列表。"),
        row("cmd_resolve 文件数", "cmd_resolve_files", lambda n: str(n), "CONFIRMED",
            "证据 apk_scan_*.json cmd_resolve 列表。"),
        row("UI 文件数", "ui_files", lambda n: str(n), "CONFIRMED",
            "证据 apk_scan_*.json ui_files 列表。"),
        row("UI 覆盖模块数(ui_by_module)", "ui_by_module", lambda n: str(n), "CONFIRMED",
            "证据 apk_scan_*.json ui_by_module 字典键数。"),
        row("res 资源分类数", "res_categories", lambda n: str(n), "CONFIRMED",
            "证据 apk_scan_*.json res_categories 字典键数。"),
        {
            "dimension": "版本自证(NOW_VERSION)",
            "kind": "scan_metric",
            "v130": m["1.3.0"]["now_version"],
            "v149": m["1.4.9"]["now_version"],
            "v1411": m["1.4.11"]["now_version"],
            "delta_1411_vs_130": "%+d" % (int(m["1.4.11"]["now_version"]) - int(m["1.3.0"]["now_version"])),
            "evidence": "CONFIRMED",
            "notes": "读 assets/src/config.luac 明文 NOW_VERSION（apk_scan_*.json version_probe）。"
                     "'1.3.0' 是工程代号 INFERENCE（实际版本串 1.0.100/35，ewan 渠道）。",
        },
        {
            "dimension": "item 配置条数",
            "kind": "row_count",
            "v130": "UNKNOWN",
            "v149": "UNKNOWN",
            "v1411": str(srv["item"]),
            "delta_1411_vs_130": "N/A",
            "evidence": "VERIFIED",
            "notes": "1.4.11=server/item_config.json 顶层键数（本脚本实测）；1.3.0/1.4.9 仅 config 表存在性证据，条数 UNKNOWN。",
        },
        {
            "dimension": "mission 配置条数",
            "kind": "row_count",
            "v130": "UNKNOWN",
            "v149": "UNKNOWN",
            "v1411": str(srv["mission"]),
            "delta_1411_vs_130": "N/A",
            "evidence": "VERIFIED",
            "notes": "1.4.11=server/mission_config.json 顶层键数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。",
        },
        {
            "dimension": "mall 配置条数",
            "kind": "row_count",
            "v130": "UNKNOWN",
            "v149": "UNKNOWN",
            "v1411": str(srv["mall"]),
            "delta_1411_vs_130": "N/A",
            "evidence": "VERIFIED",
            "notes": "1.4.11=server/mall_config.json 顶层条数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。",
        },
        {
            "dimension": "partner 配置条数",
            "kind": "row_count",
            "v130": "UNKNOWN",
            "v149": "UNKNOWN",
            "v1411": str(srv["partner"]),
            "delta_1411_vs_130": "N/A",
            "evidence": "VERIFIED",
            "notes": "1.4.11=server/partner_config.json 顶层条数（本脚本实测）；1.3.0/1.4.9 条数 UNKNOWN。",
        },
    ]

    # 旧 caveat 中两条已被 C0 证据取代：剔除以免与新结论自相矛盾
    dropped_caveats = []
    kept_caveats = []
    for c in skeleton["caveats"]:
        if c.startswith("1.4.11 的 item/task/partner/mall 逐条计数未提取"):
            dropped_caveats.append(c)
        else:
            kept_caveats.append(c)

    out = {
        "meta": {
            "phase": "PHASE C0 客户端审计",
            "generated_by": "tools/jstm_audit/gen_version_diff.py",
            "generated_at": "2026-10-15",
            "basis": [
                "analysis/version_compare/version_diff_matrix.json（24 系统骨架，只读未改）",
                "analysis/jstm_client_audit/_raw/apk_scan_summary.json",
                "analysis/jstm_client_audit/_raw/apk_scan_1_3_0.json / apk_scan_1_4_9.json / apk_scan_1_4_11.json",
                "server/item_config.json / mission_config.json / mall_config.json / partner_config.json",
                "HANDOFF.md（server/ 归属 1.4.11 主目标）",
            ],
            "versions": {v: {"apk": scans[v]["apk"], "now_version": m[v]["now_version"]} for v in m},
        },
        "systems": systems,
        "scan_metrics": metrics,
        "system_count": len(systems),
        "metric_count": len(metrics),
        "total_dimensions": len(systems) + len(metrics),
        "evidence_legend": skeleton["evidence_legend"],
        "caveats": kept_caveats + [
            "[C0 新增] game 模块数口径：旧 inventory/旧矩阵记 92/116/119（分文件提取口径），本矩阵采用 apk_scan zip 中央目录口径 85/108/111。",
            "[C0 纠正] item/mission/mall/partner 条数归属：旧矩阵记为 1.4.9 VERIFIED；按 HANDOFF.md（主兼容版本=1.4.11，server/ 服务该客户端）纠正为 1.4.11 VERIFIED（本脚本实测 server/*.json 计数）。1.3.0/1.4.9 条数无证据，保持 UNKNOWN，禁止按 ID 连续性推测。已剔除旧矩阵中「1.4.11 条数 UNKNOWN、1.4.9=3535」的过时 caveat。",
            "[C0] assets_bytes 为未压缩字节合计（MiB 口径）：135.1/241.3/276.2MB 与旧 inventory 数值一致；APK 压缩包体积 135.8/230.5/267.8MB 为本轮新增。",
        ],
    }

    # ---- 写 JSON ----
    jout = os.path.join(OUT_DIR, "version_diff_matrix.json")
    with io.open(jout, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---- 写 Markdown ----
    L = []
    L.append("# 《绝世唐门》三版本差异矩阵（PHASE C0 审计）\n")
    L.append("> 生成：tools/jstm_audit/gen_version_diff.py（2026-10-15，只读审计）。")
    L.append("> 骨架：analysis/version_compare/version_diff_matrix.json（未修改）；新证据：_raw/apk_scan_*.json（CONFIRMED）+ server/*.json 实测（VERIFIED）。\n")
    L.append("- 维度总数：**%d**（系统维度 %d + 扫描指标维度 %d）" % (out["total_dimensions"], out["system_count"], out["metric_count"]))
    L.append("- 版本自证：1.3.0 NOW_VERSION=%s（工程代号 INFERENCE）；1.4.9 NOW_VERSION=%s；1.4.11 NOW_VERSION=%s（均读 config.luac 明文，CONFIRMED）。\n"
             % (m["1.3.0"]["now_version"], m["1.4.9"]["now_version"], m["1.4.11"]["now_version"]))
    L.append("## 一、系统维度（24，沿用既有骨架，已补新扫描证据）\n")
    L.append("| 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 差异 | 证据等级 | 说明 |")
    L.append("|---|---|---|---|---|---|---|")
    for r in systems:
        L.append("| {system} | {v130} | {v149} | {v1411} | {change} | {evidence} | {notes} |".format(**r))
    L.append("\n## 二、新增扫描指标维度（zip 中央目录直读，CONFIRMED）\n")
    L.append("| 指标 | 1.3.0 | 1.4.9 | 1.4.11 | 1.4.11 vs 1.3.0 | 证据等级 | 说明 |")
    L.append("|---|---|---|---|---|---|---|")
    for r in metrics:
        L.append("| {dimension} | {v130} | {v149} | {v1411} | {delta_1411_vs_130} | {evidence} | {notes} |".format(**r))
    L.append("\n## 三、证据等级定义\n")
    for k, v in out["evidence_legend"].items():
        L.append("- **%s**：%s" % (k, v))
    L.append("\n## 四、注意事项\n")
    for c in out["caveats"]:
        L.append("- %s" % c)
    mout = os.path.join(OUT_DIR, "version_diff_matrix.md")
    with io.open(mout, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")

    # ---- 自检打印 ----
    unknown_cells = []
    for r in systems:
        for k in ("v130", "v149", "v1411"):
            if "UNKNOWN" in str(r[k]):
                unknown_cells.append((r["system"], k, r[k]))
    for r in metrics:
        for k in ("v130", "v149", "v1411"):
            if "UNKNOWN" in str(r[k]):
                unknown_cells.append((r["dimension"], k, r[k]))
    print("WROTE", jout)
    print("WROTE", mout)
    print("total_dimensions =", out["total_dimensions"])
    print("server counts:", srv)
    print("scan metrics:", json.dumps(m, ensure_ascii=False))
    print("UNKNOWN cells (%d):" % len(unknown_cells))
    for c in unknown_cells:
        print("  -", c)


if __name__ == "__main__":
    main()
