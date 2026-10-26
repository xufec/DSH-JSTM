# 「提升」按钮 = 日常/活力面板（实机点击取证）

> 用户报障：「日常打开后为空白；**提升点击后空白**」。
> 本轮用 **adb 截屏 + 视觉定位 + 实机点击** 直接定死了「提升」是哪个面板。
> 证据等级：**CONFIRMED**（实机点击 → 服务端收到的命令）

---

## 一、★ 「提升」= 左侧栏图标，点开 = **日常/活力面板**

**实机操作**（`adb -s 127.0.0.1:16384 shell input tap 106 325`，坐标由视觉定位
`analysis/shots/dsh2.png` 得出，截图尺寸 2560×1440）：

点击「提升」后，服务端**立刻收到**：

```
[18:23:00] >> cmd=13781 ? body(4)=01 6c 00 00      ← 活力信息
[18:23:00] << 13781 SC_13781 total_val=10 huoli_list=12 lingqu=0 (84 bytes)
[18:23:00] >> cmd=13786 ? body(4)=01 6c 00 00      ← 日常信息
[18:23:00] << 13786 SC_13786 week=0 richang=24 status=0 (107 bytes)
```

截图（`analysis/shots/dsh3.png`）确认打开的正是**日常面板**，标题为
**「日常 / 日常活动 / 限时活动」**，并有「生产技能 / 活力 / 每日凌晨5点刷新 / 双倍点数 0 领取」。

⇒ **「提升」与「日常」是同一个面板**（同属 `daily_ctrl`）——**先前无法定位的问题到此解决**。

**主城左侧栏**（截屏可读）：`日常 / 提升 / 排行 / 铁石VIP`
**底部栏**：`好友 / 市场 / 神兽 / 宗门 / 魂技 / 进阶 / 伙伴 / 锻造 / 更多`
**顶部**：`福利 / 商城 / 百炼 / 变强 / 挂机 / 每日累充玩家回归`

---

## 二、★ 空白面板的**精确症状**：`拥有活力: ????/????`

### ⚠ 更正（PHASE 2.30）：`????/????` **不是"读不到数值"，是客户端自己的占位串**

反汇编 `game/daily/daily_panel.luac`（proto 里创建该标签的那段）：

```
1896:  KSTR  '????/????'        ← 字面量常量
...
1912:  TSETS ['txt_own_huoli']  ← 创建标签时就赋这个占位串
```

**⇒ `????/????` 是客户端**硬编码的初始占位文本**。**
**⇒ 真正的问题是：`txt_own_huoli` 从未被更新为真值** —— 即**更新路径没跑到**。

**更新路径**（同一文件）：
- L166：`strings('houli_data_change','clearEvent','update','isDailyCalled','isHuoliCalled','isCompleted')`
- L188/L402-405：把 `HOULI_DATA_CHANGE` 事件绑到 `houli_data_change`
- ⇒ 面板靠**事件回调**刷新活力文本；该事件由 `daily_data` 在处理 `SC_13781` 的 `huoli_list` 时触发

**⇒ 排查方向**：`daily_data.updateHuoli(huoli_list)` 是否**真的触发了 `HOULI_DATA_CHANGE`**。

### 已核实的相邻事实（本轮）

| 项 | 结论 |
|---|---|
| `on13781` 读的字段名 | **`data.total_val`、`data.lingqu_list`、`data.huoli_list`** ✓ 与 mock 一致（`daily_ctrl.luac` L226-262）|
| `huoli_list` 项 | 客户端按 **`id`** 关联自己的 `Config.Huoli`，填 `cur_num`/`cur_huoli`/`total_huoli` |
| id 是否匹配 | **匹配** ✓ mock 发的 12 个 id（1,5,7,3,13,11,19,17,12,4,14,255）**全部**在客户端 `Config.Huoli` 的 17 个键内 |
| `cur_huoli`/`total_huoli` 来源 | 客户端 `getCfgHuoliListById(huoli_id)`（**客户端配置**），非服务端字段 |

（原"六个问号 = 客户端读不到数值"的判断作废，见上。）

截屏（`dsh3.png`）显示面板内：

