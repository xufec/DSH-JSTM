# R53：挂机链续做（`15403`/`15404`）+ 两条"永不回包"命令补入 —— 以及门禁自己被抓出的 bug

> 本轮三件事：
> ① **挂机链**：把 `15402` 之后的两环（`15403` 杀怪上报、`15404` 轮次结束推送）做通；
> ② **两条真机在发、服务端一句话不回的查询型命令**（`13321` / `16664`）按 round39 判据补入；
> ③ **门禁 E 的集合解析器自己有 bug**，修好后覆盖面 82 → 132 条，露出 48 条未登记空表。
> **时间**：2026-09-29 10:40 – 11:00。

---

## 一、挂机链：`15403` / `15404`

### 1.1 客户端消费点（`ghost_ctrl.luac`，反汇编实证）

`ghost_ctrl` proto#38 是类定义块，`FNEW` 次序给出方法号：

| 方法 | proto | 行为（逐条读出） |
|---|---|---|
| `handle15402` | #30 | `mon_hongchen = GhostMon:new('mis_hongchen'); mon_hongchen:initData(data)` |
| **`handle15403`** | #31 | **`GlobalEvent:getInstance():message(data.msg)`** ← ★ `msg` 会**直接弹给玩家** |
| **`handle15404`** | #32 | `mon_hongchen:deleteMon()`（清掉挂机怪 = 结束本轮） |
| `killHuanBoss` | #33 | `mon_hongchen:killMon(data)` |

⇒ 链路：`15405`(轮次) → `15400`(启动) → `15402`(任务→地图/坐标) → 客户端自行刷怪 →
**`15403{mon_bid}` 上报** → …… → **服务端推 `15404{mission_bid}` 结束本轮**。

### 1.2 实现（**不猜轮次规则**）

```
CS_15403{mon_bid:u32} → SC_15403{code:u8, msg:string}
  · mon_bid ∈ config_guaji 的 8 条挂机怪（或 Config.Mon 里真实存在）
      ⇒ kill_count +1 **落库**，回 code=1 + msg=''（不打扰玩家）
  · 否则 ⇒ code=0 + msg='未知怪物(N)'（**不静默接受垃圾输入**）
  · ★ **不自动推 15404** —— "一轮 = 几只怪"在原版里**没有取证**
    （`config_guaji` 只给 怪/地图/等级段；`config_mission` 里没有挂机轮次字段）
    ⇒ 猜一个阈值就是在编造规则。需要结束本轮时用管理接口**显式触发**。
```

新增：
- `guaji_state` 补两列 `mission_bid` / `kill_count`（**幂等 ALTER**，R50 已踩过"新表不给旧表加列"）；
- `db_guaji_state()` / `db_guaji_update()`；
- `push_to_rid(rid, pkt)` —— 按 rid 推帧给在线连接；
- **`GET /DSH_ADMIN/guaji_end`** —— 实验旋钮：显式推 `15404{mission_bid}`。

### 1.3 验证（`tools/verify_guaji.py`，全 PASS）

```
== 15402 ==  len=16 消耗=16 PASS  mission_bid=10010 map_bid=10005 (10,58)
             map_bid 命中 config_guaji 的挂机点: 是     mission_bid 落库: 10010
== 15403 合法怪 mon_bid=10101 ==  code=1   kill_count: 0 → 1   ✓ 真落库
== 15403 未知怪 mon_bid=999999 == code=0 msg='未知怪物(999999)'  kill_count 未变 ✓
== 15404 推送 ==  /DSH_ADMIN/guaji_end → connections=1，收到 15404 len=4 消耗=4 PASS
跑完已把 guaji_state **原样恢复**（无副作用）
```

### 1.4 ★ 真机实验：链路的"卡点"仍在更前面

按 R48 的方法在 MuMu 上实走（`日常` → `参与`，`loop_count` 依次 1 与 10）：

```
>> cmd=16664          ← ★ 此前无人应答的查询命令（见 §二）
>> cmd=10204 寻路
>> cmd=15405
<< 15405 SC_15405 loop_count=10        ← 我们的实现生效
>> cmd=10204 寻路
   之后只有心跳 —— **没有 15400**
```

| 观察 | 结论 |
|---|---|
| 客户端面板显示「学院任务(今日已完成 **1/10 环**)」 | 环数来自 `daily_progress`（R48 写入的那 1 环）✓ |
| `loop_count` 给 1 或 10，行为一致 | `15405` **不是**当前唯一的卡点（R48 当时看到 `15400` 是**偶发/时序相关**） |
| 客户端停在"走到位"之后 | 缺的可能是别的**前置**（R48 记录过 `15402` 是登录后主动发的；本轮 15402 一次都没发） |

⇒ **诚实结论**：`15403/15404` 这两环**已做通并验证**（服务端侧），
但**进入挂机所需的客户端前置仍未完全取证**，本轮**不再猜**。
真机实验把 `loop_count` 复位为 **0**（默认安全值），玩家状态未被污染。

---

## 二、两条"真机在发、服务端一句话不回"的查询型命令

本轮用 `tools/_probe_gaps.py` 现场普查，发现两条**完全无人应答**的命令（比"未开放"更糟 —— 客户端干等）：

