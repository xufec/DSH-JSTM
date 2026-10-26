# 角色矩阵（R7）—— 五参考项目 × JSTM 角色/属性系统对照

> **本文档闭环 `R1_SUPPLEMENT.md` §六 未做项 ②「`comparison/` 其余矩阵未单独出文件 → `role_matrix`」。**
> 依据：`jstm_1.4.9/role_protocol.md`（42 条 CMD）+ `analysis/1.4.9/level/_attr.json`（**属性总表 64 项**）
> + `analysis/1.4.9/role/*.md` + `server/mock_server.py` 实测 + `survive/role.md` + `yzxy/role.md` + `chivalrousman/battle.md`（我方）+ `kongkongxiyou/reuse_candidates.md`。
> 标注：【已确认】/【待验证】/【未知】；未读到的一律写「未读到」。
> **本文件只读，未修改 `server/` 任何文件。**
>
> ⚠ **时效声明**：JSTM 行号/CMD 数取自本次读取快照（`server/` 正被其他 agent 活跃开发）。引用请以 CMD 号 / 列名 / 函数名定位。

---

## 一、结论速览（6 方对照）

| 维度 | **Survive** | **YZXY / CXEngine** | **大圣归来** | **侠客行** | **空空西游** | **JSTM 现状** |
|---|---|---|---|---|---|---|
| 角色属性项数 | **32 项**（含 `endidx` 哨兵） | **118 项 + `PROP_COUNT`** | **6 项** | **11 项** | 未清点（`character.js`/`player.js` 方法集） | ★ **64 项**（`AttrLen=64`） |
| 属性存储方式 | ❌ **无键数组**（下标即 `name2idx` 序号） | ❌ **裸数字数组** `[pid,45,987.0]` | ✅ SQLite/MySQL 列 | ✅ MySQL 列 | ✅ MySQL 列 | ✅ **SQLite 命名列** |
| **输入项 vs 派生项** | ✅✅ **只存前 23 项输入，派生每次登录 `CalAttr` 全量重算** | ❌ 全量存盘（含瞬时战斗态） | ❌ 无此概念 | ❌ 无此概念（客户端算） | ❌ 未清点 | ⚠ **26 列混存输入与派生**（见 §五 G1） |
| 落库属性覆盖 | **23 / 32** | 118 / 118（全量） | 6 / 6 | 11 / 11 | 未清点 | ★ **26 / 64** |
| 加点（手动分配） | ✅ `potential_point` + `OnLevelUp` **差分保留加点** | ⚠ 属性表驱动 | ❌ 无 | ❌ 无 | ⚠ `setTotalAttackAndDefence` | ⚠ **`_config_role_attr` 表驱动，加点未读到** |
| 等级成长 | ✅ `TableRole[level]` 表驱动 + 差分 | ✅ `actor_template.tsv` 表驱动 | ❌ 硬编码 `grade=1` | ✅ `upGrade()`：`maxExp += grade*100`，血蓝 +30、攻防 +5 | ⚠ `upgrade()` | ✅ `Config.RoleAttr[lev]` 表驱动 |
| 属性可见性白名单 | ✅✅ **`attr2view = {level, life, maxlife}`（只 3 个）** | ❌ 无（全量下发） | ⚠ 全量广播 7 字段 | ⛔ **`updatePlayerData()` 广播客户端自算属性** | ⚠ 领域对象 `onXxx` 直接推送 | ⚠ **未见白名单**（`SC_20013.summon_play[]` 每回合重推 16 字段） |
| 战力（power） | ✅ 有（`power` 属性） | ⚠ 未读到 | ❌ | ❌ | ⚠ | ✅ **`AttrPower` 权重表 + `SC_10306.power:uint32`** |
| 属性变更重算机制 | ✅✅ **改动后发 `"recalattr"` 信号 → `CalAttr(true)`** | ⚠ 属性直接改写 | ⛔ 客户端 `addProperty` 累加 | ⛔ 客户端 `addProperty` 累加 | ⚠ | ⚠ **未见信号机制**（`db_save_attr` 直写） |
| 角色 CMD 段 | — | — | 7 条业务消息 | 23 条 `M_Type` | — | ★ **42 条**（`10101~10399`），实现 **10** |
| LICENSE | 🔴 `aoi.h/astar.h` 内嵌 GPLv3 | 无 | 🔴 **GPL-3.0** | 无 | 无 | — |

---

## 二、★ JSTM 角色模型（权威事实，全部【已确认】）

### 2.1 角色协议段（`10000~10399`，**42 条 CMD**，实现 10 条）

