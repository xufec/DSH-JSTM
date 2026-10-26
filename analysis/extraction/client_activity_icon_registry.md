# 客户端活动图标注册表（反汇编 `activity_ctrl.luac` proto#30）

来源：1.4.11 APK `assets/src/game/activity/activity_ctrl.luac` 的 `Activityhander10925`。
证据等级：**CONFIRMED**（字节码 `TableConst` 直接读出，非推断）。

| label（活动名）| name（内部键）| icon_res |
|---|---|---|
| '神界探宝' | 'dragontreasure' |  |
| '飞升成神' | 'flyup' |  |
| '新消耗排行榜' | 'xfphb' | 'xfphb' |
| '新充值排行榜' | 'czphb' | 'czphb' |
| '砸金蛋' | 'breakeggs' |  |
| '合服首充' | 'hfsc' | 'hfsc' |
| '飞升返利礼包' | 'flyUp_gift' |  |
| '奖池转盘' | 'jiangchi' |  |
| '充值翻倍' | 'charge_double' |  |
| '老玩家回归' | 'recruit' |  |
|  |  |  |
|  | 'hefu' |  |
|  | 'answer' |  |
|  | 'guess' |  |
|  | 'rotatetable' |  |
|  | 'lucky_turntable' |  |
|  | 'guildmatchwar' |  |
|  | 'super_vip' |  |
| '众神联赛' | 'godwar' |  |
| '众神联赛场景' | 'godwarscene' |  |
|  | 'fc' |  |
|  | 'menpai' |  |
|  | 'gangwars' |  |
|  | 'guildwars' |  |
|  | 'kuafu_guildwars' |  |
|  | 'wedding' |  |
|  | 'actionrank' |  |
|  | 'invest_sec' |  |
|  | 'reward' |  |
|  | 'kuafu_xianmo' |  |
|  | 'duihuan' |  |
|  | 'yunyingduihuan' |  |
|  | 'flower' |  |
|  | 'diguowar' |  |
|  | 'luckbox' |  |
|  | 'peakwar' |  |
|  | 'zhufuqiang' |  |
|  | 'chief' |  |
|  | 'xingyunfanpai' |  |
|  | 'miling' |  |
|  | 'julong' |  |
|  | 'paimai' |  |
|  | 'guildcretarea' |  |
|  | 'treasureplane' |  |
|  | 'target' |  |
| '一元夺宝' | 'duobao' |  |
| '刮刮乐' | 'scratcher' |  |

> 共 **47** 条去重条目。
> 这是客户端**认识**的活动集合；`10924.act_list` 下发后客户端会逐项按 `name`
> 分派到对应控制器，**其中一部分会自动打开面板** —— 即 R49 观察到的"活动预告弹窗"。
> ⇒ 后续实现 `10924/10925` 时，应**排除**会触发自动打开的那几类，即可兼顾"图标显示"与"无弹窗"。
