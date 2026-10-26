# Phase 4D —— ✅ 完成（角色面板 + 全部属性显示正确）

> **最终结论：两条判据全部命中，Phase 4C/4D 目标闭环。**
> 1. **`attr` 的正确编码 = "计数 + 1 行"**（不是内联结构体）—— 已由"处理器是否被调用"判定。
> 2. **角色面板已在 (2174, 104) 稳定打开，且全部属性显示为非 0**，
>    数值与服务端下发的**完全一致**。

---

## ★★★ 判据一：`rgp_hander10303` 被调用（编码正确的直接证据）

把 `attr` 从"内联结构体"改为 **"计数 + 1 行"**（`build_10303` 里在 24 个字段前加 `w_u16(1)`），
重启后实测：

```
t=roleH&v=rgp_hander10303_rid_1001_name_DSH_lev_1_exp_0_exp_max_nil_
        gold_1000_gold_acc_5000_career_1_sex_0_skill_list:_1
[23:36:18]  << 10303 SC_10303 attr (hp_max=1000 atk=100) (192 bytes)
```

**⇒ 处理器第一次被调用** —— 回包被正确派发了。

顺带印证字段语义完全正确：
`exp=0`、`gold=1000`、`gold_acc=5000` 都读到了；而 **`exp_max=nil` 也是对的**
（`exp_max` 属于 `SC_10301`，不在 `SC_10303` 里）。

## ★★★ 判据二：面板属性全部非 0（界面闭环）

点 **(2174, 104)** 打开面板，视觉逐字判读：

| 项 | 面板显示 | 服务端下发 | 一致 |
|---|---|---|---|
| 职业 | 玄武 | `career=1`(玄武) | ✅ |
| 宗门 | 无 | `gname=''` | ✅ |
| 等级 | 1 | `lev=1` | ✅ |
| 生命 | **1000** | `hp_max=1000` | ✅ |
| 速度 | **100** | `atk_speed=100` | ✅ |
| 物攻 | **100** | `atk_s=100` | ✅ |
| 物防 | **80** | `def_s=80` | ✅ |
| 法攻 | **100** | `atk_p=100` | ✅ |
| 法防 | **80** | `def_p=80` | ✅ |
| 命中 | **50(0%)** | `hit=50` | ✅ |
| 躲闪 | **50(0%)** | `dodge=50` | ✅ |
| 暴击 | **30(0%)** | `crit=30` | ✅ |
| 抗暴 | **30(0%)** | `tenacity=30` | ✅ |
| 经验 | 0/100 | `exp=0 / exp_max=100` | ✅ |

**无空白、无 nil、无乱码、无报错。**

**⇒ 角色数据（姓名 / 职业 / 等级 / 经验 / 资产 / 全部属性）已全部由服务端提供，
并在原版角色面板中正确显示。**

---

## ★ 本次修正（一处，单变量）

```python
# server/mock_server.py  build_10303()
-  # attr 大表（内联结构体，按定义顺序逐字段）
-  for name, t in ATTR_FIELDS: ...
+  # attr 大表 —— 改为"计数 + 1 行"编码
+  b += w_u16(1)
+  for name, t in ATTR_FIELDS: ...
```

`SC_10303` body 由 **184 → 186 字节**（应答包 190 → 192 字节）。

**判据选择是关键**：上一版我用"面板属性是否非 0"作判据，因面板打不开而卡住；
改用 **"`rgp_hander10303` 是否被调用"** 后一次就定位到编码形式错误 ——
**这条判据不依赖 UI，稳定且直接。**

---

## 日志位置

```
logs/1.4.9/role_4d_verify_probe.log   关键证据（rgp_hander10303 是否被调用）
logs/1.4.9/role_4d_verify_tcp.log
shots/ROLE_PANEL_AT_2174_104.png      属性全 0（修正前）
shots/stage4d_attr_fixed.png          ★ 属性全部非 0（修正后）
```

---

