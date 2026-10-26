# mock_server 服务端梳理与除错（2026-10-17）

> 范围：`server/` 整包（重点 `mock_server.py`）
> 方法：AST 结构比对（含 docstring 归一）+ `ruff`(pyflakes) + 运行期实证 + 可复跑门禁
> 备份：`server/mock_server.py.bak_audit_*`、`*.bak_const_*`、`*.bak_converge_*`

---

## 〇、结论

`mock_server.py` 的"拆模块"重构**原来是半途状态**：顶部 `from <模块> import ...` 接进搬家实现，
文件后半又用同名 `def`/赋值重定义了一遍，把模块实现遮蔽掉。本轮把它**收敛干净**：

| 指标 | 修前 | 修后 |
|---|---:|---:|
| 被遮蔽的导入名 | 46 | **0** |
| 顶层 def/class | 372 | **326** |
| 文件行数 | 20,212 | **19,593**（−619 行重复/死代码） |
| `ruff --select F`（活代码，排除 backup） | F821 **4** · F811 46 · F401 428 · F841 49 | **All checks passed** |
| `tools/audit_mock_server.py` | SAFE 22 / DIVERGENT 24 | **SAFE 0 / DIVERGENT 0 / BAD_IMPORT 0** |

顺带修出 **4 个真 bug**（都不是风格问题）：`_sc_defined()` 恒假、10511 换装必失败、
`ROLE_DEFAULTS.face_id` 退回 0（头像空白）、`aoi.AOI._tower_of()` 一调用就 NameError。

---

## 一、怎么收敛的（46 → 0）

第一步按 **AST 完全等价**（含 docstring）判定：22 个可安全删（18 等价 + 4 死代码）。
第二步把 docstring 也归一掉（先剥 docstring 再比 AST）⇒ **又 16 个其实行为等价**
（`is_valid_item` 23 处、`role_power_of` 19 处、`build_10301/10302`、`level_*`、`item_*`、
`db_init_equip`、`db_store_init`、`build_equip_items`… 差异只在注释/文档串）⇒ 也删。
第三步剩下 **8 个真分叉**，逐个 `ast.unparse` 出纯代码差异人工判断：

| 函数 | 判定 | 依据 |
|---|---|---|
| `role_state` | **模块更新** | 模块带 R100 的 `practice_exp` 回填；本地缺 |
| `_sc_to_db_updates` | **模块更新** | 模块带 `srv_id`；本地是加 srv_id 之前的旧版 |
| `build_10303` | **模块更新** | 模块多算 `role_power`；本地缺 `power` 字段 |
| `add_role_exp` / `apply_level_attr_growth` | **模块更新** | 模块用函数内 lazy import（`level.service` 里必须如此才不循环依赖） |
| `db_bag_add` | **模块更新** | 模块 lazy import `is_valid_item` + `_time` 别名，自足 |
| `build_bag_items` | **模块更新** | 模块 `it.get(intensify_lev,0)`；本地把强化等级**硬编码 30** 并夹带 D2 过滤 |
| `role_attr_dict` | **本地更新 ⇒ 回灌** | 本地多一段从 `cfg['skills']` 回填 `practice_exp`（bid=10822）；已搬进 `attribute.service` |

7 个"模块更新"直接删本地副本（行为与 dispatch handler 一致，等于把兜底链对齐到正确实现）；
1 个"本地更新"用 `tools/converge_shadowed.py` 回灌进模块（带自由变量依赖检查）。

---

## 二、修掉的真 bug（4 个）

