# 任务系统：分支④ 的根因已找到 —— `mis_config.progress` 是**空表**

> **结论**：真实主线任务（`MIS_ZHU`）走 `missionContent` 分支④ 时，
> **`vo:getConfig().progress` 是一个 0 条目的空表**，
> 于是 `progress[mis_status]` 取到 nil ⇒ 后文按 progress 拼正文的逻辑无数据可用 ⇒
> **`mis_content` 始终不被赋值**（实测 `after_NIL`）。

---

## ★★ 决定性实测

```
t=misProg&v=progress_table_n0_type_1_status_1
t=mcCall&v=bid_10010_mtype_1_lnum_1_tval_1_before_NIL_after_NIL
```

| 读数 | 含义 |
|---|---|
| `progress_table_n0` | **`progress` 是 table，但 0 个条目（空表）** |
| `type_1` / `status_1` | `mis_type=MIS_ZHU`、`mis_status=1` |
| `after_NIL` | 因此没能写出 `mis_content` |

对照 `missionContent` 分支④ 的头两个门禁（反汇编 `mission_util proto[0]`）：

```lua
local roleVo = RoleCtrl:getInstance():getRoleVo()     -- @53-59
if roleVo == nil then return end                      -- @60-62   （我们有 RoleVo，过）
local prog = vo:getConfig().progress                  -- @65-72
if prog == nil then return end                        -- @73-75   （是空 table，**也过**）
local step = prog[vo.mis_status]                      -- @76-80  ★ 空表 ⇒ nil
...  此后全部围绕 step 拼文案（MIS_COLLECT / commit_npc_id / accept_npc_id / mis_code 等）
```

**⇒ 门禁都过了，但 `progress` 里没有条目，`prog[mis_status]` 是 nil，
后续所有分支都建立在它之上，所以最后一句话都没写出来。**

---

## ★ 这意味着什么

- **不是**我们发送的 `SC_12400` 字段错（`bid/status/loop_num/target_value` 都已验证正确）。
- **不是** `mis_config` 本身缺失（它 36 个字段齐全、`name`/`desc` 都有内容）。
- **是** `mis_config.progress` **为空** —— 而这个字段**不在 `SC_12400` 协议里**，
  也不在 `config_mission.luac` 的那条 TableConst 里（我逐指令看过度，
  该条目没有 `progress` 键，`progress` 是外面另外挂上去的）。

⇒ **`progress` 很可能是由另一条消息在下发任务进度时填进去的。**
（这也解释了为什么 `defaultMissionId` 那条能显示：它走的分支①根本不看 `progress`。）

---

## ★ 下一步：追 `progress` 是谁填的

**做法（仍按"先取证再改"）**：

1. 搜 `TSETS progress` / `progress` 的**写入点**，重点看 mission 相关文件
   （`mission_data2.luac`、`mission_ctrl.luac`）以及 `SC_12401`/`SC_12416` 等处理器；
2. 若确认由某条**服务端消息**填充，就从 `protocol/manual.md` 找该消息的字段，
   按定义补发（优先 `12401`，它的 `missions` 字段与 `12400` 同构，最可能是"带进度的任务列表"）；
3. 每步仍用探针量 `misProg` 的 `n` 值变化 —— **从 `n0` 变成非 0 就是命中了**。

> 当前已跑通的部分：任务通道、任务名、分类、以及"必成"的 `defaultMissionId` 文案。
> 剩下的只是"让普通任务的 `progress` 有数据"。

---

## 一、任务协议族 = `124xx`（从 `mission_ctrl.luac` 提取，共 33 条）

`mission_ctrl.luac` 的 `RegisterProtocal` 映射（共 33 条）：

| cmd | handler | 推测用途 |
|---|---|---|
| **12400** | `handle12400` | **任务列表** |
| 12401 | `handle12401` | 任务列表（另一组） |
| 12402 | `receiveHandler` | 领取任务 |
| 12403 | `submitHandler` | 提交任务 |
| 12404 | `giveUpHandler` | 放弃任务 |
| 12405 | `handle12405` | — |
| 12406/12407 | `deleteAccessHandler` / `addAccessHandler` | 可接列表增删 |
| 12408/12409 | `deleteCanHandler` / `addCanHandler` | 可接列表增删 |
| 12412–12417 | `huanHandler`/`extHandler`/`talkHandler`/`subGoodsHandler`/**`mainTaskHandler`**/`subHeroHandler` | 各类任务操作 |
| 12420/12421/12422/12440/12450/12451/12452/12460/12499 | `handle…` | 其它 |
| 15405/15420/15421/15422/18500/18501/18505/19500 | `handle…` | 关联系统 |

