# 协议规格审计与 CS_16603 回滚修正报告（2026-09-19 · round35）

> 承接"协议定义挖掘 → 具体对接"。本轮**没有新增功能**，做了一件更要紧的事：
> 引入**第二条独立还原路径**去审计 `protocol/fields.json`，并据此**回滚了上一轮（round34）引入的错误规格**。

---

## 一、发现并修正：CS_16603 规格回归

### 1.1 症状

round34 把 `CS_16603` 从 `{bid:uint32}` 改成 `{bid:uint32, num:uint32}`，依据是
「真机 body 恒 8 字节」+「proto#5 有 TSETS bid/num 两行」。

### 1.2 真正的证据（AutoConstruct 调用点）

`cmd_resolve_166.luac` 里每条消息由
`KSTR 'cs'|'sc'` + `KSHORT <cmd>` + `TDUP <spec 数组>` 定义。实测：

| 方向 | cmd | spec 数组 |
|---|---|---|
| **cs** | **16603** | **`['bid__I']` —— 只有 1 个字段** |
| sc | 16603 | `bid__I`, `remain_sec__I`, `finish__I`, `aim_list__T__…`, `item_effect_list__T__…`, `int_args__T__val@I`, `client_reward__s`, `rank_list__T__…` |
| cs | 16604 | `bid__I`, `aim__I`, `arg__I`（= `sender16604(1015, aim, 1)` 三个实参）|
| cs | 16605 | `bid_list__T__bid@I` |
| sc | 16605 | `status__T__bid@I##code@C##end_time@I` |

round34 引用的 `proto#5`（TSETS bid,num）其实是 **`Dsc16603item_list` 的读取器**
（`SC_16603.aim_list[].item_list` 的元素结构），不是 CS 主消息。

### 1.3 为什么"8 字节"会骗人：尾部 4 字节残留（本轮关键洞察）

扫描 341 个真机抓包后发现，**客户端每个 CS body 尾部都多出 4 字节缓冲区残留**：

| 命令 | CS 规格真实长度 | 抓包 body 长度 | 抓包 body |
|---|---|---|---|
| 16500 | 0（空消息） | 4 | `00660000` |
| 17200 | 0（空消息） | 4 | `010103e9` |
| 16400 | 1（type:u8） | 5 | `0100000003` |
| 16603 | 4（bid:u32） | 8 | `00000be1 0001316f` |
| 16605 | 410（2+102×4） | 414 | `…2d2d2d2d`（"----"）|

⇒ **包长只能给出"不超过"的上界，不能反推字段个数**：`{bid}` 与 `{bid,num}`
对 8 字节 body 都"对得上"。**规格必须以 AutoConstruct 为准。**

### 1.4 修正内容

| 文件 | 改动 |
|---|---|
| `protocol/fields.json` | `CS_16603` 还原为 `[{bid:uint32}]`，`source=spec`，note 记录回滚依据 |
| `server/mock_server.py` | 16603 注释改写（CS 规格 4 字节 + 残留说明）；长度告警 `len(body) < 8` → `< 4` |
| `server/mock_server.py` | 通用集合旁注释同步修正 |
| `tools/verify_16603.py` | CS 断言改为单字段；抓包解析改为「取前 4 字节为 bid，其余标注残留」|
| `tools/test_11215_10800.py` | 16603 用例注明第二段是残留而非 num 字段 |
| `analysis/1.4.9/round34_16603.md` | 顶部加作废横幅（第一节结论失效，SC 部分仍有效）|

---

## 二、新工具：`tools/audit_specs_vs_fields.py`

### 2.1 定位

`protocol/fields.json` 由 `tools/extract_fields.py` 生成，路径是
「类名 → 注册原型 FNEW → builder proto → spec 数组」。这条路径可靠但**不会自检**，
一处错配会静默进入产物（round34 就是这样发生的）。

本工具走**第二条独立路径**：直接扫描全部 `cmd_resolve_*.luac` 里 spec 表常量
（`TDUP` 字符串数组），向**前**开窗取最近的 `KSTR('cs'|'sc')` 与 `KSHORT` 还原 (方向, 命令号)，
再与 fields.json 逐字段比对（名称/类型/顺序/子表 items 全比）。

