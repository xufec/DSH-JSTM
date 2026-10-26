# 绝世唐门 1.4.9 私服 —— Phase E：角色经验与升级机制 · 状态报告

> **目标 APK**：`anzbao/jstm.apk`
> 包名 `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 本轮结论**只以 1.4.9 为准**；1.4.11 未参与任何判定。
> 环境：`server/mock_server.py`（TCP 9000 / HTTP 8080）+ 探针版 1.4.9 APK，模拟器 `127.0.0.1:16384`。

---

## 一、结论：升级闭环**已在真机跑通**（客户端真实行为驱动）

用户给定的目标链，逐环实测：

| # | 目标链环节 | 结果 | 证据 |
|---|---|---|---|
| 1 | 任务奖励 / 战斗奖励 | ✅ | `20:22:13 >> cmd=12403`（真实客户端提交任务 10010） |
| 2 | 获得经验 | ✅ | `** mission 10010 committed: +500 exp, +1290 coin` |
| 3 | **experience 增加** | ✅ | 布置起点 exp=3773 → +500 = 4273 |
| 4 | **检查升级所需经验** | ✅ | 用**原版等级表**：`RoleAttr[8].exp_max = 3873` |
| 5 | **达到阈值 → level +1** | ✅ | `** LEVEL UP role 1001: 7 -> 8 (升 1 级), exp 余 400` |
| 6 | **计算升级后属性** | ✅（**`IMPLEMENTATION_FALLBACK`**） | `level attr growth x1: atk_s 777→789, hp_max 4321→4381` |
| 7 | **更新角色状态** | ✅ | DB `roles.level=8, exp=400`；`role_attr.atk_s=789` |
| 8 | **通知客户端** | ✅ | `<< 10302 (refresh after commit) lev=8 exp=400` + `<< 10301/10303` |
| 9 | **经验条 / 等级刷新** | ✅（**数据层**）<br>⚠️（像素层） | 客户端**自己解出** `lev=8 / exp=400 / exp_max=4342`（§2.8，探针 `roleH`），分母与原版表一致 ⇒ 经验条应按 400/4342≈9.2% 渲染。**但未取得可靠的像素级截图**（见 §七 第 1 项） |
| 10 | 触发升级事件 → 任务/系统检查 | ✅ | 升级后紧接着推送 `12405`（任务列表刷新） |
| 11 | **持久化** | ✅ | SQLite `roles` / `role_attr` / `role_assets` 三表落库 |
| 12 | 重新登录仍保持 | ✅ | 脚本断言「重新读取等级保持 11」（见自测） |

**关键点**：这次升级**不是脚本伪造的**，而是一台**真实客户端**登录 → 请求 10301 → 移动 →
提交任务 10010 → 服务器发经验 → 用原版等级表判定升级 → 回推 10302/10301/10303。
原始帧序列（`server/logs/tcp.log`）：

```
20:21:59  >> cmd=10103 RoleReLogin     ... 客户端重连
20:21:59  >> cmd=10300 RoleInit        ... 初始化完毕
20:21:59  >> cmd=10301 角色基础信息     ... 客户端主动请求
20:21:59  << 10301 SC_10301 role info
20:22:01  >> cmd=10204 角色移动
20:22:13  >> cmd=12403                 ... 提交任务 10010
20:22:13  ** mission 10010 committed: +500 exp
20:22:13  ** LEVEL UP role 1001: 7 -> 8 (升 1 级), exp 余 400, 下一级需 4342
20:22:13  << 10302 (refresh after commit) lev=8 exp=400
20:22:13  << 10301/10303 (refresh after commit)
```

---

## 二、★ 本轮最重要的发现

### 2.1 经验表**在客户端**，而且**完整可恢复**

`Config.RoleAttr`（`assets/src/config/config_role_attr.luac`）：

| 项 | 值 |
|---|---|
| 条目数 | **200**（键 1..200）⇒ **等级上限 200** |
| 每级字段 | `exp_total` / `exp_max` / `attr_point` / `sinew_add` / `sinew_max`（**全表统一 5 个**） |
| 前 5 级 `exp_max` | 240 / 481 / 971 / 2452 / 2749 |
| 单调性 | `exp_max` 与 `exp_total` **均单调不减** |
| 递推 | `exp_total[L] = exp_total[L-1] + exp_max[L]`（**除 L=2**，见 §六） |

### 2.2 ★ 客户端取的是 `RoleAttr[lev + 1].exp_max`（**决定服务端必须怎么算**）

`assets/src/game/main/main_ui.luac` proto#16 `changeExp` 前 6 条字节码：

```
0  GGET    A=1 D=0     ; Config
1  TGETS   A=1 B=1 C=1 ; ['RoleAttr']
2  TGETS   A=2 B=0 C=2 ; ['role']
3  TGETS   A=2 B=2 C=3 ; ['lev']
4  ADDVN   A=2 D=512   ; lev + 1        ← ★ 注意 +1
5  TGETV   A=1 D=258   ; Config.RoleAttr[lev + 1]
...
13 TGETS   A=3 B=1 C=7 ; ['exp_max']     ← ★ 经验条分母
14 DIVVV                ; role.exp / exp_max
15 TGETS   A=3 B=0 C=8 ; ['expFull']
16 MULVV                ; * expFull
```

⇒ **处于 L 级时，经验条分母 = `RoleAttr[L+1].exp_max`**
⇒ 服务端升级阈值**必须用同一个值**，否则"服务端认为升级了、经验条却显示异常"。

**本项目服务端已按此实现**（`server/mock_server.py` 的 `level_need(lev)`）。

### 2.3 `SC_10301` **本身就带经验字段**（此前服务端发的是写死的 100）

`python tools/proto_spec.py cmds 10301` 的权威字段（节选）：

```
... exp_max:uint32, exp_total_nextlev:uint32, attr_point:uint16, profit_exp:uint32 ...
```

而 `server/mock_server.py` 原先在 `ROLE_DEFAULTS` 里写死
`'exp_max': 100, 'exp_total_nextlev': 100` —— **是错的**（与客户端表对不上）。

**已修**：`role_state()` 现在实时按原版等级表算：
`exp_max = level_need(lev)`、`exp_total_nextlev = level_next_total(lev)`、
`attr_point = level_attr_point(lev)`。

### 2.4 升级表现**不需要任何新协议**

`main_ui.luac` proto#12（RoleVo 字段变化回调）的常量池是
`['exp','changeExp','isUplevel','lev','power']`，反汇编显示
**只有 `lev` 变化那一支会置 `isUplevel = true`**，然后播两段式经验条动画
（先填满 → 归零 → 再填到新值，见 proto#16/#18）。

⇒ **服务端把 `lev` 改对并下发即可，客户端自己发现升级、自己播表现。**
完全符合项目总原则（不重做客户端 UI、不新增协议）。

### 2.5 ★ 发现并修复：`SC_10302` 原来**只发了 4/29 个字段**

`SC_10302` 的权威 spec（`python tools/proto_spec.py cmds 10302`）共 **29 个字段**：

```
lev:H + exp/gold/gold_acc/coin/sinew/experience/coupon/vitality/guild_contrib/
practice_exp/tower_cent/arena_cent/integral/cash_coupon/dan_point/guild_active/
marriage/course/vip_exp/lingshi/peak_point/black_soul/lottery_point/boss_point/
partner_shenqi_point/jiebai_cent/rune_exp/rune_chip   （28 个 I）
```

而 `server/mock_server.py` 原先**只拼了前 4 个**（`lev/exp/gold/gold_acc`），
**后 25 个字段在包体里根本不存在** ⇒ 客户端读越界、这些资产只能显示 0/旧值。

**发现方式**：新工具 `tools/verify_level_protocol.py` 把服务端**实际发出的字节**
按权威 spec 解回来核对（spec 由 `tools/proto_spec.py` 运行时从
`cmd_resolve_103.luac` 读取，**不是硬编码**）。

**已修**：抽出统一 builder `build_10302(st)`，并替换全部 3 处调用点
（`CS_10302` 应答 / 任务提交后刷新 / 战斗结算后刷新），避免以后再各自跑偏。

修复后自检：

```
=== SC_10302 ===
  解码 29 个字段: {'lev': 7, 'exp': 500, 'gold': 1000, 'gold_acc': 5000, 'coin': 0, ...}
  OK   10302 字段数 29 == spec
  OK   10302 lev=7
  OK   10302 exp=500
