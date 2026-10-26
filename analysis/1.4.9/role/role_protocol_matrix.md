# 角色协议矩阵（Phase 4A 审计产物）

> APK：`anzbao/jstm.apk`（**1.4.9** / `com.shiyue.dldl.ewan.qihoo`）
> 状态列**只使用**：已确认 / 已实现 / 已验证 / 待分析 / 未知
> 依据：`role_ctrl.luac` 的 `RegisterProtocal` 映射 + `protocol/manual.md` 字段 + 实机 TCP 日志。

| 功能 | CMD | 请求字段 | 响应字段 | 客户端位置 | 服务端 | 状态 |
|---|---|---|---|---|---|---|
| 帐号登录 | 1110 | `args:table(key,val)`（10 项） | `code:u8, msg:string, roles:table(rid,srv_id,name,lev,sex,career,is_online), least_career:u8` | `denglu_ctrl` proto[24]/[23] | `build_1110_roles` | 已验证 |
| 登录指定角色 | 10102 | `rid:u32, srv_id:string` | `code, msg, timestamp:u32, world_lev:u16` | `denglu_ctrl` proto[32]/[30] | 已实现 | 已验证 |
| 角色重连 | 10103 | `rid:u32, srv_id:string` | 同 10102 | `denglu_ctrl` proto[34]/[33] | 已实现 | 已验证 |
| 创建角色 | 10101 | `sex, name, career, playform` | `code, msg, rid, srv_id` | `denglu_ctrl` proto[27] | 未实现 | 待分析 |
| 客户端初始化完毕 | 10300 | 空 | （无 SC） | `denglu_ctrl` 注册表 | 收包只记录 | 已确认 |
| **角色基础信息** | **10301** | 空 | 45+ 字段（见 `role_protocol.md` 2.1） | **`role_ctrl` → `rgp_hander10301`** | `build_10301`（最小结构） | **已验证** |
| **角色资产/经验** | **10302** | 空 | `lev:u16, exp:u32, gold:u32, gold_acc:u32` | **`role_ctrl` → `rgp_hander10302`** | **未实现** | **已确认** |
| **角色属性** | **10303** | 空 | 大表（含 `attr` 24 项 + 资产 14 项 + `skill_list`） | **`role_ctrl` → `rgp_hander10303`** | **未实现** | **已确认** |
| 查看指定角色 | 10304 | `rid:u32, srv_id:string` | `rid, srv_id, name, lev, …` | `role_ctrl` → `rgp_hander10304` | 未实现 | 已确认 |
| 角色（续） | 10305 | 未确认 | 未确认 | `role_ctrl` → `rgp_hander10305` | 未实现 | 待分析 |
| 角色（续） | 10306 | 未确认 | 未确认 | `role_ctrl` → `rgp_hander10306` | 未实现 | 待分析 |
| 角色 ack | 10333 | 空 | `code:u8, msg:string` | 已请求（`role_ctrl` 家族） | **未实现** | **已确认（客户端已请求、无应答）** |
| **角色技能/世界等级** | **10621** | 空 | `world_lev:u16, skill_list:table(bid:u32, exp:u32)` | 已请求 | **未实现** | **已确认（客户端已请求、无应答）** |
| 角色移动 | 10204 | `x:u16, y:u16` | `rid:u32, srv_id:string, x:u16, y:u16` | `scene_controller` proto[37]/[14] | 已实现 + 落盘 | 已验证 |
| 角色瞬移 | 10205 | `x:u16, y:u16` | 同 10204 | `scene_controller` | 已实现 | 已实现 |
| 角色保存 | — | 无独立协议 | 由 10204 落盘实现 | — | `save_role_pos()` | 已验证 |
| 进入场景 | 10200 | — | `code, msg, bid:u32, line_id:u8, x:u16, y:u16, dir:u8` | `scene_controller` proto[68] 侧 | `_send_10200` | 已验证 |
| 场景图块 | 10201 | 空 | `roles/npcs/mons/elems` | `scene_controller` proto[36]/[9] | `build_10201`（25 NPC） | 已验证 |
| 角色属性扩展 | 10320/10321/10324/10328 | 未确认 | 未确认 | `role_ctrl` | 未实现 | 待分析 |
| 角色扩展 | 10342/10343/10391 | 未确认 | 未确认 | `role_ctrl` | 未实现 | 待分析 |
| 角色扩展 | 10947–10958 | 未确认 | 未确认 | `role_ctrl` | 未实现 | 待分析 |
| 角色扩展 | 18900–18911 | 18900 已请求 | 18900 已实现 | `role_ctrl` | 部分实现 | 已实现（18900） |

---

## 补充：本阶段**未**纳入的功能（按 Phase 4 禁止清单）

任务系统（124xx，其中 `12400` 已实现推送、`12403` 客户端已请求但未回）、
战斗、副本、伙伴、装备、魂环、翅膀、商城、充值、PVP、宗门、好友、排行榜、聊天。

---

**[WAITING FOR PHASE 4B]**
