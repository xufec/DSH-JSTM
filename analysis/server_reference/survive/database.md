# Survive 数据持久化审计（逐文件 · 类/函数级）

> 对象：`common/{db.lua,config.lua,idmgr.lua}`、`lua/redis.lua`、`groupserver/*.lua` 的 `DbStr/DbSave/Save`、`gateserver/gateserver.lua` 的登录查库、`daemon.lua` 的状态写入、`setconfig.lua`
> 状态标记：【已确认】【待验证】【未知】；方法：`zipfile` 按需读取原文（**未修改任何文件**）
> 对照目标：**JSTM**（SQLite `roles.db`，10 张表；`role_persistence.md` 已存在，**本轮未读**）

---

## 一、结论速览

| 项 | 结论 | 状态 |
|---|---|---|
| 存储引擎 | **redis / ssdb**（README 说"安装 ssdb **或** redis"；代码用 `CRedis` 驱动 + Redis 文本命令协议） | 【已确认】 |
| 连接封装 | `common/db.lua`（全局单连接 + 自动重连）+ `lua/redis.lua`（协程化同步/异步命令） | 【已确认】 |
| 键设计 | ① **`deploy`**（hash）存全服部署表 ② **`<actname>`**（string）→ chaid ③ **`nickname`**（hash）昵称占用 ④ **`chaid`**（counter）角色 id 自增 ⑤ **`chaid:<chaid>`**（hash）**角色全部数据** | 【已确认】 |
| 角色数据形态 | **每个模块一个 hash field，值是一整段 `cjson`（或 base64(cjson)）字符串** | 【已确认】 |
| **gameserver 完全不落库** | `gameserver/gameserver.lua` **没有 `Db.Init`、没 require `common.db`**；场景状态全在内存 | 【已确认】 |
| 写时机 | **各业务模块在自己的操作后立即 `DbSave()`**（异步 `CommandAsync`），靠 `dbchange` / `flag` 脏标记去重 | 【已确认】 |
| 事务 | **无**（没有 `MULTI/EXEC`，没有回滚）；单次操作的多字段写入靠**一条 `hmset`** 凑原子性 | 【已确认】 |
| 关服保存 | **无**（`Exit()` 只置 stop 标志 + yield，不做全量 flush） | 【已确认】 |
| 离线数据 | 只在**登录时读、登出时不写**（写已分散在各操作） | 【已确认】 |
| 分库/分表 | 文档描述"账号库唯一 + 角色库按 chaid hash 可多台"，**代码里只有一个 `toredis` 单连接** ⇒ **分库未实现** | 【已确认】 |
| 对 JSTM 的价值 | **「按域拆 field + JSON 值 + 脏标记 + 操作即落库」的思想可用；redis 文本协议拼接、base64 兜底、无事务、无关服 flush 都不可学** | 【已确认】 |

---

## 二、连接层

### 2.1 `common/db.lua`（全局单连接）【已确认】

| 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|
| `connect_to_redis(ip,port)` | `Sche.Spawn` 死循环：`Redis.Connect(ip,port, on_disconnected)`，成功即 `break`，失败 `Sleep(1000)` 重试；**断线回调里再调 `connect_to_redis` 实现自动重连**（除非 `activeclose`） | ✅ 适合（思想） | ★ **"断线自动重连 + 重连前通知"**是必须的；JSTM 用 SQLite 无网络断线问题，但**"DB 不可用时降级/重试而不是崩"**同样适用 |
| `CommandSync(str)` | 直接转发给 `toredis:CommandSync(str)`；未连接返回 `"redis invaild"` | ⚠️ 部分 | ⚠️ **命令靠字符串拼接**（见 §6 风险） |
| `CommandAsync(str,callback)` | 同上（异步），**本项目几乎所有写操作都用它** | ⚠️ 部分 | **异步写 + 不检查返回值** ⇒ **写失败被静默忽略**（`DbSave` 都不看返回值）【已确认】 |
| `Init(ip,port)` | `if not isInit then isInit=true; connect_to_redis(...) end` | ⚠️ 部分 | **`isInit` 置位后即使连不上也不会重试 Init** ⇒ 只能靠内部协程重试 | 
| `Finish()` | 返回 `toredis`（**当"是否连上"的探针用**，见 `groupserver.lua: while not Db.Finish() do Sche.Yield() end`） | ⚠️ | 命名与语义不符（`Finish` = "连接完成?"），可读性差 |

