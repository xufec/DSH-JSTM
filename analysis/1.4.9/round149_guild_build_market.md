# R149：一次补 6 条"能读**已建表**"的真机缺口（专用分支 296 → 302）

> 新目标第 25 批。这几条的共同点：**数据源都是我在 R121/R125/R131 建好的表**
> —— 一次把它们接上，是"补获得途径"的**自然收尾**。
> 时间：2026-09-30 17:25 – 18:00。

---

## 一、6 条与其数据源

| cmd | SC | 数据源（**都已建**）| 实测 |
|---|---|---|---|
| **`13501`** | `{page, page_total, guilds:table(**17 字段**), all_count}` | ★ `role_guild` + `role_state` + `role_power` + `db_vip_level` | `guild_name='验收宗门' head_name='DSH'` **与 DB 一致** ✓ |
| **`13701`** | `{type, lev}` | ★ `role_build.lev` | `lev=7` ✓ |
| **`13702`** / **`13703`** | `{code,msg,type,lev}` | ★ 同上 | `lev=7` ✓ |
| **`13801`** | `{left_time, type, cur_page, max_page, goods_list:table(7)}` | ★ `role_market_goods`（同 `13806`）| 结构精确 ✓ |
| **`13227`** | `{team_num:u16, role_num:u16}` | ★ **数 `roles` 表** | `role_num=1`（= DB）✓ |

### ★ `13501` 的 `guilds` 有 **17 个字段**（R143b 的纪律：先看完整列表）

```
index, gid, srv_id, realm, vip, guild_name, head_name, head_career, lev,
role_count, max_role_count, applyed, power, all_assets, is_recommend, head_sex, is_invited
```

其中 **6 个能取真实值**：
- `guild_name` ← **`role_guild.name`**
- `head_name` ← **角色名** / `head_career` ← 职业 / `head_sex` ← 性别
- `vip` ← **`db_vip_level()`**（R140b 加的 DB 直读）
- `power` ← **`role_power()`**
- `role_count` ← 1（本服 1 人）

⇒ 一条**真实的宗门条目**（不是空表）✓

---

## 二、★ 又一个我自己的小错：验收脚本的 `import` 放错位置

`verify_guild_build_market.py` 第一版报 `NameError: name 'json' is not defined`
—— 我把 `import json` 写在了 `main()` 里，而模块级的 `adm()` 在用它。
⇒ **修**：import 移到**模块顶部**。

> ★ 小但典型：**helper 函数用的模块要么在顶部 import，要么在函数内部 import** ——
> 不能期望"调用顺序"帮你兜住。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **302** / 默认 21 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 99-99** / 门禁 E **PASS** |
| 回归（**35 项**） | **新增 `verify_guild_build_market.py`** + 前 34 项 **失败数 0** |
| 判定表 | **B 15 / C 0 / A 302**（未实现 **27**）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

★ 注意 **`默认集合` 从 31 降到 21** —— 因为本轮又移出了 6 条。

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `role_count`/`guild_rows` + `13501`/`13701`-`13703`/`13801`/`13227` |
| `tools/verify_guild_build_market.py` | **新增回归第 35 项**（含真实值核对）|
| `tools/_fix_r149_guild_build_market.py` | 插入脚本 |
| `server/mock_server.py.bak_r149` | 改前备份 |

---

## 五、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **27** | **−40** |
| **专用分支** | 208 | **302** | **+94** |
| **B 类（有依据地不做）** | 57 | **15** | **−42** |
| **回归项** | 17 | **35**（失败 0）| **+18** |
| 六道门禁 | — | **全 PASS** | — |
| **C 类** | 10 | **0** | ★ 清零 |

### ★ 剩余 27 条的构成（已逐类判定）

| 类别 | 条数 | 判据 |
|---|---|---|
| 社交域（队伍/好友/召回/结拜对象）| ~12 | **1 个角色** ⇒ 空即真话 |
| 无配置源（祈福/转盘/签到/关卡/活动）| ~8 | 空表 = 默认响应 ⇒ **零增量** |
| 语义未取证（NPC `15204`/任务 `19500`）| ~4 | **不猜** |
| 其它（录像/上传）| ~3 | **事件未发生** ⇒ 空即真话 |

### 下一批

| 目标 | 依据 |
|---|---|
| ★ **启用全局兜底**（`global_default_sc`）| 让 **1144 条**潜在缺口都有安全应答 |
| 复核六道门禁基线 | 本轮"默认集合"已从 49 降到 **21** |
