# ChivalrousMan（侠客行）—— 数据库审计

> **审计对象**：`cankao/ChivalrousMan-master.zip`
> **无 LICENSE** ⇒ 无授权依据，字段与结构可作**设计参考**，**不要直接复制代码/DDL**。详见 `reuse_candidates.md`。
> 标注：【已确认】/【待验证】/【未知】。

---

## 一、★ 先回答任务书的问题：本项目有服务端数据库吗？

> ### 【已确认】**本仓库内没有服务端，也没有任何建库脚本。**
>
> | 检验项 | 实测 | 判定 |
> |---|---|---|
> | 仓库内有 `server/` 目录吗 | **没有**（顶层只有 `Classes/ cocosstudio/ include/ lib/ proj.android/ proj.ios_mac/ proj.win32/ Resources/`） | 【已确认】 |
> | 仓库内有 `.sql` 文件吗 | **没有** —— `namelist()` 全 1539 条目中 `.sql` **0 命中** | 【已确认】 |
> | 仓库内有 `DB.cfg` 吗 | **没有** —— 只有 `Resources/server.cfg`（服务器地址）与根目录 `ChivalrousMan.cfg`（工程配置） | 【已确认】 |
> | README 怎么说 | 「服务器项目源码在 _https://gitee.com/lsylovews/CM-Server_」；「执行**附件中的 sql 文件**新建数据库」；「修改同目录下的 **DB.cfg** 修改数据库配置」 | 【已确认】 |
> | ⇒ 结论 | **README 提到的 `sql 文件` 与 `DB.cfg` 都不在本仓库内** ⇒ 本仓库是**不含服务端的客户端切片** | 【已确认】 |
>
> ### ⚠ 但必须补充：**客户端直连了一个真实存在的 MySQL 库**
>
> `Classes/DBDao.h` 用 **libmysql** 直连数据库，**连接参数硬编码在客户端源码里**：
> ```cpp
> // Classes/DBDao.h:106-113（审计引用）
> DBDao<Model>::DBDao() :
>     m_host("47.93.235.6"),
>     m_passwd("3252918599lsy"),
>     m_username("game"),
>     m_dbname("chivalrousman")
> { initConnect(); }
> ```
> 配套证据：`#include<mysql.h>` / `#include<mysqld_error.h>`；`#pragma comment(lib,"libmysql.lib")`；
> `lib/libmysql.dll`（4.63 MB）、`lib/{vs12,vs14}/mysqlclient.lib`；`include/` 下 **68 个 MySQL 客户端 SDK 头文件**。
>
> ### ⇒ 因此本文件的实际内容定为：
> **①「无服务端数据库脚本」的实证（上表）；② 从客户端代码**完整反推**出的数据库结构（下面 §2 的 5 张表）。**
> 这 5 张表是**本项目对 JSTM 最有价值的数据资产** —— 因为 MySQL 端的 `CREATE TABLE` 脚本虽缺失，
> 但每张表的**表名、字段名、字段顺序与语义**都在 `Model.h` 里以可读代码形式给出【已确认】。

---

## 二、★ 反推的数据库结构（5 张表，全部【已确认】）

**反推依据**：`Classes/Model.h` 的 `getName()`（表名）+ `getAttributeName(i)`（字段名）+ `operator[](i)`（字段序号）；
配合 `Classes/DBDao.h` 的 `generateSql/generateWhere/generateValues/generateUpdate`（SQL 拼装规则）与 8 个文件的调用点。

### 2.0 库级信息

| 项 | 实测值 | 来源 |
|---|---|---|
| DBMS | **MySQL** | `#include<mysql.h>`；README「游戏使用的数据库是 mysql」 |
| 库名 | **`chivalrousman`** | `DBDao.h:110` `m_dbname("chivalrousman")` |
| 主机 | **`47.93.235.6`**（阿里云公网 IP，README 称"搭在个人的阿里云服务器上"） | `DBDao.h:107` |
| 端口 | **3306**（`unsigned int m_port = 3306;`） | `DBDao.h:100` |
| 账号 / 密码 | **`game` / `3252918599lsy`（明文硬编码）** | `DBDao.h:108-109` |
| 表数量 | **5**：`player`、`playerinfo`、`skillinfo`、`equipmentinfo`、`backpack` | `Model.h` 的 5 个 `getName()` |
| 字符集 / 引擎 | 【未读到】无建库脚本，**无法确认**（MySQL 客户端 API 未指定 `set names`） | — |
| 索引 / 外键 / 约束 | 【未读到】无建库脚本；**代码中未见任何索引或约束假设** | — |
| 事务 | ❌ **`DBDao` 完全没有事务 API**（无 `mysql_autocommit`/`mysql_commit`/`mysql_rollback`） | 【已确认】 |

