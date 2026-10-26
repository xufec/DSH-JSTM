# MahatmaComeBack —— 数据库审计（★ 重点：`Server/gametable.sql` 表结构整理）

> **对象**：`cankao/MahatmaComeBack-master.zip` → `Server/gametable.sql`
> **阅读方式**：`zipfile.ZipFile(...).read('MahatmaComeBack-master/Server/gametable.sql').decode('utf-8')` —— **全文 1397 字节，已完整读完**。
> **🔴 LICENSE = GNU GPL v3 ⇒ 本文件中的 DDL 只是**审计引用**，**严禁把 `gametable.sql` 文本导入 JSTM 的建库脚本或复制进 JSTM 源码树**。**

---

## 一、`gametable.sql` 文件级事实（【已确认】）

| 项 | 值 |
|---|---|
| 文件路径（ZIP 内） | `MahatmaComeBack-master/Server/gametable.sql` |
| 文件大小 | **1 397 字节** |
| 编码 | UTF-8（`File Encoding: 65001`） |
| 导出工具 | **Navicat Premium Data Transfer** |
| 导出时间 | `Date: 14/06/2019 01:02:28` |
| 源库 | MySQL **8.0.16**，`Source Host: localhost:3306`，`Source Schema: gametable` |
| 内容概览 | `SET NAMES utf8mb4;` / `SET FOREIGN_KEY_CHECKS = 0;` / **1 个 `DROP TABLE` + 1 个 `CREATE TABLE`** / `SET FOREIGN_KEY_CHECKS = 1;` |

### 1.1 ★ 表清单（全文实测）

| # | 表名 | 类型 | 字段数 | 主键 | 索引（非主键） | 外键 | 引擎 |
|---|---|---|---|---|---|---|---|
| 1 | **`game`** | 基表 | **11** | `account`（BTREE） | **无** | **无** | InnoDB |

> **★ 这就是全部。** `gametable.sql` 里 `DROP TABLE IF EXISTS` 出现 **1 次**，`CREATE TABLE` 出现 **1 次**。
> **没有**角色表、物品表、装备表、技能表、任务表、怪物表、地图表、邮件表、好友表、公会表、日志表、账号封禁表、充值表。
> **没有** `INSERT` 初始数据、**没有**视图、**没有**触发器、**没有**存储过程/函数、**没有**分区、**没有**额外索引。

**⇒ 结论（★ 必读）**：任务书预设的「`gametable.sql` 定义了完整的表结构」在本项目**不成立**。
它定义的是一张**"账号即角色"的扁平宽表**，只够支撑：注册 → 登录 → 建号 → 进场景 → 走路 → 聊天 → 掉线。
**所有 MMORPG 业务数据在本项目的数据层里根本不存在。**

---

## 二、`game` 表 —— 逐字段详表（【已确认】）

**DDL 关键属性**：`ENGINE = InnoDB`、`CHARACTER SET = utf8`、`COLLATE = utf8_general_ci`、`ROW_FORMAT = Dynamic`、`PRIMARY KEY (account) USING BTREE`。

| # | 字段名 | SQL 类型 | NULL | DEFAULT | 键 | 反推语义 | 取值示例（由代码反推） | 读点（代码） | 写点（代码） |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `account` | `varchar(32)` | NOT NULL | — | **PK** | 账号；**同时是整行唯一标识 ⇒ 一个账号只能有一个角色** | `"zhangsan"` | `where account=A`（登录）；`where account='A'`（注册判重） | 仅注册时 `insert` |
| 2 | `password` | `varchar(32)` | NULL | NULL | | **明文**密码 | `"123456"` | `selectMysqlPassword()` → `Rows[0]["password"]` | 仅注册时 `insert` |
| 3 | `playerName` | `varchar(32)` | NULL | NULL | | 角色名；**`""` = 尚未建号** | `""` / `"孙悟空"` | `loginResult` 下发；`playerInformation` 下发；建号判重 `where playerName='N'` | 建号 `UPDATE game SET playerName='N'` |
| 4 | `secretKey` | `varchar(320)` | NULL | NULL | | 登录下发的会话密钥（DES+Base64 字符串）；**后续所有请求的唯一凭证** | Base64（如 `"aB3+/xY="` 形态） | `where secretKey='<k>'` 出现在**建号/进游戏/nearPlayers/position/断线** 全部查询中 | 登录成功 `UPDATE game SET secretkey='<pas>'` |
| 5 | `Online` | `varchar(32)` | NULL | NULL | | 在线标记；**中文值** | `"是"` / `"否"` / `NULL` | **★ 从未被 SELECT**（全项目仅 2 处 `UPDATE`，无查询） | 进游戏 `SET Online='是'`；断线 `SET Online='否'` |
| 6 | `PlayerType` | `varchar(32)` | NULL | NULL | | 角色职业/形象，取值字符串 `"1"` 或 `"2"` | `"1"` / `"2"` | `playerInformation`/`nearPlayer` 下发 | 建号 `UPDATE game SET playerType='T'` |
| 7 | `XPoint` | `float(10,1)` | NULL | NULL | | 当前 X（**世界像素坐标**，非 TMX 格子坐标） | `300.0`（出生）/ 走动后的世界坐标 | `playerInformation`/`nearPlayer` 下发 | 建号 `SET XPoint=300.0`；走路 `SET XPoint=<x>` |
| 8 | `YPoint` | `float(10,1)` | NULL | NULL | | 当前 Y（世界像素坐标） | `300.0`（出生） | 同上 | 建号 `SET YPoint=300.0`；走路 `SET YPoint=<y>` |
| 9 | `blood` | `float(10,1)` | NULL | NULL | | 当前血量 | `100`（建号初始） | `playerInformation`/`nearPlayer` 下发 | 建号 `SET blood='100'`（**写成字符串**） |
| 10 | `direction` | `int(10)` | NULL | NULL | | 朝向，8 向枚举 `1..8` | `1`（建号初始，= 面向上） | `playerInformation`/`nearPlayer` 下发 | 建号 `SET direction=1`；走路 `SET direction=<d>` |
| 11 | `grade` | `int(10)` | NULL | NULL | | 等级 | `1`（建号初始） | `playerInformation`/`nearPlayer` 下发（转 `int`） | 建号 `SET grade='1'`（**写成字符串**） |

