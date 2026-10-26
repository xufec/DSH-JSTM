# R45 验证：副本/爬塔进度 + 两处修补（2026-09-19）

> 本轮定位：**验证方**。副本/爬塔骨架由并行会话实现（见 `round44_dungeon_tower.md`），
> 我按 R43/R44 建立的纪律**逐条核对权威规格、验证"进度真的来自 DB"**，
> 并由验证过程暴露出**两处需要修补的问题**。

---

## 一、★ 7 条命令的规格核对（逐字节）

权威规格取自 `cmd_resolve_130.luac` / `cmd_resolve_213.luac` 的 AutoConstruct，
与实现逐字段比对并**在线精确解析**：

| 命令 | 权威规格 | 应答长度 | 结果 |
|---|---|---|---|
| `13005` | `bid:I flag:C left_times:I` | 9 | **PASS** |
| `13034` | `dung_bid:I CengList:T{ceng:C count:H can_get:C is_get:C}` | 21 | **PASS** |
| `13036` | `key:C value:C` | — | **不回包**（见 §二） |
| `13045` | `floor:I rid:I srv_id:s name:s fast_rid:I fast_srv_id:s fast_name:s first_get:C` | 21 | **PASS** |
| `13052` | `select_hard:C section:C hard:C challenge:C left_times:C assets:T{assets_code:C num:I}` | 7 | **PASS** |
| `13058` | `cur_score:I get_score:I max_wave:C gain:T{type:C count:I} AwardBidList:T{Bid:I}` | 13 | **PASS** |
| `21301` | `tower_id:I floor:I is_effect:I clear_list:T{…7字段} is_clear:C daily_floors:C` | 16 | **PASS** |

⇒ **6/7 编码与权威规格完全一致**；空表一律写 `w_u16(0)` 计数（不编无效 bid，符合红线）。

---

## 二、★ 修补 1：`13036` 重发风暴的**根因**（此前只观测到现象）

### 2.1 现象（原始抓包）

```
13036 共出现 1448 次，其中一个 body 重复 1420 次：
  00009c41 04 00 | 02 09 a0 00
  └ dung_bid=40001 └ key=4 └ value=0 └ 4 字节缓冲区残留
```

### 2.2 根因（反汇编客户端 `demontower_ctrl.luac`）

`handle_13036`（proto#14）的逻辑：

```lua
if resp.key == 0 then self:openView() end                    -- ★ 打开镇魂塔界面
if resp.key == 1 then … self.view:setSelected(item_list[resp.value]) … end
if resp.key == 2 then … （另一选中形态）… end
if resp.key == 3 then self:closeView() end
message(…)                                                    -- 提示
```

**`key = 4` 没有任何分支。**

⇒ 服务端原先把 `13036` 归入**通用零值应答集合** ⇒ 回 `key=0, value=0`
⇒ 客户端**每次都执行 `openView()`** ⇒ 界面重开又触发一次 `send_13036` ⇒ **自激循环**。

### 2.3 统计证据（服务端日志按小时分桶）

| 时段 | `13036` 次数 | 说明 |
|---|---|---|
| **14 时** | **22434** | 通用零值回包期 —— **风暴** |
| 15 时 | **8** | 改为"不回包"后 |

**↓ 99.96%**。根因与数据完全吻合。

### 2.4 结论与后续正确做法

- **当前"不回包"是正确且必要的**（客户端发一次即走）。
- ⚠ **后续若要做完整实现，正确的应答是"回显请求里的 `key`/`value`"**，
  **绝不能回 `key=0`** —— 那等于命令客户端打开界面。
  `key=4` 无分支 ⇒ 回显它天然安全。
- ⇒ 该结论已写进代码注释，避免后人"顺手补个默认应答"再踩一次。

---

## 三、★ 修补 2：`10102` 忽略 `rid` ⇒ 第二个角色"进不去"

### 3.1 怎么发现的

R45 的验证要求"两个角色各有独立进度"。测试脚本给临时角色 2001 落库 `tower_floor=7`，
**重新登录该角色后 `21301` 仍返回 `floor=1`** ⇒ 说明查询读的不是这个角色的数据。

### 3.2 根因

```python
def role_state(cfg):
    st = dict(ROLE_DEFAULTS); st.update(cfg.get('role', {}) or {})
    rid = st.get('rid', 1001)          # ← 角色号来自 cfg['role']，与连接无关
```

