# CXEngine（YZXY）战斗 / 技能 / combat 目录结构审计

> 回答任务书 Q6（技能如何组织）、Q7（战斗状态如何组织）、Q8（服务端与客户端如何同步）中与战斗相关的部分。
> 标注【已确认】/【待验证】/【未读到】；判定列 ✅ 适合借鉴 / ⚠️ 局部 / ❌ 不适合 / ⛔ 必须排除。

---

## 1. ★ 战斗模式定性：【已确认】回合制

**证据（全部来自代码，不靠"看起来像"）**：

| 证据 | 出处 |
|---|---|
| 状态常量含 `BATTLE_TURN_STAND_BY` / `BTTALE_TURN_EXECUTE` / `BTTALE_TURN_NEXT` | `scripts/combat/combat_context.lua` |
| `BattleMT.turn` 逐回合自增（`NextTurn` 里 `self.turn = self.turn + 1`）| `scripts/combat/combat_system.lua` |
| 一回合先**收集全部指令**再统一执行：`BattleMT:AddCommand` → `CheckStandBy()` → `handle_turn_commands()` | 同上 |
| 指令按 **`CalcSpeed()` 降序**排序后依次结算 | `scripts/combat/server/combat_system.lua:handle_turn_commands` |
| 客户端有"每回合倒计时 30s / 排序 / 下发"的设计文档 | `assets/doc/combat.md` 第 1–4 条 |
| 文档给了状态机 mermaid | `assets/doc/server.md` |

⇒ **CXEngine 的战斗是"独立回合制战斗场景"，与 `analysis/1.4.9/battle/battle_flow.md` 对 JSTM 1.4.9 的判定同类。**
（任务书前提"JSTM 是动作/实时战斗"与本工作区既有取证冲突，详见 `architecture.md` 第 0 节。）

---

## 2. Q7：战斗状态如何组织

### 2.1 目录结构

```
scripts/combat/
├── combat_context.lua            ★ 全部战斗常量（约 40 行）
├── combat_system.lua             ★ BattleMT（共享基类 + 双端分叉入口）
├── skill.lua                     (24 KB) ★ 技能运行时（服务端算 / 客户端播，同一文件用 IsServer 分叉）
├── buff.lua                        Buff 运行时（BuffMT + __actors_buffs__ + 回合结算）
├── server/
│   └── combat_system.lua          服务端：建战场、指令收集、伤害结算、下发
├── client/
│   ├── combat_system.lua          客户端：战场摆位、点击选目标、指令菜单、逐技能播放、本地推进回合
│   └── skill.lua                  客户端专属：calc_run_to_pos、attack_get_keyframe、skill_target_end_counter
├── skill/
│   ├── 1.lua  2.lua  6.lua        SkillOnStart/SkillOnEnd（三个空实现）
│   ├── 20.lua   (横扫千军) SkillOnHit：目标死亡或第 3 连击时给自己加 buff 11
│   └── 26.lua   (催眠符)  SkillOnHit：算封印成功率 → 成功则给对方加 buff 30 + skill.success
└── buff/
    ├── 1.lua    (五庄观_乾坤妙法)  BuffOnStart 创建动画 AddBackAnim
    ├── 11.lua   (大唐官府_横扫千军) BuffOnStart SetOffsetY(10) + 动画
    └── 30.lua   (方寸山_催眠符)    BuffOnStart 覆盖 buff.turn=4；服务端置 BAN_SPELL/BAN_ATK=true；BuffOnEnd 复位
```

`combat_system.lua`（共享）末尾的分叉：

```lua
if IsServer() then script_system_dofile('../combat/server/combat_system.lua') end
if IsClient() then script_system_dofile('../combat/client/combat_system.lua') end
```

### 2.2 `scripts/combat/combat_context.lua` —— 全部常量【已确认】

```lua
PERFRAME_TIME = 0.016*2.5        -- 0.04，帧间隔基准

BATTLE_TYPE_PVE = 0
BATTLE_TYPE_PVP = 1

BATTLE_DEFAULT      = 0
BATTLE_PREPARE      = 1
BATTLE_START        = 2
BATTLE_TURN_STAND_BY= 3
BTTALE_TURN_EXECUTE = 4          -- ★ 原文件就拼错了 "BTTALE"
BTTALE_TURN_NEXT    = 5
BATTLE_END          = 6

COMMAND_STATE_PREPARE = 1
COMMAND_STATE_PALY    = 2        -- ★ "PALY"（PLAY 拼错）
COMMAND_STATE_STOP    = 3
COMMAND_TYPE_ATTACK   = 1
COMMAND_TYPE_CAST     = 2

TEAM_TYPE_ATTACKER = 1
TEAM_TYPE_DEFENDER = 2

SKILL_SUBTYPE_DEFAULT = 0
SKILL_SUBTYPE_SEAL    = 1
SKILL_SUBTYPE_HEAL    = 2
SKILL_SUBTYPE_AUXI    = 3

ACTOR_LIFE_ALIVE    = 0
ACTOR_LIFE_DEAD     = 1
ACTOR_LIFE_DEAD_FLY = 2          -- 「击飞」

SKILL_STATE_DEFAULT = 0
SKILL_STATE_START   = 1
SKILL_STATE_EXECUTE = 2
SKILL_STATE_END     = 3
```

**注意**：`COMMAND_STATE_*` 与 `COMMAND_TYPE_*` 定义了但**在已读代码里无消费者**【已确认】⇒ 预留未接线
（实际指令用的是裸表 `{master, target, skill_id, battle_id}`）。

### 2.3 `BattleMT`（`scripts/combat/combat_system.lua`，共享）【已确认】

```lua
BattleMT = {}
function BattleMT:new(o)
    o = o or {
        id = utils_next_uid('battle'),
        actors = {},
        cmds = {},
        state = BATTLE_DEFAULT,
        turn = 0,
        type = BATTLE_TYPE_PVE,
    }
    self.__index = self; setmetatable(o, self); return o
end
```

| 方法 | 机制 | 标 |
|---|---|---|
| `Serialize()` | → `{id, actors=[{id, team_type, pos_id} 或 {…, props=整个属性字典}], state, turn}`。**NPC 带全量 props，玩家不带** | 【已确认】|
| `Deserialize(info)` | 按 id 找 actor，找不到就 `actor_manager_create_actor` + `SetProperties(props)`；再设 `PROP_TEAM_TYPE`/`PROP_COMBAT_POS_ID` | 【已确认】|
| `FindActor(id)` | 线性遍历 `self.actors` | 【已确认】|
| `AddActor(actor, team_type, pos_i)` | 去重 + **同阵营同位**判重；设 `PROP_TEAM_TYPE`/`PROP_COMBAT_BATTLE_ID`/`PROP_COMBAT_POS_ID` | 【已确认】|
| `RemoveActor(actor)` | 清 `PROP_COMBAT_BATTLE_ID=0`、`PROP_IS_COMBAT=false`，从数组移除 | 【已确认】|
| `AddCommand(actor, cmd)` | `actor:SetProperty(PROP_TURN_READY, true)` + `table.insert(cmds, cmd)` | 【已确认】|
| `AutoCommand(actor)` | `math.random(1,10) <= 5` → 普攻类技能，否则法术类；目标 `RandomSelectEnemy` | 【已确认】|
| `RandomSelectEnemy(self_actor)` | 取**不同阵营**的随机一个 | 【已确认】|
| `PrepareBattle()` | `state=PREPARE`；客户端额外 `on_battle_prepare(self)` | 【已确认】|
| `StartBattle()` | `state=START`、`turn=0`、给全体置 `PROP_COMBAT_BATTLE_ID`/`PROP_IS_COMBAT=true`；**服务端把全体 HP 重置为 `GetMaxHP()`**；然后 `NextTurn()` | 【已确认】|
| `NextTurn()` | `turn++`、`cmds={}`、`state=TURN_STAND_BY`；服务端给全体清 `PROP_TURN_READY` 并对 `PROP_IS_AUTO_COMMAND` 的 actor 自动出指令；然后 `process_turn_buffs(self)` | 【已确认】|
| `CheckStandBy()` | 全体 `PROP_TURN_READY` 为真 | 【已确认】|
| `CheckEnd()` | 遍历角色，一方全 `IsDead()` 即结束 | 【已确认】|
| `CheckAllIdle()` | 全体动作是 `ACTION_BATIDLE`/`ACTION_IDLE`（客户端表现用）| 【已确认】|
| `InBattle(actor)` | 是否在 `actors` 里 | 【已确认】|
| `EndBattle()` | `state=END`；清 `PROP_IS_COMBAT`/`PROP_COMBAT_BATTLE_ID`；客户端额外 `combat_reset_actor` + `animation_manager_clear` + 恢复 BGM + `timer_manager_pause_timer('TimerWildBattle',false)`；**销毁所有 NPC actor**；清空 `actors` | 【已确认】|
| `GetNotReadyActors()` | ⚠️ **bug**：内部写 `if not actor:GetProperty(...)`（`actor` 是 nil 全局，应为 `_actor`）| 【已确认】|

### 2.4 回合状态机（实际流转）【已确认】

```
              战斗创建(CREATE)
                    ↓
              BATTLE_PREPARE(1)        客户端：reset_actor_pos 摆位
                    ↓ StartBattle()
              BATTLE_START(2)          服务端：全体 HP=MaxHP；客户端：摆位 + 切战斗 BGM
                    ↓ NextTurn()
        ┌────→ BATTLE_TURN_STAND_BY(3)  收指令：每个 cmd AddCommand + TURN_READY=true
        │           ↓ CheckStandBy() 全真
        │      BTTALE_TURN_EXECUTE(4)   handle_turn_commands：按速度排序 → 逐条结算 → 下发 all_skills
        │           ↓ CheckEnd()?
        │      ┌────┴────┐
        │    是 │         │ 否
        │  BATTLE_END(6)  └→ NextTurn()（turn++, 清 ready, AutoCommand, 结算 buff）──┐
        └──────────────────────────────────────────────────────────────────────┘
```

