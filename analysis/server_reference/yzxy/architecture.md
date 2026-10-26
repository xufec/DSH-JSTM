# CXEngine（= YZXY / 原罪西游）架构审计

> **审计对象**：`C:\Users\xu\Desktop\DSH\cankao\CXEngine-master.zip`（14.8 MB，501 条目）
> **身份**：用户已确认本项目 = 任务书第 2 项「YZXY / 原罪西游」。
> **方法**：Python `zipfile` 按需读取全部 `scripts/**`、`server/**`、`common/src/**`（关键文件）、
> `client/src/**`（关键文件）、`assets/tables/*.tsv`、`assets/doc/*.md`。**未解压、未修改任何文件。**
> **标注**：【已确认】= 直接读到代码/数据；【待验证】= 有代码线索但缺关键依赖（如 `internals/cxlua` 不在 ZIP 内）；【未知】= 未读到。
> **不猜原则**：未读到的写「未读到」，不把推断写成已确认。

---

## 0. ★ 首要提示：与任务书前提的一处冲突（必须先看）

任务书要求「特别注意：YZXY 是**回合制** MMORPG ⇒ 回合制战斗状态机**不能**套用到 JSTM 的**动作/实时战斗**」。

本次审计对 CXEngine 侧的判定【已确认】：**CXEngine 的战斗确实是回合制**（见 `battle.md`）。

但对 JSTM 侧，本工作区**已有的字节码取证结论与任务书前提相反**：

| 来源 | 原文结论 | 标注 |
|---|---|---|
| `analysis/1.4.9/battle/battle_flow.md`（第 1 节） | 「**1.4.9 使用「独立回合制战斗场景」，不是地图直接战斗。**」 | 该文自述「结论不来自现代游戏经验，只来自 APK 字节码与协议」 |
| 同上 §三 协议链 | `CS_20002` 发起 → `SC_20010` 进战斗 → `SC_20012/20013` 小回合/回合开始 → `SC_20020` 结果 | 同上 |
| `analysis/1.4.9/battle/battle_protocol_matrix.md` | `20001–20030` 是**真正的战斗协议段**（§3.1 订正：`11000/11200` 段**不是**战斗）| 该文由 `cmd_resolve_200.luac` 反汇编直读 |
| `analysis/jstm_1.4.9/protocol_index.md` | 存在 `20000~20099` 段 25 条命令 | 【已确认】 |

> ### ⚠️ 本表第一版有一处引用错误，已订正
> 第一版我写「协议链 … → **`CS_20014` 播完回执** → `SC_20020` 结果」，引自 `battle_chain_verified.md`。
> 该回执**在真机上不存在**：`battle_protocol_matrix.md` §3.0/§3.1 的真机订正记载
> **客户端 `CS_20011`（加载完成）/ `CS_20014`（动画播放完成）在整场战斗中「从未发出」**
> （`tcp.log` 无 `cmd=20011` / `cmd=20014`）⇒ 原文结论「整场战斗会停在第一回合之前，**除非服务端自己推进**」，
> 现阶段做法是**服务端自己按节拍推进（2.5 秒/回合，自续期）**。
> 第一版引用的 `battle_chain_verified.md` 描述的是**我们自己 `mock_server.py` 的实现**（`行 2445 if cmd == 20014:`），
> **不能当作真机客户端行为**。
> **对本节结论无影响**（"JSTM 是回合制"这一判定不依赖 20014），但**影响 `reuse_candidates.md` §2.1 的论证**：
> 该处原以"回合节奏所有权相反"为据，现已改为 **5 条 JSTM 字段级证据**
> （详见 `battle.md` §5.2 与 `reuse_candidates.md` §2.1(b) 的订正框）。

