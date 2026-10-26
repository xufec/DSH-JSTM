# JSTM 落地蓝图 —— ① 场景骨架 ② 工程范式

> 本文把「值得借鉴」的两条从**结论**推进到**可实施**：给出 Python 类结构、方法签名、调用顺序、分频语义，
> 并为每一条标注【保留/改造/丢弃】及理由。
> 所有事实均来自对 `cankao/kongkongxiyou-master.zip` 的源码核对（行号可回溯）；未读到的仍标【未知】。
>
> **范围声明：** 本文只写设计，不写协议。JSTM 面向《绝世唐门》1.4.9 客户端，**网络协议层【未知】**，因此
> 所有出网调用都只到 `send(player, route, msg)` 这一层为止，具体编码/加密由协议层决定。

---

## 0. 本次核验的新增/更正（先看这节，有 2 处是**对我初版报告的更正**）

### 0.1 更正 1：`messageService` **不是**「唯一出网出口」

初版报告称它是「全服出网唯一出口」。脚本核验 `app/**` 后发现 **20+ 处直接绕过它**：

| 位置 | 直推语句 |
|---|---|
| `domain/area/area.js:122` | `this.channel.pushMessage('onRemoveEntities', ...)`（掉落物消失） |
| `domain/area/area.js:172/176/182` | `this.getChannel().pushMessage("onRunArea"/"onDragArea"/"onUserLeave", ...)` |
| `domain/area/areaLogic.js:260/270/277/509/519` | `this.channel.pushMessage("onFinishFight"/"onRunArea"/"onDragArea"/"onDomainBattle"/"onUpdateDomain", ...)` |
| `domain/entity/team.js:167/268/284/300/313` | `this.channel.pushMessage('onDisbandTeam'/'onUpdateTeam'/'onTeammateLeaveTeam'/'onChat'/'onDragMember2gameCopy', ...)` |
| `services/Guilder.js:284/464/502` | `channel.pushMessage('onChat'/'onApplyGuild', ...)` |
| `services/chatService.js:124` | `channel.pushMessage(Event.chat, msg, cb)` |

**真实形态是「按受众分两条通道」**，而不是单一出口。第 2.1 节给出更正后的 JSTM 设计。

### 0.2 更正 2：`errHandler` 的「惰性掉线检测」**是空操作**（不是"部分生效"，是**完全没生效**）

初版称它「很实用」。核验链路：

| # | 代码位置 | 事实 |
|---|---|---|
| 1 | `channelService.js:358` `add(uid, sid, groups)` → `groups[sid] = [uid, ...]` | 分组里装的是 **uid** |
| 2 | `channelService.js:410-435` `failIds.concat(fails)` → `cb(null, failIds)` | 失败列表装的是 **uid** |
| 3 | `messageService.js#errHandler(err, fails)` → `removePlayerByUid(fails[i])` | 把 **uid** 当参数传入 |
| 4 | `areaManager.js#removePlayerByUid(playerId)` → `getCanUsedPlayer(playerId)` → `this.players[playerId]` | 查的是**按 playerId 索引**的 `players{}` |
| 5 | `area.js:318` `this.players[e.id]=e.entityId; this.users[e.userId]=e.id;` | 项目里 **playerId(`id`) ≠ uid(`userId`)**，正因如此才需要 `users{}` 反查表 |

⇒ **`this.players[uid]` 必然查不到 → `if (!player) return;` 静默返回。该功能一行都没执行。**【已确认】

**连带影响：** 那么「玩家断线后如何从场景里被清掉」实际靠的是
① `session.on('closed')` → `onUserLeave` → `playerRemote.playerLeave`（正常断线），
② `area.updatePlayers()` 里 `currentTime > entity.kickTime`（30 分钟心跳超时，**精度 ±3.1s**）。
**② 才是真正的兜底，而它非常慢（30 分钟）。** JSTM 不应等 30 分钟。

### 0.3 新增事实：精确的分频表（这是初版只粗略描述、现在核验到行的部分）

`domain/area/timer.js:22-30` 原文：

```js
Timer.prototype.tick = function() {
  if (this.area) {
    this.area.tick();                 // ① 每 100ms
    this.timeCount++;
    if (this.timeCount%10===0) { this.area.update1(); }   // ② 每 10 tick
    if (this.timeCount>30) { this.timeCount=0; this.area.update3(); }  // ③ 第 31 tick
  }
};
```

而 `Area.update1/update3` 只是转发（`area.js:99-105`）：

```js
Instance.prototype.update1 = function(){ this.areaLogic.update1(); };
Instance.prototype.update3 = function(){ this.areaLogic.update3(); };
```

策略基类 `AreaLogic`（`areaLogic.js:84-94`）：

```js
AreaLogic.prototype.startLogic = function() {};
AreaLogic.prototype.update1 = function() { this.area.updateZones(); };   // 刷怪/刷物
AreaLogic.prototype.update3 = function() { this.area.updatePlayers(); }; // 玩家 update + 超时踢人
```

**⇒ 精确分频表【已确认】：**

| 频率 | 精确周期 | 驱动路径 | 实际内容 | 精度含义 |
|---|---|---|---|---|
| **100 ms** | 10 Hz | `timer.tick → area.tick()` | ① `items{}` 遍历 `item.update(now)`（掉落物超时消失 → `onRemoveEntities`）② `actionManager.update(now)`（**行走滑行 + 复活计时**）③ `aiManager.update()`（行为树）④ `patrolManager.update()` | 移动位置 10 Hz 更新；**复活误差 ≤100 ms** |
| **1 s** | 每 31 tick 中 3 次（tick 10/20/30） | `update1 → areaLogic.update1 → area.updateZones()` | 遍历 `zones{}` 各自 `update()` → **刷怪（MobZone）/ 刷物（ItemZone）** | 刷怪粒度 1 s；`MobZone` 内部再以 `nextGenTime` 节流（`interval = opts.refreshTime \|\| 5000`），故**实际刷怪周期 ≈ max(1s, 5s) = 5 s**，每次刷 `genCount=3` 只到 `limit`（`opts.num \|\| 10`） |
| **3.1 s** | 每 31 tick 中 1 次（tick 31） | `update3 → areaLogic.update3 → area.updatePlayers()` | 每个在线玩家：**`kickTime` 超时则踢出**，否则 `entity.update()`；`AreaDomainLogic` 额外 `updateDomainBattle()` | **HP/MP 恢复精度 = 3.1 s**；**踢人误差 ≤3.1 s** |

**★ 两个最容易被忽略、但对「数值对齐」至关重要的推论：**

1. **`Player.update()` 是 HP/MP 恢复的唯一驱动点**（`player.js:149-192`：按 `hpCount/hpSpeed`、`mpCount/mpSpeed` 累加，有变化才推 `onHpMp`，且有 hp 变化时再 `onHp2All(hpSpeed)` 广播回血数字）。
   它只在 `updatePlayers()`（即 **3.1 s 分频**）里被调用
   ⇒ **`hpSpeed`/`mpSpeed` 的配置值必须按「每次 3.1 秒」的口径解释**。
   若 JSTM 把恢复放到每 tick（100 ms），同一份 `hpSpeed` 会让回血快 **31 倍**。
   **这是从 1.4.9 客户端/数值表迁移时最容易翻车的地方之一。**

2. **不同系统的精度被刻意分开了**：复活计时（`Revive` 是一个挂在 actionManager 上的 action，`deadline = reviveTime + now`，`update` 到点调 `player.setRevive(0)`，`consts.PLAYER.reviveTime = 30000`）走 **100 ms**，而 HP 恢复走 **3.1 s**。
   ⇒ 分频不是"随便分层"，而是**「成本 vs 精度」的显式取舍**。JSTM 必须**为每个系统显式指定频率并写进文档**。

### 0.4 新增事实：另有两处「配置被硬编码覆盖」

| 配置 | 配置值 | 代码实际值 | 位置 |
|---|---|---|---|
| `config/instance.json` `lifeTime` | `1800000`（30 min） | **`300000`（5 min）** | `domain/area/instance.js`：`this.lifeTime = 300000;` |
| `config/instance.json` `interval` | `60000` | `60000`（巧合一致，但同样是硬编码） | `domain/area/instancePool.js`：`setInterval(this.check.bind(this), 60000)` |

⇒ **`config/instance.json` 实际上是死配置，从未被读取。** JSTM 不要制造这种"看起来可配、实际不可配"的假配置。

### 0.5 新增事实：`Area` 构造函数里有副作用（启动了整个世界）

`domain/area/area.js`：构造器最后一行（约 `:65`）直接 `this.areaLogic.startLogic();`
→ `AreaNormalLogic.prototype.startLogic = function(){ this.area.start(); }`（`areaLogic.js:292-294`）
→ `Area.start()` 挂 AOI 事件、刷怪、建 NPC、起 AI、`timer.run()`（`setInterval`）。

⇒ **`new Area(map)` 就会启动 tick 循环。** 这是「构造函数产生 IO/定时器副作用」的反模式：
无法构造一个"未启动"的世界（例如做单测、或先批量建好场景再统一起服）。
**JSTM 必须把 `__init__` 与 `start()` 分开。**

---

# 第 1 部分：场景骨架

## 1.1 层级归属：先定规则，再写类

参考项目的容器划分是对的，但没说清「什么东西放哪一层」。补出四条判定规则，JSTM 应按规则落位：

| 规则 | 判定 | 归属 | 例子 |
|---|---|---|---|
| **R1** | 需要**跨场景/跨副本**视角的数据 | `AreaManager`（进程级注册表） | 全部在线玩家对象池、`scenes{}`、`instances{}`、`player_id → instance_id` |
| **R2** | 属于**一个世界实例**的数据 | `Area` | 实体表、AOI、刷怪区、动作队列、仇恨关系、场景频道 |
| **R3** | 只是**世界实例的包装/路由** | `Scene` / `Instance` | `Scene` 仅包一个 `Area` 并提供 `get_player_in_area()`；`Instance` 追加 `instance_id`/`life_time`/`is_alive()` |
| **R4** | **多个世界实例的生命周期管理** | `InstancePool` | 创建、回收、遍历 |

**关键概念：`AreaManager.players` 与 `Area.players` 是同一份 Player 对象的三套索引。**

```
                     ┌──────────────────────────────────────────────┐
   AreaManager       │  players[player_id] ─────────────┐           │
   （跨场景）        │  _player_cache[player_id]        │           │
                     └──────────────────────────────────┼───────────┘
                                                        │ 同一个 Player 对象
                     ┌──────────────────────────────────▼───────────┐
   Area              │  players[player_id] = entity_id              │
   （一个世界实例）  │  users[uid]         = player_id   ← 反查表    │
                     │  entities[entity_id] = Player                │
                     └──────────────────────────────────────────────┘
```

