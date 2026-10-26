# 《绝世唐门》1.4.11 复原工程 — AI Agent 交接文档

> 本文件供下一个 AI agent 快速接手。读完本文件 + `tests/1.4.11/FINAL_REGRESSION.md` 即可继续工作。
> 最近更新：2026-10-16（C4 批次：GM 后台管理系统 + 服务端场景缺陷修复，见 §十一）

---

## 一、项目目标

使用原版《绝世唐门》1.4.11 客户端（MuMu 模拟器运行）+ 本地 `mock_server`，尽可能恢复原游戏完整玩法闭环。
- **主兼容版本**：1.4.11（补丁包 `patched/jstm_1411_fakelogin_aligned.apk`，包名 `com.shiyue.dldl.ewan.baidu2`）
- 参考版本：1.4.9（`.qihoo`）、1.3.0（基础包）仅用于对比补全，不做最终目标
- **唯一数值标准**：JSTM APK + 资源 + 协议 + MuMu 实机运行结果。禁止编造数据。

## 二、硬纪律（最高优先级，所有后续工作必须遵守）

1. **证据等级**：CONFIRMED（APK/协议/资源/实机直接确认）> VERIFIED（实机+mock_server 实际运行）> STRONG_INFERENCE（多源推断）> INFERENCE（结构推断无直接证据）> UNKNOWN。禁止把 UNKNOWN 写成 CONFIRMED，禁止因"其他游戏通常这样"就断定 JSTM 如此。
2. **MuMu 实机数据优先**：客户端可见/可操作的真实行为是最高证据。抓不到的标 INFERENCE/UNKNOWN 并留替换点。
3. **不破坏既有闭环**：登录/角色/地图/NPC/任务/战斗/背包/商城/邮件等已工作的链路，改动后必须六项回归 + 实机冒烟。
4. **服务统一收敛**：所有资产变化走 CurrencyService/RewardService/ItemService/AttributeService/PowerService/ClientSync，GM 修改必须走正式 Service 链路，禁止直改 DB。
5. **幂等性**：奖励发放在 reward_log 表有 transaction_id 防重。
6. **每步备份**：改 mock_server.py 前存 `.bak_rXXX`，失败即回滚。

## 三、环境信息（已实测）

- **OS**：Windows，Python = `D:\Python\python.exe`（3.12.3）或 `D:\Anaconda3\python.exe`
- **MuMu 12**：安装于 `D:\MuMuPlayer`，实例 0「MuMu安卓设备」Android 12
  - adb：`D:\ADB\platform-tools\adb.exe`（PATH 内），连接命令 `adb connect 127.0.0.1:16384`，设备序列号 `127.0.0.1:16384`
  - 已装 APK：1.3.0 `com.shiyue.dldl.ewan`、1.4.9 `.qihoo`、1.4.11 `.baidu2`（本工程主用）
- **mock_server**：`server/mock_server.py`（约 18.5k 行单体 Python），TCP 9000 + HTTP 8080（/DSH_ADMIN 管理面）
  - 客户端指向：`10.0.2.2:9000`（TCP）/ `10.0.2.2:8080`（HTTP）
  - 客户端重连：server 重启后客户端约 11 秒自动重连
- **miniloop 自检**：`server/min_loop_server.py`，145/145 PASS 为回归基线

### 常用命令速查
```powershell
# 启动 mock_server（WMI 分离启动）
# 端口就绪后 /status 返回 lv70/gold=1799840/coin=9904599/scene=10001 为基线

# miniloop 回归（改代码后必跑）
python server/min_loop_server.py   # 预期 145/145

# 战斗确定性重放锚点
GET http://127.0.0.1:8080/DSH_ADMIN/battle_replay?mon_id=20001
# 两次重放 hex 必须一致（改战斗族前对照 server/backup/replay_before.json）

# GM 端点（走正式 Service）
GET /DSH_ADMIN/setlevel?rid=1001&lv=71
GET /DSH_ADMIN/reward_log          # 奖励审计
GET /DSH_ADMIN/ach_list
```

## 四、当前状态终值

