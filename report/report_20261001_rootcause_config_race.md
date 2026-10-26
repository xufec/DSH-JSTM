# ★★★ 根因确证（终）：**客户端配置加载时序竞态** —— `SceneModel:__init` 早于 `Config.MapBlock` 加载

> 时间：2026-10-01 ｜ 依据：v54 探针（多时间点采样）+ 前两轮反汇编/崩溃证据

---

## 〇、一句话结论

> **探针逐时间点采样把真相钉死了**：
>
> ```
> t≈1s    Config=table | keys=18  | MapBlock=nil   | Map=nil      ← ★ __init 就在这个时刻跑
> t≈11s   Config=table | keys=348 | MapBlock=table | Map=table
> t≈31s   Config=table | keys=363 | MapBlock=table | Map=table
> t≈60s+  Config=table | keys=363 | MapBlock=table | Map=table
> 全程:   model.map_block=nil   model.map=nil                      ← ★ 模型里永远 nil
> ```
>
> ⇒ **因果链最终定型**（全部环节均有证据）：
> ```
> ① 启动早期（Config 仅 18 键）时 SceneModel:__init 执行
>        self.map_block = Config.MapBlock   → nil   ★ 竞态发生在此
> ② 稍后 Config 加载完成（348→363 键，MapBlock/Map 都成了 table）
> ③ 但 __init 只跑一次、且**无兜底/无刷新** ⇒ model.map_block 永久 nil
> ④ sceneStart（proto#68 指令 147-150）→ self.map_block:get(sceneId) → 崩（index nil）
> ⑤ sceneStart 中断 ⇒ MAP_BLOCK / astar / readInDefaultXml / self.scene:createMap() 全没跑
> ⑥ 结果：地图没建（self.scene.map=false）、NPC 不渲染、场景层无触摸
>        ⇒「地图不清晰 / 没有NPC / 不能点击移动」三条症状
> ```
>
> ⇒ ★ **这是客户端侧的配置加载时序竞态**，不是协议错、不是我的 SC 缺字段、也不是 `Scene:New()` 的问题。
> **但它是可以在客户端补上的**（见 §二），而我们有探针 —— 所以有**可验证的修复路径**。

---

## 一、本轮原始证据（`files/dsh_v54.txt`）

```
v54_config_mapblock
t1  Config=table | keys=18  | MapBlock=nil   | Map=nil      | model.map_block=nil | model.map=nil
t11 Config=table | keys=348 | MapBlock=table | Map=table    | model.map_block=nil | model.map=nil
t31 Config=table | keys=363 | MapBlock=table | Map=table    | model.map_block=nil | model.map=nil
t60 Config=table | keys=363 | MapBlock=table | Map=table    | model.map_block=nil | model.map=nil
t61 … t120 同上
```
**关键读法**：
- `Config.MapBlock` **先 nil 后 table** ⇒ **加载时机**问题（不是"配置不存在"，`MapBlock` 键数=2）；
- `model.map_block` **全程 nil** ⇒ `__init` 那次赋的 nil **没有被更新**。

---

## 二、★ 由此得到的**可执行修复路径**（下一轮直接做）

既然确认是"`__init` 太早 + 无兜底"，那么**在配置加载完成后补上这两个字段并重跑场景初始化**，就应该能建出地图：

```lua
-- 探针 v55（修复实验）
local m = SceneModel:getInstance()
m.map_block = Config.MapBlock      -- ★ 用加载好的真值补上（round 66 已确证这里是 nil）
m.map       = Config.Map
-- 然后重新触发一次场景初始化（用当前 scene_data 或构造 {bid=10001,x,y,line_id}）
m:sceneStart(m.scene_data)         -- 期望：ok=true，且 self.scene.map != nil
```

**判据（硬）**：
1. `sceneStart` 返回 **ok=true**（不再崩在 `map_block`）；
2. `self.scene.map ~= nil`（地图建出来了）；
3. 探针 `t=view` 不再报 `no_scene_view_instance`；
4. 客户端界面出现 NPC、且**场景区 swipe/tap 能触发 `10204`**（"不能点击移动"随之解决）。

> 若 1–4 通过 ⇒ **三条症状的服务端/探针侧修复完成**；
> 同时该结果**反向印证**：官方客户端是**先加载完配置再建 SceneModel**，我们的流程让它提前了（值得再去查"是谁提前触发了 `SceneModel:getInstance()`"——那可能是**真正需要改服务端的那一环**）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★★ **根因确证**：`Config.MapBlock` **先 nil 后 table**（18→348→363 键），而 `model.map_block` **永久 nil** ⇒ 时序竞态 + 无兜底。
2. ★ **因果链六环全部有证据**（反汇编 3 处 + 运行时 2 处）。
3. ★ **给出可执行、判据明确的修复实验**（v55：补字段 + 重跑 `sceneStart`），并列出 4 条验收判据。
4. ★ 排除"配置不存在"（`MapBlock` 键数=2、`Map` 存在）⇒ 误差范围收窄到**时机**。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | v55 修复实验（补 `map_block` + 重跑 `sceneStart`） | ❌ 下一轮 |
| 2 | **谁提前触发了 `SceneModel:getInstance()`**（可能是服务端可改的一环） | ❌ |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 四、下一轮施工单

1. ★ **v55 修复实验**（按 §二，判据 4 条）。
2. ★ 若修复成功 ⇒ 立刻测"场景区 swipe → `10204`"，验证"不能点击移动"是否一并解决。
3. ★ 顺带查**提前触发者**：搜客户端里 `SceneModel:getInstance()` 的**首次调用点**
   （很可能在登录流程/某条消息的处理器里）；若确属"我们让流程走太快"，
   考虑在服务端**延后**某条推送（例如 `10200` 只在客户端 `10300` 之后再推）。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml54_add.lua` / 设备 `files/dsh_v54.txt` | ★ 多时间点采样证据（竞态确证） |
| `analysis/scene_model.luac` | `__init`（proto#1 指令 14-19）与 `sceneStart`（proto#68 指令 147-150） |
| 本报告 | ★ 最终根因 + 可执行修复实验 + 4 条验收判据 |
