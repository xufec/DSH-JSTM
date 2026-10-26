# 绝世唐门 1.4.9 私服 —— Phase F：商城系统修复 · 状态报告

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 1.4.11 未参与任何判定。
> 环境：`server/mock_server.py`（TCP 9000 / HTTP 8080），模拟器 `127.0.0.1:16384`。

---

## 一、用户提出的三件事 → 处理结果

| # | 用户诉求 | 结果 | 证据 |
|---|---|---|---|
| 1 | **丰富市场的货物** | ✅ 「常用/热卖」**134 件**（`MallGoods 110 + MallWeek 24`，**原版配置**）；另新增**珍宝 45 件** + **兑换 20 条配方** | `SC_12801 xs_list=134 (3222B)`、`SC_12836 goods_list=45 (812B)`、`SC_12840 goods_list=20` |
| 2 | **商城货物可购买、可使用** | ✅ 购买：`12805`（已有）+ **`12837`/`12839`/`12841`/`12843`（本轮新增）**；使用：`10505` | `SC_12837 code=1(TRUE)` → `背包已有 item_bid=33001 quantity=1` → `SC_10505 code=1(TRUE)` |
| 3 | **珍宝为空** | ✅ **已修复**：珍宝从 **0 件 → 45 件** | `SC_12836 goods_list=45 (812 字节)` |

**端到端自测全部通过 ✅**（`python tools/test_shop_e2e.py`，7 步，直连服务端按权威 spec 编解码）。

---

## 二、★ 三个真实根因（都不是"猜"，是查出来的）

### 根因 1：服务端**完全没实现 `12836`** ⇒ 珍宝页签必然是空的

客户端 `game/shop/shop_model.luac`：

```
proto#61  requestZhenbaoData()   ->  self.ctrl:request12836()
proto#62  setZhenbaoGoodsList(resp)  <-  读 resp.goods_list
proto#63  getZhenbaoGoodsList()      ->  zhenbaoList
```
`shop_normal_view.luac` proto#24 用 `getZhenbaoGoodsList()` 填 **ZHENBAO（珍宝）** 页签。

**⇒ 珍宝页签的数据只可能来自服务端的 `SC_12836`。** 而服务端此前
`12836/12837/12838/12839/12840/12841/12842/12843` **一个都没实现**（grep 零命中）。

### 根因 2：`config_mall.luac` 里有**五张表**，此前只提了一张半

```
Config: MallGoods(110) · MallWeek(24) · MallXian(45) · MallType(4) · MallHuobanXishu(14)
```
而 `server/mall_config.json` 只有 **134 = MallGoods + MallWeek**（id 集合已核对完全相等）。
**`MallXian`（珍宝的 45 个 id）从未被提取。**

### 根因 3 ★：**`main()` 漏调 `db_bag_init()`** ⇒ **买到了但物品进不了背包**

```
main(): db_init() · db_init_bag_volume() · db_init_equip() · db_store_init() · db_init_levgift()
                                            ↑ 唯独漏了 db_bag_init()
```
后果：从旧快照还原数据库（或全新库）时 **`bag_items` 表不存在**，
`db_bag_add()` 抛 `no such table: bag_items`，
表现就是 **购买扣了钱、物品却没进背包**（正是用户报障"买不到"的直接成因）。

实测日志：`!! 12837 购买：扣钱成功但入包失败 item=33001`、`no such table: bag_items`。
**已修**：`main()` 增加 `db_bag_init()`（并附注释说明踩坑）。

### 附带修掉的一个货币 bug

`12805/12837` 的余额校验原先读的是 **`role_assets` 表**，而 `gold` 存在 **`roles` 行**里
⇒ `gold=1000` 的角色买 50 元的东西会报 **"gold 不足（需 50，有 0）"**。
**已改为读 `role_state()` 的合并后有效值**，并改用 `db_set_assets()` **绝对值**写入
（增量写在"roles 有值、assets 无行"时会算出 -50 而不是 950）。

---

## 三、原版数据 vs 兼容数据（**严格区分**）

| 项 | 来源 | 标记 |
|---|---|---|
| 常用/热卖 **134 件**（含 item_bid/price/type/limit_week） | **原版** `Config.MallGoods` + `Config.MallWeek` | **原版** ✅ |
| 珍宝货物的 **id（21001–21045）与 cli_tag** | **原版** `Config.MallXian` | **原版** ✅ |
| 珍宝货物的 **item_bid / price / pay_type / bind / limit_num** | `MallXian` **没有**这些字段；由 `tools/build_shop_goods.py` 从**真实物品表**补 | **`IMPLEMENTATION_FALLBACK`** ❌ **不是原版数值** |
| 兑换商店 **20 条配方** | 原版配方不在 APK 内 | **`IMPLEMENTATION_FALLBACK`** ❌ |
| 副本商店（12838/12842）货物 | 原版数据不在 APK 内；本阶段**复用珍宝表** | **兼容做法**（日志里带 `［复用珍宝表·兼容做法］` 标记） |

