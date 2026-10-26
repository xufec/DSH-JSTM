# Phase 4A —— 角色协议审计（1.4.9）

> **本阶段只做审计，未修改任何服务器逻辑、未修改 APK。**
> APK：`anzbao/jstm.apk`（1.4.9 / `com.shiyue.dldl.ewan.qihoo`）
> 方法：LuaJIT 字节码反汇编（`RegisterProtocal` 映射 + `cmd_resolve_*` 字段）+ 实机 TCP 日志对照。

---

## 一、角色协议表（从 1.4.9 实际代码确认）

### 1.1 角色系统的注册入口：`role_ctrl.luac`

反汇编 `assets/src/game/role/role_ctrl.luac` 的 `RegisterProtocal` 映射，共 **40 条**，
**角色基础系统 = `103xx` 家族**：

| CMD | handler | 归属 |
|---|---|---|
| **10301** | `rgp_hander10301` | **角色基础信息** |
| **10302** | `rgp_hander10302` | **角色资产/经验** |
| **10303** | `rgp_hander10303` | **角色属性（含 attr 大表）** |
| **10304** | `rgp_hander10304` | 查看指定角色（rid+srv_id → 基础） |
| **10305** | `rgp_hander10305` | 角色（续） |
| **10306** | `rgp_hander10306` | 角色（续） |
| 10320 / 10321 | `rgp_hander10320/10321` | 角色相关 |
| 10324 / 10328 | `rgp_hander10324/10328` | 角色相关 |
| 10342 / 10343 / 10391 | `hander10342/10343/10391` | 角色相关 |
| 10399 | `receiveGmError` | GM 错误回执 |
| 10947–10958 | `hander1094x/1095x` | 角色相关扩展 |
| 18900–18911 | `hander189xx` | 角色相关扩展（法宝等） |
| 13331 / 21414 | `rgp_hander13331` / `hander21414` | 其它 |

### 1.2 与角色登录/进场景相关的（在 `denglu_ctrl.luac` / `scene_controller.luac`）

| CMD | 名称 | 方向 | 出处 |
|---|---|---|---|
| 1110 | 帐号登录 | C→S 请求 / S→C 回 | `denglu_ctrl.registerProtocals` |
| 10102 | 登录指定角色 | 双向 | 同上 |
| 10103 | 角色重连 | 双向 | 同上 |
| 10101 | 创建角色 | 双向 | 同上 |
| 10300 | 客户端初始化完毕 | C→S（仅通知） | 同上 |
| 10200 | 通知角色进入场景 | **S→C** | `scene_controller` |
| 10201 | 场景图块信息 | 双向 | `scene_controller` |
| 10204 / 10205 | 角色移动 / 瞬移 | 双向 | `scene_controller` |

### 1.3 实机日志对照：客户端实际发出 vs 服务端实际回复

最近一轮 TCP 日志：

```
发出(去重): 10001,10103,10204,10300,10301,10333,10502,10621,10800,10921,10922,
            10923,10924,10932,1110,11200,11215,11300,11301,11600,1199,12403,
            13200,13300,13771,15501,15700,15801,16500,16605,16706,17200,
            18803,18900,19400,19406,30715
回复(去重): 10103,10200,10201,10204,10301,10502,10921,10922,10924,10932,1110,
            11200,11215,11600,1199,12400,13771,15501,15700,16500,16706,17200,18900
```

**⇒ 客户端发了但服务端未回复的角色相关命令：`10300`、`10333`、`10621`、`12403`**

---

## 二、角色字段表（`SC_10301` / `SC_10302` / `SC_10303`）

### 2.1 `SC_10301` 角色基础信息（`CS_10301` 为空消息）

45+ 字段，**全部类型已确认**：

| 分组 | 字段（类型） |
|---|---|
| 身份 | `rid:u32, srv_id:string, name:string, lev:u16, sex:u8, career:u16, face_id:u16` |
| VIP | `is_vip:u8, vip_lev:u8` |
| 称号 | `cur_title:u16, ntm_title:u32` |
| 公会 | `gid:u32, gsrv_id:string, gname:string, position:u8` |
| 移动 | `mspd:u16` |
| 容量 | `volume:u8, store_volume:u8, store_partner_volume:u8, volume_open:u8, store_volume_open:u8, store_partner_volume_open:u8` |
| 经验 | `exp_max:u32, exp_total_nextlev:u32, profit_exp:u32, attr_point:u16` |
| 婚姻 | `marry_state:u8, spouse_name:string, spouse_rid:u32, spouse_srv_id:string` |
| 外观 | `head_bid:u32, chat_bubble:u32, animate_res:table(ant_id:u16, ant_val:string, ent_lev:u8, dis_method:u8)` |
| **技能** | **`skill_list:table(bid:u32)`** |
| 状态 | `buffs:table(bid:u32, duration:u32, count:u8, effect:D\|Dsc10301effect\|)` |
| 杂项 | `misc_uint8/uint16/uint32/str:table(key:u8, value:…)` |
| 结拜 | `insight_status:u8, jid:u32, j_srv_id:string, jlev:u8, j_title:string` |

> ⚠ `buffs[].effect` 是 `D|Dsc10301effect|` **动态子表**；`protocol/fields.json` 是否解出需单独确认
> （本阶段未展开）。

### 2.2 `SC_10302` 角色资产/经验

```
lev:u16, exp:u32, gold:u32, gold_acc:u32
```

### 2.3 `SC_10303` 角色属性（含 `attr` 大表）

