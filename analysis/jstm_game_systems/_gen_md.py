# generate systems_master.md and unimplemented_systems.md from systems_master.json
import json, io, os, collections

root = r"C:\Users\xu\Desktop\DSH\analysis\jstm_game_systems"
src = os.path.join(root, "systems_master.json")
_raw = json.load(open(src, encoding="utf-8"))
data = _raw["systems"] if isinstance(_raw, dict) and "systems" in _raw else _raw

CAT = {
 "CORE":"A. 核心系统","ROLE":"B. 角色系统","GROWTH":"C. 成长系统","BATTLE":"D. 战斗系统",
 "EQUIP":"E. 装备系统","FRIEND":"F. 伙伴系统","APPEAR":"G. 外观系统","ECON":"H. 资源经济",
 "QUEST":"I. 任务系统","MAP":"J. 地图系统","DUNGEON":"K. 副本系统","ACT":"L. 活动系统",
 "SOCIAL":"M. 社交系统","COMM":"N. 商业系统 / 对抗","GM":"O. GM 系统","BACK":"P. 后台系统",
 "HIDDEN":"Q. 隐藏/未归类系统","UNKNOWN":"R. 未知系统",
}
def cat_of(sid):
    parts = sid.split("_")
    return parts[1] if len(parts) > 1 else "UNKNOWN"

def fmt(v):
    if v is None: return ""
    if isinstance(v, list): return ", ".join(str(x) for x in v) if v else "—"
    return str(v)

def is_impl(st):
    st = (st or "").lower()
    if st.startswith("implemented") or st.startswith("partial") or "persisted" in st or "stub" in st:
        return "partial/impl"
    if "client" in st or "config only" in st or "client-only" in st or st.startswith("not implemented") or "unidentified" in st:
        return "not-impl"
    return "partial/impl"

MUMU_HEADER = """
## MuMu 运行时取证通道（mumu_runtime_evidence_channel）

> PHASE 0 审计新增硬约束，2026-10-02 写入。

**定位：** MuMu 运行时取证通道 = **VERIFIED 级证据的唯一来源**。APK 静态提取（配置表名/Lua 模块/协议号/DB 表结构）可作为 CONFIRMED；但数值字段、战斗行为、掉落结果、UI 显示值、回包内容必须经本机 MuMu 模拟器跑 1.4.11 客户端 + mock_server 联调后才能标 VERIFIED。

**采集流程：**
1. 启动 MuMu 12 实例（实例 0 `MuMu安卓设备`，Android 12 / hyperv）。
2. `adb connect 127.0.0.1:16384`（adb: `D:\\ADB\\platform-tools\\adb.exe`，亦在 PATH）；设备序列号 `127.0.0.1:16384`，product `rubens` / model `22041211A`，transport_id 1。
3. 安装并启动 1.4.11 补丁包：`C:\\Users\\xu\\Desktop\\DSH\\patched\\jstm_1411_fakelogin_aligned.apk`（**当前尚未安装 → 待安装**）。
4. 客户端 URL/host 配置指向本机 mock_server（TCP 9000）。
5. 抓协议 dump：客户端日志 / frida hook send/recv / 网络抓包。
6. 记录 UI 显示值与回包字段，与服务器应答逐字段比对。

**实测环境（CONFIRMED 级探测记录）：**
- MuMu 12 已安装（注册表 `MuMu模拟器 6.6.4.0`，安装目录 `D:\\MuMuPlayer`，引擎 `MuMuNxMain.exe`）。
- 实例 0 已启动；实例 1 `MuMu安卓设备-1` 存在但未启动。
- 已装包：`com.shiyue.dldl.ewan` = versionName **1.3.0** (versionCode 25, 2026-09-29)；`com.shiyue.dldl.ewan.qihoo` = versionName **1.4.9** (versionCode 44, 2026-10-01)。
- **1.4.11 尚未装入模拟器**；在装入并跑通联调前，所有数值/行为类结论不得从 INFERENCE/STRONG_INFERENCE 升级为 VERIFIED。

**标注规则：** 凡实现依赖真实运行数据（战斗数值、掉落表、装备属性、伙伴数值、怪物数值、战力公式、经验曲线、UI 显示值、商城价格等）的系统，在矩阵/未实现清单中标注 **「需 MuMu 运行时取证」**。

**Phase 1 前置：** 搭建 MuMu + mock_server 联调环境 = Phase 1 第一项任务。

---
"""

order = list(CAT.keys())
groups = collections.OrderedDict((k, []) for k in order)
for s in data:
    groups.setdefault(cat_of(s["system_id"]), []).append(s)

out = io.StringIO()
out.write("# JSTM 游戏系统百科 systems_master\n\n")
out.write("> PHASE 0 审计产物。主目标版本 1.4.11（`_tmp_cfg` 配置表 + `_tmp_*` Lua 模块 + mock_server 实现）。\n")
out.write("> 证据等级：CONFIRMED / VERIFIED / STRONG_INFERENCE / INFERENCE / UNKNOWN。UNKNOWN 不得当作事实。\n")
out.write("> 机读版本：`systems_master.json`（%d 个系统）。\n\n" % len(data))
out.write(MUMU_HEADER)
out.write("| 分类 | 系统数 |\n|---|---|\n")
for k in order:
    if k in groups and groups[k]:
        out.write("| %s | %d |\n" % (CAT.get(k, k), len(groups[k])))
