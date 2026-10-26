# CXEngine（YZXY / 原罪西游）可借鉴点清单

> 依据：本目录 `architecture.md` / `protocol.md` / `lua_server.md` / `role.md` / `battle.md` 的逐文件审计。
> 标注【已确认】/【待验证】/【未读到】。
> 判定：⭐ 强烈建议借鉴（设计） / ✅ 建议借鉴（设计） / ⚠️ 参考 / ❌ 不适用 / ⛔ 必须排除。

---

## 0. 前置：两处必须先说清的事实

### 0.1 ⛔ 许可条件（最高优先级约束）

【已确认】**CXEngine 仓库内不存在任何 LICENSE / COPYING / NOTICE 文件。**
实测方法：枚举 ZIP 全部 501 条目，匹配 `license|copying|notice`（不区分大小写）—— **零命中**；
唯一的 `readme.md` 无许可声明，只给了网盘下载资源与 QQ 群号。
`.gitmodules` 列出 16 个 `github.com/oceancx/*` 的 fork（`cxlua`/`asio`/`NESupport`/`nlohmann`/`imgui`/`nangovg`/`ejoy2d`/`luadbg` 等），
但那是**第三方依赖**，不构成对本项目自身代码的授权。

⇒ **依据任务书【原则 3】：本项目只能"研究 + 借鉴设计思想"，绝对不得复制任何代码文件、函数体、注释块、表数据。**
这与本工作区既有 `analysis/server_reference/license_audit.md` 对 CXEngine 的判定完全一致（该项结论为「⚠️ 未声明许可 ⇒ 只可借鉴设计」）。

**本文所有"借鉴"均指"设计思想"**，落地时必须用 JSTM 自己的语言（Python）、自己的协议（现状 `[u32 BE len][u16 BE cmd][body]`）、自己的命名重写。

### 0.2 ⚠️ 任务书前提的一处冲突（必须上报）

任务书要求「特别注意：YZXY 是回合制 MMORPG ⇒ 回合制战斗状态机不能套用到 JSTM 的动作/实时战斗」。

- **CXEngine 侧**：【已确认】回合制（见 `battle.md` 第 1 节，6 条代码级证据）。
- **JSTM 侧**：本工作区**既有字节码取证结论是「JSTM 1.4.9 也是独立回合制战斗场景」**：
  - `analysis/1.4.9/battle/battle_flow.md` 第 1 节标题即「**1.4.9 使用「独立回合制战斗场景」，不是地图直接战斗。**」
  - `analysis/1.4.9/battle/battle_protocol_matrix.md`：`20001–20030` 是**真正的战斗协议段**（含该文 §3.1 订正：`11000/11200` 段**不是**战斗）。
  - `analysis/jstm_1.4.9/protocol_index.md` 列出 `20000~20099` 段 25 条战斗命令。

⇒ **"JSTM 是动作/实时战斗"这一前提与既有取证不符。**
本文**不按前提删减内容**，而是给出**真正的技术理由**（见第 2 节 §2.1）。
"不能照搬 CXEngine 回合制状态机"这个**结论仍然成立**，理由见 §2.1(b)。

> ### ⚠️ 本节第一版有错，已订正（2026-09 追加）
> 第一版我写的原因是「**回合节奏的所有权相反**」（CXEngine 客户端本地推进 vs JSTM 服务端 `CS_20014` ACK 驱动）。
> **该原因作废**——它引用的 `battle_chain_verified.md` 描述的是**我们自己 `mock_server.py` 的实现**
> （`行 2445 if cmd == 20014:`），不是真机客户端行为。字节码权威来源
> `battle_protocol_matrix.md` §3.0/§3.1 的真机订正明确记载：
> **客户端 `CS_20011` / `CS_20014` 在整场战斗中「从未发出」**，
> ⇒ 「整场战斗会停在第一回合之前，除非服务端自己推进」，现阶段做法是
> **服务端自己按节拍推进（2.5 秒/回合，自续期）**，并注明「客户端为何不发 20014 尚未定位」。
> ⇒ **JSTM 与 CXEngine 在"服务端不等客户端"这点上是相似的**（一个客户端推、一个服务端推），
> **不存在"所有权相反"**。正确理由见 §2.1(b)（5 条字段级证据）。
> 同时，第一版 §1.④ 里"JSTM 的 `SC_20012/20013` **必须**显式带 buff 增/减/剩余回合"也**说过头了**：
> JSTM **本来就有**载体（并且经二次订正后确认：**载体是 `magic_list[]`,不是 `specials[]`** —— 见 §1.④ 第二个订正框与 `jstm_battle_fields.md`），
> 真正未知的是 `magic_list` 的**全量/增量语义**（`magic_list` 的字段与 `duration` 语义**已解出**）。

若任务书中的"实时/动作"指的是**地图层**（JSTM 的 `SC_10212/10213` 怪物在场景内实时移动、带 `x/y/dir`，见 `battle_flow.md` 2.1 节），
则"实时"只在地图层成立，**战斗层仍是回合制**——这一点已在该文第 2.1 节明确。

---

## 1. ★ 对 JSTM 的建议（一）：值得借鉴的设计思想

> 按"借鉴什么 → 为什么 → 落到 JSTM 哪里"写，共 12 条，前 5 条为最高优先级。

### ① ⭐ 「TSV/表单一真源 → 生成多端定义」的内容管线

**借鉴什么**：CXEngine 把**角色属性清单**放在 `assets/tables/actor_template.tsv`（`name/type/def/sync` 四列），
然后用 `scripts/generator/actor_template.lua` 从同一张表**生成 C++ 枚举**（`actor_enum.h` 的 `EActorProp`），
运行期再由 `actor_on_reg_props` 读**同一张表**注册默认值。
协议 ID 也是同一套路：`scripts/share/enums_protocol.lua` → `scripts/generator/protocol.lua` → `common/src/protocol.{h,cpp}`。

**为什么值得**：一句话定义三处使用，**三者不可能漂移**；且 `RegProperty` 的 `assert(index == m_Props.size())`
把"表行序 == 枚举值 == 数组下标"用断言锁死，错了立刻炸而不是静默错位。

**落到 JSTM**：JSTM 有 `protocol/fields.json`（3553 条字段定义）与 347 张配置表（`assets/src/config/*.luac`）。
建议**以 `fields.json` 为唯一真源，生成一个 Python 常量/结构模块**（如 `jstm/proto_defs.py`），
供 `mock_server.py`、测试脚本、抓包解码器共用；并在 CI 里校验"生成物 == 仓库内文件"。
⇒ **不要**学它"生成的 C++ 头文件不入库导致仓库不自洽"（`common/src/protocol.h` 实测只有 `CX_MSG_HEADER_LEN`，见 `protocol.md` 3.2）。

### ② ⭐ 「协议号 → 处理函数表」的零样板分发 + 两阶段收包