| 元素 | 显示 |
|---|---|
| 标题 | 日常 / 日常活动 / 限时活动 ✓ |
| 活力条 | **「拥有活力: ????/???? !」** ← ★ **四个问号** |
| 其他 | 生产技能 / 活力 / 每日凌晨5点刷新 / 18:23:16 双倍点数 0 领取 |
| **列表行** | **完全空白**（无任务名、无数值、无进度条）|

**⇒ `????` 说明客户端拿到的**数值是 `nil`**（不是 0 —— 0 会显示 "0"）⇒ **它没读到该字段**。

---

## 三、已排除的原因（逐项实证）

| 假设 | 检验 | 结论 |
|---|---|---|
| `13781` 结构错 | 1.4.11 权威 = `{total_val:H, huoli_list:T{id@H,num@H,val@H}, lingqu_list:T{huoli@H}}`；mock 回包 **84B = 4+2+78**，与布局**精确吻合** | ❌ 结构没错 |
| `13786` 结构错 | 1.4.11 权威 = `{week:C, richang_list:T{id@H,num@H}, status_list:T{id@H,num@H}}`；mock 发 `week=0 / 24 条 / 0` | ❌ 结构没错 |
| 没数据 | 实机回包 **12 条 huoli + 24 条 richang** | ❌ 数据有 |
| 客户端缺 `config_richang` | 1.4.11 APK 内 `config_richang.luac` **29,279 字节、含 `RiChang` 表** | ❌ 配置在 |
| `field.json` 字段名/类型不符 | `_sweep_fieldmismatch.py` / `_sweep_typemismatch.py` 均**未报 13781/13786** | ❌ 无差异 |
| **`10924` 空表**（R49）| 只影响**「限时活动」**部分（`activity_list`）；**「日常活动」行来自客户端 `Config.RiChang`** | ⚠ 部分相关，非主因 |

**⇒ 主因仍未定**，但症状已精确到"**客户端读不到活力数值**"。

---

## 四、★ 工具可靠性更正（重要，避免后人被误导）

`tools/_fmt_autoconstruct.py` 的 **CS 侧不可靠**：它用"`'cs'` 标记 → 最近的一个 `TableConst`"
启发式匹配，**会把相邻命令的 AutoConstruct 块匹配进来**。
例：它对 `CS_13781` 给出的是 **`SC_13786` 的形状**（`{week, richang_list, status_list}`），
而实机 `13781` 的 CS 只有 4 字节。

- **SC 侧可靠**：`SC_13781` 的布局与实机 84B 回包**精确吻合**，`SC_11215`/`SC_10341` 等亦已逐字节验证 ✓
- **CS 侧仅供参考**，判定 CS 应以**实机抓包**为准（见 `real_cs_formats_1_4_11.md`）

---

## 五、下一轮的候选排查方向（按可能性）

1. **`total_val` 的语义**：客户端显示 `拥有活力: X/Y` —— X 可能是"已完成任务的活力合计"、
   Y 可能是**上限**（`config_richang.HuoliMaxVal`，客户端配置）。若它按 `huoli_list` 求 X，
   而 mock 的 `num`/`val` 全为 0（玩家没做过任务），X 应为 **0** 而非 `????`
   ⇒ **仍有字段读不到**，需反汇编 `daily_data.luac` 里读 `huoli_list` 的那段，核字段名/顺序。
2. **反汇编 `daily_data.luac` 的 `updateHuoli`/`total_val` 消费点**（同 `11215` 那套方法：
   找 `TGETS ['total_val']` 一类的访问，核它期望的字段名）。
3. **`13781` 的 CS** 究竟该是什么（实机发 4 字节；若客户端期望带参数而服务端忽略，可能影响其状态）。
4. **`buffs` 为空**（头像旁状态）——同属"服务端没给数据"一类，但**无证据表明该预置**。

---

## 六、★★ 根因定位（PHASE 2.31）：`10924` 的 **id 空间**用错了

### 6.1 客户端证据（反汇编 `daily_data.luac` proto#17，处理 `SC_13786`）

