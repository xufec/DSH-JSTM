# R87：修伙伴界面 —— 「综合页显示图鉴 / 阵型列表为空」的真因是 `11215` 的 `type` 与 `id`

> 用户报障：**伙伴界面的「综合」子页面显示的是「图鉴」子页面**；
> **「阵型」子页面的伙伴列表为空、阵型也为空**。
> 两条都指向同一条命令 `SC_11215`（伙伴列表）的**数据形态**，已修并验收。
> **时间**：2026-09-29 21:30 – 21:50。

---

## 一、定位：两个子页面读的是同一条数据

| 子页面 | 用到的文件 | 关键常量/字段 |
|---|---|---|
| **图鉴** | `game/hero/hero_view/atlas/partner_atlas_view.luac` / `partner_atlas_container.luac` | 用到 **`ShenJiang`** 枚举 |
| **阵型** | `game/form/view/form_partner_list.luac` | 无网络命令 ⇒ 吃 `HeroData`（由 `11215` 填充） |
| 页签定义 | `game/hero/hero_constants.luac` | `TableConst(hash=[('Common',1),('ShenJiang',2)])`、`{TuJian:1, UseGoods:3}` |

⇒ **图鉴按 `type` 分成「普通 / 神将」两组**；而阵型要的是**"已拥有"的伙伴**。

---

## 二、真因：`SC_11215` 的两个字段填错了

`SC_11215.partner_list` 元素（权威 spec）：

```
id:uint32, bid:uint32, type:uint8, color:uint8, lifttime:uint32, lev:uint8, exp:uint32, …
```

我们原先的实现：

| 字段 | 我们发的 | 问题 |
|---|---|---|
| `id` | **序号 1..53** | `id` 是**实例 id**；阵型侧靠 `id != 0` 判断"已拥有"，序号让**所有伙伴都像"已拥有"**（图鉴/阵型无法区分） |
| `type` | **恒 0** | 图鉴按 `type` 分组（`Common=1 / ShenJiang=2`）⇒ **恒 0 两组都落不进去** |
| `lev` | 恒 1 | 与 DB 里的真实等级无关 |

⇒ 表现就是：**综合页拿不到干净的"已拥有"集合而退化到图鉴**、
**阵型页筛不出任何伙伴（列表空、阵型空）**。

---

## 三、修复（`build` 侧只改数据形态，不动协议结构）

```python
_owned = {h['bid']: h for h in db_hero_list(rid, cfg)}      # 已拥有（R86 的 role_heros）
for p in partner_base_cfg():                                 # 53 个（图鉴要全量）
    _is_own = p['bid'] in _owned
    id  = p['bid'] if _is_own else 0                         # ★ 已拥有=bid，未拥有=0
    type = 2 if p['is_deity'] == 1 else 1                    # ★ 神将=2 / 普通=1
    lev = _owned[bid]['lev'] if _is_own else 1               # ★ 已拥有取 DB 真值
```

依据出处都写在代码注释里（`hero_constants.luac` 的枚举 + `Config.Partner.is_deity`）。

---

## 四、验收（新增 `tools/verify_partner_list.py`）

```
== SC_11215 ==
  partner_list=53  解析 2546/2546 字节  PASS=True
== ① 全量（图鉴需要）==   伙伴表 53 个，收到 53 个  PASS=True
== ② type 与 is_deity 对应 ==
  type=1(普通) 47 个 ／ type=2(神将) 6 个 ／ 与 is_deity 不符 **0** 个  ⇒ PASS
== ③ id：已拥有非 0 ==
  id!=0（已拥有）**18** 个 ⇒ 阵型列表应有这么多 ／ id 与 bid 不一致 0 个
  样例: [(33100, 33100, 2), (33200, 33200, 2), (33300, 33300, 2)]
=== 结果: PASS ===
```

⇒ **图鉴**：53 个、按 47 普通 + 6 神将分组；
**阵型**：客户端按 `id != 0` 筛出 **18 个已拥有伙伴**（不再是空列表）。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| `lint_dispatch_shadow` | **✓ 无分发遮蔽** |
| `audit_specs_vs_fields` | 空消息 616 一致 |
| `audit_sc_conformance --generic --unsupported` | 一致 81 / 0 |
| `audit_sc_live --unsupported` | 81 命令：一致 81 / 不一致 0 |
| `audit_dedicated` | 66 条：符合 66 / 不符 0 |
| `audit_emitted_fields` | 长度不符 0 / 顶层空表告警 0 / **PASS** |
| 回归（**11 项**） | **`verify_partner_list`（新）** / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `11215` 的 `id/type/lev` 按 `role_heros` + `is_deity` 填（含出处注释） |
| `tools/_fix_r87_partner_list.py` | 修改脚本（幂等可重跑） |
| `tools/verify_partner_list.py` | **新增**：`11215` 形态三断言（全量 / type 对应 / id 已拥有） |
| `server/mock_server.py.bak_r87` | 改前备份 |
| `analysis/1.4.9/round87_partner_ui_tabs.md` | 本报告 |

---

## 七、请你试

> ① 「综合」页应回到综合内容（不再显示图鉴）；
> ② 「阵型」页应能看到 **18 个已拥有伙伴**，并可拖上阵位；
> ③ 「图鉴」页应有 53 个、并按 **47 普通 + 6 神将** 分组。

> 若 ① 仍不对，那说明"综合页"还依赖**别的**数据（例如 `11206` 容量、或阵型 `form` 的另一条命令）——
> 我会按 `form/` 与 `hero_view` 里**综合页**那份 luac 往下查它到底读哪些字段，
> 继续按字节码走、不猜。

---

## 八、一句话

> 两个子页面**读的是同一条 `SC_11215`**，而我们把 **`id` 填成序号、`type` 填成 0**
> —— 图鉴靠 `type` 分「普通/神将」两组、阵型靠 `id != 0` 筛「已拥有」，
> 两个字段都错 ⇒ **综合页退化成图鉴、阵型页筛出空列表**。
> 现在：`type` 按 `is_deity` 给出 47+6、`id` 只给已拥有的 18 个非 0。
