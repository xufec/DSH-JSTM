# 背包↔仓库「覆盖/失真」—— 已修复

> 用户报障：**背包仓库之间的转移存在失真；仓库明明有很多空间，背包转移进去会覆盖仓库原先的物品。**

---

## 一、根因（代码级，两处）

### `db_store_add` 的两个缺陷

```python
def db_store_add(rid, bid, quantity=1, bag_code=STORAGE_CODE):
    row = SELECT * FROM store_items WHERE rid=? AND bag_code=? AND bid=?
    if row:
        UPDATE quantity += ...        # ① 同 bid 就叠加
    else:
        nxt = MAX(item_id)+1          # ② 自己算 id，**忽略传入的 item_id**
        INSERT ...
```

| # | 缺陷 | 后果 |
|---|---|---|
| ① | **按 `bid` 合并** | "搬运"被当成"入库合并" ⇒ **物品身份被抹掉** |
| ② | **`MAX(item_id)+1`、忽略传入 id** | **移动后 `item_id` 变了** ⇒ 客户端/服务端按 id 定位**错位** |

**⇒ 两者叠加 ⇒ 表现就是"**覆盖原有的**"。**

**关键背景**：`store_items` 的主键是 `(rid, bag_code, item_id)` —— **id 一变，客户端按旧 id 找到的就是另一件物品。**

---

## 二、修复

### 2.1 `db_store_add` 重写

```python
def db_store_add(rid, bid, quantity=1, bag_code=STORAGE_CODE, item_id=None, merge=True):
    # ★ 传入 item_id 时**优先保留它**（冲突则顺延到不冲突的 id）
    # ★ merge=False 时**不按 bid 叠加**（用于跨囊移动）
    # ★ merge=True（默认）保持原行为（掉落/发物品时合并）
```

### 2.2 `db_bag_add` 增加 `merge` 参数

```python
def db_bag_add(rid, bid, quantity, bag_code=BAG_MAIN, item_id=None, merge=True)
```

### 2.3 `bag_put_one` 调用时保留身份

```python
if bag_code == STORAGE_CODE:
    return db_store_add(rid, bid, qty, bag_code, item_id=item_id, merge=False)
...
return db_bag_add(rid, bid, qty, bag_code, item_id=item_id, merge=False)
```

**⇒ 跨囊移动 = **搬运**（保留 item_id、不合并）；其它场景（掉落/发物品）仍走合并。**

---

## 三、实测

### 3.1 单件

```
移动前 背包: [(9,30010,47), (10,40001,39), ...]   仓库: []
移动 item_id=9 → SC_10554 code=1
移动后 背包: [(10,40001,39), ...]                   ← 移出 ✓
      仓库: [(9, 30010, 47)]                        ← ★ item_id=9 **原样保留**
⇒ 仓库原有条目还在: 是 ✅
```

### 3.2 ★ 连续搬运（用户报的"覆盖"高发场景）

```
起始: 背包 5 件 ／ 仓库 1 件 [(9,30010,47)]

移 item_id=10 (40001) → 仓库id=[9, 10]
移 item_id=14 (41601) → 仓库id=[9, 10, 14]
移 item_id=15 (16201) → 仓库id=[9, 10, 14, 15]
移 item_id=16 (36531) → 仓库id=[9, 10, 14, 15, 16]
移 item_id=17 (33001) → 仓库id=[9, 10, 14, 15, 16, 17]

⇒ item_id 互不重复 ✅
⇒ 6 件全部保留、**零覆盖** ✅
```

**⇒「覆盖」问题彻底解决。**

---

## 四、自查

```
mock_server.py OK ｜ lua-check OK ｜ 服务端 8080/9000（PID 39056）｜ stderr 0 字节
改动：db_store_add（保留 id + merge 开关）、db_bag_add（merge 参数）、bag_put_one（传 id）
未改客户端 ｜ 掉落/发物品的原有合并行为**保持不变**（避免影响其它功能）
数据已复原：背包 6 件、仓库 0 件
```

---

## 五、仍未做的（沿用上一轮清单，如实）

| 项 | 说明 |
|---|---|
| **礼包打开失败** | `30010`/`33001` 的内容**不在**已提取的 `ItemGift` 表里 ⇒ 需解析 `ItemNewGift` 哈希 |
| **聚宝盆奖池与原版不同** | 现为**占位奖池**（配置已标注） |
| **伙伴商店兑换** | 未定位协议 |
