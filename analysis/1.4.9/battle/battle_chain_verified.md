# 战斗链与任务进度接线 —— 实测全通（✅ 决定性结果）

> **本轮问题**：`scFightStart` / `scFightData` 到底从哪来？战斗能否打到底？任务条件能否被战斗推进？
> **答案**：**三者全部打通**，且**任务进度是被真实战斗推进的**（不是替身）。

---

## 一、先解答上一轮的疑点：`scFightStart` / `scFightData` 来自**我们自己服务端**

`mock_server.py` 里已存在整套战斗实现：

```
行 2371  if cmd == 20002:      ← 对怪物发起战斗
行 2445  if cmd == 20014:      ← 客户端动画播完 → 推进下一回合
行  713  def scene_quest_extras(cfg, scene_id)   ← 提供任务相关场景元素（含怪物）
行 1580  def make_battle(cfg, mon)
```

配套文件：

| 文件 | 大小 |
|---|---|
| `server/battle.py` | 16,723 |
| `analysis/1.4.9/battle/battle_flow.md` | 10,547 |
| `analysis/1.4.9/battle/battle_protocol_matrix.md` | 15,481 |
| `analysis/1.4.9/battle/monster_data_model.md` | 7,391 |
| `analysis/1.4.9/battle/test_monster.md` | 5,108 |

**协议链（源码注释即依据）**：
```
CS_20002{mon_id}   发起战斗
SC_20002{code,msg} 应答（scFightStart：成功须 code=1(TRUE)）
SC_20010{...}      真正的"进战斗"（= scFightData）
SC_20012 / 20013   小回合：技能播放 + 伤害
CS_20014           客户端动画完成 → 服务端推进下一回合
SC_20020{result}   胜负
SC_20023{...}      结算明细
```

**⇒ 上一轮我把来源标 `UNKNOWN` 是对的（没瞎断）；现在有确凿答案：来自我们服务端。**

---

## 二、★ 实测：完整战斗（从发起打到结算）

```
[18:53:19]  >> cmd=20002 ? body(8)=00 00 4e 21 13 8f 00 00
[18:53:19]  >> CS_20002 fight monster mon_id=20001 (body=8 bytes)
[18:53:19]  << 20002 SC_20002 code=1(TRUE) mon=20001 bid=20001 name=戴浩
[18:53:19]  << 20010 SC_20010 battle init fighters=2 mon_hp=2400 role_hp=4321 (127 bytes)

[18:53:22]  << 20012 SC_20012 skill_play battle round=1 (41 bytes)
[18:53:22]  << 20013 SC_20013 round_start battle round=1 (53 bytes)
[18:53:22]  ** battle round 1: role(1) -> mon(2) hit=772 mon_hp=1628/2400
[18:53:22]  ** battle round 1: mon(2)  -> role(1) hit=1   role_hp=4320/4321
[18:53:24]  ** battle round 2: hit=772 mon_hp=856/2400
[18:53:27]  ** battle round 3: hit=772 mon_hp=84/2400

[18:53:29]  ** battle monster died, battle result=1                      ← ★ 怪物死亡
[18:53:29]  << 20020 SC_20020 result=1 (7 bytes)                         ← ★ 胜负
[18:53:32]  << 20023 SC_20023 type=0 result=1 role_hurl=2 (96 bytes)     ← ★ 结算明细
[18:53:32]  << 10301/10302/10303 (battle settle refresh) lev=7 exp=550 coin=1320 gold=1000
[18:53:32]  ** battle mission progress: fight_mon target=20001 -> [10020]  ← ★★★ 任务进度被推进！
```

**⇒ 完整链路：发起战斗 → 回合循环 → 怪物死亡 → 胜负 → 结算 → **任务进度推进**。**

### 后续两次战斗还验证了更多

```
[18:57:26]  ** battle monster died, battle result=1
[18:57:29]  ** battle kill mon=20022(bid=20022) -> +50 exp +30 coin (TEST_ONLY 数值)
[18:57:29]  ** battle drop item=51038(酒剑仙灵魂玉) x2 [holiday池3001 pp=24/36]
                            -> bag item_id=1 quantity=6 (1 件)
[18:57:29]  << 10500 SC_10500 bag push bag_code=7 items=1                 ← ★ 掉落推送进背包
[18:57:30]  << 12400 SC_12400 mission_list=4 (144 bytes) [补推/NpcCtrl 就绪后]
```

