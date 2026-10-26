# MahatmaComeBack —— 网络层审计（协议 / 分帧 / 消息全表 / 可靠性）

> 对象：`cankao/MahatmaComeBack-master.zip` → `Classes/SocketService.{h,cpp}`（客户端）、`Server/游戏服务器/Form1.cs`（服务端）。
> 全部结论来自本次逐行阅读。标注：【已确认】/【待验证】/【未知】。
> **🔴 LICENSE = GPL-3.0 ⇒ 下面任何协议实现细节都只能作为"设计参考"，代码不得复制进 JSTM。**

---

## 一、传输层选型

| 项 | 实测值 | 标注 |
|---|---|---|
| 客户端 API | Cocos2d-x `network::WebSocket`（`#include "network/WebSocket.h"`） | 【已确认】`Classes/SocketService.h` 第 4 行 |
| 服务端 API | `SuperWebSocket.WebSocketServer`（SuperWebSocket 0.9.0.2 / SuperSocket 1.6.0.4） | 【已确认】`packages.config` + `.csproj` 引用 + `Form1.cs` 第 5 行 `using SuperWebSocket;` |
| URL 形态 | `ws://<ip>:<port>`（**明文，非 wss**） | 【已确认】`SocketService.cpp` 第 25 行 |
| 实测地址 | `Resources/Data.json` = `{"ip":"10.6.32.1","port":80}` | 【已确认】 |
| 服务端监听地址 | 由 WinForms 的 `ipText.Text` / `portText.Text` 两个输入框决定（`listenerButton_Click`） | 【已确认】 |
| Android 权限 | `android.permission.INTERNET` | 【已确认】`proj.android/app/AndroidManifest.xml` |
| 选型动机 | 作者原文：Socket.IO 与 HTTP「打包到 Android 上总是无法正常连接服务器，因此采用 WebSocket」 | 【已确认】`ReadMe.md` 第 33/37 行 |

---

## 二、分帧（framing）——★ 这是本项目最弱的环节

| 项 | 实测 | 标注 |
|---|---|---|
| 帧边界 | **完全依赖 WebSocket 自身消息边界**（一条 WebSocket text 消息 = 一条业务消息） | 【已确认】 |
| 长度前缀 | **无** | 【已确认】 |
| 消息序号 / 请求 ID | **无** | 【已确认】 |
| 消息体格式 | **纯文本 JSON**，手写字符串拼接 | 【已确认】 |
| 命令字段 | 每条消息顶层必有 `"type"`，字符串比较 | 【已确认】 |
| 心跳 / keepalive | **无** | 【已确认】 |
| 重连 / 断线重试 | **无**（`onError` 空实现，`onClose` 只打日志） | 【已确认】 |
| 压缩 / 加密 | **无**（`ws://` 明文） | 【已确认】 |
| 线程模型 | 客户端 `onMessage` 回调线程写 `receiveMessage`；游戏主线程在 `update()` 读 | 【已确认】⚠ 无锁无原子 ⇒ 数据竞争 |

**⇒ 与 JSTM 的硬冲突**：JSTM 1.4.9 客户端的线格式是 `[u32 BE len][u16 BE cmd][body]`【已验证，见 `../../README.md` 第 29 行】。
Mahatma 的"文本 JSON + type 字符串"**在分帧、命令编码、扩展性三个维度上都与 JSTM 不兼容**，且能力更弱（无长度校验、无命令号、文本体积大）。