> **本轮最终结论（有完整证据链）**
> 1. **角色面板坐标 = (2174, 104)**（用户提供），**点击可稳定打开**，已实测确认。
> 2. 面板显示的**框架数据全部正确**：`职业 玄武 / 宗门 无 / 等级 1 / 经验 0/100`，
>    说明 `10301` / `10302` 的数据链是通的。
> 3. **属性数值仍然全为 0**（生命/速度/物攻/物防/法攻/法防/命中/躲闪/暴击/抗暴/综合战力）。
> 4. 与"**`rgp_hander10303` 从未被调用**"这一证据完全吻合
>    ⇒ **`SC_10303` 的回包没有被客户端派发给处理器**，最可能是
>    **`attr` 的编码形式猜错**（我按"内联结构体"，实际可能是"计数 + 1 行"）。

---

## ★★ 面板打开的确认（坐标 (2174, 104)）

```
adb shell input tap 2174 104
```

**视觉判读（`shots/stage4d_2174.png`）** —— 面板成功打开：

| 项 | 显示值 |
|---|---|
| 职业 | 玄武 |
| 宗门 | 无 |
| 等级 | **1** |
| 基础属性 | 生命 0、速度 0 / 物攻 0、物防 0 / 法攻 0、法防 0 / 命中 0(0%)、躲闪 0(0%) / 暴击 0(0%)、抗暴 0(0%) |
| 经验 | **0/100** |
| 当前盈福经验 | 0 |
| 综合战力 | 0 |
| 异常 | **无空白、无 nil、无乱码、无报错** |

⇒ **面板能稳定打开，框架数据正确，唯独属性数值全 0。**

---

## ★★ 属性为 0 的原因（已定位，证据一致）

| 证据 | 内容 |
|---|---|
| 协议已应答 | `<< 10303 SC_10303 attr (hp_max=1000 atk=100) (190 bytes)` |
| **处理器未被调用** | 探针包住了 `RoleCtrl` 的四个处理器，日志里**只有 `rgp_hander10301`**，**没有 `rgp_hander10303`**（也没有 `NOT_function`，说明钩子装上了、只是没被调用） |
| 界面结果 | 属性全 0 |

**⇒ 回包发出去了但**没有派发**⇒ 解析失败 ⇒ `attr` 编码形式不对。**

`attr` 的编码形式 manual 没明说，当前实现按"**内联结构体**"写（body 184 字节）。
`roles`（同为 `table(...)`）用"**计数 + 行**"是对的，而 `attr` 没有 id 字段，
所以我当初选了内联 —— **从证据看这个选择是错的**。

---

## ★ 下一步（单变量、判据稳定、坐标已知）

**把 `attr` 改成"计数 + 1 行"编码**（`w_u16(1)` + 24 个字段），然后：

1. **判据一（最稳）**：看探针里 **`rgp_hander10303` 是否被调用** —— 被调用即编码对了；
2. **判据二（界面）**：点 **(2174, 104)** 打开面板，看属性是否变成非 0
   （期望值：生命 1000、物攻 100、物防 80、法攻 100、法防 80、命中 50、躲闪 50、暴击 30、抗暴 30）。

两条判据互补：先看 1（快、稳），再用 2 收尾（直观）。

---

## 修改文件

> **最终结论**
> 1. **角色面板已在原版客户端成功打开**，并显示出姓名/职业/等级/经验/战力/装备位/属性表
>    （打开位置：**右上角、充值按钮右边的图像方框**）。
> 2. **`SC_10303` 已实现并在协议层面验证**（客户端请求 → 服务端 190 字节应答）。
> 3. **面板里的属性此前全为 0，正是因为缺 `SC_10303`** —— 已补上。
> 4. 但"补上 `10303` 后属性是否显示非 0"这一**界面验证尚未完成**（测试中途服务端进程意外退出）。

---

## ★ 本轮最后的实现：`SC_10303`

### 字段依据（`protocol/manual.md` 的 `SC_10303` 定义，逐字段照写）

