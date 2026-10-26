# LICENSE 审计（R1 强制项）

> 任务书【原则 3】要求：检查每个参考项目 LICENSE；LICENSE 不明确时**可研究、可借鉴设计、不要直接复制代码**。
> 本文件是**逐个 ZIP 实测**的结果，不是推测。

---

## 一、审计结果总表

| # | 项目 | ZIP 大小 | 文件数 | **LICENSE 文件** | **结论** |
|---|---|---|---|---|---|
| 1 | **Survive** | 207.7 MB | 2618 | **无顶层**，但 `aoi.h`/`astar.h`/`wordfilter.h` **内嵌 GPLv3** | 🔴 **核心模块明确 copyleft** ⇒ 只可读设计 |
| 2 | **CXEngine**（疑为 YZXY 引擎） | 14.8 MB | 501 | **无** | ⚠️ **未声明许可** ⇒ 只可借鉴设计 |
| 3 | **MahatmaComeBack** | 18.2 MB | 164 条目（**136 文件** + 28 目录） | **`LICENSE` = GNU GPL v3** | 🔴 **copyleft** ⇒ **代码不得进入 JSTM** |
| 4 | **ChivalrousMan** | 51.2 MB | 1539 条目（**1411 文件**） | **无** | ⚠️ **未声明许可** ⇒ 只可借鉴设计 |
| 5 | **kongkongxiyou** | 331.8 MB | 22486 | 仅 **cocos2d-x 自带** licenses（第三方组件），**无项目自身 LICENSE** | ⚠️ **未声明许可** ⇒ 只可借鉴设计 |

**检测方法**：扫描 ZIP 内 `LICENSE*` / `COPYING*` / `NOTICE*`；
对 `Survive` 命中的 `notice_normal.png` 属**误报**（是资源图，非许可证）。

---

## 二、逐项说明

### 1. Survive —— 无 LICENSE

- 顶层：`client/`、`gameserver/`、`gateserver/`、`groupserver/`、`php/`、`doc/`
- 命中"LICENSE"的只有 `client/res/UI/main/notice_normal.png`（**误报**）
- **⇒ 无可复用许可依据 ⇒ 按任务书【原则 3】：只借鉴设计，不复制代码**

### 1.5 ★ 更正（子代理逐文件审计发现，2026-09-18）：Survive **部分文件内嵌 GPLv3**

**原判**：Survive 无 LICENSE ⇒ 默认不可复制（弱约束）
**实测更正**：以下文件**文件头内嵌 GPLv3 全文声明**（`Copyright huangweilook@21cn.com`）：
```
common/aoi.h          ← AOI 模块（JSTM 最想学的）
common/astar.h        ← 寻路模块
common/wordfilter.h   ← 敏感词
```
**⇒ 这三块**从"默认不可复制"升级为"明确 copyleft 传染"** —— **连"翻译成 Python"都有风险。**
**另**：`common/b64.h` + `encode.c` + `decode.c` 来自 joseph werle，**许可文本缺失**。

**⇒ 结论：Survive 的 AOI/寻路**只能读"设计思想"**（均匀网格 + 视野集合去重 + 新旧集合差 +
双向 enter_see/leave_see 回调；A* 8 邻域 + Bresenham 直线裁剪），**实现必须完全自写**。**

---

### 2. CXEngine —— 无 LICENSE

- 顶层：`scripts/`（`client/ server/ combat/ share/ generator/ examples/`）、`server/src/`
- **⇒ 同上，只借鉴设计**

### 3. MahatmaComeBack —— 🔴 **GPL-3.0**

原文首行：
```
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007
Copyright (C) 2007 Free Software Foundation, Inc.
```

- 服务端：`Server/游戏服务器`（**15 文件**；`Server/` 下合计 19）+ `Server/gametable.sql`（R2 逐条目实测更正，原写 17）
- **⇒ GPL-3.0 是强 copyleft：一旦把其代码并入 JSTM，JSTM 整体须以 GPL-3.0 发布。**
- **⇒ 本项目定位是"私服兼容服务端"、可能含闭源成分** ⇒ **不得复制其代码**（可读其设计思路）
- **⇒ 覆盖范围含 `Classes/`（客户端 C++）、`Resources/`（美术与字体）、`Server/`、`gametable.sql`** ⇒ **连 `gametable.sql` 文本也不得导入 JSTM 建库脚本**（详见 `mahatma/reuse_candidates.md` §1.2）

### 4. ChivalrousMan —— 无 LICENSE

- 顶层（R2 逐条目实测更正）：**没有 `client/` 目录**；顶层目录为 `Classes/`、`Resources/`、`cocosstudio/`、`include/`、`lib/`、`proj.android/`、`proj.ios_mac/`、`proj.win32/`，另有 6 个顶层文件（`.cocos-project.json`、`ChivalrousMan.ccs/.cfg/.udf`、`config.json`、`README.md`）
- 自研代码仅 **`Classes/` 的 191 个文件（92 .cpp + 99 .h）**；`.java` 31 / `.class` 128 **全部是 cocos2d-x 与 CocosPlay 框架文件**，无一行游戏逻辑
- **⇒ 无 `server/` 目录；服务端源码在作者另开的 `https://gitee.com/lsylovews/CM-Server`（不在本 ZIP）**（见 `chivalrousman/architecture.md` 的 11 条实证）
- ⚠ **重要补充**：该"客户端"用 **libmysql 直连公网 MySQL**（`Classes/DBDao.h` 硬编码 `47.93.235.6` / `game` / 明文口令 / 库 `chivalrousman`），
  因此它**同时暴露了一套 5 张表 / 33 字段的 MMORPG 业务库结构** ⇒ 它的价值**不止客户端 UI，还包括数据层对照基线**
  （已体现在 `comparison/architecture_matrix.md` 的"数据库"行：表结构参考改为 ChivalrousMan）
- **⇒ 只借鉴设计（字段语义 / 流程 / 结构），不复制代码与美术资源**（见 `chivalrousman/reuse_candidates.md`）

### 5. kongkongxiyou —— 无项目级 LICENSE

- 命中的全是 **cocos2d-x 框架自带**的第三方许可（`LICENSE_AA-EDT.txt`、`LICENSE_JSON4Lua.txt` 等）
- **⇒ 这些许可约束的是 cocos2d-x 组件本身，不构成对项目代码的授权**
- **⇒ 只借鉴设计**

---

## 三、★ 对 JSTM 的许可结论

| 允许 | 禁止 |
|---|---|
| ✅ 阅读全部 5 个项目源码 | ❌ 复制 MahatmaComeBack 代码（GPL-3.0 传染） |
| ✅ 借鉴架构/算法**思想** | ❌ 复制其余 4 个项目代码（无许可依据） |
| ✅ 用 JSTM 自己的协议重新实现 | ❌ 把参考项目的代码文件加进 `server/` |
| ✅ 引用其公开文档（README 等）说明设计来源 | ❌ 声称这些代码是自研 |

**⇒ 若将来确需复用某段代码，必须先补齐该项目的许可授权（或联系作者），
并在此表登记「来源文件 / LICENSE / 是否可再发布 / 是否进入 JSTM」。**

---

## 四、登记表模板（后续每段拟复用代码都要填）

| 来源项目 | 文件路径 | LICENSE | 功能 | 与 JSTM 差异 | 是否可复用 | 是否进入 JSTM |
|---|---|---|---|---|---|---|
| （待填） | | | | | | |
