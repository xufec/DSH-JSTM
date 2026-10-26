# C3.3 第二分片 · 挂机系统审计（hangup / automate / ghost）

- 日期：2026-10-16（纯只读审计；不实施任何修改）
- 范围：原版挂机入口/面板/协议真值/在线+离线性质/限制与收益/DB 读写/断线语义/面板异常根因
- 证据等级：`V`=真机帧或反汇编直接证据；`C`=配置表/代码注释；`I`=本服务端推断实现（非原版证据）；`U`=UNKNOWN
- 重要前提：`server/afk/service.py`（Phase 10）是本服务端自建的最小闭环实现，**不代表原版**；本审计以客户端反汇编 / fields.json / tcp.log / 原版配置表为准。

---

## §1 入口 / 面板 / 按钮 / 调用路径

| 项 | 结论 | 证据 | 等级 |
|---|---|---|---|
| 挂机图标位置 | 活动顶栏图标，坐标约 (1320,100)；**默认相机位可见可点**；相机平移出屏后消失 | docs/C2.4_导航与交互测试记录.md N7（PASSED，截图 09_hangup_N7）；C2.3 初测记为仅喷泉相机位(scene 3675,1215)可见 | V |
| 图标显示门槛 | config_function id=504「挂机」open_lev=30、is_open=1、location=10（活动顶栏）、sort_id=4；当前角色 lev=70 满足 | server/cfg/config_function.json: id=504 | C |
| 客户端模块 | `assets/src/game/automate/`：automate_ctrl / automate_panel / automate_view / automate_page_view / **automate_offline_view** / automate_data | analysis/_raw/apk_scan_1_4_11.json → ui_by_module.automate | C |
| 面板实测内容 | 打开后显示挂机地点列表：乾坤日月谷(65-74)、魂殿遗迹一层(75-84) 等；数据来自本地 config_guaji，**打开面板本身不发协议**（C2.3/C2.4 会话 tcp 日志无 10930/10932 帧） | C2.4 N7/N30；server/logs/tcp_prevR.log grep 1093x=0 命中 | V+C |
| 面板内按钮 | 双倍点数领取(1900,1230)：N30 实测点击无变化（double=0，与服务端回包一致） | C2.4 N30 | V |
| 挂机怪模块 | `assets/src/game/ghost/`（挂机怪/红尘怪）：GhostCtrl 注册 handle15402/15403/15404 | analysis/_ghost_dis.txt:19,88-99 | C |

## §2 挂机协议是否存在及真实字段

**结论：协议族存在，且是两套，不是一套。**

### A. 面板族（automate panel）= 10930–10935 + 10296/10297（反汇编直证）

| cmd | 方向/字段（fields.json） | 语义（反汇编） | 服务端 handler（当前行号） | 状态 |
|---|---|---|---|---|
| 10296 | CS 空 → SC{code:u8, msg:s, status:u8}（fields.json:1986-2005） | 在线自动挂机开关（setGuaJi/createAutomateBtn/removeAutomateBtn；_automate_dis.txt:557） | mock_server.py:13386 | ✅ 已回 status=1 |
| 10297 | CS → SC{status:u8}（:2013） | 在线挂机状态推送 | mock_server.py:13388 | ✅ |
| 10930 | CS 空 → SC{code:u8,msg:s,double:u16,double_sum:u16}（:10892） | 双倍点数查询 | mock_server.py:15285（R120 回 code=1,0,0） | ✅ |
| 10931 | CS 空 → SC{code,msg}（:10923） | 语义未取证（疑双倍领取） | **未注册** | ❌ GAP |
| 10932 | CS 空 → SC{double:u16,double_sum:u16,double_state:u16,off_state:u16}（:10946） | 离线挂机视图打开查询；客户端按字段写 setCurDoubleNum/setCanDoubleNum/setCurOfflineState/setDoubleState（_automate_dis.txt:423-457） | mock_server.py:10705（R103，off_state 读 guaji_state 表有无行） | ✅ |
| 10933 | CS 空 → SC{code,msg}（:10977） | **开启离线挂机**（proto#19 发 → proto#20 收：code==1 toast「离线挂机开启成功」+ off_state=1） | **未注册** | ❌ GAP |
| 10934 | CS 空 → SC{code,msg}（:11000） | **关闭离线挂机**（proto#21 发 → proto#22 收：toast「离线挂机关闭成功」+ off_state=0） | **未注册** | ❌ GAP |
| 10935 | 仅 SC{double:u16} 推送（:11023，无 CS） | 双倍点数变化推送 | **未注册** | ❌ GAP |

