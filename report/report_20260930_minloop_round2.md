# 最小回环 · 第 2 轮（真机端到端攻坚）—— 把客户端从"永远卡在加载"推到"已经请求服务器列表"

> 时间：2026-09-30 23:00–24:00 ｜ 目标 APK：`anzbao/jstm.apk`（1.4.9 / qihoo）｜ 环境：MuMu + adb root + frida + tcpdump
> 纪律：只写有**客户端落盘 / 服务端日志 / 抓包**三重证据的结论；**并修正上一轮报告里被本轮测量推翻的说法**。

---

## 〇、一句话结论

> 上一轮把客户端判成"启动流程走不完/画面冻结"——**本轮实测推翻了它**：
> 客户端其实**加载正常**（56%→100% 只用 2 秒、304 个模块全部加载完），
> 它卡住是因为**没人调用 `DengluCtrl:openView()` / `beginGame()`**（卡在加载界面）。
> 探针替它调用这两个入口后，客户端**自己走出了加载界面，并主动 `POST /gateway/mobile/json`**；
> 我又修掉了自己最小服网关应答里缺的字段（`srv_name`/`erl_port`/`main_srv_id` 等），
> 客户端的**每 6 秒重请求循环随之停止**（说明它接受了服务器列表）。
> **仍未完成**：它还没连游戏服 TCP（`adb` 盲点触摸 26 个位置都点不中按钮）——
> 差的是"用文本把当前界面的按钮坐标 dump 出来"，工具已在本轮写好。

---

## 一、★ 本轮最大突破：把客户端推出加载界面

### 1.1 卡在哪（文本证据，不靠截图）

用探针把 Cocos 场景树 dump 成文本（`server/_minloop_block.lua` v12/v14，输出到设备
`/data/user/0/com.shiyue.dldl.ewan.qihoo/files/dsh_ui3.txt`）：

```
D2 |Sprite|adb=1280,720|size=1280,720|vis=1
D3 |Sprite|adb=1280,456|size=545,211      ← 标题/logo
D5 |Label |adb=1448,1413|'100%'
D5 |Label |adb=1229,1413|'玩命加载中...'   ← ★ 关键：tips 停在这句
D4 |Node  |adb=1280,720|size=590x350|vis=0 ← 一个隐藏提示框（'建议您在wifi...' + 两个按钮）
```

对照本项目自己的反汇编文档 `STARTUP_UPDATE_FLOW.md` §2：

```
update_finish(proto#36)
  ⑥ version_view:setTips('玩命加载中...')          ← 屏幕上正是这句
  ⑦ video_finish = video_player(self, proto#32)   ← proto#32 = 等 #GameModule==0 → initInstance()
                                                     并设 tips '开始游戏...'
  ⑧ video_finish:scheduleUpdateWithPriorityLua(self, proto#35, 0)
  → initInstance(proto#31) → beginGame → DengluCtrl:openView()（登录界面）
```

**判据**：tips 仍是 `玩命加载中...`（没变成 `开始游戏...`）⇒ 第 ⑦/⑧ 步之后的推进没有发生。

### 1.2 先纠正上一轮的两个错误结论（本轮实测）

| 上一轮的说法 | 本轮实测 | 证据 |
|---|---|---|
| "画面 40 分钟逐像素不变 ⇒ 主循环冻结、tick 停摆" | ❌ **不成立**：加载**在正常推进**，`tick` 一直在报 | `dsh_pct.txt` 时间线：`t=…935 pct=[56%]` → `t=…937 pct=[100%]`；同一时段 `tick` 上报 540 条 |
| "客户端启动流程走不完（模块没加载）" | ❌ **不成立**：`GameModule` **304 → 0**（2 秒内加载完） | `dsh_gm.txt`：`n=1 len=304 head=game/guider/...` → `n=2 len=0` |
| "`GameNet:Update()` 抛异常 ⇒ 网络泵坏" | ❌ **改判**：**这个 build 里根本没有 `GameNet:Update`**（`Update=nil`）；真正的泵是 `net_manager:Update()` + `doOneMsg()`，**两者都正常返回** | `dsh_ml7.txt`：`ml7_types=gn.Update=nil ... gn.doOneMsg=function`；`ml7_pump2=netmgr_Update_ok=true` |

### 1.3 放行（本轮的动作与结果）

探针 v16 直接调用两个**文档确证过的入口**：

```
ml16_denglu  = inst=table openView=function
ml16_openView = ok=true err=nil          ← DengluCtrl:openView()
ml16_beginGame= ok=true err=nil          ← beginGame()
```

结果（**服务端侧日志**）：

```
[23:50:49] HTTP POST /gateway/mobile/json     ← ★ 客户端第一次主动请求网关（此前一次都没有）
```

场景树也随之变了（tips 扫描返回空 ⇒ 已切到别的界面）。

---

## 二、★ 第二个突破：修网关应答，重请求循环停止

| 时刻 | 现象 |
|---|---|
| 修之前 | 客户端 **每 ~6 秒**重发一次 `POST /gateway/mobile/json`（23:52:25/31/38/44/50/56…）= 文档里"列表为空 → 反复重请求"的症状 |
| 修之后 | **75 秒内只有 1 次** POST（23:56:50）⇒ 客户端**接受了**这份服务器列表 |

改的是什么：把应答里的每个 server 条目与参考服 `normalize_server_item()`
（`server/mock_server.py:161`，那份是实机验证过的）**逐字段对齐**，补上客户端真正会读的键：

