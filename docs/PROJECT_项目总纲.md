# 《绝世唐门》1.4.11 私服复原工程 · 项目总纲

> **文档性质**：全项目**总纲与唯一入口**。汇总项目内容、目标、成果、问题、技术架构、复原进程、未来计划。
> **编写方式**：通读仓库内 1197 个 `.md` + 289 个 `.txt`（含 `docs/` 71 份、根目录 21 份、`report/` 109 份、`analysis/` 及其子目录、`docs_raw/` 9 份、`tests/`），并交叉核对**当前实际代码与运行中的服务端**。
> **证据纪律**：沿用项目五档 **CONFIRMED > VERIFIED > STRONG_INFERENCE > INFERENCE > UNKNOWN**。本文档**不新造数值**；凡文档间冲突，一律在 §6.4 如实并列，不擅自取舍。
> **日期**：2026-10-16

---

## 一、项目内容与定位

### 1.1 一句话定位

> **不是"做一个类似绝世唐门的服务器"，而是"做一个能让原版《绝世唐门》APK 继续运行的兼容服务器"。**

客户端 APK **一行 UI 都不重做**，全部工作量集中在**服务端**。最终形态 = 原版 APK（MuMu 模拟器运行）+ 自建 `mock_server`（PC 上的 Python 单进程）。

### 1.2 三个 APK 与选型

| 包 | 文件 | 大小 | 包名后缀 | 渠道 | NOW_VERSION | 角色 |
|---|---|---|---|---|---|---|
| 1.3.0 | `anzbao/dldlJl.apk` | 135.8 MB | ewan·91CW | — | 35 | SDK 行为参考（纯 Java、弹窗明文） |
| 1.4.9 | `anzbao/jstm.apk` | 230.5 MB | `.qihoo` | 360 | 186 | **早期主攻版本**；协议/数值主要取证源 |
| **1.4.11** | `anzbao/jstm_142165.apk` | 267.8 MB | `.baidu2` | 百度 | 208 | **★ 现行目标版本** |

**为什么选 1.4.11**（`三包对比与选型.md`）：资产完整度决定宿主 ——

| 指标 | 1.3.0 | 1.4.9 | **1.4.11** |
|---|---:|---:|---:|
| APK 条目 | 10,670 | 16,379 | **19,106** |
| `.luac` 总数 | 1,557 | 2,234 | **2,297** |
| `config_*.luac` | 168 | 227 | **233** |
| `cmd_resolve_*.luac` | 89 | 122 | **124** |
| assets 字节 | 135.1 MB | 241.3 MB | **276.2 MB** |

1.4.11 相对 1.3.0 新增 **31 个 game 模块**、**66 张 config 表**。另两包少 1/3 Lua、近半资源（当年靠**已下线 CDN** 热更补全）⇒ 只有 1.4.11 能离线跑全量内容。

主用产物：`patched/jstm_1411_fakelogin_aligned.apk`（包名 `com.shiyue.dldl.ewan.baidu2`，versionCode 46）。

### 1.3 已安装的三包（同一模拟器共存）

MuMu 12 / Android 12，实测：

```
com.shiyue.dldl.ewan          → 1.3.0   （参考）
com.shiyue.dldl.ewan.qihoo    → 1.4.9   （参考）
com.shiyue.dldl.ewan.baidu2   → 1.4.11  ← 主用
```

---

## 二、目标与范围

### 2.1 总目标

**用原版 1.4.11 客户端 + 本地 `mock_server`，尽可能恢复原游戏完整玩法闭环，并完成私服化（含 GM 后台）。**

### 2.2 七条红线（贯穿始终，违反即返工）

来源：`docs/HANDOVER_移交给另一个agent.md` §一、`docs/SUMMARY_私服化总结.md` §二。

1. **原版 APK 是最终标准** —— 与任何参考项目冲突时，APK 优先
2. **不猜协议** —— 字段必须标 CONFIRMED / VERIFIED / INFERENCE / UNKNOWN
3. **参考项目只作架构参考**，禁止改名复制（5 个项目代码**全部不可复制**，其中大圣归来是 GPL-3.0、Survive 的 `aoi.h/astar.h/wordfilter.h` 文件头内嵌 GPLv3）
4. **不重做客户端 UI**、**不自己发明协议**
5. **只操作自己的服务器**
6. **不编造数据** —— 无原版依据的数值一律标注"占位，待校准"或 `[TEST_ONLY]`
7. **被否证的假设保留记录，不删**

### 2.3 明确不做（`docs/RESTORE_各模块复原设计方案.md` §九）

- 婚宴 / 情缘、社交好友圈、宗门战 / 竞速 / 跨服
- 剩余 3 个排行榜
- D 类 **8 个 1.4.11 已移除界面**（`garden` / `jingjie` / `moneytree` / `xiulianhulu` / `glz_main_ui` / `friend_view` / `mail_panel` / `libao_view`）
- **27 条仅图标证据的运营活动**

---

## 三、技术架构

### 3.1 总体形态

