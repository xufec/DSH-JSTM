# 1.4.9 经验 / 等级协议矩阵（Phase E）

> **目标 APK**：`anzbao/jstm.apk`
> `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> **1.4.11（`anzbao/jstm_142165.apk`）/ `anzbao/dldlJl.apk` / `patched\*_142165*`
> 全程未被读取。**
> 字段来源：`python tools/proto_spec.py cmds <CMD>`（= `cmd_resolve_*.luac` 里
> `AutoConstruct(dir, cmd, {'<名>__<格式>', …})` 的**权威**定义）。
> 落盘证据：`analysis/1.4.9/level/_proto_spec_exp.json`。

---

## 0. 结论速览

| # | 结论 | 证据 |
|---|---|---|
| 1 | **等级/经验没有独立的"升级协议"**：`lev` 与 `exp` 由 `10301` / `10302` / `10303` 下发，客户端靠 `RoleVo.lev` 变化自行发现升级 | 见 §4.1；`main_ui.luac` proto#12 常量池 `['exp','changeExp','isUplevel','lev','power']` |
| 2 | **`exp_max` / `exp_total_nextlev` 在 `SC_10301`**（不是 10302） | `proto_spec cmds 10301` 第 23/24 字段 |
| 3 | `10302` 只带 `lev:uint16, exp:uint32` + 27 个资产字段 | 同上 |
| 4 | `10303` 带 `exp:uint32` + **24 项 `attr` 大表** + `skill_list` | 同上 |
| 5 | **4 个 CMD 是纯 `server → client` 推送**（`cmd_resolve` 里没有 `CS_` 定义）：**`10342`（盈福经验）、`10414`（所有英雄升级）、`11202`（伙伴加经验）、`11207`（伙伴升级）** | §3 方向判定 |
| 6 | `10331`（技能学习/升级）**不改等级**：请求只有 `skill_bid`，响应只有 `code,msg` | `proto_spec cmds 10331` |
| 7 | `10343` 是**角色改名**，与等级无关（任务书把它列进"角色扩展"，需澄清） | `cmd_table.json[10343] = 角色改名` |
| 8 | 本报告**逐条核实了 30 个**经验/等级相关 CMD 的字段定义与客户端处理函数（全部经 `proto_spec.py`） | §2 主表、`_proto_spec_exp.json` |
| 9 | 服务端 `mock_server.py` 当前**已实现 7 个**：`10301 / 10302 / 10303 / 10331 / 10333 / 10621 / 10921`；**未实现 23 个** | §5（**只读**该文件，未修改任何 `server/` 文件） |
| 10 | 服务端**已经在用**本阶段的等级表：`add_role_exp()` → `level_need(L) = RoleAttr[L+1].exp_max` | `mock_server.py` 的 `level_need()` / `add_role_exp()`（见 §5.2） |

---

## 1. 取证方法

| 目的 | 手段 |
|---|---|
| 消息字段名/顺序/类型 | `python tools/proto_spec.py cmds <CMD…>` |
| 客户端**处理函数**（收包） | `python tools/find_register_protocal.py <CMD…>`（扫 `RegisterProtocal(cmd, 'handler')`）+ `python tools/battle_audit.py defs <asset>` 拿 `方法名 → proto#` |
| 客户端**发送点**（发包） | 自写扫描：在含 `SendProtocal` 字符串的 proto 里找 `KSHORT <cmd>` |
| CMD 中文名 | `protocol/cmd_table.json` |
| 服务端是否实现 | **只读** `server/mock_server.py` 的 `if cmd == N:` 分支与 `EMPTY_REPLIES`（**未修改任何 `server/` 文件**） |

> 方向判定的两条独立依据：
> ① `cmd_resolve_*.luac` 里**是否存在 `CS_<cmd>` 定义**（本文的主要依据，来自 APK）；
> ② 客户端是否存在 `sender<cmd>` 方法且该方法真的调用 `SendProtocal`。
> 两者不一致的只有 `11207`：协议无 `CS_11207`，但 `hero_equip_ctrl.luac`
> 有个 `sender_11207` —— **实测该函数 `bc=1`（空函数，什么都不做）**，
> 因此仍判为"服务端 → 客户端"。

