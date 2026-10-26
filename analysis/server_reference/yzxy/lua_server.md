# CXEngine（YZXY）C++/Lua 分工、主循环与 Lua 游戏逻辑组织

> 回答任务书 Q1（C++↔Lua 交互）、Q2（Server 主循环）、Q3（Lua 如何实现游戏逻辑）。
> 标注【已确认】/【待验证】/【未读到】；判定列 ✅ 适合借鉴 / ⚠️ 局部 / ❌ 不适合 / ⛔ 必须排除。

---

## 1. Q1：C++ 与 Lua 怎么交互

### 1.1 总体形态【已确认】

**单向控制流：C++ 是宿主，Lua 是被驱动方。** 没有协程、没有状态机桥、没有 async/await。

```
C++ main()
 └─ script_system_prepare_init()     建 lua_State + 注册全部 C 能力（一次性）
 └─ script_system_run_main_script()  luaL_dofile(--luapath，默认 main.lua)
 └─ script_system_init()             lua_pcall(on_script_system_init)
 └─ game_server_start(45000)         ← 进入 asio 事件循环，永不返回
      └─ 每 16 ms: script_system_update() → lua_pcall(on_script_system_update)
      └─ 每收一包: lua_pcall(server_thread_on_message, conn, buf, len, netq)
```

### 1.2 五种交互手法（逐条有代码出处）

| # | 手法 | C++ 侧 | Lua 侧 | 出处 |
|---|---|---|---|---|
| ① | **C 能力注册**（一次性） | `luaopen_actor(L)`、`luaopen_game_server(L)`、`luaopen_net(L)`、`luaopen_timer_manager(L)`、`luaopen_protocol(L)` … | 得到一堆**全局函数** | `common/src/script_system.cpp:script_system_prepare_init()` |
| ② | **常量/枚举注入** | `#define REG_ENUM(name, macro) (lua_pushinteger(L, macro), lua_setglobal(L, name))` | `PROP_HP`、`ACTOR_TYPE_PLAYER`、`PTO_*`、`ACTION_IDLE`、`DIR_NW`、`ADDONWDF`… 全是全局 | `script_system.cpp:luaopen_script_system()`、`actor_enum.cpp`、`protocol.cpp`、`resource_manager.cpp` |
| ③ | **C++ → Lua 回调** | `lua_getglobal(L,"名"); lua_push…; lua_pcall(L,n,ret,0); check_lua_error(L,res);` | 实现约定名的全局函数 | 见下表 1.3 |
| ④ | **Lua → C++ 调用** | `int f(lua_State* L)`（裸 `lua_CFunction`）或普通 C 函数（自动包装） | `actor:SetProperty(...)`、`net_send_message_in_c(...)`、`time_now()` | `actor_prop.cpp:actor_set_prop`、`server.cpp:net_send_message_in_c` |
| ⑤ | **自定义类型（userdata + metatable）** | `lua_push_actor(L,actor)` / `lua_check_actor(L,i)`；`luaL_Reg mt_actor[]` 注册方法表 | `actor:GetID()`、`buf:ReadAsInt()`、`anim:SetLoop(-1)` | `actor.cpp`、`LuaAPI.md` 尾部的 `mt_actor`/`MT_ANIMATION`/`mt_buffer_reg`/`MT_NET_THREAD_QUEUE` |

**两种注册函数名（易混淆，必须区分）**：

```cpp
script_system_register_luac_function(L, net_send_message_in_c);  // net_send_message_in_c 是 int f(lua_State*)
script_system_register_function(L, game_server_start);           // game_server_start 是 void f(int port)
```

【待验证】`lua_bind.h` 在 `internals/cxlua`（**不在 ZIP**），故两者的精确实现未读到；
从全部调用点可确认：`_luac_function` = 直接注册 `lua_CFunction`；`_function` = 模板包装普通 C/C++ 函数。
`assets/doc/LuaAPI.md:482` 附近有 `fn) lua_register_function(L, f` 的片段，佐证存在模板化注册器。

### 1.3 C++ → Lua 的**全部**回调点（这是理解本项目的关键）

| Lua 全局函数 | 由谁调用 | 时机 | 出处 |
|---|---|---|---|
| `on_script_system_init` | `script_system_init()` | 启动一次 | `script_system.cpp` |
| `on_script_system_update` | `script_system_update()` | **每 16 ms**；返回 bool | `script_system.cpp` + `server.cpp:main_game_update()` |
| `on_script_system_deinit` | `script_system_deinit()` | 退出（服务端实际不可达）| `script_system.cpp` |
| `on_script_system_draw` | `script_system_draw()` | 客户端每帧 | `script_system.cpp` |
| `actor_on_reg_props(actor)` | `Actor::Actor(pid)` **构造函数** | 每创建一个 actor | `actor.cpp` 顶部 |
| `actor_ev_on_click(actor,button,x,y)` | `Actor::OnClick()` | 鼠标点击 actor | `actor.cpp` |
| `actor_fire_event(actor,ev,x,y)` | `Actor::OnHover()` | 悬停 | `actor.cpp` |
| `server_thread_on_message(conn,buf,len,netq)` | `GameSession::ReadPack()` | **每收到一个完整包** | `server.cpp` |
| `game_server_dispatch_message(pt)` | `game_server_update()` | 每 tick 排空队列时 | `server.cpp` |
| `game_dispatch_message(pt)` | `net_manager_update()`（客户端）| 每帧排空队列 | `client/src/net.cpp` |
| `game_server_on_connection(connected)` | `net_manager_update()` | 连接状态变化 | `client/src/net.cpp` |
| `save_player_database` | `GameServer::OnClose()` | 关服 | `server.cpp:255` —— **该 Lua 函数全仓库未定义**（【已确认】grep 全 ZIP 仅此一处出现）|

