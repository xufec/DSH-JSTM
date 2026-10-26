# JSTM 1.4.9 战斗字段权威定义（字节码还原）—— 解出 CXEngine 对照中的三个未知

> **目标**：上一轮审计（`architecture.md` / `battle.md` / `reuse_candidates.md`）在把 CXEngine 与 JSTM 战斗做对照时，
> 遗留了三个【尚未确认】项。本文件**逐项解出**，并把结果回填到那三份报告的订正框。
> **手段**：`anzbao/jstm.apk`（1.4.9，`com.shiyue.dldl.ewan.qihoo`）内 `cmd_resolve_200.luac` 与
> 客户端战斗模块的 LuaJIT 字节码还原，全部使用本工作区已有工具：
> `tools/proto_spec.py`、`tools/dsc_spec.py`、`tools/luajit_dis.py`、`tools/luajit_bc.py`。
> **不猜**：每条结论都给出可复现命令与字节码出处；未能解出的显式标【未解出】。
> **未修改** `cankao/`、`server/` 或 APK 内任何文件（全部只读）。

---

## 0. 三个未知项的结论速览

| # | 上一轮的【尚未确认】 | 本轮结论 | 置信 |
|---|---|---|---|
| 1 | `Dsc20012magic_play` / `Dsc20012summon_play` / `Dsc20013magic_list` 的字段名与顺序 | ✅ **已解出**（见 §2）。`magic_play` 10 字段、`summon_play` 16 字段、**`magic_list` 元素 6 字段** | 【已确认】 |
| 2 | buff 的**剩余回合数**是否下发 | ✅ **下发**。`magic_list[].duration:uint8` 即剩余/持续回合；`magic_list[].fold:uint8` 为叠加层数 | 【已确认】 |
| 3 | `specials(key:u8, val:u32)` 的 key 语义 | ✅ **已解出**：**与"回合制 buff/控制状态"无关**，是**伙伴/宠物的外观属性通道**（key 1/2/4/5/6/7/8/9，共 8 个键，全部在 `battle_role.luac` proto#2 消费）| 【已确认】 |

### ★ 三个结论合起来意味着什么（对 CXEngine 对照的最终修正）

上一轮我（错误地）说：「JSTM **已有**载体 = `specials[]`」。**这是错的** —— `specials` 是外观通道，`val` 是
`Config.PartnerBase` / `PartnerStageEffect` / `PartnerHaloEffect` / `PartnerRebirthEffect` 的**配置 ID（uint32）**，
不可能是回合数（那是 `duration:uint8`）。

**真正的 buff/状态载体是 `magic_list[]`**（`SC_20012.skill_play[].magic_play[].magic_list[]` 与
`SC_20013.magic_play[].magic_list[]`），每条 = `(magic_bid, change_hp, duration, per, val, fold)`，
配合配置表 `Config.SkillMagic`（**12665 行**）与 `Config.SkillMagicType`（**31 个效果属性 ID**）。

⇒ **最终判定**：JSTM 的战斗消息**已经携带完整的"限时状态 + 剩余回合 + 层数 + 每回合HP变化 + 数值/百分比"**，
这是 CXEngine **完全没有**的（CXEngine 的 buff 存在服务端 `__actors_buffs__` 全局表里、**不在属性表内、无任何下行消息**）。
**CXEngine 是"buff 从不上线"的一方；JSTM 是"buff 逐条带上线"的一方。** 差距比上一轮判断的更大。

---

## 1. 消息与子结构的 proto 索引归属（先建立地图）

命令：`python tools/proto_spec.py cmds 20010 20012 20013 20015`

| 消息 | proto# | 含义（客户端处理器） |
|---|---|---|
| `SC_20010` | proto#13 | 战斗初始化数据（`scFightData` → `Battle:playEnterEffect`） |
| `CS_20010` | proto#20 | 空消息 |
| `SC_20012` | proto#22 | 小回合战斗效果（`scFightRound` → `Battle:doNextFrame`） |
| `SC_20013` | proto#35 | 回合开始 + 伤害（`scRoundStart` → `Battle:playRoundStart`） |
| `SC_20015` | proto#45 | 新增战斗对象（`scAddRole`） |

命令：`python tools/dsc_spec.py --file 200` → 共 **16 个**子结构读取器。按所属消息分组：

| 消息 | 子结构读取器 proto# | 结构 |
|---|---|---|
| `SC_20010` | 15 / 17 / 19 | `animate_res` / `skills` / `specials` |
| `SC_20012` | 24 / 26 / 28 / 30 / 32 / 34 | **`magic_list`(24)** / **`magic_play`(26)** / `animate_res`(28) / `skills`(30) / `specials`(32) / **`summon_play`(34)** |
| `SC_20013` | 37 / 39 / 41 / 43 | `magic_list`(37) / `animate_res`(39) / `skills`(41) / `specials`(43) |
| `SC_20015` | 47 / 49 / 51 | `animate_res` / `skills` / `specials` |

