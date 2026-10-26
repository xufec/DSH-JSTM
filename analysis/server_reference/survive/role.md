# Survive 角色系统审计（逐文件 · 类/函数级）

> 对象：`groupserver/groupplayer.lua`、`groupserver/{attr,bag,item,skill,equip,mail,friends,achievement,everydaytask,everydaysignin,homeisland,gm,util}.lua`、`gameserver/{gameplayer,avatar,attr,battlebag,skill,buff}.lua`、`common/name2idx.lua`
> 状态标记：【已确认】【待验证】【未知】；方法：`zipfile` 按需读取原文（**未修改任何文件**）
> 对照目标：**JSTM**（角色/属性/等级/EXP/背包/装备/仓库/商城 已实现；SQLite 持久化）

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| 角色被切成**两个对象** | **`groupserver/groupplayer.lua`（持久角色 / 全局逻辑）** 与 **`gameserver/gameplayer.lua`（场景实体，继承 `avatar.lua`）** —— 玩家进图时由 group 序列化 `PackPlayer` 传给 game 重建 | 【已确认】 |
| 角色权限归属 | 背包/装备/技能/签到/任务/成就/邮件/**属性计算**都在 **group**；game 只持有**战斗态副本** | 【已确认】 |
| 属性表示 | **数字下标数组**（`Name2idx` 分配 1..32），不是字符串键；同步时写 `u8 下标 + u32 值` | 【已确认】 |
| 属性白名单同步 | game 侧 `attr2view = {level, life, maxlife}` 只同步这 3 个到视野；其余只发本人 | 【已确认】 |
| 属性总表 | `common/name2idx.lua` 共 **32 项**（含 `endidx` 哨兵），其中 **`attr_db_save = attack-1` ⇒ 只持久化前 23 项**（R7 更正：原写"前 31 项"是笔误，`attack` 为第 24 项，同文 `:158` 已自证为 23） | 【已确认】 |
| 属性计算入口 | `groupplayer.lua:CalAttr(notifyclient, withoutweapon)`（**一次性重算全部派生属性**）+ `OnLevelUp(level)` | 【已确认】 |
| 货币 | 用**属性下标**当货币：`4001=贝壳(shell)` `4002=珍珠(pearl)` `4003=精元(soul)` `4004=经验(exp)` `4005=体力(stamina)`；`Util.NewRes` 按 id 分流 | 【已确认】 |
| 背包 | 60 格（`size=60`）；**1=fashion, 2=weapon, 3=belt, 4=cloth**，**5~10=战斗背包**，11~60=普通背包 | 【已确认】 |
| 装备 | 4 部位 + **强化等级（attr[3] 高 16 位）+ 升星等级（attr[3] 低 16 位）+ 4 个宝石孔（attr[1] 高/低、attr[2] 高/低）** | 【已确认】 |
| 角色数据存哪 | redis hash **`chaid:<chaid>`**，字段 `nickname/avatarid/chainfo/bag/skills/everydaysign/everydaytask/achievement/mail`（详见 `database.md`） | 【已确认】 |
| 对 JSTM 的价值 | **「属性下标化 + 白名单视野同步 + 一次全量重算 CalAttr + 强化/升星用位打包」四点高度可借鉴；代码不可复制** | 【已确认】 |

---

## 二、两个角色对象

### 2.1 `groupserver/groupplayer.lua`（持久角色 / 权威）【已确认】

**模块级注册表（4 张全局表 + 1 个 id 池）**
| 名称 | 结构 | 用途 |
|---|---|---|
| `id2player` | `[groupsession] = ply` | 按 group 会话取玩家（**所有 `CMD_CG_*` 处理的第一步**） |
| `actname2player` | `[actname] = ply` | 登录去重 / 断线重连判定 |
| `chaid2player` | `[chaid] = ply` | 好友、GM、组队等按角色 id 查 |
| `nickname2player` | `[nickname] = ply` | 聊天、好友按昵称查 |
| `freeidx` | `IdMgr.New(4096)` | groupsession 分配器 |

**`player` 对象的字段（`player:new` / `NewPlayer` / `PlayerLogin` 赋值）**
| 字段 | 类型 | 含义 | 赋值处 |
|---|---|---|---|
| `groupsession` | number | group 会话 id（**同时是 `id2player` 的键**） | `player:new` |
| `actname` | string | 账号名 | `NewPlayer` |
| `chaid` | number | 角色 id（0 = 未创角） | `PlayerLogin` / `CMD_CG_CREATE` |
| `nickname` | string | 昵称（唯一，见 §6.3 查重） | `PlayerLogin` / `CMD_CG_CREATE` |
| `avatarid` | number | 外观 id（存的是 `uint8`，见 `CMD_CG_CREATE` 的 `rpk:Read_uint8()`） | 同上 |
| `attr` | `groupserver/attr` | 属性容器 | `Attr.New():Init(ply, cjson.decode(chainfo))` |
| `bag` | `groupserver/bag` | 背包（60 格） | `Bag.New():Init(ply, ...)` |
| `skills` | `groupserver/skill` | 技能表（id → level） | `Skill.New():Init(ply, ...)` |
| `sign` | `everydaysignin` | 每日签到 | `Sign.New(ply, signdata)` |
| `task` | `everydaytask` | 每日任务 | `Task.New(ply, taskdata)` |
| `achieve` | `achievement` | 成就（含在线奖励） | `Achi.New(ply, achieve)` |
| `mail` | `mail` | 邮件（base64 存储） | `Mail.New(ply, mails)` |
| `gatesession` | `{gate=, sessionid=}` | 当前 gate 绑定；`nil` = 客户端已断 | `Gate.Bind` |
| `gamesession` | `{game=, sessionid=}` | 当前 game 绑定；`nil` = 不在场景 | `Game.Bind` |
| `mapinstance` | number \| object | 所在场景实例（或 `206` 生存赛标记） | `Map.EnterMap` |
| `status` | 常量 | 角色状态机（见 §7） | 多处 |
| `lgTimer` | timer handle | 登出定时器（60s） | `LogOutTimer:Register` |
| `ReqTick` | tick | 排队进图的时间戳 | `ReqQue:Push` |

**函数清单**
| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `NewPlayer(actname)` | 分配 `groupsession`，写 `id2player` + `actname2player` | ✅ 适合（思想） | 明确的"连接 → 玩家对象"单点构造，JSTM 已有 session，可对应 |
| `ReleasePlayer(ply)` | 从 4 张表摘除 + `ReleaseIdx` | ⚠️ 部分 | 摘除顺序正确；但**不落库**（依赖各处 `DbSave`），JSTM 应显式 flush |
| `GetPlayerBySessionId/Actname/GetPlyByNickname/GetPlyByChaid` | 4 个查表函数 | ✅ 适合 | 多索引（id/账号/角色 id/昵称）是必要的；JSTM 目前若只有单一索引会不够用 |
| `player:Send2Client(wpk)` | 包前加 `u16 cmd`、包后加 `u16 count=1` + `u32 gatesession` → 发 gate | ✅ 适合（思想） | 见 `network.md` |
| `player:Send2Game(wpk)` | 包尾加 `u32 gamesession` → 发 game | ✅ 适合（思想） | 同上 |
| `player:NotifyBeginPlay()` | `status=playing`；组 `CMD_GC_BEGINPLY`：`chaid + avatarid + nickname + attr:OnBegPly + bag:OnBegPly + skills:OnBegPly + sign:OnBegPly + os.time()`；最后 `achieve:OnBeginPlay()` | ✅ 适合（思想） | **"一次性把角色全量快照发给客户端"**是登录必备，JSTM 已有等价逻辑；值得对照检查**是否漏发**（Survive 这份包里**没有 task/achievement 全量**，是有意还是遗漏【待验证】） |
| `player:NotifyCreate()` | `status=createcha`，返回 `{true, groupsession, "create"}` 给 gate | ✅ 适合 | 创角分流 |
| `player:NotifyCreateError(msg)` | `CMD_GC_CREATE_ERROR` + 文案 | ✅ 适合 | 创角失败要有回执 |
| `player:AddExp(exp)` | 循环 `TableExperience[level].Experience` 扣减 → `OnLevelUp(level+1)` | ✅ 适合 | 与 JSTM 已实现的 EXP/等级一致思路；⚠️ **`Experience==0` 视为满级 break**，需确认 JSTM 表末行是否也如此 |
| `player:OnLevelUp(level,notifyclient)` | **差分升级**：用 `TableRole[cur_level]` 与 `TableRole[level]` 的差值算出 `*_base`（玩家手动加点部分），再 `Set` 新等级基础值 + 保留差值；`potential_point` 累加；`achieve:OnEvent(ACHI_LEVEL_UP)`；最后 `CalAttr` | ⚠️ 部分适合 | **"升级时保留手动加点"**这个差分算法是对的且必须（否则加点会被重置）；但实现把 6 个属性逐个手写 4 遍（读旧-算差-读新-写），**易错且难维护**，JSTM 应写成循环/数据驱动 |
| `player:CalAttr(notifyclient, withoutweapon)` | **全量重算派生属性**：读 `power/endurance/constitution/agile/lucky/accurate` 基础 + 武器/腰带/衣服的 `TableEquipment` + `TableIntensify[强化]` + `TableRising_Star[升星]` + 4 宝石 `TableStone`；再 `Set(attack/defencse/maxlife/dodge/crit/hit)`；`notifyclient` 则 `Update2Client` | ✅ **高度适合（思想）** | **"任何装备/加点/强化变化后一次性重算所有派生属性"**是最不容易出 bug 的做法（对比增量修改）；JSTM 的属性系统若目前是增量式，建议改为**事件驱动的全量重算**。⚠️ 注意 `CalAttr` **不更新 `life`**（当前血量）⇒ 最大生命变化后可能出现 `life > maxlife`，只在 `Add(...,maxlife)` 处夹取【待验证】 |
| `getStone(equip,pos)` / `fetchStones(stones,equip)` | 从 `equip.attr[1]` 高/低、`attr[2]` 高/低取 4 个宝石 id | ✅ 适合 | 位打包读取，见 §5 |
| `_checkDuplicateName()` → `checkDuplicateName(nickname)` | **闭包 + `Lock`**：`Lock:Lock()` → `hmget nickname <name>` → 有值则失败 → 否则 `hmset nickname <name> 1` → `Unlock` | ✅ 适合（思想） | **"昵称占用单独建索引 + 加锁防并发重名"**是必须的（JSTM 若只在角色表里 `SELECT` 查重，会有竞态）；JSTM 用 SQLite 可用 `UNIQUE` 约束 + 事务替代，**更简单更正确** |

### 2.2 `gameserver/gameplayer.lua`（场景实体）【已确认】

`player` 的 metatable 是 `Avatar.New()` 产生的对象 ⇒ **`gameplayer` 继承 `avatar`**（`local player = Avatar.New()` 后 `player:new` 又设自己的 `__index = self`，形成**两层继承：gameplayer → avatar 实例 → avatar metatable**）。

| 字段 | 含义 | 与 group 侧的关系 |
|---|---|---|
| `id` | **`mapid<<16 \| 图内idx`** ⇒ game 内唯一 | 由 `maplogic:entermap` 分配；**即 gamesession** |
| `groupsession` | group 会话 id（**number，不是表**） | 回包给 group 时当"地址"用 |
| `gatesession` | `{sock=, sessionid=, gate=}` | 由 `Gate.Bind` 绑定 |
| `actname` / `nickname` / `avatid` / `fashion` / `weapon` | 外观与展示 | 来自 `PackPlayer` |
| `attr` | `gameserver/attr`（**战斗态属性副本**） | 来自 `PackPlayer` 的 `ply.attr:Pack2Game()` |
| `skillmgr` | `Skill.New(v.skills)` | 来自 `PackPlayer` 的 `ply.skills:GetSkills()` |
| `battleitems` | `gameserver/battlebag`（6 格） | 来自 `PackPlayer` 的 `ply.bag:FetchBattleItem()` |
| `pos` / `dir` / `speed` | 位置/朝向/速度（默认 speed=27，即每格耗时） | 进图时由 `maplogic` 给坐标 |
| `path` | `{cur=, path=[[x,y]...]}` 当前路径 | `avatar:Mov` 设置 |
| `see_radius` | 5（**未在代码中被使用**） | — |
| `view_obj` / `watch_me` | 我看到的 / 看到我的（AOI 回调维护） | — |
| `aoi_obj` | `Aoi.create_obj(self)` | — |
| `buff` | `Buff.New(self)` | — |
| `teamid` | 队伍 id（默认 `bit32.band(id,0xFFFF)`） | 用于 `skill.UseSkill` 的敌我判定 |
| `isPlayer` / `isNPC` / `isMon` | 玩法内角色分类标记 | `maplogic` 设置 |
| `canUseSkill` | 是否允许放技能（开局倒计时期间为 nil） | `maplogic` 设置 |
| `robot` | AI 控制器（掉线托管 / NPC） | `robot.lua` |
| `Pickable` | 是否是可直接拾取的掉落物 | `maplogic:CreateDrop` |
| `invisible` | 隐身（buff 3002 设置） | `bufffunction.lua` |
| `stick` | 定身（buff 3101 Blackout 设置） | `bufffunction.lua` |
| `oldspeed` | 变速 buff 前的速度备份 | `bufffunction.lua` |

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `player:Init(id,avatid,map,nickname,actname,groupsession,attr,skillmgr,pos,dir,teamid,items)` | 逐字段赋值 + `Attr.New` + `Aoi.create_obj` + `Buff.New` + `Bag.New():Init` | ⚠️ 部分 | 12 个位置参数**极易传错**（`maplogic` 调用处确实有注释复述参数顺序）；JSTM 应用 `dataclass`/关键字参数 |
| `player:Send2Client(wpk)` | 与 group 版**同样**的包尾附加模式 | ✅ 适合（思想） | 保持一致 |
| `player:on_entermap()` | 组 `CMD_SC_ENTERMAP`：`maptype + attr:on_entermap + battleitems:on_entermap + map.logic:OnEnterMap(wpk) + self.id`；发给**本人**（`count=1` 的广播形式） | ✅ 适合 | **进图包应含"地图类型 + 全属性 + 战斗背包 + 玩法数据（倒计时）+ 自己的实体 id"** —— JSTM 的 `scene_init_protocol.md` 可逐项对照是否齐全 |
| `player:ReConnect(maptype)` | 停 AI → `on_entermap()` → 遍历 `view_obj` 逐个 `SendEnterSee(v)` 重建视野 | ✅ **高度适合（缺口）** | 这正是 JSTM 目前**缺**的能力：断线/切场景后如何重建"我看到的其他人" |
| 背包相关（见 §5） | — | — | — |

⚠️ **`gameplayer.lua` 里 `Require` 了 `Buff`/`Attr`/`Skill`/`Bag` 但**只有部分被用**；文件顶部还有**大段注释掉的 `battleitems` 早期实现**（61 行）——说明背包曾从 game 侧迁到 group 侧【已确认】。

---

## 三、属性系统：`common/name2idx.lua`（32 项全表）【已确认】

| 下标 | 名称 | 中文 | 分类 | 是否落库 |
|---|---|---|---|---|
| 1 | `level` | 角色等级 | 基础 | ✅ |
| 2 | `exp` | 经验值 | 基础 | ✅ |
| 3 | `power` | 力量 | 加点 | ✅ |
| 4 | `endurance` | 耐力 | 加点 | ✅ |
| 5 | `constitution` | 体质 | 加点 | ✅ |
| 6 | `agile` | 敏捷 | 加点 | ✅ |
| 7 | `lucky` | 幸运 | 加点 | ✅ |
| 8 | `accurate` | 精准 | 加点 | ✅ |
| 9 | `movement_speed` | 移动速度 | 其它 | ✅ |
| 10 | `shell` | 贝币 | 货币 | ✅ |
| 11 | `pearl` | 珍珠 | 货币 | ✅ |
| 12 | `soul` | 武魂 | 货币 | ✅ |
| 13 | `action_force` | 行动力 | 其它 | ✅ |
| 14 | `potential_point` | 可用潜能点 | 加点 | ✅ |
| 15 | `fishing_start` | 钓鱼开始时间 | 家园 | ✅ |
| 16 | `gather_start` | 采集开始时间 | 家园 | ✅ |
| 17 | `sit_start` | 打坐开始时间 | 家园 | ✅ |
| 18 | `spve_last_award` | 上次领奖关卡 | 单人副本 | ✅ |
| 19 | `spve_history_max` | 历史最高关卡 | 单人副本 | ✅ |
| 20 | `spve_today_max` | 今日关卡（未提交） | 单人副本 | ✅ |
| 21 | `introduce_step` | 新手引导步骤 | 引导 | ✅ |
| 22 | `online_award` | 在线奖励计时 | 活动 | ✅ |
| 23 | `stamina` | 体力 | 数值 | ✅ |
| 24 | `attack` | 攻击 | **派生** | ❌（`attr_db_save = attack-1 = 23`） |
| 25 | `defencse` | 防御（**拼写错误，原文如此**） | **派生** | ❌ |
| 26 | `life` | 当前生命 | 战斗态 | ❌ |
| 27 | `maxlife` | 最大生命 | **派生** | ❌ |
| 28 | `dodge` | 闪避 | **派生** | ❌ |
| 29 | `crit` | 暴击 | **派生** | ❌ |
| 30 | `hit` | 命中 | **派生** | ❌ |
| 31 | `anger` | 怒气 | 未使用 | ❌ |
| 32 | `combat_power` | 战斗力 | **未实现**（只出现在 5PVE 的初始 attr 表里，值为 0） | ❌ |
| 33 | `suffer_plusrate` | 伤害加成倍率（**浮点**，如 1.5） | 战斗 | ❌ |

**关键机制**【已确认】：
- `attr_db_save = nameidx.attack - 1 = 23` ⇒ **`groupserver/attr.lua:DbStr()` 只编码前 23 项**（基础+加点+养成计时），派生属性不落库、每次登录 `CalAttr` 重算。**这是完全正确的做法，强烈值得 JSTM 借鉴。**
- `MaxIdx = endidx - 1 = 32`；`idxname` 是反查表（`Name(idx)`）。
- ⚠️ **`suffer_plusrate` 是浮点数**，但属性在网络上以 `u32` 传输（`Write_uint32`）、在 `lua/` 侧 `Set` 直存 ⇒ **跨进程传输会截断为整数**（`1.5 → 1`）。它只在 **game 进程内部**被设置使用（`Buff3201_OnBegin` 设 1.5），所以未暴露问题，但**属隐患**。【待验证】

### 3.1 `groupserver/attr.lua` vs `gameserver/attr.lua` 差异对照【已确认】

| 能力 | group 侧 | game 侧 | 说明 |
|---|---|---|---|
| 初始化 | `Init(owner,baseinfo)`：遍历 `1..MaxIdx`，缺失补 0 | `Init(avatar,baseinfo)`：`pairs` 拷贝，然后 **`life = maxlife`** | game 侧出生即满血 |
| `Set` | `if idx > 0 and self.attr[idx] ~= val then` → 置值 + `flag[idx]` + **`dbchange=true`** | `if self.attr[idx] then` → 置值 + `flag[idx]` | ⚠️ **game 侧 `Set` 对"表中不存在的 key"静默失效**（不会新建）；group 侧允许任何 ≥1 的 idx |
| `Add/Sub` | 有（带 `0xFFFFFFFF` 上溢夹取、`max` 上限） | 有（同上） | 逻辑基本一致（互有拷贝） |
| `MoreOrEq(name,val)` | **有**（仅 group 需要"是否够钱/够材料"判断） | 无 | |
| `Pack(wpk,modfy)` | **有**：`modfy=false` 全量、`true` 只发 flag 命中的；先写 `u8` 占位、循环后 `Rewrite_uint8` 回填条数 | 无（改用 `on_entermap`/`on_entersee`） | |
| `Update2Client()` | `CMD_GC_ATTRUPDATE` + 增量 Pack + 清 flag | 无（game 用 `NotifyUpdate`） | |
| `on_entermap(wpk)` | 无 | **有**：`pairs(self.attr)` 全量写 `u8 idx + u32 val` | 进图全量 |
| `on_entersee(wpk)` | 无 | **有**：只写 `attr2view = {level, life, maxlife}` 白名单 | **★ 视野白名单** |
| `NotifyUpdate()` | 无 | **有**：**发两份包**——`wpk2view`（白名单）给视野、`wpk2self`（全部）给自己 | **★ 同一次变更按可见性拆两个包** |
| `DbStr/DbSave` | 有：`hmset chaid:<chaid> chainfo <cjson 前23项>`，只在 `dbchange` 时写 | 无 | |
| `Pack2Game()` | **有**：整表浅拷贝给 game | 无 | 角色数据跨进程传递 |
| `ClearFlag()` | 有 | 无 | 登录后清 flag，避免立刻推一大堆增量 |

**★ 三处高度值得 JSTM 借鉴**：
1. **`attr2view` 白名单**（只把 `level/life/maxlife` 同步给视野中的其他玩家）——这是**隐私/带宽/反外挂**三重收益的最小实现。JSTM 若把全属性广播给同屏玩家，应立刻收敛。
2. **"一次变更两个包"**（视野包 + 自身包）——避免"给自己发全场属性"或"给全场发私密属性"。
3. **`flag` 脏标记 + 批量推送**（`Update2Client` 只在有变更时发包，发完清 flag）。

---

## 四、属性计算公式（`CalAttr` 全文还原）【已确认】

```
基础派生（来自加点）：
  attack_base   = floor(power        * 2.5)
  defencse_base = floor(endurance    * 2)
  maxlife_base  = floor(constitution * 22.5)
  dodge_base    = floor(agile        * 0.02)
  crit_base     = floor(lucky        * 0.01)   + TableRole[level]["Crit"]
  hit_base      = floor(accurate     * 0.1)

装备加成（TableEquipment）：
  武器(pos2) → attack_plus
  腰带(pos3) → maxlife_plus
  衣服(pos4) → defencse_plus
  每件再 +
    TableIntensify[equip:GetAttrHigh(3)]   -- 强化等级（高16位）
    TableRising_Star[equip:GetAttrLow(3)]  -- 升星等级（低16位）

宝石加成（最多 4 颗，TableStone）：
  每颗先按"百分比"放大 attack/defencse/maxlife：
    attack_plus   = floor((attack_plus*100   + tb.Attack ) / 100)
    defencse_plus = floor((defencse_plus*100 + tb.Defense) / 100)
    maxlife_plus  = floor((maxlife_plus*100  + tb.Life   ) / 100)
  dodge/crit/hit 则是"加法式百分比"：
    dodge_plus += floor((dodge_base*100 + tb.Dodge) / 100)   ← 注意基数用的是 base
    crit_plus  += floor((crit_base*100  + tb.Crit ) / 100)
    hit_plus   += floor((hit_base*100   + tb.Hit  ) / 100)

最终：
  attack   = attack_base   + attack_plus
  defencse = defencse_base + defencse_plus
  maxlife  = maxlife_base  + maxlife_plus
  dodge    = dodge_base    + dodge_plus
  crit     = crit_base     + crit_plus
  hit      = hit_base      + hit_plus
```

| 观察 | 结论 | 状态 |
|---|---|---|
| `attack_base` 用的是**潜能点分配后的** `power`（`OnLevelUp` 已把基础值+差值写入） | 正确 | 【已确认】 |
| 宝石对 attack/defence/life 的作用是**乘算叠加**（`(v*100+rate)/100` 链式），对 dodge/crit/hit 是**基于 base 的加算** | 不一致，**疑似设计缺陷**（同一张 `TableStone` 的 `Attack` 与 `Dodge` 语义不同） | 【已确认】（不一致）/【待验证】（是否有意） |
| `CalAttr` 末尾有 `print(self.attr:Get("attack"))` / `print(maxlife)` | **生产路径打日志** | 【已确认】 |
| `combat_power`（战斗力）**从未被计算** | 表里有字段但无实现 | 【已确认】 |
| `hit` 在战斗结算中**从未被使用**（`CalDamage` 只用 `agile` 判闪避、`crit` 判暴击） | 属性存在但无消费方 | 【已确认】 |

**★ 对 JSTM 的建议**：这套公式**只是一份可运行示例，不是《绝世唐门》的权威公式**（`FINAL_SERVER_ARCHITECTURE.md` 已确认「战力/技能公式【未知】」）。
⇒ **只能借鉴"结构"**（基础×系数 → 加装备 → 加宝石 → 汇总），**系数一个都不能抄**；JSTM 的公式必须由 APK 数据/客户端表现反推（**APK > 参考项目**）。

---

## 五、背包 / 装备 / 宝石（`groupserver/bag.lua` + `groupserver/item.lua`）

### 5.1 槽位布局【已确认】

```
pos 1 = fashion（时装）
pos 2 = weapon （武器）
pos 3 = belt   （腰带）
pos 4 = cloth  （衣服）
pos 5 ~ 10 = 战斗背包（进副本带的 6 格，上限每格 5 个）
pos 11 ~ 60 = 普通背包（size = 60）
```

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `bag:Init(ply,bag)` | 有存档：`self.bag = {size=bag.size}`，逐格 `Item.New(v.id,v.count,v.attr)`；无存档：`{size=60}` | ✅ 适合 | 与 JSTM 已实现的背包模型一致 |
| `bag:GetItemId/GetBagItem/GetItemCount/GetItemAttr/SetBagItem/SetItemAttr` | 基础读写；**每个写操作都置 `self.flag[pos]=true` 与 `self.dbchange=true`** | ✅ 适合（思想） | 脏标记统一在访问器里置位，避免漏标 |
| `findbagpos(self,id)` / `find_battle_item_pos(self,id)` | 找空位或**同 id 可堆叠格**；11~60 / 5~10 两段不同 | ⚠️ 部分 | 逻辑可用但**重复代码**（两段几乎相同，仅区间不同） |
| `bag:AddItem(id,count,attr)` | 有 attr（装备）→ 找空格；无 attr → 先找同 id 堆叠，`count+count>65535` 夹取 | ✅ 适合 | |
| `bag:AddItems(items)` | **两阶段**：先为每个 item 找 `fitpos`（装备找唯一空格、可堆叠找同 id）并收集到 `bagpos`，全部成功后才写入 | ✅ **高度适合（思想）** | **"先全部校验、再全部落地"**避免"发一半奖励失败"的经典问题；JSTM 的发奖逻辑应照此做原子性检查 |
| `bag:Swap(pos1,pos2)` | 校验 `<=10` 的两格不能互换；`pos2<=4` 时校验 `TableItem[item1.id].Item_Type == pos2` 且 `Use_level <= level`；`pos2<=10` 时要求 `Tag == 0`；同 id 非装备**合并**；衣服/武器/腰带/衣服 4 位变动时**返回 `true,"recalattr"`** 触发 `ply:CalAttr(true)` | ✅ **高度适合（思想）** | **"换装返回一个信号让上层重算属性"**与 §3 的 `CalAttr` 配套，是干净的解耦；JSTM 的装备穿戴应同样"改数据 → 发信号重算" |
| `bag:LoadBattleItem(pos)` / `UnLoadBattleItem(pos)` | 把普通格 ↔ 战斗格搬移，战斗格上限 5 | ✅ 适合 | 出入副本带道具，JSTM 若做副本需要 |
| `bag:FetchBattleItem()` | 返回 `{{pos,id,count},...}` 给 game | ✅ 适合 | 跨进程传递战斗背包的最小表示 |
| `bag:RemItem(pos,id,count)` | 按 `id` 全局搜最后一个匹配格（`for i=0,size`）→ 扣减 → 归零则 `nil` | ⚠️ 部分 | `for i=0,size` **从 0 开始且遍历到 size**（越界一位，弱 bug）【已确认】；且"按 id 搜索取**最后**一个"语义奇怪 |
| `bag:NotifyUpdate()` | 只打包 `flag` 命中的格；`CMD_GC_BAGUPDATE`；`item:Pack` / `Item.PackEmpty`；发完清 flag | ✅ 适合 | 增量同步 |
| `bag:SynBattleItem()` | 显式同步 5~10 六格（`Write_uint8(6)` + 6 次） | ✅ 适合 | 离图/回主城后同步战斗背包 |
| `bag:PeekInfo(wpk,beg,end)` | 查看他人装备（好友详情用） | ⚠️ | 条件写成 `if end_index > beg_index or ... then return false end` ⇒ **正常情况（end>beg）反而直接返回 false**，是**逻辑反了的 bug**【已确认】 |
| `bag:DbStr()` / `Save()` | `{size, [i]={id,count,attr?}}` → `cjson.encode` → `hmset chaid:<chaid> bag <json>`（仅 `dbchange`） | ✅ 适合 | |
| `bag:OnBegPly(wpk)` | 全量打包（`size` + 条数占位 + 逐格 `v:Pack`） | ✅ 适合 | 登录快照 |

### 5.2 物品对象 `groupserver/item.lua`【已确认】

| 函数 | 机制 | 说明 |
|---|---|---|
| `item:new(id,count,attr)` | `{id, count, attr}`；`attr` 是**数组**（下标 1..N） | |
| `item:Pack(wpk)` | `u16 id + u16 count + u8 条数 + (u8 下标 + u32 值)*` | `attr` 为 nil 时**连条数都不写**（`wpos` 占位写 0 后不回填）⇒ 与 `PackEmpty` 的格式不一致【已确认】 |
| `GetAttr(idxs)` / `SetAttr(idxs,vals)` | 批量按索引读写 | |
| `GetAttrHigh(idx)` / `GetAttrLow(idx)` | `attr[idx]` 的**高 16 位 / 低 16 位** | ★ 位打包 |
| `SetAttrHigh(idx,val)` / `SetAttrLow(idx,val)` | 高位：`band(attr,0xFFFF) \| (val<<16)`；低位：`band(attr,0xFFFF0000) + val` | ★ 位打包 |
| `PackEmpty(wpk)` | `u16 0 + u16 0 + u8 0` | |

**★ 位打包（bit-packing）总结【已确认】**
| 槽位 | 高 16 位 | 低 16 位 |
|---|---|---|
| `attr[3]` | **强化等级**（`TableIntensify`） | **升星等级**（`TableRising_Star`，上限 60） |
| `attr[1]` | **宝石孔 1** | **宝石孔 2** |
| `attr[2]` | **宝石孔 3** | **宝石孔 4** |

**评价**：**思想（用一个 u32 装两个 u16）在带宽上有效，但可读性差、易错**（`groupplayer.lua:getStone` 的 4 个分支与 `equip.lua:setStone` 必须严格对应，写反一处就错位）。
⇒ JSTM（SQLite，不缺列）**不建议采用位打包**，应显式字段（`strengthen_level` / `star_level` / `gem1..gem4`）。

### 5.3 装备操作 `groupserver/equip.lua`（**只有 MsgHandler，没有 module**）【已确认】

| 命令 | 函数体逻辑 | 关键校验 | 状态 |
|---|---|---|---|
| `CMD_CG_EQUIP_UPRADE` | 强化：`strengthen_lev = GetAttrHigh(3)+1` → 查 `TableIntensify[lev].Money` → 扣 `shell` → `SetAttrHigh(3,lev)`；**当 `strengthen_lev == use_level + 5` 时 `equip.id = equip.id + 1`（升阶换 id）** → `bag:SetBagItem` + `NotifyUpdate` + `Save` + `CalAttr(true)` + `attr:DbSave` + `task:OnEvent(EQUIPUPGRADE)` + `achieve:OnEvent(ACHI_EQUIP_UPGRADE,lev)` | `pos ∈ [2,4]`；`Item_Type` 合法；`strengthen_lev <= ply_level`；`MoreOrEq("shell",need)`；**进阶时要求 `TableItem[equip.id+1]` 存在** | 【已确认】 |
| `CMD_CG_EQUIP_ADDSTAR` | 升星：`star = GetAttrLow(3)`；`star == 60` 上限 → `SetAttrLow(3,star+1)` + 扣 `shell` + `CalAttr` + 任务/成就 | 同上 | 【已确认】 |
| `CMD_CG_EQUIP_INSET` | 镶嵌：要求 `getStone(equip,stone_pos) == 0`（该孔为空）、`TableStone[stoneid].Seat == eq_pos`（**宝石有部位限制**）→ `bag:RemItem(nil,stoneid,1)` → `setStone` | 部位匹配 | 【已确认】 |
| `CMD_CG_EQUIP_UNINSET` | 卸下：`getStone` 取出 id → `bag:AddItem(stoneid,1)` 成功后 `setStone(...,0)` | — | 【已确认】 |
| `CMD_CG_STONE_COMPOSITE` | 宝石合成：`TableStone_Synthesis[tb1.Stone_Level].Price` 扣 shell，3 合 1 出 `Next_Level`；`all==1` 则按 `floor(count/3)` 批量 | `bagitem.id == id`（防伪造） | 【已确认】 |
| `CMD_CG_COMPOSITE` | 通用合成：读 `TableSynthesis[id]`，按 `Material1..N` 解析 `"id:count"`，**校验客户端传来的 `size == #materials` 且每个格子 id/数量匹配** → `Util.NewRes(ply,id,1)` → 逐个 `RemItem` → 扣 `Synthesis_Price` | 材料全量校验 | ✅ **值得借鉴**：先校验全部材料再执行（与 `bag:AddItems` 同一思路） |

⚠️ **`equip.lua` 全文件的 `print()` 调试（如 `print("CMD_CG_STONE_COMPOSITE5")`）留在生产路径**【已确认】。
⚠️ **`equip.lua` 的 `use_level` 校验只用于强化上限，宝石镶嵌不校验角色等级**（只校验部位）【已确认】。

---

## 六、技能 / 签到 / 任务 / 成就 / 邮件 / 好友

### 6.1 `groupserver/skill.lua`（角色技能面板）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `skills:Init(ply,sks)` | `sks` 是 `{{id,level},...}` → `self.skills[id]=level` | ✅ 适合 | 与 JSTM 已实现的技能模型一致 |
| `skills:OnBegPly(wpk)` | `u16 占位 + (u16 id + u8 level)*` | ✅ 适合 | 登录快照 |
| `skills:GetSkills()` | 反序列化成 `{{id,level},...}` 给 game | ✅ 适合 | 跨进程传递 |
| `skills:DbStr()/Save()` | `cjson.encode({{id,level},...})` → `hmset chaid:<chaid> skills` | ✅ 适合 | |
| `skills:Upgrade(skillid)` | `sklev+1` → `Tableskill_Upgrade[sklev].Money` 扣 shell → `CMD_GC_SKILLUPDATE` | ✅ 适合 | |
| `skills:Unlock(skillid)` | 查 `TableSkill[id].Soul` 扣 `soul` → `self.skills[skillid]=1` → `CMD_GC_ADDSKILL` | ✅ 适合 | **"技能用武魂(soul)解锁、用贝壳(shell)升级"**是双货币设计 |

⚠️ `skills:Upgrade` 里若 `Tableskill_Upgrade[sklev]` 为 nil（已满级），会**跳过扣钱但照样升级**（`if tb then ... end` 后无条件 `self.skills[skillid] = sklev`）【已确认】——满级后可无限升级且免费。**这是必须避免的漏洞**。

### 6.2 `groupserver/everydaysignin.lua`（每日签到）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `everydaysignin:new(owner,data)` | 读 `{count,lastreset,lastsign}`；`daycount = CTimeUtil.GetDayCountOfMon(year,mon)`；构造时 `CheckReset()` | ✅ 适合（思想） | |
| `Sign()` | `DiffDay(lastsign, now) ~= 0 and count < daycount` → `count+1`，`lastsign = GetTSWeeHour()`（**当日 5:00 的时间戳**），`Update2Client + DbSave` | ✅ 适合（思想） | ★ **「以每日 5:00 为分界线」**用 `GetTSWeeHour()` 统一表达，比"当天 0 点"更符合运营习惯；JSTM 的每日重置应显式定义"几点算新的一天" |
| `CheckReset(notify)` | `DiffMon(lastreset, GetMonFDay())`（**跨月**判定）→ 归零 | ⚠️ 部分 | 只有跨月重置；`DiffMon` 用 `GetDayCountOfMon(上月)` 比较**天数差**，在 2 月/大月边界是否精确**待验证** |
| `OnBegPly(wpk)` / `Update2Client()` | `u8 daycount + u8 count + u8 今日是否可签` | ✅ 适合 | |
| `DbStr/DbSave` | `hmset chaid:<chaid> everydaysign <json>` | ✅ 适合 | |

### 6.3 `groupserver/everydaytask.lua`（每日任务）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `taskType` | 8 类：`PVE5/PVP5/WUDIDONG/GUAJI/COMPOSE/SKILLUPGRADE/EQUIPUPGRADE/ADDSTAR` | ✅ 适合（分类） | **任务类型 ≈ 客户端事件类型**，与 JSTM 的 `task_data_model.md` 目标类型可对照 |
| 模块加载时 | 把 `TableDay_Task[k].Award` 字符串 `"5812:8,4001:1000"` **预解析**成 `{{id,count},...}` | ✅ 适合（思想） | ★ **配置表字符串在启动时一次性解析成结构**，避免运行时反复 `SplitString`；但**它直接改写了 `TableDay_Task` 全局表**（副作用）⚠️ |
| `everydaytask:new(owner,data)` | 无存档 → 建 8 个 `{type,counter=0,awarded=false}`；`CheckReset` 若重置则立刻 `DbSave` | ✅ 适合 | |
| `CheckReset(notifyAttr)` | `DiffDay(lastreset, os.time()) ~= 0` → 清零 + **`attr:Set("stamina",100)`** + `attr:DbSave` | ✅ 适合 | **每日任务重置顺便重置体力**（把日重置集中在一处） |
| `Pack(wpk)` | `u8 8 + (u8 counter + u8 awarded)*8` | ✅ 适合 | |
| `OnEvent(eventType)` | `counter < TableDay_Task[event] .Number` → `counter+1`（夹到上限）+ `DbSave` | ⚠️ 部分 | **每次事件都同步写库**（`DbSave` 是 async 但仍是一次 redis 往返）⇒ 高频事件（击杀）会打爆 DB；JSTM 应**内存累积 + 定时/登出落库**。⚠️ 且**用 `eventType` 直接当 `TableDay_Task` 的 key**，即"配置表主键 = 事件类型"，耦合偏紧 |
| `GetAward(type)` | 校验 `awarded` 与 `counter >= Number` → 遍历 `tb.Award` 逐个 `Util.NewRes` → `awarded=true` + 一系列 `DbSave` + `CMD_GC_EVERTDAYTASK_AWARD` | ✅ 适合（流程） | 领奖四件套 `attr:Update2Client/attr:DbSave/bag:NotifyUpdate/bag:Save/task:DbSave` 说明**每个模块各自负责自己的落库与推送** ⇒ 干净但**冗余**；JSTM 可用统一的 `flush(role)` |

### 6.4 `groupserver/achievement.lua`（成就 + 在线奖励）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `achi_type` | 12 类：单人PVE/装备强化/升星/镶嵌/加点/升级/5PVE/5PVP/合成/挂机/装备等级/击杀BOSS | ✅ 适合（分类） | |
| `achiv_check` | **`[成就id] = function(evtype,param) return 条件 end`** 的判定函数表 | ✅ **高度适合（思想）** | ★ **"成就即 (事件类型, 参数) → 谓词"**：把"达成条件"完全数据化在代码里，新增成就 = 加一个谓词。比"在业务代码里到处 if 判成就"干净得多 |
| `achievement:new(owner,data)` | 把成就分成 `achiv_open`（未达成）与 `achiv_close`（已达成）；无存档时 **16~21 号（在线奖励）预设为 close**，其余 open | ⚠️ 部分 | 用"成就号区间"表达"在线奖励"（16~21）**硬编码区间**，脆弱 |
| `achievement:OnEvent(evtype,param)` | 遍历 `achiv_open` → 命中 `achiv_check[id]` → 移入 `achiv_close` + `DbSave` + **`break`（一次事件只推一个成就）** | ⚠️ 部分 | `break` 意味着**一次事件最多完成一个成就**；若要一次完成多个会被漏掉【待验证】是否与配置有意配合 |
| `achievement:DbStr/DbSave` | `{[id]={achived=0/1,awarded=n}}` → json → `hmset chaid:<chaid> achievement` | ✅ 适合 | |
| `CMD_CG_ACHIEVE_AWARD` | 校验 `awarded`、在线奖励的 `Time_Interval` 间隔 → `awarded=1` → 遍历 `tb.Award` 发奖 → 更新 `online_award`（id 21 则置 0 表示领完）+ 一系列 `DbSave` + 重发成就列表 | ⚠️ 部分 | ⚠️ `if awarded then return end` —— **`awarded` 是未定义全局**（永远为 nil）⇒ 这句**防重复领取的判断失效**（真正的防重靠后面的 `v.awarded = 1`，但**在同一 key 重复请求时会先置 1 再被后面的逻辑判掉**？实际是 `v.awarded` 未参与前置判断）⇒ **潜在重复领奖漏洞**，JSTM 必须用显式 `if v.awarded == 1 then return end`【已确认】 |
| `achievement:OnBeginPlay()` | 若 `attr:Get("online_award") ~= 0` 则推成就列表 | ⚠️ | 条件语义不明（`online_award` 是**时间戳**，`~=0` 恒真除非被置 0） |

### 6.5 `groupserver/mail.lua`（邮件）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `mailModule:new(ply,dbdata)` | `o.list = dbdata or {}`；`o.counter = 1` | ✅ 适合 | |
| `mailModule:SendMail(mail)` | `id = string.format("%d:%d", os.time(), self.counter)`；`counter++`；`list[id]=mail`；`Save()`；再数未读数发 `CMD_GC_NEWMAIL` | ⚠️ 部分 | ⚠️ **`counter` 每次构造都从 1 开始** ⇒ 同一秒内重启/重登会**覆盖同 id 邮件**（`os.time():counter` 冲突）。JSTM 应用 UUID 或 DB 自增 |
| `mailModule:SendMailList()` | `CMD_GC_MAILLIST` + 条数占位 + 逐封 `Pack(id,mail,wpk)` | ⚠️ | ⚠️ `wpk:Rewrite_uint8(wpos,c)` 但**占位写的是 `Write_uint16(0)`** ⇒ **回填位置/宽度不匹配**（后 8 位垃圾）【已确认】 |
| `Pack(id,mail,wpk)` | `string id + string title + string content + u8 readed + u8 附件数 + (u16 item + u16 count)*` | ✅ 适合 | |
| `mailModule:DbStr()` | **`CBase64.encode(cjson.encode(list))`** | ⚠️ 部分 | ★ 思想：**"JSON 里嵌套引号/换行会破坏 redis 协议，故 base64 一层"**是可理解的防御；但**根因是"把结构化数据拼进 redis 文本协议"**。JSTM 用 SQLite 存储 ⇒ **完全不需要 base64** |
| `CMD_CG_MAILMARKREAD` | 若有附件 → 逐个 `Util.NewRes` + `bag:NotifyUpdate/Save` + `attr:Update2Client/DbSave`；然后 `list[id]=nil` + `Save` | ⚠️ 部分 | ⚠️ **"标记已读"顺手把邮件删了**（`list[id]=nil`）——命名与语义不符；且**附件与正文同一次操作**，无法"只读不领" |
| `CMD_CG_MAILDELETE` / `CMD_CG_MAILGETATTACH` | **被整段注释掉** | — | 功能缺失【已确认】 |
| `Mail.SendMail(ply,mail)` | 导出函数（供 GM 用） | ✅ | |
| **无离线邮件投递** | 邮件只能发给**在线**玩家（`GetPlyByNickname`），`notiserver` 未实现 ⇒ **离线邮件/全服邮件缺失** | ❌ | JSTM 若要做系统邮件，必须自己设计离线信箱 |

### 6.6 `groupserver/friends.lua`（好友/黑名单）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `friends:Init(ply,data)` | 默认 `{friends={},black={}}`；遍历 `data` 按 `v.black` 分流 | ⚠️ | 循环 `for k,v in pairs(data)` **对 `data.friends`/`data.black` 这两个数组本身也会迭代**（`v.black` 为 nil → 被当 friend），属**冗余/可疑** |
| `friends:Add(chaid,nickname,_type)` | `black` 类型要求先有好友（拉黑）；否则按 `nickname` 或 `chaid` 查在线玩家 → 存 `{chaid,nickname,avatarid,level}` | ⚠️ **只能加在线玩家** | **离线加好友不可用**（`GetPlyByChaid` 只查在线表）⇒ 设计缺陷；JSTM 应查库 |
| `friends:PeekInfo(chaid)` | 查在线好友 → 回包 `CMD_GC_FRIEND_INFO`（昵称/avatarid/**全属性 `attr:Pack(wpk)`**/前 4 格装备 `bag:PeekInfo(wpk,1,4)`）→ 若等级变化则 `DbSave` | ⚠️ **隐私问题** | **把对方全部属性发给好友查看**（`attr:Pack` 是全量！不是 `attr2view` 白名单）⇒ JSTM 若做"查看他人"，**必须限定字段** |
| `friends:Pack(wpk)` | `u16 占位（条数）` + 黑名单在前 + 好友在后，每条 `u32 chaid + string nickname + u16 avatarid + u8 level + u8 是否黑名单 + u8 是否在线` | ⚠️ | 见下 bug |
| `friends:DbStr/DbSave` | `{friends={...},black={...}}` → json → `hmset chaid:<chaid> friends` | ⚠️ | ⚠️ **`DbSave` 用的是 `self.owner.chaid`，而 `friends:Init` 设的是 `self.ply`（不是 `self.owner`）** ⇒ **`self.owner` 为 nil，`DbSave` 必然报错**【已确认】。⇒ **好友持久化实际是坏的** |

