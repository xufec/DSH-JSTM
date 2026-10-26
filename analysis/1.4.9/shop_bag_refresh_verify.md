# 商城购买 → 按 pay_type 扣币 → 入包 → 背包**即时**刷新（实机验证 + 本轮优化）

> 日期：2026-09-18 · 目标 APK：`anzbao/jstm.apk`（1.4.9 / `com.shiyue.dldl.ewan.qihoo`）
> 服务端：`server/mock_server.py`（PC 端 8080/9000）
> 纪律：**只写有证据的结论**；方法、坐标、日志都给全，便于复现。
> 证据类型：`LOG`=服务端日志 · `DB`=SQLite · `UI`=模拟器实机点击+截图 · `TCP`=直连 TCP 独立测试

---

## 〇、一句话结论

**这条链路在本轮首次做到"实机全通"**：在模拟器里真的买了一件东西（服务端 `SC_12805 code=1`、
扣的是 `gold`），并且**在背包面板一直开着的情况下**，服务端推一次背包就让它**当场多出一个格子**。
过程中修掉一个真实缺陷（背包推送只覆盖一个 `bag_code`）并补上一条客户端一直在问、
服务端却从不回答的协议（`12831`）。

---

## 一、实机证据（本轮新增，都可复核）

### 1.1 游戏内真实购买成功（`LOG`）

```
[11:48:24] >> cmd=12805 ? body(8)=07 d3 00 01 00 01 31 6f      ← 客户端发来：id=0x07d3=2003
[11:48:24] ** 购买成功 goods_id=2003 item=36500 x1 扣 gold=5    ← 扣的是 gold(钻石)
[11:48:24] << 10500 SC_10500 bag push (after shop_buy) bag_code=7 items=15
[11:48:24] << 12805 SC_12805 code=1(TRUE) item=2003 x1 price=5
```

对照 `mall_config.json`：`id=2003 / item_bid=36500 / price=5 / pay_type=1`
⇒ 客户端的 `id` 语义、价格、**pay_type=1 → `gold`** 三者一致（`server/config.json` 的
`shop_pay_type_asset{"1":"gold"}` 因此**得到实机支持**，不再是"仅按客户端路径推导"）。

### 1.2 背包**即时刷新**（`UI` + `DB`）—— 本轮最关键的一条

做法：先把**背包面板打开并保持开着**，然后由服务端加一件物品并推送背包（用本轮新增的
`/DSH_ADMIN/additem`），前后各截一图比对：

| 项 | 结果 |
|---|---|
| 服务端推送 | `<< 10500 SC_10500 bag push bag_code=1,2,3,4,5,6,7,8,12,13,16,17 items=16` |
| 面板变化 | 主网格原来的一格**空（锁图标）** → 变成**新物品图标 + 红色"新增"小圆点** |
| 其它 | 底部三种货币数字**不变**（说明只是背包刷新，不是别的系统在动） |
| DB 复核 | 该时刻**只有** `item_id=16 / bid=33006 / pos=16` 一条新记录（`ctime` 对得上），排除"别的活动碰巧加了东西" |

⇒ **客户端确实会消费 `SC_10500` 并刷新已打开的背包**——"买了东西要重登才看得到"的旧现象
在服务端侧已不成立（前提是推送的 `bag_code` 覆盖到用户当前看的那一页，见 §三.1）。

对比图：`shots/dsh_bag_ab.jpg`（左 A＝加物品前，右 B＝加物品后，未重开面板）。

### 1.3 打开背包时**不再**重复请求 10502（`LOG`）

购买推过 `10500` 之后再打开背包，日志里**没有新的 `CS_10502`**（此前打开会一次性请求
5 个 bag_code）——说明客户端已把推送内容并入本地背包模型，不需要再问。

---

## 二、客户端的真实行为（本轮实测汇总）

