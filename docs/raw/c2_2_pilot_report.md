# C2.2 第三分片试点报告：F1 首帧战力时序诊断与最小修复评估

- 日期：2026-10-15
- 环境：MuMu emulator-5554，2560×1440 横屏；客户端 com.shiyue.dldl.ewan.baidu2 v1.4.11 (versionCode=46)；mock_server 9000/8080 在线
- 原包：`patched\jstm_1411_fakelogin_aligned.apk`（280,472,477 bytes，2026-09-29 19:41）—— 全程未动
- 已安装包 lastUpdateTime=2026-10-14 23:54:10 —— 本会话**未做任何 install/repack**，基线完好

---

## 0. 结论速览

| 项 | 结论 |
|---|---|
| F1 根因 | **角色面板在登录数据风暴中途自动弹出，对尚未填充完成的本地 RoleVo 做了"一次性快照"渲染；之后 vo 补全（HUD 已 724112），但面板标签不再刷新** |
| 与既有假设的偏差 | 既有假设"首帧早于 SC_10304 到达"需修正：**本构建整个流程 CS/SC_10304 从不出现**；面板不发请求、纯读本地缓存 |
| 修复方案评估 | A 热补丁注入=风险高不做；B luac 字节码补丁=无工具链不做；**C 服务端补推 10303/10306=推荐，但本阶段 mock_server 只读边界外，仅记录** |
| 实际改动 | **无**（客户端未改、服务端未改） |
| 次要项 | "我是技能名"/"提升"空白面板/技能空列表 三项根因已定位（见 §4） |

---

## 1. 根因诊断证据链（任务 1）

### 1.1 复现：冷启动截图序列

捕获方式：`tools\_c22_f1_capture.ps1`（force-stop → monkey 启动 → `adb exec-out screencap` 约 0.66s 间隔 ×48 帧；实际 cmd 重定向每帧约 2.8s，48 帧覆盖 133s）。截图目录：`analysis\runtime_evidence\c2_2_f1_repro\`

| 帧 | 启动后 | 画面 | 战力 |
|---|---|---|---|
| f03 | 5.6s | 开场地图 prologue | — |
| f05 | 13.4s | 斗罗大陆序章过场 | — |
| f06 | 17.7s | 登录页"进入游戏" | — |
| **f07** | **22.6s** | **角色面板自动弹出：综合战力=0，6 装备格空 + 绿色加号，每格 `+-0123456789` 占位串** | **0** |
| f08 | 25.3s | 面板仍开；**右上 HUD=DSH 724112**；50级礼包弹出；面板仍 | **0** |
| r0 | ~16:39（开 10 分钟后） | 面板**仍**显示 0、装备格仍空、占位串仍在；HUD=724112 | **0** |
| r2_reopen | 手动关闭面板→点头像重开 | 综合战力=**724112**；6 格真实装备图标（武器/盔/甲/靴/鞋/腰带）；完整基础属性（生命7305/速度18/物攻1813/物防1579/法攻795/法防611/命中337/躲闪226/暴击113/抗暴90）；经验 13339/2600094；占位串消失 | **724112** |

### 1.2 tcp.log 协议时序（捕获窗口 16:29:33→16:31:49）

关键入向/出向事件（server\logs\tcp.log，偏移 245448 起 41125 字节）：

```
16:29:53  >> CS_10302 → << SC_10302 (lev=70, 名字/职业/头像)
16:29:53  >> CS_10303 {rid=1001} → << SC_10303 attr大表 (hp_max=7305, atk_s=1813 ... 204B，含 power)
16:29:53  >> CS_13340/14901/10331/15203/12403 （登录后数据请求簇）
16:29:55  >> CS_10103 RoleReLogin → 场景进入：
           << SC_10200/10201 push, << SC_10305, << SC_12400, << SC_10800/13300/10923/10502(6件装备!),
           << SC_10301 (角色基础 initRoleBaseData), << SC_10922/10924, << SC_13200 ...
16:29:56  （面板自动弹出 → f07，战力=0）
16:29:57  << SC_16400×8, << SC_11600(wing power=999), << SC_15501, << SC_13771, << SC_10921,
           << SC_16706, << SC_10932, << SC_16500, << SC_17200, << SC_18900(fabao), ...
