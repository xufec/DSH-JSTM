# R99：补齐**版本握手** `10996` / `10997` —— 三个版本客户端共用同一条链路

> 任务：读三个版本的 cmd、分析对应接口、**补充修复服务端与客户端的连接互通/下发握手**。
> 结论：**三个版本的 `denglu_ctrl` 都含同一套握手命令**，而服务端**四条版本命令全都没实现**。
> **时间**：2026-09-29 23:20 – 23:55。

---

## 一、三个版本 = 三个 APK

| APK | 大小 | 版本 | 假登录版 |
|---|---|---|---|
| `anzbao\jstm.apk` | 230.5MB | **1.4.9** | `patched\jstm_fakelogin_aligned.apk` |
| `anzbao\jstm_142165.apk` | 267.8MB | **1.4.11** | `patched\jstm_1411_fakelogin_aligned.apk` |
| `anzbao\dldlJl.apk` | 135.8MB | dldlJl | `patched\dldlJl_fakelogin_aligned.apk` |

服务端的版本族判定（`ver_family_of`）本来就按 **`1110` 的 args 键数** 分流
（`n<=2 ⇒ 1.3.0`；`body<210 ⇒ 1.4.11`；否则 `1.4.9`），所以"三个版本"在服务端已有对应机制。

---

## 二、★ 三个版本的握手链路**完全一致**

用 `tools/_cmp_versions.py` 分别扫三个 APK 的协议命令号：

```
=== jstm.apk (1.4.9)     ===  game/login/denglu_ctrl.luac  [10103, 10996, 10997, 10998]
=== jstm_142165.apk (1.4.11) ===  game/login/denglu_ctrl.luac  [10103, 10996, 10997, 10998]
=== dldlJl.apk (dldlJl)  ===  game/login/denglu_ctrl.luac  [10103, 10996, 10997, 10998]
```

⇒ **三个版本共用同一套版本握手**（所以这次修复**与版本无关**，一次到位）。

### 握手链（`protocol/manual_login.md` + `denglu_ctrl` 注册表）

| cmd | 方向 | 规格 | 客户端 handler |
|---|---|---|---|
| `10001` | CS | `key:string` | （首包，服务端不回）|
| `1110` | CS→SC | `args:table` → 角色列表 | `on1110Rolelist` |
| `10102` | CS→SC | `{rid:u32, srv_id:string}` → `{code,msg,timestamp,world_lev}` | `on10102Login` |
| **`10103`** | CS→SC | 同 `10102` → `{code,msg,timestamp,world_lev}` | `on10103ReLogin` |
| **`10996`** | CS→SC | → **`cli_ver_list:table(cdn_patch:string, cli_ver:uint16)`** | **`onVersionStateList`** |
| **`10997`** | CS→SC | → **`flag:uint8`** | **`checkServerState`** |
| **`10998`** | **只 SC** | `{cli_ver:u16, flag:u16}` | **`onVersionState`** |
| `10310` | 只 SC | `{is_show:u8, msg:string}` | `on10310Offline` |
| `10396` | 只 SC | 空 | `on10396CloseClient` |
| `10111` | — | `{cli_ver:u16, flag:u16}` | **该版本客户端不注册 `10111`** |

---

## 三、★★ 服务端的实际缺口（逐条核对）

| cmd | 修复前 | 说明 |
|---|---|---|
| `10001` / `1110` / `10102` | ✓ 专用 | 早已实现 |
| **`10103`** | ✓ **已实现** | 在 `if cmd in (10102, 10103):` 里（**我第一遍用 `if cmd == 10103` 查，漏判了** —— 又一次"跨形式"）|
| **`10996`** | ❌ **0 处** | ★ **客户端在问 `cli_ver_list`，没人答** |
| **`10997`** | ❌ **0 处** | 同上（`checkServerState`）|
| `10998` | — | **只 SC ⇒ 服务端主动推送**（要求更新）⇒ **不发即正确** |
| `10310` / `10396` | — | 同上（离线提示 / 关闭客户端）|

---

## 四、`onVersionStateList` 的逻辑（反汇编 `denglu_ctrl` proto#42）

```lua
for cdn_patch, cli_ver in pairs(t.cli_ver_list) do
    if cdn_patch == PLATFORM_NAME then           -- ★ 只认「平台名」匹配的那条
        local o = { cli_ver = cli_ver, flag = … }
        self:onVersionState(o)
    end
end
```

而同文件里的文案：

> **"检测到当前游戏不是最新版本，需要重启游戏以更新至最新版本，是否立即更新？"**

⇒ **`cli_ver` 一旦与客户端本地 `getNowVersion()` 不一致，就会弹更新提示。**

---

## 五、修复（两条原则：不编造、不误导）

```python
if cmd in (10996, 10997):
    if cmd == 10996:
        out = w_u16(0)          # ★ cli_ver_list = 0 项
    else:
        out = w_u8(1)           # ★ flag = 1（服务器正常）
```