```
rid u32, srv_id str, name str, lev u16, is_vip u8, vip_lev u8, sex u8, career u16,
volume/store_volume/store_partner_volume u8, volume_open/store_volume_open/
store_partner_volume_open u8, attr_point u16, skill_list table(bid:u32),
power/exp/gold/coin/gold_acc/sinew/experience/coupon/vitality/guild_contrib/
practice_exp/tower_cent/arena_cent 均 u32,
attr table(24 项：strength/intellect/armor/constiution 为 u16，
           其余 atk_s…tenacity_rate_show 为 u32),
mspd u16, animate_res table, vip_exp u32, jiebai_title str, jiebai_lev u8
```

**`attr` 的编码形式 manual 没明说**：本实现按"**内联结构体**"写（理由：`attr` 没有 `id` 字段，
而 `roles` 有 `rid` 且有计数前缀）。**若客户端读不出，需改试"计数+1 行"** —— 用面板是否
显示非 0 属性来判定。编码实算 body = **184 字节**。

### 实测（协议层面已验证）

```
t=send4b&v=10303_ok_true_err_nil                    ← 探针调用 RoleCtrl:sender10303() 成功
[23:15:57]  >> cmd=10303 ? body(4)=00 00 03 e9
[23:15:57]  << 10303 SC_10303 attr (hp_max=1000 atk=100) (190 bytes)
```

⇒ **`10303` 已实现且客户端能触发、服务端能应答。**

---

## ★★ 角色面板成功打开（用户提示"右上角、充值右边的图像方框"是对的）

**视觉判读（`shots/ROLE_PANEL_OPENED.png`）**：

| 区域 | 内容 |
|---|---|
| 面板标题 | **「背包」**；标签页：背包 / 称号 / 戒指 / 时装 / 魂骨 |
| 左上角 | VIP勋章 `1`、**`DSH`**、**`玄武 LV.1`** |
| 装备位 | **武器 / 护手 / 鞋子 / 头盔 / 衣服 / 腰带** |
| 中央 | 角色立绘 + **综合战力：0** |
| 右侧「属性」 | **职业 玄武** / 宗门 无 / **等级 1** / 生命 0、速度 0 / 物攻 0、物防 0 / 法攻 0、法防 0 / 命中 0(0%)、躲闪 0(0%) / 暴击 0(0%)、抗暴 0(0%) / **经验 0/100** / 当前盈福经验 0 |

**⇒ 姓名、职业、等级、经验、战力栏、装备位、属性表都能出现，无空白 / 无乱码 / Lua 错误 0 条。**
**唯一的缺口就是属性数值全 0 —— 即 `SC_10303`，本轮已补。**

### 打开方式的经验（写下来省得再试）

- **程序化打开走不通**：`openHeroPanel` 报 `attempt to index global 'HeroBtnTab' (a nil value)`，
  而 `HeroBtnTab` 全 APK **1 处引用、0 处定义** ⇒ 客户端自身缺陷，服务端无法修。
- **但正常点击能打开**：位置在 **右上角、充值按钮右边的图像方框**（本轮验证）。
  之前在右上角偏下点击会被当成**地图点击**（日志里出现 `10204 x18` = 角色移动），点不到 UI。

---

## ★★★ 本轮最终验证尝试（结论收敛）

### 试过的手段与结果

| 手段 | 结果 |
|---|---|
| 12 点阵盲点（x 2380~2500, y 28~170） | ❌ 未复现（该组点曾成功一次，但不可重复） |
| 在截图上画带坐标网格、让视觉读位置 → 得 (2100,100) | ❌ 按该点点击仍未打开 |
| **自验证扫描**（逐点点、每次截图与基线比对，变化 >12% 即判命中） | ⚠️ **误报**：第一次点 (1900,40) 就报 98% 变化，实为**角色移动导致地图视角变化**，不是面板 |
| 更细网格（100px 线）+ 视觉读坐标 | ❌ 视觉读数自相矛盾（把"充值"读到 x=800，与"右上角"定位矛盾） |