```

### 2.6 协议层三个"经验相关"消息的**字节级核对**全部通过

`python tools/verify_level_protocol.py`：

| 消息 | 核对项 | 结果 |
|---|---|---|
| `SC_10302` | 29 字段全在；`lev`/`exp` 正确 | ✅ |
| `SC_10301` | `lev`；**`exp_max=3873` 与原版等级表 `RoleAttr[8].exp_max` 一致**；`exp_total_nextlev=17063`；`attr_point=0` | ✅ |
| `SC_10303` | `lev`/`exp` **与 10302 同步**；`attr` 表 `count=1`（一行 24 字段）；`atk_s=777`、`hp_max=4321` 与 DB 一致 | ✅ |

> 注：`attr` 的 `count` 是**行数**不是字段数 —— 最初把 `count` 与 spec 项数直接比是**错的**
> （已在工具里更正并写明），修正后 `count=1` 正是"一个单位一行 24 字段"。

### 2.7 澄清：`10409` 不是角色经验

`python tools/proto_spec.py cmds 10409` →

```
CS_10409{hero_bid:uint32}  /  SC_10409{hero_bid:uint32, exp:uint32}
```

⇒ `10409` 是**英雄（伙伴）加经验**，字段是 `hero_bid`，**与角色升级无关**。
`10342` 则只有 `SC_10342{profit_exp:uint32}`（单向推送，盈福经验）。

### 2.8 ★★ 客户端侧决定性证据：**它自己解出来的就是 `lev=8 / exp=400 / exp_max=4342`**

探针包住了 `RoleCtrl` 的四个处理器（`rgp_hander10301/10302/10303`、`hander10333`），
在其**入口处**把 `resp` 的字段逐个打出来 —— 这是**客户端真实解析结果**，不是服务端自述。

真机实测（`server/logs/http.log`，标签 `roleH`）：

```
rgp_hander10302_rid_nil_name_nil_lev_8_exp_400_exp_max_nil_gold_1000_gold_acc_5000_career_nil_sex_nil_skill_list_nil
rgp_hander10303_rid_1001_name_DSH_lev_8_exp_400_exp_max_nil_gold_1000_gold_acc_5000_career_1_sex_0_skill_list:_1
rgp_hander10301_rid_1001_name_DSH_lev_8_exp_nil_exp_max_4342_gold_nil_gold_acc_nil_career_1_sex_0_skill_list:_1
```

逐项对照：

| 客户端解出的字段 | 值 | 应与什么一致 | 结论 |
|---|---|---|---|
| `10302.lev` / `10303.lev` | **8** | DB `roles.level=8` | ✅ |
| `10302.exp` / `10303.exp` | **400** | DB `role_assets.exp=400` | ✅ |
| `10301.exp_max` | **4342** | **原版等级表 `RoleAttr[9].exp_max = 4342`** | ✅ **完全吻合** |
| `10303.career` / `sex` / `name` | 1 / 0 / DSH | 角色配置 | ✅ |

⇒ **客户端确实收到了正确的等级 8、经验 400、以及经验条分母 4342。**
经验条按 `exp / exp_max = 400 / 4342 ≈ 9.2%` 渲染 —— 数据源已全部对齐。

> 顺带证实：`rgp_hander10303` **确实被调用了**。
> 本项目 Phase 4D 的文档曾记录"该处理器从未被调用（回包未被派发 ⇒ 解析失败）"，
> 那是当时 10303 编码形态的 bug，**现已修复并可复现地调用**。

### 2.9 并行审计任务的**独立复核**（结论一致）

`analysis/1.4.9/level/exp_table.md`（子任务产出）用**独立方法**得到相同结论：

| 项 | 我方 | 子任务 | 是否一致 |
|---|---|---|---|
| 等级上限 | 200 | 200（键恰为 1..200 连续） | ✅ |
| 前 5 级 `exp_max` | 240/481/971/2452/2749 | 同 | ✅ |
| 升级阈值口径 | `RoleAttr[L+1].exp_max` | 同，置信度"**确定**" | ✅ |
| Lv2 异常 | 有 | 有（且指出 n=3..200 全部成立） | ✅ |
| `Config.Role` 不存在 / `RoleCareer[c].attr` 空表 | 有 | 同 | ✅ |
| 客户端**无**升级奖励表 | 倾向如此 | **确认** | ✅ |

**子任务提出的两条订正（我方采纳）：**

1. **职业 id 是 `1,2,3,4,5,9`（6 个）**，不是 `90100..91000`
   —— `90100..91000` 是**职业 5「神机」的技能 id**。
   （我方 `_role_career_raw.json` 的键实测也正是 `['1','2','3','4','5','9']`。）
2. **升级的可见产出**：技能按 `unlock_role_lev` 解锁；**40–69 级每级一个天命 buff**
   （`TianmingSkill`）；**客户端没有升级奖励表**。

---

## 三、服务端改动清单

| 文件 | 改动 |
|---|---|
| `server/mock_server.py` | ① 新增等级表加载 `level_table()/max_lev()/level_row()/level_need()/level_next_total()/level_attr_point()`<br>② 新增 **`add_role_exp(cfg, rid, amount)`**：加经验 + 按原版表结算（可连升多级）+ 落库 + 属性成长<br>③ 新增 `db_set_assets()`（绝对值写入，`db_add_assets` 只能加）<br>④ 新增 `apply_level_attr_growth()`（**`IMPLEMENTATION_FALLBACK`**）<br>⑤ `role_state()` 实时计算 `exp_max`/`exp_total_nextlev`/`attr_point`（覆盖写死的 100）<br>⑥ **12403 任务提交**与**战斗击杀**的 `exp` 改走 `add_role_exp`（原先直接 `db_add_assets` ⇒ 只涨经验不升级） |
| `analysis/1.4.9/level/level_table.json` | **新增**：200 级等级表（服务端真源） |
| `tools/export_level_table.py` | **新增**：等级表导出 + 自检（连续性/单调性/递推一致性） |
| `tools/test_levelup.py` | **新增**：升级自测（自动备份/还原 DB，断言升级/余量/属性/持久化） |
| `tools/stage_levelup_e2e.py` | **新增**：布置"只差 N 经验升级"的 E2E 起点（**只设起点，不伪造完成**） |
| `tools/verify_level_protocol.py` | **新增**：把服务端**实际发出的字节**按 1.4.9 权威 spec 解回来核对（`10301/10302/10303`）—— 就是它发现了 10302 截断 |
| `server/dsh_fake_login.lua` | 探针新增等级/经验上报（`_LEV…_exp…/max…/tot…`） |

---

## 四、自测结果（不依赖客户端，可直接复跑）

```powershell
Copy-Item analysis\_db_before_battle.db server\state\roles.db -Force
python tools\test_levelup.py --exp 20000
```

实测输出：

```
--- 战前 ---   lev=7 exp=500 本级需要=3873 exp_max(下发)=3873 exp_total_nextlev=17063
               atk_s=777 hp_max=4321
