# Survive 战斗系统审计（逐文件 · 类/函数级）

> 对象：`gameserver/{skill,buff,bufffunction,robot,maplogic,snail}.lua`、`groupserver/skill.lua`、`gameserver/map.lua`（战斗入口）、`common/{TableSkill,TableSkill_Addition,TableBuff,TableBuff_Nexus}.lua`
> 状态标记：【已确认】【待验证】【未知】；方法：`zipfile` 按需读取原文（**未修改任何文件**）
> 对照目标：**JSTM**（`FINAL_SERVER_ARCHITECTURE.md`：战斗"流程通，**数值为 TEST_ONLY**"；技能"未实现"）

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| 战斗在哪算 | **全部在 gameserver**（场景进程）；groupserver **完全不参与战斗结算**，只收结算结果并发奖 | 【已确认】 |
| 战斗驱动方式 | **服务端权威**：客户端只发「技能 id + 目标 id 列表/方向/点」，服务端算伤害并广播 | 【已确认】 |
| 伤害公式 | `damage = floor((Attack_Coefficient * (atk-def))/1000 + lev * Grade_Coefficient)` 再乘 `suffer_plusrate`，**最小伤害 10** | 【已确认】 |
| 命中/闪避 | `agile > random(1,1000)` ⇒ **miss**（属性名叫敏捷，语义是闪避） | 【已确认】 |
| 暴击 | `crit > random(1,1000)` ⇒ 伤害倍率 `+1.5` | 【已确认】 |
| **服务端不校验技能距离/角度/目标数** | `UseSkill` **只校验「不是自己队友」和「没死」**，完全不看 `Attack_Distance`/`Att_Range`/`Angle`/`Attack_Number` | 【已确认】⇒ **反外挂缺失**，JSTM 必须自己补 |
| Buff | `TableBuff` 驱动 + `bufffunction.lua` 回调表（回血/变速/隐身/眩晕/加成）；**互斥表 `TableBuff_Nexus` 因键类型不匹配实际失效** | 【已确认】 |
| 特殊技能 | 通过表字段 `Suffer_Script` 指向 **Lua 全局函数名**（`skill1060`/`skill1120`），在 `UseSkill` 里 `_G[name]` 取 | 【已确认】 |
| Projectile / 弹道 | **不存在**（没有飞行物、没有命中延迟、没有前摇结算）。`timetick` 只是透传给客户端做表现对齐 | 【已确认】 |
| 死亡处理 | `avatar:OnDead` → `map.logic:OnAvatarDead` → 各玩法自处理（5PVE 入回收队列、5VP 计数、5V5 判胜负、生存赛不处理） | 【已确认】 |
| 奖励 | **场景不发奖**，通过 `CMD_GAMEG_5PVEAWARD` / `CMD_GAMEG_PVPAWARD` / `CMD_GAMEG_SURVIVE_FINISH` 发给 group，由 group 查表发放 | 【已确认】 |
| AI | `robot.lua` **协程 + 三态状态机**（巡逻/追踪/攻击），两种 AI（`aiid=1` 视野巡逻、`aiid=2` 全图找敌） | 【已确认】 |
| 对 JSTM 的价值 | **「服务端权威 + 目标列表校验 + 结算交给中心」的骨架值得借鉴；数值表/技能字段一个都不能抄** | 【已确认】 |

---

## 二、技能数据表（`common/TableSkill.lua`）字段语义【已确认】

| 字段 | 示例（skill 1010 剑气） | 含义 | 代码中是否消费 |
|---|---|---|---|
| `Target_type` | 0 | 目标类型 | ❌ **未被读取** |
| `Attack_Types` | 2 | **攻击形态：0/3=单体，1=点选 AOE，2=方向** | ✅ `UseSkill` 主分支依据 |
| `Attack_Distance` | 300 | 施法距离（像素） | ❌ **不校验** |
| `Att_Range` | 30 | 作用范围（像素） | ❌ **不校验** |
| `Angle` | 90 | 扇形角度 | ❌ **不校验** |
| `Attack_Coefficient` | 1500 | 伤害系数（**千分比**） | ✅ `CalDamage` |
| `Grade_Coefficient` | 10 | 等级系数 | ✅ `CalDamage` |
| `Skill_Name` / `Ability_Describe` / `Effect_Describe` / `Icon_Path` | — | 文案/图标（客户端用） | ❌ 服务端不用 |
| `ActionName` | `Skill1` | 动作名 | ❌ |
| `Skill_CD` | 3000 | 单技能 CD（ms） | ✅ `UseSkill` 尾 `skill.nexttime = GetSysTick()+Skill_CD` |
| `Public_CD` | 2000 | 公共 CD（ms） | ✅ `skillmgr.next_aval_tick` |
| `SkillType` | 1 | 技能类型（1/2/3，疑似门派） | ❌ **未被读取** |
| `Category` | 2 | **是否造成伤害：nil/0 = 不结算伤害；其它 = 结算** | ✅ `CalDamage` 首行判断 |
| `Break_Move` | 1 | 是否打断移动 | ✅ `UseSkill` 尾 |
| `Attack_Number` | 2 | 最大目标数 | ❌ **不校验**（客户端想传几个就几个） |
| `Repel_Range` | 200 | 击退距离（像素） | ✅ `UseSkill` 的 AOE 分支 |
| `Touch_Buff` | 3001 | 命中后附加 buff | ✅ `UseSkill` |
| `Check_Buff` | 3001（skill 1040） | **需要自身有该 buff 才能放**（如"旋风斩伤害"需要 3001） | ✅ `UseSkill` 与 `skillmgr:UseSkill` |
| `Base_Skill` | 1030（skill 1040） | 基础技能 id | ❌ 未被读取 |
| `Suffer_Script` | `skill1060` / `skill1120` | **特殊结算脚本的全局函数名** | ✅ `UseSkill` |
| `Skill_Addition` | `增加%d点伤害` | 文案 | ❌ |
| `Energy` | 3 | 能量消耗 | ❌ **未被读取**（客户端侧扣能量，服务端不校验） |
| `Soul` | 100 | 解锁消耗武魂 | ✅ `groupserver/skill.lua:Unlock` |
| `Effects_ID` / `Sound` | 30 / 11 | 特效/音效 id | ❌ 服务端不用 |

