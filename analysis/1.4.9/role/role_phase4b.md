# Phase 4B —— 角色最小协议补齐（最终记录）

> **本阶段改动只碰服务器**：未改 APK、未写 UI、未重做角色系统、未做任务系统。
> 目标：补上审计发现的"客户端已请求但无人应答"的角色相关命令。

---

## 一、本阶段实际修改（唯一文件：`server/mock_server.py`）

在 `_reply()` 中新增 **6 个分支**，全部按 `protocol/manual.md` 的字段定义逐字段编写：

| CMD | 请求 | 响应字段 | 依据 |
|---|---|---|---|
| **10302** | 空 | `lev:u16, exp:u32, gold:u32, gold_acc:u32` | `role_ctrl` `RegisterProtocal(10302,'rgp_hander10302')` |
| **10333** | 空 | `code:u8, msg:string` | 审计发现"客户端已请求、无应答" |
| **10621** | 空 | `world_lev:u16, skill_list:table(bid:u32, exp:u32)` | 同上 |
| **13340** | 空 | `name:string, lev:u8, career:u8, sex:u8, sign:string, guild_name:string, title:string, spouse_name:string, per_name:string, zone:string, city:string, gift_num:u16` | 同上（**角色个人信息/名片**） |
| **10331** | `skill_bid:u32` | `code:u8, msg:string` | 同上（**技能升级**） |
| **14901** | 空 | `cur_bid:u16, xs_title_list:table(bid:u16, left_time:u32)` | 同上 |

**配置补充**（`server/config.json`）：

```json
"role": { "lev":1, "exp":0, "gold":1000, "gold_acc":5000, "spouse_name":"", ... },
"world_lev": 1,
"skills": [ { "bid":1001, "exp":0 } ],
"sign": "本地私服测试", "guild_name": "", "title": "", "per_name": "",
"zone": "1", "city": "史莱克城", "gift_num": 0
```

**编码自查（按 `pack_frame` 实算）**：

```
10302: 00 01 | 00 00 00 00 | 00 00 03 e8 | 00 00 13 88     lev=1 exp=0 gold=1000 gold_acc=5000
10333: 00 | 00 00                                           code=0 msg=''
10621: 00 01 | 00 01 | 00 00 03 e9 | 00 00 00 00            world_lev=1 count=1 bid=1001 exp=0
13340: 00 03 "DSH" | 01 | 01 | 00 | 00 12 "本地私服测试" | 00 00 | 00 00 | 00 00 | 00 00
       | 00 01 "1" | 00 0c "史莱克城" | 00 00                    （55 字节，中文按 UTF-8）
10331: 00 | 00 00                                           code=0 msg=''
14901: 00 00 | 00 00                                        cur_bid=0 count=0
```

---

## 二、验证结果（**6 条中 5 条已验证**）

### ★★★ 本轮方法突破：把"等自然触发"改成"主动触发"

**问题**：客户端的请求集合每轮都不同，靠实机跑很难稳定走到目标协议。

**解法**：反汇编找出客户端**自己的发送函数**，再从探针里主动调用它们 —— 确定性触发。

| CMD | 客户端发送函数（反汇编得出） | 所属 |
|---|---|---|
| 10302 | `RoleCtrl:sender10302` | `game/role/role_ctrl.luac` |
| 13340 | `CircleCtrl:send13340` | `game/circle/circle_ctrl.luac` |
| 14901 | `TitleCtrl:send14901` | `game/title/title_ctrl.luac` |

探针实现在 `server/dsh_fake_login.lua`（进场景后 `S.t >= 120` 各调一次）：

```lua
RoleCtrl:getInstance():sender10302()
CircleCtrl:getInstance():send13340()
TitleCtrl:getInstance():send14901()
```

### 实测：三条全部确定性触发并得到应答

