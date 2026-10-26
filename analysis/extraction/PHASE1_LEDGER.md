# PHASE 1 取证总台账 — R1–R12 / V1–V12（JSTM 1.4.11 实机）

> 本文件是 PHASE 1 的**唯一汇总入口**：逐条给出 R/V 项目的**结论 + 证据等级 + 证据文件**。
> 等级：`CONFIRMED > VERIFIED > STRONG_INFERENCE > INFERENCE > UNKNOWN`。
> 约束遵守：**未修改 `mock_server` 核心逻辑**（`server/*.py` 全程零改动，多轮核验）；
> 全部手段为 只读端点 / 抓包解码 / 实机截图 / adb 输入。

---

## 〇、三档证据来源（决定每条能到什么等级）

| 档 | 来源 | 覆盖范围 | 可支撑等级 |
|---|---|---|---|
| **CS 原始字节** | `server/logs/tcp_*.bin`（7,700+ 个文件，全部为 CS 方向） | 客户端→服务端方向 | **CONFIRMED** |
| **SC 原始字节** | `GET /DSH_ADMIN/battle_replay`（服务端构造的 hex） | **仅战斗族** 6 帧 | **CONFIRMED** |
| **SC 字段值注释** | `tcp.log` 的 `<<` 行（655 行中 **253 行**带 `=` 值） | 服务端自述关键字段 | CONFIRMED（服务端实现）／**不等于客户端渲染** |
| **SC 结构规格** | `protocol/fields.json`（3,553 条，1.4.9 `cmd_resolve` 反汇编） | 全量结构 | CONFIRMED（结构） |
| **客户端 UI** | MuMu 实机截图（2560×1440） | UI 渲染结果 | **VERIFIED** |

---

## 一、R1–R12（协议实值）

| # | 项 | 实机观测 | 已解出的字段实值 | 等级 | 证据文件 |
|---|---|---|---|---|---|
| **R1** | 首包 + 账号登录 | `10001` ×680、`1110` ×775 | `10001={key:"game_client"}`；`1110` **10 个参数**：account/timestamp/enter_srv_id/platform/device_id/gettui_cid/idfa/token/channelId/sign | **CONFIRMED**（CS 结构）；取值来自补丁注入 ⇒ 原版取值 UNKNOWN | `phase1_r_series_field_values.md` §2 |
| **R2** | 建角 | `10101` ×3 | 规格 `CSRoleCreate_10101={sex,name,career,playform,…}`（实机 3 帧） | **CONFIRMED**（存在 + 规格） | `phase1_cs_inventory.md` |
| **R3** | 登角 | `10102` ×187、`10300` ×456 | `10102={rid:1001, srv_id:"1"}`；`10300={}` | **CONFIRMED** | 同上 §2.3 |
| **R4** | 选角重登 | `10103` ×464 | `{rid:1001, srv_id:"1"}` | **CONFIRMED** | 同上 |
| **R5** | 进场景 / 进图 | `10206` ×56；`10200` 为服务端推送（无 CS） | `10206={x:10005}`（= `map_bid` 乾坤日月谷）；服务端回 `code=1` 但**不改状态** | **CONFIRMED**（CS）；**断点已定位** | `phase1_r_series_and_afk_chain.md` §二 |
| **R6** | 移动 | `10204` ×2183 | `{x:uint16, y:uint16}`（**仅 4 字节**）；一次点击产生 3–4 帧（分步寻路）；屏幕→世界 ≈80–94 px/单位 | **CONFIRMED** | 同上 §一 + `phase1_r_series_field_values.md` §一 |
| **R7** | 战斗族 | `20002` ×34（CS） | CS：`{mon_id:int32}`∈{20001,20022,10105}；**SC 原始字节全解**：`20002{code,msg}`、`20010{round,…,fighter_info_list[]}`、`20012{skill_play[]}`、`20013{magic_play[{hit,hp_max,hp,is_target_die}]}`、`20020{result}`、`20023{role_hurl_list[{hp,hurt}]}` | **CONFIRMED**（CS + SC 原始字节） | `phase1_sc_battle_replay.md` |
| **R8** | 背包 | `10502` ×6282、`10552` ×92 | `bag_code ∈ {1,2,3,4,5,6,7,8,12,13,16,17}`；`SC_10552 code=1 bag_code=1 old=95 new=100`（扩容） | **CONFIRMED** | `phase1_r_series_field_values.md` §2.5 |
| **R9** | 邮件 | `10800` ×458 | CS 空消息（`{}`）；服务端侧 195 封（`/DSH_ADMIN/mail_list`） | CS **CONFIRMED**／SC 值 B 档 | `phase1_v_server_reference.md` |
| **R10** | 排行 | `12901` ×5、`12931` ×4、`12971` ×3 | 服务端值：战力榜 `val=724112`、等级榜 `val=0`、分项 `战力=724112（分项未取证=0）` | **CONFIRMED**（服务端值） | `phase1_v_series_panels.md` V-3 |
| **R11** | 任务 | `12400` ×2、`12403` ×110、`20504` ×182 | `SC_20504={type, mission_list[{mission_id,status,val,tot_val,target,ext_list[],item_list[]}]}` | **CONFIRMED**（结构 + 观测） | `phase1_r_series_field_values.md` §四 |
| **R12** | 商城 | `12801` ×2 | 仅确认命令存在；商品/价格/实付**未取证** | 存在性 **CONFIRMED**；内容 **UNKNOWN** | `phase1_cs_inventory.md` |

