# 数据库矩阵（R4）—— 五参考项目 × JSTM 持久化对照

> **本文档闭环 `R1_SUPPLEMENT.md` §六 的未做项 ①「`comparison/database_matrix.md` 未单独出文件」。**
> 依据：各项目**逐文件一手报告** + **JSTM 服务端实际 SQLite schema（`server/mock_server.py` 逐行实测）**。
> 标注：【已确认】/【待验证】/【未知】；未读到的一律写「未读到」。
> **本文件只读，未修改 `server/` 任何文件**（JSTM 侧数据均为阅读所得）。
>
> ⚠ **时效声明（重要）**：本文 JSTM 侧的**行号**取自**本次读取时的 `mock_server.py` 快照**；
> 该文件当时正被其他 agent 活跃开发（同批次观测到 `mock_server.py` 22:09、`aoi.py` 22:09、`pathfind.py` 22:13 均有写入）。
> ⇒ **行号可能漂移，引用时请以"表名 / 函数名 / SQL 原文"为准做二次定位**；
> **结论级事实（11 张表、98 列、`?` 全参数化、`INSERT OR IGNORE + UPDATE` 手写 UPSERT、`1110` 读 `config.json` 的 `roles`）不受行号漂移影响**。

---

## 一、结论速览（6 方对照）

| 维度 | **Survive** | **YZXY / CXEngine** | **大圣归来 Mahatma** | **侠客行 ChivalrousMan** | **空空西游 kongkongxiyou** | **JSTM 现状** |
|---|---|---|---|---|---|---|
| 存储引擎 | **redis / ssdb**（Redis 文本协议） | **无 DB**：明文 JSON 文件 | **MySQL 8.0.16** | **MySQL** | **MySQL**（+pomelo-sync 插件） | **SQLite**（`server/state/roles.db`） |
| 表/键数量 | 1 个角色 = **1 个 hash / 9 field**；键空间 8 类 | `actor.data` + `account.data` **2 个文件** | **1 张表 / 11 字段** | **5 张表 / 33 字段** | `config/schema/Pomelo.sql`（18.8 KB，**未逐字段核对**）+ DAO 30 文件 | **11 张表 / 98 列**（实测） |
| 账号↔角色 | `<actname>`→chaid 独立键；`nickname` 独立键 | 单文件含全服 actor | **1:1（账号即主键）** | **1:N**（`player.nums` 计数，上限 3） | `userDao.getPlayersByUid` ⇒ **1:N** | ⚠ **roles.uid 是 TEXT 但无账号表**（见 §五 G1） |
| 事务 | ❌ **无**（靠单条 `hmset` 凑原子） | ❌ 无 | ❌ **无**（`transaction` 参数恒 `null`） | ❌ **无**（DBDao 无事务 API） | ⚠ 有 DAO 层，**事务情况未核对** | ✅ **有**（`con.commit()` / `db_release()` 回滚未提交事务） |
| 参数化 | ❌ **字符串拼接**（昵称含空格即破坏命令） | N/A | ❌ 字符串拼接（`params` 恒 `null`） | ❌ 字符串拼接 | ⚠ 走 DAO，**未核对** | ✅ **全部 `?` 占位**（实测 11 表全部参数化） |
| 脏标记 / 定时刷 | ✅ `dbchange` 脏标记**操作即写**（异步，不检查返回值） | ❌ 全量重写文件 | ❌ 每格 3 条 UPDATE | ⚠ 操作即写，且**存档用 INSERT 导致数据膨胀** | ✅ **`dao/mapping/*Sync.js` + pomelo-sync 定时脏刷**（插件未打包） | ⚠ 操作即写（同步 `commit`），**无脏标记/无定时刷** |
| 明文密码 | 忽略密码（gate 不校验） | ⛔ **明文存 JSON** | ⛔ **明文列 + 明文比对** | ⛔ **明文列 + 明文比对** | ⚠ token 机制（`secret` 可 -1 永不过期） | ⚠ **无密码字段、无校验**（见 G1） |
| 客户端可触发写库 | ✅ 是（gate 直连 DB 只读 `<actname>`） | ⛔ **是**（`PTO_C2C_SAVE_ACTORS`） | ⛔ **是**（客户端直连 MySQL 写全部业务） | ⛔ **是**（客户端 libmysql 直连） | ❌ 否（DAO 在服务端） | ❌ 否（客户端只走 TCP） |
| LICENSE | 无顶层；`aoi.h/astar.h` **内嵌 GPLv3** | 无 | 🔴 **GPL-3.0** | 无 | 无（`ext-4.0.7-gpl` = GPL ExtJS） | — |

**⇒ 一句话**：**5 个参考项目里没有一个是「服务端权威 + 事务 + 参数化」的正面样本**，
其中 **4 个（Survive / Mahatma / 侠客行 / YZXY）明确反例**；**JSTM 现有 SQLite 实现已在范式上优于全部 5 个参考项目**，
真正缺的是**表/域的覆盖广度**（§五）与**存档策略**（脏标记 + 定时刷，§四）。

