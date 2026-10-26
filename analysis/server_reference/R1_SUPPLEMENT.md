# R1 补全：五项目**逐文件类/函数级**审计汇总

> 任务书第五节要求"逐文件记录 类/函数 → 工作机制 → 是否适合 JSTM"。
> **本轮由 4 个并行审计子代理完成，合计 52 个文件、1,165 KB。**
> 所有结论标【已确认】【待验证】【未知】；**未读到的一律写"未读到"，无编造。**

---

## 一、产出清单（**全部实测**）

| 项目 | 文件 | 合计 |
|---|---|---|
| **Survive** | architecture / network / role / scene / battle / database / reuse_candidates | ~256 KB |
| **YZXY / CXEngine** | architecture / protocol / lua_server / role / battle / reuse_candidates | ~205 KB |
| **kongkongxiyou** | architecture / pomelo / scene / aoi / pathfinding / reuse_candidates | ~208 KB |
| **MahatmaComeBack** | architecture / network / database / role / reuse_candidates | ~118 KB |
| **ChivalrousMan** | architecture / task / battle / database / reuse_candidates | ~245 KB |

**发现数量**：Survive **26 个头等设计点 + 23 处已确认缺陷**；
YZXY **12 条借鉴点 + 大量反例**；空空西游 **37 条设计思想**；Mahatma/侠客行 各一套。

---

## 二、★★★ 本轮三处**自我更正**（任务书要求"被否证的假设要保留记录"）

### 更正 1：任务书前提「JSTM 是动作/实时战斗」**与取证相反**

| 证据 | 内容 |
|---|---|
| `battle_flow.md` §一 | 「**1.4.9 使用「独立回合制战斗场景」**」 |
| `analysis/1.4.9/battle/battle_protocol_matrix.md` §3.0/§3.1（**真机订正，权威**） | 真机 `tcp.log` **无 `cmd=20011` / `cmd=20014`**；客户端收到 `SC_20020` 后主动发 `CS_20021` |

**⇒ JSTM **也是回合制**。**

> ### ⚠️ **R6 更正：本节第一版的「ACK 节流」表述已作废**
>
> **第一版写的是**：「CXEngine 客户端本地 `NextTurn()`（无 ACK）；JSTM **服务端 `SC_20012/20013` → 客户端 `CS_20014` ACK 后才推进**」，
> 因而「**回合节奏所有权相反**」。
> **该表述依据错误**：它引自 `battle_chain_verified.md`，而那份文档描述的**是我们自己 `mock_server.py` 的实现**
> （`行 2445 if cmd == 20014:`），**不是真实客户端行为**。
>
> **订正后**：
> - JSTM 真机客户端**同样不给"我播完了"的回执** ⇒ **JSTM 也必须由服务端自定节拍**（`SC_20010` 后 2.5 秒/回合、自续期）；
> - **两者都是"服务端不等客户端"** ⇒ **「所有权相反」不成立**；「照搬会丢掉 `CS_20014` 节流」**作废**（无节流可丢）；
> - **CXEngine 回合 FSM 仍不可照搬，但真正理由是 5 条字段级理由**（阵法/波次、单位每回合重推、线格式、四套独有子系统、安全模型）；
> - **「JSTM 是回合制」这一判定不受影响**（不依赖 `20014`）。
>
> 详见 `comparison/battle_matrix.md` §三 与 `comparison/architecture_matrix.md` §三/§四 第 7~9 行。

### 更正 2：★ 我对 **Mahatma 数据库价值**的判断是错的

**原判**：`gametable.sql` 定义完整表结构 ⇒ 可作数据库参考
**实测**：全文**仅 1397 字节，只有 1 张表 `game`、11 字段**；**账号表 = 角色表**（主键 `account`）；
**没有任何业务表**；无外键/索引/事务；连接串硬编码 `root/123123`
**⇒ 任务书「gametable.sql 定义了完整表结构」的预设**不成立**。**

### 更正 3：★ **ChivalrousMan 才是真正的数据库 + 分层参考**

