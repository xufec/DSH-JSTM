# R213（新目标②）：★★★ **`10601` 的 `hero_list` 用 `role_attr` 真值（含别名映射 + 端到端证明）**

> 新目标第 23 批。★★★ **把"22 个属性一个都填不出"的旧结论推翻，填上 18/22。**
> **时间**：次日 10:00 – 11:30。

---

## 一、★★★ 推翻旧结论（**"无源"是 R162 时期的判断**）

```
L10468: if cmd == 10601:
    # {flag:u32} → {p:u32, skill_bid:u32, lev:u32, hero_list:table(22 战斗属性)}
    #   ★ 22 个属性（atk_s/atk_p/…/atk_dis）本服**一个都填不出** ⇒ 空表（已登记）。
    _out = w_u32(0) + w_u32(0) + w_u32(0) + w_u16(0)
```

★ **⇒ 那是 R162 时期的结论**（**`role_attr` 通路尚未建立**）⇒
   ★★ **⇒ R204 建了 `db_role_attr`/`attr_row_bytes`** ⇒ **现在可以填** ✓

---

## 二、★★★ 取证：**22 个属性 ⟷ `role_attr` 的列**

| `hero_list` 字段 | ⟷ `role_attr` 列 | 备注 |
|---|---|---|
| `atk_s`/`atk_p`/`def_s`/`def_p`/`hp_max` | 同名 | ✓ |
| `hit`/`dodge`/`crit`/`tenacity` | 同名 | ✓ |
| `atk_abs`/`def_abs`/`reduce`/`hurt` | 同名 | ✓ |
| **`speed`** | **`atk_speed`** | ★ 别名 |
| **`def_red_s`/`def_red_p`** | **`red_def_s`/`red_def_p`** | ★ 别名（**顺序相反**）|
| **`hit_rate`/`crit_rate`** | **`hit_rate_show`/`crit_rate_show`** | ★ 别名 |
| `energy_max`/`updown`/`atk_interval`/`atk_dis` | **无** | ⇒ 0 |

★★ **⇒ 13 同名 + 5 别名 + 4 缺失 ⇒ 可填 18/22** ✓

---

## 三、★ 实现：**给 `attr_row_bytes` 加"别名回退"**

```python
_ATTR_ALIAS = {'speed': 'atk_speed', 'def_red_s': 'red_def_s', 'def_red_p': 'red_def_p',
               'hit_rate': 'hit_rate_show', 'crit_rate': 'crit_rate_show', …}
# attr_row_bytes 里：
v = row.get(nm)
if v is None:                    # ★ 别名回退
    v = row.get(_ATTR_ALIAS.get(nm))
```

★ **⇒ 这是"通用能力"**（**所有复用 `attr_row_bytes` 的命令都受益**）✓

---

## 四、★★★ **端到端证明**（**两次，都是纪律第 54 条**）

### 证明 1：**同名属性**（改 `role_attr.atk_s`）

```
① 原 atk_s=789 ⇒ 改成 4242
   10601: len=102 消耗=102 ｜ ★ hero_list=1
      atk_s=4242 atk_p=563 def_s=672 hp_max=4381
② 复原 ⇒ ③ atk_s=789
⇒ PASS（数据真的来自 DB）
```

### 证明 2：**别名映射**（设 `atk_speed`/`red_def_s`/`hit_rate_show`）

```
① 原值: atk_speed=None, red_def_s=None, hit_rate_show=None ⇒ 设 77/88/99
   ★ speed=77（←atk_speed）｜ def_red_s=88（←red_def_s）｜ hit_rate=99（←hit_rate_show）
② 复原 ⇒ ③ speed=0 def_red_s=0 hit_rate=0
⇒ PASS（别名映射生效）
```

★★ **⇒ 两次端到端证明都通过**（**同名 + 别名**都真的来自 DB）✓✓✓

---

## 五、★ 一处回归更新（**断言随行为变化**）

`tools/verify_106xx.py` 的旧断言是 **"`10601` 的 `hero_list` 为空"** ⇒
★ **⇒ 与我的改进冲突** ⇒ **更新为**：
```python
# ★ R213：hero_list == 1，且至少一个属性非零（来自 role_attr）
```
**实测**：`10601 hero_list=1 ｜ atk_s=789 atk_p=563 hp_max=4381 ⇒ ✓` ✓

> **★ 纪律第 55 条**：**"改进行为"时必须同步更新"断言旧行为的回归"** ——
> 本批的 `verify_106xx.py` 断言 **"hero_list 为空"**（**旧行为**）
> ⇒ ★★ **改进行为后必须找到并更新它**（**否则回归会 FAIL，而那是"正确的 FAIL"**）。
> ★★★ **判据**：**回归 FAIL 时先判断"是我改坏了，还是断言旧了"** ——
> **若回包数据是对的（端到端证明过）⇒ 就是断言旧了** ✓

---

## 六、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0**（含更新后的 `verify_106xx`）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | **`_ATTR_ALIAS` + `attr_row_bytes` 别名回退** + `10601` 用 `role_attr` |
| ★★ **`tools/_diag_r213b.py`** | ★ **端到端证明（同名属性）** |
| ★★ **`tools/_diag_r213c.py`** | ★ **端到端证明（别名映射）** |
| `tools/verify_106xx.py` | ★ **断言更新**（空 ⇒ 1 条且非零）|
| `tools/_fix_r213_10601.py` | 插入脚本 |

---

## 八、目标② 累计成果（新目标 23 批）

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
| **R213** | **`10601`** → 18/22 战斗属性 | **`role_attr`** | ★★★★★（**双端到端证明**）|

★ **⇒ 12 条实质升级** ✓

---

## 九、下一批

| 目标 | 依据 |
|---|---|
| ★★ **同用 `attr_row_bytes` 的其它命令** | 别名表是**通用的** ⇒ 查 `hero_list`/`attr` 类子表 |
| ★ **`10954` 的 `looks`/`surface_list`/`surface_star`** | 查对应的 DB 表 |
| ★ **`10622` 的 `skill_list` ← `config_skill`（R195 已 dump 17806 条）** | 旧注释说"解构失败"⇒ 现已 dump |
