# R69–R71：★★ 挂机链**零点击全自动跑通** —— 补 `15202` + 修 `10201` 场景 + **修推送顺序**

> 承接 R65/R66（探针证明 `createMon()` 成功）。本轮三件事全部落地，并**首次实现"登录即自动完成整条挂机链"**：
> ① 补上 `CS_15202`（`GhostMon:fight()` 发的就是它，此前**完全无人应答**）；
> ② 修 `_send_10200` 推 `10201` 用旧场景的 bug；
> ③ ★ **修推送顺序**：`15402` 必须在 `12400`（任务列表）**之后**推，否则 `mon_bid=0`。
> **时间**：2026-09-29 16:50 – 17:10。

---

## 一、★ ① 补 `15202`：`GhostMon:fight()` 的落点（此前完全无人应答）

`ghost_mon.luac` proto#5（`fight`）反汇编：

```lua
function GhostMon:fight()
    if self.mon_id then                                   -- 怪已存在才发
        proto = ProtocalRulesMgr:getInstance():GetPrototype(15202)   -- ★ CS_15202
        proto.mon_bid = self.mon_bid
        ProtocalRulesMgr:getInstance():SendProtocal(proto)
    end
    -- 其它 mis_key 分支同理（15302 …）
end
```

**查证**：`15202` 此前 **不在 `_GENERIC_DEFAULT_CMDS`、不在 `_UNSUPPORTED_ACTION_CMDS`、也没有专用分支**
⇒ 客户端发出去**没有任何应答**（干等）。**已补**：

```
CS_15202{mon_bid:u32} → SC{code:u8, msg:string}
  · mon_bid ∈ Config.Mon ⇒ code=1（允许开打；本服 20000~20099 战斗族已实现，回成功不是撒谎）
  · 否则 ⇒ code=0 + msg='未知怪物(N)'
```

---

## 二、★ ② 修 `_send_10200` 的 `10201` 场景错配

```python
sp_bid = int((self.cfg.get('spawn') or {}).get('bid') or 10001)   # ← 固定旧场景
```

切到 10005 之后紧跟的 `10201` 里 `npcs/mons/elems` 仍是 **10001（史莱克城）** 的配置
（日志里 `mons=1` 那只就是旧场景的）。**已改用传入的 `bid`**。

---

## 三、★★ ③ 修推送顺序 —— 这是"自动链 `mon_bid=0`"的真正原因

### 3.1 探针对照（同一个 `SC_15402`，两种结果）

| 场景 | 探针输出 | 结果 |
|---|---|---|
| `15402` 在 `12400` **之前**推（R70 自动链） | `ghcreate mon_bid_0 … hasMon_false / done_mon_id_nil` | ❌ `mon_bid=0` |
| `15402` 在 `12400` **之后**推（R65/R66 点 4019 时天然如此） | `ghcreate mon_bid_10105 … hasMon_true / done_mon_id_30053` | ✅ 建成 |

**原因**（R64 已查明）：`mon_bid = mis.mis_target`，而那条任务正是 **`SC_12400` 刚推给客户端的**。
**先推 `15402` ⇒ 客户端还没有这条任务 ⇒ `mis_target` 取不到 ⇒ `mon_bid=0`。**

### 3.2 修法

复用已有的 **12 秒补推机制**（心跳里、等 NpcCtrl 就绪后重推 `12400`），把 `15402` 排到它**之后**：

```python
# 10300 分支：auto_start 时只排程
self._guaji_15402_at = time.time() + 14.0
# 心跳分支：12400 补推之后
if getattr(self, '_guaji_15402_at', 0) and time.time() >= self._guaji_15402_at:
    ...push 15402...
```

---

## 四、★★ 零点击全自动跑通（真机日志）

```
[17:03:39] << 10200 SCRoleEnter (server push) bid=10005 (91,56)      ← 送进挂机图
[17:03:42] << 12400 SC_12400 mission_list=2                          ← ★ 先给任务列表
[17:03:57] << 12400 SC_12400 mission_list=2 [补推/NpcCtrl 就绪后]
[17:03:57] << 15402 补推（12400 落地之后）mission_bid=10010 map_bid=10005 (91,56)   ← ★ 顺序修正
```

**探针（同一秒）**：

```
t=ghinit   in_mb_10010_in_map_10005_scene_10005
t=ghcreate mon_bid_10105_cfg_table_cfg_map_10005_scene_10005_cfgMon_table_hasMon_true   ← ★ mon_bid 正确
t=ghcreate done_mon_id_30053        ← ★★ 怪建出来了
t=ghinit   after_mb_10105_…
t=gh15402  after_hongchen_true
```

⇒ **不需要点任何按钮**，登录后 15 秒内整条链自动完成（`10200 → 12400 → 15402 → createMon`）。

### 还差的最后一环

`15202`（`fight`）本次仍为 0 —— 即客户端建完怪后**还没发起战斗**。
`fight()` 由 `ghost_ctrl` proto#14 调起，其触发者仍待查（下一步：反汇编 `ghost_ctrl:fight` 的调用方，
或加一条 `ghfight` 探针）。`15202` 的服务端应答**本轮已就位**，一旦客户端发出就有正确应答。

---

## 五、当前"挂机可跑通"的完整配置

| 配置 | 值 | 作用 |
|---|---|---|
| `guaji_auto_start` | `true` | 登录即自动走 `10200(10005)+10201`（**零点击**） |
| `guaji_push_15402_on_enter` | `true` | 排程 `15402`（延后到 `12400` 之后） |
| `guaji_enter_scene_delay` | 3.0 | 给客户端切场景时间 |
| `guaji_15402_use_role_pos` | `true` | 怪生成在玩家脚下 |
| `guaji_mission_bid` | 10010 | 挂机线任务 |
| `guaji_push_15402` | `true` | `15400`（点 4019）后也推一次（保留手动路径） |
| `missions[10010]` | `status=2 / target=10105` | ★ `mon_bid` 的来源 |
| `guaji_state.loop_count` | 10 | 轮次（R48 的旋钮） |

> ⚠️ 仍然待形式化：`missions[10010].target=10105` 目前是手工设的。
> 正确做法是把"挂机任务的 target"写进任务生成逻辑（`mission_rows` 的 seeding），而不是手改 DB。

---

## 六、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **170** / 默认 64 / 未开放 22）、CS 2463-0、SC 静态 85+1空-0、SC 在线 **86-86**、专用 **63-63**、门禁 E **PASS** |
| 回归 | `verify_guaji` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `stderr` **0 字节**；9000 恰好 1 监听；玩家 lev=70 / gold 841046 / 背包 27 |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | **新增 `15202`**（含反汇编依据）；`_send_10200` 的 `10201` 改用传入 `bid`；`guaji_auto_start` + `_guaji_15402_at` **顺序修正**（`15402` 排到 `12400` 之后） |
| `analysis/1.4.9/round69_71_15202_and_order_fix.md` | 本报告 |

---

## 八、一句话

> **挂机链现在"登录即自动跑通"**：`10200(10005) → 12400 → 15402 → createMon(mon_id=30053)`，全程零点击。
> 关键收获是两条**顺序/配套**问题：`GhostMon:fight()` 要的 `15202` **此前根本没人应答**；
> 而 `15402` **必须排在 `12400` 之后**，否则 `mon_bid` 取不到（探针把这条直接指出来了）。
> 剩下最后一环：**谁触发 `fight()`** —— `15202` 的服务端应答已就位，只等客户端发。
