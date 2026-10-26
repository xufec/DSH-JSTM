# R59：`CS_15402` 的发送条件（反汇编）+ 三个触发实验全部否证

> 承接 R58 遗留：`15400` 真机已通，但客户端**不发 `15402`**。
> 本轮做了两件事：**① 用新工具定位 `15402` 的发送点并反汇编出条件；② 按该条件做实验 —— 全部否证。**
> **时间**：2026-09-29 12:50 – 13:10。

---

## 一、新工具：`tools/find_cmd_ref.py` —— **谁引用了某个命令号**

`CS_15402` 不在 `ghost_ctrl`（那里只有注册用的 `15402`），需要"全 APK 找谁引用它"。
于是写了这个通用扫描器：

```
原理：LuaJIT 的 `KSHORT` 把 16 位立即数放在指令字高 16 位
      op = ins & 0xff ; a = (ins>>8)&0xff ; d = (ins>>16)&0xffff
      ⇒ 文件里表现为 4 字节： [op][a][d_lo][d_hi]
★ 第一版工具写错了：直接搜 `[op][00][d_lo][d_hi]`（假设 A=0）⇒ **命中恒 0**。
  实际 `KSHORT A=3 D=15400` ⇒ 字节是 27 03 28 3c。正确做法是**先找 D 值、再回看 −2 字节是不是 op**。
```

用法：`python tools/find_cmd_ref.py 15402 --ctx`

结果：

```
assets/src/config/protocal/cmd_resolve_154.luac   ×2   （协议定义，预期命中）
assets/src/game/ghost/ghost_mon.luac              ×1   ← ★ 发送点在这里
assets/src/config/config_title.luac               ×1   （数值巧合，无关）
assets/src/config/config_skill_talent.luac / config_role_career.luac （数值巧合）
```

⇒ **`CS_15402` 由 `ghost_mon.luac` 发出**（不是 ghost_ctrl）。

---

## 二、反汇编：`ghost_mon` proto#4 的发送条件

`ghost_mon.luac` proto#4（bc=150，字符串含 `SendProtocal / mission_bid / GetPrototype /
mis_hongchen / mis_key / gotoTarget / findVoTarget / mon_cfg / inFight`）：

```lua
if Battle:getInstance():inFight() then
    message(getString('您正在战斗中'))
    return                                   -- ① 战斗中不处理
end
if not self.mon_cfg then <跳过> end
-- 组 vo：type=FindType.MONSTER, sceneId=mon_cfg.map_bid,
--        pos=cc.p(mon_cfg.x, mon_cfg.y), bid=self.mon_bid, findVoTarget=SceneModel
... :gotoTarget ...

self.select = nil
if self.mis_key == <K> then                   -- ② BC 66-68
    local proto = ProtocalRulesMgr:getInstance():GetPrototype(15402)   -- BC 74-75
    proto.mission_bid = <参数>                                          -- BC 77
    ProtocalRulesMgr:getInstance():SendProtocal(proto)                  -- BC 83-84
