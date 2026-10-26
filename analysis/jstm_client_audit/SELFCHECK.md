# PHASE C0 客户端与服务器需求矩阵 — 自检记录

> 只读审计。未修改 mock_server.py / min_loop_server.py / 任何既有文件。

## 交付物（项目路径）
- `C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\client_server_matrix.json`（93,935 B）
- `C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\client_server_matrix.md`（117,399 B）
- `C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\server_capability_needs.md`（52,534 B）
- artifacts 副本：`<agent_workspace>/artifacts/`（同名 3 文件）

## 自检项（脚本 _selfcheck.py 实测）
1. `json.load` 解析 client_server_matrix.json → OK；systems = **124**。
2. system_id 集合与顺序 vs `systems_master.json` → **完全一致**（set equal + order equal）。
3. 每系统 10 字段齐全 → 缺失 0。
4. "已实现"系统中 current_impl 无源码/测试定位者 → **空集（0）**。
5. 状态分布：已实现 **60** / 部分实现 **29** / 未实现 **35**（合计 124）。
6. 证据级分布：CONFIRMED 14 / VERIFIED 70 / STRONG_INFERENCE 14 / INFERENCE 17 / UNKNOWN 9。

## 关键证据锚点（抽样，行号指 server/mock_server.py）
- 登录/角色/属性/资产：:9968(1110) :15929(10101) :17260(10300) :17047(10301) :16098(10303)
- 场景/组队：:15957(10200) :10778 族(13200..)
- 战斗/挂机：:17384(20002) :18736(15400)
- 背包/商城/邮件/拍卖：:19229(10502) :16770(12801) :18236(10800) :12140(18020)
- 成长外观：:14887(11600 翅膀) :15232(19400 命格) :14850(15700 神器) :15297(15501 坐骑) :14807(15801 灵兽) :14840(19406 元神) :13383(10573.. 时装) :13427(19100 光环)
- 社交：:11077(18300 结婚) :10947(19505 结拜) :11854(17519 公会)
- PvP：:17804(11300 竞技) :15528(18803 巅峰) :10545(17306 竞速)
- P2.11 新模块 import 注册：:101 growth.handler(11600) :102 answer.handler(16100..) :103 growth_target.handler(30500..) :104 scratch.handler(16651/2) :105 friend.handler(13300..)

## 与既有清单的偏差（以源码为准，已在矩阵注明）
- 实测 `if cmd==N` 旧链覆盖 **801 个 opcode**，远多于 HANDOFF 所记"注册 19→34"（后者为 `@register` DISPATCH_TABLE 计数；L39 注释：DISPATCH_TABLE 当前为空，全部走旧 if 链）。
- PHASE0 unimplemented 清单中的 **答题(16100..)/刮刮乐(16651/2)/成长目标(30500..)/好友(13300..)** 在 PHASE2.11 已由 `server/answer|scratch|growth_target|friend/` 模块实现（:102-105 import 注册为证），矩阵按"已实现"计并注明与清单的差异。

## 未确认项（UNKNOWN 证据级，9 项）
SYS_GROWTH_006 魂骨、SYS_GROWTH_007 增幅、SYS_CORE_008 红点、SYS_CORE_009 UI状态、SYS_UNKNOWN_001 丹药战、SYS_UNKNOWN_002 运营活动、SYS_UNKNOWN_004 染色、SYS_EQUIP_005 装备洗练、SYS_FRIEND_006 伙伴培养消耗。
（另有 17 项 INFERENCE，多为"表已持久化但无独立 CS 命令"或"数值待 MuMu 标定"。）

## 方法学说明
- 大文件纪律：mock_server.py(1.08MB/19390行)、proto_defs.py(666KB) 仅用 Grep/python 定位，未整体读入上下文。
- "当前已实现部分"逐系统标注 `mock_server.py:<行号>` 或 `server/<模块>/` 或回归测试名；未核验处标 UNKNOWN。
