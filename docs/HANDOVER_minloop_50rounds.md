# 最小回环（minloop）· 20 轮攻坚交接文档

> 汇编自 `report/report_2026*minloop*` 全部 28 份报告 + `server/minloop/README.md`。
> 纪律：只写报告里有证据的结论；报告之间不一致或未解释的，一律标 **UNKNOWN**。
> 目标 APK：`anzbao/jstm.apk`（`com.shiyue.dldl.ewan.qihoo`，versionName 1.4.9）；环境：MuMu + adb(root) + frida 17.18 + tcpdump。

---

## 一、这是什么

`server/minloop/` 是"**登录 → 角色 → 进场景 → 接任务 → 打怪 → 结算 → 掉落进包 → 提交 → 奖励 → 背包**"
这条最小玩法回环的**独立最小实现**（3 个代码文件），用来回答：① 回环最少需要哪些命令/字段；② 每个字段能否取到原版真值。
它**不是** `server/mock_server.py`（16k 行全量服）的替代品，而是**度量尺与回归基座**（`server/minloop/README.md:1-8`）。

| 文件 | 作用 | 实测总行 | 实测非空行 | README 宣称 |
|---|---|---|---|---|
| `server/minloop/min_loop_server.py` | 协议规格编码器 + SQLite + TCP 游戏服 + HTTP 网关 | 1022 | 898 | ~800（`README.md:16`） |
| `server/minloop/selftest.py` | 离线回环自检（合成客户端 + 逐帧严格规格解析） | 328 | 287 | ~300 |
| `server/minloop/replay_real_frames.py` | 真机帧回放（无状态：只校验应答规格/`code`） | 159 | 138 | ~160 |
| `server/minloop/replay_stateful.py` | ★ 真机帧回放（**状态化**：额外跟踪 DB 副作用） | 142 | 125 | —（新增，README 未列） |

> **口径已澄清（本节原标 UNKNOWN，2026-10-01 goal round 22 复核后修正）**：
> 两个数字**不是矛盾，而是两种计数法** ——
> `总行` = Python `sum(1 for _ in open(...))`（含空行）；`非空行` = PowerShell `Measure-Object -Line`（只数非空行）。
> 二者实测差恒为空行数（如 `min_loop_server.py`：1022 − 898 = 124）。
> README 的 `~800` 与报告里的"约 1180 行"均为**早期口径**（文件在这 20 轮里被多次修改），以本表为准。

运行 / 自检（照 README）：

```bash
python server/minloop/min_loop_server.py                 # 默认 8099/9099（避开参考服 8080/9000）
python server/minloop/min_loop_server.py --http 8080 --game 9000
python server/minloop/selftest.py                        # 离线自检，不需要模拟器
python server/minloop/replay_real_frames.py [日志文件...]  # 真机帧回归
```

回环内 11 条命令（`README.md:29-43`）：`10001 / 1199 / 1110 / 10102 / 10300 / 10204 / 12400 / 12402 / 12403 / 20002 / 10502`。
回环外命令按 `protocol/fields.json` 的权威 SC 通用编码（结构对、内容零值）；**没有 SC 定义的一律不回包**。
数据来源标注纪律（`README.md:50-60`）：协议字段/任务 846/物品 3535 = [APK] 原版；怪物 HP/攻防/掉落/伤害系数 = `[TEST_ONLY]` 占位（APK 无此数据）。

---

## 二、已完成（附证据路径）