end
-- 之后对其它 mis_key 重复同样形状（BC 87+）
```

**⇒ 发送 `CS_15402` 需要同时满足**：
1. **不在战斗中**；
2. **有 `self.mon_cfg`**（挂机怪物配置：`map_bid/x/y`）；
3. 该 `GhostMon` 实例的 **`mis_key` 命中某个字符串分支**（`mis_hongchen` 等）。

而 `GhostMon` 实例是**由 `ghost_ctrl.handle15402`（收到服务端 `SC_15402` 后）创建的** ——
也就是说：**这条消息在客户端侧是"先收到、后回发"**（服务端要先把 `15402` 推/答给它）。

---

## 三、按上述条件做的实验（**三个全部否证**）

| # | 假设 | 变量 | 结果 |
|---|---|---|---|
| A | `loop_count` 为 0 所以不启动 | `guaji?n=0` | 点 4019 → `15400` ✓ → **无 `15402`** |
| B | 需要非 0 轮次（R48 当年用 10） | `guaji?n=10` | `15405 → loop_count=10`，`15400` ✓ → **无 `15402`** |
| C | 缺 `SC_15401{loop_num}`（"轮数配置"） | `guaji_push_15401=true` + `loop_num=10`（取自 `config_richang` 面板 208 `max_num=10`） | 该次点击未命中按钮，**未取得结论**；开关已复位为 false |
| D | 挂机线任务 10010 **不在途**，客户端不建 GhostMon | `missions[10010].mission_status: 3 → 2`（改后 `SC_12400` 确实列出 `(10010, status=2)`） | 重启客户端重走：`15405` ✓、`15400` ✓ → **仍无 `15402`** |

⇒ **诚实结论**：`15400` 之后客户端不发 `15402` 的**真正前置仍未取证**。
三个看起来合理的假设都被实测否掉 —— 这本身就是有价值的进展（排除了三条路）。

> ★ 本轮 `guaji?n=10` 那次客户端在 `12400` 里看到 10010 在途后，还**真的把 10051 推进了一步**
> （`mission_status` 2 → 1）⇒ 说明**任务链本身是通的**，改变的是玩家数据，收尾已还原。

---

## 四、下一步（把范围收窄到"能取证"的动作）

| # | 动作 | 为什么这条路可行 |
|---|---|---|
| 1 | **反汇编 `GhostMon:initData` 的调用者**（`ghost_ctrl` proto#30 → `mon_hongchen:initData(data)`），看它是否**只在收到 `SC_15402` 后**才建实例 | 若是，则"客户端先发 15402"这条链**根本不存在**，R48 观察到的 `15402` 属于另一条路径（登录时的场景初始化） |
| 2 | 用**探针**在真机上报 `GhostCtrl.mon_hongchen` 是否存在、`mis_key` 是什么 | 现有探针已能挂钩 `npcE/dlgS/smCall`；加一条即可，**不必猜** |
| 3 | 若确认需要服务端**主动推** `SC_15402{mission_bid}`，则按 `config_guaji` 的等级段把地图坐标推给客户端 | 我们的 `15402` **应答**实现已经过 `verify_guaji.py` 验证，改成"主动推"是同一份编码 |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/find_cmd_ref.py` | **新增**：全 APK 扫"谁引用命令 N"（含第一版 bug 与修法的注释） |
| `tools/exp_mission_state.py` | **新增**：`missions` 状态只读查看 / 改值 / 回滚（本轮实验 D 用它，收尾已还原） |
| `analysis/_ghost_mon.txt` | `ghost_mon.luac` 全量反汇编（发送条件真源） |
| `analysis/1.4.9/round59_cs15402_condition.md` | 本报告 |
| `server/config.json` | `guaji_push_15401` 已**复位为 false**（实验 C 开关保留，供下次一键复现） |

---

## 六、收尾（真机与数据状态）

| 项 | 值 |
|---|---|
| 玩家 | `rid=1001` / lev=70 / gold 841046 / 背包 27 / 场景 10001 |
| `missions` | **已还原**：10010/10020/10030/10040 = 3、10051 = **2**（实验前值） |
| `guaji_state` | `loop_count = 0`（安全默认） |
| 服务端 | 在线，9000 恰好 1 监听，`stderr` **0 字节** |
| 六道门禁 + 回归 | 全绿（lint 0 遮蔽 / CS 2463-0 / SC 静态 85+1空-0 / SC 在线 86-86 / 专用 63-63 / 门禁 E PASS；`verify_guaji`、`level_consistency`、`race`、`arena`、`dungeon`、`mission_hook` 全 PASS） |

---

## 七、一句话

> **`15400` 真机已通（R58 两次复现）；`15402` 的发送条件在客户端里是"先收到、后回发"**
> （`ghost_mon` proto#4 需要 `mon_cfg` + `mis_key` 命中 + 非战斗）。
> 四个实验（loop_count 0/10、补推 15401、任务 10010 在途）**全部否证** ⇒ 下一条路是
> **反查 `GhostMon:initData` 的调用者**，而不是继续调数值。
