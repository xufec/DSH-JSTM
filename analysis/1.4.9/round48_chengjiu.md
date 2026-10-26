# R48 续：`num` 取证定论 + 成就（`164xx`）打通（2026-09-19）

> 承接 `round48_daily.md`。本轮完成三件项目方指定的事：
> ① 补完 `num` 取证；② 做成就；③ 把"重启窗口纪律"写进 HANDOVER。

---

## 一、★ `num` 取证：**一次点击定论**

服务端跑着"`13786.richang_list` 用**面板 id**"的实验版，DB 里学院任务 `num=1`。
在真机上点开日常面板（**未重启服务端**，遵守新纪律），截图读数：

```
学院任务：次数 1/10    ← 从 0 变 1 ✅
         活力 10/70
底部：拥有活力 10/1420
```

### 取数分工（三条都已在真机验证）

| 面板上的东西 | 来源 | 证据 |
|---|---|---|
| **拥有活力** | `SC_13781.total_val` | 写 val → 底部 0/1420 变 10/1420 |
| **每任务活力** | `SC_13781.huoli_list[**huoli_id**].val` | 学院任务活力 0/70 → 10/70 |
| **每任务次数** | **`SC_13786.richang_list[面板id].num`** | 学院任务次数 0/10 → **1/10** |
| ~~每任务次数~~ | ~~`SC_13781.huoli_list[].num`~~ | **已否证**：给它 num=1 时次数仍 0/10 |

⇒ 代码已把实验注释改为定论，并把这三行分工写进 `mock_server.py` 注释，防止后人再猜。

---

## 二、成就（`164xx`）：表已抽出、`16400` 已打通

### 2.1 协议与流量

`cmd_resolve_164.luac`：

```
CS_16400{type:C} → SC_16400{type:C,
    chengjiu:T{bid:I, val:H, time:I},             -- 有进度的成就
    chengjiu_has:T{bid:I, time_out:I, state:C},   -- 已获得/可领
    chengjiu_rate:T{bid:I, rate:C}}               -- 进度%
CS_16401{bid:I} → SC{code,msg,bid}                -- 领取
SC_16402{chengjiu:T{bid,time_out}} / SC_16403{chengjiu:T{bid,val,time}}
CS_16404{group:I} → SC{code,msg,chengjiu_rate:T{bid,rate}}
```

**真机 `16400` 发了 450 次**（body `0100000003` ⇒ type=1）；`16401~16404` 从未发过。
原状：`16400` 落在通用集合回**全零**，`16401~16404` 无 handler。

### 2.2 权威表：`config_chengjiu.luac` → `server/_chengjiu.json`

`tools/extract_chengjiu.py` 抽出 **342 条**，字段齐全：

```
{bid, name, desc, val(目标值), cent(成就点), group, type, type2,
 pre, post, title, show, open_lev, guider_id,
 trigger_mod, trigger_fun}     ← ★ 后两者是「进度由什么触发」的链接
```

例：

| bid | name | val | cent | trigger_mod | trigger_fun | desc |
|---|---|---|---|---|---|---|
| 10100 | 史莱克弟子 | 5 | 1 | `mission` | `hongchen` | 完成5轮学院任务 |
| 10101 | 学院能手 | 20 | 3 | `mission` | `hongchen` | 完成20轮学院任务 |
| 10200 | 走过一轮 | 20 | 2 | `mission` | `zhuoyao` | 完成20轮监察任务 |
| 10330 | 凤仪是真爱 | 1 | 2 | `escort` | — | 护送凤仪1次 |
| 10500 | 赏金新手 | 10 | 1 | `mission` | `7` | 悬赏10次 |

⇒ `desc` 直接写明要求，`val` 就是目标值，`trigger_mod/fun` 指向前置行为。
**这是本项目迄今最"可实施"的一张表**：进度的触发链第一次有了明确字段。

### 2.3 实现

- 新增 `server/_chengjiu.json`（342 条）+ `chengjiu_progress(rid,bid,val)` 表 + `db_chengjiu_*`
- `16400` 改为 DB 驱动：
  - `chengjiu` = 有进度的成就（`val`=当前进度，取 DB）
  - `chengjiu_rate` = `rate` = 当前/目标×100（目标取自成就表 `val`，封顶 100）
  - **`chengjiu_has` 留空** —— 其 `state`（可领/已领）语义**未取证**，按纪律不猜；
    `16401` 领取流程同样未取证，本轮不做
  - `time` = 0（时间戳语义未取证）