| 项 | 状态 | 证据 |
|---|---|---|
| 离线自检 **45 → 49/49 PASS** | ✅ | `selftest.py`（45/45 见 `report_20261001_minloop_round13_goal7_BREAKTHROUGH.md:42`；49/49 见 `report_20261001_minloop_goal50_round01.md:52`） |
| 真机帧回放 **292 帧 / 0 规格不符 / 0 危险应答** | ✅ | `replay_real_frames.py`；`report_20261001_minloop_round3.md:27`、`..._round27_goal20_FINAL.md:54` |
| 真机 TCP 连上自建服 + 登录（`10001` / `1110`）+ 心跳 `1199` **×364** | ✅ | `logs/minloop/live11_stdout.log`（recv 尺寸 `{10:364, 23:29, 225:5}`）；`..._round25_goal18.md:13-17`、`..._round27_goal20_FINAL.md:37` |
| 45 种客户端命令被真机驱动过、服务端逐条应答 | ✅ | `logs/minloop/live8_stdout.log`（38 种）、`live9_stdout.log`（**45 种**）；`..._round13_goal7_BREAKTHROUGH.md:17,54` |
| 修复：`net_manager:Stop` 死等 → 跳过后 `initInstance` 可返回 | ✅ | `report_20261001_minloop_round6_BREAKTHROUGH.md:27-28`；设备内 `files/dsh_v25/v26/v27.txt` |
| 修复：**必须补 `GameNet:restartNetManager()`** | ✅ | `report_20261001_minloop_round8_goal2_REPRODUCED.md:40-43`（反汇编 `gamenet.luac` proto#29） |
| 修复：**`10200` 的 `code` 必须为 0**（"code==1 才成功"通则的例外） | ✅ | `report_20261001_minloop_round13_goal7_BREAKTHROUGH.md:21-42`；`selftest.py:207-211` 回归断言 |
| 修复：`local_srv_id` 是字符串却被当表用 ⇒ 列表消费抛异常 | ✅ | `report_20261001_minloop_round10_goal4.md:110-132`；设备内 `files/dsh_v40.txt` |
| 修复：服务器列表**被消费**（`v39_consume_ret ok=false → ok=true`） | ✅ | 同上 |
| 修复：`bag_code` 语义（主背包 = 1，此前编造值 7；2/3=装备栏、4=仓库诚实回空） | ✅ | `report_20261001_minloop_goal50_round01.md:37-68`；依据 `analysis/1.4.9/bag_code_mapping.md` |
| 修复：`12403` 提交幂等（客户端交的是 bid **10020**） | ✅ | `report_20261001_minloop_round17_goal11.md:46-54` |
| 工具 `tools/ml_dump_proto.py`（按 proto 序号反汇编） | ✅ | `report_20261001_minloop_round9_goal3.md:24`；文件存在 |
| 工具 `tools/minloop_frida_*.py`（自证版原生钩子） | ✅ | `tools/minloop_frida_send.py`、`_probe2.py`、`_sock9000.py`、`_sock9000_v2.py` |
| UI 文本 dump（场景树 + adb 点击坐标，免截图） | ✅ | `server/_minloop_block.lua`；证据 `files/dsh_ui3/4/5.txt`；`report_20261001_minloop_round3.md:23-26` |
| `lua-check` 接入打包链（`build_fakelogin.ps1` `[0/4]` 门禁，不过即 throw） | ✅ | `tools/build_fakelogin.ps1:27-33`（实测已存在）；`report_20261001_minloop_round6_BREAKTHROUGH.md:112` |

---

## 三、四次突破

| # | 突破 | 内容 | 证据 |
|---|---|---|---|
| 1 | **`Stop` 死锁 → `restartNetManager`** | `initInstance()` 里 `net_manager:Stop()` 只进不出（150 进 / 149 出），钉死 Lua 线程 ⇒ 版本检查/SDK 登录/列表/TCP/发帧全不发生。跳过它后 `initInstance` 返回；随后发现必须补 `GameNet:restartNetManager()`（反汇编 proto#29）才能真正拉起网络对象 | `report_20261001_minloop_round6_BREAKTHROUGH.md:27-28`（根因）、`report_20261001_minloop_round8_goal2_REPRODUCED.md:37-59`（可复现配方） |
| 2 | **第一次真机帧交换** | 真机 APK → 最小回环服跑出真实登录交换：`10001 → 1110（服务端回真实角色列表）→ 10302/10303/13340/14901/15203/10999/12403`；抓包 `:9000` **21 个数据包**（历轮恒为 0） | `logs/minloop/round6_exchange.txt`；`report_20261001_minloop_round6_BREAKTHROUGH.md:31-49` |
| 3 | **服务器列表消费修复** | 列表消费函数被调用、入参正确，但内部在 `denglu_mgr.luac` proto#8 指令 204/205 处 `platform .. '_' .. zone_id` 抛异常 ⇒ 整段中止。真因：`local_srv_id` 存档是**字符串 `"1"`**、代码按**表**读 ⇒ 修好后 `ok=true` | `report_20261001_minloop_round10_goal4.md:110-132`；设备内 `files/dsh_v40.txt`；`logs/minloop/live8_stdout.log` |
| 4 | **`10200` `code=0` 打开进场景** | 通则"code==1 才成功"有一例外：`scene_controller.luac proto[16]` 是 `if resp.code ~= 0 then message2(resp.msg)`。改 0 后客户端从 `scene_nil / no_scene_view_instance` 变成 `scene_table / role_table / isLoadState_true / recv_119`，命令种类 38 → **45**（出现 `15203`、`12403`）；并加回归断言 | `report_20261001_minloop_round13_goal7_BREAKTHROUGH.md:21-58`；`logs/minloop/live9_stdout.log`（改前对照 `live8_stdout.log`） |

