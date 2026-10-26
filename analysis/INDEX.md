# analysis/ 总索引 —— 《绝世唐门》JSTM 1.4.11 复原工程

> 最后更新：2026-10-06（PHASE 2.17 后）
> **接手者请先读本页**，再按需跳文档；可跳过后文全部，直接跑 `tests/1.4.11/RUN_TESTS.ps1 -SelfStart` 验证现状。

---

## 一、一句话现状

- **目标 (1) 1.3.0 资源清单 + version_diff_matrix**：✅ **已完成**（`version_compare/1.3.0/`）
- **目标 (2) 系统实现**：已注册 **34** 条命令（19 既有 + **本批 15 条**）；
  剩余缺口**全部阻塞在证据**（需实机 / 需真值），**无一属"工时不够"**。

---

## 二、★ 三条必知结论（会直接影响你做什么）

### 1. 先查客户端发不发 —— **死协议不做**

判据：`server/logs/tcp.log` 里 `>> cmd=N` 的次数。**发 = 0 就一律不实现**。
已据此排除：**送花**(13324/13326/13328/16300)、**聊天**(127xx)、
**好友扩展**(13306/13310/13314/13319/13320/13341/13342/13349)、`30503/30506`、`13369`（空表本就正确）。

### 2. 判"回空"必须走 **4 类判定法**（缺一步会误判）

| 类 | 表现 | 例 | 处置 |
|---|---|---|---|
| ① 真缺口（半接）| 写入侧/GM **有**数据源，**读侧没接** | `14901`（已修）| ✅ 可修 |
| ② 角色无数据 | 读侧**已接**，表里没这行 | `11300`、`13369` | 无需动 |
| ③ 有意回空 | 读侧**故意**不填（注释写明）| `11700`/`16605`/`10924`/`10923` | 待实机语义 |
| ④ 配置侧未填 | handler 读了 config 键，但**键缺失/为空** | `10527`、`10532` | **需真值来源** |

**判前两步**：① `tcp.log` 发没发 → ② 按 `fields.json` 精确构造 CS（`tools/probe_by_cs_spec.py`，
**别猜参数**，否则得到第二次假象）。

### 3. 剩余缺口的**阻塞类型**（详见 `tests/1.4.11/FINAL_REGRESSION.md` §附二.5）

**2 项已收口** ｜ **3 项需实机 MuMu**（#5/#6/#7）｜ **3 项需真值**（#1/#2/#3）｜ **1 项需真服**（#8）。

---

## 三、本批（PHASE 2.11 ~ 2.17）新增系统

| 系统 | 命令 | 模块 | 测试 | 阶段文档 |
|---|---|---|---|---|
| 答题 | 16100~16103 | `server/answer/` | `tools/test_answer.py` | `PHASE2_12_ANSWER_QUIZ.md` |
| 开服成长计划 | 30500~30502 | `server/growth_target/` | `tools/test_growth_target.py` | `PHASE2_13_GROWTH_TARGET.md` |
| 刮刮乐 | 16651/16652 | `server/scratch/` | `tools/test_scratch.py` | `PHASE2_14_SCRATCH.md` |
| 好友 | 13300/13303/13305/13307/13321/13323 | `server/friend/` | `tools/test_friend.py` | `PHASE2_15_FRIEND.md` |
| 称号 | 14901 | `mock_server.py` | 手工（见回归索引§三）| `PHASE2_17_TITLE_14901.md` |
| GM 累计充值 / `16900` | `/DSH_ADMIN/setcharge`、`16900` | `mock_server.py` | 手工 | `PHASE2_16_16900_AND_FRIEND_SATURATION.md` |

**一键回归**：`pwsh -File tests/1.4.11/RUN_TESTS.ps1 -SelfStart`
（自启测试服务端 → 跑全 6 项 → 自动恢复生产模式）
索引：`tests/1.4.11/NEW_SYSTEMS_REGRESSION.md`

---

## 四、选靶 / 取证依据（做决定前看这里）

| 文档 | 用途 |
|---|---|
| `extraction/dead_protocols_and_traffic.md` | ★ **死协议清单 + 真实流量画像（132 命令/6496 次）+ 空表 4 类法** |
| `extraction/core_gameplay_candidates.md` | 核心玩法候选评估（含"答题为何需项目推导键"）|
| `../analysis/gap_map.txt` + `tools/gap_map.py` | 按真实流量生成的缺口地图（含**两个假阳性类**说明）|
| `jstm_game_systems/unimplemented_systems.md` | 42 项未实现系统清单 |
| `version_compare/1.3.0/inventory.md` | 目标 (1) 交付：1.3.0 资源盘点（版本自证 CONFIRMED）|
| `version_compare/version_diff_matrix.md` | 三版本差异矩阵 |

---

## 五、纪律（违反即错）

1. **不编造**：数值只来自 APK / `server/cfg` / 运行实测；取不到标 `INFERENCE`/`UNKNOWN` 并**留替换点**。
2. **证据分级**：`CONFIRMED > VERIFIED > STRONG_INFERENCE > INFERENCE > UNKNOWN`，**勿把 UNKNOWN 写 CONFIRMED**。
3. **测试卫生**：客户端测试跑在**真实角色 1001** 上 ⇒ 必须 `snapshot()` + `cleanup()` 还原背包/资产/新表/`reward_log`。
4. **改前备份** `server/mock_server.py` → `server/backup/*.bak_rXXX`。
5. **每次改动后**跑 `RUN_TESTS.ps1` + 核 `/DSH_ADMIN/status` 基线（`lv70 / scene 10001`）。
6. **客户端有处理器 ≠ 会用**：`10305`/`10622` 都注册了处理器，一个从不请求、一个从不发送。

---

## 六、本批踩过的坑（别再踩）

| 坑 | 教训 |
|---|---|
| 手工**猜参数**复探空表 | 得到"第二次假象"（`CS_15203` 其实是**空消息**）⇒ 必须按 `fields.json` 构造 |
| 测试把奖励发进**真实角色**背包 | 首跑污染了存档 ⇒ 已加 `snapshot/cleanup`；**跑测试前先想好还原** |
| 测试自身 Python 求值顺序 | `out[r.u32()] = r.u32()` 会**先算右侧** ⇒ bid/num 反读（测试 bug，非服务端）|
| 用字节码 `type` 分派推断命令语义 | 推出"30507=登录"，被 **`cmd_table` 命令名否决** ⇒ **命令名优先** |
| 跨文档引用未核 | `15203` 被误记为"NPC 交互"，实为**元宝兑换宝图** ⇒ 引用前先核 `cmd_table` |
| miniloop 偶发 143/145 | 是**独立服务**的端口/时序抖动（连跑 3 次均 145/145）⇒ 以 **×3 稳定**为准 |

---

## 七、目录速查

```
server/answer/         答题（16100~16103）
server/growth_target/  开服成长计划（30500~30502）
server/scratch/        刮刮乐（16651/16652）
server/friend/         好友（13300/13303/13305/13307/13321/13323）
server/{core,protocol,session,role,item,inventory,currency,reward,...}  既有模块
tools/test_{answer,growth_target,scratch,friend}.py   客户端回归
tools/{gap_map,probe_by_cs_spec,reprobe_with_args,lint_dispatch_shadow}.py  取证/门禁
tests/1.4.11/RUN_TESTS.ps1                            一键回归
tests/1.4.11/FINAL_REGRESSION.md                      9 缺口 + 阻塞类型标签
tests/1.4.11/NEW_SYSTEMS_REGRESSION.md                本批系统索引
```
