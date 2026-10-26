# 1.4.9 角色不显示 / 地图模糊 / 无 NPC —— 取证记录

> 用户报告四个现象：①地图模糊 ②地图上没有角色 ③任务为空 ④没有 NPC
> 方法：**先取证再改**。本文件全部结论来自运行时读数，不猜。

---

## 一、结论先行：①② 不是协议问题，③④ 是"我们本来就没做"

| 现象 | 定性 | 证据 |
|---|---|---|
| ② 地图上没有角色 | **协议侧完全正确**，问题在客户端渲染/外观资源 | `addRole` 收到的数据逐字段正确（见第三节） |
| ① 地图模糊 | 地图瓦片已全部加载（192），但渲染为低细节 | `mapResCache=192`、`nowPicTile=table` |
| ③ 任务为空 | **服务端未实现任务系统**，没有任何任务数据下发 | 我们从未发过任务相关消息 |
| ④ 没有 NPC | **服务端 10201 的 npcs/mons/elems 全是空表** | `on10201&v=roles_1_npcs_0_mons_0_elems_0` |

**③④ 是"功能未实现"，不是 bug** —— 属于本阶段明确禁止提前做的范围（任务/NPC 系统）。
**①② 才是需要继续查的技术问题**，且已证明卡点不在协议。

---

## 二、关键测量：客户端解析后的 10201 四表

包住 `SceneController.on10201`（proto[9]）直接读它收到的 `resp`：

```
t=on10201&v=roles_1_npcs_0_mons_0_elems_0
```

⇒ **客户端把我们的 `roles` 正确解析成 1 条**。
（此前我怀疑"roles 里那 6 个 `D|Dsc*|` 动态子表编码猜错导致解析失败"——
**该怀疑被此测量否证**：能解析出 1 条，说明整条角色的字节布局是对的。）

---

## 三、关键测量：`addRole` 拿到的数据

`on10201` 里调用的是 **`self.model:addRole(...)`**（方法在 `SceneModel` 上，不在 `SceneController` 上；
我第一次挂错对象，所以看到"addRole 一次都没调用"的假象 —— 已更正）。

包住 `SceneModel.addRole` 并打印入参：

```
smCall&v=addRole_n_2_a_1_rid_1001_x_1320_y_2036_dir_0_career_1_sex_0_lev_1_name_DSH_srv_1
smCall&v=addRole_n_5_a_1_rid_1001_x_1320_y_2036_dir_0_career_1_sex_0_lev_1_name_DSH_srv_1
smCall&v=syncRoles_n_6_a_1
smCall&v=setLoadState___n_1_a_1
```

**逐字段比对：`rid=1001 ✓ x=1320 ✓ y=2036 ✓ dir=0 career=1 ✓ sex=0 lev=1 ✓ name=DSH ✓ srv_id=1 ✓`**

⇒ **客户端拿到并接受了完整的正确角色数据**，且
`addRole` / `syncRoles` / `setLoadState__` 都被调用、`isLoadState` 已为 `true`
（上一轮验证：`t_3690_isLoadState_true_mapResCache_192`）。

**所以"地图上没有角色"不是数据没到、也不是被门禁挡住，而是角色对象建立之后的
"外观/精灵"这一步没成。**

---

## 四、`on10201` 的处理逻辑（反汇编，proto[9]，212 条字节码）

从它的字符串可以读出去向：

```
roles  → addRole        npcs  → addNpc
mons   → addMonster     elems → addElement
misc_uint32 / misc_uint16 / misc_uint8 / misc_str → managerMiscKV_
is_alpha / race_camp / mount_camp / capacity / isXiuLuoEffect / isXiuLuoScene
top_effect / flyUp_lev / j_title / jlev / j_srv_id / jid / sign / position
gname / gsrv_id / gid / isFollow / isLeader / teamPos / teamId
```

**注意 `misc_*` → `managerMiscKV_`**：这四个子表在我的编码里是"计数 0 + 0 项"的空表。
`managerMiscKV_` 很可能就是**外观/装备/称号等附加显示数据**的入口 ——
空表意味着角色没有任何外观 KV。

---

## 五、决定性追加测量：角色在场景模型里**已经完整建立**

```
t_30_roleList_0_main_role_nil_mainRoleVo_false_getRole1001_false
...
t_4170_roleList_1_main_role_table_mainRoleVo_true_getRole1001_false
```

