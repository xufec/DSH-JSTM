# CXEngine（YZXY）角色数据模型审计

> 回答任务书 Q5（角色数据如何组织）。
> 标注【已确认】/【待验证】/【未读到】；判定列 ✅ 适合借鉴 / ⚠️ 局部 / ❌ 不适合 / ⛔ 必须排除。

---

## 1. 一句话结论

【已确认】**角色 = 一个 `uint64` id + 一个按 `PROP_*` 枚举索引的"类型化变体数组"，全部属性由 `assets/tables/actor_template.tsv` 一次性定义，并由此 TSV 生成 C++ 枚举、由同一 TSV 在运行时注册默认值；行为（数值公式）全部写在 Lua metatable 里。**

三层分工非常清楚：

```
assets/tables/actor_template.tsv          ← 属性清单（name / type / def / sync）
        │
        ├─ [构建期] scripts/generator/actor_template.lua → common/src/actor/actor_enum.h
        │                                                   enum EActorProp { PROP_ID, … , PROP_COUNT }
        │
        └─ [运行期] Actor::Actor() → Lua actor_on_reg_props(actor) → actor:RegProperty(i-1,type,def)
                                                                    ↓
                                                      C++ std::vector<ActorProp> m_Props
                                                                    ↓
                                             Lua ActorMT:GetProperty(PROP_HP) / SetProperty(…)
                                                                    ↓
                                              scripts/share/actor_metatable.lua 里的全部公式
```

---

## 2. C++ 侧：存储结构

### 2.1 `common/src/actor/actor.h`

| 成员/方法 | 作用 | 标 |
|---|---|---|
| `class Actor : public BaseGameEntity`（客户端再实现 `View`）| 角色实体；`SIMPLE_SERVER` 下不含渲染成员 | 【已确认】|
| `std::vector<ActorProp> m_Props` | **属性数组**，索引 = `PROP_*` | 【已确认】|
| `std::set<int> m_DirtyProps` | **脏属性集合**（同步用）| 【已确认】|
| `ActorProp& GetProperty(int index)` | 直取引用 | 【已确认】|
| `void SetProperty(int index, ActorProp)` | 赋值 + `DirtyProperty(index)` | 【已确认】|
| `void RegProperty(int index, ActorProp&)` | `assert(index == m_Props.size())` 后 `push_back` —— **强制按序注册** | 【已确认】|
| `bool IsDirty()` / `GetDirtyProps()` / `ClearDirty()` | 暴露给 Lua（`mt_actor` 里有 `IsDirty`/`ClearDirty`/`GetDirtyProps`）| 【已确认】|
| `GetID()` | `return GetProperty(PROP_ID).toUInt64();` —— **id 本身也是属性** | 【已确认】|
| `SetPos/GetPos/SetX/SetY/TranslateX/TranslateY` | 按 `IsCombat()` **自动切换** `PROP_POS` 与 `PROP_COMBAT_POS` | 【已确认】|
| `SetTarget/GetTarget`、`GetAttackVec()`（glm normalize 目标-自身）| 战斗用 | 【已确认】|
| `template<typename T> CopyProperty(int index, T& out)` | switch(type) 把变体拷到外部变量 | 【已确认】|
| `m_PatMatrix`（`std::vector<NE::PalSchemePart>`）| 调色板矩阵（染色/变异）| 【已确认】|

**⚠️ `Actor` 构造函数会回调 Lua**（这是全项目最"魔法"的一处）：

```cpp
Actor::Actor(uint64_t pid) : BaseGameEntity(pid), m_Target(nullptr)
{
	lua_State* L = script_system_get_luastate();
	lua_getglobal(L, "actor_on_reg_props");     // ★ 依赖 Lua 侧已定义该全局函数
	lua_push_actor(L, this);
	int res = lua_pcall(L, 1, 0, 0);
	check_lua_error(L, res);
	SetProperty(PROP_ID, pid);
	...
}
```

⇒ **"构造 actor 前必须先加载 `share/actor_metatable.lua` 并初始化 `actor_template` 表"** 是一条隐式硬依赖。
【已确认】`scripts/examples/example03.lua` 的注释正是这么写的（"创建一个 actor 比较复杂，会引入 scripts/share 里面的一些 lua 文件"）。

### 2.2 `common/src/actor/actor_prop.h` / `.cpp`

```cpp
enum EActorPropType { PROP_TYPE_BOOL, PROP_TYPE_FLOAT, PROP_TYPE_INT, PROP_TYPE_STR, PROP_TYPE_UINT64, PROP_TYPE_VEC2 };

class ActorProp {
    EActorPropType type;
    union { bool b; float f; int i; CXString s; uint64_t l; float v2[2]; };
    // 6 个构造函数（int/uint64/bool/float/float[2]/const char*/CXString）
    ActorProp& operator=(const ActorProp&);
    ActorProp& operator=(bool/int/float/float[2]/uint64_t/CXString/const char*);
    bool toBool(); float toFloat(); int toInt(); const CXString& toString(); uint64_t toUInt64(); float* toVec2();
    void copyUnion(const ActorProp&);
};
```

三个 Lua 绑定函数（`mt_actor` 的 `RegProperty` / `GetProperty` / `SetProperty`）：

| C 函数 | 语义 | 关键实现 |
|---|---|---|
| `actor_reg_prop(L)` | `actor:RegProperty(idx, type, value)` | 按 `type` 把 `L,4` 转成对应类型 → `actor->RegProperty(idx, prop)` |
| `actor_get_prop(L)` | `actor:GetProperty(idx)` | `switch(prop.type)` → `lua_pushboolean/integer/number/string/newtable`（VEC2 推 `{x,y}` 表）|
| `actor_set_prop(L)` | `actor:SetProperty(idx, value)` | `switch(prop.type)` → `lua_toboolean/tointeger/tonumber/tostring`；VEC2 用 `lua_geti(L,3,i+1)` 取两个分量；最后 `actor->DirtyProperty(prop_index)` |

**代码级缺陷【已确认】**：
- `ActorProp& operator=(int v)` 里写的是 `s.~basic_string()`（应为 `s.~CXString()`）；
- `actor_reg_prop` 的 `PROP_TYPE_VEC2` 分支**漏了 `break`**（会 fallthrough 到 `default`，虽然 default 为空，暂无实害）；
- `actor_get_prop`/`actor_set_prop` 的 `default:` 分支**既不推值也不报错** ⇒ 类型不匹配时静默返回 `nil`/0 个返回值。