**覆盖面**：实机共解出 **316 个 CS 命令 / 44,911 帧**，规格覆盖率 100%。

---

## 二、V1–V12（数值标定）

| # | 项 | 服务端值 | 客户端 UI | 等级 | 说明 |
|---|---|---|---|---|---|
| **V1** | 怪物 HP | **字段已定位**：`SC_20010.fighter_info_list[].hp_max`（mock=1950） | 未取证（未进战斗） | 字段 **CONFIRMED**／数值 **UNKNOWN** | 取数位置已解决，真值需真服 |
| **V2** | 怪物攻防/暴击 | `fighter_info_list[]` 中**无 atk 字段** | — | **UNKNOWN** | 需找其它 SC 或服务端公式 |
| **V3** | 伤害公式 | `SC_20013.magic_play[].hit`（mock=127/次）、`SC_20023[].hurt` | — | 结构 **CONFIRMED**／公式 **UNKNOWN** | 同上 |
| **V4** | 经验/金币产出 | mock 值 | — | **UNKNOWN** | 需真服 |
| **V5** | 掉落结果/概率 | `config_drop` 首杀池（20012→1001 等） | — | 结果 **CONFIRMED**（配置）／概率 **UNKNOWN** | 概率需实机标定 |
| **V6** | 装备属性/强化增量 | `config_intensify`：L1 **100%** / L3 **75%**，L1=2400 金币+强化石 36006 | 未对表 | **CONFIRMED**（配置真值）／UI 未取证 | 项目既有真值 |
| **V7** | 伙伴属性 | catalog **53**、owned **18**（`/DSH_ADMIN/partner_show`） | 未对表 | 计数 **CONFIRMED**／属性值 **UNKNOWN** | 面板曾打开但未截图成功 |
| **V8** | **战力 vs UI** | `power=724112`；`rank_breakdown.total=724112`；`SC_12901 val=724112`；`SC_12971 战力=724112` | 属性面板显示 **724112**（曾截图确认） | **VERIFIED**（四处一致） | ⭐ 分项 9 维服务端**全为占位 0** ⇒ 拆分 UNKNOWN |
| **V9** | 经验表 | 服务端不下发分母 | UI 显示 `13339 / **2600094**` | **CONFIRMED** | L70 经验上限新锚点 |
| **V10** | 成长族每阶属性 | wing `8801/color3/999`；shenqi `10001 lev7 star3`；mingge `21001 lev2`；fabao `bid20001 lev6 stage2`；ride `jie1 lev10`；chair `stage5` | 未对表 | 服务端值 **CONFIRMED**／UI **UNKNOWN** | 逐面板对表是剩余工作 |
| **V11** | 掉落 bid | 首杀 20012→1001、20024→1002（+coin 3000/6000） | — | **CONFIRMED**（配置） | 项目既有真值 |
| **V12** | 商城实付 | 商品数 normal **110**/week **24**/xian **45** | 未取证 | 计数 **CONFIRMED**／实付 **UNKNOWN** | 需开商城面板 |
| **V13** | 货币显示格式 | gold/coin/coupon | `180万 / 990万 / 9999万` | **CONFIRMED**（**截断到万**；`99,999,999→9999万` 为决定性样本） | 经验条不取整 |
| **V14** | 挂机地图表 | `_guaji.json` 8 张（map_bid/mon_bid/等级区间） | 面板两卡：乾坤日月谷 65–74（推荐）/ 魂殿遗迹一层 75–84 | **VERIFIED** | 推荐逻辑与 lv70 自洽 |
| **V15** | 基础属性 10 项 | `power.attrs` | 属性面板逐项 | **VERIFIED**（零偏差） | ⭐ 但客户端面板是纯展示 ⇒ 原版公式仍 INFERENCE |