**借鉴什么**：
- 全局 `stub[PTO_XXX] = function(req, js) … end`，分发处只有 4 行：
  `local type = pt:ReadAsInt(); local js = pt:ReadAllAsString(); local req = cjson.decode(js); stub[type](req, js)`；
- **两阶段**：`server_thread_on_message` 里把"握手期必须立刻答"的（注册 `SIGNUP` / 登录 `LOGIN` / GM）当场处理，
  **其余一律 `netq:push_back` 入队**，由主循环 tick 里的 `game_server_dispatch_message` 统一派发。

**为什么值得**：① 消除 `if/elif` 长链；② 避免在 IO 回调里做重逻辑，同时保证握手低延迟。

**落到 JSTM**：`mock_server.py` 目前偏 `if cmd == 20002:` 式长链（见 `battle_chain_verified.md` 引注"行 2371"）。
建议改为 `HANDLERS: dict[int, Callable]` + 装饰器注册，并保留"握手期立即处理 / 主循环派发"两阶段。

### ③ ⭐ 「C++ 提供原语、Lua 承载全部游戏逻辑」的分层 + `IsServer()/IsClient()` 同码分叉

**借鉴什么**：`common/src/script_system.cpp` 用一张**显式清单**注册全部 C 能力（`luaopen_actor/actor_manager/protocol/net/timer_manager/...`），
之后 C++ 只在 5 个生命周期点回调 Lua（`on_script_system_init/update/deinit/draw` + `main.lua`），
游戏逻辑 100% 在 Lua；同一份 Lua 用 `if IsServer()` / `if IsClient()` 分叉，`scripts/combat/combat_system.lua`
末尾直接按角色 `script_system_dofile` 加载 `combat/server/…` 或 `combat/client/…`。

**为什么值得**：逻辑与引擎彻底解耦 ⇒ 改玩法不用重编、热重载可行、同一份战斗代码两端复用（服务端只算、客户端只播）。

**落到 JSTM**：JSTM 模拟器是 Python，天然"逻辑即脚本"，**不需要**照抄这层；
但**"同一份战斗定义，服务端算结果、客户端播表现"**这个**职责切分**值得沿用（见 §1.④）。
另外"能力显式清单"这一点值得学：JSTM 逆向时最缺的正是**"客户端 Lua 可调哪些原生函数"的权威清单**——
建议做一份 `native_api.md`（本工作区已有 `native_callback_findings.md`，可扩为完整清单）。

### ④ ⭐ 「随机数只在服务端摇，结果随消息下发，客户端照结果播」的权威原则

**借鉴什么**：`scripts/combat/skill/26.lua`（催眠符）是最干净的范例：

```lua
if IsServer() then
    local rate = formula_calc_seal_success_rate(...)
    if math.random() < rate then skill.success = true;  actor_add_buff(hit_actor, 30)
    else                         skill.success = false end
end
if IsClient() then
    if skill.success then actor_add_buff(hit_actor, 30) end   -- 只按服务端结果播表现
end
```

伤害同理：服务端算完写进 `effect.hp_deltas = {{target = -772.0}}` 与 `effect.life_state = {master=…, target=…}`，
客户端 `on_attack_action_callback` 里只做 `target:ShowBeatNumber(hp_deltas[atk_counter].target)`。

**为什么值得**：这是战斗不脱同步的**唯一正确做法**。

**落到 JSTM（已订正表述）**：JSTM 的 `SC_20013`（回合开始）**已经**是"服务端算好结果逐条下发"：
字段 `magic_play[] = (order, target_anger, target_id, source_id, **hit:int8, hp_max:u32, hp:u32, is_target_die:u8**, target_talk, magic_list[])`
（`cmd_resolve_200.luac` proto#35，见 `battle.md` §5.6）。
⇒ **这一点 JSTM 已经做对了，不需要"新增"**；客户端也不得自行计算
（旁证：客户端有 `10601 测试战斗伤害` / `10610 战斗验算` 两套**本地演算**，但最终以服务端 `SC_20013.hit` 为准）。