⇒ **结论**：`ActorProp` 用"标签 + 手写 union + 显式 placement new/析构"实现了一个 C++17 之前的手工 `std::variant`。
**JSTM 若用 Python 实现同构模型，等价物是 `dict` + 一张字段规格表（类型/默认值/是否同步），既不会踩 union 的坑，也不损失表达力。**

### 2.3 `common/src/actor/actor_manager.cpp`

| 函数 | 语义 | 标 |
|---|---|---|
| `std::map<uint64_t, Actor*> g_Players` | **全局唯一角色表**（服务端就是全部在线+NPC+召唤兽）| 【已确认】|
| `lua_actor_manager_create_actor(pid)` | `new Actor(pid)` + 入 map + 推给 Lua | 【已确认】|
| `lua_actor_manager_destroy_actor(pid)` | `delete` + erase | 【已确认】|
| `lua_actor_manager_fetch_player_by_id(pid)` | **按 id 取 actor**（Lua 侧最常用函数）| 【已确认】|
| `lua_actor_manager_fetch_all_actors()` | 全部 | 【已确认】|
| `lua_actor_manager_fetch_all_players()` | `PROP_ACTOR_TYPE == ACTOR_TYPE_PLAYER` 筛选 | 【已确认】|
| `lua_actor_manager_fetch_local_player()` / `actor_manager_set_local_player` / `actor_manager_is_local_player` | **客户端专用**（`g_LocalPid`）；服务端也有该函数但 `g_LocalPid` 恒 0 | 【已确认】|
| `actor_manager_update()` / `actor_manager_draw()` | 按 `PROP_SCENE_ID` **过滤同场景**再 update/draw；draw 按 `GetY()` 排序做深度 | 【已确认】（**唯一的"视野"裁剪**，见下）|

**重要观察**：服务端的 `actor_manager_fetch_all_players()` 遍历的是**全服** map，
而 `actor_manager_update/draw` 才按 `PROP_SCENE_ID` 过滤 —— **但服务端的 `actor_manager_update` 从未被调用**
（`scripts/server/main.lua` 的 `on_script_system_update` 里没有它）。
⇒ 【已确认】**服务端没有任何 AOI/场景分区**；`actor_manager_fetch_all_players()` 就是"全服玩家"。
唯一的"场景"概念是属性 `PROP_SCENE_ID`，它只用于客户端过滤与自己画自己。

---

## 3. 属性清单的单一真源：`assets/tables/actor_template.tsv`

### 3.1 文件格式

```
name	type	def	sync
*			
*			0
prop_id	uint64	0	
prop_dir	int	4	
prop_race	int	1	1
prop_school	int	1	1
prop_school_skill_lv_targethit	int	0	1
...
prop_hp	float	0	1
...
prop_is_auto_command	bool	false	1
prop_setting_bgm	bool	false	
prop_setting_wild_battle	bool	false	
```

- 第 1 行 = 列名（`name`,`type`,`def`,`sync`）
- 以 `*` 开头的行 = 默认值行 / 占位（解析器里 `line:match('^%*')` 跳过，`utils_save_rows_to_tsv` 用来写 def_row）
- `type` ∈ `{uint64, int, float, str, bool, vec2}`
- `def` = 默认值（`vec2` 形如 `{0,0}`；`str` 直接写；`bool` 为 `true/false`）
- **`sync` = 是否参与属性同步**（`1` 同步 / 空或 `0` 不同步）

### 3.2 生成 C++ 枚举：`scripts/generator/actor_template.lua`

【已确认】文件末尾直接 `solve()`，流程：

```lua
function solve()
    local tbl = utils_parse_tsv('actor_template', {
        { name='name'}, { name='type'}, { name='def'}, { name='sync', fmt='i', def=0},
    })
    for i,row in ipairs(tbl) do
        table.insert(actor_enums, row.name:upper())   -- 'prop_id' → 'PROP_ID'
        actor_enum_types[row.type] = true
    end
    pcall(gen_actor_enum)
    cxlog_info('ActorProp生成完成！')
end
```

`gen_actor_enum()` 写出 **`common/src/actor/actor_enum.h`**：

```cpp
#pragma once
#include <lua.h>
enum EActorProp
{
	PROP_ID,
	PROP_DIR,
	...
	PROP_SETTING_WILD_BATTLE,
	PROP_COUNT            // 末尾自动追加
};
enum EActorPropType
{
	PROP_TYPE_BOOL,
	PROP_TYPE_FLOAT,
	PROP_TYPE_INT,
	PROP_TYPE_STR,
	PROP_TYPE_UINT64,
	PROP_TYPE_VEC2
};
void luaopen_actor_enum(lua_State* L);
```

以及 **`common/src/actor/actor_enum.cpp`**：

```cpp
void luaopen_actor_enum(lua_State* L) {
#define REG_ENUM(e) (lua_pushinteger(L, e), lua_setglobal(L, #e))
	REG_ENUM(PROP_ID);
	...
	REG_ENUM(PROP_COUNT);
	REG_ENUM(PROP_TYPE_BOOL);
	...
#undef REG_ENUM
};
```

⇒ **TSV 的行序 == 枚举值 == `m_Props` 下标 == Lua 全局常量数值 == `GetProperties()` 的键。**
三者被 `RegProperty` 的 `assert` 强行绑定，是一套**自洽且可验证**的设计。

**⚠️ 但入库的 `actor_enum.h` 与生成逻辑存在不一致**：入库版本里 `PROP_ID` 系列之后还有一批
（`PROP_PAL_MATRIX`、`PROP_IS_AUTO_COMMAND`、`PROP_SETTING_BGM`、`PROP_SETTING_WILD_BATTLE`），
说明**该文件是生成产物被手工改过、或 TSV 与 h 曾长期不同步** ⇒ 【待验证】最后一次生成与当前入库状态是否一致。
JSTM 若要照搬此机制，必须把"生成 + 提交 + CI 校验一致"补齐，否则必然漂移。

### 3.3 全量 `PROP_*` 清单（来自 `common/src/actor/actor_enum.h`，按枚举顺序）

> 共 **118** 个具名属性 + `PROP_COUNT`。【已确认】顺序即数值（从 0 开始）。
> 同步标记来自 `actor_template.tsv` 第 4 列（仅对能逐行对齐的部分标注；未对齐的标 `—`）。