⇒ **可借鉴点**：**回调名极简且语义单一，全部是全局裸函数**。
⇒ **反例**：全局裸函数意味着**没有编译期/加载期校验**。JSTM 侧若照抄，建议至少加"启动时校验所有必需回调已注册"的自检。

### 1.4 属性系统的绑定细节（C++ 侧最精巧的一处）

`Actor` 把属性存成**带类型标签的变体数组**，Lua 用整数索引读写：

```cpp
// actor.h
ActorProp& GetProperty(int index);
void SetProperty(int index, ActorProp prop) { m_Props[index] = prop; DirtyProperty(index); }
void DirtyProperty(int index) { m_DirtyProps.insert(index); }
void RegProperty(int index, ActorProp& prop) { assert(index == m_Props.size()); m_Props.push_back(prop); }
std::vector<ActorProp> m_Props;      // 索引 = PROP_* 枚举
std::set<int>          m_DirtyProps; // 脏属性集合

template<typename T> void CopyProperty(int index, T& out) { /* switch(prop.type) → out = prop.b/i/l/f/s/v2 */ }
```

```cpp
// actor_prop.h：标签 + union
class ActorProp {
    EActorPropType type;                 // bool/float/int/str/uint64/vec2
    union { bool b; float f; int i; CXString s; uint64_t l; float v2[2]; };
    // 构造/赋值运算符齐全；PROP_TYPE_STR 分支用 placement new / 显式析构管理 CXString
};
```

Lua 侧：`actor:SetProperty(prop_id, value)` → `actor_set_prop` → `switch(prop.type)` 决定如何 `lua_to*`；
`actor:GetProperty(prop_id)` → `actor_get_prop` → 反向 `lua_push*`。

| 项 | 事实 | 判定 | 原因 |
|---|---|---|---|
| `ActorProp` 变体 | 6 种类型 + placement-new 的 string | ⚠️ | **"一个通用属性槽"让 120 个属性共用一套存取代码**是好设计；但手写 union + 显式析构极易出 bug（`operator=(int)` 里写的是 `s.~basic_string()` 而非 `s.~CXString()`【已确认】），JSTM 建议用 `std::variant`/`nlohmann::json` 或直接 Python `dict` |
| `RegProperty` 的 `assert(index == m_Props.size())` | 强制**按序**注册 | ✅ | 用 assert 把"TSV 行序 == 枚举序 == 数组序"三者绑死的做法**很实用**（配合代码生成，见 `role.md`）|
| 脏标记 | `SetProperty` 必标脏；`IsDirty/GetDirtyProps/ClearDirty` 暴露给 Lua | ✅ | **服务端同步的挂点**就是这里（见 `battle.md` Q8）；思路简单有效 |
| 属性用**索引**而非名字跨语言 | `GetProperty(PROP_HP)` 数值常量 | ⚠️ | 省了字符串比较；但**协议里属性也变成裸数字**（`[pid, 45, 987.0]`），可读性与版本兼容都差。JSTM 已用命名字段（`code__C`），不应倒退 |

### 1.5 热重载机制【已确认】

`common/src/script_system.inl` 把 `script_system_dofile` 以**裸字符串内嵌**进 C++：

```cpp
static const char* script_system_lua_code = R"_(--line alignment
function script_system_dofile(relative_path, env)
    local path = vfs_get_luapath(relative_path)        -- 拼绝对路径
    local subpaths = {}                                 -- 手工规范化 ../ 与大小写
    ...
	local fun,err = loadfile(path,'bt',env or _ENV)
	if fun then print('script_system_dofile',path); fun() else print(err) end
end
)_";
```

用途：
- 三个入口 `scripts/{client,server,launcher}/main.lua` 全部靠它加载模块；
- `scripts/server/main.lua:server_reload()` 重载 share + actor_system + combat_system + team_system；
- 客户端 `client/addon/battle.lua` 的"战斗重载"按钮**同时**重载本地脚本，并通过 `net_manager_player_dostring` **让服务端也重载**。

