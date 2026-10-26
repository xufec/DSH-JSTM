# C3.1 第二分片：协议与客户端同步核验报告

- 日期：2026-10-15（周四）
- 环境：MuMu emulator-5554（2560×1440 横屏），客户端 `com.shiyue.dldl.ewan.baidu2` v1.4.9；mock_server TCP 9000 / HTTP 8080
- 本分片边界：只读（不修改任何源码/文件）；仅新建本文件与 `analysis\runtime_evidence\c3_1_shots\` 截图
- 实测会话：22:35:30 连接 → 22:35:46 S1 补推触发 → 22:41 仍心跳在线；日志取自重启后全新 `server\logs\tcp.log`（restart 时已轮转，旧会话留存 `tcp_prevR.log`）
- 服务端本次启动：`tools\restart_server.ps1` 第4步 WMI 分离启动**失败**（python 路径含空格 `"User Data"`，cmd 嵌套引号被 WMI 解析成 `'""' 不是内部或外部命令`）；按 S1 报告手动方式：`Invoke-CimMethod Win32_Process Create` 直接以**带引号 exe 路径**拉起 `mock_server.py`（PID 30004，9000/8080 均监听，status 200）

---

## §1 登录协议时序表（实机抓取，tcp.log 为准）

帧计数口径：tcp.log 的 `(N bytes)` 为完整帧（4B 长度头 + 2B 命令号 + body）。
方向：CS = 客户端→服务端，SC = 服务端→客户端。

| # | 时间 | 方向 | 命令 | 整帧字节 | body 字节 | 关键字段 / 说明 |
|---|------|------|------|---------|----------|----------------|
| 1 | 22:35:30 | CS | 10001 FirstPack | 23 | 17 | `00 0b "game_client" 00 00 00 00`；无 SC 回包 |
| 2 | 22:35:30 | CS | 1110 CSAccountLogin | 249 | 219 | 10 个 key=value：account=dsh_local, timestamp=1792074927, enter_srv_id="", platform=ewan, device_id="Redmi_rubens(22041211A)", gettui_cid=ec2eb3…9928f, idfa="", token=dsh_token, channelId=1, sign=dsh_sign |
| 3 | 22:35:30 | SC | 1110 SCAccountLogin | 30 | 24 | code=0；roles=[{rid=1001,srv_id="1",name="DSH",lev=70,sex=0,career=1,is_online=?}]；roles=1，ver=1.4.9 |
| 4 | 22:35:34 | CS | 10001 FirstPack（重试） | 23 | 17 | `00 0b "game_client" "dsh_"` —— 连接建立后 fake-login 补丁二次握手 |
| 5 | 22:35:34 | CS | 1110（重试） | 249 | 219 | 同 #2 载荷 |
| 6 | 22:35:34 | SC | 1110 | 30 | 24 | 同 #3 |
| 7 | 22:35:34 | CS | 10302（预入场查询） | 10 | 4 | `00 0a 00 07` |
| 8 | 22:35:34 | SC | 10302 | 128 | 122 | lev=70 exp=14439 gold=1800041 gold_acc=5000（diamond 尾标当时未读，见 #18） |
| 9 | 22:35:34 | CS | 13340 | 10 | 4 | → SC_13340 76B（profile name=DSH lev=70） |
| 10 | 22:35:34 | CS | 14901 | 34 | 28 | （含 `00 00 03 e9 "acco"`）→ SC_14901 cur_bid=0 titles=0 |
| 11 | 22:35:34 | CS | 10331 | 14 | 8 | `00 00 03 e9 "acco"` → SC_10331 9B skill_bid=1001 |
| 12 | 22:35:34 | CS | 10303（预入场查询） | 10 | 4 | `00 00 03 e9`（rid=1001） |
| 13 | 22:35:34 | SC | 10303 | 204 | 198 | hp_max=7305 atk_s=1813（含 power + 24 项 attr 大表；power 字段由 role_power() 现算，见 §2） |
| 14 | 22:35:34 | CS | 15203 | 10 | 4 | → SC_15203 9B code=0 |
| 15 | 22:35:34 | CS | 12403 | 14 | 8 | `00 00 27 24 "acco"` → SC_12403 mission_bid=10020 code=1(TRUE)（幂等） |
| 16 | 22:35:36 | CS | 10103 RoleReLogin | 21 | 11 | rid=1001, srv_id="1", "ount"（ount/ount） |
| 17 | 22:35:36 | SC | 10103 | 21 | 15 | code=0；随后服务端**主动推送**三连：10200(19B 进图) / 10201(653B 网格：roles=1 npcs=25 mons=1 elems=2) / **10305(58B 资产增量，含 practice_exp)** |
| 18 | 22:35:36 | CS | 10921 | 10 | 4 | → SC_10921 17B world_lev=1 |
| 19 | 22:35:36 | CS | 10300 CSRoleInit | 10 | 4 | rid=1001 |
| 20 | 22:35:36 | SC | 10300 handler 内联推送 | — | — | 10200(19B) 重推 + 10201(653B) 重推 + 10200(19B) 再重推 + 12400(42B mission_list=1)；排程两条：「12400 补推 +12s」「**S1 风暴收尾补推 +5s（10303/10306/13781/13786）**」 |
| 21 | 22:35:36 | CS→SC | 风暴查询簇 | — | — | 10800→154B(邮件1) / 13300(好友0) / 10923(6B) / 10502(5B, bag_code=1 items=6：309/28560×2, 310/28515×2, 312/21403×3, 315/13001, 316/46022, 319/25890) |
| 22 | 22:35:36 | CS | 10301 角色基础信息 | 10 | 4 | `01 01 03 e9` |
| 23 | 22:35:36 | SC | 10301 | 122 | 116 | role info（**无 power 字段**，见 §2/§3）——客户端 `initRoleBaseData` 重建 RoleVo 基础段；冷启动下 pre-role-state 为空 → `NavCtrl:openView()` **自动弹出角色面板** |
| 24 | 22:35:36 | CS→SC | 风暴续 | — | — | 10922→89B(act_list=9) / 10924(act_list=0，R49 抑制弹窗) / 13200 / 18803→38B / 11300→10B / 11301→8B / 14000→35B(阵型6 上阵5) / 14009 / 20500→19B / 20504×2 / 19600(签到95档) / 14600→15B / 14100 / 17600 / 11700→22B / 10527 / 10502 再次(6件装备) / 13806 / 17200 / 13579(北斗) / 13580(worship×5) / 13704→10B / 10589… |
| 25 | 22:35:46 | CS | **1199 心跳** | 10 | 4 | `07 00 00 00` —— **S1 补推触发点**：距 10300 排程(22:35:36)+5s 已过；心跳周期 8s，此为 deadline 后第一跳 |
| 26 | 22:35:46 | SC | 1199 回包 | 10 | — | time |
| 27 | 22:35:46 | SC | **10303（S1 风暴收尾补推）** | 204 | 198 | hp_max=7305 atk_s=1813（同 #13 载荷，attr 大表 + power） |
| 28 | 22:35:46 | SC | **10302（S1-B 补 diamond）** | 128 | 122 | diamond=100000（roles.diamond=0 与 assets.diamond=100000 已合并后重发） |
| 29 | 22:35:46 | SC | **10306（S1 风暴收尾补推）** | 88 | 82 | mspd=100，**power=724112** |
| 30 | 22:35:46 | SC | 13781（S1） | — | — | total_val=10 |
| 31 | 22:35:46 | SC | 13786（S1） | — | — | richang=24 |
| 32 | 22:35:54 | CS→SC | 1199 心跳 | — | — | 触发 12400 补推（42B，mission_list=1，「NpcCtrl 就绪后」） |
| 33 | 22:35:54 起 | CS | 1199 心跳周期 | 10 | 4 | 每 8s 一跳（22:35:54 / 22:36:02 / 22:36:10 … 22:41:08 持续在线）；期间零星业务帧 10204(移动)×2、16601、10341、10999 |

### 1.1 登录/重登帧序要点（相对 10300 排程时刻 t0=22:35:36）

- **t0-2s**：预入场查询簇（10302/10303 在登录屏即由客户端主动请求并得到应答）
- **t0**：10103 入场景 → 10305 主动推送；10300 → 10200×3 + 10201×2 + 12400 + 排程
- **t0+0s（同毫秒）**：10301 应答到达 → 客户端重建 RoleVo 基础段 + 自动弹出角色面板
- **t0+10s**：心跳 1199 → S1 补推 10303/10302/10306/13781/13786（deadline t0+5s，实际由 8s 心跳节拍对齐到 t0+10s）
- **t0+18s**：心跳 → 12400 补推

### 1.2 角色面板首帧表现（截图实证）

| 截图 | 时刻（22:3x） | 画面 | 综合战力 | 备注 |
|------|--------------|------|---------|------|
| `01_login_seq_n01.png` | 36:05 | 角色面板**自动弹出**（背包页） | **0** | 6 装备格空 + 绿加号 + `+-0123456789` TextAtlas 占位串；**HUD 右上 = DSH 724112**；50级礼包弹窗叠加。此时 S1 补推（22:35:46）已过去 19s |
| `01_login_seq_n02.png` | 37:0x | 面板仍开 | **0** | HUD 仍 724112 |
| `01_login_seq_n10.png` | 38:48 | 手动点 HUD 重开面板 | **724112** | 6 件真实装备图标（武器/盔/甲/靴/鞋/腰带，紫框）；属性齐全（生命7305/物攻1813/物防1579/法攻795/法防611/命中337/躲闪226/暴击113/抗暴90）；经验 14439/2600094；头像已渲染；货币 180万/9,999万/990万 |

- 重开面板期间（22:38:45 点 HUD → n10）tcp.log **无任何 10301/10302/10303/10306 请求帧**（仅有 10204 移动帧与心跳）——面板 100% 读本地缓存，与 c2_2「r2 零流量」结论一致。
- **与 S1 自测记录的差异**：S1 报告称「本次冷启动面板未自动弹出」；本分片冷启动**自动弹出复现**（n01）。自动弹出与否取决于 `isSameRoleData(srv_id,rid)` vs pre-role-state（冷启动 pre-state 为空 → openView），属概率/时序相关行为。

---

## §2 三命令（10301/10303/10306）服务端处理路径表 + 字段来源

字段定义三源一致：`protocol\fields.json` ≡ `server\proto_defs.py` ≡ 客户端字节码 spec（cmd_resolve_103.luac）。

### 2.1 处理路径表

| 命令 | 方向语义 | handler（注册点） | 帧构建函数 | 推送时机 / 触发者 |
|------|---------|------------------|-----------|------------------|
| **SC_10301** | CS 请求 → SC 应答 | `server\role\handler.py` @register(10301)（原 mock_server L16267-16272 块已注释迁移） | `role\storage.py build_10301(role_state(), cfg.skills)` | 客户端风暴中主动请求（实测 22:35:36，10300 之后） |
| **SC_10302** | CS 请求 → SC 应答；S1-B 也可主动补推 | `server\role\handler.py` @register(10302)；补推块 `mock_server.py` L10055-10058 | `role\storage.py build_10302(st)` | ①预入场查询（22:35:34）②S1-B 心跳补推（22:35:46） |
| **SC_10303** | CS 请求 → SC 应答；S1 也可主动补推 | `server\role\handler.py` @register(10303)；补推块 `mock_server.py` L10045-10050 | `role\storage.py build_10303(role_state(), skills, cfg.attr)` | ①预入场查询（22:35:34）②S1 心跳补推（22:35:46） |
| **SC_10305** | 服务端主动推送 | `mock_server.py` 10102/10103 handler（L16065） | `build_10305(cfg)` = `currency\service.db_get_assets(rid)` + CodeToAssets 标签 + practice_exp(skills bid=10822) | 10103 应答后立即推（22:35:36） |
| **SC_10306** | CS 请求 → SC 应答；S1 也可主动补推 | `server\attribute\handler.py` @register(10306)；补推块 `mock_server.py` L10061-10065 | `attribute\service.attr_table_10306(role_attr_dict)` + mspd + `power_mod.role_power()` | 客户端本会话**从未请求**（实测无 CS_10306）；仅 S1 心跳补推（22:35:46） |
| 排程点 | — | `mock_server.py` 10300 handler（L17531-17535）：`_login_repush_at = time.time()+5.0`；心跳 1199 handler（L10001-10017）检测到点 → 顺序发 10303→10302→10306→13781→13786 | — | 10300 收包后排程；下一次心跳触发 |

### 2.2 字段级来源（谁带 power / 谁不带）

| 字段组 | SC_10301（122B） | SC_10302（128B） | SC_10303（204B） | SC_10306（88B） |
|--------|-----------------|-----------------|-----------------|-----------------|
| **power（综合战力 u32）** | **❌ 无** | **❌ 无** | ✅ skill_list 之后第 1 个 u32 | ✅ 帧尾 u32 |
| **attr 大表（24 项）** | ❌ | ❌ | ✅ u16 计数 + 4×u16 + 20×u32 | ✅ 同构（中段 4×u16 + 12×u32 + 4×u16 + 4×u32，82B body 逐字节吻合） |
| 身份（rid/name/lev/career/face/title/gid…） | ✅ 全 | lev | ✅ 全 | ❌（仅 attr+mspd+power） |
| 资产（exp/gold/coin/diamond…） | ❌ | ✅ lev+28×u32 + 尾 diamond/rainbow_diamond | ✅ 12×u32（含 exp/gold/coin…） | ❌ |
| mspd | ✅ u16 | ❌ | ✅ u16 | ✅ u16 |

**power 数值来源（10303/10306 同源）**：`attribute\service.role_power()` = `power_mod.calc_power(attr_dict)`；attr_dict = `ATTR_DEFAULTS` ← cfg.attr ← `db_get_attr(rid)`（role_attr 表）；非 config.json 硬编码。实测两帧 power=724112。
**10301 字段来源**：`role_state(cfg)` = ROLE_DEFAULTS ← cfg.role ← DB roles 行 ← db_get_assets() 合并；全帧无 power、无 attr、无 gold。

---

## §3 客户端角色对象生命周期证据（静态反汇编 + 实机交叉验证）

证据文件：`analysis\_role_ctrl_dis.txt` / `_role_data_dis.txt` / `_role_vo_dis.txt` / `_display_panel_dis.txt`（均为既有 luac 反汇编，本分片未重反编译）。

### 3.1 生命周期表

| 环节 | 证据（反汇编 proto） | 行为结论 | 证据等级 |
|------|----------------------|---------|---------|
| **RoleVo 创建** | `_role_data_dis.txt` proto#6（RoleData:initAttribute(body)）：`if not role_vo then role_vo = RoleVo:New()`（proto#0 __init 将 132 个字段**全部置 0**，含 `power=0`）再 `role_vo:initAttributeData(body)`；否则跳过 New 直接就地解析 | 首次收到含 attr 的帧时创建；新建瞬间 power=0 | **A（反汇编直读）** |
| **SC_10303 处理** | `_role_ctrl_dis.txt` proto#15 rgp_hander10303 → `getData():updateRoleAllAttr(body)`；映射至 RoleData ChildRef(#5)=proto#5：`initAttribute(body)` → `setAllDataStatus(2)` → dispatchUpdateBaseAttr / dispatchUpdateAssets / dispatchUpdateFightAttr（proto#1/2/4） | **就地刷新共享 vo**（HUD 读此 vo，故 HUD 正确） | **A** |
| **SC_10301 处理** | proto#11 rgp_hander10301 → `getData():initRoleBaseData(body)` → 置 `init_role=true` → `GameData:getInstance():setRoleVo(getData():getRoleVo())` → setBubble(chat_bubble)/setWakeStatus(insight_status) → DengluMgr 缓存 + setAutoLogin/setDefaultLogin → `if not getPreRoleState() or not isSameRoleData(srv_id,rid): NavCtrl:openView()` → analyseLevel → setPreRoleState(1) → **Fire(ROLE_CREATE_SUCCESS)** → sender18900 | ①把 10301 body 的基础段写进共享 vo（RoleVo:initAttributeData 按 body 键逐项 setRoleAttribute，proto#9；**body 无 power/attr 键 ⇒ 不重置已写入的 power**）②冷启动 pre-state 空 ⇒ **自动打开角色面板** | **A** |
| **面板读战力** | `_display_panel_dis.txt` proto#2（setData 入口）：is_role ⇒ self.role_vo=vo → showRoleView → setData(vo)；proto#10 setData：`power_value:setString(vo.power)`（步骤 35-39）+ name/lev/career/initRpgRoleModel(vo.resource) | **打开时一次性快照 vo.power** 写进标签 | **A** |
| **面板活刷新** | proto#15（hero_attr_event 监听）：`if self.is_role and self.role_vo.bid == event.bid then power_value:setString(event.power)`；proto#21 注册 `HERO_ATTR_CHANGE` | 自我面板的 `role_vo.bid` 为 nil（RoleVo 无 bid 字段）⇒ **bid 恒不匹配 ⇒ 已打开面板永不刷新 power 标签** | **A**（机制）；首开时 vo.bid 未就位的实测判定引 c2_2 |
| **面板重开** | 打开即重走 proto#2/proto#10 快照 | 重读已补全 vo ⇒ 724112（n10 实证） | **A + 实机 n10** |

### 3.2 过渡态窗口如何被 S1 补推覆盖（本会话时序还原）

1. 22:35:34 预入场 SC_10303 到达：若 RoleData 单例已就绪则创建/刷新共享 vo（power=724112）；若未就绪则该帧被早期逻辑跳过（getData() 判空分支，proto#15 步骤 3-4）——**此分支本会话无 observer dump，属 UNKNOWN**。
2. 22:35:36 SC_10301 到达：`initRoleBaseData` 写入基础段；冷启动 pre-state 空 ⇒ 同秒 `NavCtrl:openView()` 自动弹出面板 ⇒ setData 快照 **vo.power 此时=0**（n01/n02：综合战力 0、装备格空）。
3. 22:35:36~38 风暴帧（10502 六件装备等）陆续到位：RoleCalculate/AttrExt 本地计算 + 推送事件逐步补全共享 vo。
4. 22:35:46 S1 补推：SC_10303/10306 携带 power=724112 + attr 大表再次就地写入共享 vo（updateRoleAllAttr 通路）⇒ HUD（直读共享 vo）显示 724112（n01 已见）。
5. **但已打开的面板 power_value 标签定格在快照 "0"**（proto#15 bid 门不触发），直到玩家手动关闭重开（n10=724112）。

### 3.3 UNKNOWN 项（明确所需证据，不猜测）

- **U1**：预入场 SC_10303（22:35:34）是否真的把 power 写进了 RoleData 共享 vo（vs 被 getData() 判空跳过）。所需证据：observer 注入 dump RoleData.role_vo 对象在 22:35:34 / 22:35:36 / 22:35:46 三个时刻的 power 字段（c2_2 §5 已标注，属方案 A 前置）。
- **U2**：`initRoleBaseData` 是否对 vo 做整表重建（逐字段保留 attr 的判定）。所需证据：同 U1 的运行时 dump 或 role_data.luac 全量反编译。
- **U3**：自动弹出面板的精确触发点（openView 后是否还经过其他中间弹窗）。所需证据：NavCtrl 注册表 dump。

---

## §4 结论：F1 修复后时序是否闭合 + 剩余风险

### 4.1 时序闭合性判定

| 链路环节 | 判定 | 依据 |
|---------|------|------|
| S1 补推排程是否触发 | ✅ 闭合 | 10300 排程 +5s（实测 22:35:36）→ 心跳 1199 于 22:35:46 触发补推（deadline+10s，8s 心跳节拍对齐） |
| 补推帧序是否完整 | ✅ 闭合 | 10303(204B) → 10302(128B, diamond=100000) → 10306(88B, power=724112) → 13781 → 13786，与设计一致 |
| HUD / 共享 vo 战力同步 | ✅ 闭合 | n01/n02 HUD=724112（补推后 19s 仍正确）；SC_10306 power=724112 与 role_power() 算法一致 |
| **自动弹出的角色面板首帧战力** | ❌ **未闭合** | n01/n02 实证：补推已过去 19s，自动弹出面板仍显示**综合战力=0** + 装备格空 + 占位串 |

**总判定：F1 方案 C 对"数据通道"闭合（vo/HUD/资产/diamond 全部正确），但对"自动弹出面板的首帧快照"不闭合。** 根因在客户端：面板 setData 是一次性快照（proto#10），活刷新监听 proto#15 的 `role_vo.bid==event.bid` 门槛对自我角色永不通过——服务端补推到达再多次，也无法改写已定格的标签。这解释了：①为何 HUD 对而面板错；②为何 S1 自测"面板未自动弹出"时感觉已修好（打开即 724112）；③为何本分片冷启动自动弹出复现时问题仍在。

### 4.2 剩余风险

1. **R1（本分片实证）**：冷启动自动弹出面板时，首帧战力=0 且不自愈，直到手动重开。玩家观感为"面板坏了"。彻底修复需客户端侧动作（面板 setData 改为订阅 vo 刷新，或 openView 延迟到补推完成后由服务端在补推末尾发"面板可渲染"事件）——服务端已无可补的帧（10303/10306 都带正确 power）。
2. **R2**：补推实际触发时刻 = deadline + 最多一个心跳周期（实测 +10s 而非 +5s）；若未来风暴延长或心跳改频，窗口需重算。
3. **R3**：自动弹出概率依赖 pre-role-state（冷启动必弹 / 切号不弹），行为不完全确定。
4. **R4**：diamond 双源（roles.diamond=0 vs assets.diamond=100000）靠 role_state 合并兜底；若后续改动 role_state 合并顺序，10302 尾字段会回落 0。
5. **R5**：restart_server.ps1 在本机失效（python 路径含空格致 WMI cmdline 解析失败），本次用手动 WMI Create 拉起；脚本本身待修。

---

## §5 自检记录

- [x] 未修改任何源码/配置/客户端文件；仅新建本 md 与 c3_1_shots 截图
- [x] tcp.log 帧字节数与字段全部来自实机日志（22:35:30→22:41:08），未编造
- [x] 服务端静态路径三源（fields.json / proto_defs.py / build_*）逐一核对行号
- [x] 客户端结论均标注证据等级（A=反汇编直读；U1-U3=UNKNOWN + 所需证据）
- [x] 实机（§1/§1.2）与静态（§2/§3）证据分开标注
- [x] 截图 10 张落盘 `analysis\runtime_evidence\c3_1_shots\`（n01/n02=面板首帧 0；n10=重开 724112）
- [x] 客户端未 install/repack；原包基线未触碰

## §6 交付物清单

- 本报告：`docs_raw\c3_1_protocol_verify.md`
- 截图：`analysis\runtime_evidence\c3_1_shots\01_login_seq_n01.png` … `01_login_seq_n10.png`
- 日志佐证：`server\logs\tcp.log`（重启后全量会话，22:35:30 起）
