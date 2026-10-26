# NPC 数据来源（Phase 5A 审计）

> 问题：「地图中的 NPC 为什么能够显示？数据来自 APK 本地配置、服务器协议，还是两者结合？」
> 结论：**C —— 本地配置 + 服务器动态数据**（**已验证**）

---

## 一、结论（先给答案）

| 层 | 来源 | 内容 | 状态 |
|---|---|---|---|
| **"本图有哪些 NPC、各在哪"** | **服务器** | `SC_10201`（`SCMapGird`）的 `npcs` 表 | **已验证** |
| **"这个 NPC 叫什么、长什么样、有什么功能"** | **APK 本地配置** | `config_npc.luac`（按 npc bid 查） | **已验证** |
| **地图级的 NPC 布置/门** | **APK 本地配置** | `config_map_npc.luac`（`Config.MapNpc` / `Config.MapSceneDoors`） | **已验证** |

**⇒ 服务端决定"有哪些 NPC 在场上"，客户端配置决定"这个 NPC 是什么"。**

---

## 二、证据链

### 2.1 服务端下发（`10201`）—— 本轮与前序实测

```
<< 10201 SCMapGird (server push) roles=1 (587 bytes)
```

`SC_10201` 的 `npcs` 表元素字段（来自 `protocol/manual.md`）：包含 npc 的
`bid` / `x` / `y` / `dir` / `name` / `status` 等。

**实测**：map 10001 我们下发 **25 条** NPC，客户端全部显示（历史截图）。

### 2.2 名字的解析 —— 一个关键实测

我们下发的 NPC 条目里 **`name` 留空**，客户端却显示出了**真实中文名**
（「萧萧」「牧师」「周漪」「唐舞桐」「霍雨浩」…）。

**⇒ 证明客户端在 `name` 为空时会去 `config_npc.luac` 按 `bid` 取真名。**
（这条**已验证**，前序阶段记录在 `analysis/1.4.9/scene/npc_final.md`）

### 2.3 本地配置

`assets/src/config/config_map_npc.luac` 的结构（反汇编确认）：

```
@5-193   Config.MapNpc          （按地图 id → NPC 列表）
@194-568 Config.MapSceneDoors   （按地图 id → 门列表）
```

**实测**：map 10001 → `MapNpc = 25` 条、`MapSceneDoors = 0` 条。

`assets/src/config/config_npc.luac`：NPC 定义（名字、模型、功能等）。

---

## 三、字段级确认情况

任务书要求确认下列字段。本节**只写有证据的**：

| 字段 | 来源 | 客户端使用位置 | 状态 |
|---|---|---|---|
| npc `bid` | 服务器 `10201` | `SceneModel.addNpc` → `scene/element/npc_vo.luac` | **已确认**（实机 addNpc 入参逐字段核对过） |
| `x` / `y` | 服务器 `10201` | 同上（**瓦片坐标**，客户端 ×30 得世界像素） | **已验证** |
| `dir` | 服务器 `10201` | 同上 | 已确认（字段存在于协议） |
| `name` | 服务器为空 → 回退本地 `config_npc` | 名字标签 | **已验证**（显示真实中文名） |
| `npc_name` | 本地 `config_npc.luac` | 名字标签 | **已确认**（配置存在） |
| `npc_model` / `npc_res` | 本地 `config_npc.luac`（推断） | 模型/资源加载 | **待验证**（未逐字段核对） |
| `npc_type` | — | — | **未知** |
| `npc_dialog` / `npc_function` | 疑似本地 `config_npc.luac` | `NpcCtrl.clickNpcOpenDialog` / `NpcDialogs` | **待验证** |

> ⚠ 上表里标 `待验证`/`未知` 的，**没有被写成"已确认"**。
> 尤其是 `npc_dialog`/`npc_function`：**这是"点击后能否弹出对话"的关键**，
> 但本轮**尚未**逐字段核对 `config_npc.luac` 的字段名与含义。

---

## 四、与本轮"点不出交互"的关联（**推测，未确认**）

实机点击 NPC 没有触发 `CS_15203`。可能与本节的"本地配置层"有关：

- 若我们下发的 NPC `bid` 在 `config_npc.luac` 里**没有对应的功能定义**，
  客户端可能就不会给它挂"可点击/可对话"的处理；
- 但我们**观察到名字能正确显示**，说明 `bid` 是有效的（至少能查到名字）——
  因此"bid 无效"这一条**与现象矛盾**，优先级下调。

**⇒ 该推断未确认，留作 Phase 5B 的排查项。**

---

## 五、下一步（Phase 5B 用）

1. 逐字段读出 `config_npc.luac` 的 NPC 定义（字段名 + 类型 + 含义）；
2. 核对 map 10001 那 25 个 NPC 的 bid 在 `config_npc.luac` 里是否都有**可交互功能**；
3. 用探针包住 `NpcCtrl.clickNpcOpenDialog`，确认**点击到底有没有调用它**
   （这能一步区分"点击没命中"与"命中但没发送"）。
