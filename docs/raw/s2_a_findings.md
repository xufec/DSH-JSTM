# S2 第一分片：静态取证 findings（天赋配置提取 + 11215 版本事实厘清）

> 分片：PHASE S2 第一分片（只读）。执行时间：2026-10-15。
> 纪律：只读，不改任何既有文件；所有结论带证据位置；UNKNOWN 如实标注。

---

## 任务 1：天赋配置提取（服务 S2 项① CS_10650 talent_list）

### 结论：✅ 有真实天赋数据

| 项 | 值 |
|---|---|
| APK 版本 | 1.4.11（`analysis\jstm_client_audit\_raw\apk_scan_1_4_11.json` → `version:"1.4.11"`，apk=`anzbao\jstm_142165.apk`） |
| 天赋表名 | `config_skill_talent.luac`（apk_scan config_tables 共 233 表，天赋相关唯一命中） |
| 本地 luac 副本 | `_tmp_cfg\config_skill_talent.luac`（37235 字节；同目录 `file_update_1411.luac` 佐证为 1.4.11 解包） |
| 解构工具 | 复用既有 `tools\config_deconstruct.py`（未重建工具链） |
| 交付 JSON | `data\s2_talent_data.json`（75115 字节，含 `_meta` 来源链） |
| 已有服务端副本 | `server\cfg\config_skill_talent.json`（53718 字节）——本次从 1.4.11 luac **重新解构并逐字段 diff = IDENTICAL**（TalentRune 35 / SkillTalent 105 / TalentRuneActivity 105） |

### 数据结构（三张表）

| 表 | 行数 | 键 → 值字段 |
|---|---|---|
| `TalentRune` | 35（skill_group） | 每组 3 个等级：`{name, talent_id, cond_desc, desc}`（例：16200→破灭杀一阶 10020「技能等级达到54级/攻击目标+1」） |
| `SkillTalent` | 105（talent_id） | `{name, bid, skill_group, skill_talent:{…}, magic_talent:{}}`；id 范围 10020..90800 |
| `TalentRuneActivity` | 105（talent_id） | `{desc, talent_id, name, cond_desc, skill_group}` |

`TalentRune` 的 skill_group 键：10200,10300,10400,11100,11300,11400,11500,13200,13300,13400,14100,14200,14300,14400,14600,15100,15200,15300,15400,15700,15800,16200,16300,17200,17300,17400,18100,18200,50062,50070,50071,50072,50080,50081,50082。

### CS_10650 响应格式（三源一致）

- `protocol\fields.json` → `SC_10650`：`talent_list:table{id:uint16}`（source=spec，file=cmd_resolve_106.luac）。
- `server\proto_defs.py` → `'SC_10650'`：`('talent_list','table','id:uint16')`。
- **1.4.11 APK 字节码级证据**：`_tmp_cr112\cmd_resolve_106.luac`（3128 字节，与 1.3.0 副本同尺寸同注册）反汇编：
  `KSHORT 10650 / TDUP TableConst(array=[None,'talent_list__T__id@H'])` ⇒ `talent_list` 表，行内仅 `id@H(=uint16)`。

### 当前服务端实现与缺口

- `server\mock_server.py` L17101–17110：`if cmd==10650` → `tl = self.cfg.get('talent_list') or []`，发 `w_u16(len)+Σw_u16(id)`。
- **缺口**：`server\config.json` 无 `talent` 键（grep 0 命中）⇒ 当前 10650 恒回**空表**。
- **组装建议**：S2-B 把 `SkillTalent` 的 105 个 `talent_id`（或按角色解锁子集）灌入 `cfg['talent_list']` 即可返回真实列表；帧格式已是 `u16计数+u16 id 序列`，与三源规格完全对齐，无需改编码器。

---

## 任务 2：11215 版本事实厘清（证据说话）

### 2.1 当前 MuMu 实际客户端版本

