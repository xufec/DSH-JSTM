# R57：执行 B（等级改回 70）+ 挂机**全链路**验证器

> 项目方选择 **B**：把 `rid=1001` 的等级改回 70。
> 本轮另把 `verify_guaji.py` 扩成**覆盖整条挂机链 6 个环节**的一键验证器。
> **时间**：2026-09-29 11:25 – 11:40。

---

## 一、执行 B：等级改回 70（已确认）

```
GET /DSH_ADMIN/setlevel?lev=70
→ {"ok": true, "rid": 1001, "level": 70, "pushed": 1}
```

**口径一致性复验**（R56 修的那条）：

```
== 等级口径 ==
  DB(admin /status) : 70
  10302             : 70
  13340             : 70
  一致: 是     === 结果: PASS ===
```

**门禁 E 复验（★ 条件豁免的"重新武装"在真实数据上得到证明）**：

```
改回 70 前：role_lev=9  → 20100:promote 命中条件豁免（when.role_lev_lt=17）
改回 70 后：role_lev=70 → 条件**不成立** ⇒ 该豁免失效，
                        而 `20100.promote` 此时**实际非空**（18 条 tips）⇒ 0 告警
```

⇒ 说明：豁免并没有把 `promote` 永久遮掉 —— 一旦等级够高，门禁会重新盯着它。
（这也是"条件式豁免"这套设计的验收依据。）

---

## 二、★ 挂机**全链路**验证器（`tools/verify_guaji.py` 扩容）

原来只覆盖 `15402/15403/15404`，本轮补上最前面两环，现在**一条命令跑完整条链**：

```
15405 轮次查询（客户端打开 NPC 对话框时由 requestHuan() 发出）
      → SC_15405{loop_count=0}                          PASS（len=2 消耗=2）
15400 启动挂机（由 funBtnHandler 在 btn.id==4019 时触发）
      → SC_15400{code=1, msg=''}                        PASS（len=3 消耗=3）
15402 任务→地图/坐标
      → {mission_bid=10010, map_bid=10005, (10,58)}     PASS（命中 config_guaji 的 10105 乾坤日月谷）
      → mission_bid 落库 10010                          ✓
15403 杀怪上报（真实挂机怪 10101）
      → code=1，kill_count 0 → 1 **真落库**              PASS
15403 杀怪上报（未知怪 999999，反向用例）
      → code=0 + msg='未知怪物(999999)'，计数**不变**     PASS
15404 轮次结束推送（/DSH_ADMIN/guaji_end 显式触发）
      → 1 帧、按规格精确解析 mission_bid=10010            PASS

跑完把 guaji_state **原样恢复**（无副作用）
=== 结果: PASS ===
```

**⇒ 服务端侧整条挂机链已就绪并逐环验证。**
唯一剩下的是**客户端那一下点击**（`btn.id == 4019`），见 §三。

---

## 三、客户端点击：本轮仍未打通（如实记录 + 给出可靠办法）

### 3.1 本轮实际尝试

| 尝试 | 结果 |
|---|---|
| R48 记录的「日常」(128,240) | ❌ 未命中（日志无 `13781`） |
| 裁剪+百分比估算 (105,308) | ❌ 未命中 |
| 视觉模型判读"日常在哪" | ❌ 与截图实际不符（同一屏两次读数互相矛盾） |

⇒ 与 R55 的结论一致：**用视觉估算坐标点 UI，成功率很低**；且**客户端是否停在"带左侧菜单的主城"**本身也有状态依赖。

### 3.2 ★ 可靠办法（下一轮直接做）：用**已有的探针**上报按钮坐标

项目**已经**有一套跑通的 Lua 探针（`server/dsh_fake_login.lua`，注入到 APK，向
`http://10.0.2.2:8080/DSH_PROBE?t=<tag>&v=<val>` 上报），它已经在挂钩：

```
npcE   — NPC 元素事件（`registEvent_vo_bid_50000` … `vo_bid_50007`、`clickHandler`）
dlgS   — 对话框：`enter_bid:` / `manager_npc_n:…` / `after_rootwnd:…` / `openNpc_wrapped`
npcH   — NPC 处理函数包装
view / state / roles / bp / …  — 已有 20+ 种上报
```

**做法（零猜测）**：在探针里对 `NpcDialogs:createBtn` 加一个包装，把每个按钮的
**`btn_key` / id / 世界坐标 / 屏幕坐标**用 `report('dlgBtn', ...)` 打出来，
然后从 `server/logs/http.log` 直接读出**精确坐标**去 `adb shell input tap`。

判据仍然是：**日志里出现 `>> cmd=15400`**。
这条改动需要走 APK 重打包链（`tools/patch_fake_login.py` → `zipalign` → `apksigner` → `adb install -r`，
HANDOVER §4.2 有完整命令），**因此不在本轮擅自执行**（会替换玩家正在用的客户端）。

---

## 四、全量验证（lev=70 基线）

| 门禁 | 结果 |
|---|---|
| `lint_dispatch_shadow.py` | 专用 169 / 默认 64 / 未开放 22 ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 / **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 86 命令：85 一致 + 1 空规格 / **0 不一致** |
| `audit_sc_live.py --unsupported` | **86/86 一致** |
| `audit_dedicated.py` | **63/63 符合规格** |
| `audit_emitted_fields.py` | 132 条 / `role_lev=70` / 顶层空表告警 **0** / **PASS**；`--selftest` **PASS** |
| 回归 | `guaji`(扩容后) / `level_consistency` / `race` / `attr_power` / `arena` / `dungeon` / `mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `stderr` 0 字节；9000 端口恰好 1 个监听；DB 20 表、玩家数据未污染 |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/verify_guaji.py` | **扩容**：`15405 → 15400 → 15402 → 15403(含反向用例) → 15404` 全链一条命令跑完 |
| `analysis/1.4.9/round57_guaji_fullchain.md` | 本报告 |
| （等级）`server/state/roles.db` | `rid=1001` 等级由 9 改回 **70**（经项目方决定，走 admin 接口） |

---

## 六、下一步

| 优先 | 事项 | 判据 |
|---|---|---|
| 1 | **探针加 `dlgBtn` 上报**（§3.2）→ 拿到 4019 按钮的精确坐标 → 点击 | 日志出现 `>> cmd=15400` |
| 2 | 命中后**一次走完**整条链（脚本已就绪）：`15400 → 15402 → 15403 → guaji_end` | `verify_guaji.py` PASS + 真机挂机画面 |
| 3 | 顺手把监察线（`zhuoyao`）的 `15402.mission_bid` 抓出来填 `_chengjiu_map.json` | 多一组真实映射 |
| 4 | `mock_server.py` 拆分（`handlers/`；计划里的 R55 顺延项） | 六道门禁数字**不变** |