- **registered CS 命令**：19 个（1110/10101/10200/10301/10302/10303/10304/10306/10502/10601/10610/10622/10651/11215/11600/12400/12401/12408/15203）
- **已闭环系统**：登录/角色/等级/经验/背包/仓库/装备/任务/商城/黑市/邮件/排行/副本/挂机/签到/日常/成就/结拜/结婚/拍卖/法宝/翅膀/坐骑/魂兽/元神/神器/命格/椅子/时装/光环/符文/投资/BOSS/称号/阵法书/伙伴面板/技能学习/GM Manager
- **架构下沉**：core/persistence/protocol/attribute/currency/role/task/equipment/scene 已模块化（8 件套 scene 函数群全部 `is==True`），AOI + 战斗 Timer sendall 全部收敛到 `SessionRegistry.push_to_rid`
- **battle_replay 确定性重放端点**：已建（两次 hex 一致）
- **测试基线**：miniloop 145/145、/status 基线一致、shadow_lint 干净

## 五、CONFIRMED 真值（已落地，10 项）

| 项 | 真值 | 来源 |
|---|---|---|
| 强化成功率 | L1=100% / L3=75% | config_intensify |
| 强化消耗 | L1=2400 金币 + 强化石 36006 | config_intensify |
| 签到 30 天 | Day1=250000 银魂币 / Day2=36500×10 / Day7=36500×15 | config_checkin |
| 掉落首杀 | 20012→1001、20024→1002（+coin 3000/6000） | config_drop |
| 战力系数 | 攻速 450/暴击 183/物攻 106… | _attr_data.json |
| 伙伴曲线 | 201 级 exp_max | config_partner_base |
| 技能点金币 | L1=10g→L10=100g | config_skill SkillPoint |
| 修炼升级 | L1→L2=402 exp；L22=63096 | SkillXiulianUp |
| 成就 | 342 条（bid/name/desc/cent/type） | config_chengjiu |
| 挂机 | 8 区域（map_bid 10002~10011） | config_guaji |
| 宝石 | 40 物品（8 类×5 级）+ ItemMiscAttrJewel 总属性表（slots12/18/24） | config_item_misc_attr |

## 六、剩余缺口清单（9 项，FINAL_REGRESSION.md 同步）

| # | 缺口 | 状态 | 后续通道 |
|---|---|---|---|
| 1 | 怪物 HP/ATK 真值 | UNKNOWN（公式在服务端，配置无显式值） | 真服抓包 / 反编译服务端公式 |
| 2 | 伙伴基础喂养消耗 | UNKNOWN（配置无显式值，账号无伙伴无可观察） | 实机喂养一次 UI 取证（需先获得伙伴） |
| 3 | 宝石镶嵌加成 | 部分 CONFIRMED（总属性表已接线）；单宝石拆分 INFERENCE | ItemJewel 反构造失败；真服 |
| 4 | 修炼 UI"50"语义 | **CONFIRMED**：50=修炼进度条本级满值（35/50），非 SkillXiulianUp | — |
| 5 | 修炼消耗/拥有 EXP 下发 | **进行中**：practice_exp 已改动态读取=35，待用户二次回证是否上屏 | 若仍空白则另有独立帧，继续 luac 定位 |
| 6 | 巡逻按钮激活条件 | 待证（客户端本地 UI 态，非挂机场所无法观察） | 挂机场景下用户观察 / hook 客户端回调 |
| 7 | chengjiu_has.state 子字段语义 | UNKNOWN | frida-tools 原生 hook / 真服 / 用户协助 |
| 8 | 真服全量数值标定 | 待办（真服大概率已下线，原版地址被补丁替换） | 真服恢复后按 gap_dig.md 清单取证 |
| 9 | 20002 战斗族注册 | 最终裁定：保留旧链运行（self 上下文传递面过大，不再下沉） | 不改 |

## 七、关键文件地图