| # | 位置 | 症状 | 修法 |
|---|---|---|---|
| 1 | `mock_server._sc_defined()` + 2 处未开放应答守卫 | 直接读 `_SC_FIELDS_CACHE` —— 该名字随 `_sc_fields` 搬家时被注释掉 ⇒ `try/except` 吞掉 NameError ⇒ **`_sc_defined` 恒 False**；两处守卫 ⇒ 本该"明确回失败"的命令**静默无应答** | `protocol/fields.py` 新增公共判定 `has_sc_definition(cmd)`（缓存是模块私有且会被 `global` 重绑，外部不能 from-import）；3 处改调用 |
| 2 | `mock_server` 10511 换装 | `slot = equip_slot_for(...) if eqm_item_id == 0 else None` ⇒ 换装时 slot 恒 None，被"非装备⇒拒绝"命中 return ⇒ **换装永远失败**，后续换装代码不可达；且调用了**从未定义**的 `db_equip_free_slot` | slot 一律按**新物品**算；旧装备按自身槽取下回包；目标槽原有装备也取下回包（防 `db_equip_put` 覆盖丢装备）；新增 `inventory.service.db_equip_free_slot()` |
| 3 | `mock_server` 的 `ROLE_DEFAULTS` 本地重定义 | 本地是旧版：`face_id: 0`，而模块已是 **100**（项里头像空白的修复）⇒ 任何走到本地常量的路径角色头像会退成空白 | 删掉本地重定义（4 个常量：`ROLE_DEFAULTS`/`BAG_MAIN`/`STORAGE_CODE`/`LEVEL_ATTR_GROWTH`，后三者值一致） |
| 4 | `aoi.AOI._tower_of()` | 函数体用 `t` 但从没定义（`t = self.tower_size` 被错写在隔壁 `_towers_in_range` 里，而那里用不到）⇒ **一调用就 NameError**；`mock_server` 里 `import aoi as aoi_mod` 是真在用的 | `_tower_of` 补上 `t = self.tower_size`；删掉隔壁的无效赋值。实测 `AOI._tower_of(100,250) = (12,31)`（tower_size=8） |

另外清掉：`gem/service.py` 里重复的 `gem_attrs`（两份都返回 `{}`，删前者）、
`mock_server` 死赋值 `chain = mission_chain(...)`、`role/handler` 拼了却不下发的 `out`、
`partner` 的占位 `power_before = 0`、以及 5 处未用变量。

---

## 三、工具（都可复跑）

| 工具 | 作用 |
|---|---|
| `tools/audit_mock_server.py` | 结构审计 + **门禁**：`SAFE`（AST 等价/0 引用）/`DIVERGENT`（行为不同，含 `MODULE_WINS` 白名单）/`BAD_IMPORT`；`--apply` 备份后删除可删副本并 py_compile 复检。当前 `结论: PASS` |
| `tools/converge_shadowed.py` | 把"本地更新"的函数**回灌**进模块（含自由变量依赖检查、双备份、编译失败自动回滚）：`--list <name>` / `--apply <name>` |
| `ruff.toml` | 新增：`exclude = ["server/backup", ...]` —— 40+ 份历史快照不再污染 lint（F821/F811 的 150+ 命中原本全在快照里） |

---

## 四、剩余（已清零 / 无需再动）

* 遮蔽（F811）：**0**；未定义名（F821）：**0**；未用导入（F401）：**0**；未用变量（F841）：**0**
  —— `ruff check server --select F` → **All checks passed**（`server/backup` 已排除）。
* 仍存在的**设计层面**事实（不是缺陷，仅登记）：
  1. `dispatch.handle()` 的语义是"已注册 handler 抛异常 ⇒ 落回旧 if 链" ⇒ **旧 if 链不能删**，
     它是兜底网；本轮已让旧链与模块实现同源，兜底才会给出和主路径一样的结果。
  2. **快照已物理移出包目录**（2026-10-17 补做）：`server/backup/` 里 47 份代码快照
     （43 个 `.py` + `.py.bak_*` + `observer.lua.bak_*`）已搬到 **`archive/server_snapshots/`**
     （附 README 说明用途与回滚方法）；`server/backup/` 只留**数据类**备份
     ——`schema_golden.sql`（`persistence/schema.py` 直接读，位置不能动）、`roles*.db`、
     `config*.json`、`fields_json_*.json`、`replay_before.json`。
     ⇒ `python -m compileall server` 不再编译快照（包内 `.py` 由 248 → **201**）。
  3. `world/` 下是一组实验模块（依赖 `mock_server`），本次只做了"未用变量/导入"级别的清理。

