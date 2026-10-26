#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE C0 — JSTM 三版本 APK 只读扫描器（可重复执行）。

用法:
    python tools/jstm_audit/scan_apk.py                # 全量扫描三包
    python tools/jstm_audit/scan_apk.py --only 1.4.11  # 单包
    python tools/jstm_audit/scan_apk.py --strings      # 额外做 luac 可打印字符串抽取

只读取 zip 中央目录 + 必要的小文件头，不解包、不修改 APK。
产物（全部落在 analysis/jstm_client_audit/_raw/）:
    apk_entries_<ver>.txt    每包完整 zip 条目清单（换行分隔，可 diff）
    apk_scan_<ver>.json      结构化分类结果
    apk_scan_summary.json    三包合并摘要 + 跨版本 diff
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "analysis", "jstm_client_audit", "_raw")

# 版本 -> 原版 APK。版本识别依据见 analysis/version_compare/*/inventory.md
APKS = collections.OrderedDict([
    ("1.3.0", os.path.join(ROOT, "anzbao", "dldlJl.apk")),
    ("1.4.9", os.path.join(ROOT, "anzbao", "jstm.apk")),
    ("1.4.11", os.path.join(ROOT, "anzbao", "jstm_142165.apk")),
])

# UI 相关 basename 后缀（客户端界面模块命名约定：*_ctrl / *_panel / *_view / *_data / *_vo）
UI_SUFFIXES = ("_ctrl.luac", "_panel.luac", "_view.luac",
               "_data.luac", "_vo.luac", "_mgr.luac", "_ui.luac")
# 配置表
CONFIG_RE = re.compile(r"^config_.*\.luac$")
# 协议解析类
CMDRES_RE = re.compile(r"^cmd_resolve_.*\.luac$")

TEXT_PROBE = (
    "NOW_VERSION", "VERSION", "BUILD_VERSION", "PLATFORM_NAME",
    "CHANNEL", "APPID", "APP_ID",
)


def classify(path):
    """把 zip 条目归到粗粒度桶。"""
    if path.startswith("assets/src/game/") or path.startswith("assets/src/"):
        return "assets/src"
    if path.startswith("assets/res/"):
        return "assets/res"
    if path.startswith("assets/"):
        return "assets/other"
    if path.startswith("lib/"):
        return "lib"
    if path.startswith("META-INF/"):
        return "META-INF"
    if path.startswith("res/"):
        return "res"
    return path.split("/")[0] if "/" in path else "(root)"


def src_module(path):
    """assets/src/game/<mod>/... -> 逻辑模块名；非 game 目录返回 None。"""
    parts = path.split("/")
    if path.startswith("assets/src/game/") and len(parts) > 3:
        return parts[3]
    return None


def src_area(path):
    """assets/src/<area>/... -> 一级区域名（game / config / sys ...）；根级 .luac 返回 (root)。"""
    parts = path.split("/")
    if path.startswith("assets/src/") and len(parts) > 3:
        return parts[2]
    if path.startswith("assets/src/") and len(parts) == 3:
        return "(src_root)"
    return None


def probe_version_strings(z, names):
    """从少量小 luac / json 明文里抓版本串。只读前 64KB。"""
    hits = []
    cand = [n for n in names
            if n.lower().endswith((".luac", ".json", ".txt", ".xml", ".properties", ".cfg", ".ini"))
            and ("version" in n.lower() or n.endswith("config.luac") or "file_update" in n.lower())]
    for n in cand[:400]:
        try:
            info = z.getinfo(n)
            if info.file_size > 262144:
                continue
            raw = z.read(n)
        except Exception:
            continue
        txt = raw.decode("utf-8", "ignore")
        for key in TEXT_PROBE:
            for m in re.finditer(key + r"[\"'\s:=]{1,4}([0-9A-Za-z_.\-]{1,40})", txt):
                hits.append({"file": n, "key": key, "value": m.group(1)})
    # 去重，保留前 60 条
    seen, out = set(), []
    for h in hits:
        k = (h["file"], h["key"], h["value"])
        if k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out[:60]