> ### ⚠️ 本条第一版说过头了，已订正
> 第一版我写的是「JSTM 的 `SC_20012/20013` **必须显式带 buff 增/减/剩余回合**」。
> **问题**：这是我在**未读 JSTM 侧字段定义**时的推断（当时把 JSTM 字段标为【未读到】），属于越界断言。
> **订正后的事实**（`tools/proto_spec.py cmds 20013` / `dsc SC_20013` 直读 1.4.9 字节码）：
> JSTM **本来就有**状态载体 —— 单位快照 `SC_20013.summon_play[]` 每回合携带
> `hp_max, hp, anger, is_auto, animate_res[], skills[], specials[]`，其中
> **`specials[] = (key:u8, val:u32)`** 就是一个通用"键→值"状态通道； ⚠️**（此判断错，已被本节 3 段后的"⚠️⚠️ 二次订正"推翻：`specials` 是外观通道，非 buff 载体）**
> `SC_20010.fighter_info_list` 的 18 字段里也有同名 `specials[]`；
> 技能状态另有 `skills[] = (bid:u32, step:u8, last_use:u16, cd:u16)` 与专用的 `SC_20012.cooldown[] = (bid:u32, last_use:u16)`。
> ⇒ **CXEngine 才是"buff 不上线"的较弱一方，JSTM 反倒更强**（每回合重推单位状态）。
>
> **⇒ 真正要做的不是"新增字段"，而是三个【尚未确认】的问题**：
> 1. **`specials` 的 key 语义**：哪个 key 对应哪个 buff/状态（`all_proto.luac`/`cmd_resolve_200.luac` 里未解出 key 表）；
> 2. **`specials` 是全量快照还是增量**：`SC_20013` 每回合重推时，是"全量覆盖"还是"仅变化项 + 客户端自行合并"；
> 3. **剩余回合数走哪里**：`SC_20012.cooldown.last_use` 与 `skills[].last_use/cd` 是"上次使用/冷却"语义（同类但**不等价于 buff 剩余回合**），
>    buff 剩余回合是否在 `specials` 的某个 `val` 里，还是**不下发**（像 CXEngine 那样靠客户端计时），**未确认**。
>
> 另有两个子结构**尚未解出**（`battle_protocol_matrix.md` §6 自述待展开，本次 `proto_spec.py dsc` 只得到标题行）：
> **`Dsc20012magic_play`、`Dsc20012summon_play`、`Dsc20013magic_list`** 的字段名与顺序。
> ⇒ **在这三项解出之前，不能断言"buff 具体走哪个字段"**。
>
> ---
> ### ⚠️⚠️ 上面这一整段也已解出，并暴露了**第二处错**（二次订正，依据 `jstm_battle_fields.md`）
>
> 我随后做了字节码穷举（扫 `assets/src/game/**` 全部 `.luac`，匹配 `KSTR 'key'` → `KSHORT n` → `TGETS 'specials'`
> 的 `keyfind('key', n, specials)` 模式），结论是 **`specials` 与 buff 毫无关系**：
>
> **① `specials` = 伙伴/宠物的"外观属性"通道**
> 全仓库只有 **8 个 key（1,2,4,5,6,7,8,9）**，全部在 `battle_role.luac` proto#2（`createBattleRole`）消费，
> `val` 用作 `Config.PartnerBase` / `PartnerStageEffect` / `PartnerHaloEffect` / `PartnerRebirthEffect` 的**配置 ID（uint32）**：
>
> | key | 语义 |
> |---|---|
> | 1 / 2 | 伙伴**模型资源**（`PartnerBase[val].resource` / `.by_resource`）|
> | 4 | 伙伴**配色**（`partner_color`）/ 评分（`pingfen`）|
> | 5 | **阶段特效**（`PartnerStageEffect[val].effect` → `effect_spine_name`）+ 视频资源（`sp_resource`）|
> | 6 | **光环特效**（`PartnerHaloEffect[val].effect` → `ring_effect_name`）|
> | 7 / 8 | **重生特效**（`PartnerRebirthEffect[val].effect` → `rebirth_effect_name`）|
> | 9 | **羁绊伙伴**标记（`isFetterPartnerBorn`，布尔）|
>
> **② 真正的 buff/状态载体是 `magic_list[]`**
> 格式串 `iiChhC`（`cmd_resolve_200.luac` proto#24 / proto#37，两处同形）：
>
> | 字段 | 类型 | 语义 |
> |---|---|---|
> | `magic_bid` | `int32` | 效果配置 ID → `Config.SkillMagic[magic_bid]`（**12665 行**）|
> | `change_hp` | `int32` | 每回合 HP 变化（DoT/HoT，有符号）|
> | **`duration`** | **`uint8`** | **★ 持续/剩余回合数** |
> | `per` | `int16` | 百分比数值（模板占位 `{per}`）|
> | `val` | `int16` | 绝对值（模板占位 `{val}`）|
> | **`fold`** | **`uint8`** | **叠加层数**（UI 渲染 `'(%s层) '`）|
>
> 挂载位置：`SC_20012.skill_play[].magic_play[].magic_list[]` 与 `SC_20013.magic_play[].magic_list[]`。
> 客户端证据：`battle_role.luac` proto#4（buff 提示框）用 `duration` + `fold` 渲染，
> 并按 `Config.SkillMagic[bid].type` 显示"**控制效果 / 增益效果 / 减益效果**"；
> `battle.luac` proto#126 里 `entry.magic_bid` 被改名为 `bid`（`{ bid = entry.magic_bid }`）用于查配置，
> 并判 `entry.duration >= 0` 决定是否仍在生效。
> 配置侧另有 `Config.SkillMagicType` = **31 个效果属性 ID**（1010–1280，含 `1240 control`、`1250 anti_control`、`1130 cure`，
> 命名 `_s`=固定值 / `_p`=百分比 / `_rate`=几率 / `be_`=受方 / `red_`=减免 / `res_`=抗性）。
>
> **③ 结论改判（第二次）**：JSTM 的 buff 同步**远比 CXEngine 强** —— 它**逐条带 `duration`（剩余回合）、
> `fold`（层数）、`change_hp`（每回合HP变化）、`val`/`per`（数值/百分比）上线**；
> 而 CXEngine 的 buff **完全不上线**（存服务端 `__actors_buffs__`，客户端靠重放判定）。
> ⇒ **"JSTM 已有载体"这句的"载体"必须是 `magic_list`，不是 `specials`。**
> ⇒ **三个【尚未确认】全部解出**（key 语义 = 外观通道 / 与 buff 无关；创建时一次性消费；剩余回合 = `magic_list[].duration`），
> 且 `magic_play`(10 字段) / `summon_play`(16 字段) / `magic_list`(6 字段) 的字段名与顺序**均已解出**。
> 完整字段表与复现命令见 **`jstm_battle_fields.md`**。**本段保留以留痕，最终以 `magic_list` 为准。**

**★ 由上面第 ② 项派生的一条真正可落地的建议（把 CXEngine 的另一处机制接上）**

> ⚠️ 本段第一版把主体写成 `specials`/`skills`，**已订正为主体 `magic_list`/`skills`**（`specials` 是外观通道，与 buff 无关）。

`magic_list`/`summon_play`/`skills` **若是全量快照** ⇒ 服务端每回合无脑填充即可，**不需要** CXEngine 的任何东西
（这是最省事的形态，也最可能是 JSTM 原版的形态，因为 `SC_20013` 每回合都带完整单位状态：
`summon_play` 16 字段里就含 `hp/hp_max/anger/skills`）。
**若是增量（仅变化项）** ⇒ 服务端必须**为每个连接维护"该客户端已知的状态"并算差额**——
这正是 CXEngine 的 **脏属性机制**（`Actor::SetProperty → DirtyProperty(index)` 进 `std::set<int> m_DirtyProps`；
`IsDirty()/GetDirtyProps()/ClearDirty()` 暴露给 Lua；`on_script_system_update` 每 tick 收 `[[pid, prop_id, value], …]` 发 `PTO_S2C_SYNC_PROPS`；
并用 `actor_template.tsv` 的 **`sync` 列**（`is_prop_sync()`）决定哪些字段才值得同步）。

**⇒ 状态：`magic_list` 的"全量/增量"语义仍是【未解出】**（`jstm_battle_fields.md` §8），需真机抓包确认。
- 已确认的可用经验：**"表里给每个字段标 `sync` 是否参与同步" + "只发脏字段"** 这套做法（`role.md` §3.1）；
- CXEngine 的**缺陷要避开**：它把脏差分**广播给全服所有人**（无 per-client 已知状态），
  对"每人的已知状态不同"的场景会出错 ⇒ 若 JSTM 走增量，**diff 基准必须是 per-connection 而不是全局**。
- **但要注意**：`magic_list` 里带 `duration`，而 `duration` **每回合都会变** ⇒
  即便 JSTM 原版是"仅变化项"，**剩余回合也必然每回合重发**（否则客户端无法显示倒计时）。
  ⇒ 这意味着**buff 状态实际上更接近"每回合全量重列"**，从而**大概率不需要** CXEngine 的脏差分机制。

### ⑤ ⭐ 「技能/buff = 静态表 + 按 ID 命名的脚本回调」

**借鉴什么**：
- `assets/tables/skill.tsv` 给静态数据（type/sub_type/school/combo/group_kill/atk_anim…）；
- `scripts/combat/skill/<id>.lua` 给**逐技能特化逻辑**，只暴露 3 个回调 `SkillOnStart/SkillOnHit/SkillOnEnd`；
- 启动时 `init_skills()` 遍历表、`io.open` 找同 ID 的脚本、`load(chunk,'@'..path,'bt', module)` 求值，把回调挂回表行；
- **表的行本身就是模板对象**，运行时 `skill_init_by_templ(skill, templ)` 拷字段 + 拷回调进实例。
- buff 完全同构（`buff.tsv` + `buff/<id>.lua` 的 `BuffOnStart/BuffOnEnd/BuffOnNextTurn`）。

