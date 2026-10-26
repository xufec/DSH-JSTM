# PHASE 1 — V 系列：**服务端侧参照值**清单（供 UI ↔ 服务端对表）

> 目的：V 系列标定 = 「客户端 UI 显示值」×「服务端真实值」。本文件固化**服务端这一半**，
> 使剩余面板标定变成机械比对。
> 数据源：`GET /DSH_ADMIN/*`（只读）。原样落盘于
> `analysis/extraction/phase1_server_state_reference.json`（27 个端点，78 KB）。
> 只读取证，未改服务端代码。

---

## 一、已完成的 V 对表（前几轮）

| 项 | 客户端 UI | 服务端 | 判定 |
|---|---|---|---|
| 10 项基础属性 + 战力 724112 | 属性面板逐项 | `/DSH_ADMIN/power` | **VERIFIED**（零偏差）|
| L70 经验上限 2,600,094 | 经验条分母 | （客户端本地表）| **CONFIRMED** |
| 货币显示"截断到万" | `180万/990万/9999万` | gold/coin/coupon | **CONFIRMED** |
| 挂机地图表 8 张 + 等级区间 + 推荐 | 挂机面板两卡 | `server/_guaji.json` | **VERIFIED** |

## 二、服务端参照值清单（本轮固化）

| 系统 | 端点 | 服务端当前值 | 待对照的 UI 面板 | 状态 |
|---|---|---|---|---|
| 战力 | `rank_breakdown` | total **724112**；**9 个分项全 0**（端点自带注释 `dims placeholder pending V8/V11 evidence`） | 属性面板（只显示总分）| ⚠ **分项是占位** ⇒ 战力拆分仍 UNKNOWN/INFERENCE |
| 翅膀 | `wing` | `wing_id=8801, color=3, power=999, star=0` | 更多→翅膀 | 待对表 |
| 神器 | `shenqi` | 2 条：`10001 lev7 star3 status1` / `10002 lev1 …` | 神器面板 | 待对表 |
| 命格 | `mingge` | ≥2 条：`21001 lev2` / `21002 lev1` | 命格面板 | 待对表 |
| 法宝 | `fabao` | 2 条：`id1 bid20001 lev6 stage2 pos1` / `id2 …` | 法宝面板 | 待对表 |
| 坐骑 | `ride` | `jie=1 lev=10`，`attrs` 全 0 | 坐骑面板 | 待对表 |
| 魂兽 | `lingshou` | `jie=2 lev=5`，`attrs` 全 0 | 魂兽面板 | 待对表 |
| 技能 | `skill_show` | catalog **105**；已学 1 条：`10020 lev2` | 魂技面板 | 待对表 |
| 伙伴 | `partner_show` / `hero` | catalog **53**；owned **18** | 伙伴面板 | 部分（面板曾打开过）|
| 副本 | `dungeon_list` | catalog **34**，rows **34** | 副本列表 | 待对表 |
| 商城 | `mall_list` | normal **110** / week **24** / xian **45** | 商城页签 | 待对表（实付金额为 HANDOFF 缺口）|
| 邮件 | `mail_list` | **195** 封 | 邮件箱 | 待对表 |
| 成就 | `ach_list` | **342** 条 | 成就面板 | 待对表 |
| 称号 | `title` | **`titles: []` 空** | 称号页签 | ⚠ 服务端空 ⇒ UI 应显示空列表（可用于验证"回空=真话"）|
| 天赋树 | `tree` | `tree_lev=0, strength_rest=48, strength_name=北斗, max_lev=5` | 提升/天赋 | 待对表 |
| 椅子(专精) | `chair` | `stage=5, power=0` | — | 待对表 |
| 建筑/学习 | `build` | `lev=5, learn_list=[30001,30002]` | — | 待对表 |
| 投资 | `invest` | `itype=0, day=0, geted=0`；types `[2,3,7,8]` | 投资面板 | 待对表 |
| 祈福 | `qifu` | `tiers=[1,2,3]`；`qifu.2=0` | 祈福面板 | 待对表 |
| BOSS | `bosskill` | `boss_count=27`，`killed: []` | BOSS 面板 | 待对表 |
| 挂机 | `afk_status` | `claimed=true, minutes=0, pending_gold=0, pending_exp=0` | 挂机面板 | ⚠ 与"进图断点(10206)"一致 |
| 背包/装备 | `status.bag` / `status.equip` | bag 6 项（bid 28560/28515/21403/…）；equip 6 槽（40003/41803/41403/41603/41003/41213）| 背包面板 | 待逐项对表 |

