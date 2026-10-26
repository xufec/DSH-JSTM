# 战斗矩阵（R6）—— 五参考项目 × JSTM 战斗系统对照

> **本文档闭环 `R1_SUPPLEMENT.md` §六 未做项 ②「`comparison/` 其余矩阵未单独出文件 → `battle_matrix`」。**
> 依据：`yzxy/battle.md`（60 KB，含 JSTM 侧字节码字段直读）+ `analysis/1.4.9/battle/battle_protocol_matrix.md`（真机订正）
> + `analysis/jstm_1.4.9/*_protocol.md`（CMD 段清点）+ `survive/battle.md` + `chivalrousman/battle.md`（我方）+ `kongkongxiyou/reuse_candidates.md`。
> 标注：【已确认】/【待验证】/【未知】；未读到的一律写「未读到」。
> **本文件只读，未修改 `server/` 任何文件。**
>
> ⚠ **时效声明**：JSTM 侧行号/CMD 数取自本次读取快照（`server/` 正被其他 agent 活跃开发）。引用请以 CMD 号 / 字段名 / 函数名定位。

---

## 一、结论速览（6 方对照）

| 维度 | **Survive** | **YZXY / CXEngine** | **大圣归来** | **侠客行** | **空空西游** | **JSTM 现状** |
|---|---|---|---|---|---|---|
| 战斗模式 | **实时**（伴随移动） | **独立回合制** | ❌ **无战斗** | **回合制逻辑 + 实时定时器调度** | **实时**（`attack(attacker,target,skill)` 即时判定） | **独立回合制**（`SC_20010/20012/20013/20020`） |
| 回合驱动 | — | **客户端本地 `NextTurn()`** | — | **客户端** `playAnimate` 递归 / `onTimer` 行动条 | — | ★ **服务端自定节拍 2.5 s/回合自续期**（见 §三） |
| 伤害权威 | **服务端**（但零校验） | **服务端**（随机只在服务端摇） | ❌ | ⛔ **客户端本地** | **服务端**（`AreaLogic.attack`） | **服务端**（`SC_20013.hp/hp_max/hit/is_target_die` 逐条下发） |
| 单位状态同步 | — | ⛔ **无单位重推；buff 完全不上线** | — | 每 0.4 s 广播坐标 | 属性推送（`onHpMp` 等） | ★ **每回合全量重推** `summon_play[]`（16 字段） |
| buff/状态载体 | 位打包（反例） | ⛔ **无协议，客户端重放判定** | ❌ | `playerState` + 内存标记 | `fightskill.js`/`buff.js` + `addBuff/removeBuff` | ✅ **`magic_list[] = (magic_bid:i32, change_hp:i32, duration:u8, per:i16, val:i16, fold:u8)`** |
| 出手顺序 | — | ✅ **服务端 `CalcSpeed()` 降序** | — | 行动条 `onTimer`（10s 手动 / 2s 自动） | 行为树 AI | ⚠ **`SC_20013.order_list[]` 已存在，是否按速度未确认** |
| 战斗反作弊 | ⛔ **零距离/角度/目标数/能量校验** | ⚠ 有状态+重复提交校验，**无归属校验/无超时** | — | ⛔ **无任何校验** | 服务端权威判定 | ⚠ **有客户端侧演算校验通道 `10601/10610`** |
| 回合超时 | — | ⛔ **文档说 30 s，代码无实现** | — | 无（但 10 s/2 s 自动托管） | — | ⚠ **有 `time:u8` 字段；超时逻辑未读到** |
| 掉落 | 有（表驱动） | 有（`assets/doc` 掉落清单） | ❌ | ⛔ **无掉落表**（grep `drop` 零命中） | ✅ `dropItem`/`_dropEquipment` | 有（`config_drop.json` / `drop_item`） |
| LICENSE | 🔴 `aoi.h/astar.h` **内嵌 GPLv3** | 无 | 🔴 **GPL-3.0** | 无 | 无 | — |

---

## 二、★ JSTM 真实战斗模型（权威字段，全部【已确认】）

### 2.1 ⚠ 先澄清一处**文件名误导**（避免后人查错文件）

| 文件 | 覆盖 CMD 段 | **实际内容** |
|---|---|---|
| `analysis/jstm_1.4.9/battle_protocol.md` | `13000~13099`（98 条） | ⚠ **不是战斗**：是**副本/爬塔/章节/成就**类（`dung_bid`、`chapter_star`、`CengList`、`floor`、`chengjiu`…） |
| `analysis/jstm_1.4.9/dungeon_protocol.md` | `13300` 起（137 条） | ⚠ 起始就是 `friend_list`（社交）⇒ 两文件的**命名与实际段位都不吻合** |
| **JSTM 真实战斗协议** | **`20000~20099`（25 条）** | ✅ 这才是战斗：`20002/20008/20010/20011/20012/20013/20014/20016/20017/20020/20021/20025–20030` |

**⇒ 【已确认】查 JSTM 战斗协议应看 `20000` 段，不要被 `battle_protocol.md` 的文件名误导。**
（依据：`architecture_matrix.md:179`「`20000~20099` 段 **25 条** CMD」+ `yzxy/battle.md` §5.6 直读 `cmd_resolve_200.luac`。）

### 2.2 战斗链路与字段（【已确认】，`cmd_resolve_200.luac` 直读）