### 2.1 表 `player` —— 账号表

**来源**：`Model.h` 的 `class GamePlayer`，`getName()` 返回 `"player"`，`getAttributeNums()` = 3。

| # | 字段名（原文小写） | C++ 成员 | 反推语义 | 实测取值示例 | 标注 |
|---|---|---|---|---|---|
| 1 | `playername` | `playerName` | 账号名 | 用户输入（UI 无长度上限，见 `ADD_EDIT(tfUserName,...)`） | 【已确认】 |
| 2 | `playerpsw` | `playerPsw` | **密码（明文）** | 用户输入；`LoginLayer` 直接用 `WHERE playername=? and playerpsw=?` 匹配 | 【已确认】 |
| 3 | `nums` | `nums` | 该账号**已创建的角色数**（上限 3） | 注册时写 `0`；建号后 `+1` | 【已确认】 |

**★ 关键**：`nums` 这一列说明设计者**有"一个账号多角色"的概念**（与 Mahatma 的"账号即角色"截然不同），
角色上限 3（`NewGameLayer::onConfirmCallBack`：`if (std::stoi(nums) >= 3) { MessageBox("角色数已达上限"); return; }`）【已确认】。

**构造/DDL 反推（JSTM 重新实现时的对照，**不是**原文 DDL）**：
`Playername` 与 `playerpsw` 是查询条件（`generateWhere` 会把所有**非空**成员都拼进 `WHERE ... AND ...`）。

### 2.2 表 `playerinfo` —— 角色表（★ 最核心）

**来源**：`Model.h` 的 `class PlayerInfo`，`getName()` 返回 `"playerinfo"`，`getAttributeNums()` = **15**。

| # | 字段名 | 类型推断 | 语义 | 建号初值（`NewGameLayer::constructPlayerInfo`） | 标注 |
|---|---|---|---|---|---|
| 1 | `playername` | varchar | 账号名（**外键语义 → `player.playername`**） | `GetStringData("playername")` | 【已确认】 |
| 2 | `rolename` | varchar | 角色名（**一个账号 ≤3 个**） | 用户输入；`≤3` 校验在客户端 | 【已确认】 |
| 3 | `roletype` | varchar | 职业/形象：`"Player1"` / `"Player2"` / `"Player3"` | 由 `m_playerType` 选择 | 【已确认】 |
| 4 | `glod` | varchar→数值 | **金币**（原文拼写 `glod`，非 `gold`） | **300** | 【已确认】 |
| 5 | `grade` | varchar→数值 | 等级 | **1** | 【已确认】 |
| 6 | `blood` | varchar→数值 | 总血量上限 | **300** | 【已确认】 |
| 7 | `mana` | varchar→数值 | 魔法上限 | **150** | 【已确认】 |
| 8 | `attack` | varchar→数值 | 攻击力 | **100** | 【已确认】 |
| 9 | `defense` | varchar→数值 | 防御力 | **20** | 【已确认】 |
| 10 | `speed` | varchar→数值 | 移动速度 | **4** | 【已确认】 |
| 11 | `exp` | varchar→数值 | 当前经验 | **0** | 【已确认】 |
| 12 | `maxexp` | varchar→数值 | 升级所需经验 | **100** | 【已确认】 |
| 13 | `destx` | varchar→数值 | 上次下线 X 坐标 | **"100"** | 【已确认】 |
| 14 | `desty` | varchar→数值 | 上次下线 Y 坐标 | **"100"** | 【已确认】 |
| 15 | `level` | varchar→数值 | **当前所在地图/关卡号**（`1..5`；命名是 `level` 但语义是 map level） | `NTS(LEVEL_ONE)` = `"1"` | 【已确认】 |