### 2.2 `lua/redis.lua`（协程化）【已确认】

| 函数 | 机制 |
|---|---|
| `Connect(ip,port,on_disconnected)` | 构造 `cbObj{co=Running(), __cb_connect, __on_disconnected}` → `CRedis.redis_connect(ip,port,cbObj)` → `Sche.Block()` 等回调 → 返回 `redisconn` |
| `redisconn:CommandSync(cmd)` | `cbObj{co=Running(), __callback=function(self,error,result) self.err=error; self.result=result; Sche.WakeUp(self.co) end}` → `CRedis.redisCommandSync(conn,cmd,cbObj)` → `Sche.Block()` → 返回 `(err, result)` |
| `redisconn:CommandAsync(cmd,callback)` | `CRedis.redisCommandAsync(conn,cmd,cbObj)`，回调签名 `__callback = callback` |
| `redisconn:Close()` | 置 `activeclose` 后 `CRedis.close` |

**★ 关键点**：**所有 SQL/命令都是纯文本字符串**，返回值由 C 模块解析（`result` 是数组/字符串）。
⇒ **JSTM 用 Python `sqlite3` 时，这一层完全没有对应物**，应直接参数化查询（避免拼接注入/转义问题）。

### 2.3 `common/config.lua`（配置也从 DB 读）【已确认】
```lua
Init(key, ip, port)
  → connect_to_redis(ip,port)（同样死循环重试）
  → while not toredis do Sche.Sleep(100) end
  → toredis:CommandSync("hmget deploy " .. key)
  → deployment = Cjson.decode(result[1])
  → toredis:Close()                      -- ★ 读完就关连接
Get(key) → deployment[key]               -- 例：Get("gate1") = {"192.168.82.128", 8010}
```
⚠️ **`deployment` 是模块级单例**（`if not deployment then ... else return true,nil end`）⇒ 一个进程只能读一份部署表【已确认】。

---

## 三、键空间（全量，实测）

| 键 | 类型 | 写入方 | 读取方 | 值样例 | 状态 |
|---|---|---|---|---|---|
| `deploy` | hash | `setconfig.lua`（`hmset deploy 测试1服 <json>`）；`daemon.lua` 另写 `set deployment <json>`（**另一个键**） | `common/config.lua:hmget deploy <区名>` | `{"db":["127.0.0.1",6379],"group":[...],"gate1":[...],"game1":[...]}` | 【已确认】 |
| `<actname>` | string | `groupplayer.lua:CMD_CG_CREATE` → `set <actname> <chaid>` | `gateserver.lua:CMD_CA_LOGIN` → `get <actname>` | `"10001"` | 【已确认】 |
| `nickname` | hash | `groupplayer.lua:checkDuplicateName` → `hmset nickname <昵称> 1` | 同上 `hmget nickname <昵称>` | `1` | 【已确认】 |
| `chaid` | counter | `CMD_CG_CREATE` → `incr chaid` | 同 | 自增整数 | 【已确认】 |
| `chaid:<chaid>` | hash | 各 group 模块的 `DbSave/Save` | `PlayerLogin` → 一条 `hmget` 读 9 个 field | 见 §4 | 【已确认】 |
| `MachineStatus` | hash | `daemon.lua`（每秒） | PHP 管理台 | `hmset MachineStatus 192.168.0.87 <base64(cjson({machine,process}))>` | 【已确认】 |
| `deployment` | string | `daemon.lua`（`set deployment <cjson>`） | **未读到读取方**（PHP？） | 部署表 JSON | 【已确认】写入 / 【未知】读取 |
| ~~`<区名>-toredis` / `-togroup` / `-gate1` / `-game1`~~ | — | **被注释掉的旧方案** | — | — | 【已确认】历史遗留 |