> ⚠️ **命名不一致（APK 自身的问题，如实记录）**：`SC_20013` 的内联 spec 写的是
> `magic_list@D|Dsc20013magic_list|`，但 proto#26（即 `magic_play` 读取器）的格式串写的是
> `D|Dsc20012magic_list|`。**两者指向同形结构**（见 §2.3），只是 APK 里的名字串没统一。
> ⇒ 不要用 `Dsc` 名字去索引，**用消息 + 字段名索引**。

**判据**（沿用 `tools/dsc_spec.py` 头注的三条证据，本文件复核未发现反例）：
① `baseprotocalstruct.luac` proto#7 `Encode` 用 `ipairs(m_value_names)` 与 `WriteFMT(m_format, ...)`
**按位置配对** ⇒ 名字顺序 = 线序，**不反转**；
② 交叉对齐：`Dsc20010skills` 名字序 `bid, step, last_use, cd` + 格式串 `ICHH`，与 `SC_20012.cooldown`
内联 spec `bid@I##last_use@H` 只有**不反转**才自洽；
③ `summon_play` 16 字段与内联 spec **16/16 逐字段逐类型一致**。

---

## 2. 解出的子结构（★ 本文核心）

### 2.1 `SC_20010` 的单位字段（已有，此处补齐子结构）

`SC_20010.fighter_info_list[]` 顶层 18 字段（含 `specials`），子结构：

| 子结构 | 线序（`name:type`） | 格式串 |
|---|---|---|
| `animate_res` | `ant_id:u16, ant_val:string, ent_lev:u8, dis_method:u8` | `HsCC` |
| `skills` | `bid:u32, step:u8, last_use:u16, cd:u16` | `ICHH` |
| `specials` | `key:u8, val:u32` | `CI` |

### 2.2 `SC_20012.skill_play[]`（小回合技能播放）

顶层字段：`order:u8, user_id:u16, skill_id:u32, father_id:u32, father_skill_id:u32, passive_skill_id:u32, user_anger:u16, talk:s, notice:s, magic_play[]:Dsc20012magic_play, summon_play[]:Dsc20012summon_play`
另加独立数组：`cooldown[] = (bid:u32, last_use:u16)`

**`Dsc20012magic_play`（proto#26）—— 10 字段**：

| # | 字段 | 类型 | 说明 |
|---|---|---|---|
| 1 | `order` | `uint8` | 出手序 |
| 2 | `target_anger` | `uint16` | 目标怒气 |
| 3 | `target_id` | `uint16` | 目标单位 id |
| 4 | `source_id` | `uint16` | 施法者单位 id |
| 5 | `hit` | **`int8`** | 命中/伤害值（**有符号**，可为负=治疗） |
| 6 | `hp_max` | `uint32` | 目标最大 HP |
| 7 | `hp` | `uint32` | 目标结算后 HP |
| 8 | `is_target_die` | `uint8` | 目标是否死亡 |
| 9 | `target_talk` | `string` | 目标台词 |
| 10 | **`magic_list`** | `TABLE(Dsc20012magic_list)` | **★ 效果/状态列表（buff 载体）** |

**`Dsc20012summon_play`（proto#34）—— 16 字段**（单位快照，与 `SC_20013.summon_play` 同形）：

| # | 字段 | 类型 | | # | 字段 | 类型 |
|---|---|---|---|---|---|---|
| 1 | `id` | `uint16` | | 9 | `group` | `uint8` |
| 2 | `rid` | `uint32` | | 10 | `hp_max` | `uint32` |
| 3 | `srv_id` | `string` | | 11 | `hp` | `uint32` |
| 4 | `name` | `string` | | 12 | `anger` | `uint32` |
| 5 | `lev` | `uint16` | | 13 | `is_auto` | `uint8` |
| 6 | `sex` | `uint8` | | 14 | `animate_res` | `TABLE` |
| 7 | `career` | `uint16` | | 15 | `skills` | `TABLE` |
| 8 | `pos` | `uint8` | | 16 | `specials` | `TABLE` |

### 2.3 ★ `magic_list` 元素（proto#24 / proto#37）—— **buff/状态条目**

**格式串 `iiChhC`，6 字段**（两位独立读取器 #24 与 #37 的内容完全一致）：

| # | 字段 | 类型 | 语义（由客户端消费代码反推，见 §3） |
|---|---|---|---|
| 1 | **`magic_bid`** | **`int32`** | 效果配置 ID → `Config.SkillMagic[magic_bid]`（12665 行）|
| 2 | **`change_hp`** | **`int32`** | 每回合 HP 变化（DoT/HoT；有符号）|
| 3 | **`duration`** | **`uint8`** | **★ 持续/剩余回合数** |
| 4 | **`per`** | **`int16`** | 百分比数值（配置模板里的 `{per}`）|
| 5 | **`val`** | **`int16`** | 绝对值（配置模板里的 `{val}`）|
| 6 | **`fold`** | **`uint8`** | **叠加层数**（UI 渲染为 `(%s层)`）|