**★ 建号初值全表（原文，【已确认】`NewGameLayer::constructPlayerInfo`）**：
```
playerinfo.setplayerName(GetStringData("playername"));
playerinfo.setroleName(name);
SetInfo(attack, 100);   SetInfo(blood, 300);   SetInfo(defense, 20);
SetInfo(glod, 300);     SetInfo(grade, 1);     SetInfo(mana, 150);
SetInfo(speed, 4);      SetInfo(exp, 0);       SetInfo(maxExp, 100);
playerinfo.setdestx("100");  playerinfo.setdesty("100");
playerinfo.setlevel(NTS(LEVEL_ONE));
```

**★ 存档路径（【已确认】`CameraPlayer::SaveGameData()`）**：
```cpp
PlayerInfo playerinfo;  DBDao<PlayerInfo> dbdao;
playerinfo.setattack / setblood / setdefense / setdestx / setdesty /
         setexp / setglod / setgrade / setmana / setmaxExp / setlevel(NTS(CurMap));
dbdao.setModel(playerinfo);
std::map<std::string,std::string> keyvls;
keyvls["playername"] = GetStringData("playername");
keyvls["rolename"]   = GetStringData("rolename");
dbdao.updateModel(keyvls);
```
⇒ 生成 SQL 形态：`UPDATE playerinfo SET attack='..', blood='..', defense='..', destx='..', desty='..', exp='..', glod='..', grade='..', mana='..', maxexp='..', level='..' WHERE playername='..' AND rolename='..'`【已确认】

**★ 注意**：`blood`（上限）与 `curblood` **不同字段** —— `curblood` 只存在于客户端内存（`PlayerData::m_curblood`），**不落库**【已确认，`SaveGameData` 未写 `curblood`】。

### 2.3 表 `skillinfo` —— 技能表

**来源**：`Model.h` 的 `class SkillInfo`，`getName()` 返回 `"skillinfo"`，`getAttributeNums()` = 4。

| # | 字段名 | 语义 | 实测 | 标注 |
|---|---|---|---|---|
| 1 | `playername` | 账号名 | — | 【已确认】 |
| 2 | `rolename` | 角色名 | — | 【已确认】 |
| 3 | `skillname` | 技能名（英文资源名，如 `"CrackIt"`、`"DragonRoar"`、`"LightStrike"`、`"SealOfTheBlade"`、`"XBArrow"`、`"long"`、`"Dante"`、`"recallCountermand"`） | 8 个技能目录 | 【已确认】 |
| 4 | `skillgrade` | 技能等级 | 购买时初始等级；`upSkill` 时 `+1` | 【已确认】 |

**★ 一个角色一行一个技能**（无 `skillid`，用 `(playername, rolename, skillname)` 三元组定位）【已确认】。
**★ 唯一约束靠"代码判重"**：`SkillManager::addSkill` → `if (m_skillMap.find(name) != end()) return -1;`（不重复购买）【已确认】。

**★ 技能上限 8 的真实来源**：不是常量、不是 DB 约束，而是**恰好 8 个技能资源目录 + `SkillFactory` 的 8 条 `if-else`**；
`SkillManager::skillNumbers()` 存在但**零调用** ⇒ **代码里根本没有对"8"的校验**【已确认，与 `battle.md` 结论一致】。

### 2.4 表 `equipmentinfo` —— 装备表

**来源**：`Model.h` 的 `class EquipmentInfo`，`getName()` 返回 `"equipmentinfo"`，`getAttributeNums()` = 5。

| # | 字段名 | 语义 | 实测 | 标注 |
|---|---|---|---|---|
| 1 | `playername` | 账号名 | — | 【已确认】 |
| 2 | `rolename` | 角色名 | — | 【已确认】 |
| 3 | `equipmentname` | 装备名（英文资源名，如 `"ArmorShoes"`、`"BlackWitchHelmet"`） | 对应 `Resources/Thing/*.png/.att/.dec` | 【已确认】 |
| 4 | `grade` | 装备等级（精炼等级） | 穿上时重置为 `1`；`upEquipment` 时 `+=1` | 【已确认】 |
| 5 | `type` | **装备槽位类型** | 宏定义见下 | 【已确认】 |