def scan_one(ver, apk_path, do_strings=False):
    if not os.path.exists(apk_path):
        return {"version": ver, "apk": apk_path, "error": "APK NOT FOUND"}
    z = zipfile.ZipFile(apk_path)
    infos = z.infolist()
    names = [i.filename for i in infos]

    buckets = collections.Counter()
    src_mods = collections.Counter()
    src_areas = collections.Counter()
    src_root_files = []
    lua_all, src_lua, cfg_tables, cmdres = [], [], [], []
    ui_files = []
    res_cats = collections.Counter()
    assets_bytes = 0

    for i in infos:
        n = i.filename
        buckets[classify(n)] += 1
        if n.startswith("assets/"):
            assets_bytes += i.file_size
        base = os.path.basename(n)
        if n.endswith(".luac"):
            lua_all.append(n)
            if n.startswith("assets/src/"):
                src_lua.append(n)
                mod = src_module(n)
                if mod:
                    src_mods[mod] += 1
                area = src_area(n)
                if area:
                    src_areas[area] += 1
                if area == "(src_root)":
                    src_root_files.append(n)
                if base.endswith(UI_SUFFIXES):
                    ui_files.append(n)
            if CONFIG_RE.match(base):
                cfg_tables.append(base)
            if CMDRES_RE.match(base):
                cmdres.append(base)
        elif n.startswith("assets/res/"):
            parts = n.split("/")
            res_cats[parts[3] if len(parts) > 3 else "(res_root)"] += 1

    ui_by_module = collections.defaultdict(list)
    for u in ui_files:
        ui_by_module[src_module(u) or src_area(u) or "(src)"] .append(os.path.basename(u))

    # basename -> 所属 game 模块目录（用于把 systems_master 的 lua_modules 反查到模块）
    luac_module_index = collections.defaultdict(set)
    for p in src_lua:
        mod = src_module(p)
        if mod:
            luac_module_index[os.path.basename(p)].add(mod)

    res_files_by_category = collections.defaultdict(list)
    for i in infos:
        n = i.filename
        if n.startswith("assets/res/"):
            parts = n.split("/")
            cat = parts[3] if len(parts) > 3 else "(res_root)"
            if len(res_files_by_category[cat]) < 400:
                res_files_by_category[cat].append(os.path.basename(n))

    result = {
        "version": ver,
        "apk": apk_path,
        "apk_bytes": os.path.getsize(apk_path),
        "entries": len(names),
        "assets_bytes": assets_bytes,
        "buckets": dict(buckets),
        "lua_total": len(lua_all),
        "lua_src": len(src_lua),
        "luac_basenames": sorted(set(os.path.basename(p) for p in lua_all)),
        "game_modules": sorted(src_mods.keys()),
        "src_areas": dict(src_areas),
        "src_root_files": sorted(os.path.basename(p) for p in src_root_files),
        "src_module_filecount": dict(src_mods),
        "config_tables": sorted(set(cfg_tables)),
        "cmd_resolve": sorted(set(cmdres)),
        "ui_files": sorted(ui_files),
        "ui_by_module": {k: sorted(v) for k, v in sorted(ui_by_module.items())},
        "luac_module_index": {k: sorted(v) for k, v in sorted(luac_module_index.items())},
        "res_files_by_category": {k: sorted(set(v)) for k, v in sorted(res_files_by_category.items())},
        "res_categories": dict(res_cats.most_common()),
        "version_probe": probe_version_strings(z, names),
        "evidence_level": "CONFIRMED",
        "evidence": "%s zip central directory (%d entries)" % (os.path.basename(apk_path), len(names)),
    }
    entries_file = os.path.join(OUT, "apk_entries_%s.txt" % ver.replace(".", "_"))
    with io.open(entries_file, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(names)))
    result["entries_file"] = os.path.relpath(entries_file, ROOT).replace("\\", "/")

    if do_strings:
        result["luac_strings_sample"] = extract_strings(z, src_lua[:400])
    z.close()
    return result


