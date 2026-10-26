# 服务端能力核实报告（PHASE 0 · VERIFIED）

> 审计时间：2026-10-02
> 审计对象：`C:\Users\xu\Desktop\DSH\server\mock_server.py`（主服）+ `server/minloop/`（最小回环服）
> 审计方式：**只读**。未修改 `server/` 下任何 `.py/.lua/.db/.json`。miniloop `selftest.py` 已运行一次（其使用 `tempfile.mkdtemp`，落盘到 `%TEMP%\minloop_selftest_*`，**未写 minloop.db**）。
> 证据纪律：`CONFIRMED` = 从代码/SQLite/运行输出直接确认；`INFERENCE` = 只能从命名/注释/相邻代码推断；`UNKNOWN` = 看不到。
> 行号基于当前 `mock_server.py`（**18,506 行**，ReadAllLines 实测；任务背景给的"约 1.6 万行"偏旧）。
>
> **★ 新增硬约束（2026-10-02，PHASE 0 末尾追加）**：本报告所有"数值真实性"结论必须用 **MuMu 12 模拟器跑 1.4.11 原版客户端**拿到真实运行报文/UI 读数才算 `VERIFIED`。凡属以下情况的条目，一律追加标注 **⚠ 需 MuMu 运行时取证**：
> - 战斗数值（怪物 HP/攻防/伤害/暴击/经验/金币）
> - 掉落表（物品 bid/数量）
> - 装备属性数值、强化/洗练/宝石结果
> - 伙伴/翅膀/坐骑/魂兽/元神/神器/命格/法宝/时装等成长族的成长曲线
> - 战力公式 `role_power()` 算出的战力值与客户端 UI 显示是否一致
> - 经验表/等级表 `exp_max` 是否与客户端经验条分母一致
> - 任何"配置已反构造但未在客户端实机上屏验证"的数据
>
> 静态代码能确认的只是"**有没有这个分支、读没读这张表、字段结构对不对**"（= `CONFIRMED by code`）；**数值对不对、客户端显不显示** 必须等 MuMu 联调（Phase 1 第一项前置任务，见第十节）。

---

## 〇、关键数字一览（VERIFIED）

| 指标 | 任务背景声称 | 本次核实 | 证据 |
|---|---|---|---|
| mock_server.py 行数 | ~98 万字节 / ~1.6 万行 | **18,506 行 / 982,387 字节** | `[IO.File]::ReadAllLines` 实测 |
| TCP 游戏端口 | 9000 | **9000**（`--game` 默认） | L15 注释、L1473 miniloop 默认 9099 |
| HTTP 管理端口 | 8080 | **8080**（`--http` 默认） | L15 注释 |
| 专用 handler 分支数 | ~1446 条 | **800 个独立命令号**（去重后）；`if cmd == N` 命中 585 处 + `if cmd in (...)` 展开后累计 ~1400 分支 | 正则扫描 `cmd\s*==\s*(\d+)` / `cmd\s+in\s*\(...\)` |
| `_UNSUPPORTED_ACTION_CMDS` | 0 个兜底 | **空 frozenset**（L1991–2002，括号内全是注释） | Read L1991–2003 |
| `_GENERIC_DEFAULT_CMDS` | 0 个兜底 | **空 frozenset**（L1903–1979，括号内全是注释） | Read L1903–1979 |
| 全局兜底 | 0 | **存在但默认关闭**：L18431 `if CFG.get('global_default_sc') and _sc_defined(cmd):`，由 `config.json` 开关控制（默认 false） | Read L18426–18435 |
| SQLite 表数 | 47 张 | **55 张**（含 `sqlite_sequence`；用户表 54 张） | `SELECT name FROM sqlite_master` |
| /DSH_ADMIN 动作数 | — | **44 个** `if act == '...'` 分支 | Grep 全量列出 |
| 配置目录 | 230+ 张 1.4.11 反构造 | `cfg/`=231, `cfg_kconst/`=285, `cfg_kconfig/`=245, `cfg_kconfig2/`=245 | Get-ChildItem |
| miniloop 命令数 | 11 条 | **17 条 LOOP + 4 条 ROLE_QUERIES**（10301–10304） | L1270–1278 |
| miniloop 自检 | 44 项 | **145 项，145 PASS / 0 FAIL**（实测运行） | 运行 `selftest.py` 输出 |

---

## 一、mock_server.py 概览

- **入口**：`main()` 在文件末尾；`ThreadingHTTPServer`（HTTP/8080）+ `socketserver.ThreadingTCPServer`（TCP/9000）双服务并发。
- **协议栈**：自实现帧编码（大端 u32 长度 + u16 cmd + body）；SC 字段表来自 `protocol/fields.json`（3553 条，由 `cmd_resolve_*.luac` 反构造）。
- **周边模块**（均 `try: import … except: = None` 软依赖）：
  - `battle.py`（L35–37）：战斗回合模拟器
  - `aoi.py`（L123–125）：九宫格 AOI
  - `power.py`（L128–130）：战力公式
  - `pathfind.py`（L133–135）：`MapGrid` + `MoveRateLimiter`
  - `world/`（area/entities/move/ticker/jstm_bridge）：在 `world/` 子目录，未被 mock_server 直接 import（属 jstm 引擎路线）
- **主分发入口**：`TcpHandler._reply(self, cmd, body)` 从 **L9589** 开始，到 **L18455** 结束（约 8,866 行的 handler 主体）。结构为顺序 `if cmd == …: … return`，无 dict dispatch。

### 1.1 兜底机制（重要更正）

