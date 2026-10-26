# C2.1 前置静态勘查报告 —— 《绝世唐门》1.4.11 客户端恢复工程真实结构

> 勘查日期：2026-10-15 ｜ 模式：**全程只读**（未启动 server、未连模拟器、未执行 adb、未修改任何既有文件；仅新建本报告）
> 方法：目录枚举 + 构建脚本逐行阅读 + `analysis/jstm_client_audit/_raw/apk_entries_1_4_11.txt`（19,106 行 APK 条目清单）按路径正则筛选 + `ui_inventory.json`（391 条）python 聚合检索 + 既有文档交叉验证。
> 证据分级沿用工程惯例：CONFIRMED（直接读文件/字节码/实机文档）> STRONG_INFERENCE > UNKNOWN。

---

## 0. 一句话结论

当前客户端修改通道是**"补丁 APK"单一通道**：DEX 单字节（`is_close=true`）+ 明文 `assets/src/config.luac` 末尾追加一段 Lua（URL 硬编码 + 本地登录），由 `tools/patch_fake_login.py` 一次写出，签名后即运行；**运行包内没有 observer/热补丁注入块**（热补丁通道只存在于另一条 `build_apk.ps1` 探针链产物里）。18 个 A 类界面已实机可显示，338 个 B 类界面模块+资源齐全但未实机验证，27 个 C 类仅图标证据、8 个 D 类 1.4.11 已移除。

---

## 1. 客户端恢复工程全貌

### 1.1 目录树（关键路径 + 大小 + 用途）

