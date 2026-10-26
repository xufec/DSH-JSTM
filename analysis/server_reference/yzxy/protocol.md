# CXEngine（YZXY）协议定义方式审计

> 结论均来自 ZIP 内明文源码；标注【已确认】/【待验证】/【未知】。
> 判定列：✅ 适合借鉴 / ⚠️ 只能借鉴局部 / ❌ 不适合 / ⛔ 必须排除

---

## 1. 一句话结论

【已确认】**CXEngine 的协议 ID 由 Lua 唯一真源定义，C++ 头文件由 Lua 脚本"打印"生成；线格式是 `[len:4][proto:4][JSON]`，没有任何字段级 schema。**
这与任务书要求 JSTM 对比的重点（`scripts/share/` 里有没有 protocol/enums 定义）**完全命中**：
`scripts/share/enums_protocol.lua` 就是协议定义文件，它同时被客户端、服务端、launcher 三方 `script_system_dofile` 加载。

---

## 2. 协议 ID 定义文件（找到了）

### 2.1 `scripts/share/enums_protocol.lua`（**协议 ID 唯一真源**）

**格式**：每行一个全局常量，第一条用 `enum_reset()` 重置计数器，其余用 `enum_next()` 自增。

```lua
PTO_C2C_SIGNUP                              = enum_reset()
PTO_C2C_LOGIN                               = enum_next()
PTO_C2C_LOGOUT                              = enum_next()
PTO_C2C_MOVE_TO_POS                         = enum_next()
PTO_C2C_PLAYER_ENTER                        = enum_next()
PTO_C2C_ACTOR_ENTER                         = enum_next()
PTO_C2C_CHAT                                = enum_next()
PTO_C2C_SAVE_ACTORS                         = enum_next()
PTO_C2C_SAVE_ACCOUNT_DATABASE               = enum_next()
PTO_C2S_COMBAT_START                        = enum_next()
...（共 63 条）...
PTO_C2S_COMBAT_PVP_START                    = enum_next()
PTO_S2C_COMBAT_PVP_START                    = enum_next()
```

紧跟其后是**给日志用的反查表**与函数：

```lua
local proto_to_name = {
    [PTO_C2C_SIGNUP] = 'PTO_C2C_SIGNUP',
    [PTO_C2C_LOGIN]  = 'PTO_C2C_LOGIN',
    ...（逐条，共 63 条）...
}
function proto_name(proto)
    return proto_to_name[proto] or proto
end
```

**命名约定**（很有价值的一条经验）：`PTO_` 前缀 + 方向 + 名。
- `C2C` = client ↔ client（实际是"客户端发起、服务端**广播给所有客户端**"，如移动/聊天/玩家进场）
- `C2S` / `S2C` = 客户端→服务端 / 服务端→客户端

**标注**：
- 【已确认】文件内容、条数（63）、命名规范、`proto_name` 反查机制。
- 【未知】`enum_reset()` / `enum_next()` 的 **C 实现不在 ZIP 内**（属 `internals/cxlua`），
  且生成的 `common/src/protocol.h` **未入库**（入库的是手写桩，只含 `CX_MSG_HEADER_LEN`）。
  ⇒ **协议 ID 的实际数值无法从本 ZIP 确定**。这点必须如实记录，不能凭 `enum_reset` 猜起始值。
- 【已确认】`assets/doc/LuaAPI.md:483-484` 把 `enum_reset`、`enum_next` 列为可用 C 函数 ⇒ 它们确由 C 侧提供。

### 2.2 全 63 条协议清单（按文件出现顺序，标注方向）

