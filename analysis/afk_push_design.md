# 挂机服务端推帧方案（2026-10-02）

## 结论：无需新造帧，复用既有 154xx 挂机族（已 CONFIRMED 客户端解析）

| 帧 | 方向 | 格式 | 客户端消费点 | 用途 |
|---|---|---|---|---|
| 15402 | CS{mission_bid:u32} -> SC{mission_bid,map_bid,x,y} | ghost_ctrl.luac | 进挂机图（传送+坐标） | 选图后触发 |
| 15403 | CS{mon_bid:u32} -> SC{code:u8,msg:string} | ghost_ctrl.luac handle15403 | 杀怪上报（kill_count+1） | 巡逻自动战斗 |
| 15404 | SC{mission_bid:u32} push_to_rid | mon_hongchen:deleteMon | 结束本轮清怪 | 退出挂机 |
| 15405 | SC{loop_count:u32} | ghost_ctrl | 轮次计数 | 进度 |

## 方案
- 客户端驱动：选挂机图 -> 发 CS_15402{mission_bid} -> 服务端按等级段
  guaji_spot_for_lev(lev) 推 SC_15402{map_bid,x,y} -> 客户端传送进图渲染怪。
- 自动巡逻战斗：客户端在图内自动打 -> 发 CS_15403{mon_bid} -> 服务端 kill_count+1。
- 服务端结算闭环（afk.patrol_kills）：挂机场次内按分钟 grant 20003 掉落组，
  ref=afk_kill:<rid>:<start>，reward_log 幂等。
- 退出：/DSH_ADMIN/guaji_end 推 15404 清怪。

## 不猜包纪律
- "一轮=几只怪"无取证，不自动推 15404（R53 已注明）；结束走 GM 旋钮。
- 定时战斗帧不新造：客户端 15403 自驱，服务端只应答+结算。