| 项 | 判定 | 原因 |
|---|---|---|
| `script_system_dofile`（相对路径 + 可注入 env） | ✅ | 简单、可注入沙箱、无需 `package.path` 折腾；**技能/剧本按 ID 加载脚本**正是靠它（见 `battle.md`） |
| `loadfile(path,'bt',…)` 的 `'bt'` | ✅ | `b`=二进制块、`t`=文本块都接受 ⇒ 同一加载器能吃 `.lua` 与字节码 |
| 重载**无依赖失效处理** | ⚠️ | 重载后旧闭包/旧 metatable 仍被引用（例如 `ActorMT` 是全局表，重载会新建表但已存在的 actor 仍指向旧表）⇒ 只适合开发期 |
| 重载 + `dostring` 组合 | ⛔ | 客户端可命令服务端重载任意脚本 ⇒ 生产环境禁用 |

---

## 2. Q2：Server 主循环怎么组织

### 2.1 启动链（`server/src/main.cpp` 全文核心）

```cpp
int main(int argc, char *argv[])
{
	handle_command_args(argc, argv);
	FileSystem::InitWorkPath();
	script_system_prepare_init();          // ① 建 Lua + 注册所有 C 能力 + 跑 script_system_lua_code
	script_system_run_main_script();       // ② luaL_dofile(--luapath，默认 main.lua)
	script_system_init();                  // ③ 调 Lua on_script_system_init
	game_server_start(45000);              // ④ 进入 io_context.run()，阻塞不返回
	script_system_deinit();                // ⑤ 实际不可达
	return 0;
}
```

**端口 45000 是硬编码**（`game_server_start(45000)`），客户端默认端口也是 45000
（`scripts/client/main.lua:SERVER_PORT = command_arg_opt_int('port', 45000)`）【已确认】。

### 2.2 主循环（`server/src/server.cpp`）

```cpp
void main_game_update() {
	time_t_timer timer(_IOContext);
	timer.expires_after(std::chrono::milliseconds(16));
	timer.async_wait([](const std::error_code& /*error*/) {
		script_system_update();     // → Lua on_script_system_update()
		main_game_update();         // 自重排
	});
}

void GameServer::Start() {
	script_system_register_luac_function(m_L, insert_pid_connection_pair);
	script_system_register_luac_function(m_L, erase_pid_connection_pair);
	_IOContext.restart();
	DoAccept();          // 异步 accept，回调里 new GameSession + 递归 DoAccept
	main_game_update();  // 起 16 ms 心跳
	_IOContext.run();    // ★ 唯一事件循环，单线程跑在主线程
}
```

⇒ **【已确认】服务端是单线程模型**：accept、read、write、16 ms tick 全在**同一个** `io_context.run()` 上。
`GameServer` 有个 `std::thread* m_Thread` 成员，但 **`Start()` 从未给它赋值**，
而 `Stop()` 却执行 `m_Thread->join()` ⇒ 【已确认】未初始化指针解引用（UB）。
同时 `DoAccept` 里 `new GameSession(...)` **泄漏**（从不 delete，只靠 socket 关闭）；`g_PlayerConnections` 只 erase 映射不 delete 对象。

### 2.3 每 tick 的 Lua 侧工作（`scripts/server/main.lua`）

```lua
function on_script_system_update()
    game_server_update()      -- C++：排空 NetThreadQueue，逐包调 game_server_dispatch_message
    scene_system_update()     -- Lua：当前为空实现
    combat_system_update()    -- Lua：把战斗中 NPC 的脏属性推给该战场里的玩家

    -- 以下：收集所有玩家 + 其召唤兽的脏属性
    local players = actor_manager_fetch_all_players()
    local dirty_props = {}
    local push_dirty_props = function(actor)
        local pid = actor:GetID()
        local props = actor:GetDirtyProps()
        for i,prop_id in ipairs(props) do
            if is_prop_sync(prop_id) then
                table.insert(dirty_props, {pid, prop_id, actor:GetProperty(prop_id)})
            end
        end
        actor:ClearDirty()
    end
    for _, p in ipairs(players) do
        if p:IsDirty() then push_dirty_props(p) end
        for __, summon in ipairs(p:GetSummons()) do
            if summon:IsDirty() then push_dirty_props(summon) end
        end
    end
    if #dirty_props > 0 then
        net_send_message_to_all_players(PTO_S2C_SYNC_PROPS, cjson.encode(dirty_props))
    end
    return true
end
```

**每 tick 固定成本**【已确认】：遍历全部玩家 + 全部召唤兽 + 其全部脏属性（`std::set<int>` 拷到 Lua 表），
无论玩家是否在交互。**无 tick 率自适应、无分区（AOI）、无剔除**。
`is_prop_sync` 的实现在同文件：

```lua
function is_prop_sync(prop_id)
    if not prop_templ_tbl then prop_templ_tbl = content_system_get_table('actor_template') end
    return prop_templ_tbl[prop_id+1].sync ~= 0
end
```

### 2.4 收包路径（两阶段）

```cpp
// GameSession::ReadPack()（io_context 线程）
auto* m_L = script_system_get_luastate();
lua_getglobal(m_L, "server_thread_on_message");
lua_pushlightuserdata(m_L, this);        // 连接对象
lua_push_cxezio_buffer(m_L, m_Buffer);   // 完整包
lua_pushinteger(m_L, len);
lua_push_net_thread_queue(m_L, &g_ReadPacketQueue);
int res = lua_pcall(m_L, 4, 0, 0);
```

