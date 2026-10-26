# -*- coding: utf-8 -*-
"""
gen_protocol_inventory.py — PHASE C0 协议总目录生成器（只读审计）

输入（全部只读）：
  protocol/fields.json                 3553 条字段定义（键=CS|SC名_cmd）
  protocol/cmd_table.json              1643 条 cmd->中文名
  protocol/registry_classes.json       客户端协议注册表类名清单
  analysis/jstm_game_systems/systems_master.json   系统-协议映射
  analysis/jstm_client_audit/_raw/apk_scan_{1_3_0,1_4_9,1_4_11}.json  三版本 cmd_resolve 文件清单
  analysis/jstm_1.4.9/*_protocol.md   1.4.9 分系统协议文档
  analysis/extraction/{real_cs_formats_1_4_11,phase1_cs_inventory,dead_protocols_and_traffic}.md
  server/proto_defs.py                 服务端已生成的协议定义

输出（仅新建，不修改任何既有文件）：
  analysis/jstm_client_audit/protocol_inventory.json
  analysis/jstm_client_audit/protocol_inventory.md

用法：python tools/jstm_audit/gen_protocol_inventory.py
"""
import json, os, re, sys, collections, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(ROOT, "analysis", "jstm_client_audit")

# ---------------------------------------------------------------- 加载数据
def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

fields = load_json(os.path.join(ROOT, "protocol", "fields.json"))
cmd_table = load_json(os.path.join(ROOT, "protocol", "cmd_table.json"))
registry_classes = load_json(os.path.join(ROOT, "protocol", "registry_classes.json"))
systems_master = load_json(os.path.join(ROOT, "analysis", "jstm_game_systems", "systems_master.json"))

apk = {}
for ver, tag in [("1_3_0", "1.3.0"), ("1_4_9", "1.4.9"), ("1_4_11", "1.4.11")]:
    apk[tag] = set(load_json(os.path.join(
        ROOT, "analysis", "jstm_client_audit", "_raw", f"apk_scan_{ver}.json"))["cmd_resolve"])

# ---------------------------------------------------------------- 拆分 fields.json
# 顶层协议条目：cmd 为纯数字；嵌套描述符条目（Dsc*，cmd 为符号名，dir=None，source=reader/fmt）另记账
proto_entries = collections.defaultdict(list)   # cmd -> [entry]
nested_descriptors = []                          # 非顶层条目，仅统计
NESTED_PARENTS = collections.Counter()

for key, v in fields.items():
    cmd = str(v.get("cmd", ""))
    if cmd.isdigit():
        proto_entries[cmd].append((key, v))
    else:
        nested_descriptors.append((key, v))
        m = re.match(r"Dsc(\d+)", key)
        if m:
            NESTED_PARENTS[m.group(1)] += 1

# ---------------------------------------------------------------- 三版本存在性
def version_present(cmd, fam_files, runtime_observed_1411):
    """true / false / UNKNOWN。家族文件存在于该版本 apk 扫描即记 true；
    无家族文件则 UNKNOWN（不能凭空白推断不存在）。1.4.11 有运行时观测则强制 true。"""
    res = {}
    for tag in ("1.3.0", "1.4.9", "1.4.11"):
        if fam_files:
            res[tag] = any(f in apk[tag] for f in fam_files)
        else:
            res[tag] = "UNKNOWN"
    if cmd in runtime_observed_1411:
        res["1.4.11"] = True
    return res

# ---------------------------------------------------------------- systems_master 映射
cmd_to_system = {}
system_names = {}
for s in systems_master.get("systems", []):
    sid = s.get("system_id", "UNKNOWN")
    system_names[sid] = s.get("system_name", sid)
    for ref in s.get("protocols", []):
        m = re.search(r"(\d{3,5})", str(ref))
        if m:
            cmd_to_system.setdefault(m.group(1), sid)

# ---------------------------------------------------------------- registry_classes -> cmd 集合
registry_cmds = set()
for cls in registry_classes:
    m = re.search(r"_(\d{3,5})$", str(cls))
    if m:
        registry_cmds.add(m.group(1))

# ---------------------------------------------------------------- 1.4.9 文档解析
DOC_FILES = ["login_protocol.md", "role_protocol.md", "scene_protocol.md",
             "movement_protocol.md", "task_protocol.md", "battle_protocol.md",
             "equipment_protocol.md", "inventory_protocol.md", "partner_protocol.md",
             "skill_protocol.md", "dungeon_protocol.md", "chat_protocol.md",
             "gm_protocol.md", "social_protocol.md"]