**★ 反外挂层面的关键发现（【已确认】）**：`Attack_Distance`、`Att_Range`、`Angle`、`Attack_Number`、`Energy` **全部只在客户端生效**。
⇒ 一个改包的客户端可以：**隔全图放技能、对任意多目标施法、0 能量放技能**。
⇒ **JSTM 必须自行补上**：距离校验（`pos` 差 ≤ `Attack_Distance`）、目标数上限（`#targets <= Attack_Number`）、能量/冷却校验。

## 2.1 加成表 `common/TableSkill_Addition.lua`【已确认】

```lua
TableSkill_Addition[技能等级][技能id] = 额外倍率      -- 例：[1]["1010"] = 2
```
- 只有 **5 个技能等级 × 15 个技能 id**，且**所有值都是 2**（明显是占位数据）。
- 消费处：`CalDamage` 里 `suffer_plusrate = suffer_plusrate + v` ⇒ **是"加到倍率上"而不是"加到伤害上"**，与表里的注释语义（`Skill_Addition = "增加%d点伤害"`）**不一致**。
- ⚠️ 用 `TableSkill_Addition[skill.lev]` 取行 —— 若 `skill.lev` 为 nil（AI 造的 `{lev=1}` 有值；但 `LevelUp` 后 lev 是 number）尚可；**若某技能 lev 超出 5 则取不到，静默不加成**。

---

## 三、伤害结算（`gameserver/skill.lua`）——**逐函数**

### 3.1 `CalDamage(atker, sufferer, skill)` → `miss, crit, damage`【已确认】

```lua
local category = skill.tb["Category"]
if not category or category == 0 then return nil,nil,0 end        -- ① 非伤害技能
local atkrate = atker.attr:Get("attack") - sufferer.attr:Get("defencse")
if atkrate < 0 then atkrate = 0 end                              -- ② 攻防差（夹 0）
local damage = math.floor((skill.tb["Attack_Coefficient"] * atkrate)/1000
                          + skill.lev * skill.tb["Grade_Coefficient"])   -- ③ 主公式
if atker ~= sufferer and damage <= 0 then damage = 10 end         -- ④ 最小伤害 10
if atker ~= sufferer and atker.attr:Get("agile") > math.random(1,1000) then
    miss = true; return miss,crit,0                               -- ⑤ 闪避
end
local suffer_plusrate = atker.attr:Get("suffer_plusrate")
if suffer_plusrate == 0 then suffer_plusrate = 1 end               -- ⑥ 默认倍率
if atker ~= sufferer and atker.attr:Get("crit") > math.random(1,1000) then
    suffer_plusrate = suffer_plusrate + 1.5; crit = true           -- ⑦ 暴击 +150%
end
local tb = TableSkill_Addition[skill.lev]
if tb then local v = tb[skill.id]; if v then suffer_plusrate = suffer_plusrate + v end end
return miss, crit, math.floor(damage * suffer_plusrate)            -- ⑧ 最终伤害
```

| 观察 | 结论 | 状态 |
|---|---|---|
| **没有防御减伤曲线**，只有 `attack - defencse` 的差 | 极简 | 【已确认】 |
| **`Grade_Coefficient` 乘的是 `skill.lev`（技能等级）**，不是角色等级 | 与字段名"等级系数"语义需注意 | 【已确认】 |
| **闪避率 = `agile/1000`**（`agile` 既是移动相关又是闪避） | 属性命名与语义脱节 | 【已确认】 |
| **暴击率 = `crit/1000`**；暴击倍率 **+1.5（即 250%）** | | 【已确认】 |
| **`miss` 判定在 `damage` 计算之后** ⇒ 命中判定晚于伤害计算，但在返回时置 0 | 逻辑上无副作用，但**可读性差** | 【已确认】 |
| `hit`（命中）属性**从未参与判定** | 属性存在但无消费方 | 【已确认】 |
| `math.random(1,1000)` 每次一条 | 无随机数种子处理（Lua 的 `math.random` 默认种子依赖 `os.time`，**未读到任何 `math.randomseed` 调用**）⇒ **同一秒启动的进程随机序列相同**【已确认】——对私服/单机影响不大，但需注意 |
| **伤害不返回给调用方做日志** | 无法做伤害统计/战报 | 【已确认】 |

### 3.2 `process_hp_change(atker, suffer, skill)`【已确认】

```lua
local miss,crit,damage = CalDamage(atker,suffer,skill)
local hp = suffer.attr:Get("life")
if damage > hp then damage = hp end                 -- 夹到当前血量
if damage > 0 then
    hp = hp - damage
    suffer.attr:Set("life", hp)
    if hp == 0 then suffer:OnDead(atker, skill.id) end   -- ★ 死亡
    suffer.attr:NotifyUpdate()                            -- ★ 属性同步
    suffer.buff:RemoveBuff(3002)                          -- ★ 被打即破隐身
end
return miss,crit,damage
```
| 观察 | 状态 |
|---|---|
| 伤害被夹到"当前血量"（不会出现负数血量） | 【已确认】 |
| **`NotifyUpdate` 每次都发**（即使只是掉 1 血）⇒ 高频战斗下属性包量很大；但 `attr:NotifyUpdate` 有 `flag` 去重与"视野包只含 level/life/maxlife"的限制，可接受 | 【已确认】 |
| **死亡即 `OnDead`，没有"死亡结算延迟"** ⇒ `OnDead` 里 `logic:OnAvatarDead` 可能同步改 `avatars` 表（5PVE 是**延迟 2 秒回收**，见 §6） | 【已确认】 |

### 3.3 `UseSkill(avatar, skill, byAi, param)` —— **战斗主流程**【已确认】

**① 前置守卫**
```lua
if not avatar.canUseSkill then return false end      -- 玩法开局倒计时期间禁止放技能
local check_buf = skill.tb["Check_Buff"]
if check_buf and check_buf > 0 and not avatar.buff:HasBuff(check_buf) then return false end
```