---

## 四、自我更正清单

| # | 曾经的说法 | 实测结论 | 证据文件 |
|---|---|---|---|
| 1 | "画面 40 分钟逐像素不变 ⇒ 主循环冻结、tick 停摆" | ❌ 不成立：加载正常推进，`tick` 一直在报（540 条） | `report_20260930_minloop_round2.md:53` |
| 2 | "`GameNet:Update()` 抛异常 ⇒ 网络泵坏" | ❌ 改判：**这个 build 里没有 `GameNet:Update`**（`Update=nil`）；真正的泵是 `net_manager:Update()` + `doOneMsg()`，都正常 | `report_20260930_minloop_round2.md:55`；`files/dsh_ml7.txt` |
| 3 | "客户端启动流程走不完（模块没加载）" | ❌ 不成立：`GameModule` 304 → 0，2 秒内加载完 | `report_20260930_minloop_round2.md:54`；`files/dsh_gm.txt` |
| 4 | "客户端不发帧 ⇒ 它根本没尝试建连" | ❌ 否证：客户端自己调过 `SetLoginServerInfo(10.0.2.2,9000)` + `AsyncConnectLoginServer(10)` | `report_20261001_minloop_round7_goal1.md:55`；`files/dsh_v33.txt` |
| 5 | "`DeleteMe` 把 net 对象销毁是罪魁" | ❌ 否证：只跳 `Stop`、保留 `DeleteMe`（v31）依然 `conn=false`、0 连接 0 帧 | `report_20261001_minloop_round7_goal1.md:56` |
| 6 | "客户端没带端口（`SetLoginServerInfo(10.0.2.2,nil)`）" | ❌ 是我自己的**日志 bug**：包装写成 `local a1, a2 = ..., nil` 丢了第二个 vararg；实测 `nargs=2 a2=9000` | `report_20261001_minloop_round7_goal1.md:84-100` |
| 7 | "修网关后仍每 6 秒重请求 ⇒ 列表未被消费（重试爆发）" | ⚠️ 误读：修前是 6 秒爆发，修后是 60 秒 / 26–36 秒周期，特征不同 | `report_20261001_minloop_round3.md:58-63` |
| 8 | "frida hook `send/write` 报 0 次写 ⇒ 客户端没往游戏服写过" | ❌ 钩子是**瞎的**（ARM 翻译层）：同期客户端写了 1575 条 HTTP ⇒ 该结论不得采信 | `report_20260930_minloop_round2.md:101`；`report_20261001_minloop_round5.md:37` |
| 9 | "`elementList` 空 / `scene_info.roles=nil` ⇒ 我的 `10201` 没被吸收" | ❌ 判据作废：历史**可用会话**里 `el=elementList_ttable_n0_npc0` 出现 130 次、`roles_nil` 出现 60227 次，都是正常现象 | `report_20261001_minloop_round12_goal6.md:18-29` |
| 10 | "`v43_socket=FOUND UserMsgAdapter` 是启发式误报"（第 21 轮自评） | ❌ 该自评本身被更正：第 23 轮反汇编确认 **`UserMsgAdapter` 确实就是发送器** | `report_20261001_minloop_round21_goal15.md:9` → `report_20261001_minloop_round23_goal17.md:31,72` |
| 11 | "`Send` 的 `nargs=0` ⇒ `game_net_id` 为 nil" | ❌ 是我包装的**观测口径问题**：调用方用点号调用 `UserMsgAdapter.Send(game_net_id)`，第一个参数即 net id；实测 `game_net_id=1` 有效 | `report_20261001_minloop_round25_goal18.md:48-54` |
| 12 | "`10102/10103` 被 `msg_list` 消息队列扣住" | ❌ 否证：`msg_list` 全程 `n=0` | `report_20261001_minloop_round10_goal4.md:25,28` |
| 13 | "`lua-check` 是硬闸门"（HANDOVER 口径） | ❌ 实际**没接在打包链上**：check.js 报 FAIL，`build_fakelogin.ps1` 照样打包装机（跑了坏 Lua） | `report_20261001_minloop_round6_BREAKTHROUGH.md:112`；`tools/build_fakelogin.ps1:27-33` |
| 14 | "`zone_id` nil 来自我的网关应答字段缺失" | ❌ 否证：补到条目/data/顶层三层后错误一模一样；真因是 `local_srv_id` 字符串被当表用 | `report_20261001_minloop_round10_goal4.md:104-108` |
| 15 | "`if conn then 重试` 救连条件" | ❌ 条件**写反**（该救的是 `conn=false`）；且改成"每次都重连"更糟（顶掉客户端自己的 OnConnect ⇒ 0 帧）。最终定下"**只救一次、连上别碰**" | `report_20261001_minloop_round17_goal11.md:23-42` |
| 16 | "探针块没在跑"（adb 读不到 `files/`） | ❌ 自误判：是**权限问题**，`adb root` 后 `dsh_v39/v40/v41` 俱全 | `report_20261001_minloop_round15_goal9.md:25-26` |