---

## 2. 主表（要求格式）

| 功能 | CMD | 方向 | 请求字段 | 响应字段 | 客户端模块/处理函数 | 服务端已实现 | 状态 |
|---|---|---|---|---|---|---|---|
| 角色基础信息（含 **`lev`/`exp_max`/`exp_total_nextlev`/`attr_point`**） | **10301** | C→S 空包 / S→C | *（空消息）* | `rid:u32, srv_id:str, name:str, **lev:u16**, is_vip:u8, vip_lev:u8, sex:u8, career:u16, face_id:u16, cur_title:u16, ntm_title:u32, gid:u32, gsrv_id:str, position:u8, gname:str, mspd:u16, volume/store_volume/store_partner_volume/volume_open/store_volume_open/store_partner_volume_open:u8, **exp_max:u32**, **exp_total_nextlev:u32**, **attr_point:u16**, profit_exp:u32, marry_state:u8, spouse_name:str, head_bid:u32, chat_bubble:u32, skill_list:T{bid:u32}, buffs:T{bid:u32,duration:u32,count:u8,effect:Dsc10301effect}, animate_res:T{ant_id:u16,ant_val:str,ent_lev:u8,dis_method:u8}, misc_uint8/16/32/str:T, spouse_rid:u32, spouse_srv_id:str, insight_status:u8, jid:u32, j_srv_id:str, jlev:u8, j_title:str` | `role_ctrl.luac` proto#4 bc#2 → **`rgp_hander10301`（proto#11，bc=152）** → `NavData.analyseLevel()`（导航按钮，**不是**经验逻辑） | **已实现** `build_10301()` | **已验证** |
| 角色资产 / 经验 | **10302** | C→S 空包 / S→C | *（空消息）* | **`lev:u16, exp:u32`**, `gold:u32, gold_acc:u32, coin:u32, sinew:u32, experience:u32, coupon:u32, vitality:u32, guild_contrib:u32, practice_exp:u32, tower_cent:u32, arena_cent:u32, integral:u32, cash_coupon:u32, dan_point:u32, guild_active:u32, marriage:u32, course:u32, vip_exp:u32, lingshi:u32, peak_point:u32, black_soul:u32, lottery_point:u32, boss_point:u32, partner_shenqi_point:u32, jiebai_cent:u32, rune_exp:u32, rune_chip:u32` | `role_ctrl.luac` proto#4 bc#7 → **`rgp_hander10302`（proto#13）** → `RoleData.initRoleAssetsData()` | **已实现** | **已验证** |
| 自己角色属性大表（含 `attr` 24 项 + `exp`） | **10303** | C→S 空包 / S→C | *（空消息）* | `rid:u32, srv_id:str, name:str, lev:u16, is_vip:u8, vip_lev:u8, sex:u8, career:u16, volume…:u8×6, attr_point:u16, skill_list:T{bid:u32}, power:u32, **exp:u32**, gold:u32, coin:u32, gold_acc:u32, sinew:u32, experience:u32, coupon:u32, vitality:u32, guild_contrib:u32, practice_exp:u32, tower_cent:u32, arena_cent:u32, **attr:T{strength:u16,intellect:u16,armor:u16,constiution:u16,atk_s:u32,atk_p:u32,def_s:u32,def_p:u32,hp_max:u32,atk_speed:u32,hit:u32,dodge:u32,crit:u32,tenacity:u32,red_def_s:u32,red_def_p:u32,atk_abs:u32,def_abs:u32,reduce:u32,hurt:u32,hit_rate_show:u32,dodge_rate_show:u32,crit_rate_show:u32,tenacity_rate_show:u32}**, mspd:u16, animate_res:T{…}, vip_exp:u32, jiebai_title:str, jiebai_lev:u8` | `role_ctrl.luac` proto#4 bc#12 → **`rgp_hander10303`（proto#15）** → `RoleData.updateRoleAllAttr()` | **已实现** `build_10303()` | **已验证** |
| 查看**他人**角色面板 | **10304** | C→S / S→C | `rid:u32, srv_id:str` | 同 `SC_10303`（结构完全一致） | `role_ctrl` proto#16 `sender10304` / 收包 **`rgp_hander10304`（proto#17）** | **未实现** | 已确认 |
| 角色资产**增量**更新（某几项） | **10305** | C→S 空包 / S→C | *（空消息）* | `assets:T{label:u8, val:u32}` | `role_ctrl` proto#18 `sender10305` / **`rgp_hander10305`（proto#19）** | **未实现** | 已确认 |
| 角色**战斗属性**（仅 `attr`+`mspd`+`power`） | **10306** | C→S 空包 / S→C | *（空消息）* | `attr:T{…24 项，其中 **`atk_abs`/`def_abs`/`reduce`/`hurt` 是 u16**…}, mspd:u16, power:u32` | `role_ctrl` proto#20 `sender10306` / **`rgp_hander10306`（proto#21）** | **未实现** | 已确认 |
| 购买体力 | **10320** | C→S 空包 / S→C | *（空消息）* | `code:u8, msg:str, times:u8` | `role_ctrl` proto#22 **`getStrengthResult`**（内含 `SendProtocal(10320)`；**没有** `sender10320` 这个方法）/ **`rgp_hander10320`（proto#23）** | **未实现** | 已确认 |
| 购买体力面板 | **10321** | C→S 空包 / S→C | *（空消息）* | `times:u8` | `role_ctrl` proto#24 **`getStrengthCountResult`**（内含发送点；**没有** `sender10321`）/ **`rgp_hander10321`（proto#25）** | **未实现** | 已确认 |
| 角色改名（改名结果） | **10324** | C→S / S→C | `name:str, is_rename:u8` | `code:u8, msg:str, name:str` | `role_ctrl` proto#26 `sender10324` / **`rgp_hander10324`（proto#27）** | **未实现** | 已确认 |
| **增加能力点**（与 `attr_point` 直接相关） | **10328** | C→S / S→C | `assets:T{label:u16, val:u16}` | `code:u8, msg:str, **point:u16**` | `role_ctrl` proto#28 `sender10328` / **`rgp_hander10328`（proto#29）** | **未实现** | 已确认 |
| 技能学习 / 技能升级（**不含等级**） | **10331** | C→S / S→C | `skill_bid:u32` | `code:u8, msg:str` | `skill_ctrl.luac` proto#4 bc#2 → **`learnHandler`**；发送点 `skill_ctrl` proto#14 | **已实现**（固定回 `code=0,msg=''`） | 已确认 |
| 一键学习 / 升级 | **10333** | C→S 空包 / S→C | *（空消息）* | `code:u8, msg:str` | `skill_ctrl.luac` proto#4 bc#12 → **`oneKeyHandler`**（发送点 proto#17） | **已实现**（固定回 `code=0,msg=''`） | 已确认 |
| 一键学习升级（铜钱消耗） | **10334** | C→S 空包 / S→C | *（空消息）* | `coin:u32` | `skill_ctrl.luac` proto#4 bc#27 → **`handleOneKeyMoney`** | **未实现** | 已确认 |
| **盈福经验更新** | **10342** | **仅 S→C** | *（无 `CS_10342` 定义；客户端无发送点）* | **`profit_exp:u32`** | `role_ctrl.luac` proto#4 bc#127 → **`hander10342`（proto#5）** → `RoleVo:setRoleAttribute('profit_exp', v)` | **未实现** | 已确认 |
| 角色改名（发起） | **10343** | C→S / S→C | `new_name:str, auto_buy:u8` | `code:u8, msg:str` | `role_ctrl` proto#6 `sender10343` / **`hander10343`（proto#7）** | **未实现** | 已确认 |
| 客户端测试包 | **10390** | C→S / S→C | `msg:str, len:u32` | `msg:str` | `common/function_test.luac` proto#45（发送点） | **未实现** | 待分析 |
| 客户端动态调用 | **10391** | C→S / S→C | `msg:str` | `type:u8, data:str` | `role_ctrl` proto#111 `hander10391`（发送点 proto#111） | **未实现** | 待分析 |
| GM 命令 | **10399** | C→S / S→C | `msg:str` | `code:u8, msg:str` | `common/gm_cmd.luac` proto#8/12/37/47（发送点）；`role_ctrl` → `receiveGmError`（proto#45） | **未实现** | 已确认 |
| **英雄加经验** | **10409** | C→S / S→C | `hero_bid:u32` | `hero_bid:u32, exp:u32` | 收包 `hero_ctrl.luac` proto#2 bc#42 → **`updateHeroExpValue`（proto#20）**；发送点 `hero_ctrl` proto#19 **`addHeroExpByBid`** | **未实现** | 已确认 |
| **所有英雄升级** | **10414** | **仅 S→C** | *（无 `CS_10414`；客户端无发送点）* | `lev:u8` | `hero_ctrl.luac` proto#2 bc#62 → **`hander10414`（proto#26）** | **未实现** | 已确认 |
| 英雄技能升级 | **10424** | C→S / S→C | `bid:u32, skill_bid:u32` | `code:u8, msg:str, bid:u32, skill_bid:u32, new_skill_bid:u32` | `hero_ctrl` proto#39 `sender10424` / **`hander10424`（proto#40）** | **未实现** | 已确认 |
| 修炼技能列表（世界技能经验） | **10621** | C→S 空包 / S→C | *（空消息）* | `world_lev:u16, skill_list:T{bid:u32, exp:u32}` | `skill_ctrl.luac` proto#4 bc#17 → **`handleTrainSkillList`**（发送点 proto#16） | **已实现**（空 `skill_list`） | 已确认 |
| **世界等级** | **10921** | C→S 空包 / S→C | *（空消息）* | `world_lev:u8, next:u32, exp:u16, dec_exp:u16, open_day:u16` | `main_ctrl.luac` proto#1 bc#17 → **`worldLevHandler`**（发送点 proto#7） | **已实现**（`EMPTY_REPLIES` 硬编码 `u8 1 + u32 0 + u16 0×3`） | 已确认 |
| 离线经验开启 | **10933** | C→S 空包 / S→C | *（空消息）* | `code:u8, msg:str` | `automate_ctrl.luac` proto#9 bc#27 → **`hander10933`** | **未实现** | 已确认 |
| 离线经验关闭 | **10934** | C→S 空包 / S→C | *（空消息）* | `code:u8, msg:str` | `automate_ctrl.luac` proto#9 bc#32 → **`hander10934`** | **未实现** | 已确认 |
| **伙伴加经验** | **11202** | **仅 S→C** | *（无 `CS_11202`；客户端无发送点）* | `id:u32, exp:u32` | `hero_equip_ctrl.luac` proto#10 bc#12 → **`hander_11202`（proto#17）** | **未实现** | 已确认 |
| **伙伴升级** | **11207** | **仅 S→C** | *（无 `CS_11207`；`sender_11207` 是 bc=1 的空函数）* | `lev_list:T{id:u32, lev:u8}` | `hero_equip_ctrl.luac` proto#10 bc#37 → **`hander_11207`（proto#27）** | **未实现** | 已确认 |
| 勇气值 / 魅力值 | **13331** | C→S 空包 / S→C | *（空消息）* | `courage:u32, charm:u32, courage_rank:u8, charm_rank:u8` | `role_ctrl` proto#30 `sender13331` / **`rgp_hander13331`（proto#31）** | **未实现** | 已确认 |
| **场景累计经验更新** | **17518** | **仅 S→C** | *（无 `CS_17518`；客户端无发送点）* | `exp:u32, hero_exp:u32, coin:u32` | `guildwars_ctrl.luac` proto#5 bc#87 → **`hander17518`** | **未实现** | 已确认 |
| 法宝加经验 | **18906** | C→S / S→C | `bid:u32, type:u8, value:u16` | `result:u8, bid:u32, pre_level:u16, post_level:u16, msg:str` | `role_ctrl.luac` proto#4 bc#177 → **`hander18906`** | **未实现** | 已确认 |