`assets/doc/server.md` 里的 mermaid **与代码一致**（只是把 `BATTLE_TURN_STAND_BY→BTTALE_TURN_NEXT` 的顺序画得不够精确）。

---

## 3. Q6：技能如何组织

### 3.1 静态数据：`assets/tables/skill.tsv`

```
ID	name	sound	type	sub_type	school	combo	atk_anim	group_kill	cast_anim	act_turn
*0			atk	0	0	0				
1	普攻		atk				0-1D3FF13C			
2	DF_冤魂不散		spell		9		6-4EA6D4BF			
16	DT_后发制人	21-39d047a5	atk		1		6-39B69986			
20	DT_横扫千军	21-30d78cef	atk		1	3	6-ACA4A54A			2
21	DT_破釜沉舟		atk		1		6-78D6FD06	3		
26	FC_催眠符		spell	1	2		6-9EC0624E			
```

| 列 | 含义 | 判定 |
|---|---|---|
| `type` | `atk` / `spell` / `flee` / `idle`（`skill.lua:on_using_skill` 分派）| 【已确认】|
| `sub_type` | `0=DEFAULT 1=SEAL 2=HEAL 3=AUXI` | 【已确认】|
| `school` | 门派；**`0` = 通用（NPC/召唤兽用）** | 【已确认】|
| `combo` | 连击次数 | 【已确认】|
| `group_kill` | **群体攻击目标数**（`>0` 时群体，`1` 表示只有主目标） | 【已确认】|
| `atk_anim` / `cast_anim` | 技能动画资源 ID（`pack-WASID`） | 【已确认】|
| `act_turn` | 疑似"行动回合数/吟唱"，**在已读代码里无消费者**【已确认】 | ⚠️ |
| 命名 | `门派缩写_技能名`（`DF_`地府 `DT_`大唐 `FC_`方寸 `HS_`化生 …）| — |

**硬编码技能 ID 约定**【已确认】：

| ID | 用途 | 出处 |
|---|---|---|
| `1` | 普通攻击（`process_turn_command` 里 `if skill_id == 1` 单独判 `PROP_COMBAT_SKILL_BAN_ATK`）| `skill.lua` |
| `264` | 防御（客户端按钮直接发 `skill_id = 264`）| `combat/client/combat_system.lua` |
| `268` | 逃跑（客户端按钮直接发 `skill_id = 268`）| 同上 |
| 断言 | `assert(msg.skill_id ~= 0 and msg.skill_id < 300)` | 同上 |

⇒ **门派/技能靠拍数字**，很脆弱；但断言 `skill_id < 300` 至少拦住越界。

### 3.2 动态数据 + 脚本回调：`scripts/combat/skill.lua`

**加载（启动期）**【已确认】：

```lua
skill_table = {}                       -- 全局，来自 skill.tsv
local skill_env = { __index = _ENV }   -- 沙箱：能读全局，但写只落到自己

function init_skills()
    local skill_template_tbl = content_system_get_table('skill')
    skill_table = skill_template_tbl
    for id, skill in pairs(skill_table) do
        local dir  = vfs_get_luapath('../combat/skill/')
        local path = dir .. id .. '.lua'
        local f = io.open(path)
        if f then
            local chunk = f:read('a'); f:close()
            local module = setmetatable({}, skill_env)
            local fun, err = load(chunk, '@'..path, 'bt', module)
            if fun then
                fun()
                skill.SkillOnStart = module.SkillOnStart
                skill.SkillOnEnd   = module.SkillOnEnd
                skill.SkillOnHit   = module.SkillOnHit
            else cxlog_info(fun, err) end
        end
    end
end
```

⇒ **"表给静态数据 + 同 ID 的 Lua 文件给逐技能特化逻辑，回调挂到表行上"**，是清晰且可扩展的设计。

**每回合执行（`process_turn_command`）**【已确认】：

```lua
function process_turn_command(battle, master_id, target_id, skill_id)
    local master = battle:FindActor(master_id)
    if not master or master:IsDead() then return end

    local skill = { id=utils_next_uid('skill'), lv=master:GetProperty(PROP_LV),
                    tid=skill_id, master=master, state=SKILL_STATE_DEFAULT, success=true }
    local target = battle:FindActor(target_id)
    if not target then                      -- 目标已死/已逃 → 随机换一个敌人
        ... 从不同阵营随机取 ...
    end
    skill.target = target
    skill.turn = battle.turn
    skill.templ = skill_table[skill_id]
    skill_init_by_templ(skill, skill.templ)

    -- 封禁校验
    if skill_id == 1 then
        if master:GetProperty(PROP_COMBAT_SKILL_BAN_ATK) then return end
    elseif skill.type == 'atk' or skill.type == 'spell' then
        if master:GetProperty(PROP_COMBAT_SKILL_BAN_SPELL) then return end
    end
    return on_using_skill(battle, skill)
end
```

**服务端结算（`base_using_skill` 的 `IsServer()` 分支）**【已确认】：

```lua
function base_using_skill(battle, skill)
  if IsServer() then
    local cskill = init_cskill(skill)              -- {id, tid, turn, master=主人id, targets={}, effects={}}
    local master = skill.master
    if skill.SkillOnStart then skill.SkillOnStart(skill, master) end

    local targets = battle_get_group_kill_targets(battle, skill.group_kill, skill.target)
    for target_i, target in ipairs(targets) do
        table.insert(cskill.targets, target:GetID())
        local effect = { target_id = target:GetID(), hp_deltas = {} }
        skill.max_hit_cnt = skill.combo > 0 and skill.combo or 1
        for hit_i = 1, skill.max_hit_cnt do
            effect.combo = hit_i
            skill_take_effect_on_target(skill, effect, master, target, target_i, hit_i)
            if master:IsDead() or target:IsDead() then break end
        end
        -- 击飞检查：NPC/召唤兽死 → ACTOR_LIFE_DEAD_FLY，移出战斗
        local master_life_state = check_life_state(master)
        if master_life_state == ACTOR_LIFE_DEAD_FLY then battle:RemoveActor(master) end
        local target_life_state = check_life_state(target)
        if target_life_state == ACTOR_LIFE_DEAD_FLY then battle:RemoveActor(target) end
        effect.life_state = { master = master_life_state, target = target_life_state }
        table.insert(cskill.effects, effect)
    end
    if skill.SkillOnEnd then skill.SkillOnEnd(skill, master) end
    cskill.success = skill.success
    return cskill                                   -- ★ 返回给 handle_turn_commands 打包下发
  else
    ... 客户端播放分支 ...
  end
end
```

**伤害落点（`skill_take_effect_on_target`）**【已确认】：

```lua
if skill.type == 'atk' then
    local hp_delta = master:GetAttackDamage(target, false, false, 0, 1)   -- 注意：暴击/连击系数传死值
    target:ModifyHP(-hp_delta)
    table.insert(effect.hp_deltas, { target = -hp_delta })
elseif skill.type == 'spell' then
    if sub_type == SEAL or sub_type == AUXI then
        -- 无伤害（封印/辅助效果由 SkillOnHit 处理）
    elseif sub_type == HEAL then
        local hp_delta = master:GetSpellDamage(target); target:ModifyHP(hp_delta)
    elseif sub_type == DEFAULT then
        local hp_delta = master:GetSpellDamage(target); target:ModifyHP(-hp_delta)
    end
end
if skill.SkillOnHit then skill.SkillOnHit(skill, master, target, target_i, hit_i) end
```

⇒ **【已确认】"客户端只收到结果"**：`GetAttackDamage(..., false, false, 0, 1)`
把 `is_critical=false, is_combo=false` 写死 ⇒ **暴击/连击在当前实现里没有真正生效**（公式支持，调用点未接）。
`sub_type == SEAL` 的成功率完全由 `skill/26.lua` 的 `SkillOnHit` 自行计算并写 `skill.success`。

**客户端播放（`IsClient()` 分支）**【已确认】：`on_using_skill` → `base_using_skill` 的 else 分支 →
按 `skill.type` 分派：

| type | 客户端函数 | 表现 |
|---|---|---|
| `atk` | `skill_cast_atk(battle, skill)` | `ClearAction` → `PushAction(BATIDLE)` → `RUNTO`（`MoveOnScreenWithDuration`）→ `PushAction(ATTACK)`（`SetLoop(combo)`，关键帧回调 `on_attack_action_callback`）→ `RUNBACK` |
| `spell` | `skill_cast_spell(battle, skill)` | `PushAction(CAST)`，半程回调里对每个目标创建法术动画（`skill_create_spell_anim`），按 `sub_type` 决定飘字/动画时机 |
| `flee` | `skill_cast_flee(battle, skill)` | 反向 + `MoveOnScreenWithDuration` 移出屏幕；`on_using_skill_update` 里按坐标判结束 |

**攻击表现的核心回调 `on_attack_action_callback(attack_action)`**（客户端）【已确认】：
- 每次攻击帧 → `atk_info.atk_counter++` → 给 target `PushAction(ACTION_BEHIT)` →
  受击第 1 帧创建 `skill.atk_anim` 的法术动画 → 调用 `skill.SkillOnHit(skill, master, target, group_kill_counter, atk_counter)` →
  播放受击音效 → `target:ShowBeatNumber(damage)`（伤害数字来自服务端算好的 `atk_info.hp_deltas[...]`）→
  双方向屏幕位移 + `Pause(动画组帧时间)`。
