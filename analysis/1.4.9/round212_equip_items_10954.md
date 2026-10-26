# R212（新目标②）：★★★ **`10954`/`10955`/`10957` 的 `items` 接上 `equip_items`（端到端证明）**

> 新目标第 22 批。★★★ **本批给出了"端到端证明"：插入 DB 行 ⇒ 回包变；删除 ⇒ 回包复原。**
> **时间**：次日 08:30 – 10:00。

---

## 一、★★★ 取证：**先确认"实体"**（R205 的教训）

```
SC_10954: {rid, srv_id, name, stage, power, luck, res_stage, grow,
           skill_list, **items:table<id,bid,hero_bid,…>**, looks, surface_star}
SC_10955/10957: {stage, power, luck, res_stage, grow,
                 skill_list, **items:table<id,bid,hero_bid,…>**, surface_list, surface_star}
```

★★ **⇒ 判据：`items` 的元素有 `hero_bid` ⇒ 是"玩家身上的装备"**（**`db_equip_all`**），
   **不是背包**（`bag_items` 的元素**没有** `hero_bid`）✓
★★★ **⇒ 而 `build_equip_items(rid, bag_code)` 已存在**（`bag_code=2` = `ROLE_EQUIP`）⇒ **复用** ✓

★ **⇒ 这是"实体确认"的可复用判据**（**R205 的教训的正向落地**）：
   | `items` 元素含 | 实体 | 表 |
   |---|---|---|
   | **`hero_bid`** | **装备**（角色/伙伴身上）| **`equip_items`** |
   | **无 `hero_bid`** | **背包** | **`bag_items`** |

---

## 二、★ 实现

```python
_eq212 = build_equip_items(_rid53, 2)      # ★ 复用已有函数（bag_code=2 = ROLE_EQUIP）
_items212 = build_bag_items(_eq212)        # ★ 复用已有的 16 字段序列化
# 10954: rid + srv_id + name + stage/power/luck/res_stage/grow + skill_list + **items** + looks + surface_star
# 10955/10957:      stage/power/luck/res_stage/grow + skill_list + **items** + surface_list + surface_star
```

---

## 三、★★★ **端到端证明**（**不只是"结构 PASS"**）

```
① 插入测试装备（equip_items: slot=1, item_id=9999, bid=28517）
   10954: len=69 消耗=69 err=None
   ★ skill_list=0 ｜ ★ items=1 ｜ id=9999 bid=28517 hero_bid=0      ← ★★★ 真值！
② 删除测试装备；`equip_items` 现有 0 行
③ 删除后 items=0 ｜ 结构 PASS
```

★ **⇒ "插入 ⇒ `items=1`（值与 DB 一致）；删除 ⇒ `items=0`"** ⇒
   ★★ **⇒ 证明数据**真的来自 DB**（**不是"碰巧结构对"**）✓✓✓

> **★ 纪律第 54 条**：**"接上数据源"的验收必须做"端到端证明"** ——
> **只断言"结构 PASS"不够**（**空表也能结构 PASS**）。
> ★★ **做法**：**临时插入一行 DB 数据 ⇒ 看回包是否变化 ⇒ 再删除**（**干净、可重复、无副作用**）。
> ★★★ **这就是"结构正确"与"数据正确"的分界**。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★ **`equip_items`** | **0 行**（测试数据已清理）✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | `10954`/`10955`/`10957` 的 `items` 用 `build_equip_items` 真值 |
| ★ **`tools/_diag_r212c.py`** | ★★ **端到端证明脚本**（**插行 → 验证 → 删行**）|
| `tools/_diag_r212b.py` | 装备表核查 |
| `tools/_fix_r212_10954.py` | 插入脚本 |

---

## 六、目标② 累计成果（新目标 22 批）

| # | 成果 | 数据源 | 可靠性 |
|---|---|---|---|
| R196 | `19600` → 95 报到档位 | `config_checkin` | ★★ |
| R197 | `15204` → `num=17` + `gold` | `npc_ctrl` | ★★ |
| R199 | `16601`/`16602` → 91 个活动 | `config_function` | ★★★ |
| R200 | `13906` → 21 充值档位 | `config_charge` | ★★★ |
| R204 | `10947` → 真实属性面板 | `role_attr` | ★★★ |
| R207 | `10526` → 1 条真实装备 | `bag_items` | ★★★★ |
| R208 | `11240` → 1 条真实装备 | `bag_items` | ★★★★ |
| R209 | `13802`/`13807` → 按 `bid` 查 | `bag_items` | ★★★★ |
| **R212** | **`10954`/`10955`/`10957`** → 装备列表 | **`equip_items`** | ★★★★★（**端到端证明**）|

★ **⇒ 11 条实质升级**（**最后一条有端到端证明**）✓

---

## 七、下一批

| 目标 | 依据 |
|---|---|
| ★★ **用"端到端证明"复查前 8 条** | 纪律第 54 条 |
| ★ **`10954` 的 `looks`/`surface_list`/`surface_star`** | 分别对应 `fashion`/`surface` 表？|
| ★ **`11000`/`10804` 等 `hero_list`/`mon_list`** | 同 `equip_items` 的模式 |