| 兜底 | 现状 | 证据 |
|---|---|---|
| `_UNSUPPORTED_ACTION_CMDS` | **空集合**。定义在 L1991，括号内 11 行全是注释（历史上 R42/R48/R50/R190 逐条移出）。L9777 仍有 `if cmd in _UNSUPPORTED_ACTION_CMDS:` 分支，但永不命中。 | CONFIRMED |
| `_GENERIC_DEFAULT_CMDS` | **空集合**。定义在 L1903，括号内 77 行全是注释（R80/R48/R46/R47/R50/R190 逐条移出）。L9802 仍有判断，但永不命中。 | CONFIRMED |
| 全局 `global_default_sc` | **存在但默认关**。L18431 `if CFG.get('global_default_sc') and _sc_defined(cmd):` → `_build_default_sc(cmd)`。注释 L18426–18430 说明 R150 把它从函数前部移到末尾，避免遮蔽专用分支。 | CONFIRMED |
| 块内 `_out = _build_default_sc(cmd, 1, '')` | 多处内联（L10162/L10232/L10868/L10967/L11063/L11198/L11334）—— 这些是**已知子族内**的安全默认（如 166xx 节日、187xx 婚姻、17xxx 跨服、30xxx 等），不是未知命令的兜底。 | CONFIRMED |

**结论**：先前审计结论"0 个 unsupported 兜底、0 个 generic 兜底" **属实**；但"CS+SC 覆盖 100%" 严格说是"对已知 SC 规格的命令 100% 有分支（含内联安全默认），未知命令默认不应答（除非开 global_default_sc）"。

---

## 二、命令族覆盖表（按千位段）

> 800 个去重命令号。每段列出范围与代表命令（CONFIRMED，来自正则扫描）。

| 段 | 命令数 | 范围 | 代表命令 | 对应系统（INFERENCE，按命令号惯例） | 状态 |
|---|---|---|---|---|---|
| 1000–1999 | 2 | 1110–1199 | 1110 登录、1199 心跳 | 账号/心跳 | CONFIRMED |
| 10000–10999 | 184 | 10001–10998 | 10001 首包、10101 建角、10102/10103 登角、10200/10201 进场景、10202/10204/10205 移动/传送、10300–10306 角色四件套、10311–10399 角色杂项、10401–10424 伙伴/上阵、10500–10593 背包/装备/使用/强化/宝石/洗练/穿戴、10601–10651 buff/饱食、10701–10762 仓库、10800–10810 邮件/欢迎、10900–10999 系统/活动/红点 | 角色/场景/背包/装备/buff/仓库/邮件 | CONFIRMED |
| 11000–11999 | 46 | 11010–11801 | 11200–11228 伙伴/神将、11300–11308 荣耀竞技场、11400–11413、11600–11699 社交/聊天、11700–11717、11801 | 伙伴/竞技场/社交 | CONFIRMED |
| 12000–12999 | 60 | 12000–12994 | 12000–12007 （杂项）、12207/12209/12212/12215、12400–12436 任务、12601/12602 爬塔/副本、12721/12723/12761/12762/12764、12801–12843 商城/珍宝/限购、12901–12971 排行榜 | 任务/商城/排行/副本 | CONFIRMED |
| 13000–13999 | 136 | 13004–13906 | 13004–13098 副本/爬塔/运营活动、13200–13254 队伍、13300–13371 好友/社交、13401–13410 限购商店、13500–13580、13701–13789、13801–13851、13901/13906 充值 | 副本/队伍/好友/商店/充值 | CONFIRMED |
| 14000–14999 | 24 | 14000–14901 | 14000–14009 活动、14100/14101、14203/14204、14600/14601 等级礼包、14700/14701、14802/14812、14901 | 活动/等级礼包 | CONFIRMED |
| 15000–15999 | 22 | 15200–15811 | 15200–15204 NPC 操作、15400–15405 挂机/AFK、15501–15519、15700–15812、15801（设计不应答） | NPC/挂机 | CONFIRMED |
| 16000–16999 | 37 | 16102–16904 | 16100–16112、16200/16202、16300/16301、16400/16401 成就、16500–16503 投资/运营、16601–16698 节日/活动、16700–16706、16900/16903/16904 | 成就/节日/活动 | CONFIRMED |
| 17000–17999 | 60 | 17000–17909 | 17000/17001、17100/17101 魂师大赛、17200/17201 巅峰战、17301–17312 竞速/跨服、17400–17402、17501–17519 宗门战、17600–17602、17700–17716、17800/17801、17902–17909 | 跨服/宗门/竞速 | CONFIRMED |
| 18000–18999 | 85 | 18001–18911 | 18001–18026 拍卖行、18100/18101、18200/18201、18300–18322 结婚/求婚/婚戒、18400–18404、18502、18600–18613、18706–18716、18803–18886、18900–18911 法宝/社交 | 拍卖/结婚/法宝 | CONFIRMED |
| 19000–19999 | 43 | 19002–19901 | 19002/19003/19005、19100–19120 光环、19200–19202、19400–19414、19500–19536 结拜、19600/19601 签到、19901 | 结拜/光环/签到 | CONFIRMED |
| 20000–20999 | 34 | 20001–20809 | 20001–20023 战斗、20100 养成/推广、20201–20310、20500–20505、20707/20725、20800–20809 | 战斗/养成 | CONFIRMED |
| 21000–21999 | 18 | 21301–21604 | 21301/21306/21312、21400–21414 符文/魂星、21603/21604 | 符文/魂星 | CONFIRMED |
| 30000–30999 | 49 | 30104–30902 | 30104–30109、30201–30220、30300–30306、30400–30403、30500–30507、30600–30603、30701–30717、30800、30900–30902 | （运营/老系统，命令号段为兼容层） | CONFIRMED |

---

## 三、SQLite 表清单（55 张，按系统归类）

> 来源：`SELECT name FROM sqlite_master WHERE type='table'` on `server/state/roles.db`（376,832 字节）。括号内为当前行数（只读 COUNT）。