**② 解析目标（客户端 / AI 两条路径）**

| 来源 | `single_target`（`Attack_Types` 0 或 3） | `Attack_Types == 1`（点选 AOE） | `Attack_Types == 2`（方向） |
|---|---|---|---|
| **客户端** | `timetick=Read_uint32`；`target=map:GetAvatar(Read_uint32)`；校验 `target:isDead()`；**`atk_type==3` 时要求 `target==avatar`**（自身技能） | `point={Read_uint16, Read_uint16}`；再 `size=Read_uint8`；循环 `size` 次读 `u32` 目标 id，**只校验 `target.teamid ~= avatar.teamid and not target:isDead()`** | `dir=Read_uint16`；同样再读目标列表 |
| **AI** | `target=param[1]` | `point=param[1]; targets=param[2]` | `dir=param[1]; targets=param[2]` |

⚠️ **关键缺陷**：**目标列表由客户端提供，服务端只过滤"队友"和"死人"，不看距离/数量**。
⇒ JSTM 必须改为**服务端根据 `Attack_Distance`/`Att_Range`/`Angle` 从 AOI 里自选目标**（或至少交叉校验客户端列表）。

**③ 结算分发**
```lua
local suffer_function = skill.tb["Suffer_Script"]
if suffer_function then suffer_function = _G[suffer_function] end
if not suffer_function then
    -- 通用：逐个目标 process_hp_change
    for k,v in pairs(targets) do
        local miss,crit,damage = process_hp_change(avatar,v,skill)
        if single_target then notify_atksuffer(avatar,v,skill.id,miss,crit,0-damage,timetick)
        else
            local Repel_Range = skill.tb["Repel_Range"]
            local pos
            if Repel_Range and Repel_Range > 0 then           -- ★ 击退
                v:StopMov()
                pos = Util.ForwardTo(avatar.map, avatar.pos, v.pos, Repel_Range)
                if pos then v.pos = pos; Aoi.moveto(v.aoi_obj, pos[1],pos[2]) end
            end
            notify_suffer(avatar, skill.id, v, miss, cirt, 0-damage, pos, timetick)  -- ← 注意：cirt（拼写错误，恒 nil）
        end
        if buf and buf > 0 then v.buff:NewBuff(v, buf) end     -- Touch_Buff
    end
    if not single_target then notify_atk_success(avatar, skill.id, atk_type, dir, point) end
else
    suffer_function(skill, avatar, targets, dir, point, timetick)   -- ★ 走特殊脚本
end
```

**④ 收尾**
```lua
skill.nexttime = C.GetSysTick() + skill.tb["Skill_CD"]
if break_move and break_move > 0 then avatar:StopMov() end
if skill.tb["Category"] == 2 then avatar.buff:RemoveBuff(3002) end   -- ★ 攻击破隐身
```

| 观察 | 结论 | 状态 |
|---|---|---|
| **`cirt` 拼写错误** ⇒ AOE 的 `notify_suffer` 永远把 `crit` 传成 nil ⇒ **AOE 不会显示暴击表现**（伤害本身已含暴击倍率） | 真实 bug | 【已确认】 |
| `Touch_Buff` 一律 `v.buff:NewBuff(v, buf)`（**释放者写成受害者自己**） | 严重语义偏差（buff 的 `releaser` 应是攻击者，影响 `buffSkill` 与 `suffer_plusrate` 归属） | 【已确认】 |
| 击退用 `ForwardTo`（LOS 射线，**遇障碍停在障碍前**）+ `Aoi.moveto` | ★ 可借鉴：**击退不是简单加坐标，而是走 LOS** | 【已确认】 |
| 特殊脚本走 `_G[name]` | 表驱动 + 全局函数名；**如果表里写错名字只会静默走通用分支**（`_G[x]` 为 nil） | 【已确认】 |
| 单目标**不发 `notify_atk_success`**（只有非单体才发） | 客户端靠 `NOTIATKSUFFER` 推断 | 【已确认】 |

### 3.4 通知包（三个 `notify_*`）【已确认】

| 函数 | 命令 | 字段 | 发给谁 |
|---|---|---|---|
| `notify_atk_success(avatar,skillid,atk_type,dir,point)` | `CMD_SC_NOTIATK` | `u32 atker.id + u16 skillid + u8 atk_type`（`atk_type==1` 补 `u16 x,y`；`==2` 补 `u16 dir`） | `Send2view`（全场） |
| `notify_atk_failed(avatar,skillid)` | `CMD_SC_NOTIATK` | 同上但 `u8 atk_type = 0` | `Send2Client`（本人） |
| `notify_atksuffer(atker,sufferer,skillid,miss,crit,damage,timetick)` | `CMD_SC_NOTIATKSUFFER` | `u32 timetick + u32 atker.id + u16 skillid + u32 sufferer.id + u32 damage + u8 (1=miss,2=crit,0=普通)` | `sufferer:Send2view`（**以"受害者"为中心广播，让周围人都看到受击表现**） |
| `notify_suffer(atker,skillid,sufferer,miss,crit,damage,pos,timetick)` | `CMD_SC_NOTISUFFER` | 上述 + `u8 有无位移 + u16 x,y` | 同上 |

**★ 值得借鉴的两点**
1. **伤害用 `0 - damage` 写入 `u32`**（即负数按补码传）⇒ 客户端能区分"伤害/治疗"。⚠️ 但 `CalDamage` 只返回正数，所以本项目**实际只有伤害**。
2. **"攻击表现"广播给视野内所有人（`NOTIATK`），"受击表现"以受害者为中心广播（`NOTIATKSUFFER`/`NOTISUFFER`）** ⇒ 两种包的生命周期不同（动作 vs 结果）。JSTM 的战斗表现协议应对照 `analysis/jstm_1.4.9/battle_protocol.md`（**本轮未读**）。

### 3.5 特殊结算脚本（在 `gameserver/skill.lua` 中定义，被 `_G[]` 引用）【已确认】