Lua 侧 `scripts/server/server.lua:server_thread_on_message`：

```lua
function server_thread_on_message(conn, buf, len, netq)
    local type = buf:PeekAsInt()
    if     type == PTO_C2C_SIGNUP then …   -- 立即处理：建账号
    elseif type == PTO_C2C_LOGIN  then …   -- 立即处理：验密码 + 绑定 pid↔conn + 回包入队
    elseif type == PTO_C2S_GM     then …   -- 立即处理：转 handle_gm_message
    else  netq:push_back(0, buf, len); buf:Consume(len)   -- 其余入队，等主 tick
    end
end
```

`game_server_update()`（C++，由 `game_server_update` 注册为 luac function）排空队列：

```cpp
while (!g_ReadPacketQueue.Empty(NetThreadQueue::Read)) {
    Buffer& pt = g_ReadPacketQueue.Front(NetThreadQueue::Read);
    lua_getglobal(L, "game_server_dispatch_message");
    lua_push_cxezio_buffer(L, pt);
    lua_pcall(L, 1, 0, 0);
    g_ReadPacketQueue.PopFront(NetThreadQueue::Read);
}
```

| 项 | 事实 | 判定 | 原因 |
|---|---|---|---|
| 16 ms 固定 tick + 自重排 timer | asio `basic_waitable_timer` | ✅ | **极简、无阻塞、与 IO 同线程**，适合小型私服/模拟器；JSTM 的 mock 若从 `select` 循环升级，这是最省事的骨架 |
| 单线程共享状态 | 无锁 | ✅ | 无并发 bug；代价是无多核扩展 |
| `m_Thread` 未初始化 + `Stop()` join | UB；且 `main` 里 deinit 不可达 | ⚠️ | 反面教材：**保留了一个"未来要起线程"的残留成员却没清理**，JSTM 别留这种半成品 |
| tick 里遍历全部玩家同步 | 每 16 ms 全量扫描 | ⚠️ | JSTM 若按此写，随在线人数线性劣化；应改为**事件驱动脏标记 + 批量 flush**（见 `battle.md` 建议）|
| 两阶段（握手期抢占 + 主循环派发）| 登录/注册/GM 在收包回调直答 | ✅ | **很值得学**：避免在 IO 回调里做重逻辑，同时保证握手低延迟 |
| `new GameSession` 泄漏 / 连接对象不回收 | 只 close socket | ❌ | 反面教材 |

---

## 3. Q3：Lua 如何实现游戏逻辑

### 3.1 入口与加载顺序（`scripts/server/main.lua`）

```lua
stub = {}
luadbg_listen(9500)                                     -- VSCode Lua 调试器（cxluadbg.dll）

script_system_dofile('../share/enums.lua')              -- 种族/门派常量
script_system_dofile('../share/enums_protocol.lua')      -- ★ 协议 ID（真源）
script_system_dofile('../share/vfs.lua')                 -- 路径
script_system_dofile('../share/utils.lua')               -- 工具 + 表解析 + 公式辅助
script_system_dofile('../share/content_system.lua')      -- ★ 全部 TSV 表加载
script_system_dofile('../share/actor_metatable.lua')     -- ★ 角色数据模型 + 数值公式

script_system_dofile('server.lua')                       -- 网络封装 + 账号库
script_system_dofile('actor_system.lua')                 -- 角色/召唤兽/移动/聊天
script_system_dofile('scene_system.lua')                 -- NPC 生成 + 点击
script_system_dofile('team_system.lua')                  -- 队伍
script_system_dofile('../combat/combat_system.lua')       -- 战斗（内部再分 server/client）

script_system_dofile('gm.lua')                            -- GM 命令
```

注意 `scripts/combat/combat_system.lua` 内部**自己分叉**：

```lua
if IsServer() then script_system_dofile('../combat/server/combat_system.lua') end
if IsClient() then script_system_dofile('../combat/client/combat_system.lua') end
```

⇒ **同一份战斗代码，服务端只加载算逻辑，客户端只加载播动画**。这是本项目最值得学的组织手法之一。

### 3.2 逻辑组织：`stub` 注册表 + `xxx_system_*` 命名约定

**消息处理**：所有 handler 写进全局 `stub`：

```lua
stub[PTO_C2C_MOVE_TO_POS] = function(req, js)
    local player = actor_manager_fetch_player_by_id(req.pid)
    if not player then return end
    player:SetPos(req.x, req.y)
    net_send_message_to_all_players(PTO_C2C_MOVE_TO_POS, js)   -- 原样转发
end

stub[PTO_C2C_CHAT] = function(req, js)
    net_send_message_to_all_players(PTO_C2C_CHAT, js)
end
```

**系统模块**统一三段式命名（无框架、纯约定）：