```
C:\Users\xu\Desktop\DSH\
├── anzbao\                                  原版 APK（只读源，不可改动）
│   ├── jstm_142165.apk        280,804,346 B ★ 1.4.11 主目标原版包（versionCode 46）
│   ├── jstm.apk               241,663,327 B   1.4.9（com.shiyue.dldl.ewan.qihoo）
│   ├── dldlJl.apk             142,437,549 B   1.3.0（com.shiyue.dldl.ewan）
│   └── *_analyze.txt           71–76 KB       三版 APK 鉴定文本
├── patched\                                 补丁 APK 产物（50 个文件 / ~6.1 GB）
│   ├── jstm_1411_fakelogin_aligned.apk 280,472,477 B ★★ 当前实机运行的 1.4.11 补丁包
│   │                                            （包名 com.shiyue.dldl.ewan.baidu2；
│   │                                              phase1_runtime_restore.md §73 实机 base.apk 同长核验）
│   ├── jstm_1411_fakelogin_raw.apk      280,687,191 B   签名前中间产物
│   ├── jstm_1411_probe.apk              272,718,667 B   联调探针版（build_apk.ps1 -NoEmbedded 产物）
│   ├── jstm_1411_probe..dexpatched.apk 280,648,779 B   DEX 补丁中间产物
│   ├── jstm_dex.apk                     280,648,780 B   DEX 补丁另一中间产物
│   ├── jstm_fakelogin*.apk / .bak_r65/.bak_r74/.bak_r93  241 MB，1.4.9 链产物+历史回滚包
│   ├── dldlJl_fakelogin_aligned.apk    142,282,019 B   1.3.0 链产物
│   └── dsh.keystore                       2,674 B      签名密钥（alias=dsh / pass=123456，明文写在脚本里）
├── tools\
│   ├── patch_fake_login.py     9,886 B   ★ 当前运行包的改包器（DEX is_close 字节改 + config.luac 注入）
│   ├── patch_apk.py            37,917 B   另一条改包器（so URL 等长替换 + config.luac 大块注入 + 内置服务端）
│   ├── patch_dex_skip_sdkinit.py 9,366 B  DEX 补丁（SuperPlatform.init()→no-op）
│   ├── patch_url_only.py        3,550 B   仅改 URL 的变体
│   ├── build_fakelogin.ps1      3,194 B   1.4.9 链一键包（lua-check 门禁→patch_fake_login→zipalign→签名→adb install）
│   ├── build_apk.ps1            4,709 B   联调/单机链一键包（DEX补丁→patch_apk→verify→zipalign→签名）
│   ├── verify_injected_lua.py   6,631 B   注入 Lua 语法闸门
│   ├── verify_patched_apks.py   4,615 B   三包（1.3.0/1.4.9/1.4.11）改包核验
│   ├── dsh_patch_probe.lua      4,059 B   热补丁探针（v1–v6，仅注入版 APK 可用）
│   ├── _cap_mumu_window.ps1     2,314 B   MuMu 窗口 PrintWindow 截屏 → shots\mumu_win.png
│   ├── _cap_mumu_screen.ps1     2,926 B   MuMu 窗口 CopyFromScreen 截屏 → shots\mumu_scr.png
│   ├── jadx\ / jadx-out\sources\           DEX 反编译产物（jadx-out\sources 存在）
│   └── dexdump_full.txt / dexdump_patched.txt  141 MB/份（DEX 反汇编全文）
├── server\
│   ├── mock_server.py          ~18.5k 行单体（TCP 9000 + HTTP 8080，/DSH_ADMIN 管理面）
│   ├── config.json              运行配置（host=10.0.2.2, http_port=8080, game_port=9000, server_list[0].ip=10.0.2.2）
│   ├── dsh_fake_login.lua       ★ 注入到运行包 config.luac 末尾的 Lua 块源码
│   ├── local_server.lua / main_lua.lua / observer.lua   build_apk.ps1 链用的内置服/引导/观测器源码
│   └── backup\mock_server.py.bak_r*   服务端改前回滚（与客户端无关）
├── analysis\
│   ├── jstm_client_audit\
│   │   ├── ui_inventory.json     406,068 B  391 条界面清单（A18/B338/C27/D8）
│   │   ├── ui_inventory.md       81,196 B   同上人类可读版
│   │   ├── ui_restoration_order.md        ★ C0 派生：45 界面复原队列（阶段1–5）
│   │   └── _raw\apk_entries_1_4_11.txt     19,106 行 1.4.11 APK 全量条目
│   ├── extraction\lua_injection_channel_round.md / lua_injection_round2.md   注入通道两轮结论
│   ├── calibrated_ui_coords.md            2560x1440 实机坐标表
│   ├── runtime_evidence\                 采集环境/README、calibration_R/V、shots\(327 PNG)
│   └── shots\                            dsh2–dsh6.png / dsh_now.png（7 个）
└── docs\
    └── _raw\c2_1_client_survey.md         ← 本报告（新建）
```

**没有发现**独立的 workdir/unpack 解包目录：客户端"源码形态"不是解压出的工程树，而是 ① APK 内 `assets/src/**/*.luac`（编译字节码）+ ② 散落的反汇编文本（`analysis/_*.txt`、`tools/dexdump_*.txt`）+ ③ `analysis/*.luac`（已抽出单独研究的关键模块：denglu_ctrl、scene_view、mission_ctrl 等约 30 个）。

### 1.2 构建 / 补丁 / 注入完整链路

**链路 A —— 当前运行包（CONFIRMED，`analysis/1.4.9/multiversion_patch.md` §四 + `tools/build_fakelogin.ps1`）：**

```
python tools/patch_fake_login.py anzbao/jstm_142165.apk patched/jstm_1411_fakelogin_raw.apk \
        --base http://10.0.2.2:8080 --lua server/dsh_fake_login.lua
  → zipalign -f -p 4 raw → patched/jstm_1411_fakelogin_aligned.apk
  → apksigner sign --ks patched/dsh.keystore (dsh/123456) --v1 --v2
```

