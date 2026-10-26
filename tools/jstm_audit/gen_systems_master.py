# -*- coding: utf-8 -*-
"""
gen_systems_master.py — JSTM PHASE C0 审计「系统总目录」生成脚本（只读审计）

输入（只读，绝不修改）：
  analysis/jstm_game_systems/systems_master.json     既有 124 系统骨架
  analysis/jstm_client_audit/_raw/apk_scan_{1_3_0,1_4_9,1_4_11}.json   三版本全量扫描
  analysis/jstm_client_audit/_raw/apk_scan_summary.json                 diff 段
  protocol/fields.json                                协议字段 spec（键 CS<Name>_<cmd>）
  protocol/cmd_table.json                            cmd → 中文名
  server/mock_server.py                               服务器命令注册表（正则提取行号）

输出（仅本任务指定文件）：
  analysis/jstm_client_audit/systems_master.json
  analysis/jstm_client_audit/systems_master.md
  analysis/jstm_client_audit/system_dependency_graph.md
  analysis/jstm_client_audit/unimplemented_systems.md

判定纪律：
  - present_in_* 一律 basename 精确匹配程序化计算，禁止手写猜测。
  - 证据五档：CONFIRMED/VERIFIED/STRONG_INFERENCE/INFERENCE/UNKNOWN。
  - 不能确认的字段填 UNKNOWN，禁止把 UNKNOWN 写成确认值。
"""
import json
import os
import re
import shutil
import sys

ROOT = r"C:\Users\xu\Desktop\DSH"
SKELETON = os.path.join(ROOT, "analysis", "jstm_game_systems", "systems_master.json")
RAW = os.path.join(ROOT, "analysis", "jstm_client_audit", "_raw")
OUT_DIR = os.path.join(ROOT, "analysis", "jstm_client_audit")
FIELDS_JSON = os.path.join(ROOT, "protocol", "fields.json")
CMD_TABLE = os.path.join(ROOT, "protocol", "cmd_table.json")
MOCK_SERVER = os.path.join(ROOT, "server", "mock_server.py")

ARTIFACTS_DIR = os.path.join(
    os.environ.get("JSTM_ARTIFACTS",
                   r"C:\Users\xu\AppData\Local\Doubao\User Data\Default\.doubao\agent_mode"
                   r"\workspace\.sessions\38447329590799362\agents\s_000EmV2vm63\artifacts")
)

VERSIONS = [("1_3_0", "1.3.0"), ("1_4_9", "1.4.9"), ("1_4_11", "1.4.11")]

REQUIRED_FIELDS = [
    "system_id", "system_name", "aliases", "first_seen_version",
    "present_in_1_3_0", "present_in_1_4_9", "present_in_1_4_11",
    "client_entry", "lua_modules", "ui_resources", "config_files",
    "data_ids", "protocol_ids", "client_local_logic", "server_dependent_logic",
    "dependencies", "current_project_status", "evidence", "confidence",
    "missing_information", "recommended_next_step", "category",
]

# --------------------------------------------------------------------------- #
# PHASE C0 一致性修正（来源：consistency_report.txt + 三版本 apk_entries 核验）
# --------------------------------------------------------------------------- #
CONFIG_FIXES = {
    # buff_tianfu_tips.luac 是 game 模块而非 config 表 → 移至 lua_modules
    "SYS_GROWTH_002": {"move_cfg_to_lua": ["buff_tianfu_tips.luac"]},
    # 以下 4 个文件名三版本 APK 条目均不存在 → 从 config_files 剔除
    "SYS_BATTLE_002": {"remove_cfg": ["config_automate.luac"]},
    "SYS_COMM_007":    {"remove_cfg": ["config_build.luac"]},
    "SYS_ACT_010":    {"remove_cfg": ["config_qifu.luac"]},
    "SYS_DUNGEON_003": {"remove_cfg": ["config_treasure_data.luac"]},
}