| 读数 | 进场景前 | 进场景后 |
|---|---|---|
| `SceneModel.roleList` 条数 | 0 | **1** ✅ |
| `SceneModel.main_role` | nil | **table** ✅ |
| `getMainRoleVo()` 非空 | false | **true** ✅ |

并且 `SceneModel.addRole = proto[39]`，其字符串只有 `['addRole','RoleVo','roleList']`
—— 它**只创建 RoleVo 并塞进 roleList，不创建可视元素**。

⇒ **整条数据链 100% 打通**：
`10201 → on10201 解析(roles=1) → managerMiscKV_ → addRole(RoleVo) → roleList=1 → main_role 设置`。
**服务端该给的角色数据一个都不缺。**

---

## 六、那"不显示"卡在哪：强烈指向**模拟器图形环境**（非服务端）

logcat 证据：

```
libEGL  : loaded /system/lib/egl/libGLESv1_CM_emulation.so
libEGL  : loaded /system/lib/egl/libGLESv2_emulation.so      ← ★ 用的是"模拟"GLES
libEGL  : loaded /system/lib/egl/libEGL_emulation.so
cocos2d-x debug info: gl.max_texture_units: 32
cocos2d-x debug info: gl.max_texture_size: 16384
```

而宿主 GPU 是：

```
GLES: Qualcomm, Adreno (TM) 740, OpenGL ES 3.1 V132
```

同时客户端**角色是用 Spine 骨骼动画渲染**的，日志可见它加载了：

```
CCFileUtils-android.cpp: relative path = src/common/spine_renderer.luac
CCFileUtils-android.cpp: relative path = src/common/spine_manager.luac
CCFileUtils-android.cpp: relative path = src/cocos/spine/SpineConstants.luac
```

而本机 APK 是 **armeabi，经 houdini 做 ARM 翻译** 运行在 x86_64 模拟器上。

**推论（标明是推论，未验证）**：
地图由**简单瓦片精灵**拼成 —— 能画出来，但在模拟 GLES / 缩放层级下会显得**模糊**；
角色由 **Spine 骨骼**渲染 —— 在"模拟 GLES + ARM 翻译"这层上**很可能画不出来或被画到错误位置**。
这能同时解释「地图模糊」与「看不到角色」两个现象，而这两者与我们的服务端数据无关
（数据已被上面第四节、第五节证明是完整的）。

### 如何验证这个推论（下一步，仍先取证再改）

1. **换渲染后端再试**：MuMu 的「极速模式 / 兼容模式」切换，或换一个模拟器（如雷电/LDPlayer 的不同渲染器），
   或在**真机**上跑同一个 APK + 同一个服务端。若角色出现 ⇒ 证实是环境问题。
2. **在客户端侧测角色元素是否创建**：包住 `game/scene/element/player.luac` 的创建流程，
   看是否为 `main_role` 生成了 player 元素、拿到什么 res id。
   若元素创建了却看不到 ⇒ 渲染/资源问题；若元素压根没创建 ⇒ 客户端逻辑问题。
3. 抓一次 GL 层错误（`adb logcat | findstr /i "glError GL_INVALID Cocos2dxRenderer"`），
   目前日志里**未见**显式 GL 错误（也是"静默失败"更符合模拟层的表现）。

---

## 六之补、继续取证：角色元素的创建入口 `createPlayer` 已被调用

定位到 **`scene_view proto[73] = createPlayer`**（134 条字节码），字符串显示：

```
getMainRoleVo / getRoleSrid / isHideRole / isMountSuitScene / getHero
res_id / spine_type / ROLE / ObjResType / role_layer
New / Player / setVo / setParentWnd / playActionOnce / DefaultStand / PlayerAction
registEvent('SCENE_ADDROLE') / GlobalEvent:Fire(SceneEvent.SCENE_ADDROLE)
```

⇒ 角色可视元素由 `createPlayer` 创建，且**用 Spine**（`spine_type`）+ `res_id`。

**实测（包住 `SceneView.createPlayer`）**：

```
t=svCall&v=createPlayer_n_391_args_2
```

⇒ **`createPlayer` 确实被调用了**（2 个参数）。