doc_rows = {}   # cmd -> dict
for d in DOC_FILES:
    p = os.path.join(ROOT, "analysis", "jstm_1.4.9", d)
    if not os.path.exists(p):
        continue
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 6:
                continue
            c0 = cells[0]
            if not re.fullmatch(r"\d{3,5}", c0):
                continue
            doc_rows[c0] = {
                "doc": d,
                "doc_direction": cells[1],           # CS / SC / CS+SC
                "implemented": "✅" in cells[2],
                "observed_sent": bool(cells[3].strip()),
                "observed_recv": bool(cells[4].strip()),
                "doc_fields_text": cells[5],
            }

# protocol_index.md 的 CMD 段说明
seg_descs = []   # (lo, hi, desc)
pidx = os.path.join(ROOT, "analysis", "jstm_1.4.9", "protocol_index.md")
if os.path.exists(pidx):
    with open(pidx, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*\|\s*(\d{4})~(\d{4})\s*\|\s*\d+\s*\|\s*([^|]+)\|", line)
            if m:
                seg_descs.append((int(m.group(1)), int(m.group(2)), m.group(3).strip()))

def seg_desc_for(cmd):
    c = int(cmd)
    for lo, hi, d in seg_descs:
        if lo <= c <= hi:
            return d
    return None

# ---------------------------------------------------------------- 运行时取证
runtime_observed = set()   # 1.4.11 实机出现过的 CS cmd
p1 = os.path.join(ROOT, "analysis", "extraction", "phase1_cs_inventory.md")
if os.path.exists(p1):
    with open(p1, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*\|\s*\d+\s*\|\s*(\d{3,5})\s*\|", line)
            if m:
                runtime_observed.add(m.group(1))
for c, r in doc_rows.items():
    if r["observed_sent"] or r["observed_recv"]:
        runtime_observed.add(c)

# real_cs_formats：1.4.11 实测与 fields.json(1.4.9) 冲突的 cmd
REAL_CS_CONFLICT = {"10924", "10922", "10923", "16903", "11300", "11301",
                    "14009", "14000", "10527", "17200", "17800", "11200", "13321"}
REAL_CS_EMPTY_OK = {"10302", "14901", "13340"}   # 实测确为空 CS

# dead_protocols：死协议（客户端从不发送）
DEAD_CMDS = {"13324", "13326", "13328", "16300", "30503", "30506", "30507", "10305"}

# ---------------------------------------------------------------- proto_defs.py 已实现定义
server_defined = set()
pdf = os.path.join(ROOT, "server", "proto_defs.py")
if os.path.exists(pdf):
    with open(pdf, encoding="utf-8") as f:
        server_defined = set(re.findall(r'"cmd":\s*(\d+)', f.read()))

# ---------------------------------------------------------------- 组装记录
EVID_RANK = ["UNKNOWN", "INFERENCE", "STRONG_INFERENCE", "CONFIRMED", "VERIFIED"]
def best(*levels):
    return max(levels, key=lambda l: EVID_RANK.index(l))

all_cmds = set(cmd_table) | set(proto_entries)
records = []
for cmd in sorted(all_cmds, key=lambda x: (len(x), x)):
    entries = proto_entries.get(cmd, [])
    name = cmd_table.get(cmd, "UNKNOWN")

    # fields（仅取自 fields.json，带 dir 标签以便区分 cs/sc）
    fields_merged = []
    fam_files = set()
    entry_sources = set()
    notes = []
    for key, v in entries:
        fam_files.add(v.get("file", ""))
        if v.get("source"):
            entry_sources.add(v["source"])
        if v.get("note"):
            notes.append(v["note"])
        for fd in v.get("fields", []):
            fields_merged.append({"name": fd.get("name"), "type": fd.get("type"),
                                  "dir": v.get("dir") or "unknown"})

    dirs = {v.get("dir") for _, v in entries if v.get("dir")}
    if dirs == {"cs"}:
        direction = "cs"
    elif dirs == {"sc"}:
        direction = "sc"
    elif "cs" in dirs and "sc" in dirs:
        direction = "bidirectional"
    else:
        direction = "UNKNOWN"

    trigger = sorted(fam_files) if fam_files else []
    related_system = cmd_to_system.get(cmd, "UNKNOWN")

    versions = version_present(cmd, fam_files, runtime_observed)

    # source_file
    source_file = []
    if entries:
        source_file.append("protocol/fields.json")
        source_file.extend(trigger)
    if cmd in cmd_table:
        source_file.append("protocol/cmd_table.json")
    if cmd in registry_cmds:
        source_file.append("protocol/registry_classes.json")
    if cmd in doc_rows:
        source_file.append("analysis/jstm_1.4.9/" + doc_rows[cmd]["doc"])
    if cmd in runtime_observed:
        source_file.append("analysis/extraction/phase1_cs_inventory.md")
    if cmd in REAL_CS_CONFLICT:
        source_file.append("analysis/extraction/real_cs_formats_1_4_11.md")
    if cmd in DEAD_CMDS:
        source_file.append("analysis/extraction/dead_protocols_and_traffic.md")
    if cmd in server_defined:
        source_file.append("server/proto_defs.py")
    source_file = sorted(set(source_file))

    # current_understanding
    parts = []
    if name != "UNKNOWN":
        parts.append(f"cmd_table中文名:{name}[cmd_table.json]")
    if related_system != "UNKNOWN":
        parts.append(f"所属系统:{system_names.get(related_system, related_system)}[{related_system}][systems_master.json]")
    sd = seg_desc_for(cmd)
    if sd and not sd.startswith("【未知】") and not sd.startswith("?"):
        parts.append(f"段说明:{sd}[protocol_index.md]")
    if cmd in doc_rows:
        r = doc_rows[cmd]
        parts.append(f"1.4.9文档载于{r['doc']}")
    if cmd in DEAD_CMDS:
        parts.append("死协议：客户端从不发送[dead_protocols_and_traffic.md]")
    if cmd in REAL_CS_CONFLICT:
        parts.append("1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md]")
    if not parts:
        parts.append("UNKNOWN")
    current_understanding = "；".join(parts)

    # unresolved
    unresolved = []
    if not entries:
        unresolved.append("fields.json 无此 cmd 条目，字段未知（仅 cmd_table 有名）")
    else:
        n_cs = sum(1 for fd in fields_merged if fd["dir"] == "cs")
        n_sc = sum(1 for fd in fields_merged if fd["dir"] == "sc")
        if n_cs == 0 and direction in ("cs", "bidirectional"):
            unresolved.append("cs 方向无字段定义")
        if n_sc == 0 and direction in ("sc", "bidirectional"):
            unresolved.append("sc 方向无字段定义")
    if name == "UNKNOWN":
        unresolved.append("cmd_table 无中文名")
    if cmd in doc_rows:
        rd = doc_rows[cmd]["doc_direction"].replace("CS+SC", "bidirectional").replace("CS", "cs").replace("SC", "sc").lower()
        if rd != direction and not (direction == "UNKNOWN"):
            unresolved.append(f"方向冲突：1.4.9文档记 {doc_rows[cmd]['doc_direction']} vs fields.json 记 {direction}")
    if cmd in REAL_CS_CONFLICT:
        unresolved.append("1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid）")
    if "UNKNOWN" in (versions["1.3.0"], versions["1.4.9"]):
        unresolved.append("无家族 cmd_resolve 文件，该版本存在性无法判定(UNKNOWN)")
    if notes:
        unresolved.append("fields.json 注释:" + " / ".join(notes))
    if NESTED_PARENTS.get(cmd):
        unresolved.append(f"含 {NESTED_PARENTS[cmd]} 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields")

    # evidence_level
    lvl = "UNKNOWN"
    if entries and fields_merged:
        lvl = best(lvl, "CONFIRMED")
    elif entries:
        lvl = best(lvl, "STRONG_INFERENCE")
    if cmd in doc_rows:
        lvl = best(lvl, "STRONG_INFERENCE")
    if cmd in cmd_table:
        lvl = best(lvl, "INFERENCE")
    if cmd in registry_cmds:
        lvl = best(lvl, "CONFIRMED")
    if cmd in runtime_observed:
        lvl = best(lvl, "VERIFIED")

    records.append({
        "cmd": cmd,
        "name": name,
        "direction": direction,
        "fields": fields_merged,
        "trigger_module": trigger,
        "related_system": related_system,
        "versions": {
            "present_in_1_3_0": versions["1.3.0"],
            "present_in_1_4_9": versions["1.4.9"],
            "present_in_1_4_11": versions["1.4.11"],
        },
        "source_file": source_file,
        "current_understanding": current_understanding,
        "evidence_level": lvl,
        "unresolved": unresolved,
    })

# ---------------------------------------------------------------- systems_master 引用一致性补录（PHASE C0 修复轮）
# 权威输入：analysis/jstm_client_audit/_raw/consistency_report.txt 的缺失块
#   "- CS_12804     (被 SYS_ECON_003 等引用)"
# 处理：
#   - cmd 已在库：方向一致 -> 忽略；方向不一致 -> A类(库内记录已存在)，只记账不补录（systems_master 侧另行修复）
#   - cmd 不在库  -> B类真缺失：按 prior analysis 引用补录一条 INFERENCE 级记录
report_path = os.path.join(ROOT, "analysis", "jstm_client_audit", "_raw", "consistency_report.txt")
missing_tokens = []   # (cmd, dir, [system_ids])
if os.path.exists(report_path):
    with open(report_path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*-\s*(CS|SC)_(\d+)\s+\(.*?被\s+([A-Z_0-9,]+)", line)
            if m:
                missing_tokens.append((m.group(2), m.group(1).lower(),
                                       m.group(3).split(",")))

record_cmds = {r["cmd"]: r for r in records}
family_by_cmd = {}
for r in records:
    for f in r["trigger_module"]:
        family_by_cmd.setdefault(r["cmd"], f)

def infer_family(cmd):
    """按同 3 位前缀已有记录的家族推断；无则回退 cmd_resolve_<前缀>.luac。"""
    votes = [f for c, f in family_by_cmd.items() if c[:3] == cmd[:3]]
    if votes:
        return collections.Counter(votes).most_common(1)[0][0]
    return f"cmd_resolve_{cmd[:3]}.luac"

supplemented = []
a_mismatch = []
for cmd, tok_dir, ref_systems in missing_tokens:
    if cmd in record_cmds:
        rec = record_cmds[cmd]
        if rec["direction"] not in (tok_dir, "bidirectional"):
            a_mismatch.append({"cmd": cmd, "record_direction": rec["direction"],
                               "systems_master_token_dirs": [tok_dir],
                               "note": "库内记录已存在，仅方向标签不一致；不补录，待 systems_master 侧修复"})
        continue
    fam = infer_family(cmd)
    versions = {}
    for tag in ("1.3.0", "1.4.9", "1.4.11"):
        versions[tag] = True if fam in apk[tag] else "UNKNOWN"
    sys_names = [system_names.get(sid, sid) for sid in ref_systems]
    name = cmd_table.get(cmd, "UNKNOWN")
    parts = [f"prior analysis 引用[systems_master.json]：{tok_dir.upper()}_{cmd}",
             "引用系统: " + "; ".join(f"{n}[{s}]" for s, n in zip(ref_systems, sys_names))]
    if name != "UNKNOWN":
        parts.insert(0, f"cmd_table中文名:{name}[cmd_table.json]")
    unres = ["无 fields.json/cmd_table spec，需反汇编 " + fam + " 验证"]
    if not versions["1.4.11"]:
        unres.append(f"推断的家族文件 {fam} 未出现在任何版本 apk 扫描清单，家族归属待核")
    records.append({
        "cmd": cmd,
        "name": name,
        "direction": tok_dir + " (inferred from systems_master token prefix)",
        "fields": [],
        "trigger_module": [fam],
        "related_system": ref_systems[0],
        "versions": {
            "present_in_1_3_0": versions["1.3.0"],
            "present_in_1_4_9": versions["1.4.9"],
            "present_in_1_4_11": versions["1.4.11"],
        },
        "source_file": ["analysis/jstm_game_systems/systems_master.json (prior analysis reference)"],
        "current_understanding": "；".join(parts),
        "evidence_level": "INFERENCE",
        "unresolved": unres,
    })
    supplemented.append(cmd)

# ---------------------------------------------------------------- 统计
stat = collections.Counter()
for r in records:
    stat["total"] += 1
    stat["dir_" + r["direction"].split(" ")[0]] += 1
    stat["with_fields" if r["fields"] else "no_fields"] += 1
    stat["ev_" + r["evidence_level"]] += 1
    if r["related_system"] != "UNKNOWN":
        stat["mapped_system"] += 1
    if r["cmd"] in doc_rows:
        stat["doc_covered"] += 1
    if r["unresolved"]:
        stat["has_unresolved"] += 1
stat["supplemented_records"] = len(supplemented)
fam_counter = collections.Counter()
for r in records:
    for f in r["trigger_module"] or ["(no_family)"]:
        fam_counter[f] += 1

payload = {
    "_meta": {
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "tools/jstm_audit/gen_protocol_inventory.py",
        "audit_mode": "READ-ONLY — no existing project file was modified",
        "evidence_levels": ["UNKNOWN", "INFERENCE", "STRONG_INFERENCE", "CONFIRMED", "VERIFIED"],
        "evidence_rule": "VERIFIED=1.4.11实机观测; CONFIRMED=fields.json静态字段/客户端注册表; STRONG_INFERENCE=1.4.9文档载录; INFERENCE=cmd_table有名; UNKNOWN=均无",
        "direction_rule": "按 fields.json 同 cmd 的 dir 条目合并：仅cs/仅sc/cs+sc=bidirectional",
        "version_rule": "家族 cmd_resolve 文件存在于该版本apk扫描即 true；无家族文件=UNKNOWN；1.4.11有运行时观测强制 true",
        "fields_rule": "fields 仅取自 protocol/fields.json，未自行补造任何字段；嵌套子消息描述符(reader/fmt, cmd为符号名)已排除并在 unresolved 记账",
        "counts": {
            "fields_json_entries": len(fields),
            "fields_json_numeric_cmds": len(proto_entries),
            "nested_descriptor_entries_excluded": len(nested_descriptors),
            "cmd_table_entries": len(cmd_table),
            "inventory_records": len(records),
            "supplemented_from_systems_master": len(supplemented),
        },
        "supplement_note": "PHASE C0 修复轮：systems_master.protocols 引用但 fields.json/cmd_table 均无的 B 类真缺失 cmd，按 prior analysis 引用补录 INFERENCE 级记录（fields=[]，方向按 token 前缀推断）",
        "supplemented_cmds": supplemented,
        "systems_master_direction_mismatches": a_mismatch,
    },
    "stats": dict(stat),
    "family_counts": dict(fam_counter),
    "protocols": records,
}

os.makedirs(OUT_DIR, exist_ok=True)
json_out = os.path.join(OUT_DIR, "protocol_inventory.json")
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- 渲染 MD
def esc(s):
    return str(s).replace("|", "/").replace("\n", " ")

lines = []
A = lines.append
A("# 绝世唐门 PHASE C0 协议总目录（只读审计）\n")
A(f"- 生成时间：{payload['_meta']['generated']}")
A("- 生成脚本：`tools/jstm_audit/gen_protocol_inventory.py`（可重复运行）")
A("- 纪律：只读审计；字段仅取自 `protocol/fields.json`，未自行补造；证据不足一律标 UNKNOWN/unresolved。\n")

A("## 一、证据等级（五档）\n")
A("| 等级 | 含义 |")
A("|---|---|")
A("| VERIFIED | 1.4.11 实机观测到收发（phase1_cs_inventory / 文档真机列） |")
A("| CONFIRMED | fields.json 静态字段定义存在，或客户端注册表(registry_classes.json)有此类 |")
A("| STRONG_INFERENCE | 1.4.9 分系统文档载录该行，但无运行时证据 |")
A("| INFERENCE | cmd_table 有中文名；或 systems_master prior analysis 引用补录（无直接 spec） |")
A("| UNKNOWN | 以上皆无 |\n")

A("## 二、总览统计\n")
A("| 指标 | 数量 |")
A("|---|---|")
A(f"| 协议记录总数（唯一 cmd） | {stat['total']} |")
A(f"| 其中：cmd_table 覆盖 | {sum(1 for r in records if r['cmd'] in cmd_table)} / {len(cmd_table)} |")
A(f"| 方向 cs | {stat.get('dir_cs',0)} |")
A(f"| 方向 sc | {stat.get('dir_sc',0)} |")
A(f"| 方向 双向 | {stat.get('dir_bidirectional',0)} |")
A(f"| 方向 UNKNOWN | {stat.get('dir_UNKNOWN',0)} |")
A(f"| 有字段定义 | {stat.get('with_fields',0)} |")
A(f"| 无字段定义 | {stat.get('no_fields',0)} |")
A(f"| 映射到系统 | {stat.get('mapped_system',0)} |")
A(f"| 1.4.9 文档补充载录 | {stat.get('doc_covered',0)} |")
A(f"| 含未确认项 | {stat.get('has_unresolved',0)} |")
A(f"| 排除的嵌套子消息描述符条目 | {len(nested_descriptors)} |")
A(f"| 修复轮补录（systems_master prior analysis 引用） | {stat.get('supplemented_records',0)} |")
A("")
A("### 证据等级分布")
A("| 等级 | 数量 |")
A("|---|---|")
for lv in EVID_RANK:
    A(f"| {lv} | {stat.get('ev_'+lv,0)} |")
A("")

A("### 修复轮补录明细（INFERENCE 级，仅旧分析引用）\n")
if supplemented:
    A("| cmd | 方向(推断) | 家族 | 引用系统 |")
    A("|---|---|---|---|")
    sup_cmds = {r["cmd"]: r for r in records if r["cmd"] in set(supplemented)}
    for c in supplemented:
        r = sup_cmds[c]
        A(f"| {c} | {esc(r['direction'])} | {esc(r['trigger_module'][0])} | {esc(r['related_system'])} |")
    A("")
if a_mismatch:
    A("### A 类：库内记录已存在、仅 systems_master token 方向标签不一致（不补录，待 systems_master 侧修复）\n")
    A("| cmd | 库内方向 | systems_master token 方向 |")
    A("|---|---|---|")
    for m in a_mismatch:
        A(f"| {m['cmd']} | {m['record_direction']} | {','.join(m['systems_master_token_dirs'])} |")
    A("")

A("## 三、按 cmd_resolve 家族分组\n")
A(f"共 {len(fam_counter)} 个家族（含 {fam_counter.get('(no_family)',0)} 条无家族文件）。\n")
A("| 家族文件 | 协议数 |")
A("|---|---|")
for fam, n in sorted(fam_counter.items(), key=lambda x: (x[0] == "(no_family)", x[0])):
    A(f"| {fam} | {n} |")
A("")

A("## 四、协议明细（按家族分组）\n")
by_fam = collections.defaultdict(list)
for r in records:
    key = r["trigger_module"][0] if r["trigger_module"] else "(no_family)"
    by_fam[key].append(r)
for fam in sorted(by_fam.keys(), key=lambda x: (x == "(no_family)", x)):
    A(f"### {fam}（{len(by_fam[fam])} 条）\n")
    A("| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for r in by_fam[fam]:
        cs_f = [f"{fd['name']}:{fd['type']}" for fd in r["fields"] if fd["dir"] == "cs"]
        sc_f = [f"{fd['name']}:{fd['type']}" for fd in r["fields"] if fd["dir"] == "sc"]
        ftxt = ("cs: " + "; ".join(cs_f) if cs_f else "cs: —") + " ／ " + \
               ("sc: " + "; ".join(sc_f) if sc_f else "sc: —")
        v = r["versions"]
        vt = lambda x: "✓" if x is True else ("✗" if x is False else "?")
        A("| {cmd} | {name} | {dir} | {ftxt} | {sys} | {a} | {b} | {c} | {ev} | {und} |".format(
            cmd=r["cmd"], name=esc(r["name"]), dir=r["direction"], ftxt=esc(ftxt),
            sys=esc(r["related_system"]), a=vt(v["present_in_1_3_0"]),
            b=vt(v["present_in_1_4_9"]), c=vt(v["present_in_1_4_11"]),
            ev=r["evidence_level"], und=esc(r["current_understanding"])))
    A("")

A("## 五、未确认项清单（unresolved）\n")
A("| cmd | 名称 | 未确认内容 |")
A("|---|---|---|")
uc = [r for r in records if r["unresolved"]]
uc.sort(key=lambda r: (len(r["unresolved"]), r["cmd"]), reverse=True)
for r in uc:
    A(f"| {r['cmd']} | {esc(r['name'])} | {esc(' ；'.join(r['unresolved']))} |")
A("")
A(f"_共 {len(uc)} 条记录含未确认项。_")

md_out = os.path.join(OUT_DIR, "protocol_inventory.md")
with open(md_out, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# ---------------------------------------------------------------- 自检打印
print("== 生成完成 ==")
print("json:", json_out)
print("md  :", md_out)
print(json.dumps({"records": len(records), "stats": dict(stat),
                  "families": len(fam_counter),
                  "doc_covered": stat.get("doc_covered", 0),
                  "has_unresolved": stat.get("has_unresolved", 0)},
                 ensure_ascii=False, indent=2))