```
┌──────────────────────────────────────────────────────────────┐
│  原版客户端 APK（Cocos2d-x 3.6 + LuaJIT 2.0 字节码）           │
│    assets/src/game/**/*.luac     2297 个（1.4.11）            │
│    assets/src/config/**/*.luac    233 张（1.4.11）            │
│    + 注入 dsh_fake_login.lua（自供 SDK 回调与本地地址）         │
└────────────────────────┬─────────────────────────────────────┘
                         │ 真实协议 [u32 BE len][u16 BE cmd][body]
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Protocol Adapter：server/mock_server.py                      │
│    Decode → cmd 分发 → 业务 → 状态变更 → Encode                │
│    专用分支 1430 条 ｜ 兜底集合 0 ｜ 未开放集合 0               │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Game Core（40 个包）                                          │
│  account role scene(+AOI+寻路) task battle item inventory      │
│  equipment enhance gem skill partner wing soulbone fashion     │
│  amplification artifact destiny formation dungeon afk shop     │
│  currency package activity reward social guild ranking mail    │
│  achievement gm persistence config monster power drop session  │
└────────────────────────┬─────────────────────────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  Persistence：SQLite `server/state/roles.db`（**64 张表**）    │
│  身份→roles ｜ 资产→role_assets ｜ 属性→role_attr              │
│  幂等→reward_log(rid, reference_id)                           │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 客户端侧

| 项 | 值 |
|---|---|
| 引擎 | Cocos2d-x 3.6 + **LuaJIT 2.0 字节码**（magic `1b 4c 4a`） |
| luac 数量 | 2,234（1.4.9）/ **2,297（1.4.11）** |
| 配置表 | 347 张（1.4.9）/ 233 张（1.4.11） |
| 主 Activity | `com.shiyue.dldl.ewan.AppActivity` |
| SDK | ewan SuperSDK（**服务已死**；qihoo/baidu2 被 Bangcle 加密进 `libsupersdkjni.so`） |

**死 SDK 处理（两条路，均已验证）**：
1. DEX 单字节补丁 `EWanSdk.<init>` 的 `is_close=0→1`（`0x61edfd: 00→10`）⇒ 17 个生命周期方法全 no-op；
2. `patch_dex_skip_sdkinit.py` **等长**替换 `SuperPlatform.init()`（主包 `0x6DD87C`；init 索引 主包 13849 / jstm 14403 / dldlJl 14431）。
   ⚠ **不等长替换会触发 ART `VerifyError`**。

另注入 Lua（`server/dsh_fake_login.lua`）自供 `sdkBackInit/sdkBackLogin` 并钩 `cc.Device.beginThirdPartyLogin`。实测 360 SDK 日志 0 条、ContainerActivity 0、crash 0。

### 3.3 服务端侧

| 项 | 值 |
|---|---|
| 语言/依赖 | **Python 3.12，纯标准库，零第三方依赖**（刻意保持，勿引入包） |
| 主文件 | `server/mock_server.py`（约 19–20k 行，随批次增长） |
| 代码规模 | `server/**/*.py` **244 个文件**；`tools/*.py` 764 个 |
| 端口 | TCP **9000**（游戏协议）/ HTTP **8080**（资源 + `/DSH_ADMIN/*` + `/GM`） |
| 客户端视角 | `10.0.2.2:9000` / `10.0.2.2:8080`（模拟器访问宿主机回环） |
| 重连 | 服务端重启后客户端约 11 秒自动重连 |

### 3.4 通信协议（CONFIRMED）

| 项 | 规则 |
|---|---|
| 帧格式 | `[u32 BE payload_len][u16 BE cmd][body]`，`len = 2 + len(body)` |
| 成功判据 | **`code == TRUE(1)` 才算成功**，否则客户端弹 `message(msg)`；**唯一例外 `10200` 要求 `code==0`** |
| 字符串 | `[u16 长度][UTF-8 字节]` |
| 表 | `[u16 项数] + 逐项` |
| ⚠ 脏字节 | CS body **尾部常带 4 字节缓冲区残留**（如 `CS_20002` 实机 8 字节 vs 规格 4 字节）；**只读规格前 N 字节，忽略尾部** |
| 规格来源优先级 | **`AutoConstruct spec` > reader 原型 > 抓包长度**（包长是弱证据，定不了字段个数） |

**协议真源链**：

```
客户端 cmd_resolve_*.luac（124 个）
  → protocol/fields.json            3553 条（CS 1444 / SC 1635 / Dsc* 472）
  → server/proto_defs.py            （由 manual.md/fields.json 解析生成）
  → mock_server / 测试 / 抓包解码器 共用
  + protocol/cmd_table.json         1643 条中文命令名
```

**启动→进游戏链路要点**（`STARTUP_UPDATE_FLOW.md`）：

1. 原生 → `assets/src/main.luac` → `loadConfig()` → **明文 `config.luac` 最先执行**
2. `main()` → `require('sdk_function')` → `require('file_update')` → 因平台登录**停住等 SDK 回调**
3. `sdkBackInit` → `ver_load_start()` → `check_new_version` → `initUpdateScene` + `initConfig`
4. **首个网络请求**：`cc.FmodexManager:downloadOtherFile(URL_LUA_CONFIG?os.time(),'url_config.lua')`
   （原生下载器，非 XHR；失败**无上限 0.2s 重试** —— 实测 45s 内 180 次）
5. `OnFileDownloadResult` 回读 → `loadstring` → `URL_PATH = URL_PATH_ALL:get(PLATFORM_NAME)`（**必须写全局**）
6. `UPDATE_SKIP=true` ⇒ 直接 `update_finish`（旁路热更）
7. `update_finish` → 逐帧 4 个加载 **688 模块** → `beginGame`：`runWithScene` + `DengluCtrl:openView()` + `GAME_INITED=true`
8. 关键命令号：**10001** 首包 → **1199** 心跳（8s，body=当前格子坐标）→ **1110** 账号登录 → **10101** 建角 → **10102** 选角 → **10300** 初始化完毕 → **10200/10201** 服务端主动推 → **10204** 移动

**服务器列表接口**：`POST /gateway/mobile/json` 必须回 `{"data":{"server_list":[…],"default_zone":"1"}}`
（`data` 在顶层内，**不是**顶层 `server_list`）；且 `get_servers_url` / `get_notice_url` **必须是函数**——写成字符串会抛
`attempt to call global 'get_servers_url' (a string value)` 并**中断登录界面构建**。

### 3.5 数据模型（SQLite，64 表）

| 类别 | 表 |
|---|---|
| 身份/资产 | `accounts`、`roles`、`role_assets`、`role_attr`、`role_point` |
| 背包/装备 | `bag_items`、`store_items`、`equip_items`、`bag_volume` |
| 任务/成就 | `missions`、`daily_progress`、`daily_lingqu`、`chengjiu_progress`、`sign_got` |
| 战斗/副本 | `reward_log`、`dungeon_progress`、`role_boss_kill`、`guaji_state`、`arena_state`/`arena_record`、`peakwar_state`、`race_state` |
| 养成 | `role_skills`、`role_heros`、`role_wing`、`role_shenqi`、`role_mingge`、`role_fabao`、`role_lingshou`、`role_ride`、`role_chair`、`role_runes`、`role_halo`(+`_equip`)、`role_yuanshen`、`role_fashion`、`role_buffs`、`role_title`、`role_tree`、`role_build`(+`_learn`)、`role_form`、`role_gt`、`role_invest`、`role_qifu` |
| 社交/经济 | `role_mail`、`role_chat`、`role_friend`(+`_req`)、`role_guild`、`role_team`(+`_invite`)、`role_marry`(+`_propose`)、`role_jiebai`、`role_moments`、`role_market`(+`_goods`)、`mall_bought`、`role_scratch`(+`_tier`)、`levgift_got`、`role_answer` |

**权威口径（重要）**：

- **身份/等级** → `roles`
- **货币/资产** → `role_assets`（**唯一权威**；`roles.gold/diamond` 已**停写**）
- **属性** → `role_attr`（⚠ `AttrLen=64` 但只落 25 列 ⇒ **混存 21 个派生项、漏 39 项**，历史设计缺陷）
- **幂等** → `reward_log(rid, reference_id)` 主键
- 合并序：`ROLE_DEFAULTS ← cfg.role ← roles 行 ← role_assets`（后者覆盖）

### 3.6 核心机制

| 机制 | 实现 | 出处 |
|---|---|---|
| **AOI** | 均匀网格 + 视野集合去重 + 新旧集合**双向差集** + 双向回调；**只产 `(uid,event)`，绝不碰 socket** | **自研**（思想借 Survive `aoi.c`，代码不可复制） |
| **寻路** | A\*（8 邻域 + octile）+ Bresenham 直线快路径 + **禁贴角** | **自研**（思想借 Survive `astar.c`） |
| **安全校验** | **L1 路径校验 + L2 令牌桶限流** | **★ JSTM 原创**（5 个参考项目全部缺失） |
| **战斗** | 服务端**自定节拍 2.5s/回合**（因客户端**从不发** `CS_20011/CS_20014`，实测 4 场完整捕获零次） | CONFIRMED |
| **会话推送** | AOI + 战斗 Timer 全部收敛到 `SessionRegistry.push_to_rid` | C3.1 |
| **奖励** | 一切走 `RewardService.grant(ref)` 幂等；GM 也必须走正式 Service 链路 | §36 硬性要求 |

### 3.7 工具链（逆向）

| 工具 | 用途 |
|---|---|
| `tools/luajit_bc.py` | LuaJIT 字节码解析器（`parse_bytes`） |
| `tools/luajit_dis.py` | 反汇编器：`python tools/luajit_dis.py <apk> <luac路径> <proto#> <起> <数>` |
| `tools/config_deconstruct.py` | **对齐解构器**（补齐 `TSETB/TSETV/TGETB/...` 等指令）→ 配置 luac → JSON |
| `tools/batch_deconstruct.py` | 204 个配置批量解构 |
| `tools/extract_item_v2.py` | 物品表（**按记录自身 bid 建键**，权威） |
| `tools/extract_config_mon.py` / `extract_guaji.py` / `extract_chengjiu.py` / `extract_mission_config.py` 等 | 各配置专项提取 |
| jadx / dexdump / apktool / frida | DEX/APK 反编译与运行时注入 |
| `tools/replay_captures.py` | 真机抓包**回放**并按规格严格解析（自动暴露编码 bug） |
| `tools/lint_dispatch_shadow.py` | 门禁：防"专用分支被通用集合遮蔽" |
| `tools/lua-check/check.js` | Lua 语法硬闸门（打包前必过） |
| `tools/apk_extract_luac.py` | 从 APK 抽 luac |

**frida 通道现状**：host frida-python 17.18.0；MuMu 需 **32 位 `fs-x86`**（游戏是 app_process32），进程名乱码须**按 PID attach**。
**技术墙**：houdini 下游戏 ARM 库不可见（294 模块无 `libcocos2dlua.so`），`lua_*` 符号钩子不可用；但 `Memory.scanSync` 可用。

**Lua 注入通道**（有效）：`print` 镜像 + 自建 XHR `/DSH_REPORT` + `dsh_patch.lua` 热补丁 ⇒ **直接读客户端 Lua VM**（如读出 `Config.SkillXiulianLev`）。
⚠ **注入会破坏联调启动流程**（`error网络异常` / 下载重试循环），需用原 fakelogin APK 恢复。

---

## 四、复原进程（分期）

> 各期是**独立的审计/实施阶段**，不是版本号。

| 期 | 主题 | 主要产出 |
|---|---|---|
| **C0** | 只读客户端审计 | `systems_master.json` **124 系统**、`ui_inventory.json` **391 界面**、`protocol_inventory.json` **1707 条** |
| **C1** | 系统恢复总纲 | 124 系统 A–F 分类 + 依赖/优先级 + 接口需求 + 首个闭环立项 |
| **C2** | 界面恢复台账 | **401 界面**八态长期台账 + 导航 32 条 + 依赖映射 24 行；分片 C2.1 基础（35）/ C2.2 养成（19）/ C2.3 玩法与内容（27）/ C2.4 完整性验收 |
| **C3** | 三大系统深挖 | C3.1 角色数据与持久化（11 条问题 + 26 条台账）／C3.2 任务系统（状态机 + 14 项 E2E，判定 **PARTIAL**）／C3.3 战斗调用链审计 |
| **S1/S2/S3** | 服务端修复与加固 | S1 链路补推 5 处；S2 三项（10650 天赋 / 钻石 / 11215）；S3 五项加固（含负数校验、gm.log 审计挂钩、幂等门控） |
| **C4** | **1.4.11 落地** | 部署指南 + **GM 后台管理系统** + 3 处场景根因修复 + 分发遮蔽清理 + 回归去 flaky |
| **C5** | **剩余缺口攻坚** | `kill_type_mon` 类型字段取证 + 接线；`use_item`/`consume_item` 接线；`12414` 对话推进；离线挂机收益机制；装备面板根因定案 |

### 4.1 C4 批次要点（2026-10-16）

**新增 GM 后台管理系统** —— 浏览器打开 `http://127.0.0.1:8080/GM`

- 11 页签：总览 / 角色管理 / 资产·等级 / 物品发放 / 邮件 / 任务 / 场景·副本 / 养成系统 / 审计日志 / 配置表 / 高级调用
- 实现：`server/gm/console.html`（单文件 SPA，零构建零依赖）+ `server/gm/console.py`（路由与聚合），由 `mock_server.py::do_GET` **顶部一行**接入，**不另起服务**
- 鉴权：写操作校验 `DSH_GM_TOKEN`（缺省 `dshgm`）；只读端点沿用无鉴权现状（内网私服）
- 新增 **`/DSH_ADMIN/setscene` = GM 传送**（写库 + 同步 `_last_enter` + 推 `10200/10201`）

**修掉的 3 处场景真缺陷**：

| ID | 缺陷 | 根因 |
|---|---|---|
| D1 | 移动校验恒用 10001 的 MapBlock | `_current_bid()` 只读 `cfg['spawn']['bid']` |
| D2 | 登录恒进 10001 ⇒ **私服只有一张图可玩** | 10102 写死 `spawn.bid` |
| D3 | 10300 补推 10200 用 `spawn.bid` | 客户端每次场景初始化就撤销切图 |

**其他**：`10933/10934` 分发遮蔽清理；`server/url_config_ewan.lua` 被**诊断探针版覆盖**（丢失全部 URL 全局，新装/清数据必崩）→ 恢复生产版。

### 4.2 C5 批次要点（2026-10-16，本次）

| 缺口 | 结论 | 证据等级 |
|---|---|---|
| `kill_type_mon` 类型字段 | **`Config.Mon.fields[4]`**，码 8=狂暴魂兽（15 只怪同名）、码 12=邪魂师族（21 只） | **CONFIRMED**（三重：配置自证 + 任务名自证 + 客户端 `mission_util` 文案 `'击杀%s/%s只狂暴魂兽'`） |
| `use_item`/`consume_item` | 触发点 = **CS_10505（使用物品）**，target = 物品 bid | CONFIRMED（配置 21+16 条 + 10505 协议） |
| `12414` 对话推进 | `accept_talk`（34 条中 **33 条未 auto_accept**）⇒ **接取**；`process_talk` 无 progress 语义 | CONFIRMED（客户端 `talkHandler` 反汇编 + 配置统计） |
| 离线挂机收益 | **速率表在客户端侧根本不存在** ⇒ 保持占位；机制已打通（配置化速率 + 幂等结算） | 收益真值 **UNKNOWN**；机制 VERIFIED |
| 装备面板 "+" 占位 | **客户端侧**：`role_equip_cell.putOnEquip()` 未被调用；面板未绑定 `GET_ALL_DATA`。服务端数据 6/6 正确 | CONFIRMED（反汇编 + 实机 + DB 交叉） |

---

## 五、成果

### 5.1 规模数字（当前实测）

| 维度 | 数值 |
|---|---:|
| 识别系统 | **124** |
| 登记界面 | **401** |
| 协议字段定义 | **3553** 条（CS 1444 / SC 1635 / Dsc* 472） |
| 已知 CMD | **1634** |
| 专用分支 | **1430**（兜底集合 0、未开放集合 0） |
| 服务端模块 | **40 个包** / 244 个 `.py` |
| DB 表 | **64** |
| 配置资产 | 物品 **3535** / 任务 **846** / 商城 **134** / 礼包 **496**+5353 映射 / 成就 **342** / 称号 175 / 伙伴 **53** / 活动 74 / 挂机点 8 / 地图 **124** / 碰撞 26 |
| 服务端行数 | `mock_server.py` 约 **19–20k 行** |

### 5.2 服务端成熟度评估（历史评分轨迹，**以 1.4.9 为准**）

| 报告 | 日期 | 评分 | 要点 |
|---|---|---:|---|
| `report/jstm_privateserver_maturity.md` | 09-17 | **6.9/10** | 硬阻塞 = 进不了场景 + 战斗画面不渲染；"垂直可行、全量未成" |
| `report/jstm_privateserver_maturity_update.md` | 09-17 晚 | **7.65/10**（结论段又写 7.2，**自相冲突**） | **推翻**"进不了场景"（`10201 npcs=26 mons=1`、NPC 上屏）；战斗数据链全通 |
| `report/privateserver-maturity-20260919/` | 09-19 | **8.0/10** | 真机协议覆盖 **128/128**；服务端 116+ 命令在线；NPC 对话 14 轮闭环 |

> ⚠ 三份评分均基于 **1.4.9**，**不能直接当作 1.4.11 的评分**。

### 5.3 已闭环玩法链（实机 + 脚本双证）

**一条完整垂直链**：
```
登录 → 角色 → 建角/选角 → 进场景 → NPC 对话 → 任务（接取/推进/提交/发奖/链推进）
  → 战斗（回合制 settle）→ 奖励（幂等）→ 背包/装备/仓库 → 商城（真扣费发货）
  → 邮件 → 排行榜 → 副本 → 挂机 → 签到/日常/成就 → 伙伴/技能/翅膀/神器/命格/法宝/坐骑/灵兽/元神/椅子/时装/光环/符文/投资/BOSS/称号/阵法书
```

**协议对接已实质收口**：

| 审计项 | 结果 |
|---|---|
| CS 规格审计 | 2463 条，**0 不一致** |
| SC 静态审计 | 1635 条，**0 不一致** |
| SC 在线审计 | 101 条，**全一致** |
| 真机抓包回放 | 231 命令 / 876 变体 ⇒ **符合 831 / 不符 0** |
| "有 SC 却无应答" | **73 → 8**（余 8 条经取证客户端**根本没有处理器**） |

### 5.4 已确认关键真值（CONFIRMED）

#### 协议/状态机

| 项 | 真值 |
|---|---|
| 线格式 | `[u32 BE len][u16 BE cmd][body]`，len 含 cmd 2 字节 |
| 成功判据 | `code==1`；**唯一例外 `10200` 要 `code==0`** |
| `bag_code` | **1=主背包 / 2·3=装备栏 / 4=仓库** |
| 奖励 code | **2=coin、4=exp、15=hero_exp** |
| 任务状态机 | **0=可接（不落库）/ 1=进行中 / 2=条件满足可提交 / 3=已完成** |
| `SC_12400` 任务条目 | **34 字节**，13 字段（`mission_bid, mission_status, commit_num, loop_count, loop_num, code, process_status, target, target_value, value, show_lave_time, lave_time, accept_time`） |
| `SC_10303.attr` | **结构体表**（`u16 计数 + 4×u16 + 20×u32`），**非平铺 u32** |
| `SC_10301` | 122 B，**无 power / 无 attr** |
| `SC_10306` | 88 B，`attr + mspd + power` |
| `SC_11215` | 去 2 字节前缀后 2552 B / **53 条伙伴**（`volume` 前缀属 11200/11206） |
| 战斗链路 | `CS_20002 → SC_20010 → SC_20012/20013 → SC_20020`；**客户端从不发 20011/20014** |
| `SC_20013.magic_list[]` | **buff 载体**（6 字段，含 `duration`）；`specials[]` 是伙伴外观通道 |

#### 货币/资产（实机双向印证）

| 服务端字段 | 客户端界面名 |
|---|---|
| `gold`（code 1） | **钻石** |
| `coin`（code 2） | **银魂币** |
| `coupon`（code 3） | **金魂币** |
| — | `diamond` **无对应 code**；商城 💎 位实际扣 `gold` |

#### 属性/战力

- `AttrLen = 64`；**战力 = Σ(属性值 × AttrPower)**
- 权重：**atk_speed 450**、dodge/hit **275**、crit/tenacity **183**、atk_s/atk_p **106**、control/anti_control **90**、def_abs/atk_abs **82**、百分比类 **41**、def_s/def_p/red_def_* **33**、**hp_max 24**
- 101–104（strength/intellect/armor/constiution）是**唯一输入项**

#### 数值真值

| 系统 | 真值 |
|---|---|
| 强化成功率 | L1=**100%**、L2=**85%**、L3=**75%** |
| 强化消耗 | L1=**2400 金币** + 强化石 bid **36006**；每级 +2000 |
| 签到 | Day1 = **银魂币 250000** + VIP exp 2；Day2 = 物品 36500×10；Day7 = 36500×15（原占位 1000/5000 **严重低估**） |
| 首杀掉落 | **20012→1001**、**20024→1002**、**30005→1011** |
| 技能点金币 | L1=10 → L10=100（每点 +10） |
| 修炼学习 | 攻击修炼 bid 10101 学 86 exp；物防/法防各 43 exp |
| 修炼升级 | L1→L2 = **402** exp，L2→L3 = **852** exp（192 级曲线） |
| 成就 | **342** 条 |
| 伙伴曲线 | `PartnerLevUp` **201 条**；`max_level=200`、`max_exp=1,908,497,990` |
| 角色经验表 | **200 级**（L70=2,577,419；L200=1,917,555,775） |
| 宝石 | `ItemMiscAttrJewel` 总属性表（L3=12 孔 / L5=18 / L7=24 / L10=24）；合成 `ItemRoleFuse` **192 条** |
| 挂机区域 | `GuajiInfo` **8 区**（星斗大森林 25–34 … 魂殿遗迹一层 75–84） |
| 任务奖励 | 10020 = coin+1290 / exp+500 / hero_exp+500（与配置逐项一致） |

#### 实机基线（rid=1001）

```
level 70 ｜ power 724112 ｜ scene 10001 (44,68)
gold 1799942 ｜ diamond 100000 ｜ coin 9923249 ｜ coupon 99999999 ｜ exp 20689 ｜ hero_exp 9800
背包 7 件 ｜ 装备 6 件（40003/41803/41403/41603/41003/41213）
```

### 5.5 回归门禁（当前全绿）

| 门禁 | 命令 | 期望 |
|---|---|---|
| 协议自检 | `python server/minloop/selftest.py` | **145/145** |
| 闭环 E2E | `python tools/c1_e2e_closed_loop.py` | **PASS=21 / FAIL=0 / NOT_RUN=1** |
| 场景 E2E | `python tools/c4_scene_e2e.py` | **12/12** |
| 条件事件 E2E | `python tools/c5_cond_e2e.py` | **16/16** |
| 离线开关 E2E | `python tools/c3_3_offline_toggle.py` | **10/10** |
| 分发遮蔽 | `python tools/lint_dispatch_shadow.py` | **✓ 无分发遮蔽** |
| Lua 语法 | `node tools/lua-check/check.js <file>` | OK |
| 控制台静态 | `node tools/_gm_console_lint.js server/gm/console.html` | OK |

---

## 六、问题

### 6.1 阻塞分类（关键结论）

> **所有剩余缺口，无一属"工时不够"，全部卡在证据。**（`FINAL_REGRESSION.md` §附二、`analysis/INDEX.md` §3）

| 类别 | 项 | 需要的途径 |
|---|---|---|
| **需实机（MuMu）** | 巡逻按钮激活条件、`chengjiu_has.state` 语义、`16605`/`10924`/`16903` 取值语义、装备帧字段偏移、宝石镶嵌 CS 帧 | 实机抓帧 + Lua 注入探针 |
| **需真值** | **怪物 HP/ATK**（配置无显式值）、**伙伴基础喂养消耗**、**宝石单件加成**、**伤害公式系数**、**挂机收益速率** | 真服抓包（**已确认不可达**）或反编译官方服务端（**无产物**） |
| **需客户端改动** | 面板首帧战力 0、装备格 `putOnEquip` 未调用 | 客户端 luac 或注入脚本 |
| **已收口** | 2 项 | — |

### 6.2 已修复的缺陷（择要）

| 缺陷 | 根因 | 状态 |
|---|---|---|
| **NPC 对话 13 轮未闭环** | 服务端下发了**不存在的技能 bid `1001`**（客户端真实 bid 是 10000/10001/10002）⇒ `kHaveSkill` 索引 nil 抛异常 ⇒ `changeScene` 中断 | ✅ 修复（用户实机确认） |
| 每 2.5s `TypeError` 刷屏 | `.get(k, default)` 对"存在但值为 None"的键返回 None | ✅ |
| 背包↔仓库覆盖 / 物品丢失 | `db_store_add` 按 bid 合并 + `MAX(item_id)+1`；`bag_put_one` 签名缺 `cfg` | ✅ |
| 背包空白 | 10 件 bid 不在物品表内（旧表仅 1117 条） | ✅ |
| 签到无法领取 | `SC_14101` **少发 `assets`/`items`**（5→24 字节） | ✅ |
| 摇钱树次数不变 | `17801` 只回 `{code,msg}` | ✅ |
| 黑市空列表 | 未填商品 | ✅ 填 21 条真实商品 |
| 进图崩（925 次/分重登） | `SceneModel:__init` 在 `Config` 只加载 18 键时执行 ⇒ `map_block=nil` 永久保留 | ✅ v67 |
| `10554` 少 4 字节 / `12832` 字段宽度错 / `13340` 截断 / `10304` 大包错位 | 编码与 AutoConstruct 规格不符 | ✅ 6 项，回放审计"规格不符 11→0" |
| **战斗 exp+掉落不在幂等门内**（可反复刷同怪） | C3.3 发现 | ✅ C3.3 修复（统一进 `reward_log` 门） |
| 场景 3 处根因（C4） | 见 §4.1 | ✅ |
| `10933/10934` 分发遮蔽 | 旧元组残留死条目 | ✅ |
| 下发配置被探针覆盖 | 诊断版覆盖生产版 | ✅ |
| `setmissions` 写死 `target=0` ⇒ 条件任务无法推进 | GM 端点未按配置播种 | ✅ C5 |
| miniloop flaky（139–145 波动） | 测试侧 `recv_all` 空档 0.15s 太短 | ✅ 稳定 145/145 |
| `c1_e2e` 12402 误报 FAIL | 断言测了服务端**明确拒绝**的语义 | ✅ 21/0/1 |
| `c3_3_offline_toggle` flaky（7/10） | 测试自己把 `updated_at` 写成"此刻"⇒ 必被频率门拦 | ✅ 稳定 10/10 |

### 6.3 未闭环项（诚实台账）

| 项 | 状态 | 说明 |
|---|---|---|
| **综合战力面板首帧 = 0** | 客户端侧 | HUD 正确（724112）；面板读 `RoleVo.power`，客户端 `display_panel` 的快照+门控（`role_vo.bid==event.bid` 对自我恒不通过）⇒ 服务端**已无帧可补** |
| **装备面板 "+" 占位** | 客户端侧 | C5 定案：`putOnEquip()` 未被调用 + 面板未绑定 `GET_ALL_DATA`；服务端数据 6/6 正确 |
| **修炼消耗/拥有 EXP 栏空白** | 半通 | 服务端已穷举（10302/10303/10304 均带 `practice_exp=35`）；`SC_10305` 是**死代码**（客户端从不请求） |
| 怪物 HP/ATK | **UNKNOWN** | `config_mon` 只有元数据 + 缩放系数（idx21: 0.7–15.0x），公式在服务端 |
| 挂机收益速率 | **UNKNOWN / 表缺失** | 客户端配置集（1.3.0+1.4.11 字节码、355 条 APK 配置清单、5 份 guaji 变体）**均无收益字段**；服务端 200金/100经验/分钟是**硬编码占位** |
| 离线挂机时长上限 / `10931` 语义 | UNKNOWN | 需真服 |
| 伙伴基础喂养消耗 | UNKNOWN | 全部 partner 表无该字段 |
| 装备基础属性（+0 白装） | UNKNOWN | `item_config` 无 atk/def 字段 |
| 怪物坐标 `Map[*].mons` | **全表为空** | ⇒ `fight_mon`/`collect_elem` 无法寻路 |
| `kill_type_mon` 可达性 | 已接线但**无处可打** | 类型 8/12 的怪（60154–60243 / 81030–81165）**不在任何场景的 mons 表**中 |
| 8 类条件事件源 | 未接 | `submit_item` 102 / `kill_scene_mon` 83 / `use_item` 21 / `consume_item` 16 / `use_item_scene` 5 / `broadcast_drama` 3 / `move` 3 / `collect_elem` 2（部分已在 C5 接通） |
| 缺失 handler | 未实现 | `12404/12411/12412/12413/12415/12416/12417/12418` |
| 账号/会话层 | **完全不存在** | `1110` 角色列表来自 `config.json`，不查 `roles` 表 |
| 属性表设计缺陷 | 未重构 | `AttrLen=64`，`role_attr` 只落 25 列 |
| 战斗画面是否渲染 | UNKNOWN | — |
| 客户端不发 `10102/10103`（1.4.9 侧） | **已判 blocked** | Lua 层发送全成功，服务端收不到；丢失点闭口于 `UserMsgAdapter:Send` 原生层；frida 两次**自证为盲** |
| 完全离线单 APK | **未达成** | 依赖 PC `mock_server.py`；"单机内置服务端"路线停在登录/选服 |
| 横向系统 | 大面积留白 | 公会/拍卖/结婚/跨服/地下城 |

### 6.4 ★ 文档间冲突清单（**必须按此表避免误引**）

| # | 冲突点 | 各种说法 |
|---|---|---|
| 1 | **主版本基准** | `C1/C2/C4/tests` = **1.4.11**（baidu2）；`ARCHITECTURE/TECHNICAL/SUMMARY/HANDOVER/根目录/phase02/report` = **1.4.9**（qihoo）；`S1/C3.1` 又把 baidu2 写成 1.4.9。**三名并存，两套"当前状态"不可混用** |
| 2 | 配置表数 | 347（1.4.9）/ 355（142165）/ 256（dldlJl）/ 233（1.4.11）。（历史任务书里的"346"在任何文档中都**未出现**） |
| 3 | SQLite 表数 | 11 → 19 → 48 → 64 → 66（口径随轮次变化） |
| 4 | `mock_server.py` 行数 | 7265 / 8375 / 19310 / 19630 |
| 5 | 综合战力是否闭环 | "未闭环" vs "已闭环" vs "HUD 正确 / 面板首帧 0" —— **三者描述对象不同（HUD vs 面板首帧），需显式区分** |
| 6 | 协议收口程度 | GAP 8 / 专用 155 vs GAP 0 / 专用 1413 vs 1430 |
| 7 | `SC_20010` 字段数 | 18 字段 vs **13 字段** |
| 8 | miniloop 基线 | 145/145 vs 139–140/145 vs 143/145 vs 135/144（C4 已去 flaky 稳定 145/145） |
| 9 | debug 包 HUD 渲染 | "不渲染" vs C4"不可复现，冷启正常" |
| 10 | exp 重复刷取风险 | C3.2"仅 crash 窄窗口" vs C3.3"**确定性**重复刷取"（C3.3 已修正并修复） |
| 11 | 系统状态口径 | `systems_master` 57/57/10 vs `matrix` 60/29/35（C1 Q-01 **已裁定以 matrix 为准**）；C2 八态 310/44 vs 312/39 |
| 12 | `TcpHandler.cfg` 类属性共享 | 旧文档列为缺点；**已由 R45 实例级 cfg 副本解决**（单向订正，未回写旧文档） |

**另外的勘误（已定案）**：

| # | 项 |
|---|---|
| 13 | `ItemJewel` 全 null 是**找错表** —— 真值在 `config_item_misc.EqmJewel`（13 行） |
| 14 | `SC_11215` 的 `volume` 前缀被错挂 —— 实际属 **11200/11206** |
| 15 | `11700`/`11710-11713` 曾被误标"副本 handler" —— 实为**排行榜/聚宝盆** |
| 16 | `15203` 曾记"NPC 交互" —— 实为**元宝兑换宝图** |
| 17 | `HANDOFF.md` §三写 `server/min_loop_server.py` —— 实际是 `server/minloop/selftest.py` |
| 18 | `HANDOFF.md` §四写 registered CS=19 —— `FINAL_REGRESSION.md` 附二已到 **34** |
| 19 | 1.4.11 客户端在服务端是**按登录体长启发式判族**（220B/10 键 ⇒ 判成 "1.4.9"），**不是客户端自述版本号** |
| 20 | `fields.json` 源自 **1.4.9**，其 CS 定义对 1.4.11 **不可靠**（`10922/10924/16903/11300/14000/10527/17200/17800/11200/13321/16664` 等记 0 字段，1.4.11 实测 body=4B）。**正确做法：实机抓包 > fields.json** |

### 6.5 许可合规（红线）

| 参考项目 | LICENSE | 能否复制代码 |
|---|---|---|
| Survive | 无顶层，但 `aoi.h`/`astar.h`/`wordfilter.h` **内嵌 GPLv3** | ❌ 连翻译都有风险 |
| CXEngine / YZXY（原罪西游） | 无 | ❌ 只借设计 |
| MahatmaComeBack（大圣归来） | **GNU GPL v3** | 🔴 **绝对不能**（传染） |
| ChivalrousMan（侠客行） | 无 | ❌ 只借设计 |
| kongkongxiyou（空空西游） | 无项目级（含 **GPL ExtJS 严禁引入**） | ❌ 只借设计 |

**⇒ 5 个项目代码全部不可复制；JSTM 所有实现必须自行编写。**

---

## 七、未来计划

### 7.1 短期（不需新证据，可直接做）

1. **补齐缺失 handler**：`12404`（放弃任务）/`12411`/`12412`/`12413`/`12415`（物品提交）/`12416`/`12417`（伙伴）/`12418`
2. **接通剩余条件事件源**：`submit_item`(102) / `kill_scene_mon`(83，已接线需补实测帧) / `use_item_scene`(5) / `collect_elem`(2) / `broadcast_drama`(3) / `move`(3)
3. **架构债**：`12402/12403/12407/12409/12419/12421` 由 `if` 链迁到 `dispatch` 新链（复用现有校验逻辑）
4. **exp 纳入 `reward_log` 同键**（闭合极窄的重复计 exp 窗口）
5. **GM 后台增强**：把「高级调用」页签补成完整端点目录；加入在线玩家时长/资产曲线

### 7.2 中期（需实机取证）

| 目标 | 手段 |
|---|---|
| 巡逻按钮激活条件 | 实机挂机场景 + Lua 注入探针包 `automate_ctrl` |
| `chengjiu_has.state` 子字段语义 | 同上 |
| 装备帧 `intensify_lev` 真实偏移 / 装备基础属性 | 穿脱装备抓 `10303` 差值 |
| 宝石镶嵌 CS 帧 | 实机操作 + 抓包（协议已知：**10521 镶嵌** / 10522 摘除 / 10530 升级 / 10531 查询） |
| 装备面板 "+" 与首帧战力 0 | 注入探针包 `initEquipData`/`putOnEquip`/`RoleVo.power`，切开"数据没到" vs "UI 没刷新" |
| 1.4.9 侧不发 `10102/10103` | 换原生观测手段（frida hook `UserMsgAdapter:Send` 的 Java 侧）或换客户端实例 |

### 7.3 长期（需真值 / 真服）

| 目标 | 现实评估 |
|---|---|
| 怪物 HP/ATK、伤害公式系数、暴击倍率 | 静态提取**已穷尽**；只能靠**真服抓包**或**运行时打木桩反推** |
| 伙伴基础喂养消耗、宝石单件加成 | 同上 |
| 挂机收益速率 / 离线时长上限 / `10931` 语义 | 需真服 |
| 真服全量数值标定 | **真服大概率已下线**，原版地址被补丁替换 ⇒ 需先确认可达性 |
| 完全离线单 APK（内置服务端） | 路线已验证可行（Lua + LuaSocket，HTTP 18080 / TCP 19000），但停在登录/选服；关键障碍：**引擎在 `config.luac`→登录页期间不给 Lua 任何定时器** |
| 横向系统（公会/拍卖/结婚/跨服/地下城） | 大面积留白，需按 C2.4 的 **48 条待接通业务**逐条推进 |

### 7.4 明确不做（维持）

婚宴/情缘、社交好友圈、宗门战/竞速/跨服、剩余 3 榜、8 个 1.4.11 已移除界面、27 条仅图标证据的运营活动。

---

## 八、附录

### 8.1 关键路径

```
DSH/
├── server/
│   ├── mock_server.py            ← 主服务（TCP 9000 + HTTP 8080，~19k 行）
│   ├── url_config_ewan.lua       ← 下发给客户端的配置（**生产版，勿被探针覆盖**）
│   ├── dsh_fake_login.lua        ← 注入 APK 的本地登录/全局定义
│   ├── item_config.json          ← 物品表（v2 提取器，按记录自身 bid 建键，权威）
│   ├── proto_defs.py             ← 协议定义（由 fields.json 生成）
│   ├── gm/console.py|.html       ← GM 后台管理系统
│   ├── minloop/selftest.py       ← 145/145 协议自检
│   ├── afk/ task/ scene/ ...     ← 40 个业务包
│   ├── cfg/ cfg_kconfig/ ...     ← 配置表 JSON
│   ├── logs/                     ← tcp.log / http.log / gm.log / server.log
│   └── state/roles.db            ← SQLite 存档（64 表）
├── tools/
│   ├── restart_server.ps1        ← 可靠重启（杀干净→自检→启动→冒烟）
│   ├── build_apk.ps1 / build_fakelogin.ps1   ← 改包+签名+安装
│   ├── c1_e2e_closed_loop.py     ← 闭环 E2E
│   ├── c4_scene_e2e.py           ← 场景/GM传送 E2E
│   ├── c5_cond_e2e.py            ← 条件事件 E2E
│   ├── lint_dispatch_shadow.py   ← 分发遮蔽门禁
│   ├── lua-check/check.js        ← Lua 语法门禁
│   └── luajit_bc.py / luajit_dis.py / config_deconstruct.py
├── docs/                         ← 71 份阶段文档（C1/C2/C3/S1-S3/C4 + ARCHITECTURE/TECHNICAL/...）
├── analysis/                     ← 逆向取证主阵地（含 1.4.9/ 260 份、extraction/ 41 份）
├── report/                       ← 109 份成熟度/逐轮报告
├── tests/1.4.11/                 ← FINAL_REGRESSION.md 等
├── patched/                      ← 改包产物 + dsh.keystore
└── anzbao/                       ← 3 个原版 APK
```

### 8.2 常用命令

```powershell
# 环境
adb connect 127.0.0.1:16384 ; adb devices

# 服务端
pwsh tools\restart_server.ps1
(Invoke-WebRequest http://127.0.0.1:8080/DSH_ADMIN/status -UseBasicParsing).Content

# GM 后台
start http://127.0.0.1:8080/GM          # 写操作 Token 默认 dshgm

# 回归
D:\Python\python.exe server\minloop\selftest.py          # 145/145
D:\Python\python.exe tools\c1_e2e_closed_loop.py         # 21/0/1
D:\Python\python.exe tools\c4_scene_e2e.py               # 12/12
D:\Python\python.exe tools\c5_cond_e2e.py                # 16/16
D:\Python\python.exe tools\lint_dispatch_shadow.py       # ✓
node tools\lua-check\check.js server\url_config_ewan.lua

# 改包
pwsh tools\build_fakelogin.ps1

# 最大化重启（构建工具）
D:\Android\SDK\build-tools\34.0.0\{zipalign.exe,apksigner.bat}
```

### 8.3 环境清单（实测）

| 组件 | 路径 / 版本 |
|---|---|
| MuMu 模拟器 12 | `D:\MuMuPlayer`（Android 12，1440×2560@544dpi，横屏 2560×1440） |
| ADB | `D:\ADB\platform-tools\adb.exe` |
| Python | `D:\Python\python.exe`（**3.12.3，零第三方依赖**） |
| JDK | `C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot` |
| Android SDK build-tools | `D:\Android\SDK\build-tools\34.0.0` |
| Node.js | `C:\Program Files\nodejs\node.exe`（v24.20） |
| 签名密钥 | `patched\dsh.keystore`（口令 `123456`，别名 `dsh`） |

### 8.4 文档地图（本项目自有）

| 目录 | 内容 |
|---|---|
| 根目录 21 份 | `HANDOFF.md`、`STARTUP_UPDATE_FLOW.md`、`绝世唐门APK鉴定报告.md`、`三包对比与选型.md`、`自研模拟器路线图.md`、`单机版内置服务端.md`、`enter_game_protocol.md`、`fake_login_patch.md`、各 `*_protocol.md`、`startup_*.md`、`phase02_*.md` |
| `docs/` 71 份 | `ARCHITECTURE_`/`TECHNICAL_`/`SUMMARY_`/`RESTORE_`/`PLAN_`/`HANDOVER_` + C1/C2/C2.1-2.4/C3.1-3.3/C4/S1-S3 全套 + `PROJECT_项目总纲.md`（本文） |
| `docs_raw/` 9 份 | C3.1 协议核验、C3.3 挂机/副本审计、S2/S3 分片报告、面板方案 |
| `analysis/` | 逆向取证（`extraction/` 真值表与缺口、`1.4.9/` 逐系统、`version_compare/`、`jstm_client_audit/`、`runtime_evidence/` 实机证据） |
| `report/` 109 份 | 成熟度评估（6.9 → 7.65 → **8.0/10**）+ 逐轮取证报告 |
| `tests/` | `1.4.11/FINAL_REGRESSION.md`（缺口清单）、`regression_baseline.md`、`RUN_TESTS.ps1` |

### 8.5 三条方法论教训（最有价值）

1. **症状 ≠ 根因** —— NPC 对话 13 轮都在追"场景字段"，真凶在**技能模块**（下发了不存在的 skill bid）。
2. **验证脚本本身也会错** —— 偏移算错、空字节 falsy、`.get()` 对 None 的陷阱 ⇒ **测试失败不等于产品失败，必须先怀疑测试**（本项目已多次因此误报，含 C5 的 12402 与 miniloop）。
3. **分发顺序的遮蔽是系统性风险** —— 新增专用实现时**必须同时把它从通用/兜底集合移出**，否则新代码永不执行（曾遮蔽 `15403`、`10933/10934`）。已建 `lint_dispatch_shadow.py` 门禁。

---

## 九、R1 阶段：客户端全量可检索化（2026-10-16）

> 目标：让 Agent 从**任意界面/按钮/协议/业务系统**出发即可追踪到 Lua 函数、配置、请求、服务端处理与回调，**不必每次重扫 APK**。
> 产出目录：`analysis/r1_client_index/`；生成器：`tools/r1_build_*.py` + `tools/r1_validate.py`（可重跑、幂等）。
> 用法见 `analysis/r1_client_index/R1_Agent检索使用说明.md`。

### 9.1 产出与规模

| 索引 | 规模 |
|---|---|
| `R1_客户端资源与脚本总索引.json` | **46,155** 条（三版本 APK 全量；分片在 `_per_version/`） |
| `R1_UI与按钮调用索引.json` | **401** 界面（**复用 C2 权威 `ui_id`**，只在原表之上增补字段） |
| `R1_协议与字段索引.json` | **1,707** 协议 + 字段 + 断点 |
| `R1_服务端处理映射.json` | **477** 命令号 → `mock_server` / `handler.py` 的**精确行号** |
| `R1_客户端调用链索引.json` | **1,455** 条链（含 8 类断点；**337** 条实机验证过） |
| 四份报告 | 三版本差异 / 解析失败与未知项 / Agent 检索说明 / 覆盖率与质量 |

### 9.2 关键数字

| 项 | 值 |
|---|---|
| 全量条目 | 46,155（1.3.0 10,670 / 1.4.9 16,379 / 1.4.11 19,106） |
| PARSED / BYTECODE_ONLY / UNKNOWN | 40,851 / 5,299 / **5**（分母未剔除未解析项） |
| luac 字节码解析成功率 | 1.3.0 1556/1557、1.4.9 2232/2234、**1.4.11 2295/2297** |
| UI：解析到脚本 / 提取到按钮 / 绑定协议 / 实机验证 | 389 / **372** / 127 / 44（共 401） |
| 脚本差异 | 1.4.11 vs 1.4.9：**+63** 独有、0 移除；vs 1.3.0：**+775** 独有、35 移除 |
| **内容级差异（SHA256）** | 1.4.11 vs 1.4.9：共有脚本 2228，其中 **161 被改**；共有配置表 347，**65 被改**。vs 1.3.0：共有脚本 1516，**1039 被改**；配置表 255，**132 被改** |
| 配置表差异 | 1.4.11 vs 1.4.9：**+8**；vs 1.3.0：**+100**、1 移除 |
| 协议版本分布 | 三版共有 **1337**；1.3.0 无而 1.4.9/1.4.11 有 **370**；**无"1.3.0 有而 1.4.11 无"** |
| UI 模块级线索 | **381/401** 界面可通过 `r1_module_scope_signals` 沿模块找到协议（模块作用域，非界面自身绑定） |

> **内容级差异是本轮新增的关键维度**：只比文件名集合看不出"同名但被改"的脚本 ——
> 1.4.11 与 1.4.9 之间就有 **161 个同名脚本被改动**，跨版本复用时这比"新增/删除"更隐蔽。

> **UI 索引最大的增量**：C0 台账里 338 个界面写的是 `buttons_interactions: UNKNOWN`，
> R1 从字节码里提取出 **372/401** 个界面的**真实按钮标识**与 **127** 个界面的协议绑定。

### 9.3 校验（40/40 PASS）

产物结构完整性 + 4 份报告 + **13 类检索场景实跑** + C2 权威总表未被改动（259,957 B 未变）
+ `protocol/fields.json` 未被改动（提取时只写 R1 目录） + 服务端行号抽样核对 **9/9 一致**。
校验器：`tools/r1_validate.py`。

### 9.4 R1.3 补充（四项收尾，2026-10-16）

| 项 | 产出 | 关键结论 |
|---|---|---|
| **字段级协议差异** | `R1_字段级协议差异.json` | 类数 **1.3.0 2279 / 1.4.9 3553 / 1.4.11 3685**；命令号 **1155 / 1740 / 1791**。★ **1.4.9↔1.4.11 线协议几乎一致**（3553 共有类中 **3540 逐字相同**），差异集中在**新增 132 类 / 51 命令** ⇒ 1.4.9 字段表对 1.4.11 的**已有类基本可用** |
| **未解析界面归因** | （并入 UI 索引 `r1_unresolved_class`） | 37 个"模块名解析不到"逐条回 C2 核对：**28 按名动态分派 / 8 已从 1.4.11 移除（D 类）/ 1 源头 UNKNOWN / 0 未分类** ⇒ **真实提取失败 = 0** |
| **持久化精确化** | `R1_服务端持久化映射.json` | 邻域扫描 → **按处理函数体三路证据**（SQL 文本 / `db_*` 映射 / 字面量表名）。有表关联的命令号 **326 → 217**；**161 个是纯假阳性**（邻域跨到相邻 handler），另有 **52 个被旧口径漏掉**；**54/64 表可反查** |
| **函数级调用图** | `R1_函数级调用图_{1.3.0,1.4.9,1.4.11}.json` | **6,088 个 luac / 111,063 个 proto / 25,917 个被调名**；反向索引可查"谁调用 X" |

> **★★ 2026-10-17 更正（重要）**：上面这条结论**已被推翻** ——
> 仓库 `tools/luajit-decompiler-v2-master.zip` 就是一个**可用的 LuaJIT 反编译器**（C++/Windows API）。
> 已成功构建为 `tools/luajit-decompiler-v2-build/LuajitDecompiler.exe`，并**全量反编译**：
> **1.4.11 共 2,254 个 `.lua`（98.1%，41.5 MB）**，输出 `analysis/luajit_src/1.4.11/`。
> 实测 `mission_ctrl.luac`(39.9 KB) → 52.8 KB 可读源码，**0.042 秒**。
> 构建需 5 处 MSVC→GCC 移植（`-funsigned-char` `-D_CHAR_UNSIGNED=1` `-std=c++20`、
> 去类体冗余限定、`std::strcmp`→`strcmp`、`-lcomdlg32`），已固化在构建目录。
> ⇒ **R1.3 交付的"函数级调用图"不再是替代品，而是补充**；源码级检索应优先用 `analysis/luajit_src/`。
> ⚠ 1.4.9 / 1.3.0 反编译失败（该工具只支持特定字节码布局）⇒ 这两版仍只能反汇编。

> ⚠ **关于"自研 LuaJIT 反编译器"**：**不可行，未做**。LuaJIT 字节码是寄存器机 + 轨迹优化产物，
> 无可用的开源反编译器（`unluac` 仅支持标准 Lua 5.1）；强行产出伪代码**无法作为证据**，
> 违反"不把推断写成确认"的纪律。改交付**函数级调用图**（标 `heuristic` 静态近似），
> 足以回答"谁调用谁"，精确定位后仍用 `tools/luajit_dis.py` 反汇编确认。

**字段差异的自证与残留**：本次对 1.4.9 的提取与仓库既有 `protocol/fields.json` 对比 ——
条目 `3553 vs 3553`，仅提取有 0，仅基线有 0，**字段不一致 4**（= **0.11%**）。
残留全是类型码 `b` 的映射差（本提取器 `b→bool`；基线用更新版类型词表，含 `bytes`/`l`/`struct<Dsc…>`），
且**三版本同口径** ⇒ 跨版本比较不受影响。

### 9.5 已如实登记的局限

| 局限 | 说明 |
|---|---|
| 无 Lua 源码级还原 | 5,299 个 luac 为 `BYTECODE_ONLY`（可反汇编，无可靠反编译器） |
| 按钮→回调为**静态推断** | 标 `static_extract`，**未经实机点击确认** |
| **界面级协议绑定只有 127/401** | 实测 `*_view.luac` 这类**子视图本身不持有协议**（协议在 panel/ctrl），故"0 绑定"是**真实结构**而非漏采；已补 `r1_module_scope_signals`（381/401 可用）作为**模块作用域**线索 |
| 37 个界面存在**无法解析的模块名** | 已用 `r1_unresolved_modules` 显式登记，不静默丢弃 |
| 服务端持久化为**邻域扫描** | 处理函数 ±120 行内出现过的表名，可能多报/漏报 |
| "服务端未实现 1243" 含水分 | 那是**协议全集**口径；真机实际只出现约 132 种命令，多为**死协议** |
| 实机验证仅 337 链 | 其余链末段为 `RUNTIME_NOT_VERIFIED` |

**三条被校验抓出并已修正的自身缺陷**（如实记录）：① 调用链缺 `persistence` 段导致消费方 KeyError；
② 把**嵌套细化**误判为**同级遮蔽**——修正后"同级遮蔽 = 0"，与项目门禁 `lint_dispatch_shadow.py` 结论一致；
③ UI 索引 `r1_lua_files_resolved` 存在重复项，已去重。

---

## 十、一句话现状

> **协议对接与基础设施已实质收口**（CS/SC 审计零不一致、真机回放 0 不符、单进程 Python+SQLite 延迟 10.8–16.9 ms），
> **一条完整垂直玩法链已在原版 1.4.11 客户端上实机跑通**（登录→场景→对话→任务→战斗→奖励→背包→商城→邮件→排行），
> **GM 后台管理系统已可用**；
> **剩余全部缺口均卡在证据**（需实机 / 需真值 / 需客户端改动），**无一属工时不足**。