| 系统 | init | update | stop/其它 | 文件 |
|---|---|---|---|---|
| 内容表 | `content_system_init()` | — | — | `share/content_system.lua` |
| 角色 | `actors_on_load()` / `read_account_database()` | — | `actors_on_save()` | `server/actor_system.lua`、`server.lua` |
| 场景 | `scene_system_init()` | `scene_system_update()`（空）| `scene_system_stop()`（空）| `server/scene_system.lua` |
| 队伍 | — | — | `team_system_on_disconnect()` | `server/team_system.lua` |
| 战斗 | `combat_system_init()` | `combat_system_update()` | `combat_system_battle_on_actor_leave()` | `combat/server/combat_system.lua` |
| GM | — | — | `handle_gm_message(conn,msg)` | `server/gm.lua` |

⇒ **没有系统注册表、没有依赖注入、没有加载顺序声明**，全靠 `main.lua` 里的手写顺序。
但 `main.lua` 同时提供了 `server_reload()` 明确列出重载顺序 ⇒ 顺序知识被显式记录，这点是好的。

### 3.3 内容表驱动（`scripts/share/content_system.lua`）

```lua
local content_tables = {}
function content_system_get_table(name) return content_tables[name] end
function content_system_set_table(name, func, ...)
    content_tables[name] = perf_call('content_system_set_table '..name, func, ...)
end

function content_system_init()
    content_system_set_table('avatar_role',        read_avatar_role)
    content_system_set_table('avatar_weapon',      read_avatar_weapon)
    content_system_set_table('avatar_npc',         read_npc_table)
    content_system_set_table('avatar_scene_npc',   read_avatar_scene_npc_table)
    content_system_set_table('avatar_summon',      read_avatar_summon_table)
    content_system_set_table('scene_monster',      read_scene_monster)
    content_system_set_table('magic',              read_magic_table)
    content_system_set_table('maps',               read_map_table)
    content_system_set_table('actor_template',     read_actor_template)
    content_system_set_table('skill',              init_skill_template_table)
    content_system_set_table('buff',               init_buff_template_table)
    content_system_set_table('school',             init_school_templ_table)
    content_system_set_table('equip',             init_equip_templ_table)
    content_system_set_table('npc',                init_npc_table)
    content_system_set_table('summon_quality',     init_summon_quality_table)
    content_system_set_table('scene',              init_scene_table)
    content_system_set_table('transport',          init_transport_table)
    ... 共 19 张
end
```

统一走 `utils_parse_tsv(name, columns)`（`share/utils.lua`）：

```lua
utils_parse_tsv = function(name, columns)
    return utils_parse_tsv_file(vfs_get_tsvpath(name), columns)
end
```

而 TSV 解析器支持**声明式列格式**：`{ name='ID', fmt='i' }`、`fmt='n'`（float）、`fmt='pos'`（`x,y` → `{x,y}`）、`fmt='res'`、`def=` 默认值。

| 项 | 判定 | 原因 |
|---|---|---|
| `content_system_get_table(name)` 全局表注册 | ✅ | **"表名 → 内存表"** 是内容驱动的地基；JSTM 已有 347 张 `luac` 表，正好可以做一个同构的 `get_table(name)` 门面统一访问 |
| `perf_call` 包装每张表加载并打耗时 | ✅ | 启动性能可观测；JSTM 的表总量更大，更需要 |
| `utils_parse_tsv` 的声明式 `fmt` | ✅ | 声明式列类型比逐列手写转换更不易错；且 `*` 行=默认值、首行=列名，格式友好 |
| `read_magic_table` 内硬算 `row.resid = (pack<<32)|wasid` | ⚠️ | 把资源 ID 拼装逻辑写进表加载器 ⇒ JSTM 的 `res_id` 解析应集中到独立模块，而不是散在 read_* 里 |

### 3.4 存档（明文 JSON，客户端可触发）

```lua
-- scripts/server/actor_system.lua
function actors_on_save()
    local actor_infos = {}
    for pid, actor in pairs(actor_manager_fetch_all_actors()) do
        table.insert(actor_infos, actor:GetProperties())     -- 0 基属性字典
    end
    table.sort(actor_infos, function(a,b) return a[PROP_ID] < b[PROP_ID] end)
    local fw = io.open(vfs_get_workdir()..'/assets/storage/actor.data','w')
    fw:write(cjson.encode(actor_infos)); fw:close()
end
stub[PTO_C2C_SAVE_ACTORS] = function() actors_on_save() end
```

```lua
-- scripts/server/server.lua
function read_account_database()   -- 启动时读 account.data 建 account → {pid,account,password}
stub[PTO_C2C_SAVE_ACCOUNT_DATABASE] = function() ... cjson.encode(accounts) ... end
```

**问题清单**（均为【已确认】）：

