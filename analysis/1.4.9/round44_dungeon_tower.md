# 副本/爬塔进度系统骨架：13005/13034/13036/13045/13052/13058、21301（2026-09-19 · round44）

> 承接 round43（珍宝/充值/VIP/伙伴收口）。按 HANDOVER §6 **P1′-A** 开副本/爬塔模块。
> 本轮是**进度系统骨架**：把这 7 条原本在 `_GENERIC_DEFAULT_CMDS` 里回全零/空表的
> 查询型 CMD，做成"结构正确 + 关键数值非零 + 进度落库"。
> **不做进本战斗/刷怪/结算**——那是后续轮次。

---

## 一、问题

| CMD | 原状 | 危害 |
|---|---|---|
| `21301` 爬塔主界面 | 通用零值（floor=0/clear_list=空） | 爬塔页打不开/判未开启 |
| `13045` 爬塔层详情 | 通用零值 | 层信息空白 |
| `13052` 副本选择界面 | 通用零值（left_times=0） | 副本页次数/难度空白 |
| `13034` 副本章节奖励 | 通用零值 | CengList 空 |
| `13005` 副本次数查询 | 通用零值 | left_times=0 |
| `13036` 副本内设置回执 | 通用零值 | 设置不生效 |
| `13058` 波次活动副本 | 通用零值 | 分数/波次空白 |

---

## 二、取证（show_cmd.py 权威规格）

| CMD | CS 请求 | SC 应答 |
|---|---|---|
| 13005 | `bid:u32, flag:u8` | `bid:u32, flag:u8, left_times:u32` |
| 13034 | `dung_bid:u32` | `dung_bid:u32, CengList: T{ceng:u8,count:u16,can_get:u8,is_get:u8}` |
| 13036 | `dung_bid:u32, key:u8, value:u8` | `key:u8, value:u8` |
| 13045 | `floor:u32` | `floor:u32, rid:u32, srv_id, name, fast_rid:u32, fast_srv_id, fast_name, first_get:u8` |
| 13052 | 空 | `select_hard:u8, section:u8, hard:u8, challenge:u8, left_times:u8, assets: T{code:u8,num:u32}` |
| 13058 | `bid:u32` | `cur_score:u32, get_score:u32, max_wave:u8, gain: T{type:u8,count:u32}, AwardBidList: T{Bid:u32}` |
| 21301 | 空 | `tower_id:u32, floor:u32, is_effect:u32, clear_list: T{floor,first_clear_id,first_clear_srvid,first_clear_name,best_clear_id,best_clear_srvid,best_clear_name}, is_clear:u8, daily_floors:u8` |

原版配置表已定位（供后续轮次取真实数值）：
`config_single_tower`(156) / `config_dungeon_tower`(48) / `config_dungeon_new`(30) /
`config_golden_tower`(26) / `config_dungeon_endless_data`(11) 等。

---

## 三、做法

### 3.1 存储：新建 `dungeon_progress` KV 表

```sql
CREATE TABLE IF NOT EXISTS dungeon_progress (
    rid INTEGER, ptype TEXT, pkey TEXT, value INTEGER,
    PRIMARY KEY (rid, ptype, pkey))
```

- **不复用 `missions`**：missions 是任务状态专用（rid+mission_bid），副本/爬塔存的是
  "当前层/剩余次数/章节已领"等异构进度，硬塞会污染任务查询。
- `ptype`：`tower_floor`(pkey=tower_id) / `dung_left`(pkey=dung_bid) /
  `dung_got`(pkey='{dung_bid}_{ceng}')。
- 配套 `db_dung_get/set(rid, ptype, pkey, default)`（惰性建表，不碰现有 11 表）。

### 3.2 七个 handler 的应答设计（安全优先）

| CMD | 关键字段处理 |
|---|---|
| 21301 | tower_id=1, **floor=DB 读取(默认 1)** 而非 0, clear_list=空表, 其余 0 |
| 13045 | 回显请求 floor；所有 name/srv_id **空串**、rid/rid=0（单机无首通记录） |
| 13052 | section=1, hard=1, **left_times=DB(默认 5)**, assets=空表（不编消耗） |
| 13034 | 回显 dung_bid；CengList=空表（章节奖励发放后续做） |
| 13005 | 回显 bid/flag；**left_times=DB(默认 5)** |
| 13036 | 原样回显 key/value（设置回执） |
| 13058 | cur_score/get_score/max_wave=0；gain/AwardBidList=空表（**不发无效 bid**） |

**字节流已逐条手工核对**（对照规格字段数）：21301=16B / 13045=21B / 13052=7B /
13034=6B / 13005=9B / 13036=2B / 13058=13B，均与字段宽度之和一致。

### 3.3 ★ 分发纪律（round40 坑，第三次执行）

7 个 CMD **全部从 `_GENERIC_DEFAULT_CMDS` 移除**——否则靠前的通用分支会抢先回全零，
专用 handler 根本不执行（round40 排行榜全零、round43 充值页空白的同一根因）。

---