**★ 观察**：
1. **一个角色 = 一个 hash，9 个 field**（`chaid:<id>`）；**hash field 名 = 模块名**，非常直观。
2. 「**账号 → 角色 id**」与「**昵称占用**」**各占一个独立键**，而不是存在角色 hash 里 ⇒ **登录时只需 1 次 `get`、创角查重只需 1 次 `hmget`**，不用扫表。
⇒ **这两点在 SQLite 里对应"两列唯一索引"**；JSTM 应把 `account→role_id` 与 `nickname` 都建 `UNIQUE` 索引，可得到同样效果且更强（有事务）。
3. ⚠️ **`chaid` 是全局自增计数器**，`incr` 不可回退：创角走到一半失败会**永久消耗一个 id**（`CMD_CG_CREATE` 里 `incr` 成功但 `hmset` 失败 ⇒ 产生"有 id 无角色"的孤儿）【已确认】。

---

## 四、`chaid:<chaid>` 的 9 个 field（**角色数据的完整定义**）

| field | 写入（`DbStr`/`Save`） | 读取（`PlayerLogin`） | 值结构 | 状态 |
|---|---|---|---|---|
| `nickname` | 创角时 `hmset chaid:<id> nickname <?>` | `result[1]`（**直接当字符串**） | 字符串 | 【已确认】 |
| `avatarid` | 同上 | `result[2]`（`tonumber`） | 数字 | 【已确认】 |
| `chainfo` | `groupserver/attr.lua:DbStr` → `cjson.encode(前 23 项数组)` | `result[3]` → `Cjson.decode` → `Attr.New():Init(ply, ...)` | **JSON 数组，下标即 `name2idx` 序号** | 【已确认】 |
| `bag` | `groupserver/bag.lua:DbStr` → `cjson.encode({size=n, [i]={id,count,attr?}})` | `result[4]` → `Bag.New():Init(ply, Cjson.decode(...))` | **JSON 对象（数字键被 cjson 转成字符串键，读回时 `tonumber(k)`）** | 【已确认】 |
| `skills` | `groupserver/skill.lua:DbStr` → `cjson.encode({{id,level},...})` | `result[5]` | **JSON 数组的数组** | 【已确认】 |
| `everydaysign` | `everydaysignin.lua:DbStr` → `cjson.encode({count,lastreset,lastsign})` | `result[6]`（可为 nil） | JSON 对象 | 【已确认】 |
| `everydaytask` | `everydaytask.lua:DbStr` → `cjson.encode({lastreset,tasks})` | `result[7]`（可为 nil） | JSON 对象 | 【已确认】 |
| `achievement` | `achievement.lua:DbStr` → `cjson.encode({[id]={achived,awarded}})` | `result[8]`（可为 nil） | JSON 对象 | 【已确认】 |
| `mail` | `mail.lua:DbStr` → **`CBase64.encode(cjson.encode(list))`** | `result[9]` → `CBase64.decode` → `Cjson.decode` | **base64(JSON)** | 【已确认】 |
| ~~`friends`~~ | `friends.lua` 声称 `hmset chaid:<id> friends ...` | **`PlayerLogin` 的 `hmget` 列表里没有 `friends`** ⇒ **好友数据既不读也不写** | — | 【已确认】⚠️ |
| ~~`homeisland` / `shop` / `tutorial`~~ | 无独立 field（家园/引导的状态**存在 `chainfo` 的属性里**：`fishing_start/gather_start/sit_start/introduce_step`） | — | — | 【已确认】 |

