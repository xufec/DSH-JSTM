# R198（新目标②）：**B 类"配置源"取证（第二轮）—— 含一项**否决**

> 新目标第 8 批。★ **取证 ≠ 实现**：本批**找到了三个配置的顶层键与字段结构**，
> 并**否决了一个错误的假设**（`config_act` 不是活动配置）。
> **时间**：次日 10:30 – 12:00。

---

## 一、★★ 取证结果（三项）

| 配置 | ★ 顶层键 / 主表 | 字段结构 | 对应的 B 类命令 |
|---|---|---|---|
| **`config_mission`（620122 B）** | **`Config.Mission`**（kgc[425]）| ★ **30 个字段**：`accept_talk`/`accept_npc_id`/`commit_talk`/**`type`**/`show_type`/**`bid`**/`progress_edit`/`career`/`auto_commit`/`process_talk`/`max_lev`/`times_arg`/`realm`/`is_drama`/**`name`**/`times_type`/`guider_res_id`/`lev_track`/`time_lim…` | **`19500`（任务）** |
| **`config_global_wish_data`（1244 B）** | **`Config.GlobalWishStatic`**（kgc[32]）| `{bid: 25729, content_len: 40, refresh_len: 15, version: 1, add_val}` | **`qifu`（祈福）** |
| **`config_holiday_balloon`（19219 B）** | **`Config.BalloonQuestion`**（kgc[29]）| **128 条问答**：`{c:"唐雅", a:"少年雨浩", d:"海公主", content:"以下哪个伙伴可以拥有复活技能", b}` | 气球问答活动 |

---

## 二、★★★ 一项**否决**（**取证的价值也在这里**）

**假设**：`16601`/`16602`（活动列表）的配置源是 **`config_act`**（**508 条**）。

**验证**：`config_act` 的 508 条里 **505 条是 list 型**：
```
[0] [null, 0, "E63010", 10, 0, "hurt", 40, 40, 0, "", 0, 120]
[1] [null, "flyItem"]
[3] [null, "attack"]
...
字符串常量: ["PlayOrderData", "PlayOrder", "Config"]
```
★ **⇒ 它是"战斗演出（`PlayOrder`）"配置**（`E63010` 特效 id、`hurt` 动作、`40/40` 时间）
   —— **不是"活动（holiday）配置"** ❌

★★ **⇒ 结论**：**`16601`/`16602` 的配置源需要另找**（`config_fest_data`/`config_holiday_*`/`config_function`）。

> **★ 纪律第 39 条**：**"配置源"的假设必须验证，不能凭名字** ——
> `config_act` 名字像"活动"，**但内容其实是"战斗演出"**；
> ★★ **判据**：**打开配置看"实际条目内容"**（本批就是靠 `[null,0,"E63010",…,"hurt",…]` 推翻假设的）。

---

## 三、★ 处置（**R134 规则**）

| B 类命令 | 处置 | 理由 |
|---|---|---|
| **`19500`（`CS[]` → `{code,msg}`）** | ★ **维持 `code=0`** | 无参数 + 语义未证明 ⇒ **不冒进**；但**已在报告里记录"任务配置存在（30 字段 / 300+ 条）"** |
| **`16601`/`16602`** | ★ 继续取证 | 配置源待另找 |
| **`qifu`** | ★ 取证完成，可实现 | `GlobalWishStatic` 的 35 条 |
| `dailysign`（`19600`）| ★★ **R196 已升级** | 95 档位 |
| `npc`（`15204`）| ★★ **R197 已升级** | `num=17` + 真实 `gold` |

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/_diag_r198.py` | 顶层键诊断 |
| `tools/_diag_r198b.py` / `_diag_r198c.py` | ★ **"找主表"诊断**（对每个配置找 hash 项最多的 dict）|
| `tools/_diag_r198d.py` | ★ **list 型条目诊断**（**推翻 `config_act` 假设的关键**）|

---

## 六、下一批

| 目标 | 依据 |
|---|---|
| ★★ **`16601`/`16602` 的真配置源** | 试 `config_fest_data`/`config_festival_goods`/`config_function`/`config_holiday_*` |
| ★ **`qifu` 用 `config_global_wish_data`（35 条）实现** | — |
| ★ **`19500`：若能从 `config_mission` 的 `type` 字段取证语义，则升级** | 30 字段里有 `type`/`show_type` |
| ★ **其余 8 条社交域** | 维持"空即真话" |