| CMD | 实现 | 真机发过 | 关键字段 | 语义 |
|---|---|---|---|---|
| `10101` | ✅ | | CS `sex:u8, name:string, career:i16, playform:string` ／ SC `code:u8, msg:string, rid:u32, srv_id:string` | **创建角色** |
| `10102` / `10103` | ✅ | `10103` ✅ | CS `rid:u32, srv_id:string` ／ SC `code:u8, msg:string, timestamp:u32, world_lev:u16` | **角色登录 / 重连** |
| `10300` | ✅ | ✅ | CS 空 | **角色初始化**（`scene_controller` 里才绑定 `LOGIN_SUCCESS`） |
| **`10301`** | ✅ | ✅ | SC `rid, srv_id, name, lev:u16, is_vip, vip_lev, sex, career:u16, face_id:u16, cur_title:u16, ntm_title:u32, gid:u32, gsrv_id:string` | **身份/外观** |
| **`10302`** | ✅ | ✅ | SC `lev:u16, exp:u32, gold, gold_acc, coin, sinew, experience, coupon, vitality, guild_contrib, practice_exp, tower_c…, arena_c…` | **货币/经验**（全 `uint32`） |
| **`10303`** | ✅ | ✅ | SC `rid, srv_id, name, lev, is_vip, vip_lev, sex, career, volume:u8, store_volume:u8, store_partner_volume:u8, volume_open:u8, …` | **容量**（背包/仓库/伙伴） |
| **`10306`** | ❌ | | SC **`attr:table; mspd:u16; power:u32`** | ★ **属性载荷 + 移速 + 战力** |
| `10331` / `10333` | ✅ | `10331` ✅ | CS `skill_bid:u32` ／ SC `code, msg` | 学技能 / 技能列表 |
| `10332` | ❌ | | SC `skill_list:table` | **技能列表**（未实现） |
| `10341` | ❌ | ✅ | CS `id_list:table` ／ SC `rid, srv_id, id, img:bool, upload_time:u32` | **真人认证/头像** |
| `10388` | ❌ | | SC `online_roles:table` | 在线角色 |
| `10397` | ✅ | | CS `status:u8` | 状态上报 |

**⇒ 关键发现**：
1. **`SC_10306` 是唯一的"属性全量"消息**（`attr:table` + `mspd` + `power`），**但 JSTM 未实现**（❌，真机也未发）⇒ 属性下发目前走哪条路径【待验证】。
2. **`SC_10302` 的货币字段全是 `uint32`**（`gold`/`gold_acc`/`coin`/`sinew`/`experience`/`coupon`/`vitality`/`guild_contrib`/`practice_exp`/…）⇒ 与 JSTM `role_assets (rid, name, amount)` 的"通用资产表"设计**互补**：前者是**协议固定字段**，后者是**DB 通用容器**。

### 2.2 ★★ 属性系统：`AttrLen = 64` vs `role_attr` **26 列**

`analysis/1.4.9/level/_attr.json`（9 815 字节）实测的 9 个顶层键：

| 键 | 含义 |
|---|---|
| **`AttrLen`** | **= 64** ⇒ 属性向量长度 **64** |
| `AttrId2Key` / `AttrKey2Id` | 属性 ID ↔ 名称双向映射 |
| `AttrId2Str` / `AttrKey2Str` | ID/名称 → 中文名 |
| **`AttrKeyIsShow`** | **哪些属性对外可见**（= 可见性白名单的配置源） |
| **`AttrPower`** | **每个属性的战力权重**（`SC_10306.power` 的计算依据） |
| `AttrPartnerPower` | 伙伴战力权重 |

**属性 ID 分段（从 `AttrId2Key` 实测，节选）**：

| 段 | 属性 |
|---|---|
| **101~104** | `strength` / `intellect` / `armor` / `constiution` ← **基础四维（输入项）** |
| **105~110** | `atk_s` / `atk_p` / `def_s` / `def_p` / `hp_max` / `hp` |
| 111~113 | `atk_speed` / `hit` / `dodge` |
| 116~118 | `energy_max` / `energy_min` / `energy` |
| 119~123 | `red_def_s` / `red_def_p` / `atk_abs` / `def_abs` / `reduce` |
| 124~127 | `hurt` / `hit_rate` / `crit_rate` / `anger_start` |
| 128~131 | `cure` / `be_cure` / `mspd` / `control` |
| 136~151 | `hurt_p` / `be_hurt` / `dodge_rate` / `tenacity_rate` / `be_hurt_s` / `be_hurt_p` / `atk_abs_s` / `atk_abs_p` / `def_abs_s` / `def_abs_p` / `res` / `dam` / `res_s` / `res_p` / `dam_s` / `dam_p` |
| **201~209** | `*_rate_show`（4 个展示用）+ `crit_hurt` / `crit_reduce` / `red_tar_def_s` / `dmg_back` |
| 240~243 | `anti_control_s` / `anti_control_c` / `anti_control_y` |