| # | 协议名 | 方向（按名）| 实测处理位置 |
|---|---|---|---|
| 1 | `PTO_C2C_SIGNUP` | C→S（注册）| `scripts/server/server.lua` `server_thread_on_message` |
| 2 | `PTO_C2C_LOGIN` | C→S 登录 | `server_thread_on_message`（校验）+ `actor_system.lua`（建角色）|
| 3 | `PTO_C2C_LOGOUT` | C→S | 未读到处理函数 |
| 4 | `PTO_C2C_MOVE_TO_POS` | C→S 移动 | `actor_system.lua` → 广播 |
| 5 | `PTO_C2C_PLAYER_ENTER` | S→C 玩家进场 | `actor_system.lua` 发出；`client/actor_manager.lua` 收 |
| 6 | `PTO_C2C_ACTOR_ENTER` | S→C NPC/召唤兽进场 | `actor_system.lua` 发出；`client/actor_manager.lua` 收 |
| 7 | `PTO_C2C_CHAT` | C→S 聊天 | `actor_system.lua` → 广播；`client/net_manager.lua` 收 |
| 8 | `PTO_C2C_SAVE_ACTORS` | C→S 触发存档 | `actor_system.lua` `stub[PTO_C2C_SAVE_ACTORS]` |
| 9 | `PTO_C2C_SAVE_ACCOUNT_DATABASE` | C→S 触发存档 | `server.lua` `stub[PTO_C2C_SAVE_ACCOUNT_DATABASE]` |
| 10 | `PTO_C2S_COMBAT_START` | C→S（PVP 指定 atk/def）| `combat/server/combat_system.lua` |
| 11 | `PTO_S2C_COMBAT_START` | S→C 战场全量 | 同上发出；`combat/client/combat_system.lua` 收 |
| 12 | `PTO_S2C_COMBAT_EXECUTE` | S→C 回合技能效果数组 | 同上 |
| 13 | `PTO_C2S_COMBAT_CMD` | C→S 战斗指令 | `combat/server/combat_system.lua` |
| 14 | `PTO_S2C_SYNC_PROPS` | S→C 脏属性增量 | `server/main.lua`、`combat/server/combat_system.lua` 发出；`client/net_manager.lua` 收 |
| 15–16 | `PTO_C2S_NPC_DIALOG` / `PTO_S2C_NPC_DIALOG` | 对话 | 未读到 `stub` 处理（客户端 `module/dialog.lua` 只调 UI） |
| 17 | `PTO_C2S_DOSTRING` | C→S **远程执行 Lua** | `server/main.lua` `stub[PTO_C2S_DOSTRING]` |
| 18 | `PTO_C2S_PLAYER_DOSTRING` | C→S 以 player 为 env 执行 | 同上 |
| 19 | `PTO_C2S_ACTOR_DOSTRING` | C→S 以 actor 为 env 执行 | 同上 |
| 20 | `PTO_C2S_CREATE_PLAYER` | C→S 整体覆盖角色属性 | `actor_system.lua` |
| 21–22 | `PTO_C2S_CLICK_NPC` / `PTO_S2C_CLICK_NPC` | 点击 NPC | `scene_system.lua` / `client/actor_manager.lua` |
| 23–34 | `PTO_C2S_TEAM_*` / `PTO_S2C_TEAM_*`（CREATE/DISMISS/ADD_MEMBER/REMOVE_MEMBER）| 队伍 | `team_system.lua` |
| 35–36 | `PTO_C2S_FETCH_TEAM` / `PTO_S2C_FETCH_TEAM` | 拉取队伍 | `team_system.lua` |
| 37–38 | `PTO_C2S_COMBAT_LEAVE_BATTLE` / `PTO_S2C_COMBAT_LEAVE_BATTLE` | 脱战 | 未读到 `stub`（只有 `combat_system_battle_on_actor_leave` 函数）|
| 39–40 | `PTO_C2S_COMBAT_END_BATTLE` / `PTO_S2C_COMBAT_END_BATTLE` | 结束战斗 | `combat/server/combat_system.lua` / `client/combat_system.lua` |
| 41–42 | `PTO_C2S_CREATE_SUMMON` / `PTO_S2C_CREATE_SUMMON_RESP` | 创建召唤兽 | `actor_system.lua` |
| 43–44 | `PTO_C2S_FETCH_SUMMON` / `PTO_S2C_FETCH_SUMMON_RESP` | 拉取召唤兽 | `actor_system.lua` / `client/module/summon.lua` |
| 45–46 | `PTO_C2S_GM` / `PTO_S2C_GM` | GM | `server/gm.lua` `handle_gm_message` / `client/net_manager.lua` |
| 47–48 | `PTO_C2S_SWITCH_SCENE` / `PTO_S2C_SWITCH_SCENE` | 切场景 | `client/actor_manager.lua` 有 `PTO_S2C_SWITCH_SCENE` 空实现；**服务端未读到处理** |
| 49 | `PTO_C2S_FETCH_ACCOUNT_INFO` | 拉账号信息 | 未读到 `stub` |
| 50–51 | `PTO_C2S_COMBAT_CREATE` / `PTO_S2C_COMBAT_CREATE` | 建战场 | `combat/server/combat_system.lua` / `client/combat_system.lua` |
| 52–53 | `PTO_C2S_CREATE_ACTOR` / `PTO_S2C_CREATE_ACTOR` | 动态建 actor | `actor_system.lua` / `client/actor_manager.lua` |
| 54–55 | `PTO_C2S_DELETE_ACTOR` / `PTO_S2C_DELETE_ACTOR` | 动态删 actor | `actor_system.lua` / `client/actor_manager.lua` |
| 56–57 | `PTO_C2S_SAVE_ACTOR` / `PTO_S2C_SAVE_ACTOR` | 单角色存档 | 未读到 `stub` |
| 58–59 | `PTO_C2S_PVE_BATTLE_START` / `PTO_S2C_PVE_BATTLE_START` | 暗雷战斗 | **未读到实现**（疑似废弃）|
| 60–61 | `PTO_C2S_COMBAT_PVE_START` / `PTO_S2C_COMBAT_PVE_START` | PVE 战斗（`PTO_S2C` 只作 `PTO_S2C_COMBAT_START` 回复）| `combat/server/combat_system.lua` |
| 62–63 | `PTO_C2S_COMBAT_PVP_START` / `PTO_S2C_COMBAT_PVP_START` | PVP 战斗 | `stub[PTO_C2S_COMBAT_PVP_START]` **是空函数**【已确认】|

