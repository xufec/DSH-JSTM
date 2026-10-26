# 真实购买收口：`12832` / `13402` 接入共用购买内核（2026-09-19 · round42）

> 承接 round41（协议收口）。本轮把**两个"购买"入口**从"假成功 / 未开放"改成**真扣费 + 真发货**。

---

## 一、问题

| 命令 | 原状 | 危害 |
|---|---|---|
| **`12832`** | **桩**：只回 `code=1`，**不扣费、不发货** | 客户端显示"购买成功"而实际什么都没发生 ⇒ **比沉默更糟**（玩家以为买到了） |
| **`13402`** | 在 `_UNSUPPORTED_ACTION_CMDS` 里回 `code=0 未开放` | 134xx 限购商店点"购买"永远失败 |

而本服务端其实**早就有**完整的购买实现 —— 在 `12805`（含选币/限购/扣费/发货/记限购），
只是没有被另外两个入口复用。

**`12832` 的真机 id 已核实落在 `mall_config` 空间内**：
抓包样本 `4e24 0001`（id=20004）、`4e33`（20019）、`4e21`（20001）、`4e37`（20007）
—— 全部存在于 `server/mall_config.json`（`type=20`，`limit_week=1~2`）。

---

## 二、做法：抽共用内核 `shop_try_buy()`

```python
def shop_try_buy(cfg, src, gid, num):
    """选币 → 限购校验 → 扣费 → 发货 → 记限购
       返回 (code, msg, g, total, bought_after)；code=1 成功 / 0 失败"""
    g = shop_find_goods(src, gid)            # 按条目 id（回退 item_bid）
    if g is None: return 0, '商品不存在', None, 0, 0
    pay  = shop_pay_asset(cfg, g)            # ★ 与客户端 Config.AssetsEnToCode 同源
    unit = int(g.get('price', 0) or 0); total = unit * num
    bought0 = db_mall_bought(rid).get(gid, 0)
    lim = int(g.get('limit_week', 0) or 0)   # 限购 = 权威上限（APK 里可取）
    if lim > 0 and bought0 + num > lim:      → 0, '超过限购…'
    if total > 0 and have < total:           → 0, '%s 不足…'
    db_set_assets(rid, {pay: have - total})  # ★ 用**绝对值**写入（见 12805 踩坑）
    db_bag_add(rid, item_bid, num)           # 发货
    db_mall_bought_add(rid, gid, num)        # 记限购
    return 1, '', g, total, bought0 + num
```

**抽取动机（架构层面）**：三个购买入口（`12805` / `12832` / `13402`）若各写一份，
迟早各自漂移。收敛到一处后，"选币规则改了"只需改一次。
（`12805` 早于本函数实现，逻辑等价、**暂未重构**以降低回归风险。）

**入口差异**：

| 命令 | 商品源 | 应答形状 | 成功后推送 |
|---|---|---|---|
| `12805` | `mall_cfg()` | `code,msg,id,num,total` | 包刷新 + `12831` + live_push |
| **`12832`** | `mall_cfg()` | `code,msg,id,num` | 包刷新 + `12831` + live_push |
| **`13402`** | `mall_cfg()`（**与 `13401/13403` 同源**） | `id,type,buy_num,new_price,code,msg` | 包刷新 + **`18909`（已购列表）** + live_push |

> `13402` 的 `new_price` 回**当前单价**：本服配置是固定价（`mall_config` 无动态价字段）
> ⇒ 回原价是真话，不编"涨价"。

---

## 三、★ 迁移时踩的坑：**旧日志行引用了已删变量**

把 `13402` 从"内联流程"改写成"调 `shop_try_buy`"后，**末尾那行成功日志**
仍引用 `g_gid / item_bid / pay / buy_num` —— 这些变量在新作用域里已不存在。

```python
log('tcp.log', '  ** 13402 购买成功 …' % (g_gid, item_bid, bnum, pay, total, buy_num))
```

后果很隐蔽：**应答已经发出去**（`code=1`、扣费/发货也已完成），
随后抛 `NameError` ⇒ 连接被异常处理打断。**玩家看到"购买成功"，但连接断了。**

⇒ 已修：按 `code` 分支，变量全部安全取自 `g` / 返回值。

**教训**：**重构时"最后一行日志"最容易被漏掉** —— 它不在主逻辑路径上，静态检查也未必报。
改完必须**真跑一次该命令**（本轮用 `tools/verify_13402.py` 覆盖）。

---

## 四、验证

`tools/verify_13402.py`（端到端做一次真实购买，三向核对）：

```
购买前: coin=976339  item_bid=40002 x0
13401: type=5 条目 10 个，首个 id=4011 buy_num=0
13402: id=4011 type=5 buy_num=1 new_price=16000 code=1 msg=''
购买后: coin=960339 (差 -16000)  item_bid=40002 x1 (差 1)
   ✓ 扣费正确 = 16000      ✓ 发货正确 = 1      ✓ 限购计数已更新
=== 结果: PASS ===
```

**协议审计（无副作用部分，round42 复跑）**

| 审计 | 结果 |
|---|---|
| `audit_specs_vs_fields.py` | 2463 条：**0 不一致** |
| `audit_sc_conformance.py`（全量 1635） | **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 101 条：**100 一致 + 1 空规格** |
| `audit_sc_live.py --unsupported` | **101/101 一致** |

---

## 五、产出

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `shop_try_buy()` 共用内核；`12832` 与 `13402` 接入；`13402` 移出未开放集合 |
| `tools/verify_13402.py` | 新增：购买三向核对（扣费/发货/限购计数） |

---

## 六、★ 运维注意（本轮踩到的现实约束）

调试期间发现 **真机客户端正在活跃游戏**（`10.0.2.2` 模拟器登录、移动、购买），
因此确立两条纪律：

1. **不要再"还原 DB"**：`backup/roles.db.bak_*` 是**开发期**的还原点；
   一旦有真机玩家，还原会**毁掉玩家进度**。
2. **不要在有玩家时跑 `replay_captures.py`**：它会回放 876 个真实变体
   （含购买/领取/移动），会大改玩家状态。协议审计应改用
   `audit_specs_vs_fields.py` / `audit_sc_conformance.py` / `audit_sc_live.py`
   这三道**无副作用**的工具。

---

## 七、下一步

协议对接这条线到此收口。后续按 `docs/HANDOVER` §6 **P1′** 推进玩法：
副本/爬塔进度 → NPC 交互 → 社交聊天 → 大玩法（宗门战/竞速/婚宴/跨服）；
以及剩余 3 个排行榜（`12902/12911/12912`）——**若解出榜名即可照 `12901` 补真实 `val`**。
