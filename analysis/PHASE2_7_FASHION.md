# PHASE 2.7 —— 时装（10573-10578）真实实现

> 时装此前走 `105xx`"装备家族"块 → **只回 `code=1`，不落库**（激活/穿戴/升星全是空转）。

## 一、数据与证据

| 项 | 来源 | 等级 |
|---|---|---|
| 协议字段 | `protocol/fields.json`（`cmd_resolve_105.luac`） | **CONFIRMED** |
| 时装数据 | `server/cfg_kconfig/config_fashion.json`（原版配置：`bid/name/career/animate_id_*`） | **CONFIRMED** |
| `role_fashion` 表 | 无原版证据 ⇒ 兼容层 | **INFERENCE** |

★ 关键取正：`CS_10574/10575/10576` 的字段名是 **`id`**（SC 亦回 `id`）；
时装**没有实例概念** ⇒ `id` 即 **bid**（代码注释已写明）。

## 二、实现（server/mock_server.py）

| cmd | 语义 | 行为 |
|---|---|---|
| 10573 | 时装激活 `CS{bid}` | 校验 bid 在 `config_fashion` 中为**有效时装** → 落库 `active=1`；无效 ⇒ `code=0`「无效时装」 |
| 10578 | 使用物品激活 `CS{bid}` | 同上（SC 少一个 `bid` 回显） |
| 10574 | 穿戴 `CS{id}` | 未激活 ⇒ `code=0`；否则 `worn=1` |
| 10576 | 脱下 `CS{id}` | `worn=0` |
| 10575 | 升星 `CS{id}` | `star += 1` |

新增 `role_fashion(rid,bid,active,worn,star,expire,ctime)` + `fashion_def / db_fashion_init / rows / get / upsert`。
从 `105xx` 装备家族块**移出这 5 条**（否则遮蔽新实现）。

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_fashion.py --port 9191      →  ALL PASS（13 项）
```

要点（真值校验）：
```
10573 bid=999999 → code=0「无效时装」（**拒绝编造 bid**）
10573 bid=43264（夏日冰淇淋）→ code=1，DB 落库 (43264,active=1)
10574 未激活 id=43263 → code=0；43264 → code=1，DB worn=1
10575 → star=1   10576 → worn=0
10578 bid=43263 → 两件均 active=1
```

**回归全绿（7 套）**：team / jiebai / jiebai_multi / marry / marry_propose / multi_session / fashion。
**门禁**：`lint_dispatch_shadow` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。
**清理**：6 张新表均 **0 行**，`roles` 只剩 1001。

## 四、诚实边界

| 项 | 状态 |
|---|---|
| 10577 时装过期（**推送** `SC{id}`） | 未实现（需定时器判定 expire；表已留 `expire` 字段） |
| 时装**属性/战力贡献** | **未接**：尚未把 `role_fashion` 汇入 `role_attr`/`role_power_of`（这是"统一 AttributeService"的下一步） |
| 时装升星的**材料消耗/成功率**（`config_fashion_upgrade` 有 `need_coin/succ_count/fail_count`） | 未实现（不编造概率语义） |
| 光环 19100/19103 | **本轮未做**（`SC_19100` 字段体量与嵌套极深，需单独一轮） |

## 五、下一步

**光环 19100/19103**（需先啃 `SC_19100` 的嵌套结构）→ **拍卖 18020/18021** →
再回到**统一属性/战力汇总**（把时装/翅膀/命格等成长汇入 `role_attr`）。

[PHASE 2.7 时装完成]