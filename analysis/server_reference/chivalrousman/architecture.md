# ChivalrousMan（侠客行）架构审计 —— 含「是否真无服务端」实证结论

> **审计对象**：`C:\Users\xu\Desktop\DSH\cankao\ChivalrousMan-master.zip`（51.2 MB，**1539 条目 / 解压后 1411 个文件**）
> **实测方法**：Python `zipfile.namelist()` 列全部条目 → 全量解压 → GBK→UTF-8 转换 → 逐文件阅读。
> **未改动 `cankao/` 下任何文件**（解压副本读于系统 TEMP）。
> **⚠ 无 LICENSE**（全仓库无 `LICENSE`/`COPYING`/`LICENCE` 文件）⇒ 无许可依据，**只可借鉴设计，不要直接复制代码**。详见 `reuse_candidates.md`。
>
> 标注：【已确认】= 本次亲自读到该行代码/该条文件；【待验证】= 由命名/资源推断；【未知】= 未读到。

---

## 一、★ 结论先行：ChivalrousMan 是否真的没有服务端？

> ## ✅ **【已确认】本仓库内确实没有服务端代码。**
> 它的服务端位于**另一个独立仓库** `https://gitee.com/lsylovews/CM-Server`（作者在 `README.md` 中明示），
> **不在本 ZIP 内，本次未读到其任何一行代码**。
>
> **但有一个必须补充的关键修正**：
> ## ⚠ **【已确认】本仓库的"客户端"承担了本应属于服务端的持久化职责** ——
> 客户的登录、注册、建号、选角、背包、装备、技能、玩家属性存档，**全部由客户端通过 `libmysql` 直连 MySQL 完成**（`Classes/DBDao.h`）。
> 因此它对本项目的价值**不止于"客户端 UI 流程证据"**，还**完整暴露了一套 MMORPG 业务表结构与持久化流程**。

---

## 二、「无服务端」的 11 条实证（逐条可复核）

| # | 检验项 | 实测结果 | 判定 |
|---|---|---|---|
| 1 | 顶层目录枚举 | `Classes/`、`cocosstudio/`、`include/`、`lib/`、`proj.android/`、`proj.ios_mac/`、`proj.win32/`、`Resources/` —— **没有 `server/` / `Server/` / `src/server`** | 【已确认】 |
| 2 | 顶层文件枚举 | `.cocos-project.json`、`ChivalrousMan.ccs`、`ChivalrousMan.cfg`、`ChivalrousMan.udf`、`config.json`、`README.md`（**6 个，无一个服务端入口**） | 【已确认】 |
| 3 | **文件名**含 `serv`（不区分大小写）的全部 11 个命中 | ①`include/mysql_com_server.h`、`include/mysql/service_my_snprintf.h`、`include/mysql/service_mysql_alloc.h` → **MySQL 客户端 SDK 自带头文件**<br>②`proj.android/{src,gen,bin/aidl,bin/classes}/com/enhance/gameservice/IGameTuningService.{aidl,java,class}` → **触控 CocosPlay 的"游戏加速"Android AIDL 服务（打包/调优用）**，与游戏逻辑无关<br>③`Resources/server.cfg` → **客户端读的服务器地址配置** | **全部与服务端无关**【已确认】 |
| 4 | **目录名**含 `serv` 的全部 4 个 | 全在 `proj.android/{bin/aidl,bin/classes,gen,src}/com/enhance/gameservice`（同 #3②） | 【已确认】 |
| 5 | 全仓库唯一的 `.sln` | `proj.win32/ChivalrousMan.sln` → **`Project(...)= "ChivalrousMan", "ChivalrousMan.vcxproj"` 仅 1 个工程** | 【已确认】 |
| 6 | `ChivalrousMan.vcxproj` 的 `ClCompile` 清单 | **92 个 `..\Classes\*.cpp` + `main.cpp`**，共计 93 个编译单元；**没有任何"服务端"入口**（无 `Server.cpp`/`main_server.cpp`） | 【已确认】 |
| 7 | `ClInclude` 清单 | 含 `DBDao.h`、`Model.h`、`ShareData.h`、`TCPClient.h`、`CMClient.h` …… 全为客户端头；**`DBDao.cpp` 不在编译列表**（见 §6.3） | 【已确认】 |
| 8 | **服务端 socket 特征**（`listen(` / `accept(` / `bind(` / `SOCKADDR_IN`）在 `Classes/*.{h,cpp}` 中 | **0 命中** | 【已确认】 |
| 9 | `Classes/` 内唯一的 socket 角色 | `Net::CTCPClient`（`TCPClient.{h,cpp}`）：`WSAStartup` → `socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)` → **`connect(...)`** → 起 `m_recvThread` 跑 `DoServerMsg()` 循环 `recv` —— **纯客户端** | 【已确认】 |
| 10 | `Resources/server.cfg` 内容 | `//服务器配置文件`<br>`serverIp 192.168.229.128`<br>`port 6036` —— 客户端读该文件去连**外部**服务器 | 【已确认】 |
| 11 | **归档/其它语言服务端** | 全仓库**无 `.sql`、无 Dockerfile、无 `package.json`、无 `.py` 服务端**、无 `.zip/.rar/.7z` 归档 | 【已确认】 |

### 2.1 作者自述（最强证据）【已确认】

`README.md` 实测原文（第 9 行，节选）：

