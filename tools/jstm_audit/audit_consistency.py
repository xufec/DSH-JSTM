#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE C0 — 最终交付物交叉核验审计器（只读，可重复运行）。

对 analysis/jstm_client_audit/ 下的最终交付物做交叉核验；部分交付物尚未生成时
优雅跳过并在报告中注明 SKIPPED。不修改任何既有文件，只写审计报告本身。

核验项:
  a) 每个顶层 .json 可被 json.load 解析；同名 .md 成对存在
  b) systems_master[].protocol_ids (CS_*/SC_*) 与 protocol_inventory 的 cmd 集合一致
  c) systems_master[].config_files basename 与三版本 raw config_tables 清单核对
  d) data_inventory[].config_files(按版本) 与该版本 raw config_tables 清单核对
  e) ui_inventory 的模块 / luac basename / 资源类名 与 raw 清单核对
  f) systems_master 的 present_in_* 与 presence_lib 独立复算结果一致
  g) client_server_matrix 的 system 集合与 systems_master 对齐

用法:
    python tools/jstm_audit/audit_consistency.py                 # 报告写到 _raw/consistency_report.txt
    python tools/jstm_audit/audit_consistency.py --out <路径>    # 报告另存他处
"""
import argparse
import io
import json
import os
import re
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import presence_lib as pl  # noqa: E402

ROOT = pl.ROOT
AUDIT_DIR = os.path.join(ROOT, "analysis", "jstm_client_audit")
DEFAULT_OUT = os.path.join(AUDIT_DIR, "_raw", "consistency_report.txt")

# 顶层交付物（相对 AUDIT_DIR），缺失即 SKIPPED
DELIVERABLES = {
    "systems_master": "systems_master.json",
    "protocol_inventory": "protocol_inventory.json",
    "data_inventory": "data_inventory.json",
    "ui_inventory": "ui_inventory.json",
    "client_server_matrix": "client_server_matrix.json",
}

PID_TOKEN_RE = re.compile(r"^((?:CS|SC)_\d+)")
# 从可能带注释的字符串里抽取真正的 luac basename，如
# "glz_main_ui.luac  (1.3.0 only)" -> "glz_main_ui.luac"
LUA_NAME_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.luac)")


def extract_lua_basename(tok):
    """从 token 中抽取 luac basename；明显是注释/占位串时返回 None（跳过核对）。"""
    s = str(tok).strip()
    if not s:
        return None
    m = LUA_NAME_RE.search(s)
    if not m:
        return None
    base = os.path.basename(m.group(1).replace("\\", "/"))
    # 抽取结果与原串差异过大（原串含说明文字）时仍核对 basename 本体
    return base


def _load_json(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class Report(object):
    def __init__(self):
        self.lines = []

    def w(self, line=""):
        self.lines.append(line)

    def section(self, title):
        self.w("")
        self.w("=" * 78)
        self.w(title)
        self.w("-" * 78)

    def dump(self):
        return "\n".join(self.lines) + "\n"


# ---------------------------------------------------------------- checks

def check_a_pairing(rep):
    """a) 顶层 json 可解析 + 与 md 成对。"""
    rep.section("a) JSON 可解析性 / json-md 成对")
    top_jsons = sorted(f for f in os.listdir(AUDIT_DIR)
                       if f.endswith(".json") and os.path.isfile(os.path.join(AUDIT_DIR, f)))
    parsed = {}
    for jf in top_jsons:
        jp = os.path.join(AUDIT_DIR, jf)
        mp = jp[:-5] + ".md"
        try:
            parsed[jf] = _load_json(jp)
            tag = "OK(json parsed)"
        except Exception as e:
            tag = "FAIL(parse error: %s)" % e
        md_tag = "md-present" if os.path.exists(mp) else "md-MISSING"
        rep.w("  %-32s %-26s %s" % (jf, tag, md_tag))
    # 反向：md 无 json 配对（信息性）
    for md in sorted(f for f in os.listdir(AUDIT_DIR) if f.endswith(".md")):
        if not os.path.exists(os.path.join(AUDIT_DIR, md[:-3] + ".json")):
            rep.w("  info: %-32s 无同名 json（纯 md 交付物，不算错误）" % md)
    return parsed


def load_deliverable(parsed, key, rep, title):
    fname = DELIVERABLES[key]
    if fname in parsed:
        return parsed[fname]
    p = os.path.join(AUDIT_DIR, fname)
    if not os.path.exists(p):
        rep.w("  SKIPPED: %s 缺失 (%s)" % (title, p))
        return None
    try:
        return _load_json(p)
    except Exception as e:
        rep.w("  SKIPPED: %s 解析失败: %s" % (title, e))
        return None


def check_b_protocols(rep, sm, pi):
    rep.section("b) systems_master.protocol_ids 与 protocol_inventory.cmd 一致性")
    if sm is None or pi is None:
        rep.w("  SKIPPED（见上）")
        return
    inv = set()
    for p in pi.get("protocols", []):
        cmd = str(p.get("cmd", "")).strip()
        if not cmd:
            continue
        # direction 可能形如 "cs (inferred from systems_master token prefix)"，
        # 先取空格/括号前的词干再判定
        raw_dir = str(p.get("direction", "")).strip().lower()
        d = raw_dir.split()[0] if raw_dir else ""
        if d in ("cs", "bidirectional"):
            inv.add("CS_" + cmd)
        if d in ("sc", "bidirectional"):
            inv.add("SC_" + cmd)
    used = {}
    for sy in sm.get("systems", []):
        for raw_pid in sy.get("protocol_ids") or []:
            m = PID_TOKEN_RE.match(str(raw_pid).strip())
            if m:
                used.setdefault(m.group(1), []).append(sy.get("system_id"))
    missing = sorted(set(used) - inv)
    rep.w("  systems_master 引用协议 token 数: %d；protocol_inventory 收录 token 数: %d"
          % (len(used), len(inv)))
    if missing:
        rep.w("  !! systems_master 引用但 protocol_inventory 缺失的协议 (%d):" % len(missing))
        for t in missing:
            rep.w("     - %-12s (被 %s 等引用)" % (t, ",".join(used[t][:3])))
    else:
        rep.w("  PASS: systems_master 引用的全部协议 token 均在 protocol_inventory 中")


def check_c_configs(rep, sm):
    rep.section("c) systems_master.config_files 与 raw config_tables 核对")
    if sm is None:
        rep.w("  SKIPPED")
        return
    union = set()
    for v in pl.VERSIONS:
        try:
            union |= pl.config_set(v)
        except Exception as e:
            rep.w("  SKIPPED: raw scan 读取失败: %s" % e)
            return
    claimed = {}
    for sy in sm.get("systems", []):
        for c in sy.get("config_files") or []:
            claimed.setdefault(os.path.basename(str(c)), []).append(sy.get("system_id"))
    absent = sorted(set(claimed) - union)
    luac_absent = [x for x in absent if x.endswith(".luac")]
    other_absent = [x for x in absent if not x.endswith(".luac")]
    rep.w("  systems_master 声明 config basename 数: %d；raw 三版本 config_tables 并集: %d"
          % (len(claimed), len(union)))
    rep.w("  !! 声明但不在任何版本 config_tables 的 .luac (%d):" % len(luac_absent))
    for x in luac_absent:
        rep.w("     - %-40s (声明自 %s)" % (x, ",".join(claimed[x][:3])))
    if other_absent:
        rep.w("  info: 声明的非 .luac basename（raw config_tables 只枚举 config_*.luac，"
              "以下项需另行核对 assets/，不算硬冲突）(%d):" % len(other_absent))
        for x in sorted(other_absent)[:30]:
            rep.w("     - %s" % x)
        if len(other_absent) > 30:
            rep.w("     ... 共 %d 项" % len(other_absent))
    if not luac_absent:
        rep.w("  PASS: 全部 .luac 配置表声明均在 raw config_tables 并集中")


def check_d_data_configs(rep, di):
    rep.section("d) data_inventory.config_files 与对应版本 raw config_tables 核对")
    if di is None:
        rep.w("  SKIPPED")
        return
    bad = []
    total = 0
    for rec in di.get("records", []):
        cf = rec.get("config_files") or {}
        if not isinstance(cf, dict):
            continue
        for ver_key, files in cf.items():
            ver = ver_key.replace("_", ".")
            try:
                have = pl.config_set(ver)
            except Exception as e:
                rep.w("  SKIPPED: raw scan 读取失败 (%s): %s" % (ver, e))
                return
            for f in files or []:
                total += 1
                if f not in have:
                    bad.append((rec.get("data_id"), ver, f))
    rep.w("  核对条目总数: %d" % total)
    if bad:
        rep.w("  !! data_inventory 声明但该版本 raw config_tables 缺失 (%d):" % len(bad))
        for did, ver, f in bad[:60]:
            rep.w("     - [%s] %s 缺 %s" % (ver, did, f))
        if len(bad) > 60:
            rep.w("     ... 共 %d 项" % len(bad))
    else:
        rep.w("  PASS: 全部 data_inventory 配置声明均可在对应版本 raw config_tables 中找到")


def check_e_ui(rep, ui):
    rep.section("e) ui_inventory 模块/资源 basename 与 raw 清单核对")
    if ui is None:
        rep.w("  SKIPPED")
        return
    meta = ui.get("_meta") or {}
    target = str(meta.get("target_version") or "1.4.11")
    try:
        luacs = pl.luac_set(target)
        uikeys = pl.ui_module_keys(target)
        gamemods = pl.game_module_set(target)
        rescats = pl.res_category_set(target)
    except Exception as e:
        rep.w("  SKIPPED: raw scan 读取失败: %s" % e)
        return
    rep.w("  目标版本: %s" % target)
    bad_mod, bad_lua, bad_res = [], [], []
    for e in ui.get("entries", []):
        name = e.get("ui_name") or "?"
        mod = e.get("module")
        if mod and mod not in uikeys and mod not in gamemods:
            bad_mod.append((name, mod))
        ce = extract_lua_basename(e.get("client_entry_luac"))
        if ce and ce not in luacs:
            bad_lua.append((name, ce))
        for m in e.get("related_lua_modules") or []:
            mb = extract_lua_basename(m)
            if mb and mb not in luacs:
                bad_lua.append((name, mb))
        for c in e.get("related_res_categories") or []:
            if c not in rescats:
                bad_res.append((name, c))
    bad_lua = sorted(set(bad_lua))  # client_entry 与 related 可能重复，去重
    rep.w("  entries=%d  raw luac=%d ui_mods=%d res_cats=%d"
          % (len(ui.get("entries", [])), len(luacs), len(uikeys), len(rescats)))
    for title, items in (("模块不存在", bad_mod), ("luac basename 不存在", bad_lua),
                         ("资源类名不存在", bad_res)):
        if items:
            rep.w("  !! %s (%d):" % (title, len(items)))
            for nm, x in items[:40]:
                rep.w("     - [%s] %s" % (nm, x))
            if len(items) > 40:
                rep.w("     ... 共 %d 项" % len(items))
        else:
            rep.w("  PASS: %s 全部命中 raw 清单" % title)


def check_f_present(rep, sm):
    rep.section("f) systems_master.present_in_* 与 presence_lib 独立复算核对")
    if sm is None:
        rep.w("  SKIPPED")
        return
    conflicts = []
    for sy in sm.get("systems", []):
        cands_lua = set()
        for x in (sy.get("lua_modules") or []):
            cands_lua.add(os.path.basename(str(x)))
        if sy.get("client_entry"):
            cands_lua.add(os.path.basename(str(sy["client_entry"])))
        cands_cfg = set(os.path.basename(str(c)) for c in (sy.get("config_files") or []))
        has_candidates = bool(cands_lua or cands_cfg)
        for v in pl.VERSIONS:
            key = "present_in_" + v.replace(".", "_")
            stored = str(sy.get(key, "")).strip()
            try:
                hit_lua = bool(cands_lua & pl.luac_set(v))
                hit_cfg = bool(cands_cfg & pl.config_set(v))
            except Exception as e:
                rep.w("  SKIPPED: raw scan 读取失败: %s" % e)
                return
            if not has_candidates:
                recomputed = "UNKNOWN"
            elif hit_lua or hit_cfg:
                recomputed = "true"
            else:
                recomputed = "false"
            if stored and stored.lower() != recomputed:
                conflicts.append((sy.get("system_id"), v, stored.lower(), recomputed))
    rep.w("  复算口径: 候选=lua_modules+client_entry 的 basename ∪ config_files basename；"
          "命中 luac_basenames/config_tables 记 true，有候选零命中记 false，无候选记 UNKNOWN")
    rep.w("  注: gen_systems_master 的 present_in_rule 还允许 protocol-chunk 等额外证据，"
          "下列冲突需人工复核（多数为仅含 .json 配置/通配符名目的系统）")
    if conflicts:
        rep.w("  !! present_in_* 与复算冲突 (%d):" % len(conflicts))
        for sid, v, stored, recomputed in conflicts[:60]:
            rep.w("     - %s [%s] stored=%s recomputed=%s" % (sid, v, stored, recomputed))
        if len(conflicts) > 60:
            rep.w("     ... 共 %d 项" % len(conflicts))
    else:
        rep.w("  PASS: 全部 present_in_* 与 presence_lib 复算一致")


def check_g_matrix(rep, sm, cm):
    rep.section("g) client_server_matrix.system 集合与 systems_master 对齐")
    if sm is None or cm is None:
        rep.w("  SKIPPED")
        return
    a = set(s.get("system_id") for s in sm.get("systems", []))
    b = set(s.get("system_id") for s in cm.get("systems", []))
    only_sm, only_cm = sorted(a - b), sorted(b - a)
    rep.w("  systems_master=%d  matrix=%d" % (len(a), len(b)))
    if only_sm:
        rep.w("  !! 仅在 systems_master 中 (%d): %s" % (len(only_sm), ", ".join(only_sm)))
    if only_cm:
        rep.w("  !! 仅在 client_server_matrix 中 (%d): %s" % (len(only_cm), ", ".join(only_cm)))
    if not only_sm and not only_cm:
        rep.w("  PASS: system 集合完全对齐")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="报告输出路径（默认 analysis/jstm_client_audit/_raw/consistency_report.txt）")
    args = ap.parse_args()

    rep = Report()
    rep.w("JSTM PHASE C0 一致性审计报告")
    rep.w("生成时间: %s" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    rep.w("只读审计：未修改任何既有文件。数据源: analysis/jstm_client_audit/_raw/apk_scan_*.json")

    parsed = check_a_pairing(rep)
    sm = load_deliverable(parsed, "systems_master", rep, "systems_master")
    pi = load_deliverable(parsed, "protocol_inventory", rep, "protocol_inventory")
    di = load_deliverable(parsed, "data_inventory", rep, "data_inventory")
    ui = load_deliverable(parsed, "ui_inventory", rep, "ui_inventory")
    cm = load_deliverable(parsed, "client_server_matrix", rep, "client_server_matrix")

    check_b_protocols(rep, sm, pi)
    check_c_configs(rep, sm)
    check_d_data_configs(rep, di)
    check_e_ui(rep, ui)
    check_f_present(rep, sm)
    check_g_matrix(rep, sm, cm)

    out = os.path.abspath(args.out)
    if not os.path.exists(os.path.dirname(out)):
        os.makedirs(os.path.dirname(out))
    with io.open(out, "w", encoding="utf-8") as f:
        f.write(rep.dump())
    print(rep.dump())
    print("-> report written: %s" % out)


if __name__ == "__main__":
    main()
