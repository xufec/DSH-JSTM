import json, io, os
root = r"C:\Users\xu\Desktop\DSH\analysis"
_raw = json.load(open(os.path.join(root, "jstm_game_systems", "systems_master.json"), encoding="utf-8"))
data = _raw["systems"] if isinstance(_raw, dict) and "systems" in _raw else _raw

def f(v):
    if v is None: return ""
    if isinstance(v, list): return ", ".join(map(str, v)) if v else "—"
    return str(v)

def st(s):
    x = (s.get("implementation_status") or "").lower()
    if x.startswith("implemented"): base = "✅ 已实现"
    elif x.startswith("partial"): base = "🟡 部分实现"
    elif "client" in x or "config only" in x or x.startswith("not implemented") or "unidentified" in x:
        base = "❌ 未实现"
    else:
        base = "🟡 部分实现"
    if s.get("needs_mumu_runtime"):
        base += " ⏳需MuMu取证"
    return base

out = io.StringIO()
out.write("# 客户端系统 → 服务端需求矩阵 client_server_matrix\n\n")
out.write("> PHASE 0 审计产物。由 `analysis/jstm_game_systems/systems_master.json` 生成。\n")
out.write("> 主目标版本 1.4.11。状态：✅ 已实现 / 🟡 部分实现 / ❌ 未实现。\n")
out.write("> **⏳「需MuMu取证」= 该系统实现依赖真实运行数据（战斗数值/掉落表/装备属性/伙伴数值/怪物数值/战力公式/经验曲线/UI 显示值等），须在 MuMu 模拟器跑通 1.4.11 客户端 + mock_server 联调后才能确认真实值；详见 systems_master.md 顶部「MuMu 运行时取证通道」。**\n\n")
out.write("| 系统 | APK 入口 | 协议 | 数据(config/DB) | 服务端 | 状态 |\n")
out.write("|---|---|---|---|---|---|\n")
for s in data:
    entry = f(s.get("client_entry")) or "—"
    proto = f(s.get("protocols")) or "—"
    if len(proto) > 60: proto = proto[:57] + "…"
    datafiles = (f(s.get("config_files")) + " | " + f(s.get("database_state"))).strip(" |")
    if len(datafiles) > 80: datafiles = datafiles[:77] + "…"
    srv = f(s.get("server_state")) or "—"
    out.write("| %s (%s) | %s | %s | %s | %s | %s |\n" % (
        f(s.get("system_name")), f(s.get("aliases")), entry, proto, datafiles, srv, st(s)))
open(os.path.join(root, "client_server_matrix.md"), "w", encoding="utf-8").write(out.getvalue())
print("client_server_matrix.md written, rows =", len(data))
