# 1.4.9 地图加载门禁 —— 取证记录（已定位并修复）

> 目标：找出"进入地图后角色不能移动"的真实卡点。
> 方法：**先取证再改**。全部结论附运行时读数或反汇编出处；被否证的假设也保留。
> **状态：卡点已定位，修法已验证生效（纯服务端改动）。**

---

## 〇、结论：修法已生效（实测）

**改动**：服务端在收到客户端 `10300`（客户端初始化完毕）之后，**再补推一次 `10200`**。

```python
if cmd == 10300:
    log('tcp.log', '  .. 10300 CSRoleInit received')
    if self.cfg.get('repush_10200_on_init', True):
        self._send_10200(self.cfg.get('spawn', {}).get('bid', 1))
        log('tcp.log', '  << 10200 re-push after 10300 (client ready)')
```

**实测对比（所有诊断手段全部关闭：forceLoad / directCM / probeMove 均未启用）**：

| 读数 | 修前 | **修后** |
|---|---|---|
| `mapResCache` | **0** | **192**（正好 = `assets/res/scene/10001/` 的 192 个文件） |
| `nowPicTile` | `nil` | **table** |
| `SceneController.model:isLoadState()` | **false** | **true** ✅ |

修后只读测量原文：

```
t_3690_isLoadState_true_mapResCache_192
t_3720_isLoadState_true_mapResCache_192
t_3750_isLoadState_true_mapResCache_192
```

⇒ **`isLoadState` 自然为真，不再需要任何干预。**

---

## 一、根因

```
scene_controller.move (proto[37])
  └─ if not self.model:isLoadState() then return end     ← 移动被挡在这
       ├─ 初值 false ：scene_view proto[1]  @95-99   setLoadState__(false)
       └─ 置真 true  ：scene_view proto[37] @18-22   setLoadState__(true)
             └─ 它是 createMap(proto[38]) @25 处 FNEW 出来的**闭包回调**
                   └─ 调用者：scene_model proto[68] sceneStart @109-112  self.scene:createMap()
```

**关键机制**：`sceneStart` 每次收到 `10200` 都会走一遍并调用 `scene:createMap()`。
客户端**第一次**被 `10200` 触发时（刚进场景、资源尚未就绪），`createMap` **半途而废**：
`nowPicTile` 没设、闭包回调没触发 ⇒ `isLoadState` 停在 false；
而 `sceneStart` 之后**不会自动重试**，于是卡死。

**修法**：既然 `sceneStart` 会重新调用 `createMap`，那就让服务端在客户端**明确表示
自己已初始化完毕（`10300`）之后**再补推一次 `10200` —— 此时资源已就绪，
`createMap` 一次跑通。

**这是纯服务端改动**：不改客户端、不改 APK 业务逻辑、不改协议。

---

## 二、决定性取证过程（含我推翻自己的部分）

### 2.1 早期结论"包装无效 / 方法从未调用"是**错的**

第一次包装 `SceneView` 方法时 `svCall` 一条都没有。我当时判断"从未调用"，
但随后自查发现这是**采集时机**问题：包装放在 `step()` 里，而 `step` 挂在
`GameNet.doOneMsg` 上，必须等 `sys/gamenet` 加载完（约 35 秒）才装得上，
而场景构建发生得更早。

### 2.2 修正采集时机后的真相

改用 `_G` 的 `__newindex` **拦截 `SceneView` 的创建**（它在 `scene_view.luac`
里以 `GSET SceneView` 出现），在它刚被赋值的一瞬间包装方法：

```
t=svHook&v=newindex_armed_tick_0                 ← 拦截生效（tick 0，最早的时机）
t=svEq&v=inst_eq_class_true_inst_owns_false      ← 实例方法确实走类表 ⇒ 包装有效
svCall 条数: 409                                  ← 方法一直在被调用
  createMap_n_1_args_0                           ← ★ createMap 只被调用过 1 次
  renderScene_n_4 / clearLayer_n_2 / layoutScene_n_3 / getScenePicByPos_n_9 / getPicRes_n_12…
```

### 2.3 直接调一次 createMap（诊断，非修复）

```
t=directCM&v=ok_true_err_nil_svN_before_0_svN_after_390
            _nowPicTile_table:_0xb1f7ee78_isLoadState_true
```

**手动调一次 `createMap()`：`nowPicTile` 被设置、`isLoadState` 变 true、无报错。**
⇒ 证明"再跑一次就好"，从而导出上面的服务端修法。
（该诊断随后已关闭，最终验证是在**全诊断关闭**下取得的。）

---

## 三、被否证的假设（保留记录）

