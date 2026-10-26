# -*- coding: utf-8 -*-
"""生成 **缺口判定文档**：把 `cmd_unknown --by-system` 的每条未实现命令
按"是否有配置/DB 出处"自动分成三类，并给出结论。

## 为什么需要

`gap_worklist` 只告诉我们"哪些命令只回默认响应"，但**不告诉我们"为什么没做"**。
追到第 4 轮后出现明显的**收益递减**：top 缺口里越来越多是
① 社交域（本服只有 1 个角色 ⇒ 空即真话）、② 玩家没有该物品（⇒ 与默认响应等价）、
③ 语义未取证 / 无配置源。

⇒ 本工具**自动分类**，产出 `analysis/1.4.9/gap_verdicts.md`：
   · **A 类**：已实现（在服务端有专用分支）
   · **B 类**：空即真话（判据：命令落在已知的社交/单角色系统里）
   · **C 类**：需人工判定（其余）—— 附上"可能的配置源"线索

用法： python tools/gap_verdicts.py
"""
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

# 已知的"社交/单角色"系统 ⇒ 空即真话（判据：本服 `roles` 只有 1 个角色）
SOCIAL_SYS = {
    'circle': '朋友圈（要有好友）',
    'team': '队伍（要有多人）',
    'friend': '好友（要有他人）',
    'friendback': '好友召回（要有他人）',
    'market': '摆摊交易（要有买家）',
    'wedding': '婚宴（要有配偶）',
    'guild_race': '宗门竞速（要有宗门）',
    'guild_secret_area': '宗门秘境（要有宗门）',
    'guild': '宗门（要有多人）',
    'chat': '聊天（要有他人）',
}

# ★ R119b：**按命令号**的判定（系统名归不上来时用）
CMD_VERDICT = {
    10999: ('**A′ 正确行为**', 'CS-only（`fields.json` 只有 CS 无 SC）⇒ 客户端上报日志，'
                              '服务端**不应答才是对的**'),
    11400: ('**B 空即真话**', '称号；玩家没有称号'),
    13201: ('**B 空即真话**', '队伍信息；**1 个角色** ⇒ 没有队伍'),
    13224: ('**B 空即真话**', '邀请入队；需要**别人**才能组队'),
    13343: ('**B 空即真话**', '群发给好友；需要好友'),
    18300: ('**B 空即真话**', '婚宴；需要配偶'),
    15200: ('**B 空即真话**', 'NPC；`SC{code,msg}` 两字段，action 语义未取证 ⇒ 不猜'),
    19100: ('**B 与默认响应等价**', '光环（`halo`）；SC 结构与 `20800` 座椅**完全相同**，'
                              '玩家未获得光环 ⇒ 全 0 + 空表 = 与默认响应字节等价'),
    15506: ('**A 已实现**', '坐骑幸运值；取 `role_ride.jie_luck`（与 `15501` 同一套）'),
    12971: ('**A 已实现**', '战力对比；本服只有自己 ⇒ 回真实 `role_power`（分项未取证=0）'),
    10805: ('**A 已实现**', '邮件操作应答（`id` 原样回 + `code=1`）'),
    10206: ('**A 已实现**', '寻路/传送应答（`code=1`，不改状态）'),
    13741: ('**B 与默认响应等价**', '建筑技能（`lev`/`learn_list` 均为玩家态，初始 0）'),
    19600: ('**B 无配置源**', '每日签到的 `list` 档位**找不到配置表** ⇒ 空即真话'),
    15204: ('**B 语义未取证**', 'NPC（`SC{num:u8, gold:u8}` 两个 u8，语义不明 ⇒ 不猜）'),
    15700: ('**B 与默认响应等价**', '神器（`shenqi_list` 是玩家拥有的神器，初始为空）'),
    17001: ('**B 无 DB 源**', '关卡（`dungeon_progress` 只有副本设置、**无关卡进度**）'),
    # ---- R120–R125：以下都由"未开放/等价默认响应"改成了**真功能**
    20800: ('**A 已实现**', '座椅；R125 建了 `role_chair` + `/DSH_ADMIN/chair` ⇒ **读真实 DB**'),
    11600: ('**A 已实现**', '翅膀；R125 建了 `role_wing` + `/DSH_ADMIN/wing` ⇒ **读真实 DB**'),
    18600: ('**A 已实现**', '坐骑地图态；读 `role_ride` ⇒ 有坐骑才 `map_state=1`'),
    13500: ('**A 已实现**', '建宗门；**真落** `role_guild`（重名/已有都拒）'),
    13803: ('**A 已实现**', '摆摊开关；**真落** `role_market.on_state`'),
    13020: ('**A 已实现**', '进镇魔塔；**真落** `dungeon_progress(dung_enter)`'),
    10343: ('**A 已实现**', '改名；**真改** `roles.name`'),
    10504: ('**A 已实现**', '出售；**真删**物品 + 按 `item_config.value` 入账'),
    12821: ('**A 已实现**', '商城购买；**真扣**金币 + **真给**物品（`config_mall.MallGoods`）'),
    10930: ('**A 已实现**', '双倍经验；与 `10932` 同族（本服无双倍 ⇒ 0，真话）'),
    13342: ('**A 已实现**', '拉取好友消息；`SC` 只有一个 `code` ⇒ `code=1`（**空 ≠ 失败**）'),
    13359: ('**A 已实现**', '**发**朋友圈；**真存** `role_moments`（写操作不需要好友）'),
    12762: ('**A 已实现**', '**发**言；**真存** `role_chat`（写操作不需要他人）'),
    30201: ('**A 已实现**', '宗门秘境；**有宗门才** `code=1`（读 `role_guild`）'),
}