**为什么值得**：300+ 技能里只有 5 个需要特化（实测 `skill/` 只有 `1,2,6,20,26.lua`），
**通用流程走表、特例走文件**——扩展时不需要改核心，也不需要 300 个空分支。

**落到 JSTM**：JSTM 的技能/效果配置在 `config`（`_config_*`），建议对"特殊技能"建 `jstm/skills/<id>.py`，
只暴露 `on_start/on_hit/on_end`（或 `on_apply/on_expire/on_tick`），由核心按 ID 动态加载。
⇒ 注意：CXEngine 的这套机制**实际只被用了 2 个技能**（20、26）⇒ 借鉴**机制**，别声称它已被验证。

---

### ⑥ ✅ 战斗常量集中 + 状态机与数据分离

**借鉴什么**：`scripts/combat/combat_context.lua` 把 `BATTLE_*` 七态、`TEAM_TYPE_*`、`SKILL_SUBTYPE_*`、
`ACTOR_LIFE_*`、`SKILL_STATE_*` 全部集中在一个 40 行文件；
`BattleMT` 数据只有 `{id, actors, cmds, state, turn, type}` 五个字段，状态迁移全在方法里。

**落到 JSTM**：建 `jstm/battle/constants.py`，把 20000 段战斗相关的状态/阵营/技能子类型写全，
避免在 handler 里散落魔法数字。（注意 `COMMAND_STATE_*` 与 `COMMAND_TYPE_*` 在 CXEngine 里**定义了却没人用**——只写真正在用的。）

### ⑦ ✅ 回合内出手顺序按服务端算（`CalcSpeed()` 降序）

**借鉴什么**：`handle_turn_commands(battle)` 先 `table.sort(battle.cmds, by CalcSpeed() desc)` 再逐条结算。

**为什么值得**：回合制的核心规则之一；且**排序是在服务端做的**，客户端只按 `all_skills` 的顺播。

**落到 JSTM**：`SC_20012/20013` 的推送顺序应由服务端按速度决定（JSTM 是否已有速度字段需按 `fields.json` 确认）。

### ⑧ ✅ 「先快照收件人，再结算」的收件人安全模式

**借鉴什么**：`handle_turn_commands` 开头：

```lua
-- 先记录当前 actors 里面玩家的 pid，因为战斗处理有可能移除掉
local send_pids = {}
for i, actor in ipairs(battle.actors) do
    if actor:IsPlayer() then table.insert(send_pids, actor:GetID()) end
end
-- …结算过程中 actor 可能被移出战斗…
for i, pid in ipairs(send_pids) do net_send_message(pid, PTO_S2C_COMBAT_EXECUTE, …) end
```

源码注释里就写明了原因（"因为战斗处理有可能移除掉"）。

**落到 JSTM**：任何"结算 → 广播"的链路都必须先快照收件人 id，否则被击飞的单位会导致其主人收不到消息。

### ⑨ ✅ 「按范围选收件人」的两处雏形（JSTM 需要正式化）

**借鉴什么**：CXEngine 整体是**全服广播**（`net_send_message_to_all_players` 用于移动 `PTO_C2C_MOVE_TO_POS` 与聊天 `PTO_C2C_CHAT`），
但它有**两处**已经在收窄范围：
- `combat_system_send_message(battle, proto, msg)`：只发给 `battle.actors` 里的玩家；
- `combat_system_update()`：只把**战斗中非玩家且无主人**的 actor 脏属性推给**该战场**的玩家。

**落到 JSTM**：JSTM 是实时地图 + 场景内多玩家（`SC_10212` 附近怪物进场），**必须有 AOI**。
把 CXEngine 这两处"按战斗范围发送"推广成"按场景/按视野发送"即可 —— 这是最该补的一环。

### ⑩ ✅ 具名定时器管理器（回调用 registry ref 防 GC）

**借鉴什么**：`common/src/time/timer_manager.cpp` 用**字符串名**索引定时器
（`timer_manager_add_timer('TimerWildBattle', 15000, fn, true)`），
支持 `PauseTimer/ResetTimer/ForceEndTimer/ForwardTimer`；Lua 回调通过 `luaL_ref(L, LUA_REGISTRYINDEX)` 持有，
删除用 `m_GarbageContainer` 双缓冲延迟释放（避免在遍历中改容器）。

**落到 JSTM**：JSTM 有大量"活动刷新/冷却/自动战斗/野外遇怪"类定时任务，
具名定时器比匿名 `setTimeout` 好调试得多（可 `pause/reset/force_end` 单个逻辑时钟）。
`TimerWildBattle` 的用法特别值得学：**进战斗时 pause、退战斗时 resume**（`combat/client/combat_system.lua`）。

### ⑪ ✅ 异步加载任务表（后台线程 + 去重 + 主线程轮询状态）

**借鉴什么**：`common/src/file_loading.cpp` 的 `FileLoadingThread`：
`PostTask(path, parser)` 入队（**同路径去重**，已在加载/已完成则跳过），单后台线程消费，
主线程用 `IsFileLoading(path)` / `IsFileLoadOk(path)` 轮询。

**落到 JSTM**：JSTM 的表很大（实测 `_config_mon_data.luac` 857 KB、`_config_item.luac` 838 KB、`_config_mon.json` 818 KB），
启动/切场景时异步加载 + 状态轮询能显著缩短卡顿；去重键也避免重复解析同一张表。

### ⑫ ✅ 可执行文档 + 文档即短板清单

**借鉴什么**：
- `assets/doc/LuaAPI.md`：手工维护的**"Lua 可调 C 函数 / 全局枚举 / metatable 方法"完整清单**（约 500 行）；
- `scripts/examples/example00..07.lua`：**可运行教程**（`example03.lua` 头注释直接列出全部 `ACTION_*`/`WEAPON_*`/`ROLE_*`/`SCHOOL_*` 枚举含义）；
- `assets/doc/roadmap.md`：自己列出了未完成项（"战斗逻辑挪到服务端"、"回合机制完善"…）；
- `assets/doc/server.md`：状态机 mermaid 与代码**一致**。

**落到 JSTM**：① 维护一份 `native_api.md`（客户端可调原生函数）；② 把关键协议链做成**可运行的 pytest 夹具**而不是纯 md；
③ 立项文档里显式列"已知未完成项"，避免后人误以为已实现（CXEngine 的 `PTO_C2S_COMBAT_PVP_START` 是**空函数**，就是隐患）。

---

## 2. ★ 对 JSTM 的建议（二）：完全不能借鉴的

### 2.1 ⛔⛔ 回合制战斗状态机（`BattleMT` 的回合推进模型）—— **不能套用**

**任务书已提示此条，此处给出精确边界与**真正**原因。**

#### (a) 结论