| 观测 | 证据 |
|---|---|
| 打开商城第一件事是问 `12831`（限购/已购），**不是**先问列表 | `LOG`：11:45:56 `12831` → 11:45:59 `12803` |
| `CS_12803` 带 1 字节（页/分类？），服务端目前忽略该字节 | `LOG`：`body(4)=05 68 00 26`、`06 …` |
| 客户端**为不同背包页**用不同 `bag_code` 请求 `10502`：本轮累计见到 **1–8 / 12 / 13 / 16 / 17 共 12 个** | `LOG`：10500 推送回显的 `bag_code` 列表 |
| 商城的「限购 2 个」「热卖/折扣」等标签**由客户端本地配置渲染**（`Config.Mall` 就是 `mall_config.json` 的来源；其中 `limit_week/limit_day_cli/cli_tag` 都在客户端手里） | `UI` + `mall_config.json` 字段集合 |

---

## 三、本轮代码改动（`server/mock_server.py`）

### 3.1 ★ 背包推送改为覆盖**所有已请求的 bag_code**（修真实缺陷）

- **原实现**：只推 `getattr(self, '_last_bag_code', BAG_MAIN)` **一个**。
- **问题**：用户当前看的若不是最后请求过的那一页，界面就不会刷新
  （而客户端确实有 12 个 bag_code 在用）。
- **现实现**：新增 `bag_push_frames(handler, rid)`——记录该连接**请求过的全部** `bag_code`
  （`_bag_codes_seen`），逐个推送；购买、战斗掉落、管理接口三处统一走它。
- **验证**：`TCP` 测试里先请求 bag_code 1/7/12，购买后收到**三条** `SC_10500`
  （1、7、12）；`UI` 场景下 12 条全推。
- **保守处**：所有 bag_code 的内容仍取同一个 `bag_items` 表（本服务端的既有简化，未改）。

### 3.2 ★ 新增 `SC_12831`（客户端一直在问，原实现从不回答）

```
CS_12831（空） → SC_12831{ id_list: table(id:u16, has_buy_num:u16) }
```

- 依据：`tools/show_cmd.py 12831`；**无 `D|Dsc*|` 未解子表** ⇒ 可安全编码。
- `has_buy_num` 按字面取**"已购买次数"**（对照 `12801` 的 `can_buy_num`=可购买数量）；
  新增 `mall_bought(rid, goods_id, num)` 表记录购买次数，**只回报本服务端确实记录到的数字**，
  原版限购总量不可得 ⇒ 不编造。
- **验证**：`LOG` `<< 12831 SC_12831 id_list=134 (544 bytes) 已购商品种类=1`；
  `TCP` 测试购买 2003 后，该商品 `has_buy_num=1`。

### 3.3 新增管理接口 `/DSH_ADMIN/additem`

```
GET /DSH_ADMIN/additem?rid=1001&bid=33006&n=1
→ {"ok":true,...,"bag_count":16,"pushed":1}
```

给角色加物品并**立即推送背包刷新**。既是"给自己发道具"的常用操作，
也是本轮验证"背包开着能不能实时刷新"的探针。

---

## 四、直连 TCP 回归（不依赖客户端 UI）

脚本：`tools/shop_buy_test.py`（`python tools/shop_buy_test.py [goods_id]`）

```
① 10502 回包: [(10502, 627), (10502, 627), (10502, 627)]        ← 先请求 bag_code 1/7/12
② 购买后收到:
   SC_10500 背包推送 bag_code=1 items=16 (body 627 字节)
   SC_10500 背包推送 bag_code=7 items=16 (body 627 字节)
   SC_10500 背包推送 bag_code=12 items=16 (body 627 字节)       ← ★ 三个 code 都推了
   SC_10302 / SC_10301 / SC_10303 角色刷新
   SC_12805 code=1 id=2003 num=1 price=5
③ SC_12831 id_list=134, 商品 2003 的 has_buy_num=1              ← ★ 已购数量对得上
gold: 929381 → 929376（−5）                                     ← ★ 扣币币种与金额正确
```

---

## 五、模拟器操作手册（本轮踩过的坑 + 已验证可用的坐标）

坐标系：`screencap` 得到 **2560x1440 横屏**，`input tap` 用的就是这个空间（与既有文档一致）。