| 系统 | 表名（行数） | 备注 |
|---|---|---|
| 账号 | `accounts`(1) | R44 起多账号 |
| 角色主表 | `roles`(1) | rid/名字/职业/性别/等级/经验/坐标 |
| 角色扩展 | `role_attr`(1)、`role_assets`(9)、`role_buffs`(0)、`role_point`(1) | 属性/货币/buff/点数 |
| 背包/装备 | `bag_items`(4)、`bag_volume`(4)、`equip_items`(6)、`store_items`(0) | 含多 bag_code |
| 任务 | `missions`(5) | 846 条任务配置来自 `mission_config.json` |
| 伙伴/神将 | `role_heros`(18)、`role_form`(1) | 53 个伙伴来自 `_partner_base.json` |
| 装备进阶族 | `role_fabao`(4)、`role_lingshou`(1)、`role_yuanshen`(1)、`role_shenqi`(2)、`role_mingge`(2)、`role_chair`(1)、`role_wing`(1)、`role_ride`(1)、`role_runes`(1)、`role_halo`(0)、`role_halo_equip`(0)、`role_fashion`(0) | 法宝/魂兽/元神/神器/命格/椅子/翅膀/坐骑/符文/光环/时装 |
| 社交 | `role_chat`(1)、`role_moments`(1)、`role_team`(0)、`role_team_invite`(0)、`role_jiebai`(0)、`role_marry`(0)、`role_marry_propose`(0)、`role_guild`(1)、`role_qifu`(1) | 结拜/结婚/公会祈福 |
| 建筑/科技 | `role_build`(1)、`role_build_learn`(2)、`role_tree`(1) | 公会建筑/摇钱树 |
| 商业 | `mall_bought`(43)、`role_market`(1)、`role_market_goods`(1) | 商城限购/摆摊 |
| 邮件 | `role_mail`(194) | R161 起真实落库 |
| 排行/竞技 | `arena_state`(0)、`arena_record`(0)、`peakwar_state`(0)、`race_state`(0)、`role_boss_kill`(0)、`role_title`(0) | 荣耀竞技场/巅峰战/魂师大赛/BOSS/称号 |
| 副本/爬塔 | `dungeon_progress`(5) | 130xx 段 |
| 日常/成就/挂机 | `daily_progress`(1)、`daily_lingqu`(0)、`chengjiu_progress`(4)、`guaji_state`(1)、`sign_got`(1) | 43 日常/342 成就 |
| 投资 | `role_invest`(0) | R107/R117 |
| 等级礼包 | `levgift_got`(0) | |
| 元数据 | `sqlite_sequence`(1) | 自增主键表 |

**注意**：任务背景声称"47 张"已过时；实际 **54 张用户表 + 1 张 sqlite_sequence = 55**。部分表（`role_team`/`role_jiebai`/`role_marry`/`role_fashion`/`role_halo` 等）在代码注释里明确标 **INFERENCE 兼容层**（原版表结构不可取证）。

---

## 四、/DSH_ADMIN 动作清单（44 个，CONFIRMED）

> 入口 L704 `if p.startswith('/DSH_ADMIN/')`。所有动作默认 `rid=1001`，可 `?rid=` 覆盖。

| 动作 | 行号 | 用途 |
|---|---|---|
| `getlevel` | 709 | 查等级/经验 |
| `daily` | 715 | 加日常进度（R48） |
| `chengjiu` | 741 | 加成就进度（R48） |
| `guaji` | 763 | 设挂机轮次 15405（R48） |
| `guaji_end` | 772 | 推 15404 结束本轮（R53） |
| `addbag` | 790 | 发物品/一键发阵法书（R89） |
| `mail` | 830 | 发真实邮件（R161） |
| `marketgoods` | 838 | 摆摊上架（R140） |
| `build` | 849 | 建筑技能发放（R140） |
| `tree` | 859 | 摇钱树等级（R138） |
| `fabao` | 869 | 法宝发放（R131） |
| `bosskill` | 880 | 标记 BOSS 已杀（R129） |
| `title` | 896 | 称号发放（R129） |
| `lingshou` | 907 | 魂兽发放（R127） |
| `yuanshen` | 916 | 元神发放（R127） |
| `shenqi` | 924 | 神器发放（R126） |
| `mingge` | 934 | 命格发放（R126） |
| `chair` | 942 | 座椅发放（R125） |
| `wing` | 953 | 翅膀发放（R125） |
| `invest` | 964 | 投资进度（R117） |
| `ride` | 984 | 坐骑发放（R115） |
| `qifu` | 996 | 公会祈福次数（R243） |
| `exp` | 1007 | 实验开关（hero_bag_limit 等 4 键） |
| `hero` | 1029 | 伙伴背包管理（R86） |
| `buff` | 1051 | buff 列表管理（R80） |
| `power` | 1067 | 战力明细（role_power + power_items） |
| `aoi` | 1084 | AOI/寻路只读状态 |
| `cfglist` | 1097 | 列出 APK 内 347 张 .luac 配置表 |
| `cfg` | 1115 | 读任意配置表（?name=…&kw=…） |
| `status` | 1159 | 一次拉全部状态（角色/资产/包/装备/仓库/礼包） |
| `giveitem` | 1175 | 发物品（多件，bid/num 后缀） |
| `givegift` | 1208 | 发礼包 |
| `setequip` | 1231 | 穿装备 |
| `unequip` | 1249 | 脱装备 |
| `setheros` | 1258 | 设置伙伴列表 |
| `setjubaopen` | 1275 | 聚宝盆 |
| `setmissions` | 1299 | 设置任务 |
| `reset` | 1321 | 重置角色 |
| `reload` | 1342 | 热重载配置 |
| `listitems` | 1370 | 列物品 |
| `setassets` | 1387 | 设货币 |
| `getassets` | 1445 | 查货币 |
| `setlevel` | 1454 | 设等级并推送 |
| `additem` | 1473 | 加物品（别名/addbag） |

---

## 五、配置读取机制（CONFIRMED）