---

## 七、角色状态机

### 7.1 groupserver 侧（`groupserver/groupserver.lua` 顶部的**全局常量**）【已确认】

```lua
createcha  = 1   creating  = 2   loading   = 3   playing   = 4
releasing  = 5   entermap  = 6   leavingmap= 7   queueing  = 8
```
⚠️ 这些是**全局变量**（没有 `local`），任何模块都能改；且 `groupplayer.lua` 里又用了一个**未定义的 `creating`**（`CMD_CG_CREATE` 中 `ply.status = creating`）——它靠 `groupserver.lua` 先被加载才存在【已确认】。

| 状态迁移 | 触发 | 说明 |
|---|---|---|
| `nil → loading` | `PlayerLogin` 读库前 | 读库中 |
| `loading → playing` | 读库成功 + `NotifyBeginPlay` | |
| `loading → createcha` | 无 `chainfo`/`bag`/`skills` 等字段 | 需要创角 |
| `createcha → creating` | `CMD_CG_CREATE` 进入 | 创角中 |
| `creating → playing` | 创角成功 | |
| `playing → entermap` | `CMD_CG_ENTERMAP` | |
| `entermap → playing` | `Map.EnterMap` 成功 | 注：**失败时也回到 playing** |
| `playing → queueing` | `ReqQue:Push` | 多人副本排队 |
| `playing → leavingmap` | `CMD_CG_LEAVEMAP` | |
| 任意 → `releasing` | gate 掉线且状态是 `verifying`/`login2group` | 等 RPC 回来自清理 |