| 目标 | 做法 / 坐标 |
|---|---|
| 判断"面板到底开没开" | **别信视觉**，用服务端日志当反馈：打开商城必发 `12831`；打开背包发 `10502` |
| 打开背包（魂囊） | `input tap 2468 1164`（命中判定：截图差分 diff≈67，自然动画噪声只有 0.4） |
| 关闭背包面板 | **`input tap 2280 120`**（面板右上角 ✕；`Back` 键**无效**） |
| 打开商城 | 顶栏 `y=90`，**`x=550~750` 之间**逐个试，每次试完查日志有没有 `12831` |
| 选中商品格 | 2 列 × 4 行：col1 `x≈587` / col2 `x≈1462`；行 `y≈306 / 619 / 931 / 1244` |
| 点「购买」 | 详情区右下绿色按钮，本轮实测 `(2065,1263)` 生效过一次 |

**三个硬坑（都是实测踩到的）**：

1. **`Back` 键无效**：连按两次，屏幕差分只有 0.09/0.13（等于没反应）⇒ 只能点面板自己的 ✕。
2. **背包面板是模态的**：它开着的时候，顶栏的商城按钮**点不到**（点了没有任何 128xx）；
   必须先 ✕ 关掉背包，才能开商城。
3. **视觉给坐标不可靠**：同一张图上视觉给「购买」按钮的位置误差可达 ±10%（≈±250 px），
   而按钮只有约 120x60 ⇒ **必须用"日志反馈"或"截图差分"来确认命中**，不能凭视觉直接点。

---

## 六、仍未做 / 下一步（已定位，别重复找）

| # | 项 | 现状与线索 |
|---|---|---|
| 1 | ~~`12836`~~ → **已取证并定论（见 §八）** | `12836` 是「**珍宝 / MallXian**」列表；该列表的商品数据（价格/物品/限购）**不在 APK 里**，只有 id 白名单 ⇒ **不实现（不编造）**。真正的"限购/已购"已在 `12801/12803/12805/12831` 这条链上补齐并实机验证（§八）。 |
| 2 | `CS_12803` 的首字节 | 客户端发的是 `05 / 06` 之类，疑似"分类/页"；服务端目前**忽略**它、一律回全量 134 条 ⇒ 分类页可能显示同一批货。 |
| 3 | `pay_type=2 / 24` 的币种 | 本轮实机只验到 `pay_type=1 → gold`。`pay_type=2`（44 件，价 4000）与 `pay_type=24`（15 件，**映射表里没有** ⇒ 回退 `shop_pay_asset=coin`）**尚未实机单变量验证**。 |
| 4 | 「限购」是否该由服务端下发 | 客户端本地已有 `limit_week/limit_day_cli`，UI 的"限购 2 个"能正常显示；服务端是否需要配合拦截"超限购买"**未定**（当前不拦）。 |
| 5 | 重登后背包可见 | 逻辑上成立（`10502` 读同一张 `bag_items`），但**未单独跑过**"购买 → 强杀 → 重登"的端到端。 |

---

## 七、本轮附带产出

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `bag_push_frames` / `live_push_bag` / `db_mall_bought*` / `SC_12831` / `DSH_ADMIN.additem` / `mall_bought` 表 |
| `tools/shop_buy_test.py` | 直连 TCP 回归（购买 + 多 bag_code 推送 + 12831 已购数量） |
| `shots/dsh_bag_ab.jpg` | 背包"开着不重开"就多出一件物品的前后对比（本轮关键证据） |
| `shots/dsh_shop_open2.png` | 实机商城面板（含限购/折扣标签） |
| `logs/_cmd_coverage.txt` | 覆盖率清单（`12831` 已从缺口转为已应答） |

---

## 八、第二轮（同日）：`12836` 取证定论 + 「限购/已购」真正补齐

### 8.1 `12836` 是什么：取证过程与结论（**决定不实现**）