| 函数 | 技能 | 机制 | 备注 |
|---|---|---|---|
| `skill1060(skill,atker,sufferers,dir,point,timetick)` | 1060 无敌斩 | **要求恰好 3 个目标**（`if #sufferers == 0 or #sufferers ~= 3 then` 回失败包）；逐个 `process_hp_change` 并把 `-damage` 记入包；**最后把攻击者传送到第 3 个目标的位置**（`atker.pos = last_suffer.pos` + `Aoi.moveto`） | ⚠️ **"必须 3 个目标"是硬编码关卡式约定**；⚠️ 传送**不检查目标位置是否可走** |
| `skill1120(skill,atker,sufferers,dir,point,timetick)` | 1120 野蛮冲撞 | 只有一个目标时：距离 > `Pixel2Grid(500)` ⇒ **把攻击者向前推进 200 像素**（`ForwardTo`）并只发位置；否则 **攻击者瞬移到受害者位置、受害者被推到攻击者前进方向 +100 像素** + 伤害 + `suffer:StopMov()`；无目标 ⇒ 只朝 `dir` 前进 200 像素 | ⚠️ **双方位置都被服务端硬改**；`Aoi.moveto` 在最后统一调用 |

**★ 评价**：这两个脚本把"冲刺/位移/击退"写成**手写特例**。JSTM 若要实现类似效果，建议抽象成**技能效果原语**（`move_self_to` / `push_target` / `damage_targets`），而不是每个技能一个函数。

### 3.6 技能管理器（`skillmgr`）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `skillmgr:Init(skills)` | `skills = {{id,lev},...}` → `self.skills[id] = {id,lev,nexttime=GetSysTick(),tb=TableSkill[id]}`；`self.next_aval_tick = GetSysTick()` | ✅ 适合 | 与 `groupserver/skill.lua` 的数据形态一致 |
| `skillmgr:UseSkill(avatar,rpk)` | **从客户端包读 `u16 id`**；若 `self.skills[id]` 不存在则**现场创建** `{id,lev=1,nexttime=now,tb=TableSkill[id]}`；`Check_Buff==0` 时检查公共 CD；调 `UseSkill(...)`；失败 `notify_atk_failed`；成功更新 `next_aval_tick` | ⚠️ **危险** | ⚠️ **"服务端不认识这个技能 id 就自动学会它"** ⇒ 任何客户端都能放任意技能（含未解锁技能）。**JSTM 必须改为 `if not skill then return end`**【已确认】。⚠️ `skill.tb` 若 `TableSkill[id]` 为 nil，下一行 `skill.tb["Check_Buff"]` 会**崩溃**（被 `application.lua` 的 xpcall 兜住） |
| `skillmgr:UseSkillAi(avatar,skill,param)` | 同 AI 入口 | ⚠️ 同上 | |
| `skillmgr:GetAvailableSkill()` | 遍历 `self.skills`，返回第一个"check_buf 为空 且 CD 已过"的技能 | ⚠️ **有优先级 bug** | 条件写作 `if not check_buf or check_buf == 0 and tick >= v.nexttime then` ⇒ Lua 里 `and` 优先级高于 `or`，等价于 `(not check_buf) or (check_buf==0 and tick>=nexttime)` ⇒ **`check_buf` 为 nil 时直接返回，完全不看 CD** ⇒ AI 会"无视 CD 连放"。**JSTM 若照抄会让 AI 变得极强**（反过来说，也可以用来判断：**AI 强度实际由这条 bug 决定**）【已确认】 |
| `skillmgr:GetSkill(id)` | 查表 | ✅ | |

---

## 四、Buff 系统（`gameserver/buff.lua` + `bufffunction.lua`）

### 4.1 数据表 `common/TableBuff.lua`【已确认】

| 字段 | 含义 | 消费处 |
|---|---|---|
| `Period1` / `Period2` | 持续时间（`period = Period1 + Period2`） | `buff:Init` |
| `Interval` | 间隔触发周期（0 = 不触发） | `buff:Init` + `Tick` |
| `ClientInterval` | 客户端表现间隔 | ❌ 服务端不用 |
| `Range` | 作用范围 | ❌ **未被读取**（`self.range` 存了但无消费方） |
| `OnBegin` / `OnEnd` / `OnInterval` | **回调函数名字符串** | `GetTabFunction(tb,name) = BuffFunc[tb[name]]` |
| `AtkSkill` | buff 期间自动释放的技能（**只给 AI 用**） | `buffmgr:NewBuff` 里 `if AtkSkill and releaser.robot then buf.buffSkill = {AtkSkill, now+100, 500}` |
| `ActionName` / `Effects_ID` / `Sound` | 表现 | ❌ 服务端不用 |
| `Move_Speed` / `Begin_Reply` / `Reply` | 具体回调的**参数** | 由 `bufffunction.lua` 里的函数读取 |

**已定义 buff（16 个）**：3001（AtkSkill=1040 的"旋风"持续态）、3002（隐身，OnBegin/OnEnd 设 `avatar.invisible`）、3101（眩晕 `Blackout_*` 设 `avatar.stick`）、3201（`suffer_plusrate=1.5`）、3300~3306（持续回血）、3321~3324（变速）。

### 4.2 `buff:Init(id,owner,releaser,tb)`【已确认】
```lua
self.releaser = releaser      -- 释放者
self.owner    = owner         -- 承载者
self.interval = tb.Interval or 0
self.period   = (tb.Period1 or 0) + (tb.Period2 or 0)
self.endTick  = C.GetSysTick() + self.period
self.onBegin/onEnd/onInterval = GetTabFunction(tb, "OnBegin"/"OnEnd"/"OnInterval")
if self.interval > 0 and self.onInterval then self.nextInterval = GetSysTick() + self.interval end
```

### 4.3 `buff:Tick(currenttick)` / `buff:Reset(releaser)` / `Do(event)`【已确认】