> 【已确认】清单与序号来自 `scripts/share/enums_protocol.lua`；方向判定来自名字前缀 + 实测调用点。
> 【待验证】`PTO_*` 的**数值**未知（见 2.1）；表中序号是文件内出现顺序，**不等于协议值**。

---

## 3. 协议 ID 的代码生成链（★ 本项目的亮点之一）

### 3.1 `scripts/generator/protocol.lua`

【已确认】该脚本是一段**启动即执行**（文件末尾直接 `gen_protocol()`）的生成器，流程：

1. `vfs_makepath('scripts/share/enums_protocol.lua')` → 定位真源；
2. 建 `module = setmetatable({}, {__index = _ENV})`，`loadfile(path,'bt',module)` 后 `func()` ——
   **在沙箱里求值**，于是 `module` 里得到 `PTO_XXX = 数值` 的表；
3. `utils_fetch_sort_keys(module, function(a,b) return module[a] < module[b] end)` —— 按数值排序；
4. **写 `common/src/protocol.h`**：

```cpp
#pragma once
#include <string>
#define  CX_MSG_HEADER_LEN 4

enum EProtocalType
{
	PTO_C2C_SIGNUP=0,
	PTO_C2C_LOGIN=1,
	...
	PTO_S2C_COMBAT_PVP_START=62
};

void luaopen_protocol(lua_State* L);
```

5. **写 `common/src/protocol.cpp`**：

```cpp
#include "protocol.h"

void luaopen_protocol(lua_State* L)
{
#define REG_ENUM(name)  (lua_pushinteger(L, name),lua_setglobal(L, #name))
	REG_ENUM(PTO_C2C_SIGNUP);
	...
#undef REG_ENUM
	(lua_pushinteger(L, CX_MSG_HEADER_LEN), lua_setglobal(L, "CX_MSG_HEADER_LEN"));
}
```

**同一模式**也用于角色属性枚举：`scripts/generator/actor_template.lua` 读 `actor_template.tsv` → 写
`common/src/actor/actor_enum.h`（`enum EActorProp { PROP_ID, PROP_DIR, … , PROP_COUNT }` + `EActorPropType`）
与 `actor_enum.cpp`（`REG_ENUM` 逐条 `lua_setglobal`）。见 `role.md`。

### 3.2 这套生成机制的评价

| 维度 | 评价 |
|---|---|
| 单一真源 | ✅ 好：协议 ID 只写一遍（Lua），C++ 与 Lua 不可能漂移 |
| 与 JSTM 的匹配度 | ⚠️ JSTM 的协议真源是 `assets/src/config/protocal/{all_proto,cmd_resolve_*}.luac`（**客户端自带、只读、JIT 字节码**），JSTM 服务端**无法回写生成**客户端文件。CXEngine 是"自己的引擎自己生成"，JSTM 是"逆向别人的客户端"。⇒ **生成方向必须反过来**：JSTM 应从 `cmd_resolve_*.luac` 生成服务端常量/结构，而不是从服务端生成客户端 |
| 风险 | ⛔ 生成器产物 `common/src/protocol.h` **未入库**，导致"仓库里看到的 `protocol.h` 是残缺桩"，容易误导；生成脚本与消费代码同时入库是更稳的做法 |