`patch_fake_login.py` 写两处：
1. **DEX**：`com.shiyue.sdk.EWanSdk.<init>` 里 `is_close` 写入字节 `00→10`（const/4 v0,#1），360/ewan SDK 全部生命周期方法变为 no-op（字节码证据见 `fake_login_patch.md` §二；脚本内有寄存器一致性强制断言）。
2. **`assets/src/config.luac`（明文 GBK Lua）末尾追加** `server/dsh_fake_login.lua` 块：硬编码 `HOST=10.0.2.2 / PORT=8080`，写入 `URL_PATH_ALL / URL_PATH / CDN_PATH_BASE / CDN_URL / url_res_config`，`IS_PLATFORM_LOGIN=false`，预写本地登录账号 `last_login_account=dsh_local`（注入块由 `main.luac` 的 loadConfig() 在任何网络访问前执行，`server/dsh_fake_login.lua` 文件头注释）。

**链路 B —— 联调探针版（CONFIRMED，`analysis/extraction/lua_injection_channel_round.md` §1.1）：**

```
pwsh tools\build_apk.ps1 -Src anzbao\jstm_142165.apk -Out patched\jstm_1411_probe.apk `
     -NoEmbedded -SkipSdkInit -Host 10.0.2.2 -Port 8080
```
五步：① `patch_dex_skip_sdkinit.py`（把 `EwanSdk.onCollectData` 里 `SuperPlatform.init()` 改 SB no-op）→ ② `patch_apk.py`（`lib/armeabi/libentryexstd.so` 8 个网关 URL **等长替换**为 `http://10.0.2.2:8080/...`；所有 `.luac` 内 `ewan.cn/jstm` URL 等长替换；`config.luac` 改写 `URL_LUA_CONFIG` + 翻 `IS_PLATFORM_LOGIN` + 追加 URL_PATH 全局块 / `UPDATE_SKIP=true` / `_is_game_restart=true` / `FmodexManager.downloadOtherFile` Lua 垫片 / pcall-xpcall-print hook / `dsh_patch.lua` 热补丁加载器 / `server/observer.lua`；丢弃 `assets/res/resource/login/gamecg.mp4`）→ ③ `verify_injected_lua.py` 语法闸门 → ④ zipalign → ⑤ apksigner。

**Lua 如何被加载执行（CONFIRMED，patch_apk.py 注释 + lua_injection_round2.md）：**
- 启动顺序：`main.luac` → `loadConfig()` 执行 `config.luac`（注入块在此运行）→ `require("file_update")` → proto#9 见 `URL_PATH` 非 nil 即短路（否则 0.2s 无限重下 url_config.lua）→ `update_finish()` → `ver_load_start()`（注入块设 `_is_game_restart=true` 迫使 main() 同步调用，绕过"无场景→Action 不触发"死锁）→ `game_start` → denglu 登录界面。
- 热补丁：注入块 `pcall` 读 `<writable>/dsh_patch.lua`（=`/data/user/0/com.shiyue.dldl.ewan.baidu2/files/dsh_patch.lua`）→ `loadstring` → `pcall`；迭代只需 `adb push` + 重启。
- ⚠ **副作用已实测**：完整注入块在联调（连 PC mock_server）下会卡启动（"error网络异常"、不连 9000）；obs-only 变体也会卡下载循环。结论（lua_injection_round2.md §二）：**当前运行包用的是链路 A，不带 observer/热补丁块**；已重装链路 A 包恢复运行态。

### 1.3 可回滚性

| 层级 | 原/回滚物 | 位置 |
|---|---|---|
| 原版 APK（源头备份） | `anzbao/jstm_142165.apk`（未改动，只读） | CONFIRMED |
| 运行包回滚 | `adb install -r patched/jstm_1411_fakelogin_aligned.apk`（探针实验后的标准恢复动作，lua_injection_round2.md §三） | CONFIRMED |
| 1.4.9 链历史包 | `patched/jstm_fakelogin.apk.bak_r65`、`jstm_fakelogin_aligned.apk.bak_r74/.bak_r93` | CONFIRMED |
| 热补丁停用 | `adb shell su 0 rm <writable>/dsh_patch.lua`（仅注入版有意义） | CONFIRMED |
| 服务端侧回滚 | `server/backup/mock_server.py.bak_r*`、`backup/roles.db.bak_round37`（与客户端无关，仅说明工程惯例） | CONFIRMED |

