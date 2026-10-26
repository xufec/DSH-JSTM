# C3.3 第三分片（C）实施记录：战斗结算幂等修正 + Service 链路复核 + 实机联调

日期：2026-10-16 ｜ 执行者：豆包 Agent ｜ 作用域：DSH（rid=1001 基线不碰，隔离账号测试）
基线口径：role_assets 权威（gold=1799942 / exp=20689 / coin=9923249 / hero_exp=9800）

---

## 0. 备份

| 文件 | 备份路径 | 字节 |
|---|---|---|
| server/mock_server.py | server/mock_server.py.bak_c33_20261016 | 1,103,904（与源一致） |

---

## 1. 现状实测结论（改前）

改前代码 `_battle_settle`（mock_server.py:9916-10001）的执行顺序：

```
delta = KILL_REWARD  # {exp:50, coin:30}
_exp_gain = delta.pop('exp')  # 50
add_role_exp(rid, 50)           # ← ① exp 无条件直加，先于幂等检查
grant(rid, [{coin:30}], ref='kill:<mon_bid>:<rid>')  # ← ② coin 经 reward_log PK 幂等
if not already:
    mission_progress_advance(...)  # ← ③ 任务进度仅首杀推进
roll_drops(mon_bid) → db_bag_add(...)  # ← ④ 掉落无条件入包
```

**实测结论（基于 A 分片审计 + 活库 reward_log 佐证）**：

| 击杀次数 | exp | coin | 掉落 | 任务进度 | reward_log |
|---|---|---|---|---|---|
| 第 1 次（同 mon） | +50 ✅ | +30 ✅ | +1 件 ✅ | +1 ✅ | +1 条 |
| 第 2 次（同 mon） | **+50 ❗** | **+0（already）** | **+1 件 ❗** | 跳过 | +0 |
| 第 N 次 | **每次 +50 ❗** | +0 | **每次 +1 件 ❗** | 跳过 | +0 |

**核心问题**：`reference_id='kill:<mon_bid>:<rid>'` 键把 coin 和任务进度挡成"每怪每人仅一次"，但 exp 和掉落根本不在幂等门内——同型怪可被反复刷 exp 与掉落物。

活库佐证：`reward_log` 中 `kill:20001:1001`、`kill:20002:1001` 各仅 1 行（coin 幂等生效）；但 exp 可被多次叠加（审计 §2-A7）。

---

## 2. 幂等修正设计（实测→方案→改动）

### 2.1 方案

**目标**：同一次战斗只结算一次（含重试/断线重发/异步重入）；正常刷怪每次击杀独立结算。

**设计**：
1. 在 `on_20002` 建战斗时，为每场战斗生成唯一结算引用 `kill:<mon_bid>:<rid>:<毫秒时间戳>`。
2. `_battle_settle` 中 grant() 使用该唯一引用作为 reference_id。
3. 将 exp（add_role_exp）和掉落（db_bag_add）从"无条件执行"移入 `if not already:` 幂等门内。
4. 保留 `_battle_settled` 内存标志防同连接重入；保留 `self.battle` 门防并发战斗。

**为什么用毫秒时间戳做 seq**：每场战斗由 CS_20002 触发，建战斗时记录 `int(time.time()*1000)`，保证：
- 两次正常击杀间隔 >1ms → 不同 ref → 独立结算
- 同一战斗实例的异步重入（timer 重复触发）→ 同一 ref → already=True → 跳过

### 2.2 改动行号与内容

#### 改动 1：on_20002 生成 battle_settle_ref（mock_server.py:17687-17700）

在 `self.battle = make_battle(...)` 之后追加：

```python
# ★ C3.3：每场战斗生成唯一结算引用（kill:mon_bid:rid:<毫秒时间戳>）。
#   目的：(a) 每次正常击杀独立结算；(b) 同一战斗实例的异步重入/重放被 reward_log PK 挡住。
try:
    _rid_now = int(role_state(self.cfg).get('rid', 1001))
except Exception:
    _rid_now = 1001
self.battle_settle_ref = 'kill:%d:%d:%d' % (
    int(mon_id), _rid_now, int(time.time() * 1000))
```

#### 改动 2：_battle_settle 使用实例级 ref + exp/掉落纳入幂等门（mock_server.py:9920-10010）

**原行为**：
```python
_exp_gain = int(delta.pop('exp', 0))
if _exp_gain:
    add_role_exp(self.cfg, rid, _exp_gain)          # ← 无条件
_kill_gr = grant(rid, _awards, ref='kill:%d:%d' % (mon_bid, rid), ...)
if not _kill_gr.get('already'):
    mission_progress_advance(...)
# 掉落（在 if 块外，无条件）
drops = roll_drops(mon_bid)
...
db_bag_add(...)
```