**⇒ 结论：在"用坐标点 UI"这条路上，我缺乏可靠的位置基准，继续盲试价值不大。**

### ★ 但协议侧拿到了一个**决定性证据**

补上 `SC_10303` 后重启实测（`logs/1.4.9/role_4d_verify_probe.log`）：

```
[23:24:41]  << 10302 SC_10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)
[23:24:41]  << 10303 SC_10303 attr (hp_max=1000 atk=100) (190 bytes)   ← 已应答
[23:24:43]  << 10301 SC_10301 role info (109 bytes)
```

而客户端处理器命中记录**只有 10301，没有 10303**：

```
t=roleH&v=rgp_hander10301_rid_1001_name_DSH_lev_1_exp_nil_exp_max_100_…_skill_list:_1
t=roleH&v=hander10333_NOT_function_nil
（没有任何 rgp_hander10303 记录，也没有 rgp_hander10303_NOT_function）
```

⇒ **钩子装上了、函数却从未被调用** ⇒ **`SC_10303` 的回包没有被派发给处理器**，
最可能是**回包解析失败**，而失败的嫌疑就是 **`attr` 的编码形式猜错**
（我按"内联结构体"编码，实际可能是"计数 + 1 行"）。

### ★ 下一步（单变量、**不需要点 UI**，判据稳定）

**把 `attr` 改成"计数 + 1 行"编码**，判据看 **`rgp_hander10303` 是否被调用**：

- 被调用 ⇒ 编码对了，再看它解析出的属性数值（探针可 dump）；
- 仍不被调用 ⇒ 两种形式都不对，回 `cmd_resolve_103.luac` 逐指令还原。

**这条判据比"属性是否显示"稳定得多** —— 本轮正是靠它把问题从"界面看不出来"
收敛到"回包是否被派发"这一层。

---

## 修改文件

| 文件 | 改动 |
|---|---|
| `server/mock_server.py` | ① 新增 `ATTR_FIELDS`（24 项，按 manual 顺序）+ `ATTR_DEFAULTS`（非 0 默认值）<br>② 新增 `build_10303(role, skills, attr)`（含资产 14 项 + attr 大表 + skill_list）<br>③ `_reply()` 新增 `10303` 分支 |
| `server/dsh_fake_login.lua` | 探针新增：`sender10303` 确定性触发；`rgp_hander10303` 处理器挂钩；`openRole*` 主动打开尝试 |
| `server/config.json` | （沿用）`role` / `skills` / `world_lev` |

---

## 日志位置

```
logs/1.4.9/role_4d_openprobe.log   打开尝试 + open 系列报错
logs/1.4.9/role_4d_grid_tcp.log    面板成功打开期间的 TCP
logs/1.4.9/role_4d_tcp.log         首次点击扫描（含 10204 x18）
shots/ROLE_PANEL_OPENED.png        ★ 面板成功打开
shots/stage4d_attr2.png            补 10303 后的尝试（面板未开）
```

---

## 仍然缺失

1. **属性非 0 的界面验证**（本轮被服务端意外退出打断）。
   若验证后仍全 0 ⇒ 说明 `attr` 应按"计数+1 行"编码，改试即可。
2. `10341`（头像查询）未实现。
3. 主界面金币显示与下发值对不上（未解释）。
4. 角色数据持久化（4E）未开始。

---

**按阶段纪律：本 Phase 主体完成（面板已打开、`SC_10303` 已实现并协议验证），
剩一步界面验证。**

**[WAITING FOR NEXT INSTRUCTION]**

> **最终结论：角色面板已在原版客户端成功打开，并显示出角色数据。
> 同时暴露出下一个明确的缺口：属性（attr）全为 0 —— 即 `SC_10303` 未实现。**

---

## ★★★ 成功：面板打开并显示数据