> 「游戏使用的数据库是 mysql 搭建在个人的阿里云服务器上，同时**游戏的服务器也搭建在个人的阿里云服务器上
> 服务器项目源码在 _https://gitee.com/lsylovews/CM-Server_** 上。附件中包含项目的 exe 可执行文件……
> 只要个人的阿里云服务器还没过期，游戏就可以运行，如果服务器过期那就需要**在自己的电脑上搭建服务器和安装 mysql**，
> 同时**执行附件中的 sql 文件新建数据库**，服务器可以自己安装一个 Ubuntu 虚拟机然后自己编译运行服务器代码，
> 最后就是修改可执行文件同目录下的 **server.cfg 修改服务器配置**和修改同目录下的 **DB.cfg 修改数据库配置**。」

**⇒ 三条独立事实**：
1. **服务端源码在 `gitee.com/lsylovews/CM-Server`，不在本仓库**【已确认】；
2. 服务端是 **Linux（Ubuntu）编译运行的 C++**，而本仓库的 C++ 是 **Win32/iOS/Android 客户端** ⇒ 两者是不同工程【已确认】；
3. README 提到交付物应含 **`.sql` 建库文件与 `DB.cfg`**，但**本仓库中都不存在**（`DB.cfg` 无、`*.sql` 无）⇒ 本仓库是**不完整的客户端切片**【已确认】。

### 2.2 文件构成实证

| 类别 | 数量 | 位置 | 性质 |
|---|---|---|---|
| `.cpp` | **95**（= `Classes/` 92 + `proj.{android,ios_mac,win32}/main.cpp` 3） | 客户端 | 【已确认】 |
| `.h` | **167**（= `Classes/` 99 + `include/` 68 MySQL SDK 头） | 客户端 + 第三方 | 【已确认】 |
| `.java` | **31** | `proj.android/src`(28) + `proj.android/gen`(3) | **全部是 cocos2d-x / CocosPlay 框架文件**，无一行游戏逻辑【已确认】 |
| `.class` | **128** | `proj.android/bin/classes/` | Java 编译产物（cocos2d-x 118 + CocosPlay 4 + R/BuildConfig 等）【已确认】 |
| `.png/.BMP/.gif/.jpg` | 748 | `Resources/`、`proj.android/res` | 美术资源 |
| 客户端自研 C++ | **92 个 .cpp + 99 个 .h（`Classes/`）** | 唯一自研代码 | 【已确认】 |

**⇒ 结论**：1539 条目中，**自研代码只有 `Classes/` 的 191 个文件**；其余全是 cocos2d-x 框架、Android 工程、MySQL 客户端 SDK、美术资源。
**没有任何一个文件属于游戏服务端。**

---

## 三、★ 真实架构：**双通道客户端**（这是本项目的核心特征）

```
                       ┌───────────────────────────────────────────────────────┐
                       │              ChivalrousMan 客户端（本仓库）            │
                       │                                                       │
  实时游戏交互 ◀───────┤  CMClient（协议分发，22 种 M_Type）                    │
  （移动/战斗/组队     │        │                                              │
   /聊天/位置校验）     │        └── Net::CTCPClient（原始 TCP，自定义二进制）    │
                       │                     │                                 │
                       │                     └────► Resources/server.cfg        │
                       │                              serverIp 192.168.229.128  │
                       │                              port     6036             │
                       │                                                       │
  持久化/账号/物品 ◀───┤  DBDao<Model> 模板（#include <mysql.h>，libmysql 直连） │
  （登录/注册/建号/    │        │                                              │
   选角/背包/装备/技能）│        └──► 硬编码 host 47.93.235.6 / user game /     │
                       │                  passwd 3252918599lsy / db chivalrousman│
                       └───────────────────────────────────────────────────────┘
                                        │                            │
                                        ▼                            ▼
                             外部游戏服务端                外部 MySQL
                        (gitee.com/lsylovews/CM-Server)   (阿里云，本仓库无 .sql)
                        ★ 不在本仓库，未读到
```

### 3.1 通道 A —— 实时游戏（TCP + 自定义二进制）