---

## 五、第二轮深挖：运行期报错 + 热路径健壮性（2026-10-17 续）

### 5.1 日志里的真实报错（按内容聚合，共 10 条 `!!`）

| 报错 | 条数 | 结论 / 处置 |
|---|---:|---|
| `账号鉴权失败` / `本区已有角色` / `跨区登录被拒` | 6 | **我自检的预期拒绝**，非缺陷 |
| `_dedicated_cmds failed: NameError("name 're' is not defined")` | 1 | **历史报错（10:50，早于本轮修改）**；现版本函数内已 `import re as _re`，实测 `_dedicated_cmds()` 提取 **1392** 条命令 ✔ |
| `achievement load failed: AttributeError("'str' object has no attribute 'get'")` | 2 | **真 bug，本轮修**（见 5.2） |

### 5.2 修：成就表"一条坏数据 → 342 条全丢"

`achievement/service.py::_load_all()` 原来逐条 `(it or {}).get('hash')`，只要有一条不是 dict
（配置半写入/旧结构/写坏）就抛 `AttributeError`，被外层 `try` 吞掉后 **整个成就表返回空**
（成就面板全空）。改为**单条形状不认识就跳过、不影响其它条目**。
实测：正常配置 342 条；构造一条 `"BROKEN"` 字符串条目后仍能载入其余 2/3 条。

### 5.3 修：单条命令异常会掐断整条 TCP 连接（重连风暴的根）

`TcpHandler.handle()` 的收包循环里原来是裸的 `self._reply(cmd, body)`：任何 handler 未捕获的
异常都会冒泡到连接级 `except Exception` ⇒ 记一行 `--- error:` 然后**关闭连接** ⇒
客户端立刻重连（这正是之前观测到的"重连风暴 / 进图半成品"的机制之一）。
现在**逐条兜住**：`try: self._reply(...) except: 落完整堆栈 + 连接保持 + 后续命令照常处理`；
连接级异常也补上了 `traceback.format_exc()`（原来只有 `%r`，定位不到行号）。

### 5.4 检查过、**未发现**问题的类别（留档，避免重复审）

| 类别 | 结论 |
|---|---|
| 可变默认参数 / 循环闭包晚绑定 / `raise ... from` | `ruff B006,B023,B904` → 无命中 |
| SQL 用 f-string/`%` 拼用户数据 | 无命中（全部参数化 `?`） |
| 裸 `except:`（E722） | 无命中（都是 `except Exception`） |
| `assert` 当运行期校验（`-O` 下会失效） | 无命中 |
| 无界缓存 | 只有 3 个惰性常量表（`_TALENT_LIST_CACHE`/`_LEVEL_TABLE`/`_CJ_MAP`，一次性载入） |
| SQLite 连接池 | 线程本地复用、显式不关闭、`db_release` 仅回滚未提交事务（设计如此） |
| 帧写入溢出 | `w_u8/w_u16/w_u32` 均做 `& 0xFF/0xFFFF/0xFFFFFFFF` 掩码 |

> 遗留**设计级**提示（不算 bug，未改）：`db_release()` 会回滚**本线程**未提交事务 ⇒ 同一线程里
> "A 开了事务 → 调 B → B 调 db_release" 这种嵌套会把 A 的写回滚掉。当前代码都是"写完就 commit"，
> 未发现实际踩中；以后若加长事务，需要改成显式事务管理器。

---

## 六、验证（本轮实测）

