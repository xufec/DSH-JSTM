import zipfile, os, json, collections

APS = {
    "1.3.0":  r"C:\Users\xu\Desktop\DSH\anzbao\dldlJl.apk",
    "1.4.9":  r"C:\Users\xu\Desktop\DSH\anzbao\jstm.apk",
    "1.4.11": r"C:\Users\xu\Desktop\DSH\anzbao\jstm_142165.apk",
}

def analyze(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    luac = [n for n in names if n.endswith(".luac")]
    src = [n for n in luac if n.startswith("assets/src/")]
    mods = set()
    for n in src:
        if n.startswith("assets/src/game/"):
            p = n.split("/")
            if len(p) > 4:
                mods.add(p[3])
        elif n.startswith("assets/src/"):
            p = n.split("/")
            if len(p) > 3:
                mods.add(p[2])
    cfg = sorted(set(os.path.basename(n) for n in luac if os.path.basename(n).startswith("config_")))
    cmdr = sorted(set(os.path.basename(n) for n in luac if os.path.basename(n).startswith("cmd_resolve_")))
    return {
        "entries": len(names),
        "luac": len(luac),
        "src_luac": len(src),
        "assets_bytes": sum(z.getinfo(n).file_size for n in names if n.startswith("assets/")),
        "mods": mods,
        "configs": set(cfg),
        "cmd_resolve": set(cmdr),
    }

res = {k: analyze(v) for k, v in APS.items()}
summary = {}
for k, r in res.items():
    summary[k] = {kk: (len(vv) if isinstance(vv, set) else vv) for kk, vv in r.items()}
print(json.dumps(summary, indent=2, ensure_ascii=False))

v149, v1411, v130 = res["1.4.9"], res["1.4.11"], res["1.3.0"]
print("\n=== game module dirs ===")
print("1.3.0 only :", sorted(v130["mods"] - v149["mods"] - v1411["mods"]))
print("1.4.9 only :", sorted(v149["mods"] - v130["mods"] - v1411["mods"]))
print("1.4.11 only:", sorted(v1411["mods"] - v130["mods"] - v149["mods"]))
print("in 1.4.11 not 1.3.0:", sorted(v1411["mods"] - v130["mods"]))
print("in 1.3.0 not 1.4.11:", sorted(v130["mods"] - v1411["mods"]))

print("\n=== config_*.luac tables ===")
print("1.3.0 count:", len(v130["configs"]), "1.4.9 count:", len(v149["configs"]), "1.4.11 count:", len(v1411["configs"]))
print("1.4.11 only vs 1.3.0:", sorted(v1411["configs"] - v130["configs"]))
print("1.3.0 only vs 1.4.11:", sorted(v130["configs"] - v1411["configs"]))

print("\n=== cmd_resolve files ===")
print("1.3.0:", len(v130["cmd_resolve"]), "1.4.9:", len(v149["cmd_resolve"]), "1.4.11:", len(v1411["cmd_resolve"]))
print("1.4.11 only:", sorted(v1411["cmd_resolve"] - v130["cmd_resolve"]))
print("1.3.0 only:", sorted(v130["cmd_resolve"] - v1411["cmd_resolve"]))

out = r"C:\Users\xu\Desktop\DSH\analysis\version_compare\_apk_structural_compare.json"
json.dump({
    "per_version": {k: {kk: (sorted(vv) if isinstance(vv, set) else vv) for kk, vv in r.items()} for k, r in res.items()},
    "diffs": {
        "mods_1411_only_vs_130": sorted(v1411["mods"] - v130["mods"]),
        "mods_130_only_vs_1411": sorted(v130["mods"] - v1411["mods"]),
        "configs_1411_only_vs_130": sorted(v1411["configs"] - v130["configs"]),
        "configs_130_only_vs_1411": sorted(v130["configs"] - v1411["configs"]),
        "cmd_resolve_1411_only": sorted(v1411["cmd_resolve"] - v130["cmd_resolve"]),
        "cmd_resolve_130_only": sorted(v130["cmd_resolve"] - v1411["cmd_resolve"]),
    }
}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwrote", out)