**反推出的 5 张表 / 33 字段**：
```
player(playername, playerpsw, nums)
playerinfo(playername, rolename, roletype, glod, grade, blood, mana,
           attack, defense, speed, exp, maxexp, destx, desty, level)
skillinfo / equipmentinfo(type=槽位1005-1009) / backpack(thingtype 1001药品/1002装备/1003技能)
建号初值：attack100 / blood300 / defense20 / glod300 / grade1 / mana150 /
         speed4 / exp0 / maxExp100 / destx=desty=100 / level1
```
**且它有本审计里最"教科书"的**五段式分层**：**
```
TCPClient(纯传输) / ShareData.h(23命令+22定长结构体) / CMClient(switch分发+一消息一函数)
/ Model.h(实体自描述) / DBDao<T>(泛型DAO) / 5 个按域 Manager
```
**⚠ 三条限制**：① 它的服务端在 `gitee.com/lsylovews/CM-Server`（**不在 ZIP**）
② 客户端直连公网 MySQL，**凭据已泄露**（绝非可复用配置） ③ **无 LICENSE**

---

## 三、★★★ LICENSE 最终结论（**关键模块明确 copyleft**）

| 项目 | LICENSE | 结论 |
|---|---|---|
| **Survive** | 无顶层，但 **`aoi.h`/`astar.h`/`wordfilter.h` 文件头内嵌 GPLv3** | 🔴 **核心模块明确传染** ⇒ **连"翻译成 Python"都有风险** |
| **YZXY / CXEngine** | 无（501 条目零命中） | ⚠️ 只借鉴设计 |
| **MahatmaComeBack** | **GNU GPL v3** | 🔴 **代码绝对不得进入 JSTM** |
| **ChivalrousMan** | 无 | ⚠️ 只借鉴设计 |
| **kongkongxiyou** | 无（`pomelo-admin-web/.../ext-4.0.7-gpl` = **GPL ExtJS，严禁引入**） | ⚠️ 只借鉴设计 |

**⇒ 最终结论：5 个项目的**核心模块全部不可复制**。**
**⇒ Survive 的 AOI/寻路**连翻译都受限** —— 只能读"设计思想"，**实现必须完全自写**。**

---

## 四、★ 三家**最有价值的可借鉴点**（已落点）

### 4.1 Survive —— **AOI / 寻路 / 移动同步**（JSTM 完全缺失的三块）

| # | 借鉴什么 | 拿到 JSTM 变成什么 |
|---|---|---|
| **D11** | **AOI**：均匀网格 + 每对象视野集合去重 + 新旧集合差（enter/unchange/leave）+ **双向 enter_see/leave_see 回调** | JSTM `scene/aoi/` 自写（**不可复制 GPL 代码**） |
| **D12** | **寻路**：A\* 8 邻域 + **Bresenham 直线裁剪 `lineto`（遇障碍即停，用于击退/位移/追踪点）** | JSTM `scene/path/` 自写 |
| **D13/D14** | **移动同步三件套**：客户端**只发目标点** → 服务端算路径后**只广播"速度+目标点"**（**不播路径**）→ 服务端用 **100ms + `movmargin` 时间预算自己也走**；**进视野/重连要补发移动与 Buff** | ★ **直接对应 JSTM 目前"移动未闭环"** |
| **D8/D9/D10** | **属性**：只持久化**输入项**（前 23 项），派生属性**每次登录 `CalAttr` 全量重算**；`attr2view={level,life,maxlife}` 白名单只同步 3 个；换装返回 `"recalattr"` 信号 | JSTM `role_attr` 若存了派生值应改掉 |
| **D2** | **`cmd → handler` 注册表** | 正是 R4 建议 JSTM 从 `if` 链改成 `HANDLERS[cmd]` 的形态 |
| **D15/D17/D18/D25** | 掉线交 AI 托管；凑够就开+超时也开+原子入场；发奖先校验后落地；AI=协程+三态状态机 | 后续阶段 |