| 问题 | 事实 | 判定 |
|---|---|---|
| 明文明文密码 | `account_info.password = msg.password` 直接存 JSON | ⛔ JSTM 禁止 |
| 客户端可触发存盘 | `PTO_C2C_SAVE_ACTORS` / `PTO_C2C_SAVE_ACCOUNT_DATABASE` 是 C→S 协议，无鉴权 | ⛔ 可被刷 IO / 竞态覆盖 |
| 全量重写 | 每次保存重写整个文件，无原子写（无 tmp+rename） | ❌ 崩溃即存档损坏 |
| 存档格式耦合 0 基索引 | JSON 键为 `"0".."N"` | ⚠️ 脆弱 |
| UID 生成 | `utils_next_uid(ns)`：`os.time()%0xFFFFFFFF` 起，内存自增，**不持久化** | ❌ 重启后可能重号（同一秒内重启 ⇒ 首个 uid 相同）⇒ JSTM 必须用持久化自增/雪花 ID |
| `prop_id_to_name` | `content_system_get_table('actor_template')[prop_id+1].name` | ✅ 调试期把属性号翻成名字，很实用 |

### 3.5 未读到 / 待验证（Q1–Q3）

- 【未读到】`internals/cxlua` 全部（`lua_bind.h`、`cxlua.h`、`cxezio/buffer.h`、`net_thread_queue.h`、`lua_net.h`）
  ⇒ `script_system_register_function` 与 `_luac_function` 的精确实现、`NetThreadQueue` 的线程安全性均【待验证】。
- 【未读到】`common/src/actor/action.cpp`（`ActionStateMachine`，21 KB）仅读片段。
- 【未读到】`scripts/client/actor_metatable.lua`、`addon/{bag,props,options,quest}.lua`。
- 【未知】`luadbg_listen` 的调试端口在生产是否默认开启（`scripts/server/main.lua` 顶部无条件 `luadbg_listen(9500)`）【已确认无条件调用】。

---