**★ 槽位类型宏（【已确认】`Classes/PreProcess.h` 108-113）**：
```cpp
#define EM_HEAD     1005   // 头盔
#define EM_WEPON    1006   // 武器（原文拼写 WEPON）
#define EM_JEWELRY  1007   // 首饰
#define EM_CLOTH    1008   // 衣服/装甲
#define EM_FOOT     1009   // 鞋子
```
**⇒ 5 个装备槽位**，与 README「一个玩家最多可以装备五件装备分别是头盔、装甲、首饰、武器和鞋子」**完全一致**【已确认】。
**⇒ `type` 是"穿在哪个槽"而不是"物品分类"** —— 这是它与 `backpack.thingtype` 的关键区别【已确认，`EquipmentManager::wearEquipment` 里 `if (it->type == info.type)` 按槽替换】。

**★ "穿上装备会把该槽已有装备卸下"（【已确认】`EquipmentManager::wearEquipment`）**：遍历 `m_emlist` 找同 `type` → `EquipMent::createWithImage(it->name + ".png")` + `setgrade(it->grade)` + `Disassemble(nullptr)`（销毁旧的）→ `it->name = info.name; it->grade = 1;` return -1（替换）；否则 `push_back` return 0（新装）。

### 2.5 表 `backpack` —— 背包表

**来源**：`Model.h` 的 `class BackPack`，`getName()` 返回 `"backpack"`，`getAttributeNums()` = 6。

| # | 字段名 | 语义 | 实测 | 标注 |
|---|---|---|---|---|
| 1 | `playername` | 账号名 | — | 【已确认】 |
| 2 | `rolename` | 角色名 | — | 【已确认】 |
| 3 | `thingname` | 物品名（英文资源名，如 `"BlueMedicine"`、`"BeastBone"`、`"AnimalSkin"`） | 44 个 `.att` | 【已确认】 |
| 4 | `thingtype` | **物品类型** | 宏见下 | 【已确认】 |
| 5 | `thingnums` | 数量（堆叠） | `BackPackManager` 内 `++it->nums` / `--(it->nums)` | 【已确认】 |
| 6 | `thinggrade` | 物品等级 | 从 DB 读入 `info.grade = std::stoi(var.getthinggrade())` | 【已确认】 |

**★ 物品类型宏（【已确认】`Classes/PreProcess.h` 104-106）**：
```cpp
#define MEDICATION  1001   // 药品
#define EQUIPMENT   1002   // 装备
#define SKILL       1003   // 技能（书）
```
**⇒ 一张 `backpack` 表同时容纳药品 / 装备 / 技能书**，用 `thingtype` 区分【已确认】。
（`PlayerItem.cpp` 与 `DealLayer.cpp` 应据此分流 —— 见 `task.md`。）

### 2.6 五张表的关系图（反推）

```
   player (账号)
     playername  PK(语义)   playerpsw   nums(角色数 ≤3)
        │
        │ 1 : N   （靠 playername 关联；无 DB 外键）
        ▼
   playerinfo (角色)
     playername + rolename            ← 复合逻辑主键
     roletype  glod grade blood mana attack defense speed exp maxexp destx desty level
        │
        ├── 1 : N ──► skillinfo      (playername, rolename, skillname)      skillgrade
        ├── 1 : N ──► equipmentinfo  (playername, rolename, equipmentname)  grade, type(槽位)
        └── 1 : N ──► backpack       (playername, rolename, thingname)      thingtype, thingnums, thinggrade
```
**⇒ 【已确认】三张子表都用 `(playername, rolename)` 双列做归属**，而不是 `roleId` 单列 —— 这是它最重要的结构特征（也是弱点，见 §4）。

---

## 三、`DBDao<T>` 的 SQL 生成规则（★ 决定了"表结构如何被使用"）

**来源**：`Classes/DBDao.h`（336 行，模板全在头文件里）。

