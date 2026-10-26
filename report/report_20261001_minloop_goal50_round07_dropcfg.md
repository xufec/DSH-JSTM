# 50 轮目标 · Round 7（goal round 26）—— 用 **APK 真实掉落配置**替换掉击杀奖励里的编造数据

> 时间：2026-10-01 ｜ 本轮目标：消灭"击杀奖励/掉落"里的 `[TEST_ONLY]` 占位值，改为配置驱动

---

## 〇、一句话结论

> 从 `analysis/1.4.9/item/_config_drop.json`（由 `assets/src/config/config_drop.luac` 还原）拿到
> 怪物 **20001** 的**真实**掉落记录：
> ```json
> {"mon_bid":20001, "drop_type":1, "coin":"{1000}", "wood":"{500}",
>  "first":0, "core":0, "normal":{}, ...}
> ```
> 并且 `analysis/1.4.9/item/drop_table.md:102` 明确把 `20001` 列入
> "**三个掉落节全空（只有 coin/wood）**"的 12 只怪。
> ⇒ 我此前的击杀奖励 **+30 coin / +50 exp** 与**每次掉一件 `bid=33001`** 都是**编造数据**，本轮全部移除，
> 改为：**coin +1000**、**不发任何物品**、**不发 exp**（客户端怪物配置里根本没有 exp 字段，
> `server/config.json::mon_calibration_note` 早有记载）。
> 自检 **58 → 59/59 PASS**。

---

## 一、本轮改动

| # | 文件 | 改动 |
|---|---|---|
| 1 | `min_loop_server.py` | 新增 `apk_drop(mon_bid)` / `parse_apk_num()` / `_drop_has_items()`；`kill_reward()` 改为**读 APK 配置**：`coin=parse("{1000}")`；**仅在配置确有物品节时**才发 `10500` 掉落 |
| 2 | `min_loop_server.py` | `KILL_REWARD` 标为 **`[DEPRECATED]`**（不再用于击杀奖励，保留常量仅为兼容） |
| 3 | `min_loop_server.py` | ★ **补 `import re`** —— 缺这个 import 导致 `parse_apk_num` 抛 `NameError`，整个 `kill_reward` 静默失败（见 §二） |
| 4 | `selftest.py` | 断言改为 **APK 真值**：`击杀 20001 ⇒ coin +1000`、`无物品掉落 ⇒ 背包不新增 + 不发 10500`；背包查询改为断言"**应答与 DB 真实一致**"（不再硬要求非空） |

**诚实标注（保留 UNKNOWN，不硬塞）**：`wood={500}` 是 APK 真实字段，但本服 `roles` 表**无 wood 列**
⇒ 本轮**只记录、不落库**（也不塞进别的货币字段冒充）。

---

## 二、★ 过程中发现的一个真实缺陷（`import re` 缺失）

- 首跑自检 5 项失败，其中 `coin 0→0` 很反常（分支明明走到了"无物品掉落"）。
- 直接探针定位：`python -c "…M.parse_apk_num('{1000}')"` → **`NameError: name 're' is not defined`**。
- ⇒ `kill_reward` 在**第一行就抛异常**，被服务端逐消息的 `except` 吞掉、只留一条错误日志
  ⇒ 表现为"击杀后既没奖励也没掉落"。
- 修复：`import re`。**再次复跑 ⇒ 59/59 全绿。**

> 教训（已固化进自检）：**新增工具函数必须被断言覆盖**，否则异常会被 per-message 的 try/except 静默吃掉。

---

## 三、自检（回归门禁）

```
python server/minloop/selftest.py
  → 检查项 59，通过 59，失败 0        （此前 58/58）
```
本轮新增/改写的关键断言：

| 断言 | 实测 |
|---|---|
| ★ `击杀 20001 的 coin 奖励 = APK 配置的 1000` | PASS |
| ★ `怪物 20001 按 APK 配置无物品掉落 ⇒ 背包不新增` | PASS |
| ★ `无物品掉落时**不发** 10500 掉落推送（不编造）` | PASS |
| `10502 返回的物品数与本服 DB 真实一致` | PASS |
| ★ `背包里不应再出现已移除的占位掉落物 bid=33001` | PASS |
| ★ `击杀后提交 10020 ⇒ 成功`（上一轮加的，仍 PASS） | PASS |
| ★ `10020 奖励与 APK 配置逐项相等`（上一轮加的，仍 PASS） | PASS |

---

## 四、完成 / 未完成（本轮）

### 4.1 完成
1. ★ **击杀奖励/掉落改为 APK 配置驱动**，删掉两处编造数据（占位 coin/exp、占位掉落物）。
2. ★ **找到并修掉一个静默失败缺陷**（缺 `import re` ⇒ 异常被 per-message `except` 吞掉）。
3. 自检基线 58 → **59**，且新增断言覆盖了新工具函数。
4. 保留 `wood` 的 `UNKNOWN`（无字段 ⇒ 不落库），未把未知硬塞进已知货币字段。

### 4.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `wood` 的落库位置（本服无字段） | **UNKNOWN**（仅记录） |
| 2 | 有**真实物品掉落**的怪物（24 只里除 12 只空表外的那些）是否该按配置发物品 | 未做；且 `drop_table.md` 提示其物品 `51000–51066` **不属于本作**（"0 个"）⇒ 需谨慎评估再动 |
| 3 | 其余 `analysis/` 文档逐条对照 | 🚧 进行中 |
| 4 | 客户端 `10102/10103` 不上线（唯一硬卡点） | 仍 blocked（需外部原生观测手段） |

---

## 五、下一轮建议

1. **评估"有物品掉落的怪"**：先读 `analysis/1.4.9/item/drop_model.md` 里关于
   "`51000–51066` 不属于本作"的取证，判断**是否应当**按配置发这些物品；
   **在确证之前不发**（宁缺勿造）。
2. 把击杀的 `wood` 做成**显式 UNKNOWN 清单**（写进 README/HANDOVER 的"未落库字段"一节）。
3. 继续文档对照：`analysis/jstm_1.4.9/task_protocol.md` 的 `12404~12450`、场景/战斗字段。

---

## 六、本轮产物

| 文件 | 说明 |
|---|---|
| `server/minloop/min_loop_server.py` | ★ 配置驱动击杀奖励 + 新工具函数 + `import re` 修复 |
| `server/minloop/selftest.py` | ★ 断言改为 APK 真值（并新增"不得出现占位物"红线），59/59 |
| `analysis/1.4.9/item/_config_drop.json`、`drop_table.md` | 本轮依据（APK 真实掉落配置 + 文档记载） |
