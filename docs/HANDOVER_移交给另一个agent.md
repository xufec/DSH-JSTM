# 移交文档 —— 绝世唐门 1.4.9 私服化

> **收件人**：接手本项目的另一个 AI Agent
> **目的**：让你**在最短时间内**理解现状、复用资产、避开已知的坑，并**继续推进**。
> **生成时间**：2026-09-18
> **重要**：本文所有"已验证"结论都有产出物可复核；**未验证的一律标注**，请勿当事实使用。

---

## 〇、30 秒速览

```
目标：让原版 APK（anzbao/jstm.apk，1.4.9）连上自建服务端并完整跑通
现状：登录→角色→地图→NPC对话→任务→战斗→奖励→背包/装备/仓库→商城(真扣费)/黑市→活动
      + 真实数据内容（伙伴53/邮件/活动列表/节日/排行榜）
      + ★ 协议层已"审计化"：CS 规格 & SC 应答两侧**全量零不一致**
服务端：单进程 Python（server/mock_server.py，7265 行），SQLite 11 表
★ 协议对接已实质收口 ⇒ 后续瓶颈是**玩法系统**，不是协议；优先级见 §6
```

---

## 一、绝对红线（违反即前功尽弃）

| # | 红线 | 原因 |
|---|---|---|
| 1 | **原版 APK 是最终标准** | 任何参考项目与 APK 冲突，**APK 赢** |
| 2 | **不猜协议** | 字段必须从 `cmd_resolve_*.luac` 取证；含 `D\|Dsc*\|` 未解子表的 CMD **不实现** |
| 3 | **不复制参考项目代码** | 4 个无 LICENSE + **大圣归来 GPL-3.0**；**Survive 的 `aoi.h/astar.h/wordfilter.h` 内嵌 GPLv3** |
| 4 | **不重做客户端 UI**、**不自造协议** | 我们做的是"兼容服务器"，不是"重做游戏" |
| 5 | **只操作自己的服务器** | 禁止扫描/连接第三方生产服务器 |
| 6 | **不编造数据** | 无原版依据的数值一律标"占位，待校准" |
| 7 | **先取证再改**；一次一个变量；**被否证的假设不删** | 本项目最大教训（见 §5） |

---

## 二、目录与关键资产

```
C:\Users\xu\Desktop\DSH\
├── anzbao\jstm.apk              ← ★ 目标 APK（1.4.9）
│   ├── jstm_142165.apk          ← 更高版本（355 配置表，1.4.9 是其子集，可交叉校验）
│   └── dldlJl.apk               ← 另一渠道（256 表）
├── server\                      ← ★ 服务端
│   ├── mock_server.py           ← 主服务端（7265 行）
│   ├── aoi.py / pathfind.py     ← 自研 AOI + 寻路（含 JSTM 原创 L1/L2 安全校验）
│   ├── power.py                 ← 战力引擎（原版 AttrPower 权重）
│   ├── battle.py                ← 战斗（回合制）
│   ├── quest_spawn.py           ← 任务刷怪
│   ├── world\                   ← P1 骨架（ticker/五层容器）+ jstm_bridge.py（dormant）
│   ├── config.json              ← 运行配置（★ 很多数值在这里，未落库）
│   ├── map_block.json           ← 碰撞数据（26/124 场景）
│   ├── item_config.json         ← 3535 物品
│   ├── mission_config.json      ← 846 任务
│   ├── item_gift.json / mall_config.json / _attr_data.json / _skill_raw.json
│   ├── state\roles.db           ← ★ SQLite（11 表 / 98 列）
│   └── logs\                    ← tcp.log / http.log / server.log / server_stderr.log
├── protocol\fields.json         ← ★ 3553 条协议定义（唯一真源候选）
├── analysis\                    ← 全部分析报告
│   ├── server_reference\        ← 五项目审计（43 份 .md）
│   ├── jstm_1.4.9\              ← ★ JSTM 协议文档（16 份）
│   └── 1.4.9\                   ← 逆向过程记录（117 份）
├── tools\                       ← 200+ 脚本（见 §3）
├── cankao\                      ← 5 个参考项目 ZIP（Survive/CXEngine=YZXY/大圣/侠客行/空空西游）
├── patched\                     ← 打补丁后的 APK + keystore
└── docs\                        ← 本批文档
```