--- 加 20000 经验 ---
  ** level attr growth x4 (FALLBACK): {'atk_s': 825, 'hp_max': 4561, ...}
  ** LEVEL UP role 1001: 7 -> 11 (升 4 级), exp 余 1959, 下一级需 6119
--- 断言 ---
  OK 等级 7 -> 11（升 4 级）
  OK 剩余经验 1959 < 下一级需求 6119
  OK 下发的 exp_max 与阈值一致 (6119)
  OK 属性成长 atk_s 777 -> 825
  OK 重新读取等级保持 11
结论: 全部通过 ✅
```

---

## 五、原版数据 vs 兼容数据（**严格区分**）

| 项 | 来源 | 标记 |
|---|---|---|
| **升级所需经验**（1..200 级） | 1.4.9 `Config.RoleAttr` | **原版** ✅ |
| **等级上限 200** | 同上 | **原版** ✅ |
| 客户端取表下标（`lev+1`） | `main_ui.luac` proto#16 | **原版** ✅ |
| `10301` 的 `exp_max/exp_total_nextlev/attr_point` | `cmd_resolve_103.luac` | **原版** ✅ |
| **逐级属性成长（atk/hp/def…）** | APK 内**不存在** | **`IMPLEMENTATION_FALLBACK`**（`LEVEL_ATTR_GROWTH`） |
| 战斗击杀经验 50 / 金币 30 | APK 内**不存在** | **`TEST_ONLY`**（Phase D 既有） |

**必须明确：`LEVEL_ATTR_GROWTH`（每级 atk_s+12 / hp_max+60 …）不是原版数值。**

### 5.1 为什么属性成长"不可恢复"（证据）

| 候选来源 | 实测结果 |
|---|---|
| `Config.RoleAttr` | 只有 `exp_total/exp_max/attr_point/sinew_add/sinew_max`，**无 atk/hp/def**；且 `attr_point` **全 200 级都是 0** |
| `Config.RoleCareer[career].attr` | **空表 `{}`** |
| `Config.RoleCareer[career].turn_career_attr` | **空表 `{}`** |
| `Config.Role` | **整包内不存在**（全 347 个 config `.luac` 扫描，无定义点） |
| `config_role_attribute.luac` | 2 个 proto，**无全局安装点**（几乎空文件） |
| 客户端 `role_calculate.luac` | 27 个方法**全是装备/时装/法宝**的属性计算，**不含逐级成长** |

⇒ 逐级属性属**原版服务端数据**，APK 内无取证途径 —— 与 Phase D 的怪物 HP 同类缺口。

---

## 六、★ 发现的**原版数据异常**（如实保留，不修正）

`Config.RoleAttr` 里 `exp_total[L] = exp_total[L-1] + exp_max[L]` 对 **199/200** 个等级成立，
**唯独 L=2 不成立**：

| L | exp_max | exp_total（实测） | 按递推应为 |
|---|---|---|---|
| 1 | 240 | 240 | 240 |
| **2** | **481** | **481** | **721** |
| 3 | 971 | 1452 | 1452 ✓ |

⇒ `exp_total[2]` 看起来被写成了等于 `exp_max[2]`。
**这是原版配置自身的不一致**，`tools/export_level_table.py` 会把它**打印出来但不修改**。
（对升级判定无影响：客户端与服务端都只用 `exp_max`。）

---

## 七、诚实交代：本轮**未完成**的部分

| # | 项 | 状态 |
|---|---|---|
| 1 | **客户端经验条的像素级确认** | ⚠️ **数据层已确认，像素层不可靠**。客户端自己解出 `exp=400 / exp_max=4342`（§2.8），这是经验条的唯一输入，所以**数据链是通的**。但视觉模型对底部那条细经验条的读数**自相矛盾**（同一张图先读"1–2%"、再读"0%，未见填充"），且它把 VIP 徽章上的"1"误认成等级 —— **该读数不可采信，故不声称像素级已验证**。此外客户端本次多次启动失败（约 1/3 成功率），未能稳定复现截图窗口。 |
| 2 | **逐级属性成长** | `IMPLEMENTATION_FALLBACK`（原版不可恢复，见 §5.1；子任务独立复核同结论） |
| 3 | **升级奖励** | ✅ **已澄清**：客户端**没有**升级奖励表；升级的可见产出是 **技能按 `unlock_role_lev` 解锁** + **40–69 级每级一个天命 buff**（并行任务确认，我方同向） |
| 4 | `profit_exp`（盈福经验）语义与 `10342` 的关系 | `UNKNOWN`（`SC_10342{profit_exp:u32}` 是纯推送；客户端如何消费尚未追） |
| 5 | 多级跳升时的客户端表现 | 服务端支持连升多级（自测 7→11、7→9），**客户端是否逐级播动画未验证** |
| 6 | 200 级以上行为 | `UNKNOWN`（表止于 200，客户端对 nil 有守卫） |

---

## 八、复现步骤

```powershell
# 1) 起服务端（含可靠重启 + 冒烟）
pwsh tools\restart_server.ps1

