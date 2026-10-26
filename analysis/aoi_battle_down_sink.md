# AOI / 20002 族下沉可行性评估（任务3，只读，不动代码）

> 日期：2026-10-02 04:45 UTC+8。承接 persistence_down_sink.md。
> 范围：10204 移动 + AOI 邻居闭包/任务替身；20002 战斗链 Timer 异步回调族。

## 1. 依赖图（传递依赖）

### 1.1 AOI / 10204 移动族
- 入口：`if cmd == 10204`（mock_server _reply，移动落库）。
- 传递依赖：
  - `role_state(cfg)` → role.storage（已下沉）✓
  - 落库坐标：db_save_role（role.storage，已下沉）✓
  - **AOI 邻居闭包**：遍历 LIVE_CONNECTIONS / SessionRegistry，对邻居 sendall SC_10201/10212 帧；闭包捕获 `self.request`、当前 rid、场景状态。
  - **任务替身**：移动时顺手推进任务进度（fight_mon / reach_npc）→ 调 db_save_mission / mission_rows（已下沉）。
- **阻塞点**：AOI 广播闭包直接 `self.request.sendall` + 遍历全局 LIVE_CONNECTIONS，与 SessionRegistry 投递模型耦合；闭包内还内联拼邻居帧（pack_frame 串）。

### 1.2 20002 战斗链族
- 入口：20002 开战 → 20010 → 20012/20013×N → 20020 → 20023 → 20021。
- 传递依赖：
  - battle.py（battle_service）数值计算（P5 已接 JSTM 模型）。
  - **threading.Timer 异步回调**：tick/settle 在 timer 线程里产出 SC 字节，再 push_to_rid 投递。
  - 击杀奖励：20023 → reward.grant（P45-C 已接）✓。
- **阻塞点**：Timer 回调持有战斗上下文（mon hp、回合序列、rid），帧拼装散落在回调内；与 SessionRegistry.push_to_rid 的边界需逐函数核对（design 风险5：timer 不直接碰 socket）。

## 2. 字节锚点
- 10204：移动后邻居推送 SC_10201/10212 帧（坐标字段）；改前/改后抓邻居帧对比。
- 20002：战斗链帧序列 20002→20010→20012/20013×4→20020→20023→20021（key_frames.md）。

## 3. 下沉步骤（解锁后）
1. AOI：先把邻居帧拼装抽成纯函数（入参=邻居 rid + 坐标，出参=bytes），再把闭包改为调 SessionRegistry.push_to_rid。
2. 20002：把 Timer 回调内的帧拼装抽成 builder 函数（出参 bytes），回调只负责调 push_to_rid。
3. 逐命令注册：10204 → 20002/20010/... 每步重启+实机字节对比。

## 4. 风险
- Timer 异步：回调在独立线程，帧漂移/时序敏感，逐字节对比难度高。
- self.request 深耦合：AOI 闭包直接 sendall，需先引入 push_to_rid 再拆。
- 帧漂移：邻居数量随场景人数变化，对比需固定同角色单开场景。

## 5. 当前可下沉性结论
**暂不可安全下沉。** 理由：
- AOI 广播闭包仍直接碰 `self.request.sendall` + 全局 LIVE_CONNECTIONS，未先收敛到 SessionRegistry.push_to_rid 投递模型。
- 20002 Timer 回调内帧拼装未抽 builder，异步时序使逐字节对比锚点不稳。
- **解锁前置条件**：① 先把 AOI 邻居推送改走 SessionRegistry.push_to_rid；② 把 20002 Timer 回调内帧拼装抽成纯 builder。两步做完后再按第3节逐命令注册。

---

## 6. 进展更新（2026-10-02 05:10）
- **前置① AOI**：已完成收敛。`_scene_broadcast_10204`（mock_server L680）改为 `for wrid in watchers: push_to_rid(wrid, pkt)`。单客户端 watchers 恒空 ⇒ 广播不触发，邻居帧需第二客户端才能观测。
- **前置② 20002 builder**：**确认 builder 已存在于 battle.py**。Timer 回调（_battle_push_round/_battle_settle）只做 pack_frame+sendall，帧字节全部来自 `bt.play_round()` / `bt.build_20020()` / `bt.build_20023()`（battle.py 内纯 builder）。散落拼装仅剩 `w_u16(0)`（20022）。
- **剩余风险**：Timer 回调仍在独立线程直接 `self.request.sendall`（push_to_rid 等价但未改）。改为 push_to_rid 是异步热路径，单客户端帧时序难逐字节固定，留安全断点。
- **结论**：builder 抽取实质已完成；20002 族注册需把 Timer sendall→push_to_rid 收敛后再做，当前留断点。
