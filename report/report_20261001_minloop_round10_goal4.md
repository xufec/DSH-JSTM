# 最小回环 · 第 10 轮（goal round 4/20）—— 三问全部有答案：**列表被消费了，但消费过程抛异常**

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：定位"服务器列表为何没被消费 / 10102 为何没上线"。

---

## 〇、一句话结论

> **客户端确实调用了列表消费函数，而且我喂给它的数据完全正确**
> （`v39_consume=CALLED ... server_list_n=1 first{srv_id=1,zone_id=1,ip=10.0.2.2,port=9000}`），
> **但它内部抛异常中止了**：
> `v39_consume_ret=ok=false err=…attempt to concatenate field 'zone_id' (a nil value)`
> ⇒ 列表没被吃进去 → `loginData` 为空 → 没有游戏服地址 → `10102/10103` 上不了线。
> **整条上游因果链在本轮被闭合到"一个具体的 nil"上**。

---

## 一、三问的答案（v39，客户端 `dsh_v39.txt`）

| # | 问题 | 答案 | 证据 |
|---|---|---|---|
| ① | 客户端是否走了"列表为空"弹窗分支？ | ❌ **没有** | 钩子 `CommonAlert.show` 已装但**全程未触发** |
| ② | 列表消费函数有没有被调用？入参对不对？ | ✅ **被调用了，参数完全正确** | `v39_consume=CALLED type=table has_data=true server_list_n=1 first{srv_id=1,zone_id=1,ip=10.0.2.2,port=9000} has_msg=false` |
| ②b | 调用结果？ | ❌ **抛异常** | `v39_consume_ret=ok=false err=denglu_mgr.luac: attempt to concatenate field 'zone_id' (a nil value)` |
| ③ | `10102/10103` 是否躺在 `msg_list` 队列里？ | ❌ **否证**（队列是空的） | `v39_msgl_list=type=table`、`v39_msg_list=n=0 []`；调 `request10102Login` 之后 `msg_list_n` 全程 `0`（n=20…70） |
| ③b | `game_net_id` | `1` | `v39_game_net_id=1` |

> ⇒ 上一轮的"消息队列假设"**被否证**。`msg_list` 不是原因。

---

## 二、★ 异常点已定位到具体指令（`denglu_mgr.luac` proto#8，params=4）

```
58-65  GGET cc ; UserDefault:getInstance() ; getStringForKey('local_srv_id')   ← 读一个**存档字符串**
...
195-211（第二处拼接）：
  195 ISF  A=0 D=6   ; 若寄存器6为假 → 跳到 212（走 loginData.srv_id 分支）
  197 MOV  A=12 D=0  ; self
  198 TGETS getServer
  199 TGETS A=13 B=6 C=28  ; **寄存器6.srv_id**
  200 IST / 201 JMP(+4 → 206)   ← srv_id 存在就**跳过拼接**
  202 TGETS A=13 B=6 C=29  ; 寄存器6.platform
  203 KSTR  '_'
  204 TGETS A=15 B=6 C=31  ; 寄存器6.zone_id     ★ **就是这里 nil**
  205 CAT   A=13 D=3343    ; platform .. '_' .. zone_id
  206 CALL  getServer(...) ; 208 setCurSrv(...)
212-215 TGETS loginData ; TGETS loginData.srv_id ; …
```

**读法**：寄存器 6 是一张**既有 `platform`、却没有 `zone_id`** 的表（否则报的会是 `platform`），
而它来自 `UserDefault:getStringForKey('local_srv_id')` 这条线（指令 58–65）。
⇒ **客户端存档里的 `local_srv_id` 状态与"当成表用"的用法不匹配**，于是在 `zone_id` 处炸掉，
**整段列表消费中止**。

> 诚实标注：寄存器 6 的**确切来源**（是 `local_srv_id` 这个字符串本身被当表用，
> 还是由它查出来的条目为空表）本轮**未单独验证** ⇒ 标 **UNKNOWN**。
> 但两条修法都不依赖这个细节（见下）。

---

## 三、完成 / 未完成

### 3.1 完成
1. **闭合上游因果链**：列表被调用 → 内部抛异常 → 列表没吃进去 → `loginData` 空 → 无游戏服地址 → `10102/10103` 不上线。
2. **否证"消息队列"假设**（`msg_list` 全程为空）。
3. **否证"客户端走了空列表弹窗分支"**（`CommonAlert.show` 未触发）⇒ 说明**我发的应答是被接受的**，
   问题在客户端自己的归一化逻辑。