> **⇒ 第 2 个未知项的答案：buff 剩余回合数 = `magic_list[].duration:uint8`，确实下发。**
> 且不止剩余回合：**每回合 HP 变化（`change_hp`）、层数（`fold`）、数值与百分比（`val`/`per`）也一并下发。**
> 服务端**不需要**让客户端自己计时 —— 这是与 CXEngine 相反的、明显更强的设计。

### 2.4 复现命令

```powershell
python tools/proto_spec.py cmds 20012 20013     # 顶层字段
python tools/proto_spec.py list 200              # 2xx 段全部消息
python tools/dsc_spec.py --file 200              # 16 个子结构读取器（含 fmt + 线序名）
python tools/dsc_spec.py Dsc20012                # 只看名字含 Dsc20012 的两个
```

`dsc_spec.py --file 200` 的关键原文输出（节选，`proto#24` 即 `magic_list`）：

```
cmd_resolve_200.luac   proto#24   fmt=iiChhC
      magic_bid              int32
      change_hp              int32
      duration               uint8
      per                    int16
      val                    int16
      fold                   uint8
```

---

## 3. 客户端如何消费 `magic_list`（证明 `duration`/`fold` 的语义）

### 3.1 消费点扫描

命令（本工作区脚本，扫 `assets/src/game/**` 全部 `.luac`，找同时引用相关字段的 proto）：

| 模块 | proto# | 同时引用的字段 |
|---|---|---|
| `battle_role.luac` | #4 | `buff_icon, duration, fold, magic_list` ← **buff 提示框** |
| `battle.luac` | #61 | `buff_icon, duration, fold, magic_bid, magic_list` |
| `battle.luac` | #126 | `change_hp, duration, fold, magic_bid, magic_list` ← **效果增删** |
| `battle.luac` | #57 / #62 / #117 / #124 / #127 | `magic_bid`/`magic_list` |
| `battle.luac` | #29 / #36 / #59 / #109 / #137 | `change_hp` / `magic_list` |
| `skill_act.luac` | #77 | `magic_bid, magic_list` |

### 3.2 `battle_role.luac` proto#4 —— buff 提示框（语义最直白）

命令：`python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle_role.luac 4 0 90`

该 proto 是长按单位后弹出 `buff_info_layer` 的函数。其常量表（`kgc`）直接给出了渲染规则：

```
#18 'duration'      #19 '(%s层) '      #21 'fold'
#22 '{val_per}'     #23 'val'          #26 'per'        #29 '{per}'
#33 'magic_desc'    #34 'bid'          #36 'SkillMagic' #37 'Config'   #38 'type'
#39 'magic_list'
#40 '<div fontcolor=#ffff00>控制效果</div>'
#41 '<div fontcolor=#ffff00>增益效果</div>'
#42 '<div fontcolor=#ffff00>减益效果</div>'
#49 'buff_icon'     #44 'magic_effect' #45 'getBattleRes'
```

对应的反汇编逻辑（节选）：

```
  42  GGET    A=6  D=16          ; ipairs
  44  TGETS   A=7  B=7  C=17     ; self.buff_icon
  46  ISNEXT  A=9  D=32925       ; for _, v in ipairs(self.buff_icon) do
  ...
  75  GGET    A=12 D=18          ; 'duration'
  77  KSTR    A=14 D=24          ; '减益效果'
  ...
  87  KSTR    A=14 D=25          ; '增益效果'
  ...
  95  KSTR    A=14 D=26          ; '控制效果'
  ...
 105  TGETS   A=16 B=15 C=28     ; v.type
 109  TGETS   A=16 B=16 C=30     ; Config.SkillMagic
 111  TGETS   A=17 B=15 C=32     ; v.bid
```

⇒ **确认**：
- 客户端遍历自己的 `buff_icon`（由 `magic_list` 累积而来），逐条渲染
  **类别标题（控制效果 / 增益效果 / 减益效果）+ 图标 + `duration` + `fold`（"%s层"）+ `val`/`per`**
- 类别 `type` 来自 **`Config.SkillMagic[bid].type`**，不是线上的字段
- 图标走 `PathTool.getBattleRes('magic_effect', ...)`，描述走 `magic_desc` 模板 + `{val}`/`{per}`/`{val_per}` 占位替换

### 3.3 `battle.luac` proto#126 —— 效果增删（`specMagicEffectAdd` / `specMagicEffectRemove`）

命令：`python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle.luac 126 0 60`

```
   3  TGETS   A=5  B=3  C=2      ; entry.duration
   5  ISGE    A=6  D=5           ; if entry.duration >= 0 then
  17  TGETS   A=5  B=2  C=6      ; self.show_list
  23  KSTR    A=6  D=8          ; 'bid'
  24  TGETS   A=7  B=3  C=9      ; entry.magic_bid
  36  TGETS   A=5  B=5  C=11     ; table.insert
  38  TDUP    A=7  D=12         ; { }
  40  TSETS   A=8  B=7  C=8      ; { bid = entry.magic_bid }
```

