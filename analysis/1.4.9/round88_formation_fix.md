# R88：阵型页空白的真源 —— `14000` 回的是**不存在的阵型 + 写死的 1 个伙伴**

> 用户复测"仍不对"。R87 修的是 `11215`（伙伴列表/图鉴/阵型候选），
> 本轮继续挖到**阵型本身的独立系统**：`game/form/form_ctrl.luac`（命令 `14000~14009`），
> 并找到 `14000` 的两处**硬编码错误**。
> **时间**：2026-09-29 21:30 – 22:00。

---

## 一、阵型是**独立系统**，不是伙伴列表的字段

| 目录 | 证据 |
|---|---|
| `game/form/form_ctrl.luac` | 注册表：**`14000→handle_14000` … `14009→handle_14009`、`14099`、`13250~13254`** |
| `config/config_formation.luac` | 7 个阵法：`(name, need_lev, order, f_type)` |
| `game/form/form_type_list.luac` | 阵型列表 UI |

**真机实际发过**：`14099`×55、`14009`×28、`14000`×28
（`14001~14008` 一次没发 —— 它们是上/下阵操作，用户还没点）。

---

## 二、`SC_14000` 的权威规格

```
SC_14000{flag:u8, select_type:u8,
  info_list:table(type:u8, f_lev:u8,
     hero_pos_info:table(hero_bid:u32, pos:u8),
     member_pos_info:table(member_id:u32, member_srv_id:string, career:u16, pos:u8, sex:u8))}
```

**我们的元素格式是对的**（`hero_bid:u32 + pos:u8`）—— 问题在**内容**：

```python
out = (w_u8(1) + w_u8(1) + w_u16(1) +
       w_u8(9) +                 # ★ type=9 —— 不是任何合法阵型！
       w_u8(1) + w_u16(1) +
       w_u32(33100) +            # ★ 写死「唐舞桐」一个
       w_u8(1) + w_u16(0))
```

### 阵型表（`config_formation.luac` 实提取）

| f_type | 阵法 | need_lev |
|---|---|---|
| **1** | 流云阵 | **1** |
| 2 | 天攻阵 | 20 |
| 4 | 疾风阵 | 32 |
| 3 | 地御阵 | 36 |
| 5 | 破雷阵 | 42 |
| 6 | 飘雨阵 | 46 |
| 7 | 锋矢阵 | 50 |

⇒ **`type=9` 不在表里** ⇒ 客户端找不到对应阵型 ⇒ **阵型显示为空**；
伙伴位写死 1 条 ⇒ **伙伴列表只有一个人**。
（容量 **5** —— 配置里每组阵法的开放位置表都是 5 项，如 `[1,2,3,5,8]`。）

---

## 三、修复

```python
_FORMATIONS = [(1,1),(2,20),(4,32),(3,36),(5,42),(6,46),(7,50)]   # f_type → need_lev

_best = 等级可用的最高 f_type         # lev=70 ⇒ 7（锋矢阵）
_heroes = db_hero_list(rid)[:5]       # ★ 已拥有伙伴（R86 的 role_heros）依次落位
info_list: type=_best, f_lev=1, hero_pos_info=[(bid, 1..N)], member_pos_info=空
```

日志也同步改掉（原先会打 `hero_pos=唐舞桐(33100)` 这种**固定文案**，日志本身在说谎）。

---

## 四、验收（新增 `tools/verify_formation.py`）

```
SC_14000 flag=1 select_type=1 info_list=1
  type(阵型)=7 f_lev=1 hero_pos_info=5 member=0
  上阵伙伴: [(30800,1), (31300,2), (32100,3), (32200,4), (32300,5)]
  解析 35/35  PASS=True
断言：结构精确解析 ✓ ／ type 是合法阵型(1..7) ✓ ／ type 是等级可用最高档 ✓ ／ 伙伴位 ≥2 且 pos=1..N ✓
=== 结果: PASS ===
```

---

## 五、★ 请你先做一件事再复测：**重启客户端**

日志里你最近一次操作是 **21:31** 的 `14099`，而 R87/R88 的服务端是 **21:35** 才起来的。
客户端的 `HeroData`/阵型数据是**登录时拉一次并缓存**的 ——
**不重启客户端，看到的还是旧数据**。

> 正确复测步骤：**MuMu 里 force-stop 客户端 → 重新打开 → 进游戏 → 再开伙伴界面**。

---

## 六、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint 0 遮蔽 / CS 2463-0 / SC 静态 81+1空-0 / SC 在线 **81-81** / 专用 66-66 / 门禁 E **PASS** |
| 回归（**12 项**） | **`verify_formation`（新）** / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`（21:35:31 起）、`9000 监听=1`、`stderr=0B` |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `_FORMATIONS` 常量；`14000` 改为真实阵型 + 已拥有伙伴落位；日志文案同步 |
| `tools/_fix_r88_formation.py` | 常量注入脚本 |
| `tools/verify_formation.py` | **新增**：`14000` 四条断言 |
| `server/mock_server.py.bak_r88` | 改前备份 |
| `analysis/_form_ctrl.txt` / `_cfg_formation.txt` | 反汇编证据 |
| `analysis/1.4.9/round88_formation_fix.md` | 本报告 |

---

## 八、一句话

> **`14000` 回的是 `type=9`（阵型表里根本没有这个类型）和写死的 1 个唐舞桐**
> ⇒ 阵型页找不到阵型、伙伴列表只有一格的残影。
> 现在：`type` = 等级可用最高档（70 级 ⇒ **7 锋矢阵**），`hero_pos_info` = **5 个真实已拥有伙伴**。
> **复测前请先重启客户端**（阵型数据是登录时拉的）。
