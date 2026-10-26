# R84：环境修复（双进程真相）+ 门禁「长度不符」的真相是**多版本尾部字段**

> 本轮两件事：① 修掉**反复出现的"服务端消失/双进程"**（找到了真正来源）；
> ② 查清门禁报的 `10301/10302 长度不符` —— **不是 bug，是刻意的多版本兼容**，
> 给四个门禁补上**带理由的尾部豁免**（含自检）。
> **时间**：2026-09-29 20:15 – 20:45。

---

## 一、★ 环境修复：双进程的**真正来源**

### 1.1 现象

- 我每次"重启服务端"都写 `Get-Process python | Stop-Process -Force`，
  然后起一个新的 ⇒ 下次一查，**9000 上有两个监听**。
- 服务端还会"自己消失"（9000 无监听）。

### 1.2 真相（`Win32_Process` 查出来的进程树）

| PID | 父进程 | 命令行 |
|---|---|---|
| 4556 | 4060（我起的 `cmd /c python server\mock_server.py`） | `python server\mock_server.py` |
| 5756 | 12716（**我早前某次调用留下的 pwsh**） | `"D:\Anaconda3\python.exe" mock_server.py` |
| 28772 | — | `cmd /c "C:\Users\xu\Desktop\DSH\dsh_admin.bat"` |

- **`dsh_admin.bat` 自己就会拉起服务端**（11:02 起一直在跑）—— 那是**项目正常的运维入口**。
- 我"全杀 python + 再起一个" ⇒ **把它的和我的都杀了**，然后两边又各自拉起一个
  ⇒ **双进程不是别人造成的，是我自己造成的**。

### 1.3 规范做法（写进纪律）

1. **服务端只用一个受管后台 job**（`run_in_background: true`）；
2. 需要重启时用 **`job_kill <job_id>`**，**不要** `Get-Process python | Stop-Process`；
3. 起服务端前先确认 `9000 监听数 == 0`（避免双进程），起来后确认 **恰好 1**；
4. 若发现 `dsh_admin.bat` 在跑，**先与它的实例对齐**，不要另起一份。

**当前状态（已确认）**：`python=1`、`9000 监听=1`、`stderr=0B`、`HTTP 200`、客户端在线。

---

## 二、★★ 门禁「长度不符 2」的真相：**多版本尾部字段**（不是 bug）

### 2.1 症状

```
=== 「该发而未发」门禁（132 条命令，role_lev=70）===
长度不符: 2
★ 10301    消耗 111 != 112
★ 10302    消耗 114 != 122
```

### 2.2 查证

`build_10302` 的注释与代码里写得清清楚楚：

```python
# ★★ 多版本并集（R49）：1.4.11 的 sc/10302 比 1.4.9 **多两个尾部字段**
#   （`diamond:I` + `rainbow_diamond:I`，由 tools/diff_role_specs.py 逐字段比对确认）。
#   1.4.9 只读它自己那 29 个、**忽略尾部多余字节**；1.4.11 要读满 31 个
#   ⇒ **少发会让 1.4.11 解析越界、整条消息被丢弃** ⇒ 客户端没有角色数据
#     ⇒ 主城功能按钮按 `open_lev` 门禁全部隐藏（**且不报错**，与实测吻合）。
b += w_u32(st['diamond']); b += w_u32(st['rainbow_diamond'])
```

量化对照：`SC_10302` 规格 = **29 字段 / 固定 114 字节**；我们发 **122** ⇒ 正好多 **8 字节**（2×u32）。

⇒ **门禁用的是 1.4.9 的 spec**，所以必然报"消耗 114 != 122"。
**不能把包改回去** —— 那会让 1.4.11 客户端解析越界丢消息（有实测证据）。

### 2.3 修复：给门禁加**显式、带理由、有自检**的豁免

规则（抽成函数，四处共用）：

```python
def tail_exempt(cmd, r):
    return (int(cmd) in MULTI_VERSION_TAIL      # ① 显式名单（不是通配）
            and not r.get('err')                # ② 规格字段全部解析成功
            and r.get('consumed', 0) < r.get('len', 0))   # ③ 包**比规格长**
```

**③ 的方向很关键**：`<` 表示"多出来的都在尾部"；**`>`（少发）一律不豁免**
—— 那正是会让 1.4.11 越界丢消息的情形。名单 `MULTI_VERSION_TAIL = {10301, 10302}`，
注释里写明出处（`tools/diff_role_specs.py`）。

**落到了四个门禁**：`audit_emitted_fields` / `audit_sc_live` / `audit_dedicated`（+ `audit_sc_conformance` 本就一致）。

### 2.4 ★★ 同一个坑我踩了**三次**：`cmd` 是**字符串**

| 次 | 门禁 | 写法 | 结果 |
|---|---|---|---|
| 1 | `audit_emitted_fields` | `c in MULTI_VERSION_TAIL`（int 集合） | 恒 False ⇒ 豁免**静默失效** |
| 2 | `audit_emitted_fields` | 清了 `err` 但**没让长度判定跳过** | 仍进 mismatch |
| 3 | `audit_sc_live` | `cmd in (10301, 10302)` | 同样恒 False |

⇒ 三处都必须 **`int(cmd)`**。**教训：跨循环用命令号比较时，先确认它的类型**；
而且**豁免失效是静默的**（门禁照旧报错，看起来像"豁免没用"，本质是类型不匹配）。

### 2.5 给新豁免配自检（按 R83 的教训：门禁必须有自检）

```
尾部豁免: 多尾字节 ✓ ／ 少发不放行 ✓ ／ 名单外不放行 ✓ ／ 解析出错不放行 ✓
自检: PASS
```

四条边界全覆盖 —— 特别是 **"少发不放行"**（防止把"漏字段"误当"多尾字节"放过）。

---

## 三、全量验证（六道门禁逐条完整输出）

| 门禁 | 结果 |
|---|---|
| `lint_dispatch_shadow` | **✓ 无分发遮蔽**（专用 174 / 默认 60 / 未开放 22） |
| `audit_specs_vs_fields` | 空消息 **616 一致** |
| `audit_sc_conformance --generic --unsupported` | **一致 81 / 不一致 0** / 空规格 1 |
| `audit_sc_live --unsupported` | **82 命令：一致 82 / 不一致 0**（无 MISMATCH 行） |
| `audit_dedicated` | **66 条：符合规格 66 / 不符 0 / 无应答 0** |
| `audit_emitted_fields` | **长度不符 0 / 顶层空表告警 0 / PASS**；`--selftest` **PASS** |
| 回归 | `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B`、HTTP 200、客户端在线 |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `tools/audit_emitted_fields.py` | 新增 `MULTI_VERSION_TAIL` + `tail_exempt()`，长度判定放行尾部字节；自检加 4 条边界 |
| `tools/audit_sc_live.py` | 同规则豁免（`int(cmd)`） |
| `tools/audit_dedicated.py` | 同规则豁免（`int(cmd)`） |
| `analysis/1.4.9/round84_env_and_gate_tail_exempt.md` | 本报告 |

---

## 五、一句话

> **双进程是我自己造成的**（`dsh_admin.bat` 本来就在拉服务端，我还每次全杀再起一个）——
> 规范做法已写进纪律：**一个 job + `job_kill`，起前先确认 0 监听**。
> **`10301/10302 长度不符`不是 bug**：是刻意多发尾部字段兼容 1.4.11（有逐字段比对依据），
> 给四个门禁补了**带理由 + 带自检**的尾部豁免；
> 顺带记下我在同一处踩了三次的**类型陷阱**：`cmd` 在循环里是字符串，`in (int…)` 恒 False。