⛔ **`scripts/combat/combat_system.lua` 的 `BattleMT` 状态机（`BATTLE_TURN_STAND_BY → BTTALE_TURN_EXECUTE → BTTALE_TURN_NEXT`）
不能移植到 JSTM。** 但**不是**因为"JSTM 是实时/动作战斗"（见 §0.2：既有取证显示 JSTM 1.4.9 同为回合制）。

#### (b) 真正的原因：**JSTM 的战场数据模型比 CXEngine 丰富得多，CXEngine 的 `BattleMT` 表达不了**

> ⚠️ **第一版的 (b) 是错的，已被本节替换。** 第一版写「回合节奏的所有权相反：CXEngine 客户端本地推进 vs
> JSTM 服务端 `CS_20014` ACK 驱动」。该说法引用的 `battle_chain_verified.md` 描述的是**我们自己
> `mock_server.py` 的实现**（`行 2445 if cmd == 20014:`），而字节码权威来源
> `battle_protocol_matrix.md` §3.0/§3.1 的真机订正明确记载：
> **客户端 `CS_20011` / `CS_20014` 在整场战斗中「从未发出」**（`tcp.log` 无 `cmd=20011` / `cmd=20014`），
> ⇒「整场战斗会停在第一回合之前，**除非服务端自己推进**」，现阶段做法是**服务端自己按节拍推进（2.5 秒/回合，自续期）**，
> 并注明「客户端为何不发 20014 尚未定位」。
> ⇒ **JSTM 与 CXEngine 在"服务端不等客户端"这一点上是相似的**（JSTM 服务端自推、CXEngine 客户端自推），
> **不存在"所有权相反"。** 请以本节 (b) 的五条为准。

【已确认，代码级】CXEngine 的回合推进确实是**客户端本地**完成的（`combat_system_update` 播完技能直接 `NextTurn()`，
服务端只在收到下一条 `PTO_C2S_COMBAT_CMD` 时推进）。**但这只是它"弱"的表现之一，不是不可移植的根本原因。**

**根本原因是以下 5 条，每条都有 JSTM 侧字节码字段证据**（字段见 `battle.md` §5.6）：

| # | 理由 | 证据 |
|---|---|---|
| 1 | **战场数据模型表达力不足** | JSTM `SC_20010` 带 **阵法**（`atk_formation_type/lev`、`def_formation_type/lev`）、**回合波次**（`round_wave`/`wave_max`/`wave_no`）、**观战**（`is_observer`）、**战斗特效**（`effect_id`），单位 **18 字段**（含 `specials[]`/`skills[]`/`animate_res[]`）。CXEngine `BattleMT:Serialize()` 只有 `{id, team_type, pos_id}`（NPC 再加 `props`）⇒ **表达不了 JSTM 的一回合** |
| 2 | **单位状态"每回合重推"** | JSTM `SC_20013.summon_play[]` 每回合带 `hp_max/hp/anger/is_auto/animate_res[]/skills[]/specials[]`。CXEngine **无任何单位重推机制**，buff 状态**完全不上线**（`battle.md` §4.4）⇒ CXEngine 是**较弱**的一方 |
| 3 | **线格式与协议哲学不同** | JSTM `[u32 BE len][u16 BE cmd][二进制字段序]` vs CXEngine `[LE u32][LE u32][JSON]`（本文件 §2.2）|
| 4 | **JSTM 有 CXEngine 完全没有的整块子系统** | 观战（`20016/20017`）、战斗录像（`20025–20030`）、自动战斗（`20008` + 客户端 `dungeon/auto_fight.luac`）、客户端侧战斗演算（`10601/10610`）、出手顺序列表（`SC_20010.order_list` / `SC_20013.order_list`，客户端有 `initOrder`/`playOrder`）|
| 5 | **安全模型与内容不可复用** | 见本文件 §2.3 / §2.5 |

⇒ **换句话说：不是"节奏对不上"，而是"CXEngine 的战斗对象比 JSTM 需要的少了一半字段"。**
照搬 `BattleMT` 会**丢字段**（阵法/波次/观战/CD/怒气/单位重推），而不是"丢节流"。

#### (c) 如果照搬会发生什么

| 后果 | 说明 |
|---|---|
| **丢字段**（最主要） | `SC_20010` 的阵法/波次/观战/`effect_id`、单位的 `specials/skills/animate_res/anger`、`SC_20012.cooldown` 全无对应；客户端 `battle.luac`（150 proto / 104 方法）期望的数据没有 ⇒ 战斗场景无法正常表现 |
| **服务端失去节拍控制** | CXEngine 让**客户端**推进回合。JSTM 真机客户端连"播完了"都不发（`CS_20014` 未发）⇒ 若再让客户端推回合，服务端将完全无法处理慢客户端/挂机/断线（CXEngine 自身也无回合超时，见下条） |
| **无回合超时兜底** | CXEngine **完全没有**回合超时（`assets/doc/combat.md` 说"倒计时 30s"，代码里**没有**）。JSTM 的 `SC_20013.time:uint8`、`SC_20010` 的波次字段暗示有**服务端节奏控制** ⇒ 必须由服务端掌握 |
| **掉线处理不可接受** | CXEngine：一人掉线 → `combat_system_battle_on_actor_leave` → **整场战斗结束**（`battle.md` §5.2）。JSTM 有观战（`is_observer`）与多人在场 ⇒ 不可能这么做 |
| **无观战概念** | CXEngine 的 `battle.local_team_type` 是**单机本地玩家视角**语义；JSTM 有 `is_observer` + `20016/20017` 观战协议 ⇒ 照搬会算错阵营 |

#### (d) 可以借鉴的**部分**（把状态机拆开看）

| 可借 | 不可借 |
|---|---|
| ✅ 状态**命名与分层**（准备/开始/待命/执行/下一回合/结束）| ⛔ 状态迁移的**触发者**（客户端本地 `NextTurn()`）|
| ✅ 服务端按速度排序定序（§1.⑦）| ⛔ "一次性下发整回合结果数组"的批次粒度（JSTM 是逐条推 `SC_20012`）|
| ✅ "先快照收件人再结算"（§1.⑧）| ⛔ `battle:Serialize()` 的全量战场结构（字段与 JSTM 的 `SC_20010` 不同）|
| ✅ "目标失效自动换目标" / "封禁校验"（`process_turn_command`）| ⛔ 客户端重放 buff 判定（见 §2.4）|
| ✅ "NPC 被击飞 → 移出战斗；玩家 → 就地倒地"的 `life_state` 差异化 | ⛔ 击飞轨迹实现（绑 800×600 屏幕边界）|

### 2.2 ⛔ 线格式：JSON 明文协议

【已确认】CXEngine 是 `[LE u32 len][LE u32 proto][UTF-8 JSON]`，**无 schema、无版本、无校验、无加密**。
【已验证】JSTM 是 `[u32 BE len][u16 BE cmd][body]`。

