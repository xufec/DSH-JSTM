# PHASE 1 — 战斗族 SC 字节解码（来自只读端点 `battle_replay`）

> 通道：`GET /DSH_ADMIN/battle_replay?mon_id=20001`（服务端构造的确定性回放，两次调用 hex 一致）。
> 解码：`protocol/fields.json` 的 SC 规格。
> ⚠ **结构 = CONFIRMED**（服务端按规格编码，能被规格解出）；
> **数值 = mock 实现值（TEST_ONLY）**，不等于原版真值。

## 帧清单（去重后 10 帧；原始 10 帧）

| cmd | SC 规格 | hex 长度 |
|---|---|---|
| 20002 | SC_20002 | 9 B |
| 20010 | SC_20010 | 130 B |
| 20012 | SC_20012 | 41 B |
| 20013 | SC_20013 | 53 B |
| 20012 | SC_20012 | 41 B |
| 20013 | SC_20013 | 39 B |
| 20012 | SC_20012 | 41 B |
| 20013 | SC_20013 | 53 B |
| 20020 | SC_20020 | 7 B |
| 20023 | SC_20023 | 99 B |

## 帧  cmd=20002  (SC_20002)

```
raw  (  9 B) = 000000054e22010000
body (  3 B) = 01 00 00
fields      = {"code": 1, "msg": ""}
```

## 帧  cmd=20010  (SC_20010)

```
raw  (130 B) = 0000007e4e2a0001000100010001010001000000000002000000010000000200020001000003e900013100034453480046000001010100001c8900001c890000000000000000000000000200004e2100036d6f6e00067265706c6179004600000101020000079e0000079e0000000000000100010006483332303030000000000000
body (124 B) = 00 01 00 01 00 01 00 01 01 00 01 00 00 00 00 00 02 00 00 00 01 00 00 00 02 00 02 00 01 00 00 03 e9 00 01 31 00 03 44 53 48 00 46 00 00 01 01 01 00 00 1c 89 00 00 1c 89 00 00 00 00 00 00 00 00 00 00 00 00 02 00 00 4e 21 00 03 6d 6f 6e 00 06 72 65 70 6c 61 79 00 46 00 00 01 01 02 00 00 07 9e 00 00 07 9e 00 00 00 00 00 00 01 00 01 00 06 48 33 32 30 30 30 00 00 00 00 00 00
fields      = {"round": 1, "round_wave": 1, "wave_max": 1, "wave_no": 1, "atk_formation_type": 1, "atk_formation_lev": 0, "def_formation_type": 1, "def_formation_lev": 0, "is_observer": 0, "effect_id": "", "order_list": [{"id": 1}, {"id": 2}], "fighter_info_list": [{"id": 1, "rid": 1001, "srv_id": "1", "name": "DSH", "lev": 70, "sex": 0, "career": 1, "pos": 1, "group": 1, "hp_max": 7305, "hp": 7305, "anger": 0, "is_auto": 0, "animate_res": [], "skills": [], "specials": []}, {"id": 2, "rid": 20001, "srv_id": "mon", "name": "replay", "lev": 70, "sex": 0, "career": 1, "pos": 1, "group": 2, "hp_max": 1950, "hp": 1950, "anger": 0, "is_auto": 0, "animate_res": [{"ant_id": 1, "ant_val": "H32000", "ent_lev": 0, "dis_method": 0}], "skills": [], "specials": []}]}
```

## 帧  cmd=20012  (SC_20012)

```
raw  ( 41 B) = 000000254e2c0001000100000100002710000000000000000000000000000000000000000000000000
body ( 35 B) = 00 01 00 01 00 00 01 00 00 27 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
fields      = {"round": 1, "skill_play": [{"order": 0, "user_id": 1, "skill_id": 10000, "father_id": 0, "father_skill_id": 0, "passive_skill_id": 0, "user_anger": 0, "talk": "", "notice": "", "magic_play": [], "summon_play": []}], "cooldown": []}
```

## 帧  cmd=20013  (SC_20013)

```
raw  ( 53 B) = 000000314e2d0001000100010001000000000200017f0000079e0000020b000000000100002710fffffa6d00000000000000000000
body ( 47 B) = 00 01 00 01 00 01 00 01 00 00 00 00 02 00 01 7f 00 00 07 9e 00 00 02 0b 00 00 00 00 01 00 00 27 10 ff ff fa 6d 00 00 00 00 00 00 00 00 00 00
fields      = {"round": 1, "round_wave": 1, "time": 0, "wave_no": 1, "magic_play": [{"order": 0, "target_anger": 0, "target_id": 2, "source_id": 1, "hit": 127, "hp_max": 1950, "hp": 523, "is_target_die": 0, "target_talk": "", "magic_list": [{"fold": 0}]}], "summon_play": [{"id": 65535, "rid": 4201447424, "srv_id": "", "name": "", "lev": 0, "sex": 0, "career": "<decode-stop>", "pos": 0, "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, "<...9992 more rows...>"], "order_list": "<decode-stop>"}
```

