# 背包系统检查与修复报告（2026-09-18）

> 用户要求：**背包系统存在错误，自行检查修复。**
> 结论：**定位并根治 1 个根因 + 补齐 3 条未实现协议 + 清理脏数据；回归 24/24 通过。**

---

## 一、★★ 根因：`is_valid_item()` **只查"键存在"，不查记录是否有真实数据**

### 证据

```
server/item_config.json：3535 条
  ├─ 有效（type 非 None）：2987 条
  └─ **空记录（type=None）：548 条**（占 15.5%）
     样例：bid = 0,1,2,3,4,5,6,10,13,20,25,30,37,41,50,...

原实现：
    def is_valid_item(bid):
        return str(int(bid)) in ids        # ← ★ 只判断键是否存在
```

**⇒ 548 条"键存在但全字段为 None"的记录被**判为有效** ⇒ 无效物品能进背包。**

### 实测后果（背包里真的有）

```
背包 6 件里 4 件是无效物品：
  bid=5   qty=36  type=None  name=1       ← 客户端显示【空白/乱码】
  bid=10  qty=84  type=None  name=None
  bid=1   qty=72  type=None  name=None
  bid=2   qty=24  type=None  name=None
```

---

## 二、★ 修复（3 处，含"单点防御"）

### 修复 1：`is_valid_item()` 要求真实 `type`

```python
def is_valid_item(bid):
    ids = item_ids()
    if not ids:
        return True                     # 表加载失败时不过滤（避免误杀）
    key = str(int(bid))
    if key not in ids:
        return False
    v = item_cfg().get(key)
    if isinstance(v, dict):
        return v.get('type') is not None    # ★ 要求带真实 type
    if isinstance(v, list):
        return len(v) > 3 and v[3] is not None
    return False
```

### 修复 2 & 3：**单点防御** —— 在唯一写入口拒绝无效物品

**审计发现：`db_bag_add` **自身不校验**，于是所有调用方都必须各自记得校验 ——
而有 **9 处漏了**：**

| 行 | 场景 |
|---|---|
| 1030 | **admin giveitem**（后台发物品） |
| 5512 | 等级礼包领取 |
| 5793 | 聚宝盆抽奖 |
| 4835 | 商城购买 |
| 4690 | 商城兑换 |
| 5290 | 装备替换（旧装备回包） |
| 800 / 5832 | 卸下装备 |
| 3574 | 跨囊移动 |

**⇒ 与其逐个补 9 处（将来新增调用方还会漏），不如把校验收敛到唯一写入口：**

```python
def db_bag_add(rid, bid, quantity, bag_code=BAG_MAIN, item_id=None, merge=True):
    try:
        if not is_valid_item(bid):
            log('tcp.log', '  !! db_bag_add 拒绝无效物品 bid=%r qty=%r bag_code=%r' % ...)
            return None                    # ★ 拒绝
        ...
def db_store_add(...):
    if not is_valid_item(bid):
        log('tcp.log', '  !! db_store_add 拒绝无效物品 ...')
        return None
```

**⇒ 现在**没有**任何路径能把无效物品写进背包/仓库**（即使将来忘记校验）。

### 附带：2 处 `item_exists` → `is_valid_item`

```
行 3044  掉落物品过滤（注释明写"必须存在于真实物品表"）
行 3952  battle_test_drop 校验
```
**⇒ `item_exists` 语义是"键存在"（名称无误），但这两处的**意图**是"物品可用" ⇒ 改用 `is_valid_item`。**

---

## 三、★ 补齐 3 条**真机在发但无人应答**的背包协议

### 发现方式

用"真机发过的 CMD 集合 − 服务端已实现集合"比对 `10500~10599` 段 ⇒ 得到：

```
10514 / 10532 / 10560    ← 真机实际发过，服务端**无人应答**
```

### 客户端注册位置与语义（已核实）

