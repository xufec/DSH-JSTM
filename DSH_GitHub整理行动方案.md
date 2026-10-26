# DSH 文件夹整理与 GitHub 上传行动方案

> 编制日期：2026-10-26 ｜ 状态：待审批
> 目标：梳理 `D:\DSH`（《绝世唐门》1.4.11 复原工程），清理过时/临时/备份文件，整理目录结构，使其适合上传 GitHub，并生成 README。

---

## 一、现状盘点（实测）

### 1.1 总体规模

| 项目 | 数值 |
|---|---|
| 顶层目录数 | 约 60 个 |
| 根目录文件 | 约 45 个（21 个 .md + 17 个日志 + 脚本/杂项） |
| 估算总占用 | **约 26 GB+** |
| Git 状态 | 未初始化（无 .git） |

### 1.2 主要体积构成（实测，非估算）

| 目录 | 大小 | 内容性质 |
|---|---|---|
| `tools/grok-build-main/` | **14.2 GB**（42,269 文件） | 第三方构建产物/依赖，疑似含 node_modules 类巨型依赖 |
| `patched/` | **6.5 GB** | 补丁 APK（含 `dsh.keystore` 签名密钥） |
| `analysis/runtime_evidence/` | **2.25 GB**（945 文件） | 实机截屏/录屏证据 |
| `tools/`（其余） | ~1.4 GB | 第三方逆向工具（jadx/frida/dexdump/protoc/grok 等）+ 反编译输出 + 自研脚本 |
| `anzbao/` | 650 MB | 3 个原版 APK + 分析文本 |
| `cankao/` | 609 MB | 5 个第三方参考项目 zip |
| `001/` | 641 MB | 反编译工具链（jadx-gui/apktool/ghidra/frida-server） |
| `shots/` | 182 MB | 实机截图 |
| `server/` | ~116 MB | 核心服务端代码（其中 logs 54MB / minloop 66MB / 备份 ~165MB） |
| `analysis/`（其余） | ~160 MB | 分析文档 + luac 反编译产物 + 索引 |
| `archive/ backup/ docs/ report/ tests/ protocol/ data/ logs/ photo/ skill/` | ~60 MB | 归档/备份/文档/测试/协议/杂项 |

### 1.3 结构性发现

1. **`server/` 存在 150+ 个 `mock_server.py.bak_rXXX` 备份**（每个约 1.1MB，合计约 165MB），另有大量 `_fix_*.py`、`_p2b_*.py`、`_s2_*.py`、`_t3_*.py`、`_c32_*.py`、`_ml*.lua` 一次性脚本（约 90 个）。
2. **`tools/` 存在 250+ 个 `_fix_r*.py` / `_diag_r*.py` 一次性诊断脚本**，以及大量 `*.txt` / `*.xml` / `*.png` 诊断输出文件（约 300 个）。
3. **16 个 `_tmp_*` 临时目录**（约 27 MB，其中 `_tmp_cfg/` 305 文件 16MB，为 1.4.11 配置提取，需确认是否已被 `server/cfg/` 取代）。
4. **4 个工具生成目录**：`.ruff_cache/`（ruff 缓存）、`.sessions/`、`.dsh-vision-router/`、`.trae-html-share-packages/`——均为程序生成物。
5. **2 个异常目录**：`null/skylot/`（jadx 空输出）、`PowerShell 7.5.4/`（jadx-gui 误建的配置目录）。
6. **根目录 17 个 `logs_*.log`（约 30 MB）**为早期调试日志，已无价值。
7. **根目录 21 个 .md** 为 9 月中旬早期阶段文档（`phase02_*.md`、`startup_*.md`、`*_protocol.md` 等），主文档已迁移至 `docs/`（C1–C4 批次）与 `analysis/`。
8. **`docs_raw/` 与 `docs/_raw/` 内容不重复**（分别为 c3/s2/s3 与 c1/c2 系列），可合并统一。
9. **运行时数据**：`server/game.db`、`server/state/`（jstm.db、roles.db 及备份）、`server/logs/`（7812 个日志文件）、`server/minloop/minloop.db`——均不应进入版本库。
10. **签名密钥 `patched/dsh.keystore`** 存在，**绝不能上传**（安全风险）。

---

## 二、处理策略（三分类）

### A 类：保留进 GitHub（代码与文档主体）