| 假设 | 结论 |
|---|---|
| `scene_info.mons` 为 nil 导致 `pairs(nil)` 抛错 | **否证**：实测 `mons=table` |
| `10201` 的 `roles` 元素编码错（那 6 个未解出的 `D|Dsc*|` 子表） | **否证**：加开关 `send_roles_in_10201=false` 重跑，`scene_info.roles` 仍为 nil、其余无变化 |
| `bid` 非法 | **否证**：`bid=10001` 合法，`assets/res/scene/10001/` 有 192 个文件 |
| 客户端向我们下载地图资源失败 | **否证**：HTTP 日志无任何 `/cdn/`、`/res/`、`.plist`、`.png` 请求 |
| Lua 抛错中止 | **否证**：logcat 里 0 条 `stack traceback` |

---

## 四、仍然未完成的一项（如实说明）

**`isLoadState` 已为 true，但用 ADB 模拟点击/拖拽仍未能让客户端发出 `CS_10204`。**

- 探针里的 `move()` 调用已**禁用**，所以这段时间 tcp.log 里只有心跳（`1199 x5`），
  任何 `10204` 都只可能来自真实输入 —— 而一条都没有。
- 已排除"门禁挡住"：门禁现在是开的（`isLoadState=true`）。
- 因此问题在**输入落点**：我无法确定摇杆/可行走地图区的屏幕坐标。

### 已有的线索（下一步的取证方向）

客户端有独立摇杆模块 `game/main/joystick.luac`（类 `Joystick`），
`main_ctrl` 里有 `showJoystick` / `JoystickMove`，且 `scene_model` 有 **`isJoystick`** 标志、
事件 `SHOW_JOYSTICK` / `JOYSTICK_MOVE`。

**下一步应先测量**：`SceneModel:getInstance().isJoystick` 的取值、
摇杆节点在场景中的位置与可见性 —— 再据此给输入坐标。
仍按"先取证再改"，不盲试。

（本机没有视觉 CLI（`grok` 未安装），我无法直接看截图确认摇杆位置；
如能从画面确认，这一步会快很多。）


---

## 一、结论摘要

| 项 | 状态 |
|---|---|
| 移动协议 / 服务端 / 落盘 / 重登恢复 | ✅ 已实测通过（见 `movement_test.md`） |
| 客户端自然操作下不能移动 | ❌ 由 `scene_controller.model:isLoadState() == false` 导致 |
| `isLoadState` 由谁置真 | `scene_view` proto[37]，作为 `createMap` 内部的**闭包回调** |
| `createMap` 是否跑完 | ❌ **没有**：它应在 @46 设置 `nowPicTile`，实测 `nowPicTile = nil` |
| 为什么跑不完 | **未确认**（见第五节，含已否证的假设） |

---

## 二、门禁链（全部有出处）

```
scene_controller.move (proto[37])
  └─ if not self.model:isLoadState() then return end        ← 移动被挡在这里
        └─ isLoadState 初值：scene_view proto[1] @95-99  setLoadState__(false)
        └─ 置真唯一处：scene_view proto[37] @18-22        setLoadState__(true)
              └─ proto[37] 是 createMap(proto[38]) @25 处 FNEW 出来的闭包
                    └─ 调用者：scene_model proto[68] sceneStart @109-112
                         self.scene:createMap()
```

### 运行时读数（探针上报）

```
t=view  reslist=0  loading=false  loadingNum=nil  quequeAddFun=function  via=SceneModel.scene
t=sceneData  scene_data=table  sceneId=10001  mapResCache=0  order=0  nowPicTile=nil
t=sceneInfo  scene_info=table  roles=nil  npcs=table  mons=table  elems=table  bid=number
t=gates  isOnTeamFollow=nil  isLoadState=false
```

要点：

1. **视图对象存在**（`SceneModel:getInstance().scene`） ⇒ `SceneView.New()` 确实执行过
   （`scene_model proto[68]` @4-10：`if self.scene == nil then self.scene = SceneView.New() end`）。
2. **`scene_data` 是 table、`sceneId=10001`** ⇒ 场景数据在。
3. **`mapResCache = 0`**（其填充函数是 `getPicRes` proto[67]，按需填充 ⇒ 首帧为空属正常）。
4. **`nowPicTile = nil`** ⇒ `createMap` 没走到 @46（那里才 `TSETS nowPicTile`）。
5. **无 Lua 错误**（logcat 里 `stack traceback` / `.luac:\d+:` 均为 0） ⇒ 不是抛错中止，
   而是**根本没执行到**。

---

## 三、`createMap` 的关键语句（proto[38]，params=1）

