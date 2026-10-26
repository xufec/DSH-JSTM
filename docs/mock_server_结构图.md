# `server/mock_server.py` 结构图与主线

> 自动生成：`tools/r1b_mock_server_structure.py`。**只读分析，未改动源文件**。

> 目的：把 20k 行压成可读骨架，让"主线在哪、某功能在哪、哪些是死代码"一目了然。


## 一、总览

| 指标 | 值 |
|---|---:|
| 总行数 | **20378** |
| 代码行 | 14612 (71.7%) |
| 注释行 | 4535 (22.3%) |
| 空行 | 1231 |
| **连续注释块(≥5行)** | **284 块 / 3341 行（16.4%）** ← 死代码主体 |
| `[P2X-migrated]` 标记 | 443 处 |
| 顶层 `def` | 369 个 |
| `class` | 3 个 |
| `Handler` 方法 | 20 个 |
| `if cmd == N:` 分支 | 277 个 |
| `if cmd in (...)` 分支 | 99 个 |

> **一句话**：文件不是"乱"，而是**长期增量叠加**——真正的业务逻辑在 14,612 行代码里，另外 **3,301 行是已下沉模块后留下的注释副本**（死代码）。


## 二、主线（从连接建立起）

```
TCP accept
  └─ Handler(SocketServer.BaseRequestHandler)
       └─ handle()  ── recv 循环
            ├─ FrameParser          ← 拆 [u32 len][u16 cmd][body]
            └─ 尾部 **if cmd == N / if cmd in (...)** 主分发链（约 376 个分支）
                 ├─ 专用业务分支（多数）
                 └─ global_default_sc 全局兜底（★ 必须在所有专用分支之后）

HTTP 侧（同一 Handler 类，另一个方向）
  └─ Handler.do_GET
       ├─ /GM*            → gm.console（后台管理系统）
       ├─ /DSH_ADMIN/*    → 管理面（~80 个 action，含 GM 写操作）
       ├─ /DSH_PROBE      → 客户端探针回传
       └─ 资源面          → url_config / version / gateway / notice …
```

**读代码的建议顺序**（按主线逆推）：
1. `class Handler` → `handle()`（TCP 主循环，约在 F 区起点）
2. 主分发链：搜 `if cmd ==` 找到目标命令
3. 该分支调用的 `build_*` / `db_*` —— 在 E 区（业务辅助）
4. 帧编码规则 —— 在 D 区（协议底座）
5. 出问题时：`global_default_sc`（I 区）可能抢先命中 → 见 §五 陷阱


## 三、分区骨架（按行号）

| 区 | 起止行 | 行数 | 代码 | 注释 | 死代码标记 | cmd 分支 | 内容 |
|---|---|---:|---:|---:|---:|---:|---|
| A. 文件头 / 导入 / 全局 | 1–120 | 120 | 57 | 52 | 3 | 0 | |
| B. 场景与 AOI 基础件 | 121–600 | 480 | 375 | 54 | 16 | 0 | |
| C. HTTP Handler：管理面 + 资源面 | 601–2600 | 2000 | 1448 | 452 | 26 | 0 | |
| D. 协议底座：编码器 / 字段 / 默认响应 / 权威编码器 | 2601–7000 | 4400 | 2695 | 1188 | 380 | 0 | |
| E. 业务辅助（货币/背包/任务/场景/战斗/属性等 db_* 与 build_*） | 7001–9800 | 2800 | 2266 | 105 | 1 | 0 | |
| F. TCP 主处理：分发主链（recv → cmd 分支） | 9801–17200 | 7400 | 5695 | 1608 | 11 | 276 | |
| G. 战斗 / 挂机 / 场景内链（154xx / 200xx） | 17201–18300 | 1100 | 656 | 436 | 4 | 27 | |
| H. 登录 / 活动 / 邮件 / 伙伴 / 场景重推（108xx~154xx 尾部） | 18301–20000 | 1700 | 1158 | 540 | 1 | 52 | |
| I. 全局兜底与入口 main() | 20001–20337 | 337 | 228 | 99 | 1 | 21 | |
| **合计** | 1–20378 | **20337** | 14578 | 4534 | 443 | 376 | |


## 四、死代码分布（已下沉模块的注释副本）

