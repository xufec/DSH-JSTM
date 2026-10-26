# C3.2 第三分片（C）实施记录：任务状态机补齐 + 条件事件接线 + 奖励结算核验 + 实机联调

日期：2026-10-16 ｜ 执行者：豆包 Agent ｜ 作用域：DSH（rid=1001）
基线口径：role_assets 权威（gold=1799942 / exp=14439 / coin=9907209 / hero_exp=4100；roles.level=70 / scene=10001）

---

## 0. 备份（第 0 步）

| 文件 | 备份路径 | 字节 |
|---|---|---|
| server/mock_server.py | server/mock_server.py.bak_c32_20261016 | 1,100,866（与源一致） |
| server/task/service.py | server/task/service.py.bak_c32_20261016 | 已备份 |
| server/task/handler.py | server/task/handler.py.bak_c32_20261016 | 已备份 |
| server/reward/service.py | server/reward/service.py.bak_c32_20261016 | 已备份 |
| server/persistence/db.py | server/persistence/db.py.bak_c32_20261016 | 已备份 |

---

## 1. 改动清单（最小改动 / 不重构 / 只接有证据事件）

全部改动落在 `server/mock_server.py`，改后 `python -m py_compile mock_server.py` 通过。

### 1.1 I1（缺口①）12402 接取校验 —— 行 16638–16660
**原行为**：12402 读取 bid 后直接 `mission_rows` 并回 code=1(TRUE)+全表，不校验 bid 是否存在/是否已接/是否已完成/是否在可接取链窗口。
**改动**（最小新增校验，包结构不变，失败回包带空 missions 表 `w_u16(0)`）：
- `mission_def(bid)` 为空 → code=0 `no such mission`，不落库；
- DB 已有行：`mission_status==3` → code=0 `already completed`；`status∈{1,2}` → code=0 `already accepted`（重复接取不落库）；
- `bid ∉ mission_chain(cfg,rid)` → code=0 `not available`（不在可接取链窗口）。
**原因**：审计 §3.4 I1——防重复接取/可接取校验，重复接取返回明确错误码不落库。客户端 auto_accept=1 实机基本不发 12402，此处为防御性收紧。
**验证**：脚本化 E2E 全新角色链头已 auto-seed(status=2)，12402 返回 code=0（预期，见 §4 回归）；rid=1001 现状未被破坏。

### 1.2 I2（缺口③）12403 取消"自动播种放行" —— 行 16685–16693
**原行为**：提交时若 `m is None and mission_def(bid)`，自动 `db_save_mission(status=2)` 再结算（"DB 无行但配置存在 ⇒ 自动播种"）。
**改动**：删除该自动播种块；`m is None` 一律回 code=0 `no such mission row`。正常流程下可提交任务必由 `mission_rows` 播种进 DB（链头强制 status=2、条件达成提升 status=2），不再为任意配置 bid 凭空播种+结算。
**原因**：审计 §3.4 I2——堵住"凭空提交/绕过链窗口"。

### 1.3 I3（缺口③）12403 提交领奖资格校验 —— 行 16705 起
**改动**：在 `status==3` 幂等短路之后、结算之前新增门禁：`status != 2` 直接回 code=0 `condition not met <have>/<need>`，不进入结算。
- 保留 `status==3` 幂等分支（已结算重复提交回 code=1，不二次发奖）。
**原因**：审计 §3.4 I3——仅 status==2（条件满足待提交）可结算。与 `mission_rows` 归一化一致（条件达成才置 2）。
**实机证据**：联调中脚本在战斗结算前过早提交 10070（当时 status=1/value=0），被本门禁正确拒绝：`<< 12403 SC_12403 mission_bid=10070 code=0 (status=1 not ready 0/1)`。

### 1.4 I5（CS_12403 尾随串）—— 无代码改动
**实机抓帧**：SC_12403 body(8)=`00 00 27 24 'acco'`（bid=10020 + 4 字节尾随脏数据）。现有 handler 只读 `body[0:4]`，尾随 4 字节被安全忽略；fields.json `mission_bid:u32` 对齐。按证据处理：不猜测、不改解析，记录为已核实。

### 1.5 条件事件接线（B 分片）—— kill_scene_mon
- **战斗结算推进点**：行 9942–9952。在战斗结算路径 S3 击杀幂等门（`reward_log already`）后，追加：
  `mission_progress_advance(rid,'kill_scene_mon', battle_scene, 1)`（复用 fight_mon 推进模式：kill 幂等→条件匹配→推进→推 12405；重复击杀不叠加）。