| 分组 | 属性 |
|---|---|
| **身份/基础** | `PROP_ID`(—) `PROP_DIR`(—) `PROP_RACE`(✅1) `PROP_SCHOOL`(✅1) |
| **门派技能等级**（决定各属性成长） | `PROP_SCHOOL_SKILL_LV_TARGETHIT`(1) `_DAMAGE`(1) `_DEFEND`(1) `_SPEED`(1) `_DODGE`(1) `_SPIRITUAL`(1) `_HP`(1) `_MP`(1) |
| **装备加成** | `PROP_EQUIP_HP`(1) `_MP`(1) `_TARGET`(1) `_DAMAGE`(1) `_DEFEND`(1) `_SPIRITUAL`(1) `_AGILE`(1) |
| **辅助技能等级** | `PROP_AUXI_SKILL_LV_HP`(1) `_MP`(1) |
| **调试/表现开关** | `PROP_SHOW_BOUNDINGBOX` `PROP_SHOW_AVATAR_INFO` `PROP_IS_AUTORUN` |
| **状态** | `PROP_IS_DEAD` `PROP_FRAME_SPEED` `PROP_ACTOR_TYPE`(1) |
| **外观/形象** | `PROP_NAME`(1) `PROP_AVATAR_ID`(1) `PROP_WEAPON_AVATAR_ID`(1) `PROP_SCENE_ID`(1) `PROP_ROLE_ID` `PROP_WEAPON_ID` `PROP_WEAPON_TYPE` |
| **位置/动作（大地图）** | `PROP_ACTION_ID` `PROP_POS` `PROP_MOVE_TO_POS` `PROP_DIR_COUNT` `PROP_IS_MOVE` `PROP_MOVE_VELOCITY` `PROP_CAN_MOVE` `PROP_IS_CALC_MOVE_LIST` `PROP_SAY_DURATION` `PROP_IS_LOCAL` |
| **战斗位（另一套坐标）** | `PROP_IS_COMBAT` `PROP_TARGET_ID` `PROP_CAST_ID` `PROP_COMBAT_POS` `PROP_COMBAT_DIR` `PROP_COMBAT_BACKUP_POS` `PROP_COMBAT_TARGET_POS` `PROP_COMBAT_ACTING` `PROP_COMBAT_BATTLE_ID` `PROP_COMBAT_POS_ID` |
| **队伍/指令** | `PROP_TEAM_TYPE`(1) `PROP_TEAM_ID`(1) `PROP_USING_SKILL` `PROP_CAST_SKILL_TID` `PROP_TURN_READY`(1) |
| **客户端动作状态机（ASM）** | `PROP_ASM_ATK_COMBO` `PROP_ASM_BEHIT_ANIM` `PROP_ASM_DAMAGE` `PROP_ASM_HEAL` `PROP_ASM_BUFF_ANIM` `PROP_ASM_PLAY_BEHIT` `PROP_ASM_RUNTO_X` `PROP_ASM_RUNTO_Y` |
| **资源条** | `PROP_HP`(1) `PROP_MP`(1) `PROP_SP` `PROP_LV`(1) `PROP_EXP` |
| **属性加点** | `PROP_ADD_PROP_PLAN` `PROP_ASSIGN_FORCE` `PROP_ASSIGN_HEALTH` `PROP_ASSIGN_STAMINA` `PROP_ASSIGN_AGILITY` `PROP_ASSIGN_MAGIC` |
| **五维基础** | `PROP_BASE_FORCE` `PROP_BASE_HEALTH` `PROP_BASE_STAMINA` `PROP_BASE_AGILITY` `PROP_BASE_MAGIC` |
| **召唤兽（宝宝）** | `PROP_SUMMON_TAKE_LEVEL` `PROP_SUMMON_BATTLE_LEVEL` `PROP_SUMMON_ATK_QUAL` `PROP_SUMMON_DEF_QUAL` `PROP_SUMMON_HEALTH_QUAL` `PROP_SUMMON_MAGIC_QUAL` `PROP_SUMMON_SPEED_QUAL` `PROP_SUMMON_DODGE_QUAL` `PROP_SUMMON_GROW_COEF` `PROP_SUMMON_UIDS` `PROP_SUMMON_HAS_OWNER` `PROP_SUMMON_OWNER` |
| **技能使用态** | `PROP_IS_USING_SKILL` `PROP_COMBAT_SKILL_BAN_ATK` `PROP_COMBAT_SKILL_BAN_SPELL` |
| **额外加成占位** | `PROP_DAMAGE_EXTRA` `PROP_DEFEND_EXTRA` `PROP_SPEED_EXTRA` `PROP_SPIRITUAL_EXTRA` `PROP_TARGETHIT_EXTRA` `PROP_DODGE_EXTRA`（**全部未被任何公式使用**【已确认】，是预留位）|
| **修炼** | `PROP_ATK_PRACTICE_SKILL_LV` `PROP_ATK_RESISTANCE_SKILL_LV` `PROP_SPELL_PRACTICE_SKILL_LV` `PROP_SPELL_RESISTANCE_SKILL_LV` |
| **调色板/变异** | `PROP_PAL_MATRIX`（存 `cjson` 字符串）|
| **AI/设置** | `PROP_IS_AUTO_COMMAND`(1) `PROP_SETTING_BGM` `PROP_SETTING_WILD_BATTLE` |
| **哨兵** | `PROP_COUNT`（= 118）|

### 3.4 运行时注册：`scripts/share/actor_metatable.lua:actor_on_reg_props()`

```lua
local actor_enum_typename_to_type = {
    bool=PROP_TYPE_BOOL, int=PROP_TYPE_INT, uint64=PROP_TYPE_UINT64,
    float=PROP_TYPE_FLOAT, str=PROP_TYPE_STR, vec2=PROP_TYPE_VEC2
}
local prop_names = {}
function actor_on_reg_props(actor)
    local tbl = content_system_get_table('actor_template')
    for i,row in ipairs(tbl) do
        local reg_type = actor_enum_typename_to_type[row.type]
        local v
        if     row.type == 'bool'   then v = row.def == 'true'
        elseif row.type == 'int' or row.type == 'uint64' then v = math.tointeger(row.def)
        elseif row.type == 'float'  then v = tonumber(row.def)
        elseif row.type == 'str'    then v = row.def
        elseif row.type == 'vec2'   then
            local strx,stry = string.match(row.def,'{(.-),(.-)}')
            v = {tonumber(strx), tonumber(stry)}
        end
        actor:RegProperty(i-1, reg_type, v)      -- ★ i-1：TSV 第 1 行数据 → 属性 0
        prop_names[i-1] = row.name
    end
end
```