**⇒ 还顺带打通了：**击杀奖励**（exp/coin）与**掉落进背包**（`SC_10500 bag push`）。**

---

## 三、★ 关键结论：任务进度**不是替身，是真实战斗驱动**

```
** battle mission progress: fight_mon target=20001 -> [10020]
```

**⇒ `mission_progress_advance(rid, 'fight_mon', 20001, 1)` 已经**接在战斗结算上** ——
`10020`「切磋魂技」（条件 `fight_mon 20001 ×1`）现在可以**真正**通过打怪完成。**

**⇒ 之前我加的"移动替身"（`mission_auto_progress`）**已不再是唯一途径**；
若要区分，可在 `config.json` 把 `mission_auto_progress` 关掉，只靠真实战斗推进。**

---

## 四、怪物数据的诚实性（**保持**）

`config.json` 的 `mons` 里对测试怪 20001 有自注：

```json
"why": "Phase D 测试怪：bid 20001 取自 1.4.9 Config.Mon（name/res_id 为原版），坐标是仿真摆位"
```

**⇒ bid / name / res_id 来自**原版配置**，**坐标明确标注为"仿真摆位"** —— 没有冒充原版数据。**
（实测怪物真名「戴浩」，来自 `Config.Mon`。）

---

## 五、当前完整闭环（截至本轮）

```
进图
 ↓ 服务端推 12400（APK 主线链，自动接取）
任务栏显示（多任务、两行真实文案）
 ↓ 探针/玩家找怪 → 点击
CS_20002 发起战斗
 ↓ 服务端 SC_20002(code=1) + SC_20010（进战斗）
回合循环（20012/20013 ↔ CS_20014）
 ↓ 怪物死亡 → SC_20020{result} + SC_20023（结算）
★ 击杀奖励（exp/coin）+ 掉落进背包（SC_10500）
★ 任务进度推进（fight_mon → [10020]）
 ↓ 提交 → SC_12403(code=1) → 配置驱动发奖 → 12406 移出列表 → 剧情链前移
退出重登 → 任务与角色数据仍在（SQLite 持久化）
```

---

## 六、仍然缺失 / 待验证（如实）

| # | 项 | 状态 |
|---|---|---|
| 1 | **战斗数值是 TEST_ONLY**（`+50 exp +30 coin` 标注了 TEST_ONLY） | ⚠️ 非原版数值，需按原版掉落/经验配置校准 |
| 2 | 怪物**坐标是仿真摆位** | ⚠️ 原版布置数据 UNKNOWN |
| 3 | `SC_20020.result` 的**取值语义**（0/1/2） | ⚠️ 文档已标 UNKNOWN，未编造 |
| 4 | 探索式**自动点怪**（探针 `pickMon`+`tick`）是**调试手段**，不是原版行为 | ⚠️ 原版应由玩家点击触发 |
| 5 | NPC 对话 UI 仍未打通（提交走 `MissionCtrl:submit`） | ❌ |
| 6 | `14000` / `20504` 含未解动态子表 ⇒ 主动不实现 | ❌（守"不猜"） |

---

## 七、结论

| 项 | 结果 |
|---|---|
| `scFightStart`/`scFightData` 来源 | ✅ **我们自己服务端**（已确认） |
| 战斗能否打到底 | ✅ **能**（回合循环 → 怪物死 → 20020 → 20023） |
| 任务进度是否被战斗推进 | ✅ **是**（`battle mission progress: fight_mon target=20001 -> [10020]`） |
| 击杀奖励 / 掉落 | ✅ 已验证（`+50 exp +30 coin`、`SC_10500 bag push`） |
| 数值是否为原版 | ⚠️ 战斗奖励标 **TEST_ONLY**；怪物坐标标**仿真摆位** —— **未冒充原版** |
| 改 APK 业务 / UI | ✅ 未做（探针是调试注入） |