**⚠ 明确不可借鉴**：多进程三件套形态、它的协议、redis 字符串拼接持久化、name2idx 无键数组、
位打包、**它的所有数值**（伤害系数/战力/塔防系数都是编的）、地图 `.meta` 格式与世界尺度。
**⚠ 致命缺陷**：**Survive 战斗层零距离/角度/目标数/能量校验**（客户端给目标列表，服务端只滤队友+死人）
⇒ **照抄等于开放全图秒杀。**

### 4.2 kongkongxiyou —— **场景骨架 + 工程范式**

| # | 借鉴什么 | 关键数据 |
|---|---|---|
| **A** | **AOI 三件套**：watcher+object 双注册 → 4 事件契约 → `onObjectUpdate` **双向差集**（开销正比于**视野变化量**） | 配套 `getWatcherUids(pos,types,ignoreList)` 让 **AOI 绝不碰 socket** |
| **B** | **场景五层**：`AreaManager→Scene/InstancePool→Instance→Area` + **100ms 主 tick / 1s(含刷怪) / 3s 分频** + `actionManager` 把行走建模为**可中断 singleton Action** + `instanceId` 命名即共享域 | **完全不依赖 Pomelo，Python 平移成本极低** |
| **C** | **工程范式**：`handleRemote` **迁移适配层** + `messageService` 唯一出网出口 + `dataApi→DataTable` + handler 前置守卫 filter + 行为树 `TryAndAdjust = Select[try, Sequence[adjust, try]]` | — |

**★ 决定性验证**：**该项目自己已从多进程退回准单体**（6 类进程 → 12 场景挤 1 个 area-server；
chat/path/fight 未部署；作者留 `handleRemote` 把跨进程调用收敛为单进程函数调用）
**⇒ **等于免费验证了 JSTM 单进程路线可行**。**

**🔴 安全红线（JSTM 必须补）**：`handler.move` **直接信任客户端整条路径**；
`Map.verifyPath` 已定义但**全项目 0 处调用** ⇒ 可穿墙/瞬移/加速/拉怪。
**⇒ JSTM 必须补 L1（路径校验+起点一致性）+ L2（位移上限/限流）。**

### 4.3 YZXY / CXEngine —— **单一真源 + 代码生成**

| # | 借鉴什么 |
|---|---|
| **①⭐** | **TSV/表单一真源 → 生成多端定义**：`actor_template.tsv`(含 `sync` 列) → 生成 `EActorProp` 枚举 → 运行期读**同一张表**注册；`assert(index == m_Props.size())` 把"表行序==枚举值==数组下标"**锁死** |
| **②⭐** | **`stub[PTO_XXX]` 零样板分发 + 两阶段收包**（握手期立即答，其余入队由主 tick 派发） → 落地：`HANDLERS[cmd]` 注册表 |
| **③⭐** | C++ 提供原语、Lua 承载**全部**游戏逻辑 + `IsServer()/IsClient()` 同码分叉 |
| **④⭐** | **随机数只在服务端摇，结果随消息下发，客户端照结果播** |
| **⑤⭐** | 技能/buff = **静态表 + 按 ID 命名的脚本回调** |

**★ 落地建议**：以 `protocol/fields.json`(3553 条) **为唯一真源生成 `jstm/proto_defs.py`**，
供 mock_server / 测试脚本 / 抓包解码器共用，**CI 校验"生成物 == 仓库内文件"**。

**★ 反例清单（可作"明确不做"）**：`DOSTRING` 系列 = **服务端远程执行客户端 Lua（后门）**；
handler 用请求体 `req.pid` 决定回包对象（**可冒领**）；账号密码明文 JSON；
`PTO_S2C_SYNC_PROPS` **全服广播无 AOI**；`ActorMT:AddSummon` 无条件 `uids_str='[]'`（**只可能有 1 只召唤兽**）；
`GetAttackDamage(...,false,false,0,1)` **暴击/连击从未生效**；逃跑判定 `or true` **恒真**。