---

## 三、★ 必会的工具（`tools/`）

| 工具 | 用途 | 用法 |
|---|---|---|
| `luajit_bc.py` | 解析 LuaJIT 2.0 字节码 | 库 |
| `luajit_dis.py` | 反汇编（`OPS` **是 list**，`OPS[w&0xff]`） | 库 |
| `show_cmd.py` | **看某 CMD 的权威字段定义** | `python tools/show_cmd.py 10304` |
| `dsc_spec.py` | 展开 `D\|Dsc*\|` 未解子表 | `python tools/dsc_spec.py --file 200` |
| `proto_spec.py` | 读协议规格 | — |
| `extract_config.py` | **通用配置表读取器**（347 表） | `python tools/extract_config.py peek config_skill 5` |
| `extract_config_mapblock.py` | 提取碰撞数据 | — |
| `patch_fake_login.py` | 给 APK 打探针（注入 `dsh_fake_login.lua`） | 见 §4.2 |
| `bench_server.py` / `prof_server.py` | 性能基准 | — |
| `test_*.py` | 各类回归测试 | — |

**★★ 协议审计 / 验证工具（round35–42 新建 —— 改协议前**必跑**）**

| 工具 | 用途 | 用法 |
|---|---|---|
| `audit_specs_vs_fields.py` | **CS 规格第二路径审计**（AutoConstruct 调用点独立还原 vs `fields.json`） | `python tools/audit_specs_vs_fields.py` |
| `audit_sc_conformance.py` | SC 默认应答**静态**一致性（全量 1635 条 / `--generic` / `--unsupported`） | `python tools/audit_sc_conformance.py --generic --unsupported` |
| `audit_sc_live.py` | SC 应答**在线**复核（走 TCP 真解析） | `python tools/audit_sc_live.py --unsupported` |
| **`audit_dedicated.py`** | ★ **专用 handler 查询型审计** —— 补"另两道审计都覆盖不到"的盲区（真机没发过 + 走专用分支）；R43 的 `10306` 就藏在这里 | `python tools/audit_dedicated.py` |
| `replay_captures.py` | **真机流量回放**（341 抓包；`--per-cmd N` 取多变体） | `python tools/replay_captures.py --per-cmd 5` |
| `triage_gaps.py` | 把"有 SC 却无应答"按**客户端是否注册处理器**分类 | `python tools/triage_gaps.py --json <回放JSON>` |
| `resolve_dsc_refs.py` | 以 **reader 原型**为准重建 `Dsc*` + 展开 `D\|X\|` | `python tools/resolve_dsc_refs.py --apply` |
| `gen_attr_meta.py` | 生成 64 项属性元数据 + 与 `role_attr` 的差异清单 | `python tools/gen_attr_meta.py` |
| `verify_rank.py` / `verify_13402.py` / `verify_attr_power.py` / `verify_account.py` / `verify_10924.py` / `verify_16603.py` / `verify_11215_10800.py` | 各功能**逐字节规格验证** | `python tools/verify_rank.py` |
| `_field_use.py` / `_bid_flag_map.py` | 字段读取点定位 / bid↔活动开关映射 | `python tools/_field_use.py <luac> <field>` |

> ⚠ **改协议相关代码后，最少跑**：`audit_sc_conformance.py --generic --unsupported`
> （静态）+ **`audit_dedicated.py`**（专用 handler 查询）+ `replay_captures.py`（真机回放）。
> 三者口径必须都归零。**新写专用 handler 时尤其要跑 `audit_dedicated.py`**。

