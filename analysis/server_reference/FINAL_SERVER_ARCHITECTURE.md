# FINAL SERVER ARCHITECTURE（R4 定稿）

> 依据附件任务书执行。**本文件是 R1→R2→R3→R4 的最终产出。**
> 所有结论分【已确认】【已验证】【待验证】【未知】；**不把 INFERRED 写成 CONFIRMED**。

---

## 〇、最高原则（红线，照抄任务书）

1. **绝世唐门 1.4.9 APK 是最终标准** —— 与参考项目冲突时，**APK > 参考项目**
2. **参考项目只作架构参考** —— 禁止改名复制
3. **优先复用架构思想，谨慎复用代码**
4. **不猜协议** —— 字段必须标级别
5. **只操作自己的服务器**

---

## 一、审计基础（全部实测，非推测）

### 1.1 五个参考项目（`cankao/*.zip`）

| # | 项目 | ZIP | 文件数 | 服务端位置 |
|---|---|---|---|---|
| 1 | **Survive** | 207.7 MB | 2618 | `gameserver/`(16 lua) + `gateserver/` + `groupserver/` |
| 2 | **CXEngine = YZXY / 原罪西游**（★ 用户已确认） | 14.8 MB | 501 | `scripts/{server,combat,share}/` + `server/src/` |
| 3 | **MahatmaComeBack** | 18.2 MB | 164 条目（**136 文件**） | `Server/游戏服务器`(**15**) + `Server/gametable.sql`（R2 逐条目更正，原写 17） |
| 4 | **ChivalrousMan** | 51.2 MB | 1539 条目（**1411 文件**） | **无服务端目录**；服务端在作者另开的 `gitee.com/lsylovews/CM-Server`（不在 ZIP）⚠ 但客户端用 libmysql 直连 MySQL ⇒ **反推出 5 表 / 33 字段业务库结构** |
| 5 | **kongkongxiyou** | 331.8 MB | 22486 | `game-server/app/servers/`(39 js) + `domain/`(48) |

**★★ LICENSE 审计结论（`license_audit.md`）：**
**5 个项目**全部不可复制代码** —— 4 个无 LICENSE，`MahatmaComeBack` 是 **GPL-3.0（传染）**。**
**⇒ JSTM 所有实现必须**自行编写**。**

### 1.2 JSTM 1.4.9 APK（R2 实测）

| 指标 | 数量 |
|---|---|
| **协议定义总数** | **3553** |
| **出现的 CMD 数** | **1652** |
| **服务端已实现** | **83** |
| **真机客户端实际发过** | **128** |
| **真机未应答** | **66**（61 个有 SC ⇒ 该实现；5 个仅 CS ⇒ 无需应答） |

**★ R2 最重要的发现：**
**客户端实际只用了 128 个 CMD（占 1652 的 7.7%）⇒ 不必实现全部协议。**
**⇒ 真正的缺口是那 **61 个有 SC 的未应答命令**。**

**配置资产（已验证）**：347 张配置表 / 3535 物品 / 846 任务 / 134 商城 / 496 礼包

---

## 一之补、★★★ 前提冲突已**裁决**：**JSTM 是回合制战斗**（用户 2026-09-18 确认）

### 冲突内容

**任务书前提**：「JSTM 是**动作/实时**战斗」⇒ 故要求"不能照搬 CXEngine 的**回合制**状态机"。

**但本工作区既有取证结论相反：**