**打开方式**：在**右上角角色信息区**点击（用户提示"角色面板在右上角"是对的）。
一开始的点击落在右上偏下，被客户端当成**地图点击**（日志里出现 `10204 x18` = 角色移动），
把点阵上移到最右上角区域后，面板成功打开。

**视觉判读（`shots/stage4d_grid.png`）**：

| 区域 | 内容 |
|---|---|
| 面板标题 | **「背包」**；竖向标签页：**背包 / 称号 / 戒指 / 时装 / 魂骨** |
| 左上角信息 | VIP勋章 `1`、**`DSH`**、**`玄武 LV.1`** ← **姓名与等级都显示出来了** |
| 装备位 | **武器 / 护手 / 鞋子 / 头盔 / 衣服 / 腰带**（六格） |
| 中央 | 角色全身立绘 + **「综合战力：0」** ← **战力栏出现** |
| 右侧「属性」面板 | **职业 玄武** / 宗门 无 / **等级 1**<br>基础属性：生命 0、速度 0 / 物攻 0、物防 0 / 法攻 0、法防 0 / 命中 0(0%)、躲闪 0(0%) / 暴击 0(0%)、抗暴 0(0%)<br>**经验条：0/100** ← **经验显示出来了**<br>当前盈福经验：0 |
| 底部 | 时装 / 钻石 / 玫瑰 / 返回；资源栏：钻石 0、金币 0、红色漩涡 0 |

**⇒ 姓名、职业、等级、经验、战力、装备位、属性表 —— 全都出现了，且无空白、无 nil、无乱码。**

---

## ★★ 由此得出的下一个明确缺口

面板里**所有属性数值都是 0**（生命/物攻/物防/法攻/法防/命中/躲闪/暴击/抗暴），
而 `SC_10303` 正是携带 `attr` 大表（24 项）的那条协议 —— **它尚未实现**。

```
SC_10303.attr = table(strength:u16, intellect:u16, armor:u16, constiution:u16,
   atk_s:u32, atk_p:u32, def_s:u32, def_p:u32, hp_max:u32, atk_speed:u32,
   hit:u32, dodge:u32, crit:u32, tenacity:u32, red_def_s:u32, red_def_p:u32,
   atk_abs:u32, def_abs:u32, reduce:u32, hurt:u32,
   hit_rate_show:u32, dodge_rate_show:u32, crit_rate_show:u32, tenacity_rate_show:u32)
```

**⇒ 4D 的收尾动作应是：实现 `SC_10303`，把这些属性填成非 0，再看面板是否显示。**

另外本轮客户端请求了 `10341`（头像查询，`CS{id_list}` → `SC{rid,srv_id,id,img,upload_time}`）——
面板右上角的角色头像可能依赖它（**未确认**）。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| `server/dsh_fake_login.lua` | 探针新增"主动打开角色面板"区块（`RoleCtrl` 的 `openRoleHeroPanel/openHeroPanel/openMainPanel`），用于 4D 取证 |
| （服务器业务逻辑） | **未改** |

---

## 2. 协议证据

### 2.1 主动打开的实测（含报错，都是客户端侧信息）

```
openMainPanel_ok=true    err=nil
openHeroPanel_ok=false   err= game/role/role_ctrl.luac:0:
                              attempt to index global 'HeroBtnTab' (a nil value)
openRoleHeroPanel_ok=false err= game/role/new_ui/role_show_panel.luac:0:
                              attempt to index a nil value
```

`HeroBtnTab` 全 APK **只有 1 处引用（`role_ctrl.luac proto[39]`）、0 处定义**
⇒ 这条"程序化打开"的路走不通（客户端自身缺陷），
**但用正常 UI 点击（右上角）是能打开的** —— 这也是最终成功的方式。

### 2.2 打开期间的角色协议（均正常应答）

```
>> cmd=10301  → << 10301 SC_10301 role info (109 bytes)
>> cmd=10302  → << 10302 SC_10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)
>> cmd=10331  → << 10331 SC_10331 code=0
>> cmd=13340  → << 13340 SC_13340 profile name=DSH lev=1
>> cmd=14901  → << 14901 SC_14901 cur_bid=0 xs_title_list=0
>> cmd=10341  （头像查询，未实现）
>> cmd=10999  CS_10999{msg:string}，无 SC 定义 ⇒ 单向日志消息，无需应答
```

