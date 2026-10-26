# 伙伴系统 / 聚宝盆 / 物品获取与使用效果 —— 实施报告

> 用户要求：完善伙伴系统、聚宝盆系统；物品与伙伴的获取及使用、使用效果。
> 方法：**先取证**（客户端注册表 + 协议定义 + 真机日志），再实现。

---

## 一、★ 取证：两套系统的协议全部定位（客户端字节码）

### 伙伴系统 `game/hero/hero_ctrl.luac`

```
10401 receiveHeroInfoList    11651? 无
10402 receiveHeroInfo
10403 receiveSingleHeroInfo
10404 receiveAttributeCount
10405 receiveHeroUpdateLev
10406 receiveHeroUpdateStartLev
```
**伙伴装备 `game/hero/hero_equip_ctrl.luac`：`11200 ~ 11205`**

### 聚宝盆 `game/jubaopen/jubaopen_ctrl.luac`

```
11710 on11710   11711 on11711   11712 on11712   11713 on11713
10570 on10570   ← ⚠ 同时被背包与聚宝盆注册
```

### ★ 真机日志证实**聚宝盆正在被使用**（且原先无人应答）

```
[13:43:54] >> cmd=11710 ? body(5)=65 00 0b e1 03
[13:43:59] >> cmd=11712 ? body(6)=65 32 0b e1 03 e9
[13:44:02] >> cmd=11710 ? body(5)=66 32 0b e1 03      ← 连续在点
```

---

## 二、已实现并验证

### 2.1 聚宝盆 `11710 / 11711 / 11712 / 11713`

| CMD | 定义 | 实现 |
|---|---|---|
| `11710` | `{type:u8}` → `{type,get_times,record_server:table(name,id),record_self:table(id)}` | 取 config |
| `11711` | (空) → `{code,msg,id}` | `code=1` |
| **`11712`** | `{type:u8,count:u8}` → `{code,type,msg,**Items:table(bid:u32,num:u8)**}` | ★ **加权随机抽取 → 入包 → 推 `10500`** |
| `11713` | (空) → `{code,msg}` | `code=1` |

**实测：**
```
SC_11710 type=101 get_times=0
   ← 收到 10500 背包推送
SC_11712 code=1 type=101 Items=[(33001,1), (16201,1), (33001,1)]    ← ★ 抽到 3 件
抽取后背包: [..., (33001,2), (16201,1)]                             ← 入包 ✓
```

**奖池配置（⚠ 原版奖池**未取证**，用真实存在的 bid 做占位并注明）：**
```json
"jubaopen_pool": [ {"bid":16201,"num":1,"weight":40}, {"bid":33001,"weight":30},
                   {"bid":30010,"weight":20}, {"bid":40001,"weight":10} ]
```

### 2.2 伙伴系统 `10401 / 10402 / 10403 / 10404`

| CMD | 定义 | 实现 |
|---|---|---|
| `10401` | (空) → `{hero_bag:table(bid,color,lev,exp,state,chip,skill:D\|Dsc10401skill\|), hero_chip:table(bid,chip)}` | **`skill` 子表发 0 项**（同背包做法，不编造） |
| `10402` | `{hero_bid}` → `{bid,lev,color,exp}` | 取 config |
| `10403` | `{hero_bid}` → `{bid,attr:table(code,value)}` | **attr 发 0 项** |
| `10404` | `{hero_bid}` → `{bid,lev,exp,color}` | 取 config |

**实测：`10401`→4字节、`10402`→8、`10403`→4、`10404`→8，全部有应答 ✓**

```json
"heros": [],        // ⚠ 原版初始伙伴未取证 ⇒ 默认空；需要时在此按 {bid,color,lev,exp,state,chip} 添加
"hero_chips": []
```

### 2.3 ★ 物品**使用效果** —— 礼包打开真正给东西

**提取了 `config_item_gift.luac`（新工具 `tools/extract_item_gift.py`）：**

```
结构（字节码 TDUP 直读）：[None, 礼包bid, 物品bid, 数量]
结果：496 个礼包 / 5353 条映射
样例：21900→[[4,1]]  100→[[21200,1],[21201,1],[21202,1]]  800→[[42003,1],[36531,1],[36020,1]]
内容件数分布：{1件:279, 2件:52, 3件:7, 4件:18, 5件:8, 6件:8, 7件:6, 8件:10}
```

**已接进 `10505`（使用物品）：消耗后若该 bid 是礼包 ⇒ 发内容 + 推 `10500` 刷新背包。**

```python
gave = []
for cb, cn in gift_contents(bid):
    if is_valid_item(cb):
        db_bag_add(rid, cb, cn or 1)
        gave.append((cb, cn or 1))
if gave: push 10500 ...
```

---

## 三、★ 仍未做 / 未覆盖（如实）

| 项 | 原因 |
|---|---|
| **`30010`（10级礼包）的内容** | 它**不在这张表**里 ⇒ 应在 `Config.ItemNewGift` / `Config.SelectGift`（**未提取**）⇒ **打开仍不给东西** |
| **`11200`（伙伴背包）** | 含 **6 个 `D\|Dsc11200*\|` 未解子表** ⇒ 按纪律**不完整实现** |
| **`11201~11205`（伙伴装备）** | 未做 |
| **`10405`/`10406`（伙伴升级）** | 未做 |
| **伙伴的属性/战力计算** | 需 `config_partner_base(85KB)` / `config_hero_attr(57KB)` 等**大量配置**，且需权威公式 |
| **`use_type` 的实际效果** | 目前只做"**礼包给内容**"；**加经验/buff/回血**等**未实现**（需效果表） |
| **`10570` 的双重语义** | 它同时被背包与聚宝盆注册 ⇒ 我按"批量删除"实现**可能是错的**，**待定性** |

---

## 四、本轮自查

```
mock_server.py OK ｜ lua-check OK ｜ 服务端 8080/9000（PID 1044）｜ stderr 0 字节
新增：11710/11711/11712/11713（聚宝盆）、10401~10404（伙伴）
新增：gift_contents() + tools/extract_item_gift.py + server/item_gift.json
修掉：一处自己写坏的残留表达式（`... if False else pool`）
未改客户端 ｜ 未取证的一律默认空并在配置里注明
```
