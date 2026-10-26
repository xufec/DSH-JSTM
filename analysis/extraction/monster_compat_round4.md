# 目标④ — 怪物数值 JSTM 兼容实现：验证 + 补强（第 4 轮）

> 用户指令：**「若怪物数值真值找不到原本数据则接受兼容实现」**。
> 本轮改动核心逻辑（已授权），改动范围：`server/monster/service.py`(29 行) + `server/mock_server.py`(9 行)，均有备份。

---

## 一、先说重要事实：兼容模型**本来就有**，缺的是「等级来源」这一环

`server/monster/service.py` 里已存在 **`JSTMCompatibleMonsterModel`**（Phase 5 产物），本就标了
`# INFERENCE: JSTMCompatibleMonsterModel, formula UNKNOWN per E1/E2` 并**留了替换点**
（`config_mon_data.json` 的 `Mon` 主表一旦非空即优先返回真值行）：

```python
_BASE_HP  = lambda lev: 200 + lev * 25     # lv70 → 1950
_BASE_ATK = lambda lev: 8   + lev * 1.2    # lv70 → 92
_BASE_DEF = lambda lev: 4   + lev * 0.6    # lv70 → 46
_BASE_EXP = lambda lev: lev * 8
_BASE_COIN= lambda lev: lev * 5
```

⇒ 所以本轮**不需要**新造模型；要做的是「**证明它真在跑**」+「**补强它最弱的一环**」。

### 1.1 证明它在跑（VERIFIED）

`GET /DSH_ADMIN/battle_replay?mon_id=20001` 的 `SC_20010` 原始 hex 里，怪段落是：

```
6d6f6e 00 06 7265706c6179 00 46 00000101 02 0000 079e 0000 079e ...
"mon"    len=6 "replay"    lev=70        group=2  hp_max=1950  hp=1950
```

`0x079e = 1950 = 200 + 70×25` ⇒ **数值确由该模型产生**，
而 `server/battle.py` 的 `MON_STATS hp_max=2400` **已不是实战路径**（其上方注释与现状不符，属过期说明）。

---

## 二、发现并修掉的缺陷：挂机怪等级被当成 **35 级**

改动前的实测（同一 hex 手法）：

| 怪 | 挂机图 | 配置里的等级区间 | 改动前 lev | 改动前 hp_max |
|---|---|---|---|---|
| 10101 | 星斗大森林 | 25–34 | 35 | **1075** |
| 10105 | 乾坤日月谷 | **65–74** | 35 | **1075** |
| 10106 | 魂殿遗迹一层 | **75–84** | 35 | **1075** |

⇒ **所有 101xx 挂机怪都被算成 35 级**：对 lv70 玩家而言 1075 血过弱，
且与「图是 65–74 档」的配置自相矛盾。
根因：`make_battle` 用 APK 表的 `fields[2]`（注释自承 **「疑似 level（INFERRED）」**）作等级。

---

## 三、改动（最小、可回滚）

| 文件 | 改动 |
|---|---|
| `server/monster/service.py` | 新增 `band_level(mon_id)`：读 `server/_guaji.json`（**CONFIRMED**，且该表已实机 UI 对表验证——挂机面板「乾坤日月谷 65–74 级」与配置逐字一致），返回该怪所属挂机图的**等级区间上界** |
| `server/mock_server.py` `make_battle()` | 等级解析顺序改为：**`band_level()`（CONFIRMED）> APK 表 `fields[2]`（INFERRED）> 1** |
| 备份 | `server/backup/{monster_service.py,mock_server.py}.bak_r_mon_bandlev_20261014` |

**取区间上界的理由**（已写进注释）：玩家按区间进图，怪按区间上界给数值，避免"图是 65–74、怪按 35 级"。

---

## 四、验证：六只怪逐字节对表（**CONFIRMED**）

`battle_replay` 的 `SC_20010` 里怪 `hp_max`（u32）与公式期望值：

| 怪 | 等级（来源） | 期望 hp_max | **hex 实测** | 一致 |
|---|---|---|---|---|
| 20001（非挂机，APK 字段 70） | 70 | 1950 | `00 00 07 9e` = **1950** | ✅ |
| 10101 星斗大森林 25–34 | 34 | 1050 | `00 00 04 1a` = **1050** | ✅ |
| 10103 宁静海湾 45–54 | 54 | 1550 | `00 00 06 0e` = **1550** | ✅ |
| 10105 乾坤日月谷 65–74 | 74 | 2050 | `00 00 08 02` = **2050** | ✅ |
| 10106 魂殿遗迹一层 75–84 | 84 | 2300 | `00 00 08 fc` = **2300** | ✅ |
| 10108 魂殿遗迹三层 95–104 | 104 | 2800 | `00 00 0a f0` = **2800** | ✅ |

⇒ **六条全中**；且非挂机怪 20001 **保持 1950 不变**（未被误伤）。

---

## 五、回归

| 项 | 结果 |
|---|---|
| 语法 | `mock_server.py` + `monster/service.py` 均 OK |
| 分发遮蔽 | 专用分支 1430 / 默认 0 / 未开放 0 ⇒ 无遮蔽 |
| miniloop ×3 | run1 **143/145**（既有 `10505` flake）、run2 **145/145**、run3 **145/145** |
| `/status` 基线 | `rid=1001 lv=70 scene=10001`，`power=724112` —— **不变** |
| diff 规模 | `mock_server.py` 9 行、`monster/service.py` 29 行 |

> 注：miniloop 用的是它**自己**的 `MON_STATS`（`min_loop_server.py:348`），与本改动无耦合；
> 那条 `10505` flake 上一轮已单独记录。

---

## 六、替换点（拿到真服真值后怎么做）

`get_mon()` 的优先级已写好：**只要 `server/cfg/config_mon_data.json` 的 `Mon` 主表非空，
就自动改用真值行**（`row['hp_max']` 等）——不需要再改代码。
当前该文件是 311 B 的空壳；**已提取的表在 `server/cfg_kconfig/config_mon_data.json`（1 MB，13,267 条怪）**，
但它是**无列名的数组形态**且**不含 HP/ATK 列**（只有名字/等级类字段/动画资源），
与项目既有结论「数值在服务端、APK 内无显式值」一致。

⇒ **结论（写入台账）**：怪物 HP/ATK 属**原版真值不可得**，按用户指令采用兼容实现；
本轮的贡献是：①确认兼容模型在跑 ②把它的**等级输入**从"疑似字段"升级为**CONFIRMED 配置**
③给出逐字节可复核的验收表 ④保留一键切真值的替换点。

---

## 七、下一轮

1. **③ 补完**：技能面板内切到 **修炼** 页签 → 验证「消耗/拥有」是否空白（直接对项目缺口 #5）；
2. 符文槽数据源定位（10621/10650 之外的命令）；
3. ② 日常（需客户端侧观测：frida hook `updateHuoli` 或反汇编 `daily_data.luac`）。