真机帧证据：`server/logs/restart_stdout.log:3857`、`r_20261002_030506.out:24514`、`tcp_prev.log:313` 等多处 `>> cmd=10932` → `<< 10932`。**注意偏差**：fields.json 标 CS_10932 fields=[]，但真机帧 body=4B（如 `08 6c 00 00`）——客户端在空体帧后带了 4 字节（疑似坐标/rid 残留），服务端 handler 忽略 body，不受影响。

### B. 挂机怪族（ghost / 红尘任务怪）= 15400–15405

| cmd | 字段（fields.json） | 服务端 handler（当前行号） | 备注 |
|---|---|---|---|
| 15400 | CS 空 → SC{code,msg}（:50961） | mock_server.py:18990 | 自起点启动挂机怪 |
| 15402 | SC{code,msg,x:u16,y:u16,mon_bid:u32,...}（:50978） | mock_server.py:18932 | 传送挂机图 + 刷怪 |
| 15403 | CS{mon_id:u32}（:50994） | mock_server.py:18952 | 击杀回报 |
| 15404 | SC{mon_id:u32} 推送（:51010） | 无独立 handler（推送） | 挂机怪生成 |
| 15405 | CS 空 → SC{code,msg}（:51042） | mock_server.py:18922 | 位置上报/附近挂机怪查询 |

- SELFCHECK 记载「15400→:18736」为旧行号；**当前核实：15400@18990、15402@18932、15403@18952、15405@18922**（mock_server.py 当前版本）。
- 真机帧（V）：`server/logs/tcp_prev7.log:2214-2235`，19:02:28→19:02:32 客户端连发三帧：
  `3c2d`(15405) body=`00 41 00 3d` → `3c28`(15400) body=`00 44 00 3d` → `3c2d`(15405) body=`00 44 00 3d`。
  **偏差记录**：fields.json 标 CS_15400/15405 fields=[]，但真机 body=4B 且恰为玩家当前坐标（与紧邻 10204 移动帧坐标一致）——规范与抓包不一致，实施时 body 应忽略而非解析。
- 客户端确有接收方：_ghost_dis.txt:88-99 注册 handle15402/15403/15404。

## §3 在线自动战斗 / 离线计时收益 / 两者

**结论：两者都有。**

| 形态 | 证据 | 等级 |
|---|---|---|
| 在线自动战斗 | ① 10296/10297 在线挂机开关（场景内自动巡逻按钮）；② 154xx 链=在线场景内自动战斗：15402 传送挂机图 → 客户端建 ghost_mon → 自动打怪 → 15403 击杀回报。全程在线、客户端驱动 | V+C |
| 离线计时收益 | ① 客户端存在 automate_offline_view.luac；② 10932 返回 off_state；③ 10933/10934 = 离线挂机开启/关闭开关，成功 toast「离线挂机开启成功/关闭成功」（_automate_dis.txt:477,519）；④ dead_protocols_and_traffic.md:149 记 16903 在线福利是双倍点数状态源 | C（反汇编） |

## §4 时间 / 场景 / 等级 / 次数 / 奖励限制

