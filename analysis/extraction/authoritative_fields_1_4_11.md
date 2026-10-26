# 1.4.11 权威字段表（从 APK `cmd_resolve_*.luac` 直读）

> 来源：1.4.11 APK `assets/src/config/protocal/cmd_resolve_<N>.luac` 的
> `AutoConstruct('sc'|'cs', <cmd>, TableConst(array=[...]))`。
> 证据等级：**CONFIRMED**（客户端自己的协议构造代码）。
> 工具：`tools/_fmt_autoconstruct.py <cmd> [cmd...]`（可复跑）。
> **批量排查工具**（本轮新增，推荐先跑这两个）：
> · `tools/_sweep_fieldmismatch.py` —— 比对**字段名/序/数量**（找"漏字段/错序"）
> · `tools/_sweep_typemismatch.py` —— 比对**字段类型**（找"类型标错"，如 `bool` 实为 `bytes`）

---

## ★★ 已确证的差异清单（PHASE 2.24~2.29，**均已修**）

`protocol/fields.json`（**源自 1.4.9**）与 1.4.11 的差异，逐条实证：

| # | cmd.字段 | `fields.json`(1.4.9) | **1.4.11 权威** | 用户可见后果 | 状态 |
|---|---|---|---|---|---|
| 1 | `SC_11215` 整包 | 只有 `partner_list` | **`volume(u8)+volume_open(u8)+partner_bag(表)`** | **伙伴面板空白** | ✅ 已修 |
| 2 | `SC_10341.img` | `bool` | **`img__b`（字节数组）** | 保存自定义头像应答错位（15B→**16B**）| ✅ 已修 |
| 3 | `CS_10340.img` | `bool` | **`img__b`** | 上传自定义头像请求错位 | ✅ 已修 |
| 4 | `CS_12725.voice` | `bool` | **`voice__b`** | 语音发送错位 | ✅ 已修 |
| 5 | `SC_12726.voice` | `bool` | **`voice__b`** | 语音缓存应答错位 | ✅ 已修 |
| 6 | `10325` **数据源** | （取 `FriendZoneSkin` 头像框 13 项）| 字段是 `face_id` ⇒ 应取 **`RoleFace`（100..113，14 项）** | 头像列表全是无效项 ⇒ **头像选择/显示异常** | ✅ 已修 |
| 7 | `SC_10302` 末 2 字段 | — | `diamond`/`rainbow_diamond` | （构造本身不缺；差 8B 是 `CUR_VER` 竞态所致）| ✅ 见 `ROOTCAUSE_cur_ver_global_race.md` |

**配套修复**：`protocol/fields.py::_sc_w` 补上**字节数组**类型（`b`/`bytes`/`buffer` → 变长，
线序 `u16 长度 + 原始字节`，与 `string` 同框架）。

**收敛验证（本轮）**：
- `tools/_sweep_typemismatch.py` ⇒ **0 处类型不符**（对客户端真实在发的命令集）
- `tools/_sweep_fieldmismatch.py` ⇒ 仅 `10301`/`10302` 两条数量差（**经查 mock 实现是对的**，是 fields.json 少列）
- 全库 `bool` 字段 ⇒ **（无）**

---

## ★ 为什么需要这份表（PHASE 2.24/2.25 的教训）

`protocol/fields.json` **源自 1.4.9**，对 **1.4.11 不可靠**。已确证的两处严重差异：

| cmd | `fields.json`(1.4.9) | **1.4.11 实际** | 后果 |
|---|---|---|---|
| **11215** | 只有 `partner_list:table{…}` | **`volume(u8)` + `volume_open(u8)` + `partner_bag(表)`** | mock 以表计数开头 ⇒ 客户端把计数读成 `volume`/`volume_open` ⇒ **整表错位 ⇒ 伙伴面板空白**（已修）|
| **10301** | （旧实现按另一套字段序）| **45 个字段**，其中 `[8] face_id__H`、`[28] head_bid__I`、`[31] buffs__T` | 见下 |

---

