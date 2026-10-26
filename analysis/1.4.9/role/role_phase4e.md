# Phase 4E —— 角色状态持久化（SQLite）✅ 完成（角色数据 + 属性均已入库）

> **目标**：把 `lev/exp/gold/**属性**/坐标` 等从 `config.json` 的**静态配置**
> 搬进**数据库**，保证**服务器重启后角色数据仍在**。
> **结论**：完成。两条决定性证据：
> 1. 重启后客户端面板显示 **LV.7**（配置里是 1）；
> 2. 重启后面板属性显示 **生命 4321 / 物攻 777 / 物防 666 / 法攻 555 / 法防 444 /
>    命中 333 / 躲闪 222 / 暴击 111 / 抗暴 88** —— 全部来自数据库，
>    **与默认值（1000/100/80/100/80/50/50/30/30）完全不同**。

---

## ★★ 本轮续做：**属性（attr）也入库**

### 新增表 `role_attr`

列名**直接用协议里的 attr 字段名**（避免二次映射出错）：

```sql
CREATE TABLE IF NOT EXISTS role_attr (
  rid INTEGER PRIMARY KEY,
  strength INTEGER, intellect INTEGER, armor INTEGER, constiution INTEGER,
  atk_s INTEGER, atk_p INTEGER, def_s INTEGER, def_p INTEGER,
  hp_max INTEGER, atk_speed INTEGER, hit INTEGER, dodge INTEGER,
  crit INTEGER, tenacity INTEGER, red_def_s INTEGER, red_def_p INTEGER,
  atk_abs INTEGER, def_abs INTEGER, reduce INTEGER, hurt INTEGER,
  hit_rate_show INTEGER, dodge_rate_show INTEGER,
  crit_rate_show INTEGER, tenacity_rate_show INTEGER,
  updated_at INTEGER)
```

新增 `db_get_attr(rid)` / `db_save_attr(rid, attr)` / `_ATTR_COL_SET`。
`build_10303` 的取值顺序改为 **`ATTR_DEFAULTS` < 配置 < 数据库行**（与角色表同一原则）：

```python
a = dict(ATTR_DEFAULTS); a.update(attr or {})     # 配置作种子
db_a = db_get_attr(rid)
if not db_a: db_save_attr(rid, a); db_a = db_get_attr(rid)   # 首次播种
if db_a: a.update(db_a)                           # 数据库为准
```

### ★ 决定性验证：重启后面板显示 DB 里的**特征值**

先写入明显区别于默认值的特征值，**杀掉服务器进程并重启**，再重登客户端、点 (2174,104)：

| 项 | 面板显示 | DB 值 | 默认值 | 结论 |
|---|---|---|---|---|
| 生命 | **4321** | 4321 | 1000 | ✅ 来自 DB |
| 物攻 | **777** | 777 | 100 | ✅ |
| 物防 | **666** | 666 | 80 | ✅ |
| 法攻 | **555** | 555 | 100 | ✅ |
| 法防 | **444** | 444 | 80 | ✅ |
| 命中 | **333(0%)** | 333 | 50 | ✅ |
| 躲闪 | **222(0%)** | 222 | 50 | ✅ |
| 暴击 | **111(0%)** | 111 | 30 | ✅ |
| 抗暴 | **88(0%)** | 88 | 30 | ✅ |
| 速度 | 100 | 100 | 100 | ✅（未改） |

**无空白、无 nil、无乱码、无报错**（`shots/stage4e_attr_persist2.png`）。

**⇒ 属性也完全走数据库，且活过服务器重启。**

顺带修掉一处**日志文案**问题：`10303` 的日志原先硬编码打印 `ATTR_DEFAULTS`，
现改为打印**实际下发的 DB 值**。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① `import sqlite3`<br>② 新增 `DB_PATH` / `_DB_COLS` / `db_init()` / `db_get_role()` / `db_save_role()`，建表 `roles`<br>③ **续做**：新增 `role_attr` 表 + `db_get_attr()` / `db_save_attr()` / `_ATTR_COL_SET`<br>④ 新增 `_DB_TO_SC`（DB 列 ↔ SC 字段名）与 `_sc_to_db_updates()`（状态 → DB 列）<br>⑤ **`role_state(cfg)` 三级合并**：`ROLE_DEFAULTS` < `config.json.role` < **DB 行**（首次播种）<br>⑥ **`build_10303` 的 attr 也三级合并**（DB 为准）<br>⑦ `save_role_pos()` 改为写 DB（保留 JSON 快照）<br>⑧ `role_with_saved_pos()` 改从 `role_state()` 取<br>⑨ `main()` 启动调用 `db_init()`<br>⑩ 修正 `10303` 日志文案打印真实值 |
| `server/state/roles.db` | **新增**（SQLite，含 `roles` 与 `role_attr` 两张表） |