```
DSH/
├── HANDOFF.md                     ← 本文件
├── server/
│   ├── mock_server.py             ← 主服务（约 18.5k 行，改前 .bak_rXXX）
│   ├── min_loop_server.py         ← 145/145 自检
│   ├── battle.py / power.py / pathfind.py / aoi.py / quest_spawn.py
│   ├── core/ protocol/ session/ account/ role/ scene/ npc/ task/ battle/
│   │   item/ inventory/ equipment/ enhancement/ skill/ partner/ wing/
│   │   soulbone/ fashion/ amplification/ artifact/ destiny/ formation/
│   │   dungeon/ afk/ shop/ currency/ package/ activity/ reward/ social/
│   │   guild/ ranking/ mail/ achievement/ gm/ persistence/ config/
│   ├── config.json / _attr_data.json / _chengjiu.json / _guaji.json …
│   ├── game.db / world/ state/roles.db
│   └── backup/replay_before.json  ← battle_replay 字节锚点
├── analysis/
│   ├── PHASE0_AUDIT.md            ← 全量审计报告
│   ├── client_server_matrix.md    ← 124 系统需求矩阵
│   ├── systems_master.md/json     ← 系统百科（124 系统）
│   ├── unimplemented_systems.md   ← 42 项未实现
│   ├── version_compare/          ← 三版本差异矩阵
│   ├── persistence_down_sink.md   ← 下沉设计
│   ├── battle_register_design.md  ← 20002 注册设计
│   ├── aoi_battle_down_sink.md
│   ├── afk_push_design.md
│   ├── calibrated_ui_coords.md    ← 实机 UI 校准坐标
│   ├── d2_render_fix.md / d2_rootcause.md  ← 背包渲染问题
│   ├── runtime_evidence/shots/  ← 实机截屏
│   │   └── user_assist/          ← 用户协助证据（修炼面板/符文面板）
│   └── extraction/
│       ├── truth_values.md/json  ← CONFIRMED 真值
│       ├── gap_dig.md/json       ← 缺口深挖
│       ├── ui_display_values.md   ← UI 显示值证据
│       ├── xiulian_frame_spec.md ← 修炼帧规格
│       ├── patrol_button_spec.md
│       ├── afk_enter_verify_report.md
│       └── monster_values.md
├── tests/1.4.11/
│   ├── FINAL_REGRESSION.md        ← 最终回归+缺口清单
│   └── regression_baseline.md     ← 每批回归记录
├── patched/                       ← 1.4.11 补丁包
├── anzbao/                       ← 3 原版 APK
├── _tmp_cfg/                     ← 1.4.11 配置提取（305 文件）
└── cankao/                       ← 5 个参考项目（仅架构参考，禁用其数值/协议）
```

## 八、当前进行中的工作（交接点）

**practice_exp 二次回证**：
- 已改 `mock_server.py` ROLE_DEFAULTS 与 SC_10304 编码器，practice_exp 从修炼状态动态读取=35
- server 已重启，客户端自动重连后需用户打开 **更多→魂技→修炼** 面板截图确认"拥有"栏是否显示 35
- 若仍空白 → 说明消耗/拥有栏读另一独立帧（非 practice_exp），继续 luac 定位 xiulian 帧扩展字段
- 若上屏 → 修炼栏闭环，更新 FINAL_REGRESSION.md 缺口 #5

## 九、下一步推荐顺序

1. **practice_exp 二次回证**（见上）
2. 宝石镶嵌 CS 命令取证 → 接通"镶嵌→总属性表→AttributeService→PowerService"完整闭环
3. 修炼进度条"50"配置源继续 luac（五表全查不匹配，可能客户端归一化缩放）
4. 获得伙伴后实机喂养取证（补缺口 #2）
5. 挂机场景下观察巡逻按钮（补缺口 #6）
6. 真服若恢复，按 gap_dig.md 清单补怪物/伙伴喂养/宝石真值

## 十、参考项目使用纪律

`cankao/` 下 5 个项目（Survive/kongkongxiyou/CXEngine/YZXY/MahatmaComeBack/ChivalrousMan）**只借架构设计**，协议/数值/任务/装备/技能/怪物/属性/战斗规则一律不得当 JSTM 数据。最高标准永远是 JSTM APK + 资源 + 协议 + 实机运行。

---

## 十一、C4 批次（2026-10-16）—— GM 后台 + 服务端缺陷修复

> 完整报告：`docs/C4_实施记录与回归报告.md`；部署指南：`docs/C4_下载安装与私服部署指南.md`

### 11.1 新增：GM 后台管理系统

浏览器打开 **`http://127.0.0.1:8080/GM`**（11 页签：总览/角色/资产/物品/邮件/任务/场景副本/养成/审计/配置/高级调用）。

- 实现：`server/gm/console.html`（单文件 SPA，零构建零依赖）+ `server/gm/console.py`（路由与聚合），
  由 `mock_server.py::Handler.do_GET` **顶部一行**接入，**不另起服务**。