## 二、`SC_12400` 结构（`protocol/manual.md`，**全简单类型**）

```
mission_list : table(
    mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
    loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
    value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32 )
```

**没有未解出的 `D|Dsc*|` 子表** ⇒ 可以安全编码。

## 三、任务 bid 的真实范围

`config_mission.luac`（504KB）里 **772 个整数常量全是 5 位数，且都在 `35000+`**：

```
35000, 35001, 35002 … 35016, 35030 … 35035, 35050 … 35056 …
```

⇒ 用 `mission_bid = 35000` 是合法任务。

## 四、关键发现：客户端**不会主动请求**任务列表

实测 TCP 日志：

```
<< 12400 SC_12400 mission_list=1 (42 bytes)      ← 服务端推送
（没有任何 >> cmd=124… ）                          ← 客户端从未请求
```

⇒ **任务列表必须由服务端主动推送**（与此前"未被回复的命令多为 `SC_*`-only"的推断一致）。

**做法**：在收到 `10300`（客户端初始化完毕）后，连同 `10200` 补推一起，**推一次 `SC_12400`**。

## 五、实测结果：任务名已显示 ✅

服务端实现（`server/mock_server.py`）：

```python
def build_mission_entry(m):  # 13 个字段按 SC_12400 定义顺序拼接
    return (w_u32(m['mission_bid']) + w_u8(m['mission_status']) + w_u16(m['commit_num'])
            + w_u16(m['loop_count']) + w_u16(m['loop_num']) + w_u8(m['code'])
            + w_u8(m['process_status']) + w_u32(m['target']) + w_u32(m['target_value'])
            + w_u32(m['value']) + w_u8(m['show_lave_time']) + w_u32(m['lave_time'])
            + w_u32(m['accept_time']))

def build_12400(missions):
    b = w_u16(len(missions))
    for m in missions: b += build_mission_entry(m)
    return b
```

`config.json` 里 `missions` 给一条 `mission_bid=35000`。

**视觉确认（`shots/stage3_task1.png`）**：

> "右上角'任务'按钮右侧弹出一个灰色面板，内有两行文字：
> 第一行是**蓝色字体「学院-寻人」**，第二行是黑色字体 **「nil」**。"
> "与'任务栏完全是空的'相比，**本次有变化**：任务按钮旁弹出了含'学院-寻人'的灰色小面板，
> **说明任务系统已触发显示**（尽管内容异常）。"

**⇒ `mission_bid=35000` 被客户端正确解析，任务名「学院-寻人」来自客户端自带的
`config_mission.luac`** —— 说明通道完全正确。

## 六、唯一待解决：第二行显示 `nil`

任务面板第二行（应为目标/进度文案）显示 `nil`，说明**某个字段没给对**。

**候选原因**：

1. `target = 0` —— 客户端可能用 `target` 去 `config_mission` 里查目标文案，0 查不到 → nil；
2. 或需要额外的任务进度/目标消息（例如 12401 或某条 `SC_*`）；
3. 或 `mission_status` 取值不对（我给的 1），导致取了未初始化的分支。

**下一步取证**（下一步该做的）：

1. 从 `config_mission.luac` 里把 `mission_bid=35000` 那条的**真实 `target` / `target_value` / `progress`** 读出来填上；
2. 若仍 nil，再测 `mission_status` 的不同取值（0/1/2/3）；
3. 该配置一个 proto 有 18737 条指令、`knum` 772 个，需要按嵌套结构解析
   （`Config.Mission[bid] = {target=…, progress=…, …}`）。

---

## 七、当前总体状态

| 项 | 状态 |
|---|---|
| ① 地图模糊 | ✅ 已解决 |
| ② 看不到角色 | ✅ 已解决 |
| ④ 没有 NPC | ✅ 已解决（25 个，真实中文名） |
| ③ 任务栏 | ⚠️ **通道已打通、任务名已显示**；第二行目标文案仍为 `nil`，下一步补字段 |