### 2.2 审计结果（全量）

```
调用点(独立还原)条目: 2463
fields.json 命令对 : 3079
一致 2463 / 不一致 0 / 仅规格 0 / 仅fields(有字段) 0 / fields空 0
空消息(无 spec，一致视为正常) 616
```

- **2463 条带 spec 的消息：字段名、类型、顺序、子表结构 100% 一致，零不一致。**
- 616 条差额全部是**空 CS 消息**（如 `CS_10111`、`CS_10301`、`CSMapGird_10201`），
  本就没有 spec 数组，属正常。

### 2.3 灵敏度自检（证明它能抓到 round34 那个错）

```
spec        : (('bid','uint32'),)
正确 fields : (('bid','uint32'),)                    -> 一致
错误 fields : (('bid','uint32'), ('num','uint32'))   -> ✗ 不一致（会被审计抓到）
```

⇒ 该审计对"多一个字段"这类错误**确实敏感**，不是空转。

用法：
```bash
python tools/audit_specs_vs_fields.py                 # 全量审计
python tools/audit_specs_vs_fields.py --cmd 16603      # 单命令
python tools/audit_specs_vs_fields.py --json out.json   # 落盘
```

---

## 三、验证与回归

| 项目 | 结果 |
|---|---|
| `tools/verify_16603.py` | **PASS** — CS 规格=`[('bid','uint32')]`；5 组抓包 bid=3041/3041/3041/0/3041，残留各 4 字节；SC 22 字节精确消耗 |
| `tools/test_11215_10800.py`（端到端） | **PASS** — 11215×53 伙伴 / 10800×1 邮件 / 10924×74 活动 / 16603 bid=3041 回显 |
| `tools/_finalreg.py`（核心回归） | **24 通 / 0 失败** |
| 服务端重启 | PID 40240，`known messages: 2463, known commands: 1634`，stderr 空 |
| CS 解析全量核对 | `mock_server.py` 内所有 `len(body)` 读取均为 `>= N` 前缀式，天然容忍尾部残留；16603 是唯一严格长度检查，已修正 |

---

## 四、纪律沉淀

1. **规格来源优先级**：`AutoConstruct spec` > reader 原型（`Dsc*`）> 抓包长度。
   读包长只能证明"至多这么多字段"，不能证明字段存在。
2. **`Dsc*` 读取器不是消息定义**：TSETS 名字相同的读取器可能属于任一消息的嵌套子表
   （round34 的 `Dsc16603item_list` 就被误当成 CS 主消息）。
3. **基线产物要能被独立复算**：`fields.json` 现已具备双路径可复现性
   （`extract_fields.py` 生成 + `audit_specs_vs_fields.py` 独立审计）。
4. **改动规格必须同步改断言**：`verify_*.py` 里写死的期望值会固化错误，本轮已一并修正。

---

## 五、下一步（按真机流量排序，均已有权威规格基础）

| 命令 | 抓包次数 | 现状 | 数据源 |
|---|---|---|---|
| 16500 投资 | 730 | 空表（CS 空消息 + 尾部残留） | `config_invest.luac`（登录基金/等级基金/豪华投资/至尊投资）|
| 19400 命格 | 665 | 空表（SC 含 3 个未解子表）| `config_mingge.luac` |
| 17200 投资日期/状态 | 487 | `{day:0, status:0}` | 与 16500 同系统 |
| 16605 活动状态批查 | 441 | 空表 | 与已实现的 16603 同族 |
| 16400 成就 | 379 | 空表 | `config_chengjiu.luac`（客户端自渲染列表，空进度即真实）|

> ⚠️ 注：16500 的 `info` 子字段（`is_active/get_num/can_buy/time/charge_rmb`）
> 语义仅部分取证（`is_active==0` ⇒ 客户端显示"投资"按钮，据 `invest_level_ui` proto#12），
> 落地前需先补齐语义取证，避免出现"显示可买却买不了"的死路。