**JSTM `role_attr` 表（26 列，`mock_server.py:1562-1571` 实测）**：
`rid, strength, intellect, armor, constiution, atk_s, atk_p, def_s, def_p, hp_max, atk_speed, hit, dodge, crit, tenacity, red_def_s, red_def_p, atk_abs, def_abs, reduce, hurt, hit_rate_show, dodge_rate_show, crit_rate_show, tenacity_rate_show, updated_at`

| 对照 | 结果 |
|---|---|
| **已落库** | **25 个属性**（+ `rid` = 26 列） |
| **属性系统总数** | **64** |
| **⇒ 未落库属性** | **39 个**（含 `strength/intellect/armor/constiution` **之外的全部基础项**？——注意四维**在**表中） |
| **输入项（应落库）** | `strength / intellect / armor / constiution`（4 个）+ 可能的加点/养成项 |
| **派生项（不应落库）** | `hp_max / atk_s / atk_p / def_s / def_p / atk_abs / def_abs / reduce / hurt / *_rate_show` 等**其余 21 个** |
| **表中有但 `AttrId2Key` 无对应** | ⚠ `crit` / `tenacity`（配置里是 `crit_rate` / `tenacity_rate`，另有 `crit_rate_show` / `tenacity_rate_show`）⇒ **命名不一致，需核对** |

**⇒ ★ 这是 `database_matrix` G4 的量化版**：JSTM 的属性表**既存了派生项（21 个）**，**又漏了 39 个属性** ——
**两个问题同源：属性表是按"当前实现需要"逐步加的列，而不是按 `AttrLen=64` 的属性总表设计的。**

### 2.3 ⚠ 一处**过时的项目文档**（需更正）

| 文档 | 现述内容 | 问题 |
|---|---|---|
| `analysis/1.4.9/role/role_persistence.md` | 「先用 **JSON 落盘**」；「当前只落地了 **rid + x + y**」；`name/lev/career/scene_id/hp/mp/uid` **全部标 ⬜ 未存** | 🔴 **这是 Phase 4E 之前的状态**。实测 `server/mock_server.py` 的 `save_role_pos()` docstring 已明确写「把坐标写进 **数据库**（**Phase 4E 起以 DB 为准**）」，且库中已有 **`roles`(23 列)** 等 11 张表 —— `name/level/career/hp/mp/uid/scene_id` **全部已落库** |

**⇒ 该文档已过期**，会把读者误导为"JSTM 只有 rid+x+y 持久化"。建议加过期标注或重写（见 §七 更正 4）。

---

## 三、★★ 属性系统四方对照（本矩阵核心）

| 关注点 | **Survive**（最佳实践） | **YZXY** | **侠客行** | **JSTM 现状** |
|---|---|---|---|---|
| **属性总量** | 32 项 | 118 项 + `PROP_COUNT` | 11 项运行时字段 | **64 项** |
| **属性定义源** | `common/name2idx.lua`（**手写顺序表**） | ★ `actor_template.tsv` → **生成** `EActorProp` 枚举（含 `sync` 列） | 无（散在 `PlayerData.h`） | ✅ `_attr.json`（`AttrId2Key` 等 9 键，含战力权重） |
| **下标一致性保证** | ❌ 无（`name2idx` 改顺序即老档错位） | ✅ **`assert(index == m_Props.size())` 把"表行序==枚举值==数组下标"锁死** | — | ✅ 命名列（无下标风险） |
| **持久化范围** | ✅ `attr_db_save = attack - 1 = **23**` ⇒ **只存前 23 项输入** | ❌ 全量存盘（**含瞬时战斗态** `PROP_COMBAT_BATTLE_ID`/`PROP_TURN_READY`） | ❌ 全量（11 字段直存） | ⚠ **26 列混存**（21 派生 + 4 输入 + 未覆盖 39） |
| **派生属性计算** | ✅✅ **`CalAttr(notifyclient, withoutweapon)` 一次性全量重算**（读基础 + `TableEquipment` + `TableIntensify` + `TableRising_Star` + 4 宝石 `TableStone`） | ⚠ 属性直接改写 | ⛔ 客户端 `addProperty` 累加 | ⚠ **未见重算入口**（`db_save_attr` 直接写列） |
| **变更 → 重算的解耦** | ✅✅ **`bag:Swap` 返回 `true,"recalattr"` → `ply:CalAttr(true)`** | ❌ | ❌ | ⚠ **未见信号机制** |
| **加点保留** | ✅✅ **`OnLevelUp` 差分法**：用 `TableRole[cur]` 与 `TableRole[level]` 的**差值**算出 `*_base`（手动加点部分），`Set` 新等级基础值 + **保留差值** | ⚠ 表驱动 | ❌ | ⚠ **加点机制未读到**（`Config.RoleAttr` 表存在） |
| **可见性白名单** | ✅✅ **`attr2view = {level, life, maxlife}`（只 3 个）** + **一次变更两个包**（视野包/自身包） | ❌ 全量 | ⛔ 全量广播**客户端自算**属性 | ⚠ 未见白名单；但 `AttrKeyIsShow` **配置已存在** ⇒ **可直接拿来用** |
| **战力公式** | ✅ 有 `power` 属性 | ⚠ 未读到 | ❌ | ✅ **`AttrPower` 权重表**（`SC_10306.power:u32`） |
| **已知缺陷** | ⚠ **`CalAttr` 不更新 `life`**（当前血量）⇒ 可能 `life > maxlife`【待验证】；`friends:PeekInfo` **把全属性发给好友**（与 `attr2view` 白名单自相矛盾） | ⚠ `EActorProp` 118 项使协议退化为**裸数字** `[pid,45,987.0]`（不可读、不可版本兼容） | ⚠ `m_addspeed` 读了但 `addProperty` 无速度形参 ⇒ **速度加成永不生效** | ⚠ 见 §五 |