| 证据 | 内容 |
|---|---|
| `server\logs\tcp.log` L5–25（今日 20:37:31） | 真机登录帧：`=== connection from 127.0.0.1:46189` → CS_10001 `game_client` → **CS_1110 body=220 字节**，10 个 args 键（account/timestamp/enter_srv_id/platform=**ewan**/device_id=`Redmi_rubens(22041211A)`/gettui_cid/idfa/token/channelId/sign）→ 日志打 `ver=1.4.9`。 |
| 版本判定逻辑 | `server\core\runtime.py` L87–99 `ver_family_of(body_len,args)`：`n≤2→1.3.0`；`body<210→1.4.11`；**其余→1.4.9**。本次 220 字节/10 键 ⇒ 落 1.4.9 分支。 |
| 后续会话（20:57+） | 同 log L1436 起 `account=dsh_local/r48_hook`、keys=['account','platform'] ⇒ `ver=1.3.0` —— 判定为自动化测试脚本（非 MuMu 真机）。 |
| 客户端显式版本号 | **无**。10996 `cli_ver_list` 服务端按 `analysis\1.4.9\round99_version_handshake.md` §五 故意回空表（不做版本约束）⇒ 客户端不会上报本地版本号到链路上；"1.4.9" 是**服务端按登录体长的分类**，不是客户端自述。 |
| APK 映射（既有文档） | `round99_version_handshake.md` §一：1.4.9=`anzbao\jstm.apk`→`patched\jstm_fakelogin_aligned.apk`；1.4.11=`anzbao\jstm_142165.apk`→`patched\jstm_1411_fakelogin_aligned.apk`。 |

**结论**：当前 MuMu 真机会话按服务端版本族判定 = **1.4.9**（220 字节登录帧实据）。严格说，此版本号是"登录体长启发式分类"而非客户端自述；若需 100% 锁定安装包，待 S2-B 现场抓包核对 MuMu 内当前 APK 包名/versionName（本分片不碰模拟器）。

### 2.2 SC_11215 三源核对表

| 源 | 位置 | SC_11215 字段序列 | 有无 volume/volume_open 前缀 |
|---|---|---|---|
| fields.json | `protocol\fields.json` → `SC_11215`（source=spec，file=cmd_resolve_112.luac） | `partner_list:table{ id:u32, bid:u32, type:u8, color:u8, lifttime:u32, lev:u8, exp:u32, grow:u16, score:u32, stage:u8, rebirth:u8, acc:u8, partner_attr:D\|Dsc11215partner_attr\|, power:u32, aptitude:D\|Dsc11215aptitude\|, innate_skill:u32, skill:D\|Dsc11215skill\|, jindan_skill:D\|Dsc11215jindan_skill\|, talisman_skill:D\|Dsc11215talisman_skill\|, ext:D\|Dsc11215ext\| }` | **无** |
| proto_defs.py | `server\proto_defs.py` `'SC_11215'`（同表，D 引用展开） | 与 fields.json 逐字段一致 | **无** |
| 1.4.11 APK | `_tmp_cr112\cmd_resolve_112.luac`（31321 字节）proto #37 反汇编 | `KSHORT 11215 / TDUP TableConst=[None,'partner_list__T__id@I##bid@I##type@C##color@C##lifttime@I##lev@C##exp@I##grow@H##score@I##stage@C##rebirth@C##acc@C##partner_attr@D\|Dsc11215partner_attr\|##power@I##aptitude@D\|Dsc11215aptitude\|##innate_skill@I##skill@D\|Dsc11215skill\|##jindan_skill@D\|Dsc11215jindan_skill\|##talisman_skill@D\|Dsc11215talisman_skill\|##ext@D\|Dsc11215ext\|']` | **无** |
| 1.3.0 APK（旁证） | `analysis\version_compare\1.3.0\extracted\config\protocal\cmd_resolve_112.luac` 反汇编 | 同上 `partner_list__T…Dsc11215…` | **无** |