（第 22 轮还记录了自己两处"包装守卫先置位后重置"导致归属实验无数据的探针 bug，见 `report_20261001_minloop_round22_goal16.md:14-16`。）

---

## 五、未完成 / 卡点

**卡点（原文实质）**：客户端**从不发送 `10102/10103`**。

- Lua 侧**全部成功**：`WriteHeader=true`、`Encode=true`、`Send` 被调用、`SendProtocal=true`、`game_net_id=1`（`report_20261001_minloop_round24_goal17b.md:11-19`、`..._round25_goal18.md:26-30`）。
- 服务端侧 `recv` 尺寸**只有 `{10, 23, 225}`**（对应 `1199` / `10001` / `1110`），`未解帧 = 0`（`..._round25_goal18.md:13-17`、`..._round27_goal20_FINAL.md:37`）。
- 链路层 160 秒全量抓包：游戏服对端**只有 `10.0.2.2:9000`**（窗口内仅 1 次 SYN），`10102/10103` **没有发往任何地方**；其余外部流量全是第三方 SDK（Getui/360/Bugly）（`..._round26_goal19.md:11-19`）。
- **丢弃点闭口在客户端 `UserMsgAdapter:Send`**（原生实现；该适配器**无可枚举 Lua 字段**）（`..._round25_goal18.md:27,66`）。
- frida 原生钩子**两次被自证为盲**（BLIND）：第 5 轮报 0 次写而同期 1575 条 HTTP；第 20 轮 1330 个钩子报"全部写=0（fd 数=0）"，同期服务端 +7 条上报 ⇒ 工具自己判读 `INCONCLUSIVE（钩子瞎）`（`..._round27_goal20_FINAL.md:23-28`）。

**次级未知（UNKNOWN）**：

| # | 项 | 状态 | 出处 |
|---|---|---|---|
| 1 | `mapResCache = 0`（历史可用会话是 192） | ⚠️ UNKNOWN，是否有害未定；但 `isLoadState_true` 已成立 | `..._round13_goal7_BREAKTHROUGH.md:75`、`..._round27_goal20_FINAL.md:70` |
| 2 | **两实例差异**：16384 实例曾进场景 / 7555 实例始终 `scene_nil` | UNKNOWN，本轮未做对比 | `..._round16_goal10.md:95-97`、`..._round27_goal20_FINAL.md:81` |
| 3 | 多实例 adb 端口位移 **16384 → 7555**（16384 拒连），且 `files/` 需重新 `adb root` | 已定位，非根因 | `..._round15_goal9.md:9-11` |
| 4 | `dump_proto.py` / `ml_dump_proto.py` 的 `GGET` 全局名解析缺口 | 后续由 `tools/luajit_dis.py::kidx` 补上 | `..._round19_goal13.md:35` → `..._round23_goal17.md:104` |
| 5 | "帧回放 8831 帧"（第 1 轮）vs "292 帧"（第 3 轮起） | ✅ **已澄清（2026-10-01 goal round 22）：不是矛盾，是"回放了几个日志"的差别** | 同一脚本、不同日志集合（见下） |
| 6 | ★ **新增（round 22）**：状态化回放的真机 DB 效果 | ✅ 已取到：`task_chain_tcp.log` ⇒ `exp +500 / coin +1290`（= APK `award_assets`）；`battle_chain_tcp.log` ⇒ `missions_rows 0→4、bag_rows 0→1、bag_qty 0→2` | `report/report_20261001_minloop_goal50_round03_replay.md` |