| 配置 | 路径 | 规模 | 用途 |
|---|---|---|---|
| 运行配置 | `server/config.json` | 73,524 B | 端口/host/默认角色/mon/NPC/开关 |
| 物品表 | `server/item_config.json` | 2,186,699 B / 3535 件 | L1771 `tools/extract_item_v2.py` 产物 |
| 任务表 | `server/mission_config.json` | 718,567 B / 846 条 | L1741 `tools/extract_mission_config.py` |
| 商城 | `server/mall_config.json` | 27,108 B | L1766 |
| 礼包 | `server/item_gift.json` | 60,521 B / 496 礼包 / 5353 条 | L1803 |
| 珍宝商城 | `server/mall_zhenbao.json` | 11,097 B | L3997（IMPLEMENTATION_FALLBACK） |
| 兑换 | `server/mall_exchange.json` | 7,664 B | L4125（IMPLEMENTATION_FALLBACK） |
| 伙伴基础 | `server/_partner_base.json` | 31,629 B / 53 个 | L3924 |
| 日常 | `server/_richang.json` | 19,393 B / 43 条 | L6561 |
| 成就 | `server/_chengjiu.json` | 120,464 B / 342 条 | L1913 注释 |
| 战力权重 | `server/_attr_data.json` | 8,144 B | power.py L33 加载 `AttrPower` |
| 地图阻挡 | `server/map_block.json` | 129,151 B | L341 |
| 反构造配置 | `server/cfg/` | **231** 个 JSON | 1.4.11 反构造 |
| 常量池 | `server/cfg_kconst/` | **285** 个 JSON | L3248 `cfg_kconst(name)` |
| 配置表 | `server/cfg_kconfig/` | **245** 个 JSON | L3691 `cfg_kconfig(name)` |
| 合并配置 | `server/cfg_kconfig2/` | **245** 个 JSON | L3773 `cfg_kconfig2(name)`（R237b） |
| 符文 | `server/_rune_cfg.json` | 1,745,692 B | |
| 推广/进阶 | `server/_promote.json` | 45,540 B | |
| 命格/挂机/投资/转盘 | `_mingge_cfg.json` / `_guaji.json` / `_invest_cfg.json` / `_dial_reward.json` | 小 | |
| 协议规格 | `protocol/fields.json`（项目根，不在 server/） | 3553 条 | L2014 `_sc_fields(cmd)` |

---

## 六、用户点名系统逐项核实表

> 证据列给出行号或命令号范围。结论：✅ 已实现 / 🟡 部分实现 / ❌ 未实现 / ❓ UNKNOWN。
> **"运行时取证"列**：= ✅ **代码结构 CONFIRMED（字段/分支/表都在）**；⚠ **需 MuMu 运行时取证**（数值真实性、UI 上屏一致性未验）。本表默认所有"数值类"系统都需 MuMu 联调才能升级为 VERIFIED。