---

## 3. 测试结果

| 测试 | 结果 |
|---|---|
| 能否打开原版角色 UI | ✅ **能**（右上角角色信息区点击） |
| 是否出现空白 | ✅ 无空白 |
| 是否报错 | ✅ Lua 错误 0 条；无报错弹窗 |
| 是否继续请求服务器协议 | ✅ 请求了 10301/10302/10331/13340/14901/10341 |
| 服务器是否收到 | ✅ 全部收到 |
| 客户端期待什么响应 | ✅ 角色数据要 `10301`/`10302`；**属性要 `10303`（未实现）** |
| 姓名/职业/等级/经验/战力 | ✅ **全部显示**（DSH / 玄武 / LV.1 / 0/100 / 综合战力 0） |
| 具体属性数值 | ⚠️ **全为 0**（缺 `SC_10303.attr`） |

---

## 4. 日志位置

```
logs/1.4.9/role_4d_openprobe.log   打开过程探针上报（含 open 系列报错）
logs/1.4.9/role_4d_open_tcp.log    打开期间的 TCP 日志
logs/1.4.9/role_4d_tcp.log         首次点击扫描日志（含 10204 x18，说明点到了地图）
shots/stage4d_grid.png             ★ 角色面板成功打开的截图
shots/stage4d_locate.png / stage4d_panel2.png   之前的状态截图
```

---

## 5. 仍然缺失的问题

1. **`SC_10303` 未实现** ⇒ 面板属性全 0（生命/物攻/物防/法攻/法防/命中/躲闪/暴击/抗暴/战力）。
   **这是 4D 收尾的直接目标**（字段定义已确认，见上文）。
2. `10341`（头像查询）未实现 —— 面板头像区可能依赖（未确认）。
3. 主界面金币显示与下发值对不上（仍未解释）。
4. 角色数据持久化（4E）未开始。

---

**按阶段纪律：本 Phase 主体已完成（面板已打开并验证），收尾动作是补 `SC_10303`。**

**[WAITING FOR NEXT INSTRUCTION]**

> **本阶段目标**：进入地图后打开原版角色面板，观察它请求什么协议、缺什么数据。
> **禁止**：重做 UI。
> **结论先行**：本轮**尚未打开角色面板** —— 但定位到了它的类，并排除了"点击坐标算错"这一嫌疑。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| — | **本阶段未改任何代码**（只做观察与静态定位） |

---

## 2. 协议证据 / 静态定位成果

### 2.1 主角色面板的类已找到

遍历 `assets/src/game/role/` 下所有 `.luac` 的 `GSET` 类名，得到全部角色 UI 类：

```
RoleCheckPanel / RoleCheckView / …（check 系列，属性核对页）
RoleChangNameView / RoleDecoratePanel / RoleFashionView / FashionGrowPanel
RolePackView / **RoleShowPanel** / RoleDisplayPanel / RoleHeroPanel
▶ **RoleMainView**   ← game/role/new_ui/ver_one/role_main_view.luac（主角色面板）
RoleWeaponView / WeaponGainPanel
```

`RoleMainView` 的方法（`TSETS` 名）：

```
__init, initView, initData, initMainView, openByTab, createTabBar, createTitleTxt,
createWealth, createEquipBtn, showRoleAttrMsg, showRolePackView, showWareHouse,
showFashionView, showPackDataByType, role_show_view, is_show_warehouse
```

其中 **`initView` / `initData` / `openByTab` / `showRoleAttrMsg`** 就是"打开面板并填数据"的入口。

### 2.2 谁引用它

```
game/role/new_ui/ver_one/role_hero_panel.luac   proto[10]
game/role/new_ui/ver_one/role_main_view.luac    proto[41]（类表自身）
```

