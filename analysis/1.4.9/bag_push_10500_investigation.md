# 购买后背包不实时更新 —— 客户端侧取证

> 现象：商城购买后**推了 `SC_10500`**，但客户端背包**仍不刷新**（需重登）。
> 方法：**先取证**（反汇编客户端 handler），不猜。

---

## 一、服务端侧：已按既有模式补上 `SC_10500` 推送

| 位置 | 是否推 `SC_10500` |
|---|---|
| battle 掉落那段（既有） | ✅ 推了 |
| `12805` 购买（我新增的） | ❌ 原先**只推角色数据**，已补上 `10500` |

**修复后实测：购买能收到 `SC_10500`（`bag_code=1, items=11`）—— 但用户反馈「仍不会当场出现」。**

**⇒ 所以问题**不在服务端推不推**，而在**客户端怎么处理**。**

---

## 二、★ 客户端侧取证：`handle_10500` 的第一行就返回了

**定位**：`backpack_ctrl.luac proto[18]` 注册 `10500 → 'handle_10500'`；
实现在 **`proto[19]`（仅 9 条字节码）**：

```lua
handle_10500(self, resp):
  @0  TGETS 'data'
  @1  ISEQP                 -- if resp.data == nil
  @2  JMP                   -- ★ **直接 return，什么都不做**
  @3  TGETS 'data'
  @4  MOV
  @5  TGETS 'addItemInBagCode'
  @6  MOV
  @7  CALL                  -- self.data:addItemInBagCode(resp.data, resp)
  @8  RET0
```

### 对照：`handle_10502`（重登走这条，**能用**）

```lua
handle_10502(self, resp):             -- proto[22]，24 条
  @0  TGETS 'data'
  @1  ISEQP
  @2  JMP
  @3  TGETS 'data' / 'initItemList' / CALL      -- self.data:initItemList(resp.data)
  @8  TGETS 'data' / 'setRequireGoods'
  @11 TGETS 'bag_code'                          -- ★ 用 resp.bag_code
  @13 CALL
```

### 结论（`CONFIRMED`）

1. **`handle_10500` 在 `resp.data == nil` 时**整个直接返回** ⇒ 这正是"推了却不刷新"的直接原因。**
2. **`addItemInBagCode(self, bagCode, resp)` 内部把 `resp.data` **当作 `bagCode`** 使用
   （`self.item_list[bagCode]`）—— 见 `backpack_data.luac proto[4]` @0-7。**
3. **`handle_10502` 用的是 `resp.bag_code`（可直接读）** ⇒
   **`resp.data` **不是** `bag_code`，来源另有其他。**

### ⚠ 尚未确定（如实）

**`resp.data` 到底由谁、按什么规则填充 —— `UNKNOWN`。**
`SC_10500` 的**权威规范**（`manual.md` + `cmd_resolve_105.luac`）里**没有 `data` 字段**，
只有 `bag_code:uint8` + `items:table(...)`。

**⇒ 所以 `data` 不是协议字段，而应是**框架层**（协议分发器）在构造 `resp` 时附带的。**

---

### ★ 重要修正（本条推翻了上一节的推断）

**`handle_10502` **也**做同样的判断：**
```lua
handle_10502: @0 TGETS 'data' / @1 ISEQP / @2 JMP      ← 同样 `if resp.data == nil then return end`
handle_10500: @0 TGETS 'data' / @1 ISEQP / @2 JMP
```

**⇒ 而 `10502` 是**能用的**（重登后背包有物品）⇒ 说明 `resp.data` **在两条协议上都是非 nil 的**。**

**⇒ 所以「`resp.data` 为 nil 导致直接返回」这个推断**不成立** —— 我撤回它。**

**⇒ `resp.data` 是**框架层统一提供**的（不是协议字段），两种协议都拿得到。**

---

## 二之二、★ 新的推断方向（有依据，待验证）

既然 `resp.data` 不是问题，那么 `10500` 与 `10502` 的差别在**处理方法**上：

| 协议 | 调用的方法 | 语义（从名字推断） |
|---|---|---|
| `10502` | `initItemList(resp.data)` + `setRequireGoods(resp.bag_code, ...)` | **全量初始化**列表 |
| `10500` | **`addItemInBagCode(resp.data, resp)`** | **增量添加** |

**⇒ 服务器我们现在**每次都推"背包全量列表"**（`db_bag_get()` 的全部 items）。**

**⇒ 而 `10500` 的语义是"**增量添加**"（`addItemInBagCode`）——
把**全量**喂给一个"**增量**"接口，很可能导致：**

