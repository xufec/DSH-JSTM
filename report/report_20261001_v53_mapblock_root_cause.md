# ★★★ 根因定论：`sceneStart` 崩在 **`self.map_block:get(self.sceneId)`**（`map_block` 为 nil）

> 时间：2026-10-01 ｜ 依据：v53 探针（pcall 抓错误）+ `scene_model.luac::sceneStart` 反汇编（proto#68）

---

## 〇、一句话结论

> **三条症状（地图不清晰 / 没有NPC / 不能点击移动）的统一根因找到了，而且精确到字节码行**：
>
> ```
> v53 探针（pcall 手动调 sceneStart）:
>   手动调 sceneStart ok=false err=[string "game/scene/scene_model.luac"]:0:
>       attempt to index field 'map_block' (a nil value)      ← ★ 崩溃点
>
> sceneStart 反汇编（proto#68）:
>   147  self.map_block                       ← ★ 为 nil
>   148  self.map_block:get(self.sceneId)     ← ★ 在这一行崩（index nil）
>   151  <全局 MAP_BLOCK> = 上面的返回值
>   152-155  self.astar:clear()  …            ← 后面全都没跑
> ```
>
> ⇒ **`self.map_block`（地图块管理器）是 `nil`** ⇒ `sceneStart` **抛错中断**
> ⇒ 它后面的 `MAP_BLOCK` 赋值、`astar` 初始化、以及更早的
> `RenderMgr:getData():readInDefaultXml()` / **`self.scene:createMap()`** 等**全部没执行**
> ⇒ **地图没建、NPC 没渲染、场景层没有触摸处理器** ⇒ **三条症状一次性全解释**。
>
> 旁证（同一份 v53）：`self.scene=table`、**`map=false`**、`root=userdata`
> ⇒ 场景对象**存在但没有地图**，与"`createMap()` 没跑"完全一致。

---

## 一、本轮证据

### 1.1 v53 探针输出（`files/dsh_v53.txt`）

```
probe _G.Scene=nil | 带Scene的全局=[SceneMenu,GuildWarsSceneConst,GuildWarsSceneInfo,
      XianMoReadySceneView,SceneController,GuildWarsSceneList,XianMoSceneView,SceneView]
      | 类表.Scene=nil | self.scene=table | map=false | root=userdata | children=?
手动调 sceneStart ok=false err=…:0: attempt to index field 'map_block' (a nil value)     ← ★★
（其后每 20 秒采样都相同：self.scene=table / map=false）
```

### 1.2 `sceneStart` 的崩溃段（proto#68，指令 147-155）

```
147  TGETS  self.map_block
148  TGETS  self.map_block.get
149  TGETS  self.sceneId
150  CALL   self.map_block:get(self.sceneId)      ← ★ 此处 attempt to index nil
151  GSET   <全局 MAP_BLOCK> = 返回值
152  TGETS  self.astar
153-155        self.astar:clear()
```

---

## 二、★ 一处**自我更正**（诚实记录）

| 上一轮的判断 | 现状 |
|---|---|
| "探针看到 `_G.Scene=nil` ⇒ `Scene:New()` 抛错 ⇒ `sceneStart` 静默中断" | ❌ **作废**：真实错误是 **`map_block`**，与 `Scene` 无关 ⇒ 说明 `Scene` 在**模块内部**是可解析的（`_G.Scene=nil` 只是**探针视角**的假象 —— 我上轮已把它标为"待排除"，现在**排除**） |
| "首次 `self.scene=nil` ⇒ 会执行 `Scene:New()`" | ✅ 保持（`self.scene` 现在是 table，`root=userdata`） |

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★★ **定位根因到字节码行**：`sceneStart` 在 `self.map_block:get(self.sceneId)` 处因 `map_block=nil` 崩溃。
2. ★ **解释了全部三条症状**（地图/ NPC / 触摸全因为 `createMap()` 及其前置步骤没跑）。
3. ★ **旁证一致**：`self.scene` 存在但 **`map=false`**。
4. ★ **自我更正**上一轮关于 `Scene` 类的推断（作废），并把"私有 env"这一替代解释**排除**。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | **`self.map_block` 本该由谁设置**（客户端 init？某条消息？某张 config？） | ❌ 下一轮（决定"能否修、谁来修"） |
| 2 | 若是客户端 init 缺失 ⇒ 是否有**服务端可控**的触发条件 | ❌ |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 四、下一轮施工单（直指 `map_block` 的来源）

1. ★ **反汇编 `SceneModel:__init`（proto#1）**：看它是否本来要赋 `self.map_block`（例如
   `self.map_block = Config.MapBlock` 或 `<某管理器>:getInstance()`），以及**是否有条件分支会被跳过**。
2. ★ **在客户端 Lua 里搜 `map_block` 的赋值点**：用 `tools/scan_luac_strings*.py` 或按字符串搜
   `map_block` / `MapBlock` / `MAP_BLOCK`，找出**谁给它赋值**；
   - 若指向 `Config.MapBlock`（APK 内的配置表）⇒ 问题在**客户端配置加载**（与我们无关，但可验证：
     探针里直接读 `Config.MapBlock` 看是否为 nil）；
   - 若指向**某条协议字段/消息** ⇒ 那就是**可修的服务端缺陷**（按真值补）。
3. 探针 v54：直接打印 `Config` 里含 MapBlock 的项、以及 `SceneModel:getInstance().map_block` 的赋值时机。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `server/_ml53_add.lua` / 设备 `files/dsh_v53.txt` | ★ 本轮探针与原始证据（`map_block` nil 崩溃） |
| `report/report_20261001_v53_...`（本文件） | ★ 根因定论 + 自我更正 |
| `analysis/scene_model.luac` | 反汇编依据（`sceneStart` proto#68 指令 147-155） |