### 4.1 登录时的读库（**一条 `hmget` 读全部**）【已确认】
```lua
Db.CommandSync("hmget chaid:" .. chaid ..
    " nickname avatarid chainfo bag skills everydaysign everydaytask achievement mail")
-- 校验：if not result or not result[1] or not result[2] or not result[3]
--                or not result[4] or not result[5] then  → NotifyCreate()  end
```
★ **一次往返取全角色**是很好的设计（避免 N 次往返）；⚠️ 但**前 5 个字段任一为空就判定"需要创角"** —— 若 `bag` 因某次写失败而丢失，玩家会被**要求重新创角**（`nickname` 已占用 ⇒ 卡死）【已确认】。

### 4.2 创角时的写库（**一条 `hmset` 写 8 个字段**）【已确认】
```lua
Db.CommandSync(string.format(
  "hmset chaid:%u nickname %s avatarid %u chainfo %s bag %s skills %s everydaysign %s everydaytask %s achievement %s",
  ply.chaid, ply.nickname, ply.avatarid, ply.attr:DbStr(), ply.bag:DbStr(),
  ply.skills:DbStr(), ply.sign:DbStr(), ply.task:DbStr(), ply.achieve:DbStr()))
```
★ **一次往返写全部初始数据**（原子性由单条 `hmset` 保证，redis 单命令原子）；
⚠️ **不含 `mail`**（初始无邮件，`PlayerLogin` 里 `mail` 缺失是可接受的）；
⚠️ **`%s` 直接拼 JSON 字符串**：若昵称含空格/引号会**破坏命令**（⚠️ 昵称来自客户端且**未做过滤/转义**）【已确认】。

---

## 五、各模块的持久化实现（逐文件）