---

## 2. UI 框架机制（APK 内 `assets/src/**` 真实模块）

> 路径均来自 `_raw/apk_entries_1_4_11.txt` 正则筛选；职责来自 `analysis/blank_dialog.md`、`analysis/login_flow.md`、`analysis/runtime_findings.md` 等字节码级文档。

### 2.1 启动/网络/事件底座

| 类/模块 | APK 路径 | 职责 |
|---|---|---|
| main.luac | `assets/src/main.luac` | 引擎入口：initSearchPath → sdk_function → require(file_update)；指令 118–128：`_is_game_restart=true` 时同步 `ver_load_start()` |
| config.luac | `assets/src/config.luac` | 明文 Lua（GBK）：URL_LUA_CONFIG、IS_PLATFORM_LOGIN、全局开关；补丁注入点 |
| file_update.luac | `assets/src/file_update.luac` | proto#9 URL_PATH 短路点 / #5 update_finish / #8 OnFileDownloadResult / #36/#39 开场 CG |
| game_start.luac | `assets/src/game_start.luac` | 视频结束后 initInstance → 登录界面 |
| sys/gamenet.luac | `assets/src/sys/gamenet.luac` | GameNet：`SetLoginServerInfo(host,port)`、SendProtocal、协议收发；业务控制器的父链终点（beast_ctrl → base_controller → gamenet） |
| sys/event.luac | `assets/src/sys/event.luac` | 事件系统：`DengluEvent:Fire(LOGIN_SUCCESS)` → SceneController 进场景 |
| sys/module_include.luac | `assets/src/sys/module_include.luac` | GameModule 列表注册表 |
| sys/protocalrulesmgr.luac | `assets/src/sys/protocalrulesmgr.luac` | `ProtocalRulesMgr` 协议规则全局表（实机 dump 确认是 table） |
| sys/global_time_ticket.luac | `assets/src/sys/global_time_ticket.luac` | LOGIN_REQUEST_tiket 等计时条目 |
| base/base_controller.luac | `assets/src/base/base_controller.luac` | 控制器基类（所有 *_ctrl 继承链） |
| base/base_view.luac / baseclass.luac / baseprotocalstruct.luac | `assets/src/base/` | 视图基类 / 协议 Dsc 结构基类 |

### 2.2 弹窗 / 提示（确认框与气泡）

| 类/模块 | APK 路径 | 职责（字节码证据） |
|---|---|---|
| **CommonAlert** | `assets/src/common/common_alert.luac`（analysis/ 下有抽出副本 13,388 B） | proto[6] `show(msg, title=getString('提示'), okBtn, retryCb, {no_clear=true})`：带标题+确定按钮的确认弹窗；`denglu_ctrl.on10102Login code≠1`、`denglu_mgr proto[8]` 空列表重试都走它（blank_dialog.md §根因3） |
| `message()` 全局提示 | `assets/src/common/common_function.luac`（analysis/ 下抽出副本 36,620 B） | proto[120]：轻提示函数（IS_TEST_SERVER 下转发原实现）；`team_data.luac`/`beast_ctrl.luac` 多处 `message(resp.msg)` |
| common_tips_mgr / common_tips / common_tips_two | `assets/src/common/common_tips*.luac` | tips 管理与两层气泡 |
| buy_alert | `assets/src/common/buy_alert.luac` | 购买确认弹窗 |
| common_notice | `assets/src/common/common_notice.luac` | 公告/跑马灯 |
| prompt_ctrl/view | `assets/src/game/prompt/prompt_ctrl.luac` 等 5 文件 | 游戏内提示系统（ui_inventory 仅 B 类 1 条） |