⇒ **同一张 TSV 被"读两次"**：一次在构建期（生成枚举），一次在运行期（注册默认值）。
好处是数值与顺序天然一致；代价是**每次 `new Actor` 都全表遍历 118 行**（服务端创建 NPC 时批量发生）。

---

## 4. Lua 侧：角色行为全部在 `scripts/share/actor_metatable.lua`（36 KB）

`local ActorMT = actor_get_metatable()` —— 从 C++ 取到 `mt_actor` 的元表并挂方法，**客户端/服务端共享**。

### 4.1 位置与属性系统

| 函数 | 机制 | 标 |
|---|---|---|
| `ActorMT:GetPos()/SetPos(x,y)/SetCombatPos(x,y)` | 按 `PROP_IS_COMBAT` **自动选** `PROP_COMBAT_POS` 或 `PROP_POS` | 【已确认】|
| `ActorMT:GetX()/GetY()` | 解包 vec2 | 【已确认】|
| `ActorMT:GetProperties()` | **`for prop_id=0,PROP_COUNT-1` → 0 基表**（协议格式的来源）| 【已确认】|
| `ActorMT:SetProperties(props)` | `for k,v in pairs(props) do SetProperty(k,v) end`；客户端额外解 `PROP_PAL_MATRIX` JSON 并 `ChangePalMatrix` | 【已确认】|
| `ActorMT:FaceTo(target)` | 算角度 → `GetDirByDegree` → `math_dir_8_to_4`；**同时给 target 也设朝向再反向** | 【已确认】|
| `ActorMT:StopMove()` | `MoveTo(当前位置)` | 【已确认】|
| `ActorMT:ApplySummonQual(name)` | 从 `summon_quality` 表按名刷 6 项资质 + 成长系数 | 【已确认】|
| `ActorMT:IsPlayer()/IsNPC()/IsSummon()` | 判 `PROP_ACTOR_TYPE` | 【已确认】|
| `ActorMT:GetSummonOwner()/SetSummonOwner()/RemoveSummonOwner()` | 召唤兽→主人 | 【已确认】|
| `ActorMT:GetSceneName()/GetSchoolName()/GetRaceName()/GetSceneBGMName()` | 查表翻译 | 【已确认】|
| `ActorMT:Variation()` | 读 `summon_variation` 表的 `wpal` 路径 → `decode_mypal` 解析调色板 → 取每段最后一个 3×3 矩阵生成 `from/to/mat` → 存 `PROP_PAL_MATRIX`（JSON）| 【已确认】|
| `ActorMT:GetRandomSkillID(type)` | NPC/召唤兽按 `school==0 and type==type` 随机；玩家按 `school==自己门派` 随机；兜底返回 1 | 【已确认】|

### 4.2 数值公式（全部硬编码在 Lua，服务端与客户端共用）

**种族系数表**：

```lua
COEF = {
  [RACE_HUMAN]  = {health=5,   magic=3,   target=2,   damage=0.7, defend=1.5},
  [RACE_DEVIL]  = {health=6,   magic=2.5, target=2.3, damage=0.8, defend=1.3},
  [RACE_SPIRIT] = {health=4.5, magic=3.5, target=1.7, damage=0.6, defend=1.6},
}
```

| 公式函数 | 内容（原始注释即中文） | 标 |
|---|---|---|
| `formula_calc_hp` | 气血 = 体质×COEF.health + 100 | 【已确认】|
| `formula_calc_mp` | 魔法 = 魔力×COEF.magic + 80 | 【已确认】|
| `formula_calc_targethit` | 命中 = 力量×COEF.target + (魔 27 / 其它 30) | 【已确认】|
| `formula_calc_atk` | 伤害 = 力量×COEF.damage + (魔 34 / 其它 40) | 【已确认】|
| `formula_calc_defend` | 防御 = 耐力×COEF.defend | 【已确认】|
| `formula_calc_speed` | 速度 = 体质×0.1 + 力量×0.1 + 耐力×0.1 + 敏捷×0.7 | 【已确认】|
| `formula_calc_dodge` | 躲避 = 敏捷×1 + 10（魔 +8）| 【已确认】|
| `formula_calc_spiritual` | 灵力 = 体质×0.3 + 魔力×0.7 + 力量×0.4 + 耐力×0.2 | 【已确认】|
| `formula_calc_summon_hp` | 气血 = 体质×成长×6 + 体力资质×等级÷1000 | 【已确认】|
| `formula_calc_summon_mp` | 魔法 = 魔力×成长×3 + 法力资质×等级÷500 | 【已确认】|
| `formula_calc_summon_atk` | 攻击 = 力量×成长 + 攻击资质×等级×7/2000 | 【已确认】|
| `formula_calc_summon_defend` | 防御 = 耐力×成长×4/3 + 防御资质×等级/433 | 【已确认】|
| `formula_calc_summon_speed` | 速度 = 敏捷×速度资质÷1000 | 【已确认】|
| `formula_calc_summon_spiritual` | 灵力 = 等级×(法力资质+1640)×(成长+1)/7500 + 魔力×0.7 + 力量×0.4 + 体质×0.3 + 耐力×0.2 | 【已确认】|
| `formula_calc_summon_dodge` / `_growth_1` / `_growth_2` | **空实现（`return 0` / 无体）** | 【已确认】|

**门派技能加成**（按门派分支的**逐级累加**，实现方式极"考古"）：

| 函数 | 内容 | 标 |
|---|---|---|
| `ActorMT:CalcSchoolSkillTargethit()` | 遍历 `1..skill_lv`，按门派累加（大唐 `0.97+i*0.0203`、凌波 `1+i*0.0099`、盘丝 `+3/级`）| 【已确认】|
| `ActorMT:CalcSchoolSkillDamage()` | **15 个门派各一段 `if`**，含 `damage=(69-46)` 这类"首级系数"；地府分白天/夜晚两套（夜晚注释掉白天）| 【已确认】|
| `ActorMT:CalcSchoolSkillDefend()` | 统一 `1 + 0.0138*i` | 【已确认】|
| `ActorMT:CalcSchoolSkillSpeed()` | **仅女儿村**（`school==SCHOOL_NE`）非 0，公式 `skill_lv/0.7+sqrt(skill_lv)-skill_lv/4.2+skill_lv^2/5000` | 【已确认】|
| `ActorMT:CalcSchoolSkillDodge()` | 女儿村返回 0，其它门派 `2.1775+0.01839*i` 累加 | 【已确认】|
| `ActorMT:CalcSchoolSkillSpiritual()` | 盘丝 `0.46639+0.0141*i`，其它 `0.46639+0.0092*i` | 【已确认】|
| `ActorMT:CalcSchoolSkillHP(base)` / `CalcSchoolSkillMP(base)` | 天宫 HP 每级 ×1.003、五庄 MP 每级 ×1.005，返回**增量** | 【已确认】|