---

## 二、JSTM 现状（★ 逐行实测，`server/mock_server.py`）

### 2.1 11 张表全表（【已确认】，行号为 `mock_server.py` 实际行号）

| # | 表名 | 主键 | 列（原文顺序） | 列数 | 定义位置 |
|---|---|---|---|---|---|
| 1 | `roles` | `rid` | `rid, uid, name, level, career, sex, exp, hp, max_hp, mp, max_mp, gold, gold_acc, diamond, coin, scene_id, x, y, dir, vip_level, title, status, updated_at` | **23** | `:1554-1560` |
| 2 | `role_attr` | `rid` | `rid, strength, intellect, armor, constiution, atk_s, atk_p, def_s, def_p, hp_max, atk_speed, hit, dodge, crit, tenacity, red_def_s, red_def_p, atk_abs, def_abs, reduce, hurt, hit_rate_show, dodge_rate_show, crit_rate_show, tenacity_rate_show, updated_at` | **26** | `:1562-1571` |
| 3 | `missions` | `(rid, mission_bid)` | `rid, mission_bid, mission_status, process_status, target, target_value, value, commit_num, loop_count, loop_num, code, accept_time, updated_at` | **13** | `:1573-1579` |
| 4 | `role_assets` | `(rid, name)` | `rid, name, amount` | **3** | `:1581-1583` |
| 5 | `mall_bought` | `(rid, goods_id)` | `rid, goods_id, num, updated_at` | **4** | `:1585-1587` |
| 6 | `bag_items` | `(rid, bag_code, item_id)` | `rid, bag_code, item_id, bid, pos, quantity, ctime` | **7** | `:2943-2946` |
| 7 | `bag_volume` | `(rid, bag_code)` | `rid, bag_code, volume` | **3** | `:3149-3152` |
| 8 | `equip_items` | `(rid, slot)` | `rid, slot, item_id, bid, hero_bid, ctime` | **6** | `:3200-3203` |
| 9 | `store_items` | `(rid, bag_code, item_id)` | `rid, bag_code, item_id, bid, pos, quantity, ctime` | **7** | `:3297-3300` |
| 10 | `levgift_got` | `(rid, days)` | `rid, days, ctime` | **3** | `:3377-3379` |
| 11 | `sign_got` | `(rid, days)` | `rid, days, ctime` | **3** | `:3468-3469` |
| | **合计** | | | **98 列** | |

**连接与释放策略（【已确认】，JSTM 已有内容）**：
| 机制 | 实现 | 位置 | 评价 |
|---|---|---|---|
| 线程本地连接 | `_DB_LOCAL = threading.local()`；`db_conn()` 取/建本线程连接 | `:1526-1536` | ✅ 服务端多线程（`ThreadingHTTPServer` + `ThreadingTCPServer`）⇒ **每线程一个连接**正确 |
| `row_factory` 复位 | `con.row_factory = None` 每次交付时复位 | `:1535` | ✅ **防上一个调用者的 `sqlite3.Row` 泄漏给下一个**，是很细心的处理 |
| 事务回滚 | `db_release()` 里 `if c.in_transaction: c.rollback()` | `:1539-1548` | ✅ **异常中途退出不留脏事务** |
| 性能依据 | 注释记录：`cProfile` 显示一次 `SC_12400` 里 `sqlite3.connect` 被调 **6 次**、占该请求 **37%** 耗时 | `:1515-1524` | ✅ **有实测数据驱动的优化**，值得保留该注释 |

### 2.2 ★ 配置态 vs 数据库态的分界（**这是最关键的一张表**）

JSTM 当前的持久化切分（【已确认】，`server/config.json` 实测）：