**未能测到的一半（如实说明）**：我同时用 `_G.__newindex` 拦截全局 `Player` 来统计 `Player.New`，
但**没有任何 `playerHook` 上报** ⇒ 说明这次拦截**没有生效**
（很可能 `Player` 在拦截装好之前就已经存在于 `_G` 上）。
因此"`Player.New` 有没有被调用"**目前无数据，不能下结论**。

### 当前已测通的完整链条

```
10201 到达
 ├─ on10201 解析            → roles=1                        ✅ 实测
 ├─ managerMiscKV_ ×4        （空表）                        ✅
 ├─ SceneModel.addRole       → 入参 rid/x/y/dir/career/sex/lev/name/srv_id 全对 ✅ 实测
 ├─ roleList = 1, main_role = table, getMainRoleVo() 非空     ✅ 实测
 ├─ setLoadState__           → isLoadState = true            ✅ 实测
 ├─ createMap / createPlayer → 均被调用                       ✅ 实测
 └─ 屏幕上仍然看不到角色                                       ❌ 现象
```

**数据与对象创建这条链上没有发现任何缺失或错误。**

---

## 六之补二、决定性：角色可视元素 `Player.New` **确实被创建**

把 `Player` 包装改为"函数 + `__newindex` 与轮询双路径安装"后（上一轮只在
`__newindex` 装、没装上也无从得知），实测：

```
t=playerHook&v=keys_New___delete___init_super
t=playerHook&v=New_wrapped
t=svCall&v=createPlayer_n_391_args_2        ← createPlayer 被调用（2 参数）
t=playerNew&v=n_1_a_1                        ← ★ Player.New 被调用 1 次
```

⇒ **角色可视元素对象已经创建出来了。**

### 至此，整条链每一步都有实测证据

```
10201 到达
 ├─ on10201 解析            → roles = 1                              ✅
 ├─ SceneModel.addRole       → rid/x/y/dir/career/sex/lev/name/srv_id 全对 ✅
 ├─ roleList = 1, main_role = table, getMainRoleVo() 非空             ✅
 ├─ setLoadState__           → isLoadState = true                    ✅
 ├─ createMap                → mapResCache = 192, nowPicTile = table  ✅
 ├─ createPlayer             → 被调用                                 ✅
 └─ Player.New               → 被调用（元素对象已创建）                ✅
────────────────────────────────────────────────────────────────────
   屏幕上仍然看不到角色                                                ❌
```

**数据、对象、可视元素创建 —— 没有任何一步缺失或报错。**
问题只可能出在**"创建出来之后画不出来"**：资源解析、摆放位置、或图形环境。

---

## 六之补三、下一个最可疑点：外观 Spine 资源解析

`createPlayer`（proto[73]）的字符串里出现：

```
getHero / hero / weapon_spine / res_id / spine_type
isMountSuitScene / DefaultStand / PlayerAction / playActionOnce
```

⇒ 角色的**外观资源（`res_id` / `spine_type`）与"英雄/伙伴"数据相关**（`getHero`）。

而我们的服务端对 **`11215`（伙伴列表）回的是空表**
（`SC_11215{partner_list: table}` 条数 0）。

**假设（未验证）**：若 `getHero` 返回 nil，外观资源可能解析不出 → 元素建了但没有可用
Spine 资源 → 屏幕上空白。（"地图模糊"也属同类：能画的东西画出来但质量异常。）

**另一条并行假设（同样未验证）**：图形环境问题 —— 见第七节
（`libGLESv2_emulation.so` 模拟 GLES + armeabi 经 houdini 翻译 + 角色用 Spine）。

### 区分这两个假设的最快方法（先取证再改）

1. **在真机（或换渲染后端的模拟器）上跑同一个 APK + 同一个服务端**：
   若角色出现 ⇒ 图形环境问题，服务端无需改；若仍不出现 ⇒ 往资源解析方向查。
2. 若走资源方向：**把 `11215` 伙伴列表填上至少 1 条**（`partner_list` 的字段结构需先
   从 `cmd_resolve_112.luac` 确认，`D|Dsc*|` 子表未解出前不要猜），再观察角色是否出现。

---

## 六之补四、★★ 最终决定性证据：角色被**完整构建**（外观资源已解析）

抓住 `Player` 实例后逐字段测量：