| CMD | 注册位置 | 语义 |
|---|---|---|
| **10514** | `backpack_ctrl.handle_10514` | 背包→装备结果（CS 空） |
| **10532** | `equip_ctrl.hander_10532` → `Fire(EquipEvents.**EQUIP_GOLD_MATRIAL**, val)` | ★ **装备升级所需金币材料** |
| **10560** | `equip_ctrl.hander_10560` → `Fire(EquipEvents.**GET_GOODS_PRICE**, args)` | ★ **物品价格查询** |

**真机看 10560 的入参**：`13001(30打造石)`、`35161(30玄武图纸)` ⇒ 确认是**升级材料价格**。

### 实现与验证

```
10514 → 7 字节   code=1（空表，安全）
10532 → 4 字节   val=0
10560 → 20 字节  args=2：id=13001 type=32 / id=35161 type=7   ← ★ type 是真实数据
```

**新增 `config.item_type`**（2987 条真实 bid→type 映射，供 10560 用）。
**⚠ `item_price`（价格/升级消耗）原版**未取证**（item_config 的 `value` 全空）⇒ 默认空、回 0，**不编造**。

---

## 四、清理脏数据

```
已从 DB 删除 4 件无效物品：bag_items 的 bid 1 / 2 / 5 / 10
备份：server/state/roles.db.bak_pre_bagfix
背包最终：4 件（25104 角色经验书 / 28560 抽奖券 / 28514 小型宝石袋 / 28515 庆典夏日时装券）
         全部带真实 type ✅
```

---

## 五、验证

### 单点防御实测

```
db_bag_add(1001, 5, 99)    -> None   ✅ 拒绝（日志：!! db_bag_add 拒绝无效物品 bid=5）
db_bag_add(1001, 25104, 1) -> ok     ✅ 正常
db_store_add(1001, 10, 5)  -> None   ✅ 拒绝
```

### `is_valid_item` 判定

```
空记录 bid = 0,1,2,3,4,5      -> False ✅
有效物品 bid = 11,52,119,147  -> True  ✅
```

### 全量回归 **24/24 通过**

```
✅ 10301/10302/10303/10304（角色/属性/战力）
✅ 12400/12409（任务）
✅ **10502 code1=120B / code2=3B / code4=3B**（背包按囊分返，正确）
✅ **10514 / 10532 / 10560**（本轮新增）
✅ 14100/14101（签到）   ✅ 14700/14701（转盘）
✅ 17800（摇钱树）        ✅ 17600（在线福利）
✅ 13781（日常）          ✅ 10925（活跃度）
✅ 30600（黑市）          ✅ 20100（综合战力）
✅ 12430/12431（悬赏）
```
**stderr 0 字节** ｜ 服务端在线（PID 40980）

---

## 六、★ 方法论收获

| # | 收获 |
|---|---|
| 1 | **"键存在" ≠ "数据可用"** —— 配置表可以有大量**空记录**（本例 548/3535）。校验必须看**关键字段是否有值** |
| 2 | **校验要收敛到唯一写入口** —— 逐个调用方补校验必然遗漏（本次发现 9 处漏），且将来新增还会漏。**单点防御**才是根治 |
| 3 | **"真机发过的 CMD − 已实现 CMD" 是找缺口的好方法** —— 一次就找出 3 条无人应答的背包协议 |
| 4 | **客户端 handler 名能反推语义** —— `EQUIP_GOLD_MATRIAL` / `GET_GOODS_PRICE` 直接说明了 10532/10560 的用途 |
| 5 | **清理要连数据一起清** —— 修了校验还要**清掉已进库的脏数据**，否则老毛病仍在 |

---

## 七、当前状态

```
服务端：在线健康（PID 40980 / 8080+9000）｜ stderr 0 字节 ｜ 6443 行
背包  ：4 件，全部有效
修复  ：1 个根因（is_valid_item）+ 2 处单点防御 + 2 处调用点 + 3 条协议 + 4 件脏数据
备份  ：mock_server.py.bak_post_bagfix ｜ roles.db.bak_pre_bagfix
回归  ：24/24
```

**未处理（诚实）**：`item_price`（原版价格/升级消耗未取证）⇒ 10532/10560 的数值回 0，
拿到原版价格表后填入 `config.item_price` 即可生效（代码不需要改）。