| 差异 | CXEngine | JSTM |
|---|---|---|
| 长度字段 | `u32` **小端** | `u32` **大端** |
| 命令号 | `u32` **小端** | `u16` **大端** |
| 载荷 | JSON 文本 | 二进制字段序（`AutoConstruct` 规格） |

⇒ **三项全不同，任何一侧照搬都会立刻断开客户端。** 且 JSON 载荷让"属性协议"退化成
`[[pid, 45, 987.0], …]` 这种**裸数字三元组**（`PROP_HP` 的数值直接上线），不可读、不可版本兼容。
⇒ JSTM 应保留自己的二进制字段序，**可读性靠"发送出口按 `fields.json` 解码打印"实现**，而不是改线格式。

### 2.3 ⛔ 安全模型（4 条必须排除）

| # | CXEngine 的做法 | 出处 | 为什么必须排除 |
|---|---|---|---|
| 1 | `stub[PTO_C2S_DOSTRING]`：`load(req.code,'@client','bt',_ENV)` 在**服务端执行客户端 Lua**（`PLAYER_DOSTRING`/`ACTOR_DOSTRING` 注入 `{player=…}` env，但仍可 `_ENV` 逃逸）| `scripts/server/main.lua` | **服务端远程代码执行**。哪怕只在开发期，也不得进入 JSTM |
| 2 | 用**请求体里的 `req.pid`** 决定回包对象，从不校验"该 pid 是否属于当前连接" | `actor_system.lua`、`team_system.lua`、`combat/*` 全部 handler | **任意客户端可冒领他人回包**（含队伍/战斗数据）。JSTM 必须用 `session → role_id` 的权威绑定，忽略 body 里的 pid |
| 3 | `stub[PTO_C2S_CREATE_PLAYER]`：`cjson.decode(js)` 后整体 `actor:SetProperties(props)` | `scripts/server/actor_system.lua` | **客户端权威**：可任意改等级/HP/装备加成 ⇒ 作弊入口 |
| 4 | `PTO_C2C_SAVE_ACTORS` / `PTO_C2C_SAVE_ACCOUNT_DATABASE` 由**客户端**触发服务端全量写盘；账号密码**明文**存 JSON | `actor_system.lua`、`server.lua` | 可被刷 IO / 竞态覆盖 / 明文密码。JSTM 已用 sqlite（工作区存在 `_db_before_battle.db`），不应倒退 |

**额外**：`GameSession::ReadPack()` 的 `len` 来自网络且**无上界校验**（`m_Buffer.ReserveWritable(40960)` 只是初始容量）
⇒ 畸形包可致大分配。JSTM 服务端必须校验 `len` 与 `cmd` 的合法范围。

### 2.4 ⛔ 「buff 状态靠客户端重放判定同步」

【已确认】CXEngine **没有任何 buff 同步协议**：buff 存在服务端 `__actors_buffs__[actor_id][buff_id]`（**不在 actor 属性里**），
客户端只能靠**执行同一段判定代码**来"猜"buff（`skill/26.lua` 的 `IsClient()` 分支 `if skill.success then actor_add_buff(...) end`；
`skill/20.lua` 也是同套路）。
后果：随机数、时序、丢失事件任一不一致 ⇒ **两端 buff 永久漂移且无纠正通道**。
（旁证：`PROP_ASM_BUFF_ANIM` 是唯一与"buff 表现"相关的属性，但在全仓库里**只被读到（`common/src/actor/action.cpp:188`）与被清 0（`scripts/combat/client/combat_system.lua:82`），没有任何地方写入真实的动画 ID** ⇒ 连"表现"这一半也只是预留未接线。）

⇒ **别学 CXEngine 的"客户端重放"这条路**。这是 CXEngine 战斗同步**最大的设计缺陷**，也是最容易照抄错的陷阱。

> ### ⚠️ 本段第一版结论有错，已订正
> 第一版我接着写「**JSTM 必须在 `SC_20012` 之类的回合消息里显式携带 buff 的增/减/剩余回合**」。
> **这是越界断言** —— 当时我把 JSTM 侧字段标为【未读到】，却在没有字段证据的情况下规定 JSTM 要加什么字段。
> **订正后的事实**（`tools/proto_spec.py` 直读 1.4.9 `cmd_resolve_200.luac`，见 `battle.md` §5.6）：
> JSTM **本来就有**载体，而且**比 CXEngine 强**：
> - 单位快照 `SC_20013.summon_play[]` **每回合**携带 `hp_max, hp, anger, is_auto, animate_res[], skills[], specials[]`；
> - **★ buff/状态的真实载体是 `magic_list[]`**（**不是** `specials` —— `specials` 经穷举确认是伙伴/宠物的**外观**配置通道，8 个 key，与 buff 无关；见 §1.④ 第二个订正框与 `jstm_battle_fields.md`）：
>   `(magic_bid:i32, change_hp:i32, **duration:u8**, per:i16, val:i16, **fold:u8**)` —— `duration`=**剩余回合**、`fold`=**层数**、`change_hp`=**每回合HP变化**；
> - 技能状态另有 `skills[] = (bid:u32, step:u8, last_use:u16, cd:u16)` 与专用的 `SC_20012.cooldown[] = (bid:u32, last_use:u16)`。
>
> ⇒ **结论改判**：CXEngine 才是"buff 不上线"的**较弱**一方；**JSTM 的 buff 逐条带剩余回合/层数/每回合HP变化上线，明显更强**。
> **本条的定性不是"JSTM 必须新增缓冲字段"，而是"JSTM 已有 `magic_list` 契约，服务端照它填充即可"。**
> **唯一仍未解出的是 `magic_list` 的"全量重列 vs 仅变化项"**（`jstm_battle_fields.md` §8）。
> 另有 `Dsc20012magic_play`/`Dsc20012summon_play`/`Dsc20013magic_list` 三个子结构的字段名与顺序**尚未解出**
> （`battle_protocol_matrix.md` §6 自述待展开）。**在这三项解出之前，不得断言 buff 走哪个字段。**
>
> **仍然成立的教训**：⛔ 不要采用"客户端重放判定"来同步状态 —— 这一点对任何回合制服务端都成立。

### 2.5 ❌ 与《梦幻西游》强绑定的内容（一律不可复用）