| 限制 | 证据 | 等级 |
|---|---|---|
| 功能开放等级 | config_function id=504 open_lev=30 | C |
| 分场景等级段 | config_guaji.json 每点 lev_l/lev_r（乾坤日月谷 65-74、魂殿遗迹一层 75-84 等 8 点） | C |
| 每日次数 | **无配置证据** | U |
| 挂机时长上限 | config_guaji 无 time 字段；`server/afk/service.py` MAX_MIN=480 是本服务端推断，**非原版** | I（非原版） |
| 离线挂机时长/上限 | 无配置表证据（off_state 仅 0/1 开关） | U |
| 双倍点数上限 | double_sum 字段存在（:10946），规则/产出率无证据 | U |

## §5 挂机收益配置真实来源

- config_guaji.json 字段仅：`mon_bid / map_bid / lev_l / lev_r / disc / show`——**无任何收益字段**。
- 本服务端实现用掉落组 20003 发经验/铜币（server/afk/service.py）= **I 推断，无原版配置支撑**。
- 离线收益/双倍点数的真实产出表：UNKNOWN（16903 在线福利表只覆盖双倍点数来源之一）。

## §6 挂机状态是否需要数据库保存（现有读写点）

| 存储 | 用途 | 证据 |
|---|---|---|
| `guaji_state` 表（rid/loop_count/mission_bid/kill_count） | 在线挂机怪循环计数；15400/15403 读写（mock_server.py:9355-9450）；10932 用「有无行」判 off_state（:10715） | C |
| `dungeon_progress` KV ptype='afk'（start/minutes/last_collect） | 本服务端自建离线计时（server/afk/service.py）——**原版离线状态如何持久化无证据** | I |

## §7 客户端退出/断线时原版机制

- 机制存在性：离线挂机（off_state）本身就是为断线/退出后累积收益设计——**确认有**。
- 累积窗口、上限、上线后领取入口（是否 10931=领取）：**无真机帧/配置证据 = BLOCKED**。
- 本服务端：退出不主动清理 guaji_state；afk 模块按 start 时间戳到下次登录结算（I）。

## §8 挂机面板异常根因归类

| 现象 | C2.3 初测 | C2.4 复测 | 根因判定 |
|---|---|---|---|
| 挂机图标随相机平移消失 | 仅喷泉相机位可见；点测无面板无 CS | **默认位(1320,100)可点开面板**；平移出屏后消失 | **UI 渲染层问题（世界锚定节点），非协议/非服务端** |

- 证据：docs/C2.3_未完成项与阻塞问题.md §2-e（图标锚在场景坐标 3675,1215，非固定 HUD 层）；docs/C2.4_导航与交互测试记录.md §4（已修正 C2.3 误判为「不可开」）。
- 归类：UI 导航/节点生命周期——图标挂在场景世界层，相机移出视野即不可见。**服务端数据与协议不是根因**（默认位下面板正常打开、N7 PASSED）。

---

## 挂机审计结论 + 最小闭环建议

1. **入口**：无需修。默认相机位已可开（C2.4 N7 PASSED）；测试纪律=保持默认相机位。
2. **协议接线缺口（有证据）**：
   - 10933 未接 → 离线挂机「开启」按钮点了无 toast；建议回 `{code=1,msg=''}` 并在 guaji_state 建行（与 10932 的 off_state 读法自洽）。
   - 10934 未接 → 建议回 `{code=1,msg=''}` 并删行。
   - 10935 推送暂不需要（无双倍系统）。
3. **BLOCKED（无证据不动）**：
   - 10931 语义（疑双倍领取/离线收益领取）——需先反汇编 automate_data/panel 确认哪个按钮发它，再接线。
   - 挂机收益数值来源——config_guaji 无收益字段，20003 掉落组是本端推断；原版收益表未定位前不扩写。
   - 离线挂机时长上限/领取规则——无配置证据。
4. **文档勘误**：本仓既有 C1/C2 文档把 154xx 整体称作「挂机协议」，审计确认 154xx=挂机怪(ghost)族、1093x=挂机面板族，两者不可混接。
