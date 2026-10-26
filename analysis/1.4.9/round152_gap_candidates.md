# R152：★ 新工具 `classify_gap.py` —— 从 1144 条缺口里**精准筛出真候选**

> **新目标第 1 轮**。上一目标完成的是"真机发过的"命令；本目标推进 **1144 条潜在缺口**
> （它们现在只走 R151 的全局兜底 = **空表**，还没有真实数据）。
> **时间**：2026-09-30 19:40 – 20:20。

---

## 一、★ 新工具：按"家族 + 字段独特性"两级筛选

`tools/classify_gap.py`（本批新增）做了两件事：

### ① 家族聚类（1144 条的分布）

| 家族 | 条数 | 家族 | 条数 |
|---|---|---|---|
| `13xxx` | **226** | `20xxx` | 69 |
| `10xxx` | **146** | `19xxx` | 60 |
| `18xxx` | **128** | `30xxx` | 58 |
| `12xxx` | 111 | `17xxx` | 57 |
| `11xxx` | 84 | `15xxx` / `14xxx` | 44 / 43 |
| `16xxx` | 72 | `31xxx` / `21xxx` | 24 / 22 |

### ② 字段独特性筛选（**关键创新**）

★ 简单的"字段名能对上配置"**不可信** —— `bid`/`time`/`coin`/`lev` 这类
**通用名会与几十张配置撞车**（R147 已踩过）。

⇒ 本工具改用：**只保留出现在 ≤2 张配置里的字段**（"高独特性"），
且要求 **SC 里至少 2 个**这样的字段命中：

```
高独特性字段（出现在 ≤2 张配置）: 3051 个
★★ 真候选（SC 里 >=2 个高独特性字段命中）: 22 条
```

**22 条真候选**（部分）：

| cmd | SC 关键字段 | 候选配置 |
|---|---|---|
| **`18400`** | `merge_index, tar_val` | ★ **`config_group_control`（唯一命中）** |
| **`12414`** | `mission_bid, npc_bid` | `config_guild_mission` / `config_mission_escort` |
| **`14204`** | `mission_bid, assets_list` | `config_guild_mission` / `config_item_gift` |
| **`13326`** | `courage, charm` | `config_game_data` / `config_sns` |
| `10529`/`10541`/`11201` | `score, power` / `grade, power` | `config_dan_war` / `config_skill_xiulian` |
| `10947`/`10954`–`10957` | `stage, power, skill_list` | `config_eqm_ancient` / `config_insight` |
| `16610`/`16634`/`16636` | 活动/礼包 | `config_global_wish_data` / `config_lucky_box_data` |

---

## 二、本批实现 4 条（**都有真实依据**）

### `18400`（合服/世界进程）—— 配置里**唯一命中**

```
SC_18400{is_open:u8, merge_index:u8, step:u8, status:u8, val:u16, tar_val:u16}
```
`config_group_control`：
```
GroupControl[1] = {name:"世界连接", min_lev:45, days:4, ★tar_val:7000,
                   first_desc:"击杀50级世界首领", …}       ← 共 32 项
ControlSys[2000] = {name:"跨服聊天", ★is_open:1, need_step:1}   ← 共 9 项
```
⇒ **`tar_val` 取配置的 7000**；`is_open` 由 `ControlSys` 算；`val`（玩家进程值）无源 ⇒ **0（真话）**。

### `13326`（看他人社交信息）—— 本服只有自己

```
SC_13326{rid,srv_id,name,career,is_online,courage,charm,send_num,send_list}
```
⇒ 用**真实的 name/career** + **`courage`/`charm`**（R137 已存 `role_assets`）；
`send_list` 无赠送行为 ⇒ 空（登记）。

### `12414` / `14204`（NPC 对话校验 / 任务奖励预览）
⇒ 回显 `mission_bid`/`npc_bid` + `code` 如实；`14204` 回**真实** `mission_bid`。

### 实测（**核对真实值**）

```
== 18400 ==  len=8 err=None is_open=1 tar_val=7000（配置 7000）✓
== 13326 ==  name='DSH' career=1 online=1 courage=321 charm=654 ✓（courage/charm 是刚置进去的）
== 12414 ==  mission_bid=23001 npc_bid=80001 code=1 ✓
== 14204 ==  mission_bid=23001 ✓
=== 结果: PASS ===
```

---

## 三、★ 本批两次自纠（都记录）

| # | 现象 | 真因 | 修 |
|---|---|---|---|
| ① | 补丁第①步**没生效** ⇒ `18400` 抛 `NameError` ⇒ **连接被关** | **替换锚点用了"我要加的那个函数名"**（它本来不存在）| 锚点改为**已存在的** `def dungeon_cfg():` |
| ② | verifier 报 `unpack_from` 越界 | **我把 `tar_val` 的偏移算成 8**（应为 **6**：`1+1+1+1+2` 之后）| 改 offset 并写明布局 |

> ★ ①的教训与 R143c 同源：**改完必须用工具复核**（`Select-String` 确认锚点命中）。
> ②是"手算偏移"的老毛病 ⇒ **结构断言一律用门禁权威解析器**，手写只用于取值。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **306** / 默认 21 / 未开放 6）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 100-100** / 门禁 E **PASS** |
| 回归（**36 项**） | **新增 `verify_gap_candidates.py`** + 前 35 项 **失败数 0** |
| 判定表 | **B 15 / C 0 / A 306** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| **`tools/classify_gap.py`** | ★ **1144 条的分类器**（家族聚类 + 字段独特性筛选）|
| `analysis/1.4.9/_gap_classify.md` | 分类报告 |
| `server/mock_server.py` | `group_control_cfg`/`group_first_tar_val`/`group_is_open` + `18400`/`13326`/`12414`/`14204` |
| `tools/verify_gap_candidates.py` | **新增回归第 36 项** |
| `tools/_fix_r152_gap_candidates.py` | 插入脚本 |
| `server/mock_server.py.bak_r152` | 改前备份 |

---

## 六、新目标进度

| 指标 | 上一目标结束 | 现在 | 变化 |
|---|---|---|---|
| **专用分支** | 302 | **306** | **+4** |
| **回归项** | 35 | **36**（失败 0）| **+1** |
| 六道门禁 | 全 PASS | **全 PASS** | — |
| ★ **真候选池** | 未分类 | **22 条**（已做 4）| ★ **本批建立** |
| 潜在缺口 | 1144（空表兜底）| 1140 条仍空表 + **4 条真实数据** | — |

### 下一批（按候选池推进）

| 目标 | 依据 |
|---|---|
| `10529`/`10541`/`11201`（`score`/`grade`/`power`）| `config_dan_war` / `config_skill_xiulian` |
| `10954`–`10957`（`stage`/`skill_list`）| `config_eqm_ancient` / `config_insight` |
| `16610`/`16634`/`16636`（活动/礼包）| `config_global_wish_data` / `config_lucky_box_data` |
| ★ 把"字段独特性"筛法**推广到 10xxx / 13xxx 大族** | `classify_gap.py --family` |