⇒ **结论**：JSTM 1.4.9 的战斗**也是回合制**，而不是动作/实时战斗。
任务书里的「JSTM 的动作/实时战斗」这一前提**与本工作区既有取证不一致**，本报告按实测事实记录，
并把「为什么仍然不能照搬 CXEngine 回合制状态机」的原因**换成真正的技术原因**
（**5 条 JSTM 字段级证据**，见 `reuse_candidates.md` §2.1(b)；⚠️ 该处第一版曾用"回合节奏所有权相反"，
已因真机 `CS_20014` 从未发出而订正）。
**此冲突需要上游确认**：若 JSTM 的「实时/动作」指地图层（`10212/10213` 怪物在场景内实时移动、带 `x/y/dir`，
见 `analysis/1.4.9/battle/battle_flow.md` 2.1 节），则该前提只在地图层成立，战斗层不成立。

---

## 1. 仓库全景（实测）

| 目录 | 角色 | 实测内容 |
|---|---|---|
| `common/src/` | **CXEngine 与 CXServer 共享**的 C++ | `actor/`（actor, actor_prop, actor_manager, actor_enum, action, actor_event）、`script_system.{h,cpp,inl}`、`protocol.{h,cpp}`、`entity.h`、`message.{h,cpp}`、`state.h`、`file_system`、`file_loading`、`logger`、`profile`、`time/{time,timer,timer_manager}`、`astar/`、`imgui/` |
| `client/src/` | 仅客户端 C++ | `window.cpp`、`game.cpp`、`net.cpp`、`input_manager`、`resource_manager`、`scene/{base_scene,game_map,scene_manager}`、`animation/sprite`、`sprite_renderer`、`sprite_batch`、`text_renderer`、`graphics/{bitmap,shader,texture,ui_renderer}`、`audio/audio_manager`、`actor/move`、`math/vector`、`ui`、`camera` |
| `server/src/` | 仅服务端 C++ | **实测 5 个源文件**：`main.cpp`、`server.h`、`server.cpp`、`pch/precompile.h`、`pch/precompile.cpp`（任务书说的「7 文件」应含 `server/CMakeLists.txt` 与 `server/.gitignore`） |
| `cxluax/src/` | **launcher**（登录器/GM 工具） | `main.cpp`、`window.cpp`、`net.cpp`、`lua_ezio_net.cpp`、`coordinate.cpp` |
| `scripts/share/` | launcher/客户端/服务端**三方共享** Lua | `enums.lua`、`enums_protocol.lua`、`vfs.lua`、`utils.lua`、`content_system.lua`、`actor_metatable.lua`(36 KB) |
| `scripts/server/` | 服务端 Lua | `main.lua`、`server.lua`、`actor_system.lua`、`scene_system.lua`、`team_system.lua`、`gm.lua` |
| `scripts/combat/` | 战斗（**客户端+服务端共享 + 各自分叉**） | `combat_context.lua`、`combat_system.lua`（共享基类）、`server/combat_system.lua`、`client/combat_system.lua`、`client/skill.lua`、`skill.lua`(24 KB)、`buff.lua`、`skill/<id>.lua`、`buff/<id>.lua` |
| `scripts/client/` | 客户端 Lua | `main.lua`、`net_manager.lua`、`actor_manager.lua`、`actor_metatable.lua`、`scene_manager.lua`、`event_system.lua`、`addon_manager.lua`、`addon/*`（bag/props/battle/quest/options/action/hud）、`module/*`（team/dialog/summon） |
| `scripts/generator/` | **Lua 写 Lua/C++ 代码生成器** | `protocol.lua`（写 `common/src/protocol.{h,cpp}`）、`actor_template.lua`（写 `common/src/actor/actor_enum.{h,cpp}`）、`table_template.lua`(20 KB，资源 INI→TSV)、`parser_keys.lua`、`imgui_binding_generator.lua`(41 KB)、`sound_tsv_parser.lua`、`parser.lua` |
| `scripts/examples/` | 示例/教程 | `example00..07.lua`、`extract.lua`、`math.lua`、`_debugger.lua` |
| `scripts/launcher/` | 登录器 Lua | `main.lua`、`window.lua`(15 KB)、`summon_handle.lua` |
| `assets/tables/` | **游戏内容全部由表驱动** | 35 个 `.tsv`（actor_template / skill / buff / school / scene / npc / equip / level / summon_quality / avatar_* / sound_* / scene_monster / transport / magic / map / smap …）+ `ini/`（WDF 资源索引）+ `second/` + `wasee_pal/`（121 个 `.wpal` 调色板） |
| `assets/storage/` | **存档（明文 JSON）** | `account.data`、`actor.data` |
| `assets/doc/` | 设计文档 | `combat.md`、`server.md`、`roadmap.md`、`LuaAPI.md`、`Unity移植计划.md`、`lua函数参考手册.md` |
| `externals/`、`internals/` | 子模块（**不在 ZIP 内**） | `.gitmodules` 列 16 个 oceancx fork：`cxlua`、`asio`、`NESupport`、`nlohmann`、`imgui`、`lua-cmake`、`luacjson-cmake`、`miniaudio-cmake`、`nanovg`、`ejoy2d`、`luadbg`、`gsm-cmake`、`glm`、`glew-cmake`、`freetype`、`glfw` |