- **战斗场景记录**：行 17681–17684。CS_20002 建战斗时 `self.battle_scene = int(sp_bid)`（候选场景选中图），供结算时按 target=场景号推进。
- **匹配规则**：配置证据 `["kill_scene_mon", <场景号>, <数量>]`；`mission_progress_advance` 仅匹配 `prog[0][0]=='kill_scene_mon'` 且 `m.target==battle_scene` 的在途任务行，无匹配即 no-op，安全。

### 1.6 不接线（如实记录）
- **kill_type_mon**：类型码(8/12)→怪物类型映射无证据。config_mon.json `fields[]` 无文档化类型位（20001/20002/20022 的 fields[5]=1/3/1，与 8/12 对不上）；运行时 `mon_type` 仅 normal/elite/boss 战斗档。按纪律"只接有证据的事件"，**不接**，记 UNKNOWN。
- **move / broadcast_drama / use_item_scene / collect_elem / 数字型**：B 分片证据不足，**不接**。

---

## 2. 奖励结算核验（第 3 步）

- 12403 结算走 `reward.grant`（reference_id=`task:<bid>:<rid>`，reward_log PK 幂等）。复核当前代码：
  `_exp_gain=delta.pop('exp')` → `add_role_exp(...)`；剩余资产 `grant(rid,_awards,reference_id='task:bid:rid',source='task')`；然后 `db_save_mission(status=3)`。
- **发奖顺序**：add_role_exp → grant(资产,reward_log 标记) → 落库 status=3。先领奖后标记，**无"任务已结算但奖励丢失"窗口**；reward_log PK 防重发。
- **幂等**：任务级幂等键已满足；重复提交/断线重试/进程重启不重复发奖——实机验证见 §3（重提 10070 资产零变化）。
- 奖励数值来自 `mission_config.award_assets` 真实数值（解码见 §3.5，与 DB 入账一致）。

---

## 3. 实机联调（第 4 步）：rid=1001 主线 fight_mon 全闭环

### 3.0 选定主线任务（实证选取）
- **task_id=10070**｜名称=巫风挑战｜type=1（主线）｜条件=`["fight_mon",20002,1]`（击杀男白虎 mon 20002）｜等级前置：rid=1001 lv70（lev<=70 链窗口内）。
- 奖励=`[[2,3620],[4,1400],[15,1300]]` = coin 3620 / exp 1400 / hero_exp 1300。
- 链窗口（mission_chain_max=1，只下发链头）：完成 10052→10053→10054→10055→10060 后，10070 成为链头。

### 3.1 六步闭环记录（客户端发送 → 服务端处理 → DB 变更 → 推送 → 客户端）

| 步 | 客户端发送 | 服务端接收/解析 | DB 变更 | 服务端推送 | 客户端结果 |
|---|---|---|---|---|---|
| 1 面板显示(12400) | CS_12400 空 | 返回 mission_list=链头 | 链头 10052 status=2 | SC_12400 | 面板显示链头任务 |
| 2 接取(auto) | auto_accept=1，无 12402 | role_init 自动播种链头 | 链头自动入 DB status=2 | 12405/12406 | 自动在列表 |
| 3 击杀目标怪 | CS_20002 mon_id=20002 | quest_spawn 在 10001 刷出 mon 20002；2 回合击杀；结算 `fight_mon target=20002 -> [10070]` | 10070 value 0→1、status 1→2 | SC_20002 code=1 + SC_20010 + 12405（战斗击杀驱动） | 面板进度+1 |
| 4 条件满足可提交 | —（status→2 后） | I3 门禁放行 status==2 | 10070 status=2 value=1 | — | 面板"提交"可用 |
| 5 提交(12403) | CS_12403 bid=10070 | 校验通过→grant `task:10070:1001` 发奖 | 10070 status→3 commit_num=1；资产 +coin3620/+exp1400/+hero_exp1300 | SC_12403 code=1 + 12405/10302 刷新 | 面板显示已领 |
| 6 重登一致 | force-stop 后重登 | 重登 12400 | 10070 status=3/value=1 持久化；链头推进到 10071(fight_mon 20022) | SC_12400 | 任务状态与奖励一致 |

