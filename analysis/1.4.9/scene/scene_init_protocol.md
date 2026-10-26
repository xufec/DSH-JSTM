# 1.4.9 场景初始化协议（scene init protocol）

> 目标 APK：**1.4.9** / `com.shiyue.dldl.ewan.qihoo`。
> 所有结构来自客户端 `assets/src/config/protocal/cmd_resolve_102.luac` 等定义，非推测。

---

## 一、场景相关命令一览（1.4.9）

| CMD | 客户端类 | 方向 | 结构 |
|---|---|---|---|
| 10200 | `CSRoleEnter_10200` | C→S | `bid:uint32` |
| 10200 | `SCRoleEnter_10200` | **S→C** | `code:u8, msg:string, bid:u32, line_id:u8, x:u16, y:u16, dir:u8` |
| 10201 | `CSMapGird_10201` | C→S | **无字段（空消息）** |
| 10201 | `SCMapGird_10201` | S→C | `roles:table, npcs:table, mons:table, elems:table` |
| 10202 | `SCMapRole_10202` | S→C | `roles:table(…同 10201 的 roles 元素…)` |
| 10203 | `SCRoleLeave_10203` | S→C | `role_ids:table(rid:u32,srv_id:string), bid:u32` |
| 10204 | `CS_10204` / `SC_10204` | C→S / S→C | C:`x:u16,y:u16` / S:`rid:u32,srv_id:string,x:u16,y:u16` |
| 10205 | `CS_10205` / `SC_10205` | C→S / S→C | 同 10204（瞬移） |
| 10206 | 传送 | 双向 | 传送到指定场景 |
| 10210 | 切换线路 | | |
| 10222 | 传送到指定场景指定坐标 | | |

## 二、`roles` 元素结构（10201/10202 共用）

```
rid:u32  srv_id:string  name:string  lev:u16  career:u16  vip_lev:u8  sex:u8
status:u8  mspd:u16  x:u16  y:u16  dir:u8  hidden:u8  cur_title:u16
ntm_title:u32  marry_state:u8  spouse_name:string
buff_bids:D|Dsc10201buff_bids|        ← bid:u16
misc_uint8 / misc_uint16 / misc_uint32 / misc_str : D|Dsc10201misc_*|
animate_res:D|Dsc10201animate_res|    ← dis_method:u16, ent_lev:string, ant_val:u8, ant_id:u8
```

**已知不确定**：`misc_*` 四组在 `protocol/fields.json` 里**没有解出字段**
（`Dsc10201misc` 标注"无字段"）。当前按"计数前缀 + 0 项"编码，
客户端**未报错**，但**不能断言编码正确**。

`npcs` 元素另有 `misc`（`Dsc10201misc`）与 `member`（`Dsc10201member`）两个未解出的子表。

## 三、编码约定（实测确认）

- 帧：`[u32 大端 payload_len][u16 大端 cmd][body]`，`len = 2 + len(body)`
- 字符串：`[u16 大端 长度][字节]`
- key/val 形表：`[u16 项数]` + 每项 `[str key][str val]`
- 结构化数组表：`[u16 项数]` + 每项按字段顺序拼接
- **短消息尾部有脏数据**：客户端整段发定长缓冲，服务端必须按定义读、忽略尾部

## 四、服务端实现状态

| 项 | 状态 |
|---|---|
| 10200 主动下发（进场景通知） | ✅ 已实现，坐标取自**持久化状态**（已实测读回 777,888） |
| 10201 应答（客户端请求时） | ✅ 已实现，带"自己"这个角色 |
| 10201 主动推送（进场景时） | ✅ 已实现 |
| 10202 / 10203（附近角色进出） | ⬜ 未实现（单人测试服暂不需要） |
| 10204 / 10205（移动/瞬移） | ✅ 已实现（回权威坐标 + 落盘），**未被客户端触发** |

## 五、进场景所需的最小数据集

**必须**：服务器条目、`1110.code==1`、`roles` 至少 1 条、`10103/10102 code=0`、
`SCRoleEnter_10200`（含 x,y）、`SCMapGird_10201.roles` 含自己、`SC_10301`。
**可空**：`10201` 的 `npcs/mons/elems`；14 个子系统的空应答。
详见 `analysis/1.4.9/scene/enter_scene_flow.md` 第三节。