| 项 | 说明 |
|---|---|
| `server/` 代码主体 | 全部模块目录 + `mock_server.py` + `min_loop_server.py` + 配置 json + GM 后台 |
| `docs/` + `docs_raw/` + `docs/_raw/` | 合并为 `docs/raw/`，统一管理 |
| `analysis/` 核心文档 | `extraction/`、`version_compare/`、`INDEX.md`、PHASE 系列、luac 反编译产物（精选） |
| `tests/` | 含 `1.4.11/FINAL_REGRESSION.md` 等 |
| `protocol/`、`report/`、`data/` | 全部保留 |
| `tools/` 自研脚本 | 保留可复用脚本（`lint_dispatch_shadow.py`、`_gm_console_lint.js`、c1/c4 e2e、`minloop_frida_*`、`verify_*` 等正式测试脚本），**排除第三方二进制与输出文件** |
| 根目录精选 | `HANDOFF.md`、`dsh_admin.ps1`、`dsh_admin.bat`、`ruff.toml`、`apk_analyze.py`、`三包对比与选型.md`、`单机版内置服务端.md` 等仍有效的文件 |

### B 类：本地归档（移动至 `D:\DSH\.archive_pre_git\`，git 排除，可恢复）

| 项 | 说明 |
|---|---|
| `server/` 全部 `mock_server.py.bak_*`、`*.bak_*` | 历史备份，Git 版本历史可取代 |
| `server/` 全部 `_fix_*.py` / `_p2b_*.py` / `_s2_*.py` / `_t3_*.py` / `_c32_*.py` / `_ml*.lua` 等一次性脚本 | 已合入主代码，仅留档 |
| `tools/` 全部 `_fix_r*.py` / `_diag_r*.py` / 一次性 `analyze_*.py` | 同左 |
| `tools/` 全部 `*.txt` / `*.xml` / `*.png` / `ui*.xml` 输出文件 | 诊断产物留档 |
| 根目录 `logs_*.log`（17 个） | 早期日志留档 |
| 根目录 21 个早期 .md（`phase02_*`、`startup_*`、`*_protocol.md` 等） | 早期文档留档（如需保留可改放 `docs/archive/`，见决策点④） |
| 根目录杂项：`_tmp_probe_*.luac`、`stateful_replay_out.txt`、`vision_probe.png`、`dsh_admin.ps1.bak` | 临时/备份留档 |
| `_tmp_*` 16 个临时目录 | 全部归档（含 `_tmp_cfg`，经确认已被 `server/cfg/` 取代） |
| `analysis/` 散落的 `_*.txt` 诊断输出、`_*.db` 临时库 | 留档 |
| `logs/` 目录全部 | 留档 |

### C 类：git 排除（留在原地不进版本库，本地工作流不受影响）

| 项 | 说明 |
|---|---|
| `anzbao/`、`patched/`、`001/`、`cankao/`、`shots/`、`photo/` | 大二进制/第三方/版权敏感，全部 `.gitignore` 排除 |
| `tools/grok*`、`tools/jadx*`、`tools/dexdump/`、`tools/frida/`、`tools/ljd/`、`tools/protoc/`、`tools/luajit-decompiler-v2-*`、`cfr.jar`、`jadx.zip` 等 | 第三方工具链与构建产物 |
| `analysis/runtime_evidence/`、`analysis/luajit_src/`、`analysis/runtime_trace/`、`analysis/r1_client_index/` 大文件部分 | 大体积证据/第三方源码（如需少量证据图可精选，见决策点⑤） |
| `server/game.db`、`server/state/`、`server/logs/`、`server/minloop/minloop.db`、`server/world/tests/` | 运行时数据与日志 |
| `.ruff_cache/`、`__pycache__/`、`*.pyc`、`.sessions/`、`.dsh-vision-router/`、`.trae-html-share-packages/` | 缓存与工具生成物（`.ruff_cache` 等纯缓存直接删除，见下） |
| `null/`、`PowerShell 7.5.4/` | 异常目录（直接删除） |
| `.archive_pre_git/` | 归档目录本身 |

**直接删除项**（纯缓存/程序生成垃圾，无保留价值）：`.ruff_cache/`、`PowerShell 7.5.4/`、`null/`、`.sessions/`、`.dsh-vision-router/`、`.trae-html-share-packages/`、全部 `__pycache__/`。

---

## 三、执行步骤

