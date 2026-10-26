# miniloop 与参考项目可借鉴能力表（PHASE C0 只读审计）

> 生成日期：2026-10-15 ｜ 性质：**只读审计**，未修改任何既有文件，cankao/ zip 未解压写回，未连第三方服务器。

## 〇、红线（最高优先级）

- 参考项目只能用于架构和实现方式参考。不得将其他游戏的协议、数值、任务、物品或战斗规则直接当作 JSTM 原版数据。
- 本表所有‘可借鉴点’仅指实现机制/架构模式，不指数据内容。
- JSTM 1.4.9 APK(assets/src/config/*.luac、all_proto.luac、真机 tcp.log) 是唯一事实标准；与参考项目冲突时 APK > 参考项目。
- 5 个参考项目代码全部不可复制：survive aoi/astar/wordfilter 内嵌 GPLv3；mahatma 整体 GPL-3.0；其余无 LICENSE(默认保留全部权利)；kongkongxiyou 仅 pomelo/lordofpomelo 骨架为 MIT。

## 一、读法与证据等级

- 状态词：`有` / `部分` / `无` / `UNKNOWN`。
- 证据等级五档：CONFIRMED(本轮直读) / VERIFIED(既有逐文件审计实测) / STRONG_INFERENCE / INFERENCE / UNKNOWN。
- 每格字段：`implementation`(语言/框架/核心类) · `borrowable`(可搬用机制) · `evidence`(证据文件) · `evidence_level`。

## 二、状态矩阵（项目 × 能力维）

| 能力维 | miniloop(JSTM 最小回环服) | chivalrousman 侠客行 | kongkongxiyou 空空西游 | mahatma 大圣归来 | survive | yzxy / CXEngine 原罪西游 |
|---|---|---|---|---|---|---|
| 网络与Session | 有 | 部分 | 有 | 有 | 有 | 有 |
| 协议编解码 | 有 | 部分 | 有 | 有 | 有 | 有 |
| 角色状态 | 有 | 部分 | 有 | 部分 | 有 | 有 |
| 场景和移动 | 部分 | 部分 | 有 | 部分 | 有 | 部分 |
| 任务 | 有 | 部分 | 有 | 无 | 部分 | UNKNOWN |
| 战斗 | 部分 | 部分 | 有 | 无 | 有 | 有 |
| 背包与装备 | 部分 | 部分 | 有 | 无 | 有 | 部分 |
| 养成系统 | 部分 | 部分 | 部分 | 部分 | 有 | 部分 |
| 持久化 | 有 | 部分 | 有 | 有 | 有 | 部分 |
| GM 管理 | 部分 | 无 | 有 | 部分 | 部分 | 部分 |
| 配置加载 | 有 | 部分 | 有 | 有 | 有 | 有 |
| 测试和日志 | 有 | 无 | 部分 | 无 | 有 | 部分 |

## 三、逐格详表

### miniloop(JSTM 最小回环服)

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 有 | Python 单进程；socketserver.ThreadingTCPServer 每连接一线程，TcpHandler→Session 每连接一对象；另起 BaseHTTPServer Gateway 出服务器列表；心跳 cmd 1199 直接回 time。 | 即 JSTM 目标形态本身；可向参考项目反取的是：Session.LOOP 已是 {cmd:方法名} 注册表雏形，后续可演进为 kongkongxiyou 式按域 handler。 | server/minloop/min_loop_server.py:1315-1353(TcpServer/Handler)、:549-595(Session/on_1199)、:1355-1443(HTTP Gateway) | CONFIRMED |
| 协议编解码 | 有 | pack_frame 组 [u32BE len][u16BE cmd][body]；FrameParser 流式拆包；Spec 加载 protocol/fields.json(3553 条) 做通用 encode_sc/read_cs；handle() 经 LOOP 表 getattr 分发，回环外命令按权威 SC 通用零值编码。 | Spec 以 fields.json 为唯一真源编解码——正是 YZXY ①单一真源管线在 JSTM 的已落地形态；LOOP 注册表 = Survive D2 / YZXY stub[PTO] 的 Python 雏形。 | min_loop_server.py:65-231(pack_frame/FrameParser/Spec)、:1270-1313(LOOP/handle)；server/minloop/README.md §2 | CONFIRMED |
| 角色状态 | 有 | SQLite roles 表；Store.ensure_role/role/set_role；Session.role_values()/attrs()/power() 现算属性与战力。 | 现状即基线；可补 Survive D8/D9：派生属性不落库、登录全量重算、attr2view 白名单。 | min_loop_server.py:219(roles DDL)、:259-275、:796-838 | CONFIRMED |
| 场景和移动 | 部分 | on_10204 收 CS x/y→落库→仅回发本人；push_10200/10201 下发场景实体与 NPC 摆位(_mapnpc_10001.json)。无 AOI、无寻路、无多玩家同步（README §5 明示不做）。 | 缺口即借鉴方向：Survive D11-D14（AOI 集合差/lineto/移动同步三件套/进视野补发）+ kongkongxiyou B3-B6。 | min_loop_server.py:839-848(on_10204)、:741-775(push_10200/10201)；README §5 已知不做清单 | CONFIRMED |
| 任务 | 有 | missions 表；12400 列表(只给链头)、12402 接取(对照真 mission_config.json 846 条验 bid)、12403 提交(校验条件→grant_award)、12404/12414/12415；击杀后 mission_bump 反哺进度。 | 4 态进度已与 kongkongxiyou TaskState 同构；可补其下线批量落库与怪侧上报进度机制。 | min_loop_server.py:322-336(missions DAO)、:889-1190(on_12400/12402/12403/12404/12414/12415) | CONFIRMED |
| 战斗 | 部分 | on_20002 驱动 20010→每回合 20012/20013→20020→20023→掉落 10500→击杀奖励→反哺任务；服务端 2.5s/回合自续期节拍；怪物数值 [TEST_ONLY]（APK 无此数据）。 | 已是服务端权威结算；可补 YZXY ⑦按速度降序出手、⑧先快照收件人；侠客行双档超时托管；不照抄任何项目战斗状态机本身。 | min_loop_server.py:977-1100(on_20002/kill_reward)；README §2/§3/§5.2 | CONFIRMED |
| 背包与装备 | 部分 | bag 表(rid,bid,quantity,bind)；bag_add/has/del；10502 查询、10505 双击物品；grant_award 经 add_assets+bag_add。装备系统未在回环内。 | 可补 Survive D18 发奖两阶段(先校验后落地)；chivalrousman D5/D6 统一容器 vs 分表取舍已在 bag 表落地。 | min_loop_server.py:284-320(bag DAO)、:1191-1280(on_10505/10502) | CONFIRMED |
| 养成系统 | 部分 | add_assets(gold/coin/coupon/exp/hero_exp)；attrs()/power() 由等级现算；无升阶/升星/成长目标等系统。 | 可参考 Survive CalAttr 派生重算口径；成长类数值必须以 JSTM APK 配置表为准。 | min_loop_server.py:277(add_assets)、:823-838(attrs/power) | CONFIRMED |
| 持久化 | 有 | SQLite(minloop.db) 4 表 roles/bag/missions/kv；Store.ex/one/all 每操作即提交；无脏标记/批量刷。 | 可补 kongkongxiyou B27 脏标记+定时批量 flush、Survive D20 一角色一次多字段读写；当前即写即提交对单机回环足够。 | min_loop_server.py:219-231(DDL)、:233-256(Store) | CONFIRMED |
| GM 管理 | 部分 | HTTP Gateway 仅出服务器列表 JSON(/gateway/mobile/json)、/notice 占位、其余回 {ok:true} 并记录 POST body；无游戏内 GM 命令、无运营面板、无权限模型。 | 缺口：参考 survive php Web 后台形态 / kongkongxiyou B31 admin 三段式；mahatma S12 提示 GM 公告必须带权限校验。 | min_loop_server.py:1355-1443(Gateway/do_GET/do_POST) | CONFIRMED |
| 配置加载 | 有 | Spec 读 protocol/fields.json；Data 读 server/mission_config.json(846)/item_config.json(3535)/config.json/_mapnpc_10001.json；掉落口径读 analysis 侧 _config_drop.json 并标注证据等级。 | 已是 JSON 配置驱动；可补 kongkongxiyou B13 dataApi→DataTable 按 id/字段索引访问口。 | min_loop_server.py:127-231(Spec)、:480-535(Data)；README §3/§5.3 | CONFIRMED |
| 测试和日志 | 有 | selftest.py 离线回环逐帧严格解码校验(父任务书基线 145/145；脚本末尾打印‘检查项 N 通过 N 失败 0’)；replay_real_frames.py 真机帧回放(292/422/8831 帧 0 规格不符)；log() 写 minloop_server.log。 | 真协议回放即 Survive D22 压测机器人的已落地形态；可补其 Python bot 做移动/NPC 复现。 | server/minloop/selftest.py:33-37/739；replay_real_frames.py；README §4/§5.3 | CONFIRMED |

### chivalrousman 侠客行

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 部分 | 仅客户端(包内无服务端)；TCPClient 纯传输(connect/send/recv+虚 OnRecv)；CMClient switch(type) 分发到 22 个 doXxxMsg；无心跳/无重连/无发送队列(反面)；结构体内存裸发无长度前缀(反面)。 | N7/N8 五段式分层形状(TCPClient 纯传输/ShareData.h 集中定义/CMClient switch 分发/Model.h 实体自描述/DBDao<T> 泛型 DAO/按域 Manager)；反面 X9/X10：裸发无端序、无心跳不可学。 | chivalrousman/reuse_candidates.md N7-N10、X9/X10 | VERIFIED |
| 协议编解码 | 部分 | ShareData.h 集中 23 个 M_Type 命令枚举+22 个定长 *_Msg 结构体；收 switch 分发、发 15+ SendXxxMsg 对称形状；public.h 魔数字符串断线哨兵(反面)。 | N1 命令+结构体集中定义一个头文件；D7 千位分段全局枚举(1xxx 物品/2xxx 任务/3xxx NPC/4xxx 玩家/5xxx 队伍)——JSTM 自查常量命名空间。 | chivalrousman/reuse_candidates.md N1/N8/D7/X9 | VERIFIED |
| 角色状态 | 部分 | PlayerInfo 15 字段(playername…destx/desty/level)；Player_Info 远端广播字段清单；UpdateData_Msg 属性变化单独增量消息。 | N3 进场景全量(InitData)+运行期增量(UpdateData)两段式属性同步；N2 远端玩家广播字段清单可对照 AOI 实体字段。 | chivalrousman/reuse_candidates.md N2/N3/D2 | VERIFIED |
| 场景和移动 | 部分 | 客户端 FindRoad A*+map{n}.mp 网格；存在 M_VerifyPos 服务端校验/客户端校准消息，但 doPlayerPosVerifyMsg 循环条件写错致从未生效(反面)。 | N4 位置校验消息形状(服务端下达/客户端校准)——JSTM 做移动反外挂可参考该形状，且必须修对循环 bug；B10 map 网格数据结构。 | chivalrousman/reuse_candidates.md N4/B10/X13 | VERIFIED |
| 任务 | 部分 | Task{n}.tsk 8 字段(name/…/type)+.tk 三态对话+NS_HTASK/WSTASK/STASK 状态宏；但权威模型是客户端每 15 秒随机生成、不走 TCP、不落库、本地发奖(反面)。 | B2 .tsk 8 字段+三态对话+NPC 任务状态宏的数据结构形状；其权威模型(随机生成/客户端发奖)明确不可借鉴。 | chivalrousman/task.md 附录 D；reuse_candidates.md B2 | VERIFIED |
| 战斗 | 部分 | 客户端 FightLayer 回合逻辑+实时定时器调度；8 标志位状态机；伤害客户端本地算(attack-defense 下限 1)；PlayerAtk_Msg 不含伤害/血量。 | 侠客行手动 10s/自动 2s 双档超时托管(FINAL §二之补)；反面 X12：客户端算伤害/发奖不可学——JSTM 战斗必须服务端权威。 | chivalrousman/battle.md；reuse_candidates.md B9/X12；FINAL_SERVER_ARCHITECTURE.md §二之补 | VERIFIED |
| 背包与装备 | 部分 | backpack 统一容器 6 字段(thingtype 1001 药品/1002 装备/1003 技能书)；equipmentinfo type=槽位(1005-1009)穿新卸旧；精炼=grade+1；UseMedication 走独立 TCP 消息广播队友。 | D5/D6 统一容器+类型字段 vs 按类型分表的取舍样本、type=槽位紧凑设计；B4 五槽位+穿新卸旧规则形状。 | chivalrousman/reuse_candidates.md D5/D6/B3/B4/N6 | VERIFIED |
| 养成系统 | 部分 | 建号初值配方(attack100/blood300/def20/glod300/grade1/mana150/speed4/exp0/maxExp100)；skillinfo skillgrade；技能伤害 (baseAttack+30×grade)-def。 | D3 1 级新角色属性基线‘配方’形状(数值不可搬)；技能表 4 字段对照。 | chivalrousman/reuse_candidates.md D3/D4/B5 | VERIFIED |
| 持久化 | 部分 | 客户端 libmysql 直连公网 MySQL(凭据已泄露)；Model.h 自描述表名+字段+序号→DBDao<T> 泛型 SQL 生成；5 表 33 字段；无参数化/无事务/INSERT 而非 UPSERT/双字符串外键(反面)。 | D8 Model.h 实体自描述→DAO 泛型化形状(JSTM 必须改参数化+事务+UPSERT+roleId 主键)；5 表 33 字段作为业务库字段语义对照基线。 | chivalrousman/database.md；reuse_candidates.md D1-D8/X1-X8 | VERIFIED |
| GM 管理 | 无 | 包内无服务端，无 GM 体系。 | 无。 | chivalrousman/reuse_candidates.md(无 GM 条目)；reference_projects_verified.md §2.5 | VERIFIED |
| 配置加载 | 部分 | GameData.xml plist 名字即索引；Thing/*.att(4 字段属性)+*.dec(名/描述)静态数据外置；PreProcess.h 宏定义集中。 | B11 静态数据外置+名字即索引；D7 枚举集中一个头文件。 | chivalrousman/reuse_candidates.md B11/D7/E2 | VERIFIED |
| 测试和日志 | 无 | 无测试体系。 | 无。 | chivalrousman/reuse_candidates.md(无测试条目) | UNKNOWN |

### kongkongxiyou 空空西游

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 有 | Node.js+Pomelo；connector(gate)/area/auth/chat/manager 多服务器；hybridconnector 混合 TCP/WS；sessionService(session 副本+pushAll)；channelService 跨进程广播。 | B7 定向推送收口 messageService+频道广播再收敛同一底层 send()；B15 频道抽象(area_/team_/guild_ 命名规则)；pomelo connector 协议栈本身不可用(JSTM 协议来自 APK)。 | kongkongxiyou/pomelo.md；reuse_candidates.md B7/B15、§2.1 | VERIFIED |
| 协议编解码 | 有 | Pomelo 路由串 serverType.handlerName.methodName；dictionary.json route→数字(本项目未用 protobuf)；JSON 消息；playerFilter 前置守卫统一取玩家/校验归属/注入 session.player。 | B11 ‘协议名=模块.方法’路由约定(日后拆进程零改动)；B12 handler 前置守卫 filter+异常时 onChangeArea 自愈；B14 集中错误码表+onLogTips/onTipsBox 两档提示。 | kongkongxiyou/reuse_candidates.md B11/B12/B14 | VERIFIED |
| 角色状态 | 有 | domain/entity/{player,character,mob,npc}.js；strip()(给别人看)与 playerStrip()(给自己看) 分字段集序列化。 | B25 strip/playerStrip 双视角字段集——解决同步宽表；JSTM 对同屏可见属性应收敛字段。 | kongkongxiyou/reuse_candidates.md B25 | VERIFIED |
| 场景和移动 | 有 | AreaManager→Scene/InstancePool→Instance→Area 五层；100ms 主 tick+1s/3s 分频；ActionManager 把行走建模为可中断 singleton Action；AOI watcher+object 双注册/4 事件/双向差集；handler.move 直接信任客户端整条路径(verifyPath 零调用)。 | B1-B6 场景五层+AOI 三件套(getWatcherUids 让 AOI 绝不碰 socket)；B9/B10 Action+服务端权威位置推进；B22 instanceId 命名即共享域；红线 N1：JSTM 必须补 L1 路径校验+起点一致、L2 位移上限/限流。AOI/A* 内核未随 ZIP 打包，须自研。 | kongkongxiyou/aoi.md、pathfinding.md、scene.md；reuse_candidates.md B1-B10/N1 | VERIFIED |
| 任务 | 有 | area/handler/taskHandler.js + app/domain/task/*.js：TaskState 4 态(与 JSTM mission_status 0/1/2/3 1:1 同构)、TaskType 3 类、怪侧上报进度、下线批量落库。 | R5 已认证的首选任务参考：4 态状态机形状+怪侧进度上报+下线批量落库；按域 taskHandler 切文件。注意 TaskType 对应 JSTM 的 progress 计算方式，不是 MissionType 28 类。 | comparison/task_matrix.md §三/§五/§八；architecture_matrix.md §一任务行 | VERIFIED |
| 战斗 | 有 | area/handler/fightHandler.js；实时制(非回合)；怪物仇恨表 increaseHateFor/getMostHater；areaKind 策略模式按场景类型分流。 | 仇恨表机制+areaKind 策略模式；不照搬实时判定(JSTM 回合制)。 | comparison/battle_matrix.md §三；kongkongxiyou/reuse_candidates.md F 节 | VERIFIED |
| 背包与装备 | 有 | area/handler/{equip,market,shop}Handler.js 按业务域切文件；dao/mapping/{bag,equipment,...}Sync.js 脏刷映射。 | 按业务域切 handler 的组织方式；B27 DAO 内存对象+脏标记+定时批量 UPDATE。 | server_reference/README.md §2.2 handler 清单；reuse_candidates.md B27 | VERIFIED |
| 养成系统 | 部分 | skillHandler.js/playerHandler.js；exp/等级在 player 域；矩阵评分 EXP/等级=4、技能=4(未实现部分)。 | 技能/养成按域 handler 组织；数值不可搬。 | comparison/architecture_matrix.md §一(EXP=4/技能=4)；README §2.2 skillHandler | STRONG_INFERENCE |
| 持久化 | 有 | MySQL(config/schema/Pomelo.sql 18.8KB)；app/dao/** + dao/mapping/*Sync.js；pomelo-sync-plugin 定时脏刷(插件本体未打包，只剩 mapping 表)。 | B27 内存对象+脏标记+定时批量 flush 是 MMORPG 存档正解——JSTM 自研 dirty_registry；Pomelo.sql 对应空空西游数据模型，不可照搬。 | kongkongxiyou/reuse_candidates.md B27、§2.3 | VERIFIED |
| GM 管理 | 有 | pomelo-admin-web(ExtJS 管理台，GPL ExtJS 严禁引入)；manager server chatHandler 有 SYSTEM 频道 @ 发奖后门(反面)；monitorHandler/masterHandler/clientHandler 三段式监控。 | B31 admin 监控三段式 moduleId 约定可做在线数/场景状态 Web 面板模板；反面 N22：内置发奖后门必须显式权限校验+独立管理通道。 | kongkongxiyou/reuse_candidates.md B31/N22；reference_projects_verified.md §2.2 | VERIFIED |
| 配置加载 | 有 | exceldata/ Excel→JSON 管线；util/dataApi.js new DataTable 按 id/字段索引(findById/findBy/findBigger)；error_code.json/forbid_word.json。 | B13 dataApi→DataTable 约 30 行统一配置访问口，JSTM 直接移植 Python DataTable 类；B14 错误码集中表。 | kongkongxiyou/reuse_candidates.md B13/B14 | VERIFIED |
| 测试和日志 | 部分 | 无单测框架；utils.myPrint 硬编码全量日志(反面)；uncaughtException 只 console.error 不退出(反面)；handlerService.watchHandlers 热重载。 | B36 reloadHandlers 热重载(Python importlib.reload)；反面 N18/N19：热路径禁打日志、异常后优雅下线/重启。 | kongkongxiyou/reuse_candidates.md B36/N18/N19 | VERIFIED |

### mahatma 大圣归来

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 有 | C#/.NET WinForms：Form1.cs 同时是 WebSocket 监听+协议解析+业务分发(190 行 if/else)+SQL+UI；secretKey 登录票据贯穿后续请求。 | S10 登录发一次票据后续用票据的会话模型(改随机串+过期+可撤销)；S4 ws_Open/Close/Message 三事件标准形状；反面 S3：一文件全包不可学。 | mahatma/network.md；reuse_candidates.md S3/S4/S10 | VERIFIED |
| 协议编解码 | 有 | WebSocket+JSON；manipulationData(type,json,client) 190 行 if/else；远端角色同步=一条 JSON 全字段+state 枚举(walk/free/remove)。 | S5/S6/S7 远端角色同步用单一消息+state 枚举(走/停/下线)而非 N 个消息类型——JSTM 可减少命令号并补 AOI。 | mahatma/reuse_candidates.md S5/S6/S7 | VERIFIED |
| 角色状态 | 部分 | game 表 11 字段(账号=角色主键)；客户端 Player state 枚举 FREE/WALK/ATTACK/DEAD；服务端无属性系统。 | C11 状态机骨架(FREE/WALK/ATTACK/DEAD)可对照，JSTM 需扩展受击/施法/眩晕。 | mahatma/role.md；reuse_candidates.md C11 | VERIFIED |
| 场景和移动 | 部分 | 服务端零寻路校验；客户端 GameScene 用 map.tmx opacity=0 独立图层判墙；4 邻接 A* 曼哈顿启发；atan2 分档 8 向朝向。 | C4 同一 tmx 碰撞图层客户端/服务端共用(避免双份维护)；C5 8 向 direction 取值定义；反面 N4：全服广播无 AOI。 | mahatma/reuse_candidates.md C4-C8、N3/N4 | VERIFIED |
| 任务 | 无 | gametable.sql 仅 1 表 game(11 字段)，无任务/物品/装备/技能任何业务表。 | 无可借鉴；作为‘一账号一角色全 varchar’反例读。 | FINAL_SERVER_ARCHITECTURE.md §二之补二 更正 1；mahatma/database.md | VERIFIED |
| 战斗 | 无 | 服务端无战斗逻辑(教学级 Demo 只到走路/聊天)。 | 无。 | mahatma/reuse_candidates.md §三 N1-N9；FINAL §二之补二 | VERIFIED |
| 背包与装备 | 无 | 无业务表，无背包/装备系统。 | 无。 | mahatma/database.md §3；FINAL §二之补二 | VERIFIED |
| 养成系统 | 部分 | game 表含 grade/blood/mana；客户端 initWithJson 里 grade=1 硬编码覆盖服务端下发值(反面)。 | 反面 C21：加载后字段被硬编码重置——JSTM 自查同类覆盖。 | mahatma/reuse_candidates.md C21 | VERIFIED |
| 持久化 | 有 | MySQL；DbConnectionMySQL.cs 静态门面(ExecuteNonQuery 4 重载+事务重载+参数缓存)，但全部调用传 null 弃用参数化/事务；每走一格 3 条 UPDATE。 | S1/S2 DB 门面 API 形状(统一入口+事务作一等公民+参数缓存)；反面 N3/N8：事务必须用、参数化必须开。 | mahatma/database.md；reuse_candidates.md S1/S2/N3/N8 | VERIFIED |
| GM 管理 | 部分 | Form1.button1_Click 全服公告按钮(无权限控制)；即最小运营能力的位置占位。 | S12：JSTM 需要带权限校验的 GM 公告通道。 | mahatma/reuse_candidates.md S12 | VERIFIED |
| 配置加载 | 有 | Resources/Data.json {ip,port} 驱动服务器地址；Resources/text.xml 文案外置 plist-dict 代码只用 key。 | C2 服务器地址外置不硬编码；C12 文案外置 key 引用。 | mahatma/reuse_candidates.md C2/C12 | VERIFIED |
| 测试和日志 | 无 | WinForms 调试输出；无测试体系。 | 无。 | mahatma/reuse_candidates.md(无测试条目) | UNKNOWN |

### survive

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 有 | Lua+自研 distrilua 框架；gate/group/game/notise 多进程，gateserver 可多台；同步写法异步实现(协程 socket)；三套 id 体系(gate/group/player)；断线重连逻辑完整。 | D1 中心只听/成员反注册免配置实例列表；D3 路由键写尾读尾(转发层零业务知识)；D4 同屏广播按连接合并+只在 watch_me 上发；D14 进视野/重连补发移动与 Buff。多进程形态本身不搬(JSTM 单进程)。 | server_reference/survive/network.md §二/§七/§八；reuse_candidates.md D1/D3/D4/D14 | VERIFIED |
| 协议编解码 | 有 | netcmd/netcmd.lua 命令号按方向分十段；msghandler.lua RegHandler(cmd,f) require 时自注册，分发一次查表；lua/rpc.lua 函数名派发+identity 去重+5s 超时重试。 | D2 cmd→handler 注册表+按域拆文件(正是 JSTM 该从 if 链改成的形态)；D7 至少一次投递+服务端去重=恰好一次、断线批量唤醒 pending。命令号自增方式不可用(JSTM 号段被 APK 锁死)。 | survive/network.md §4(msghandler.lua)、§六(rpc.lua)；R1_SUPPLEMENT §4.1 D2 | VERIFIED |
| 角色状态 | 有 | groupserver/groupplayer.lua + gameserver/avatar.lua；attr.lua 下标化属性表，只持久化前 23 项输入属性，派生值每次登录 CalAttr 全量重算。 | D8 只存输入项杜绝存档与公式不一致(须改命名字段)；D9 attr2view={level,life,maxlife} 白名单+一次变更两包(视野包/自身包)；D10 装备变动返回 'recalattr' 信号。 | survive/role.md §3-§4；reuse_candidates.md D8/D9/D10 | VERIFIED |
| 场景和移动 | 有 | gameserver/map.lua/maplogic.lua/areatrigger.lua；C 扩展 aoi.so/astar.so(文件头内嵌 GPLv3)；单线程一服务加载 1-N 场景。 | D11 AOI 均匀网格+视野集合去重+enter/unchange/leave 差+双向 enter_see/leave_see 回调；D12 A* 8 邻域+Bresenham lineto(遇障即停，用于击退/位移/追踪)；D13 移动同步三件套(客户端只发目标点→服务端只广播速度+目标点→100ms movmargin 自走)。实现必须自写(GPLv3)。 | survive/scene.md §3/§4/§5.4；reuse_candidates.md D11-D14 | VERIFIED |
| 任务 | 部分 | 跨场景任务/日常任务在 groupserver 承载(groupserver 为全局逻辑中心)；everydaytask.lua 事件驱动。 | 分层思想：全局任务类放中心服；反面教训 D21 旁注——everydaytask 每事件都写库是反例，JSTM 应加节流/脏刷。 | survive/reuse_candidates.md D21 旁注；README.md §三评分表(任务=3) | STRONG_INFERENCE |
| 战斗 | 有 | skill.lua/buff.lua/bufffunction.lua/triggerfunction.lua/battlebag.lua；实时制；buff=静态表 TableBuff+按名字符串查 BuffFunc 函数表；robot.lua AI=协程+三态状态机+事件唤醒。 | D19 配置写函数名→代码查函数表(须补启动时引用校验)；D25 AI 协程化、追击事件驱动不轮询；反面：战斗层零距离/角度/目标数校验，照抄=开放全图秒杀。 | survive/battle.md §3/§4/§5；reuse_candidates.md D19/D25；R1_SUPPLEMENT §4.1 末 | VERIFIED |
| 背包与装备 | 有 | groupserver/bag.lua/equip.lua；AddItems 先收集全部 bagpos 成功才写；Swap 只改数据并返回 'recalattr'。 | D18 发奖先全量校验再全部落地两阶段；D20 一角色一次多字段 hmset/hmget；D21 脏标记+只写变更。 | survive/role.md §5；reuse_candidates.md D18/D20/D21 | VERIFIED |
| 养成系统 | 有 | attr.lua CalAttr 派生重算；EXP/等级曲线在 groupserver；矩阵评分 EXP/等级=4。 | 同角色状态维：派生属性登录全量重算思想；数值不可搬。 | comparison/architecture_matrix.md §一(EXP/等级=4)；survive/role.md §4 | STRONG_INFERENCE |
| 持久化 | 有 | groupserver 侧 Redis：一角色一条 hmset(8-9 field)，dbchange 脏标记异步落库；lua 字符串拼接 key。 | D20/D21 一角色一次读写+脏标记思想可平移到 SQLite；反面：redis 字符串拼接、无事务(JSTM 应加)。 | survive/database.md §3/§4；reuse_candidates.md D20/D21 | VERIFIED |
| GM 管理 | 部分 | php/ Web 后台(68 个 php 文件) + notiserver；无权限细节审计。 | Web GM 后台的组织方式可参考；具体交互未逐文件读。 | reference_projects_verified.md §2.1；server_reference/README.md §1.1 | STRONG_INFERENCE |
| 配置加载 | 有 | common/Table*.lua 配置表 + setconfig.lua 启动配置；TableBuff/TriggerTable 等静态表驱动回调。 | D19 配置表写函数名→运行期查函数表；JSTM 须补‘启动时校验引用存在’(Survive 未做，错名静默失效)。 | survive/reuse_candidates.md D19 | VERIFIED |
| 测试和日志 | 有 | robotclient.lua 50 协程真协议压测机器人(登录/进图/随机移动)；network.md §九 日志与可观测性；daemon.lua 守护。 | D22 用真实协议写压测/回归 bot——JSTM 已有真协议，写 Python bot 更容易，可复现移动/NPC 对话问题。 | survive/reuse_candidates.md D22；network.md §九 | VERIFIED |

### yzxy / CXEngine 原罪西游

| 能力维 | 状态 | 实现方式 | 对 JSTM mock_server 的可借鉴点 | 证据文件 | 证据等级 |
|---|---|---|---|---|---|
| 网络与Session | 有 | C++(cxluax 绑定)+Lua；scripts/server/ 脚本层服务端；server_thread_on_message 两阶段收包(握手期注册/登录/GM 当场处理，其余 netq 入队由主 tick 派发)；IsServer()/IsClient() 同码分叉。 | YZXY ② 两阶段收包(握手低延迟+主循环统一派发)——JSTM ThreadingTCPServer 可演进为‘登录/心跳立即答、业务入主循环’；能力显式清单注册 C 原语。 | yzxy/lua_server.md；reuse_candidates.md ②/③ | VERIFIED |
| 协议编解码 | 有 | scripts/share/enums_protocol.lua 协议 ID 唯一真源→scripts/generator/protocol.lua 生成 C++ 协议头；线格式 [LE u32][LE u32][JSON]；stub[PTO_XXX]=fn 4 行分发。 | YZXY ① TSV/表单一真源→生成多端定义(以 fields.json 生成 proto_defs.py 供服务器/测试/解码器共用+CI 校验生成物==仓库文件)；stub 零样板分发。 | yzxy/protocol.md §2/§3/§5；reuse_candidates.md ①/② | VERIFIED |
| 角色状态 | 有 | assets/tables/actor_template.tsv(name/type/def/sync 列)→生成 EActorProp 枚举；RegProperty assert(index==m_Props.size()) 锁死表行序==枚举==数组下标。 | ① sync 列声明哪些属性需上线同步+断言锁死映射(错了立刻炸而非静默错位)；JSTM 可对 fields.json 做同类‘行序==字段序==编码序’断言。 | yzxy/reuse_candidates.md ①；role.md | VERIFIED |
| 场景和移动 | 部分 | 动作引擎实时移动；scripts/client addon 体系；场景/移动细节未逐文件审计(矩阵评分 场景=3/寻路=3)。 | 有限：实时制移动不对应 JSTM 回合场景；C++ 原语+Lua 逻辑分层思想已在网络维覆盖。 | comparison/architecture_matrix.md §一(场景=3/寻路=3)；yzxy/architecture.md | STRONG_INFERENCE |
| 任务 | UNKNOWN | scripts/client/addon/quest.lua 从未被任何审计读过(R5 已登记‘未取证’)；无服务端任务域文件记录。 | 无可确认借鉴点——任务参考已改为 kongkongxiyou domain/task + chivalrousman。 | yzxy/architecture.md:214、yzxy/lua_server.md:422(均记‘未读’)；comparison/task_matrix.md §八 | VERIFIED |
| 战斗 | 有 | 独立 scripts/combat/ 战斗层；BattleMT 回合 FSM(客户端本地 NextTurn 推进)；CalcSpeed() 降序出手；先快照收件人再结算；随机数只在服务端摇随消息下发；buff 无同步协议(缺陷)。 | ⑦ 服务端按速度降序定出手顺序；⑧ 先快照收件人再结算；④ 服务端摇随机结果下发；⑤ buff=静态表+按 ID 脚本回调+回合统一结算骨架；⑩ 具名定时器管理器。不可照搬：客户端推回合、buff 不上线、5 条字段级理由。 | yzxy/battle.md；reuse_candidates.md ④-⑩；comparison/battle_matrix.md §三 | VERIFIED |
| 背包与装备 | 部分 | scripts/client/addon/{bag,props} 按功能插件化；服务端对应域未逐文件读(矩阵评分 背包=4)。 | addon/ 按功能插件化(bag/props/quest/hud)的模块组织方式。 | server_reference/README.md §2.3；comparison/architecture_matrix.md §一(背包=4) | STRONG_INFERENCE |
| 养成系统 | 部分 | actor props 体系；yzxy/impl 已抽取 skill_magic.json(2.3MB)+battle_magic.py 技能/魔法骨架。 | 技能/魔法=静态表+脚本回调骨架(⑤)；数值全为《梦幻西游》内容，一律不可搬。 | yzxy/impl/battle_magic.py、skill_magic.json；reuse_candidates.md ⑤ | STRONG_INFERENCE |
| 持久化 | 部分 | 脚本层服务端含持久化；具体存储引擎/表结构未在本轮逐文件读取。 | 无可确认具体机制。 | yzxy/architecture.md(本轮未深读持久化节) | UNKNOWN |
| GM 管理 | 部分 | 两阶段收包中 GM/注册/登录类命令与握手同列，当场立即处理不等主 tick。 | ② GM/握手命令即时处理、不入队主 tick 的优先级形状。 | yzxy/reuse_candidates.md ② | VERIFIED |
| 配置加载 | 有 | assets/tables/*.tsv 单一真源→generator 生成多端定义；⑪ 异步加载任务表(后台线程+去重+主线程轮询状态)。 | ① TSV→代码生成管线(同 fields.json 路线)；⑪ 异步加载大表+去重+主线程轮询状态。 | yzxy/reuse_candidates.md ①/⑪ | VERIFIED |
| 测试和日志 | 部分 | 开发期 assert 锁死不变量(如 RegProperty)；⑫ 可执行文档+文档即短板清单；无独立单测框架记录。 | assert 锁死映射不变量+CI 校验生成物==仓库文件。 | yzxy/reuse_candidates.md ①/⑫ | STRONG_INFERENCE |

## 四、最有借鉴价值的机制点（Top 5）

1. **cmd→handler 注册表（Survive D2 / YZXY stub[PTO] / kongkongxiyou handler 按域切分）**——JSTM miniloop 已是 LOOP 表雏形，下一步按业务域拆 handler，消灭 if 长链。
2. **AOI 三件套（Survive D11 + kongkongxiyou B3-B6）**——watcher/object 双注册 + 4 事件契约 + 双向差量同步，getWatcherUids 让 AOI 绝不碰 socket；JSTM 完全缺失，须自研（GPL 不可翻译照抄）。
3. **移动同步三件套（Survive D13/D14 + kongkongxiyou B8/B10）**——客户端只发目标点、服务端只广播速度+目标点、服务端按时间预算自走；进视野/重连补发移动与 buff；必须补 L1 路径校验+L2 限流。
4. **单一真源+代码生成（YZXY ①）**——以 protocol/fields.json(3553 条) 为唯一真源生成 proto_defs.py，CI 校验生成物==仓库文件；JSTM miniloop 的 Spec 已是该路线雏形。
5. **发奖两阶段+属性派生重算（Survive D8/D10/D18）**——先全量校验再落地；属性只存输入项、登录 CalAttr 全量重算、attr2view 白名单、‘recalattr’ 信号解耦数据与计算。

## 五、未确认项清单（UNKNOWN / 待取证）

- **yzxy·任务**：addon/quest.lua 从未被任何审计读过 → 标 UNKNOWN；任务参考已改 kongkongxiyou domain/task + chivalrousman。
- **yzxy·持久化**：存储引擎/表结构本轮未逐文件读 → 部分/UNKNOWN。
- **mahatma·测试和日志**、**chivalrousman·测试和日志/GM 管理**：无体系可考 → 无/UNKNOWN。
- **kongkongxiyou AOI/A\* 算法本体**：pomelo-aoi/pomelo-pathfinding/pomelo-bt 未随 ZIP 打包，只有调用契约 → JSTM 必须自研。
- **jstm/ 8 个模型文档**(server_reference/jstm/ 空目录)：未产出，本表现以 miniloop 实测代码代替。

## 六、自检记录

- JSON 由本构建脚本一次性生成，随后 python json.load 复测可解析。
- 覆盖：6 项目 × 12 维度 = 72 格全覆盖；无空格。
- miniloop 行基于 server/minloop/min_loop_server.py 本轮 Grep 实测（TcpServer/Session/LOOP/Spec/Store/4 张 SQLite 表/心跳 1199/HTTP Gateway）。
- 参考项目行基于 analysis/server_reference/ 既有逐文件审计（README/FINAL_SERVER_ARCHITECTURE/R1_SUPPLEMENT/comparison 矩阵/各项目 reuse_candidates）+ analysis/reference_projects_verified.md 复核结论。

