# 移动 协议（R2）

> 数据来源：`protocol/fields.json`（权威字段定义）+ `mock_server.py`（实现）+ 真机日志。
> **字段来自 `cmd_resolve_*.luac`，不是推测。**

## 命令清单（38 条）

| CMD | 方向 | 实现 | 真机发过 | 真机回过 | 字段 |
|---|---|---|---|---|---|
| 10900 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; hour:uint32; interdict:string ／ SC code:uint8; msg:string |
| 10901 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; hour:uint32; banned:string ／ SC code:uint8; msg:string |
| 10902 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; stop_role:string ／ SC code:uint8; msg:string |
| 10910 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC dnf_info:table |
| 10911 | SC | ❌ |  |  | SC rid:uint32; srv_id:string; buffs:table |
| 10912 | SC | ❌ |  |  | SC bid:uint32; effect:table |
| 10913 | SC | ❌ |  |  | SC buffs:table |
| 10921 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC world_lev:uint8; next:uint32; exp:uint16; dec_exp:uint16; open_day:uint16 |
| 10922 | CS+SC | ✅ | ✅ | ✅ | CS （无字段/空消息） ／ SC act_list:table |
| 10923 | CS+SC | ✅ | ✅ | ✅ | CS id:uint16 ／ SC id:uint16; status:uint8; int_args:table |
| 10924 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC act_list:table |
| 10925 | CS+SC | ❌ |  |  | CS id:uint16 ／ SC id:uint16; status:uint8; int_args:table |
| 10930 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; double:uint16; double_sum:uint16 |
| 10931 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10932 | CS+SC | ❌ | ✅ | ✅ | CS （无字段/空消息） ／ SC double:uint16; double_sum:uint16; double_state:uint16; off_state:uint16 |
| 10933 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10934 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string |
| 10935 | SC | ❌ |  |  | SC double:uint16 |
| 10941 | SC | ❌ |  |  | SC id:uint8 |
| 10942 | CS+SC | ❌ |  |  | CS id:uint8 ／ SC （无字段/空消息） |
| 10945 | CS+SC | ❌ |  |  | CS card_id:string ／ SC code:uint8; msg:string; items:table |
| 10946 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC code:uint8; msg:string; item_bid:uint32 |
| 10947 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; lev:uint16; career:uint16; sex:uint8; is_vip:uint8; vip_lev:uint8; gname:string; cur_title:uint32; marry_state:uint8; spouse_n |
| 10948 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; items:table |
| 10949 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:ta |
| 10950 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; jie:uint8; jie_luck:uint16; grow:uint16; zz:uint16; face:uint8; use:uint8; skill_list:table; attr_list:table; can_item_list:table; items:ta |
| 10951 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; color:uint8; wing_id:uint32; power:uint32; wing_skill:table; add_attr:table; star:uint16 |
| 10952 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; use_id:uint32; shenqi_list:table |
| 10953 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string; type:uint8 ／ SC code:uint8; msg:string |
| 10954 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; name:string; stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; looks:table; surface_star |
| 10955 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table |
| 10957 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC stage:uint8; power:uint32; luck:uint16; res_stage:uint8; grow:uint16; skill_list:table; items:table; surface_list:table; surface_star:table |
| 10958 | CS+SC | ❌ |  |  | CS rid:uint32; srv_id:string ／ SC rid:uint32; srv_id:string; items:table |
| 10995 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC srv_list:table |
| 10996 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC cli_ver_list:table |
| 10997 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC flag:uint8 |
| 10998 | CS+SC | ❌ |  |  | CS （无字段/空消息） ／ SC cli_ver:uint16; flag:uint16 |
| 10999 | CS | ❌ | ✅ |  | CS msg:string |

## 说明

- **实现**：`mock_server.py` 历程里有对应分支
- **真机发/回**：在实机会话日志里观测到过
- ⚠ 字段列真空 = 该 CMD 在 `fields.json` 里无字段定义（可能是空消息或未解）

---

## ★★ 修正记录（2026-09-18）：**移动主体在 10200 段，不在 10900 段**

> **原报告错误**：只列了 `10900+`，**漏掉了整个 `10200` 段**。
> **而 `10204` 才是真正的角色移动协议。**

### 10200 段实测（真机日志已验证）

| CMD | 方向 | 实现 | 真机发 | 真机回 | 说明 |
|---|---|---|---|---|---|
| **10204** | CS+SC | **✅** | **✅** | **✅** | **CS_10204{x:u16, y:u16} → SC_10204{rid, srv_id, x, y}**，`scene_controller.on10204 → model:syncRoles` |
| **10205** | CS+SC | **✅** | | | CS_10205 瞬移 |
| 10200 | CS+SC | ✅ | ✅ | | 进场/初始化 |
| 10201 | CS+SC | ✅ | ✅ | | 场景数据 |
| 10202-10203 | SC | ❌ | | | 待定性 |
| 10206-10224 | CS/SC | ❌ | | | 待定性（含 10212/10213，提取里是怪物实时移动） |
| 10230-10299 | CS/SC | ❌ | | | 待定性 |

### ★ 对「移动不通」这个结论的修正

**位置同步（10204）是通的** —— 真机日志显示客户端发坐标、服务端回并保存。

不通的是**点击自动寻路**（点任务/地点 → 客户端自己算路径过去）。
★ 据 R1 审计（Survive D13/D14），这类“客户端发目标点”应走**寻路协议**，
而不是 10204 的“逐步上报坐标”。**具体 CMD 待定位**。