**总属性聚合**：

```
GetMaxHP()  = [玩家] formula_calc_hp + PROP_EQUIP_HP + CalcSchoolSkillHP(上式之和)
              [召唤兽/NPC] formula_calc_summon_hp
GetMaxMP()  = 同构（MP / formula_calc_summon_mp）
CalcAttack()= [玩家] formula_calc_atk + CalcSchoolSkillDamage + PROP_EQUIP_DAMAGE
                     + (PROP_EQUIP_TARGET + CalcSchoolSkillTargethit)/3
CalcDefend()= [玩家] formula_calc_defend + PROP_EQUIP_DEFEND + CalcSchoolSkillDefend
CalcSpeed() = [玩家] formula_calc_speed + PROP_EQUIP_AGILE*0.7 + CalcSchoolSkillSpeed
CalcSpiritual() = [玩家] formula_calc_spiritual + PROP_EQUIP_SPIRITUAL + CalcSchoolSkillSpiritual
CalcDodge() = [玩家] formula_calc_dodge + PROP_EQUIP_AGILE + CalcSchoolSkillDodge
CalcTargetHit() = [玩家] formula_calc_targethit + PROP_EQUIP_TARGET + CalcSchoolSkillTargethit
              [召唤兽/NPC 的攻击/防御/速度/灵力走 formula_calc_summon_*，命中/躲避返回 0]
```

**HP/MP 修改**：

```lua
function ActorMT:ModifyHP(delta)
    local hp = self:GetProperty(PROP_HP) + delta
    if hp <= 0 then hp = 0 end
    local max_hp = self:GetMaxHP()
    if hp >= max_hp then hp = max_hp end
    self:SetProperty(PROP_HP, hp)
    self:SetProperty(PROP_IS_DEAD, hp <= 0)     -- ★ 死亡由 HP 派生
end
function ActorMT:ModifyMP(delta) ... if mp >= self:GetMaxHP() ... -- ★ BUG：用 GetMaxHP 夹取 MP
```

**加点与方案**：

```lua
init_prop = {
  [RACE_HUMAN]  = {10,10,10,10,10},
  [RACE_SPIRIT] = {12, 5,11,12,10},
  [RACE_DEVIL]  = {12,11,11, 8, 8},
}
GetInitXxxProp() = init_prop[race][i] + lv                 -- 玩家
                  20 + lv                                   -- 召唤兽/NPC
GetXxxProp()     = GetInitXxxProp() + PROP_ASSIGN_XXX
GetRemainPropPoints() = (lv+1)*5 - Σ PROP_ASSIGN_*
SetPropsByPlan(plan) / UpdatePropPtsByPlan()   -- 按比例分配 (lv+1)*5 点
```

**战斗伤害公式**（也在 `actor_metatable.lua`）：

```lua
ACTOR_TYPE_COEF_PVP=1  ACTOR_TYPE_COEF_PVE=0.9  ACTOR_TYPE_COEF_EVP=0.8  ACTOR_TYPE_COEF_EVE=1

formula_calc_atk_base_damage(attacker,defender,atk,def,is_critical,is_combo,combo_coef,actor_type_coef)
    base = atk - def
    -- 修炼：1.02^(攻修-抗修)*(base+250)-250  /  0.98^(抗修-攻修)*(base+250)-250   ← 注释里写明是"修炼公式"
    if is_combo then base = combo_coef*atk - def end     -- 第一次 0.75 / 第二次 0.5
    if is_critical then base = base*2 end
    return base * actor_type_coef

formula_calc_atk_float_damage(atk, damage)               -- 三档浮动：0.1~0.9 用 90%~110%；<0.1 用 10%~20%；>0.9 用 85%~95%
formula_calc_atk_night_damage(damage, is_night)          -- 夜晚 ×0.8
ActorMT:GetAttackDamage(target,is_critical,is_combo,combo_coef,actor_type_coef) = base → float

ActorMT:GetSpellDamage(target) = max(1, lv*3 + formula_calc_spell_base_damage*1.2 + 20)
formula_calc_spell_base_damage = 灵力差，同样套 1.02^n/0.98^n 修炼修正
formula_calc_seal_success_rate(skill_lv,target_lv,practice_lv,resistance_lv)
    -- 技能等级≤对方：0.9^(对方-技能)*0.6
    -- 技能等级> 对方：0.98-0.38*0.975^(技能-对方)
    -- 再乘修炼：1.02^(练-抗) 或 0.98^(抗-练)
```

**装备标准套**：`ActorMT:SetGlobalStandardEquip(lv, is_enforce)`
按 `lv//10` 取 `equip.tsv` 里 `weapon/armor/helmet/belt/necklace/shoes`（可带 `_enforced` 后缀）
的 `base_* + x*lv_accum_*`，汇总写入 `PROP_EQUIP_{HP,MP,TARGET,DAMAGE,DEFEND,SPIRITUAL,AGILE}`。

### 4.3 公式来源（值得注意）

`actor_metatable.lua` 里直接贴了**参考链接与出处**：

```lua
-- [梦幻西游法伤的计算公式？（包括修炼的计算公式。）]https://zhidao.baidu.com/question/568287506.html
-- https://zhidao.baidu.com/question/568287506.html
-- [在《梦幻西游》里都有哪些经典的数值公式？]https://www.gameres.com/849887.html
-- 法宠(单法)=等级×3+灵力差×1.2+20
-- 法宠(群法)=(等级×3+灵力差×1.2+10)×（10-作用人数）/10
```

⇒ **这些公式是《梦幻西游》的公开数值公式，不是 CXEngine 的独创**。
对 JSTM 而言：**公式本身属于第三方游戏（梦幻西游）的知识，且 JSTM 是《绝世唐门》，门派/属性体系完全不同**
⇒ 公式**只能作为"如何组织一套属性公式"的样例**，数值一律不可复用（详见 `reuse_candidates.md`）。

---

## 5. 持久化与账号

### 5.1 账号（`scripts/server/server.lua`）

