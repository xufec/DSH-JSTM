# PHASE 2.10 —— ★ 统一属性汇总入口（AttributeService 雏形）

> 本轮不是"再加一个系统"，而是**修一个真实的一致性缺陷**，并把属性收敛到单一入口。

## 一、★ 发现的真实不一致（本轮）

`role_attr_dict(cfg)` **只读 cfg**（`ATTR_DEFAULTS` + `cfg['role_attrs']`），而：

| 消息 | 属性来源 | 后果 |
|---|---|---|
| `10304` 角色属性大包 | `role_attr_dict`（**cfg**） | 面板用**缺省值** |
| `10306` 属性同步小包（写 `RoleVo.power`） | `role_attr_dict`（**cfg**） | 同上 |
| `10947` 属性面板 | `db_role_attr(rid)`（**DB**） | 用**真值** |
| `10601` 战斗属性 | `db_role_attr(rid)`（**DB**） | 用**真值** |

⇒ **同一角色、两套属性**：DB 里 `atk_s=789`，而 10304/10306 面板显示的是缺省值；
GM/成长系统写进 `role_attr` 的值**在面板与战力上完全看不到**。

## 二、修复：单一汇总入口

`role_attr_dict(cfg)` 改为：

```
ATTR_DEFAULTS  <  cfg['role_attrs']  <  DB role_attr(rid)
```

- DB 只覆盖 **非 None** 且 **在 ATTR 键集内** 的列（与 `role_state` 同纪律）⇒ **不会把缺省值抹成 0**；
- `atk_*`/`hp_max` 等 24 项键集**已核对**：`role_attr` 列 = ATTR 键集 + `rid`/`updated_at`（无缺口）；
- 失败时记日志并回退到 cfg（不抛）。

**收益**：`10304`/`10306` 面板与**战力**（`role_power` → 同一入口）从此与 DB 一致；
**今后时装/光环/翅膀等成长系统只需把加成写进 `role_attr` 或在此累加**，
即可一次性影响面板与战力 —— 这正是"禁止各系统自算属性"的**收敛点**。

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_attr_unify.py --port 9191     →  ALL PASS（9 项）
```

```
[1] 10304 atk_s=789 == DB、hp_max=4381 == DB、power=522390（>0）
[2] 改 DB atk_s +5000 ⇒ 10304 panel=5789（跟随）、power 522390→1052390（跟随）
[3] 10306（无前缀，attr 表直出）atk_s=5789、power 同步跟随
（测试结束自动还原 DB atk_s=789 ✓）
```

**回归全绿（9 套）**：team / jiebai / jiebai_multi / marry / marry_propose / multi_session / fashion / halo / auction。
**门禁**：`lint_dispatch_shadow` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。
**状态**：`role_attr(1001).atk_s` 已还原 789；全部新表 0 行。

## 四、诚实边界

| 项 | 状态 |
|---|---|
| 时装/光环 → 属性加成 | **仍未接**：`config_fashion` 的属性行（奇数键，`atk_p/def_s/...`）**与具体时装 bid 的对应关系无证据**（48 个时装 bid vs 45 条属性行，无字段引用）⇒ **按纪律不猜**，加成暂为 0 |
| 光环属性 | `config_halo` 只有 `up_exp/sum_exp/self_exp`（**无属性字段**）⇒ 光环战力应来自**其装备位物品**，待接入 |
| 装备属性 | 同样尚未汇入（`role_attr_dict` 不读 `equip_items`） |
| 原版战力公式 | 仍是 `JSTMCompatiblePowerFormula`（INFERENCE） |

⇒ 下一步若要"让成长看得见"，需要**先取证**时装属性行的索引语义（反汇编 `game/fashion*` 或
比对 `config_fashion_upgrade` 的阶数行），**而不是硬套**。

## 五、下一步

1. **取证时装属性行语义**（`config_fashion` 奇数键 ↔ 时装/阶数）；
2. 接入 `role_fashion` / `role_halo_equip` / `equip_items` 的属性加成到本入口；
3. 之后按优先级继续：节日/运营活动 → 神魔战 → 传送类副本。

[PHASE 2.10 统一属性入口完成]