> **§5 澄清（原标 UNKNOWN，已复核）**：两者是**同一脚本 `replay_real_frames.py` 传入不同日志集合**的结果——
> · 单日志：`python server/minloop/replay_real_frames.py logs/1.4.9/battle_chain_tcp.log` ⇒ **合计真实帧 292**；
> · 三日志：`... battle_chain_tcp.log logs/1.4.9/task_chain_tcp.log server/logs/tcp_prevR.log` ⇒ **合计真实帧 8831**（`tcp_prevR.log` 本身有数千帧）。
> ⇒ **口径 = "回放的日志集合大小"，两次都正确**；本会话两次数值均有原样输出可查。

---

## 六、怎么继续

1. **要外部手段（第一优先）**：本环境 frida 对该 APP 的原生写是盲的（两轮复现）。需要**换一种能拦住其写的观测方式**：
   换 frida 版本/`--enable-` 选项、在 `libcocos2dlua.so` / supersdk 的原生符号上直接挂钩、或 LD_PRELOAD 式注入。
   **纪律不变**：任何"0 事件/0 字节"结论必须**同窗口 hook 一个必然发生的写自证**（模板已在库）（`..._round27_goal20_FINAL.md:77-80`）。
2. **或换一个客户端实例/版本**：先做 16384 vs 7555 的**两实例差异对比**（存档 `local_srv_id` / `last_login_accounts`、资源完整性、CDN 资源是否齐全）（`..._round16_goal10.md:95-97`、`..._round27_goal20_FINAL.md:81`）。
3. **或拿到 .so 名称**：`UserMsgAdapter:Send` 的原生实现所在库名当前 **UNKNOWN**（报告只给出"需在 `libcocos2dlua.so`/supersdk 原生符号上挂钩"这一方向，未确证发送器落在哪个 `.so`）⇒ 需要外部指认该库名后才能定点观测。
4. **服务端侧可直接交付**：`server/minloop/` 可用于最小回环验证与回归（49/49 自检 + 292 真机帧回放）；
   新增专用 handler 时**同时跑 `audit_dedicated.py` 与 `selftest.py`**（`..._round27_goal20_FINAL.md:83-85`）。
5. **不依赖客户端的可选推进**：继续做**协议级真机帧回放**的端到端校验（把 `replay_real_frames.py` 升级为"按连接顺序回放 + 断言 DB 副作用：接取/提交/奖励/掉落"）（`report_20261001_minloop_goal50_round01.md:94-95`）。
6. **继续文档对照修错**（便宜有效）：核对 `analysis/jstm_1.4.9/task_protocol.md`、`battle_protocol.md`、`scene_protocol.md` 与本服字段/`code` 约定（`report_20261001_minloop_goal50_round01.md:91-94`）。

---

## 七、证据索引

**服务端代码**

- `server/minloop/min_loop_server.py`、`server/minloop/selftest.py`、`server/minloop/replay_real_frames.py`、`server/minloop/README.md`
- 探针：`server/_minloop_block.lua`、`server/_ml41_add.lua`、`_ml42_add.lua`、`_ml43_add.lua`、`_ml44_add.lua`、`_ml45_add.lua`、`_ml46_add.lua`、`_ml47_add.lua`、`server/dsh_minloop_probe.lua`

**报告**

- `report/report_20260930_minloop.md`、`report/report_20260930_minloop_round2.md`
- `report/report_20261001_minloop_round3.md` … `report/report_20261001_minloop_round27_goal20_FINAL.md`（共 25 份）
- `report/report_20261001_minloop_goal50_round01.md`

**设备侧文件（需 `adb root`，7555 实例）**

- `files/dsh_v25.txt` / `v26` / `v27`（Stop 死锁根因链）、`dsh_v31…v47.txt`（逐轮实验）
- `files/dsh_ui3.txt` / `dsh_ui4.txt` / `dsh_ui5.txt`（UI 树 + adb 坐标）、`dsh_pct.txt`、`dsh_gm.txt`、`dsh_ml*.txt`、`dsh_e*.txt`、`dsh_srv.txt`、`dsh_enter.txt`、`dsh_login.txt`

**服务端日志**