| 域 | JSTM 存在哪 | 证据 | 是否落 DB |
|---|---|---|---|
| 角色基础属性 | `roles` 表 | `_DB_COLS` (`:1508-1511`) | ✅ |
| 角色派生属性 | `role_attr` 表 | `:1562-1571` | ✅ |
| 任务进度 | `missions` 表 | `:1573-1579` | ✅ |
| 通用资产（金币/钻石/魂币…） | `role_assets` 表（`name`→`amount`） | `:1581-1583` | ✅ |
| 商城购买记录 | `mall_bought` 表 | `:1585-1587` | ✅ |
| 背包 / 仓库 / 装备 | `bag_items` / `store_items` / `equip_items` | `:2943` / `:3297` / `:3200` | ✅ |
| 背包容量 | `bag_volume` 表 | `:3149` | ✅ |
| 等级礼包 / 签到 | `levgift_got` / `sign_got` 表 | `:3377` / `:3468` | ✅ |
| **角色列表（登录用）** | ⚠ **`config.json` 的 `roles` 数组** | `1110` 处理读 `self.cfg.get('roles', [])`（`:3919`）；`config.json` 有 `"roles":[{rid:1001,...}]` | ❌ **不查 `roles` 表** |
| **角色当前数值快照** | ⚠ **`config.json` 的 `role` 对象**（`lev/gold/exp/spouse_name/guild_contrib/…` 22 字段） | `config.json` `"role":{...}` | ❌ |
| **技能** | ⚠ **`config.json` 的 `skills` 数组**（`[{bid,exp}×3]`） | `config.json`；`skills_note` 记录了 1001→10000 的修正 | ❌ **无 skills 表** |
| **伙伴** | ⚠ `config.json` 的 `heros` / `hero_chips` / `partner_bag` | 均为 `[]` | ❌ **无伙伴表** |
| **公会 / 称号 / 配偶** | ⚠ `config.json` 的 `guild_name` / `title` / `per_name` / `spouse_name` | `config.json` | ❌ |
| 签到/在线/摇钱树/聚宝盆/黑市/日常 | ⚠ `config.json` 各字段（`sign_*`/`online_*`/`moneytree_*`/`jubaopen_*`/`black_market_*`/`richang_*`） | `config.json` | ❌ **只有 `sign_got`/`levgift_got` 落了表，其余在配置** |
| 场景/NPC/怪物摆位 | `config.json` 的 `npcs`(25) / `mons`(1) / `spawn` | `config.json` | ❌（**配置态，符合预期**） |
| 角色位置快照（人类可读） | `state/role_<rid>.json` = `{rid,x,y,saved_at}` | `:2389` `_role_state_path()` | ⚠ **兼容快照，非权威** |

**★ 关于 `role_<rid>.json` 的正确结论（避免误判）**：
`save_role_pos()` 的 docstring 明确写着
「把坐标写进 **数据库**（Phase 4E 起以 DB 为准）。仍保留 `role_<rid>.json` 作为**可读快照**，便于人工核对。」
（`mock_server.py:2399-2401`）⇒ **这是有意为之的只读快照，不是双写不一致**，无需整改【已确认】。

### 2.3 ★ 写入模式（【已确认】，`db_save_role` / `db_save_attr`）

JSTM 的实际写库模式是**手写 UPSERT + 列名白名单 + 成败检查**，这是本审计中**最值得记录的一处正向设计**：

```python
# mock_server.py:2084-2101（审计引用）
def db_save_role(rid, **kw):
    """按字段增量保存（INSERT OR IGNORE 建行 → UPDATE 指定字段）。"""
    ...
    con.execute('INSERT OR IGNORE INTO roles (rid) VALUES (?)', (rid,))
    kw['updated_at'] = int(time.time())
    cols = [c for c in kw if c in _DB_COLS]          # ★ 列名白名单
    if cols:
        con.execute('UPDATE roles SET %s WHERE rid=?' %
                    ','.join('%s=?' % c for c in cols),   # 值全参数化
                    [kw[c] for c in cols] + [rid])
    con.commit()
    db_release(con)
    return True
```

| 设计点 | 机制 | 为什么这是对的 | 对照的反例 |
|---|---|---|---|
| **手写 UPSERT** | `INSERT OR IGNORE ... (rid)` → `UPDATE ... WHERE rid=?` | 既保证行存在、又只写变化字段；**等价于"UPSERT 但不会覆盖未提交字段"** | 侠客行 `saveBackpackInfo` 直接 `INSERT` ⇒ **每次存档新增全量副本、数据膨胀** |
| **列名白名单** | `cols = [c for c in kw if c in _DB_COLS]` | 动态拼接列名**必须**过滤，否则是注入口；JSTM 已过滤 | Survive / 大圣 / 侠客行全部**直接拼字符串** |
| **值全参数化** | `','.join('%s=?' % c)` + `[kw[c] for c in cols] + [rid]` | **列名走白名单、值走 `?`** ⇒ 两手都干净 | 同上 |
| **`updated_at` 自动维护** | `kw['updated_at'] = int(time.time())` 在过滤前注入 | 每行写入都带时间戳（**G5 的一半已做到**） | Survive **完全没有**时间戳 |
| **成败可查** | `return True` / `except` 里 `log(...)` 后 `return False` | **写失败不被静默忽略** | Survive `CommandAsync` 无回调、不看返回值 |
| **单事务** | `INSERT` 与 `UPDATE` 之间无 `commit`，末尾统一 `con.commit()`；Python `sqlite3` 在 DML 前隐式开启事务 | 两条语句在**同一隐式事务**内 ⇒ 原子 | 大圣 / 侠客行**无事务**，建号中途失败即不一致 |

**⇒ 结论**：**JSTM 的写库实现已在范式上超过全部 5 个参考项目**；
G6（脏标记/定时刷）要补的是**调用频率**（"何时写"），而**不是**"怎么写"。

---

## 三、五项目的存储模型（逐项对照）

