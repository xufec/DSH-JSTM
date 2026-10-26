# 《绝世唐门》协议手册（自动提取）

> 类型：uint8/int8/uint16/int16/uint32/int32/string/float/double/bool/table。`CS*` = 客户端→服务端，`SC*` = 服务端→客户端。

## 命令 ext

- `Dsc11200ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc11215ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc11221ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc11224ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc12972ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc12974ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc14210ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc14299ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc18713ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

- `Dsc18714ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

## 命令 val

- `Dsc20100val`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |
  | code | uint32 |

## 命令 1100

- `CStestLogin_1100`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ticket | string |
  | account | string |

## 命令 1101

- `SCtestLogin_1101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |

## 命令 1110

- `CSAccountLogin_1110`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | args | table(key:string, val:string) |

- `SCAccountLogin_1110`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | roles | table(rid:uint32, srv_id:string, name:string, lev:uint16, sex:uint8, career:uint16, is_online:uint8) |
  | least_career | uint8 |

## 命令 1199

- `CSheartbeast_1199` — 无字段（空消息）
- `SCheartbeast_1199`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | time | uint32 |

## 命令 1200

- `CSSendPackTest_1200`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | len | uint16 |

## 命令 1201

- `CSSendPackTest2_1201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | time | l |
  | id | uint32 |
  | msg | string |

- `SCSendPackTest2_1201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | time | l |
  | id | uint32 |
  | msg | string |

## 命令 attr

- `Dsc10500attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10502attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10526attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10540attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10544attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |

- `Dsc10948attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10949attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10950attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10954attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10955attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10957attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc10958attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11221attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11224attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11237attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11238attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11240attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc11242attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc12971attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc12972attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc12974attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc13802attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc13807attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc15501attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc15801attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc17706attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc18713attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc18828attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc19100attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc20800attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc21400attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc21414attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

- `Dsc21600attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | state | uint8 |

## 命令 gain

- `Dsc13053gain`（?）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |

## 命令 help

- `Dsc13519help`（?）

  | 字段 | 类型 |
  |---|---|---|
  | help_digit | uint8 |
  | help_type | struct<Dsc13519help_digit> |

- `Dsc13542help`（?）

  | 字段 | 类型 |
  |---|---|---|
  | help_digit | uint8 |
  | help_type | struct<Dsc13542help_digit> |

## 命令 list

- `Dcs10299list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | list2 | uint16 |

- `Dsc10299list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | list2 | uint8 |
  | key1 | struct<Dsc10299list2> |

## 命令 misc

- `Dsc10201misc` — 无字段（空消息）
## 命令 10001

- `CSFirstPack_10001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | key | string |

## 命令 10101

- `CSRoleCreate_10101`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint8 |
  | name | string |
  | career | int16 |
  | playform | string |

- `SCRoleCreate_10101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 10102

- `CSRoleLogin_10102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SCRoleLogin_10102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | timestamp | uint32 |
  | world_lev | uint16 |

## 命令 10103

- `CSRoleReLogin_10103`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SCRoleReLogin_10103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | timestamp | uint32 |
  | world_lev | uint16 |

## 命令 10110

- `SCCommitData_10110`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | method | uint8 |
  | url | string |
  | args | table(name:string, value:string) |

## 命令 10111

- `CS_10111` — 无字段（空消息）
- `SC_10111`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cli_ver | uint16 |
  | flag | uint16 |

## 命令 10200

- `CSRoleEnter_10200`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SCRoleEnter_10200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | line_id | uint8 |
  | x | uint16 |
  | y | uint16 |
  | dir | uint8 |

## 命令 10201

- `CSMapGird_10201` — 无字段（空消息）
- `SCMapGird_10201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | roles | table(rid:uint32, srv_id:string, name:string, lev:uint16, career:uint16, vip_lev:uint8, sex:uint8, status:uint8, mspd:uint16, x:uint16, y:uint16, dir:uint8, hidden:uint8, cur_title:uint16, ntm_title:uint32, marry_state:uint8, spouse_name:string, buff_bids:D|Dsc10201buff_bids|, misc_uint8:D|Dsc10201misc_uint8|, misc_uint16:D|Dsc10201misc_uint16|, misc_uint32:D|Dsc10201misc_uint32|, misc_str:D|Dsc10201misc_str|, animate_res:D|Dsc10201animate_res|) |
  | npcs | table(id:uint32, bid:uint32, type:uint8, x:uint16, y:uint16, name:string, misc:D|Dsc10201misc|, animate_res:D|Dsc10201animate_res|, member:D|Dsc10201member|) |
  | mons | table(id:uint32, bid:uint32, type:uint8, name:string, realm:uint8, mspd:uint16, x:uint16, y:uint16, dir:uint8, res_id:string, status:uint8) |
  | elems | table(id:uint32, bid:uint32, type:uint8, sub_type:uint8, name:string, x:uint16, y:uint16, res_id:string) |

## 命令 10202

- `SCMapRole_10202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | roles | table(rid:uint32, srv_id:string, name:string, lev:uint16, career:uint16, vip_lev:uint8, sex:uint8, status:uint8, mspd:uint16, x:uint16, y:uint16, dir:uint8, hidden:uint8, cur_title:uint16, ntm_title:uint32, marry_state:uint8, spouse_name:string, buff_bids:D|Dsc10202buff_bids|, misc_uint8:D|Dsc10202misc_uint8|, misc_uint16:D|Dsc10202misc_uint16|, misc_uint32:D|Dsc10202misc_uint32|, misc_str:D|Dsc10202misc_str|, animate_res:D|Dsc10202animate_res|) |

## 命令 10203

- `SCRoleLeave_10203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_ids | table(rid:uint32, srv_id:string) |
  | bid | uint32 |

## 命令 10204

- `CS_10204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | x | uint16 |
  | y | uint16 |

- `SC_10204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | x | uint16 |
  | y | uint16 |

## 命令 10205

- `CS_10205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | x | uint16 |
  | y | uint16 |

- `SC_10205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | x | uint16 |
  | y | uint16 |

## 命令 10206

- `CS_10206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | x | uint32 |

- `SC_10206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10207

- `CS_10207` — 无字段（空消息）
- `SC_10207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10208

- `SCMapRoleChangeStr_10208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | change_list | table(key:uint8, val:string) |

## 命令 10209

- `SCMapRoleChangeInt_10209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | change_list | table(key:uint8, val:uint32) |

## 命令 10210

- `CSChangeLine_10210`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | line_id | uint8 |

- `SCChangeLine_10210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |

## 命令 10211

- `CSLineRoleNum_10211`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SCLineRoleNum_10211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | all_line_status | table(line_id:uint8, line_status:uint8) |

## 命令 10212

- `SC_10212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |
  | type | uint8 |
  | name | string |
  | realm | uint8 |
  | mspd | uint16 |
  | x | uint16 |
  | y | uint16 |
  | dir | uint8 |
  | res_id | string |
  | status | uint8 |
  | enter_effect | uint8 |

## 命令 10213

- `SC_10213`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | x | uint16 |
  | y | uint16 |

## 命令 10214

- `SC_10214`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | status | uint8 |

## 命令 10215

- `SC_10215`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 10216

- `CS_10216`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10216`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 10217

- `SC_10217`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |
  | type | uint8 |
  | sub_type | uint8 |
  | name | string |
  | x | uint16 |
  | y | uint16 |
  | res_id | string |

## 命令 10218

- `SC_10218`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | role_attrs | table(attr_code:uint8, attr_val:uint32) |

## 命令 10219

- `SC_10219`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | misc_uint8 | table(key:uint8, value:uint8) |
  | misc_uint16 | table(key:uint8, value:uint16) |
  | misc_uint32 | table(key:uint8, value:uint32) |
  | misc_str | table(key:uint8, value:string) |

## 命令 10220

- `SC_10220`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mon_ids | table(id:uint32) |
  | role_ids | table(rid:uint32, srv_id:string) |

## 命令 10221

- `CS_10221` — 无字段（空消息）
- `SC_10221`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mons | table(id:uint32, bid:uint32, x:uint16, y:uint16) |

## 命令 10222

- `CS_10222`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

- `SC_10222`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10223

- `SC_10223`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dynamic_block | table(id:uint8, val:uint8) |

## 命令 10224

- `SC_10224`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | srv_id | string |
  | type | uint8 |
  | val | int32 |

## 命令 10230

- `SC_10230`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |
  | type | uint8 |
  | x | uint16 |
  | y | uint16 |
  | name | string |
  | misc | table(key:uint8, value:uint16) |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | member | table(sex:uint8, career:uint8, name:string, lev:uint8, animate_res:D|Dsc10230animate_res|) |

## 命令 10231

- `SC_10231`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 10232

- `CS_10232`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | npc_id | uint32 |
  | id | uint32 |

- `SC_10232`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10233

- `CS_10233`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10233`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | time | uint32 |

## 命令 10239

- `SC_10239`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |
  | type | uint8 |
  | x | uint16 |
  | y | uint16 |
  | name | string |
  | misc | table(key:uint8, value:uint16) |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | member | table(sex:uint8, career:uint8, name:string, lev:uint8, animate_res:D|Dsc10239animate_res|) |

## 命令 10250

- `SC_10250`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | animate_res_replace | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | animate_res_del | table(ant_id:uint16, ant_val:string) |

## 命令 10295

- `SC_10295`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | key | string |
  | str_val | string |
  | int_val | int32 |

## 命令 10296

- `CS_10296` — 无字段（空消息）
- `SC_10296`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | status | uint8 |

## 命令 10297

- `CS_10297` — 无字段（空消息）
- `SC_10297`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |

## 命令 10299

- `CSTestData_10299`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | args | table(list:D|Dcs10299list|) |

- `SCTestData_10299`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | args | table(list:D|Dsc10299list|) |

## 命令 10300

- `CSRoleInit_10300` — 无字段（空消息）
## 命令 10301

- `CS_10301` — 无字段（空消息）
- `SC_10301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint16 |
  | is_vip | uint8 |
  | vip_lev | uint8 |
  | sex | uint8 |
  | career | uint16 |
  | face_id | uint16 |
  | cur_title | uint16 |
  | ntm_title | uint32 |
  | gid | uint32 |
  | gsrv_id | string |
  | position | uint8 |
  | gname | string |
  | mspd | uint16 |
  | volume | uint8 |
  | store_volume | uint8 |
  | store_partner_volume | uint8 |
  | volume_open | uint8 |
  | store_volume_open | uint8 |
  | store_partner_volume_open | uint8 |
  | exp_max | uint32 |
  | exp_total_nextlev | uint32 |
  | attr_point | uint16 |
  | profit_exp | uint32 |
  | marry_state | uint8 |
  | spouse_name | string |
  | head_bid | uint32 |
  | chat_bubble | uint32 |
  | skill_list | table(bid:uint32) |
  | buffs | table(bid:uint32, duration:uint32, count:uint8, effect:D|Dsc10301effect|) |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | misc_uint8 | table(key:uint8, value:uint8) |
  | misc_uint16 | table(key:uint8, value:uint16) |
  | misc_uint32 | table(key:uint8, value:uint32) |
  | misc_str | table(key:uint8, value:string) |
  | spouse_rid | uint32 |
  | spouse_srv_id | string |
  | insight_status | uint8 |
  | jid | uint32 |
  | j_srv_id | string |
  | jlev | uint8 |
  | j_title | string |

## 命令 10302

- `CS_10302` — 无字段（空消息）
- `SC_10302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint16 |
  | exp | uint32 |
  | gold | uint32 |
  | gold_acc | uint32 |
  | coin | uint32 |
  | sinew | uint32 |
  | experience | uint32 |
  | coupon | uint32 |
  | vitality | uint32 |
  | guild_contrib | uint32 |
  | practice_exp | uint32 |
  | tower_cent | uint32 |
  | arena_cent | uint32 |
  | integral | uint32 |
  | cash_coupon | uint32 |
  | dan_point | uint32 |
  | guild_active | uint32 |
  | marriage | uint32 |
  | course | uint32 |
  | vip_exp | uint32 |
  | lingshi | uint32 |
  | peak_point | uint32 |
  | black_soul | uint32 |
  | lottery_point | uint32 |
  | boss_point | uint32 |
  | partner_shenqi_point | uint32 |
  | jiebai_cent | uint32 |
  | rune_exp | uint32 |
  | rune_chip | uint32 |

## 命令 10303

- `CS_10303` — 无字段（空消息）
- `SC_10303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint16 |
  | is_vip | uint8 |
  | vip_lev | uint8 |
  | sex | uint8 |
  | career | uint16 |
  | volume | uint8 |
  | store_volume | uint8 |
  | store_partner_volume | uint8 |
  | volume_open | uint8 |
  | store_volume_open | uint8 |
  | store_partner_volume_open | uint8 |
  | attr_point | uint16 |
  | skill_list | table(bid:uint32) |
  | power | uint32 |
  | exp | uint32 |
  | gold | uint32 |
  | coin | uint32 |
  | gold_acc | uint32 |
  | sinew | uint32 |
  | experience | uint32 |
  | coupon | uint32 |
  | vitality | uint32 |
  | guild_contrib | uint32 |
  | practice_exp | uint32 |
  | tower_cent | uint32 |
  | arena_cent | uint32 |
  | attr | table(strength:uint16, intellect:uint16, armor:uint16, constiution:uint16, atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, red_def_s:uint32, red_def_p:uint32, atk_abs:uint32, def_abs:uint32, reduce:uint32, hurt:uint32, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | mspd | uint16 |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | vip_exp | uint32 |
  | jiebai_title | string |
  | jiebai_lev | uint8 |

## 命令 10304

- `CS_10304`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint16 |
  | is_vip | uint8 |
  | vip_lev | uint8 |
  | sex | uint8 |
  | career | uint16 |
  | volume | uint8 |
  | store_volume | uint8 |
  | store_partner_volume | uint8 |
  | volume_open | uint8 |
  | store_volume_open | uint8 |
  | store_partner_volume_open | uint8 |
  | attr_point | uint16 |
  | skill_list | table(bid:uint32) |
  | power | uint32 |
  | exp | uint32 |
  | gold | uint32 |
  | coin | uint32 |
  | gold_acc | uint32 |
  | sinew | uint32 |
  | experience | uint32 |
  | coupon | uint32 |
  | vitality | uint32 |
  | guild_contrib | uint32 |
  | practice_exp | uint32 |
  | tower_cent | uint32 |
  | arena_cent | uint32 |
  | attr | table(strength:uint16, intellect:uint16, armor:uint16, constiution:uint16, atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, red_def_s:uint32, red_def_p:uint32, atk_abs:uint32, def_abs:uint32, reduce:uint32, hurt:uint32, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | mspd | uint16 |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | vip_exp | uint32 |
  | jiebai_title | string |
  | jiebai_lev | uint8 |

## 命令 10305

- `CS_10305` — 无字段（空消息）
- `SC_10305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assets | table(label:uint8, val:uint32) |

## 命令 10306

- `CS_10306` — 无字段（空消息）
- `SC_10306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | attr | table(strength:uint16, intellect:uint16, armor:uint16, constiution:uint16, atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, red_def_s:uint32, red_def_p:uint32, atk_abs:uint16, def_abs:uint16, reduce:uint16, hurt:uint16, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | mspd | uint16 |
  | power | uint32 |

## 命令 10310

- `SC_10310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | is_show | uint8 |
  | msg | string |

## 命令 10311

- `CS_10311`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

- `SC_10311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10312

- `CS_10312` — 无字段（空消息）
## 命令 10320

- `CS_10320` — 无字段（空消息）
- `SC_10320`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | times | uint8 |

## 命令 10321

- `CS_10321` — 无字段（空消息）
- `SC_10321`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | times | uint8 |

## 命令 10322

- `CS_10322`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Code | uint8 |

- `SC_10322`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Code1 | uint8 |

## 命令 10323

- `CS_10323` — 无字段（空消息）
- `SC_10323`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Code | uint8 |

## 命令 10324

- `CS_10324`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |
  | is_rename | uint8 |

- `SC_10324`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | name | string |

## 命令 10325

- `CS_10325` — 无字段（空消息）
- `SC_10325`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | face_list | table(face_id:uint16) |

## 命令 10326

- `CS_10326` — 无字段（空消息）
- `SC_10326`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | face_list | table(face_id:uint16) |

## 命令 10327

- `CS_10327`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | face_id | uint16 |

- `SC_10327`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | face_id | uint16 |

## 命令 10328

- `CS_10328`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | assets | table(label:uint16, val:uint16) |

- `SC_10328`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | point | uint16 |

## 命令 10331

- `CS_10331`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint32 |

- `SC_10331`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10332

- `CS_10332` — 无字段（空消息）
- `SC_10332`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | skill_list | table(bid:uint32) |

## 命令 10333

- `CS_10333` — 无字段（空消息）
- `SC_10333`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10334

- `CS_10334` — 无字段（空消息）
- `SC_10334`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | coin | uint32 |

## 命令 10340

- `CS_10340`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | img | bool |
  | size | uint32 |

- `SC_10340`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | img_id | uint32 |

## 命令 10341

- `CS_10341`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id_list | table(rid:uint32, srv_id:string, upload_time:uint32) |

- `SC_10341`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | id | uint32 |
  | img | bool |
  | upload_time | uint32 |

## 命令 10342

- `SC_10342`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | profit_exp | uint32 |

## 命令 10343

- `CS_10343`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | new_name | string |
  | auto_buy | uint8 |

- `SC_10343`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10346

- `SC_10346`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | id | uint32 |

## 命令 10347

- `SC_10347`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | face_list | table(rid:uint32, srv_id:string, id:uint32, upload_time:uint32) |

## 命令 10348

- `CS_10348`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | face_id | uint16 |

- `SC_10348`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | face_id | uint16 |
  | msg | string |

## 命令 10388

- `CS_10388`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id_list | table(id:uint32, srv_id:string) |

- `SC_10388`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | online_roles | table(id:uint32, srv_id:string) |

## 命令 10389

- `CS_10389` — 无字段（空消息）
- `SC_10389`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | photos | table(id:uint16, upload_time:uint32, status:uint8, default:uint8, offset_id:uint16) |

## 命令 10390

- `CS_10390`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |
  | len | uint32 |

- `SC_10390`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 10391

- `CS_10391`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

- `SC_10391`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | data | string |

## 命令 10396

- `SC_10396` — 无字段（空消息）
## 命令 10397

- `CS_10397`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |

## 命令 10399

- `CSGMCommand_10399`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

- `SCGMCommand_10399`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10401

- `CSHeroBag_10401` — 无字段（空消息）
- `SCHeroBag_10401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bag | table(bid:uint32, color:uint8, lev:uint8, exp:uint32, state:uint8, chip:uint16, skill:D|Dsc10401skill|) |
  | hero_chip | table(bid:uint32, chip:uint16) |

## 命令 10402

- `CSHeroInfo_10402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroInfo_10402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | lev | uint8 |
  | color | uint8 |
  | exp | uint32 |

## 命令 10403

- `CSHeroAll_10403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroAll_10403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | attr | table(code:uint16, value:uint32) |

## 命令 10404

- `CSHeroBase_10404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroBase_10404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | lev | uint8 |
  | exp | uint32 |
  | color | uint8 |

## 命令 10405

- `CSHeroUpQ_10405`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroUpQ_10405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hero_bid | uint32 |
  | color | uint8 |
  | chip | uint16 |
  | skills | table(color1:uint8, skill_bid:uint32) |

## 命令 10406

- `CSHeroUpStar_10406`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroUpStar_10406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 10407

- `CSHerosAll_10407`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | args | table(hero_bid:uint32, power:uint32) |

- `SCHerosAll_10407`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_error | table(bid:uint32) |

## 命令 10408

- `SCHeroUpDataChipNum_10408`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_chips | table(hero_bid:uint8, chip:uint32) |

## 命令 10409

- `CSHeroAddExp_10409`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroAddExp_10409`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |
  | exp | uint32 |

## 命令 10410

- `CS_10410`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SC_10410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10411

- `CSHeroSkill_10411`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |

- `SCHeroSkill_10411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | skills | table(skill_bid:uint32) |

## 命令 10412

- `SCHeroState_10412`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint32 |
  | state | uint8 |

## 命令 10413

- `CSHeroStates_10413` — 无字段（空消息）
- `SCHeroStates_10413`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_states | table(hero_bid:uint32, state:uint8) |

## 命令 10414

- `SC_10414`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |

## 命令 10421

- `CSSkillPointInfo_10421` — 无字段（空消息）
- `SCSkillPointInfo_10421`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | max_point | uint8 |
  | cur_point | uint8 |
  | sec | uint16 |

## 命令 10422

- `CSQryBuySkillPoint_10422` — 无字段（空消息）
- `SCQryBuySkillPoint_10422`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |
  | gold | uint16 |
  | add_point | uint16 |

## 命令 10423

- `CSBuySkillPoint_10423` — 无字段（空消息）
- `SCBuySkillPoint_10423`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | cur_point | uint16 |

## 命令 10424

- `CSSkillUpLev_10424`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | skill_bid | uint32 |

- `SCSkillUpLev_10424`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | skill_bid | uint32 |
  | new_skill_bid | uint32 |

## 命令 10500

- `SCAddRoleBag_10500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10500attrs_ext|, attrs_ext_list:D|Dsc10500attrs_ext_list|, attrs_ext_one_list:D|Dsc10500attrs_ext_one_list|, jewel_list:D|Dsc10500jewel_list|, str_ext_list:D|Dsc10500str_ext_list|) |

## 命令 10501

- `SCNumUpdate_10501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | num_up_arr | table(item_id:uint32, new_qty:uint16) |

## 命令 10502

- `CSRoleBag_10502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |

- `SCRoleBag_10502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10502attrs_ext|, attrs_ext_list:D|Dsc10502attrs_ext_list|, attrs_ext_one_list:D|Dsc10502attrs_ext_one_list|, jewel_list:D|Dsc10502jewel_list|, str_ext_list:D|Dsc10502str_ext_list|) |

## 命令 10503

- `SCDelItems_10503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | del_ids_arr | table(item_id:uint32) |

## 命令 10504

- `CSSellItems_10504`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | items_id | table(item_id:uint32, item_bid:uint32, item_count:uint16) |

- `SCSellItems_10504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10505

- `CSDblclickItem_10505`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | item_id | uint32 |
  | use_num | uint16 |
  | type | uint32 |
  | bid | uint32 |

- `SCDblclickItem_10505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |

## 命令 10506

- `CS_10506`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_item_id | uint32 |
  | hero_bid | uint32 |

- `SC_10506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_item_id | uint32 |
  | item_bid | uint32 |
  | hero_bid | uint32 |
  | eqm_new_pos | uint8 |

## 命令 10507

- `CS_10507`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_10507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10508

- `SC_10508`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | pos_up_arr | table(item_id:uint32, new_pos:uint8) |

## 命令 10509

- `CS_10509`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |

- `SC_10509`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10510

- `SC_10510`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | volume | uint8 |
  | open_volume | uint8 |

## 命令 10511

- `CS_10511`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | hero_bid | uint32 |

- `SC_10511`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | is_auto | uint8 |
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | eqm_new_pos | uint8 |
  | hero_bid | uint32 |

## 命令 10512

- `CS_10512`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

- `SC_10512`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

## 命令 10513

- `CS_10513`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_10513`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | eqm_item_id_new | uint32 |
  | eqm_item_bid_new | uint32 |
  | eqm_item_power_new | uint32 |

## 命令 10514

- `CS_10514` — 无字段（空消息）
- `SC_10514`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_to_eqm | table(bag_item_id:uint32, eqm_new_pos:uint8) |
  | bag_replace_eqm | table(bag_item_id:uint32, eqm_item_id:uint32, eqm_new_pos:uint8) |

## 命令 10515

- `SC_10515`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | durable_update | table(bag_code:uint8, item_id:uint32, durable:uint16) |

## 命令 10516

- `CS_10516`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |

- `SC_10516`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10517

- `CS_10517` — 无字段（空消息）
- `SC_10517`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10518

- `CS_10518`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_list | table(item_bid:uint32, count:uint16) |

- `SC_10518`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10519

- `CS_10519`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_10519`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | lev | uint8 |
  | power | uint32 |

## 命令 10520

- `CS_10520`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | count | uint16 |
  | state | uint8 |

- `SC_10520`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | color | uint8 |
  | lev | uint8 |
  | exp | uint16 |
  | power | uint32 |

## 命令 10521

- `CS_10521`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | jewel_item_id | uint32 |

- `SC_10521`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | pos | uint8 |

## 命令 10522

- `CS_10522`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | pos | uint8 |

- `SC_10522`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |

## 命令 10523

- `CS_10523`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | gold_state | uint8 |
  | all_state | uint8 |

- `SC_10523`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |
  | bid_list | table(bid:uint32) |

## 命令 10524

- `CS_10524`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | all_state | uint32 |

- `SC_10524`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | fc_bid_list | table(bid:uint32) |
  | bid_list | table(bid:uint32) |

## 命令 10525

- `CS_10525`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from_code | uint8 |
  | item_id | uint32 |

- `SC_10525`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | uniq_id | uint32 |
  | from_code | uint8 |
  | item_id | uint32 |

## 命令 10526

- `CS_10526`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | uniq_id | uint32 |

- `SC_10526`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10526attrs_ext|, attrs_ext_list:D|Dsc10526attrs_ext_list|, attrs_ext_one_list:D|Dsc10526attrs_ext_one_list|, jewel_list:D|Dsc10526jewel_list|, str_ext_list:D|Dsc10526str_ext_list|) |

## 命令 10527

- `CS_10527` — 无字段（空消息）
- `SC_10527`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | state_list | table(lev:uint8, time:uint32, flag:uint8) |

## 命令 10528

- `CS_10528`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | type | uint8 |

- `SC_10528`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | lev | uint8 |
  | state_list | table(lev:uint8, time:uint32, flag:uint8) |

## 命令 10529

- `CS_10529`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code_bag | uint8 |
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_10529`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | code_bag | uint8 |
  | eqm_item_id | uint32 |
  | score | uint16 |
  | power | uint32 |
  | refine | uint16 |
  | attr | table(state:uint8, code:uint8, value:uint32) |

## 命令 10530

- `CS_10530`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | jewel_pos | uint8 |
  | state | uint8 |

- `SC_10530`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | jewel_pos | uint8 |
  | jewel_bid | uint8 |

## 命令 10531

- `CS_10531`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_list | table(item_bid:uint32) |

- `SC_10531`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_coin | table(item_bid:uint32, coin:uint32) |

## 命令 10532

- `CS_10532`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | type | uint8 |
  | item_id | uint32 |

- `SC_10532`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | val | int32 |

## 命令 10533

- `CS_10533`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | partner_id | uint32 |

- `SC_10533`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

## 命令 10534

- `CS_10534`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_10534`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

## 命令 10535

- `SC_10535`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gift_item_bid | uint32 |
  | item_list | table(item_bid:uint32, num:uint32, bind:uint8) |
  | assets_list | table(item_bid:uint32, num:uint32) |

## 命令 10536

- `CS_10536`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |
  | item_num | uint32 |

- `SC_10536`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid_list | table(bid:uint32, num:uint32) |

## 命令 10537

- `CS_10537`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_10537`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_id | uint32 |

## 命令 10540

- `SC_10540`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_list | table(hero_bid:uint32, items:D|Dsc10540items|) |

## 命令 10541

- `CS_10541`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_10541`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | grade | uint8 |
  | power | uint32 |

## 命令 10542

- `SC_10542`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | val | string |
  | msg | string |

## 命令 10543

- `SC_10543`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | up_date_ext | table(item_id:uint32, attrs_ext:D|Dsc10543attrs_ext|) |

## 命令 10544

- `CS_10544` — 无字段（空消息）
- `SC_10544`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | attrs_ext_list | table(id:uint8, skill_list:D|Dsc10544skill_list|, attr:D|Dsc10544attr|) |

## 命令 10545

- `CS_10545`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id_1 | uint32 |
  | eqm_item_id_2 | uint32 |

- `SC_10545`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | new_eqm_item_id | uint32 |

## 命令 10546

- `CS_10546`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_10546`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | new_eqm_item_id | uint32 |
  | skill_list | table(bid:uint32) |
  | attr | table(code:uint8, value:uint32) |

## 命令 10547

- `CS_10547`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id_1 | uint32 |

- `SC_10547`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10548

- `SC_10548`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | val | uint32 |
  | msg | string |

## 命令 10551

- `CS_10551`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_10551`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |

## 命令 10552

- `CS_10552`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | volume | uint8 |
  | state | uint8 |

- `SC_10552`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | old | uint16 |
  | new | uint16 |

## 命令 10553

- `CS_10553`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from_code | uint8 |
  | from_item_id | uint32 |
  | to_code | uint8 |
  | to_item_id | uint32 |

- `SC_10553`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | from_code | uint8 |
  | from_item_id | uint32 |
  | to_code | uint8 |
  | to_item_id | uint32 |

## 命令 10554

- `CS_10554`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from_code | uint8 |
  | target_code | uint8 |
  | item_id | uint32 |

- `SC_10554`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | from_code | uint8 |
  | target_code | uint8 |
  | item_id | uint32 |

## 命令 10555

- `CS_10555`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | items_id | table(item_id:uint32, item_bid:uint32, item_count:uint16) |

- `SC_10555`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10556

- `SC_10556` — 无字段（空消息）
## 命令 10557

- `CS_10557`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | args | table(id:uint32) |

- `SC_10557`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10558

- `CS_10558` — 无字段（空消息）
- `SC_10558`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | suit_lev | uint16 |
  | next_suit_lev | uint16 |

## 命令 10560

- `CS_10560`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | args | table(id:uint32) |

- `SC_10560`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | args | table(id:uint32, type:uint8, num:uint32) |

## 命令 10561

- `CS_10561`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | key | uint16 |
  | args | table(bid:uint32, num:uint16) |

- `SC_10561`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | key | uint16 |
  | args | table(bid:uint32, num:uint16, assets:D|Dsc10561assets|) |

## 命令 10570

- `CS_10570`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | ItemIdList | table(id:uint32) |

- `SC_10570`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 10571

- `CS_10571`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |
  | is_buy | uint8 |

- `SC_10571`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_id | uint32 |
  | star_lev | uint8 |
  | star_grid | uint8 |

## 命令 10572

- `CS_10572`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gift_id | uint32 |
  | chose_ids | table(id:uint32) |
  | count | uint16 |

- `SC_10572`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10573

- `CS_10573`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_10573`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 10574

- `CS_10574`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10574`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | id | uint32 |
  | msg | string |

## 命令 10575

- `CS_10575`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10575`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | id | uint32 |
  | msg | string |

## 命令 10576

- `CS_10576`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10576`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | id | uint32 |
  | msg | string |

## 命令 10577

- `SC_10577`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 10578

- `CS_10578`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_10578`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10582

- `SC_10582`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |
  | item_bid | uint32 |
  | type | uint8 |
  | item_list | table(bid:uint32, cnt:uint32) |

## 命令 10586

- `CS_10586`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ItemIdList | table(id:uint32) |

- `SC_10586`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10587

- `CS_10587`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | hero_bid | uint32 |

- `SC_10587`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | is_auto | uint8 |
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | eqm_new_pos | uint8 |
  | hero_bid | uint32 |

## 命令 10588

- `CS_10588`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

- `SC_10588`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

## 命令 10589

- `CS_10589` — 无字段（空消息）
- `SC_10589`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flyup_lev | uint8 |
  | flyup_stage | uint8 |
  | exp | uint32 |
  | dan_cnt | uint8 |

## 命令 10590

- `CS_10590`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ItemIdList | table(id:uint32) |

- `SC_10590`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | ItemIdList | table(id:uint32) |

## 命令 10591

- `CS_10591`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | use_num | uint8 |

- `SC_10591`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |
  | use_num | uint8 |

## 命令 10592

- `CS_10592` — 无字段（空消息）
- `SC_10592`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | GiftList | table(id:uint32, cnt:uint16, assest:uint8, price:uint32, ShowList:D|Dsc10592ShowList|, ico:string, title:string, title2:string, top_banner:string, price2:uint32) |

## 命令 10593

- `CS_10593`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10593`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | cnt | uint16 |

## 命令 10601

- `CSTestSkillInjure_10601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint32 |

- `SCTestSkillInjure_10601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | p | uint32 |
  | skill_bid | uint32 |
  | lev | uint32 |
  | hero_list | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, energy_max:uint32, def_red_s:uint32, def_red_p:uint32, atk_abs:uint32, def_abs:uint32, reduce:uint32, hurt:uint32, hit_rate:uint32, crit_rate:uint32, updown:uint32, atk_interval:uint32, atk_dis:uint32) |

## 命令 10610

- `CSFithtCheck_10610`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | fight_handle | table(magic_bid:uint32, fps_start:uint16, fps_stop:uint16) |
  | mons_bid_value | table(mon_bid:uint32, value:uint16) |
  | fps | uint32 |

- `SCFithtCheck_10610`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10621

- `CS_10621` — 无字段（空消息）
- `SC_10621`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | world_lev | uint16 |
  | skill_list | table(bid:uint32, exp:uint32) |

## 命令 10622

- `CS_10622`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_10622`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | skill_list | table(bid:uint32, exp:uint32) |

## 命令 10630

- `SC_10630`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | skill_list | table(bid:uint32, type:uint8, cd:uint16) |

## 命令 10631

- `CS_10631`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_10631`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | skill_bid | uint32 |
  | last_time | uint32 |

## 命令 10632

- `CS_10632`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | target_type | uint8 |
  | target_id | uint32 |
  | target_srv_id | string |

- `SC_10632`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | skill_bid | uint32 |
  | last_time | uint32 |

## 命令 10633

- `CS_10633`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | x | uint16 |
  | y | uint16 |

- `SC_10633`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | skill_bid | uint32 |
  | last_time | uint32 |

## 命令 10640

- `CS_10640` — 无字段（空消息）
- `SC_10640`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | buff_list | table(caeer:uint8, buff_bid:uint32) |

## 命令 10650

- `CS_10650` — 无字段（空消息）
- `SC_10650`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | talent_list | table(id:uint16) |

## 命令 10651

- `CS_10651` — 无字段（空消息）
- `SC_10651`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10701

- `CSBulidingResearchUpgrade_10701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |

- `SCBulidingResearchUpgrade_10701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 10702

- `CSBuildingResearchState_10702` — 无字段（空消息）
- `SCBuildingResearchState_10702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | all_building | table(building_type:uint8, lev:uint8) |

## 命令 10705

- `CSEnterManor_10705` — 无字段（空消息）
## 命令 10706

- `CSManorNpcList_10706` — 无字段（空消息）
- `SCManorNpcList_10706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_list | table(npc_bid:uint32) |

## 命令 10707

- `SCManorAddNpc_10707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |
  | type | uint8 |

## 命令 10708

- `SCManorDelNpc_10708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |

## 命令 10709

- `CSManorSelectFood_10709`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | time | uint16 |

- `SCManorSelectFood_10709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10710

- `CSManorFood_10710` — 无字段（空消息）
- `SCManorFood_10710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | store_num | uint32 |
  | status | uint8 |
  | left_time | uint32 |
  | total_time | uint32 |

## 命令 10711

- `CSGainManorFood_10711` — 无字段（空消息）
- `SCGainManorFood_10711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | val | uint32 |

## 命令 10712

- `CSCancelManorFood_10712` — 无字段（空消息）
- `SCCancelManorFood_10712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10713

- `CSFastProduceFood_10713` — 无字段（空消息）
- `SCFastProduceFood_10713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10714

- `CSStorehouseInfo_10714` — 无字段（空消息）
- `SCStorehouseInfo_10714`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | InfoList | table(type:uint8, cur_val:uint32, max_val:uint32, show_max_val:uint32) |

## 命令 10715

- `SC_10715`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | TypeList | table(type:uint8) |

## 命令 10716

- `SC_10716`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | val | uint32 |

## 命令 10731

- `CSBuildHouseInfo_10731`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Type | uint8 |

- `SCBuildHouseInfo_10731`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Type | uint8 |
  | lev | uint8 |
  | gold | uint32 |
  | next_time | uint16 |

## 命令 10733

- `CSSetHouseHeroList_10733`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_list | table(Type:uint8, hero_bid:uint32) |

- `SCSetHouseHeroList_10733`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | set_house_hero_return | table(Type:uint8, hero_list:D|Dsc10733hero_list|) |

## 命令 10734

- `CSGetHouseGold_10734`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Type | uint8 |

- `SCGetHouseGold_10734`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | gold | uint32 |

## 命令 10735

- `CSBuildHouseHero2_10735` — 无字段（空消息）
- `SCBuildHouseHero2_10735`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | house_hero | table(building_type:uint8, lev:uint8, gold:uint32, next_time:uint16, hero_bid_list:D|Dsc10735hero_bid_list|) |

## 命令 10741

- `CSBuildWoodInfo_10741` — 无字段（空消息）
- `SCBuildWoodInfo_10741`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | status | uint8 |
  | flag | uint8 |
  | time | uint32 |
  | all_time | uint32 |
  | can_get | uint32 |
  | be_rob | uint32 |

## 命令 10742

- `CSMakeWood_10742`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SCMakeWood_10742`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10743

- `CSUnMakeWood_10743` — 无字段（空消息）
- `SCUnMakeWood_10743`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10744

- `CSGetWood_10744` — 无字段（空消息）
- `SCGetWood_10744`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | wood | uint32 |

## 命令 10745

- `CSWoodSpeed_10745` — 无字段（空消息）
- `SCWoodSpeed_10745`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10751

- `CSOpenPropsList_10751` — 无字段（空消息）
- `SCOpenPropsList_10751`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | open_props_list | table(props_id:uint32, props_status:uint8) |

## 命令 10752

- `CSUpgradeProps_10752`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | props_id | uint32 |
  | ext_queue_id | uint32 |

- `SCUpgradeProps_10752`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10753

- `CSMakeProps_10753`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | props_id | uint32 |
  | props_num | uint32 |
  | ext_queue_id | uint32 |

- `SCMakeProps_10753`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10754

- `CSUpgrateTimeList_10754` — 无字段（空消息）
- `SCUpgrateTimeList_10754`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | upgrate_time_list | table(props_id:uint32, props_type:uint32, ext_queue_id:uint32, cool_time:uint32) |

## 命令 10755

- `CSMakeTimeList_10755` — 无字段（空消息）
- `SCMakeTimeList_10755`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | make_time_list | table(props_id:uint32, props_type:uint32, props_num:uint32, ext_queue_id:uint32, cool_time:uint32) |

