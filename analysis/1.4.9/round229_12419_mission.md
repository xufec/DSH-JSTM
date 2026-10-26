# R229（新目标②）：★★ **`12419`（按 `uniq_id` 查任务状态）接上 `missions`（5 行）—— 第 20 条**

> 新目标第 39 批。★★ **按 R226 的权威清单推进 `124xx` 族，复用已有的 `build_mission_entry`。**
> **时间**：次日 15:00 – 17:00。

---

## 一、★★★ 关键发现：**`SC_12419` 与已有的 `build_mission_entry` 字段完全相同**

```
SC_12419（CS{srv_id:string, uniq_id:u32}）:
   mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16, loop_num:u16,
   code:u8, process_status:u8, target:u32, target_value:u32, value:u32,
   show_lave_time:u8, lave_time:u32, accept_time:u32        ← ★ 13 个字段

已有的 build_mission_entry(m)（L4910，R186 为 12400 写的）:
   ★ **字段完全相同（13 个、顺序一致）** ✓

missions 表列: [rid, mission_bid, mission_status, process_status, target, target_value,
               value, commit_num, loop_count, loop_num, code, accept_time, updated_at]
   ⇒ ★ **11 个与 SC 同名** ✓
```

★★ **⇒ 直接复用 `build_mission_entry`**（**R186 的既有函数** —— **纪律第 59 条**）✓

---

## 二、★ 处置（**如实标注不确定性**）

| 项 | 处置 |
|---|---|
| **`uniq_id`** | ★ `missions` **没有该列** ⇒ 按 **"行索引（1-based）"** 解释；**越界 ⇒ 退回第 1 行**（**语义未确凿**）⚠ |
| **13 个字段** | ★ **用 `build_mission_entry`**（**与 `12400` 同一函数**）✓ |

---

## 三、★ 实测

```
DB missions: 5 行 ｜ [(10010,3), (10020,3), (10030,3)]
12419 uniq_id=1: len=34 消耗=34 err=None ｜ ★ mission_bid=10010 status=3   ⇒ PASS
12419 uniq_id=2: len=34 消耗=34 err=None ｜ ★ mission_bid=10020 status=3   ⇒ PASS
```

★ **⇒ `uniq_id` 按行索引 ⇒ 返回对应的真实任务**（**与 DB 一致**）✓

---

## 四、★ 一处自纠（**函数名猜错**）

第一版用了 **`db_mission_list`**（**不存在**）⇒ `NameError: name 'db_mission_list' is not defined`
⇒ **服务端连接关闭**（`tcp.log` 报 `--- error: NameError(...)`）❌
**修**：**`db_get_missions(rid)`**（**返回 `{bid: mission}` dict** ⇒ `list((...or {}).values())`）✓

> **★ 纪律第 70 条**：**"内建函数名"必须先 grep 现有用法** ——
> 本批猜了 `db_mission_list`（**不存在**）⇒ `NameError` ⇒ **连接关闭**。
> ★★ **这与纪律第 38 条（"读 DB 的接口要先 grep"）同源**，但**更普遍**：
> **凡"调用项目内函数"前，先 grep `def <名>` 或现有调用**。
> ★★★ **判据**：**`tcp.log` 里的 `--- error: NameError(...)` 就是信号**。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1446** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★ **`12419`** | **`mission_bid=10010 status=3`**（**与 `missions` 一致**）✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | **`12419` 的专用实现**（复用 `build_mission_entry`）|
| `tools/_diag_r229.py` / `_diag_r229b.py` | ★ **`124xx` 族 + 验证** |

---

## 七、目标② 累计成果（新目标 39 批）：**20 条实质升级**

| # | 成果 | 数据源 |
|---|---|---|
| R196–R200 | `19600`/`15204`/`16601`/`16602`/`13906` | 各配置 |
| R204/R207–R209 | `10947`/`10526`/`11240`/`13802`/`13807` | `role_attr`/`bag_items` |
| R212–R213 | `10954-10957`/`10601` | `equip_items`/`role_attr` |
| R214/R217–R219 | `11600`/`15700`/`11210`/`18907`/`10202`/`10203` | 各表 |
| R227 | `11010` | `roles` |
| R228 | `11221`/`11224` | `role_heros` |
| **R229** | **`12419`** | **`missions`** |

---

## 八、下一批

| 族 | 条数 | 方向 |
|---|---|---|
| ★★ **`187xx`（15）** | 跑玩法 | `config_dragon` |
| ★ **`133xx`（14）/ `135xx`（13）** | 社交/限购 | 看 SC |
| ★ **`124xx`（8，已去 1）** | 任务 | `missions` |
| ★ **`132xx`（9）** | 组队 | 看 SC |