## 四、验证

### 4.1 协议审计（服务端已重启加载 round44）

| 审计 | 本轮 | round43 基线 | 判定 |
|---|---|---|---|
| `audit_specs_vs_fields.py` | 2463 / **0 不一致** | 2463 / 0 | ✅ |
| `audit_sc_conformance.py`（全量 1635） | 1619 / **0 不一致** / 16 空 | 0 不一致 | ✅ |
| `audit_sc_conformance.py --generic --unsupported` | 93 一致 / **0 不一致** / 1 空 | 100 + 1 空 | ✅ 见注 |
| `audit_sc_live.py --unsupported` | **94/94 一致** | 101/101 | ✅ 见注 |

> 注：通用集合命令数 **101 → 94**，差值正好是本轮移出的 7 个 CMD；
> 移出后剩余项在线复核 94/94 一致，证明移出干净、无遮蔽、无退化。

### 4.2 分级

- 【已验证】四道审计零不一致；7 个 CMD 已移出通用集合；字节流逐条核对与规格吻合。
- 【待真机验证】7 个 handler 的实际渲染（爬塔页是否显示"第 1 层"、副本页次数是否=5）——需客户端触发后看 tcp.log。
- 【占位，待校准】`left_times=5`、`floor 默认 1`、`tower_id=1`——未对照 `config_single_tower`/`config_dungeon_tower` 的真实开放等级与每日次数。
- 【未做】进本战斗/刷怪/结算、章节奖励(CengList)真实数据、爬塔首通记录。

---

## 四bis、★ round44.1 补：13036 死循环止血（同日真机发现）

真机验收"有内容了"后，tcp.log 暴露一个 round44 引入的回归：

- **现象**：玩家在 14:48:05 点了封魔塔某按钮，客户端发 `CS_13036 dung_bid=40001 key=4 value=0`，
  本服按规格回 `SC{key=4,value=0}`（2 字节）后，客户端**同一秒内重发同包 1424 次/分钟**，刷爆日志。
- **对照证据**：旧进程（round44 前）对 13036 **不回包**时，客户端只发一次 `key=1 value=1` 就继续走心跳，不死循环。
  ⇒ 该 CMD 在此版本是 **fire-and-forget**（或客户端对回包有未取证的隐含要求），主动按规格回 key/value 反而触发重试。
- **控制器归属**（round39 分类）：13034/13036 属 **demontower（封魔塔）**；13045 属 tower_ctrl；
  13052 属 trial_ctrl；13005/13058 属 dungeon_ctrl——四者不是同一玩法，本轮并表处理是简化。

**止血改法**（`_fix_round44_1_13036.py`）：13036 handler 改为不 sendall，仅把 `(dung_bid,key)->value`
落 `dung_setting` KV 备查并记日志。重启后审计仍 93/0 无退化。

> 【已取证 · round44.2】已反汇编 `demontower_ctrl.luac`（6.6KB，proto #14 = handle_13036）：
> SC_13036 按 `info.key` 分四分支（knum=[1,2,3,4]）：
>   key=1 → `openView()`；key=2 → `view:setSelected(value)`（选层）；
>   key=3 → `view:openTower(value)`（进塔）；**key=4 → `closeView()`**（关闭封魔塔视图）+ `Debug(msg)`。
> 即 13036 不只是设置回执，更是**服务端推送指令**；key=4 = 关闭界面。
> 真机复测：新进程"不回包"后客户端只发一次 key=1 即停（14:54:35 后无刷屏），确认止血有效。
> 完整 key=4 处理需配套把玩家切出封魔塔场景（玩家当时仍在塔内），随封魔塔玩法一起做。

---

## 五、产出

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `db_dung_init/get/set`；7 个副本/爬塔 handler；7 CMD 移出通用集合 |
| `server/mock_server.py.bak_round44_dungeon` | 改前备份 |
| `server/_fix_round44_dungeon.py` | 本轮补丁脚本（可复现） |
| DB | 运行时新建 `dungeon_progress` 表（rid/ptype/pkey/value） |

---

## 六、运维

- **服务端已重启**（旧 PID 44872 已停，新进程监听 9000/8080）。SQLite 数据在盘上不丢，真机玩家重连即可。
- 重启后首次真机进副本/爬塔页时，注意 `server/logs/tcp.log` 里 21301/13052 等的 `<<` 行。
- 纪律延续：有玩家在时**不要还原 DB、不要跑 `replay_captures.py`**。

---

## 七、下一步

1. **真机验收**：让客户端进爬塔/副本页，确认不崩、有内容；把【待真机验证】项坐实。
2. **数值校准**：从 `config_single_tower`(156 条) / `config_dungeon_tower`(48) 取真实
   `floor 上限 / 每日次数 / 开放等级`，替换占位的 5 和 1。
3. 并行取证**综合战力闭环**（写 `RoleVo.power[1].val` 的那条同步消息）。
4. 后续轮次再做：进本战斗接线、CengList 章节奖励真实数据与领取、爬塔首通记录。