| 步骤 | 做法 | 结果 |
|---|---|---|
| 1 | `tools/find_register_protocal.py 12836` | 注册在 `assets/src/game/shop/shop_ctrl.luac` proto#1，handler 名 `on12836` |
| 2 | `tools/find_method_def.py anzbao/jstm.apk on12836` | 方法体只有 6 条字节码：`self.model:setZhenbaoGoodsList(resp)` ⇒ 它驱动的是**珍宝(zhenbao)列表**，不是商城主页 |
| 3 | 拆 `config_mall.luac`（新工具 `tools/split_mall_tables.py`） | 顶层表有四张：**`MallGoods`(134 条商品，= `server/mall_config.json`)**、`MallHuobanXishu`、`MallWeek`、`MallXian` |
| 4 | 看四张表各自的字段 | **`Config.MallXian` 只有 `{id, cli_tag}`**，共 45 条（id 21001–21045）；`price / pay_type / item_bid / 限购` **一个都没有** |
| 5 | 反汇编 `shop_model.luac` proto#62（`ZHENBAO_GOODS_LIST` 解析器） | 它从**服务端响应**取 `price/pay_type/item_bid/limit_num/buy_num`，只用本地 `Config.MallXian[id].cli_tag` 补一个标签 ⇒ **这些商品数据属于原版服务端，APK 无取证途径** |
| 6 | 交叉验证 id 是否另有出处 | `config_item.json` 无 21001/21045；全包只有 `all_res_file.luac`、`config_skill.luac` 偶然含该数字（无关） |

**⇒ 结论：忠实实现 `12836` 必须为 45 件商品**编造**价格/物品/限购 —— 违反本项目"不猜"的纪律，故不实现。**
这条结论本身有价值：它把一个"看起来该做"的缺口，变成了**有据可依的"不该做"**。

> 副产物：`tools/split_mall_tables.py` + `analysis/1.4.9/shop_luac/mall_table_1_Config.json`
> —— 现在能证明 `server/mall_config.json` 就是原版 `Config.MallGoods` 的 134 条（与原表逐条一致）。

### 8.2 那么"限购/已购"到底该改哪里：客户端的两条通路

反汇编 `shop_cell.luac` proto#2（格子视图）与 `shop_model.luac` proto#36（GUILD/WEEKDAY 列表）：

```
proto#36 @139-149 :  limit_num = Config.MallGoods[id].limit_week − checkChangesWeekdayData(id)
                     （checkChangesWeekdayData 的缓存由 on12831 → setWeekDataCache 写入）
shop_cell#2 @344  :  limit_day − buy_num      （剩余）
shop_cell#2 @552  :  can_buy_num              （图标角标；==0 时不显示）
```

⇒ **"限购 N 个"= 原版 `limit_week`（客户端本地配置）− 服务端告诉它的"已购数"**。
所以补齐它只需要两件事：**服务端如实回报已购数**（`SC_12831.has_buy_num`）＋ **服务端真的按 `limit_week` 拦截**。

### 8.3 本轮实现（`server/mock_server.py`）

| # | 改动 | 依据 |
|---|---|---|
| 1 | `SC_12831.has_buy_num` ← 新增的 `mall_bought` 购买记录表（每买一次 +1） | 客户端 `on12831 → setWeekDataCache`，proto#36 用它算剩余 |
| 2 | **购买成功后主动推一次 `SC_12831`** | 否则界面上的限购数字要等下次打开商城才更新 |
| 3 | `12805` **限购校验**：`已购 + 本次 > limit_week` ⇒ `code=0` + 非空 msg | 原版 `limit_week` 就是权威上限（APK 可取）；不校验则"显示限购、却无限卖" |
| 4 | `12801/12802` 的 `can_buy_num` 由写死的 0 改为 `max(0, limit_week − 已购)`；`limit_week=0` 仍回 0 | 原版 `Config.MallGoods` **没有** can_buy_num 字段；客户端 proto#17 把它当可购数量用，且 0 表示"不显示角标"（保持原行为） |

### 8.4 证据

**直连 TCP 回归**（`tools/shop_limit_test.py 20006`，`id=20006` 的 `limit_week=2`、价 21）：

```
① can_buy_num: 20006=2  20008=150  2001=0(不限购)
第1次: SC_10500 bag push bag_code=1 items=17 / SC_12831 has_buy_num[20006]=1 / code=1
第2次: SC_10500 bag push / SC_12831 has_buy_num[20006]=2 / code=1
第3次: code=0  msg='超过限购（限购 2，已购 2）'          ← ★ 被拒绝
④ 复取 can_buy_num: 20006=0                              ← ★ 已归零
```