- `/DSH_ADMIN/chengjiu?bid=10100&n=5` 写入路径（调参旋钮 + 可验证入口）
- **`16400` 已移出 `_GENERIC_DEFAULT_CMDS`**

**验证**（真机之外先做协议级）：

```
16400: len=22 解析=22 PASS
  chengjiu=1 条   bid=10100 val=5 time=0
  chengjiu_has= 0
  rate bid=10100 → 100%
```

---

## 三、★ 我自己犯的同源错误：**把 handler 插进了别的命令的嵌套块**

改完 `16400` 第一次验证：**完全无应答**。

根因：我把 `if cmd == 16400:` 插到了
`if cmd in (13781, 13786, 13787, 13788, 13789, 10925):` 这个**嵌套块内部**
⇒ 对 `cmd=16400` 永远不执行；而我又把它从通用集合移出了 ⇒ **没有任何分支接它**。

**这与"分发顺序遮蔽"是同一类错误的另一种形态**：

| 形态 | 后果 |
|---|---|
| 通用集合抢先 return（前四次） | 专用实现变**死代码**，回的是零值 |
| **handler 嵌进别人的 guard（本次）** | 专用实现**根本不执行**，且因已移出集合 ⇒ **无应答** |

⇒ **被自己的验证脚本当场抓住**（"期望有应答、实际超时"）。这再次说明：
**改完必须真跑一次该命令**，而不是靠读代码确认。

**建议**（下次实现）：把 `lint_dispatch_shadow.py` 扩成两项检查——
除了"集合成员 ∩ 专用分支"，再加 **"`if cmd == N:` 的缩进是否落在另一个 `if cmd …` 块内"**。

---

## 四、HANDOVER 已更新（项目方指定）

新增两节：

- **§5.5 ★★ 真机共存纪律**（5 条，每条对应一次真实事故或险情）
  1. **不要在客户端"面板已打开/等应答"时重启服务端** ← R48 的 ANR 事故
  2. 不要为"回到干净状态"而还原 `roles.db`（会毁玩家进度）
  3. 有玩家时不要跑 `replay_captures.py`（会真扣费/发货）⇒ 改用三道无副作用审计
  4. 测试数据只写测试账号，结束即清理
  5. 重启前先看 `tcp.log` 尾部判断客户端是否空闲（3 秒，避免第 1 条）
- **§5.6 ★ 真机取数：用 adb 主动驱动 MuMu**
  （含连接方式、包名、**2560×1440 横屏**要点、`locate_in_image` 不可用时的 PIL 替代法、
  以及"以服务端是否收到该 cmd 作为面板真的打开了"的判据）

---

## 五、复核

| 项目 | 结果 |
|---|---|
| `lint_dispatch_shadow.py` | **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 条：**0 不一致** |
| `audit_sc_conformance.py`（全量 1635） | **0 不一致** |
| `audit_sc_live.py --unsupported` | **89/89**（16400 移出，90 → 89） |
| `audit_dedicated.py` | **61/61** |
| 玩家角色 | `rid=1001 uid=dsh_local` 完好；游戏已从 ANR 恢复并回到主城 |

---

## 六、产出

| 文件 | 说明 |
|---|---|
| `tools/extract_chengjiu.py` | 抽取 `config_chengjiu` → 342 条成就表 |
| `server/_chengjiu.json` | 成就表产物 |
| `server/mock_server.py` | `chengjiu_progress` + `db_chengjiu_*`；`16400` DB 驱动（**顶层**）；`/DSH_ADMIN/chengjiu`；`13786` 定论注释；`16400` 移出通用集合 |
| `docs/HANDOVER_移交给另一个agent.md` | 新增 §5.5 真机共存纪律 / §5.6 adb 取数法 |
| `analysis/1.4.9/round48_chengjiu.md` | 本报告 |

---

## 七、下一步（★ 第一次有了明确的进度触发链）

成就表里的 `trigger_mod` / `trigger_fun` **就是"进度由什么触发"的字段**
⇒ 下一步可以不再"靠 admin 写入造数据"，而是**按触发链真实挂钩**：

1. **`mission` + `hongchen`/`zhuoyao`**：找 `config_mission` 里对应的任务组
   （成就 10100「完成5轮学院任务」↔ 日常 208「学院任务」很可能是同一组）
   ⇒ 若能对上，**一次挂钩同时喂饱"日常次数"与"成就进度"**，两边都真实增长；
2. `escort`（护送）、`vip_single`（通关副本）、`mission`+数字（悬赏）同理；
3. `16401`（领取）与 `13787`（活力档位领取）待取证后实现。