## 三、本轮**新增的 R 系列**：战斗族 SC 结构（来自只读 `battle_replay`）

发现 `/DSH_ADMIN/battle_replay?mon_id=20001` 返回的是**服务端构造的 SC 字节**（hex），
这是本项目**唯一**能拿到 SC 侧真实字节的只读通道（`tcp_*.bin` 只落盘 CS 方向）。
用 SC 规格解码后，**战斗族全部 SC 帧结构 = CONFIRMED**：

| SC | 字段（解出） | 作用 |
|---|---|---|
| `20002` | `{code:1, msg:""}` | 开战应答 |
| `20010` | `{round, round_wave, wave_max, wave_no, atk/def_formation_type/lev, is_observer, effect_id, order_list[], fighter_info_list[]}` | 开场/阵容 |
| `20012` | `{round, skill_play[{order, user_id, skill_id, father_id, father_skill_id, passive_skill_id, user_anger, talk, notice, magic_play[], summon_play[]}], …}` | 技能演出 |
| `20013` | `{round, round_wave, time, wave_no, magic_play[{order, target_anger, target_id, source_id, **hit**, **hp_max**, **hp**, is_target_die, target_talk, …}]}` | 伤害结算 |
| `20020` | `{result:1}` | 结果 |
| `20023` | `{type, result, role_hurl_list[{rid, srv_id, name, group, lev, sex, career, **hp_max**, **hp**, **hurt**, master_rid, master_srv_id, id}], val_list, msg}` | 结算快照 |

`fighter_info_list` 实解（mock 值）：
```
玩家: rid=1001 srv_id="1"  name="DSH" lev=70 career=1 pos=1 group=1 hp_max=7305 hp=7305
怪物: rid=20001 srv_id="mon" name="replay" lev=70 career=1 pos=1 group=2 hp_max=1950 hp=1950
       animate_res=[{ant_id:1, ant_val:"H32000", ent_lev:0, dis_method:0}]
```

### ★ 这一结果对缺口 #1（怪物 HP/ATK 真值）的意义

- **取数字段已定位（CONFIRMED）**：怪物血量在 `SC_20010.fighter_info_list[].hp_max`，
  伤害在 `SC_20013.magic_play[].hit`、`SC_20023.role_hurl_list[].hurt`。
  ⇒ 将来拿到**真服**（或真服残留流量）时，**只需读这几个字段**，不必再猜结构。
- **数值本身仍是 mock 的 TEST_ONLY**（1950 / 1227+…）：**不等于原版真值**，缺口 #1 未闭合。
- **附带澄清**：`SC_20002` 只有 `{code,msg}` ⇒ `CS_20002{mon_id}` 是**开战动作**而非属性查询
  （与上一轮结论一致，双证）。

---

## 四、下一步（V 系列收尾清单）

1. 逐一打开上表"待对表"面板 → 截图 → 与本节服务端值比对（机械工作，每面板 1 轮可批处理）；
2. **优先 **：商城（110+24+45 商品、实付金额）、副本列表（34）、邮件（195）、成就（342）、
   技能（catalog 105 / 已学 10020 lev2）、伙伴（catalog 53 / owned 18）—— 数据量大、可一次覆盖多行；
3. 称号 `titles: []` 空列表 + 战力分项全 0 是**两个"服务端已知占位"**，
   可用于检验「客户端对空数据的渲染是否正常」（D2 渲染类问题的对照组）。