常量：`#0 'effectUser' #3 'cycle' #4 'location' #5 'specMagicEffectAdd' #6 'specMagicEffectRemove'`
`#9 'change_hp' #10 'res_down' #11 'res_up' #12 'fold' #13 'magic_list' #14 'res_buff_up'`
`#19 'magic_bid' #20 'bid' #21 'keyfind' #22 'show_list' #25 'must_play' #26 'duration'`

⇒ **确认**：线上 `magic_bid` 到客户端后改名为 `bid`（`{ bid = entry.magic_bid }`）用于查 `Config.SkillMagic`；
`duration >= 0` 是"还在生效"的判断；`res_up`/`res_down`/`res_buff_up`/`cycle`/`location`/`must_play`
均来自配置（决定表现资源与循环方式）。

---

## 4. `specials` = 伙伴/宠物**外观**通道（★ 纠正上一轮的判断）

### 4.1 全部被使用的 key（穷举扫描）

扫描范围：`assets/src/game/**` 全部 `.luac`，匹配字节码模式
`KSTR 'key'` → `KSHORT <n>` → `TGETS 'specials'`（即 `keyfind('key', n, vo.specials)`）。

**结果：只有 8 个 key（1,2,4,5,6,7,8,9），全部集中在 `battle_role.luac` proto#2（`createBattleRole`）。**

### 4.2 逐 key 语义（从消费代码反推）

命令：`python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle_role.luac 2 0 400`

| key | 消费路径 | 语义 |
|---|---|---|
| **1** | `.val` → `Config.PartnerBase[val].resource` / `.by_resource` → 单位模型资源 `res` | 伙伴模型资源（pet 分支）|
| **2** | `.val` → `Config.PartnerBase[val].resource` / `.by_resource` → `res` | 伙伴模型资源（另一分支）|
| **4** | `.val` → `partner_color`；并影响 `RoleCareer` / `getCareerRes` / `bid`；另一处 @327 → `pingfen` | 伙伴配色 / 评分 |
| **5** | `.val` → `Config.PartnerStageEffect[val].has_surface` / `.effect` → `effect_spine_name`；`.sp_resource` → `shipin_res` | 伙伴**阶段特效** + 视频资源 |
| **6** | `.val` → `Config.PartnerHaloEffect[val].effect` → `ring_effect_name` | 伙伴**光环/戒指特效** |
| **7** | `.val` → `Config.PartnerRebirthEffect[val].effect` → `rebirth_effect_name`；参与 `rebirth` 名前缀 | 伙伴**重生特效** |
| **8** | `.val` 与 key=7 配合参与 `PartnerRebirthEffect` 判定 | 重生相关 |
| **9** | `.val` → `isFetterPartnerBorn`（布尔）| **羁绊伙伴**出生标记 |

- `keyfind` 是通用"按键查表"辅助函数（`battle_role.luac` proto#2 常量表含 `'keyfind'`、`'key'`、`'val'`）。
- 相关常量：`'PartnerBase'`、`'PartnerStageEffect'`、`'PartnerHaloEffect'`、`'PartnerRebirthEffect'`、
  `'partner_color'`、`'rebirth_effect_name'`、`'ring_effect_name'`、`'effect_spine_name'`、`'pingfen'`。

### 4.3 ⇒ 结论

**`specials` 与"回合制 buff / 控制状态"完全无关。** 它是**伙伴/宠物的外观属性通道**：
`val` 是 `Config.Partner*` 系列的**配置 ID（uint32）**，用于决定模型、配色、阶段特效、光环、重生特效、是否羁绊伙伴。

**类型自证**：`specials.val` 是 `uint32`（配置 ID 空间），而 buff 剩余回合是 `duration:uint8`——
**两者在类型与语义上都不是一回事**。

> ⚠️ **纠正上一轮的报告**：我在给上级的汇报与 `reuse_candidates.md` §1.④ 里写过
> 「JSTM **已有**载体：单位上的 `specials[] = (key:u8, val:u32)`」。
> **该表述错误**：`specials` 不是 buff 载体。**正确的 buff 载体是 `magic_list[]`**（§2.3）。
> 已在 `reuse_candidates.md` §1.④ 与 §4 追加订正框。

---

## 5. 配置侧：`Config.SkillMagic` 与 `Config.SkillMagicType`

### 5.1 `Config.SkillMagic`（`assets/src/config/config_skill_magic.luac`）

- **12665 行**（proto#0 的 `kgc` 里 TableConst 计数）。
- 由 proto#1 逐行 `TSETS`，字段名顺序（proto#1 常量表原文）：

```
must_play, cycle, location, icon, effect_type, magic_desc, desc,
res_down, res_buff_up, res_up, duration, target_camp, per, grade, flag, type, bid, data
```