**已确认 CMD 数：30 个**（全部经 `proto_spec.py` 取出字段定义；
其中 4 个判定为纯服务端推送）。`cmd_table.json` 里含"经验/等级/升级"关键词的
CMD 共 **55** 个，本表覆盖其中与**角色/英雄/伙伴等级与经验**直接相关的 30 个；
其余 25 个属装备/宝石/帮会/魔灵/VIP/排行榜等其它系统，不在本阶段范围。

---

## 3. 方向判定明细

| CMD | `CS_` 定义 | 客户端 `SendProtocal` 发送点 | 判定 |
|---|---|---|---|
| 10301/10302/10303 | 有（空消息） | `sender10301/10302/10303` | 双向（请求空包，应答数据） |
| 10304 | 有 | `sender10304`（proto#16） | 双向 |
| 10305/10306/10324/10328 | 有（10305/10306 为空消息） | `sender10305/10306/10324/10328`（proto#18/20/26/28） | 双向 |
| 10320 | 有（空） | **无 `sender10320`**；发送点在 `getStrengthResult`（proto#22） | 双向 |
| 10321 | 有（空） | **无 `sender10321`**；发送点在 `getStrengthCountResult`（proto#24） | 双向 |
| 10331/10333 | 有 | `skill_ctrl` proto#14 / proto#17 | 双向 |
| 10334 | 有（空） | 未扫到发送点 | **待分析** |
| **10342** | **无** | **无** | **纯 S→C 推送** |
| 10343 / 10390 / 10391 / 10399 | 有 | `sender10343` / `function_test` proto#45 / `hander10391` 同 proto / `gm_cmd` proto#8,12,37,47 | 双向 |
| 10409 | 有 | `hero_ctrl` proto#19 `addHeroExpByBid` | 双向 |
| **10414** | **无** | **无** | **纯 S→C 推送** |
| 10424 | 有 | `sender10424`（proto#39） | 双向 |
| 10621 / 10921 / 13331 | 有（空） | `skill_ctrl` proto#16 / `main_ctrl` proto#7 / `role_ctrl` proto#30 | 双向 |
| 10933 / 10934 | 有（空） | 未扫到发送点 | **待分析** |
| **11202** | **无** | **无** | **纯 S→C 推送** |
| **11207** | **无** | `sender_11207` 存在但 **bc=1（空函数）** | **纯 S→C 推送** |
| **17518** | **无** | **无** | **纯 S→C 推送** |
| 18906 | 有 | 未扫到发送点（`cmd_table` 有中文名） | **待分析** |

