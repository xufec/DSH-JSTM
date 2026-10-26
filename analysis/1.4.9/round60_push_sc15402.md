# R60：按取证结论**改成服务端主动推 `SC_15402`** —— 以及缺的那一环

> 项目方指定了三步。本轮把 **① 反汇编调用者** 与 **③ 改成主动推** 都做完了，并在过程中
> **找到了"推了但客户端不动"的下一环**。
> **时间**：2026-09-29 13:30 – 14:00。

---

## 步骤 ① ✅ `mon_hongchen` 的创建路径（结论：**客户端不会先发 15402**）

全 `ghost_ctrl` 里 `mon_hongchen` 只出现 **8 处**，逐个看完：

| proto | 方法（proto#38 类定义块给出名字） | 对 `mon_hongchen` 做什么 |
|---|---|---|
| #0 | `config` | 只声明字段 |
| #4 | （`showTitle` 相关） | **只读**：`if self.mon_hongchen then …` |
| #14 | `fight` | 只**调用**已存在的实例 |
| #16 | `createMon` | 只**调用**已存在的实例（`self.mon_hongchen:createMon()`） |
| **#30** | **`handle15402`（收到 `SC_15402`）** | ★ **创建**：`if not self.mon_hongchen then GhostMon:new('mis_hongchen') end` → `:initData(data)` |
| #32 | `handle15404`（收到 `SC_15404`） | `self.mon_hongchen:deleteMon()` |
| **#33** | **`killHuanBoss`（事件回调）** | ★ **创建**：同样的懒创建 → `:killMon(data)` |

**⇒ 只有两条创建路径**：
1. **收到服务端 `SC_15402`**（`handle15402`）—— 唯一的服务端驱动路径；
2. `killHuanBoss` —— 由 `registerEvents`（proto#5：`SCENE_ADDMON` / `SCENE_CLIENT_ELEM_CLICK` / `SCENE_SUCCESS_GHOST`）触发，
   而"场景里有挂机怪"本身又要先有 `createMon` ⇒ **仍以"实例已存在"为前提**。

而 `ghost_mon` proto#4 里那段"发 `CS_15402`"的代码，前提正是 `self.mon_hongchen` 已存在。

> **⇒ 结论（回答项目方的判断）：成立。 "客户端先发 15402"这条链不存在。**
> R48 当年看到的 `15402`，是**在我们答/推之后**客户端才发出来的（或被点击事件带出来的）。

---

## 步骤 ③ ✅ 已改成**服务端主动推** `SC_15402`，并真机验证"推得出去"

```python
# mock_server.py  if cmd == 15400:  （启动挂机成功应答之后）
if self.cfg.get('guaji_push_15402', True):
    _mb  = int(self.cfg.get('guaji_mission_bid') or 10010)   # 依据 R48 真机抓到的 10010
    _spot = guaji_spot_for_lev(lev) or {}                     # config_guaji 的等级段
    _map  = _spot['map_bid'] ; _x, _y = map_def_xy(_map)       # config_map 的 def_x/def_y
    self.request.sendall(pack_frame(15402, w_u32(_mb)+w_u32(_map)+w_u32(_x)+w_u32(_y)))
```

**载荷与应答实现完全同源**（同一份编码，已由 `tools/verify_guaji.py` 逐字节验证过）。
开关 `config.json: guaji_push_15402`（默认 `true`），置 false 即回到原行为。

**真机日志（推成功）**：

```
[13:48:55] >> cmd=15400 ? body(4)=00 46 00 3b
[13:48:55] << 15400 SC_15400 code=1(允许启动挂机)
[13:48:55] << 15402 主动推 SC_15402 mission_bid=10010 map_bid=10005 (10,58) （R60：客户端不发，必须服务端先给）
```

⚠️ 但客户端**无任何后续动作**（之后只有心跳）。

---

## ★ 缺的那一环：`initData` 要的是**客户端本地那条任务的数据**

`ghost_mon` proto#1（`initData`，bc=38）的字符串：

```
'killMon', 'select', 'createMon', 'mis_target', 'mission_bid',
'getMission', 'getMissionData', 'MissionCtrl', 'mon_bid', 'mon_cfg', ...
```

⇒ 结构是：

