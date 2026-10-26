# 1.4.11 复原工程 —— 新系统回归索引

> 一键运行（**推荐**，答题项也可跑通）：
> `pwsh -File tests/1.4.11/RUN_TESTS.ps1 -SelfStart`
> 用现有服务端：`pwsh -File tests/1.4.11/RUN_TESTS.ps1`
> 仅静态门禁（不需服务端）：`pwsh -File tests/1.4.11/RUN_TESTS.ps1 -Static`

---

## 〇、`-SelfStart` 做什么（会短暂影响在线服务端）

| 步 | 动作 |
|---|---|
| 1 | 记录 9000 上是否已有服务端 |
| 2 | 有则**停掉**，以 `DSH_ANSWER_OPEN=1` 启动**测试服务端** |
| 3 | 跑全部客户端回归（答题项因时段放开而**可跑通**，不再是 SKIP）|
| 4 | 停测试服务端 → **若步骤 1 有服务端，自动恢复为生产模式**（无覆盖变量）|

> 实测：`-SelfStart` 下 **4 项客户端回归全部 ALL PASS**（答题不再 SKIP），
> 跑完自动恢复生产模式（复验：`16101` 正确返回"不在活动时间"），且**测试残留为 0**。

---

## 一、一键回归覆盖范围

| 阶段 | 内容 | 判据 |
|---|---|---|
| 静态 | `miniloop selftest` **×3** | 每次都 `检查项 145，通过 145，失败 0` |
| 静态 | `py_compile` | 9 个文件（mock_server + 4 个新模块）全部通过 |
| 静态 | `shadow_lint` | `✓ 无分发遮蔽` |
| 客户端 | 答题 16100~16103 | `ALL PASS`（时段外自动 `SKIP`）|
| 客户端 | 开服成长计划 30500~30502 | `ALL PASS` |
| 客户端 | 刮刮乐 16651/16652 | `ALL PASS` |
| 客户端 | 好友 13300/13321/13303/13305/13307/13323 | `ALL PASS` |
| 客户端 | **活动族 16605/10923/16602/16664** | `ALL PASS`（PHASE 2.18~2.21 的改动）|
| 客户端 | **零散修复 14901/16900/GM setcharge** | `ALL PASS`（PHASE 2.16~2.17 的改动）|
| 基线 | `/DSH_ADMIN/status` | `lv=70 scene=10001` |

> ★ **本会话的服务端改动已 100% 进入自动化门禁**（6 个客户端套件）。
> 唯一未自动化的是 `16605`/`10924` 这类**依赖实机 UI 观察**的行为断言（须人眼看面板）。

> ★ **注意答题项的时段**：`16101` 只在 `11:00-13:00` / `17:00-19:00` 开放。
> **时段内跑会显示 `ALL PASS`（这是正确的）**；时段外则显示 `SKIP`。
> 见下方"⚠ 答题的时段门禁"。

**退出码**：0 = 全过；非 0 = 有失败项（`SKIP` 不计为失败）。

### ⚠ 答题的时段门禁

`16101` 只在配置时段（11:00-13:00 / 17:00-19:00）开放。时段外跑回归会看到：

```
[SKIP] 无法开始答题：不在活动时间（时段外需以 DSH_ANSWER_OPEN=1 启动 mock_server）
```

要跑通该项，用**测试模式**启动服务端：

```powershell
$env:DSH_ANSWER_OPEN='1'; python server/mock_server.py --http 8080 --game 9000
```

> `DSH_ANSWER_OPEN` 是**测试/联调专用**环境变量，**不写进 `config.json`**，不影响正式行为。

---

## 二、本批次（PHASE 2.11 ~ 2.17）新增系统