**★ 借鉴点**：**显式状态机 + 每个 `CMD_CG_*` 入口先校验 status**（例如 `CMD_CG_ENTERMAP` 会分别打日志区分"无 gatesession / 已在地图 / 状态非法"）。
⇒ JSTM 若有"同一玩家重复进图/进图途中又发包"的问题，这套校验值得照搬**思想**（用枚举 + 前置断言）。

### 7.2 gateserver 侧（`gateserver/gateplayer.lua`，**local 常量**）【已确认】
```lua
verifying=1  login2group=2  createcha=3  playing=4  releasing=5
```
⚠️ **与 group 侧的状态常量定义在不同文件、编号含义不同**（gate 的 3 是创角界面，group 的 3 是 loading）。⇒ **两套状态机各自独立**，靠消息而非共享状态同步。**这是本项目一个明显的可读性隐患**，JSTM 应统一状态枚举。

---

## 八、登录 / 创角 / 进图流程（端到端）【已确认】

```
① 客户端 → gate:  CMD_CA_LOGIN(type, actname)
② gate: Player.NewGatePly(sock)（分配 gatesession）；status=verifying
        Db.CommandSync("get " .. actname) → chaid（无则 0）
        IsVaild(player) 复检（人可能已断线）
③ gate → group:  RPC PlayerLogin(actname, chaid, gatesession)
④ group PlayerLogin：
        已有 actname2player 且无 gatesession ⇒ 断线重连分支（见 network.md §8）
        否则 NewPlayer(actname)；Gate.Bind(gate, ply, gatesession)
        chaid == 0 ⇒ 返回 {true, groupsession, "create"}
        否则 hmget chaid:<chaid> nickname avatarid chainfo bag skills
                                  everydaysign everydaytask achievement mail
             任一关键字段缺失 ⇒ 返回创角
             否则逐个 Cjson.decode 构造 attr/bag/skills/sign/task/achieve/mail
                   ply:CalAttr()（**重算派生属性**）
                   ply.attr:ClearFlag()
                   Sche.Spawn( → 写 chaid2player/nickname2player + NotifyBeginPlay() )
             返回 {true, groupsession}
⑤ gate 收到 ret：ret[3] 有值 ⇒ 发 CMD_GC_CREATE 给客户端（进入创角）；否则 status=playing
⑥ 客户端 → gate:  CMD_CG_CREATE(avatarid, nickname, weapon, groupsession)  ← 注意：**avatarid 是 uint8**
⑦ group CMD_CG_CREATE：
        校验 nickname 非空、TableItem[weapon].Item_Type == 2（必须是武器）
        checkDuplicateName(nickname)（加锁查重）
        chaid == 0 ⇒ incr chaid + set <actname> <chaid>
        建 attr（全 0）→ 设 online_award=now, stamina=100000, shell/pearl/soul=100000,
                       potential_point=10000（**测试期白送**）
        Sign/Task/Achi/Mail.New
        按武器给额外技能：5101→{1110,1}，5201→{1210,1}，其他→{1010,1}
        初始背包：size=60, pos2=武器, pos3=5401(腰带), pos11=5502×10, pos12=5503×10
        初始技能：{11,1},{12,1},{13,1},{21,1} + extra_skill
        OnLevelUp(1) + attr:ClearFlag()
        hmset chaid:<chaid> nickname avatarid chainfo bag skills
                            everydaysign everydaytask achievement   ← **一条命令写 8 个字段**
        + chaid2player / nickname2player + NotifyBeginPlay()
⑧ 客户端 → gate:  CMD_CG_ENTERMAP(type)   → group Map.EnterMap（见 scene.md）
```