| 字段 | 作用（据 §3 客户端消费 + 命名） |
|---|---|
| `bid` | 效果 ID（= 线上 `magic_bid`）|
| `type` | **效果类别**（→ `SkillMagicType`，UI 显示控制/增益/减益）|
| `effect_type` | 效果属性 ID（→ `SkillMagicType`，见 5.2）|
| `duration` | 默认持续回合 |
| `per` | 百分比 |
| `icon` | buff 图标 |
| `magic_desc` | 描述模板，含 `{val}` / `{per}` / `{val_per}` 占位（实例：`'潜伏 躲闪率+{val_per}%'`）|
| `desc` | 名称（实例：`'潜伏'`）|
| `must_play` | 是否必须播放表现 |
| `cycle` / `location` | 表现循环方式 / 挂点 |
| `target_camp` | 目标阵营 |
| `res_up` / `res_down` / `res_buff_up` | 上/下/增益 表现资源 |
| `grade` / `flag` / `data` | 等级 / 标志 / 附加数据 |

实例（proto#0 第 2 行原文）：
`[None, 910290, 1225, '', 0, 0, 2, 2, '', None, '', '潜伏', '潜伏 躲闪率+{val_per}%', 2, 11, 0, 1, 0]`

### 5.2 ★ `Config.SkillMagicType` —— 31 个效果属性 ID（proto#2 的 hash 常量，全文）

| ID | 名称 | ID | 名称 | ID | 名称 |
|---|---|---|---|---|---|
| 1010 | `atk_s` | 1110 | `hurt` | 1220 | `hit_rate` |
| 1020 | `atk_p` | 1111 | `dam_s` | 1225 | `dodge_rate` |
| 1030 | `def_s` | 1112 | `dam_p` | 1230 | `crit_rate` |
| 1040 | `def_p` | 1115 | `be_hurt` | 1235 | `tenacity_rate` |
| 1050 | `hp_max` | 1116 | `be_hurt_s` | **1240** | **`control`（控制）** |
| 1060 | `atk_speed` | 1117 | `be_hurt_p` | **1250** | **`anti_control`（抗控）** |
| 1070 | `hit` | 1120 | `be_cure` | 1270 | `crit_hurt` |
| 1080 | `dodge` | 1130 | `cure`（治疗）| 1280 | `reduce` |
| 1090 | `crit` | 1140 | `reduce` | | |
| 1100 | `tenacity` | 1141 | `res_s` | | |
| | | 1142 | `res_p` | | |
| | | 1200 | `red_def_s` | | |
| | | 1210 | `red_def_p` | | |

**命名规律**（对 JSTM 建模有用）：`_s` = 固定值（value）、`_p` = 百分比（percent）、
`_rate` = 几率、`be_*` = 受方视角、`red_*` = 减免、`res_*` = 抗性。
配合 §2.3 的 `val`(int16) / `per`(int16)，一个效果可按 `SkillMagicType` 决定"加固定值还是加百分比"。

### 5.3 复现命令

```powershell
python tools/extract_config_table.py assets/src/config/config_skill_magic.luac   # 需先解出文件；本文件用直接 zipfile 读
```

本文用直接 `zipfile` + `luajit_bc.parse_bytes` 读取（脚本见 §6），因为
`extract_config_table.py` 需要磁盘上的 `.luac` 路径，而本任务**不允许把 APK 内容写到 `cankao/`**。

---

## 6. 本文所有结论的复现脚本（可整段粘贴运行）

```powershell
# ① 消息顶层字段 + proto 索引
Set-Location C:\Users\xu\Desktop\DSH
python tools/proto_spec.py cmds 20010 20012 20013 20015

# ② 全部 Dsc 子结构（含 magic_list = iiChhC）
python tools/dsc_spec.py --file 200

# ③ specials 消费点（battle_role.luac proto#2）
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle_role.luac 2 0 400

# ④ buff 提示框（duration / fold / 控制-增益-减益）（battle_role.luac proto#4）
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle_role.luac 4 0 90

# ⑤ 效果增删（magic_bid -> bid）（battle.luac proto#126）
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/battle/battle.luac 126 0 60
```

---

## 7. 对 CXEngine 对照结论的最终回填