---

## 4. 线格式（Wire Format）—— 逐字节

【已确认】服务端 `server/src/server.cpp`：`SendMessageToPlayer` / `SendMessageToPlayers`：

```cpp
Buffer buf;
buf.Write(proto);                                  // 4 字节协议号
buf.Write(msg, strlen(msg));                        // JSON 文本，无长度前缀
buf.Prepend((int)buf.readable_size());              // 最前面插入总长 = proto + json 的字节数
it->second->Send(buf);
```

客户端 `client/src/net.cpp`：`net_send_message_in_c(int proto, const char* msg)` 完全同构。

接收侧 `GameSession::ReadHeader()` / `ReadPack()`：

```cpp
asio::async_read(m_Socket, asio::buffer(m_Buffer.BeginWrite(), 4), ...);  // 先读 4 字节长度
int len = m_Buffer.ReadAsInt32();                                          // 小端 int32
asio::async_read(m_Socket, asio::buffer(m_Buffer.BeginWrite(), len), ...); // 再读 len 字节
```

Lua 侧解析（`scripts/server/main.lua`）：

```lua
function game_server_dispatch_message(pt)
    local type = pt:ReadAsInt()            -- 4 字节协议号
    local js = pt:ReadAllAsString()        -- 剩余全部 = JSON 文本
    local req = cjson.decode(js)
    if stub[type] then stub[type](req, js) end
end
```

于是完整帧：

```
+--------+---------+----------------------------+
| len:4  | proto:4 | JSON payload (len-4 bytes) |
| LE u32 | LE u32  | UTF-8, cjson 编码           |
+--------+---------+----------------------------+
        ^ len 覆盖 proto + payload
```

| 属性 | 值 | 标注 |
|---|---|---|
| 长度字段 | 4 字节，**小端 int32**，值为 `4 + #json` | 【已确认】 |
| 协议号 | 4 字节**小端 int32** | 【已确认】 |
| 载荷 | `luacjson` 的 `cjson.encode/decode`，UTF-8 JSON 文本 | 【已确认】 |
| 头常量 | `CX_MSG_HEADER_LEN = 4` | 【已确认】 |
| **字段 schema** | **完全没有**。字段名/类型/顺序全靠收发双方在 Lua 里约定 | 【已确认】 |
| 版本号 | **无** | 【已确认】 |
| 校验/CRC | **无** | 【已确认】 |
| 加密/压缩 | **无** | 【已确认】 |
| 心跳 | **未读到**（无 heartbeat 协议） | 【未读到】 |
| 最大包长 | `m_Buffer.ReserveWritable(40960)`，但 `len` 来自网络且**未做上界校验** | 【已确认】⇒ 可被用于畸形包攻击 |

### 4.1 载荷样例（逐条来自实测代码）

| 协议 | 载荷（cjson） | 出处 |
|---|---|---|
| `PTO_C2C_SIGNUP` | `{"account":"…","password":"…"}` | `scripts/server/server.lua` |
| `PTO_C2C_LOGIN` | `{"account":"…","password":"…","name":"yzxy","scene_id":186,"role_id":1,"weapon_id":40,"x":306,"y":466}` | `client/net_manager.lua` `game_server_on_connection` |
| `PTO_C2C_LOGIN`(回) | 同上去掉 password + `"pid":<int64>` | `server.lua` |
| `PTO_C2C_PLAYER_ENTER` | `{"local_pid":123,"actors":[{"0":123,"1":4,…}, …]}` | `actor_system.lua` |
| `PTO_C2C_ACTOR_ENTER` | `{"npcs":[{…属性字典…}, …]}` | `actor_system.lua` |
| `PTO_C2C_MOVE_TO_POS` | `{"pid":123,"x":306,"y":466}` | `client/addon_manager.lua` |
| `PTO_C2C_CHAT` | `{"pid":123,"msg":"hello"}` | `client/net_manager.lua` |
| `PTO_S2C_SYNC_PROPS` | `[[123,45,987.0],[123,70,0], …]`（数组的数组：pid, prop_id, value）| `server/main.lua` |
| `PTO_C2S_COMBAT_CMD` | `{"master":123,"target":456,"skill_id":20,"battle_id":7}` | `client/combat/client/combat_system.lua` |
| `PTO_S2C_COMBAT_EXECUTE` | `[{"id":…,"tid":20,"turn":1,"master":123,"targets":[456],"effects":[{"target_id":456,"combo":1,"hp_deltas":[{"target":-772.0}],"life_state":{"master":0,"target":1}}],"success":true}, …]` | `combat/server/combat_system.lua` + `skill.lua` `init_cskill` |
| `PTO_S2C_COMBAT_START`/`CREATE` | `{"pid":…,"battle":{"id":7,"actors":[{"id":123,"team_type":1,"pos_id":1},{"id":200,"team_type":2,"pos_id":1,"props":{…}}],"state":2,"turn":0}}` | `combat_system.lua` `BattleMT:Serialize` |
| `PTO_C2S_GM` | `{"type":"account_info"}` / `{"type":"exit_server"}` | `client/examples/example00.lua`、`server/gm.lua` |
| `PTO_C2S_DOSTRING` | `{"code":"player:SetProperty(PROP_SCENE_ID, 5)"}` | `server/main.lua` |
| `PTO_C2C_SAVE_ACTORS` | （空/未读字段）| `actor_system.lua` |