- 受击停止回调里判 `life_state`：
  `ACTOR_LIFE_DEAD_FLY` → `skill_play_target_dead_fly`（带边界反弹的抛物线击飞，撞到屏幕边就 `combat_system_remove_from_battle`）；
  `ACTOR_LIFE_DEAD` → 播 `ACTION_CLPS` 倒地；
  否则回退位移。

⇒ **【已确认】客户端与服务端的"确定性重放"靠服务端下发的 `hp_deltas` 与 `life_state`，客户端不自己算伤害。**

### 3.3 一个逐技能脚本样例（`scripts/combat/skill/26.lua`，催眠符）【已确认】

```lua
function SkillOnStart(skill, actor, target) end

function SkillOnHit(skill, actor, hit_actor)
    if IsServer() then
        local skill_lv      = actor:GetProperty(PROP_SCHOOL_SKILL_LV_SPIRITUAL)   -- ★ 用"灵力技能等级"
        local target_lv     = hit_actor:GetProperty(PROP_LV)
        local practice_lv   = actor:GetProperty(PROP_SPELL_PRACTICE_SKILL_LV)     -- 法修
        local resistance_lv = hit_actor:GetProperty(PROP_SPELL_RESISTANCE_SKILL_LV) -- 法抗
        local rate = formula_calc_seal_success_rate(skill_lv, target_lv, practice_lv, resistance_lv)
        local random_rate = math.random()
        if random_rate < rate then
            skill.success = true
            actor_add_buff(hit_actor, 30)         -- 30 = 方寸山_催眠符 buff
        else
            skill.success = false                 -- ★ 写进 skill，随后进入 cskill.success 下发
        end
    end
    if IsClient() then
        if skill.success then actor_add_buff(hit_actor, 30) end   -- 客户端按同一结果加 buff 表现
    end
end
function SkillOnEnd(skill, actor, target) end
```

⇒ **"随机数只在服务端摇，结果随 `skill.success` 下发，客户端照结果播表现"** —— **这是本项目战斗同步最正确的一处**，值得 JSTM 学。
（对比：`skill/20.lua` 里暴击/连击判断在服务端写死为 `combo_i == 3`，客户端则用 `skill.effects[target_i].combo == combo_i` 判 —— 形式不同但结果一致。）

---

## 4. buff 体系（`scripts/combat/buff.lua` + `buff/<id>.lua`）

### 4.1 静态数据：`assets/tables/buff.tsv`

```
ID	name	type	buff_anim	turn
1	五庄观_乾坤妙法		23-7F842CEF	
11	大唐官府_横扫千军		23-D9463A0C	2
30	方寸山_催眠符		23-CA8FDEAD	
```

### 4.2 运行时【已确认】

```lua
local BuffMT = {}
function BuffMT:new(o) ... end                       -- 定义了但已读代码未使用

local buff_table = {}
function init_buffs()                                -- 与 init_skills 同构：表 + buff/<id>.lua 回调
    buff_table = content_system_get_table('buff')
    for id, buff in pairs(buff_table) do
        -- load(chunk,'@'..path,'bt', module) → 挂 BuffOnStart / BuffOnEnd / BuffOnNextTurn
    end
end

function init_buff_by_templ(buff, templ)             -- buff 实例从模板取 turn 与三个回调
    buff.turn = templ.turn
    buff.turn_count_down = buff.turn
    buff.BuffOnStart = templ.BuffOnStart
    buff.BuffOnEnd = templ.BuffOnEnd
    buff.BuffOnNextTurn = templ.BuffOnNextTurn
end

__actors_buffs__ = {}                                -- ★ 全局：actor_id → {buff_id → buff}
function actor_get_buffs(actor) ... end
function actor_add_buff(actor, buff_tid)             -- 建实例 + 入表 + 立即 BuffOnStart
function actor_remove_buff(actor, buff_id)           -- BuffOnEnd + 移除
function actor_remove_buff_by_tid(actor, buff_tid)   -- 按模板 id 移除

function actor_buff_next_turn(actor)                 -- 回合递减
    for id, buff in pairs(actor_get_buffs(actor)) do
        if buff.turn_count_down > 0 then
            buff.turn_count_down = buff.turn_count_down - 1
            if buff.turn_count_down == 0 then actor_remove_buff(actor, buff.id)
            else if buff.BuffOnNextTurn then buff.BuffOnNextTurn(buff, actor, buff.turn - buff.turn_count_down) end end
        end
    end
end

function process_turn_buffs(battle)                  -- 由 BattleMT:NextTurn 调用
    for i, actor in ipairs(battle.actors) do actor_buff_next_turn(actor) end
end
```

### 4.3 buff 脚本样例（`scripts/combat/buff/30.lua`，催眠符的封禁效果）【已确认】

```lua
function BuffOnStart(buff, actor, target)
    buff.turn = 4                      -- ★ 覆盖表里的 turn（表里 30 的 turn 为空）
    buff.turn_count_down = 4
    if IsServer() then
        actor:SetProperty(PROP_COMBAT_SKILL_BAN_SPELL, true)
        actor:SetProperty(PROP_COMBAT_SKILL_BAN_ATK, true)
    end
    if IsClient() then
        local anim = animation_create(23, 0xCA8FDEAD)
        buff.anim = anim; anim:SetLoop(0)
        actor:AddBackAnim(anim)        -- 挂在角色背后循环播放
    end
end

function BuffOnEnd(buff, actor, target)
    if IsServer() then
        actor:SetProperty(PROP_COMBAT_SKILL_BAN_SPELL, false)
        actor:SetProperty(PROP_COMBAT_SKILL_BAN_ATK, false)
    end
    if IsClient() then buff.anim:Stop() end
end
```

⇒ **【已确认】buff 的"逻辑效果（改属性）"在服务端，"表现（动画）"在客户端，同一个文件用 `IsServer()/IsClient()` 并列写。**
`BuffOnStart` 里**直接覆盖 `buff.turn`** 说明"时长可以写在脚本里而不写在表里"——灵活但两处真源。

### 4.4 buff / 状态同步的关键事实【已确认】

| 事实 | 说明 |
|---|---|
| buff 存在**服务端 `__actors_buffs__` 全局表**里（不在 actor 属性里）| 客户端从哪里知道 buff？⇒ **只能通过 `SkillOnHit` 里 `actor_add_buff(hit_actor, 30)` 与服务端同规则执行**（`skill/26.lua` 的 `IsClient()` 分支就是这么做的）|
| ⇒ **没有"buff 列表同步协议"** | 客户端靠**重放同一段判定逻辑**得到 buff 状态（`skill/20.lua` 也是同样套路）|
| ⇒ 后果 | 一旦服务端与客户端判定不一致（随机数、时序、缺事件），**buff 会两端不一致且无纠正机制** |
| `PROP_ASM_BUFF_ANIM` | 属性存在（`actor_template.tsv` 与枚举里都有）。grep 全仓库仅 6 处命中：定义/注册/文档 + `common/src/actor/action.cpp:188`（**读**）+ `scripts/combat/client/combat_system.lua:82`（`combat_reset_actor` 里清 **0**）⇒ **没有任何地方写入真实动画 ID**，属预留未接线【已确认】|

---

## 5. Q8：服务端与客户端如何同步（战斗部分 + 全局）

### 5.1 全局同步机制的三个层次【已确认】

| 层次 | 机制 | 协议 |
|---|---|---|
| **① 进场全量** | 登录时给本人发全部玩家属性、给他人发新玩家、再发 NPC 列表；战斗开始时发整个 `battle:Serialize()` | `PTO_C2C_PLAYER_ENTER`、`PTO_C2C_ACTOR_ENTER`、`PTO_S2C_COMBAT_CREATE/START` |
| **② 脏属性增量** | 每 tick 扫玩家 + 召唤兽的 `IsDirty()`，用 TSV `sync` 列过滤，打包 `[pid, prop_id, value]` 数组 | `PTO_S2C_SYNC_PROPS` |
| **③ 战斗回合结果** | 服务端算完整回合结果（含 `hp_deltas`/`life_state`），一次性下发，客户端照数据播动画 | `PTO_S2C_COMBAT_EXECUTE` |

**CXEngine 缺失的机制**（均在已读代码中不存在【已确认】）：AOI/视野裁剪、帧同步、快照插值、**回合超时**、
断线重连补发、校验和、**观战**、**战斗录像**、**出手顺序列表下发**、**单位状态每回合重推**。
⚠️ 注意：**"客户端 ACK"不算 CXEngine 的缺失**——JSTM 真机客户端同样不发完成回执（见 §5.2 订正），
所以**不应**把"有 ACK"当作 JSTM 的既有优势；JSTM 的既有优势是**字段集丰富**（§5.6）与**单位状态每回合重推**。
【已确认】`PTO_S2C_SYNC_PROPS` 是**广播给所有玩家**（`net_send_message_to_all_players`），不做筛选。

### 5.2 战斗同步完整时序【已确认，逐跳有代码】