- 鉴权：写操作校验 `DSH_GM_TOKEN`（缺省 `dshgm`）；只读端点沿用无鉴权现状。
- 静态校验：`node tools/_gm_console_lint.js server/gm/console.html`

### 11.2 新增端点

```
GET /GM                                后台管理页面
GET /GM/api?act=overview|roles|rolecard|online|gmlog|token
GET /DSH_ADMIN/roles|accounts|online|gmsessions|gmlog|rolecard|rolemail
GET /DSH_ADMIN/setscene?rid=&scene=&x=&y=&token=   ★ GM 传送（写库 + 同步 _last_enter + 推 10200/10201）
```

### 11.3 修掉的**真缺陷**（都有实机/日志复现证据）

| ID | 缺陷 | 根因 | 影响 |
|---|---|---|---|
| D1 | 移动校验恒用 10001 的 MapBlock | `_current_bid()` 只读 `cfg['spawn']['bid']` | 切图后合法坐标被判"不可走"、被拽回并落库 |
| D2 | 登录恒进 10001 | 10102 写死 `spawn.bid` | 挂机图/副本/GM 传送**一重登即丢** ⇒ 私服只有一张图 |
| D3 | 10300 补推 10200 用 `spawn.bid` | 同上 | 客户端每次场景初始化就被拽回旧图，当场撤销切图 |
| D4 | 10933/10934 分发遮蔽 | 旧元组残留死条目 | 门禁报错；同类隐患曾遮蔽 15403 |
| D5 | 下发的 `url_config` 是探针 | 诊断版覆盖生产版 | **全新安装**客户端会抛 `get_servers_url` 未定义并中断登录界面 |
| D6 | miniloop flaky（139–143 波动） | 测试侧 `recv_all` 空档 0.15s 太短 | 门禁不可信 |
| D7 | c1_e2e 12402 断言写错 | 测了服务端明确不提供的语义 | 长期误报 FAIL |

**关键修复点**（改 `mock_server.py` 前必读）：
- `_current_bid(handler)` **优先取 `handler._last_enter[0]`**（每连接实际进图），无记录才回退 spawn。
- `login_scene_bid(cfg)`：登录进场景优先读**存档 `roles.scene_id`**，校验在 `config_map` 内，否则回退 spawn。
- **用 `push_to_rid` 推 10200 时，必须同时同步目标连接的 `_last_enter`**，否则校验仍按旧图。

### 11.4 回归基线（本批终值，改代码后按此对照）

| 门禁 | 结果 |
|---|---|
| `python server/minloop/selftest.py` | **145/145**（去 flaky 后连跑 2 次一致） |
| `python tools/c1_e2e_closed_loop.py` | **PASS=21 / FAIL=0 / NOT_RUN=1** |
| `python tools/c4_scene_e2e.py` | **12/12 PASS** |
| `python tools/lint_dispatch_shadow.py` | **✓ 无分发遮蔽** |
| `node tools/lua-check/check.js server/url_config_ewan.lua` | **OK** |
| `node tools/_gm_console_lint.js server/gm/console.html` | **OK** |

### 11.5 实机结论（MuMu + 1.4.11 `com.shiyue.dldl.ewan.baidu2`）

- **HUD/底部导航正常渲染**（C3.3 报的"HUD 不渲染 BLOCKER"本轮**不可复现**，判为客户端偶发渲染态）。
- GM 传送实测：10001 史莱克城 → 10005 乾坤日月谷 → 10010 → 10002 星斗大森林，**画面均正确跟随**。
- **重登保持存档场景**已验证（修复 D2 前必被拽回史莱克城）。
- ⚠ `server/url_config_ewan.lua` **已是生产版**，不要再拿探针版覆盖它。

### 11.6 不要做的事

1. 不要用诊断探针覆盖 `server/url_config_ewan.lua`（会丢 URL 全局，只在老机器上被缓存掩盖）。
2. 不要把 `10933/10934`（或任何命令号）同时放进"专用分支"和"通用族"元组（用 `lint_dispatch_shadow.py` 把关）。
3. 不要用 `push_to_rid` 推场景帧却不更新 `_last_enter`。
4. 不要为跑通测试而放宽服务端校验（D7 是**测试**写错，服务端是对的）。