4. 异常点**精确定位到指令级**（proto#8 的 204/205）。
5. 配方继续稳定（v39：`Stop` 跳 → `initInstance` → `restartNetManager` → 连上、登录、心跳）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | 客户端成功消费服务器列表（`getServerList()`/`loginData` 非空） | ❌（已到"只差这一步"） |
| 2 | `10102` 上线 → 进场景 `10200/10201` | ❌ |
| 3 | 任务/战斗/结算/掉落/提交/奖励 | ❌ |
| 4 | 寄存器 6 的确切来源 | **UNKNOWN** |

---

## 四、下一轮直接照做（两条修法，都很便宜；建议**先做 A 再做 B**）

**A. 服务端侧补字段（不用重打包，改完立刻可验）**
   - 在 `/gateway/mobile/json` 的应答里**把 `zone_id / platform / srv_id / main_*` 也放到
     `data` 层与顶层**（现在只在条目里），让"任何一层读 zone_id"都不会是 nil；
   - 顺带补 `local_srv_id`（对象形式：`{srv_id='1', platform='ewan', zone_id='1'}`），
     因为 proto#8 明确读这个名字。
   - 判据：`v39_consume_ret` 从 `ok=false` 变 `ok=true`，且 `getServerList()` 非空。

**B. 探针侧确认寄存器 6 的来源（一次挂钩子即可定论）**
   - 包住 `cc.UserDefault:getInstance():getStringForKey('local_srv_id')`，打印它的真实返回值；
   - 若它返回的是**字符串**而后续当表用 ⇒ 直接**用 `setStringForKey` 写入一个能被解析的值**，
     或改成"跳过该分支"（指令 199 的 `srv_id` 一旦存在就会跳过拼接 ⇒ 只要让它查得到 `srv_id` 即可）。

**C. 拿到 `loginData` 非空之后**：10102 应能上线 → 本服推 `10200/10201` 进场景 →
   再往 `10300/12400/20002/12403/10502` 推进（这些本服都已实现并有自检覆盖）。

---

## 六、★ 本轮追加：Bug 已定位并**修好了**（`v39_consume_ret: ok=false → ok=true`）

### 6.1 先否证一条（诚实记录）

我按"把 `zone_id/platform/srv_id/local_srv_id` 补到**条目 / data / 顶层**三层"改了服务端应答
（`min_loop_server.py::_server_list`，无需重打包），重启后让客户端自己重发 POST 再消费 ——
**错误一模一样**（`ok=false … zone_id nil`），连报 3 次。
⇒ **"nil 来自我的应答字段缺失"这条假设被否证**。（该补字段的改动保留，它是无害的防御。）

### 6.2 真正的根因：`local_srv_id` 是**字符串**，却被当**表**用

v40 追加块把 UserDefault 读出来并落盘：

```
v40_read=local_srv_id=1 type=string          ← ★ 存档里是字符串 "1"
v40_key=last_login_account=dsh_local
v40_key=local_srv_id=1
v40_set=setStringForKey(local_srv_id,1) ok=true now=1
```

对照 proto#8 指令 58-65（`getStringForKey('local_srv_id')`）与 195-211
（`r6.srv_id / r6.platform / r6.zone_id`）⇒ **同一份数据，一边按字符串存、一边按表读** ⇒
字符串上取 `.zone_id` 得 nil ⇒ `platform .. '_' .. zone_id` 抛异常 ⇒ 整段消费中止。

### 6.3 修好之后（**本轮决定性结果**）

```
v39_consume_ret=ok=true err=nil      ← ★★ 服务器列表消费**成功**了（此前恒为 ok=false）
v39_consume_ret=ok=true err=nil
```

⇒ **上游那道门被打开了**：客户端终于能正确吃下服务器列表。

### 6.4 但 10102 仍未上线（未完成，且发现了新现象）

服务端 `live8` 里在 40 秒内出现 **4 次 `>> 1110`**（客户端**反复重登录**，不是稳定态），
且**依旧没有 `>> 10102`**。
⇒ 列表消费修好后，"没有游戏服地址"这一环应当已解除，但客户端**进入了另一个循环**（反复 1110）。
这正是下一轮要查的点（优先看 `getLoginData()` 现在是否非空、以及 1110 循环的触发条件）。

---

## 七、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_minloop_block.lua` | 现为 **v39**：配方 + `CommonAlert.show` / `managerServerListByJsonObj` / `msg_list` 三处观察 |
| 设备内 `files/dsh_v39.txt` | ★ 本轮核心证据（消费被调用、入参正确、内部抛异常、队列为空） |
| `logs/minloop/live7_stdout.log` | 服务端侧（10001/1110/1199 到达；10102 缺席） |
| `analysis/denglu_mgr.luac` + `tools/ml_dump_proto.py` | 静态分析依据（proto#8 逐指令） |