### 2.1 DDL 原文（审计引用，**禁止复制进 JSTM**）

```sql
-- ----------------------------
-- Table structure for game
-- ----------------------------
DROP TABLE IF EXISTS `game`;
CREATE TABLE `game`  (
  `account`    varchar(32)  CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `password`   varchar(32)  CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `playerName` varchar(32)  CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `secretKey`  varchar(320) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `Online`     varchar(32)  CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `PlayerType` varchar(32)  CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `XPoint`     float(10, 1) NULL DEFAULT NULL,
  `YPoint`     float(10, 1) NULL DEFAULT NULL,
  `blood`      float(10, 1) NULL DEFAULT NULL,
  `direction`  int(10)      NULL DEFAULT NULL,
  `grade`      int(10)      NULL DEFAULT NULL,
  PRIMARY KEY (`account`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
```

### 2.2 DDL 的其它实测细节

| 项 | 实测 | 备注 |
|---|---|---|
| 文件头 drop 顺序 | `SET NAMES utf8mb4;` → `SET FOREIGN_KEY_CHECKS = 0;` → DROP/CREATE → `SET FOREIGN_KEY_CHECKS = 1;` | 说明确实是 Navicat 导出模板产物 |
| `utf8mb4` vs `utf8` | `SET NAMES utf8mb4`（连接层）但表是 `utf8`（3 字节）；**`Online` 存中文 `是/否`** ⇒ 用 utf8 恰好够（中文在 BMP 内） | 混用两套字符集是隐患 |
| `float(10,1)` 用于坐标 | 只有 1 位小数；但客户端 TMX 世界坐标以**像素**为单位（tile 64×64），1 位小数够用 | 用 `float` 存世界坐标不如 `int`/`DECIMAL` 稳 |
| 没有任何 `AUTO_INCREMENT` | 主键是业务字符串 `account` | 无代理键 ⇒ 无法改账号、无法分表 |
| 没有任何时间戳 | 无 `createTime` / `lastLogin` / `lastLogout` | 无法做运营分析、无法做会话过期 |
| 没有任何 `NOT NULL` 以外的约束 | 无 `CHECK`、无 `UNIQUE`（除 PK）、无外键 | `playerName` 没建唯一索引 ⇒ 重名只能靠**应用层先查后写**（并发下可重名） |

---

## 三、每个字段的 SQL 读写点全表（可逐条回源代码）

> 全部出自 `Server/游戏服务器/Form1.cs`，行号为解压后 UTF-8 副本行号。
> **⚠ 所有 SQL 都是字符串拼接，且调用 `DbConnectionMySQL.*(..., null)` ⇒ 参数数组恒为 `null`、事务恒为 `null`。**