| 函数 | 机制 |
|---|---|
| `Tick(currenttick)` | ① `nextInterval` 到点 → 重置 `nextInterval` + `Do("onInterval")`；② `currenttick >= endTick` → `return false`（**上层据此移除**）；③ 若 `self.buffSkill` 存在且 `releaser.robot` 在运行 → 到点 `robot:UseBuffSkill(skillid)` |
| `Reset(releaser)` | 覆盖 `releaser` + `endTick = now + period`（**同类 buff 叠加重置时长**） |
| `Do(event)` | `pcall(self[event], self)` + 错误日志（**回调异常不影响主循环**） |
| `NotifyBegin(o)` / `NotifyEnd()` | 广播 `CMD_SC_BUFFBEGIN` / `CMD_SC_BUFFEND`（`u32 owner.id + u16 buffid`）；`NotifyBegin` 里 `if o and o.gatesession == nil then return end`（**不为非玩家观察者发包**） | 

### 4.4 `buffmgr:NewBuff(releaser, id)` —— **互斥语义（有 bug）**【已确认】

```lua
local tb = TableBuff[id]; if not tb then return false end
for k,v in pairs(self.buffs) do
    local exclusion = buffExclusion[id]        -- buffExclusion = TableBuff_Nexus
    if exclusion then exclusion = exclusion[k] end     -- ← k 是"已有 buff 的数字 id"
    if exclusion == exclude then  return false                       -- 2 = 排斥（不叠加）
    elseif exclusion == replace or id == k then
        if id == k then v:Reset(releaser); return true               -- 同类 → 只刷新时长
        else self:RemoveBuff(k); break end                            -- 1 = 替换旧 buff
    elseif exclusion == interrupt then self:RemoveBuff(k) end          -- 3 = 打断（移除旧的但继续加新的）
end
local buf = buff:new():Init(id, self.avatar, releaser, tb)
self.buffs[id] = buf
...
buf:NotifyBegin(); buf:Do("onBegin")
```

| 观察 | 结论 | 状态 |
|---|---|---|
| **互斥表实际失效** | `TableBuff_Nexus[id] = {["BUFF2"] = 0}`，而查表用的是 **数字键 `k`**（已有 buff 的 id），字符串 `"BUFF2"` 永远匹配不上 ⇒ `exclusion` 恒为 nil ⇒ **`replace`/`exclude`/`interrupt` 三条规则从不触发** | 【已确认】 |
| 于是实际生效的只有 `id == k` ⇒ **同类 buff 只刷新时长、不同 buff 无条件共存** | 简化为"无互斥" | 【已确认】 |
| `return true` 在 `for` 循环内部**提前返回**（刷新时长路径） | 语义正确（同类只需刷新一次） | 【已确认】 |
| `local replace/exclude/interrupt = 1/2/3` 定义在**文件级** | 可读性尚可 | 【已确认】 |
| `buffmgr:RemoveBuff(id)` | 删表 + `NotifyEnd` | ✅ |
| `buffmgr:Tick(currenttick)` | 遍历，`Tick` 返回 false 则 `NotifyEnd` + 删 | ✅ |
| `buffmgr:OnAvatarDead()` | 所有 buff `NotifyEnd` + 清表（⇒ **减速/定身等回调的 `OnEnd` 会执行，状态能复原**） | ✅ 好的做法 |
| `buffmgr:OnEnterSee(o)` | 对所有 buff 重发 `NotifyBegin(o)`（**新人进视野时补齐 buff 表现**） | ★ **必须做**，与 `SendEnterSee` 里的 `other.buff:OnEnterSee(self)` 配套 |
| `buffmgr:HasBuff(buffid)` | 查表 | ✅ |

### 4.5 `bufffunction.lua`（回调表，7 个函数）【已确认】

| 函数 | 作用 | 备注 |
|---|---|---|
| `LifeRecover_OnBegin` | `Add("life", tb.Begin_Reply, maxlife)` + `NotifyUpdate` | |
| `LifeRecover_onInterval` | `Add("life", tb.Reply, maxlife)` + `NotifyUpdate` | 持续回血 |
| `SpeedChange_OnBegin` | `newspeed = floor(oldspeed * (100 + tb.Move_Speed))`；**夹在 [17, 37]**；备份 `avatar.oldspeed`；`SetSpeed` | ⚠️ **公式少乘 1/100**（`Move_Speed=10` 会算出 27×110 = 2970，被上限 37 夹住）⇒ **所有加速 buff 都直接顶到上限 37，所有加速效果无差异**【已确认】。减速 `-5/-10` 则算出 2565/2430 也被夹到 37 ⇒ **减速实际无效**。这是一个**完全没被发现的公式错误** |
| `SpeedChange_OnEnd` | `SetSpeed(avatar.oldspeed)` | 若 buff 期间又叠加一个变速 buff，`oldspeed` 会被覆盖 ⇒ 恢复错值【待验证】 |
| `Buff3201_OnBegin` | `attr:Set("suffer_plusrate", 1.5)` | ⚠️ **写死 1.5，且属性是浮点**（见 `role.md` §3 的 u32 截断隐患） |
| `Buff3201_OnEnd` | `attr:Set("suffer_plusrate", 1)` | |
| `Blackout_OnBegin/OnEnd` | `avatar.stick = true/nil` + `StopMov()` | 定身 |
| `Buff3002_OnBegin/OnEnd` | `avatar.invisible = true/false` | 隐身；被攻击时 `process_hp_change` 主动 `RemoveBuff(3002)` |

**★ 结构上的亮点**：**"表里写函数名 → 代码里查函数表"** 的两级派发（`TableBuff.OnBegin = "LifeRecover_OnBegin"` → `BuffFunc["LifeRecover_OnBegin"]`）在 `triggerfunction`/`skill.Suffer_Script` 里是同一套模式。
⇒ **JSTM 可据此设计"配置驱动的 Buff/触发器/技能效果"**；⚠️ 但要用显式注册表并**在启动时校验所有引用都存在**（Survive 没做，写错名字只会静默失效）。

---

## 五、AI（`gameserver/robot.lua`）——**协程 + 状态机**

### 5.1 结构【已确认】