- `logs/minloop/live_stdout.log`、`live2…live11_stdout.log`（`live11` 含 recv 尺寸分布这一关键证据）
- `logs/minloop/round6_exchange.txt`（第一次真机帧交换）、`logs/minloop/my_10201.bin`（623 字节 10201 原始字节）
- 画面：`logs/minloop/ref_01_after_launch.png` vs `logs/minloop/live_real_apk_screen.png`

**抓包（链路层）**

- 设备内 `/data/local/tmp/all.txt`、`/data/local/tmp/all2.txt`（21110 行）、`/data/local/tmp/s*.txt`、`/data/local/tmp/p1.txt`

**静态字节码**

- `analysis/base_controller.luac`（`SendProtocal` proto#3）、`analysis/gamenet.luac`（`restartNetManager` proto#29）、
  `analysis/denglu_ctrl.luac`（`request10102Login` proto#32）、`analysis/denglu_mgr.luac`（`managerServerListByJsonObj` proto#8）、
  `analysis/scene_controller.luac`（proto[16] 的 code 例外）

**工具**

- `tools/ml_dump_proto.py`（按 proto 序号反汇编）、`tools/dump_proto.py`、`tools/luac_defs.py`、`tools/luajit_dis.py`
- `tools/minloop_frida_send.py`、`tools/minloop_frida_probe2.py`、`tools/minloop_frida_sock9000.py`、`tools/minloop_frida_sock9000_v2.py`
- `tools/build_fakelogin.ps1`（含 `[0/4]` lua-check 门禁）、`tools/lua-check/`

**其他依据**

- `analysis/1.4.9/bag_code_mapping.md`（`bag_code` 权威语义）、`analysis/1.4.9/round67_68_scene_10201_fix.md`（参考服 `10200→10201→15402` 推送组合）、`server/mock_server.py`（已知可用实现，作标尺）

---

# 附录 A · 本目标「50 轮」增量（goal round 21–50，共 30 轮）

> 本节由自动轮次逐轮累积；每一条都有可复查证据（报告文件名 = `report/report_20261001_minloop_goal50_round*.md`）。
> 纪律沿用：**能查证才写"已验证"；查不到写 UNKNOWN；被否证的旧结论保留在案**。

## A.1 服务端侧**修掉的真实缺陷**（每条都有断言守着）

| # | 缺陷 | 证据/依据 | 修复 |
|---|---|---|---|
| 1 | `bag_code` 语义用错（默认编造值 7，且**任何分囊都回主背包**）⇒ 装备栏看到普通物品 | `analysis/1.4.9/bag_code_mapping.md`（客户端 `BackpackConst.Bag_Code` 取证：1=主背包/2·3=装备/4=仓库） | 按分囊分支；未实现内容**诚实回空** |
| 2 | **任务条件解析错**：配置里 `progress` 是**列表行**（`["fight_mon",20001,1]`），旧码只认 dict ⇒ **要打怪的任务被当成无条件** | `server/mission_config.json`（10020 实例） | 支持列表行；**行为级断言**："未击杀前提交必须被拒" |
| 3 | **击杀奖励是编造数据**（`[TEST_ONLY]` +30 coin/+50 exp + 每次掉占位物） | `analysis/1.4.9/item/_config_drop.json`（怪 20001 真实记录：`coin={1000}`、三掉落节**全空**） | 改为配置驱动（coin+1000）、**无掉落节 ⇒ 不发物品** |
| 4 | `10505` 会给**不在物品表**的 bid 建背包行（编造物品） | `partner_jubaopen_item_effects.md:93-99`（参考服 `is_valid_item` 过滤） | 加 `item_ok()` 过滤；跳过项如实记日志 |
| 5 | `on_12402` 推 `12405` 用错字段名（`mission_list` ⇒ 实际是空表） | `protocol/fields.json`：`SC_12405.update_mission_list` | 改字段名 |
| 6 | `on_12403` 提交成功后**漏推 `12405`+`12406`**（候选后果：已提交任务不消失） | 参考服抓包 `logs/1.4.9/task_chain_tcp.log:136-137`、`battle_chain_tcp.log:633/663/709/866` | 补推；并补参考服的**提交后刷新** `10301/10303` |
| 7 | ★★ **`10303` 帧长暴增 11 倍**（2233 字节）：`attr` 是**结构体表**（~176 B/项），我传**字典** ⇒ 被逐键展开成多行 | 参考服真机帧 **192 字节**（`battle_chain_tcp.log:63`，`attr (hp_max=… atk_s=…)` 单块） | 改传**单结构体列表** ⇒ **197 字节**（差 5 = 名字长度） |
| 8 | 自己新代码 bug：`import re` 缺失 ⇒ `kill_reward` 首行抛错被 per-message `except` 吞掉 | 自检首跑 `coin 0→0` | 补 import |
| 9 | 自己新代码 bug：`sqlite3.Row` 无 `.get()`（`bag_has`）⇒ `12415` 完全无应答 | 自检输出 `!! 回环处理 12415 异常` | 用 `r['n']` |
| 10 | 打包链**未接 lua-check**（坏 Lua 曾被照常打包） | — | `build_fakelogin.ps1` 加 `[0/4]` 门禁 |