### 2.1 客户端收发实现（逐文件）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SocketService.cpp` | `sendMessage(string str)` | `client->send(str);`（先 `log("%s", str)`） | 不适合 | 无分帧、无队列、无发送失败处理（`WebSocket::send` 返回值被丢弃） |
| `Classes/SocketService.cpp` | `onMessage(WebSocket*, const WebSocket::Data& data)` | `receiveMessage = data.bytes; ifReceviceMessage = true;` | 不适合 | 🔴 **单变量覆盖式缓冲**：两帧间隔内到达的第 2 条会**静默丢弃第 1 条** |
| `Classes/SocketService.cpp` | `getMessage()` | `return receiveMessage;`（**不检查 `ifReceviceMessage`**） | 不适合 | `ifReceviceMessage` 被赋值但**全项目从未读取** ⇒ 死字段【已确认】 |
| `Classes/SocketService.cpp` | `setMessage(string s)` | 直接覆盖 `receiveMessage`，供消费方清空 | 不适合 | 用"清空字符串"当"消费完成信号"，语义脆弱；应改为返回 `std::optional`/队列 `pop()` |
| `Classes/SocketService.cpp` | `onOpen/onClose/onError` | 前两者 `log()`，`onError` **空函数体** | 不适合 | 无错误上抛；JSTM 需要连接状态机 + 超时 + 重连退避 |
| `Classes/SocketService.cpp` | `~SocketService()` | `client->close();`（**未 `delete client`**） | 待验证 | `delteInstance()` 只 `delete socket`，`client` 疑似泄漏 |
| `Classes/SocketService.cpp` | `getInstance()/delteInstance()` | 懒加载单例 / 删除 | 待验证 | 非线程安全单例（无 `call_once`/锁），Cocos 主线程调用通常安全，但回调线程访问 `receiveMessage` 不安全 |
| `Classes/LoginScene.cpp` | `update(float delta)` | 轮询 `getMessage()`；**非空即 `setMessage("")` 清空**，之后才判断 `type` | 不适合 | 🔴 若消息 `type` 不属于当前 Scene（例如切场景瞬间到达的 `nearPlayer`），**消息被清空且未处理** ⇒ 永久丢失 |
| `Classes/GameScene.cpp` | `update(float delta)` | 同上；只处理 `nearPlayer` 与 `message`，其它 `type` 一律丢弃 | 不适合 | 同上的丢包模式 |
| `Classes/SelectPlayerScene.cpp` | `update(float delta)` | 只处理 `craetePlayerResult` / `playerInformation` | 不适合 | 同上 |
| `Classes/Tools.cpp` | `getStringFromJsonKey/getFloatFromJsonKey/getIntFromJsonKey` | 每次调用**重新 `Parse` 整条 JSON**；无 key 存在性检查 | 不适合 | 一条 `loginResult` 被解析 3~5 次；key 缺失时 `GetString()` 断言/崩溃 |

---

## 三、消息全表（★ 客户端与服务端逐条对齐）

> 「方向」C→S 表示客户端发出，S→C 表示服务端下发。
> 「触发点」= 客户端发送处 / 服务端接收分支；「下发点」= 服务端发送处 / 客户端消费处。

### 3.1 客户端 → 服务端（全部 7 条）

| # | `type` | 方向 | 字段（含引号前的原始拼写） | 触发点（客户端） | 处理分支（服务端 `manipulationData`） | 服务端行为 | 标注 |
|---|---|---|---|---|---|---|---|
| 1 | `register` | C→S | `account`(str), `password`(str) | `LoginScene::callBack` tag==5 | `type=="register"`（`Form1.cs` 172-195） | 查 `game` 账号是否存在 → 不存在则 `insert into game(account,password)` → 回 `registerResult` | 【已确认】 |
| 2 | `login` | C→S | `account`(str), `password`(str) | `LoginScene::callBack` tag==1 | `type=="login"`（196-247） | 见 `architecture.md` §2 | 【已确认】 |
| 3 | `createPlayer` | C→S | `secretKey`(str), `playerName`(str), `playerType`(int 1\|2，**发的是数字**) | `SelectPlayerScene::callBack` tag==10 | `type=="createPlayer"`（248-278） | 判重名 → `UPDATE game SET playerName,playerType,XPoint=300,YPoint=300,grade='1',blood='100',direction=1 WHERE secretKey` → 回 `craetePlayerResult` | 【已确认】 |
| 4 | `loginGameScene` | C→S | `secretKey`(str) | `SelectPlayerScene::callBack` else 分支（tag==20） | `type=="loginGameScene"`（279-306） | 7× `SELECT ... WHERE secretKey` → 回 `playerInformation` → `UPDATE game SET Online='是'` | 【已确认】 |
| 5 | `nearPlayers` | C→S | `secretKey`(str) | `GameScene::init`（第 46 行，**进场景只发一次**） | `type=="nearPlayers"`（307-330） | 读自己 7 字段组 `nearPlayer`+`state:"free"` → `GetAllLayer(secretKey, client, js)` | 【已确认】 |
| 6 | `position` | C→S | `secretKey`(str), `state`(**str**：`"walk"` \| `"free"`), `XPoint`(float, 仅 walk), `YPoint`(float, 仅 walk), `direction`(int, 仅 walk) | `GameScene::playAnimate()`（第 297 行 free / 第 307 行 walk） | `type=="position"`（331-355） | `state=="walk"`：3× `UPDATE game SET XPoint/YPoint/direction` + `SendToAllPosition(...,"walk")`；`state=="free"`：`SendToAllPosition(secretKey,0,0,0,"free")` | 【已确认】 |
| 7 | `message` | C→S | `secretKey`(str), `message`(str), `playerName`(str) | `GameScene::sendMessageCallBack` | `type=="message"`（356-363） | `SendToMessage(secretKey,name,message)` 全服广播（**不回显给自己**） | 【已确认】 |