⇒ 主角色面板很可能由 **`RoleHeroPanel`** 这一层拉起（**待进一步确认**）。

---

## 3. 测试结果（本轮实测）

### 3.1 点击扫描（屏幕 2560×1440）

依次点击了 6 个候选位置：

| 坐标 | 猜测 |
|---|---|
| (2380,150) | 右上角色信息框 |
| (150,150) | 左上地图/头像 |
| (2300,60) | VIP 区 |
| (1280,1300) | 底部中央 |
| (130,1380) | 左下角 |
| (2430,1380) | 右下角 |

**结果**：点击期间 TCP 日志里**只出现心跳与移动包**（`1199 x3`、`10204 x2`），
**没有任何面板相关的新协议**。

### 3.2 但有一个重要发现：**面板确实能打开**

视觉判读点击后的截图：**画面打开了「世界地图」面板**（半透明浮层 + 右上金色 X 关闭按钮 +
右侧竖排「回城 / NPC / 世界地图」按钮）。

⇒ **UI 响应正常、面板能打开**，只是我点的位置落在"世界地图"上，**不是角色面板**。

### 3.3 排除了"坐标算错"这一嫌疑

用程序量了截图的非黑区域：

```
截图尺寸 (2560,1440)；非黑区域边界 left=0 top=0 right=2559 bottom=1439
```

⇒ **游戏画面就是完整一屏，没有黑边/letterbox** ⇒ **点击坐标系是对的**，
问题是**主 HUD 上确实没有"角色/属性/人物"字样的按钮**（视觉模型也确认了这一点）。

主 HUD 可见按钮（视觉确认）：

```
顶部：商城 / 首充 / VIP勋章 / 充值 / 角色信息框(DSH, 0)
右侧：任务 / 队伍
左下：好友 / 聊天 / 语音 / 经验
右下：魂囊 / 更多
（世界地图浮层打开后另有：回城 / NPC / 世界地图）
```

---

## 4. 日志位置

```
logs/1.4.9/role_4d_tcp.log        点击扫描期间的服务器 TCP 日志（本轮生成）
shots/stage4d_tapsweep.png        点击后的截图（世界地图浮层）
shots/stage4d_normal.png / stage4d_state.png   后续截图
```

---

## 5. 仍然缺失的问题（下一轮的直接目标）

1. **角色面板的入口按钮没有在主 HUD 上直接暴露** ⇒ 需要确定它到底挂在哪里。
   两条可行路径（都不需要改 UI）：
   - **静态**：继续追 `RoleHeroPanel` / `RoleMainView` 的**调用者**，
     看是哪个按钮的点击回调把它拉起来的；
   - **动态**：在探针里**包住 `RoleMainView`**（`initView`/`openByTab`），
     面板一打开就能看到它跑没跑、并顺带看它读了哪些字段 ——
     **即使我点不到，也能用"主动调用"的方式把它打开**（与 4B 验证协议同一手法）。
2. 角色面板一旦打开，重点观察：
   - 是否空白 / 是否报错
   - **它请求了什么 CMD**（很可能是 `10301`/`10302`/`10303` 的组合）
   - `SC_10303` 的 `attr` 大表**是否需要**（目前未实现）
3. 主界面金币显示与下发的 `gold=1000`/`gold_acc=5000` 对不上的问题，仍未解释。

---

## 6. ★★ 用"主动打开"的方式继续追（本轮新增，含决定性发现）

### 6.1 找到 `RoleCtrl` 的 open 系列入口

反汇编 `role_ctrl.luac` 的 `TSETS` 名，得到全部打开方法：

```
openMainPanel        ← 主面板
openHeroPanel        ← 英雄/角色面板（RoleHeroPanel → RoleMainView）
openRoleHeroPanel
openOtherRole / openPointPanel / openChangeEffectPanel /
openFashionGrowPanel / openRoleDecoratePanel / openWeapon*
```

### 6.2 在探针里主动调用（不再依赖点击坐标）