| 证据 | 内容 |
|---|---|
| `analysis/1.4.9/battle/battle_flow.md` §一 | 标题即「**1.4.9 使用「独立回合制战斗场景」，不是地图直接战斗。**」（该文自述只依据 APK 字节码与协议） |
| `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1（**★ 真机订正，权威**） | 真机 `tcp.log` **无 `cmd=20011` / `cmd=20014`**；客户端收到 `SC_20020` 后主动发 `CS_20021` |
| `protocol_index.md` | `20000~20099` 段 **25 条** CMD（20001~20030） |
| ⚠ `battle_chain_verified.md` | **降级：这不是真机取证**，它描述的是**我们自己的 `mock_server.py` 实现**（`行 2445 if cmd == 20014:`）|

**⇒ 结论：JSTM 1.4.9 **也是回合制**。**（该判定依据 `battle_flow.md` §一 与 `20000` 段 CMD 的存在，**不依赖 `20014`**。）

> ### ⚠️ **R6 更正：「回合节奏所有权相反 / ACK 节流」不成立（本节第一版有错）**
>
> **第一版写的是**：JSTM「服务端推 `SC_20012/20013` → 客户端 `CS_20014` ACK 后才推进」⇒ 与 CXEngine「**回合节奏所有权相反**」，照搬会「**丢掉 ACK 节流**」。
> **该表述依据错误**：它引自 `battle_chain_verified.md`，**而那份文档描述的是我们自己的 mock 实现**
> （`行 2445 if cmd == 20014:` —— **我们自己把 20014 当成了推进条件**），**不是真实客户端行为**。
>
> **订正后的正确表述**：
> - JSTM 真机客户端**同样不给"我播完了"的回执** ⇒ **JSTM 也必须由服务端自定节拍**（现实现：`SC_20010` 之后 **2.5 秒/回合、自续期**）；
> - **CXEngine 与 JSTM 在"服务端不等客户端"这一点上相似**（CXEngine：**客户端**自己推；JSTM：**服务端**自己推）⇒ **「所有权相反」不成立**；
> - **「照搬会丢掉 `CS_20014` 节流」作废**（**没有节流可丢**；真机把 `20014` 发都不发）。
>
> 详见 `comparison/battle_matrix.md` §三。

### ★ 但这**不改变**"不能照搬 CXEngine 状态机"的结论 —— 真正原因是 **5 条字段级理由**

| # | 理由 | 证据 |
|---|---|---|
| 1 | **战场结构表达不了一回合** | JSTM `SC_20010` 含**阵法**（`atk/def_formation_type+lev`）与**回合波次**（`round_wave`/`wave_max`/`wave_no`）；CXEngine `BattleMT:Serialize()` 只有 `{id, team_type, pos_id}` |
| 2 | **单位状态每回合全量重推** | JSTM `SC_20013.summon_play[]` 每回合带 `hp_max/hp/anger/is_auto/animate_res[]/skills[]/specials[]`；CXEngine **无重推机制，buff 完全不上线** |
| 3 | **线格式与协议哲学不同** | JSTM `[u32BE len][u16BE cmd][二进制字段序]` vs CXEngine `[LE u32][LE u32][JSON]` |
| 4 | **JSTM 有四套 CXEngine 没有的子系统** | 观战（`20016/20017`）、战斗录像（`20025–20030`）、自动战斗（`20008`）、客户端侧演算校验（`10601/10610`） |
| 5 | **安全模型与内容不可复用** | CXEngine 有状态/重复提交校验但**无归属校验、无限速、无超时**；`assets/doc/*` 数值**全是《梦幻西游》数值** |

**⇒ 因此：CXEngine 的战斗状态机**只有 3 条机制可借**（见下表），**推进权必须留在服务端**，
且 `SC_20012/20013` **必须显式携带伤害 + buff 增/减/剩余回合**。**✅ 好消息：JSTM 本来就有这两样**（见 §九 表）。

### ✅ 裁决结果（用户 2026-09-18 确认）

> **JSTM 是回合制战斗。**

**∴ 任务书原前提「动作/实时」正式修正。本方案与 R3 矩阵已按此更新。**

### ∴ 对战斗架构的直接影响（重要）

**CXEngine/YZXY 也是回合制 ⇒ 它的战斗状态机在**结构上**部分相关，但字段集与系统边界对不上。**

| 可借鉴（**仅机制**） | 不可照搬 |
|---|---|
| ① **按 `CalcSpeed()` 降序**决定回合内出手顺序（服务端算） | CXEngine 由**客户端本地** `NextTurn()` 推进回合 |
| ② **先快照收件人再结算**（防结算中 actor 被移除漏发） | `BattleMT` **双向引用无一致性保护**（`GetNotReadyActors` 写错变量名） |
| ③ **随机数只在服务端摇**，结果随消息下发 | CXEngine **buff 无任何同步协议**（**最大缺陷**）⇒ 但**不要**由此推出"JSTM 需新增 buff 字段" |
| ④ **目标失效自动换目标** + **封禁校验**（buff 影响指令合法性） | —— |
| ⑤ **buff = 静态表 + 按 ID 命名的脚本回调 + 回合统一结算**（骨架） | —— |
| ⑥ `BattleMT` **双端共享**“服务端算结果、客户端只播表现”的**原则** | 其 `Serialize()` 字段太薄，**表达不了 JSTM 的一回合** |
| ⑦ ★ **侠客行的"手动 10 s / 自动 2 s 双档超时托管"** | 侠客行的**客户端本地结算伤害与奖励** |
| ⑧ ★ **空空西游的仇恨表（`increaseHateFor`/`getMostHater`）** | 空空西游的**实时制**（非回合）战斗判定 |

**⇒ ★ JSTM 的 `SC_20012/20013` 必须显式携带：伤害 + 技能播放 + **buff 增/减/剩余回合**。
⚠ **但不保留"`CS_20014` ACK 节流"——真机根本不发它（R6 更正）；改为服务端 2.5 s 自定节拍 + 回合超时兜底（参考侠客行双档）。**

---

## 二、五项目架构要点（R1 实测）

### Survive —— **实时手游多服务组**（README 原文已确认）

```
distri.lua 框架；除 AOI 和 astar 两个模块外，所有游戏逻辑皆用 Lua
gateserver   前端连接/可多台/转发
groupserver  中心/一台/全局逻辑
gameserver   战斗及地图/单线程/每服务加载 1-n 场景
服务端 lua：gameserver gameplayer gate map maplogic areatrigger attr avatar
           battlebag buff bufffunction skill robot snail triggerfunction util
```

### kongkongxiyou —— **Pomelo 分布式**

```
auth/remote          连接入口
connector/handler/   entryHandler + roleHandler
area/handler/        {boss,chat,equip,federate,fight,guild,market,player,
                      resource,shop,skill,task,team}Handler.js   ← 按业务域切
area/remote/         areaRemote + guildRemote + playerRemote     ← 跨进程 RPC
```

### CXEngine (YZXY) —— **C++/Lua + combat 独立**

```
scripts/client/{actor_manager, addon/{action,bag,battle,hud,options,props,quest}, ...}
scripts/server/   scripts/combat/   scripts/share/   server/src/(C++)
```

### MahatmaComeBack / ChivalrousMan

- **Mahatma**：Cocos 客户端 + 独立 `Server/` + `gametable.sql`（**表结构可看，代码不可用**）
- **侠客行**：**实测无服务端** ⇒ 参考价值仅限**客户端侧业务流程**

---

## 二之补二、★★ 两处**自我更正**（子代理 #4 发现，必须记录）

### 更正 1：★ 我在 R1/R3 里对 **Mahatma 的数据库价值判断是错的**

**我原先写的**：「`gametable.sql` 定义了完整表结构 ⇒ 可作为数据库参考」

**实测推翻（子代理核验）**：
```
Server/gametable.sql 全文**仅 1397 字节**，只有 **1 张表 `game`，11 个字段**
字段：account(主键) / password / playerName / secretKey / Online / PlayerType /
      XPoint / YPoint / blood / direction / grade
⇒ **账号表 = 角色表**（主键就是 account）⇒ 一个账号只能有一个角色
⇒ **没有任何业务表**（无物品/装备/技能/任务/邮件/公会/日志）
⇒ 无外键、无索引、无初始 INSERT、无事务（transaction 参数全传 null）、SQL 全字符串拼接
⇒ 连接串硬编码 root/123123
```
**⇒ 任务书「gametable.sql 定义了完整表结构」这一预设**不成立**。
⇒ 它在数据层只能支撑"注册→登录→建号→进场景→走路→聊天→掉线"的最小闭环。**

### 更正 2：★ 真正的数据库参考是 **ChivalrousMan**（我原先把它判为"无服务端 ⇒ 价值有限"）

**子代理反推出它的真实结构（本项目最有价值的资产之一）：**

```
5 张表 / 33 字段：
  player(playername, playerpsw, nums)
  playerinfo(playername, rolename, roletype, glod, grade, blood, mana,
             attack, defense, speed, exp, maxexp, destx, desty, level)
  skillinfo(... skillname, skillgrade)
  equipmentinfo(... equipmentname, grade, type=槽位1005-1009)
  backpack(... thingname, thingtype(1001药品/1002装备/1003技能), thingnums, thinggrade)

建号初值配方：attack100 / blood300 / defense20 / glod300 / grade1 /
             mana150 / speed4 / exp0 / maxExp100 / destx=desty=100 / level1
```

**★ 而且它有真正的**五段式分层**（本审计里最接近"教科书"的分层）：**
```
TCPClient(纯传输) / ShareData.h(23 命令枚举 + 22 定长结构体集中定义)
/ CMClient(switch 分发 + 一消息一函数) / Model.h(实体自描述表名+字段名+序号)
/ DBDao<T>(泛型 DAO) / 5 个按域 Manager(TaskSystem/Skill/Equipment/BackPack/Team)
```

**⇒ 但三条限制（如实）：**
1. **本项目**确实没有服务端代码**（11 条实证：无 `server/`、无 `listen/accept/bind`、
   README 第 9 行明示服务端在 `gitee.com/lsylovews/CM-Server`（**不在 ZIP**））
2. **它的"客户端"直连公网 MySQL**（`Classes/DBDao.h` 硬编码 `47.93.235.6`）
   ⇒ 这是**已泄露凭据**，绝不可复用为配置
3. **无 LICENSE** ⇒ 只借鉴设计
4. **任务两条通道都不走**（定义来自 `Resources/Task/Task<N>.tsk`，状态在内存单例）

### 附带：两项目的分层对照（回答任务书第 7 问）

| | Mahatma | **ChivalrousMan** |
|---|---|---|
| 分层 | **服务端零分离**：`Form1.cs`（497 行 WinForms）同时是网络监听+协议解析+业务分发（190 行 if/else）+SQL+UI | **五段式**（见上） |
| 寻路 | 纯客户端 A\*（TMX `opacity=0` 图层判墙 + 曼哈顿 H）；**服务端零校验** | 8 方向 + **有 `M_VerifyPos`**（但循环条件写错致校验从未生效） |
| 战斗 | — | **逻辑回合制 + 定时器实时调度**；`PlayerAtk_Msg` **不含伤害/血量**，伤害**客户端本地算** |

---

## 二之补、★★★ 空空西游审计的**决定性发现**（子代理 #3）

### 发现 1：该项目**自己已从多进程退回准单体** —— **免费验证了 JSTM 单进程路线**

实测（子代理核验）：
```
6 类进程（connector/area/auth/gate/manager/trade），12 个场景挤在 **1 个 area-server**
chat / path / fight 在 servers.json 中**未部署**
作者留下 handleRemote 适配层，把跨进程调用点**逐个收敛为单进程函数调用**
```
**⇒ 即：参考项目中最"分布式"的那个，**作者本人**也从多进程退回了准单体。**
**⇒ 这**正面支持**本方案第四节的核心判断：JSTM 保持单进程 Python 是**合理**的，不是妥协。**

### 发现 2：★ AOI 的三件套（JSTM 必须自研）

```
① watcher(有视野,range) + object(被看见)  双注册模型
② 4 事件契约  add / remove / update / update_watcher
③ onObjectUpdate 对 oldWatchers/newWatchers 求**双向差集**（<40 行）
   ⇒ 只推增删，开销正比于**视野变化量**而非视野内实体数
配套：getWatcherUids(pos,types,ignoreList) 把 AOI 结果翻成 [{uid,sid}]，**让 AOI 绝不碰 socket**
```

**⚠ 但**算法内核读不到**：`pomelo-aoi` / `pomelo-pathfinding` / `pomelo-bt` **均未随 ZIP 打包**
（全库 22486 文件搜索 0 命中）⇒ **只有"调用契约"，内核必须 JSTM 自研。**
**参考项目的三处缺陷要自己改好**：塔格硬编码 300、**MOB 的 remove 分支被注释**、零埋点。

### 发现 3：★ 寻路的**安全红线**（JSTM 必须补）

```
kongkongxiyou: handler.move 里 `var path = msg`
             ⇒ **直接信任客户端上传的整条路径**
             Map.verifyPath 已定义但**全项目 0 处调用**（子代理脚本核验）
             ⇒ 可穿墙 / 瞬移 / 加速 / 拉怪；且**无移动限流**
```
**⇒ JSTM 若实现寻路，必须补：L1（路径校验 + 起点一致性）+ L2（位移上限/限流）。**
**⇒ 这直接回答了任务书【第十二节】的"移动"环节该怎么做。**

### 发现 4：工程范式四条（Python 平移成本极低）

| 范式 | 说明 |
|---|---|
| **handleRemote 迁移适配层** | 把跨进程调用点逐个收敛为单进程函数调用，重构风险极低 |
| **messageService 唯一出网出口** | + 错误码集中表（`onLogTips`/`onTipsBox` 两档提示） |
| **dataApi → DataTable** | 把数组配置表映射为按 id/字段索引的表（约 30 行） |
| **行为树 + 黑板 + TryAndAdjust** | `Select[try, Sequence[adjust, try]]`（"先试失败则调整再试"），Python 约 100 行可实现 |

### 发现 5：★ 许可红线（子代理全 ZIP 核验）

```
根目录**无任何 LICENSE/COPYING/NOTICE**（排除 node_modules 后 34 个符号许可文件全是第三方自带）
作者 README 只有**口头授权**（"授权大家随便使用…使用和转发需要注明博客地址"）⇒ **非正式许可**
lordofpomelo/LICENSE = NetEase MIT（**只覆盖上游 lordofpomelo/pomelo，不覆盖作者原创业务代码**）
★ pomelo-admin-web/public/ext-4.0.7-gpl/license.txt = **GPL（ExtJS，传染性，严禁引入）**
```
**⇒ 与 `license_audit.md` 判定一致：只借鉴设计，绝不复制代码/数据表/数值/地图碰撞/美术资源。**
**⇒ 建议 JSTM 增加 `THIRD_PARTY_NOTES.md` 留痕；若要 Pomelo 代码只能直接从 NetEase 上游取并保留 MIT 声明。**

---

## 三、R3 映射矩阵（详见 `comparison/architecture_matrix.md`）

**综合评分（16 模块 × 5 项目；0~5 分）—— 节选：**

| 模块 | Survive | YZXY | 大圣 | 侠客行 | 空空西游 | **JSTM 方案** |
|---|---|---|---|---|---|---|
| 网络层 | **5** | 3 | 2 | 1 | 4 | 保留 JSTM TCP |
| Gateway | **5** | 2 | 1 | 0 | **5** | **JSTM 单进程不需要** |
| 角色 | 4 | 4 | 3 | 3 | 4 | 已实现 |
| 场景 | 4 | 3 | 2 | 1 | **5** | 已实现基础 |
| **AOI** | **4** | 3 | 1 | 0 | 4 | ★ **缺** |
| **寻路** | **4** | 3 | 3 | 1 | 4 | ★ **缺** |
| 任务 | 3 | **4** | 3 | **4** | 4 | 已实现 |
| 战斗 | 4 | **4** | 2 | 3 | 4 | 流程通，数值 TEST_ONLY |
| 技能 | 4 | 4 | 3 | 3 | 4 | ★ **缺** |
| 副本 | 4 | 3 | 2 | 2 | 4 | ★ **缺** |
| 数据库 | 3 | 3 | ~~4~~ **1** | **4** | 4 | SQLite（★ 表结构参考 **ChivalrousMan**） |
| **LICENSE 可用性** | **0** | **0** | **0** | **0** | **0** | **全部不可复制** |

---

## 四、★ 终局判断

### 4.1 参考项目能给什么 / 不能给什么

| 能给 | 不能给 |
|---|---|
| ✅ **分层思想**（gate/group/game、connector/area、addon 插件化） | ❌ **代码**（5 个全部无可用许可） |
| ✅ **模块划分**（按业务域切 handler） | ❌ **协议**（各项目有自己的协议，与 JSTM 无关） |
| ✅ **表结构组织**（★ **ChivalrousMan** 5 表 33 字段；Mahatma 只有 1 表） | ❌ **服务形态**（多进程 ≠ JSTM 单进程） |
| ✅ **AOI / 寻路算法思路**（Survive 的 C 模块） | ❌ **回合制战斗**（YZXY 是回合制，JSTM 不是） |

### 4.2 JSTM 的独特资产（本审计最关键的判断）

**参考项目给的是"怎么做服务器"；JSTM 已经有的是"原版客户端要什么"。**

| JSTM 资产 | 状态 | 为何珍贵 |
|---|---|---|
| **1.4.9 原版协议实现（83 个 CMD）** | 【已验证】 | **5 个参考项目都没有** |
| 347 张配置表通用读取器 | 【已验证】 | 可读任意 `.luac` |
| 3535 物品 / 846 任务 / 496 礼包 | 【已验证】 | 原版数据 |
| 10 张 SQLite 表 + 17 个管理动作 | 【已验证】 | 可运营调试 |
| **实机闭环**（登录→地图→任务→战斗→奖励） | 【已验证】 | Vertical Slice 已跑通 |

**⇒ 核心建议：**
**不要因为参考项目是"多进程/C+Lua/MySQL"就去改 JSTM 形态。
JSTM 的形态（单进程 Python + SQLite）对"私服兼容"**已经够用且已验证**。
真正缺的是**功能**（AOI / 寻路 / 技能 / 副本），**不是架构重构**。**

---

## 五、Protocol Adapter 层（任务书第九节）

```
原版 APK ──真实 1.4.9 协议──▶ Protocol Adapter ──▶ JSTM Game Core ──▶ SQLite
                                  │
                 Decode → Command → 业务 → State Change → Encode
```

**现状**：JSTM **已经是**这个形态（`pack_frame` + cmd 分支 + DB）—— **不是从零开始**。
**改造方向（非本轮实施）**：单文件 `if` 链按域拆 handler（借鉴 kongkongxiyou 的 `area/handler/*Handler.js`）。

---

## 六、推荐目录结构（**基于审计调整**）

```
server/
  core/        net/（帧解析，已验证）session/ protocol/（★ Adapter 注册表）
               timer/（心跳 1199）logger/
  logic/       login/ role/ scene/{aoi/★ path/★} task/ battle/
               item/{warehouse/} shop/ partner/ dungeon/★ skill/★ gm/
  persistence/ sqlite/（10 张表）
  config/      347 张表读取器
```

**★ 与任务书建议树的差异（如实）：**
- 任务书建议 `gateway/` ⇒ **JSTM 单进程不需要**，引入是过度设计
- 任务书建议 `cache/` ⇒ SQLite 本地已毫秒级，暂不需要
- 任务书建议 `chat/ social/ friend/ guild/` ⇒ JSTM 尚未涉及，列 P2

---

## 七、最小 Vertical Slice（任务书第十二节）

```
任务 → 移动 → 找 NPC/怪物 → 战斗 → EXP → 升级 → 完成任务 → 奖励 → 下一任务
```

| 环节 | JSTM 状态 |
|---|---|
| 任务列表/接取/提交/奖励/链推进 | ✅ 已验证 |
| 战斗（发怪/结算/掉落） | ⚠️ 流程通，**数值 TEST_ONLY** |
| EXP / 升级 | ✅ 已验证 |
| **移动** | ✅ **实测已通**（真机 `10204` 连续发变化坐标 (119,45)→(121,44)→…→(48,42)）—— 寻路由**客户端自己算**，服务端只接收+保存 |
| **NPC 对话** | ❌ **不通**（`getScene()==nil`，九轮追查未闭环） |

**⇒ Slice **只差"移动"与"NPC 对话"两环** —— 两者都卡在**客户端场景对象**上。**

---

## 八、分阶段计划

| 阶段 | 内容 | 前置 |
|---|---|---|
| **第一阶段（最小可运行）** | ✅ 基本达成：登录/角色/场景/任务/背包/装备/商城/仓库/聚宝盆 | — |
| **第二阶段** | ① 补 **NPC 对话 + 移动**（打通 Slice 最后两环）<br>② 补 **AOI + 寻路**<br>③ 协议层按域拆 handler<br>④ 实现 61 个未应答中优先级高的 | `getScene()==nil` 需先解 |
| **第三阶段** | 技能 / 副本 / 伙伴属性 / 聊天 / 社交 | — |

---

## 九、第十六节 58 问速查

| 问 | 答 |
|---|---|
| 网络层参考谁 | **kongkongxiyou**（分层）+ **Survive**（C 层） |
| Gateway 参考谁 | **kongkongxiyou** / **Survive**（但 **JSTM 单进程不需要**） |
| 角色 / 场景 | 以 **JSTM APK 协议**为准；组织方式参考 Survive / 空空西游 |
| **AOI / 寻路** | **Survive**（唯一直接可学的） |
| 任务 | ★ **R5 更正**：改为 **空空西游 `app/domain/task/*.js`**（`TaskState` 4 态 + `TaskType` 3 类，**已读且与 JSTM `mission_status 0/1/2/3` 1:1 同构**）+ **侠客行 `TaskSystem`**（第二个独立 4 态样本 + 11 个任务模板数值 + 三态对话）。<br>⚠ 原写「CXEngine `addon/quest`」**已作废**：该文件**从未被任何审计读过**（`yzxy/architecture.md:214`、`yzxy/lua_server.md:422` 均记录"未读"），且其"目标类型"维度对应的是 JSTM 的 `progress` 计算方式，**不是** `MissionType`（28 类）。详见 `comparison/task_matrix.md` §八 |
| 战斗 | **CXEngine `scripts/combat`** |
| 背包/装备/技能 | CXEngine `addon/*` / Survive `skill.lua` |
| 数据库 | ~~Mahatma~~ ⇒ ★ **更正为 ChivalrousMan**（Mahatma 只有 1 张 11 字段表） |
| Lua/C++ | **Survive（distri.lua）** |
| **哪些代码可合法复用** | **无（5 个全部无可用许可）** |
| **哪些只能参考** | **全部 5 个** |
| JSTM 真实协议放哪层 | **Protocol Adapter 层**（与 Game Core 解耦） |
| 现有服务端哪些保留 | **全部保留**（协议实现是最大资产） |
| 哪些需重构 | CMD 分发 `if` 长链 ⇒ 按域拆 handler |
| 哪些需重新实现 | **AOI / 寻路**（完全没有） |
| 最终目录结构 | 见第六节 |
| 第一阶段最小版 | 已基本达成 |
| 第二阶段/第三阶段 | 见第八节 |

---

## 十、【未知】与风险

| 项 | 状态 |
|---|---|
| `getScene() == nil` 根因 | 【未知】—— 静态已到尽头，**需真机调用栈** |
| CMD 段完整定性（13000/13300/13500） | 【未知】—— 大段未定性 |
| 战力 / 技能公式 | 【未知】—— 未找到权威公式 |
| 怪物战斗数值 | **APK 里不存在**（已验证）⇒ **不可校准** |
| 礼包内容（如 30010） | 【未知】—— **不在客户端 3 张礼包表内** ⇒ 服务端逻辑 |
| 聚宝盆 `drop_id=17000` 指向 | 【未知】—— 不在 `config_drop`（34 组） |
| ~~任务书前提与取证冲突~~ | ✅ **已裁决**：**JSTM 是回合制战斗**（用户 2026-09-18 确认） |
| 五项目**逐文件**审计 | ⏳ **R1 补全中**（4 子代理并行：Survive / YZXY / 空空西游 / Mahatma+侠客行） |

---

## 十一、约束遵守声明

```
✅ R1~R4 全程**只做审计**：读 ZIP、读 APK、分析、写报告
✅ **未修改** mock_server.py / APK / 任务系统 / 登录 / 角色 / 地图
✅ **未实现**任何新功能
```

# [WAITING FOR IMPLEMENTATION APPROVAL]