### 2.3 S1-B 表述复核（重点纠偏）

- **S1-B 称「1.4.9 SC_11215 无 volume 前缀，直接 partner_list:table 表计数」** —— ✅ **属实**（fields.json + proto_defs.py 一致）。
- **S1-B 称「proto_defs 旧码按 1.4.11 加 volume+volume_open 前缀」** —— ⚠️ **前提误归因**：带 `volume__C##volume_open__C##partner_bag__T…Dsc11200…##gratis__T…` 的格式串，经字节码级反汇编确认注册在 **cmd 11200（proto #0）= 伙伴仓库包**，不是 11215；`code__C,msg__s,volume__C,volume_open__C` 注册在 **cmd 11206（proto #23）**。`server\partner\service.py` L132–143 的 PHASE 2.24 docstring 把 11200 的 bag 格式误记为 11215 的 1.4.11 权威格式；其后 S1-B 据运行时 LUA ERROR 去掉两字节前缀——**结论方向对，但论证链挂错了命令号**。
- **proto_defs.py 现状**：`'SC_11215'` 当前 = `partner_list:table…`，无前缀（本次 grep 实证，char@230883 起）。
- 客户端 reader 旁证：`_tmp_hero\hero_equip_data.luac` 字符串表 27–30 `gratis / partner_bag / volume_open / volume` 同现 —— 这正是 `storagePartnerList(data)` 读 **11200 仓库包** 的取值序列，进一步佐证 volume/volume_open 属 11200 而非 11215。

### 2.4 分流结论与建议

1. **11215 无需按版本分流**：1.3.0 / 1.4.9(fields.json) / 1.4.11(luac) 三源 SC_11215 格式完全一致（`partner_list:table`，无前缀）。当前 `server\partner\service.py::build_panel_11215`（`w_u16(计数)+行序列`，无 volume 前缀）对三个版本都是正确帧。
2. **真正需要带 volume/volume_open 前缀的是 11200（伙伴仓库）与 11206（容量应答）**——后续涉及这两个命令时按 2.3 的注册事实发包，不要再把前缀错挂到 11215。
3. `service.py` L132–143 docstring 的"1.4.11 SC_11215 = volume+volume_open+partner_bag"错误归因建议 S2-B 顺手更正为"该格式属 SC_11200"（本分片不改代码，仅记录）。
4. 现场锁定真机 APK：待 S2-B 抓包核对 MuMu 当前安装包 versionName（本分片证据链下，分类结果为 1.4.9）。

---

## 自检记录

| 检查项 | 结果 |
|---|---|
| 只读纪律 | ✅ 未修改任何既有文件；仅新建 `data\s2_talent_data.json`、`docs_raw\s2_a_findings.md`（+scratch 在 agent workspace，非项目目录） |
| 天赋数据真实性 | ✅ 从 `_tmp_cfg\config_skill_talent.luac`（1.4.11）用既有 `tools\config_deconstruct.py` 解构；与 `server\cfg\config_skill_talent.json` 逐字段 diff = IDENTICAL |
| 10650 格式三源 | ✅ fields.json / proto_defs.py / cmd_resolve_106.luac 反汇编 三处一致 `talent_list__T__id@H` |
| 11215 三源核对 | ✅ fields.json = proto_defs.py = 1.4.11 luac proto#37 = 1.3.0 luac（均无前缀） |
| volume 前缀归属 | ✅ 反汇编坐实：11200=volume+volume_open+partner_bag+gratis；11206=code,msg,volume,volume_open |
| 真机版本 | ✅ tcp.log 20:37:31 登录帧 220 字节 → ver_family_of→1.4.9；非客户端自述版本号，已标注启发式前提 |
| UNKNOWN 项 | ① 客户端自述版本号链路不存在（10996 故意空表）——已如实标注；② talent_list 应发全量 105 id 还是解锁子集，属 S2-B 设计决策，本分片不编造 |