**★ 反汇编速查（血泪换来的）**：
```
KSTR/GGET/GSET → kidx(pt, (w>>16)&0xffff)
TGETS/TSETS    → kidx(pt, (w>>16)&0xff)
KSHORT         → 值 = (w>>16)&0xffff
OPS 是 list，只能 OPS[w&0xff]，不能 .get()
TSETS A, C     ⇒ R(A-1)[K[C]] = R(A)      ← 由 npc_ctrl proto[84] 定义块定标
ISNEN A, D     ⇒ D 是**常量表索引**，必须读 knum[D]（不是值！）
```

---

## 四、构建 / 部署 / 调试

### 4.1 启动服务端
```powershell
python server/mock_server.py
# TCP 9000（游戏） / HTTP 8080（管理 + 探针上报）
```

### 4.2 改客户端（探针注入）完整链
```powershell
# 1) 写/改探针
server/dsh_fake_login.lua          # 注入到客户端的 Lua 探针
# 2) 语法门禁（★ 必须过，它能拦住 `...` vararg 之类的错）
node tools/lua-check/check.js server/dsh_fake_login.lua
# 3) 打补丁
python tools/patch_fake_login.py anzbao/jstm.apk patched/jstm_fakelogin_raw.apk `
       --base http://10.0.2.2:8080 --lua server/dsh_fake_login.lua
# 4) 对齐 + 签名
$bt='D:\Android\SDK\build-tools\34.0.0'
& "$bt\zipalign.exe" -f -p 4 patched\jstm_fakelogin_raw.apk patched\jstm_fakelogin_aligned.apk
& "$bt\apksigner.bat" sign --ks patched\dsh.keystore --ks-pass pass:123456 `
    --ks-key-alias dsh --key-pass pass:123456 patched\jstm_fakelogin_aligned.apk
# 5) 安装 + 跑
adb connect 127.0.0.1:16384
adb -s 127.0.0.1:16384 install -r -d patched\jstm_fakelogin.apk
adb -s 127.0.0.1:16384 shell am force-stop com.shiyue.dldl.ewan.qihoo
adb -s 127.0.0.1:16384 shell am start -n com.shiyue.dldl.ewan.qihoo/org.cocos2dx.lua.AppActivity
Start-Sleep 65
adb -s 127.0.0.1:16384 shell input tap 2200 84     # ★ 只点一次（取消键）
Start-Sleep 90
# 6) 取数
Select-String -Path server/logs/http.log -Pattern 't=xxx'
```

### 4.3 调试要点
- **探针上报格式**：`http.log` 里 `...&t=<type>&v=<value>`
- **管理接口**：`http://127.0.0.1:8080/DSH_ADMIN/status`（还有 `/aoi` `/power` `/cfg` `/giveitem` …）
- **★ 端口约定**：调试用**备用端口**（如 8099/9099），**别动在线的 9000**
- **★ DB 安全**：测试前读原值、测后恢复（避免污染玩家数据）

---

## 五、★ 已知的坑（务必先读）

### 5.1 协议层
| 坑 | 说明 |
|---|---|
| **`code == 1` 才是成功** | 回 0 会走 `message(msg)`；`msg` 为空 ⇒ **空白框** |
| **`10500/10501/10503` 是推送型**，`10502` 是请求-应答型 | 主动推 `10502` 会被忽略 |
| **`SC_14101` 必须带 `assets`/`items`** | 少发 ⇒ 客户端"领不了"（虽然 code 对） |
| **下发的 ID 必须校验存在性** | ★ 曾发无效技能 bid `1001` ⇒ **客户端崩溃**（NPC 对话失败 13 轮！） |
| ~~含 `D\|Dsc*\|` 的 CMD~~ | ✅ **该纪律已可解除**：round38 起 `fields.json` 的子结构引用已**全部展开**（`resolve_dsc_refs.py`，346 处），不再有"未解子表" |

**★ round34–42 新增的协议层坑（都真实踩过）**