### 3.2 服务端 → 客户端（全部 6 条）

| # | `type` | 方向 | 字段 | 下发点（服务端） | 消费点（客户端） | 客户端行为 | 标注 |
|---|---|---|---|---|---|---|---|
| 1 | `registerResult` | S→C | `reason`("true"\|"false") | `Form1.cs` 182-193 | `LoginScene::update`（181-194） | `reason=="true"` → 提示 `registerTrue`；否则 `registerFalse` | 【已确认】 |
| 2 | `loginResult` | S→C | 成功：`ifloginSuccess`("true"), `privatePassword`(str), `playerName`(str), `playerType`(str, **仅当 playerName 非空**)<br>失败：`ifloginSuccess`("false"), `reason`(`"NoAccount"`\|`"PasswordError"`) | `Form1.cs` 207-246 | `LoginScene::update`（196-233） | 成功 → `setPrivatePassword` + `setAccount`；`playerName==""` → `SelectPlayerScene::createScene(1)`，否则 `setPlayerType` + `createScene(2)`。失败 → 按 `reason` 弹 `NoAccount`/`PasswordError` | 【已确认】 |
| 3 | `craetePlayerResult` | S→C | `ifSuccess`("true"\|"false"), `playerType`(str, 仅成功) | `Form1.cs` 262-276 | `SelectPlayerScene::update`（194-211） | 成功 → `setPlayerType` + `selectPlayerLayer()`；失败 → 弹 `playerNameError` | 【已确认】★ 服务端与客户端**同时把 `create` 拼错为 `craete`** |
| 4 | `playerInformation` | S→C | `playerName`(str), `playerType`(str), `XPoint`(float), `YPoint`(float), `grade`(int), `blood`(float), `direction`(int) | `Form1.cs` 291-300 | `SelectPlayerScene::update`（212-215） | `Director::replaceScene(GameScene::createScene(str))`（**整条 JSON 透传**） | 【已确认】 |
| 5 | `nearPlayer` | S→C | `playerName`(str), `playerType`(str), `XPoint`(float), `YPoint`(float), `grade`(int), `blood`(float), `direction`(int), `state`(str：`"free"`\|`"walk"`\|`"remove"`) | ①`SendToAllPosition`（374-410）②`GetAllLayer`（416-453）③`ws_SessionClosed` 里以 `"remove"` 下发 | `GameScene::update`（355-405） | 按名字在 `nearplayers` 找：`"remove"`→删除；`"free"`→`freeAction()`；否则 `setDirection`+`walkAction()`+`MoveTo(0.4, (x,y))`；找不到则 `Player::createWithjson(str)` 新建 | 【已确认】 |
| 6 | `message` | S→C | `playerName`(str), `message`(str) | ①`SendToMessage`（101-118）②`button1_Click` 公告（474-492，`playerName="公告"`） | `GameScene::update`（407-412） | `Tools::showMessageToListView(listview, name, message)` | 【已确认】 |

### 3.3 无消息覆盖的能力（对照式缺口）