out.write("| **合计** | **%d** |\n" % sum(len(groups[k]) for k in order if k in groups))
out.write("\n---\n\n")

for k in order:
    if k not in groups or not groups[k]:
        continue
    out.write("## %s\n\n" % CAT.get(k, k))
    out.write("| system_id | 名称 | 中文别名 | 客户端入口 | 协议 | 配置表 | 服务端 | 证据/置信 |\n")
    out.write("|---|---|---|---|---|---|---|---|\n")
    for s in groups[k]:
        runtime_mark = " ⏳需MuMu取证" if s.get("needs_mumu_runtime") else ""
        out.write("| %s | %s | %s | %s | %s | %s | %s%s | %s / %s |\n" % (
            s["system_id"], fmt(s.get("system_name")), fmt(s.get("aliases")),
            fmt(s.get("client_entry")), fmt(s.get("protocols")), fmt(s.get("config_files")),
            fmt(s.get("implementation_status")), runtime_mark,
            fmt(s.get("evidence")), fmt(s.get("confidence"))))
    out.write("\n")
    for s in groups[k]:
        out.write("### %s — %s\n" % (s["system_id"], fmt(s.get("system_name"))))
        for f in ["aliases","version","client_entry","lua_modules","protocols","config_files","data_files",
                  "UI_files","dependencies","server_state","database_state","rewards","currencies",
                  "related_systems","evidence","confidence","implementation_status"]:
            if s.get(f) not in (None, "", []):
                out.write("- **%s**: %s\n" % (f, fmt(s.get(f))))
        if s.get("needs_mumu_runtime"):
            out.write("- **needs_mumu_runtime**: true （需 MuMu 运行时取证）\n")
        if s.get("notes"):
            out.write("- **notes**: %s\n" % fmt(s["notes"]))
        out.write("\n")
    out.write("---\n\n")

open(os.path.join(root, "systems_master.md"), "w", encoding="utf-8").write(out.getvalue())

# unimplemented
not_impl = [s for s in data if is_impl(s.get("implementation_status")) == "not-impl"]
u = io.StringIO()
u.write("# 未实现 / 未接入系统清单 unimplemented_systems\n\n")
u.write("> PHASE 0 审计产物。判据：客户端存在入口（config 表 / Lua 模块 / function id / 协议），\n")
u.write("> 但 mock_server 无对应数据库表或仅有通用/空响应、或完全没有服务端实现。\n")
u.write("> 证据等级见各行。共 **%d** 项（另有 partial 项已实现但未完整，见 systems_master.md）。\n\n" % len(not_impl))
u.write("> **⏳「需 MuMu 运行时取证」含义**：该系统的数值/掉落/奖励/UI 行为只有在 1.4.11 客户端于 MuMu 实机运行 + mock_server 联调后，才能确认真实值与行为；APK 静态配置表存在性仍按 CONFIRMED 处理。详见 systems_master.md 顶部「MuMu 运行时取证通道」。\n\n")
u.write("| 系统 | 分类 | 发现位置(客户端入口) | 版本 | 相关配置 | 关联协议 | 依赖 | 优先级 | 证据等级 | 运行时取证 |\n")
u.write("|---|---|---|---|---|---|---|---|---|---|\n")
for s in not_impl:
    prio = "P1" if cat_of(s["system_id"]) in ("ECON","QUEST","DUNGEON","ACT","SOCIAL","APPEAR","GROWTH") else "P2"
    rt = "⏳需MuMu取证" if s.get("needs_mumu_runtime") else "—"
    u.write("| %s (%s) | %s | %s | %s | %s | %s | %s | %s | %s | %s |\n" % (
        fmt(s.get("system_name")), fmt(s.get("aliases")), CAT.get(cat_of(s["system_id"]), ""),
        fmt(s.get("client_entry")), fmt(s.get("version")), fmt(s.get("config_files")),
        fmt(s.get("protocols")), fmt(s.get("dependencies")), prio, fmt(s.get("confidence")), rt))
u.write("\n## 逐项详述\n\n")
for s in not_impl:
    u.write("### %s — %s\n" % (s["system_id"], fmt(s.get("system_name"))))
    for f in ["aliases","version","client_entry","lua_modules","protocols","config_files","dependencies",
              "server_state","database_state","evidence","confidence","implementation_status"]:
        if s.get(f) not in (None,"",[]):
            u.write("- **%s**: %s\n" % (f, fmt(s.get(f))))
    if s.get("needs_mumu_runtime"):
        u.write("- **needs_mumu_runtime**: true （需 MuMu 运行时取证）\n")
    u.write("\n")
open(os.path.join(root, "unimplemented_systems.md"), "w", encoding="utf-8").write(u.getvalue())

print("systems_master.md written; unimplemented count =", len(not_impl), "of", len(data))