```
客户端                                    服务端
  │ 点怪/暗雷(15s timer)                     │
  ├─ CS PTO_C2S_COMBAT_PVE_START {pid} ────▶│  combat_system_create_pve_battle(player)
  │                                          │   ├ scene_monster[场景名].monster → 筛 avatar_summon 里有的
  │                                          │   ├ enemy_count 按队伍人数随机(1~3 / 2~4 / … / 7~10)
  │                                          │   ├ 对每只怪：actor_manager_create_actor(uid)
  │                                          │   │   SetProperty(LV=玩家LV, ACTOR_TYPE=NPC, IS_AUTO_COMMAND=true)
  │                                          │   │   ClearAssignPoints + ApplySummonQual + 五项 ASSIGN_* = 玩家LV
  │                                          │   │   math.random(1,10)==1 → actor:Variation()   (10% 变异)
  │                                          │   └ battle:AddActor(怪, TEAM_TYPE_DEFENDER, i)
  │                                          │  battle:StartBattle()   (全体 HP=MaxHP)
  │◀─ SC PTO_S2C_COMBAT_START {battle=Serialize()} ─┤  combat_system_send_message(只发给玩家)
  │  BattleMT:Deserialize → 建怪 → 找自己 → local_team_type
  │  on_battle_start → reset_actor_pos（固定 10 己方 / 10 敌方坐标）
  │  combat_system_update → state==TURN_STAND_BY → ImGui 菜单选技能
  ├─ CS PTO_C2S_COMBAT_CMD {master,target,skill_id,battle_id} ─▶│  battle:AddCommand(master, req)
  │                                          │  CheckStandBy()?  全部 TURN_READY 才继续
  │                                          │  state = BTTALE_TURN_EXECUTE
  │                                          │  handle_turn_commands(battle):
  │                                          │    table.sort(cmds, by CalcSpeed() desc)
  │                                          │    for cmd: process_turn_command → cskill
  │                                          │    收集 all_skills[]
  │◀─ SC PTO_S2C_COMBAT_EXECUTE [cskill, …] ─┤  发给每个玩家
  │  battle_commands = cskill_to_skill(每个)
  │  combat_system_update: 逐个播（DEFAULT→START→END）
  │    on_using_skill → skill_cast_atk / skill_cast_spell
  │    on_using_skill_update(caster_end && target_end) → 下一个
  │  播完所有技能 → CheckEnd()?
  │     ├ 否 → battle:NextTurn()   ★★ 客户端自己推进回合！
  │     └ 是 → battle:EndBattle() → combat_system_end_battle()
  ├─ CS PTO_C2S_COMBAT_END_BATTLE {pid,battle_id} ─▶│  EndBattle() + SC PTO_S2C_COMBAT_END_BATTLE
```

**★ 最关键的一处不兼容点【已确认】**：

> **CXEngine 的回合推进是"客户端本地"的**（`combat/client/combat_system.lua:combat_system_update` 在技能播完后
> 直接调 `battle:NextTurn()`，服务端**不知道客户端播完了**）。
> 服务端的 `NextTurn()` 只在 `stub[PTO_C2S_COMBAT_CMD]` 里被调（即收到下一条指令时）。
> ⇒ 服务端与客户端**各自独立维护 `turn` 计数**，靠"下一条 CMD 到达"隐式对齐。

> ### ⚠️ 本节第一版有错，已订正（2026-09 追加）
>
> **第一版我写的是**：JSTM 是「服务端推 `SC_20012/20013` → 客户端播完发 `CS_20014` 回执 → 服务端推进」的
> **ACK 节流模型**，因此「两者回合节奏所有权相反」。
> 该表述**依据错误**：它来自 `analysis/1.4.9/battle/battle_chain_verified.md`，而那份文档描述的
> **是我们自己 `mock_server.py` 的实现**（`行 2445 if cmd == 20014:` —— 我们自己把 20014 当成推进条件），
> **不是真实客户端的行为**。
>
> **字节码权威来源 `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1 的真机订正明确记载**：
>
> | 观察 | 结果 |
> |---|---|
> | 客户端是否发 `CS_20011`（加载完成）| ❌ **从未发出**（整场战斗 `tcp.log` 无 `cmd=20011`）|
> | 客户端是否发 `CS_20014`（动画播放完成）| ❌ **从未发出**（无 `cmd=20014`）|
> | 客户端收到 `SC_20020` 后 | ✅ **主动发了 `CS_20021`**（`csCloseFinishView`）|
>
> 原文结论：「⇒ **整场战斗会停在第一回合之前，除非服务端自己推进**」，
> 现阶段的可行做法是「服务端在 `SC_20010` 之后**自己按节拍推进（2.5 秒/回合，自续期）**；
> `CS_20014` 仍然接收并记录，但**不作为推进的必要条件**」；
> 并注明「**客户端为何不发 20014 尚未定位**」。
>
> **⇒ 订正后的正确表述**：
> - JSTM 真机客户端**同样不给"我播完了"的回执** ⇒ **JSTM 也必须由服务端自定节拍**。
> - 因此 **CXEngine 与 JSTM 在"服务端不等客户端"这一点上其实是相似的**
>   （CXEngine：**客户端**自己推；JSTM：**服务端**自己推）。**"所有权相反"的说法不成立。**
> - ⇒ 我此前给出的"照搬会丢掉 `CS_20014` 节流"这一**理由作废**（没有节流可丢）。

**那么"CXEngine 回合制战斗状态机不能移植到 JSTM"的真正原因是什么？**
换成下面 5 条**有 JSTM 侧字节码字段证据**的理由（见下节 5.6 的字段对照）：

1. **数据模型表达能力不足**：JSTM 的 `SC_20010` 带 CXEngine 完全没有的
   **阵法**（`atk_formation_type/lev`、`def_formation_type/lev`）、**回合波次**（`round_wave`/`wave_max`/`wave_no`）、
   **观战标记**（`is_observer`）、**战斗特效**（`effect_id`），单位是 **18 字段**（含 `specials[]`/`skills[]`/`animate_res[]`）；
   而 CXEngine 的 `BattleMT:Serialize()` 只有 `{id, team_type, pos_id}`（NPC 再加 `props`）。
   ⇒ **CXEngine 的战场结构表达不了 JSTM 的一回合**。
2. **单位状态是"每回合重推"的**：JSTM 的 `SC_20013.summon_play[]` 每回合携带单位的
   `hp_max/hp/anger/is_auto/animate_res[]/skills[]/specials[]`；CXEngine **没有任何单位重推机制**，
   buff 状态甚至**完全不上线**（见 §4.4）。
3. **线格式与协议哲学不同**：JSTM `[u32 BE len][u16 BE cmd][二进制字段序]` vs CXEngine `[LE u32][LE u32][JSON]`（见 §5.6）。
4. **JSTM 有 CXEngine 没有的整块子系统**：观战（`20016/20017`）、战斗录像（`20025–20030`）、
   自动战斗（`20008` + 客户端 `dungeon/auto_fight.luac`）、客户端侧战斗演算校验（`10601/10610`）。
5. **安全模型与内容不可复用**（见 `reuse_candidates.md` §2.3 / §2.5）。

### 5.6 JSTM 战斗消息的权威字段（`cmd_resolve_200.luac` 直读，供上条 5 个理由取证）

工具：`python tools/proto_spec.py cmds 20012 20013` / `dsc SC_20013`（源：`protocol/fields.json` 1.28 MB，3553 条）。

**`SC_20012` 小回合战斗效果**（`battle_ctrl` → `Battle:doNextFrame`）：

| 字段 | 类型 |
|---|---|
| `round` | `uint16` |
| `skill_play[]` | `order:uint8, user_id:uint16, skill_id:uint32, father_id:uint32, father_skill_id:uint32, passive_skill_id:uint32, user_anger:uint16, talk:string, notice:string, magic_play[]:`Dsc20012magic_play`, summon_play[]:`Dsc20012summon_play` |
| `cooldown[]` | `bid:uint32, last_use:uint16` |

**`SC_20013` 回合开始（伤害落点）**（`battle_ctrl` → `Battle:playRoundStart`）：

| 字段 | 类型 |
|---|---|
| `round` | `uint16` |
| `round_wave` | `uint16` |
| `time` | `uint8` |
| `wave_no` | `uint8` |
| `magic_play[]` | `order:uint8, target_anger:uint16, target_id:uint16, source_id:uint16, hit:int8, hp_max:uint32, hp:uint32, is_target_die:uint8, target_talk:string, magic_list[]:`Dsc20013magic_list` |
| `summon_play[]` | `id:uint16, rid:uint32, srv_id:string, name:string, lev:uint16, sex:uint8, career:uint16, pos:uint8, group:uint8, hp_max:uint32, hp:uint32, anger:uint32, is_auto:uint8, animate_res[]:`Dsc20013animate_res`, skills[]:`Dsc20013skills`, specials[]:`Dsc20013specials` |
| `order_list[]` | `id:uint32` |

**`SC_20010` 战斗初始化的单位字段**（18 字段，含 `skills[] = (bid:u32, step:u8, last_use:u16, cd:u16)`、
`specials[] = (key:u8, val:u32)`、`animate_res[] = (ant_id:u16, ant_val:s, ent_lev:u8, dis_method:u8)`），
**顺序须按 `battle_protocol_matrix.md` §4.6 的订正**（`Dsc*` 子结构在 `manual.md`/`fields.json` 里是反的）。