```
 0-2   self.scene_info = self.model.scene_info
 3-4   self.loading_pic = nil
 5-9   self:clearLayer(self.scene_info, ...)
10-13  self:layoutScene(...)
14-16  for k,v in pairs(self.scene_info.mons) do ... end     ← 曾怀疑此处 pairs(nil)
22-24  self:renderScene()
25     cb = <proto[37]>                                       ← 置 LoadState 的回调
28-40  self:getScenePicByPos(self.model.scene_data, s_img_w, s_img_h,
                             TileUtil.changeXToPixs(scene_data.x),
                             TileUtil.changeYToPixs(scene_data.y))
41-46  self.nowPicTile = cc.p(...)
47-69  遍历 mapResCache 按距 nowPicTile 排序 → table.insert(mapResCacheOrder, ...)
...    后续再排队→createFloorSpriteAct→addMapTile，最终触发 cb
```

---

## 四、已**否证**的假设（保留记录，避免重走）

### 假设 A：`scene_info.mons` 为 nil 导致 `pairs(nil)` 抛错

- 静态上确实像（@14-16 对 `scene_info.mons` 做 `pairs`）。
- **实测否证**：`sceneInfo` 上报显示 `mons = table` ⇒ 不会抛错。

### 假设 B：`10201` 的 `roles` 元素编码错（那 6 个未解出的 `D|Dsc*|` 子表）导致解析失败

- 诱因：实测 `scene_info` 里 `roles = nil`，而 `npcs/mons/elems` 都是 `table`。
- **一次一变量对照实验**：加开关 `send_roles_in_10201=false`（`10201` 回 0 条 roles），重跑。
- **结果：无变化** —— `scene_info.roles` 仍是 `nil`，`nowPicTile` 仍 `nil`，`mapResCache` 仍 0。
- ⇒ **`scene_info.roles` 并非来自 `10201` 的 roles 表**，该假设不成立。（开关已还原为 `true`。）

### 已排除的其它候选

| 候选 | 排除依据 |
|---|---|
| 点错屏幕坐标 | 已绕过触屏，直接调客户端 `move()` |
| `bid` 非法 | **`bid=10001` 合法**：`assets/res/scene/10001/` 存在，192 个文件 |
| 客户端向我们下载地图资源失败 | HTTP 日志**没有**任何 `/cdn/`、`/res/`、`.plist`、`.png` 请求 |
| Lua 抛错中止 | logcat 里 0 条 `stack traceback` |

---

## 五、尚未确认（下一步要什么证据）

### 5.1 做过的实验：包装 `SceneView` 的六个方法计数

在 `SceneView` 类表上包装 `createMap / layoutScene / renderScene /
getScenePicByPos / clearLayer / getPicRes`，每次调用上报。

**结果**：`svHook=installed` 有上报，但 **`svCall` 一条都没有**。

**但这个结果不可作为证据**，原因是**采集时机**：

- 探针的钩子是在驱动里装的，而驱动挂在 `GameNet.doOneMsg` 上 ⇒
  **必须等 `sys/gamenet` 加载完（约 35 秒）才可能装上钩子**；
- 而场景构建（`sceneStart` → `createMap`）发生在**角色重连之后不久**，
  很可能**早于**钩子安装完成；
- 于是"没看到调用"更可能是"调用发生在我装钩子之前"，而不是"从未调用"。

**必须修正后再测**：把这段包装移到**更早**的时机 ——
例如挂在 `registerProtocals` 之后、或者用"引导钩子"
（`cc.Director.replaceScene` 那套，之前用它成功引导过 `doOneMsg`）。
在那之前，本节结论**不成立**。

### 5.2 仍然待查的三个候选

由于没有抛错，候选是：

1. `sceneStart` 在调用 `createMap`（@109-112）**之前**还有别的门禁
   （@113-124 已在用 `RoleCtrl:getInstance():getRoleVo().career` 之类做判断），
   可能 `createMap` 之前的某步没满足。
2. `createMap` 内部的 `layoutScene`（@10-13）或 `clearLayer`（@5-9）里提前 return。
3. `scene_data` 虽是 table，但缺 `x`/`y`（`getScenePicByPos` 需要），
   导致行为异常但未抛错。

### 5.3 建议取证顺序（仍按"先取证再改"）

1. **先把包装时机提前**到 `registerProtocals` 完成后（见 5.1），
   再确认 `createMap` 到底有没有进去、走到哪一步停。
2. 上报 `model.scene_data.x` / `.y` 的**取值**（现在只知道类型是 table）。
3. 检查 `sceneStart` @113-124 那段对 `RoleCtrl:getRoleVo()` 的判断是否走了 else。

---

## 六、诚实结论

- **移动协议链路是通的**（四方向 + 落盘 + 重登恢复 + 重启恢复，全部实测）。
- **卡点不在协议、不在服务端数据**，而在**客户端自身的地图构建流程没有跑完**。
- 我**没有**修好它，也**没有**用 `setLoadState__(true)` 这种诊断手段冒充修复。
- 阶段 3 的"角色可以移动（玩家自然操作）"这一条**仍未达成**。