| # | 系统 | 结论 | 证据（行号/命令） | 备注 / 证据等级 |
|---|---|---|---|---|
| 1 | 登录（账号） | ✅ | L9637 `if cmd == 1110`；`accounts` 表 | CONFIRMED；不校验 token（L9645 注释） |
| 2 | 角色（建角/登角） | ✅ | L15156 `10101`、L15089 `if cmd in (10102, 10103)` | CONFIRMED |
| 3 | 等级/经验 | ✅ | `roles.level/exp`；L5786 升级属性成长（**IMPLEMENTATION_FALLBACK**） | 等级表 config.json；成长数值 FALLBACK |
| 4 | 属性 | ✅ | L56 `role_attr_dict()`；`role_attr` 表 | 64 项属性（power.py 头注） |
| 5 | 战力 | ✅ | L82 `role_power()` → `power.py:calc_power()` | **CONFIRMED**：原版权重 `AttrPower` 从 `_attr_data.json` 读（power.py L11–18），非 INFERENCE |
| 6 | 货币 | ✅ | `role_assets`(9 行)；`setassets/getassets` 管理动作 | 钻石=gold/银魂币=coin/金魂币=coupon（L160 旧矩阵已复验） |
| 7 | 背包 | ✅ | L18345 `10502`；L15486 `10500` 推送；`bag_items/bag_volume` | CONFIRMED；多 bag_code |
| 8 | 装备 | ✅ | `equip_items`；L1231 setequip/L1249 unequip；命令 10573–10578 | CONFIRMED |
| 9 | 强化 | 🟡 | L9751 注释"装备强化/洗练结果"；命令 105xx 段 | 有分支但具体强化算法 INFERENCE（未见独立强化公式） |
| 10 | 升阶 | 🟡 | L8277 `ride_jie_items()` 坐骑升阶；椅子/翅膀/坐骑/法宝/神器段均有 jie/stage 字段 | CONFIRMED 存在；数值来自 cfg_kconfig |
| 11 | 洗练 | 🟡 | L9751 注释提及；105xx 段有分支 | INFERENCE：未见独立洗练公式 |
| 12 | 宝石 | 🟡 | 105xx 段（10534/10551 旧矩阵标缺口，现在 L16802 `if cmd in (10534, 10551)` 已有分支） | CONFIRMED 有分支；具体孔位/数值 INFERENCE |
| 13 | 技能 | ❓ | 命令 11xxx/13xxx 段未见明确技能学习分支；战斗内 20009 选技 | UNKNOWN：被动技能/技能升级未在本次扫描中定位 |
| 14 | 伙伴（神将） | ✅ | L13171 `11210`；L12778 `12419`；`role_heros`(18)；`_partner_base.json` 53 个 | CONFIRMED（R86/R110/R217/R228） |
| 15 | 翅膀 | ✅ | L953 `wing` 管理动作；L14131 专用分支；`role_wing` | CONFIRMED（R125/R142） |
| 16 | 魂骨 | ❓ | 未在命令扫描中定位到明确"魂骨"分支 | UNKNOWN |
| 17 | 时装 | ✅ | L7873–7940 时装段（10573–10578）；`role_fashion` | CONFIRMED 配置（cfg_kconfig/config_fashion）；表结构 INFERENCE |
| 18 | 增幅 | ❓ | 未见独立"增幅"分支 | UNKNOWN |
| 19 | 神器 | ✅ | L924 `shenqi`；L14094 专用分支；`role_shenqi`(2) | CONFIRMED（R126/R144） |
| 20 | 命格 | ✅ | L934 `mingge`；L14476 命格背包；`role_mingge`(2) | CONFIRMED（R126/R143） |
| 21 | 阵法 | ✅ | L1901 `FORMATION_BOOKS`；L18036 阵型属性汇总；`role_form` | CONFIRMED；阵法书 36052–36057 |
| 22 | 副本 | ✅ | 13004–13098 段；`dungeon_progress`(5)；12601/12602 爬塔 | CONFIRMED（R44/R45/R46/R147/R170） |
| 23 | 挂机（AFK） | ✅ | L17803–17948 段（15400–15405）；`guaji_state` | CONFIRMED（R48/R53/R54/R57） |
| 24 | 商城 | ✅ | L15978 12801/L15985 12803/L16000 12805/L15775 12831/L15876 12840 | CONFIRMED；限购已实现 |
| 25 | 礼包 | ✅ | L15035 `10514`/L15042 `10532`；`item_gift.json` 496 礼包 | CONFIRMED |
| 26 | 活动 | ✅ | 14000–14901、16600–16698、17200 段；config_function.json 91 条 | CONFIRMED |
| 27 | 签到 | ✅ | L10108 `19600` 每日签到（config_checkin 95 条）；`sign_got` | CONFIRMED |
| 28 | 日常 | ✅ | L715 `daily` 管理；`daily_progress`；`_richang.json` 43 条 | CONFIRMED |
| 29 | 成就 | ✅ | L741 `chengjiu`；`chengjiu_progress`；`_chengjiu.json` 342 条；L17764 `16400` | CONFIRMED（R48） |
| 30 | 社交（聊天/动态） | 🟡 | `role_chat`(1)、`role_moments`(1)；11600–11699 段 | CONFIRMED 有分支；IM 实时转发未深入验证 |
| 31 | 好友 | ✅ | 13300–13371 段（L11954 起）；L11485 注释 13321 好友申请 | CONFIRMED |
| 32 | 聊天 | 🟡 | 11600–11699 段；`role_chat` 表 | INFERENCE：频道广播未实测 |
| 33 | 公会 | 🟡 | `role_guild`(1)、`role_build`、`role_qifu`；13200 是队伍不是公会 | INFERENCE：公会本体数据多为空（peakwar/race 表 0 行） |
| 34 | 排行榜 | ✅ | 12901–12971 段；L15401 `if cmd in (12901, 12902, 12911, 12912, 12931)` | CONFIRMED（R40/R171/R172/R173） |
| 35 | 邮件 | ✅ | L830 `mail` 管理；`role_mail`(194)；10800 欢迎邮件；10801–10810 段 | CONFIRMED（R161） |
| 36 | 掉落 | 🟡 | battle.py `FALLBACK_DROPS`（**TEST_ONLY**）；L9490–9529 | 怪物 HP/攻防/经验/金币/掉落全部 **TEST_ONLY**（APK 无此数据） |
| 37 | 货币增减 | ✅ | L9490 `KILL_REWARD`；L1387 setassets | CONFIRMED 机制；数值 TEST_ONLY |
| 38 | 经验 | 🟡 | 升级路径存在；怪物经验 KILL_REWARD 为 TEST_ONLY | 玩家升 exp 路径 CONFIRMED；怪物给的 exp 为占位 |
| 39 | 等级 | ✅ | `roles.level`；L1454 `setlevel` | CONFIRMED |
| 40 | 属性面板 | ✅ | L15325 `10303`；L16228 `10301`；L15336 `10302` | CONFIRMED |
| 41 | NPC | 🟡 | L15560 `15202`/L15584 `15203`/L10089 `15204`；SC_10201.npcs 摆位 | CONFIRMED 摆位；NPC 对话 UI 旧矩阵标 NO（客户端 setOpenNpc 未定义） |
| 42 | 地图 | ✅ | `map_block.json`；L341；10200/10201 推送 | CONFIRMED |
| 43 | 自动寻路 | 🟡 | L4434 注释"把任务目标放进 SC_10201 的 npcs/mons"；pathfind.py | 旧矩阵：部分（任务条点击能移动，missionGoto 不直接发移动包） |
| 44 | 怪物 | 🟡 | SC_10201.mons；battle.py MON_STATS | CONFIRMED 摆位；HP/攻防 **TEST_ONLY** |
| 45 | BOSS | 🟡 | L880 `bosskill`；L14028 BOSS 列表；`role_boss_kill` | CONFIRMED 列表/已杀标记 |
| 46 | GM 能力 | ✅ | 44 个 /DSH_ADMIN 动作（见第四节） | CONFIRMED |
| 47 | 红点/UI 状态 | 🟡 | 10900–10999 段（活动列表/系统解锁）；10621/10650 等 | CONFIRMED 有分支；红点语义 INFERENCE |
| 48 | 结婚/结拜 | 🟡 | L10539 18300–18322 结婚；L10409 19505–19536 结拜 | 表 `role_marry/role_jiebai` 为 INFERENCE 兼容层 |
| 49 | 拍卖 | 🟡 | L11532 18020/18021；L11577 18008/18024/18025 | CONFIRMED 有分支 |
| 50 | 坐骑 | ✅ | L984 `ride`；L14541 专用分支；`role_ride` | CONFIRMED（R115/R144） |
| 51 | 魂兽/灵兽 | ✅ | L907 `lingshou`；L14050；`role_lingshou` | CONFIRMED（R127） |
| 52 | 元神 | ✅ | L916 `yuanshen`；L14083；`role_yuanshen` | CONFIRMED（R127） |
| 53 | 法宝 | ✅ | L869 `fabao`；L13971；`role_fabao`(4) | CONFIRMED（R131/R134/R218） |
| 54 | 符文/魂星 | ✅ | 21300–21604 段；`_rune_cfg.json` 1.7MB | CONFIRMED（R104/R109/R113/R114） |
| 55 | 投资 | ✅ | L964 `invest`；`role_invest`；16500/16503 | CONFIRMED（R107/R117） |