| 坑 | 说明 |
|---|---|
| **客户端 CS 尾部有 4 字节缓冲区残留** | `16500` 空消息发 4 字节、`16603` 单字段发 8 字节…⇒ 服务端只读规格前 N 字节 |
| **包长是弱证据，不能反推字段数** | `{bid}` 与 `{bid,num}` 对 8 字节**都"对得上"** ⇒ round34 据此误订正 `CS_16603` |
| **规格来源优先级** | `AutoConstruct spec` > reader 原型 > **抓包长度**（最弱，别当铁证） |
| **`Dsc*` 段曾被反转** | `fields.json` 的 `Dsc*` 顺序是反的（类型随之错位）⇒ 以 **reader 原型**为准 |
| **同族协议条目结构不一致** | `12901/12902/12911/12912` 榜单项有 `career:u16`，**`12931` 没有** ⇒ 别抽通用头部 |
| **分发顺序：靠前分支遮蔽靠后分支** | `round39` 把排行榜并入通用集合 ⇒ `round40` 的专用实现**根本不执行**（返回全零）。**新增专用实现必须同时从通用集合移出** |
| **CS-only 消息不能回包** | `10999` 协议里**没有 SC 定义** ⇒ 回空帧会把客户端推进未知分支（同 `10001`） |
| **审计工具会"表示过时"** | 产物一变（引用展开 / 应答带 `msg`），审计仍按旧表示算 ⇒ 冒出成批**假阳性**；**两个审计矛盾时先怀疑检查器** |

### 5.2 数据层
| 坑 | 说明 |
|---|---|
| **`config.json` vs DB** | 很多数值（skills/heros/sign_*/moneytree_*）**在 config.json，未落库** |
| **`role_attr` 设计缺陷** | `AttrLen=64` 但只落 25 列（**混存 21 个派生项 + 漏 39 个属性**） |
| **无账号/会话层** | `1110` 的角色列表来自 `config.json`，**不查 roles 表** |
| **无效 bid** | 必须用 `is_valid_item()` 过滤（旧表仅 1117 条，现 3535 条） |

### 5.3 客户端侧（服务端修不了）
| 坑 | 说明 |
|---|---|
| **`setSceneInfo` 写 R1 读 R0** | 客户端寄存器错位 ⇒ `self.scene_info` 永为 nil |
| **`on14101` 读 `resp.assets/items`** | 字段缺失 ⇒ 静默不显示 |
| **`advance_new_panel` 读 `RoleVo.power[1].val`** | ⚠️ 综合战力**至今未闭环**（见 §6） |

### 5.4 工程层
| 坑 | 说明 |
|---|---|
| **`.get(k, default)` 对 None 无效** | "存在但值为 None" 会返回 None ⇒ `int(None)` 崩 |
| **同一文件并发编辑** | 会互相覆盖 ⇒ **同一时间只由一人编辑** |
| **`.ps1` 必须 UTF-8 带 BOM** | 且用 `powershell.exe -File`（5.1）验证 |
| **PowerShell 的 `"$var: "`** | `:` 被当驱动器引用 ⇒ 写 `"${var}: "` |
| **`TcpHandler.cfg` 是类属性** | 全连接共享 ⇒ 真机多角色验证受阻（R45 已用**实例级 cfg 副本**解决） |

### 5.5 ★★ 真机共存纪律（都是踩过之后立的规矩）

> 本项目的调试对象是**真机上正在玩的玩家**，不是离线测试环境。
> 下面每一条都对应一次真实事故或险些发生的事故。