## 命令 10756

- `CSOpenExtQueue_10756`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | queue_type | uint8 |
  | props_type | uint32 |

- `SCOpenExtQueue_10756`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10757

- `CSLookQueueList_10757` — 无字段（空消息）
- `SCLookQueueList_10757`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | look_queue_list | table(queue_type:uint32, props_type:uint32, ext_queue_id:uint32, is_use:uint8) |

## 命令 10761

- `CSBuildCastleInfo_10761` — 无字段（空消息）
- `SCBuildCastleInfo_10761`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | can_get | uint32 |
  | be_rob | uint32 |
  | next_time | uint16 |

## 命令 10762

- `CSGetCastleGold_10762` — 无字段（空消息）
- `SCGetCastleGold_10762`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | gold | uint32 |

## 命令 10771

- `SC_10771`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | all_building | table(building_type:uint8, lev:uint8) |

## 命令 10800

- `CS_10800` — 无字段（空消息）
- `SC_10800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mail | table(id:uint32, from_name:string, subject:string, content:string, assets:D|Dsc10800assets|, items:D|Dsc10800items|, send_time:uint32, read_time:uint32, time_out:uint32) |

## 命令 10801

- `CS_10801`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 10802

- `CS_10802` — 无字段（空消息）
- `SC_10802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ids | table(id:uint32, read_time:uint32) |
  | msg | string |

## 命令 10803

- `CS_10803` — 无字段（空消息）
- `SC_10803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | from_name | string |
  | subject | string |
  | content | string |
  | assets | table(label:uint8, val:uint32) |
  | items | table(bid:uint32, quantity:uint8) |
  | send_time | uint32 |
  | read_time | uint32 |
  | time_out | uint32 |

## 命令 10804

- `SC_10804`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ids | table(id:uint32) |
  | msg | string |

## 命令 10805

- `CS_10805`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_10805`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | code | uint8 |
  | msg | string |
  | read_time | uint32 |
  | is_delete | uint8 |

## 命令 10810

- `CS_10810`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | issue_type | uint8 |
  | title | string |
  | content | string |

- `SC_10810`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10900

- `CS_10900`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | hour | uint32 |
  | interdict | string |

- `SC_10900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10901

- `CS_10901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | hour | uint32 |
  | banned | string |

- `SC_10901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10902

- `CS_10902`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | stop_role | string |

- `SC_10902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10910

- `CS_10910` — 无字段（空消息）
- `SC_10910`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dnf_info | table(chapter:uint8, rid:uint32, srv_id:string, face_id:uint16, lev:uint8, name:string, x:int16, y:int16, time:uint32) |

## 命令 10911

- `SC_10911`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | buffs | table(bid:uint32, duration:uint32, count:uint8, effect:D|Dsc10911effect|) |

## 命令 10912

- `SC_10912`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | effect | table(key:uint8, val:uint32) |

## 命令 10913

- `SC_10913`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | buffs | table(change_type:uint8, bid:uint32, duration:uint32, count:uint8, effect:D|Dsc10913effect|) |

## 命令 10921

- `CS_10921` — 无字段（空消息）
- `SC_10921`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | world_lev | uint8 |
  | next | uint32 |
  | exp | uint16 |
  | dec_exp | uint16 |
  | open_day | uint16 |

## 命令 10922

- `CS_10922` — 无字段（空消息）
- `SC_10922`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | act_list | table(id:uint16, status:uint8, int_args:D|Dsc10922int_args|) |

## 命令 10923

- `CS_10923`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |

- `SC_10923`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | status | uint8 |
  | int_args | table(val:uint32) |

## 命令 10924

- `CS_10924` — 无字段（空消息）
- `SC_10924`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | act_list | table(id:uint16, status:uint8, int_args:D|Dsc10924int_args|) |

## 命令 10925

- `CS_10925`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |

- `SC_10925`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | status | uint8 |
  | int_args | table(val:uint32) |

## 命令 10930

- `CS_10930` — 无字段（空消息）
- `SC_10930`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | double | uint16 |
  | double_sum | uint16 |

## 命令 10931

- `CS_10931` — 无字段（空消息）
- `SC_10931`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10932

- `CS_10932` — 无字段（空消息）
- `SC_10932`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | double | uint16 |
  | double_sum | uint16 |
  | double_state | uint16 |
  | off_state | uint16 |

## 命令 10933

- `CS_10933` — 无字段（空消息）
- `SC_10933`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10934

- `CS_10934` — 无字段（空消息）
- `SC_10934`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10935

- `SC_10935`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | double | uint16 |

## 命令 10941

- `SC_10941`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

## 命令 10942

- `CS_10942`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

- `SC_10942` — 无字段（空消息）
## 命令 10945

- `CS_10945`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | card_id | string |

- `SC_10945`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | items | table(bid:uint32, quantity:uint32) |

## 命令 10946

- `CS_10946` — 无字段（空消息）
- `SC_10946`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |

## 命令 10947

- `CS_10947`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10947`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint16 |
  | career | uint16 |
  | sex | uint8 |
  | is_vip | uint8 |
  | vip_lev | uint8 |
  | gname | string |
  | cur_title | uint32 |
  | marry_state | uint8 |
  | spouse_name | string |
  | attr | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | power | uint32 |
  | all_power | uint32 |
  | face_id | uint32 |
  | ride | uint8 |
  | lingshou | uint8 |
  | wing | uint8 |
  | has_shenqi | uint8 |
  | refine_suit | uint16 |
  | refine_suit_next | uint16 |
  | misc_uint32 | table(key:uint8, value:uint32) |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | jiebai_title | string |
  | jiebai_lev | uint8 |
  | halo_stage | uint8 |
  | chair_stage | uint8 |
  | spirit | uint8 |
  | flyup_lev | uint8 |

## 命令 10948

- `CS_10948`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10948`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10948attrs_ext|, attrs_ext_list:D|Dsc10948attrs_ext_list|, attrs_ext_one_list:D|Dsc10948attrs_ext_one_list|, jewel_list:D|Dsc10948jewel_list|, str_ext_list:D|Dsc10948str_ext_list|) |

## 命令 10949

- `CS_10949`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10949`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | jie | uint8 |
  | jie_luck | uint16 |
  | grow | uint16 |
  | zz | uint16 |
  | face | uint8 |
  | use | uint8 |
  | skill_list | table(skill_bid_bid:uint32) |
  | attr_list | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, mspd:uint32, tenacity:uint32, hit:uint32, dodge:uint32, crit:uint32, red_def_s:uint32, red_def_p:uint32) |
  | can_item_list | table(jie:uint8, item_bid:uint32, item_num:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10949attrs_ext|, attrs_ext_list:D|Dsc10949attrs_ext_list|, attrs_ext_one_list:D|Dsc10949attrs_ext_one_list|, jewel_list:D|Dsc10949jewel_list|, str_ext_list:D|Dsc10949str_ext_list|) |
  | surface_list | table(surface_id:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 10950

- `CS_10950`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10950`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | jie | uint8 |
  | jie_luck | uint16 |
  | grow | uint16 |
  | zz | uint16 |
  | face | uint8 |
  | use | uint8 |
  | skill_list | table(skill_bid_bid:uint32) |
  | attr_list | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, tenacity:uint32, hit:uint32, dodge:uint32, crit:uint32, red_def_s:uint32, red_def_p:uint32) |
  | can_item_list | table(jie:uint8, item_bid:uint32, item_num:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10950attrs_ext|, attrs_ext_list:D|Dsc10950attrs_ext_list|, attrs_ext_one_list:D|Dsc10950attrs_ext_one_list|, jewel_list:D|Dsc10950jewel_list|, str_ext_list:D|Dsc10950str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 10951

- `CS_10951`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10951`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | color | uint8 |
  | wing_id | uint32 |
  | power | uint32 |
  | wing_skill | table(skill_bid:uint32) |
  | add_attr | table(code:uint8, value:uint32) |
  | star | uint16 |

## 命令 10952

- `CS_10952`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10952`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | use_id | uint32 |
  | shenqi_list | table(id:uint32, lev:uint16, star:uint16, status:uint8, mark:uint16) |

## 命令 10953

- `CS_10953`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | type | uint8 |

- `SC_10953`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 10954

- `CS_10954`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10954`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10954attrs_ext|, attrs_ext_list:D|Dsc10954attrs_ext_list|, attrs_ext_one_list:D|Dsc10954attrs_ext_one_list|, jewel_list:D|Dsc10954jewel_list|, str_ext_list:D|Dsc10954str_ext_list|) |
  | looks | table(id:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 10955

- `CS_10955`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10955`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10955attrs_ext|, attrs_ext_list:D|Dsc10955attrs_ext_list|, attrs_ext_one_list:D|Dsc10955attrs_ext_one_list|, jewel_list:D|Dsc10955jewel_list|, str_ext_list:D|Dsc10955str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 10957

- `CS_10957`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10957`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10957attrs_ext|, attrs_ext_list:D|Dsc10957attrs_ext_list|, attrs_ext_one_list:D|Dsc10957attrs_ext_one_list|, jewel_list:D|Dsc10957jewel_list|, str_ext_list:D|Dsc10957str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 10958

- `CS_10958`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_10958`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc10958attrs_ext|, attrs_ext_list:D|Dsc10958attrs_ext_list|, attrs_ext_one_list:D|Dsc10958attrs_ext_one_list|, jewel_list:D|Dsc10958jewel_list|, str_ext_list:D|Dsc10958str_ext_list|) |

## 命令 10995

- `CS_10995` — 无字段（空消息）
- `SC_10995`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | srv_list | table(srv_id:string) |

## 命令 10996

- `CS_10996` — 无字段（空消息）
- `SC_10996`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cli_ver_list | table(cdn_patch:string, cli_ver:uint16) |

## 命令 10997

- `CS_10997` — 无字段（空消息）
- `SC_10997`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

## 命令 10998

- `CS_10998` — 无字段（空消息）
- `SC_10998`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cli_ver | uint16 |
  | flag | uint16 |

## 命令 10999

- `CS_10999`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 11000

- `CS_11000` — 无字段（空消息）
- `SC_11000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | times | uint8 |
  | ceng_max | uint8 |
  | ceng | uint8 |
  | dnf_base | table(id:uint8, dnf_num:uint8, time:uint32, update_time:uint32, status:uint8, assets:uint32, pitfall:D|Dsc11000pitfall|, hero_list:D|Dsc11000hero_list|, mon_list:D|Dsc11000mon_list|) |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | mon_list | table(bid:uint32, id:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

## 命令 11001

- `CS_11001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |

- `SC_11001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | ceng | uint8 |

## 命令 11002

- `CS_11002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |

- `SC_11002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | times | uint8 |
  | id | uint8 |
  | dnf_num | uint8 |
  | status | uint8 |
  | update_time | uint32 |
  | mon_list | table(bid:uint32, id:uint32) |
  | hero_list | table(bid:uint32) |

## 命令 11003

- `CS_11003`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |
  | hero_list | table(bid:uint32) |

- `SC_11003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | mon_list | table(id:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

## 命令 11004

- `CS_11004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |
  | hero_list | table(bid:uint32) |

- `SC_11004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hero_list | table(bid:uint32) |
  | assets | uint32 |

## 命令 11005

- `CS_11005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | tr_rid | uint32 |
  | tr_srv_id | string |

- `SC_11005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | old_tr_rid | uint32 |
  | old_tr_srv_id | string |
  | new_tr_rid | uint32 |
  | new_tr_srv_id | string |
  | new_tr_name | string |

## 命令 11006

- `CS_11006`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |

- `SC_11006`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | value | uint32 |
  | item_bid | uint32 |

## 命令 11007

- `CS_11007`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |
  | pitfall | uint32 |
  | x | int16 |
  | y | int16 |

- `SC_11007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | x | int16 |
  | y | int16 |

## 命令 11008

- `CS_11008`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | ceng | uint8 |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | mon_list | table(id:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

- `SC_11008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | status | uint8 |
  | time | uint32 |
  | hero_list | table(bid:uint32) |

## 命令 11009

- `SC_11009`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |
  | status | uint8 |

## 命令 11010

- `CS_11010`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_11010`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | name | string |
  | lev | uint8 |
  | face_id | uint16 |
  | sex | uint8 |
  | ceng | uint8 |
  | shield_time | uint32 |
  | be_hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | be_tr_hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | reward | table(code:uint8, value:uint32, item_bid:uint32) |
  | dnf_base | table(id:uint8, dnf_num:uint8, value:uint32, status:uint8, hero_list:D|Dsc11010hero_list|) |

## 命令 11011

- `CS_11011`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_11011`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | ceng | uint8 |
  | num | uint8 |
  | set_hero_list | table(bid:uint32) |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | tr_hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

## 命令 11012

- `CS_11012`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tr_rid | uint32 |
  | tr_srv_id | string |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | tr_hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

- `SC_11012`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | reward | table(code:uint8, value:uint32, item_bid:uint32) |

## 命令 11013

- `CS_11013`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |

- `SC_11013`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | status | uint8 |
  | ceng | uint8 |

## 命令 11014

- `CS_11014`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_11014`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | tr_rid | uint32 |
  | tr_srv_id | string |

## 命令 11015

- `CS_11015` — 无字段（空消息）
- `SC_11015`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | reward | table(ceng:uint8, count:uint32) |

## 命令 11016

- `CS_11016`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hero_list_1 | table(bid:uint32) |
  | hero_list_2 | table(bid:uint32) |
  | hero_list_3 | table(bid:uint32) |

- `SC_11016`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11017

- `CS_11017` — 无字段（空消息）
- `SC_11017`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | set_hero_list | table(num:uint8, hero_list:D|Dsc11017hero_list|) |

## 命令 11018

- `CS_11018`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_11018`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | set_hero_list | table(num:uint8, hero_list:D|Dsc11018hero_list|) |

## 命令 11100

- `CS_11100`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | drama_bid | uint32 |
  | step_id | uint8 |

## 命令 11101

- `SC_11101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | drama_bid | uint32 |

## 命令 11102

- `CS_11102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | drama_bid | uint32 |

- `SC_11102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11110

- `SC_11110`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |
  | act_list | table(id:uint16, act_type:uint8, base_id:uint32, map_bid:uint32, type:uint16, x:uint16, y:uint16, val:uint32, name:string, desc:string) |

## 命令 11111

- `CS_11111`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | bid | uint32 |

- `SC_11111`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11200

- `CS_11200` — 无字段（空消息）
- `SC_11200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | volume | uint8 |
  | volume_open | uint8 |
  | partner_bag | table(id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, grow:uint16, score:uint32, stage:uint8, rebirth:uint8, acc:uint8, partner_attr:D|Dsc11200partner_attr|, power:uint32, aptitude:D|Dsc11200aptitude|, innate_skill:uint32, skill:D|Dsc11200skill|, jindan_skill:D|Dsc11200jindan_skill|, talisman_skill:D|Dsc11200talisman_skill|, ext:D|Dsc11200ext|) |
  | gratis | table(bid:uint32, type:uint8) |

## 命令 11201

- `CS_11201` — 无字段（空消息）
- `SC_11201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |
  | type | uint8 |
  | color | uint8 |
  | lifttime | uint32 |
  | lev | uint8 |
  | exp | uint32 |
  | grow | uint16 |
  | score | uint32 |
  | stage | uint8 |
  | rebirth | uint8 |
  | acc | uint8 |
  | partner_attr | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | power | uint32 |
  | aptitude | table(code:uint32, val:uint32, val_max:uint32) |
  | innate_skill | uint32 |
  | skill | table(skill_bid:uint32) |
  | jindan_skill | table(skill_bid:uint32) |
  | talisman_skill | table(skill_bid:uint32) |
  | ext | table(key:uint32, val:uint32) |

## 命令 11202

- `SC_11202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | exp | uint32 |

## 命令 11203

- `CS_11203`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_11203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11204

- `CS_11204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_11204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | skill | table(skill_bid:uint32) |

## 命令 11205

- `CS_11205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_11205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 11206

- `CS_11206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | state | uint8 |

- `SC_11206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | volume | uint8 |
  | volume_open | uint8 |

## 命令 11207

- `SC_11207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev_list | table(id:uint32, lev:uint8) |

## 命令 11208

- `CS_11208`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | state | uint8 |

- `SC_11208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11209

- `SC_11209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lift_list | table(id:uint32, lifttime:uint16) |

## 命令 11210

- `SC_11210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | lev | uint16 |
  | exp | uint32 |
  | color | uint8 |
  | score | uint32 |
  | partner_attr | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, hit:uint32, dodge:uint32, crit:uint32, tenacity:uint32, hit_rate_show:uint32, dodge_rate_show:uint32, crit_rate_show:uint32, tenacity_rate_show:uint32) |
  | power | uint32 |

## 命令 11211

- `SC_11211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | talisman_skill | table(skill_bid:uint32) |

## 命令 11212

- `CS_11212`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | type | uint8 |

- `SC_11212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | type | uint8 |

## 命令 11213

- `CS_11213`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | attr_code | uint16 |

- `SC_11213`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | attr_code | uint16 |
  | attr_val | uint16 |

## 命令 11214

- `CS_11214`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from_code | uint8 |
  | target_code | uint8 |
  | partner_id | uint32 |

- `SC_11214`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | from_code | uint8 |
  | target_code | uint8 |
  | partner_id | uint32 |

## 命令 11215

- `CS_11215` — 无字段（空消息）
- `SC_11215`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | partner_list | table(id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, grow:uint16, score:uint32, stage:uint8, rebirth:uint8, acc:uint8, partner_attr:D|Dsc11215partner_attr|, power:uint32, aptitude:D|Dsc11215aptitude|, innate_skill:uint32, skill:D|Dsc11215skill|, jindan_skill:D|Dsc11215jindan_skill|, talisman_skill:D|Dsc11215talisman_skill|, ext:D|Dsc11215ext|) |

## 命令 11216

- `CS_11216`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_bid | uint32 |
  | state | uint8 |

- `SC_11216`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | partner_bid | uint32 |

## 命令 11217

- `CS_11217`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | state | uint8 |

- `SC_11217`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 11218

- `CS_11218`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | state | uint8 |

- `SC_11218`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | partner_bid | uint32 |

## 命令 11221

- `CS_11221`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | cache_id | uint32 |

- `SC_11221`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cache_id | uint32 |
  | partner_list | table(id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, grow:uint16, score:uint32, stage:uint8, rebirth:uint8, acc:uint8, partner_attr:D|Dsc11221partner_attr|, power:uint32, aptitude:D|Dsc11221aptitude|, innate_skill:uint32, skill:D|Dsc11221skill|, jindan_skill:D|Dsc11221jindan_skill|, talisman_skill:D|Dsc11221talisman_skill|, ext:D|Dsc11221ext|) |
  | eqm_list | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc11221attrs_ext|, attrs_ext_list:D|Dsc11221attrs_ext_list|, attrs_ext_one_list:D|Dsc11221attrs_ext_one_list|, jewel_list:D|Dsc11221jewel_list|, str_ext_list:D|Dsc11221str_ext_list|) |

## 命令 11222

- `CS_11222`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_11222`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |

## 命令 11223

- `SC_11223`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | power_list | table(id:uint32, power:uint32) |

## 命令 11224

- `CS_11224`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | id | uint32 |

- `SC_11224`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | partner_list | table(id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, grow:uint16, score:uint32, stage:uint8, rebirth:uint8, acc:uint8, partner_attr:D|Dsc11224partner_attr|, power:uint32, aptitude:D|Dsc11224aptitude|, innate_skill:uint32, skill:D|Dsc11224skill|, jindan_skill:D|Dsc11224jindan_skill|, talisman_skill:D|Dsc11224talisman_skill|, ext:D|Dsc11224ext|) |
  | eqm_list | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc11224attrs_ext|, attrs_ext_list:D|Dsc11224attrs_ext_list|, attrs_ext_one_list:D|Dsc11224attrs_ext_one_list|, jewel_list:D|Dsc11224jewel_list|, str_ext_list:D|Dsc11224str_ext_list|) |

## 命令 11225

- `SC_11225`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | ext | table(key:uint8, val:uint32) |

## 命令 11226

- `CS_11226`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | state | uint8 |

- `SC_11226`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 11227

- `CS_11227`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | hufu_id | uint32 |
  | fazhen_id | uint32 |

- `SC_11227`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 11228

- `CS_11228`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | item_id | uint32 |

- `SC_11228`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 11237

- `CS_11237`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | formation_type | uint32 |

- `SC_11237`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | stage | uint32 |
  | star | uint32 |
  | open_index | uint32 |
  | rune_data | table(index:uint32, rune_list:D|Dsc11237rune_list|) |
  | formation_type | uint32 |
  | partner_list | table(index:uint32, partner_id:uint32) |
  | exp | uint32 |
  | crit_cnt | uint32 |
  | not_crit_cnt | uint32 |
  | break | uint32 |

## 命令 11238

- `CS_11238` — 无字段（空消息）
- `SC_11238`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | stage | uint32 |
  | star | uint32 |
  | open_index | uint32 |
  | rune_data | table(index:uint32, rune_list:D|Dsc11238rune_list|) |
  | exp | uint32 |
  | crit_cnt | uint32 |
  | not_crit_cnt | uint32 |
  | break | uint32 |
  | is_crit | uint8 |

## 命令 11239

- `CS_11239`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | formation_type | uint32 |
  | index | uint32 |
  | partner_id | uint32 |
  | op_type | uint32 |

- `SC_11239`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | formation_type | uint32 |
  | index | uint32 |
  | partner_id | uint32 |
  | op_type | uint32 |

## 命令 11240

- `CS_11240`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint32 |
  | rune_index | uint32 |
  | item_id | uint32 |
  | op_type | uint32 |

- `SC_11240`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | index | uint32 |
  | rune_index | uint32 |
  | item_id | uint32 |
  | op_type | uint32 |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc11240attrs_ext|, attrs_ext_list:D|Dsc11240attrs_ext_list|, attrs_ext_one_list:D|Dsc11240attrs_ext_one_list|, jewel_list:D|Dsc11240jewel_list|, str_ext_list:D|Dsc11240str_ext_list|) |

## 命令 11241

- `CS_11241`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint32 |
  | rune_index | uint32 |
  | item_id | uint32 |
  | item_list | table(item_id:uint32) |

- `SC_11241`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | index | uint32 |
  | rune_index | uint32 |
  | item_id | uint32 |
  | item_lev | uint32 |
  | item_exp | uint32 |
  | item_list | table(item_id:uint32) |

## 命令 11242

- `CS_11242` — 无字段（空消息）
- `SC_11242`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | stage | uint32 |
  | star | uint32 |
  | open_index | uint32 |
  | rune_data | table(index:uint32, rune_list:D|Dsc11242rune_list|) |
  | exp | uint32 |
  | crit_cnt | uint32 |
  | not_crit_cnt | uint32 |
  | break | uint32 |

## 命令 11300

- `CS_11300` — 无字段（空消息）
- `SC_11300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | trophy | uint32 |
  | times | uint8 |
  | index_state | uint8 |
  | pk_show | table(id:uint8, rid:uint32, srv_id:string, name:string, lev:uint16, career:uint16, sex:uint8, trophy:uint32, partner_list:D|Dsc11300partner_list|, arena_soul:uint8) |
  | pk_record | table(type:uint8, rid:uint32, srv_id:string, name:string, result:uint8, trophy:uint32, is_counterattack:uint8, reply_id:string) |

## 命令 11301

- `CS_11301` — 无字段（空消息）
- `SC_11301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | num | uint8 |

## 命令 11302

- `CS_11302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

- `SC_11302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11303

- `CS_11303` — 无字段（空消息）
- `SC_11303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11304

- `SC_11304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | num | uint8 |
  | lev | uint8 |

## 命令 11305

- `CS_11305` — 无字段（空消息）
- `SC_11305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11306

- `CS_11306`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_11306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 11307

- `SC_11307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | trophy | uint32 |
  | pk_record | table(type:uint8, rid:uint32, srv_id:string, name:string, result:uint8, trophy:uint32, is_counterattack:uint8, reply_id:string) |

## 命令 11308

- `CS_11308` — 无字段（空消息）
- `SC_11308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | win_times | uint8 |
  | state | uint8 |

## 命令 11309

- `CS_11309` — 无字段（空消息）
- `SC_11309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | prize | table(bid:uint32, cnt:uint32) |

## 命令 11400

- `CS_11400` — 无字段（空消息）
- `SC_11400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11401

- `CS_11401` — 无字段（空消息）
- `SC_11401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11402

- `CS_11402` — 无字段（空消息）
- `SC_11402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | pos_list | table(rid:uint32, srv_id:string, pos:uint8) |

## 命令 11403

- `CS_11403` — 无字段（空消息）
- `SC_11403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, pos:uint8, pos_y:uint8, realm:uint8, state:uint8, kill_num:uint16, skill_list:D|Dsc11403skill_list|) |

## 命令 11404

- `CS_11404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_11404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | tr_rid | uint32 |
  | tr_srv_id | string |

## 命令 11405

- `CS_11405` — 无字段（空消息）
- `SC_11405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | leave_list | table(rid:uint32, srv_id:string) |

## 命令 11406

- `CS_11406` — 无字段（空消息）
- `SC_11406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | leave_list | table(rid:uint32, srv_id:string, name:string, power:uint32) |

## 命令 11407

- `CS_11407` — 无字段（空消息）
- `SC_11407`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | power | uint32 |

## 命令 11408

- `CS_11408` — 无字段（空消息）
- `SC_11408`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | kill_num | uint8 |
  | cent | uint16 |
  | room_id | uint8 |
  | x_realm | uint16 |
  | m_realm | uint16 |
  | role_list | table(srv_id:string, name:string, cent:uint16, realm:uint8) |

## 命令 11409

- `SC_11409`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | kill_num | uint8 |
  | cent | uint16 |
  | realm_win | uint8 |
  | role_list | table(srv_id:string, name:string, career:uint16, lev:uint8, realm:uint8, kill_num:uint16, cent:uint16) |

## 命令 11410

- `CS_11410`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | sm_lev | uint8 |
  | room_id | uint8 |

- `SC_11410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | sm_lev | uint8 |
  | room_id | uint8 |
  | win_realm | uint8 |
  | role_list | table(srv_id:string, name:string, career:uint16, lev:uint8, realm:uint8, kill_num:uint16, cent:uint16) |

## 命令 11411

- `CS_11411` — 无字段（空消息）
- `SC_11411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | sm_lev | uint8 |
  | room_id | uint8 |
  | win_realm | uint8 |
  | role_list | table(srv_id:string, name:string, career:uint16, lev:uint8, realm:uint8, kill_num:uint16, cent:uint16) |
  | rank | table(lev:uint8, room_id:uint8) |

## 命令 11412

- `CS_11412` — 无字段（空消息）
- `SC_11412`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint8 |
  | realm | uint8 |
  | state | uint8 |
  | skill_list | table(skill_state:uint8) |

## 命令 11413

- `CS_11413` — 无字段（空消息）
- `SC_11413`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | skii_type | uint8 |

## 命令 11414

- `CS_11414` — 无字段（空消息）
- `SC_11414`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assets_list | table(code:uint8, val:uint32) |

## 命令 11500

- `CS_11500` — 无字段（空消息）
- `SC_11500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lingqi | uint32 |
  | garden_work | table(type:uint8, volume:uint8, garden_partner:D|Dsc11500garden_partner|) |

## 命令 11501

- `CS_11501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | partner_id | uint32 |

- `SC_11501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | partner_id | uint32 |
  | state | uint8 |
  | time_out | uint32 |
  | val | uint32 |

## 命令 11502

- `CS_11502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_11502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | volume | uint8 |

## 命令 11503

- `CS_11503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | partner_id | uint32 |

- `SC_11503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | partner_id | uint32 |

## 命令 11504

- `SC_11504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | partner_id | uint32 |
  | state | uint8 |
  | time_out | uint32 |

## 命令 11505

- `SC_11505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lingqi | uint32 |

## 命令 11506

- `CS_11506` — 无字段（空消息）
- `SC_11506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | garden_partner | table(type:uint8, partner_id:uint32) |

## 命令 11507

- `CS_11507` — 无字段（空消息）
- `SC_11507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11600

- `CS_11600` — 无字段（空消息）
- `SC_11600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | color | uint8 |
  | wing_id | uint32 |
  | power | uint32 |
  | wing_skill | table(skill_bid:uint32) |
  | add_attr | table(code:uint8, value:uint32) |
  | star | uint16 |
  | lingxi_num | uint32 |
  | jiewing_id | uint32 |
  | surface_list | table(surface_id:uint32, surface_time:uint32, surface_star:uint32) |

## 命令 11601

- `CS_11601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_buy | uint8 |

- `SC_11601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | wing_id | uint32 |
  | star | uint8 |
  | power | uint32 |

## 命令 11602

- `CS_11602` — 无字段（空消息）
- `SC_11602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | wing_id | uint32 |
  | skill_bid | uint32 |
  | add_attr | table(code:uint8, value:uint32) |
  | power | uint32 |

## 命令 11603

- `CS_11603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_buy | uint8 |

- `SC_11603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | color | uint8 |
  | star | uint16 |
  | wing_id | uint32 |
  | wing_skill | table(skill_bid:uint32) |
  | power | uint32 |

## 命令 11604

- `CS_11604`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_11604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11605

- `CS_11605`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_11605`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11606

- `CS_11606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_11606`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | animate | uint16 |

## 命令 11607

- `CS_11607`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_11607`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 11698

- `CS_11698` — 无字段（空消息）
- `SC_11698`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | wing_id | uint32 |
  | star | uint8 |
  | power | uint32 |

## 命令 11699

- `CS_11699` — 无字段（空消息）
- `SC_11699`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | wing_id | uint32 |
  | star | uint8 |
  | power | uint32 |

## 命令 11700

- `CS_11700` — 无字段（空消息）
- `SC_11700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | free_times | uint8 |
  | all_times | uint8 |
  | reward_coin | uint32 |
  | one_name | string |
  | one_coin | uint32 |
  | record_server | table(name:string, id:uint8, val:uint32) |
  | record_self | table(id:uint8, val:uint32) |

## 命令 11701

- `CS_11701` — 无字段（空消息）
- `SC_11701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint8 |

## 命令 11702

- `CS_11702` — 无字段（空消息）
- `SC_11702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11703

- `CS_11703` — 无字段（空消息）
- `SC_11703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | get_times | uint8 |
  | all_times | uint8 |
  | reward_gold | uint32 |
  | one_name | string |
  | one_coin | uint32 |
  | record_server | table(name:string, id:uint8, val:uint32) |
  | record_self | table(id:uint8, val:uint32) |

## 命令 11704

- `CS_11704` — 无字段（空消息）
- `SC_11704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint8 |

## 命令 11705

- `CS_11705` — 无字段（空消息）
- `SC_11705`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11706

- `CS_11706` — 无字段（空消息）
- `SC_11706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | time | uint32 |

## 命令 11707

- `CS_11707` — 无字段（空消息）
- `SC_11707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_server | table(name:string, id:uint8, val:uint32) |

## 命令 11708

- `CS_11708` — 无字段（空消息）
- `SC_11708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint8 |

## 命令 11709

- `CS_11709` — 无字段（空消息）
- `SC_11709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11710

- `CS_11710`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_11710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | get_times | uint8 |
  | record_server | table(name:string, id:uint8) |
  | record_self | table(id:uint8) |

## 命令 11711

- `CS_11711` — 无字段（空消息）
- `SC_11711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint8 |

## 命令 11712

- `CS_11712`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | count | uint8 |

- `SC_11712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | type | uint8 |
  | msg | string |
  | Items | table(bid:uint32, num:uint8) |

## 命令 11713

- `CS_11713` — 无字段（空消息）
- `SC_11713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11717

- `CS_11717` — 无字段（空消息）
- `SC_11717`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | timestamp | uint32 |
  | free_time | uint8 |
  | holiday_name | string |
  | reward_list | table(index:uint8, id:uint32, item_bid:uint32, cnt:uint16, is_effect:uint8) |
  | record_server | table(name:string, item_bid:uint32, cnt:uint16) |
  | show_list | table(item_bid:uint32, cnt:uint32) |

## 命令 11718

- `CS_11718`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | pay_type | uint8 |

- `SC_11718`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | reward_id | uint32 |
  | record_server | table(name:string, item_bid:uint32, cnt:uint16) |
  | reward | table(item_bid:uint32, cnt:uint16) |

## 命令 11719

- `CS_11719`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | pay_type | uint8 |

- `SC_11719`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | record_server | table(name:string, item_bid:uint32, cnt:uint16) |
  | reward | table(item_bid:uint32, cnt:uint16) |

## 命令 11720

- `CS_11720` — 无字段（空消息）
- `SC_11720`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | free_time | uint8 |
  | reward_list | table(index:uint8, id:uint32, item_bid:uint32, cnt:uint16, is_effect:uint8) |

## 命令 11721

- `CS_11721` — 无字段（空消息）
- `SC_11721`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11800

- `CS_11800` — 无字段（空消息）
- `SC_11800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 11801

- `CS_11801`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | set_line | uint8 |

- `SC_11801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 11900

- `CS_11900` — 无字段（空消息）
- `SC_11900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | first_reward | uint8 |
  | day_reward | uint8 |
  | online_time | uint32 |
  | online_id | uint8 |
  | lev_list | table(lev:uint8) |
  | timer_reward | uint8 |

## 命令 11901

- `CS_11901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_11901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |

## 命令 11902

- `SC_11902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

## 命令 12000

- `CSDungeonIn_12000`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |

- `SCDungeonIn_12000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | mon_list | table(mon_bid:uint32, id:uint8, coin:uint32, wood:uint32) |
  | item_list | table(id:uint8, item_bid:uint32, num:uint8) |

## 命令 12001

- `CS_12001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | finish | uint32 |
  | live_num | uint8 |

- `SC_12001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | star_lev | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8) |

## 命令 12002

- `CS_12002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |

- `SC_12002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | dung_bid | uint32 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(type:uint32, count:uint32) |

## 命令 12003

- `CS_12003` — 无字段（空消息）
- `SC_12003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_bid | uint32 |

## 命令 12004

- `CS_12004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_bid | uint32 |

- `SC_12004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12005

- `CSChapterStar_12005` — 无字段（空消息）
- `SCChapterStar_12005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_star | table(chapter_id:uint32, level_star:D|Dsc12005level_star|) |

## 命令 12006

- `CS_12006`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_12006`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | left_times | uint32 |

## 命令 12007

- `CS_12007`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_12007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | buy_times | uint32 |

## 命令 12008

- `CS_12008`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_12008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | count | uint16 |

## 命令 12021

- `CS_12021` — 无字段（空消息）
- `SC_12021`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | week | uint8 |
  | interval_list | table(dung_type:uint16, sec:uint32) |

## 命令 12022

- `CS_12022`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint16 |

- `SC_12022`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |
  | sec | uint32 |

## 命令 12100

- `CS_12100`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | function_id | uint32 |

- `SC_12100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 12101

- `CS_12101` — 无字段（空消息）
- `SC_12101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | function_list | table(function_id:uint32, status:uint8) |

## 命令 12201

- `CSexplorate_12201` — 无字段（空消息）
- `SCexplorate_12201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | minerals | table(rid:uint32, srv_id:string, id:uint32, type:uint8, lev:uint8, status:uint8, chapter_id:uint8, x:int16, y:int16) |

## 命令 12202

- `CS_12202` — 无字段（空消息）
- `SC_12202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | coin | uint32 |

## 命令 12203

- `CS_12203`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_12203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | status | uint8 |
  | item_id | uint32 |
  | total | uint32 |
  | speed | uint32 |
  | left_time | uint32 |
  | stronghold | table(s_id:uint8, occ_flag:uint8) |

## 命令 12204

- `CS_12204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | s_id | uint8 |

- `SC_12204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12205

- `CS_12205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | s_id | uint8 |
  | flag | uint8 |
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |
  | g_flag | uint8 |
  | g_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

- `SC_12205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | int8 |
  | msg | string |

## 命令 12206

- `CS_12206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | stronghold_id | uint8 |
  | hero_list | table(bid:uint32) |

- `SC_12206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | total | uint32 |
  | speed | uint32 |

## 命令 12207

- `CS_12207` — 无字段（空消息）
- `SC_12207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 12208

- `CS_12208`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | stronghold_id | uint8 |

- `SC_12208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | s_id | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | face_id | uint16 |
  | mon_list | table(bid:uint32, hp:uint32, morale:uint16, is_dead:uint8) |
  | hero_list | table(bid:uint32, lev:uint8, color:uint8, star_lev:uint8, morale:uint16, loyalty:uint8, state:uint8, attr_list:D|Dsc12208attr_list|, skill_list:D|Dsc12208skill_list|, hp:uint32, is_dead:uint8) |

## 命令 12209

- `CS_12209` — 无字段（空消息）
- `SC_12209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 12210

- `CS_12210`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_12210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | lev | uint8 |
  | item_id | uint32 |
  | total | uint32 |

## 命令 12211

- `CS_12211` — 无字段（空消息）
- `SC_12211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | minerals | table(rid:uint32, srv_id:string, id:uint32, type:uint8, lev:uint8, status:uint8, chapter_id:uint8, x:int16, y:int16) |

## 命令 12212

- `CS_12212` — 无字段（空消息）
- `SC_12212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 12213

- `CS_12213` — 无字段（空消息）
- `SC_12213`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | lev | uint8 |
  | item_id | uint32 |
  | total | uint32 |

## 命令 12214

- `CS_12214`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_12214`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | hero_list | table(bid:uint32, morale:uint16, hp:uint32, is_dead:uint8) |

## 命令 12215

- `CS_12215` — 无字段（空消息）
- `SC_12215`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

## 命令 12400

- `CS_12400` — 无字段（空消息）
- `SC_12400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_list | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12401

- `CS_12401` — 无字段（空消息）
- `SC_12401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | missions | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12402

- `CS_12402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_12402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | missions | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12403

- `CS_12403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_12403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12404

- `CS_12404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_12404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | mission_bid | uint32 |

## 命令 12405

- `CS_12405` — 无字段（空消息）
- `SC_12405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | update_mission_list | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12406

- `CS_12406` — 无字段（空消息）
- `SC_12406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | del_mission_list | table(mission_bid:uint32) |

## 命令 12407

- `CS_12407` — 无字段（空消息）
- `SC_12407`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | add_mission_list | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12408

- `CS_12408` — 无字段（空消息）
- `SC_12408`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | delete_list | table(mission_bid:uint32) |

## 命令 12409