**构建**：CMake 单工程产出 3 个可执行文件 —— `CXEngine.exe`（客户端）、`CXServer.exe`（服务端）、`cxluax.exe`（launcher）。
`common/src/script_system.cpp` 用 `-DSIMPLE_ENGINE` / `-DSIMPLE_SERVER` / `-DCXLUAX` 三组宏在同一份 C++ 里切角色。

**Lua 版本**：【已确认】标准 **Lua 5.3+**，不是 LuaJIT。
证据：`scripts/share/content_system.lua` 用 `(pack<<32)|wasid`（位运算）、`math.tointeger`；
`utils.lua` 用 `string.unpack`、`table.pack/unpack`；`main.lua` 用 `load(chunk,'@'..path,'bt',module)` 的 `'bt'` 模式。
⇒ **与 JSTM（LuaJIT 2.0 字节码）不同**，CXEngine 的 Lua 逻辑**不能以字节码形式**在 JSTM 客户端复用。

---

## 2. 任务书 8 问 —— 逐条核心答案

> 详细表格见同目录 `lua_server.md`（Q1/Q2/Q3）、`protocol.md`（Q4）、`role.md`（Q5）、`battle.md`（Q6/Q7/Q8）。

### Q1. C++ 与 Lua 怎么交互？
**机制**：【已确认】C++ 创建单个 `lua_State`，按固定清单 `luaopen_*` 把 C 函数以**全局名**注册进 Lua；
之后 C++ 每帧/每事件用 `lua_getglobal + lua_push… + lua_pcall` 回调 Lua 全局函数；
Lua 侧通过 `lua_CFunction` 包装直接调 C（`actor:SetProperty` → `actor_set_prop`）；
自定义类型用 **userdata + metatable**（`mt_actor`、`MT_ANIMATION`、`MT_NET_THREAD_QUEUE`、`mt_buffer` …）；
枚举用 `lua_pushinteger + lua_setglobal` 变成 Lua 全局常量。
**要点**：**全局符号双向绑定，无命名空间、无接口表、无异常边界** —— 拼错一个全局函数名不会在编译期被拦截。

### Q2. Server 主循环怎么组织？
**机制**：【已确认】**单线程 asio `io_context` 事件循环**。
`main.cpp` → `script_system_prepare_init()`（建 Lua 状态）→ `script_system_run_main_script()`（跑 `scripts/server/main.lua`）
→ `script_system_init()`（调 Lua `on_script_system_init`）→ `game_server_start(45000)`（**阻塞不返回**）。
`GameServer::Start()` 里 `DoAccept()`（异步 accept 递归）+ `main_game_update()`（16 ms `basic_waitable_timer` 自重排）
+ `_IOContext.run()`。**每个 16 ms tick 调 Lua `on_script_system_update()`**，它串行执行
`game_server_update()`（排空收包队列并派发）→ `scene_system_update()` → `combat_system_update()` → 脏属性广播。
**缺陷**：【已确认】`m_Thread` 在服务端从未赋值，`Stop()` 里 `m_Thread->join()` 是 UB；且 `main` 里 `script_system_deinit()` 不可达。

