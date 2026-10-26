# R85：`10303 vip_exp 越界` 的真相 —— **验证器用 1.3.0 的登录形态，却按 1.4.9 的 spec 校验**

> R84 收尾时门禁突然报 `10303 vip_exp: 越界 (off=191 len=187)`。
> 一路挖下去发现：**不是服务端 bug，是"验证器与真机不同形态"** —— 门禁一直在测 **1.3.0 的代码路径**。
> 顺带**更正 R84 对"双进程"的结论**（真凶是 **DSH 自己**在拉服务端）。
> **时间**：2026-09-29 20:50 – 21:05。

---

## 一、★★ 更正 R84 的结论：**DSH 自己会拉起服务端**

R84 我写的是"`dsh_admin.bat` 自己拉服务端，我全杀 python 把它杀了"。
进程树（`Win32_Process`）给出了**更准确**的事实：

| PID | 父进程 | 命令行 | 创建时间 |
|---|---|---|---|
| 6824 | 12392（`WmiPrvSE`，我 WMI 起的） | `python server\mock_server.py` | 20:51:50 |
| 7728 | **11088（`pwsh`）→ 父是 `node.exe`（DSH）** | `cd ...\server; python mock_server.py` | **20:51:54** |

⇒ **`dsh_admin.ps1` 只是查询 `/DSH_ADMIN/*` 的终端界面**（它自己的注释写着"须先启动服务端"），
**它不启动服务端**。真正自动拉起服务端的是 **DSH（`node.exe` 派生的 pwsh）**。

**⇒ 双进程 = 我手起一份 + DSH 自起一份。**
**纪律（更正版）**：**不要手动起/杀服务端**；确认只有 DSH 那一份；要重启用 `job_kill`，
**绝不** `Get-Process python | Stop-Process`（会连 DSH 的一起杀，然后它又拉起 ⇒ 看起来像"反复重启"）。

---

## 二、★★ `10303 vip_exp 越界` 的真相

### 2.1 先排除"构建器写错"

用**门禁自己的解析器**解析**本地构造**的 10303：

```
本地 10303 长度 = 182
解析结果: 消耗=182 len=182 err=None        ← ★ 完全吻合
顶层空表: ['skill_list', 'animate_res']
```

⇒ 构建器没问题。问题出在**活包**（187 字节）与 spec 的期望不一致。

### 2.2 真因：服务端按 `CS_1110` 的 **args 键数**判版本族

```python
def ver_family_of(body_len, args):
    n = len(args or {})
    if n <= 2:         return '1.3.0'      # ★ 键数 ≤2 ⇒ 1.3.0
    if body_len < 210: return '1.4.11'
    return '1.4.9'
```

而 `build_10303` 的尾部是**版本条件**的：

```python
if CUR_VER != '1.3.0':
    b += w_u32(vip_exp); b += w_str(jiebai_title); b += w_u8(jiebai_lev)
```

**对照（同一时刻的日志）**：

| 来源 | `CS_1110` 的 args | 判定 | 10303 尾部 |
|---|---|---|---|
| **真机 1.4.9 客户端** | **10 键**（`account, channelId, device_id, enter_srv_id, gettui_cid, idfa, platform, sign, timestamp, token`） | **1.4.9** ✓ | 发 |
| **门禁/验证器**（原先） | `struct.pack('>III', 1, 1, 1)` —— **根本不是 args 表** ⇒ `args={}` | **1.3.0** ✗ | 跳过 |

⇒ 门禁测的是 **1.3.0 的产出**，却用 **1.4.9 的 spec** 去解析
⇒ 少 4 字节（`vip_exp`）⇒ `vip_exp: 越界 (off=191 len=187)`。

### 2.3 修复：**让验证器与真机同形态**（而不是给门禁加豁免）

- `tools/audit_sc_live.py` 的 `login()` 改为发**真机同款 10 键 args**；
- **三个门禁都 `from audit_sc_live import login`** ⇒ 改一处即可（`audit_emitted_fields` / `audit_dedicated` 一并修好）；
- `tools/_login149.py` 把这份"真机形态登录"沉淀成**共享辅助**（含实测键名与判据说明）。

**效果（日志实证）**：

```
[20:59:29] << 1110 SCAccountLogin account=dsh_local roles=1
   keys=['account','channelId','device_id','enter_srv_id','gettui_cid','idfa','platform','sign','timestamp','token']
   ver=1.4.9
```

⇒ **门禁现在测的是真机那条路径**（测试保真度的实质提升，不只是"让门禁变绿"）。

### 2.4 顺带修 4 个验证脚本（★ 期间我自己又踩了一次）

按同一理由把 `verify_guaji / verify_battle_20022 / verify_20002_click / verify_level_consistency`
的登录也改成真机形态。**第一版补丁写坏了**：替换正则多吞了 `pack_frame(1110, …)`，
把整段换成裸 `_args` 发出去（**没有包头**）⇒ 4 个脚本全部 `socket.timeout`。
已修回 `pack_frame(1110, _args)`，4 个全部恢复 PASS。

> **教训**：批量正则替换**必须**在替换后**立刻跑一遍被改的脚本**；
> 语法检查（`ast.parse`）**发现不了**"发出的是裸字节"这种语义错误。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| `lint_dispatch_shadow` | **✓ 无分发遮蔽**（专用 174 / 默认 60 / 未开放 22） |
| `audit_specs_vs_fields` | 空消息 616 一致 |
| `audit_sc_conformance --generic --unsupported` | 一致 **81 / 0** / 空规格 1 |
| `audit_sc_live --unsupported` | **82 命令：一致 82 / 不一致 0**（**无 MISMATCH**） |
| `audit_dedicated` | **66 条：符合 66 / 不符 0 / 无应答 0** |
| `audit_emitted_fields` | **长度不符 0 / 顶层空表告警 0 / PASS**；`--selftest` **PASS** |
| 回归（9 项） | `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `tools/audit_sc_live.py` | `login()` 改为**真机 1.4.9 形态**（10 键 args）+ 说明 |
| `tools/_login149.py` | **新增**：共享的真机形态登录辅助（`login/q/w_str`） |
| `tools/_fix_r85_verifier_login.py` | 把 4 个验证脚本改成真机形态的脚本 |
| `tools/verify_guaji.py` 等 4 个 | 登录形态修正（并修回被我改坏的裸 `_args`） |
| `analysis/1.4.9/round85_verifier_login_shape.md` | 本报告 |

---

## 五、一句话

> **门禁报的 `10303 vip_exp 越界` 不是服务端的问题**：服务端按 `CS_1110` 的 **args 键数**判版本族，
> 而门禁发的是 `struct.pack('>III',1,1,1)`（**压根不是 args 表**）⇒ 被判成 **1.3.0** ⇒ 少发 4 字节尾部，
> 再用 **1.4.9 的 spec** 解析 ⇒ 必然越界。
> **修法是让验证器与真机同形态**（10 键 ⇒ `ver=1.4.9`），而不是给门禁加豁免 ——
> 顺带把门禁的**测试保真度**从"1.3.0 路径"提到"真机路径"。
> 另：更正 R84 —— **是 DSH 自己在拉服务端**，`dsh_admin.ps1` 只是查询界面。