### 4.4 ChivalrousMan —— **五段式分层 + 5 张表**（见更正 3）

**⚠ 客户端本地算伤害**（`attack<=defense?1:attack-defense`），`PlayerAtk_Msg` **不含伤害/血量字段**
⇒ **服务端无权威结算** —— JSTM **不可照此**（我们的战斗必须服务端算）。

### 4.5 Mahatma —— **仅 1 张表，价值有限**

**唯一可借鉴**：`DbConnectionMySQL` 的**门面 API 形状**（统一 DB 访问入口 + 事务作为一等公民暴露）。
**反面教材**：`Form1.cs`（497 行 WinForms）**同时**是网络监听 + 协议解析 + 业务分发（190 行 if/else）+ SQL + UI。

---

## 五、★ 汇总：JSTM 该怎么做（本 R1 补全的**行动结论**）

### 5.1 必做（按优先级）

| # | 事项 | 来源 |
|---|---|---|
| **1** | **协议层重构**：`if cmd == …` 长链 → `HANDLERS[cmd]` 注册表 | Survive D2 + 空空西游 + YZXY ② |
| **2** | **补 AOI**（JSTM 完全没有）—— 自写：均匀网格 + 视野集合去重 + 新旧差集 + 双向回调 | 三家共识（Survive/空空西游） |
| **3** | **补寻路 + 移动同步**：客户端发目标点 → 服务端算路径 → **只广播"速度+目标点"** → 100ms 自走 | Survive D13/D14 |
| **4** | **移动安全**：L1 路径校验 + 起点一致性；L2 位移上限/限流 | 空空西游红线（`verifyPath` 0 调用） |
| **5** | **属性只存输入项**，派生每次重算；`attr2view` 白名单 | Survive D8/D9/D10 |
| **6** | **单一真源 + 代码生成**：`fields.json` → `proto_defs.py` | YZXY ① |

### 5.2 明确不做

- ❌ **不改成多进程**（连空空西游作者都退回了准单体）
- ❌ **不引入 Pomelo/Node.js**（JSTM 是 Python 单进程）
- ❌ **不照抄任何项目的协议**（APK > 参考项目）
- ❌ **不照抄 Survive 的战斗校验缺失**（会开放全图秒杀）
- ❌ **不照抄 ChivalrousMan 的客户端算伤害**
- ❌ **不复制任何代码**（含 Survive AOI/astar 的 GPL 头）

---

## 六、仍未做 / 未读到（如实）

| 项 | 说明 |
|---|---|
| **R3 映射矩阵的逐项细化** | 现有 `comparison/architecture_matrix.md` 已含 128 个真实 CMD，但**未把子代理的具体设计点逐条映射进去** |
| **`comparison/` 其余 6 个矩阵** | `protocol_matrix` / `role_matrix` / `task_matrix` / `battle_matrix` / `scene_matrix` / `database_matrix` / `license_matrix` **未单独出文件**（内容已散在各项目报告里） |
| **`jstm/` 的 8 个模型文档** | `protocol_map` / `role_model` / `scene_model` / `task_model` / `battle_model` / `item_model` / `skill_model` / `gm_model` **未出**（R2 的 15 份协议文档已覆盖大部分） |
| **未读到的参考源码** | 各子代理已列：`internals/cxlua`、`distrilua` C 源码、`pomelo-aoi/pathfinding/bt` 插件（**ZIP 内不存在**）、`CM-Server`（**不在 ZIP**）、`php/`、`client/` 渲染层 |
| **真机调用栈** | `getScene()==nil` 仍需真机栈 |

---

## 七、约束遵守声明（任务书红线）

```
✅ 4 个子代理**全程只读**：Python zipfile 按需读取，未解压、未改 cankao/ 与 server/
✅ 主 agent 本轮**未修改** mock_server.py / APK / 任务系统 / 登录 / 角色 / 地图
✅ 未实现任何新功能
✅ 已核验 cankao/ 下 5 个 zip 时间戳未变
```