---

## 三、方法学结论（比单条数据更重要）

| # | 结论 | 等级 |
|---|---|---|
| M-1 | **CS 帧尾部 4 字节 = 发送缓冲残留**（铁证：`10001` 尾部 = 下一帧 `dsh_local` 的开头 `"dsh_"`；`10102` 尾部 `"ount"`）⇒ 解析必须按规格长度截断 | **CONFIRMED** |
| M-2 | `1199` 规格为空 ⇒ 其 4 字节**全为残留**，"心跳带坐标"被否决 | **CONFIRMED** |
| M-3 | SC 证据三档（原始字节 / 服务端注释 / 规格），注释 ≠ 客户端渲染 | 方法学结论 |
| M-4 | **跨表数字对齐必须限定字段语义**：按"数字键"判 bid 覆盖会得到 73/107 的**假象**（config_rune_data 撞 47 个），改用字段值口径得 **29/107** | 方法学结论（自我纠错）|
| M-5 | `9xxxx = 90000 + 基号` 派生规律（客户端同一 `bid_list` 内 **28 组配对**支撑） | STRONG_INFERENCE |
| M-6 | **BACK×2 会退出游戏**；客户端冷启后 ~45 s 自动重连；探针禁止盲发 BACK | **CONFIRMED**（操作教训）|
| M-7 | 日常面板：服务端发 `total_val=10/huoli_list=12`，UI 却显示 `????/????` ⇒ **服务端 SC 值 ≠ 客户端渲染** | **VERIFIED**（不一致）；根因 UNKNOWN |

---

## 四、未完成项与阻塞类型（不是工时不足）

| # | 未完成 | 阻塞类型 | 解除条件 |
|---|---|---|---|
| 1 | V1/V2/V3/V4 怪物数值与伤害公式真值 | **需真服** | 真服恢复 / 真服残留流量；取数字段已定位 |
| 2 | V7/V10 V12 面板 UI 逐项对表 | **需可靠 UI 坐标** | 先视觉定位再单点验证（禁止盲发 BACK）；服务端侧参照值已固化 |
| 3 | M-7 `13781` 渲染异常根因 | **需 SC 原始字节** | 开 SC 落盘（属核心改动，本目标禁止）或 frida 抓 socket |
| 4 | 挂机进图 `10206` 落地 | **需改服务端逻辑** | 超出本目标范围（"不改核心逻辑"），已定位为 Phase 5 第一优先 |
| 5 | SC 侧全量原始字节 | **需 SC 落盘/frida** | 同上 |

---

## 五、文件索引（`analysis/extraction/`）

