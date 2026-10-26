# 1.4.9 战斗模式与流程（实测 + 字节码双向取证）

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> 本文回答一个问题：**1.4.9 到底用什么战斗模式。**
> 结论不来自"现代游戏经验"，只来自 APK 字节码与协议。

---

## 一、结论（先给答案）

**1.4.9 使用「独立回合制战斗场景」，不是地图直接战斗。**

即：

```
地图（SceneModel / SceneView）
   ↓  点击怪物（Monster:clickHandler）
   ↓  GlobalEvent:Fire(SceneEvent.SCENE_MONSTER_CLICK, vo)
   ↓  SceneModel 的怪物点击回调
   ↓  BattleCtrl:csFightMon(vo)          → 发 CS_20002{mon_id}
   ↓  服务器回 SC_20002{code, msg}        （仅是应答/错误通道）
   ↓  服务器推 SC_20010{...}              ← ★ 真正的"进战斗"
   ↓  客户端【切到独立战斗场景】并创建战斗单位
   ↓  服务器逐回合推 SC_20012 / SC_20013   （技能 + 伤害）
   ↓  客户端播动画，播完回 CS_20014
   ↓  服务器推 SC_20020{result}            （胜负）
   ↓  服务器推 SC_20023{...}               （结算明细）
   ↓  客户端结算界面 → 回到地图
```

**判定依据**（三条，均为 1.4.9 本体证据）：

1. **客户端有一整套独立战斗场景代码**（`assets/src/game/battle/`，见下表），
   且 `battle.luac` 的方法表里有 `createBattleScene` / `enterFightFunc` /
   `exitFightFunc` / `initScene` / `blackScreen` / `fadeOut` / `fadeIn` /
   `addRole` / `calcTargetPos` / `initOrder` / `playOrder` / `playRoundStart` /
   `playMagic` / `result` / `escape` —— 这是**独立战斗场景**才需要的东西。
2. **协议段是 20000 段**（`battle_ctrl.luac` proto#0 的 `RegisterProtocal` 原文），
   含"对怪物发起战斗(20002)"、"战斗初始化数据(20010)"、"小回合战斗效果(20012)"、
   "回合开始(20013)"、"战斗结果(20020)"、"显示战斗结束界面(20022)"。
   这是**回合制战斗的消息序列**。
3. `battle_ctrl.luac` proto#10 `scFightData` 收到 `SC_20010` 后立即调用
   `Battle:playEnterEffect(data)`（并设置 `Director:getScheduler():setTimeScale`），
   `proto#13 scRoundStart` 调 `Battle:playRoundStart(data)` ——
   **20010 才是"进战斗"的触发点，而不是 20002。**

⇒ `SC_20002` 只是**成功/失败应答**：`scFightStart`（proto#5）的逻辑是
`if resp.code ~= TRUE then message(resp.msg) end`，成功时**什么都不做**。

---

## 二、触发链路的逐跳证据

### 2.1 怪物怎么出现在地图上（服务端下发）

`SC_10201` 的 `mons` 表（`protocol/manual.md`，字段顺序已由
`tools/proto_spec.py cmds 10201` 复核）：

```
mons: table(id:uint32, bid:uint32, type:uint8, name:string, realm:uint8,
            mspd:uint16, x:uint16, y:uint16, dir:uint8, res_id:string, status:uint8)
```

另有单独推送：

| CMD | 含义 | 字段 |
|---|---|---|
| 10212 | 附近有 MON 进入场景 | `id, bid, type, name, realm, mspd, x, y, dir, res_id, status, enter_effect` |
| 10213 | MON 移动 | `id, x, y` |
| 10214 | MON 状态改变 | `id, status` |
| 10215 | 有 Mon 离开场景 | `id` |
| 10220 | 删除角色、MON | `mon_ids, role_ids` |
| 10221 | 获取当前场景所有怪物坐标（挂机用） | `mons:table(id,bid,x,y)`（CS 为空） |

⇒ **怪物的坐标/外观/名字全部由服务端提供**，客户端 `Config.Map[*].mons`
实测**全表为空**（上一阶段结论，本阶段复核一致）。

### 2.2 点击 → 发请求