| 能力 | Mahatma | 说明 | 标注 |
|---|---|---|---|
| 服务端主动校验位置 | ❌ | 无 `VerifyPos` 类消息；服务端全盘接受上报坐标 | 【已确认】 |
| 服务端主动踢人/顶号 | ❌ | 同一账号重复登录：`dic.Add(client, pas)` 会**抛 `ArgumentException`**（重复 key 检测的是 session 不是 key，所以实际不抛）——但 DB 里 `secretKey` 被**后者覆盖** ⇒ 前者所有后续请求 `WHERE secretKey=旧值` 查不到 → `Rows[0]` 抛 `IndexOutOfRangeException` | 【待验证】 |
| 同账号多开限制 | ❌ | `Online` 字段有写但**从未被查询**（grep `Online` 只出现在两处 `UPDATE`） | 【已确认】 |
| 心跳/在线超时 | ❌ | 依赖 WebSocket 关闭事件 | 【已确认】 |
| 错误码体系 | ❌ | 只有 `reason` 三个字符串字面量（`"true"/"false"` 复用于布尔；`"NoAccount"/"PasswordError"`） | 【已确认】 |
| 请求/响应关联 | ❌ | 无 ID，靠"下一条到达的消息"匹配；同一场景同时发起两个请求即错配 | 【已确认】 |
| 消息分片/大包 | ❌ | 聊天 `message` 无长度上限（`EditBox::setMaxLength(15)` 只在客户端） | 待验证 |
| 频道（世界/私聊/队伍/公会） | ❌ | 只有一条全服 `message` | 【已确认】 |
| 物品/技能/任务/战斗消息 | ❌ | `manipulationData` 只有 7 个分支 | 【已确认】 |

---

## 四、可靠性缺陷清单（每条可指回代码）

| # | 缺陷 | 代码证据 | 后果 | 标注 |
|---|---|---|---|---|
| 1 | 单变量消息缓冲 | `SocketService::onMessage` → `receiveMessage = data.bytes;` | 同帧两消息丢一 | 【已确认】 |
| 2 | 每帧只消费一条 | `LoginScene/SelectPlayerScene/GameScene` 的 `update()` 里 `if (str != "") { ... }`（无 while） | 高延迟下消息积压在服务端/浏览器缓冲区 | 【已确认】 |
| 3 | 先清空后判类型 | `SocketService::getInstance()->setMessage("");` 在 `type` 判断之前 | 不认识的 `type` 被静默丢弃（切场景窗口期） | 【已确认】 |
| 4 | `Tools::getXxxFromJsonKey` 无 key 存在性检查 | `doc[key.c_str()].GetString()` / `GetInt()` | 服务端少发一个字段即崩客户端（例：`loginResult` 失败分支**不含 `playerName`**，而成功分支才含；客户端只在成功分支取，侥幸不崩） | 【已确认】 |
| 5 | `onError` 空实现 | `SocketService::onError` 函数体为空 | 网络错误无感知、无重连 | 【已确认】 |
| 6 | 无发送失败处理 | `client->send(str)` 返回值丢弃 | 发送失败无感知 | 【已确认】 |
| 7 | 服务端广播无 AOI | `SendToAllPosition` / `SendToMessage` 遍历 `server.GetAllSessions()` | O(在线人数) 广播；**1000 人时每人每次移动触发 999 条消息** | 【已确认】 |
| 8 | 广播中内联 SQL | `SendToAllPosition` 循环体内 `DbConnectionMySQL.GetDataSet(... "select * from game where secretKey=...")` | O(在线人数) 次 DB 查询/每次移动 | 【已确认】 |
| 9 | 服务端遍历中未防御 `dic` 缺 key | `var key = dic[sendSession];`（`SendToAllPosition` / `SendToMessage` / `GetAllLayer`） | 未登录的 session 触发 `KeyNotFoundException`；只有 `GetAllLayer`/`SendToAllPosition` 的 `try` 捕获了 `IndexOutOfRangeException` | 【已确认】 |
| 10 | `dic` 只增不减（正常路径） | `dic.Remove(session)` 仅在 `catch(KeyNotFoundException)` 分支内 | 内存中 session→key 累积 | 【已确认】 |
| 11 | 无并发保护 | `Form1_Load` 里 `Control.CheckForIllegalCrossThreadCalls = false;`；`dic` 是普通 `Dictionary` | SuperWebSocket 回调线程 + UI 线程同时读写 | 【已确认】 |
| 12 | 明文传输 | `ws://`，`Data.json` 用 HTTP 端口 80 | 密码/密钥可被抓包 | 【已确认】 |
| 13 | 密码明文入库 | `selectMysqlPassword` 直接 `==` 比较；DB 列 `password varchar(32)` | 拖库即全泄露 | 【已确认】 |
| 14 | SQL 注入 | 例：`"select * from game where account=" + account`（**连引号都没有**，`account` 直接拼进 SQL）；`"select * from game where account='" + account + "'"` 亦为字符串拼接 | 任意 SQL 注入 | 【已确认】 |
| 15 | 密钥含秒级时间且无过期 | `encryptionPassword(pas + DateTime.Now.ToLongTimeString(), "thisisapassword")` | 同一秒内同密码可预测；key 永不过期 | 【已确认】 |
| 16 | 每次消息刷 UI 全表 | `showData()` → `select * from game` + `dataGridView1.DataSource = ...` | 登录/建号/进游戏后全表查询并重绑 DataGridView | 【已确认】 |

