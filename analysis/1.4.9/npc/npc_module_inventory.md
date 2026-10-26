# NPC 模块清单（Phase 5A 审计）

> APK：`anzbao/jstm.apk` = **1.4.9** / `com.shiyue.dldl.ewan.qihoo`
> 方法：LuaJIT 字节码反汇编（`GSET` 类名 + `RegisterProtocal` 映射）+ 实机 TCP 日志
> 状态列只用：**已确认 / 已验证 / 待验证 / 未知**

---

## 一、NPC 相关文件

| 文件 | 功能 | 涉及网络 | 涉及 UI | 状态 |
|---|---|---|---|---|
| `game/npc/npc_ctrl.luac` (24.5KB) | **NpcCtrl** — NPC 交互总控（注册 15 条协议、有 sender 与点击入口） | **是** | 是 | **已确认** |
| `game/npc/npc_dialogs.luac` (23.9KB) | **NpcDialogs** — NPC 对话 UI | 否 | **是** | **已确认** |
| `game/npc/elem_dialogs.luac` (6.8KB) | 场景元素（非人形 NPC/门）对话 | 否 | 是 | **已确认** |
| `game/npc/npc_mission_manager.luac` (2.4KB) | **NPC ↔ 任务 的关联管理** | 否 | 否 | **已确认**（文件与类名） |
| `game/npc/npc_mission_vo.luac` (912B) | **MNpcVo** — NPC 任务 VO | 否 | 否 | **已确认**（类名）；字段**待验证** |
| `game/npc/npc_talk_manager.luac` (776B) | **NpcTalkManager** — 对话管理 | 否 | 否 | **已确认**（类名）；用途**待验证** |
| `game/npc/npc_contants.luac` (376B) | **NpcContants** — 常量 | 否 | 否 | **已确认**（类名）；常量值**待验证** |
| `game/npc/npc_asset_item.luac` (1.2KB) | **NpcAssetItem** — NPC 资源项 | 否 | 是 | **已确认**（类名） |
| `game/npc/view/map_exchange_view.luac` (6KB) | 地图兑换界面 | 是 | 是 | 已确认（属 NPC 目录） |
| `game/scene/element/npc.luac` (4.1KB) | **Npc** — 场景里的 NPC 实体（渲染/点击体） | 否 | 是 | **已确认** |
| `game/scene/element/npc_vo.luac` (1.5KB) | **NpcVo** — 场景 NPC 数据对象 | 否 | 否 | **已确认** |

---

## 二、`NpcCtrl` 注册的协议（15 条）

反汇编 `npc_ctrl.luac` 的 `RegisterProtocal` 调用，得到：

```
10232 -> sendBtnHandler
15200 -> handle15200        15400 -> handle15400
15203 -> handle15203        15401 -> handle15401
15204 -> handle15204        15300 -> handle15300
15206 -> handle15206        17000 -> handle17000
15207 -> handle15207        17001 -> handle17001
15208 -> handle15208        18200 -> handle18200
                            18201 -> handle18201
12744 -> handle12744
```

## 三、`NpcCtrl` 的交互相关方法（`TSETS` 名）

```
clickNpcOpenDialog        ← ★ NPC 点击入口
sceneClickEvt             ← 场景点击事件
getOpenNpc / setOpenNpc   ← 当前打开的 NPC
open / openElemDialogs / elemDialog
openFavourPanel
sendBtn / sendBtnHandler / sender17000 / sender17001 / sender18200 / sender18201
add_mission_event / delete_mission_event    ← ★ NPC ↔ 任务 的关联
checkIsOpen
```

---

## 四、NPC 显示链路（前序阶段已验证，此处归档）

| 环节 | 证据 | 状态 |
|---|---|---|
| 服务端下发 NPC | `SC_10201`（`SCMapGird`）的 `npcs` 表，map 10001 = **25 条**（实测） | **已验证** |
| 客户端接收 | `scene_controller proto[9] on10201` → `SceneModel.addNpc` | 已确认 |
| NPC 名字 | 服务端 `name=""` 时客户端从 `config_npc.luac` 取真名（实测显示「萧萧」「牧师」「周漪」「唐舞桐」「霍雨浩」） | **已验证** |
| NPC 配置来源 | `config_map_npc.luac`（`Config.MapNpc` / `Config.MapSceneDoors`）；map 10001 MapNpc=25、MapSceneDoors=0 | **已验证** |

---

## 五、交互协议（本轮新发现）

**`clickNpcOpenDialog` 的实现**（`npc_ctrl proto[17]`，仅 5 条字节码）：

```lua
function NpcCtrl:clickNpcOpenDialog(npc)
  local proto = ProtocalRulesMgr:getInstance():GetPrototype(15203)
  self:SendProtocal(proto)
end
```

**⇒ NPC 点击的请求协议 = `CS_15203`**（**已确认**：客户端代码证据）。

字段定义（`tools/show_cmd.py 15203`，来自 1.4.9）：

```
CS_15203 — 无字段（空消息）
SC_15203 — code:uint8, msg:string
```

**⇒ `CS_15203` 不带 NPC id。** 也就是说：**NPC 的身份不上报**，
服务端只能靠"客户端当前所在场景 + 上下文"或其它协议判断（**待验证**）。

---

## 六、★★★ 决定性结论（本轮补齐，5A 最后两项达成）

**用探针包住 `NpcCtrl.clickNpcOpenDialog` 后实机点击 NPC，结果：该函数**一次都没有被调用**。**

```
钩子安装:  setOpenNpc_wrapped / clickNpcOpenDialog_wrapped /
           open_wrapped / openElemDialogs_wrapped        ← 都装上了
           sceneClickEvt_NOT_function_table              ← 它是"表"不是函数
点击结果:  npcH 命中 0 条
服务器收到: 全是 CS_10204（移动）：00 64 00 2c → 00 63 00 2a → … → 00 46 00 35
```

**⇒ 点击 NPC 时，请求**没进入 NPC 处理链** ——
点击被**地图层**拦截、解释为"移动到该点"，所以 `CS_15203` 从未发出。**

**⇒ 因此 5A 的两项未达成项有了明确答案：**

| 5A 要求 | 结论 |
|---|---|
| 抓到 NPC 点击实际协议 | ❌ **未抓到**，且**已查明原因**（点击根本没进 NPC 链） |
| 确认服务器收到协议 | ⚠️ 服务器收到的是 `CS_10204`（移动），**不是** NPC 交互协议 |

**⇒ 这不是"服务端缺协议"，而是"客户端没发"。Phase 5B 首要任务 = 让点击能命中 NPC。**

---

## 七、关键未解项
