# R55：挂机前置取证（续）—— **按钮 4019 就是「学院任务(N/10 环)」，闭环成立**

> 承接 R54 §四 第 1 项：「反查 `4019` 属于哪个 NPC 的对话框 / 是不是客户端配置」。
> **结论：它就是我们一直在墙上看到的那颗按钮，本服不需要补任何消息。**
> **时间**：2026-09-29 11:00 – 11:15。**本轮未改服务端代码。**

---

## 一、结论（TL;DR）

```lua
-- npc_dialogs.luac proto#11（对话框按钮构建器）
knum(9): [0, 9019, 4019, 1, 4, 22, 66, 46, 2]
--               K(1) K(2)

for _, btn in ipairs(self.npc_cfg.button) do            -- BC 174-178
    if btn.id == K(1)=9019 then <另一分支> end
    if btn.id == K(2)=4019 then                          -- BC 183-185  ★★
        btn.name = string.format(getString('(今日已完成%s/10环)'),
                                 math.min(10, MissionCtrl:getInstance():getHuanRound()))
        self:registerHuanEvent(nil)                       -- BC 206
        MissionCtrl:getInstance():requestHuan()           -- BC 214 ★ 这里会发 CS_15405
        btn_key = 'key_huan'                              -- BC 216
        self:createBtn(2, btn.id, btn, nil)               -- BC 218-224 ★ 用 btn.id 建按钮
    end
end
```

**⇒ 面板上那颗「学院任务(今日已完成 N/10 环)」的按钮，`id` 就是 `4019`。**
点它 → `NpcCtrl:funBtnHandler` → `btn.id==4019` → **`NpcCtrl:acceptNewHuanMis()`** → **发出 `CS_15400`**。

```
npc_cfg.button 里 id==4019 的按钮
  → 标签「学院任务(今日已完成 N/10环)」，N = min(10, MissionCtrl:getHuanRound())
  → 点击 → funBtnHandler → acceptNewHuanMis() → CS_15400
  → 服务端 SC_15400{code=1} → CS_15402{mission_bid} → 15403 / 15404（R48/R53 已做通）
```

**⇒ 本服无需新增任何下发**：按钮来自客户端配置 `config_npc` 的 `button` 字段。

---

## 二、证据链（四段，全部可复核）

| # | 证据 | 出处 |
|---|---|---|
| 1 | `CS_15400` 的唯一发送点 = `NpcCtrl:acceptNewHuanMis()`（proto#42，`KSHORT D=15400`） | R54，`analysis/_npc_ctrl.txt` |
| 2 | 它只在 `funBtnHandler(btn)` 里 `btn.id == K(3)` 时被调用 | 同上 |
| 3 | `funBtnHandler` 的 `knum(90)[3] = **4019**`（相邻为 4017/4018/4020） | 同上 |
| 4 | **构建器 proto#11 的 `knum(9)[2] = 4019`**，该分支给 `btn.name` 赋 `'（今日已完成%s/10环）'` 并 `createBtn` | 本轮，`analysis/_npc_dialogs_p11.txt` |

**交叉印证**：`npc_contants.luac` 给出原版常量表 ——

```lua
NpcContants.BaoTu_Coin = 5000
NpcContants.BtID_Coin  = 4017      -- 宝图（铜币）
NpcContants.BtID_Gold  = 4018      -- 宝图（金币）
```

⇒ 4017 / 4018 已被命名占用；**4019 是同一按钮家族里唯一"无名"的那个**，正好对应构建器里那颗"幻/红尘"按钮。
（这一条只作旁证 —— 真正的定论来自 proto#11 的 `knum` + 分支体。）

---

## 三、顺带解决了另一个疑问：`15405` 是**对话框**发的

```lua
MissionCtrl:getInstance():requestHuan()    -- BC 214
```
`requestHuan()` 就是发 `CS_15405` 的地方 ⇒ **`15405` 在"打开 NPC 对话框"时发出**，
与我们观察到的"点「参与」走过去、对话框弹出来 → `15405`"完全吻合。
它的返回值 `loop_count` 只用来**渲染按钮标签**（`min(10, getHuanRound())`），
**不是"能不能挂机"的开关** —— 这与 R53 实测（给 1 或 10 行为一致）一致。

---

## 四、为什么前几轮一直点不出来（诚实归因）

| 原因 | 说明 |
|---|---|
| **点击坐标不准** | 本轮用"视觉估百分比"去点「日常」，**连续两次都没点中**（日志里 `13781` 计数为 0）。R48 记录的 (1300,245)/(1870,1020) 也是估的 |
| 弹窗遮挡 | 多次截图上「50级礼包」与「请选择要做」**同时在场**，容易点错层 |
| 误把 `loop_count` 当开关 | R48 §7.2 看到的 `15400` 是**偶发**；R53 已实测它不是稳定触发条件 |

⇒ **正确操作**：打开周漪的对话框后，点**对话框里那颗「学院任务(N/10环)」**（= id 4019），
而不是点日常面板里的"参与"。**这是一次"点对按钮"的问题，不是服务端缺失。**

---

## 五、下一步（可执行）

| # | 动作 | 判据 |
|---|---|---|
| 1 | 在 MuMu 上**精确校准坐标**：截全屏 → 裁对话框区域 → 让视觉模型**只答百分比** → 换算 → 点击 → **以"日志里出现 `15400`"为命中判据**（不要看截图） | 出现 `>> cmd=15400` |
| 2 | 命中后按 `15400 → 15402{mission_bid} → 15403 → /DSH_ADMIN/guaji_end` 走完，**顺便把 `_chengjiu_map.json` 的监察线（`zhuoyao`）映射也抓出来** | `15402` 的 bid 落进 `_chengjiu_map.json` |
| 3 | 若最终仍点不出，再考虑"50级礼包弹窗遮挡"⇒ 用 `/DSH_ADMIN` 让该礼包处于已领状态 | — |

> ★ 方法论提醒（本轮亲历）：**用视觉估算坐标去点 UI，成功率很低**（本轮 0/2）。
> 判定必须靠"服务端是否收到预期 cmd"，且坐标要用**裁剪+百分比换算**（见 `PLAN` §5.3 的标定 SOP）。

---

## 六、本轮影响

**未改任何服务端代码**（纯取证）。六道门禁与 R53/R54 基线一致：

```
lint 0 遮蔽（169 / 64 / 22） ｜ CS 规格 2463/0 ｜ SC 静态 85+1空/0
SC 在线 86/86 ｜ 专用查询 63/63 ｜ 门禁 E PASS（132 条 / 顶层空表告警 0）
server_stderr.log 0 字节 ｜ 9000 端口恰好 1 个监听
```

真机：`guaji_state.loop_count` 保持 **0**；玩家数据未被写入。

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `analysis/_npc_dialogs.txt` | `npc_dialogs.luac` 全量反汇编 |
| `analysis/_npc_dialogs_p11.txt` | **proto#11 单列反汇编**（按钮构建器 = 本轮定论的真源） |
| `analysis/_npc_ctrl.txt` | `npc_ctrl.luac` 全量反汇编（`acceptNewHuanMis` / `funBtnHandler`） |
| `_tmp_cfg/npc_contants.luac` | 原版常量表（4017/4018 旁证） |
| `analysis/1.4.9/round55_huan_button_4019.md` | 本报告 |
