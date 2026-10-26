# 背包"没有装备" —— `bag_code` 分囊（权威取证 + 已修复）

> 用户报障：「背包没有装备，只有物品」。

---

## 一、★ 权威取证：`BackPackConst.Bag_Code`（客户端 `game/backpack/backpack_const.luac`，15 项）

```
BACKPACK            = 1     ← 背包
ROLE_EQUIP          = 2     ← ★ 角色装备
HERO_EQUIP          = 3     ← 伙伴装备
STORAGE             = 4     ← 仓库
HERO_STORAGE        = 5
JBP_WAREHOUSE       = 6
FASHION_PACK        = 7
TREASUR_PLANE       = 8
PARTNER_ARTIFACT    = 11
FIRECRACKER         = 12
SOULSTAR_PACK       = 13
SOULSTAR_ROLEPACK   = 14
SOULSTAR_HEROPACK   = 15
ROLE_ARTIFACT       = 16
ROLEARTIFACT_BAG    = 17
```

**⇒ 这**解决**了此前一直标为 `UNKNOWN` 的 "`bag_code` 语义"，也解释了用户的现象。**

---

## 二、根因

**我们的 `10502` 对**任何** `bag_code` 都返回主背包内容**（原实现有一行注释明确写着这是
"简化，如实标注：`bag_code` 取值域 UNKNOWN"）。

⇒ **客户端请求 `bag_code=2`（角色装备栏）时，拿到的是普通背包的物品 ⇒ 装备栏看不到装备。**

---

## 三、修复

```python
if bag_code == BAG_MAIN:          # 1 → 背包
    items = db_bag_get(rid, BAG_MAIN)
elif bag_code in (2, 3):          # 2/3 → 角色/伙伴装备
    items = build_equip_items(rid, bag_code)
else:                             # 其它 → 按 code 取（未实现的囊回空）
    items = db_bag_get(rid, bag_code)
```

**新增 `build_equip_items(rid, bag_code)`**：把 `equip_items` 表转成 `SC_10502.items` 的形状
（`pos` 用装备槽号；**⚠ 原版槽位编号语义未取证**）。

---

## 四、验证（独立 TCP）

```
bag_code=1 (BACKPACK)  : items=3  [(7,33002,pos1), (8,36500,pos2), (9,36531,pos3)]
bag_code=2 (ROLE_EQUIP): items=1  [(6,33001,pos1)]     ← ★ 装备栏能看到装备了
bag_code=4 (STORAGE)   : items=0  []                   ← 仓库（空，未实现内容）
```

---

## 五、剩余的囊（如实）

| code | 囊 | 现状 |
|---|---|---|
| 1 | 背包 | ✅ 有内容 |
| **2 / 3** | **角色/伙伴装备** | ✅ **本轮修好** |
| 4 / 5 | 仓库 | ⚠️ 表未建 ⇒ 回空（**需 `store_items` + `10714` 字段取证**） |
| 6 / 7 / 8 / 11–17 | 魂导器/时装/寻宝/神器/魂星等 | ⚠️ 未实现 ⇒ 回空 |

**⇒ 客户端**实测请求过**的 code 是 `5/6/7/8/12` —— 这些对应的囊都还没做内容。**

---

## 六、下一步（按此表即可推进）

1. **仓库（`STORAGE=4` / `HERO_STORAGE=5`）**：建 `store_items` 表 + 实现 `10714`（`CSStorehouseInfo`）
2. **`JBP_WAREHOUSE=6`**：先 `show_cmd` 看有没有对应协议
3. **`FASHION_PACK=7` / `TREASUR_PLANE=8` / `FIRECRACKER=12`**：同上
