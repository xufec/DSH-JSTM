# 四项后续任务的执行状态与取证结论

> 用户要求：① 校准战斗数值到原版 ② 关闭移动替身 ③ NPC 对话 UI ④ Phase C 定性 25 条协议
> 本文给出**已完成的**、**有取证结论的**、以及**仍未做的**。

---

### ★★ 深入取证后的**更正**（原判断被数据否证）

**原判断**：`Config.MonData.hp_num` 存在 ⇒ **血量可校准**。
**深入取证后**：**否证。**

从 `proto[0]`（**7,956 条怪物条目**）统计：

```
总条目:          7956
type 分布:       [(1, 6273), (0, 1205), (4, 427), (6, 24), (7, 20), (2, 7)]
hp_num > 0 的:   ★ 只有 27 条
hp_num 常见值:   [(0, 7929), (5, 10), (1, 10), (3, 7)]
```

**⇒ 7,956 条里 7,929 条 `hp_num = 0`（99.7%）。**
**⇒ `hp_num` 不是"战斗血量"**（更可能是段数/变体数之类），**不能用来校准战斗血量。**

（抽查「邪魂法师/邪魂祭祀」等：`hp_num` 全为 0。）

### ★ 最终结论（经否证后）

| 战斗数值 | 结论 |
|---|---|
| 怪物血量 | ❌ **不可校准**（`hp_num` 99.7% 为 0，不是血量） |
| `atk` / `def` | ❌ **不可校准**（字段根本不存在） |
| `exp` / `coin`（击杀奖励） | ❌ **不可校准**（字段根本不存在） |
| `name` / `res_id` / `lev` | ✅ 可从 `Config.MonData` 取（已确认结构） |

**⇒ "把战斗数值校准到原版"这个任务，在 1.4.9 客户端配置范围内**做不到** ——
因为战斗数值（血量/攻防/奖励）**根本不在客户端配置里**，应属**服务端数据**，而原版服务端数据我们没有。**

**⇒ 因此现有实现保持 `TEST_ONLY` 标注是**唯一诚实的选择**，不应伪装成原版数值。**

**（按项目规则，被否证的假设保留记录 —— 本文档即保留了从"可校准"到"否证"的完整过程。）**

---

## 已产出的工具（可复用）

| 文件 | 作用 |
|---|---|
| `tools/extract_mon_data.py` | `Config.MonData` 提取器（含 23 字段下标映射） |
| `tools/extract_mission_config.py` | `Config.Mission` 提取器（846 条） |
| `tools/build_quest_route.py` | 剧情路线图生成器（262 条主线） |

**`Config.MonData` 的 23 字段下标映射（`proto[1]` 的 `__index` 反汇编所得）：**
```
d[1]=name  d[2]=lev  d[3]=type  d[4]=type2  d[5]=career  d[6]=special_type
d[7]=hp_num  d[8]=res_id  d[9]=born  d[10]=leave  d[11]=sound
d[12]=enter_map_effect  d[13]=width  d[14]=height  d[15]=anime_die
d[16]=die_effect  d[17]=mon_list  d[18]=formation_type  d[19]=filter_id
d[20]=halo_id  d[21]=model_size  d[22]=desc  d[23]=dir
```
（其中 **没有** `atk`/`def`/`exp`/`coin` —— 已确证。）

---

## ① 校准战斗数值到原版 —— **结论已更正为"不可校准"**

### ★ 决定性取证：`Config.MonData` 的真实字段

从 `config_mon_data.luac`（857,309 字节）的 **`proto[1]` 字段名表**逐项读出：

```
anime_die, born, career, data, desc, die_effect, dir, enter_map_effect,
filter_id, formation_type, halo_id, height, hp_num, leave, lev, model_size,
name, res_id, sound, special_type, type, type2, width
```

（`proto[2]` 是 `Config.Filter.Mon` / `setmetatable` 的索引包装器；`proto[0]` 是数据本体。）

### 判定