```lua
local account_database = {}
function read_account_database()
    local path = vfs_get_workdir() .. '/assets/storage/account.data'
    local db = read_database_file(path)            -- cjson.decode 整个文件
    if db then for i,v in ipairs(db) do account_database[v.account] = v end end
end

stub[PTO_C2C_SAVE_ACCOUNT_DATABASE] = function()
    -- 排序后整体 cjson.encode 写回
end
```

`account.data` 每条 = `{pid, account, password, ...}`（**明文密码**【已确认】）。

### 5.2 角色（`scripts/server/actor_system.lua`）

```lua
function actors_on_load()
    local db = read_database_file(vfs_get_workdir()..'/assets/storage/actor.data')
    for i,v in ipairs(db) do
        local pid = v[tostring(PROP_ID)]                  -- ★ 键是字符串 "0"
        local actor = actor_manager_create_actor(pid)
        actor:SetProperties(v)
        actor:SetProperty(PROP_ID, pid)
    end
end

function actors_on_save()
    local actor_infos = {}
    for pid, actor in pairs(actor_manager_fetch_all_actors()) do
        table.insert(actor_infos, actor:GetProperties())  -- 0 基属性字典
    end
    table.sort(actor_infos, function(a,b) return a[PROP_ID] < b[PROP_ID] end)
    -- 整体 cjson.encode 写 actor.data
end
stub[PTO_C2C_SAVE_ACTORS] = function() actors_on_save() end
```

### 5.3 存档问题清单（全部【已确认】）

| # | 问题 | 具体 | 判定 |
|---|---|---|---|
| 1 | **明文密码** | `account_info.password = msg.password` 直接入 JSON | ⛔ |
| 2 | **客户端可触发全量存档** | `PTO_C2C_SAVE_ACTORS` / `PTO_C2C_SAVE_ACCOUNT_DATABASE` 无鉴权 | ⛔ |
| 3 | **非原子写** | 直接 `io.open(path,'w')` + `write`，无 tmp+rename | ❌ |
| 4 | **存档内容 = 全量属性数组** | 含 `PROP_IS_COMBAT`、`PROP_COMBAT_BATTLE_ID`、`PROP_TURN_READY` 等**瞬时战斗态** | ❌ 读档后可能带着战斗标记 |
| 5 | **存档含全服 NPC** | `actors_on_save` 遍历 `fetch_all_actors()`（含服务端用 `npc.tsv` 生成的 NPC）| ❌ 会把 NPC 当玩家存档 |
| 6 | **0 基索引 JSON** | 键 `"0".."118"`，依赖 Lua 5.3 字符串→数字强转才可读回 | ⚠️ |
| 7 | **UID 不持久化** | `utils_next_uid('actor')` = `os.time()%0xFFFFFFFF` 起、内存自增 | ❌ 重启后可能重号 |
| 8 | 保存时机 | 只有客户端点按钮；`GameServer::OnClose()` 想调 `save_player_database` 但**该函数不存在** | ❌ |

---

## 6. 队伍与召唤兽（角色模型的扩展部分）

### 6.1 召唤兽：`scripts/server/actor_system.lua` + `client/module/summon.lua`

```lua
-- 服务端：创建召唤兽
stub[PTO_C2S_CREATE_SUMMON] = function(req)
    local pid = utils_next_uid('actor')
    local actor = actor_manager_create_actor(pid)
    actor:SetProperties(req.props)
    actor:SetProperty(PROP_ID, pid)
    actor:SetProperty(PROP_TEAM_ID, 0)
    actor:SetProperty(PROP_ACTOR_TYPE, ACTOR_TYPE_SUMMON)
    actor:SetProperty(PROP_IS_AUTO_COMMAND, false)
    local owner = actor_manager_fetch_player_by_id(req.owner)
    if owner then owner:AddSummon(actor) end
    __summons__[pid] = actor
    -- 回 PTO_S2C_FETCH_SUMMON_RESP：全部召唤兽属性
end

function ActorMT:AddSummon(summon)
    local uids_str = self:GetProperty(PROP_SUMMON_UIDS)
    uids_str = '[]'                                  -- ★ 无条件覆盖！永远从空开始
    local uids = cjson.decode(uids_str)
    table.insert(uids, summon:GetID())
    summon:SetProperty(PROP_SUMMON_HAS_OWNER, true)
    summon:SetProperty(PROP_SUMMON_OWNER, self:GetID())
    self:SetProperty(PROP_SUMMON_UIDS, cjson.encode(uids))
end
function ActorMT:GetSummon()  -- 取 uids[1]
function ActorMT:GetSummons() -- 全部实例化
```

**【已确认】严重缺陷**：`AddSummon` 里 `uids_str = '[]'` **无条件覆盖**了读出来的属性值
⇒ 玩家**永远只能有 1 只召唤兽**（每次添加都把列表重置为只含新兽）。
同时 `GetSummon()/GetSummons()` 读 `PROP_SUMMON_UIDS` 若为 nil 会 `cjson.decode(nil)` 报错。
⇒ **反面教材**：用 JSON 字符串表达"引用列表"本身可接受，但必须保留读改写、且要处理空值。

### 6.2 队伍：`scripts/server/team_system.lua`（+ 客户端 `client/module/team.lua`）

```lua
TeamMT = {}
function TeamMT:new(o)
    o = o or { id = utils_next_uid('team'), members = {}, leader }
    self.__index = self; setmetatable(o, self); return o
end
function TeamMT:AddMember(actor)   -- 去重 + table.insert(members) + actor:SetProperty(PROP_TEAM_ID, self.id)
function TeamMT:RemoveMember(actor) -- table.remove + PROP_TEAM_ID = 0
function TeamMT:HasMember(actor) / SetLeader(actor) / GetMembers() / GetLeader()
function TeamMT:Serialize()         -- → {id, members, leader}
end

__teams__ = __teams__ or {}
function team_system_create_team(actor)  -- 建队 + 自己是队长
function team_system_get_team(actor)     -- 用 actor 的 PROP_TEAM_ID 反查 __teams__
function team_system_dismiss_team(actor) / team_system_leave_team(actor)
function team_system_on_disconnect(player)  -- 断线自动退队并广播
```

**设计要点**（判定 ✅）：**"对象表 + 属性反向索引"**：
队伍实体存 `__teams__[team_id]`，成员是否在队只由角色自己的 `PROP_TEAM_ID` 决定，
取队时用 `actor:GetProperty(PROP_TEAM_ID)` 反查。
⇒ 干净、无双向一致性负担；但【已确认】**队伍没有持久化**（`__teams__` 是纯内存全局表），重启即散。