### 2.3 主界面 / 场景 / 导航 / 窗口管理

| 类/模块 | APK 路径 | 职责 |
|---|---|---|
| **view_manager** | `assets/src/game/main/view_manager.luac` | ★ 窗口/视图管理器（主界面面板挂载点，C2.1 最小切入点候选） |
| main_ui / main_ctrl / main_tab_btn / main_fun_tab | `assets/src/game/main/*.luac` | 主界面 HUD：顶部功能栏（福利/商城/挂机）、底部功能栏（魂技/伙伴/锻造/更多）、聊天图标、耐久条 |
| scene_controller / scene_model / scene_view | `assets/src/game/scene/*.luac`（analysis/ 下有抽出副本 scene_controller.luac 9,998 B / scene_model.luac 42,843 B / scene_view.luac 57,298 B） | 场景管理：on10200 `if resp.code~=0 then message2(resp.msg)`；on10206 move |
| nav_ctrl / nav_view / nav_secondary_menu / nav_open | `assets/src/game/nav/*.luac`（9 文件） | 自动寻路导航 + **二级菜单**（secondary_menu）—— 主界面按钮→二级面板跳转的直接证据点 |
| sidebar_ui / sidebar_ctrl / sidebar_events / sidebar_mis_item / sidebar_team_ui | `assets/src/game/sidebar/*.luac`（6 文件） | 侧边任务栏 / 组队 UI / 补守提示 |
| joystick / run_ctrl | `assets/src/game/main/joystick.luac`、`run_ctrl.luac` | 摇杆 + 移动控制 |
| buff_manager / durable_panel / hunger | `assets/src/game/main/buff/*.luac`、`main/durable_panel.luac` | HUD buff 条 / 耐久面板 / 饱食度 |

### 2.4 导航入口证据（主界面按钮→二级面板）

实机坐标（`analysis/calibrated_ui_coords.md`，2560×1440）：
- 顶部栏：福利 (640,100) / 商城 (800,100) / 挂机 (1320,100)
- 底部栏：魂技=技能面板 (1800,1360) / 伙伴 (2160,1360) / 锻造 (2340,1360) / 更多 (2480,1310)
- 通用面板关闭 X：(2200–2210, 70–85)（角色/伙伴/挂机/技能四面板同位置 ⇒ **统一 view_manager 弹窗模板**）
- 截屏命名链（runtime_evidence/shots/）：`003316_tap_more` → `003337_tap_avatar`(角色) → `003407_tap_bag`(背包) → `003507_tap_attr`(属性) → `003741_tap_mall`(商城) —— 与上述坐标一一对应。

---

## 3. C2.1 目标界面盘点（静态初判，python 聚合 ui_inventory.json）

> 状态定义（ui_inventory.md §四类）：**A**=已实机验证（18）｜**B**=模块+资源均存在未验证（338）｜**C**=仅图标/字符串证据（27）｜**D**=1.4.11 已移除（8）。
> 坐标证据：`analysis/calibrated_ui_coords.md` + `analysis/runtime_evidence/shots/*.png`（327 张）。