| 项 | 实测 | 标注 |
|---|---|---|
| 传输 | 原始 BSD socket，`AF_INET` / `SOCK_STREAM` / `IPPROTO_TCP`，`ws2_32.lib` | 【已确认】`TCPClient.cpp` 30-52 |
| 服务端地址 | 运行期从 `Resources/server.cfg` 读（`CMClient::readConfConnectServer()`） | 【已确认】 |
| 连接时机 | `BeginScene::init()` 里 `if (CMClient::getInstance()->Connect())`，在**独立 `std::thread`** 中执行 | 【已确认】 |
| 收包线程 | `ConnectSever` 成功后 `m_recvThread = new thread{&CTCPClient::DoServerMsg, this}` | 【已确认】 |
| 协议常量 | `Classes/ShareData.h`：`enum M_Type { M_EntryGame, M_InitData, M_WorldTalk, M_PrivateTalk, M_InitPos, M_PlayerLeave, M_MoveTo, M_VerifyPos, M_UpdateData, M_TeamApply, M_RefuseTeam, M_AgreeTeam, M_TeamMove, M_TeamGotoMap, M_DissolveTeam, M_QuitTeam, M_KickOutteam, M_TeamFight, M_MonsterAtk, M_PlayerAtk, M_PlayerRun, M_UseMedication, M_PlayerDie }` —— **共 23 个枚举值** | 【已确认】 |
| 协议结构体 | 22 个 POD：`Player_Info`、`InitData_Msg`、`WorldTalk_Msg`、`PrivateTalk_Msg`、`InitPos_Msg`、`PlayerLeave_Msg`、`MoveTo_Msg`、`VerifyPos_Msg`、`UpdateData_Msg`、`TeamApply_Msg`、`RefuseTeam_Msg`、`AgreeTeam_Msg`、`TeamMove_Msg`、`TeamGotoMap_Msg`、`TeamManage_Msg`、`TeamFight_Msg`、`MonsterAtk_Msg`、`PlayerAtk_Msg`、`PlayerRun_Msg`、`UseMedication_Msg`、`PlayerDie_Msg` | 【已确认】 |
| 打包方式 | **直接 `SendMsg((char*)&msg, sizeof(msg))` —— 结构体内存直发（无序列化、无对齐处理、无长度前缀、无字节序转换）** | 【已确认】 |
| 解包方式 | `M_Type type = *((M_Type*)buff);` + `(InitData_Msg*)buff` 直接强制转换 | 【已确认】 |
| 断线约定 | `public.h`：`#define CLOSE_MESSAGE "~#@**close**@#~"`；`CMClient::OnRecv` 首行 `if (!strcmp(buff, CLOSE_MESSAGE))` → `MessageBox("服务器异常关闭")` + `Director::end()` | 【已确认】 |
| 分帧 | **无** —— `recv` 到多少就是一条消息（`DoServerMsg` 里一次 `recv` 直接回调 `OnRecv(buff)`） | 【已确认】 |
| 心跳 | **无** | 【已确认】 |
| 加密 | **无** | 【已确认】 |

### 3.2 通道 B —— 持久化（libmysql 直连 MySQL）

| 项 | 实测 | 标注 |
|---|---|---|
| 头文件 | `Classes/DBDao.h`：`#include<WinSock2.h>` / `#include<mysql.h>` / `#include<mysqld_error.h>` + `#pragma comment(lib,"libmysql.lib")` | 【已确认】 |
| 库文件 | `lib/libmysql.dll`（4.63 MB）、`lib/libmysql.lib`、`lib/vs12/mysqlclient.lib`、`lib/vs14/mysqlclient.lib`；`Resources/libmysql.dll`（运行时拷贝） | 【已确认】 |
| 头文件 | `include/`（68 个 MySQL 客户端 SDK 头，含 `mysql.h`、`mysql_com.h`、`mysqld_error.h`、`psi/*`） | 【已确认】 |
| 连接参数 | **硬编码在 `DBDao<Model>::DBDao()` 默认构造**：`m_host("47.93.235.6")`、`m_passwd("3252918599lsy")`、`m_username("game")`、`m_dbname("chivalrousman")`、`m_port=3306` | 【已确认】`DBDao.h` 105-113 |
| 连接方式 | `mysql_init(0)` → `mysql_real_connect(...)` —— **明文 TCP 直连公网数据库** | 【已确认】`DBDao.h` 214-219 |
| 使用点（7 个文件） | `LoginLayer.cpp`、`SigOnLayer.cpp`、`NewGameLayer.cpp`、`SelectLayer.cpp`、`CameraPlayer.cpp`、`BackPackManager.cpp`、`EquipmentManager.cpp`、`SkillManager.cpp` | 【已确认】 |
| SQL 生成 | `generateSql(QUERY/INSERT/DELETE/UPDATE)` + `generateWhere/generateValues/generateUpdate`，**全部字符串拼接**（`+= "'" + value + "'"`），无参数化 | 【已确认】 |
| 事务 | **无** | 【已确认】 |
| 实体映射 | `Model.h`：5 个 Model 类，每个实现 `operator[](int)`（序号→字段）、`getAttributeName(int)`、`getName()`（表名）、`getAttributeNums()` | 【已确认】 |

**★ 这条通道是本项目最有价值的资产**：它把**一套完整的 MMORPG 业务表结构**（`player` / `playerinfo` / `skillinfo` / `equipmentinfo` / `backpack`）
以可读的 C++ 代码形式暴露了出来 —— 详见 `database.md`。

### 3.3 两条通道的职责边界（逐业务实测）