- `CS_12409` — 无字段（空消息）
- `SC_12409`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | missions | table(mission_bid:uint32, mission_status:uint8, commit_num:uint16, loop_count:uint16, loop_num:uint16, code:uint8, process_status:uint8, target:uint32, target_value:uint32, value:uint32, show_lave_time:uint8, lave_time:uint32, accept_time:uint32) |

## 命令 12410

- `CS_12410` — 无字段（空消息）
- `SC_12410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | lottery_list | table(id:uint32, item_bid:uint32, item_num:uint32, bind:uint8) |

## 命令 12411

- `CS_12411` — 无字段（空消息）
- `SC_12411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12412

- `CS_12412`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_12412`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | assets | table(code:uint8, num:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |
  | guild_assets | uint32 |
  | guild_wage | uint32 |

## 命令 12413

- `CS_12413` — 无字段（空消息）
- `SC_12413`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | progress_list | table(code:uint32, ext_list:D|Dsc12413ext_list|) |

## 命令 12414

- `CS_12414`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | talk_bid | uint32 |
  | mission_bid | uint32 |
  | npc_bid | uint32 |

- `SC_12414`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | npc_bid | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12415

- `CS_12415`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | item_bid | uint32 |
  | item_num | uint32 |

- `SC_12415`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | item_bid | uint32 |
  | item_num | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12416

- `CS_12416` — 无字段（空消息）
- `SC_12416`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 12417

- `CS_12417`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | partner_id | uint32 |
  | partner_num | uint32 |

- `SC_12417`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | partner_id | uint32 |
  | partner_num | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12418

- `CS_12418`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_12418`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | uniq_id | uint32 |
  | mission_bid | uint32 |

## 命令 12419

- `CS_12419`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | uniq_id | uint32 |

- `SC_12419`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | mission_status | uint8 |
  | commit_num | uint16 |
  | loop_count | uint16 |
  | loop_num | uint16 |
  | code | uint8 |
  | process_status | uint8 |
  | target | uint32 |
  | target_value | uint32 |
  | value | uint32 |
  | show_lave_time | uint8 |
  | lave_time | uint32 |
  | accept_time | uint32 |

## 命令 12420

- `SC_12420`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |

## 命令 12421

- `CS_12421` — 无字段（空消息）
- `SC_12421`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | finish_task_list | table(bid:uint32) |

## 命令 12422

- `CS_12422`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | item_list | table(bid:uint32, num:uint32) |

- `SC_12422`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12430

- `CS_12430`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_12430`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | quantity | uint8 |
  | msg | string |

## 命令 12431

- `CS_12431` — 无字段（空消息）
- `SC_12431`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bonus | table(quantity:uint32, coin:uint32, exp:uint32, hero_exp:uint32) |
  | cur_quantity | uint32 |
  | free_refresh_times | uint8 |
  | times | uint8 |
  | total_times | uint8 |
  | assist_times | uint8 |
  | total_assist_times | uint8 |

## 命令 12432

- `CS_12432` — 无字段（空消息）
- `SC_12432`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12433

- `SC_12433`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | times | uint8 |
  | coin | uint32 |
  | exp | uint32 |
  | hero_exp | uint32 |
  | old_coin | uint32 |
  | old_exp | uint32 |
  | old_hero_exp | uint32 |

## 命令 12434

- `CS_12434` — 无字段（空消息）
- `SC_12434`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12435

- `CS_12435` — 无字段（空消息）
- `SC_12435`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | total_win | uint8 |
  | round | uint8 |
  | quality | uint8 |
  | team_win | table(rid:uint32, srv_id:string, finger:uint8) |

## 命令 12436

- `CS_12436`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | finger | uint8 |

- `SC_12436`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | role_finger | uint8 |

## 命令 12437

- `SC_12437`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | total_win | uint8 |
  | quality | uint8 |

## 命令 12438

- `SC_12438`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | total_win | uint8 |
  | round | uint8 |
  | result | uint8 |
  | win_count | uint8 |
  | quality | uint8 |
  | sys_finger | uint8 |
  | team_win | table(rid:uint32, srv_id:string, finger:uint8, win:uint8) |

## 命令 12439

- `CS_12439`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_12439`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12440

- `CS_12440` — 无字段（空消息）
- `SC_12440`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 12450

- `CS_12450`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_12450`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | question_id | uint32 |
  | answer_id | uint8 |

## 命令 12451

- `CS_12451`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | answer_id | uint8 |

- `SC_12451`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12452

- `SC_12452`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | spouse_answer_id | uint8 |

## 命令 12460

- `CS_12460`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_12460`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12499

- `CS_12499`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_12499`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | num | uint8 |

## 命令 12601

- `CS_12601` — 无字段（空消息）
- `SC_12601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | demon_list | table(bid:uint32, career:uint8, star_lev:uint8, nature:uint8, chip:uint16, action_power:uint32, power:uint32, skill:D|Dsc12601skill|) |
  | demon_chip | table(bid:uint32, chip_num:uint16) |

## 命令 12602

- `CS_12602`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | demon_bid | uint32 |

- `SC_12602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | career | uint8 |
  | star_lev | uint8 |
  | nature | uint8 |
  | chip | uint16 |
  | action_power | uint32 |
  | power | uint32 |
  | skill | table(skill_bid:uint32) |

## 命令 12603

- `CS_12603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | demon_bid | uint32 |

- `SC_12603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | demon_bid | uint32 |
  | code | uint8 |
  | msg | string |
  | skill_new | table(skill_bid:uint32) |

## 命令 12604

- `CS_12604`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | demon_bid | uint32 |

- `SC_12604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 12605

- `SC_12605`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | chip_num | uint16 |

## 命令 12606

- `CS_12606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | demon_bid | uint32 |
  | skill_bid | uint32 |

- `SC_12606`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | demon_bid | uint32 |
  | skill_bid | uint32 |
  | new_skill | uint32 |

## 命令 12720

- `CS_12720`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | to_rid | uint32 |
  | to_srv_id | string |
  | len | uint8 |
  | msg | string |

- `SC_12720`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12721

- `CS_12721` — 无字段（空消息）
- `SC_12721`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint8 |
  | career | uint16 |
  | face_id | uint16 |
  | len | uint8 |
  | msg | string |
  | sex | uint8 |
  | vip_lev | uint8 |
  | capacity | uint8 |
  | head_bid | uint32 |
  | bubble_bid | uint32 |
  | tick | uint32 |

## 命令 12722

- `CS_12722` — 无字段（空消息）
- `SC_12722`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | offline_list | table(rid:uint32, srv_id:string, name:string, lev:uint8, career:uint16, face_id:uint16, sex:uint8, vip_lev:uint8, capacity:uint8, head_bid:uint32, chat_bubble:uint32, msg_list:D|Dsc12722msg_list|) |

## 命令 12723

- `CS_12723`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_12723` — 无字段（空消息）
## 命令 12724

- `CS_12724` — 无字段（空消息）
- `SC_12724`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 12725

- `CS_12725`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | voice | bool |
  | voice_len | uint16 |
  | time | uint8 |
  | type | uint8 |

- `SC_12725`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | srv_id | string |
  | voice_id | uint32 |
  | msg | string |

## 命令 12726

- `CS_12726`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | voice_id | uint32 |

- `SC_12726`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | voice_id | uint32 |
  | time | uint8 |
  | voice | bool |
  | type | uint8 |

## 命令 12741

- `SC_12741`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 12742

- `SC_12742`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | asset_list | table(opt:uint8, key:uint32, val:uint32) |

## 命令 12743

- `SC_12743`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 12744

- `SC_12744`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | msg | string |

## 命令 12761

- `CS_12761` — 无字段（空消息）
- `SC_12761`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career:uint16, vip_lev:uint8, capacity:uint8, head_bid:uint32, bubble_bid:uint32) |
  | channel | uint16 |
  | len | uint8 |
  | msg | string |

## 命令 12762

- `CS_12762`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | len | uint8 |
  | msg | string |

- `SC_12762`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12763

- `CS_12763` — 无字段（空消息）
- `SC_12763`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | id | string |
  | msg | string |

## 命令 12764

- `CS_12764`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | id | string |
  | msg | string |

- `SC_12764` — 无字段（空消息）
## 命令 12766

- `CS_12766`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |

- `SC_12766`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | msg_list | table(role_list:D|Dsc12766role_list|, channel:uint16, len:uint8, msg:string, tick:uint32) |

## 命令 12771

- `CS_12771`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_12771`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | is_online | uint8 |
  | team_id | uint32 |
  | team_srv_id | string |

## 命令 12772

- `CS_12772`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | type | uint8 |
  | content | string |
  | msg | string |

- `SC_12772`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12799

- `SC_12799`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 12801

- `CS_12801` — 无字段（空消息）
- `SC_12801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_shop_lev | uint32 |
  | xs_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, old_price:uint32, price:uint32, type:uint8, ico:uint8, left_time:uint32, can_buy_num:uint16) |

## 命令 12802

- `CS_12802` — 无字段（空消息）
- `SC_12802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | xs_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, old_price:uint32, price:uint32, type:uint8, ico:uint8, left_time:uint32, can_buy_num:uint16) |

## 命令 12803

- `CS_12803` — 无字段（空消息）
- `SC_12803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_list | table(item_bid:uint32, price:uint32) |

## 命令 12805

- `CS_12805`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12805`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |
  | price | uint32 |

## 命令 12821

- `CS_12821`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | bid | uint32 |

- `SC_12821`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |

## 命令 12822

- `CS_12822`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_12822`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | bid | uint32 |

## 命令 12823

- `CS_12823`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |

- `SC_12823`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | huoban_list | table(bid:uint32, num:uint8) |

## 命令 12831

- `CS_12831` — 无字段（空消息）
- `SC_12831`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id_list | table(id:uint16, has_buy_num:uint16) |

## 命令 12832

- `CS_12832`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12832`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |

## 命令 12836

- `CS_12836` — 无字段（空消息）
- `SC_12836`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | goods_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, old_price:uint32, price:uint32, limit_num:uint8, buy_num:uint8) |

## 命令 12837

- `CS_12837`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12837`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |

## 命令 12838

- `CS_12838` — 无字段（空消息）
- `SC_12838`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | goods_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, old_price:uint32, price:uint32, limit_num:uint8, buy_num:uint8) |

## 命令 12839

- `CS_12839`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12839`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |

## 命令 12840

- `CS_12840` — 无字段（空消息）
- `SC_12840`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | goods_list | table(id:uint16, new_item_bid:uint32, new_item_num:uint32, new_bind:uint8, item_bid:uint32, item_num:uint32, limit_num:uint8, buy_num:uint8) |

## 命令 12841

- `CS_12841`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12841`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |

## 命令 12842

- `CS_12842` — 无字段（空消息）
- `SC_12842`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | goods_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, old_price:uint32, price:uint32, limit_num:uint8, buy_num:uint8) |

## 命令 12843

- `CS_12843`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12843`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |

## 命令 12853

- `CS_12853` — 无字段（空消息）
- `SC_12853`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | refresh_time | uint16 |
  | free_time | uint16 |
  | max_time | uint16 |
  | cost | uint16 |
  | count | uint8 |
  | limit_count | uint8 |
  | goods_list | table(id:uint16, item_bid:uint32, bind:uint8, pay_type:uint8, price:uint32, limit_num:uint8, buy_num:uint8) |

## 命令 12854

- `CS_12854`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_12854`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | buy_num | uint8 |

## 命令 12855

- `CS_12855` — 无字段（空消息）
- `SC_12855`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 12856

- `CS_12856` — 无字段（空消息）
- `SC_12856`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | count | uint8 |
  | limit_count | uint8 |

## 命令 12901

- `CS_12901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_role | table(power_eqm_role:uint32, power_skill:uint32, power_xiulian:uint32, power_hero:uint32, power_ride:uint32, power_lingshou:uint32, power_shenqi:uint32, power_wing:uint32, power_fabao:uint32) |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32, rank_role:D|Dsc12901rank_role|, show_partner:D|Dsc12901show_partner|) |

## 命令 12902

- `CS_12902`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32) |

## 命令 12903

- `CS_12903`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12903`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | partner_bid | uint32 |
  | partner_color | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, hero_bid:uint32, val:uint32, color:uint32) |

## 命令 12904

- `CS_12904`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12904`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32) |

## 命令 12911

- `CS_12911`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12911`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32) |

## 命令 12912

- `CS_12912`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12912`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32) |

## 命令 12913

- `CS_12913`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12913`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint16, time:uint16) |

## 命令 12914

- `CS_12914`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12914`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_ride_jie | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, hero_bid:uint32, val:uint16) |

## 命令 12915

- `CS_12915`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12915`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_lingshou_jie | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, hero_bid:uint32, val:uint16) |

## 命令 12916

- `CS_12916`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12916`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_wing_color | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, hero_bid:uint32, val:uint16) |

## 命令 12917

- `CS_12917`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12917`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint16) |

## 命令 12918

- `CS_12918`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12918`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_g_name | string |
  | my_head_name | string |
  | my_g_num | uint16 |
  | rank_list | table(ord:uint8, gid:uint32, g_srv_id:string, g_name:string, head_name:string, g_num:uint16, val:uint16) |

## 命令 12919

- `CS_12919`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12919`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_win_num | uint16 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, award:uint16, val:uint16) |

## 命令 12920

- `CS_12920`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12920`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint16) |

## 命令 12921

- `CS_12921`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12921`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_shenqi_bid | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, hero_bid:uint32, val:uint32) |

## 命令 12922

- `CS_12922`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12922`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, lev:uint8, power:uint32, val:uint16) |

## 命令 12923

- `CS_12923`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12923`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint16) |

## 命令 12924

- `CS_12924`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12924`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, lev:uint8, val:uint32) |

## 命令 12925

- `CS_12925`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12925`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12926

- `CS_12926`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12926`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12927

- `CS_12927`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12927`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_ride_jie | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32, hero_bid:uint32) |

## 命令 12928

- `CS_12928`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12928`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_jie | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32, jie:uint8) |

## 命令 12929

- `CS_12929`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12929`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12930

- `CS_12930`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12930`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12931

- `CS_12931`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12931`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint8, val:uint32) |

## 命令 12932

- `CS_12932`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12932`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_fabao_list | table(my_bid:uint32, my_power:uint32, my_level:uint16, my_stage:uint8, my_skill_list:D|Dsc12932my_skill_list|, my_effect_level:uint16) |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, all_power:uint32, fabao_list:D|Dsc12932fabao_list|) |

## 命令 12933

- `CS_12933`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12933`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12934

- `CS_12934`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12934`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_hero_bid | uint32 |
  | grow | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, val:uint32, hero_bid:uint32, grow:uint32) |

## 命令 12971

- `CS_12971`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | rid | uint32 |
  | srv_id | string |
  | flag | uint8 |

- `SC_12971`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | rid | uint32 |
  | srv_id | string |
  | role_list | table(name:string, sex:uint8, career:uint16, lev:uint8, guild_name:string, power:uint32, power_eqm_role:uint32, power_lev:uint32, power_skill:uint32, power_xiulian:uint32, power_hero:uint32, power_ride:uint32, power_lingshou:uint32, power_shenqi:uint32, power_wing:uint32, my_power:uint32, my_power_eqm_role:uint32, my_power_lev:uint32, my_power_skill:uint32, my_power_xiulian:uint32, my_power_hero:uint32, my_power_ride:uint32, my_power_lingshou:uint32, my_power_shenqi:uint32, my_power_wing:uint32, items:D|Dsc12971items|) |

## 命令 12972

- `CS_12972`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | rid | uint32 |
  | srv_id | string |
  | flag | uint8 |

- `SC_12972`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | rid | uint32 |
  | srv_id | string |
  | role_list | table(partner_list:D|Dsc12972partner_list|, eqm_list:D|Dsc12972eqm_list|) |

## 命令 12973

- `CS_12973`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12973`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | partner_list | table(rid:uint32, srv_id:string, bid:uint32, partner_id:uint32, color:uint8, rebirth:uint8) |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32, partner_list:D|Dsc12973partner_list|) |

## 命令 12974

- `CS_12974`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | bid | uint32 |

- `SC_12974`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint16 |
  | rid | uint32 |
  | srv_id | string |
  | role_list | table(partner_list:D|Dsc12974partner_list|, eqm_list:D|Dsc12974eqm_list|) |

## 命令 12977

- `CS_12977`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12977`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint16) |

## 命令 12978

- `CS_12978`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12978`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint16) |

## 命令 12979

- `CS_12979`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12979`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12980

- `CS_12980`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12980`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | my_ord | uint8 |
  | my_val | uint8 |
  | my_sec | uint32 |
  | my_team_member | table(leader:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, lev:uint8, head_bid:uint32) |
  | rank_list | table(ord:uint8, floor:uint8, use_sec:uint32, team_member:D|Dsc12980team_member|) |

## 命令 12986

- `CS_12986`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12986`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_mingge_stage | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, lev:uint8, career:uint8, sex:uint8, head_bid:uint32, val:uint32, mingge_stage:uint8) |

## 命令 12988

- `CS_12988`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12988`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, lev:uint8, career:uint8, sex:uint8, head_bid:uint32, val:uint32) |

## 命令 12994

- `CS_12994`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12994`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint16 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, friend_val:uint32, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, lev:uint8) |

## 命令 12995

- `CS_12995`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12995`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12996

- `CS_12996`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12996`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12997

- `CS_12997`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12997`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 12998

- `CS_12998`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12998`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_ring_lev | uint8 |
  | my_ring_star | uint16 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, val:uint32, ring_lev:uint8, ring_star:uint16, career:uint8) |

## 命令 12999

- `CS_12999`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_12999`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 13000

- `CS_13000`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |

- `SC_13000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13001

- `CS_13001` — 无字段（空消息）
- `SC_13001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13002

- `SC_13002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | use_time | uint32 |
  | task_all | uint8 |
  | task_process_cur | uint8 |
  | task_tips | string |
  | task_type | uint8 |
  | arg_list | table(arg:uint32) |
  | cur_task_num | uint8 |
  | has_time_limit | uint8 |
  | task_time_limit | uint32 |
  | time_limit | uint32 |

## 命令 13003

- `SC_13003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |
  | star | uint8 |
  | min_round | uint8 |
  | max_round | uint8 |
  | time | uint16 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13004

- `CS_13004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | count | uint16 |

## 命令 13005

- `CS_13005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | flag | uint8 |

- `SC_13005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | flag | uint8 |
  | left_times | uint32 |

## 命令 13007

- `SC_13007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | left_time | uint32 |

## 命令 13008

- `CS_13008` — 无字段（空消息）
- `SC_13008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_bid | uint32 |

## 命令 13010

- `CS_13010` — 无字段（空消息）
- `SC_13010`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bids | table(bid:uint32, star:uint8) |

## 命令 13011

- `CSChapterStar_13011` — 无字段（空消息）
- `SCChapterStar_13011`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_star | table(chapter_id:uint32, flag:uint8, star:uint8) |

## 命令 13012

- `CS_13012`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_id | uint32 |
  | flag | uint8 |
  | star | uint32 |

- `SC_13012`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13013

- `SC_13013`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_bid | uint32 |
  | flag | uint8 |
  | star | uint8 |

## 命令 13015

- `CS_13015` — 无字段（空消息）
- `SC_13015`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chapter_reward | table(chapter_id:uint32, flag:uint8, star:uint8) |

## 命令 13016

- `SC_13016`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | flag | uint8 |
  | min_round | uint8 |
  | max_round | uint8 |

## 命令 13017

- `CS_13017` — 无字段（空消息）
- `SC_13017`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | role_out | table(r_id:uint32, out_hero:uint32) |
  | hero_out | table(hero_bid:uint32, out_hero:uint32) |
  | mon_out | table(mon_bid:uint32, out_mon:uint32) |

## 命令 13018

- `CS_13018`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | pos | uint8 |

- `SC_13018`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | pos | uint8 |
  | count | uint8 |
  | items | table(item_bid:uint32, num:uint32, is_bind:uint8) |
  | all | uint8 |
  | items_other | table(pos:uint8, item_bid:uint32, num:uint32, is_bind:uint8) |

## 命令 13019

- `SC_13019`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint8 |
  | member_id | uint32 |
  | member_srv_id | string |
  | member_name | string |
  | items | table(item_bid:uint32, num:uint32, is_bind:uint8) |
  | all | uint8 |
  | items_other | table(pos:uint8, item_bid:uint32, num:uint32, is_bind:uint8) |

## 命令 13020

- `CS_13020`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | args | table(key:uint8, value:uint8) |

- `SC_13020`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13021

- `CS_13021`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | arg | uint8 |

- `SC_13021`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | int8 |
  | msg | string |

## 命令 13022

- `CS_13022` — 无字段（空消息）
- `SC_13022`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | section | uint8 |
  | challenge | uint8 |
  | hard | uint8 |
  | assets | table(assets_code:uint8, num:uint32) |

## 命令 13023

- `SC_13023`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |
  | vip_gain | table(type:uint8, count:uint32) |

## 命令 13024

- `SC_13024`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | level | uint8 |
  | pk_id | uint32 |
  | pk_srv_id | string |
  | mon_bid | uint32 |
  | pk_name | string |
  | pk_lev | uint8 |
  | pk_career | uint8 |
  | pk_sex | uint8 |
  | pk_power | uint8 |
  | pk_status | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |
  | hard | uint8 |

## 命令 13025

- `SC_13025`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | Count | uint8 |

## 命令 13026

- `CS_13026`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | select | uint8 |

- `SC_13026`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13027

- `SC_13027`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | arg | uint16 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13028

- `CS_13028` — 无字段（空消息）
- `SC_13028`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |
  | dung_list | table(bid:uint32) |

## 命令 13029

- `SC_13029`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | round | uint16 |
  | star | uint16 |
  | score | uint16 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |
  | effect_type_per | table(effect_type:uint8, effect_type_per:uint16) |

## 命令 13030

- `SC_13030`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | int16 |
  | time | uint16 |

## 命令 13031

- `SC_13031`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | round_num | uint8 |
  | cur_hp | uint32 |

## 命令 13032

- `SC_13032`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | floor | uint8 |
  | BossList | table(boss_bid:uint32, kill_num:uint8, max_num:uint8) |

## 命令 13033

- `SC_13033`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | round | int16 |
  | time | uint16 |
  | rank | uint8 |
  | output | uint32 |

## 命令 13034

- `CS_13034`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |

- `SC_13034`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | CengList | table(ceng:uint8, count:uint16, can_get:uint8, is_get:uint8) |

## 命令 13035

- `CS_13035`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | ceng | uint8 |

- `SC_13035`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_list | table(ceng:uint8, index:uint8, round:uint8, time:uint8, member_list:D|Dsc13035member_list|) |

## 命令 13036

- `CS_13036`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | key | uint8 |
  | value | uint8 |

- `SC_13036`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | key | uint8 |
  | value | uint8 |

## 命令 13037

- `CS_13037`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | ceng | uint8 |

- `SC_13037`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | ceng | uint8 |
  | tips | uint8 |
  | msg | string |

## 命令 13038

- `CS_13038`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | ceng | uint8 |

- `SC_13038`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_str | string |

## 命令 13039

- `SC_13039`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |

## 命令 13040

- `SC_13040`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | MonList | table(mon_bid:uint32, status:uint8) |

## 命令 13041

- `SC_13041`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

## 命令 13042

- `CS_13042` — 无字段（空消息）
- `SC_13042`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | high_floor | uint32 |
  | ceng_list | table(ceng:uint8) |
  | status | uint8 |
  | cur_ceng | uint8 |
  | left_time | uint32 |
  | clear_list | table(clear_ceng:uint8) |
  | count | uint8 |

## 命令 13043

- `CS_13043` — 无字段（空消息）
- `SC_13043`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | count | uint8 |

## 命令 13044

- `CS_13044`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |

- `SC_13044`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13045

- `CS_13045`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint32 |

- `SC_13045`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint32 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | fast_rid | uint32 |
  | fast_srv_id | string |
  | fast_name | string |
  | first_get | uint8 |

## 命令 13046

- `SC_13046`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | floor | uint8 |
  | BossList | table(boss_bid:uint32, kill_num:uint8, max_num:uint8) |

## 命令 13047

- `SC_13047`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | left_time | uint32 |

## 命令 13048

- `SC_13048`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13049

- `SC_13049`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |
  | first_items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13050

- `CS_13050` — 无字段（空消息）
## 命令 13051

- `CS_13051` — 无字段（空消息）
- `SC_13051`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13052

- `CS_13052` — 无字段（空消息）
- `SC_13052`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | select_hard | uint8 |
  | section | uint8 |
  | hard | uint8 |
  | challenge | uint8 |
  | left_times | uint8 |
  | assets | table(assets_code:uint8, num:uint32) |

## 命令 13053

- `SC_13053`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | FloorAwardList | table(floor:uint8, gain:D|Dsc13053gain|, items:D|Dsc13053items|) |

## 命令 13054

- `SC_13054`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | star | uint32 |
  | EffectList | table(EffectId:uint32) |
  | effect_type_per | table(effect_type:uint8, effect_type_per:uint16) |

## 命令 13055

- `CS_13055`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | EffectId | uint32 |

- `SC_13055`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | star | uint32 |
  | effect_type_per | table(effect_type:uint8, effect_type_per:uint16) |

## 命令 13056

- `SC_13056`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | score | uint32 |
  | max_wave | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13057

- `CS_13057`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13057`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13058

- `CS_13058`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13058`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cur_score | uint32 |
  | get_score | uint32 |
  | max_wave | uint8 |
  | gain | table(type:uint8, count:uint32) |
  | AwardBidList | table(Bid:uint32) |

## 命令 13059

- `SC_13059`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | round | uint32 |
  | star | uint32 |
  | hard_boss | table(hard:uint8, boss_bid:uint32) |

## 命令 13060

- `CS_13060`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | round | uint32 |
  | hard | uint8 |

- `SC_13060`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | round | uint32 |

## 命令 13061

- `CS_13061` — 无字段（空消息）
- `SC_13061`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | wave | uint16 |

## 命令 13062

- `CS_13062`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ceng | uint8 |

- `SC_13062`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | ceng | uint8 |

## 命令 13065

- `SC_13065`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |
  | question_id | uint32 |

## 命令 13066

- `CS_13066`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |
  | question_id | uint32 |
  | answer_id | uint32 |

- `SC_13066`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |
  | answer_id | uint32 |

## 命令 13067

- `SC_13067`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 13068

- `SC_13068`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | npc_status | table(npc_bid:uint32, status:uint8) |
  | mons | table(boss_bid:uint32, num:uint8) |

## 命令 13069

- `SC_13069`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | cur_round | uint8 |
  | vese_id | uint32 |
  | verse_status | table(index:uint32, status:uint8) |

## 命令 13070

- `SC_13070`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | npc_bid | uint32 |

## 命令 13071

- `SC_13071`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | box_num | uint8 |
  | open_box_num | uint8 |
  | boss_bid | uint32 |
  | num | uint8 |

## 命令 13072

- `SC_13072`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | mon_status | table(mon_bid:uint32, mon_status:uint8) |
  | boss_bid | uint32 |
  | num | uint8 |

## 命令 13073

- `CS_13073` — 无字段（空消息）
- `SC_13073`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor_count | table(floor:uint8, left_count:uint8) |

## 命令 13074

- `CS_13074` — 无字段（空消息）
- `SC_13074`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13075

- `CS_13075`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13075`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13076

- `CS_13076` — 无字段（空消息）
- `SC_13076`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, face_id:uint32, msg:string) |

## 命令 13079

- `CS_13079`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13079`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | enter_count | uint16 |
  | buy_count | uint16 |

## 命令 13080

- `CS_13080` — 无字段（空消息）
- `SC_13080`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(bid:uint32, enter_count:uint16, buy_count:uint16, time:uint32, is_finish:uint8) |

## 命令 13081

- `SC_13081`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 13082

- `CS_13082`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13082`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | time | uint16 |

## 命令 13083

- `CS_13083`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_13083`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13084

- `CS_13084` — 无字段（空消息）
- `SC_13084`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | max_wave | uint16 |
  | rank | uint16 |
  | partner_list | table(partner_bid:uint32, attr_id:uint16, attr_val:int16) |
  | goods_index | uint16 |
  | goods_flag | uint8 |
  | max_passed | uint16 |

## 命令 13085

- `CS_13085`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | start_rank | uint16 |
  | end_rank | uint16 |

- `SC_13085`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | rank_list | table(rank:uint16, rid:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, carrer:uint8, wave:uint16) |

## 命令 13086

- `CS_13086`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_list | table(partner_id:uint32) |
  | rid | uint32 |
  | srv_id | string |
  | partner_id | uint32 |

- `SC_13086`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13087

- `CS_13087` — 无字段（空消息）
- `SC_13087`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | wave | uint16 |
  | rank | uint16 |
  | per_name | string |
  | per_wave | uint16 |
  | assets | table(assets_code:uint8, val:uint32) |

## 命令 13088

- `CS_13088` — 无字段（空消息）
- `SC_13088`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | wave | uint16 |
  | rank | uint16 |
  | add_rank | int16 |
  | assets | table(assets_code:uint8, val:uint32) |
  | rank_list | table(rank:uint16, rid:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, carrer:uint8, wave:uint16) |

## 命令 13094

- `SC_13094`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | floor | uint8 |
  | BossList | table(boss_bid:uint32, kill_num:uint8, max_num:uint8) |

## 命令 13095

- `SC_13095`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | round | int16 |
  | time | uint16 |
  | rank | uint8 |
  | output | uint32 |

## 命令 13096

- `CS_13096`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | ceng | uint8 |

- `SC_13096`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_list | table(ceng:uint8, index:uint8, round:uint8, time:uint8, member_list:D|Dsc13096member_list|) |

## 命令 13097

- `CS_13097`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |

- `SC_13097`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | CengList | table(ceng:uint8, count:uint16, can_get:uint8, is_get:uint8) |

## 命令 13098

- `CS_13098`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | ceng | uint8 |

- `SC_13098`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Bid | uint32 |
  | ceng | uint8 |
  | tips | uint8 |
  | msg | string |

## 命令 13099

- `SC_13099`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | floor | uint8 |
  | time_out | uint32 |
  | ElemList | table(elem_bid:uint32, elem_status:uint8) |
  | MonList | table(mon_bid:uint32, mon_kill_num:uint8, mon_max_num:uint8) |
  | BossList | table(boss_bid:uint32, kill_num:uint8, max_num:uint8) |

## 命令 13100

- `CS_13100` — 无字段（空消息）
- `SC_13100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | f_lev | uint8 |
  | hero_list | table(hero_bid:uint32, status:uint8) |
  | f_info | table(type:uint8, is_select:uint8, hero_pos_info:D|Dsc13100hero_pos_info|) |

## 命令 13101

- `CS_13101`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |

- `SC_13101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | pos_info | table(type:uint8, hero_pos_info:D|Dsc13101hero_pos_info|) |

## 命令 13102

- `CS_13102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |

- `SC_13102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | pos_info | table(type:uint8, hero_pos_info:D|Dsc13102hero_pos_info|) |

## 命令 13103

- `CS_13103` — 无字段（空消息）
- `SC_13103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | f_lev | uint8 |
  | f_info | table(type:uint8, is_select:uint8, hero_pos_info:D|Dsc13103hero_pos_info|) |

## 命令 13104

- `CS_13104`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13104`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | s_type | uint8 |

## 命令 13105

- `CS_13105` — 无字段（空消息）
- `SC_13105`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | experience | uint32 |

## 命令 13200

- `CS_13200` — 无字段（空消息）
- `SC_13200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |
  | team_id | uint32 |
  | team_srv_id | string |
  | leader_id | uint32 |
  | leader_srv_id | string |
  | leader_speed | uint32 |
  | team_member_list | table(member_id:uint32, member_srv_id:string, member_name:string, member_lev:uint8, member_career:uint16, member_sex:uint8, member_face_id:uint32, member_mode:uint8, member_hp:uint32, member_hp_max:uint32, power:uint32) |

## 命令 13201

- `CS_13201` — 无字段（空消息）
- `SC_13201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13202

- `CS_13202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 13203

- `SC_13203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | leader_id | uint32 |
  | leader_srv_id | string |
  | leader_name | string |
  | leader_lev | uint8 |
  | leader_career | uint8 |
  | team_id | uint32 |
  | team_srv_id | string |
  | team_num | uint8 |
  | team_max_num | uint8 |
  | invite_flag | uint8 |

## 命令 13204

- `CS_13204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_ok | uint8 |
  | ok_id | uint32 |
  | ok_srv_id | string |

- `SC_13204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | id | uint32 |
  | srv_id | string |

## 命令 13205

- `CS_13205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_ok | uint8 |
  | team_id | uint32 |
  | team_srv_id | string |
  | invite_flag | uint8 |
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | team_id | uint32 |
  | team_srv_id | string |

## 命令 13206

- `CS_13206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |

- `SC_13206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13207

- `CS_13207` — 无字段（空消息）
- `SC_13207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | apply_list | table(apply_id:uint32, apply_srv_id:string, apply_name:string, apply_lev:uint8, apply_career:uint16, apply_power:uint32) |

## 命令 13208

- `SC_13208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | apply_id | uint32 |
  | apply_srv_id | string |
  | apply_name | string |
  | apply_lev | uint8 |
  | apply_career | uint16 |
  | apply_power | uint32 |

## 命令 13209

- `CS_13209`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13210

- `CS_13210` — 无字段（空消息）
- `SC_13210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13211

- `CS_13211`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13212

- `SC_13212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |
  | msg | string |

## 命令 13213

- `CS_13213` — 无字段（空消息）
- `SC_13213`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13214

- `CS_13214`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13214`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13215

- `SC_13215`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | leader_id | uint32 |
  | leader_srv_id | string |
  | leader_name | string |
  | map_bid | uint32 |
  | map_x | uint16 |
  | map_y | uint16 |

## 命令 13216

- `CS_13216`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |
  | flag | uint8 |
  | send_flag | uint8 |

- `SC_13216`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13217

- `CS_13217`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | member_id | uint32 |
  | member_srv_id | string |

- `SC_13217`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13218

- `CS_13218` — 无字段（空消息）
- `SC_13218`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_list | table(team_id:uint32, team_srv_id:string, leader_id:uint32, leader_srv_id:string, leader_name:string, leader_lev:uint8, leader_career:uint16, leader_sex:uint16, team_member_num:uint8, team_member_max_num:uint8) |

## 命令 13219

- `CS_13219`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_13219`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | flag | uint8 |
  | role_list | table(role_id:uint32, role_srv_id:string, role_name:string, role_lev:uint8, role_career:uint16, role_power:uint32, role_sex:uint32) |

## 命令 13220

- `CS_13220`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | role_list | table(role_id:uint32, role_srv_id:string) |

- `SC_13220`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13221

- `SC_13221`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | role_srv_id | string |
  | role_name | string |

## 命令 13223

- `CS_13223`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | purpose | uint8 |
  | arg | uint32 |
  | min_lev | uint8 |
  | max_lev | uint8 |
  | leader_new | uint8 |

- `SC_13223`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | purpose | uint8 |
  | arg | uint32 |
  | min_lev | uint8 |
  | max_lev | uint8 |
  | leader_new | uint8 |

## 命令 13224

- `CS_13224`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | p_list | table(purpose:uint8, arg:uint32) |
  | min_lev | uint8 |
  | max_lev | uint8 |
  | team_id | uint32 |
  | team_srv_id | string |

- `SC_13224`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13225

- `CS_13225` — 无字段（空消息）
- `SC_13225`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13226

- `CS_13226` — 无字段（空消息）
- `SC_13226`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13227

- `CS_13227`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | p_list | table(purpose:uint8, arg:uint32) |

- `SC_13227`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_num | uint16 |
  | role_num | uint16 |

## 命令 13228

- `CS_13228` — 无字段（空消息）
- `SC_13228`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13229

- `CS_13229`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | arg_list | table(arg:uint32) |

- `SC_13229`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13230

- `SC_13230`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | time | uint8 |
  | count | uint8 |
  | arg_list | table(arg:uint32) |

## 命令 13231

- `CS_13231`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | arg_list | table(arg:uint32) |

- `SC_13231`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13232

- `SC_13232`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |
  | flag | uint8 |
  | type | uint8 |
  | arg_list | table(arg:uint32) |

## 命令 13233

- `SC_13233`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | purpose | uint8 |
  | arg | uint32 |

## 命令 13234

- `CS_13234`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | purpose | uint8 |
  | arg | uint32 |

- `SC_13234`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | member_list | table(role_id:uint32, role_srv_id:string, role_name:string, role_lev:uint8, role_career:uint16, role_sex:uint16) |

## 命令 13235

- `CS_13235`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | key | uint8 |
  | value | uint8 |

- `SC_13235`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | key | uint8 |
  | value | uint8 |

## 命令 13236

- `SC_13236`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | purpose | uint8 |
  | arg | uint32 |

## 命令 13237

- `CS_13237`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13237`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |
  | num | uint8 |
  | gid | uint32 |
  | gsrv | string |
  | gname | string |

## 命令 13238

- `CS_13238`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint16 |
  | purpose | uint8 |
  | arg | uint32 |
  | min_lev | uint8 |
  | max_lev | uint8 |
  | leader_new | uint8 |

- `SC_13238`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | time | uint32 |

## 命令 13250

- `CS_13250` — 无字段（空消息）
- `SC_13250`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | select_type | uint8 |
  | info_list | table(type:uint8, f_lev:uint32, hero_pos_info:D|Dsc13250hero_pos_info|, member_pos_info:D|Dsc13250member_pos_info|) |

## 命令 13251

- `CS_13251`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_13251`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | pos_info | table(type:uint8, f_lev:uint32, hero_pos_info:D|Dsc13251hero_pos_info|, member_pos_info:D|Dsc13251member_pos_info|) |

## 命令 13253

- `CS_13253`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13253`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | s_type | uint8 |

## 命令 13254

- `CS_13254` — 无字段（空消息）
- `SC_13254`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | f_info | table(type:uint8, f_lev:uint32, hero_pos_info:D|Dsc13254hero_pos_info|, member_pos_info:D|Dsc13254member_pos_info|) |

## 命令 13256

- `CS_13256` — 无字段（空消息）
- `SC_13256`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13257

- `SC_13257`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | name | string |

## 命令 13258

- `CS_13258`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13258`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 13300

- `CS_13300` — 无字段（空消息）
- `SC_13300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | friend_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, login_time:uint32, face_id:uint8, is_online:uint8, group_id:uint32, intimacy:uint32, grid:uint32, gsrv_id:string, guild_name:string) |

## 命令 13301

- `CS_13301` — 无字段（空消息）
- `SC_13301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