```
t=playerAppear&v=body_userdata_spine_name__R10100__career_1_action__stand__name_nil
```

| 字段 | 实测值 | 含义 |
|---|---|---|
| `body` | **userdata** | **可视节点真的存在**（cc.Node） |
| `body_spine_name` | **`R10100`** | **Spine 外观资源解析成功**（R + career1 + 01 + 00） |
| `career` | `1` | 与我们下发的 `career=1` 一致 |
| `action_name` | **`stand`** | **站立动画已设置** |

（另测得 `getPositionX/isVisible/getParent` 都不存在 ⇒ `Player` 不是 cc.Node，
而是控制器对象，真正的可视节点是它的 `body` 字段 —— 这正是上面测到 userdata 的原因。）

### 结论：客户端侧一切正常，问题在图形环境

```
数据        ✅  10201 解析 roles=1，字段逐项正确
对象        ✅  addRole → roleList=1，main_role 设置，getMainRoleVo() 可用
加载门禁    ✅  isLoadState = true（createMap 已跑通，mapResCache=192）
可视元素    ✅  createPlayer → Player.New 被调用
外观资源    ✅  body = userdata（节点存在）、body_spine_name = R10100（已解析）
动画        ✅  action_name = stand
──────────────────────────────────────────────────────────────
屏幕上仍看不到角色  ❌
```

**能查的每一层都是对的，而且角色已经被摆成"站立"状态。**
⇒ **服务端与协议侧已无任何可改之处**；剩下的只能是**渲染/图形环境**。

### 这解释了为什么"假设 A（资源解析不出）"也不成立

我此前怀疑"`getHero` 拿不到伙伴数据 ⇒ 外观资源解析不出"。
但实测 `body_spine_name = "R10100"` —— **外观资源已经解析出来了**，
所以这条假设**被否证**。

### 剩下的就是"假设 B：模拟器图形环境"（证据一致指向它）

- 客户端加载 `libGLESv2_emulation.so` / `libGLESv1_CM_emulation.so`（**模拟** GLES），
  而宿主 GPU 是 `Qualcomm Adreno 740 / GLES 3.1`；
- APK 是 **armeabi**，经 **houdini** 做 ARM→x86 翻译运行；
- 角色用 **Spine 骨骼动画**（`body_spine_name` / `spine_renderer.luac` / `spine_manager.luac`）；
- 地图（简单瓦片精灵）**能画出来但模糊**，Spine 角色**完全看不到** ——
  与"简单图形勉强能画、复杂骨骼渲染失败"的表现一致。

**建议的验证（一步就能定论）**：在**真机**、或换一个渲染后端的模拟器上，
跑同一个 APK + 同一个服务端。若角色出现 ⇒ 确认是环境问题，服务端无需任何改动。

---

## 七、四个现象的最终定性

| 现象 | 定性 | 依据 |
|---|---|---|
| ② 地图上没有角色 | **服务端/协议侧已无问题**；角色已被完整构建（节点+Spine 资源+stand 动画），问题在**图形环境** | `body=userdata`、`body_spine_name=R10100`、`action_name=stand` |
| ① 地图模糊 | 同属渲染层（192 瓦片全部加载仍模糊） | `mapResCache=192` |
| ③ 任务为空 | **服务端未实现任务系统**（本阶段明确不做） | 从未下发任何任务数据 |
| ④ 没有 NPC | **服务端 10201 的 npcs/mons/elems 为空表**（未实现） | `on10201&v=roles_1_npcs_0_mons_0_elems_0` |

**① 与 ② 建议先在真机/换渲染后端的模拟器上复验**（一步即可定论）；
**③④ 是把数据按协议补上就会出现**（`on10201` 已有 `addNpc`/`addMonster`/`addElement` 通路）。

---

## 八、自查与纪律

- 本轮**推翻了我自己上一轮的判断**两次：
  1. "`svCall`=0 ⇒ 方法从未被调用" —— 错，是采集时机问题；
  2. "`addRole` 一次都没调用" —— 错，是**挂错对象**（挂 `SceneController`，
     实际在 `SceneModel`）。
  两次都写入本文件，避免后续重走。
- 所有打包前都过 `node tools/lua-check` **硬门禁**（本轮它抓到过一次真实语法错）。
- 未做任何"为了让现象消失"的伪造性修改。