**由此产生一个必须显式处理的中间态【已确认，参考项目正是这样】：**
Player **可能存在于 `AreaManager.players` 但不在任何 `Area.players` 里**（离线缓存/刚查库还没进场/换场景过程中）。
`playerFilter` 就是为这个中间态写的（`servers/area/filter/playerFilter.js`）：除了 `enterScene` 路由，其它路由一律推 `onChangeArea` 并报错。
⇒ **JSTM 必须把它建模成显式状态**（见 1.3 的 `PlayerLocation`），而不是靠"查不到就兜底"。

## 1.2 Tick 分频：JSTM 设计

### 1.2.1 与参考实现的差异（3 处刻意不同）

| # | 参考实现 | JSTM 设计 | 理由 |
|---|---|---|---|
| 1 | **每个 Area 各自 `setInterval(100)`**（12 个场景 = 12 个独立定时器） | **单一全局 ticker，稳定顺序遍历全部 Area** | ① 顺序确定（便于复现 bug、便于确定性单测）；② 可在**全局**层面做预算与降级；③ 避免 N 个定时器同时唤醒时的不确定交错 |
| 2 | `timeCount>30 → 归零` ⇒ 周期 **31 tick = 3.1 s**，且 1s/3s 会漂移 | **绝对时间戳调度**（`next_1s += 1.0`、`next_3s += 3.0`） | 消除 31-tick 漂移；周期语义精确为 1.0 s / 3.0 s，**便于与客户端/数值表对齐** |
| 3 | **无预算、无降级**（12 场景 × 每 tick 全量 action/AI/AOI） | **每 tick 预算 + 超预算降级队列** | 单进程 Python 一旦某 tick 超时，会积压并雪崩。必须能"丢车保帅"（例如把 A* 请求推迟到下一 tick） |

> ⚠️ **第 2 条需要你确认**：参考实现是 **3.1 s**，我建议改成 **3.0 s**。
> 如果 JSTM 要严格复刻 1.4.9 的资源恢复手感，就应保持 **3.1 s**（即保留 31-tick 语义）。
> 我倾向 3.0 s + 按 3.0 重新标定 `hpSpeed`，因为 3.0 更容易解释和测试。**这条列入第 3 节开放问题。**

### 1.2.2 代码骨架

```python
# jstm/world/ticker.py
import asyncio, time
from typing import Callable

class TickScheduler:
    """单一全局 tick 循环。

    分层依据（来自参考实现，已核验）：
      100ms → items / actions(行走,复活) / AI / 巡逻
      1s    → 刷怪刷物（zones）
      3s    → 玩家 update(HP/MP 恢复) + 心跳超时踢人 + 策略类扩展
    """

    TICK_S = 0.1

    def __init__(self, area_manager, clock=time.monotonic):
        self.area_manager = area_manager
        self.clock = clock
        self._running = False
        self._tick_no = 0
        self._next_1s = 0.0
        self._next_3s = 0.0
        self._deferred: list[Callable[[], None]] = []   # 超预算被推迟的重活
        self.stats = {
            "tick": 0, "over_budget": 0, "max_ms": 0.0,
            "deferred": 0, "deferred_dropped": 0,
        }

    async def run(self) -> None:
        self._running = True
        now = self.clock()
        self._next_1s, self._next_3s = now + 1.0, now + 3.0
        deadline = now

        while self._running:
            deadline += self.TICK_S
            t0 = time.perf_counter()
            self._tick_no += 1
            now = self.clock()

            # ---- 100ms 层 ----
            self.area_manager.tick_all(self.TICK_S)

            # ---- 1s 层（绝对时间戳，不漂移） ----
            if now >= self._next_1s:
                self._next_1s += 1.0
                self.area_manager.tick_1s_all()

            # ---- 3s 层 ----
            if now >= self._next_3s:
                self._next_3s += 3.0
                self.area_manager.tick_3s_all()

            self._drain_deferred()

            # ---- 预算与观测 ----
            used_ms = (time.perf_counter() - t0) * 1000.0
            self.stats["tick"] += 1
            self.stats["max_ms"] = max(self.stats["max_ms"], used_ms)
            if used_ms > self.TICK_S * 1000.0 * 0.5:      # 超过半预算
                self.stats["over_budget"] += 1
                # TODO: 这里接 logging.warning，并把重活入 _deferred

            delay = deadline - self.clock()
            await asyncio.sleep(delay if delay > 0 else 0)

    def defer(self, fn: Callable[[], None], max_pending: int = 2000) -> None:
        """把重活（典型：A* 寻路）推迟到本 tick 之后，避免阻塞主循环。"""
        if len(self._deferred) >= max_pending:
            self.stats["deferred_dropped"] += 1
            return
        self._deferred.append(fn)
        self.stats["deferred"] += 1

    def _drain_deferred(self) -> None:
        # 每 tick 只做有限个，保证主循环不被拖垮
        for _ in range(min(len(self._deferred), 32)):
            self._deferred.pop(0)()
```

```python
# jstm/world/area_manager.py（分频入口，与 R1 规则一致）
class AreaManager:
    def tick_all(self, dt: float) -> None:
        for area in self._ordered_areas():          # 稳定顺序
            area.tick(dt)

    def tick_1s_all(self) -> None:
        for area in self._ordered_areas():
            area.tick_1s()                          # → logic.tick_1s() → update_zones()

    def tick_3s_all(self) -> None:
        for area in self._ordered_areas():
            area.tick_3s()                          # → logic.tick_3s() → update_players() [+ 策略扩展]

    def _ordered_areas(self):
        """稳定顺序：先场景（按 area_id 升序），再副本（按 instance_id）。
        参考实现是 setInterval 各自触发，顺序不确定；JSTM 刻意确定化。"""
        return [*self.scenes_by_id.values(), *self.instance_pool.all_instances()]
```

**Area 侧保持参考实现的「转发到策略类」结构**（这是好设计：Area 不管业务，只做调度）：

```python
# jstm/world/area.py
class Area:
    def tick(self, dt: float) -> None:
        now = time.time()
        # ① 掉落物/地面物：超时消失
        for item in list(self._items.values()):
            item.update(now)
            if item.died:
                self.channel.push_message("onRemoveEntities", {"entities": [item.entity_id]})
                self.remove_entity(item.entity_id)
        # ② 动作（行走滑行、复活计时）—— 顺序刻意在 AI 之前，AI 才能读到最新位置
        self.actions.update(dt)
        # ③ AI 行为树
        self.ai_manager.update()
        # ④ 巡逻状态机
        self.patrol_manager.update()

    def tick_1s(self) -> None: self.logic.tick_1s()     # 基类：刷怪刷物
    def tick_3s(self) -> None: self.logic.tick_3s()     # 基类：玩家 update + 踢人
```

## 1.3 五层容器的 Python 设计

```python
# jstm/world/area_manager.py
class AreaManager:
    """R1：进程级注册表。单进程下就是"全世界"。"""

    def __init__(self, map_repo: "MapRepository", player_repo: "PlayerRepository"):
        self._map_repo = map_repo
        self._player_repo = player_repo
        self.scenes_by_id: dict[int, Scene] = {}
        self.players: dict[int, Player] = {}                 # player_id -> Player（在线）
        self._player_cache = TTLCache(ttl=60.0)              # 下线缓存，修正参考实现的 bug
        self.instances: dict[str, Instance] = {}             # instance_id -> Instance
        self.player_to_instance: dict[int, str] = {}
        self.instance_pool = InstancePool(self)
        self._load_locks: dict[int, asyncio.Lock] = {}       # 每玩家一把锁，修正 'waiting' bug

    # ---- 场景 ----
    def init_scenes(self, area_ids: list[int]) -> None:
        for aid in area_ids:
            cfg = self._map_repo.area_config(aid)
            if cfg is None:
                log.error("area config missing area_id=%s", aid); continue
            self.scenes_by_id[aid] = Scene(cfg, self._map_repo.map_for(aid))

    # ---- 玩家两级读取（参考实现的设计，缓存部分重写） ----
    def get_player(self, player_id: int) -> Player | None:
        p = self.players.get(player_id)
        if p is not None:
            return p
        p = self._player_cache.get(player_id)     # 命中则"提升"回在线
        if p is not None:
            self._player_cache.pop(player_id)
            self.players[player_id] = p
        return p

    async def get_or_load_player(self, player_id: int) -> Player:
        """参考实现用 requestList + 字符串 'waiting' 当并发错误 → 高并发首登偶发失败。
        JSTM 改为「每玩家一把锁 + 等待」，语义正确且不丢请求。"""
        p = self.get_player(player_id)
        if p is not None:
            return p
        lock = self._load_locks.setdefault(player_id, asyncio.Lock())
        async with lock:
            p = self.get_player(player_id)          # 双检
            if p is not None:
                return p
            p = await self._player_repo.load_all(player_id)
            self.players[player_id] = p
            return p

    # ---- 归属判定（R2/R3） ----
    def get_area_by_player(self, player: Player) -> Area | None:
        """参考实现：先按 area_id 找场景，再按 instance_id 找副本。
        JSTM 用显式的 PlayerLocation 代替"猜"，并在失败时记录而非静默改写数据。"""
        loc = player.location
        if loc.kind is LocationKind.SCENE:
            scene = self.scenes_by_id.get(loc.area_id)
            return scene.get_player_in_area() if scene else None
        if loc.kind is LocationKind.INSTANCE:
            inst = self.instances.get(loc.instance_id)
            return inst.get_area() if inst else None
        return None                                  # PlayerLocation.NONE：未进场

    # ---- 换场景：单一分派点 ----
    async def change_area(self, req: "ChangeAreaRequest") -> int:
        target = self._map_repo.area_config(req.target_id)
        if target is None:
            return Code.AREA_NOT_FOUND               # 参考实现返回魔法数 111
        if target.type <= AreaType.SCENE:
            return await self._goto_scene(req, target)
        if target.type == AreaType.TEAM_INSTANCE:
            return await self._goto_team_instance(req, target)
        return await self._goto_instance(req, target)

    def remove_player(self, player_id: int) -> None:
        self.players.pop(player_id, None)

    def cache_offline_player(self, player: Player) -> None:
        """修正参考实现的 clearPlayerCaches bug（边写边全清 + 掏空对象）。"""
        self.remove_player(player.id)
        self._player_cache.set(player.id, player)    # TTL 到期自动过期

    def find_by_uid(self, uid: int) -> Player | None:
        """★ 新增：uid → Player 的正确反查。
        参考实现缺失这个入口，导致 errHandler 把 uid 当 player_id 用（见 0.2）。"""
        for p in self.players.values():
            if p.uid == uid:
                return p
        return self._player_cache.find_by(lambda p: p.uid == uid)
```

