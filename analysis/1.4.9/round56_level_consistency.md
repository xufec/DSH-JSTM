# R56：等级口径不一致修复 + 门禁 E 条件式豁免（由一次 admin 改等级引发）

> 本轮起点是一个**意外**：门禁 E 突然报 `▲ cmd=20100 field=promote ← 规格要 table，实际发空表`。
> 顺着它查下去，抓出一条**真实的"口径不一致"**，并把门禁的豁免机制升级成**条件式**。
> **时间**：2026-09-29 11:05 – 11:25。

---

## 一、链条还原（全部有日志）

### 1.1 等级被 admin 改过

```
server/logs/http.log
  [11:02:28] GET /DSH_ADMIN/setlevel?lev=20 → ** ADMIN setlevel rid=1001 -> 20
  [11:02:47] GET /DSH_ADMIN/setlevel?lev=9  → ** ADMIN setlevel rid=1001 -> 9
  [11:02:54] GET /DSH_ADMIN/setlevel?lev=9  → ** ADMIN setlevel rid=1001 -> 9
```

（同一日志里更早还有 `18:15:16 -> 100`、`18:23:36 -> 70`。**`setlevel` 是项目既有的管理旋钮**，
不是缺陷；本轮只是如实地把这次改动的后果记录下来。）

### 1.2 ★ 抓出的真缺陷：同一个角色，两条应答给出**不同的等级**

```
[11:07:30] << 10302 SC_10302 lev=9  ...        ← 走 role_state()（DB 真源）
[11:07:30] << 13340 SC_13340 profile name=DSH lev=70   ← 走 config.json 的静态模板
```

**根因**（`mock_server.py` `if cmd == 13340` 原来那一行）：

```python
r = self.cfg.get('role', {})      # ← config.json 里的 role 模板（lev=70 是写死的种子值）
```

而 `role_state()` 的优先级是「`ROLE_DEFAULTS` < `config.json.role` < **数据库行**」，
DB 一旦入库就以 DB 为准 ⇒ **两处永久可能不一致**。
与 R43「战力口径统一」（4 处算法 → 1 处）是**同一类问题**。

### 1.3 修复

```python
# ★★ R56 修复「等级口径不一致」
r = role_state(self.cfg)                                  # ← 身份/等级一律走真源
out = (w_str(r.get('name', '')) + w_u8(int(r.get('lev', 1)) & 0xff) +
       w_u8(int(r.get('career', 1)) & 0xff) + w_u8(int(r.get('sex', 0)) & 0xff) + ...)
```

（`sign/guild_name/title/per_name/zone/city/gift_num` 这些**非角色状态**字段仍取 `self.cfg`，语义不变。）

**新增守卫** `tools/verify_level_consistency.py`：

```
== 等级口径 ==
  DB(admin /status) : 9
  10302             : 9
  13340             : 9
  一致: 是
=== 结果: PASS ===
```

> 写这个 verifier 时自己踩了一次：`SC_10302` 的 `lev` 是 **uint16** 不是 u8，
> 只读首字节会得到 0 —— 被"DB=9 / 10302=0"的假不一致立刻暴露，属于**测试自己的错**（METHODOLOGY §5 那条）。

---

## 二、`20100.promote` 为空：**这是正确行为**，不是缺陷

```
19 条提升项(tips) 的 display_lev 取值 = [17,20,20,20,25,30,30,30,31,35,35,38,50,50,55,58,63,63,200]
最小值 = 17
客户端按 `Config.Promote[code].display_lev <= roleVo.lev` 过滤（advance_new_panel proto#17）
⇒ 角色等级 9 < 17 ⇒ **本就没有任何提升项可显示** ⇒ 空表正确
```

⇒ 门禁 E 的**判据需要升级**：有些空表是**依赖角色状态**的，不能一刀切。
同时**绝不能**用无条件白名单把它永久遮掉（那会让 R49b 那类真缺陷再次静默通过）。

### 2.1 门禁 E 升级：条件式豁免

```json
"20100:promote": {
  "reason": "…display_lev 最小值 17 ⇒ lev<17 时必然为空且客户端也不显示任何提升项，是正确行为…",
  "when": { "role_lev_lt": 17 }
}
```