---

## 四、五项目角色模型（逐文件表）

> 格式：`文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因`

### 4.1 Survive（★ 属性系统的最佳参考）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `common/name2idx.lua` | `name2idx` 表 | **32 项属性顺序表**（含 `endidx` 哨兵）；`attr_db_save = attack - 1` | ⚠ 部分 | ★ **"用一张表定义属性顺序 + 用一个游标标出持久化边界"**思想极好；❌ 但**无键数组**⇒ 顺序一改老档全错位 ⇒ **JSTM 应用命名列** |
| `groupserver/attr.lua` | `DbStr()` | `for i=1,attr_db_save do t[i]=attr[i] end; cjson.encode(t)` —— **只存前 23 项** | ✅✅ **高度适合** | ★ ★ **"只持久化输入项、派生项每次重算"是防数据腐化的根本手段**，直接对应 JSTM 的 G1 |
| `groupserver/attr.lua` | `Get/Set/Add/Sub/NotifyUpdate` | 属性读写 + 变更通知 | ✅ 适合 | 属性变更统一走 `NotifyUpdate` |
| `gameserver/attr.lua` | **`attr2view = {level, life, maxlife}`** + `on_entersee` + `NotifyUpdate` | **视野内玩家只收 3 个属性；自己收全量；一次变更生成"视野包 + 自身包"** | ✅✅ **高度适合** | ★ ★ **隐私 + 带宽 + 反外挂三重收益**；JSTM **已有 `AttrKeyIsShow` 配置** ⇒ 可直接实现同构白名单 |
| `groupserver/groupplayer.lua` | **`CalAttr(notifyclient, withoutweapon)`** | **一次性全量重算所有派生属性**（基础 + 装备 + 强化 + 升星 + 宝石） | ✅✅ **高度适合（思想）** | ★ ★ **"任何变化后一次性重算"比"增量修改"最不容易出 bug**；JSTM 应改为**事件驱动的全量重算** |
| 同上 | **`OnLevelUp(level, notifyclient)`** | **差分升级**：`TableRole[cur]` 与 `TableRole[level]` 差值 = 手动加点部分；`Set` 新基础 + **保留差值**；`potential_point` 累加；最后 `CalAttr` | ✅ **适合（算法）** | ★ ★ **"升级时保留手动加点"必须这样做**（否则加点被重置）；⚠ 其实现把 6 个属性**逐个手写 4 遍**（读旧-算差-读新-写）⇒ **JSTM 应写成循环/数据驱动** |
| `groupserver/bag.lua` | `Swap(pos1,pos2)` | 校验槽位/类型/等级/绑定；同 id 非装备**合并**；**衣服/武器/腰带 4 位变动时返回 `true,"recalattr"`** | ✅✅ **高度适合（思想）** | ★ ★ **"换装只改数据并返回信号，上层据此重算"**是干净的解耦 ⇒ JSTM 的装备穿戴应同样"改数据 → 发信号重算" |
| `groupserver/groupplayer.lua` | `CMD_CG_EQUIP_UPRADE` / `ADDSTAR` | 强化/升星：`SetAttrLow/High` 位打包 + 扣币 + `CalAttr` + 任务/成就事件 | ⚠ 部分 | ★ **"强化 + 升星都触发属性重算"**的顺序对；❌ **位打包**不可学（见 `reuse_candidates.md`） |
| `groupserver/friends.lua` | `PeekInfo(chaid)` | 查在线好友 → `attr:Pack(wpk)` **全属性**发给好友 | ⛔ **不适合** | 🔴 **与 `attr2view` 白名单自相矛盾** ⇒ "查看他人"必须限定字段 |
| 已知 bug ≥7 处 | 满级免费升级 / `awarded` 未定义 / 邮件 id 冲突 / 好友 `self.owner` nil / `PeekInfo` 逻辑取反 / `RemItem` 越界 / `CalAttr` 不更新 `life` | — | ⛔ | **只借结构，不要借实现** |