### Q3. Lua 如何实现游戏逻辑？
**机制**：【已确认】**一切游戏逻辑都是 Lua**，C++ 只提供引擎原语（buffer/actor/动画/timer/fs）。
`scripts/server/main.lua` 按序 `script_system_dofile` 加载 share + 各 system，然后**把每条协议的处理函数注册进全局表 `stub[PTO_XXX]`**；
`stub` 被 `server_thread_on_message`（网络线程/收包回调）与 `game_server_dispatch_message`（主 tick）两个入口派发。
系统模块统一 `xxx_init / xxx_update / xxx_stop` 命名约定；`server_reload()` 支持热重载。
**风险**：`stub[PTO_C2S_DOSTRING]/PLAYER_DOSTRING/ACTOR_DOSTRING` 是**服务端远程执行客户端 Lua 代码**的后门（见 `reuse_candidates.md`）。

### Q4. 协议如何定义？
**机制**：【已确认】**Lua 是协议 ID 的唯一真源，C++ 头文件由 Lua 生成**。
`scripts/share/enums_protocol.lua` 用 `PTO_XXX = enum_reset()/enum_next()`（C 提供的自增枚举）列出全部 63 条协议，
并建 `proto_to_name` 映射供日志用；`scripts/generator/protocol.lua` 读它、按值排序、**写出 `common/src/protocol.h`（`enum EProtocalType`）与 `protocol.cpp`（`REG_ENUM` → `lua_setglobal`）**。
**线格式**：`[int32 len][int32 proto][JSON(UTF-8) payload]`，**无字段 schema、无版本、无校验、无加密**。
⇒ 与 JSTM 的 `AutoConstruct('sc', cmd, {'code__C','msg__s'})` 字段规格体系是**两种完全不同的协议哲学**。

### Q5. 角色数据如何组织？
**机制**：【已确认】**TSV 定义属性表 → Lua 生成 C++ 枚举 → 运行时 Lua 注册默认值进 C++ 变体数组**。
`assets/tables/actor_template.tsv` 每行 `name/type/def/sync`；
`scripts/generator/actor_template.lua` 由它生成 `common/src/actor/actor_enum.h`（`EActorProp`，约 118 项 + `PROP_COUNT`）；
`Actor` 构造时回调 Lua `actor_on_reg_props`，读同一张 TSV 逐项 `actor:RegProperty(i-1, type, default)`。
存储是 `std::vector<ActorProp>`，索引即 `PROP_*`；`ActorProp` 是 `type` 标签 + `union{bool,float,int,CXString,uint64,float[2]}`。
同步控制由 TSV 第 4 列 `sync` 决定（`is_prop_sync()`）。
持久化：`assets/storage/actor.data` = `cjson` 编码的 `GetProperties()`（**0 基索引 → JSON 对象键 "0".."N"**）。

### Q6. 技能如何组织？
**机制**：【已确认】**表 + 按 ID 命名的 Lua 脚本回调**。
`assets/tables/skill.tsv`（ID/name/sound/type/sub_type/school/combo/atk_anim/group_kill/cast_anim/act_turn）
给出技能静态数据；`scripts/combat/skill/<id>.lua` 用 `SkillOnStart/SkillOnHit/SkillOnEnd` 提供**逐技能特化逻辑**，
`init_skills()` 在启动时 `load(chunk,'@'..path,'bt',sandbox)` 把回调挂到技能模板行上。
服务端权威计算（`base_using_skill`：选目标 → 按 combo 逐次结算 → 产出 `cskill`），
客户端只做**动画重放**（`skill_cast_atk` / `skill_cast_spell` / `skill_cast_flee`）。
技能 ID 有硬编码约定：`1`=普攻、`264`=防御、`268`=逃跑。