---

## 4. 等级/经验的关键协议语义

### 4.1 升级是"客户端自己发现的"，没有升级协议

- `SC_10301` 里的 `lev:u16` 是**服务端权威**；
- `main_ui.luac` proto#16（`MainUI:changeExp`）用
  `Config.RoleAttr[self.role.lev + 1].exp_max` 当经验条分母（详见
  `exp_table.md` §4.1）；
- `main_ui.luac` proto#12 的常量池是
  `['exp', 'changeExp', 'isUplevel', 'lev', 'power']`，即**属性变更回调**；
- `main_ui.luac` proto#18（`MainUI:updateExp`）里有
  `isUplevel` / `isOnlevel` 两段式动画（先填满 → 归零 → 再填到新值）。

⇒ **服务端只要把 `lev` / `exp` 改对并下发 `SC_10301`/`SC_10302`/`SC_10303`，
客户端就会自己刷新经验条并播升级表现，不需要新增协议。**

### 4.2 `10301` vs `10302` vs `10303` 的分工（容易踩坑）

| 字段 | 10301 | 10302 | 10303 |
|---|---|---|---|
| `lev` | **有**（u16） | **有**（u16） | **有**（u16） |
| `exp` | **无** | **有**（u32） | **有**（u32） |
| `exp_max` | **有**（u32） | 无 | 无 |
| `exp_total_nextlev` | **有**（u32） | 无 | 无 |
| `attr_point` | **有**（u16） | 无 | **有**（u16） |
| `attr` 大表 | 无 | 无 | **有**（24 项） |
| `power` | 无 | 无 | **有** |

