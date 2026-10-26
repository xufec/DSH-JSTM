# 《绝世唐门》协议手册 · 登录链路

> 类型：uint8/int8/uint16/int16/uint32/int32/string/float/double/bool/table。`CS*` = 客户端→服务端，`SC*` = 服务端→客户端。

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