### Q7. 战斗状态如何组织？
**机制**：【已确认】**回合制有限状态机 + `__battles__` 全局表**。
状态常量集中在 `scripts/combat/combat_context.lua`：
`BATTLE_DEFAULT(0)→PREPARE(1)→START(2)→TURN_STAND_BY(3)→TURN_EXECUTE(4)→TURN_NEXT(5)→END(6)`。
`BattleMT`（`scripts/combat/combat_system.lua`，**共享基类**）持有 `{id, actors[], cmds[], state, turn, type}`；
`if IsServer()` 走 `scripts/combat/server/combat_system.lua`（真正算伤害），
`if IsClient()` 走 `scripts/combat/client/combat_system.lua`（只播动画）。
回合流程：STAND_BY 收集所有 `cmd{master,target,skill_id}` → **按 `CalcSpeed()` 降序排序** → `handle_turn_commands` 逐条结算 →
打包 `all_skills` 下发 → 客户端播完后**本地 `NextTurn()`**（**无客户端 ACK**）。
Buff 体系独立（`buff.lua` + `buff/<id>.lua`），在 `NextTurn` 时由 `process_turn_buffs` 统一扣回合。

### Q8. 服务端与客户端如何同步？
**机制**：【已确认】**全量广播 + 脏属性增量 + 客户端确定性重放，无 AOI、无帧同步、无快照插值**。
- 登录：`PTO_C2C_LOGIN`（网络回调里校验账号）→ 主 tick 的 `stub[PTO_C2C_LOGIN]` 建角色、
  给本人发 `PTO_C2C_PLAYER_ENTER{local_pid, actors=全部玩家属性}`、给他人发 `{actors={新玩家}}`、
  再发 `PTO_C2C_ACTOR_ENTER{npcs=[...]}`。
- 移动/聊天：`PTO_C2C_MOVE_TO_POS` / `PTO_C2C_CHAT` 由服务端 **`net_send_message_to_all_players` 全服广播**（客户端靠 `IsLocal()` 忽略自己）。
- 属性：每 tick 遍历玩家与其召唤兽，`IsDirty()` + TSV `sync` 列过滤，发 `PTO_S2C_SYNC_PROPS` = `[[pid,prop_id,value],…]` **广播给所有人**。
- 战斗：`PTO_S2C_COMBAT_CREATE/START` 带 `battle:Serialize()` 全量战场；`PTO_S2C_COMBAT_EXECUTE` 带**已算好的技能效果数组**（`hp_deltas`、`life_state`），
  客户端照数据播动画。回程只有 `PTO_C2S_COMBAT_END_BATTLE`。
- 存档：`PTO_C2C_SAVE_ACTORS` / `PTO_C2C_SAVE_ACCOUNT_DATABASE` 由**客户端触发**服务端写 JSON 文件。
- **安全缺陷**：处理函数普遍用**请求体里的 `req.pid`** 决定收件人（`net_send_message(req.pid, …)`），
  而**从不校验该 pid 是否属于当前连接** ⇒ 任意客户端可冒充他人 pid 领取他人回包。

---

## 3. 全局逐文件表（架构级）