| 文件 | 函数 | 机制 | 是否适合 JSTM | 原因 |
|---|---|---|---|---|
| `groupserver/attr.lua` | `DbStr()` | `t = {}; for i=1,Name2idx.attr_db_save do t[i]=self.attr[i] or 0 end; return Cjson.encode(t)` —— **只存前 23 项**（派生属性不落库） | ✅ **高度适合** | ★ **"只持久化输入、派生属性每次重算"**是防数据腐化的根本手段；JSTM 的 `role_attr` 若存了 `attack/maxlife` 等派生值，建议改掉 |
| | `DbSave()` | `if self.dbchange then hmset chaid:<id> chainfo <json>; self.dbchange=false end` | ✅ 适合（思想） | ★ **脏标记去重**：只有 `Set/Add/Sub` 改过才写 |
| `groupserver/bag.lua` | `DbStr()` | `{size=n}` + 每个非空格 `b[i]={id,count,attr?}` → `Cjson.encode` | ✅ 适合 | 稀疏结构用 JSON 表达，直观 |
| | `Save()` | `if self.dbchange then hmset chaid:<id> bag <json>; dbchange=false end` | ✅ 适合 | |
| | `Init(ply,bag)` | `for k,v in pairs(bag) do if k ~= "size" then self.bag[tonumber(k)] = Item.New(...) end end` | ✅ 适合 | ⚠️ **依赖 cjson 把数字键编码成字符串键**再 `tonumber` 转回 ⇒ 换 JSON 库会出问题（Python 里 `json` 的键也全是字符串，同样要转） |
| `groupserver/skill.lua` | `DbStr/Save` | `Cjson.encode({{id,level},...})` → `hmset ... skills` | ✅ 适合 | ⚠️ `Save()` 里留了一行 `print(cmd)` **打印整条命令**（含全部数据）【已确认】 |
| `groupserver/everydaysignin.lua` | `DbStr/DbSave` | `{count,lastreset,lastsign}` → json | ✅ 适合 | 另有 `CheckReset` 在跨月时重置 |
| `groupserver/everydaytask.lua` | `DbStr/DbSave` | `{lastreset, tasks={[i]={type,counter,awarded}}}` → json | ⚠️ 部分 | ⚠️ **每次 `OnEvent` 都 `DbSave`**（高频事件把 DB 当计数器写）⇒ JSTM 应内存累积 + 定时 flush |
| `groupserver/achievement.lua` | `DbStr/DbSave` | `{[id]={achived,awarded}}` → json | ✅ 适合 | |
| `groupserver/mail.lua` | `DbStr()` | **`CBase64.encode(Cjson.encode(list))`** | ❌ 不适合 | ★ 根因：**把结构化数据拼进 redis 文本协议**，引号/换行会破坏命令 ⇒ 用 base64 兜底。**JSTM 用 SQLite 完全不需要**，直接存 JSON 列或专用表 |
| | `Save()` | `hmset chaid:<id> mail <base64>` | ❌ | 同上；且**邮件 id 用 `os.time():counter` 会冲突**（见 `role.md` §6.5） |
| `groupserver/friends.lua` | `DbStr/DbSave` | 声称 `hmset chaid:<id> friends <json>` | ❌ **坏** | ⚠️ **`DbSave` 用 `self.owner.chaid`，而 `Init` 设的是 `self.ply`** ⇒ `self.owner` 为 nil ⇒ **好友落库必报错**；且 `PlayerLogin` 的 `hmget` **不含 `friends`** ⇒ **好友完全不持久化**【已确认】 |
| `groupserver/groupplayer.lua` | `CMD_CG_CREATE` | 一条 `hmset` 写 8 field（见 §4.2） | ✅ 适合（思想） | ★ 原子初始快照 |
| | `PlayerLogin` | 一条 `hmget` 读 9 field（见 §4.1） | ✅ 适合（思想） | ★ 单次往返 |
| | `_checkDuplicateName` | `hmget nickname <名>` → 有则失败 → `hmset nickname <名> 1`（**用 `lua/lock.lua` 保护临界区**） | ⚠️ 部分 | ★ 思想对（唯一索引）；⚠️ 实现**没有"删除/释放昵称"的路径**（改昵称后旧昵称永久占用），且**加锁仅在本进程内有效**（多 groupserver 会失效——虽然设计上只一台） |
| `groupserver/map.lua` | 全部 | **不落库**（场景实例是内存账本 `maps[type][id]`） | ❌ 不适合（但项目如此） | ⚠️ **groupserver 重启后所有场景实例账本丢失**，而 gameserver 里的图还在 ⇒ **状态不一致**（`GetInstanceByType` 靠"RPC 失败"间接发现）。JSTM 单进程无此问题 |
| `groupserver/survive.lua` | 全部 | **不落库**（`nextTime/applyDeadLine/applyers/waitForTransfer` 全在内存） | ⚠️ | ⚠️ **进程重启 ⇒ 活动时间与报名全部丢失**；JSTM 若做限时活动，应把**时间表**与**报名名单**落库 |
| `gateserver/gateserver.lua` | `CMD_CA_LOGIN` | `Db.CommandSync("get " .. actname)` 取 chaid | ⚠️ 部分 | ★ 只查一个键就完成"有没有角色"的判断（因为 `<actname>` 键的存在即代表已创角）；⚠️ **无密码/无 token 校验**（README 明说忽略密码） |
| | `Db.Init(redis_ip,redis_port)` | gate 也连 DB（**只为了 `get <actname>`**） | ⚠️ 部分 | ★ 思想："轻量查询放到离客户端近的节点"；⚠️ 让 gate 直连 DB 会**破坏"只有 group 碰 DB"的边界**，JSTM 不必如此（单进程） |
| `gameserver/*` | **无任何 DB 调用** | — | ✅（架构上） | ★ **"场景进程无状态"** 是好设计（可随意重启/扩容，数据只在 group）；`gameserver/battlebag.lua` 里的 `Save()` 位于**被注释掉的代码块**中，**不是活代码**【已确认】 |
| `daemon.lua` | 主循环 | 每秒 `C.Top()` → 解析进程表 → `hmset MachineStatus <ip> <base64(cjson({machine,process}))>`；启动时 `set deployment <cjson>` | ⚠️ 部分 | ★ **"运维状态上报中心库 + Web 读同一份数据"** 思想可用；⚠️ **ip 硬编码 `192.168.0.87`**、`collectgarbage("collect")` 每秒一次 | 
| `setconfig.lua` | 顶层 | `Db.Init(127.0.0.1,6379)` → 等连接 → `hmset deploy 测试1服 <cjson(deployment)>` | ⚠️ 部分 | ★ **"部署表入库、进程按名取址"** 思想可用（见 `architecture.md` §4） |