## 一、`SC_10301` 角色基础信息 —— **45 个字段（CONFIRMED）**

| # | 字段 | # | 字段 | # | 字段 |
|---|---|---|---|---|---|
| 0 | `rid__I` | 15 | `mspd__H` | 30 | `skill_list__T__bid@I` |
| 1 | `srv_id__s` | 16 | `volume__C` | 31 | **`buffs__T__bid@I##duration@I##count@C##effect@D…`** ← **头像旁状态** |
| 2 | `name__s` | 17 | `store_volume__C` | 32 | `animate_res__T__ant_id@H##ant_val@s##ent_lev@C##dis_method@C` |
| 3 | `lev__H` | 18 | `store_partner_volume__C` | 33 | `misc_uint8__T__key@C##value@C` |
| 4 | `is_vip__C` | 19 | `volume_open__C` | 34 | `misc_uint16__T__key@C##value@H` |
| 5 | `vip_lev__C` | 20 | `store_volume_open__C` | 35 | `misc_uint32__T__key@C##value@I` |
| 6 | `sex__C` | 21 | `store_partner_volume_open__C` | 36 | `misc_str__T__key@C##value@s` |
| 7 | `career__H` | 22 | `exp_max__I` | 37 | `spouse_rid__I` |
| **8** | **`face_id__H`** ← **头像** | 23 | `exp_total_nextlev__I` | 38 | `spouse_srv_id__s` |
| 9 | `cur_title__H` | 24 | `attr_point__H` | 39 | `insight_status__C` |
| 10 | `ntm_title__I` | 25 | `profit_exp__I` | 40 | `jid__I` |
| 11 | `gid__I` | 26 | `marry_state__C` | 41 | `j_srv_id__s` |
| 12 | `gsrv_id__s` | 27 | `spouse_name__s` | 42 | `jlev__C` |
| 13 | `position__C` | **28** | **`head_bid__I`** ← **头像框** | 43 | `j_title__s` |
| 14 | `gname__s` | 29 | `chat_bubble__I` | 44 | `vip_diamond__C` |

**`CS_10301` = 14 字段**：`lev__H, exp__I, gold__I, gold_acc__I, coin__I, sinew__I, experience__I, coupon__I, vitality__I, guild_contrib__I, practice_exp__I, tower_cent__I, arena_cent__I, integral`

---

## 二、`SC_10304` 战力/资产大包 —— **35 个字段（CONFIRMED，前 13 项）**

`rid__I, srv_id__s, name__s, lev__H, is_vip__C, vip_lev__C, sex__C, career__H, volume__C, store_volume__C, store_partner_volume__C, volume_open__C, store_volume_open__C, …`

> 完整 35 项见 `tools/_fmt_autoconstruct.py 10304` 输出（本文件未全列，避免与工具输出重复）。

---

## 三、★ 已据此修掉的两处（PHASE 2.24 / 2.25）

| 症状（用户报障）| 根因 | 修复 |
|---|---|---|
| **伙伴面板空白** | `SC_11215` 缺开头 `volume`/`volume_open` 两个字节 | `partner/service.build_panel_11215` 补 `w_u8(volume)+w_u8(volume_open)`（**已验证**：2546→2548B，客户端格式解析正确）|
| **头像空白** | `role/storage.ROLE_DEFAULTS['face_id']=0` 且 `roles` 表**无 face_id 列** ⇒ `SC_10301` 发 0 | 默认改为 **100**（`config_role_face.RoleFace` 键 100..113 的首个；**已验证**：10301 回 `face_id=100`）|

**未修（待续）**：
- **头像旁状态点不了** ⇒ 疑与 `SC_10301[31] buffs__T` 有关（本服是否发 buffs、结构是否合 1.4.11）
- **日常面板空白** ⇒ `13786` 的 1.4.11 格式**已核对无误**（`richang_list__T__id@H##num@H` + `status_list__T__id@H##num@H`），
  根因待查；**疑点**：`daily_ctrl.luac` 同时注册 `on10922/10923/10924/10925`，而 `10924` 现为空表（R49 取舍）