> 判定列：✅ 适合借鉴 / ⚠️ 只能借鉴局部 / ❌ 不适合 / ⛔ 必须排除（安全问题或死路）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `CMakeLists.txt` | `CXEngineAll` | 单工程产出 client/server/launcher 三个 exe；`common/` 代码双端复用 | ⚠️ | **思路**（共享核心 + 双端壳）可借鉴；CMake/VS2017 + cotire 预编译头与 JSTM 的 Python 模拟器技术栈完全不搭 |
| `server/CMakeLists.txt` | `CXServer` | `-DSIMPLE_SERVER` 开关 + cotire PCH | ⚠️ | 宏切角色的做法可借鉴；构建系统本身不可迁移 |
| `common/src/script_system.cpp` | `script_system_prepare_init()` | 建 `lua_State` → 固定清单 `luaopen_*` → 装载 `script_system_lua_code` → 加载 `cxluadbg.dll` | ✅ | **「C++ 提供原语、Lua 写逻辑」的分层**正是 JSTM 模拟器最需要的骨架；但 `luaL_newstate` 是纯 Lua，JSTM 客户端是 LuaJIT，两端不可共享字节码 |
| `common/src/script_system.cpp` | `script_system_run_main_script()` | 按 `--luapath` 参数 `luaL_dofile` 入口脚本（默认 `main.lua`） | ✅ | 入口可配置 + 同一份 C++ 跑不同 `.lua` 入口（client/server/launcher/examples）→ JSTM 的 mock 服务端也可以用「同进程多入口」做工具链 |
| `common/src/script_system.cpp` | `script_system_init/update/deinit()` | 调用 Lua 全局 `on_script_system_init/update/deinit`；`update` 返回 bool | ✅ | **生命周期钩子约定**极简清晰，值得照抄命名风格（init/update/deinit 三段） |
| `common/src/script_system.cpp` | `process_is_server()` | `#ifdef SIMPLE_SERVER` 暴露给 Lua `IsServer()/IsClient()` | ✅ | **同一份 Lua 代码用 `IsServer()` 分叉**，一个文件同时承载服务端算法与客户端表现 —— 对 JSTM 单进程模拟器（同进程既做 server 又做 client 夹具）非常实用 |
| `common/src/script_system.inl` | `script_system_lua_code` / `script_system_dofile()` | 把 `script_system_dofile` 以裸字符串内嵌进 C++，用 `loadfile(path,'bt',env)` 实现相对路径加载 + 可注入 env | ✅ | **相对路径 dofile + 可注入沙箱 env** 是技能/剧本脚本加载的基础设施，值得借鉴（比 `require` 更适合热重载） |
| `common/src/protocol.h` / `.cpp` | `luaopen_protocol()`, `CX_MSG_HEADER_LEN` | 目前入库的是**手写桩**，只注册 `CX_MSG_HEADER_LEN=4`；完整枚举由 generator 生成 | ⚠️ | 「协议 ID 常量暴露给 Lua」思路可用；但**生成的 `protocol.h` 没有入库**，实际数值只能在 `enums_protocol.lua` 侧推断 |
| `common/src/entity.h` | `BaseGameEntity`, `GameEntityManager` | 实体基类（id/name）+ 单例注册表 `map<id,entity*>` | ✅ | **实体 id 注册表 + `GetEntityByID`** 是消息分发的地基；但 `GameEntityManager` **实际上从未被 `RegisterEntity` 使用**（`Actor` 构造不注册）【已确认】⇒ 借鉴概念、不借鉴实现 |
| `common/src/message.h` / `.cpp` | `Telegram`, `MessageDispatcher::DispatchMessageX/DispatchDelayedMessage` | 延迟消息队列（`set<Telegram>` 按 DispatchTime 排序），`HandleMessage` 派发 | ⚠️ | **「延迟/定时消息」抽象**可借鉴用于 JSTM 的 buff 到期、技能 CD；但**`BaseGameEntity` 的 `HandleMessage` 全部 `return false`**（`Actor` 也返回 false），整条消息系统**在 CXEngine 里是死代码** 【已确认】⇒ 只是骨架，无可用实现 |
| `common/src/state.h` | `State<EntityType>`, `StateMachine<EntityType>` | 教科书式 FSM（Enter/Execute/Exit/OnMessage + Current/Previous/Global） | ✅ | **纯头文件、零依赖的 FSM 模板**是本项目质量最好的 C++ 之一；但 `ChangeState` 有 **null 解引用 bug**（先 `m_pPreviousState->Exit()` 再判空）【已确认】⇒ 借鉴接口形态，重写实现 |
| `common/src/file_loading.cpp` | `FileLoadingThread::PostTask/Run` | 单后台线程 + `condition_variable` + 任务状态缓存（Loading/Ok）异步加载资源 | ✅ | **「按路径去重的异步加载任务表 + 主线程轮询 `IsFileLoading/IsFileLoadOk`」** 值得 JSTM 借鉴（APK 资源解包/表加载很慢）；注意其去重键是路径字符串，无并发上限 |
| `common/src/time/timer_manager.cpp` | `TimerManager::Create/Remove/Pause/Forward`, `timer_manager_add_timer` | 按**字符串名**索引的定时器表；`m_GarbageContainer` 双缓冲延迟删除；Lua 回调用 `luaL_ref` 存引用 | ✅ | **按名取定时器**极适合游戏逻辑（`TimerWildBattle` 这类具名计时器），且**回调注册用 registry ref 避免 GC**；对 JSTM 的自动战斗/CD/刷新很有用 |
| `common/src/time/timer.cpp` / `time.cpp` | `Timer::Update`, 时间换算 | 单定时器实现（倒计时/正计时/循环/暂停） | ⚠️ | 逻辑简单可自研，不必借鉴 |
| `common/src/file_system.cpp` | `FileSystem::InitWorkPath/GetLuaPath` | 工作目录 + `--cwd` 参数解析；Lua 脚本路径解析 | ✅ | **命令行式工作目录**（`--cwd=`）让同一 exe 可服务任意资源目录 ⇒ 对 JSTM「切包对比」很实用 |
| `common/src/logger.cpp` | `cxlog_info/warn/error` | 上报到 Lua | ✅ | 让 Lua 统一收日志，便于做**协议抓包/回放日志**（JSTM 正在做的事） |
| `common/src/astar/` | `astar.cpp`, `heap.h` | A* 寻路 + 二叉堆 | ⚠️ | 服务端不用（服务端不寻路）；客户端用。JSTM 若做怪物 AI 巡逻可参考，但需与地图阻挡格式（`_config_map_block`）对齐，格式不同 |
| `scripts/share/vfs.lua` | `vfs_getpath/makepath/get_tsvpath/IsServer/IsClient` | 路径拼接集中化；`IsServer()` 由 `SIMPLE_SERVER` 全局判断 | ✅ | **路径逻辑集中在一处**避免各模块硬编码；注意本文件版本与 `utils.lua` 末尾的同名 `IsServer/IsClient` **定义冲突**（后者用 `process_is_server()`）【已确认】⇒ 借鉴集中化，慎用重复定义 |
| `assets/tables/*.tsv` | — | 35 张制表符表，`*` 行=默认值，第 1 行=列名 | ✅ | **TSV + 首行 schema + `*` 默认值行**的轻量配置格式清晰；JSTM 侧已是 `luac` 表，可考虑把关键表转成同构 TSV 便于人工校对 |
| `assets/tables/wasee_pal/*.wpal` (121) | `decode_mypal()`（`utils.lua`） | 解析 `wpal` 调色板二进制（segment 表 + 3×3 颜色矩阵）实现「变异/染色」 | ❌ | 这是**梦幻西游美术资源格式**；JSTM 是《绝世唐门》，调色/染色资源完全不同 ⇒ 不可复用（连格式都不通用） |
| `assets/storage/account.data`, `actor.data` | — | 明文 JSON 存档 | ❌ | **明文 JSON + 客户端可触发保存**是反面教材（见 `reuse_candidates.md`）；JSTM 用 sqlite（`_db_before_battle.db` 已存在） |
| `readme.md`、`assets/doc/combat.md`、`assets/doc/server.md` | — | 设计文档（回合流程 mermaid、buff/skill 设计、公式清单） | ✅ | **文档里有可直接用于需求比对的回合流程状态机与公式来源**（含「修炼公式 an=1.02^n(a+250)-250」等），对 JSTM 战斗数值校对有参考价值（数值本身属梦幻西游，不可直接搬） |