```lua
result = Array:New() ; self.daily_list = Array:New()
for _, item in <遍历 self.activity_list> do          -- ★ 行来自 activity_list（= 10924 的产物）
    item.num = 0
    for _, d in pairs(richang_list) do
        if d.id == item.id then item.num = d.num end -- ★ 用 id 匹配 13786.richang_list
    end
    for _, d in pairs(status_list) do
        if d.id == item.id then item.status = d.num end
    end
    ... result:PushBack(item)
end
```

**⇒ 两条结论**：
1. **日常活动的行来自 `activity_list`（`10924` 的产物）**，不是客户端配置；
   ⇒ **`10924` 回空表 ⇒ `daily_list` 为空 ⇒ 面板空白** ✓
2. **`item.id` 必须与 `13786.richang_list[].id` 同一 id 空间** —— 即 **`config_richang.RiChang` 的 id（208/205/207/215/210…）**。

### 6.2 原实现的错处

原实现（含 R49）的 `act_list` 取 **`config_function` 的 id**（3/5/6/…/121/1000/2000…），
与 `richang_list` 的 `config_richang` id **不相交** ⇒ **一行都匹配不上** ⇒ 面板恒空。

（R49 的 `notice_act_ids=[101,107,108,111,112,113,115,116,118]` 是 **richang id**，
拿去过滤 `config_function` 的 id ⇒ **只有个别重合 id 才碰巧生效**。）

### 6.3 实验方案（已实现为开关，默认关闭）

```powershell
# 1) 临时把 config.json 的 send_personal_act_list 置 true（否则走 R49 的空表分支）
# 2) 以环境变量启用 richang id 空间
$env:DSH_10924_RICHANG='1'; python server/mock_server.py --http 8080 --game 9000
```

**已实测**：开关打开后 `10924 act_list = 34 条`，
id = `[103,208,205,102,207,215,105,210,104,203,227,211,216,206,109,225,110,219,209,222,…]`
—— **与 `13786.richang_list`（208/205/207/215/210…）同一空间** ✓

**⚠ 验证状态：❌ 已实测 —— 该方案 *未能* 修好面板（PHASE 2.32）**

视觉工具恢复后，我对实验态下的截屏（`analysis/shots/dsh4.png`）做了确认：

| 观测 | 结果 |
|---|---|
| 面板列表 | **仍然空白**（右侧大片米色区域无任务行）|
| `拥有活力:` | **仍然是 `????/????`**（未更新）|
| 弹窗 | **没有**（✓ 这半条推断成立：richang 的日常任务 id 不触发预告）|

**⇒ id 空间假设被推翻。** 复核支持这一否定结论：
- 实验态 `10924.act_list` 的 id = `[103,208,205,102,207,215,105,210,…]`，
  与 `13786.richang_list` 的 id（208/205/207/215/210…）**确实同一空间、交集非空**；
- 客户端 `config_richang`（63 个名字：学院任务/监察任务/斗魂场…）与服务端
  `config_richang.RiChang`（43 键，id 落在 101-121 / 203-216）**同类同范围**；
- `13781`/`13786` **只被 `daily_ctrl` 注册**（无模块覆盖）；
- `on13781` = ChildRef(#10) = proto#10，读 `data.huoli_list` → `updateHuoli`，**无提前 return**。

**⇒ 结论：线格式、字段名、id 空间、注册唯一性全部无误，但列表仍不渲染、活力标签仍不更新。**
**⇒ 问题在更后面的"客户端渲染/时序"环节**（`isDailyCalled`/`isHuoliCalled`/`isCompleted` 三个标志、
或某条前置命令未发），本轮未及定位。

**⚠ 实验态已还原**：`config.json.send_personal_act_list` 已改回 `false`、服务端不带 env 重启、
`10924 act_list=0`。备份：`server/backup/config_10924exp_*.json`、`server/backup/mock_server_10924richang_*.py`。

### 6.4 若验证成功的后续处理

- `act_list` 的 id 空间改为 richang ⇒ **日常行能填上**；
- 同时 R49 的弹窗问题需重新评估：richang id 里**不含**那 9 个预告 id（它们是 `config_richang` 的**活动类** id，
  而 `RiChang` 是**日常任务类** id）⇒ **理论上不会触发弹窗** —— 这需要实测确认，可能是"两全"方案。