# 2) 不依赖客户端的升级自测
Copy-Item analysis\_db_before_battle.db server\state\roles.db -Force
python tools\test_levelup.py --exp 20000

# 3) 真机 E2E：把角色布置到"只差 100 经验升级"
python tools\stage_levelup_e2e.py --gap 100
#    打开战斗探针（server/dsh_fake_login.lua 里 _G.__dsh_battle = true）后：
pwsh tools\build_fakelogin.ps1
#    等客户端进图并自动提交任务 → 看服务端日志
Select-String -Path server\logs\tcp.log -Pattern 'LEVEL UP|level attr|10302 \(refresh'
```

---

## 九、交付物索引

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/level/level_table.json` | **原版等级表**（200 级，服务端真源） |
| `analysis/1.4.9/level/client_levelup_view.md` | 客户端经验条/升级表现逐句还原（proto#12/16/18） |
| `analysis/1.4.9/level/role_attr.json` / `role_career.json` | `Config.RoleAttr` / `Config.RoleCareer` 提取结果 |
| `analysis/1.4.9/level/exp_table.md` | 经验表文档（**并行任务产出**） |
| `analysis/1.4.9/level/levelup_protocol_matrix.md` | 升级相关协议矩阵（**并行任务产出**） |
| `tools/export_level_table.py` | 等级表导出 + 自检 |
| `tools/test_levelup.py` | 升级自测（自动备份/还原） |
| `tools/stage_levelup_e2e.py` | E2E 起点布置 |
| `server/mock_server.py` | `add_role_exp` 等 Phase E 实现 |
