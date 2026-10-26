# 第二十五轮：综合战力 —— 最终诚实结论

> 用户：综合战力仍旧 0。本轮做了**决定性运行时取证**，给出最终判断。

---

## 一、已确证（全部 CONFIRMED，逐步实证）

### 1. 客户端"综合战力"的读取路径
```
advance_new_panel.luac proto[20]（变强/综合战力面板）：
  vo = GameData:getInstance():getRoleVo()
  self.power_value:setString(vo.power[1].val)      ← ★ 读 RoleVo.power[1].val（当前战力）
  self.tui_power:setString(vo.power[2].val)        ← 推荐战力
  vo.power[3] ... getPingfen                        ← 评分
```
**⇒ 综合战力 = `RoleVo.power` 这个数组的第 1 项 val。**

### 2. `RoleVo.power` 是**客户端字段**，由 `setRoleAttribute('power', ...)` 写入
- `advance_new_panel` **没有**直接 `TSETS 'power'` ⇒ `power` 是 RoleVo 属性
- `setRoleAttribute(attrId, val)` 是唯一写入器（RoleVo proto[22]）

### 3. ★★ 运行时取证（探针实测）
**包住 `setRoleAttribute` 后：**
```
探针在跑（openNpc_sceneStart 等 wrapper 正常上报）
但 **setRoleAttribute 从未被调用（power/atk_s/hp_max/dodge 等键一次都没写入）**
getCombatPower **不存在**（未触发 wrapper）
```
**⇒ `RoleVo.power` 从始至终没有被任何消息填充 ⇒ 面板读 `power[1]` = nil ⇒ 显示 0。**

---

## 二、★ 我已做到（服务端侧全部就绪）

| 项 | 状态 |
|---|---|
| 战力引擎（原版权重 64 项 + 公式） | ✅ `server/power.py` |
| `10304`（属性+power 大包） | ✅ 实现，回 160095 |
| `20100`（变强面板 power 分量） | ✅ 实现，编码正确（对照已知表约定），回 power=160095 |
| 编码 | ✅ 与所有能工作的 table 一致（w_u16(len)+逐元素） |

**⇒ 服务端把 power=160095 发给客户端了（`<< 20100 power_total=160095` 实测）。**

---

## 三、★ 卡在哪（诚实）

**客户端虽然收到了 20100 的 power=160095，但它的 `RoleVo.power` 没被写入。**

**原因（结合探针）：**

1. **服务器发的 20100 → 客户端 handle20100 → Fire(Update_Data)** —— 但事件**不带数据**（disasm 显示 Fire 无参）。
2. **面板的 `self.power` = `RoleVo.power`**，需要由**另一条"角色属性同步"消息**通过 `setRoleAttribute('power', ...)` 写入。
3. **探针证实这条消息**从未触发 setRoleAttribute 写 power**。
4. **而 `RoleVo.power` 是数组**（面板读 `power[1].val`），**不是** 10304 的标量 power / 20100 的分量列表 —— **它们不是同一个 `power` 字段**。

**⇒ 存在一个"角色属性同步"消息，带 `power`（数组），能写入 RoleVo.power —— 我**没有找到它**（也不在已实现协议里）。**

---

## 四、最终诚实交付（不编造）

**我不能保证"再改哪个协议就让综合战力非零"** —— 因为：
- 服务端已经发了 power=160095（10304 + 20100）
- 客户端的 RoleVo.power 是**另一个**数组字段，需要**一条我尚未定位的"属性同步"消息**来写

**我已经把：**
- 战力计算 → 真实（原版权重）
- 两个候选协议（10304/20100）→ 实现 + 正确编码
- 运行时证据 → 客户端 RoleVo.power 未被写入

**我能做的下一步（三选一，请你定）：**

| 选项 | 内容 | 性质 |
|---|---|---|
| **A. 深度追"角色属性同步消息"** | 查 `setRoleAttribute('power',...)` 的调用链究竟来自哪条 CMD（可能是 10302/10303 里的某个字段或独立推送） | 服务端正解，还需 1-2 轮 |
| **B. 探针直接注入** | 在探针里把 RoleVo.power 设成服务端算好的值（客户端侧补） | **绕过协议 = 造假显示**（我不推荐） |
| **C. 先接受现状** | 战力引擎/10304/20100 已交付，综合战力显示暂不追 | 等有更多真机数据再查 |

**我诚实推荐 A**（若你坚持综合战力真实显示）；但**我不能保证 A 一定能找到那条消息** —— 若它需要客户端特定交互才触发（如点开某界面），可能需要你在游戏里特定操作配合取证。

**另**：B 是"客户端注入假战力"——违反实事求是，我不主动做，除非你明确接受"探针演示值"。

**你定 A/B/C？**