| 项 | 结果 |
|---|---|
| `python -m compileall server` | 退出码 0（不再包含 47 份快照） |
| `ruff check server --select F` | **All checks passed**（快照已移出；`ruff.toml` 仍 exclude `server/backup` + `archive` 作双保险） |
| `ruff check server --select F,B006,E722` | **All checks passed** |
| `tools/audit_mock_server.py` | `SAFE=0 ｜ DIVERGENT=0 ｜ BAD_IMPORT=0 ｜ PASS` |
| 服务端重启 + 冒烟 | 就绪（HTTP 200 / TCP 1199 回包） |
| 账号·区服自检 `verify_3zones_accounts.py` | **PASS 23/23** |
| 活服端到端 `verify_3zones_live.py` | **PASS 15/15**（本轮新增 10301/10302/10303 实际出包：116/122/198 字节） |
| 快照搬迁后 `schema.py` | `table_count_baseline=55`、`golden_schema_path()` 仍可读（True） |
| 常量抽查 | `ROLE_DEFAULTS.face_id = 100`（旧本地值 0）· `BAG_MAIN=1` · `STORAGE_CODE=4` · `LEVEL_ATTR_GROWTH.atk_s=12` |
| 行为抽查 | `role_state` → `rid=1001 srv_id=1 lev=70 face_id=100`；`AOI._tower_of(100,250)=(12,31)` |
| `has_sc_definition` | `1110=True / 10999=False / 30715=True`（空字段也算有定义） |
| `db_equip_free_slot` | `rid=1001`（已穿 1..6）→ **7**；`rid=2001` → **1** |

---

## 七、四系统自检：伙伴 / 背包 / 战斗 / 魂技（2026-10-17 第三轮）

### 7.1 工具（新增，都可复跑、都自带清理）

| 工具 | 作用 |
|---|---|
| `tools/verify_systems.py` | **语义自检**：临时建号 → 登录/建角/进角色 → 逐系统校验 → **删号清理**。判据不只看"有没有回包"，而是**与服务端模块自己的输出做字节级比对**（如 `11215` vs `partner.service.build_panel_11215`）+ **DB 前后一致性**（穿装备不能凭空多/少物品） |
| `tools/probe_silent_cmds.py` | 静默命令实测：逐条发命令，报告"有没有回包/多少字节" |
| `tools/probe_battle_stream.py` | 战斗链**逐帧**观察（带时间戳），确认服务端定时器推回合 |
| `tools/audit_cmd_coverage.py` | 跨全部轮转日志统计"请求了但没回包"的命令（⚠ 历史日志，结论必须用上面的探针现场复核 —— 本轮就误判过一次） |

### 7.2 结果：**16 PASS / 0 FAIL / 0 SKIP**

| 系统 | 实测结论 |
|---|---|
| **伙伴** | `11200` 面板容器 6B；`11215` partner_list **2546B 与 `partner.service.build_panel_11215` 字节一致**；`11206` 扩容回 code=1；`owned_map(rid)` 与 DB 一致 |
| **背包** | `10502` 条目数 **= DB 真值**；`10511` 穿装：背包 2→1、装备 0→1、**被拒的礼盒仍在背包**；`10511` 换装：新装备进槽、旧装备回背包；`10502` 复读与 DB 一致 |
| **战斗** | `CS_20002(mon=20001)` → `SC_20002 code=1` + `SC_20010` 135B；**服务端定时器每 2.5s 自动推 `20012`/`20013` 回合**（逐帧实测 +3.0/+5.5/+8.0/+10.5s）；客户端**不发** `CS_20014`（服务端注释与实测一致） |
| **魂技** | `10622` 已学技能列表**与 `skill.service.build_10622` 字节一致**；给金币后 `learn(10020)` 成功（扣 10 金）且 `10622` 即时反映；`10601` hero_list 属性表 14B |

### 7.3 本轮修掉的问题

| # | 问题 | 影响 | 修法 |
|---|---|---|---|
| 1 | **`10511` 穿非装备会吞掉物品** | 数据丢失：礼盒等非装备被拒（code=0）**但已先从背包删掉**，玩家物品人间蒸发 | 把"从背包取走"挪到**校验通过之后**（先校验、后动数据） |
| 2 | `equip_slot_for` 对**查不到类型**的物品（`item_type_of→None`）回退"找一个空槽" | 未知物品照样能占装备位（注释里明确要防的"礼包占武器位"） | 配了 `equip_type_slot` 时，类型不在映射内**或查不到**一律拒绝 |
| 3 | **`CFG` 只在 `mock_server.main()` 里装配**（导入时 `CFG == {}`） | 自检/脚本读到的一切配置都是默认值 —— 本轮据此**误判过一次** `equip_type_slot`（以为配置缺失，实际是工具没加载） | 抽出 `build_cfg()` / `init_db()` / `publish_cfg()`，主程序与工具**共用同一份装配逻辑** |

