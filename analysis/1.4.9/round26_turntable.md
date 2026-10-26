# 第二十六轮：幸运转盘修复（14700/14701）+ 当前总状态

> 用户"继续" → 我把此前**明确报过但未闭环**的"幸运转盘"清掉。

---

## 一、幸运转盘 —— ✅ 已修复

### 取证（客户端 `game/turntable/turntable_ctrl.luac`）
```
RegisterProtocal 14700 on14700 / 14701 on14701
GetPrototype 14701          ← ★ 客户端主动发这条
```

### 协议（manual.md，均无未解子表）
```
14700 (空) → SC{id:u32, lottery_list:table(id:u32, bid:u32, quantity:u32, bind:u8)}  ← 奖池列表
14701 (空) → SC{id:u32, code:u8, msg:string}                                         ← ★ 抽奖
```

### 配置（`config_holiday_dial_reward_data.luac`）
```
LuckyTurnTableConstant: gold_once=**80钻石/抽**、gold_ten=800、lev_limit=30、free_times=5
HolidayDialRewardList:  index→item_bid（28560时装卡/28515玄冰葫芦碎片/一等奖=奖池50%...）
```

### 实现与验证
```
14700 → 58 字节（奖池 4 件）
14701 → **转盘抽奖 -80钻石 → +28515 x1**（日志实锤）
```

### 本轮踩的 1 个坑（如实）
**`db_sub_assets` 不存在**（我误用了不存在的函数名）⇒ 14701 首测无回包。
**修**：资产扣除应该用 `db_add_assets(rid, {'gold': -cost})`（负数）。
另：`self._bag_code` 不存在 ⇒ 改回固定 `BAG_MAIN`。

---

## 二、当前服务端总状态（合并子代理 3 批 + 我）

| 项 | 状态 |
|---|---|
| **服务端** | ✅ 运行中（PID 44148），stderr 0，语法 OK，已备份 `.bak_pre_world` |
| **AOI/寻路接线**（10204 双向广播） | ✅ 已激活（子代理 85b3f015 完成 + 我重启生效） |
| **10304**（属性+战力包）/ **20100**（综合战力） | ✅ 已实现 |
| **幸运转盘 14700/14701** | ✅ **本轮**修复 |
| `server/world/` P1 骨架 | 📦 已交付（未接 TCP/HTTP） |

### 三个已知真问题（待后续）
1. `get_mapgrid()` 仍 `allow_all=True` ⇒ **防穿墙是纸面校验**（数据源待接）
2. `TcpHandler.cfg` 类属性共享 ⇒ 全连接共用 rid=1001 ⇒ **真机双客户端看不到广播**
3. `pathfind.py` 文档前提（"客户端不能传路径"）与 Q2 事实相反，待修订

---

## 三、后台子代理的最新增量（已记录，未触发冲突）

- **task_matrix.md**（R5）：3 项目收敛到"4 态"任务状态；纠正"任务参考 CXEngine addon/quest"（该文件从未被读）→ 改指向空空西游 `task/*.js`
- **战斗字段解出**：`magic_list` 才是 buff 载体（`duration:uint8`）、`specials` 是外观通道；真机捕获证明"原版服务端数据不可得"⇒ 决定按"每回合全量重列"实现；且客户端**容忍空 buff 表**（可后置实现）

---

## 四、交付
```
server/mock_server.py     （新增 14700/14701）
server/config.json        （新增 turntable_pool/gold_once）
```

**本轮**：清掉"幸运转盘无法完成抽奖"。服务端在线健康（PID 44148）。

**下一步候选**（你定）：① 幸运转盘实机确认是否"能抽到奖"；② 修 P1 项（任务 `show_lave_time/lave_time` 缺口）或 P0 账号/会话缺失；③ 接 `server/world/`。或转回综合战力 A 线。