```python
# jstm/world/scene.py  —— R3：只是包装
class Scene:
    def __init__(self, area_cfg: dict, map_obj: Map):
        self.area = Area(area_cfg, map_obj)      # 注意：不在此处 start()
        self.id = self.area.area_id
    def get_player_in_area(self) -> Area: return self.area
    def remove_player_by_uid(self, uid: int) -> None: self.area.remove_player_by_uid(uid)

# jstm/world/instance.py —— R3 + 生命周期
class Instance:
    def __init__(self, map_obj: Map, instance_id: str, area_cfg: dict, life_time: float):
        self.id = instance_id
        self.area = Area(area_cfg, map_obj, instance_id=instance_id)
        self.life_time = life_time               # ★ 从配置读，不再硬编码 300000
    def start(self) -> None: self.area.start()
    def is_alive(self) -> bool:
        if self.area.is_empty() and (time.time() - self.area.empty_time) > self.life_time:
            return False
        return True

# jstm/world/instance_pool.py —— R4
class InstancePool:
    def __init__(self, manager: AreaManager):
        self._manager = manager
        self.instances: dict[str, Instance] = {}
    def create(self, area_id: int, instance_id: str) -> int:
        if instance_id in self.instances:
            return Code.INSTANCE_EXISTS
        inst = Instance(self._manager._map_repo.map_for(area_id), instance_id,
                        self._manager._map_repo.area_config(area_id),
                        life_time=self._manager._map_repo.instance_life_time())
        self.instances[instance_id] = inst
        inst.start()
        return Code.OK
    def collect_garbage(self) -> list[str]:
        """参考实现这里要跨进程 RPC 问 manager；单进程直接本地回收。"""
        dead = [iid for iid, inst in self.instances.items() if not inst.is_alive()]
        for iid in dead:
            self.instances.pop(iid).close()
        return dead
    def all_instances(self) -> list[Instance]: return list(self.instances.values())
```

```python
# jstm/world/area.py —— R2：真正的世界
class Area:
    def __init__(self, area_cfg: dict, map_obj: Map, instance_id: str | None = None):
        self.map = map_obj                       # ★ 全进程共享同一 Map 对象（参考实现的关键优化）
        self.area_id = area_cfg["id"]
        self.type = area_cfg["type"]
        self.area_kind = area_cfg["kind"]
        self.instance_id = instance_id

        self.entities: dict[int, Entity] = {}
        self.players: dict[int, int] = {}        # player_id -> entity_id
        self.users: dict[int, int] = {}          # uid       -> player_id  （反查表）
        self.items: dict[int, int] = {}
        self.npcs: dict[int, NPC] = {}
        self.zones: dict[int, Zone] = {}
        self.player_num = 0
        self.empty_time = time.time()

        # ★ 塔格尺寸来自配置，不再硬编码 300
        self.aoi = TowerAOI(
            width=map_obj.width, height=map_obj.height,
            tower_w=area_cfg.get("tower_width", 300),
            tower_h=area_cfg.get("tower_height", 300),
        )
        self.actions = ActionManager()
        self.ai_manager = AIManager(area=self)
        self.patrol_manager = PatrolManager(area=self)
        self.channel = None                      # 懒创建
        self.logic = create_area_logic(self)     # 策略模式（照搬参考实现）
        self._started = False

    # ★ 与参考实现的关键差异：构造函数不启动世界
    def start(self) -> None:
        if self._started:
            return
        self._started = True
        # 顺序至关重要（照搬参考实现 area.js#start）：
        aoi_event_manager.register(self, self.aoi)   # ① 先挂 AOI 事件，否则丢首批同步
        self.init_mob_zones()                        # ② 刷怪区
        self.init_npcs()                             # ③ NPC（不进 AOI）
        self.ai_manager.start()                      # ④ AI
        # ⑤ tick 由全局 TickScheduler 统一驱动，这里不再自建定时器

    def get_channel(self) -> Channel:
        if self.channel is None:
            name = (f"area_{self.instance_id}" if self.instance_id else f"area_{self.area_id}")
            self.channel = self.channel_service.get_channel(name, create=True)
        return self.channel

    # ---- 实体进出（照搬参考实现的双注册模型 + 清理顺序） ----
    def add_entity(self, e: Entity) -> bool: ...
    def remove_entity(self, entity_id: int) -> bool: ...
```

## 1.4 六条关键时序（Python；每条都标注了参考实现的对应代码）

### ① 启动

```python
async def bootstrap(env: str) -> "World":
    world = World()
    world.area_manager.init_scenes(cfg.area_ids)          # 只建对象，不 start
    for area in world.area_manager.scenes_by_id.values():
        area.start()                                       # 显式统一起服
    world.ticker_task = asyncio.create_task(world.ticker.run())
    return world
# 参考实现：AreaManager.initScenes → new Scene → new Area → 构造器里 areaLogic.startLogic()
#           → area.start() → timer.run()。即"建对象"和"起服"耦合。JSTM 拆开。
```

### ② 进场景（`enterScene`）

```python
@area_handler("area.playerHandler.enterScene", guard=False)   # 唯一豁免前置守卫的路由
async def enter_scene(ctx: HandlerCtx, msg: dict):
    player, area = ctx.player, ctx.area
    if area.get_player(player.id):                        # 已在场 → 先摘掉
        area.remove_player(player.id)
    if ctx.session.uid != player.uid:                     # uid 归属校验（参考实现有，保留）
        return Err(Code.UID_MISMATCH)
    if player.hp <= 2:                                    # 参考实现：进普通场景补半血
        player.hp = player.max_hp // 2
    area.logic.enter_area(player)                         # = abort_all_action + 策略类 enterArea
    if not area.map.is_reachable(player.x, player.y):      # 坐标非法 → 出生点
        player.x, player.y = area.map.get_born_point()
    entities = area.get_area_info_strip((player.x, player.y), player.range)  # ★ 先取快照
    if not area.add_entity(player):                       # ★ 后 addEntity（内部才 aoi.add_watcher）
        return Err(Code.ADD_PLAYER_FAILED)
    return Ok({"areaId": area.area_id, "entities": entities, "curPlayer": player.player_strip()})
# 参考实现：playerHandler.js#enterScene（顺序是 "先快照后 addEntity"，必须保持，否则自己会出现在自己的可见列表里）
# ★ 修正：参考实现写成 area.getAreaInfoStrip(player, player.range)，签名却是 (pos, range)，
#   靠 JS 鸭子类型侥幸工作。JSTM 显式传 (x, y)。
```

### ③ 移动（★ 与参考实现刻意不同的地方）

```python
@area_handler("area.playerHandler.move")
async def move(ctx: HandlerCtx, msg: dict):
    player, area = ctx.player, ctx.area
    if player.died:
        return Ok()

    path = msg.get("path", [])
    # ===== 下列 5 项校验是 JSTM 必须补的（参考实现一项都没有）=====
    if not security.validate_move(player, path, now=time.time()):
        # 内含：起点一致性(≤tile/2) / 每点可达 / 相邻点直线可达 / 总位移≤walk_speed*Δt*1.3
        #       / 点数≤上限 / 每玩家限流
        await ctx.send("onStand", {"entityId": player.entity_id, "x": player.x, "y": player.y})
        return Err(Code.ILLEGAL_MOVE)
    # =============================================================
    player.is_stop = False
    action = MoveAction(entity=player, path=normalize_path(path, player), speed=player.walk_speed)
    if not area.actions.add(action):
        player.set_is_moving(False)
        return Ok()
    start = path[0]
    if (player.x, player.y) != (start["x"], start["y"]):
        watcher = {"id": player.entity_id, "type": EntityType.PLAYER}
        # 参考实现经由 area.timer.updateObject/updateWatcher 转发到 aoi；
        # JSTM 已去掉 Timer 中间层（tick 由全局 TickScheduler 驱动），直接打 aoi。
        area.aoi.update_object(watcher, (player.x, player.y), (start["x"], start["y"]))
        area.aoi.update_watcher(watcher, (player.x, player.y), (start["x"], start["y"]),
                                player.range, player.range)
    await message_service.push_by_aoi(area, "onMove",
        {"entityId": player.entity_id, "areaId": area.area_id, "path": path}, (start["x"], start["y"]))
    player.kick_time = time.time() + KICK_TIME
    return Ok()
# 参考实现：playerHandler.js#move —— `var path = msg;` 直接信任客户端；Map.verifyPath 全项目 0 调用
```

`MoveAction.update` 照搬参考实现的插值算法（`action/move.js`），这是**无状态、不依赖固定 tick 间隔**的正确写法：

```python
class MoveAction(Action):
    """沿折线按 speed*dt 滑行，单 tick 可跨多个路径点。
    singleton：一个实体同时只有一个移动动作。"""
    def update(self, dt: float) -> None:
        travel = self.speed * dt
        old = (self.entity.x, self.entity.y)
        pos = old
        while travel > 0:
            dest = self.path[self.index]
            dist = distance(pos, dest)
            if dist <= travel:
                travel -= dist
                pos = dest
                self.index += 1
                if self.index >= len(self.path):
                    self.finished = True
                    self.entity.set_is_moving(False)
                    break
            else:
                pos = lerp_toward(pos, dest, dist - travel)
                travel = 0.0
        self.entity.x, self.entity.y = int(pos[0]), int(pos[1])
        # ★ 每 tick 必须更新 AOI 两次：一次让"别人看见我"，一次算"我看见了谁"
        watcher = {"id": self.entity.entity_id, "type": self.entity.type}
        self.area.aoi.update_object(watcher, old, pos)
        self.area.aoi.update_watcher(watcher, old, pos, self.entity.range, self.entity.range)
```

### ④ 换场景 / 进副本（instanceId 命名即共享域）

```python
async def _goto_instance(self, req, target) -> int:
    kind, arg = target["kind"], req.arg_id
    if kind == AreaKinds.FIGHT_AREA:        arg = f"fight_{arg}"
    elif kind == AreaKinds.MY_BOSS_AREA:    arg = f"my_{req.player_id}{req.target_id % 10}"
    elif kind == AreaKinds.WORLD_BOSS_AREA: arg = "boss"
    else:                                   arg = f"sin_{req.player_id}"
    instance_id = f"{req.target_id}_{arg}"          # ★ 命名即语义

    req.area.exit_area(req.player)
    code = self.instance_pool.create(req.target_id, instance_id)
    if code != Code.OK: return code
    self.instances[instance_id] = self.instance_pool.instances[instance_id]
    self.player_to_instance[req.player_id] = instance_id
    req.player.location = PlayerLocation.instance(instance_id, req.target_id)
    return Code.OK
# 参考实现：areaManager.js#gotoInstance（命名规则完全一致，照搬）
```

### ⑤ 下线（顺序化、每步独立容错）