| # | 界面 | luac 模块路径 | 资源 | C0 状态 | 实机坐标/截图证据 |
|---|---|---|---|---|---|
| 1 | 登录入口（login panel） | `assets/src/game/login/login_panel.luac` | login/ 资源（77 文件） | **A** HIGH rtv=是 | shots/20261002_002907_00_initial.png、p16_login.png；runtime_evidence/README |
| 1b | 选服 / 平台 / 用户面板 | `game/login/server_panel.luac`、`platform_panel.luac`、`user_panel.luac` | 同上 | B LOW 未验证 | 坐标 UNKNOWN（选服在 dsh_local 本地账号流程下基本不出现） |
| 2 | 角色选择/创建 | `game/login/create_view.luac`（建角）、`role_cell_login.luac`（角色格）、`name_data.luac` | login/ | **未单列条目（B 缺项）** | UNKNOWN；注：本地存档已有 last_login_account，自动跳过选角 |
| 2b | 角色信息面板（role ctrl） | `game/role/role_ctrl.luac` + `role_display_panel.luac`、`role_main_view.luac`、`role_show_panel.luac`、`role_vo.luac`、`role_data.luac` | role/(55 文件) | ctrl=**A** HIGH；panel/view=B | shots/20261002_003507_tap_attr.png、p45a_attr.png；X 按钮 (2200,70)；综合战力=0 已知缺陷（runtime_findings D1） |
| 3 | 游戏主界面 HUD | `game/main/main_ui.luac`、`main_ctrl.luac`、`main_tab_btn.luac`、`main_fun_tab.luac`、`view_manager.luac` | main/ + common/btn(50) | **未单列（HUD 本身）**；durable_panel=B | 顶部/底部栏坐标见 §2.4；场景 shots/phase1_world_*.png |
| 4 | 角色属性面板 | 同 2b（role_ctrl=A；role_display_panel=B） | 同上 | A+B 混合 | X (2200,70)；tap_avatar (640,100) 区 |
| 5 | 背包面板 | `game/backpack/backpack_ctrl.luac` | item/(1383 文件) | **A** HIGH | shots/20261002_003407_tap_bag.png、d2root_06_bag_open.png；已知"0/150 空 vs 10502 有 4 件"渲染缺陷（D2） |
| 6 | 任务面板 | `game/mission/mission_panel.luac` + `mission_ctrl.luac`(抽出副本 39,923 B)、`mission_data2.luac` | mission/(57 文件) | **A** HIGH；nycollect_subpanel=B | shots/uival_09_quest.png、uival_18_quest.png |
| 7 | 系统设置 | `game/set/view/set_panel.luac` + `set_ctrl/data/view/vo`、`view/setting_view.luac`、`view/set_channel_panel.luac` | set/ | **A** HIGH；channel_panel=B | shots/uival_01_more.png、v7_more_a_203916.png（"更多"入口 = (2480,1310)） |
| 8 | 二级面板（示例） | `game/nav/nav_secondary_menu.luac`；技能 `skill/skill_panel.luac`=A；商城 `shop/shop_ctrl.luac`=A；好友 `friend/friend_panel.luac`=A；日常 `daily/daily_panel.luac`=A | 各系统 res/ 目录 | 18 个 A + 338 个 B | 魂技 (1800,1360)；锻造 (2340,1360)；伙伴 (2160,1360) |
| 9 | 确认/提示弹窗 | `common/common_alert.luac`（CommonAlert:show）+ `common_function.luac` message()；`common/buy_alert.luac` | common/ | **A 级已验证存在**（blank_dialog.md 四轮 A/B 实测，非 ui_inventory 条目） | 50 级礼包弹窗 X (2360,680) CONFIRMED；空白框四根因已修复 |

**补充**：A 类 18 个完整名单（ui_restoration_order.md §2）= login / role_ctrl / backpack / battle_ctrl / mission / shop / skill / hero / friend / guild_base / daily / automate / equipforge / map_view / vip / answer / scratcher / set。D 类 8 个 1.4.11 已移除（garden/jingjie/moneytree/xiulianhulu/glz_main_ui/friend_view/mail_panel/libao_view）。

---

## 4. 运行时接线现状

### 4.1 登录接线（fakelogin 注入点）

- 运行包注入点 = `assets/src/config.luac` 末尾（`server/dsh_fake_login.lua` 块）：URL 全局 + `IS_PLATFORM_LOGIN=false` + 本地账号预写。
- DEX：`EWanSdk.<init> is_close=true`（方案 C，`fake_login_patch.md`）→ SDK 不回调；Lua 侧 `denglu_platform` 走本地账号。
- 登录命令序列（login_flow.md §一，CONFIRMED）：`10001 FirstPack → 1110 账号登录 → 10102 登录指定角色 → 10103 重连 → 10300/10301 角色初始化 → 10502 背包 → 各子系统`；成功条件：1110/10102/10103 的 `code==1`（TRUE），否则 `CommonAlert:show(msg)` 停在登录（blank_dialog.md 根因 1/3）。