---

## 六、风险清单（**JSTM 必须避免的**）

| 风险 | 证据 | 影响 | 状态 |
|---|---|---|---|
| **命令字符串拼接（无参数化/转义）** | 全项目 `hmset ... <cjson>` / `get <actname>` / `hmget nickname <昵称>` | 昵称含空格/引号/换行 ⇒ **命令被截断或注入**；JSON 里的引号能通过只因 JSON 会被 redis 当整体参数？**不会** —— redis 文本协议按空格分词 ⇒ **含空格的昵称必然破坏命令**（`hmset nickname 张 三 1`）【已确认】 | 🔴 高危 |
| **无事务 / 无回滚** | `incr chaid` 与后续 `hmset` 分离；`AddItems` 校验与写入之间无事务 | 产生"有 chaid 无角色"孤儿；并发下可重复发奖 | 🔴 |
| **异步写不检查返回值** | 所有 `Db.CommandAsync(cmd)` 无回调、无错误处理 | **写失败被静默忽略**（存档悄悄丢失） | 🔴 |
| **无关服 flush / 无定时全量保存** | `Exit()` 只置标志 | 依赖"每操作即写"才不丢数据；但 `everydaytask` 之外仍有遗漏（如 `groupplayer.lua:CMD_CG_COMMIT_SPVE` 已写、`friends` 未写） | 🟡 |
| **派生属性与输入混存的风险已被规避** | `attr_db_save=23` + 登录 `CalAttr` | ✅ 这是**正面**做法 | ✅ |
| **`chainfo` 是"无键数组"** | `cjson.encode({a1,a2,...a23})` | **`name2idx.lua` 的顺序一旦调整，所有老存档都会错位** | 🔴 **JSTM 若照抄：必须禁止"用数组下标存属性"**，应存 `{"level":1,"power":50,...}` 键值形式 |
| **`bag` 的键是数字** | cjson 把 `[2]` 编成 `"2"`，读回 `tonumber` | 换 JSON 库/换语言时易错 | 🟡 |
| **`mail` 用 base64 兜底** | `CBase64.encode(cjson.encode(list))` | 存储膨胀 33%、不可读、不可查询 | 🟡 |
| **昵称占用键无删除路径** | `nickname` hash 只写不删 | 昵称永久占用（无改名/回收） | 🟡 |
| **`PlayerLogin` 关键字段缺失 ⇒ 要求重创角** | `if not result[1..5] then NotifyCreate()` | 存档部分损坏 ⇒ 玩家卡死在创角（昵称还被占用） | 🔴 |
| **多进程写同一 hash 无并发控制** | 设计上 group 只一台 ⇒ 侥幸安全 | 若按文档扩多台 group（`daemon.lua` 里配了 group1/group2/测试3区）会立刻冲突 | 🟡 |
| **`gameserver` 无状态但 groupserver 的场景账本在内存** | `groupserver/map.lua` 的 `maps` | 重启后账本与 game 实况不一致 | 🟡 |
| **无时间戳/版本号字段** | 角色 hash 里没有任何 `updated_at` / `schema_version` | 无法做增量备份、无法迁移表结构 | 🟡 **JSTM 应加 `updated_at` 与 `data_version`** |

---

## 七、对 JSTM 的建议（持久化层）