| 函数 | 生成的 SQL 形态 | 关键机制 | 标注 |
|---|---|---|---|
| `queryModel()` | `SELECT * FROM <getname> WHERE <非空字段1>='v1' AND <非空字段2>='v2' ...` | `generateSql(QUERY)` 只用 `generateWhere()`；**WHERE 条件 = 该 Model 对象中所有"非空"成员** | 【已确认】 |
| `insertModel()` | `INSERT INTO <表名> VALUES('v1','v2',...,'vN')` | `generateValues()`：**按序号 1..N 顺序拼全部字段**（空字符串也拼成 `''`）；**无字段名列表** ⇒ 换列顺序即错位 | 【已确认】 |
| `deleteModel()` | `DELETE FROM <表名> WHERE <非空字段>=...` | 复用 `generateWhere()` | 【已确认】 |
| `updateModel(fieldName, value)` | `UPDATE <表名> SET <非空字段>=... WHERE <fieldName>='<value>'` | — | 【已确认】 |
| `updateModel(keyvls: map)` | `UPDATE <表名> SET <非空字段>=... WHERE k1='v1' AND k2='v2' ...` | 调用方传 `(playername, rolename[, thingname/equipmentname/skillname])` | 【已确认】 |
| `generateWhere()` | 遍历 `i=1..N`，`m_md[i] != ""` 即加入 `WHERE`/`AND` | **用空串当"未设置"哨兵**；无法把字段更新为 `""` | 【已确认】 |
| `generateValues()` | `values('v1','v2',...,'vN')` | **全部字段都写**，未设置的字段落 `''` | 【已确认】 |
| `generateUpdate()` | `set f1='v1' , f2='v2' ...` | 只写非空字段 | 【已确认】 |
| `initConnect()` | `mysql_init(0)` → `mysql_real_connect(host,user,passwd,db,3306,NULL,0)`（**每次构造都建连**） | 无连接池 | 【已确认】 |
| `~DBDao()` | `mysql_close(m_sqlCon)` | — | 【已确认】 |

### 3.1 每张表的读写调用点全表（【已确认】）

| 表 | 读（SELECT） | 写（INSERT / UPDATE / DELETE） | 文件:行 |
|---|---|---|---|
| `player` | 登录校验 | INSERT（注册） | `LoginLayer.cpp:147-153`；`SigOnLayer.cpp:106-115` |
| `player`（`nums` 列） | — | UPDATE（建号后角色数 +1） | `NewGameLayer.cpp:200-208` `dao.updateModel("playername", GetStringData("playername"))` |
| `playerinfo` | 选角时读全部角色 | INSERT（建号）；UPDATE（存档） | `SelectLayer.cpp:100-104`（读）；`NewGameLayer.cpp:94-99`（INSERT）；`CameraPlayer.cpp:247-263`（UPDATE）；`CameraPlayer.cpp` 亦含 `DBDao<PlayerInfo>` |
| `skillinfo` | `readSkillInfo()` → `SELECT * WHERE playername & rolename` | INSERT（`saveSkillInfo`）；UPDATE（`upSkill`） | `SkillManager.cpp:76-89`（读）、`91-104`（INSERT）、`57-74`（UPDATE skillgrade） |
| `equipmentinfo` | `readEquipmentInfo()` | INSERT（`saveEquipmentInfo`）；UPDATE（`updateEm`）；DELETE（`deleteEm`） | `EquipmentManager.cpp:68-85`、`87-101`、`103-114`、`116-127` |
| `backpack` | `readBackpackInfo()` | INSERT（`saveBackpackInfo`）；UPDATE（`updateBackpack`）；DELETE（`deleteBackpack`） | `BackPackManager.cpp:80-98`、`100-115`、`117-128`、`130-139` |

### 3.2 生命周期时序（谁在什么时候碰数据库）

```
【启动】BeginScene::init         → 只连游戏服务端 TCP（不碰 DB）
【注册】SigOnLayer::SigonEvent   → INSERT player(playername, playerpsw, nums=0)
【登录】LoginLayer::LoginEvent   → SELECT player（playername + playerpsw 匹配）
                                  → 读 nums（角色数）到 GameDynamicData
【选角】SelectLayer::initPlayerView → SELECT playerinfo WHERE playername
【建号】NewGameLayer::onConfirmCallBack
                                → 校验 nums < 3
                                → INSERT playerinfo（15 字段，含全部初值）
                                → UPDATE player SET nums = nums+1
                                → CMClient::SendInitPlayerData()（TCP）
【进场景】SelectLayer::onConfirmCallBack
                                → GameDynamicData 写入 rolename/PlayerType/DestX/DestY/CurMap
                                → PlayerData 载入属性（attack/blood/defense/exp/glod/grade/mana/maxExp/speed）
                                → BackPackManager::readBackpackInfo()   → SELECT backpack
                                → EquipmentManager::readEquipmentInfo() → SELECT equipmentinfo
                                → SkillManager::readSkillInfo()         → SELECT skillinfo
                                → CMClient::SendInitPlayerData()（TCP）
                                → GameScene::createWithLevel(CurMap)
【场景内】GameScene::initScene  → CMClient::SendInitPos()（TCP）
【购/用/穿/升级】各 Manager      → 即时 INSERT/UPDATE/DELETE
【存档】CameraPlayer::SaveGameData
                                → UPDATE playerinfo（11 字段，WHERE playername+rolename）
                                → BackPackManager::saveBackpackInfo()   → INSERT backpack（逐条）
                                → EquipmentManager::saveEquipmentInfo() → INSERT equipmentinfo（逐条）
                                → SkillManager::saveSkillInfo()         → INSERT skillinfo（逐条）
【购买物品】即刻写库（见 task.md）
```