| 对照维度 | CXEngine（YZXY） | JSTM 1.4.9（本轮解出后） | 判定 |
|---|---|---|---|
| **限时状态（buff/debuff）是否上线** | ❌ **完全不上线**。buff 存服务端 `__actors_buffs__[actor_id][buff_id]`，**不在 `Actor` 属性数组内、无任何下行消息**；客户端只能靠 `skill/26.lua` 的 `IsClient()` 分支**重放同一段判定**来"猜" | ✅ **逐条上线**。`magic_list[] = (magic_bid, change_hp, duration, per, val, fold)` 挂在 `SC_20012.skill_play[].magic_play[]` 与 `SC_20013.magic_play[]` 上 | **CXEngine 弱、JSTM 强**；不要学 CXEngine 的"重放" |
| **剩余回合** | ❌ 服务端 `buff.turn_count_down` 私有，客户端无 | ✅ `magic_list[].duration:uint8` | JSTM 已具备，**无需新增** |
| **叠加层数** | ❌ 无概念 | ✅ `magic_list[].fold:uint8`（UI 显示 `(%s层)`）| JSTM 已具备 |
| **每回合 HP 变化（DoT/HoT）** | ⚠️ 靠 `BuffOnNextTurn` 服务端改 HP，再走**通用属性同步**（`PROP_HP` 本身在 `sync=1`）；但**没有"这是哪个 buff 造成的"这一信息** | ✅ `magic_list[].change_hp:int32` **与 `magic_bid` 绑定下发** | JSTM 的语义更完整（能定位到具体效果）|
| **效果类别（控制/增益/减益）** | ⚠️ 只有 `buff.tsv` 的 `type` 列（内容为空或数字），且**不上线** | ✅ 配置 `Config.SkillMagic[bid].type` → UI 直接渲染"控制效果/增益效果/减益效果" | — |
| **效果属性 ID 空间** | ⚠️ 硬编码在 Lua 公式里（`PROP_*` + 门派分支）| ✅ `Config.SkillMagicType` **31 个结构化 ID**（1010–1280，`_s`/`_p`/`_rate`/`be_`/`red_`/`res_` 命名规整）| JSTM 的表驱动更干净 |
| **单位状态每回合重推** | ❌ 无（`BattleMT:Serialize()` 只在建/开战时发一次）| ✅ `SC_20013.summon_play[]` 16 字段每回合带 `hp_max/hp/anger/is_auto/animate_res/skills/specials` | JSTM 强 |
| **效果配置规模** | `assets/tables/buff.tsv`（约 55 行，`ID/name/type/buff_anim/turn`，**`turn` 列大量为空且被脚本覆盖**）| `Config.SkillMagic` **12665 行** + `SkillMagicType` 31 项 | 量级差异；JSTM 是真正的表驱动 |

**⇒ 一句话**：**CXEngine 的 buff 体系（表 + `buff/<id>.lua` 回调 + 回合结算）在"服务端逻辑组织"上值得借鉴，
但它的"状态同步"是缺失的；JSTM 的 `magic_list` 已经把 CXEngine 缺的那一半做完了。**
因此对 JSTM 的正确动作是 **"解出语义、照它现有契约实现"**，而**不是**"新增 buff 字段"。

---

## 8. 仍未解出 / 边界（如实标注）

| 项 | 状态 | 要什么才能解 |
|---|---|---|
| **`magic_list` 是"全量重列"还是"仅变化项"** | ⛔ **不可取证（本轮结论）** —— 详见 §9。**原版服务端数据本工作区明确「不可得」**（`report/battle_restore_status.md` §七、`analysis/1.4.9/battle/monster_data_model.md` §3.1、`analysis/1.4.9/battle/battle_flow.md` §六 均记载「原版服务端数据，APK 内无取证途径」）；现存**全部**战斗捕获都是 **客户端 ↔ 我们自己 `mock_server.py`**（`logs/1.4.9/battle/battle_raw_tcp.log`），而 mock 发的是**空 `magic_list`**（`server/battle.py:305`）⇒ **捕获里没有可判别的 `magic_list` 内容** | **无解（除非出现原版服务端）**。⇒ **改为由 JSTM 自行决定**：客户端**容忍空 `magic_list`**（§9.3 实测跑完 4 回合），且 `duration` 每回合必变 ⇒ **推荐实现为"每回合全量重列"**（最稳、最易实现、与 `summon_play` 每回合重推同构） |
| `specials` 是否为**全量快照还是增量** | 【未解出】—— 客户端只在 `createBattleRole`（**创建单位**时）消费 `specials`，之后**未见增量更新路径**；倾向"**创建时一次性给定**"（因为是外观属性），但**未找到反证也未有直证** | 同上（原版服务端不可得）；捕获里 mock 发的 `specials` 亦为空 |
| 战斗期间客户端的**主动上报**有哪些 | ✅ **本轮解出**（§9.2）：`CS_20021` 是战斗内客户端**唯一**主动发出的战斗消息（在收到 `SC_20020` 之后）；`CS_20011`/`CS_20014` **确认零次** | — |
| `SC_20012.skill_play[].summon_play` 与 `SC_20013.summon_play` 的**分工** | 【未解出】—— 两处同形（16 字段），`SC_20012` 侧用于"技能播放中顺势刷新单位"，`SC_20013` 侧用于"回合开始刷新"，但**触发边界未取证**；捕获里 mock 两类都发空表，无法判别 | 原版服务端数据（不可得） |
| `Config.SkillMagic` 的**行内字段精确对齐** | 【待验证】—— proto#0 的行是 17/18 元素数组，proto#1 给出的字段名有 19 项（含一个嵌套 TableConst），**逐位置对齐需再验**（不影响 §2.3 的线上结构结论） | 用 `extract_config_table.py` 落盘后逐行校验 |
| `SkillMagic` 的 `type` **数值→类别**映射 | 【未解出】—— UI 代码里出现与 `1` 和 `0` 的比较（`ISNEN A=9 D=1` / `D=0`），指向 1=减益、0=增益、其它=控制，但**未取到 `SkillMagicType`/`SkillMagic.type` 的枚举数据**（proto#2 的 hash 是 `effect_type` 空间，不是类别空间）| 找 `SkillMagic.type` 的取值分布 |
| `Dsc20010`/`Dsc20015` 全量字段 | 【部分解出】—— 子结构已解（§2.1），顶层 18/16 字段见 `battle.md` §5.6 | — |
| **CXEngine 侧** | 本文只复核了 `battle.md` 已确认的部分，未新增 CXEngine 侧读取 | — |

