# Phase 5F —— 接取任务（✅ 完成，且顺带解决了 Phase 4 遗留的 `nil`）

> **结论：服务端推送 `SC_12400` 带 `mission_bid=10010` 后，
> 客户端**自动接取**（`auto_accept=1`），任务追踪栏正常显示两行真实文案，**无 `nil`**。**

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① 新增 **`12402`** 分支：`CS{mission_bid:u32}` → `SC{code:u8, msg:string, missions:table(13字段)}`（接取）<br>② 新增 **`12403`** 分支：`CS{mission_bid:u32}` → `SC{mission_bid:u32, code:u8, msg:string}`（提交，先保证有应答；5H 细化） |
| **`server/config.json`** | `missions` 换成第一条测试任务：`mission_bid=10010, mission_status=1, loop_num=1, process_status=0, …` |

**协议依据（全部来自 1.4.9）**：
- `mission_ctrl.luac` 的 `RegisterProtocal(12402/12403, …)`
- 字段取自 `protocol/manual.md`（`tools/show_cmd.py 12402` / `12403` 可复核）

---

## 2. 协议证据

```
CS_12402 : mission_bid:uint32
SC_12402 : code:uint8, msg:string, missions:table(13 字段)

CS_12403 : mission_bid:uint32
SC_12403 : mission_bid:uint32, code:uint8, msg:string
```

**本轮实测**：客户端**没有发 `12402`**（日志里无 `cmd=12402`）——
**与 5E 读出的 `auto_accept=1` / `accept_npc_id=0` 完全吻合**：
这条任务是**自动接取**，只需服务端把它放进 `12400` 列表。

---

## 3. 测试结果（**关键**）

### 3.1 服务端推送

```
[09:48:26]  << 12400 SC_12400 mission_list=1 (42 bytes)
```

### 3.2 客户端接收与关联本地配置（探针上报）

```
t=misVO&v=…_mis_bid_10010_mis_code_0_loop_num_1_commit_num_0_accept_time_0_…
          _mis_config_table_…
t=misCfg&v=n_36_nameLen_12_descLen_24_bid_10010_type_1_keys=abandon_flag,
          accept_npc_id,accept_talk,auto_accept,auto_commit,award_assets,bid,…
t=misContent&v=mis_contentLen_30_mis_bid_10010_mis_code_0_mis_type_1
```

| 读数 | 含义 |
|---|---|
| `mis_bid_10010` | 客户端按服务端给的 bid 建了任务 VO |
| `misCfg n_36 / nameLen_12 / descLen_24 / type_1` | **成功关联到本地 `Config.Mission[10010]`**（36 字段；名字 12 字节 = 「斗罗魂师」；描述 24 字节 = 「去周漪老师处报到」；type=1 主线） |
| **`misContent mis_contentLen_30`** | **★★ `mis_content` 有值了（30 字节）** |

### 3.3 ★★ 界面确认（视觉逐字判读）

```
任务追踪栏：
  第一行：主线-斗罗魂师
  第二行：去史莱克城找周漪        ← ★ 不再是 "nil"
无 nil、无乱码、无报错
```

**⇒ Phase 4 长期未解决的"追踪栏第二行 `nil`"问题，在本次一并解决。**

（原因回顾：`MissionUtil.missionContent` 的第 4 段需要 `progress[status]` 等条件；
`10010` 与 `10070` 在这套数据下终于走通，`mis_content` 被正常填充。）

---

## 4. 日志位置

```
logs/1.4.9/task_5f_tcp.log      12400 推送（42 字节）
logs/1.4.9/task_5f_probe.log    探针上报（misVO / misCfg / misContent）
shots/p5f_accept.png            任务栏显示「主线-斗罗魂师 / 去史莱克城找周漪」
```

---

## 5. 仍然缺失的问题

1. **`12402` 未被触发** —— 因为 `auto_accept=1`。若要验证"手动接取"，
   需换一条 `auto_accept=0` 且 `accept_npc_id≠0` 的任务（**当前不需要**）。
2. **完成条件仍未确认** —— `Config.Mission[10010].progress` 在运行期为空，
   它到底是"到周漪处直接提交"还是需要别的进度，**要在 5G/5H 用单变量确认**。
3. **NPC 头顶标记是否变化** —— 5F 未检查（可用 5B 的截图对照）。
4. `award_assets` 的二元组含义（`{1=2,2=1290}` 等）**仍待验证**（5I 领奖时需要）。
5. **任务状态未落库** —— 任务数据现在仍来自 `config.json` 静态配置，
   真正的"任务持久化"是 **5J**。

---

## 6. Phase 5F 结论

| 项 | 结果 |
|---|---|
| 服务端推送任务（`12400`） | ✅ 已验证（42 字节，含 `10010`） |
| 客户端建任务 VO 并关联本地配置 | ✅ 已验证（`mis_bid_10010` + `misCfg n_36`） |
| 客户端"接取" | ✅ 已验证（自动接取，无需 `12402`） |
| **任务栏显示** | ✅ **已验证**（「主线-斗罗魂师」/「去史莱克城找周漪」） |
| **`nil` 问题** | ✅ **已解决**（Phase 4 遗留项一并关闭） |
| `12402` / `12403` 服务端实现 | ✅ 已实现（其中 `12402` 未被触发，属正常） |
| 改 APK / UI / 新增任务定义 | ✅ 未做（只改服务端应答与配置） |

**⇒ 5F 完成。第一条任务（`10010`）已成功"接取"并在原版任务栏正确显示。**

---

**[WAITING FOR PHASE 5G]**
