# R54：挂机前置取证 —— `CS_15400` 的唯一发送点与触发按钮

> 目标（R53 §六 第 1 项）：**挂钩 `15400` 的发送条件**，用取证代替猜测。
> **结论：找到了，而且是个精确的按钮 id。** 本轮**不改服务端行为**，只出取证结果 + 下一步定位方向。
> **时间**：2026-09-29 10:55 – 11:10。

---

## 一、结论（TL;DR）

```lua
-- npc_ctrl.luac
function NpcCtrl:acceptNewHuanMis()          -- proto#42（FNEW → TSETS 'acceptNewHuanMis'）
    ProtocalRulesMgr:getInstance():GetPrototype(15400)   -- ★ 这就是 CS_15400 的唯一发送点
    ...:SendProtocal()
end

function NpcCtrl:funBtnHandler(btn)          -- proto#33
    if btn.type ~= K(0)=1 then <next> end
    if btn.id == K(1)=4017 then acceptBaotuMis()     end   -- 接取宝图任务
    if btn.id == K(2)=4018 then exchangeBaotu()      end   -- 兑换宝图
    if btn.id == K(3)=4019 then acceptNewHuanMis()   end   -- ★★ 接受幻境任务 → CS_15400
    if btn.id == K(4)=4020 then checkItems()         end
end
```

**⇒ `CS_15400` 只在玩家点到 `id == 4019` 的 NPC 对话按钮时才发出。**
不是 `loop_count` 的数值问题，也不是"走到位就停"——是**那个按钮从来没被点到**。

---

## 二、取证过程（可复核）

### 2.1 谁注册 / 谁发送

| 命令 | 注册处（接收） | 发送处 |
|---|---|---|
| `15400` | `npc_ctrl.luac`（`KSHORT 15400` + `KSTR 'handle15400'`） | **`npc_ctrl.luac` proto#42** |
| `15405` | `mission_ctrl.luac`（`handle15405`） | — |

全 APK 扫描 `acceptNewHuanMis` 字符串：**只有 `npc_ctrl.luac` 命中**。

### 2.2 proto#42 的字节码（原文）

```
--- proto #42 bc=13 param=1 fsize=5 uv=0 flags=0x00 ---
  strings(4): 'SendProtocal', 'GetPrototype', 'getInstance', 'ProtocalRulesMgr'
     0  GGET    A=1   D=0
     1  MOV     A=2   D=1
     2  TGETS   A=1   B=1   C=1     ; ['getInstance']
     3  CALL    A=1   D=514
     4  MOV     A=2   D=1
     5  TGETS   A=1   B=1   C=2     ; ['GetPrototype']
     6  KSHORT  A=3   D=15400       ; ★ 15400
     7  CALL    A=1   D=515
     8  MOV     A=3   D=0
     9  TGETS   A=2   B=0   C=3     ; ['SendProtocal']
    10  MOV     A=4   D=1
    11  CALL    A=2   D=259
    12  RET0    A=0   D=1
```

### 2.3 方法名与调用点

```
L3814: 83  FNEW  A=1 D=54 ; ChildRef(#42)
L3815: 84  TSETS A=1 B=0 C=53 ; ['acceptNewHuanMis']      ← proto#42 就是它

L915: 41  TGETS A=3 B=0 C=12 ; ['acceptNewHuanMis']       ← 唯一调用点
```

调用点的 if 链与 `knum`（**逐个核对，不是按顺序数出来的**）：

```
knum(90): [1, 4017, 4018, 4019, 4020, 9004, 4025, ...]
                K(1)  K(2)  K(3)  K(4)
```

| 位置 | 指令 | 含义 |
|---|---|---|
| 13 | `ISNEN A=3 D=0` | `btn.type ~= K(0)=1` |
| 16 | `ISNEN A=3 D=1` | `btn.id ~= 4017` |
| 30 | `ISNEN A=3 D=2` | `btn.id ~= 4018` |
| **37** | **`ISNEN A=3 D=3`** | **`btn.id ~= 4019`** |
| **41** | **`TGETS ['acceptNewHuanMis']`** | **⇒ 点 `id==4019` 时发出 `CS_15400`** |
| 44 | `ISNEN A=3 D=4` | `btn.id ~= 4020` |

