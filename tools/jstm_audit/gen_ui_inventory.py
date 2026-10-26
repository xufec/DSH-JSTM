#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE C0 只读审计：生成《绝世唐门》UI 清单 (ui_inventory.json / .md)。

- 骨架：1.4.11 apk_scan.ui_by_module（115 模块）
- 每条 = 一个界面/面板（不是每个 luac 文件）
- 自动：版本存在性、模块→系统映射、B/D 初判、资源类关联
- 人工覆盖：A 类（实机验证证据）在 A_CLASS_OVERRIDES 中
- 只读：不修改任何既有文件；只写 ui_inventory.json/.md 到本脚本同目录的上一级
"""

import json, os, re, sys
from collections import defaultdict, OrderedDict

ROOT = r"C:\Users\xu\Desktop\DSH"
RAW  = os.path.join(ROOT, "analysis", "jstm_client_audit", "_raw")
OUTDIR = os.path.join(ROOT, "analysis", "jstm_client_audit")
SYS_MASTER = os.path.join(ROOT, "analysis", "jstm_game_systems", "systems_master.json")

# ---------------------------------------------------------------------------
# 1. 加载扫描数据
# ---------------------------------------------------------------------------
def load_scan(ver):
    p = os.path.join(RAW, f"apk_scan_{ver.replace('.','_')}.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

s130  = load_scan("1.3.0")
s149  = load_scan("1.4.9")
s1411 = load_scan("1.4.11")

with open(os.path.join(RAW, "apk_scan_summary.json"), "r", encoding="utf-8") as f:
    summary = json.load(f)
with open(SYS_MASTER, "r", encoding="utf-8") as f:
    sysmaster = json.load(f)

# 1.3.0 缺失/1.4.11 新增模块
d11_vs_130 = summary["diff"]["1_4_11_vs_1_3_0"]
modules_only_in_130 = set(d11_vs_130["game_modules_only_in_1.3.0"])
ui_files_only_in_130 = set(d11_vs_130["ui_files_only_in_1.3.0"])
config_only_in_130   = set(d11_vs_130["config_tables_only_in_1.3.0"])

# ---------------------------------------------------------------------------
# 2. system_master 索引：basename → system_id
# ---------------------------------------------------------------------------
base2sys = {}  # basename (e.g. "achieve_panel.luac") -> (system_id, system_name)
sys_by_id = {}
for s in sysmaster["systems"]:
    sid = s["system_id"]; sname = s["system_name"]
    sys_by_id[sid] = s
    for m in s.get("lua_modules", []) or []:
        b = os.path.basename(m).lower()
        base2sys.setdefault(b, (sid, sname))
    ce = s.get("client_entry", "") or ""
    if ce and ce.endswith(".luac"):
        base2sys.setdefault(os.path.basename(ce).lower(), (sid, sname))

# 模块名（game/<mod>）→ system_id 的粗映射（兜底）
# 关键字段：sysmaster 里 lua_modules 通常以 <mod>_xxx.luac 出现
mod2sys = {}
for s in sysmaster["systems"]:
    sid = s["system_id"]
    for m in s.get("lua_modules", []) or []:
        b = os.path.basename(m).lower().replace(".luac", "")
        # 取前缀
        prefix = b.split("_")[0]
        if prefix and prefix not in ("",):
            mod2sys.setdefault(prefix, (sid, s["system_name"]))

# 显式模块→系统映射（mod2sys 启发式不准的，手工兜底）
MOD2SYS_EXPLICIT = {
    "achieve":     ("SYS_QUEST_003", "Achievement 成就"),
    "action":      ("SYS_ACT_006",   "Operation Activity 节日/运营活动"),
    "actionanswer":("SYS_ACT_007",  "Answer Quiz 答题(活动版)"),
    "activity":    ("SYS_ACT_006",   "Operation Activity"),
    "advance":     ("SYS_GROWTH_005","Morale/Advance"),
    "alchemy":     ("SYS_EQUIP_002", "Smith/Forge 锻造/合成"),
    "animaequip":  ("SYS_APPEAR_009","Fashion/Skin 时装(动画装备)"),
    "answer":      ("SYS_ACT_007",   "Answer Quiz 答题"),
    "arena":       ("SYS_COMM_002",  "Arena 竞技场"),
    "artifact":    ("SYS_APPEAR_005","Divine Artifact 神器"),
    "auction":     ("SYS_ECON_008",  "Auction/拍卖"),
    "automate":    ("SYS_BATTLE_002","Auto-battle/AFK 挂机"),
    "backpack":    ("SYS_ECON_002",  "Inventory/Bag 背包"),
    "battle":      ("SYS_BATTLE_001","Turn-based Battle 回合制战斗"),
    "battlevideo": ("SYS_BATTLE_003","Battle Replay 战报"),
    "beast":       ("SYS_APPEAR_003","Beast 灵兽"),
    "blackmarketeer":("SYS_ECON_006","Black Market 黑市"),
    "boss":        ("SYS_BATTLE_005","Boss System BOSS"),
    "build":       ("SYS_APPEAR_008","Chair/座驾(cook/cut/forge/mojo UI)"),
    "cash":        ("SYS_ECON_003",  "Mall/Shop 现金商城"),
    "chair":       ("SYS_APPEAR_008","Vehicle/Chair 座驾"),
    "chat":        ("SYS_SOCIAL_001","Chat 聊天"),
    "chief":       ("SYS_HIDDEN_003","Chief 会长/百官"),
    "chongzhi":    ("SYS_ECON_010",  "Recharge/充值"),
    "circle":      ("SYS_SOCIAL_003","Moments/朋友圈"),
    "contact":     ("SYS_SOCIAL_002","Friend 联系人"),
    "convoy":      ("SYS_COMM_009",  "Freight/Escort 押镖"),
    "crossdungeon":("SYS_DUNGEON_005","Cross-server Dungeon 跨服副本"),
    "crossserver": ("SYS_COMM_005",  "Cross-server 跨服"),
    "daily":       ("SYS_QUEST_002", "Daily/Active 日常活跃"),
    "dailysign":   ("SYS_ACT_001",  "Sign-in 签到"),
    "demontower":  ("SYS_DUNGEON_003","Tower 镇魂塔"),
    "diguowar":    ("SYS_BATTLE_004","God War 帝国战"),
    "drop":        ("SYS_ECON_012", "Drop/Loot 掉落"),
    "dungeon":     ("SYS_DUNGEON_001","Dungeon 副本"),
    "endless":     ("SYS_DUNGEON_002","Endless Dungeon 无尽"),
    "equip":       ("SYS_EQUIP_001","Equipment 装备"),
    "equipforge":  ("SYS_EQUIP_002","Smith/Forge 锻造"),
    "fengce":      ("SYS_UNKNOWN_002","封测/活动运营"),
    "flyup":       ("SYS_ACT_006",  "FlyUp 飞升成神活动"),
    "footmark":    ("SYS_APPEAR_001","Wing/Footmark 足迹"),
    "form":        ("SYS_FRIEND_002","Formation 阵法"),
    "friend":      ("SYS_SOCIAL_002","Friend 好友"),
    "friendback":  ("SYS_ACT_012",  "Return/Back Flow 回归"),
    "gangwars":    ("SYS_SOCIAL_009","Guild Wars 公会战"),
    "ghost":       ("SYS_HIDDEN_002","XiuLuo/Ghost 修罗"),
    "gm_report":   ("SYS_GM_001",   "GM Tools"),
    "godredeem":   ("SYS_HIDDEN_005","God Redemption 神位"),
    "godwar":      ("SYS_BATTLE_004","God War Battle 神魔战"),
    "gradebreak":  ("SYS_ROLE_005", "Grade Break 等级突破"),
    "guider":      ("SYS_QUEST_005","Guide System 新手引导"),
    "guild":       ("SYS_SOCIAL_004","Guild 公会"),
    "guildrace":   ("SYS_COMM_004", "Race/Guild Race 竞速"),
    "guildsecretarea":("SYS_SOCIAL_010","Guild Secret Area 公会秘境"),
    "guildtarget": ("SYS_SOCIAL_010","Guild Target 公会目标"),
    "guildwars":   ("SYS_SOCIAL_009","Guild Wars 公会战"),
    "halo":        ("SYS_APPEAR_010","Halo 光环"),
    "head":        ("SYS_ROLE_006", "Avatar/Head 头像"),
    "hero":        ("SYS_FRIEND_001","Partner/Hero 伙伴"),
    "hide":        ("SYS_CORE_008", "Red Dot/Hide 红点隐藏"),
    "horse":       ("SYS_APPEAR_002","Mount 坐骑"),
    "invest":      ("SYS_ACT_003",  "Invest 投资"),
    "jewelvip":    ("SYS_ROLE_004", "VIP/宝石VIP"),
    "jubaopen":    ("SYS_ACT_006",  "聚宝盆活动"),
    "kunshentower":("SYS_DUNGEON_003","KunShen Tower 坤神塔"),
    "login":       ("SYS_CORE_001","Account Login 登录"),
    "mail":        ("SYS_ECON_009", "Mail 邮件"),
    "main":        ("SYS_CORE_003","Role Main UI 主界面"),
    "map":         ("SYS_MAP_001", "World Map 世界地图"),
    "market":      ("SYS_ECON_005","Trade Market 市场"),
    "mine":        ("SYS_COMM_006","Mining 采矿"),
    "mission":     ("SYS_QUEST_001","Mission 任务"),
    "nav":         ("SYS_MAP_001", "Nav 导航"),
    "newguide":    ("SYS_QUEST_005","New Guide 新手指引"),
    "notice":      ("SYS_CORE_008","Notice 公告"),
    "npc":         ("SYS_CORE_005","NPC 交互"),
    "peakwar":     ("SYS_COMM_003","Peakwar 巅峰战"),
    "prompt":      ("SYS_CORE_008","Prompt 提示"),
    "race":        ("SYS_COMM_004","Race 竞速"),
    "rank":        ("SYS_COMM_001","Rank 排行榜"),
    "recharge":    ("SYS_ECON_010","Recharge/Payment 充值"),
    "role":        ("SYS_ROLE_001","Role Attribute 角色属性"),
    "rotatetable": ("SYS_ACT_004", "Turntable 转盘"),
    "scene":       ("SYS_CORE_005","Scene 场景"),
    "scratcher":   ("SYS_ACT_005", "Scratch Card 刮刮乐"),
    "set":         ("SYS_CORE_009","Settings 设置"),
    "shop":        ("SYS_ECON_003","Mall/Shop 商城"),
    "sidebar":     ("SYS_CORE_009","Sidebar 侧边栏"),
    "skill":       ("SYS_GROWTH_001","Skill 技能"),
    "soulstar":    ("SYS_HIDDEN_004","Star Soul 星魂"),
    "story":       ("SYS_QUEST_005","Story 剧情"),
    "sworn":       ("SYS_SOCIAL_006","Jiebai 结拜"),
    "team":        ("SYS_MAP_002", "Team 组队"),
    "title":       ("SYS_ROLE_003", "Title 称号"),
    "tower":       ("SYS_DUNGEON_003","Tower 塔"),
    "treasure":    ("SYS_ACT_011", "Treasure 夺宝"),
    "treasure_plane":("SYS_MAP_001","Treasure Plane 秘境"),
    "trial":       ("SYS_DUNGEON_005","Trial 试炼"),
    "turntable":   ("SYS_ACT_004", "Turntable 转盘"),
    "vip":         ("SYS_ROLE_004", "VIP 系统"),
    "warehouse":   ("SYS_ECON_004","Storage 仓库"),
    "weapon":      ("SYS_FRIEND_006","Partner Weapon 伙伴武器"),
    "wedding":     ("SYS_SOCIAL_005","Marriage 结婚"),
    "wing":        ("SYS_APPEAR_001","Wing 翅膀"),
    "xianmo":      ("SYS_BATTLE_004","XianMo 仙魔"),
    "xianzun":     ("SYS_HIDDEN_005","XianZun 仙尊"),
    "xuan":        ("SYS_UNKNOWN_002","Xuan 选服"),
    "yuangu":      ("SYS_DUNGEON_005","YuanGu 远古"),
    "yuanshen":    ("SYS_APPEAR_004","Yuanshen 元神"),
    "config":      ("SYS_BACK_001", "Config Tables 配置表"),
    "common":      ("SYS_CORE_009","Common UI 通用组件"),
    "base":        ("SYS_CORE_009","Base View 基础视图"),
    "sys":         ("SYS_CORE_006","System 系统层"),
    "util":        ("SYS_CORE_006","Util 工具"),
    "loadres":     ("SYS_CORE_007","Resource Update 资源更新"),
    "ghost_ctrl":  ("SYS_HIDDEN_002","Ghost"),
    "gm_report_ctrl":("SYS_GM_001","GM"),
}

# ---------------------------------------------------------------------------
# 3. 面板文件识别
# ---------------------------------------------------------------------------
# 后缀：作为独立"界面条目"的文件
PANEL_SUFFIXES = ("_panel.luac", "_main_ui.luac")
# 兜底：若模块无 *_panel，则把主 view/ctrl 当界面
PRIMARY_VIEW_RE = re.compile(r"^(?P<mod>[a-z0-9]+)_(view|ctrl|ui)\.luac$")
# 子视图/辅助文件（不单独成条目，挂到父面板下）
SUPPORT_SUFFIXES = (
    "_view.luac", "_data.luac", "_ctrl.luac", "_vo.luac",
    "_item.luac", "_cell.luac", "_tip.luac", "_tips.luac",
    "_help.luac", "_select_view.luac", "_share_view.luac",
    "_share_select_view.luac", "_result_panel.luac", "_result_view.luac",
    "_pop.luac", "_popup.luac", "_ui.luac",
)
# 这些 _panel 是子面板/弹窗，独立成条目（按子前缀拆分）
def split_subprefix(fname):
    """
    对 action/hero/guild/role/yuanshen 这类大模块，按 <mod>_<sub>_<kind>.luac 拆分。
    返回 (sub_key, rest) ；无 sub 时 sub_key == ""。
    """
    b = fname[:-len(".luac")]  # strip .luac
    parts = b.split("_")
    # 至少 3 段才认为有 sub（mod_sub_kind）
    if len(parts) >= 3:
        return parts[1], "_".join(parts[2:])
    return "", "_".join(parts[1:])

# ---------------------------------------------------------------------------
# 4. A 类人工标注（实机验证证据）
#    key = module name (ui_by_module key) ；value = dict of panel_basename -> evidence
#    panel_basename == "*" 表示整个模块主面板
# ---------------------------------------------------------------------------
# A 类：必须有"实机截屏 + 点击/面板打开"证据。仅服务端命令注册/回包不算 A。
# key = module；"*" 仅作用于该模块主条目（sub=="" 的那个 panel）；
#       其他 key 必须是具体 panel 文件名（basename）。
A_CLASS_OVERRIDES = {
    "login": {"*": {
        "evidence": "runtime_evidence/README.md ; shots/20261002_002907_00_initial.png, p16_login.png",
        "protocols": ["CS_1110 AccountLogin", "CS_10103 RoleReLogin", "CS_1199 heartbeat"],
        "open": "App 启动 → 选服 → 自动登录（假登录补丁）",
        "close": "进入场景 10001 后自动关闭",
    }},
    "main": {"*": {
        "evidence": "shots/p16_game.png, p16_lv71.png, uival_13_main.png ; runtime_findings.md §D5.5",
        "protocols": ["CS_10300", "CS_10302", "CS_10502", "CS_11215", "CS_12803", "CS_16400"],
        "open": "登录完成后常驻主界面",
        "close": "（常驻）",
    }},
    "role": {"*": {
        "evidence": "runtime_findings.md §D1 ; shots/20261002_003507_tap_attr.png, p45a_attr.png, p2b_charpanel.png",
        "protocols": ["CS_10301", "CS_10303", "CS_10304", "CS_10306"],
        "open": "底部栏角色头像/属性按钮",
        "close": "(2200,70) X",
    }},
    "backpack": {"*": {
        "evidence": "runtime_findings.md §D2 ; shots/20261002_003407_tap_hunang.png, d2root_06_bag_open.png",
        "protocols": ["CS_10502 BagSync", "CS_10552 BagVolume"],
        "open": "底部栏「背包」/ 登录后默认弹出",
        "close": "(1900,40) X",
    }},
    "shop": {"*": {
        "evidence": "runtime_findings.md §D5.3 ; shots/20261002_003741_tap_mall.png, mall_clean.png",
        "protocols": ["CS_12803 MallList", "CS_12805 Buy(未实测购买)"],
        "open": "顶部栏「商城」(800,100)",
        "close": "面板 X",
    }},
    "skill": {"*": {
        "evidence": "extraction/skill_panel_located.md ; shots/hj_1710_224355.png, uival_05_skill.png",
        "protocols": ["CS_10621 SkillList", "CS_10622 LearnedSkill", "CS_10650 Talent"],
        "open": "底部栏「魂技」(1710,1320)",
        "close": "(2210,85) X",
    }},
    "automate": {"*": {
        "evidence": "extraction/ui_display_values.md §5 ; shots/uival_19_guaji.png, afk_05_afkpanel.png",
        "protocols": ["CS_15400/15402/15405 挂机族"],
        "open": "顶部栏「挂机」(1320,100)",
        "close": "(2210,85) X",
    }},
    "daily": {"*": {
        "evidence": "extraction/daily_panel_realclick.md ; shots/v_daily2_201708.png, st_daily_open.png",
        "protocols": ["CS_13781 Huoli", "CS_13786 RiChang"],
        "open": "左栏「提升/日常」(30,200)",
        "close": "面板 X",
    }},
    "rank": {"*": {
        "evidence": "extraction/phase1_v_series_panels.md §V-3 ; shots/v_rank_201453.png, v_rank2_201701.png",
        "protocols": ["CS_12901 RankPower", "CS_12931 RankLevel", "CS_12971 RankBreakdown"],
        "open": "左栏「排行」(30,400)",
        "close": "面板 X",
    }},
    "friend": {"*": {
        "evidence": "tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (13300/13321 客户端回归 ALL PASS) ; PHASE2_15_FRIEND.md",
        "protocols": ["CS_13300 FriendList", "CS_13321 FriendUpdate"],
        "open": "底部栏「好友」(150,1000)",
        "close": "面板 X",
    }},
    "hero": {"*": {
        "evidence": "extraction/ui_display_values.md §2 ; shots/uival_07_partner.png",
        "protocols": ["CS_11215 PartnerList"],
        "open": "底部栏「伙伴」(2160,1360)",
        "close": "(2210,85) X",
    }},
    "mission": {"*": {
        "evidence": "runtime_findings.md §D5.2 ; shots/uival_09_quest.png, uival_18_quest.png",
        "protocols": ["CS_12400 MissionList", "CS_12401 MissionNPC", "CS_12403 MissionCommit"],
        "open": "右侧任务追踪栏",
        "close": "面板 X",
    }},
    "battle": {"*": {
        "evidence": "runtime_findings.md §D3 (20010 mon_hp=2400, 20013 回合 hit) ; tcp.log L1169-1236",
        "protocols": ["SC_20010 BattleStart", "SC_20013 BattleRound", "SC_20020 BattleEnd"],
        "open": "挂机巡逻/任务触发",
        "close": "回合结束自动返回",
    }},
    "answer": {"*": {
        "evidence": "tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (16100~16103 客户端回归 ALL PASS) ; PHASE2_12_ANSWER_QUIZ.md",
        "protocols": ["CS_16100", "CS_16101", "CS_16102", "CS_16103"],
        "open": "活动时间内左栏答题入口",
        "close": "面板 X",
    }},
    "scratcher": {"*": {
        "evidence": "tests/1.4.11/NEW_SYSTEMS_REGRESSION.md §一 (16651/16652 ALL PASS) ; PHASE2_14_SCRATCH.md",
        "protocols": ["CS_16651", "CS_16652"],
        "open": "运营活动面板内刮刮乐入口",
        "close": "面板 X",
    }},
    "set": {"*": {
        "evidence": "shots/uival_01_more.png, v7_more_a_203916.png",
        "protocols": ["UNKNOWN (本地面板为主)"],
        "open": "底部栏「更多」(2480,1310) → 设置",
        "close": "面板 X",
    }},
    "guild": {"*": {
        "evidence": "shots/activity_guild_smoke.png ; skill_panel_located.md §三 (1960,1320 宗门面板)",
        "protocols": ["CS_183xx 公会族"],
        "open": "底部栏「宗门」(1960,1320)",
        "close": "面板 X",
    }},
    "vip": {"*": {
        "evidence": "shots/20261002_003351_close_recharge.png (误触打开后立即关闭)",
        "protocols": ["UNKNOWN (super_vip)"],
        "open": "(2110,1320) VIP 按钮",
        "close": "面板 X",
    }},
    "recharge": {"*": {
        "evidence": "shots/20261002_003351_close_recharge.png (误触)",
        "protocols": ["UNKNOWN (充值族)"],
        "open": "顶部充值入口",
        "close": "面板 X",
    }},
    "equipforge": {"*": {
        "evidence": "shots/user_assist/forge_upgrade_panel.png (用户协助)",
        "protocols": ["UNKNOWN (锻造族)"],
        "open": "底部栏「锻造」(2340,1360)",
        "close": "面板 X",
    }},
    "map": {"*": {
        "evidence": "shots/phase1_world_131336.png, v7_world_203911.png ; skill_panel_located.md §三 (世界地图 X=(2060,85))",
        "protocols": ["UNKNOWN (本地为主)"],
        "open": "主界面世界地图按钮",
        "close": "(2060,85) X",
    }},
}

# ---------------------------------------------------------------------------
# 5. 生成条目
# ---------------------------------------------------------------------------
entries = []
seen_paths = set()

def classify_support(fname):
    """返回 'panel' / 'primary' / 'support'"""
    b = fname.lower()
    if b.endswith(PANEL_SUFFIXES):
        return "panel"
    if b.endswith(("_view.luac","_ui.luac")):
        # 主 view（模块名开头）= primary；其他 = support
        return "view"
    return "support"

def make_entry(module, panel_file, related_files, system_hint, sub_key=""):
    """构造一条 UI 条目。sub_key="" 表示这是模块主条目（可命中 A 类 "*" 覆盖）。"""
    # 推断界面名
    base = panel_file.replace(".luac", "")
    # 友好名：把 _ 转空格，title-case
    ui_name = base.replace("_", " ")
    # 系统归属
    sid, sname = system_hint
    # 资源类关联：按模块名猜
    res_hint = []
    m = module.lower()
    cat_map = {
        "achieve": ["title"], "title": ["title"], "guild": ["guild"],
        "battle": ["battle"], "skill": ["skill"], "artifact": ["artifact"],
        "action": ["action","activities"], "activities": ["activities"],
        "login": ["login"], "head": ["head"], "mission": ["mission"],
    }
    for k, v in cat_map.items():
        if k in m:
            res_hint.extend(v)
    res_hint = list(dict.fromkeys(res_hint))  # dedup keep order

    # 协议初判：UNKNOWN（除非 A 类覆盖）
    protocols = ["UNKNOWN"]
    server_dep = "UNKNOWN"
    verified = "否"
    evidence = f"ui_by_module['{module}'] (apk_scan_1_4_11.json)"
    confidence = "LOW"
    difficulty = "中"
    open_cond = "UNKNOWN"
    close_way = "面板 X 按钮（通用右上角）"
    subs = []

    # 默认 B 类（模块+资源都在）
    status = "B"

    # A 类覆盖：仅当 sub_key=="" 时查 "*"；具体 panel 名永远命中
    ov = A_CLASS_OVERRIDES.get(module, {})
    hit = None
    if panel_file in ov:
        hit = ov[panel_file]
    elif sub_key == "" and "*" in ov:
        hit = ov["*"]
    if hit:
        status = "A"
        verified = "是"
        evidence = hit.get("evidence", evidence)
        protocols = hit.get("protocols", protocols)
        open_cond = hit.get("open", open_cond)
        close_way = hit.get("close", close_way)
        confidence = "HIGH"
        server_dep = "是"

    # D 类：1.3.0 有但 1.4.11 无的模块/文件
    if module in modules_only_in_130:
        status = "D"
        evidence = (f"diff: game_modules_only_in_1.3.0 含 '{module}'；"
                    f"1.4.11 ui_by_module 无此模块。"
                    f"version_compare/1.3.0/extracted/game/{module}/")
        confidence = "HIGH"
        difficulty = "难（已被移除，需从 1.3.0 反编译重建）"
        server_dep = "UNKNOWN"

    # 收集 related lua modules（basename 列表）
    related = sorted([os.path.basename(x) for x in related_files])

    # 配置表关联：扫 config_tables 里有没有同名前缀
    config_tables = s1411.get("config_tables", [])
    cfgs = [c for c in config_tables if c.startswith(f"config_{module}")]

    return OrderedDict([
        ("ui_name", ui_name),
        ("module", module),
        ("system_id", sid),
        ("system_name", sname),
        ("client_entry_luac", f"assets/src/game/{module}/{panel_file}"),
        ("related_lua_modules", related),
        ("related_res_categories", res_hint),
        ("open_condition", open_cond),
        ("close_method", close_way),
        ("sub_panels", subs),
        ("buttons_interactions", "UNKNOWN"),
        ("data_config_tables", cfgs),
        ("protocols", protocols),
        ("depends_on_server", server_dep),
        ("runtime_verified", verified),
        ("restore_difficulty", difficulty),
        ("status", status),
        ("evidence", evidence),
        ("confidence", confidence),
    ])

# 主循环
um1411 = s1411["ui_by_module"]
um130  = s130.get("ui_by_module", {})

for module, files in sorted(um1411.items()):
    # 找系统：显式表优先
    if module in MOD2SYS_EXPLICIT:
        sys_hint = MOD2SYS_EXPLICIT[module]
    else:
        sys_hint = mod2sys.get(module, ("SYS_UNKNOWN_002", "Unknown/运营活动"))
        # 再尝试按文件 basename 精确匹配
        for f in files:
            b = f.lower()
            if b in base2sys:
                sys_hint = base2sys[b]; break

    # 分类文件
    panel_files = [f for f in files if f.endswith(PANEL_SUFFIXES)]
    primary_view = None
    if not panel_files:
        # 找主 view/ctrl
        for f in files:
            b = f.lower()
            m = PRIMARY_VIEW_RE.match(b)
            if m and m.group("mod") == module:
                primary_view = f; break
        if not primary_view:
            # 兜底：任意 *_view.luac 或 *_ctrl.luac
            for f in files:
                if f.endswith(("_view.luac", "_ctrl.luac")):
                    primary_view = f; break

    if panel_files:
        # 大模块（action/hero/guild/role/dungeon/godwar/mine/peakwar/sworn/circle/yuanshen/dailysign/soulstar）
        # 按 sub-prefix 拆分
        if module in ("action", "hero", "guild", "role", "dungeon", "godwar",
                      "mine", "peakwar", "sworn", "circle", "yuanshen",
                      "dailysign", "soulstar", "equip", "friend"):
            groups = defaultdict(list)
            for f in files:
                sub, rest = split_subprefix(f)
                groups[sub].append(f)
            for sub, group_files in sorted(groups.items()):
                # 在 group_files 里挑 panel
                sub_panels = [f for f in group_files if f.endswith(PANEL_SUFFIXES)]
                if not sub_panels:
                    for f in group_files:
                        if f.endswith(("_view.luac","_ui.luac")) and not f.endswith(("_tip_view.luac","_help_view.luac","_item_view.luac","_cell_view.luac","_select_view.luac","_share_view.luac","_result_view.luac")):
                            sub_panels = [f]; break
                if not sub_panels:
                    for f in group_files:
                        if f.endswith("_ctrl.luac"):
                            sub_panels = [f]; break
                # 判断是否为主条目：panel 文件必须以 <module>_ 开头，且为 base/main/panel/view/ctrl
                is_main = False
                for pf in sub_panels:
                    if not pf.startswith(module + "_"):
                        continue
                    if pf in (f"{module}_base_panel.luac", f"{module}_main_ui.luac",
                              f"{module}_panel.luac", f"{module}_view.luac",
                              f"{module}_ctrl.luac"):
                        is_main = True
                sk = "" if is_main else "__sub__"
                for pf in sub_panels[:1]:
                    entries.append(make_entry(module, pf, group_files, sys_hint, sub_key=sk))
        else:
            # 非拆分模块：只把 `<mod>_panel.luac` 当主条目（sub_key=""），
            # 其他 *_panel.luac 当子面板（不命中 A 类 "*"）
            primary_panel = f"{module}_panel.luac"
            for pf in panel_files:
                if pf == primary_panel:
                    entries.append(make_entry(module, pf, files, sys_hint, sub_key=""))
                else:
                    entries.append(make_entry(module, pf, files, sys_hint, sub_key="__sub__"))
    elif primary_view:
        entries.append(make_entry(module, primary_view, files, sys_hint, sub_key=""))
    else:
        # 无 UI 入口文件（纯 logic）→ 跳过，但记一条备注
        entries.append(make_entry(module, files[0] if files else f"{module}_ctrl.luac", files, sys_hint, sub_key=""))

# D 类：1.3.0 独有模块（garden/jingjie/moneytree/xiulianhulu/chongzhi 等）
for mod in sorted(modules_only_in_130):
    entries.append(OrderedDict([
        ("ui_name", f"{mod} (1.3.0 已移除)"),
        ("module", mod),
        ("system_id", "SYS_ACT_009" if mod=="moneytree" else "SYS_UNKNOWN_002"),
        ("system_name", "Money Tree" if mod=="moneytree" else f"Legacy/{mod}"),
        ("client_entry_luac", f"assets/src/game/{mod}/ (1.3.0 only, 1.4.11 缺失)"),
        ("related_lua_modules", []),
        ("related_res_categories", []),
        ("open_condition", "UNKNOWN (1.3.0 入口，1.4.11 已下线)"),
        ("close_method", "N/A"),
        ("sub_panels", []),
        ("buttons_interactions", "UNKNOWN"),
        ("data_config_tables", sorted(config_only_in_130) if mod in ("garden","jingjie","moneytree","xiulianhulu","chongzhi") else []),
        ("protocols", ["UNKNOWN"]),
        ("depends_on_server", "UNKNOWN"),
        ("runtime_verified", "否"),
        ("restore_difficulty", "难（模块已从 1.4.11 移除，需从 1.3.0 APK 反向重建）"),
        ("status", "D"),
        ("evidence", f"diff.game_modules_only_in_1.3.0 含 '{mod}'；"
                     f"version_compare/1.3.0/extracted/game/{mod}/ 下有 ctrl/data/view 文件"),
        ("confidence", "HIGH"),
    ]))

# D 类：1.3.0 独有 ui_files（friend_view / garden_* / glz_* 等 18 条）
for fp in sorted(ui_files_only_in_130):
    # 跳过已经作为整模块 D 条目的
    parts = fp.split("/")
    if len(parts) >= 4:
        mod = parts[3]
        if mod in modules_only_in_130:
            continue
    entries.append(OrderedDict([
        ("ui_name", os.path.basename(fp).replace(".luac"," ").replace("_"," ")),
        ("module", parts[3] if len(parts)>=4 else "unknown"),
        ("system_id", "SYS_UNKNOWN_002"),
        ("system_name", f"Legacy file ({os.path.basename(fp)})"),
        ("client_entry_luac", fp + "  (1.3.0 only)"),
        ("related_lua_modules", [os.path.basename(fp)]),
        ("related_res_categories", []),
        ("open_condition", "UNKNOWN"),
        ("close_method", "N/A"),
        ("sub_panels", []),
        ("buttons_interactions", "UNKNOWN"),
        ("data_config_tables", []),
        ("protocols", ["UNKNOWN"]),
        ("depends_on_server", "UNKNOWN"),
        ("runtime_verified", "否"),
        ("restore_difficulty", "难（1.4.11 已移除该文件）"),
        ("status", "D"),
        ("evidence", f"diff.ui_files_only_in_1.3.0 含 '{fp}'"),
        ("confidence", "HIGH"),
    ]))

# ---------------------------------------------------------------------------
# 5b. C 类：仅图标/字符串证据（来自 client_activity_icon_registry.md 的 47 条活动名，
#     其中没有独立 lua 模块的活动 → 标 C，不得夸大为完整玩法）
# ---------------------------------------------------------------------------
# 1.4.11 已有独立模块的活动名（覆盖自 ui_by_module）
known_activity_modules = set(um1411.keys())
# 从 registry 47 条里挑"无独立模块"的
C_ACTIVITIES = [
    # (label_cn, internal_name, system_id_hint)
    ("新消耗排行榜",   "xfphb",          "SYS_COMM_001"),
    ("新充值排行榜",   "czphb",          "SYS_COMM_001"),
    ("合服首充",       "hfsc",           "SYS_ECON_010"),
    ("飞升返利礼包",   "flyUp_gift",     "SYS_ACT_013"),
    ("奖池转盘",       "jiangchi",       "SYS_ACT_004"),
    ("充值翻倍",       "charge_double",  "SYS_ACT_013"),
    ("老玩家回归",     "recruit",        "SYS_ACT_012"),
    ("合服",           "hefu",           "SYS_UNKNOWN_002"),
    ("竞猜",           "guess",          "SYS_ACT_008"),
    ("幸运转盘",       "lucky_turntable","SYS_ACT_004"),
    ("众神联赛场景",   "godwarscene",    "SYS_BATTLE_004"),
    ("FC",             "fc",             "SYS_UNKNOWN_002"),
    ("门派",           "menpai",         "SYS_ROLE_002"),
    ("跨服公会战",     "kuafu_guildwars","SYS_SOCIAL_009"),
    ("活动排行榜",     "actionrank",     "SYS_COMM_001"),
    ("投资_sec",       "invest_sec",     "SYS_ACT_003"),
    ("奖励",           "reward",         "SYS_ACT_006"),
    ("跨服仙魔",       "kuafu_xianmo",   "SYS_BATTLE_004"),
    ("运营兑换",       "yunyingduihuan", "SYS_ECON_007"),
    ("送花",           "flower",         "SYS_SOCIAL_007"),
    ("幸运宝箱",       "luckbox",        "SYS_ACT_006"),
    ("祈福墙",         "zhufuqiang",     "SYS_ACT_010"),
    ("幸运翻牌",       "xingyunfanpai",  "SYS_ACT_006"),
    ("密令",           "miling",         "SYS_UNKNOWN_002"),
    ("巨龙/神龙",      "julong",         "SYS_HIDDEN_006"),
    ("成长目标",       "target",         "SYS_QUEST_004"),
    ("一元夺宝",       "duobao",         "SYS_ACT_011"),
]
# 排除：已有独立模块的（flyup/answer/rotatetable/godwar/gangwars/guildwars/wedding/invest/peakwar/chief/treasure_plane/scratcher/diguowar/xianmo/auction(paimai)/guildsecretarea(guildcretarea)）
skip_mods = {"flyup","answer","rotatetable","godwar","gangwars","guildwars","wedding",
             "invest","peakwar","chief","treasure_plane","scratcher","diguowar",
             "xianmo","auction","guildsecretarea"}
for label, name, sid in C_ACTIVITIES:
    # 若该 name 已作为子模块出现在 1.4.11（例如 action/xxx），跳过
    entries.append(OrderedDict([
        ("ui_name", f"运营活动-{label} ({name})"),
        ("module", name),
        ("system_id", sid),
        ("system_name", "Operation Activity"),
        ("client_entry_luac", f"(无独立 luac；由 activity_ctrl.luac 按 name 分派)"),
        ("related_lua_modules", ["activity_ctrl.luac", "activity_view.luac"]),
        ("related_res_categories", ["activities", "action"]),
        ("open_condition", f"SC_10924.act_list 下发 name='{name}' 后由客户端自动打开图标（部分会自动弹窗）"),
        ("close_method", "面板 X"),
        ("sub_panels", []),
        ("buttons_interactions", "UNKNOWN"),
        ("data_config_tables", []),
        ("protocols", ["CS_10924 ActList", "CS_10925 ActHandler"]),
        ("depends_on_server", "是"),
        ("runtime_verified", "否"),
        ("restore_difficulty", "未知（仅图标/字符串证据，功能未确认）"),
        ("status", "C"),
        ("evidence", f"extraction/client_activity_icon_registry.md：活动图标注册表含 label='{label}' name='{name}'；"
                     f"1.4.11 ui_by_module 无独立 '{name}' 模块，由 activity_ctrl 按 proto#30 分派"),
        ("confidence", "MEDIUM"),
    ]))

# ---------------------------------------------------------------------------
# 6. 写出 JSON
# ---------------------------------------------------------------------------
out = OrderedDict([
    ("_meta", OrderedDict([
        ("audit_phase", "C0"),
        ("generated_by", "tools/jstm_audit/gen_ui_inventory.py"),
        ("evidence_level", "READ_ONLY_STATIC"),
        ("versions", ["1.3.0", "1.4.9", "1.4.11"]),
        ("target_version", "1.4.11"),
        ("status_definitions", {
            "A": "已实机/本地运行验证（runtime_evidence/shots, PHASE2_*.md, regression 报告）",
            "B": "ui_by_module 有模块文件 + res_categories 有资源，未运行验证",
            "C": "仅图标/字符串证据，模块缺失或极弱（本批骨架未触发，预留）",
            "D": "1.4.11 扫描中缺失（1.3.0 有而 1.4.11 无），config/UI 被移除"
        }),
        ("confidence_levels", ["VERY_LOW","LOW","MEDIUM","HIGH","VERY_HIGH"]),
    ])),
    ("total_entries", len(entries)),
    ("entries", entries),
])

# 统计
counts = defaultdict(int)
sys_counts = defaultdict(int)
for e in entries:
    counts[e["status"]] += 1
    sys_counts[e["system_id"]] += 1

out["summary_by_status"] = dict(counts)
out["summary_by_system"] = dict(sorted(sys_counts.items(), key=lambda x:-x[1]))

json_path = os.path.join(OUTDIR, "ui_inventory.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# 7. 渲染 Markdown（按系统分组）
# ---------------------------------------------------------------------------
md = []
md.append("# 《绝世唐门》PHASE C0 界面与功能清单\n")
md.append(f"> 目标版本：1.4.11 ｜ 条目数：**{len(entries)}** ｜ 生成脚本：`tools/jstm_audit/gen_ui_inventory.py`")
md.append(f"> 状态分布：**A={counts['A']} / B={counts['B']} / C={counts['C']} / D={counts['D']}**\n")
md.append("## 四类状态定义\n")
md.append("- **A 已实际验证**：有实机/本地运行证据，见 evidence 字段")
md.append("- **B 资源与模块均存在、尚未运行验证**：ui_by_module 有文件 + res_categories 有资源")
md.append("- **C 仅图标/字符串证据**：模块缺失或极弱（本批骨架未触发）")
md.append("- **D 疑似废弃/被版本替换**：1.4.11 缺失，diff 证据\n")

# 按系统分组
by_sys = defaultdict(list)
for e in entries:
    by_sys[e["system_id"]].append(e)

md.append("## 按系统分组\n")
for sid in sorted(by_sys.keys()):
    elist = by_sys[sid]
    sname = elist[0]["system_name"]
    md.append(f"### {sid} · {sname}  ({len(elist)} 条)\n")
    md.append("| 界面 | 模块 | 入口 luac | 状态 | 验证 | 协议 | 证据 |")
    md.append("|---|---|---|---|---|---|---|")
    for e in elist:
        proto = ",".join(e["protocols"][:3])
        if len(e["protocols"])>3: proto += "…"
        ev = e["evidence"].replace("|","/").replace("\n"," ")[:120]
        md.append(f"| {e['ui_name']} | {e['module']} | `{e['client_entry_luac']}` | **{e['status']}** | {e['runtime_verified']} | {proto} | {ev} |")
    md.append("")

# 未确认项清单
md.append("## 未确认项清单（status=UNKNOWN/字段空缺）\n")
unknowns = [e for e in entries if e["protocols"]==["UNKNOWN"] and e["status"]!="D"]
md.append(f"共 **{len(unknowns)}** 条协议号未确认（B 类默认）。完整列表见 json。\n")

md_path = os.path.join(OUTDIR, "ui_inventory.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))

print(f"OK: total={len(entries)} A={counts['A']} B={counts['B']} C={counts['C']} D={counts['D']}")
print(f"json: {json_path}")
print(f"md:   {md_path}")