## 命令 13302

- `CS_13302` — 无字段（空消息）
- `SC_13302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

## 命令 13303

- `CS_13303`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13304

- `CS_13304` — 无字段（空消息）
- `SC_13304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | sex | uint8 |
  | lev | uint8 |

## 命令 13305

- `CS_13305`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | agreed | uint8 |

- `SC_13305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13306

- `CS_13306`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string) |

- `SC_13306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13307

- `CS_13307`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13308

- `CS_13308` — 无字段（空消息）
- `SC_13308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

## 命令 13309

- `CS_13309`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | del_list | table(rid:uint32, srv_id:string) |

- `SC_13309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | del_list2 | table(rid:uint32, srv_id:string) |

## 命令 13310

- `CS_13310`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | string | string |

## 命令 13311

- `CS_13311` — 无字段（空消息）
- `SC_13311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | all_give_times | uint8 |
  | all_award_times | uint8 |
  | give_times | uint8 |
  | award_times | uint8 |
  | give_list | table(rid:uint32, srv_id:string, status:uint8, value:uint32) |
  | be_give_list | table(rid:uint32, srv_id:string, status:uint8, value:uint32) |

## 命令 13312

- `CS_13312` — 无字段（空消息）
- `SC_13312`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | spirit | uint8 |

## 命令 13313

- `CS_13313`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13313`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | string | string |

## 命令 13314

- `CS_13314`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |

- `SC_13314`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, status:uint8) |

## 命令 13315

- `CS_13315`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | send_list | table(id:uint32, bid:uint32, num:uint32) |

- `SC_13315`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13316

- `CS_13316` — 无字段（空消息）
- `SC_13316`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | group_list | table(group_id:uint32, group_name:string) |

## 命令 13317

- `CS_13317`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | group_name | string |

- `SC_13317`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13318

- `CS_13318`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | group_id | uint32 |

- `SC_13318`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13319

- `CS_13319`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | old_group_id | uint32 |
  | new_group_id | uint32 |

- `SC_13319`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13320

- `CS_13320` — 无字段（空消息）
- `SC_13320`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | recommend_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, is_online:uint8, career:uint16) |

## 命令 13321

- `CS_13321` — 无字段（空消息）
- `SC_13321`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | request_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, login_time:uint32, face_id:uint8, is_online:uint8, group_id:uint32, intimacy:uint32, grid:uint32, gsrv_id:string, guild_name:string) |

## 命令 13322

- `CS_13322` — 无字段（空消息）
- `SC_13322`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | add_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, login_time:uint32, face_id:uint8, is_online:uint8, group_id:uint32, intimacy:uint32, grid:uint32, gsrv_id:string, guild_name:string) |

## 命令 13323

- `CS_13323` — 无字段（空消息）
- `SC_13323`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |

## 命令 13324

- `CS_13324`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | bid | uint32 |
  | num | uint32 |
  | auto_buy | uint8 |
  | msg | string |

- `SC_13324`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | string | string |
  | bid | uint32 |
  | num | uint32 |

## 命令 13325

- `CS_13325`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13325`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | give_times | uint32 |
  | all_times | uint32 |

## 命令 13326

- `CS_13326`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13326`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | career | uint16 |
  | is_online | uint8 |
  | courage | uint32 |
  | charm | uint32 |
  | send_num | uint32 |
  | send_list | table(rid:uint32, srv_id:string, name:string, career:uint16, b_rid:uint32, b_srv_id:string, b_name:string, b_career:uint16, item_bid:uint32) |

## 命令 13328

- `CS_13328` — 无字段（空消息）
- `SC_13328`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | career | uint16 |
  | b_rid | uint32 |
  | b_srv_id | string |
  | b_name | string |
  | b_career | uint16 |
  | item_bid | uint32 |

## 命令 13331

- `CS_13331` — 无字段（空消息）
- `SC_13331`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | courage | uint32 |
  | charm | uint32 |
  | courage_rank | uint8 |
  | charm_rank | uint8 |

## 命令 13336

- `CS_13336` — 无字段（空消息）
- `SC_13336`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | intimacy | uint32 |

## 命令 13340

- `CS_13340` — 无字段（空消息）
- `SC_13340`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |
  | lev | uint8 |
  | career | uint8 |
  | sex | uint8 |
  | sign | string |
  | guild_name | string |
  | title | string |
  | spouse_name | string |
  | per_name | string |
  | zone | string |
  | city | string |
  | gift_num | uint16 |
  | nice_num | uint32 |
  | flower | uint32 |
  | new_msg | uint8 |
  | zone_skin | uint16 |
  | head_skin | uint16 |
  | use_badge_list | table(badge:uint32) |

## 命令 13341

- `CS_13341`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | max_len | uint8 |

- `SC_13341`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | max_len | uint8 |
  | msg_list | table(index:uint32, rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, content:string, ctime:uint32, nice_num:uint32, nice_list:D|Dsc13341nice_list|, comment_num:uint8, comment_list:D|Dsc13341comment_list|, head_bid:uint32) |

## 命令 13342

- `CS_13342`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | ord | uint8 |
  | max_len | uint8 |

- `SC_13342`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | ord | uint8 |
  | max_len | uint8 |
  | msg_list | table(index:uint32, rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, content:string, ctime:uint32, nice_num:uint32, nice_list:D|Dsc13342nice_list|, comment_num:uint8, comment_list:D|Dsc13342comment_list|, head_bid:uint32) |

## 命令 13343

- `CS_13343`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | content | string |
  | friend_list | table(rid:uint32, srv_id:string) |

- `SC_13343`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13344

- `CS_13344`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | type | uint8 |
  | to_rid | uint32 |
  | to_srv_id | string |
  | to_name | string |
  | comment | string |

- `SC_13344`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | comment_num | uint8 |
  | comment_list | table(ctime:uint32, rid:uint32, srv_id:string, name:string, type:uint8, to_rid:uint32, to_srv_id:string, to_name:string, comment:string) |

## 命令 13345

- `CS_13345`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint32 |
  | srv_id | string |

- `SC_13345`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |

## 命令 13346

- `CS_13346`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | say_rid | uint32 |
  | say_srv_id | string |
  | say_ctime | uint32 |

- `SC_13346`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | say_rid | uint32 |
  | say_srv_id | string |
  | say_ctime | uint32 |

## 命令 13347

- `CS_13347`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |

- `SC_13347`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | nice_num | uint8 |
  | nice_list | table(rid:uint32, srv_id:string, role_name:string) |

## 命令 13348

- `CS_13348`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |

- `SC_13348`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | nice_num | uint8 |
  | nice_list | table(rid:uint32, srv_id:string, role_name:string) |

## 命令 13349

- `CS_13349`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13349`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | name | string |
  | lev | uint8 |
  | career | uint8 |
  | sex | uint8 |
  | sign | string |
  | guild_name | string |
  | title | string |
  | spouse_name | string |
  | per_name | string |
  | zone | string |
  | city | string |
  | gift_num | uint16 |
  | nice_num | uint32 |
  | flower | uint32 |
  | is_nice | uint8 |
  | zone_skin | uint16 |
  | head_skin | uint16 |
  | use_badge_list | table(badge:uint32) |

## 命令 13350

- `CS_13350`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13350`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | nice_num | uint32 |
  | gift_num | uint16 |

## 命令 13351

- `CS_13351`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint16 |

- `SC_13351`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | gift_num | uint16 |

## 命令 13352

- `CS_13352` — 无字段（空消息）
- `SC_13352`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, lev:uint8, ctime:uint32, gift_num:uint16) |

## 命令 13353

- `CS_13353` — 无字段（空消息）
- `SC_13353`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, bid:uint32, ctime:uint32, msg:string) |

## 命令 13354

- `CS_13354`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | ord | uint8 |
  | max_len | uint8 |

- `SC_13354`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | ord | uint8 |
  | max_len | uint8 |
  | role_list | table(rank:uint8, rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, nice_num:uint32, gift_num:uint8, face_id:uint32, head_bid:uint32) |

## 命令 13355

- `CS_13355` — 无字段（空消息）
- `SC_13355`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | msg_list | table(type:uint8, rid:uint32, srv_id:string, index:uint32, content:string, msg_rid:uint32, msg_srv_id:string, name:string, career:uint8, sex:uint8, msg:string, ctime:uint32, head_bid:uint32) |

## 命令 13356

- `CS_13356`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | index | uint32 |
  | msg_rid | uint32 |
  | msg_srv_id | string |
  | ctime | uint32 |

- `SC_13356`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | msg_list | table(index:uint32, rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, content:string, ctime:uint32, nice_num:uint32, nice_list:D|Dsc13356nice_list|, comment_num:uint8, comment_list:D|Dsc13356comment_list|, head_bid:uint32) |

## 命令 13357

- `CS_13357` — 无字段（空消息）
- `SC_13357`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13358

- `CS_13358`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | partner_id | uint32 |

- `SC_13358`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13359

- `CS_13359`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | content | string |

- `SC_13359`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | content | string |

## 命令 13360

- `CS_13360`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | town | string |
  | city | string |

- `SC_13360`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | town | string |
  | city | string |

## 命令 13361

- `CS_13361` — 无字段（空消息）
- `SC_13361`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | zone_list | table(bid:uint16) |
  | head_list | table(bid:uint16) |

## 命令 13362

- `CS_13362`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `SC_13362`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint16 |

## 命令 13363

- `CS_13363`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | bid | uint16 |

- `SC_13363`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | bid | uint16 |

## 命令 13364

- `CS_13364` — 无字段（空消息）
- `SC_13364`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | use_badge_list | table(badge:uint32) |

## 命令 13365

- `CS_13365` — 无字段（空消息）
- `SC_13365`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | act_badge_list | table(badge:uint32) |

## 命令 13366

- `CS_13366`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid_list | table(bid:uint16) |

- `SC_13366`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid_list | table(bid:uint16) |

## 命令 13367

- `CS_13367`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | index | uint32 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | reason | string |
  | desc | string |
  | content | string |

- `SC_13367`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 13368

- `CS_13368`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | len | uint8 |
  | msg | string |

- `SC_13368`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13369

- `CS_13369` — 无字段（空消息）
- `SC_13369`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | black_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, login_time:uint32, face_id:uint8, is_online:uint8, group_id:uint32, intimacy:uint32, grid:uint32, gsrv_id:string, guild_name:string) |

## 命令 13370

- `CS_13370`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | op_type | uint8 |

- `SC_13370`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint32 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | op_type | uint8 |

## 命令 13371

- `CS_13371` — 无字段（空消息）
- `SC_13371`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | add_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, lev:uint16, career:uint16, power:uint32, login_time:uint32, face_id:uint8, is_online:uint8, group_id:uint32, intimacy:uint32, grid:uint32, gsrv_id:string, guild_name:string) |

## 命令 13401

- `CS_13401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | buy_list | table(id:uint16, buy_num:uint16) |

## 命令 13402

- `CS_13402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | num | uint16 |

- `SC_13402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | type | uint8 |
  | buy_num | uint16 |
  | new_price | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 13403

- `CS_13403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | item_list | table(item_bid:uint32, price:uint32) |

## 命令 13410

- `CS_13410` — 无字段（空消息）
- `SC_13410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | is_sign | uint8 |
  | record | table(rid:uint32, srv_id:string, name:string, money:uint16, item_bid:uint32, item_num:uint8) |

## 命令 13411

- `CS_13411` — 无字段（空消息）
- `SC_13411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record | table(item_bid:uint32, item_num:uint8, money:uint16, state:uint8) |

## 命令 13415

- `CS_13415`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | real_name | string |
  | tel | string |
  | qq | string |
  | address | string |

- `SC_13415`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13416

- `CS_13416` — 无字段（空消息）
- `SC_13416`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | real_name | string |
  | tel | string |
  | qq | string |
  | address | string |

## 命令 13500

- `CS_13500`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_name | string |

- `SC_13500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13501

- `CS_13501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | args | table(key:uint8, val:string) |
  | flag | uint8 |
  | num | uint8 |

- `SC_13501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | page_total | uint8 |
  | guilds | table(index:uint8, gid:uint32, srv_id:string, realm:uint8, vip:uint8, guild_name:string, head_name:string, head_career:uint8, lev:uint8, role_count:uint16, max_role_count:uint16, applyed:uint8, power:uint32, all_assets:uint32, is_recommend:uint8, head_sex:uint8, is_invited:uint8) |
  | all_count | uint32 |

## 命令 13502

- `CS_13502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | srv_id | string |

- `SC_13502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | gid | uint32 |
  | srv_id | string |
  | realm | uint8 |
  | vip | uint8 |
  | guild_name | string |
  | head_name | string |
  | head_career | uint8 |
  | lev | uint8 |
  | role_count | uint16 |
  | max_role_count | uint16 |
  | applyed | uint8 |
  | power | uint32 |
  | assets | uint32 |
  | is_recommend | uint8 |
  | head_sex | uint8 |
  | is_invited | uint8 |

## 命令 13503

- `CS_13503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | srv_id | string |

- `SC_13503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13504

- `CS_13504` — 无字段（空消息）
- `SC_13504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | all_request | uint8 |

## 命令 13505

- `CS_13505`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |

- `SC_13505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13506

- `CS_13506` — 无字段（空消息）
- `SC_13506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

## 命令 13507

- `CS_13507`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint32 |
  | num | uint8 |

- `SC_13507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | page_total | uint8 |
  | guids | table(rid:uint32, srv_id:string, name:string, lev:uint8, career:uint8, sex:uint8, power:uint32, apply_time:uint32, is_vip:uint8, vip_lev:uint8) |

## 命令 13508

- `CS_13508`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | role_name | string |

- `SC_13508`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13509

- `CS_13509` — 无字段（空消息）
- `SC_13509` — 无字段（空消息）
## 命令 13510

- `CS_13510`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | gid | uint32 |
  | gsrv_id | string |

- `SC_13510`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | gid | uint32 |
  | gsrv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13511

- `CS_13511` — 无字段（空消息）
- `SC_13511`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | gname | string |
  | rname | string |

## 命令 13512

- `CS_13512` — 无字段（空消息）
- `SC_13512` — 无字段（空消息）
## 命令 13513

- `CS_13513`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |

- `SC_13513`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13514

- `CS_13514` — 无字段（空消息）
- `SC_13514`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13515

- `CS_13515`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | modify | table(key:uint8, value:string) |

- `SC_13515`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13516

- `CS_13516` — 无字段（空消息）
- `SC_13516`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13517

- `CS_13517`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |

- `SC_13517`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13518

- `CS_13518` — 无字段（空消息）
- `SC_13518`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_name | string |
  | lev | uint8 |
  | role_count | uint16 |
  | max_role_count | uint16 |
  | stu_count | uint16 |
  | max_stu_count | uint16 |
  | aim | string |
  | sign | string |
  | qq | string |
  | yy | string |
  | head_name | string |
  | maintain | uint32 |
  | all_assets | uint32 |
  | max_assets | uint32 |
  | member_lev | uint16 |
  | health | uint32 |
  | week_wage | uint32 |
  | max_week_wage | uint32 |
  | all_request | uint8 |

## 命令 13519

- `CS_13519`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |

- `SC_13519`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guid_roles | table(rid:uint32, srv_id:string, sex:uint8, name:string, position:uint8, lev:uint8, career:uint8, lave_contrib:uint32, all_contrib:uint32, power:uint32, logout_time:uint32, is_online:uint8, is_vip:uint8, vip_lev:uint8, face_id:uint16, hongbao:D|Dsc13519hongbao|, help:D|Dsc13519help|) |

## 命令 13520

- `CS_13520`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | position | uint8 |
  | old_position | uint8 |

- `SC_13520`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | position | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 13521

- `CS_13521` — 无字段（空消息）
- `SC_13521`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | position1 | uint8 |
  | now_position1 | uint8 |
  | position2 | uint8 |
  | now_position2 | uint8 |
  | position3 | uint8 |
  | now_position3 | uint8 |
  | position4 | uint8 |
  | now_position4 | uint8 |
  | position5 | uint8 |
  | now_position5 | uint8 |
  | position6 | uint8 |
  | now_position6 | uint8 |

## 命令 13522

- `CS_13522`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |

- `SC_13522`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 13523

- `CS_13523`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | build_lev | uint32 |

- `SC_13523`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | new_build_lev | uint32 |
  | up_status | uint32 |
  | up_time | uint32 |
  | speed_time | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 13524

- `CS_13524`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |

- `SC_13524`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guilds | table(build_id:uint32, build_lev:uint32, up_status:uint32, up_time:uint32, speed_time:uint32) |

## 命令 13525

- `CS_13525`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | good_bid | uint32 |
  | good_num | string |

- `SC_13525`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | good_bid | uint32 |
  | buy_num | string |
  | all_num | string |
  | code | uint8 |
  | msg | string |

## 命令 13526

- `CS_13526` — 无字段（空消息）
- `SC_13526`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_shop | table(good_bid:uint32, buy_num:string, all_num:string) |

## 命令 13527

- `CS_13527`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint32 |

- `SC_13527`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13528

- `CS_13528` — 无字段（空消息）
- `SC_13528`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13529

- `CS_13529` — 无字段（空消息）
- `SC_13529`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |

## 命令 13530

- `CS_13530` — 无字段（空消息）
- `SC_13530`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_shop | table(good_bid:uint32, num:string) |

## 命令 13531

- `CS_13531`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | srv_id | string |
  | good_bid | uint32 |
  | num | string |

- `SC_13531`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | good_bid | uint32 |
  | num | string |
  | code | uint8 |
  | msg | string |

## 命令 13532

- `CS_13532`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | old_position | uint8 |

- `SC_13532`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13533

- `CS_13533`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | build_lev | uint32 |

- `SC_13533`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | build_lev | uint32 |
  | up_status | uint32 |
  | up_time | uint32 |
  | speed_time | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 13534

- `CS_13534`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | speed_id | uint32 |

- `SC_13534`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | build_id | uint32 |
  | speed_time | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 13535

- `CS_13535`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mem_lev | uint32 |

- `SC_13535`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mem_lev | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 13536

- `CS_13536`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13536`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13537

- `CS_13537`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13537`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13538

- `CS_13538` — 无字段（空消息）
- `SC_13538`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_assets | table(id:uint32, value:uint32) |

## 命令 13539

- `CS_13539`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_name | string |

- `SC_13539`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guilds | table(index:uint8, gid:uint32, srv_id:string, realm:uint8, vip:uint8, guild_name:string, head_name:string, head_career:uint8, lev:uint8, role_count:uint16, max_role_count:uint16, applyed:uint8, power:uint32, assets:uint32, is_recommend:uint8, head_sex:uint8, is_invited:uint8) |

## 命令 13540

- `CS_13540`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_list | table(gid:uint32, gsrv_id:string) |

- `SC_13540`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_list | table(gid:uint32, gsrv_id:string) |
  | code | uint8 |
  | msg | string |

## 命令 13541

- `CS_13541` — 无字段（空消息）
- `SC_13541`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13542

- `CS_13542` — 无字段（空消息）
- `SC_13542`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | guid_roles | table(rid:uint32, srv_id:string, sex:uint8, name:string, position:uint8, lev:uint8, career:uint8, lave_contrib:uint32, all_contrib:uint32, power:uint32, logout_time:uint32, is_online:uint8, is_vip:uint8, vip_lev:uint8, face_id:uint16, hongbao:D|Dsc13542hongbao|, help:D|Dsc13542help|) |

## 命令 13543

- `CS_13543` — 无字段（空消息）
- `SC_13543`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13546

- `CS_13546` — 无字段（空消息）
- `SC_13546`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gonggao_list | table(name:string, msg:string, tick:uint32) |

## 命令 13547

- `CS_13547`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

- `SC_13547`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13548

- `CS_13548` — 无字段（空消息）
- `SC_13548` — 无字段（空消息）
## 命令 13551

- `CS_13551` — 无字段（空消息）
- `SC_13551`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gift_num | uint32 |

## 命令 13552

- `CS_13552` — 无字段（空消息）
- `SC_13552`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gift_num | uint32 |
  | id_list | table(rid:uint32, srv_id:string) |

## 命令 13553

- `CS_13553`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id_list | table(rid:uint32, srv_id:string) |

- `SC_13553`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | gift_num | uint32 |
  | id_list | table(rid:uint32, srv_id:string) |

## 命令 13556

- `CS_13556` — 无字段（空消息）
- `SC_13556`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | contrib | uint32 |
  | gift_num | uint32 |
  | week_wage | uint32 |

## 命令 13561

- `CS_13561` — 无字段（空消息）
- `SC_13561`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | sign_list | table(rid:uint32, srv_id:string, sign:string) |

## 命令 13562

- `CS_13562`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | sign | string |

- `SC_13562`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | sign | string |

## 命令 13563

- `CS_13563` — 无字段（空消息）
- `SC_13563`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | sign | string |

## 命令 13564

- `CS_13564`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |

- `SC_13564`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13565

- `SC_13565`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |
  | state | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | career | uint8 |
  | type | uint8 |
  | sex | uint8 |

## 命令 13566

- `CS_13566`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |

- `SC_13566`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | create_name | string |
  | create_career | uint8 |
  | id | uint16 |
  | type | uint8 |
  | val | uint32 |
  | hongbao_get | uint16 |
  | hongbao_max | uint16 |
  | reward_get | uint32 |
  | reward_max | uint32 |
  | stop_time | uint32 |
  | role_list | table(rid:uint32, srv_id:string, name:string, career:uint8, reward:uint32, time:uint32, create_sex:uint8) |
  | create_sex | uint8 |

## 命令 13567

- `CS_13567`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint16 |

- `SC_13567`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | val | uint32 |

## 命令 13568

- `CS_13568`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13568`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | val | uint16 |

## 命令 13569

- `CS_13569` — 无字段（空消息）
- `SC_13569`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | info | table(type:uint8, val:uint8, val_max:uint16) |

## 命令 13570

- `CS_13570`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | num | uint8 |

- `SC_13570`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | page_total | uint8 |
  | role_list | table(rid:uint32, srv_id:string, name:string, partner_id:uint32, partner_bid:uint32, partner_lev:uint32, partner_color:uint32, partner_type:uint8, times:uint8, timeout:uint32, state:uint8) |

## 命令 13571

- `CS_13571`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id | uint32 |

- `SC_13571`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13572

- `CS_13572`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | partner_id | uint32 |

- `SC_13572`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | partner_id | uint32 |

## 命令 13573

- `CS_13573`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id | uint32 |

- `SC_13573`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | partner_id | uint32 |

## 命令 13574

- `CS_13574` — 无字段（空消息）
- `SC_13574`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | role_list | table(partner_id:uint32, partner_bid:uint32, partner_lev:uint32, partner_color:uint32, partner_type:uint8, times:uint8, timeout:uint32, event_list:D|Dsc13574event_list|) |

## 命令 13575

- `CS_13575` — 无字段（空消息）
- `SC_13575`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | partner_list | table(partner_id:uint32) |

## 命令 13576

- `CS_13576` — 无字段（空消息）
- `SC_13576`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13577

- `CS_13577`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_13577`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |
  | page_total | uint8 |
  | role_list | table(rid:uint32, srv_id:string, name:string, partner_id:uint32, partner_bid:uint32, partner_lev:uint32, partner_color:uint32, partner_type:uint8, times:uint8, timeout:uint32, state:uint8) |

## 命令 13578

- `CS_13578` — 无字段（空消息）
- `SC_13578`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | act_list | table(id:uint16, times:uint16) |

## 命令 13579

- `CS_13579` — 无字段（空消息）
- `SC_13579`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tree_lev | uint8 |
  | strength_rest | uint32 |
  | strength_name | string |
  | role_eff | uint32 |
  | role_delay | uint32 |
  | role_attrs | table(code:uint8, value:int32) |
  | parter_eff | uint32 |
  | parter_delay | uint32 |
  | parter_attrs | table(code:uint8, value:int32) |

## 命令 13580

- `CS_13580` — 无字段（空消息）
- `SC_13580`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | worship_list | table(type:uint8, lev:uint16, exp:uint32, used:uint8) |

## 命令 13581

- `CS_13581`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13581`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | new_type | uint8 |

## 命令 13582

- `CS_13582`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13582`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13583

- `CS_13583` — 无字段（空消息）
- `SC_13583`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | strength_rest | uint32 |
  | strength_name | string |

## 命令 13584

- `CS_13584`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | npc_x | int32 |
  | npc_y | int32 |

- `SC_13584`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13600

- `CS_13600` — 无字段（空消息）
- `SC_13600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | left_fresh_time | uint32 |
  | boss_list | table(uid:uint32, npc_bid:uint32, create_lev:uint8, mon_bid:uint32, star:uint8, map_bid:uint32, x:uint8, y:uint8, role_id:uint32, role_srv_id:string, role_name:string, status:uint8) |
  | accept_list | table(uid:uint32, npc_bid:uint32, create_lev:uint8, mon_bid:uint32, star:uint8, map_bid:uint32, x:uint8, y:uint8) |
  | srv_record | table(name:string, rewards:D|Dsc13600rewards|) |
  | self_record | table(rewards:D|Dsc13600rewards|) |

## 命令 13601

- `CS_13601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | uid | uint32 |

- `SC_13601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | uid | uint32 |
  | role_id | uint32 |
  | role_srv_id | string |
  | role_name | string |

## 命令 13701

- `CS_13701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | lev | uint8 |

## 命令 13702

- `CS_13702`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_13702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | lev | uint8 |

## 命令 13703

- `CS_13703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | flag | uint8 |

- `SC_13703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | lev | uint8 |

## 命令 13704

- `CS_13704` — 无字段（空消息）
- `SC_13704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev1 | uint8 |
  | lev2 | uint8 |
  | lev3 | uint8 |
  | lev4 | uint8 |

## 命令 13711

- `CS_13711` — 无字段（空消息）
- `SC_13711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13721

- `CS_13721`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13721`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13731

- `CS_13731`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13731`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13741

- `CS_13741` — 无字段（空消息）
- `SC_13741`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint8 |
  | learn_list | table(item_bid:uint32) |

## 命令 13742

- `CS_13742` — 无字段（空消息）
- `SC_13742`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |

## 命令 13743

- `CS_13743`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13743`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13771

- `CS_13771` — 无字段（空消息）
- `SC_13771`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint16 |
  | price | uint32 |

## 命令 13772

- `CS_13772` — 无字段（空消息）
- `SC_13772`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | val | uint16 |

## 命令 13781

- `CS_13781` — 无字段（空消息）
- `SC_13781`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | total_val | uint16 |
  | huoli_list | table(id:uint16, num:uint16, val:uint16) |
  | lingqu_list | table(huoli:uint16) |

## 命令 13786

- `CS_13786` — 无字段（空消息）
- `SC_13786`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | week | uint8 |
  | richang_list | table(id:uint16, num:uint16) |
  | status_list | table(id:uint16, num:uint16) |

## 命令 13787

- `CS_13787` — 无字段（空消息）
- `SC_13787`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | lingqu_list | table(huoli:uint16) |

## 命令 13788

- `CS_13788` — 无字段（空消息）
- `SC_13788` — 无字段（空消息）
## 命令 13789

- `CS_13789`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | huoli | uint16 |

- `SC_13789`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | huoli | uint16 |

## 命令 13801

- `CS_13801`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | page | uint8 |

- `SC_13801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | left_time | uint16 |
  | type | uint16 |
  | cur_page | uint8 |
  | max_page | uint8 |
  | goods_list | table(market_id:uint32, item_bid:uint32, item_num:uint16, sell_num:uint16, sell_type:uint8, price:uint32, time_out:uint32) |

## 命令 13802

- `CS_13802`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |

- `SC_13802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc13802attrs_ext|, attrs_ext_list:D|Dsc13802attrs_ext_list|, attrs_ext_one_list:D|Dsc13802attrs_ext_one_list|, jewel_list:D|Dsc13802jewel_list|, str_ext_list:D|Dsc13802str_ext_list|) |

## 命令 13803

- `CS_13803`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |

- `SC_13803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13806

- `CS_13806` — 无字段（空消息）
- `SC_13806`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | add_space | uint8 |
  | goods_list | table(market_id:uint32, item_bid:uint32, item_num:uint16, sell_num:uint16, sell_type:uint8, price:uint32, time_out:uint32) |

## 命令 13807

- `CS_13807`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |

- `SC_13807`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc13807attrs_ext|, attrs_ext_list:D|Dsc13807attrs_ext_list|, attrs_ext_one_list:D|Dsc13807attrs_ext_one_list|, jewel_list:D|Dsc13807jewel_list|, str_ext_list:D|Dsc13807str_ext_list|) |

## 命令 13810

- `CS_13810`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | sell_list | table(item_id:uint32, price:uint32, sell_num:uint16, sell_type:uint8) |

- `SC_13810`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | sell_list | table(item_id:uint32) |

## 命令 13811

- `CS_13811`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |
  | price | uint32 |
  | sell_num | uint16 |
  | sell_type | uint8 |

- `SC_13811`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13812

- `CS_13812`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |

- `SC_13812`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | market_id | uint32 |

## 命令 13813

- `CS_13813`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |
  | price | uint32 |
  | buy_num | uint16 |

- `SC_13813`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | market_id | uint32 |
  | item_num | uint16 |
  | sell_num | uint16 |
  | sell_type | uint8 |

## 命令 13814

- `CS_13814`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |

- `SC_13814`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | market_id | uint32 |

## 命令 13815

- `CS_13815`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13815`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | price | uint32 |
  | gold | uint32 |

## 命令 13816

- `CS_13816`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | market_id | uint32 |
  | item_bid | uint32 |
  | item_num | uint16 |
  | price | uint32 |
  | sell_type | uint8 |

- `SC_13816`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | market_id | uint32 |

## 命令 13817

- `CS_13817`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | tiqu_list | table(market_id:uint32, item_id:uint32) |

- `SC_13817`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | tiqu_list | table(market_id:uint32) |

## 命令 13818

- `CS_13818`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | re_sell_list | table(market_id:uint32, item_bid:uint32, item_num:uint16, price:uint32, sell_type:uint8) |

- `SC_13818`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13819

- `SC_13819` — 无字段（空消息）
## 命令 13821

- `CS_13821`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | add_space | uint8 |

- `SC_13821`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | sum_space | uint8 |

## 命令 13826

- `CS_13826`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | need_update_list | table(market_id:uint32, item_id:uint32) |

- `SC_13826`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | update_my_goods_list | table(market_id:uint32, item_bid:uint32, item_num:uint16, sell_num:uint16, price:uint32, time_out:uint32, sell_type:uint8) |

## 命令 13841

- `CS_13841`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |

- `SC_13841`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint16 |
  | yinbi_list | table(item_bid:uint32, last_price:uint32, cur_price:uint32) |

## 命令 13842

- `CS_13842`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | num | uint32 |

- `SC_13842`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13843

- `CS_13843`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_13843`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13851

- `CS_13851`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_13851`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | price | uint32 |

## 命令 13901

- `CS_13901` — 无字段（空消息）
- `SC_13901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | month_card_timeout | uint32 |
  | charge_list | table(use_val:uint32, get_val:uint32, add_val:uint32, ico:uint8, pic:uint8, is_firset:uint8) |
  | is_imperial_card | uint8 |
  | charge_return_rate | uint32 |

## 命令 13902

- `CS_13902`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rmb | uint16 |

- `SC_13902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13906

- `CS_13906`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | label | uint8 |

- `SC_13906`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | label | uint8 |
  | val_list | table(use_val:uint16, get_val:uint32, add_val:uint32, ico:uint8, pic:uint8) |

## 命令 13907

- `CS_13907`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | label | uint8 |
  | rmb | uint16 |

- `SC_13907`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 13910

- `CS_13910`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | body | string |

## 命令 13999

- `CS_13999`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | sign | int32 |

- `SC_13999`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | sign | int32 |

## 命令 14000

- `CS_14000`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_14000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | select_type | uint8 |
  | info_list | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14000hero_pos_info|, member_pos_info:D|Dsc14000member_pos_info|) |

## 命令 14001

- `CS_14001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_14001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14001hero_pos_info|, member_pos_info:D|Dsc14001member_pos_info|) |

## 命令 14002

- `CS_14002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_14002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14002hero_pos_info|, member_pos_info:D|Dsc14002member_pos_info|) |

## 命令 14003

- `CS_14003`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |

- `SC_14003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | s_type | uint8 |

## 命令 14004

- `CS_14004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_14004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | type | uint8 |
  | f_lev | uint8 |

## 命令 14005

- `CS_14005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |

- `SC_14005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | type | uint8 |
  | f_lev | uint8 |
  | hero_pos_info | table(hero_bid:uint32, pos:uint8) |
  | member_pos_info | table(member_id:uint32, member_srv_id:string, career:uint16, pos:uint8, sex:uint16) |

## 命令 14006

- `CS_14006`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | hero_bid | uint32 |
  | pos | uint8 |

- `SC_14006`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | cheer_hero | table(hero_bid:uint32, pos:uint8) |

## 命令 14007

- `CS_14007`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | hero_bid | uint32 |

- `SC_14007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | cheer_hero | table(hero_bid:uint32, pos:uint8) |

## 命令 14008

- `CS_14008`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | hero_bid | uint32 |

- `SC_14008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14008hero_pos_info|, member_pos_info:D|Dsc14008member_pos_info|) |

## 命令 14009

- `CS_14009`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_14009`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | cheer_hero | table(hero_bid:uint32, pos:uint8) |

## 命令 14020

- `CS_14020`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_14020`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | select_type | uint8 |
  | info_list | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14020hero_pos_info|, member_pos_info:D|Dsc14020member_pos_info|) |

## 命令 14021

- `CS_14021`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_14021`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14021hero_pos_info|, member_pos_info:D|Dsc14021member_pos_info|) |

## 命令 14022

- `CS_14022`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_bid | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_14022`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14022hero_pos_info|, member_pos_info:D|Dsc14022member_pos_info|) |

## 命令 14023

- `CS_14023`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |

- `SC_14023`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | s_type | uint8 |

## 命令 14028

- `CS_14028`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | hero_bid | uint32 |

- `SC_14028`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc14028hero_pos_info|, member_pos_info:D|Dsc14028member_pos_info|) |

## 命令 14099

- `CS_14099` — 无字段（空消息）
- `SC_14099`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | attr_list | table(attr:uint8, value:uint32) |

## 命令 14100

- `CS_14100` — 无字段（空消息）
- `SC_14100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | days | uint8 |
  | is_get | uint8 |
  | vip_lev | uint8 |

## 命令 14101

- `CS_14101` — 无字段（空消息）
- `SC_14101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | days | uint8 |
  | assets | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 14200

- `CS_14200` — 无字段（空消息）
- `SC_14200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14201

- `CS_14201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |

- `SC_14201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | code | uint8 |
  | msg | string |

## 命令 14202

- `CS_14202` — 无字段（空消息）
- `SC_14202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lave_count | uint32 |
  | refresh_list | table(rid:uint32, srv_id:string, name:string, mission_bid:uint32, status:uint32, quality:uint8, refresh_count:uint8, all_refresh_count:uint8, brush_count:uint8) |

## 命令 14203

- `CS_14203` — 无字段（空消息）
- `SC_14203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | mission_bid | uint32 |
  | status | uint32 |
  | quality | uint8 |
  | refresh_count | uint8 |
  | all_refresh_count | uint8 |
  | brush_count | uint8 |

## 命令 14204

- `CS_14204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_14204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | quality_id | uint8 |
  | assets_list | table(type:uint8, value:uint32) |

## 命令 14205

- `CS_14205` — 无字段（空消息）
- `SC_14205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14206

- `CS_14206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | type2 | uint8 |

- `SC_14206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | type2 | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 14207

- `CS_14207` — 无字段（空消息）
- `SC_14207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lave_count | uint32 |

## 命令 14210

- `CS_14210` — 无字段（空消息）
- `SC_14210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | reward_list | table(id:uint8) |
  | total_star | uint32 |
  | mission_list | table(bid:uint32, star:uint8, reward_flag:uint8, ext:D|Dsc14210ext|) |
  | free_times | uint8 |
  | free_refresh_time | uint8 |

## 命令 14211

- `CS_14211`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | pay_type | uint8 |

- `SC_14211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | star | uint8 |
  | free_times | uint8 |

## 命令 14212

- `CS_14212`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_14212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | total_star | uint32 |

## 命令 14213

- `CS_14213`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_14213`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 14214

- `SC_14214`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

## 命令 14215

- `SC_14215`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | ext | table(key:uint8, val:uint32) |

## 命令 14216

- `CS_14216` — 无字段（空消息）
- `SC_14216`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14298

- `CS_14298` — 无字段（空消息）
- `SC_14298`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | free_refresh_time | uint8 |

## 命令 14299

- `CS_14299`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | uint32 |

- `SC_14299`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | mission | table(bid:uint32, star:uint8, status:uint8, ext:D|Dsc14299ext|) |

## 命令 14300

- `CS_14300` — 无字段（空消息）
- `SC_14300` — 无字段（空消息）
## 命令 14301

- `CS_14301`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint32 |

- `SC_14301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14302

- `CS_14302` — 无字段（空消息）
- `SC_14302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint32 |

## 命令 14400

- `CS_14400` — 无字段（空消息）
- `SC_14400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | animal_lev | uint8 |
  | animal_exp | uint32 |
  | call_times | uint8 |
  | animal_record | table(role_name:string, type:uint8, exp:uint16) |

## 命令 14401

- `CS_14401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | feed_type | uint8 |

- `SC_14401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14402

- `CS_14402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | animal_lev | uint8 |

- `SC_14402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14403

- `CS_14403` — 无字段（空消息）
- `SC_14403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | feed_times | uint8 |
  | all_times | uint8 |

## 命令 14404

- `CS_14404` — 无字段（空消息）
- `SC_14404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14500

- `CS_14500` — 无字段（空消息）
- `SC_14500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14501

- `CS_14501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_14501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

## 命令 14502

- `CS_14502` — 无字段（空消息）
- `SC_14502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | times | uint32 |
  | times_led | uint32 |
  | times_week | uint32 |

## 命令 14503

- `CS_14503` — 无字段（空消息）
- `SC_14503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | exp | uint32 |
  | coin | uint32 |

## 命令 14504

- `CS_14504`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_14504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14505

- `CS_14505` — 无字段（空消息）
- `SC_14505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 14506

- `SC_14506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cur_double | uint16 |
  | week_left_double | uint16 |