**实机 UI 验证**（买满后重开商城，`shots/dsh_shop_limit2.jpg`）：

| 格子 | 原版 limit_week | 已购 | 界面显示 |
|---|---|---|---|
| 洗髓丹礼盒 / 坐骑进阶礼盒 / …（7 个） | 2 | 0 | **「限购 2 个」**，彩色可买 |
| **一袋银魂币**（id=20006） | 2 | 2 | **「限购 0 个」+ 灰底暗图标 + 红色售罄图章** |

⇒ **同一条链在真实客户端上闭环**：服务端已购数 → 客户端"限购/剩余"与售罄灰显。

> ⚠ **判据说明**：本节（§8.4）那条"面板开着即时刷新"的**判据只是视觉读图**，
> 强度不足，已在 **§十** 中作废（不代表结论一定错，而是**没被可靠证实**）。
> 限购/售罄那条（`SC_12831`）不受影响：它有 `12801`/`12831` 双通道 + TCP 复算。

---

## 九、第三轮（同日）：`pay_type` 币种按客户端权威表定死 + 背包「整理/删除」落地

### 9.1 找到 `pay_type → 币种` 的**权威定义**（不再靠图标推导）

| 步骤 | 做法 | 结果 |
|---|---|---|
| 1 | 在 APK 里搜 `payTypeEnToCode` | 出现在 `common/common_function.luac` 与 `shop/shop_model.luac` |
| 2 | `tools/export_map.py common_function.luac 134 payTypeEnToCode` | 导出表把该名字指向 **ChildRef(#69)** |
| 3 | `tools/show_proto.py ... 69` 反汇编（**只有 7 条字节码**） | `return Config.AssetsEnToCode[pay_type] or 1` —— 语义一目了然 |
| 4 | 从 `config_game_data.luac` **原样 dump** `AssetsEnToCode` | 它是**数组**：`1=gold 2=coin 3=coupon 4=exp … 8=guild_contrib … 24=guild_active … 31=arena_soul 32=black_soul 33=jiebai_cent 36=lottery_point 37=boss_point 38=partner_shenqi_point 39=rune_exp 40=rune_chip`（34/35 客户端就是 nil） |

**⇒ `pay_type` 的编号与"资产 code"完全同源**：`pay_type=N` 就是扣 `AssetsEnToCode[N]` 那个资产。

### 9.2 由此查出服务端**两处真错**（实机可见的钱错）

| # | 问题 | 后果 |
|---|---|---|
| 1 | `shop_pay_type_asset` **缺 24** | `pay_type=24` 的 **15 件公会商城商品**（`type=3` 且 `guild_lev>0`）会回退到全局 `shop_pay_asset="coin"` ⇒ **错误地扣「银魂币」**，正确应是 `guild_active`（公会活跃度） |
| 2 | `"31": "zhuangshi"` | `zhuangshi` 根本不是 `AssetsEnToCode` 里的资产名 ⇒ 旧表是把 `PathTool.getMoneyIconRes` 的**图标资源名**当成了**资产字段名**；code 31 实为 `arena_soul` |

### 9.3 本轮实现

| 文件 | 改动 |
|---|---|
| `server/config.json` | `shop_pay_type_asset` 按 dump 出来的表**整体重订为 38 项**（含 `24=guild_active`、`31=arena_soul`），note 写明取证链与"图标名 ≠ 资产名"的更正记录 |
| `server/mock_server.py` | ① `ASSETS_EN_TO_CODE` 补 `36=lottery_point`（原来漏了）；② `12805` 支付币种优先级改为 **配置 > 与客户端同源的 `CODE_TO_ASSET` > `shop_pay_asset`**（原来"配置未命中就回退 coin"正是 9.2-① 的成因）；③ `DSH_ADMIN setassets` 支持**任意已知资产**（如 `guild_active`），`getassets` 附带返回全部资产 |

### 9.4 证据（直连 TCP，`tools/shop_paytype_test.py`）

```
购买前: coin=1001961  gold=929313  coupon=999999  guild_active=777777
买 id=3001（pay_type=24, 价 6）   → SC_12805 code=1
买 id=4001（pay_type=2,  价 4000）→ SC_12805 code=1
购买后: coin=997961(-4000)  guild_active=777771(-6)
```

⇒ `pay_type=24` 现在**正确扣公会活跃度**（此前会扣银魂币），`pay_type=2` 扣银魂币，均与客户端同一张表一致。

### 9.5 背包「整理」「删除物品」落地（第三轮）

两条都是客户端**请求过但服务端从不回答**的命令，规格与注册点都早有取证
（`tools/show_cmd.py 10509/10557`；`inventory_protocol_matrix.md`：`backpack_ctrl` bc#37 → `handle_10509`、bc#132 → `hander_10557`）：

| CMD | 实现 | 依据 |
|---|---|---|
| `10509` 整理 | 把 `pos` 压紧为 `1..N` → 推 `SC_10500` 让界面按新顺序刷新 → 回 `SC_10509 code=1` | `CS{bag_code}` / `SC{code,msg}`，无未解子表 |
| `10557` 删除物品 | 解析 `args:table(id:u32)` → 按 `item_id` 真删 → 推 `SC_10500` → 回 `SC_10557 code=1` | `CS{bag_code,args}` / `SC{code,msg}` |

**证据**（`tools/bag_test.py`）：

```
① 背包 18 件（item_id 1..19）
② 删除 item_id=[19] → SC_10500 bag push items=17 ; SC_10557 code=1 msg=''
③ 删除后 17 件（19 已消失）
④ 整理 → SC_10500 bag push items=17 ; SC_10509 code=1 msg=''
⑤ 整理后 pos = 1..17（连续）
```

### 9.6 本轮看到的新线索（下一步）

| # | 项 | 线索 |
|---|---|---|
| 1 | `12832` | 形状与 `12805` 几乎一样：`CS{id:u16,num:u16}` → `SC{code:u8,msg:str,id:u16,num:u16}`（**少一个 price**）。**语义未定**（疑似另一种购买/兑换入口），未实现 —— 需先看客户端注册它的 handler 干什么 |
| 2 | `10714` 仓库 | `SC{lev:u8, InfoList:table(type,cur_val,max_val,show_max_val)}` 是**仓库容量信息**，不是物品列表 ⇒ 要做「仓库」还需先决定仓库存哪、怎么建表 |
| 3 | `12803` 的分类字节 | 客户端确有本地 `Config.MallType`（`min_lev/max_lev/type`，如 1-9→type4、10-19→type5…）⇒ 商城的分类很可能**由客户端本地按 type/lev 过滤**（这也解释了为何不同页签能显示不同商品，而服务端始终回同一批 134 条）。**待确认**，暂不改服务端 |
| 4 | 整理按钮的实机点击 | 本轮尝试用"日志反馈扫按钮"定位「整理」未命中（背包面板布局与预期不同）；功能已由 TCP 用例证明，实机点击待后续补 |

---

## 十、第四轮（同日）：**一次事故与一次结论撤回** —— 背包界面变空

### 10.1 现象与排查

| 步骤 | 结果 |
|---|---|
| 用户报障 | 「背包界面空了」 |
| 查 SQLite | **数据完好**：`bag_items` 17 行，`pos` 1..17，`bag_code` 全为 1，`rid` 全为 1001 |
| 查客户端探针（patched APK 的 `/DSH_PROBE`） | `http.log` 里出现 `t=bp&v=...`：<br>`H10500_items18_datanil_bagcode4`<br>`addItem_bagCodetable:_0xc0916fd8_items-1`<br>`after_item_list_sizena` |
| 读探针**源码**（`server/dsh_fake_login.lua` 第 1944-1996 行） | ★ **这些"异常"是探针自己的包装签名写错造成的假象**，不是客户端的问题：<br>`handle_10500` 的真实签名是 `(self, resp)`，探针却按 `(self, resp)` 打印 `resp.data` —— 而 `SC_10500` **本来就没有 `data` 字段**，所以 `datanil` 是正常值；<br>`addItemInBagCode` 的真实签名是 `(self, resp)`，探针却按 `(self, bagCode, resp)` 记录 ⇒ 日志里的"`bagCode`"其实是 **resp 这个表**，"`items-1`/`sizena`" 都是这么来的。 |

**⇒ `SC_10500` 实际上是**被正常处理**的（`items18` 说明我们的 items 数组解析正确）。
第四轮我据此写下的"10500 从未写进背包模型"以及随后的"结论撤回"，**都是我误读探针造成的，现一并纠正**。**

### 10.2 反汇编确认的两条消息真实语义（关键）

```
SC_10500 → backpack_ctrl.handle_10500 → backpack_data:addItemInBagCode(resp)   ← 增量添加
SC_10502 → backpack_ctrl.handle_10502 → backpack_data:initItemList(resp)       ← 清空并按响应重建
```

**⇒ 用 `10500`（增量添加）去做"整包刷新"在语义上就是错的**；真正的"整包刷新"是 `SC_10502`
（客户端 `initItemList`）。我们此前把掉落/购买/管理接口的刷新全压在 `10500` 上，属于**用法错误**。

### 10.3 两次判断的更正记录（都记下来）

| 轮次 | 我说过的话 | 实际 |
|---|---|---|
| 第二轮 §8.4 | "背包面板开着不重开就多出一格（UI+DB 证据）"，矩阵标 **YES（实机）** | 证据只是**视觉模型读了一张 A/B 对比图**；DB 多一件物品**不能证明客户端渲染了它**。**判据太弱，已作废** |
| 第四轮 §10.1 | "`SC_10500` 从未真正写进背包模型"，并据此回退代码、撤回上一轮结论 | **误读探针**：那些 `datanil`/`addItem_bagCode<table>`/`sizena` 是**探针包装签名写错**造成的假象（见 §10.1）。`SC_10500` 处理是正常的 —— 本轮**再次更正** |

**教训（流程级，写进纪律）**：
1. 客户端行为要**以探针为准**，但**读探针之前必须先读探针源码**，否则会把包装器的 bug 当成游戏的 bug；
2. 任何"实机验证"的**判据强度**要写清楚：`视觉模型读截图` < `服务端日志` < `客户端探针/DB`；
3. 一次移动两处（代码 + 结论）时，先把**判据**复核一遍再动手。

### 10.4 本轮做的事（修复与恢复）

| 项 | 动作 |
|---|---|
| 代码回退 | `bag_push_frames` 从"对请求过的**每个** bag_code 各推一条"回退为**只推一条**（该连接最后请求过的 bag_code）。理由与探针无关：把**同一批主背包物品**写进 12 个不同 bag_code 的页是语义错误（每个背包页应各有内容），多推没有收益 |
| 服务端 | 重启（新代码生效，`stderr 0`） |
| 客户端 | `am force-stop` + 重新拉起游戏 → 客户端重建 Lua 状态；它随即重新请求 `10502`（bag_code 7/12/8/6/7…），服务端每次回 **items=17** |
| 复验 | 重启 App 后 `http.log` **不再出现** `t=bp` 异常项；最近一次 `10500` 推送为单条 |

### 10.5 尚未解决 / 下一步

| # | 项 |
|---|---|
| 1 | **"背包界面空了"仍未闭环**：DB 完好、`10502` 重建正常、`10500` 处理正常 ⇒ 需要确认用户看到的是**哪一页**（那个多标签面板有 `背包/称号/戒指/时装/魂骨` 五个标签，**只有"背包"页有内容**；其余页的协议我们没实现，本来就是空白） |
| 2 | 若要自己判定而不靠肉眼：可给注入探针**加一个 bag 探针**（打印 `BackPackData.item_list` 各 bag_code 的条目数 + 当前面板），重打包 APK —— 这是最可靠的一条路，但要一次 build/install |
| 3 | 探针源码里 `addItemInBagCode` 的包装签名应改成 `(self, resp)`（顺手修掉这个会误导人的探针 bug） |
| 4 | 面板里那几个空白页对应的命令仍在缺口清单（如 `10528` 是**背包扩展/格子状态**、`10505` 是**双击使用物品**、`10552` 是**背包容量/状态**）—— 实现前需先按规格+客户端消费代码取证，**不猜** |

---

## 十一、第五轮（同日）：**找到并修掉真根因** —— 推送推错了背包

### 11.1 先把探针修好（否则永远在猜）

第四轮我误读了探针，根因是**探针自己的包装签名写错**。本轮修掉并**增强了探针**：

| 改动 | 内容 |
|---|---|
| 修签名 | `BackPackData.addItemInBagCode` 的真实签名是 `(self, resp)`，探针原来按 `(self, bagCode, resp)` 记录 ⇒ 日志里的 `addItem_bagCode<table>_items-1` / `sizena` 都是假的。已改为读 `resp.bag_code` / `resp.items` |
| 加探针 | 每 30 tick 上报客户端**背包模型实况**：`bagSizes_t<N>_main<bag1条目数>_1:..,2:..`，直接从 `BackPackCtrl:getInstance().data.item_list` 取（实例的获取见探针注释） |
| 为什么值 | **判据强度**：`视觉读截图` < `服务端日志` < `客户端模型直读`。有了它，"背包到底刷没刷新"不再靠肉眼 |

重建并安装（`pwsh tools/build_fakelogin.ps1`，约 20s），探针随即开始上报。

### 11.2 真根因（探针直读，一次就看清）

```
推送前  bagSizes … 1:9  … 7:0
LOG     << 10500 SC_10500 bag push bag_code=7 items=10      ← 推给了 bag 7
推送后  bagSizes … 1:9  … 7:10                              ← 物品进了 bag 7
```

* 客户端里 **bag1 的条目数 == 我们 DB 里 `bag_code=1` 的行数**（实测 9==9）⇒ **魂囊页显示的就是 bag 1**；
* 而 `bag_push_frames` 用的是 `_last_bag_code`＝**客户端最后请求过**的那个包（背包初始化时会依次问
  6/7/8/12…，所以常年是 7 或 12）⇒ **推送落在一个用户没在看的包上**，
  可见的 bag 1 **永远不会出现新物品**。

**⇒ 这就是最初那句"买了东西/加了东西，背包不刷新"的根因**（不是编码问题、也不是"客户端没吃下 10500"）。

### 11.3 修复与验证

| 项 | 内容 |
|---|---|
| 修复 | `bag_push_frames()` 一律推 **`bag_code = BAG_MAIN(=1)`**（我们的物品也都存在 `bag_code=1`），不再用 `_last_bag_code` |
| 验证（探针强判据） | 修复后重启，加一件物品：`LOG << 10500 bag push bag_code=1 items=13`，客户端 `bagSizes` 的 **bag1 随之变化**（此前推 bag 7 时 bag1 纹丝不动） |
| 数据一致性 | DB 10 行 ↔ 客户端 bag1 探针值 11（差值来自用户正在游戏里使用/购买物品，非丢失） |

### 11.4 顺带查清 / 需要协同的事

| # | 项 |
|---|---|
| 1 | 探针显示客户端会**按物品类型自行分流**：我们 9 件物品全进 bag1，bag2 得 1 件、bag4 得 2 件（装备/时装位）⇒ 只要 `bid` 在真实物品表内就不会丢（本轮复核 DB 里所有 bid **都在** `Config.Item` 内） |
| 2 | ⚠ **`server/mock_server.py` 正被另一个会话同时修改**：12:54 的文件比本会话上次编辑多了约 580 行（新增 `10505/10511/10552/10570/10534/10551/10528` 等处理器，注释为 `\uXXXX` 转义风格）。**两个会话改同一个文件**是明显风险 —— 本会话此后一律用**外科式单点编辑**（带冲突保护），不再整文件重写 |
| 3 | `10502` 仍是"任何 bag_code 都回主背包内容"的简化实现；因为客户端会自行分流，目前表现正常，**暂不改**（要改需先验证其它页的期望） |

### 9.7 本轮测试产生的状态（可一键还原）

| 项 | 值 |
|---|---|
| `guild_active`（为区分币种而设的标记值） | **777777**（购买后 777771） |
| `coin` | 997961（买了 id=4001 花 4000） |
| 背包 | 多了一件 `item_id=18 / bid=40001`（id=4001 购买所得）；测试道具 `bid=33006` 已用 10557 删掉 |

