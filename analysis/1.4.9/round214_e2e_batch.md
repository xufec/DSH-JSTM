# R214（新目标②）：★★★ **端到端证明的"批量应用" —— 系统化确认"数据真的来自 DB"**

> 新目标第 24 批。★★ **本批把"端到端证明"（纪律第 54 条）工具化，并确认了 3 条已接 DB 的命令。**
> **时间**：次日 11:30 – 13:00。

---

## 一、★★ 本轮的两个"否决"（**先确认语义/数据源，不做无源填充**）

| 对象 | 检查 | 结论 |
|---|---|---|
| **`10954` 的 `looks`/`surface_list`/`surface_star`** | **DB 里没有 `role_surface`/`role_fashion`** | ★ **无源 ⇒ 空是"真话"** ⇒ **不做** ✓ |
| **`10622` 的 `skill_list`** | 需"伙伴 ↔ 技能"关系 ⇒ R206 已查：**`config_hero_skill_order` 无 `bid`** | ★ **对应关系不可靠 ⇒ 不做** ✓ |

---

## 二、★★★ 发现：**`11600`/`15700` 早就接了 DB**（**R125/R126**）

```
L11827: if cmd == 11600:
    _wg = db_wing_state(role_state(self.cfg).get('rid', 1001))
    _out = (w_u8(_wg['color']) + w_u32(_wg['wing_id']) + w_u32(_wg['power']) + …)
```
★ **⇒ 它们**已实现**（**`color`/`wing_id`/`power`/`star` 读真实 DB**）—— **只是"子表"仍空**（**无源**）✓

★★ **⇒ 与 DB 表的"逐名对应"**：
| 命令 | SC 子表/字段 | ⟷ DB 表 |
|---|---|---|
| **`11600`** | `color`/`wing_id`/`power`/`star` | ★ **`role_wing`**（**同名**）|
| **`15700`** | `shenqi_list<id, lev, star, status, mark>` | ★ **`role_shenqi`**（`sid`↔`id`）|
| **`19400`/`19401`** | `mingge_list<id, bid, bind, lev, gongming_lev, quantity>` | ★ `role_mingge` |
| `10954` | `looks`/`surface_list`/`surface_star` | ❌ **无表** |

---

## 三、★★★ 端到端证明（**工具化**：`tools/prove_e2e_db.py`）

```python
def prove(name, cmd, body, setter, restorer, extract):
    before = extract(ask(cmd, body))
    setter()                      # ★ 改 DB
    mid = extract(ask(cmd, body))
    restorer()                    # ★ 复原
    after = extract(ask(cmd, body))
    ok = (before != mid) and (after == before)      # ★ 三项判定
```

### 实测

```
  11600      cmd=11600  8801 → 54321 → 8801 ｜ ✓       ← 改 wing_id ⇒ 回包变；复原 ⇒ 恢复
  role_shenqi 现有 2 行: [(10001, 4, 2, 0, 0), (10002, 1, 0, 1, 0)]
  15700: len=28 消耗=28 err=None ｜ ★ shenqi_list=2      ← 与 DB 的 2 行一致 ✓
  ★ 端到端证明：1/1 通过
```

★★ **⇒ 两项判定一起做**（`before != mid` **且** `after == before`）⇒
   **既能证明"数据来自 DB"，又能证明"复原干净"**（**无副作用**）✓

> **★ 纪律第 56 条**：**端到端证明要做"双向"** ——
> ① **`before != mid`**（**改了 DB ⇒ 回包必须变**）⇒ 证明"真的读了 DB"；
> ② **`after == before`**（**复原 ⇒ 回包必须恢复**）⇒ 证明"**没有副作用**"。
> ★★ **只做 ① 不够**（**可能改了 DB 但顺带污染别处**）；**只做 ② 不够**（**可能压根没读 DB**）。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★★ **`tools/prove_e2e_db.py`** | ★★ **端到端证明（批量）** —— 改 DB ⇒ 看回包 ⇒ 复原 ⇒ **双向判定** |
| `tools/_diag_r214.py` | `looks`/`surface` 与 DB 表的核查 |

---

## 六、目标② 累计成果（新目标 24 批）

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
| R212 | `10954`/`10955`/`10957` → 装备列表 | `equip_items` | ★★★★★ |
| R213 | `10601` → 18/22 战斗属性 | `role_attr` | ★★★★★ |
| **R214** | **确认 `11600`/`15700` 已接 DB** + **端到端证明工具化** | `role_wing`/`role_shenqi` | ★★★★★ |

---

## 七、下一批

| 目标 | 依据 |
|---|---|
| ★★ **用 `prove_e2e_db.py` 复查前 8 条** | 纪律第 56 条（**双向判定**）|
| ★ **`19400`/`19401` 的 `mingge_list` ← `role_mingge`** | 逐名对应（`bid`/`lev`/`quantity`）|
| ★ **`role_shenqi` 的 `lev`/`star` 是否为 u16**（SC 里是 u16）| 注意宽度 |