```
robot:new(avatar, aiid)
   └─ stateMachine:new(ro, aiid)
        └─ AiTable[aiid] = { [1]=巡逻, [2]=追踪, [3]=攻击 }
robot:StartRun() → self.co = Sche.Spawn(self.main, self)
robot:main()     → while self.run do stateMac:execute(); if not self.run then break end; Sche.Yield() end
robot:Stop()     → 解除 target/follow 的 traceme；self.run=nil；Sche.Schedule(co)（**立刻跑一次让它退出**）
robot:Wakeup()   → 若 run 且有 co → Sche.WakeUp(co)
```

| 状态 | 类 | `execute()` 机制 |
|---|---|---|
| `stat_partol = 1` | `state_partol`（AI 1） | 有 target → 转追踪；否则**在自己的 `view_obj` 里找** `not invisible and ~= self and not isDead and teamid ~= 我` 的敌人 → 设 target + `v:AddTraceMe(avatar)` → 转追踪；找不到 → `Mov(pos ± random(-10,10))` 随机巡逻 + `Sche.Block()`（**等移动完成**）+ `Sleep(random(200,1000))` |
| `stat_partol = 1` | `state_partol_goto`（存在但**未被 `AiTable` 使用**） | 走向指定 `targetpoint`，到达后**把 `stateMgr[stat_partol]` 换回普通巡逻** |
| `stat_partol_npc`（AI 2） | | **遍历 `avatar.map.avatars` 全图找敌**（不限于视野！）⇒ 全图嘲讽式仇恨 |
| `stat_trace = 2` | `state_trace`（AI 1） | target 失效/隐身/死亡/**距离 > 500 像素** → 清 target 转巡逻；**距离 ≤ 150 → 转攻击**；否则 `target:AssignAtkPoint(avatar,140)` 取一个攻击站位 → `Mov` + `Block` |
| `stat_trace_npc`（AI 2） | | 同上但阈值是 **150**（追踪范围 150，比 AI 1 的 500 小，**但配合全图找目标**） |
| `stat_atk = 3` | `state_atk`（两种 AI 共用） | target 失效 → 转巡逻；距离 > 150 → `Sleep(random(100,500))` 转追踪；否则 `Sleep(150)` + `DirTo(target)` + `AiUseSkill(ro,target)`；**技能失败则 `Sleep(500)`** |

**★ 三个值得借鉴的设计**
1. **AI 是被 `Sche.Block()` 挂起的协程**：`avatar:Mov` 成功后就 `Block()`，由 `avatar:process_mov` 在路径走完时 `robot:Wakeup()` 唤醒 ⇒ **不需要 AI 轮询"我到哪了"**，代码非常干净。
2. **`AddTraceMe`/`NotifyTargetPosChange`**：目标每次移动一格就通知追踪者 ⇒ **追击是事件驱动的**，不是每帧算距离。
3. **状态机"返回下一个状态号"**（`execute()` 返回 `stat_trace` 等，`stateMachine:execute` 据此切换）⇒ 极简、无需显式 transition 表。

**⚠️ 四个缺陷**
| 缺陷 | 说明 | 状态 |
|---|---|---|
| `AiUseSkill` 里定义了**全局函数** `UseSkillSingle/UseSkillPoint/UseSkillDir`（缺 `local`） | 全局污染；多 AI 并发时会互相覆盖（虽然单线程无竞态，但可读性差） | 【已确认】 |
| `state_atk` 里 `avatar:DirTo(target)` 后才放技能，但**从不做朝向/距离的最终校验** | 依赖 `UseSkill` 内部（而 `UseSkill` 也不校验距离） | 【已确认】 |
| `state_partol:execute` 里 `Sche.Block()` **无超时** | 若 `Mov` 后永远等不到 `Wakeup`（例如路径因 AOI 回调被打断），AI 会永久挂起【待验证】 | 【待验证】 |
| `robot:Stop()` 用 `Sche.Schedule(co)` 而非 `WakeUp` | 立即执行协程体以让它看到 `self.run == nil` 退出；**若协程正阻塞在 `Block()` 而未被唤醒，`Schedule` 不会执行它**（`Schedule` 对 `stat_block` 状态的 co 会直接 `SwitchTo`？—— 实际 `Schedule(co)` 里 `sche.timer:Remove(co)` 后 `SwitchTo(co)` 无条件 resume）⇒ 可行但绕 | 【待验证】 |
| `AiUseSkill` 的 `skill = skill or avatar.skillmgr:GetAvailableSkill()` | 配合 `GetAvailableSkill` 的优先级 bug ⇒ **AI 无视 CD 连放技能**（见 §3.6） | 【已确认】 |
| `AiUseSkill` 按 `Attack_Types` 分派：`3 or 0 → 单体`；`2 → 方向`；**else → 点选**（并把视野内 200 像素的敌人全收集为 targets） | 逻辑与 `UseSkill` 的客户端分支**不完全一致**（客户端分支里 `1` 是点选、`2` 是方向；这里 `2` 是方向、else 是点选，**恰好等价**） | 【已确认】 |

### 5.2 机器人补位（`maplogic.lua`）【已确认】

| 位置 | 机制 |
|---|---|
| `FiveVE:entermap` | `if self.plycount < 5 then` 造 `5 - plycount` 个 `CreateNPC(self, math.random(1,4), "robot", {id=5001,...}, base_attr, {{1030,1},{1040,1},{11,1},{1020,1}}, pos, 5, 1, 2)`（**aiid=2**），标 `isNPC=true` |
| `FiveVP:entermap` | 同上按队交替补位，`MaxPly` 从 `mapdef` 读 |
| `maplogic:OnClientDisconnect` | **真人掉线后 `ply.robot = Robot.New(ply,1)` + `StartRun()`** ⇒ 掉线玩家由 AI 托管继续战斗 |
| `avatar:OnDead` 里 | `self.robot:Stop(); self.robot = nil` |

**★ 这是本项目对 JSTM 最有实用价值的设计之一**：**"人不够就用 AI 填、人掉线就 AI 托管"** ⇒ 单机/小服也能跑副本与 PvP。JSTM 若要补副本功能，强烈建议采用。

---

## 六、死亡 / 复活 / 玩法结算

### 6.1 死亡链【已确认】
```
process_hp_change: hp==0
  → suffer:OnDead(atker, skill.id)
       ├─ self.buff:OnAvatarDead()        -- 清所有 buff（触发 OnEnd 复原状态）
       ├─ self.map.logic:OnAvatarDead(self, atker, skillid)   -- ★ 玩法钩子
       ├─ self.robot:Stop(); self.robot = nil
       └─ self:StopMov()
```

| 玩法 | `OnAvatarDead` 行为 | 后续 |
|---|---|---|
| `maplogic`（通用） | **空实现** ⇒ **通用图里玩家死亡不产生任何后果**（没有掉落、没有复活、没有惩罚） | 【已确认】 |
| `FiveVE` | `isMon` ⇒ `table.insert(self.recycle, {avatar, now+2000})`（**延迟 2 秒回收**）；否则 `live_ply_count -= 1` | `Tick` 里：`live_ply_count == 0` ⇒ 组 `CMD_GAMEG_5PVEAWARD(u16 round, u8 count, [u16 groupsession]*count)` 发给 group + 逐个玩家发 `CMD_SC_5PVE_RESULT` + `isFinish=true` + `KickAll = os.time()+5` |
| `FiveVP` | 按 `teamid` 减 `team1/2_alive_count` | `Tick` 里某队归零 ⇒ 组 `CMD_GAMEG_PVPAWARD(maptype, count, [groupsession, win])` 发 group + 每人 `CMD_SC_5PVP_RESULT` + `KickAll = now+5` |
| `Survive` | **空**（`Survive` 类没实现 `OnAvatarDead`，走基类空实现） | 存活计数在 `Tick` 里数 `attr:Get("life") > 0` 的 `isPlayer` |

### 6.2 结算与踢人【已确认】

| 机制 | 代码 | 说明 |
|---|---|---|
| **结算发回中心** | `togroup:Send(wpk)`（game 侧直接发） | ★ **场景不发奖，只报"谁赢了/打到第几轮"**，由 group 查 `TableTower_Reward`/`TableArena_Reward` 发放 ⇒ **奖励配置与发放集中在中心**，是干净的分工 |
| **踢人** | `self.KickAll = os.time() + 5`；`Tick` 里到点对每个玩家 `v:Release()` + 发 `CMD_GAMEG_KICK(u16 groupsession)` 给 group | ⚠️ `Tick` 里是 `v:Release()` **后**才取 `v.groupsession` 构造包，但 `Release` 会 `Gate.UnBind(self)`（清 `gatesession`）**不清 `groupsession`** ⇒ 侥幸可行【已确认】 |
| **地图回收** | `self.map:Release()`（含停定时器 + `Aoi.destroy_map`） | ✅ |
| **生存赛结束** | `Survive:Tick` 里 `alive_count == 1` ⇒ `isFinish`；向所有玩家发 `CMD_SC_SURVIVE_WIN(string winner)`；`destroyTime = now+2`；到点组 `CMD_GAMEG_SURVIVE_FINISH(string winner, u8 count, [u32 groupsession]*count)` 发 group → **`g_survive = nil`** | ⚠️ **`g_survive` 在 `map.lua` 的 `EnterSurvive` 里赋值、在 `maplogic.lua` 的 `Survive:Tick` 里置 nil**，跨文件全局共享 ⇒ 脆弱 |

### 6.3 `snail.lua`（螺旋方案预计算）【已确认】

| 函数 | 机制 |
|---|---|
| `cloneMatrix(matrix)` | 深拷贝 3×4 矩阵（**每次递归都克隆**） |
| `isVaild(matrix,x,y)` | 该格未访问 |
| `search(matrix,num)` | 把"访问序号"映射回 `base[y][x]` 的**区域编号** |
| `snail(matrix,c,x,y)` | **DFS 遍历 4×3 网格的所有路径**：`matrix[y][x] = ++c`；走满 12 格就把整条访问顺序转成区域编号序列 `table.insert(output, tmp)`；否则对 4 个方向递归 |
| **模块顶层三重循环** | `for i=1..3 do for j=1..4 do snail({{},{},{}},0,j,i) end end` ⇒ **模块加载时把全部方案算完**（`output` 是全局，被 `maplogic.lua` 当作 `boomScheme`） |

**评价**：用一个**穷举预计算**换来"每局随机取一条合法螺旋"，写法简单但
⚠️ **在 `require` 阶段做重计算**（DFS 全排列 + 每次克隆矩阵）⇒ **启动变慢、内存占一份固定表**；
⚠️ `totalcount` 变量无用；`output` 是**全局变量**（无 `local`）。
⇒ JSTM 若要"缩圈顺序"，直接运行时按规则生成即可（比预计算所有路径更省）。

---

## 七、玩法层战斗（`maplogic.lua` 的 4 个玩法，从战斗视角）

| 玩法 | 战斗特征 | 可借鉴之处 |
|---|---|---|
| **通用图（`open`）** | 玩家自由打怪；**死亡无后果**；NPC 由 AI 驱动 | ⚠️ 通用图**没有掉落/经验**（`OnAvatarDead` 空）⇒ 说明"通用图"仅用于非战斗场景（如主城）【待验证】 |
| **5 人 PVE（`FiveVE`，maptype 203）** | 10 秒准备 → 每轮生成 5 只怪（数值 = `TableTower_Defense[平均等级] × TableTower_Coefficient[轮次]`）→ 全灭则下一轮（**无限轮次**）→ 玩家全灭结算 | ★ **"等级 + 轮次双系数"的无限爬塔结构**；★ **机器人补位**；★ **延迟回收（2 秒）避免"死亡瞬间被引用"** |
| **5V5 PVP（`FiveVP`，maptype 204/207/208）** | 交错分队 + 固定出生点；两队存活计数；一方归零判胜负 | ★ **一个类同时支持 5V5/1V1/2V2**（靠 `mapdef.MaxPly` 与 maptype 参数） ⇒ **玩法参数化** |
| **生存赛（`Survive`，maptype 206）** | 12 区定时爆炸（10 秒一区）；区域内玩家 `life=0`；`TransferTo` 触发器跳区；最后 1 人胜 | ★ **"区域 + 触发器 + 定时事件"三件套**实现缩圈 |

**★ 战斗与玩法的接口只有 5 个**（`Init` / `entermap` / `leavemap` / `Tick` / `OnAvatarDead` / `OnClientDisconnect`）⇒ **JSTM 若要新增玩法，照这个接口切一个类即可**，不需要改战斗代码。这是值得学习的**扩展点设计**。

---

## 八、对 JSTM 的建议（战斗层）

| 优先级 | 借鉴点 | 出处 | 说明 |
|---|---|---|---|
| **P0** | **服务端权威结算 + 广播"攻击表现"与"受击表现"两种包** | `skill.lua` 的三个 `notify_*` | JSTM 的 `battle_protocol.md` 已存在（**本轮未读**），应对照确认 JSTM 是否也是服务端算伤害；若是客户端算，需改 |
| **P0** | **技能效果 = 表驱动 + 回调函数表**（`Suffer_Script`/`OnBegin`/`OnInterval`/`TriggerFunc` 同一模式） | `skill.lua` / `buff.lua` / `triggerfunction.lua` | 统一一套"配置里写名字 → 代码里注册表"的派发；**务必启动时校验引用存在** |
| **P0** | **服务端必须补的校验**（Survive 全缺）：技能距离、扇形角度、目标数上限、能量/冷却、技能是否已学会 | `UseSkill` / `skillmgr:UseSkill` | ★ 若 JSTM 照抄 Survive 的"由客户端给目标列表"，等于**开放全图秒杀** |
| **P0** | **Buff 的 `OnEnd` 必须能在死亡/断线/换场景时执行**（避免速度/定身等状态残留） | `buffmgr:OnAvatarDead` | |
| **P1** | **AI = 协程 + 三态状态机 + "到点唤醒"**（而不是每帧轮询） | `robot.lua` | 若 JSTM 用 asyncio 或"事件队列"，思路一致 |
| **P1** | **追踪/仇恨用"目标位置变化通知"而不是每帧算距离** | `AddTraceMe`/`NotifyTargetPosChange` | 性能 |
| **P1** | **人不够用机器人补位；掉线交 AI 托管** | `FiveVE:entermap` / `maplogic:OnClientDisconnect` | ★ 单机/小服可玩性的关键 |
| **P1** | **玩法钩子只有 6 个方法**（新增玩法不解耦战斗代码） | `maplogic` 家族 | 扩展点设计 |
| **P1** | **奖励由中心发放，场景只报结果** | `CMD_GAMEG_*` | 配置集中、防作弊 |
| **P2** | **击退/位移用 LOS 射线（遇障碍即停）** | `Util.ForwardTo` + `Astar.lineto` | 比"直接加坐标"正确得多 |
| **P2** | 进入视野时**补发 buff 与移动状态** | `buffmgr:OnEnterSee` + `SendEnterSee` 的 path 补发 | 否则新人看到"没有 buff、静止"的假象 |
| **禁止** | 🚫 抄 `Attack_Coefficient`/`Grade_Coefficient`/`TableTower_*`/`TableSkill_Addition` 等**任何数值** | — | 这些是占位数值（`TableSkill_Addition` 全是 2） |
| **禁止** | 🚫 抄 `Attack_Types` 的编号语义（0/3 单体、1 点选、2 方向） | — | 必须由 JSTM 客户端协议决定 |
| **禁止** | 🚫 抄 `Skill_CD`/`Public_CD`/`Energy` 的具体数值 | — | APK 里应有（**未读**） |
| **警示** | ⚠️ Survive 战斗层已确认的 bug 至少 **8 处**（`cirt` 拼写、`Touch_Buff` 释放者写错、`GetAvailableSkill` 优先级、`UseSkill` 自动学技能、`Buff_Nexus` 键不匹配、`SpeedChange` 公式漏 /100、`buff.Range` 未消费、`attack/Att_Range/Angle/Attack_Number` 不校验） | 见各节 | **只借结构，不要借实现** |

---

## 九、【未读到】/【未知】

| 项 | 状态 |
|---|---|
| **JSTM 的战斗协议与数值来源** | 【未读】`analysis/jstm_1.4.9/battle_protocol.md`、`analysis/1.4.9/battle/*`、`server/battle.py` 本轮**未打开**；`FINAL_SERVER_ARCHITECTURE.md` 已记录"怪物战斗数值 **APK 里不存在** ⇒ 不可校准"、战斗"数值为 TEST_ONLY" |
| **《绝世唐门》的权威伤害/战力公式** | 【未知】——`FINAL_SERVER_ARCHITECTURE.md` 已列为未知项，**Survive 的公式只是示例，不是答案** |
| `client/src/MgrFight.lua` / `MgrSkill.lua`（客户端战斗） | 【未读到】本轮不审计客户端；**"客户端是否也做预测结算"未验证** |
| `TableSkill` 的完整 43 行（约 20+ 技能） | 【部分已确认】读到前 15 行（11/12/13/21/1010/1020/1030/1040/1050/1060/1110/1120/1130…）；其余技能字段【未知】 |
| `timetick` 的语义与客户端如何使用 | 【待验证】服务端只透传 `rpk:Read_uint32()`，**未做任何时间校验**（⇒ 客户端可传任意值；是否被服务端用于回滚判定【未知】） |
| `anger`（怒气）/`combat_power`（战斗力）/`hit`（命中）的消费方 | 【未知】全项目未发现使用 |
| Buff 的 `Range` 字段为何存在 | 【未知】`self.range = tb["Range"]` 存了但无消费方 |
| 是否有 `math.randomseed` | 【未读到】未见调用 |
| 技能特效/动作与客户端的一致性校验 | 【未知】服务端完全不校验 `ActionName`/`Effects_ID` |
| `notiserver` 是否参与战斗通知 | 【未读到】（主体被注释） |
