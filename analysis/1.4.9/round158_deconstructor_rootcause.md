# R158：★★★ 一次**高价值的发现轮** —— 18 个核心配置的解构失败

> 新目标第 7 批。本批**没有加新命令**，但查出了**比加命令更有价值的东西**：
> **解构器对 18 个核心配置失败**（含 `config_item`/`config_skill`/`config_mon_data`/`config_role_attribute`）——
> 而**修它能一次解锁一大批命令**。
> **时间**：2026-09-30 23:40 – 次日 00:50。

---

## 一、★ 发现 1：`_unhandled_cs_sc.txt` 是**过期清单**

我一直在用它当"未实现清单"，但它**还是 R136 生成的样子** ——
里面列着我**已经做完的 40 条 `105xx`**。

**⇒ 重新生成后：1144 → 1057 条**（正好对应我累计做的 **87 条**）。
★ **教训**：**工具链的静态输入会过期** —— 每批开工前应**先刷新清单**。

---

## 二、★★ 发现 2：**18 个核心配置解出来是空的**

```
config_client, config_common, config_dragon, config_drop_item,
config_dungeon_jieyi, config_dungeon_reward_desc, config_fashion_upgrade,
config_helloween_data, config_holiday_crowd_lottery,
★ config_item（物品表）, config_map_block, config_mission_buffy,
config_mission_loop, config_mission_marry,
★ config_mon_data（怪物表）, config_role_attribute（角色属性表）,
★ config_skill（技能表）, config_skill_magic
```

★★ 这些是**最核心的表** —— `config_item` 应有 **1117 个物品**，而解出来是 `{}`。

---

## 三、★★★ 发现 3：根因方向已定位

诊断 `config_item.luac`（838KB）**用到的 21 种指令**：

```
TSETB  27119 次   ← ★ 本工具**从未处理**
TNEW   20472
TDUP   10456
TSETV   3609      ← ★ 本工具**从未处理**
KSHORT  1896 / KNUM 1117 / KSTR 596 / TSETS 228 / …
```

⇒ **`TSETB`（设表字段·字节键）出现了 2.7 万次**，而工具没处理它
⇒ **表根本没被填上** ⇒ 输出空表。**这就是根因。**

## 四、★★★ 发现 4：**`proto_index` 也要试**（部分改善）

`deconstruct(path, proto_index=N)` 默认只看 **`proto0`**，而"建表"的代码常在**后面的 proto**：

| 配置 | 默认(0) | 最佳 idx | 解出的 |
|---|---|---|---|
| `config_item` | 空 | **1** | `Config.ItemDecomList`（含 `18071`）|
| `config_skill` | 空 | **2** | `Config`（737B）|
| `config_mon_data` | 空 | **2** | `Config`（311B）|
| `config_role_attribute` | 空 | **1** | `Config_RoleAttr`（25B）|
| `config_common` | 空 | **0** | `Config/GameSystem/SystemNum/ShieldSystem`（1365B）|

★ **但都远小于应有规模**（`config_item` 只 120B，应 1117 项）
⇒ **光换 `proto_index` 不够，必须把表构建语义补全**。

---

## 五、我做了什么（**无损**）

1. **补了 `TSETB`/`TSETV`/`TSETR`/`TGETB`/`TGETV`** 的处理（方向对，但**语义还没完全对上** —— 见下）
2. **修了 `luajit_dis.py` 的 import 崩溃**（`sys.stdout.reconfigure` 在 stdout 已关时抛
   `ValueError: I/O operation on closed file` ⇒ 被 import 时直接崩）—— ★ 这个是**真修复**
3. **验证无损**：重跑批量解构 ⇒ **222 个配置 / 18 个空**，**与 R111 基线完全一致** ✓

★ **诚实说明**：我补的 `TSETB`/`TSETV` **没有真正解出 `config_item`**
（只解出 `ItemDecomList` 一小段）⇒ **a/b/c 的映射或指令语义还没对**。
**本次没有把它"假装修好"**，而是**如实记录方向 + 证据**。

---

## 六、★ 下一批的主攻方向（**最高杠杆**）

**完整实现 `deconstruct` 的表构建语义** ⇒ 一次解锁 18 个核心配置 ⇒
`config_item`（1117 物品）/`config_skill`/`config_mon_data`/`config_role_attribute`
**全部可用** ⇒ 一大批"无源"命令立刻有真实数据。

**做法建议**：
1. 用 `luajit_dis` 打印 `config_item` **proto1 的完整指令序列**，逐条对照 LuaJIT 语义
2. 先用**一个已知正确的配置**（如 `config_dungeon_new`，34 项解得好）做**回归基准**：
   改一处语义就跑一次，确认**不破坏已知正确的**
3. 对照 LuaJIT 官方 `lj_bc.h` 的 `TSETB`/`TSETV`/`TSETR` 定义（注意 A/B/C 的**寄存器 vs 常量**差别）
4. **不要一次改太多** —— 每改一个指令就验证

---

## 七、全量验证（服务端不受影响）

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **354** / 默认 21 / 未开放 6）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 105-105** / 门禁 E **PASS** |
| 配置解构 | **222 个 / 18 个空**（与基线一致 ⇒ **无损**）|
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 八、产出物

| 文件 | 说明 |
|---|---|
| `analysis/1.4.9/_unhandled_cs_sc.txt` | ★ **重新生成**（1144 → **1057**）|
| `tools/config_deconstruct.py` | 补 `TSETB`/`TSETV`/`TSETR`/`TGETB`/`TGETV`（**方向对、语义待完善**）|
| `tools/luajit_dis.py` | ★ **修 import 崩溃**（`reconfigure` 加 try/except）|
| `analysis/1.4.9/round158_deconstructor_rootcause.md` | 本报告 |

---

## 九、新目标进度

| 指标 | 现在 |
|---|---|
| **专用分支** | **354**（本批未变）|
| **回归项** | **41**（失败 0）|
| 六道门禁 | **全 PASS** |
| ★ **潜在缺口清单** | **1057 条**（**最新**；此前用的一直是过期的 1144）|
| ★ **重大待办** | **修解构器 ⇒ 解锁 18 个核心配置**（最高杠杆）|