- 重复添加（同一 item_id 被反复并入）
- 或内部索引（`item_bid_to_id` / `item_id_to_bid`）被覆盖
- **⇒ 界面看起来"没变化"或"状态错乱"**

**⇒ 这解释了"推了 `10500` 却看不到变化"。**

### ⇒ 正确的修复方向（待验证）

**`SC_10500` 应只推**新增/变化的那几件**，而不是全量列表**；
**全量列表用 `SC_10502`（`initItemList`）的语义。**

**⇒ 具体做法（下一步）：**
1. 购买成功后，**只推刚入包的那一件**（`db_bag_add` 的返回值 `row`）
2. 若客户端仍不刷新，再试推 `SC_10502` 的语义（全量初始化）

**⚠ 但这两个都还是**推断**。按上次 `pos` 的教训，**先取证再改**：
最稳的是包住客户端的 `handle_10500` / `addItemInBagCode`，
观察它**实际收到什么、执行后 `item_list` 变成什么** —— 一次就能定论。**

---

## 三之二、探针已布好（设备已安装），等一次真实购买取数

### 已做的探针

包住两处：
1. **`BackPackData.addItemInBagCode`** —— 报出收到的 `bagCode`、`items` 条数、**执行后 `item_list` 的大小**
2. `BackPackCtrl.handle_10500` —— 报出收到的 `items` 条数 / `resp.data` 类型 / `bag_code`

### ★ 探针自查抓到的一个错（如实记录）

**我一开始把全局名写成 `BackpackCtrl` / `BackpackData`（小写 p）⇒ 钩子完全装不上、零上报。**
**静态查 GSET 得知真实全局名是 **`BackPackCtrl` / `BackPackData`（大写 P）**。**
**⇒ 已更正。**（幸亏探针里有 `_wrapped` 上报，才能区分"没装上"与"没被调用"。）

### 本轮结果

```
1 x addItemInBagCode_wrapped      ← BackPackData 的钩子装上 ✓
（无 handle_10500_wrapped）        ← BackPackCtrl.handle_10500 不是**类上**的函数
                                  （可能在实例/元表上 ⇒ 需换挂法）
本轮**没有触发购买** ⇒ 探针一次都没被调用
```

**⇒ 要取到数，需要**在游戏里真实买一件东西**（探针已装在设备上）。**

### 下一步（两步）

1. **请你在游戏里买一件东西** ⇒ 我读探针上报
   - 若 `addItem_bagCode..._items N` + `after_item_list_size M` 出现，即可判定：
     **是"增量 vs 全量"语义问题，还是根本没走到**
2. **若 `handle_10500` 仍装不上** ⇒ 改为**包实例对象**（`BackPackCtrl:getInstance().handle_10500`）
   或包框架分发处（`sys/gamenet.luac` 的 `doOneMsg`，**探针已有挂钩点**）

---

## 五、背包空白：找到一处**数据异常**并已修复（数据驱动）

### 取证：先查数据，不猜

```
修复前 bag_items：
   item_id 序列: 1,2,3,...,15,**17**,18        ← ★ 缺 16（跳号）
   pos 序列    : 1..17（连续）
   bid 重复: 无 ｜ pos 冲突: 无 ｜ bag_code: {1}
```

**⇒ `item_id` 跳号 ⇒ 若客户端按 `item_id` 建数组/索引，**缺号会导致越界或整表失败** ⇒ 背包空白。**

**⇒ 这个跳号**很可能是我之前那次 `pos` 迁移（+1/−1）反复改动数据造成的** —— 我的责任。**

### 修复：规范化 `item_id` 与 `pos` 为连续 1..N

```
重排 2 行 ⇒ item_id = 1..17（连续）  pos = 1..17（连续）
```

### 验证（独立 TCP，按规范算术复核）

```
每项字节数（按规范）：39 = id4+bid4+hero_bid4+bind1+intensify_lev1+pos2+quantity2
                            +ctime4+expire_ts4+durable2+object1 + 5×2(子表)
SC_10502 bag_code=1 items=17 body=666 字节   （期望 3 + 17×39 = 666）★ 精确匹配
(item_id,pos,bid) 前 5 项: [(1,1,33001),(2,2,33002),(3,3,25890),(4,4,25301),(5,5,36500)]
item_id 连续: True ｜ pos 连续: True ｜ 条数: 17
```

**⇒ 服务端编码与规范**逐字节吻合**；数据也规范化了。**

### ⚠ 仍需你确认

