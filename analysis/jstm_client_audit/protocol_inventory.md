# 绝世唐门 PHASE C0 协议总目录（只读审计）

- 生成时间：2026-10-15 13:45:33
- 生成脚本：`tools/jstm_audit/gen_protocol_inventory.py`（可重复运行）
- 纪律：只读审计；字段仅取自 `protocol/fields.json`，未自行补造；证据不足一律标 UNKNOWN/unresolved。

## 一、证据等级（五档）

| 等级 | 含义 |
|---|---|
| VERIFIED | 1.4.11 实机观测到收发（phase1_cs_inventory / 文档真机列） |
| CONFIRMED | fields.json 静态字段定义存在，或客户端注册表(registry_classes.json)有此类 |
| STRONG_INFERENCE | 1.4.9 分系统文档载录该行，但无运行时证据 |
| INFERENCE | cmd_table 有中文名；或 systems_master prior analysis 引用补录（无直接 spec） |
| UNKNOWN | 以上皆无 |

## 二、总览统计

| 指标 | 数量 |
|---|---|
| 协议记录总数（唯一 cmd） | 1707 |
| 其中：cmd_table 覆盖 | 1643 / 1643 |
| 方向 cs | 71 |
| 方向 sc | 209 |
| 方向 双向 | 1427 |
| 方向 UNKNOWN | 0 |
| 有字段定义 | 1634 |
| 无字段定义 | 73 |
| 映射到系统 | 146 |
| 1.4.9 文档补充载录 | 669 |
| 含未确认项 | 759 |
| 排除的嵌套子消息描述符条目 | 474 |
| 修复轮补录（systems_master prior analysis 引用） | 55 |

### 证据等级分布
| 等级 | 数量 |
|---|---|
| UNKNOWN | 0 |
| INFERENCE | 55 |
| STRONG_INFERENCE | 0 |
| CONFIRMED | 1326 |
| VERIFIED | 326 |

### 修复轮补录明细（INFERENCE 级，仅旧分析引用）

| cmd | 方向(推断) | 家族 | 引用系统 |
|---|---|---|---|
| 10926 | cs (inferred from systems_master token prefix) | cmd_resolve_109.luac | SYS_GM_001 |
| 10927 | cs (inferred from systems_master token prefix) | cmd_resolve_109.luac | SYS_GM_001 |
| 10928 | cs (inferred from systems_master token prefix) | cmd_resolve_109.luac | SYS_GM_001 |
| 10929 | cs (inferred from systems_master token prefix) | cmd_resolve_109.luac | SYS_GM_001 |
| 11310 | cs (inferred from systems_master token prefix) | cmd_resolve_113.luac | SYS_COMM_002 |
| 11999 | cs (inferred from systems_master token prefix) | cmd_resolve_119.luac | SYS_GM_001 |
| 12804 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12806 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12807 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12808 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12809 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12810 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12811 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12812 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12813 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12814 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12815 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12816 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12817 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12818 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12819 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12820 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12824 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12825 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12826 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12827 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12828 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12829 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12830 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12833 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12834 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12835 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12844 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12845 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12846 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12847 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12848 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12849 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12850 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12851 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 12852 | cs (inferred from systems_master token prefix) | cmd_resolve_128.luac | SYS_ECON_003 |
| 13404 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13405 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13406 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13407 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13408 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13409 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13412 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13413 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 13414 | cs (inferred from systems_master token prefix) | cmd_resolve_134.luac | SYS_ECON_003 |
| 16902 | cs (inferred from systems_master token prefix) | cmd_resolve_169.luac | SYS_COMM_001 |
| 17500 | cs (inferred from systems_master token prefix) | cmd_resolve_175.luac | SYS_SOCIAL_004 |
| 30100 | cs (inferred from systems_master token prefix) | cmd_resolve_301.luac | SYS_COMM_005 |
| 31299 | cs (inferred from systems_master token prefix) | cmd_resolve_312.luac | SYS_COMM_005 |
| 13752 | sc (inferred from systems_master token prefix) | cmd_resolve_137.luac | SYS_DUNGEON_003 |

### A 类：库内记录已存在、仅 systems_master token 方向标签不一致（不补录，待 systems_master 侧修复）

| cmd | 库内方向 | systems_master token 方向 |
|---|---|---|
| 10500 | sc | cs |
| 11202 | sc | cs |
| 11304 | sc | cs |
| 11307 | sc | cs |
| 12420 | sc | cs |
| 13203 | sc | cs |
| 19511 | sc | cs |
| 19513 | sc | cs |
| 20012 | sc | cs |
| 10300 | cs | sc |

## 三、按 cmd_resolve 家族分组

共 121 个家族（含 0 条无家族文件）。

| 家族文件 | 协议数 |
|---|---|
| cmd_resolve_100.luac | 1 |
| cmd_resolve_101.luac | 5 |
| cmd_resolve_102.luac | 35 |
| cmd_resolve_103.luac | 37 |
| cmd_resolve_104.luac | 18 |
| cmd_resolve_105.luac | 75 |
| cmd_resolve_106.luac | 11 |
| cmd_resolve_107.luac | 33 |
| cmd_resolve_108.luac | 7 |
| cmd_resolve_109.luac | 42 |
| cmd_resolve_11.luac | 4 |
| cmd_resolve_110.luac | 19 |
| cmd_resolve_111.luac | 5 |
| cmd_resolve_112.luac | 33 |
| cmd_resolve_113.luac | 11 |
| cmd_resolve_114.luac | 15 |
| cmd_resolve_115.luac | 8 |
| cmd_resolve_116.luac | 10 |
| cmd_resolve_117.luac | 19 |
| cmd_resolve_118.luac | 2 |
| cmd_resolve_119.luac | 4 |
| cmd_resolve_12.luac | 2 |
| cmd_resolve_120.luac | 11 |
| cmd_resolve_121.luac | 2 |
| cmd_resolve_122.luac | 15 |
| cmd_resolve_124.luac | 39 |
| cmd_resolve_126.luac | 6 |
| cmd_resolve_127.luac | 19 |
| cmd_resolve_128.luac | 56 |
| cmd_resolve_129.luac | 44 |
| cmd_resolve_130.luac | 88 |
| cmd_resolve_131.luac | 6 |
| cmd_resolve_132.luac | 45 |
| cmd_resolve_133.luac | 62 |
| cmd_resolve_134.luac | 16 |
| cmd_resolve_135.luac | 75 |
| cmd_resolve_136.luac | 2 |
| cmd_resolve_137.luac | 18 |
| cmd_resolve_138.luac | 21 |
| cmd_resolve_139.luac | 6 |
| cmd_resolve_140.luac | 16 |
| cmd_resolve_141.luac | 2 |
| cmd_resolve_142.luac | 17 |
| cmd_resolve_143.luac | 3 |
| cmd_resolve_144.luac | 5 |
| cmd_resolve_145.luac | 8 |
| cmd_resolve_146.luac | 2 |
| cmd_resolve_147.luac | 2 |
| cmd_resolve_148.luac | 7 |
| cmd_resolve_149.luac | 2 |
| cmd_resolve_150.luac | 11 |
| cmd_resolve_151.luac | 2 |
| cmd_resolve_152.luac | 9 |
| cmd_resolve_153.luac | 4 |
| cmd_resolve_154.luac | 9 |
| cmd_resolve_155.luac | 10 |
| cmd_resolve_156.luac | 4 |
| cmd_resolve_157.luac | 5 |
| cmd_resolve_158.luac | 11 |
| cmd_resolve_159.luac | 2 |
| cmd_resolve_160.luac | 3 |
| cmd_resolve_161.luac | 8 |
| cmd_resolve_162.luac | 3 |
| cmd_resolve_163.luac | 5 |
| cmd_resolve_164.luac | 5 |
| cmd_resolve_165.luac | 4 |
| cmd_resolve_166.luac | 56 |
| cmd_resolve_167.luac | 7 |
| cmd_resolve_168.luac | 1 |
| cmd_resolve_169.luac | 5 |
| cmd_resolve_170.luac | 2 |
| cmd_resolve_171.luac | 3 |
| cmd_resolve_172.luac | 2 |
| cmd_resolve_173.luac | 12 |
| cmd_resolve_174.luac | 7 |
| cmd_resolve_175.luac | 22 |
| cmd_resolve_176.luac | 3 |
| cmd_resolve_177.luac | 15 |
| cmd_resolve_178.luac | 2 |
| cmd_resolve_179.luac | 9 |
| cmd_resolve_180.luac | 23 |
| cmd_resolve_181.luac | 4 |
| cmd_resolve_182.luac | 2 |
| cmd_resolve_183.luac | 23 |
| cmd_resolve_184.luac | 5 |
| cmd_resolve_185.luac | 6 |
| cmd_resolve_186.luac | 15 |
| cmd_resolve_187.luac | 35 |
| cmd_resolve_188.luac | 33 |
| cmd_resolve_189.luac | 12 |
| cmd_resolve_190.luac | 6 |
| cmd_resolve_191.luac | 8 |
| cmd_resolve_192.luac | 3 |
| cmd_resolve_194.luac | 16 |
| cmd_resolve_195.luac | 35 |
| cmd_resolve_196.luac | 5 |
| cmd_resolve_199.luac | 6 |
| cmd_resolve_200.luac | 25 |
| cmd_resolve_201.luac | 1 |
| cmd_resolve_202.luac | 13 |
| cmd_resolve_203.luac | 15 |
| cmd_resolve_205.luac | 11 |
| cmd_resolve_207.luac | 31 |
| cmd_resolve_208.luac | 10 |
| cmd_resolve_213.luac | 14 |
| cmd_resolve_214.luac | 13 |
| cmd_resolve_216.luac | 10 |
| cmd_resolve_300.luac | 2 |
| cmd_resolve_301.luac | 10 |
| cmd_resolve_302.luac | 12 |
| cmd_resolve_303.luac | 7 |
| cmd_resolve_304.luac | 4 |
| cmd_resolve_305.luac | 8 |
| cmd_resolve_306.luac | 4 |
| cmd_resolve_307.luac | 18 |
| cmd_resolve_308.luac | 1 |
| cmd_resolve_309.luac | 3 |
| cmd_resolve_310.luac | 9 |
| cmd_resolve_311.luac | 5 |
| cmd_resolve_312.luac | 10 |
| cmd_resolve_313.luac | 2 |

## 四、协议明细（按家族分组）

### cmd_resolve_100.luac（1 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10001 | 客户端发起连接后的第一个包 | cs | cs: key:string ／ sc: — | SYS_CORE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端发起连接后的第一个包[cmd_table.json]；所属系统:Account Login[SYS_CORE_001][systems_master.json]；1.4.9文档载于login_protocol.md |

### cmd_resolve_101.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10101 | 创建角色 | bidirectional | cs: sex:uint8; name:string; career:int16; playform:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | SYS_CORE_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:创建角色[cmd_table.json]；所属系统:Role Creation[SYS_CORE_002][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10102 | 登录指定角色 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; timestamp:uint32; world_lev:uint16 | SYS_CORE_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:登录指定角色[cmd_table.json]；所属系统:Role Creation[SYS_CORE_002][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10103 | 角色重连 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; timestamp:uint32; world_lev:uint16 | SYS_CORE_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色重连[cmd_table.json]；所属系统:Role Creation[SYS_CORE_002][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10110 | 客户端调用URL（用于平台数据提交 | sc | cs: — ／ sc: method:uint8; url:string; args:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端调用URL（用于平台数据提交[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10111 | 客户端版本号 | bidirectional | cs: — ／ sc: cli_ver:uint16; flag:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端版本号[cmd_table.json]；1.4.9文档载于role_protocol.md |

### cmd_resolve_102.luac（35 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10200 | 通知角色进入场景 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; line_id:uint8; x:uint16; y:uint16; dir:uint8 | SYS_CORE_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:通知角色进入场景[cmd_table.json]；所属系统:Scene & Movement[SYS_CORE_005][systems_master.json]；1.4.9文档载于movement_protocol.md |
| 10201 | 场景图块信息() | bidirectional | cs: — ／ sc: roles:table; npcs:table; mons:table; elems:table | SYS_CORE_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:场景图块信息()[cmd_table.json]；所属系统:Scene & Movement[SYS_CORE_005][systems_master.json]；1.4.9文档载于movement_protocol.md |
| 10202 | 附近有角色进入场景 | sc | cs: — ／ sc: roles:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:附近有角色进入场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10203 | 附近有角色离开场景 | sc | cs: — ／ sc: role_ids:table; bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:附近有角色离开场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10204 | 角色移动 | bidirectional | cs: x:uint16; y:uint16 ／ sc: rid:uint32; srv_id:string; x:uint16; y:uint16 | SYS_CORE_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色移动[cmd_table.json]；所属系统:Scene & Movement[SYS_CORE_005][systems_master.json]；1.4.9文档载于login_protocol.md |
| 10205 | 角色瞬移 | bidirectional | cs: x:uint16; y:uint16 ／ sc: rid:uint32; srv_id:string; x:uint16; y:uint16 | SYS_CORE_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色瞬移[cmd_table.json]；所属系统:Scene & Movement[SYS_CORE_005][systems_master.json]；1.4.9文档载于login_protocol.md |
| 10206 | 传送到指定场景 | bidirectional | cs: x:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:传送到指定场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10207 | 回到上个场景(用于退出副本或者内城) | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回到上个场景(用于退出副本或者内城)[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10208 | 角色场景显示属性改变 | sc | cs: — ／ sc: rid:uint32; srv_id:string; change_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色场景显示属性改变[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10209 | 角色场景显示属性改变 | sc | cs: — ／ sc: rid:uint32; srv_id:string; change_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色场景显示属性改变[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10210 | 切换线路 | bidirectional | cs: line_id:uint8 ／ sc: code:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:切换线路[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10211 | 获取某个场景所有线路人数 | bidirectional | cs: bid:uint32 ／ sc: all_line_status:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取某个场景所有线路人数[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10212 | 附近有MON进入场景 | sc | cs: — ／ sc: id:uint32; bid:uint32; type:uint8; name:string; realm:uint8; mspd:uint16; x:uint16; y:uint16; dir:uint8; res_id:string; status:uint8; enter_effect:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:附近有MON进入场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10213 | MON移动 | sc | cs: — ／ sc: id:uint32; x:uint16; y:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:MON移动[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10214 | MON状态改变 | sc | cs: — ／ sc: id:uint32; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:MON状态改变[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10215 | 有Mon离开场景 | sc | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:有Mon离开场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10216 | 点击场景元素 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:点击场景元素[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10217 | 附近有ELEM进入场景 | sc | cs: — ／ sc: id:uint32; bid:uint32; type:uint8; sub_type:uint8; name:string; x:uint16; y:uint16; res_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:附近有ELEM进入场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10218 | 速度等属性变化,地图广播 | sc | cs: — ／ sc: rid:uint32; srv_id:string; role_attrs:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:速度等属性变化,地图广播[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10219 | 角色杂项变化 | sc | cs: — ／ sc: rid:uint32; srv_id:string; misc_uint8:table; misc_uint16:table; misc_uint32:table; misc_str:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色杂项变化[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10220 | 删除角色、MON | sc | cs: — ／ sc: mon_ids:table; role_ids:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除角色、MON[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10221 | 获取当前场景所有怪物坐标(挂机用) | bidirectional | cs: — ／ sc: mons:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前场景所有怪物坐标(挂机用)[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10222 | 传送到指定场景指定坐标 | bidirectional | cs: map_bid:uint32; x:uint32; y:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:传送到指定场景指定坐标[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10223 | 动态可行走区域 | sc | cs: — ／ sc: dynamic_block:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:动态可行走区域[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10224 | 单位特效 | sc | cs: — ／ sc: id:uint32; srv_id:string; type:uint8; val:int32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单位特效[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10230 | NPC进入场景 | sc | cs: — ／ sc: id:uint32; bid:uint32; type:uint8; x:uint16; y:uint16; name:string; misc:table; animate_res:table; member:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:NPC进入场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10231 | 有NPC离开场景 | sc | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:有NPC离开场景[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10232 | Npc按钮 | bidirectional | cs: npc_id:uint32; id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:Npc按钮[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10233 | 元素开始采集， 和10216搭配使用 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32; time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:元素开始采集， 和10216搭配使用[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10239 | 更新场景NPC | sc | cs: — ／ sc: id:uint32; bid:uint32; type:uint8; x:uint16; y:uint16; name:string; misc:table; animate_res:table; member:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新场景NPC[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10250 | 角色动画资源，地图广播 | sc | cs: — ／ sc: rid:uint32; srv_id:string; animate_res_replace:table; animate_res_del:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色动画资源，地图广播[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10295 | 通用协议(处理一些特殊数据) | sc | cs: — ／ sc: key:string; str_val:string; int_val:int32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通用协议(处理一些特殊数据)[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10296 | 设置挂机、取消挂机 | bidirectional | cs: — ／ sc: code:uint8; msg:string; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:设置挂机、取消挂机[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10297 | 挂机状态 | bidirectional | cs: — ／ sc: status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挂机状态[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 10299 | 测试 | bidirectional | cs: rid:uint32; srv_id:string; args:table ／ sc: args:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:测试[cmd_table.json]；1.4.9文档载于login_protocol.md |

### cmd_resolve_103.luac（37 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10300 | 客户端初始化完毕 | cs | cs: — ／ sc: — | SYS_CORE_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端初始化完毕[cmd_table.json]；所属系统:Role Base/Init[SYS_CORE_003][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10301 | 获取角色基础信息 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; face_id:uint16; cur_title:uint16; ntm_title:uint32; gid:uint32; gsrv_id:string; position:uint8; gname:string; mspd:uint16; volume:uint8; store_volume:uint8; store_partner_volume:uint8; volume_open:uint8; store_volume_open:uint8; store_partner_volume_open:uint8; exp_max:uint32; exp_total_nextlev:uint32; attr_point:uint16; profit_exp:uint32; marry_state:uint8; spouse_name:string; head_bid:uint32; chat_bubble:uint32; skill_list:table; buffs:table; animate_res:table; misc_uint8:table; misc_uint16:table; misc_uint32:table; misc_str:table; spouse_rid:uint32; spouse_srv_id:string; insight_status:uint8; jid:uint32; j_srv_id:string; jlev:uint8; j_title:string | SYS_CORE_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取角色基础信息[cmd_table.json]；所属系统:Role Base/Init[SYS_CORE_003][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10302 | 角色资产信息 | bidirectional | cs: — ／ sc: lev:uint16; exp:uint32; gold:uint32; gold_acc:uint32; coin:uint32; sinew:uint32; experience:uint32; coupon:uint32; vitality:uint32; guild_contrib:uint32; practice_exp:uint32; tower_cent:uint32; arena_cent:uint32; integral:uint32; cash_coupon:uint32; dan_point:uint32; guild_active:uint32; marriage:uint32; course:uint32; vip_exp:uint32; lingshi:uint32; peak_point:uint32; black_soul:uint32; lottery_point:uint32; boss_point:uint32; partner_shenqi_point:uint32; jiebai_cent:uint32; rune_exp:uint32; rune_chip:uint32 | SYS_CORE_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色资产信息[cmd_table.json]；所属系统:Role Base/Init[SYS_CORE_003][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10303 | 自己角色面板属性(相当于前面2条 加 10306 合起来的属性) | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; volume:uint8; store_volume:uint8; store_partner_volume:uint8; volume_open:uint8; store_volume_open:uint8; store_partner_volume_open:uint8; attr_point:uint16; skill_list:table; power:uint32; exp:uint32; gold:uint32; coin:uint32; gold_acc:uint32; sinew:uint32; experience:uint32; coupon:uint32; vitality:uint32; guild_contrib:uint32; practice_exp:uint32; tower_cent:uint32; arena_cent:uint32; attr:table; mspd:uint16; animate_res:table; vip_exp:uint32; jiebai_title:string; jiebai_lev:uint8 | SYS_CORE_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:自己角色面板属性(相当于前面2条 加 10306 合起来的属性)[cmd_table.json]；所属系统:Role Base/Init[SYS_CORE_003][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10304 | 别人角色面板属性(相当于前面3条合起来的属性) | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; name:string; lev:uint16; is_vip:uint8; vip_lev:uint8; sex:uint8; career:uint16; volume:uint8; store_volume:uint8; store_partner_volume:uint8; volume_open:uint8; store_volume_open:uint8; store_partner_volume_open:uint8; attr_point:uint16; skill_list:table; power:uint32; exp:uint32; gold:uint32; coin:uint32; gold_acc:uint32; sinew:uint32; experience:uint32; coupon:uint32; vitality:uint32; guild_contrib:uint32; practice_exp:uint32; tower_cent:uint32; arena_cent:uint32; attr:table; mspd:uint16; animate_res:table; vip_exp:uint32; jiebai_title:string; jiebai_lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:别人角色面板属性(相当于前面3条合起来的属性)[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10305 | 角色资产信息更新某几个 | bidirectional | cs: — ／ sc: assets:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色资产信息更新某几个[cmd_table.json]；1.4.9文档载于role_protocol.md；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 10306 | 角色属性 | bidirectional | cs: — ／ sc: attr:table; mspd:uint16; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色属性[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10310 | 掉线提示 | sc | cs: — ／ sc: is_show:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:掉线提示[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10311 | 复活 | bidirectional | cs: msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:复活[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10312 | 角色强制下线 | cs | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色强制下线[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10320 | 购买体力 | bidirectional | cs: — ／ sc: code:uint8; msg:string; times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买体力[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10321 | 购买体力面板数据 | bidirectional | cs: — ／ sc: times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买体力面板数据[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10322 | 设置系统配置 | bidirectional | cs: Code:uint8 ／ sc: Code1:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置系统配置[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10323 | 获取系统设置 | bidirectional | cs: — ／ sc: Code:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取系统设置[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10324 | 角色名字 | bidirectional | cs: name:string; is_rename:uint8 ／ sc: code:uint8; msg:string; name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色名字[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10325 | 头像列表 | bidirectional | cs: — ／ sc: face_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:头像列表[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10326 | 新增头像列表 | bidirectional | cs: — ／ sc: face_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:新增头像列表[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10327 | 设置头像 | bidirectional | cs: face_id:uint16 ／ sc: code:uint8; msg:string; face_id:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置头像[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10328 | 增加能力点 | bidirectional | cs: assets:table ／ sc: code:uint8; msg:string; point:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:增加能力点[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10331 | 角色技能学习、技能升级 | bidirectional | cs: skill_bid:uint32 ／ sc: code:uint8; msg:string | SYS_ROLE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色技能学习、技能升级[cmd_table.json]；所属系统:Role Attribute[SYS_ROLE_001][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10332 | 更新角色技能 | bidirectional | cs: — ／ sc: skill_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新角色技能[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10333 | 一键学习升级 | bidirectional | cs: — ／ sc: code:uint8; msg:string | SYS_ROLE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一键学习升级[cmd_table.json]；所属系统:Role Attribute[SYS_ROLE_001][systems_master.json]；1.4.9文档载于role_protocol.md |
| 10334 | 一键学习升级铜钱 | bidirectional | cs: — ／ sc: coin:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一键学习升级铜钱[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10340 | 上传自定义头像 | bidirectional | cs: img:bytes; size:uint32 ／ sc: code:uint8; msg:string; img_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上传自定义头像[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10341 | 请求自定义头像 | bidirectional | cs: id_list:table ／ sc: rid:uint32; srv_id:string; id:uint32; img:bytes; upload_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求自定义头像[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10342 | 盈福经验更新 | sc | cs: — ／ sc: profit_exp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:盈福经验更新[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10343 | 角色改名 | bidirectional | cs: new_name:string; auto_buy:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:角色改名[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10346 | 更新face_id | sc | cs: — ／ sc: rid:uint32; srv_id:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新face_id[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10347 | 批量更新face_id | sc | cs: — ／ sc: face_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:批量更新face_id[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10348 | 删除指定头像 | bidirectional | cs: face_id:uint16 ／ sc: code:uint8; face_id:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除指定头像[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10388 | 查询角色在线信息 | bidirectional | cs: id_list:table ／ sc: online_roles:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询角色在线信息[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10389 | 获取头像描述信息 | bidirectional | cs: — ／ sc: photos:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取头像描述信息[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10390 | 客户端测试 | bidirectional | cs: msg:string; len:uint32 ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端测试[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10391 | 客户端动态调用 | bidirectional | cs: msg:string ／ sc: type:uint8; data:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端动态调用[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10396 | 强制关闭客户端 | sc | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:强制关闭客户端[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10397 | 客户端进入后台 | cs | cs: status:uint8 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端进入后台[cmd_table.json]；1.4.9文档载于role_protocol.md |
| 10399 | GM命令 | bidirectional | cs: msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:GM命令[cmd_table.json]；1.4.9文档载于role_protocol.md |

### cmd_resolve_104.luac（18 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10401 | 获取英雄基础信息 | bidirectional | cs: — ／ sc: hero_bag:table; hero_chip:table | SYS_GROWTH_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取英雄基础信息[cmd_table.json]；所属系统:Skill System[SYS_GROWTH_001][systems_master.json]；1.4.9文档载于partner_protocol.md |
| 10402 | 请求单个英雄基础数据 | bidirectional | cs: hero_bid:uint32 ／ sc: bid:uint16; lev:uint8; color:uint8; exp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求单个英雄基础数据[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10403 | 请求单个英雄详细数据 | bidirectional | cs: hero_bid:uint32 ／ sc: bid:uint16; attr:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求单个英雄详细数据[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10404 | 客户端英雄基础数据计算 | bidirectional | cs: hero_bid:uint32 ／ sc: bid:uint16; lev:uint8; exp:uint32; color:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端英雄基础数据计算[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10405 | 英雄提品 | bidirectional | cs: hero_bid:uint32 ／ sc: code:uint8; msg:string; hero_bid:uint32; color:uint8; chip:uint16; skills:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄提品[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10406 | 英雄升星(废弃) | bidirectional | cs: hero_bid:uint32 ／ sc: hero_bid:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄升星(废弃)[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10407 | 请求几个个英雄详细数据 | bidirectional | cs: args:table ／ sc: hero_error:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求几个个英雄详细数据[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10408 | 英雄碎片更新 | sc | cs: — ／ sc: hero_chips:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄碎片更新[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10409 | 英雄加经验 | bidirectional | cs: hero_bid:uint32 ／ sc: hero_bid:uint32; exp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄加经验[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10410 | 招募英雄 | bidirectional | cs: hero_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:招募英雄[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10411 | 请求单个英雄技能 | bidirectional | cs: hero_bid:uint32 ／ sc: bid:uint16; skills:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求单个英雄技能[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10412 | 推送单个英雄状态 | sc | cs: — ／ sc: hero_bid:uint32; state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送单个英雄状态[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10413 | 推送全部英雄状态 | bidirectional | cs: — ／ sc: hero_states:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送全部英雄状态[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10414 | 所有英雄升级 | sc | cs: — ／ sc: lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:所有英雄升级[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10421 | 角色用的技能点(每次点骑士界面请求一次) | bidirectional | cs: — ／ sc: max_point:uint8; cur_point:uint8; sec:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色用的技能点(每次点骑士界面请求一次)[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10422 | 查询购买技能点 | bidirectional | cs: — ／ sc: count:uint8; gold:uint16; add_point:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询购买技能点[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10423 | 购买技能点 | bidirectional | cs: — ／ sc: code:uint8; msg:string; cur_point:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买技能点[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 10424 | 升级技能 | bidirectional | cs: bid:uint32; skill_bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; skill_bid:uint32; new_skill_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级技能[cmd_table.json]；1.4.9文档载于partner_protocol.md |

### cmd_resolve_105.luac（75 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10500 | 推送角色背包数据 | sc | cs: — ／ sc: bag_code:uint8; items:table | SYS_EQUIP_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:推送角色背包数据[cmd_table.json]；所属系统:Equipment System[SYS_EQUIP_001][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10501 | 物品数量更新 | sc | cs: — ／ sc: code:uint8; num_up_arr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品数量更新[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10502 | 请求角色背包数据 | bidirectional | cs: bag_code:uint8 ／ sc: bag_code:uint8; items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求角色背包数据[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10503 | 删除背包物品 | sc | cs: — ／ sc: code:uint8; del_ids_arr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除背包物品[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10504 | 卖物品 | bidirectional | cs: code:uint8; items_id:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:卖物品[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10505 |  物品使用协议 | bidirectional | cs: code:uint8; item_id:uint32; use_num:uint16; type:uint32; bid:uint32 ／ sc: code:uint8; msg:string; item_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名: 物品使用协议[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10506 | 穿装备 (废弃 | bidirectional | cs: bag_item_id:uint32; hero_bid:uint32 ／ sc: code:uint8; msg:string; bag_item_id:uint32; item_bid:uint32; hero_bid:uint32; eqm_new_pos:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:穿装备 (废弃[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10507 | 装备合成(废弃) | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备合成(废弃)[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10508 | 物品位置更新 | sc | cs: — ／ sc: code:uint8; pos_up_arr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品位置更新[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10509 | 整理指定背包 | bidirectional | cs: bag_code:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:整理指定背包[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10510 | 更新背包格子最大值 | sc | cs: — ／ sc: code:uint8; volume:uint8; open_volume:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新背包格子最大值[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10511 | 穿装备 | bidirectional | cs: bag_item_id:uint32; eqm_item_id:uint32; hero_bid:uint32 ／ sc: code:uint8; msg:string; is_auto:uint8; bag_item_id:uint32; eqm_item_id:uint32; eqm_new_pos:uint8; hero_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:穿装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10512 | 脱装备 | bidirectional | cs: eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 ／ sc: code:uint8; msg:string; eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:脱装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10513 | 装备升级 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; eqm_item_id_new:uint32; eqm_item_bid_new:uint32; eqm_item_power_new:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备升级[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10514 | 一件穿戴 | bidirectional | cs: — ／ sc: code:uint8; msg:string; bag_to_eqm:table; bag_replace_eqm:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一件穿戴[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10515 | 装备耐久度更新 | sc | cs: — ／ sc: durable_update:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备耐久度更新[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10516 | 修理单件装备 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:修理单件装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10517 | 修理全部装备上的装备 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:修理全部装备上的装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10518 | 元宝买物品 | bidirectional | cs: item_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:元宝买物品[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10519 | 装备强化 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; lev:uint8; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:装备强化[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10520 | 装备精炼 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; count:uint16; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; color:uint8; lev:uint8; exp:uint16; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备精炼[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10521 | 宝石镶嵌 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; jewel_item_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; pos:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝石镶嵌[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10522 | 宝石摘除 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; pos:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝石摘除[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10523 | 物品合成 | bidirectional | cs: item_bid:uint32; gold_state:uint8; all_state:uint8 ／ sc: code:uint8; msg:string; item_bid:uint32; bid_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:物品合成[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10524 | 物品分解 | bidirectional | cs: item_bid:uint32; all_state:uint32 ／ sc: code:uint8; msg:string; fc_bid_list:table; bid_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品分解[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10525 | 发送物品数据到聊天缓存，使用返回的值唯一id来构造点击事件 | bidirectional | cs: from_code:uint8; item_id:uint32 ／ sc: uniq_id:uint32; from_code:uint8; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发送物品数据到聊天缓存，使用返回的值唯一id来构造点击事件[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10526 | 使用10525返回的唯一id来读取一个聊天页面物品数据 | bidirectional | cs: srv_id:string; uniq_id:uint32 ／ sc: items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:使用10525返回的唯一id来读取一个聊天页面物品数据[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10527 | 新手礼包开启状态 | bidirectional | cs: — ／ sc: state_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:新手礼包开启状态[cmd_table.json]；1.4.9文档载于inventory_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 10528 | 打开新手礼包 | bidirectional | cs: lev:uint8; type:uint8 ／ sc: code:uint8; msg:string; lev:uint8; state_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开新手礼包[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10529 | 洗练 | bidirectional | cs: code_bag:uint8; eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; code_bag:uint8; eqm_item_id:uint32; score:uint16; power:uint32; refine:uint16; attr:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:洗练[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10530 | 宝石升级 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; jewel_pos:uint8; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; jewel_pos:uint8; jewel_bid:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝石升级[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10531 | 宝石镶嵌或升级所需铜币 | bidirectional | cs: item_list:table ／ sc: item_coin:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝石镶嵌或升级所需铜币[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10532 | 装备玩法所需元宝(只能做穿戴装备上的) | bidirectional | cs: bag_code:uint8; type:uint8; item_id:uint32 ／ sc: val:int32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:装备玩法所需元宝(只能做穿戴装备上的)[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10533 | 伙伴玩法所需元宝 | bidirectional | cs: type:uint8; partner_id:uint32 ／ sc: val:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴玩法所需元宝[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10534 | 物品价值元宝 | bidirectional | cs: item_bid:uint32 ／ sc: val:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:物品价值元宝[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10535 | 礼包开启获得 | sc | cs: — ／ sc: gift_item_bid:uint32; item_list:table; assets_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:礼包开启获得[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10536 | 道具分解 | bidirectional | cs: item_id:uint32; item_num:uint32 ／ sc: code:uint8; msg:string; bid_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:道具分解[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10537 | 道具绑定 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:道具绑定[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10540 | 英雄换装推送 | sc | cs: — ／ sc: eqm_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄换装推送[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10541 | 装备炼神 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; grade:uint8; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备炼神[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10542 | 物品使用特效 | sc | cs: — ／ sc: item_bid:uint32; val:string; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品使用特效[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10543 | 物品更新扩展字段 | sc | cs: — ／ sc: code:uint8; up_date_ext:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品更新扩展字段[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10544 | 伙伴法宝界面信息 | bidirectional | cs: — ／ sc: attrs_ext_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴法宝界面信息[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10545 | 法宝合成 | bidirectional | cs: eqm_item_id_1:uint32; eqm_item_id_2:uint32 ／ sc: code:uint8; msg:string; new_eqm_item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝合成[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10546 | 法宝重铸 | bidirectional | cs: eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; new_eqm_item_id:uint32; skill_list:table; attr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝重铸[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10547 | 法宝保存 | bidirectional | cs: eqm_item_id_1:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝保存[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10548 | 物品使用粒子特效 | sc | cs: — ／ sc: item_bid:uint32; val:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品使用粒子特效[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10551 | 获取铜钱袋价值 | bidirectional | cs: item_bid:uint32 ／ sc: val:uint32 | SYS_APPEAR_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取铜钱袋价值[cmd_table.json]；所属系统:Mount 坐骑[SYS_APPEAR_002][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10552 | 开启格子 | bidirectional | cs: bag_code:uint8; volume:uint8; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; old:uint16; new:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:开启格子[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10553 | 背包，角色仓库一对一 互换道具位置 | bidirectional | cs: from_code:uint8; from_item_id:uint32; to_code:uint8; to_item_id:uint32 ／ sc: code:uint8; msg:string; from_code:uint8; from_item_id:uint32; to_code:uint8; to_item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:背包，角色仓库一对一 互换道具位置[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10554 | 移动物品( 背包=>仓库; 仓库=>背包 ) | bidirectional | cs: from_code:uint8; target_code:uint8; item_id:uint32 ／ sc: code:uint8; msg:string; from_code:uint8; target_code:uint8; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:移动物品( 背包=>仓库; 仓库=>背包 )[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10555 | 物品炼化 | bidirectional | cs: items_id:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品炼化[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10556 | 提示客户端一键穿装 | sc | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提示客户端一键穿装[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10557 | 删除物品 | bidirectional | cs: bag_code:uint8; args:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除物品[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10558 | 玩家装备洗练套 | bidirectional | cs: — ／ sc: suit_lev:uint16; next_suit_lev:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玩家装备洗练套[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10560 | 获取材料价格(转成铜钱或者银两) | bidirectional | cs: args:table ／ sc: args:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取材料价格(转成铜钱或者银两)[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10561 | 获取材料价格（转成资产） | bidirectional | cs: key:uint16; args:table ／ sc: key:uint16; args:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取材料价格（转成资产）[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10570 | 仓库拾取到背包, 单个或者全部 | bidirectional | cs: bag_code:uint8; ItemIdList:table ／ sc: bag_code:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:仓库拾取到背包, 单个或者全部[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10571 | 装备升星 | bidirectional | cs: item_id:uint32; is_buy:uint8 ／ sc: code:uint8; msg:string; item_id:uint32; star_lev:uint8; star_grid:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备升星[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10572 | 自选礼包 | bidirectional | cs: gift_id:uint32; chose_ids:table; count:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自选礼包[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10573 | 时装激活 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; bid:uint32; msg:string | SYS_APPEAR_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:时装激活[cmd_table.json]；所属系统:Fashion/Skin 时装[SYS_APPEAR_009][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10574 | 时装穿戴 | bidirectional | cs: id:uint32 ／ sc: code:uint8; id:uint32; msg:string | SYS_APPEAR_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:时装穿戴[cmd_table.json]；所属系统:Fashion/Skin 时装[SYS_APPEAR_009][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10575 | 时装升星 | bidirectional | cs: id:uint32 ／ sc: code:uint8; id:uint32; msg:string | SYS_APPEAR_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:时装升星[cmd_table.json]；所属系统:Fashion/Skin 时装[SYS_APPEAR_009][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10576 | 时装脱下 | bidirectional | cs: id:uint32 ／ sc: code:uint8; id:uint32; msg:string | SYS_APPEAR_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:时装脱下[cmd_table.json]；所属系统:Fashion/Skin 时装[SYS_APPEAR_009][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10577 | 时装过期协议 | sc | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:时装过期协议[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10578 | 使用物品激活时装 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string | SYS_APPEAR_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:使用物品激活时装[cmd_table.json]；所属系统:Fashion/Skin 时装[SYS_APPEAR_009][systems_master.json]；1.4.9文档载于inventory_protocol.md |
| 10582 | 推送礼包奖励列表 | sc | cs: — ／ sc: item_id:uint32; item_bid:uint32; type:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送礼包奖励列表[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10586 | 活动仓库拾取到背包, 单个或者全部 | bidirectional | cs: ItemIdList:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动仓库拾取到背包, 单个或者全部[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10587 | 穿上古仙器装备 | bidirectional | cs: bag_item_id:uint32; eqm_item_id:uint32; hero_bid:uint32 ／ sc: code:uint8; msg:string; is_auto:uint8; bag_item_id:uint32; eqm_item_id:uint32; eqm_new_pos:uint8; hero_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:穿上古仙器装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10588 | 脱上古仙器装备 | bidirectional | cs: eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 ／ sc: code:uint8; msg:string; eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:脱上古仙器装备[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10589 | 获取飞升数据 | bidirectional | cs: — ／ sc: flyup_lev:uint8; flyup_stage:uint8; exp:uint32; dan_cnt:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取飞升数据[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10590 | 飞升熔炼 | bidirectional | cs: ItemIdList:table ／ sc: code:uint8; msg:string; ItemIdList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升熔炼[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10591 |  仙元丹使用协议 | bidirectional | cs: item_bid:uint32; use_num:uint8 ／ sc: code:uint8; msg:string; item_bid:uint32; use_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名: 仙元丹使用协议[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10592 | 获取上古神器限时抢购礼包数据 | bidirectional | cs: — ／ sc: end_time:uint32; GiftList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取上古神器限时抢购礼包数据[cmd_table.json]；1.4.9文档载于inventory_protocol.md |
| 10593 | 上古神器限时抢购礼包购买协议 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32; cnt:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上古神器限时抢购礼包购买协议[cmd_table.json]；1.4.9文档载于inventory_protocol.md |

### cmd_resolve_106.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10601 | 测试战斗伤害 | bidirectional | cs: flag:uint32 ／ sc: p:uint32; skill_bid:uint32; lev:uint32; hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:测试战斗伤害[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10610 | 战斗验算 | bidirectional | cs: fight_handle:table; mons_bid_value:table; fps:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗验算[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10621 | 修炼技能列表 | bidirectional | cs: — ／ sc: world_lev:uint16; skill_list:table | SYS_ECON_004 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:修炼技能列表[cmd_table.json]；所属系统:Storage/Warehouse 仓库[SYS_ECON_004][systems_master.json]；1.4.9文档载于scene_protocol.md |
| 10622 | 角色技能学习、技能升级 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; skill_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:角色技能学习、技能升级[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10630 | 场景技能列表 | sc | cs: — ／ sc: skill_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:场景技能列表[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10631 | 无目标使用技能 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; skill_bid:uint32; last_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:无目标使用技能[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10632 | 对目标使用技能 | bidirectional | cs: bid:uint32; target_type:uint8; target_id:uint32; target_srv_id:string ／ sc: code:uint8; msg:string; skill_bid:uint32; last_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对目标使用技能[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10633 | 对坐标使用技能 | bidirectional | cs: bid:uint32; x:uint16; y:uint16 ／ sc: code:uint8; msg:string; skill_bid:uint32; last_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对坐标使用技能[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10640 | 获取天命技能增加的BUFF效果 | bidirectional | cs: — ／ sc: buff_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取天命技能增加的BUFF效果[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10650 | 获取天赋开启情况 | bidirectional | cs: — ／ sc: talent_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取天赋开启情况[cmd_table.json]；1.4.9文档载于scene_protocol.md |
| 10651 | 使用修炼笔记 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用修炼笔记[cmd_table.json]；1.4.9文档载于scene_protocol.md |

### cmd_resolve_107.luac（33 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10701 | 领地建筑和建筑研究升级 | bidirectional | cs: flag:uint8; type:uint8 ／ sc: type:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:领地建筑和建筑研究升级[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10702 | 所有领地建筑和研究状态 | bidirectional | cs: — ／ sc: all_building:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:所有领地建筑和研究状态[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10705 | 进入内城 | cs | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入内城[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10706 | 内城特殊NPC列表 | bidirectional | cs: — ／ sc: npc_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:内城特殊NPC列表[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10707 | 增加内城特殊NPC | sc | cs: — ／ sc: npc_bid:uint32; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:增加内城特殊NPC[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10708 | 删除内城特殊NPC | sc | cs: — ／ sc: npc_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除内城特殊NPC[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10709 | 选择食物房生产 | bidirectional | cs: time:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:选择食物房生产[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10710 | 获取食物房生产食物的信息 | bidirectional | cs: — ／ sc: lev:uint8; store_num:uint32; status:uint8; left_time:uint32; total_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取食物房生产食物的信息[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10711 | 获取食物房生产食物 | bidirectional | cs: — ／ sc: code:uint8; msg:string; val:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取食物房生产食物[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10712 | 取消食物房生产食物 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消食物房生产食物[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10713 | 食物房生产食物加速 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:食物房生产食物加速[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10714 | 获取仓库信息 | bidirectional | cs: — ／ sc: lev:uint8; InfoList:table | SYS_ECON_004 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取仓库信息[cmd_table.json]；所属系统:Storage/Warehouse 仓库[SYS_ECON_004][systems_master.json]；1.4.9文档载于equipment_protocol.md |
| 10715 | 仓库达到上限发送信息 | sc | cs: — ／ sc: TypeList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仓库达到上限发送信息[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10716 | 仓库某一类型数量变化,发送更新通知 | sc | cs: — ／ sc: type:uint8; val:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仓库某一类型数量变化,发送更新通知[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10731 | 民房信息 | bidirectional | cs: Type:uint8 ／ sc: Type:uint8; lev:uint8; gold:uint32; next_time:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:民房信息[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10733 | 设置民房英雄 | bidirectional | cs: hero_list:table ／ sc: code:uint8; msg:string; set_house_hero_return:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置民房英雄[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10734 | 收民房金币 | bidirectional | cs: Type:uint8 ／ sc: code:uint8; msg:string; gold:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收民房金币[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10735 | 建筑居住的英雄 | bidirectional | cs: — ／ sc: house_hero:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:建筑居住的英雄[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10741 | 伐木场信息; | bidirectional | cs: — ／ sc: lev:uint8; status:uint8; flag:uint8; time:uint32; all_time:uint32; can_get:uint32; be_rob:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伐木场信息;[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10742 | 开始伐木 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始伐木[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10743 | 取消伐木 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消伐木[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10744 | 收伐木场产出的木头 | bidirectional | cs: — ／ sc: code:uint8; msg:string; wood:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收伐木场产出的木头[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10745 | 伐木场加速 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伐木场加速[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10751 | 开放的道具列表 | bidirectional | cs: — ／ sc: open_props_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开放的道具列表[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10752 | 升级道具 | bidirectional | cs: props_id:uint32; ext_queue_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级道具[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10753 | 制造道具 | bidirectional | cs: props_id:uint32; props_num:uint32; ext_queue_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:制造道具[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10754 | 升级道具冷却时间 | bidirectional | cs: — ／ sc: upgrate_time_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级道具冷却时间[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10755 | 制造道具冷却时间 | bidirectional | cs: — ／ sc: make_time_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:制造道具冷却时间[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10756 | 开通额外队列 | bidirectional | cs: queue_type:uint8; props_type:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开通额外队列[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10757 | 查看各个通道信息 | bidirectional | cs: — ／ sc: look_queue_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看各个通道信息[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10761 | 主堡信息 | bidirectional | cs: — ／ sc: lev:uint8; can_get:uint32; be_rob:uint32; next_time:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:主堡信息[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10762 | 收去主堡金币 | bidirectional | cs: — ／ sc: code:uint8; msg:string; gold:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收去主堡金币[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 10771 | 所有领地建筑和研究状态——地下城查看他人数据，服务端主动推送 | sc | cs: — ／ sc: all_building:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:所有领地建筑和研究状态——地下城查看他人数据，服务端主动推送[cmd_table.json]；1.4.9文档载于equipment_protocol.md |

### cmd_resolve_108.luac（7 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10800 | 读取邮件列表 | bidirectional | cs: — ／ sc: mail:table | SYS_ECON_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:读取邮件列表[cmd_table.json]；所属系统:Mail 邮件[SYS_ECON_009][systems_master.json] |
| 10801 | 提取单个邮件的附件 | bidirectional | cs: id:uint32 ／ sc: id:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:提取单个邮件的附件[cmd_table.json] |
| 10802 | 一键提取附件 | bidirectional | cs: — ／ sc: ids:table; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键提取附件[cmd_table.json] |
| 10803 | 新邮件推送 | bidirectional | cs: — ／ sc: id:uint32; from_name:string; subject:string; content:string; assets:table; items:table; send_time:uint32; read_time:uint32; time_out:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:新邮件推送[cmd_table.json] |
| 10804 | 删除没有附件的邮件 | sc | cs: — ／ sc: ids:table; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除没有附件的邮件[cmd_table.json] |
| 10805 | 读取邮件 | bidirectional | cs: id:uint32 ／ sc: id:uint32; code:uint8; msg:string; read_time:uint32; is_delete:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:读取邮件[cmd_table.json] |
| 10810 | 客服反馈 | bidirectional | cs: issue_type:uint8; title:string; content:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客服反馈[cmd_table.json] |

### cmd_resolve_109.luac（42 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 10900 | 封号 | bidirectional | cs: rid:uint32; srv_id:string; hour:uint32; interdict:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:封号[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10901 | 禁言 | bidirectional | cs: rid:uint32; srv_id:string; hour:uint32; banned:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:禁言[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10902 | 踢人 | bidirectional | cs: rid:uint32; srv_id:string; stop_role:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:踢人[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10910 | 大地图数据 | bidirectional | cs: — ／ sc: dnf_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:大地图数据[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10911 | BUFF | sc | cs: — ／ sc: rid:uint32; srv_id:string; buffs:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:BUFF[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10912 | BUFF更新信息 | sc | cs: — ／ sc: bid:uint32; effect:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:BUFF更新信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10913 | 特殊buff显示 | sc | cs: — ／ sc: buffs:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:特殊buff显示[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10921 | 世界等级 | bidirectional | cs: — ／ sc: world_lev:uint8; next:uint32; exp:uint16; dec_exp:uint16; open_day:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:世界等级[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10922 | 全服活动的活动状态 | bidirectional | cs: — ／ sc: act_list:table | SYS_GM_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:全服活动的活动状态[cmd_table.json]；所属系统:GM Tools[SYS_GM_001][systems_master.json]；1.4.9文档载于movement_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 10923 | 全服活动的单个活动状态 | bidirectional | cs: id:uint16 ／ sc: id:uint16; status:uint8; int_args:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:全服活动的单个活动状态[cmd_table.json]；1.4.9文档载于movement_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 10924 | 个人活动图标 | bidirectional | cs: — ／ sc: act_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:个人活动图标[cmd_table.json]；1.4.9文档载于movement_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 10925 | 个人活动图标的单个活动状态 | bidirectional | cs: id:uint16 ／ sc: id:uint16; status:uint8; int_args:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人活动图标的单个活动状态[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10930 | 领取双倍 | bidirectional | cs: — ／ sc: code:uint8; msg:string; double:uint16; double_sum:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:领取双倍[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10931 | 冻结双倍 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:冻结双倍[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10932 | 双倍信息 | bidirectional | cs: — ／ sc: double:uint16; double_sum:uint16; double_state:uint16; off_state:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:双倍信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10933 | 离线经验开启 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:离线经验开启[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10934 | 离线经验关闭 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:离线经验关闭[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10935 | 双倍点改变 | sc | cs: — ／ sc: double:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:双倍点改变[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10941 | 通知功能开启 | sc | cs: — ／ sc: id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知功能开启[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10942 | 客户端请求开启功能 | bidirectional | cs: id:uint8 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端请求开启功能[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10945 | 领取卡包(媒体卡,新手卡等)奖励 | bidirectional | cs: card_id:string ／ sc: code:uint8; msg:string; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取卡包(媒体卡,新手卡等)奖励[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10946 | 创号第二天领取神器 | bidirectional | cs: — ／ sc: code:uint8; msg:string; item_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:创号第二天领取神器[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10947 | 目标玩家基础信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; name:string; lev:uint16; career:uint16; sex:uint8; is_vip:uint8; vip_lev:uint8; gname:string; cur_title:uint32; marry_state:uint8; spouse_name:string; attr:table; power:uint32; all_power:uint32; face_id:uint32; ride:uint8; lingshou:uint8; wing:uint8; has_shenqi:uint8; refine_suit:uint16; refine_suit_next:uint16; misc_uint32:table; animate_res:table; jiebai_title:string; jiebai_lev:uint8; halo_stage:uint8; chair_stage:uint8; spirit:uint8; flyup_lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:目标玩家基础信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10948 | 目标玩家装备信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家装备信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10949 | 目标玩家坐骑信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家坐骑信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10950 | 目标玩家仙灵信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家仙灵信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10951 | 目标玩家翅膀信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; color:uint8; wing_id:uint32; power:uint32; wing_skill:table; add_attr:table; star:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家翅膀信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10952 | 目标玩家神器信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; use_id:uint32; shenqi_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家神器信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10953 | 查看目标玩家数据 | bidirectional | cs: rid:uint32; srv_id:string; type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看目标玩家数据[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10954 | 目标玩家魂环信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; name:string; stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; looks:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:目标玩家魂环信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10955 | 目标玩家仙座信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家仙座信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10957 | 目标玩家灵器信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家灵器信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10958 | 目标玩家上古神器装备信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标玩家上古神器装备信息[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10995 | 合服服务器ID列表 | bidirectional | cs: — ／ sc: srv_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:合服服务器ID列表[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10996 | 新版本客户端版本号 | bidirectional | cs: — ／ sc: cli_ver_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:新版本客户端版本号[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10997 | 服务器版本标签 | bidirectional | cs: — ／ sc: flag:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:服务器版本标签[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10998 | 客户端版本号 | bidirectional | cs: — ／ sc: cli_ver:uint16; flag:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端版本号[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10999 | 客户端报错日志 | cs | cs: msg:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端报错日志[cmd_table.json]；1.4.9文档载于movement_protocol.md |
| 10926 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_GM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_10926；引用系统: GM Tools[SYS_GM_001] |
| 10927 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_GM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_10927；引用系统: GM Tools[SYS_GM_001] |
| 10928 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_GM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_10928；引用系统: GM Tools[SYS_GM_001] |
| 10929 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_GM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_10929；引用系统: GM Tools[SYS_GM_001] |

### cmd_resolve_11.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 1100 | 测试连接登录处理 | cs | cs: ticket:string; account:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:测试连接登录处理[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 1101 | 测试连接登录处理 | sc | cs: — ／ sc: code:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:测试连接登录处理[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 1110 | 帐号登录 | bidirectional | cs: args:table ／ sc: code:uint8; msg:string; roles:table; least_career:uint8 | SYS_CORE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:帐号登录[cmd_table.json]；所属系统:Account Login[SYS_CORE_001][systems_master.json]；1.4.9文档载于login_protocol.md |
| 1199 | 心跳包 | bidirectional | cs: — ／ sc: time:uint32 | SYS_CORE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:心跳包[cmd_table.json]；所属系统:Account Login[SYS_CORE_001][systems_master.json]；1.4.9文档载于login_protocol.md |

### cmd_resolve_110.luac（19 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11000 | 获取地下城数据 | bidirectional | cs: — ／ sc: times:uint8; ceng_max:uint8; ceng:uint8; dnf_base:table; hero_list:table; mon_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取地下城数据[cmd_table.json] |
| 11001 | 开启地下城 | bidirectional | cs: ceng:uint8 ／ sc: code:uint8; msg:string; ceng:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:开启地下城[cmd_table.json] |
| 11002 | 搜索地下城 | bidirectional | cs: ceng:uint8 ／ sc: code:uint8; msg:string; times:uint8; id:uint8; dnf_num:uint8; status:uint8; update_time:uint32; mon_list:table; hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:搜索地下城[cmd_table.json] |
| 11003 | 挑战 | bidirectional | cs: ceng:uint8; hero_list:table ／ sc: code:uint8; msg:string; hero_list:table; mon_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战[cmd_table.json] |
| 11004 | 设置防守骑士 | bidirectional | cs: ceng:uint8; hero_list:table ／ sc: code:uint8; msg:string; hero_list:table; assets:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置防守骑士[cmd_table.json] |
| 11005 | 大地图更换对手 | bidirectional | cs: tr_rid:uint32; tr_srv_id:string ／ sc: code:uint8; msg:string; old_tr_rid:uint32; old_tr_srv_id:string; new_tr_rid:uint32; new_tr_srv_id:string; new_tr_name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:大地图更换对手[cmd_table.json] |
| 11006 | 领取地下城奖励 | bidirectional | cs: ceng:uint8 ／ sc: code:uint8; msg:string; type:uint8; value:uint32; item_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取地下城奖励[cmd_table.json] |
| 11007 | 设置陷阱 | bidirectional | cs: ceng:uint8; pitfall:uint32; x:int16; y:int16 ／ sc: code:uint8; msg:string; x:int16; y:int16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置陷阱[cmd_table.json] |
| 11008 | 攻打自己地下城客户端回调 | bidirectional | cs: code:uint8; ceng:uint8; hero_list:table; mon_list:table ／ sc: code:uint8; msg:string; status:uint8; time:uint32; hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打自己地下城客户端回调[cmd_table.json] |
| 11009 | 更新自己地下城单层状态， 主要为了超时地下城制空 | sc | cs: — ／ sc: ceng:uint8; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新自己地下城单层状态， 主要为了超时地下城制空[cmd_table.json] |
| 11010 | 查看地图上某个玩家地下城数据 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; name:string; lev:uint8; face_id:uint16; sex:uint8; ceng:uint8; shield_time:uint32; be_hero_list:table; be_tr_hero_list:table; reward:table; dnf_base:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看地图上某个玩家地下城数据[cmd_table.json] |
| 11011 | 攻打地图上其他玩家地下城 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; ceng:uint8; num:uint8; set_hero_list:table; hero_list:table; tr_hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打地图上其他玩家地下城[cmd_table.json] |
| 11012 | 攻打其他玩家地下城客户端回调 | bidirectional | cs: code:uint8; tr_rid:uint32; tr_srv_id:string; hero_list:table; tr_hero_list:table ／ sc: code:uint8; msg:string; type:uint8; reward:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打其他玩家地下城客户端回调[cmd_table.json] |
| 11013 | 放弃挑战自己地下城 | bidirectional | cs: ceng:uint8 ／ sc: code:uint8; msg:string; status:uint8; ceng:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:放弃挑战自己地下城[cmd_table.json] |
| 11014 | 放弃挑战其他玩家地下城 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; tr_rid:uint32; tr_srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:放弃挑战其他玩家地下城[cmd_table.json] |
| 11015 | 刷新自己地下城资产 | bidirectional | cs: — ／ sc: reward:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新自己地下城资产[cmd_table.json] |
| 11016 | 掠夺 设置队伍 | bidirectional | cs: hero_list_1:table; hero_list_2:table; hero_list_3:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:掠夺 设置队伍[cmd_table.json] |
| 11017 | 设置过的队伍信息 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; set_hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:设置过的队伍信息[cmd_table.json] |
| 11018 | 地图上进攻按钮 返回11010 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; set_hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:地图上进攻按钮 返回11010[cmd_table.json] |

### cmd_resolve_111.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11100 | 剧情播放（客户端播放返回第几部） | cs | cs: drama_bid:uint32; step_id:uint8 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:剧情播放（客户端播放返回第几部）[cmd_table.json] |
| 11101 | 服务端触发剧情 | sc | cs: — ／ sc: drama_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:服务端触发剧情[cmd_table.json] |
| 11102 | 跳过剧情 | bidirectional | cs: drama_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:跳过剧情[cmd_table.json] |
| 11110 | 播放服务端剧情 | sc | cs: — ／ sc: id:uint8; act_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:播放服务端剧情[cmd_table.json] |
| 11111 | 点击剧情单位 | bidirectional | cs: type:uint16; bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:点击剧情单位[cmd_table.json] |

### cmd_resolve_112.luac（33 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11200 | 伙伴基础界面信息 | bidirectional | cs: — ／ sc: volume:uint8; volume_open:uint8; partner_bag:table; gratis:table | SYS_EQUIP_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:伙伴基础界面信息[cmd_table.json]；所属系统:Equipment System[SYS_EQUIP_001][systems_master.json]；1.4.9文档载于equipment_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 11201 | 获取单个伙伴数据 | bidirectional | cs: — ／ sc: id:uint32; bid:uint32; type:uint8; color:uint8; lifttime:uint32; lev:uint8; exp:uint32; grow:uint16; score:uint32; stage:uint8; rebirth:uint8; acc:uint8; partner_attr:table; power:uint32; aptitude:table; innate_skill:uint32; skill:table; jindan_skill:table; talisman_skill:table; ext:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取单个伙伴数据[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11202 | 伙伴加经验 | sc | cs: — ／ sc: id:uint32; exp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴加经验[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11203 | 招募伙伴 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:招募伙伴[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11204 | 单个伙伴技能 | bidirectional | cs: id:uint32 ／ sc: id:uint32; skill:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单个伙伴技能[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11205 | 放生 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:放生[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11206 | 开启格子 | bidirectional | cs: state:uint8 ／ sc: code:uint8; msg:string; volume:uint8; volume_open:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:开启格子[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11207 | 升级 | sc | cs: — ／ sc: lev_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11208 | 洗髓 | bidirectional | cs: id:uint32; state:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:洗髓[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11209 | 寿命 | sc | cs: — ／ sc: lift_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:寿命[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11210 | 伙伴属性 | sc | cs: — ／ sc: id:uint32; lev:uint16; exp:uint32; color:uint8; score:uint32; partner_attr:table; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴属性[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11211 | 法宝技能改变 | sc | cs: — ／ sc: id:uint32; talisman_skill:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝技能改变[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11212 | 特殊获得伙伴 | bidirectional | cs: bid:uint32; type:uint8 ／ sc: code:uint8; msg:string; bid:uint32; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:特殊获得伙伴[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11213 | 培养资质 | bidirectional | cs: id:uint32; attr_code:uint16 ／ sc: code:uint8; msg:string; attr_code:uint16; attr_val:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:培养资质[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11214 | 移动伙伴( 角色=>仓库; 仓库=>角色 ) | bidirectional | cs: from_code:uint8; target_code:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string; from_code:uint8; target_code:uint8; partner_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:移动伙伴( 角色=>仓库; 仓库=>角色 )[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11215 | 伙伴仓库数据 | bidirectional | cs: — ／ sc: partner_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:伙伴仓库数据[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11216 | 神将兑换 | bidirectional | cs: partner_bid:uint32; state:uint8 ／ sc: code:uint8; msg:string; partner_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:神将兑换[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11217 | 伙伴穿戴饰品 | bidirectional | cs: id:uint32; state:uint8 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴穿戴饰品[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11218 | 神将重铸 | bidirectional | cs: id:uint32; state:uint8 ／ sc: code:uint8; msg:string; partner_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:神将重铸[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11221 | 获取聊天缓存伙伴 | bidirectional | cs: srv_id:string; cache_id:uint32 ／ sc: cache_id:uint32; partner_list:table; eqm_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取聊天缓存伙伴[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11222 | 聊天向伙伴缓存进程发送数据 | bidirectional | cs: id:uint32 ／ sc: code:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:聊天向伙伴缓存进程发送数据[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11223 | 伙伴战力更新 | sc | cs: — ／ sc: power_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴战力更新[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11224 | 查看其他人伙伴 | bidirectional | cs: rid:uint32; srv_id:string; id:uint32 ／ sc: id:uint32; partner_list:table; eqm_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看其他人伙伴[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11225 | 更新ext字段 | sc | cs: — ／ sc: id:uint32; ext:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新ext字段[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11226 | 伙伴进阶 | bidirectional | cs: id:uint32; state:uint8 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴进阶[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11227 | 伙伴转生 | bidirectional | cs: id:uint32; hufu_id:uint32; fazhen_id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴转生[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11228 | 购买并使用技能书 | bidirectional | cs: id:uint32; item_id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买并使用技能书[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11237 | 获取伙伴羁绊数据 | bidirectional | cs: formation_type:uint32 ／ sc: code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; formation_type:uint32; partner_list:table; exp:uint32; crit_cnt:uint32; not_crit_cnt:uint32; break:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取伙伴羁绊数据[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11238 | 伙伴羁绊升星 | bidirectional | cs: — ／ sc: code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; exp:uint32; crit_cnt:uint32; not_crit_cnt:uint32; break:uint32; is_crit:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴羁绊升星[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11239 | 羁绊伙伴上/下阵 | bidirectional | cs: formation_type:uint32; index:uint32; partner_id:uint32; op_type:uint32 ／ sc: code:uint32; msg:string; formation_type:uint32; index:uint32; partner_id:uint32; op_type:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:羁绊伙伴上/下阵[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11240 | 穿戴/脱下符文 | bidirectional | cs: index:uint32; rune_index:uint32; item_id:uint32; op_type:uint32 ／ sc: code:uint32; msg:string; index:uint32; rune_index:uint32; item_id:uint32; op_type:uint32; items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:穿戴/脱下符文[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11241 | 符文吞噬 | bidirectional | cs: index:uint32; rune_index:uint32; item_id:uint32; item_list:table ／ sc: code:uint32; msg:string; index:uint32; rune_index:uint32; item_id:uint32; item_lev:uint32; item_exp:uint32; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:符文吞噬[cmd_table.json]；1.4.9文档载于equipment_protocol.md |
| 11242 | 伙伴羁绊突破 | bidirectional | cs: — ／ sc: code:uint32; msg:string; stage:uint32; star:uint32; open_index:uint32; rune_data:table; exp:uint32; crit_cnt:uint32; not_crit_cnt:uint32; break:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴羁绊突破[cmd_table.json]；1.4.9文档载于equipment_protocol.md |

### cmd_resolve_113.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11300 | 竞技场界面信息 | bidirectional | cs: — ／ sc: trophy:uint32; times:uint8; index_state:uint8; pk_show:table; pk_record:table | SYS_COMM_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:竞技场界面信息[cmd_table.json]；所属系统:Arena 竞技场[SYS_COMM_002][systems_master.json]；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 11301 | 晋级界面信息 | bidirectional | cs: — ／ sc: lev:uint8; num:uint8 | SYS_COMM_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:晋级界面信息[cmd_table.json]；所属系统:Arena 竞技场[SYS_COMM_002][systems_master.json]；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 11302 | 挑战 | bidirectional | cs: id:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战[cmd_table.json] |
| 11303 | 晋级挑战 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:晋级挑战[cmd_table.json] |
| 11304 | 晋级挑战结果 | sc | cs: — ／ sc: code:uint8; num:uint8; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:晋级挑战结果[cmd_table.json] |
| 11305 | 刷新对手 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新对手[cmd_table.json] |
| 11306 | 反击 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:反击[cmd_table.json] |
| 11307 | 增加战报数据 | sc | cs: — ／ sc: trophy:uint32; pk_record:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:增加战报数据[cmd_table.json] |
| 11308 | 竞技场5战奖励数据 | bidirectional | cs: — ／ sc: win_times:uint8; state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:竞技场5战奖励数据[cmd_table.json] |
| 11309 | 竞技场5战奖励领奖 | bidirectional | cs: — ／ sc: code:uint8; msg:string; prize:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:竞技场5战奖励领奖[cmd_table.json] |
| 11310 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_COMM_002 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_11310；引用系统: Arena 竞技场[SYS_COMM_002] |

### cmd_resolve_114.luac（15 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11400 | 进入仙魔战场 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入仙魔战场[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11401 | 离开仙魔战场 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:离开仙魔战场[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11402 | 战场内位置广播 | bidirectional | cs: — ／ sc: pos_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战场内位置广播[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11403 | 战场内玩家数据 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战场内玩家数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11404 | 战场玩法 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8; tr_rid:uint32; tr_srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战场玩法[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11405 | 离开玩家Id | bidirectional | cs: — ／ sc: leave_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:离开玩家Id[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11406 | 准备区战力数据 | bidirectional | cs: — ／ sc: leave_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备区战力数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11407 | 准备区新加角色数据 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备区新加角色数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11408 | 战区角色数据 | bidirectional | cs: — ／ sc: kill_num:uint8; cent:uint16; room_id:uint8; x_realm:uint16; m_realm:uint16; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战区角色数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11409 | 结算面板 | sc | cs: — ／ sc: kill_num:uint8; cent:uint16; realm_win:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结算面板[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11410 | 英雄榜数据 | bidirectional | cs: sm_lev:uint8; room_id:uint8 ／ sc: sm_lev:uint8; room_id:uint8; win_realm:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄榜数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11411 | 第一次请求英雄榜数据 | bidirectional | cs: — ／ sc: sm_lev:uint8; room_id:uint8; win_realm:uint8; role_list:table; rank:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:第一次请求英雄榜数据[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11412 | 主动请求角色战区信息 | bidirectional | cs: — ／ sc: pos:uint8; realm:uint8; state:uint8; skill_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:主动请求角色战区信息[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11413 | 战场技能 被使用玩家 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; skii_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战场技能 被使用玩家[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11414 | 准备区获得资产奖励（个人） | bidirectional | cs: — ／ sc: assets_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备区获得资产奖励（个人）[cmd_table.json]；1.4.9文档载于skill_protocol.md |

### cmd_resolve_115.luac（8 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11500 | 百草园主界面 | bidirectional | cs: — ／ sc: lingqi:uint32; garden_work:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:百草园主界面[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11501 | 百草园 伙伴驻守 | bidirectional | cs: type:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string; type:uint8; partner_id:uint32; state:uint8; time_out:uint32; val:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:百草园 伙伴驻守[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11502 | 开启格子 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8; volume:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开启格子[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11503 | 收获果实 | bidirectional | cs: type:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string; type:uint8; partner_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收获果实[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11504 | 通知果园伙伴状态改变 | sc | cs: — ／ sc: type:uint8; partner_id:uint32; state:uint8; time_out:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知果园伙伴状态改变[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11505 | 最新灵气值 | sc | cs: — ／ sc: lingqi:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:最新灵气值[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11506 | 一键领取 | bidirectional | cs: — ／ sc: code:uint8; msg:string; garden_partner:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键领取[cmd_table.json]；1.4.9文档载于skill_protocol.md |
| 11507 | 元宝换灵气 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:元宝换灵气[cmd_table.json]；1.4.9文档载于skill_protocol.md |

### cmd_resolve_116.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11600 | 翅膀主界面 | bidirectional | cs: — ／ sc: color:uint8; wing_id:uint32; power:uint32; wing_skill:table; add_attr:table; star:uint16; lingxi_num:uint32; jiewing_id:uint32; surface_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:翅膀主界面[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11601 | 翅膀幻化 | bidirectional | cs: is_buy:uint8 ／ sc: code:uint8; msg:string; wing_id:uint32; star:uint8; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:翅膀幻化[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11602 | 保存翅膀幻化（不用） | bidirectional | cs: — ／ sc: code:uint8; msg:string; wing_id:uint32; skill_bid:uint32; add_attr:table; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:保存翅膀幻化（不用）[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11603 | 翅膀进阶 | bidirectional | cs: is_buy:uint8 ／ sc: code:uint8; msg:string; color:uint8; star:uint16; wing_id:uint32; wing_skill:table; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翅膀进阶[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11604 | 非时限翅膀激活 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:非时限翅膀激活[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11605 | 时限翅膀激活 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:时限翅膀激活[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11606 | 改变翅膀外形 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; animate:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:改变翅膀外形[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11607 | 翅膀升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翅膀升星[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11698 | 获取重置后翅膀信息 | bidirectional | cs: — ／ sc: wing_id:uint32; star:uint8; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取重置后翅膀信息[cmd_table.json]；1.4.9文档载于partner_protocol.md |
| 11699 | 保存重置后的翅膀 | bidirectional | cs: — ／ sc: code:uint8; msg:string; wing_id:uint32; star:uint8; power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:保存重置后的翅膀[cmd_table.json]；1.4.9文档载于partner_protocol.md |

### cmd_resolve_117.luac（19 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11700 | 嘉年华主界面 | bidirectional | cs: — ／ sc: free_times:uint8; all_times:uint8; reward_coin:uint32; one_name:string; one_coin:uint32; record_server:table; record_self:table | SYS_DUNGEON_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:嘉年华主界面[cmd_table.json]；所属系统:Dungeon 副本[SYS_DUNGEON_001][systems_master.json]；1.4.9文档载于social_protocol.md |
| 11701 | 抽奖 | bidirectional | cs: — ／ sc: code:uint8; msg:string; id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:抽奖[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11702 | 发送奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:发送奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11703 | 元宝嘉年华主界面 | bidirectional | cs: — ／ sc: get_times:uint8; all_times:uint8; reward_gold:uint32; one_name:string; one_coin:uint32; record_server:table; record_self:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:元宝嘉年华主界面[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11704 | 抽奖 | bidirectional | cs: — ／ sc: code:uint8; msg:string; id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:抽奖[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11705 | 发送奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发送奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11706 | 元宝嘉年华活动倒计时 | bidirectional | cs: — ／ sc: time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:元宝嘉年华活动倒计时[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11707 | vip嘉年华主界面 | bidirectional | cs: — ／ sc: record_server:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip嘉年华主界面[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11708 | vip转盘抽奖 | bidirectional | cs: — ／ sc: code:uint8; msg:string; id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip转盘抽奖[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11709 | vip转盘发送奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:vip转盘发送奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11710 | 聚宝盆主界面 | bidirectional | cs: type:uint8 ／ sc: type:uint8; get_times:uint8; record_server:table; record_self:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:聚宝盆主界面[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11711 | 抽奖一次 | bidirectional | cs: — ／ sc: code:uint8; msg:string; id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:抽奖一次[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11712 | 抽奖多次 | bidirectional | cs: type:uint8; count:uint8 ／ sc: code:uint8; type:uint8; msg:string; Items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:抽奖多次[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11713 | 抽奖一次发送奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:抽奖一次发送奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11717 | 幸运转盘主界面 | bidirectional | cs: — ／ sc: timestamp:uint32; free_time:uint8; holiday_name:string; reward_list:table; record_server:table; show_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:幸运转盘主界面[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11718 | 幸运转盘抽奖一次 | bidirectional | cs: pay_type:uint8 ／ sc: code:uint8; msg:string; id:uint32; reward_id:uint32; record_server:table; reward:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:幸运转盘抽奖一次[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11719 | 幸运转盘抽奖多次 | bidirectional | cs: pay_type:uint8 ／ sc: code:uint8; msg:string; record_server:table; reward:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:幸运转盘抽奖多次[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11720 | 刷新幸运转盘 | bidirectional | cs: — ／ sc: code:uint8; msg:string; free_time:uint8; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新幸运转盘[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11721 | 领取幸运转盘奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取幸运转盘奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |

### cmd_resolve_118.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11800 | 帮会竞技场报名 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会竞技场报名[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11801 | 设置线路 | bidirectional | cs: rid:uint32; srv_id:string; set_line:uint8 ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置线路[cmd_table.json]；1.4.9文档载于social_protocol.md |

### cmd_resolve_119.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 11900 | 运营活动基本信息 | bidirectional | cs: — ／ sc: first_reward:uint8; day_reward:uint8; online_time:uint32; online_id:uint8; lev_list:table; timer_reward:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:运营活动基本信息[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11901 | 领取奖励 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11902 | 服务端通知有奖励可领 | sc | cs: — ／ sc: type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:服务端通知有奖励可领[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 11999 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_GM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_11999；引用系统: GM Tools[SYS_GM_001] |

### cmd_resolve_12.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 1200 | 收发包测试 | cs | cs: len:uint16 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收发包测试[cmd_table.json]；1.4.9文档载于login_protocol.md |
| 1201 | 收发包测试 | bidirectional | cs: time:l; id:uint32; msg:string ／ sc: time:l; id:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:收发包测试[cmd_table.json]；1.4.9文档载于login_protocol.md |

### cmd_resolve_120.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12000 | 进入副本 | bidirectional | cs: dung_bid:uint32 ／ sc: tips:uint16; msg:string; mon_list:table; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入副本[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12001 | 副本挑战结算 | bidirectional | cs: dung_bid:uint32; finish:uint32; live_num:uint8 ／ sc: bid:uint16; star_lev:uint8; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本挑战结算[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12002 | 副本领取首次通关奖励 | bidirectional | cs: dung_bid:uint32 ／ sc: code:uint8; msg:string; dung_bid:uint32; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本领取首次通关奖励[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12003 | 最高章节 | bidirectional | cs: — ／ sc: chapter_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:最高章节[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12004 | 章节开启 | bidirectional | cs: chapter_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:章节开启[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12005 | 所有开启章节的关卡星级情况 | bidirectional | cs: — ／ sc: chapter_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:所有开启章节的关卡星级情况[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12006 | 请求副本进入剩余次数 | bidirectional | cs: bid:uint32 ／ sc: bid:uint32; left_times:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求副本进入剩余次数[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12007 | 请求当前购买次数 | bidirectional | cs: bid:uint32 ／ sc: bid:uint32; buy_times:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求当前购买次数[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12008 | 购买副本进入次数 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; count:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买副本进入次数[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12021 | 属性副本冷却时间列表 | bidirectional | cs: — ／ sc: week:uint8; interval_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:属性副本冷却时间列表[cmd_table.json]；1.4.9文档载于social_protocol.md |
| 12022 | 某副本类型 | bidirectional | cs: dung_bid:uint16 ／ sc: num:uint8; sec:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:某副本类型[cmd_table.json]；1.4.9文档载于social_protocol.md |

### cmd_resolve_121.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12100 | 功能状态验证 | bidirectional | cs: function_id:uint32 ／ sc: status:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:功能状态验证[cmd_table.json] |
| 12101 | 更新功能状态 | bidirectional | cs: — ／ sc: function_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新功能状态[cmd_table.json] |

### cmd_resolve_122.luac（15 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12201 | 勘探 | bidirectional | cs: — ／ sc: code:uint8; msg:string; minerals:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:勘探[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12202 | 勘探提示 | bidirectional | cs: — ／ sc: code:uint8; msg:string; coin:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:勘探提示[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12203 | 进入矿洞 | bidirectional | cs: id:uint32 ／ sc: type:uint8; status:uint8; item_id:uint32; total:uint32; speed:uint32; left_time:uint32; stronghold:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入矿洞[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12204 | 攻打矿中的据点 | bidirectional | cs: id:uint32; s_id:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打矿中的据点[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12205 | 攻打矿洞据点成功或者失败 | bidirectional | cs: id:uint32; s_id:uint8; flag:uint8; hero_list:table; g_flag:uint8; g_list:table ／ sc: code:int8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打矿洞据点成功或者失败[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12206 | 更换骑士驻守 | bidirectional | cs: id:uint32; stronghold_id:uint8; hero_list:table ／ sc: code:uint8; msg:string; total:uint32; speed:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更换骑士驻守[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12207 | 矿被占领,发送给客户端 | bidirectional | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿被占领,发送给客户端[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12208 | 获取据点信息 | bidirectional | cs: id:uint32; stronghold_id:uint8 ／ sc: code:uint8; msg:string; s_id:uint8; rid:uint32; srv_id:string; name:string; face_id:uint16; mon_list:table; hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取据点信息[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12209 | 矿枯竭提示 | bidirectional | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿枯竭提示[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12210 | 矿枯竭获取收益 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; type:uint8; lev:uint8; item_id:uint32; total:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿枯竭获取收益[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12211 | 上线获取矿信息 | bidirectional | cs: — ／ sc: minerals:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上线获取矿信息[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12212 | 矿废弃提示 | bidirectional | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿废弃提示[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12213 | 矿攻占成功(服务端发送) | bidirectional | cs: — ／ sc: type:uint8; lev:uint8; item_id:uint32; total:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿攻占成功(服务端发送)[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12214 | 攻打据点获取自身英雄相关信息列表 | bidirectional | cs: id:uint32 ／ sc: hero_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打据点获取自身英雄相关信息列表[cmd_table.json]；1.4.9文档载于chat_protocol.md |
| 12215 | 矿攻打超时提示 | bidirectional | cs: — ／ sc: id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:矿攻打超时提示[cmd_table.json]；1.4.9文档载于chat_protocol.md |

### cmd_resolve_124.luac（39 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12400 | 已接列表 | bidirectional | cs: — ／ sc: mission_list:table | SYS_QUEST_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:已接列表[cmd_table.json]；所属系统:Mission/Quest 任务[SYS_QUEST_001][systems_master.json]；1.4.9文档载于task_protocol.md |
| 12401 | 可接任务列表 | bidirectional | cs: — ／ sc: missions:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:可接任务列表[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12402 | 接受任务 | bidirectional | cs: mission_bid:uint32 ／ sc: code:uint8; msg:string; missions:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接受任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12403 | 提交任务 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:提交任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12404 | 删除已接任务 | bidirectional | cs: mission_bid:uint32 ／ sc: code:uint8; msg:string; mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除已接任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12405 | 更新已接任务进度 | bidirectional | cs: — ／ sc: update_mission_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新已接任务进度[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12406 | 删除已接任务列表 | bidirectional | cs: — ／ sc: del_mission_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除已接任务列表[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12407 | 添加已接任务列表 | bidirectional | cs: — ／ sc: add_mission_list:table | SYS_QUEST_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:添加已接任务列表[cmd_table.json]；所属系统:Mission/Quest 任务[SYS_QUEST_001][systems_master.json]；1.4.9文档载于task_protocol.md |
| 12408 | 删除可接任务列表 | bidirectional | cs: — ／ sc: delete_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除可接任务列表[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12409 | 添加可接任务列表 | bidirectional | cs: — ／ sc: missions:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:添加可接任务列表[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12410 | 推送跑环任务抽奖 | bidirectional | cs: — ／ sc: id:uint32; lottery_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:推送跑环任务抽奖[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12411 | 跑环抽奖 | bidirectional | cs: — ／ sc: id:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:跑环抽奖[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12412 | 特殊任务的奖励数据 | bidirectional | cs: bid:uint32 ／ sc: bid:uint32; assets:table; items:table; guild_assets:uint32; guild_wage:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:特殊任务的奖励数据[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12413 | 更新任务目标拓展参数 | bidirectional | cs: — ／ sc: bid:uint32; progress_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新任务目标拓展参数[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12414 | 对话任务完成 | bidirectional | cs: talk_bid:uint32; mission_bid:uint32; npc_bid:uint32 ／ sc: mission_bid:uint32; npc_bid:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对话任务完成[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12415 | 提交物品,完成任务 | bidirectional | cs: mission_bid:uint32; item_bid:uint32; item_num:uint32 ／ sc: mission_bid:uint32; item_bid:uint32; item_num:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交物品,完成任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12416 | 主线任务进度 | bidirectional | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:主线任务进度[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12417 | 提交物品,完成任务 | bidirectional | cs: mission_bid:uint32; partner_id:uint32; partner_num:uint32 ／ sc: mission_bid:uint32; partner_id:uint32; partner_num:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交物品,完成任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12418 | 发送任务数据到聊天缓存，使用返回的值唯一id来构造点击事件 | bidirectional | cs: mission_bid:uint32 ／ sc: uniq_id:uint32; mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发送任务数据到聊天缓存，使用返回的值唯一id来构造点击事件[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12419 | 使用12418返回的唯一id来读取一个聊天页面任务数据 | bidirectional | cs: srv_id:string; uniq_id:uint32 ／ sc: mission_bid:uint32; mission_status:uint8; commit_num:uint16; loop_count:uint16; loop_num:uint16; code:uint8; process_status:uint8; target:uint32; target_value:uint32; value:uint32; show_lave_time:uint8; lave_time:uint32; accept_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用12418返回的唯一id来读取一个聊天页面任务数据[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12420 | 英雄试炼发送PK角色名 | sc | cs: — ／ sc: name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄试炼发送PK角色名[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12421 | 已完成任务列表 | bidirectional | cs: — ／ sc: finish_task_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:已完成任务列表[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12422 | 提交物品,完成任务 | bidirectional | cs: mission_bid:uint32; item_list:table ／ sc: mission_bid:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交物品,完成任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12430 | 刷新任务品质 | bidirectional | cs: type:uint8 ／ sc: code:uint8; quantity:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新任务品质[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12431 | 获取护送相关数据 | bidirectional | cs: — ／ sc: bonus:table; cur_quantity:uint32; free_refresh_times:uint8; times:uint8; total_times:uint8; assist_times:uint8; total_assist_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取护送相关数据[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12432 | 进入下个场景 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入下个场景[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12433 | 护送完成 | sc | cs: — ／ sc: times:uint8; coin:uint32; exp:uint32; hero_exp:uint32; old_coin:uint32; old_exp:uint32; old_hero_exp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:护送完成[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12434 | 求助 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:求助[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12435 | 猜拳数据 | bidirectional | cs: — ／ sc: total_win:uint8; round:uint8; quality:uint8; team_win:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:猜拳数据[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12436 | 出拳 | bidirectional | cs: finger:uint8 ／ sc: rid:uint32; srv_id:string; role_finger:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:出拳[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12437 | 猜拳结束关闭界面 | sc | cs: — ／ sc: total_win:uint8; quality:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:猜拳结束关闭界面[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12438 | 猜拳回合结果 | sc | cs: — ／ sc: total_win:uint8; round:uint8; result:uint8; win_count:uint8; quality:uint8; sys_finger:uint8; team_win:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:猜拳回合结果[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12439 | 集字兑换 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:集字兑换[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12440 | 接取任务奖励的物品推送 | bidirectional | cs: — ／ sc: bid:uint32; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取任务奖励的物品推送[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12450 | 获取问题 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8; question_id:uint32; answer_id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取问题[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12451 | 回答问题 | bidirectional | cs: type:uint8; answer_id:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回答问题[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12452 | 回答问题发给对方 | sc | cs: — ／ sc: spouse_answer_id:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回答问题发给对方[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12460 | 接取循环任务 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取循环任务[cmd_table.json]；1.4.9文档载于task_protocol.md |
| 12499 | 获取任务当天已完成的次数 | bidirectional | cs: type:uint8 ／ sc: type:uint8; num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取任务当天已完成的次数[cmd_table.json]；1.4.9文档载于task_protocol.md |

### cmd_resolve_126.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12601 | 获取魔灵基础信息 | bidirectional | cs: — ／ sc: demon_list:table; demon_chip:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取魔灵基础信息[cmd_table.json] |
| 12602 | 请求单个魔灵基础数据 | bidirectional | cs: demon_bid:uint32 ／ sc: bid:uint32; career:uint8; star_lev:uint8; nature:uint8; chip:uint16; action_power:uint32; power:uint32; skill:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求单个魔灵基础数据[cmd_table.json] |
| 12603 | 魔灵升星 | bidirectional | cs: demon_bid:uint32 ／ sc: demon_bid:uint32; code:uint8; msg:string; skill_new:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:魔灵升星[cmd_table.json] |
| 12604 | 用魔灵碎片生成魔灵 | bidirectional | cs: demon_bid:uint32 ／ sc: bid:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:用魔灵碎片生成魔灵[cmd_table.json] |
| 12605 | 魔灵碎片更新 | sc | cs: — ／ sc: bid:uint32; chip_num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:魔灵碎片更新[cmd_table.json] |
| 12606 | 魔灵技能升级 | bidirectional | cs: demon_bid:uint32; skill_bid:uint32 ／ sc: code:uint8; msg:string; demon_bid:uint32; skill_bid:uint32; new_skill:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:魔灵技能升级[cmd_table.json] |

### cmd_resolve_127.luac（19 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12720 | 私聊 | bidirectional | cs: to_rid:uint32; to_srv_id:string; len:uint8; msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:私聊[cmd_table.json] |
| 12721 | 推送私聊 | bidirectional | cs: — ／ sc: flag:uint8; rid:uint32; srv_id:string; name:string; lev:uint8; career:uint16; face_id:uint16; len:uint8; msg:string; sex:uint8; vip_lev:uint8; capacity:uint8; head_bid:uint32; bubble_bid:uint32; tick:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:推送私聊[cmd_table.json] |
| 12722 | 登录推送离线消息 | bidirectional | cs: — ／ sc: offline_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:登录推送离线消息[cmd_table.json] |
| 12723 | 通知客户端已读消息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知客户端已读消息[cmd_table.json] |
| 12724 | 私聊通知类消息(服务端推送) | bidirectional | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:私聊通知类消息(服务端推送)[cmd_table.json] |
| 12725 | 语音信息 | bidirectional | cs: voice:bytes; voice_len:uint16; time:uint8; type:uint8 ／ sc: flag:uint8; srv_id:string; voice_id:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:语音信息[cmd_table.json] |
| 12726 | 请求语音缓存 | bidirectional | cs: srv_id:string; voice_id:uint32 ／ sc: srv_id:string; voice_id:uint32; time:uint8; voice:bytes; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求语音缓存[cmd_table.json] |
| 12741 | 提示信息 | sc | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提示信息[cmd_table.json] |
| 12742 | 提示获得资产/物品 | sc | cs: — ／ sc: asset_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提示获得资产/物品[cmd_table.json] |
| 12743 | 提示信息(并且在聊天框显示) | sc | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提示信息(并且在聊天框显示)[cmd_table.json] |
| 12744 | 弹框的提示信息 | sc | cs: — ／ sc: type:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:弹框的提示信息[cmd_table.json] |
| 12761 | 聊天协议；世界，场景，帮派，队伍，传闻，系统 | bidirectional | cs: — ／ sc: role_list:table; channel:uint16; len:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:聊天协议；世界，场景，帮派，队伍，传闻，系统[cmd_table.json] |
| 12762 | 发表聊天;成功不会返回 | bidirectional | cs: channel:uint16; len:uint8; msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:发表聊天;成功不会返回[cmd_table.json] |
| 12763 | 翻译分发;语音翻译1:世界;2:场景;4:帮派;8;队伍; | bidirectional | cs: — ／ sc: channel:uint16; id:string; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻译分发;语音翻译1:世界;2:场景;4:帮派;8;队伍;[cmd_table.json] |
| 12764 | 翻译;客户端请求分发翻译1:世界;2:场景;4:帮派;8;队伍; | bidirectional | cs: channel:uint16; id:string; msg:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻译;客户端请求分发翻译1:世界;2:场景;4:帮派;8;队伍;[cmd_table.json] |
| 12766 | 最近的几条聊天消息(帮派和队伍) | bidirectional | cs: channel:uint16 ／ sc: channel:uint16; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:最近的几条聊天消息(帮派和队伍)[cmd_table.json] |
| 12771 | 获取聊天玩家的队伍id | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; is_online:uint8; team_id:uint32; team_srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取聊天玩家的队伍id[cmd_table.json] |
| 12772 | 举报玩家 | bidirectional | cs: rid:uint32; srv_id:string; type:uint8; content:string; msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:举报玩家[cmd_table.json] |
| 12799 | 事件提示框 | sc | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:事件提示框[cmd_table.json] |

### cmd_resolve_128.luac（56 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12801 | 商城商品列表 | bidirectional | cs: — ／ sc: guild_shop_lev:uint32; xs_list:table | SYS_ECON_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:商城商品列表[cmd_table.json]；所属系统:Mall/Shop 商城[SYS_ECON_003][systems_master.json] |
| 12802 | 1、新增商品推，如果id没有，弹界面，插入列表里面；2、同步推（购买成功），如果xs_list为空，需要删除商品，否则，更新商品；3、商品超时客户端请求（需要在left_time加2秒，防死循环），如果xs_list为空，需要删除商品，否则，更新商品 | bidirectional | cs: — ／ sc: id:uint16; xs_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:1、新增商品推，如果id没有，弹界面，插入列表里面；2、同步推（购买成功），如果xs_list为空，需要删除商品，否则，更新商品；3、商品超时客户端请求（需要在left_time加2秒，防死循环），如果xs_list为空，需要删除商品，否则，更新商品[cmd_table.json] |
| 12803 | 元宝商城物品动态变化价格 | bidirectional | cs: — ／ sc: item_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:元宝商城物品动态变化价格[cmd_table.json] |
| 12805 | 买商城商品 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16; price:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:买商城商品[cmd_table.json] |
| 12821 | 买伙伴商店小伙伴 | bidirectional | cs: lev:uint8; bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:买伙伴商店小伙伴[cmd_table.json] |
| 12822 | 卖小伙伴 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32; bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:卖小伙伴[cmd_table.json] |
| 12823 | 小伙伴列表 | bidirectional | cs: lev:uint8 ／ sc: lev:uint8; huoban_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:小伙伴列表[cmd_table.json] |
| 12831 | 周商店，有购买的商品,没有买过的没有传 | bidirectional | cs: — ／ sc: id_list:table | SYS_ECON_010 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:周商店，有购买的商品,没有买过的没有传[cmd_table.json]；所属系统:Recharge/Payment 充值[SYS_ECON_010][systems_master.json] |
| 12832 | 买商城商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:买商城商品,需要根据返回值修正下数量[cmd_table.json] |
| 12836 | 限时商店，所有商品情况 | bidirectional | cs: — ／ sc: goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:限时商店，所有商品情况[cmd_table.json] |
| 12837 | 买商城商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:买商城商品,需要根据返回值修正下数量[cmd_table.json] |
| 12838 | 副本商店，所有商品情况 | bidirectional | cs: — ／ sc: goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本商店，所有商品情况[cmd_table.json] |
| 12839 | 买副本商店商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:买副本商店商品,需要根据返回值修正下数量[cmd_table.json] |
| 12840 | 兑换商店，所有商品情况 | bidirectional | cs: — ／ sc: goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:兑换商店，所有商品情况[cmd_table.json] |
| 12841 | 买兑换商店商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:买兑换商店商品,需要根据返回值修正下数量[cmd_table.json] |
| 12842 | 副本商店2，所有商品情况 | bidirectional | cs: — ／ sc: goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本商店2，所有商品情况[cmd_table.json] |
| 12843 | 买副本商店2商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:买副本商店2商品,需要根据返回值修正下数量[cmd_table.json] |
| 12853 | 伙伴神器商店，所有商品情况 | bidirectional | cs: — ／ sc: refresh_time:uint16; free_time:uint16; max_time:uint16; cost:uint16; count:uint8; limit_count:uint8; goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:伙伴神器商店，所有商品情况[cmd_table.json] |
| 12854 | 买商城商品,需要根据返回值修正下数量 | bidirectional | cs: id:uint16; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; buy_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:买商城商品,需要根据返回值修正下数量[cmd_table.json] |
| 12855 | 刷新伙伴神器商店商品列表 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新伙伴神器商店商品列表[cmd_table.json] |
| 12856 | 元宝兑换伙伴神器积分 | bidirectional | cs: — ／ sc: code:uint8; msg:string; count:uint8; limit_count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:元宝兑换伙伴神器积分[cmd_table.json] |
| 12804 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12804；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12806 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12806；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12807 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12807；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12808 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12808；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12809 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12809；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12810 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12810；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12811 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12811；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12812 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12812；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12813 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12813；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12814 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12814；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12815 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12815；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12816 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12816；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12817 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12817；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12818 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12818；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12819 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12819；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12820 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12820；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12824 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12824；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12825 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12825；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12826 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12826；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12827 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12827；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12828 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12828；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12829 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12829；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12830 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12830；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12833 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12833；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12834 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12834；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12835 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12835；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12844 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12844；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12845 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12845；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12846 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12846；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12847 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12847；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12848 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12848；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12849 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12849；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12850 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12850；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12851 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12851；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 12852 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_12852；引用系统: Mall/Shop 商城[SYS_ECON_003] |

### cmd_resolve_129.luac（44 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 12901 | 101综合战力；排名、性别、角色名、综合实力 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_role:table; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:101综合战力；排名、性别、角色名、综合实力[cmd_table.json] |
| 12902 | 102人物战力;排名、性别、角色名、职业、人物战力 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:102人物战力;排名、性别、角色名、职业、人物战力[cmd_table.json] |
| 12903 | 103英雄战力;排名、性别、角色名、职业、英雄战力 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; partner_bid:uint32; partner_color:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:103英雄战力;排名、性别、角色名、职业、英雄战力[cmd_table.json] |
| 12904 | 104角色等级;排名、性别、角色名、职业、等级 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:104角色等级;排名、性别、角色名、职业、等级[cmd_table.json] |
| 12911 | 201勇气榜;排名、性别、角色名、职业、等级 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:201勇气榜;排名、性别、角色名、职业、等级[cmd_table.json] |
| 12912 | 202魅力榜;排名、性别、角色名、职业、等级 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:202魅力榜;排名、性别、角色名、职业、等级[cmd_table.json] |
| 12913 | 401门派榜;排名、角色名、星级、通关时间 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:401门派榜;排名、角色名、星级、通关时间[cmd_table.json] |
| 12914 | 105坐骑排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_ride_jie:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:105坐骑排行[cmd_table.json] |
| 12915 | 106仙灵排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_lingshou_jie:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:106仙灵排行[cmd_table.json] |
| 12916 | 107翅膀排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_wing_color:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:107翅膀排行[cmd_table.json] |
| 12917 | 108修炼技能等级排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:108修炼技能等级排行[cmd_table.json] |
| 12918 | 501帮会排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_g_name:string; my_head_name:string; my_g_num:uint16; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:501帮会排行[cmd_table.json] |
| 12919 | 102段位排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_win_num:uint16; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:102段位排行[cmd_table.json] |
| 12920 | 109成就排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:109成就排行[cmd_table.json] |
| 12921 | 110神器排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_shenqi_bid:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:110神器排行[cmd_table.json] |
| 12922 | 111南天门排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:111南天门排行[cmd_table.json] |
| 12923 | 112强化等级排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:112强化等级排行[cmd_table.json] |
| 12924 | 601跨服进程值排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:601跨服进程值排行[cmd_table.json] |
| 12925 | 宝贝榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝贝榜[cmd_table.json] |
| 12926 | 情圣榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:情圣榜[cmd_table.json] |
| 12927 | 坐骑进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_ride_jie:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑进阶丹消耗排行[cmd_table.json] |
| 12928 | 仙灵进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_jie:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙灵进阶丹消耗排行[cmd_table.json] |
| 12929 | 聚宝盆次数排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:聚宝盆次数排行[cmd_table.json] |
| 12930 | 神器注灵消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:神器注灵消耗排行[cmd_table.json] |
| 12931 | 301竞技场积分;排名、性别、角色名、职业、等级 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:301竞技场积分;排名、性别、角色名、职业、等级[cmd_table.json] |
| 12932 | 法宝战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_fabao_list:table; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝战力排行榜[cmd_table.json] |
| 12933 | 光环进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:光环进阶丹消耗排行[cmd_table.json] |
| 12934 | 光环战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_hero_bid:uint32; grow:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:光环战力排行榜[cmd_table.json] |
| 12971 | 请求角色信息 | bidirectional | cs: type:uint16; rid:uint32; srv_id:string; flag:uint8 ／ sc: type:uint16; rid:uint32; srv_id:string; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求角色信息[cmd_table.json] |
| 12972 | 请求英雄信息 | bidirectional | cs: type:uint16; rid:uint32; srv_id:string; flag:uint8 ／ sc: type:uint16; rid:uint32; srv_id:string; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求英雄信息[cmd_table.json] |
| 12973 | 单人无尽试炼排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; partner_list:table; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单人无尽试炼排行榜[cmd_table.json] |
| 12974 | 单人无尽排行榜伙伴数据 | bidirectional | cs: rid:uint32; srv_id:string; bid:uint32 ／ sc: ord:uint16; rid:uint32; srv_id:string; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单人无尽排行榜伙伴数据[cmd_table.json] |
| 12977 | 强化积分活动排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:强化积分活动排行[cmd_table.json] |
| 12978 | 累计充值活动排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:累计充值活动排行[cmd_table.json] |
| 12979 | 累计消费活动排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:累计消费活动排行[cmd_table.json] |
| 12980 | 封魔录副本排行 | bidirectional | cs: bid:uint32; ord:uint8; num:uint8; flag:uint8 ／ sc: bid:uint32; my_ord:uint8; my_val:uint8; my_sec:uint32; my_team_member:table; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:封魔录副本排行[cmd_table.json] |
| 12986 | 命格战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_mingge_stage:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格战力排行榜[cmd_table.json] |
| 12988 | 伙伴积分排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴积分排行榜[cmd_table.json] |
| 12994 | 情缘积分排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint16; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:情缘积分排行[cmd_table.json] |
| 12995 | 送花榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:送花榜[cmd_table.json] |
| 12996 | 位面探宝排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:位面探宝排行榜[cmd_table.json] |
| 12997 | 鲜花榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:鲜花榜[cmd_table.json] |
| 12998 | 婚戒战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_ring_lev:uint8; my_ring_star:uint16; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:婚戒战力排行榜[cmd_table.json] |
| 12999 | 魂骨进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:魂骨进阶丹消耗排行[cmd_table.json] |

### cmd_resolve_130.luac（88 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13000 | 进入副本 | bidirectional | cs: dung_bid:uint32 ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入副本[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13001 | 退出副本 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出副本[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13002 | 副本进度 | sc | cs: — ／ sc: use_time:uint32; task_all:uint8; task_process_cur:uint8; task_tips:string; task_type:uint8; arg_list:table; cur_task_num:uint8; has_time_limit:uint8; task_time_limit:uint32; time_limit:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本进度[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13003 | 副本成功 | sc | cs: — ／ sc: bid:uint16; star:uint8; min_round:uint8; max_round:uint8; time:uint16; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本成功[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13004 | 购买副本进入次数 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; count:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:购买副本进入次数[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13005 | 请求副本相关类型次数 | bidirectional | cs: bid:uint32; flag:uint8 ／ sc: bid:uint32; flag:uint8; left_times:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求副本相关类型次数[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13007 | 副本剩余时间 | sc | cs: — ／ sc: bid:uint32; left_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本剩余时间[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13008 | 最高章节 | bidirectional | cs: — ／ sc: chapter_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:最高章节[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13010 | 获取所有通关的副本ID | bidirectional | cs: — ／ sc: bids:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取所有通关的副本ID[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13011 | 所有开启章节的星级情况 | bidirectional | cs: — ／ sc: chapter_star:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:所有开启章节的星级情况[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13012 | 获取章节星级奖励 | bidirectional | cs: chapter_id:uint32; flag:uint8; star:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取章节星级奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13013 | 章节星级更新 | sc | cs: — ／ sc: chapter_bid:uint32; flag:uint8; star:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:章节星级更新[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13015 | 获取章节奖励领取情况 | bidirectional | cs: — ／ sc: chapter_reward:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取章节奖励领取情况[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13016 | 副本挑战失败 | sc | cs: — ／ sc: bid:uint32; flag:uint8; min_round:uint8; max_round:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本挑战失败[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13017 | 获取战力输出 | bidirectional | cs: — ／ sc: bid:uint32; role_out:table; hero_out:table; mon_out:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取战力输出[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13018 | 翻牌 | bidirectional | cs: floor:uint8; pos:uint8 ／ sc: code:uint8; msg:string; pos:uint8; count:uint8; items:table; all:uint8; items_other:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻牌[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13019 | 翻牌发给其他队员 | sc | cs: — ／ sc: pos:uint8; member_id:uint32; member_srv_id:string; member_name:string; items:table; all:uint8; items_other:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻牌发给其他队员[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13020 | 进入副本,带参数 | bidirectional | cs: dung_bid:uint32; args:table ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入副本,带参数[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13021 | 重置英雄试炼副本 | bidirectional | cs: dung_bid:uint32; arg:uint8 ／ sc: tips:int8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重置英雄试炼副本[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13022 | 极地寻宝统计信息 | bidirectional | cs: — ／ sc: section:uint8; challenge:uint8; hard:uint8; assets:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:极地寻宝统计信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13023 | 英雄试炼发送宝箱奖励 | sc | cs: — ／ sc: gain:table; items:table; vip_gain:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄试炼发送宝箱奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13024 | 英雄试炼关卡信息 | sc | cs: — ／ sc: level:uint8; pk_id:uint32; pk_srv_id:string; mon_bid:uint32; pk_name:string; pk_lev:uint8; pk_career:uint8; pk_sex:uint8; pk_power:uint8; pk_status:uint8; gain:table; items:table; hard:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄试炼关卡信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13025 | 真火封印弹出复活框 | sc | cs: — ／ sc: Bid:uint32; Count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印弹出复活框[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13026 | 失败界面选择 | bidirectional | cs: Bid:uint32; select:uint8 ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:失败界面选择[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13027 | 等级副本结算界面 | sc | cs: — ／ sc: bid:uint32; arg:uint16; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:等级副本结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13028 | 副本开启 | bidirectional | cs: — ／ sc: count:uint8; dung_list:table | SYS_DUNGEON_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本开启[cmd_table.json]；所属系统:Dungeon 副本[SYS_DUNGEON_001][systems_master.json]；1.4.9文档载于battle_protocol.md |
| 13029 | 真火封印副本每一波获取总奖励 | sc | cs: — ／ sc: bid:uint32; round:uint16; star:uint16; score:uint16; gain:table; items:table; effect_type_per:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印副本每一波获取总奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13030 | 鹰愁涧副本倒计时 | sc | cs: — ／ sc: flag:int16; time:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:鹰愁涧副本倒计时[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13031 | 鹰愁涧副本波数和NPC当前血量 | sc | cs: — ／ sc: bid:uint32; round_num:uint8; cur_hp:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:鹰愁涧副本波数和NPC当前血量[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13032 | 镇妖塔副本每层侧边数据协议 | sc | cs: — ／ sc: dung_bid:uint32; floor:uint8; BossList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:镇妖塔副本每层侧边数据协议[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13033 | 副本每层结算界面 | sc | cs: — ／ sc: floor:uint8; round:int16; time:uint16; rank:uint8; output:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本每层结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13034 | 镇妖塔通关的层列表 | bidirectional | cs: dung_bid:uint32 ／ sc: dung_bid:uint32; CengList:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:镇妖塔通关的层列表[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13035 | 镇妖塔每层排行榜,取前3 | bidirectional | cs: dung_bid:uint32; ceng:uint8 ／ sc: team_list:table | SYS_DUNGEON_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:镇妖塔每层排行榜,取前3[cmd_table.json]；所属系统:Tower 塔[SYS_DUNGEON_003][systems_master.json]；1.4.9文档载于battle_protocol.md |
| 13036 | 镇妖塔操作,队长操作发给队员 | bidirectional | cs: dung_bid:uint32; key:uint8; value:uint8 ／ sc: key:uint8; value:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:镇妖塔操作,队长操作发给队员[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13037 | 镇妖塔领取宝箱奖励 | bidirectional | cs: Bid:uint32; ceng:uint8 ／ sc: Bid:uint32; ceng:uint8; tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:镇妖塔领取宝箱奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13038 | 镇妖塔获取录像Id | bidirectional | cs: Bid:uint32; ceng:uint8 ／ sc: record_str:string | SYS_DUNGEON_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:镇妖塔获取录像Id[cmd_table.json]；所属系统:Tower 塔[SYS_DUNGEON_003][systems_master.json]；1.4.9文档载于battle_protocol.md |
| 13039 | 上线进入副本发送Bid | sc | cs: — ／ sc: Bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上线进入副本发送Bid[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13040 | 进入副本发送怪物信息 | sc | cs: — ／ sc: Bid:uint32; MonList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入副本发送怪物信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13041 | 怪物死亡发送信息 | sc | cs: — ／ sc: mon_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:怪物死亡发送信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13042 | 单人塔副本相关信息 | bidirectional | cs: — ／ sc: high_floor:uint32; ceng_list:table; status:uint8; cur_ceng:uint8; left_time:uint32; clear_list:table; count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:单人塔副本相关信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13043 | 重置单人塔副本 | bidirectional | cs: — ／ sc: tips:uint16; msg:string; count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重置单人塔副本[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13044 | 副本扫荡 | bidirectional | cs: Bid:uint32 ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13045 | 无底洞副本每层相关信息 | bidirectional | cs: floor:uint32 ／ sc: floor:uint32; rid:uint32; srv_id:string; name:string; fast_rid:uint32; fast_srv_id:string; fast_name:string; first_get:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:无底洞副本每层相关信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13046 | 无底洞副本每层侧边数据协议 | sc | cs: — ／ sc: dung_bid:uint32; floor:uint8; BossList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:无底洞副本每层侧边数据协议[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13047 | 副本相应层开始扫荡 | sc | cs: — ／ sc: floor:uint8; left_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本相应层开始扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13048 | 副本相应层扫荡完毕 | sc | cs: — ／ sc: floor:uint8; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本相应层扫荡完毕[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13049 | 单人塔副本发送结算界面 | sc | cs: — ／ sc: floor:uint8; gain:table; items:table; first_items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单人塔副本发送结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13050 | 无底洞进入下一层 | cs | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:无底洞进入下一层[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13051 | 结束扫荡 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结束扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13052 | 英雄试炼获取界面相关信息 | bidirectional | cs: — ／ sc: select_hard:uint8; section:uint8; hard:uint8; challenge:uint8; left_times:uint8; assets:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:英雄试炼获取界面相关信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13053 | 副本免cd扫荡 | sc | cs: — ／ sc: FloorAwardList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本免cd扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13054 | 真火封印,选择效果显示 | sc | cs: — ／ sc: star:uint32; EffectList:table; effect_type_per:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印,选择效果显示[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13055 | 真火封印,效果选择 | bidirectional | cs: EffectId:uint32 ／ sc: tips:uint16; msg:string; star:uint32; effect_type_per:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印,效果选择[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13056 | 真火封印副本结算界面 | sc | cs: — ／ sc: bid:uint32; score:uint32; max_wave:uint8; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印副本结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13057 | 真火封印,领取奖励 | bidirectional | cs: bid:uint32 ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印,领取奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13058 | 真火封印面板 | bidirectional | cs: bid:uint32 ／ sc: cur_score:uint32; get_score:uint32; max_wave:uint8; gain:table; AwardBidList:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:真火封印面板[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13059 | 真火封印,难度显示 | sc | cs: — ／ sc: bid:uint32; round:uint32; star:uint32; hard_boss:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印,难度显示[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13060 | 真火封印,每一波难度选择 | bidirectional | cs: bid:uint32; round:uint32; hard:uint8 ／ sc: tips:uint16; msg:string; round:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:真火封印,每一波难度选择[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13061 | 鹰愁涧最大波 | bidirectional | cs: — ／ sc: wave:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:鹰愁涧最大波[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13062 | 南天门领取首次奖励 | bidirectional | cs: ceng:uint8 ／ sc: tips:uint16; msg:string; ceng:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:南天门领取首次奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13065 | 玄武门获取问题 | sc | cs: — ／ sc: npc_bid:uint32; question_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玄武门获取问题[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13066 | 玄武门回答问题 | bidirectional | cs: npc_bid:uint32; question_id:uint32; answer_id:uint32 ／ sc: npc_bid:uint32; answer_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玄武门回答问题[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13067 | 答题关闭面板,附带信息显示 | sc | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题关闭面板,附带信息显示[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13068 | npc答题状态和boss信息 | sc | cs: — ／ sc: dung_bid:uint32; npc_status:table; mons:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:npc答题状态和boss信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13069 | 白虎门推送诗词id | sc | cs: — ／ sc: dung_bid:uint32; cur_round:uint8; vese_id:uint32; verse_status:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:白虎门推送诗词id[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13070 | 白虎门杀怪错误 | sc | cs: — ／ sc: npc_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:白虎门杀怪错误[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13071 | 朱雀门信息 | sc | cs: — ／ sc: dung_bid:uint32; box_num:uint8; open_box_num:uint8; boss_bid:uint32; num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:朱雀门信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13072 | 青龙门信息 | sc | cs: — ／ sc: dung_bid:uint32; mon_status:table; boss_bid:uint32; num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:青龙门信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13073 | 四门绝阵次数信息 | bidirectional | cs: — ／ sc: floor_count:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:四门绝阵次数信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13074 | 四门绝阵问题求助 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:四门绝阵问题求助[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13075 | 四门绝阵问题援助 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:四门绝阵问题援助[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13076 | 四门绝阵问题答案查看 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:四门绝阵问题答案查看[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13079 | 购买vip单人副本次数 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; enter_count:uint16; buy_count:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买vip单人副本次数[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13080 | vip单人副本次数信息 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip单人副本次数信息[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13081 | vip单人副本结算界面 | sc | cs: — ／ sc: bid:uint32; gain:table; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip单人副本结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13082 | vip单人副本开始扫荡 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string; time:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip单人副本开始扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13083 | vip单人副本加速扫荡 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip单人副本加速扫荡[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13084 | 佣兵无尽试炼面板 | bidirectional | cs: — ／ sc: max_wave:uint16; rank:uint16; partner_list:table; goods_index:uint16; goods_flag:uint8; max_passed:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:佣兵无尽试炼面板[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13085 | 佣兵无尽试炼排行榜 | bidirectional | cs: type:uint8; start_rank:uint16; end_rank:uint16 ／ sc: type:uint8; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:佣兵无尽试炼排行榜[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13086 | 佣兵无尽试炼开始挑战 | bidirectional | cs: partner_list:table; rid:uint32; srv_id:string; partner_id:uint32 ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:佣兵无尽试炼开始挑战[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13087 | 推送战斗波数 | bidirectional | cs: — ／ sc: wave:uint16; rank:uint16; per_name:string; per_wave:uint16; assets:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送战斗波数[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13088 | 佣兵无尽试炼战斗结束 | bidirectional | cs: — ／ sc: wave:uint16; rank:uint16; add_rank:int16; assets:table; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:佣兵无尽试炼战斗结束[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13094 | 困神塔副本每层侧边数据协议 | sc | cs: — ／ sc: dung_bid:uint32; floor:uint8; BossList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:困神塔副本每层侧边数据协议[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13095 | 困神塔副本每层结算界面 | sc | cs: — ／ sc: floor:uint8; round:int16; time:uint16; rank:uint8; output:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:困神塔副本每层结算界面[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13096 | 困神塔每层排行榜,取前3 | bidirectional | cs: dung_bid:uint32; ceng:uint8 ／ sc: team_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:困神塔每层排行榜,取前3[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13097 | 困神塔通关的层列表 | bidirectional | cs: dung_bid:uint32 ／ sc: dung_bid:uint32; CengList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:困神塔通关的层列表[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13098 | 困神塔领取宝箱奖励 | bidirectional | cs: Bid:uint32; ceng:uint8 ／ sc: Bid:uint32; ceng:uint8; tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:困神塔领取宝箱奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 13099 | 结义副本每层侧边数据协议 | sc | cs: — ／ sc: dung_bid:uint32; floor:uint8; time_out:uint32; ElemList:table; MonList:table; BossList:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结义副本每层侧边数据协议[cmd_table.json]；1.4.9文档载于battle_protocol.md |

### cmd_resolve_131.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13100 | UNKNOWN | bidirectional | cs: — ／ sc: f_lev:uint8; hero_list:table; f_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 13101 | UNKNOWN | bidirectional | cs: type:uint8; pos:uint8; hero_bid:uint32 ／ sc: tips:uint16; msg:string; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 13102 | UNKNOWN | bidirectional | cs: type:uint8; pos:uint8; hero_bid:uint32 ／ sc: tips:uint16; msg:string; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 13103 | UNKNOWN | bidirectional | cs: — ／ sc: tips:uint16; msg:string; f_lev:uint8; f_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 13104 | UNKNOWN | bidirectional | cs: type:uint8 ／ sc: tips:uint16; msg:string; s_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 13105 | UNKNOWN | bidirectional | cs: — ／ sc: experience:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | UNKNOWN |

### cmd_resolve_132.luac（45 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13200 | 队伍信息 | bidirectional | cs: — ／ sc: msg:string; team_id:uint32; team_srv_id:string; leader_id:uint32; leader_srv_id:string; leader_speed:uint32; team_member_list:table | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:队伍信息[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13201 | 创建队伍 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:创建队伍[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13202 | 邀请进队 | bidirectional | cs: member_id:uint32; member_srv_id:string ／ sc: tips:uint16; msg:string | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:邀请进队[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13203 | 组队发送到被邀请人 | sc | cs: — ／ sc: leader_id:uint32; leader_srv_id:string; leader_name:string; leader_lev:uint8; leader_career:uint8; team_id:uint32; team_srv_id:string; team_num:uint8; team_max_num:uint8; invite_flag:uint8 | SYS_MAP_002 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:组队发送到被邀请人[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13204 | 队长同意申请 | bidirectional | cs: is_ok:uint8; ok_id:uint32; ok_srv_id:string ／ sc: tips:uint8; msg:string; id:uint32; srv_id:string | SYS_MAP_002 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队长同意申请[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13205 | 同意邀请 | bidirectional | cs: is_ok:uint8; team_id:uint32; team_srv_id:string; invite_flag:uint8; member_id:uint32; member_srv_id:string ／ sc: tips:uint8; msg:string; team_id:uint32; team_srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:同意邀请[cmd_table.json] |
| 13206 | 申请入队 | bidirectional | cs: team_id:uint32; team_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:申请入队[cmd_table.json] |
| 13207 | 队长获取申请列表 | bidirectional | cs: — ／ sc: apply_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队长获取申请列表[cmd_table.json] |
| 13208 | 申请入队人员发给队长,此由服务端转发 | sc | cs: — ／ sc: apply_id:uint32; apply_srv_id:string; apply_name:string; apply_lev:uint8; apply_career:uint16; apply_power:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:申请入队人员发给队长,此由服务端转发[cmd_table.json] |
| 13209 | 任命队长 | bidirectional | cs: member_id:uint32; member_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:任命队长[cmd_table.json] |
| 13210 | 退出队伍 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:退出队伍[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13211 | 踢出队员 | bidirectional | cs: member_id:uint32; member_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:踢出队员[cmd_table.json] |
| 13212 | 踢出队员发送给被踢出人 | sc | cs: — ／ sc: member_id:uint32; member_srv_id:string; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:踢出队员发送给被踢出人[cmd_table.json] |
| 13213 | 暂离 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:暂离[cmd_table.json] |
| 13214 | 召回 | bidirectional | cs: member_id:uint32; member_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:召回[cmd_table.json] |
| 13215 | 召回发送给暂离队员 | sc | cs: — ／ sc: leader_id:uint32; leader_srv_id:string; leader_name:string; map_bid:uint32; map_x:uint16; map_y:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:召回发送给暂离队员[cmd_table.json] |
| 13216 | 队员发送召回结果 | bidirectional | cs: member_id:uint32; member_srv_id:string; flag:uint8; send_flag:uint8 ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队员发送召回结果[cmd_table.json] |
| 13217 | 队员归队 | bidirectional | cs: member_id:uint32; member_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队员归队[cmd_table.json] |
| 13218 | 组队大厅所有队伍 | bidirectional | cs: — ／ sc: team_list:table | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:组队大厅所有队伍[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13219 | 队伍招募列表 | bidirectional | cs: flag:uint8 ／ sc: tips:uint8; msg:string; flag:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍招募列表[cmd_table.json] |
| 13220 | 一键招募 | bidirectional | cs: flag:uint8; role_list:table ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键招募[cmd_table.json] |
| 13221 | 任命暂离队员为队长,信息发送给正常队员 | sc | cs: — ／ sc: role_id:uint32; role_srv_id:string; role_name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:任命暂离队员为队长,信息发送给正常队员[cmd_table.json] |
| 13223 | 发布招募 | bidirectional | cs: purpose:uint8; arg:uint32; min_lev:uint8; max_lev:uint8; leader_new:uint8 ／ sc: tips:uint8; msg:string; purpose:uint8; arg:uint32; min_lev:uint8; max_lev:uint8; leader_new:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发布招募[cmd_table.json] |
| 13224 | 快速组队 | bidirectional | cs: p_list:table; min_lev:uint8; max_lev:uint8; team_id:uint32; team_srv_id:string ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:快速组队[cmd_table.json] |
| 13225 | 取消快速组队 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消快速组队[cmd_table.json] |
| 13226 | 解散队伍 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:解散队伍[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13227 | 快速组队排队队伍和排队人数 | bidirectional | cs: p_list:table ／ sc: team_num:uint16; role_num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:快速组队排队队伍和排队人数[cmd_table.json] |
| 13228 | 取消队伍发布招募 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消队伍发布招募[cmd_table.json] |
| 13229 | 组队玩法进行确认 | bidirectional | cs: type:uint8; arg_list:table ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:组队玩法进行确认[cmd_table.json] |
| 13230 | 组队玩法确认发给队员 | sc | cs: — ／ sc: type:uint8; time:uint8; count:uint8; arg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:组队玩法确认发给队员[cmd_table.json] |
| 13231 | 队员确认 | bidirectional | cs: flag:uint8; type:uint8; arg_list:table ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队员确认[cmd_table.json] |
| 13232 | 队员确认发给队长 | sc | cs: — ／ sc: name:string; flag:uint8; type:uint8; arg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队员确认发给队长[cmd_table.json] |
| 13233 | 队伍人数满,发给队长前往目的地提示 | sc | cs: — ／ sc: purpose:uint8; arg:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍人数满,发给队长前往目的地提示[cmd_table.json] |
| 13234 | 队伍发布招募,当打开面板时返回的快速组队排队队员申请列表 | bidirectional | cs: purpose:uint8; arg:uint32 ／ sc: code:uint8; member_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍发布招募,当打开面板时返回的快速组队排队队员申请列表[cmd_table.json] |
| 13235 | 队长操作发给队员 | bidirectional | cs: type:uint8; key:uint8; value:uint8 ／ sc: type:uint8; key:uint8; value:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队长操作发给队员[cmd_table.json] |
| 13236 | 队伍满员发送匹配提示 | sc | cs: — ／ sc: purpose:uint8; arg:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍满员发送匹配提示[cmd_table.json] |
| 13237 | 查看其它玩家队伍信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: team_id:uint32; team_srv_id:string; num:uint8; gid:uint32; gsrv:string; gname:string | SYS_MAP_002 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看其它玩家队伍信息[cmd_table.json]；所属系统:Team Group 组队[SYS_MAP_002][systems_master.json] |
| 13238 | 队伍喊话 | bidirectional | cs: code:uint16; purpose:uint8; arg:uint32; min_lev:uint8; max_lev:uint8; leader_new:uint8 ／ sc: tips:uint8; msg:string; time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍喊话[cmd_table.json] |
| 13250 | 获取组队阵法信息 | bidirectional | cs: — ／ sc: select_type:uint8; info_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取组队阵法信息[cmd_table.json] |
| 13251 | 设置阵位 | bidirectional | cs: type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置阵位[cmd_table.json] |
| 13253 | 队伍选中某个阵法 | bidirectional | cs: type:uint8 ／ sc: tips:uint16; msg:string; s_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队伍选中某个阵法[cmd_table.json] |
| 13254 | 一键上阵 | bidirectional | cs: — ／ sc: f_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键上阵[cmd_table.json] |
| 13256 | 发起替换队长 | bidirectional | cs: — ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发起替换队长[cmd_table.json] |
| 13257 | 顶替队长投票开始 | sc | cs: — ／ sc: tips:uint8; msg:string; rid:uint32; srv_id:string; name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:顶替队长投票开始[cmd_table.json] |
| 13258 | 投票顶替队长 | bidirectional | cs: type:uint8 ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:投票顶替队长[cmd_table.json] |

### cmd_resolve_133.luac（62 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13300 | 获取好友列表信息 | bidirectional | cs: — ／ sc: friend_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取好友列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13301 | 告诉客户端某玩家上线 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:告诉客户端某玩家上线[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13302 | 告诉客户端某玩家下线 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:告诉客户端某玩家下线[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13303 | 请求加好友;A向服务端请求想加B为好友;会返回消息告诉A这次请求是否成功 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求加好友;A向服务端请求想加B为好友;会返回消息告诉A这次请求是否成功[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13304 | 服务端告诉客户端;A想加B为好友 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; sex:uint8; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:服务端告诉客户端;A想加B为好友[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13305 | B告诉服务端，加或不加A为好友;服务端会告诉B这次结果怎么样 | bidirectional | cs: rid:uint32; srv_id:string; agreed:uint8 ／ sc: rid:uint32; srv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:B告诉服务端，加或不加A为好友;服务端会告诉B这次结果怎么样[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13306 | 批量加好友 | bidirectional | cs: role_list:table ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:批量加好友[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13307 | 主动删除好友;需要客户端把好友删除 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:主动删除好友;需要客户端把好友删除[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13308 | 被动删除好友 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被动删除好友[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13309 | 批量删除 | bidirectional | cs: del_list:table ／ sc: del_list2:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:批量删除[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13310 | 赠送体力给好友 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送体力给好友[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13311 | 查询赠送体力列表 | bidirectional | cs: — ／ sc: all_give_times:uint8; all_award_times:uint8; give_times:uint8; award_times:uint8; give_list:table; be_give_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询赠送体力列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13312 | 通知玩家收到体力 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; spirit:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知玩家收到体力[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13313 | 领取玩家收到的体力 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取玩家收到的体力[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13314 | 查询好友信息 | bidirectional | cs: name:string ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询好友信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13315 | 赠送物品 | bidirectional | cs: rid:uint32; srv_id:string; send_list:table ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送物品[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13316 | 分组列表信息 | bidirectional | cs: — ／ sc: group_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分组列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13317 | 创建分组 | bidirectional | cs: group_name:string ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:创建分组[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13318 | 删除分组 | bidirectional | cs: group_id:uint32 ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除分组[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13319 | 移动好友 | bidirectional | cs: rid:uint32; srv_id:string; old_group_id:uint32; new_group_id:uint32 ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:移动好友[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13320 | 好友推荐 | bidirectional | cs: — ／ sc: recommend_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:好友推荐[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13321 | 获取好友申请列表信息 | bidirectional | cs: — ／ sc: request_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取好友申请列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 13322 | 增加的好友列表信息 | bidirectional | cs: — ／ sc: add_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:增加的好友列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13323 | 一键清空好友申请 | bidirectional | cs: — ／ sc: code:uint8; string:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键清空好友申请[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13324 | 赠送鲜花 | bidirectional | cs: rid:uint32; srv_id:string; bid:uint32; num:uint32; auto_buy:uint8; msg:string ／ sc: code:uint8; string:string; bid:uint32; num:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送鲜花[cmd_table.json]；1.4.9文档载于dungeon_protocol.md；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 13325 | 赠送物品的面板 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; give_times:uint32; all_times:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送物品的面板[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13326 | 赠送鲜花的面板 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; name:string; career:uint16; is_online:uint8; courage:uint32; charm:uint32; send_num:uint32; send_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送鲜花的面板[cmd_table.json]；1.4.9文档载于dungeon_protocol.md；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 13328 | 送花送成功,服务端推送 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; career:uint16; b_rid:uint32; b_srv_id:string; b_name:string; b_career:uint16; item_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:送花送成功,服务端推送[cmd_table.json]；1.4.9文档载于dungeon_protocol.md；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 13331 | 获取本人的勇气值和魅力值 | bidirectional | cs: — ／ sc: courage:uint32; charm:uint32; courage_rank:uint8; charm_rank:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取本人的勇气值和魅力值[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13336 | 获取本人的勇气值和魅力值 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; intimacy:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取本人的勇气值和魅力值[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13340 | 打开空间界面 | bidirectional | cs: — ／ sc: name:string; lev:uint8; career:uint8; sex:uint8; sign:string; guild_name:string; title:string; spouse_name:string; per_name:string; zone:string; city:string; gift_num:uint16; nice_num:uint32; flower:uint32; new_msg:uint8; zone_skin:uint16; head_skin:uint16; use_badge_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开空间界面[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13341 | 请求自己好友状态 | bidirectional | cs: ord:uint8; max_len:uint8 ／ sc: ord:uint8; max_len:uint8; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求自己好友状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13342 | 查看好友状态 | bidirectional | cs: rid:uint32; srv_id:string; ord:uint8; max_len:uint8 ／ sc: code:uint8; msg:string; ord:uint8; max_len:uint8; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看好友状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13343 | 发表状态 | bidirectional | cs: content:string; friend_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:发表状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13344 | 发表评论 | bidirectional | cs: rid:uint32; srv_id:string; index:uint32; type:uint8; to_rid:uint32; to_srv_id:string; to_name:string; comment:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; comment_num:uint8; comment_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发表评论[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13345 | 删除状态 | bidirectional | cs: index:uint32; srv_id:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13346 | 删除评论 | bidirectional | cs: rid:uint32; srv_id:string; index:uint32; say_rid:uint32; say_srv_id:string; say_ctime:uint32 ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; say_rid:uint32; say_srv_id:string; say_ctime:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除评论[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13347 | 点赞状态 | bidirectional | cs: rid:uint32; srv_id:string; index:uint32 ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; nice_num:uint8; nice_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:点赞状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13348 | 取消点赞 | bidirectional | cs: rid:uint32; srv_id:string; index:uint32 ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; index:uint32; nice_num:uint8; nice_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消点赞[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13349 | 查看好友空间 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; name:string; lev:uint8; career:uint8; sex:uint8; sign:string; guild_name:string; title:string; spouse_name:string; per_name:string; zone:string; city:string; gift_num:uint16; nice_num:uint32; flower:uint32; is_nice:uint8; zone_skin:uint16; head_skin:uint16; use_badge_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看好友空间[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13350 | 点赞空间 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; nice_num:uint32; gift_num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:点赞空间[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13351 | 增加空间礼物 | bidirectional | cs: num:uint16 ／ sc: code:uint8; msg:string; gift_num:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:增加空间礼物[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13352 | 获取空间足迹（点赞过自己空间的玩家） | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取空间足迹（点赞过自己空间的玩家）[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13353 | 获取空间送花历史 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取空间送花历史[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13354 | 获取空间人气排行榜 | bidirectional | cs: type:uint8; ord:uint8; max_len:uint8 ／ sc: type:uint8; ord:uint8; max_len:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取空间人气排行榜[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13355 | 获取新消息列表 | bidirectional | cs: — ／ sc: code:uint8; msg:string; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取新消息列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13356 | 查看新消息 | bidirectional | cs: rid:uint32; srv_id:string; index:uint32; msg_rid:uint32; msg_srv_id:string; ctime:uint32 ／ sc: code:uint8; msg:string; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看新消息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13357 | 删除新消息 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除新消息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13358 | 查看空间伙伴 | bidirectional | cs: rid:uint32; srv_id:string; partner_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看空间伙伴[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13359 | 修改个性签名 | bidirectional | cs: content:string ／ sc: code:uint8; msg:string; content:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:修改个性签名[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13360 | 设置所在 | bidirectional | cs: town:string; city:string ／ sc: code:uint8; msg:string; town:string; city:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置所在[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13361 | 获取已获得的外框 | bidirectional | cs: — ／ sc: zone_list:table; head_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取已获得的外框[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13362 | 购买外框 | bidirectional | cs: bid:uint16 ／ sc: code:uint8; msg:string; bid:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买外框[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13363 | 使用外框 | bidirectional | cs: type:uint8; bid:uint16 ／ sc: code:uint8; msg:string; type:uint8; bid:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用外框[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13364 | 获取已使用的徽章 | bidirectional | cs: — ／ sc: use_badge_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取已使用的徽章[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13365 | 获取已激活的徽章列表 | bidirectional | cs: — ／ sc: act_badge_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取已激活的徽章列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13366 | 使用/撤下徽章 | bidirectional | cs: bid_list:table ／ sc: code:uint8; msg:string; bid_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用/撤下徽章[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13367 | 投诉 | bidirectional | cs: type:uint8; index:uint32; rid:uint32; srv_id:string; name:string; reason:string; desc:string; content:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:投诉[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13368 | 分享 | bidirectional | cs: channel:uint16; len:uint8; msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分享[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13369 | 获取黑名单列表信息 | bidirectional | cs: — ／ sc: black_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取黑名单列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13370 | 拉黑 | bidirectional | cs: rid:uint32; srv_id:string; op_type:uint8 ／ sc: code:uint32; msg:string; rid:uint32; srv_id:string; op_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:拉黑[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13371 | 增加的黑名单列表信息 | bidirectional | cs: — ／ sc: add_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:增加的黑名单列表信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |

### cmd_resolve_134.luac（16 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13401 | 兑换商店商品当天购买数量 | bidirectional | cs: type:uint8 ／ sc: type:uint8; buy_list:table | SYS_ECON_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:兑换商店商品当天购买数量[cmd_table.json]；所属系统:Mall/Shop 商城[SYS_ECON_003][systems_master.json] |
| 13402 | 兑换商店购买商品 | bidirectional | cs: id:uint16; num:uint16 ／ sc: id:uint16; type:uint8; buy_num:uint16; new_price:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:兑换商店购买商品[cmd_table.json] |
| 13403 | 兑换商城物品动态变化价格 | bidirectional | cs: type:uint8 ／ sc: type:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:兑换商城物品动态变化价格[cmd_table.json] |
| 13410 | 现金券兑换界面信息 | bidirectional | cs: — ／ sc: is_sign:uint8; record:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:现金券兑换界面信息[cmd_table.json] |
| 13411 | 个人兑换记录 | bidirectional | cs: — ／ sc: record:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人兑换记录[cmd_table.json] |
| 13415 | 填写个人信息 | bidirectional | cs: real_name:string; tel:string; qq:string; address:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:填写个人信息[cmd_table.json] |
| 13416 | 查看个人信息 | bidirectional | cs: — ／ sc: real_name:string; tel:string; qq:string; address:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看个人信息[cmd_table.json] |
| 13404 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13404；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13405 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13405；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13406 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13406；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13407 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13407；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13408 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13408；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13409 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13409；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13412 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13412；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13413 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13413；引用系统: Mall/Shop 商城[SYS_ECON_003] |
| 13414 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_ECON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_13414；引用系统: Mall/Shop 商城[SYS_ECON_003] |

### cmd_resolve_135.luac（75 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13500 | 创建帮会 | bidirectional | cs: guild_name:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:创建帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13501 | 获取帮会列表 | bidirectional | cs: page:uint8; args:table; flag:uint8; num:uint8 ／ sc: page:uint8; page_total:uint8; guilds:table; all_count:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取帮会列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13502 | 获取指定帮会基本信息 | bidirectional | cs: gid:uint32; srv_id:string ／ sc: index:uint8; gid:uint32; srv_id:string; realm:uint8; vip:uint8; guild_name:string; head_name:string; head_career:uint8; lev:uint8; role_count:uint16; max_role_count:uint16; applyed:uint8; power:uint32; assets:uint32; is_recommend:uint8; head_sex:uint8; is_invited:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取指定帮会基本信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13503 | 申请加入帮会 | bidirectional | cs: gid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:申请加入帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13504 | 本帮有人申请加入 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; all_request:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:本帮有人申请加入[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13505 | 同意或者拒绝加入帮会 | bidirectional | cs: type:uint8; rid:uint32; srv_id:string; name:string ／ sc: type:uint8; rid:uint32; srv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:同意或者拒绝加入帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13506 | 成功加入帮会 | bidirectional | cs: — ／ sc: type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:成功加入帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13507 | 获取申请加入帮会列表 | bidirectional | cs: page:uint32; num:uint8 ／ sc: page:uint8; page_total:uint8; guids:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取申请加入帮会列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13508 | 邀请加入帮会 | bidirectional | cs: rid:uint32; srv_id:string; role_name:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:邀请加入帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13509 | 获取帮会邀请列表 | bidirectional | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取帮会邀请列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13510 | 同意或者拒绝帮会邀请 | bidirectional | cs: type:uint8; gid:uint32; gsrv_id:string ／ sc: type:uint8; gid:uint32; gsrv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:同意或者拒绝帮会邀请[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13511 | 被成功邀请加入帮会 | bidirectional | cs: — ／ sc: gid:uint32; gsrv_id:string; gname:string; rname:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被成功邀请加入帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13512 | 被踢出帮会通知 | bidirectional | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被踢出帮会通知[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13513 | 从帮会中踢人 | bidirectional | cs: rid:uint32; srv_id:string; name:string ／ sc: rid:uint32; srv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:从帮会中踢人[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13514 | 退帮 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退帮[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13515 | 修改帮会信息 | bidirectional | cs: modify:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:修改帮会信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13516 | 解散帮会 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:解散帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13517 | 转让帮会 | bidirectional | cs: rid:uint32; srv_id:string; name:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转让帮会[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13518 | 获取本帮会基本信息 | bidirectional | cs: — ／ sc: guild_name:string; lev:uint8; role_count:uint16; max_role_count:uint16; stu_count:uint16; max_stu_count:uint16; aim:string; sign:string; qq:string; yy:string; head_name:string; maintain:uint32; all_assets:uint32; max_assets:uint32; member_lev:uint16; health:uint32; week_wage:uint32; max_week_wage:uint32; all_request:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取本帮会基本信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13519 | 获取帮会成员列表 | bidirectional | cs: gid:uint32; gsrv_id:string ／ sc: guid_roles:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取帮会成员列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13520 | 任命帮会职位 | bidirectional | cs: rid:uint32; srv_id:string; name:string; position:uint8; old_position:uint8 ／ sc: rid:uint32; srv_id:string; position:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:任命帮会职位[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13521 | 获取帮会职位信息 | bidirectional | cs: — ／ sc: position1:uint8; now_position1:uint8; position2:uint8; now_position2:uint8; position3:uint8; now_position3:uint8; position4:uint8; now_position4:uint8; position5:uint8; now_position5:uint8; position6:uint8; now_position6:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取帮会职位信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13522 | 取消帮会申请 | bidirectional | cs: gid:uint32; gsrv_id:string ／ sc: gid:uint32; gsrv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消帮会申请[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13523 | 帮会建筑升级 | bidirectional | cs: build_id:uint32; build_lev:uint32 ／ sc: build_id:uint32; new_build_lev:uint32; up_status:uint32; up_time:uint32; speed_time:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会建筑升级[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13524 | 帮会建筑等级信息 | bidirectional | cs: gid:uint32; gsrv_id:string ／ sc: guilds:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会建筑等级信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13525 | 购买帮会商店的物品 | bidirectional | cs: good_bid:uint32; good_num:string ／ sc: good_bid:uint32; buy_num:string; all_num:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买帮会商店的物品[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13526 | 购买帮会商店的物品 | bidirectional | cs: — ／ sc: guild_shop:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买帮会商店的物品[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13527 | 兑换帮贡 | bidirectional | cs: type:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:兑换帮贡[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13528 | 领取本周福利 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取本周福利[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13529 | 获取本周福利状态 | bidirectional | cs: — ／ sc: status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取本周福利状态[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13530 | 获取帮会仓库信息 | bidirectional | cs: — ／ sc: guild_shop:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取帮会仓库信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13531 | 分配仓库里的东西 | bidirectional | cs: id:uint32; srv_id:string; good_bid:uint32; num:string ／ sc: good_bid:uint32; num:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分配仓库里的东西[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13532 | 职位罢免 | bidirectional | cs: rid:uint32; srv_id:string; name:string; old_position:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:职位罢免[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13533 | 帮会建筑降级 | bidirectional | cs: build_id:uint32; build_lev:uint32 ／ sc: build_id:uint32; build_lev:uint32; up_status:uint32; up_time:uint32; speed_time:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会建筑降级[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13534 | 减少升级时间 | bidirectional | cs: build_id:uint32; speed_id:uint32 ／ sc: build_id:uint32; speed_time:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:减少升级时间[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13535 | 设置学徒等级 | bidirectional | cs: mem_lev:uint32 ／ sc: mem_lev:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置学徒等级[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13536 | 进入或者退出帮会领地 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入或者退出帮会领地[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13537 | 上缴宗卷 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上缴宗卷[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13538 | 更新帮会资产 | bidirectional | cs: — ／ sc: guild_assets:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新帮会资产[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13539 | 帮会搜索 | bidirectional | cs: guild_name:string ／ sc: guilds:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会搜索[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13540 | 一键加入 | bidirectional | cs: guild_list:table ／ sc: guild_list:table; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键加入[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13541 | 一键拒绝 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键拒绝[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13542 | 更新帮会成员列表 | bidirectional | cs: — ／ sc: type:uint8; guid_roles:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新帮会成员列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13543 | 发广告 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发广告[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13546 | 公告列表 | bidirectional | cs: — ／ sc: gonggao_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:公告列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13547 | 发公告 | bidirectional | cs: msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发公告[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13548 | 有新公告的时候，服务端推送本协议，告诉客户端 | bidirectional | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:有新公告的时候，服务端推送本协议，告诉客户端[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13551 | 剩余帮派礼盒总数量 | bidirectional | cs: — ／ sc: gift_num:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:剩余帮派礼盒总数量[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13552 | 帮派礼盒面板,返回可分配的角色id | bidirectional | cs: — ／ sc: gift_num:uint32; id_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮派礼盒面板,返回可分配的角色id[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13553 | 分配礼盒 | bidirectional | cs: id_list:table ／ sc: code:uint8; msg:string; gift_num:uint32; id_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分配礼盒[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13556 | 帮派福利面板 | bidirectional | cs: — ／ sc: contrib:uint32; gift_num:uint32; week_wage:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮派福利面板[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13561 | 个性签名列表 | bidirectional | cs: — ／ sc: sign_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个性签名列表[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13562 | 修改个性签名 | bidirectional | cs: rid:uint32; srv_id:string; sign:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; sign:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:修改个性签名[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13563 | 自己的个性签名 | bidirectional | cs: — ／ sc: sign:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自己的个性签名[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13564 | 获取红包信息 请求之后，根据实际情况推送13565或13566 | bidirectional | cs: id:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取红包信息 请求之后，根据实际情况推送13565或13566[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13565 | 未拆开过的红包 | sc | cs: — ／ sc: id:uint16; state:uint8; rid:uint32; srv_id:string; name:string; career:uint8; type:uint8; sex:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:未拆开过的红包[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13566 | 查看大家手气 | bidirectional | cs: id:uint16 ／ sc: code:uint8; msg:string; create_name:string; create_career:uint8; id:uint16; type:uint8; val:uint32; hongbao_get:uint16; hongbao_max:uint16; reward_get:uint32; reward_max:uint32; stop_time:uint32; role_list:table; create_sex:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看大家手气[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13567 | 拆红包 | bidirectional | cs: id:uint16 ／ sc: code:uint8; msg:string; id:uint16; val:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:拆红包[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13568 | 祈福 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8; val:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:祈福[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13569 | 祈福信息 | bidirectional | cs: — ／ sc: info:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:祈福信息[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13570 | 家族练功房数据 | bidirectional | cs: page:uint8; num:uint8 ／ sc: page:uint8; page_total:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:家族练功房数据[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13571 | 设置伙伴练功 | bidirectional | cs: partner_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置伙伴练功[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13572 | 帮助别人伙伴练功 | bidirectional | cs: rid:uint32; srv_id:string; partner_id:uint32 ／ sc: code:uint8; msg:string; partner_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮助别人伙伴练功[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13573 | 领取练功伙伴 | bidirectional | cs: partner_id:uint32 ／ sc: code:uint8; msg:string; partner_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取练功伙伴[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13574 | 查看练功房数据 | bidirectional | cs: — ／ sc: code:uint8; msg:string; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看练功房数据[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13575 | 练功房一键领取 | bidirectional | cs: — ／ sc: code:uint8; msg:string; partner_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:练功房一键领取[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13576 | 求助 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:求助[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13577 | 查看求助 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: page:uint8; page_total:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看求助[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13578 | 查看活动次数 | bidirectional | cs: — ／ sc: act_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看活动次数[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13579 | 查看神树界面 | bidirectional | cs: — ／ sc: tree_lev:uint8; strength_rest:uint32; strength_name:string; role_eff:uint32; role_delay:uint32; role_attrs:table; parter_eff:uint32; parter_delay:uint32; parter_attrs:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看神树界面[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13580 | 查看神树研究界面 | bidirectional | cs: — ／ sc: worship_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看神树研究界面[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13581 | 更换供奉研究 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; new_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更换供奉研究[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13582 | 供奉洗练 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:供奉洗练[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13583 | 强化供奉 | bidirectional | cs: — ／ sc: code:uint8; msg:string; strength_rest:uint32; strength_name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:强化供奉[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |
| 13584 | 邀请浇花 | bidirectional | cs: npc_x:int32; npc_y:int32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:邀请浇花[cmd_table.json]；1.4.9文档载于dungeon_protocol.md |

### cmd_resolve_136.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13600 | 悬赏榜信息 | bidirectional | cs: — ／ sc: left_fresh_time:uint32; boss_list:table; accept_list:table; srv_record:table; self_record:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:悬赏榜信息[cmd_table.json] |
| 13601 | 悬赏榜接受任务 | bidirectional | cs: uid:uint32 ／ sc: tips:uint8; msg:string; uid:uint32; role_id:uint32; role_srv_id:string; role_name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:悬赏榜接受任务[cmd_table.json] |

### cmd_resolve_137.luac（18 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13701 | 技能等级 | bidirectional | cs: type:uint8 ／ sc: type:uint8; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:技能等级[cmd_table.json] |
| 13702 | 技能升级 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:技能升级[cmd_table.json] |
| 13703 | 技能升级(升级5次) | bidirectional | cs: type:uint8; flag:uint8 ／ sc: code:uint8; msg:string; type:uint8; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:技能升级(升级5次)[cmd_table.json] |
| 13704 | 技能等级 | bidirectional | cs: — ／ sc: lev1:uint8; lev2:uint8; lev3:uint8; lev4:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:技能等级[cmd_table.json] |
| 13711 | 符咒生产 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:符咒生产[cmd_table.json] |
| 13721 | 裁缝生产 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:裁缝生产[cmd_table.json] |
| 13731 | 打造生产 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打造生产[cmd_table.json] |
| 13741 | 烹饪信息 | bidirectional | cs: — ／ sc: lev:uint8; learn_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:烹饪信息[cmd_table.json] |
| 13742 | 烹饪生产 | bidirectional | cs: — ／ sc: code:uint8; msg:string; item_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:烹饪生产[cmd_table.json] |
| 13743 | 烹饪学习 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:烹饪学习[cmd_table.json] |
| 13771 | 查询饱和度 | bidirectional | cs: — ／ sc: val:uint16; price:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查询饱和度[cmd_table.json] |
| 13772 | 购买饱和度 | bidirectional | cs: — ／ sc: code:uint8; msg:string; val:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:购买饱和度[cmd_table.json] |
| 13781 | 活力信息 | bidirectional | cs: — ／ sc: total_val:uint16; huoli_list:table; lingqu_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:活力信息[cmd_table.json] |
| 13786 | 日常信息 | bidirectional | cs: — ／ sc: week:uint8; richang_list:table; status_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:日常信息[cmd_table.json] |
| 13787 | 领取活力值奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string; lingqu_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取活力值奖励[cmd_table.json] |
| 13788 | 通知活力达到上限 | bidirectional | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知活力达到上限[cmd_table.json] |
| 13789 | 领取活力值奖励 | bidirectional | cs: huoli:uint16 ／ sc: code:uint8; msg:string; huoli:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取活力值奖励[cmd_table.json] |
| 13752 | UNKNOWN | sc (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_DUNGEON_003 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：SC_13752；引用系统: Tower 塔[SYS_DUNGEON_003] |

### cmd_resolve_138.luac（21 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13801 | 查询市场市场记录 | bidirectional | cs: type:uint16; page:uint8 ／ sc: left_time:uint16; type:uint16; cur_page:uint8; max_page:uint8; goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查询市场市场记录[cmd_table.json] |
| 13802 | 请求单13802个物品信息 | bidirectional | cs: market_id:uint32; item_bid:uint32 ／ sc: market_id:uint32; items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求单13802个物品信息[cmd_table.json] |
| 13803 | 元宝刷一次市场信息;成功就推13801 | bidirectional | cs: type:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:元宝刷一次市场信息;成功就推13801[cmd_table.json] |
| 13806 | 请求出售信息 | bidirectional | cs: — ／ sc: add_space:uint8; goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求出售信息[cmd_table.json] |
| 13807 | 请求单13806个物品信息 | bidirectional | cs: market_id:uint32; item_bid:uint32 ／ sc: market_id:uint32; items:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求单13806个物品信息[cmd_table.json] |
| 13810 | 批量出售物品 | bidirectional | cs: sell_list:table ／ sc: code:uint8; msg:string; sell_list:table | SYS_ACT_011 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:批量出售物品[cmd_table.json]；所属系统:Treasure Hunt 夺宝/探宝[SYS_ACT_011][systems_master.json] |
| 13811 | 物品出售 | bidirectional | cs: item_id:uint32; price:uint32; sell_num:uint16; sell_type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品出售[cmd_table.json] |
| 13812 | 物品下架 | bidirectional | cs: market_id:uint32; item_bid:uint32 ／ sc: code:uint8; msg:string; market_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品下架[cmd_table.json] |
| 13813 | 购买物品 | bidirectional | cs: market_id:uint32; item_bid:uint32; price:uint32; buy_num:uint16 ／ sc: code:uint8; msg:string; market_id:uint32; item_num:uint16; sell_num:uint16; sell_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买物品[cmd_table.json] |
| 13814 | 提取铜币/元宝（卖商品获得的） | bidirectional | cs: market_id:uint32; item_bid:uint32 ／ sc: code:uint8; msg:string; market_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提取铜币/元宝（卖商品获得的）[cmd_table.json] |
| 13815 | 查询物品价格 | bidirectional | cs: item_bid:uint32 ／ sc: price:uint32; gold:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询物品价格[cmd_table.json] |
| 13816 | 重新上架 | bidirectional | cs: market_id:uint32; item_bid:uint32; item_num:uint16; price:uint32; sell_type:uint8 ／ sc: code:uint8; msg:string; market_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重新上架[cmd_table.json] |
| 13817 | 一键提取 | bidirectional | cs: tiqu_list:table ／ sc: code:uint8; msg:string; tiqu_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键提取[cmd_table.json] |
| 13818 | 批量重新上架 | bidirectional | cs: re_sell_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:批量重新上架[cmd_table.json] |
| 13819 | 物品出售成功 | sc | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:物品出售成功[cmd_table.json] |
| 13821 | 开格子 | bidirectional | cs: add_space:uint8 ／ sc: code:uint8; msg:string; sum_space:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开格子[cmd_table.json] |
| 13826 | 更新商品(自己出售的,摆摊) | bidirectional | cs: need_update_list:table ／ sc: update_my_goods_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新商品(自己出售的,摆摊)[cmd_table.json] |
| 13841 | 查询银币商店记录 | bidirectional | cs: type:uint16 ／ sc: type:uint16; yinbi_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:查询银币商店记录[cmd_table.json] |
| 13842 | 银币商店买 | bidirectional | cs: item_bid:uint32; num:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:银币商店买[cmd_table.json] |
| 13843 | 银币商店卖 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:银币商店卖[cmd_table.json] |
| 13851 | 银币商店，物品价格 | bidirectional | cs: item_bid:uint32 ／ sc: price:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:银币商店，物品价格[cmd_table.json] |

### cmd_resolve_139.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 13901 | 充值查询 | bidirectional | cs: — ／ sc: month_card_timeout:uint32; charge_list:table; is_imperial_card:uint8; charge_return_rate:uint32 | SYS_ACT_003 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:充值查询[cmd_table.json]；所属系统:Invest 投资[SYS_ACT_003][systems_master.json] |
| 13902 | 充值 | bidirectional | cs: rmb:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:充值[cmd_table.json] |
| 13906 | 兑换查询，元宝兑换铜币，银币等 | bidirectional | cs: label:uint8 ／ sc: label:uint8; val_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:兑换查询，元宝兑换铜币，银币等[cmd_table.json] |
| 13907 | 货币兑换，元宝兑换铜币，银币等 | bidirectional | cs: label:uint8; rmb:uint16 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:货币兑换，元宝兑换铜币，银币等[cmd_table.json] |
| 13910 | 通知WEB请求发货验证(IOS专用) | cs | cs: body:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知WEB请求发货验证(IOS专用)[cmd_table.json] |
| 13999 | 测试协议 | bidirectional | cs: sign:int32 ／ sc: sign:int32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:测试协议[cmd_table.json] |

### cmd_resolve_140.luac（16 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14000 | 获取阵法信息 | bidirectional | cs: flag:uint8 ／ sc: flag:uint8; select_type:uint8; info_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取阵法信息[cmd_table.json]；1.4.9文档载于gm_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 14001 | 设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14002 | 取消设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14003 | 选中某个阵法 | bidirectional | cs: flag:uint8; type:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; s_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:选中某个阵法[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14004 | 升级 | bidirectional | cs: type:uint8 ／ sc: tips:uint16; msg:string; type:uint8; f_lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14005 | 激活某种类型阵法 | bidirectional | cs: flag:uint8; type:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; type:uint8; f_lev:uint8; hero_pos_info:table; member_pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:激活某种类型阵法[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14006 | 英雄助阵 | bidirectional | cs: flag:uint8; hero_bid:uint32; pos:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; cheer_hero:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄助阵[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14007 | 取消英雄助阵 | bidirectional | cs: flag:uint8; hero_bid:uint32 ／ sc: flag:uint8; cheer_hero:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消英雄助阵[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14008 | 双击设置阵位 | bidirectional | cs: flag:uint8; type:uint8; hero_bid:uint32 ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:双击设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14009 | 获取英雄助阵信息 | bidirectional | cs: flag:uint8 ／ sc: flag:uint8; cheer_hero:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取英雄助阵信息[cmd_table.json]；1.4.9文档载于gm_protocol.md；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 14020 | 获取阵法信息 | bidirectional | cs: flag:uint8 ／ sc: flag:uint8; select_type:uint8; info_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取阵法信息[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14021 | 设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14022 | 取消设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_bid:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14023 | 选中某个阵法 | bidirectional | cs: flag:uint8; type:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; s_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:选中某个阵法[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14028 | 双击设置阵位 | bidirectional | cs: flag:uint8; type:uint8; hero_bid:uint32 ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:双击设置阵位[cmd_table.json]；1.4.9文档载于gm_protocol.md |
| 14099 | 获取助阵伙伴属性加成 | bidirectional | cs: — ／ sc: attr_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取助阵伙伴属性加成[cmd_table.json]；1.4.9文档载于gm_protocol.md |

### cmd_resolve_141.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14100 | 累积签到天数 | bidirectional | cs: — ／ sc: days:uint8; is_get:uint8; vip_lev:uint8 | SYS_ACT_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:累积签到天数[cmd_table.json]；所属系统:Sign-in/Check-in 签到[SYS_ACT_001][systems_master.json]；1.4.9文档载于gm_protocol.md |
| 14101 | 签到领取奖励 | bidirectional | cs: — ／ sc: tips:uint16; msg:string; days:uint8; assets:table; items:table | SYS_ACT_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:签到领取奖励[cmd_table.json]；所属系统:Sign-in/Check-in 签到[SYS_ACT_001][systems_master.json]；1.4.9文档载于gm_protocol.md |

### cmd_resolve_142.luac（17 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14200 | 发送邀请 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发送邀请[cmd_table.json] |
| 14201 | 刷新任务 | bidirectional | cs: rid:uint32; srv_id:string; name:string ／ sc: rid:uint32; srv_id:string; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新任务[cmd_table.json] |
| 14202 | 试炼面板 | bidirectional | cs: — ／ sc: lave_count:uint32; refresh_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:试炼面板[cmd_table.json] |
| 14203 | 更新试炼数据 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; name:string; mission_bid:uint32; status:uint32; quality:uint8; refresh_count:uint8; all_refresh_count:uint8; brush_count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新试炼数据[cmd_table.json] |
| 14204 | 试炼任务品质 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; quality_id:uint8; assets_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:试炼任务品质[cmd_table.json] |
| 14205 | 接受试炼任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接受试炼任务[cmd_table.json] |
| 14206 | 领取任务奖励 | bidirectional | cs: mission_bid:uint32; type2:uint8 ／ sc: mission_bid:uint32; type2:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取任务奖励[cmd_table.json] |
| 14207 | 推送剩余刷新次数 | bidirectional | cs: — ／ sc: lave_count:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送剩余刷新次数[cmd_table.json] |
| 14210 | 任务列表 | bidirectional | cs: — ／ sc: reward_list:table; total_star:uint32; mission_list:table; free_times:uint8; free_refresh_time:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:任务列表[cmd_table.json] |
| 14211 | 刷新任务星数 | bidirectional | cs: bid:uint32; pay_type:uint8 ／ sc: code:uint8; msg:string; bid:uint32; star:uint8; free_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新任务星数[cmd_table.json] |
| 14212 | 领取任务奖励 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; total_star:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取任务奖励[cmd_table.json] |
| 14213 | 领取总星数奖励 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取总星数奖励[cmd_table.json] |
| 14214 | 推送任务完成 | sc | cs: — ／ sc: bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送任务完成[cmd_table.json] |
| 14215 | 更新任务扩展参数 | sc | cs: — ／ sc: bid:uint32; ext:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新任务扩展参数[cmd_table.json] |
| 14216 | 重新获取种花种子 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重新获取种花种子[cmd_table.json] |
| 14298 | 宗门任务免费刷新次数 | bidirectional | cs: — ／ sc: free_refresh_time:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门任务免费刷新次数[cmd_table.json] |
| 14299 | 刷新宗门任务 | bidirectional | cs: msg:uint32 ／ sc: code:uint8; msg:string; bid:uint32; mission:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新宗门任务[cmd_table.json] |

### cmd_resolve_143.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14300 | 弹出转职界面 | bidirectional | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:弹出转职界面[cmd_table.json] |
| 14301 | 转职 | bidirectional | cs: career:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转职[cmd_table.json] |
| 14302 | 转职成功 | bidirectional | cs: — ／ sc: career:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转职成功[cmd_table.json] |

### cmd_resolve_144.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14400 | 帮会神兽面板 | bidirectional | cs: — ／ sc: animal_lev:uint8; animal_exp:uint32; call_times:uint8; animal_record:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会神兽面板[cmd_table.json] |
| 14401 | 帮会神兽喂养 | bidirectional | cs: feed_type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会神兽喂养[cmd_table.json] |
| 14402 | 帮会神兽召唤 | bidirectional | cs: animal_lev:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会神兽召唤[cmd_table.json] |
| 14403 | 神兽喂养面板 | bidirectional | cs: — ／ sc: feed_times:uint8; all_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:神兽喂养面板[cmd_table.json] |
| 14404 | 求助 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:求助[cmd_table.json] |

### cmd_resolve_145.luac（8 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14500 | 接取捉鬼任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:接取捉鬼任务[cmd_table.json] |
| 14501 | 捉鬼寻路信息 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; map_bid:uint32; x:uint32; y:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:捉鬼寻路信息[cmd_table.json] |
| 14502 | 个人捉鬼进度 | bidirectional | cs: — ／ sc: times:uint32; times_led:uint32; times_week:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人捉鬼进度[cmd_table.json] |
| 14503 | 捉鬼奖励 | bidirectional | cs: — ／ sc: exp:uint32; coin:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:捉鬼奖励[cmd_table.json] |
| 14504 | 捉鬼战斗 | bidirectional | cs: mon_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:捉鬼战斗[cmd_table.json] |
| 14505 | 捉鬼任务成功 | bidirectional | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:捉鬼任务成功[cmd_table.json] |
| 14506 | 领取双倍提示 | sc | cs: — ／ sc: cur_double:uint16; week_left_double:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取双倍提示[cmd_table.json] |
| 14507 | 领取双倍 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取双倍[cmd_table.json] |

### cmd_resolve_146.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14600 | 累积登录天数 | bidirectional | cs: — ／ sc: days:uint16; get_day:table | SYS_ROLE_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:累积登录天数[cmd_table.json]；所属系统:Experience/Level[SYS_ROLE_005][systems_master.json]；1.4.9文档载于gm_protocol.md |
| 14601 | 登录领取奖励 | bidirectional | cs: days:uint8 ／ sc: tips:uint16; msg:string; days:uint8 | SYS_ROLE_005 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:登录领取奖励[cmd_table.json]；所属系统:Experience/Level[SYS_ROLE_005][systems_master.json]；1.4.9文档载于gm_protocol.md |

### cmd_resolve_147.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14700 | 推送抽奖数据 | bidirectional | cs: — ／ sc: id:uint32; lottery_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:推送抽奖数据[cmd_table.json] |
| 14701 | 抽奖 | bidirectional | cs: — ／ sc: id:uint32; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:抽奖[cmd_table.json] |

### cmd_resolve_148.luac（7 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14801 | 我的炼丹炉列表 | bidirectional | cs: — ／ sc: do_help_num:uint8; send_help_num:uint8; is_finish:uint8; left_time:uint32; lian_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:我的炼丹炉列表[cmd_table.json] |
| 14802 | 查看别人的炼丹炉列表 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; left_time:uint32; lian_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看别人的炼丹炉列表[cmd_table.json] |
| 14803 | 我的炼丹炉列表(接到此消息，客户端会打开界面) | bidirectional | cs: — ／ sc: do_help_num:uint8; send_help_num:uint8; is_finish:uint8; left_time:uint32; lian_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:我的炼丹炉列表(接到此消息，客户端会打开界面)[cmd_table.json] |
| 14806 | 提交物品;如果成功，客户端自行修改下数据 | bidirectional | cs: ord:uint8 ／ sc: ord:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交物品;如果成功，客户端自行修改下数据[cmd_table.json] |
| 14807 | 提交任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交任务[cmd_table.json] |
| 14811 | 发求助 | bidirectional | cs: ord:uint8 ／ sc: ord:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发求助[cmd_table.json] |
| 14812 | 帮助别人 | bidirectional | cs: rid:uint32; srv_id:string; ord:uint8 ／ sc: rid:uint32; srv_id:string; ord:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮助别人[cmd_table.json] |

### cmd_resolve_149.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 14901 | 称号列表 | bidirectional | cs: — ／ sc: cur_bid:uint16; xs_title_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:称号列表[cmd_table.json] |
| 14906 | 使用称号 | bidirectional | cs: bid:uint16 ／ sc: code:uint8; msg:string; bid:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用称号[cmd_table.json] |

### cmd_resolve_150.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15000 | 挖宝,推送藏宝图奖励数据,将物品和事件分开两个数组 | bidirectional | cs: item_id:uint32 ／ sc: pos:uint8; item_list:table; event_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挖宝,推送藏宝图奖励数据,将物品和事件分开两个数组[cmd_table.json] |
| 15001 | 藏宝图奖励获取 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:藏宝图奖励获取[cmd_table.json] |
| 15002 | 藏宝图使用 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string; item_id:uint32; MapBid:uint32; x:uint16; y:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:藏宝图使用[cmd_table.json] |
| 15003 | 藏宝图炼化 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:藏宝图炼化[cmd_table.json] |
| 15011 | 宝箱扣费询问 | sc | cs: — ／ sc: code:uint8; msg:string; elem_id:uint32; box_bid:uint32; item_list:table; assets:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝箱扣费询问[cmd_table.json] |
| 15012 | 扣费开启宝箱（成功会推送15013/15014） | bidirectional | cs: elem_id:uint32; box_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:扣费开启宝箱（成功会推送15013/15014）[cmd_table.json] |
| 15013 | 宝箱开启结果推送 | sc | cs: — ／ sc: code:uint8; msg:string; elem_id:uint32; box_bid:uint32; item_bid:uint32; item_num:uint32; is_roll:uint8; end_time:uint32; roll_member:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝箱开启结果推送[cmd_table.json] |
| 15014 | 骰子宝箱开始转盘 | sc | cs: — ／ sc: code:uint8; msg:string; elem_id:uint32; box_bid:uint32; pos:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:骰子宝箱开始转盘[cmd_table.json] |
| 15015 | 骰子宝箱转盘结束 | bidirectional | cs: elem_id:uint32; box_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:骰子宝箱转盘结束[cmd_table.json] |
| 15016 | 队员参与摇骰 | bidirectional | cs: — ／ sc: code:uint8; msg:string; roll_point:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队员参与摇骰[cmd_table.json] |
| 15017 | 推送其他成员摇骰结果 | sc | cs: — ／ sc: is_end:uint8; win_rid:uint32; win_srv_id:string; roll_member:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送其他成员摇骰结果[cmd_table.json] |

### cmd_resolve_151.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15101 | 葫芦数据，采集完，服务端会推送给客户端 | bidirectional | cs: — ／ sc: stop_val:uint16; val_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:葫芦数据，采集完，服务端会推送给客户端[cmd_table.json] |
| 15102 | 客户端通知服务端，葫芦停止转动 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端通知服务端，葫芦停止转动[cmd_table.json] |

### cmd_resolve_152.luac（9 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15200 | 接取宝图任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:接取宝图任务[cmd_table.json] |
| 15201 | 杀怪寻路信息 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; map_bid:uint32; x:uint32; y:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪寻路信息[cmd_table.json] |
| 15202 | 宝图杀怪 | bidirectional | cs: mon_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝图杀怪[cmd_table.json] |
| 15203 | 元宝兑换宝图 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:元宝兑换宝图[cmd_table.json] |
| 15204 | 获取剩余宝图元宝数 | bidirectional | cs: — ／ sc: num:uint8; gold:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取剩余宝图元宝数[cmd_table.json] |
| 15205 | 宝图杀怪任务成功 | sc | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝图杀怪任务成功[cmd_table.json] |
| 15206 | 兑换高级宝图 | bidirectional | cs: type:uint8; times:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:兑换高级宝图[cmd_table.json] |
| 15207 | 兑换高级图时,材料不足返回元宝提示 | bidirectional | cs: — ／ sc: item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:兑换高级图时,材料不足返回元宝提示[cmd_table.json] |
| 15208 | 藏宝图兑换材料信息 | bidirectional | cs: — ／ sc: times:uint16; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:藏宝图兑换材料信息[cmd_table.json] |

### cmd_resolve_153.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15300 | 接取帮会循环任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取帮会循环任务[cmd_table.json] |
| 15301 | 杀怪寻路信息 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; map_bid:uint32; x:uint32; y:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪寻路信息[cmd_table.json] |
| 15302 | 杀怪 | bidirectional | cs: mon_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪[cmd_table.json] |
| 15303 | 杀怪任务成功 | bidirectional | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪任务成功[cmd_table.json] |

### cmd_resolve_154.luac（9 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15400 | 接取循环任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:接取循环任务[cmd_table.json] |
| 15401 | 触发询问面板 | sc | cs: — ／ sc: loop_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:触发询问面板[cmd_table.json] |
| 15402 | 杀怪寻路信息 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; map_bid:uint32; x:uint32; y:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:杀怪寻路信息[cmd_table.json] |
| 15403 | 跑环杀怪 | bidirectional | cs: mon_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:跑环杀怪[cmd_table.json] |
| 15404 | 杀怪任务成功 | sc | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪任务成功[cmd_table.json] |
| 15405 | 今日杀怪总任务 | bidirectional | cs: — ／ sc: loop_count:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:今日杀怪总任务[cmd_table.json] |
| 15420 | 接取夫妻任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取夫妻任务[cmd_table.json] |
| 15421 | 触发事件 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:触发事件[cmd_table.json] |
| 15422 | 提交任务(废弃) | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交任务(废弃)[cmd_table.json] |

### cmd_resolve_155.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15501 | 我的坐骑信息 | bidirectional | cs: — ／ sc: jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:我的坐骑信息[cmd_table.json] |
| 15506 | 坐骑进阶 | bidirectional | cs: — ／ sc: code:uint8; msg:string; jie_luck:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:坐骑进阶[cmd_table.json] |
| 15507 | 领取进阶奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取进阶奖励[cmd_table.json] |
| 15511 | 坐骑装备穿戴 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑装备穿戴[cmd_table.json] |
| 15512 | 脱装备 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:脱装备[cmd_table.json] |
| 15516 | 改变外形 | bidirectional | cs: jie:uint8 ／ sc: code:uint8; msg:string; jie:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:改变外形[cmd_table.json] |
| 15517 | 上、下坐骑 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string; flag:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上、下坐骑[cmd_table.json] |
| 15518 | 装备吞噬 | bidirectional | cs: item_id_lev:uint32; item_id_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备吞噬[cmd_table.json] |
| 15519 | 使用碎片 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用碎片[cmd_table.json] |
| 15520 | 坐骑升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑升星[cmd_table.json] |

### cmd_resolve_156.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15601 | 仙尊面板 | bidirectional | cs: — ／ sc: left_time:uint32; primus_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙尊面板[cmd_table.json] |
| 15606 | 挑战 | bidirectional | cs: bid:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战[cmd_table.json] |
| 15607 | 挑战结果 | bidirectional | cs: — ／ sc: bid:uint8; code:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战结果[cmd_table.json] |
| 15611 | 加速 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:加速[cmd_table.json] |

### cmd_resolve_157.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15700 | 我的神器信息 | bidirectional | cs: — ／ sc: use_id:uint32; shenqi_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:我的神器信息[cmd_table.json] |
| 15701 | 激活神器 | bidirectional | cs: id:uint32 ／ sc: result:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活神器[cmd_table.json] |
| 15702 | 使用神器 | bidirectional | cs: id:uint32 ／ sc: result:uint8; msg:string; new_use_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用神器[cmd_table.json] |
| 15703 | 神器注能 | bidirectional | cs: id:uint32 ／ sc: result:uint8; msg:string; id:uint32; new_lev:uint16; new_star:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:神器注能[cmd_table.json] |
| 15704 | 使用魂魄 | bidirectional | cs: item_bid:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:使用魂魄[cmd_table.json] |

### cmd_resolve_158.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15801 | 我的仙灵信息 | bidirectional | cs: — ／ sc: jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:我的仙灵信息[cmd_table.json] |
| 15806 | 仙灵进阶 | bidirectional | cs: — ／ sc: code:uint8; msg:string; jie_luck:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:仙灵进阶[cmd_table.json] |
| 15807 | 领取进阶奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取进阶奖励[cmd_table.json] |
| 15811 | 仙灵装备穿戴 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙灵装备穿戴[cmd_table.json] |
| 15812 | 脱装备 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:脱装备[cmd_table.json] |
| 15816 | 改变外形 | bidirectional | cs: jie:uint16 ／ sc: code:uint8; msg:string; jie:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:改变外形[cmd_table.json] |
| 15817 | 召唤仙灵 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string; flag:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:召唤仙灵[cmd_table.json] |
| 15818 | 装备吞噬 | bidirectional | cs: item_id_lev:uint32; item_id_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备吞噬[cmd_table.json] |
| 15819 | 使用碎片激活仙灵形象 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用碎片激活仙灵形象[cmd_table.json] |
| 15820 | 仙灵升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙灵升星[cmd_table.json] |
| 15821 | 激活时效仙灵 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活时效仙灵[cmd_table.json] |

### cmd_resolve_159.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 15900 | 获取当前功能预告Id,上线推 | bidirectional | cs: — ／ sc: Id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前功能预告Id,上线推[cmd_table.json] |
| 15901 | 保存功能预告Id | cs | cs: Id:uint32 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:保存功能预告Id[cmd_table.json] |

### cmd_resolve_160.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16000 | 首冲奖励当天信息 | bidirectional | cs: — ／ sc: day:uint32; flag:uint8; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:首冲奖励当天信息[cmd_table.json] |
| 16001 | 领取奖励 | bidirectional | cs: — ／ sc: tips:uint16; msg:string; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 16002 | 购买首充 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买首充[cmd_table.json] |

### cmd_resolve_161.luac（8 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16100 | 获取今日参加答题次数 | bidirectional | cs: — ／ sc: count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取今日参加答题次数[cmd_table.json] |
| 16101 | 开始答题 | bidirectional | cs: — ／ sc: code:uint8; msg:string; left_time:uint32; index:uint8; correct_num:uint8; question_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:开始答题[cmd_table.json] |
| 16102 | 答题 | bidirectional | cs: question_id:uint32; answer:uint8 ／ sc: index:uint8; correct_num:uint8; correct_answer:uint8; question_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题[cmd_table.json] |
| 16103 | 答题超时 | sc | cs: — ／ sc: correct_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题超时[cmd_table.json] |
| 16110 | 获取今日参加答题次数 | bidirectional | cs: — ／ sc: count:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取今日参加答题次数[cmd_table.json] |
| 16111 | 开始答题 | bidirectional | cs: — ／ sc: code:uint8; msg:string; left_time:uint32; index:uint8; correct_num:uint8; question_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始答题[cmd_table.json] |
| 16112 | 答题 | bidirectional | cs: question_id:uint32; answer_list:table ／ sc: index:uint8; correct_num:uint8; correct_answer_list:table; question_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题[cmd_table.json] |
| 16113 | 答题超时 | sc | cs: — ／ sc: correct_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题超时[cmd_table.json] |

### cmd_resolve_162.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16200 | 获取Boss列表 | bidirectional | cs: — ／ sc: count:uint8; boss_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取Boss列表[cmd_table.json] |
| 16201 | Boss被杀 | sc | cs: — ／ sc: mon_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:Boss被杀[cmd_table.json] |
| 16202 | 倒计时为0时请求 | bidirectional | cs: mon_bid:uint32 ／ sc: mon_bid:uint32; kill:uint8; map_bid:uint32; x:uint16; y:uint16; left_time:uint32; award:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:倒计时为0时请求[cmd_table.json] |

### cmd_resolve_163.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16300 | 获取鲜花信息 | bidirectional | cs: ElementId:uint32 ／ sc: flower_id:uint32; rid:uint32; srv_id:string; r_name:string; water_count:uint16; rate:uint16; asset_code:uint8; asset_val:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取鲜花信息[cmd_table.json]；1.4.9文档载于battle_protocol.md；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 16301 | 浇水 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: water_count:uint16; code:uint8; rid:uint32; srv_id:string; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:浇水[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16302 | 收取 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16303 | 浇水记录 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: water_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:浇水记录[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16304 | 宗门种花数据 | bidirectional | cs: — ／ sc: flowers:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门种花数据[cmd_table.json]；1.4.9文档载于battle_protocol.md |

### cmd_resolve_164.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16400 | 成就 | bidirectional | cs: type:uint8 ／ sc: type:uint8; chengjiu:table; chengjiu_has:table; chengjiu_rate:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:成就[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16401 | 领取成就奖励 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取成就奖励[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16402 | 提示完成成就 | sc | cs: — ／ sc: chengjiu:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提示完成成就[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16403 | 成就进度改变 | sc | cs: — ／ sc: chengjiu:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:成就进度改变[cmd_table.json]；1.4.9文档载于battle_protocol.md |
| 16404 | 请求组别段内，其他玩家完成情况 | bidirectional | cs: group:uint32 ／ sc: code:uint8; msg:string; chengjiu_rate:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求组别段内，其他玩家完成情况[cmd_table.json]；1.4.9文档载于battle_protocol.md |

### cmd_resolve_165.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16500 | 投资功能标签信息 | bidirectional | cs: — ／ sc: info:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:投资功能标签信息[cmd_table.json] |
| 16501 | 激活投资 | bidirectional | cs: type:uint8 ／ sc: tips:uint16; msg:string; type:uint8; get_info:table; can_get_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活投资[cmd_table.json] |
| 16502 | 领取投资奖励 | bidirectional | cs: type:uint8; val:uint16 ／ sc: tips:uint16; msg:string; type:uint8; val:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取投资奖励[cmd_table.json] |
| 16503 | 投资显示 | bidirectional | cs: type:uint8 ／ sc: type:uint8; get_info:table; can_get_info:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:投资显示[cmd_table.json] |

### cmd_resolve_166.luac（56 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16601 | 所有活动(第一次打开请求) | bidirectional | cs: type:uint8 ／ sc: holiday_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:所有活动(第一次打开请求)[cmd_table.json] |
| 16602 | 请求所有活动未领取奖励 | bidirectional | cs: type:uint8 ／ sc: type:uint8; holiday_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求所有活动未领取奖励[cmd_table.json] |
| 16603 | 子活动 | bidirectional | cs: bid:uint32 ／ sc: bid:uint32; remain_sec:uint32; finish:uint32; aim_list:table; item_effect_list:table; int_args:table; client_reward:string; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:子活动[cmd_table.json] |
| 16604 | 领取奖励 | bidirectional | cs: bid:uint32; aim:uint32; arg:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 16605 | 活动是否开启 | bidirectional | cs: bid_list:table ／ sc: status:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:活动是否开启[cmd_table.json] |
| 16606 | 五星评论通知 | cs | cs: bid:uint32 ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:五星评论通知[cmd_table.json] |
| 16610 | 打开活动界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; end_date:string; cost_item:uint32; cost_num:uint32; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开活动界面[cmd_table.json] |
| 16611 | 开始抽奖 | bidirectional | cs: — ／ sc: code:uint8; msg:string; reward_id:uint8; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始抽奖[cmd_table.json] |
| 16612 | 获奖玩家列表 | bidirectional | cs: — ／ sc: his_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获奖玩家列表[cmd_table.json] |
| 16613 | 玩家获奖公告 | bidirectional | cs: — ／ sc: srv_id:string; name:string; type:uint8; item_id:uint32; num:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玩家获奖公告[cmd_table.json] |
| 16614 | 获取祝福墙 | bidirectional | cs: — ／ sc: total_score:uint32; title2:string; top_banner:string; rule_str:string; time_str:string; aim_list:table; record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取祝福墙[cmd_table.json] |
| 16615 | 刷新祝福墙 | bidirectional | cs: — ／ sc: code:uint8; msg:string; record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新祝福墙[cmd_table.json] |
| 16616 | 发送祝福 | bidirectional | cs: msg:string ／ sc: code:uint8; msg:string; record:string; total_score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发送祝福[cmd_table.json] |
| 16617 | 领取祝福值奖励 | bidirectional | cs: aim:uint32 ／ sc: code:uint8; msg:string; aim:uint32; total_score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取祝福值奖励[cmd_table.json] |
| 16620 | 子活动 | bidirectional | cs: id_list:table ／ sc: holiday_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:子活动[cmd_table.json] |
| 16621 | 翻牌界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; end_date:string; reward_list:table; card_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻牌界面[cmd_table.json] |
| 16622 | 开始翻牌 | bidirectional | cs: index:uint8 ／ sc: code:uint8; msg:string; index:uint8; reward_id:uint16; reset_flag:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始翻牌[cmd_table.json] |
| 16623 | 重置翻牌（成功推送16621） | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重置翻牌（成功推送16621）[cmd_table.json] |
| 16624 | 翻牌公告记录 | bidirectional | cs: — ／ sc: his_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻牌公告记录[cmd_table.json] |
| 16625 | 推送翻牌获奖公告 | sc | cs: — ／ sc: srv_id:string; name:string; item_id:uint32; num:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送翻牌获奖公告[cmd_table.json] |
| 16626 | 密令活动信息 | bidirectional | cs: — ／ sc: holiday_bid:uint32; remain_sec:uint32; list:table; client_reward:string; item_effect_list:table; refresh_times:uint8; tot_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:密令活动信息[cmd_table.json] |
| 16627 | 领取密令任务最终奖励 | bidirectional | cs: mission_type:uint8 ／ sc: code:uint8; msg:string; mission_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取密令任务最终奖励[cmd_table.json] |
| 16630 | 1元抢购活动信息 | bidirectional | cs: page:uint8 ／ sc: holiday_bid:uint32; time_str:string; page:uint8; list:table; end_time:uint32; remain_sec:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:1元抢购活动信息[cmd_table.json] |
| 16631 | 获取中奖者信息列表 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取中奖者信息列表[cmd_table.json] |
| 16632 | 夺宝 | bidirectional | cs: order_bid:uint32; version:uint32; type:uint8; buy_cnt:uint32; item_bid:uint32; item_cnt:uint32 ／ sc: code:uint8; msg:string; order_bid:uint32; version:uint32; type:uint8; buy_cnt:uint32; sell_out:uint8; home_page:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:夺宝[cmd_table.json] |
| 16633 | 查看订单的夺宝记录 | bidirectional | cs: order_bid:uint32; version:uint32 ／ sc: list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看订单的夺宝记录[cmd_table.json] |
| 16634 | 更新单个订单信息 | bidirectional | cs: type:uint8; order_bid:uint32; version:uint32 ／ sc: code:uint8; type:uint8; order_bid:uint32; version:uint32; tag:uint8; status:uint8; rest:uint32; total:uint32; dead_line:uint32; item_list:table; shelf:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新单个订单信息[cmd_table.json] |
| 16635 | 查看我的夺宝记录列表 | bidirectional | cs: — ／ sc: order_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看我的夺宝记录列表[cmd_table.json] |
| 16636 | 查看单个我的夺宝记录 | bidirectional | cs: order_bid:uint32; version:uint32 ／ sc: type:uint8; order_bid:uint32; version:uint32; buy_cnt:uint32; buy_time:uint32; rest:uint32; total:uint32; item_list:table; number:uint32; role_id:uint32; srv_id:string; role_name:string; open_time:uint32; dead_line:uint32; order_status:uint8; shelf:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看单个我的夺宝记录[cmd_table.json] |
| 16637 | 查看某张订单我的幸运号码 | bidirectional | cs: order_bid:uint32; version:uint32 ／ sc: order_bid:uint32; version:uint32; buy_cnt:uint32; status:uint8; num_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看某张订单我的幸运号码[cmd_table.json] |
| 16638 | 查看某张订单幸运号码的计算公式 | bidirectional | cs: order_bid:uint32; version:uint32 ／ sc: order_bid:uint32; version:uint32; rand_num:uint32; change_num:uint32; tot_time:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看某张订单幸运号码的计算公式[cmd_table.json] |
| 16639 | 刷新密令任务 | bidirectional | cs: mission_type:uint8; old_mission_bid:uint32 ／ sc: code:uint8; msg:string; mission_type:uint8; old_mission_bid:uint32; new_mission_bid:uint32; new_flag:uint8; refresh_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新密令任务[cmd_table.json] |
| 16640 | 获取你选我送活动数据 | bidirectional | cs: holiday_bid:uint32 ／ sc: holiday_bid:uint32; choose_list:table; coin_type:uint8; refresh_cost:uint32; refresh_status:uint8; reward_list:table; status:uint8; client_reward:string; item_effect_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取你选我送活动数据[cmd_table.json] |
| 16641 | 刷新待选奖励列表 | bidirectional | cs: holiday_bid:uint32 ／ sc: code:uint8; msg:string; holiday_bid:uint32; coin_type:uint8; refresh_cost:uint32; choose_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新待选奖励列表[cmd_table.json] |
| 16642 | 选择奖励 | bidirectional | cs: holiday_bid:uint32; id:uint16 ／ sc: code:uint8; msg:string; holiday_bid:uint32; id:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:选择奖励[cmd_table.json] |
| 16643 | 领取奖励 | bidirectional | cs: holiday_bid:uint32 ／ sc: code:uint8; msg:string; holiday_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 16646 | 获取奖励找回信息列表 | bidirectional | cs: type:uint8 ／ sc: type:uint8; list:table; countdown:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取奖励找回信息列表[cmd_table.json] |
| 16647 | 领取奖励 | bidirectional | cs: id:uint32; type:uint8; order:uint8 ／ sc: code:uint8; msg:string; id:uint32; type:uint8; order:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 16648 | 奖励找回数据刷新 | sc | cs: — ／ sc: type:uint8; list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:奖励找回数据刷新[cmd_table.json] |
| 16649 | 获取奖励一键找回总花费 | bidirectional | cs: type:uint8 ／ sc: type:uint8; coin_type1:uint8; coin1:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取奖励一键找回总花费[cmd_table.json] |
| 16650 | 奖励找回数据刷新 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:奖励找回数据刷新[cmd_table.json] |
| 16651 | 获取刮刮乐活动数据 | bidirectional | cs: — ／ sc: code:uint8; msg:string; remain_sec:uint32; cash_reward:uint32; card_list:table; item_list:table; item_effect_list:table; client_reward:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取刮刮乐活动数据[cmd_table.json] |
| 16652 | 刮卡 | bidirectional | cs: index:uint32 ／ sc: code:uint8; msg:string; index:uint32; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刮卡[cmd_table.json] |
| 16653 | 再来一轮 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:再来一轮[cmd_table.json] |
| 16664 | 获取限时充值返利活动数据 | bidirectional | cs: — ／ sc: msg:string; bid:uint32; remain_sec:uint32; status:uint32; end_time:uint32; rate:uint32; client_reward:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取限时充值返利活动数据[cmd_table.json] |
| 16665 | 打开金银塔界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; end_time:uint32; score:uint32; level:uint8; index:uint8; record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开金银塔界面[cmd_table.json] |
| 16666 | 开始抽奖 | bidirectional | cs: count:uint8 ／ sc: code:uint8; msg:string; per_level:uint8; per_index:uint8; new_level:uint8; new_index:uint8; score:uint32; count:uint8; run_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始抽奖[cmd_table.json] |
| 16667 | 抽奖完毕 | bidirectional | cs: — ／ sc: code:uint8; msg:string; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:抽奖完毕[cmd_table.json] |
| 16668 | 抽奖记录 | bidirectional | cs: — ／ sc: record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:抽奖记录[cmd_table.json] |
| 16693 | 查询奖池转盘信息 | bidirectional | cs: — ／ sc: end_time:uint32; info:table; records:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查询奖池转盘信息[cmd_table.json] |
| 16694 | 奖池转盘抽奖 | bidirectional | cs: num:uint8 ／ sc: code:uint8; bonus:uint32; rewards:table; records:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:奖池转盘抽奖[cmd_table.json] |
| 16695 | 请求下载有礼的状态 | bidirectional | cs: — ／ sc: status:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求下载有礼的状态[cmd_table.json] |
| 16696 | 领取边玩边下奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取边玩边下奖励[cmd_table.json] |
| 16697 | 坐骑转盘信息 | bidirectional | cs: — ／ sc: num:uint32; end_time:uint32; need_item_bid:uint16; need_item_num:uint32; trun_list:table; ext_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑转盘信息[cmd_table.json] |
| 16698 | 坐骑转盘 | bidirectional | cs: n:uint32 ／ sc: code:uint8; msg:string; n:uint32; num:uint32; bid_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑转盘[cmd_table.json] |
| 16699 | 坐骑转盘发奖励 | bidirectional | cs: — ／ sc: type:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:坐骑转盘发奖励[cmd_table.json] |

### cmd_resolve_167.luac（7 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16700 | vip获取等级 | bidirectional | cs: — ／ sc: vip_lev:uint8; get_award:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip获取等级[cmd_table.json] |
| 16701 | vip面板 | bidirectional | cs: vip_lev:uint8 ／ sc: get_info:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:vip面板[cmd_table.json] |
| 16702 | vip领取奖励 | bidirectional | cs: vip_lev:uint8 ／ sc: tips:uint16; msg:string; get_award:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:vip领取奖励[cmd_table.json] |
| 16703 | 领取VIP等级礼包 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取VIP等级礼包[cmd_table.json] |
| 16704 | 获取VIP等级礼包每日状态 | bidirectional | cs: — ／ sc: vip_lev:uint8; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取VIP等级礼包每日状态[cmd_table.json] |
| 16705 | 获取超级VIP显示状态 | bidirectional | cs: — ／ sc: status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取超级VIP显示状态[cmd_table.json] |
| 16706 | 获取超级VIP界面信息 | bidirectional | cs: — ／ sc: status:uint8; qq:string; items:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取超级VIP界面信息[cmd_table.json] |

### cmd_resolve_168.luac（1 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16800 | 屏幕下方提示 | sc | cs: — ／ sc: type:uint8; arg_uint32:table; arg_str:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:屏幕下方提示[cmd_table.json] |

### cmd_resolve_169.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 16900 | 累积充值可领取状态 | bidirectional | cs: — ／ sc: charge:uint32; status:table | SYS_COMM_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:累积充值可领取状态[cmd_table.json]；所属系统:Rank 排行榜[SYS_COMM_001][systems_master.json] |
| 16901 | 领取累积充值奖励 | bidirectional | cs: key:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取累积充值奖励[cmd_table.json] |
| 16903 | 在线领取奖励状态 | bidirectional | cs: — ／ sc: day:uint32; online_time:uint32; next_aim:uint32; status:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:在线领取奖励状态[cmd_table.json]；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 16904 | 领取在线奖励 | bidirectional | cs: aim:uint32 ／ sc: code:uint8; msg:string; aim:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取在线奖励[cmd_table.json] |
| 16902 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_COMM_001 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_16902；引用系统: Rank 排行榜[SYS_COMM_001] |

### cmd_resolve_170.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17000 | 接取任务 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:接取任务[cmd_table.json] |
| 17001 | 获取玩家今日最大通关数 | bidirectional | cs: — ／ sc: max_gate:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取玩家今日最大通关数[cmd_table.json] |

### cmd_resolve_171.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17100 | 每日充值当天信息 | bidirectional | cs: — ／ sc: day:uint32; gold_num:uint32; type_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:每日充值当天信息[cmd_table.json] |
| 17101 | 领取奖励 | bidirectional | cs: type:uint8 ／ sc: tips:uint16; msg:string; type:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 17199 | 首发转盘 | bidirectional | cs: holiday_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:首发转盘[cmd_table.json] |

### cmd_resolve_172.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17200 | 一次充值信息 | bidirectional | cs: — ／ sc: day:uint32; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一次充值信息[cmd_table.json]；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 17201 | 领取奖励 | bidirectional | cs: — ／ sc: tips:uint16; msg:string; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |

### cmd_resolve_173.luac（12 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17301 | 打开界面 | bidirectional | cs: — ／ sc: result:uint8; msg:string; daily_time:uint16; daily_time2:uint32; score:uint32; win_times:uint32; lose_times:uint32; total_times:uint32; rest_time:uint32; first_reward:uint8; is_match:uint8; kill_number:uint32; continue_win:uint32; is_team_open:uint8; act_status:uint8; daily_win:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开界面[cmd_table.json] |
| 17302 | 参与/取消匹配 | bidirectional | cs: act_type:uint8; action:uint8 ／ sc: tips:uint8; msg:string; act_type:uint8; is_match:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:参与/取消匹配[cmd_table.json] |
| 17303 | 匹配结果返回 | sc | cs: — ／ sc: tips:uint8; msg:string; type:uint8; friend_team_power:uint32; friend_list:table; enemy_team_power:uint32; enemy_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:匹配结果返回[cmd_table.json] |
| 17304 | 战斗异常返回 | sc | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗异常返回[cmd_table.json] |
| 17305 | 战斗结果返回 | sc | cs: — ／ sc: tips:uint8; act_type:uint8; bat_res:uint8; win_point:uint32; point:uint32; win_score:int32; score:uint32; coin:uint32; exp:uint32; daily_time:uint32; daily_time2:uint32; friend_list:table; role_hurl_list:table; daily_win:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结果返回[cmd_table.json] |
| 17306 | 活动奖励状态 | bidirectional | cs: — ／ sc: reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:活动奖励状态[cmd_table.json] |
| 17307 | 领取每日段位奖励 | bidirectional | cs: type:uint8; num:uint8 ／ sc: tips:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取每日段位奖励[cmd_table.json] |
| 17308 | 获取段位排行榜 | bidirectional | cs: start_rank:uint32; end_rank:uint32 ／ sc: rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取段位排行榜[cmd_table.json] |
| 17309 | 好友段位排行榜 | bidirectional | cs: — ／ sc: rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:好友段位排行榜[cmd_table.json] |
| 17310 | 段位分分布表 | bidirectional | cs: — ／ sc: score_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:段位分分布表[cmd_table.json] |
| 17311 | 3V3队长进入报名页面后通知队员 | bidirectional | cs: type:uint8 ／ sc: type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:3V3队长进入报名页面后通知队员[cmd_table.json] |
| 17312 | 进入准备场景 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入准备场景[cmd_table.json] |

### cmd_resolve_174.luac（7 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17400 | 进入活动界面显示 | bidirectional | cs: — ／ sc: code:uint8; msg:string; enemy_guild_id:uint32; enemy_guild_srv_id:string; enemy_guild_name:string; status:uint32; time:uint32; total_star:uint16; max_star:uint16; total_attack:uint32; enemy_total_star:uint16; enemy_max_star:uint16; enemy_total_attack:uint32; left_times:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入活动界面显示[cmd_table.json] |
| 17401 | 帮会参战人员信息 | bidirectional | cs: guild_id:uint32; guild_srv_id:string; divide_num:uint32 ／ sc: divide_num:uint32; guild_id:uint32; guild_srv_id:string; member_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会参战人员信息[cmd_table.json] |
| 17402 | 敌方参战人员城堡信息 | bidirectional | cs: guild_id:uint32; guild_srv_id:string; r_id:uint32; r_srv_id:string ／ sc: def_count:uint32; attack_star:uint8; r_name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:敌方参战人员城堡信息[cmd_table.json] |
| 17403 | 我方参战人员城堡信息 | bidirectional | cs: guild_id:uint32; guild_srv_id:string; r_id:uint32; r_srv_id:string ／ sc: attack_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:我方参战人员城堡信息[cmd_table.json] |
| 17404 | 参战人员城堡被攻击记录 | bidirectional | cs: guild_id:uint32; guild_srv_id:string; r_id:uint32; r_srv_id:string ／ sc: be_attack_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:参战人员城堡被攻击记录[cmd_table.json] |
| 17405 | 攻打城堡 | bidirectional | cs: guild_id:uint32; guild_srv_id:string; r_id:uint32; r_srv_id:string; star:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻打城堡[cmd_table.json] |
| 17406 | 我方进攻一览 | bidirectional | cs: — ／ sc: attack_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:我方进攻一览[cmd_table.json] |

### cmd_resolve_175.luac（22 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17501 | 进入场景 | bidirectional | cs: type:uint8 ／ sc: code:uint8; type:uint8; msg:string | SYS_SOCIAL_009 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入场景[cmd_table.json]；所属系统:Guild Wars 公会战[SYS_SOCIAL_009][systems_master.json] |
| 17502 | 活动倒计时 | bidirectional | cs: — ／ sc: state:uint8; rest_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动倒计时[cmd_table.json] |
| 17503 | 获取界面信息 | bidirectional | cs: — ／ sc: code:uint8; msg:string; state:uint8; rest_time:uint32; rank:uint16; score:uint32; rest_count:uint8; first_state:uint8; cont_state:uint8; war_state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取界面信息[cmd_table.json] |
| 17504 | 帮会积分榜 | bidirectional | cs: — ／ sc: rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会积分榜[cmd_table.json] |
| 17505 | 帮会个人积分榜 | bidirectional | cs: — ／ sc: rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会个人积分榜[cmd_table.json] |
| 17506 | 准备区获得资产奖励（个人） | bidirectional | cs: — ／ sc: assets_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备区获得资产奖励（个人）[cmd_table.json] |
| 17507 | 开始匹配 | bidirectional | cs: — ／ sc: code:uint8; msg:string; time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始匹配[cmd_table.json] |
| 17508 | 匹配失败 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:匹配失败[cmd_table.json] |
| 17509 | 匹配结果 | bidirectional | cs: — ／ sc: code:uint8; msg:string; role_name:string; lev:uint16; career:uint8; sex:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:匹配结果[cmd_table.json] |
| 17510 | 战斗结果 | bidirectional | cs: — ／ sc: code:uint8; msg:string; bat_res:uint8; rest_count:uint8; rank:uint16; win_score:uint32; score:uint32; first_state:uint8; cont_state:uint8; assets:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结果[cmd_table.json] |
| 17511 | 战斗出错 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗出错[cmd_table.json] |
| 17512 | 聊天协议；世界，场景，帮派，队伍，传闻，系统 | bidirectional | cs: — ／ sc: role_list:table; channel:uint16; len:uint8; msg:string; self_guild:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:聊天协议；世界，场景，帮派，队伍，传闻，系统[cmd_table.json] |
| 17513 | 最近的几条聊天消息(帮派和队伍) | bidirectional | cs: channel:uint16 ／ sc: channel:uint16; msg_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:最近的几条聊天消息(帮派和队伍)[cmd_table.json] |
| 17514 | 发表聊天;成功不会返回 | bidirectional | cs: channel:uint16; len:uint8; msg:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发表聊天;成功不会返回[cmd_table.json] |
| 17515 | 领取参赛奖励 | bidirectional | cs: type:uint8 ／ sc: code:uint8; type:uint8; state:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取参赛奖励[cmd_table.json] |
| 17516 | 通知玩家报名 | bidirectional | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知玩家报名[cmd_table.json] |
| 17517 | 帮会总结算 | bidirectional | cs: — ／ sc: rank:uint16; gname:string; num:uint16; total_score:uint32; score:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会总结算[cmd_table.json] |
| 17518 | 场景累计经验更新 | bidirectional | cs: — ／ sc: exp:uint32; hero_exp:uint32; coin:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:场景累计经验更新[cmd_table.json] |
| 17519 | 场景信息 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:场景信息[cmd_table.json] |
| 17520 | 请求观察战斗 | bidirectional | cs: rid:uint32; srv:string; key:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求观察战斗[cmd_table.json] |
| 17521 | 主动报名 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:主动报名[cmd_table.json] |
| 17500 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_SOCIAL_004 | ✓ | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_17500；引用系统: Guild 公会[SYS_SOCIAL_004] |

### cmd_resolve_176.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17600 | 界面信息 | bidirectional | cs: — ／ sc: days:uint16; reward:uint8; get_day:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:界面信息[cmd_table.json] |
| 17601 | 翻牌 | bidirectional | cs: day:uint8 ／ sc: tips:uint16; msg:string; days:uint8; num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:翻牌[cmd_table.json] |
| 17602 | 领奖 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领奖[cmd_table.json] |

### cmd_resolve_177.luac（15 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17700 | 强化 | bidirectional | cs: from_code:uint8; item_id:uint32; protect_id:uint32; lucky_id:uint32; lucky_num:uint8; state:uint8 ／ sc: code:uint8; msg:string; from_code:uint8; item_id:uint32; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:强化[cmd_table.json] |
| 17703 | 装备升级 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; inherit_id:uint8; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; eqm_item_id_new:uint32; eqm_item_bid_new:uint32; eqm_item_power_new:uint32; intensify_lev:uint8; refine:uint16; attr:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:装备升级[cmd_table.json] |
| 17704 | 装备重铸 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32; state:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; rate:uint16; refine:uint16; attr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备重铸[cmd_table.json] |
| 17705 | 保存重铸属性 | bidirectional | cs: bag_code:uint8; eqm_item_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; eqm_item_id:uint32; eqm_item_power_new:uint32; rate:uint16; refine:uint16; attr:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:保存重铸属性[cmd_table.json] |
| 17706 | 一键升级伙伴装备 | bidirectional | cs: bag_code:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键升级伙伴装备[cmd_table.json] |
| 17707 | 一键对调伙伴装备 | bidirectional | cs: partner_id_a:uint32; partner_id_b:uint32 ／ sc: code:uint8; msg:string; item_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键对调伙伴装备[cmd_table.json] |
| 17708 | 一键升级伙伴装备花销 | bidirectional | cs: bag_code:uint8; partner_id:uint32 ／ sc: code:uint8; cost:uint32; list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:一键升级伙伴装备花销[cmd_table.json] |
| 17709 | 共鸣消耗 | bidirectional | cs: id:uint32; bid:uint16 ／ sc: tips:uint8; msg:string; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:共鸣消耗[cmd_table.json] |
| 17710 | 共鸣保存 | bidirectional | cs: id:uint32 ／ sc: tips:uint8; msg:string; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:共鸣保存[cmd_table.json] |
| 17711 | 装备突破 | bidirectional | cs: bag_code:uint8; id:uint32 ／ sc: tips:uint8; msg:string; bag_code:uint8; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备突破[cmd_table.json] |
| 17712 | 伙伴神器升阶 | bidirectional | cs: bag_code:uint8; id:uint32 ／ sc: tips:uint8; msg:string; bag_code:uint8; item_id:uint32; stage:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴神器升阶[cmd_table.json] |
| 17713 | 伙伴神器碎片合成 | bidirectional | cs: bag_code:uint8; item_bid:uint32 ／ sc: tips:uint8; msg:string; bag_code:uint8; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴神器碎片合成[cmd_table.json] |
| 17714 | 伙伴神器碎片分解 | bidirectional | cs: bag_code:uint8; id:uint32 ／ sc: tips:uint8; msg:string; bag_code:uint8; item_id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴神器碎片分解[cmd_table.json] |
| 17715 | 伙伴神器分解 | bidirectional | cs: bag_code:uint8; id:uint32 ／ sc: tips:uint8; msg:string; bag_code:uint8; item_id:uint32; list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴神器分解[cmd_table.json] |
| 17716 | 伙伴神器强化转移 | bidirectional | cs: bag_code1:uint8; id1:uint32; bag_code2:uint8; id2:uint32 ／ sc: tips:uint8; msg:string; bag_code1:uint8; id1:uint32; intensify_lev1:uint32; bag_code2:uint8; id2:uint32; intensify_lev2:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴神器强化转移[cmd_table.json] |

### cmd_resolve_178.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17800 | 获取今日摇钱次数 | bidirectional | cs: — ／ sc: free_count:uint8; all_free_count:uint8; gold_count:uint8; get_coin:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取今日摇钱次数[cmd_table.json]；1.4.11实机实测CS带rid(4字节)，fields.json(源自1.4.9)记为空CS[real_cs_formats_1_4_11.md] |
| 17801 | 摇钱 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:摇钱[cmd_table.json] |

### cmd_resolve_179.luac（9 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 17901 | 打开界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; rank:uint32; rest_times:uint8; buy_times:uint16; delay_sec:uint32; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开界面[cmd_table.json] |
| 17902 | 挑战列表 | bidirectional | cs: — ／ sc: rank:uint32; rank_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战列表[cmd_table.json] |
| 17903 | 历史战报 | bidirectional | cs: — ／ sc: his_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:历史战报[cmd_table.json] |
| 17904 | 开始挑战 | bidirectional | cs: rank:uint32; bid:uint32 ／ sc: code:uint8; msg:string; rest_times:uint8; delay_sec:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开始挑战[cmd_table.json] |
| 17905 | 战斗结果 | bidirectional | cs: — ／ sc: res:uint8; rank:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结果[cmd_table.json] |
| 17906 | 购买次数 | bidirectional | cs: — ／ sc: code:uint8; msg:string; rest_times:uint8; buy_times:uint16 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买次数[cmd_table.json] |
| 17907 | 加速冷却 | bidirectional | cs: — ／ sc: code:uint8; msg:string; delay_sec:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:加速冷却[cmd_table.json] |
| 17908 | 领取入围奖 | bidirectional | cs: rank:uint32 ／ sc: code:uint8; msg:string; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取入围奖[cmd_table.json] |
| 17909 | 被挑战通知 | bidirectional | cs: — ／ sc: state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被挑战通知[cmd_table.json] |

### cmd_resolve_180.luac（23 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18000 | 打开界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; lucky_star:uint8; rest_times:uint8; list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开界面[cmd_table.json] |
| 18001 | 祝福玩家 | bidirectional | cs: type:uint8; rid:uint32; srv:string ／ sc: code:uint8; msg:string; star:uint8; rest_times:uint8; rid:uint32; srv:string; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:祝福玩家[cmd_table.json] |
| 18002 | 被邀请 | bidirectional | cs: — ／ sc: star:uint8; rid:uint32; srv:string; name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被邀请[cmd_table.json] |
| 18003 | 被祝福 | bidirectional | cs: — ／ sc: type:uint8; star:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被祝福[cmd_table.json] |
| 18004 | 单独请求剩余次数和运势 | bidirectional | cs: — ／ sc: lucky_star:uint8; rest_times:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:单独请求剩余次数和运势[cmd_table.json] |
| 18005 | 一键邀请 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一键邀请[cmd_table.json] |
| 18006 | 帮会目标界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; task_list:table; reward_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会目标界面[cmd_table.json] |
| 18007 | 领取帮会目标奖励 | bidirectional | cs: num:uint8 ／ sc: code:uint8; msg:string; num:uint8; state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取帮会目标奖励[cmd_table.json] |
| 18008 | 帮会目标完成提示(推送) | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会目标完成提示(推送)[cmd_table.json] |
| 18009 | 帮会技能升级界面 | bidirectional | cs: — ／ sc: skill_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会技能升级界面[cmd_table.json] |
| 18010 | 帮会技能提升上限界面 | bidirectional | cs: — ／ sc: skill_data:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会技能提升上限界面[cmd_table.json] |
| 18011 | 提升个人帮会技能 | bidirectional | cs: type:uint32 ／ sc: code:uint8; msg:string; type:uint32; lev:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提升个人帮会技能[cmd_table.json] |
| 18012 | 提升帮会技能上限 | bidirectional | cs: type:uint32 ／ sc: code:uint8; msg:string; type:uint32; lev_limit:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提升帮会技能上限[cmd_table.json] |
| 18013 | 推送新人入帮提示 | sc | cs: — ／ sc: rid:uint32; srv_id:string; career:uint8; sex:uint8; lev:uint8; role_name:string; head_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送新人入帮提示[cmd_table.json] |
| 18014 | 赠送金币 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:赠送金币[cmd_table.json] |
| 18015 | 推送赠送金币提示 | sc | cs: — ／ sc: rid:uint32; srv_id:string; career:uint8; sex:uint8; lev:uint8; role_name:string; head_bid:uint32; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送赠送金币提示[cmd_table.json] |
| 18020 | 打开拍卖行界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; buy_list:table; notice_list:table; item_list:table | SYS_ECON_008 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开拍卖行界面[cmd_table.json]；所属系统:Auction/拍卖[SYS_ECON_008][systems_master.json] |
| 18021 | 推送拍卖行物品信息 | bidirectional | cs: — ／ sc: type:uint8; item_list:table | SYS_ECON_008 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:推送拍卖行物品信息[cmd_table.json]；所属系统:Auction/拍卖[SYS_ECON_008][systems_master.json] |
| 18022 | 一口价购买 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | SYS_ECON_008 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:一口价购买[cmd_table.json]；所属系统:Auction/拍卖[SYS_ECON_008][systems_master.json] |
| 18023 | 参与竞价 | bidirectional | cs: id:uint32; price:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:参与竞价[cmd_table.json] |
| 18024 | 自己的竞拍记录 | bidirectional | cs: — ／ sc: record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自己的竞拍记录[cmd_table.json] |
| 18025 | 帮会的竞拍记录 | bidirectional | cs: — ／ sc: record_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会的竞拍记录[cmd_table.json] |
| 18026 | 设置关注 | bidirectional | cs: item_bid:uint32; type:uint8 ／ sc: code:uint8; msg:string; item_bid:uint32; type:uint8; notice_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置关注[cmd_table.json] |

### cmd_resolve_181.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18100 | 获取元神信息 | bidirectional | cs: — ／ sc: ys_list:table; cur_type:uint8; left_time:uint32; state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取元神信息[cmd_table.json] |
| 18101 | 修炼元神 | bidirectional | cs: ys_type:uint8 ／ sc: code:uint8; msg:string; ys_type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:修炼元神[cmd_table.json] |
| 18102 | 提升境界 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提升境界[cmd_table.json] |
| 18103 | 加速修炼 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:加速修炼[cmd_table.json] |

### cmd_resolve_182.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18200 | 接取任务 | bidirectional | cs: — ／ sc: tips:uint16; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取任务[cmd_table.json] |
| 18201 | 获取玩家今日最大通关数 | bidirectional | cs: — ／ sc: max_gate:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取玩家今日最大通关数[cmd_table.json] |

### cmd_resolve_183.luac（23 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18300 | 发起求婚 | bidirectional | cs: — ／ sc: code:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:发起求婚[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18301 | 询问求婚反馈（服务端推送） | bidirectional | cs: — ／ sc: self_state:uint8; spouse_state:uint8; boyname:string; grilname:string; obj_rid:uint32; obj_srv:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:询问求婚反馈（服务端推送）[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18302 | 求婚应答 | bidirectional | cs: ret:uint8 ／ sc: code:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:求婚应答[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18303 | 推送求婚结果，状态：0不同意，1同意 | bidirectional | cs: — ／ sc: self_state:uint8; spouse_state:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送求婚结果，状态：0不同意，1同意[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18304 | 选择婚宴 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:选择婚宴[cmd_table.json] |
| 18305 | 进入婚宴 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入婚宴[cmd_table.json] |
| 18306 | 退出婚宴 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出婚宴[cmd_table.json] |
| 18307 | 婚宴信息 | bidirectional | cs: — ／ sc: a_name:string; b_name:string; type:uint8; rest_time:uint32; status:uint8; end_time:uint32 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:婚宴信息[cmd_table.json] |
| 18308 | 广播婚宴阶段 | bidirectional | cs: — ／ sc: main_state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:广播婚宴阶段[cmd_table.json] |
| 18309 | 广播婚宴仪式阶段 | bidirectional | cs: — ／ sc: state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:广播婚宴仪式阶段[cmd_table.json] |
| 18310 | 发红包、喜糖 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发红包、喜糖[cmd_table.json] |
| 18311 | 敬酒、撒花、弹幕 | bidirectional | cs: type:uint8; content:string ／ sc: code:uint8; msg:string; type:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:敬酒、撒花、弹幕[cmd_table.json] |
| 18312 | 广播弹幕 | bidirectional | cs: — ／ sc: content_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:广播弹幕[cmd_table.json] |
| 18313 | 检查是否满足离婚离线天数 | bidirectional | cs: — ／ sc: ret:uint8 | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:检查是否满足离婚离线天数[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18314 | 发起离婚 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:发起离婚[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18315 | 询问离婚反馈（服务端推送） | bidirectional | cs: — ／ sc: msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:询问离婚反馈（服务端推送）[cmd_table.json] |
| 18316 | 离婚应答 | bidirectional | cs: ret:uint8 ／ sc: code:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:离婚应答[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18317 | 广播互动玩法 | bidirectional | cs: — ／ sc: type:uint8; name:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:广播互动玩法[cmd_table.json] |
| 18318 | 结婚状态推送 | bidirectional | cs: — ／ sc: state:uint8; spouse_name:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:结婚状态推送[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18319 | 结婚场景信息（推送） | bidirectional | cs: — ／ sc: qifen:uint32; total_qifen:uint32; rest_time:uint32; exp:uint32; coin:uint32; use_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结婚场景信息（推送）[cmd_table.json] |
| 18320 | 结婚场景人员信息 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结婚场景人员信息[cmd_table.json] |
| 18321 | 婚戒装备进阶 | bidirectional | cs: — ／ sc: code:uint8; msg:string | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:婚戒装备进阶[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |
| 18322 | 婚戒技能升级 | bidirectional | cs: skill_id:uint32 ／ sc: code:uint8; msg:string; new_skill_id:uint32 | SYS_SOCIAL_005 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:婚戒技能升级[cmd_table.json]；所属系统:Marriage 结婚[SYS_SOCIAL_005][systems_master.json] |

### cmd_resolve_184.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18400 | 跨服进程信息 | bidirectional | cs: — ／ sc: is_open:uint8; merge_index:uint8; step:uint8; status:uint8; val:uint16; tar_val:uint16 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:跨服进程信息[cmd_table.json] |
| 18401 | 领取个人奖励 | bidirectional | cs: step:uint8 ／ sc: step:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取个人奖励[cmd_table.json] |
| 18402 | 跨服阶段信息 | bidirectional | cs: — ／ sc: step_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:跨服阶段信息[cmd_table.json] |
| 18403 | 领取进程奖励 | bidirectional | cs: step:uint8 ／ sc: step:uint8; code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取进程奖励[cmd_table.json] |
| 18404 | 全服奖励领取情况 | bidirectional | cs: — ／ sc: rewarded_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:全服奖励领取情况[cmd_table.json] |

### cmd_resolve_185.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18500 | 接取循环任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:接取循环任务[cmd_table.json] |
| 18501 | 队长确认邀请配偶进队 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:队长确认邀请配偶进队[cmd_table.json] |
| 18502 | 杀怪寻路信息 | bidirectional | cs: mission_bid:uint32 ／ sc: mission_bid:uint32; map_bid:uint32; x:uint32; y:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪寻路信息[cmd_table.json] |
| 18503 | 跑环杀怪 | bidirectional | cs: mon_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:跑环杀怪[cmd_table.json] |
| 18504 | 杀怪任务成功 | sc | cs: — ／ sc: mission_bid:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:杀怪任务成功[cmd_table.json] |
| 18505 | 触发事件 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:触发事件[cmd_table.json] |

### cmd_resolve_186.luac（15 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18600 | 进入战区 | bidirectional | cs: — ／ sc: code:uint8; msg:string; map_state:uint8; status:uint8 | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入战区[cmd_table.json] |
| 18601 | 退出战区 | bidirectional | cs: — ／ sc: code:uint8; msg:string; map_state:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出战区[cmd_table.json] |
| 18602 | 玩家进入战斗区 | bidirectional | cs: map_index:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玩家进入战斗区[cmd_table.json] |
| 18603 | 战败回到复活区 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战败回到复活区[cmd_table.json] |
| 18604 | 活动阵营信息 | bidirectional | cs: — ／ sc: code:uint8; msg:string; self_camp:uint8; camp_a_score:uint32; camp_a_num:uint8; camp_b_score:uint32; camp_b_num:uint8; add_score:uint32; score:uint32; base_score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动阵营信息[cmd_table.json] |
| 18605 | 战区玩家仙桃排行榜 | bidirectional | cs: — ／ sc: code:uint8; msg:string; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战区玩家仙桃排行榜[cmd_table.json] |
| 18606 | 上缴仙桃 | bidirectional | cs: num:int16 ／ sc: code:uint8; msg:string; add_score:uint32; score:uint32; base_score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上缴仙桃[cmd_table.json] |
| 18607 | 挑战玩家 | bidirectional | cs: rid:int32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战玩家[cmd_table.json] |
| 18608 | 战斗结束 | bidirectional | cs: — ／ sc: type:uint8; msg:string; bat_res:uint8; win_score:int32; new_score:uint32; base_score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结束[cmd_table.json] |
| 18609 | 结算排行榜 | bidirectional | cs: — ／ sc: camp_a_score:uint32; camp_a_num:uint8; camp_b_score:uint32; camp_b_num:uint8; add_score:uint32; self_camp:uint8; role_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结算排行榜[cmd_table.json] |
| 18610 | 攻击怪物 | bidirectional | cs: mod_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:攻击怪物[cmd_table.json] |
| 18611 | 推送玩家积分变化(采集物品时推送) | bidirectional | cs: — ／ sc: score:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送玩家积分变化(采集物品时推送)[cmd_table.json] |
| 18612 | 推送阵营积分变化（有玩家提交材料时） | bidirectional | cs: — ／ sc: camp_a_score:uint32; camp_a_num:uint8; camp_b_score:uint32; camp_b_num:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送阵营积分变化（有玩家提交材料时）[cmd_table.json] |
| 18613 | 推送活动状态和剩余时间 | bidirectional | cs: — ／ sc: status:uint8; sec:uint32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送活动状态和剩余时间[cmd_table.json] |
| 18614 | 推送阵营数据 | bidirectional | cs: — ／ sc: self_camp:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送阵营数据[cmd_table.json] |

### cmd_resolve_187.luac（35 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18700 | 获取阵法信息 | bidirectional | cs: flag:uint8 ／ sc: flag:uint8; select_type:uint8; info_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取阵法信息[cmd_table.json] |
| 18701 | 设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_id:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设置阵位[cmd_table.json] |
| 18702 | 取消设置阵位 | bidirectional | cs: flag:uint8; type:uint8; pos:uint8; hero_id:uint32; rid:uint32; srv_id:string ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消设置阵位[cmd_table.json] |
| 18703 | 选中某个阵法 | bidirectional | cs: flag:uint8; type:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; s_type:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:选中某个阵法[cmd_table.json] |
| 18706 | 英雄助阵 | bidirectional | cs: flag:uint8; hero_id:uint32; pos:uint8 ／ sc: tips:uint16; msg:string; flag:uint8; cheer_hero:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:英雄助阵[cmd_table.json] |
| 18707 | 取消英雄助阵 | bidirectional | cs: flag:uint8; hero_id:uint32 ／ sc: flag:uint8; cheer_hero:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消英雄助阵[cmd_table.json] |
| 18708 | 双击设置阵位 | bidirectional | cs: flag:uint8; type:uint8; rid:uint32; srv_id:string; hero_id:uint32 ／ sc: tips:uint16; msg:string; flag:uint8; pos_info:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:双击设置阵位[cmd_table.json] |
| 18709 | 派出伙伴 | bidirectional | cs: partner_id:uint32 ／ sc: code:uint8; tips:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:派出伙伴[cmd_table.json] |
| 18710 | 获取雇佣伙伴列表 | bidirectional | cs: — ／ sc: code:uint8; tips:string; refresh_times:uint8; partner_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取雇佣伙伴列表[cmd_table.json] |
| 18711 | 刷新雇佣列表 | bidirectional | cs: — ／ sc: code:uint8; tips:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新雇佣列表[cmd_table.json] |
| 18712 | 雇佣伙伴 | bidirectional | cs: rid:uint32; srv_id:string; partner_id:uint32 ／ sc: code:uint8; tips:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:雇佣伙伴[cmd_table.json] |
| 18713 | 查看雇佣伙伴 | bidirectional | cs: rid:uint32; srv_id:string; partner_id:uint32 ／ sc: code:uint8; tips:string; rid:uint32; srv_id:string; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看雇佣伙伴[cmd_table.json] |
| 18714 | 获取已雇佣伙伴 | bidirectional | cs: — ／ sc: rid:uint32; srv_id:string; partner_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取已雇佣伙伴[cmd_table.json] |
| 18715 | 购买抢购物品 | bidirectional | cs: — ／ sc: code:uint8; tips:string; goods_index:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买抢购物品[cmd_table.json] |
| 18716 | 获取英雄助阵信息 | bidirectional | cs: flag:uint8 ／ sc: flag:uint8; cheer_hero:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取英雄助阵信息[cmd_table.json] |
| 18730 | 打开界面 | bidirectional | cs: — ／ sc: map_id:uint8; grid:uint8; record_list:table; chip_num:uint16; change_list:table; run_times:uint8; next_time:uint32; list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开界面[cmd_table.json] |
| 18731 | 掷色子 | bidirectional | cs: — ／ sc: code:uint8; msg:string; run_point:uint8; map_id:uint8; from_grid:uint8; to_grid:uint8; add_chip:uint8; chip_num:uint16; next_time:uint32; run_times:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:掷色子[cmd_table.json] |
| 18732 | 前端行走完毕通知服务端 | bidirectional | cs: map_id:uint8; to_grid:uint8 ／ sc: code:uint8; rand_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:前端行走完毕通知服务端[cmd_table.json] |
| 18733 | 碎片兑换奖励 | bidirectional | cs: id:uint8 ／ sc: code:uint8; msg:string; chip_num:uint16; id:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:碎片兑换奖励[cmd_table.json] |
| 18734 | 通知增加摇骰次数 | sc | cs: — ／ sc: run_times:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知增加摇骰次数[cmd_table.json] |
| 18735 | 获取buff列表 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取buff列表[cmd_table.json] |
| 18736 | 激活buff | bidirectional | cs: buff_bid:uint32 ／ sc: code:uint8; msg:string; buff_bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活buff[cmd_table.json] |
| 18737 | 推送获得buff | sc | cs: — ／ sc: buff_bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送获得buff[cmd_table.json] |
| 18750 | 打开界面 | bidirectional | cs: — ／ sc: end_time:uint32; boss_hp:uint32; status:uint8; boss_bid:uint32; max_hp:uint32; boss_time:uint32; role_time:uint32; info_list:table; self_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开界面[cmd_table.json] |
| 18751 | 活动个人积分 | bidirectional | cs: career:uint8; ord:uint8; num:uint8; flag:uint8 ／ sc: career:uint8; my_ord:uint16; carrer_rank:uint16; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动个人积分[cmd_table.json] |
| 18752 | 活动帮会积分 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_guild:string; gid:uint32; gsrv_id:string; role_num:uint8; host_name:string; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动帮会积分[cmd_table.json] |
| 18753 | 获取抢夺列表 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取抢夺列表[cmd_table.json] |
| 18754 | 全服事件列表 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:全服事件列表[cmd_table.json] |
| 18755 | 个人事件列表 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人事件列表[cmd_table.json] |
| 18756 | 挑战玩家 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; protect_time:uint32; rid:uint32; srv_id:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战玩家[cmd_table.json] |
| 18757 | 对战玩家挑战结果 | sc | cs: — ／ sc: bat_res:uint8; full_hurt:uint32; my_hurt:uint32; hero_list:table; target_name:string; target_rid:uint32; target_srv_id:string; target_career:uint8; target_sex:uint8; target_hurt:uint32; target_hero_list:table; win_score:int32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对战玩家挑战结果[cmd_table.json] |
| 18758 | 挑战boss | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战boss[cmd_table.json] |
| 18759 | 挑战boss战斗结果 | sc | cs: — ／ sc: bat_res:uint8; full_hurt:uint32; my_hurt:uint32; hero_list:table; win_score:int32; mon_hurt_list:table; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战boss战斗结果[cmd_table.json] |
| 18760 | 获取boss血量 | bidirectional | cs: — ／ sc: boss_hp:uint32; max_hp:uint32; status:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取boss血量[cmd_table.json] |
| 18761 | 通知活动结束退出战斗 | sc | cs: — ／ sc: — | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知活动结束退出战斗[cmd_table.json] |

### cmd_resolve_188.luac（33 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18800 | 进入大厅 | bidirectional | cs: — ／ sc: code:uint8; msg:string; hall_index:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入大厅[cmd_table.json] |
| 18801 | 退出大厅 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出大厅[cmd_table.json] |
| 18802 | 报名参战 | bidirectional | cs: type:uint8 ／ sc: type:uint8; code:uint8; msg:string; match_flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:报名参战[cmd_table.json] |
| 18803 | 个人信息 | bidirectional | cs: — ／ sc: rest_time:uint8; win_times:uint16; total_times:uint16; score:uint32; win_reward_flag:uint8; time_reward_flag:uint8; rank:uint32; end_time:uint32; match_flag:uint8; daily_times:uint16; up_bat_list:table; peak_index:uint16; cont_win_times:uint16; max_score:uint32 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:个人信息[cmd_table.json] |
| 18804 | 匹配结果 | bidirectional | cs: — ／ sc: code:uint8; msg:string; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:匹配结果[cmd_table.json] |
| 18805 | 战斗结果 | sc | cs: — ／ sc: code:uint8; msg:string; bat_result:uint8; reward_box_bid:uint32; is_up_suc:uint8; up_bat_list:table; battle_role:table; role_hurl_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结果[cmd_table.json] |
| 18806 | 排行榜 | bidirectional | cs: type:uint8; career:uint8 ／ sc: type:uint8; career:uint8; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:排行榜[cmd_table.json] |
| 18807 | 右侧栏信息 | bidirectional | cs: — ／ sc: score:uint32; hall_index:uint8; match_flag:uint8; daily_times:uint16; hall_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:右侧栏信息[cmd_table.json] |
| 18808 | 段位说明界面 | bidirectional | cs: — ／ sc: score:uint32; reward_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:段位说明界面[cmd_table.json] |
| 18809 | 获取历史战报 | bidirectional | cs: — ／ sc: battle_record:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取历史战报[cmd_table.json] |
| 18810 | 推送战报 | sc | cs: — ／ sc: battle_record:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送战报[cmd_table.json] |
| 18811 | 领取首次胜利奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取首次胜利奖励[cmd_table.json] |
| 18812 | 领取十次战斗奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取十次战斗奖励[cmd_table.json] |
| 18813 | 大厅跳转 | bidirectional | cs: hall_index:uint8 ／ sc: code:uint8; msg:string; hall_index:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:大厅跳转[cmd_table.json] |
| 18814 | 领取段位阶段奖励 | bidirectional | cs: grade:uint8 ／ sc: code:uint8; msg:string; reward_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取段位阶段奖励[cmd_table.json] |
| 18815 | 查找个人信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; win_times:uint16; total_times:uint16; score:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查找个人信息[cmd_table.json] |
| 18820 | 进入公共场景 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入公共场景[cmd_table.json] |
| 18821 | 退出公共场景 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出公共场景[cmd_table.json] |
| 18823 | 副本关卡信息 | sc | cs: — ／ sc: dungeon_bid:uint32; index:uint8; type:uint8; mon_list:table; rest_time:uint32; reward_flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本关卡信息[cmd_table.json] |
| 18826 | 激活铜人阵 | bidirectional | cs: — ／ sc: code:uint8; msg:string; floor:uint8; rest_time:uint32; kill_number:uint16; win_coin:uint32; rest_wave:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活铜人阵[cmd_table.json] |
| 18827 | 获取封魔录霸主名单 | bidirectional | cs: — ／ sc: role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取封魔录霸主名单[cmd_table.json] |
| 18828 | 雕像数据 | bidirectional | cs: dun_bid:uint32 ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string; name:string; career:uint8; sex:uint8; lev:uint8; power:uint32; disagree:uint16; animate_res:table; items:table; team_member:table; floor:uint8; use_sec:uint32; my_floor:uint8; my_use_sec:uint32; my_count:uint8; leader_name:string; my_team_member:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:雕像数据[cmd_table.json] |
| 18829 | 雕像砸鸡蛋 | bidirectional | cs: dun_bid:uint32 ／ sc: code:uint8; msg:string; dun_bid:uint32; disagree:uint16; my_count:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:雕像砸鸡蛋[cmd_table.json] |
| 18833 | 屈原副本关卡信息 | sc | cs: — ／ sc: dungeon_bid:uint32; index:uint8; type:uint8; mon_list:table; rest_time:uint32; reward_flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:屈原副本关卡信息[cmd_table.json] |
| 18861 | 进入场景 | bidirectional | cs: is_cross:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入场景[cmd_table.json] |
| 18862 | 退出场景 | bidirectional | cs: is_cross:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出场景[cmd_table.json] |
| 18863 | 挑战玩家 | bidirectional | cs: is_cross:uint8; rid:uint32; string:string ／ sc: code:uint8; msg:string; rid:uint32; string:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战玩家[cmd_table.json] |
| 18864 | 场景信息 | bidirectional | cs: is_cross:uint8 ／ sc: floor:uint8; score:uint32; dan_score:uint32; end_time:uint32; reward_flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:场景信息[cmd_table.json] |
| 18865 | 总结算排行榜 | bidirectional | cs: is_cross:uint8; career:uint8; ord:uint8; num:uint8 ／ sc: career:uint8; ord:uint8; num:uint8; rank:uint16; total_score:uint32; score:uint32; dan_score:uint32; max_floor:uint8; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:总结算排行榜[cmd_table.json] |
| 18866 | 推送积分变化 | sc | cs: — ／ sc: score:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送积分变化[cmd_table.json] |
| 18867 | 推送获得称号 | sc | cs: — ／ sc: title_bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送获得称号[cmd_table.json] |
| 18868 | 领取层数礼包 | bidirectional | cs: — ／ sc: code:uint8; msg:string; reward_flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取层数礼包[cmd_table.json] |
| 18886 | 查看其他玩家信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; role_name:string; career:uint8; sex:uint8; win_times:uint16; total_times:uint16; score:uint32; index:uint16; end_time:uint32; cont_win_times:uint16; best_friend:string; max_score:uint32; kill_num:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看其他玩家信息[cmd_table.json] |

### cmd_resolve_189.luac（12 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 18900 | 法宝信息 | bidirectional | cs: — ／ sc: coin_times:uint16; power:uint16; fabao_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:法宝信息[cmd_table.json] |
| 18901 | 激活法宝 | bidirectional | cs: bid:uint32 ／ sc: result:uint8; bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活法宝[cmd_table.json] |
| 18902 | 穿戴法宝 | bidirectional | cs: bid:uint32 ／ sc: result:uint8; bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:穿戴法宝[cmd_table.json] |
| 18903 | 卸下法宝 | bidirectional | cs: bid:uint32 ／ sc: result:uint8; bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:卸下法宝[cmd_table.json] |
| 18904 | 法宝效果置换 | bidirectional | cs: bid:uint32; stage:uint8 ／ sc: result:uint8; bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:法宝效果置换[cmd_table.json] |
| 18905 | 法宝升阶 | bidirectional | cs: bid:uint32 ／ sc: result:uint8; bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝升阶[cmd_table.json] |
| 18906 | 法宝加经验 | bidirectional | cs: bid:uint32; type:uint8; value:uint16 ／ sc: result:uint8; bid:uint32; pre_level:uint16; post_level:uint16; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝加经验[cmd_table.json] |
| 18907 | 法宝信息(更新单个信息) | sc | cs: — ／ sc: coin_times:uint16; power:uint16; fabao_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝信息(更新单个信息)[cmd_table.json] |
| 18908 | 分解 | bidirectional | cs: item_bid:uint32; count:uint16 ／ sc: result:uint8; item_bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分解[cmd_table.json] |
| 18909 | 法宝商店信息 | bidirectional | cs: — ／ sc: buy_list:table | SYS_ECON_005 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:法宝商店信息[cmd_table.json]；所属系统:Trade Market 市场/交易[SYS_ECON_005][systems_master.json] |
| 18910 | 法宝商店购买 | bidirectional | cs: id:uint32; count:uint16 ／ sc: result:uint8; id:uint32; count:uint16; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:法宝商店购买[cmd_table.json] |
| 18911 | 查看他人的法宝信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: result:uint8; msg:string; power:uint32; fabao_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:查看他人的法宝信息[cmd_table.json] |

### cmd_resolve_190.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19000 | 玩家宝箱背包 | bidirectional | cs: — ／ sc: box_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:玩家宝箱背包[cmd_table.json] |
| 19001 | 获取某个来源宝箱 | bidirectional | cs: from:uint8 ／ sc: code:uint8; msg:string; from:uint8; box_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取某个来源宝箱[cmd_table.json] |
| 19002 | 解锁宝箱 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32; dtime:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:解锁宝箱[cmd_table.json] |
| 19003 | 打开宝箱 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开宝箱[cmd_table.json] |
| 19004 | 宝箱信息推送 | sc | cs: — ／ sc: type:uint8; box_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝箱信息推送[cmd_table.json] |
| 19005 | 宝箱加速 | bidirectional | cs: id:uint32 ／ sc: code:uint8; msg:string; id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宝箱加速[cmd_table.json] |

### cmd_resolve_191.luac（8 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19100 | 光环信息 | bidirectional | cs: — ／ sc: stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; looks:table; surface_star:table | SYS_APPEAR_010 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:光环信息[cmd_table.json]；所属系统:Halo 光环[SYS_APPEAR_010][systems_master.json] |
| 19101 | 升阶 | bidirectional | cs: — ／ sc: result:uint8; msg:string; stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升阶[cmd_table.json] |
| 19102 | 转换资源 | bidirectional | cs: type:uint8; args:uint32 ／ sc: result:uint8; msg:string; type:uint8; args:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转换资源[cmd_table.json] |
| 19103 | 光环装备穿戴 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | SYS_APPEAR_010 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:光环装备穿戴[cmd_table.json]；所属系统:Halo 光环[SYS_APPEAR_010][systems_master.json] |
| 19104 | 脱装备 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | SYS_APPEAR_010 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:脱装备[cmd_table.json]；所属系统:Halo 光环[SYS_APPEAR_010][systems_master.json] |
| 19108 | 装备吞噬 | bidirectional | cs: item_id_lev:uint32; item_id_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备吞噬[cmd_table.json] |
| 19120 | 魂环升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:魂环升星[cmd_table.json] |
| 19199 | 激活幻化外观 | bidirectional | cs: look_id:uint32 ／ sc: result:uint8; msg:string; look_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活幻化外观[cmd_table.json] |

### cmd_resolve_192.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19200 | UNKNOWN | bidirectional | cs: — ／ sc: code:uint8; msg:string; current_pos:uint8; total_steps:uint32; step_box:table; already_roll_count:uint32; remain_free_count:uint8; events:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 19201 | UNKNOWN | bidirectional | cs: count:uint8; args:uint8 ／ sc: result:uint8; msg:string; step_info:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | UNKNOWN |
| 19202 | UNKNOWN | bidirectional | cs: step_bid:uint8 ／ sc: result:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | UNKNOWN |

### cmd_resolve_194.luac（16 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19400 | 命格背包信息 | bidirectional | cs: bagcode:uint8 ／ sc: bag_code:uint8; mingge_stage:uint8; mingge_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:命格背包信息[cmd_table.json] |
| 19401 | 命格数据变更协议 | sc | cs: — ／ sc: bag_code:uint8; mingge_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格数据变更协议[cmd_table.json] |
| 19402 | 命格穿戴 | bidirectional | cs: src_bag_code:uint8; mingge_id:uint32; id:uint32; pos:uint8 ／ sc: code:uint8; msg:string; src_bag_code:uint8; target_bag_code:uint8; mingge_id:uint32; id:uint32; pos:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格穿戴[cmd_table.json] |
| 19403 | 命格脱下 | bidirectional | cs: src_bag_code:uint8; mingge_id:uint32 ／ sc: code:uint8; msg:string; src_bag_code:uint8; target_bag_code:uint8; mingge_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格脱下[cmd_table.json] |
| 19404 | 命格删除协议 | bidirectional | cs: bag_code:uint8; del_ids_arr:table ／ sc: code:uint8; msg:string; bag_code:uint8; del_ids_arr:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格删除协议[cmd_table.json] |
| 19405 | 命格升级 | bidirectional | cs: bag_code:uint8; mingge_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; mingge_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格升级[cmd_table.json] |
| 19406 | 查询魂力数据 | bidirectional | cs: — ／ sc: soul:uint16; soul_max:uint16; coin_type:uint8; price:uint32; is_tick:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:查询魂力数据[cmd_table.json] |
| 19407 | 购买魂力 | bidirectional | cs: — ／ sc: code:uint8; msg:string; val:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买魂力[cmd_table.json] |
| 19408 | 打勾自动补充魂力 | bidirectional | cs: is_tick:uint8 ／ sc: code:uint8; msg:string; is_tick:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打勾自动补充魂力[cmd_table.json] |
| 19409 | 境界突破 | bidirectional | cs: — ／ sc: code:uint8; msg:string; mingge_stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:境界突破[cmd_table.json] |
| 19410 | 共鸣开孔/重置 | bidirectional | cs: bag_code:uint8; mingge_id:uint32; hole:uint8 ／ sc: code:uint8; msg:string; bag_code:uint8; mingge_id:uint32; hole:uint8; mingge_bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:共鸣开孔/重置[cmd_table.json] |
| 19411 | 命格分解 | bidirectional | cs: bag_code:uint8; mingge_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; mingge_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格分解[cmd_table.json] |
| 19412 | 命格炼化 | bidirectional | cs: bag_code:uint8; ids:table ／ sc: code:uint8; msg:string; bag_code:uint8; mingge_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格炼化[cmd_table.json] |
| 19413 | 命格出售 | bidirectional | cs: bag_code:uint8; mingge_id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; mingge_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格出售[cmd_table.json] |
| 19414 | 查看玩家命格信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; mingge_stage:uint8; role_mingge_list:table; partner_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看玩家命格信息[cmd_table.json] |
| 19499 | 伙伴换装 | bidirectional | cs: partner_id:uint32; pos:uint8; swap_partner_id:uint32; swap_pos:uint8 ／ sc: code:uint8; partner_id:uint32; pos:uint8; swap_partner_id:uint32; swap_pos:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:伙伴换装[cmd_table.json] |

### cmd_resolve_195.luac（35 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19500 | 接结义任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:接结义任务[cmd_table.json] |
| 19501 | 挑战结义副本 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挑战结义副本[cmd_table.json] |
| 19505 | 队长发起结拜 | bidirectional | cs: — ／ sc: code:uint8; msg:string | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:队长发起结拜[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19506 | 通知队员界面信息 | sc | cs: — ／ sc: code:uint8; msg:string; member_list:table; end_time:uint32; member_len:uint8; vote_sort:uint8; vote_flag:uint8; is_finish:uint8; notice:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知队员界面信息[cmd_table.json] |
| 19507 | 大哥设置名字 | bidirectional | cs: front_name:string; end_name:string ／ sc: code:uint8; msg:string; front_name:string; end_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:大哥设置名字[cmd_table.json] |
| 19508 | 通知队员更新称号名字 | sc | cs: — ／ sc: code:uint8; msg:string; front_name:string; end_name:string; end_time:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知队员更新称号名字[cmd_table.json] |
| 19509 | 结拜成员设置称号名0字 | bidirectional | cs: second_name:string ／ sc: code:uint8; msg:string; second_name:string | SYS_SOCIAL_004 | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结拜成员设置称号名0字[cmd_table.json]；所属系统:Guild 公会[SYS_SOCIAL_004][systems_master.json] |
| 19510 | 广播其他成员设置的称号 | sc | cs: — ／ sc: rid:uint32; srv_id:string; second_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:广播其他成员设置的称号[cmd_table.json] |
| 19511 | 通知成员开始确认结拜 | sc | cs: — ／ sc: code:uint8; msg:string; flag:uint8; member_list:table; end_time:uint32 | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知成员开始确认结拜[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19512 | 结拜成员确认结拜 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结拜成员确认结拜[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19513 | 通知结拜结果 | sc | cs: — ／ sc: code:uint8; msg:string | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知结拜结果[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19514 | 打开结拜空间 | bidirectional | cs: — ／ sc: code:uint8; msg:string; jid:uint32; j_srv_id:string; front_name:string; member_len:uint8; end_name:string; lev:uint8; leader_name:string; exp:uint32; common_notice:string; member_list:table; vote_type:uint8; vote_status:uint8; vote_end_time:uint32; host_rid:uint32; host_srv_id:string; vote_host:string; member_rid:uint32; member_srv_id:string; vote_member:string; vote_list:table | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:打开结拜空间[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19515 | 打开结拜技能界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; skill_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开结拜技能界面[cmd_table.json] |
| 19516 | 升级结拜技能 | bidirectional | cs: skill_bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; lev:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级结拜技能[cmd_table.json] |
| 19517 | 踢出队员 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:踢出队员[cmd_table.json] |
| 19518 | 申请退出 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:申请退出[cmd_table.json] |
| 19519 | 投票 | bidirectional | cs: vote_sort:uint8; rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:投票[cmd_table.json] |
| 19520 | 推送投票结果 | sc | cs: — ／ sc: vote_sort:uint8; rid:uint32; srv_id:string; vote_num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送投票结果[cmd_table.json] |
| 19521 | 推送投票结果 | sc | cs: — ／ sc: vote_type:uint8; vote_status:uint8; vote_end_time:uint32; host_rid:uint32; host_srv_id:string; vote_host:string; member_rid:uint32; member_srv_id:string; vote_member:string; vote_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送投票结果[cmd_table.json] |
| 19522 | 参与投票 | bidirectional | cs: vote_type:uint8; ret:uint8 ／ sc: code:uint8; msg:string; vote_type:uint8; ret:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:参与投票[cmd_table.json] |
| 19523 | 更换公共称号 | bidirectional | cs: front_name:string; end_name:string ／ sc: code:uint8; msg:string; front_name:string; end_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更换公共称号[cmd_table.json] |
| 19524 | 邀请好友加入 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string; rid:uint32; srv_id:string | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:邀请好友加入[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19525 | 收到邀请推送 | sc | cs: — ／ sc: jid:uint32; j_srv_id:string; vote_name:string; front_name:string; member_len:uint8; end_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收到邀请推送[cmd_table.json] |
| 19526 | 回复邀请 | bidirectional | cs: jid:uint32; j_srv_id:string; result:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回复邀请[cmd_table.json] |
| 19527 | 更换结拜宣言 | bidirectional | cs: common_notice:string ／ sc: code:uint8; msg:string; common_notice:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更换结拜宣言[cmd_table.json] |
| 19528 | 更换个人称号 | bidirectional | cs: title_name:string ／ sc: code:uint8; msg:string; title_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更换个人称号[cmd_table.json] |
| 19529 | 取消申请退出 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消申请退出[cmd_table.json] |
| 19530 | 请求打开界面 | bidirectional | cs: — ／ sc: code:uint8; msg:string; member_list:table; end_time:uint32 | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求打开界面[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19531 | 确认玩家列表 | sc | cs: — ／ sc: member_list:table; end_time:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:确认玩家列表[cmd_table.json] |
| 19532 | 确认参与结拜 | bidirectional | cs: ret:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:确认参与结拜[cmd_table.json] |
| 19533 | 取消结拜 | bidirectional | cs: — ／ sc: code:uint8; msg:string | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:取消结拜[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19534 | 结义空间基础信息 | bidirectional | cs: — ／ sc: jid:uint32; j_srv_id:string; front_name:string; member_len:uint8; end_name:string; lev:uint8; exp:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结义空间基础信息[cmd_table.json] |
| 19535 | 结义流程提示语 | sc | cs: — ／ sc: msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结义流程提示语[cmd_table.json] |
| 19536 | 提升结拜空间等级 | bidirectional | cs: — ／ sc: code:uint8; msg:string; jlev:uint8 | SYS_SOCIAL_006 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:提升结拜空间等级[cmd_table.json]；所属系统:Jiebai Soulmate 结拜[SYS_SOCIAL_006][systems_master.json] |
| 19537 | 发起顶替队长投票 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发起顶替队长投票[cmd_table.json] |

### cmd_resolve_196.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19600 | 获取奖励找回信息列表 | bidirectional | cs: type:uint8 ／ sc: type:uint8; list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取奖励找回信息列表[cmd_table.json] |
| 19601 | 领取奖励 | bidirectional | cs: id:uint32; type:uint8; order:uint8 ／ sc: code:uint8; msg:string; id:uint32; type:uint8; order:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |
| 19602 | 奖励找回数据刷新 | sc | cs: — ／ sc: type:uint8; list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:奖励找回数据刷新[cmd_table.json] |
| 19603 | 获取奖励一键找回总花费 | bidirectional | cs: type:uint8 ／ sc: type:uint8; coin_type1:uint8; coin1:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取奖励一键找回总花费[cmd_table.json] |
| 19604 | 奖励找回数据刷新 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; type:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:奖励找回数据刷新[cmd_table.json] |

### cmd_resolve_199.luac（6 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 19900 | 获取答题数据 | sc | cs: — ／ sc: code:uint8; msg:string; state:uint8; question_id:uint32; end_time:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取答题数据[cmd_table.json] |
| 19901 | 答题 | bidirectional | cs: question_id:uint32; answer:uint8 ／ sc: msg:string; right_answer:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:答题[cmd_table.json] |
| 19902 | 获取房间数据 | bidirectional | cs: — ／ sc: code:uint8; msg:string; round:uint8; status:uint8; end_time:uint32; role_num:uint8; balloon_num:uint8; right_num:uint8; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取房间数据[cmd_table.json] |
| 19903 | 退出抢气球活动场景 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出抢气球活动场景[cmd_table.json] |
| 19904 | 进入抢气球活动场景 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入抢气球活动场景[cmd_table.json] |
| 19905 | 推送获得抢气球活动资格 | sc | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送获得抢气球活动资格[cmd_table.json] |

### cmd_resolve_200.luac（25 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20001 | 对角色发起战斗 | bidirectional | cs: rid:int32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对角色发起战斗[cmd_table.json] |
| 20002 | 对怪物发起战斗 | bidirectional | cs: mon_id:int32 ／ sc: code:uint8; msg:string | SYS_BATTLE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:对怪物发起战斗[cmd_table.json]；所属系统:Turn-based Battle[SYS_BATTLE_001][systems_master.json] |
| 20003 | 测试战斗 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:测试战斗[cmd_table.json] |
| 20004 | 发起切磋 | bidirectional | cs: rid:int32; srv_id:string; name:string ／ sc: name:string; rid:int32; srv_id:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发起切磋[cmd_table.json] |
| 20005 | 确认切磋 | cs | cs: result:int8; rid:int32; srv_id:string ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:确认切磋[cmd_table.json] |
| 20008 | 自动战斗 | bidirectional | cs: flag:uint8 ／ sc: id:int8; flag:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自动战斗[cmd_table.json] |
| 20009 | 使用技能 | bidirectional | cs: skill_id:int32 ／ sc: skill_id:int32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用技能[cmd_table.json] |
| 20010 | 战斗初始化数据 | bidirectional | cs: — ／ sc: round:uint16; round_wave:uint16; wave_max:uint16; wave_no:uint16; atk_formation_type:uint8; atk_formation_lev:uint8; def_formation_type:uint8; def_formation_lev:uint8; is_observer:uint8; effect_id:string; order_list:table; fighter_info_list:table | SYS_BATTLE_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗初始化数据[cmd_table.json]；所属系统:Turn-based Battle[SYS_BATTLE_001][systems_master.json] |
| 20011 | 客户端加载完成 | cs | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:客户端加载完成[cmd_table.json] |
| 20012 | 小回合战斗效果 | sc | cs: — ／ sc: round:uint16; skill_play:table; cooldown:table | SYS_GROWTH_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:小回合战斗效果[cmd_table.json]；所属系统:Skill System[SYS_GROWTH_001][systems_master.json] |
| 20013 | 回合开始 | sc | cs: — ／ sc: round:uint16; round_wave:uint16; time:uint8; wave_no:uint8; magic_play:table; summon_play:table; order_list:table | SYS_BATTLE_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回合开始[cmd_table.json]；所属系统:Turn-based Battle[SYS_BATTLE_001][systems_master.json] |
| 20014 | 客户端动画播放完成通知 | cs | cs: — ／ sc: — | SYS_BATTLE_001 | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:客户端动画播放完成通知[cmd_table.json]；所属系统:Turn-based Battle[SYS_BATTLE_001][systems_master.json] |
| 20015 | 新增战斗对象 | sc | cs: — ／ sc: fighter_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:新增战斗对象[cmd_table.json] |
| 20016 | 申请观战 | bidirectional | cs: rid:int32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:申请观战[cmd_table.json] |
| 20017 | 退出观战 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出观战[cmd_table.json] |
| 20020 | 战斗结果 | sc | cs: — ／ sc: result:uint8 | SYS_BATTLE_001 | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结果[cmd_table.json]；所属系统:Turn-based Battle[SYS_BATTLE_001][systems_master.json] |
| 20021 | 闭关战斗结束界面 | cs | cs: — ／ sc: — | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:闭关战斗结束界面[cmd_table.json] |
| 20022 | 显示战斗结束界面 | sc | cs: — ／ sc: icon_list:table | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:显示战斗结束界面[cmd_table.json] |
| 20023 | 显示战斗伤害信息 | sc | cs: — ／ sc: type:uint8; result:uint8; role_hurl_list:table; val_list:table; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:显示战斗伤害信息[cmd_table.json] |
| 20025 | 获取战斗录像 | bidirectional | cs: id:string; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取战斗录像[cmd_table.json] |
| 20026 | 获取战斗录像大小 | bidirectional | cs: id:string; srv_id:string ／ sc: size:int32 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取战斗录像大小[cmd_table.json] |
| 20027 | 停止播放录像 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:停止播放录像[cmd_table.json] |
| 20028 | 录像列表 | bidirectional | cs: type:uint8 ／ sc: type:uint8; replay_list:table | UNKNOWN | ✓ | ✓ | ✓ | VERIFIED | cmd_table中文名:录像列表[cmd_table.json] |
| 20029 | 战斗录像锁定 | bidirectional | cs: id:string; lock:uint8 ／ sc: code:uint8; msg:string; id:string; lock:uint8 | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗录像锁定[cmd_table.json] |
| 20030 | 分享战斗录像 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✓ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分享战斗录像[cmd_table.json] |

### cmd_resolve_201.luac（1 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20100 | 我要变强界面 | bidirectional | cs: — ／ sc: power:table; promote:table | SYS_CORE_007 | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:我要变强界面[cmd_table.json]；所属系统:Version/Resource Update[SYS_CORE_007][systems_master.json] |

### cmd_resolve_202.luac（13 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20200 | 获取我的矿洞数据 | bidirectional | cs: — ／ sc: search_times:uint8; rob_times:uint8; occupy_time:uint8; occupy_num:uint8; mine_list:table; search_cost:uint32; hero_exp:uint32; search_assets:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取我的矿洞数据[cmd_table.json] |
| 20201 | 勘探矿洞 | bidirectional | cs: index:uint8; type:uint8 ／ sc: code:uint8; msg:string; index:uint32; type:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:勘探矿洞[cmd_table.json] |
| 20202 | 占领矿洞 | bidirectional | cs: op_type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:占领矿洞[cmd_table.json] |
| 20203 | 收取矿洞资源 | bidirectional | cs: index:uint8 ／ sc: code:uint8; msg:string; assets:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取矿洞资源[cmd_table.json] |
| 20204 | 可掠夺矿洞列表 | bidirectional | cs: — ／ sc: search_times:uint8; rob_times:uint8; occupy_time:uint8; occupy_num:uint8; reward:table; search_cost:uint32; hero_exp:uint32; search_assets:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:可掠夺矿洞列表[cmd_table.json] |
| 20205 | 掠夺矿洞资源 | bidirectional | cs: challenge_id:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:掠夺矿洞资源[cmd_table.json] |
| 20206 | 搜索可掠夺矿洞 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:搜索可掠夺矿洞[cmd_table.json] |
| 20207 | 查看矿洞被掠夺记录 | bidirectional | cs: index:uint8 ／ sc: index:uint8; rob_record:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看矿洞被掠夺记录[cmd_table.json] |
| 20208 | 刷新单个我的矿洞数据 | sc | cs: — ／ sc: search_times:uint8; rob_times:uint8; occupy_time:uint8; occupy_num:uint8; mine_list:table; search_cost:uint32; hero_exp:uint32; search_assets:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新单个我的矿洞数据[cmd_table.json] |
| 20209 | 刷新单个可掠夺矿洞数据 | sc | cs: — ／ sc: search_times:uint8; rob_times:uint8; occupy_time:uint8; occupy_num:uint8; challenge_id:uint8; rid:uint32; srv_id:string; role_name:string; role_lev:uint8; sex:uint8; career:uint8; mine_bid:uint32; type:uint8; color:uint8; pos_x:uint16; pos_y:uint16; flag:uint8; defend_succ_times:uint16; tot_defend_times:uint16; reward:table; formation:table; mine_type:uint8; index:uint8; mine_endtime:uint32; status:uint8; loss_list:table; gain_list:table; occupy_cnt:uint16; search_cost:uint32; hero_exp:uint32; search_assets:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新单个可掠夺矿洞数据[cmd_table.json] |
| 20210 | 推送掠夺战斗结算 | sc | cs: — ／ sc: code:uint8; mine_bid:uint32; type:uint32; color:uint32; occupy_num:uint8; rest_num:uint8; reward:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送掠夺战斗结算[cmd_table.json] |
| 20211 | 收取矿洞资源(伙伴经验矿) | bidirectional | cs: index:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取矿洞资源(伙伴经验矿)[cmd_table.json] |
| 20212 | 收取掠夺的伙伴经验 | bidirectional | cs: partner_id:uint32 ／ sc: code:uint8; msg:string; hero_exp:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取掠夺的伙伴经验[cmd_table.json] |

### cmd_resolve_203.luac（15 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20300 | 获取矿区矿洞数据 | bidirectional | cs: — ／ sc: code:uint8; msg:string; rob_times:uint8; occupy_num:uint8; max_scene:uint8; my_scene:table; scene_index:uint8; mine_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取矿区矿洞数据[cmd_table.json] |
| 20301 | 查看矿洞详细信息 | bidirectional | cs: id:uint32; msrv_id:string ／ sc: code:uint8; msg:string; type:uint8; id:uint32; msrv_id:string; index:uint8; bid:uint8; quality:uint8; rid:uint32; srv_id:string; name:string; gname:string; val:uint32; rob_val:uint32; end_time:uint32; lose_count:uint16; win_count:uint32; rest_sec:uint32; role_lev:uint8; sex:uint8; career:uint8; face_id:uint32; formation:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看矿洞详细信息[cmd_table.json] |
| 20302 | 占领矿洞 | bidirectional | cs: id:uint32; msrv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:占领矿洞[cmd_table.json] |
| 20303 | 收取矿洞资源 | bidirectional | cs: id:uint32; msrv_id:string ／ sc: code:uint8; msg:string; assets_code:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取矿洞资源[cmd_table.json] |
| 20304 | 查看掠夺记录 | bidirectional | cs: — ／ sc: rob_record:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看掠夺记录[cmd_table.json] |
| 20305 | 刷新单个可掠夺矿洞数据 | sc | cs: — ／ sc: id:uint32; msrv_id:string; index:uint8; bid:uint8; quality:uint8; rid:uint32; srv_id:string; name:string; gname:string; val:uint32; rob_val:uint32; end_time:uint32; lose_count:uint16; win_count:uint32; rest_sec:uint32; role_lev:uint8; sex:uint8; career:uint8; face_id:uint32; formation:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:刷新单个可掠夺矿洞数据[cmd_table.json] |
| 20306 | 获取矿区矿洞数据(指定某一屏) | bidirectional | cs: scene_index:uint8 ／ sc: code:uint8; msg:string; scene_index:uint8; mine_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取矿区矿洞数据(指定某一屏)[cmd_table.json] |
| 20307 | 资产列表 | bidirectional | cs: — ／ sc: assets:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:资产列表[cmd_table.json] |
| 20308 | 收取伙伴经验资产 | bidirectional | cs: code:uint8; partner_id:uint32 ／ sc: code:uint8; msg:string; assets:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:收取伙伴经验资产[cmd_table.json] |
| 20309 | 战斗结算界面 | sc | cs: — ／ sc: bat_res:uint8; id:uint32; msrv_id:string; index:uint8; bid:uint8; quality:uint8; rid:uint32; srv_id:string; name:string; gname:string; val:uint32; rob_val:uint32; end_time:uint32; is_save:uint8; rob_times:uint8; occupy_num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战斗结算界面[cmd_table.json] |
| 20310 | 确定占领矿洞 | bidirectional | cs: id:uint32; msrv_id:string; type:uint8 ／ sc: code:uint8; msg:string; id:uint32; msrv_id:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:确定占领矿洞[cmd_table.json] |
| 20311 | 打开排行榜 | bidirectional | cs: — ／ sc: code:uint8; msg:string; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开排行榜[cmd_table.json] |
| 20312 | 推送玩家自己矿洞所在屏数 | bidirectional | cs: — ／ sc: rob_times:uint8; occupy_num:uint8; my_scene:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送玩家自己矿洞所在屏数[cmd_table.json] |
| 20313 | 本周收益历史 | bidirectional | cs: — ／ sc: assets_list:table; loss_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:本周收益历史[cmd_table.json] |
| 20314 | 帮会防守记录 | bidirectional | cs: — ／ sc: record_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮会防守记录[cmd_table.json] |

### cmd_resolve_205.luac（11 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20500 | 获取好友回归数据 | bidirectional | cs: — ／ sc: end_time:uint32; role_id:uint32; srv_id:string; name:string; lev:uint8; sex:uint8; career:uint8; intimacy:uint32 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取好友回归数据[cmd_table.json] |
| 20501 | 获取可招募的好友列表 | bidirectional | cs: — ／ sc: friend_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取可招募的好友列表[cmd_table.json] |
| 20502 | 获取招募人列表 | bidirectional | cs: — ／ sc: recruit_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取招募人列表[cmd_table.json] |
| 20503 | 绑定招募人 | bidirectional | cs: role_id:uint32; srv_id:string ／ sc: code:uint8; msg:string; role_id:uint32; srv_id:string; name:string; lev:uint8; sex:uint8; career:uint8; intimacy:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:绑定招募人[cmd_table.json] |
| 20504 | 获取任务列表 | bidirectional | cs: type:uint8 ／ sc: type:uint8; mission_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取任务列表[cmd_table.json] |
| 20505 | 领取任务奖励 | bidirectional | cs: mission_id:uint32 ／ sc: code:uint8; msg:string; mission_id:uint32; status:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取任务奖励[cmd_table.json] |
| 20506 | 询问是否绑定 | sc | cs: — ／ sc: role_id:uint32; srv_id:string; role_bame:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:询问是否绑定[cmd_table.json] |
| 20507 | 回复是否绑定 | bidirectional | cs: role_id:uint32; srv_id:string; op:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回复是否绑定[cmd_table.json] |
| 20508 | 招募玩家发起绑定 | bidirectional | cs: role_id:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:招募玩家发起绑定[cmd_table.json] |
| 20509 | 询问回归玩家是否绑定 | sc | cs: — ／ sc: role_id:uint32; srv_id:string; role_bame:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:询问回归玩家是否绑定[cmd_table.json] |
| 20510 | 回归玩家回复是否绑定 | bidirectional | cs: role_id:uint32; srv_id:string; op:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:回归玩家回复是否绑定[cmd_table.json] |

### cmd_resolve_207.luac（31 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20700 | 比赛阶段信息 | bidirectional | cs: — ／ sc: flag:uint8; round:uint8; time_start:uint32; time_end:uint32; lev_group:uint16; team_index:uint16; team_id:uint32; team_srv_id:string; is_leader:uint8; leader_rid:uint32; leader_srv_id:string; leader_name:string; is_fight:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:比赛阶段信息[cmd_table.json] |
| 20701 | 战事安排信息 | bidirectional | cs: — ／ sc: index:uint16; flag:uint8; round:uint8; register_start:uint32; register_end:uint32; notice_start:uint32; notice_end:uint32; flag_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战事安排信息[cmd_table.json] |
| 20702 | 自己战队信息 | bidirectional | cs: — ／ sc: flag:uint8; win_count:uint16; fail_count:uint16; team_id:uint32; team_srv_id:string; team_name:string; team_power:uint32; rank:uint16; member_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自己战队信息[cmd_table.json] |
| 20703 | 战队申请列表 | bidirectional | cs: start:uint16; len:uint16 ／ sc: start:uint16; len:uint16; total_num:uint16; apply_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战队申请列表[cmd_table.json] |
| 20704 | 按条件搜索战队列表 | bidirectional | cs: team_name:string ／ sc: team_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:按条件搜索战队列表[cmd_table.json] |
| 20705 | 同意队员加入 | bidirectional | cs: rid:uint32; srv_id:string; type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:同意队员加入[cmd_table.json] |
| 20706 | 战队列表 | bidirectional | cs: start:uint16; len:uint16 ／ sc: start:uint16; len:uint16; total_num:uint16; team_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:战队列表[cmd_table.json] |
| 20707 | 创建战队 | bidirectional | cs: team_name:string ／ sc: code:uint8; msg:string; team_name:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:创建战队[cmd_table.json] |
| 20708 | 查看信息 | bidirectional | cs: team_id:uint32; team_srv_id:string ／ sc: win_count:uint16; fail_count:uint16; team_name:string; team_power:uint32; rank:uint16; member_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看信息[cmd_table.json] |
| 20709 | 申请加入 | bidirectional | cs: team_id:uint32; team_srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:申请加入[cmd_table.json] |
| 20710 | 取消申请 | bidirectional | cs: team_id:uint32; team_srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消申请[cmd_table.json] |
| 20711 | 邀请加入战队 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:邀请加入战队[cmd_table.json] |
| 20712 | 取消邀请 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消邀请[cmd_table.json] |
| 20713 | 同意、拒绝邀请 | bidirectional | cs: team_id:uint32; team_srv_id:string; type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:同意、拒绝邀请[cmd_table.json] |
| 20714 | 踢队员 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:踢队员[cmd_table.json] |
| 20715 | 离开战队 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:离开战队[cmd_table.json] |
| 20716 | 解散战队 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:解散战队[cmd_table.json] |
| 20717 | 自己战队的下一场对战信息 | bidirectional | cs: — ／ sc: flag:uint8; round:uint8; start_time:uint32; end_time:uint32; team_name:string; member_list:table; enemy_team_name:string; enemy_member_list:table; next_start_time:uint32; fight_state:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自己战队的下一场对战信息[cmd_table.json] |
| 20718 | 请求沙场信息(小组赛) | bidirectional | cs: lev_group:uint8 ／ sc: lev_group:uint8; group_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求沙场信息(小组赛)[cmd_table.json] |
| 20719 | 请求沙场信息(复活赛) | bidirectional | cs: lev_group:uint8; index:uint8 ／ sc: lev_group:uint8; index:uint8; is_win:uint8; team_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求沙场信息(复活赛)[cmd_table.json] |
| 20720 | 请求沙场信息（淘汰赛） | bidirectional | cs: lev_group:uint8; index:uint8 ／ sc: lev_group:uint8; index:uint8; team_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求沙场信息（淘汰赛）[cmd_table.json] |
| 20721 | 请求沙场信息（决赛） | bidirectional | cs: lev_group:uint8 ／ sc: flag:uint8; round:uint8; lev_group:uint8; team_list:table; team_list2:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求沙场信息（决赛）[cmd_table.json] |
| 20722 | 进入准备区 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入准备区[cmd_table.json] |
| 20723 | 退出准备区 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出准备区[cmd_table.json] |
| 20724 | 准备区信息 | bidirectional | cs: — ／ sc: team_id:uint32; team_srv_id:string; team_name:string; state:uint8; team_id2:uint32; team_srv_id2:string; team_name2:string; state2:uint8; flag:uint8; round:uint8; status:uint8; end_time:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备区信息[cmd_table.json] |
| 20725 | 准备状态 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string; state:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备状态[cmd_table.json] |
| 20726 | 准备状态变更 | sc | cs: — ／ sc: team_id:uint32; team_srv_id:string; state:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:准备状态变更[cmd_table.json] |
| 20727 | 对战玩家挑战结果 | sc | cs: — ／ sc: bat_res:uint8; flag:uint8; round:uint8; score:uint8; total_hurt:uint32; role_list:table; target_hurt:uint32; target_role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:对战玩家挑战结果[cmd_table.json] |
| 20728 | 通知队长有新队员申请 | sc | cs: — ／ sc: num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:通知队长有新队员申请[cmd_table.json] |
| 20729 | 被邀请的显示红点 | sc | cs: — ／ sc: — | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:被邀请的显示红点[cmd_table.json] |
| 20799 | 淘汰赛往后的场次战斗信息 | bidirectional | cs: — ／ sc: play:uint8; play_win:uint8; enemy_play_win:uint8; timeout:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:淘汰赛往后的场次战斗信息[cmd_table.json] |

### cmd_resolve_208.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 20800 | 仙椅信息 | bidirectional | cs: — ／ sc: stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:仙椅信息[cmd_table.json] |
| 20801 | 升阶 | bidirectional | cs: — ／ sc: result:uint8; msg:string; stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:升阶[cmd_table.json] |
| 20802 | 转换资源 | bidirectional | cs: stage:uint8 ／ sc: result:uint8; msg:string; stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转换资源[cmd_table.json] |
| 20803 | 仙椅装备穿戴 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙椅装备穿戴[cmd_table.json] |
| 20804 | 脱装备 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:脱装备[cmd_table.json] |
| 20805 | 仙椅升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙椅升星[cmd_table.json] |
| 20806 | 使用仙椅碎片 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用仙椅碎片[cmd_table.json] |
| 20807 | 激活时效仙椅 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活时效仙椅[cmd_table.json] |
| 20808 | 装备吞噬 | bidirectional | cs: item_id_lev:uint32; item_id_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备吞噬[cmd_table.json] |
| 20809 | 上、下仙座 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string; flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:上、下仙座[cmd_table.json] |

### cmd_resolve_213.luac（14 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 21301 | 获取星魂塔数据 | bidirectional | cs: — ／ sc: tower_id:uint32; floor:uint32; is_effect:uint32; clear_list:table; is_clear:uint8; daily_floors:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获取星魂塔数据[cmd_table.json] |
| 21302 | 进入星魂塔下一层 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:进入星魂塔下一层[cmd_table.json] |
| 21303 | 星魂塔每层侧边数据协议 | sc | cs: — ／ sc: dung_bid:uint32; tower_id:uint8; floor:uint8; BossList:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:星魂塔每层侧边数据协议[cmd_table.json] |
| 21304 | 星魂塔每层结算协议 | sc | cs: — ／ sc: tower_id:uint8; floor:uint8; round:uint8; reward_list:table; daily_floors:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:星魂塔每层结算协议[cmd_table.json] |
| 21305 | 购买飞升副本次数 | bidirectional | cs: bid:uint32 ／ sc: code:uint8; msg:string; bid:uint32; enter_count:uint16; buy_count:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:购买飞升副本次数[cmd_table.json] |
| 21306 | 飞升副本次数信息 | bidirectional | cs: — ／ sc: list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:飞升副本次数信息[cmd_table.json] |
| 21307 | 飞升副本结算界面 | sc | cs: — ／ sc: bid:uint32; gain:table; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本结算界面[cmd_table.json] |
| 21308 | 飞升副本开始扫荡 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string; time:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本开始扫荡[cmd_table.json] |
| 21309 | 飞升副本加速扫荡 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string; bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本加速扫荡[cmd_table.json] |
| 21310 | 飞升副本一键扫荡 | bidirectional | cs: — ／ sc: tips:uint8; msg:string; one_key_sweep_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本一键扫荡[cmd_table.json] |
| 21311 | 飞升副本取消一键扫荡 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string; one_key_sweep_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本取消一键扫荡[cmd_table.json] |
| 21312 | 飞升副本一键扫荡信息 | bidirectional | cs: — ／ sc: one_key_sweep_list:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:飞升副本一键扫荡信息[cmd_table.json] |
| 21313 | 飞升副本加入一键扫荡队列 | bidirectional | cs: bid:uint32 ／ sc: tips:uint8; msg:string; one_key_sweep_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:飞升副本加入一键扫荡队列[cmd_table.json] |
| 21399 | 获取星魂塔通关信息 | bidirectional | cs: tower_id:uint32 ／ sc: tower_id:uint32; clear_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取星魂塔通关信息[cmd_table.json] |

### cmd_resolve_214.luac（13 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 21400 | 符文装备栏数据 | bidirectional | cs: — ／ sc: role_eqm:table; partner_eqm:table; eqm_grid:uint8; dung_bid:uint32; floor:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:符文装备栏数据[cmd_table.json] |
| 21401 | 推送符文装备栏解锁 | sc | cs: — ／ sc: eqm_grid:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送符文装备栏解锁[cmd_table.json] |
| 21402 | 镶嵌符文 | bidirectional | cs: bag_item_id:uint32; eqm_item_id:uint32; eqm_pos:uint8; hero_id:uint32 ／ sc: code:uint8; msg:string; bag_item_id:uint32; eqm_item_id:uint32; eqm_pos:uint8; hero_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:镶嵌符文[cmd_table.json] |
| 21403 | 拆卸符文 | bidirectional | cs: eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 ／ sc: code:uint8; msg:string; eqm_item_id:uint32; bag_item_id:uint32; bag_pos:uint8; hero_bid:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:拆卸符文[cmd_table.json] |
| 21404 | 分解护符 | bidirectional | cs: list:table ／ sc: code:uint8; msg:string; add_val:uint32; val:uint32; list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:分解护符[cmd_table.json] |
| 21405 | 兑换护符 | bidirectional | cs: rune_bid:uint32; num:uint16 ／ sc: code:uint8; msg:string; id:uint16; num:uint16; price:uint32 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:兑换护符[cmd_table.json] |
| 21406 | 升级护符 | bidirectional | cs: bag_code:uint8; id:uint32 ／ sc: code:uint8; msg:string; bag_code:uint8; id:uint16; new_lev:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级护符[cmd_table.json] |
| 21407 | 推送符文塔信息 | sc | cs: — ／ sc: dung_bid:uint32; floor:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:推送符文塔信息[cmd_table.json] |
| 21410 | 寻宝主界面 | bidirectional | cs: — ／ sc: free_times:uint8; is_haft:uint8; free_end_time:uint32; rest_times:uint8; coin_count:uint8; record_server:table; show_vip:uint8; gold_count:uint8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:寻宝主界面[cmd_table.json] |
| 21411 | 抽奖 | bidirectional | cs: count_type:uint8; color:uint8 ／ sc: code:uint8; msg:string; coin_count:uint8; rest_times:uint8; Items:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:抽奖[cmd_table.json] |
| 21412 | 获取免费次数 | bidirectional | cs: — ／ sc: free_times:uint8; is_haft:uint8; free_end_time:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取免费次数[cmd_table.json] |
| 21413 | 获取抽奖记录 | bidirectional | cs: — ／ sc: record_server:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取抽奖记录[cmd_table.json] |
| 21414 | 查看玩家星魂信息 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; role_eqm:table; role_power:uint32; eqm_grid:uint8; dung_bid:uint32; floor:uint8; partner_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看玩家星魂信息[cmd_table.json] |

### cmd_resolve_216.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 21600 | 灵器信息 | bidirectional | cs: — ／ sc: stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:灵器信息[cmd_table.json] |
| 21601 | 升阶 | bidirectional | cs: — ／ sc: result:uint8; msg:string; stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升阶[cmd_table.json] |
| 21602 | 转换资源 | bidirectional | cs: stage:uint8 ／ sc: result:uint8; msg:string; stage:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:转换资源[cmd_table.json] |
| 21603 | 灵器装备穿戴 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:灵器装备穿戴[cmd_table.json] |
| 21604 | 脱装备 | bidirectional | cs: item_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:脱装备[cmd_table.json] |
| 21605 | 灵器升星 | bidirectional | cs: surface_id:uint16 ／ sc: code:uint8; msg:string; surface_id:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:灵器升星[cmd_table.json] |
| 21606 | 使用灵器碎片 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用灵器碎片[cmd_table.json] |
| 21607 | 激活时效灵器 | bidirectional | cs: item_bid:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活时效灵器[cmd_table.json] |
| 21608 | 装备吞噬 | bidirectional | cs: item_id_lev:uint32; item_id_list:table ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:装备吞噬[cmd_table.json] |
| 21609 | 使用/取消灵器 | bidirectional | cs: flag:uint8 ／ sc: code:uint8; msg:string; flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用/取消灵器[cmd_table.json] |

### cmd_resolve_300.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30000 | 宗门弹劾投票 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门弹劾投票[cmd_table.json] |
| 30001 | 获得弹劾信息 | bidirectional | cs: — ／ sc: lanucher_name:string; host_name:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:获得弹劾信息[cmd_table.json] |

### cmd_resolve_301.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30101 | 报名进入 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:报名进入[cmd_table.json] |
| 30102 | 退出 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:退出[cmd_table.json] |
| 30103 | 加BUFF | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:加BUFF[cmd_table.json] |
| 30104 | 获取当前巨龙信息 | bidirectional | cs: — ／ sc: boss_bid:uint32; boss_hp:uint32; boss_hp_max:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前巨龙信息[cmd_table.json] |
| 30105 | 获取当前角色排行信息 | bidirectional | cs: career:uint8; idx:uint8; num:uint8 ／ sc: career:uint8; idx:uint8; num:uint8; rank:uint16; hurt:uint32; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前角色排行信息[cmd_table.json] |
| 30106 | 获取当前角色排行信息 | sc | cs: — ／ sc: — | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前角色排行信息[cmd_table.json] |
| 30107 | 复活 | bidirectional | cs: type:uint8 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:复活[cmd_table.json] |
| 30108 | 获取个人信息 | bidirectional | cs: — ／ sc: buff_num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取个人信息[cmd_table.json] |
| 30109 | 获取结算排行信息 | bidirectional | cs: career:uint8; idx:uint8; num:uint8 ／ sc: career:uint8; idx:uint8; num:uint8; rank:uint16; career_rank:uint16; hurt:uint32; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取结算排行信息[cmd_table.json] |
| 30100 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_COMM_005 | ? | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_30100；引用系统: Cross-server 跨服[SYS_COMM_005] |

### cmd_resolve_302.luac（12 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30200 | 活动开启 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动开启[cmd_table.json] |
| 30201 | 活动报名 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:活动报名[cmd_table.json] |
| 30202 | 活动退出 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:活动退出[cmd_table.json] |
| 30203 | 使用特殊道具 | bidirectional | cs: type:uint8; val:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:使用特殊道具[cmd_table.json] |
| 30204 | 个人信息 | bidirectional | cs: — ／ sc: num1:uint8; num2:uint8; num3:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人信息[cmd_table.json] |
| 30205 | 基础信息 | bidirectional | cs: — ／ sc: bid:uint32; hp:uint32; max_hp:uint32; wave:uint8; max_wave:uint8; mon_num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:基础信息[cmd_table.json] |
| 30206 | 获取当前角色排行信息 | bidirectional | cs: idx:uint8; num:uint8 ／ sc: idx:uint8; num:uint8; rank:uint16; score:uint32; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前角色排行信息[cmd_table.json] |
| 30207 | 打开ROLL抽取信息 | bidirectional | cs: — ／ sc: end_time:uint32; item_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:打开ROLL抽取信息[cmd_table.json] |
| 30208 | 抽取ROLL点 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:抽取ROLL点[cmd_table.json] |
| 30209 | 更新玩家抽到ROLL点信息 | sc | cs: — ／ sc: rid:uint32; srv_id:string; name:string; sex:uint8; career:uint8; val:uint8; idx:uint8; flag:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新玩家抽到ROLL点信息[cmd_table.json] |
| 30210 | 更新玩家抽到ROLL点信息 | sc | cs: — ／ sc: end_time:uint32; item_list:table; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新玩家抽到ROLL点信息[cmd_table.json] |
| 30220 | 结算排行信息 | bidirectional | cs: — ／ sc: wave:uint8; rank:uint16; score:uint32; item_list:table; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:结算排行信息[cmd_table.json] |

### cmd_resolve_303.luac（7 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30300 | 我的年货收集列表 | bidirectional | cs: — ／ sc: assist:uint8; freight:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:我的年货收集列表[cmd_table.json] |
| 30301 | 查看别人的年货收集列表 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: rid:uint32; srv_id:string; freight:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:查看别人的年货收集列表[cmd_table.json] |
| 30302 | 提交物品;如果成功，客户端自行修改下数据 | bidirectional | cs: id:uint8 ／ sc: id:uint8; code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交物品;如果成功，客户端自行修改下数据[cmd_table.json] |
| 30303 | 提交任务 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:提交任务[cmd_table.json] |
| 30304 | 发求助 | bidirectional | cs: id:uint8 ／ sc: id:uint8; code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发求助[cmd_table.json] |
| 30305 | 帮助别人 | bidirectional | cs: rid:uint32; srv_id:string; id:uint8 ／ sc: rid:uint32; srv_id:string; id:uint8; code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:帮助别人[cmd_table.json] |
| 30306 | 当前已提交的箱子数量 | bidirectional | cs: — ／ sc: num:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:当前已提交的箱子数量[cmd_table.json] |

### cmd_resolve_304.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30400 | 请求位面信息 | bidirectional | cs: — ／ sc: code:uint8; msg:string; current_pos:uint8; total_steps:uint32; step_box:table; already_roll_count:uint32; remain_free_count:uint8; events:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求位面信息[cmd_table.json] |
| 30401 | 摇色子 | bidirectional | cs: count:uint8; args:uint8 ／ sc: result:uint8; msg:string; step_info:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:摇色子[cmd_table.json] |
| 30402 | 领取阶段奖励 | bidirectional | cs: step_bid:uint32 ／ sc: result:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取阶段奖励[cmd_table.json] |
| 30403 | 摇完色子请求 | bidirectional | cs: — ／ sc: items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:摇完色子请求[cmd_table.json] |

### cmd_resolve_305.luac（8 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30500 | 请求成长目标信息 | bidirectional | cs: — ／ sc: code:uint8; msg:string; current_day:int32; remain_time:uint32; growth_targets:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求成长目标信息[cmd_table.json] |
| 30501 | 领取登陆奖励 | bidirectional | cs: day:uint8 ／ sc: result:uint8; msg:string; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取登陆奖励[cmd_table.json] |
| 30502 | 领取充值奖励 | bidirectional | cs: day:uint8 ／ sc: result:uint8; msg:string; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取充值奖励[cmd_table.json] |
| 30503 | 半价抢购 | bidirectional | cs: day:uint8 ／ sc: result:uint8; msg:string; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:半价抢购[cmd_table.json]；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 30504 | 目标信息变化通知 | bidirectional | cs: — ／ sc: day:uint16; target_id:uint32; finished_value:uint32; total_value:uint32; target_state:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:目标信息变化通知[cmd_table.json] |
| 30505 | 组合奖励状态通知 | bidirectional | cs: — ／ sc: day:uint16; target_state:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:组合奖励状态通知[cmd_table.json] |
| 30506 | 领取目标奖励 | bidirectional | cs: target_id:uint32 ／ sc: result:uint8; msg:string; target_id:uint32; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取目标奖励[cmd_table.json]；死协议：客户端从不发送[dead_protocols_and_traffic.md] |
| 30507 | 领取组合奖励 | bidirectional | cs: day:uint16 ／ sc: result:uint8; msg:string; day:uint16; items:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取组合奖励[cmd_table.json]；死协议：客户端从不发送[dead_protocols_and_traffic.md] |

### cmd_resolve_306.luac（4 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30600 | 黑市商品数据 | bidirectional | cs: — ／ sc: refresh_times:uint8; next_time:uint32; items:table | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:黑市商品数据[cmd_table.json] |
| 30601 | 刷新黑市商品 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:刷新黑市商品[cmd_table.json] |
| 30602 | 购买黑市商品 | bidirectional | cs: Id:uint8; type:uint8 ／ sc: code:uint8; Id:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:购买黑市商品[cmd_table.json] |
| 30603 | 出售黑市商品 | bidirectional | cs: items:table ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:出售黑市商品[cmd_table.json] |

### cmd_resolve_307.luac（18 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30700 | 宗门报名 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门报名[cmd_table.json] |
| 30701 | 宗门报名列表 | bidirectional | cs: idx:uint16; num:uint8 ／ sc: idx:uint16; num:uint8; all_num:uint16; guild_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门报名列表[cmd_table.json] |
| 30702 | 宗门基础信息 | bidirectional | cs: gid:uint32; gsrv_id:string ／ sc: gid:uint32; gsrv_id:string; group:uint8; season_win:uint16; all_win:uint32; score:uint32; rank:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门基础信息[cmd_table.json] |
| 30703 | 宗门匹配列表 | bidirectional | cs: group:uint8 ／ sc: group:uint8; start_time:uint32; count:uint32; season:uint32; guild_match_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门匹配列表[cmd_table.json] |
| 30704 | 玩家报名进入 | bidirectional | cs: — ／ sc: code:uint8; msg:string; remain_relive_count:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玩家报名进入[cmd_table.json] |
| 30705 | 玩家退出 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:玩家退出[cmd_table.json] |
| 30706 | 击杀玩家 | bidirectional | cs: rid:uint32; srv_id:string ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:击杀玩家[cmd_table.json] |
| 30707 | 宗门对战信息 | bidirectional | cs: — ／ sc: group:uint8; gid1:uint32; gsrv_id1:string; gname1:string; gid2:uint32; gsrv_id2:string; gname2:string; time:uint32; ret:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门对战信息[cmd_table.json] |
| 30708 | 塔列表 | bidirectional | cs: — ／ sc: tower_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:塔列表[cmd_table.json] |
| 30709 | 个人积分列表 | bidirectional | cs: gid:uint32; gsrv_id:string; idx:uint16; num:uint8 ／ sc: gid:uint32; gsrv_id:string; idx:uint16; num:uint8; all_num:uint16; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:个人积分列表[cmd_table.json] |
| 30710 | 宗门赛季列表 | bidirectional | cs: group:uint8; idx:uint16; num:uint8 ／ sc: group:uint8; idx:uint16; num:uint8; all_num:uint16; guild_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:宗门赛季列表[cmd_table.json] |
| 30711 | 死亡复活状态 | bidirectional | cs: — ／ sc: relive_time:uint32; remain_relive_count:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:死亡复活状态[cmd_table.json] |
| 30712 | 自己宗门基础信息 | bidirectional | cs: — ／ sc: gid:uint32; gsrv_id:string; gname:string; group:uint8; season_win:uint16; season_num:uint16; all_win:uint32; score:uint32; rank:uint16; sign_cond:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:自己宗门基础信息[cmd_table.json] |
| 30713 | 大炮信息 | bidirectional | cs: — ／ sc: elem_id:uint32; cd_time:uint32; time:uint32; max_time:uint32; play_effect:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:大炮信息[cmd_table.json] |
| 30714 | 删除塔元素 | bidirectional | cs: elem_id:uint32 ／ sc: — | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:删除塔元素[cmd_table.json] |
| 30715 | 进入塔元素 | bidirectional | cs: elem_bid:uint32 ／ sc: — | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:进入塔元素[cmd_table.json] |
| 30716 | 请求淘汰赛的对阵表 | bidirectional | cs: — ／ sc: start_time:table; elimination_match:table; champion_id:int8 | UNKNOWN | ✗ | ✓ | ✓ | VERIFIED | cmd_table中文名:请求淘汰赛的对阵表[cmd_table.json] |
| 30717 | 请求超级联赛的冠军 | bidirectional | cs: — ／ sc: guild_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求超级联赛的冠军[cmd_table.json] |

### cmd_resolve_308.luac（1 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30800 | 领取海神九考首次通过奖励 | bidirectional | cs: reward_wave:uint16 ／ sc: code:uint8; max_passed:uint16; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取海神九考首次通过奖励[cmd_table.json] |

### cmd_resolve_309.luac（3 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 30900 | 喂养 | bidirectional | cs: — ／ sc: result:uint8; msg:string; value:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:喂养[cmd_table.json] |
| 30901 | 道具翻倍活动购买 | bidirectional | cs: — ／ sc: result:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:道具翻倍活动购买[cmd_table.json] |
| 30902 | 领取道具翻倍奖励 | bidirectional | cs: day:uint8 ／ sc: result:uint8; msg:string; double:uint8; day:uint8; item_lists:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取道具翻倍奖励[cmd_table.json] |

### cmd_resolve_310.luac（9 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 31000 | 请求信息 | bidirectional | cs: — ／ sc: is_open:uint8; copy_infos:table; boss_infos:table; first_target:uint32; command_id:uint32; boss_buff:uint32; remain_seconds:uint32; copy_id:uint32; attack_remain_count:uint32; attack_total_count:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:请求信息[cmd_table.json] |
| 31001 | 开启副本 | bidirectional | cs: copy_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:开启副本[cmd_table.json] |
| 31002 | 设定优先目标 | bidirectional | cs: boss_id:uint32 ／ sc: code:uint8; msg:string; boss_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设定优先目标[cmd_table.json] |
| 31003 | 设定指挥指令 | bidirectional | cs: command_id:uint32 ／ sc: code:uint8; msg:string; command_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:设定指挥指令[cmd_table.json] |
| 31004 | 发起战斗 | bidirectional | cs: boss_id:uint32 ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:发起战斗[cmd_table.json] |
| 31005 | 取消优先目标 | bidirectional | cs: boss_id:uint32 ／ sc: code:uint8; msg:string; boss_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:取消优先目标[cmd_table.json] |
| 31006 | 获取当前角色排行信息 | bidirectional | cs: career:uint8; idx:uint8; num:uint8 ／ sc: career:uint8; idx:uint8; num:uint8; rank:uint16; hurt:uint32; name:string; my_lev:uint16; role_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取当前角色排行信息[cmd_table.json] |
| 31007 | 红点信息 | bidirectional | cs: — ／ sc: can_fight:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:红点信息[cmd_table.json] |
| 31008 | 副本通关通知 | bidirectional | cs: — ／ sc: copy_id:uint32 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:副本通关通知[cmd_table.json] |

### cmd_resolve_311.luac（5 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 31100 | 获取武魂觉醒信息 | bidirectional | cs: — ／ sc: point:uint16; insight_skill:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取武魂觉醒信息[cmd_table.json] |
| 31101 | 激活觉醒技能 | bidirectional | cs: insight_bid:uint32 ／ sc: code:uint8; insight_bid:uint32; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:激活觉醒技能[cmd_table.json] |
| 31102 | 升级觉醒技能 | bidirectional | cs: insight_bid:uint32 ／ sc: point:uint16; insight_bid:uint32; lev:uint8 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:升级觉醒技能[cmd_table.json] |
| 31103 | 重置加点 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:重置加点[cmd_table.json] |
| 31104 | 更新技能点 | bidirectional | cs: — ／ sc: point:uint16 | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:更新技能点[cmd_table.json] |

### cmd_resolve_312.luac（10 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 31200 | 命格消耗积分排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:命格消耗积分排行榜[cmd_table.json] |
| 31201 | 仙座战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_hero_bid:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙座战力排行榜[cmd_table.json] |
| 31202 | 仙座进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_stage:uint8; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:仙座进阶丹消耗排行[cmd_table.json] |
| 31203 | 观星台寻宝积分排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:观星台寻宝积分排行榜[cmd_table.json] |
| 31204 | 119 星魂战力；排名、星魂总等级、角色名、星魂总战力 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_lev:uint32; my_power:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:119 星魂战力；排名、星魂总等级、角色名、星魂总战力[cmd_table.json] |
| 31205 | 挖宝积分排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:挖宝积分排行[cmd_table.json] |
| 31206 | 灵器战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; my_hero_bid:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:灵器战力排行榜[cmd_table.json] |
| 31207 | 灵器进阶丹消耗排行 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:灵器进阶丹消耗排行[cmd_table.json] |
| 31208 | 上古仙器战力排行榜 | bidirectional | cs: ord:uint8; num:uint8; flag:uint8 ／ sc: my_ord:uint8; my_val:uint32; rank_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:上古仙器战力排行榜[cmd_table.json] |
| 31299 | UNKNOWN | cs (inferred from systems_master token prefix) | cs: — ／ sc: — | SYS_COMM_005 | ? | ✓ | ✓ | INFERENCE | prior analysis 引用[systems_master.json]：CS_31299；引用系统: Cross-server 跨服[SYS_COMM_005] |

### cmd_resolve_313.luac（2 条）

| cmd | 名称 | 方向 | 字段(cs / sc) | 系统 | 1.3.0 | 1.4.9 | 1.4.11 | 证据 | 用途理解 |
|---|---|---|---|---|---|---|---|---|---|
| 31300 | 获取财神送福奖励信息 | sc | cs: — ／ sc: reward_id:uint8; reward_list:table | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:获取财神送福奖励信息[cmd_table.json] |
| 31301 | 领取奖励 | bidirectional | cs: — ／ sc: code:uint8; msg:string | UNKNOWN | ✗ | ✓ | ✓ | CONFIRMED | cmd_table中文名:领取奖励[cmd_table.json] |

## 五、未确认项清单（unresolved）

| cmd | 名称 | 未确认内容 |
|---|---|---|
| 13103 | UNKNOWN | cs 方向无字段定义 ；cmd_table 无中文名 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13100 | UNKNOWN | cs 方向无字段定义 ；cmd_table 无中文名 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11300 | 竞技场界面信息 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11200 | 伙伴基础界面信息 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） ；含 6 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10924 | 个人活动图标 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10922 | 全服活动的活动状态 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 30500 | 请求成长目标信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 30300 | 我的年货收集列表 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 21600 | 灵器信息 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 21400 | 符文装备栏数据 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20800 | 仙椅信息 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20717 | 自己战队的下一场对战信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20702 | 自己战队信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20701 | 战事安排信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20204 | 可掠夺矿洞列表 | cs 方向无字段定义 ；含 4 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20200 | 获取我的矿洞数据 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20100 | 我要变强界面 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20010 | 战斗初始化数据 | cs 方向无字段定义 ；含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19200 | UNKNOWN | cs 方向无字段定义 ；cmd_table 无中文名 |
| 19100 | 光环信息 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18900 | 法宝信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18753 | 获取抢夺列表 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18714 | 获取已雇佣伙伴 | cs 方向无字段定义 ；含 6 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18402 | 跨服阶段信息 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 17800 | 获取今日摇钱次数 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 17406 | 我方进攻一览 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 17200 | 一次充值信息 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 16903 | 在线领取奖励状态 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 16697 | 坐骑转盘信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16635 | 查看我的夺宝记录列表 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16626 | 密令活动信息 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16614 | 获取祝福墙 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16603 | 子活动 | fields.json 注释:2026-09-19 回滚: AutoConstruct cs/16603 规格 = ['bid__I'] 单字段; 真机 8 字节 = bid(4) + 客户端缓冲区 4 字节残留(同 16500/17200/16400 现象) ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 15801 | 我的仙灵信息 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 15601 | 仙尊面板 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 15501 | 我的坐骑信息 | cs 方向无字段定义 ；含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14300 | 弹出转职界面 | cs 方向无字段定义 ；sc 方向无字段定义 |
| 14210 | 任务列表 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14000 | 获取阵法信息 | 1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13788 | 通知活力达到上限 | cs 方向无字段定义 ；sc 方向无字段定义 |
| 13600 | 悬赏榜信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13574 | 查看练功房数据 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13548 | 有新公告的时候，服务端推送本协议，告诉客户端 | cs 方向无字段定义 ；sc 方向无字段定义 |
| 13542 | 更新帮会成员列表 | cs 方向无字段定义 ；含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13512 | 被踢出帮会通知 | cs 方向无字段定义 ；sc 方向无字段定义 |
| 13509 | 获取帮会邀请列表 | cs 方向无字段定义 ；sc 方向无字段定义 |
| 13321 | 获取好友申请列表信息 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 13254 | 一键上阵 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13250 | 获取组队阵法信息 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13105 | UNKNOWN | cs 方向无字段定义 ；cmd_table 无中文名 |
| 13102 | UNKNOWN | cmd_table 无中文名 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13101 | UNKNOWN | cmd_table 无中文名 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12722 | 登录推送离线消息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12601 | 获取魔灵基础信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12413 | 更新任务目标拓展参数 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12005 | 所有开启章节的关卡星级情况 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11500 | 百草园主界面 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11403 | 战场内玩家数据 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11301 | 晋级界面信息 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 11242 | 伙伴羁绊突破 | cs 方向无字段定义 ；含 9 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11238 | 伙伴羁绊升星 | cs 方向无字段定义 ；含 9 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11215 | 伙伴仓库数据 | cs 方向无字段定义 ；含 6 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11017 | 设置过的队伍信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11000 | 获取地下城数据 | cs 方向无字段定义 ；含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10800 | 读取邮件列表 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10735 | 建筑居住的英雄 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10592 | 获取上古神器限时抢购礼包数据 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10544 | 伙伴法宝界面信息 | cs 方向无字段定义 ；含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10527 | 新手礼包开启状态 | cs 方向无字段定义 ；1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 10401 | 获取英雄基础信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10301 | 获取角色基础信息 | cs 方向无字段定义 ；含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10201 | 场景图块信息() | cs 方向无字段定义 ；含 8 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 31301 | 领取奖励 | cs 方向无字段定义 |
| 31299 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_312.luac 验证 |
| 31104 | 更新技能点 | cs 方向无字段定义 |
| 31103 | 重置加点 | cs 方向无字段定义 |
| 31100 | 获取武魂觉醒信息 | cs 方向无字段定义 |
| 31008 | 副本通关通知 | cs 方向无字段定义 |
| 31007 | 红点信息 | cs 方向无字段定义 |
| 31000 | 请求信息 | cs 方向无字段定义 |
| 30901 | 道具翻倍活动购买 | cs 方向无字段定义 |
| 30900 | 喂养 | cs 方向无字段定义 |
| 30717 | 请求超级联赛的冠军 | cs 方向无字段定义 |
| 30716 | 请求淘汰赛的对阵表 | cs 方向无字段定义 |
| 30715 | 进入塔元素 | sc 方向无字段定义 |
| 30714 | 删除塔元素 | sc 方向无字段定义 |
| 30713 | 大炮信息 | cs 方向无字段定义 |
| 30712 | 自己宗门基础信息 | cs 方向无字段定义 |
| 30711 | 死亡复活状态 | cs 方向无字段定义 |
| 30708 | 塔列表 | cs 方向无字段定义 |
| 30707 | 宗门对战信息 | cs 方向无字段定义 |
| 30705 | 玩家退出 | cs 方向无字段定义 |
| 30704 | 玩家报名进入 | cs 方向无字段定义 |
| 30700 | 宗门报名 | cs 方向无字段定义 |
| 30601 | 刷新黑市商品 | cs 方向无字段定义 |
| 30600 | 黑市商品数据 | cs 方向无字段定义 |
| 30505 | 组合奖励状态通知 | cs 方向无字段定义 |
| 30504 | 目标信息变化通知 | cs 方向无字段定义 |
| 30403 | 摇完色子请求 | cs 方向无字段定义 |
| 30400 | 请求位面信息 | cs 方向无字段定义 |
| 30306 | 当前已提交的箱子数量 | cs 方向无字段定义 |
| 30303 | 提交任务 | cs 方向无字段定义 |
| 30301 | 查看别人的年货收集列表 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 30220 | 结算排行信息 | cs 方向无字段定义 |
| 30208 | 抽取ROLL点 | cs 方向无字段定义 |
| 30207 | 打开ROLL抽取信息 | cs 方向无字段定义 |
| 30205 | 基础信息 | cs 方向无字段定义 |
| 30204 | 个人信息 | cs 方向无字段定义 |
| 30202 | 活动退出 | cs 方向无字段定义 |
| 30201 | 活动报名 | cs 方向无字段定义 |
| 30200 | 活动开启 | cs 方向无字段定义 |
| 30108 | 获取个人信息 | cs 方向无字段定义 |
| 30106 | 获取当前角色排行信息 | sc 方向无字段定义 |
| 30104 | 获取当前巨龙信息 | cs 方向无字段定义 |
| 30102 | 退出 | cs 方向无字段定义 |
| 30101 | 报名进入 | cs 方向无字段定义 |
| 30100 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_301.luac 验证 |
| 30001 | 获得弹劾信息 | cs 方向无字段定义 |
| 21601 | 升阶 | cs 方向无字段定义 |
| 21414 | 查看玩家星魂信息 | 含 8 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 21413 | 获取抽奖记录 | cs 方向无字段定义 |
| 21412 | 获取免费次数 | cs 方向无字段定义 |
| 21410 | 寻宝主界面 | cs 方向无字段定义 |
| 21312 | 飞升副本一键扫荡信息 | cs 方向无字段定义 |
| 21310 | 飞升副本一键扫荡 | cs 方向无字段定义 |
| 21306 | 飞升副本次数信息 | cs 方向无字段定义 |
| 21302 | 进入星魂塔下一层 | cs 方向无字段定义 |
| 21301 | 获取星魂塔数据 | cs 方向无字段定义 |
| 20801 | 升阶 | cs 方向无字段定义 |
| 20799 | 淘汰赛往后的场次战斗信息 | cs 方向无字段定义 |
| 20729 | 被邀请的显示红点 | sc 方向无字段定义 |
| 20724 | 准备区信息 | cs 方向无字段定义 |
| 20723 | 退出准备区 | cs 方向无字段定义 |
| 20722 | 进入准备区 | cs 方向无字段定义 |
| 20721 | 请求沙场信息（决赛） | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20720 | 请求沙场信息（淘汰赛） | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20719 | 请求沙场信息(复活赛) | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20718 | 请求沙场信息(小组赛) | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20716 | 解散战队 | cs 方向无字段定义 |
| 20715 | 离开战队 | cs 方向无字段定义 |
| 20708 | 查看信息 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20700 | 比赛阶段信息 | cs 方向无字段定义 |
| 20504 | 获取任务列表 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20502 | 获取招募人列表 | cs 方向无字段定义 |
| 20501 | 获取可招募的好友列表 | cs 方向无字段定义 |
| 20500 | 获取好友回归数据 | cs 方向无字段定义 |
| 20314 | 帮会防守记录 | cs 方向无字段定义 |
| 20313 | 本周收益历史 | cs 方向无字段定义 |
| 20312 | 推送玩家自己矿洞所在屏数 | cs 方向无字段定义 |
| 20311 | 打开排行榜 | cs 方向无字段定义 |
| 20307 | 资产列表 | cs 方向无字段定义 |
| 20304 | 查看掠夺记录 | cs 方向无字段定义 |
| 20300 | 获取矿区矿洞数据 | cs 方向无字段定义 |
| 20208 | 刷新单个我的矿洞数据 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20206 | 搜索可掠夺矿洞 | cs 方向无字段定义 |
| 20030 | 分享战斗录像 | cs 方向无字段定义 |
| 20027 | 停止播放录像 | cs 方向无字段定义 |
| 20021 | 闭关战斗结束界面 | cs 方向无字段定义 |
| 20017 | 退出观战 | cs 方向无字段定义 |
| 20015 | 新增战斗对象 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20014 | 客户端动画播放完成通知 | cs 方向无字段定义 |
| 20013 | 回合开始 | 含 4 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20012 | 小回合战斗效果 | 含 6 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 20011 | 客户端加载完成 | cs 方向无字段定义 |
| 20003 | 测试战斗 | cs 方向无字段定义 |
| 19904 | 进入抢气球活动场景 | cs 方向无字段定义 |
| 19903 | 退出抢气球活动场景 | cs 方向无字段定义 |
| 19902 | 获取房间数据 | cs 方向无字段定义 |
| 19602 | 奖励找回数据刷新 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19600 | 获取奖励找回信息列表 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19537 | 发起顶替队长投票 | cs 方向无字段定义 |
| 19536 | 提升结拜空间等级 | cs 方向无字段定义 |
| 19534 | 结义空间基础信息 | cs 方向无字段定义 |
| 19533 | 取消结拜 | cs 方向无字段定义 |
| 19530 | 请求打开界面 | cs 方向无字段定义 |
| 19529 | 取消申请退出 | cs 方向无字段定义 |
| 19518 | 申请退出 | cs 方向无字段定义 |
| 19515 | 打开结拜技能界面 | cs 方向无字段定义 |
| 19514 | 打开结拜空间 | cs 方向无字段定义 |
| 19505 | 队长发起结拜 | cs 方向无字段定义 |
| 19501 | 挑战结义副本 | cs 方向无字段定义 |
| 19500 | 接结义任务 | cs 方向无字段定义 |
| 19414 | 查看玩家命格信息 | 含 4 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19409 | 境界突破 | cs 方向无字段定义 |
| 19407 | 购买魂力 | cs 方向无字段定义 |
| 19406 | 查询魂力数据 | cs 方向无字段定义 |
| 19401 | 命格数据变更协议 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19400 | 命格背包信息 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 19202 | UNKNOWN | cmd_table 无中文名 |
| 19201 | UNKNOWN | cmd_table 无中文名 |
| 19101 | 升阶 | cs 方向无字段定义 |
| 19000 | 玩家宝箱背包 | cs 方向无字段定义 |
| 18911 | 查看他人的法宝信息 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18909 | 法宝商店信息 | cs 方向无字段定义 |
| 18907 | 法宝信息(更新单个信息) | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18868 | 领取层数礼包 | cs 方向无字段定义 |
| 18828 | 雕像数据 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18827 | 获取封魔录霸主名单 | cs 方向无字段定义 |
| 18826 | 激活铜人阵 | cs 方向无字段定义 |
| 18821 | 退出公共场景 | cs 方向无字段定义 |
| 18820 | 进入公共场景 | cs 方向无字段定义 |
| 18812 | 领取十次战斗奖励 | cs 方向无字段定义 |
| 18811 | 领取首次胜利奖励 | cs 方向无字段定义 |
| 18809 | 获取历史战报 | cs 方向无字段定义 |
| 18808 | 段位说明界面 | cs 方向无字段定义 |
| 18807 | 右侧栏信息 | cs 方向无字段定义 |
| 18804 | 匹配结果 | cs 方向无字段定义 |
| 18803 | 个人信息 | cs 方向无字段定义 |
| 18801 | 退出大厅 | cs 方向无字段定义 |
| 18800 | 进入大厅 | cs 方向无字段定义 |
| 18761 | 通知活动结束退出战斗 | sc 方向无字段定义 |
| 18760 | 获取boss血量 | cs 方向无字段定义 |
| 18758 | 挑战boss | cs 方向无字段定义 |
| 18755 | 个人事件列表 | cs 方向无字段定义 |
| 18754 | 全服事件列表 | cs 方向无字段定义 |
| 18750 | 打开界面 | cs 方向无字段定义 |
| 18735 | 获取buff列表 | cs 方向无字段定义 |
| 18731 | 掷色子 | cs 方向无字段定义 |
| 18730 | 打开界面 | cs 方向无字段定义 |
| 18715 | 购买抢购物品 | cs 方向无字段定义 |
| 18713 | 查看雇佣伙伴 | 含 15 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18711 | 刷新雇佣列表 | cs 方向无字段定义 |
| 18710 | 获取雇佣伙伴列表 | cs 方向无字段定义 |
| 18708 | 双击设置阵位 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18702 | 取消设置阵位 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18701 | 设置阵位 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18700 | 获取阵法信息 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 18614 | 推送阵营数据 | cs 方向无字段定义 |
| 18613 | 推送活动状态和剩余时间 | cs 方向无字段定义 |
| 18612 | 推送阵营积分变化（有玩家提交材料时） | cs 方向无字段定义 |
| 18611 | 推送玩家积分变化(采集物品时推送) | cs 方向无字段定义 |
| 18609 | 结算排行榜 | cs 方向无字段定义 |
| 18608 | 战斗结束 | cs 方向无字段定义 |
| 18605 | 战区玩家仙桃排行榜 | cs 方向无字段定义 |
| 18604 | 活动阵营信息 | cs 方向无字段定义 |
| 18603 | 战败回到复活区 | cs 方向无字段定义 |
| 18601 | 退出战区 | cs 方向无字段定义 |
| 18600 | 进入战区 | cs 方向无字段定义 |
| 18501 | 队长确认邀请配偶进队 | cs 方向无字段定义 |
| 18500 | 接取循环任务 | cs 方向无字段定义 |
| 18404 | 全服奖励领取情况 | cs 方向无字段定义 |
| 18400 | 跨服进程信息 | cs 方向无字段定义 |
| 18321 | 婚戒装备进阶 | cs 方向无字段定义 |
| 18320 | 结婚场景人员信息 | cs 方向无字段定义 |
| 18319 | 结婚场景信息（推送） | cs 方向无字段定义 |
| 18318 | 结婚状态推送 | cs 方向无字段定义 |
| 18317 | 广播互动玩法 | cs 方向无字段定义 |
| 18315 | 询问离婚反馈（服务端推送） | cs 方向无字段定义 |
| 18313 | 检查是否满足离婚离线天数 | cs 方向无字段定义 |
| 18312 | 广播弹幕 | cs 方向无字段定义 |
| 18309 | 广播婚宴仪式阶段 | cs 方向无字段定义 |
| 18308 | 广播婚宴阶段 | cs 方向无字段定义 |
| 18307 | 婚宴信息 | cs 方向无字段定义 |
| 18306 | 退出婚宴 | cs 方向无字段定义 |
| 18305 | 进入婚宴 | cs 方向无字段定义 |
| 18303 | 推送求婚结果，状态：0不同意，1同意 | cs 方向无字段定义 |
| 18301 | 询问求婚反馈（服务端推送） | cs 方向无字段定义 |
| 18300 | 发起求婚 | cs 方向无字段定义 |
| 18201 | 获取玩家今日最大通关数 | cs 方向无字段定义 |
| 18200 | 接取任务 | cs 方向无字段定义 |
| 18103 | 加速修炼 | cs 方向无字段定义 |
| 18102 | 提升境界 | cs 方向无字段定义 |
| 18100 | 获取元神信息 | cs 方向无字段定义 |
| 18025 | 帮会的竞拍记录 | cs 方向无字段定义 |
| 18024 | 自己的竞拍记录 | cs 方向无字段定义 |
| 18021 | 推送拍卖行物品信息 | cs 方向无字段定义 |
| 18020 | 打开拍卖行界面 | cs 方向无字段定义 |
| 18010 | 帮会技能提升上限界面 | cs 方向无字段定义 |
| 18009 | 帮会技能升级界面 | cs 方向无字段定义 |
| 18008 | 帮会目标完成提示(推送) | cs 方向无字段定义 |
| 18006 | 帮会目标界面 | cs 方向无字段定义 |
| 18005 | 一键邀请 | cs 方向无字段定义 |
| 18004 | 单独请求剩余次数和运势 | cs 方向无字段定义 |
| 18003 | 被祝福 | cs 方向无字段定义 |
| 18002 | 被邀请 | cs 方向无字段定义 |
| 18000 | 打开界面 | cs 方向无字段定义 |
| 17909 | 被挑战通知 | cs 方向无字段定义 |
| 17907 | 加速冷却 | cs 方向无字段定义 |
| 17906 | 购买次数 | cs 方向无字段定义 |
| 17905 | 战斗结果 | cs 方向无字段定义 |
| 17903 | 历史战报 | cs 方向无字段定义 |
| 17902 | 挑战列表 | cs 方向无字段定义 |
| 17901 | 打开界面 | cs 方向无字段定义 |
| 17801 | 摇钱 | cs 方向无字段定义 |
| 17706 | 一键升级伙伴装备 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 17602 | 领奖 | cs 方向无字段定义 |
| 17600 | 界面信息 | cs 方向无字段定义 |
| 17521 | 主动报名 | cs 方向无字段定义 |
| 17519 | 场景信息 | cs 方向无字段定义 |
| 17518 | 场景累计经验更新 | cs 方向无字段定义 |
| 17517 | 帮会总结算 | cs 方向无字段定义 |
| 17516 | 通知玩家报名 | cs 方向无字段定义 |
| 17513 | 最近的几条聊天消息(帮派和队伍) | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 17512 | 聊天协议；世界，场景，帮派，队伍，传闻，系统 | cs 方向无字段定义 |
| 17511 | 战斗出错 | cs 方向无字段定义 |
| 17510 | 战斗结果 | cs 方向无字段定义 |
| 17509 | 匹配结果 | cs 方向无字段定义 |
| 17508 | 匹配失败 | cs 方向无字段定义 |
| 17507 | 开始匹配 | cs 方向无字段定义 |
| 17506 | 准备区获得资产奖励（个人） | cs 方向无字段定义 |
| 17505 | 帮会个人积分榜 | cs 方向无字段定义 |
| 17504 | 帮会积分榜 | cs 方向无字段定义 |
| 17503 | 获取界面信息 | cs 方向无字段定义 |
| 17502 | 活动倒计时 | cs 方向无字段定义 |
| 17500 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_175.luac 验证 |
| 17400 | 进入活动界面显示 | cs 方向无字段定义 |
| 17310 | 段位分分布表 | cs 方向无字段定义 |
| 17309 | 好友段位排行榜 | cs 方向无字段定义 |
| 17306 | 活动奖励状态 | cs 方向无字段定义 |
| 17301 | 打开界面 | cs 方向无字段定义 |
| 17201 | 领取奖励 | cs 方向无字段定义 |
| 17100 | 每日充值当天信息 | cs 方向无字段定义 |
| 17001 | 获取玩家今日最大通关数 | cs 方向无字段定义 |
| 17000 | 接取任务 | cs 方向无字段定义 |
| 16902 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_169.luac 验证 |
| 16900 | 累积充值可领取状态 | cs 方向无字段定义 |
| 16706 | 获取超级VIP界面信息 | cs 方向无字段定义 |
| 16705 | 获取超级VIP显示状态 | cs 方向无字段定义 |
| 16704 | 获取VIP等级礼包每日状态 | cs 方向无字段定义 |
| 16703 | 领取VIP等级礼包 | cs 方向无字段定义 |
| 16700 | vip获取等级 | cs 方向无字段定义 |
| 16699 | 坐骑转盘发奖励 | cs 方向无字段定义 |
| 16696 | 领取边玩边下奖励 | cs 方向无字段定义 |
| 16695 | 请求下载有礼的状态 | cs 方向无字段定义 |
| 16693 | 查询奖池转盘信息 | cs 方向无字段定义 |
| 16668 | 抽奖记录 | cs 方向无字段定义 |
| 16667 | 抽奖完毕 | cs 方向无字段定义 |
| 16665 | 打开金银塔界面 | cs 方向无字段定义 |
| 16664 | 获取限时充值返利活动数据 | cs 方向无字段定义 |
| 16653 | 再来一轮 | cs 方向无字段定义 |
| 16651 | 获取刮刮乐活动数据 | cs 方向无字段定义 |
| 16648 | 奖励找回数据刷新 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16646 | 获取奖励找回信息列表 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16631 | 获取中奖者信息列表 | cs 方向无字段定义 |
| 16630 | 1元抢购活动信息 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16624 | 翻牌公告记录 | cs 方向无字段定义 |
| 16623 | 重置翻牌（成功推送16621） | cs 方向无字段定义 |
| 16621 | 翻牌界面 | cs 方向无字段定义 |
| 16620 | 子活动 | 含 5 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 16615 | 刷新祝福墙 | cs 方向无字段定义 |
| 16613 | 玩家获奖公告 | cs 方向无字段定义 |
| 16612 | 获奖玩家列表 | cs 方向无字段定义 |
| 16611 | 开始抽奖 | cs 方向无字段定义 |
| 16610 | 打开活动界面 | cs 方向无字段定义 |
| 16500 | 投资功能标签信息 | cs 方向无字段定义 |
| 16304 | 宗门种花数据 | cs 方向无字段定义 |
| 16200 | 获取Boss列表 | cs 方向无字段定义 |
| 16111 | 开始答题 | cs 方向无字段定义 |
| 16110 | 获取今日参加答题次数 | cs 方向无字段定义 |
| 16101 | 开始答题 | cs 方向无字段定义 |
| 16100 | 获取今日参加答题次数 | cs 方向无字段定义 |
| 16002 | 购买首充 | cs 方向无字段定义 |
| 16001 | 领取奖励 | cs 方向无字段定义 |
| 16000 | 首冲奖励当天信息 | cs 方向无字段定义 |
| 15900 | 获取当前功能预告Id,上线推 | cs 方向无字段定义 |
| 15807 | 领取进阶奖励 | cs 方向无字段定义 |
| 15806 | 仙灵进阶 | cs 方向无字段定义 |
| 15700 | 我的神器信息 | cs 方向无字段定义 |
| 15611 | 加速 | cs 方向无字段定义 |
| 15607 | 挑战结果 | cs 方向无字段定义 |
| 15507 | 领取进阶奖励 | cs 方向无字段定义 |
| 15506 | 坐骑进阶 | cs 方向无字段定义 |
| 15422 | 提交任务(废弃) | cs 方向无字段定义 |
| 15420 | 接取夫妻任务 | cs 方向无字段定义 |
| 15405 | 今日杀怪总任务 | cs 方向无字段定义 |
| 15400 | 接取循环任务 | cs 方向无字段定义 |
| 15303 | 杀怪任务成功 | cs 方向无字段定义 |
| 15300 | 接取帮会循环任务 | cs 方向无字段定义 |
| 15208 | 藏宝图兑换材料信息 | cs 方向无字段定义 |
| 15207 | 兑换高级图时,材料不足返回元宝提示 | cs 方向无字段定义 |
| 15204 | 获取剩余宝图元宝数 | cs 方向无字段定义 |
| 15203 | 元宝兑换宝图 | cs 方向无字段定义 |
| 15200 | 接取宝图任务 | cs 方向无字段定义 |
| 15102 | 客户端通知服务端，葫芦停止转动 | cs 方向无字段定义 |
| 15101 | 葫芦数据，采集完，服务端会推送给客户端 | cs 方向无字段定义 |
| 15016 | 队员参与摇骰 | cs 方向无字段定义 |
| 15001 | 藏宝图奖励获取 | cs 方向无字段定义 |
| 14901 | 称号列表 | cs 方向无字段定义 |
| 14807 | 提交任务 | cs 方向无字段定义 |
| 14803 | 我的炼丹炉列表(接到此消息，客户端会打开界面) | cs 方向无字段定义 |
| 14801 | 我的炼丹炉列表 | cs 方向无字段定义 |
| 14701 | 抽奖 | cs 方向无字段定义 |
| 14700 | 推送抽奖数据 | cs 方向无字段定义 |
| 14600 | 累积登录天数 | cs 方向无字段定义 |
| 14507 | 领取双倍 | cs 方向无字段定义 |
| 14505 | 捉鬼任务成功 | cs 方向无字段定义 |
| 14503 | 捉鬼奖励 | cs 方向无字段定义 |
| 14502 | 个人捉鬼进度 | cs 方向无字段定义 |
| 14500 | 接取捉鬼任务 | cs 方向无字段定义 |
| 14404 | 求助 | cs 方向无字段定义 |
| 14403 | 神兽喂养面板 | cs 方向无字段定义 |
| 14400 | 帮会神兽面板 | cs 方向无字段定义 |
| 14302 | 转职成功 | cs 方向无字段定义 |
| 14299 | 刷新宗门任务 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14298 | 宗门任务免费刷新次数 | cs 方向无字段定义 |
| 14216 | 重新获取种花种子 | cs 方向无字段定义 |
| 14207 | 推送剩余刷新次数 | cs 方向无字段定义 |
| 14205 | 接受试炼任务 | cs 方向无字段定义 |
| 14203 | 更新试炼数据 | cs 方向无字段定义 |
| 14202 | 试炼面板 | cs 方向无字段定义 |
| 14200 | 发送邀请 | cs 方向无字段定义 |
| 14101 | 签到领取奖励 | cs 方向无字段定义 |
| 14100 | 累积签到天数 | cs 方向无字段定义 |
| 14099 | 获取助阵伙伴属性加成 | cs 方向无字段定义 |
| 14028 | 双击设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14022 | 取消设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14021 | 设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14020 | 获取阵法信息 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14009 | 获取英雄助阵信息 | 1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 14008 | 双击设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14002 | 取消设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 14001 | 设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13901 | 充值查询 | cs 方向无字段定义 |
| 13819 | 物品出售成功 | sc 方向无字段定义 |
| 13807 | 请求单13806个物品信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13806 | 请求出售信息 | cs 方向无字段定义 |
| 13802 | 请求单13802个物品信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13787 | 领取活力值奖励 | cs 方向无字段定义 |
| 13786 | 日常信息 | cs 方向无字段定义 |
| 13781 | 活力信息 | cs 方向无字段定义 |
| 13772 | 购买饱和度 | cs 方向无字段定义 |
| 13771 | 查询饱和度 | cs 方向无字段定义 |
| 13752 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_137.luac 验证 |
| 13742 | 烹饪生产 | cs 方向无字段定义 |
| 13741 | 烹饪信息 | cs 方向无字段定义 |
| 13711 | 符咒生产 | cs 方向无字段定义 |
| 13704 | 技能等级 | cs 方向无字段定义 |
| 13583 | 强化供奉 | cs 方向无字段定义 |
| 13580 | 查看神树研究界面 | cs 方向无字段定义 |
| 13579 | 查看神树界面 | cs 方向无字段定义 |
| 13578 | 查看活动次数 | cs 方向无字段定义 |
| 13576 | 求助 | cs 方向无字段定义 |
| 13575 | 练功房一键领取 | cs 方向无字段定义 |
| 13569 | 祈福信息 | cs 方向无字段定义 |
| 13563 | 自己的个性签名 | cs 方向无字段定义 |
| 13561 | 个性签名列表 | cs 方向无字段定义 |
| 13556 | 帮派福利面板 | cs 方向无字段定义 |
| 13552 | 帮派礼盒面板,返回可分配的角色id | cs 方向无字段定义 |
| 13551 | 剩余帮派礼盒总数量 | cs 方向无字段定义 |
| 13546 | 公告列表 | cs 方向无字段定义 |
| 13543 | 发广告 | cs 方向无字段定义 |
| 13541 | 一键拒绝 | cs 方向无字段定义 |
| 13538 | 更新帮会资产 | cs 方向无字段定义 |
| 13530 | 获取帮会仓库信息 | cs 方向无字段定义 |
| 13529 | 获取本周福利状态 | cs 方向无字段定义 |
| 13528 | 领取本周福利 | cs 方向无字段定义 |
| 13526 | 购买帮会商店的物品 | cs 方向无字段定义 |
| 13521 | 获取帮会职位信息 | cs 方向无字段定义 |
| 13519 | 获取帮会成员列表 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13518 | 获取本帮会基本信息 | cs 方向无字段定义 |
| 13516 | 解散帮会 | cs 方向无字段定义 |
| 13514 | 退帮 | cs 方向无字段定义 |
| 13511 | 被成功邀请加入帮会 | cs 方向无字段定义 |
| 13506 | 成功加入帮会 | cs 方向无字段定义 |
| 13504 | 本帮有人申请加入 | cs 方向无字段定义 |
| 13416 | 查看个人信息 | cs 方向无字段定义 |
| 13414 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13413 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13412 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13411 | 个人兑换记录 | cs 方向无字段定义 |
| 13410 | 现金券兑换界面信息 | cs 方向无字段定义 |
| 13409 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13408 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13407 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13406 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13405 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13404 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_134.luac 验证 |
| 13371 | 增加的黑名单列表信息 | cs 方向无字段定义 |
| 13369 | 获取黑名单列表信息 | cs 方向无字段定义 |
| 13365 | 获取已激活的徽章列表 | cs 方向无字段定义 |
| 13364 | 获取已使用的徽章 | cs 方向无字段定义 |
| 13361 | 获取已获得的外框 | cs 方向无字段定义 |
| 13357 | 删除新消息 | cs 方向无字段定义 |
| 13356 | 查看新消息 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13355 | 获取新消息列表 | cs 方向无字段定义 |
| 13353 | 获取空间送花历史 | cs 方向无字段定义 |
| 13352 | 获取空间足迹（点赞过自己空间的玩家） | cs 方向无字段定义 |
| 13342 | 查看好友状态 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13341 | 请求自己好友状态 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13340 | 打开空间界面 | cs 方向无字段定义 |
| 13336 | 获取本人的勇气值和魅力值 | cs 方向无字段定义 |
| 13331 | 获取本人的勇气值和魅力值 | cs 方向无字段定义 |
| 13328 | 送花送成功,服务端推送 | cs 方向无字段定义 |
| 13323 | 一键清空好友申请 | cs 方向无字段定义 |
| 13322 | 增加的好友列表信息 | cs 方向无字段定义 |
| 13320 | 好友推荐 | cs 方向无字段定义 |
| 13316 | 分组列表信息 | cs 方向无字段定义 |
| 13312 | 通知玩家收到体力 | cs 方向无字段定义 |
| 13311 | 查询赠送体力列表 | cs 方向无字段定义 |
| 13308 | 被动删除好友 | cs 方向无字段定义 |
| 13304 | 服务端告诉客户端;A想加B为好友 | cs 方向无字段定义 |
| 13302 | 告诉客户端某玩家下线 | cs 方向无字段定义 |
| 13301 | 告诉客户端某玩家上线 | cs 方向无字段定义 |
| 13300 | 获取好友列表信息 | cs 方向无字段定义 |
| 13256 | 发起替换队长 | cs 方向无字段定义 |
| 13251 | 设置阵位 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13228 | 取消队伍发布招募 | cs 方向无字段定义 |
| 13226 | 解散队伍 | cs 方向无字段定义 |
| 13225 | 取消快速组队 | cs 方向无字段定义 |
| 13218 | 组队大厅所有队伍 | cs 方向无字段定义 |
| 13213 | 暂离 | cs 方向无字段定义 |
| 13210 | 退出队伍 | cs 方向无字段定义 |
| 13207 | 队长获取申请列表 | cs 方向无字段定义 |
| 13201 | 创建队伍 | cs 方向无字段定义 |
| 13200 | 队伍信息 | cs 方向无字段定义 |
| 13104 | UNKNOWN | cmd_table 无中文名 |
| 13096 | 困神塔每层排行榜,取前3 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13088 | 佣兵无尽试炼战斗结束 | cs 方向无字段定义 |
| 13087 | 推送战斗波数 | cs 方向无字段定义 |
| 13084 | 佣兵无尽试炼面板 | cs 方向无字段定义 |
| 13080 | vip单人副本次数信息 | cs 方向无字段定义 |
| 13076 | 四门绝阵问题答案查看 | cs 方向无字段定义 |
| 13074 | 四门绝阵问题求助 | cs 方向无字段定义 |
| 13073 | 四门绝阵次数信息 | cs 方向无字段定义 |
| 13061 | 鹰愁涧最大波 | cs 方向无字段定义 |
| 13053 | 副本免cd扫荡 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13052 | 英雄试炼获取界面相关信息 | cs 方向无字段定义 |
| 13051 | 结束扫荡 | cs 方向无字段定义 |
| 13050 | 无底洞进入下一层 | cs 方向无字段定义 |
| 13043 | 重置单人塔副本 | cs 方向无字段定义 |
| 13042 | 单人塔副本相关信息 | cs 方向无字段定义 |
| 13035 | 镇妖塔每层排行榜,取前3 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 13028 | 副本开启 | cs 方向无字段定义 |
| 13022 | 极地寻宝统计信息 | cs 方向无字段定义 |
| 13017 | 获取战力输出 | cs 方向无字段定义 |
| 13015 | 获取章节奖励领取情况 | cs 方向无字段定义 |
| 13011 | 所有开启章节的星级情况 | cs 方向无字段定义 |
| 13010 | 获取所有通关的副本ID | cs 方向无字段定义 |
| 13008 | 最高章节 | cs 方向无字段定义 |
| 13001 | 退出副本 | cs 方向无字段定义 |
| 12980 | 封魔录副本排行 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12974 | 单人无尽排行榜伙伴数据 | 含 15 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12973 | 单人无尽试炼排行榜 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12972 | 请求英雄信息 | 含 15 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12971 | 请求角色信息 | 含 8 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12932 | 法宝战力排行榜 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12901 | 101综合战力；排名、性别、角色名、综合实力 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12856 | 元宝兑换伙伴神器积分 | cs 方向无字段定义 |
| 12855 | 刷新伙伴神器商店商品列表 | cs 方向无字段定义 |
| 12853 | 伙伴神器商店，所有商品情况 | cs 方向无字段定义 |
| 12852 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12851 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12850 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12849 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12848 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12847 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12846 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12845 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12844 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12842 | 副本商店2，所有商品情况 | cs 方向无字段定义 |
| 12840 | 兑换商店，所有商品情况 | cs 方向无字段定义 |
| 12838 | 副本商店，所有商品情况 | cs 方向无字段定义 |
| 12836 | 限时商店，所有商品情况 | cs 方向无字段定义 |
| 12835 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12834 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12833 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12831 | 周商店，有购买的商品,没有买过的没有传 | cs 方向无字段定义 |
| 12830 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12829 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12828 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12827 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12826 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12825 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12824 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12820 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12819 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12818 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12817 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12816 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12815 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12814 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12813 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12812 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12811 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12810 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12809 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12808 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12807 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12806 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12804 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_128.luac 验证 |
| 12803 | 元宝商城物品动态变化价格 | cs 方向无字段定义 |
| 12802 | 1、新增商品推，如果id没有，弹界面，插入列表里面；2、同步推（购买成功），如果xs_list为空，需要删除商品，否则，更新商品；3、商品超时客户端请求（需要在left_time加2秒，防死循环），如果xs_list为空，需要删除商品，否则，更新商品 | cs 方向无字段定义 |
| 12801 | 商城商品列表 | cs 方向无字段定义 |
| 12766 | 最近的几条聊天消息(帮派和队伍) | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12764 | 翻译;客户端请求分发翻译1:世界;2:场景;4:帮派;8;队伍; | sc 方向无字段定义 |
| 12763 | 翻译分发;语音翻译1:世界;2:场景;4:帮派;8;队伍; | cs 方向无字段定义 |
| 12761 | 聊天协议；世界，场景，帮派，队伍，传闻，系统 | cs 方向无字段定义 |
| 12724 | 私聊通知类消息(服务端推送) | cs 方向无字段定义 |
| 12723 | 通知客户端已读消息 | sc 方向无字段定义 |
| 12721 | 推送私聊 | cs 方向无字段定义 |
| 12440 | 接取任务奖励的物品推送 | cs 方向无字段定义 |
| 12435 | 猜拳数据 | cs 方向无字段定义 |
| 12434 | 求助 | cs 方向无字段定义 |
| 12432 | 进入下个场景 | cs 方向无字段定义 |
| 12431 | 获取护送相关数据 | cs 方向无字段定义 |
| 12421 | 已完成任务列表 | cs 方向无字段定义 |
| 12416 | 主线任务进度 | cs 方向无字段定义 |
| 12411 | 跑环抽奖 | cs 方向无字段定义 |
| 12410 | 推送跑环任务抽奖 | cs 方向无字段定义 |
| 12409 | 添加可接任务列表 | cs 方向无字段定义 |
| 12408 | 删除可接任务列表 | cs 方向无字段定义 |
| 12407 | 添加已接任务列表 | cs 方向无字段定义 |
| 12406 | 删除已接任务列表 | cs 方向无字段定义 |
| 12405 | 更新已接任务进度 | cs 方向无字段定义 |
| 12401 | 可接任务列表 | cs 方向无字段定义 |
| 12400 | 已接列表 | cs 方向无字段定义 |
| 12215 | 矿攻打超时提示 | cs 方向无字段定义 |
| 12213 | 矿攻占成功(服务端发送) | cs 方向无字段定义 |
| 12212 | 矿废弃提示 | cs 方向无字段定义 |
| 12211 | 上线获取矿信息 | cs 方向无字段定义 |
| 12209 | 矿枯竭提示 | cs 方向无字段定义 |
| 12208 | 获取据点信息 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 12207 | 矿被占领,发送给客户端 | cs 方向无字段定义 |
| 12202 | 勘探提示 | cs 方向无字段定义 |
| 12201 | 勘探 | cs 方向无字段定义 |
| 12101 | 更新功能状态 | cs 方向无字段定义 |
| 12021 | 属性副本冷却时间列表 | cs 方向无字段定义 |
| 12003 | 最高章节 | cs 方向无字段定义 |
| 11999 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_119.luac 验证 |
| 1199 | 心跳包 | cs 方向无字段定义 |
| 11900 | 运营活动基本信息 | cs 方向无字段定义 |
| 11800 | 帮会竞技场报名 | cs 方向无字段定义 |
| 11721 | 领取幸运转盘奖励 | cs 方向无字段定义 |
| 11720 | 刷新幸运转盘 | cs 方向无字段定义 |
| 11717 | 幸运转盘主界面 | cs 方向无字段定义 |
| 11713 | 抽奖一次发送奖励 | cs 方向无字段定义 |
| 11711 | 抽奖一次 | cs 方向无字段定义 |
| 11709 | vip转盘发送奖励 | cs 方向无字段定义 |
| 11708 | vip转盘抽奖 | cs 方向无字段定义 |
| 11707 | vip嘉年华主界面 | cs 方向无字段定义 |
| 11706 | 元宝嘉年华活动倒计时 | cs 方向无字段定义 |
| 11705 | 发送奖励 | cs 方向无字段定义 |
| 11704 | 抽奖 | cs 方向无字段定义 |
| 11703 | 元宝嘉年华主界面 | cs 方向无字段定义 |
| 11702 | 发送奖励 | cs 方向无字段定义 |
| 11701 | 抽奖 | cs 方向无字段定义 |
| 11700 | 嘉年华主界面 | cs 方向无字段定义 |
| 11699 | 保存重置后的翅膀 | cs 方向无字段定义 |
| 11698 | 获取重置后翅膀信息 | cs 方向无字段定义 |
| 11602 | 保存翅膀幻化（不用） | cs 方向无字段定义 |
| 11600 | 翅膀主界面 | cs 方向无字段定义 |
| 11507 | 元宝换灵气 | cs 方向无字段定义 |
| 11506 | 一键领取 | cs 方向无字段定义 |
| 11414 | 准备区获得资产奖励（个人） | cs 方向无字段定义 |
| 11413 | 战场技能 被使用玩家 | cs 方向无字段定义 |
| 11412 | 主动请求角色战区信息 | cs 方向无字段定义 |
| 11411 | 第一次请求英雄榜数据 | cs 方向无字段定义 |
| 11408 | 战区角色数据 | cs 方向无字段定义 |
| 11407 | 准备区新加角色数据 | cs 方向无字段定义 |
| 11406 | 准备区战力数据 | cs 方向无字段定义 |
| 11405 | 离开玩家Id | cs 方向无字段定义 |
| 11402 | 战场内位置广播 | cs 方向无字段定义 |
| 11401 | 离开仙魔战场 | cs 方向无字段定义 |
| 11400 | 进入仙魔战场 | cs 方向无字段定义 |
| 11310 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_113.luac 验证 |
| 11309 | 竞技场5战奖励领奖 | cs 方向无字段定义 |
| 11308 | 竞技场5战奖励数据 | cs 方向无字段定义 |
| 11305 | 刷新对手 | cs 方向无字段定义 |
| 11303 | 晋级挑战 | cs 方向无字段定义 |
| 11240 | 穿戴/脱下符文 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11237 | 获取伙伴羁绊数据 | 含 9 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11224 | 查看其他人伙伴 | 含 13 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11221 | 获取聊天缓存伙伴 | 含 13 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11201 | 获取单个伙伴数据 | cs 方向无字段定义 |
| 11018 | 地图上进攻按钮 返回11010 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 11015 | 刷新自己地下城资产 | cs 方向无字段定义 |
| 11010 | 查看地图上某个玩家地下城数据 | 含 3 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10998 | 客户端版本号 | cs 方向无字段定义 |
| 10997 | 服务器版本标签 | cs 方向无字段定义 |
| 10996 | 新版本客户端版本号 | cs 方向无字段定义 |
| 10995 | 合服服务器ID列表 | cs 方向无字段定义 |
| 10958 | 目标玩家上古神器装备信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10957 | 目标玩家灵器信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10955 | 目标玩家仙座信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10954 | 目标玩家魂环信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10950 | 目标玩家仙灵信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10949 | 目标玩家坐骑信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10948 | 目标玩家装备信息 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10946 | 创号第二天领取神器 | cs 方向无字段定义 |
| 10942 | 客户端请求开启功能 | sc 方向无字段定义 |
| 10934 | 离线经验关闭 | cs 方向无字段定义 |
| 10933 | 离线经验开启 | cs 方向无字段定义 |
| 10932 | 双倍信息 | cs 方向无字段定义 |
| 10931 | 冻结双倍 | cs 方向无字段定义 |
| 10930 | 领取双倍 | cs 方向无字段定义 |
| 10929 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_109.luac 验证 |
| 10928 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_109.luac 验证 |
| 10927 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_109.luac 验证 |
| 10926 | UNKNOWN | 无 fields.json/cmd_table spec，需反汇编 cmd_resolve_109.luac 验证 |
| 10923 | 全服活动的单个活动状态 | 1.4.11 实测 CS 格式与 fields.json(1.4.9) 不一致（实机带 rid） |
| 10921 | 世界等级 | cs 方向无字段定义 |
| 10913 | 特殊buff显示 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10911 | BUFF | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10910 | 大地图数据 | cs 方向无字段定义 |
| 10803 | 新邮件推送 | cs 方向无字段定义 |
| 10802 | 一键提取附件 | cs 方向无字段定义 |
| 10762 | 收去主堡金币 | cs 方向无字段定义 |
| 10761 | 主堡信息 | cs 方向无字段定义 |
| 10757 | 查看各个通道信息 | cs 方向无字段定义 |
| 10755 | 制造道具冷却时间 | cs 方向无字段定义 |
| 10754 | 升级道具冷却时间 | cs 方向无字段定义 |
| 10751 | 开放的道具列表 | cs 方向无字段定义 |
| 10745 | 伐木场加速 | cs 方向无字段定义 |
| 10744 | 收伐木场产出的木头 | cs 方向无字段定义 |
| 10743 | 取消伐木 | cs 方向无字段定义 |
| 10741 | 伐木场信息; | cs 方向无字段定义 |
| 10733 | 设置民房英雄 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10714 | 获取仓库信息 | cs 方向无字段定义 |
| 10713 | 食物房生产食物加速 | cs 方向无字段定义 |
| 10712 | 取消食物房生产食物 | cs 方向无字段定义 |
| 10711 | 获取食物房生产食物 | cs 方向无字段定义 |
| 10710 | 获取食物房生产食物的信息 | cs 方向无字段定义 |
| 10706 | 内城特殊NPC列表 | cs 方向无字段定义 |
| 10705 | 进入内城 | cs 方向无字段定义 |
| 10702 | 所有领地建筑和研究状态 | cs 方向无字段定义 |
| 10651 | 使用修炼笔记 | cs 方向无字段定义 |
| 10650 | 获取天赋开启情况 | cs 方向无字段定义 |
| 10640 | 获取天命技能增加的BUFF效果 | cs 方向无字段定义 |
| 10621 | 修炼技能列表 | cs 方向无字段定义 |
| 10589 | 获取飞升数据 | cs 方向无字段定义 |
| 10561 | 获取材料价格（转成资产） | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10558 | 玩家装备洗练套 | cs 方向无字段定义 |
| 10556 | 提示客户端一键穿装 | sc 方向无字段定义 |
| 10543 | 物品更新扩展字段 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10540 | 英雄换装推送 | 含 8 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10526 | 使用10525返回的唯一id来读取一个聊天页面物品数据 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10517 | 修理全部装备上的装备 | cs 方向无字段定义 |
| 10514 | 一件穿戴 | cs 方向无字段定义 |
| 10502 | 请求角色背包数据 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10500 | 推送角色背包数据 | 含 7 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10423 | 购买技能点 | cs 方向无字段定义 |
| 10422 | 查询购买技能点 | cs 方向无字段定义 |
| 10421 | 角色用的技能点(每次点骑士界面请求一次) | cs 方向无字段定义 |
| 10413 | 推送全部英雄状态 | cs 方向无字段定义 |
| 10396 | 强制关闭客户端 | sc 方向无字段定义 |
| 10389 | 获取头像描述信息 | cs 方向无字段定义 |
| 10334 | 一键学习升级铜钱 | cs 方向无字段定义 |
| 10333 | 一键学习升级 | cs 方向无字段定义 |
| 10332 | 更新角色技能 | cs 方向无字段定义 |
| 10326 | 新增头像列表 | cs 方向无字段定义 |
| 10325 | 头像列表 | cs 方向无字段定义 |
| 10323 | 获取系统设置 | cs 方向无字段定义 |
| 10321 | 购买体力面板数据 | cs 方向无字段定义 |
| 10320 | 购买体力 | cs 方向无字段定义 |
| 10312 | 角色强制下线 | cs 方向无字段定义 |
| 10306 | 角色属性 | cs 方向无字段定义 |
| 10305 | 角色资产信息更新某几个 | cs 方向无字段定义 |
| 10303 | 自己角色面板属性(相当于前面2条 加 10306 合起来的属性) | cs 方向无字段定义 |
| 10302 | 角色资产信息 | cs 方向无字段定义 |
| 10300 | 客户端初始化完毕 | cs 方向无字段定义 |
| 10299 | 测试 | 含 2 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10297 | 挂机状态 | cs 方向无字段定义 |
| 10296 | 设置挂机、取消挂机 | cs 方向无字段定义 |
| 10239 | 更新场景NPC | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10230 | NPC进入场景 | 含 1 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10221 | 获取当前场景所有怪物坐标(挂机用) | cs 方向无字段定义 |
| 10207 | 回到上个场景(用于退出副本或者内城) | cs 方向无字段定义 |
| 10202 | 附近有角色进入场景 | 含 6 条嵌套子消息描述符(reader/fmt)，未计入顶层 fields |
| 10111 | 客户端版本号 | cs 方向无字段定义 |

_共 759 条记录含未确认项。_