### 3.1 Survive —— redis hash，一角色 9 field

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `common/db.lua` | `connect_to_redis` | `Sche.Spawn` 死循环重试 + 断线回调自动重连 | ✅ 适合（思想） | 「DB 不可用时重试而非崩」通用；JSTM 用 SQLite 无网络断线，但**重试/降级**语义可保留 |
| `common/db.lua` | `CommandAsync` | 所有写操作异步、**不检查返回值** | ❌ 不适合 | 🔴 **写失败被静默忽略**（存档悄悄丢失）⇒ JSTM 的 `commit()` 必须检查 |
| `groupserver/attr.lua` | `DbStr()` | `for i=1,attr_db_save do t[i]=attr[i] end; cjson.encode(t)` —— **只存前 23 项输入属性，派生属性不落库** | ✅✅ **高度适合** | ★ **JSTM `role_attr` 存的 26 列里含大量派生项**（`hp_max/atk_abs/def_abs/reduce/hurt/*_rate_show`）⇒ **应区分"输入项"与"派生项"**，见 §五 G4 |
| `groupserver/attr.lua` | `DbSave()` | `if dbchange then hmset …; dbchange=false end` | ✅ ✅ 适合 | ★ **脏标记去重**；JSTM 当前是"操作即 commit"，缺此机制 |
| `groupserver/everydaytask.lua` | `DbSave()` | **每次 `OnEvent` 都写库**（把 DB 当计数器用） | ❌ 不适合 | 高频事件打爆 DB；JSTM 应"内存累积 + 定时 flush" |
| `groupserver/mail.lua` | `DbStr()` | `CBase64.encode(Cjson.encode(list))` | ❌ 不适合 | 因把结构化数据塞进 redis 文本协议而用 base64 兜底 ⇒ **JSTM 用 SQLite 表天然不需要** |
| `groupserver/friends.lua` | `DbSave()` | 用 `self.owner.chaid` 而 `Init` 设的是 `self.ply` ⇒ `nil` | ❌ 坏 | 好友**既不读也不写**（`PlayerLogin` 的 `hmget` 无 `friends`）⇒ 反面教材 |
| `gameserver/*` | 全部 | **无任何 DB 调用** | ✅ 适合（架构） | ★ **"场景进程无状态"**是好设计（JSTM 单进程无此问题，但**场景数据不应直连 DB**的原则可保留） |

**Survive 键空间（8 类，【已确认】）**：`deploy`(hash,部署表) / `<actname>`(string,账号→chaid) / `nickname`(hash,昵称占用) / `chaid`(counter,自增) / `chaid:<id>`(hash,角色全数据) / `MachineStatus`(hash,运维) / `deployment`(string) / ~~旧方案键（已注释）~~。

### 3.2 YZXY / CXEngine —— 无数据库，明文 JSON 文件

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `scripts/server/actor_system.lua` | `actors_on_save` | `assets/storage/actor.data` = `cjson.encode(GetProperties())`，**0 基索引 → JSON 键 `"0".."N"`** | ❌ **不适合** | 🔴 **表结构 = 数组下标** ⇒ 加/删属性即错位；**无原子写**（直接覆盖，无 tmp+rename）⇒ 崩溃即存档损坏 |
| `scripts/server/server.lua` | `PTO_C2C_SAVE_ACCOUNT_DATABASE` / `PTO_C2C_SAVE_ACTORS` | **客户端触发**服务端全量写盘；账号密码**明文**入 JSON | ❌ **不适合** | ⛔ 客户端可刷 IO / 竞态覆盖 / 明文密码 |
| `scripts/share/utils.lua` | `utils_next_uid(ns)` | `os.time()%0xFFFFFFFF` 起 + 内存自增，**不持久化** | ❌ 不适合 | 同秒重启可能重号 ⇒ JSTM 已用 SQLite `INTEGER PRIMARY KEY`（rowid 自增），**优于它** |
| `scripts/server/team_system.lua` | `TeamMT` | 对象表 + `PROP_TEAM_ID` 反查；**队伍纯内存，重启即散** | ⚠ 部分 | 「对象表 + 单属性反向索引」建模干净；**不持久化是缺陷**，JSTM 若做队伍需落表 |