## 命令 14507

- `CS_14507` — 无字段（空消息）
- `SC_14507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14600

- `CS_14600` — 无字段（空消息）
- `SC_14600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | days | uint16 |
  | get_day | table(type:uint8) |

## 命令 14601

- `CS_14601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | days | uint8 |

- `SC_14601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | days | uint8 |

## 命令 14700

- `CS_14700` — 无字段（空消息）
- `SC_14700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | lottery_list | table(id:uint32, bid:uint32, quantity:uint32, bind:uint8) |

## 命令 14701

- `CS_14701` — 无字段（空消息）
- `SC_14701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | code | uint8 |
  | msg | string |

## 命令 14801

- `CS_14801` — 无字段（空消息）
- `SC_14801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | do_help_num | uint8 |
  | send_help_num | uint8 |
  | is_finish | uint8 |
  | left_time | uint32 |
  | lian_list | table(ord:uint8, item_bid:uint32, item_group:uint32, item_num:uint8, is_finish:uint8, is_help:uint8, xiu_exp:uint16) |

## 命令 14802

- `CS_14802`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_14802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | left_time | uint32 |
  | lian_list | table(ord:uint8, item_bid:uint32, item_group:uint32, item_num:uint8, is_finish:uint8, is_help:uint8, xiu_exp:uint16) |

## 命令 14803

- `CS_14803` — 无字段（空消息）
- `SC_14803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | do_help_num | uint8 |
  | send_help_num | uint8 |
  | is_finish | uint8 |
  | left_time | uint32 |
  | lian_list | table(ord:uint8, item_bid:uint32, item_group:uint32, item_num:uint8, is_finish:uint8, is_help:uint8, xiu_exp:uint16) |

## 命令 14806

- `CS_14806`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |

- `SC_14806`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 14807

- `CS_14807` — 无字段（空消息）
- `SC_14807`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 14811

- `CS_14811`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |

- `SC_14811`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 14812

- `CS_14812`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | ord | uint8 |

- `SC_14812`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | ord | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 14901

- `CS_14901` — 无字段（空消息）
- `SC_14901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | cur_bid | uint16 |
  | xs_title_list | table(bid:uint16, left_time:uint32) |

## 命令 14906

- `CS_14906`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `SC_14906`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint16 |

## 命令 15000

- `CS_15000`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint8 |
  | item_list | table(pos:uint32, item_type:uint8, bid:uint32, quantity:uint32, bind:uint8) |
  | event_list | table(pos:uint32, event_type:uint8) |

## 命令 15001

- `CS_15001` — 无字段（空消息）
- `SC_15001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15002

- `CS_15002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_id | uint32 |
  | MapBid | uint32 |
  | x | uint16 |
  | y | uint16 |

## 命令 15003

- `CS_15003`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15011

- `SC_15011`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | elem_id | uint32 |
  | box_bid | uint32 |
  | item_list | table(item_bid:uint32, item_num:uint32) |
  | assets | table(assets_code:uint8, number:uint32) |

## 命令 15012

- `CS_15012`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | elem_id | uint32 |
  | box_bid | uint32 |

- `SC_15012`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15013

- `SC_15013`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | elem_id | uint32 |
  | box_bid | uint32 |
  | item_bid | uint32 |
  | item_num | uint32 |
  | is_roll | uint8 |
  | end_time | uint32 |
  | roll_member | table(rid:uint32, srv_id:string, is_leader:uint8, name:string, lev:uint8, head_bid:uint32, career:uint8, sex:uint8, roll_point:uint8) |

## 命令 15014

- `SC_15014`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | elem_id | uint32 |
  | box_bid | uint32 |
  | pos | uint8 |
  | item_list | table(pos:uint32, bid:uint32, number:uint32, bind:uint8) |

## 命令 15015

- `CS_15015`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | elem_id | uint32 |
  | box_bid | uint32 |

- `SC_15015`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15016

- `CS_15016` — 无字段（空消息）
- `SC_15016`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | roll_point | uint8 |

## 命令 15017

- `SC_15017`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | is_end | uint8 |
  | win_rid | uint32 |
  | win_srv_id | string |
  | roll_member | table(rid:uint32, srv_id:string, roll_point:uint8, add_point:uint8) |

## 命令 15101

- `CS_15101` — 无字段（空消息）
- `SC_15101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stop_val | uint16 |
  | val_list | table(val:uint16) |

## 命令 15102

- `CS_15102` — 无字段（空消息）
- `SC_15102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15200

- `CS_15200` — 无字段（空消息）
- `SC_15200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15201

- `CS_15201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_15201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

## 命令 15202

- `CS_15202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_15202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15203

- `CS_15203` — 无字段（空消息）
- `SC_15203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15204

- `CS_15204` — 无字段（空消息）
- `SC_15204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |
  | gold | uint8 |

## 命令 15205

- `SC_15205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 15206

- `CS_15206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | times | uint8 |

- `SC_15206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15207

- `CS_15207` — 无字段（空消息）
- `SC_15207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | item_list | table(item_bid:uint32, gold:uint16) |

## 命令 15208

- `CS_15208` — 无字段（空消息）
- `SC_15208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | times | uint16 |
  | item_list | table(item_bid:uint32, item_cnt:uint16, coupon:uint32, status:uint8) |

## 命令 15300

- `CS_15300` — 无字段（空消息）
- `SC_15300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15301

- `CS_15301`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_15301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

## 命令 15302

- `CS_15302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_15302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15303

- `CS_15303` — 无字段（空消息）
- `SC_15303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 15400

- `CS_15400` — 无字段（空消息）
- `SC_15400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15401

- `SC_15401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | loop_num | uint8 |

## 命令 15402

- `CS_15402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_15402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

## 命令 15403

- `CS_15403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_15403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15404

- `SC_15404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 15405

- `CS_15405` — 无字段（空消息）
- `SC_15405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | loop_count | uint16 |

## 命令 15420

- `CS_15420` — 无字段（空消息）
- `SC_15420`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15421

- `CS_15421`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_15421`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15422

- `CS_15422` — 无字段（空消息）
- `SC_15422`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15501

- `CS_15501` — 无字段（空消息）
- `SC_15501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | jie | uint8 |
  | jie_luck | uint16 |
  | grow | uint16 |
  | zz | uint16 |
  | face | uint8 |
  | use | uint8 |
  | skill_list | table(skill_bid_bid:uint32) |
  | attr_list | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, mspd:uint32, tenacity:uint32, hit:uint32, dodge:uint32, crit:uint32, red_def_s:uint32, red_def_p:uint32) |
  | can_item_list | table(jie:uint8, item_bid:uint32, item_num:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc15501attrs_ext|, attrs_ext_list:D|Dsc15501attrs_ext_list|, attrs_ext_one_list:D|Dsc15501attrs_ext_one_list|, jewel_list:D|Dsc15501jewel_list|, str_ext_list:D|Dsc15501str_ext_list|) |
  | surface_list | table(surface_id:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 15506

- `CS_15506` — 无字段（空消息）
- `SC_15506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jie_luck | uint16 |

## 命令 15507

- `CS_15507` — 无字段（空消息）
- `SC_15507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15511

- `CS_15511`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15511`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15512

- `CS_15512`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15512`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15516

- `CS_15516`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | jie | uint8 |

- `SC_15516`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jie | uint8 |

## 命令 15517

- `CS_15517`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_15517`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | flag | uint8 |

## 命令 15518

- `CS_15518`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id_lev | uint32 |
  | item_id_list | table(item_id:uint32) |

- `SC_15518`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15519

- `CS_15519`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_15519`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15520

- `CS_15520`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_15520`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 15601

- `CS_15601` — 无字段（空消息）
- `SC_15601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | left_time | uint32 |
  | primus_list | table(bid:uint8, lev:uint16, status:uint8, primus_role_list:D|Dsc15601primus_role_list|) |

## 命令 15606

- `CS_15606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint8 |

- `SC_15606`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15607

- `CS_15607` — 无字段（空消息）
- `SC_15607`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint8 |
  | code | uint8 |

## 命令 15611

- `CS_15611` — 无字段（空消息）
- `SC_15611`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15700

- `CS_15700` — 无字段（空消息）
- `SC_15700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | use_id | uint32 |
  | shenqi_list | table(id:uint32, lev:uint16, star:uint16, status:uint8, mark:uint16) |

## 命令 15701

- `CS_15701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_15701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |

## 命令 15702

- `CS_15702`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_15702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | new_use_id | uint32 |

## 命令 15703

- `CS_15703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_15703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | id | uint32 |
  | new_lev | uint16 |
  | new_star | uint16 |

## 命令 15704

- `CS_15704`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint8 |

- `SC_15704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15801

- `CS_15801` — 无字段（空消息）
- `SC_15801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | jie | uint8 |
  | jie_luck | uint16 |
  | grow | uint16 |
  | zz | uint16 |
  | face | uint8 |
  | use | uint8 |
  | skill_list | table(skill_bid_bid:uint32) |
  | attr_list | table(atk_s:uint32, atk_p:uint32, def_s:uint32, def_p:uint32, hp_max:uint32, atk_speed:uint32, tenacity:uint32, hit:uint32, dodge:uint32, crit:uint32, red_def_s:uint32, red_def_p:uint32) |
  | can_item_list | table(jie:uint8, item_bid:uint32, item_num:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc15801attrs_ext|, attrs_ext_list:D|Dsc15801attrs_ext_list|, attrs_ext_one_list:D|Dsc15801attrs_ext_one_list|, jewel_list:D|Dsc15801jewel_list|, str_ext_list:D|Dsc15801str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 15806

- `CS_15806` — 无字段（空消息）
- `SC_15806`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jie_luck | uint16 |

## 命令 15807

- `CS_15807` — 无字段（空消息）
- `SC_15807`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15811

- `CS_15811`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15811`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15812

- `CS_15812`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_15812`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15816

- `CS_15816`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | jie | uint16 |

- `SC_15816`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jie | uint16 |

## 命令 15817

- `CS_15817`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_15817`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | flag | uint8 |

## 命令 15818

- `CS_15818`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id_lev | uint32 |
  | item_id_list | table(item_id:uint32) |

- `SC_15818`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15819

- `CS_15819`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_15819`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15820

- `CS_15820`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_15820`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 15821

- `CS_15821`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_15821`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 15900

- `CS_15900` — 无字段（空消息）
- `SC_15900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | Id | uint32 |

## 命令 15901

- `CS_15901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Id | uint32 |

## 命令 16000

- `CS_16000` — 无字段（空消息）
- `SC_16000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint32 |
  | flag | uint8 |
  | status | uint8 |

## 命令 16001

- `CS_16001` — 无字段（空消息）
- `SC_16001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | item_list | table(bid:uint32, quantity:uint32, bind:uint8) |

## 命令 16002

- `CS_16002` — 无字段（空消息）
- `SC_16002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 16100

- `CS_16100` — 无字段（空消息）
- `SC_16100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |

## 命令 16101

- `CS_16101` — 无字段（空消息）
- `SC_16101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | left_time | uint32 |
  | index | uint8 |
  | correct_num | uint8 |
  | question_id | uint32 |

## 命令 16102

- `CS_16102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | question_id | uint32 |
  | answer | uint8 |

- `SC_16102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | correct_num | uint8 |
  | correct_answer | uint8 |
  | question_id | uint32 |

## 命令 16103

- `SC_16103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | correct_num | uint8 |

## 命令 16110

- `CS_16110` — 无字段（空消息）
- `SC_16110`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |

## 命令 16111

- `CS_16111` — 无字段（空消息）
- `SC_16111`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | left_time | uint32 |
  | index | uint8 |
  | correct_num | uint8 |
  | question_id | uint32 |

## 命令 16112

- `CS_16112`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | question_id | uint32 |
  | answer_list | table(answer_id:uint16) |

- `SC_16112`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | correct_num | uint8 |
  | correct_answer_list | table(answer_id:uint16) |
  | question_id | uint32 |

## 命令 16113

- `SC_16113`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | correct_num | uint8 |

## 命令 16200

- `CS_16200` — 无字段（空消息）
- `SC_16200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |
  | boss_list | table(mon_bid:uint32, kill:uint8, map_bid:uint32, x:uint16, y:uint16, left_time:uint32, award:uint8) |

## 命令 16201

- `SC_16201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

## 命令 16202

- `CS_16202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_16202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |
  | kill | uint8 |
  | map_bid | uint32 |
  | x | uint16 |
  | y | uint16 |
  | left_time | uint32 |
  | award | uint8 |

## 命令 16300

- `CS_16300`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ElementId | uint32 |

- `SC_16300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flower_id | uint32 |
  | rid | uint32 |
  | srv_id | string |
  | r_name | string |
  | water_count | uint16 |
  | rate | uint16 |
  | asset_code | uint8 |
  | asset_val | uint32 |

## 命令 16301

- `CS_16301`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_16301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | water_count | uint16 |
  | code | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | msg | string |

## 命令 16302

- `CS_16302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_16302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16303

- `CS_16303`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_16303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | water_list | table(rid:uint32, srv_id:string, name:string, year:uint16, month:uint16, day:uint16, hour:uint16, min:uint16, sec:uint16) |

## 命令 16304

- `CS_16304` — 无字段（空消息）
- `SC_16304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flowers | table(rid:uint32, srv_id:string, element_id:uint32, r_name:string, water:uint8) |

## 命令 16400

- `CS_16400`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | chengjiu | table(bid:uint32, val:uint16, time:uint32) |
  | chengjiu_has | table(bid:uint32, time_out:uint32, state:uint8) |
  | chengjiu_rate | table(bid:uint32, rate:uint8) |

## 命令 16401

- `CS_16401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_16401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |

## 命令 16402

- `SC_16402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chengjiu | table(bid:uint32, time_out:uint32) |

## 命令 16403

- `SC_16403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | chengjiu | table(bid:uint32, val:uint32, time:uint32) |

## 命令 16404

- `CS_16404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint32 |

- `SC_16404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | chengjiu_rate | table(bid:uint32, rate:uint8) |

## 命令 16500

- `CS_16500` — 无字段（空消息）
- `SC_16500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | info | table(type:uint8, is_active:uint8, get_num:uint8, can_buy:uint8, time:uint32, charge_rmb:uint32) |

## 命令 16501

- `CS_16501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | type | uint8 |
  | get_info | table(day_or_lev:uint8) |
  | can_get_info | table(can_day_or_lev:uint8) |

## 命令 16502

- `CS_16502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | val | uint16 |

- `SC_16502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | type | uint8 |
  | val | uint16 |

## 命令 16503

- `CS_16503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | get_info | table(day_or_lev:uint8) |
  | can_get_info | table(can_day_or_lev:uint8) |

## 命令 16601

- `CS_16601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_list | table(bid:uint32, title:string, title2:string, ico:string, type_ico:uint8, top_banner:string, rule_str:string, time_str:string, bottom_alert:string, aim_title:string, panel_type:uint8, remain_sec:uint32, channel_ban:string) |

## 命令 16602

- `CS_16602`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | holiday_list | table(bid:uint32, can_get_num:uint8) |

## 命令 16603

- `CS_16603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_16603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | remain_sec | uint32 |
  | finish | uint32 |
  | aim_list | table(aim:uint32, aim_str:string, status:uint8, item_list:D|Dsc16603item_list|, int_args:D|Dsc16603int_args|) |
  | item_effect_list | table(bid:uint32, effect_1:uint8, effect_2:uint8) |
  | int_args | table(val:uint32) |
  | client_reward | string |
  | rank_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, lev:uint8, val:uint32) |

## 命令 16604

- `CS_16604`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | aim | uint32 |
  | arg | uint32 |

- `SC_16604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16605

- `CS_16605`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid_list | table(bid:uint32) |

- `SC_16605`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | table(bid:uint32, code:uint8, end_time:uint32) |

## 命令 16606

- `CS_16606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

## 命令 16610

- `CS_16610` — 无字段（空消息）
- `SC_16610`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | end_date | string |
  | cost_item | uint32 |
  | cost_num | uint32 |
  | reward_list | table(id:uint8, type:uint8, item_id:uint32, num:uint32, state:uint8) |

## 命令 16611

- `CS_16611` — 无字段（空消息）
- `SC_16611`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | reward_id | uint8 |
  | reward_list | table(id:uint8, type:uint8, item_id:uint32, num:uint32, state:uint8) |

## 命令 16612

- `CS_16612` — 无字段（空消息）
- `SC_16612`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | his_list | table(srv_id:string, name:string, type:uint8, item_id:uint32, num:uint32) |

## 命令 16613

- `CS_16613` — 无字段（空消息）
- `SC_16613`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | name | string |
  | type | uint8 |
  | item_id | uint32 |
  | num | uint32 |

## 命令 16614

- `CS_16614` — 无字段（空消息）
- `SC_16614`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | total_score | uint32 |
  | title2 | string |
  | top_banner | string |
  | rule_str | string |
  | time_str | string |
  | aim_list | table(aim:uint32, status:uint8, item_list:D|Dsc16614item_list|) |
  | record_list | table(srv_id:string, name:string, msg:string) |

## 命令 16615

- `CS_16615` — 无字段（空消息）
- `SC_16615`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | record_list | table(srv_id:string, name:string, msg:string) |

## 命令 16616

- `CS_16616`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

- `SC_16616`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | record | string |
  | total_score | uint32 |

## 命令 16617

- `CS_16617`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | aim | uint32 |

- `SC_16617`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | aim | uint32 |
  | total_score | uint32 |

## 命令 16620

- `CS_16620`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id_list | table(id:uint32) |

- `SC_16620`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_list | table(bid:uint32, remain_sec:uint32, finish:uint32, aim_list:D|Dsc16620aim_list|, item_effect_list:D|Dsc16620item_effect_list|, int_args:D|Dsc16620int_args|, client_reward:string, rank_list:D|Dsc16620rank_list|) |

## 命令 16621

- `CS_16621` — 无字段（空消息）
- `SC_16621`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | end_date | string |
  | reward_list | table(reward_id:uint16, item_id:uint32, num:uint32, flag:uint8) |
  | card_list | table(index:uint8, reward_id:uint16) |

## 命令 16622

- `CS_16622`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |

- `SC_16622`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | index | uint8 |
  | reward_id | uint16 |
  | reset_flag | uint8 |

## 命令 16623

- `CS_16623` — 无字段（空消息）
- `SC_16623`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16624

- `CS_16624` — 无字段（空消息）
- `SC_16624`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | his_list | table(srv_id:string, name:string, item_id:uint32, num:uint32) |

## 命令 16625

- `SC_16625`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | string |
  | name | string |
  | item_id | uint32 |
  | num | uint32 |

## 命令 16626

- `CS_16626` — 无字段（空消息）
- `SC_16626`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |
  | remain_sec | uint32 |
  | list | table(mission_type:uint8, type_name:string, status:uint8, cur_progress:uint8, tot_progress:uint8, aim_str:string, item_list:D|Dsc16626item_list|, mission_list:D|Dsc16626mission_list|) |
  | client_reward | string |
  | item_effect_list | table(bid:uint32, effect_1:uint8, effect_2:uint8) |
  | refresh_times | uint8 |
  | tot_times | uint8 |

## 命令 16627

- `CS_16627`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_type | uint8 |

- `SC_16627`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | mission_type | uint8 |

## 命令 16630

- `CS_16630`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | page | uint8 |

- `SC_16630`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |
  | time_str | string |
  | page | uint8 |
  | list | table(type:uint8, order_bid:uint32, version:uint32, tag:uint8, status:uint8, rest:uint32, total:uint32, dead_line:uint32, item_list:D|Dsc16630item_list|, shelf:uint8) |
  | end_time | uint32 |
  | remain_sec | uint32 |

## 命令 16631

- `CS_16631` — 无字段（空消息）
- `SC_16631`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(role_id:uint32, srv_id:string, role_name:string, buy_cnt:uint32, total_cnt:uint32, item_bid:uint32, item_cnt:uint32, open_time:uint32) |

## 命令 16632

- `CS_16632`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |
  | type | uint8 |
  | buy_cnt | uint32 |
  | item_bid | uint32 |
  | item_cnt | uint32 |

- `SC_16632`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | order_bid | uint32 |
  | version | uint32 |
  | type | uint8 |
  | buy_cnt | uint32 |
  | sell_out | uint8 |
  | home_page | uint8 |

## 命令 16633

- `CS_16633`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |

- `SC_16633`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(role_id:uint32, srv_id:string, role_name:string, buy_cnt:uint32, time:uint32) |

## 命令 16634

- `CS_16634`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | order_bid | uint32 |
  | version | uint32 |

- `SC_16634`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | type | uint8 |
  | order_bid | uint32 |
  | version | uint32 |
  | tag | uint8 |
  | status | uint8 |
  | rest | uint32 |
  | total | uint32 |
  | dead_line | uint32 |
  | item_list | table(item_bid:uint32, item_cnt:uint32) |
  | shelf | uint8 |

## 命令 16635

- `CS_16635` — 无字段（空消息）
- `SC_16635`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | order_list | table(type:uint8, order_bid:uint32, version:uint32, buy_cnt:uint32, buy_time:uint32, rest:uint32, total:uint32, item_list:D|Dsc16635item_list|, number:uint32, role_id:uint32, srv_id:string, role_name:string, open_time:uint32, dead_line:uint32, order_status:uint8, shelf:uint8) |

## 命令 16636

- `CS_16636`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |

- `SC_16636`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | order_bid | uint32 |
  | version | uint32 |
  | buy_cnt | uint32 |
  | buy_time | uint32 |
  | rest | uint32 |
  | total | uint32 |
  | item_list | table(item_bid:uint32, item_cnt:uint32) |
  | number | uint32 |
  | role_id | uint32 |
  | srv_id | string |
  | role_name | string |
  | open_time | uint32 |
  | dead_line | uint32 |
  | order_status | uint8 |
  | shelf | uint8 |

## 命令 16637

- `CS_16637`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |

- `SC_16637`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |
  | buy_cnt | uint32 |
  | status | uint8 |
  | num_list | table(number:uint32) |

## 命令 16638

- `CS_16638`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |

- `SC_16638`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | order_bid | uint32 |
  | version | uint32 |
  | rand_num | uint32 |
  | change_num | uint32 |
  | tot_time | string |

## 命令 16639

- `CS_16639`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_type | uint8 |
  | old_mission_bid | uint32 |

- `SC_16639`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | mission_type | uint8 |
  | old_mission_bid | uint32 |
  | new_mission_bid | uint32 |
  | new_flag | uint8 |
  | refresh_times | uint8 |

## 命令 16640

- `CS_16640`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |

- `SC_16640`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |
  | choose_list | table(id:uint16, item_bid:uint32, item_cnt:uint32, item_status:uint8) |
  | coin_type | uint8 |
  | refresh_cost | uint32 |
  | refresh_status | uint8 |
  | reward_list | table(item_bid:uint32, item_cnt:uint32) |
  | status | uint8 |
  | client_reward | string |
  | item_effect_list | table(bid:uint32, effect_1:uint8, effect_2:uint8) |

## 命令 16641

- `CS_16641`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |

- `SC_16641`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | holiday_bid | uint32 |
  | coin_type | uint8 |
  | refresh_cost | uint32 |
  | choose_list | table(id:uint16, item_bid:uint32, item_cnt:uint32, item_status:uint8) |

## 命令 16642

- `CS_16642`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |
  | id | uint16 |

- `SC_16642`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | holiday_bid | uint32 |
  | id | uint16 |

## 命令 16643

- `CS_16643`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |

- `SC_16643`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | holiday_bid | uint32 |

## 命令 16646

- `CS_16646`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16646`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | list | table(id:uint32, order:uint8, tot_time:uint8, status:uint8, reward_list:D|Dsc16646reward_list|, coin_type1:uint8, coin1:uint32) |
  | countdown | uint32 |

## 命令 16647

- `CS_16647`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | type | uint8 |
  | order | uint8 |

- `SC_16647`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | type | uint8 |
  | order | uint8 |

## 命令 16648

- `SC_16648`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | list | table(id:uint32, order:uint8, tot_time:uint8, status:uint8, reward_list:D|Dsc16648reward_list|, coin_type1:uint8, coin1:uint32) |

## 命令 16649

- `CS_16649`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16649`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | coin_type1 | uint8 |
  | coin1 | uint32 |

## 命令 16650

- `CS_16650`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_16650`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |

## 命令 16651

- `CS_16651` — 无字段（空消息）
- `SC_16651`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | remain_sec | uint32 |
  | cash_reward | uint32 |
  | card_list | table(index:uint32, card_id:uint32, gold:uint32, status:uint8) |
  | item_list | table(bid:uint32, num:uint32) |
  | item_effect_list | table(bid:uint32, effect_1:uint8, effect_2:uint8) |
  | client_reward | string |

## 命令 16652

- `CS_16652`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint32 |

- `SC_16652`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | index | uint32 |
  | status | uint8 |

## 命令 16653

- `CS_16653` — 无字段（空消息）
- `SC_16653`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16664

- `CS_16664` — 无字段（空消息）
- `SC_16664`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |
  | bid | uint32 |
  | remain_sec | uint32 |
  | status | uint32 |
  | end_time | uint32 |
  | rate | uint32 |
  | client_reward | string |

## 命令 16665

- `CS_16665` — 无字段（空消息）
- `SC_16665`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | end_time | uint32 |
  | score | uint32 |
  | level | uint8 |
  | index | uint8 |
  | record_list | table(msg:string) |

## 命令 16666

- `CS_16666`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |

- `SC_16666`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | per_level | uint8 |
  | per_index | uint8 |
  | new_level | uint8 |
  | new_index | uint8 |
  | score | uint32 |
  | count | uint8 |
  | run_list | table(sort:uint8, level:uint8, index:uint8, tmp_score:uint32) |

## 命令 16667

- `CS_16667` — 无字段（空消息）
- `SC_16667`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | reward_list | table(item_bid:uint32, num:uint32) |

## 命令 16668

- `CS_16668` — 无字段（空消息）
- `SC_16668`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_list | table(msg:string) |

## 命令 16693

- `CS_16693` — 无字段（空消息）
- `SC_16693`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | info | table(key:uint8, val:uint32) |
  | records | table(name:string, id:uint32, item_bid:uint32, val:uint32) |

## 命令 16694

- `CS_16694`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |

- `SC_16694`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | bonus | uint32 |
  | rewards | table(id:uint32, item_bid:uint32, cnt:uint32) |
  | records | table(name:string, id:uint32, item_bid:uint32, val:uint32) |

## 命令 16695

- `CS_16695` — 无字段（空消息）
- `SC_16695`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | item_list | table(bid:uint16, num:uint32) |

## 命令 16696

- `CS_16696` — 无字段（空消息）
- `SC_16696`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_list | table(bid:uint16, num:uint32) |

## 命令 16697

- `CS_16697` — 无字段（空消息）
- `SC_16697`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint32 |
  | end_time | uint32 |
  | need_item_bid | uint16 |
  | need_item_num | uint32 |
  | trun_list | table(bid:uint16) |
  | ext_list | table(type:uint8, num:uint32, item_list:D|Dsc16697item_list|) |

## 命令 16698

- `CS_16698`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | n | uint32 |

- `SC_16698`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | n | uint32 |
  | num | uint32 |
  | bid_list | table(bid:uint32) |

## 命令 16699

- `CS_16699` — 无字段（空消息）
- `SC_16699`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | item_list | table(bid:uint16, num:uint32) |

## 命令 16700

- `CS_16700` — 无字段（空消息）
- `SC_16700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | vip_lev | uint8 |
  | get_award | uint8 |

## 命令 16701

- `CS_16701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | vip_lev | uint8 |

- `SC_16701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | get_info | table(vip_lev:uint8, get_award:uint8) |

## 命令 16702

- `CS_16702`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | vip_lev | uint8 |

- `SC_16702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | get_award | uint8 |

## 命令 16703

- `CS_16703` — 无字段（空消息）
- `SC_16703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16704

- `CS_16704` — 无字段（空消息）
- `SC_16704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | vip_lev | uint8 |
  | status | uint8 |

## 命令 16705

- `CS_16705` — 无字段（空消息）
- `SC_16705`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |

## 命令 16706

- `CS_16706` — 无字段（空消息）
- `SC_16706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | qq | string |
  | items | table(item:uint32, num:uint8) |

## 命令 16800

- `SC_16800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | arg_uint32 | table(key:uint8, value:uint32) |
  | arg_str | table(key:uint8, value:string) |

## 命令 16900

- `CS_16900` — 无字段（空消息）
- `SC_16900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | charge | uint32 |
  | status | table(key:uint32, state:uint8) |

## 命令 16901

- `CS_16901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | key | uint32 |

- `SC_16901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 16903

- `CS_16903` — 无字段（空消息）
- `SC_16903`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint32 |
  | online_time | uint32 |
  | next_aim | uint32 |
  | status | table(time_arg:uint32, state:uint8) |

## 命令 16904

- `CS_16904`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | aim | uint32 |

- `SC_16904`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | aim | uint32 |

## 命令 17000

- `CS_17000` — 无字段（空消息）
- `SC_17000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 17001

- `CS_17001` — 无字段（空消息）
- `SC_17001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | max_gate | uint8 |

## 命令 17100

- `CS_17100` — 无字段（空消息）
- `SC_17100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint32 |
  | gold_num | uint32 |
  | type_list | table(type:uint8) |

## 命令 17101

- `CS_17101`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_17101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | type | uint8 |
  | item_list | table(bid:uint32, quantity:uint32, bind:uint8) |

## 命令 17199

- `CS_17199`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | holiday_bid | uint32 |

- `SC_17199`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17200

- `CS_17200` — 无字段（空消息）
- `SC_17200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint32 |
  | status | uint8 |

## 命令 17201

- `CS_17201` — 无字段（空消息）
- `SC_17201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | item_list | table(bid:uint32, quantity:uint32, bind:uint8) |

## 命令 17301

- `CS_17301` — 无字段（空消息）
- `SC_17301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | daily_time | uint16 |
  | daily_time2 | uint32 |
  | score | uint32 |
  | win_times | uint32 |
  | lose_times | uint32 |
  | total_times | uint32 |
  | rest_time | uint32 |
  | first_reward | uint8 |
  | is_match | uint8 |
  | kill_number | uint32 |
  | continue_win | uint32 |
  | is_team_open | uint8 |
  | act_status | uint8 |
  | daily_win | uint16 |

## 命令 17302

- `CS_17302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | act_type | uint8 |
  | action | uint8 |

- `SC_17302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | act_type | uint8 |
  | is_match | uint8 |

## 命令 17303

- `SC_17303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | type | uint8 |
  | friend_team_power | uint32 |
  | friend_list | table(rid:uint32, srv_id:string, role_name:string, career:uint8, sex:uint8, lev:uint16, power:uint32, shenqi_res:string, zhenfa:uint32, score:uint32, leader:uint8) |
  | enemy_team_power | uint32 |
  | enemy_list | table(rid:uint32, srv_id:string, role_name:string, career:uint8, sex:uint8, lev:uint16, power:uint32, shenqi_res:string, zhenfa:uint32, score:uint32, leader:uint8) |

## 命令 17304

- `SC_17304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 17305

- `SC_17305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | act_type | uint8 |
  | bat_res | uint8 |
  | win_point | uint32 |
  | point | uint32 |
  | win_score | int32 |
  | score | uint32 |
  | coin | uint32 |
  | exp | uint32 |
  | daily_time | uint32 |
  | daily_time2 | uint32 |
  | friend_list | table(rid:uint32, srv_id:string, role_name:string, career:uint8, sex:uint8, lev:uint16, leader:uint8, score:uint32) |
  | role_hurl_list | table(rid:uint32, srv_id:string, name:string, group:uint8, lev:uint16, sex:uint8, career:uint16, hp_max:uint32, hp:uint32, hurt:uint32, master_rid:uint32, master_srv_id:string, id:uint32) |
  | daily_win | uint16 |

## 命令 17306

- `CS_17306` — 无字段（空消息）
- `SC_17306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | reward_list | table(type:uint8, num:uint8, status:uint8) |

## 命令 17307

- `CS_17307`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | num | uint8 |

- `SC_17307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |

## 命令 17308

- `CS_17308`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | start_rank | uint32 |
  | end_rank | uint32 |

- `SC_17308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank_list | table(role_name:string, rid:uint32, srid:string, rank:uint32, career:uint8, sex:uint8, score:uint32, lev:uint32, win_num:uint32) |

## 命令 17309

- `CS_17309` — 无字段（空消息）
- `SC_17309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank_list | table(role_name:string, rid:uint32, srid:string, rank:uint32, career:uint8, sex:uint8, score:uint32, lev:uint32, win_num:uint32) |

## 命令 17310

- `CS_17310` — 无字段（空消息）
- `SC_17310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | score_list | table(grade:uint32, number:uint32) |

## 命令 17311

- `CS_17311`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_17311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

## 命令 17312

- `CS_17312`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_17312`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17400

- `CS_17400` — 无字段（空消息）
- `SC_17400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | enemy_guild_id | uint32 |
  | enemy_guild_srv_id | string |
  | enemy_guild_name | string |
  | status | uint32 |
  | time | uint32 |
  | total_star | uint16 |
  | max_star | uint16 |
  | total_attack | uint32 |
  | enemy_total_star | uint16 |
  | enemy_max_star | uint16 |
  | enemy_total_attack | uint32 |
  | left_times | uint32 |

## 命令 17401

- `CS_17401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_id | uint32 |
  | guild_srv_id | string |
  | divide_num | uint32 |

- `SC_17401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | divide_num | uint32 |
  | guild_id | uint32 |
  | guild_srv_id | string |
  | member_list | table(id:uint8, r_id:uint32, r_srv_id:string, r_name:string, lev:uint8, career:uint8, sex:uint8, x:uint32, y:uint32, bei:uint32, attack_status:uint8, attack_star:uint8) |

## 命令 17402

- `CS_17402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_id | uint32 |
  | guild_srv_id | string |
  | r_id | uint32 |
  | r_srv_id | string |

- `SC_17402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | def_count | uint32 |
  | attack_star | uint8 |
  | r_name | string |

## 命令 17403

- `CS_17403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_id | uint32 |
  | guild_srv_id | string |
  | r_id | uint32 |
  | r_srv_id | string |

- `SC_17403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | attack_list | table(star:uint8, b_r_name:string, b_r_lev:uint8, is_success:uint8) |

## 命令 17404

- `CS_17404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_id | uint32 |
  | guild_srv_id | string |
  | r_id | uint32 |
  | r_srv_id | string |

- `SC_17404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | be_attack_list | table(star:uint8, b_r_name:string, b_r_lev:uint8, is_success:uint8) |

## 命令 17405

- `CS_17405`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | guild_id | uint32 |
  | guild_srv_id | string |
  | r_id | uint32 |
  | r_srv_id | string |
  | star | uint8 |

- `SC_17405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17406

- `CS_17406` — 无字段（空消息）
- `SC_17406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | attack_list | table(r_name:string, r_lev:uint8, def_count:uint32, attack_list:D|Dsc17406attack_list|) |

## 命令 17501

- `CS_17501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_17501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | type | uint8 |
  | msg | string |

## 命令 17502

- `CS_17502` — 无字段（空消息）
- `SC_17502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | state | uint8 |
  | rest_time | uint32 |

## 命令 17503

- `CS_17503` — 无字段（空消息）
- `SC_17503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | state | uint8 |
  | rest_time | uint32 |
  | rank | uint16 |
  | score | uint32 |
  | rest_count | uint8 |
  | first_state | uint8 |
  | cont_state | uint8 |
  | war_state | uint8 |

## 命令 17504

- `CS_17504` — 无字段（空消息）
- `SC_17504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank_list | table(rand:uint16, gid:uint32, srv_id:string, name:string, score:uint32, number:uint16) |

## 命令 17505

- `CS_17505` — 无字段（空消息）
- `SC_17505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank_list | table(rand:uint16, rid:uint32, srv_id:string, name:string, score:uint32, win_count:uint16, total_count:uint16) |

## 命令 17506

- `CS_17506` — 无字段（空消息）
- `SC_17506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assets_list | table(code:uint8, val:uint32) |

## 命令 17507

- `CS_17507` — 无字段（空消息）
- `SC_17507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | time | uint32 |

## 命令 17508

- `CS_17508` — 无字段（空消息）
- `SC_17508`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17509

- `CS_17509` — 无字段（空消息）
- `SC_17509`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | role_name | string |
  | lev | uint16 |
  | career | uint8 |
  | sex | uint8 |

## 命令 17510

- `CS_17510` — 无字段（空消息）
- `SC_17510`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bat_res | uint8 |
  | rest_count | uint8 |
  | rank | uint16 |
  | win_score | uint32 |
  | score | uint32 |
  | first_state | uint8 |
  | cont_state | uint8 |
  | assets | table(code:uint8, val:uint32) |

## 命令 17511

- `CS_17511` — 无字段（空消息）
- `SC_17511`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17512

- `CS_17512` — 无字段（空消息）
- `SC_17512`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career:uint16, vip_lev:uint8) |
  | channel | uint16 |
  | len | uint8 |
  | msg | string |
  | self_guild | uint8 |

## 命令 17513

- `CS_17513`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |

- `SC_17513`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | msg_list | table(role_list:D|Dsc17513role_list|, channel:uint16, len:uint8, msg:string, tick:uint32, self_guild:uint8) |

## 命令 17514

- `CS_17514`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | channel | uint16 |
  | len | uint8 |
  | msg | string |

- `SC_17514`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17515

- `CS_17515`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_17515`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | type | uint8 |
  | state | uint8 |
  | msg | string |

## 命令 17516

- `CS_17516` — 无字段（空消息）
- `SC_17516`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 17517

- `CS_17517` — 无字段（空消息）
- `SC_17517`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank | uint16 |
  | gname | string |
  | num | uint16 |
  | total_score | uint32 |
  | score | uint32 |
  | rank_list | table(rank:uint16, g_srv:string, name:string, num:uint16, total_score:uint32, score:uint32, is_self:uint8) |

## 命令 17518

- `CS_17518` — 无字段（空消息）
- `SC_17518`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | exp | uint32 |
  | hero_exp | uint32 |
  | coin | uint32 |

## 命令 17519

- `CS_17519` — 无字段（空消息）
- `SC_17519`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(rid:uint32, srv:string, name:string, gid:uint32, gsrv:string, gname:string) |

## 命令 17520

- `CS_17520`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv | string |
  | key | uint32 |

- `SC_17520`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17521

- `CS_17521` — 无字段（空消息）
- `SC_17521`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17600

- `CS_17600` — 无字段（空消息）
- `SC_17600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | days | uint16 |
  | reward | uint8 |
  | get_day | table(day:uint8, num:uint8) |

## 命令 17601

- `CS_17601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint8 |

- `SC_17601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | days | uint8 |
  | num | uint8 |

## 命令 17602

- `CS_17602` — 无字段（空消息）
- `SC_17602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 17700

- `CS_17700`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from_code | uint8 |
  | item_id | uint32 |
  | protect_id | uint32 |
  | lucky_id | uint32 |
  | lucky_num | uint8 |
  | state | uint8 |

- `SC_17700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | from_code | uint8 |
  | item_id | uint32 |
  | lev | uint8 |

## 命令 17703

- `CS_17703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | inherit_id | uint8 |
  | state | uint8 |

- `SC_17703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | eqm_item_id_new | uint32 |
  | eqm_item_bid_new | uint32 |
  | eqm_item_power_new | uint32 |
  | intensify_lev | uint8 |
  | refine | uint16 |
  | attr | table(state:uint8, code:uint8, value:uint32) |

## 命令 17704

- `CS_17704`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | state | uint8 |

- `SC_17704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | rate | uint16 |
  | refine | uint16 |
  | attr | table(state:uint8, code:uint8, value:uint32) |

## 命令 17705

- `CS_17705`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | eqm_item_id | uint32 |

- `SC_17705`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | eqm_item_id | uint32 |
  | eqm_item_power_new | uint32 |
  | rate | uint16 |
  | refine | uint16 |
  | attr | table(state:uint8, code:uint8, value:uint32) |

## 命令 17706

- `CS_17706`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | partner_id | uint32 |

- `SC_17706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_list | table(eqm_item_id:uint32, eqm_item_id_new:uint32, eqm_item_bid_new:uint32, eqm_item_power_new:uint32, intensify_lev:uint8, refine:uint16, attr:D|Dsc17706attr|) |

## 命令 17707

- `CS_17707`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id_a | uint32 |
  | partner_id_b | uint32 |

- `SC_17707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_list | table(item_id:uint32, partner_id:uint32, partner_id_new:uint32) |

## 命令 17708

- `CS_17708`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | partner_id | uint32 |

- `SC_17708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | cost | uint32 |
  | list | table(state:uint8, cur_lev:uint8, target_lev:uint32) |

## 命令 17709

- `CS_17709`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint16 |

- `SC_17709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | item_id | uint32 |

## 命令 17710

- `CS_17710`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_17710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | item_id | uint32 |

## 命令 17711

- `CS_17711`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | id | uint32 |

- `SC_17711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_id | uint32 |

## 命令 17712

- `CS_17712`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | id | uint32 |

- `SC_17712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_id | uint32 |
  | stage | uint32 |

## 命令 17713

- `CS_17713`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | item_bid | uint32 |

- `SC_17713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_id | uint32 |

## 命令 17714

- `CS_17714`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | id | uint32 |

- `SC_17714`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_id | uint32 |

## 命令 17715

- `CS_17715`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | id | uint32 |

- `SC_17715`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | item_id | uint32 |
  | list | table(item_bid:uint32, cnt:uint32) |

## 命令 17716

- `CS_17716`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code1 | uint8 |
  | id1 | uint32 |
  | bag_code2 | uint8 |
  | id2 | uint32 |

- `SC_17716`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bag_code1 | uint8 |
  | id1 | uint32 |
  | intensify_lev1 | uint32 |
  | bag_code2 | uint8 |
  | id2 | uint32 |
  | intensify_lev2 | uint32 |

## 命令 17800

- `CS_17800` — 无字段（空消息）
- `SC_17800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | free_count | uint8 |
  | all_free_count | uint8 |
  | gold_count | uint8 |
  | get_coin | uint32 |

## 命令 17801

- `CS_17801` — 无字段（空消息）
- `SC_17801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 17901

- `CS_17901` — 无字段（空消息）
- `SC_17901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rank | uint32 |
  | rest_times | uint8 |
  | buy_times | uint16 |
  | delay_sec | uint32 |
  | reward_list | table(rank:uint32, state:uint8) |

## 命令 17902

- `CS_17902` — 无字段（空消息）
- `SC_17902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rank | uint32 |
  | rank_list | table(rank:uint32, name:string, lev:uint16, career:uint8, sex:uint8, power:uint32, bid:uint32) |

## 命令 17903

- `CS_17903` — 无字段（空消息）
- `SC_17903`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | his_list | table(time:uint32, type:uint8, name:string, rank:uint32) |

## 命令 17904

- `CS_17904`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rank | uint32 |
  | bid | uint32 |

- `SC_17904`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rest_times | uint8 |
  | delay_sec | uint32 |

## 命令 17905

- `CS_17905` — 无字段（空消息）
- `SC_17905`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | res | uint8 |
  | rank | uint32 |
  | msg | string |

## 命令 17906

- `CS_17906` — 无字段（空消息）
- `SC_17906`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rest_times | uint8 |
  | buy_times | uint16 |

## 命令 17907

- `CS_17907` — 无字段（空消息）
- `SC_17907`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | delay_sec | uint8 |

## 命令 17908

- `CS_17908`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rank | uint32 |

- `SC_17908`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | reward_list | table(rank:uint32, state:uint8) |

## 命令 17909

- `CS_17909` — 无字段（空消息）
- `SC_17909`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | state | uint8 |

## 命令 18000

- `CS_18000` — 无字段（空消息）
- `SC_18000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | lucky_star | uint8 |
  | rest_times | uint8 |
  | list | table(rid:uint32, srv:string, name:string, star:uint8) |

## 命令 18001

- `CS_18001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | rid | uint32 |
  | srv | string |

- `SC_18001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | star | uint8 |
  | rest_times | uint8 |
  | rid | uint32 |
  | srv | string |
  | type | uint8 |

## 命令 18002

- `CS_18002` — 无字段（空消息）
- `SC_18002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | star | uint8 |
  | rid | uint32 |
  | srv | string |
  | name | string |

## 命令 18003

- `CS_18003` — 无字段（空消息）
- `SC_18003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | star | uint8 |

## 命令 18004

- `CS_18004` — 无字段（空消息）
- `SC_18004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lucky_star | uint8 |
  | rest_times | uint8 |

## 命令 18005

- `CS_18005` — 无字段（空消息）
- `SC_18005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18006

- `CS_18006` — 无字段（空消息）
- `SC_18006`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | task_list | table(id:uint32, num:uint16, max:uint16) |
  | reward_list | table(num:uint8, state:uint8) |

## 命令 18007

- `CS_18007`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |

- `SC_18007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | num | uint8 |
  | state | uint8 |

## 命令 18008

- `CS_18008` — 无字段（空消息）
- `SC_18008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(id:uint32) |

## 命令 18009

- `CS_18009` — 无字段（空消息）
- `SC_18009`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | skill_list | table(type:uint32, lev:uint8, lev_limit:uint8) |

## 命令 18010

- `CS_18010` — 无字段（空消息）
- `SC_18010`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | skill_data | table(type:uint32, lev_limit:uint8) |

## 命令 18011

- `CS_18011`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint32 |

- `SC_18011`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint32 |
  | lev | uint8 |

## 命令 18012

- `CS_18012`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint32 |

- `SC_18012`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint32 |
  | lev_limit | uint8 |

## 命令 18013

- `SC_18013`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | career | uint8 |
  | sex | uint8 |
  | lev | uint8 |
  | role_name | string |
  | head_bid | uint32 |

## 命令 18014

- `CS_18014`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_18014`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18015

- `SC_18015`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | career | uint8 |
  | sex | uint8 |
  | lev | uint8 |
  | role_name | string |
  | head_bid | uint32 |
  | msg | string |

## 命令 18020

- `CS_18020` — 无字段（空消息）
- `SC_18020`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | buy_list | table(id:uint32) |
  | notice_list | table(item_bid:uint32) |
  | item_list | table(id:uint32, item_bid:uint32, item_number:uint32, from_way:uint8, price_assets:uint8, last_price:uint32, buy_price:uint32, status:uint8, end_time:uint32, rid:uint32, srv_id:string) |

## 命令 18021

- `CS_18021` — 无字段（空消息）
- `SC_18021`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | item_list | table(id:uint32, item_bid:uint32, item_number:uint32, from_way:uint8, price_assets:uint8, last_price:uint32, buy_price:uint32, status:uint8, end_time:uint32, rid:uint32, srv_id:string) |

## 命令 18022

- `CS_18022`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_18022`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 18023

- `CS_18023`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | price | uint32 |

- `SC_18023`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 18024

- `CS_18024` — 无字段（空消息）
- `SC_18024`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_list | table(id:uint32, item_bid:uint32, item_number:uint32, assets:uint8, price:uint32, end_time:uint32, rid:uint32, srv_id:string) |

## 命令 18025

- `CS_18025` — 无字段（空消息）
- `SC_18025`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_list | table(item_bid:uint32, item_number:uint32, type:uint8, assets:uint8, price:uint32, rid:uint32, srv_id:string, buy_time:uint32) |

## 命令 18026

- `CS_18026`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | type | uint8 |

- `SC_18026`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | item_bid | uint32 |
  | type | uint8 |
  | notice_list | table(item_bid:uint32) |

## 命令 18100

- `CS_18100` — 无字段（空消息）
- `SC_18100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ys_list | table(ys_type:uint8, ys_lev:uint8, ys_ceng:int8) |
  | cur_type | uint8 |
  | left_time | uint32 |
  | state | uint8 |

## 命令 18101

- `CS_18101`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ys_type | uint8 |

- `SC_18101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | ys_type | uint8 |

## 命令 18102

- `CS_18102` — 无字段（空消息）
- `SC_18102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18103

- `CS_18103` — 无字段（空消息）
- `SC_18103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18200

- `CS_18200` — 无字段（空消息）
- `SC_18200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |

## 命令 18201

- `CS_18201` — 无字段（空消息）
- `SC_18201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | max_gate | uint8 |

## 命令 18300

- `CS_18300` — 无字段（空消息）
- `SC_18300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18301

- `CS_18301` — 无字段（空消息）
- `SC_18301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | self_state | uint8 |
  | spouse_state | uint8 |
  | boyname | string |
  | grilname | string |
  | obj_rid | uint32 |
  | obj_srv | string |

## 命令 18302

- `CS_18302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ret | uint8 |

- `SC_18302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18303

- `CS_18303` — 无字段（空消息）
- `SC_18303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | self_state | uint8 |
  | spouse_state | uint8 |
  | msg | string |

## 命令 18304

- `CS_18304`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_18304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18305

- `CS_18305` — 无字段（空消息）
- `SC_18305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18306

- `CS_18306` — 无字段（空消息）
- `SC_18306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18307

- `CS_18307` — 无字段（空消息）
- `SC_18307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | a_name | string |
  | b_name | string |
  | type | uint8 |
  | rest_time | uint32 |
  | status | uint8 |
  | end_time | uint32 |

## 命令 18308

- `CS_18308` — 无字段（空消息）
- `SC_18308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | main_state | uint8 |

## 命令 18309

- `CS_18309` — 无字段（空消息）
- `SC_18309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | state | uint8 |

## 命令 18310

- `CS_18310`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_18310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18311

- `CS_18311`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | content | string |

- `SC_18311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |

## 命令 18312

- `CS_18312` — 无字段（空消息）
- `SC_18312`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | content_list | table(role_name:string, content:string) |

## 命令 18313

- `CS_18313` — 无字段（空消息）
- `SC_18313`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | ret | uint8 |

## 命令 18314

- `CS_18314`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_18314`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18315

- `CS_18315` — 无字段（空消息）
- `SC_18315`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 18316

- `CS_18316`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ret | uint8 |

- `SC_18316`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18317

- `CS_18317` — 无字段（空消息）
- `SC_18317`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | name | string |

## 命令 18318

- `CS_18318` — 无字段（空消息）
- `SC_18318`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | state | uint8 |
  | spouse_name | string |

## 命令 18319

- `CS_18319` — 无字段（空消息）
- `SC_18319`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | qifen | uint32 |
  | total_qifen | uint32 |
  | rest_time | uint32 |
  | exp | uint32 |
  | coin | uint32 |
  | use_list | table(type:uint8, use_times:uint8) |

## 命令 18320

- `CS_18320` — 无字段（空消息）
- `SC_18320`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(role_name:string, qifen:uint32, rank:uint8) |

## 命令 18321

- `CS_18321` — 无字段（空消息）
- `SC_18321`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18322

- `CS_18322`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | skill_id | uint32 |

- `SC_18322`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | new_skill_id | uint32 |

## 命令 18400

- `CS_18400` — 无字段（空消息）
- `SC_18400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | is_open | uint8 |
  | merge_index | uint8 |
  | step | uint8 |
  | status | uint8 |
  | val | uint16 |
  | tar_val | uint16 |

## 命令 18401

- `CS_18401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | step | uint8 |

- `SC_18401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | step | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 18402

- `CS_18402` — 无字段（空消息）
- `SC_18402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | step_list | table(step:uint8, srv_list:D|Dsc18402srv_list|) |

## 命令 18403

- `CS_18403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | step | uint8 |

- `SC_18403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | step | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 18404

- `CS_18404` — 无字段（空消息）
- `SC_18404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rewarded_list | table(step:uint8) |

## 命令 18500

- `CS_18500` — 无字段（空消息）
- `SC_18500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18501

- `CS_18501` — 无字段（空消息）
- `SC_18501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18502

- `CS_18502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

- `SC_18502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |
  | map_bid | uint32 |
  | x | uint32 |
  | y | uint32 |

## 命令 18503

- `CS_18503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_bid | uint32 |

- `SC_18503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18504

- `SC_18504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | mission_bid | uint32 |

## 命令 18505

- `CS_18505`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_18505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18600

- `CS_18600` — 无字段（空消息）
- `SC_18600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | map_state | uint8 |
  | status | uint8 |

## 命令 18601

- `CS_18601` — 无字段（空消息）
- `SC_18601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | map_state | uint8 |

## 命令 18602

- `CS_18602`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | map_index | uint8 |

- `SC_18602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18603

- `CS_18603` — 无字段（空消息）
- `SC_18603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18604

- `CS_18604` — 无字段（空消息）
- `SC_18604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | self_camp | uint8 |
  | camp_a_score | uint32 |
  | camp_a_num | uint8 |
  | camp_b_score | uint32 |
  | camp_b_num | uint8 |
  | add_score | uint32 |
  | score | uint32 |
  | base_score | uint32 |

## 命令 18605

- `CS_18605` — 无字段（空消息）
- `SC_18605`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | role_list | table(rid:uint32, srv_id:string, name:string, score:uint32) |

## 命令 18606

- `CS_18606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | num | int16 |

- `SC_18606`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | add_score | uint32 |
  | score | uint32 |
  | base_score | uint32 |

## 命令 18607

- `CS_18607`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | int32 |
  | srv_id | string |

- `SC_18607`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18608

- `CS_18608` — 无字段（空消息）
- `SC_18608`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | msg | string |
  | bat_res | uint8 |
  | win_score | int32 |
  | new_score | uint32 |
  | base_score | uint32 |

## 命令 18609

- `CS_18609` — 无字段（空消息）
- `SC_18609`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | camp_a_score | uint32 |
  | camp_a_num | uint8 |
  | camp_b_score | uint32 |
  | camp_b_num | uint8 |
  | add_score | uint32 |
  | self_camp | uint8 |
  | role_list | table(rid:uint32, srv_id:string, name:string, camp:uint8, add_score:uint32) |

## 命令 18610

- `CS_18610`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mod_id | uint32 |

- `SC_18610`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18611

- `CS_18611` — 无字段（空消息）
- `SC_18611`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | score | uint32 |

## 命令 18612

- `CS_18612` — 无字段（空消息）
- `SC_18612`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | camp_a_score | uint32 |
  | camp_a_num | uint8 |
  | camp_b_score | uint32 |
  | camp_b_num | uint8 |

## 命令 18613

- `CS_18613` — 无字段（空消息）
- `SC_18613`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | sec | uint32 |

## 命令 18614

- `CS_18614` — 无字段（空消息）
- `SC_18614`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | self_camp | uint8 |

## 命令 18700

- `CS_18700`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_18700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | select_type | uint8 |
  | info_list | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc18700hero_pos_info|, member_pos_info:D|Dsc18700member_pos_info|, partner_pos_info:D|Dsc18700partner_pos_info|) |