## 4. 逐文件表（Q1/Q2/Q3 相关）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `server/src/main.cpp` | `main()` | 5 步启动，`game_server_start(45000)` 阻塞 | ✅ | **启动顺序清晰**（参数→工作目录→Lua→入口脚本→init 回调→服务启动），可直接映射为 JSTM 模拟器的 `main()` |
| `server/src/server.cpp` | `main_game_update()` | 16 ms asio timer 自重排 → `script_system_update()` | ✅ | **固定 tick + 自重排**是最省事的服务端心跳骨架；JSTM 的 mock_server 若从阻塞 recv 循环改造，这是首选形态 |
| `server/src/server.cpp` | `GameServer::Start()` | `DoAccept` + `main_game_update` + `_IOContext.run()` | ⚠️ | 骨架对；但 `m_Thread` 未初始化、`new GameSession` 泄漏 ⇒ 只取结构不取实现 |
| `server/src/server.cpp` | `GameSession::ReadHeader()/ReadPack()` | 4 字节长度帧 + 异步读 + `lua_pcall(server_thread_on_message)` | ⚠️ | **"收包即回调 Lua"** 缩短链路；但 `len` 无上界校验 ⇒ JSTM 必须加上界（JSTM 帧头是 `u16 BE cmd`，本来就比 `u32` 窄，仍须校验） |
| `server/src/server.cpp` | `game_server_update(lua_State*)` | 主 tick 排空 `g_ReadPacketQueue` → `game_server_dispatch_message` | ✅ | **"网络线程只入队、主循环统一派发"** 的正确形态；JSTM 应照此把 IO 与逻辑解耦（这也是 JSTM 目前缺的） |
| `server/src/server.cpp` | `net_send_message_in_c` / `_to_players_in_c` / `_to_all_players_in_c` | 按 pid 查连接发；`ToAll` 遍历 map | ⚠️ | 三个原语足够表达全部下行；但**ToAll 无过滤**（无 AOI）⇒ JSTM 需要"按场景/视野筛"的第三层封装 |
| `server/src/server.cpp` | `insert_pid_connection_pair` / `erase_pid_connection_pair` | Lua 持有 C++ 连接指针并维护映射 | ⚠️ | **"绑定关系由 Lua 决定"** 便于多开测试；裸指针 + 无生命周期保护是隐患 |
| `server/src/server.cpp` | `GameServer::OnClose()` | 调未定义的 `save_player_database` | ❌ | 死代码 + 缺失实现，反面教材 |
| `server/src/server.h` | `class GameServer` | 持有 `lua_State* m_L`、acceptor、thread | ⚠️ | `m_Thread` 半成品成员 |
| `server/CMakeLists.txt` | `-DSIMPLE_SERVER` | 宏切角色 + cotire PCH | ⚠️ | 宏切角色的思想可借鉴；构建系统不可迁移 |
| `common/src/script_system.cpp` | `script_system_prepare_init()` | 建 state + 固定 `luaopen_*` 清单 + 内嵌 lua code + `cxluadbg.dll` | ✅ | **"C 能力显式清单注册"** 一目了然，启动期即可发现缺失；JSTM 可照此列出全部需注册的原生函数 |
| `common/src/script_system.cpp` | `script_system_run_main_script()` / `init/update/deinit/draw` | `--luapath` 指定入口；5 个生命周期回调 | ✅ | 入口可配 + 生命周期钩子极简 ⇒ **同一进程可跑 client/server/launcher/examples 四种入口**（CXEngine 正是这么做的），对 JSTM 做夹具/工具链极有用 |
| `common/src/script_system.cpp` | `process_is_server()` | 暴露给 Lua `IsServer()` | ✅ | **同代码双端分叉**的基础设施（见下条）|
| `common/src/script_system.inl` | `script_system_lua_code` / `script_system_dofile()` | 内嵌 Lua 源码实现相对路径 dofile + env 注入 | ✅ | 技能/剧本按 ID 加载、热重载都靠它；**值得 JSTM 借鉴的最小加载器** |
| `common/src/message.h`/`.cpp` | `Telegram`, `MessageDispatcher` | 延迟消息队列 | ⚠️ | 抽象可用；但全项目 `HandleMessage` 均 `return false` ⇒ 死代码，只借概念（定时/延迟消息用 JSTM 自己的调度）|
| `common/src/state.h` | `State<EntityType>`, `StateMachine<EntityType>` | 教科书 FSM | ⚠️ | **接口干净值得学**；`ChangeState` 有 null 解引用 bug ⇒ 重写 |
| `common/src/time/timer_manager.cpp` | `TimerManager::Create/…`, `timer_manager_add_timer` | 具名定时器 + 双缓冲垃圾回收 + `luaL_ref` 持有回调 | ✅ | **按名取定时器的游戏逻辑友好性极高**（`timer_manager_pause_timer('TimerWildBattle',false)`）；JSTM 的 CD/刷新/自动战斗直接受用 |
| `common/src/file_loading.cpp` | `FileLoadingThread::PostTask/Run/IsFileLoading/IsFileLoadOk` | 单后台线程 + 任务去重 + 状态查询 | ✅ | **异步加载 + 主线程轮询状态**对 APK 资源/大表加载是刚需；JSTM 的 `_config_mon.json`(818 KB)/`_config_item.luac`(838 KB) 都适合异步 |
| `common/src/entity.h` | `BaseGameEntity`, `GameEntityManager` | 实体基类 + 单例注册表 | ⚠️ | `GameEntityManager` 从未被使用（`Actor` 不注册）⇒ 只借"实体 id → 对象"的概念，用 JSTM 自己的注册表 |
| `common/src/logger.cpp` | `cxlog_info/warn/error` | 日志上报到 Lua | ✅ | JSTM 正在做爬包/回放，**统一日志出口**是前提 |
| `scripts/server/main.lua` | `on_script_system_init` | `content_system_init → combat_system_init → scene_system_init → read_account_database → actors_on_load` | ✅ | **启动顺序即依赖声明**，明确可读 |
| `scripts/server/main.lua` | `on_script_system_update` | 收包 + 场景 + 战斗 + 脏属性广播，返回 true | ⚠️ | 结构清晰；但**每 tick 全量扫描玩家**不可扩展 |
| `scripts/server/main.lua` | `game_server_dispatch_message` | `ReadAsInt` + `ReadAllAsString` + `cjson.decode` + `stub[type]` | ✅ | 协议分发的零样板写法 |
| `scripts/server/main.lua` | `stub[PTO_C2S_DOSTRING / PLAYER_DOSTRING / ACTOR_DOSTRING]` | 服务端 `load()` 客户端 Lua 并执行 | ⛔ | **远程代码执行后门**，绝对禁止 |
| `scripts/server/main.lua` | `server_reload()` | 显式重载顺序 + 重新 init | ✅ | **把"正确重载顺序"写成代码**，比文档可靠 |
| `scripts/server/server.lua` | `net_send_message*`（3 个） | 打印 `proto_name` 后转 C | ✅ | 发送出口统一打印协议名 |
| `scripts/server/server.lua` | `read_account_database`, `stub[PTO_C2C_SAVE_ACCOUNT_DATABASE]` | 账号库内存 + 明文 JSON 落盘 | ❌ | 明文密码 + 客户端触发存盘 |
| `scripts/server/server.lua` | `server_thread_on_message(conn,buf,len,netq)` | 4 分支：注册/登录/GM 立即处理，其余入队 | ✅ | **两阶段收包**：握手低延迟 + 主循环做重逻辑 |
| `scripts/server/server.lua` | `server_on_disconnect(pid)` | 退队 + 脱战 | ✅ | 断线清理集中一处 |
| `scripts/server/actor_system.lua` | `actors_on_load` / `actors_on_save` / `stub[PTO_C2C_LOGIN]` / `PTO_C2S_CREATE_SUMMON` / `PTO_C2S_FETCH_SUMMON` / `PTO_C2C_MOVE_TO_POS` / `PTO_C2C_CHAT` / `PTO_C2S_CREATE_PLAYER` / `PTO_C2S_DELETE_ACTOR` / `ActorMT:AddSummon/GetSummon/GetSummons` | 登录建号、召唤兽管理、移动与聊天全服广播 | ⚠️ | **"召唤兽 uid 列表存 JSON 字符串属性里"**（`PROP_SUMMON_UIDS` = `cjson.encode({...})`）是可用但丑陋的做法；`PTO_C2S_CREATE_PLAYER` 用客户端 JSON 覆盖属性 = 客户端权威 |
| `scripts/server/scene_system.lua` | `scene_system_init/update/stop`, `stub[PTO_C2S_CLICK_NPC]` | 启动时按 `npc.tsv` 批量创建 NPC actor；点击 NPC 回包 | ✅ | **场景 NPC 由表批量生成、服务端持有实体**，这是端游式做法，对 JSTM 场景静态 NPC 有参考价值 |
| `scripts/server/team_system.lua` | `TeamMT:*`（new/GetID/AddMember/RemoveMember/HasMember/SetLeader/GetMembers/GetLeader/Serialize）+ `team_system_*` + `stub[PTO_C2S_TEAM_*]` | 队伍对象存 `__teams__`，成员列表存 id，`PROP_TEAM_ID` 反向索引 | ✅ | **"对象表 + 属性反向索引"** 简洁；`Serialize()` 统一出网格式值得学 |
| `scripts/server/gm.lua` | `handle_gm_message(conn,msg)` | `exit_server` 直接 `os.exit(0)`；`account_info` 直接写回 buffer；其它全服广播 | ⚠️ | **GM 走同一连接但绕过 `stub`** 的旁路设计思路可参考；`os.exit` 无存档 = 危险 |
| `scripts/share/content_system.lua` | `content_system_init/get_table/set_table` + 19 个 `read_*/init_*` | TSV → 内存表，`perf_call` 计时 | ✅ | **表名门面 + 启动计时**；JSTM 347 张表正需要这个门面 |
| `scripts/share/utils.lua` | `utils_parse_tsv*`, `utils_string_split*`, `utils_next_uid`, `read_database_file`, `prop_id_to_name`, `get_local_ips` | 工具集 | ⚠️ | 大多可自研；`utils_next_uid`（重启可能重号）与 `get_local_ips`（`io.popen('ipconfig')` + GB2312 转码）不可借鉴 |
| `scripts/share/vfs.lua` | `vfs_getpath/makepath/get_tsvpath/get_luapath/get_wdfpath/get_mappath/IsServer/IsClient` | 路径集中 | ✅ | 路径集中化；注意与 `utils.lua` 末尾同名 `IsServer/IsClient` **重复定义** |
| `scripts/share/enums.lua` | `RACE_*`, `SCHOOL_*` | 手写常量 | ❌ | 内容是《梦幻西游》15 门派，与 JSTM《绝世唐门》职业体系无关 |
| `scripts/generator/actor_template.lua` | `gen_actor_enum()`, `solve()` | `actor_template.tsv` → `actor_enum.{h,cpp}` | ✅ | **表 → C++ 枚举的代码生成**是真正亮点（详见 `role.md`）|
| `scripts/generator/protocol.lua` | `gen_protocol()` | `enums_protocol.lua` → `protocol.{h,cpp}` | ⚠️ | 机制好、方向要反过来（详见 `protocol.md`）|
| `scripts/generator/table_template.lua`（20 KB）| `_parse_weapon_row/_parse_role_row/_parse_npc_row/_parse_bb_row`, `init_table_templates` | 解析梦幻 WDF 的 `.ini` 资源索引 → 生成 `avatar_*.tsv` | ❌ | **梦幻西游专属资源格式**（武器/角色/召唤兽/动作命名法），对 JSTM 无用 |
| `scripts/generator/imgui_binding_generator.lua`（41 KB）| — | 自动生成 ImGui 的 Lua 绑定 | ⚠️ | **"自动生成绑定层"** 的思路可借鉴（若 JSTM 需要给 Python/调试面板生成协议字段绑定）；实现是 ImGui 专属，不可用 |
| `scripts/examples/example00..07.lua` | `init/update` | 教程式示例，展示可用 API | ✅ | **可执行文档**：想知道"这个引擎能干什么"最快的方式；example03 甚至列出了全部枚举与用法 |
| `scripts/launcher/main.lua` + `window.lua` | `init/update/deinit`, `launcher_init/update` | 独立 exe 启动服务端/客户端、看账号、发 GM | ✅ | **"launcher 用同一套 Lua 能力独立成型"** 说明分层真的成立；JSTM 可仿此做"一键起服务端 + 抓包面板" |
| `scripts/examples/_debugger.lua` | — | 调试器适配示例 | ⚠️ | 仅参考调试接线 |
| `common/src/file_system.cpp` | `FileSystem::InitWorkPath/GetLuaPath` | `--cwd` 工作目录 + 脚本路径解析 | ✅ | 命令行工作目录 ⇒ 同一 exe 服务任意资源目录（JSTM 切包对比场景直接受用）|
| `assets/doc/LuaAPI.md` | 全文 | 手工维护的 C 函数/枚举/方法表清单 | ✅ | **"可调原生能力清单"**，正是 JSTM 逆向最缺的文档形态 |