### 4.2 一个反直觉但重要的细节：属性字典的键是**字符串化的数组下标**

`ActorMT:GetProperties()`（`scripts/share/actor_metatable.lua`）返回 **0 基索引** 的表：

```lua
function ActorMT:GetProperties()
    local props = {}
    for prop_id = 0, PROP_COUNT - 1 do
        props[prop_id] = self:GetProperty(prop_id)
    end
    return props
end
```

`cjson` 遇到 0 基索引表会**编码成 JSON 对象**，键为 `"0".."N"`；
于是客户端必须用 `actor_info[tostring(PROP_ID)]`（即 `["0"]`）取 id —— 这在
`client/actor_manager.lua`、`client/module/summon.lua`、`server/actor_system.lua` 里一致出现。
回写时 `ActorMT:SetProperties(props)` 做 `for k,v in pairs(props) do self:SetProperty(k,v) end`，
键是字符串 `"45"`，靠 **Lua 5.3 的 `lua_tointeger` 字符串→数字强制转换** 才生效【已确认，代码如此；强转可行性属 Lua 语义，标【待验证】是否所有构建均开启】。

⇒ **这是一个脆弱点**：属性协议的键类型在同一系统内既是字符串又是数字。

---

## 5. 协议处理的分发机制

【已确认】`stub` 是**全局表**，键=协议号，值=函数；两个入口：

| 入口 | 位置 | 线程/时机 | 处理内容 |
|---|---|---|---|
| `server_thread_on_message(conn, buf, len, netq)` | `scripts/server/server.lua` | 收包回调（服务端即同一 io_context 线程）| ① `PTO_C2C_SIGNUP` 建账号 ② `PTO_C2C_LOGIN` 验账号密码 + `insert_pid_connection_pair` + 回 `PTO_C2C_LOGIN` ③ `PTO_C2S_GM` 转 `handle_gm_message` ④ **其它一律 `netq:push_back` 入队** |
| `game_server_dispatch_message(pt)` | `scripts/server/main.lua` | 每 16 ms tick，由 C++ `game_server_update()` 排空队列后调用 | `stub[type](req, js)` |

⇒ **两阶段设计**：需要在"握手期"立刻答的（注册/登录/GM）在前置回调里处理，其余进队列在游戏 tick 里处理。
这是一个**清晰、可借鉴**的分工（避免在 IO 回调里做重逻辑）。

客户端侧同构：`client/src/net.cpp` 的 `net_manager_update()` 排空队列后调 Lua `game_dispatch_message(pt)`，
分发到 `client/net_manager.lua` 的 `stub`。

---