### 4.2 连 mock_server 的地址配置在哪

| 链路 | 地址 | 配置位置 |
|---|---|---|
| HTTP（更新/网关/上报） | `http://10.0.2.2:8080` | **硬编码进补丁 APK**：① `config.luac` 注入块 `URL_PATH*/CDN_*`；② `libentryexstd.so` 8 个网关 URL 等长替换（patch_apk.py GATEWAY_RE）；运行包由 `patch_fake_login.py --base http://10.0.2.2:8080` 写入 |
| TCP 游戏服 | `10.0.2.2:9000` | **不是硬编码**：由 mock_server 在 `GET /gateway/mobile/json` 返回 `data.server_list[0]={ip:"10.0.2.2", port:9000}`（`server/config.json` 第 3–11 行）；客户端 `denglu_mgr.luac proto[8]` 解析 → `GameNet:SetLoginServerInfo(host,port)`（login_flow.md §二） |
| 服务端监听 | TCP 9000 + HTTP 8080 | `server/mock_server.py`（`--http 8080 --game 9000`，bind 0.0.0.0） |

### 4.3 C0 实机证据清单（静态列目，不执行）

- `analysis/runtime_evidence/`：README.md（采集环境）、runtime_findings.md（D1 战力=0 / D2 背包空 / D3 战斗占位值 / D4 货币映射 / D5 心跳坐标）、calibration_R.md（协议实值 R1–R12）、calibration_V.md（数值 V1–V12）、frames/key_frames.md、probes/dsh_probe_excerpt.md、**shots/ 327 个 PNG + user_assist/ 子目录**。
- `analysis/shots/`：dsh2.png–dsh6.png、dsh_now.png（7 个）。
- `analysis/calibrated_ui_coords.md`：2560×1440 坐标表（§2.4 已摘）。

### 4.4 截屏脚本可用性（仅列路径与用法）

| 脚本 | 用法 | 输出 |
|---|---|---|
| `analysis/runtime_evidence/shot.ps1` | `pwsh shot.ps1 <名字>`（内部写死 `adb -s 127.0.0.1:16384 shell screencap`） | `runtime_evidence/shots/<时间戳>_<名字>.png` + `_view.jpg`(900px) |
| `tools/_cap_mumu_window.ps1` | 直接执行（EnumWindows 找标题含 MuMu 的最大窗口，PrintWindow 2=PW_RENDERFULLCONTENT） | `DSH/shots/mumu_win.png` |
| `tools/_cap_mumu_screen.ps1` | 直接执行（前置窗口后 CopyFromScreen 整屏） | `DSH/shots/mumu_scr.png` |

---

## 5. 风险与结论

### 5.1 明确回答任务的五问