| # | 纪律 | 起因 |
|---|---|---|
| 1 | **不要在客户端处于"面板已打开 / 正在等应答"时重启服务端** | R48：客户端停在日常面板等回包时重启 ⇒ **客户端 ANR 卡死**（`绝世唐门没有响应`，不会自动消失）。恢复方式：`am force-stop` + 重新拉起 + 点"进入游戏"。**安全窗口 = 客户端只有心跳（长时间无 `cmd=` 业务包）时** |
| 2 | **不要为了"回到干净状态"而还原 `server/state/roles.db`** | 还原点是**开发期**用的；一旦有真机玩家，还原会**毁掉玩家进度** |
| 3 | **不要在有玩家时跑 `replay_captures.py`** | 它会回放 876 个真实变体（含购买/领取/移动），**会真扣费、真发货**。协议审计改用三道**无副作用**工具：`audit_specs_vs_fields.py` / `audit_sc_conformance.py` / `audit_sc_live.py` |
| 4 | **测试数据只写测试账号**（如 `r45_test`/`r47_test`），结束即清理 | 避免污染玩家账号（`dsh_local`/rid=1001） |
| 5 | **重启前先看一眼 `server/logs/tcp.log` 尾部** | 判断客户端是否空闲；这一步 3 秒，能避免上面第 1 条 |

### 5.6 ★ 真机取数：用 adb 主动驱动 MuMu（R48 首次实践）

被动等抓包很慢；**直接驱动模拟器点开面板**可以立刻拿到该面板的协议流量：

```powershell
$adb = 'D:\ADB\platform-tools\adb.exe'
& $adb connect 127.0.0.1:7555          # 与 emulator-5554 是同一实例
& $adb -s 127.0.0.1:7555 exec-out screencap -p > shots/now.png     # 2560x1440 横屏
& $adb -s 127.0.0.1:7555 shell input tap X Y
# 用 see_image 读截图定位按钮；随后看 server/logs/tcp.log 新增的 cmd 即可
```

**要点**：
- 截屏是 **2560×1440 横屏**（`wm size` 报的 1440×2560 是物理值，别搞反）；
- `locate_in_image` 工具曾报 `loadImage is not defined` ⇒ 改用 **PIL 裁剪 + `see_image` 估坐标**；
- 点开面板后，**以"服务端是否收到该 cmd"** 作为"面板真的打开了"的判据（比看截图可靠）；
- 游戏包名：`com.shiyue.dldl.ewan.qihoo`。

---

## 六、★ 下一步优先级（建议）

### P0（阻塞"真实感"的最关键项）

| # | 任务 | 起点 | 难点 |
|---|---|---|---|
| **1** | **综合战力显示闭环** | 面板读 `RoleVo.power[1].val`；`10304`/`20100` 已实现但**未被采用** | 需找到**写 `RoleVo.power` 的那条"角色属性同步消息"**（运行时探针已证明从无消息写入） |
| **2** | **属性表重构** | `AttrLen=64`（`server/_attr_data.json`）；现 `role_attr` 25 列混存 | 按 **Survive 三条铁律**：只存输入项 + 变更发信号重算 + 可见性白名单（`AttrKeyIsShow` 配置**已存在**） |

### P1

| # | 任务 | 说明 |
|---|---|---|
| 3 | 限时任务 | `missions` 表补 `show_lave_time`/`lave_time`（`Config.Mission.time_limit` 存在） |
| 4 | 招募奖励 | 协议**未定位**（可能在 hero/活动模块） |
| 5 | 碰撞数据补全 | 90/124 场景无数据；`4` 语义未知（仅 7 格） |
| 6 | 限流标定 | `MoveRateLimiter` 默认 12 格/秒**是拍的**，现已有 **387 个真实 10204 坐标**可算阈值 |

### ★ P1′（round39–42 新增：把"零值/未开放"升级为真实玩法）

> **背景**：协议对接已收口（见 §〇）。剩下的都是有**真实缺口**但需要玩法系统支撑的项。
> `tools/replay_captures.py` 回放报告里的 GAP 现仅 8 条（客户端无处理器，无害），
> 真正该看的是**当前回零值/回来开放**的那些命令。

