# 第十八轮：战力系统引擎 + 属性数据提取

> 用户要求：① 幸运转盘与签到同界面 ② 角色属性参考 5 个文件 + 读取 3 个 APK 原数据 ③ 完善战力系统 ④ 剧情待完善

---

## 一、★★ 战力系统引擎 —— ✅ **已实装（基于原版数据）**

### 数据源（`config_attr.luac` proto[0]，CONFIRMED）

```
AttrLen = 64（共 64 项属性）
AttrId2Key   = {101:strength, 102:intellect, 103:armor, 104:体质, 105:atk_s(物攻), 106:atk_p(法攻), ...}
AttrId2Str   = {101:'力量', 102:'智力', 105:'物攻', 109:'生命', ...}
AttrKey2Str  = {atk_speed:'速度', dodge:'躲闪', hit:'命中', ...}
**AttrPower     = {atk_speed:450, dodge:275, hit:275, crit:183, tenacity:183,
                  atk_p:106, atk_s:106, control:90, anti_control:90,
                  def_abs:82, atk_abs:82, atk_abs_p:41, def_s:33, ...}**   ← 战力权重
AttrKeyIsShow  = {atk_s, atk_p, atk_speed, crit, def_s, def_p, dodge, hit, hp_max, tenacity}
```

### 战力公式（原版语义）

```
战力 = Σ( 属性值[key] × AttrPower[key] )
  权重为 0 的基础项（strength/intellect/armor/hp 等）**不参与战力**。
```

### 实装

**`server/power.py`**：
- `attr_power(key)` / `calc_power(attrs)` / `power_items(attrs)`
- 数据来自 `server/_attr_data.json`（从 APK 原样提出）

**服务端**：新增 `/DSH_ADMIN/power` 接口
```
GET /DSH_ADMIN/power
→ {"ok":true, "power":<战力>, "attrs":{...}, "detail":[{"key","name","contrib"}], "module":true}
```

**单元测试**：
```
attr_power('atk_speed')=450 ｜ attr_power('atk_s')=106 ｜ attr_power('strength')=0
calc_power({atk_s:120, atk_p:200, dodge:30, hit:30, crit:50, hp_max:10000, strength:50}) 
  = 120*106 + 200*106 + 30*275 + 30*275 + 50*183 + 10000*24(hp_max权重) = 299570 ✓
  （★ 手算验算时曾漏掉 hp_max，其实 weight=24，生命参与战力）
```

---

## 二、★★ 角色属性数据 —— ✅ **已提取**

| 表 | 内容 | 状态 |
|---|---|---|
| `config_attr` | 64 项属性 id/key/str/power/partnerPower 全量 | ✅ `server/_attr_data.json` |
| `config_role_attr` | **等级升级表**（exp_total/exp_max/sinew_max/attr_point 每级） | ✅ 已识别（非属性向量） |
| `config_role_career` | **6 职业**（1玄武/2火凤/3白虎/4琉璃/5神机/9测试）+ `attr` 字段 | ✅ 职业识别；**attr 为嵌套结构未解** |
| `config_fight` | `HeroModifyDamage`（战斗修正） | ✅ 字段识别 |
| `config_skill` | 技能（前已提取真实 bid） | ✅ |

**等级表样例（config_role_attr）：**
```
Lv1: exp_total=240, exp_max=240, attr_point=0, sinew_max=120
Lv2: exp_total=481, exp_max=481
Lv3: exp_total=1452, exp_max=971
```

---

## 三、★ 版本关系（3 个 APK 交叉验证）

```
anzbao\jstm.apk         1.4.9     347 config 表
anzbao\jstm_142165.apk  更高版     355 表（**超集** —— 1.4.9 有的它都有）
anzbao\dldlJl.apk       另一渠道    256 表（少 92 张）
```
**⇒ 142165 多出的 8 张表**（foot_print/golden_egg/kaifu_gift/top_level/treasure_palace/vip_diamond/cmd_resolve_210/221）
**是 1.4.9 没有的功能 ⇒ 与我们的目标无关。**
**⇒ 1.4.9 与 142165 的角色/属性数据兼容（可交叉校验）。**

---

## 四、⚠ 战力 = 0 的原因（如实）

**`role_state()` 返回的角色属性向量（atk_s/hp_max 等）**未填充**（都默认 0）⇒ 战力算出 0。**

**根因：** 属性的初始向量来自**职业基础属性**（`config_role_career` 的 `attr` 字段），
但该字段是**嵌套结构**（不是简单 hash/array），**本轮未解开**。

**⇒ 战力引擎已就绪，只差"角色属性向量"这个输入。** 一旦从职业表填上，战力即非零。

**下一步**：解 `config_role_career` 的嵌套 `attr` → 按职业+等级生成初始属性向量 →
填充 `role_state` → 战力生效。

---

## 五、幸运转盘 / 剧情（未完成，如实）

### 幸运转盘
**用户确认与签到同界面。** `dailysign` 模块排查出 `million/`（百万）、`online/`、`loginday/`、
`moneytree_*` —— **但没有明显的 turntable**。配置表 `config_holiday_lucky_turntable_data`(781B) 已找到。
**尚未定位转盘的 CMD**。`20100` 已确认是**变强面板**（power/promote），不是转盘。

### 剧情
**未开始**（本轮聚焦属性/战力）。剧情链已能推进（任务提交已通）。

---

## 六、自查

```
mock_server.py OK ｜ server/power.py 单元测试通过 ｜ 服务端 8080/9000（PID 38492）｜ stderr 0 字节
新增：server/power.py（战力引擎）+ server/_attr_data.json（64 项原版数据）
      + /DSH_ADMIN/power 接口 + server/_career_attr.json（占位）
```

---

## 七、请实机 / 后续方向

1. **战力**：现在接口返回 0（因属性未填充）；我下步解职业 `attr` 填充属性向量。
2. **幸运转盘**：请告诉我转盘**在弹出的那个界面里叫什么/长什么样**（是"幸运转盘"tab 还是"百万"？）
   —— `million`（百万）可能就是它，我优先查。
3. **剧情**：需要你明确"哪些剧情待完善"（具体哪个任务链卡住？）