**⚠ 一处文档自相矛盾（需更正）**：`survive/role.md:17` 写「**`attr_db_save = attack-1` ⇒ 只持久化前 31 项**」，
而同文 `:158` 写「`attr_db_save = nameidx.attack - 1 = **23**`」。
按 `attack` 是第 24 项（`:146`）推算 ⇒ **正确值是 23**，`:17` 的"31"是笔误（连公式都写成 23 的形式却写结论 31）。

### 4.2 YZXY / CXEngine（★ 属性定义的"单一真源"范式）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `assets/tables/actor_template.tsv` | — | **属性模板表（含 `sync` 列）** | ✅✅ **高度适合（范式）** | ★ ★ **"表单一真源 → 生成多端定义"**：同一张表既生成 C++ 枚举、又供运行期注册 |
| `scripts/generator/actor_template.lua` | — | 由 TSV **生成** `actor_enum.h` | ✅✅ 适合 | ★ JSTM 可等价：**以 `_attr.json` 的 `AttrId2Key` 为唯一真源，生成服务端常量 + 客户端映射 + 校验用 schema** |
| `common/src/actor/actor_enum.h` | `enum EActorProp`（**118 项 + `PROP_COUNT`**）、`EActorPropType{BOOL,FLOAT,INT,STR,UINT64,VEC2}` | 枚举值 = 数组下标 = 协议属性号 | ⚠ 部分 | ★ **"表行序==枚举值==数组下标"由 `assert(index == m_Props.size())` 锁死**是防错好手段；❌ **但让协议退化为裸数字 `[pid,45,987.0]`**（不可读、不可版本兼容）⇒ **JSTM 不应把属性退化成裸数字** |
| `scripts/server/actor_system.lua` | `actors_on_load` / `actors_on_save` | 全量 JSON 读/写 `actor.data` | ⛔ **不适合** | 🔴 **明文 + 全量重写 + 含瞬时战斗态 + 含全服 NPC** |
| `scripts/share/utils.lua` | `utils_next_uid(ns)` | `os.time()%0xFFFFFFFF` 起、内存自增、**不持久化** | ⛔ 不适合 | 同秒重启可能重号 ⇒ JSTM 用 SQLite `INTEGER PRIMARY KEY`（**优于它**） |
| `scripts/client/actor_metatable.lua` | — | 客户端属性元表 | 【未读到】 | `yzxy/architecture.md:214` 记录为"仅读到片段/未读" |

### 4.3 侠客行（★ 有一份可用的成长公式；但权威在客户端）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/PlayerData.h` | `class PlayerData` | 运行时属性全集：`glod / grade / blood / mana / attack / defense / speed / exp / maxExp / curblood / curmana` | ✅ 适合（字段清单） | ★ **上限值与当前值分两组**（`blood` vs `curblood`）—— 与 JSTM `role_attr.hp_max` / `roles.hp` 的**同名同构** |
| `Classes/PlayerData.cpp:58-66` | `upGrade()` | `++m_grade`；`m_maxExp += m_grade * 100`；`addProperty(**30 blood, 30 mana, 5 attack, 5 defense**)` | ✅ **适合（成长公式）** | ★ **升级成长：血蓝各 +30、攻防各 +5；经验需求 `grade*100` 累加** ⇒ 一套完整可用的等级曲线起点 |
| `Classes/PlayerData.cpp:68-75` | `addProperty(...)` | 加属性后**最后一行立刻 `CMClient::updatePlayerData()`** 把新属性广播给所有人 | ⛔ **不适合** | 🔴 广播的是**客户端自算**的属性 ⇒ **等于把伪造入口留给玩家**（JSTM 必须服务端算） |
| `Classes/EquipMent.cpp:74-85` | `beUse` | 穿戴：`addProperty(addblood+(grade-1)***30**, addmana+(grade-1)*30, addattack+(grade-1)***8**, adddefense+(grade-1)*8)` | ✅ 适合（公式） | ★ **"装备加成 = 基础值 + (等级−1) × 每级增量"**（血魔 30/级、攻防 8/级）统一公式，简洁 |
| `Classes/EquipMent.cpp:87-103` | `Disassemble` | 拆卸用**完全相同公式反向扣除** + 退回背包 | ✅ 适合（设计） | ★ **加/减成对使用同一公式** ⇒ 保证穿脱对称（装备系统最易错处，本项目处理正确） |
| `Classes/EquipMent.cpp:45,156-159` | `m_baseupglod` / `upGlod()` | `m_baseupglod = addblood + addmana + addattack*10 + adddefense*10`；升级价 `m_baseupglod + m_grade*(100 + m_baseupglod/10)` | ✅ 适合（设计） | ★ **升级价由装备强度派生**（攻防按 ×10 权重）而非硬编码 ⇒ 配方表可省一列 |
| `Classes/EquipMent.cpp:69,81` + `PlayerData.h:58` | `m_addspeed` | 读了 `speed`，但 `addProperty` **只有 4 个形参**（blood/mana/attack/defense） | ⛔ | 🔴 **速度加成永不生效**（与怪物 `speed` 无人使用相互印证）⇒ JSTM 若保留 speed 必须真接上 |
| `Classes/Model.h` → `playerinfo` | 15 字段 | `playername, rolename, roletype, glod, grade, blood, mana, attack, defense, speed, exp, maxexp, destx, desty, level` | ✅ 适合（字段语义） | ★ 已支撑 JSTM 角色表设计；⚠ `level` 实为**地图号**（命名误导）；⚠ 无 `hp_max`/`curblood` 之分 |
| 建号初值（`NewGameLayer::constructPlayerInfo`） | — | attack 100 / blood 300 / defense 20 / glod 300 / grade 1 / mana 150 / speed 4 / exp 0 / maxExp 100 / destx=desty=100 / level 1 | ✅ 适合（数值） | ★ JSTM 1 级角色属性基线的对照样本 |

