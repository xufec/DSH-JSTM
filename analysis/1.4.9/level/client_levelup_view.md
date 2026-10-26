# 1.4.9 客户端「经验条 / 升级表现」实现分析

> **目标 APK**：`anzbao/jstm.apk` / `com.shiyue.dldl.ewan.qihoo` / versionName **1.4.9**
> 本文全部结论**只以 1.4.9 字节码为依据**；1.4.11 未参与任何判定。

---

## 一、★ 最重要的结论（决定服务端该怎么做）

| # | 结论 | 证据 |
|---|---|---|
| 1 | **经验表在客户端**：`Config.RoleAttr[role.lev + 1].exp_max` 就是"本级升下一级所需经验"（经验条分母） | `main_ui.luac` proto#16 bc#0–5 |
| 2 | **等级由服务端权威**：客户端**不**从经验反推等级，直接用 `RoleVo.lev` | `main_ui.luac` proto#16 bc#2–3 |
| 3 | **升级表现由 `RoleVo.lev` 变化触发**：客户端发现 `lev` 字段变了就置 `isUplevel = true` 并播升级动画，**不需要任何"升级协议"** | `main_ui.luac` proto#12 bc#5–11 |
| 4 | `Config.RoleAttr` 含 **`exp_max`** 字段 | `config_role_attr.luac` proto#0 字符串池 |

⇒ **服务端只要把 `lev` / `exp` 改对并下发（10301/10302/10303），客户端就会自己刷新等级、播经验条动画、播升级表现。**
不需要新增协议，也不需要客户端改动 —— 完全符合项目总原则。

---

## 二、经验条的实现（`game/main/main_ui.luac`）

### 2.1 方法表

| 方法 | proto | 作用 |
|---|---|---|
| `changeExp` | proto#16 (bc=70) | **刷新经验条**（`MainUI_updateExp`） |
| `updateExp` | proto#18 (bc=84) | **逐帧动画**（经验条平滑增长 / 升级两段式） |
| （事件回调） | proto#12 (bc=20) | 监听 RoleVo 字段变化 → 置 `isUplevel` |
| `registerEvent` 辅助 | proto#14 | 绑定 `RoleRpgEvents.UPDATE_ROLE_ATTRIBUTE`、`SceneEvent.scene_success_event`、`RoleRpgEvents.role_fight_event` |

### 2.2 `changeExp`（proto#16）逐句还原

```lua
function MainUI:changeExp()
    local cfg = Config.RoleAttr[self.role.lev + 1]        -- ★ bc#0-5：查表
    if cfg == nil then return end                          --   查不到就直接返回

    if self.isFirstLogin then                              -- bc#8-10
        self.expPos = self.role.exp / cfg.exp_max * self.expFull
        self.exp_bar:setContentSize(cc.size(self.expPos, 11))
        self.isFirstLogin = false
        return
    end

    if self.isOnlevel then                                 -- bc#30-32（升级动画第二段中）
        self.expPos = self.role.exp / cfg.exp_max * self.expFull
    else
        self.prePos  = self.expPos                         -- bc#41-42
        self.expPos  = self.role.exp / cfg.exp_max * self.expFull
        self.curPos  = self.prePos
        if self.isUplevel then                             -- bc#52-54
            self.isOnlevel = true                          -- bc#55-56
            RenderMgr:getInstance():frameAddCall(<closure#15>, 'MainUI_updateExp')
            return
        end
    end
    ...
end
```

**要点**：
- 分母 `cfg.exp_max` 来自 **`Config.RoleAttr[lev + 1]`**（不是 `[lev]`）
- 进度 = `role.exp / cfg.exp_max * self.expFull`
- `exp_bar` 用 `setContentSize` 拉伸，高度固定 `11`

### 2.3 `updateExp`（proto#18）—— 逐帧动画（**两段式升级动画**）