### 7.4 未覆盖 / 下一步（按优先级）

1. **战斗结算链**（`20020` 胜负 / `20023` 明细 / 掉落）未观测到：测试怪 20001 有 1950 HP、每回合只掉 ~57 ⇒ 约 35 回合、~90 秒。**下一步**：把观察窗拉到 120s 跑一次完整战斗，或临时调高伤害/降低怪血，确认结算与 `battle_test_drop` 掉落真的落地。
2. **伙伴养成链**：本号 0 个伙伴 ⇒ `feed`（升级/经验）、`partner_shenqi_cost`/`partner_talisman_cost`、战力贡献**全未测**。**下一步**：先给一个伙伴（`11216` 或直接写 `role_heros`），再跑 feed 与战力对比。
3. **魂技联动**：`learn/upgrade` 已通，但"技能进战斗"（`20010` 里的 `skill_list`）与天赋树（105 条 `config_skill_talent`）未验证。
4. **背包其余分支**：`10552` 扩容、仓库（bag_code=4）、`10557` 删除、堆叠合并/拆分、`10500/10503` 推送一致性。
5. **战斗其余命令**：`20008`（自动战斗开关）/`20009`（选技能）目前**只记日志不改编排**；`20001/20003/20004`（角色对战/测试战斗/切磋）按设计回失败 —— 要不要实现属于产品决策。
6. **工程性**：把 `verify_systems.py` + `verify_3zones_*.py` + `audit_mock_server.py` 串成一个 `tools/selfcheck.ps1`，每次改完一键跑；`db_release()` 的"回滚本线程未提交事务"在长事务下会吃掉别人的写（见 §5.4 提示）。

---

## 八、第四轮深挖：覆盖矩阵 + 99 条未测命令冒烟 + 语义深检（2026-10-17 续）

### 8.1 两个新工具

| 工具 | 作用 |
|---|---|
| `tools/audit_system_coverage.py` | **系统覆盖矩阵**（**只认活代码**：AST 扫 `@register(N)` 与真实 `if cmd == N`，扫**整个 server 包**）。输出"协议声明 / 活代码处理 / 客户端真发过 / **未测**"。为什么必须 AST：`mock_server.py` 里大量**注释掉的旧 if 块**会让正则把"已处理"全判成 ✔（本项目已第二次踩这个坑） |
| `tools/smoke_systems.py` | **未测命令批量冒烟**：把"协议有 CS + 活代码处理 + 客户端从没发过"的命令逐条打一遍（临时号、自清理），按"有无 SC 定义"区分**真沉默**与**通知型静默**，并抓 `!! cmd=N 处理异常` |

### 8.2 覆盖矩阵（四系统）

| 系统 | 协议 CS | 活代码处理 | 冒烟前"客户端发过" |
|---|---:|---:|---:|
| 伙伴 112xx | 26 | **26** | 3 |
| 背包 105xx | 61 | **61** | 6 |
| 战斗 200xx | 19 | **19** | 4 |
| 魂技 106xx | 10 | **10** | 4 |

⇒ 服务端**声明**全覆盖，但真机只跑过其中少数 ⇒ 剩下的都是"从没被触发过的分支"。

### 8.3 冒烟结果：99 条未测命令 → **零异常**

`REJECT(code=0) 84 ｜ OK(code=1) 12 ｜ SILENT 3`，其中 3 条静默里
`20011`/`20014` 协议里**没有 SC 定义**（通知型，沉默正确），**`20008`/`20009` 有 SC 定义却沉默 ⇒ 真缺陷**（见 8.4）。

