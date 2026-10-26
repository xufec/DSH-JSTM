# R44：最小账号层 + 审计盲区收口（2026-09-19）

> 依据《各模块复原设计方案》§八 决策 #3（**B 最小 account 表，支持多角色**）与 §九 R44。
> 另按项目方指示**穿插**完成 R43 暴露的"审计盲区"收口。

---

## 一、R44 验收

```
1110(dsh_local): code=1 roles=[(1001, 'DSH', 150, 0, 1, 0)]     ← 既有角色完好
1110(r44_test):  code=1 roles=[]                                 ← 账号隔离
10101 建角#1: code=1 rid=2001 name=R44甲
10101 建角#2: code=1 rid=2002 name=R44乙
1110(r44_test) 再次: roles=[(2001,'R44甲',1,…), (2002,'R44乙',1,…)]  ← **同账号 2 角色**
1110(dsh_local) 复查: roles=[(1001, 'DSH', 150, …)]              ← 无串号
已清理测试角色 [2001, 2002] 与测试账号 r44_test
```

`tools/verify_account.py` → **PASS**（全程用独立测试账号，不写玩家账号数据）。

---

## 二、取证：`CS_1110` 到底带什么

真机 341 抓包中 `1110` 有两种 body：

| 形态 | 次数 | 内容 |
|---|---|---|
| **219 字节** | 822 | `args = {key,val}` **10 对** |
| **12 字节** | 580 | `args` 计数 = 0（空表）+ 残留（我方测试脚本） |

219 字节那 10 对逐条解出：

```
account=dsh_local      timestamp=1789711500   enter_srv_id=''
platform=ewan          device_id=Redmi_rubens(22041211AC)
getui_cid=ca221ee…     idfa=''
token=dsh_token        channelId=1            sign=dsh_signrror
```

**⇒ 三个结论：**

1. **账号标识 = `account`**，且真机 **822 次恒为 `dsh_local`**（补丁客户端的假账号）
   ⇒ 与 `DEFAULT_UID` 完全一致，**玩家角色不会因账号层上线而"变孤儿"**。
2. **协议里没有密码字段** —— 原版走 `token` + `idfa` + `device_id`。
   ⇒ 按决策 #4（**严格不猜**）+ YAGNI：**不做 password 列、不自造密码/鉴权流程**；
   `accounts` 表只有 `(uid, name, create_ts)`。
3. 其余键（token/idfa/channelId/sign…）**协议无对应语义** ⇒ 只记日志里的键名，不据此鉴权。

---

## 三、改动

| 位置 | 原状 | 改后 |
|---|---|---|
| `accounts` 表 | **不存在** | 新增最小表 `(uid TEXT PK, name TEXT, create_ts INTEGER)` |
| `roles.uid` | 列**已存在但恒为 NULL** | `db_init()` 幂等**补登**：`UPDATE roles SET uid='dsh_local' WHERE uid IS NULL` |
| `1110` | 读 `config.json` 的 `roles`，**完全忽略 CS** | 解析 `args` → 取 `account` → **查 DB** 返回该账号角色 |
| `10101` | **桩**：恒回 `code=0 + rid=2001`，**不落库** | **真建角色**：`db_create_role()` 落库、返回新 rid、`code=1` |

**新角色如何初始化（严格不猜）**：复用服务端已有的 `ROLE_DEFAULTS` **模板**
（`lev=1`/`mspd=100`/资产 0…），**不自造数值**；`rid` 从 **2001** 起分配
（1001 是既有首角色）。落库复用 `db_save_role()`（其 `_DB_COLS` **本就含 `uid`**
⇒ 无需新写库路径）。

**账号归属**：`10101` 用同一连接里最近一次 `1110` 决定的 `uid`（`self._uid`），
无则落 `DEFAULT_UID` —— 最小账号层不做会话表，够用即可。

---

## 四、★ 审计盲区收口（R43 暴露的问题）

### 4.1 盲区是什么

| 审计 | 覆盖 | **盲区** |
|---|---|---|
| `audit_sc_live.py` | 默认应答集合（76+25） | **专用 handler** 不在其中 |
| `replay_captures.py` | 真机发过的 233 条 | **真机没发过**的完全测不到 |
| `verify_*.py` | 若干点状功能 | 需人工列举 |

⇒ **"专用 handler + 真机从未发送"** 的命令**无人校验**。
R43 的 `SC_10306` 正是此类：真机 0 次、走专用分支，结果 `attr` 条目结构
与 `10304` 不同却被复用切分 ⇒ **多写 8 字节**，两道审计都放过了。

### 4.2 做法：`tools/audit_dedicated.py`

```
1. 解析 mock_server.py 的专用分发：if cmd == N / if cmd in (…)  → 155 条
2. 过滤出**安全可调**的：CS 字段为空（纯查询）且 SC 不含 code/result/tips（非操作结果）
   → 58 条
3. 逐条发空 CS，按 SC 规格**精确解析**应答
```

**结果**：

```
=== 专用 handler 查询审计（58 条）===
  符合规格 58 / 不符 0 / 无应答 0
```

⇒ R43 修掉 10306 后，**其余专用查询型没有同类结构错位**。

### 4.3 灵敏度自检（证明它真能抓到 10306 那种错）

```
正确(10306 切分, 88B)   len=88  解析消耗=88  PASS
误用(10304 切分, 96B)   len=96  解析消耗=88  MISMATCH -> 消耗 88 != 96
```

⇒ 若 R43 未修，本审计会报 `MISMATCH 10306`。**盲区已闭合**。

---

## 五、全量验证

| 项目 | 结果 |
|---|---|
| `audit_specs_vs_fields.py` | 2463 条：**0 不一致** |
| `audit_sc_conformance.py`（全量 1635） | **0 不一致** |
| `audit_sc_live.py --unsupported` | **93/93** |
| **`audit_dedicated.py`（新）** | **58/58 符合规格** |
| `verify_attr_power.py`（R43） | **PASS**（三处战力一致 / 10306 = 88B） |
| `verify_account.py`（R44） | **PASS**（隔离 / 建角 / 多角色） |
| `test_11215_10800.py` | **PASS** |

---

## 六、产出

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `accounts` 表 + `DEFAULT_UID` + 三个辅助函数；`1110` 改为查账号；`10101` 真建角色 |
| `tools/verify_account.py` | 新增：账号隔离 / 建角 / 多角色 验证（默认清理测试数据） |
| `tools/audit_dedicated.py` | 新增：**专用 handler 查询型审计**（补盲区） |
| `analysis/1.4.9/round44_account.md` | 本报告 |

---

## 七、下一步

按计划 **R45 = 副本/爬塔进度快照真实化**（`13005/13034/13036/13045/13052/13058/21301`
由零值 → 真实进度；新建 `handlers/dungeon.py` 与 `dungeon_progress`/`tower_progress` 表）。

**已具备的条件**：配置资产齐备（`config_dungeon_new/tower/single_tower/golden_tower/reward_desc`）；
且 R44 的**多角色**能力让"两个角色各自独立的副本进度"可验证。

**注意（决策 #4 严格不猜）**：首版只做"**进度快照真实**"，
副本战斗数值沿用既有 `battle.py` 编排并标【占位，待校准】。

**另建议**（成本低、收益明确）：把 `audit_dedicated.py` 纳入每轮收尾清单
（与另两道审计并列），因为它覆盖了"新写专用 handler"最容易犯的错。
