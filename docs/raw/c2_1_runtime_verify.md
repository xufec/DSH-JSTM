# C2.1 实机验证报告 —— 《绝世唐门》1.4.11 客户端运行时逐界面实测

> 验证日期：2026-10-15 14:36–15:00 (UTC+8)
> 验证者：C2.1 实机验证分片（全程独占模拟器与 mock_server，未修改任何客户端/服务端文件）
> 方法：adb 实机操作 + 逐界面截屏取证 + logcat/tcp.log 交叉验证
> 证据：截图目录 `analysis/runtime_evidence/c2_1_shots/`（26 张 PNG，全部 >0 字节）

---

## 1. 环境状态表

| 项 | 状态 | 证据 |
|---|---|---|
| MuMu 12 模拟器 | ✅ 在线 | `adb devices` → `emulator-5554  device`（注：实例 0 的 adb 端口为 emulator-5554 而非 127.0.0.1:16384；`adb connect 127.0.0.1:16384` 返回"积极拒绝"，但 MuMu 进程已自动以 emulator-5554 挂载） |
| 设备型号 | Redmi rubens (22041211A)，Android 12 | `getprop ro.product.model`=22041211A，ro.product.brand=Redmi，ro.build.version.release=12 |
| 屏幕分辨率 | Physical 1440×2560（竖屏物理），游戏横屏渲染 2560×1440 | `wm size`=1440x2560；`SurfaceOrientation=1`（横屏）；screencap 实际输出 2560×1440 |
| 客户端包 | ✅ 已安装 | `pm list packages` → `com.shiyue.dldl.ewan.baidu2`（另装 qihoo/ewan 旧包） |
| 启动 Activity | ✅ 已确认 | `cmd package resolve-activity` → `com.shiyue.dldl.ewan.baidu2/org.cocos2dx.lua.AppActivity` |
| mock_server | ✅ 在线 | PID 8312，监听 TCP 9000 + HTTP 8080；`/DSH_ADMIN/status` 返回 rid=1001 DSH lv70 |
| 客户端→服务端连接 | ✅ 稳定 | tcp.log 每 8 秒一次 cmd=1199 心跳往返，无断连 |
| 日志无崩溃 | ✅ | logcat 仅 Cocos2d JniHelper 调试日志，无 FATAL/Exception/AndroidRuntime 错误 |

---

## 2. 逐界面验证表

| # | 界面 | 是否打开 | 数据来源 | 关闭/返回/重复打开行为 | 截图路径 | C2.1 六类初判 |
|---|---|---|---|---|---|---|
| a | 登录界面 login_panel | ⚠ 未直接观察 | fake login 注入块自动本地登录（dsh_local），跳过平台/选服/选角直入主场景 | N/A（自动流程） | `00_initial.png`（加载CG）、`01_after_load.png`（已在主场景） | **已存在但未验证**（fake login 旁路了登录 UI；如需验证需临时回退注入块） |
| b | 选服/平台流程 | ⚠ 未观察 | IS_PLATFORM_LOGIN=false + last_login_account=dsh_local 预写 | N/A | 同上 | **证据不足暂不处理**（设计如此，非缺陷） |
| c | 选角/建角 | ⚠ 未观察 | 已有角色 rid=1001，走 10103 重连路径 | N/A | 同上 | **证据不足暂不处理**（设计如此） |
| d | 主界面 HUD | ✅ 打开 | 真实场景数据（史莱克城 scene=10001，NPC 戴舞桐/mon20001，喷泉，聊天滚动） | 所有面板关闭后正常返回 HUD，无黑屏/叠层 | `07_main_ui_hud.png`、`26_back_to_main.png` | **已完成且已验证** |
| e | 角色属性面板 role_ctrl | ✅ 打开 | 真实服务端 10303 属性：玄武 LV70，生命7305/物攻1813/物防1579/法攻795/法防611/速度18/命中337/躲闪226/暴击113/抗暴90，经验13339/2600094 | X 关闭正常；重复打开 2 次无叠层/输入失效 | `08_role_panel.png`、`24_reopen_role_1.png`、`25_reopen_role_2.png` | **已完成且已验证** |
| f | 背包面板 backpack_ctrl | ✅ 打开（装备+属性合页） | 装备槽 6 件全部渲染（武器/头盔/衣服/鞋子/腰带/护符，带紫橙边框）；货币 180万钻/9999万券/990万币 | X 关闭正常 | `08_role_panel.png`（同角色面板） | **已存在但未完全验证**：装备渲染正常，但背包物品格（bag_code=1 的 6 件道具 bid 28560/28515/21403/13001/46022/33001）未在独立网格视图中逐一确认；D2"0/150空"在本次装备槽已不复现 |
| g | 任务面板 mission_panel | ✅ 打开 | 主线"武魂觉醒"真实数据：跟老师学习魂技，奖励 经验1000/2580/900，"立即传送"按钮；可接任务 tab 显示"当前无任务" | X 关闭正常（见阻塞项 B1 坐标偏移）；tab 切换正常 | `10_mission_panel.png`、`16_available_tasks.png` | **已完成且已验证** |
| h | 系统设置面板 set_panel | ✅ 打开 | 本地设置：音乐/音效/语音滑块、队伍/宗门/世界语音开关、显示品质（正常品质选中）、社交开关、切换账号/系统公告/联系GM按钮 | X 关闭正常 | `22_settings_panel.png` | **已完成且已验证** |
| i | 确认/提示弹窗 common_alert | ✅ 触发并关闭 | 50级礼包弹窗（gift popup）：礼盒图标+"50级礼包"+"领取"按钮+红色X关闭 | 红色X关闭正常（校准坐标 2360,680 CONFIRMED） | `01_after_load.png`（弹窗出现）、`06_gift_close_calib.png`（弹窗关闭后主界面） | **已完成且已验证** |
| j-1 | 技能面板 skill_panel | ✅ 打开 | 面板框架正常，但左侧技能列表为空，槽位全部"未激活"，定位/冷却显示"--" | X 关闭正常 | `19_skill_panel.png` | **依赖服务端**（mock_server 未推送已学技能列表/技能数据；面板本身可打开） |
| j-2 | 商城面板 shop_panel | ✅ 打开 | 真实 12803 商城数据：热卖8件（洗髓丹250/坐骑360/魂灵360/魂环360/神器突破480/修炼笔记630/低级神格330/高级神格680），拥有钻石1800140，与 calibration_V R11 一致 | X 关闭正常 | `20_shop_panel.png` | **已完成且已验证** |
| j-3 | 好友面板 friend_panel | ✅ 打开 | "您还没有好友"（空数据），邮件 tab 有红点通知（对应 admin 状态 1 封欢迎邮件） | X 关闭正常 | `23_friend_panel.png` | **已完成且已验证**（空好友列表为真实状态非缺陷） |
| j-4 | 更多子菜单（设置/制作/结拜/录像） | ✅ 展开 | 底部"更多"按钮展开二级菜单 | 点击设置直达设置面板 | `21_more_settings.png` | **已完成且已验证** |

