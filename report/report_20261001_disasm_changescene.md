# 反汇编 `SceneModel:changeScene` + 一个通道结论：**Lua print 不进 logcat**

> 时间：2026-10-01 ｜ 文件：`assets/src/game/scene/scene_model.luac`

---

## 〇、一句话结论

> ① **`SceneModel:changeScene`（proto#66，bc=80）不会因字段缺失提前 return** —— 它是一路往下走：
> ```lua
> print('===>>进入 ' .. msg.bid .. ' 前场景 ' .. self.sceneId .. ' 线路：' .. msg.line_id)
> self.scene_data:clear()
> self.line_id    = msg.line_id
> self.sceneId    = msg.bid          -- ★ 只依赖 msg.bid / line_id / x / y
> self.scene_data = msg
> self:sceneStart(msg)               -- ★ **建视图的逻辑在这里面**（下一个目标）
> GlobalEvent:getInstance():Fire(SceneEvent.TANCHAUNG, msg.bid)
> ```
> ⇒ ① 它**不挑字段**（只要 `bid` 等基本字段）⇒ **"我发的 10200 缺字段导致它提前 return"这条假设被否证**；
> ② **视图创建在 `sceneStart(msg)` 里** ⇒ 下一轮直接反汇编/挂钩它。
>
> ② ★ 想用 `print('===>>进入 …')` 这行**在客户端侧验证"10200 是否真进了 changeScene"**，
> 但实测**该 build 的 Lua `print` 不进 logcat**：`logcat -d | grep -c 'LUA-print'` = **0**，
> 按进程抓也只有 `JniHelper` 噪声。⇒ **这条路（读 print）不可用**，
> 要验证只能**在探针里挂钩** `changeScene` / `sceneStart` 并上报（下一轮）。

---

## 一、本轮证据

### 1.1 `changeScene` 反汇编（节选，proto#66）

```
 0-17  log('===>>进入 ' .. msg.bid .. ' 前场景 ' .. self.sceneId .. ' 线路：' .. msg.line_id)
18-20  self.scene_data:clear()
21-22  self.line_id = msg.line_id
23-24  self.sceneId = msg.bid
25     self.scene_data = msg
26-29  self:sceneStart(msg)
30-39  GlobalEvent:getInstance():Fire(SceneEvent.TANCHAUNG, msg.bid)
40-51  ChairModel:getInstance():getFlag() …（探床/椅子逻辑，与本问题无关）
```
**关键读法**：`sceneId` 直接取 `msg.bid`；**没有任何"若某字段为 nil/0 就 return"的分支**
⇒ `10200` 的 payload 只要 `bid` 合理，`changeScene` 就会执行到 `sceneStart`。

### 1.2 `on10200` → `changeScene` 的链路（上一轮已证）

`SceneController.on10200`（proto#8，6 条字节码）= `self.model:changeScene(msg)` —— 已经是**一行转发**。

### 1.3 Lua print 通道实测

```
$ adb shell "logcat -d | grep -c 'LUA-print'"        → 0
$ adb shell "logcat -d | grep -e '==>' -e '进入'"     → （无）
$ adb shell "logcat -d --pid=<game> -t 60"            → 只有 JniHelper: getJavaVM() 噪声
```
⇒ **该 build 的 Lua 日志不进 logcat**（与既往"探针落盘才是可靠通道"的经验一致）。

---

## 二、完成 / 未完成

### 2.1 完成
1. ★ **反汇编 `SceneModel:changeScene`** 并**否证**"它因缺字段提前 return"的假设（它不挑字段）。
2. ★ **把目标收窄到 `sceneStart(msg)`** —— 视图/地图构建几乎肯定在里面。
3. ★ **否证一条观测通道**：Lua `print` 不进 logcat（`LUA-print` 计数 0）⇒ 客户端侧验证必须走**探针挂钩**。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `sceneStart` 里视图创建为何没完成 | ❌ 下一轮（反汇编 + 探针挂钩） |
| 2 | "10200 是否真的进了 `changeScene`" | ❌ 需要探针挂钩验证（print 通道不可用） |
| 3 | 真机自然操作发 `10204` | ❌ |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 三、下一轮施工单（两条腿并行）

1. ★ **静态**：反汇编 `sceneStart`（在 `scene_model.luac` 里取 proto 号）——
   找它在哪里建视图、以及**是否有条件分支会跳过建视图**（重点：`scene_data` 里的
   `npcs/mons/elems/roles` 是否被用于**决定是否创建**）。
2. ★ **动态**：探针 v52 挂钩 `SceneModel.changeScene` 与 `SceneModel.sceneStart`，
   上报**是否被调用 + 入参字段（bid/line_id/x/y）**：
   - 若 `changeScene` **被调用**而 `sceneStart` 没走到 ⇒ 卡在 `scene_data:clear()` 等步骤；
   - 若两者都**没被调用** ⇒ **我发的 `10200` 没到/没被解析** ⇒ 回头查 `10200` 的 SC 形状与触发时机
     （注意：`10200` 的 `code` 我已按既往实机结论设为 **0**）。
3. 顺带：`GameNet.getTime()` 的赋值点（round 61 遗留）—— 它门禁着 `gotoScene/10206`。

---

## 四、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_model.luac` / `analysis/scene_controller.luac` | 反汇编对象 |
| 本报告 | ★ `changeScene` 不挑字段（否证） + 目标收窄到 `sceneStart` + Lua print 通道不可用 |