⇒ **`exp_max` 只在 10301 里**。若服务端只推 10302，客户端经验条拿到的
`exp_max` 就是 `nil`（`role_attr_msg.luac` proto#9 会
`updateExpBar(exp, nil)`）。

### 4.3 `10331` / `10333` 与等级无关

`CS_10331{skill_bid:u32}` → `SC_10331{code:u8, msg:str}`；
`CS_10333`（空）→ `SC_10333{code:u8, msg:str}`。
**两边的字段里都没有 `lev`/`exp`**，所以"技能学习/升级"不会顺带改角色等级。

### 4.4 `10342`（盈福经验）

`SC_10342{profit_exp:u32}` 是**单字段推送**；客户端 `hander10342`
把它写进 `RoleVo`（`setRoleAttribute('profit_exp', v)`），
与 `SC_10301.profit_exp:u32` 同源。**没有 `CS_10342`，也没有客户端发送点**
⇒ 必须由服务端主动推。服务端当前**未实现**（`profit_exp` 只在
`ROLE_DEFAULTS` 里为 0，靠 10301 带出去）。

---

## 5. 服务端实现现状（只读 `server/mock_server.py`，未修改）

> ⚠ `server/mock_server.py` 在本阶段**被另一条并行任务持续编辑**
> （本报告两次读取之间它从 2860 行长到 2887 行），**因此本报告只引用
> 函数名 / 分支条件，不引用行号**。`if cmd == N:` 分支集合与
> `EMPTY_REPLIES` 键集合在本次核对时如下（`Get-Item` 时间戳 2026/9/17 20:30:09）。