---

## 3. 回归结论

### 3.1 主流程回归（重新登录→进场景→角色存在）

| 回归项 | 结论 | 证据 |
|---|---|---|
| 自动登录（fake login） | ✅ 无退化 | 客户端启动后 ~45 秒自动进入主场景，无报错弹窗 |
| 角色加载 | ✅ 无退化 | rid=1001 DSH 玄武 lv70 正确加载，属性面板数值与 admin/status 一致 |
| 场景加载 | ✅ 无退化 | 史莱克城（scene=10001）正常渲染：NPC 2 个、怪物 1 个、喷泉建筑、聊天栏滚动系统消息 |
| 心跳/连接 | ✅ 无退化 | tcp.log 显示每 8 秒 1199 心跳正常往返，总计 6148 字节 |
| 面板开关稳定性 | ✅ 无退化 | 角色面板连续打开 2 次（截图 24/25），无重复 UI 叠加、无输入失效、无黑屏 |
| 逐级返回 | ✅ 无退化 | 从二级面板（技能/商城/好友/设置）关闭后均返回主 HUD，无叠层残留 |

### 3.2 logcat 关键证据

```
10-15 14:59:13.693  2330 25006 D JniHelper: JniHelper::getJavaVM()
...（连续 JniHelper 调试日志，PID 2330 = cocos2dx.lua.AppActivity）
10-15 14:59:19.643 25103 25103 I sh: type=1400 audit: avc: denied { read } ... permissive=1
```
- 无 FATAL EXCEPTION、无 AndroidRuntime 崩溃、无 Lua error 打印
- 唯一 SELinux audit 为 permissive=1，不影响运行

### 3.3 tcp.log 关键证据

```
[14:58:49] >> cmd=1199 heartbeast 心跳 body(4)=00 01 00 00
[14:58:49] << 1199 heartbeat reply (10 bytes)
...（每 8 秒一次，持续至 14:59:21，共 6148 字节）
```

---

## 4. C2.1 六类状态统计

| 分类 | 数量 | 界面 |
|---|---|---|
| 已完成且已验证 | 8 | 主HUD、角色属性、任务、设置、common_alert弹窗、商城、好友、更多子菜单 |
| 已存在但未验证 | 2 | 登录界面（fake login 旁路）、背包物品网格（装备槽已验证，道具格未逐一确认） |
| 需要修复 | 0 | — |
| 需要新增兼容层 | 0 | — |
| 依赖服务端 | 1 | 技能面板（技能列表空/未激活，需 mock_server 推送技能数据） |
| 证据不足暂不处理 | 2 | 选服/平台流程、选角/建角（fake login 设计旁路，非缺陷） |

---

## 5. 已知缺陷复现情况