### 6.3 `PROP_TEAM_TYPE` 与 `PROP_TEAM_ID` 是两回事（易混）

| 属性 | 含义 | 用途 |
|---|---|---|
| `PROP_TEAM_ID` | **队伍** id（社交组队）| `team_system` |
| `PROP_TEAM_TYPE` | **战斗阵营**（`TEAM_TYPE_ATTACKER=1` / `TEAM_TYPE_DEFENDER=2`）| 战斗（见 `battle.md`）|

---

## 7. 逐文件表（角色数据模型）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `assets/tables/actor_template.tsv` | 118 行属性定义（name/type/def/sync） | **属性的单一真源** | ✅ | **"一张表定义角色全部字段（名/类型/默认值/是否同步）"** 正是 JSTM 最该学的：JSTM 的 `_config_role_attr.luac`/`role_attr.json` 已有类似内容，但缺"是否同步"这一列 ⇒ **建议加 `sync` 列**，直接决定哪些字段走增量推送 |
| `common/src/actor/actor_enum.h` | `enum EActorProp`（118 项 + `PROP_COUNT`） | 由 TSV 生成的属性枚举；同时是 `m_Props` 下标 | ⚠️ | **"枚举下标 = 数组下标 = 协议属性号"三合一**在 C++ 里高效；但 JSTM 用命名字段协议，**不应把属性退化成裸数字**（`[pid,45,987.0]` 不可读、不可版本兼容）|
| `common/src/actor/actor_enum.cpp` | `luaopen_actor_enum()` + `REG_ENUM` | 生成器产物：把枚举灌成 Lua 全局 | ⚠️ | 宏简洁；但全局常量命名污染 |
| `common/src/actor/actor.h` | `class Actor` | id + `vector<ActorProp>` + 脏集合 + 位置/战斗/目标/调色板 | ✅ | **"实体 = 一张稀疏类型化属性表 + 脏标记"** 是端游式通用模型，JSTM 用 `dict` + `dirty set` 同样成立；`SetPos` 按 `IsCombat()` 自动切换地图/战斗两套坐标的**技巧值得学**（回合制战斗需要"记录并还原大地图坐标"）|
| `common/src/actor/actor.h` | `Actor::Actor(uint64_t pid)` | 构造时回调 Lua `actor_on_reg_props` 初始化属性 | ⚠️ | **"让 Lua 决定 C++ 实体的字段"** 让内容可热改；但构造期回调 ⇒ 隐式加载顺序依赖 + `new` 变慢（每只 NPC 都全表遍历）|
| `common/src/actor/actor.h` | `RegProperty/DirtyProperty/IsDirty/GetDirtyProps/ClearDirty` | 属性注册 + 脏标记 | ✅ | **脏标记是同步的最小挂点**，比全量对比便宜；JSTM 应照此思路给角色字段加 dirty |
| `common/src/actor/actor_prop.h/.cpp` | `class ActorProp`, `actor_set_prop/get_prop/reg_prop` | 标签 + 手写 union 变体 + Lua 绑定 | ⚠️ | **"一个通用槽承载 6 种类型"** 思想可用；实现有 bug（析构写错、`default` 静默、缺 break）⇒ **JSTM 用 Python `dict`/`Union` 直接绕开这类问题** |
| `common/src/actor/actor_manager.cpp` | `g_Players`, `create/destroy/fetch_by_id/fetch_all_players/fetch_all_actors`, `actor_manager_update/draw`, `set/fetch_local_player` | 全局 id→Actor 表；客户端用 `g_LocalPid` 区分自己 | ✅ | **全局 id 注册表 + `fetch_by_id`** 是消息处理的前提；JSTM 的 mock 也需要"id→角色对象"的权威表。**注意 CXEngine 服务端无场景分区**，JSTM 需要自己加 |
| `common/src/actor/actor_manager.cpp` | `actor_manager_fetch_all_players()` | 遍历全服按 type 过滤 | ⚠️ | 语义是"全服玩家"，随人数线性；JSTM 需要"按场景/按队伍"版本 |
| `scripts/share/actor_metatable.lua` | `actor_on_reg_props(actor)` | 读 TSV 逐项 `RegProperty(i-1, type, def)` | ✅ | **"Lua 侧注册 C++ 实体字段"** 是做**内容热更**的关键一步：改 TSV 即可加字段（无需重编 C++，只要枚举已生成）。JSTM 若坚持 schema 稳定，可只借鉴"运行期兜底默认值"|
| `scripts/share/actor_metatable.lua` | `ActorMT:GetProperties()/SetProperties()` | 0 基字典 ↔ 属性数组 | ⚠️ | **全量序列化只有一个函数**很清爽；但 0 基 + 字符串键 + 无 schema 三者叠加导致协议脆弱（见 `protocol.md` 4.2）|
| `scripts/share/actor_metatable.lua` | `formula_calc_*`（14 个）、`CalcSchoolSkill*`（8 个）、`GetMaxHP/MP`、`CalcAttack/Defend/Speed/Spiritual/Dodge/TargetHit`、`GetAttackDamage`、`GetSpellDamage`、`formula_calc_seal_success_rate` | **全部数值公式集中在同一文件**（约 700 行） | ⚠️ | **"公式集中、可读、带出处注释"** 的工程习惯值得学（JSTM 的数值校对正需要这种集中）；但**公式内容是《梦幻西游》的**（文件里就贴了百度知道/GameRes 链接），与 JSTM《绝世唐门》职业/属性体系无关 ⇒ **结构可借、数值不可借** |
| `scripts/share/actor_metatable.lua` | `ActorMT:GetInitXxxProp/GetXxxProp/GetRemainPropPoints/SetPropsByPlan/UpdatePropPtsByPlan/SetGlobalStandardEquip` | 加点与标准装备生成 | ⚠️ | 「(lv+1)*5 点自由分配 + 按计划比例」是很清晰的加点模型；JSTM 若有点数系统可参考结构 |
| `scripts/share/actor_metatable.lua` | `ActorMT:ModifyHP/ModifyMP` | 夹取 + 置 `PROP_IS_DEAD` | ⚠️ | 派生死亡标记 ✅；但 `ModifyMP` 用 `GetMaxHP()` 夹取是 bug ⇒ 不可照抄 |
| `scripts/share/actor_metatable.lua` | `ActorMT:Variation()` + `utils.lua:decode_mypal()` | 读 `wpal` 调色板 → `from/to/mat` 段 → `PROP_PAL_MATRIX` | ❌ | **梦幻西游专属美术格式**（`wasee_pal/*.wpal`，121 个），JSTM 无对应资源 |
| `scripts/share/actor_metatable.lua` | `ActorMT:GetRandomSkillID(type)` | 按门派/召唤兽筛 `skill.tsv` 随机 | ⚠️ | NPC 自动选技能的朴素做法；JSTM 若有 AI 应做权重/条件选择，别照抄"纯随机" |
| `scripts/server/actor_system.lua` | `actors_on_load` / `actors_on_save` | 全量 JSON 读/写 `actor.data` | ❌ | 明文 + 全量重写 + 含瞬时战斗态 + 含 NPC（见 5.3）；JSTM 已用 sqlite，不应倒退 |
| `scripts/server/actor_system.lua` | `ActorMT:AddSummon/GetSummon/GetSummons`, `stub[PTO_C2S_CREATE_SUMMON/FETCH_SUMMON]` | 召唤兽 uid 列表存 JSON 字符串属性；服务端 `__summons__` 表 | ⚠️ | **"孩子挂在父亲的引用列表里"** 思路简单；但 `AddSummon` 无条件 `uids_str='[]'` ⇒ 只能 1 只（bug）；且 `cjson.decode(nil)` 会崩 |
| `scripts/server/actor_system.lua` | `stub[PTO_C2C_LOGIN]` | 首次登录建角色（type=PLAYER、出生点取 `scene.tsv` 的 `birth_pos`）；给本人发全部玩家、给他人发新玩家、再发 NPC 列表 | ✅ | **登录数据编排**（谁收到什么）写得清楚，是"玩家进场同步"的完整样例（见 `battle.md` Q8）|
| `scripts/server/actor_system.lua` | `stub[PTO_C2S_CREATE_PLAYER]` | `cjson.decode(js)` 后整体 `actor:SetProperties(props)` | ⛔ | **客户端权威**：客户端可任意改自己属性（等级/HP/装备加成）⇒ 作弊入口 |
| `scripts/server/team_system.lua` | `TeamMT`（9 方法）+ `team_system_*` + `stub[PTO_C2S_TEAM_*]` | 队伍对象表 + `PROP_TEAM_ID` 反查；`Serialize()` 统一出网 | ✅ | **"对象表 + 单属性反向索引"** 是干净的关系建模；**队伍不持久化**是缺陷（重启即散）|
| `scripts/client/module/team.lua` / `module/summon.lua` | 客户端侧同名方法 | 与服务端 metatable **同名同语义**（双端共享 `ActorMT`）| ⚠️ | **"同一套 API 名在两端都有实现"** 降低心智负担；但也意味着**同名函数被反复覆盖**（`GetSummon` 在 share/server/client 三处定义）⇒ 谁最后加载谁生效，极易出错 |
| `assets/storage/account.data`, `actor.data` | — | 明文 JSON | ⛔ | 明文密码 + 可被客户端触发写入 |
| `scripts/generator/actor_template.lua` | `gen_actor_enum()`, `solve()` | TSV → `actor_enum.{h,cpp}` | ✅ | **本项目最有价值的工程实践之一**：内容表 → 编译期枚举 → 运行时默认值，三者同源。JSTM 可用它把 `role_attr.json`(27 KB) 生成 Python 常量模块 + 校验表 |
| `assets/tables/level.tsv` | `level, role_exp, pet_exp` | 升级经验表（0→175 级）| ❌ | **数值属《梦幻西游》**（`assets/doc/roadmap.md` 里贴了同一份表）；JSTM 已有自己的 `exp_table.md`/`level_table.json` |
| `assets/tables/school.tsv` | 15 门派 | 门派 id→名 | ❌ | 梦幻西游 15 门派，与 JSTM 职业体系无关 |
| `assets/tables/summon_quality.tsv` | 资质/成长 | 召唤兽资质表（`take_level/battle_level/atk_qual/.../grow_coef`）| ⚠️ | **"资质 + 成长率"双维度建模**是有意思的设计（梦幻西游/大话系宠物体系），**结构可借、数值不可借**；JSTM 的伙伴(hero)体系是否用这套需另判 |
| `assets/doc/roadmap.md` | 全文 | 含属性→资源映射（体质→HP、力量→攻击/灵力、耐力→防御、敏捷→速度）| ⚠️ | **"五维 → 派生属性"的映射表**可与 JSTM 的 `role_attr` 对照（JSTM 侧已有 `analysis/1.4.9/level/role_attr.json` 27 KB），但两游戏映射关系不同 |

