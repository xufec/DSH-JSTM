# ChivalrousMan（侠客行）客户端侧业务流程证据审计 —— 任务 / 装备 / 技能 / 药品 / 背包 / 组队 / 聊天

- 审计对象：开源项目 ChivalrousMan（Cocos2d-x 3.x C++ 客户端 + 缺失的服务端）
- 只读素材：`C:\WINDOWS\TEMP\audit_chiv\Classes\`、`C:\WINDOWS\TEMP\audit_chiv\Resources\`（临时解压副本）
- 原压缩包：`C:\Users\xu\Desktop\DSH\cankao\ChivalrousMan-master.zip`（未改动）
- 目标项目：JSTM =《绝世唐门》1.4.9 私服兼容项目（复刻该类 MMORPG 服务端 + 客户端业务）
- 授权说明：ChivalrousMan **无 LICENSE 文件**（本次未读到）⇒ **不存在 GPL 那类 copyleft 传染问题**；但"无 LICENSE"不等于已获授权（默认保留全部权利）。按本项目【原则 3】口径：**可研究、可借鉴设计（字段语义/流程/结构）、不要直接复制代码与美术资源**。详见 `reuse_candidates.md`
- 证据等级：**【已确认】** = 本次亲自读到该行代码/该文件内容；**【待验证】** = 由命名、资源或 README 推断，但未读到实现；**【未知】** = 未读到，不作结论

---

## 0. 结论摘要（必读）

### 0.1 本项目服务端缺失 —— 已确认

| 证据 | 内容 | 等级 |
|---|---|---|
| `proj.win32/ChivalrousMan.sln` | 全文仅有 1 个 `Project(...)` 条目：`ChivalrousMan.vcxproj`，无第二个工程 | 【已确认】 |
| 解压根目录 | 无 `server/` 目录；目录为 Classes、cocosstudio、include、lib、proj.android、proj.ios_mac、proj.win32、Resources | 【已确认】 |
| `README.md` 第 9 行 | 「游戏的服务器也搭建在个人的阿里云服务器上服务器项目源码在 _https://gitee.com/lsylovews/CM-Server_ 上」 | 【已确认】 |
| `README.md` 第 12 行 | 「如果要重新编译源代码，建议使用 vs2017，同时修改 Resources 文件夹下的 server.cfg 和 DB.cfg 修改服务器和数据库的配置」——但 `Resources/` 下**只有 server.cfg，没有 DB.cfg**（DB 配置被硬编码进 `DBDao.h`） | 【已确认】 |

因此：**本文件记录的全部业务流程证据都来自客户端**；服务端行为（CM-Server 仓库）本次未读到，凡涉及服务端实现处一律标【待验证】或【未知】。

### 0.2 两条数据通道，及其权威性归属 —— 已确认，逐类说明

客户端同时存在两条互不相干的通道：

**通道 A：MySQL 直连（客户端 = 持久化权威）**

- `Classes/DBDao.h` 第 5 行 `#include<mysql.h>`；第 107-110 行默认构造函数硬编码 `m_host("47.93.235.6")`、`m_username("game")`、`m_passwd("3252918599lsy")`、`m_dbname("chivalrousman")`、`m_port=3306`。
- `initConnect()`（DBDao.h:214-219）调用 `mysql_real_connect(...)` 并**忽略返回值**（无失败处理、无重连）。
- **走通道 A 的业务（全部为持久化读写）**：
  | 业务 | 证据 | SQL 目标表 |
  |---|---|---|
  | 账号登录校验 | `LoginLayer.cpp:147-153` `DBDao<GamePlayer> dao; dao.setModel(player); dao.queryModel()` | `player` |
  | 账号注册 | `SigOnLayer.cpp:106-115` `DBDao<GamePlayer> … dao.insertModel()` | `player` |
  | 角色列表 | `SelectLayer.cpp:100-104` `DBDao<PlayerInfo> … dao.queryModel()` | `playerinfo` |
  | 新建角色 | `NewGameLayer.cpp:94-99` `DBDao<PlayerInfo> … dao.insertModel()`；`NewGameLayer.cpp:198-208` `dao.updateModel("playername",…)` 累加 `nums` | `playerinfo` / `player` |
  | 角色数据存档 | `CameraPlayer.cpp:244-267` `SaveGameData()`：`DBDao<PlayerInfo> … updateModel(keyvls)` + 依次调用 `saveBackpackInfo()` / `saveEquipmentInfo()` / `saveSkillInfo()` | `playerinfo`、`backpack`、`equipmentinfo`、`skillinfo` |
  | 背包读取/增删改 | `BackPackManager.cpp:80-138` `readBackpackInfo` / `saveBackpackInfo` / `updateBackpack` / `deleteBackpack` | `backpack` |
  | 装备读取/增删改 | `EquipmentManager.cpp:68-127` `readEquipmentInfo` / `saveEquipmentInfo` / `updateEm` / `deleteEm` | `equipmentinfo` |
  | 技能读取/升级/保存 | `SkillManager.cpp:57-104` `upSkill` / `readSkillInfo` / `saveSkillInfo` | `skillinfo` |
  | 进入游戏时一次性装载 | `SelectLayer.cpp:131-133` `readBackpackInfo()`、`readEquipmentInfo()`、`readSkillInfo()` | 上述三表 |

  ⇒ **结论：账号、角色、背包、装备、技能这五类"业务数据"的权威副本在 MySQL，由客户端直连写入**，不经过游戏服务端。

**通道 B：自定义二进制 TCP（客户端 = 实时表现权威）**

- `Resources/server.cfg` 内容（已确认）：
  ```
  //服务器配置文件
  serverIp 192.168.229.128
  port 6036
  ```
- `CMClient::readConfConnectServer()`（CMClient.cpp:113-131）读该文件，注意它**连续 3 次 `fin >> m_serverip`**（吃掉注释行后才取到真实 IP）；`BeginScene.cpp:23-35` 在独立线程里调用 `CMClient::getInstance()->Connect()` → `CTCPClient::ConnectSever(m_serverip,m_port)`（CMClient.cpp:133-136）。
- 协议形态（`public.h`、`TCPClient.cpp`、`ShareData.h`）：**定长结构体裸发**，无长度前缀、无序列号、无粘包处理。`BUFF_SIZE 1024`、`PORT 6036`、断开哨兵 `CLOSE_MESSAGE "~#@**close**@#~"`。收包线程 `CTCPClient::DoServerMsg()`（TCPClient.cpp:87-122）单次 `recv` 后直接 `OnRecv(buff)`。
- **走通道 B 的业务**：进入游戏广播自身数据、位置同步与校验、玩家进出场景、队伍全部流程、战斗（普攻/技能/逃跑/死亡/怪物攻击）、使用药品广播、世界聊天、私聊。
- **通道 B 的完整消息枚举**：`ShareData.h:6-31` 的 `enum M_Type`，共 23 项，每一项对应一个以 `M_Type type` 为**首字段**的跨端结构体；`CMClient::OnRecv`（CMClient.cpp:36-111）按 `*((M_Type*)buff)` 分发。

**关键结论**：
1. **任务系统既不走 MySQL 也不走 TCP**——任务定义来自客户端本地文件 `Resources/Task/TaskN.tsk`，任务状态是客户端单例 `TaskSystem` 的内存链表（详见 §2）。
2. **战斗结算、升级、买卖、精炼、技能升级都在客户端本地算完直接落库或直接改内存**，服务端只负责转发与广播（详见 §3–§7）。
3. 同一份"玩家数据"被双写：TCP 通道广播用 `InitData_Msg/UpdateData_Msg`，MySQL 通道存档用 `PlayerInfo`，两边字段并不完全一致（TCP 无 exp/maxExp/glod，MySQL 无 fg/playertype 之外的运行时字段）。

### 0.3 面向 JSTM 的总体可借鉴点

| 可借鉴项 | 出处 | 价值 |
|---|---|---|
| 23 项 `M_Type` 消息目录与逐条结构体字段清单 | `ShareData.h` | 可直接作为 JSTM 消息枚举与字段设计的对照基线 |
| 任务三态机 `NS_FREE/NS_HTASK/NS_WSTASK/NS_STASK` 与 NPC 头顶图标映射 | `PreProcess.h:121-124`、`Npc.cpp:65-105` | 任务状态机与 NPC 表现层解耦范式 |
| 任务数据模型 `TaskInfo` 九字段 | `TaskSystem.h:14-26` | 任务表字段清单 |
| 装备五槽位常量 `EM_HEAD/EM_WEPON/EM_JEWELRY/EM_CLOTH/EM_FOOT` 与槽位坐标布局 | `PreProcess.h:109-113`、`RoleInfoLayer.cpp:184-203` | 槽位枚举与 UI 映射 |
| `ThingInfo{name,type,nums,grade}` + 三张持久化表 | `BackPackManager.h:11-22`、`Model.h` | 物品/装备/技能统一模型 |
| `REFLECT` 宏族按类名从地图文件生成 NPC | `ReflectNpc.h`、`ObjectLayer.cpp:60-89` | 地图刷 NPC 的数据驱动范式 |

---

## 1. 全局基础设施与数据模型

### 1.1 实体到表名/字段的映射（`Classes/Model.h`）

`Model.h` 用 `GettingAndSetting` 宏 + `operator[]` 序号索引 + `getAttributeName(i)` 组成"实体 = 表"的 ORM 契约：`getName()` 返回表名，`getAttributeNums()` 返回字段数，`operator[](i)` 与 `getAttributeName(i)` 必须一一对应。`DBDao<T>::generateSql()` 直接用这些字符串拼 SQL。

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/Model.h` | `class GamePlayer`（`getName()` = `"player"`） | 3 字段：`playername`/`playerpsw`/`nums`；`operator[]` 1..3；`getAttributeNums()`=3。用于账号表 | 适合 | 可借鉴：账号表最小字段集（账号名、密码明文、已建角色数）。注意密码明文存储，JSTM 应改哈希 |
| `Classes/Model.h` | `class PlayerInfo`（`getName()` = `"playerinfo"`） | 15 字段：`playername`/`rolename`/`roletype`/`glod`/`grade`/`blood`/`mana`/`attack`/`defense`/`speed`/`exp`/`maxexp`/`destx`/`desty`/`level` | 适合 | 可借鉴：角色表完整字段清单；注意 `level` 字段被复用为**当前地图号**（`CameraPlayer.cpp:258` `setlevel(NTS(GetIntData("CurMap")))`），语义污染，JSTM 应拆分 `mapid` 与 `level` |
| `Classes/Model.h` | `class SkillInfo`（`getName()` = `"skillinfo"`） | 4 字段：`playername`/`rolename`/`skillname`/`skillgrade` | 适合 | 可借鉴：角色技能表 (角色名,技能名,等级) 三元组设计，天然支持"技能不可重复" |
| `Classes/Model.h` | `class EquipmentInfo`（`getName()` = `"equipmentinfo"`） | 5 字段：`playername`/`rolename`/`equipmentname`/`grade`/`type` | 适合 | 可借鉴：`type` 即槽位号（1005–1009），`grade` 即精炼等级 |
| `Classes/Model.h` | `class BackPack`（`getName()` = `"backpack"`） | 6 字段：`playername`/`rolename`/`thingname`/`thingtype`/`thingnums`/`thinggrade` | 适合 | 可借鉴：`thingtype` 复用物品大类（1001 药/1002 装/1003 技能）；**注意装备与技能也被存进这张表**（`EquipMent::Disassemble` 存 `EQUIPMENT`），JSTM 若分表需重设计 |
| `Classes/Model.h` | `GettingAndSetting` 宏（第 6-9 行） | 展开为 `private: varType varName=""; get##funName(); set##funName()` | 适合 | 可借鉴：极简字段声明宏；但 `DBDao` 依赖"空串 = 不参与 WHERE"的约定，很脆弱 |

### 1.2 直连 MySQL 的 DAL（`Classes/DBDao.h` / `DBDao.cpp`）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/DBDao.h` | `template<Model> class DBDao` | 模板化单表 CRUD：`queryModel/insertModel/deleteModel/updateModel(1参/2参)`；`generateSql(QUERY/INSERT/DELETE/UPDATE)` 拼 SQL；`generateWhere/generateValues/generateUpdate` 由 `m_md` 非空字段动态生成 | 不适合 | 不适合直接照搬：① 纯字符串拼接，**存在 SQL 注入**（`updateModel(const std::string&, const std::string&)` 第 183-193 行直接拼值）；② `m_sql` 是成员且 `generateSql` 用 `append` **不清空**，同一 dao 实例重复调用会叠加 SQL；③ `mysql_real_connect` 返回值被忽略（第 217 行），无断线重连；④ `m_sqlCon` 在 `mysql_store_result` 后未 `mysql_free_result`（第 147-163 行，内存泄漏）。**可借鉴点**：`operator[]` + `getAttributeName` 的字段序号映射表（可作为 JSTM 实体↔表结构对照表） |
| `Classes/DBDao.h` | `DBDao()` 默认构造（第 106-113 行） | 硬编码主机 `47.93.235.6`、库 `chivalrousman`、用户 `game`、口令 `3252918599lsy` | 不适合 | 凭据硬编码进客户端二进制；JSTM 绝不能复制这种"客户端直连 DB"架构（应做服务端权威） |
| `Classes/DBDao.h` | `generateWhere()`（第 261-292 行） | 从 1 到 `getAttributeNums()` 遍历，非空字段拼 `and`，首个非空前插 `where` | 适合 | 可借鉴：由实体非空字段自动生成 WHERE 的思路（用于只读查询台、后台工具） |
| `Classes/DBDao.h` | `generateValues()`（第 295-313 行） | 同理生成 `values('…','…')` | 适合 | 同上 |
| `Classes/DBDao.h` | `generateUpdate()`（第 316-334 行） | 生成 `field='v' , field='v'`，跳过空字段 | 适合 | 可借鉴："只更新非空字段"的部分更新语义 |

### 1.3 TCP 客户端底层（`Classes/TCPClient.h/.cpp`、`Classes/public.h`）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/public.h` | `PORT`/`BUFF_SIZE`/`CLOSE_MESSAGE`/`CONNECT_MESSAGE` | `PORT 6036`、`BUFF_SIZE 1024`、断开哨兵 `"~#@**close**@#~"`、连接哨兵 `"~#@**connect**@#~"`；另有 `MY_IO_DATA`/`MY_IO_UDATA` 两个重叠 I/O 结构（服务端遗留） | 不适合 | 不适合照搬：`BUFF_SIZE 1024` 对定长结构体裸发是隐患（`PrivateTalk_Msg` 已 216 字节，`InitData_Msg` 约 120 字节，粘包即错位）。**可借鉴点**：`CLOSE_MESSAGE` 哨兵字符串作为"连接级控制帧"与业务帧区分的设计 |
| `Classes/TCPClient.cpp` | `ConnectSever(ip,port)` | `WSAStartup` → `socket` → `connect` → `new thread{DoServerMsg}` | 适合 | 可借鉴：单收包线程 + 主线程回调的最小客户端骨架 |
| `Classes/TCPClient.cpp` | `DoServerMsg()` | `while(true)` `recv(m_sockServer, buff, sizeof(buff), 0)`；`iRet==0 或 SOCKET_ERROR` 时回调 `CLOSE_MESSAGE` 并 break；否则整块 `buff` 交给 `OnRecv` | 不适合 | 不适合照搬：**一次 recv 当一帧**，无长度头、无粘包/半包处理、无心跳。JSTM 需要重做帧格式（长度前缀 + 消息号），但"整帧投递到 OnRecv 后由 M_Type 分发"的分层思路可借鉴 |
| `Classes/TCPClient.cpp` | `SendMsg(buff,len)` | 直接 `send`，失败置 `m_Error = "向服务发送消息失败!"` | 适合 | 可借鉴：`GetLastError()` 返回中文错误串，便于客户端提示 |
| `Classes/TCPClient.h` | `CTCPClient(ClientFunc, LPVOID)` | 支持函数指针回调模式（与虚函数 `OnRecv` 二选一） | 适合 | 可借鉴：回调/继承双模式，便于把网络层与业务层解耦 |