| 缺陷编号 | 描述（来自历史标定） | 本次复现结果 |
|---|---|---|
| D1 | 综合战力 UI=0（calibration_V.md V9） | **已不复现**：角色面板显示"综合战力: 724112"，顶栏同步显示 724112。服务端 10303 已携带战力字段。 |
| D2 | 背包"0/150 空"但 10502 有 4 件（calibration_V.md §重大发现2） | **装备槽已渲染**：6 件已穿装备正确显示图标。背包道具格（bag_code=1）未在独立网格视图中逐一目验，需后续打开背包 tab 确认。 |
| D3 | 战斗数值为占位 TEST_ONLY | 本次未进入战斗，未复测。 |

---

## 6. 阻塞项清单

| # | 现象 | 证据 | 建议 |
|---|---|---|---|
| B1 | **面板 X 关闭按钮触摸坐标偏移**：校准文档坐标 (2200–2210, 70–85) 在当前 emulator-5554 实例上点击任务面板 X 无响应，需在 x 方向 +30px（即 ~2240→2270）才能命中 | 截图 12/13/14/17 显示 (2240,70)/(2210,85)/back键 均未关闭任务面板；(2270,70) 一次命中关闭 | 更新 `analysis/calibrated_ui_coords.md`，为 emulator-5554 实例补充触摸偏移量；或在脚本中统一加 +30 x 偏移 |
| B2 | **登录/选服/选角界面未直接验证**：fake login 注入块自动登录直入主场景，无法观察 login_panel/server_panel/create_view | 截图 00→01 直接从加载 CG 跳到主场景 | 如需验证登录 UI，需临时用非 fakelogin 包或回退注入块；当前阶段非阻塞 |
| B3 | **技能面板数据为空**：面板框架正常但技能列表为空、槽位"未激活" | 截图 19_skill_panel.png | 需 mock_server 推送 11xxx/12xxx 技能命令下发角色已学技能数据；属服务端补齐而非客户端缺陷 |
| B4 | **模拟器 adb 端口差异**：任务书指定 127.0.0.1:16384，实际设备为 emulator-5554（自动挂载） | `adb connect 16384` 被拒，`adb devices` 显示 emulator-5554 | 更新文档中设备序列号；后续操作统一用 `-s emulator-5554` |

---

## 7. 全部真实命令与输出摘要

```
# 1. 设备连接
adb connect 127.0.0.1:16384 → 积极拒绝 (10061)
adb devices → emulator-5554  device

# 2. 设备信息
adb -s emulator-5554 shell getprop ro.product.model → 22041211A
adb -s emulator-5554 shell getprop ro.product.brand → Redmi
adb -s emulator-5554 shell wm size → Physical size: 1440x2560
adb -s emulator-5554 shell getprop ro.build.version.release → 12

# 3. 服务端启动（tools/restart_server.ps1）
→ WMI PID 11412, 监听 8080,9000
→ 冒烟: HTTP /notice.json 200, TCP 1199 回包
→ /DSH_ADMIN/status → rid=1001 DSH lv70 scene=10001

# 4. 包检查
adb shell pm list packages | grep shiyue
→ com.shiyue.dldl.ewan.baidu2 (已装, 无需 install)

# 5. 启动 Activity
adb shell cmd package resolve-activity --brief com.shiyue.dldl.ewan.baidu2
→ com.shiyue.dldl.ewan.baidu2/org.cocos2dx.lua.AppActivity
adb shell am start -n .../AppActivity → Starting: Intent {...}

# 6. 逐界面操作（adb shell input tap <x> <y> + screencap -p）
→ 角色面板 tap(2150,80) → 打开；tap(2270,70) → 关闭
→ 任务面板 tap(2120,360) → 打开；tap(2270,70) → 关闭
→ 技能面板 tap(1800,1360) → 打开；tap(2270,70) → 关闭
→ 商城 tap(800,100) → 打开；tap(2270,70) → 关闭
→ 更多 tap(2480,1310) → 展开子菜单；设置 tap(1950,1330) → 打开设置面板
→ 好友 tap(180,1050) → 打开；tap(2270,70) → 关闭
→ 礼包弹窗 X 校准坐标 tap(2360,680) → 关闭

# 7. logcat
adb logcat -d -t 100 → 仅 JniHelper 调试日志, 无崩溃

# 8. tcp.log
→ 每8秒 cmd=1199 心跳正常往返
```

---

## 8. 自检记录

- [x] 未修改任何 APK/luac/mock_server/既有文件；仅新建 `analysis/runtime_evidence/c2_1_shots/` 截图与本报告
- [x] 所有截图真实存在（26 张 PNG，文件大小 429KB–4.6MB，全部 >0）
- [x] 界面显示什么记录什么：空数据（好友无/技能空/可接任务无）如实标注为"真实空状态"而非"渲染失败"
- [x] 坐标取自 calibration 文档；X 按钮偏移问题已如实记录为阻塞项 B1
- [x] logcat 与 tcp.log 作为服务端连通性证据
- [x] D1（战力=0）已确认不复现；D2 装备槽已渲染但道具格未逐一目验