```lua
function MainUI:updateExp()
    if not self.isUplevel then return end                  -- bc#0-2
    self.curPos = self.curPos + self.step                  -- bc#3-6

    if self.isOnlevel then                                 -- 第一段：先填满
        self.step = self:getStep(self.curPos, self.expFull)
        if self.curPos > self.expFull then
            self.curPos    = 0                             -- 归零，开始第二段
            self.isOnlevel = false
        end
    else                                                   -- 第二段：填到新进度
        self.step = self:getStep(self.curPos, self.expPos)
        if self.curPos > self.expPos then
            self.curPos    = self.expPos
            self.isOnlevel = false
            self.isUplevel = false                         -- 动画结束
            ...  # 触发后续刷新
        end
    end
end
```

⇒ **升级时经验条会「先填满 → 归零 → 再填到新值」**，这是原版表现，服务端无需干预。

### 2.4 升级是怎么被发现的（proto#12）

`proto#12` 的常量池是 `['exp', 'changeExp', 'isUplevel', 'lev', 'power']`，反汇编为：

```lua
function MainUI:???(key)                 -- 监听 RoleVo 字段变化
    if key == 'exp' then
        ...
    end
    if key ~= 'lev' then                 -- bc#3-4
        self.isUplevel = true            -- bc#5-7   ★ 只有 lev 变化才置 true
        self:changeExp()
    else
        self:changeExp()
    end
end
```

> 说明：分支归属（哪一支对应 `lev`）依据 bc#3 `ISNES A=0 D=1` 比较的是常量池第 2 项。
> **`isUplevel` 只在 `lev` 变化这一支被置 true** 这一点是明确的
> （另一支只调 `changeExp()`）。

**⇒ 客户端完全靠「`RoleVo.lev` 字段变化」自己发现升级。服务端不需要发升级事件。**

---

## 三、事件绑定（`main_ui.luac` proto#14）

`registerEvent` 绑定的事件：

| 事件 | 来源 |
|---|---|
| `RoleRpgEvents.UPDATE_ROLE_ATTRIBUTE` | 角色属性更新 → 触发经验条/等级重新取数 |
| `SceneEvent.scene_success_event` | 进场景成功 |
| `RoleRpgEvents.role_fight_event` | 战斗相关 |

⇒ 服务端推 `10301` / `10302` / `10303` 之后，客户端**已绑定好的这些刷新路径会自己跑**。

---

## 四、对服务端实现的要求（本阶段结论）

| 要求 | 说明 |
|---|---|
| **必须**下发正确的 `lev` | 客户端直接信任它（不从 exp 反推） |
| **必须**下发正确的 `exp` | 客户端用它算经验条进度 |
| **应当**下发更新后的属性（10303） | 升级后属性面板要更新 |
| **不需要**新增升级协议 | 客户端自己检测 `lev` 变化 |
| **不需要**发经验条分母 | 客户端自己查 `Config.RoleAttr` |

### 4.1 升级判定该用哪张表？

因为客户端用 `Config.RoleAttr[lev + 1].exp_max` 作分母，**服务端必须用同一张表**，
否则会出现"服务端认为升级了、客户端经验条却显示异常"的不一致。

⇒ 服务端应**直接复用** `Config.RoleAttr` 的 `exp_max` 作为升级阈值。

> `Config.RoleAttr` 的完整提取见 `exp_table.md`（由并行的配置提取任务产出）。

---

## 五、本阶段**未确定**的部分（不猜）

| 项 | 状态 |
|---|---|
| `Config.RoleAttr` 的完整结构与等级上限 | 见 `exp_table.md`（并行任务） |
| 升级后**属性**如何成长（客户端算还是服务端下发） | **待查**：`10303` 的属性是服务端下发的，但客户端 `role_calculate.luac` 也会算（装备/伙伴加成） |
| 是否存在**升级奖励**（道具/邮件） | **待查**：需在协议与配置里找"升级奖励"来源 |
| `10342`（盈福经验）与 `profit_exp` 的关系 | **待查** |
| `Config.RoleAttr[lev+1]` 为何是 `+1` | **`INFERRED`**：推测 `RoleAttr[N].exp_max` = "升到 N 级所需经验"，故本级用 `[lev+1]` |