| 决定 | 理由 |
|---|---|
| `10996` 回 **空表** | `cli_ver` 是**客户端本地**的版本号（`getNowVersion`），服务端**无从得知**；填错就会触发上面那句更新提示 ⇒ 空表让客户端**遍历不到匹配项、不做版本约束**（既不卡住也不弹更新） |
| `10997` 回 `flag=1` | `checkServerState` 字面即"检查服务器状态"，同族成功约定就是 1（`14000`/`14009`/`11216`）；回 0 会让客户端以为服务器不可用 |
| `10998`/`10310`/`10396` **不发** | 它们是 **SC-only 的服务端推送**（要求更新/离线/关客户端）—— 不属于"应答"，我们不需要逼客户端更新 |

### 实测

```
SC_10996 len=2 body=0000   → cli_ver_list = 0 项（不做版本约束）
SC_10997 len=1 body=01     → flag=1（服务器正常）
```

### 门禁 E 的处置

门禁 E 的职责正是"**规格要求发的 table 若长度为 0 就必须给理由**"，于是这条空表被它抓到了。
**按纪律登记理由**（`tools/_emitted_empty_allow.json`，现共 89 条），**不是**把告警关掉：

> `10996:cli_ver_list` → "客户端遍历找 `cdn_patch==PLATFORM_NAME`，找到就调 `onVersionState`；
> 而 `cli_ver` 与客户端本地 `getNowVersion()` 不一致会弹『需要重启更新』。
> `cli_ver` 是客户端本地值、服务端无从得知 ⇒ 回空表不做版本约束。修复前是完全无应答。"

---

## 六、★ 本轮又踩了三个"自己的坑"（都记录，避免复发）

| # | 坑 | 教训 |
|---|---|---|
| 1 | 我第一遍用 **`if cmd == 10103`** 查处理器，判定 `10103` "无实现"；实际它在 **`if cmd in (10102, 10103)`** 里 | **跨形式**（`==` vs `in (...)`）的静态检查会漏判 —— 与 R86 的 `11216` 遮蔽是同一类，查代码要查**两种形式** |
| 2 | 脚本里"从通用集合移出"用了**全文** `re.sub('10996, ')`，结果**删到了自己刚插入的** `if cmd in (10996, 10997):` ⇒ 变成 `(10997)`，`10996` 永远进不去（**`ast.parse` 发现不了**）| 批量替换必须**限定作用域**（这次改成只在 `_GENERIC_DEFAULT_CMDS` 的定义体内替换）|
| 3 | 插入用的 HANDLER 尾巴**带着锚点那一行**，而 `replace(anc, HANDLER+anc[1:])` 又会补上 ⇒ 拼出 `if cmd in (10102, 10103):        if cmd in (10102, 10103):`（第 2 次同类）| **插入用的代码块不能包含锚点行**；且插入后必须**立刻 `ast.parse` + grep 双查** |

> ★ 另外还踩了一次 **PowerShell 内联 python 的引号地狱**（连续两次 `ParserError`）——
> 结论：**带引号的补丁一律写成 `.py` 文件**再跑，不要内联。

---

## 七、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **186** / 默认 58 / 未开放 22）/ CS 2463-0 / SC 静态 80+1空-0 / SC 在线 **80-80** / 专用 **69-69**（+2 = 新增 `10996`/`10997`）/ 门禁 E **PASS**（长度不符 0 / 空表告警 0，`10996` 已登记理由）|
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |
| R98 实验开关 | 已复位为 `hero_bag_limit=0`（不影响正常游玩）|

---

## 八、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `10996`/`10997` 版本握手处理器（与登录处理器相邻）|
| `tools/_cmp_versions.py` | **新增**：对比三个 APK 的握手命令 |
| `tools/_fix_r99_version_handshake.py` | 插入脚本（含三个坑的注释）|
| `tools/_fix_r99_allow_empty.py` | 把 `10996:cli_ver_list` 的理由登记进门禁 E 白名单 |
| `tools/_emitted_empty_allow.json` | 89 条已登记理由（+1）|
| `server/mock_server.py.bak_r99` | 改前备份 |
| `analysis/_denglu_ctrl.txt` | `denglu_ctrl` 反汇编（`onVersionStateList` 的真源）|
| `analysis/1.4.9/round99_version_handshake.md` | 本报告 |

---

## 九、一句话

> **三个版本的 `denglu_ctrl` 都注册了同一套握手命令 `[10103, 10996, 10997, 10998]`**，
> 而服务端 **`10996`（版本列表）与 `10997`（服务器状态）完全没实现** —— 客户端问了没人答。
> 已补齐：`10996` 回**空 `cli_ver_list`**（客户端不做版本约束，避免弹"需要重启更新"——
> 因为 `cli_ver` 是客户端本地版本号、服务端无从得知），`10997` 回 `flag=1`；
> `10998`/`10310`/`10396` 是 **SC-only 推送**，不发就是对的。
> 空表按门禁纪律**登记了理由**，不是关告警。