## 帧  cmd=20012  (SC_20012)

```
raw  ( 41 B) = 000000254e2c0001000100000200000000000000000000000000000000000000000000000000000000
body ( 35 B) = 00 01 00 01 00 00 02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
fields      = {"round": 1, "skill_play": [{"order": 0, "user_id": 2, "skill_id": 0, "father_id": 0, "father_skill_id": 0, "passive_skill_id": 0, "user_anger": 0, "talk": "", "notice": "", "magic_play": [], "summon_play": []}], "cooldown": []}
```

## 帧  cmd=20013  (SC_20013)

```
raw  ( 39 B) = 000000234e2d0001000100010001010000000100020100001c8900001c88000000000000000000
body ( 33 B) = 00 01 00 01 00 01 00 01 01 00 00 00 01 00 02 01 00 00 1c 89 00 00 1c 88 00 00 00 00 00 00 00 00 00
fields      = {"round": 1, "round_wave": 1, "time": 0, "wave_no": 1, "magic_play": [{"order": 1, "target_anger": 0, "target_id": 1, "source_id": 2, "hit": 1, "hp_max": 7305, "hp": 7304, "is_target_die": 0, "target_talk": "", "magic_list": []}], "summon_play": [], "order_list": []}
```

## 帧  cmd=20012  (SC_20012)

```
raw  ( 41 B) = 000000254e2c0002000100000100002710000000000000000000000000000000000000000000000000
body ( 35 B) = 00 02 00 01 00 00 01 00 00 27 10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
fields      = {"round": 2, "skill_play": [{"order": 0, "user_id": 1, "skill_id": 10000, "father_id": 0, "father_skill_id": 0, "passive_skill_id": 0, "user_anger": 0, "talk": "", "notice": "", "magic_play": [], "summon_play": []}], "cooldown": []}
```

## 帧  cmd=20013  (SC_20013)

```
raw  ( 53 B) = 000000314e2d0002000100010001000000000200017f0000079e00000000010000000100002710fffffa6d00000000000000000000
body ( 47 B) = 00 02 00 01 00 01 00 01 00 00 00 00 02 00 01 7f 00 00 07 9e 00 00 00 00 01 00 00 00 01 00 00 27 10 ff ff fa 6d 00 00 00 00 00 00 00 00 00 00
fields      = {"round": 2, "round_wave": 1, "time": 0, "wave_no": 1, "magic_play": [{"order": 0, "target_anger": 0, "target_id": 2, "source_id": 1, "hit": 127, "hp_max": 1950, "hp": 0, "is_target_die": 1, "target_talk": "", "magic_list": [{"fold": 0}]}], "summon_play": [{"id": 65535, "rid": 4201447424, "srv_id": "", "name": "", "lev": 0, "sex": 0, "career": "<decode-stop>", "pos": 0, "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, {"id": "<decode-stop>", "rid": "<decode-stop>", "srv_id": "<decode-stop>", "name": "<decode-stop>", "lev": "<decode-stop>", "sex": "<decode-stop>", "career": "<decode-stop>", "pos": "<decode-stop>", "group": "<decode-stop>", "hp_max": "<decode-stop>", "hp": "<decode-stop>", "anger": "<decode-stop>", "is_auto": "<decode-stop>", "animate_res": "<decode-stop>", "skills": "<decode-stop>", "specials": "<decode-stop>"}, "<...9992 more rows...>"], "order_list": "<decode-stop>"}
```

## 帧  cmd=20020  (SC_20020)

```
raw  (  7 B) = 000000034e3401
body (  1 B) = 01
fields      = {"result": 1}
```

## 帧  cmd=20023  (SC_20023)

```
raw  ( 99 B) = 0000005f4e3700010002000003e9000131000344534801004600000100001c8900001c88000000010000000000000000000100004e2100036d6f6e00067265706c61790200460000010000079e0000000000000b260000000000000000000200000000
body ( 93 B) = 00 01 00 02 00 00 03 e9 00 01 31 00 03 44 53 48 01 00 46 00 00 01 00 00 1c 89 00 00 1c 88 00 00 00 01 00 00 00 00 00 00 00 00 00 01 00 00 4e 21 00 03 6d 6f 6e 00 06 72 65 70 6c 61 79 02 00 46 00 00 01 00 00 07 9e 00 00 00 00 00 00 0b 26 00 00 00 00 00 00 00 00 00 02 00 00 00 00
fields      = {"type": 0, "result": 1, "role_hurl_list": [{"rid": 1001, "srv_id": "1", "name": "DSH", "group": 1, "lev": 70, "sex": 0, "career": 1, "hp_max": 7305, "hp": 7304, "hurt": 1, "master_rid": 0, "master_srv_id": "", "id": 1}, {"rid": 20001, "srv_id": "mon", "name": "replay", "group": 2, "lev": 70, "sex": 0, "career": 1, "hp_max": 1950, "hp": 0, "hurt": 2854, "master_rid": 0, "master_srv_id": "", "id": 2}], "val_list": [], "msg": ""}
```