### 3.3 大圣归来 Mahatma —— MySQL 单表

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Server/gametable.sql` | `game` 表 | **1 张表 11 字段**：`account(PK)/password/playerName/secretKey/Online/PlayerType/XPoint/YPoint/blood/direction/grade` | ❌ 不适合 | 🔴 **账号表 = 角色表**（主键即账号）⇒ 一账号一角色；无任何业务表；`Online` 用中文 `是/否` 且**从不被查询** |
| `Server/游戏服务器/DbConnectionMySQL.cs` | `DbConnectionMySQL` 门面 | 4 个 `ExecuteNonQuery` 重载（含 **MySqlTransaction** 重载）、`GetDataSet`、`ExecuteScalar`×2、参数缓存 | ⚠ 部分适合 | ★ **门面 API 形状**（事务作为一等公民暴露）可借鉴为"JSTM 自查清单"；但调用方**全部传 `null`** ⇒ 能力被浪费 |
| `Server/游戏服务器/Form1.cs` | `type=="position"` | 每走一格 **3 条 UPDATE**（X/Y/direction），无事务 | ❌ **不适合** | 🔴 JSTM 应"内存态 + 定时/下线落库" |
| `Server/游戏服务器/Form1.cs` | `type=="loginGameScene"` | 同一 `secretKey` 跑 **7 条独立 SELECT** | ❌ 不适合 | N+1 查询；JSTM 已是一次多列 SELECT |
| `Server/gametable.sql` | 无 `roleId` | 子表不存在，无从谈代理键 | ❌ | 见 §五 G2 |

### 3.4 侠客行 ChivalrousMan —— MySQL 5 表（★ 本审计唯一的正面表结构样本）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/Model.h` | `GamePlayer` → 表 `player` | `(playername, playerpsw, nums)` —— **账号表 + 角色计数列** | ✅ 适合（结构） | ★ **`nums` 是"角色数上限 3"的计数实现**；JSTM 建议用 `COUNT(*)` 校验而非计数列 |
| `Classes/Model.h` | `PlayerInfo` → 表 `playerinfo` | **15 字段**：`playername, rolename, roletype, glod, grade, blood, mana, attack, defense, speed, exp, maxexp, destx, desty, level` | ✅ **适合（字段语义）** | ★ 已支撑 JSTM 角色表设计；注意 `level` 实为**地图号**（命名误导） |
| `Classes/Model.h` | `SkillInfo` → 表 `skillinfo` | `(playername, rolename, skillname, skillgrade)` | ✅ 适合 | 一行一技能；JSTM **目前没有技能表**（见 G3） |
| `Classes/Model.h` | `EquipmentInfo` → 表 `equipmentinfo` | `(playername, rolename, equipmentname, grade, type)`，`type` = **槽位 1005~1009** | ✅ 适合 | ★ **用 `type` 表达槽位**；JSTM 的 `equip_items.slot` 思路一致（更规范） |
| `Classes/Model.h` | `BackPack` → 表 `backpack` | `(playername, rolename, thingname, thingtype, thingnums, thinggrade)`；**一张表容纳 药品 1001 / 装备 1002 / 技能书 1003** | ✅ 适合（统一容器） | ★ **"统一容器 + 类型字段"** vs JSTM 的 `bag_items`+`equip_items` 分表 —— 两种取舍都成立 |
| `Classes/DBDao.h` | `DBDao<T>::saveXxxInfo` | **用 `insertModel()`（INSERT）而非 UPSERT** | ❌ **不适合** | 🔴 **每次存档新增全量副本** ⇒ 背包/装备/技能数据膨胀 |
| `Classes/DBDao.h` | `queryModel/generateWhere` | `m_sql += var.first + "='" + var.second + "'"` 字符串拼接；`queryModel` 未 `mysql_free_result` | ❌ 不适合 | 注入面 + 结果集泄漏 |
| `Classes/DBDao.h` | `DBDao()` 默认构造 | `m_host("47.93.235.6")` / `m_passwd("3252918599lsy")` 明文硬编码，**客户端直连公网 MySQL** | ❌ **不适合** | ⛔ 已泄露凭据；**绝不是可复用配置** |

**建号初值配方（【已确认】，可直接用于 JSTM 数值校准）**：
`attack 100 / blood 300 / defense 20 / glod 300 / grade 1 / mana 150 / speed 4 / exp 0 / maxExp 100 / destx=desty=100 / level 1`

### 3.5 空空西游 kongkongxiyou —— MySQL + DAO + 定时脏刷

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `lordofpomelo/app.js` | `app.use(sync, {path: dao/mapping, dbclient})` | 挂 pomelo-sync-plugin：**内存对象 + 脏标记 + 定时批量 UPDATE** | ✅✅ **强适合（思想）** | ★ ★ **这是 5 个项目里最值得照搬的存档策略**：JSTM 目前无脏标记、无定时刷 |
| `app/dao/**`（30 文件）+ `dao/mapping/*Sync.js`（7 文件） | `userDao`(14.9 KB 最大) / `taskDao` / `guildDao` … | DAO 层 + **mapping 声明"哪些字段需要定时落库"** | ✅ 强适合（结构） | ★ 「DAO 分层 + 落库字段白名单」值得照搬**结构**；**SQL 与表结构不可复制** |
| `app/dao/mysql/{mysql,dao-pool}.js` | `init(app)` | 连接池 + 查询封装 | ✅ 思想适合 | Python 侧对应 `sqlite3` 线程本地连接（JSTM 已做） |
| `config/schema/Pomelo.sql`（18.8 KB） | — | 空空西游自己的数据模型 | ⚠ **未逐字段核对** | ⚠ 与《绝世唐门》1.4.9 数据模型不同 ⇒ **只能读方法，不能抄结构** |
| `app/domain/playerBank.js` + `dao/playerBankDao.js` | — | 钱庄/银行 | ✅ 适合 | JSTM **无银行域**（见 G7） |
| `common/service/channelService.js` | `restoreChannel` / `addToStore` / `loadAllFromStore` | 频道状态持久化（跨进程恢复） | ❌ 不需要 | 单进程下频道就是 `dict[str, set]`，无需持久化 |
| `config/servers.json` 等 | `authRemote.auth(token)` | `tokenService.parse(token, secret)` + `checkExpire`（`expire<0` 视为永不过期） | ⚠ 部分适合 | ★ **极简 token 模型的形状可用**；⚠ `expire = -1` 永不过期**不可取** |