---

## 4. 质量与风险速览（全部【已确认】，逐条有代码出处）

| 项 | 事实 | 出处 |
|---|---|---|
| 服务端线程模型 | 单线程 io_context；`m_Thread` 从未赋值，`Stop()` 中 `m_Thread->join()` 为 UB | `server/src/server.h:30`, `server/src/server.cpp:245` |
| 关服回调 | `GameServer::OnClose()` 调 Lua `save_player_database`，但**该 Lua 函数全仓库未定义** | grep 全 ZIP：仅 `server/src/server.cpp:255` 出现 |
| 后门 | `PTO_C2S_DOSTRING` / `PLAYER_DOSTRING` / `ACTOR_DOSTRING` 直接在服务端 `load()` 客户端传来的 Lua 代码 | `scripts/server/main.lua` |
| 身份校验 | 处理函数用**请求体 `req.pid`** 决定回包对象，不校验连接↔pid 绑定 | `scripts/server/actor_system.lua`、`team_system.lua`、`combat/*` |
| 客户端权威 | `PTO_C2S_CREATE_PLAYER` 用客户端 JSON 整体 `SetProperties` | `scripts/server/actor_system.lua` |
| 明文协议 | JSON 文本 + 无签名/加密 | `scripts/server/main.lua` `cjson.decode` |
| 明文存档 | `assets/storage/*.data` = JSON | `scripts/server/server.lua`、`actor_system.lua` |
| UID 生成 | `os.time()%0xFFFFFFFF` 起始 + 内存自增，不持久化 | `scripts/share/utils.lua` `utils_next_uid` |
| 战斗代码 bug | `GetNotReadyActors` 用 nil 全局 `actor`；`combat_system_remove_battle` 用 nil `battle`；`ModifyMP` 用 `GetMaxHP()` 夹取；`on_using_flee_skill` 服务端逃跑判定 `… or true` 恒真 | `scripts/combat/combat_system.lua`、`scripts/combat/skill.lua`、`scripts/share/actor_metatable.lua` |
| 依赖缺失 | `lua_bind.h`、`cxlua`、`net_thread_queue.h`、`lua_net.h`、`cxezio/*`、`NESupport.h`、`define_types.h`、`utils.h`、`cxmath.h`、`singleton.h`、`tsv.h` 均在 `internals/`/`externals/`，**ZIP 内不存在** | `.gitmodules` + 头文件 include 列表 |

