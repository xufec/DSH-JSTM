# 《绝世唐门》1.4.11 复原工程（DSH）

使用原版《绝世唐门》1.4.11 客户端（MuMu 模拟器）+ 本地 `mock_server`，尽可能恢复原游戏完整玩法闭环的**单机私服复原研究项目**。

> 核心交接文档：`HANDOFF.md` ｜ 最终回归报告：`tests/1.4.11/FINAL_REGRESSION.md`

## ⚠️ 免责声明

本项目**仅供技术学习与逆向研究使用，不用于任何商业用途**。
- 原版游戏客户端、素材与数据的版权归原厂商所有；
- 仓库**不包含**原版 APK、补丁 APK 与第三方参考项目（本地保留，已通过 `.gitignore` 排除）；
- 如权利方认为内容侵权，请联系删除。

## ✨ 功能特性

已闭环的系统（60+）：登录 / 角色 / 等级 / 经验 / 背包 / 仓库 / 装备 / 任务 / 商城 / 黑市 / 邮件 / 排行 / 副本 / 挂机 / 签到 / 日常 / 成就 / 结拜 / 结婚 / 拍卖 / 法宝 / 翅膀 / 坐骑 / 魂兽 / 元神 / 神器 / 命格 / 椅子 / 时装 / 光环 / 符文 / 投资 / BOSS / 称号 / 阵法书 / 伙伴面板 / 技能学习 / **GM 后台管理系统**。

## 🏗️ 技术架构

```
客户端（MuMu 12 / Android 12，APK 1.4.11 com.shiyue.dldl.ewan.baidu2）
        │  TCP 9000（游戏协议）  /  HTTP 8080（GM / 管理面）
        ▼
mock_server（server/mock_server.py，单文件 ~1100 KB 单体服务）
        ├── 模块化架构：core / protocol / persistence / attribute / currency /
        │   role / task / equipment / scene / battle / gm ...
        ├── 配置：config.json / _attr_data.json / _chengjiu.json / _guaji.json ...
        ├── GM 后台：server/gm/console.html（单文件 SPA，零构建）
        └── 测试：server/minloop/（miniloop 自检 145/145）
```

- **客户端指向**：`10.0.2.2:9000`（TCP）/ `10.0.2.2:8080`（HTTP）
- **服务重启后客户端约 11 秒自动重连**
- **battle_replay 确定性重放**：两次重放 hex 必须一致（锚点 `server/backup/replay_before.json`）

## 🚀 快速开始

### 环境要求
| 依赖 | 说明 |
|---|---|
| OS | Windows（本项目实测环境） |
| Python | 3.12.x（`D:\Python\python.exe` 或 Anaconda3） |
| MuMu 12 | Android 12 模拟器，adb 连接 `127.0.0.1:16384` |
| APK | 1.4.11 补丁包（本地 `patched/`，不入库） |

### 启动步骤
```powershell
# 1. 启动 mock_server（TCP 9000 + HTTP 8080）
python server/mock_server.py

# 2. 启动后访问 GM 后台（默认 token: dshgm）
#    http://127.0.0.1:8080/GM

# 3. 打开模拟器中的客户端进入游戏
#    端口就绪后 /status 返回 lv70/gold=1799840/coin=9904599/scene=10001 为基线
```

### 回归测试
```powershell
# miniloop 自检（改代码后必跑，预期 145/145）
python server/minloop/selftest.py

# 端到端测试
python tools/c1_e2e_closed_loop.py        # PASS=21 / FAIL=0 / NOT_RUN=1
python tools/c4_scene_e2e.py              # 12/12 PASS

# 静态校验
python tools/lint_dispatch_shadow.py      # 无分发遮蔽
node tools/_gm_console_lint.js server/gm/console.html   # GM 后台 OK
node tools/lua-check/check.js server/url_config_ewan.lua # OK
```

## 📁 目录结构

```
DSH/
├── HANDOFF.md                  # AI 交接文档（入口）
├── server/                     # 核心服务端
│   ├── mock_server.py          # 主服务（改前存 .bak_rXXX，本仓库已清理历史备份）
│   ├── minloop/                # miniloop 自检（145/145）
│   ├── gm/                     # GM 后台（console.html + console.py）
│   ├── core/ cfg/ config/ protocol/ persistence/ ...
│   └── backup/replay_before.json   # battle_replay 字节锚点
├── docs/                       # 实施文档（C1–C4 批次 + raw/ 原始记录）
├── analysis/                   # 逆向分析（审计报告 / 真值 / 版本对比 / luac 反编译）
├── tests/                      # 测试与回归（1.4.11/FINAL_REGRESSION.md）
├── protocol/                   # 协议文件（cmd_table / fields / manual）
├── report/                     # 各阶段报告
├── tools/                      # 自研分析/测试脚本（第三方工具链已 git 排除）
├── data/                       # 数据文件
└── archive/                    # 本地归档（server_snapshots 等，git 排除）
```

> 被 `.gitignore` 排除的内容（本地保留，不入库）：`001/` `anzbao/` `patched/` `cankao/` `shots/` `photo/` `skill/`、tools 第三方工具链、`analysis/runtime_evidence/` 等大体积证据、运行时数据库与日志、`.archive_pre_git/` 整理归档区。

## 🔬 证据等级纪律

```
CONFIRMED（APK/协议/资源/实机直接确认）
  > VERIFIED（实机 + mock_server 实际运行）
  > STRONG_INFERENCE（多源推断）
  > INFERENCE（结构推断无直接证据）
  > UNKNOWN
```

禁止把 UNKNOWN 写成 CONFIRMED；唯一数值标准是 JSTM APK + 资源 + 协议 + MuMu 实机运行结果。CONFIRMED 真值见 `analysis/extraction/truth_values.md`。

## 🧪 质量基线（2026-10-16 C4 批次）

| 门禁 | 结果 |
|---|---|
| miniloop selftest | 145/145（连跑 2 次一致） |
| c1_e2e_closed_loop | PASS=21 / FAIL=0 / NOT_RUN=1 |
| c4_scene_e2e | 12/12 PASS |
| lint_dispatch_shadow | 无分发遮蔽 |
| GM 传送实测 | 10001→10005→10010→10002 画面正确跟随 |

## 📄 许可证

本项目不附带正式开源许可证。代码与文档仅作学习研究用途，相关游戏版权归原厂商所有。