> ★ 一开始按"第 3 个分支就是 id==3"读，**差点写错成 3**；
> 是 `knum` 那一行把真实常量钉住了（**4019**）。这与项目一贯的教训一致：
> **分支顺序不是证据，常量表才是。**

---

## 三、为什么 R48 / 本轮都点不出 `15400`

| 观测 | 解释 |
|---|---|
| R48 Step 2/3：点「参与」→ **只有 `10204` 寻路**，无任务命令 | 「参与」按钮属于**日常面板**（`config_richang` panel 208），走的是寻路，不是 `funBtnHandler` |
| 本轮真机：`日常`→`参与` → `15405`（回 `loop_count=1/10`）→ `10204` → 只有心跳 | 同上；**没有点到 id=4019** |
| 「请选择要做」弹窗里**只有一个**选项「学院任务(0/10 环)」 | 该弹窗的按钮不是 4017~4020 之一 ⇒ 走不到 `acceptNewHuanMis` |

⇒ **R48 当时看到的那条 `15400` 是偶发/时序相关，不是稳定路径**；本轮把真正的触发条件钉死了。

---

## 四、下一步（精确到可执行）

| # | 动作 | 说明 |
|---|---|---|
| 1 | **找 `4019` 这个按钮属于哪个 NPC 的对话框** | `config_npc.luac` 里含「红尘」6 处 —— 挂机线（`GhostMon('mis_hongchen')`）的 NPC 很可能就在这里；按 npc bid 反查其对话按钮表 |
| 2 | **确认按钮的来源是客户端配置还是服务端下发** | 若客户端配置 ⇒ 玩家走到该 NPC 点对按钮即可（本服无需改）；若服务端下发 ⇒ 我们要补那条下发消息 |
| 3 | 走通路后按 `15405→15400→15402→15403→15404` 顺序验证 | `15402/15403/15404` 已在 R48/R53 做通并有 `tools/verify_guaji.py` 守着 |
| 4 | **不要把 `loop_count` 当成开关** | R53 已实测：给 1 或 10 行为一致 ⇒ 它**不是**当前卡点 |

---

## 五、顺带发现（与本轮主题无关，但该记）

| 项 | 内容 |
|---|---|
| `server/_npcs_10001.json` | **文件被截断**（163 行，末行停在 `"id": `），`json.load` 报错；且 `mock_server.py` **从不读它** ⇒ **未使用的残缺产物**（无运行时影响）。建议：要么补全，要么删除（本轮未动它）。 |
| 客户端无「幻境」字样 | 全 APK 扫描：`幻境` **0 命中**；`红尘` 命中 14 个文件（`config_mon_data` 59× / `config_skill*` / `config_mission` 18× / `config_npc` 6×）⇒ **挂机线在客户端叫"红尘"**，按钮文案不会是「幻境」。定位按钮时按"红尘"找，别按"幻境"找。 |

---

## 六、验证 / 本轮影响

**本轮未改任何服务端代码**（纯取证 + 文档），因此六道门禁结果与 R53 一致：

```
lint 0 遮蔽（169 / 64 / 22） ｜ CS 规格 2463/0 ｜ SC 静态 85+1空/0
SC 在线 86/86 ｜ 专用查询 63/63 ｜ 门禁 E PASS（132 条 / 空表告警 0）
server_stderr.log 0 字节 ｜ 9000 端口恰好 1 个监听
```

真机实验期间把 `guaji_state.loop_count` **复位为 0**（默认安全值），玩家数据未被污染。

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `analysis/_npc_ctrl.txt` | `npc_ctrl.luac` 全量反汇编（本轮取证的真源） |
| `analysis/1.4.9/round54_guaji_trigger_forensics.md` | 本报告 |