```
门禁运行时读 /DSH_ADMIN/status 拿 role_lev：
  条件成立 ⇒ 记为"已登记理由"
  条件不成立（等级够高）⇒ **仍然告警**   ← 关键：豁免会"重新武装"
```

**自检同步升级**（`--selftest`）：

```
== 灵敏度自检（SC_20100）==
  空 promote  : empties=['promote']            → 检出 ✓
  有 2 条     : promote 不再被报                → 修好后不再报 ✓
  条件豁免: lev=9 生效 ✓ ／ lev=70 不生效（会照常告警）✓
  自检: PASS
```

---

## 三、连带修正：`verify_guaji.py` 不该依赖玩家等级

等级 9 落在 `config_guaji` 的**所有等级段之外**（最低段 `lev_l=25`），
于是 `15402` 老实回了 `map_bid=0`——但原 verifier 断言"必须命中某个挂机点"⇒ 误报 FAIL。

改为**按同一规则算期望**：

```
角色等级=9 ⇒ 期望挂机点=无（等级段之外）
等级段之外 ⇒ 期望 map_bid=0: 是      ← 服务端没有硬塞一个点，正确
```

⇒ `verify_guaji.py` 现在**与玩家等级解耦**，任何等级下都能跑。

---

## 四、全量验证

| 门禁 | 结果 |
|---|---|
| `audit_emitted_fields.py --selftest` | **PASS**（含条件豁免"重新武装"自检） |
| `lint_dispatch_shadow.py` | 专用 169 / 默认 64 / 未开放 22 ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 / **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 86 命令：85 一致 + 1 空规格 / **0 不一致** |
| `audit_sc_live.py --unsupported` | **86/86 一致** |
| `audit_dedicated.py` | **63/63 符合规格** |
| **`audit_emitted_fields.py`** | 132 条 / `role_lev=9` / 顶层空表告警 **0** / **PASS** |
| 回归 | `verify_level_consistency`（新）/ `guaji` / `race` / `attr_power` / `arena` / `dungeon` / `mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `stderr` 0 字节；9000 端口恰好 1 个监听 |

---

## 五、★ 需要你决定的一件事（不擅自改）

**玩家角色 `rid=1001` 的等级当前是 `9`**（由 admin `/setlevel` 写入，不是我改的），
但 `role_attr` 里仍是 **70 级那一套属性**（`hp_max=4381` 等）⇒ 这是一个**不自洽的状态**。

| 选项 | 影响 |
|---|---|
| A. 保持 9 | 变强面板无提升项、`15402` 无挂机点（等级段之外）、挂机链仍走不通 |
| B. 改回 70 | 与 `role_attr` 一致、`config_guaji` 命中 `10005`（lv65–74）、可为 R55 的 4019 按钮实验创造条件 |

命令（供你选）：
```powershell
# 改回 70（与属性一致）
Invoke-WebRequest 'http://127.0.0.1:8080/DSH_ADMIN/setlevel?lev=70'
```
**本轮未执行**（改玩家数据属项目红线内需谨慎的动作，且这次是 admin 有意为之）。

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `13340` 改用 `role_state()`（口径统一），附完整事由注释 |
| `tools/verify_level_consistency.py` | 新增：`10302 / 13340 / DB` 三处等级一致性守卫 |
| `tools/audit_emitted_fields.py` | **条件式豁免**（`when.role_lev_lt`）+ 自检新增"重新武装"断言 |
| `tools/_emitted_empty_allow.json` | `20100:promote` 改为**条件式**（88 条） |
| `tools/_fix_r56_allow.py` | 白名单改写脚本（幂等） |
| `tools/verify_guaji.py` | 改为**等级无关**的期望值计算 |
| `analysis/1.4.9/round56_level_consistency.md` | 本报告 |

---

## 七、下一步

| 优先 | 事项 |
|---|---|
| 1 | **你决定 §五 的 A/B** —— 若选 B（改回 70），即可继续 R55 的"点 4019 按钮"实验 |
| 2 | 该实验的判据仍然是**日志里出现 `>> cmd=15400`**（不是看截图）；坐标要用"裁剪 + 百分比换算"标定 |
| 3 | 顺手把 `13340` 之外的同类"读 config 模板当现行状态"的地方清一遍（本轮只改了 13340 这一处真出问题的） |