---

## 8. 未读到 / 待验证（角色模型）

- 【未读到】`common/src/actor/action.cpp`（`ActionStateMachine`，21 KB）—— 客户端的动作状态机实现细节（只读到片段）。
- 【未读到】`common/src/actor/actor_event.h`（85 字节，仅 `ACTOR_EV_ON_CLICK/ON_HOVER` 枚举）。
- 【未读到】`client/src/actor/move.cpp`、`common/src/entity.cpp`、`common/src/state.cpp`（后者仅 20 字节 = 只有 include）。
- 【待验证】入库的 `actor_enum.h` 与 `actor_template.tsv` **是否严格一致**（`actor_enum.h` 末尾几项疑似手工增补，见 3.2）。
- 【待验证】`SetProperties` 依赖 Lua 5.3 把字符串键 `"45"` 强转为整数索引 —— 该强转在 `lua_tointeger` 中的行为依赖 Lua 版本/编译选项（`LUA_NOCVTN2S` 等），未在本 ZIP 内验证。
- 【未读到】`PROP_BASE_*` 与 `PROP_*_EXTRA` 的任何**消费者**（公式里只用 `PROP_ASSIGN_*` 与 `PROP_EQUIP_*`）⇒ 这批属性疑似预留未接线【已确认在已读代码中无消费者，标"疑似"】。
- 【未读到】`ACTOR_TYPE_DEFAULT/PLAYER/SUMMON/NPC`、`ACTION_*`、`DIR_*`、`WEAPON_*`、`ROLE_*` 的**具体数值**（在 `actor.cpp` 的 `luaopen_actor` 中 `REG_ENUM`，仅读到文件前 ~300 行）；`assets/doc/LuaAPI.md` 确认它们**存在且为全局常量**。