---

## 五、状态机（`state` 字段）

| `state` 值 | 谁发 | 含义 | 服务端处理 | 客户端处理 | 标注 |
|---|---|---|---|---|---|
| `"walk"` | 客户端（`position`） | 正在走向下一格 | 3× UPDATE + `SendToAllPosition(...,"walk")` | 接收方：`setDirection` + `walkAction` + `MoveTo(0.4s, (x,y))` | 【已确认】 |
| `"free"` | 客户端（`position`） | 已停下 | `SendToAllPosition(secretKey, 0.0f, 0.0f, 0, "free")` ← **坐标被强制为 0,0** | 接收方：`freeAction()`（**不使用坐标**，所以 0,0 不产生可见错误） | 【已确认】 |
| `"remove"` | **仅服务端**（`ws_SessionClosed`） | 玩家下线 | 下发 `XPoint=0,YPoint=0,direction=0` | 接收方：`removeFromParentAndCleanup(true)` + 从 `nearplayers` 移除 | 【已确认】 |
| 其它 | — | **未定义** | `else` 不存在（`state=="walk"` / `else if state=="free"`），其它值**什么都不做** | `if (nearState == "free") ... else ...` ⇒ 未知值被当作"走路"处理 | 【待验证】 |

---

## 六、与 JSTM 协议层的映射建议（仅设计，不抄代码）

| Mahatma 概念 | JSTM 对应 | 建议 |
|---|---|---|
| `type` 字符串 | `u16 cmd` | **必须换成命令号**；JSTM 已有 `cmd_resolve_*.luac` 定义 |
| 文本 JSON body | 二进制 body | JSTM 已有既定结构，不要引入 JSON |
| `secretKey`（登录票据） | 会话 token | 保留"登录发票据、后续用票据"的思路；但需 `expireAt` + 随机化 + 独立会话表 |
| `state:"walk"/"free"/"remove"` | 移动同步命令 | 可参考其"三态（走/停/离线）"抽象；JSTM 实际命令以 APK 为准 |
| `nearPlayer`（一条消息含全部远端角色字段） | AOI 增量同步 | 参考其"字段集合"（name/type/x/y/grade/blood/direction/state），但**必须加 AOI** |
| 无位置校验 | 需新增 | JSTM 应至少做"距离/时间"软校验（ChivalrousMan 的 `M_VerifyPos` 可作参考，见 `../chivalrousman/architecture.md`） |

---

## 七、未读到 / 待验证

| 项 | 状态 |
|---|---|
| WebSocket 握手细节（子协议、Origin 校验） | 【未读到】`SuperWebSocket` 库内部，源码未包含在 ZIP 中 |
| 是否存在 `wss` 支持 | 【未读到】`SocketService.cpp` 只构造 `ws://` |
| 消息体大小上限 | 【未知】 |
| `client->send()` 在 WebSocket 未就绪时的行为 | 【未知】未读到 Cocos 库实现 |
| 同一账号二次登录的具体崩溃路径 | 【待验证】仅从 `dic`/`secretKey` 覆盖推断 |
| 长时间无消息时 WebSocket 是否被中间设备断开 | 【未知】 |