| 观察 | 结论 | 状态 |
|---|---|---|
| 创角时**一次性 `hmset` 8 个字段** | ✅ 好做法（原子性 + 一次往返） | 【已确认】 |
| **创角未把 `nickname` 索引与 `chaid` 索引放进同一事务** | ⚠️ 若 `incr chaid` 成功但后续 `hmset` 失败 ⇒ 产生"有 chaid 无角色"的孤儿 | 【已确认】 |
| 创角赠送大量货币（`stamina/shell/pearl/soul = 100000`，`potential_point=10000`） | ⚠️ **测试配置**，非正式数值 | 【已确认】 |
| `avatarid` 是 `uint8` 而 `TableAvatar` 的 key 到 701 | ⚠️ **701 无法用 uint8 表达** ⇒ 创角只能选 1..4（`robotclient.lua` 里 `math.random(1,2)`） | 【已确认】 |
| `checkDuplicateName` 在**昵称相同**时会跳过查重（`if not ply.nickname or ply.nickname ~= nickname then`） | ⚠️ 重连创角场景下的"特例"处理，逻辑正确但隐晦 | 【待验证】 |
| 登录时**没有版本号/校验和/心跳校验** | ⚠️ 无客户端版本兼容检查 | 【已确认】 |
| **密码完全不校验** | ⚠️ README 明示"忽略密码直接点击进入游戏"；`CMD_CA_LOGIN` 只读 `type` 与 `actname` | 【已确认】 |