### 6.1 运行时取证分组（依新硬约束）

**A. 静态代码已 CONFIRMED，数值真实性需 MuMu 取证（⚠）：**

- 等级/经验/属性（#3/#4）：等级表来自 config.json，但 `exp_max` 分母、升级后属性增量必须与客户端经验条/属性面板上屏值比对。
- 战力（#5）：`role_power()` 走 `_attr_data.json` 的原版权重，公式本身 CONFIRMED；但**算出的战力值与客户端 UI 显示战力是否一致**未验。
- 货币（#6）：资产 code 语义（1 钻石/2 银魂币/3 金魂币）旧矩阵用界面读数复验过，但需 1.4.11 重抓。
- 强化/升阶/洗练/宝石（#9/#10/#11/#12）：有分支、扣材料写库，但**强化成功率/属性增量/孔位数值**未验。
- 装备（#8）：穿戴/脱下落库，但装备 item_attr 数值是否与客户端装备面板一致未验。
- 伙伴（#14）：53 个伙伴来自 `_partner_base.json`，但伙伴战力/资质/技能数值需客户端上屏比对。
- 翅膀/坐骑/魂兽/元神/神器/命格/法宝/时装/椅子/光环/符文（#15/#19/#20/#21/#51/#52/#53）：配置来自 cfg_kconfig，但**每阶属性加成、进阶消耗、外观是否在客户端正确挂载**未验。
- 阵法（#21）：FORMATION_BOOKS 与阵法书 bid 已知，但阵法属性汇总（18036）数值未验。
- 副本/爬塔（#22）：进度落库，但层数奖励/怪物配置未验。
- 战斗（#36/#37/#38/#44）：battle.py 的 MON_STATS/KILL_REWARD/FALLBACK_DROPS/DAMAGE_SCALE **全部 TEST_ONLY**，必须用 MuMu 实抓真实怪物 HP/伤害/经验/金币/掉落。
- 任务奖励（#2 表内任务）：`award_assets` 来自 mission_config.json，但任务条件判定（杀怪数/交物品数）与客户端进度条是否一致需验证。
- 商城（#24）：商品 134 件来自 mall_config.json，但价格/限购/支付后客户端扣币动画是否一致需验证。
- 签到/日常/成就（#27/#28/#29）：进度落库，但客户端红点/可领状态是否正确点亮需验证。

**B. 纯结构 CONFIRMED、不依赖数值上屏（代码层即 VERIFIED）：**
- 登录/建角/登角/心跳（#1/#2）、协议帧编解码、AOI/寻路模块加载、/DSH_ADMIN 44 个动作、SQLite 55 张表的 schema、命令分发结构本身。

**C. UNKNOWN 需进一步代码阅读或实机验证：**
- 技能学习/升级（#13）、魂骨（#16）、增幅（#18）、聊天频道实时广播（#32）、公会本体（#33，表 0 行）、NPC 对话 UI（#41，客户端 setOpenNpc 未定义）。

---

## 七、miniloop 能力总结

### 7.1 命令清单（L1270–1278，CONFIRMED）

**LOOP 字典（17 条）**：`10001, 1199, 1110, 10101, 10102, 10103, 10300, 10204, 12400, 12402, 12403, 12404, 12414, 12415, 20002, 10502, 10505`。

**ROLE_QUERIES（4 条，走 `on_role_query` 通用回真实数据）**：`10301, 10302, 10303, 10304`。

**回环外命令**：按 `protocol/fields.json` 的 SC 规格通用编码（结构对、内容零值）；无 SC 定义的命令不回包（L1296 起 `handle`）。

> ⚠ README 声称"11 条命令"已过时：实际 **17 条 LOOP + 4 条 ROLE_QUERIES = 21 个专用 handler**。

### 7.2 回环流程

登录（1110 code=1）→ 建角（10101）/ 登角（10102/10103）→ 推 10200/10201（场景格子含角色/NPC/怪）→ 10300 触发 10301–10304 四件套 → 10204 移动落库 → 12400 任务列表（链头）→ 12402 接取 → 20002 开战（20010 初始化 → 20012/20013 回合 → 20020 结果 → 20023 结算）→ 12403/12414/12415 提交（杀怪/交物品）→ 发奖（10302 货币同步 + 12405/12406 任务更新）→ 10502 背包查询。

### 7.3 selftest 运行结果（VERIFIED，本次实跑）

```
检查项 145，通过 145，失败 0
DB 落盘：C:\WINDOWS\TEMP\minloop_selftest_hu3n1zai\test.db
```

- README 声称"44 项自检" **严重过时**；实际 145 项（含 12414/12415 交物品、10101 建角/重名/非法职业、10505 礼包、10922 空表断言、回环外命令通用应答等）。
- 运行未触碰 `server/minloop/minloop.db`（用 tempfile）。

### 7.4 端口

默认 `--http 8099 --game 9099`（避开主服 8080/9000）；可 `--http 8080 --game 9000` 覆盖。

### 7.5 数据真实性标注（README §三，CONFIRMED）

- 协议规格/任务 846/物品 3535 = **[APK] 原版**
- 怪物 HP/攻防/经验/金币/掉落/伤害系数 = **[TEST_ONLY] 占位**
- 公会/拍卖/结婚/跨服/副本/社交 = **不实现**（回环外）

---