---

## 2. 协议证据 / 数据流

```
config.json.role ──┐
                   ├─► 首次：播种一行进 DB（日志 "role 1001 seeded into DB from config"）
ROLE_DEFAULTS    ──┘
                          ↓
   数据库 roles 行  ──►  role_state(cfg)  ──►  build_10301 / build_10302 / build_10303 / 10200 / 10201
                          ↑
   客户端 CS_10204（移动）──► save_role_pos() ──► db_save_role(x, y) 落盘
```

**优先级明确：`ROLE_DEFAULTS` < `config.json.role` < 数据库行。**
⇒ 角色一旦入库，**后续一切以数据库为准**（这才叫持久化）。

---

## 3. 测试结果（含**决定性**证据）

### 3.1 冒烟测试：播种 + 读写

```
** role 1001 seeded into DB from config
role_state:  {'rid':1001,'name':'DSH','lev':1,'exp':0,'gold':1000,'gold_acc':5000,'x':30,'y':30}
after update:{'lev':7,'gold':8888,'x':99,'y':77}
```

### 3.2 ★ 服务器重启后数据仍在，且 DB 优先于配置

把 DB 改成 `lev=7 / gold=8888 / x=99 / y=77`（**故意与配置不同**），
然后**杀掉服务器进程并重启**：

```
config.json 里:   lev=1   gold=1000   x=30  y=30
服务器实际用的:   lev=7   gold=8888   x=99  y=77     ← 来自 DB，活过了重启
```

### 3.3 ★ 客户端重登后读到的是**数据库的值**

重登客户端后，服务端日志：

```
[23:42:48]  << 10302 SC_10302 lev=7 exp=0 gold=8888 gold_acc=5000 (20 bytes)
[23:42:50]  .. role 1001 state from DB pos=(94,65) lev=7 gold=8888
[23:42:57]  ** DB persist role 1001 pos=(94,65)      ← 客户端移动后自动写回 DB
```

### 3.4 ★ 界面确认：面板显示 **LV.7**

点 **(2174, 104)** 打开角色面板，视觉逐字判读（`shots/stage4e_persist2.png`）：

| 项 | 面板显示 | 来源 |
|---|---|---|
| **等级** | **LV.7**（绿色 7，清晰可辨） | **数据库**（配置里是 1） |
| 职业 | 玄武 | DB |
| 生命 / 物攻 / 物防 / 法攻 / 法防 | 1000 / 100 / 80 / 100 / 80 | `ATTR_DEFAULTS`（尚未入库，见"仍缺失"） |
| 异常 | **无空白、无 nil、无乱码** | — |

**⇒ 服务器重启 → 客户端重登 → 等级显示 7（DB 值）而不是 1（配置值）
= 持久化成功的决定性证据。**

---

## 4. 日志位置

```
logs/1.4.9/role_4e_tcp.log        服务器 TCP（含 "state from DB" / "DB persist"）
server/state/roles.db             SQLite 数据库
server/logs/server.log            启动日志（含 "DB ready -> …"）
shots/stage4e_persist2.png        ★ 面板显示 LV.7 的截图
```

---

## 5. 仍然缺失的问题

1. **`attr`（属性数值）尚未入库** —— 目前仍来自 `ATTR_DEFAULTS`，
   所以面板属性不会随 DB 变化。**下一小步**：把属性也加进表/或单独一张 `role_attr` 表。
2. `uid` 列已建但未真正使用（登录未带 uid）—— 属"预留"，**未编造逻辑**。
3. `hp/max_hp/mp/max_mp` 列已建，但服务端目前没有"战斗/回血"逻辑去改它们；
   `SC_10303` 也没有这两个字段（生命上限走 `attr.hp_max`）—— **状态未确认**，故保持默认。
4. `scene_id` 已持久化，但当前只有一张地图（10001），**多场景未验证**。
5. 4F（移动 + 坐标保存）中的"服务端重启后坐标恢复"本轮已顺带验证
   （`x/y` 在 DB，重启后仍是 `(94,65)`）—— **但 4F 的完整回归测试尚未跑**。

---

## 6. Phase 4E 结论

| 项 | 结果 |
|---|---|
| 数据库 | ✅ SQLite `server/state/roles.db`，表 `roles`（字段按阶段要求） |
| 数据源 | ✅ **DB 优先**（配置仅作首次播种） |
| 服务器重启后数据仍在 | ✅ 实测（lev=7/gold=8888/x/y 全部存活） |
| 客户端读到 DB 值 | ✅ 实测（面板 **LV.7**） |
| 移动自动落盘 | ✅ 实测（`DB persist role 1001 pos=(94,65)`） |
| 改 APK / 改 UI | ✅ 未做 |

**按阶段纪律：本 Phase 完成，不自动进入 4F。**

---

**[WAITING FOR PHASE 4F]**