| 文件 | 内容 |
|---|---|
| `PHASE1_LEDGER.md` | ← 本文件（总台账） |
| `phase1_runtime_restore.md` | 运行态恢复记录（MuMu+adb+mock_server）+ 客户端身份 |
| `phase1_session_frames.md/.json` | 实机会话逐帧 CS/SC（138/122 帧） |
| `phase1_cs_inventory.md` | **316 命令 / 44,911 帧**普查表 |
| `phase1_cs_decode_raw.txt` | 4.8 MB 原始解码（可复现） |
| `phase1_r_series_field_values.md` | R 系列字段实值 + 残留机制 |
| `phase1_r_series_and_afk_chain.md` | 移动/进图/挂机链 + 屏幕→世界映射 |
| `phase1_sc_battle_replay.md` | 战斗族 **SC 原始字节** 解码 |
| `phase1_v_calibration.md` | V-15/V-13/V-9（属性/货币/经验，同屏比对） |
| `phase1_v_series_panels.md` | V-3/V-4/V-5/V-6 + 事故记录 + SC 三档 |
| `phase1_v_server_reference.md` | 服务端侧参照值清单（27 端点） |
| `phase1_server_state_reference.json` | 27 端点原始快照（78 KB） |
| `phase1_bid_coverage.md/.json` | bid 覆盖度（含方法学纠错 + 派生规律） |
| `phase1_state_snapshot.json` | 角色状态快照（status/reward_log/邮件/副本/replay） |
| `phase1_battle_family_raw.txt` | 战斗族帧原始上下文 |

**工具**（`tools/`，全部只读）：`_phase1_decode_cs.py`、`_phase1_cs_inventory.py`、
`_phase1_decode_sc_replay.py`、`_phase1_bid_coverage.py`、`_phase1_server_state_snapshot.py`、
`_phase1_ui_probe.ps1`、`_phase1_ui_scan2.ps1`

---

## 六、第 8 轮补充（收官）

### 6.1 新增可复用方法：**截图字节数当"面板是否打开"的探测器**（M-8）

实测（2560×1440 PNG）：

| 画面 | 截图字节数 |
|---|---|
| 世界视图（史莱克城，持续动画） | **4.10–4.70 MB** |
| 面板打开（内容区大块静态深色） | **1.10–2.15 MB** |

⇒ 判据：**`< 2.6 MB` 视为面板已打开**。配合"点击后单点验证 + 禁止盲发 BACK"，
比依赖视觉模型坐标（±100–200 px 不可靠）可靠得多。本轮即以此在底栏扫描中一次命中。

### 6.2 V-16 个人战斗面板（新对表）

| 项 | 客户端 UI | 服务端 | 判定 |
|---|---|---|---|
| 面板 | tap **(1800,1330)** 打开：标题 `个人战斗`，页签 `最近战斗 / 录像收藏`，列头 `排序/对战双方/战斗类型/日期/操作`，右栏 `个人战斗 / 巅峰对决` | 无对应列表数据源（`battle_replay` 是确定性回放端点，不是"我的战斗记录"） | **内容区为空 = 与服务端一致** ⇒ VERIFIED（"回空=真话"正例）|

> ⚠ **修正**：项目旧校准表 `analysis/calibrated_ui_coords.md` 把 `(1800,1360)` 记为「魂技（技能面板）」，
> 实测为 **个人战斗**面板。旧表该行需更正（技能面板/魂技入口另在其处）。

### 6.3 技能面板的参照值（仍未对表）

服务端：`/DSH_ADMIN/skill_show` → `catalog=105`、`learned=[{skill_bid:10020, lev:2}]`；
`/DSH_ADMIN/build` → `lev=5, learn_list=[30001,30002]`。
客户端技能面板本轮**未成功打开**（底栏其余坐标均为世界/空区），
故 V7/V10/V12 类"UI 对表"仍按 §四 的阻塞类型记为未完成。

### 6.4 收官状态

- 运行态：MuMu 实例 0 + adb `127.0.0.1:16384` + mock_server PID 44008（9000/8080）**保持在线**，
  客户端前台运行、心跳正常，供后续直接取证；
- `server/*.py` **全程零改动**（多轮核验，8 小时窗口内亦无改动）；
- `analysis/extraction/` 交付：**19 个取证文件 + 本台账**，每条结论均带等级与出处。