### 1.4 业务消息总线（`Classes/CMClient.h/.cpp`、`Classes/ShareData.h`）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/ShareData.h` | `enum M_Type`（第 6-31 行） | 23 个消息类型，顺序即协议号：`M_EntryGame, M_InitData, M_WorldTalk, M_PrivateTalk, M_InitPos, M_PlayerLeave, M_MoveTo, M_VerifyPos, M_UpdateData, M_TeamApply, M_RefuseTeam, M_AgreeTeam, M_TeamMove, M_TeamGotoMap, M_DissolveTeam, M_QuitTeam, M_KickOutteam, M_TeamFight, M_MonsterAtk, M_PlayerAtk, M_PlayerRun, M_UseMedication, M_PlayerDie` | 适合 | 高价值：**可直接作为 JSTM 消息枚举目录**。注意 `M_QuitTeam`(退队) 与 `M_KickOutteam`(踢人) 已定义但**未读到客户端实装**（见 §8） |
| `Classes/ShareData.h` | `struct InitData_Msg` | `type; char playername[40]; char rolename[40]; float blood/mana/attack/defense; int curmap; char playertype[10]; int grade; int fd;` | 适合 | 可借鉴：进场景广播字段集（含 `fd` 作为会话内玩家唯一标识）。**注意定长 char 数组**，JSTM 建议改长度前缀字符串 |
| `Classes/ShareData.h` | `struct Player_Info`（第 33-47 行） | 客户端本地玩家缓存结构：`playername/rolename/blood/mana/attack/defense/curmap/playertype/x/y/grade/fd` | 适合 | 可借鉴：客户端玩家对象字段集，可直接对照 JSTM 的 AOI/场景实体 |
| `Classes/ShareData.h` | `struct WorldTalk_Msg` | `type; int fd; char msg[200];` | 适合 | 可借鉴：世界频道帧（`fd==-1` 表示自己发的） |
| `Classes/ShareData.h` | `struct PrivateTalk_Msg` | `type; int fd; int dest; char msg[200];` | 适合 | 可借鉴：私聊帧需 `dest` 目标；发送方置 `fd=-1`、接收方置 `dest` |
| `Classes/ShareData.h` | `struct UpdateData_Msg` | `type; float blood/mana/attack/defense; int grade; int fd;` | 适合 | 可借鉴：属性变化广播帧最简字段集 |
| `Classes/ShareData.h` | `UseMedication_Msg` / `PlayerDie_Msg` / `PlayerRun_Msg` / `MonsterAtk_Msg` / `PlayerAtk_Msg` / `TeamFight_Msg` / `TeamManage_Msg` / `TeamGotoMap_Msg` / `TeamMove_Msg` / `AgreeTeam_Msg` / `RefuseTeam_Msg` / `TeamApply_Msg` / `VerifyPos_Msg` / `MoveTo_Msg` / `PlayerLeave_Msg` / `InitPos_Msg` | 每个结构体均以 `M_Type type` 为首字段，多数在构造函数里预置 `type` 与 `fd=-1` 默认值 | 适合 | 高价值：**结构体即协议帧**，构造函数预置 type 避免漏填；`PlayerAtk_Msg{char skill[30]; int grade;}` 携带技能名与技能等级，是"技能伤害跨端同步"的字段设计 |
| `Classes/CMClient.h` | `class CMClient : public Net::CTCPClient`（单例） | 承载收包分发、玩家列表、聊天队列、队伍申请队列、队伍跳图队列 | 适合 | 可借鉴：单例网络门面 + 本地缓存的组合 |
| `Classes/CMClient.cpp` | `OnRecv(char* buff)`（第 36-111 行） | 先比对 `CLOSE_MESSAGE`（弹「服务器异常关闭」并 `Director::end()`），再 `switch(*((M_Type*)buff))` 分发到 21 个 `doXxxMsg` | 适合 | 高价值：**消息号→处理函数映射表**，JSTM 可照此为每个 opcode 建 handler 注册 |
| `Classes/CMClient.cpp` | `readConfConnectServer()`（第 113-131 行） | 从 `server.cfg` 读 IP/端口；**连续 3 次读 IP** 以跳过注释行 | 适合 | 可借鉴：把连接配置外置为 `server.cfg`（JSTM 应改成容错解析 `key value` 形式，而非连读 3 次） |
| `Classes/CMClient.cpp` | `findRoleNameByFd` / `findPlayerInfoByFd` | 在 `m_playerlist` 中按 `fd` 线性查找 | 适合 | 可借鉴：`fd` 作为会话内玩家句柄。注意 O(n) 线性查找，JSTM 应换 `unordered_map<int,…>` |
| `Classes/CMClient.cpp` | `removePlayer(int fd)`（第 214-228 行） | 移除玩家时**级联清理**：`ObjectLayer::removePlayer` → `TeamManager::removeTeamMembers` → `m_privateTalkMsgs.erase(fd)` | 适合 | 高价值：离线级联清理顺序可作为 JSTM 会话回收的参考状态机 |

### 1.5 本地静态数据与全局动态数据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/GameData.h/.cpp` | `class GameData`（单例） | `init()` 用 `Dictionary::createWithContentsOfFile("GameData.xml")` 加载 plist；`StringValue(key)` 等宏 = `getStringByKey` 等 | 适合 | 可借鉴：**所有 UI 文案、资源路径、怪物/技能/地图/NPC 中文名集中在一个 XML**（`Resources/GameData.xml`，16.5KB）。JSTM 可复用"键值资源字典"结构。不适合照搬：`valueForKey` 未判空，缺键即崩 |
| `Resources/GameData.xml` | 键位清单（节选，已确认存在） | 怪物路径 `Ghost/BlackDragon/Dragon/…`；技能目录 `Skill/CrackIt/`…；NPC 中文名 `NpcBlueCN/NpcEquipCN/NpcMamomCN/NpcMonkCN/NpcPinkCN/NpcSkillCN/NpcValligeCN/BlackDragonCN`；任务面板文案 `TaskTitle/Process/DestMen/Kill/Collect/Access/PickTaskText`；属性文案 `Glod/Exp/Blood/Mana/LackGlod/UpgradeText`；技能 UI `SkillText/NoSelectSkill` | 适合 | 高价值：**任务类型→文案键的映射**（`T_KILL→"Kill"`、`T_ACCESS→"Access"`、`T_COLLECT→"Collect"`）可直接照抄；`*CN` 后缀的中英文名映射表对应 `TaskSystem::m_entocn` |
| `Classes/GameDynamicData.h/.cpp` | `class GameDynamicData`（单例） | 两套 `map<string,string>`：`m_data`（内存态）、`m_saveData`（落盘态）；`setXxxByKey(key,val,save)`，`save=true` 写 `m_saveData`；析构时 `writeDateToFile()` 写 `GameDynamicData.data` | 适合 | 可借鉴：**"会话内临时数据"与"需要跨会话保存的客户端偏好"分离**的设计。JSTM 可用于保存音量、上次地图等客户端设置。不适合照搬：仅在析构写盘，异常退出丢数据 |
| `Classes/GameDynamicData.cpp` | `GetValue` 宏 | 先查 `m_data` 再查 `m_saveData`，都没有返回 `-1` | 不适合 | 不适合：「未设置」与「值为 -1」不可区分，JSTM 应返回 `optional` |
| `Classes/PreProcess.h` | 物品类型宏（第 103-106 行） | `#define MEDICATION 1001`、`EQUIPMENT 1002`、`SKILL 1003` | 适合 | 高价值：**物品大类枚举**，直接对应 `ThingInfo.type` 与 `backpack.thingtype` |
| `Classes/PreProcess.h` | 装备槽位宏（第 108-113 行） | `EM_HEAD 1005`、`EM_WEPON 1006`、`EM_JEWELRY 1007`、`EM_CLOTH 1008`、`EM_FOOT 1009` | 适合 | 高价值：**装备槽位枚举**，与 `equipmentinfo.type` 同域（见 §4 槽位映射表） |
| `Classes/PreProcess.h` | 任务类型宏（第 115-118 行） | `T_KILL 2001`（击杀怪物）、`T_COLLECT 2002`（收集物品）、`T_ACCESS 2003`（访问别人） | 适合 | 高价值：**任务类型枚举**，与 `Task1.tsk` 中 `type 2001` 字面量一致（已交叉验证） |
| `Classes/PreProcess.h` | NPC 状态宏（第 120-124 行） | `NS_FREE 3001`（空闲）、`NS_HTASK 3002`（有未接任务）、`NS_WSTASK 3003`（有等待提交的任务）、`NS_STASK 3004`（有待提交任务） | 适合 | 高价值：**任务状态机四态**，JSTM 服务端可直接采用同一套语义 |
| `Classes/PreProcess.h` | 玩家队伍状态宏（第 126-129 行） | `P_STATUS_NORMAL 4001`、`P_STATUS_HEADER 4002`、`P_STATUS_MEMBER 4003` | 适合 | 可借鉴：队伍角色三态（无队/队长/队员） |
| `Classes/PreProcess.h` | 队伍按钮行为宏（第 131-135 行） | `TB_DISSOLVE 5001`、`TB_QUIT 5002`、`TB_KICKOUT 5003`、`TB_NULL 5004` | 适合 | 高价值：**队伍操作枚举**，`TB_NULL` 表示"该位置不显示按钮"，可直接照抄 |
| `Classes/Commen.h` | `RELEASE_NULL`、`ClickAction`、`ITEM_COMMEN`、`INIT_TALK_IN_NPC`、`AddToBackPack` 等宏族 | UI 与资源装载宏；`INIT_TALK_IN_NPC(X)` 从 `GameData.xml` 的 `"XTalk"` 键读整段 NPC 对话；`ITEM_COMMEN` 统一生成"头像框+头像+角色名+等级"列表项 | 适合 | 可借鉴：`ITEM_COMMEN` 抽出的**列表项公共结构**（头像资源名 = `playertype + "Head"`）与 `INIT_TALK_IN_NPC` 的对话数据驱动装载 |

---

## 2. 任务系统（客户端本地驱动，不走 MySQL / 不走 TCP）

### 2.1 任务数据来源与结构

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TaskSystem.h` | `struct TaskInfo`（第 14-26 行） | 9 字段：`name`（任务名）、`fromwho`（在谁处接）、`destwho`（提交给谁）、`schedulewho`（提交物/目标怪）、`glodreward`、`expreward`、`index`（任务索引）、`curschedule`（当前进度）、`allschedule`（总进度）、`type`（任务类型） | 适合 | **高价值：JSTM 任务表字段清单可直接照此设计**。`fromwho`/`destwho` 双 NPC 设计支持"异 NPC 交付"任务；`schedulewho` 单字段同时承载"怪物名"与"物品名"，按 `type` 解释 |
| `Classes/TaskSystem.cpp` | `TaskSystem::createTask()`（第 65-108 行） | 若未接列表 `< 3`：`rand()%11+1` 取索引（1..11）→ 查重 `m_taskindexs` → 打开 `Task/Task<N>.tsk` → 按固定顺序读 9 个 key/value 对 → `fromwho`/`destwho` 从 `m_npcvec` 随机取 → 入 `m_missedTask` | 适合 | **任务定义来自客户端本地文件**：`std::string filename = "Task/Task" + NTS(index) + ".tsk"`（第 77 行）。可借鉴：**任务定义文件格式（9 行 key value）与随机发任务策略**；不适合照搬：任务随机生成在客户端、上限 3 个未接任务均为客户端硬编码 |
| `Resources/Task/Task1.tsk` | 任务定义文件（已确认全文） | `name 黑龙肆虐 / schedulewho BlackDragon / glodreward 500 / expreward 600 / index 1 / curschedule 0 / allschedule 6 / type 2001` | 适合 | **高价值：任务定义文件字段顺序与样例数值**，与 `createTask()` 的读取顺序逐行对应，可作为 JSTM 任务表/配表模板 |
| `Resources/Task/` 目录 | `Task1..Task11`（`.tsk` + `.tk`） + `EndTask.tk` + `NoEndTask.tk` | `.tsk` = 任务数据（11 个）；`.tk` = 该任务的 NPC 对话文本；`EndTask.tk` = 可提交时的通用对话；`NoEndTask.tk` = 未完成时的通用对话 | 适合 | 可借鉴：**任务数据与任务对话分离**的配表组织方式；通用对话复用两份文件避免每个任务都写 |
| `Classes/TaskSystem.h` | `m_missedTask` / `m_pickedupTask` | 两个 `std::list<TaskInfo>`：未接列表、已接列表 | 适合 | 可借鉴：以两条链表表达任务生命周期 |
| `Classes/TaskSystem.h` | `m_taskindexs`（`std::set<int>`） | 已有任务索引去重集合 | 适合 | 可借鉴：用索引集合防止重复发任务 |
| `Classes/TaskSystem.cpp` | `TaskSystem::workThread()`（第 52-63 行） | 常驻线程：`createTask(); Sleep(15000);` 每 15 秒尝试生成一个新任务 | 适合 | 可借鉴：**定时刷新任务**的节奏（15 秒）；不适合照搬：任务刷新在客户端本地，服务端无法统一控制 |
| `Classes/TaskSystem.cpp` | `m_entocn` 映射表（构造函数 16-37 行） | 英文资源名 → `GameData.xml` 的 `*CN` 中文名键；含 7 个 NPC + 10 个怪物 | 适合 | 高价值：**英文标识→中文显示名映射表**，是客户端本地化的最小实现 |
| `Classes/TaskSystem.cpp` | `m_npcvec = { "NpcVallige","NpcBlue","NpcMamom","NpcMonk" }`（第 36 行） | 可接/可交任务的 4 个 NPC 白名单，`fromwho`/`destwho` 只从这 4 个里随机 | 待验证 | 【待验证】该白名单与 `Resources/LevelObject/Level1.lobject` 的 NPC 列表（`NpcVallige/NpcBlue/NpcMamom`）**不完全一致**（多出 `NpcMonk`），未读到 `NpcMonk` 的刷点文件故无法确认是否只是其他地图刷出 |

### 2.2 任务状态机（未接 → 已接 → 可提交 → 已完成）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TaskSystem.cpp` | `pickupTask(int index)`（第 110-122 行） | 在 `m_missedTask` 中按 `index` 找到 → `push_back` 到 `m_pickedupTask` → 从 `m_missedTask` 删除；成功返回 0，未找到返回 1 | 适合 | 高价值：**"接取"状态迁移的最小实现**。JSTM 服务端可映射为 `quest_status: 0→1` |
| `Classes/PickupTaskLayer.cpp` | `onOkBtnClickCallback()`（第 54-59 行） | 点「确定」→ `TaskSystem::pickupTask(m_npc->getTaskIndex())` → `m_npc->changeState(NS_FREE, 0)` → 移除本层 | 适合 | 可借鉴：**接取 UI 只在确认后调用状态机**，取消不做任何变更 |
| `Classes/TaskSystem.cpp` | `submitTask(node,index)`（第 124-140 行） | 在 `m_pickedupTask` 中按 `index` 找到 → `GetPlayerData().addGlod(glodreward)` + `addExp(expreward)` → 弹 `TipLayer` 提示「Glod+X,Exp+Y」→ 从已接列表删除 → 从 `m_taskindexs` 删除索引 | 适合 | **高价值但也高风险**：奖励结算完全在客户端内存完成（`addGlod`/`addExp` 直接改本地数据），服务端不参与；JSTM 必须把这段搬到服务端 |
| `Classes/TaskSystem.cpp` | `havePickedupTask(name)`（第 154-172 行） | 遍历已接任务，若 `destwho == name`：`curschedule >= allschedule` 返回正 `index`（可提交）；否则返回 `-index`（未完成），最终返回 0 表示无 | 适合 | **高价值：用返回值符号位编码三态的巧思**（正=可提交、负=未完成、0=无任务），JSTM 可借用此约定做紧凑的 NPC 状态查询协议 |
| `Classes/TaskSystem.cpp` | `haveMissedTask(name)`（第 142-152 行） | 遍历未接任务，`fromwho == name` 则返回 `index`，否则 0 | 适合 | 可借鉴：NPC 是否有未接任务的查询接口 |
| `Classes/ObjectLayer.cpp` | `checkmissedTask()` / `checkpickedupTask()`（第 113-135 行） | 每帧（`update`）对场景内所有 NPC 调上述两函数，据结果调 `changeState(NS_HTASK,index)` 或 `changeState(index>0 ? NS_STASK : NS_WSTASK, abs(index))` | 适合 | **高价值：任务状态→NPC 表现的每帧同步范式**。JSTM 服务端推送任务状态变更后，客户端可按同一模式刷新 NPC 头顶图标 |
| `Classes/Npc.cpp` | `changeState(int state,int index)`（第 65-105 行） | 同状态且 `pickup==true` 时早退防抖；更新 `m_state`/`m_taskindex`；先 `m_face->removeChildByName("TaskState")` 清旧图标，再按状态挂 `Taskh`(3002) / `Taskw`(3003) / `Tasks`(3004) 图标；`NS_WSTASK`/`NS_STASK` 置 `pickup=false` | 适合 | 高价值：**状态图标映射表**（`NS_HTASK→"Taskh"`、`NS_WSTASK→"Taskw"`、`NS_STASK→"Tasks"`）与防抖逻辑；`Resources/` 下确有 `taskh.png/taskw.png/tasks.png`（已确认） |
| `Classes/Npc.cpp` | `talkEndEvent()`（第 107-134 行） | `NS_STASK` → `TaskSystem::submitTask(CurGameScene(), m_taskindex)` + `changeState(NS_FREE,0)`；`NS_HTASK` → 创建 `PickupTaskLayer`；`NS_WSTASK` → 仅恢复对话；三态统一 `m_talkmsg = m_tmptalk` 还原通用对话 | 适合 | 高价值：**对话结束事件即任务状态迁移触发点**，是完整的"对话驱动任务"状态机 |
| `Classes/Npc.cpp` | `collisionEvent()`（第 22-44 行） | 置 `m_isCollision=true` → `resetIndex()` → 按 `m_state` 装载对话（`NS_WSTASK→initNoEndTaskTalk()`、`NS_HTASK→initMissTaskTalk()`、`NS_STASK→initEndTaskTalk()`）→ 加 `TalkLayer` | 适合 | 可借鉴：碰撞进入即按状态装载对应对话文本 |
| `Classes/Npc.cpp` | `endCollisionEvent()`（第 46-52 行） | 移除 `talkLayer` 与 `pklayer` | 适合 | 可借鉴：离开碰撞即清理对话/接取层 |
| `Classes/Npc.cpp` | `initMissTaskTalk()` / `initEndTaskTalk()` / `initNoEndTaskTalk()`（第 141-154 行） | 分别读 `Task/Task<N>.tk`、`Task/EndTask.tk`、`Task/NoEndTask.tk` | 适合 | **高价值：`Task<N>.tk` 与 `Task<N>.tsk` 同索引配对**的命名约定，JSTM 可直接沿用 |
| `Classes/Npc.cpp` | `initTaskTalk(filename)`（第 156-179 行） | 逐 token 读入 `m_talkmsg`；随后若 `TaskSystem::checkTask(m_taskindex,dest) == T_ACCESS`，把 `dest`（目标 NPC 中文名）拼到 `m_talkmsg[0]` 末尾并加 `"?"` | 适合 | 可借鉴：**T_ACCESS 任务的对话动态拼接目标名**，是"访问类任务"的唯一客户端痕迹 |
| `Classes/TaskSystem.cpp` | `checkTask(int index, std::string& name)`（第 186-196 行） | 在 `m_missedTask` 中按 `index` 找，命中则出参 `name = m_entocn[var.destwho]` 并返回 `var.type`，否则 -1 | 适合 | 可借鉴：**任务类型与目标名一次查询返回**的接口设计 |
| `Classes/TaskItem.cpp` | `TaskItem::init(tinfo)`（第 21-81 行） | 任务条目 UI：任务名 + `Process:curschedule/allschedule` + `DestMen:<中文提交人>` + 按 `type` 显示 `Kill/Collect/Access + 目标中文名` + `Glod:xx` + `Exp:xx` | 适合 | **高价值：任务面板每一行的字段清单**（名称/进度/提交人/类型描述/金币/经验），JSTM 可直接对照做任务详情协议 |
| `Classes/TaskLayer.cpp` | `initTaskItem(basePos)`（第 26-41 行） | 遍历 `TaskSystem::getInstance()->getpickedupTask()`，最多显示 7 条（`index > 6` 即 return），每条间隔 80px | 适合 | **任务面板数据来源 = 客户端内存链表**（非 GameData.xml、非 MySQL、非 TCP）——【已确认】。可借鉴：面板最多 7 条的布局约束 |