```python
async def on_session_closed(world, session, reason):
    if not session.uid: return
    player_id = session.player_id
    player = world.area_manager.get_player(player_id)
    if player is None: return

    # ① 存档 + 出场（必须最先做，且不可跳过）
    await safely(world.player_remote.player_leave, player_id)
    # ② 社交/竞技/聊天/交易逐项清理，每项独立 try/except，不因前者失败而中断
    await safely(world.guild_service.player_leave, session.uid, player.guild_id, player_id)
    await safely(world.fight_service.kick, player_id)
    await safely(world.chat_service.kick, session.uid)
    await safely(world.market_service.kick, player_id)
# 参考实现：entryHandler.js#onUserLeave（结构完全一致，照搬）
```

`player_leave` 内部（照搬参考实现 `area/remote/playerRemote.js#playerLeave`，但修掉两处）：
```python
async def player_leave(self, player_id: int) -> None:
    player = self.manager.get_player(player_id)
    if player is None: return
    area = self.manager.get_area_by_player(player)
    if area is None: return
    if player.team_id: await self.team_remote.leave_team_by_id({"playerId": player_id})
    if player.hp == 0: player.hp = player.max_hp // 2
    if area.type > AreaType.SCENE:                       # 副本内 → 回场景出生点
        player.x, player.y = self.area_service.get_born_point(player.location.area_id)
    await self.player_repo.update_player(player)
    await self.task_repo.tasks_update(player.cur_tasks)
    area.exit_area(player)
    self.manager.cache_offline_player(player)            # ★ 修掉参考实现的 clearPlayerCaches bug
    area.on_user_leave(player_id)
    if area.instance_id and area.is_empty():
        self.manager.remove_instance(area.instance_id)   # ★ 本地删，不跨进程
```

### ⑥ 副本回收

```python
# 挂在 TickScheduler 的 3s 层或独立 60s 定时器
def collect_instances(world):
    dead = world.area_manager.instance_pool.collect_garbage()   # 本地回收
    if dead: log.info("instances closed: %s", dead)
```

## 1.5 设计决策表（【保留】/【改造】/【丢弃】）

| # | 参考实现的设计 | 决策 | JSTM 做法与理由 |
|---|---|---|---|
| 1 | `AreaManager / Scene / Instance / InstancePool / Area` 五层 | **保留** | 结构正确且不依赖 Pomelo；按 1.1 的 R1–R4 规则落位 |
| 2 | `Map` 全进程共享、`Area` 只持引用 | **保留** | 碰撞图/寻路器只占一份内存 |
| 3 | 100ms / 1s / 3s 三层分频 | **改造** | 保留分层与内容归属；周期改绝对时间戳（消漂移）；**逐系统显式标注频率与精度** |
| 4 | 每 Area 一个 `setInterval` | **丢弃** | 改单一全局 ticker：确定性顺序 + 全局预算 |
| 5 | `Area.update1/update3` 转发到 `areaLogic` 策略类 | **保留** | Area 只调度、策略类管业务，是干净的策略模式 |
| 6 | `createAreaLogic(area)` 按 `area_kind` 工厂选策略 | **保留** | 五套 AreaLogic（普通/城战/竞技/个人BOSS/世界BOSS）直接对应 Python 类 |
| 7 | 构造器里 `areaLogic.startLogic()` → `area.start()` | **丢弃** | 构造与启动分离（`__init__` / `start()`）；否则无法单测、无法批量建场景 |
| 8 | `actionManager` + `singleton` 移动 Action | **保留** | 移动/AI追击/巡逻三处共用一套位置推进；`singleton` 保证一实体一动作 |
| 9 | `Move.update` 按 `speed*dt` 沿折线滑行（无状态插值） | **保留** | 不依赖固定 tick，抗抖动 |
| 10 | 进出场景先 `abort_all_action` | **保留** | 防残留动作把角色带跑 |
| 11 | AOI 双注册（watcher + object） | **保留** | 见 `aoi.md`（本次不改，AOI 单独设计） |
| 12 | `get_area_info_strip` 快照里额外塞全部 NPC | **保留** | NPC 数量少且固定，折中有效 |
| 13 | `player_caches` 60s 下线缓存 | **改造** | 思路保留，**实现重写**（参考实现边写边全清 + 掏空对象，等于没缓存） |
| 14 | `requestList` + `'waiting'` 字符串防并发 | **丢弃** | 改「每玩家一把 `asyncio.Lock` + 等待」，不丢请求 |
| 15 | `playerFilter` 前置守卫统一注入 `session.player` | **保留** | 见 2.4 |
| 16 | `get_area_by_player` 失败时静默把 `area_id` 改回 1001 | **改造** | 保留兜底能力，但**必须记警告 + 上报**，不静默改数据 |
| 17 | 「先取 AOI 快照，再 addEntity」的进场顺序 | **保留** | 顺序反了会把自己塞进自己的可见列表 |
| 18 | 用 `opts.level` 是否存在区分 MobZone/ItemZone | **丢弃** | 改显式 `type` 字段 |
| 19 | 场景号区间硬编码 `6001..6005` | **丢弃** | 配置化 |
| 20 | `tower_width/height` 硬编码 300 | **改造** | 改为 `area_cfg` 可配，默认 300 |
| 21 | `instance.life_time` 硬编码 300000（配置 1800000 未生效） | **改造** | 从配置读；**不制造"假配置"** |
| 22 | `area.close()` 手动把 `self` 所有字段 delete、`setTimeout` 置 null | **丢弃** | Python 依赖解除引用即可，不要手动清字段（会造成悬挂引用） |
| 23 | 移动路径完全信任客户端 | **丢弃** | 见 1.4③ 的 5 项校验（这是最高优先级的安全项） |
| 24 | `getEntity` 按 id 返回任意实体数据 | **丢弃** | 必须校验目标在自身 AOI 范围内 |
| 25 | 双份 `changeArea` 实现并存 | **丢弃** | 只保留一套，死代码删掉 |
| 26 | 无 tick 预算、无降级 | **新增** | 超半预算告警；A\* 等重活入 `defer` 队列 |
| 27 | 无任何性能埋点 | **新增** | tick 耗时/超预算次数/deferred 数最大 tick 必采 |
| 28 | `uncaughtException` 只打日志 | **丢弃** | 记录后优雅下线/重启；至少标记"不可信状态" |
| 29 | `utils.myPrint` 硬编码全开 + `Error.prepareStackTrace` | **丢弃** | 标准 `logging`，级别可配，禁止热路径打日志 |
| 30 | `loadAreaResource` 进服预下发资源清单 | **保留** | 老客户端刚需（属 handler 层，见 2.4） |

## 1.6 分阶段实施（每阶段都有可验证产出）

| 阶段 | 内容 | 可验证产出 |
|---|---|---|
| **P1 骨架可跑** | `TickScheduler` + `AreaManager` + `Scene` + `Area`（仅空世界 + NPC） + 分频埋点 | 起服后 tick 稳定 10 Hz，`stats["max_ms"]` 打印；建 12 个场景不启动 tick 也能成功（证明构造/启动已分离） |
| **P2 玩家进场** | `PlayerRepository` + `get_or_load_player`（带锁）+ `enter_scene` + `playerFilter` 守卫 + 点对点推送 | 两个客户端能互相看见（`onAddEntities`/`onRemoveEntities`）；重复登录挤下线 |
| **P3 移动与 AOI** | `MoveAction` + `TowerAOI` + `aoi_event_manager` 差量同步 + **5 项移动校验** | 移动平滑；穿墙/瞬移/超速包被拒并强制 `onStand`；AOI 差集推送计数可观测 |
| **P4 世界活性** | `MobZone`（1s 分频 + 5s 节流）+ `PatrolManager` + `AIManager` + `Revive`（100ms 精度）+ HP/MP 恢复（3s 分频） | 怪按 5s 节奏刷新并巡逻；被打脱战回位；**HP 恢复速率与 1.4.9 数值表对齐** |
| **P5 副本与回收** | `InstancePool` + `goto_scene/goto_instance` + 空场回收（配置化） | 进副本、退副本、空场 5 分钟回收；个人/世界 BOSS 的实例隔离正确 |

---

# 第 2 部分：工程范式

## 2.1 出网双通道（更正后的设计）

### 设计原则

```
                  ┌────────────────────────────────────────────┐
   定向推送 ──────▶│ MessageService                             │
   （明确受众）    │  send_to_player(player, route, msg)        │
                  │  send_to_uids([(uid,sid)], route, msg)     │──┐
                  │  send_by_aoi(area, route, msg, pos, ignore)│  │
                  │  send_tips(player, error_code)             │  │
                  └────────────────────────────────────────────┘  │
                                                                  ▼
                  ┌────────────────────────────────────────────┐  ┌──────────────────┐
   频道广播 ──────▶│ Channel.push_message(route, msg)           │─▶│ 底层唯一落点      │
   （频道成员）    │  = for m in members: send(m, route, msg)   │  │ send(player,     │
                  └────────────────────────────────────────────┘  │       route,msg) │
                                                                  └──────────────────┘
                                                                          │
                                                              ┌───────────▼───────────┐
                                                              │ 协议层（【未知】）      │
                                                              │ 编码/加密/分片/重传     │
                                                              └───────────────────────┘
```

**三条硬性要求（都是参考项目的缺陷所在）：**
1. **两条通道必须共用同一个底层 `send(player, route, msg)`** —— 参考项目两条通道各自直接调 `channelService`，没有共同落点，导致错误处理/日志/统计要写两遍（而且实际只写了一遍，见 0.2）。
2. **失败处理只写一次**，且**必须携带能唯一定位玩家的键**（推荐 `player_id`；若必须携带 `uid`，则 `AreaManager` 必须提供 `find_by_uid()`）。
3. **失败 → 踢下线的动作要限速**，不要一次失败就立刻踢（网络抖动会导致误踢）。参考实现是"失败即清场景"，且是空操作，所以没暴露这个问题。

