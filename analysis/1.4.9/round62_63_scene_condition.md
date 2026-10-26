# R62/R63：`createMon` 的**场景条件**已确认并打通（客户端确实切图了），但它仍不建怪

> 本轮把 R61 指出的"场景前提"**从假设变成了实测**：
> `ghost_mon` proto#3 的第三个早退条件确认为 `getSceneId() == mon_cfg.map_bid`；
> 我们据此**把玩家送进了 10005**（真机确认切图成功），并补了**竞态延时** ——
> **但客户端依旧不建怪、不发任何后续包**。
> **时间**：2026-09-29 14:00 – 14:15。

---

## 一、✅ 反汇编确认：`createMon` 的三个早退条件

`ghost_mon.luac` proto#3（bc=70）逐条读出：

```lua
function GhostMon:createMon()
    if not self.mon_bid then return end                                    -- ① mon_bid 必须有
    if self.mon_cfg == nil then return end                                 -- ② mon_cfg 必须有
    if SceneModel:getInstance():getSceneId() ~= self.mon_cfg.map_bid       -- ★★ ③ 必须在目标场景
        then return end
    if not Config.Mon[self.mon_bid] then return end                        -- ④ 配置里要有这只怪
    if not self.mon_id then
        self.mon_id = SceneModel:getInstance():getMaxMonsterId() + 1
    end
    local vo = { id=self.mon_id, bid=self.mon_bid, x=mon_cfg.x, y=mon_cfg.y,
                 res_id=…, name=…, is_client=nil }
    GlobalEvent:getInstance():Fire(SceneEvent.SCENE_CLIENT_ADD, vo)         -- 把怪加进场景
end
```

⇒ **第 ③ 条是硬条件**：玩家不在 `mon_cfg.map_bid` 那个图里，`createMon()` 直接 `return`，
**外部表现就是"收到 `SC_15402` 什么都不做"**。这解释了 R60/R61 的全部观测。

---

## 二、✅ 按该条件实施：**把玩家送进挂机图**（真机确认切图成功）

新增实验分支（`config: guaji_enter_scene`，默认关）：`15400` 应答成功后

```
1) 推 10200 SCRoleEnter{bid=10005}
2) 推 10201 SCMapGird（该图的 npcs/mons/elems）
3) 推 15402 SC_15402{mission_bid=10010, map_bid=10005, (10,58)}
```

**真机证据（切图成功）**：

```
[14:04:34] << 10200 SCRoleEnter (server push) bid=10005 (68,60)
[14:04:34] << 10201 SCMapGird (server push) roles=1 npcs=25 mons=1 elems=2
[14:04:35] << 15402 主动推 SC_15402 mission_bid=10010 map_bid=10005 (10,58)
```

截图判读：**左上角地图名 =「乾坤日月谷」** ⇒ 客户端**确实被送到了 10005**（此前一直是"史莱克城"）。

---

## 三、❌ 但仍不建怪 —— 竞态假设也否证了

| # | 假设 | 变量 | 结果 |
|---|---|---|---|
| G | 三个条件要同时满足（本地 mission + 在目标场景 + 收到 `SC_15402`） | `missions[10010]`=2（`SC_12400 mission_list=2` 带上了它）**且** `guaji_enter_scene=true`（真机已切到 10005）**且**推 `15402` | 全部满足 ⇒ 客户端**仍无任何后续**（只有心跳） |
| H | `10200` 与 `15402` **同 tick 送达**存在竞态（处理 15402 时场景还没切完） | 新增 `guaji_enter_scene_delay=3.0`：`10200` 在 14:10:30、`15402` 在 14:10:33 | 延时生效、顺序正确 ⇒ **依旧无反应** |

⇒ R59–R63 **累计否证 8 个假设**：
`loop_count=0` / `=10` / 补推 `15401` / 缺本地 mission / 15400 后推 / 进场景推 / 三条件齐备 / 场景切换竞态。

> **有价值的正面结论仍然有两个**：
> ① 四环链路（`13781 → 15405 → 15400 → <<15402`）**稳定可复现**，4019 按钮坐标 (1853,869) 可靠；
> ② **服务端可以把玩家送进任意场景**（`10200` 推送有效、真机已确认切到乾坤日月谷）—— 这条能力本身很有用。

---

## 四、下一步：**别再猜，上探针**（这也是项目方在本轮之前就批准的方向）

八次否证说明：**黑盒试参数已经到边际**。剩下的问题是"客户端内部到底走到哪一步了"，
只有探针能回答：

| 要观测 | 探针上报点 |
|---|---|
| `GhostCtrl.handle15402` **有没有被调用** | 包装 `GhostCtrl.handle15402`，`report('g15402', 'called')` |
| `mon_hongchen` **实例是否存在** | `report('ghost', 'hongchen=' .. tostring(ctrl.mon_hongchen ~= nil))` |
| `GhostMon.mis_key` / `mon_bid` / `mon_cfg` **是什么** | 在 `initData` 尾部 `report('ginit', 'key='..…' bid='..…)` |
| `createMon()` **在哪一条早退返回** | 在三个 `return` 前各插一条 `report('gm', 'bail=N')` |
| `SceneModel:getSceneId()` **当时是多少** | `report('gscene', 'id='..tostring(SceneModel:getInstance():getSceneId()))` |

现有探针（`server/dsh_fake_login.lua`）已经在挂钩 `npcE / dlgS / smCall / svCall / view …` 20+ 种上报，
**加这 5 条是同一套路**；代价是要走一次 APK 重打包链
（`tools/patch_fake_login.py` → `zipalign` → `apksigner` → `adb install -r`，HANDOVER §4.2），
**会替换玩家正在用的客户端**，因此**不擅自执行**。

---

## 五、收尾（全部还原 + 全绿）

| 项 | 值 |
|---|---|
| 玩家 | `rid=1001` / lev=70 / gold 841046 / 背包 27 |
| `missions` | **已还原**：10010=3、10051=2 |
| `guaji_state` | `loop_count = 0` |
| `config.json` | `guaji_push_15402=true`（R60 正式行为保留）、`guaji_enter_scene=**false**`（R62 实验，未达成目标 ⇒ 关；代码与开关保留）、`guaji_enter_scene_delay=3.0`、`guaji_push_15402_on_enter=false`、`guaji_push_15401=false` |
| 服务端 | 在线，9000 恰好 1 监听，`stderr` **0 字节** |
| 六道门禁 + 回归 | 全绿（lint 0 遮蔽 / CS 2463-0 / SC 静态 85+1空-0 / SC 在线 86-86 / 专用 63-63 / 门禁 E PASS；`verify_guaji`、`level_consistency`、`race`、`arena`、`dungeon`、`mission_hook` 全 PASS） |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `15400` 后可选「送进挂机图 + 延时 + 推 15402」（`guaji_enter_scene` / `guaji_enter_scene_delay`，默认关） |
| `analysis/1.4.9/round62_63_scene_condition.md` | 本报告 |
| `analysis/_ghost_mon.txt` | `createMon`（proto#3）真源 |

---

## 七、一句话

> **`createMon` 的场景条件是硬条件——已确认，并且我们成功把玩家送进了乾坤日月谷。**
> 但八次黑盒实验全部否证 ⇒ **该上探针看客户端内部了**（5 个上报点已列清，代价是一次 APK 重打包）。