| 业务 | 走通道 A（TCP 服务端） | 走通道 B（MySQL 直连） | 证据 | 标注 |
|---|---|---|---|---|
| 注册账号 | ❌ | ✅ `insert into player(playername,playerpsw,nums)` | `SigOnLayer::SigonEvent` | 【已确认】 |
| 登录账号 | ❌ | ✅ `select * from player where playername=? and playerpsw=?` | `LoginLayer::LoginEvent` | 【已确认】 |
| 建号 | ❌ | ✅ `insert into playerinfo(...)` + `update player set nums` | `NewGameLayer::onConfirmCallBack` / `addRoleNums` | 【已确认】 |
| 选角 / 读角色列表 | ❌ | ✅ `select * from playerinfo where playername=?` | `SelectLayer::initPlayerView` | 【已确认】 |
| 背包 | ❌ | ✅ `DBDao<BackPack>`（`readBackpackInfo`/`saveBackpackInfo`） | `BackPackManager.cpp` 84/105/120/133 | 【已确认】 |
| 装备 | ❌ | ✅ `DBDao<EquipmentInfo>` | `EquipmentManager.cpp` 72/92/106/119 | 【已确认】 |
| 技能 | ❌ | ✅ `DBDao<SkillInfo>` | `SkillManager.cpp` 63/80/96 | 【已确认】 |
| **玩家属性存档** | ❌ | ✅ `DBDao<PlayerInfo>::updateModel(map)` | `CameraPlayer::SaveGameData` | 【已确认】 |
| 进场景初始化 | ✅ `SendInitPlayerData()`（`M_InitData` 带 playername/rolename/playertype/curmap/attack/blood/defense/mana/grade） | ❌ | `CMClient.cpp` 138-154 | 【已确认】 |
| 进场景位置 | ✅ `SendInitPos()`（`M_InitPos` 带 x/y/curmap） | ❌ | `CMClient.cpp` 156-165 | 【已确认】 |
| 移动 | ✅ `SendMoveToMsg(pos, less)`（`M_MoveTo`） | ❌ | `CameraPlayer::moveTo` | 【已确认】 |
| 位置校验 | ✅ `VerifyPlayerPos()`（`M_VerifyPos`）/ 收 `M_VerifyPos` 校准 | ❌ | `AudioSystem.cpp:47` / `CMClient::doPlayerPosVerifyMsg` | 【已确认】 |
| 属性变化同步 | ✅ `updatePlayerData()`（`M_UpdateData`） | ❌ | `PlayerData.cpp:74` | 【已确认】 |
| 世界聊天 / 私聊 | ✅ `M_WorldTalk` / `M_PrivateTalk` | ❌ | `CMClient::addWorldTalkMsg`/`addPrivateTalkMsg`；`GameUILayer.cpp:226`、`PrivateTalkLayer.cpp:101` | 【已确认】 |
| 组队（申请/同意/拒绝/移动/切图/解散/踢人） | ✅ `M_TeamApply`/`M_AgreeTeam`/`M_RefuseTeam`/`M_TeamMove`/`M_TeamGotoMap`/`M_DissolveTeam`/`M_QuitTeam`/`M_KickOutteam` | ❌ | `CMClient` 各 `doTeam*` / `TeamMsgItem.cpp:71,95`、`MemberItem.cpp:11` | 【已确认】 |
| 战斗（玩家攻击/怪物攻击/逃跑/用药/死亡） | ✅ `M_PlayerAtk`/`M_MonsterAtk`/`M_PlayerRun`/`M_UseMedication`/`M_PlayerDie`/`M_TeamFight` | ❌ | `CMClient::send*/do*` | 【已确认】 |
| 离线 | ✅ `SendPlayerLeaveMsg()`（`M_PlayerLeave`） | ❌ | `GameMenuLayer.cpp:13` | 【已确认】 |
| **任务** | — **未见 TCP 消息** | `Resources/Task/*.tsk/.tk` 本地文件 | 见 `task.md` | 【待验证】 |

**⇒ 关键判断**：**通道 B 承担"账号 + 全部物品/属性持久化"；通道 A 承担"地图内的实时交互"。**
这是一种**极不安全、极不寻常**的设计（客户端直连公网数据库、数据库凭据硬编码在可执行文件里、客户端可任意改自己的金币/等级），
但**对本项目而言它是一个巨大的信息红利**：MMORPG 的业务数据结构因此在客户端侧完全可读。

---

## 四、分层实况（这是它与 Mahatma 最大的差别）