- 身份：`rid, srv_id, name, lev, is_vip, vip_lev, sex, career`
- 容量：`volume, store_volume, store_partner_volume, volume_open, store_volume_open, store_partner_volume_open`
- 点数：`attr_point:u16`
- **技能**：`skill_list:table(bid:u32)`
- 战力：`power:u32`
- **资产**：`exp, gold, coin, gold_acc, sinew, experience, coupon, vitality, guild_contrib, practice_exp, tower_cent, arena_cent`（**均 u32**）
- **属性大表** `attr:table(...)`：
  `strength:u16, intellect:u16, armor:u16, constiution:u16, atk_s:u32, atk_p:u32,
   def_s:u32, def_p:u32, hp_max:u32, atk_speed:u32, hit:u32, dodge:u32, crit:u32,
   tenacity:u32, red_def_s:u32, red_def_p:u32, atk_abs:u32, def_abs:u32, reduce:u32,
   hurt:u32, hit_rate_show:u32, dodge_rate_show:u32, crit_rate_show:u32, tenacity_rate_show:u32`
- 其它：`mspd:u16, animate_res:table(...), vip_exp:u32, jiebai_title:string, jiebai_lev:u8`

### 2.4 `SC_10304` 查看指定角色

```
CS: rid:u32, srv_id:string
SC: rid:u32, srv_id:string, name:string, lev:u16, …
```

### 2.5 未回复命令的字段（审计发现，本阶段记入清单）

| CMD | 请求 | 响应 |
|---|---|---|
| `10333` | 空 | `SC_10333{code:u8, msg:string}` |
| `10621` | 空 | **`SC_10621{world_lev:u16, skill_list:table(bid:u32, exp:u32)}`** |
| `12403` | `mission_bid:u32` | `SC_12403{mission_bid:u32, code:u8, msg:string}`（任务系统，本阶段不做） |

---

## 三、当前服务端缺失协议（审计结论）

| CMD | 客户端是否请求 | 服务端是否实现 | 结论 |
|---|---|---|---|
| 10301 | ✅ 请求 | ✅ 实现（`build_10301`） | 已实现 |
| 10300 | ✅ 请求 | 不回包（仅记录，之后主动推 10200/12400） | 设计如此，不算缺失 |
| **10333** | ✅ 请求 | ❌ **无** | **缺失** |
| **10621** | ✅ 请求 | ❌ **无** | **缺失（角色技能列表！）** |
| 10302 / 10303 / 10304 / 10305 / 10306 | ❌ **未请求** | ❌ 无 | 待分析（客户端尚未索取） |
| 10320/10321/10324/10328/10342/10343/10391 | ❌ 未请求 | ❌ 无 | 待分析 |
| 10947–10958 / 18900–18911 | 18900 已请求 | 18900 已实现 | 其余待分析 |
| 12403 | ✅ 请求 | ❌ 无 | 任务系统，本阶段不做 |

---

## 四、当前客户端缺失数据（审计结论）

1. **`SC_10621` 未回** ⇒ 客户端拿不到 `world_lev` 与 `skill_list`（角色技能）。
2. **`SC_10333` 未回** ⇒ 某条角色操作的 ack 缺失（`code/msg`）。
3. **`SC_10302`（角色资产/经验）客户端尚未请求** —— 说明它依赖的前置还没触发；
   一旦触发而我们不回，资产/经验就会是空。
4. **`10301` 目前只回最小结构**（`skill_list/buffs/animate_res/misc_*` 给空表）——
   角色面板若要显示技能/状态，需要补这些。

---

## 五、推荐下一步最小修改（Phase 4B 用，本阶段不执行）

按"一次一条、有协议依据"的原则，建议顺序：

1. **补 `SC_10333`**（最简单）：`code=0` + `msg=''` → 1 个字节 + 空串。
2. **补 `SC_10621`**：`world_lev:u16` + `skill_list:table(bid:u32, exp:u32)`（先给 0 条或 1 条真实技能 bid）。
3. **补 `SC_10302`**：`lev/exp/gold/gold_acc` 四字段，数据直接取角色模型（**这一条最贴合本阶段"角色基础系统"目标**）。
4. 视面板需要，再补 `SC_10303` 的 `attr` 大表。

---

## 六、不修改代码情况下的验证结果（本阶段实测）

| 项 | 结果 | 依据 |
|---|---|---|
| 客户端会请求 10301 | ✅ | TCP 日志 `>> cmd=10301` |
| 服务端回 10301 | ✅（105 字节） | `<< 10301 SC_10301 role info (105 bytes)` |
| 客户端**未**请求 10302/10303/10304/10305/10306 | ✅ | 最近一轮 TCP 日志无这些命令 |
| 客户端**请求了** 10333 / 10621 / 12403 但**无人应答** | ✅ | 发出/回复去重列表对比 |
| 角色基础信息显示 | ✅ 已验证（历史截图：角色名 DSH、等级 1 等） | `shots/FIXED_character_visible.png` 等 |
| 资产/经验/技能显示 | ❌ 无数据（对应协议未实现） | 上述缺失清单 |

---

## 七、本阶段边界（遵守）

- **未修改**服务器逻辑、**未修改** APK、未写新角色系统、未写任务系统、未写 UI。
- 本文件为 Phase 4A 唯一产物，其余文档（`role_data_model.md`、`role_login_flow.md`、
  `role_init_flow.md`、`role_persistence.md`、`role_ui_dependency.md`、`role_test.md`）
  按计划留到对应 Phase 再写（4B/4C/4E/4G）。

---

**[WAITING FOR PHASE 4B]**