而 `TcpHandler.cfg` 是**类属性**（`TcpHandler.cfg = cfg`，全连接共享），
且 `10102`（选角登录）**完全忽略 CS 的 `rid`**：

```python
if cmd in (10102, 10103):
    body = (w_u8(1) + w_str('') + w_u32(time) + w_u16(world_lev))   # rid 没用上
```

⇒ **R44 建出来的第二个角色"能列、能建、进不去"**：选它登录后，
所有 handler 仍读配置角色 1001 的数据 —— 轻则数据错乱，重则改到别的角色身上。

### 3.3 修法（最小且安全）

在 `10102/10103` 里按 CS 的 `rid` **切换本连接的角色**：

1. **只接受「存在于 `roles` 表」且（已知账号时）「属于本账号」的 rid**
   —— 否则任意 rid 会触发 `role_state()` 的种子建行逻辑；
2. 通过 `self.cfg = cfg副本` 建立**实例级** cfg
   —— `TcpHandler.cfg` 是类属性，**实例赋值只影响本连接**，不会串号；
3. 非法 rid 记日志并**保持原角色**（不静默换人）。

**对玩家零影响**：玩家登录的角色就是配置角色 1001，`rid == _cur` ⇒ 直接跳过整段逻辑。

---

## 四、验证结果

```
== 规格一致性（玩家角色）==
  SC_13005  len=9     PASS      SC_13045  len=21   PASS
  SC_13034  len=21    PASS      SC_13052  len=7    PASS
  SC_13036  无应答 —— 期望如此   SC_13058  len=13   PASS
  SC_21301  len=16    PASS

== 进度落库真实性（测试角色）==
  测试角色(2001) floor=7 ｜ 玩家角色(1001) floor=1
   ✓ 进度来自 DB（写了 7 就读到 7）      ✓ 多角色隔离
```

`tools/verify_dungeon.py` → **PASS**（玩家角色全程只读；测试数据结束即清理）。

### ★ 反向测试（`10102` 安全性）

改了登录选角就必须证明它**不会被滥用**。`tools/verify_role_switch_guard.py`：

```
初始 roles: [1001]
  请求 rid=99999 后 whoami = 1001   ✓ 未切换、未建行
  请求别人的 rid=3001 后 whoami = 1001   ✓ 拒绝越权（仍是自己的角色）
  正常登录 rid=1001 后 whoami = 1001   ✓ 正常路径无变化
```

三条性质都成立：
① 请求**不存在**的 rid ⇒ 不切换且**不在 `roles` 表建行**（不会因任意 rid 造脏数据）；
② 请求**属于别的账号**的 rid ⇒ **拒绝**（不越权看/改别人角色）；
③ 玩家自己的 rid ⇒ 与改动前完全一致（`rid == _cur` 直接跳过整段逻辑）。


**全量套件（改动后复跑）**

| 项目 | 结果 |
|---|---|
| `audit_specs_vs_fields.py` | 2463 条：**0 不一致** |
| `audit_sc_conformance.py`（全量 1635） | **0 不一致** |
| `audit_sc_live.py --unsupported` | **93/93** |
| `audit_dedicated.py` | **58/58** |
| `verify_attr_power.py`（R43） | **PASS** |
| `verify_account.py`（R44） | **PASS** |
| `verify_dungeon.py`（R45） | **PASS** |
| `test_11215_10800.py` | **PASS** |

---

## 五、产出

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `10102/10103` 按 CS `rid` 切换本连接角色（含归属校验 + 实例级 cfg） |
| `tools/verify_dungeon.py` | 新增：7 条规格核对 + 进度落库真实性 + 多角色隔离（自带清理） |
| `tools/verify_role_switch_guard.py` | 新增：`10102` 反向测试（非法 rid 不切换/不建行、拒绝越权） |
| `analysis/1.4.9/round45_dungeon_verify.md` | 本报告 |

---

## 六、下一步

按计划 **R46 = 副本"进入 / 结算"打通**（复用 `battle.py` 编排，数值标【占位，待校准】）。

**R45 遗留的两点建议**：

1. **`13036` 的完整实现**：确定它到底该"回显"还是"不回包"之后再做；
   在此之前**不要**给它加默认应答（会立刻复现 22434 次/时的风暴）。
2. **角色切换的纵深**：本轮只让 `role_state()` 走对角色；但**启动时的
   `cfg['role']` 播种、`pack_push`/AOI 的全局状态、`Ticker` 周期任务**是否也按连接隔离，
   尚未逐一核对。多角色长期并存前，建议做一次"全局共享状态"盘点。
