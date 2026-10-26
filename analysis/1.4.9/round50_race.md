# R50：P0-2 五条「未开放」命令分诊 —— 魂师大赛（竞速）真实化

> 承接 `docs/PLAN_下一阶段实施方案与校验设计.md` §4 **P0-2**。
> 对象（真机 22:12 会话实测请求次数）：`17501`×6、`17312`×3、`18600`×3、`11400`×3、`17301`×1。
> **时间**：2026-09-29 10:10 – 10:25。

---

## 一、分诊结论（逐条）

| CMD | 权威名 / 归属 | 处置 | 依据 |
|---|---|---|---|
| **`17301`** | 魂师大赛主状态（`race_ctrl` proto#14 `on17301`） | ✅ **改为 DB 驱动真实值** | 见 §二 |
| **`17309`** | 魂师大赛排行榜（`race_ctrl` proto#? `setDuanList`） | ✅ **改为真实 `rank_list`** | 见 §三 |
| **`17501`** | 宗门战入口（`guildwars_ctrl.handle17501`） | ⚠️ **保留诚实回失败，但改为回显 CS 的 `type`** | 见 §四 |
| `17312` | 竞速操作型（`{code,msg}`） | ⏸ **维持"未开放"** | 无 `type` 语义取证，回成功=撒谎 |
| `18600` | 跨服（`{code,msg,map_state,status}`） | ⏸ **维持"未开放"** | 本服无跨服玩法 |
| `11400` | `{code,msg}` | ⏸ **维持"未开放"** | 归属未定（`11400~11499` 在项目文档里仍是【未知】） |

---

## 二、`17301`：为什么"改为真实值"不等于"撒谎"

客户端 `race_ctrl.luac` proto#14（bc=56，`on17301`）逐条：

```lua
self.model:setStatus(0)
self.model:setMatchData(nil)
self.model:setResultData(data)      -- 整包存进模型
self:openWaitPanel(...) / openResultPanel(...) / gainFirstAward()
if data.act_type ~= 0 then BattleTips:new(..., 6) end
self.model:setScore(data.score)     -- ★ 战绩分
```

`race_ui_wait` / `race_ui_rank` / `race_ui_result` 消费 `score / win_times / total_times / continue_win / rank_list`。

⇒ **`score/win/lose/total/kill/continue_win` 都是"战绩"**：本服**没有任何战斗结算会写入**它们，
所以"**全 0**"是**真话**（= 这个角色还没打过），与 R47 竞技场同一口径 ——
**把"存 / 读 / 榜单"做通，产出等玩法**。

### 2.1 新增存储（列逐个对齐协议，不引入猜测映射）

```sql
race_state (rid PK, daily_time, daily_time2, score, win_times, lose_times,
            total_times, rest_time, first_reward, is_match, kill_number,
            continue_win, is_team_open, act_status, daily_win, updated_at)
```

### 2.2 ★ 一个被**当场抓出**的漏字段（本轮的实证价值）

第一版只写了 `show_cmd.py` 前 16 行能看到的 10 个字段。`tools/verify_race.py` 一跑就报：

```
SC_17301 len=30  解析消耗=31  errs=['is_match: 越界 (off=31 len=30)']  MISMATCH
```

`SC_17301` **实际有 16 个字段**，被截断漏掉的是：

```
is_match:u8, kill_number:u32, continue_win:u32, is_team_open:u8, act_status:u8, daily_win:u16
```

补齐后 `len=43 解析消耗=43 → PASS`。
⇒ **教训（写进方法论）**：`show_cmd.py` 的默认输出会截断，
**"照规格实现"必须用 `parse_full` 做"消耗字节 == 实际长度"的机械断言**，
不能靠肉眼看字段表。

### 2.3 ★ 第二个被现场抓出的坑：`CREATE TABLE IF NOT EXISTS` 不给旧表加列

补了 6 个字段后，**已存在的 `race_state`（首版 11 列）不会自动加列**；
`sqlite3.Row[k]` 取缺失列会抛错，而它在 `try/except` 里 ⇒ **静默退化成"字段恒 0"**，
测不出、看不见。修法（`db_race_init` 内，最小迁移、保留既有行）：

```python
have = set(d[1] for d in con.execute('PRAGMA table_info(race_state)'))
for col in ('is_match','kill_number','continue_win','is_team_open','act_status','daily_win'):
    if col not in have:
        con.execute('ALTER TABLE race_state ADD COLUMN %s INTEGER' % col)
```

复核：`PRAGMA table_info` 由 11 列 → **16 列** ✓
> ⇒ **一般化结论**：本项目"用 `try/except` 包住的 DB 读取"会把**结构漂移**变成静默的 0。
> 凡是新增/改动表结构，必须同时核对 `PRAGMA table_info` 与协议字段数。

---

## 三、`17309`：真实排行榜（沿用 R47 决策 A）