```
CS_20002（发起战斗）
   → SC_20010（战斗初始化：单位 18 字段，含 skills[]/specials[]/animate_res[]）
   → SC_20012（小回合战斗效果）  ┐
   → SC_20013（回合开始·伤害落点）├ 每回合重复，服务端自定节拍（2.5 s 自续期）
   → SC_20020（战斗结果）        ┘
   → CS_20021（客户端唯一主动上报，body 4 字节 = 被击败怪物 mon_id）
```

| 消息 | 字段 | 语义 |
|---|---|---|
| **`SC_20012`** | `round:u16`；`skill_play[] = order:u8, user_id:u16, skill_id:u32, father_id:u32, father_skill_id:u32, passive_skill_id:u32, user_anger:u16, talk:string, notice:string, magic_play[], summon_play[]`；`cooldown[] = bid:u32, last_use:u16` | **技能播放**（谁对谁放了什么） |
| **`SC_20013`** | `round:u16, round_wave:u16, time:u8, wave_no:u8`；`magic_play[] = order:u8, target_anger:u16, target_id:u16, source_id:u16, hit:i8, hp_max:u32, hp:u32, is_target_die:u8, target_talk:string, magic_list[]`；`summon_play[]`（16 字段）；`order_list[] = id:u32` | **伤害落点**（HP 结果逐条下发 ⇒ **服务端权威**） |
| **`magic_list[]`** | `magic_bid:i32, change_hp:i32, duration:u8, per:i16, val:i16, fold:u8` | ★ **buff/状态载体**：`duration`=剩余回合、`fold`=层数、`change_hp`=每回合 HP 变化 |
| 配置侧 | `Config.SkillMagic`（**12 665 行**）+ `Config.SkillMagicType`（**31 个属性 ID**，含 `1240 control`/`1250 anti_control`/`1130 cure`） | buff 定义 |

**⚠ 一处已纠正的误判**：`specials[]`（8 个 key）**不是** buff 载体，而是**伙伴外观通道**（模型/配色评分/阶段特效/光环/重生/羁绊标记）；
buff 载体是 **`magic_list`**（依据：`yzxy/jstm_battle_fields.md` §9 的穷举）。

### 2.3 JSTM 有而参考项目没有的战斗子系统（【已确认】）

| 子系统 | JSTM CMD | CXEngine | 空空西游 |
|---|---|---|---|
| 观战 | `20016` / `20017` | ❌ | ❌ |
| 战斗录像 | `20025`–`20030` | ❌ | ❌ |
| 自动战斗 | `20008` + 客户端 `dungeon/auto_fight.luac` | ❌ | ⚠ 行为树 `autoFight` brain |
| 客户端侧演算校验 | `10601` / `10610` | ❌ | ❌ |
| 单位状态每回合全量重推 | `SC_20013.summon_play[]` | ⛔ **无** | ❌ |

**⇒ 结论**：**参考项目在"战斗同步的字段集与完整性"上全面弱于 JSTM** —— 能从它们身上学的只有"结构/机制"，**字段本身无需参考**。

---

## 三、★★★ 回合驱动模型：三方对比 + **一处必须传播的更正（R6）**

### 3.1 ⚠ 共享集成文档仍带**已作废**的"ACK 节流"结论

| 文档 | 现行表述（**过时**） | 位置 |
|---|---|---|
| `comparison/architecture_matrix.md` | 「回合推进：服务端推 `SC_20012/20013`；**有无回执：✅ 客户端 `CS_20014` ACK 后才推进**；照搬后果：**会丢掉 ACK 节流**」 | `:187-189` |
| `comparison/architecture_matrix.md` | 「**推进权必须在服务端**（客户端 `CS_20014` ACK 后才推）」 | `:18` |
| `R1_SUPPLEMENT.md` | 「JSTM **服务端 `SC_20012/20013` → 客户端 `CS_20014` ACK 后才推进**」 | `:35` |
| `FINAL_SERVER_ARCHITECTURE.md` | 「`CS_20002 → SC_20010 → SC_20012/20013 → **CS_20014(播完回执)** → SC_20020`」；「✅ 客户端 `CS_20014` ACK 后才推进」；「**会丢掉 ACK 节流**」；「保留 `CS_20014` 的 ACK 节流」 | `:63, :66, :73, :74, :92, :98` |

### 3.2 ✅ 权威订正（**已在 `yzxy/` 目录内完成，但从未传播到集成文档**）

