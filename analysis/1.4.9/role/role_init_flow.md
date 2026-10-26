# 角色初始化流程（role init flow）—— 1.4.9

> 指"从角色登录成功 → 客户端拿到完整角色状态 → 可以正常进场景并被渲染"这一段。
> 依据：`scene_controller.luac` / `scene_model.luac` / `role_ctrl.luac` 反汇编 + 实机日志。

---

## 一、客户端侧的实际初始化链（逐环节已实测）

```
10102/10103 应答
   └─ denglu_ctrl.on10102Login / on10103ReLogin
        ├─ GameNet:setTime()
        ├─ cacheNearLoginData / setWorldLev
        ├─ SendProtocal(10300)                      ← 客户端说"我初始化完了"
        └─ GlobalEvent:Fire(RE_LINK_GAME)

10300 到达服务端
   └─ 服务端补推 10200（关键：让客户端在资源就绪后**重跑** sceneStart→createMap）

10200 到达客户端
   └─ scene_model proto[68] sceneStart
        ├─ setSceneInfo(sceneId)
        ├─ if self.scene == nil then self.scene = SceneView.New() end
        ├─ SceneController:changeSceneLayer(view.root, scene_info)
        └─ self.scene:createMap()      ← 第一次常常跑不完（资源未就绪）

10201 到达客户端
   └─ scene_controller proto[9] on10201
        ├─ npcs  → SceneModel.addNpc
        ├─ elems → addElement
        ├─ mons  → addMonster
        ├─ roles → 逐条 managerMiscKV_ + SceneModel.addRole
        └─ 之后 initRecList()

10301 到达客户端
   └─ role_ctrl proto[31..] rgp_hander10301 → 建/更新 RoleVo（含 skill_list）

10302 到达客户端
   └─ rgp_hander10302 → 资产/经验（lev/exp/gold/gold_acc）
```

## 二、两个必须知道的"坑"（都已实测确认）

### 坑 1：`createMap` 需要被"重跑"一次

- `scene_view proto[1]` 初始化时 `setLoadState__(false)`；
- 置真只在 `scene_view proto[37]`，而它是 `createMap` 内部的**闭包回调**；
- 客户端第一次被 `10200` 触发时资源未就绪，`createMap` 半途而废 ⇒
  `nowPicTile` 不设置、回调不触发 ⇒ `isLoadState` 停在 false ⇒
  `scene_controller.move` 的门禁 `if not model:isLoadState() then return end` 直接挡掉移动。
- **解法（服务端侧）**：收到 `10300` 后再推一次 `10200`。实测修好后
  `mapResCache 0→192`、`nowPicTile=table`、`isLoadState=true`。

### 坑 2：坐标必须是"地图内的瓦片坐标"

- 客户端把 `x,y` 当**瓦片坐标**，乘瓦片像素尺寸（实测 30）得世界像素显示；
- 早期 `spawn=(1320,2036)` 远超地图范围 ⇒ 相机停在地图外 ⇒
  **地图模糊 + 看不到角色**。
- **解法**：用地图内合法坐标（如 `(30,30)`）。实测修好后角色可见、会自动移动。

## 三、服务端在初始化阶段要下发的东西（Phase 4C 现状）

| 时机 | 下发 | 现状 |
|---|---|---|
| 收到 `1110` | `SCAccountLogin`（`code` 必须 1） | ✅ |
| 收到 `10102`/`10103` | `SCRoleLogin`/`SCRoleReLogin`（`code=0`） | ✅ |
| 收到 `10300` | **补推 `10200`** + 推 `12400` | ✅ |
| 收到 `10201` | `SCMapGird`：roles（自己）+ npcs（25 条）+ mons/elems | ✅ |
| 收到 `10301` | `SC_10301`（`role_state()`，含 `skill_list`） | ✅ |
| 收到 `10302` | `SC_10302`（`lev/exp/gold/gold_acc`） | ✅ |
| 收到 `10621` | `SC_10621`（`world_lev` + `skill_list`） | ✅ |
| 收到 `10333` | `SC_10333`（`code=0`） | ✅ |
| 收到 `13340` | `SC_13340`（个人信息/名片） | ✅ |

## 四、尚未完成（供 4D 及以后）

1. **主界面不显示等级/经验/HP/MP/战力** ⇒ 待 4D 打开角色面板确认；
   若面板也需要，则要补 `SC_10303` 的 `attr` 大表。
2. 金币显示数值与下发对不上（原因未确认，不猜改）。
3. 角色档案仍是**静态配置**（`config.json`），不是真正的持久化（4E）。
