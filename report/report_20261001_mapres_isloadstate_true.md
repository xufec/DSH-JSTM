# 追查"不能移动/地图不清晰" —— ★ 既往结论在**当前会话被否证**：`isLoadState` 是 **true**

> 时间：2026-10-01 ｜ 做法：按既往文档线索①（盯 `mapResAsyncList`）做 v50 探针 + 实测

---

## 〇、一句话结论

> ★ **既往文档的根因（`isLoadState` 门禁为 false）在当前会话不成立**：
> v50 探针实测 **`SceneModel.isLoadState = true`**（全程稳定为 true），
> 即 `scene_controller.move` 开头那道 `if not self.model:isLoadState() then return end` **是开着的**；
> **但客户端依然 0 次 `CS_10204`**、地图不清、NPC 不显示。
> ⇒ **"不能移动"现在不能再用那道门禁解释** —— 旧的"修法/结论"**不能照搬**，必须另找原因。
> （这条否证本身很有价值：避免了照着过期结论去修一个已经不存在的问题。）

---

## 一、本轮证据

### 1.1 v50 探针（新加，追 `mapResAsyncList`）

```
$ head -30 /data/user/0/com.shiyue.dldl.ewan.qihoo/files/dsh_v50.txt
v50_mapres_async_probe
-- state SceneModel.isLoadState=nil    SceneView.model.isLoadState=nil      ← 进图前（模型还没建）
-- state SceneModel.isLoadState=nil    …
-- state SceneModel.isLoadState=true   SceneView.model.isLoadState=nil      ← ★ 进图后**恒为 true**
（其后 30 行全部是 isLoadState=true）
$ wc -l → 33 行；**没有** `hooked=` 行、**没有**任何 `*res*` 表 dump 行
```

### 1.2 客户端协议侧（同期）

```
t=state → scene_table:_0xc4afc658_role_table:_0xc8297918_recv_300      ← 在图内、活跃
live14 客户端命令: {1199:218, 10502:156, 10300:21, 10800:21, 13300:21, 10923:21, 13321:21, 16400:16, 10921:13, 10922:13}
10204 次数: 0                                                          ← ★ 从不移动
```

---

## 二、与既往文档的差异（诚实对照）

| 项 | 既往会话（`analysis/1.4.9/movement/movement_test.md`） | **本会话（今天）** |
|---|---|---|
| `isLoadState` | **恒为 false** ⇒ `move()` 空转、不发包 | **恒为 true** ⇒ 门禁**开着** |
| 移动 | 需**强行 `setLoadState__(true)`** 才能让 `move()` 发包（**诊断为诊断手段，非修复**） | 门禁已开，**但客户端仍不发 `10204`** |
| 结论 | 卡点在"地图资源异步加载没走完" | **该结论对本会话不适用** ⇒ 卡点在别处 |

> 注意：既往文档自己也写明"`setLoadState__(true)` 是诊断手段、不是修复"——
> 而现在它**本来就是 true**，所以这条线索到此为止。

---

## 三、本轮**未装上**的挂钩（如实记录）

v50 想在 `SceneView` 上挂 `asyncLoad`/`asyncLoadRole`/`getPicRes`/`updateNpcAnimateRes`（这些名字来自
`scene_view.luac`：proto#70/#72/#67/#56/#140）并打印**资源名**，但：

- 文件里**没有** `hooked=` 行 ⇒ 挂载循环一个都没命中；
- 也没有任何 `*res*` 表 dump ⇒ 说明 `SceneView:getInstance()` 在探针里**拿不到实例**
  （`SceneModel:getInstance()` 是好的——`isLoadState` 就是从它读到的）。
- ⇒ **UNKNOWN**：`asyncLoad*` 挂在哪个实例上（下一步换访问路径，例如经 `SceneController` 持有的 view）。

---

## 四、由此得到的**新**方向（下一轮第一件事，便宜且判据明确）

既然 **门禁是开的**，那么"**直接调客户端自己的 `move()`**"应当**立刻发出 `10204`**：

```
探针: SceneController:getInstance():move({x=<当前x+4>, y=<当前y>})   →  看服务端是否出现 >> 10204
```

- 若**出现 `10204`** ⇒ **移动协议链路是通的**，问题纯在"**点击/摇杆事件没进到游戏的移动逻辑**"
  （即输入层或命中判定问题）⇒ 下一步查点击事件为何不触发 `move()`；
- 若**仍无 `10204`** ⇒ 说明 `move()` 内部还有**别的**提前 return（例如 `isOnTeamFollow()` 为真、或坐标非法），
  下一步打印 `move()` 入口的几个前提值。

> 既往文档正是用这一招区分"协议问题"和"门禁问题"的（当时结论是门禁）；
> 现在门禁已开，正好用同一招定位**新的**原因。

---

## 五、完成 / 未完成

### 5.1 完成
1. ★ **否证既往根因对本会话的适用性**：`isLoadState=true`（而既往是 false）⇒ 不能照搬旧修法。
2. ★ 新增 v50 探针（`isLoadState` + `*res*` 表 + 加载类函数挂钩的框架）并落盘可复查。
3. ★ 拿到同期协议侧对照证据（在图内、活跃拉子系统、**`10204`=0**）。
4. ★ 给出**下一轮判据明确的实验**（直接调 `move()` 看是否发 `10204`）。

### 5.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 挂钩 `SceneView.asyncLoad*` 打印资源名 | ❌（实例拿不到，UNKNOWN） |
| 2 | "点击/摇杆为何不触发移动" | ❌（下一轮用 `move()` 直接调用实验定位） |
| 3 | 地图不清晰 / NPC 显示 | ❌（与移动同源待定） |
| 4 | 充值档位承载命令 | **UNKNOWN** |

---

## 六、产物

| 文件 | 说明 |
|---|---|
| `server/_ml50_add.lua` | ★ v50 探针（isLoadState + res 表 + 加载函数挂钩框架） |
| 设备 `files/dsh_v50.txt` | ★ **`isLoadState=true`** 的实测记录（本轮关键证据） |
| `logs/minloop/live14_stdout.log` | 同期协议证据（`10204`=0） |
| `analysis/1.4.9/movement/movement_test.md` | 既往对照文档（结论已不适用，保留在案） |