**订正来源**：`analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1 真机订正
（经 `yzxy/architecture.md:28-43`、`yzxy/battle.md:523-548`、`yzxy/reuse_candidates.md:39-45,327-332` 三处引用确认）

| 观察（真机 `tcp.log`） | 结果 |
|---|---|
| 客户端是否发 `CS_20011`（加载完成） | ❌ **从未发出**（整场战斗无 `cmd=20011`） |
| 客户端是否发 `CS_20014`（动画播放完成） | ❌ **从未发出**（无 `cmd=20014`） |
| 客户端收到 `SC_20020` 后 | ✅ **主动发了 `CS_20021`**（`csCloseFinishView`） |

**★ 根因**：原「`CS_20014` ACK 驱动」的结论引自 `analysis/1.4.9/battle/battle_chain_verified.md`，
**而那份文档描述的是我们自己的 `mock_server.py` 实现**（`行 2445 if cmd == 20014:` —— **我们自己把 20014 当成了推进条件**），
**不是真实客户端行为**。

**⇒ 订正后的正确表述**：
1. **JSTM 真机客户端同样不给"我播完了"的回执** ⇒ **JSTM 也必须由服务端自定节拍**（现实现：`SC_20010` 之后 **2.5 秒/回合、自续期**）；
2. **CXEngine 与 JSTM 在"服务端不等客户端"这一点上是相似的**
   （CXEngine：**客户端**自己推回合；JSTM：**服务端**自己推）⇒ **「回合节奏所有权相反」不成立**；
3. **「照搬会丢掉 `CS_20014` 节流」这一理由作废**（**没有节流可丢**）；
4. 「CXEngine 回合 FSM 不可移植」的**真正理由**改为 5 条**有字段证据**的理由（见 §四）。

**⇒ 「JSTM 是回合制」这一判定不受影响**（不依赖 `20014`）—— 该判定依据 `battle_flow.md` 与 `SC_20010/20012/20013/20020` 的存在。

### 3.3 那么 CXEngine 回合 FSM 为何仍不可照搬（★ 5 条字段级理由）

| # | 理由 | 证据 |
|---|---|---|
| 1 | **战场结构表达不了一回合** | JSTM `SC_20010` 含**阵法**（`atk_formation_type/lev`、`def_formation_type/lev`）、**回合波次**（`round_wave`/`wave_max`/`wave_no`）；CXEngine `BattleMT:Serialize()` 只有 `{id, team_type, pos_id}` |
| 2 | **单位状态是每回合重推的** | JSTM `SC_20013.summon_play[]` 每回合带 `hp_max/hp/anger/is_auto/animate_res[]/skills[]/specials[]`；CXEngine **无任何单位重推机制**，buff 状态**完全不上线** |
| 3 | **线格式与协议哲学不同** | JSTM `[u32 BE len][u16 BE cmd][二进制字段序]` vs CXEngine `[LE u32][LE u32][JSON]` |
| 4 | **JSTM 有 CXEngine 没有的整块子系统** | 观战 / 战斗录像 / 自动战斗 / 客户端侧演算校验（§2.3） |
| 5 | **安全模型与内容不可复用** | CXEngine 有状态与重复提交校验但**无归属校验、无限速、无超时**；`assets/doc/*` 的数值**全部是《梦幻西游》数值** |

**⇒ 可借鉴的只剩 3 条机制**：①**服务端摇随机、结果下发**；②**`stub` 里的状态机校验**（全 ready 才执行）；
③**"先快照收件人再结算"**（防结算中 actor 被移除导致漏发）。

---

## 四、五项目战斗模型（逐文件表）

> 格式：`文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因`

### 4.1 YZXY / CXEngine（★ 回合制结构参考，评分 5）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `scripts/combat/combat_system.lua` | `BattleMT:new` | 战斗对象 `{id, actors, cmds, state, turn, type}` | ✅ 适合 | 战斗对象字段极简、状态机与数据分离得当 |
| 同上 | `BattleMT:NextTurn()` | `turn++`、清 ready、AutoCommand、`process_turn_buffs` | ⚠ 部分 | ★ **"回合切换统一入口"（把 buff 结算挂这里）是正确做法**；但**客户端也调它** ⇒ 双端各自推进**不可照搬** |
| 同上 | `BattleMT:Serialize/Deserialize` | 战场全量出网（NPC 带 props、玩家不带） | ✅ 适合 | ★ **"NPC 带全量、玩家只带位次"**的差分思想 ⇒ JSTM 可照此裁剪 `SC_20010` 体量 |
| 同上 | `BattleMT:CheckEnd()` | 一方全死 | ✅ 适合 | 胜负判定简单可靠；⚠ 它返回"某方全死"而非"谁赢" ⇒ JSTM 的 `SC_20020{result}` 显式给结果**更清晰** |
| `scripts/combat/server/combat_system.lua` | `handle_turn_commands(battle)` | **①先快照 `send_pids`（防中途被移除）②按 `CalcSpeed()` 降序 ③逐条 `process_turn_command` ④收集 `all_skills` 发每人** | ✅ **强适合** | ★ ★ **两个细节特别值得学**：①**先快照收件人**；②**按速度排序的回合内出手顺序**是最经典回合制做法（JSTM `SC_20012` 也需要出手顺序） |
| `scripts/combat/server/combat_system.lua` | `stub[PTO_C2S_COMBAT_CMD]` | 校验 `battle.state == BATTLE_TURN_STAND_BY` + `master.PROP_TURN_READY`；全 ready 才执行 | ⚠ 部分 | **状态 + 重复提交校验有了**（比其余 handler 严谨）；但**不校验 `req.master` 是否属该连接**、无限速、无回合超时 ⇒ JSTM 必须补 |
| `scripts/combat/client/combat_system.lua` | `combat_system_update()` | 逐技能播 → 播完 `NextTurn()`（**本地**） | ⛔ **不适合** | 🔴 **不能让客户端决定回合推进**：真机客户端连"播完了"都不发（`CS_20014` 未发）⇒ 服务端将完全失去节拍控制（无超时、无法处理慢客户端/挂机） |
| `scripts/combat/skill.lua` | `base_using_skill(battle, skill)` | **服务端算 / 客户端播，同一函数用 `IsServer()` 分叉** | ✅ 适合（结构） | ★ **同一份代码承载"权威计算"与"表现重放"**，是理解整个战斗同步的钥匙；**但客户端分支不能有"推进回合"这类决策** |
| `scripts/combat/skill.lua` | `init_cskill/cskill_to_skill` | 出网表示 `{id,tid,turn,master,targets,effects[{target_id,combo,hp_deltas,life_state}],success}` | ✅ 适合 | ★ **"服务端下发可重放的战斗结果"的完整数据契约**；可逐项对照 JSTM `SC_20012/20013` 字段集 |
| `scripts/combat/skill.lua` | `process_turn_command` | 建 skill 实例、**目标失效则随机换敌**、封禁校验（`PROP_COMBAT_SKILL_BAN_ATK/SPELL`） | ✅ 适合 | ★ **"目标失效自动换目标"**是回合制必须处理的边界；**封禁校验**展示 buff 如何影响指令合法性 |
| `scripts/combat/skill.lua` | `battle_get_group_kill_targets` | 主目标 + 从同阵营存活者按速度排序随机补 `group_kill-1` 个 | ✅ 适合 | **群攻目标选择**完整实现 |
| `scripts/combat/buff.lua` | `actor_buff_next_turn` / `process_turn_buffs` | buff 存 `__actors_buffs__[actor_id][buff_id]`；`NextTurn` 统一递减、归零 `BuffOnEnd` | ✅ 适合 | ★ **与技能同构的"表 + `buff/<id>.lua` 回调 + 回合统一结算"**骨架，JSTM 可直接套 |
| `scripts/combat/buff.lua` + 同步（无文件） | — | **buff 无任何下行消息，靠客户端重放同一判定逻辑** | ⛔ **不适合** | 🔴 **这是 CXEngine 战斗同步最大的设计缺陷**。JSTM **本来就有**载体（`magic_list`）⇒ **只学"服务端摇随机"，绝不要学"buff 不上线"** |
| `scripts/combat/buff/1.lua`, `11.lua` | `BuffOnStart`/`BuffOnEnd` | **纯客户端动画**（服务端分支都没有） | ⚠ | buff 表混装了"表现"与"逻辑"两类 ⇒ JSTM 应分开 |
| `assets/doc/combat.md` / `roadmap.md` | 全文 | 设计文档；`roadmap.md` 含"**战斗逻辑挪到服务端**"等**未完成项** | ⚠ 部分 | ★ **它自己列出的 TODO 就是这套架构的短板清单** ⇒ 提醒 JSTM：**"服务端权威"必须一开始就做对**；⚠ 数值全是《梦幻西游》⇒ **不可用** |
| `assets/doc/server.md` | 全文 | 服务端战斗流程 + 状态机 mermaid + **特殊情况清单**（NPC 可被击飞销毁 / 唯一玩家逃跑则战斗结束 / BB 被击飞移出 / BB 被召唤加入） | ✅ 适合 | ★ **"文档与实现对齐"的好例子**；特殊情况清单建议 JSTM 立项时逐条确认 |

### 4.2 Survive（★ 实时制；战斗校验缺失是红线）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `gameserver/skill.lua` | — | 技能定义与结算 | ⚠ 部分 | 与 JSTM **回合制**不同（Survive 是实时）⇒ 结构不通用 |
| `gameserver/buff.lua` / `bufffunction.lua` | — | buff 运行时 | ⚠ 部分 | 同上 |
| `gameserver/battlebag.lua` | `Save()` | 位于**被注释掉的代码块**中（非活代码） | ⛔ | 战斗包不持久化 |
| **整体** | — | ⛔ **战斗层零距离/角度/目标数/能量校验**（客户端给目标列表，服务端只滤队友 + 死人） | ⛔ **红线** | 🔴 **照抄等于开放全图秒杀**（`R1_SUPPLEMENT.md` §4.1 已列为致命缺陷） |
| 数值 | — | ⛔ 伤害系数/战力/塔防系数**都是编的** | ⛔ | 数值全部不可用 |

**⇒ Survive 对 JSTM 战斗的价值**：**仅"移动/位置校验"与"掉线交 AI 托管"**（`D15`），**战斗本体不可参考**。

### 4.3 侠客行（★ 回合制 + 客户端权威 ⇒ 反面教材）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/FightLayer.h:221-233` | 8 个布尔/计数标志 | **真正的战斗状态机**（`m_isPlayer`/`m_isPlayerEnd`/`m_curMonster`/`m_lastMonsterEnd`…） | ⚠ 部分 | 「玩家回合 → 怪物逐个回合 → 交还玩家」用标志位表达，**最简可用**；但无超时、无断线处理 |
| `Classes/FightLayer.cpp:212-224, 410-432` | `onTimer` 行动条 | **手动 10 秒 / 自动 2 秒**超时托管（超时执行上次技能或普攻） | ✅ 适合 | ★ **挂机体验的核心**：回合超时自动托管 ⇒ **JSTM 可参考其"双档超时"设计**（JSTM 当前是固定 2.5 s 自续期） |
| `Classes/Monster.cpp:103` / `CameraPlayer::beAttack` | — | `hurtvalue = attack <= defense ? 1 : attack - defense`（**三处相同公式**） | ✅ 适合（公式） | ★ **`max(1, 攻击 − 防御)`** 保底减法，是最简可用伤害式；JSTM 可作基线并加暴击/系数层 |
| `Classes/Skill.cpp:76` | `Skill::beUse` | 技能伤害 `m_baseAttack + 30 * m_grade` | ✅ 适合（公式） | ★ 线性成长公式极简清晰 |
| `Classes/Skill.cpp:90` | `getUseMana` | 蓝耗 `m_baseMana + m_grade * 10` | ✅ 适合 | 与伤害同构，便于服务端复算校验 |
| `Classes/SkillLayer.cpp:63-64` | `onBtnUpClickCallback` | 升级价 `m_baseupGlod + 50 * grade` | ✅ 适合 | 四条线性公式是一套自洽数值起点 |
| `Classes/ShareData.h:232-245` | `PlayerAtk_Msg` / `MonsterAtk_Msg` | **消息里根本没有伤害/血量字段** | ⛔ **不适合** | 🔴 **服务端只按 `dest` 定向转发，无任何权威结算** |
| `Classes/FightLayer.cpp:512-513` | `GetPlayerData().addGlod/addExp` | **经验金币本地累加**，再由 `CameraPlayer::SaveGameData` 经 `DBDao<PlayerInfo>` 直连 MySQL 回写 | ⛔ **不适合** | 🔴 **奖励在客户端结算** |
| `Classes/FightLayer.cpp:510-521` | 结算分支 | **失败/逃跑也照发已击杀怪物的奖励**（`endFunc` 无条件发奖） | ⛔ | 明确 bug |
| `Classes/AppDelegate.cpp:175-184` | `LoadSkillAnimation` | 两个等长数组 `skill[8]` + `nums[8]={16,14,9,9,10,17,15,9}` 批量预热 8 个技能动画 | ✅ 适合 | ★ **"两个等长数组 + 循环预热"**与**序列帧长条图切分**（`width/num`）值得参考 |
| `Classes/Monster.cpp:72-92` | `initMonsterAnimation` | 按 `frames` 载入 `<Name><i>.png`，`setDelayPerUnit(0.15)`，`RepeatForever` | ✅ 适合 | ★ **"属性文件 + 帧序号图片 + 固定帧间隔"**是最省事的怪物接入方式 |
| `Classes/GameLogicLayer.cpp:155-208` | `randomMeetMonster` | **遇敌概率/数量/种类全由客户端随机决定** | ⛔ | 🔴 JSTM 必须服务端决定 |
| `Classes/HurtValueLayer.cpp` | `createWithInfo(pos, value)` | 伤害飘字 | ✅ 适合 | 飘字数值**来自本地计算**（不是消息字段）；JSTM 应改为用 `SC_20013.hp` 差值驱动飘字 |
| 数值表（R2 已补全） | 8 技能 `.att` + 10 怪物 `.att` | 技能 `baseattack` 100~350 / `basemana` 全 50；怪物 `speed` **10/10 全是 5** | ✅ 适合（数值校准） | ★ 10 怪 ↔ Task1~10 一一对应（`battle.md` 附录 C.3）⇒ 可作为 JSTM 前 10 级战斗数值对照 |

### 4.4 空空西游（★ 实时制 + 服务端权威；有完整战斗实体模型）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `app/domain/area/areaLogic.js`（33 KB） | `AreaLogic` 基类 + 按 `areaKind` 选子类 | `attack / multiAttack / killReward / diedInArea / reviveInArea / finishFight` | ✅ **强适合（设计）** | ★ **策略模式：按 `areaKind` 选不同 AreaLogic** 是本项目最优雅的设计之一 ⇒ JSTM 可按"PVE/PVP/副本/世界BOSS"分策略 |
| 同上 | `attack(attacker,target,skill)` / `multiAttack` | 攻击判定、伤害、仇恨、掉落 | ✅ 强适合 | 战斗核心；⚠ 但它是**实时**判定，JSTM 回合制需改造 |
| `app/domain/entity/character.js` | `attack / getAvailableSkill / checkSkillAvailable / hit / reduceHp / reduceMp / addBuff / removeBuff / addEnemy / forEachEnemy / forgetEnemy / increaseHateFor / getMostHater` | **战斗实体：技能冷却 + 命中 + 仇恨表 + 敌人表** | ✅ **强适合** | ★ **仇恨表（`increaseHateFor`/`getMostHater`）+ 敌人表**是 JSTM 目前缺的（JSTM 的 `SC_20013.magic_play[].order` 已暗示出手顺序，但无仇恨模型） |
| `app/domain/fightskill.js` + `buff.js` | `judge/attack/coolDownTime`、`addBuff/removeBuff` | 技能判定 + BUFF | ✅ 适合 | 战斗系统骨架；⚠ 无"回合"概念 |
| `app/servers/area/handler/fightHandler.js` | `useSkillAttack(msg, session, next)` / `fightPrize` | **技能攻击入口** | ✅ 强适合 | 与 JSTM 的 `CS_20002` 入口同职责 |
| `app/services/fightService.js`（10 KB） | `enterFight/exitFight/readyFight/changeFight/cancelFight/prepareFight/finishFight/pushFighter/pushCompetitor/pushPlayerToArea` | **竞技场匹配与流程** | ✅ 适合 | ★ **PVP 全流程**：JSTM 若做 PVP 可参考其"准备/换位/取消"状态集 |
| `app/ai/service/brainService.js` | `getBrain(type, bb)` / `registerBrain` | 注册表机制；**`type` 非 `autoFight`/`player` 一律当 `tiger`** | ⚠ 部分 | ⚠ **"所有怪共用一套脑"是偷懒** ⇒ JSTM 应支持多脑（JSTM 有 `_config_mon_data` 857 KB 怪物数据，值得做得更好） |
| `app/ai/action/tryAttack.js` | `doAction` | 无 `curSkill` / 目标消失 / 目标变更 → `RES_FAIL`；`character.attack` 返回 SUCCESS/MISS → `RES_SUCCESS` | ✅ 强适合 | 行为树叶子节点标准写法 |
| `app/ai/**` + `app/patrol/**` 的 `test/` | `tigerTest/autoFightTest/...` | 用 mocha 对 AI/巡逻做**单元测试** | ✅ **强适合** | ★ **行为树与巡逻状态机是最适合写单测的部分** ⇒ JSTM 应配套单测 |
| `app/domain/map/mobzone.js` | `MobZone.update/generateMobs` | `nextGenTime` 节流；每次刷 `genCount=3` 只到 `limit`（默认 10） | ✅ 强适合 | 刷怪区标准实现（1 秒分频 + 5 秒节流）⇒ 与 JSTM 的 `quest_spawn.py` 可对照 |

### 4.5 大圣归来（❌ 无战斗系统）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| （服务端） | — | `manipulationData` 8 个分支**无任何战斗消息**；`game` 表有 `blood` 但**从不更新** | ⛔ | 数据层与网络层都不支撑战斗 |
| `Classes/Player.cpp:128-135` | `attackAction()` | **定义了但全 `Classes/` 无任何调用点**（R2 已闭合） | ⛔ | 攻击动画是死代码 |
| `Classes/Player.h:14-15` | `state{ FREE, WALK, ATTACK, DEAD }` | **`DEAD` 零引用**；`ATTACK` 仅由无人调用的 `attackAction()` 设置 | ⛔ | 战斗/死亡状态机完全未实现 |
| **⇒ 结论** | — | **大圣归来在战斗维度信息量为 0** | ⛔ | 仅可作"有 `blood` 字段却从不更新的反面" |

---

## 五、★ 逐字段映射：JSTM `SC_20013` ← 参考项目字段

| JSTM 字段 | CXEngine 对应 | 侠客行对应 | 空空西游对应 | 结论 |
|---|---|---|---|---|
| `magic_play[].target_id` / `source_id` | `effects[].target_id` + `master` | ❌（无） | `attack(attacker,target,skill)` 的参数 | JSTM 更完整 |
| `magic_play[].hit:i8` | `success`（bool） | ❌ | `character.hit` 返回值 | ★ **JSTM 的 `hit:i8`（带符号）比 CXEngine 的 bool 表达力强**（可表达暴击/MISS/格挡档位？【待验证】） |
| `magic_play[].hp_max` / `hp` | `hp_deltas`（**只给差值**） | ❌ | `reduceHp` 后推送 | ★ **JSTM 给绝对值 + 上限，CXEngine 只给 delta** ⇒ JSTM 更抗丢包 |
| `magic_play[].is_target_die` | `life_state` | ❌ | `diedInArea` | ✅ 语义等价 |
| `magic_list[].duration` / `fold` / `change_hp` | ⛔ **无对应（buff 不上线）** | ❌ | `addBuff/removeBuff`（有状态但无剩余回合字段） | ★ **JSTM 独有且更完整** ⇒ **无需向参考项目学 buff 同步** |
| `summon_play[]`（16 字段，每回合重推） | ⛔ 无 | ❌ | ⚠ 属性推送（`onHpMp`） | ★ **JSTM 独有** |
| `order_list[]`（出手顺序） | ✅ `CalcSpeed()` 降序（**在服务端算，不下发顺序表**） | ⚠ 行动条 `onTimer` | ⚠ 行为树 | ★ **CXEngine 的"按速度降序"是唯一可学的顺序策略**；JSTM 需确认 `order_list` 是否按速度 |
| `round_wave` / `wave_no` | ❌ | ❌ | ❌ | JSTM 独有（多波次） |
| 阵法（`*_formation_type/lev`） | ❌ | ❌ | ❌ | JSTM 独有 |
| 战斗超时 | ⛔ 文档说 30 s、代码无实现 | ✅ **手动 10 s / 自动 2 s 双档托管** | ❌ | ★ **唯一可学的超时设计来自侠客行** |
| 仇恨模型 | ❌ | ❌ | ✅ `increaseHateFor`/`getMostHater` | ★ **唯一可学的仇恨模型来自空空西游** |
| 掉落 | 有（`assets/doc` 清单，数值不可用） | ⛔ **无掉落表** | ✅ `dropItem`/`_dropEquipment` | 参考空空西游 |
| 怪物 AI | ⚠ `AutoCommand` 50% 普攻/50% 法术随机 | ⚠ 固定套路 | ✅ 行为树 + 注册表 | 参考空空西游 |

---

## 六、★ 战斗缺口（对 JSTM）

| # | 缺口 | 现状证据 | 参考依据 | 建议 | 优先级 |
|---|---|---|---|---|---|
| **B1** | **回合超时无实现** | JSTM 有 `SC_20013.time:u8` 字段；服务端 2.5 s/回合**自续期**（不检查客户端） | ★ 侠客行 **手动 10 s / 自动 2 s 双档托管** | 加超时状态机：超时→自动执行"上次技能或普攻"；双档（手动/自动战斗）| **P1** |
| **B2** | **出手顺序策略未确认** | `SC_20013.order_list[]` 存在；未见按速度排序代码 | ★ CXEngine `handle_turn_commands` **按 `CalcSpeed()` 降序** | 明确 `order_list` 生成规则（速度降序 + 平手规则），并写进文档 | **P1** |
| **B3** | **无仇恨模型** | 未见 `hate`/`aggro` 相关列或函数 | ★ 空空西游 `increaseHateFor`/`getMostHater` + 仇恨表 | 若 JSTM 怪物需选目标，加仇恨表（内存即可，不必落库） | P2 |
| **B4** | **buff 承载已具备但 `magic_list` 填充度未知** | JSTM 有 `magic_list` 6 字段契约；`battle.py:305` mock 发**空** `magic_list` | CXEngine **反面**（buff 不上线） | ★ **好消息**：实测客户端对空 `magic_list` 宽容 ⇒ **buff 可后置实现**，不被空表阻塞 | P2 |
| **B5** | **战斗未落库** | `missions` 等 11 表**无战斗表**；战斗态仅在 `battle.py` 内存 | 空空西游 `dao/mapping/*Sync.js` 有 `fight*` 相关 | 若需断线续战/录像回放，加 `battle_log` / `battle_record` 表（JSTM 有 `20025–20030` 录像 CMD ⇒ 可能已有内存实现） | P2 |
| **B6** | **战斗反作弊** | JSTM 有 `10601/10610` 客户端侧演算校验通道 | ⛔ Survive 零校验（红线）；⚠ CXEngine 有状态+重复提交校验但**无归属校验/无限速/无超时** | 补：①`req.master` 归属校验 ②每回合指令限速 ③伤害上限合理性校验 | **P1** |
| **B7** | **副本/爬塔与战斗的协议文件命名易误导** | `jstm_1.4.9/battle_protocol.md` 覆盖 `13000~13099`（**实为副本/爬塔/成就**） | — | 建议把该文件改名为 `gameplay_protocol.md` 或加显著注记 | P3（文档级） |
| **B8** | **PVP 全流程未实现** | 未见 PVP CMD 实现 | 空空西游 `fightService`（10 个方法） | 若做 PVP，参考其 `enterFight/readyFight/changeFight/cancelFight/prepareFight` 状态集 | P2 |

---

## 七、五项目战斗反例清单（JSTM 明确不要学）

| # | 反例 | 来源 | 后果 |
|---|---|---|---|
| 1 | **战斗层零距离/角度/目标数/能量校验** | Survive | 🔴 **照抄 = 开放全图秒杀** |
| 2 | **客户端本地结算伤害 + 本地发奖** | 侠客行 | 可任意刷金币经验；`PlayerAtk_Msg` 连伤害字段都没有 |
| 3 | **失败/逃跑也照发奖** | 侠客行 `endFunc` 无条件发奖 | 可刷奖励 |
| 4 | **遇敌概率/数量/种类由客户端决定** | 侠客行 `randomMeetMonster` | 可控制遇敌、拉怪 |
| 5 | **buff 完全不上线，靠客户端重放判定** | CXEngine | 客户端可伪造 buff 状态 |
| 6 | **客户端本地推进回合** | CXEngine `combat_system_update → NextTurn()` | 服务端失去节拍控制（无超时、无法处理挂机/慢客户端） |
| 7 | **回合超时只在文档里**（30 s 倒计时无代码） | CXEngine `assets/doc/combat.md` | 回合卡死 |
| 8 | **`BattleMT` 双向引用无一致性保护** | CXEngine（`GetNotReadyActors` 写错变量名） | 建议 JSTM 单向：battle 持 participant 列表，角色只存 `battle_id` |
| 9 | **所有怪共用一套脑** | 空空西游 `brainService.getBrain` | AI 无差异化 |
| 10 | **buff 表混装"表现"与"逻辑"** | CXEngine `buff/1.lua`（纯客户端动画也占 buff 位） | 服务端空跑无逻辑 buff |
| 11 | **战斗数值是编的** | Survive（伤害系数/战力/塔防） | 不可用 |
| 12 | **战斗数值是《梦幻西游》的** | CXEngine `assets/doc/{combat,roadmap}.md` | 不可用 |
| 13 | **有 `blood` 字段却从不更新** | 大圣归来 `game.blood` | 数据层假象 |

---

## 八、★★ R6 待传播的更正清单（本矩阵发现）

| # | 文档 | 位置 | 过时表述 | 更正为 | 依据 |
|---|---|---|---|---|---|
| 1 | `comparison/architecture_matrix.md` | §三 前提裁决表 | 「✅ **客户端 `CS_20014` ACK 后才推进**」「**会丢掉 ACK 节流**」 | ★ **`CS_20011`/`CS_20014` 真机从未发出** ⇒ 无 ACK 节流可丢；**JSTM 由服务端自定节拍**；「回合节奏所有权相反」**不成立** | `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1；`yzxy/battle.md:523-548` |
| 2 | `comparison/architecture_matrix.md` | §一 战斗行 | 「推进权必须在服务端（客户端 `CS_20014` ACK 后才推）」 | 同 #1；且**不可移植的真正理由是 5 条字段级理由**（§3.3） | 同上 |
| 3 | `R1_SUPPLEMENT.md` | §二 更正 1 | 「JSTM 服务端 `SC_20012/20013` → 客户端 `CS_20014` ACK 后才推进」 | 同 #1 | 同上 |
| 4 | `FINAL_SERVER_ARCHITECTURE.md` | `:63/:66/:73/:74/:92/:98` | 6 处「`CS_20014` 回执 / ACK 节流」 | 同 #1 | 同上 |
| 5 | `FINAL_SERVER_ARCHITECTURE.md` | `:63` | 引 `battle_chain_verified.md` 为「✅ 决定性结果」 | ⚠ 该文档描述的是**我们自己的 `mock_server.py` 实现**，**不是真机行为** ⇒ 降级为「mock 实现记录」 | `yzxy/architecture.md:28-35` |
| 6 | 全库 | — | 把 `jstm_1.4.9/battle_protocol.md` 当作战斗协议 | ⚠ 其 `13000~13099` 段**实为副本/爬塔/成就**；真实战斗在 `20000~20099` | §2.1 |

---

## 九、【待验证】/【未知】

| 项 | 状态 |
|---|---|
| `CS_20014` 为何真机不发 | 【未读到】权威文档明确写「**客户端为何不发 20014 尚未定位**」⇒ 保持未知，**不做推测** |
| `magic_list` 是"每回合全量"还是"增量" | 【未读到】**明确记载"在本工作区不可取证"** ⇒ JSTM 按"每回合全量重列"实现（`duration` 每回合必变、与 `summon_play` 重推同构） |
| `order_list[]` 是否按速度降序生成 | 【待验证】 |
| `SC_20013.time:u8` 的具体语义（回合时限 or 时长） | 【待验证】 |
| `hit:i8` 的取值域（暴击/MISS/格挡？） | 【待验证】 |
| JSTM 是否有内存战斗录像（对应 `20025–20030`） | 【未读到】`battle.py` 未展读 |
| CXEngine `ACTION_*` 状态机内部实现 | 【未读到】`common/src/actor/action.cpp`（21 KB） |
| CXEngine `stub[PTO_C2S_COMBAT_CMD]` 在玩家掉线时是否 `RemoveActor` | 【待验证】代码层面可确认**无超时逻辑**；`combat_system_battle_on_actor_leave` 是 `EndBattle`（不卡但整场结束） |
| 空空西游 `fightService` 是否部署 | 【已确认】**`servers.json` 无 `fight` 进程**；竞技场实际由 `manager/handler/fightHandler.js` + `fightService.js` 承担 |

---

## 十、一句话结论

> **JSTM 的战斗系统在"字段集完整度"上远超全部 5 个参考项目**：
> 它有**每回合全量单位重推**（`summon_play[]` 16 字段）、**buff 逐条上线**（`magic_list` 6 字段含 `duration`/`fold`/`change_hp`）、
> **伤害绝对值 + 上限**（`hp`/`hp_max`）、**多波次与阵法**、以及参考项目都没有的**观战 / 录像 / 自动战斗 / 客户端侧演算校验**四套子系统。
> **CXEngine 恰恰在这两点上是弱的一方**（buff 完全不上线、客户端本地推回合）⇒ **它的回合 FSM「不可移植」不是因为没有 ACK 节流，而是因为字段集与系统边界对不上**。
>
> **★ 本矩阵最重要的一条是"更正"而非"发现"**：
> 共享集成文档（`architecture_matrix.md` / `R1_SUPPLEMENT.md` / `FINAL_SERVER_ARCHITECTURE.md`，共 **9 处**）仍在宣称
> 「JSTM 有 `CS_20014` ACK 节流」——**该结论的真实依据是我们自己 mock 的实现，而真机客户端 `CS_20011`/`CS_20014` 从未发出**。
> 订正早在 `yzxy/` 目录内完成（3 处引用 + 字节码权威源），**但从未传播到集成文档** ⇒ **这正是 R3/R5 同一类"更正不传播"问题的第三次复现**。
>
> **可借鉴清单（共 8 条，全部为机制/结构，均需自研）**：
> ①CXEngine **按速度降序定回合内出手顺序**；②CXEngine **先快照收件人再结算**；③CXEngine **服务端摇随机、结果下发**；
> ④CXEngine **目标失效自动换目标** + **封禁校验**；⑤CXEngine `buff` 的"**表 + 按 id 脚本回调 + 回合统一结算**"骨架；
> ⑥**侠客行的"手动 10 s / 自动 2 s 双档超时托管"**（JSTM 唯一可学的超时设计）；⑦**空空西游的仇恨表 + 敌人表**（JSTM 唯一可学的仇恨模型）；
> ⑧**空空西游按 `areaKind` 选 `AreaLogic` 的策略模式** + **战斗实体的单测习惯**。