> ### ✅ 上面这条【尚未确认】已解出（补读，详见 **`jstm_battle_fields.md`**）
> 用 `tools/dsc_spec.py --file 200` 展开（共 16 个子结构）得到：
>
> **`magic_list` 元素**（proto#24 / proto#37，格式串 `iiChhC`）—— **★ buff/状态条目**：
>
> | 字段 | 类型 | 语义 |
> |---|---|---|
> | `magic_bid` | `int32` | 效果 ID → `Config.SkillMagic[magic_bid]`（**12665 行**）|
> | `change_hp` | `int32` | 每回合 HP 变化（DoT/HoT）|
> | **`duration`** | **`uint8`** | **★ 持续/剩余回合** |
> | `per` | `int16` | 百分比（模板占位 `{per}`）|
> | `val` | `int16` | 绝对值（模板占位 `{val}`）|
> | **`fold`** | **`uint8`** | **叠加层数**（UI 渲染 `'(%s层) '`）|
>
> **`magic_play`** = `order, target_anger, target_id, source_id, hit:int8, hp_max, hp, is_target_die, target_talk, magic_list[]`（10 字段）
> **`summon_play`** = 16 字段（`id, rid, srv_id, name, lev, sex, career, pos, group, hp_max, hp, anger, is_auto, animate_res[], skills[], specials[]`）
>
> **⇒ 第 2 个未知项（buff 剩余回合是否下发）答案：下发，= `magic_list[].duration:uint8`。**
> 且同时下发 `fold`（层数）、`change_hp`（每回合HP变化）、`val`/`per`（数值/百分比）。
> 客户端证据：`battle_role.luac` proto#4 用 `duration` + `fold` 渲染 buff 提示框，
> 类别取自 `Config.SkillMagic[bid].type`（控制效果/增益效果/减益效果）；
> `battle.luac` proto#126 判 `entry.duration >= 0` 决定效果是否仍在生效。
>
> ⚠️ **同时纠正一个我犯过的错**：`specials` **不是** buff 载体。
> 穷举（扫 `assets/src/game/**` 全部 `.luac` 的 `keyfind('key', n, specials)` 模式）显示：
> 全仓库**只有 8 个 key（1,2,4,5,6,7,8,9）**，全部在 `battle_role.luac` proto#2（`createBattleRole`）消费，
> `val` 是 `Config.PartnerBase` / `PartnerStageEffect` / `PartnerHaloEffect` / `PartnerRebirthEffect` 的**配置 ID**,
> 语义 = 伙伴**模型(1,2)、配色·评分(4)、阶段特效(5)、光环特效(6)、重生特效(7,8)、羁绊伙伴标记(9)**。
> **⇒ `specials` 是外观通道；buff 载体是 `magic_list`。**
> 配置侧另有 `Config.SkillMagicType` = **31 个效果属性 ID**（1010–1280，含 `1240 control`、`1250 anti_control`、`1130 cure`）。
>
> ### 补充：真机捕获（client ↔ 我们自己的 mock）给出的两条可用事实
> 依据 `logs/1.4.9/battle/battle_raw_tcp.log`、`battle_action.log`、`battle_render_chain.log`（**只读**），详见 `jstm_battle_fields.md` §9。
>
> | # | 事实 | 对本报告的意义 |
> |---|---|---|
> | 1 | **战斗内客户端唯一主动上报 = `CS_20021`**（收到 `SC_20020` 后立刻发，body 4 字节 = 被击败怪物 `mon_id`）；`CS_20011`/`CS_20014` 在 4 场完整战斗捕获中**零次** | 强化 §7 的"回合驱动"结论：**JSTM 客户端确实不回报"播完了"**，服务端只能自定节拍 |
> | 2 | **客户端对空的 `magic_list`/`summon_play`/`order_list`/`cooldown` 宽容**：mock 全发空表，客户端仍完整跑通 4 回合 + 结算（逻辑链 `playEnterEffect → start → createBattleScene → addRole×2 → roleReady×2 → playRoundStart×4 → playMagic → result → clear → exitFight`）| **buff 可后置实现**：先跑通无 buff 的战斗，再逐条填 `magic_list`，**不会被空表阻塞** |
> | 3 | ⚠️ `CS_20500/20501/20504/20800` **不是战斗命令**（分别是好友 / 好友列表 / 任务列表 / 英雄-背包-外观阶段），只是与进战斗同时发生的界面刷新 | 避免把它们误当战斗协议 |
> | 4 | ⛔ **"`magic_list` 全量还是增量"在本工作区不可取证**：原版服务端数据多处明确记载**不可得**，现存捕获全是 mock 流量且 mock 发空 `magic_list`（`server/battle.py:305`）| **不再追这条线**；JSTM 按"**每回合全量重列**"实现（`duration` 每回合必变、与 `summon_play` 每回合重推同构）|
>
> **交叉验证**：客户端 `bt_in` 探针记录的反序列化表（`battle_action.log:12`）里 `magic_play[1]` **确实带 `magic_list` 子键**，
> 且出现的键（`round`/`round_wave`/`wave_max`/`wave_no`/`time`/`is_observer`/`atk_formation_lev`/`def_formation_lev`/`effect_id`/`order_list`/`fighter_info_list`/`skill_play`/`cooldown`/`summon_play`）
> 与本文 §5.6 的静态规格**逐一对应** ⇒ **运行期反证了静态字段表**。
> （`server/battle.py:33` 亦早已独立还原出同一 `magic_list` 格式串 `magic_bid@i, change_hp@i, duration@C, per@h, val@h, fold@C`，与本轮直读结果一致 ⇒ 相互印证。）

### 5.3 PVE 战斗的怪物生成（`combat_system_create_pve_battle`）【已确认】

```lua
local scene_monster_tbl = content_system_get_table('scene_monster')   -- 按场景名 → 怪物名列表
local avatar_summon     = content_system_get_table('avatar_summon')    -- 只有能作为模型的才算
-- 筛出 monsters
local enemy_count
if team then
    local n = #team:GetMembers()
    if     n == 1 then enemy_count = math.random(1,3)
    elseif n == 2 then enemy_count = math.random(2,4)
    elseif n == 3 then enemy_count = math.random(3,6)
    elseif n == 4 then enemy_count = math.random(5,8)
    elseif n == 5 then enemy_count = math.random(7,10) end
else enemy_count = math.random(1,3) end

for i = 1, enemy_count do
    local actor = actor_manager_create_actor(utils_next_uid('actor'))
    actor:SetProperty(PROP_LV, player_lv)          -- ★ 怪物等级 = 玩家等级（无成长曲线）
    actor:ClearAssignPoints()
    actor:ApplySummonQual(monster_name)            -- 用 summon_quality 表的资质
    actor:SetProperty(PROP_ASSIGN_HEALTH, player_lv)   -- ★ 五项加点也 = 玩家等级
    ... (MAGIC/FORCE/STAMINA/AGILITY 同)
    actor:SetProperty(PROP_IS_AUTO_COMMAND, true)  -- 怪物自动出招
    if math.random(1,10) == 1 then actor:Variation() end   -- 10% 变异（换色）
    battle:AddActor(actor, TEAM_TYPE_DEFENDER, i)
end
```

⇒ **暗雷战斗的怪物是"动态创建 + 纯等级缩放"**，无模板表、无 AI、无掉落（掉落完全未实现）。
怪物名字/模型来自 `avatar_summon`（把召唤兽当怪物用），这也解释了为什么 `ACTOR_TYPE_NPC` 与 `SUMMON` 共享公式。

### 5.4 PVP 战斗【已确认】

```lua
function combat_system_create_battle(atk_actor, def_actor)
    local battle = BattleMT:new()
    local team = atk_actor:GetTeam()
    if team and team:HasMember(def_actor) then return end     -- 同队不能打
    combat_system_add_team_by_actor(battle, atk_actor, TEAM_TYPE_ATTACKER)
    combat_system_add_team_by_actor(battle, def_actor, TEAM_TYPE_DEFENDER)
    __battles__[battle.id] = battle
    return battle
end

function combat_system_add_team_by_actor(battle, actor, team_type)
    if actor:HasTeam() then
        local team = actor:GetTeam()
        for i, mem in ipairs(team:GetMembers()) do battle:AddActor(mem, team_type, i) end
        for i, mem in ipairs(team:GetMembers()) do
            if mem:IsPlayer() then
                local summon = mem:GetSummon()
                if summon then battle:AddActor(summon, team_type, i+5) end   -- ★ 宝宝占 i+5 位
            end
        end
    else
        battle:AddActor(actor, team_type, 1)
        if actor:IsPlayer() then
            local summon = actor:GetSummon()
            if summon then battle:AddActor(summon, team_type, 6) end
        end
    end
end
```

⇒ **站位规则硬编码**：玩家占 1..5，宝宝占 6..10（`i+5`）。
（`BattleMT:AddActor` 里有"同阵营同位判重"，所以 `i+5` 与 `i` 不会撞。）
`stub[PTO_C2S_COMBAT_PVP_START]` **是空函数**【已确认】⇒ PVP 实际入口是 `PTO_C2S_COMBAT_START{atk,def}`。

### 5.5 客户端表现层（`scripts/combat/client/combat_system.lua`）【已确认】

| 项 | 内容 |
|---|---|
| 战场背景 | `BattleBG = animation_create(ADDONWDF, 0xE3B87E0F)`，`combat_system_draw` 先画 |
| 站位坐标 | `calc_combat_self_pos(ratio_x, ratio_y)` 与 `calc_combat_enemy_pos(...)` 各返回 **10 个固定点**，按 `game_get_width()/640`、`game_get_height()/480` 缩放 |
| 摆位 | `reset_actor_pos(battle)`：己方用 `combat_self_pos[pos_i]` + `DIR_NW`；敌方用 `combat_enemy_pos[pos_i]` + `DIR_SE`；`PushAction(ACTION_BATIDLE)` |
| 点击选目标 | `combat_system_actor_ev_on_click(actor, ...)`：仅 `state == BATTLE_TURN_STAND_BY` 且 `battle:InBattle(actor)`；发 `PTO_C2S_COMBAT_CMD{master,target,skill_id,battle_id}`，`skill_id` 取自 `PROP_USING_SKILL` |
| 指令菜单 | ImGui：法术（按 `school` 列出门派技能弹窗）/ 特技（空）/ 道具（空）/ 防御（`skill_id=264`）/ 召唤（空）/ 召还（空）/ 捕捉（空）/ 逃跑（`skill_id=268`） |
| 谁在出招 | `combat_system_imgui_update` 先看自己 `PROP_TURN_READY` 否 → 再看出宝宝的 `PROP_TURN_READY`（**玩家出完指令自动轮到宝宝**）|
| HP 条 | 对 `battle.actors` 逐个 `GetAvatarRect()` + ImGui 文本 `hp/max_hp` |
| 回合推进 | `combat_system_update`：`battle_commands` 非空则逐个播；空则 `CheckEnd()` → `EndBattle()` 或 **`NextTurn()`（本地）** |
| 断线/退场 | `if not battle:FindActor(player:GetID()) then battle:EndBattle() end` |