---

## 9. 真机捕获复核（client ↔ 我们自己的 mock）与"不可取证"的证明

> 本轮额外读了 `logs/1.4.9/battle/` 下 6 个捕获与 `server/logs/tcp.log`（**只读**）。
> 结论有两个：① **捕获不能回答"原版 full vs delta"**（它是 mock 的流量）；② 但它**能从客户端运行期反过来印证本文的字段表**，
> 并给出**客户端容忍度**这一可直接用于 JSTM 的工程结论。

### 9.1 捕获的性质（为什么不能回答原版语义）

`logs/1.4.9/battle/battle_raw_tcp.log`（77 行，`[18:53:18]`–`[18:57:29]`）原文节选：

```
[18:53:19]   << 20010 SC_20010 battle init fighters=2 mon_hp=2400 role_hp=4321 (127 bytes)
[18:53:22]   << 20012 SC_20012 skill_play battle round=1 (41 bytes)
[18:53:22]   << 20013 SC_20013 round_start battle round=1 (53 bytes)
[18:53:22]   << 20012 SC_20012 skill_play battle round=1 (41 bytes)
[18:53:22]   << 20013 SC_20013 round_start battle round=1 (39 bytes)
[18:53:24]   << 20012 ... round=2 ...
...
[18:53:29]   << 20020 SC_20020 result=1 (7 bytes)
[18:53:30]   >> cmd=20021 ? body(4)=07 66 00 00
[18:53:32]   << 20023 SC_20023 type=0 result=1 role_hurl=2 (96 bytes)
```

- **`SC_20012` 只有 41 字节、`SC_20013` 只有 39/53 字节** ⇒ 不可能含 12665 行配置下的真实 `magic_list`。
- 核对我们自己的实现 `server/battle.py`：`:281 b += w_u16(0)  # summon_play（空）`、
  `:305` 注释 `magic_list: D|Dsc20013magic_list| = magic_bid@i, change_hp@i, duration@C, per@h, val@h, fold@C`
  ⇒ **mock 只按格式串发了"计数 0"的空数组**。
- 节拍 `18:53:22 → 24 → 27 → 29` = **约 2.5 秒/回合**，与 mock 的自续期定时器一致（`battle_flow.md` §三：「服务端在 `SC_20010` 之后**自己按节拍推进**（2.5 秒/回合，自续期）」），
  **不是**原版节拍的证据。
- ⇒ **因此"`magic_list` 全量还是增量"在现有资产下不可判定。** 原版服务端数据本工作区多处明确记载**不可得**
  （`battle_restore_status.md` §七 #1/#2/#5、`monster_data_model.md` §3.1、`battle_flow.md` §六）。
  **本报告在此停止追这条线，并按 §8 给出的"自行决定"处理。**

### 9.2 捕获给出的新增事实（可用）

| # | 事实 | 依据 |
|---|---|---|
| 1 | **战斗内客户端唯一主动上报 = `CS_20021`**（收到 `SC_20020` 之后立刻发，body 4 字节 = 被击败怪物的 `mon_id`）| `[18:53:30] >> cmd=20021 body(4)=07 66 00 00`；另一次 `=00 00 4e 21`/`01 00 4e 36` 亦为 mon id |
| 2 | **`CS_20011` / `CS_20014` 零次**（与前一轮结论一致，本轮在 4 场完整战斗捕获中再次确认）| 全文无 `cmd=20011`/`cmd=20014` |
| 3 | **消息次序固定为 `SC_20020` →（客户端 `CS_20021`）→ `SC_20023`** | 三条时间戳 18:53:29 / 30 / 32 |
| 4 | **每回合出现两组 `(SC_20012, SC_20013)`**（先己方、后敌方；或按施法单位分组）| 每 round 2 组 |
| 5 | ⚠️ **`CS_20500/20501/20504/20800` 不是战斗命令**：查 `proto_spec.py cmds 20500 20501 20504 20800` ⇒ `20500/20501` = **好友**（`role_id/srv_id/name/lev/sex/career/intimacy`、`friend_list`）、`20504` = **任务列表**（`mission_list`）、`20800` = **英雄/背包/外观阶段**（`stage/power/luck/skill_list/items/surface_list`）。它们出现在 `20002` 之前只是**界面刷新**，**不要误当战斗协议** | 字节码定义 |

