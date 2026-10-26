# R65/R66：★★ 探针给出决定性答案 —— **怪其实早就被建出来了，前十轮的判据是错的**

> 项目方批准了 APK 重打包（方案 A）。本轮完成：
> ① 注入 4 组 ghost 探针（`gh15402` / `ghinit` / `ghcreate` / `ghost`）并重打包安装；
> ② **探针立刻推翻了我自己前十轮的判断**：`createMon()` 四个条件全过、**怪真的被建出来了**；
> ③ 据此修正坐标（怪生成在玩家脚下），并写下一条重要的方法论教训。
> **时间**：2026-09-29 14:15 – 14:35。

---

## 一、探针注入与构建（全部走通）

| 步骤 | 结果 |
|---|---|
| 备份当前客户端 | `patched/jstm_fakelogin.apk.bak_r65`（241,414,402 B） |
| Lua 语法门禁 | `node tools/lua-check/check.js` → **OK**（126,351 B） |
| 打补丁 | `patch_fake_login.py` → `jstm_fakelogin_raw.apk`（230.4 MB，lua 127,786 B） |
| 对齐 + 签名 | `zipalign -f -p 4` → `apksigner`（`CN=DSH` 验签通过） |
| 安装 | `adb install -r -d` → **Success**，`lastUpdateTime=2026-09-29 14:25:47` |

### ★ 构建中踩到并修掉的一个坑（值得记）

第一版探针**一行都没上报**：我把它插在了文件里 `_G.__dsh_battle = false` 守卫的
**战斗探针块**内 ⇒ `if not _G.__dsh_battle then return end` **整块直接返回**。

```lua
_G.__dsh_battle = false
pcall(function()
  ...
  if not _G.__dsh_battle then return end     -- ★ 我插在这下面 ⇒ 永远不执行
```

⇒ 改为**独立顶层 `pcall` 块**（自己的 `__dsh_ghost_blk` 守卫 + 从 `_G.__dsh_report` 取上报函数）。
改完首次启动即上报 `ghost&v=installed`。

> **教训**：往探针文件里加东西，**必须确认插入点所在 pcall 块没有前置守卫**。

---

## 二、★★ 探针结果（决定性）

```text
[14:26:05] t=ghost   &v=installed

[14:27:54] t=gh15402 &v=called_mb_10010_map_10005_scene_10005_hongchen_before_false
[14:27:54] t=ghinit  &v=in_mb_10010_in_map_10005_scene_10005
[14:27:54] t=ghcreate&v=mon_bid_10105_cfg_table_cfg_map_10005_scene_10005_cfgMon_table_hasMon_true
[14:27:54] t=gh15402 &v=after_hongchen_true          ← ★★ 实例被创建
[14:27:54] t=ghcreate&v=done_mon_id_30068            ← ★★★ **怪真的建出来了**
[14:27:54] t=ghinit  &v=after_mb_10105_cfg_table_cfg_map_10005_scene_10005
```

逐条对照 `createMon()` 的四个早退条件（R62 反汇编）：

| 条件 | 探针实测 | 结果 |
|---|---|---|
| ① `mon_bid` 非空 | `mon_bid=10105` | ✅ 过 |
| ② `mon_cfg ~= nil` | `cfg=table` | ✅ 过 |
| ③ `getSceneId()==mon_cfg.map_bid` | `scene=10005` / `cfg_map=10005` | ✅ 过 |
| ④ `Config.Mon[mon_bid]` 存在 | `cfgMon=table` / `hasMon=true` | ✅ 过 |
| → 结果 | **`done_mon_id=30068`** | ✅ **怪已加入场景** |

---

## 三、★★ 最重要的更正：**判据本身错了**

前十轮（R59–R64）我一直用「**客户端有没有发出新包**」当作"挂机有没有启动"的判据，
并据此写下 9 次"否证"。**探针证明这个判据不成立**：

> `createMon()` 最后一步是 `GlobalEvent:Fire(SceneEvent.SCENE_CLIENT_ADD, vo)`
> —— **这是客户端内部事件，不产生任何网络包**。
> 所以"服务端日志里之后只有心跳"**恰恰是正常的**，它不代表客户端没动作。

