# R117：实现 `17200`（投资天数/状态）+ `16503`（领取信息）—— 缺口第一名落地

> 目标轮次 3/40。`tools/gap_worklist.py` 的**当前第一名是 `17200`（真机 60 次）**，
> 本轮把它与同家族的 `16503` 一起做掉，并建了 `role_invest` 状态表。
> **时间**：2026-09-30 01:35 – 02:00。

---

## 一、投资家族的完整规格（一次看全）

| cmd | CS | SC | 状态 |
|---|---|---|---|
| `16500` | 空 | `{info:table(type,is_active,get_num,can_buy,time,charge_rmb)}` | ✅ R107 |
| `16501` | `{type:u8}` | `{tips,msg,type}` | 动作（购买/激活）|
| `16502` | `{type:u8,val:u16}` | `{tips,msg}` | 动作（加注）|
| **`16503`** | `{type:u8}` | `{type,get_info:table(day_or_lev),can_get_info:table(can_day_or_lev)}` | ✅ **本轮** |
| **`17200`** | 空 | `{day:u32,status:u8}` | ✅ **本轮** |
| `17201` | 空 | `{tips,msg,item_list:table(bid,quantity,bind)}` | 未做（可领奖励，配置为空）|

**客户端 handler**：`invest_ctrl` 的注册表 —— `16500→handle16500`、`16501→handle16501`、
`16502→handle16502`、`16503→handle16503`、**`17200→on17200`**、`17201→on17201`；
`on17200` 把数据经 **`setGiftData`/`setGetedState`** 存起来
⇒ `day` = **投资天数**、`status` = **领取状态**（这是取值的依据）。

---

## 二、配置依据（`config_invest`，R107 解出）

```
InvestType = {2:登录基金, 3:等级基金, 7:豪华投资, 8:至尊投资}
DayInvest  = {7:{1..7}, 8:{1..7}}        ← ★ 「按天数」的里程碑（类型 7/8）
LevDays    = {3:[25,35,45,55,65,75]}     ← ★ 「按等级」的里程碑（类型 3）
```

**新增 `invest_milestones(itype)`**：类型 7/8 取 `DayInvest[type]` 的天数；
类型 3 取 `LevDays[type]` 的等级；**都没有 ⇒ 空（诚实）**。

---

## 三、实现

### 新建 `role_invest(rid, itype, day, geted, updated_at)`

| 列 | 语义 |
|---|---|
| `itype` | 投资档位（2/3/7/8）|
| `day` | 进行到第几天/级 |
| `geted` | 已领里程碑的**位图**（与 `16503` 的"可领"判定一一对应）|

**没有行 ⇒ 没有该档投资**（真话）。

### `17200`

```
day    ← role_invest.day（无行 ⇒ 0）
status ← 0 没有投资 ／ 1 还有可领 ／ 2 已领完（在 `on17200` 的 setGetedState 路径上取值）
```

### `16503`

```
get_info     ← 里程碑中 day/lev <= 当前进度的（**已达成**）
can_get_info ← 其中 `geted` 位图**未置位**的（**还没领**）
```

### 发放途径

`GET /DSH_ADMIN/invest?type=7&day=3&geted=0`（`type=0` 清空）——**没有途径就无法验收**。

---

## 四、实测（五段全通）

```
== 没有投资 ==
  SC_17200 len=5 day=0 status=0                              ✓ 真话
== 没有投资时的 16503{7} ==
  get_info=[] can_get_info=[]  解析=5/5                       ✓
== 发放投资 type=7 day=3 ==
  管理端里程碑=[1,2,3,4,5,6,7]
  SC_17200 day=3 status=1                                     ✓ 有可领
== 有进度后的 16503{7} ==
  get_info=[1,2,3]  can_get_info=[1,2,3]  解析=11/11          ✓ 与配置里程碑(≤3)一致
== 标记首位已领后 ==
  get_info=[1,2,3]  can_get_info=[2,3]                        ✓ 少 1 个
=== 结果: PASS ===
```

★ 判据都用**真实配置/DB**对照（`get_info` 与 `invest_milestones` 的结果逐项比对），
不是"看 `code` 就算过"。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **205** / 默认 47 / 未开放 20）/ 静态审计 PASS / conformance PASS / **SC 在线 67-67** / **专用 78-78** / 门禁 E **PASS**（长度不符 0）|
| 回归（**17 项**） | **新增 `verify_invest.py`** + 前 16 项 **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `role_invest` 表 + `db_invest_init/state/set` + `invest_type_list`/`invest_milestones` + `17200`/`16503` 处理器 + `/DSH_ADMIN/invest`；从 `_GENERIC_DEFAULT_CMDS` 移出 `17200` |
| `tools/_fix_r117_invest.py` | 插入脚本 |
| `tools/verify_invest.py` | **新增回归第 17 项** |
| `server/mock_server.py.bak_r117` | 改前备份 |
| `analysis/_invest_ctrl.txt` | `invest_ctrl` 反汇编（`on17200` 的消费点）|
| `analysis/1.4.9/round117_invest_17200.md` | 本报告 |

---

## 七、进度（对比目标起点）

| 指标 | 起点 | 现在 | 变化 |
|---|---|---|---|
| **只回默认响应的命令** | 59 | **47** | **−12** |
| **未实现且真机发过的系统/命令** | 42 / 82 | **41 / 70** | **−12** |
| **专用分支** | 186 | **205** | **+19** |
| **回归项** | 12 | **17** | **+5** |
| 六道门禁 | — | **全 PASS** | — |

## 八、下一批

| 序 | 目标 | 现成数据 |
|---|---|---|
| 1 | **`16664`（26 次）** | 转盘；`_dial_reward.json` 是档位奖品表（无 `bid` 源）⇒ 需再取证 |
| 2 | **`13200`/`13300`/`13321`（各 25 次）** | 社交域 ⇒ 1 角色，空即真话（已判定不做）|
| 3 | **`13741`（20 次，建筑/庄园）** | `config_manor`(19键) 已解出 ← **优先** |
| 4 | **`13806`（20 次）/ `15204`（20 次）** | 摆摊 / `{num:u8, gold:u8}` |
| 5 | **`15700`（神器）** | `config_shenqi`(7)/`config_partner_shenqi`(9) |
| 6 | 投资的动作侧 `16501`/`16502` | `InvestType`/`cost`（金币价）已解出 |