def is_cs_only(fields, cmd):
    """`fields.json` 里只有 CS、没有 SC ⇒ 客户端上报，服务端不该答。"""
    d = {v.get('dir') for k, v in fields.items() if str(v.get('cmd')) == str(cmd)}
    return 'cs' in d and 'sc' not in d


# 已知的"玩家没有该物 ⇒ 与默认响应等价"的系统
NORES_SYS = {
    'wing': '翅膀（玩家未获得）',
    'chair': '座椅（玩家未获得）',
    'qifu': '祈福（未参与）',
    'artifact': '神器（玩家未获得）',
    'beast': '魂兽（未获得）',
    'vip': 'VIP 道具（无 VIP）',
    'yuanshen': '元神（未获得）',
    'soulstar': '魂星（`21410` 与默认响应等价）',
    'mount': '坐骑（未获得）',
    'boss': 'BOSS（无击杀记录）',
    'title': '称号（未获得）',
    'backpack': '背包（`10504` 出售，无操作）',
    'shop': '商店（`12821` 无购买）',
    'demontower': '镇魔塔（未参与）',
    'tower': '爬塔（未参与）',
    'battlevideo': '战斗录像（无记录）',
    'chief': '首席（未参与）',
    'chongzhi': '充值（未充值）',
    'tree': '摇钱树/膜拜（无 `config_tree` 配置）',
    'build': '建筑（`lev`/`learn_list` 均为玩家态，初始为 0）',
    'npc': 'NPC（`15204` 仅 2 个 u8，语义未取证）',
    'action': '活动（`16664` 缺 `bid` 源；`16602` 缺 `holiday_list.bid` 源）',
    'role': '角色（`10343`/`13331`/`18900` 为玩家态）',
    'dungeon': '副本（`21306` 回空 `list` 当前安全）',
    'dailysign': '签到（`19600` 的 `list` 档位无配置源）',
    'mission': '任务（`19500` 语义未取证）',
    'automate': '自动挂机（`10930` 未参与）',
}