### 4.4 空空西游（★ 实时制 + 领域对象推送风格）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `app/domain/entity/player.js`（22.5 KB） | `equip / unEquip / useItem / pickItem / addItem / learnSkill / upgradeSkill / **setTotalAttackAndDefence** / upgrade / onHpMp / onHp2All …` | 玩家全套行为 + **客户端推送方法** | ✅ **强适合** | ★ **`setTotalAttackAndDefence`**（**统一入口重算攻防**）与 Survive `CalAttr` 同职责；★ **"领域对象的 `onXxx` 直接负责推送"**是本项目风格（`onExp`/`onMoney`/`onHpMp`）⇒ 可借鉴**但要注意别让领域层依赖网络层** |
| `app/domain/entity/character.js` | `attack / getAvailableSkill / checkSkillAvailable / hit / reduceHp / reduceMp / addBuff / removeBuff / addEnemy / forEachEnemy / forgetEnemy / increaseHateFor / getMostHater` | 战斗实体（技能冷却 + 命中 + **仇恨表** + 敌人表） | ✅ 强适合 | ★ **仇恨表 + 敌人表**是 JSTM 目前缺的（见 `battle_matrix` B3） |
| `app/dao/**` + `dao/mapping/*Sync.js` | `userDao.updatePlayer` / `taskDao.tasksUpdate` | **内存对象 + 脏标记 + 定时批量 UPDATE** | ✅✅ **强适合** | ★ ★ **存档策略的唯一正面样本**（对应 `database_matrix` G6） |
| `app/domain/entity/player.js` | `upgrade()` | 升级 | ⚠ 部分 | 未清点成长公式细节【未读到】 |

### 4.5 大圣归来（❌ 角色维度几乎无信息）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Server/gametable.sql` | `game` 表 | 11 字段，角色字段仅 6 个（`playerName/PlayerType/XPoint/YPoint/blood/grade/direction`） | ⛔ | **无 `maxBlood`/`mana`/`attack`/`defense`/`exp`/`gold`** ⇒ 数据层不支撑属性系统 |
| `Classes/Player.cpp:55-98` | `initWithJson` | 解析 6 字段；**`grade` 在 type 分支里被硬编码覆盖为 1** | ⛔ | 🔴 服务端下发的等级加载后立即丢失 |
| `Classes/Player.h` | — | 成员仅 6 个可持久化字段；`state{ FREE, WALK, ATTACK, DEAD }`（`DEAD` 零引用） | ⛔ | 数据模型过薄 |
| **⇒ 结论** | — | **大圣归来在角色/属性维度信息量为 0**，仅可作"有 `blood` 却从不更新的反面" | ⛔ | — |

---

## 五、★ 角色/属性缺口（对 JSTM）