---

## 四、★★ 逐域映射：JSTM 表 ← 参考项目给了什么

| JSTM 域（现有表） | 最相关的参考项目 | **可借鉴** | **必须避免** |
|---|---|---|---|
| `roles`（角色主表） | 侠客行 `playerinfo` | 15 字段语义 + 建号初值配方；入参命名 `destx/desty`（下线点） | 大圣的"账号即角色"；YZXY 的"数组下标存属性" |
| `role_attr`（属性表） | Survive `attr.lua` | ★ **只存输入项、派生项每次重算**；脏标记 `dbchange` | JSTM 当前 26 列含大量派生项（G4） |
| `missions`（任务进度） | 侠客行 `TaskSystem` + 大圣（无） | ★ 四态状态机字段语义（`mission_status`/`process_status` 与 `NS_*` 对应）；`target/target_value/value` 与 `curschedule/allschedule` 对应 | 侠客行的"客户端随机生成 + 不落库"；大圣的"任务无表" |
| `role_assets`（通用资产） | — **5 个项目均无此抽象** | ★ **JSTM 自创的正向设计**：`(rid,name,amount)` 让"奖励配置驱动"成为可能 | Survive 把资产塞进 `chainfo` 的 23 项数组 |
| `bag_items` / `store_items` | 侠客行 `backpack`；Survive `bag.lua` | 数量增减需**原子**（`SET n=n+Δ`）；`bag_code` 区分囊位（JSTM 已有） | 侠客行 `removeBackPackThing` 的 erase-then-deref UB；`saveBackpackInfo` 的 INSERT 膨胀 |
| `equip_items` | 侠客行 `equipmentinfo` | 槽位即主键的一部分（`PRIMARY KEY(rid,slot)` ⇒ **同槽互斥由 DB 保证**，优于侠客行的应用层遍历） | 侠客行 `EquipmentManager` 的 `list` 线性查槽 + 换装把等级写成 1 |
| `bag_volume` | — 5 个项目均无 | ★ JSTM 自创：容量独立成表 | Survive 容量存在 `bag` JSON 的 `size` 键里 |
| `mall_bought` | — 5 个项目均无 | ★ JSTM 自创：`(rid,goods_id,num)` 支撑 `has_buy_num` | — |
| `levgift_got` / `sign_got` | — 5 个项目均无（Survive 有 `everydaysign` 但存 JSON） | ★ JSTM 自创的"幂等领取标记表"（`(rid,days)` 主键 ⇒ **天然防重复领取**） | Survive `everydaysign` 存 `{count,lastreset,lastsign}` JSON（**可重复领的坑**） |
| — **无对应表** | 侠客行 `skillinfo` | **技能表可直接照其 4 字段扩展** | YZXY 把技能存进 actor JSON 数组 |
| — **无对应表** | 空空西游 `playerBankDao` | 银行/钱庄表 | — |
| 存档策略（跨全表） | **空空西游 `pomelo-sync`** + Survive `dbchange` | ★ ★ **内存脏标记 + 定时批量落库** | 大圣的"每格 3 条 UPDATE"；侠客行的"INSERT 全量" |

---

## 五、★★★ JSTM 数据库缺口表（对照 5 个项目后得出，按优先级）

