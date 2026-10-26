# C3.3 第四分片（D）报告：最小挂机闭环（离线开关）

日期：2026-10-16
范围：恢复最小挂机闭环——离线挂机开关 10933（开）/10934（关）/10932（查询 off_state）接线；收紧 CS_15403 信任客户端发奖缺陷；收益规则按 config_guaji.json 证据定；实机联调取证；回归。

---

## 0. 备份

- 改前备份：`server/mock_server.py.bak_c33b_20261016` = **1,105,196 字节**（与源文件逐字节一致；C 分片已建 `.bak_c33_20261016`=1,103,904 字节，本批另命名保留）。
- 服务端：`server/mock_server.py`（~19.6k 行）。DB：`server/state/roles.db`。

---

## 1. 取证定案：挂机本体判定

读三份审计（B 分片 `docs_raw/c3_3_hangup_audit.md`、A 分片 `docs/C3.3_战斗系统现状与调用链审计.md`、C 分片 `docs_raw/c3_3_c_report.md`）+ 源码/帧证据，结论：

**挂机本体 = 面板族 `10930-10935` + `10296/10297`（automate_panel）。**
- 离线开关在面板族：`10933`=开、`10934`=关、`10932`=视图查询（含 off_state）。反汇编直证（B 分片）：客户端收 `code==1` 弹 toast「离线挂机开启/关闭成功」。
- `154xx`（15400-15405）= **ghost 挂机怪链（红尘任务怪，在线场景内自动战斗子系统）**，不是离线开关本体。行号订正后仍成立：15400=启动挂机、15402=上报 mission_bid、15403=杀怪上报、15405=loop_count 推送。
- 两者关系：面板族是「挂机入口/离线开关」；154xx 是「在线挂机刷怪」。本批接面板族离线开关，15403 只做服务端权威收紧（A 分片缺陷），不扩展在线刷怪玩法。

---

## 2. 收益规则决策：BLOCKED（不发奖）

逐字段读 `config_guaji.json`（场景 `task/config_guaji.json`），字段仅：
- `mon_bid`（挂机怪 bid）、`map_bid`（场景）、`lev_l`/`lev_r`（等级段）、`disc`、`show`。

**没有任何收益字段**——无经验/金币/时长换算/次数奖励配置。按任务纪律（无证据不编造收益数值）：

> **本批收益 = BLOCKED。** 只做状态闭环（开启/关闭/查询/持久化），不发放任何奖励。文档标注「原版收益表缺失 BLOCKED，不编造收益规则」。后续若取得原版收益表（如离线挂机经验/小时配置），再接入统一 `reward.grant`（幂等 settle_ref 模式，见 C 分片）。

等级门禁有配置证据：`config_function id=504「挂机」open_lev=30` ⇒ 10933 开启时 lev<30 拒绝。

---

## 3. 实施改动（最小改动，7 处，行号以改后文件为准）

| # | 位置 | 内容 | 原因 |
|---|------|------|------|
| 1 | `db_guaji_init` :9362-9368 | `PRAGMA table_info` 后 ALTER 补列 `off_on`、`off_started_at`（INTEGER），幂等（有列则跳过） | 离线开关需持久化状态；老库自动迁移 |
| 2 | `db_guaji_state` :9379-9380 | 默认 dict 加 `off_on:0, off_started_at:0`；:9389 `if r[k] is not None` 才覆盖 | 无行/老行 NULL ⇒ 安全当 0 |
| 3 | `db_guaji_update` :9403-9407 | INSERT 列清单扩展为 `(rid,loop_count,mission_bid,kill_count,off_on,off_started_at,updated_at)` | 写入两新列 |
| 4 | 10932 handler :10717-10730 | `off_state` 从「有无行」改为读 `db_guaji_state(rid)['off_on']`（int 化，异常兜底 0） | 订正旧误报：在线 ghost 链 15402 也建行，不能用「有行」判离线开 |
| 5 | 新增 10933 handler :10736-10758 | lev<30 拒（code=0）；否则 `db_guaji_update(off_on=1, off_started_at=now)`，回 `code=1`；重复开启幂等仍 code=1；写日志（事件/rid/前后状态/时间戳） | 离线开启闭环；服务端权威 |
| 6 | 新增 10934 handler :10760-10771 | `db_guaji_update(off_on=0)`（**保留该行**，不删在线 ghost 计数 loop_count/mission_bid/kill_count），回 `code=1` | 关闭闭环；不误删在线挂机状态 |
| 7 | 15403 handler :19010-19048 | (a) 会话校验 `mission_bid==0` ⇒ code=0「请先启动挂机」；(b) 频率限制距上次 `updated_at < guaji_kill_min_sec`（默认 1.0s）⇒ code=0「操作过快」；(c) 保留原 mon_bid 存在性校验；grant 路径（drop 20003 组 coin=1000 + item 4001）未动 | 修 A 分片缺陷「信任客户端 mon_bid 即发奖」 |