## 6. 逐文件表

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `scripts/share/enums_protocol.lua` | `PTO_*`（63 条）、`proto_to_name`、`proto_name(proto)` | 用 C 提供的 `enum_reset()/enum_next()` 自增生成协议号；建反查表供日志 | ✅ | **「协议号 = 单一 Lua 真源 + 名字反查表」** 正是 JSTM 缺的：JSTM 有 1652 个 CMD 却只有 `all_proto.luac` 的中文名，没有统一常量模块。可在 JSTM 侧由 `fields.json` **生成**一个同风格的 `enums_protocol.lua`，两边共用、日志自动可读 |
| `scripts/share/enums_protocol.lua` | 命名约定 `PTO_C2C/C2S/S2C_*` | 前缀表达方向；`C2C` 实为"广播给所有客户端" | ⚠️ | **方向前缀思想值得学**，但 JSTM 的 CMD 是**数字段**（20000 战斗 / 10500 背包 / 11700 聚宝盆…，见 `analysis/jstm_1.4.9/protocol_index.md`），**段号即域**是 JSTM 已有的更强组织方式 ⇒ 不要引入 CXEngine 命名法覆盖既有段约定 |
| `scripts/generator/protocol.lua` | `gen_protocol()` | 沙箱 `loadfile` 求值 → 按值排序 → 写 `protocol.h`(`enum EProtocalType`) + `protocol.cpp`(`REG_ENUM`) | ⚠️ | **「定义一次、生成多端」的机制值得学**，但方向必须反过来（JSTM 从客户端 `cmd_resolve_*.luac` 生成服务端）；直接照搬会生成"服务端→客户端"文件，而 JSTM 客户端是只读 APK |
| `scripts/generator/protocol.lua` | `vfs_makepath` + 沙箱 `__index=_ENV` | 用 `setmetatable(module,{__index=_ENV})` 让被求值的枚举文件能访问全局 | ✅ | **沙箱求值 + `__index` 回退**是读不可信/纯声明脚本的安全模式，值得借鉴 |
| `common/src/protocol.h` | `CX_MSG_HEADER_LEN`, `luaopen_protocol` | 入库的是手写桩（只有头长常量）；完整 enum 由 generator 产物覆盖 | ❌ | **生成产物未入库**导致仓库状态不自洽（编译期若非先跑 generator，`EProtocalType` 不存在）。反面教材 |
| `common/src/protocol.cpp` | `luaopen_protocol()` → `REG_ENUM` | `lua_pushinteger + lua_setglobal` 把 C 枚举暴露成 Lua 全局 | ⚠️ | 宏 `REG_ENUM` 很简洁；但**把常量灌成 Lua 全局**在 JSTM（LuaJIT + 已有大量全局）会加剧命名冲突 |
| `server/src/server.cpp` | `GameSession::ReadHeader()/ReadPack()`, `Send()` | 4 字节长度帧 + 异步读；读满后直接 `lua_pcall(server_thread_on_message)` | ⚠️ | **「长度前缀 + 异步读」** 思路通用；但 `len` **无上界校验**、载荷**未做 base 校验** ⇒ 不可照抄实现 |
| `server/src/server.cpp` | `GameServer::SendMessageToPlayer(pid,proto,msg)` / `…ToPlayers` / `net_send_message_to_all_players_in_c` | `buf.Write(proto)+Write(json)+Prepend(len)`；按 pid 查 `g_PlayerConnections` 发送；`ToAll` 遍历 map | ⚠️ | 「proto+json+长度前缀」极简，**对 JSTM 的调试太方便了**（抓包即明文可读）；但**生产不可用**：JSTM 是 `[u32 BE len][u16 BE cmd][body]` 二进制，**长度与命令号都是大端且 cmd 是 u16**，与 CXEngine `[LE u32][LE u32][json]` 三项全不同 ⇒ **不可混用，只能借鉴"日志可读"这一目标** |
| `server/src/server.cpp` | `insert_pid_connection_pair` / `erase_pid_connection_pair` | Lua 侧维护 `pid → GameSession*` 映射（userdata 直传指针）| ⚠️ | **「会话对象暴露给 Lua，由 Lua 决定绑定关系」** 便于调试/多开；但**Lua 里存裸 C++ 指针**（`(GameSession*)lua_touserdata`）无生命周期保护 ⇒ 危险 |
| `scripts/server/main.lua` | `game_server_dispatch_message(pt)` | `ReadAsInt` + `ReadAllAsString` + `cjson.decode` + `stub[type](req,js)` | ✅ | **"协议号 → 处理函数表"的零样板分发**比 `if/elif` 长链可维护得多。JSTM 侧 `mock_server.py` 目前偏 `if cmd == …` 链（见 `battle_chain_verified.md` 里 `行 2371 if cmd == 20002`）⇒ **这是最该学的一条** |
| `scripts/server/main.lua` | `stub[PTO_C2S_DOSTRING/PLAYER_DOSTRING/ACTOR_DOSTRING]` | `load(req.code,'@client','bt',_ENV)` 后直接调用 | ⛔ | **服务端远程执行客户端 Lua**：`PTO_C2S_DOSTRING` 用 `_ENV`（全权限），`PLAYER_DOSTRING`/`ACTOR_DOSTRING` 才注入 `{player=…}`/`{actor=…}` 沙箱。这是**作弊/后门**，任何情况不得进入 JSTM |
| `scripts/client/net_manager.lua` | `game_dispatch_message(pt)`, `net_send_message(proto,msg)` | 客户端对称分发；`stub` 来自 `net_manager_stub()` 共享表 | ✅ | 与 `server/main.lua` 同构 ⇒ **一套分发骨架复用两端**；JSTM 若做"同进程模拟器"，这点很有用 |
| `scripts/server/server.lua` | `net_send_message*` 三个封装 | 打印 `proto_name(proto)` 后再调 C | ✅ | **发送前统一打印协议名**使日志自解释；JSTM 目前靠抓包脚本，若在发送出口统一打名会省很多事 |
| `scripts/share/vfs.lua` | `vfs_getpath/get_tsvpath/get_luapath` | 路径前缀统一 | ✅ | 与协议无关但同属 share；见 `architecture.md` |
| `assets/doc/LuaAPI.md` | `enum_reset`, `enum_next`, `command_arg_*`, `net_thread_queue` 等 | 手工维护的 Lua 可调 C 函数清单（约 500 行） | ✅ | **「C 侧能力清单文档化」**值得学：JSTM 逆向时最缺的就是"客户端 Lua 能调哪些原生函数"的权威清单（本工作区已有 `native_callback_findings.md`，可与此法对齐） |