## 八、与既有能力矩阵（analysis/1.4.9/server_capability_matrix.md）的差异

> 旧矩阵日期 2026-09-18，统计自 `logs/tcp.log`（107 条客户端请求 / 45 条应答 / 59 条缺口）。本报告基于 2026-10-02 代码现状。

| 项 | 旧矩阵声明 | 本次代码核实 | 差异 |
|---|---|---|---|
| 客户端请求数 | 107 条 | 未重新抓 log；代码侧 **800 个命令号有分支** | 旧矩阵只覆盖当时日志见过的命令 |
| 缺口数 | 59 条 ❌ | **0 条**（`_UNSUPPORTED_ACTION_CMDS` 与 `_GENERIC_DEFAULT_CMDS` 均已清空） | 旧矩阵的 59 条缺口在 R42–R230 系列轮次中**全部补齐或显式移出** |
| 12836 珍宝商城 | 不实现 | L15784 `if cmd in (12836, 12838, 12842)` **已有分支**（mall_zhenbao.json） | 已实现（IMPLEMENTATION_FALLBACK 数据） |
| 13401/13403 | 缺口 | L10873 `if cmd in (13401, 13403)` 已有 | 已补 |
| 13200 队伍 | 缺口 | L10264 起完整队伍段（创建/退出/解散/信息/大厅/邀请/应答） | 已补 |
| 13300 好友 | 缺口 | L11954 起完整好友段 | 已补 |
| 13402 限购商店购买 | 缺口 | L14974 `if cmd == 13402` 已实现 | 已补 |
| 14000 活动 | 缺口 | L14801 `if cmd == 14000` 已实现 | 已补 |
| 16400 成就 | 缺口 | L17764 `if cmd == 16400` 已实现（chengjiu_progress + 342 条） | 已补 |
| 16601/16605 | 缺口 | L10702 `if cmd in (16601, 16602)`、L15528 `16605` 已有 | 已补（空表，诚实） |
| 16900/16903 | 缺口 | L9967 `16900`、L18228 `16903/16904` 已有 | 已补 |
| 17100 | 缺口 | L9922 `17100` 已有 | 已补 |
| 17600 | 缺口 | L18185 `17600/17601/17602` 已有 | 已补 |
| 18803 | 缺口 | L14771 `18803` 已有 | 已补 |
| 18909 | 缺口 | L9849 `18909` 已有 | 已补 |
| 19400/19406 | 缺口 | L14475 `19400`、L14083 `19406` 已有 | 已补 |
| 19600 签到 | 缺口 | L10108 `19600` 已实现（config_checkin 95 条） | 已补 |
| 20500/20504 | 缺口 | 205xx 段（L10858 `20505`） | 已补 |
| 20800 | 缺口 | L14112 `20800`、L13640–13662 段 | 已补 |
| 30715 | 缺口 | L10775 `30715` 已有 | 已补 |
| 10397 | 有分支但不应答 | L16546 `if cmd == 10397` 仍存在 | 维持"仅记录"设计 |
| 15801 | 设计不应答 | L14050 `if cmd == 15801` 仍存在 | 维持设计 |
| 10001 | 设计不应答 | L9632 仍存在 | 维持 |
| 10300 | 设计不应答 | L16441 仍存在（仅触发补推） | 维持 |
| 仓库 10714 | 标 NO | L16889 `if cmd == 10714` 已有分支 | 已补 |
| NPC 对话 UI | 客户端 setOpenNpc 未定义 | 服务端 15202/15203/15204 分支齐全；**客户端侧问题不在本服** | 服务端已就绪 |
| 战力公式 | 旧矩阵未明确标注 | **CONFIRMED**（power.py 直接读原版权重 AttrPower） | 不是 INFERENCE |
| 战斗数值 | 旧矩阵 §5.4 已标 TEST_ONLY | battle.py 头注仍标 TEST_ONLY/IMPLEMENTATION_FALLBACK | 维持 |
| SQLite 表数 | 旧矩阵未列 | **55 张**（任务背景声称 47） | 已扩充 |
| miniloop 自检 | README 称 44 项 | **实跑 145 项全过** | README 过时 |

---

## 九、结论

1. **mock_server 已从"59 条缺口的演示服"演进为"800 命令号全分支"的高覆盖服**。两个兜底 frozenset 均已清空，仅保留一个默认关闭的 `global_default_sc` 开关；先前审计结论"0 个 unsupported / 0 个 generic 兜底" **CONFIRMED**。
2. **数据库已从 47 张扩到 55 张**，覆盖角色/背包/装备/伙伴/成长族（法宝/魂兽/元神/神器/命格/椅子/翅膀/坐骑/符文/光环/时装）/社交（结拜/结婚/公会）/商业（商城/摆摊）/排行/副本/日常/成就/挂机/投资。
3. **GM 接口非常完整**：44 个 /DSH_ADMIN 动作，几乎每个成长系统都有对应发放/查询/重置旋钮。
4. **配置源丰富**：3535 物品、846 任务、496 礼包、53 伙伴、43 日常、342 成就、231+285+245+245 ≈ 1000 张反构造 JSON。
5. **战力公式是 CONFIRMED 原版权重**（不是 INFERENCE）——但**算出的战力值是否与客户端 UI 一致需 MuMu 运行时取证**（见第十节 V9）；**战斗数值仍是 TEST_ONLY**（APK 无怪物 HP/攻防/掉落数据）——这两个标记在代码里都明确写了，与旧矩阵一致。**依新硬约束，所有 TEST_ONLY/占位/未上屏验证的数值系统一律标"⚠ 需 MuMu 运行时取证"**。
6. **miniloop 是可靠的回归基座**：145 项自检全过，回环覆盖登录→建角→进场景→任务→打怪→掉落→提交→奖励→背包；但自检只验证"SC 结构严格合规格"，**不验证数值真实性**（miniloop 的 MON_STATS/KILL_REWARD 同样 TEST_ONLY）。
7. **主要 UNKNOWN**：技能学习/升级、魂骨、增幅、聊天频道实时转发、公会本体（多张表 0 行）——这些在代码里有命令号分支但具体业务逻辑未在本次只读扫描中深入；要判定需进一步阅读对应 handler 主体或运行时验证。
8. **Phase 1 第一项前置任务**：搭 MuMu 1.4.11 + mock_server 联调环境（见第十节）。在该环境跑通前，本报告所有"数值类"结论只能算 `CONFIRMED by code`，不能算 `VERIFIED runtime`。