| 优先级 | 建议 | 依据 | 说明 |
|---|---|---|---|
| **P0** | **属性只存"输入项"，派生项每次重算** | `attr_db_save` + 登录 `CalAttr` | 防"存档与公式不一致"的祖传 bug |
| **P0** | **属性存档用"命名字段"而不是"数组下标"** | Survive 用无键数组（**反面教材**） | JSTM 应存 `{"level":..,"power":..}` 或 SQLite 列；顺序调整不应破坏老档 |
| **P0** | **参数化写入 + 事务** | Survive 全靠字符串拼接（**反面教材**） | SQLite 用 `?` 占位 + `BEGIN/COMMIT`；创角（account→id + 角色行 + 昵称唯一）必须是**一个事务** |
| **P0** | **关键写操作要检查成败** | `Db.CommandAsync` 无回调（**反面教材**） | 至少记录失败日志 + 关键路径用同步写 |
| **P1** | **"一个角色 = 一次读写"**：登录一条查询、创角一条写入 | `hmget chaid:<id> <9 fields>` / `hmset`（8 fields） | 减少往返；SQLite 里是一次多列 `SELECT`/`INSERT` |
| **P1** | **按域拆存储单元**（角色/背包/技能/任务/成就 各一块） | 每模块一个 hash field + 各自 `DbSave` | 便于"哪块变了只写哪块"；JSTM 已接近（多表），可加**每表脏标记** |
| **P1** | **脏标记 + 合并写**（同一 tick 内多次改动只落一次库） | `dbchange` / `flag` | 避免高频事件打爆 DB |
| **P1** | **加 `updated_at` + `data_version`** | Survive 完全没有 | 便于备份、迁移、回档 |
| **P2** | **"账号→角色"与"昵称占用"建 UNIQUE 索引** | `<actname>` / `nickname` 两个独立键 | SQLite 天然更强（有事务） |
| **P2** | **场景进程不要碰 DB**（数据只在逻辑层） | gameserver 无 DB 调用 | 若 JSTM 将来拆场景模块，保持"场景无状态" |
| **P2** | **运维状态上报到一张表**（进程/在线/负载） | `daemon.lua:MachineStatus` | 供 GM 后台读 |
| **禁止** | 🚫 抄 redis 键名（`chaid:<id>` / `deploy` / `MachineStatus`）、抄 JSON 结构、抄 `name2idx` 下标顺序 | — | JSTM 的表结构应服务自己的协议与查询 |
| **禁止** | 🚫 用 base64 包 JSON 存邮件 | `mail.lua` | 反面教材 |
| **禁止** | 🚫 用"全局自增 `incr chaid` 且无回滚" | `CMD_CG_CREATE` | JSTM 用 SQLite `AUTOINCREMENT` + 事务即可 |

---

## 八、【未读到】/【未知】

| 项 | 状态 |
|---|---|
| **JSTM 现有持久化实现** | 【未读】`analysis/1.4.9/role/role_persistence.md`、`server/mock_server.py` 的 DB 层、`server/state/roles.db` 的 10 张表结构 **本轮均未打开** |
| redis 的真实实现是 **redis 还是 ssdb** | 【待验证】README 说二者皆可；`CRedis` 走 Redis 协议 ⇒ 应是 redis（或 ssdb 的 redis 兼容模式） |
| `ssdb.conf` / redis 配置 | 【未读到】ZIP 内无 |
| `deployment` 键（`daemon.lua` 写的那个）谁读 | 【未知】推测是 PHP 管理台 |
| `php/` 里的 DB 操作 | 【未读到】（1267 文件，本轮未审计） |
| 是否有备份/定时 dump | 【未知】ZIP 内无相关脚本（`daemon.lua` 只上报状态，不备份） |
| `CBase64` 的实现 | 【未读到】（`common/encode.c`/`decode.c` 是 joseph werle 的 b64 实现，**但 CBase64 是 distri 内建，未必是同一份**） |
| `CTimeUtil` 的时间语义 | 【待验证】见 `role.md` |
| 是否曾用 ssdb 的 `hsize`/`zset` 等特性 | 【已确认】**只用了 string / hash / incr** 三种操作（`get/set/hmset/hmget/incr`） |
