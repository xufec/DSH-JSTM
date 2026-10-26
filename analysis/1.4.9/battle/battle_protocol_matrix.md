# 1.4.9 战斗协议矩阵

> **目标 APK**：`anzbao/jstm.apk`
> 包名 `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**（360 / ewan.qihoo 渠道）
> **本文所有 CMD、字段名、字段顺序与类型均从 1.4.9 APK 字节码直读，无一条凭经验填写。**
> 1.4.11（`jstm_142165.apk`）**未参与任何判定**。

---

## 一、证据链（每个结论都可复现）

| 证据 | 来源文件（1.4.9 APK 内） | 提取方法 |
|---|---|---|
| CMD → 中文含义 | `assets/src/config/protocal/all_proto.luac`（1643 条） | `tools` 直接读 TDUP 表 |
| **消息字段名 + 顺序 + 线类型** | `assets/src/config/protocal/cmd_resolve_200.luac` | `python tools/proto_spec.py cmds <CMD>` |
| CMD → 客户端处理函数 | `assets/src/game/battle/battle_ctrl.luac` proto#0 | `python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle_ctrl.luac 0` |
| 处理函数语义 | 同文件 proto#2/3/5/10/12/13/18/19/20/31 | 同上，指定 proto# |
| 客户端模块清单 | 资产名扫描 | `python tools/battle_audit.py files` |

### 1.1 消息定义的权威形态（关键发现）

`cmd_resolve_*.luac` 里每个消息都是一个 `AutoConstruct` 调用：

```
TGETS  A=1 B=0 C=0   ; ['AutoConstruct']
KSTR   A=3 D=1       ; 'sc'                      <- 方向
KSHORT A=4 D=20001   ; 20001                     <- CMD
TDUP   A=5 D=2       ; TableConst(array=[None,'code__C','msg__s'])
CALL   A=1 D=261
```

⇒ 规格是 `AutoConstruct(方向, CMD, { '<字段名>__<格式字符>', ... })`，
**数组顺序就是字段顺序**（这一点用 `SC_20001` 与 `manual.md` 的
`code:uint8, msg:string` 交叉对齐验证过）。

格式字符（LuaJIT `ReadFMT`）：

| 字符 | 类型 | 字符 | 类型 |
|---|---|---|---|
| `C` | uint8 | `c` | int8 |
| `H` | uint16 | `h` | int16 |
| `I` | uint32 | `i` | int32 |
| `s` | string | `D\|Xxx\|` | 计数前缀 + `Xxx` 结构数组 |

---

## 二、★ CMD → 客户端处理函数（`battle_ctrl.luac` 注册表原文）

`battle_ctrl.luac` proto#0 `registerProtocals` 的反汇编结果（1.4.9 原文）：

| CMD | 注册的处理器 | CMD | 注册的处理器 |
|---|---|---|---|
| 20001 | `scFightStart` | 20015 | `scAddRole` |
| 20002 | `scFightStart` | 20016 | `watchBattleReply` |
| 20003 | `scFightStart` | 20017 | `scExitWatch` |
| 20004 | `sc20004AskForFight` | 20020 | `scFightEnd` |
| 20008 | `scAuto` | 20022 | `hander_20022` |
| 20009 | `scSelectSkill` | 20023 | `scFightEndData` |
| 20010 | `scFightData` | 20025 | `watchReplayReply` |
| 20012 | `scFightRound` | | |
| 20013 | `scRoundStart` | | |

---

## 三、战斗协议矩阵

状态取值：`已确认`（字节码权威）／`已验证`（真机实测）／`待实现`／`未知`

### 3.0 ★ 本轮真机验证结果（2026-09-17 实测）

实现并跑通闭环后，以下 CMD 由「已确认」升级为 **`已验证`**：

| CMD | 方向 | 实测证据 |
|---|---|---|
| **20002** | C→S | `>> cmd=20002 body=00 00 4e 21 13 8f 00 00`（mon_id=20001） |
| **20002** | S→C | `<< 20002 code=1(TRUE)`；客户端探针 `bt_in scFightStart code_1` |
| **20010** | S→C | `<< 20010 fighters=2`；客户端探针 `bt_in scFightData … fighter_info_list_{1:{rid=..` ⇒ **客户端成功解析** |
| **20012** | S→C | `<< 20012 SC_20012 skill_play`（每回合 2 条：我方 + 敌方） |
| **20013** | S→C | `<< 20013 SC_20013 round_start`（含 `hit=772` / `hp` / `is_target_die`） |
| **20020** | S→C | `<< 20020 SC_20020 result=1`；**客户端随后主动发 `CS_20021`** ⇒ 它确实收到了 |
| **20023** | S→C | `<< 20023 SC_20023 result=1 role_hurl=2` |
| **20021** | C→S | `>> cmd=20021`（客户端收到 20020 后的反应，**实测确实发出**） |
| **10502** | C→S | `>> cmd=10502 body=08 00 00 00 00` 等 |
| **10502** | S→C | `<< 10502 SC_10502 bag_code=… items=…` |
| **10500** | S→C | `<< 10500 SC_10500 bag push items=1` |

**仍然 `未实现`**：20001/20003/20004/20005/20008/20009/20011/20014/20015/20016/20017/
20022/10601/10610 —— 本阶段不展开（见 §6）。其中 **20011 / 20014 实测客户端根本不发**
（详见 `battle_flow.md` §三 的订正说明）。

### 3.1 主表

| 功能 | CMD | 请求字段 | 响应字段 | 客户端模块 | 服务端 | 状态 |
|---|---|---|---|---|---|---|
| 对角色发起战斗 | 20001 | `rid:int32, srv_id:string` | `code:uint8, msg:string` | `battle/battle_ctrl.luac` → `csFightRole` / `scFightStart` | 回了 code=0（明确不在范围） | 已确认 |
| **对怪物发起战斗** | **20002** | **`mon_id:int32`** | **`code:uint8, msg:string`** | `battle/battle_ctrl.luac` → `csFightMon` / `scFightStart` | **已实现** | **已验证** |
| 测试战斗 | 20003 | （空） | `code:uint8, msg:string` | `battle_ctrl` → `scFightStart` | 回了 code=0 | 已确认 |
| 发起切磋 | 20004 | `rid:int32, srv_id:string, name:string` | `name:string, rid:int32, srv_id:string` | `battle_ctrl` → `sc20004AskForFight` | 明确不在范围 | 已确认 |
| 确认切磋 | 20005 | `result:int8, rid:int32, srv_id:string` | — | `battle_ctrl` → `on20005AccectFight` | 明确不在范围 | 已确认 |
| 自动战斗开关 | 20008 | `flag:uint8` | `id:int8, flag:uint8` | `battle_ctrl` → `setAuto` / `scAuto` | 仅记录 | 已确认 |
| **使用技能** | **20009** | **`skill_id:int32`** | **`skill_id:int32`** | `battle_ctrl` → `csSelectSkill` / `scSelectSkill` | 仅记录 | 已确认 |
| **战斗初始化数据** | **20010** | （空） | 见 §4.1 | `battle_ctrl` → `scFightData` → `Battle:playEnterEffect` | **已实现** | **已验证** |
| 客户端加载完成 | 20011 | （空） | — | `battle/battle.luac` → `loadFinish` | 接收但不依赖（**客户端实测不发**） | 已确认 |
| **小回合战斗效果** | **20012** | — | 见 §4.2 | `battle_ctrl` → `scFightRound` → `Battle:doNextFrame` | **已实现** | **已验证** |
| **回合开始（含伤害）** | **20013** | — | 见 §4.3 | `battle_ctrl` → `scRoundStart` → `Battle:playRoundStart` | **已实现** | **已验证** |
| 客户端动画播放完成 | 20014 | （空） | — | `battle_ctrl` → `playEnd` 主动发 | 接收但不依赖（**客户端实测不发**） | 已确认 |
| 新增战斗对象 | 20015 | — | `fighter_list:table(18 字段)` | `battle_ctrl` → `scAddRole` | 未实现 | 已确认 |
| 申请观战 | 20016 | `rid:int32, srv_id:string` | `code:uint8, msg:string` | `battle_ctrl` → `watchBattle` | 明确不在范围 | 已确认 |
| 退出观战 | 20017 | （空） | `code:uint8, msg:string` | `battle_ctrl` → `csExitWatch` | 明确不在范围 | 已确认 |
| **战斗结果** | **20020** | — | **`result:uint8`** | `battle_ctrl` → `scFightEnd` | **已实现** | **已验证** |
| 闭关战斗结束界面 | 20021 | （空） | — | `battle_ctrl` → `csCloseFinishView` | **实测客户端收到 20020 后主动发出** | **已验证** |
| 显示战斗结束界面 | 20022 | — | `icon_list:table(icon_id:uint32)` | `battle_ctrl` → `hander_20022` → `openBattleFail` | 未实现（战败界面） | 已确认 |
| **显示战斗伤害信息** | **20023** | — | 见 §4.4 | `battle_ctrl` → `scFightEndData` | **已实现** | **已验证** |
| 获取战斗录像 | 20025 | `id:string, srv_id:string` | `code:uint8, msg:string` | `battlevideo/battlevideo_ctrl.luac` | 不实现（录像） | 已确认 |
| 获取战斗录像大小 | 20026 | `id:string, srv_id:string` | `code:uint8, msg:string` | `battlevideo_ctrl.luac` | 不实现（录像） | 已确认 |
| 停止播放录像 | 20027 | 见 `cmd_resolve_200.luac` | — | `battlevideo_ctrl.luac` | 不实现（录像） | 未知 |
| 录像列表 | 20028 | — | — | `battlevideo_ctrl.luac` | 不实现（录像） | 未知 |
| 战斗录像锁定 | 20029 | — | — | `battlevideo_ctrl.luac` | 不实现（录像） | 未知 |
| 分享战斗录像 | 20030 | — | — | `battlevideo_ctrl.luac` | 不实现（录像） | 未知 |
| **测试战斗伤害** | **10601** | `flag:uint32` | `p:uint32, skill_bid:uint32, lev:uint32, hero_list:table(22 项战斗属性)` | `skill/skill_ctrl.luac` | 未实现 | 已确认 |
| **战斗验算** | **10610** | `fight_handle:table(magic_bid:I, fps_start:H, fps_stop:H), mons_bid_value:table(mon_bid:I, value:H), fps:uint32` | `code:uint8, msg:string` | 出生战斗模拟校验 | 未实现 | 已确认 |

### 3.1 与本文档初版判断的**重要订正**

`server/mock_server.py` 中曾有一处注释断言「真正的击杀发生在战斗实例
（**11000 / 11200 系列**，含 mon_list / skill）」。经 1.4.9 字节码核对：

| CMD 段 | 实际含义（`all_proto.luac`） | 判定 |
|---|---|---|
| 11000–11018 | 地下城（获取/开启/搜索/挑战/掠夺） | **与战斗无关** |
| 11200–11242 | 伙伴（基础界面/技能/招募/洗髓…） | **与战斗无关** |
| **20001–20030** | **战斗** | ✅ **真正的战斗协议段** |

⇒ 11000/11200 系列**不是**战斗协议。原注释为误判，本阶段以 20000 段为准。

---

## 四、关键消息的完整字段展开（权威）

### 4.1 `SC_20010` 战斗初始化数据（`cmd_resolve_200.luac` proto#13）

| # | 字段 | 类型 |
|---|---|---|
| 1 | round | uint16 |
| 2 | round_wave | uint16 |
| 3 | wave_max | uint16 |
| 4 | wave_no | uint16 |
| 5 | atk_formation_type | uint8 |
| 6 | atk_formation_lev | uint8 |
| 7 | def_formation_type | uint8 |
| 8 | def_formation_lev | uint8 |
| 9 | is_observer | uint8 |
| 10 | effect_id | string |
| 11 | order_list | **T** `FMT(id@I)` |
| 12 | fighter_info_list | **T** `FMT(id@H##rid@I##srv_id@s##name@s##lev@H##sex@C##career@H##pos@C##group@C##hp_max@I##hp@I##anger@I##is_auto@C##animate_res@D\|Dsc20010animate_res\|##skills@D\|Dsc20010skills\|##specials@D\|Dsc20010specials\|)` |

引用的子结构（同文件，顺序见 §4.6 的重要订正）：

| 子结构 | 字段（线序，`name@类型`） |
|---|---|
| `Dsc20010animate_res` | `ant_id@H##ant_val@s##ent_lev@C##dis_method@C` |
| `Dsc20010skills` | `bid@I##step@C##last_use@H##cd@H` |
| `Dsc20010specials` | `key@C##val@I` |

### 4.2 `SC_20012` 小回合战斗效果（proto#22）

| 字段 | 类型 |
|---|---|
| round | uint16 |
| skill_play | **T** `FMT(order@C##user_id@H##skill_id@I##father_id@I##father_skill_id@I##passive_skill_id@I##user_anger@H##talk@s##notice@s##magic_play@D\|Dsc20012magic_play\|##summon_play@D\|Dsc20012summon_play\|)` |
| cooldown | **T** `FMT(bid@I##last_use@H)` |

### 4.3 `SC_20013` 回合开始（proto#35）—— **伤害就落在这里**

| 字段 | 类型 |
|---|---|
| round | uint16 |
| round_wave | uint16 |
| time | uint8 |
| wave_no | uint8 |
| magic_play | **T** `FMT(order@C##target_anger@H##target_id@H##source_id@H##hit@c##hp_max@I##hp@I##is_target_die@C##target_talk@s##magic_list@D\|Dsc20013magic_list\|)` |
| summon_play | **T** `FMT(id@H##rid@I##srv_id@s##name@s##lev@H##sex@C##career@H##pos@C##group@C##hp_max@I##hp@I##anger@I##is_auto@C##animate_res@...##skills@...##specials@...)` |
| order_list | **T** `FMT(id@I)` |

⇒ **生命值扣减由 `magic_play.hp` / `hp_max` / `hit` / `is_target_die` 表达**，
即：**伤害不由客户端计算，而是服务端算好后逐条下发**。

### 4.4 `SC_20023` 显示战斗伤害信息（proto#59）

| 字段 | 类型 |
|---|---|
| type | uint8 |
| result | uint8 |
| role_hurl_list | **T** `FMT(rid@I##srv_id@s##name@s##group@C##lev@H##sex@C##career@H##hp_max@I##hp@I##hurt@I##master_rid@I##master_srv_id@s##id@I)` |
| val_list | **T** `FMT(key@C##val@I)` |
| msg | string |

### 4.5 `SC_20020` 战斗结果（proto#56）

**只有 `result:uint8` 一个字段。** ⇒ 战斗**胜负**在 20020，而
**伤害/结算明细在 20023**，经验/金币/掉落**不在这两条消息里**（见 §6）。

### 4.6 ★ 重要订正：`Dsc*` 子结构的字段顺序（本阶段发现）

`protocol/manual.md` 与 `protocol/fields.json` 里 **`Dsc*` 子结构段的字段顺序是反的**。
顶层消息（`AutoConstruct` 的 `name__T__id@H##rid@I##...` 内联数组）**不受影响，是对的**。

**判据（三条独立证据，全部来自 1.4.9 APK）**：

1. `baseprotocalstruct.luac` proto#7 `Encode` 的反汇编：
   `ipairs(self.m_value_names)` 逐个把 `m_value_src[name]` 追加进 `m_values`，
   再 `WriteFMT(self.m_format, unpack(m_values))`
   ⇒ **名字顺序与格式串按位置配对**，且是**顺序**。
2. **同名字段交叉对齐**：`Dsc20010skills` 读取器的名字顺序是 `bid, step, last_use, cd`、
   格式串 `ICHH`；而 `SC_20012.cooldown` 的**内联 spec** 是 `bid@I##last_use@H`。
   只有**不反转**才能自洽（`bid`=uint32、`last_use`=uint16）；
   反转会得到 `bid`=uint16 / `last_use`=uint8，与内联 spec **直接冲突**。
3. **16 字段全中**：`Dsc20013summon_play` 读取器顺序与 `SC_20013.summon_play`
   内联 spec 逐字段逐类型完全一致（16/16）。

**订正前后对照**（以 `Dsc20010animate_res` / `Dsc20010skills` 为例）：

| 子结构 | manual.md（**错**） | 订正后（**对**，线序） |
|---|---|---|
| `Dsc20010animate_res` | dis_method:u16, ent_lev:s, ant_val:u8, ant_id:u8 | **ant_id:u16, ant_val:s, ent_lev:u8, dis_method:u8** |
| `Dsc20010skills` | cd:u32, last_use:u8, step:u16, bid:u16 | **bid:u32, step:u8, last_use:u16, cd:u16** |
| `Dsc20010specials` | val:u8（只有 1 字段） | **key:u8, val:u32**（2 字段，键值对） |

**工具**：`python tools/dsc_spec.py --file 200` 按本判据输出全部子结构（脚本头注含完整判据）。

---

## 五、战斗相关客户端模块清单（1.4.9 实际存在）

| 模块 | 路径 | 大小 | 作用（据方法名表） |
|---|---|---|---|
| `battle` | `game/battle/battle.luac` | 47487 | 战斗场景/单位/回合/播放（104 个方法） |
| `battle_ctrl` | `game/battle/battle_ctrl.luac` | 6408 | 协议注册与收发（31 个方法） |
| `battle_view` | `game/battle/battle_view.luac` | 30135 | 战斗 UI |
| `battle_role` | `game/battle/battle_role.luac` | 17419 | 战斗单位表现 |
| `skill_act` | `game/battle/skill_act.luac` | 27902 | 技能动作 |
| `battle_tips` | `game/battle/battle_tips.luac` | 11941 | 战斗提示 |
| `battle_fail` | `game/battle/battle_fail.luac` | 3819 | 战败界面 |
| `battle_debug` | `game/battle/battle_debug.luac` | 1713 | 调试 |
| `fabao_select` | `game/battle/fabao_select.luac` | 15677 | 法宝选择 |
| 场景怪物 | `game/scene/element/monster.luac` | 3289 | 地图上的怪物单位（点击 → `SCENE_MONSTER_CLICK`） |
| 怪物 VO | `game/scene/element/monster_vo.luac` | 309 | 怪物数据对象 |
| 掉落 | `game/drop/drop_ctrl.luac`, `drop_data.luac`, `drop_item.luac`, `drop_vo.luac` | 300/93/3461/272 | 掉落表现 |
| 自动战斗 | `game/dungeon/auto_fight.luac` | 4255 | 自动战斗（副本用） |
| 战斗录像 | `game/battlevideo/*.luac` | — | 录像（超出本阶段范围） |

⇒ **客户端 UI / 场景 / 动画 / 技能 / 伤害显示 / 结算界面全部已存在**，
本阶段只做「让服务器提供客户端期待的数据」（符合项目总原则）。

---

## 六、★ 本阶段**尚未确认**的部分（如实标注，不猜）

| 缺口 | 现状 | 需要什么证据 |
|---|---|---|
| **经验 / 金币的发放协议** | `SC_20020` 只有 `result:uint8`；`SC_20023` 的 `val_list(key:uint8,val:uint32)` **语义未知**（key 的含义未解出）。经验/金币**不在这两条战斗消息中**。 | 需实测：真机上打完一场，看服务端该发哪条（候选：`10409 英雄加经验`、`12742 提示获得资产/物品`、`10302` 角色数据刷新、`10500/10501` 背包推送） |
| **掉落的传输协议** | `SC_20023` 也没有物品列表。`10500 推送角色背包数据` / `10501 物品数量更新` / `12742 提示获得资产/物品` 是候选，**未验证** | 同上，需实测抓包 |
| **怪物 HP / 攻击力 / 经验 / 金币 的权威数据源** | `Config.Mon` 2645 条**不含** hp/atk/exp/gold（字段分布见 `monster_data_model.md`） | 原版服务端数据；APK 内无法取证 |
| **伤害计算公式** | 客户端有 `10601 测试战斗伤害`（返回 22 项战斗属性）与 `10610 战斗验算`（客户端模拟校验），说明**客户端也有一套战斗计算**；但服务端下发 `SC_20013.hit` 意味着**最终伤害以服务端为准** | 需实测或原版服务端数据 |
| `SC_20012` / `SC_20013` 子结构 `Dsc20012magic_play` / `Dsc20012summon_play` / `Dsc20013magic_list` 的字段 | 已在 `cmd_resolve_200.luac` 中定位到格式串，**字段名与顺序的配对尚需逐一展开验证** | `python tools/proto_spec.py` 的 `dsc` 展开（本阶段续做） |

> 上表中「经验/金币/掉落走哪条协议」是本阶段**最关键的一个未知**，
> 必须靠**实测**（`logs/1.4.9/battle/`）确定，**不得凭经验填写**。
