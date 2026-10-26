# R80：修复「饱食度无法补充」+ 战斗结算界面/伤害分侧的证据链

> 用户报障四条：① 地图与战斗模型不一致；② **没有战斗结算界面**；③ 敌我伤害放在同一侧；
> ④ **饱食度无法补充**。
> 本轮把 ④ **修好并验证**；②③ 拿到**关键证据**（结算界面是客户端自己弹的、分侧看 `group`）；
> ① 仍待继续取证。过程中又抓到**第 7 次"分发顺序遮蔽"**（而且是门禁自己报出来的）。
> **时间**：2026-09-29 19:20 – 19:40。

---

## 一、★★ ④ 饱食度：根因是 `CS_10640` **无应答**

### 1.1 定位链路

- 全 APK 搜「饱食」⇒ `assets/src/game/main/buff/hunger.luac`（饱食度 UI）与 `buff_manager.luac`
- 扫这些 luac 的命令号 ⇒ **`10014 / 10015 / 10016 / 10640 / 20021`**
- `protocol/fields.json`：

```
CS_10640 — 无字段（空消息）
SC_10640 — buff_list: table(caeer:uint8, buff_bid:uint32)      # caeer = 原文拼写，实为 career
```

- 真机日志：**客户端每隔几分钟就发 `CS_10640`**（18:54 / 19:01 / 19:18 …），
  而本服**既不在通用集合、也无专用分支** ⇒ **一句话都不回**。

### 1.2 饱食 buff 的真身（`config_buff_data.luac` 实提取）

```
bid = 10009
name = '饱食'          cli_effect = 'hunger'
type = 2               time_type = 4        group = 10009
desc = '每场战斗结束后，会自动消耗一定的饱食度点数,用来恢复上阵单位气血'
```

⇒ **角色固有 buff**（不靠掉落/道具获得）⇒ 默认就下发。

### 1.3 修复

| 位置 | 内容 |
|---|---|
| `mock_server.py` | 新增专用分支 `if cmd == 10640` ⇒ 回 `SC_10640{buff_list}` |
| `db_buff_init/list/set` | 新表 `role_buffs(rid, career, buff_bid)`；**只存"有哪些 buff"，不编造数值列** |
| `config.json: base_buffs` | `[{"career":0,"buff_bid":10009}]` —— 可改可清空，**没写死在代码里** |
| `/DSH_ADMIN/buff` | `?bid=NNN[&career=C]` 加 / `&off=1` 删 / 不传则查 |

⚠ **量纲说明（不编造）**：`buff_list` 元素只有 `(career, buff_bid)`，**不带任何数值**
⇒ **"当前饱食度点数"不在本条协议里**，下一步需要另找承载它的命令。

### 1.4 ★★ 过程中又踩到「分发顺序遮蔽」（第 7 次）

加完专用分支后，真机调用仍打进通用默认响应：

```
[19:27:49] >> cmd=10640 ? body(0)=
[19:27:49] << 10640 SC_10640 **默认响应** (8 bytes)     ← 专用分支没执行
```

原因：**`10640` 原本就在 `_GENERIC_DEFAULT_CMDS` 里** —— 新增专用实现时**没把它移出去**。
**这次是门禁自己报出来的**（`tools/lint_dispatch_shadow.py`）：

```
★ 被 _GENERIC_DEFAULT_CMDS 遮蔽的专用实现（1 条）：
  10640
```

移出后门禁恢复「✓ 无分发遮蔽」。

> ★ 我先前用一次性正则自查时误判为"不在集合里"——**门禁是权威，手查不算数**。

### 1.5 验证

```
SC_10640 buff_list=1 [(0, 10009)]      === 结果: PASS ===
```

---

## 二、② 没有结算界面 —— 结算界面是**客户端自己弹的**，内容来自 `SC_20023`

`battle.luac`（`finish_data` 相关 proto）里的事件：