---

## 九、角色系统 → JSTM 借鉴结论汇总

| 优先级 | 借鉴点 | 出处 | 价值 |
|---|---|---|---|
| **P0** | **属性下标化 + 派生属性不落库（每次登录 `CalAttr` 全量重算）** | `name2idx.lua` 的 `attr_db_save` + `groupplayer.lua:CalAttr` | 彻底避免"存档里的派生属性与公式不一致"这一类祖传 bug |
| **P0** | **成就/任务的达成条件谓词化**（`(事件类型,参数) → 条件函数`） | `achievement.lua:achiv_check` | 让"新增任务/成就"不改业务代码 |
| **P0** | **改动后发信号重算属性**（换装返回 `"recalattr"`） | `bag.lua:Swap` + `groupplayer.lua:CalAttr` | 解耦"数据变更"与"属性计算" |
| **P0** | **进图包结构**（maptype + 全属性 + 战斗背包 + 玩法数据 + selfid）；**重连时逐个重建视野** | `gameplayer.lua:on_entermap` / `ReConnect` | 直接对应 JSTM 目前"重连/NPC 对话未闭环"的缺口 |
| **P1** | **属性可见性白名单**（`attr2view`）+ **一次变更两个包**（视野包/自身包） | `gameserver/attr.lua` | 隐私 + 带宽 + 反外挂 |
| **P1** | **发奖"先全量校验、再全部落地"** | `bag.lua:AddItems` / `equip.lua:CMD_CG_COMPOSITE` | 防止"发一半奖励" |
| **P1** | **昵称唯一索引 + 加锁查重**（JSTM 可用 SQLite `UNIQUE` + 事务，更简单） | `groupplayer.lua:checkDuplicateName` | 防并发重名 |
| **P1** | **日重置集中化**（每日任务重置顺便重置体力）+ **以 5:00 为分界** | `everydaytask.lua:CheckReset` + `GetTSWeeHour()` | JSTM 的每日/签到/限时活动 |
| **P2** | **多索引角色表**（session / actname / chaid / nickname） | `groupplayer.lua` 4 张表 | 聊天/好友/GM 都需要 |
| **P2** | **创角一次性 `hmset` 全部字段** | `groupplayer.lua:CMD_CG_CREATE` | 原子性 + 性能 |
| **禁止** | 抄属性**公式系数**（2.5 / 2 / 22.5 / 0.02 / 0.01 / 0.1）、抄货币 id（4001~4005）、抄 32 项属性下标顺序 | `CalAttr` / `Util.NewRes` | **JSTM 的公式与字段必须来自 APK** |
| **禁止** | 抄**位打包**（attr[3] 存强化+升星）、抄"用属性下标当货币"（4001=shell） | `item.lua` / `util.lua` | 可读性差、不可读不可查；JSTM 有 SQLite 应显式建模 |
| **警示** | 本项目**角色系统的已知 bug 至少 7 处**（§6.1 满级免费升级、§6.4 `awarded` 未定义全局、§6.5 邮件 id 冲突+回填宽度不匹配、§6.6 好友 `self.owner` nil、§5.1 `PeekInfo` 逻辑取反、`RemItem` 越界、`CalAttr` 不更新 life） | 见各节 | **只借结构，不要借实现** |

---

## 十、【未读到】/【未知】

| 项 | 状态 |
|---|---|
| `TableRole`/`TableExperience` 的**完整数值范围** | 【部分已确认】读到前 30 / 前 20 行；最大等级【未知】 |
| `combat_power`（战斗力）计算方式 | 【未知】表里有字段、代码里从未计算 |
| `hit`（命中）的消费方 | 【未知】**全项目未发现使用** |
| `anger`（怒气）的消费方 | 【未知】未发现使用 |
| `movement_speed` 的消费方 | 【未读到】`avatar.speed` 是硬编码 27，不走该属性 |
| `CTimeUtil` 的时区语义（`GetTSWeeHour` 是"当日 5:00"还是"本周 5:00"） | 【待验证】—— 名字含 `Wee`(Week?) 但用法像"当日 5 点"，需读 C 源码确认 |
| 客户端角色相关协议（`UILogin.lua` / 创角界面） | 【未读到】（本轮不审计客户端） |
| `php/` 后台的 GM 角色操作 | 【未读到】 |