## A.2 新增能力（协议/覆盖/工具）

| 项 | 说明 | 依据/验证 |
|---|---|---|
| `10505` 开礼包 | 用**真实礼包表** `item_gift.json`（496 礼包 / 5353 条，95.9% 命中真物品表）发内容 + 推 `10500`/`10302` | 断言"推送 == 礼包真实内容" |
| `12404` 放弃任务 | 删行 + `code=1` + 推 `12406`（参考服当时是 **no-op**） | 四步断言；**真机 UNVERIFIED**（超参考服范围） |
| `12414` NPC 交任务 | 达条件 ⇒ 完成 + 发奖（**奖励 coin+1290 = APK 配置**）；否则诚实拒绝 | 断言含"奖励=APK 配置" |
| `12415` 交物品 | 新增 `bag_has/bag_del`；**库存不足 ⇒ 诚实拒绝**；用**真物品**测 | 断言含"背包真实扣减" |
| `10204` 移动覆盖 | 参考服最高频命令（472 次）此前**完全没测** | 断言：回显 + 落库 + 严格规格 |
| 高频命令批量覆盖 | 14 条按参考服频度排序的命令一次纳入回归 | +28 断言 |
| `tools/cmp_sc_lengths.py` | **SC 帧长奇偶校验器**（参考服 vs 本服，带 ±32B 邻近容差） | 一次性把"候选"从 7 降到 2，且剩余的经算术核查为**内容差异** |

## A.3 证据等级与纪律（成文条文，已进 README）

- **数据来源证据等级表**（README §5.3）：`fields.json`（帧回放 0 规格不符）、`mission_config.json`（客户端 `scanMis 846` 对上）、`item_config.json`（界面读数交叉验证）＝**已实测**；`_config_drop.json`＝**`[APK_CONFIG/未实机验证]`**（`drop_model.md:291` 客户端从不读取）。
- **「确有真值、但按纪律故意不填」清单**（README §5.4）：`10922`（有 43 条真活动，但 `status` 语义 UNKNOWN）、`11200`（协议含 **6 个未解子表**）、`11215`（与未结客户端问题纠缠）。
- **两条通用判据**：① "配置里读到但客户端不读"的值只能标 `[APK_CONFIG]`；② "**有数据 ≠ 可以发**"——SC 里有语义未确证的判别字段就宁可回"空但合法"。

## A.4 硬卡点（与主文档 §五一致，无变化）

客户端**从不发送 `10102/10103`**：Lua 侧全成功（`WriteHeader=true`/`Encode=true`/`Send` 被调用/`game_net_id=1`），
服务端 `recv` 尺寸只有 `{10,23,225}`，链路层抓包确认**未发往任何目的地** ⇒ 丢失点闭口在客户端 Lua→原生 `UserMsgAdapter:Send`；
**frida 原生钩子两次被自证为盲** ⇒ 本环境无可用原生观测手段 ⇒ 该路需外部条件（另一观测手段 / 换实例 / 该 so 名）。

## A.5 当前基线（可复跑）

| 项 | 结果 |
|---|---|
| `python server/minloop/selftest.py` | **132/132 PASS** |
| `python tools/cmp_sc_lengths.py --mine logs/minloop/live12_stdout.log` | 有交集 11 ｜ 邻近容差 5 ｜ 候选 2（均为内容差异）｜ 仅参考服有 33 |
| `python server/minloop/replay_stateful.py` | 302 帧级回放，严格不符 0、危险应答 0；DB 副作用与真机 `award_assets` **4/4 一致** |
