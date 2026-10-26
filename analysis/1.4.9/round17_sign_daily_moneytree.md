# 第十七轮：签到领取修复 + 日常面板实现 + 摇钱树修复

> 用户报障五项：① 签到不能领取（要求"读取签到奖励列表的物品下发"）② 幸运转盘无法完成抽奖
> ③ 摇钱树次数不变、不发奖 ④ 日常面板有错误 ⑤ 变强面板"我要变强"为空

---

## 一、① 签到不能领取 —— ✅ **已修（根因：我的 14101 少发了两个字段）**

### 取证（客户端字节码 `dailysign_ctrl.luac` proto[10]）

```lua
on14101 (42 条):
  @0-2   if resp.data == nil then return        ← 框架字段
  @3-5   if resp.tips ~= nil then ...
  @13-22 TDUP{days, vip_lev} → data:updateSignData(...)
  @25-30 dispatcher:Fire(DailySignEvent.GET_CALL_BACK, **resp.assets**, **resp.items**)   ← ★★
  @38-40 message(resp.msg)
```

### ★★ 根因

```
SC_14101 权威定义: {tips:u16, msg:string, days:u8,
                    **assets:table(type:u8,count:u32)**,
                    **items:table(item_bid:u32,num:u8,is_bind:u8)**}
我的实现(改前):     w_u16(tips) + w_str(msg) + w_u8(days)      ← ★ **少了 assets 和 items！**
```

**⇒ 客户端 `Fire(GET_CALL_BACK, resp.assets, resp.items)` 拿到的是 **nil** ⇒
奖励回调拿不到东西 ⇒ **界面上就是"领不了"**（虽然 code 是对的）。**

**⇒ 这正是你说的"读取签到奖励列表的物品进行下发"。**

### 修复

```python
out = w_u16(1) + w_str('') + w_u8(days)
out += w_u16(len(assets))                      # assets:table(type, count)
for a in assets: out += w_u8(type_code) + w_u32(count)
out += w_u16(len(items))                       # items:table(item_bid, num, is_bind)
for it in items: out += w_u32(bid) + w_u8(num) + w_u8(is_bind)
```

**验证：`14101` 从 5 字节 → **24 字节**（含奖励表）✓**
**幂等分支也补成完整字段（`tips=0` + 空表）。**

---

## 二、④ 日常面板 —— ✅ **已实现 6 条协议**

### 取证（`game/daily/daily_ctrl.luac`）

```
RegisterProtocal 13781 13786 13787 13788 13789 (+10922~10925)
```

### 实现与验证

| 功能 | CMD | 定义 | 实测 |
|---|---|---|---|
| 日常总览 | `13781` | `(空) → SC{total_val, huoli_list:table(id,num,val), lingqu_list:table(huoli)}` | 6 字节 ✓ |
| 日常列表 | `13786` | `(空) → SC{week, richang_list:table(id,num), status_list:table(id,num)}` | 5 字节 ✓ |
| 领取 | `13787` | `(空) → SC{code, msg, lingqu_list:table(huoli)}` | 5 字节 ✓ |
| （空回） | `13788` | `(空) → SC(空)` | 6 字节 ✓ |
| 按活力领 | `13789` | `{huoli:u16} → SC{code, msg, huoli:u16}` | 5 字节 ✓ |
| 活跃度 | `10925` | `{id:u16} → SC{id, status, int_args:table(val:u32)}` | 9 字节 ✓ |

**⚠ 活力/日常任务表**原版未逐项取证**⇒ config 默认空，需要时按字段填（已标注）。未编造。**

---

## 三、③ 摇钱树次数不变/不发奖 —— ✅ **已修**

**改前：`17801` 只回 `{code,msg}`，**不改次数、不发奖**。**
**改后：**
1. **真正扣次数**（`moneytree_free_count -= 1`），为 0 时回 `code=0` + "今日次数已用完"
2. **真正发奖**（`db_add_assets(rid, {coin})`）
3. **★ 写盘持久化**（否则重启后次数会回涨）
4. **回包后立即补推一次 `17800`** ⇒ 客户端次数**当场刷新**
5. **`live_push` 通知资产变化**

---

## 四、⚠ 未完成两项（如实）

### 4.1 ⑤ 变强面板 —— **`20100`，含未解子表 ⇒ 按纪律不实现**

```
20100 (空) → SC{power:table(code:u8, val:u32),
                promote:table(code:u8, **val:D|Dsc20100val|**)}   ← ★ 未解子表
```
**⇒ 按项目纪律（不猜协议编码）**主动不实现**。
**⇒ 这是你说的"我要变强为空"的直接原因 —— 但补齐它需要先解出 `Dsc20100val` 子表结构。**

### 4.2 ② 幸运转盘 —— **协议未定位**

**排查结果：`20100` 的字段是 `power`/`promote` ⇒ 它是**变强面板**，**不是转盘**。**
**⇒ 转盘的 CMD **尚未定位**。**
**⇒ 已找到相关配置表（`config_holiday_lucky_turntable_data.luac` 781B / `config_holiday_dial_reward_data.luac` 2682B），
但**没找到对应的客户端协议注册点**。**

**⇒ 需要你提供转盘的**入口位置**（哪个界面/按钮进去的）⇒ 我据此定位模块再查协议，最快。**

---

## 五、两处**测试脚本**的自纠（非服务端问题）

| # | 现象 | 真相 |
|---|---|---|
| 9 | `30600 items=5377` | **我读错偏移**（count 在偏移 5，我读了 6）⇒ 服务端正确，实为 **21** |
| 10 | `13788 无应答` | **空字节 `b''` 是 falsy** ⇒ 我的测试把"空回包"当成"无应答" ⇒ 服务端正确（6 字节帧） |

---

## 六、自查

```
mock_server.py OK ｜ 服务端 8080/9000（PID 18464）｜ stderr 0 字节
改动：14101 补 assets/items（5→24 字节）；新增日常面板 6 条；摇钱树扣次数+发奖+落盘+补推
新增 config：huoli_total/huoli_list/huoli_lingqu/richang_week/richang_list/richang_status
```

---

## 七、请实机确认

1. **签到** —— 现在能领了吗？（领到 500 银魂币）
2. **日常面板** —— 还报错吗？
3. **摇钱树** —— 次数会减、奖励会发了吗？

**另外请告诉我「幸运转盘」的入口在哪**（哪个按钮/界面）—— 那是定位它协议的最快路径。