| CMD | 权威名（`cmd_table.json`） | SC 规格 | 判据 |
|---|---|---|---|
| **`13321`** | — | `{request_list:table(15 字段)}` | 无 `code/result/tips` ⇒ **查询型** |
| **`16664`** | **获取限时充值返利活动数据** | `{msg:s, bid:u32, remain_sec:u32, status:u32, end_time:u32, rate:u32, client_reward:s}` | 无结果码 ⇒ **查询型** |

按 round39 已立的判据（**SC 里没有结果码 ⇒ 缺数据时回"零值/空表"是真话**）补入 `_GENERIC_DEFAULT_CMDS`。

### 真机复验（同一台机，重新登录）

```
改前会话 GAP = 4：10001 / 10300 / 13321 / 16664
改后会话 GAP = 2：10001 / 10300        ← 余下两条 `fields.json` 里**没有 SC 定义**
                                        （CS-only 上报型，本就不该应答）
```

| 门禁 | 变化 |
|---|---|
| 默认集合 | 62 → **64** |
| 默认应答一致性审计 | 84 → **86 命令**（64 + 22，交叉自洽 ✓） |

---

## 三、★★ 门禁 E **自己**被抓出的 bug（本轮最有价值的意外）

补完 `13321/16664` 后，门禁 E 却报"待查命令 82 条"——**和加之前一样多**。
追查发现：门禁解析 `_GENERIC_DEFAULT_CMDS` 的正则要求"`=` 后面紧跟 `(`/`[`"，
而源码是：

```python
_GENERIC_DEFAULT_CMDS = frozenset([        # ← `frozenset` 开头，正则匹配不到
```

⇒ **集合被静默解析成 0 条**，门禁一直只覆盖"专用分支"（82 条）在跑，
`_GENERIC_DEFAULT_CMDS` / `_UNSUPPORTED_ACTION_CMDS` 的成员**从未被检查过**。

修法：注释先剥掉 + **括号配对扫描**（不再用正则）。修好后：

```
覆盖命令：82 → 132 条
新暴露：★ 48 条未登记的顶层空表
```

48 条**逐条写明理由**后登记入白名单（`_emitted_empty_allow.json`，39 → **87 条**），
性质全是"本服没有该玩法/没有记录 ⇒ 空是真话"（好友/法宝/神兵/翅膀技能/仙椅/段位分布…），
其中就包括本轮新增的 `13321:request_list`。

> **教训（写进方法论）**：这是本项目 **第 5 次**"审计工具自身有 bug"（前 4 次见 METHODOLOGY §5/§6）。
> **审计报"通过"之前，先证明它真的检查到了东西** —— 本轮靠"改动前后覆盖条数没变"这个异常发现的。

---

## 四、全量验证（六道门禁 + 全套回归）

| 门禁 | 结果 |
|---|---|
| `lint_dispatch_shadow.py` | 专用 **169** / 默认 **64** / 未开放 **22** ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 / **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 86 命令：85 一致 + 1 空规格 / **0 不一致** |
| `audit_sc_live.py --unsupported` | **86/86 一致** |
| `audit_dedicated.py` | **63/63 符合规格** |
| **`audit_emitted_fields.py`** | 132 条命令 / 顶层空表告警 **0** / 豁免 87 条 / **PASS**；`--selftest` **PASS** |
| 交叉自洽 | `64 + 22 == 86` ✓、`169 == 169` ✓ |
| 回归 | `verify_guaji` / `verify_race` / `verify_attr_power` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `server_stderr.log` **0 字节**；9000 端口**恰好 1 个监听**；真机 8 帧完整、正常进主城 |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `15403` handler；`15402` 记 `mission_bid`；`guaji_state` 补两列 + `db_guaji_state/update`；`push_to_rid()`；`/DSH_ADMIN/guaji_end`；`13321/16664` 补入默认集合 |
| `tools/verify_guaji.py` | 新增：挂机链四段验证（含"未知怪拒绝计数"反向用例、跑完恢复 DB） |
| `tools/audit_emitted_fields.py` | **修掉集合解析器 bug**（括号配对扫描）；覆盖面 82 → 132 |
| `tools/_emitted_empty_allow.json` | 白名单 39 → **87 条**（新增 48 条均写明理由） |
| `tools/_fix_r53_allow.py` | 白名单批量登记脚本（可重跑） |
| `analysis/1.4.9/round53_guaji_and_gap.md` | 本报告 |

---

## 六、下一步

| 优先 | 事项 | 说明 |
|---|---|---|
| 1 | **挂机前置取证** | `15403/15404` 已通，但客户端在 `15405` 之后不推进到 `15400`。下一步应**挂钩 `15400` 的发送条件**（`ghost_ctrl` 里 `goto`/`onSceneSuccess`/`planHandler` + `AutomateCtrl`）—— 不要猜轮次数值 |
| 2 | **`10331` 无效 bid** | 真机反复发 `skill_bid=1001`（无效），服务端回 `code=0`。需判定是"客户端真的这么发"还是"CS 尾部 4 字节残留被误读" |
| 3 | **`15203`** | 空 CS 查询型却回 `code=0`；语义待查 |
| 4 | **`19400` 命格背包** | 需先有"玩家拥有命格"的来源 |
| 5 | **推荐战力** | **外部依赖**：`Config.RoleAttr` 无战斗属性，原版曲线不在 APK 里 |