### 9.3 ★ 客户端**容忍度**（可直接用于 JSTM 的工程结论）

`logs/1.4.9/battle/battle_action.log`（客户端 `bt_in` 探针，记录**客户端反序列化后的表**）显示，
客户端在 mock 只发**空** `magic_list`/`summon_play`/`order_list`/`cooldown` 的情况下，
**完整跑通 4 回合 + 结算**，且逻辑链全绿（`battle_render_chain.log`：
`playEnterEffect → start → createBattleScene → addRole×2 → roleReady×2 → playRoundStart×4 → playMagic → result → clear → exitFight`）。

探针原文（`battle_action.log:12`）：

```
bt_in scRoundStart_n1_a1__round_1_round_wave_1_
      magic_play__1__order_.._hp_.._source_id_.._**magic_list**_.._is_target_die_.._target_id_.._..___
      **order_list**____time_0_wave_no_1_**summon_play**____
```

⇒ **两条工程结论**：
1. **客户端对战斗消息是"宽容解析"**：缺失/空的 `magic_list`、`summon_play`、`order_list`、`cooldown`
   **不会**导致解析失败或卡住回合 ⇒ **buff 可以后置实现**，先跑通无 buff 的战斗再逐条加，风险低。
2. **反过来印证了本文的字段表**（**交叉验证**，非独立来源）：客户端运行期解析出的键与 §2 / §5.6 的静态规格**逐一对应** ——
   `round`/`round_wave`/`wave_max`/`wave_no`/`time`/`is_observer`/`atk_formation_lev`/`def_formation_lev`/`effect_id`/`order_list`/`fighter_info_list`
   （`scFightData`）、`round`/`skill_play`/`cooldown`（`scFightRound`）、
   `magic_play{order,hp,source_id,**magic_list**,is_target_die,target_id,…}`/`order_list`/`summon_play`（`scRoundStart`）。
   **其中 `magic_list` 作为 `magic_play` 的子键被客户端实际创建出来** ⇒ §2.3 的结构在**运行期**成立。
   （另：`server/battle.py:33` 早已独立还原出同一格式串 `magic_bid@i, change_hp@i, duration@C, per@h, val@h, fold@C`，
   与本轮从 `cmd_resolve_200.luac` 直读的结果**一致** ⇒ 相互印证。）

### 9.4 mock 的报文尺寸基线（供未来对比）

| 消息 | mock 实现尺寸 | 说明 |
|---|---|---|
| `SC_20010` | 127 B（2 单位）/ 130 B | 单位 `specials`/`skills`/`animate_res` 均发空 |
| `SC_20012` | 41 B | `magic_play` 空、`summon_play` 空、`cooldown` 空 |
| `SC_20013` | 39 B / 53 B | `magic_list` 空、`summon_play` 空、`order_list` 空 |
| `SC_20020` | 7 B | 仅 `result:u8` |
| `SC_20023` | 96 B / 99 B | — |

⇒ 将来若拿到原版服务端，**只要 `SC_20012/20013` 明显大于 ~100 B，就说明原版确实在发 `magic_list` 内容**；
再对比同单位相邻回合的 `magic_list` 长度是否随 `duration` 递减而收敛，即可判定 full/delta。**这条判据已备好，等数据。**

---

## 10. 一句话总结（含本轮边界）

**三个未知项全部解出：`magic_list` 元素 = `(magic_bid:i32, change_hp:i32, duration:u8, per:i16, val:i16, fold:u8)`，
`duration` 就是 buff 剩余回合、`fold` 是层数；`specials` 则与 buff 无关，是伙伴/宠物的外观配置通道（8 个 key）。**
⇒ 上一轮"JSTM 已有 `specials` 载体"的说法**已订正为"JSTM 已有 `magic_list` 载体"**；
CXEngine 与 JSTM 在状态同步上的差距**比我上一轮判断的更大**，且**JSTM 是强的一方**。

**本轮边界（必须交代）**：追问"`magic_list` 是每回合全量重列还是仅变化项"时，
本轮**证明它是不可取证的** —— 原版服务端数据本工作区多处明确记载**不可得**，
而现存全部战斗捕获都是**客户端 ↔ 我们自己的 mock**，mock 发的是**空 `magic_list`**（`server/battle.py:305`），
捕获里没有可判别的内容（§9.1）。
⇒ **不再追这条线**，改为给出可执行决策：**JSTM 按"每回合全量重列"实现**（理由：客户端容忍空表 §9.3、
`duration` 每回合必变、与 `summon_play` 每回合重推同构）；并备好判据（`SC_20012/20013` 尺寸基线 §9.4），
一旦拿到原版数据即可判定。

**本轮另有两项副产品**：① 客户端 `bt_in` 探针**从运行期反证了本文的字段表**（含 `magic_list` 确为 `magic_play` 子键）；
② 实测**客户端对空 `magic_list`/`summon_play`/`order_list`/`cooldown` 宽容**，可完整跑完 4 回合 ⇒ **buff 可后置实现**。