1. **当前客户端修改通道是什么？** —— **补丁 APK 单通道**：`patch_fake_login.py` 对 `anzbao/jstm_142165.apk` 做 DEX 单字节（is_close）+ `assets/src/config.luac` 末尾追加 `dsh_fake_login.lua` 块，zipalign + dsh.keystore 签名产出 `patched/jstm_1411_fakelogin_aligned.apk`。Lua 热补丁通道（dsh_patch.lua 加载器 + observer）**只在另一条 build_apk.ps1 探针链产物里，当前运行包没有**（lua_injection_round2.md §二明示"原 fakelogin APK 连注入块都没有"）。两者并存于工程、不并存于运行包。
2. **哪些界面可直接显示？** —— 18 个 A 类（见 §3 表 + ui_restoration_order §2）：登录/角色 ctrl/背包/战斗/任务/商城/技能/伙伴/好友/公会/日常/挂机/锻造/世界地图/VIP/答题/刮刮乐/设置。
3. **哪些界面缺模块/资源？** —— 27 个 C 类（运营活动系列：jiangchi/luckbox/guess/invest_sec 等，由 activity_ctrl 按 name 分派、无独立 luac）；8 个 D 类（1.4.11 已移除，勿恢复）；另 ~120 个 B 类服务端缺失不排（ui_restoration_order §7.3）。
4. **UI 框架改造的最小切入点？** —— **`assets/src/game/main/view_manager.luac`**（面板挂载/关闭统一模板，四面板 X 按钮同坐标可证）+ **`assets/src/game/nav/nav_secondary_menu.luac`**（主界面按钮→二级面板的跳转注册表）。改动方式上，所有客户端修改只能走"重打包 APK"（改 luac → patch_fake_login.py 链或 patch_apk.py 链 → 签名 → adb install），**不存在免重打包的运行时热改**（当前运行包无 dsh_patch 加载器；可写目录推 config.luac 覆盖已实测无效，patch_apk.py 注释 §热补丁节）。

### 5.2 风险清单

| # | 风险 | 证据/影响 |
|---|---|---|
| R1 | **重打包即重新签名+安装**：任何 UI 模块改动都要走完整链（改 luac→patch→签名→adb install），迭代慢；且 patch_apk.py 的 .so URL 替换要求**等长**，改配置须遵守 | patch_apk.py fit() 函数；build_apk.ps1 五步链 |
| R2 | **注入块会干扰启动**： observer/热补丁块在联调模式实测卡死启动（网络异常/下载循环）；C2.1 若需运行时探针，必须先做 observer 解耦（lua_injection_round2.md §六方案 A+B） | lua_injection_round2.md §二 |
| R3 | **背包渲染缺陷未解**：10502 已发 4 件但 UI "0/150" 空白；角色综合战力=0 —— 复原背包/属性面板时这些已知缺陷会被当成"复原失败"重复踩坑 | runtime_findings.md D1/D2 |
| R4 | **B 类 338 个全部 confidence=LOW**：ui_inventory 由 apk_scan 机械生成，模块存在≠导航可达；"主界面 HUD"本身未单列条目 —— C2.1 第一个实机动作应是开机截屏核对 HUD 与 view_manager 挂载 | ui_inventory.json entries 字段 |
| R5 | **角色选择/创建界面缺 ui_inventory 条目**：create_view.luac/role_cell_login.luac 在 APK 里存在，但清单无对应条目；本地账号自动跳过选角 —— 该流程实机表现 UNKNOWN | §3 第 2 行 |
| R6 | 坐标基于 2560×1440 横屏、MuMu adb 127.0.0.1:16384；换分辨率/换实例需重校准 | calibrated_ui_coords.md 头部 |
| R7 | patched/ 已 6.1 GB 含 50 个历史 APK；重打包中间产物（_raw/_dexpatched）与正式产物混放，取错包风险 | workspace_audit.md |

### 5.3 自检记录

- [x] 未启动 mock_server、未连模拟器、未执行 adb、未修改任何既有文件（仅新建 `docs/_raw/` 与本报告）。
- [x] 构建链路：patch_fake_login.py（已读全文调用方文档 multiversion_patch.md §四）+ build_apk.ps1（全文 108 行）+ patch_apk.py（全文 681 行）三方互证。
- [x] ui_inventory.json 用 python 按模块/状态聚合检索（未整读入上下文；406 KB）。
- [x] 目标界面 9 类逐项列出 luac 路径 + C0 状态 + 截图证据；UNKNOWN 处已标注（选角流程/HUD 本体条目缺失）。
- [x] 地址配置两处来源（APK 内硬编码 HTTP / 服务端 JSON 下发 TCP）均带文件行号证据。