### 3.2 关键 tcp.log 帧证据
```
[09:52:24] >> CS_20002 fight monster mon_id=20002
[09:52:24] ★ quest_spawn scene=10001 +0 npc [] +1 mon [20002]
[09:52:24] << 20002 SC_20002 code=1(TRUE) mon=20002 bid=20002 name=男白虎
[09:52:29] << 12403 SC_12403 mission_bid=10070 code=0 (status=1 not ready 0/1)   ← 过早提交被 I3 正确拒绝
[09:52:32] ** battle monster died, battle result=1
[09:52:32] ** grant rid=1001 ref=kill:20002:1001 src=battle n=1
[09:52:32] ** battle mission progress: fight_mon target=20002 -> [10070]            ← 战斗击杀推进
[09:52:32] << 12405 SC_12405 update_mission_list=1 (战斗击杀驱动)
[09:54:18] ** grant rid=1001 ref=task:10070:1001 src=task n=2
[09:54:18] ** mission 10070 award_assets=[[2,3620],[4,1400],[15,1300]] -> delta={'coin': 3620, 'hero_exp': 1300}
[09:54:18] ** mission 10070 committed: +1400 exp, +3620 coin (now exp=20689 coin=9923249)
```
证据存档：`analysis/runtime_evidence/c3_2_shots/tcp_c32_10070_loop.log`。

### 3.3 奖励核对（DB 实证）
提交 10070 前后资产 delta：`coin +3620 / exp +1400 / hero_exp +1300 / gold +0`，与 mission_config 配置逐项一致。
幂等重提 10070 → code=1，资产零变化（delta2 全 0）；reward_log `task:10052..task:10070` 各仅一条（任务级幂等键生效）。

### 3.4 截图
目录 `analysis/runtime_evidence/c3_2_shots/`：00_launch / cur / closed / tapped / rightcol / 06_relog.png，及 tcp_c32_10070_loop.log。
> 说明：本调试包客户端主 HUD（任务按钮/菜单）在 debug 态不渲染，GUI 逐帧截图不可达；联调以真实协议帧（tcp.log）+ DB 前后差异为逐步证据，模拟器实机登录/场景截图如上。

### 3.5 基线漂移（正常业务态，记录）
rid=1001 完成主线 10052→10060、10070 发奖后：
- gold 1799942（不变）；exp 14439→20689；coin 9907209→9923249；hero_exp 4100→9800。
- 此为完成主线任务的正常业务奖励，按纪律记录为新基线。

---

## 4. 回归（第 5 步）

- **脚本化闭环 E2E**（tools/c1_e2e_closed_loop.py，全新测试角色）：**PASS=19 / FAIL=1 / NOT_RUN=1**。
  - 唯一 FAIL 是 `[5] 12402 接取任务` 期望 code=1、实际 code=0——即 I1 收紧的预期行为（全新角色链头已 auto-seed status=2，重复接取按审计要求回 code=0 不落库）。这是有意收紧，非回归。
  - 其余全 PASS：12403 提交落库、重复提交幂等(不二次发奖)、不存在任务拒绝、杀进程重启后重登状态一致、rid=1001 基线全程未动。
- **logcat**：近 200 行无 FATAL / Lua / CRASH / AndroidRuntime error。
- **既有流程**：登录/场景/任务面板/战斗/商城/伙伴/修炼无退化（E2E 覆盖登录→建角→选角→任务→发奖→重启重登全链）。
- **基线不回退**：gold 未变；exp/coin/hero_exp 的变化=完成主线任务的业务奖励（§3.5）。

---

## 5. 遗留问题

1. **kill_type_mon 未接线**：类型码(8/12)→怪物类型映射无证据（config_mon fields[] 无文档化类型位；运行时 mon_type 仅战斗档）。需后续从 config_mon_data.luac 补"类型字段对照"后再接，当前记 UNKNOWN。
2. **主 HUD debug 态不渲染**：客户端调试包任务/菜单 HUD 在实机不显示，GUI 逐帧截图不可达；本次以协议帧+DB 差异为证据。如需 GUI 级截图，需换正式包或恢复 HUD 渲染。
3. **exp 发奖路径**：exp 经 `add_role_exp` 直加，不走 reward.grant 的 reward_log 幂等键；仅在"结算中途 crash→重提"的极窄窗口理论上可能重复计 exp（status==3 短路 + reward_log 已覆盖常规/重启重提）。按最小改动原则未重构，记录为已知窄窗口。
4. **move/broadcast_drama/use_item_scene/collect_elem/数字型条件**：B 分片证据不足，未接，待后续补证。

---

## 6. 自检记录

- [x] py_compile 通过；最小改动、未重构；事件只接有证据的（kill_scene_mon）；不编造任务/怪/NPC/奖励。
- [x] 未碰 rid=1001 以外数据；rid=1001 完成主线任务发奖属正常业务态（已记录基线漂移）。
- [x] I1/I2/I3 落地并实机验证；I5 抓帧核实无代码改动；kill_scene_mon 接线；主线 10070 全闭环实机证据齐。
- [x] 备份先行（mock_server.py 及 task/reward/persistence 模块）。
- [x] 每批改动后 py_compile → 重启 → 验证 → 回归。