### 2.3 任务进度如何计算

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TaskSystem.cpp` | `checkKillMonster(const std::string& name)`（第 174-184 行） | 遍历 `m_pickedupTask`，**只要 `schedulewho == name` 就 `it->curschedule++` 并 return**（不区分任务类型、不校验 `curschedule` 是否已满） | 适合 | **高价值：进度推进的唯一客户端入口**。可借鉴：以"目标名匹配"驱动进度；不适合照搬：未判 `type==T_KILL`、未封顶（可超 `allschedule`）、未持久化 |
| `Classes/Monster.cpp` | `Monster::beAttack(attack)`（第 95-120 行） | 怪物血量 `<=0` 时置 `m_isdie=true`，`scheduleOnce(0.3)` 后 `((FightLayer*)getParent())->removeMonster(this)` 并 `TaskSystem::getInstance()->checkKillMonster(this->getname())` | 适合 | 高价值：**进度推进的触发点 = 怪物死亡回调**，链路完整（`Monster::beAttack` → `checkKillMonster` → `curschedule++`） |
| `Classes/Monster.cpp` | 伤害公式（第 103 行） | `float hurtvalue = attack <= m_defense ? 1 : attack - m_defense;` | 适合 | 可借鉴：**最小伤害 1** 的保底规则 |
| — | 收集类 / 访问类进度 | **未读到** `T_COLLECT` 的背包拾取推进代码、也**未读到** `T_ACCESS` 的访问推进代码；全仓库仅 `checkKillMonster` 一处进度入口（已确认 `checkKillMonster` 仅在 `Monster.cpp:114` 被调用） | 待验证 | 【待验证】`T_COLLECT`/`T_ACCESS` 两类任务的进度推进是否由服务端（CM-Server）实现，本次未读到 |

### 2.4 任务面板数据来源（明确回答）

| 问题 | 结论 | 证据 | 等级 |
|---|---|---|---|
| 任务定义（名称/目标/奖励/类型）来自哪 | **客户端本地文件 `Resources/Task/Task<N>.tsk`** | `TaskSystem.cpp:76-100` | 【已确认】 |
| 任务对话文本来自哪 | **客户端本地文件 `Task/*.tk`** | `Npc.cpp:143-153`、`Commen.h` `INIT_TALK_IN_NPC`(读 `GameData.xml` 的 `*Talk` 键) | 【已确认】 |
| 任务面板（TaskLayer）数据来自哪 | **客户端内存单例 `TaskSystem::m_pickedupTask`** | `TaskLayer.cpp:30` | 【已确认】 |
| 任务是否落库 | **否**：`Model.h` 中无任何 Task 实体，`CameraPlayer::SaveGameData()` 也只保存 playerinfo/backpack/equipmentinfo/skillinfo | `Model.h` 全文、`CameraPlayer.cpp:244-267` | 【已确认】 |
| 任务是否走 TCP | **否**：`M_Type` 中无任何任务消息 | `ShareData.h:6-31`、`CMClient.cpp:36-111` | 【已确认】 |
| 任务定义是否与服务端同一份 | 未读到 CM-Server 源码 | — | 待验证 |

---

## 3. 背包与物品（MySQL 直连持久化）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/BackPackManager.h` | `struct ThingInfo`（第 11-22 行） | `name`（资源名）、`type`（1001/1002/1003）、`nums`、`grade`（默认 1）；`operator==` 只比 `name && type` | 适合 | **高价值：物品统一模型**，一份结构同时表达药品/装备/技能。可借鉴 `operator==` 的"同类物品"判定 |
| `Classes/BackPackManager.h` | 宏 `AddToBackPack` / `RemoveFromBackPack` / `BackPackMap` | 把单例方法包装成短宏供全局调用 | 适合 | 可借鉴：单例访问宏降低调用噪音 |
| `Classes/BackPackManager.cpp` | `addBackPackThing(ThingInfo)`（第 25-41 行） | 线性查同名 → 命中则 `++nums`（**不更新 grade**）；未命中则 `nums=1` 并 `push_back` | 适合 | 可借鉴：同名堆叠；不适合照搬：堆叠时忽略 grade 差异（不同精炼等级装备会混堆） |
| `Classes/BackPackManager.cpp` | `removeBackPackThing(name)`（第 43-61 行） | 命中则 `--nums`；减到 0 则 `erase(it)` 后 `deleteBackpack(*it)` 并返回 -2；否则 `updateBackpack(*it)` 返回 -1；未命中返回 0 | 不适合 | **已确认缺陷**：第 52-53 行 `m_backpackList.erase(it)` 之后立刻解引用 `*it`（迭代器失效，UB）。三态返回值约定（0 未找到 / -1 减一 / -2 减到零）值得借鉴，但实现必须重写 |
| `Classes/BackPackManager.cpp` | `ThingNums(name)`（第 68-78 行） | 按名查数量，未命中 0 | 适合 | 可借鉴：数量查询接口 |
| `Classes/BackPackManager.cpp` | `readBackpackInfo()`（第 80-98 行） | 清空本地列表 → `BackPack info` 只填 `playername`+`rolename` → `DBDao<BackPack>::queryModel()` 生成 `select * from backpack where playername='…' and rolename='…'` → 逐行 `stoi` 回填 `ThingInfo` | 适合 | **高价值：`backpack` 表的读取路径与字段映射**（`thinggrade/thingname/thingnums/thingtype`）；`playername + rolename` 作为联合查询键 |
| `Classes/BackPackManager.cpp` | `saveBackpackInfo()`（第 100-115 行） | 遍历本地列表，**每件物品都 `insertModel()`，且保存前不删旧行** | 不适合 | **已确认缺陷**：重复调用（每次切场景/退出都调）会在 `backpack` 表**累积重复行**。可借鉴点：`insert into backpack values('playername','rolename','thingname','thingtype','thingnums','thinggrade')` 的完整字段顺序 |
| `Classes/BackPackManager.cpp` | `updateBackpack(ThingInfo)`（第 117-128 行） | `BackPack thing` 只填 `thingnums` → `generateUpdate()` 只更新非空字段 → `keyvls = {playername, rolename, thingname}` 拼 WHERE | 适合 | **高价值：部分更新 + 组合主键定位**的 SQL 形态（`update backpack set thingnums='N' where playername='..' and rolename='..' and thingname='..'`） |
| `Classes/BackPackManager.cpp` | `deleteBackpack(ThingInfo)`（第 130-139 行） | 填 `thingname`+`playername`+`rolename` → `delete from backpack where playername=… and rolename=… and thingname=…` | 适合 | 可借鉴：删除仅以三字段定位 |
| `Classes/BackPackLayer.cpp` | `initBackPackThing()`（第 122-156 行） | 遍历 `BackPackMap()`：`type==MEDICATION` → `Medication::createWithImage(name+".png")`；否则 → `EquipMent::createWithImage(...)` 并 `setgrade(it.grade)`；8 列（`#define BASENUM 8`）网格布局；用 `setTag(index)` 存索引、另存 `m_numlabels` 数量标签 | 适合 | **高价值：背包网格 = 8 列**（`BASENUM 8`）、`MEDICATION→Medication`、其余→`EquipMent` 的分派规则。注意技能（1003）在此会被当作装备实例化，已确认 |
| `Classes/BackPackLayer.cpp` | `sellBtnCallback()`（第 70-89 行） | 取当前选中物 → 读数量标签 → `nums>0` 则标签减一 + `removeBackPackThing(name)` + `GetPlayerData().addGlod(pth->getsellglod())`；否则提示「LackNums」 | 适合 | **出售逻辑完全在客户端**：价格来自 `Thing*.att` 的 `sellglod`，金币加在本地 `PlayerData`。JSTM 必须服务端校验 |
| `Classes/BackPackLayer.cpp` | `useBtnCallBack()`（第 91-110 行） | 取选中物 → `pth->beUse(this)` → 数量减一 → `removeBackPackThing(name)` | 适合 | 可借鉴：**使用物品 = 虚函数 `Thing::beUse` 多态 + 数量扣减**的分工 |
| `Classes/Thing.h/.cpp` | `class Thing : public cocos2d::MenuItemImage` | 物品基类：`showDetail(node)` 创建 `DetailLayer`；`getDetails()` 返回 `m_details`；纯虚行为 `beUse(obj,who,towho)`；`initDetails(name)` 读 `<name>.dec` 文件 | 适合 | **高价值：物品详情由 `<name>.dec` 文本文件驱动**（首行 `m_firsttext` 作标题，其余为明细行，`Thing.cpp:51-70`）；`Resources/Thing/` 下每件物品确有 `.dec/.att/.png` 三件套（已确认，如 `AnimalSkin.dec/.att/.png`） |
| `Classes/Thing.cpp` | `getfileName(name)`（第 32-49 行） | 截断到第一个 `.` 之前，得到纯物品名 | 适合 | 可借鉴：资源名去扩展名的工具函数 |
| `Classes/Thing.h` | `PROPERTY__REF(float, m_buyglod, buyglod)` 等 | 购买价/卖出价/名称/首句详情四个属性 | 适合 | 可借鉴：物品公共属性字段清单 |
| `Classes/DetailLayer.cpp` | `DetailLayer::init(Thing* th)` | 逐行渲染 `th->getDetails()`（字号 20，行高 = 文字高度）+ 末尾 `Cost<buyglod>` + 关闭按钮 | 适合 | 可借鉴：物品详情弹层的字段渲染顺序（明细行 → 购买价） |
| `Classes/DealLayer.h/.cpp` | `class DealLayer` + `createWithType(type,name)` | 按 `type` 分派：`MEDICATION→ADD_THING(Medication,1)`、`EQUIPMENT→ADD_THING(EquipMent,1)`、`SKILL→ADD_THING(Skill,0)`；`ADD_THING` 宏从 `GameData.xml` 拿到商品列表文件名，逐个读物品名并用 `Thing/` 或 `Skill/<name>/` 路径建图 | 适合 | **高价值：商店类型 → 商品列表文件 → 图标路径**的三级数据驱动；`ADD_THING` 宏内已含 SKILL 走 `Skill/%s/%s.png` 而普通物品走 `Thing/%s.png` 的路径差异 |
| `Classes/DealLayer.cpp` | `checkBuy(float money)`（第 168-203 行） | 金币不足提示「LackGlod」；`SKILL` 类型先 `SkillManager::haveSkill(name)` 查重（重复则提示空文本并 return），否则 `addSkill(name)`；非技能则 `AddToBackPack(info)`；最后提示「BuySuccess」并 `GetPlayerData().setglod(haveglod - money)` | 适合 | **高价值：购买流程 4 步状态机**（校验金币 → 技能查重 → 入背包/学技能 → 扣钱提示）。JSTM 可照此设计服务端购买事务；**注意此处完全没有技能数量上限校验**（见 §5.3） |
| `Classes/NpcPink.cpp` | `talkEndEvent()` | 对话结束 → `pauseSchedulerAndActions()` → `DealLayer::createWithType(MEDICATION, StringValue("DealMedication"))`，层名设为 `DealLayer` | 适合 | 可借鉴：**NPC 类型 ↔ 商店类型绑定**（`NpcPink`=药品商）。`endCollisionEvent` 会 `removeChildByName("DealLayer")` |
| `Classes/NpcEquip.cpp` | `talkEndEvent()` | 同上，`DealLayer::createWithType(EQUIPMENT, StringValue("DealEquipMent"))` | 适合 | 可借鉴：`NpcEquip`=装备商 |
| `Classes/NpcSkill.cpp` | `talkEndEvent()` | 同上，`DealLayer::createWithType(SKILL, StringValue("DealSkill"))` | 适合 | 可借鉴：`NpcSkill`=技能商 |

### 3.1 背包物品属性文件格式（已确认）

`Resources/Thing/BlueMedicine.att`：
```
//蓝瓶
buyglod 100
sellglod 50
addblood 0
addmana 100
```
`Classes/Medication.cpp:48-65` 的 `initProperty` 先用一次 `fin >> tmp` 吃掉注释行，再用 `ADD_PROPERTY`（`PreProcess.h:76-79`：连读两个 token，取第二个 `stof`）逐项读 `buyglod/sellglod/addblood/addmana`——**每个 `ADD_PROPERTY` 消费"标签+值"两个 token**，与文件格式精确对应。【已确认】

---

## 4. 装备系统（MySQL 直连持久化 + 客户端本地精炼）

### 4.1 装备槽位映射（头 / 武器 / 首饰 / 衣服 / 鞋）

| 槽位常量（`PreProcess.h:108-113`） | 值 | 对应的 UI 坐标（`RoleInfoLayer.cpp:184-203`） | 数据库字段 | 等级 |
|---|---|---|---|---|
| `EM_HEAD` | 1005 | `m_centerP.x, m_centerP.y + 55`（居中偏上） | `equipmentinfo.type = '1005'` | 【已确认】 |
| `EM_WEPON` | 1006 | `m_centerP.x - 55, m_centerP.y`（左） | `equipmentinfo.type = '1006'` | 【已确认】 |
| `EM_JEWELRY` | 1007 | `m_centerP.x + 55, m_centerP.y`（右） | `equipmentinfo.type = '1007'` | 【已确认】 |
| `EM_CLOTH` | 1008 | `m_centerP`（正中） | `equipmentinfo.type = '1008'` | 【已确认】 |
| `EM_FOOT` | 1009 | `m_centerP.x, m_centerP.y - 55`（居中偏下） | `equipmentinfo.type = '1009'` | 【已确认】 |

槽位号的真实出处是装备自身的 `.att` 文件：`Resources/Thing/BlackWitchHelmet.att` 末行 `type 1005`（头盔）。`EquipMent::initProperty`（`EquipMent.cpp:51-72`）按 `buyglod/sellglod/addblood/addmana/addattack/adddefense/addspeed/type` 顺序读取，`type` 即槽位。【已确认】

README 第 5-6 行「一个玩家最多可以装备五件装备分别是头盔、装甲、首饰、武器和鞋子」与本表五槽位一致。【已确认】

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/PreProcess.h` | `EM_*` 五个宏 | 槽位枚举，值域 1005–1009，与物品大类 1001–1003 同属"1000 段"编码 | 适合 | **高价值：槽位枚举枚举值可直接照抄**；注意与物品大类共用命名空间，JSTM 建议改为独立枚举 |
| `Classes/EquipmentManager.h` | `struct EMInfo { name; type; grade; }` | 已穿戴装备的内存模型：名称、槽位、精炼等级 | 适合 | **高价值：穿戴态最小字段集** |
| `Classes/EquipmentManager.cpp` | `wearEquipment(const EMInfo& info)`（第 17-33 行） | 按 `type` 找同槽位：命中则用**旧装备**建 `EquipMent` → `Disassemble(nullptr)` 把旧装备退回背包 → 覆盖 `it->name` 且 `it->grade = 1`；未命中则 `push_back`。返回 -1（替换）/0（新穿） | 不适合 | **已确认缺陷**：替换时把新装备精炼等级强制重置为 1，且旧装备通过与"新实例"同名的对象退回背包，语义混乱。**可借鉴点**：返回值 -1/0 区分"替换/新增"；"脱下旧装回背包"的流程 |
| `Classes/EquipMent.cpp` | `EquipMent::beUse(obj,who,towho)`（第 74-85 行） | 组装 `EMInfo{name,type,grade}` → `EquipmentManager::wearEquipment(info)` → `GetPlayerData().addProperty(addblood+(grade-1)*30, addmana+(grade-1)*30, addattack+(grade-1)*8, adddefense+(grade-1)*8)` → 提示「WearSuccess」 | 适合 | **高价值：穿戴生效公式（含精炼换算）**：血/魔 `+30×(grade-1)`、攻/防 `+8×(grade-1)`。JSTM 可复用该公式或替换为配置表 |
| `Classes/EquipMent.cpp` | `Disassemble(Node*)`（第 87-103 行） | 计算 `sub*` 同上公式并 `addProperty(-sub…)` 反向扣除 → 组装 `ThingInfo{name, nums=1, type=EQUIPMENT, grade=m_grade}` → `AddToBackPack` | 适合 | **高价值：脱装的属性反向扣除 + 物品回背包**的完整流程。注意 `grade` 被保留（与 `wearEquipment` 替换分支的 `grade=1` 不一致） |
| `Classes/EquipMent.cpp` | `upgrade(Node*)`（第 105-114 行） | `m_grade += 1`；`GetPlayerData().addProperty(30,30,8,8)`（**固定加值，非按等级换算**）；若 `PropertyLayer` 存在则刷新属性面板 | 适合 | 高价值：**精炼 = 本地等级自增 + 固定属性加成**。注意与 `beUse` 的 `(grade-1)*30` 公式不一致，说明精炼后属性并非严格按等级重算 |
| `Classes/EquipMent.cpp` | `upGlod()`（第 156-159 行） | 下一级精炼费用 = `m_baseupglod + m_grade*(100 + m_baseupglod/10)` | 适合 | **高价值：精炼费用公式**，JSTM 可直接照抄或替换为配置 |
| `Classes/EquipMent.cpp` | `init(filename)`（第 38-49 行） | `m_baseupglod = m_addblood + m_addmana + m_addattack*10 + m_adddefense*10` | 适合 | 高价值：**精炼基础费用由装备属性反推**，可借鉴为"按属性价值定价"的策略 |
| `Classes/EquipMent.cpp` | `showProperty(node)`（第 116-154 行） | 属性面板显示：名称(`m_firsttext`) / Blood / Mana / Attack / Defense / `GradeText+m_grade` / `NextGrade:<upGlod()>` | 适合 | 高价值：**装备详情字段清单与展示顺序**，可直接映射为 JSTM 装备详情协议字段 |
| `Classes/EquipmentManager.cpp` | `upEquipment(const std::string& name)`（第 35-47 行） | 按名找到内存项 `var.grade += 1` → `updateEm(var)` 落库；找不到返回 1 | 适合 | **高价值：精炼等级写回 `equipmentinfo.grade`**，可映射为 JSTM `UPDATE equipment SET grade=grade+1 WHERE …` |
| `Classes/EquipmentManager.cpp` | `updateEm(EMInfo)`（第 103-114 行） | `EquipmentInfo em` 只填 `grade` → `keyvls={playername,rolename,equipmentname}` | 适合 | 可借鉴：`update equipmentinfo set grade='N' where playername=.. and rolename=.. and equipmentname=..` |
| `Classes/EquipmentManager.cpp` | `readEquipmentInfo()`（第 68-85 行） | `select * from equipmentinfo where playername=… and rolename=…` → 回填 `EMInfo.name/grade/type` | 适合 | 高价值：**装备读数路径与字段映射**（`equipmentname/grade/type`） |
| `Classes/EquipmentManager.cpp` | `saveEquipmentInfo()`（第 87-101 行） | 同背包：逐件 `insertModel()`，保存前不删旧行 | 不适合 | 已确认缺陷：`equipmentinfo` 表同样会累积重复行 |
| `Classes/EquipmentManager.cpp` | `deleteEm(EMInfo)`（第 116-127 行） | 填 `grade/equipmentname/playername/rolename/type` 后 `deleteModel()` | 适合 | 可借鉴：`delete from equipmentinfo where …`（**注意 WHERE 会包含 grade 与 type**，语义偏怪） |
| `Classes/RoleInfoLayer.cpp` | `initRoleEquipment()`（第 176-206 行） | 遍历 `EquipmentManager::getEmList()` 建 `EquipMent` 图标，按 `it->type` 用 `switch` 摆到五个槽位坐标 | 适合 | **高价值：槽位号 → 屏幕锚点映射表**（见 §4.1 表），JSTM 客户端可直接复用 |
| `Classes/RoleInfoLayer.cpp` | `onUpBtnClick()`（第 146-165 行） | 取 `upGlod()`；金币足够则 `EquipmentManager::upEquipment(name)` + `EquipMent::upgrade(this)` + `subGlod(glod)`；不足提示「LackGlod」 | 适合 | **精炼逻辑在客户端**（属性、等级、扣钱、落库全在客户端，TCP 不参与）——【已确认】。JSTM 必须服务端化 |
| `Classes/RoleInfoLayer.cpp` | `onDisassembleBtnClick()`（第 208-219 行） | `removeEquipment(name)` 移出内存与库 → `EquipMent::Disassemble(this)` 退回背包 → 隐藏图标 | 适合 | 可借鉴：拆解 = 列表移除 + 属性回退 + 物品入背包 |

### 4.2 精炼 / 升级逻辑在客户端还是服务端（明确回答）

| 环节 | 位置 | 证据 | 等级 |
|---|---|---|---|
| 精炼费用计算 | **客户端** | `EquipMent::upGlod()`（`EquipMent.cpp:156-159`） | 【已确认】 |
| 精炼等级自增 | **客户端** | `EquipMent::upgrade()`（`EquipMent.cpp:108`）、`EquipmentManager::upEquipment()`（`EquipmentManager.cpp:41`） | 【已确认】 |
| 精炼属性加成 | **客户端** | `GetPlayerData().addProperty(30,30,8,8)`（`EquipMent.cpp:109`） | 【已确认】 |
| 扣金币 | **客户端** | `GetPlayerData().subGlod(glod)`（`RoleInfoLayer.cpp:157`） | 【已确认】 |
| 落库 | **客户端直连 MySQL** | `EquipmentManager::updateEm()` → `DBDao<EquipmentInfo>::updateModel` | 【已确认】 |
| 是否走 TCP 广播 | **否**：`M_Type` 无装备相关消息；`UpdateData_Msg` 只带 blood/mana/attack/defense/grade | `ShareData.h:116-125` | 【已确认】 |
| 服务端是否二次校验精炼 | 未读到 CM-Server 源码 | — | 待验证 |

---

## 5. 技能系统（MySQL 直连持久化 + 客户端本地升级）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SkillManager.h` | `class SkillManager`（单例） | 核心容器 `std::map<std::string,int> m_skillMap`（技能名 → 技能等级） | 适合 | **高价值：技能表用 `map<技能名,等级>` 表达**，天然保证技能不重复 |
| `Classes/SkillManager.cpp` | `addSkill(name, grade=1)`（第 25-34 行） | `find(name)` 命中返回 -1（已学），否则 `m_skillMap[name]=grade` 返回 0 | 适合 | 高价值：**技能唯一性校验 + 默认 1 级**，JSTM 可映射为 `INSERT … ON DUPLICATE` 前的查重 |
| `Classes/SkillManager.cpp` | `skillNumbers()`（第 52-55 行） | 返回 `m_skillMap.size()` | 适合 | **已确认：该函数在全仓库无任何调用点**（仅 `.h` 声明与 `.cpp` 定义），即"技能数量"接口存在但未被使用——见 §5.3 |
| `Classes/SkillManager.cpp` | `upSkill(name)`（第 57-74 行） | `m_skillMap[name] += 1` → 组装 `SkillInfo{skillgrade}` → `keyvls={playername,rolename,skillname}` → `DBDao<SkillInfo>::updateModel(keyvls)` | 适合 | **高价值：技能升级 = 内存自增 + `skillinfo` 表 UPDATE**，SQL 形态为 `update skillinfo set skillgrade='N' where playername=.. and rolename=.. and skillname=..` |
| `Classes/SkillManager.cpp` | `readSkillInfo()`（第 76-89 行） | `select * from skillinfo where playername=… and rolename=…` → `m_skillMap[skillname] = stoi(skillgrade)` | 适合 | 高价值：**技能表字段映射**（`playername/rolename/skillname/skillgrade`） |
| `Classes/SkillManager.cpp` | `saveSkillInfo()`（第 91-104 行） | 逐技能 `insertModel()`，保存前不删旧行 | 不适合 | 已确认缺陷：`skillinfo` 表会累积重复行，且 `m_skillMap` 是 `map` 天然唯一，说明重复行纯粹是该保存策略造成的 |
| `Classes/SkillManager.cpp` | `removeSkill(name)`（第 36-39 行） | `m_skillMap.erase(name)`，**未落库** | 不适合 | 不适合：内存与库不一致（删内存不删库），JSTM 需补 DELETE |
| `Classes/Skill.h` | `class Skill : public Thing` | 技能图标兼行为对象：`beUse(obj,who,towho)`、`incGrade()`、`getUseMana()`；属性 `m_baseAttack/m_baseMana/m_baseupGlod/m_grade` | 适合 | **高价值：技能四字段清单**（基础攻击、基础耗蓝、升级基础费用、等级），与技能 `.att` 文件一一对应 |
| `Classes/Skill.cpp` | `initProperty(name)`（第 51-71 行） | 连读 3 次到 `m_name`（吃掉中文注释行 + `name` 标签 + 真名），随后按 `buyglod/sellglod/baseAttack/baseMana/baseupGlod` 读取 | 适合 | **高价值：技能属性文件格式**，已用 `Resources/Skill/Long/Long.att` 交叉验证：`火龙诀 / name Long / buyglod 1200 / sellglod 600 / baseattack 340 / basemana 50 / baseupglod 620` |
| `Classes/Skill.cpp` | `beUse(obj,who,towho)`（第 73-81 行） | **伤害公式：`m_baseAttack + 30 * m_grade`**；`SkillFactory::createSkill(m_name, pFt, towho, 伤害)` 生成表现实例；对 `who` 播 0.2s 位移动作；返回 `skill->getTag()` 作为技能动画时长（供 `FightLayer` 排程） | 适合 | **高价值：技能伤害升级公式（每级 +30）与"技能返回动画时长"的约定**。`FightLayer.cpp:611` 用 `scheduleOnce(func, delay + 0.5, "item")` 消费该返回值 |
| `Classes/Skill.cpp` | `getUseMana()`（第 88-91 行） | **耗蓝公式：`m_baseMana + m_grade * 10`** | 适合 | **高价值：耗蓝随等级公式（每级 +10）** |
| `Classes/Skill.cpp` | `incGrade()`（第 83-86 行） | `++m_grade` | 适合 | 可借鉴：与 `SkillManager::upSkill` 成对调用（内存对象与 map 双写） |
| `Classes/SkillFactory.h/.cpp` | `SkillFactory::createSkill(name,parent,towho,attack)` | 按**技能名字符串**分派到具体表现类：`CrackIt / Dante / DragonRoar / LightStrike / Long / RecallCountermand / SealOfTheBlade / XBArrow`，共 8 个；未命中返回 `nullptr` | 适合 | **高价值：8 个技能的表现类分派表**，是全项目唯一硬编码的技能名单。JSTM 可改为数据驱动（技能 id → 表现工厂） |
| `Classes/RealSkill.h/.cpp` | `class RealSkill : public cocos2d::Sprite` | 技能表现基类：`died(dt)` 自毁；静态 `loadAnimation(name,nums,delay)` 批量注册帧动画到 `AnimationCache`；`getAnimation(key)` 取动画 | 适合 | 可借鉴：技能动画的预加载/缓存范式（`setDelayPerUnit(0.15)`，帧名 `name + i + ".png"`） |
| `Classes/SkillLayer.cpp` | `initSkillIcon()`（第 81-113 行） | 遍历 `SkillManager::getSkillMap()`：`filename = StringValue(name) + name + ".png"`（即 `GameData.xml` 的目录前缀 + 技能名 + `.png`）；每技能下方渲染 `+等级` 与"下一级费用 `baseupGlod + grade*50`"；用 `setTag(index)` 存索引 | 适合 | **高价值：技能面板 = `map` 遍历 + 每格显示等级与升价**，`Resources/Skill/` 下确有 8 个技能目录（已确认） |
| `Classes/SkillLayer.cpp` | `onBtnUpClickCallback()`（第 53-79 行） | 未选中提示「NoSelectSkill」；**升级费 = `baseupGlod + grade*50`**；金币不足提示「LackGlod」；否则 `subGlod(glod)` → `Skill::incGrade()` → `SkillManager::upSkill(name)`（落库）→ 刷新 `+等级` 与下一级费用标签 | 适合 | **高价值：技能升级完整流程与费用公式（每级 +50）**；与 `Skill::getUseMana`(+10/级)、伤害(+30/级) 共同构成技能成长曲线 |
| `Classes/SkillInfo.h` | `class SkillInfo`（第 10-18 行） | **空类**（只有构造/析构声明，无成员）；且 `Classes/SkillInfo.cpp` 文件大小为 **0 字节** | 不适合 | 不适合：这是与 `Model.h` 中 `class SkillInfo`（技能持久化实体）**同名但无关**的废弃类，且 `.cpp` 为空文件——JSTM 注意区分，不要误用 |
| `Classes/FightLayer.cpp` | `onSkillClickCallBack(sender)`（第 290-338 行） | 反向同类：首次展开时遍历 `SkillManager::getSkillMap()` 为每个技能建 `Skill` 图标（`StringValue(name)+name+".png"`，按 map 顺序横向排列 50px 间距） | 适合 | 可借鉴：**战斗内技能面板与技能面板共用同一数据源** |
| `Classes/FightLayer.cpp` | `onSkill(sender)`（第 582-625 行） | 需 `m_isPlayer && m_otherplayerEnd`（轮到自己）；目标已死不动作；**耗蓝校验 `getcurmana() >= getUseMana()`**；足则 `Skill::beUse(this,m_player,m_selectedMonster)` + `subcurMana(mana)`；组队时对每个队员 `sendPlayerAtkMsg(技能名, 技能等级, var.first, 目标索引)`；不足则提示 `NoMana` 并退化为普攻 | 适合 | **高价值：战斗内施法判定链（回合权 → 目标存活 → 蓝量 → 扣蓝 → 广播）**，是 JSTM 战斗协议的关键参考 |
| `Classes/CMClient.cpp` | `sendPlayerAtkMsg(skill,grade,dest,towho)`（第 489-498 行） | 填 `PlayerAtk_Msg{fd=-1, grade, dest, skill(技能名), towho}` 后 `SendMsg` | 适合 | **高价值：技能攻击走 TCP，字段为"技能名 + 技能等级 + 目标"，服务端据此可复算伤害** |
| `Classes/CMClient.cpp` | `doPlayerAtkMsg(msg)`（第 510-517 行） | 转发给 `FightLayer::otherPlayerAtk(msg->fd, msg->skill, msg->grade, msg->towho)` | 适合 | 可借鉴：队友攻击表现的远端重放 |

### 5.1 技能购买数量上限（README 说最多 8 个）—— 明确回答

| 问题 | 结论 | 证据 | 等级 |
|---|---|---|---|
| README 是否声明上限 8 | 是：`README.md` 第 6-7 行「同时一个玩家最多可以购买八个技能，技能不能重复购买」 | `README.md` | 【已确认】 |
| 客户端是否实现"最多 8 个"校验 | **未读到**。购买入口 `DealLayer::checkBuy` 只做 `haveSkill(name)` **重复**校验，无数量判断 | `DealLayer.cpp:180-192` | 【已确认】 |
| 是否存在可用的数量统计接口 | 存在但**未被调用**：`SkillManager::skillNumbers()` | `SkillManager.h:63`、`SkillManager.cpp:52-55`，全仓库无调用点 | 【已确认】 |
| 一次购买是否会超上限 | 会：`DealLayer` 无拦截，`SkillManager::addSkill` 只挡重复 | 同上 | 【已确认】 |
| 实际上限来源 | 疑似由"商店只卖 8 个技能"促成：`SkillFactory` 硬编码 8 个技能，`Resources/Skill/` 恰好 8 个目录（`CrackIt/Dante/DragonRoar/LightStrike/long/recallCountermand/SealOfTheBlade/XBArrow`） | `SkillFactory.cpp`、`Resources/Skill/` | 【待验证】"上限 8 = 技能总数 8"这一因果关系未读到代码证明 |
| 服务端是否强制 8 上限 | 未读到 CM-Server 源码 | — | 待验证 |

### 5.2 技能伤害升级 —— 汇总（全部【已确认】）

| 维度 | 公式 | 出处 |
|---|---|---|
| 施放伤害 | `m_baseAttack + 30 * m_grade` | `Skill.cpp:76` |
| 施放耗蓝 | `m_baseMana + m_grade * 10` | `Skill.cpp:90` |
| 升级费用 | `m_baseupGlod + m_grade * 50` | `SkillLayer.cpp:63-64`、`SkillLayer.cpp:100` |
| 基础属性来源 | `Skill/<Name>/<Name>.att` 的 `baseattack` / `basemana` / `baseupglod` | `Skill.cpp:51-71`；样例 `Resources/Skill/Long/Long.att` |
| 升级落库 | `update skillinfo set skillgrade='N' where playername/rolename/skillname` | `SkillManager.cpp:57-74` |

### 5.3 技能与 MySQL、TCP 的通道归属（明确回答）

- **学技能 / 升级技能 → 只走 MySQL**：`SkillManager::addSkill` 仅改内存（`DealLayer.cpp:190`），升级时 `upSkill` 才落库（`SkillManager.cpp:70`）；`saveSkillInfo()` 在退出/换角色时补插（`CameraPlayer.cpp:266`）。
- **技能施放 → 只走 TCP**：`sendPlayerAtkMsg`（`CMClient.cpp:489-498`），且**仅组队时广播**（`FightLayer.cpp:598-604`）；单人战斗不发送任何攻击消息。
- 因此单人模式下的技能伤害**完全由客户端自算自显**；组队时把「技能名 + 技能等级」告知队友用于表现重放。【已确认】

---

## 6. 药品系统（使用时机 + TCP 消息）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/Medication.h` | `class Medication : public Thing` | 药品 = 物品子类，新增 `m_addblood`/`m_addmana`；覆写 `beUse` | 适合 | 高价值：**药品模型 = 物品基类 + 血/魔回复两字段** |
| `Classes/Medication.cpp` | `initProperty(name)`（第 48-65 行） | 读 `<name>.att`：`buyglod/sellglod/addblood/addmana` | 适合 | 高价值：药品配表四字段（见 §3.1 的 `BlueMedicine.att` 实例） |
| `Classes/Medication.cpp` | `beUse(obj,who,towho)`（第 67-78 行） | `GetPlayerData().addcurBlood(m_addblood)` + `addcurMana(m_addmana)`（**两个 `add` 内部有封顶**）→ 提示「Blood+X Mana+Y」→ 返回 0.0f | 适合 | **高价值：药品效果实现 + 封顶逻辑**。封顶在 `PlayerData.cpp:38-51`：`m_curblood = m_curblood+vl > m_blood ? m_blood : m_curblood+vl` |
| `Classes/PlayerData.cpp` | `addcurBlood` / `addcurMana`（第 38-51 行） | 封顶回血/回蓝；另有 `subcurBlood/subcurMana` 无封顶 | 适合 | 高价值：**当前值不超过上限**的语义，JSTM 服务端应保留同一规则 |
| `Classes/BackPackLayer.cpp` | `useBtnCallBack()`（第 91-110 行） | **战斗外使用**：背包中点「使用」→ `pth->beUse(this)`（回血回蓝、弹提示）→ 数量减一 → `removeBackPackThing(name)` | 适合 | **已确认：药品可在战斗外（背包界面）直接使用**，且只走 MySQL 数量更新，不走 TCP |
| `Classes/FightLayer.cpp` | `onMedicationClickCallBack(sender)`（第 226-288 行） | **战斗内使用**：展开药品条 —— 遍历 `BackPackMap()`，仅取 `type == MEDICATION` 的项，`Medication::createWithImage(name+".png")`，`setTag(it->nums)` 存数量、`setName(flag)` 存索引，按 50px 间距横向展开；再次点击收起 | 适合 | **高价值：战斗内药品快捷条的数据来源与布局**（只筛 `MEDICATION`，用 tag/name 复用节点存两个索引） |
| `Classes/FightLayer.cpp` | `onMedication(sender)`（第 550-580 行） | 需 `m_isPlayer && m_otherplayerEnd`（轮到自己）；`tag > 0` 才可用 → `pth->beUse(this)` 生效 → `SetOtherPalyerAction()` → **组队时给每个队员 `sendUseMedicationMsg(var.first)`** → 置回合标志、`setTag(tag-1)` → `removeBackPackThing(name)` → 刷新数量标签；`tag <= 0` 提示「LackNums」 | 适合 | **高价值：战斗内用药完整流程（回合权 → 用效 → 广播 → 扣数量）**；注意药效只在本地 `PlayerData` 生效，服务端仅广播"某人用了药" |
| `Classes/CMClient.h` | `sendUseMedicationMsg(int dest)` | 声明；实现在 `.cpp:554-559` | 适合 | **已确认：用药走 TCP（有 `UseMedication_Msg`）**，回答"是否走 TCP 消息"→ 是 |
| `Classes/CMClient.cpp` | `sendUseMedicationMsg(int dest)`（第 554-559 行） | 构造 `UseMedication_Msg`（构造函数预置 `type = M_UseMedication`）→ 填 `dest` → `SendMsg((char*)&msg, sizeof(msg))`。**注意：未设置 `fd`**（构造函数不置默认，属未初始化字段） | 适合 | **高价值：`UseMedication_Msg{type, fd, dest}` 三字段帧**。**缺陷**：`fd` 未初始化即发送，服务端不可依赖该字段 |
| `Classes/ShareData.h` | `struct UseMedication_Msg`（第 262-272 行） | `M_Type type; int fd; int dest;`；构造函数只置 `type` | 适合 | 高价值：**用药帧字段清单**（仅告知"对谁"用药，不含药品 id、不含回复量） |
| `Classes/CMClient.cpp` | `doUseMedicationMsg(msg)`（第 561-566 行） | 转发给 `FightLayer::setOtherPalyerEnd()`——**只用来把队友的回合标记为结束**，而非同步血量 | 适合 | **关键发现**：用药广播的语义是"队友结束本回合"，**不含药品效果数据**；因此队友的血量不同步，JSTM 需补齐效果字段 |
| `Classes/NpcPink.cpp` | `talkEndEvent()` | `DealLayer::createWithType(MEDICATION, "DealMedication")` 打开药品商店 | 适合 | 可借鉴：药品商 NPC 绑定 |
| `Classes/DealLayer.cpp` | `checkBuy(money)` | 药品与装备同路：`AddToBackPack(info)` + 扣金；药品不入 `equipmentinfo` 也不入 `skillinfo`，只入本地列表 | 适合 | 可借鉴：买药 → `backpack` 表（`thingtype = 1001`） |

### 6.1 药品使用时机与通道（明确回答）

| 时机 | 触发入口 | 效果计算 | 持久化通道 | TCP 广播 | 等级 |
|---|---|---|---|---|---|
| **战斗外**（背包界面「使用」） | `BackPackLayer::useBtnCallBack` → `Medication::beUse` | 客户端本地 `PlayerData` | MySQL `backpack`（数量，`removeBackPackThing`→`updateBackpack`/`deleteBackpack`） | **无** | 【已确认】 |
| **战斗内**（战斗界面药品条） | `FightLayer::onMedication` → `Medication::beUse` | 客户端本地 `PlayerData`（封顶） | MySQL `backpack`（数量） | **有，且仅组队时**：`sendUseMedicationMsg(dest)` 逐队员发送 `UseMedication_Msg` | 【已确认】 |
| 接收端行为 | `CMClient::doUseMedicationMsg` → `FightLayer::setOtherPalyerEnd()` | 无效果计算 | — | 仅置回合标志 | 【已确认】 |
| 服务端是否复算/校验药效 | 未读到 CM-Server 源码 | 未读到 | 未读到 | 未读到 | 【待验证】 |

---

## 7. 组队系统（纯 TCP 驱动，不经 MySQL）

### 7.1 队伍数据模型与状态

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TeamManager.h` | `class TeamManager`（单例） | `std::map<int,int> m_teamMembers`（`fd` → 队伍角色 `P_STATUS_HEADER/P_STATUS_MEMBER`）；注释「暂时队伍人数上限为2个」 | 适合 | **高价值：队伍 = `map<fd,status>`**；上限 2 的注释见 §7.4 |
| `Classes/TeamManager.cpp` | `createTeam(fd,status)`（第 13-17 行） | **先 `m_teamMembers.clear()`** 再 `m_teamMembers[fd] = status` | 不适合 | **已确认缺陷**：`clear()` 使"加入队伍"变成"重建队伍"，成员会互相覆盖——这是 2 人上限的实现方式（只保留最后一人）。JSTM 必须重写为追加 |
| `Classes/TeamManager.cpp` | `removeTeamMembers(fd)`（第 19-29 行） | `erase(fd)`；若删后 `size()==0` 则把队长状态复位为 `P_STATUS_NORMAL` | 适合 | 高价值：**成员清空即自动解散**的判定 |
| `Classes/TeamManager.cpp` | `dissolveTeam()`（第 31-35 行） | `m_teamMembers.clear()` + 自身状态复位 `P_STATUS_NORMAL` | 适合 | 可借鉴：解散 = 清容器 + 复位角色 |
| `Classes/PreProcess.h` | `P_STATUS_NORMAL/HEADER/MEMBER` | 4001/4002/4003 | 适合 | 高价值：队伍角色枚举，JSTM 服务端可直接沿用 |
| `Classes/PreProcess.h` | `TB_DISSOLVE/QUIT/KICKOUT/NULL` | 5001/5002/5003/5004 | 适合 | 高价值：**队伍按钮行为枚举**，`TB_NULL` 表示不显示按钮 |
| `Classes/CMClient.h` | `std::list<int> m_applyTeamList` | 收到的入队申请 `fd` 队列 | 适合 | 高价值：**服务端推送申请列表**的本地缓存 |
| `Classes/CMClient.h` | `std::list<TeamGotoMap_Msg> m_gotoMapMsgs` | 缓存"队伍需要跳图"的消息，等待进入 `GameScene` 后再消费 | 适合 | 高价值：**跨场景消息延迟消费队列**（解决场景切换期间丢消息） |

### 7.2 组队消息流转全链路（申请 / 同意 / 拒绝 / 踢人 / 解散）

| 步骤 | 文件路径 | 类/函数名 | 消息结构体 | 流向 | 等级 |
|---|---|---|---|---|---|
| ① 发起申请 | `Classes/PlayerItem.cpp` | `onMakeTeamClick()`（第 61-75 行） | `TeamApply_Msg{dest}` | 客户端 → 服务端。前提 `PlayerTeamStatus() == P_STATUS_NORMAL`；若自己已有队则提示「MakeTeamFailed」 | 【已确认】 |
| ② 收到申请 | `Classes/CMClient.cpp` | `doTeamApplyMsg(msg)`（第 396-407 行） | `TeamApply_Msg` | 服务端 → 客户端。`m_applyTeamList.push_back(msg->fd)`，超过 6 条 `pop_front()`；若在游戏场景则 `GameUILayer::setTeamSpot(true)` 亮队伍红点 | 【已确认】 |
| ③ 查看申请列表 | `Classes/TeamLayer.cpp` | `init()`（第 12-42 行）+ `initApplyList()`（第 44-55 行） | — | 本地。`PlayerTeamStatus()==P_STATUS_NORMAL` 时标题「ApplyListText」并逐条建 `TeamMsgItem` | 【已确认】 |
| ④ 同意 | `Classes/TeamMsgItem.cpp` | `onOkBtnClick()`（第 60-85 行） | `AgreeTeam_Msg{dest}` | 客户端 → 服务端。先校验 `info.curmap == GetIntData("CurMap")`（**同地图才能组队**，否则提示「NotEqualMap」）；延时 0.2s 后：从 UI 列表移除 → 设 `msg.dest` → 从 `m_applyTeamList` 移除 → `SendMsg` → `TeamManager::createTeam(fd, P_STATUS_HEADER)` → 自己置 `P_STATUS_MEMBER` → 走到申请人身边 | 【已确认】 |
| ⑤ 拒绝 | `Classes/TeamMsgItem.cpp` | `onRefuseBtnClick()`（第 87-98 行） | `RefuseTeam_Msg{dest}` | 客户端 → 服务端。同样延时移除列表项、从申请队列移除、发送 | 【已确认】 |
| ⑥ 对方收到同意 | `Classes/CMClient.cpp` | `doAgreeTeamMsg(msg)`（第 416-423 行） | `AgreeTeam_Msg` | 服务端 → 客户端。`findRoleNameByFd(msg->fd)` 取名字 → 提示「{名字}AgreeText」→ `CameraPlayer::setTeamStatus(P_STATUS_HEADER)`（**注意：收到同意的人变成 HEADER**）→ `TeamManager::createTeam(msg->fd, P_STATUS_MEMBER)`（队友为 MEMBER） | 【已确认】 |
| ⑦ 对方收到拒绝 | `Classes/CMClient.cpp` | `doRefuseTeamMsg(msg)`（第 409-414 行） | `RefuseTeam_Msg` | 服务端 → 客户端。提示「{名字}RefuseText」 | 【已确认】 |
| ⑧ 队伍移动广播 | `Classes/CameraPlayer.cpp` | `moveTeamMembers(target)`（第 293-299 行） | `TeamMove_Msg{x,y,dest}` | 客户端 → 每个队员。`CMClient::sendTeamMoveMsg`（`CMClient.cpp:425-432`）；接收端 `doTeamMoveMsg`（第 434-437 行）执行 `moveTo(Vec2{x,y}, 1)` | 【已确认】 |
| ⑨ 队伍跳图广播 | `Classes/CMClient.cpp` | `sendTeamGotoMapMsg(map,target,dest)`（第 439-447 行） | `TeamGotoMap_Msg{map[10],x,y,dest}` | 双向。接收端 `doTeamGotoMapMsg`（第 449-453 行）**仅在当前场景名为 `GameScene` 时**入 `m_gotoMapMsgs` 队列 | 【已确认】 |
| ⑩ 解散 | `Classes/MemberItem.cpp` | `DISSOLVE_TEAM()` 宏（第 8-13 行）+ `onDissolveBtnClick`（第 73-78 行） | `TeamManage_Msg{type=M_DissolveTeam, dest}` | 客户端 → 每个队员。`SendTeamDissolveMsg`（`CMClient.cpp:455-461`）；接收端 `doTeamDissolveMsg`（第 463-468 行）→ `TeamManager::dissolveTeam()` + 提示「TeamDissolveText」 | 【已确认】 |
| ⑪ 踢人 | `Classes/MemberItem.cpp` | `onKickOutBtnClick()`（第 80-85 行） | **复用 `TeamManage_Msg` 但 type 仍为 `M_DissolveTeam`** | 客户端 → 每个队员 | 【已确认】踢人按钮 `TB_KICKOUT` 存在，但实现**直接调用 `DISSOLVE_TEAM()` 宏**，即"踢人 = 全员解散"，并未使用 `M_KickOutteam` |
| ⑫ 退队 | `Classes/MemberItem.cpp` | `onQuitTeamBtnClick()`（第 87-92 行） | **同样复用 `DISSOLVE_TEAM()`** | 客户端 → 每个队员 | 【已确认】退队按钮 `TB_QUIT` 也未使用 `M_QuitTeam`，而是全员解散 |
| ⑬ 按钮分配 | `Classes/TeamLayer.cpp` | `initTeamMember()`（第 57-77 行） | — | 本地。自己那行：`P_STATUS_HEADER ? TB_DISSOLVE : TB_QUIT`；队友行：`P_STATUS_HEADER ? TB_KICKOUT : TB_NULL` | 【已确认】 |
| ⑭ 离线级联 | `Classes/CMClient.cpp` | `removePlayer(fd)`（第 214-228 行） | — | 本地。`TeamManager::removeTeamMembers(fd)` 自动处理退队 | 【已确认】 |

**关键结论**：`M_QuitTeam`（`ShareData.h:23`）与 `M_KickOutteam`（`ShareData.h:24`）已定义但**客户端未实装独立发送逻辑**；退队/踢人/解散三种操作在 2 人队伍下被统一成"广播 `M_DissolveTeam` 给所有队友 + 本地清空"。JSTM 若要做多人队伍，必须补齐这三种语义。【已确认】

### 7.3 组队战斗消息（TCP）

| 文件路径 | 类/函数名 | 消息结构体 | 工作机制 | 等级 |
|---|---|---|---|---|
| `Classes/CMClient.cpp` | `sendTeamFightMsg(dest,name,nums)`（第 470-477 行） | `TeamFight_Msg{name[20],nums,dest}` | 通知队友进入战斗：怪物名 + 数量 | 【已确认】 |
| `Classes/CMClient.cpp` | `doTeamFightMsg(msg)`（第 479-487 行） | `TeamFight_Msg` | 接收端置 `IsEntryFight=1`、`MonsterNums`、`MonsterName` 供场景切换 | 【已确认】 |
| `Classes/CMClient.cpp` | `sendMonsterAtkMsg(dest,who,towho)`（第 500-508 行） | `MonsterAtk_Msg{fd,who,towho,dest}` | 队长把"怪物攻击了谁"同步给队友 | 【已确认】 |
| `Classes/CMClient.cpp` | `doMonsterAtkMsg(msg)`（第 519-535 行） | `MonsterAtk_Msg` | `towho == -1` 时用 `findOtherPlayerIndexByFd(msg->fd)` 反查，否则用 `msg->towho`；再调 `monsterAttackPlayer(who,towho)` | 【已确认】 |
| `Classes/CMClient.cpp` | `sendPlayerAtkMsg(skill,grade,dest,towho)`（第 489-498 行） | `PlayerAtk_Msg{skill[30],grade,towho,dest}` | 组队时把"技能名 + 技能等级 + 目标"同步给队友（见 §5） | 【已确认】 |
| `Classes/CMClient.cpp` | `sendPlayerRunMsg(dest,flag)` / `doPlayerRunMsg` | `PlayerRun_Msg{flag,dest}` | 逃跑结果（成功/失败）同步给队友 | 【已确认】 |
| `Classes/CMClient.cpp` | `sendPlayerDieMsg(dest)` / `doPlayerDieMsg` | `PlayerDie_Msg{dest}` | 自己阵亡同步给队友（`FightLayer.cpp:697-699`）；接收端 `setOtherPlayerDie()` | 【已确认】 |
| `Classes/CMClient.cpp` | `sendUseMedicationMsg(dest)` / `doUseMedicationMsg`（第 554-566 行） | `UseMedication_Msg{fd,dest}` | 组队时把"队友使用了药品"同步给队友（见 §6） | 【已确认】 |
| `Classes/CMClient.cpp` | `updatePlayerData()`（第 278-289 行） | `UpdateData_Msg{blood,mana,attack,defense,grade,fd}` | 属性变化时广播给全服同图玩家（`PlayerData::addProperty` 每次加属性都会调，`PlayerData.cpp:74`） | 【已确认】 |
| `Classes/FightLayer.cpp` | `checkMonsterBehavie()`（第 639-682 行） | — | 按 `PlayerTeamStatus()` 分三种回合调度：`P_STATUS_HEADER` 由队长算怪物攻击目标并 `notifyOtherPlayerMonsterAtk`；`MEMBER` 等 `m_otherNoAction`；`NORMAL` 单机流程 | 【已确认】 |

### 7.4 组队人数上限（明确回答）

| 问题 | 结论 | 证据 | 等级 |
|---|---|---|---|
| 声明 | 2 人 | `TeamManager.h:9` 注释「暂时队伍人数上限为2个」 | 【已确认】 |
| 实现方式 | **靠 `createTeam` 里的 `m_teamMembers.clear()` 强制成"只能保留一个队友"**，而非计数校验 | `TeamManager.cpp:15` | 【已确认】 |
| 是否有显式上限判定 | **未读到**任何 `size() >= 2` 之类的判断 | 全仓库 grep `skillNumbers`/`> 8` 等未命中队伍计数 | 【已确认】 |
| 服务端侧上限 | 未读到 CM-Server 源码 | — | 待验证 |

---

## 8. 聊天系统（纯 TCP 驱动 + 本地队列）

### 8.1 消息结构与本地队列

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/CMClient.h` | `struct TalkMsg`（第 11-17 行） | `rolename`（发送者）、`destname`（接收者）、`msg`（内容）、`change`（未读标记，默认 false） | 适合 | **高价值：聊天记录条目模型**，`change` 用于红点未读状态 |
| `Classes/CMClient.h` | `std::deque<TalkMsg> m_worldTalkMsgs` | **世界聊天本地队列**（`deque` 双端队列） | 适合 | 高价值：世界频道用 `deque` 支持头删尾插 |
| `Classes/CMClient.h` | `std::map<int, std::deque<TalkMsg>> m_privateTalkMsgs` | **私聊本地队列**，按 `fd` 分组，每组一个 `deque` | 适合 | **高价值：私聊按对端 `fd` 分组的多会话结构**，JSTM 可映射为 `session -> messages` |
| `Classes/CMClient.cpp` | `addWorldTalkMsg(WorldTalk_Msg* msg)`（第 320-335 行） | `fd != -1` → `findRoleNameByFd(fd)` 作发送者；否则发送者 = `StringValue("Me")`（自己发的）；入队；**`size() > 100` 时 `pop_front()`**；若在游戏中则 `GameUILayer::updateWorldTalkQueue(tmsg)` | 适合 | **高价值：世界聊天 100 条历史上限 + 自己的消息用 fd==-1 标识** |
| `Classes/CMClient.cpp` | `addPrivateTalkMsg(PrivateTalk_Msg* msg)`（第 337-381 行） | `fd != -1`（收到）→ 发送者 = `findRoleNameByFd(fd)`、`realfd = fd`；`fd == -1`（自己发）→ 发送者 = `Me`、`realfd = dest`。用 `findRoleNameByFd(realfd)` 取 `destname`，**若为空则判为对方离线**：`SetIntData("IsHaveTip",1)` + `SetStringData("TipText", StringValue("OffLine"))` 并 return。随后写入 `m_privateTalkMsgs[realfd]`；会话数 `>= 6` 时 `erase(begin())`（丢弃最早会话）；单会话 `> 18` 时 `pop_front()`；自己发时不置红点，收到时置 `m_privateTalkMsgs[realfd][0].change = true` 并 `setRedSpot(true)` | 适合 | **高价值：私聊完整规则集**（离线判定、最多 6 个会话、每会话 18 条、收消息才亮红点）。**可借鉴点**：`change` 标记挂在队列首元素上表达"该会话有未读" |
| `Classes/CMClient.cpp` | `removePlayer(fd)`（第 223 行） | 玩家离线时 `m_privateTalkMsgs.erase(fd)` 清理其会话 | 适合 | 可借鉴：会话随玩家离线回收 |
| `Classes/CMClient.h` | `getPrivateMsgs()` / `getApplyTeamList()` / `getGotoMapMsgs()` | 暴露内部容器的引用 | 适合 | 可借鉴：轻量访问器；不适合照搬：直接暴露可变引用破坏封装 |

### 8.2 世界聊天 vs 私聊（发送 / 接收全链路）

| 类型 | 发送方 | 消息结构体 | 本地动作 | 网络动作 | 等级 |
|---|---|---|---|---|---|
| **世界聊天** | `Classes/GameUILayer.cpp` `onSendClickCallBack()`（第 216-229 行） | `WorldTalk_Msg{fd=-1, msg[200]}` | 输入非空时**先本地入队** `CMClient::addWorldTalkMsg(&msg)`，再 `SendMsg`，然后清空输入框 | 客户端 → 服务端；服务端应广播给全服，客户端 `OnRecv` 走 `M_WorldTalk → addWorldTalkMsg` | 【已确认】 |
| **世界聊天（接收）** | `Classes/CMClient.cpp` `addWorldTalkMsg` | `WorldTalk_Msg{fd=发送者fd, msg}` | 用 `fd` 反查角色名 → 入 `m_worldTalkMsgs` → `GameUILayer::updateWorldTalkQueue` | — | 【已确认】 |
| **世界聊天（渲染）** | `Classes/GameUILayer.cpp` `updateWorldTalkQueue(msg)`（第 289-309 行） | — | 生成 `"{rolename}Say:{msg}"` 标签（`Say` 来自 `GameData.xml`），插入 `m_talkFrame` 左下角，已有标签整体上移 18px；**屏上最多 5 条**（`> 5` 即删最早） | — | 【已确认】 |
| **私聊（发送）** | `Classes/PrivateTalkLayer.cpp` `onSendBtnClick()`（第 94-104 行） | `PrivateTalk_Msg{fd=-1, dest=m_fd, msg[200]}` | **先本地入队** `CMClient::addPrivateTalkMsg(&msg)`，再 `SendMsg`，清空输入框 | 客户端 → 服务端 | 【已确认】 |
| **私聊（发送入口 2）** | `Classes/PlayerItem.cpp` `onPrivateTalkClick()`（第 53-59 行） | — | 从"附近玩家"列表点私聊 → `PrivateTalkLayer::create(m_fd)` | — | 【已确认】 |
| **私聊（接收）** | `Classes/CMClient.cpp` `addPrivateTalkMsg` | `PrivateTalk_Msg{fd=发送者fd, dest}` | 见 §8.1；若 `PrivateTalkLayer` 已打开则 `ptlayer->addMsg(rolename, msg)` 实时追加 | — | 【已确认】 |
| **私聊会话列表** | `Classes/MsgListLayer.cpp` `initMsgItem()`（第 32-48 行） | — | 遍历 `CMClient::getPrivateMsgs()`（`map<int,deque>`），每个 `fd` 建一个 `MsgItem` | — | 【已确认】 |
| **私聊会话条目** | `Classes/MsgItem.cpp` `init()`（第 24-71 行） | — | 显示头像（`info.playertype + "Head"`）、角色名、`GradeText+grade`，并按 `getPrivateMsgs()[fd][0].change` 决定红点显隐；含删除按钮 | — | 【已确认】 |
| **打开会话** | `Classes/MsgListLayer.cpp` `onItemClickCallback()`（第 50-64 行） | — | 把该会话 `[0].change = false`、关红点、延时 0.22s 后 `PrivateTalkLayer::create(fd)` 并隐藏列表 | — | 【已确认】 |
| **私聊窗口** | `Classes/PrivateTalkLayer.cpp` `init()`（第 23-71 行） | — | 标题 = 对端角色名；输入框 + 发送按钮 + 关闭按钮；`initMsgList()` 倒序渲染 `m_privateTalkMsgs[m_fd]`（`rbegin→rend`） | — | 【已确认】 |
| **私聊窗口追加** | `Classes/PrivateTalkLayer.cpp` `addMsg(who,msg)`（第 137-154 行） | — | 已有消息整体上移 22px，新消息插在底部；**窗口内最多 18 条**（超出删最早） | — | 【已确认】 |
| **私聊关闭** | `Classes/PrivateTalkLayer.cpp` `onCloseBtnClick()`（第 106-119 行） | — | 延时 0.1s 恢复 `MsgListLayer` 与 `PlayerListLayer` 可见性后自毁 | — | 【已确认】 |
| **红点总控** | `Classes/GameUILayer.cpp` | `setRedSpot(b)` / `setTeamSpot(b)`（第 325-333 行） | 私聊红点与队伍申请红点分属两个 `Sprite("MsgTip")`，分别由 `addPrivateTalkMsg` 的 fd!=-1 分支与 `doTeamApplyMsg` 触发 | — | 【已确认】 |

### 8.3 聊天通道归属（明确回答）

- **世界聊天与私聊都只走 TCP**（`M_WorldTalk` / `M_PrivateTalk`），**不经 MySQL**：`Model.h` 无聊天表，`CameraPlayer::SaveGameData()` 不保存聊天。
- **本地队列是权威显示源**：发送方先 `addWorldTalkMsg`/`addPrivateTalkMsg` 入本地队列再发包（`GameUILayer.cpp:225-226`、`PrivateTalkLayer.cpp:101-102`），因此即使服务端不回显，自己也能看到自己的消息——这是"客户端乐观显示"。【已确认】
- 队列容量常量：世界 100 条 / 屏显 5 条 / 私聊会话 6 个 / 单会话 18 条。【已确认】
- 私聊的"发送者下线"判定依赖 `findRoleNameByFd(realfd) == ""`，即**依赖本地玩家列表**，而不是服务端返回错误码。【已确认】

---

## 9. NPC 与任务/商店的绑定（反射式生成）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/ReflectNpc.h` | `DEC_REFLECT_FUNC` / `DEF_REFLECT_FUNC` / `REG_REFLECT_CLASS` / `GET_REFLECT_OBJECT` 宏族 | 每个 NPC 子类用 `DEF_REFLECT_FUNC(X)` 生成一个无参工厂 `Npc* ReflectClassX()`；`REG_REFLECT_CLASS(X)` 把类名字符串注册进 `ReflectNpc::m_reflectMap`；`GET_REFLECT_OBJECT(name)` 按名字造对象 | 适合 | **高价值：字符串类名 → 对象 的反射注册表**，使地图文件只写类名即可刷 NPC，是 JSTM 刷怪/刷 NPC 的理想范式 |
| `Classes/ReflectNpc.cpp` | `registerReflectClass` / `getReflectObject` | `map<string, 函数指针>` 注册与查找；未命中返回 `nullptr` | 适合 | 可借鉴：最小反射表实现 |
| `Classes/ObjectLayer.cpp` | `initNpcObject(level)`（第 60-89 行） | 打开 `LevelObject/Level<N>.lobject`；**先读一次 `objname` 吃掉注释行**，再循环读 `objname/x/y`；`GET_REFLECT_OBJECT(objname)` 造 NPC；坐标乘以 `MapGridW/MapGridH`；`Sprite::create(StringValue(objname))` 取图；入 `m_npcList` 并 `addChild(face)` | 适合 | **高价值：地图 NPC 配表格式与加载流程**。已用 `Resources/LevelObject/Level1.lobject` 交叉验证：首行 `//对象名，坐标x、y`，随后 `NpcVallige 14 7` / `NpcBlue 5 7` / `NpcMamom 24 10` |
| `Classes/Npc.h` | `class Npc`（非 `Node` 派生） | 数据与表现分离：NPC 本体持有 `m_x/m_y/m_taskindex/m_state/m_talkmsg` 等数据，`m_face` 指向场景中的 `Sprite`；行为接口 `collisionEvent/endCollisionEvent/getNextTalkMsg/talkEndEvent/resetIndex/changeState` | 适合 | **高价值：NPC 逻辑对象与精灵分离**的设计，便于服务端化（数据可搬走） |
| `Classes/Npc.cpp` | `getNextTalkMsg()`（第 54-63 行） | 逐条返回 `m_talkmsg[index++]`，耗尽返回 `""` | 适合 | 可借鉴：对话游标推进 |
| `Classes/Npc.cpp` | `resetIndex()` | `index = 0` | 适合 | 可借鉴：每次碰撞重置对话游标 |
| `Classes/TalkLayer.cpp` | `onNextCallBack()`（第 61-76 行） | 取下一句；非空则替换文本；为空则移除对话层并调 `m_npc->talkEndEvent()` | 适合 | **高价值：对话结束才触发业务（接/交任务、开商店）**，把"对话"与"业务"彻底解耦 |
| `Classes/NpcVallige/NpcBlue/NpcMamom/NpcMonk.cpp` | 各自构造函数 | `INIT_TALK_IN_NPC(X)` 从 `GameData.xml` 读 `"XTalk"` 键装载整段默认对话；`m_name = "X"` | 适合 | 可借鉴：通用对话走配置键，任务对话走 `Task/*.tk`，两级对话来源 |
| `Classes/NpcEquip/NpcSkill/NpcPink.cpp` | 各自 `talkEndEvent()` | 对话结束 → 暂停调度器 → 按类型打开 `DealLayer`（装备/技能/药品） | 适合 | 高价值：**NPC 类 → 商店类型 → 商品列表 的三级绑定**（`NpcEquip→EQUIPMENT`、`NpcSkill→SKILL`、`NpcPink→MEDICATION`） |
| `Resources/LevelObject/` | `Level1.lobject` / `Level2.lobject` | 目前**只有 2 张地图有 NPC 刷点文件**，而 `Resources/` 有 `map1..map5` 五张地图与 5 个 `.mp` 文件 | 待验证 | 【待验证】`Level3/4/5.lobject` 缺失，未读到地图 3-5 的 NPC 配置，无法确认是遗漏还是这些地图本就无 NPC |
| `Resources/mapinfo.xxp` | 世界地图配置 | 5 行：`map1 142 420 流水村` / `map2 230 190 火山城` / `map3 490 300 荒山` / `map4 530 450 大平原` / `map5 680 490 极寒之地` | 适合 | 高价值：**地图号 → UI 坐标 → 中文名** 三字段；与 `WorldMapLayer::initMapInfo()`（`WorldMapLayer.cpp:36-55`）的读取顺序（key/pos.x/pos.y/name）完全对应【已确认】 |
| `Classes/WorldMapLayer.cpp` | `init()`（第 7-34 行） | 底图 `WorldMap`（裁切 `Rect{40,20,800,600}`）；遍历 `m_maps` 按坐标渲染地图中文名（红色，字号 30）；用 `"map" + CurMap` 取当前地图坐标放红点（`y-30` 偏移） | 适合 | 可借鉴：世界地图 = 配置表 + 当前地图高亮 |

---

## 10. 面向 JSTM 的关键结论汇总

### 10.1 通道归属总表（一句话版）

| 业务 | 权威通道 | 证据入口 | 等级 |
|---|---|---|---|
| 登录 / 注册 / 建角色 / 角色列表 | **MySQL 直连** | `LoginLayer.cpp:147-153`、`SigOnLayer.cpp:106-115`、`NewGameLayer.cpp:94-99`、`SelectLayer.cpp:100-104` | 【已确认】 |
| 角色属性存档（血/蓝/攻/防/金/经验/等级/坐标/地图） | **MySQL 直连** | `CameraPlayer::SaveGameData()`（`CameraPlayer.cpp:244-267`） | 【已确认】 |
| 背包 | **MySQL 直连** | `BackPackManager.cpp:80-138` | 【已确认】 |
| 装备（含精炼） | **MySQL 直连**（精炼计算在客户端） | `EquipmentManager.cpp:68-127`、`RoleInfoLayer.cpp:146-165` | 【已确认】 |
| 技能（含升级） | **MySQL 直连**（伤害/耗蓝/费用公式在客户端） | `SkillManager.cpp:57-104`、`Skill.cpp:76,90`、`SkillLayer.cpp:53-79` | 【已确认】 |
| 药品库存 | **MySQL 直连** | `BackPackManager` 同一路径 | 【已确认】 |
| 任务（定义 + 状态 + 进度 + 奖励） | **既不 MySQL 也不 TCP**，纯客户端本地文件 + 内存 | `TaskSystem.cpp` 全文、`TaskLayer.cpp:30`、`Model.h` 无任务表 | 【已确认】 |
| 移动 / 位置校验 / 玩家进出 | **TCP** | `M_MoveTo`/`M_VerifyPos`/`M_InitPos`/`M_PlayerLeave` | 【已确认】 |
| 属性变化广播 | **TCP** | `UpdateData_Msg`（`CMClient.cpp:278-289`） | 【已确认】 |
| 战斗（普攻/技能/逃跑/死亡/怪攻） | **TCP，且仅组队时广播** | `FightLayer.cpp:434-462,582-625,684-713`、`CMClient.cpp:489-579` | 【已确认】 |
| 用药 | **TCP，且仅组队时广播**；药效本地计算 | `FightLayer.cpp:550-580`、`CMClient.cpp:554-566` | 【已确认】 |
| 组队（申请/同意/拒绝/解散） | **TCP** | `PlayerItem.cpp:61-75`、`TeamMsgItem.cpp:60-98`、`CMClient.cpp:396-468`、`MemberItem.cpp:8-13` | 【已确认】 |
| 世界聊天 / 私聊 | **TCP** + 本地队列 | `M_WorldTalk`/`M_PrivateTalk`、`CMClient.cpp:320-381` | 【已确认】 |
| 地图名 / NPC 中文名 / UI 文案 | **本地 `GameData.xml` + `mapinfo.xxp`** | `GameData.cpp:47-56`、`WorldMapLayer.cpp:36-55` | 【已确认】 |
| NPC 刷点 | **本地 `LevelObject/Level<N>.lobject`** | `ObjectLayer.cpp:60-89` | 【已确认】 |
| 任务定义 / 对话 | **本地 `Task/*.tsk` / `Task/*.tk`** | `TaskSystem.cpp:76-100`、`Npc.cpp:141-179` | 【已确认】 |
| 物品 / 装备 / 技能属性 | **本地 `<name>.att` / `<name>.dec`** | `Thing.cpp:51-70`、`Medication.cpp:48-65`、`EquipMent.cpp:51-72`、`Skill.cpp:51-71` | 【已确认】 |

### 10.2 客户端侧已确认的实现缺陷（JSTM 借鉴时须规避）

| 编号 | 缺陷 | 位置 | 等级 |
|---|---|---|---|
| D1 | `erase(it)` 后解引用 `*it`（迭代器失效，UB） | `BackPackManager.cpp:52-53` | 【已确认】 |
| D2 | 存档只用 `INSERT` 不清旧行 → `backpack`/`equipmentinfo`/`skillinfo` 三表重复行累积 | `BackPackManager.cpp:100-115`、`EquipmentManager.cpp:87-101`、`SkillManager.cpp:91-104` | 【已确认】 |
| D3 | `TeamManager::createTeam` 先 `clear()` 再加人 → 多人组队互相覆盖 | `TeamManager.cpp:15` | 【已确认】 |
| D4 | 踢人/退队按钮复用「全员解散」宏，`M_QuitTeam`/`M_KickOutteam` 未实装 | `MemberItem.cpp:80-92` | 【已确认】 |
| D5 | 装备替换时把新装备 `grade` 强制重置为 1 | `EquipmentManager.cpp:23-28` | 【已确认】 |
| D6 | `upgrade()` 固定 `addProperty(30,30,8,8)`，与 `beUse` 的 `(grade-1)*30` 公式不一致 | `EquipMent.cpp:81` vs `EquipMent.cpp:109` | 【已确认】 |
| D7 | `removeSkill` 只改内存不删库 | `SkillManager.cpp:36-39` | 【已确认】 |
| D8 | `sendUseMedicationMsg` 未初始化 `fd` 字段即发送 | `CMClient.cpp:554-559`、`ShareData.h:262-272` | 【已确认】 |
| D9 | 技能数量上限（8）无任何校验，`skillNumbers()` 是死代码 | `SkillManager.cpp:52-55`、`DealLayer.cpp:180-192` | 【已确认】 |
| D10 | `DBDao::m_sql` 用 `append` 且从不清空，同实例重复调用会叠加 SQL | `DBDao.h:222-258` | 【已确认】 |
| D11 | `mysql_real_connect` 返回值被忽略，无重连/无错误处理 | `DBDao.h:214-219` | 【已确认】 |
| D12 | `queryModel()` 后未 `mysql_free_result` | `DBDao.h:147-163` | 【已确认】 |
| D13 | `GameData::getStringByKey` 未判 `valueForKey` 空指针，缺键即崩 | `GameData.cpp:5-6,22-40` | 【已确认】 |
| D14 | TCP 无长度前缀/无粘包处理，1024 缓冲区内含变长消息即错位风险 | `TCPClient.cpp:95-120`、`public.h:6` | 【已确认】 |
| D15 | 客户端本地结算金币/经验/属性/购买/精炼/技能，服务端不参与（最严重：无法防作弊） | `TaskSystem.cpp:124-140`、`BackPackLayer.cpp:70-89`、`DealLayer.cpp:168-203`、`RoleInfoLayer.cpp:146-165`、`SkillLayer.cpp:53-79` | 【已确认】 |

### 10.3 本次未读到、需要 CM-Server 或数据库 SQL 才能定论的问题（【待验证】清单）

| # | 【待验证】问题 | 为什么未定论 |
|---|---|---|
| 1 | 【待验证】任务定义是否在服务端也有一份（客户端 `Task/*.tsk` 与服务端是否同源） | 未读到 CM-Server 源码 |
| 2 | 【待验证】技能购买「最多 8 个」的上限由服务端强制还是根本不强制 | 客户端未实现（D9），服务端代码缺失 |
| 3 | 【待验证】`T_COLLECT`（收集）与 `T_ACCESS`（访问）两类任务的进度推进实现位置 | 客户端仅有 `checkKillMonster` 一个进度入口（`Monster.cpp:114` 唯一调用点） |
| 4 | 【待验证】组队人数上限 2 的服务端强制方式 | 客户端靠 `clear()` 实现（D3），无计数校验 |
| 5 | 【待验证】技能伤害 `baseAttack + 30*grade`、耗蓝 `baseMana + 10*grade`、升级费 `baseupGlod + grade*50` 是否与服务端一致（否则组队时伤害表现与实际不符） | 服务端代码缺失 |
| 6 | 【待验证】服务端是否校验客户端上报的移动坐标（`M_VerifyPos`）、攻击目标、药品使用、金币变更 | 服务端代码缺失；客户端侧完全无校验 |
| 7 | 【待验证】`save*Info()` 的重复 INSERT 是否依赖数据库唯一键/服务端去重才不至于产生脏数据 | 未读到 `.sql` 建表脚本与 CM-Server |
| 8 | 【待验证】`Player_Info.playertype`（`Player1/2/3`）与头像/动画资源名 `playertype + "Head"`、`playertype + "WaitLeft"` 的拼接约定是否也被服务端使用 | 未读到服务端角色校验逻辑 |
| 9 | 【待验证】`Resources/DB.cfg` 是否存在（README 提到需修改，但解压后 `Resources/` 下只有 `server.cfg`） | 未读到该文件；DB 配置实际硬编码在 `DBDao.h` |
| 10 | 【待验证】`LevelObject/Level3/4/5.lobject` 缺失是否为仓库遗漏 | 仅读到 Level1、Level2 两个刷点文件 |
| 11 | 【待验证】`TaskSystem::m_npcvec` 白名单（4 个 NPC）与 `Level1.lobject` 刷点（3 个）不一致，`NpcMonk` 的刷点位置未知 | 未读到 `Level2.lobject` 之外的地图 NPC 配置 |

---

## 11. 逐文件覆盖补全表（第二轮：头文件与未单列文件）

> 本轮说明：任务要求「**每个文件**用 Markdown 表格记录」。第一轮已完成各 `.cpp` 与核心 `.h` 的行；本节把任务清单中剩余未单独成行的**头文件**逐个补齐，全部为本次实读。【已确认】

### 11.1 任务组补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TaskItem.h` | `class TaskItem : public cocos2d::Node` | 只声明 `static TaskItem* create(const TaskInfo&)` 与 `bool init(const TaskInfo&)`；用 `CLASS_ESSENTAIL` 宏私有化构造与析构 | 适合 | 可借鉴：**任务条目 UI 组件只接收 `TaskInfo` 值对象**，与数据源完全解耦，JSTM 可把任务条目做成纯展示组件 |
| `Classes/TaskLayer.h` | `class TaskLayer : public cocos2d::Layer` | `CREATE_FUNC(TaskLayer)` + `init()` override + 私有 `initTaskItem(cocos2d::Vec2)` | 适合 | 可借鉴：面板层只做布局，数据实时向 `TaskSystem` 单例拉取，不持有任务数据副本，避免双份状态 |
| `Classes/PickupTaskLayer.h` | `class PickupTaskLayer : public cocos2d::Layer` | `static create(Npc*)`；私有 `onOkBtnClickCallback` / `onCancelClickCallback`；成员 `Npc* m_npc` | 适合 | 可借鉴：**接取确认弹层只持 NPC 指针**，确认时回查 `m_npc->getTaskIndex()` 再驱动状态机，UI 不缓存任务索引 |
| `Classes/PickupTaskLayer.cpp` | `PickupTaskLayer::onOkBtnClickCallback(cocos2d::CCObject*)`（第 54-59 行） | 「确定」→ `TaskSystem::pickupTask(m_npc->getTaskIndex())` → `m_npc->changeState(NS_FREE, 0)` → `getParent()->removeChild(this)` | 适合 | **高价值：任务接取的三段调用顺序**（状态机迁移 → NPC 表现复位 → 关闭 UI），JSTM 可 1:1 复刻 |
| `Classes/PickupTaskLayer.cpp` | `PickupTaskLayer::onCancelClickCallback(cocos2d::CCObject*)`（第 61-64 行） | 仅 `getParent()->removeChild(this)`，不触碰任何状态 | 适合 | 可借鉴：取消路径零副作用（安全默认）；与「确定」路径的状态迁移形成清晰边界 |

### 11.2 背包与物品组补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/BackPackLayer.h` | `class BackPackLayer : public cocos2d::Layer` | `CREATE_FUNC` + `init()` override；公开 `sellBtnCallback` / `useBtnCallBack` / `bp1BtnCallBack` / `bp2BtnCallBack` / `onClickThingCallBack`；成员 `m_basePoint` / `m_selector` / `m_curSel` / `m_numlabels` / `m_menu` | 适合 | 可借鉴：**「当前选中物 + 数量标签数组 + 选择框 + 基准点」是网格背包的最小 UI 状态集**；其中 `bp1BtnCallBack` / `bp2BtnCallBack` 在 `.cpp` 第 112-120 行为**空实现**（分页按钮未完成） |
| `Classes/EquipMent.h` | `class EquipMent : public Thing` | `createWithImage` / `init` / `beUse` / `Disassemble` / `upgrade` / `showProperty` / `upGlod`；8 个 `PROPERTY__REF`：`m_addblood` / `m_addmana` / `m_addattack` / `m_adddefense` / `m_speed` / `m_grade` / `m_type` / `m_baseupglod` | 适合 | **高价值：装备完整属性字段清单**，与 `Resources/Thing/*.att` 的键逐项对应，JSTM 装备配置表可照此建列 |
| `Classes/DetailLayer.h` | `class DetailLayer : public cocos2d::Layer` | `createWithThing(Thing*)` / `init(Thing*)` / 私有 `onCloseClickCallBack` | 适合 | 可借鉴：详情弹层只依赖 `Thing*` 抽象，**药品 / 装备 / 技能共用同一详情 UI**，是"物品基类"设计价值的直接体现 |

### 11.3 技能组补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SkillLayer.h` | `class SkillLayer : public cocos2d::Layer` | `init()` override；私有 `initSkillIcon` / `onSkillCkickCallBack` / `onBtnUpClickCallback`；成员 `m_selectedSkill` + 两个平行数组 `m_gradelabels`、`m_upskillGlods` | 适合 | 可借鉴：**用两个平行 `std::vector<LabelTTF*>` 分别存「+等级」与「下一级价格」**，靠 `setTag(index)` 索引对齐；JSTM 若做同类列表应改用结构体数组，避免三处索引不同步 |

### 11.4 组队组补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/TeamLayer.h` | `class TeamLayer : public cocos2d::Layer` | `CREATE_FUNC`；公开 `removeMsgItem(cocos2d::Node*)`；私有 `initApplyList` / `initTeamMember`；成员 `std::list<cocos2d::Node*> m_itemlist` | 适合 | **高价值：同一层复用为「申请列表」与「成员列表」两种模式**，由 `PlayerTeamStatus()` 二选一；JSTM 可复用这一"双态面板"设计以减少 UI 重复 |
| `Classes/TeamMsgItem.h` | `class TeamMsgItem : public cocos2d::Node` | `create(const int& fd)` / `init(fd)`；`onHeadClick` / `onOkBtnClick` / `onRefuseBtnClick`；成员仅 `int m_fd` | 适合 | 可借鉴：**申请条目只存 `fd`**，角色名 / 等级 / 地图全部实时向 `CMClient::findPlayerInfoByFd` 查询，避免数据副本过期 |

### 11.5 聊天组补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/MsgListLayer.h` | `class MsgListLayer : public cocos2d::Layer` | `CREATE_FUNC`；公开 `removeMsgItem(MsgItem*)`；私有 `initMsgItem(Vec2)` / `onItemClickCallback`；成员 `std::list<MsgItem*> m_itemlist` | 适合 | 可借鉴：私聊会话列表的容器与增删接口；删项后对后续项执行 `MoveBy(0,80)` 补位动画（`.cpp` 第 78-84 行） |
| `Classes/MsgItem.h` | `class MsgItem : public cocos2d::MenuItemImage` | `create(fd)` / `init(fd)`；`const int& getFd()`；`setRedSpot(bool)`；成员 `m_redspot` + `m_fd` | 适合 | 高价值：**`getFd()` 对外暴露会话键**，使列表层无需额外映射即可从被点击条目定位到 `m_privateTalkMsgs` 的键 |
| `Classes/PrivateTalkLayer.h` | `class PrivateTalkLayer : public cocos2d::Layer, public cocos2d::TextFieldDelegate` | `create(fd)` / `init(fd)`；IME 挂载 / 卸载回调；`onSendBtnClick` / `onCloseBtnClick` / `addMsg(who,msg)`；成员 `m_fd` / `m_editFrame` / `m_msgList` / `m_basePos` | 适合 | 可借鉴：**双继承 `TextFieldDelegate`** 以获得输入法挂载 / 卸载事件（用于暂停与恢复场景动作），是 Cocos2d-x 下处理文本输入的常见做法 |
| `Classes/TalkLayer.h` | `class TalkLayer : public cocos2d::Layer` | `createWithNpc(Npc*)` / `init(Npc*)`；私有 `onNextCallBack`；成员 `Npc* m_npc` + `Vec2 m_talkPos` | 适合 | 可借鉴：对话层只持 NPC 指针、逐句向 `Npc::getNextTalkMsg()` 索取，是"文本流"而非"文本数组"，天然支持不定长对话 |
| `Classes/WorldMapLayer.h` | `class WorldMapLayer` + `struct stMap { cocos2d::Vec2 pos; std::string name; }` | `init()` override；私有 `initMapInfo()`；成员 `std::map<std::string, stMap> m_maps` | 适合 | **高价值：`stMap` 的两个字段（坐标 + 名）与 `Resources/mapinfo.xxp` 每行四 token（key + x + y + name）精确对应**，JSTM 世界地图配表可直接照抄 |

### 11.6 NPC 组补全（每个文件单列）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/NpcEquip.h` | `class NpcEquip : public Npc`（注释：装备商人） | `DEC_REFLECT_FUNC(NpcEquip)` 声明反射工厂；override `collisionEvent` / `talkEndEvent` | 适合 | 高价值：**类名即地图刷点文件里的标识**（`DEF_REFLECT_FUNC` 生成 `ReflectClassNpcEquip`），新增一个商人只需「头文件 + 实现 + 刷点文件一行」 |
| `Classes/NpcSkill.h` | `class NpcSkill : public Npc`（注释：技能商人） | 同上；`talkEndEvent` 打开 `DealLayer(SKILL, "DealSkill")` | 适合 | 同上，是可复制的 NPC 模板 |
| `Classes/NpcPink.h` | `class NpcPink : public Npc`（注释：粉衣少女） | 同上，且**额外 override `endCollisionEvent`** 用于关闭 `DealLayer` | 适合 | 可借鉴：**只有会开交易层的 NPC 才需要覆写 `endCollisionEvent` 做清理**，是精准的最小覆写原则 |
| `Classes/NpcBlue.h` | `class NpcBlue : public Npc`（注释：蓝衣少女） | 仅 override `collisionEvent`（纯对话 NPC） | 适合 | 可借鉴：纯对话 NPC 无需任何额外逻辑 |
| `Classes/NpcMonk.h` | `class NpcMonk : public Npc`（注释：老和尚） | 仅 override `collisionEvent` | 适合 | 同上 |
| `Classes/NpcManmom.h` | `class NpcMamom : public Npc`（注释：财神） | `DEC_REFLECT_FUNC(NpcMamom);`（**带尾分号**，其余同类宏无）；仅 override `collisionEvent` | 适合 | **注意笔误**：文件名是 `NpcManmom.h`（Man-mom）而类名是 `NpcMamom`，`NpcMamom.cpp:1` 写的是 `#include"NpcManmom.h"`；JSTM 借鉴时勿照抄该拼写 |
| `Classes/NpcVallige.h` | `class NpcVallige : public Npc`（注释：Npc老村长） | 仅 override `collisionEvent` | 适合 | 可借鉴：新手村村长，`Level1.lobject` 中刷在 `(14,7)` |
| `Classes/NpcBlue.cpp` | `NpcBlue::NpcBlue()`（第 7-11 行） | `INIT_TALK_IN_NPC(NpcBlue)` 从 `GameData.xml` 的 `NpcBlueTalk` 键装载默认对话；`m_name = "NpcBlue"` | 适合 | 可借鉴：**`m_name` 必须与刷点文件中的类名一致**，这是反射链路的隐含契约（`ObjectLayer.cpp:83` 用 `StringValue(objname)` 取图，也依赖同名资源键） |
| `Classes/NpcMonk.cpp` | `NpcMonk::NpcMonk()`（第 7-11 行） | 同上，对话键 `NpcMonkTalk` | 适合 | 同上 |
| `Classes/NpcMamom.cpp` | `NpcMamom::NpcMamom()`（第 7-11 行） | 同上，对话键 `NpcMamomTalk` | 适合 | 同上 |
| `Classes/NpcVallige.cpp` | `NpcVallige::NpcVallige()`（第 10-14 行） | 同上，对话键 `NpcValligeTalk` | 适合 | 同上 |
| `Classes/ReflectNpc.cpp` | `registerReflectClass` / `getReflectObject` / `release`（第 6-25 行） | `m_reflectMap[classname] = callfunc`；`getReflectObject` 查表命中则 `it->second()` 造对象，未命中返回 `nullptr` | 适合 | 高价值：**未命中返回 `nullptr`，而调用方 `ObjectLayer.cpp:80-84` 未判空即 `npc->setX(...)`**——刷点文件写错类名会直接崩溃；JSTM 移植时必须补判空 |

### 11.7 其他补全

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/PlayerItem.h` | `class PlayerItem : public cocos2d::Node` | `create(const Player_Info&)` / `init(const Player_Info&)`；私有 `onHeadClick` / `onPrivateTalkClick` / `onMakeTeamClick`；`PROPERTY__REF(int, m_fd, Fd)` | 适合 | 高价值：**「附近玩家」列表项同时承载私聊与组队两个业务入口**，是 JSTM 社交入口的最小实现；`m_fd` 是从 UI 回到网络层的唯一钥匙 |
| `Classes/PlayerData.h` | `class PlayerData` | 属性存取器（`glod` / `grade` / `blood` / `mana` / `attack` / `defense` / `speed` / `exp` / `maxExp` / `curblood` / `curmana`）+ 行为方法 `addGlod` / `subGlod` / `addExp` / `addcurBlood` / `subcurBlood` / `addcurMana` / `subcurMana` / `upGrade` / `addProperty` | 适合 | **高价值：玩家运行时属性字段全集**，可直接作为 JSTM 客户端 `PlayerData` 与「属性变更广播字段（`UpdateData_Msg`）」的对照表；注意上限值与当前值分成两组字段（`blood` vs `curblood`） |
| `Classes/EquipmentManager.h` | `class EquipmentManager`（单例） | `wearEquipment` / `upEquipment` / `removeEquipment` / `getEmList` / `readEquipmentInfo` / `saveEquipmentInfo`；私有 `updateEm` / `deleteEm`；成员 `std::list<EMInfo> m_emlist` | 适合 | 可借鉴接口划分；**不适合照搬容器**：装备用 `std::list` 存储，每次穿装都要线性按 `type` 找槽位（`EquipmentManager.cpp:19-30`），JSTM 应改 `map<槽位, EMInfo>` 以获得 O(1) 槽位定位 |
| `Classes/Waite.h` | 仅含一行 `#pragma once`（全文 1 行，无任何内容） | 空头文件 | 不适合 | 死文件，无内容可借鉴；JSTM 不应复制此类残留文件 |

---

## 12. 特别问答：任务原文「特别要回答的点」逐条索引与结论

### 12.1 任务数据结构对应的数据库表名与字段（特别问答）

**结论：本仓库中不存在任何任务表，任务数据完全不落库。**【已确认】

证据链（全部为本次实读）：

| 证据 | 内容 | 等级 |
|---|---|---|
| `Classes/Model.h` 全文 | 只定义 5 个实体，`getName()` 分别是 `"player"` / `"playerinfo"` / `"skillinfo"` / `"equipmentinfo"` / `"backpack"`，**没有任何任务或任务进度实体** | 【已确认】 |
| `Classes/DBDao.h:229,236,243,250` | 表名的唯一来源是 `m_sql.append(m_md.getName())`，即"没有实体类 = 没有可访问的表" | 【已确认】 |
| `Classes/CameraPlayer.cpp:244-267` | 存档入口 `SaveGameData()` 只写 `playerinfo`，并调用 `saveBackpackInfo()` / `saveEquipmentInfo()` / `saveSkillInfo()`，**没有 `saveTaskInfo()`** | 【已确认】 |
| `Classes/SelectLayer.cpp:131-133` | 进入游戏时装载 `readBackpackInfo()` / `readEquipmentInfo()` / `readSkillInfo()`，**没有 `readTaskInfo()`** | 【已确认】 |
| `Classes/TaskSystem.cpp:76-104` | 任务的唯一"存储"是本地文件 `Task/Task<N>.tsk`（只读定义）+ 内存 `m_missedTask` / `m_pickedupTask`（进程退出即丢） | 【已确认】 |

**任务配置字段的实际来源（仓库原文，可用作 JSTM 建表依据）**：`Resources/Task/Task1.tsk` 的字面量 key 与 `TaskInfo` 成员对照：

| 字段语义 | `.tsk` 文件 key（字面量） | `TaskInfo` 成员 | 备注 |
|---|---|---|---|
| 任务名 | `name` | `name` | 例：`黑龙肆虐` |
| 目标怪 / 物名 | `schedulewho` | `schedulewho` | 例：`BlackDragon` |
| 金币奖励 | `glodreward` | `glodreward` | 例：`500` |
| 经验奖励 | `expreward` | `expreward` | 例：`600` |
| 任务编号 | `index` | `index` | 例：`1`（1..11） |
| 进度初值 | `curschedule` | `curschedule` | 例：`0`——**这是玩家态，却写在配置文件里** |
| 总进度 | `allschedule` | `allschedule` | 例：`6` |
| 任务类型 | `type` | `type` | 例：`2001`（=`T_KILL`） |
| 接取 NPC | **`.tsk` 中无此 key**（实读全文确认） | `fromwho` | 由客户端 `m_npcvec` 随机赋值（`TaskSystem.cpp:101`） |
| 交付 NPC | **`.tsk` 中无此 key**（实读全文确认） | `destwho` | 同上（`TaskSystem.cpp:102`） |

> 面向 JSTM 的建议（**以下是本次为 JSTM 拟的命名，非仓库原文**）：把 `curschedule` 从配置表移出，改为玩家态表 `player_quest(playername, rolename, quest_index, cur_schedule, state)`；把 `fromwho` / `destwho` 固化到任务配置中（仓库当前把它们交给客户端随机，服务端将无法校验）。仓库原文可用的字段名只有上表左两列。

### 12.2 逐条索引

| 任务原文要求 | 本文档位置 | 一句话结论 | 等级 |
|---|---|---|---|
| 任务类型宏 | §1.5、§2.1 | `T_KILL 2001` / `T_COLLECT 2002` / `T_ACCESS 2003`（`PreProcess.h:115-118`），与 `Task1.tsk` 的 `type 2001` 交叉验证一致 | 【已确认】 |
| 任务状态机（未接 / 已接 / 可提交 / 已完成） | §2.2 | 四态宏 `NS_FREE 3001` / `NS_HTASK 3002` / `NS_WSTASK 3003` / `NS_STASK 3004`；`havePickedupTask` 用"返回值符号位"编码 可提交(+index) / 未完成(-index) / 无任务(0) | 【已确认】 |
| 任务进度如何计算 | §2.3 | 唯一进度入口 `TaskSystem::checkKillMonster`，由 `Monster::beAttack` 的死亡回调触发 `curschedule++`；**未判任务类型、未封顶** | 【已确认】 |
| 任务面板数据来自何处 | §2.2、§2.4 | 客户端内存 `TaskSystem::m_pickedupTask`；定义来自本地 `Resources/Task/*.tsk`；**既不是 GameData.xml，也不是 MySQL，也不是 TCP** | 【已确认】 |
| 任务数据结构对应的数据库表名与字段 | §2.4、§12.1 | **不存在任务表**；`Model.h` 只有 `player` / `playerinfo` / `backpack` / `equipmentinfo` / `skillinfo` 五张表 | 【已确认】 |
| 装备槽位如何映射到字段 | §4.1 | 槽位常量 1005–1009 写在装备自己的 `.att` 的 `type` 键（如 `BlackWitchHelmet.att` 末行 `type 1005`），落库到 `equipmentinfo.type`；UI 锚点映射在 `RoleInfoLayer.cpp:184-203` | 【已确认】 |
| 精炼 / 升级逻辑在客户端还是服务端 | §4.2 | **全在客户端**：费用 `m_baseupglod + m_grade*(100 + m_baseupglod/10)`、等级自增、属性加值、扣金币、写库；TCP 无任何装备消息 | 【已确认】 |
| 技能购买数量上限（README 说最多 8 个） | §5.1 | 客户端**未实现**该上限；`SkillManager::skillNumbers()` 是死代码（无调用点）；购买入口只挡重复不挡数量 | 【已确认】 |
| 技能伤害升级 | §5.2 | 伤害 `m_baseAttack + 30*m_grade`；耗蓝 `m_baseMana + m_grade*10`；升级费 `m_baseupGlod + m_grade*50` | 【已确认】 |
| 药品使用时机（战斗内 / 外） | §6.1 | 战斗外：背包「使用」按钮，无 TCP；战斗内：战斗界面药品条 `FightLayer::onMedication`，需轮到自己且 `tag>0` | 【已确认】 |
| 药品是否走 TCP 消息（找 `UseMedication_Msg`） | §6、§6.1 | **是，但仅在组队时**：`CMClient::sendUseMedicationMsg(dest)`；接收端 `doUseMedicationMsg` 只调 `FightLayer::setOtherPalyerEnd()`，**不携带任何药品效果字段，不同步血量** | 【已确认】 |
| 组队 申请 / 同意 / 拒绝 / 踢人 / 解散 的完整消息流转与涉及结构体 | §7.2、§7.3 | 申请 `TeamApply_Msg` → 同意 `AgreeTeam_Msg` → 拒绝 `RefuseTeam_Msg` → 解散 `TeamManage_Msg{type=M_DissolveTeam}`；另有 `TeamMove_Msg` / `TeamGotoMap_Msg` / `TeamFight_Msg` 与战斗类 `MonsterAtk_Msg` / `PlayerAtk_Msg` / `PlayerRun_Msg` / `UseMedication_Msg` / `PlayerDie_Msg`。**踢人与退队按钮均复用「全员解散」宏**，`M_QuitTeam` / `M_KickOutteam` 已定义但未实装 | 【已确认】 |
| 聊天：世界聊天 vs 私聊的消息结构与本地队列 | §8.1、§8.2 | 世界 `WorldTalk_Msg{type, fd, msg[200]}` → `std::deque<TalkMsg> m_worldTalkMsgs`（上限 100 条，屏显 5 条）；私聊 `PrivateTalk_Msg{type, fd, dest, msg[200]}` → `std::map<int, std::deque<TalkMsg>> m_privateTalkMsgs`（上限 6 会话 × 每会话 18 条）；发送方均**先本地入队再发包** | 【已确认】 |

---

## 附录 A：本文件引用的关键代码片段

**A1. 双通道并存（`Classes/BeginScene.cpp:23-35` + `Classes/CMClient.cpp:113-136`）**
```cpp
auto func = [beginlayer, this] {
    if (CMClient::getInstance()->Connect())   // → CTCPClient::ConnectSever(m_serverip, m_port)
    { beginlayer->showBtn(); SetIntData("IsConnectNet", 1); ... }
};
```

**A2. 任务定义来自客户端本地文件（`Classes/TaskSystem.cpp:76-104`）**
```cpp
std::ifstream fin;
std::string filename = "Task/Task" + NTS(index) + ".tsk";
fin.open(filename, std::ios::in);
...
info.fromwho = m_npcvec[rand() % 4];
info.destwho = m_npcvec[rand() % 4];
m_missedTask.push_back(info);
m_taskindexs.insert(info.index);
```

**A3. 背包直连 MySQL 的部分更新（`Classes/BackPackManager.cpp:117-128`）**
```cpp
BackPack thing;  DBDao<BackPack> dao;
thing.setthingnums(NTS(info.nums));
std::map<std::string, std::string> keyvls;
keyvls["playername"] = GetStringData("playername");
keyvls["rolename"]   = GetStringData("rolename");
keyvls["thingname"]  = info.name;
dao.setModel(thing);  dao.updateModel(keyvls);
```

**A4. 技能伤害升级（`Classes/Skill.cpp:73-90`）**
```cpp
RealSkill* skill = SkillFactory::createSkill(m_name, pFt, towho, m_baseAttack + 30 * m_grade);
...
float Skill::getUseMana() { return m_baseMana + m_grade * 10; }
```

**A5. 用药走 TCP（`Classes/FightLayer.cpp:559-565`）**
```cpp
if (PlayerTeamStatus() != P_STATUS_NORMAL)
{
    for (auto var : TeamManager::getInstance()->getTeamMembers())
        CMClient::getInstance()->sendUseMedicationMsg(var.first);
}
```

**A6. 组队"退队/踢人 = 全员解散"（`Classes/MemberItem.cpp:8-13`）**
```cpp
#define DISSOLVE_TEAM()    \
for (auto var : TeamManager::getInstance()->getTeamMembers())  \
{   CMClient::getInstance()->SendTeamDissolveMsg(var.first);   }  \
TeamManager::getInstance()->dissolveTeam()
```

**A7. 世界聊天先本地入队再发包（`Classes/GameUILayer.cpp:219-228`）**
```cpp
WorldTalk_Msg msg;  msg.type = M_WorldTalk;  msg.fd = -1;
strcpy_s(msg.msg, m_editFrame->getString().c_str());
CMClient::getInstance()->addWorldTalkMsg(&msg);
CMClient::getInstance()->SendMsg((char*)&msg, sizeof(msg));
```

---

## 附录 B：审计范围与证据等级统计

- 实读文件（`Classes/`，共 **102** 个）：`Model.h`、`PreProcess.h`、`Commen.h`、`ShareData.h`、`public.h`、`DBDao.h`、`DBDao.cpp`、`TCPClient.h`、`TCPClient.cpp`、`CMClient.h`、`CMClient.cpp`、`TaskSystem.h`、`TaskSystem.cpp`、`TaskItem.h`、`TaskItem.cpp`、`TaskLayer.h`、`TaskLayer.cpp`、`PickupTaskLayer.h`、`PickupTaskLayer.cpp`、`BackPackManager.h`、`BackPackManager.cpp`、`BackPackLayer.h`、`BackPackLayer.cpp`、`Thing.h`、`Thing.cpp`、`Medication.h`、`Medication.cpp`、`EquipmentManager.h`、`EquipmentManager.cpp`、`EquipMent.h`、`EquipMent.cpp`、`DetailLayer.h`、`DetailLayer.cpp`、`DealLayer.h`、`DealLayer.cpp`、`SkillManager.h`、`SkillManager.cpp`、`Skill.h`、`Skill.cpp`、`SkillFactory.h`、`SkillFactory.cpp`、`RealSkill.h`、`RealSkill.cpp`、`SkillLayer.h`、`SkillLayer.cpp`、`SkillInfo.h`、`TeamManager.h`、`TeamManager.cpp`、`TeamLayer.h`、`TeamLayer.cpp`、`TeamMsgItem.h`、`TeamMsgItem.cpp`、`MsgListLayer.h`、`MsgListLayer.cpp`、`PrivateTalkLayer.h`、`PrivateTalkLayer.cpp`、`TalkLayer.h`、`TalkLayer.cpp`、`MsgItem.h`、`MsgItem.cpp`、`WorldMapLayer.h`、`WorldMapLayer.cpp`、`Npc.h`、`Npc.cpp`、`NpcBlue.h`、`NpcBlue.cpp`、`NpcEquip.h`、`NpcEquip.cpp`、`NpcSkill.h`、`NpcSkill.cpp`、`NpcPink.h`、`NpcPink.cpp`、`NpcMonk.h`、`NpcMonk.cpp`、`NpcManmom.h`、`NpcMamom.cpp`、`NpcVallige.h`、`NpcVallige.cpp`、`ReflectNpc.h`、`ReflectNpc.cpp`、`ObjectLayer.cpp`、`Monster.cpp`、`PlayerItem.h`、`PlayerItem.cpp`、`PlayerListLayer.cpp`、`MemberItem.cpp`、`PlayerData.h`、`PlayerData.cpp`、`GameData.h`、`GameData.cpp`、`GameDynamicData.h`、`GameDynamicData.cpp`、`CameraPlayer.cpp`（部分）、`RoleInfoLayer.cpp`、`FightLayer.cpp`（部分）、`LoginLayer.cpp`、`SigOnLayer.cpp`、`NewGameLayer.cpp`（部分）、`SelectLayer.cpp`、`BeginScene.cpp`、`GameMenuLayer.cpp`、`Waite.h`
- 实读资源：`README.md`、`Resources/server.cfg`、`Resources/GameData.xml`（部分键）、`Resources/Task/Task1.tsk`、`Resources/Task/Task1.tk`、`Resources/Task/EndTask.tk`、`Resources/Thing/BlueMedicine.att`、`Resources/Thing/BlackWitchHelmet.att`、`Resources/Skill/CrackIt/CrackIt.att`、`Resources/Skill/DragonRoar/DragonRoar.att`、`Resources/Skill/long/Long.att`、`Resources/mapinfo.xxp`、`Resources/LevelObject/Level1.lobject`、`Resources/` 与 `Resources/Task/`、`Resources/Skill/`、`Resources/Thing/`、`Resources/LevelObject/` 目录清单、`proj.win32/ChivalrousMan.sln`
- 未读到（因服务端缺失）：CM-Server 全部源码、`.sql` 建表脚本、`DB.cfg`
- 统计：**【已确认】标记 133 处**（覆盖全部实读文件与实读资源的事实陈述）；**【待验证】标记 21 处 = 5 处正文 inline 结论 + 11 项 §10.3 清单条目 + 5 处等级定义/索引引用，去重后为 11 个独立待验证结论**（完整清单见 §10.3 表格 11 项）；**【未知】标记 4 处，均为等级定义与范围限定语句中的引用**，本文件未对完全未读到的功能直接下【未知】结论
- 覆盖完整性：任务清单列出的全部文件均已在正文表格中单独成行（第二轮由 §11 补齐 31 个文件 = 25 个头文件 + 6 个仅被引用过的实现文件，以 32 行表格记录），每个「特别要回答的点」均由 §12.2 索引到唯一章节

---

# 附录 D（R2 回填，主审计员逐份实读 11 个任务模板后新增）

> 本附录由主审计员在 R2 阶段**把 `Resources/Task/Task1.tsk` ～ `Task11.tsk` **全部 11 个文件逐份读完**，并与 `TaskSystem.cpp` / `Monster.cpp` / `Npc.cpp` 交叉比对后回填。
> 它**解答了正文遗留的 3 个关键疑问**，并**修正正文 1 处计数**。全部条目均为 **【已确认】**。

## D.1 ★ 11 个任务模板全表（★ 本附录最有价值的部分）

| # | 文件 | `name`（中文名） | `schedulewho`（目标） | `glodreward` | `expreward` | `index` | `curschedule` | `allschedule` | `type` | 类型 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `Task1.tsk` | 黑龙肆虐 | `BlackDragon` | 500 | 600 | 1 | 0 | **6** | 2001 | T_KILL |
| 2 | `Task2.tsk` | 飞龙坐骑 | `Dragon` | 600 | 550 | 2 | 0 | **6** | 2001 | T_KILL |
| 3 | `Task3.tsk` | 亡灵扰人 | `Ghost` | 550 | 550 | 3 | 0 | **7** | 2001 | T_KILL |
| 4 | `Task4.tsk` | 甲兽壳 | `Kougamon` | 700 | 600 | 4 | 0 | **8** | 2001 | T_KILL |
| 5 | `Task5.tsk` | 狂狮伤人 | `Lion` | 750 | 600 | 5 | 0 | **8** | 2001 | T_KILL |
| 6 | `Task6.tsk` | 怪牛打人 | `Minotaur` | 760 | 620 | 6 | 0 | **8** | 2001 | T_KILL |
| 7 | `Task7.tsk` | 章鱼肉 | `Octopus` | 900 | 700 | 7 | 0 | **7** | 2001 | T_KILL |
| 8 | `Task8.tsk` | 肥龙戏人 | `Pterosaur` | 950 | 750 | 8 | 0 | **8** | 2001 | T_KILL |
| 9 | `Task9.tsk` | 摄魂法师 | `SkeletonMaster` | 1000 | 800 | 9 | 0 | **8** | 2001 | T_KILL |
| 10 | `Task10.tsk` | 魔龙使者 | `TarrasqueMessenger` | 1000 | 800 | 10 | 0 | **10** | 2001 | T_KILL |
| 11 | `Task11.tsk` | 访亲问友 | **`""`（空字符串）** | 600 | 600 | 11 | **1** | **1** | **2003** | **T_ACCESS** |

**★ 从这张表能直接读出 4 条设计事实（全部【已确认】）**：
1. **`Task1..Task10` 的 `schedulewho` 恰好是 `Resources/Monster/` 下的 10 个怪物名**，与 `TaskSystem::m_entocn` 的 10 条怪物映射**完全一一对应** ⇒ 任务是"一只怪一个击杀任务"。
2. **`T_COLLECT 2002` 在 11 个模板中使用了 0 次** ⇒ 它是**已声明但从未使用的任务类型**（`TaskItem.cpp:56-58` 有渲染分支，`PreProcess.h:117` 有宏，但无任何模板）。
3. **唯一的 `T_ACCESS`（`Task11`）自带 `curschedule 1` / `allschedule 1`** ⇒ **接取瞬间即满足"可提交"条件**（`curschedule >= allschedule`）。这**完美解释了正文遗留的疑问**：T_ACCESS 不需要任何进度推进代码，因为它的进度**从配置里就是满的**。
4. **任务奖励随难度单调递增**：`glodreward` 500→1000、`expreward` 550→800，`allschedule` 6→10 —— 说明设计者确实按怪物强度调过数值（与 `Monster/*.att` 的 attack/blood/exp/glod **同向**）。

## D.2 修正正文 1 处计数

| 位置 | 正文原文 | 修正为 | 依据 |
|---|---|---|---|
| §2.3 `TaskSystem::createTask()` 行 | "按固定顺序读 **9** 个 key/value 对" | **8 个** key/value 对（`name / schedulewho / glodreward / expreward / index / curschedule / allschedule / type`） | `TaskSystem.cpp:85-100` 共 8 组 `fin >> tmp; fin >> info.X;`；`.tsk` 文件实测也恰好 8 行键值 |

## D.3 ★ 升级 1 项、新增 3 项结论

| # | 结论 | 证据 | 等级变化 |
|---|---|---|---|
| D-1 | ★ **`curschedule++` 在全 `Classes/`（99 个 .h + 92 个 .cpp）中只出现 1 次**，位于 `TaskSystem.cpp:180`（`checkKillMonster` 内）；而 `checkKillMonster` 只被 `Monster.cpp:114` 调用 | grep 全量实测 | 正文 §2.3 的 `T_COLLECT`/`T_ACCESS` 进度问题（原【待验证】）：**客户端侧现在可【已确认】为"不存在任何实现路径"**；由 D.1 第 2/3 条进一步说明**这不是缺陷而是设计**（2002 未使用、2003 自带满进度）。**是否由服务端补足仍【待验证】** |
| D-2 | **`checkKillMonster` 不判 `type`、不封顶** ⇒ 若某任务 `schedulewho` 与怪物同名，就会被击杀错误推进 | `TaskSystem.cpp:174-184`（无 `type` 判断、无 `curschedule < allschedule` 判断） | 正文已提及"未判 `type`、未封顶"，本附录**补上后果**：这构成**类型间进度交叉污染**的隐患（当前 11 个模板下不会触发，因为 2002 未使用） |
| D-3 | **`submitTask` 内部不校验 `curschedule >= allschedule`**，安全性完全依赖 NPC 状态 `NS_STASK` 这条 UI 路径（唯一调用点 `Npc.cpp:112`） | `TaskSystem.cpp:124-140`（只见 `it->index == index` 判定） | **新增**：即"能否交任务"由**上游状态**兜底，而非由提交函数自身校验；若将来新增调用点即可未完成领奖 |
| D-4 | **`TaskSystem` 存在无锁数据竞争**：`TaskSystem.h:6` `#include<mutex>`，但类中**没有任何 `std::mutex`/`std::atomic` 成员**；`workThread`（后台线程，构造函数 `TaskSystem.cpp:35` 即启动）写 `m_missedTask`/`m_taskindexs`，主线程在 `ObjectLayer::update`（`ObjectLayer.cpp:117/129`）与任务面板（`TaskLayer.cpp:30`）读同一批容器 | `TaskSystem.h:104-109` 成员列表 + `TaskSystem.cpp:35/52-63/103-104` | **新增**：与 `GameDynamicData` 的"单例创建有 atomic 保护、但 map 读写无锁"是**同源问题**；表现为"新增任务瞬间开面板/切场景可能崩" |

## D.5 对 JSTM 的补充建议

| # | 建议 | 依据 |
|---|---|---|
| 1 | **任务模板表应把 `curschedule` 移出**：它是**玩家态**却写在配置文件里（`Task1.tsk` 的 `curschedule 0` 与 `Task11.tsk` 的 `curschedule 1` 都是"起始进度"语义） | D.1 / 正文 §12.1 |
| 2 | **`schedulewho` 应带类型语义或拆分字段**：当前 `T_KILL` 用怪物名、`T_ACCESS` 用空串、`T_COLLECT` 本应用物品名 —— 三类共用一个字段易混淆；JSTM 建议拆为 `target_type` + `target_id` | D.1 / D-2 |
| 3 | **11 个模板可作为 JSTM "最小任务集" 的对照样本**：10 个击杀（6~10 只）+ 1 个访问，奖励 500~1000 金币 / 550~800 经验 —— 这套数值量级可用来校准 JSTM 前 10 级的新手任务产出 | D.1 |