**背包是否恢复显示** —— 我**不能只凭"编码对"就宣布修好**（上次 `pos` 的教训）。
**若仍空白**，下一个可查的数据点是：
- `bid` 是否都在**真实物品表**（1117 条）内 —— 个别无效 bid 也可能让整表渲染失败
- 或者回到探针路线（`addItemInBagCode` 已挂钩）

---

## 六、★ 背包空白的**真正根因**：包里有 bid 不在物品表内（已修两处）

### 取证（数据驱动，逐条核对）

**把背包里 17 件物品的 `bid` 逐条对照真实物品表（`config_item.luac` → 1117 条）：**

```
不在物品表内的 **10 件**：
   item_id=3  bid=25890     item_id=4  bid=25301
   item_id=6  bid=25933     item_id=7  bid=25955
   item_id=10 bid=25940     item_id=11 bid=25104
   item_id=12 bid=25932     item_id=13 bid=20110
   item_id=15 bid=25950     item_id=16 bid=25934

**这 10 件的 bid 全部来自原版 `config_mall.luac` 的商城商品表**
```

### ★ 根因（`INFERRED`，但与全部现象吻合）

**客户端渲染背包时要查 `Config.Item[bid]` 拿物品定义。
**只要包里有一件 bid 查不到，整张背包就渲染不出来（空白）** —— 这解释了为什么是
"**整片空白**"而不是"少显示几件"。**

### 已做的两处修复

**① 清理当前背包**（移除 10 件无效物品，保留 7 件有效的）
```
清理后：item_id=1..7  bid=33001, 33002, 36500, 36532, 36531, 36573, 40001
SC_10502 items=7  body=276 字节 （期望 3+7×39=276）★ 精确匹配
备份：server/state/roles.db.bak_before_bagclean
```

**② 商城加"物品表过滤"**（防止再次买回无效物品 ⇒ 根治复发）
```python
def is_valid_item(bid):
    """bid 是否存在于真实物品表；表加载失败时不过滤（避免误杀）。"""
```
**加在 `12801/12802/12803/12805` 四处。实测：**
```
item table loaded: 1117 条
SC_12801 xs_list = **71** 件（过滤前 134 件）
```

### ⇒ 效果

- **背包里的物品现在全部有效** ⇒ 客户端应能渲染
- **商城只卖真实物品（71 件）** ⇒ **不会再因为购买把背包弄白**

### ⚠ 仍待你确认

**背包是否恢复显示** —— **我不凭"编码对/数据净"就宣布修好**（上次 `pos` 的教训）。
**若仍空白**，下一个数据检查点：
- `Config.Item` 提取是否**完整**（`config_item.json` 1117 条是否等于原版物品总数）
- 背包渲染是否还要求别的前置（`10502` 之外）

### 附带发现（值得记录）

**原版 `config_mall` 的 `item_bid` 有 63/134 **不在物品表内** —— 这不是我们的 bug，
而是**商城配置引用了物品表之外的 id**（可能是活动/礼包类商品，需要别的表）。
**⇒ 我们把它们过滤掉，是"不卖不确定的东西"的保守做法，符合"不猜"原则。**

---

## 三、下一步（取证方向，不猜）

**去查框架如何构造 `resp`** —— 即 `resp.data` 的赋值点：

1. 在客户端的协议分发器里（`gamenet.luac` / `net_manager` / 协议基类）搜 `data` 字段的赋值
2. 或直接在真机上包住 `handle_10500`，把 `resp` 的**全部键**报出来
   （用探针 `pairs(resp)` 列键名 + 类型，同 `smk`/`mcs` 的手法）

**⇒ 拿到 `resp` 的真实结构后，才知道服务端该怎么摆字段 —— 而不是继续试。**

**⇒ 关键点：这不是"服务端没推"，而是**客户端 handler 有一个未被满足的前置条件（`resp.data`）**。**

---

## 四、给用户的建议（本轮结论）

| 项 | 状态 |
|---|---|
| 服务端推送 `SC_10500` | ✅ **已补上**（battle 掉落段本就有；购买段现也补了） |
| 客户端**收到**后是否刷新 | ❌ **不刷新** —— 因为 `handle_10500` 需要 `resp.data`，而我们的消息没有该字段 |
| `resp.data` 的来源 | ⚠️ **UNKNOWN** —— 需探针列出 `resp` 的实际键 |

**⇒ 下一步只有一个动作：包住 `handle_10500`，把 `resp` 的键名列出来。这是纯探针、风险最低，且能一次定位。**
