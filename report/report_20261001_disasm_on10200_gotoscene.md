# 反汇编突破：`on10200 → model:changeScene` ｜ `gotoScene` 就是 **`10206` 的发送者**（并解释了"多数输入没反应"）

> 时间：2026-10-01 ｜ 文件：`assets/src/game/scene/scene_controller.luac`（47 个 proto）

---

## 〇、一句话结论

> ① **`on10200` 只有 6 条字节码**，做的事情是：**`self.model:changeScene(msg)`**
> ⇒ **"进场景/建视图"的真正逻辑在 `SceneModel:changeScene`**（不在 controller），
> 这就是下一步静态分析的目标（也解释了为什么探针里 `SceneView` 拿不到——视图由 model 那一侧建）。
>
> ② ★ **`gotoScene`（proto#41）不是建视图，而是 `CS_10206` 的发送者**：
> ```lua
> function SceneController:gotoScene(x)
>   if self.model:getIsOnFight() then return end
>   if GameNet:getInstance():getTime() == self.last_send_10206 then return end   -- ★ 时间门禁
>   self.last_send_10206 = GameNet:getInstance():getTime()
>   local p = ProtocalRulesMgr:getInstance():GetPrototype(10206)
>   p.x = x
>   self:SendProtocal(p)
> end
> ```
> ⇒ **`10206` = 客户端的"自动寻路/goto"请求，只带一个 `x`**（与 `fields.json` 的 `CS_10206 = x:uint32` 完全对上）。
> ⇒ 并且它被 **`GameNet:getTime()` 的"值是否变化"**卡住 ——
> **这解释了"我做了大量 tap/swipe，绝大多数都没有任何帧"**：
> 门禁基于**时间值**，值没变就直接 return。

---

## 一、本轮证据（逐条反汇编）

### 1.1 `on10200`（proto#8，bc=6）

```
0 TGETS model      1 MOV A=3 D=2      2 TGETS changeScene
3 MOV A=4 D=1      4 CALL A=2 D=259   5 RET0
⇒ self.model:changeScene(msg)        ← ★ 进场景逻辑在 **SceneModel:changeScene**
```

### 1.2 `gotoScene`（proto#41，bc=40）

```
0-6    if self.model:getIsOnFight() then return end
7-17   if GameNet:getInstance():getTime() == self.last_send_10206 then return end   ← ★ 时间门禁
18-25  self.last_send_10206 = GameNet:getInstance():getTime()
26-34  p = ProtocalRulesMgr:getInstance():GetPrototype(10206)
       p.x = <参数>                    ← 单参 x（与 CS_10206 = x:uint32 一致）
35-39  self:SendProtocal(p)
```

---

## 二、★ 这条发现**回头解释了两个此前的观测**

| 此前观测 | 现在有了机制解释 |
|---|---|
| round 58：`swipe 300,1250→620,1100` 触发了 **`10206`** | **不是轮询巧合** —— 是我的拖动触发了 `gotoScene()`，只是被时间门禁限制成"只发一次" |
| round 59/60：大量 tap/swipe **全是 0 帧** | `getTime()` 未变化 ⇒ `gotoScene()` 直接 return（**门禁机制**，不是"输入没到游戏"） |
| 探针里拿不到 `SceneView` 实例 | 视图由 **model 侧**（`SceneModel:changeScene`）创建，controller 不持有它 —— 需要换访问路径 |

> 这修正了我上一轮的部分判断：**"场景区拖动完全无反应"的表述过强** ——
> 至少 `gotoScene` 这条通路是**能被输入触发的（一次）**，只是被时间门禁掐住。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★ **定位 `10200` 的真实去向**：`on10200 → SceneModel:changeScene(msg)`（下一步目标）。
2. ★★ **查明 `10206` 的语义与门禁**：`gotoScene()` 发 `CS_10206{x}`，被
   `getIsOnFight()` 与 **`GameNet:getTime()` 值变化**双重门禁卡住。
3. ★ **回头解释了 round 58 的命中与 round 59/60 的全阴**（同一机制的两面），并**修正**了上一轮"完全无反应"的过强表述。
4. ★ 明确下一目标：`SceneModel:changeScene`（建场景/视图）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `SceneModel:changeScene` 里视图创建为何没完成 | ❌ 下一轮 |
| 2 | `GameNet.getTime()` 由谁设置（哪个服务端消息/字段） | **UNKNOWN**（若与我们有关，可用真值补齐） |
| 3 | 让真机自然操作发 `10204` | ❌ |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 四、下一轮施工单

1. ★ **反汇编 `SceneModel:changeScene`**（`game/scene/scene_model.luac`）：
   看它如何建视图/载地图、以及**会不会因为某个字段缺失而提前 return**
   （重点看它对 `10200` 的 `bid/code/line_id` 与 `10201` 的 `npcs/mons/elems` 的依赖）。
2. ★ **查 `GameNet.getTime()`**：搜 `gamenet.luac` 里 `getTime` 的实现与赋值点，
   确认时间来自**哪条服务端消息**；若来自某条我"通用应答"的命令（时间恒为 0），
   那就是**可修的服务端缺陷**（按真值补上时间）。
3. 若两者都指向"客户端内部" ⇒ 再回到探针路线（换访问路径 hook `SceneModel:changeScene` 打 traceback）。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_controller.luac` | ★ 本轮反汇编对象（`on10200` proto#8 / `gotoScene` proto#41） |
| 本报告 | ★ 两条关键结论 + 对既往观测的重新解释 |
| `analysis/1.4.9/movement/movement_test.md` | 既往线索（错误路径） |