**结论**：客户端表现层**完全由服务端数据驱动**，但**回合节拍由客户端自己决定**（见 5.2 ★）。

---

## 6. 逐文件表（战斗 / 技能 / 同步）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `scripts/combat/combat_context.lua` | `BATTLE_*`, `COMMAND_*`, `TEAM_TYPE_*`, `SKILL_SUBTYPE_*`, `ACTOR_LIFE_*`, `SKILL_STATE_*`, `PERFRAME_TIME` | 全部战斗常量集中一处 | ✅ | **"战斗常量集中到一个文件"** 是极好的习惯：JSTM 的 20000 段战斗 CMD 也应有一个 `battle_const.py` 把状态/阵营/技能子类型写全，避免散落魔法数字。注意其 `COMMAND_*` 两项**未被使用** ⇒ 借鉴时只写真正在用的 |
| `scripts/combat/combat_system.lua` | `BattleMT:new` | `{id, actors, cmds, state, turn, type}` | ✅ | **战斗对象字段极简**（5 个），状态机与数据分离得当 |
| `scripts/combat/combat_system.lua` | `BattleMT:AddActor/RemoveActor/FindActor/InBattle` | 数组存 actor + 属性回写 `PROP_TEAM_TYPE`/`PROP_COMBAT_POS_ID`/`PROP_COMBAT_BATTLE_ID` | ⚠️ | **"战斗对象与角色对象互指"**（battle.actors ↔ actor 的战斗属性）读写方便；但**双向引用无一致性保护**（`GetNotReadyActors` 就写错了变量名）⇒ JSTM 建议单向：battle 持有 participant 列表，角色只存 `battle_id` |
| `scripts/combat/combat_system.lua` | `BattleMT:Serialize/Deserialize` | 战场全量出网（NPC 带 props，玩家不带） | ✅ | **"NPC 带全量、玩家只带位次"** 的差分思想很实用（玩家数据客户端已有）⇒ JSTM 可照此裁剪 `SC_20010` 的体量 |
| `scripts/combat/combat_system.lua` | `BattleMT:NextTurn()` | `turn++`、清 ready、AutoCommand、`process_turn_buffs` | ⚠️ | **回合切换统一入口**（把 buff 结算挂在这里）是正确做法；但**客户端也调它** ⇒ 双端各自推进（见 5.2 ★）不可照搬 |
| `scripts/combat/combat_system.lua` | `BattleMT:CheckEnd()` | 一方全死 | ✅ | 胜负判定只看"是否全死"，简单可靠；**注意它返回"某一方全死"而不是"谁赢"**，胜负由调用方从 `result` 语义推出（JSTM 用 `SC_20020{result}` 显式给结果，更清晰）|
| `scripts/combat/combat_system.lua` | `BattleMT:EndBattle()` | 清状态 + 客户端恢复 BGM/清动画 + **销毁所有 NPC** | ⚠️ | **"战斗结束销毁临时 NPC"** 是必须的（否则 actor 表泄漏）；但销毁逻辑写在共享类里并用 `IsServer/IsClient` 分叉 ⇒ JSTM 应放各自类 |
| `scripts/combat/combat_system.lua` | `GetNotReadyActors()` | ⚠️ 变量名 bug（`actor` vs `_actor`）| ❌ | 不可照抄；它**根本没有调用点**（用 `CheckStandBy` 代替）|
| `scripts/combat/combat_system.lua` | `BattleMT:AutoCommand(actor)` | 50% 普攻 / 50% 法术，目标随机敌人 | ⚠️ | **"NPC 自动出招"** 的占位实现；随机而非策略 ⇒ JSTM 若做怪物 AI 需重写（JSTM 的 `_config_mon_data.luac` 有 857 KB 怪物数据，值得做得更好）|
| `scripts/combat/server/combat_system.lua` | `__battles__` + `ActorMT:GetBattle()` | 全局战斗表；actor 用 `PROP_COMBAT_BATTLE_ID` 反查 | ✅ | **与队伍同构的"对象表 + 属性反查"**，一致性负担低 |
| `scripts/combat/server/combat_system.lua` | `combat_system_create_pve_battle(player)` | 场景怪表 + 队伍人数 → 随机数量 → 动态建怪（等级=玩家等级、资质来自 `summon_quality`、10% 变异）| ⚠️ | **"暗雷战斗按玩家等级动态生成"** 是端游正确做法（JSTM 的 `SC_20010` 也是服务器给怪）；但"怪物属性 = 玩家等级直接赋值、无模板、无 AI、无掉落"过于简陋 ⇒ 借鉴生成时机，不借鉴生成规则 |
| `scripts/combat/server/combat_system.lua` | `combat_system_add_team_by_actor(battle, actor, team_type)` | 队伍成员占位 1..n，宝宝占位 `i+5`/`6` | ✅ | **"队员 + 各自宝宝同场"** 的组队战斗建模，与 JSTM 的回合制队伍战形态接近，可参考其**位次规则**（JSTM 用 `pos`/`calcTargetPos`，见 `battle_flow.md`）|
| `scripts/combat/server/combat_system.lua` | `handle_turn_commands(battle)` | 先快照 `send_pids`（防中途被移除）→ 按 `CalcSpeed()` 降序排 → 逐条 `process_turn_command` → 收集 `all_skills` → 发给每个玩家 | ✅ | **两个细节特别值得学**：① **先快照收件人**，避免结算中 actor 被移除导致漏发；② **按速度排序的回合内出手顺序**是最经典的回合制做法。这正是 JSTM 需要的（JSTM 的 `SC_20012` 也需要出手顺序）|
| `scripts/combat/server/combat_system.lua` | `stub[PTO_C2S_COMBAT_CMD]` | 校验 `battle.state == BATTLE_TURN_STAND_BY` + `master.PROP_TURN_READY`；全 ready 才执行 | ⚠️ | **状态与重复提交校验有了**（比其余 handler 严谨）；但**不校验 `req.master` 是否属于该连接**、无限速、无回合超时 ⇒ JSTM 必须补 |
| `scripts/combat/server/combat_system.lua` | `combat_system_send_message(battle, proto, msg)` | 遍历 battle.actors，只发给 `IsPlayer()` | ✅ | **战斗消息的收件人 = 战场内玩家**（这是全项目唯一的"按范围收件人"实现）⇒ JSTM 可扩成"场景内玩家" |
| `scripts/combat/server/combat_system.lua` | `combat_system_update()` | 只把**非玩家且无主人**的战斗 actor 的脏属性推给该战场玩家 | ✅ | **"战斗内怪物属性只推给参战者"** 解决了 `PTO_S2C_SYNC_PROPS` 全服广播的浪费 ⇒ 这是"按范围同步"的雏形，值得 JSTM 学 |
| `scripts/combat/server/combat_system.lua` | `stub[PTO_C2S_COMBAT_END_BATTLE]` / `combat_system_battle_on_actor_leave(pid)` | 结束战斗并通知参战玩家；掉线时**直接结束整场战斗** | ⚠️ | 掉线处理过于粗暴（一人掉线全场结束）⇒ 不可照抄（JSTM 应做"逃跑/托管"）|
| `scripts/combat/server/combat_system.lua` | `combat_system_remove_battle(battle_id)` | ⚠️ 函数体用 `battle.id`（nil 全局）| ❌ | 明显 bug，且无调用点 |
| `scripts/combat/server/combat_system.lua` | `stub[PTO_C2S_COMBAT_PVP_START]` | **空函数** | ❌ | 未实现 |
| `scripts/combat/client/combat_system.lua` | `calc_combat_self_pos/enemy_pos` | 各 10 个固定坐标 × 屏幕比例 | ❌ | 坐标是**该游戏 UI 分辨率下的硬编码**（梦幻 640×480 布局），JSTM 战斗场景布局完全不同 ⇒ 不可复用 |
| `scripts/combat/client/combat_system.lua` | `combat_system_actor_ev_on_click(actor,...)` | 点击战场角色 → 发 `PTO_C2S_COMBAT_CMD` | ✅ | **"选目标 + 提交指令"** 的交互骨架（`ACTOR_CLICK_MODE_ATTACK/SPELL`）清晰可参考；JSTM 侧目标是服务端下发还是客户端点选需按协议确认 |
| `scripts/combat/client/combat_system.lua` | `combat_system_imgui_update()` | 玩家出完 → 自动轮到宝宝；法术弹窗按 `school` 列技能；防御/逃跑写死 `skill_id` | ⚠️ | **"玩家与宝宝轮流提交指令"** 的模型对 JSTM（伙伴 hero 系统，`10401~10406` 协议）**很贴切，值得借鉴**；ImGui 实现不可用 |
| `scripts/combat/client/combat_system.lua` | `combat_system_update()` | 逐技能播 → 播完 `NextTurn()`（**本地**）| ⛔ | **不能让客户端决定回合推进**：JSTM 真机客户端连"播完了"都不发（`CS_20014` 未发，见 §5.2 订正），若再让客户端推回合，服务端将完全失去节拍控制（无超时、无法处理慢客户端/挂机）⇒ 绝不可照搬。**注意**：订正前的理由（"与 `CS_20014` ACK 节流冲突"）**作废** |
| `scripts/combat/client/combat_system.lua` | `reset_actor_pos(self)` / `on_battle_prepare/start` | 固定摆位 + 切战斗 BGM + 暂停野外遇怪 timer | ✅ | **"进战斗要暂停大地图行为、退战斗要恢复"**（`timer_manager_pause_timer('TimerWildBattle')`）是必须做且容易漏的细节，值得学 |
| `scripts/combat/client/combat_system.lua` | `combat_reset_actor(actor)` | 清 `PROP_ASM_BUFF_ANIM`/`IS_COMBAT`/前后景动画/动作，回到 `ACTION_IDLE` | ✅ | **"战斗态清理清单"** 写得完整，是脱战复位的良好范例 |
| `scripts/combat/client/skill.lua` | `calc_run_to_pos(actor,target)` | 按 4 方向算"跑到目标身边的像素偏移"（用双方帧的 KeyX/KeyY/Width/Height）| ⚠️ | **"按帧锚点算攻击落位"** 是 2D 精灵游戏的通用技巧；但公式强绑梦幻资源帧结构 ⇒ JSTM 若也用精灵帧，可借鉴**按 KeyX/KeyY 对齐**的思路 |
| `scripts/combat/client/skill.lua` | `attack_get_keyframe(actor)` / `skill_target_end_counter(skill)` | 取攻击关键帧；目标计数递减 | ✅ | 「多目标全部播完才结束技能」的计数法是**回合制多目标技能的必要机制**，JSTM 群攻技能直接用得上 |
| `scripts/combat/skill.lua` | `init_skills()` | 表 + `skill/<id>.lua` 回调（沙箱 `load`）| ✅ | **★ 最值得借鉴的技能组织方式**：静态数据在表、特化逻辑按 ID 命名成文件、启动时挂回调。JSTM 的技能表在 `config`（`_config_*`），可照此为"特殊技能"建 `skills/<id>.py` |
| `scripts/combat/skill.lua` | `battle_get_group_kill_targets(battle, group_kill, main_target)` | 主目标 + 从同阵营存活者里随机补 `group_kill-1` 个（按速度排序候选）| ✅ | **"群攻目标选择"** 的完整实现；JSTM 的群攻技能需要同一职责的函数（JSTM 侧群攻更像"按前后排/固定个数"，需按协议定）|
| `scripts/combat/skill.lua` | `base_using_skill(battle, skill)` | **服务端算 / 客户端播，同一函数用 `IsServer()` 分叉** | ✅ | **同一份代码承载"权威计算"与"表现重放"**，是理解整个战斗同步的钥匙；也是 JSTM 最该学的**结构**（但客户端分支不能有"推进回合"这类决策）|
| `scripts/combat/skill.lua` | `skill_take_effect_on_target(...)` | 按 `type`/`sub_type` 落伤害：atk→`GetAttackDamage`；spell SEAL/AUXI→无伤；HEAL→`GetSpellDamage` 正；DEFAULT→负 | ⚠️ | **"伤害按技能类型分派"** 结构清晰；但 **`GetAttackDamage(target,false,false,0,1)` 把暴击/连击写死** ⇒ 公式支持但未接线【已确认】|
| `scripts/combat/skill.lua` | `init_cskill(skill)` / `cskill_to_skill(skill)` | 出网表示 `{id,tid,turn,master(=主人id),targets,effects[{target_id,combo,hp_deltas,life_state}],success}`；客户端反序列化 | ✅ | **★ 这是"服务端下发可重放的战斗结果"的完整数据契约**，字段设计值得逐项对照 JSTM 的 `SC_20012`（技能播放）/`SC_20013`（回合开始）**字段集**看缺什么 |
| `scripts/combat/skill.lua` | `on_attack_action_callback(attack_action)` | 客户端攻击帧回调：受击动作 + 技能动画 + `SkillOnHit` + 音效 + `ShowBeatNumber(hp_deltas[...])` + 位移 | ⚠️ | **"帧回调 + 服务端伤害数字"** 是 2D 回合制表现核心；但强依赖该引擎的 `Animation`/`AddFrameCallback` ⇒ 只借"用关键帧驱动逐次伤害飘字"的思想 |
| `scripts/combat/skill.lua` | `skill_play_target_dead_fly(skill, behit_action, master, target)` | 击飞：带**上下边界反弹**的位移 + 出屏后 `combat_system_remove_from_battle` | ⚠️ | **"击飞是回合制战斗的独立生命周期"**（NPC 被击飞=移出战斗）与 JSTM 的 `SC_20012` 是否含击飞需对照；实现强绑屏幕边界常量（800×600）⇒ 不可复用 |
| `scripts/combat/skill.lua` | `skill_cast_atk/spell/flee(battle, skill)` | 客户端表现：跑去→攻击(combo)→跑回 / 施法→逐目标受击 / 逃跑移出屏幕 | ⛔ | **"跑到目标身边打一下再跑回"是梦幻式单挑演出**；JSTM 的战斗场景演出（`battle.luac` 的 `playOrder`/`playMagic`/`calcTargetPos`）是另一套 ⇒ 不可复用 |
| `scripts/combat/skill.lua` | `process_turn_command(battle, master_id, target_id, skill_id)` | 建 skill 实例、目标失效则随机换敌、封禁校验、`on_using_skill` | ✅ | **"目标失效自动换目标"**是回合制必须处理的边界（目标可能已死/已逃）；**封禁校验**（`PROP_COMBAT_SKILL_BAN_ATK/SPELL`）展示了 buff 如何影响指令合法性。两点都值得 JSTM 学 |
| `scripts/combat/skill.lua` | `check_life_state(actor)` | 死 → 玩家=`DEAD`，非玩家=`DEAD_FLY` | ✅ | 「NPC 被击飞、玩家就地倒地」的差异化处理；JSTM 若也有"怪物消散/玩家倒地"两种表现可直接沿用该判定 |
| `scripts/combat/skill.lua` | `on_using_flee_skill` | 服务端 `math.random(1,10)<=5 **or true**`（恒真）| ⛔ | 逃跑**永远成功**，明显是调试残留 ⇒ 反面教材 |
| `scripts/combat/skill.lua` | `skill_init_by_templ(skill, templ)` | 把模板字段（name/sub_type/atk_anim/group_kill/combo/type/sound）与三个回调拷进实例 | ✅ | **"模板 → 实例"的拷贝清单明确**；JSTM 的 buff/skill 实例化可照此列全字段 |
| `scripts/combat/skill/<id>.lua`（1/2/6/20/26） | `SkillOnStart/SkillOnHit/SkillOnEnd` | 逐技能特化；**只有 20、26 有实体逻辑**，其余全空 | ⚠️ | **"空壳文件占位"**说明这套回调机制**基本未被使用**（5 个文件里 3 个空）⇒ 借鉴**机制**而非"它证明这机制被验证过"。但 26 的**服务端摇随机、结果下发、客户端照结果播**是正确范式，务必学 |
| `scripts/combat/buff.lua` | `init_buffs()`, `init_buff_by_templ()`, `actor_get_buffs/add_buff/remove_buff/remove_buff_by_tid/actor_buff_next_turn`, `process_turn_buffs(battle)` | buff 存 `__actors_buffs__[actor_id][buff_id]`；`NextTurn` 时统一递减并在归零时 `BuffOnEnd` | ✅ | **★ 与技能同构的"表 + `buff/<id>.lua` 回调 + 回合统一结算"** 是干净的 DoT/控制效果实现；`turn_count_down` 递减 + 归零即 `BuffOnEnd` 保证清理对称。JSTM 的 buff（`_config_*` 里的效果）可直接套这个骨架 |
| `scripts/combat/buff.lua` | `BuffMT:new(o)` | 定义了但**无使用者** | ⚠️ | 冗余代码 |
| `scripts/combat/buff/30.lua` | `BuffOnStart`/`BuffOnEnd` | 服务端置/复位 `PROP_COMBAT_SKILL_BAN_SPELL`/`BAN_ATK`；客户端挂/停循环动画；**并覆盖 `buff.turn = 4`** | ✅ | **"控制效果 = 服务端改属性开关 + 客户端加表现"** 的范式清晰；但"时长写在脚本里覆盖表"造成**两处真源** ⇒ JSTM 应统一到表 |
| `scripts/combat/buff/1.lua`, `11.lua` | `BuffOnStart`/`BuffOnEnd` | **纯客户端动画**（服务端分支都没有）| ⚠️ | 纯表现型 buff（如"横扫千军"的姿态）在服务端**无任何逻辑**，却仍会占 buff 位并参与回合递减 ⇒ 说明 buff 表混装了"表现"与"逻辑"两类东西，JSTM 应分开 |
| `skills`/`buff` 的同步（无文件，结论）| — | buff 状态**没有独立同步协议**，靠客户端重放同一判定逻辑（`skill/26.lua` 的 `IsClient()` 分支）| ⛔ | **这是 CXEngine 战斗同步最大的设计缺陷**：随机结果虽由 `skill.success` 下发，但**buff 的存在性/剩余回合数没有任何下行消息**。**⇒ 只学它的"随机数只在服务端摇"这一半；另一半（buff 不上线）绝不要学。** ⚠️ 但**不要**由此推出"JSTM 需要新增 buff 字段"——JSTM **本来就有**载体（见下条与 §5.6）|
| `assets/tables/skill.tsv` | 11 列技能表 | 静态技能数据 | ⚠️ | **"技能表含动画 ID/音效/连击数/群攻数/子类型"** 的字段集可对照 JSTM 的技能配置核对**必备字段**；但表内容是梦幻西游技能（`DF_判官令`、`DT_横扫千军`…），**数值与技能名一律不可复用** |
| `assets/tables/buff.tsv` | 5 列 buff 表 | 静态 buff 数据 | ⚠️ | 同上；`turn` 列可为空并被脚本覆盖 ⇒ 设计缺陷 |
| `assets/doc/combat.md` | 全文（含公式、门派坐标、掉落表）| 设计文档；贴了梦幻西游经验表、师门技能花费、暗器伤害公式、怪物掉落清单 | ❌ | **内容全是《梦幻西游》数值**（`assets/doc/roadmap.md` 也一样）⇒ **只能作为"回合制战斗该有哪些子系统"的功能清单**（连击/暴击/吸血/反震/反击/击飞/封印/辅助/特技/暗器/防御/保护/捕捉/召唤/召还/逃跑），数值全部不可用 |
| `assets/doc/server.md` | 全文 | 服务端战斗流程说明 + 状态机 mermaid + 待办清单 | ✅ | **状态机 mermaid 与代码一致**，是"文档与实现对齐"的好例子；其中的**特殊情况清单**（NPC 可被击飞销毁 / 唯一玩家逃跑则战斗结束 / BB 被击飞移出 / BB 被召唤加入）非常像 JSTM 需要处理的分支，建议 JSTM 立项时对照逐条确认 |
| `assets/doc/roadmap.md` | 全文 | 含"战斗逻辑挪到服务端""战斗结算系统""回合机制完善"等**未完成项** | ✅ | **它自己列出的 TODO 就是这套架构的短板清单**：战斗逻辑当时还在客户端（`server.md` 说"服务端战斗指令处理流程"已设计，但 `roadmap.md` 仍把"战斗逻辑挪到服务端"列为需求）⇒ 提醒 JSTM：**"服务端权威"必须一开始就做对，不然回调代价极大** |