```sql
SELECT rid, name, level, career, sex FROM roles ORDER BY rid LIMIT 20
```
- 姓名 / 等级 / 职业 / 性别 → **取自 `roles` 真表**；
- `score` / `win_num` → 各自的 `race_state`（没打过 = 0）；
- 名次按 (分, 胜场) 降序编连续序号，**不编造并列名次**。

单角色环境下 `rank_list` 只有自己（`rank=1 name=DSH rid=1001 lev=70 score=0`）——
**这就是真话**，与 R47 竞技场"没有第二个角色时对手列表为空"同理。

---

## 四、`17501`：诚实回失败 + 回显 `type`

`SC_17501{code:u8, type:u8, msg:s}`。原先 `type` 一律填 0；
现在从 CS 取 `type` 原样回显（`guildwars_ctrl.handle17501` 按 `type` 分支）。
**玩法本体不存在 ⇒ `code=0 + msg='该功能暂未开放'` 不变** ——
回 `code=1` 会让客户端进一个没有内容的宗门战面板，比"未开放"更糟。

---

## 五、★ 分发集合同步（本项目踩过 4 次的坑，这次按纪律做）

| 集合 | 改动 | 原因 |
|---|---|---|
| `_UNSUPPORTED_ACTION_CMDS` | **移出 `17301`、`17501`**；24 → 22 条 | 否则靠前的集合会**抢先**回"未开放"，专用实现永远不执行 |
| `_GENERIC_DEFAULT_CMDS` | **移出 `17309`**；63 → 62 条 | 否则被抢先回空表 |

`tools/lint_dispatch_shadow.py` 复核：**专用 168 / 默认 62 / 未开放 22 ⇒ ✓ 0 遮蔽**。
**交叉自洽**：`62 + 22 = 84` == `audit_sc_conformance` 的审计命令数 **84** ✓
（该断言是 §5.1 新增的门禁，本次首次实际发挥作用）。

---

## 六、验证

```
tools/verify_race.py                                                  → PASS
  17301 len=43  解析消耗=43  errs=[]  result=1 score=0 win=0 lose=0 total=0
  17309 len=31  解析消耗=31  errs=[]  rank_list=1 (rank=1 DSH rid=1001 lev=70 career=1)
```

| 项目 | 改动前 | **改动后** |
|---|---|---|
| `lint_dispatch_shadow.py` | 165 / 63 / 24，0 遮蔽 | **168 / 62 / 22，0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 / 0 | **2463 / 0** |
| `audit_sc_conformance.py --generic --unsupported` | 87/0 | **84（83 一致 + 1 空规格）/ 0 不一致** |
| `audit_sc_live.py --unsupported` | 87/87 | **84/84 一致** |
| `audit_dedicated.py` | 62/62 | **63/63 符合规格** |
| `verify_attr_power` / `verify_account` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` | PASS | **全部 PASS** |
| 真机 | — | 8 帧全部完整（**无黑屏+弹窗帧**）⇒ R49 的弹窗修复**仍然有效** |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `race_state` 表 + `db_race_init/db_race_state/race_rank_list`；`17301`/`17309`/`17501` 专用 handler；两个集合同步移出 |
| `tools/verify_race.py` | 新增：规格精确解析 + 值来源核对（只读，可重复跑） |
| `analysis/_race_ctrl_dis.txt` | `race_ctrl.luac` 反汇编（`on17301` 消费点为真源） |
| `analysis/1.4.9/round50_race.md` | 本报告 |

---

## 八、P0-3 的**明确起点**（留给 R51，避免下轮重新摸索）

| 目标 | 现状 | 起点 / 阻塞点 |
|---|---|---|
| **`16602`** 节日活动列表 | 回 `type` 回显 + **空表**（round39 已判为**真话**） | 真机 CS 为 `03 66 00 00 13` ⇒ `type=3`；`SC{type, holiday_list:table(bid:u32, can_get_num:u8)}` 的 `bid` 是**节日活动 bid**。`config_fest_data.luac` 是 `FestTimer/FestLev/FestOnLine/FestDay/FestFirst`（时间/等级/在线/首充表），**不是 holiday bid 表** ⇒ **id 空间未取证，不得硬填** |
| **`19400`** 铭格 | 回通用零值 | `CS{bagcode:u8}`；`SC{bag_code, mingge_stage, mingge_list:table(…)}` 的嵌套子表**已展开**；配置 `config_mingge`（77KB，在 `_tmp_cfg`）在手 ⇒ **可做真实数据**，是本轮之后的第一个可落地项 |
| **`18307` / `20500` / `20504` / `20800` / `16500` / `19600`** | 回通用零值 | 逐条按"有无原版配置支撑"二选一：有 ⇒ 做真实数据；无 ⇒ 归入诚实化分诊并登记 |
| **属性补 10 列（带权重）** | `role_attr` 非零仅 11/26 列 | 等装备/养成系统的属性计算到位（**不补零占位**） |