16:29:58  HUD 已 724112（f08）
```

**出向命令直方图（全窗口）**：10103×1, 10301×1, 10302×1, 10303×1, 10502×24, 10601×1, 10615×1, 10911×1, 11200×1, 11601×1, 13300×1, 13340×1, 14901×1, 15203×1, 16400×8, 16600×1, 16800×1, 16900×1, 18900×1 —— **全程无 CS_10304、无 CS_10306**。

**重开面板零流量**：从捕获结束到 r2 重开（16:31:49→16:40+），tcp.log 无任何非心跳 `>> cmd=`。即重开渲染 100% 走本地缓存。

### 1.3 静态证据（analysis\ 既有反汇编，未重反编译）

`analysis\_role_ctrl_dis.txt`：
- proto#14 `sender10303`：发空包 CS_10303；proto#15 `rgp_hander10303`：`getData():updateRoleAllAttr(body)`（**就地更新 RoleData 里的 vo 属性/power**）
- proto#16 `sender10304` / proto#17 `rgp_hander10304`：收包后 `RoleVo:New()` + `initAttributeData` + `Fire(DISPATCH_PLAYER_VO_EVENT)` —— **但客户端从不发 CS_10304，该 handler 本会话从未触发**
- proto#11 `rgp_hander10301`：`getData():initRoleBaseData(body)` + `GameData:setRoleVo(data:getRoleVo())` —— **SC_10301 重建角色基础 vo（10301 帧不含 power 字段）**
- proto#42 `getCurrRoleVo()`：`curr_role_vo` 为 nil 时回退 `getData():getRoleVo()`；proto#43 `getSelfRoleVo()` 直接读 RoleData.vo

`analysis\_display_panel_dis.txt`：
- proto#10（setData 渲染）：`self.power_value:setString(vo.power)` —— **打开时一次性把 vo.power 写成标签字符串**；同时写 name/lev/career
- proto#15：存在一个事件监听（校验 `is_role` 且 `role_vo.bid==事件 bid` 才 setString）——但首开时 vo.bid 尚未就位，校验不通过，且快照早已完成

### 1.4 根因链（修正版）

1. 冷启动登录：客户端在登录屏就请求 10302/10303（16:29:53），SC_10303（含 power=724112 + attr 大表）即时到达
2. 10103 重登录入场景（16:29:55）：服务端推送风暴，其中 **SC_10301 在 16:29:55 到达，`initRoleBaseData` 重建角色基础 vo**（此时 power/装备视图尚处过渡态：0 / 空）
3. 游戏流程**在风暴中途（~16:29:56）自动弹出角色背包面板** → setData 对"过渡态 vo"做一次性快照：power_value="0"、装备空（+号 + `+-0123456789` TextAtlas 占位，即 issue_placeholder_string.md 所述未被 setString 的默认 TextAtlas 文本）
4. 风暴继续（16:29:57）：10502 六件装备、各养成系统 push 陆续到位，vo 逐步补全 → HUD 直接读 RoleData.vo，实时刷新到 724112
5. **已打开的面板不会重渲染**：updateRoleAllAttr 更新共享 vo，但面板 power_value 标签定格在快照 "0"（f08、r0 开 10 分钟仍 0 即证）
6. 手动重开面板：重新 setData 读已补全的 vo → 724112 + 真实装备（r2），零网络流量

**结论：F1 是"面板自动弹出时机 vs 本地 vo 补全节奏"的竞态，表现为一次性快照定格；不是缺 10304 推送。**

---

## 2. 修复方案评估（任务 2）

### 方案 A：注入补丁（patch_apk.py 链路 B observer 热补丁）—— 不实施

- 现状：已安装包 = fakelogin，**无注入块**；热补丁通道（`dsh_patch.lua` 加载器）只存在于 probe 包
- 既有结论（lua_injection_round2.md）：**observer 注入块两种形态都会破坏启动**（全注入=登录报错无业务 HTTP；obs-only=卡资源包重试循环）；round2 提的 A+B 修法（observer 默认不包 XHR + 延迟注册）**未实现、未验证**
- 要走 A 需先：改 server/observer.lua 去 XHR 包装 → 重打包签名安装 → 写 Lua 补丁 hook 面板 setData 延迟重渲染 → 再验启动回归。收益（ cosmetic 自愈缺陷）<< 风险（已两次实测启动卡死）
- 判定：**风险高，本轮不做**

### 方案 B：luac 字节码补丁（改 role display panel 常量/逻辑）—— 不实施

- 工具链现状：tools/luajit_dis.py 仅反汇编；build_apk.ps1/patch_apk.py 只做二进制 URL 字节修补 + 注入加载流 Lua 文本，**不能替换 game/ 下已编译 luac 资产**
- 手编 LuaJIT 2.0 字节码（改指令长度/常量表引用）极易破坏校验与内存布局；且无回滚粒度外的快速验证
- 判定：**无工具链、风险极高，本轮不做**

### 方案 C：服务端补推（推荐）—— 本阶段只读边界外，记录

- 依据：登录链已有"10200 在 10300 后重推"的既有模式；SC_10303（含 power+attr 大表）当前先于 SC_10301 到达，被 10301 的 initRoleBaseData 重置节奏打乱
- 最小服务端改法：在 SC_10301 + 场景推送风暴收尾后（对齐现有 10200 重推点），**补推一次 SC_10303（attr+power）或 SC_10306**；vo 补全后若面板已开，updateRoleAllAttr 就地刷新共享 vo（HUD 已证该通路有效）
- 若客户端面板事件监听（display_panel proto#15 校验 bid）能在 vo 补全后触发重渲染，则一并闭环；若不能，次优是客户端 hook（回到方案 A 前置条件）
- 判定：**根因级修复、改动小、风险低；但 mock_server 本阶段只读，留待下一阶段服务端可写时实施**

### 本轮实际改动

- **客户端：无**（未 install、未 repack、未 push 文件；lastUpdateTime 仍 2026-10-14 23:54:10）
- **服务端：无**（只读 tcp.log/server 源码）
- 新产物 APK：**未生成**（无需回滚操作）

---

## 3. 实机验证记录

| 验证项 | 结果 | 证据 |
|---|---|---|
| F1 冷启动复现 | ✅ 首帧战力=0、装备空、占位串 | f07_22.56s.png / f08_25.30s.png / r0_now.png |
| 面板不自动恢复 | ✅ 开 10 分钟仍 0 | r0_now.png |
| 重开自愈 | ✅ 724112 + 6 件真实装备 + 全属性 | r2_reopen.png |
| 重开零网络流量 | ✅ tcp.log 无新 CS | 偏移 286573 后仅心跳 |
| HUD 全程正确 | ✅ 724112 | f08/r0/r2 右上角 |
| 原包完好 | ✅ 280,472,477B / 2026-09-29 | Test-Patch + Get-Item |
| 基线包未被覆盖 | ✅ lastUpdateTime=2026-10-14 | dumpsys package |

回归：未做任何安装，无需回归；截图过程仅点击 UI 关闭/重开面板，未触碰 mock_server。

---

## 4. 次要项诊断（任务 3，只读）

### 4.1 "我要变强"占位文本"我是技能名" —— 配置映射缺口
- 静态：`analysis\_advance_panel_dis.txt` createItem proto 字符串表含 `'我是技能名'`（行 1682），行 1789 `KSTR '我是技能名'`；随后 `setString(item.mulu_name)`（行 122-123）
- 推断：该串是客户端 createItem 的**硬编码兜底标题**；当 item.mulu_name 解析为空（服务端下发/本地 promote 列表引用了客户端 `Config.Promote_Catalog` 没有的 id）时显示
- 修复建议：下一阶段对齐 promote 列表 id 与客户端 Promote_Catalog 配置键（与技能 bid 问题同族——id 空间错位）；客户端侧无法用 luac 补丁低成本修

### 4.2 "提升"按钮空白暗面板 —— 子面板内容未注册
- 实测：点左侧 (230,250) → 弹出暗色矩形容器（约 360×420，右上有 X），**零子控件渲染**（s3_tisheng.png）
- 推断：该二级飞动面板的容器被创建，但内容列表为空——导航注册表（nav_secondary_menu / ctrl 注册）在该上下文无子项；非网络问题（按钮按下无业务 CS，tcp.log 佐证）
- 修复建议：需 observer 注入 dump nav 注册表确认（方案 A 前置条件）；本轮不深挖

### 4.3 技能面板空列表 —— 已知 id 空间错位
- tcp.log 实证：`<< 10621 SC_10621 world_lev=1 skill_list=4`（16:29:56，服务端**有推** 4 条技能）
- 既有结论（lua_injection_channel_round.md §2.1）：mock 发的 skill_list = 10000/10001/10002/10822，客户端修炼表键 = 10801+ 起，id 错位导致列表渲染为空
- 修复建议：服务端 10621 改发客户端配置表内的 skill bid（下一阶段服务端可写时）

---

## 5. 风险清单

1. **未修 F1**：首开面板战力=0 持续到手动重开（HUD 正确，不影响玩法数据）；下一阶段服务端补推 10303/10306 即可闭环
2. 方案 A/B 若未来启用：observer 注入块有两次启动卡死前科，须先做 observer 最小化（去 XHR 包装）+ 延迟注册 + 单独冒烟启动通过后再接业务 hook
3. `+-0123456789` 占位串与 F1 同源（首拍时装备视图未填充），随 F1 修复一并消失；单独修无意义
4. 本报告"根因链"基于 tcp.log 时序 + 反汇编控制流推断；vo 内部字段级重建行为（initRoleBaseData 是否逐字段保留 attr）未做运行时 dump（需 observer，属方案 A 前置）

## 6. 自检记录

- [x] 原包存在性：`Test-Path patched\jstm_1411_fakelogin_aligned.apk` = True（280,472,477B）
- [x] 未生成新 APK、未 install、未 push 文件
- [x] mock_server 全程只读（仅 tail tcp.log）
- [x] 证据截图全部落盘 `analysis\runtime_evidence\c2_2_f1_repro\`
- [x] 不伪造：F1 未实施客户端修复，如实记录方案 C 为下一阶段动作

## 7. 交付物

- 本报告：`docs\_raw\c2_2_pilot_report.md`
- 证据目录：`analysis\runtime_evidence\c2_2_f1_repro\`（f03~f47 冷启动序列 + r0/r1/r2 + s3_tisheng）
- 复现脚本：`tools\_c22_f1_capture.ps1`