```python
# jstm/net/message_service.py
class MessageService:
    def __init__(self, session_router, area_manager, data_api):
        self._router = session_router
        self._area_manager = area_manager
        self._data_api = data_api
        self._fail_streak: dict[int, int] = {}     # player_id -> 连续失败次数

    # ---------- 底层唯一落点 ----------
    async def send(self, player: Player | None, route: str, msg: dict) -> bool:
        if player is None or not player.session_addr:
            return False
        ok = await self._router.send(player.session_addr, route, msg)
        if ok:
            self._fail_streak.pop(player.id, None)
            return True
        # 惰性掉线检测：连续失败达阈值才判定断线（避免抖动误踢）
        n = self._fail_streak[player.id] = self._fail_streak.get(player.id, 0) + 1
        if n >= FAIL_STREAK_TO_KICK:
            log.info("player unreachable, force cleanup player_id=%s", player.id)
            await self._area_manager.force_cleanup(player.id)
        return False

    # ---------- 通道 A：定向 ----------
    async def send_to_player(self, player: Player, route: str, msg: dict) -> bool:
        return await self.send(player, route, msg)

    async def send_by_aoi(self, area, route, msg, pos, ignore: set[int] | None = None) -> int:
        """AOI 群推：pos → watcher player_id 列表 → 逐个 send。
        注意：参考实现的 getWatcherUids 返回 [{uid, sid}]，JSTM 直接返回 Player/player_id，
        避免 uid/playerId 混淆（这正是参考实现 errHandler 坏掉的原因）。"""
        targets = area.get_aoi_players(pos, (EntityType.PLAYER,), ignore)
        sent = 0
        for pl in targets:
            if await self.send(pl, route, msg):
                sent += 1
        return sent

    async def send_tips(self, player: Player, error_code: int) -> None:
        await self.send(player, "onLogTips",
                        {"code": error_code, "msg": self._data_api.error_code.find_by_id(error_code)})

    async def send_tips_box(self, player: Player, error_code: int) -> None:
        await self.send(player, "onTipsBox",
                        {"code": error_code, "msg": self._data_api.error_code.find_by_id(error_code)})

# jstm/net/channel.py
class Channel:
    """单进程频道。参考实现是跨进程 ChannelService（按 sid 分组 + RPC + store 持久化），
    单进程下这些全部不需要，只保留"成员集合 + 广播 + 空则销毁"。"""
    def __init__(self, name: str, message_service: MessageService):
        self.name = name
        self._ms = message_service
        self._members: set[int] = set()          # player_id 集合

    def add(self, player_id: int) -> None: self._members.add(player_id)
    def leave(self, player_id: int) -> None: self._members.discard(player_id)
    def get_user_amount(self) -> int: return len(self._members)

    async def push_message(self, route: str, msg: dict) -> int:
        """★ 与定向通道共用同一个 send()。"""
        area_manager = self._ms._area_manager
        sent = 0
        for pid in list(self._members):
            pl = area_manager.get_player(pid)
            if pl is None:
                self._members.discard(pid)        # 顺手清理（自愈）
                continue
            if await self._ms.send(pl, route, msg):
                sent += 1
        return sent

class ChannelService:
    def __init__(self, message_service: MessageService):
        self._ms = message_service
        self._channels: dict[str, Channel] = {}

    def get_channel(self, name: str, create: bool = False) -> Channel | None:
        ch = self._channels.get(name)
        if ch is None and create:
            ch = self._channels[name] = Channel(name, self._ms)
        return ch

    def destroy_channel(self, name: str) -> None:
        self._channels.pop(name, None)

    def sweep_empty(self) -> None:
        for name, ch in list(self._channels.items()):
            if ch.get_user_amount() == 0:
                self.destroy_channel(name)
```

**频道命名规则照搬参考实现**（`util/channelUtil.js`，单进程下依然有价值——它把"社交结构"编码进频道名）：

```python
GLOBAL_CHANNEL = "pomelo"                      # 全局（世界聊天/系统/跑马灯）
def area_channel(area_id_or_instance_id) -> str: return f"area_{area_id_or_instance_id}"
def team_channel(team_id: int) -> str:           return f"team_{team_id}"
def guild_channel(guild_id: int) -> str:         return f"guild_{guild_id}"
# ⚠️ GLOBAL_CHANNEL 字面量 "pomelo" 是否被 1.4.9 客户端依赖？【未知】——
#    若不依赖，建议改成语义名 "world"；若客户端有硬编码，必须保留。
```

## 2.2 迁移适配层（handleRemote 模式）

### 它解决的问题

参考项目的真实场景：**聊天功能从 `chat` 进程搬到了 `manager` 进程**。作者的解法不是去改几十个调用点，而是加一层：

```js
// app/consts/handleRemote.js（原文）
handleRemote.chatRemote_add  = function(session, uid, playerId, channelName) {
  pomelo.app.rpc.manager.chatRemote.add(session, uid, playerId, channelName, consts.BLACKHOLEFUNC);
};
handleRemote.chatRemote_kick = function(session, uid) {
  pomelo.app.rpc.manager.chatRemote.kick(session, uid, consts.BLACKHOLEFUNC);
};
// …共 6 个函数，全部只改"目标服务名"
```

调用点（`entryHandler`、`area/chatHandler` 等）只 `require('.../handleRemote')`，**完全不知道聊天在哪台服务器上**。

### JSTM 的用法：把「跨进程调用」渐进收敛为「函数调用」

JSTM 的落地路径本身就是「从多进程设计 → 单进程实现」，这个模式正好是**降低重构风险的杠杆**。

```python
# jstm/services/remote_facade.py
"""跨服务调用收敛层（参照 kongkongxiyou 的 consts/handleRemote.js）。

第一阶段：原样保留调用形态，只是把 pomelo RPC 换成 Python 协程调用。
第二阶段：调用点逐个改为直接依赖具体 service。
第三阶段：删除本层。

★ 纪律：本层的每个方法都必须是"薄"的——只做转发 + 参数适配，
   不写任何业务逻辑（否则第三阶段就删不掉了）。
"""

class RemoteFacade:
    def __init__(self, world: "World"):
        self._w = world

    # ---- 旧语义：pomelo.app.rpc.manager.chatRemote.add(session, uid, playerId, channel) ----
    async def chat_remote_add(self, session, uid: int, player_id: int, channel_name: str) -> int:
        return await self._w.chat_service.add(uid, player_id, channel_name)

    async def chat_remote_kick(self, session, uid: int) -> None:
        await self._w.chat_service.kick(uid)

    async def chat_remote_read_mail(self, session, player_id: int, mail_id: int):
        return await self._w.chat_service.read_mail(player_id, mail_id)

    # ---- 旧语义：rpc.manager.guildRemote.enterGuild(session, userId, guildId, playerId) ----
    async def guild_remote_enter(self, session, uid: int, guild_id: int, player_id: int) -> None:
        await self._w.guild_service.enter_guild(guild_id, player_id)

    # ---- 旧语义：rpc.area.playerRemote.playerLeave(session, {playerId, time}) ----
    async def player_remote_leave(self, session, args: dict) -> None:
        await self._w.player_remote.player_leave(args["playerId"])
```

**退休流程（建议写进 JSTM 的工程规范）：**

| 阶段 | 动作 | 完成判据 |
|---|---|---|
| S1 | 所有"跨服务"调用都经 `RemoteFacade` | `grep -r "world\.\w*_service\." handlers/ | wc -l` 为 0（handler 只依赖 facade） |
| S2 | 逐模块把调用点改成直接依赖具体 service，并在 facade 方法上标 `@deprecated(since=...)` | 每个 facade 方法都有 0 个调用点后才能删 |
| S3 | 删除 `RemoteFacade` | 文件不存在，且全量测试通过 |

**为什么值得做：** JSTM 面对 1.4.9 客户端时，服务边界**一定会反复调整**（哪些合、哪些分）。有这层在，每次调整只改一处；没有这层，每次调整都要全库改调用点。这也是参考项目里**唯一一处体现了"分布式→单体"演进经验**的代码。

## 2.3 配置表映射（dataApi）

参考实现 `util/dataApi.js` 只有约 30 行，却是全项目 28 张配置表的统一入口。它的设计值得**逐条保留**：

```js
var Data = function(data) {
  data = require('../../config/data/' + data);
  var fields = {};
  data[1].forEach(function(i, k) { fields[i] = k; });   // 第 2 行是字段名
  data.splice(0, 2);                                    // 去掉前两行（说明行 + 字段名行）
  var result = {};
  data.forEach(function(k) { var item = mapData(fields, k); result[item.id] = item; });
  this.data = result;                                   // 按 id 索引
};
```

即：**「二维数组表」→「按字段名映射的对象表」→「按 id 索引的字典」**，并提供 `find_by_id / find_by / find_bigger / find_smaller / all`。

```python
# jstm/config/data_table.py
from dataclasses import dataclass
from typing import Any, Callable, Iterable

class DataTable:
    """把策划表（二维数组）转成按 id 索引的不可变对象表。

    表格式（沿用参考实现，便于直接用 exceldata 工具链产出）：
      row[0] = 说明行（忽略）
      row[1] = 字段名
      row[2:] = 数据行
    """

    def __init__(self, rows: list[list[Any]], *, table_name: str):
        if len(rows) < 2:
            raise ValueError(f"{table_name}: 表至少需要 说明行 + 字段名行")
        self._name = table_name
        self._fields = list(rows[1])
        self._by_id: dict[int, dict] = {}
        for raw in rows[2:]:
            if raw is None or len(raw) == 0 or raw[0] in (None, ""):
                continue                       # 空行/分隔行
            item = {f: raw[i] if i < len(raw) else None for i, f in enumerate(self._fields)}
            self._by_id[int(item["id"])] = item
        # 冻结，防止业务代码误改配置（参考实现是可变对象，容易被改坏）
        for item in self._by_id.values():
            item.freeze() if hasattr(item, "freeze") else None

    def find_by_id(self, _id: int) -> dict | None:
        return self._by_id.get(int(_id))

    def find_by(self, attr: str, value: Any) -> list[dict]:
        return [it for it in self._by_id.values() if it.get(attr) == value]

    def find_bigger(self, attr: str, value: float) -> list[dict]:
        return [it for it in self._by_id.values() if float(it.get(attr) or 0) >= float(value)]

    def find_smaller(self, attr: str, value: float) -> list[dict]:
        return [it for it in self._by_id.values() if float(it.get(attr) or 0) <= float(value)]

    def all(self) -> list[dict]:
        return list(self._by_id.values())

    def __len__(self) -> int: return len(self._by_id)

@dataclass
class DataApi:
    """与参考实现 dataApi.js 的同名表一一对应（28 张）。"""
    area: DataTable
    character: DataTable
    equipment: DataTable
    experience: DataTable
    npc: DataTable
    role: DataTable
    item: DataTable
    fightskill: DataTable
    task: DataTable
    team: DataTable
    error_code: DataTable
    strength: DataTable
    item_shop: DataTable
    task_daily: DataTable
    task_main: DataTable
    hpmp: DataTable
    market: DataTable
    officer: DataTable
    guild: DataTable
    fightlevel: DataTable
    guild_town: DataTable
    myboss: DataTable
    recharge: DataTable
    exchange: DataTable
    gift: DataTable
    recycle: DataTable
    fruit_slot: DataTable

    @classmethod
    def load(cls, data_dir) -> "DataApi":
        """启动时一次性加载 + 校验；失败即启动失败（不要运行期才发现表缺列）。"""
        ...
```