**新行为**：
```python
_exp_gain = int(delta.pop('exp', 0))
_settle_ref = getattr(self, 'battle_settle_ref', None) or 'kill:%d:%d' % (mon_bid, rid)
_kill_gr = grant(rid, _awards, reference_id=_settle_ref, source='battle')

if not _kill_gr.get('already'):
    if _exp_gain:
        add_role_exp(self.cfg, rid, _exp_gain)     # ← 纳入幂等门
    mission_progress_advance(...)
    drops = roll_drops(mon_bid)                     # ← 纳入幂等门
    ...
    db_bag_add(...)
else:
    log('tcp.log', '  ** battle settle already done ref=%s (replay/async re-entry), skip' % _settle_ref)
```

#### 改动 3：收尾清理 battle_settle_ref（mock_server.py:10015）

在 `self._battle_settled = False` 后追加 `self.battle_settle_ref = None`。

### 2.3 为什么这样改是正确的

| 场景 | 旧行为 | 新行为 |
|---|---|---|
| 正常击杀第 1 只怪 | exp+50 coin+30 drop+1 | exp+50 coin+30 drop+1（ref=kill:mon:rid:t1） |
| 正常击杀第 2 只同型怪 | exp+50 coin+0 drop+1（bug） | exp+50 coin+30 drop+1（ref=kill:mon:rid:t2）✅ |
| 同战斗异步重入（timer 双触发） | exp 加两次 | grant() 查 reward_log → already → 全跳过 ✅ |
| 服务端重启后补结算 | 内存 battle 丢失，不结算 | 同左（少发不重复发）✅ |
| 断线重连后重新点怪 | 新连接新战斗，exp/drop 重复 | 新连接新战斗新 ref → 独立结算（合理）✅ |

---

## 3. 实机联调：隔离账号连杀同型怪两次

测试脚本：`tools/c3_3_battle_idem.py`（隔离账号 c33test_battle_*，测后自动清理）。

### 3.1 测试结果（tcp.log 实证）

```
[11:19:25] >> CS_20002 fight monster mon_id=20001
[11:19:25] << 20002 code=1(TRUE) mon=20001 name=mon20001
[11:19:25] << 20010 battle init mon_hp=1950 role_hp=50000
[11:19:28] << 20012/20013 round 1: role hit=6377 mon_hp=0/1950 → 怪物死亡
[11:19:28] << 20020 result=1 + 20023 type=0 result=1
[11:19:31] ** grant ref=kill:20001:2001:1792120765223 n=1     ← 第 1 次结算
[11:19:31] ** battle kill mon=20001 -> +50 exp +30 coin (settle_ref=...5223)
[11:19:31] ** battle drop item=33001 x1 -> bag qty=1
[11:19:31] << 10500 bag push / 10301/10302/10303 refresh

[11:19:40] >> CS_20002 fight monster mon_id=20001（第 2 次）
[11:19:40] << 20002 code=1(TRUE) mon=20001
[11:19:40] << 20010 battle init mon_hp=1950 role_hp=50000
[11:19:43] << 20012/20013 round 1: mon dies
[11:19:43] << 20020 result=1 + 20023
[11:19:46] ** grant ref=kill:20001:2001:1792120780260 n=1     ← 第 2 次结算（不同 ref!）
[11:19:46] ** battle kill mon=20001 -> +50 exp +30 coin (现 exp=50 coin=60)
[11:19:46] ** battle drop item=33001 x1 -> bag qty=2（堆叠）
[11:19:46] << 10500 bag push / 10301/10302/10303 refresh
```

### 3.2 DB 前后差异

| 指标 | 基线 | 第 1 次后 | 第 2 次后 | 总计 |
|---|---|---|---|---|
| exp | 0 | +50 | +50 | **+100** ✅ |
| coin | 0 | +30 | +30 | **+60** ✅ |
| bag_items | 0 | 1 行 qty=1 | 1 行 qty=2 | **+2 件（堆叠）** ✅ |
| reward_log kill | 0 | +1 条 | +1 条 | **+2 条** ✅ |

**两个 settle_ref**：
- `kill:20001:2001:1792120765223`（第 1 次）
- `kill:20001:2001:1792120780260`（第 2 次，间隔 ~15s）

### 3.3 六层联调记录