| 跳 | 文件与位置 | 证据 |
|---|---|---|
| 1 | `game/scene/element/monster.luac` proto#6 `clickHandler` | 字符串池含 `SCENE_MONSTER_CLICK`、`SceneEvent`、`GlobalEvent`、`Fire` |
| 2 | `game/scene/element/monster.luac` proto#5 `registEvent` | 绑定 `addTouchEventListener` → `clickHandler` |
| 3 | `game/scene/scene_model.luac` proto#15 `initEvent` | 字符串池含 `SCENE_MONSTER_CLICK` → `mon_click_event`（Bind 表） |
| 4 | `scene_model.luac` proto#32/#33 | 唯一外部调用是 `BattleCtrl:getInstance():csFightMon(...)` |
| 5 | `scene_model.luac` proto#36 `managerMonster` | 含 `csFightMon` + "单人挑战/组队挑战"确认框（难度提示） |
| 6 | `game/battle/battle_ctrl.luac` proto#3 `csFightMon` | 见下 |

`battle_ctrl.luac` proto#3 `csFightMon` 的反汇编要点：

```
self.last_fight 与 GameNet:getInstance():getTime() 比较，间隔 < 1 秒则 return（限流 1 次/秒）
proto = GameNet:getInstance():GetPrototype(20002)
proto.mon_id = <怪物 vo 的 id>          ← ★ 见下方"关键点"
self:SendProtocal(proto)
```

> ★ **关键点**：`mon_id` 取的是**怪物 VO 的 `id` 字段**（即 `SC_10201.mons[].id`，
> 场景内怪物实例 id），**不是** `bid`（怪物配置 id）。
> 服务端必须把 `SC_10201.mons[].id` 记住，并在收到 `CS_20002.mon_id` 时按它反查怪物。

### 2.3 客户端怪物数据对象

`game/scene/element/monster_vo.luac`（继承 `RoleVo`）字段：
`id, res_id, enter_effect, bid, realm, type, type2, is_client, model_size, spine_type, dir`。

⇒ 客户端的怪物 VO 字段与 `SC_10201.mons` 的字段**一一对应**，
说明服务端下发的就是这份数据。

---

## 三、战斗消息时序（严格按字节码，非推测）

| # | 方向 | CMD | 客户端行为（字节码证据） | 服务端职责 |
|---|---|---|---|---|
| 1 | C→S | **20002** | `csFightMon` 发 `{mon_id}` | 校验角色/怪物/场景/合法性 |
| 2 | S→C | 20002 | `scFightStart`：`code ~= TRUE` 则 `message(msg)` | 回 `code=1(TRUE), msg=''` |
| 3 | S→C | **20010** | `scFightData` → `Battle:playEnterEffect(data)` + 设置调度 `timeScale` | 下发全部战斗单位 |
| 4 | C→S | 20011 | `Battle:loadFinish` 主动发（空消息） | 可忽略/记录 |
| 5 | S→C | **20012** | `scFightRound` → `Battle:doNextFrame(callback)` | 下发本回合技能播放 |
| 6 | S→C | **20013** | `scRoundStart` → `Battle:playRoundStart(data)`；再 `GlobalEvent:Fire(WAVE_NUMBER)` | 下发本回合技能效果与**伤害** |
| 7 | C→S | **20014** | `playEnd` 主动发（空消息） | 推进下一回合 |
| 8 | C→S | 20009 | `csSelectSkill` 发 `{skill_id}`（玩家手动选技能时） | 记录选择 |
| 9 | C→S | 20008 | `setAuto` 发 `{flag}`（自动战斗开关） | 记录开关 |
| 10 | S→C | 20008 | `scAuto`：`{id, flag}` | 广播自动状态 |
| 11 | S→C | 20009 | `scSelectSkill`：`{skill_id}` | 广播选择结果 |
| 12 | S→C | 20015 | `scAddRole`（战斗中新增单位，如召唤） | 按需 |
| 13 | S→C | **20020** | `scFightEnd`：设置动画间隔，按 `result` 分支 | 下发胜负 |
| 14 | S→C | **20023** | `scFightEndData`：遍历 `role_hurl_list`，按 `srv_id` 过滤自己 | 下发伤害/结算明细 |
| 15 | S→C | 20022 | `hander_20022` → `openBattleFail(icon_list)` | 战败界面图标（按需） |

**回合循环**：5→6→7 会重复若干回合，直到 13。

**玩家主动技能**（`CS_20009{s kill_id}`）与**自动战斗**（`CS_20008{flag}`）
由客户端在回合内发出，服务端据此决定后续的 `SC_20012.skill_play`。

### 3.1 ★ 真机订正：客户端**不会**发 20011 / 20014

上一节第 4、7 步（客户端发 `CS_20011` 加载完成、`CS_20014` 动画播放完成）
是**按协议定义推断**的。真机实测（`logs/1.4.9/battle/battle_action.log`）：