def extract_strings(z, files):
    """对少量 luac 做可打印字符串抽取（ASCII/Lua 常量）。仅抽样，非完整反编译。"""
    pat = re.compile(rb"[\x20-\x7e]{6,80}")
    out = {}
    for n in files:
        try:
            raw = z.read(n)
        except Exception:
            continue
        s = [m.group().decode("ascii", "ignore") for m in pat.finditer(raw)]
        if s:
            out[os.path.basename(n)] = s[:60]
    return out


def build_diff(scans):
    """三包跨版本 diff：模块 / 配置表 / cmd_resolve / UI。"""
    def s(ver, key):
        return set(scans.get(ver, {}).get(key, []) or [])
    diff = {}
    pairs = [("1.4.11", "1.3.0"), ("1.4.11", "1.4.9"), ("1.4.9", "1.3.0")]
    for a, b in pairs:
        tag = "%s_vs_%s" % (a.replace(".", "_"), b.replace(".", "_"))
        diff[tag] = {
            "game_modules_only_in_%s" % a: sorted(s(a, "game_modules") - s(b, "game_modules")),
            "game_modules_only_in_%s" % b: sorted(s(b, "game_modules") - s(a, "game_modules")),
            "config_tables_only_in_%s" % a: sorted(s(a, "config_tables") - s(b, "config_tables")),
            "config_tables_only_in_%s" % b: sorted(s(b, "config_tables") - s(a, "config_tables")),
            "cmd_resolve_only_in_%s" % a: sorted(s(a, "cmd_resolve") - s(b, "cmd_resolve")),
            "cmd_resolve_only_in_%s" % b: sorted(s(b, "cmd_resolve") - s(a, "cmd_resolve")),
            "ui_files_only_in_%s" % a: sorted(s(a, "ui_files") - s(b, "ui_files")),
            "ui_files_only_in_%s" % b: sorted(s(b, "ui_files") - s(a, "ui_files")),
        }
    return diff


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None, help="只扫某一版本，如 1.4.11")
    ap.add_argument("--strings", action="store_true", help="额外抽 luac 可打印字符串样本")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    scans = {}
    for ver, path in APKS.items():
        if args.only and args.only != ver:
            continue
        sys.stderr.write("[scan] %s <- %s\n" % (ver, path))
        r = scan_one(ver, path, do_strings=args.strings)
        scans[ver] = r
        with io.open(os.path.join(OUT, "apk_scan_%s.json" % ver.replace(".", "_")),
                     "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=1)

    summary = {
        "generated_by": "tools/jstm_audit/scan_apk.py",
        "evidence_level": "CONFIRMED",
        "note": "只读 zip 中央目录扫描；不含反编译，不修改 APK。",
        "versions": {v: {k: r.get(k) for k in
                         ("apk", "apk_bytes", "entries", "assets_bytes",
                          "lua_total", "lua_src", "entries_file")}
                     for v, r in scans.items()},
        "diff": build_diff(scans) if len(scans) > 1 else {},
    }
    with io.open(os.path.join(OUT, "apk_scan_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    for v, r in scans.items():
        if "error" in r:
            print("%-7s ERROR %s" % (v, r["error"]))
            continue
        print("%-7s entries=%-6d luac=%-5d cfg=%-4d cmdres=%-4d ui=%-4d gamemods=%-4d assets=%.1fMB"
              % (v, r["entries"], r["lua_total"], len(r["config_tables"]),
                 len(r["cmd_resolve"]), len(r["ui_files"]), len(r["game_modules"]),
                 r["assets_bytes"] / 1048576))
    print("-> %s" % OUT)


if __name__ == "__main__":
    main()