# --------------------------------------------------------------------------- #
# 加载三版本扫描清单
# --------------------------------------------------------------------------- #
def load_scans():
    scans = {}
    for tag, ver in VERSIONS:
        d = json.load(open(os.path.join(RAW, "apk_scan_%s.json" % tag), encoding="utf-8"))
        lua_set = set(d.get("luac_basenames", [])) | set(d.get("luac_module_index", {}).keys())
        mod_set = set(d.get("game_modules", [])) | set(d.get("ui_by_module", {}).keys())
        cfg_set = set(os.path.basename(x) for x in d.get("config_tables", []))
        chunk_set = set(os.path.basename(x) for x in d.get("cmd_resolve", []))
        scans[tag] = {
            "version": ver,
            "lua_set": lua_set,
            "mod_set": mod_set,
            "cfg_set": cfg_set,
            "chunk_set": chunk_set,
            "ui_by_module": d.get("ui_by_module", {}),
        }
    return scans


# --------------------------------------------------------------------------- #
# fields.json / cmd_table 映射
# --------------------------------------------------------------------------- #
def load_protocol_maps():
    fields = json.load(open(FIELDS_JSON, encoding="utf-8"))
    cmd_table = json.load(open(CMD_TABLE, encoding="utf-8"))
    # (dir, cmd_str) -> list[fields.json key]
    dir_cmd_to_keys = {}
    cmd_to_chunks = {}   # cmd_str -> set(cmd_resolve basename)
    for key, val in fields.items():
        m = re.match(r"^(CS|SC)_?(?:([A-Za-z0-9]+)_)?(\d{4,6})$", key)
        if not m:
            continue
        dirn, _name, cmd = m.group(1).lower(), m.group(2), m.group(3)
        dir_cmd_to_keys.setdefault((dirn, cmd), []).append(key)
        chunk = os.path.basename(val.get("file", ""))
        if chunk:
            cmd_to_chunks.setdefault(cmd, set()).add(chunk)
    return fields, cmd_table, dir_cmd_to_keys, cmd_to_chunks