| # | 缺口 | 现状证据 | 参考依据 | 建议 | 优先级 |
|---|---|---|---|---|---|
| **G1** | **无账号 / 会话表，且 `1110` 不查库、不校验密码** | `1110` 处理：`roles = self.cfg.get('roles', [])`（`:3919`）⇒ 角色列表来自 **`config.json`**；全文件**无 `password`/`token` 字段与校验**（`grep password\|token` 仅命中注释与日志文案）；11 张表**无 account/user 表** | 空空西游 `authRemote.auth`（token+expire）；Survive `<actname>`→chaid 独立键 | 新增 `accounts(uid, account, pass_hash, salt, created_at)` + `sessions(token, uid, expire_at, ip)`；`1110` 改查 `roles WHERE uid=?` | **P0** |
| ~~G2~~ | ~~`roles.rid` 无独立自增语义保证~~ | **✅ 本轮已核查：不成立，无需整改**。全部 3 处 INSERT **都显式绑定 `rid`**：`INSERT OR IGNORE INTO roles (rid, level) VALUES (?,?)`（`:914`）、`INSERT OR IGNORE INTO role_attr (rid) VALUES (?)`（`:2056`）、`INSERT OR IGNORE INTO roles (rid) VALUES (?)`（`:2089`） | — | 见 §2.3 的写入模式说明 | **已闭合** |
| **G1b** | `1110` 的角色列表**不查 `roles` 表**（见 G1），导致 `roles` 表可能存在但登录不读 | `1110` ⇒ `self.cfg.get('roles', [])`（`:3919`）；`config.json` 亦有 `roles` 数组 | 侠客行 `SelectLayer` 用 `SELECT * FROM playerinfo WHERE playername=?` | `1110` 改为 `SELECT rid, name, level, career, sex, status FROM roles WHERE uid=?` | **P0** |
| **G3** | **无 `skills` 表**（技能未持久化） | `config.json` 的 `"skills":[{bid,exp}]`；11 表中无 skills | 侠客行 `skillinfo`（4 字段） | 建 `role_skills(rid, skill_bid, level, exp, ctime)`；`mapping` 参考侠客行"一行一技能" | **P1** |
| **G4** | `role_attr` 的 26 列**输入项与派生项混存**，且只覆盖属性总表的一小部分 | `role_attr` 含 `hp_max/atk_abs/def_abs/reduce/hurt/*_rate_show`（派生）与 `strength/intellect/armor/constiution`（输入）；**★ R7 量化补充：属性系统 `AttrLen = 64`（`analysis/1.4.9/level/_attr.json`），而 `role_attr` 只有 25 个属性列 ⇒ 落库 25/64、39 个未落库；其中 21 个属"不该落库的派生项"** | ★ Survive `attr_db_save=23` + 登录 `CalAttr` 全量重算 | **拆表**：`role_attr_base` 只存输入项；派生项不落库、登录/变更时全量重算。详见 `role_matrix.md` §五 G1 | **P0**（R7 由 P1 升为 P0） |
| **G5** | 无 `updated_at` 一致性 / 无 `data_version` | `roles/role_attr/missions/mall_bought` 有 `updated_at`；**`role_assets`/`bag_volume`/`levgift_got`/`sign_got` 没有**；全库无 `schema_version` | Survive **完全没有**（反例）；JSTM 已部分做到 | 统一补 `updated_at`；加 `meta(schema_version, data_version, updated_at)` 支持迁移与回档 | **P1** |
| **G6** | **无脏标记 / 无定时批量落库** | 全部为"操作即 `commit()`"（11 表逐处 `con.commit()`） | ★ ★ 空空西游 `pomelo-sync` + Survive `dbchange` | 引入 `dirty_registry: dict[(table,key), None]` + 每 N 秒 flush；高频域（任务进度、资产）优先 | **P1** |
| **G7** | 无社交域表（好友/队伍/公会/邮件） | 11 表无相关；`config.json` 的 `guild_name` 为空串 | 空空西游 `guildDao`；侠客行组队 8 条消息（**无表**）；YZXY 队伍纯内存（反例） | 按需建 `friends` / `team` / `team_member` / `guild` / `guild_member` / `mail` | P2 |
| **G8** | 无伙伴域表 | `config.json` 的 `heros: []` / `partner_bag: []` | — 5 个项目均弱 | `jstm_1.4.9/partner_protocol.md` 已存在 ⇒ 表可随后端实现补 | P2 |
| **G9** | 无审计 / 运营表 | 11 表均无日志类；`levelup`/`mall`/`jubaopen` 等只有结果态 | 空空西游 `onlineUser` 注册 + 管理台 | `gm_log(ts, uid, rid, cmd, detail)`、`item_log`、`currency_log` | P2 |
| **G10** | 无副本/战斗态表 | `jstm_1.4.9/dungeon_protocol.md` / `battle_protocol.md` 已存在；11 表无副本 | — | 副本进度表 + 战斗快照（若需断线续战） | P2 |

**⇒ 缺口优先级含义**：**G1（鉴权）与 G2（主键一致性）是"正确性"问题，必须先做**；
**G4/G6 是"防腐化/防性能"问题**；G3/G5/G7~G10 是"覆盖广度"问题。

---

## 六、★ 五项目数据库反例清单（JSTM 明确不要学的 15 条）

| # | 反例 | 来源 | 后果 |
|---|---|---|---|
| 1 | 账号表 = 角色表（账号即主键） | 大圣 `game` 表 | 一账号一角色、无法多区服 |
| 2 | 属性用**数组下标**存 | YZXY `actor.data`；Survive `chainfo` | 调整字段顺序 ⇒ 所有老存档错位 |
| 3 | 明文密码入库 | 大圣、侠客行、YZXY | 拖库即全泄露 |
| 4 | 客户端可触发/直接写库 | 侠客行（libmysql 直连）、YZXY（`PTO_C2C_SAVE_ACTORS`）、大圣（`position` 每格写） | 数据可任意伪造 |
| 5 | 存档用 INSERT 而非 UPSERT | 侠客行 `saveBackpackInfo`/`saveEquipmentInfo`/`saveSkillInfo` | 数据膨胀、重复累加 |
| 6 | 无事务 + 自增 id 无回滚 | Survive `incr chaid` 与 `hmset` 分离 | "有 id 无角色"孤儿 |
| 7 | 字符串拼接 SQL/命令（无参数化） | Survive、大圣、侠客行 | 注入；昵称含空格直接破坏命令 |
| 8 | 异步写不检查返回值 | Survive `CommandAsync` | **写失败被静默忽略** |
| 9 | 用 base64 包 JSON 存邮件 | Survive `mail.lua` | 膨胀 33%、不可读、不可查询 |
| 10 | 全量重写文件、无原子写（无 tmp+rename） | YZXY `actors_on_save` | 崩溃即存档损坏 |
| 11 | 存档含**瞬时战斗态** | YZXY（`PROP_COMBAT_BATTLE_ID`/`PROP_TURN_READY`） | 读档后带着战斗标记 |
| 12 | 存档含**全服 NPC** | YZXY `actors_on_save` 遍历 `fetch_all_actors()` | 把 NPC 当玩家存档 |
| 13 | 关键字段缺失即要求"重新创角" | Survive `if not result[1..5] then NotifyCreate()` | 存档部分损坏 ⇒ 玩家卡死在创角 |
| 14 | 昵称占用键**只写不删** | Survive `nickname` hash | 昵称永久占用，无改名/回收 |
| 15 | 完全无 `updated_at` / `schema_version` | Survive（全缺）、JSTM（部分缺） | 无法做增量备份、无法迁移表结构 |