---

## 四、★ 结构与实现的缺陷（每条可指回代码）

| # | 缺陷 | 证据 | 后果 | 标注 |
|---|---|---|---|---|
| 1 | **无 `roleId` 代理键**，子表全用 `(playername, rolename)` 归属 | `Model.h` 中 3 个子表的前两个字段都是 `playername`/`rolename` | 改角色名即断链；无法按 `roleId` 索引；无法跨服 | 【已确认】 |
| 2 | **所有字段都是 `std::string`**，数值靠 `std::stoi` 还原 | `Model.h` 全部 `GettingAndSetting(std::string, ...)`；`std::stoi(var.getgrade())` | 空串/非数字即抛异常；`stoi` 无法处理 `""` | 【已确认】 |
| 3 | **`saveBackpackInfo`/`saveEquipmentInfo`/`saveSkillInfo` 用的是 `insertModel()`（INSERT），不是 UPSERT** | `BackPackManager.cpp:113` `dao.insertModel();` | 🔴 **每次存档都会新增一份全量物品行** ⇒ 背包/装备/技能数据**指数膨胀、重复累加**（症状：背包数量越来越多） | 【已确认】 |
| 4 | `saveXxxInfo` 逐条 `new DBDao`（逐条 `mysql_real_connect`） | `for (auto var : list) { DBDao<...> dao; ... }` | 一次存档 = N 次建连；无批量、无事务 | 【已确认】 |
| 5 | **无事务**：`DBDao` 无任何事务 API | grep `mysql_commit`/`mysql_rollback`/`mysql_autocommit` **0 命中** | 建号 = INSERT playerinfo + UPDATE player；中间失败即数据不一致 | 【已确认】 |
| 6 | **无参数化**：`m_sql += var.first + "='" + var.second + "'"` | `DBDao.h:204` 等 | SQL 注入（角色名/物品名来自用户输入与资源文件名） | 【已确认】 |
| 7 | `queryModel()` 里 `mysql_store_result` 后**未 `mysql_free_result`** | `DBDao.h:147-164` | 内存泄漏（每次查询泄漏一个结果集） | 【已确认】 |
| 8 | **密码明文**，且以 `WHERE playername=? and playerpsw=?` 直接比对 | `LoginLayer.cpp:149-153` | 拖库即全泄露；且 WHERE 里带密码 ⇒ SQL 里出现明文 | 【已确认】 |
| 9 | **数据库凭据硬编码在客户端可执行文件** | `DBDao.h:107-110` | 任何用户可提取 `game/3252918599lsy` 直连生产库，为所欲为 | 【已确认】 |
| 10 | 客户端**直连公网 MySQL** | `m_host("47.93.235.6")` | 无内网隔离、无防火墙假设；且**客户端可任意改自己的金币/等级/装备**（本地记账 → 直接 UPDATE） | 【已确认】 |
| 11 | `BackPackManager::removeBackPackThing` 里 `m_backpackList.erase(it); deleteBackpack(*it);` | `BackPackManager.cpp:52-53` | 🔴 **迭代器失效后解引用（use-after-erase）** ⇒ 未定义行为 | 【已确认】 |
| 12 | `generateWhere()` 用 `""` 当"未设置"哨兵 | `DBDao.h:261-292` | **无法把字段更新为空串**；`queryModel` 无法按"空值"筛选 | 【已确认】 |
| 13 | `insertModel` 的 `generateValues` **不带字段名列表** | `DBDao.h:295-313` | 依赖 DB 列顺序与 `operator[]` 序号**严格一致**；一旦 DB 加列即静默错位 | 【已确认】 |
| 14 | 缺少常用字段：无 `createTime`/`lastLogin`/`maxMana`/`curblood`/`curmana` | `Model.h` 15 字段 | 无法做运营分析；当前血量/魔法不持久化 | 【已确认】 |
| 15 | `RolesInfo` 无删除/改名路径 | 未见相关代码 | 角色不可删改 | 【待验证】 |
| 16 | 无索引设计痕迹（子表查询条件都是 `(playername, rolename)`） | 全部 MANAGER 查询 | 【未读到】建库脚本 ⇒ 无法确认是否建了复合索引；**但代码期望有** | 【未知】 |