| # | 任务 | 起点 |
|---|---|---|
| A | **副本 / 爬塔进度** | `13005/13034/13036/13045/13052/13058`、`21301` 现回零值；需副本进度系统（可扩展 `missions` 表） |
| B | **NPC 交互** | `15200/15204/15400`（`17001` 已回真实 `max_gate`）；`config_npc`/`map_npc` 已在手 |
| C | **社交 / 聊天** | `12762` 聊天、`13342/13343/13359` 社交圈（现回"未开放"） |
| D | **大玩法** | 宗门战 `17501`、竞速 `17301/17312`、婚宴 `18300`、跨服 `18600/19500` —— 需成体系实现 |
| E | **剩余 3 个排行榜** | `12902/12911/12912` 现回空榜（榜名是资源 id、资源清单非 LuaJIT 格式 ⇒ 指标未取证）；若解出榜名即可按 `12901` 的模式补真实 `val` |

### P2

| # | 任务 | 说明 |
|---|---|---|
| 7 | 账号/会话层 | 目前完全不存在（无 password/token/account 表） |
| 8 | `world/` 桥接层激活 | `config.json` 加 `world_bridge_enabled:true` + 4 行 attach |
| 9 | 怪物/NPC 移动 | 未接线（A\* 已就绪） |
| 10 | 探针瘦身 | 某条上报累计数千次 |
| 11 | **`mock_server.py` 拆分** | **7265 行**已达维护上限；round42 抽 `shop_try_buy()` 是正确方向（三处购买入口共用一处实现） |

---

## 七、★ 前 30 分钟建议动作

```powershell
cd C:\Users\xu\Desktop\DSH
# 1) 确认服务端健康
Get-NetTCPConnection -State Listen -LocalPort 8080,9000
python -c "import ast; ast.parse(open(r'server/mock_server.py',encoding='utf-8').read()); print('OK')"
# 2) 看当前实现了哪些命令
python -c "
import re; src=open(r'server\mock_server.py',encoding='utf-8').read()
s=set()
for m in re.finditer(r'if cmd (?:==|in) \(?(\d{4,5})', src): s.add(int(m.group(1)))
print(sorted(s))"
# 3) 读这两份，理解协议与真机行为
#    analysis/jstm_1.4.9/protocol_index.md
#    analysis/server_reference/FINAL_SERVER_ARCHITECTURE.md
# 4) 读最近的实施记录（★ 按时间从新到旧）
#    analysis/1.4.9/round41_unsupported_actions.md（协议收口：GAP 34→8）
#    analysis/1.4.9/round40_rank.md              （排行榜真实数据）
#    analysis/1.4.9/round38_resolve_refs.md      （规格自洽化）
#    analysis/1.4.9/round37_replay_audit.md      （回放抓到 6 个编码 bug）
#    analysis/1.4.9/npc_dialog_round14_FIXED.md  （历史最大突破）
# 5) ★ 跑一遍协议审计，确认基线是"绿"的（改协议前必跑，见 §3）
python tools/audit_specs_vs_fields.py            # CS 规格：应 2463 一致 / 0 不一致
python tools/audit_sc_conformance.py --generic --unsupported   # SC 静态：应 0 不一致
python tools/audit_sc_live.py --unsupported      # SC 在线：应全一致
python tools/audit_dedicated.py                  # 专用 handler 查询：应 58/58（新写 handler 后必跑）
# （replay_captures.py 会真实触发购买/领取 ⇒ 有真机玩家在玩时**不要**跑）
# 5) 若要改客户端：先跑 tools/lua-check/check.js 门禁
```

---

## 八、★ 你被期望延续的工作方式

1. **先取证再改**：任何改动前先 `show_cmd.py` / 反汇编 / 真机日志确认
2. **一次一个变量**：便于回归定位
3. **结论分级**：【已确认】【已验证】【待验证】【未知】
4. **被否证的假设保留记录**（本项目 docs 里有 20+ 处自我更正，**不要删**）
5. **每轮产出报告**到 `analysis/1.4.9/roundN_xxx.md`
6. **不编造**：无依据的数值标"占位"
7. **改服务端前备份**（本项目习惯：`*.bak_<阶段>`）
8. **★ 改协议相关代码后必须跑审计**（见 §3）：
   `audit_sc_conformance.py --generic --unsupported` + `replay_captures.py`
   —— 两者口径必须都归零；**有真机玩家在玩时不要跑 `replay_captures.py`**（它会真扣费/发货）