**实测结果（三次调用，报错信息非常精确）：**

```
openMainPanel_ok=true   err=nil
openHeroPanel_ok=false  err= string game/role/role_ctrl.luac:0:
                              attempt to index global 'HeroBtnTab' (a nil value)
openRoleHeroPanel_ok=false err= string game/role/new_ui/role_show_panel.luac:0:
                              attempt to index a nil value
```

### 6.3 ★ 决定性发现：`HeroBtnTab` 是一个**没有任何定义**的全局

全 APK 的 Lua 字节码搜索：

| 项 | 结果 |
|---|---|
| 引用处 | **只有 1 处**：`game/role/role_ctrl.luac proto[39]` |
| 定义处（`GSET` / `TSETS`） | **0 处** |

**⇒ `openHeroPanel` 必然失败**：它要读 `HeroBtnTab`，而这个全局在整个 1.4.9 客户端里
**从未被定义**。

**⇒ 这是客户端侧的问题，不是服务端能修的**：
服务端无法让一个客户端自己的 nil 全局变成有值（`HeroBtnTab` 不是任何协议字段，
`protocol/manual.md` 里也没有它）。

### 6.4 另外两条线索

- `openMainPanel` **调用成功但面板不出现** ⇒ 它多半不是"角色面板"的入口，
  或它内部有别的静默前置条件（未确认）。
- `openRoleHeroPanel` 在 `role_show_panel.luac` 里索引 nil ⇒ 另一条独立的前置缺失（未确认）。
- 打开过程中客户端请求了 `10301/10302/10331/13340/14901`（角色协议都正常应答），
  并出现 **`10999`**：`CS_10999{msg:string}`、**无 SC 定义** ⇒ 客户端→服务端的单向
  日志/GM 消息，**无需应答**（body 是一串 `-`）。

### 6.5 主角色面板打开失败，但**主界面本身完好**

视觉判读（`shots/stage4d_panel2.png`）：仍是主城界面，**无空白、无乱码、无报错弹窗**；
可见 `史莱克城 / 商城 / 首充 / VIP勋章1 / 充值 / 任务 / 队伍 / 好友 / 消息 / 语音 /
魂囊 / 魂技 / 更多`，角色名 `DSH`、`唐雅`、`周漪` 正常。

---

## 7. Phase 4D 结论（诚实版）

| 目标 | 结果 |
|---|---|
| 找到角色面板类 | ✅ `RoleMainView`（`game/role/new_ui/ver_one/role_main_view.luac`） |
| 找到打开入口 | ✅ `RoleCtrl.openMainPanel / openHeroPanel / openRoleHeroPanel …` |
| **成功打开面板** | ❌ **未打开** |
| 失败原因 | ✅ **已定位**：`openHeroPanel` 依赖全局 `HeroBtnTab`，而它在 1.4.9 里**从未定义** |
| 是否服务端可修 | ❌ **不可修** —— `HeroBtnTab` 不在任何协议里，服务端无法提供 |
| 是否要改客户端 | ❌ **不改**（本阶段明令"不要重新制作 UI"，且改客户端超出范围） |

**⇒ Phase 4D 的结论是"**角色面板在原版 1.4.9 客户端里打不开，原因是客户端自身的
`HeroBtnTab` 全局缺失**"，而不是"我们的服务端缺数据"。**

**下一步（若仍要继续）只能二选一（都需要你决定）**：

- **A**：接受"角色面板打不开"这一现状，**跳过 4D**，直接做 4E（角色数据持久化）与 4F（移动+坐标保存）
  —— 这两项不依赖角色面板；
- **B**：明确授权"为 `HeroBtnTab` 补一个最小定义"（**这属于改客户端**，
  与阶段 4 的"不要重做 UI"边界冲突，需你确认）。

---

**按阶段纪律：本 Phase 未完成，不自动进入 4E。**

**[WAITING FOR PHASE 4D-续 / NEXT INSTRUCTION]**