---

## 5. 未读到清单（明确边界）

| 未读到 | 影响 |
|---|---|
| `internals/cxlua`（`lua_bind.h`、`cxlua.h`、`cxezio/*`、`lua_net.h`、`net_thread_queue.h`） | `script_system_register_function`（包装普通 C 函数）与 `script_system_register_luac_function`（裸 `lua_CFunction`）的**精确实现**未知 ⇒ 已按其调用签名差异推断语义，标【待验证】 |
| `enum_reset()` / `enum_next()` 的 C 实现 | **协议 ID 的实际起始数值未知** ⇒ 无法给出 CXEngine 协议的数值表 |
| `internals/NESupport`（`NESupport.h`） | 梦幻 WDF/WAS 资源读取实现未读到 |
| `common/src/actor/action.cpp`（`ActionStateMachine`，21 KB，仅读到片段） | 客户端动作状态机内部细节未全读 |
| `scripts/client/actor_metatable.lua`、`addon/{bag,props,options,quest}.lua`、`generator/{table_template,parser_keys,sound_tsv_parser,imgui_binding_generator}.lua` | 仅读到片段/未读 ⇒ 相关结论标【未读到】 |
| `client/src/{window,game,scene/*,animation/sprite,text_renderer,resource_manager,graphics/*}.cpp`、`cxluax/src/lua_ezio_net.cpp` | 渲染/输入/资源层未逐文件读 ⇒ 本报告不对其下结论 |

---

## 6. 一句话总结

CXEngine = **「C++ 提供引擎原语 + Lua 承载全部游戏逻辑 + TSV 驱动全部内容 + Lua 生成 C++ 枚举」的回合制 MMO（梦幻西游题材）原型机**；
架构分层与代码生成思路**值得 JSTM 认真借鉴**，但**协议哲学（JSON 无 schema）、同步模型（全服广播 + 无 AOI + 无 ACK）、安全模型（明文 + `req.pid` + `dostring` 后门）、数值内容（梦幻西游）全部不可复用**；
且**无 LICENSE ⇒ 只可借鉴设计，禁止复制代码**。