9. **★ 新增专用实现时，同时把它从通用集合（`_GENERIC_DEFAULT_CMDS` / `_UNSUPPORTED_ACTION_CMDS`）移出**
   —— 否则靠前的通用分支会**遮蔽**它（round40 已踩）

---

## 九、参考文档索引（按重要性）

| 文档 | 内容 |
|---|---|
| `analysis/jstm_1.4.9/protocol_index.md` | ★ 协议总索引（3553 定义 / 已知 1634 CMD / 已实现 / 未应答） |
| `analysis/jstm_1.4.9/*_protocol.md` | 14 份领域协议（login/role/scene/task/battle/inventory/...） |
| `analysis/server_reference/FINAL_SERVER_ARCHITECTURE.md` | ★ R4 架构定稿（含前提裁决、自我更正） |
| `analysis/server_reference/R1_SUPPLEMENT.md` | R1 补全（五项目逐文件审计 + 5 处自我更正） |
| `analysis/server_reference/yzxy/jstm_battle_fields.md` | ★ 战斗字段权威表（`magic_list` = buff 载体） |
| `analysis/server_reference/comparison/*_matrix.md` | 五项目 × JSTM 映射矩阵（task/battle/role/database/architecture） |
| `analysis/server_reference/kongkongxiyou/jstm_blueprint.md` | 可实施蓝图（场景骨架 + 工程范式） |
| `analysis/1.4.9/npc_dialog_round14_FIXED.md` | ★ 13 轮谜题的最终根因与修复 |
| **`analysis/1.4.9/round37_replay_audit.md`** | ★★ **真机流量回放**：抓到 6 个服务端编码 bug |
| **`analysis/1.4.9/round38_resolve_refs.md`** | ★★ 规格自洽化（`Dsc*` 重建 + 346 处引用展开） |
| **`analysis/1.4.9/round39_gap_triage.md`** | ★★ GAP 分类（73→34）与"查询型批量诚实应答" |
| **`analysis/1.4.9/round40_rank.md`** | 排行榜真实数据（含"分发顺序遮蔽"与"同族结构不一致"两坑） |
| **`analysis/1.4.9/round41_unsupported_actions.md`** | ★★ 协议收口（GAP 34→8）+ 审计工具缺陷复盘 |
| **`analysis/1.4.9/round42_shop_buy.md`** | ★★ 真实购买收口（`shop_try_buy()` 共用内核）+ **运维注意：有真机玩家时别还原 DB / 别跑回放** |
| `analysis/1.4.9/round31~33_*.md` | 商城 / 伙伴 / 活动列表 的真实数据对接 |
| `docs/TECHNICAL_技术文档.md` | 本批技术文档（★ 含"4 字节缓冲区残留"与四道审计） |
| `docs/ARCHITECTURE_架构及分析.md` | 本批架构分析 |
| `docs/SUMMARY_私服化总结.md` | 本批总结（方向/优缺点/挫折） |

---

## 十、一句话交接

> **本项目最大的资产不是代码，而是"3553 条协议定义 + 347 张配置表 + 四道可重复执行的协议审计 + 全量零不一致"。**
> **最大的风险是"以为某结论已验证，其实是推测"** —— 请务必复核分级标注，
> 并在改协议前跑 §3 的三条审计命令。
>
> **★ 协议对接已收口**（CS 规格 / SC 应答两侧零不一致，应答缺口仅剩 8 条且均无害）；
> 接下来的实质工作是**玩法系统**（副本/社交/宗门/竞速），推进清单见 §6 P1′。
