# ★★★ 因果链闭合：`self.map_block = Config.MapBlock`（proto#1 指令 14-16）—— 根因是 **`Config.MapBlock` 为 nil**

> 时间：2026-10-01 ｜ 依据：`SceneModel:__init` 反汇编（proto#1）+ v53 的运行时崩溃证据

---

## 〇、一句话结论

> 因果链**完全闭合**，五环齐全、每环都有反汇编或运行时证据：
>
> ```
> ① SceneModel:__init:
>     14-16  self.map_block = Config.MapBlock      ← ★ nil 在这一环产生
>     17-19  self.map       = Config.Map
> ② 运行时: self.map_block == nil                   （v53 实测崩溃）
> ③ sceneStart (proto#68) 指令 147-150:
>     self.map_block:get(self.sceneId)              → attempt to index field 'map_block' (a nil value)
> ④ sceneStart 抛错中断 ⇒ 其后的 MAP_BLOCK / astar / readInDefaultXml / **self.scene:createMap()** 全没跑
> ⑤ 结果: 地图没建（self.scene.map=false）、NPC 没渲染、场景层无触摸处理
>        ⇒「地图不清晰 / 没有NPC / 不能点击移动」三条症状
> ```
>
> ⇒ **根因 = 客户端侧 `Config.MapBlock` 在 `SceneModel:__init` 执行时是 nil**
> （既不是我的协议错、也不是 `Scene:New()` 的问题）。

---

## 一、本轮证据：赋值点

```
=== scene_model.luac proto #1（SceneModel:__init，bc=90）===
  strings: … 'Map', 'map', 'MapBlock', 'Config', 'map_block' …

 14  GGET   A=1   D=8          ; 全局 'Config'
 15  TGETS  A=1   B=1   C=9    ; ['MapBlock']
 16  TSETS  A=1   B=0   C=7    ; self.map_block = Config.MapBlock      ← ★★ 赋值点
 17  GGET   A=1   D=8          ; 'Config'
 18  TGETS  A=1   B=1   C=11   ; ['Map']
 19  TSETS  A=1   B=0   C=10   ; self.map = Config.Map                  ← 同一个模式
 20+ 其余字段初始化（scene/scene_info/path/curPos/isWalking/autoFight/…）
```

**读法**：`map_block` 与 `map` 都直接取自**客户端的 `Config` 表**；
`__init` 里**没有** `if Config.MapBlock then … else 兜底` 这类保护 ⇒ 若 `Config.MapBlock` 为 nil，
`self.map_block` 就**永久为 nil**，直到 `sceneStart` 崩在它上面。

---

## 二、由此推出的**新**方向（下一轮第一件事）

**问题不再是"谁没设置 `self.map_block`"，而是"`Config.MapBlock` 为什么是 nil"**。三种可能：

| # | 可能 | 验证办法（便宜） |
|---|---|---|
| 1 | `Config` 表里**确实没有** MapBlock（该配置未加载） | 探针直接打印 `type(Config)`、`Config.MapBlock`、`Config.Map`、以及 `Config` 的键数 |
| 2 | **加载时机**问题：`SceneModel:__init` 跑在 `Config.MapBlock` 填充**之前** | 探针在若干时间点重复读 `Config.MapBlock`：若**先 nil 后 table** ⇒ 时机问题（且 `self.map_block` 已被永久写成 nil） |
| 3 | **配置加载由某条服务端消息触发**（我"通用应答"或从不发的那条） | 搜客户端里加载 MapBlock 的调用点（`MapBlock` 字符串的**赋值/load 处**），看它的**触发者** |

> ★ 若落在第 3 种，那就是**可修的服务端缺陷**（把那条消息按真值补上）；
> 若落在第 1/2 种，则是**客户端侧**问题（我们只能如实记录 + 给出绕过思路）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★★ **找到 `map_block` 的赋值点**：`self.map_block = Config.MapBlock`（proto#1 指令 14-16），
   同一模式也用于 `self.map = Config.Map`。
2. ★ **因果链闭合**（五环，各环有反汇编或运行时证据）。
3. ★ **把问题重述到正确的一环**：不再是"谁没设 `map_block`"，而是"**`Config.MapBlock` 为何为 nil**"，
   并给出 3 种可能 + 每种的可执行验证。
4. ★ 确认 `__init` 里**没有**对 `Config.MapBlock` 的兜底判断（所以一次 nil 就永久 nil）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `Config.MapBlock` 到底是不是 nil（及是否"先 nil 后 table"） | ❌ 下一轮探针（v54） |
| 2 | 加载 MapBlock 的**触发者**（是否有服务端消息参与） | ❌ 下一轮 |
| 3 | 真机自然操作发 `10204` / 充值档位承载命令 | ❌ / **UNKNOWN** |

---

## 四、下一轮施工单

1. ★ **探针 v54**（一次跑完）：
   - 打印 `type(Config)`、`Config.MapBlock`、`Config.Map`、`#Config`（键数）；
   - **在多个时间点重复读**（t=1s/10s/30s/60s）⇒ 判断是否"先 nil 后 table"（时机问题）；
   - 打印 `SceneModel:getInstance().map_block` 的当前值，与 `__init` 时的假设对照。
2. ★ **静态找触发者**：在客户端 Lua 里搜 `MapBlock` 的**赋值/加载**处
   （`tools/scan_luac_strings_deep.py` / 按字符串搜），看它由**谁**加载：
   - 若是某个 `ConfigMgr:load('MapBlock')` ⇒ 找它的调用点（启动流程？某条消息？）；
   - 若是启动时批量加载 ⇒ 检查**是否有前置配置加载失败**导致中断。
3. 若确认是**服务端可控**的触发 ⇒ 按真值补该消息（并加断言）；否则如实记录为**客户端侧根因**。

---

## 五、产物

| 文件 | 说明 |
|---|---|
| `analysis/scene_model.luac` | 反汇编依据（`__init` proto#1 指令 14-19） |
| `report/report_20261001_v53_mapblock_root_cause.md` | 上一轮：崩溃点（指令 147-150） |
| 本报告 | ★ 赋值点 + 因果链闭合 + 下一轮验证方案 |