---

## 十、等 MuMu 环境就绪后需补抓的运行时数据清单（Phase 1 前置）

> **状态：未完成 / 待办。** MuMu 12（D:\MuMuPlayer）实例 0 已运行，adb 127.0.0.1:16384（设备 22041211A，Android 12）；已装 1.3.0 与 1.4.9；**1.4.11 补丁包（`patched\jstm_1411_fakelogin_aligned.apk）尚未装入**。下表所有项均为 Phase 1 第一项前置任务。

### 10.1 环境搭建

| # | 任务 | 状态 | 产出 |
|---|---|---|---|
| E1 | 把 1.4.11 补丁包装入 MuMu（`adb install -r patched\jstm_1411_fakelogin_aligned.apk`） | ☐ 待办 | 设备上 com.shiyue.dldl.ewan 1.4.11 可启动 |
| E2 | 启动 mock_server（9000/8080）+ URL 注入（`url_config_ewan.lua` 指向 PC IP） | ☐ 待办 | 客户端能连到 mock_server |
| E3 | 抓首包：1110 登录、10102/10103 登角、10200/10201 进场景 | ☐ 待办 | tcp.log 全量 |
| E4 | 写一个 `tools/mumu_capture.py`：用 adb logcat + tcp.log 双侧对齐 | ☐ 待办 | 自动取证脚本 |

### 10.2 关键命令 CS/SC 实值抓取

| # | 命令 | 要抓的字段 | 当前实现 | 差距 |
|---|---|---|---|---|
| R1 | 1110 登录 | account/token/platform/sign 全表 | 只取 account，其他仅记录 | 鉴权语义未验 |
| R2 | 10102/10103 登角 | code 约定、rid/srv_id/name | 已实现 | code 字节序需对照 |
| R3 | 10200 进场景 | scene_id/code/x/y | 已实现 | 客户端是否接受 code=0 |
| R4 | 10201 场景格子 | roles/npcs/mons/elems 字段实值 | 已实现 | NPC 摆位是否与客户端期望一致 |
| R5 | 10301/10302/10303/10304 | 角色名/货币/属性数组/战力 | 已实现 | **战力值 vs UI 显示** |
| R6 | 10204 移动 | x/y 权威回包 | 已实现 | 四方向实测 |
| R7 | 12400 任务列表 | 任务行实字段 | 已实现 | 任务进度条 |
| R8 | 12403 提交 | 奖励 award_assets 实值 | 已实现 | 奖励是否真到账 |
| R9 | 20002 战斗 | 整场 20010/20012/20013/20020/20023 帧 | battle.py | **怪物 HP/攻防/伤害/暴击** |
| R10 | 10502 背包 | 物品行字段 | 已实现 | bag_code 与页面对应 |
| R11 | 12801/12805 商城 | 商品列表/购买扣币 | 已实现 | 价格/币种映射 |
| R12 | 10500 背包推送 | bag_code 与 items | 已实现 | 客户端即时刷新 |

### 10.3 必须用 MuMu 实抓才能标定的数值（当前全是 TEST_ONLY/占位）

| # | 数值 | 当前来源 | 标定方法 |
|---|---|---|---|
| V1 | 怪物 HP / 攻击 / 防御 | battle.py `MON_STATS`（TEST_ONLY） | 实抓 20010 fighter_info_list.hp_max 与 20013 magic_list.change_hp 反推 |
| V2 | 暴击率 / 抗暴 / 命中 / 躲闪 | 未实现 | 抓 20012 round 帧统计 hit/miss |
| V3 | 伤害公式 | battle.py `calc_damage()`（IMPLEMENTATION_FALLBACK） | 用 V1 数值 + 多次战斗帧回归 |
| V4 | 击杀经验 / 金币 | battle.py `KILL_REWARD`（TEST_ONLY） | 杀怪前后 10302 exp/coin 差值 |
| V5 | 掉落物品 bid/数量 | battle.py `FALLBACK_DROPS`（TEST_ONLY） | 杀怪前后 10500 推送与 10502 背包差 |
| V6 | 装备属性数值 | item_config.json（APK 反构造） | 穿脱装备前后 10303 attr 数组差 |
| V7 | 强化/升阶属性增量 | 未独立实现 | 客户端强化按钮前后 10303 差值 |
| V8 | 伙伴属性/战力 | _partner_base.json（53 个） | 伙伴上阵前后 10304 战力差 |
| V9 | 战力公式权重 | power.py `AttrPower`（CONFIRMED 反构造） | 客户端 UI 战力数字 vs role_power() 算出值 |
| V10 | 经验表 exp_max | config.json 静态 | 客户端经验条分母 |
| V11 | 翅膀/坐骑/魂兽/元神/神器/命格/法宝每阶属性 | cfg_kconfig 反构造 | 每阶穿戴前后 10303 差值 |
| V12 | 阵法属性 | role_form + config_formation | 上阵前后 10303 差值 |

### 10.4 与 mock_server 当前实现的差异清单（待抓后填）

> 抓完 R1–R12、V1–V12 后，把"客户端实际收到 vs mock_server 发出"逐字段比对，落盘到 `analysis/1.4.11/runtime_diff_roundN.md`。本表当前为空，待 Phase 1 填充。

---

*报告完。所有行号基于 2026-10-02 快照的 mock_server.py（18,506 行）。*