---

## 7. 战斗同步与 JSTM 1.4.9 的逐项对照（★ 决策依据）

| 维度 | CXEngine（YZXY）| JSTM 1.4.9（据本工作区既有取证）| 能否照搬 |
|---|---|---|---|
| 战斗模式 | 独立回合制战斗场景 | 独立回合制战斗场景（`battle_flow.md`） | **同类** ⇒ 大方向可参考 |
| 进战斗 | `PTO_C2S_COMBAT_PVE_START` → `PTO_S2C_COMBAT_START{battle=Serialize()}` | `CS_20002{mon_id}` → `SC_20002{code,msg}` 应答 + `SC_20010{...}` 战场数据 | 结构相似：**应答 + 独立"进战斗"消息**两段式；字段不同 |
| 回合驱动 | **客户端本地 `NextTurn()`**（服务端不知客户端播完）| **服务端自定节拍**（真机客户端**不发** `CS_20011`/`CS_20014`，见 §5.2 订正）；我们 mock 用 2.5 秒/回合自续期 | ⛔ **不可照搬** —— 但**不是**因为"所有权相反"（两者都是服务端不等的模式），而是见 §5.2 列的 5 条（字段集/每回合重推/线格式/子系统/安全内容）|
| 回合内结果 | 一次性下发整回合 `all_skills` 数组（含 `hp_deltas`/`life_state`）| 逐条推 `SC_20012`（技能播放）+ `SC_20013`（回合开始）| ⛔ 字段与批次粒度都不同；但**"下发已算好的伤害，客户端只播"** 这一原则两边一致 |
| 出手顺序 | 服务端按 `CalcSpeed()` 降序 | 未读到 JSTM 是否按速度（`SC_20013 round_start` 字段未在本次范围内确认）| ⚠️ 借鉴"服务端定序" |
| 战斗结束 | `CheckEnd()`（一方全死）+ `PTO_C2S_COMBAT_END_BATTLE` | `SC_20020{result}` + `SC_20023` 结算明细 | ⚠️ JSTM 的胜负/结算消息更完整（有独立结算包）|
| 回合超时 | **无**（文档说 30s 倒计时，代码无实现）| 未读到（JSTM 有 `time:uint16`/`left_time` 类字段，如 13007/13047）| ⚠️ CXEngine **无**超时机制 ⇒ 不可参考；JSTM 需自研 |
| 掉线处理 | **一人掉线 → 整场战斗结束** | 未读到 | ⛔ 不可照搬 |
| buff 同步 | **无协议，客户端重放判定**（buff 存 `__actors_buffs__`，不在属性表内，**无任何下行消息**）| ✅ **逐条上线**：`magic_list[] = (magic_bid:i32, change_hp:i32, **duration:u8**, per:i16, val:i16, **fold:u8**)`，挂在 `SC_20012.skill_play[].magic_play[]` 与 `SC_20013.magic_play[]` 上（`duration`=**剩余回合**、`fold`=**层数**、`change_hp`=**每回合HP变化**）；配置 `Config.SkillMagic`（**12665 行**）+ `Config.SkillMagicType`（**31 个属性 ID**）。<br>⚠️ 订正：`specials` **不是** buff 载体（穷举确认它是伙伴/宠物的**外观**配置通道，8 个 key）。| ✅ **学 CXEngine 的"服务端摇随机、结果下发"**；⛔ **别学它"buff 不上线 + 客户端重放"**。<br>**JSTM 侧不需要新增任何 buff 字段**——只需**照 `magic_list` 契约填充**（详见 `jstm_battle_fields.md`）|
| 服务端权威性 | 伤害/封印结果服务端算 ✅；但 buff 存在性靠重放 ❌ | — | ✅ 学"随机数只在服务端摇、结果下发"；❌ 别学"客户端重放" |

