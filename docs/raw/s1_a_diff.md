# S1-A 第一分片改动 diff 记录

- 日期：2026-10-15
- 文件：`server/mock_server.py`
- 备份：`server/mock_server.py.bak_20261015_1908`（1,087,247 bytes，与原文件一致）

## 改动 1：10300 handler 中排程 S1 补推

- 位置：原行 17361–17363 → 新行 17417–17422
- 上下文：10300 (CSRoleInit) handler 末尾，`_mis_repush_at` 排程之后、`return` 之前
- 原因：在客户端初始化完毕后，排程 5 秒后触发补推（由 1199 心跳驱动）
- 新增内容（5 行）：
  ```python
  # ★ S1 第一分片：登录风暴收尾补推（F1 战力归零 + 日常活力）
  #   C2.2/C2.3 诊断：10301 重建 RoleVo 后 power=0，面板自动弹出定格 0；
  #   日常 tab 从不发 CS_13781/13786。修法：心跳驱动延迟补推。
  self._login_repush_at = time.time() + 5.0
  log('tcp.log', '  .. S1 风暴收尾补推已排程（+5s，10303/10306/13781/13786）')
  ```

## 改动 2：1199 心跳 handler 中执行 S1 补推

- 位置：原行 9940 → 新行 9941–9994
- 上下文：1199 (心跳) handler 中，12400 补推块之后、15402 补推块之前
- 原因：心跳是"客户端已稳定"的最好信号（复用既有 `_mis_repush_at` / `_guaji_15402_at` 模式）；延迟 5s 确保 10301 重建 vo + 面板弹出快照完成后再补推
- 新增内容（约 54 行）：
  - 10303：复用 `build_10303(role_state, skills, attr)`，power 由 `build_10303` 内部经 `role_power` 真实计算（非硬编码）
  - 10306：复用 `attr_table_10306(ad)` + `w_u16(mspd)` + `w_u32(power)`，与 `attribute/handler.py` handle_10306 同构
  - 13781：复用 `db_daily_get` + `richang_daily_tasks` + `db_daily_lingqu`，与 CS_13781 handler 同构
  - 13786：复用 `richang_daily_tasks` + `db_daily_get`，与 CS_13786 handler 同构
  - 整体 try/except 包裹，失败仅记日志不崩溃

## 未改动
- 既有 `build_10303` / `build_10301` / `build_10302` / `build_10305` 函数体
- 既有 `_mis_repush_at` / `_guaji_15402_at` 逻辑
- 客户端 APK（未 install/repack）
- 配置文件 config.json
