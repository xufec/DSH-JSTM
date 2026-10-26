# R239（新目标①④）：★★★ **`12410`（抽奖列表）接 `config_fabao`（69 行，`cfg_kconfig2`）**

> 新目标第 9 批。★★★ **`cfg_kconfig2` 的第二次实战 —— 4/4 字段全对应，接出 69 条真数据。**
> **时间**：次日 13:00 – 15:00。

---

## 一、★★ 阈值降到 4 重扫（`tools/scan_gap_sources2.py`）

```
★★ 有候选的: 14 / 122 条
   12405 ← missions(11) ｜ 12208 ← role_heros(5)+config_single_tower(4)
   12980/13542/18753 ← config_mission(5) ｜ 12201 ← config_game_data(4)
   12722 ← config_mission(4) ｜ 13600 ← roles(5)
   11410/11411 ← config_mission(4) ｜ 11717 ← config_vip_ernie_data(4)
   12211 ← roles(4) ｜ ★ **12410 ← config_fabao(4)** ｜ 18807 ← peakwar_state(3)
```

★ **⇒ `12410` 只有 5 个字段、`config_fabao` 有 69 行** ⇒ **最值得先做** ✓

---

## 二、★★★ 取证（**4/4 逐名对应**）

```
SC_12410: CS[] → SC{id:u32, lottery_list:table<id:u32, item_bid:u32,
                                               item_num:u32, bind:u8>}

cfg_kconfig2/config_fabao（**69 行**）的列:
   **id** ✓ ｜ **item_bid** ✓ ｜ **item_num** ✓ ｜ **bind** ✓ ｜ type ｜ limit_day
   ｜ item_name ｜ pay_type ｜ price ｜ order
   ⇒ ★★ **4/4 全对应** ✓

实数据:
   [23022] = {type:9, bind:0, item_num:1, item_name:"碧磷毒牙精华",
              item_bid:25771, id:23022, price:90, order:22}
   [23021] = {…, item_name:"神鹰之翼精华", item_bid:25770, …}
```

★ **`cfg/config_fabao.json`（11 行）⇒ 线性解构不完整** ⇒ **必须用 `cfg_kconfig2`** ✓

---

## 三、★ 实测（**69 条真数据**）

```
cfg_kconfig2/config_fabao: 69 行
12410: len=903 消耗=903 err=None ｜ ★ lottery_list=69（应 69）
   [0] id=23022 item_bid=25771 item_num=1 bind=0
   [1] id=23021 item_bid=25770 item_num=1 bind=0
   [2] id=23020 item_bid=25769 item_num=1 bind=0
⇒ PASS
```

★★ **⇒ 69 个真实抽奖商品**（`id`/`item_bid`/`item_num`/`bind` **全有真值**）✓

---

## 四、★ `cfg_kconfig2` 的**第三次验证**

| 轮 | 命令 | `cfg_kconfig`（旧）| ★ `cfg_kconfig2`（新）|
|---|---|---|---|
| R237 | `12601` | 60 个残缺行 ⇒ **全 0** | ★ **9 个完整恶魔**（**真值**）✓ |
| **R239** | **`12410`** | — | ★ **69 个抽奖商品**（**真值**）✓ |

★★ **⇒ "按关键键合并散片"的规则**再次证明有效**** ✓

> **★ 纪律第 78 条**：**"`cfg_kconfig2` 是"接配置"的首选数据源"** ——
> 它**按 `bid`/`id` 合并散片** ⇒ **行数与"关键键出现次数"一致** ⇒ **字段完整**。
> ★★ **判据**：**"要接配置时，先看 `cfg_kconfig2/<name>.json` 的 `rows` 里有没有你要的键"**。
> ★★★ **对照**：`cfg`（**线性解构**，231 个）/ `cfg_kconfig`（**残缺行**，245 个）/ **`cfg_kconfig2`（完整行，245 个）**。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1550** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★ **`12410`** | **69 条真实抽奖商品** ✓ |
| ★★ **缺口清单** | **122 → 121 条** ✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | `12410` 的专用实现（**用 `kcfg2_rows('config_fabao')`**）|
| `tools/_diag_r239.py` | `12410` / `config_fabao` 的取证 |

---

## 七、进度（新目标 9 批）

| 指标 | 起点 | 现在 |
|---|---|---|
| **专用分支** | 1446 | **1550**（**+104**）|
| **缺口清单** | 318 | **121** |
| **实质数据接入** | — | **+14 条** |
| **报告** | 206 | **215** |
| **纪律** | 70 | **78** |

---

## 八、下一批

| 命令 | 数据源 | 方向 |
|---|---|---|
| ★★ **`12208`** | `role_heros`(5) + `config_single_tower`(4) | 伙伴/爬塔 |
| ★ **`12201`** | `config_game_data`(4) | 配置驱动 |
| ★ **`11717`** | `config_vip_ernie_data`(4) | VIP 抽奖 |
| ★ **`11410`/`11411`** | `config_mission`(4) | 比武场（需 pvp）|
| ★★ **用 `cfg_kconfig2` 扫"所有配置的消费命令"** | — | **系统性"用途④"推进** |