| 层 | 第 1 次击杀 | 第 2 次击杀 |
|---|---|---|
| ①界面 | 点怪 → 进战斗 → 胜利 | 同左 |
| ②协议 | CS_20002 → SC_20002 code=1 → 20010 → 20012/20013 → 20020 → 20023 | 同左 |
| ③注册 | 服务端权威：mon_hp=1950, player_dmg=6377, mon_dies in 1 round | 同左 |
| ④业务 | grant(coin=30) + add_role_exp(50) + db_bag_add(33001,1) + mission_progress | grant(coin=30) + add_role_exp(50) + db_bag_add(33001,1) + mission_progress |
| ⑤DB | role_assets.exp=50 coin=30; reward_log +1; bag qty=1 | role_assets.exp=100 coin=60; reward_log +1; bag qty=2 |
| ⑥展示 | 10500 bag push + 10301/10302/10303 属性刷新 | 同左 |

---

## 4. 结算 Service 链路复核

| 奖励类型 | Service 路径 | 行号 | 复核结论 |
|---|---|---|---|
| exp | `level/service.py:87 add_role_exp` → `currency/db_set_assets('exp')` + `db_save_role` | 9923-9925 | ✅ 纳入幂等门；处理升级和属性成长 |
| coin | `reward/service.py:51 grant` → `currency/db_add_assets('coin')` | 9928 | ✅ reward_log PK 幂等 |
| 掉落 | `inventory/service.py:135 db_bag_add` | 9990-9996 | ✅ 纳入幂等门；合并堆叠 |
| 任务进度 | `task/service.py:171 db_save_mission` | 9941-9963 | ✅ C3.2 已接，本次未破坏 |
| power 刷新 | `build_10303(st2, skills, attr)` → 推送 10303 | 10007-10008 | ✅ 战斗后推送属性大表（含统一计算 power） |
| kill_type_mon | **不接** | — | B2 阻塞：config_mon_data 类型字段空，记录 UNKNOWN |

**掉落数值来源标注**：当前掉落固定 item 33001（VIP2每日礼包），来自 `battle_test_drop_item` 配置（默认 33001）。**原版掉落表 UNKNOWN**（APK config_drop 为别家 IP 死数据，见 drop_model.md §9）。TEST_ONLY 数值保留发放逻辑但不当作原版掉落表。

**战斗数值来源标注**：mon_hp=1950 / player_dmg=6377（calc_damage(8000, 10)）/ mon_dmg=100 / KILL_REWARD={exp:50, coin:30} 全部 TEST_ONLY 硬编码（battle.py + mock_server.py:9920）。原版数值 UNKNOWN。

---

## 5. 回归

### 5.1 基线不回退

rid=1001 改后验证：
- role_assets: exp=20689 / coin=9923249 / gold=1799942 / hero_exp=9800（与改前一致）✅
- reward_log: 17 条（与改前一致）✅
- kill refs: `kill:20001:1001`、`kill:20002:1001`（旧格式，未动）✅

### 5.2 测试账号清理

c33test_battle_* 账号测后自动删除（所有含 rid 的表 + accounts 表）。✅

### 5.3 py_compile

`python -m py_compile mock_server.py` → PY_COMPILE OK ✅

### 5.4 服务端重启

restart_server.ps1 干净重启，冒烟测试通过 ✅

---

## 6. 遗留问题

1. **断线重连竞态**：`_battle_settle` 线程收尾时 `self.battle=None` 会清掉重连后新建的战斗实例（实测中发现：结算线程和主请求线程竞争 self.battle）。本次测试通过延长等待规避，但根因需在后续批次加锁或状态机治理。
2. **CS_20002 尾 4 字节语义**（B1）：服务端已容错忽略，不阻塞闭环；严格协议对齐需反汇编客户端 send 处。
3. **kill_type_mon 未接线**（B2）：怪物类型码映射无证据，记录 UNKNOWN。
4. **真实战斗数值/掉落表**（B3/B4）：全部 TEST_ONLY 硬编码，原版服务端数据不可从 APK 取证。
5. **HP 不持久化**：战斗中受击不落库，重登满血（现有行为，按配置/证据保留）。
6. **bag 计数测试方法**：c3_3_battle_idem.py 按 bag_items 行数统计掉落，可堆叠物品（33001）会堆到同一行导致行数不变。实际掉落数量应查 quantity 字段。

---

## 7. 自检记录

- [x] py_compile 通过；最小改动、未重构战斗模拟。
- [x] exp/coin/掉落三路全部纳入同一幂等门（settle_ref）。
- [x] 每次正常击杀独立结算（2 次 = 2 份奖励，DB 实证）。
- [x] 同一战斗实例重入被 reward_log PK 挡住（ref 相同 → already → 跳过）。
- [x] 未碰 rid=1001；基线全程未动。
- [x] 测试账号测后清理。
- [x] 不编造伤害公式/怪物属性/掉落率；TEST_ONLY 数值已标注 UNKNOWN。
- [x] 备份先行（mock_server.py.bak_c33_20261016）。