## 命令 18701

- `CS_18701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_id | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_18701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc18701hero_pos_info|, member_pos_info:D|Dsc18701member_pos_info|, partner_pos_info:D|Dsc18701partner_pos_info|) |

## 命令 18702

- `CS_18702`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | pos | uint8 |
  | hero_id | uint32 |
  | rid | uint32 |
  | srv_id | string |

- `SC_18702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc18702hero_pos_info|, member_pos_info:D|Dsc18702member_pos_info|, partner_pos_info:D|Dsc18702partner_pos_info|) |

## 命令 18703

- `CS_18703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |

- `SC_18703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | s_type | uint8 |

## 命令 18706

- `CS_18706`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | hero_id | uint32 |
  | pos | uint8 |

- `SC_18706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | cheer_hero | table(hero_id:uint32, pos:uint8) |

## 命令 18707

- `CS_18707`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | hero_id | uint32 |

- `SC_18707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | cheer_hero | table(hero_bid:uint32, pos:uint8) |

## 命令 18708

- `CS_18708`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | type | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | hero_id | uint32 |

- `SC_18708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint16 |
  | msg | string |
  | flag | uint8 |
  | pos_info | table(type:uint8, f_lev:uint8, hero_pos_info:D|Dsc18708hero_pos_info|, member_pos_info:D|Dsc18708member_pos_info|, partner_pos_info:D|Dsc18708partner_pos_info|) |

## 命令 18709

- `CS_18709`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id | uint32 |

- `SC_18709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |

## 命令 18710

- `CS_18710` — 无字段（空消息）
- `SC_18710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |
  | refresh_times | uint8 |
  | partner_list | table(hero_bid:uint32, partner_id:uint32, lev:uint8, power:uint32, rid:uint32, srv_id:string, color:uint8, rebirth:uint8, role_name:string) |

## 命令 18711

- `CS_18711` — 无字段（空消息）
- `SC_18711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |

## 命令 18712

- `CS_18712`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | partner_id | uint32 |

- `SC_18712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |

## 命令 18713

- `CS_18713`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | partner_id | uint32 |

- `SC_18713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |
  | rid | uint32 |
  | srv_id | string |
  | role_list | table(partner_list:D|Dsc18713partner_list|, eqm_list:D|Dsc18713eqm_list|) |

## 命令 18714

- `CS_18714` — 无字段（空消息）
- `SC_18714`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | partner_list | table(id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, grow:uint16, score:uint32, stage:uint8, rebirth:uint8, acc:uint8, partner_attr:D|Dsc18714partner_attr|, power:uint32, aptitude:D|Dsc18714aptitude|, innate_skill:uint32, skill:D|Dsc18714skill|, jindan_skill:D|Dsc18714jindan_skill|, talisman_skill:D|Dsc18714talisman_skill|, ext:D|Dsc18714ext|) |

## 命令 18715

- `CS_18715` — 无字段（空消息）
- `SC_18715`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | tips | string |
  | goods_index | uint16 |

## 命令 18716

- `CS_18716`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_18716`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | cheer_hero | table(hero_id:uint32, pos:uint8) |

## 命令 18730

- `CS_18730` — 无字段（空消息）
- `SC_18730`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | map_id | uint8 |
  | grid | uint8 |
  | record_list | table(name:string, msg:string) |
  | chip_num | uint16 |
  | change_list | table(id:uint8, use_num:uint8) |
  | run_times | uint8 |
  | next_time | uint32 |
  | list | table(buff_bid:uint32, act:uint32) |

## 命令 18731

- `CS_18731` — 无字段（空消息）
- `SC_18731`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | run_point | uint8 |
  | map_id | uint8 |
  | from_grid | uint8 |
  | to_grid | uint8 |
  | add_chip | uint8 |
  | chip_num | uint16 |
  | next_time | uint32 |
  | run_times | uint8 |

## 命令 18732

- `CS_18732`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | map_id | uint8 |
  | to_grid | uint8 |

- `SC_18732`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | rand_id | uint32 |

## 命令 18733

- `CS_18733`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

- `SC_18733`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | chip_num | uint16 |
  | id | uint8 |

## 命令 18734

- `SC_18734`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | run_times | uint16 |

## 命令 18735

- `CS_18735` — 无字段（空消息）
- `SC_18735`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(buff_bid:uint32, act:uint32) |

## 命令 18736

- `CS_18736`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | buff_bid | uint32 |

- `SC_18736`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | buff_bid | uint32 |

## 命令 18737

- `SC_18737`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | buff_bid | uint32 |

## 命令 18750

- `CS_18750` — 无字段（空消息）
- `SC_18750`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | boss_hp | uint32 |
  | status | uint8 |
  | boss_bid | uint32 |
  | max_hp | uint32 |
  | boss_time | uint32 |
  | role_time | uint32 |
  | info_list | table(type:uint8, msg:string) |
  | self_list | table(type:uint8, msg:string) |

## 命令 18751

- `CS_18751`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_18751`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | my_ord | uint16 |
  | carrer_rank | uint16 |
  | my_val | uint32 |
  | rank_list | table(ord:uint16, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, head_bid:uint32, gid:uint32, gsrv_id:string, gname:string, score:uint32) |

## 命令 18752

- `CS_18752`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_18752`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_guild | string |
  | gid | uint32 |
  | gsrv_id | string |
  | role_num | uint8 |
  | host_name | string |
  | rank_list | table(ord:uint8, name:string, gid:uint32, gsrv_id:string, gname:string, score:uint32, role_num:uint8) |

## 命令 18753

- `CS_18753` — 无字段（空消息）
- `SC_18753`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(index:uint8, name:string, rid:uint32, srv_id:string, career:uint8, sex:uint8, type:uint8, score:uint32, lev:uint8, save_time:uint32, hero_list:D|Dsc18753hero_list|) |

## 命令 18754

- `CS_18754` — 无字段（空消息）
- `SC_18754`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(type:uint8, msg:string) |

## 命令 18755

- `CS_18755` — 无字段（空消息）
- `SC_18755`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(type:uint8, msg:string) |

## 命令 18756

- `CS_18756`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_18756`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | protect_time | uint32 |
  | rid | uint32 |
  | srv_id | string |

## 命令 18757

- `SC_18757`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | full_hurt | uint32 |
  | my_hurt | uint32 |
  | hero_list | table(head_bid:uint32, hurt_val:uint32, hp:uint32) |
  | target_name | string |
  | target_rid | uint32 |
  | target_srv_id | string |
  | target_career | uint8 |
  | target_sex | uint8 |
  | target_hurt | uint32 |
  | target_hero_list | table(head_bid:uint32, hurt_val:uint32, hp:uint32) |
  | win_score | int32 |
  | msg | string |

## 命令 18758

- `CS_18758` — 无字段（空消息）
- `SC_18758`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18759

- `SC_18759`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | full_hurt | uint32 |
  | my_hurt | uint32 |
  | hero_list | table(head_bid:uint32, hurt_val:uint32, hp:uint32) |
  | win_score | int32 |
  | mon_hurt_list | table(mon_bid:uint32, is_boss:uint8, hurt_val:uint32, hp:uint32) |
  | msg | string |

## 命令 18760

- `CS_18760` — 无字段（空消息）
- `SC_18760`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | boss_hp | uint32 |
  | max_hp | uint32 |
  | status | uint8 |

## 命令 18761

- `SC_18761` — 无字段（空消息）
## 命令 18800

- `CS_18800` — 无字段（空消息）
- `SC_18800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hall_index | uint8 |

## 命令 18801

- `CS_18801` — 无字段（空消息）
- `SC_18801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18802

- `CS_18802`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_18802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | code | uint8 |
  | msg | string |
  | match_flag | uint8 |

## 命令 18803

- `CS_18803` — 无字段（空消息）
- `SC_18803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rest_time | uint8 |
  | win_times | uint16 |
  | total_times | uint16 |
  | score | uint32 |
  | win_reward_flag | uint8 |
  | time_reward_flag | uint8 |
  | rank | uint32 |
  | end_time | uint32 |
  | match_flag | uint8 |
  | daily_times | uint16 |
  | up_bat_list | table(index:uint8, score:int32) |
  | peak_index | uint16 |
  | cont_win_times | uint16 |
  | max_score | uint32 |

## 命令 18804

- `CS_18804` — 无字段（空消息）
- `SC_18804`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | role_list | table(rid:uint32, srv_id:string, role_name:string, career:uint8, sex:uint8, lev:uint8, power:uint32, score:uint32) |

## 命令 18805

- `SC_18805`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bat_result | uint8 |
  | reward_box_bid | uint32 |
  | is_up_suc | uint8 |
  | up_bat_list | table(index:uint8, score:int32) |
  | battle_role | table(name:string, lev:uint8, sex:uint8, career:uint8, score:uint32, win_score:int32, win_point:int32, bat_result:uint8) |
  | role_hurl_list | table(rid:uint32, srv_id:string, name:string, group:uint8, lev:uint16, sex:uint8, career:uint16, hp_max:uint32, hp:uint32, hurt:uint32, master_rid:uint32, master_srv_id:string, id:uint32) |

## 命令 18806

- `CS_18806`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | career | uint8 |

- `SC_18806`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | career | uint8 |
  | role_list | table(rank:uint16, rid:uint32, srv_id:string, role_name:string, career:uint8, sex:uint8, lev:uint8, power:uint32, score:uint32) |

## 命令 18807

- `CS_18807` — 无字段（空消息）
- `SC_18807`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | score | uint32 |
  | hall_index | uint8 |
  | match_flag | uint8 |
  | daily_times | uint16 |
  | hall_list | table(index:uint8, number:uint32) |

## 命令 18808

- `CS_18808` — 无字段（空消息）
- `SC_18808`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | score | uint32 |
  | reward_list | table(index:uint8, flag:uint8) |

## 命令 18809

- `CS_18809` — 无字段（空消息）
- `SC_18809`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | battle_record | table(msg:string, self:uint8) |

## 命令 18810

- `SC_18810`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | battle_record | table(msg:string, self:uint8) |

## 命令 18811

- `CS_18811` — 无字段（空消息）
- `SC_18811`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18812

- `CS_18812` — 无字段（空消息）
- `SC_18812`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18813

- `CS_18813`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | hall_index | uint8 |

- `SC_18813`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hall_index | uint8 |

## 命令 18814

- `CS_18814`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | grade | uint8 |

- `SC_18814`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | reward_list | table(index:uint8, flag:uint8) |

## 命令 18815

- `CS_18815`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_18815`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | win_times | uint16 |
  | total_times | uint16 |
  | score | uint32 |

## 命令 18820

- `CS_18820` — 无字段（空消息）
- `SC_18820`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18821

- `CS_18821` — 无字段（空消息）
- `SC_18821`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18823

- `SC_18823`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dungeon_bid | uint32 |
  | index | uint8 |
  | type | uint8 |
  | mon_list | table(mon_bid:uint32, finish_num:uint8, total:uint8) |
  | rest_time | uint32 |
  | reward_flag | uint8 |

## 命令 18826

- `CS_18826` — 无字段（空消息）
- `SC_18826`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | floor | uint8 |
  | rest_time | uint32 |
  | kill_number | uint16 |
  | win_coin | uint32 |
  | rest_wave | uint8 |

## 命令 18827

- `CS_18827` — 无字段（空消息）
- `SC_18827`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | table(bid:uint32, rid:uint32, srv_id:string, name:string) |

## 命令 18828

- `CS_18828`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dun_bid | uint32 |

- `SC_18828`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | career | uint8 |
  | sex | uint8 |
  | lev | uint8 |
  | power | uint32 |
  | disagree | uint16 |
  | animate_res | table(ant_id:uint16, ant_val:string, ent_lev:uint8, dis_method:uint8) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc18828attrs_ext|, attrs_ext_list:D|Dsc18828attrs_ext_list|, attrs_ext_one_list:D|Dsc18828attrs_ext_one_list|, jewel_list:D|Dsc18828jewel_list|, str_ext_list:D|Dsc18828str_ext_list|) |
  | team_member | table(member_name:string) |
  | floor | uint8 |
  | use_sec | uint32 |
  | my_floor | uint8 |
  | my_use_sec | uint32 |
  | my_count | uint8 |
  | leader_name | string |
  | my_team_member | table(member_name:string) |

## 命令 18829

- `CS_18829`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | dun_bid | uint32 |

- `SC_18829`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | dun_bid | uint32 |
  | disagree | uint16 |
  | my_count | uint8 |

## 命令 18833

- `SC_18833`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dungeon_bid | uint32 |
  | index | uint8 |
  | type | uint8 |
  | mon_list | table(mon_bid:uint32, finish_num:uint8, total:uint8) |
  | rest_time | uint32 |
  | reward_flag | uint8 |

## 命令 18861

- `CS_18861`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_cross | uint8 |

- `SC_18861`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18862

- `CS_18862`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_cross | uint8 |

- `SC_18862`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 18863

- `CS_18863`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_cross | uint8 |
  | rid | uint32 |
  | string | string |

- `SC_18863`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | string | string |

## 命令 18864

- `CS_18864`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_cross | uint8 |

- `SC_18864`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | floor | uint8 |
  | score | uint32 |
  | dan_score | uint32 |
  | end_time | uint32 |
  | reward_flag | uint8 |

## 命令 18865

- `CS_18865`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_cross | uint8 |
  | career | uint8 |
  | ord | uint8 |
  | num | uint8 |

- `SC_18865`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | ord | uint8 |
  | num | uint8 |
  | rank | uint16 |
  | total_score | uint32 |
  | score | uint32 |
  | dan_score | uint32 |
  | max_floor | uint8 |
  | rank_list | table(rank:uint16, rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, total_score:uint32, score:uint32, dan_score:uint32, max_floor:uint8) |

## 命令 18866

- `SC_18866`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | score | uint32 |

## 命令 18867

- `SC_18867`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | title_bid | uint32 |

## 命令 18868

- `CS_18868` — 无字段（空消息）
- `SC_18868`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | reward_flag | uint8 |

## 命令 18886

- `CS_18886`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_18886`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | role_name | string |
  | career | uint8 |
  | sex | uint8 |
  | win_times | uint16 |
  | total_times | uint16 |
  | score | uint32 |
  | index | uint16 |
  | end_time | uint32 |
  | cont_win_times | uint16 |
  | best_friend | string |
  | max_score | uint32 |
  | kill_num | uint16 |

## 命令 18900

- `CS_18900` — 无字段（空消息）
- `SC_18900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | coin_times | uint16 |
  | power | uint16 |
  | fabao_list | table(id:uint32, bid:uint32, level:uint16, exp:uint16, stage:uint8, skill_list:D|Dsc18900skill_list|, pos:uint16, effect_level:uint16) |

## 命令 18901

- `CS_18901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_18901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 18902

- `CS_18902`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_18902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 18903

- `CS_18903`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_18903`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 18904

- `CS_18904`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | stage | uint8 |

- `SC_18904`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 18905

- `CS_18905`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_18905`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | msg | string |

## 命令 18906

- `CS_18906`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | type | uint8 |
  | value | uint16 |

- `SC_18906`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | bid | uint32 |
  | pre_level | uint16 |
  | post_level | uint16 |
  | msg | string |

## 命令 18907

- `SC_18907`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | coin_times | uint16 |
  | power | uint16 |
  | fabao_list | table(id:uint32, bid:uint32, level:uint16, exp:uint16, stage:uint8, skill_list:D|Dsc18907skill_list|, pos:uint16, effect_level:uint16) |

## 命令 18908

- `CS_18908`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |
  | count | uint16 |

- `SC_18908`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | item_bid | uint32 |
  | msg | string |

## 命令 18909

- `CS_18909` — 无字段（空消息）
- `SC_18909`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | buy_list | table(id:uint16, buy_num:uint16) |

## 命令 18910

- `CS_18910`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | count | uint16 |

- `SC_18910`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | id | uint32 |
  | count | uint16 |
  | msg | string |

## 命令 18911

- `CS_18911`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_18911`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | power | uint32 |
  | fabao_list | table(id:uint32, bid:uint32, level:uint16, exp:uint16, stage:uint8, skill_list:D|Dsc18911skill_list|, pos:uint16, effect_level:uint16) |

## 命令 19000

- `CS_19000` — 无字段（空消息）
- `SC_19000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | box_list | table(id:uint32, bid:uint32, grid:uint32, dtime:uint32, flag:uint8, from:uint8) |

## 命令 19001

- `CS_19001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | from | uint8 |

- `SC_19001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | from | uint8 |
  | box_list | table(id:uint32, bid:uint32, grid:uint32, dtime:uint32, flag:uint8, from:uint8) |

## 命令 19002

- `CS_19002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_19002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | dtime | uint32 |

## 命令 19003

- `CS_19003`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_19003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 19004

- `SC_19004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | box_list | table(id:uint32, bid:uint32, grid:uint32, dtime:uint32, flag:uint8, from:uint8) |

## 命令 19005

- `CS_19005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |

- `SC_19005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |

## 命令 19100

- `CS_19100` — 无字段（空消息）
- `SC_19100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc19100attrs_ext|, attrs_ext_list:D|Dsc19100attrs_ext_list|, attrs_ext_one_list:D|Dsc19100attrs_ext_one_list|, jewel_list:D|Dsc19100jewel_list|, str_ext_list:D|Dsc19100str_ext_list|) |
  | looks | table(id:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 19101

- `CS_19101` — 无字段（空消息）
- `SC_19101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | stage | uint8 |

## 命令 19102

- `CS_19102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | args | uint32 |

- `SC_19102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | type | uint8 |
  | args | uint32 |

## 命令 19103

- `CS_19103`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_19103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19104

- `CS_19104`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_19104`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19108

- `CS_19108`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id_lev | uint32 |
  | item_id_list | table(item_id:uint32) |

- `SC_19108`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19120

- `CS_19120`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_19120`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 19199

- `CS_19199`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | look_id | uint32 |

- `SC_19199`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | look_id | uint32 |

## 命令 19200

- `CS_19200` — 无字段（空消息）
- `SC_19200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | current_pos | uint8 |
  | total_steps | uint32 |
  | step_box | table(box_id:uint32, is_received:uint32) |
  | already_roll_count | uint32 |
  | remain_free_count | uint8 |
  | events | table(event_bid:uint32) |

## 命令 19201

- `CS_19201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |
  | args | uint8 |

- `SC_19201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | step_info | table(step:uint8, event_bid:uint32) |

## 命令 19202

- `CS_19202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | step_bid | uint8 |

- `SC_19202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |

## 命令 19400

- `CS_19400`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bagcode | uint8 |

- `SC_19400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_stage | uint8 |
  | mingge_list | table(id:uint32, bid:uint32, bind:uint8, lev:uint8, gongming_lev:uint8, quantity:uint8, pos:uint16, hero_bid:uint32, ctime:uint32, effect_list:D|Dsc19400effect_list|, gongming_holes:uint8, gongming_bid_list:D|Dsc19400gongming_bid_list|, attr_ext:D|Dsc19400attr_ext|) |

## 命令 19401

- `SC_19401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_list | table(id:uint32, bid:uint32, bind:uint8, lev:uint8, gongming_lev:uint8, quantity:uint8, pos:uint16, hero_bid:uint32, ctime:uint32, effect_list:D|Dsc19401effect_list|, gongming_holes:uint8, gongming_bid_list:D|Dsc19401gongming_bid_list|, attr_ext:D|Dsc19401attr_ext|) |

## 命令 19402

- `CS_19402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | src_bag_code | uint8 |
  | mingge_id | uint32 |
  | id | uint32 |
  | pos | uint8 |

- `SC_19402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | src_bag_code | uint8 |
  | target_bag_code | uint8 |
  | mingge_id | uint32 |
  | id | uint32 |
  | pos | uint8 |

## 命令 19403

- `CS_19403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | src_bag_code | uint8 |
  | mingge_id | uint32 |

- `SC_19403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | src_bag_code | uint8 |
  | target_bag_code | uint8 |
  | mingge_id | uint32 |

## 命令 19404

- `CS_19404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | del_ids_arr | table(item_id:uint32) |

- `SC_19404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | del_ids_arr | table(item_id:uint32) |

## 命令 19405

- `CS_19405`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_id | uint32 |

- `SC_19405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | mingge_id | uint32 |

## 命令 19406

- `CS_19406` — 无字段（空消息）
- `SC_19406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | soul | uint16 |
  | soul_max | uint16 |
  | coin_type | uint8 |
  | price | uint32 |
  | is_tick | uint8 |

## 命令 19407

- `CS_19407` — 无字段（空消息）
- `SC_19407`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | val | uint16 |

## 命令 19408

- `CS_19408`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | is_tick | uint8 |

- `SC_19408`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | is_tick | uint8 |

## 命令 19409

- `CS_19409` — 无字段（空消息）
- `SC_19409`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | mingge_stage | uint8 |

## 命令 19410

- `CS_19410`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_id | uint32 |
  | hole | uint8 |

- `SC_19410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | mingge_id | uint32 |
  | hole | uint8 |
  | mingge_bid | uint32 |

## 命令 19411

- `CS_19411`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_id | uint32 |

- `SC_19411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | mingge_id | uint32 |

## 命令 19412

- `CS_19412`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | ids | table(item_id:uint32) |

- `SC_19412`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | mingge_id | uint32 |

## 命令 19413

- `CS_19413`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | mingge_id | uint32 |

- `SC_19413`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | mingge_id | uint32 |

## 命令 19414

- `CS_19414`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_19414`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | mingge_stage | uint8 |
  | role_mingge_list | table(id:uint32, bid:uint32, bind:uint8, lev:uint8, gongming_lev:uint8, quantity:uint8, pos:uint16, hero_bid:uint32, ctime:uint32, effect_list:D|Dsc19414effect_list|, gongming_holes:uint8, gongming_bid_list:D|Dsc19414gongming_bid_list|, attr_ext:D|Dsc19414attr_ext|) |
  | partner_list | table(id:uint32, bid:uint32, acc:uint8, lev:uint8, color:uint8, stage:uint8, rebirth:uint8, mingge_list:D|Dsc19414mingge_list|) |

## 命令 19499

- `CS_19499`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id | uint32 |
  | pos | uint8 |
  | swap_partner_id | uint32 |
  | swap_pos | uint8 |

- `SC_19499`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | partner_id | uint32 |
  | pos | uint8 |
  | swap_partner_id | uint32 |
  | swap_pos | uint8 |
  | msg | string |

## 命令 19500

- `CS_19500` — 无字段（空消息）
- `SC_19500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19501

- `CS_19501` — 无字段（空消息）
- `SC_19501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19505

- `CS_19505` — 无字段（空消息）
- `SC_19505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19506

- `SC_19506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | member_list | table(rid:uint32, srv_id:string, name:string, is_leader:uint8, sex:uint8, career:uint8, power:uint32, second_name:string, sort:uint8, vote_num:uint8) |
  | end_time | uint32 |
  | member_len | uint8 |
  | vote_sort | uint8 |
  | vote_flag | uint8 |
  | is_finish | uint8 |
  | notice | string |

## 命令 19507

- `CS_19507`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | front_name | string |
  | end_name | string |

- `SC_19507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | front_name | string |
  | end_name | string |

## 命令 19508

- `SC_19508`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | front_name | string |
  | end_name | string |
  | end_time | uint32 |

## 命令 19509

- `CS_19509`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | second_name | string |

- `SC_19509`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | second_name | string |

## 命令 19510

- `SC_19510`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | second_name | string |

## 命令 19511

- `SC_19511`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | flag | uint8 |
  | member_list | table(rid:uint32, srv_id:string, confirm:uint8) |
  | end_time | uint32 |

## 命令 19512

- `CS_19512`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_19512`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19513

- `SC_19513`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19514

- `CS_19514` — 无字段（空消息）
- `SC_19514`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jid | uint32 |
  | j_srv_id | string |
  | front_name | string |
  | member_len | uint8 |
  | end_name | string |
  | lev | uint8 |
  | leader_name | string |
  | exp | uint32 |
  | common_notice | string |
  | member_list | table(rid:uint32, srv_id:string, name:string, sort:uint8, sex:uint8, career:uint8, second_name:string, trophy:uint32, lev:uint8, jieyi:uint32, jieyi_total:uint32, is_online:uint8, offline_time:uint32) |
  | vote_type | uint8 |
  | vote_status | uint8 |
  | vote_end_time | uint32 |
  | host_rid | uint32 |
  | host_srv_id | string |
  | vote_host | string |
  | member_rid | uint32 |
  | member_srv_id | string |
  | vote_member | string |
  | vote_list | table(rid:uint32, srv_id:string, name:string, ret:uint8) |

## 命令 19515

- `CS_19515` — 无字段（空消息）
- `SC_19515`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | skill_list | table(skill_bid:uint32, lev:uint8) |

## 命令 19516

- `CS_19516`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint32 |

- `SC_19516`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | lev | uint8 |

## 命令 19517

- `CS_19517`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_19517`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 19518

- `CS_19518` — 无字段（空消息）
- `SC_19518`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19519

- `CS_19519`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | vote_sort | uint8 |
  | rid | uint32 |
  | srv_id | string |

- `SC_19519`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19520

- `SC_19520`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | vote_sort | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | vote_num | uint8 |

## 命令 19521

- `SC_19521`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | vote_type | uint8 |
  | vote_status | uint8 |
  | vote_end_time | uint32 |
  | host_rid | uint32 |
  | host_srv_id | string |
  | vote_host | string |
  | member_rid | uint32 |
  | member_srv_id | string |
  | vote_member | string |
  | vote_list | table(rid:uint32, srv_id:string, name:string, ret:uint8) |

## 命令 19522

- `CS_19522`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | vote_type | uint8 |
  | ret | uint8 |

- `SC_19522`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | vote_type | uint8 |
  | ret | uint8 |

## 命令 19523

- `CS_19523`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | front_name | string |
  | end_name | string |

- `SC_19523`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | front_name | string |
  | end_name | string |

## 命令 19524

- `CS_19524`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_19524`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rid | uint32 |
  | srv_id | string |

## 命令 19525

- `SC_19525`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | jid | uint32 |
  | j_srv_id | string |
  | vote_name | string |
  | front_name | string |
  | member_len | uint8 |
  | end_name | string |

## 命令 19526

- `CS_19526`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | jid | uint32 |
  | j_srv_id | string |
  | result | uint8 |

- `SC_19526`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19527

- `CS_19527`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | common_notice | string |

- `SC_19527`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | common_notice | string |

## 命令 19528

- `CS_19528`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | title_name | string |

- `SC_19528`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | title_name | string |

## 命令 19529

- `CS_19529` — 无字段（空消息）
- `SC_19529`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19530

- `CS_19530` — 无字段（空消息）
- `SC_19530`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | member_list | table(rid:uint32, srv_id:string, name:string, is_leader:uint8, sex:uint8, career:uint8, power:uint32, second_name:string, sort:uint8) |
  | end_time | uint32 |

## 命令 19531

- `SC_19531`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | member_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, ret:uint8) |
  | end_time | uint32 |

## 命令 19532

- `CS_19532`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ret | uint8 |

- `SC_19532`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19533

- `CS_19533` — 无字段（空消息）
- `SC_19533`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19534

- `CS_19534` — 无字段（空消息）
- `SC_19534`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | jid | uint32 |
  | j_srv_id | string |
  | front_name | string |
  | member_len | uint8 |
  | end_name | string |
  | lev | uint8 |
  | exp | uint32 |

## 命令 19535

- `SC_19535`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |

## 命令 19536

- `CS_19536` — 无字段（空消息）
- `SC_19536`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | jlev | uint8 |

## 命令 19537

- `CS_19537` — 无字段（空消息）
- `SC_19537`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19600

- `CS_19600`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_19600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | list | table(id:uint32, order:uint8, tot_time:uint8, day_time:uint8, status:uint8, reward_list:D|Dsc19600reward_list|, coin_type1:uint8, coin1:uint32) |

## 命令 19601

- `CS_19601`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | type | uint8 |
  | order | uint8 |

- `SC_19601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | type | uint8 |
  | order | uint8 |

## 命令 19602

- `SC_19602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | list | table(id:uint32, order:uint8, tot_time:uint8, day_time:uint8, status:uint8, reward_list:D|Dsc19602reward_list|, coin_type1:uint8, coin1:uint32) |

## 命令 19603

- `CS_19603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_19603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | coin_type1 | uint8 |
  | coin1 | uint32 |

## 命令 19604

- `CS_19604`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_19604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |

## 命令 19900

- `SC_19900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | state | uint8 |
  | question_id | uint32 |
  | end_time | uint32 |

## 命令 19901

- `CS_19901`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | question_id | uint32 |
  | answer | uint8 |

- `SC_19901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | msg | string |
  | right_answer | uint8 |

## 命令 19902

- `CS_19902` — 无字段（空消息）
- `SC_19902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | round | uint8 |
  | status | uint8 |
  | end_time | uint32 |
  | role_num | uint8 |
  | balloon_num | uint8 |
  | right_num | uint8 |
  | rank_list | table(role_id:uint32, srv_id:string) |

## 命令 19903

- `CS_19903` — 无字段（空消息）
- `SC_19903`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19904

- `CS_19904` — 无字段（空消息）
- `SC_19904`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 19905

- `SC_19905`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20001

- `CS_20001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | int32 |
  | srv_id | string |

- `SC_20001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20002

- `CS_20002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mon_id | int32 |

- `SC_20002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20003

- `CS_20003` — 无字段（空消息）
- `SC_20003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20004

- `CS_20004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | int32 |
  | srv_id | string |
  | name | string |

- `SC_20004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | name | string |
  | rid | int32 |
  | srv_id | string |

## 命令 20005

- `CS_20005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | result | int8 |
  | rid | int32 |
  | srv_id | string |

## 命令 20008

- `CS_20008`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_20008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | int8 |
  | flag | uint8 |

## 命令 20009

- `CS_20009`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | skill_id | int32 |

- `SC_20009`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | skill_id | int32 |

## 命令 20010

- `CS_20010` — 无字段（空消息）
- `SC_20010`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | round | uint16 |
  | round_wave | uint16 |
  | wave_max | uint16 |
  | wave_no | uint16 |
  | atk_formation_type | uint8 |
  | atk_formation_lev | uint8 |
  | def_formation_type | uint8 |
  | def_formation_lev | uint8 |
  | is_observer | uint8 |
  | effect_id | string |
  | order_list | table(id:uint32) |
  | fighter_info_list | table(id:uint16, rid:uint32, srv_id:string, name:string, lev:uint16, sex:uint8, career:uint16, pos:uint8, group:uint8, hp_max:uint32, hp:uint32, anger:uint32, is_auto:uint8, animate_res:D|Dsc20010animate_res|, skills:D|Dsc20010skills|, specials:D|Dsc20010specials|) |

## 命令 20011

- `CS_20011` — 无字段（空消息）
## 命令 20012

- `SC_20012`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | round | uint16 |
  | skill_play | table(order:uint8, user_id:uint16, skill_id:uint32, father_id:uint32, father_skill_id:uint32, passive_skill_id:uint32, user_anger:uint16, talk:string, notice:string, magic_play:D|Dsc20012magic_play|, summon_play:D|Dsc20012summon_play|) |
  | cooldown | table(bid:uint32, last_use:uint16) |

## 命令 20013

- `SC_20013`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | round | uint16 |
  | round_wave | uint16 |
  | time | uint8 |
  | wave_no | uint8 |
  | magic_play | table(order:uint8, target_anger:uint16, target_id:uint16, source_id:uint16, hit:int8, hp_max:uint32, hp:uint32, is_target_die:uint8, target_talk:string, magic_list:D|Dsc20013magic_list|) |
  | summon_play | table(id:uint16, rid:uint32, srv_id:string, name:string, lev:uint16, sex:uint8, career:uint16, pos:uint8, group:uint8, hp_max:uint32, hp:uint32, anger:uint32, is_auto:uint8, animate_res:D|Dsc20013animate_res|, skills:D|Dsc20013skills|, specials:D|Dsc20013specials|) |
  | order_list | table(id:uint32) |

## 命令 20014

- `CS_20014` — 无字段（空消息）
## 命令 20015

- `SC_20015`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | fighter_list | table(id:uint16, rid:uint32, srv_id:string, name:string, lev:uint16, sex:uint8, career:uint16, pos:uint8, group:uint8, hp_max:uint32, hp:uint32, anger:uint32, is_auto:uint8, animate_res:D|Dsc20015animate_res|, skills:D|Dsc20015skills|, specials:D|Dsc20015specials|) |

## 命令 20016

- `CS_20016`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | int32 |
  | srv_id | string |

- `SC_20016`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20017

- `CS_20017` — 无字段（空消息）
- `SC_20017`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20020

- `SC_20020`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |

## 命令 20021

- `CS_20021` — 无字段（空消息）
## 命令 20022

- `SC_20022`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | icon_list | table(icon_id:uint32) |

## 命令 20023

- `SC_20023`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | result | uint8 |
  | role_hurl_list | table(rid:uint32, srv_id:string, name:string, group:uint8, lev:uint16, sex:uint8, career:uint16, hp_max:uint32, hp:uint32, hurt:uint32, master_rid:uint32, master_srv_id:string, id:uint32) |
  | val_list | table(key:uint8, val:uint32) |
  | msg | string |

## 命令 20025

- `CS_20025`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | string |
  | srv_id | string |

- `SC_20025`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20026

- `CS_20026`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | string |
  | srv_id | string |

- `SC_20026`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | size | int32 |

## 命令 20027

- `CS_20027` — 无字段（空消息）
- `SC_20027`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20028

- `CS_20028`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_20028`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | replay_list | table(id:string, combat_type:uint8, create_time:uint32, max_round:uint16, atk_rid:uint32, atk_srv_id:string, atk_name:string, dfd_rid:uint32, dfd_srv_id:string, dfd_name:string, is_lock:uint8) |

## 命令 20029

- `CS_20029`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | string |
  | lock | uint8 |

- `SC_20029`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | string |
  | lock | uint8 |

## 命令 20030

- `CS_20030` — 无字段（空消息）
- `SC_20030`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20100

- `CS_20100` — 无字段（空消息）
- `SC_20100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | power | table(code:uint8, val:uint32) |
  | promote | table(code:uint8, val:D|Dsc20100val|) |

## 命令 20200

- `CS_20200` — 无字段（空消息）
- `SC_20200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | search_times | uint8 |
  | rob_times | uint8 |
  | occupy_time | uint8 |
  | occupy_num | uint8 |
  | mine_list | table(index:uint8, mine_bid:uint32, type:uint8, color:uint8, pos_x:uint16, pos_y:uint16, mine_endtime:uint32, status:uint8, defend_succ_times:uint16, tot_defend_times:uint16, loss_list:D|Dsc20200loss_list|, gain_list:D|Dsc20200gain_list|) |
  | search_cost | uint32 |
  | hero_exp | uint32 |
  | search_assets | uint8 |

## 命令 20201

- `CS_20201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | type | uint8 |

- `SC_20201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | index | uint32 |
  | type | uint8 |

## 命令 20202

- `CS_20202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | op_type | uint8 |

- `SC_20202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20203

- `CS_20203`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |

- `SC_20203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | assets | uint8 |

## 命令 20204

- `CS_20204` — 无字段（空消息）
- `SC_20204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | search_times | uint8 |
  | rob_times | uint8 |
  | occupy_time | uint8 |
  | occupy_num | uint8 |
  | reward | table(challenge_id:uint8, rid:uint32, srv_id:string, role_name:string, role_lev:uint8, sex:uint8, career:uint8, mine_bid:uint32, type:uint8, color:uint8, pos_x:uint16, pos_y:uint16, flag:uint8, defend_succ_times:uint16, tot_defend_times:uint16, reward:D|Dsc20204reward|, formation:D|Dsc20204formation|, mine_type:uint8, index:uint8, mine_endtime:uint32, status:uint8, loss_list:D|Dsc20204loss_list|, gain_list:D|Dsc20204gain_list|, occupy_cnt:uint16) |
  | search_cost | uint32 |
  | hero_exp | uint32 |
  | search_assets | uint8 |

## 命令 20205

- `CS_20205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | challenge_id | uint8 |

- `SC_20205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20206

- `CS_20206` — 无字段（空消息）
- `SC_20206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20207

- `CS_20207`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |

- `SC_20207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | rob_record | table(rid:uint32, srv_id:string, name:string, rob_time:uint32, result:uint8, assets:uint8, cnt:uint32) |

## 命令 20208

- `SC_20208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | search_times | uint8 |
  | rob_times | uint8 |
  | occupy_time | uint8 |
  | occupy_num | uint8 |
  | mine_list | table(index:uint8, mine_bid:uint32, type:uint8, color:uint8, pos_x:uint16, pos_y:uint16, mine_endtime:uint32, status:uint8, defend_succ_times:uint16, tot_defined_times:uint16, loss_list:D|Dsc20208loss_list|, gain_list:D|Dsc20208gain_list|) |
  | search_cost | uint32 |
  | hero_exp | uint32 |
  | search_assets | uint8 |

## 命令 20209

- `SC_20209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | search_times | uint8 |
  | rob_times | uint8 |
  | occupy_time | uint8 |
  | occupy_num | uint8 |
  | challenge_id | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | role_name | string |
  | role_lev | uint8 |
  | sex | uint8 |
  | career | uint8 |
  | mine_bid | uint32 |
  | type | uint8 |
  | color | uint8 |
  | pos_x | uint16 |
  | pos_y | uint16 |
  | flag | uint8 |
  | defend_succ_times | uint16 |
  | tot_defend_times | uint16 |
  | reward | table(bid:uint32, cnt:uint32) |
  | formation | table(rid:uint32, srv_id:string, bid:uint32, partner_id:uint32, color:uint8, rebirth:uint8) |
  | mine_type | uint8 |
  | index | uint8 |
  | mine_endtime | uint32 |
  | status | uint8 |
  | loss_list | table(bid:uint32, cnt:uint32) |
  | gain_list | table(bid:uint32, cnt:uint32) |
  | occupy_cnt | uint16 |
  | search_cost | uint32 |
  | hero_exp | uint32 |
  | search_assets | uint8 |

## 命令 20210

- `SC_20210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | mine_bid | uint32 |
  | type | uint32 |
  | color | uint32 |
  | occupy_num | uint8 |
  | rest_num | uint8 |
  | reward | table(bid:uint32, cnt:uint32) |

## 命令 20211

- `CS_20211`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint8 |
  | partner_id | uint32 |

- `SC_20211`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20212

- `CS_20212`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | partner_id | uint32 |

- `SC_20212`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | hero_exp | uint32 |

## 命令 20300

- `CS_20300` — 无字段（空消息）
- `SC_20300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rob_times | uint8 |
  | occupy_num | uint8 |
  | max_scene | uint8 |
  | my_scene | table(index:uint8, scene_index:uint8) |
  | scene_index | uint8 |
  | mine_list | table(id:uint32, msrv_id:string, index:uint8, bid:uint32, quality:uint8, rid:uint32, srv_id:string, name:string, gname:string, val:uint32, end_time:uint32, rest_sec:uint32) |

## 命令 20301

- `CS_20301`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | msrv_id | string |

- `SC_20301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | type | uint8 |
  | id | uint32 |
  | msrv_id | string |
  | index | uint8 |
  | bid | uint8 |
  | quality | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | gname | string |
  | val | uint32 |
  | rob_val | uint32 |
  | end_time | uint32 |
  | lose_count | uint16 |
  | win_count | uint32 |
  | rest_sec | uint32 |
  | role_lev | uint8 |
  | sex | uint8 |
  | career | uint8 |
  | face_id | uint32 |
  | formation | table(bid:uint32, partner_id:uint32, color:uint8, rebirth:uint8) |

## 命令 20302

- `CS_20302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | msrv_id | string |

- `SC_20302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20303

- `CS_20303`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | msrv_id | string |

- `SC_20303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | assets_code | uint8 |

## 命令 20304

- `CS_20304` — 无字段（空消息）
- `SC_20304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rob_record | table(rid:uint32, srv_id:string, name:string, rob_time:uint32, guild_name:string, result:uint8, rob_val:uint32, rest_val:uint32, bid:uint16, quality:uint8) |

## 命令 20305

- `SC_20305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | msrv_id | string |
  | index | uint8 |
  | bid | uint8 |
  | quality | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | gname | string |
  | val | uint32 |
  | rob_val | uint32 |
  | end_time | uint32 |
  | lose_count | uint16 |
  | win_count | uint32 |
  | rest_sec | uint32 |
  | role_lev | uint8 |
  | sex | uint8 |
  | career | uint8 |
  | face_id | uint32 |
  | formation | table(bid:uint32, partner_id:uint32, color:uint8, rebirth:uint8) |

## 命令 20306

- `CS_20306`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | scene_index | uint8 |

- `SC_20306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | scene_index | uint8 |
  | mine_list | table(id:uint32, msrv_id:string, index:uint8, bid:uint32, quality:uint8, rid:uint32, srv_id:string, name:string, gname:string, val:uint32, end_time:uint32, rest_sec:uint32) |

## 命令 20307

- `CS_20307` — 无字段（空消息）
- `SC_20307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assets | table(assets_code:uint8, val:uint32) |

## 命令 20308

- `CS_20308`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | partner_id | uint32 |

- `SC_20308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | assets | table(assets_code:uint8, val:uint32) |

## 命令 20309

- `SC_20309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | id | uint32 |
  | msrv_id | string |
  | index | uint8 |
  | bid | uint8 |
  | quality | uint8 |
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | gname | string |
  | val | uint32 |
  | rob_val | uint32 |
  | end_time | uint32 |
  | is_save | uint8 |
  | rob_times | uint8 |
  | occupy_num | uint8 |

## 命令 20310

- `CS_20310`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | msrv_id | string |
  | type | uint8 |

- `SC_20310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint32 |
  | msrv_id | string |

## 命令 20311

- `CS_20311` — 无字段（空消息）
- `SC_20311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | rank_list | table(rank:uint8, gname:string, score:uint32, gid:uint32, gsrv_id:string) |

## 命令 20312

- `CS_20312` — 无字段（空消息）
- `SC_20312`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rob_times | uint8 |
  | occupy_num | uint8 |
  | my_scene | table(index:uint8, scene_index:uint8) |

## 命令 20313

- `CS_20313` — 无字段（空消息）
- `SC_20313`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assets_list | table(code:uint8, val:uint32) |
  | loss_list | table(code:uint8, val:uint32) |

## 命令 20314

- `CS_20314` — 无字段（空消息）
- `SC_20314`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_list | table(rid:uint32, srv_id:string, name:string, rob_time:uint32, guild_name:string, member_rid:uint32, member_srv_id:uint32, result:uint8, rob_val:uint32, rest_val:uint32, bid:uint16, quality:uint8) |

## 命令 20500

- `CS_20500` — 无字段（空消息）
- `SC_20500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | role_id | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint8 |
  | sex | uint8 |
  | career | uint8 |
  | intimacy | uint32 |

## 命令 20501

- `CS_20501` — 无字段（空消息）
- `SC_20501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | friend_list | table(role_id:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career:uint8, intimacy:uint32, bind:uint8, is_online:uint8) |

## 命令 20502

- `CS_20502` — 无字段（空消息）
- `SC_20502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | recruit_list | table(role_id:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career:uint8, intimacy:uint32, is_online:uint8) |

## 命令 20503

- `CS_20503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |

- `SC_20503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | role_id | uint32 |
  | srv_id | string |
  | name | string |
  | lev | uint8 |
  | sex | uint8 |
  | career | uint8 |
  | intimacy | uint32 |

## 命令 20504

- `CS_20504`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_20504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | mission_list | table(mission_id:uint32, status:uint8, val:uint32, tot_val:uint32, target:uint32, ext_list:D|Dsc20504ext_list|, item_list:D|Dsc20504item_list|) |

## 命令 20505

- `CS_20505`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | mission_id | uint32 |

- `SC_20505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | mission_id | uint32 |
  | status | uint8 |

## 命令 20506

- `SC_20506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |
  | role_bame | string |

## 命令 20507

- `CS_20507`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |
  | op | uint8 |

- `SC_20507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20508

- `CS_20508`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |

- `SC_20508`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20509

- `SC_20509`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |
  | role_bame | string |

## 命令 20510

- `CS_20510`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | role_id | uint32 |
  | srv_id | string |
  | op | uint8 |

- `SC_20510`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20700

- `CS_20700` — 无字段（空消息）
- `SC_20700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | round | uint8 |
  | time_start | uint32 |
  | time_end | uint32 |
  | lev_group | uint16 |
  | team_index | uint16 |
  | team_id | uint32 |
  | team_srv_id | string |
  | is_leader | uint8 |
  | leader_rid | uint32 |
  | leader_srv_id | string |
  | leader_name | string |
  | is_fight | uint8 |

## 命令 20701

- `CS_20701` — 无字段（空消息）
- `SC_20701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | index | uint16 |
  | flag | uint8 |
  | round | uint8 |
  | register_start | uint32 |
  | register_end | uint32 |
  | notice_start | uint32 |
  | notice_end | uint32 |
  | flag_list | table(flag:uint8, round_list:D|Dsc20701round_list|) |

## 命令 20702

- `CS_20702` — 无字段（空消息）
- `SC_20702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | win_count | uint16 |
  | fail_count | uint16 |
  | team_id | uint32 |
  | team_srv_id | string |
  | team_name | string |
  | team_power | uint32 |
  | rank | uint16 |
  | member_list | table(is_leader:uint8, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, animate_res:D|Dsc20702animate_res|) |

## 命令 20703

- `CS_20703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | start | uint16 |
  | len | uint16 |

- `SC_20703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | start | uint16 |
  | len | uint16 |
  | total_num | uint16 |
  | apply_list | table(rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, power:uint32) |

## 命令 20704

- `CS_20704`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_name | string |

- `SC_20704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_list | table(team_id:uint32, team_srv_id:string, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, max_lev:uint8, member_len:uint8, team_name:string, applyed:uint8, is_invited:uint8) |

## 命令 20705

- `CS_20705`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | type | uint8 |

- `SC_20705`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20706

- `CS_20706`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | start | uint16 |
  | len | uint16 |

- `SC_20706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | start | uint16 |
  | len | uint16 |
  | total_num | uint16 |
  | team_list | table(team_id:uint32, team_srv_id:string, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, max_lev:uint8, member_len:uint8, team_name:string, applyed:uint8, is_invited:uint8) |

## 命令 20707

- `CS_20707`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_name | string |

- `SC_20707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | team_name | string |

## 命令 20708

- `CS_20708`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |

- `SC_20708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | win_count | uint16 |
  | fail_count | uint16 |
  | team_name | string |
  | team_power | uint32 |
  | rank | uint16 |
  | member_list | table(is_leader:uint8, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, animate_res:D|Dsc20708animate_res|) |

## 命令 20709

- `CS_20709`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |

- `SC_20709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20710

- `CS_20710`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |

- `SC_20710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20711

- `CS_20711`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_20711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20712

- `CS_20712`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_20712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20713

- `CS_20713`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |
  | type | uint8 |

- `SC_20713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20714

- `CS_20714`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_20714`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20715

- `CS_20715` — 无字段（空消息）
- `SC_20715`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20716

- `CS_20716` — 无字段（空消息）
- `SC_20716`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20717

- `CS_20717` — 无字段（空消息）
- `SC_20717`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | round | uint8 |
  | start_time | uint32 |
  | end_time | uint32 |
  | team_name | string |
  | member_list | table(is_leader:uint8, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, animate_res:D|Dsc20717animate_res|) |
  | enemy_team_name | string |
  | enemy_member_list | table(is_leader:uint8, rid:uint32, srv_id:string, lev:uint8, career:uint8, sex:uint32, name:string, animate_res:D|Dsc20717animate_res|) |
  | next_start_time | uint32 |
  | fight_state | uint8 |

## 命令 20718

- `CS_20718`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |

- `SC_20718`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |
  | group_list | table(index:uint8, team_list:D|Dsc20718team_list|) |

## 命令 20719

- `CS_20719`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |
  | index | uint8 |

- `SC_20719`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |
  | index | uint8 |
  | is_win | uint8 |
  | team_list | table(sort_index:uint8, team_id:uint32, team_srv_id:string, team_name:string, win_round:D|Dsc20719win_round|) |

## 命令 20720

- `CS_20720`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |
  | index | uint8 |

- `SC_20720`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |
  | index | uint8 |
  | team_list | table(sort_index:uint8, team_id:uint32, team_srv_id:string, team_name:string, win_round:D|Dsc20720win_round|) |

## 命令 20721

- `CS_20721`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | lev_group | uint8 |

- `SC_20721`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |
  | round | uint8 |
  | lev_group | uint8 |
  | team_list | table(sort_index:uint8, team_id:uint32, team_srv_id:string, team_name:string, win_round:D|Dsc20721win_round|) |
  | team_list2 | table(sort_index:uint8, team_id:uint32, team_srv_id:string, team_name:string, win_round:D|Dsc20721win_round|) |

## 命令 20722

- `CS_20722` — 无字段（空消息）
- `SC_20722`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20723

- `CS_20723` — 无字段（空消息）
- `SC_20723`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20724

- `CS_20724` — 无字段（空消息）
- `SC_20724`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |
  | team_name | string |
  | state | uint8 |
  | team_id2 | uint32 |
  | team_srv_id2 | string |
  | team_name2 | string |
  | state2 | uint8 |
  | flag | uint8 |
  | round | uint8 |
  | status | uint8 |
  | end_time | uint32 |

## 命令 20725

- `CS_20725`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_20725`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | state | uint8 |

## 命令 20726

- `SC_20726`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | team_id | uint32 |
  | team_srv_id | string |
  | state | uint8 |

## 命令 20727

- `SC_20727`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | flag | uint8 |
  | round | uint8 |
  | score | uint8 |
  | total_hurt | uint32 |
  | role_list | table(is_leader:uint8, rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, lev:uint8, hurt_val:uint32) |
  | target_hurt | uint32 |
  | target_role_list | table(is_leader:uint8, rid:uint32, srv_id:string, name:string, career:uint8, sex:uint8, lev:uint8, hurt_val:uint32) |

## 命令 20728

- `SC_20728`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |

## 命令 20729

- `SC_20729` — 无字段（空消息）
## 命令 20799

- `CS_20799` — 无字段（空消息）
- `SC_20799`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | play | uint8 |
  | play_win | uint8 |
  | enemy_play_win | uint8 |
  | timeout | uint32 |

## 命令 20800

- `CS_20800` — 无字段（空消息）
- `SC_20800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc20800attrs_ext|, attrs_ext_list:D|Dsc20800attrs_ext_list|, attrs_ext_one_list:D|Dsc20800attrs_ext_one_list|, jewel_list:D|Dsc20800jewel_list|, str_ext_list:D|Dsc20800str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 20801

- `CS_20801` — 无字段（空消息）
- `SC_20801`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | stage | uint8 |

## 命令 20802

- `CS_20802`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |

- `SC_20802`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | stage | uint8 |

## 命令 20803

- `CS_20803`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_20803`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20804

- `CS_20804`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_20804`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20805

- `CS_20805`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_20805`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 20806

- `CS_20806`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_20806`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20807

- `CS_20807`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_20807`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20808

- `CS_20808`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id_lev | uint32 |
  | item_id_list | table(item_id:uint32) |

- `SC_20808`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 20809

- `CS_20809`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_20809`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | flag | uint8 |

## 命令 21301

- `CS_21301` — 无字段（空消息）
- `SC_21301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tower_id | uint32 |
  | floor | uint32 |
  | is_effect | uint32 |
  | clear_list | table(floor:uint32, first_clear_id:uint32, first_clear_srvid:string, first_clear_name:string, best_clear_id:uint32, best_clear_srvid:string, best_clear_name:string) |
  | is_clear | uint8 |
  | daily_floors | uint8 |

## 命令 21302

- `CS_21302` — 无字段（空消息）
- `SC_21302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21303

- `SC_21303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | tower_id | uint8 |
  | floor | uint8 |
  | BossList | table(boss_bid:uint32, kill_num:uint8, max_num:uint8) |

## 命令 21304

- `SC_21304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tower_id | uint8 |
  | floor | uint8 |
  | round | uint8 |
  | reward_list | table(bid:uint32, cnt:uint32) |
  | daily_floors | uint8 |

## 命令 21305

- `CS_21305`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_21305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bid | uint32 |
  | enter_count | uint16 |
  | buy_count | uint16 |

## 命令 21306

- `CS_21306` — 无字段（空消息）
- `SC_21306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(bid:uint32, enter_count:uint16, buy_count:uint16, time:uint32, is_finish:uint8) |

## 命令 21307

- `SC_21307`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | gain | table(type:uint8, count:uint32) |
  | items | table(item_bid:uint32, num:uint8, is_bind:uint8) |

## 命令 21308

- `CS_21308`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_21308`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | time | uint16 |

## 命令 21309

- `CS_21309`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_21309`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | bid | uint32 |

## 命令 21310

- `CS_21310` — 无字段（空消息）
- `SC_21310`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | one_key_sweep_list | table(bid:uint32) |

## 命令 21311

- `CS_21311`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_21311`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | one_key_sweep_list | table(bid:uint32) |

## 命令 21312

- `CS_21312` — 无字段（空消息）
- `SC_21312`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | one_key_sweep_list | table(bid:uint32) |

## 命令 21313

- `CS_21313`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |

- `SC_21313`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tips | uint8 |
  | msg | string |
  | one_key_sweep_list | table(bid:uint32) |

## 命令 21399

- `CS_21399`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | tower_id | uint32 |

- `SC_21399`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tower_id | uint32 |
  | clear_list | table(floor:uint32, first_clear_id:uint32, first_clear_srvid:string, first_clear_name:string, best_clear_id:uint32, best_clear_srvid:string, best_clear_name:string) |

## 命令 21400

- `CS_21400` — 无字段（空消息）
- `SC_21400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | role_eqm | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc21400attrs_ext|, attrs_ext_list:D|Dsc21400attrs_ext_list|, attrs_ext_one_list:D|Dsc21400attrs_ext_one_list|, jewel_list:D|Dsc21400jewel_list|, str_ext_list:D|Dsc21400str_ext_list|) |
  | partner_eqm | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc21400attrs_ext|, attrs_ext_list:D|Dsc21400attrs_ext_list|, attrs_ext_one_list:D|Dsc21400attrs_ext_one_list|, jewel_list:D|Dsc21400jewel_list|, str_ext_list:D|Dsc21400str_ext_list|) |
  | eqm_grid | uint8 |
  | dung_bid | uint32 |
  | floor | uint8 |

## 命令 21401

- `SC_21401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_grid | uint8 |

## 命令 21402

- `CS_21402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | eqm_pos | uint8 |
  | hero_id | uint32 |

- `SC_21402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_item_id | uint32 |
  | eqm_item_id | uint32 |
  | eqm_pos | uint8 |
  | hero_id | uint32 |

## 命令 21403

- `CS_21403`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

- `SC_21403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | eqm_item_id | uint32 |
  | bag_item_id | uint32 |
  | bag_pos | uint8 |
  | hero_bid | uint32 |

## 命令 21404

- `CS_21404`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | list | table(id:uint32) |

- `SC_21404`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | add_val | uint32 |
  | val | uint32 |
  | list | table(id:uint32) |

## 命令 21405

- `CS_21405`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rune_bid | uint32 |
  | num | uint16 |

- `SC_21405`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | id | uint16 |
  | num | uint16 |
  | price | uint32 |

## 命令 21406

- `CS_21406`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | bag_code | uint8 |
  | id | uint32 |

- `SC_21406`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | bag_code | uint8 |
  | id | uint16 |
  | new_lev | uint8 |

## 命令 21407

- `SC_21407`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | dung_bid | uint32 |
  | floor | uint8 |

## 命令 21410

- `CS_21410` — 无字段（空消息）
- `SC_21410`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | free_times | uint8 |
  | is_haft | uint8 |
  | free_end_time | uint32 |
  | rest_times | uint8 |
  | coin_count | uint8 |
  | record_server | table(name:string, bid:uint32, num:uint32) |
  | show_vip | uint8 |
  | gold_count | uint8 |

## 命令 21411

- `CS_21411`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | count_type | uint8 |
  | color | uint8 |

- `SC_21411`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | coin_count | uint8 |
  | rest_times | uint8 |
  | Items | table(bid:uint32, num:uint32, exchange:uint8) |

## 命令 21412

- `CS_21412` — 无字段（空消息）
- `SC_21412`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | free_times | uint8 |
  | is_haft | uint8 |
  | free_end_time | uint32 |

## 命令 21413

- `CS_21413` — 无字段（空消息）
- `SC_21413`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | record_server | table(name:string, bid:uint32, num:uint32) |

## 命令 21414

- `CS_21414`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_21414`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | role_eqm | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc21414attrs_ext|, attrs_ext_list:D|Dsc21414attrs_ext_list|, attrs_ext_one_list:D|Dsc21414attrs_ext_one_list|, jewel_list:D|Dsc21414jewel_list|, str_ext_list:D|Dsc21414str_ext_list|) |
  | role_power | uint32 |
  | eqm_grid | uint8 |
  | dung_bid | uint32 |
  | floor | uint8 |
  | partner_list | table(id:uint32, bid:uint32, acc:uint8, lev:uint8, color:uint8, stage:uint8, rebirth:uint8, partner_power:uint32, partner_eqm:D|Dsc21414partner_eqm|) |

## 命令 21600

- `CS_21600` — 无字段（空消息）
- `SC_21600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |
  | power | uint32 |
  | luck | uint16 |
  | res_stage | uint8 |
  | grow | uint16 |
  | skill_list | table(skill_bid:uint32) |
  | items | table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D|Dsc21600attrs_ext|, attrs_ext_list:D|Dsc21600attrs_ext_list|, attrs_ext_one_list:D|Dsc21600attrs_ext_one_list|, jewel_list:D|Dsc21600jewel_list|, str_ext_list:D|Dsc21600str_ext_list|) |
  | surface_list | table(surface_id:uint32, surface_time:uint32) |
  | surface_star | table(surface_id:uint32, star:uint16) |

## 命令 21601

- `CS_21601` — 无字段（空消息）
- `SC_21601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | stage | uint8 |

## 命令 21602

- `CS_21602`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | stage | uint8 |

- `SC_21602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | stage | uint8 |

## 命令 21603

- `CS_21603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_21603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21604

- `CS_21604`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id | uint32 |

- `SC_21604`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21605

- `CS_21605`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | surface_id | uint16 |

- `SC_21605`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | surface_id | uint16 |

## 命令 21606

- `CS_21606`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_21606`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21607

- `CS_21607`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_bid | uint32 |

- `SC_21607`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21608

- `CS_21608`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | item_id_lev | uint32 |
  | item_id_list | table(item_id:uint32) |

- `SC_21608`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 21609

- `CS_21609`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint8 |

- `SC_21609`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | flag | uint8 |

## 命令 30000

- `CS_30000`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_30000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30001

- `CS_30001` — 无字段（空消息）
- `SC_30001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | lanucher_name | string |
  | host_name | string |

## 命令 30101

- `CS_30101` — 无字段（空消息）
- `SC_30101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30102

- `CS_30102` — 无字段（空消息）
- `SC_30102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30103

- `CS_30103`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_30103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30104

- `CS_30104` — 无字段（空消息）
- `SC_30104`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | boss_bid | uint32 |
  | boss_hp | uint32 |
  | boss_hp_max | uint32 |

## 命令 30105

- `CS_30105`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |

- `SC_30105`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |
  | rank | uint16 |
  | hurt | uint32 |
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, hurt:uint32, index:uint16) |

## 命令 30106

- `SC_30106` — 无字段（空消息）
## 命令 30107

- `CS_30107`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |

- `SC_30107`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30108

- `CS_30108` — 无字段（空消息）
- `SC_30108`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | buff_num | uint8 |

## 命令 30109

- `CS_30109`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |

- `SC_30109`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |
  | rank | uint16 |
  | career_rank | uint16 |
  | hurt | uint32 |
  | role_list | table(rid:uint32, srv_id:string, name:string, guild:string, sex:uint8, career:uint8, hurt:uint32, index:uint16) |

## 命令 30200

- `CS_30200` — 无字段（空消息）
- `SC_30200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30201

- `CS_30201` — 无字段（空消息）
- `SC_30201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30202

- `CS_30202` — 无字段（空消息）
- `SC_30202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30203

- `CS_30203`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | type | uint8 |
  | val | uint32 |

- `SC_30203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30204

- `CS_30204` — 无字段（空消息）
- `SC_30204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num1 | uint8 |
  | num2 | uint8 |
  | num3 | uint8 |