| 层 | 文件 | 职责 | 是否适合 JSTM | 原因 |
|---|---|---|---|---|
| **传输层** | `Classes/TCPClient.{h,cpp}` | 只做 `connect` / `send` / `recv` / 回调 | **适合（借鉴分层）** | ★ 职责单一：`CTCPClient` 完全不知道业务；`OnRecv` 虚函数留给上层。**对比 Mahatma 把网络塞在 Form 里，这是明显更清晰的边界** |
| **协议定义层** | `Classes/ShareData.h` | 23 个 `M_Type` 枚举 + 22 个 `*_Msg` POD + `Player_Info` | **★ 适合（高价值）** | 协议**集中在一个头文件**，字段与语义有注释；JSTM 可对照检查"协议常量是否集中" |
| **协议分发层** | `Classes/CMClient.{h,cpp}` | 继承 `CTCPClient`；`OnRecv` 里 `switch(type)` 分发到 22 个 `doXxxMsg`；提供 15+ 个 `SendXxxMsg` | **★ 适合（高价值）** | "收：switch 分发；发：每类消息一个函数" 是清晰形状。**缺点**：`CMClient` 同时持有业务缓存（`m_playerlist` / `m_worldTalkMsgs` / `m_privateTalkMsgs` / `m_applyTeamList` / `m_gotoMapMsgs`），职责偏重 |
| **数据实体层** | `Classes/Model.h` | 5 个 Model（`GamePlayer`/`PlayerInfo`/`SkillInfo`/`EquipmentInfo`/`BackPack`），每个自带表名 + 字段名 + 序号映射 | **★ 适合（高价值）** | 见 `database.md`；这是 JSTM"表结构设计"的**唯一正面参照** |
| **持久层** | `Classes/DBDao.h` | `template<Model> DBDao`：`queryModel/insertModel/deleteModel/updateModel(×2)` + `generateSql/generateWhere/generateValues/generateUpdate` | **适合（思想）** | ★ **泛型 DAO + 实体自描述表结构** 是干净的设计；但**无参数化、无事务、无连接池**（每次 `new DBDao` 就 `mysql_real_connect`） |
| **配置/全局态** | `Classes/GameDynamicData.{h,cpp}` | 单例 map，`Set/Get{Int,Float,String}Data` 宏；一个 `m_curgs` 持有当前 `GameScene*` | **待验证** | 用**无类型 key-value 全局字典**传递游戏状态（如 `CurMap`/`destx`/`IsHaveGameScene`）—— 灵活但不可查错；JSTM 若用 Lua 的 global table 需注意同类风险 |
| **业务管理层** | `TaskSystem`、`SkillManager`、`EquipmentManager`、`BackPackManager`、`TeamManager` | 各系统一个 Manager（多为单例） | **★ 适合（高价值）** | ★ **按业务域切 Manager** —— 这正是 Mahatma 完全缺失的。详见 `task.md` / `battle.md` |
| **业务实体（轻量）** | `Thing`、`Medication`、`EquipMent`、`Skill`、`RealSkill`、`TaskItem`、`Monster`、`Npc`、`Player*`、`Animal`、`Door` | 数据 + 少量自绘 | 适合 | 与 Manager 配合的实体类 |
| **数据驱动配置** | `Resources/GameData.xml`（plist, 16.5 KB）、`Resources/*.xxp/.att/.dec/.tsk/.tk/.mp` | 静态数据外置 | **★ 适合（高价值）** | ★ 见 §5 |
| **UI 层** | `BeginLayer`、`LoginLayer`、`SigOnLayer`、`NewGameLayer`、`SelectLayer`、`GameUILayer`、`RoleInfoLayer`、`BackPackLayer`、`SkillLayer`、`EquipMent/DetailLayer`、`TaskLayer`、`TeamLayer`、`MsgListLayer`、`PrivateTalkLayer`、`TalkLayer`、`FightLayer`、`WorldMapLayer`、`DealLayer`、`PickupTaskLayer`、`PlayerListLayer`、`RoleInfoLayer` … | 各界面一个 Layer | 不适合照抄 | UI 与业务有一定耦合（Layer 直接调 Manager/CMClient） |

**⇒ 分层评分对照**：

| 关注点 | ChivalrousMan | MahatmaComeBack |
|---|---|---|
| 传输/协议独立文件 | ✅ `TCPClient` + `ShareData.h` + `CMClient` | ❌ 全在 `Form1.cs` / `SocketService` |
| 协议结构体集中 | ✅ 23 枚举 + 22 结构体 | ❌ 无（裸字符串） |
| 数据实体 Model | ✅ `Model.h`（5 个，自描述表结构） | ❌ 无 |
| 持久层泛型 DAO | ✅ `DBDao<T>` | ⚠ 有门面但被绕过 |
| 业务按域拆 Manager | ✅ 5 个 Manager | ❌ 一个 `manipulationData` |
| 静态数据外置 | ✅ plist + 自定义文本表 | ⚠ 仅 `text.xml` 文案 |
| 心跳/分帧/加密 | ❌ 全无 | ⚠ 仅靠 WebSocket 分帧 |

---

## 五、静态数据驱动（★ 可借鉴度很高的部分）