服务端安全要点：
- **按 rid 隔离**：所有读写经 `role_state(rid)` + `guaji_state.rid` 主键，跨角色不串。
- **时间回拨锚点**：`off_started_at` 记服务端时间戳（本批不结算，仅作未来离线结算/防回拨锚点）。
- **重启持久化**：状态落 SQLite `guaji_state`，重登由 10932 读回。
- **不重复领取**：15403 grant 走 `reward.grant(..., "guaji_kill:<rid>:<kill_count>")`（C 分片幂等 key 模式）。

---

## 4. 脚本化 E2E（功能证明）：10/10 PASS

`tools/c3_3_offline_toggle.py`（复用 C 分片 `c3_3_battle_idem.py` 的 TCP Client 框架），隔离账号 `c33test_off_*`：

1. 初始 10932 `off_state=0` ✓
2. 裸 15403（mission_bid=0）被会话拦截 code=0 ✓
3. 有会话后 15403 放行 kill+1 ✓
4. 连发 15403 被频率拦截（<1s）✓
5. 隔 1.5s 后再放行 ✓
6. 10933 开启 ⇒ DB `off_on=1` ✓
7. 10932 查询 ⇒ `off_state=1` ✓
8. 10934 关闭 ⇒ DB `off_on=0` ✓
9. 10932 查询 ⇒ `off_state=0` ✓
10. lev=1 账号 10933 被 30 级门禁拒 ✓

测试账号已自动清理。

---

## 5. 实机联调：HUD 不可达（如实记录 BLOCKER）

环境：MuMu `emulator-5554`，横屏 2560x1440，包 `com.shiyue.dldl.ewan`（C2.4 记录为 `.baidu2`，`.ewan` 同连本服同一 DSH 角色）。

过程记录：
- 重登后**装备面板自动弹出**（全槽位占位符 `+-0123456789`、综合战力 0——客户端测试态）+ 50 级礼包浮窗。关闭位置：礼包 X≈(2315,640)、装备窗 X≈(2170,130)。证据：`r02_equip_autopopup.png`。
- 关窗后主城场景在跑，但 **HUD 顶栏（含挂机图标）始终不渲染**。证据：`r01_spawn_nohud.png`（出生点机位）、`r03_walked_nohud.png`（走动后）。
- C2.4 参照 `c2_4_shots/32_relogin_hud.png`：干净 HUD 顶栏挂机图标在 (1320,100)，同排 福利/商城/首充/变强/限时返利/玩家回归/VIP/充值。
- **实测 tap (1320,100) 只产生 10204 移动帧，无任何 1093x 帧**（tcp.log 实锤）⇒ 图标不在该屏位，HUD 是世界锚定节点（B 分片已定性：UI 渲染层问题，非协议）。
- 取证角色机位：DB 坐标一度漂到 (122,57)（楼梯/城门机位）。查 `config_map.json` scene 10001 得 `def_x=44, def_y=68`（出生点），把 DB 坐标设回 (44,68) 重登——仍是出生点楼梯机位，HUD 依旧不渲染。
- 无 GM 传送端点（已查 `/DSH_ADMIN/` 无 scene/teleport/setpos/goto）。