| 触发消息 | 行号 | SQL 语句（原文形态） | 涉及字段 | 事务 |
|---|---|---|---|---|
| `register` 判重 | 178 | `select * from game where account='<A>'` | account | 无 |
| `register` 插入 | 180 | `insert into game(account,password) values('<A>','<P>')` | account, password | 无 |
| `login` 取密码 | 457 | `select * from game where account=<A>` ← **★ 引号缺失** | account, password | 无 |
| `login` 取角色名 | 221 | `select * from game where account=<A>` ← **★ 引号缺失** | account, playerName | 无 |
| `login` 取角色类型 | 222 | `select * from game where account=<A>` ← **★ 引号缺失** | account, PlayerType | 无 |
| `login` 写密钥 | 234 | `update game set secretkey='<pas>' where account=<A>` ← account 无引号 | secretKey, account | 无 |
| `createPlayer` 判重名 | 255 | `select * from game where playerName='<N>'` | playerName | 无 |
| `createPlayer` 建号 | 259 | `update game set playerName='<N>',playerType='<T>',XPoint=300.0,YPoint=300.0,grade='1',blood='100',direction=1 where secretKey='<k>'` | playerName, PlayerType, XPoint, YPoint, grade, blood, direction, secretKey | 无 |
| `loginGameScene` 读角色 | 283 | `select * from game where secretKey='<k>'` ×**7 次**（每次只取一个字段） | playerName, PlayerType, XPoint, YPoint, grade, blood, direction | 无 |
| `loginGameScene` 置在线 | 302 | `update game set Online='是' where secretKey='<k>'` | Online | 无 |
| `nearPlayers` 读自己 | 311-317 | `select * from game where secretKey='<k>'` ×**7 次** | 同上 | 无 |
| `position` walk 写 X | 343 | `update game set XPoint=<x> where secretKey='<k>'` | XPoint | 无 |
| `position` walk 写 Y | 344 | `update game set YPoint=<y> where secretKey='<k>'` | YPoint | 无 |
| `position` walk 写朝向 | 345 | `update game set direction=<d> where secretKey='<k>'` | direction | 无 |
| `position` 广播读自己 | 384-387 | `select * from game where secretKey='<k>'` ×**4 次**（playerName/PlayerType/grade/blood） | 4 字段 | 无 |
| `GetAllLayer` 读他人 | 426-432 | `select * from game where secretKey='<key>'` ×**7 次**（**每个在线会话各 7 次**） | 7 字段 | 无 |
| UI `connectMysqlButton` | 145 | `select * from game` | 全表 | 无 |
| UI `showData()` | 471 | `select * from game` | 全表 | 无 |
| 断线 `ws_SessionClosed` | 73 | `update game set Online='否' where secretKey='<k>'` | Online | 无 |

### 3.1 SQL 查询复杂度（实测统计）

| 场景 | SELECT 次数 | UPDATE 次数 | 备注 |
|---|---|---|---|
| 注册一次 | 1 | 1（insert） | — |
| 登录一次 | **3**（密码/角色名/角色类型，同一 `where account=` 查 3 遍） | 1 | 可合并为 1 次 |
| 建号一次 | 1 | 1 | — |
| 进游戏一次 | **7**（同一 secretKey 查 7 遍） | 1 | 可合并为 1 次 |
| 走路**每格** | 0（自己）+ **4 × 其它在线人数** | **3** | 🔴 每 0.4 秒触发一轮 |
| 拉周围玩家一次 | **7 × 其它在线人数** | 0 | — |
| 断线一次 | 0 | 1 | — |

**⇒ 关键量化结论**：一个 **N 人在线**的服务器，**每名玩家每走一格**（0.4 s）就会产生
**3 次 UPDATE + 4×(N−1) 次 SELECT**，并向 **N−1** 个会话各发一条消息。
N=100 时，单人行走即造成 **396 次 SELECT + 3 次 UPDATE / 0.4 秒**。这是**不可扩展**的实现。

---

## 四、数据流闭环（含"实际写入的是谁的权威值"）

```
                      ┌──────────────────────────────────────────────┐
  register  ─────────▶│ insert game(account,password)                │  明文密码
                      └──────────────────────────────────────────────┘
                      ┌──────────────────────────────────────────────┐
  login     ─────────▶│ SELECT password → 明文比对 → UPDATE secretkey│  密钥=DES(密码+时间)
                      └──────────────────────────────────────────────┘
                      ┌──────────────────────────────────────────────┐
  createPlayer ──────▶│ UPDATE playerName/PlayerType/XPoint=300/      │  ★ 一账号一角色
                      │        YPoint=300/grade=1/blood=100/dir=1     │
                      └──────────────────────────────────────────────┘
                      ┌──────────────────────────────────────────────┐
  loginGameScene ────▶│ SELECT ×7 → 下发 playerInformation            │  ★ 无内存缓存
                      │ UPDATE Online='是'                            │
                      └──────────────────────────────────────────────┘
                      ┌──────────────────────────────────────────────┐
  position(walk) ────▶│ UPDATE XPoint / YPoint / direction（3 条）    │  ★ 客户端上报即权威
                      │ → 广播 nearPlayer 给其它 N-1 个会话            │
                      └──────────────────────────────────────────────┘
                      ┌──────────────────────────────────────────────┐
  断线        ────────▶│ UPDATE Online='否' + 广播 state='remove'      │
                      └──────────────────────────────────────────────┘
```