| # | 系统 | 命令 | 模块 | 测试 | 文档 |
|---|---|---|---|---|---|
| 1 | **答题** | 16100/16101/16102/16103 | `server/answer/` | `tools/test_answer.py` | `PHASE2_12_ANSWER_QUIZ.md` |
| 2 | **开服成长计划** | 30500/30501/30502 (+`16900` 读 + GM `setcharge` 写) | `server/growth_target/` | `tools/test_growth_target.py` | `PHASE2_13_GROWTH_TARGET.md`、`PHASE2_16_*.md` |
| 3 | **刮刮乐** | 16651/16652 | `server/scratch/` | `tools/test_scratch.py` | `PHASE2_14_SCRATCH.md` |
| 4 | **好友** | 13300/13321/13303/13305/13307/13323（+`13304`/`13308`/`13322` 推送）| `server/friend/` | `tools/test_friend.py` | `PHASE2_15_FRIEND.md` |
| 5 | **称号** | 14901（接 `role_title` 真值）| `mock_server.py` 内 | 见 §三 | `PHASE2_17_TITLE_14901.md` |
| 6 | **GM 累计充值** | `GET /DSH_ADMIN/setcharge?n=80[&rid=]` | `mock_server.py` 内 | 见 §三 | `PHASE2_16_*.md` |

**共 15 条游戏命令**从"假成功/空表"升级为"真落库 / 真发奖 / 真推送"。

---

## 三、无独立测试脚本的两项（手工验证命令）

### 5. 称号 `14901`（读 `role_title`）

```powershell
# 发两个称号（与 GM 同一条写入路径）
python -c "import sys;sys.path.insert(0,'server');from mock_server import db_title_add;db_title_add(1001,1001);db_title_add(1001,1002)"
# 查：应回 titles=2（修前恒 0）
python tools/probe_by_cs_spec.py --port 9000 14901
# 清理
python -c "import sqlite3;c=sqlite3.connect('server/state/roles.db');c.execute('DELETE FROM role_title');c.commit()"
```

### 6. GM 累计充值 `setcharge`

```powershell
Invoke-WebRequest 'http://127.0.0.1:8080/DSH_ADMIN/setcharge?n=80' | Select -Expand Content
# → {"ok": true, "rid": 1001, "total_charge": 80}
# 服务端 16900 应回 charge=80；30502 达到 charge_gold 门槛后即可领
Invoke-WebRequest 'http://127.0.0.1:8080/DSH_ADMIN/setcharge?n=0'   # 还原
```

---

## 四、选靶/取证依据（后续接手必读）

| 文档 | 用途 |
|---|---|
| `analysis/extraction/dead_protocols_and_traffic.md` | ★ **死协议清单** + 真实流量画像 + "真值 vs 空表"复核 + **空表 4 类判定法** |
| `analysis/gap_map.txt` / `tools/gap_map.py` | 按真实流量生成的缺口地图（含**两个假阳性类**说明）|
| `analysis/extraction/core_gameplay_candidates.md` | 核心玩法候选评估（含"答题为何需要项目推导键"）|
| `analysis/jstm_game_systems/unimplemented_systems.md` | 42 项未实现系统清单 |

### ★ 空表 4 类判定法（判"回空"必用，缺一步会误判）

| 类 | 表现 | 例 | 处置 |
|---|---|---|---|
| ① 真缺口（半接）| 写入侧/GM 有数据源，**读侧没接** | `14901` | ✅ 可修 |
| ② 角色无数据 | 读侧已接，**表里没这行** | `11300`、`13369` | 无需动 |
| ③ 有意回空 | 读侧**故意**不填（注释写明）| `11700`/`16605`/`10924`/`10923` | 待实机语义 |
| ④ 配置侧未填 | handler 读了 config 键，但**键缺失/为空** | `10527`、`10532` | **需真值来源** |

**判前先做**：查 `tcp.log` 的 `>> cmd=N`（发=0 ⇒ 死协议，不做）。

---

## 五、纪律提醒（接手者）

1. **不编造**：数值只来自 APK / `server/cfg` / 运行实测；取不到就标 `INFERENCE`/`UNKNOWN` 并留替换点。
2. **测试卫生**：测试跑在**真实角色 1001** 上 ⇒ 必须 `snapshot()`+`cleanup()` 还原背包/资产/新表/`reward_log`。
3. **改前备份** `server/mock_server.py` 为 `.bak_rXXX`（现存于 `server/backup/`）。
4. **每次改动后**跑 `RUN_TESTS.ps1` + 核对 `/DSH_ADMIN/status` 基线。
5. **死协议不做**：先看客户端发不发。