连续注释块 ≥5 行的 15 个最大块：

| 起始行 | 行数 | 首行摘要 |
|---|---:|---|
| L5155 | 154 | `# [P3deep-migrated] static_mons/quest_spawn/map_cfg/scene_elems/scene_` |
| L5483 | 111 | `# [P3deep-migrated] mission_rows 已整体下沉 task/service.py（逐字一致）：` |
| L3789 | 78 | `# [P2B-migrated protocol/fields.py::_cs_fields/_sc_w/encode_by_sc_with` |
| L2445 | 75 | `# ★ R80：**10640 已移出**（它现在是专用分支）—— 不移出的话通用默认响应会先命中，` |
| L18060 | 71 | `# [P2B-migrated dispatch/handler.py]         if cmd == 10306:` |
| L4916 | 49 | `# [P2B-migrated persistence/db.py::db_init] def db_init():` |
| L16895 | 47 | `# [P2D-migrated] task/handler.py handle_12408` |
| L16750 | 44 | `# [P2B-migrated dispatch/handler.py]         if cmd == 10101:` |
| L20 | 40 | `# ====================================================================` |
| L4114 | 39 | `# [P3deep-migrated] attr_row_bytes 已下沉 attribute/service.py（L67 import` |
| L20216 | 39 | `# [P2C-migrated inventory/handler.py]         if cmd == 10502:` |
| L19010 | 35 | `# ★★★ 2026-09-19：限时目标/天降豪礼详情查询（客户端真机在发）` |
| L3938 | 34 | `# [P2B-migrated config/loader.py::kconst_rows/str/int]     ★ 两种形态都支持（*` |
| L10572 | 32 | `# [P2B-migrated dispatch/handler.py]         if cmd == 1110:` |
| L4005 | 29 | `# [P2B-migrated config/loader.py::_kcfg_*/kcfg_best_attr_table] def _k` |

> 这些块**全部**以 `[P2X-migrated …]` 开头，指向 `server/` 下已存在的模块文件。
> 它们是"搬家时的原文留档"，**不是**仍在执行的代码。


## 五、已知陷阱（读/改此文件前必看）

1. **兜底位置**：`global_default_sc` **必须**在所有专用分支之后（见 I 区注释）。
   若被挪到前面，所有专用实现都会被它抢走 —— 这是本项目反复踩过的坑。
2. **同一个 cmd 不要既在专用分支又在通用元组里** —— 项目有门禁 `tools/lint_dispatch_shadow.py`；当前为 ✓ 无遮蔽。
3. **`.get(k, default)` 对"键存在但值为 None"返回 None** —— 曾导致每 2.5 秒异常刷屏。
4. **CS body 尾部有 4 字节脏数据** —— 只读规格前 N 字节。
5. **`code==1` 才是成功**，唯一例外 `10200` 要 `code==0`。


## 六、关于"死代码"的处置（**已实测，结论：维持现状**）

尝试过三种方案，**实测结果如下**：

| 方案 | 结果 |
|---|---|
| **A. 原样保留**（当前采用） | ✅ 零风险 |
| B. 整块搬到 `server/_migrated_archive.py` | ❌ **不安全**（见下） |
| C. 直接删除 | ❌ 更不安全 |

### B 为什么不可行（实测证据）

用 `tokenize` 精确识别"纯注释行"后按连续块搬迁，只搬了 39 块就触发 `IndentationError: unexpected indent`。原因是这些注释块**与活代码/活注释交错**：

```
  L3761-3767  # [P2B-migrated …] <旧代码>      ← 列0 注释（可搬）
  L3768            # ② 按 SC 编码                ← 缩进 4 的活注释
  L3769-3774  # [P2B-migrated …] <旧代码>
  L3775-3780            # ★★★ R203：…            ← 缩进 12 的**活注释**（有用）
  ...
  L3787                return w_u16(n) + …        ← **活代码**，缩进 12
```
⇒ 整块移除会**删掉活注释**，并让后面的**活代码失去缩进归属**。
要安全搬，必须对 283 个块**逐块做语义核对** —— 收益只是篇幅，**不值这个风险**。

> **结论**：保留现状。已在 `mock_server.py` 顶部加**导航头**（`tools/r1b_add_nav_header.py`），让主线与分区可读，而不动任何代码结构。

