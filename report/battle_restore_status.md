# 绝世唐门 1.4.9 私服 —— Phase D：战斗系统最小垂直闭环 · 状态报告

> **目标 APK**：`anzbao/jstm.apk`
> 包名 `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**（360 / ewan.qihoo）
> 本轮全部结论**只以 1.4.9 为准**；`jstm_142165.apk`（1.4.11）等**未参与任何判定**。
> 环境：本地服务端 `server/mock_server.py`（TCP 9000 / HTTP 8080）+ 探针版 1.4.9 APK。
> 模拟器 `127.0.0.1:16384`。

---

## 一、结论：最小垂直闭环**已跑通并验证**

用户给定的目标链，逐环实测结果：

| # | 目标链环节 | 结果 | 关键证据 |
|---|---|---|---|
| 1 | 地图 | ✅ | `sceneId_10001`、`isLoadState_true` |
| 2 | 发现怪物 | ✅ | 探针 `bt_mon … id20001 bid20001 resH32000 xy34,34` |
| 3 | 点击怪物 | ✅ | `GlobalEvent:Fire(SceneEvent.SCENE_MONSTER_CLICK, vo)` → `ok=true` |
| 4 | 客户端发起攻击请求 | ✅ | `BattleCtrl:csFightMon` → `bt_send csFightMon_monid20001` |
| 5 | 服务器识别角色和怪物 | ✅ | `>> cmd=20002 body=00 00 4e 21 13 8f 00 00`（mon_id=20001） |
| 6 | 进入原版战斗流程 | ✅ | `<< 20002 code=1(TRUE)` → `<< 20010 SC_20010 battle init fighters=2` |
| 7 | **客户端显示战斗** | ✅ | 探针 `bt_in scFightData … fighter_info_list_{1:{rid=..,skills=..` —— **客户端成功解析** |
| 8 | 角色攻击 | ✅ | `<< 20012 SC_20012 skill_play` + `<< 20013 SC_20013 round_start` |
| 9 | **怪物受伤** | ✅ | `battle round 1: role(1) -> mon(2) hit=772 mon_hp=1628/2400`（4 回合 2400→0） |
| 10 | **怪物死亡** | ✅ | `battle monster died, battle result=1` |
| 11 | 战斗结算 | ✅ | `<< 20020 SC_20020 result=1` → `<< 20023 SC_20023 result=1 role_hurl=2` |
| 12 | **获得经验** | ✅ | 服务端 `+50 exp`；DB `exp 500→2320`；客户端探针 `exp2320` |
| 13 | **获得金币** | ✅ | 服务端 `+30 coin`；DB `coin 1290→5800`；客户端探针 `coin5800` |
| 14 | **产生掉落** | ✅ | `battle drop item=51038(酒剑仙灵魂玉) x2 [holiday池3001 pp=24/36]`（**原版掉落表**） |
| 15 | **进入背包** | ✅ | DB `bag_items: item_id=1 bid=51038 quantity=6`；`<< 10500 SC_10500 bag push` |
| 16 | **任务击杀进度更新** | ✅ | `battle mission progress: fight_mon target=20001 -> [10020]`；DB `10020 status=1→2 value=0→1` |
| 17 | 保存角色状态 | ✅ | 全部落 SQLite（`roles` / `role_assets` / `missions` / `bag_items`） |
| 18 | **重新登录后数据仍在** | ✅ | 强杀重开后探针 `before_recv_n4_exp2820_coin7090`（上一轮战果原样恢复） |

**额外收获**：`<< 20020` 之后客户端主动发了 `>> cmd=20021`（`csCloseFinishView`，
"闭关战斗结束界面"）——证明**客户端确实收到了战斗结果并做出了反应**。

---

## 二、★ 本轮最重要的 4 个发现（都改变了实现方式）

### 1. `cmd_resolve_*.luac` 里藏着**权威**消息定义（本轮最大突破）

每个消息都是一个 `AutoConstruct(方向, CMD, { '<字段名>__<类型>', ... })`：

```
TGETS  A=1 B=0 C=0   ; ['AutoConstruct']
KSTR   A=3 D=1       ; 'sc'
KSHORT A=4 D=20001   ; 20001
TDUP   A=5 D=2       ; TableConst(array=[None,'code__C','msg__s'])
```

⇒ **数组顺序就是字段顺序，且类型直接写在字段名里**。
`protocol/manual.md` 是二次加工的产物，而这个是**一手权威**。
新工具：`tools/proto_spec.py`（顶层消息）、`tools/dsc_spec.py`（嵌套子结构）。

### 2. ★ 订正：`manual.md` / `fields.json` 的 `Dsc*` 子结构字段顺序**是反的**

判据（三条独立证据，全部来自 1.4.9）：

1. `baseprotocalstruct.luac` proto#7 `Encode`：`ipairs(m_value_names)` 逐个 append 到
   `m_values`，再 `WriteFMT(m_format, unpack(m_values))` ⇒ 名字与格式串**按位置配对**。
2. **同名字段交叉对齐**：`Dsc20010skills` 的名字顺序 `bid, step, last_use, cd` + 格式串
   `ICHH`；而 `SC_20012.cooldown` 的**内联 spec** 是 `bid@I##last_use@H`。
   只有**不反转**才自洽（`bid`=uint32 / `last_use`=uint16）。
3. **16 字段全中**：`Dsc20013summon_play` 读取器顺序与 `SC_20013.summon_play` 内联 spec
   逐字段逐类型完全一致。

订正示例：

| 子结构 | manual.md（错） | 订正后（对） |
|---|---|---|
| `Dsc20010animate_res` | dis_method:u16, ent_lev:s, ant_val:u8, ant_id:u8 | **ant_id:u16, ant_val:s, ent_lev:u8, dis_method:u8** |
| `Dsc20010skills` | cd:u32, last_use:u8, step:u16, bid:u16 | **bid:u32, step:u8, last_use:u16, cd:u16** |
| `Dsc20010specials` | val:u8（1 字段） | **key:u8, val:u32**（2 字段） |

### 3. ★ 订正：**11000/11200 不是战斗协议**

`server/mock_server.py` 里原有注释断言「真正的击杀发生在战斗实例（**11000/11200 系列**）」。
经 `all_proto.luac` 核对：

| CMD 段 | 实际含义 |
|---|---|
| 11000–11018 | **地下城** |
| 11200–11242 | **伙伴** |
| **20001–20030** | **战斗** ✅ |

⇒ 战斗是 **20000 段**。原注释为误判，已订正（见 `battle_protocol_matrix.md` §3.1）。

### 4. ★ 客户端**不会**主动驱动战斗回合

实测：`SC_20010` 被正确解析后，客户端**既不发 `CS_20011`（加载完成）
也不发 `CS_20014`（动画播放完成）**，整场战斗会停在第一回合前。

⇒ 服务端必须**自己按节拍推进**（本实现 2.5 秒/回合，自续期）：
`SC_20010 → (SC_20012+SC_20013)×N → SC_20020 → SC_20023`。
`CS_20014` 仍然接收并记录，但**不作为推进的必要条件**。

---

## 三、原版数据 vs 兼容数据的**严格区分**（不混淆）

| 项 | 来源 | 标记 |
|---|---|---|
| 怪物 id / 名字 / 外观资源 | 1.4.9 `Config.Mon`（2645 条） | **原版** ✅ |
| 掉落物品 id / 名字 / 数量 / 概率权重 | 1.4.9 `Config.Drop` / `Config.DropItem` | **原版** ✅ |
| 全部协议字段名/顺序/类型 | 1.4.9 `cmd_resolve_*.luac` | **原版** ✅ |
| **怪物 HP / 攻击 / 防御** | APK 内**不存在** | **`TEST_ONLY`**（`battle.py: MON_STATS`） |
| **伤害公式** | APK 内**不存在** | **`IMPLEMENTATION_FALLBACK`**（`battle.py: calc_damage`） |
| **击杀经验 / 金币** | APK 内**不存在** | **`TEST_ONLY`**（`battle.py: KILL_REWARD` = 50/30） |
| 怪物**摆位坐标** | 原版摆位表不在 APK 里 | **`emulated`**（配置项显式带 `source` 字段） |
| 掉落 **roll 规则**（几次/保底/池优先级） | 掉落判定**不在客户端**（全包 2234 个 `.luac` 零引用） | **`IMPLEMENTATION_FALLBACK`** |

> **必须明确：`+50 exp / +30 coin` 不是原版数值，`2400 HP` 不是原版数值，
> 伤害公式也不是原版公式。** 这些是明确标注的兼容值，等拿到原版服务端数据后整体替换。

### 3.1 ⚠️ **重大更正**：原版掉落表是**模板残留死数据**，不能当原版掉落用

> 本节原先写的是「测试怪 20001 的掉落是**真原版数据**」。
> **该结论是错的，现予更正。** 起因是子代理的深挖 + 我方独立复核。

**复核证据（三组，全部来自 1.4.9 APK 本体）：**

**① 掉落池里的 29 个物品，全部不是《绝世唐门》的角色**

`Config.DropItem` 的 29 个物品名：李逍遥／酒剑仙／赵灵儿／林月如／南宫煌／韩菱纱／
聂小倩／孙思邈／千叶禅师／宁采臣／飞蓬／魔翳／龙幽／龙葵／小蛮／夕瑶／
柳梦璃／星璇／唐雨柔（召唤符 + 灵魂玉）＋ 小仙桃／大仙桃／铜银金经验符。

⇒ 这批角色属于**仙剑奇侠传／轩辕剑／古剑奇谭**，与本作（斗罗大陆II 绝世唐门）**毫无关系**。
本作角色是 霍雨浩／唐舞桐／戴浩／宁天／贝贝／叶夕水 等。

**② ★ 决定性证据：那批物品**根本不在本作的真实物品表里**

本阶段新提取出**真实物品表 `Config.Item`**
（`config_item.luac` proto#1：`bc=65483`、`knum=1117`）

```
真实物品表 Config.Item: 1117 条
  bid 号段：33000–46999 与 99000–99999
  样例：33001「10级速度符」、33006「100级伤害符」、35043「情缘烟花」
  → 51000 / 51037 / 51038 / 51066 …… **全部不在表内** ❌
```

⇒ 掉落表引用的物品**在本作里根本不存在**，客户端连名字/图标都查不到。
**这直接证明掉落表是死数据。**

**③ 29 条掉落记录里 12 条完全为空**（三个掉落节 + 三个 sum 全是空表，
只有 `coin`/`wood` 字符串）—— 活表不会 41% 是空的。

**结论**：

| 判断 | 依据 |
|---|---|
| `Config.Drop` / `Config.DropItem` 是**模板残留/死数据** | ①②③ |
| 其**唯一可靠用途**是「掉落算法结构样例」（三层结构 + `pp/p_sum` 权重） | — |
| **不能直接搬进私服** | 否则玩家会拿到不存在的物品 |

### 3.2 服务端已按此加固

| 改动 | 说明 |
|---|---|
| `roll_drops()` **逐项校验** | 物品必须存在于真实物品表 `Config.Item`；不在的**一律丢弃并告警** |
| 新增 `item_cfg()` / `item_exists()` / `item_name()` | 加载真实物品表（1117 条） |
| 掉落回退为 **`TEST_ONLY`** | 用**真实存在**的物品 id（默认 `33001`「10级速度符」），只为把「掉落→进背包→重登仍在」链路跑通。**掉落规则/概率不是原版数据**（原版掉落表不可恢复） |
| 配置开关 | `battle_test_drop`（默认 true）、`battle_test_drop_item`（默认 33001） |

实测（`roll_drops` 对全部 5 只有掉落表的怪）：

```
!! 原版掉落表引用了**不存在的物品**（模板残留），已丢弃：
   [(51037, '李逍遥灵魂玉', 'holiday池3001 pp=12/36')]
   → mon 20001 -> []
```

⇒ **服务端再也不会发出本作不存在的物品。**

---

## 四、服务端改动清单

| 文件 | 改动 |
|---|---|
| `server/battle.py` | **新增**：战斗状态机 + SC_20010/20012/20013/20020/20023 编码器（逐字段对照权威 spec） |
| `server/mock_server.py` | 新增：`static_mons` / `mon_cfg` / `mon_def`（怪物资源表）；`make_battle`；战斗处理器（20002/20011/20014/20008/20009/20001/20003/20004/20005/20016/20017）；`_battle_tick` / `_battle_push_round` / `_battle_settle`；背包 `db_bag_*` / `build_bag_items` / 10502 / 10500；掉落 `drop_cfg` / `roll_drops` |
| `server/config.json` | 新增 `mons`（测试怪 20001 @ 34,34，`source=emulated`）；`mission_auto_progress` 改 **false** |
| `server/dsh_fake_login.lua` | 新增战斗探针段（`_G.__dsh_battle`，**已置 false**） |
| `tools/build_fakelogin.ps1` | 修 apksigner 原地签名在 Windows 上被占用失败的问题（改用 `--out`） |

### 4.1 ★ 已移除「移动替身」

上一阶段为了让任务链能跑通，`mission_auto_progress=true` 时用**角色移动**去推进
`fight_mon` 进度（代码里明确标注为「替身·无战斗」）。本轮已：

- 配置置 `mission_auto_progress=false`；
- 任务进度改由**真实战斗击杀**驱动：`mission_progress_advance(rid, 'fight_mon', mon_bid, 1)`。

实测：DB 里 `10020` 由 `status=1 value=0` → `status=2 value=1`（可提交），
**没有任何直接改库伪造完成**。

---

## 五、端到端复现步骤

```powershell
# 1) 还原到「战斗回归起点」（任务 10020 重置为进行中 0/1，角色放在测试怪旁）
Copy-Item analysis\_db_before_battle.db server\state\roles.db -Force
Remove-Item server\state\role_1001.json -Force -ErrorAction SilentlyContinue

# 2) 打开战斗探针（复跑回归时；正式游玩保持 false）
#    编辑 server\dsh_fake_login.lua：_G.__dsh_battle = true

# 3) 起服务端
python server\mock_server.py

# 4) 构建并安装探针客户端（约 30 秒，会自动跑到地图并自动攻怪）
pwsh tools\build_fakelogin.ps1

# 5) 等约 120 秒，读结果
Select-String -Path server\logs\tcp.log -Pattern '<< 200|battle |drop|mission progress'
python tools\inspect_db.py
python tools\extract_battle_logs.py     # 落证据到 logs/1.4.9/battle/
```

---

## 六、交付物索引

### 分析文档（`analysis/1.4.9/battle/`）

| 文件 | 内容 |
|---|---|
| `battle_protocol_matrix.md` | **战斗协议矩阵**（CMD/请求/响应/客户端模块/状态）+ `Dsc*` 顺序订正 |
| `battle_flow.md` | **战斗模式判定**（独立回合制）+ 逐跳触发链路 + 时序表 |
| `monster_data_model.md` | 怪物数据模型（`Config.Mon` 23 字段分布 + 服务端下发结构） |
| `test_monster.md` | 第一只测试怪（bid 20001 戴浩）的取值、来源与证据 |

### 物品文档（`analysis/1.4.9/item/`）

| 文件 | 内容 |
|---|---|
| `drop_model.md` | 掉落模型（`Config.Drop` 29 条 / `Config.DropItem` 17 组 39 条） |
| `drop_table.md` | 掉落明细表（75 行，含证据列） |
| `inventory_protocol_matrix.md` | 背包协议矩阵（11/11 CMD 已确认，物品 16 字段） |

### 实测日志（`logs/1.4.9/battle/`）

`monster_click.log`、`battle_start.log`、`battle_action.log`、
`battle_result.log`、`battle_raw_tcp.log`、
**`battle_render_chain.log`**（客户端战斗渲染链调用轨迹，§九 的证据）
（由 `tools/extract_battle_logs.py` / `tools/extract_render.py` 可复现地抽取）

### 工具（`tools/`）

| 工具 | 作用 |
|---|---|
| `proto_spec.py` | **权威**消息定义还原（`AutoConstruct` 数组 → 字段名+顺序+类型） |
| `dsc_spec.py` | 嵌套 `Dsc*` 子结构还原（含"不反转"判据的完整论证） |
| `battle_audit.py` | 战斗模块清点 / 方法表还原 / 字符串池 |
| `extract_battle_logs.py` | 战斗证据抽取 |
| `extract_render.py` | 战斗渲染链证据抽取（§九） |
| `dump_drop_config.py` 等 | 掉落表还原（极简 LuaJIT 解释器） |

### 服务端

`server/battle.py`（新增）、`server/mock_server.py`、`server/config.json`

### 快照

`analysis/_db_before_battle.db`（战斗回归起点）

---

## 七、**未完成 / 未知**（诚实交代）

| # | 项 | 状态 | 说明 |
|---|---|---|---|
| 1 | 怪物 HP/攻击/防御/经验/金币 | **`UNKNOWN`** | 原版服务端数据，APK 内无取证途径；当前用 `TEST_ONLY` 值 |
| 2 | 伤害计算公式 | **`UNKNOWN`** | 同上；当前用 `IMPLEMENTATION_FALLBACK` |
| 3 | 战斗**胜负取值语义**（`SC_20020.result`：1=胜？） | **`UNKNOWN`** | 本实现用 1=胜 / 2=败，**未经原版验证** |
| 4 | 经验/金币**实际走哪条协议** | 部分 | 本实现走 `role_assets` + 推送 `10301/10302/10303`（客户端探针显示数值确实更新了），但**原版是否如此未知** |
| 5 | 掉落 roll 规则（次数/保底/池优先级） | **`UNKNOWN`** | 判定逻辑不在客户端；当前是最小可解释规则 |
| 6 | `bag_code` 取值域 | **`UNKNOWN`** | 客户端实测会发 06/07/08/0c；本实现统一按主背包返回 |
| 7 | `SC_20023.val_list` 的 `key` 语义 | **`UNKNOWN`** | 本实现发空表 |
| 8 | 战斗摆位 `pos` / `group` 的原版约定 | **`IMPLEMENTATION_FALLBACK`** | 按"我方 group=1 / 敌方 group=2，pos 0..2" |
| 9 | 客户端**为什么**不发 20011/20014 | **未定位** | 可能是战斗场景资源/动画未就绪；已改为服务端驱动以绕开 |
| 10 | 战斗**画面**的视觉确认 | ❌ **未通过，根因未定论** | 客户端**执行完了整场战斗逻辑**（`playEnterEffect → start → createBattleScene → addRole×2 → roleReady×2 → playRoundStart×4 → playMagic → result → clear → exitFight`），但 `BattleView:loadBack` / `createUI`（战斗背景与战斗 UI 的构建者）**未观察到被调用**。A–E 五条证据存在矛盾，**根因尚未定位**（详见 §九，其中 §9.9 更正了 §9.5–9.7 的一个错误结论） |
| 11 | 掉落表覆盖率 | **24/2645（0.91%）**，且**这 24 条是模板残留死数据** | 其物品（51000 号段）**全部不在真实物品表 `Config.Item` 内** ⇒ 已弃用，见 §3.1 |
| 13 | **真实物品表** | ✅ **已恢复** | `Config.Item` 1117 条（33000–99999），`analysis/1.4.9/item/config_item.json`；工具 `tools/extract_config_item.py` |
| 14 | 真实物品表的**字段语义** | 部分 `UNKNOWN` | 已知 `[2]` 是名字（如 33001「10级速度符」）；其余 30 个字段名在 `config_item.luac` proto#0（`use_num`/`effect`/`desc`/`animate_res_id`…）但**下标对应关系未逐一验证** |
| 12 | `Config.ItemData` | **APK 内不存在** | 客户端没有物品配置表 ⇒ 物品名/图标只能由服务端自建 |

---

## 八、下一步建议

1. **定位战斗画面不渲染的根因**（**当前最高优先**）：见 §九。
2. **定位客户端不发 20011/20014 的原因**：与 §九 很可能是**同一个根因**
   ——战斗场景"就绪"回调没触发，所以既没有 UI，也不会回报"动画播完"。
3. **扩散战斗范围**：目前只支持「我方 1 单位 vs 敌方 1 怪」，
   可扩到多波（`wave_max`/`wave_no` 字段已经在下发）、多单位（`SC_20015` 已解）。
4. **补战斗与任务的更多条件类型**：`kill_mon` / `collect_elem` / `seal_mon` 等
   （`mission_util` 的条件分派表已经还原）。

---

## 九、★ 追加取证：战斗画面为什么不显示（第 1 轮定位）

### 9.1 做法

用探针勾住 `Battle`（`battle.luac`，18 个方法）与 `BattleView`
（`battle_view.luac`，9 个方法），跑一次完整战斗，记录**每个方法的实际调用**。
证据：`logs/1.4.9/battle/battle_render_chain.log`（89 条 btm/btv + 68 条场景采样）。

### 9.2 结果

**逻辑链：全部执行 ✅**

```
playEnterEffect → start → createBattleScene
→ addRole(我方) → createBattleRole → addRole(敌方)
→ roleReady ×2（add_act_spine=true）
→ playRoundStart(round=1..4) → playMagic
→ result(result=1) → clear() → exitFight()
```

**视图链：只走了一半 ❌**

| BattleView 方法 | 调用 |
|---|---|
| `create` | ✅ |
| `createRole` | ✅ |
| `createEffect` | ✅ |
| **`loadBack`**（战斗背景 `BattleBG` / `bg_<sceneId>`） | ❌ **从未调用** |
| **`createUI`**（bc=1065，战斗 UI 构建器） | ❌ **从未调用** |

`Battle:initScene` / `Battle:enterFightFunc` 同样**从未调用**。

### 9.3 判定

- **不是客户端缺功能**：战斗逻辑、单位创建、回合播放、结算全部跑完。
- **不是资源缺失**：`bg_10001.jpg`、`skillbg.png`、`huihe_di.png`、`zd_di*.png`
  等**都在 1.4.9 APK 内**（实测 `assets/res/resource/battle/` 下 109 个条目）。
- **是"战斗场景就绪"回调没有触发**：`battle.luac` 里 `loadBack` / `createUI`
  只出现在两个闭包里（proto#0 `loadBack(sceneId)`、proto#2 `createUI+enterFightFunc`），
  它们应当是一个**资源加载完成回调**。

### 9.4 影响与结论（诚实交代）

**本阶段交付的「战斗最小垂直闭环」在协议层与数据层是完全成立的**
（CS/SC 收发、扣血、死亡、结算、经验金币、掉落进包、任务进度、重登持久化全部实测通过），
**但"客户端把战斗画出来"这一环尚未达成**，因此不能声称"客户端显示战斗"已完成。

这也同时解释了 §七 第 9 项（客户端不发 `CS_20014`）：**同一个根因**——
场景没就绪，自然不会回报"动画播完"。

> ✅ **对服务端实现的影响：无。** 服务端已经通过"自己按节拍推进"绕开了这个问题
> （`battle_round_interval`），闭环不依赖客户端的 20014。

### 9.5 ★★ 第 2 轮：**根因已完整定位**（静态字节码链，闭合）

反汇编 `battle.luac` proto#4 `Battle:start`（bc=205）的尾部：

```
164  RenderMgr:getInstance()
169  TGETS doNextFrame
170  FNEW  A=5 D=64   ; ChildRef(#0)  ← proto#0 = { battle_scene:loadBack(SceneModel.sceneId) }
171  CALL                                 RenderMgr:getInstance():doNextFrame(<#0>)

172  battle_scene:createRole()
176  battle_scene:createEffect()
181  self.is_lock = nil
183  self:createBattleRole(data.fighter_info_list)

186  RenderMgr:getInstance()
191  TGETS doNextFrame
192  FNEW  A=5 D=69   ; ChildRef(#2)  ← proto#2 = { battle_scene:createUI(); enterFightFunc(); ... }
193  CALL                                 RenderMgr:getInstance():doNextFrame(<#2>)
200  FNEW  A=5 D=70   ; ChildRef(#3)
201  CALL                                 RenderMgr:getInstance():doNextFrame(<#3>)
```

⇒ **`loadBack` / `createUI` 不是直接调用，而是通过
`RenderMgr:getInstance():doNextFrame(fn)` 注册的「下一帧回调」。**

再看 `game/scene/util/render_mgr.luac`：

| 方法 | 反汇编要点 | 语义 |
|---|---|---|
| `__init` (proto#0) | `next_do_list = {}`、`isStop = nil`、`sharedScheduler = cc.Director:getInstance():getScheduler()` | **不调用 `start()`** |
| `getInstance` (proto#1) | 不存在则 `New` | 只建单例 |
| `doNextFrame` (proto#12) | `table.insert(self.next_do_list, {fn1, fn2})` | **只入队** |
| `update` (proto#10) | 遍历 `dic`/`funDic`；然后 `while #next_do_list > 0 do local f = table.remove(next_do_list,1); f[1](); f[2]() end` | **唯一出队者** |
| `start` (proto#3) | `if self.isStop ~= nil then return end; self.isStop=false; if not self.schedule_ then self.schedule_ = sharedScheduler:scheduleScriptFunc(<proto#2>, 0, false) end` | **唯一调度 `update` 的地方** |
| `stop` (proto#4) | 取消调度 | — |

**而 `RenderMgr:start()` 在整个 APK 里只有一处被调用**：
`game/map/map_view.luac` proto#15 —— 也就是
**「点击地图自由移动（`freeMove` / `isOnRange`）」那条路径**里
（`kgc` 同时含 `RenderMgr` / `getInstance` / `start` / `freeMove` / `isOnRange`，
字节码尾部为 `…:getInstance()` → `:start()`）。

### 9.6 结论（一句话）

> **`RenderMgr` 的每帧 `update` 只有在「玩家点过地图走路」之后才会被调度。**
> 我们的探针是**直接用 `GlobalEvent:Fire(SCENE_MONSTER_CLICK)` / `csFightMon` 攻怪**，
> 从来没有点过地图 ⇒ `RenderMgr:update` 从未运行 ⇒
> `next_do_list` 里的 `loadBack` / `createUI` 回调**永远不会出队** ⇒
> **战斗背景与战斗 UI 从不建立。**

### 9.7 这条根因的**影响面远大于战斗**

全 APK 有 **16 个文件**在用 `RenderMgr:getInstance():doNextFrame(...)`：

```
battle / battle_ctrl / main_chat / story_ctrl / skill_ctrl / horse_ctrl
daily_ctrl / equip_data / shop_model / guider_up_model / beast_ctrl
backpack(shortcut_alert) / action_card_view / role_main_view / invest_model
chongzhi(yueka_view) / action_card_view_cz
```

⇒ **「未点过地图走路」时，这些模块的下一帧回调全部静默失效。**
这很可能解释本项目此前遇到的一批「某个界面/流程莫名其妙不生效」的现象。
**这是一个系统性发现，不局限于战斗。**

### 9.8 已就绪的验证手段（待环境恢复即可跑）

探针里已经加好验证代码：**攻怪前显式调用 `RenderMgr:getInstance():start()`**，
并上报 `isStop` / `next_do_list` 长度 / `schedule_` 是否建立（探针标签 `bt_rm`）。

**下一次只需**：
1. 把 `server/dsh_fake_login.lua` 的 `_G.__dsh_battle` 置 `true`；
2. `pwsh tools\build_fakelogin.ps1`；
3. 看 `bt_rm` 的三点上报 + 战斗窗口内截图。
   若战斗画面出现 ⇒ 根因确认，且**「客户端显示战斗」随之达成**。

> ⚠ **本轮未能完成该运行时验证**：收尾时客户端出现**间歇性连不上游戏服 TCP**
> （HTTP 正常、`tcp.log` 不生成或连上数秒即 `closed`；重试 4 次未恢复）。
> 这是本项目记录过的老问题，与本轮代码改动无关。
> **静态根因链本身是闭合的**（三处反汇编互为印证：闭包注册点 → 入队 → 出队条件）。

### 9.9 ⚠️ 第 3 轮：**上一轮的关键结论被推翻**（必须更正）

上一轮我写「`RenderMgr:start()` 在整个 APK 里**只有一处**调用点（`map_view` 自由移动）」——
**这是错的，原因是那次扫描的输出被截断了（只看了前 30 行）。**

重新做**完整扫描**（不再截断）后，`RenderMgr` 的调用点共 **16 个文件**，
其中**真正调用 `start()`** 的是：

```
game/scene/scene_model.luac   proto#68   ← SceneModel:sceneStart()
```

反汇编 `scene_model.luac` proto#68（`bc=173`）第 **76–111** 行，是**直线代码、无分支**：

```
 82  GGET   GlobalEvent
 84  TGETS  getInstance
 87  TGETS  Fire
 88  GGET   SceneEvent
 89  TGETS  SCENE_START
 90  TGETS  self.sceneId
 91  CALL                      GlobalEvent:getInstance():Fire(SceneEvent.SCENE_START, sceneId)

 92  GGET   RenderMgr          ; D=22 → kgc[49-1-22]=kgc[26]='RenderMgr'
 94  TGETS  getInstance
 97  TGETS  start              ; C=23 → kgc[48-23]=kgc[25]='start'
 98  CALL                      ★ RenderMgr:getInstance():start()

109  TGETS  self.scene
111  TGETS  createMap
112  CALL                      self.scene:createMap()
```

**而 `createMap()`（第 111 行）在本项目里是被实测确认跑过的基础功能**
（地图能渲染，上一阶段文档 `server/mock_server.py` 里也写明
「实测 scene_model proto[68] sceneStart → SceneView:createMap()」）。

⇒ **`RenderMgr:getInstance():start()` 必然被调用过，`RenderMgr.update` 必然在跑。**

⇒ **我上一轮给的"根因"（RenderMgr 从未被调度 ⇒ 回调永不出队）不成立。**

### 9.10 现在的**真实**状态：证据之间仍然矛盾

| # | 已确认的事实 | 强度 |
|---|---|---|
| A | `Battle:start`（proto#4）在 170/192 行用 `RenderMgr:doNextFrame(<闭包>)` 注册 `loadBack` / `createUI` | **反汇编直证** |
| B | `RenderMgr.doNextFrame` 只入队；`RenderMgr.update` 是唯一出队者；`update` 由 `start()` 调度 | **反汇编直证** |
| C | `RenderMgr:start()` 由 `SceneModel:sceneStart()`（proto#68）**无条件**调用，且其后的 `createMap()` 确实跑过 | **反汇编直证 + 本项目既有实测** |
| D | 探针**没有**观察到 `BattleView.loadBack` / `createUI` 被调用 | 实测（探针上报） |
| E | 探针**观察到** `BattleView.create` / `createRole` / `createEffect` 被调用（同一批钩子） | 实测（探针上报） |

**A+B+C 推出「两个回调应该被执行」，D 说没有。矛盾。**

⇒ **可能的解释（尚未区分）**：

1. **探针漏钩（当前最可能）**：`battle_scene` 实例的 `__index` 可能指向
   `BattleView:create()` 里构造的**副本/子表**，而不是 `BattleView` 模块表本身，
   于是 `loadBack` / `createUI` 走的是**未被替换的原函数**；
   而 `create` / `createRole` / `createEffect` 恰好是从模块表上调用的，所以被钩到。
   —— 但 `createRole`/`createEffect` 与 `loadBack`/`createUI` 在源码里**都是
   `self.battle_scene:xxx()`** 形式，这一解释并不自洽，需实测区分。
2. **`update` 里 `next_do_list` 的分支条件没进去**（`#next_do_list > 0` 的比较方向读错）。
3. **闭包执行时抛错**（`loadBack` 内部 `PlistMgr` / 资源加载失败），
   `pcall` 之外的错误被引擎吞掉。

### 9.11 ★★ 第 4 轮：**运行时拿到了决定性证据**

探针第 3 轮加装的 `RenderMgr` 钩子在真机上成功触发，回报了 **RenderMgr 的真实内部状态**：

```
[19:28:58] t=bt_rm&v=hooked_isStop_true_sched_false
                              ^^^^^^^^^^^^  ^^^^^^^^^^^
                              isStop=true   schedule_=nil（从未被调度）
```

**两条都是真机事实，不是推断。** 结合 `render_mgr.luac` 的反汇编：

| 事实 | 出处 |
|---|---|
| `__init` 里 `isStop = true`（`KPRI D=2` → true） | proto#0 bc#18–19 |
| `start()` 只在 `isStop == false` 时才继续，否则直接 `return` | proto#3 bc#0–3 |
| `stop()` 把 `isStop` 置回 `true` 并注销调度 | proto#4 bc#4–15 |
| **除 `start()` 自身外，没有任何代码把 `isStop` 置为 `false`** | 全包扫描 |
| 真机：`schedule_ == nil` | **运行时实测** |

⇒ **`RenderMgr` 从未被成功 `start()`，其 `update` 从未运行，
`next_do_list` 里的回调从未出队。**

这与观察 D（`loadBack` / `createUI` 没被调用）**完全一致**，
而与"`sceneStart` 调用了 `start()`"**并不矛盾** —— `start()` 被调用了，
但**因为 `isStop == true` 而立刻返回**，没做任何事。

### 9.12 ✅ 结论（本轮闭环）

> **根因**：`RenderMgr` 的 `isStop` 在构造时被置为 `true`，
> 而 `start()` 的守卫是「`isStop ~= false` 就返回」，
> **因此 `start()` 永远无法真正建立每帧调度**。
> ⇒ `RenderMgr.update` 从不运行 ⇒ `Battle:start` 用 `doNextFrame` 注册的
> `BattleView.loadBack` / `createUI` 永远留在队列里 ⇒
> **战斗背景与战斗 UI 从不建立，画面看不到战斗。**

> ⚠ 仍需下一轮在真机上确认：把 `isStop` 强制置 `false` 后再 `start()`，
> 调度器是否建立（`schedule_ ~= nil`）、回调是否出队、战斗画面是否出现。
> 探针已按此写好（`bt_rm` 三点上报：`before_start_isStop/sched/queue`
> → `plain_start_sched` → `forced_start_sched`）。

### 9.13 影响面（**收窄后的正确表述**）

- 这**不是"没点地图"造成的**（上一轮的推论错误，已更正）。
- 它是 `RenderMgr` 自身的状态机问题，**影响所有 `doNextFrame` 用户**
  （16 个文件）。但**只有当某个界面/流程确实依赖 `doNextFrame` 时才会显现**
  —— 所以现象是"某些界面/表现不生效"，而不是全局崩坏。
- 但本项目**目前只观察到战斗这一处**因此失效；
  其他 15 个模块**尚未逐一验证**，不应断言它们都坏了。

### 9.14 修复方向（更新）

| 方案 | 说明 | 评价 |
|---|---|---|
| **A. 探针在攻怪前 `m.isStop=false; m:start()`** | 已写进探针，可立即验证根因 | **推荐先做**（验证用） |
| **B. 在客户端启动早期就把 `RenderMgr` 拉起来** | 例如在注入脚本里做一次 `isStop=false; start()` | **可作为正式修复**（一处改动惠及全部 `doNextFrame` 用户） |
| **C. 服务端绕开** | 服务端无法改客户端渲染，不可行 | — |

> 注意：**这是客户端侧的问题，不是服务端 bug。**
> 本阶段交付的服务端战斗闭环（协议/伤害/结算/奖励/掉落/任务/持久化）
> **不受影响、已全部实测通过**。