| 观察 | 结果 |
|---|---|
| 客户端收到 `SC_20010` | ✅ 探针 `bt_in scFightData … fighter_info_list_{1:{rid=..` —— **解析成功** |
| 客户端是否发 `CS_20011` | ❌ **从未发出**（整场战斗 `tcp.log` 无 `cmd=20011`） |
| 客户端是否发 `CS_20014` | ❌ **从未发出**（无 `cmd=20014`） |
| 客户端收到 `SC_20020` 后 | ✅ **主动发了 `CS_20021`**（`csCloseFinishView`） |

⇒ **整场战斗会停在第一回合之前**，除非服务端自己推进。

**本阶段的做法**（已实测跑通）：服务端在 `SC_20010` 之后**自己按节拍推进**
（2.5 秒/回合，自续期）：

```
SC_20010 → (SC_20012 + SC_20013) × N → SC_20020 → SC_20023
```

`CS_20014` 仍然接收并记录，但**不作为推进的必要条件**。
（客户端为何不发 20014 **尚未定位** —— 可能与战斗场景资源/动画未就绪有关，
见 `report/battle_restore_status.md` §七 第 9 项。）

---

## 四、独立战斗场景的客户端证据（`battle.luac` 方法表节选）

`battle.luac` 共 150 个 proto、模块表定义 104 个方法。与"独立场景"直接相关者：

| 方法 | 作用 |
|---|---|
| `start` / `clear` / `exitFight` | 战斗生命周期 |
| `initScene` / `createBattleScene` | **创建独立战斗场景** |
| `enterFightFunc` / `exitFightFunc` | 进/出战斗的过场 |
| `blackScreen` / `blackScreen2` / `cancleBlackScreen` | 切场景黑屏 |
| `fadeOut` / `fadeIn` | 渐变 |
| `addRole` / `createBattleRole` / `roleReady` | 战斗单位 |
| `calcTargetPos` / `moveTo` / `moveToPos` / `moveBack` / `calcMoveTime` | 战斗内走位 |
| `initOrder` / `playOrder` | 出手顺序 |
| `playRoundStart` / `playMagic` / `playMagicEffect` | 回合与技能表现 |
| `attack` / `mutiAttack` / `flyItem` / `mutiFlyItem` | 攻击表现 |
| `effectUser` / `playSelfEffect` / `mutiHurtNum` | 特效与伤害数字 |
| `result` / `isFinish` | 结算 |
| `escape` | 逃跑 |
| `watchBattle` / `watchReplay` | 观战/录像（超范围） |

配套模块：`battle_view.luac`（战斗 UI，30 KB）、`battle_role.luac`（战斗单位表现，17 KB）、
`skill_act.luac`（技能动作，28 KB）、`battle_tips.luac`、`battle_fail.luac`、`fabao_select.luac`。

⇒ **客户端战斗 UI / 场景 / 动画 / 技能 / 伤害显示 / 结算界面全部已存在。**
按项目总原则，本阶段**不重做客户端 UI**，只让服务端提供其期待的数据。

### 4.1 ★ 追加实测：**战斗逻辑跑通了，但战斗画面没有建立**

用探针勾住 `Battle`（`battle.luac`）与 `BattleView`（`battle_view.luac`）的方法后，
实测一次完整战斗的调用轨迹（证据：`logs/1.4.9/battle/battle_render_chain.log`）：

**逻辑链（全部执行 ✅）**

```
playEnterEffect(data)        ← SC_20010
start(data)
createBattleScene(data)
addRole(我方 id=1 hp=4321 lev=7 rid=1001)
createBattleRole({1:…, 2:…})
addRole(敌方 id=2 hp=2400 lev=70 rid=0 animate_res={1:{ant_id,ant_val,ent_lev,dis_method}})
roleReady(...) ×2            ← add_act_spine=true，单位已 ready
playRoundStart(round=1..4)   ← SC_20013
playMagic(...)               ← 技能播放
result(result=1)             ← SC_20020
clear()
exitFight()                  ← 退出战斗
```

**视图链（只走了一半 ❌）**

| BattleView 方法 | 是否被调用 |
|---|---|
| `create` | ✅ 调用（创建 ui_layer / role_layer） |
| `createRole` | ✅ 调用 |
| `createEffect` | ✅ 调用 |
| **`loadBack`**（加载战斗背景 `BattleBG` / `bg_<sceneId>`） | ❌ **从未调用** |
| **`createUI`**（bc=1065 的战斗 UI 构建器） | ❌ **从未调用** |