| 文件 | 格式（实测样例） | 用途 | 是否适合 JSTM | 原因 |
|---|---|---|---|---|
| `Resources/GameData.xml` | plist dict，16.5 KB；`<key>Ghost</key><string>Monster/Ghost/Ghost</string>` … | 资源名 → 资源路径映射（怪物/技能/NPC/物品/UI） | **适合** | ★ **"名字即索引"**：代码只写 `StringValue("Ghost")`，路径变更无需改代码 |
| `Resources/mapinfo.xxp` | `map1 142 420 流水村` / `map2 230 190 火山城` / `map3 490 300 荒山` / `map4 530 450 大平原` / `map5 680 490 极寒之地` | 5 张地图：id / 宽 / 高 / 中文名 | **适合** | ★ 极小但完整的**地图表**（= JSTM `config_map` 的迷你版） |
| `Resources/Task/Task{n}.tsk` | `name 黑龙肆虐` / `schedulewho BlackDragon` / `glodreward 500` / `expreward 600` / `index 1` / `curschedule 0` / `allschedule 6` / `type 2001` | **任务定义表**（名/目标怪/金币奖励/经验奖励/序号/当前进度/总进度/类型） | **★ 适合（高价值）** | 8 个字段就定义完一条"击杀任务"；`type 2001` 与 `PreProcess.h` 的 `#define T_KILL 2001` 对应 |
| `Resources/Task/Task{n}.tk` / `EndTask.tk` / `NoEndTask.tk` | 多行对话文本 | 接任务/交任务/未完成 三态对话 | **★ 适合** | ★ **任务状态 ↔ 对话文本**一一对应，是 NPC 任务对话的最小实现 |
| `Resources/Thing/*.att` | `buyglod 100` / `sellglod 50` / `addblood 0` / `addmana 100` | **物品属性表**（买入价/卖出价/加血/加蓝） | **★ 适合（高价值）** | 44 个 `.att` = 44 件物品的**价格与效果** |
| `Resources/Thing/*.dec` | `蓝瓶` / `蓝蓝的真好喝` / `还能补篮` / `绝对是居家旅行的必备之物` | 物品名 + 描述（首行名、后续行描述） | 适合 | 文案外置 |
| `Resources/Skill/<名>/<名>.att` | ✅ **R2 已读到全部 8 个**（【已确认】）。格式 = 首行中文名 + 6 个键值：`name` / `buyglod` / `sellglod` / `baseattack` / `basemana` / `baseupglod`。<br>实测全表：`CrackIt` 紫焰狼爪 1500/750/300/50/500；`Dante` 裂地 1200/600/100/50/550；`DragonRoar` 蓝龙诀 1000/500/250/50/550；`LightStrike` 狂雷诀 1500/750/230/50/600；`long` 火龙诀 1200/600/340/50/620；`recallCountermand` 烈焰神龙 1600/800/350/50/650；`SealOfTheBlade` 天魔-封 1700/850/250/50/690；`XBArrow` 冰毒箭 1300/650/320/50/720 | **技能属性表**（含中文名/买价/卖价/**基础攻击**/基础耗蓝/**升级基础花费**） | **★ 适合（高价值）** | 8 个技能目录 + 8 条 `SkillFactory` 分支 = "技能上限 8" 的真实来源；`baseattack` 与 `baseupglod` 是**技能伤害与升级花费的配置来源**（对照 `battle.md` 的伤害公式 `baseAttack + 30×grade`） |
| `Resources/Monster/<名>/<名>.att` | ✅ **R2 已读到全部 10 个**（【已确认】）。格式 = 首行 `//最后一行为动画帧数` + 中文名 + 7 个键值：`attack` / `blood` / `defense` / `speed` / `exp` / `glod` / `frames`。<br>实测全表（attack/blood/defense/speed/exp/glod/frames）：`BlackDragon` 黑龙 120/320/40/5/100/30/6；`Dragon` 小飞龙 100/200/60/5/150/40/12；`Ghost` 亡灵 250/200/40/5/150/60/6；`Kougamon` 甲兽 180/700/120/5/180/50/6；`Lion` 小狂狮 250/560/60/5/200/70/5；`Minotaur` 牛头怪 255/500/100/5/200/80/5；`Octopus` 章鱼哥 265/600/80/5/200/80/6；`Pterosaur` 肥龙 300/500/100/5/300/80/7；`SkeletonMaster` 骨法师 280/560/80/5/300/100/9；`TarrasqueMessenger` 魔龙使者 300/600/80/5/300/100/6 | **怪物属性表** | **★ 适合（高价值）** | 10 个怪物的完整战斗数值 + 经验/金币产出；**全部 `speed = 5`（10 只怪速度完全一致）** ⇒ 设计上不区分怪物行动速度；**无掉落字段**（与 `battle.md` 的"无掉落表"一致） |
| `Resources/mapinfo.xxp` / `map{n}.mp` | `.mp` = 地图阻挡/传送点（文件名 `map1.mp`~`map5.mp`） | 地图网格/阻挡 | 【待验证】 | `MapInfo::readMapInfoFromFile` 读取 |
| `Resources/GameDynamicData.data` | `BgMusic 0` | 动态数据持久化文件 | 不适合 | 客户端本地存档（`GameDynamicData::readDataFromFile/writeDateToFile`） |

**⇒ ★ 8 个技能目录 + 8 条技能分支 = "技能数量上限 8" 的真实来源**（不是常量，是资源与代码的事实上限）——
详见 `battle.md` 的对应结论。

---

## 六、关键工程细节与缺陷

### 6.1 协议打包方式（★ 与 JSTM 最相关的兼容风险）

| 项 | 实测 | 风险 |
|---|---|---|
| 发送 | `SendMsg((char*)&msg, sizeof(msg))` | 结构体内存直发 ⇒ **依赖编译器对齐/填充、结构体布局、字节序**；32/64 位或不同编译器下布局可能不同 |
| 接收 | `M_Type type = *((M_Type*)buff);` + `(InitData_Msg*)buff` | **无长度校验、无边界检查**；`recv` 无分帧 ⇒ 粘包/半包直接错乱 |
| `char[]` 字段 | `char playername[40]`、`char msg[200]`、`char skill[30]`、`char map[10]` | 定长字符数组 ⇒ 协议**不可扩展**（改长度即全端不兼容） |
| 字符串复制 | `strcpy_s(msg.playername, GetStringData("playername").c_str())` | **无长度校验**（`strcpy_s` 只在越界时抛，不截断）⇒ 超长名会崩 |
| `fd` 字段 | 服务端分配的唯一连接标识；客户端发消息时填 `-1` | 【待验证】语义见 `battle.md` |
| 断线哨兵 | `CLOSE_MESSAGE "~#@**close**@#~"` | ★ 用一个**魔数字符串**当断线信号（在无分帧的情况下这是"能跑"的取巧），且会与真实消息内容冲突 |

### 6.2 线程模型

| 项 | 实测 | 判定 |
|---|---|---|
| 连接 | `BeginScene::init` 里 `std::thread th{func}; th.detach();` | 【已确认】连接在**游离线程**里做，成功后写 `SetIntData("IsConnectNet",1)` |
| 接收 | `m_recvThread` 跑 `DoServerMsg()` 死循环 `recv` | 【已确认】 |
| 回调 | `recv` 的 buff 直接在**接收线程**里回调 `CMClient::OnRecv` → 直接操作 Cocos 节点（`CurGameScene()->getObjectLayer()->addPlayer(...)`） | ⚠ **跨线程操作 Cocos 场景图**（Cocos 非线程安全）【已确认】 |
| `GameDynamicData` | 用 `std::atomic` + `std::mutex` 实现单例（`PreProcess.h` 宏） | 【已确认】单例创建有保护，但 **map 读写没有加锁** |
| `TCPClient::CloseClient` | `WSACleanup(); closesocket(); m_isClose=true; m_recvThread->join();` | 【待验证】`WSACleanup` 在 `closesocket` 之前调用，顺序可疑 |

### 6.3 死代码/遗留物（实测）

| 文件 | 现象 | 判定 |
|---|---|---|
| `Classes/DBDao.cpp` | 定义了 **非模板** 的 `DBDao::DBDao(host,user,passwd,dbname)` / `~DBDao` / `registerModel()`，但 `DBDao.h` 里 `DBDao` 已是 **template<typename Model>** ⇒ **不可能编译通过** | 【已确认】；且 **不在 `ChivalrousMan.vcxproj` 的 `ClCompile` 列表** ⇒ **未被编译的死文件** |
| `Classes/SkillInfo.cpp` | **0 字节** | 【已确认】空文件 |
| `Classes/Waite.h` | 13 字节（文件名疑似 `Wait` 拼写错误） | 【已确认】 |
| `Classes/Login.{h,cpp}`、`Classes/SignOn.{h,cpp}` | 与 `LoginLayer`/`SigOnLayer` 并存（旧版遗留） | 【待验证】（`Login.cpp`/`SignOn.cpp` 未出现在 `ClCompile` 列表 ⇒ 疑为死代码） |
| `Classes/HelloWorldScene.{h,cpp}` | cocos2d 模板遗留 | 【已确认】 |
| `Classes/typelist.h` | 19 KB 前向声明大表（`#include` 聚合） | 适合（工程手法） |

### 6.4 已知稳定缺陷（可指回代码）

| # | 缺陷 | 位置 | 后果 | 标注 |
|---|---|---|---|---|
| 1 | `doPlayerPosVerifyMsg` 循环条件写成 `var != m_playerlist.begin()` | `CMClient.cpp` 256 | 🔴 **循环体永不执行**（起点即等于 `begin()`）⇒ 服务端下发的**位置校验消息从未生效** | 【已确认】 |
| 2 | `CameraPlayer::SaveGameData()` 里 `playerinfo.setlevel(NTS(GetIntData("CurMap")))`，但 `updateModel` 的 `where` 用 `playername + rolename` | `CameraPlayer.cpp` 244-263 | 存档以 (playername, rolename) 为键 —— 正确；但 `PlayerInfo` 的 `playername`/`rolename` **未被 `setModel` 之外赋值**？实测**已赋值** | 【已确认】 |
| 3 | `findPlayerInfoByFd` 未命中时返回**默认构造**的 `Player_Info`（字段未初始化） | `CMClient.cpp` 383-394 | 调用方无法区分"未找到"与"有效空信息" | 【已确认】 |
| 4 | `m_privateTalkMsgs` 容量逻辑矛盾：先判 `size() >= 6` 删 `begin()`（这是**会话数**上限），后判 `[realfd].size() > 18` 删 `front()`（**消息数**上限） | `CMClient.cpp` 359-380 | 语义混淆；注释与实际不符 | 【已确认】 |
| 5 | 数据库凭据硬编码在客户端可执行文件 | `DBDao.h` 105-113 | 任意用户可提取凭据、直连生产库 | 【已确认】 |
| 6 | `DBDao` 每次构造都 `mysql_real_connect`，每次操作后 `mysql_close`；无连接池 | `DBDao.h` 106-129 | 频繁建连；同时 `queryModel` 里 `mysql_store_result` 后**未 `mysql_free_result`** ⇒ 内存泄漏 | 【已确认】 |
| 7 | `TCPClient::SendMsg` **无分帧、无发送队列** | `TCPClient.cpp` 55-63 | 多线程并发发送会交错 | 【已确认】 |
| 8 | 接收线程直接改 Cocos 场景图 | `CMClient::doInitPlayerPosMsg` → `CurGameScene()->getObjectLayer()->addPlayer(...)` | 跨线程渲染风险 | 【已确认】 |

---

## 七、与 JSTM 的映射建议（按子系统）

| JSTM 子系统 | ChivalrousMan 可借鉴什么 | 形态 | 优先级 |
|---|---|---|---|
| **数据库设计** | ★ ★ **`Model.h` 的 5 张表（`player`/`playerinfo`/`skillinfo`/`equipmentinfo`/`backpack`）及全部字段** + 账号/角色分表思路 | **思想 + 字段清单** | **最高** |
| 持久化流程 | 注册→登录→建号→选角→读背包/装备/技能 → 进场景 的完整时序 | 思想 | 高 |
| 协议设计 | ★ `ShareData.h` 的"命令枚举 + 定长结构体"集中定义方式；22 条消息的**职责划分** | 思想 | 高 |
| 组队系统 | ★ 组队申请/同意/拒绝/移动/切图/解散/踢人 **8 条消息**的完整拆分 | 思想（`task.md`/`battle.md` 详列） | 高 |
| 聊天系统 | 世界/私聊两通道 + 本地队列（`m_worldTalkMsgs` 上限 100、私聊按 fd 分组上限 18） | 思想 | 中 |
| 任务系统 | ★ `Task{n}.tsk`（8 字段）+ `Task{n}.tk`（三态对话）+ `type` 宏（`T_KILL/T_COLLECT/T_ACCESS`） | **思想 + 数据结构** | 高 |
| 背包/装备/技能 | ★ 5 表结构 + 槽位宏（`EM_HEAD/WEPON/JEWELRY/CLOTH/FOOT`）+ 物品类型宏（`MEDICATION/EQUIPMENT/SKILL`） | 思想 + 字段清单 | 高 |
| 战斗 | 见 `battle.md`（**回合制逻辑 + 客户端权威 + 无伤害字段的协议** ⇒ 明确**不要学**其权威模型） | 反面为主 | 中 |
| 移动同步 | ★ **存在 `M_VerifyPos` 位置校验消息**（Mahatma 完全没有）；但客户端实现有 bug（§6.4 #1） | 思想 | **高** |
| 静态数据 | ★ `GameData.xml`（名字即索引）+ `mapinfo.xxp`（地图表）+ `.att/.dec`（物品表） | 思想 | 中 |
| 分层组织 | ★ `TCPClient`（传输）/`CMClient`（协议）/`Model.h`（实体）/`DBDao<T>`（持久）/`*Manager`（业务）五段式 | 思想 | 高 |
| 任何代码 | ⚠ 无 LICENSE ⇒ 无授权依据，**不要直接复制** | ❌ | — |

---

## 八、一句话总结

> **ChivalrousMan 本仓库确实只有客户端（92 个 `Classes/*.cpp`），服务端在 `gitee.com/lsylovews/CM-Server`（未包含、未读到）。
> 但它的客户端里嵌了一个"半个服务端"——`DBDao.h` 用 libmysql 直连 MySQL（凭据硬编码），
> 因此本仓库同时暴露了：①一套完整的 MMORPG 业务分发层（`TCPClient`+`ShareData`+`CMClient`），
> ②一套按域切的业务管理层（5 个 Manager），③**一套 5 张表的业务数据库结构**。
> 它是本项目在"传统 MMORPG 业务流程与数据结构"维度上**信息量最大的参考**，但**必须只用其思路与字段语义，不能复制代码（无 LICENSE）**。**

---

## 九、未读到 / 待验证

> **R2 更新**：本次闭合 3 项（标 ✅），并新增 1 项由逐文件阅读得到的重要结论。

| 项 | 状态 |
|---|---|
| ✅ `Resources/Skill/*/` 8 个技能的 `.att` 内容 | **已闭合 →【已确认】全部 8 个已读，见 §5 表格** |
| ✅ `Resources/Monster/*/` 10 个怪物的 `.att` 内容 | **已闭合 →【已确认】全部 10 个已读，见 §5 表格** |
| ✅ 任务进度是否通过 TCP 上报服务端 | **已闭合 →【已确认】不走 TCP、也不落库**：`M_Type` 中**无任何任务消息**；`Model.h` 中**无任务实体**；任务定义由**客户端后台线程每 15 秒随机生成**（`TaskSystem.cpp:52-63` `workThread` → `createTask() ; Sleep(15000)`），任务列表仅在内存 `std::list` 中 ⇒ **客户端重启即全部丢失**。详见 `task.md` R2 附录 |
| ✅ 新增：任务系统本质 | **【已确认】任务是"客户端本地随机生成"的**：`createTask()` 用 `std::random_device` 取 `rand()%11+1` 选模板（`Resources/Task/Task1..11.tsk` 共 11 个），**且 `fromwho`/`destwho`（接取 NPC / 交付 NPC）由 `m_npcvec[rand()%4]` 随机指定，不来自 `.tsk`**（`TaskSystem.cpp:101-102`，`m_npcvec = {"NpcVallige","NpcBlue","NpcMamom","NpcMonk"}`） |
| 服务端源码（`gitee.com/lsylovews/CM-Server`） | 【未读到】不在 ZIP 内；**这是本项目最大的信息缺口** |
| `*.sql` 建库脚本（README 提到"附件中的 sql 文件"） | 【未读到】本仓库无 `.sql` 文件 |
| `DB.cfg`（README 提到的数据库配置） | 【未读到】仓库内无此文件（凭据只硬编码在 `DBDao.h`） |
| `Resources/*.mp` 地图文件的二进制格式 | 【未读到】`MapInfo::readMapInfoFromFile` 已读到函数签名，未展读实现 |
| `Resources/mapinfo.xxp` 之外的 `Resources/res/` 与 `LevelObject/` 用途 | 【未读到】 |
| `Classes/Login.{h,cpp}`、`SignOn.{h,cpp}` 是否为死代码 | 【待验证】未在 `ClCompile` 列表 ⇒ 疑为旧版遗留 |
| `T_COLLECT` / `T_ACCESS` 两类任务的进度实现位置 | 【待验证】全 `Classes/` 中 `curschedule++` **只出现 1 次**（`TaskSystem.cpp:180`，位于 `checkKillMonster` 内），而 `checkKillMonster` 只被 `Monster.cpp:114`（怪物死亡）调用 ⇒ **收集类与访问类任务在客户端侧没有任何进度增加路径**（疑似无法完成）；是否由服务端补足未读到 |
| 客户端本地记账与服务端存档的一致性 | 【未知】服务端缺失，无法验证 |