**⇒ 【已确认】数据的唯一权威来源是客户端**：服务端只做"抄写"（`UPDATE`）+ "转发"。
客户端 `GameScene::playAnimate()` 决定坐标，服务端不校验、不修正、不回滚。

---

## 五、与 JSTM 数据层的对照（差距表）

| 维度 | MahatmaComeBack | JSTM 1.4.9 需要 | 差距 |
|---|---|---|---|
| 表数量 | **1** | 数十张 | **巨大** |
| 账号↔角色 | 1:1 同表同行 | 1:N 分表（`account` / `role` + `roleId`） | **架构性** |
| 主键 | 业务字符串 `account` | 自增/雪花 `roleId` | 大 |
| 密码 | **明文** | 哈希 + 盐 + 迭代 | **安全红线** |
| 在线态 | 中文 `varchar '是'/'否'` 且**从不查询** | `TINYINT` / 内存在线表，且被真正使用 | 大 |
| 坐标 | 每格 3 条 UPDATE | 内存态 + 定时/下线批量持久化 | **性能红线** |
| 属性 | 只有 blood/grade，无 maxBlood/mana/attack/defense/exp/gold | 完整属性集 | 巨大 |
| 背包/装备 | **无表** | 独立表 + 槽位 + 强化等级 | 缺失 |
| 技能 | **无表** | 学习表 + 等级 + CD | 缺失 |
| 任务 | **无表** | 任务进度表 + 状态机 | 缺失 |
| 日志 | **无表** | 登录/物品/货币/战斗日志 | 缺失 |
| 事务 | **0 处使用**（`transaction` 参数恒 `null`） | 关键操作必须事务 | **红线** |
| 参数化 SQL | **0 处使用**（`params` 恒 `null`） | 全部参数化 | **安全红线** |
| 会话 | 塞在角色行的 `secretKey` 列 | 独立会话表（token/expire/ip/device） | 大 |
| 字符集 | `SET NAMES utf8mb4` + 表 `utf8` 混用 | 统一 `utf8mb4` | 小 |
| 版本 | MySQL 8.0.16 | JSTM 现状 **SQLite**（见 `../../README.md` 第 119/163 行） | **存储引擎不同** |

### 5.1 可以直接"吸收教训"的 6 条（不抄任何代码/DDL）

| # | 教训 | 对应 JSTM 动作 | 标注 |
|---|---|---|---|
| 1 | 账号表不能兼角色表 | JSTM 保证 `account` 与 `role` 分离（ChivalrousMan 的 `player`/`playerinfo` 是正面参照） | 【已确认】 |
| 2 | 密码不能明文 | 上线前做一次"是否存在明文密码列"的自查 | 【已确认】 |
| 3 | 坐标不能每格落库 | JSTM 移动同步只走内存，落库走定时/下线/切图触发 | 【已确认】 |
| 4 | `DbConnectionMySQL` 有事务重载但没人用 | JSTM 自查：所有"多写"操作是否在事务里 | 【已确认】 |
| 5 | 有 `@param` 能力但传 `null` | JSTM 自查：是否存在字符串拼接 SQL | 【已确认】 |
| 6 | 同一实体被 SELECT 7 次只取 1 个字段 | JSTM 自查：是否存在 N+1 查询 | 【已确认】 |

---

## 六、未读到 / 待验证

| 项 | 状态 |
|---|---|
| 是否存在被 ZIP 遗漏的第二个 `.sql`（如角色表/物品表） | **否** —— `namelist()` 全 **136 个文件**（ZIP 条目 164，含 28 个目录）中 `.sql` 仅此 1 个【已确认】 |
| `gametable.sql` 之外的建库脚本（如 `ReadMe.md` 提到的截图版设计） | 【未读到】README 只给了一张 CSDN 图片链接，未包含在 ZIP 中 |
| 服务端是否曾跑过 `server/` 之外的迁移脚本 | 【未知】 |
| `Online` 中文值在不同 `lower_case_table_names`/字符集下的实际存取 | 【待验证】未实际连库验证 |
| `secretKey varchar(320)` 是否被长到溢出 | 【待验证】DES+Base64 输出远小于 320，理论安全 |
| 实际数据库里 `game` 表的数据分布 | 【未读到】仓库未附数据导出 |

---

## 七、一句话总结

> **`gametable.sql` 只有 1 张 11 字段的 `game` 表，把账号、明文密码、会话密钥、在线态、职业、坐标、血量、朝向、等级
> 全部塞在同一行，主键就是账号 —— 因此"一个账号只能有一个角色"，并且整个项目在数据层没有任何 MMORPG 业务表。
> 它对 JSTM 的价值是**反面的**：告诉 JSTM"不要这样设计"。
> 正面的表结构参照请看 `../chivalrousman/database.md`（5 张业务表 + 字段清单）。**
