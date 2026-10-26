# R140：实现 `13806`（摆摊）/ `16706`（VIP 道具）/ `13741`（建筑技能）+ ★ **修一个既存 bug**

> 新目标第 17 批。三条新实现之外，**发现并修复了一个之前就存在的 bug**（`16704` 读不到真实 VIP）。
> **时间**：2026-09-30 12:35 – 13:20。

---

## 一、三条新实现

| cmd | SC | 数据源 |
|---|---|---|
| **`13806`** | `{add_space:u8, goods_list:table(market_id:u32, item_bid:u32, item_num:u16, sell_num:u16, sell_type:u8, price:u32, time_out:u32)}` | ★ 新建 `role_market_goods`；**没上架 ⇒ 空（真话）** |
| **`16706`** | `{status:u8, qq:string, items:table(item:u32, num:u8)}` | ★ `status ← roles.vip_level`（**DB 直读**）；`qq` 空串；`items` 空表 |
| **`13741`** | `{lev:u8, learn_list:table(item_bid:u32)}` | ★ 新建 `role_build`/`role_build_learn`；读真实 DB |

★★ `13741` 的 `learn_list:table(item_bid:u32)` 是**一行一字段**的表 ⇒ `cnt` = 已学条数
（这是 R128 教训的**正常**用法；`attr_list` 那种"一行 12 字段"才是特例）。

### 实测

```
== 13806 摆摊 ==
  未上架: len=3 err=None 条目=0
  上架后: len=24 消耗=24 err=None 条目=1 item_bid=21903     ← ★ 真实反映
== 16706 VIP ==
  vip=0 ⇒ status=0 ｜ vip=3 ⇒ status=1                      ← ★ 随真实 VIP 变化
== 13741 建筑技能 ==
  未学: lev=0 列表=0 ｜ 学习后: lev=5 列表=2                 ← ★ 与 DB 一致
=== 结果: PASS ===
```

---

## 二、★★★★★ 发现并修复一个**既存 bug**：`vip_level` 读的是**会话缓存**

`16706` 第一版 FAIL（`vip=3` 却 `status=0`）。排查时**对比 `16704`**（VIP 状态，R103 实现）：

```
DB: roles.vip_level = 3
>> cmd=16704
<< 16704 SC_16704 vip_lev=0 status=0      ← ★ **16704 也读成 0**
>> cmd=16706
<< 16706 SC_16706 status=0（vip_level=0）
```

⇒ **不是新代码的问题** —— 两条都用 `role_state(self.cfg).get('vip_level')`，
而那是**会话开始时装载的配置**，`vip_level` 在里面是旧值（0），**不随 DB 变化**。

### 修

新增 `db_vip_level(rid)` —— **每次从 DB 直读** `roles.vip_level`，`16704` 与 `16706` 共用。

**修复确认**：
```
DB vip_level=3：
  16704 ⇒ vip_lev=3 status=1     ← ★ 原先读成 0，现已正确
  16706 ⇒ status=1
```

> ★ **这一类问题的命名**：**"读了会话缓存而不是 DB"**。
> 判据：凡是"**玩家状态类的数值**"（VIP/等级/资产/已学列表…），
> 都应该**每次从 DB 读**，或在写入后**使缓存失效**。
> 本次是"同一根因影响两条命令"，值得单独记一笔。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **255** / 默认 32 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 38-38** / **专用 92-92** / 门禁 E **PASS** |
| 回归（**28 项**） | **新增 `verify_market_vip_build.py`** + 前 27 项 **失败数 0** |
| 判定表 | **B 26 / C 0 / A 255** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `market_goods`/`db_market_goods_add`、`db_build_state`/`db_build_set`、**`db_vip_level`** + `13806`/`16706`/`13741`；**并修 `16704`** |
| `tools/verify_market_vip_build.py` | **新增回归第 28 项**（含容错的 `ex()`）|
| `tools/_fix_r140_market_vip_build.py` / `_fix_r140b_vip_db.py` | 实现 + 修 bug |
| `tools/_emitted_empty_allow.json` | 新增 3 条理由 |
| `server/mock_server.py.bak_r140` | 改前备份 |

---

## 五、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **41** | **−26** |
| **专用分支** | 208 | **255** | **+47** |
| **B 类（有依据地不做）** | 57 | **26** | **−31** |
| **回归项** | 17 | **28**（失败 0）| **+11** |
| 六道门禁 | — | **全 PASS** | — |
| **C 类** | 10 | **0** | ★ 清零（保持）|

### 下一批

| 目标 | 依据 |
|---|---|
| ★ **排查同类"会话缓存"问题** | 用 `role_state(self.cfg)` 读**玩家状态**的地方都可能中招 ⇒ 系统性复查 |
| `13569`（祈福）| `info:table` 无配置源 ⇒ 结构正确的空表 + 登记 |
| `scan_growth_cmds.py` 剩余动作 | 座椅 `20803`–`20809`、翅膀 `11602`–`11607` |