**补强两点（参考实现的短板）：**
1. **启动时校验**：字段名去重、`id` 唯一、必填列存在、外键（如 `character.skillId` 指向 `fightskill`）可解析。参考实现是 `require` 进来直接用，**错列到运行期才炸**。
2. **配置不可变**：参考实现的 `this.data` 是可变的，业务代码一旦误改会污染全局（所有 Area 共享）。JSTM 用 `MappingProxyType` 或冻结 dataclass。

## 2.4 Handler 前置守卫（playerFilter 模式）

参考实现的 `playerFilter` 做四件事，**逐条保留**，并把 bug 修掉：

| 参考实现做的事 | JSTM |
|---|---|
| 取玩家：内存 → 下线缓存 → 查库并 `addPlayer` | `await area_manager.get_or_load_player(pid)`（带 per-player 锁） |
| 补回包地址：`player.serverId` / `player.sessionData` | Proxy 持有 `session_addr`，在**登录时**一次性绑定（不在每次请求里补） |
| 定位 Area：先 `scenes[areaId]` 再 `instances[instanceId]` | `get_area_by_player()`，基于显式 `PlayerLocation`；失败记警告 |
| 玩家不在 Area 里 → 除 `enterScene` 外一律推 `onChangeArea` + 报错 | 同左（**这是"异常自愈"，值得保留**）；但错误用结构化 Error，不用字符串 |
| 注入 `session.area` / `session.player` | 注入 `ctx.area` / `ctx.player`（显式上下文对象，不用隐式 session 字段） |
| ⚠️ `'waiting'` 字符串当并发错误 → 调用方当致命错误 | 锁 + 等待，不产生这种错误 |

```python
# jstm/handlers/guard.py
from functools import wraps

def area_handler(route: str, *, guard: bool = True, allow_states: set = frozenset()):
    """Area 类 handler 的前置守卫（参照 servers/area/filter/playerFilter.js）。

    做四件事：取玩家 → 定位 Area → 校验"玩家在场" → 注入 ctx.area / ctx.player
    """
    def deco(fn):
        @wraps(fn)
        async def wrapper(ctx: "HandlerCtx", msg: dict):
            if not guard:
                return await fn(ctx, msg)

            pid = ctx.session.player_id
            if not pid:
                return Err(Code.NOT_LOGGED_IN)

            # ① 取玩家（缓存两级 + 每玩家锁）
            player = await ctx.world.area_manager.get_or_load_player(pid)
            if player is None:
                return Err(Code.PLAYER_NOT_FOUND)

            # ② 定位 Area（显式 PlayerLocation，不猜）
            area = ctx.world.area_manager.get_area_by_player(player)
            if area is None:
                # 兜底：让客户端回到主城重进（保留参考实现的自愈能力）
                await ctx.world.message_service.send_to_player(
                    player, "onChangeArea", {"target": FALLBACK_AREA_ID})
                return Err(Code.AREA_NOT_FOUND)

            # ③ 校验玩家确实在场（★ 参考实现正是在这一步检查 route 是否 enterScene）
            if area.get_player(pid) is None and ContextState.IN_AREA not in allow_states:
                log.warning("player not in area, telling client to re-enter "
                            "player_id=%s area_id=%s route=%s", pid, area.area_id, route)
                await ctx.world.message_service.send_to_player(
                    player, "onChangeArea", {"target": area.area_id})
                return Err(Code.PLAYER_NOT_IN_AREA)

            # ④ 注入上下文
            ctx.player, ctx.area = player, area
            return await fn(ctx, msg)
        return wrapper
    return deco


# 使用（路由名与参考实现的 route 字符串保持一致，便于对照与限流统计）
@area_handler("area.playerHandler.move")
async def move(ctx: HandlerCtx, msg: dict) -> Result: ...

@area_handler("area.playerHandler.enterScene", guard=False)
async def enter_scene(ctx: HandlerCtx, msg: dict) -> Result:
    """enterScene 是唯一豁免守卫的路由（参考实现 playerFilter 里的特例）。
    JSTM 改为显式声明豁免，而不是靠 route 字符串后缀匹配（参考实现的
    `msg.__route__.search(/enterScene$/i) >= 0` 又慢又隐晦）。"""
```

**顺带保留参考实现的一个好设计：`loadAreaResource`（进服预下发资源清单）。** 它统计本场景各类型 `kindId` 去重集合，让客户端先加载资源。对 1.4.9 这类老客户端是刚需。

## 2.5 行为树 + TryAndAdjust

参考实现用外部 `pomelo-bt`（未打包，节点内部语义【待验证】），但**用法是明确可见的**：`Sequence / Select / Loop / If / Node` + `RES_SUCCESS / RES_FAIL / RES_WAIT` + 黑板。Python 侧约 120 行即可，**不需要任何外部依赖**。

```python
# jstm/ai/bt.py
from enum import IntEnum

class Status(IntEnum):
    SUCCESS = 1
    FAIL    = 2
    WAIT    = 3          # "这一 tick 还没做完，下一 tick 继续"

class Node:
    def __init__(self, blackboard: "Blackboard"): self.bb = blackboard
    def tick(self) -> Status: raise NotImplementedError

class Sequence(Node):
    """顺序执行：任一子节点 FAIL → FAIL；全 SUCCESS → SUCCESS；有 WAIT → WAIT。"""
    def __init__(self, blackboard, children=None):
        super().__init__(blackboard); self.children = children or []; self._i = 0
    def add_child(self, c): self.children.append(c); return self
    def tick(self):
        while self._i < len(self.children):
            st = self.children[self._i].tick()
            if st == Status.FAIL:
                self._i = 0; return Status.FAIL
            if st == Status.WAIT:
                return Status.WAIT
            self._i += 1                      # SUCCESS → 下一个
        self._i = 0; return Status.SUCCESS

class Select(Node):
    """选择执行：任一子节点 SUCCESS → SUCCESS；全 FAIL → FAIL；有 WAIT → WAIT。
    （参考实现 tiger 脑的根节点就是 Select）"""
    def __init__(self, blackboard, children=None):
        super().__init__(blackboard); self.children = children or []; self._i = 0
    def add_child(self, c): self.children.append(c); return self
    def tick(self):
        while self._i < len(self.children):
            st = self.children[self._i].tick()
            if st == Status.SUCCESS:
                self._i = 0; return Status.SUCCESS
            if st == Status.WAIT:
                return Status.WAIT
            self._i += 1                      # FAIL → 试下一个
        self._i = 0; return Status.FAIL

class Loop(Node):
    """循环 until loopCond(bb) 为假。参考实现：tiger 的循环攻击。
    ★ 注意：参考实现里 loopCond 判定"目标是否变化"，变了就跳出循环。"""
    def __init__(self, blackboard, child, loop_cond):
        super().__init__(blackboard); self.child = child; self.loop_cond = loop_cond
    def tick(self):
        if not self.loop_cond(self.bb):
            return Status.SUCCESS
        st = self.child.tick()
        return Status.WAIT if st in (Status.SUCCESS, Status.WAIT) else Status.FAIL

class If(Node):
    """条件分支：cond(bb) 为真则执行 action，否则 FAIL。"""
    def __init__(self, blackboard, cond, action):
        super().__init__(blackboard); self.cond = cond; self.action = action
    def tick(self):
        return self.action.tick() if self.cond(self.bb) else Status.FAIL

class TryAndAdjust(Node):
    """★ 参考实现最值得学的自定义节点（ai/node/tryAndAdjust.js，原文语义）：

        Select[ tryAction,
                Sequence[ adjustAction, tryAction ] ]

    即"先直接试；不行就先调整（走过去/换个位置）再试一次"。
    一个节点同时服务"攻击/拾取/对话"三种意图——这是这套 AI 最优雅的地方。
    """
    def __init__(self, blackboard, try_action, adjust_action):
        super().__init__(blackboard)
        self._seq = Sequence(blackboard, [adjust_action, try_action])
        self._sel = Select(blackboard, [try_action, self._seq])
    def tick(self) -> Status:
        return self._sel.tick()
```

黑板 + 按名注册（照搬参考实现 `ai/service/{aiManager,brainService}.js` 的机制，但修掉"所有怪共用 tiger"的偷懒）：

```python
# jstm/ai/blackboard.py
class Blackboard:
    """参考实现：Blackboard.create({manager, area, curCharacter})，运行期再挂
    curTarget / targetPos / moved / distanceLimit。JSTM 用显式字段避免拼写错误。"""
    __slots__ = ("manager", "area", "cur_character", "cur_target",
                 "target_pos", "moved", "distance_limit")
    def __init__(self, manager, area, cur_character):
        self.manager, self.area, self.cur_character = manager, area, cur_character
        self.cur_target = None
        self.target_pos = None
        self.moved = False
        self.distance_limit = 0

# jstm/ai/brain_service.py
class BrainService:
    """参考实现：fs.readdirSync(brain) 自动注册；getBrain 里
    `if (type !== 'autoFight' && type !== 'player') type = 'tiger';` ← 所有怪共用一套脑。

    JSTM：保留"按名注册 + clone"机制，去掉"一律 tiger"的兜底——
         改为显式按 monster 配置的 brain_id 选脑，缺失则报错（配置问题不掩盖）。"""
    def __init__(self): self._brains: dict[str, Callable] = {}
    def register(self, name: str, factory: Callable[[Blackboard], Node]) -> None:
        self._brains[name] = factory
    def create(self, brain_id: str, bb: Blackboard) -> Node:
        factory = self._brains.get(brain_id)
        if factory is None:
            raise KeyError(f"unknown brain_id={brain_id!r}; registered={sorted(self._brains)}")
        return factory(bb)

def autoload_brains(brain_dir) -> dict[str, Callable]:
    """目录扫描自动注册（对应参考实现 ai/ai.js 的 readdirSync）。"""
    import importlib, pkgutil
    brains = {}
    for m in pkgutil.iter_modules([str(brain_dir)]):
        mod = importlib.import_module(f"{brain_dir.name}.{m.name}")
        if hasattr(mod, "NAME") and hasattr(mod, "build"):
            brains[mod.NAME] = mod.build          # 约定：NAME = brain 名，build(bb) → Node
    return brains
```

**骨架照搬参考实现（tiger / player 两棵树）**：

```python
# jstm/ai/brain/tiger.py —— 怪物
NAME = "tiger"
def build(bb: Blackboard) -> Node:
    attack = TryAndAdjust(bb,
        try_action=TryAttackAction(bb),
        adjust_action=MoveToTargetForAttackAction(bb))

    def has_target(b):
        """目标存在且是玩家（参考实现 tiger.haveTarget 的语义）。"""
        t = b.area.get_entity(b.cur_character.target)
        if t is None:
            b.cur_character.forget_hater(b.cur_character.target)
            b.cur_target = None
            return False
        if t.type == EntityType.PLAYER:
            b.cur_target = t.entity_id
            return True
        return False

    loop_attack = Loop(bb, child=attack,
        loop_cond=lambda b: b.cur_target is not None and b.cur_target == b.cur_character.target)
    attack_if = If(bb, cond=has_target, action=loop_attack)

    def no_target(b):
        return b.area.get_entity(b.cur_character.target) is None

    patrol_if = If(bb, cond=no_target, action=PatrolAction(bb))

    return Select(bb, [attack_if, patrol_if])
```

