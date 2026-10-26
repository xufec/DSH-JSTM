# R64：`initData` 的真相 —— `mon_cfg` 就是 `SC_15402` 本身；`mon_bid` 来自 `SC_12400.target`

> 本轮把 `GhostMon:initData` 逐条反汇编读完，**两个字段的来源被彻底钉死**，
> 并据此把 `target` 填成真实怪 bid（`Config.Mon[10105]` 已核实存在）——
> **四个条件全部满足，客户端仍不建怪**。
> 同时**更正**了前三轮的一个误判（`10051` 变 1 不是客户端推进的）。
> **时间**：2026-09-29 14:12 – 14:25。

---

## 一、★ `GhostMon:initData(data)` 的逐条真相（`ghost_mon` proto#1，bc=38）

```lua
function GhostMon:initData(data)
    GlobalEvent:getInstance():Fire(SideBarEvents.SELECT_TAB_BTN, 1)
    self.mon_cfg = data                    -- ★★★ 整个 SC_15402 包**就是** mon_cfg
    self.mon_bid = 0
    local mis = MissionCtrl:getInstance():getMissionData():getMission(data.mission_bid)
    if mis then
        self.mon_bid = mis.mis_target      -- ★★★ mon_bid 唯一来源
        self:createMon()
    end
    if self.select then self:killMon() end
end
```

| 字段 | 来源 | 结论 |
|---|---|---|
| **`mon_cfg`** | **= `SC_15402` 整包** | 所以 `createMon` 里的 `mon_cfg.map_bid / x / y` 就是我们发的 `map_bid/x/y` ⇒ **条件②③由我们的包内容决定** |
| **`mon_bid`** | **`mis.mis_target`**（客户端本地该任务的字段） | 而它由 **`SC_12400.missions[].target:u32`** 填充 ⇒ **服务端唯一能填的地方** |

⇒ 这把 `createMon()` 的四个早退条件全部变成"服务端可控"：

```
① self.mon_bid 非空      ← SC_12400.target 决定
② self.mon_cfg == data   ← SC_15402 整包（永远非空）
③ getSceneId()==data.map_bid ← 需要玩家在该场景（R62 已能送）
④ Config.Mon[mon_bid]    ← SC_12400.target 必须是真实怪 bid
```

---

## 二、✅ 按此把条件补齐（并核实 `Config.Mon`）

| 条件 | 本轮取值 | 证据 |
|---|---|---|
| ① `mon_bid` | **10105** | `SC_12400.target=10105`（DB `missions[10010].target`） |
| ② `mon_cfg` | `SC_15402` 包 | `mission_bid=10010, map_bid=10005, (10,58)` |
| ③ 场景 | **10005** | 推 `10200 bid=10005`，R62 已真机确认切图成功 |
| ④ `Config.Mon[10105]` | **存在** | `mon_def(10105) = {'name': '圣灵教精英', 'res_id': 'H34800'}`（`config_mon.json` 2645 条） |

另一条证据：`config_guaji` 里 lev 65–74 段正是 `{mon_bid: 10105, map_bid: 10005, disc: '乾坤日月谷'}`。

**真机执行（四条件齐备）**：
```
[14:16:08] >> cmd=15400 → << 15400 SC_15400 code=1
[14:16:08] << 10200 SCRoleEnter (server push) bid=10005 (68,62)
[14:16:11] << 15402 主动推 SC_15402 mission_bid=10010 map_bid=10005 (10,58)   ← 与 10200 间隔 3s
之后：只有心跳
```

⇒ **仍无任何后续包**。R59–R64 **累计否证 9 个假设**。

---

## 三、★ 更正：`10051` 反复变成 1 **不是客户端推进的**

R59/R60/R61 三次观察到"客户端的任务状态被推进"（`10051: 2 → 1`），并据此推断"任务链是通的"。
**本轮查清了：那是服务端自己的行为。**

`mission_rows()`（`mock_server.py` L2619 附近）在**每次**被调用时都会做"链头归一"并**写库**：

```python
_head = <chain 里第一个 status<3 的任务>
for k, m in rows.items():
    ...
    if k == _head:
        if st != 2: db_save_mission(..., {'mission_status': 2})   # 链头 → 2
    elif st == 2:
        db_save_mission(..., {'mission_status': 1})               # 其它在途 → 1  ★
```

⇒ 我把 `10010` 设为在途后，`10010` 成了链头，于是 `10051` 被服务端自己改成 1。
**与客户端无关。** 原结论撤回。

> 顺带发现两处副作用（本轮已清理）：
> ① 该归一化**会写库**，属"读取即修改"——建议加开关或改成只在推送前算一次；
> ② 实验期间 `missions` 被 seed 出 `10052/10053/10054` 三行（实验前只有 5 行），**已删除还原**。

---

## 四、结论与下一步

**九次黑盒实验全部否证** ⇒ 变量空间（轮次/推送时机/任务在途/场景/怪 bid）**已经穷尽**，
而四个条件按反汇编都该满足却仍不建怪。**继续猜下去收益为负。**

**唯一能给出答案的是探针**（R62/R63 报告里已列 5 个上报点）：

| 要观测 | 位置 |
|---|---|
| `GhostCtrl.handle15402` 有没有被调用 | 包装该方法 |
| `mon_hongchen` 实例是否存在 | `GhostCtrl` 实例字段 |
| `initData` 里 `mon_bid` / `mis_target` 实际是多少 | `initData` 尾部 |
| `createMon()` 在哪一条早退返回 | 三个 `return` 前各插一条 |
| 那一刻 `getSceneId()` 是多少 | 同处 |

代价是一次 APK 重打包（`patch_fake_login.py → zipalign → apksigner → adb install -r`），
**会替换玩家正在用的客户端** ⇒ 需要明确许可才执行。

---

## 五、收尾（全部还原 + 全绿）

| 项 | 值 |
|---|---|
| 玩家 | `rid=1001` / lev=70 / gold 841046 / 背包 27 / 场景 10001 |
| `missions` | **已还原为实验前的 5 行**：10010=3、10020=3、10030=3、10040=3、10051=2（`10010.target` 已回 0；实验 seed 的 10052~10054 已删） |
| `guaji_state` | `loop_count = 0` |
| `config.json` | `guaji_push_15402=true`（正式行为）、`guaji_enter_scene=**false**`、`guaji_enter_scene_delay=3.0`、`guaji_push_15402_on_enter=false`、`guaji_push_15401=false` |
| 服务端 | 在线，9000 恰好 1 监听，`stderr` **0 字节** |
| 六道门禁 + 回归 | 全绿（lint 0 遮蔽 / CS 2463-0 / SC 静态 85+1空-0 / SC 在线 86-86 / 专用 63-63 / 门禁 E PASS；6 个 verify 全 PASS） |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `tools/exp_mission_target.py` | **新增**：查/改/还原 `missions.target` + `mission_status`（本轮实验 D/E 用它，可重跑） |
| `analysis/1.4.9/round64_initdata_truth.md` | 本报告 |
| `analysis/_ghost_mon.txt` | `initData`（proto#1）与 `createMon`（proto#3）真源 |

---

## 七、一句话

> **`mon_cfg` 就是 `SC_15402` 整包，`mon_bid` 就是 `SC_12400.target`** —— 两个字段来源现在都是硬证据。
> 四条件按此全部补齐（含 `Config.Mon[10105]=圣灵教精英` 已核实），**客户端依旧不建怪**。
> **黑盒到此为止：要么上探针，要么先做别的。**