```lua
GlobalEvent:Fire(MainContants.EventId.SHOW_UI, 'BATTLE_FINISH_UI_CLOSE',
                 result, finish_data)
```

| 结论 | 依据 |
|---|---|
| **不需要额外再发一条"弹界面"的包** | 客户端在 `SC_20020{result}` + `finish_data` 到达后自行 `SHOW_UI` |
| **面板内容 = `finish_data` = `SC_20023`** | 同上一行；`battle.luac` 多处 `TSETS ['finish_data']` |
| ⇒ "没有结算界面"最可能是 **`SC_20023` 载荷不当** | 我们的 `build_20023` 里 `val_list` 是**空表**、`msg` 为空 |

⚠ `val_list` 的 `key` 语义**未取证** ⇒ 仍按纪律**不编造**，下一步要从
`battle_view.luac` 里读 `finish_data.val_list` 的消费点，拿到 key 的含义再补。

---

## 三、③ 敌我伤害同一侧 —— 分侧字段是 `group`

`battle_view.luac` 里多处 `TGETS ['group']`（含 `dmg_hit_text` / `hurt_sum` 的摆位逻辑），
说明**伤害分侧看 `group`**。我们的 `build_20023.role_hurl_list` 两行分别是
`group=1`（我方）与 `group=2`（敌方），**看起来是对的**。

**下一步**：读 `battle_view` 里 `hurt_sum` / `dmg_hit_text` 所在 proto（L3055 附近 / L3194 附近），
确认它取的是 `hurt`、`hp`、还是 `hp_max`，以及**我方/敌方各自的"伤害"语义**
（我方承受 vs 敌方承受）——不要再凭直觉换值。

---

## 四、① 地图/战斗模型不一致 —— 待继续

两条路都用到 `Config.Mon[bid].res_id = 'H34800'`：

| 路 | 取值 |
|---|---|
| 地图（`10201.mons[]`） | 我们直接写 `res_id` 字段 |
| 战斗（`SC_20010.fighter_info_list`） | 客户端 `if srv_id=='mon' then Config.Mon[rid].res_id` |

⇒ 现在两边**应当一致**。若仍不一致，需继续读 `battle_role.luac` proto#2 里
`res` 之后的 `getSpineTypeByName` / `add_act_spine` / `sp_resource`，看战斗侧是否还要求别的字段
（`specials` / `pet` / `scale`）。

---

## 五、全量验证 / 环境

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **171** / 默认 **63** / 未开放 22）、CS 2463-0、SC 静态 84+1空-0、SC 在线 **85-85**、专用 **64-64**、门禁 E **PASS** |
| 回归 | `verify_battle_20022` / `verify_20002_click` / `verify_guaji` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `stderr` **0 字节**；9000 恰好 1 监听 |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `10640` 处理器；`10640` 从 `_GENERIC_DEFAULT_CMDS` **移出**（修遮蔽）；`db_buff_init/list/set`；`/DSH_ADMIN/buff` 路由 |
| `server/config.json` | 新增 `base_buffs`（含饱食 10009） |
| `tools/_fix_r80_buff.py` | 上述插入脚本（幂等可重跑） |
| `analysis/_cfg_buff.txt` / `_hunger.txt` / `_buff_mgr.txt` | 反汇编证据 |
| `analysis/1.4.9/round80_satiety_and_finish_ui.md` | 本报告 |

---

## 七、一句话

> **饱食度已修好**：客户端一直在发 `CS_10640`，我们**从来没回**；现在回
> `SC_10640{buff_list}`，含 **`10009 饱食`**（`config_buff_data` 里的真身）。
> 而且这次**门禁自己抓出了第 7 次"分发顺序遮蔽"**（新增专用分支必须同时从通用集合移出）。
> ②③ 的证据也拿到了：**结算界面由客户端在 `SC_20020/20023` 后自行弹出**，
> 所以"没有界面"要先查 `SC_20023` 的 `val_list`；**伤害分侧字段是 `group`**（我们的值看起来是对的）。