### 8.4 本轮修掉的问题

| # | 问题 | 影响 | 修法 |
|---|---|---|---|
| 1 | **`20008`/`20009` 有 SC 定义却只记日志不回包** | `SC_20008{id,flag}` / `SC_20009{skill_id}` 都有定义，客户端"自动战斗/选技能"后会落进未知命令分支或干等 | 两者改为**回显**（id=0+flag / skill_id 原值），编排仍由服务端定时器驱动 |

### 8.5 语义深检：**25 PASS / 0 FAIL / 0 SKIP**（`tools/verify_systems.py`）

新增覆盖（都带 DB 前后一致性判据）：

* **伙伴养成链**：`11216` 兑换（`role_heros` 真出现 bid）→ 面板仍与模块**字节一致** → GM 端点喂食（金币 500000→498000，**lev 1→5，exp 0→40**）；
* **背包分支**：`10552` 扩容（DB 容量 +5）→ `10557` 删除（物品真移除）→ `10554` 入仓（**仓库 0→1 且背包已移除**，无丢失）；
* **战斗全链**：`20002`→`code=1` + `SC_20010` → **服务端定时器自动推回合 `20012/20013` → 结算 `20020/20023`**（实测到了结算！）→ `20008/20009` 回显；
* **魂技**：`10622` 与模块字节一致、`10601` 属性表、`learn` 后即时反映。

### 8.6 下一步

1. **属性/等级 103xx（未测 25 条）**：`10304/10306`（属性表）、`10320~10334`（升星/洗练类）、`10388~10391` —— 是本轮之后**最大的覆盖空白**，建议照 `smoke_systems.py` 先冒烟、再按系统写语义检查。
2. **任务 124xx（未测 33 条）**：接/交/放弃/环任务，涉及 DB 写入，值得优先。
3. **场景 102xx（未测 15 条）**：`10205/10206/10207`（寻路/传送类）等。
4. **战斗奖励**：本轮已到 `20020/20023`，但**掉落/经验/金币是否真落库**还没判据 —— 建议给战斗结算加一条"战前战后资产差"的断言。
5. **伙伴战力贡献**：喂食已通，但对 `10303 skill_list`/战力字段的贡献未断言（`partner.service.feed` 内部 `apply_delta` 的效果）。

---

## 九、背包系统专项：缺格子 / 空格显示 / 整理刷新缺失（2026-10-17 第五轮）

用户报障三条：**空格显示、缺格子、整理刷新功能缺失**。三条全部定位到服务端，且都能给出
"客户端真机已收到什么"的证据。

### 9.1 根因（三条症状 → 三个真问题）

| 症状 | 根因 | 依据 |
|---|---|---|
| **缺格子**（格子太少/扩容不变多） | `SC_10510{code, volume, open_volume}`（**格子最大值/已开启格子数**）**服务端从未推送过** —— 全量 `tcp*.log` grep `<< 10510` = **0 条**；而客户端格子数正是取自它（文档 `analysis/1.4.9/item/inventory_protocol_matrix.md` §3.8/§8.3：**无 CS、纯 S→C、需下发**；客户端 bc#42 `handle_10510`，配套 `getRemainCellNum`） | 全量日志 0 条 + 协议文档 §8.3 |
| **空格显示**（格子之间空洞） | ① `db_bag_delete()` **不压紧 `pos`** ⇒ 删除后位置留洞（1,3,5…）；② 删除后只推 `SC_10500`（**增量添加**），它永远不会移除客户端里的旧行、也不改位置 | `db_bag_delete` 源码 + `SC_10500 → addItemInBagCode`（反汇编确认） |
| **整理刷新缺失**（点整理顺序/数量不变、删掉的还在） | `10509` 原来推的是 `bag_push_frames()`（= `SC_10500` 增量添加）—— **不会告诉客户端"位置变了"**；而**主动推 `SC_10502` 会被客户端忽略**（只在它自己发 `CS_10502` 后才处理 `initItemList`） | 文档 §8.3 把 10501/10503/**10508**/10510/10543 列为"服务端主动推送"型，10502 不在其列；本文件 10554 块还留着 R 轮次的实测记录"原实现推的是 SC_10502…主动推的会被忽略" |