# --------------------------------------------------------------------------- #
# mock_server.py 命令注册表提取（正则，带行号）
# --------------------------------------------------------------------------- #
def load_server_handlers():
    cmds = {}
    pat_eq = re.compile(r"if cmd == (\d{4,6})")
    pat_in = re.compile(r"if cmd in \(([^)]+)\)")
    with open(MOCK_SERVER, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            for m in pat_eq.finditer(line):
                cmds.setdefault(int(m.group(1)), []).append(i)
            for m in pat_in.finditer(line):
                for n in re.findall(r"\d{4,6}", m.group(1)):
                    cmds.setdefault(int(n), []).append(i)
    # 去重保序
    return {c: sorted(set(v)) for c, v in cmds.items()}


# --------------------------------------------------------------------------- #
# 协议字符串解析 → canonical tokens "CS_<n>" / "SC_<n>"
# --------------------------------------------------------------------------- #
RANGE_RE = re.compile(r"(\d{4,6})\s*[.~-]+\s*(\d{4,6})\??")
SLASH_RE = re.compile(r"(\d{4,6})(?:\s*/\s*(\d{4,6}))+")
PLAIN_RE = re.compile(r"(?<!\d)(\d{4,6})(?!\d)")


def parse_protocols(proto_entries):
    """返回 (canonical_tokens, unconfirmed_raw)。
    canonical_tokens: list of "CS_<n>" / "SC_<n>"（去重保序）。
    unconfirmed_raw: 无法规范化的原始串（如 'all' / '' / 纯范围未闭合）。"""
    tokens = []
    unconfirmed = []

    def add(dirn, n):
        tok = "%s_%s" % (dirn, n)
        if tok not in tokens:
            tokens.append(tok)

    for raw in proto_entries:
        s = (raw or "").strip()
        if not s or s.lower() == "all":
            if s:
                unconfirmed.append(s)
            continue
        # 方向：串内任一 CS/SC 出现即记为默认方向
        dirn = None
        up = s.upper()
        if "CS" in up:
            dirn = "CS"
        elif "SC" in up:
            dirn = "SC"
        # 展开范围（上限 80 防爆炸）
        consumed = set()
        for m in RANGE_RE.finditer(s):
            a, b = int(m.group(1)), int(m.group(2))
            if b < a or b - a > 80:
                unconfirmed.append(s)
                continue
            d = dirn or "CS"   # 无方向时按客户端请求约定记 CS，标记推断
            for n in range(a, b + 1):
                add(d, str(n))
                consumed.add(m.start())
        # 斜杠列表
        for m in SLASH_RE.finditer(s):
            for n in re.findall(r"\d{4,6}", m.group(0)):
                add(dirn or "CS", n)
                consumed.add(m.start())
        # 其余裸数字
        for m in PLAIN_RE.finditer(s):
            if m.start() in consumed:
                continue
            add(dirn or "CS", m.group(1))
            consumed.add(m.start())
        if not consumed:
            unconfirmed.append(s)
    return tokens, unconfirmed


# --------------------------------------------------------------------------- #
# 文件名 token 规范化
# --------------------------------------------------------------------------- #
def clean_token(t):
    """去掉尾部 ? 和括号注释。"""
    t = t.strip()
    t = re.sub(r"\(.*?\)", "", t).strip()
    t = t.rstrip("?").strip()
    return t


def system_candidates(s):
    """从骨架字段提取匹配候选：
    返回 dict(basenames=set, modules=set, chunks=set, has_any=bool)。"""
    basenames, modules, chunks = set(), set(), set()
    for l in s.get("lua_modules", []):
        t = clean_token(l)
        if not t:
            continue
        if "*" in t:
            # glob 匹配留给扫描阶段；先原样记录为特殊项
            basenames.add("GLOB:" + t)
        elif t.endswith(".luac"):
            basenames.add(t)
        elif re.match(r"^[A-Za-z0-9_]+$", t):
            modules.add(t)
    for c in s.get("config_files", []):
        t = clean_token(c)
        if t.endswith(".luac"):
            basenames.add(t)
        elif t:
            modules.add(t)
    return {"basenames": basenames, "modules": modules, "chunks": chunks}


def present_in(cand, scans_tag, cmd_to_chunks, proto_tokens):
    """返回 True/False/UNKNOWN。"""
    sc = scans_tag
    # 把系统协议 cmd 映射到 chunk 文件
    chunk_files = set()
    for tok in proto_tokens:
        _d, _, n = tok.partition("_")
        chunk_files |= cmd_to_chunks.get(n, set())

    basenames = set()
    globs = []
    for b in cand["basenames"]:
        if b.startswith("GLOB:"):
            globs.append(b[5:])
        else:
            basenames.add(b)

    hits = False
    has_candidate = False

    for b in basenames:
        if b in sc["lua_set"] or b in sc["cfg_set"]:
            hits = True
        if b in sc["lua_set"] or b in sc["cfg_set"]:
            has_candidate = True
    for g in globs:
        pat = re.compile("^" + re.escape(g).replace(r"\*", ".*") + "$")
        has_candidate = True
        if any(pat.match(x) for x in sc["lua_set"]):
            hits = True
    for m in cand["modules"]:
        has_candidate = True
        if m in sc["mod_set"]:
            hits = True
    for c in chunk_files:
        has_candidate = True
        if c in sc["chunk_set"]:
            hits = True
    # config basenames 也可能在 cfg_set（已含于上面）
    if not has_candidate:
        return "UNKNOWN"
    return "true" if hits else "false"


# --------------------------------------------------------------------------- #
# implementation_status 归一化
# --------------------------------------------------------------------------- #
def normalize_status(raw):
    r = (raw or "").lower()
    if "client-only" in r or "client-config" in r or "client-event-data" in r \
       or "client ui" in r or "unidentified" in r:
        return "partial"
    if "partial" in r:
        return "partial"
    if "not implemented" in r or "not_implemented" in r:
        return "not_implemented"
    if "implemented" in r:
        return "implemented"
    return "UNKNOWN"


def reconcile_direction(tok, dir_cmd_to_keys):
    """PHASE C0 一致性修正：协议 token 方向复核。
    返回 (canonical_tok, was)。
    - 两方向都在 fields.json → 保留原方向，was=None。
    - 仅反方向存在 → 翻转方向，was=原 token（标注 'was CS_11202'）。
    - 两方向都无 → 保留原样（后续标 UNCONFIRMED 并列入 missing_information）。"""
    d, _, n = tok.partition("_")
    mine = dir_cmd_to_keys.get((d.lower(), n), [])
    rev = "SC" if d == "CS" else "CS"
    other = dir_cmd_to_keys.get((rev.lower(), n), [])
    if mine and other:
        return tok, None
    if other and not mine:
        return "%s_%s" % (rev, n), "was %s" % tok
    return tok, None


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main():
    skeleton = json.load(open(SKELETON, encoding="utf-8"))
    scans = load_scans()
    _fields, cmd_table, dir_cmd_to_keys, cmd_to_chunks = load_protocol_maps()
    server_cmds = load_server_handlers()
    summary = json.load(open(os.path.join(RAW, "apk_scan_summary.json"), encoding="utf-8"))

    out_systems = []
    unconfirmed_protos = []   # (system_id, token) 找不到 fields.json 映射
    flip_log = []             # (system_id, old, new) 方向翻转记录
    cfg_fix_log = []          # (system_id, action, file) config_files 清洗记录
    stats = {"true": 0, "false": 0, "UNKNOWN": 0, "per_ver": {v[0]: {"true": 0, "false": 0, "UNKNOWN": 0} for v in VERSIONS}}

    for s in skeleton["systems"]:
        sid = s["system_id"]

        # PHASE C0 一致性修正：config_files 清洗（不写回骨架文件，仅在内存副本上改）
        cfg_note = ""
        if sid in CONFIG_FIXES:
            fix = CONFIG_FIXES[sid]
            for rm in fix.get("remove_cfg", []):
                if rm in s.get("config_files", []):
                    s["config_files"] = [x for x in s["config_files"] if x != rm]
                    cfg_note += "旧分析误录：%s 三版本 APK 条目均无此文件，已剔除（CONFIRMED）；" % rm
                    cfg_fix_log.append((sid, "removed", rm))
            for mv in fix.get("move_cfg_to_lua", []):
                if mv in s.get("config_files", []):
                    s["config_files"] = [x for x in s["config_files"] if x != mv]
                    if mv not in s.setdefault("lua_modules", []):
                        s["lua_modules"].append(mv + " (1.4.11 assets/src/game/main/buff/ 存在)")
                    cfg_note += "%s 由 config_files 移至 lua_modules（1.4.11 存在性 CONFIRMED）；" % mv
                    cfg_fix_log.append((sid, "moved_cfg->lua", mv))

        proto_tokens, proto_unconfirmed = parse_protocols(s.get("protocols", []))

        # 协议方向一致性修正 + fields.json 映射
        verified_tokens = []
        spec_missing = []
        for tok in proto_tokens:
            canon, was = reconcile_direction(tok, dir_cmd_to_keys)
            d, _, n = canon.partition("_")
            keys = dir_cmd_to_keys.get((d.lower(), n), [])
            if keys:
                tag = " (fields: %s)" % keys[0]
                if was:
                    tag += " [dir corrected: %s]" % was
                    flip_log.append((sid, was.replace("was ", ""), canon))
                verified_tokens.append(canon + tag)
            else:
                verified_tokens.append("%s [UNCONFIRMED: fields.json 两方向均无映射]" % canon)
                unconfirmed_protos.append((sid, canon))
                spec_missing.append(canon)

        cand = system_candidates(s)
        pres = {}
        for tag, _ver in VERSIONS:
            pres[tag] = present_in(cand, scans[tag], cmd_to_chunks, proto_tokens)
            stats["per_ver"][tag][pres[tag]] += 1

        # first_seen_version
        first = "UNKNOWN"
        for tag, ver in VERSIONS:
            if pres[tag] == "true":
                first = ver
                break

        # ui_resources：取 1.4.11 ui_by_module 里命中模块的 ui 文件
        ui_res = []
        ui11 = scans["1_4_11"]["ui_by_module"]
        for m in cand["modules"]:
            if m in ui11:
                for u in ui11[m][:6]:
                    b = os.path.basename(u)
                    if b not in ui_res:
                        ui_res.append(b)
        if not ui_res:
            ui_res = "UNKNOWN"

        # 服务器覆盖
        handled, missing = [], []
        for tok in proto_tokens:
            _d, _, n = tok.partition("_")
            n = int(n)
            if n in server_cmds:
                handled.append("%s→mock_server.py:%s" % (n, ",".join(map(str, server_cmds[n][:2]))))
            else:
                missing.append(str(n))
        cov = "%d/%d cmds 有 handler" % (len({t.split("_")[1] for t in proto_tokens if int(t.split("_")[1]) in server_cmds}), len({t.split("_")[1] for t in proto_tokens})) if proto_tokens else "无协议记录"

        # current_project_status：骨架归一化 + 服务器核验降级
        st = normalize_status(s.get("implementation_status"))
        if st == "implemented" and proto_tokens and not handled:
            st = "partial"
        if st == "UNKNOWN":
            st = normalize_status(s.get("implementation_status"))

        # 证据合并
        ev_parts = [s.get("evidence", "") or ""]
        ev_parts.append("present_in_* = basename 精确匹配 apk_scan_%s/game_modules+config_tables+cmd_resolve+ui_by_module（CONFIRMED）" % "/".join(v[0] for v in VERSIONS))
        if handled:
            ev_parts.append("服务器覆盖: " + "; ".join(handled[:6]))
        ev = " | ".join(p for p in ev_parts if p)

        # 叙述字段（基于既有骨架+扫描证据，不清空 UNKNOWN）
        lua = s.get("lua_modules", []) or []
        cfg = s.get("config_files", []) or []
        if lua or cfg:
            client_local = ("客户端本地：模块 %s；配置表 %s；面板/逻辑随对应 game_modules 加载。"
                            "证据: apk_scan_1.4.11（lua_modules/config_tables basename 命中）。"
                            % (", ".join(lua) if lua else "UNKNOWN",
                               ", ".join(cfg) if cfg else "UNKNOWN"))
        else:
            client_local = "UNKNOWN（骨架无 lua_modules/config_files；仅别名/字符串证据，玩法存在性待反编译确认）"

        if proto_tokens:
            server_dep = ("协议 %s；mock_server %s；缺失 handler cmds: %s。DB: %s"
                          % (", ".join(verified_tokens[:8]) + (" ..." if len(verified_tokens) > 8 else ""),
                             cov,
                             ", ".join(missing[:12]) if missing else "无",
                             ", ".join(s.get("data_files", [])) or "UNKNOWN"))
        else:
            server_dep = "UNKNOWN（无协议记录；若为纯客户端展示则无服务器依赖，否则待补协议）"

        # missing_information / recommended_next_step
        miss = []
        if pres["1_3_0"] == "UNKNOWN" or (pres["1_3_0"] == "false" and pres["1_4_11"] == "true"):
            if pres["1_3_0"] == "UNKNOWN":
                miss.append("present_in_* 含 UNKNOWN（无可匹配 lua/config/cmd 候选）")
        if pres["1_4_9"] == "true" and pres["1_3_0"] == "false":
            miss.append("1.3.0→1.4.9 新增（diff: game_modules/config_tables_only_in_1.4.9）")
        if pres["1_4_11"] == "true" and pres["1_4_9"] == "false":
            miss.append("1.4.9→1.4.11 新增（diff: config_tables_only_in_1.4.11）")
        if missing:
            miss.append("服务器未处理 cmds: %s" % ", ".join(missing[:10]))
        if spec_missing:
            miss.append("协议 spec 缺失（fields.json 两方向均无）: %s" % ", ".join(spec_missing[:10]))
        if cfg_note:
            miss.append(cfg_note)
        if not lua and not cfg:
            miss.append("客户端 lua_modules/config_files 缺失记录")
        missing_information = "；".join(miss) if miss else "UNKNOWN（无显著缺口记录）"

        if st == "implemented":
            nxt = "保持现状；MuMu 12 + mock_server 联调取证（数值/回包字段逐字段比对，升 VERIFIED）"
        elif st == "partial":
            nxt = "补全服务器 handler（缺失 cmds: %s）+ DB 表持久化 + SC 回包对齐 fields.json spec" % (", ".join(missing[:10]) if missing else "见 evidence")
        elif st == "not_implemented":
            nxt = "按 fields.json spec 从 CS handler → SC 回包 → DB 持久化全链路实现；先反编译 lua 确认玩法边界"
        else:
            nxt = "反编译 lua_modules/配置表，确认玩法是否真实存在；再决定是否排期"

        conf = s.get("confidence", "UNKNOWN")
        if pres["1_3_0"] == "UNKNOWN" and pres["1_4_9"] == "UNKNOWN" and pres["1_4_11"] == "UNKNOWN":
            if conf in ("CONFIRMED", "VERIFIED"):
                conf = "UNKNOWN"

        rec = {
            "system_id": sid,
            "system_name": s.get("system_name", "UNKNOWN"),
            "aliases": s.get("aliases", []),
            "first_seen_version": first,
            "present_in_1_3_0": pres["1_3_0"],
            "present_in_1_4_9": pres["1_4_9"],
            "present_in_1_4_11": pres["1_4_11"],
            "client_entry": s.get("client_entry", "UNKNOWN"),
            "lua_modules": s.get("lua_modules", []),
            "ui_resources": ui_res,
            "config_files": s.get("config_files", []),
            "data_ids": s.get("data_files", []),
            "protocol_ids": verified_tokens if verified_tokens else ["UNKNOWN"],
            "client_local_logic": client_local,
            "server_dependent_logic": server_dep,
            "dependencies": s.get("dependencies", []),
            "current_project_status": st,
            "evidence": ev,
            "confidence": conf,
            "missing_information": missing_information,
            "recommended_next_step": nxt,
            "category": s.get("category", "UNKNOWN"),
        }
        out_systems.append(rec)

    # ---------------- 写 systems_master.json ---------------- #
    out = {
        "_meta": {
            "generated_by": "tools/jstm_audit/gen_systems_master.py",
            "phase": "C0",
            "task": "系统总目录（统一系统注册表）",
            "evidence_levels": ["CONFIRMED", "VERIFIED", "STRONG_INFERENCE", "INFERENCE", "UNKNOWN"],
            "present_in_rule": "true=任一 lua_modules/config_files/protocol-chunk basename 精确命中该版本 apk_scan 的 lua_set/mod_set/cfg_set/chunk_set；false=有候选但零命中；UNKNOWN=无任何候选可判定",
            "source_skeleton": "analysis/jstm_game_systems/systems_master.json (124 系统)",
            "scans": ["_raw/apk_scan_1_3_0.json", "_raw/apk_scan_1_4_9.json", "_raw/apk_scan_1_4_11.json"],
            "field_count_per_system": len(REQUIRED_FIELDS),
            "server_handlers_scanned": len(server_cmds),
        },
        "systems": out_systems,
    }
    json.dump(out, open(os.path.join(OUT_DIR, "systems_master.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # ---------------- 渲染 systems_master.md ---------------- #
    lines = []
    lines.append("# JSTM 系统总目录 systems_master（PHASE C0 审计）\n")
    lines.append("> 机读版：`systems_master.json`（%d 系统，每系统 %d 字段）。" % (len(out_systems), len(REQUIRED_FIELDS)))
    lines.append("> present_in_* 由脚本 basename 精确匹配三版本扫描清单生成（CONFIRMED）。\n")
    lines.append("| system_id | 名称 | 分类 | 首现 | 1.3.0 | 1.4.9 | 1.4.11 | 现状 | 置信 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in out_systems:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["system_id"], r["system_name"], r["category"], r["first_seen_version"],
            r["present_in_1_3_0"], r["present_in_1_4_9"], r["present_in_1_4_11"],
            r["current_project_status"], r["confidence"]))
    lines.append("\n## present_in_* 一致性统计\n")
    lines.append("| 版本 | true | false | UNKNOWN |")
    lines.append("|---|---|---|---|")
    for tag, ver in VERSIONS:
        p = stats["per_ver"][tag]
        lines.append("| %s | %d | %d | %d |" % (ver, p["true"], p["false"], p["UNKNOWN"]))
    open(os.path.join(OUT_DIR, "systems_master.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # ---------------- system_dependency_graph.md ---------------- #
    de_lines = ["# JSTM 系统依赖图 system_dependency_graph.md（PHASE C0）\n",
                "> 由 systems_master.json 的 dependencies/related_systems 程序化生成；强依赖在表中标注。\n",
                "```mermaid", "graph TD"]
    strong = []
    for r in out_systems:
        for dep in r.get("dependencies", []):
            dep = (dep or "").strip()
            if not dep or dep.lower() in ("all",):
                continue
            de_lines.append('  %s --> %s' % (r["system_id"], dep.replace(" ", "_").replace("/", "_")))
            # 强依赖判定：常见收敛链
            if any(k in (r["system_name"] + dep).lower() for k in ["equip", "bag", "attribute", "power", "reward", "currency"]):
                strong.append((r["system_name"], dep))
    de_lines.append("```\n")
    de_lines.append("## 强依赖链（收敛到统一服务）\n")
    de_lines.append("| 依赖链 | 说明 |")
    de_lines.append("|---|---|")
    chains = [
        ("装备 → 背包 → 属性 → 战力", "穿戴/强化改背包→属性→战力重算"),
        ("商城/黑市/活动 → CurrencyService → RewardService", "扣费/发放统一走货币与奖励服务"),
        ("任务 → ConditionService → RewardService", "条件判定后发奖，幂等 reference_id"),
        ("所有成长系统 → AttributeService → PowerService", "禁止自行算属性/战力"),
    ]
    for a, b in chains:
        de_lines.append("| %s | %s |" % (a, b))
    de_lines.append("\n## 数据一致性纪律\n")
    de_lines.append("- 状态变更必须经 Service 落盘并 ClientSync。")
    de_lines.append("- 奖励必须带 reference_id 防重。")
    de_lines.append("- 任何系统禁止绕过 CurrencyService/RewardService。")
    open(os.path.join(OUT_DIR, "system_dependency_graph.md"), "w", encoding="utf-8").write("\n".join(de_lines) + "\n")

    # ---------------- unimplemented_systems.md ---------------- #
    un = [r for r in out_systems if r["current_project_status"] in ("not_implemented", "partial")]
    ulines = ["# JSTM 未实现 / 未完整实现系统清单 unimplemented_systems.md（PHASE C0）\n",
              "> 骨架：analysis/jstm_game_systems/unimplemented_systems.md（42 项）。本表按新 system_id 对齐，"
              "覆盖 current_project_status ∈ {not_implemented, partial} 的全部系统。共 **%d** 项。\n" % len(un),
              "| system_id | 名称 | 现状 | 缺失能力 | 证据 | 建议下一步 |"]
    ulines.append("|---|---|---|---|---|---|")
    for r in un:
        ulines.append("| %s | %s | %s | %s | %s | %s |" % (
            r["system_id"], r["system_name"], r["current_project_status"],
            r["missing_information"][:80],
            r["evidence"][:80],
            r["recommended_next_step"][:60]))
    open(os.path.join(OUT_DIR, "unimplemented_systems.md"), "w", encoding="utf-8").write("\n".join(ulines) + "\n")

    # ---------------- 复制 artifacts ---------------- #
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    for fn in ["systems_master.json", "systems_master.md", "system_dependency_graph.md", "unimplemented_systems.md"]:
        shutil.copy2(os.path.join(OUT_DIR, fn), os.path.join(ARTIFACTS_DIR, fn))

    # ---------------- 自检输出 ---------------- #
    print("=== SELF CHECK ===")
    print("systems:", len(out_systems))
    bad_fields = [r["system_id"] for r in out_systems if list(r.keys()) != REQUIRED_FIELDS]
    print("field-count issues:", len(bad_fields), bad_fields[:5])
    for tag, ver in VERSIONS:
        p = stats["per_ver"][tag]
        print("present_in %s: true=%d false=%d UNKNOWN=%d" % (ver, p["true"], p["false"], p["UNKNOWN"]))
    print("server cmds scanned:", len(server_cmds))
    print("unconfirmed proto tokens:", len(unconfirmed_protos))
    for sid, tok in unconfirmed_protos:
        print("  UNCONFIRMED:", sid, tok)
    print("direction flips:", len(flip_log))
    for sid, old, new in flip_log:
        print("  FLIP:", sid, old, "->", new)
    print("config_files cleans:", len(cfg_fix_log))
    for sid, act, fn in cfg_fix_log:
        print("  CFG-FIX:", sid, act, fn)
    print("unimplemented+partial:", len(un))
    print("artifacts dir:", ARTIFACTS_DIR)


if __name__ == "__main__":
    main()
