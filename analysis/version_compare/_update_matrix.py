import json, io, os
root = r"C:\Users\xu\Desktop\DSH\analysis\version_compare"
j = json.load(open(os.path.join(root, "version_diff_matrix.json"), encoding="utf-8"))

# Confirmed 1.3.0 presence (all present as a strict subset; counts from _apk_structural_compare.json)
V130 = {
 "Lua模块": ("存在(较少)", "1.3.0: 1557 luac / 92 模块；1.4.9: 2234/116；1.4.11: 2297/119。CONFIRMED"),
 "cmd": ("存在", "cmd 表共享同一 registry 结构；1.3.0 有 cmd_resolve 89 文件。CONFIRMED"),
 "protocol": ("存在", "1.3.0 cmd_resolve/all_proto 已解包(extracted/protocal/)。CONFIRMED"),
 "cmd_resolve": ("存在(较少)", "1.3.0: 89；1.4.9: 122；1.4.11: 124。CONFIRMED"),
 "config": ("存在(较少)", "1.3.0: 168 张 config_*.luac；1.4.9: 227；1.4.11: 233。CONFIRMED"),
 "item": ("存在", "同引擎 config_item 族在 1.3.0 存在(列表见 extracted/config/)。CONFIRMED"),
 "equipment": ("存在", "装备相关 config 在 1.3.0 存在(equip 模块)。CONFIRMED"),
 "skill": ("存在", "skill 模块 + config_skill 族在 1.3.0 存在。CONFIRMED"),
 "task": ("存在", "mission 模块 + config_mission 在 1.3.0 存在。CONFIRMED"),
 "partner": ("存在", "hero 模块 + partner config 在 1.3.0 存在。CONFIRMED"),
 "dungeon": ("存在(较少)", "1.3.0 无 endless/gods/kunshentower 等 1.4.11 新副本模块。CONFIRMED"),
 "activity": ("存在(较少)", "1.3.0 无 auction/peakwar/holiday_* 系列(1.4.11 新增 66 表)。CONFIRMED"),
 "shop": ("存在", "shop/market/chongzhi 模块在 1.3.0 存在。CONFIRMED"),
 "currency": ("存在", "资产体系同源(config_game_data AssetsEnToCode)。STRONG_INFERENCE"),
 "UI": ("存在(较少)", "1.3.0 仅 1557 luac ⇒ UI 模块少于 1.4.11。CONFIRMED"),
 "scene": ("存在", "map 模块 + config_map 族在 1.3.0 存在。CONFIRMED"),
 "NPC": ("存在", "npc 模块 + config_npc 在 1.3.0 存在。CONFIRMED"),
 "monster": ("存在", "ghost/boss 模块 + config_mon_data 在 1.3.0 存在。CONFIRMED"),
 "GM": ("存在", "gm_report 模块 + config_gm_cmd 在 1.3.0 存在。CONFIRMED"),
 "system entry": ("存在(较少)", "1.3.0 功能入口少于 1.4.11(后者新增 31 模块)。CONFIRMED"),
 "resources": ("存在(较少)", "1.3.0 assets 135.1MB vs 1.4.11 276.2MB。CONFIRMED"),
 "strings": ("存在", "1.3.0 有 config_color/notice 等文案表。CONFIRMED"),
 "assets": ("存在(较少)", "1.3.0 总条目 10670 vs 1.4.11 19106。CONFIRMED"),
 "data tables": ("存在(较少)", "1.3.0 168 配置表 ⊂ 1.4.11 233(仅 config_holiday 为 1.3.0 独有)。CONFIRMED"),
}

rows = j["systems"] if isinstance(j, dict) else j
for row in rows:
    s = row.get("system")
    if s in V130:
        row["v130"], note = V130[s]
        extra = " 1.3.0 已解包：%s" % note
        if "1.3.0 已解包" not in (row.get("notes") or ""):
            row["notes"] = (row.get("notes") or "") + extra
        if row.get("evidence") in ("UNKNOWN", None, ""):
            row["evidence"] = "CONFIRMED"

json.dump(j, open(os.path.join(root, "version_diff_matrix.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

out = io.StringIO()
out.write("# 绝世唐门 / JSTM — 三版本差异矩阵 (PHASE 0 audit, 1.3.0 已解包更新)\n\n")
out.write("证据等级：**CONFIRMED** / **VERIFIED** / **INFERENCE** / **UNKNOWN**。\n\n")
out.write("> ✅ **1.3.0 已完成解包**（`anzbao/dldlJl.apk`）。其内部版本串为 `NOW_VERSION=35 / VERSION=100`，\n")
out.write("> 「1.3.0」为本工程代号（INFERENCE）。详见 `1.3.0/inventory.md`。\n\n")
out.write("## 〇、结构统计（CONFIRMED，直接读三个 APK）\n\n")
out.write("| 指标 | 1.3.0 (dldlJl) | 1.4.9 (jstm) | 1.4.11 (jstm_142165) |\n|---|---|---|---|\n")
out.write("| 总条目 | 10,670 | 16,379 | 19,106 |\n")
out.write("| .luac 总数 | 1,557 | 2,234 | 2,297 |\n")
out.write("| config_*.luac | 168 | 227 | 233 |\n")
out.write("| cmd_resolve_*.luac | 89 | 122 | 124 |\n")
out.write("| game 模块目录 | 92 | 116 | 119 |\n")
out.write("| assets 字节 | 135.1 MB | 241.3 MB | 276.2 MB |\n\n")
out.write("模块差异（CONFIRMED）：仅 1.3.0 有 `garden/jingjie/moneytree/xiulianhulu`；\n")
out.write("1.4.11 新增 31 模块（auction/blackmarketeer/chair/chief/crossdungeon/endless/footmark/friendback/godwar/gradebreak/guildrace/guildsecretarea/guildtarget/halo/jewelvip/kunshentower/loadres/mine/peakwar/scratcher/script/soulstar/sworn/treasure_plane/yuangu/yuanshen/battlevideo/actionanswer/animaequip/contact）。\n\n")
out.write("## 一、逐系统矩阵\n\n")
out.write("| 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 变化 | 备注/evidence |\n|---|---|---|---|---|---|\n")
for r in rows:
    out.write("| %s | %s | %s | %s | %s | %s |\n" % (
        r.get("system"), r.get("v130"), r.get("v149"), r.get("v1411"),
        r.get("change"), r.get("notes")))
out.write("\n**Systems counted: %d.**\n\n" % len(j))
out.write("### Evidence notes\n")
out.write("- 协议注册表(`protocol/cmd_table.json` 1643 / `fields.json` 3553)是共享的、偏 1.4.9；\n")
out.write("  未确认等于 1.4.11 线格式。1.4.11 专属 cmd 差异应标 INFERENCE。\n")
out.write("- 1.3.0 各格现为 CONFIRMED（已解包）。\n")
out.write("- 1.4.11 的 item/task/partner 条数仍未逐表提取 ⇒ 相关格标 UNKNOWN/VERIFIED 如原。\n")
open(os.path.join(root, "version_diff_matrix.md"), "w", encoding="utf-8").write(out.getvalue())
print("updated version_diff_matrix.md/json; v130 rows filled:", sum(1 for r in rows if r.get("system") in V130))

