# R93–R97：伙伴/阵型 UI —— **客户端内存侧探测的负面结论**（7 次重打包）

> 承接 R92 的下一阶段：主线的最后一环是"**数据到底有没有进客户端**"。
> 我连续做了 **7 次 APK 重打包**逐步收紧探针，最后得到一个**明确但负面**的结论。
> **本轮的产出是一个"不要再走这条路"的结论 + 一条可行替代路径**。
> **时间**：2026-09-29 22:35 – 23:00。

---

## 一、起点：服务端侧已经是干净的

用**门禁自己的严格解析器**跑线上包（R91 已做）：

```
SC_10401 len=274  消耗=274  err=None
SC_11215 len=2546 消耗=2546 err=None
SC_14000 len=35   消耗=35   err=None
```

⇒ 服务端数据、字段顺序、长度**全部合规**。那问题只能在客户端侧。
于是加了探针（`server/dsh_fake_login.lua` 的独立顶层块，与 R65 的 ghost 探针同款）**直接读客户端内存**。

---

## 二、7 次重打包的逐步收紧（全部实测）

| # | 探针 | 上报结果 | 结论 |
|---|---|---|---|
| 1 | `heroProbe`：读 `HeroCtrl:getInstance().data.hero_list` 条数 | `hero_list=nil … cfgPB=53` | 值取不到；但 **`Config.PartnerBase` 能读到 53 条** ⇒ 取值机制本身是通的 |
| 2 | `heroDiag`：读 `type(_G.HeroCtrl)` / 能否 `getInstance()` / `data` 的键 | **`HC=nil_FC=nil_view=n/a`** | ★ **`HeroCtrl` / `FormCtrl` 不是全局** |
| 3 | `globals`：枚举 `_G` 里名字含 `hero`/`form`/`wing` 的全局 | `hero=[CSHeroBag_10401:table, SCHeroAll_10403:table, …]`、`form=[mat4_transformVector,…]`、`wing=[]` | ★ **`_G` 里含 'hero' 的只有协议表**，没有任何 ctrl |
| 4 | `loaded`：扫 `package.loaded`（require 缓存）里的 `hero`/`form` 模块 | `hero=[game/hero/vo/partner_vo:boolean, …]`、**`lcount=34`** | ★ 本项目 `require` 缓存的值是 **boolean**（自定义 loader）⇒ **拿不到模块对象** |
| 5 | `singles`：扫 `_G` 里像单例的 table（`ctrl/mgr/data/model/…`）并试 `getInstance()`，看谁持有 hero/form 字段 | **只有 `CCGameLib` / `ScriptHandlerMgr`，都不持有** | ★ **没有任何全局能触达伙伴/阵型数据** |

---

## 三、★★ 结论（负面但**明确**，写下来免得后人重复走）

> **该项目的 Controller 实例被闭包隔离**：
> - 类定义块里那个 `GSET` 写的是 **chunk 级名字**，**不是 `_G`**（我最初误判成了全局）；
> - `require` 走**自定义 loader**，`package.loaded` 里只留 **boolean**；
> - `_G` 里能拿到的只有**协议表**（`CSHeroBag_10401` 等）与引擎类（`CCGameLib`／`ScriptHandlerMgr`）。

⇒ **探针无法从 `_G` / `package.loaded` 触达 `HeroCtrl`/`FormCtrl`**；
而"想 hook 它"也**无从下手**（连类都拿不到）。
**⇒ 客户端内存侧的黑盒探测到此为止。**

> 这次 7 次重打包不是白费：**它把一个"以为能做的事"证否了**，
> 并留下准确的**边界描述**（`_G` 里有什么、`package.loaded` 里是什么形态、哪些路走不通）。

---

## 四、★ 替代路径：**服务端对照实验**（不需要重打包，把判定权交给看得见屏幕的人）

既然"数据没进客户端"与"UI 过滤掉了"这两种可能**无法从客户端侧区分**，
那就**从服务端逐个改字段、让用户看屏幕**——一次实验锁定一个变量：

| 实验 | 改什么 | 预期判据 |
|---|---|---|
| A | `config.json: hero_state`：`1 → 0`（`10401.hero_bag[].state`） | 若界面反而出现/消失 ⇒ 就是 `state` 在过滤 |
| B | `11215` 的 `id` 全置 0（`/DSH_ADMIN` 加一个开关） | 若"阵型可选列表"变化 ⇒ 说明它读 `11215.id` |
| C | `10401` 临时只回 **1 个**伙伴 | 若界面从"空"变成"1 个" ⇒ 说明它**确实读 10401**，问题在**过滤**而非数据 |
| D | `SC_14000.hero_pos_info` 从 5 位改成 **0 位** | 若阵型位随之消失 ⇒ 上阵数据源确认是 `14000` |

★ 每个实验都**只改一个值**、**可秒级回退**（`/DSH_ADMIN` 接口），且**全部在服务端**。
★ 其中 **C 最有判别力**：它能一句话分开"数据没到"与"UI 过滤"。

---

## 五、全量验证（本轮服务端改动只有 R92 的 `14099`）

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 184 / 默认 58 / 未开放 22）/ CS 2463-0 / SC 静态 80+1空-0 / SC 在线 **80-80** / 专用 **67-67** / 门禁 E **PASS** |
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |
| 客户端 | **已装第 7 次重打包版**（含 5 组诊断探针）；旧版备份 `.bak_r93` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/dsh_fake_login.lua` | 新增 5 组探针：`heroProbe` / `heroDiag` / `globals` / `loaded` / `singles`（各自独立顶层块，含"为什么这么探"的注释） |
| `patched/jstm_fakelogin_aligned.apk` | 第 7 次重打包客户端（已装入 MuMu） |
| `server/dsh_fake_login.lua.bak_r93`、`patched/jstm_fakelogin_aligned.apk.bak_r93` | 改前备份 |
| `analysis/1.4.9/round93_97_client_probe_conclusion.md` | 本报告 |

---

## 七、一句话

> **7 次重打包换来一个明确的负面结论**：该项目的 ctrl 实例**被闭包隔离** ——
> `_G` 里只有协议表、`package.loaded` 里只有 `boolean`、没有任何全局能触达
> `HeroCtrl`/`FormCtrl` ⇒ **客户端内存侧的黑盒探测到此为止**。
> 下一步改用**服务端对照实验**（改一个字段 → 你看一眼屏幕），其中"把 `10401` 临时改成只回 1 个伙伴"
> **最有判别力**：能一句话分开"数据没到客户端"与"UI 把它过滤了"。