---

## 七、【待验证】/【未知】

| 项 | 状态 |
|---|---|
| ~~G2 是否真实存在~~ | ✅ **已闭合 →【已确认】不成立**：`roles`/`role_attr` 的全部 3 处 INSERT 均显式绑定 `rid`（`:914` / `:2056` / `:2089`），且采用 `INSERT OR IGNORE + UPDATE` 手写 UPSERT；SQLite `INTEGER PRIMARY KEY` 的 rowid-alias 风险**未被触发**。详见 §2.3 |
| ~~JSTM 是否所有 INSERT 都带 `rid`~~ | ✅ 同上 |
| 空空西游 `config/schema/Pomelo.sql`（18.8 KB）的逐字段内容 | 【未读到】仅知文件存在，未核对 |
| 空空西游 DAO 层是否使用事务 | 【未读到】`app/dao/**` 30 文件只作签名级阅读 |
| YZXY `account.data` 的字段结构 | 【未读到】只确认其为明文 JSON 存档 |
| Survive `php/`（1267 文件）里的 DB 操作 | 【未读到】 |
| 大圣 `Form1.resx` 是否存在被注释掉的业务入口 | 【未知】 |
| JSTM `role_assets.name` 的取值域（是否为 `AssetsEnToCode` 的资产名） | 【待验证】`config.json` 的 `shop_pay_type_asset` 表提供了 40 个资产名映射，但未与 `role_assets` 实际行比对 |
| JSTM `missions.code` 的语义 | 【待验证】与 `mission_status`/`process_status` 的职责划分未在本文核对 |
| JSTM 其余 8 张表（`bag_items`/`store_items`/`equip_items`/`bag_volume`/`mall_bought`/`levgift_got`/`sign_got`/`role_assets`）是否也都显式带主键列 | 【待验证】本轮只逐条核对了 `roles` / `role_attr` 两表（因它们是 `rid INTEGER PRIMARY KEY`，风险最高）；其余表主键为**复合主键**（如 `(rid,bag_code,item_id)`），**不带 `rid` 会直接违反 NOT NULL 语义/插入失败**，风险等级低 |

---

## 八、一句话结论

> **JSTM 现有的 11 表 / 98 列 SQLite 实现，在"事务 + 参数化 + 线程本地连接 + `row_factory` 复位 + 手写 UPSERT + 列名白名单 + 成败检查"这七点上，是 5 个参考项目里最好的**
> （Survive 无事务/拼接命令/异步写不看返回值、大圣无事务/7 次 SELECT、侠客行无事务/INSERT 膨胀、YZXY 无 DB、空空西游未核对）。
> **本轮还闭合了一个我原先标为 P0 的怀疑**：`roles`/`role_attr` 的 rowid-alias 主键一致性风险 ——
> **实测 3 处 INSERT 全部显式绑定 `rid`，风险不成立**（§2.3）。
>
> **⇒ 不需要"换数据库"。真正要做的只剩两件**：
> 1. **补 G1 / G1b（账号与会话）** —— 这是唯一的 P0 正确性缺口：`1110` 的角色列表来自 `config.json` 而非 `roles` 表，且全库无密码/票据字段与校验；
> 2. **补 G4 / G6（输入项与派生项分离 + 脏标记/定时刷）** —— 这是存档策略的升级，唯一正面样本是**空空西游的 `pomelo-sync`** 与 **Survive 的 `dbchange`**，
>    两者都**只能学思想、不能抄代码**（无许可 / 内嵌 GPLv3 GPL）。
>
> **表结构层面的唯一正面样本是侠客行的 5 张业务表**（账号-角色分表 + 15 字段角色表 + 槽位型装备表 + 统一容器背包表 + 一行一技能表），
> 但它的**存档实现（INSERT 全量）与访问路径（客户端 libmysql 直连）是明确反例** ——
> **JSTM 应"抄它的字段语义、不抄它的写入方式"**。
