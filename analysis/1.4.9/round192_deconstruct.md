# R192（新目标④）：**解构器工程 —— 找到"主 proto"规律，救回 4 个核心配置**

> 新目标第 2 批。★★ **本批找到了"配置解构失败"的根因，并建立了"只增不减"的安全改法。**
> **时间**：次日 23:00 – 01:30。

---

## 一、★★★ 根因：**"主 chunk"不一定是 `proto0`**

`batch_deconstruct.py` 一直用 `deconstruct(path, proto_index=0)`。
但实测（`_diag_r192b.txt`）：

| 配置 | 各 proto 的**指令数** | **主 proto** | 用对后 |
|---|---|---|---|
| **`config_item`** | 91 / **65483** | **proto1** | `Config`（120 字符）|
| **`config_skill`** | **69601** / 137 / 40 | **proto0** | `Config`（**737**）|
| **`config_mon_data`** | **58359** / 71 / 33 | **proto0** | `Config`（**311**）|
| **`config_common`** | **57** | proto0 | ★ **13 个顶层键**（**1365**）✓ |

★ **关键证据**：`config_item` 的 **`proto1` 有 `KNum=1117`** ——
   **正好等于 `config_item` 的物品数（1117）** ⇒ **数据确实在 `proto1`** ✓
   而 `proto0`（91 条 = helper）**解出 2 字符** ⇒ **这就是"解构失败"的真相**。

---

## 二、★★★ 安全改法：**"只增不减"**（保护已有数据）

### 第一版的错（值得记录）

R192 第一版规则是 **"新结果 ≥ 旧结果就覆盖"** ⇒ **覆盖了 70 个文件**。
结果 **`config_map_npc.json` 从 `{MapNpc: …}` 被覆盖成 `{Config: …}`** ⇒
**`verify_107xx.py` 报 `KeyError: 'MapNpc'`** —— ★ **真机回归当场抓到**。

★ **⇒ 改成"只对原来就空/极小（<200B）的文件"应用自动解构**：
```
① 先用 batch_deconstruct.py 重建（回到原始解构状态）
② 找出"空/极小"的（<200B）
③ 只对这些跑"自动选主 proto"并覆盖
④ 非空的文件一律不动
```

### 结果显示（**最终**）

```
③ ★ 救回 4 个（原来空、现在有数据）：
   config_common        1365 字符（proto0/1）
   config_mon_data       311 字符（proto2/3）
   config_skill          737 字符（proto2/3）
   config_skill_magic    743 字符（proto2/3）
④ 非空的文件一律未动（保护已有数据）✓
```

**验证**：**66 项回归失败 0** ｜ 门禁全 PASS ✓

> **★ 纪律第 34 条**：**"批量重生成产物"必须"只增不减"** ——
> 只要"新结果更大"就覆盖，**会把"结构不同但内容正确"的文件改坏**
> （本批的 `config_map_npc`：`{MapNpc:…}` → `{Config:…}`，**新结果更大但丢了键**）。
> ★★ **安全规则**：**已有数据一律不动；只补"空的"**。
> ★★★ **验证手段**：**真机回归**（`verify_107xx` 的 `KeyError` 就是它抓到的）。

---

## 三、★ 本批的工具产出

| 工具 | 说明 |
|---|---|
| **`tools/scan_global_fallback.py`** | ★★ **扫"协议有 CS+SC 但不在任何专用分支里"的命令** ⇒ 实测 **0 条**（**目标①③ 达成**）|
| **`tools/deconstruct_auto2.py`** | ★★ **安全版自动解构**（重建 → 只补空的）|
| `tools/_diag_r192.py` / `_diag_r192b.py` | ★ **主 proto 诊断**（`KGC`/`KNum`/`KStr` 计数）|

---

## 四、★★ 目标达成情况

| 目标 | 状态 | 硬证据 |
|---|---|---|
| ① 两个兜底集合升级 | ★★ **达成** | R191 已清零；`scan_global_fallback` 实测 **0 条**走全局兜底 |
| ② B 类 15 条 + 回执型复查 | ★ **部分** | 见下批 |
| ③ 按家族扫"仍走兜底"的 | ★★ **达成** | **0 条** |
| ④ 解构器工程 | ★ **重大进展** | **找到"主 proto"规律** + **救回 4 个核心配置**（`config_skill`/`config_mon_data`/`config_common`/`config_skill_magic`）|

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0（默认集合空）/ 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| **`tools/scan_global_fallback.py`** | ★ 扫"仍走全局兜底"的命令（**实测 0**）|
| **`tools/deconstruct_auto2.py`** | ★ 安全版自动解构 |
| `tools/deconstruct_auto.py` | （第一版，含"只增不减"注释）|
| `server/cfg/config_{common,mon_data,skill,skill_magic}.json` | ★ **救回**（空 → 有数据）|
| `server/cfg.bak_r192/` | cfg 备份 |

---

## 七、下一批

| 目标 | 依据 |
|---|---|
| ★ **`config_item` 仍只有 120 字符** | 它的数据在 **`Config.ItemDeCompose.ItemDecomList`**（**深层赋值**）⇒ 解构器要支持"嵌套路径" |
| ★ **仍空 68 个配置**（`config_client`/`config_drop_item`/`config_role_attribute`…）| 用同一套诊断逐个看 |
| ★ **B 类 15 条 + 回执型复查**（目标②）| — |