⇒ **R60 起挂机链其实已经跑通了**（`15400 → 10200(10005) → 15402 → 客户端建怪`），
只是我一直在用错的仪表盘看它。

> ★ 这条比"再试一个参数"值钱得多：**先确认判据能观测到被测对象，再下结论。**

---

## 四、为什么屏幕上仍看不见怪（已修正）

`createMon` 建怪的坐标取 `mon_cfg.x/y`，而 `mon_cfg` 就是 `SC_15402` 整包
⇒ 我们发的是**地图默认出生点 (10,58)**，而玩家被 `10200` 放到 **(68,61)**，
相距 58 格 ⇒ **怪在视野外**。

**已修**（`config: guaji_15402_use_role_pos`，默认 true）：`SC_15402` 的 `x/y` 改用**角色当前坐标**，
让怪生成在玩家脚下。

⚠️ 本轮复测时 **4019 按钮那一下点击没命中**（连试 4 个坐标均为 0）⇒ **视觉确认未取得**，
留给下一轮（坐标 (1853,869) 在 R58/R64 已两次命中，属可复现动作）。

---

## 五、当前配置（这套现在是"挂机可跑通"的组合）

| 配置 | 值 | 作用 |
|---|---|---|
| `guaji_push_15402` | `true` | `15400` 后主动推 `SC_15402`（客户端不会自发） |
| `guaji_enter_scene` | `true` | 先推 `10200(10005)+10201` 把玩家送进挂机图（`createMon` 条件③） |
| `guaji_enter_scene_delay` | `3.0` | 给客户端切场景的时间 |
| `guaji_15402_use_role_pos` | `true` | **新增**：怪生成在玩家脚下（否则离屏） |
| `guaji_mission_bid` | `10010` | 依据 R48 真机抓包 |
| `missions[10010].target` | **10105** | ★ **必须**：`mon_bid` 来自 `SC_12400.target`，而 `10105` 是 `config_guaji` lev65–74 段的怪（`Config.Mon[10105]=圣灵教精英`） |

> ⚠️ **数据播种说明（需下一轮形式化）**：`missions[10010]` 的 `status=2 / target=10105`
> 是我手工改的（`tools/exp_mission_target.py`）。**正确做法应是把"挂机任务的 target"写进
> mission 配置的生成逻辑**，而不是手改 DB。当前保留该值，因为**没有它挂机链不成立**。

---

## 六、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**、CS 规格 2463-0、SC 静态 85+1空-0、SC 在线 **86-86**、专用 **63-63**、门禁 E **PASS** |
| 回归 | `verify_guaji` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `stderr` **0 字节**；9000 恰好 1 监听；玩家 lev=70 / gold 841046 / 背包 27；客户端在跑（新 APK） |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `server/dsh_fake_login.lua` | **新增 4 组 ghost 探针**（独立顶层块）；备份 `dsh_fake_login.lua.bak_r65` |
| `tools/_fix_r65_move_probe.py` | 把探针从"战斗块"搬到独立块的脚本（含原因注释） |
| `patched/jstm_fakelogin_aligned.apk` | **新客户端**（已装入 MuMu） |
| `patched/jstm_fakelogin.apk.bak_r65` | 旧客户端备份 |
| `server/mock_server.py` | `SC_15402` 的 `x/y` 改用角色当前坐标（`guaji_15402_use_role_pos`） |
| `analysis/1.4.9/round65_66_probe_verdict.md` | 本报告 |

---

## 八、下一步

| # | 动作 | 判据 |
|---|---|---|
| 1 | 复跑一次（点 4019）→ **截图确认怪在玩家脚下** | 画面里出现「圣灵教精英」 |
| 2 | 看客户端是否**自动开打**（`SCENE_CLIENT_ADD` 后 `GhostMon:fight()`） | 探针已可加 `ghfight`；或看是否出现 `>> cmd=20002` / `15403` |
| 3 | 把"挂机任务的 target"**形式化**进任务生成逻辑（别手改 DB） | 代码里可追溯 |
| 4 | 若自动开打 ⇒ 接 `15403`（已有）→ `/DSH_ADMIN/guaji_end` 走完整轮 | `verify_guaji.py` |