### Phase 1：备份与归档（先于任何删除）
1. 创建 `D:\DSH\.archive_pre_git\`（隐藏目录，git 排除）。
2. 按 B 类清单**移动**（非复制、非删除）所有备份/一次性脚本/日志/早期文档/临时目录至归档区，保持相对结构（如 `archive/server_baks/`、`archive/tools_scripts/`、`archive/root_docs/`）。
3. 直接删除 C 类缓存与异常目录（`.ruff_cache`、`PowerShell 7.5.4`、`null`、`.sessions`、`.dsh-vision-router`、`.trae-html-share-packages`、全部 `__pycache__`）。

### Phase 2：目录整理
4. 合并 `docs_raw/` + `docs/_raw/` → `docs/raw/`（按批次建子目录）。
5. 根目录保留文件归位：早期 .md 按决策点④处理；`apk_analyze.py`、`dsh_admin.*`、`ruff.toml` 留根目录或移入 `tools/`/根目录保持。
6. `analysis/` 清理散落 `_*.txt` 输出与临时 db（移归档），保留核心文档与索引。

### Phase 3：GitHub 配套
7. 编写 `.gitignore`（覆盖 C 类全部项 + 常见 Python 忽略 + `*.bak*` + 大文件白名单）。
8. 编写 `README.md`（内容见第四节）。
9. LICENSE 按决策点②处理。
10. `git init` + 首次提交（提交信息如 `chore: initial commit - DSH 1.4.11 restoration project cleanup`），**不 push**（远程仓库由你创建或提供地址）。

### Phase 4：验证
11. 复查：`git status` 确认暂存内容为 A 类白名单；`git count-objects` 估算仓库体积（目标 <50MB）；抽查 `server/` 可运行性不受影响（不启动服务，仅确认 `mock_server.py` 仍在、配置 json 齐全）。
12. 核对归档区：B 类文件确实已移动（可恢复），原路径不再残留。

---

## 四、README.md 内容规划（中文）

1. **项目标题与简介**：《绝世唐门》1.4.11 客户端复原工程 —— 本地 mock_server 私服研究项目。
2. **免责声明**：项目仅供技术学习与研究，不用于商业用途；游戏客户端与素材版权归原厂商所有；不包含原版 APK 与补丁包。
3. **功能特性**：已闭环系统清单（登录/角色/任务/战斗/背包/商城/邮件/GM 后台等 60+ 系统，引用 HANDOFF.md）。
4. **技术架构**：TCP 9000（协议）+ HTTP 8080（GM/管理面），模块化 server（core/protocol/persistence/…），MuMu 12 模拟器 + adb。
5. **快速开始**：环境要求（Windows + Python 3.12 + MuMu 12）、启动步骤、回归测试（`min_loop_server.py` 145/145）、GM 后台入口。
6. **目录结构**：整理后的结构说明。
7. **证据等级纪律**：CONFIRMED > VERIFIED > STRONG_INFERENCE > INFERENCE > UNKNOWN。
8. **测试与质量基线**：miniloop、c1_e2e、c4_scene_e2e、shadow lint。

---

## 五、风险与注意

1. **版权风险**：原版 APK（`anzbao/`）、补丁 APK（`patched/`）、第三方参考项目（`cankao/`）一律不进仓库；`server/cfg/*.json` 为从 APK 提取的游戏配置数据，属灰色地带——**若仓库设为公开，建议仅保留必需配置并保留免责声明；更稳妥选择是私有仓库**。
2. **密钥安全**：`patched/dsh.keystore`（APK 签名密钥）绝不入库，已在排除清单。
3. **体积**：GitHub 单文件上限 100MB，本方案仓库体积目标 <50MB，符合要求。
4. **可恢复性**：采用"移动归档"而非直接删除，误判可恢复；确认满意后归档区可自行删除。
5. **数据库与日志**：运行时 db 与日志不入库，避免敏感数据与仓库膨胀。

---

## 六、待确认决策点（请审批时回复）

1. **归档策略**：推荐"移动归档"（`.archive_pre_git/` 保留可恢复）；如需彻底删除可改选"直接删除"。
2. **LICENSE**：推荐不生成正式 LICENSE（因含游戏素材，仅 README 免责声明）；或选择 MIT。
3. **仓库可见性**：公开 or 私有（影响版权风险与配置数据取舍）。
4. **根目录早期 .md（21 个）**：推荐移入归档（`archive/root_docs/`）；或改放 `docs/archive/` 进入版本库。
5. **实机证据图**：`shots/`（182MB）与 `analysis/runtime_evidence/`（2.25GB）默认全部排除；如需精选少量关键证据图入仓可说明。

---

*本方案所有数据均来自 2026-10-26 对 `D:\DSH` 的实际探查（PowerShell 只读统计），可复核。*