```
srv_name, erl_port, main_srv_id(= platform_zone 形式), zone_id, main_platform, main_zone_id,
platform_flag, can_create_role, maintain, first_zone, recomed, isnew, open_time, begin_time
```

---

## 三、★ 排除项（本轮花了力气**证明"不是"什么**，同样重要）

| # | 假设 | 结论 | 证据 |
|---|---|---|---|
| 1 | "服务端漏读客户端字节" | ❌ 排除 | 服务端加了**字节级日志**（`-- recv N bytes`）；控制客户端（Python）发同样帧 → 服务端正常记录 `>> 10001 / >> 1199` |
| 2 | "客户端其实发了帧，只是帧格式不对" | ❌ 排除 | `tcpdump -i any port 9000`：**只有 SYN/SYN-ACK/ACK，双向 0 个数据包**（14 包全是握手/收尾） |
| 3 | "触摸能触发登录" | ❌ 排除 | 26 个位置盲扫（含两次独立扫），每处后查 `tcpdump` → **带数据包数恒为 0** |
| 4 | "syscall 层能看到客户端写" | ⚠️ **本次作废** | frida hook `send/write` 报 0 次写，但**同一时间窗客户端写了 1575 条 HTTP 上报** ⇒ **钩子是瞎的**（ARM 翻译层），该结论**不得采信** |
| 5 | "`SendProtocal`/`Encode` 返回 true ⇒ 帧出去了" | ❌ 排除 | 两者都 `true`、`net_manager:Update()` 也 `ok`，但抓包 0 数据包 ⇒ **Lua 侧的 true 是假成功** |

---

## 四、完成 / 未完成 / 优化 / 继续

### 4.1 本轮完成

1. 探针 12 个版本（v3→v16）把客户端内部 API 摸清并**写成文本证据**（`dsh_ml*.txt`、`dsh_ui*.txt`、`dsh_gm.txt`、`dsh_pct.txt`）。
2. 修正 3 条上一轮的错误结论（见 §1.2）——**保留在案，不删**。
3. 找到并**推开**了"永远卡在加载界面"这堵墙：`openView()` + `beginGame()`。
4. 客户端**第一次**主动请求网关；修好网关应答后**重请求循环停止**。
5. 新增两个可复用工具：`tools/minloop_frida_send.py`（附**"钩子是否有效"的自证要求**）、`server/_minloop_block.lua` 的 **UI 树文本 dump**（含 adb 坐标换算）。
6. 最小回环服加**字节级日志**与 POST 体积日志。

### 4.2 本轮未完成

| # | 项 | 状态 | 卡点 |
|---|---|---|---|
| 1 | 客户端连上游戏服 TCP 并发帧 | ❌ | 还停在**服务器列表界面**，需要用**坐标**点中"进入游戏/选服"项；盲扫 26 处无效 |
| 2 | 真机跑完整条回环 | ❌ | 同 1 |
| 3 | 最小服的 `/gateway` 之外 CDN 路径 | ⚠️ | 客户端目前没请求过 CDN（`/cdn/*`、`/update/*` 一次都没来） |

### 4.3 该怎么优化（按顺序）

1. **给 UI dump 换成"列表界面触发"**（现成代码，5 分钟）：把 `server/_minloop_block.lua` 里 v14 的触发条件从"出现 100%"改成"`openView` 调用成功之后"，重新打包（19 秒），即可拿到
   **`CANDIDATE_CLICKABLES`（含 adb 坐标）** → 直接点中入口。
2. 拿到坐标后：`adb shell input tap <adb_x> <adb_y>` → 用 `tcpdump 'port 9000 and (tcp[13]&8!=0)'` 判"是否真的发帧"（本轮已把这条判据跑通）。
3. 一旦有帧，最小回环服就会走它自己的回环（`10001→1110→10102→…`），即可开始**真机回环**验证。
4. frida 想再用的话，必须**先自证钩子有效**（例如同时 hook 必然发生的 HTTP 写），否则结论作废（本轮已踩）。

### 4.4 该怎么继续复原玩法

- **短期**：打通"列表 → 进服 → 登录"，把真机回环跑起来（下一轮就能验）。
- **中期**：真机回环跑通后，逐条把最小服的"通用零值应答"升级为**真实数据**（优先级照 `report/report_20260930_minloop.md` §四）。
- **长期**：横向系统（公会/拍卖/结婚/跨服/副本）按"最小可验证子集"逐条推进。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/_minloop_block.lua` | 探针驱动（现为 v16：读 tips + 调 `openView()`/`beginGame()`）；v14 的 UI dump + adb 坐标换算就在里面 |
| `server/dsh_minloop_probe.lua` | = `server/dsh_fake_login.lua` + 上面的块（过 `lua-check` 门禁） |
| `patched/jstm_minloop.apk` | 装机用的探针版 APK |
| `tools/minloop_frida_send.py` | frida syscall 钩子（**含"钩子有效性"警示**） |
| `server/minloop/min_loop_server.py` | 最小回环服：网关应答**对齐参考服** + 字节级日志 + POST 体积日志 |
| 设备内 `files/dsh_ui3.txt`、`dsh_pct.txt`、`dsh_gm.txt`、`dsh_login.txt`、`dsh_ml*.txt` | 客户端侧**原始**证据（全部可复查） |
| `logs/minloop/live*.log` | 服务端侧证据（含真机连接、网关 POST、字节数） |
