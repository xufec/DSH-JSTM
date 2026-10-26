# 1.4.9 商城协议矩阵

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> **字段全部来自权威 spec**：`python tools/proto_spec.py cmds <CMD>`
> （读 `assets/src/config/protocal/cmd_resolve_128.luac` 的
> `AutoConstruct(dir, cmd, {'字段__类型', ...})`，数组顺序即字段顺序）。

---

## 一、商城协议矩阵

| 功能 | CMD | 方向 | 请求字段 | 响应字段 | 客户端模块/处理函数 | 服务端 | 状态 |
|---|---|---|---|---|---|---|---|
| 商城商品列表 | **12801** | C→S 空 / S→C | （空） | `guild_shop_lev:u32, xs_list:T(id:H, item_bid:I, bind:C, pay_type:C, old_price:I, price:I, type:C, ico:C, left_time:I, can_buy_num:H)` | `shop_ctrl` / `shop_model` | ✅ 134 件 | **已验证** |
| 商品推送/同步 | **12802** | S→C（部分场景 C→S） | （空） | `id:u16, xs_list:T(同上)` | 同上 | ✅ 已实现 | 已确认 |
| 动态价格 | **12803** | C→S 空 / S→C | （空） | `item_list:T(item_bid:I, price:I)` | `shop_model` proto#? `request12803` | ✅ 已实现 | **已验证** |
| **买商城商品** | **12805** | C→S | `id:u16, num:u16` | `code:u8, msg:s, id:u16, num:u16, price:u32` | `shop_ctrl` | ✅ 已实现 | **已验证** |
| 已购数量 | **12831** | C→S 空 / S→C | （空） | `id_list:T(id:u16, has_buy_num:u16)` | `shop_model` `request12831` | ✅ 已实现 | **已验证** |
| **珍宝/限时商店货物** | **12836** | C→S 空 / S→C | （空） | `goods_list:T(id:H, item_bid:I, bind:C, pay_type:C, old_price:I, price:I, limit_num:C, buy_num:C)` | `shop_model` proto#61 `requestZhenbaoData`→`request12836`；proto#62 `setZhenbaoGoodsList` | ✅ **本阶段实现（45 件）** | **已验证** |
| **珍宝购买** | **12837** | C→S | `id:u16, num:u16` | `code:u8, msg:s, id:u16, num:u16`（**无 price**） | `shop_ctrl` proto#26 `request12837` | ✅ **本阶段实现** | **已验证** |
| 副本商店货物 | **12838** | C→S 空 / S→C | （空） | `goods_list:T(同 12836)` | `shop_model` proto#65 | ✅ 本阶段实现（复用珍宝表·标注） | **已验证** |
| 副本商店购买 | **12839** | C→S | `id:u16, num:u16` | `code:u8, msg:s, id:u16, num:u16` | `shop_ctrl` proto#10 | ✅ 本阶段实现 | 已确认 |
| **兑换商店货物** | **12840** | C→S 空 / S→C | （空） | `goods_list:T(id:H, new_item_bid:I, new_item_num:I, new_bind:C, item_bid:I, item_num:I, limit_num:C, buy_num:C)` | `shop_ctrl` proto#6 `request12840` | ✅ **本阶段实现（20 条）** | **已验证** |
| **兑换** | **12841** | C→S | `id:u16, num:u16` | `code:u8, msg:s, id:u16, num:u16` | `shop_ctrl` proto#12 | ✅ **本阶段实现** | **已验证** |
| 副本商店2货物 | **12842** | C→S 空 / S→C | （空） | `goods_list:T(同 12836)` | `shop_model` proto#66 | ✅ 本阶段实现（复用珍宝表·标注） | **已验证** |
| 副本商店2购买 | **12843** | C→S | `id:u16, num:u16` | `code:u8, msg:s, id:u16, num:u16` | `shop_ctrl` proto#11 | ✅ 本阶段实现 | 已确认 |

### 1.1 ★ 三个易错点（权威 spec 与直觉不同）

1. **`SC_12836/12838/12842` 的 `goods_list` 与 `SC_12801` 的 `xs_list` **不是同一结构**：**
   - `12801.xs_list` = `… type:C, ico:C, left_time:I, can_buy_num:H`
   - `12836.goods_list` = `… limit_num:C, buy_num:C`（**没有 type/ico/left_time**）
2. **`SC_12837/12839/12841/12843` 没有 `price` 字段**，而 `SC_12805` **有** `price:u32`。
3. **`SC_12840` 是"交换"不是"购买"**：`item_bid × item_num` → `new_item_bid × new_item_num`。

---

## 二、客户端请求入口（`game/shop/shop_ctrl.luac` 实测）

| 方法 | proto | 发出的 CMD |
|---|---|---|
| `request12803` | proto#29 | 12803 |
| `request12831` | proto#20 | 12831 |
| `request12836` | proto#24 | 12836 |
| `request12837` | proto#26 | 12837 |
| `request12838` | proto#4 | 12838 |
| `request12839` | proto#10 | 12839 |
| `request12840` | proto#6 | 12840 |
| `request12841` | proto#12 | 12841 |
| `request12842` | proto#5 | 12842 |
| `request12843` | proto#11 | 12843 |
| `request12832` | proto#22 | 12832 |

⇒ **商城一共只用 11 个 CMD**；本阶段结束时**全部已实现**。

---

## 三、物品「使用」链路（使货物"可使用"）

| 功能 | CMD | 请求 | 响应 | 服务端 |
|---|---|---|---|---|
| 请求背包 | 10502 | `bag_code:u8` | `bag_code:u8, items:T(16 字段)` | ✅ |
| 推送背包 | 10500 | —（纯推） | `bag_code:u8, items:T(同上)` | ✅ |
| 数量变化 | 10501 | —（纯推） | 见 spec | ✅ |
| 删除物品 | 10503 | —（纯推） | 见 spec | ✅ |
| **双击使用物品** | **10505** | `code:u8, item_id:u32, use_num:u16, type:u32, bid:u32` | `code:u8, msg:s, item_bid:u32` | ✅ 闭环：扣数量 → 归零则删行并推 10503，否则推 10501 → 回 10505 |

`10505` 的类名为 `CSDblclickItem_10505` / `SCDblclickItem_10505`
—— **直接证实它就是"双击物品（使用/装备）"**（独立于 `cmd_table.json` 的第二条证据）。

---

## 四、端到端验证

工具：`python tools/test_shop_e2e.py`（直连 TCP 9000，按权威 spec 编解码，
**不依赖手机客户端**）。实测输出：

```
① CS_12801  → SC_12801 xs_list=134 条 (3222 字节)                    OK
② CS_12836  → SC_12836 goods_list=45 条 (812 字节)   ← 珍宝不再为空    OK
③ CS_12837  → SC_12837 code=1(TRUE) id=21001 num=1                   OK
④ CS_10502  → 背包已有 item_bid=33001, quantity=1                    OK
⑤ CS_10505  → SC_10505 code=1(TRUE) item_bid=33001                  OK
⑥ CS_12836  → buy_num 已更新为 1                                    OK
⑦ CS_12840  → goods_list=20；CS_12841 → code=1(TRUE)                OK
结论: 全部通过 ✅
```