| 资产 | 内容 | 判定 |
|---|---|---|
| `assets/tables/school.tsv` | 15 门派（大唐官府/方寸山/…）| ❌ JSTM《绝世唐门》职业体系不同 |
| `assets/tables/skill.tsv`（300+ 行）| 技能名/动画/连击数（`DF_判官令`、`DT_横扫千军`…）| ❌ 数值与名称均属梦幻西游 |
| `assets/tables/buff.tsv` | buff 名/动画（`方寸山_催眠符`…）| ❌ |
| `assets/tables/level.tsv` | 0→175 级经验表（`role_exp`/`pet_exp`）| ❌ 本工作区 `analysis/1.4.9/level/exp_table.md` 已有 JSTM 自己的表 |
| `scripts/share/actor_metatable.lua` 的全部 `formula_*` / `CalcSchoolSkill*` | 梦幻西游公开数值公式（文件内自带百度知道/GameRes 出处链接）| ❌ **结构可借、数值不可借** |
| `scripts/share/enums.lua` | `RACE_HUMAN/SPIRIT/DEVIL`、`SCHOOL_DT..SM` | ❌ |
| `assets/tables/wasee_pal/*.wpal`（121 个）+ `utils.lua:decode_mypal()` | 梦幻西游调色板二进制格式（染色/变异）| ❌ 格式与资源都不通用 |
| `assets/doc/combat.md` / `roadmap.md` 中的大段表格 | 师门技能花费、暗器伤害、掉落清单、NPC 坐标、传送圈坐标 | ❌ 纯梦幻西游攻略数据 |
| `scripts/generator/table_template.lua` | 解析梦幻 WDF `.ini` → `avatar_*.tsv` | ❌ 梦幻专属资源命名法 |
| `scripts/combat/client/combat_system.lua` 的 `calc_combat_self_pos/enemy_pos` | 梦幻 640×480 战斗站位硬编码 | ❌ |

### 2.6 ❌ 工程质量反面清单（别照抄的"实现"）

| 项 | 事实 | 出处 |
|---|---|---|
| `GameServer::Stop()` | `m_Thread` 从未赋值却 `m_Thread->join()` ⇒ UB；且 `main` 里 `script_system_deinit()` 不可达 | `server/src/server.cpp:245`、`server.h:30` |
| `GameServer::OnClose()` | 调用**全仓库未定义**的 Lua `save_player_database` | `server/src/server.cpp:255` |
| `new GameSession` | 只 close socket，从不 delete ⇒ 连接对象泄漏 | `server/src/server.cpp` |
| `BaseGameEntity::HandleMessage` / `Actor::HandleMessage` | 全项目 `return false` ⇒ `MessageDispatcher` 整条消息系统是**死代码** | `common/src/message.h`、`actor.h` |
| `GameEntityManager` | `RegisterEntity` 从未被调用 ⇒ `GetEntityByID` 永远返回空 | `common/src/entity.h` |
| `StateMachine::ChangeState` | 先 `m_pPreviousState->Exit()` 再判空 ⇒ 首次切换即 null 解引用 | `common/src/state.h` |
| `ActorProp::operator=(int)` | 析构写的是 `s.~basic_string()`（应为 `~CXString()`）| `common/src/actor/actor_prop.cpp` |
| `actor_reg_prop` VEC2 分支 | 缺 `break` | `common/src/actor/actor_prop.cpp` |
| `ActorMT:ModifyMP` | 用 `GetMaxHP()` 夹取 MP | `scripts/share/actor_metatable.lua` |
| `ActorMT:AddSummon` | 无条件 `uids_str = '[]'` ⇒ **永远只能有 1 只召唤兽** | `scripts/server/actor_system.lua` |
| `BattleMT:GetNotReadyActors` | 引用 nil 全局 `actor` | `scripts/combat/combat_system.lua` |
| `combat_system_remove_battle(battle_id)` | 函数体用 nil 全局 `battle.id`；且无调用点 | `scripts/combat/server/combat_system.lua` |
| `get_attack_damage` 调用点 | `GetAttackDamage(target, false, false, 0, 1)` 把暴击/连击写死 ⇒ **公式支持但从未生效** | `scripts/combat/skill.lua` |
| `on_using_flee_skill` | `math.random(1,10) <= 5 or true` ⇒ **逃跑恒成功**（调试残留）| `scripts/combat/skill.lua` |
| `stub[PTO_C2S_COMBAT_PVP_START]` | **空函数**（PVP 真实入口是 `PTO_C2S_COMBAT_START`）| `scripts/combat/server/combat_system.lua` |
| `utils_next_uid(ns)` | `os.time()%0xFFFFFFFF` 起、内存自增、**不持久化** ⇒ 同秒重启可能重号 | `scripts/share/utils.lua` |
| `vfs.lua` vs `utils.lua` | `IsServer()/IsClient()` **重复定义**（前者看 `SIMPLE_SERVER`，后者调 `process_is_server()`）| 两个文件 |
| `combat_context.lua` | `BTTALE_TURN_EXECUTE`、`COMMAND_STATE_PALY` 拼写错误；`COMMAND_STATE_*`/`COMMAND_TYPE_*` 定义了但无人使用 | `scripts/combat/combat_context.lua` |
| 阶段未完成 | `assets/doc/roadmap.md` 自己把"战斗逻辑挪到服务端"列为**待办**；实测服务端确实只做指令结算，客户端做表现与推进 | `assets/doc/roadmap.md` |

---

## 3. ★ 对 JSTM 的建议（三）：无 LICENSE ⇒ 只借鉴设计，绝不复制代码

### 3.1 事实认定【已确认】

| 项 | 实测结果 |
|---|---|
| CXEngine ZIP 内 `LICENSE*` / `COPYING*` / `NOTICE*` | **0 命中** |
| `readme.md` 的许可声明 | **无**（只有网盘链接、构建说明、QQ 群 983630090、以及"未来会转移到 Unity（CXEngineUnity）"的通知） |
| `.gitmodules` 的 16 个子模块 | 全为 `github.com/oceancx/*` 的第三方库 fork（`cxlua`/`asio`/`NESupport`/`nlohmann`/`imgui`/`nanovg`/`ejoy2d`/`luadbg`/`glm`/`glfw`/`freetype`/`glew-cmake`/`lua-cmake`/`luacjson-cmake`/`miniaudio-cmake`/`gsm-cmake`）+ `lua-bind` 等 —— **不构成对项目自身代码的授权** |
| 与既有审计的一致性 | 本工作区 `analysis/server_reference/license_audit.md` 对 CXEngine 的判定为「⚠️ 未声明许可 ⇒ 只可借鉴设计」，**本次独立复核结论相同** |

### 3.2 强制规则

| 允许 ✅ | 禁止 ⛔ |
|---|---|
| 阅读全部源码与文档 | 复制任何 `.lua` / `.cpp` / `.h` / `.inl` 文件进 JSTM |
| 借鉴**架构、分层、命名约定、流程、数据模型形态** | 逐行翻译/改写 CXEngine 的函数体（含变量名、注释） |
| 借鉴"表驱动 + 代码生成"这类**工程方法** | 复制 `actor_template.tsv` / `skill.tsv` / `buff.tsv` / `level.tsv` 的表数据 |
| 引用其公开文档（`readme.md`/`assets/doc/*.md`）说明设计来源 | 把 `assets/doc/*.md` 的梦幻西游数值表（经验/公式/坐标/掉落）搬进 JSTM 文档当作 JSTM 的数据 |
| 在 JSTM 文档中注明"该设计参考自 CXEngine" | 声称这些代码/设计是 JSTM 自研 |
| 用 JSTM 自己的语言与协议**重新实现** | 因"只是 JSON/只是 4 字节头"而认为协议实现"没有版权" —— **实现细节同样受著作权保护** |