## 命令 30205

- `CS_30205` — 无字段（空消息）
- `SC_30205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint32 |
  | hp | uint32 |
  | max_hp | uint32 |
  | wave | uint8 |
  | max_wave | uint8 |
  | mon_num | uint8 |

## 命令 30206

- `CS_30206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | idx | uint8 |
  | num | uint8 |

- `SC_30206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | idx | uint8 |
  | num | uint8 |
  | rank | uint16 |
  | score | uint32 |
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, score:uint32, index:uint16) |

## 命令 30207

- `CS_30207` — 无字段（空消息）
- `SC_30207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | item_list | table(item_bid:uint32, num:uint32) |

## 命令 30208

- `CS_30208` — 无字段（空消息）
- `SC_30208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30209

- `SC_30209`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | name | string |
  | sex | uint8 |
  | career | uint8 |
  | val | uint8 |
  | idx | uint8 |
  | flag | uint8 |

## 命令 30210

- `SC_30210`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | end_time | uint32 |
  | item_list | table(item_bid:uint32, num:uint32) |
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint8, idx:uint8) |

## 命令 30220

- `CS_30220` — 无字段（空消息）
- `SC_30220`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | wave | uint8 |
  | rank | uint16 |
  | score | uint32 |
  | item_list | table(item_bid:uint32, num:uint32) |
  | role_list | table(rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, score:uint32, index:uint16) |

## 命令 30300

- `CS_30300` — 无字段（空消息）
- `SC_30300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | assist | uint8 |
  | freight | table(status:uint8, start_time:uint32, help:uint8, cells:D|Dsc30300cells|) |

## 命令 30301

- `CS_30301`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_30301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | freight | table(status:uint8, start_time:uint32, help:uint8, cells:D|Dsc30301cells|) |

## 命令 30302

- `CS_30302`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

- `SC_30302`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 30303

- `CS_30303` — 无字段（空消息）
- `SC_30303`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30304

- `CS_30304`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |

- `SC_30304`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 30305

- `CS_30305`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | id | uint8 |

- `SC_30305`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |
  | id | uint8 |
  | code | uint8 |
  | msg | string |

## 命令 30306

- `CS_30306` — 无字段（空消息）
- `SC_30306`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint8 |

## 命令 30400

- `CS_30400` — 无字段（空消息）
- `SC_30400`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | current_pos | uint8 |
  | total_steps | uint32 |
  | step_box | table(box_id:uint32, is_received:uint32) |
  | already_roll_count | uint32 |
  | remain_free_count | uint8 |
  | events | table(event_bid:uint32) |

## 命令 30401

- `CS_30401`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | count | uint8 |
  | args | uint8 |

- `SC_30401`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | step_info | table(step:uint8, event_bid:uint32) |

## 命令 30402

- `CS_30402`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | step_bid | uint32 |

- `SC_30402`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |

## 命令 30403

- `CS_30403` — 无字段（空消息）
- `SC_30403`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30500

- `CS_30500` — 无字段（空消息）
- `SC_30500`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | current_day | int32 |
  | remain_time | uint32 |
  | growth_targets | table(day:uint8, login_reward_state:uint8, charge_reward_state:uint8, total_charge:uint32, targets:D|Dsc30500targets|, day_target_state:uint8, goods_state:uint8) |

## 命令 30501

- `CS_30501`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint8 |

- `SC_30501`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30502

- `CS_30502`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint8 |

- `SC_30502`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30503

- `CS_30503`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint8 |

- `SC_30503`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30504

- `CS_30504` — 无字段（空消息）
- `SC_30504`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint16 |
  | target_id | uint32 |
  | finished_value | uint32 |
  | total_value | uint32 |
  | target_state | uint8 |

## 命令 30505

- `CS_30505` — 无字段（空消息）
- `SC_30505`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint16 |
  | target_state | uint8 |

## 命令 30506

- `CS_30506`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | target_id | uint32 |

- `SC_30506`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | target_id | uint32 |
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30507

- `CS_30507`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint16 |

- `SC_30507`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | day | uint16 |
  | items | table(item_bid:uint32, num:uint32) |

## 命令 30600

- `CS_30600` — 无字段（空消息）
- `SC_30600`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | refresh_times | uint8 |
  | next_time | uint32 |
  | items | table(id:uint8, status:uint8) |

## 命令 30601

- `CS_30601` — 无字段（空消息）
- `SC_30601`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30602

- `CS_30602`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | Id | uint8 |
  | type | uint8 |

- `SC_30602`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | Id | uint8 |
  | msg | string |

## 命令 30603

- `CS_30603`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | items | table(item_bid:uint32, num:uint32) |

- `SC_30603`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30700

- `CS_30700` — 无字段（空消息）
- `SC_30700`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30701

- `CS_30701`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | idx | uint16 |
  | num | uint8 |

- `SC_30701`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | idx | uint16 |
  | num | uint8 |
  | all_num | uint16 |
  | guild_list | table(rank:uint16, gid:uint32, gsrv_id:string, gname:string, head_rid:uint32, head_srv_id:string, head_name:string, head_sex:uint8, head_career:uint8, head_face:uint32, head_surface:uint32, glev:uint8, num:uint8, group:uint8, power:uint32) |

## 命令 30702

- `CS_30702`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |

- `SC_30702`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | group | uint8 |
  | season_win | uint16 |
  | all_win | uint32 |
  | score | uint32 |
  | rank | uint16 |

## 命令 30703

- `CS_30703`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint8 |

- `SC_30703`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint8 |
  | start_time | uint32 |
  | count | uint32 |
  | season | uint32 |
  | guild_match_list | table(gid1:uint32, gsrv_id1:string, gname1:string, gid2:uint32, gsrv_id2:string, gname2:string, is_elimination:int8) |

## 命令 30704

- `CS_30704` — 无字段（空消息）
- `SC_30704`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | remain_relive_count | uint32 |

## 命令 30705

- `CS_30705` — 无字段（空消息）
- `SC_30705`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30706

- `CS_30706`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | rid | uint32 |
  | srv_id | string |

- `SC_30706`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 30707

- `CS_30707` — 无字段（空消息）
- `SC_30707`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint8 |
  | gid1 | uint32 |
  | gsrv_id1 | string |
  | gname1 | string |
  | gid2 | uint32 |
  | gsrv_id2 | string |
  | gname2 | string |
  | time | uint32 |
  | ret | uint8 |

## 命令 30708

- `CS_30708` — 无字段（空消息）
- `SC_30708`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | tower_list | table(id:uint32, n:uint8, camp:uint8, bid:uint32, hp:uint32, hp_max:uint32, active:uint8) |

## 命令 30709

- `CS_30709`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | idx | uint16 |
  | num | uint8 |

- `SC_30709`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | idx | uint16 |
  | num | uint8 |
  | all_num | uint16 |
  | role_list | table(rank:uint8, rid:uint32, srv_id:string, name:string, win:uint16, lose:uint16, tower_score:uint32, score:uint32) |

## 命令 30710

- `CS_30710`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint8 |
  | idx | uint16 |
  | num | uint8 |

- `SC_30710`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | group | uint8 |
  | idx | uint16 |
  | num | uint8 |
  | all_num | uint16 |
  | guild_list | table(rank:uint16, gid:uint32, gsrv_id:string, gname:string, head_rid:uint32, head_srv_id:string, head_name:string, head_sex:uint8, head_career:uint8, head_face:uint32, head_surface:uint32, glev:uint8, num:uint8, score:uint32, all_num:uint32, all_win:uint32, season_num:uint32, season_win:uint32) |

## 命令 30711

- `CS_30711` — 无字段（空消息）
- `SC_30711`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | relive_time | uint32 |
  | remain_relive_count | uint32 |

## 命令 30712

- `CS_30712` — 无字段（空消息）
- `SC_30712`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | gid | uint32 |
  | gsrv_id | string |
  | gname | string |
  | group | uint8 |
  | season_win | uint16 |
  | season_num | uint16 |
  | all_win | uint32 |
  | score | uint32 |
  | rank | uint16 |
  | sign_cond | uint8 |

## 命令 30713

- `CS_30713` — 无字段（空消息）
- `SC_30713`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | elem_id | uint32 |
  | cd_time | uint32 |
  | time | uint32 |
  | max_time | uint32 |
  | play_effect | uint8 |

## 命令 30714

- `CS_30714`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | elem_id | uint32 |

- `SC_30714` — 无字段（空消息）
## 命令 30715

- `CS_30715`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | elem_bid | uint32 |

- `SC_30715` — 无字段（空消息）
## 命令 30716

- `CS_30716` — 无字段（空消息）
- `SC_30716`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | start_time | table(start_time:uint32) |
  | elimination_match | table(id:int8, gid1:uint32, gsrv_id1:string, gname1:string) |
  | champion_id | int8 |

## 命令 30717

- `CS_30717` — 无字段（空消息）
- `SC_30717`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | guild_list | table(season:uint32, gid:uint32, gsrv_id:string, gname:string, head_rid:uint32, head_srv_id:string, head_name:string, power:uint32) |

## 命令 30800

- `CS_30800`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | reward_wave | uint16 |

- `SC_30800`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | max_passed | uint16 |
  | msg | string |

## 命令 30900

- `CS_30900` — 无字段（空消息）
- `SC_30900`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | value | uint32 |

## 命令 30901

- `CS_30901` — 无字段（空消息）
- `SC_30901`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |

## 命令 30902

- `CS_30902`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | day | uint8 |

- `SC_30902`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | result | uint8 |
  | msg | string |
  | double | uint8 |
  | day | uint8 |
  | item_lists | table(item_id:uint32, num:uint32) |

## 命令 31000

- `CS_31000` — 无字段（空消息）
- `SC_31000`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | is_open | uint8 |
  | copy_infos | table(copy_id:uint32, star:uint8, state:uint8, need_guild_lev:uint16) |
  | boss_infos | table(boss_id:uint32, current_hp:uint32, max_hp:uint32) |
  | first_target | uint32 |
  | command_id | uint32 |
  | boss_buff | uint32 |
  | remain_seconds | uint32 |
  | copy_id | uint32 |
  | attack_remain_count | uint32 |
  | attack_total_count | uint32 |

## 命令 31001

- `CS_31001`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | copy_id | uint32 |

- `SC_31001`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 31002

- `CS_31002`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | boss_id | uint32 |

- `SC_31002`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | boss_id | uint32 |

## 命令 31003

- `CS_31003`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | command_id | uint32 |

- `SC_31003`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | command_id | uint32 |

## 命令 31004

- `CS_31004`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | boss_id | uint32 |

- `SC_31004`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 31005

- `CS_31005`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | boss_id | uint32 |

- `SC_31005`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |
  | boss_id | uint32 |

## 命令 31006

- `CS_31006`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |

- `SC_31006`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | career | uint8 |
  | idx | uint8 |
  | num | uint8 |
  | rank | uint16 |
  | hurt | uint32 |
  | name | string |
  | my_lev | uint16 |
  | role_list | table(rid:uint32, srv_id:string, name:string, hurt:uint32, index:uint16, lev:uint16) |

## 命令 31007

- `CS_31007` — 无字段（空消息）
- `SC_31007`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | can_fight | uint8 |

## 命令 31008

- `CS_31008` — 无字段（空消息）
- `SC_31008`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | copy_id | uint32 |

## 命令 31100

- `CS_31100` — 无字段（空消息）
- `SC_31100`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | point | uint16 |
  | insight_skill | table(bid:uint32, lev:uint8) |

## 命令 31101

- `CS_31101`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | insight_bid | uint32 |

- `SC_31101`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | insight_bid | uint32 |
  | msg | string |

## 命令 31102

- `CS_31102`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | insight_bid | uint32 |

- `SC_31102`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | point | uint16 |
  | insight_bid | uint32 |
  | lev | uint8 |

## 命令 31103

- `CS_31103` — 无字段（空消息）
- `SC_31103`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 31104

- `CS_31104` — 无字段（空消息）
- `SC_31104`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | point | uint16 |

## 命令 31200

- `CS_31200`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31200`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, lev:uint8, career:uint8, sex:uint8, head_bid:uint32, val:uint32) |

## 命令 31201

- `CS_31201`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31201`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_hero_bid | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, val:uint32, hero_bid:uint32, grow:uint32) |

## 命令 31202

- `CS_31202`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31202`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_stage | uint8 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, stage:uint8, val:uint32) |

## 命令 31203

- `CS_31203`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31203`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, lev:uint8, career:uint8, sex:uint8, head_bid:uint32, val:uint32) |

## 命令 31204

- `CS_31204`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31204`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_lev | uint32 |
  | my_power | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, lev:uint32, val:uint32) |

## 命令 31205

- `CS_31205`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31205`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, lev:uint8, sex:uint8, career:uint8, val:uint32) |

## 命令 31206

- `CS_31206`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31206`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | my_hero_bid | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, val:uint32, hero_bid:uint32, grow:uint32) |

## 命令 31207

- `CS_31207`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31207`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint8, val:uint32) |

## 命令 31208

- `CS_31208`（cs）

  | 字段 | 类型 |
  |---|---|---|
  | ord | uint8 |
  | num | uint8 |
  | flag | uint8 |

- `SC_31208`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | my_ord | uint8 |
  | my_val | uint32 |
  | rank_list | table(ord:uint8, rid:uint32, srv_id:string, name:string, sex:uint8, career:uint16, val:uint32, flyup_lev:uint32) |

## 命令 31300

- `SC_31300`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | reward_id | uint8 |
  | reward_list | table(id:uint8, bid:uint32, num:uint32) |

## 命令 31301

- `CS_31301` — 无字段（空消息）
- `SC_31301`（sc）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint8 |
  | msg | string |

## 命令 cells

- `Dsc30300cells`（?）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | id | uint8 |

- `Dsc30301cells`（?）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | id | uint8 |

## 命令 items

- `Dsc10540items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc10800items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | quantity | uint32 |
  | bid | uint8 |

- `Dsc11237items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc11238items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc11242items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc12971items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc13053items`（?）

  | 字段 | 类型 |
  |---|---|---|
  | is_bind | uint32 |
  | num | uint8 |
  | item_bid | uint8 |

## 命令 list2

- `Dcs10299list2`（?）

  | 字段 | 类型 |
  |---|---|---|
  | vv1 | uint8 |

- `Dsc10299list2`（?）

  | 字段 | 类型 |
  |---|---|---|
  | vv1 | uint8 |

## 命令 skill

- `Dsc10401skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint8 |
  | color1 | uint32 |

- `Dsc11200skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11215skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11221skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11224skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12601skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12972skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12974skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18713skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18714skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

## 命令 assets

- `Dsc10561assets`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc10800assets`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |
  | label | uint32 |

## 命令 effect

- `Dsc10301effect`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc10911effect`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc10913effect`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint16 |

## 命令 member

- `Dsc10201member`（?）

  | 字段 | 类型 |
  |---|---|---|
  | animate_res | uint8 |
  | lev | uint8 |
  | name | string |
  | career | uint8 |
  | sex | struct<Dsc10201animate_res> |

## 命令 reward

- `Dsc20204reward`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

## 命令 skills

- `Dsc20010skills`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cd | uint32 |
  | last_use | uint8 |
  | step | uint16 |
  | bid | uint16 |

- `Dsc20012skills`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cd | uint32 |
  | last_use | uint8 |
  | step | uint16 |
  | bid | uint16 |

- `Dsc20013skills`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cd | uint32 |
  | last_use | uint8 |
  | step | uint16 |
  | bid | uint16 |

- `Dsc20015skills`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cd | uint32 |
  | last_use | uint8 |
  | step | uint16 |
  | bid | uint16 |

## 命令 hongbao

- `Dsc13519hongbao`（?）

  | 字段 | 类型 |
  |---|---|---|
  | hongbao_id | uint16 |

- `Dsc13542hongbao`（?）

  | 字段 | 类型 |
  |---|---|---|
  | hongbao_id | uint16 |

## 命令 pitfall

- `Dsc11000pitfall`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

## 命令 rewards

- `Dsc13600rewards`（?）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint32 |
  | item_bid | uint32 |

## 命令 targets

- `Dsc30500targets`（?）

  | 字段 | 类型 |
  |---|---|---|
  | target_state | uint32 |
  | total_value | uint32 |
  | finished_value | uint32 |
  | target_id | uint8 |

## 命令 ShowList

- `Dsc10592ShowList`（?）

  | 字段 | 类型 |
  |---|---|---|
  | is_effect | uint32 |
  | item_cnt | uint32 |
  | item_bid | uint8 |

## 命令 aim_list

- `Dsc16620aim_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | int_args | uint32 |
  | item_list | string |
  | status | uint8 |
  | aim_str | struct<Dsc16620item_list> |
  | aim | struct<Dsc16620int_args> |

## 命令 aptitude

- `Dsc11200aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc11215aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc11221aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc11224aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc12972aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc12974aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc18713aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

- `Dsc18714aptitude`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val_max | uint32 |
  | val | uint32 |
  | code | uint32 |

## 命令 attr_ext

- `Dsc19400attr_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | attr_ext_id | uint32 |

- `Dsc19401attr_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | attr_ext_id | uint32 |

- `Dsc19414attr_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | attr_ext_id | uint32 |

## 命令 eqm_list

- `Dsc12972eqm_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc12974eqm_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

- `Dsc18713eqm_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

## 命令 ext_list

- `Dsc12413ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | ext_value | uint32 |
  | ext_id | uint32 |

- `Dsc20504ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | ext_value | uint32 |
  | ext_id | uint32 |

## 命令 int_args

- `Dsc10922int_args`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint16 |

- `Dsc10924int_args`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint16 |

- `Dsc16603int_args`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc16620int_args`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint16 |

## 命令 misc_str

- `Dsc10201misc_str` — 无字段（空消息）
- `Dsc10202misc_str` — 无字段（空消息）
## 命令 mon_list

- `Dsc11000mon_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | id | uint32 |
  | bid | uint32 |

## 命令 msg_list

- `Dsc12722msg_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tick | uint8 |
  | msg | string |

## 命令 specials

- `Dsc20010specials`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc20012specials`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc20013specials`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc20015specials`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

## 命令 srv_list

- `Dsc18402srv_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | role_list | string |
  | can_reward | uint16 |
  | status | uint16 |
  | tar_val | uint8 |
  | val | uint8 |
  | srv_id | struct<Dsc18402role_list> |

## 命令 attr_list

- `Dsc11010attr_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint16 |

- `Dsc12208attr_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | code | uint16 |

## 命令 attrs_ext

- `Dsc10500attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10502attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10526attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10540attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10543attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10948attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10949attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10950attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10954attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10955attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10957attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc10958attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11221attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11224attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11237attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11238attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11240attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc11242attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc12971attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc12972attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc12974attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc13802attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc13807attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc15501attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc15801attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc18713attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc18828attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc19100attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc20800attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc21400attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc21414attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

- `Dsc21600attrs_ext`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |
  | attr_code | uint32 |

## 命令 buff_bids

- `Dsc10201buff_bids`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `Dsc10202buff_bids`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

## 命令 formation

- `Dsc20204formation`（?）

  | 字段 | 类型 |
  |---|---|---|
  | rebirth | uint32 |
  | color | string |
  | partner_id | uint32 |
  | bid | uint32 |
  | srv_id | uint8 |
  | rid | uint8 |

## 命令 gain_list

- `Dsc20200gain_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc20204gain_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc20208gain_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

## 命令 hero_list

- `Dsc10733hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint16 |

- `Dsc11000hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `Dsc11010hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_list | uint32 |
  | attr_list | uint8 |
  | state | uint8 |
  | loyalty | uint8 |
  | morale | uint16 |
  | star_lev | uint8 |
  | color | uint8 |
  | lev | struct<Dsc11010attr_list> |
  | bid | struct<Dsc11010skill_list> |

- `Dsc11017hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `Dsc11018hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `Dsc18753hero_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | lev | uint32 |
  | hero_bid | uint8 |

## 命令 item_list

- `Dsc16603item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint32 |
  | bid | uint32 |

- `Dsc16614item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint32 |
  | bid | uint32 |

- `Dsc16620item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint32 |
  | bid | uint32 |

- `Dsc16626item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | item_bid | uint32 |

- `Dsc16630item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | item_cnt | uint32 |
  | item_bid | uint32 |

- `Dsc16635item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | item_cnt | uint32 |
  | item_bid | uint32 |

- `Dsc16697item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | num | uint16 |
  | bid | uint32 |

- `Dsc20504item_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | item_bid | uint32 |

## 命令 loss_list

- `Dsc20200loss_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc20204loss_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc20208loss_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

## 命令 nice_list

- `Dsc13341nice_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | role_name | uint32 |
  | srv_id | string |
  | rid | string |

- `Dsc13342nice_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | role_name | uint32 |
  | srv_id | string |
  | rid | string |

- `Dsc13356nice_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | role_name | uint32 |
  | srv_id | string |
  | rid | string |

## 命令 rank_list

- `Dsc16620rank_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |
  | lev | string |
  | career | string |
  | sex | uint8 |
  | name | uint8 |
  | srv_id | uint8 |
  | rid | uint32 |

## 命令 rank_role

- `Dsc12901rank_role`（?）

  | 字段 | 类型 |
  |---|---|---|
  | power_fabao | uint32 |
  | power_wing | uint32 |
  | power_shenqi | uint32 |
  | power_lingshou | uint32 |
  | power_ride | uint32 |
  | power_hero | uint32 |
  | power_xiulian | uint32 |
  | power_skill | uint32 |
  | power_eqm_role | uint32 |

## 命令 role_list

- `Dsc12766role_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | chat_bubble | uint32 |
  | head_bid | string |
  | capacity | string |
  | vip_lev | uint8 |
  | career | uint8 |
  | sex | uint16 |
  | lev | uint8 |
  | name | uint8 |
  | srv_id | uint32 |
  | rid | uint32 |

- `Dsc17513role_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | vip_lev | uint32 |
  | career | string |
  | sex | string |
  | lev | uint8 |
  | name | uint8 |
  | srv_id | uint16 |
  | rid | uint8 |

- `Dsc18402role_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | name | uint32 |
  | srv_id | string |
  | rid | string |

## 命令 rune_list

- `Dsc11237rune_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | items | uint32 |
  | status | uint32 |
  | rune_index | struct<Dsc11237items> |

- `Dsc11238rune_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | items | uint32 |
  | status | uint32 |
  | rune_index | struct<Dsc11238items> |

- `Dsc11242rune_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | items | uint32 |
  | status | uint32 |
  | rune_index | struct<Dsc11242items> |

## 命令 team_list

- `Dsc20718team_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | team_power | uint32 |
  | score | string |
  | total_couont | string |
  | win_count | string |
  | leader_name | uint32 |
  | team_name | uint32 |
  | team_srv_id | uint32 |
  | team_id | uint32 |

## 命令 win_round

- `Dsc20719win_round`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | round | uint8 |

- `Dsc20720win_round`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | round | uint8 |

- `Dsc20721win_round`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bat_res | uint8 |
  | round | uint8 |

## 命令 event_list

- `Dsc13574event_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |
  | code | uint8 |

## 命令 fabao_list

- `Dsc12932fabao_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | effect_level | uint32 |
  | skill_list | uint32 |
  | stage | uint16 |
  | level | uint8 |
  | power | struct<Dsc12932skill_list> |
  | bid | uint16 |

## 命令 help_digit

- `Dsc13519help_digit`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

- `Dsc13542help_digit`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint8 |

## 命令 jewel_list

- `Dsc10500jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10502jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10526jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10540jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10948jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10949jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10950jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10954jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10955jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10957jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc10958jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11221jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11224jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11237jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11238jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11240jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc11242jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc12971jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc12972jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc12974jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc13802jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc13807jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc15501jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc15801jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc18713jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc18828jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc19100jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc20800jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc21400jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc21414jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

- `Dsc21600jewel_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | bid | uint32 |

## 命令 level_star

- `Dsc12005level_star`（?）

  | 字段 | 类型 |
  |---|---|---|
  | star | uint32 |
  | level_id | uint8 |

## 命令 magic_list

- `Dsc20012magic_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | fold | uint16 |

- `Dsc20013magic_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | fold | uint16 |

## 命令 magic_play

- `Dsc20012magic_play`（?）

  | 字段 | 类型 |
  |---|---|---|
  | magic_list | uint8 |
  | target_talk | uint16 |
  | is_target_die | uint16 |
  | hp | uint16 |
  | hp_max | int8 |
  | hit | uint32 |
  | source_id | uint32 |
  | target_id | uint8 |
  | target_anger | string |
  | order | struct<Dsc20012magic_list> |

## 命令 misc_uint8

- `Dsc10201misc_uint8` — 无字段（空消息）
- `Dsc10202misc_uint8` — 无字段（空消息）
## 命令 round_list

- `Dsc20701round_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | fight_state | uint8 |
  | time_end | uint32 |
  | time_start | uint32 |
  | round | uint8 |

## 命令 skill_list

- `Dsc10544skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | bid | uint16 |

- `Dsc11010skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |
  | color | uint32 |

- `Dsc11403skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_state | uint8 |

- `Dsc12208skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |
  | color | uint32 |

- `Dsc12932skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | yinyang | uint16 |
  | stage | uint8 |

- `Dsc18900skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | yinyang | uint16 |
  | stage | uint8 |

- `Dsc18907skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | yinyang | uint16 |
  | stage | uint8 |

- `Dsc18911skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | yinyang | uint16 |
  | stage | uint8 |

## 命令 animate_res

- `Dsc10201animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc10202animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc10230animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc10239animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc15601animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20010animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20012animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20013animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20015animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20702animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20708animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

- `Dsc20717animate_res`（?）

  | 字段 | 类型 |
  |---|---|---|
  | dis_method | uint16 |
  | ent_lev | string |
  | ant_val | uint8 |
  | ant_id | uint8 |

## 命令 attack_list

- `Dsc17406attack_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | is_success | uint8 |
  | b_r_lev | string |
  | b_r_name | uint8 |
  | star | uint8 |

## 命令 effect_list

- `Dsc19400effect_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | effect_id | uint16 |

- `Dsc19401effect_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | effect_id | uint16 |

- `Dsc19414effect_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | effect_id | uint16 |

## 命令 member_list

- `Dsc13035member_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | guild_name | uint32 |
  | sex | string |
  | career | string |
  | lev | uint16 |
  | name | uint16 |
  | srv_id | uint8 |
  | rid | string |

- `Dsc13096member_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | guild_name | uint32 |
  | sex | string |
  | career | string |
  | lev | uint16 |
  | name | uint16 |
  | srv_id | uint8 |
  | rid | string |

## 命令 mingge_list

- `Dsc19414mingge_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_ext | uint32 |
  | gongming_bid_list | uint32 |
  | gongming_holes | uint8 |
  | effect_list | uint8 |
  | ctime | uint8 |
  | hero_bid | uint8 |
  | pos | uint16 |
  | quantity | uint32 |
  | gongming_lev | uint32 |
  | lev | struct<Dsc19414effect_list> |
  | bind | uint8 |
  | bid | struct<Dsc19414gongming_bid_list> |
  | id | struct<Dsc19414attr_ext> |

## 命令 misc_uint16

- `Dsc10201misc_uint16` — 无字段（空消息）
- `Dsc10202misc_uint16` — 无字段（空消息）
## 命令 misc_uint32

- `Dsc10201misc_uint32` — 无字段（空消息）
- `Dsc10202misc_uint32` — 无字段（空消息）
## 命令 partner_eqm

- `Dsc21414partner_eqm`（?）

  | 字段 | 类型 |
  |---|---|---|
  | str_ext_list | uint16 |

## 命令 reward_list

- `Dsc16646reward_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc16648reward_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc19600reward_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

- `Dsc19602reward_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | cnt | uint32 |
  | bid | uint32 |

## 命令 summon_play

- `Dsc20012summon_play`（?）

  | 字段 | 类型 |
  |---|---|---|
  | specials | uint16 |
  | skills | uint32 |
  | animate_res | string |
  | is_auto | string |
  | anger | uint16 |
  | hp | uint8 |
  | hp_max | uint16 |
  | group | uint8 |
  | pos | uint8 |
  | career | uint32 |
  | sex | uint32 |
  | lev | uint32 |
  | name | uint8 |
  | srv_id | struct<Dsc20012animate_res> |
  | rid | struct<Dsc20012skills> |
  | id | struct<Dsc20012specials> |

## 命令 team_member

- `Dsc12980team_member`（?）

  | 字段 | 类型 |
  |---|---|---|
  | head_bid | uint8 |
  | lev | uint32 |
  | career | string |
  | sex | string |
  | name | uint8 |
  | srv_id | uint8 |
  | rid | uint8 |
  | leader | uint32 |

## 命令 comment_list

- `Dsc13341comment_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | comment | uint32 |
  | to_name | uint32 |
  | to_srv_id | string |
  | to_rid | string |
  | name | uint8 |
  | srv_id | uint32 |
  | rid | string |
  | ctime | string |

- `Dsc13342comment_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | comment | uint32 |
  | to_name | uint32 |
  | to_srv_id | string |
  | to_rid | string |
  | name | uint8 |
  | srv_id | uint32 |
  | rid | string |
  | ctime | string |

- `Dsc13356comment_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | comment | uint32 |
  | to_name | uint32 |
  | to_srv_id | string |
  | to_rid | string |
  | name | uint8 |
  | srv_id | uint32 |
  | rid | string |
  | ctime | string |

## 命令 jindan_skill

- `Dsc11200jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11215jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11221jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11224jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12972jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12974jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18713jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18714jindan_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

## 命令 mission_list

- `Dsc16626mission_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | flag | uint32 |
  | mission_bid | uint8 |

## 命令 partner_attr

- `Dsc11200partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc11215partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc11221partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc11224partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc12972partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc12974partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc18713partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

- `Dsc18714partner_attr`（?）

  | 字段 | 类型 |
  |---|---|---|
  | tenacity_rate_show | uint32 |
  | crit_rate_show | uint32 |
  | dodge_rate_show | uint32 |
  | hit_rate_show | uint32 |
  | tenacity | uint32 |
  | crit | uint32 |
  | dodge | uint32 |
  | hit | uint32 |
  | atk_speed | uint32 |
  | hp_max | uint32 |
  | def_p | uint32 |
  | def_s | uint32 |
  | atk_p | uint32 |
  | atk_s | uint32 |

## 命令 partner_list

- `Dsc11300partner_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | rebirth | uint32 |
  | color | string |
  | partner_id | uint32 |
  | bid | uint32 |
  | srv_id | uint8 |
  | rid | uint8 |

- `Dsc12972partner_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | ext | uint16 |

- `Dsc12973partner_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | rebirth | uint32 |
  | color | string |
  | partner_id | uint32 |
  | bid | uint32 |
  | srv_id | uint8 |
  | rid | uint8 |

- `Dsc12974partner_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | ext | uint16 |

- `Dsc18713partner_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | ext | uint16 |

## 命令 show_partner

- `Dsc12901show_partner`（?）

  | 字段 | 类型 |
  |---|---|---|
  | rebirth | uint32 |
  | color | uint32 |

## 命令 str_ext_list

- `Dsc10500str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10502str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10526str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10540str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10948str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10949str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10950str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10954str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10955str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10957str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc10958str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11221str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11224str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11237str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11238str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11240str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc11242str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc12971str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc12972str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc12974str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc13802str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc13807str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc15501str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc15801str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc18713str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc18828str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc19100str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc20800str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc21400str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc21414str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

- `Dsc21600str_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_str | uint8 |
  | id | string |

## 命令 attr_one_list

- `Dsc10500attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10502attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10526attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10540attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10948attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10949attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10950attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10954attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10955attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10957attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc10958attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11221attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11224attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11237attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11238attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11240attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc11242attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc12971attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc12972attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc12974attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc13802attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc13807attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc15501attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc15801attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc18713attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc18828attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc19100attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc20800attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc21400attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc21414attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

- `Dsc21600attr_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_val | uint16 |

## 命令 hero_bid_list

- `Dsc10735hero_bid_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | hero_bid | uint16 |

## 命令 hero_pos_info

- `Dsc13100hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc13101hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc13102hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc13103hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc13250hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_color | uint32 |
  | hero_bid | uint8 |
  | hero_id | uint8 |

- `Dsc13251hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_color | uint32 |
  | hero_bid | uint8 |
  | hero_id | uint8 |

- `Dsc13254hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_color | uint32 |
  | hero_bid | uint8 |
  | hero_id | uint8 |

- `Dsc14000hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14001hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14002hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14008hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14020hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14021hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14022hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc14028hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_bid | uint8 |

- `Dsc18700hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_id | uint8 |

- `Dsc18701hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_id | uint8 |

- `Dsc18702hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_id | uint8 |

- `Dsc18708hero_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | pos | uint32 |
  | hero_id | uint8 |

## 命令 my_skill_list

- `Dsc12932my_skill_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | my_yinyang | uint16 |
  | my_stage | uint8 |

## 命令 attrs_ext_list

- `Dsc10500attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10500attr> |

- `Dsc10502attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10502attr> |

- `Dsc10526attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10526attr> |

- `Dsc10540attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10540attr> |

- `Dsc10948attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10948attr> |

- `Dsc10949attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10949attr> |

- `Dsc10950attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10950attr> |

- `Dsc10954attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10954attr> |

- `Dsc10955attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10955attr> |

- `Dsc10957attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10957attr> |

- `Dsc10958attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc10958attr> |

- `Dsc11221attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11221attr> |

- `Dsc11224attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11224attr> |

- `Dsc11237attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11237attr> |

- `Dsc11238attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11238attr> |

- `Dsc11240attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11240attr> |

- `Dsc11242attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc11242attr> |

- `Dsc12971attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc12971attr> |

- `Dsc12972attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc12972attr> |

- `Dsc12974attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc12974attr> |

- `Dsc13802attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc13802attr> |

- `Dsc13807attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc13807attr> |

- `Dsc15501attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc15501attr> |

- `Dsc15801attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc15801attr> |

- `Dsc18713attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc18713attr> |

- `Dsc18828attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc18828attr> |

- `Dsc19100attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc19100attr> |

- `Dsc20800attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc20800attr> |

- `Dsc21400attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc21400attr> |

- `Dsc21414attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc21414attr> |

- `Dsc21600attrs_ext_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr | uint8 |
  | id | struct<Dsc21600attr> |

## 命令 garden_partner

- `Dsc11500garden_partner`（?）

  | 字段 | 类型 |
  |---|---|---|
  | val | uint32 |
  | time_out | uint8 |
  | state | uint32 |
  | partner_id | uint32 |

## 命令 talisman_skill

- `Dsc11200talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11215talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11221talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc11224talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12972talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc12974talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18713talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

- `Dsc18714talisman_skill`（?）

  | 字段 | 类型 |
  |---|---|---|
  | skill_bid | uint16 |

## 命令 member_pos_info

- `Dsc13250member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint8 |

- `Dsc13251member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint8 |

- `Dsc13254member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint8 |

- `Dsc14000member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14001member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14002member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14008member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14020member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14021member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14022member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc14028member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc18700member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc18701member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc18702member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

- `Dsc18708member_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | sex | uint32 |
  | pos | string |
  | career | uint16 |
  | member_srv_id | uint8 |
  | member_id | uint16 |

## 命令 item_effect_list

- `Dsc16620item_effect_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | effect_2 | uint32 |
  | effect_1 | uint8 |
  | bid | uint8 |

## 命令 partner_pos_info

- `Dsc18700partner_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | uint32 |
  | rid | uint8 |
  | pos | uint32 |
  | hero_id | string |

- `Dsc18701partner_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | uint32 |
  | rid | uint8 |
  | pos | uint32 |
  | hero_id | string |

- `Dsc18702partner_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | uint32 |
  | rid | uint8 |
  | pos | uint32 |
  | hero_id | string |

- `Dsc18708partner_pos_info`（?）

  | 字段 | 类型 |
  |---|---|---|
  | srv_id | uint32 |
  | rid | uint8 |
  | pos | uint32 |
  | hero_id | string |

## 命令 primus_role_list

- `Dsc15601primus_role_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | animate_res | uint32 |
  | power | string |
  | guild_name | string |
  | lev | uint16 |
  | sex | uint8 |
  | career | uint16 |
  | name | string |
  | srv_id | uint32 |
  | rid | struct<Dsc15601animate_res> |

## 命令 gongming_bid_list

- `Dsc19400gongming_bid_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | mingge_bid | uint32 |
  | hole | uint32 |

- `Dsc19401gongming_bid_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | mingge_bid | uint32 |
  | hole | uint32 |

- `Dsc19414gongming_bid_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | status | uint8 |
  | mingge_bid | uint32 |
  | hole | uint32 |

## 命令 attrs_ext_one_list

- `Dsc10500attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10500attr_one_list> |

- `Dsc10502attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10502attr_one_list> |

- `Dsc10526attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10526attr_one_list> |

- `Dsc10540attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10540attr_one_list> |

- `Dsc10948attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10948attr_one_list> |

- `Dsc10949attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10949attr_one_list> |

- `Dsc10950attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10950attr_one_list> |

- `Dsc10954attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10954attr_one_list> |

- `Dsc10955attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10955attr_one_list> |

- `Dsc10957attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10957attr_one_list> |

- `Dsc10958attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc10958attr_one_list> |

- `Dsc11221attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11221attr_one_list> |

- `Dsc11224attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11224attr_one_list> |

- `Dsc11237attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11237attr_one_list> |

- `Dsc11238attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11238attr_one_list> |

- `Dsc11240attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11240attr_one_list> |

- `Dsc11242attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc11242attr_one_list> |

- `Dsc12971attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc12971attr_one_list> |

- `Dsc12972attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc12972attr_one_list> |

- `Dsc12974attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc12974attr_one_list> |

- `Dsc13802attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc13802attr_one_list> |

- `Dsc13807attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc13807attr_one_list> |

- `Dsc15501attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc15501attr_one_list> |

- `Dsc15801attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc15801attr_one_list> |

- `Dsc18713attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc18713attr_one_list> |

- `Dsc18828attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc18828attr_one_list> |

- `Dsc19100attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc19100attr_one_list> |

- `Dsc20800attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc20800attr_one_list> |

- `Dsc21400attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc21400attr_one_list> |

- `Dsc21414attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc21414attr_one_list> |

- `Dsc21600attrs_ext_one_list`（?）

  | 字段 | 类型 |
  |---|---|---|
  | attr_one_list | uint16 |
  | id | struct<Dsc21600attr_one_list> |