---

## 7. ★ 对 JSTM 的协议层建议（结论段）

| # | 建议 | 依据 | 置信 |
|---|---|---|---|
| 1 | **建一个 `enums_protocol.lua` 级别的"C2S/S2C 常量单一真源"**，从 `protocol/fields.json`（3553 条）自动生成，供 mock_server 与测试脚本共用；名字反查表用于日志 | CXEngine 的 `proto_name()` 让每条日志自带协议名 | 高 |
| 2 | **保留 JSTM 既有数字段约定（10500 背包 / 13000 副本 / 20000 战斗）**，只补名字，不引入 `PTO_*` 命名法 | JSTM 段号本身即业务域划分，比前缀更强 | 高 |
| 3 | **把 `mock_server.py` 的 `if cmd == …` 长链改为 `handlers[cmd] = fn` 注册表**，并保留"握手期立即处理 / 主循环派发"两阶段 | `server/main.lua` 的 `stub` + `server.lua` 的两阶段 | 高 |
| 4 | **线格式绝不可改成 CXEngine 的 JSON**：JSTM 已实测 `[u32 BE len][u16 BE cmd][body]`，改动=客户端即刻不兼容 | CXEngine 是 `[LE u32][LE u32][json]`，三项全不同 | 高 |
| 5 | 若要"抓包可读"，**在 JSTM 服务端发送出口做字段级解码打印**（已有 `tools/proto_spec.py`），而不是改线格式 | CXEngine 靠明文 JSON 换可读性，代价是体积/安全 | 高 |
| 6 | **协议常量与结构体定义必须两边都入库**，不要像 CXEngine 那样只入库生成的残缺桩 | `common/src/protocol.h` 仅含 `CX_MSG_HEADER_LEN` | 中 |
| 7 | **明确禁止 `dostring` 类协议**；GM 能力必须走带鉴权的最小命令集 | `stub[PTO_C2S_DOSTRING]` 用 `_ENV` | 高 |

### 未读到 / 待验证（协议层）

- 【未知】`PTO_*` 的**具体数值**（`enum_reset` 起始值在 `internals/cxlua`，不在 ZIP；生成物 `protocol.h` 未入库）。
- 【未知】是否存在**心跳/超时/断线重连**协议——63 条清单里未见，但 `client/net.cpp` 有 `net_manager_reconnect()`，说明重连是客户端主动行为。【未读到】服务端侧的重连处理。
- 【未读到】`PTO_C2S_SWITCH_SCENE`、`PTO_C2S_NPC_DIALOG`、`PTO_C2S_FETCH_ACCOUNT_INFO`、`PTO_C2C_LOGOUT` 的服务端处理函数。