| # | 缺口 | 现状证据 | 参考依据 | 建议 | 优先级 |
|---|---|---|---|---|---|
| **G1** | **`role_attr` 26 列混存输入项与派生项，且只覆盖 25/64 个属性** | `role_attr` 有 `hp_max/atk_s/atk_p/def_s/def_p/atk_abs/def_abs/reduce/hurt/*_rate_show`（**派生**）与 `strength/intellect/armor/constiution`（**输入**）；`AttrLen = 64` | ★ ★ Survive `attr_db_save=23` + `CalAttr` 全量重算 | **拆两张表**：`role_attr_base(rid, strength, intellect, armor, constiution, …加点/养成)` **只存输入**；派生项**不落库**，登录/变更时用 `Config.RoleAttr` + 装备 + 强化**全量重算** | **P0** |
| **G2** | **无"属性变更 → 重算"的信号机制** | 未见 `recalattr` 类信号；`db_save_attr` 直接写列 | ★ ★ Survive `bag:Swap → true,"recalattr" → CalAttr(true)`；空空西游 `setTotalAttackAndDefence` | 装备/强化/升级/加点 4 条路径**统一发信号**，由单一入口重算后再下发 | **P0** |
| **G3** | **无属性可见性白名单** | 未见白名单；`SC_20013.summon_play[]` 每回合重推 16 字段 | ★ ★ Survive `attr2view = {level, life, maxlife}` + 一次变更两个包 | ★ **JSTM 的 `_attr.json` 已有 `AttrKeyIsShow`** ⇒ 直接用它生成白名单；他人只能看白名单字段，自己收全量 | **P1** |
| **G4** | **39 个属性未落库**（64 − 25） | `AttrLen=64` vs `role_attr` 25 个属性列 | — | 先明确"哪些是输入项"（应落库）、"哪些是派生项"（不该落库、该重算）⇒ 按 G1 拆分后**大部分 39 个会落在"派生"侧，无需落库** | **P1** |
| **G5** | **加点（手动分配）机制未读到** | `Config.RoleAttr[lev]` 表存在；加点列未见 | ★ ★ Survive `OnLevelUp` **差分法保留加点** + `potential_point` | 若 JSTM 有加点，**必须用差分法**（否则升级会重置加点） | **P1** |
| **G6** | **`SC_10306`（`attr:table + mspd + power`）未实现** | `role_protocol.md`：`10306` ❌ 未实现 | — | 属性下发目前走哪条路径【待验证】；若走 `10302/10306`，需明确 `attr` 子表结构 | **P1** |
| **G7** | **`crit` / `tenacity` 与配置命名不一致** | `role_attr` 列名是 `crit` / `tenacity`；`AttrId2Key` 是 `crit_rate` / `tenacity_rate`（另有 `crit_rate_show` / `tenacity_rate_show`） | — | 统一命名，避免"同名不同义" | P2 |
| **G8** | **角色 CMD 42 条只实现 10 条** | 未实装：`10304`（看他人）、`10305`（资产）、`10306`（属性）、`10324`（改名）、`10325-10327`（换脸）、`10328`（兑换点）、`10332`（技能列表）、`10334`（洗点币）、`10340-10343`（真人认证/改名卡）等 | — | 按真机实测优先级推进（真机发过：`10103`/`10300`/`10301`/`10302`/`10303`/`10331`/`10341`） | P2 |
| **G9** | **战力（`power`）计算未落地** | `_attr.json` 已有 **`AttrPower` 权重表**；`SC_10306.power:u32` 未实现 | — | 用 `AttrPower` 直接算（**无需向参考项目学**） | P2 |
| **G10** | **`role_persistence.md` 已过期** | 文档说"只有 rid+x+y"，实际 11 表 98 列已落库 | — | 加过期标注或重写（§七 更正 4） | P2（文档级） |

---

## 六、五项目角色反例清单（JSTM 明确不要学）

| # | 反例 | 来源 | 后果 |
|---|---|---|---|
| 1 | **属性用无键数组存**（下标即属性号） | Survive `name2idx` + `chainfo` | 顺序一改，**全部老档错位** |
| 2 | **属性退化为裸数字协议** `[pid,45,987.0]` | YZXY `EActorProp` 118 项 | 不可读、不可版本兼容 |
| 3 | **存档含瞬时战斗态** | YZXY（`PROP_COMBAT_BATTLE_ID` / `PROP_TURN_READY`） | 读档后带着战斗标记 |
| 4 | **存档含全服 NPC** | YZXY `actors_on_save` 遍历 `fetch_all_actors()` | 把 NPC 当玩家存档 |
| 5 | **明文 + 全量重写存档、无原子写** | YZXY `actors_on_save` | 崩溃即存档损坏 |
| 6 | **客户端自算属性并广播** | 侠客行 `addProperty → updatePlayerData()` | 伪造入口 |
| 7 | **读了 `speed` 但从未生效** | 侠客行 `m_addspeed`（`addProperty` 无速度形参） | 数值表与实现脱节 |
| 8 | **查看他人把全属性发出** | Survive `friends:PeekInfo → attr:Pack` | 隐私泄露（且与自家白名单矛盾） |
| 9 | **加/减属性公式不一致** | 侠客行 `upgrade()` 固定 `addProperty(30,30,8,8)` vs `beUse` 的 `(grade-1)*30` | 精炼后属性非严格按等级重算 |
| 10 | **服务端下发的 `grade` 加载后被硬编码覆盖** | 大圣归来 `Player.initWithJson` | 等级丢失 |
| 11 | **有 `blood` 字段却从不更新** | 大圣归来 | 数据层假象 |
| 12 | **领域对象直接依赖网络层推送** | 空空西游 `onXxx` 推送风格 | 分层被破坏（可借鉴但需注意） |

---

## 七、本矩阵发现的**待传播更正**清单