```
t=send4b&v=10302_ok_true_err_nil
t=send4b&v=13340_ok_true_err_nil
t=send4b&v=14901_ok_true_err_nil

[22:27:34]  << 10302 SC_10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)   ✅
[22:27:34]  << 13340 SC_13340 profile name=DSH lev=1 (61 bytes)                ✅
[22:27:34]  << 14901 SC_14901 cur_bid=0 xs_title_list=0 (10 bytes)             ✅
```

### Lua 错误检查：**0 条**

```
Call Function[stack top]  : 0
.luac:<行号> 形式的栈回溯 : 0
```

### 最终状态表

| CMD | 已实现 | 已验证 | 依据 |
|---|---|---|---|
| **10333** | ✅ | ✅ | `>> cmd=10333` → `<< 10333 code=0 (9 bytes)` |
| **10621** | ✅ | ✅ | `>> cmd=10621` → `<< 10621 world_lev=1 skill_list=1 (18 bytes)` |
| **10302** | ✅ | ✅ | 主动触发 → `<< 10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)` |
| **13340** | ✅ | ✅ | 主动触发 → `<< 13340 profile name=DSH lev=1 (61 bytes)` |
| **14901** | ✅ | ✅ | 主动触发 → `<< 14901 cur_bid=0 xs_title_list=0 (10 bytes)` |
| **10331** | ✅ | ⚠️ **未验证** | 全仓无 sender（技能升级由 UI 操作触发），需手动点技能面板才能验 |

**⇒ 6 条中 5 条已验证，1 条（`10331`）已实现待验证。**

---

## 二之二、仍存在的方法论记录（保留）

**客户端的请求集合每轮不同**：4B 第 1 轮没触发、第 2 轮触发了 10333/10621、
第 3 轮又换一组。⇒ **"未回复"清单不能用单轮结果判定，要看多轮并集**；
且**能用"主动调用客户端 sender"时就不该靠自然触发**（本轮已证明有效）。

---

## 二之三、★ UI 显示经**视觉确认**（本轮新增，结论重要）

用视觉模型判读当前实机截图（`shots/stage3_4b_roleinfo.png`）：

| 项 | 结果 |
|---|---|
| **角色姓名** | ✅ **正确显示**：`DSH`（我们的角色，绿色字）、另有 `唐舞桐`、`霍雨浩` |
| 等级 | ❌ 未显示（无 `Lv`/`等级` 字样） |
| 经验 | ❌ 左下角只有「经验」标签，**被灰色面板遮挡**，无数值 |
| HP / MP | ❌ 无血条蓝条 |
| 战力 | ❌ 无 |
| 职业 | ❌ 无文本标注 |
| 金币/钻石 | ⚠️ 显示了，但金币为 `3135,1395`（**格式可疑**，与我们下发的 `gold=1000`/`gold_acc=5000` 对不上）；钻石 `0` |
| 任务栏 | ⚠️ 仍有 `nil`（**已知的任务系统问题**，不在 Phase 4 范围） |

**⇒ 结论：姓名已通，但等级/经验/HP/MP/战力/职业在主界面上都没显示。**

**说明（不含猜测）**：这些数值很可能只在**打开角色面板**后才显示
（对应下发的 `10301`/`10302`/`10303`），而"打开角色面板"属于 **Phase 4D** 的内容。
**本轮只做观察，未点开面板、未改 UI。**

**⇒ 因此 4B 的定位应是："协议已通 5/6、姓名已显示；角色数值的界面呈现留待 4D 验证"。**

---

## 二之四、`10331`（技能升级）的触发入口已找到

全仓搜 `GetPrototype(10331)`：

```
game/skill/skill_ctrl.luac  proto[4]  @2    → registerProtocals（注册处）
game/skill/skill_ctrl.luac  proto[14] @6    → **learn**（学习/升级技能）
```

且 `skill_ctrl` 的类名是全局 **`SkillCtrl`**。

⇒ **`SkillCtrl:learn(...)` 就是发送 10331 的入口**（需要技能 bid 参数）。
本轮**未调用它**（要先确认 `learn` 的参数形态，避免传错），
故 **`10331` 仍是"已实现未验证"**。

---