### 4.1 与 MahatmaComeBack 表设计的对照

| 维度 | ChivalrousMan | MahatmaComeBack |
|---|---|---|
| 表数量 | **5** | **1** |
| 账号↔角色 | **1 : N**（`player.nums` 计数，上限 3） | **1 : 1**（`account` 兼主键） |
| 角色属性字段数 | **15** | **6**（playerName/PlayerType/X/Y/blood/grade/direction） |
| 子表归属键 | `(playername, rolename)` 双列 | — 无子表 |
| 背包/装备/技能表 | ✅ 3 张 | ❌ 无 |
| 密码 | 明文 | 明文 |
| 事务 | ❌ 无 | ❌ 无（但**有 API**未用） |
| 参数化 | ❌ 无 | ❌ 无（但**有 API**未用） |
| 建库脚本 | ❌ **不在仓库** | ✅ `gametable.sql` |
| 可参考度 | **★ 高（字段语义完整）** | ⚠ 仅作反例 |

---

## 五、给 JSTM 的数据库建议（从本项目吸收什么）

| # | 建议 | 依据 |
|---|---|---|
| 1 | **账号与角色必须分表**（`player` + `playerinfo`），角色表用 `(accountId, roleId)` 归属，**不要用 `(playername, rolename)` 做子表外键** | §2.1/§2.2/§4.1 |
| 2 | **子表必须用 `roleId` 单列**（本项目用双列字符串是最大的结构弱点） | §4 #1 |
| 3 | **物品表可分而合之**：本项目用一张 `backpack` + `thingtype`（MEDICATION/EQUIPMENT/SKILL）区分 —— 这种"统一容器 + 类型字段"值得参考（JSTM 若按类型分表则需 JOIN） | §2.5 |
| 4 | **装备槽位用 `type` 字段 + 槽位宏（1005..1009）表达** —— 与 JSTM 的装备槽设计可对照 | §2.4 |
| 5 | **`level` 字段实际存"地图号"** ⇒ 命名要准确（建议 JSTM 用 `mapId`），并**地图/关卡配置独立成表**（本项目是硬编码 `map1..map5`，见 `task.md`） | §2.2 |
| 6 | **背包数量增减靠"读-改-写"整行 UPDATE**（`thingnums`）—— JSTM 应用 SQL 原子增减（`SET nums = nums - 1 WHERE nums > 0`）避免竞态 | §3 / `BackPackManager` |
| 7 | **存档必须用 UPSERT / 事务** —— 本项目用 INSERT 导致数据膨胀，是最典型的反面案例 | §4 #3 |
| 8 | 数值字段**必须用数值类型**，不要全 `varchar` + `stoi` | §4 #2 |
| 9 | 数据库凭据**绝不能进客户端**；客户端应只与服务端通信 | §4 #9/#10 |

---

## 六、未读到 / 待验证

| 项 | 状态 |
|---|---|
| **建库脚本（`CREATE TABLE` 原文、索引、引擎、字符集、列顺序）** | 【未读到】仓库内无 `.sql`；列顺序只能由 `Model.h` 的 `operator[]` 序号推断 |
| `DB.cfg`（README 提到的数据库配置） | 【未读到】仓库内无此文件 |
| 服务端（`gitee.com/lsylovews/CM-Server`）如何读写同一个库 | 【未读到】不在 ZIP 内 |
| 服务端是否与客户端"同时写同一张表"（并发冲突） | 【未知】 |
| 各表的实际数据规模与重复行情况 | 【未知】无数据导出 |
| 是否存在 `drop`/迁移脚本 | 【未读到】 |
| `player.nums` 与实际 `playerinfo` 行数是否一致（可能因缺陷 #3 不一致） | 【待验证】 |
| `stoi` 遇到 DB 里空串时的行为 | 【待验证】`std::stoi("")` 抛 `std::invalid_argument`；若某列曾为 `NULL`/`''` 则客户端崩 |