| 战斗数值 | 在 `Config.MonData` 里? | 能否校准到原版 |
|---|---|---|
| **`hp_num`（怪物血量）** | ✅ **有** | ✅ **可以校准** |
| `lev` / `name` / `res_id` | ✅ 有 | ✅ 可以 |
| **`atk` / `def`** | ❌ **没有** | ❌ **不可能** |
| **`exp` / `coin`（击杀奖励）** | ❌ **没有** | ❌ **不可能** |
| 掉落 | `config_drop.luac`(8,195) / `config_drop_item.luac`(3,939) 已存在 | ⚠️ 部分可校准 |

**⇒ 结论（实事求是）：**
- **"把战斗数值完全校准到原版"**做不到** —— 因为 `atk`/`def`/`exp`/`coin` **在 1.4.9 客户端配置里根本不存在**
- **但 `hp_num` 可以校准**，这是**最大可校准范围**
- 现有实现已把不可校准项标为 **`TEST_ONLY`**（`battle.py` 第 98–116 行，注释里写明"APK 里没有"）—— **标注是诚实的，不是伪装成原版**

### 已做

在 `config.json` 记入 `mon_calibration_note`，把**可校准字段清单**固化下来。

### 未做（下一步）

**写一个 `Config.MonData` 提取器**（结构同 `extract_mission_config.py`：`proto[0]` 状态机 + `TSETV`），
把每只怪的 **`hp_num` / `lev` / `name` / `res_id`** 导成 JSON，再让 `battle.py` 按 `hp_num` 取血，
**替换掉 `MON_STATS['hp_max'] = 2400` 这个 TEST_ONLY 值**。

---

## ② 关闭移动替身 —— ✅ **已完成**

```json
"mission_auto_progress": false,
"mission_progress_note": "替身已关闭：任务进度只由真实战斗结算推进（battle mission progress）"
```

**⇒ 从此任务进度**只由真实战斗**推进**（已实测：`** battle mission progress: fight_mon target=20001 -> [10020]`）。

服务端重启：`stderr 0 字节`、8080/9000 正常。

---

## ③ NPC 对话 UI —— ❌ **未做**（本轮容量不足）

已知现状（Phase 5C 遗留）：

| 项 | 状态 |
|---|---|
| `NpcDialogs:openNpc(bid)` | ✅ **可调用**（传 **bid 数字**，不是 VO 表；传表必报 `npc_dialogs.luac: attempt to index a nil value`） |
| `Npc:clickHandler` | ✅ 可调，`Fire(SceneEvent.SCENE_NPC_CLICK, vo)` |
| **对话框渲染** | ❌ **不出画面** |
| 当前提交任务方式 | 探针直调 `MissionCtrl:getInstance():submit(bid)`（**非原版交互**） |

**⇒ 目标**：让"点 NPC → 出对话框 → 接/交任务"走原版链路。
**拦路点**：`scene_model.luac` 的 `SCENE_NPC_CLICK` 监听者**后段 nil**（已排除 `type` 因素，`config.json` 的 25 个 NPC `type` 已按 `ObjType.NPC=2` 修正）。

---

## ④ Phase C：25 条未查清协议 —— ❌ **未做**（本轮容量不足）

`MissionCtrl` 注册 33 条，**已查清 8 条**：
```
12400 12401 12402 12403 12404 12405 12406 12416
```
**未查清 25 条**：
```
12407 12408 12409 12412 12413 12414 12415 12417 12420 12421 12422
12440 12450 12451 12452 12460 12499 15405 15420 15421 15422
18500 18501 18505 19500
```
（已知处理函数名：`addAccessHandler(12407)`、`deleteCanHandler(12408)`、`addCanHandler(12409)`）

**⇒ 方法**：逐条 `tools/show_cmd.py <cmd>`（有字段定义即抄录）；无线级定义的，
用探针包住 `mission_ctrl` 里对应的 handler 名字，**观测它读哪些字段**（同 F3 手法）。

---

## 当前系统状态

```
服务端   8080/9000（PID 27748，stderr 0 字节）｜ mission 846 条
替身     mission_auto_progress = false（只走真实战斗）
战斗链   已验证（20002→20010→20012/20013↔20014→20020→20023）
任务链   已验证（10010→10020→10030→10040 完成，10051/10052 可提交）
持久化   SQLite 四表（roles / role_attr / missions / role_assets）
备份     backup/before_quest_restore/ 完好
```
