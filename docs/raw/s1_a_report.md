# S1-A 第一分片实施报告：服务端补推链路修复

- 日期：2026-10-15
- 环境：MuMu emulator-5554，2560×1440 横屏；客户端 com.shiyue.dldl.ewan.baidu2（原包不动）
- mock_server：server/mock_server.py，TCP 9000 + HTTP 8080
- 备份：`server/mock_server.py.bak_20261015_1908`（1,087,247 bytes，与原文件一致）

---

## 0. 结论速览

| 项 | 状态 | 证据 |
|---|---|---|
| F1 战力归零 | ✅ 修复 | 角色面板综合战力=724112（非 0），重开仍 724112 |
| 日常活力 | ✅ 修复 | 日常面板活跃度=10/2000（非 ?????/?????） |
| 回归基线 | ✅ 未回退 | HUD power=724112, gold=1,800,140, level=70 |
| logcat FATAL | ✅ 无 | 无 FATAL/Crash |

---

## 1. 项1 F1 战力归零

### 根因（C2.2 诊断确认）
登录风暴中 SC_10301（initRoleBaseData 重建 RoleVo，无 power 字段）晚于 SC_10303 到达；客户端角色面板在风暴中途对过渡态 vo 一次性快照定格 power=0 且不重渲染。

### 定位行号
- 10300 (CSRoleInit) handler：原 L17260（客户端说"我初始化完了"）
- 既有 10200 重推模式：L17273–17276（`repush_10200_on_init`）
- 1199 心跳 handler 中延迟任务驱动：L9928–9940（`_mis_repush_at` 模式）
- power 计算入口：`attribute.service.role_power(cfg)` → `power_mod.calc_power(attr)`
- build_10303：`role/storage.py:187`（内部 L222–226 经 `_role_power` 计算 power）
- 10306 编码：`attribute.service.attr_table_10306(ad)`（L188 注释：4×u16 + 12×u32 + 4×u16 + 4×u32）

### 改动内容
1. **L17417–17421**：10300 handler 末尾排程 `self._login_repush_at = time.time() + 5.0`
2. **L9941–9994**：1199 心跳 handler 中检查 `_login_repush_at` 到期后推送：
   - SC_10303（204 bytes，含真实 power=724112）
   - SC_10306（88 bytes，attr 表 + mspd=100 + power=724112）

### 验证结果
- tcp.log 证据：
  ```
  [19:27:57]   .. S1 风暴收尾补推已排程（+5s，10303/10306/13781/13786）
  [19:28:12]   << 10303 SC_10303 attr（S1 风暴收尾补推）(204 bytes)
  [19:28:12]   << 10306 SC_10306 mspd=100 power=724112（S1 风暴收尾补推）(88 bytes)
  ```
- 截图：
  - `02_f1_charpanel.png`：角色面板综合战力=724112，6 装备格真实图标，完整基础属性
  - `03_f1_charpanel_reopen.png`：关闭重开仍 724112
- 首帧面板未自动弹出（本次冷启动面板未自动弹出，手动点头像打开）；打开即 724112

---

## 2. 项2 日常活力

### 根因（C2.3 诊断确认）
客户端日常面板从不发 CS_13781/13786（tab 打开不发请求）；服务端 handler 已就绪无请求可应。

### 定位行号
- CS_13781 handler：mock_server.py L18832–18861
- CS_13786 handler：mock_server.py L18862–18892
- 数据来源：`db_daily_get(rid)` + `richang_daily_tasks()` + `db_daily_lingqu(rid)`

### 改动内容
- 同一项1 的延迟补推块（L9964–9992）：推送 SC_13781（total_val=10, huoli_list 来自 DB）+ SC_13786（richang_list=24 条）
- 活力值 total_val=10 来自 DB 真实任务进度求和（非硬编码）

### 验证结果
- tcp.log 证据：
  ```
  [19:28:12]   << 13781 SC_13781 total_val=10（S1 风暴收尾补推）
  [19:28:12]   << 13786 SC_13786 richang=24（S1 风暴收尾补推）
  ```
- 截图：`12_daily_full2.png`：日常面板活跃度=10/2000（非 ?????/?????），进度条可见
- 打开方式：HUD 任务按钮 (2120,360) → 左 rail "日常"

---

## 3. 回归结论

| 指标 | 基线 | 实测 | 结论 |
|---|---|---|---|
| power | 724112 | 724112 (HUD + 面板) | ✅ |
| gold | 1,800,140 | 1,800,140 | ✅ |
| level | 70 | 70 | ✅ |
| coin | 9,904,629 | 9,907,209 | 微漂移 (+2,580，前序会话累计，非本次改动) |
| scene | 10001 | 10001 | ✅ |
| exp | 14389 | 14389 | ✅ |
| logcat FATAL | — | 无 | ✅ |

---

## 4. 遗留问题

1. **面板自动弹出时机**：本次冷启动角色面板未自动弹出（C2.2 记录的 f07 自动弹出未复现）；手动打开即 724112，补推已生效。
2. **coin 微漂移**：9,907,209 vs 基线 9,904,629（+2,580），来自前序会话的怪物掉落/任务奖励，非本次改动引入。
3. **11215 伙伴列表 Lua 报错**（C2.3 新发现）：本次未触及，留待下阶段。
4. **延迟 5s 的选择**：基于 tcp.log 风暴在 ~3s 内完成，5s 余量确保 10301 重建 + 面板快照完成；如未来风暴变长可调整。

---

## 5. 自检记录

- [x] 备份存在：`server/mock_server.py.bak_20261015_1908`（1,087,247 bytes）
- [x] py_compile 通过
- [x] 最小改动：仅 2 处插入，未重构既有逻辑
- [x] 数值真实：power 经 `role_power()` 计算；活力来自 `db_daily_get`
- [x] 不伪造：两项均实机验证，截图落盘
- [x] 客户端零改动：未 install/repack
