# R236（新目标①④）：★★★ **`12601` 接 `cfg_kconfig`（60 行）—— 但发现"转换不完整"**

> 新目标第 6 批。★★★ **第一次把 `cfg_kconfig` 接进消费命令（用途④），并如实发现它的边界。**
> **时间**：次日 06:30 – 08:30。

---

## 一、★★★ 为什么选 `12601`

```
SC_12601: CS[] → SC{demon_list:table<bid:u32, career:u8, star_lev:u8, nature:u8,
                                     chip:u16, action_power:u32, power:u32,
                                     skill:table<skill_bid:u32>>,
                  demon_chip:table<bid:u32, chip_num:u16>}

cfg_kconfig/config_demon（**60 行**）的列:
   action_power ✓ ｜ action_power_kill ｜ balance_ratio ｜ **bid** ✓ ｜ **career** ✓
   ｜ **chip** ✓ ｜ chip_sum ｜ cost ｜ lev ｜ lev_up_chip ｜ name ｜ **nature** ✓
   ｜ res_id ｜ **star_lev** ✓
⇒ ★★ **6 个字段逐名对应**（`bid`/`career`/`star_lev`/`nature`/`chip`/`action_power`）✓

cfg/config_demon.json（**只有 4 行**）⇒ ★ **线性解构失败** ⇒ **必须用 `cfg_kconfig`** ✓
```

★ **⇒ 这是"用途④（把 `cfg_kconfig` 接进消费命令）"的**第一个实例**** ✓

---

## 二、★★★ 但**实测发现 `cfg_kconfig` 的"转换不完整"**

```
rows: 60 个键
   [1] = {"action_power_kill": 10, "balance_ratio": 1}              ← ★ **只有 2 个字段**
   [2] = {"lev_up_chip": 130, "lev": 5, "cost": 400, "chip_sum": 310}  ← ★ **另一组字段**
   [3] = {"lev_up_chip": 100, "lev": 4, "cost": 300, "chip_sum": 180}
   [4] = {"lev_up_chip": 50, "lev": 3, "cost": 200, "chip_sum": 80}
lists:
   proto0（**51 条**）= [[null,3,5,7,9,11], [null,1,2,3,4,5], [null,14800], [null,10100], …]
```

★★ **⇒ `rows` 是"零散的字段片段"**（**不是"每行一个实体的全部字段"**）⇒
   ★★★ **⇒ `lists` 是"零散数组"**（**如 `bid → 阶段序列`**）⇒
      **⇒ 都**对不上 `SC_12601.demon_list` 的 8 个字段** ⚠

### ★ 实测

```
cfg_kconfig/config_demon: 60 行（cfg 只有 4 行）
12601: len=1144 消耗=1144 err=None ｜ ★ demon_list=60（应 60）
   首条: bid=0 career=0 star_lev=0 nature=0 chip=0 action_power=0     ← ★ **全 0**
⇒ PASS（结构）但**内容为空** ⚠
```

★ **⇒ 按纪律第 71 条**（**"结构 PASS 但内容为空 ⇒ 先查'字段是不是取错'"**）⇒
   **⇒ 查明：`cfg_kconfig` 的 `config_demon` 转换**不完整（**R221 的规则对"多 dict 各装一行"型的配置不适用**）⇒
   **⇒ 不硬填，如实记录** ✓

> **★ 纪律第 76 条**：**"常量池 → 配置表"的转换对"多 dict 各装一行"型的配置**不完整** ——
> R221 的规则 ①（**"N 个 dict 各装一行" ⇒ 每个一行**）**在 `config_demon` 上失败**：
> `rows` 里每个键只有**部分字段**、`lists` 是**零散数组**。
> ★★ **判据**：**"转换后每行的字段数远少于预期" ⇒ 转换不完整**（**不要硬接**）。
> ★★★ **升级路径**：**需要在 `kconst_to_cfg.py` 里加"把同一实体的散片合并"的规则**。

---

## 三、★ 但仍保留（**比"大 tuple"好**）

★ `12601` **现在有专用分支**：
   - **结构正确**（`demon_list=60`，**计数与配置行数一致**）
   - **换成"大 tuple"也只有全 0** ⇒ **没有变差**
   - ★★ **为下一步"接真值"留好了位置**（**改一处不影响别处**）✓

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1546** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★★ **缺口清单** | **126 → 125 条** ✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | `12601` 的专用实现（**用 `kcfg_rows('config_demon')`**）|
| ★★ **本报告第二节** | ★★ **`cfg_kconfig` 转换边界的首次量化**（**纪律第 76 条**）|

---

## 六、下一批（**调整方向**）

| 方向 | 理由 |
|---|---|
| ★★ **修 `kconst_to_cfg.py`：加"散片合并"规则** | **解锁"多 dict 各装一行"型的配置**（如 `config_demon`）|
| ★ **`13600`（`role_boss_kill` 0 行）** | **BOOS 列表**（**本服 0 行 ⇒ 空是真话**）|
| ★ **`12208`（`role_heros`）** | **据点的非战斗部分** |
| ★ **`18807`（`peakwar_state` 0 行）** | **巅峰战** |