> 我第一版按"推 10502 = 清空重建"改了穿装/卸装两处 —— 查证文档与既有实测后**已回滚**
> （那两处物品消失本来就由紧跟的 `SC_10503` 交代）。教训记在 `bag_push_frames()` 的 docstring 里。

### 9.2 修法（全部服务端，**客户端不用重装 APK**）

| 改动 | 位置 | 说明 |
|---|---|---|
| 新增 `build_10510 / push_10510` | `inventory/service.py` | 容量取 DB `bag_volume`（默认 `bag_volume_default`，已补回 config = **200**，依据同文件 `volume_note`"统一设为 200"）；字段 u8 ⇒ 夹 0..255 |
| 三处推送 10510 | ① 进角色（10102/10305 之后）② **每次 10502 应答后** ③ `10552` 扩容后 | 客户端每次打开/切囊都会要 10502 ⇒ 顺带拿到格子数 |
| 新增 `db_bag_repack()` | `mock_server.py` | 压紧 pos 并返回 `[(item_id,new_pos),…]`；`db_bag_compact()` 保留（只回计数） |
| 新增 `push_10503 / push_10508` | `inventory/service.py` | `SC_10503{code,del_ids_arr}`（哪些物品没了）、`SC_10508{code,pos_up_arr(item_id,new_pos)}`（新位置） |
| **删除**流程 | 10557 | 真删 → **压紧 pos** → 推 `10503`（删除）→ 推 `10508`（位置）→ 推 `10510` → 回 `code=1` |
| **整理**流程 | 10509 | 压紧 pos → 推 `10508`（新位置）→ 推 `10510` → 回 `code=1` |
| 容量默认 | `config.json` | 新增 `bag_volume_default: 200` + 说明；`db_get_bag_volume` 默认由 0 改为它（原来新角色 **0 个格子**） |
| 下沉 | `db_init/get/set_bag_volume`、10510 构造与推送 → `inventory/service.py` | 因为 `10502` 的 handler 在 `inventory/handler.py`，而本包有"禁止反向 import mock_server"的红线 |

### 9.3 真实客户端证据（emulator-5554，本轮修复后）

```
（客户端进角色）
  << 10510 SC_10510 bag_code=1 volume=200 open=200 (9 bytes)
  << 10500 SC_10500 bag push(增量添加) bag_code=1 items=7
（客户端逐个请求 12 个囊：bag_code = 1,2,3,4,5,6,7,8,12,13,16,17）
  >> cmd=10502 …  << 10502 SC_10502 bag_code=6 items=0  →  << 10510 volume=200 open=200
  >> cmd=10502 …  << 10502 SC_10502 bag_code=7 items=0  →  << 10510 volume=200 open=200
  >> cmd=10502 …  << 10502 SC_10502 bag_code=8 items=0  →  << 10510 volume=200 open=200
  …（bag_code=5 用 DB 里已有的 6 格：volume=6 open=6）
```

### 9.4 自检新增断言（`tools/verify_systems.py` 背包段 11 项全过）

* `SC_10510` **随 10502 下发且数值 == DB**（`volume/open=35（DB=35）`）；
* `10557` 删除 → 收到 **10503 + 10508**，且 DB `pos` 压紧为 `[1,2]`；
* `10509` 整理 → 收到 **10508**，`pos` 压紧为 `[1,2]`（用例会先**人为造一个空洞**，否则"无变化就不推"是正确行为，第一版自检在这里误报过）；
* 原有：条目数 == DB、拒绝非装备且**物品不丢**、穿装/换装守恒、10552 扩容、10554 入仓。

> 全部回归：`ruff -F,B006,E722` 全绿 ｜ 结构审计 PASS ｜ 账号·区服 23/23 ｜ 活服 15/15 ｜ **四系统 28/28**。