**怪物 AI 的边界（照搬参考实现 `ai/action/moveToTarget.js`，这个数值很关键）：**

```python
LEASH_RANGE = 500        # |x - spawn_x| > 500 或 |y - spawn_y| > 500 → 脱战回家
def tick(self):
    ch, tgt = self.bb.cur_character, self.bb.area.get_entity(self.bb.cur_target)
    if tgt is None or tgt.died:
        ch.forget_hater(self.bb.cur_target); self.bb.cur_target = None
        return Status.FAIL
    if in_range(ch, tgt, self.bb.distance_limit or 200):
        self.bb.area.actions.abort(ActionType.MOVE, ch.entity_id)
        self.bb.distance_limit, self.bb.moved = 0, False
        return Status.SUCCESS
    if ch.type == EntityType.MOB and (abs(ch.x - ch.spawn_x) > LEASH_RANGE
                                      or abs(ch.y - ch.spawn_y) > LEASH_RANGE):
        ch.forget_hater(self.bb.cur_target)          # ★ 脱战
        self.bb.moved = False
        return Status.FAIL
    ...  # 首次 move(target)；目标移动且距离近则重算（照搬参考实现的两段逻辑）
    return Status.WAIT
```

## 2.6 分阶段实施

| 阶段 | 内容 | 可验证产出 |
|---|---|---|
| **E1 出网双通道** | `MessageService.send`（唯一落点 + 失败限速踢人）+ `Channel`/`ChannelService`（共用 send）+ `send_by_aoi` | 定向与频道推送都走同一个 `send`；断网玩家的连续失败能触发一次清理；`send_by_aoi` 返回实际送达数 |
| **E2 迁移适配层** | `RemoteFacade` 骨架 + 纪律（薄转发）+ 退休流程文档 | handler 层 0 处直接引用具体 service |
| **E3 配置表** | `DataTable` + `DataApi.load`（启动期校验 + 不可变） | 故意写错一列字段名 → **启动即失败**并指出表名与列名 |
| **E4 前置守卫** | `@area_handler` 装饰器 + 结构化 Error + `enterScene` 显式豁免 | 玩家不在场时自动推 `onChangeArea` 且不崩；并发首登不丢请求（对比参考实现的 `'waiting'`） |
| **E5 行为树** | `bt.py`（Sequence/Select/Loop/If/TryAndAdjust）+ `BrainService` + tiger/player 两棵树 + 巡逻状态机 | 单测覆盖：`TryAndAdjust` 的四种状态转移；怪的追击→脱战→巡逻回位全链路（参考项目有现成的 `test/ai/brain/*.js` 可作测试用例来源——**只借用例设计，不抄代码**） |

---

# 第 3 部分：开放问题（★ 已于本轮全部决策 —— 回执见文末「第 4 部分」）

**决策结果：Q1 = 3.0s；Q2 = 客户端必须上传整条路径；Q3 = 需要 P1 骨架（已交付）。**
下文保留原始问题与选项，便于回溯取舍理由。

我在本文里做了三处**主动取舍**，它们会直接影响手感与工作量，建议你定一下（不定我就按"推荐值"往下走）：

| # | 问题 | 选项 | 我的推荐 | 影响面 |
|---|---|---|---|---|
| **Q1** | **3s 分频取 3.0s 还是复刻 3.1s？** 参考实现因 `timeCount>30→归零` 实际是 **31 tick = 3.1 s**；这直接决定 HP/MP 恢复速率，`hp_speed` 的数值口径要跟着变 | (a) 3.0s 精确，重新标定 `hp_speed`；(b) 严格 3.1s 复刻手感 | **(a) 3.0s** —— 好解释、好测；但**如果 1.4.9 的客户端表现/数值表是按 3.1s 标定的**，就必须选 (b) | 数值对齐、玩家回血手感 |
| **Q2** | **移动协议：1.4.9 客户端是否必须"上传整条路径"？** 若是（大概率），则服务端主导模式不可行，只能走"接受 + 严格校验" | (a) 接受整条路径 + 5 项校验（L1+L2）；(b) 服务端算路径下发（L3，需客户端支持） | **(a)** —— 在**未确认客户端能力前**，(b) 有协议不兼容风险 | 反外挂强度、与客户端兼容性 |
| **Q3** | **要不要我现在直接产出 `server/` 下的 Python 骨架代码？**（可运行的 P1：ticker + 五层容器 + 空世界） | (a) 只要这份设计文档；(b) 生成 P1 可运行骨架；(c) 生成到你指定的路径 | 你定 | 工作量与交付形态 |

**另有两个与本文相关、但需要看客户端才能定的问题（标【未知】，非阻塞）：**
- `GLOBAL_CHANNEL = "pomelo"` 这个字面量是否被 1.4.9 客户端硬编码依赖？若否，建议改成语义名 `"world"`。
- 客户端是否内置了 Pomelo 的 `dictionary.json` route→数字 压缩表？（若内置，JSTM 必须复刻该表；否则不必。）

---

## 附：本文相对于 6 份审计报告的增量

| 类型 | 数量 | 内容 |
|---|---|---|
| **更正** | 2 | ① `messageService` 不是唯一出口（实为双通道）；② `errHandler` 的惰性掉线检测是**空操作**（uid/playerId 错配） |
| **新增核验事实** | 6 | ① 精确分频表（1s=刷怪 / 3.1s=玩家update+踢人）；② HP/MP 恢复的唯一驱动点与口径陷阱；③ `Revive` 走 100ms 精度；④ `config/instance.json` 是死配置；⑤ Area 构造器有启动副作用；⑥ `MobZone` 实际刷怪周期 ≈5s |
| **新增设计** | 5 | ① 单一全局 ticker（确定性顺序 + 绝对时间戳 + 预算降级）；② `PlayerLocation` 显式状态取代"猜归属"；③ 出网双通道共用底层 `send` + 失败限速踢人；④ 五层容器的 Python 类/签名；⑤ `bt.py` 行为树（含 `TryAndAdjust` 的四种状态转移） |
| **新增决策表** | 30 条 | 场景骨架逐项【保留/改造/丢弃】+ 理由 |

---

# 第 4 部分：决策回执 + P1 骨架交付（本轮）

## 4.1 决策回执

| # | 决定 | 落地位置 | 影响 |
|---|---|---|---|
| **Q1** | **3.0s**（精确，不复制参考实现的 31 tick = 3.1s） | `server/world/ticker.py` 用**绝对时间戳** `next_1s += 1.0` / `next_3s += 3.0`；`consts.HP_TICK_SECONDS = THREE_SECONDS = 3.0` | ① 无 31-tick 漂移；② **`hp_speed` 必须按 3.0s 口径重新标定**，提供 `hpmp_recalibrate(target_full_seconds, max_hp)` 与 `hp_speed_to_3s()` |
| **Q2** | **客户端必须上传整条路径** ⇒ 服务端主导路径（L3）不可行，走「**接受整条路径 + 严格校验**」 | `server/world/move.py#validate_client_move` + `server/world/guards.py#move` | 8 项校验：点数上限 / 起点一致（带容差）/ 每点可走 / **每段直线可达** / 单段上限 / 总长上限 / 限流 / 拒绝后强制回位推 `onStand` |
| **Q3** | **需要** P1 骨架 | `server/world/`（12 个文件）+ `server/world/tests/` | 复用既有 `aoi.py` / `pathfind.py`；`python -m world.demo` 全绿；`python -m unittest world.tests.test_world` 40 项全绿 |

## 4.2 ★★ 接入时发现的两个真问题（这是本轮最有价值的产出）

### 问题 1：`pathfind.verify_path()` **不能**用于客户端路径（Q2 直接踩中）

- `verify_path()` 的规则是「**每一步必须相邻**」（`abs(b-a) > 1 → 拒绝`），那是给**服务端生成的稠密路径**用的。
- 而 **Q2 确认客户端上传的是压缩后的航点列表**（相邻航点往往相隔数格）⇒ 用它校验会**把所有合法移动全部拒掉**。
- 更糟的是反向风险：若为了"能用"而放宽成"只查每点可走"，就**丢掉了防穿墙的核心校验**。
- **因此 `world/move.py` 另写 `validate_client_move()`：逐段 `line_of_sight`（Bresenham）校验**，同时覆盖「相邻格」与「远距离航点」两种形态。
- 已写成**回归测试** `test_pathfind_verify_path_would_reject_sparse`：同一个稀疏路径，`verify_path` 拒绝、`validate_client_move` 接受。
- ⚠️ 附带发现：`pathfind.py` 头部写着「**客户端永远不能提供路径，只能提供目标点**」——这与 Q2 事实**相反**，其设计前提已被证伪。建议修订该文档串，避免后续实现者按错误前提接线。
- ✅ 依赖说明：`validate_client_move` 的**禁贴角穿缝**能力继承自 `pathfind.bresenham_points` 的 P4b 修复（LOS 本身已禁穿角）；已用 `test_corner_cut_rejected` 把该依赖锁成回归测试。

### 问题 2：既有 `aoi.py` 的 `add_watcher/add_object` **不派发事件** ⇒ 进场玩家互相看不见

- 参考项目靠 AOI 的 `add` 事件（`onPlayerAdd`）让"已有玩家得知新玩家进来"；而既有 `aoi.py` 的注册函数**只登记、不产生 enter 事件**。
- 后果：**新进场玩家的快照里没有后来者，后来者也不知道他存在** ⇒ 两人互相看不见（一端瞎）。
- **修复：`Area._announce_aoi_entry()`** —— 注册后立刻 `aoi.move(eid)`（**不传坐标 = 只重算视野**）：
  - **只派发 `watch_events`**（通知"别人看到了新实体"）；
  - **丢弃 `self_events`**（新玩家自己的可见列表已由 `area_info_strip()` 快照给出，再推会重复）；
  - 但**必须调用**，因为它会初始化 `seen` / `_old_watchers` —— 否则该实体第一次移动时会产出大量**重复 enter/leave**。
- 已写成回归测试 `test_entry_notifies_existing_watchers` / `test_leave_notifies` / `test_move_produces_diff_events`。

## 4.3 单测抓出的两个实现级 bug（骨架自身，已修）