| # | 文档 | 位置 | 现有表述 | 更正为 | 依据 |
|---|---|---|---|---|---|
| 1 | `survive/role.md` | `:17` | 「`attr_db_save = attack-1` ⇒ **只持久化前 31 项**」 | **23 项**（同文 `:158` 已自证 `= 23`；`attack` 为第 24 项） | `survive/role.md:146/:158` |
| 2 | `R1_SUPPLEMENT.md` | `:102` | 「只持久化**输入项**（前 23 项）」 | ✅ **正确**，无需改（仅与 #1 对照说明 23 是准的） | 同上 |
| 3 | `database_matrix.md` | §一 属性行 | 已写"只存前 23 项" | ✅ 正确 | 同上 |
| 4 | `analysis/1.4.9/role/role_persistence.md` | 全文 | 「先用 JSON 落盘」「当前只落地 rid + x + y」「`name/lev/career/scene_id/hp/mp/uid` 全部 ⬜ 未存」 | 🔴 **已过期**：Phase 4E 起 **DB 为准**（`save_role_pos` docstring 自证），`roles` 23 列已含 `uid/name/level/career/hp/mp/scene_id` | `server/mock_server.py:2399-2401`（`save_role_pos` docstring）+ `roles` 表 23 列 |
| 5 | `database_matrix.md` | G4 行 | 「`role_attr` 的 26 列**输入项与派生项混存**」 | **量化补充**：属性系统 `AttrLen = 64` ⇒ **落库 25 / 64**，**39 个属性未落库**；其中 21 个是**不该落库的派生项** | `analysis/1.4.9/level/_attr.json` `AttrLen=64`；`role_attr` 26 列 |

---

## 八、【待验证】/【未知】

| 项 | 状态 |
|---|---|
| JSTM 属性下发路径（`SC_10306` 未实现，属性走哪条消息） | 【待验证】 |
| JSTM 加点（手动分配）机制 | 【未读到】`Config.RoleAttr` 表存在但加点列未见 |
| JSTM 是否有属性重算入口（对应 `CalAttr`） | 【未读到】`mock_server.py` 只见 `db_save_attr` 直写 |
| `role_attr` 的 `crit` / `tenacity` 是否对应 `AttrId2Key` 的哪些键 | 【待验证】命名不一致 |
| `AttrPower` 的具体权重值与 `power` 公式 | 【未读到】只确认该键存在（`_attr.json` 9 键之一） |
| `AttrKeyIsShow` 的取值（哪些属性对外可见） | 【未读到】键存在，未展读 |
| 空空西游 `player.js` 的 `upgrade()` 成长公式 | 【未读到】 |
| YZXY `EActorProp` 118 项的逐项名称 | 【未读到】只确认枚举规模与 `PROP_COUNT` |
| Survive `CalAttr` 的公式系数 | 【已确认读到】，但 ⛔ **不可抄**（`survive/role.md:478` 明列禁用） |
| 侠客行服务端的角色/属性实现 | 【未读到】CM-Server 不在 ZIP |

---

## 九、一句话结论

> **JSTM 的角色系统在"属性容量"上远超全部 5 个参考项目**（`AttrLen = 64` vs Survive 32 / 侠客行 11 / 大圣 6），
> 且**已有参考项目都没有的配套元数据**：`AttrId2Key`/`AttrKey2Id`（双向映射）、`AttrKeyIsShow`（**可见性白名单配置，直接可用**）、
> **`AttrPower`（战力权重公式）**、`AttrId2Str`/`AttrKey2Str`（中文名）。
>
> **⇒ 但属性表 `role_attr` 只落了 25/64，且把 21 个派生项也存了进去** ——
> **两个问题同源：该表是按"当前实现需要"逐列加的，而不是按 `AttrLen=64` 的属性总表设计的。**
>
> **⇒ 唯一需要向参考项目学的是"属性系统的三条铁律"，全部来自 Survive**：
> ① **只持久化输入项，派生项每次全量重算**（`attr_db_save=23` + `CalAttr`）；
> ② **变更后发信号重算，而不是就地改派生值**（`bag:Swap` 返回 `"recalattr"`）；
> ③ **属性可见性白名单 + 一次变更两个包**（`attr2view={level,life,maxlife}`）。
> **⇒ 而这三条 JSTM 都已有落地条件**（`AttrKeyIsShow` 配置、`Config.RoleAttr` 表、`role_assets` 通用容器），
> **只是还没接起来** —— 这正是 `database_matrix` G4 与本文 G1/G2/G3 的同一件事。
>
> **另一处可直接复用的成长数值**来自侠客行：升级 `maxExp += grade*100`、血蓝各 +30、攻防各 +5；
> 装备加成 `基础值 + (等级−1) × (血魔 30 / 攻防 8)`；升级价 `m_baseupglod + m_grade*(100 + m_baseupglod/10)` ——
> **四条线性公式构成一套完整可用的等级/装备曲线起点**（但**必须服务端结算**，侠客行把它们放在客户端是明确反例）。