### 5.1 已实现（7 个）

| CMD | 实现位置（函数/结构名） | 说明 |
|---|---|---|
| 10301 | `build_10301()` + `if cmd == 10301:` | 45 字段逐字段照写；`exp_max` / `exp_total_nextlev` / `attr_point` 由 `role_state()` **实时按等级表算** |
| 10302 | `if cmd == 10302:` | 只写 `lev/exp/gold/gold_acc` 4 字段（**`SC_10302` 里还有另外 25 个资产字段，服务端未写**；这是本阶段之前就存在的简化） |
| 10303 | `build_10303()` + `if cmd == 10303:` | 资产 14 项 + `attr` 24 项 + `skill_list`；`attr` 用"计数 + 1 行"编码（注释里有实测依据） |
| 10331 | `if cmd == 10331:` | 固定 `code=0, msg=''` |
| 10333 | `if cmd == 10333:` | 固定 `code=0, msg=''` |
| 10621 | `if cmd == 10621:` | `world_lev=1` + 空 `skill_list` |
| 10921 | `EMPTY_REPLIES[10921]` | `u8 1 + u32 0 + u16 0 + u16 0 + u16 0` |

### 5.2 ★ 等级表已接入服务端

```
★ Phase E：角色等级表 Config.RoleAttr（1.4.9，200 级）
    LEVEL_TABLE_PATH = analysis/1.4.9/level/level_table.json
    level_table() / max_lev() / level_row(lev)
    level_need(L)        = RoleAttr[L+1].exp_max    ← 与客户端 main_ui#16 完全对齐
    level_next_total(L)  = RoleAttr[L+1].exp_total  ← 对应 SC_10301.exp_total_nextlev
    level_attr_point(L)  = RoleAttr[L+1].attr_point

role_state(cfg) 末尾（★ Phase E）：
    st['exp_max']           = level_need(_lev) or 0
    st['exp_total_nextlev'] = level_next_total(_lev)
    st['attr_point']        = level_attr_point(_lev)
    —— 覆盖 ROLE_DEFAULTS 里写死的 100/100

add_role_exp(cfg, rid, amount, apply_attr_growth=True)：
    while lev < max_lev():
        need = level_need(lev)
        if not need or exp < need: break
        exp -= need; lev += 1
    落盘：lev -> roles.level；exp -> role_assets.exp（并同步 roles.exp）

apply_level_attr_growth(rid, ups)：
    LEVEL_ATTR_GROWTH 是**显式标注的 IMPLEMENTATION_FALLBACK / TEST_ONLY**
    （注释写明"这些增量不是原版数值（APK 内无逐级属性表）"）
```