## 二之五、★ `10331` 也已验证 —— **Phase 4B 达到 6/6**

`SkillCtrl:learn` 的参数形态（反汇编 `skill_ctrl proto[14]`，params=2）：

```lua
function SkillCtrl:learn(skill_bid)
  local proto = ProtocalRulesMgr:getInstance():GetPrototype(10331)
  proto.skill_bid = skill_bid          -- 直接把 bid 塞进 CS
  self:SendProtocal(proto)
end
```

⇒ 参数就是**技能 bid**，于是探针里直接 `SkillCtrl:getInstance():learn(1001)`。

**实测（4 条 sender 一次全部触发）：**

```
t=send4b&v=10302_ok_true_err_nil
t=send4b&v=13340_ok_true_err_nil
t=send4b&v=10331_ok_true_err_nil      ← ★ 本轮补上
t=send4b&v=14901_ok_true_err_nil

[22:36:40]  << 10302 SC_10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)
[22:36:40]  << 13340 SC_13340 profile name=DSH lev=1 (61 bytes)
[22:36:40]  << 14901 SC_14901 cur_bid=0 xs_title_list=0 (10 bytes)
[22:36:40]  << 10331 SC_10331 skill_bid=1001 code=0 (9 bytes)     ← ★
```

**Lua 错误：`Call Function[stack top]` = 0，`.luac:行号` 栈回溯 = 0。**

### 最终成绩单：**6/6 全部已验证**

| CMD | 已实现 | 已验证 | 验证方式 |
|---|---|---|---|
| 10333 | ✅ | ✅ | 客户端自然请求 |
| 10621 | ✅ | ✅ | 客户端自然请求 |
| 10302 | ✅ | ✅ | 主动触发 `RoleCtrl:sender10302()` |
| 13340 | ✅ | ✅ | 主动触发 `CircleCtrl:send13340()` |
| 14901 | ✅ | ✅ | 主动触发 `TitleCtrl:send14901()` |
| **10331** | ✅ | ✅ | 主动触发 `SkillCtrl:learn(1001)` |

---

## 三、多轮并集：仍然无人应答的命令（截至本阶段）

```
10001  10300  10800  10923  11300  11301  13200  13300
15801  16605  18803  19400  19406  30715
```

- 其中 `10001`（FirstPack）与 `10300`（客户端初始化完毕）按设计就没有 SC 应答；
- `15801` 是**故意不回**（早前回猜包导致空白弹窗，已改为不应答）；
- 其余（`10800/10923/11300/11301/13200/13300/16605/18803/19400/19406/30715`）
  属于其它子系统，**不在 Phase 4 范围**。

**结论：角色基础系统范围内，已无"客户端请求但无人应答"的命令。**

---

## 四、Phase 4B 结论

| 项 | 结果 |
|---|---|
| 新增协议 | **6 条**（`10302`/`10333`/`10621`/`13340`/`10331`/`14901`） |
| **已验证** | **6 条（6/6）** |
| 编码核对 | 6 条全部按定义实算通过（含中文 UTF-8 长度） |
| Lua 错误 | **0** |
| **UI 视觉确认** | ✅ 姓名正确显示（`DSH`）；❌ 等级/经验/HP/MP/战力/职业未显示 ⇒ **待 4D 开面板验证** |
| 改 APK / 改 UI / 重做角色系统 / 任务系统 | **均未做**（探针是既有的调试注入） |
| 角色数据持久化（4E） | 未开始（目前仅 x/y 落盘） |

**本阶段沉淀的两条方法论**：

1. **客户端的请求集合每轮不同** ⇒ 判定协议缺失必须看**多轮并集**，单轮结果不可用。
2. **能主动调用客户端自己的 sender 时就不该靠自然触发** —— 本轮据此一次验证了 4 条
   （`sender10302` / `send13340` / `send14901` / `learn`），把"能验的"从 2/6 提到 6/6。

**按阶段纪律：本 Phase 到此停止，不自动进入 4C。**

---

**[WAITING FOR PHASE 4C]**