### 3.3 登记表（示例：本次审计认定的 12 条借鉴点全部登记为"只借设计、不进代码"）

| 来源项目 | 来源路径 | LICENSE | 借鉴内容 | 是否复制代码 | 是否进入 JSTM |
|---|---|---|---|---|---|
| CXEngine | `assets/tables/actor_template.tsv` + `scripts/generator/actor_template.lua` | **无** | 「表单一真源 → 生成多端定义」管线（§1.①） | 否 | 仅落地为 JSTM 自己的 `proto_defs.py` 生成器 |
| CXEngine | `scripts/server/main.lua` + `server.lua` | **无** | 「协议号→handler 表」+ 两阶段收包（§1.②） | 否 | 落地为 JSTM `HANDLERS` 注册表 |
| CXEngine | `common/src/script_system.cpp` + `scripts/combat/combat_system.lua` | **无** | 「原语/逻辑分层 + `IsServer` 同码分叉」（§1.③） | 否 | 仅借"服务端算、客户端播"的职责切分 |
| CXEngine | `scripts/combat/skill/26.lua` | **无** | 「随机数只在服务端摇、结果下发」（§1.④） | 否 | 落地为 JSTM `SC_20012` 字段设计原则 |
| CXEngine | `scripts/combat/skill.lua` + `buff.lua` | **无** | 「静态表 + 按 ID 命名脚本回调」（§1.⑤） | 否 | 落地为 `jstm/skills/<id>.py` 回调机制 |
| CXEngine | `scripts/combat/combat_context.lua` | **无** | 战斗常量集中（§1.⑥） | 否 | 落地为 `jstm/battle/constants.py` |
| CXEngine | `scripts/combat/server/combat_system.lua` | **无** | 速度定序、快照收件人、按战斗范围发送（§1.⑦⑧⑨） | 否 | 落地为 JSTM 回合调度与 AOI 雏形 |
| CXEngine | `common/src/time/timer_manager.cpp` | **无** | 具名定时器 + 回调持有（§1.⑩） | 否 | 落地为 JSTM 具名调度器 |
| CXEngine | `common/src/file_loading.cpp` | **无** | 异步加载任务表（§1.⑪） | 否 | 落地为 JSTM 表加载器 |
| CXEngine | `assets/doc/LuaAPI.md` + `scripts/examples/*.lua` | **无** | 「可执行文档 + 能力清单」（§1.⑫） | 否 | 落地为 JSTM `native_api.md` + pytest 夹具 |
| CXEngine | 全部战斗源码 | **无** | **反例**：回合推进所有权、buff 同步、安全模型（§2.1/2.3/2.4） | 否 | **作为"明确不做"的清单** |
| CXEngine | `assets/tables/{school,skill,buff,level}.tsv` 等 | **无** | **内容不借**（属《梦幻西游》） | 否 | 不进入 JSTM |

### 3.4 若将来确需复用代码

必须先补齐授权：① 联系作者（`github.com/oceancx`，README 给了 QQ 群 983630090）取得书面许可；
② 在 `server_reference/license_audit.md` 的登记表中登记「来源文件 / LICENSE / 是否可再发布 / 是否进入 JSTM」；
③ 记录许可文本与范围。**在拿到许可之前，任何形式的代码搬运（包括"改写 70%"）都不做。**

---

## 4. 汇总：Top 3 最值得借鉴（一句话版）

| 排名 | 借鉴点 | 具体落地 |
|---|---|---|
| **1** | **内容/协议的单一真源 + 代码生成**（`actor_template.tsv → actor_enum.h`；`enums_protocol.lua → protocol.h`）| 以 JSTM 的 `protocol/fields.json` 为唯一真源，生成 `jstm/proto_defs.py`，供 mock_server / 测试 / 抓包解码器共用，并在 CI 校验生成物一致 |
| **2** | **「协议号 → handler 表」+ 两阶段收包**（`stub[PTO_*]`；握手期立即答 + 主循环统一派发）| 把 `mock_server.py` 的 `if cmd == …` 长链改为 `HANDLERS[cmd]` 注册表，登录/握手走快路径 |
| **3** | **「服务端算结果、客户端只播表现」的权威原则**（`skill/26.lua` 的随机数只在服务端；伤害以 `hp_deltas`/`life_state` 下发）| JSTM 的 `SC_20013`「**已经**是服务端算好逐条下发」（`hit:int8`/`hp`/`hp_max`/`is_target_die`）⇒ **不需要新增任何字段**。<br>**且 buff 也已逐条上线**（本轮已解出，见 `jstm_battle_fields.md`）：`magic_list[] = (magic_bid:i32, change_hp:i32, **duration:u8**, per:i16, val:i16, **fold:u8**)`，`duration` = **剩余回合**、`fold` = **层数**、`change_hp` = **每回合HP变化**。<br>⇒ **对 JSTM 的动作只有两条**：① **不让客户端参与判定**（`10601`/`10610` 的本地演算只作校验）；② **不让客户端推进回合**（真机客户端连 `CS_20014` 都不发）。<br>⛔ **不要**把 CXEngine 的"客户端本地 `NextTurn()`"和"buff 完全不上线 + 客户端重放判定"搬过来——CXEngine 在这两点上都是**弱的一方**。<br>（本行经**两次**订正：第一版写"JSTM 必须携带 buff 增/减/剩余回合 + 保留 `CS_20014` 驱动"；第二版误以为 buff 载体是 `specials`。**最终以 `magic_list` 为准**，详见 §1.④ 的两个订正框与 `jstm_battle_fields.md`）|

---

## 5. 本文的边界与未读到

- 【未读到】`internals/cxlua`（`lua_bind.h`、`cxlua.h`、`cxezio/*`、`net_thread_queue.h`、`lua_net.h`）、
  `internals/NESupport`（`NESupport.h`）、`externals/*` —— 均不在 ZIP 内（`.gitmodules` 子模块）⇒ 相关结论标【待验证】。
- 【未读到】`common/src/actor/action.cpp`（21 KB）、`client/src/**` 的渲染/资源层、
  `scripts/client/actor_metatable.lua`、`scripts/client/addon/{bag,props,options,quest}.lua`、
  `scripts/generator/{table_template,parser_keys,sound_tsv_parser,imgui_binding_generator}.lua`（仅片段）。
- 【未知】`PTO_*` 协议号的**实际数值**（生成物 `protocol.h` 未入库，`enum_reset()` C 实现不在 ZIP）。
- 【待验证】入库的 `actor_enum.h` 与 `actor_template.tsv` 是否严格一致（前者末尾疑为手工增补）。
- 【未读到】JSTM 侧 `SC_20013 round_start` / `SC_20012` 的完整字段定义（不在本任务范围；见
  `analysis/1.4.9/battle/battle_protocol_matrix.md` 与 `analysis/jstm_1.4.9/battle_protocol.md`）。