```lua
function GhostMon:initData(data)
    self.mission_bid = data.mission_bid                        -- 来自 SC_15402
    local mis = MissionCtrl:getInstance():getMission(...):getMissionData(self.mission_bid)
    self.mis_target = ...                                      -- ★ 来自**本地任务数据**
    self.mon_bid    = <mis_target.mon_bid 之类>                 -- ★ 同样来自本地任务
    self.mon_cfg    = Config.Mon[mon_bid]（或 Config.Guaji）    -- ★ mon_cfg 由它推出
    self:createMon()
end
```

**`mon_bid` / `mon_cfg` 都不在 `SC_15402` 里** —— 它们来自"**客户端本地这条 mission 的数据**"。

而我们的 `SC_12400` 因为 `mission_chain_max=1`（R44 为消重名而改）**只下发 `10051`**：
```
[13:51:36] << 12400 SC_12400 mission_list=1     ← 只有 10051
```
⇒ 客户端 `getMissionData(10010)` = **nil** ⇒ `mon_cfg` = nil ⇒ `createMon()` 直接返回。
**这就是"推了 `15402` 但客户端不动"的最合理解释。**

### 因此下一步要验的是**两个条件同时成立**

| 条件 | 现状 | 做法 |
|---|---|---|
| ① 服务端**主动推** `SC_15402{10010,…}` | ✅ 本轮已实现（真机推成功） | `guaji_push_15402=true` |
| ② 客户端**本地有 mission 10010** | ❌ 12400 只发 10051 | `missions[10010].mission_status: 3 → 2` |

本轮把 ①②**都布置好了**（10010 置 2 + 开关 true），但那次 `15400` 的**点击未命中**
（对话框已关/时间窗错过，连试 4 个坐标都是 0）⇒ **该组合尚未取得有效观测**。

复现命令（下一轮照做即可）：

```powershell
python tools\exp_mission_state.py --set 2          # 让 12400 带上 10010
# 重启客户端 → 日常(128,240) → 参与(1300,245) → 4019(1853,869)
# 判据（按顺序）：<< 13781 → >> 15405 → >> 15400 → << 15402(主动推) → 之后是否出现
#   >> 15402 / >> 15403 / >> 10200(bid=10005) / >> 124xx
python tools\exp_mission_state.py --set 3           # 收尾还原
```

---

## 收尾（真机与数据状态）

| 项 | 值 |
|---|---|
| 玩家 | `rid=1001` / lev=70 / gold 841046 / 背包 27 / 场景 10001 |
| `missions` | **已还原**：10010/10020/10030/10040=3、10051=**2** |
| `guaji_state` | `loop_count = 0` |
| `config.json` | `guaji_push_15402=true`（新，默认行为）、`guaji_mission_bid=10010`、`guaji_push_15401=false`（旧实验开关，保留） |
| 服务端 | 在线，9000 恰好 1 监听，`stderr` **0 字节** |
| 六道门禁 + 回归 | 全绿（lint 0 遮蔽 / CS 2463-0 / SC 静态 85+1空-0 / SC 在线 86-86 / 专用 63-63 / 门禁 E PASS；`verify_guaji`、`level_consistency`、`race`、`arena`、`dungeon`、`mission_hook` 全 PASS） |

> ★ 注：两次真机实验期间，客户端**把 `10051` 的 `mission_status` 从 2 推进到了 1**
> （说明任务链本身是通的）—— 这是玩家数据改动，**已两次都还原为 2**。

---

## 产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `15400` 应答成功后**主动推 `SC_15402`**（含完整取证事由注释） |
| `tools/_fix_r60_cfg.py` | `guaji_push_15402` / `guaji_mission_bid` 写入脚本（幂等） |
| `analysis/_ghost_mon.txt` | `ghost_mon.luac` 全量反汇编（`initData` / proto#4 发送条件真源） |
| `analysis/_ghost_dis.txt` | `ghost_ctrl.luac` 全量反汇编（8 处 `mon_hongchen`） |
| `analysis/1.4.9/round60_push_sc15402.md` | 本报告 |

---

## 一句话

> **步骤①成立：客户端不会先发 `15402`，只能由服务端先给；步骤③已改成主动推并真机推成功。**
> **但 `initData` 还要"客户端本地有这条 mission"才能推出 `mon_bid/mon_cfg`** ——
> 而我们的 `12400` 只发 `10051`。**下一轮只需让 `12400` 带上 `10010`，两个条件就齐了。**