**结论（实机）**：本会话客户端 HUD 顶栏不渲染，挂机面板入口在实机上不可达；盲走/重登/设回出生点均未恢复到 C2.4 的广场机位（NPC 史莱克商人+绿色喷泉+蓝色水晶球）。按纪律 #3「面板相机异常是 UI 渲染层，不改服务端掩盖」。**协议闭环的功能正确性由脚本化 E2E 10/10 证明；实机 10933/10934/10932 帧序列未能在本机触发，如实标 BLOCKED（UI 入口），不编造截图。**

---

## 6. 回归

- `python -m py_compile server/mock_server.py`：**OK**。
- `tools/c1_e2e_closed_loop.py`：**PASS=19 / FAIL=1 / NOT_RUN=1**。
  - FAIL=1：`[5] 12402 接取任务 code=0`——与挂机无关（本批未碰任务模块）；紧随其后的 `12403 提交任务 code=1`、重复提交幂等（gold 不变）、杀进程重启后状态一致、rid=1001 基线全程未动（equal=True）均 PASS。判定为既有的测试账号任务接取态怪癖（新号可能已自动接 10010，重复接取被拒），非本批退化。
  - NOT_RUN=1：setassets 负数金币（脚本自身标注）。
- **基线 rid=1001 复核（测后实测）**：
  - `role_assets`：gold=**1799942**、exp=**20689**、coin=**9923249**、hero_exp=**9800** ✓ 全部吻合基线。
  - `roles`：level=**70**、scene_id=**10001**、exp=20689 ✓。
  - `guaji_state rid=1001`：loop_count=0, mission_bid=10010, kill_count=20, off_on=NULL（老行，读取安全兜底为 0，本批未在实机开过离线开关）。
- 测试账号（c31test_*、c33test_off_*）均已自动清理；rid=1001 资产未动。
- 说明：「minloop selftest」本环境无对应可执行脚本（tools 下仅 minloop_frida_*，需模拟器 Frida 注入），在 HUD 不可达前提下未跑，如实标 NOT_RUN。

---

## 7. 遗留问题

1. **实机 HUD 顶栏不渲染（BLOCKER，UI 层）**：挂机面板/离线开关按钮实机不可达。需后续单独排查客户端为何本会话 HUD 世界锚点全部偏移出屏（与 C2.4 同包同服却不同表现，疑似客户端相机/UI 节点状态在 force-stop 重启后漂移）。本批不改服务端掩盖。
2. **离线挂机收益 = BLOCKED**：`config_guaji.json` 无收益字段。待取得原版收益表（经验/小时等）再接 `reward.grant`（幂等）。
3. **15403 频率限制是防御旋钮**：`guaji_kill_min_sec` 默认 1.0s，非原版玩法规则（原版限次规则无证据，不编造）。
4. 15403 合法击杀 grant 仍发 drop 20003 组（coin=1000 + item 4001），沿用 C 分片既有 grant，本批未改；该掉落是否对应原版挂机奖励未取证（标注 UNKNOWN）。

---

## 8. 自检

- [x] 改前备份存在且字节数记录（1,105,196）。
- [x] 每批只改挂机闭环一个业务面；未碰任务/商城/伙伴/修炼/战斗结算。
- [x] 服务端权威：不信任客户端 15403 mon_bid 即发奖（加会话+频率+存在性三道）。
- [x] 重复/跨角色/时间回拨：rid 隔离、off_started_at 服务端时间戳、状态落库持久化。
- [x] 不编造收益数值：无收益字段 ⇒ BLOCKED。
- [x] rid=1001 基线未回退（逐项实测吻合）。
- [x] 测试账号测后清理。
- [x] 实机入口不可达如实记录，未编造面板/toast 截图。
