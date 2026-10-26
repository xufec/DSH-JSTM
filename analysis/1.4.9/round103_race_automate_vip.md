# R103：补完三个系统 —— `race`(17306/17308/17310/17312) + `automate`(10932) + `vip`(16704)

> 按 R102 的地图，实现三个系统共 **6 条命令**。
> 原则不变：**能指到真实数据源的就发真实值；指不到的一律空表/诚实 msg + 登记理由**。
> **时间**：2026-09-29 01:25 – 01:55。

---

## 一、逐条处置与依据

| cmd | 规格 | 处置 | 依据 |
|---|---|---|---|
| **16704** | `{vip_lev:u8, status:u8}` | `vip_lev = roles.vip_level`；`status = 1 if vip_lev>0 else 0` | ★ `roles` 表**真实字段 `vip_level`** |
| **10932** | `{double:u16, double_sum:u16, double_state:u16, off_state:u16}` | **`off_state` 由 `guaji_state` 是否有行推导**；其余 0 | ★ 本服 `guaji_state` **有真实行** ⇒ 离线挂机可用是真话；**没有双倍经验也是真话** |
| **17312** | `CS{type:u8}` → `{code:u8, msg:string}` | **`code=0` + 诚实 msg**（`本服未配置竞速奖励`）| ★ 竞速**没有奖励配置源**（`config_game_data`/`config_week_calendar` 只在文字里提到"竞速"，**不是奖励表**；APK 内也没有 `config_race*`）⇒ **不假装成功** |
| **17306** | `{reward_list:table(type:u8,num:u8,status:u8)}` | **空表**（+ 登记理由）| 同上（无奖励档位配置）|
| **17308** | `CS{start_rank,end_rank}` → `{rank_list:table(role_name,rid,srid,rank,career,sex,score,lev,win_num)}` | **空表**（+ 登记理由）| ★ `roles` **只有 1 个角色** ⇒ **没有排名竞争是真话** |
| **17310** | `{score_list:table(grade:u32, number:u32)}` | **空表**（+ 登记理由）| 同上（分数段人数分布需要多玩家）|

★ `race_state` 表已有（R50），**1001 没有行** ⇒ 竞速状态全 0 是**真话**（还没打过）。

### 实测

```
SC_16704 vip_lev=0 status=0  len=2                 ← roles.vip_level 真实值
SC_10932 double=0 sum=0 state=0 off_state=1  len=8 ← ★ off_state=1（guaji_state 有行）
SC_17312 code=0 msg='本服未配置竞速奖励' 解析=30/30 PASS
SC_17306 reward_list=0  len=2
SC_17308 rank_list=0  len=2
SC_17310 score_list=0  len=2
```

> 报告一句自查：第一次验证 `17312` 的 msg 时我读偏了 1 字节（`u16` 长度前缀从 offset 1 开始，msg 数据从 **3** 开始），
> 显示成乱码；**那是我验证脚本的错，不是服务端的** —— 重读后 `解析=30/30 PASS`。

---

## 二、★★ 本轮门禁**当场抓到我自己引入的遮蔽**

插入 `17312` 后，`tools/lint_dispatch_shadow.py` 立刻报：

```
★ 被 _UNSUPPORTED_ACTION_CMDS 遮蔽的专用实现（1 条）：
  17312   ⇒ 请从集合中移出。
```

⇒ `17312` 原本在**"未开放"集合**（回 `code=0 未开放`）里，它会**遮蔽**我刚写的专用实现。
修：从 `_UNSUPPORTED_ACTION_CMDS` 移出后门禁恢复 `✓ 无分发遮蔽`。

> ★ **这是本项目第一次"门禁在我写完的同一轮里抓到遮蔽"** —— 之前 9 次遮蔽都是事后由用户报障发现的。
> 说明 R86/R99 把"跨形式 + 缩进分层"补进 `duplicate_dedicated()` 是有效的：
> 它现在**同时**检查 `_GENERIC_DEFAULT_CMDS` 与 `_UNSUPPORTED_ACTION_CMDS` 两条遮蔽路径。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **193** / 默认 **52** / 未开放 **21**）/ CS 2463-0 / SC 静态 **73+1空-0** / SC 在线 **73-73** / 专用 **74-74**（+4）/ 门禁 E **PASS**（长度不符 0 / 空表告警 0，本轮登记 3 条）|
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / **`verify_race`** / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `16704`/`10932`/`17312`/`17306`/`17308`/`17310` 六个处理器；从 `_GENERIC_DEFAULT_CMDS` 移出 5 条、从 `_UNSUPPORTED_ACTION_CMDS` 移出 `17312` |
| `tools/_fix_r103_race_automate_vip.py` | 插入脚本 |
| `tools/_fix_r103_allow_empty.py` | 三条空表的理由登记（白名单 87→90 条）|
| `server/mock_server.py.bak_r103` | 改前备份 |
| `analysis/1.4.9/round103_race_automate_vip.md` | 本报告 |

---

## 五、一句话

> **三个系统 6 条命令全部落地**：`16704` 发**真实的 `roles.vip_level`**；
> `10932` 的 `off_state` 由 **`guaji_state` 真实行**推导（=1，你正在挂机）；
> `17312` 领奖**回 `code=0` + 诚实 msg**（竞速没有奖励配置，**不假装成功**）；
> `17306`/`17308`/`17310` 空表 + 登记理由（**没有奖励配置 / 本服只有 1 个角色**）。
> ★ 本轮门禁**在我写完的同一轮就抓到了我自己引入的 `17312` 遮蔽** —— 这是第一次"遮蔽在合并前被发现"。