| # | bug | 症状 | 修复 |
|---|---|---|---|
| 1 | **`empty_time = 0.0` 的 falsy 陷阱** | `Instance.is_alive()` 里 `if self.area.empty_time and (...)` —— 当 `empty_time == 0.0`（可注入时钟起点为 0）时判据恒假 ⇒ **空副本永远回收不掉** | `empty_time` 改为「绝对时间戳 或 `None`」；`is_alive()` 用 `is None` 显式判断 |
| 2 | **`ActionManager.__len__` 把已 abort 的动作算进去** | `abort_all()` 后 `len(actions)` 仍 > 0（队列条目要等下次 update 才被跳过）⇒ 但"是否还有动作"的判断会失真 | `__len__` 改为 `len(self._by_key)`（只数活跃动作） |

> 这两处都是"**看起来对、边界才炸**"的类型，正好印证了 4.2/4.3 的结论：**五层骨架的价值在于把这类隐式状态显式化**。

## 4.4 并发提示（重要）

本轮进行到一半时发现 `server/aoi.py` / `pathfind.py` / `mock_server.py` 的**大小与 mtime 发生了变化**（有并发的协作者在改服务端）：

| 文件 | 我读到的版本 | 交付时的版本 |
|---|---|---|
| `aoi.py` | 16599 B | **19062 B**（新增 `add_player()` = A9 修复、`watchers_seeing()`） |
| `pathfind.py` | 9944 B | **14861 B**（新增 `bresenham_points` / `walk_until_blocked` / `forward_to` / `path_for_walk`；`verify_path` 补 P4 禁穿角；LOS 补 P4b） |
| `mock_server.py` | 313909 B | **323296 B** |

**我的骨架已对"当前版本"验证通过（40 项单测 + 演示全绿）**，并做了两处向前兼容：
- `Area.add_entity` 优先调用 `aoi.add_player()`，旧版本没有该方法时回退到 `add_watcher + add_object`；
- 禁穿角不自己实现，而是依赖 `bresenham_points` 的 P4b 修复（并用回归测试锁定）。

## 4.5 交付清单

| 文件 | 作用 |
|---|---|
| `server/world/__init__.py` | 包入口与公开 API |
| `server/world/_deps.py` | **复用** `server/aoi.py` / `pathfind.py`（不重复实现） |
| `server/world/consts.py` | 分频/容量/枚举/返回码（`HP_TICK_SECONDS=3.0`） |
| `server/world/ticker.py` | 单一全局分层 ticker（同步 `step()` + 线程驱动 + 预算 + defer + 埋点） |
| `server/world/message.py` | 出网双通道（定向 + 频道）**共用同一 `send()`**；失败限速踢人 |
| `server/world/entities.py` | Player/Mob/Item/PlayerLocation + **3.0s 口径恢复** + `hpmp_recalibrate()` |
| `server/world/move.py` | **`validate_client_move()`（Q2 落地）** + ActionManager + MoveAction |
| `server/world/area.py` | Area（世界）：三索引 + AOI 双注册 + `_announce_aoi_entry` + 三层 tick + 刷怪区 |
| `server/world/containers.py` | AreaManager / Scene / Instance / InstancePool / TTLCache |
| `server/world/guards.py` | `@area_handler` 前置守卫 + 示例 handler（`enter_scene` / `move`） |
| `server/world/demo.py` | **可运行演示**（18 项断言，退出码 0/1） |
| `server/world/tests/test_world.py` | **55 项单测**，覆盖分层/校验/AOI/恢复口径/身份与清理/副本回收/桥接 |

## 4.6 ★ 接入 `mock_server`：发现"已有接线"，因此**改为桥接而非重写**

### 4.6.1 关键发现：协作者**已经**做了 10204 的 AOI 接线

`mock_server.py` 里已存在一套标注"第二阶段"的实现（约 2026-09-18）：

| 已有函数 | 作用 |
|---|---|
| `_scene_enter / _scene_ensure / _scene_leave` | 进/离场景，调用 **`aoi.add_player()`**（即 A9 修复后的双注册） |
| `_scene_validate_move(h, rid, x, y, cmd)` | 可走性 + **可选**限流；**拒绝时返回服务端权威坐标** |
| `_scene_apply_move(h, rid, x, y)` | `aoi.move()`（A4 一次双向）+ 返回 `watchers_seeing(rid)` |
| `_scene_broadcast_10204(...)` | 按 watcher 集合广播 SC_10204（**已接受 watcher 作参数 ⇒ 天然解耦**） |
| `_LAST_POS[rid]` | 服务端权威坐标 |
| 开关 | `aoi_broadcast`（默认 True）、`move_rate_limit`（**默认 False**）、`aoi_view_range`（15）、`aoi_tower_size`（8） |

并且注释里已经写明一条**关键校结论**（引 `aoi_pathfind_review.md` P5）：
> 「12 格/秒是拍的，**未按真机 10204 标定前打开会误杀正常玩家**」

⇒ **这就是 Q2 的安全关切，协作者已经想过并刻意把校验默认关了。** 我若再写一条 10204 通路，就正好制造了我在审计里反复点名的"**两套实现并存**"陷阱（参考项目 `areaManager.changeArea` vs `areaService.changeArea`）。

**因此本轮决定：不新增第二条 10204 通路，不修改 `mock_server.py`，改为交付一个 dormant 的桥接层。**

### 4.6.2 协议修正：10204 是**单点**，不是整条路径

依据 `analysis/jstm_1.4.9/movement_protocol.md`（项目自有审计，真机已验证）：

| CMD | 形态 | 状态 |
|---|---|---|
| **10204** | `CS_10204{x:u16,y:u16}` → `SC_10204{rid,srv_id,x,y}` | ✅ **客户端逐步上报单个坐标**，已通 |
| 10205 | 瞬移 | ✅ |
| 点击自动寻路 | 「客户端发**目标点**」应走寻路协议 | ❌ **CMD 仍待定位** |

⇒ 这修正了我先前的表述：**Q2 的"整条路径"对应的是那个尚未定位的寻路 CMD**；10204 本身是单点上报。
⇒ 因此校验器**分两套**，不可混用：
- `validate_step_move()` ← **10204 单点**（本轮新增）
- `validate_client_move()` ← **未定位的寻路 CMD**（Q2 预留，已就绪待接）

### 4.6.3 桥接层的边界（沿用"AOI 绝不碰 socket"原则）

```
world/ 负责【谁应该看见我】(决策)          mock_server 负责【怎么发包】(I/O)
   ├─ get_or_load_player / add_entity        ├─ pack_frame / sendall
   ├─ validate_step_move                     ├─ LIVE_CONNECTIONS 遍历
   └─ aoi.watchers_seeing(rid) ──set──────▶  └─ _scene_broadcast_10204(..., watchers)  ← 原样保留
```

`attach(ns)` 只重绑 **5 个判定函数**，**`_scene_broadcast_10204` 一律不动**（单测断言其 `__module__` 仍为 `mock_server`）。

### 4.6.4 激活方式（dormant by default，可整段回退）

`config.json` 加 `{"world_bridge_enabled": true}`，再在 `mock_server.py` 的 `_scene_broadcast_10204` 之后插入 4 行：

```python
try:                                   # ← 世界层桥接（默认关闭，见 world/jstm_bridge.py）
    from world.jstm_bridge import attach as _attach_world_bridge
    _attach_world_bridge(globals())
except Exception as _e:
    print('!! world bridge attach failed: %r' % (_e,))
```

> ⚠️ **我没有替协作者加这 4 行**，理由：该文件正由协作者拥有（单文件单负责人），且他刚在同一区域做过零回归设计；插入位置/时机应由该负责人定。**这是一段 4 行、可整段删除的回退型改动。**

### 4.6.5 验证（三层，全部通过）

| 层级 | 手段 | 结果 |
|---|---|---|
| 单测 | `python -m unittest world.tests.test_world` | **55 项全绿**（含桥接的 dormant/替换范围/fail-open/uid≠rid） |
| **真实命名空间 drop-in** | `import mock_server` 后 `attach(mock_server.__dict__, enabled=True)` | 所需 12 个 ns 键**全部存在**；恰好替换 5 个；`_scene_broadcast_10204` 仍属 `mock_server`；`area_id` 正确推导为 10001 |
| **功能端到端** | 两个模拟客户端走**真实的** rebound 函数 | 2 次进场 → `player_num=2`；可走⇒`None`；越界 (999,999)⇒拒绝并回权威坐标 (10,10)；`apply_move` 返回**互相可见** `{1002}` / `{1001}`；`_scene_leave`⇒`player_num=1` 且进缓存；**errors=0** |

### 4.6.6 保留的既有约定（不可违反）

| 约定 | 出处 | 桥接层的处理 |
|---|---|---|
| 校验失败 → 回**服务端权威坐标**，不静默丢弃 | `_scene_validate_move` 注释 | `validate_step_move` 的 `corrected=last_pos`，桥接层原样转交 |
| 限流**默认关闭**（未标定会误杀） | `aoi_pathfind_review.md` P5 | `enforce_rate_limit` 默认 False；`max_step` 默认 None |
| 异常一律放行（fail-open） | `mock_server` 既有设计 | 桥接层每个方法 try/except，异常仅计数(`errors`)并放行 |
| uid ≠ rid | 参考项目 errHandler 的教训 | `Player.uid = rid + 900000`（或读 `role_state.uid`），并有单测断言 |

### 4.6.7 复验记录：`mock_server.py` 仍在被并发修改

本轮内该文件**又变了两次**（313909 B → 323296 B → **330990 B**，mtime 22:09:49 → **22:47:53**），
即**在我做 drop-in 验证之后约 20 秒**又被改了一次 ⇒ 协作者正在同一区域活跃开发。

**这正面印证了「不修改 `mock_server.py`、只交付 dormant 桥接层」是对的**（否则必然冲突）。

因此我对**最新版本**重新做了一次契约复验，结论是桥接层依然可 drop-in：

| 复验项 | 结果 |
|---|---|
| 12 个依赖的命名空间键 | **全部存在**（无缺失） |
| 6 个函数的签名 | `_scene_enter(handler)` / `_scene_ensure(handler)` / `_scene_leave(handler)` / `_scene_validate_move(handler, rid, x, y, cmd)` / `_scene_apply_move(handler, rid, x, y)` / `_scene_broadcast_10204(src, rid, srv_id, x, y, watchers)` —— **与桥接层的位置参数顺序逐一吻合** |
| `attach(enabled=True)` | 恰好替换 5 个判定函数 |
| `_scene_broadcast_10204` | `__module__` 仍为 `mock_server`（未被接管） |

> ⚠️ 该文件仍在变动中，**激活前请由它的负责人再跑一次** `python -c "import mock_server; from world.jstm_bridge import attach; print(attach(mock_server.__dict__, enabled=True))"` 确认契约未漂移。这条命令是只读的（不改文件），可安全重复执行。
