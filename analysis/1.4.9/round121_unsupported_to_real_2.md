# R121：再 4 条"未开放" → 真功能（建宗门 / 摆摊 / 坐骑地图态 / 进镇魔塔）

> 新目标第 2 批。`_UNSUPPORTED_ACTION_CMDS` 从 **19 → 11**。
> **时间**：2026-09-30 03:10 – 03:40。

---

## 一、本批 4 条

| cmd | CS | SC | 真实状态 |
|---|---|---|---|
| **`13500`** | `{guild_name:string}` | `{code,msg}` | ★ 新建 `role_guild(rid,name,ctime)`；重名/已有/空名 **明确拒绝** |
| **`13803`** | `{type:u16}` | `{code,msg}` | ★ 新建 `role_market(rid,on_state,ctime)`（`type=0` ⇒ 关、其余 ⇒ 开，**注释标注未取证**）|
| **`18600`** | 空 | `{code,msg,map_state:u8,status:u8}` | ★ 复用 R115 的 `role_ride`：**有坐骑才 `map_state=1`** |
| **`13020`** | `{dung_bid:u32, args:table(key,value)}` | `{tips,msg}` | ★ 记入 `dungeon_progress`（`ptype='dung_enter'`，`args` 原样存档）|

---

## 二、实测（全部以**数据库真实状态**为准）

```
== 13500 建宗门 ==
  code=1 msg=''  role_guild 行=[('DSH测试宗门',)]        ← ★ 真的建了
  重复创建 ⇒ code=0 msg='已经创建过宗门'                  ✓
  空名     ⇒ code=0 msg='宗门名不能为空'                  ✓

== 13803 摆摊 ==
  type=1 ⇒ code=1，表里 on_state=[(1,)]                  ← ★ 真的落库
  type=0 ⇒ code=1，表里 on_state=[(0,)]                  ✓

== 18600 坐骑地图态 ==
  没坐骑 ⇒ map_state=0 status=0
  有坐骑 ⇒ map_state=1 status=0                          ← ★ 真实 DB 驱动
  ★ 有坐骑才 map_state=1 ⇒ ✓

== 13020 进镇魔塔 ==
  tips=0  dungeon_progress(dung_enter) 行=[('40001', 105)]  ← ★ 真的落库
=== 结果: PASS ===
```

★ 关键判据都是**读 DB 前后对比**（`role_guild` / `role_market.on_state` / `dungeon_progress`），
`18600` 还做了**对照组**（没坐骑 vs 有坐骑 ⇒ `0` vs `1`）。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **216** / 默认 47 / **未开放 11**）/ 静态 PASS / conformance PASS / **SC 在线 58-58** / **专用 78-78** / 门禁 E **PASS** |
| 回归（**19 项**） | **新增 `verify_unsupported4b.py`** + 前 18 项 **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `db_guild_init/create`、`db_market_set`、`db_dung_enter` + `13500`/`13803`/`18600`/`13020` 处理器；从 `_UNSUPPORTED_ACTION_CMDS` 移出 4 条 |
| `tools/_fix_r121_unsupported4b.py` | 插入脚本 |
| `tools/verify_unsupported4b.py` | **新增回归第 19 项** |
| `server/mock_server.py.bak_r121` | 改前备份 |

---

## 五、★ 剩余 11 条"未开放"的处置

| cmd | 计划 |
|---|---|
| **`30201`（宗门秘境）** | ★ **本批新建了 `role_guild`** ⇒ 现在可以**依据真实宗门状态**实现（下一批）|
| `12762`（聊天）/ `13201`（队伍）/ `13224`（邀请）/ `13342`（好友消息）/ `13343`（群发）/ `13359`（朋友圈）/ `18300`（婚宴）| 社交域 —— **1 个角色** ⇒ 空即真话（但`13359`朋友圈**可发单条**，见下批评估）|
| `11400`（称号）| 玩家没有该物 ⇒ 与默认响应等价 |
| `15200`（NPC）/ `19500`（任务）| 字段语义未取证 ⇒ 不猜 |

**新目标进度**：未开放 **19 → 11**；专用分支 **208 → 216**；回归 **17 → 19**。