---

## 8. 未读到 / 待验证（战斗）

- 【未读到】`scripts/combat/skill/<id>.lua` 中除 1/2/6/20/26 之外的技能脚本 —— **只存在这 5 个文件**（【已确认】目录枚举），其余 300+ 技能**没有特化脚本**，全部走表 + 通用流程。
- 【未读到】`scripts/combat/buff/<id>.lua` 只有 1/11/30 三个（【已确认】）；其余 buff 无脚本。
- 【未读到】`common/src/actor/action.cpp`（`ActionStateMachine`，21 KB）—— `ACTION_*` 状态机的内部实现。
- 【未读到】`client/src/animation/sprite.cpp`（33 KB）—— `animation_create`/`AddFrameCallback`/`GetGroupFrameTime` 的实现。
- 【待验证】`PTO_S2C_COMBAT_EXECUTE` 的**消息体大小**：`all_skills` 含每个目标的每次连击的 `hp_deltas`，10v10 群攻时可能很大（无分片、无压缩）。
- 【待验证】服务端 `stub[PTO_C2S_COMBAT_CMD]` 用 `battle:CheckStandBy()` 判断"所有 actor 都已提交"。但**玩家掉线/逃跑的 actor 若仍留在 `actors` 且 `PROP_TURN_READY` 未置真，回合将永久卡住**（无超时兜底）—— 代码层面可确认无超时逻辑【已确认】，是否真会卡住取决于掉线时是否 `RemoveActor`（`combat_system_battle_on_actor_leave` 是 EndBattle，所以不卡，但会整场结束）。
- 【未知】`TEAM_TYPE_ATTACKER/DEFENDER` 与 `battle.local_team_type` 在观战/多人同场时的一致性。
  ⚠️ 本条原写"JSTM 侧若有多人同场观战需另设计"——**订正**：JSTM **已有观战**（`SC_20010.is_observer`、
  `CS_20016 watchBattle` / `CS_20017 csExitWatch`，见 `battle_protocol_matrix.md` §3.1），
  所以问题不是"要不要设计观战"，而是"CXEngine 的单机 `local_team_type` 语义在观战者视角下会算错阵营"。
- ✅ **已补读到（订正）**：JSTM 侧 `SC_20010` / `SC_20012` / `SC_20013` / `SC_20020` / `SC_20023` 的**权威字段**
  已在本文 §5.6 给出（`python tools/proto_spec.py cmds 20012 20013`，源 `protocol/fields.json`）。
  第一版此处写"未读到…不在本次任务范围"，属**边界收得过窄**，导致 §1.④ / §2.1 出现过界断言（已订正）。
- **JSTM 侧缺口的最终状态**（本文件第二版写的三条"尚未确认"，**全部已解出**，详见 `jstm_battle_fields.md`）：
  - ✅ `Dsc20012magic_play`(10 字段) / `Dsc20012summon_play`(16 字段) / `magic_list`(**6 字段**) 的**字段名与顺序已解出**
    （`python tools/dsc_spec.py --file 200`；`magic_list` 格式串 `iiChhC`）；
  - ✅ `specials` 的 key 语义**已解出且与 buff 无关**：只有 8 个 key（1,2,4,5,6,7,8,9），
    全部是 `Config.Partner*` 系列的**外观配置 ID**（模型/配色/阶段特效/光环/重生/羁绊标记）；
  - ✅ buff **剩余回合确实下发** = **`magic_list[].duration:uint8`**（另有 `fold` 层数、`change_hp` 每回合HP变化）。
  - **仍然【未解出】**：① `magic_list` 是**全量重列还是仅变化项**；② `specials` 是否会有增量更新路径
    （目前只在 `createBattleRole` 消费，倾向"创建时一次性给定"）；
    ③ `Config.SkillMagic.type` 的**数值→类别**（控制/增益/减益）精确映射；
    ④ `Config.SkillMagic` 行内字段与 proto#1 字段名的**逐位置对齐**（proto#0 行是 17/18 元素，字段名 19 项含一个嵌套表）。
