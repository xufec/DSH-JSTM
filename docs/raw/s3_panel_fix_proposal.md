# S3-A 任务5：自动弹出面板首帧战力=0 —— 客户端方案评估（只出方案，不实施）

> 阶段：PHASE S3-A 第五分片（纯方案文档）
> 日期：2026-10-15（周四）
> 范围：基于 C3.1-B 证据（`docs_raw/c3_1_protocol_verify.md` §3）给出最小改动方案；**本阶段不实施客户端修改**，待批准。
> 纪律：不改客户端、不改服务端帧；只列选项 / 改动点 / 风险 / 回归影响 / 推荐。

---

## §1 问题复证（一句话根因）

冷启动自动弹出的角色面板，其「综合战力」标签定格在 **0**，直到玩家手动关闭重开才显示真实值 724112。

- HUD（直读共享 vo）正确 = 724112；同屏面板却 = 0（实机 n01/n02 vs n10）。
- 服务端已无可补的帧：10303（204B，含 power）/10306（88B，含 power）都在 S1 补推里带了正确 power=724112。
- 根因在客户端两处（证据等级 A=反汇编直读）：
  1. **面板 setData 是一次性快照**（`_display_panel_dis.txt` proto#10：`power_value:setString(vo.power)`，打开时取一次就写标签）。
  2. **面板活刷新门控对自我角色恒不通过**（proto#15 hero_attr_event：`if self.is_role and self.role_vo.bid == event.bid then power_value:setString(event.power)`；自我 RoleVo 无 bid 字段 ⇒ bid==event.bid 永假 ⇒ 已开面板永不刷新 power 标签）。
- 自动弹出时机：冷启动 pre-role-state 为空 ⇒ 10301 `initRoleBaseData` 后 `NavCtrl:openView()` 自动弹面板；此时 vo.power 仍=0（预入场 10303 是否写进 vo 属 UNKNOWN U1）。

---

## §2 候选方案

> 所有「彻底修复」都落在客户端 .luac；服务端已无新帧可发。下列 A/B/C 为客户端改法，D 为纯服务端（只能缓解、不能根治）。

### 方案 A（推荐）：放宽自我面板的活刷新 bid 门控

- **改动点**：客户端 `display_panel.luac` proto#15（hero_attr_event 监听）。
  把
  ```lua
  if self.is_role and self.role_vo.bid == event.bid then
      power_value:setString(event.power)
  end
  ```
  改为：当 `self.is_role` 为真时，**不要求 bid 相等**，直接 `power_value:setString(event.power)`（自我面板没有 bid，本就该无条件跟随 vo）。
- **效果**：S1 补推 10306/10303（power=724112）到达后，已打开的面板 power 标签**就地刷新**为 724112，无需手动重开。
- **风险**：低。只影响「自我角色面板」这一条事件分支；英雄/伙伴面板（is_role=false）仍走 bid 门控，不受影响。
- **回归影响**：① 面板打开期间任何 attr 变化（升级/换装）都会即时刷 power——这正是期望行为；② 需确认 HERO_ATTR_CHANGE 事件确实携带 self 的 power（10306 已带 power，事件由 10306 触发 ⇒ 携带）。
- **评级**：风险低 / 收益直接 / 改动最小（单行门控放宽）。

### 方案 B：面板打开时机延后到 vo.power 就绪

- **改动点**：客户端 `role_data.luac` proto#11（rgp_hander10301）里 `NavCtrl:openView()` 自动弹窗的判定。
  在 `if not getPreRoleState() or not isSameRoleData(...)` 后加一道：**vo.power > 0 再 openView**；否则由后续 10306（带 power）就绪事件再触发 openView。
- **效果**：冷启动不再「先弹一个 0 面板」，等 vo 有真实 power 才弹。
- **风险**：中。① 若 10306 永远不到（心跳被屏蔽），面板永不自动弹——需兜底超时；② 改了自动弹窗触发链，可能影响「切号必弹/同号不弹」的既有概率行为（R3）；③ 与 50 级礼包等叠加弹窗的时序需重排。
- **回归影响**：自动弹出面板的首帧行为整体改变；需回归冷启动/切号/重登三种入口。

### 方案 C：setData 改订阅而非快照

- **改动点**：客户端 `display_panel.luac` proto#10 setData 不再 `setString(vo.power)` 定格，而是注册一个对 vo 的弱引用刷新（每次 onEnter / 每次 attr 事件重读 vo.power）。
- **效果**：彻底根治「快照定格」类问题（不只 power，其他 vo 字段也受益）。
- **风险**：中高。改动面大于 A；要处理面板关闭时反注册，避免泄漏；与既有 proto#15 监听可能重复刷新。
- **回归影响**：面板所有数值标签的刷新时机都变，回归面最大。

### 方案 D：服务端把 S1 补推提前到 10301 应答后立即发（不能根治，仅缓解）

- **改动点**：服务端 `mock_server.py` 10301 handler 应答后，不等心跳 +5s，立即排程/直推一次 10306。
- **效果**：**不能根治**。面板在 10301 body 处理的同一毫秒已 openView 并快照 power=0；紧随其后的 10306 只会更新 vo（HUD 对），面板标签仍定格（门控问题不变）。
- **结论**：仅当配合 A/B/C 时才作为时序优化，单独做无意义。**不推荐单独实施。**

---

## §3 推荐与风险评级

| 方案 | 改动位置 | 根治? | 风险 | 回归面 | 评级 |
|---|---|---|---|---|---|
| **A 放宽自我面板 bid 门控** | display_panel.luac proto#15 一行 | ✅ | 低 | 小（仅自我 power 标签） | **推荐** |
| B 延后 openView 到 power 就绪 | role_data.luac proto#11 | ✅ | 中 | 中（弹窗时序） | 备选 |
| C setData 改订阅 | display_panel.luac proto#10 | ✅（顺带） | 中高 | 大 | 不推荐（过度） |
| D 服务端提前补推 | mock_server 10301 handler | ❌ 不根治 | 低 | — | 不推荐单独做 |

**推荐：方案 A。** 理由：
1. 它直接命中根因之一（活刷新门控对自我角色恒不通过），单行改动、风险最低；
2. 不改变自动弹窗时机（B 的概率性行为不动），不扩大回归面；
3. 服务端 D 已无可补帧，A 让既有的 10306 补推真正「被面板消费」，形成闭环。

---

## §4 前置取证（实施 A 前需补的 UNKNOWN）

- **U1**（来自 C3.1-B §3.3）：预入场 SC_10303（22:35:34）是否真把 power 写进了共享 vo？若写进了，A 方案下 S1 补推 10306 的事件一定会刷新面板；若没写进（被 getData() 判空跳过），需确认 S1 补推的 10306 是否一定触发 HERO_ATTR_CHANGE。
  - 所需证据：observer 注入 dump RoleData.role_vo.power 在 22:35:34 / 22:35:36 / 22:35:46 三时刻值。
- **U2**：10306 到达后客户端 dispatch 的事件名是否就是面板 proto#21 注册的 `HERO_ATTR_CHANGE`（proto#15 的监听源）。若是，A 直接生效；若否，需对齐事件名。

---

## §5 本阶段边界

- 本文档**不实施**任何客户端 .luac 修改；服务端 S3-A 其余任务（双路收敛/admin 校验与审计/发奖幂等/商城映射）不依赖本方案。
- 待用户批准方案 A 并补齐 U1/U2 证据后，再在 S3-B（实机验证分片）落地客户端补丁。
