# round45 — 综合战力闭环 + 镇魂塔 CengList

日期：2026-09-19
基线：round44（副本/爬塔骨架 + 13036 止血）

## 本轮两件事

### ① 综合战力闭环（HANDOVER P0-1）

**问题**：变强/综合战力面板读 `RoleVo.power[1].val`，但运行时探针证明"从无消息写入该字段"——面板一直空。

**取证**：grep fields.json 全部 SC 消息里含 `power` 的，锁定
- `SC_10306 = {attr表(24项), mspd:u16, power:u32}`，`CS_10306` 空消息。
- 语义：客户端发空包**主动请求"同步我的属性"**，服务端回 attr+mspd+power；这正是把 power 写进 `RoleVo.power` 的那条消息。
- 此前 mock_server.py grep `10306` **0 命中**——完全没实现，客户端请求了也没人回，故 `RoleVo.power` 永不写入。

**实现**：新增 10306 handler（插在 10304 前）：
- attr 表与 10304 同源：`u16(1)` 计数 + ATTR_KEYS[:4] 各 u16 + ATTR_KEYS[4:] 各 u32
- `mspd:u16` + `power:u32 = role_power(cfg)`
- 共 96 字节。

补丁：`server/_fix_round45_10306.py`

### ② 13034 CengList 从空表改为非空

**取证**：反汇编 `demontower_view.luac`（22KB）proto#25：
- UI 每层一个 item，`item.level == ceng` 时调 `setPassed(count, is_get状态, can_get状态)`。
- 字段真实含义：
  - `ceng`(u8) = 层号
  - `count`(u16) = 该层进度/通关次数
  - `is_get`(u8) = 0 可领 / 非0 已领
  - `can_get`(u8) = 0 可领 / 非0 不可领
- strings(32) 确认该塔客户端内叫 **"传灵塔"/"镇魂塔"**（用户纠正对了，不是封魔塔）。
- 注：客户端请求的 `dung_bid=40001` 不在任何已导出配置表（config_dungeon_tower 48 条 key 为 18201/10201 等），其真实层数结构待镇魂塔玩法阶段再取证。

**实现**：CengList 从 `w_u16(0)`（空表）改为 3 条占位：
`(ceng=1,count=0,can_get=0,is_get=0) × 3`，让章节奖励页不再空白；真实进度随玩法同步。
顺手把 13036 注释与日志里的"封魔塔"更正为"镇魂塔"。

补丁：`server/_fix_round45_13034.py`

## 验证

四道审计全绿：
1. `audit_specs_vs_fields.py` → 2463/0
2. `audit_sc_conformance.py` → 1619 一致 / 16 空
3. `audit_sc_conformance.py --generic --unsupported` → 93 一致 / 1 空（94 通用集合）
4. `audit_sc_live.py --unsupported` → 94/94

服务端已重启（PID 35396）。

## 待办

- 10306 真机验收：进变强/综合战力面板应看到数值（不再 0/空）。
- 13034 真机验收：镇魂塔章节奖励页应列出前 3 层。
- 40001 塔真实层数结构待镇魂塔玩法阶段取证。