def main():
    import importlib.util
    spec = importlib.util.spec_from_file_location('cu', os.path.join(ROOT, 'tools', 'cmd_unknown.py'))
    # 直接复用其内部函数（避免重跑一遍 APK 扫描：读已经产出的 md 更省）
    _FIELDS = json.load(open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8'))
    src = open(os.path.join(ROOT, 'server', 'mock_server.py'), encoding='utf-8').read()
    s2 = re.sub(r'#[^\n]*', '', src)
    m = re.search(r'_GENERIC_DEFAULT_CMDS\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    gen = set(int(x) for x in re.findall(r'\b\d{4,5}\b', m.group(1))) if m else set()
    m2 = re.search(r'_UNSUPPORTED_ACTION_CMDS\s*=\s*frozenset\(\[(.*?)\]\)', s2, re.S)
    uns = set(int(x) for x in re.findall(r'\b\d{4,5}\b', m2.group(1))) if m2 else set()
    eq = set(int(x) for x in re.findall(r'if cmd == (\d{4,5}):', s2))
    for mm in re.finditer(r'if cmd in \(([^)]*)\):', s2):
        for x in re.findall(r'\d{4,5}', mm.group(1)):
            eq.add(int(x))

    # 读 `_unknown_by_system.md`（R102 生成的按系统表）
    p = os.path.join(ROOT, 'analysis', '1.4.9', '_unknown_by_system.md')
    rows = []
    if os.path.exists(p):
        for ln in open(p, encoding='utf-8'):
            mm = re.match(r'\|\s*\*\*(.+?)\*\*\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|', ln)
            if mm:
                rows.append((mm.group(1), int(mm.group(2)), int(mm.group(3)), int(mm.group(4)),
                             [int(x) for x in re.findall(r'`(\d+)`', mm.group(5))]))

    lines = ['# 缺口判定总表（自动生成）', '',
             '> 由 `tools/gap_verdicts.py` 生成。目的：把"未实现"从**待办**变成**已判定** ——',
             '> 每条都必须能回答"为什么没做"，而不是悬着。', '',
             '| 系统 | 未实现 | 真机次数 | 判定 | 依据 |', '|---|---|---|---|---|']
    n_a = n_b = n_c = 0
    for name, cnt, _dflt, sent, cmds in rows:
        # ★ R119b：先查"按命令号"的判定；再查 CS-only（自动检测）
        hit = None
        for c in cmds:
            if c in CMD_VERDICT:
                hit = CMD_VERDICT[c]
                break
        if hit is None:
            for c in cmds:
                if is_cs_only(_FIELDS, c):
                    hit = ('**A′ 正确行为**', 'CS-only ⇒ 服务端不应答才是对的')
                    break
        if hit is not None:
            verdict, why = hit
        elif name in SOCIAL_SYS:
            verdict, why = '**B 空即真话**', SOCIAL_SYS[name]
            n_b += cnt
        elif name in NORES_SYS:
            verdict, why = '**B 与默认响应等价**', NORES_SYS[name]
            n_b += cnt
        else:
            verdict, why = '**C 需人工判定**', '（未归类，见命令号）'
            n_c += cnt
        lines.append('| **%s** | %d | %d | %s | %s |'
                     % (name, cnt, sent, verdict, why))

    lines += ['', '## 统计', '',
              '- **B 类（有依据地不做）**：%d 条 —— 判据是"本服只有 1 个角色"或"玩家没有该物"' % n_b,
              '- **C 类（需人工判定）**：%d 条' % n_c,
              '- **已实现（A 类）**：服务端现有 **%d** 条专用分支' % len(eq),
              '', '## 判据说明', '',
              '- **B1 社交域**：`roles` 表只有 **1 个角色** ⇒ 好友/队伍/摆摊/婚宴/宗门 的"空"是**事实**，不是缺陷。',
              '- **B2 玩家没有该物**：命令回的是"玩家拥有的 X 的列表/状态"，而玩家尚未获得 ⇒',
              '  回 0/空表与"通用默认响应"**字节等价** ⇒ 实现它**零增量**（R105 已论证）。',
              '- **C 类**：要么配置源未找到、要么字段语义未取证 ⇒ 按纪律**不猜**，留待单独取证。']

    out = os.path.join(ROOT, 'analysis', '1.4.9', 'gap_verdicts.md')
    open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
    print('已写出 %s' % out)
    print('  B 类（有依据地不做）：%d 条' % n_b)
    print('  C 类（需人工判定）：%d 条' % n_c)
    print('  A 类（已实现专用分支）：%d 条' % len(eq))


if __name__ == '__main__':
    main()