`Battle:initScene` / `Battle:enterFightFunc` 同样**从未被调用**。

⇒ **结论**：客户端**执行完了整场战斗的逻辑**，但
**战斗背景与战斗 UI 都没有建立**，所以画面上看不到战斗（截图仍是地图）。

### 4.2 ⚠️ 根因**未定论**（一轮错误结论已更正）

**已确认的反汇编事实：**

1. `battle.luac` proto#4 `Battle:start` 在 bc#170 / bc#192 用
   `RenderMgr:getInstance():doNextFrame(<闭包>)` 注册了两个回调：
   - `proto#0` = `{ battle_scene:loadBack(SceneModel:getInstance().sceneId) }`
   - `proto#2` = `{ battle_scene:createUI(); enterFightFunc(); … }`
2. `game/scene/util/render_mgr.luac`：
   - `doNextFrame` (proto#12) = `table.insert(self.next_do_list, {fn1,fn2})`（**只入队**）
   - `update` (proto#10) = 唯一的出队者
   - `start` (proto#3) = 唯一调度 `update` 的地方
3. `RenderMgr:getInstance():start()` 由 **`SceneModel:sceneStart()`**
   （`scene_model.luac` proto#68，bc#92–98）**无条件**调用，
   且其后的 `createMap()`（bc#111）**确实跑过**（地图能渲染，本项目既有实测）

**观察到的现象：**

- 探针**看到** `BattleView.create` / `createRole` / `createEffect` 被调用
- 探针**没看到** `BattleView.loadBack` / `createUI` 被调用

**⇒ 事实 1+2+3 推出「两个回调应当被执行」，与观察矛盾，根因未定论。**

> ❌ **更正**：本文档上一版曾断言「`RenderMgr:start()` 只有 `map_view` 一处调用点，
> 未点地图 ⇒ 队列永不出队」。该结论基于**被截断的扫描输出**，**是错的** ——
> 完整扫描显示 `sceneStart` 才是常规调用点。详见
> `report/battle_restore_status.md` §9.9–§9.12。

**下一步（决定性实验，已写进探针）**：改为直接钩 `RenderMgr.doNextFrame` /
`RenderMgr.update`，并采样 `next_do_list` 长度、给队列里的闭包包一层 `pcall`
上报错误 —— 即可区分「探针漏钩 / 没进分支 / 闭包抛错」。

---

## 五、伤害发生在哪里（本阶段的关键结论）

`SC_20013.magic_play` 的字段（`cmd_resolve_200.luac` proto#35 **内联 spec**，权威）：

```
order@C##target_anger@H##target_id@H##source_id@H##hit@c##hp_max@I##hp@I##is_target_die@C##target_talk@s##magic_list@D|Dsc20013magic_list|
```

⇒ **掉血由服务端算好后逐条下发**：`hit` 是本次伤害，`hp_max`/`hp` 是受击者
结算后的血量，`is_target_die` 是死亡标记。

⇒ **服务端是战斗的权威**；客户端只负责播动画。
（客户端另有一套 `10601 测试战斗伤害` / `10610 战斗验算`，用于战斗模拟校验，
但落地血量仍以服务端 `SC_20013` 为准。）

---

## 六、★ 本阶段**未确认**的部分（不猜）

| 缺口 | 现状 |
|---|---|
| **战斗胜负如何变成经验/金币/掉落** | `SC_20020` 只有 `result:uint8`；`SC_20023` 只有 `role_hurl_list`/`val_list`/`msg`。**经验、金币、掉落都不在这两条战斗消息里。** 必须实测确定实际走哪条协议（候选：`10409 英雄加经验`、`12742 提示获得资产/物品`、`10302 角色数据刷新`、`10500/10501 背包推送`）。 |
| 怪物 HP / 攻击力 / 经验 / 金币 | `Config.Mon`（2645 条）**不含**这些数值（见 `monster_data_model.md`）。原版服务端数据，APK 内无法取证。 |
| `SC_20012` 的 `Dsc20012magic_play` / `Dsc20012summon_play` 内部布局 | 已用 `tools/dsc_spec.py` 还原（见 `battle_protocol_matrix.md` §4.6），**尚未上机验证**。 |
| `SC_20020.result` 的取值语义（1=胜？0=败？） | 未确认，需实测或从 `battle.luac` 的 `result` 分支进一步还原。 |

上述第 1 项是**本阶段最关键的未知**，将通过 `logs/1.4.9/battle/` 的实测抓取确定，
**不得凭经验填写**。