> **为什么珍宝内容必须自己补**：`Config.MallXian` 45 条**字段集合唯一且只有 `{cli_tag, id}`**
> （与 `MallGoods`/`MallWeek` 交集均为 0）。原版珍宝卖什么、多少钱属**原版服务端数据**，
> APK 内无取证途径 —— 与「怪物 HP」「逐级属性成长」同类缺口。

---

## 四、服务端改动清单

| 位置 | 改动 |
|---|---|
| `main()` | **补 `db_bag_init()`**（根因 3） |
| 新增 `mall_zhenbao()` / `MALL_ZHENBAO_PATH` | 加载 `server/mall_zhenbao.json`（45 件） |
| 新增 `mall_exchange()` / `MALL_EXCHANGE_PATH` | 加载 `server/mall_exchange.json`（20 条配方） |
| 新增 `build_goods_list_sc12836()` | 编码 `12836/12838/12842` 的 `goods_list`（含与 12801 结构差异的注释） |
| 新增 `build_goods_list_sc12840()` | 编码 `12840` 的交换配方 |
| 新增 `shop_pay_asset()` / `shop_find_goods()` | 抽出 `pay_type→资产` 映射与按条目 id 查货 |
| 新增处理分支 | **12836/12838/12842**（列表）、**12837/12839/12843**（购买）、**12840**（列表）、**12841**（兑换） |
| 修改 | `12805` 与新增购买路径的**余额校验 + 绝对值扣费** |

新增数据文件：`server/mall_zhenbao.json`（45）、`server/mall_exchange.json`（20）
新增/修改工具：`tools/build_shop_goods.py`、`tools/audit_mall.py`、`tools/test_shop_e2e.py`

---

## 五、复现步骤

```powershell
# 1) 提取 5 张商城表 + 生成货物（可重复执行）
python tools\dump_drop_config.py analysis\1.4.9\shop_luac\config_mall.luac `
       --json analysis\1.4.9\shop_luac\_mall_all.json
python tools\build_shop_goods.py          # 核对 134、生成 珍宝45 + 兑换20
python tools\audit_mall.py                # 看 type 分布 / 过滤情况

# 2) 起服务端
pwsh tools\restart_server.ps1

# 3) 端到端自测（不需手机客户端）
python tools\test_shop_e2e.py
```

---

## 六、诚实交代：仍未确定 / 未验证的

| # | 项 | 状态 |
|---|---|---|
| 1 | **手机客户端上的画面确认** | ⚠️ **未做**。客户端启动仍不稳定（Phase D/E 起就反复卡在加载 100%/TCP 重连循环），本轮改用**直连服务端的协议级 E2E** 验证（7 步全过）。**协议层已确证，UI 层未肉眼确认。** |
| 2 | 原版珍宝/兑换/副本商店的**真实货物与价格** | **`UNKNOWN`**（APK 内无此数据，见 §三） |
| 3 | `12802`（商品推送）的触发时机 | 已实现应答，但**原版何时主动推**未追证 |
| 4 | 其余页签（兑换/试炼/宗门/声望/积分/金魂币） | 客户端共只用 **11 个商城 CMD**，本轮**已全部实现**；但这些页签是否还有**非 128xx 系列**的数据源，未逐一追证 |
| 5 | `MallHuobanXishu`（14 条伙伴系数） | 未追（非商城主流程） |
| 6 | `cli_tag`（八折/五折/HOT）的展示语义 | 取值已知，语义 `INFERRED` |

---

## 七、交付物索引

| 文件 | 内容 |
|---|---|
| `analysis/1.4.9/shop/mall_protocol_matrix.md` | 商城协议矩阵（12 个 CMD，含三个"与直觉不同"的易错点） |
| `analysis/1.4.9/shop/mall_data_model.md` | 五张配置表 + 页签→数据源映射 + 原版/合成区分 |
| `server/mall_zhenbao.json` | 珍宝 45 件（id 原版 / 内容 FALLBACK） |
| `server/mall_exchange.json` | 兑换 20 条配方（FALLBACK） |
| `tools/build_shop_goods.py` | 提取 5 表 + 生成货物 + 核对 |
| `tools/audit_mall.py` | 商城数据审计 |
| `tools/test_shop_e2e.py` | 商城端到端自测（购买/使用/兑换） |
| `server/mock_server.py` | Phase F 全部改动 |