⇒ **升级判定口径与客户端一致**：处于 L 级 → 需要 `RoleAttr[L+1].exp_max`。
这正是本阶段 `exp_table.md` §4 的结论在服务端的落地。

### 5.3 未实现（23 个）

`10304, 10305, 10306, 10320, 10321, 10324, 10328, 10334, 10342, 10343,
10390, 10391, 10399, 10409, 10414, 10424, 10933, 10934, 11202, 11207,
13331, 17518, 18906`

其中与本阶段（经验/等级）**直接相关**、建议优先补的：

| 优先级 | CMD | 为什么 |
|---|---|---|
| 中 | **10342** | 盈福经验是**服务端主动推**的单字段包；不推则客户端 `profit_exp` 永远为 0 |
| 中 | **10305** | 资产增量更新（`assets:T{label:u8,val:u32}`），比每次重推 10302 更贴近原版 |
| 低 | **10306** | 只推 `attr`+`mspd`+`power`，升级后刷新属性面板的轻量包（注意 `atk_abs` 等 4 项是 u16） |
| 低 | **10409 / 10414 / 11202 / 11207 / 17518** | 英雄/伙伴/场景经验；与"角色等级"是不同系统，本阶段可暂不做 |
| 低 | **10328** | "增加能力点"（`point:u16`）—— 与 `attr_point` 配套，但 1.4.9 的 `RoleAttr.attr_point` 全为 0，没有配置依据 |

---

## 6. 未能确定（UNKNOWN）

| # | 项 | 依据现状 | 会怎样定案 |
|---|---|---|---|
| 1 | `10342` 的 `profit_exp` 计算规则（是否按时间累积） | 客户端只把它写进 `RoleVo`，不含算法 | 真机长时间挂机观察 `SC_10342` 推送节奏；或抓原版包 |
| 2 | `10334 / 10933 / 10934 / 18906` 的**发送方向** | `CS_` 定义存在，但未扫到 `SendProtocal(该 cmd)` 的发送点（**处理函数已全部定位**，见 §2） | 扩大发送点扫描（含 `SendProtocal` 别名）+ 逐 proto 反汇编 |
| 3 | "升级后属性如何成长" | APK 内无逐级属性表（`exp_table.md` §8.3/§10.1） | 只能抓原版服务端包对比，或采用显式标注的 fallback |
| 4 | `SC_10302` 服务端当前只写 4 字段是否会影响某面板 | 需要对比其余 25 个资产字段的显示方 | 真机逐面板核对（`role_attr_msg` / 资产面板） |
| 5 | `18906`（法宝加经验）与角色等级是否间接相关 | 字段里有 `pre_level/post_level`（**法宝**等级，非角色等级） | 读法宝模块的 `hander18906` |
| 6 | `Config.Reward`（`{30:{1..7:…}}`）的触发协议 | 与等级无关（键不是等级），但系统归属未定 | 在 `cmd_resolve_*` 里搜索带 `reward` 的 CMD |

---

## 附：本报告用到的证据文件

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/level/_proto_spec_exp.json` | 上表 30 个 CMD 的 `CS_`/`SC_` 字段名+类型+来源 proto# |
| `analysis/1.4.9/level/_flow_dis.py` | 带跳转解析的反汇编器（用于 `main_ui` proto#12/#16/#18 的还原） |
| `analysis/1.4.9/level/_role_ctrl_defs.txt` | `role_ctrl.luac` 方法名 → proto# 全表 |
| `analysis/1.4.9/level/exp_table.md` | 等级/经验表本体（Phase E 主交付物） |
| `protocol/cmd_table.json` | CMD 中文名（55 条含"经验/等级/升级"） |
