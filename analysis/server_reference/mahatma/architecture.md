# MahatmaComeBack（大圣归来）架构审计 —— 7 问逐条回答

> **审计对象**：`C:\Users\xu\Desktop\DSH\cankao\MahatmaComeBack-master.zip`（18.2 MB，ZIP 条目 **164 = 136 个文件 + 28 个目录**）
> **实测方法**：Python `zipfile.namelist()` 列全部条目 → 逐个 `read()` 读源码（GBK→UTF-8 转换后阅读）。
> **未改动 `cankao/` 下任何文件**（解压副本读于系统 TEMP）。
> **🔴 LICENSE = GNU GPL v3（`MahatmaComeBack-master/LICENSE` 首行实测）⇒ 代码绝对不能复制进 JSTM。** 详见 `reuse_candidates.md`。
>
> **标注口径**：【已确认】= 本次亲自读到该行代码；【待验证】= 由命名/资源推断但未读到实现；【未知】= 未读到。
> 本报告**不把推断写成已确认**。
>
> ⚠ **R2 计数更正**：早期文档（本目录以外的 `README.md` / `license_audit.md` / `FINAL_SERVER_ARCHITECTURE.md`）沿用了
> 「164 文件」「`Server/游戏服务器`(17)」两个数字。本次逐条目实测后更正为：
> **文件数 136**（164 是含目录的条目数）、**`Server/游戏服务器/` 为 15 个文件**（`Server/` 下合计 19 个文件）。

---

## 〇、项目构成（实测，逐条目计数）

| 层 | 路径 | 文件数 | 技术栈 |
|---|---|---|---|
| 客户端 | `Classes/` | **18**（9 组 .h/.cpp） | Cocos2d-x 3.17.2 + C++（WebSocket + rapidjson） |
| 客户端资源 | `Resources/` | **54** | `map.tmx`、`Data.json`、`text.xml`、`Layer.csb`、plist 图集、`han.ttf`(21 MB) |
| 客户端工程（Android） | `proj.android/` | **24** | Android Gradle + NDK（`Android.mk`/`Application.mk`）、keystore |
| 客户端工程（Win32） | `proj.win32/` | **11** | VS `.sln`/`.vcxproj`/`.filters`/`.user`、`main.cpp`、`game.ico` |
| **服务端** | `Server/游戏服务器/` | **15** | **C# / .NET Framework 4.5.2 / WinForms** |
| 服务端工程/脚本 | `Server/`（根） | **4** | `游戏服务器.sln`、`gametable.sql`、`.gitattributes`、`.gitignore` |
| 打包脚本 | 根目录 `*.bat` | **5** | build/run × Android/Win32 × Debug/Release |
| 根目录其它 | — | **5** | `.cocos-project.json`、`.gitignore`、`CMakeLists.txt`、`LICENSE`、`ReadMe.md` |
| **合计** | — | **136** | （+ 28 个目录 = 164 条目） |

**服务端依赖（`Server/游戏服务器/packages.config` 【已确认】）**：
`log4net 2.0.3`、`Newtonsoft.Json 5.0.8`、`SuperWebSocket 0.9.0.2`（+ 硬编码引用 `..\MySql.Data.dll`）。

**`Server/游戏服务器/` 下的全部 15 个文件（【已确认】，逐条目实测）**：
`.gitignore`、`App.config`、`packages.config`、`游戏服务器.csproj`、
`Program.cs`、`Form1.cs`、`Form1.Designer.cs`、`Form1.resx`、
`DbConnectionMySQL.cs`、`LoginEncryption.cs`、
`Properties/AssemblyInfo.cs`、`Properties/Resources.Designer.cs`、`Properties/Resources.resx`、
`Properties/Settings.Designer.cs`、`Properties/Settings.settings`。
**另在 `Server/` 根有 4 个文件**：`游戏服务器.sln`、`gametable.sql`、`.gitattributes`、`.gitignore`（合计 19）。

> **说明**：早期 R1 层文档写「`Server/游戏服务器`（17 文件）」是把 `Properties/` 下 4 个 + 根级若干重复计入所致；
> **本轮以逐条目清单为准：15**。该更正已同步写入 `../license_audit.md`。

**★ 结构上的关键事实**：服务端**没有任何** `Server/`/`Network/`/`Model/`/`Handler/` 目录，也没有接口/抽象类。
网络、业务、SQL、UI 全部塞在**一个 WinForms Form 文件 `Form1.cs`（497 行）**里【已确认】。

---

## 一、Cocos 客户端如何连接服务器？

### 1.1 结论

**WebSocket（`ws://`）+ 纯文本 JSON 单帧消息，客户端主动连接，服务器地址从 `Resources/Data.json` 读取。**
不是 HTTP 短连接，不是 Socket.IO，不是自定义二进制协议。

### 1.2 逐文件证据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SocketService.h` | `class SocketService : public network::WebSocket::Delegate` | 网络层单例声明；成员 `WebSocket* client`、`string receiveMessage`、`bool ifReceviceMessage`、`privatePassword`、`playerType`、`account` | **不适合（照抄）** | 单条消息缓冲 + 无队列，必然丢包；但"把连接信息与身份凭证集中到一个单例"的思路 JSTM 可参考。🔴 **GPL-3.0，代码不可复制** |
| `Classes/SocketService.cpp` | `SocketService::initSocket()` | `FileUtils::getInstance()->getStringFromFile("Data.json")` → `rapidjson::Document::Parse` → 取 `doc["ip"]`/`doc["port"]` → `String::createWithFormat("ws://%s:%d", ip, port)` → `new WebSocket()` + `client->init(*this, str)` | **适合（协议选型）** | 用**外部 JSON 配置**驱动服务器地址，不硬编码；JSTM 可直接采用"配置文件驱动"这一点（不复制代码） |
| `Classes/SocketService.cpp` | `SocketService::sendMessage(string)` | `client->send(str)`，**无长度前缀、无分包、无序列号** | 不适合 | 单帧文本假设；JSTM 的线格式是 `[u32 BE len][u16 BE cmd][body]`，必须自研 |
| `Classes/SocketService.cpp` | `SocketService::onMessage(ws, data)` | `receiveMessage = data.bytes; ifReceviceMessage = true;` | 不适合 | **后到消息直接覆盖前一条**，无队列；且 `ifReceviceMessage` 被赋值但**从未被读取**（`getMessage()` 不检查它）⇒ 死标志 |
| `Classes/SocketService.cpp` | `SocketService::onOpen/onClose/onError` | 仅 `log()` 打印；`onError` 是**空函数体** | 不适合 | 无重连、无超时、无错误上报；JSTM 必须补 |
| `Classes/SocketService.cpp` | `SocketService::getInstance()/delteInstance()` | 懒汉式单例，`socket == NULL` 时 `new`；`delteInstance()` 里 `delete socket; socket=NULL;`（析构函数 `client->close()`） | 待验证 | 非线程安全；JSTM 若多线程收发需另设计 |
| `Classes/LoginScene.cpp` | `LoginScene::callBack()` tag==2（确定登陆服务器按钮） | `SocketService::getInstance()->initSocket();` —— **连接动作在 UI 回调里发起** | 不适合 | 网络连接与 UI 强耦合；建议 JSTM 用独立 NetManager + 状态机 |
| `Classes/LoginScene.cpp` | `LoginScene::callBack()` tag==3（返回服务器列表） | `SocketService::getInstance()->delteInstance();` —— 断开即释放单例 | 待验证 | 反复进出可能留下悬垂指针（`client` 未 delete） |
| `Resources/Data.json` | — | `{"ip":"10.6.32.1","port":80}` | 适合（设计） | 证明"服务器列表 = 一个 ip/port 文件"，JSTM 可扩展为多区服列表 |
| `proj.android/app/AndroidManifest.xml` | `<uses-permission android:name="android.permission.INTERNET"/>` | Android 联网权限 | 适合 | 事实性配置 |

### 1.3 消息模型

| 环节 | 机制 | 状态 |
|---|---|---|
| 编码 | 手写 `String::createWithFormat("{\"type\":\"login\",\"account\":\"%s\",\"password\":\"%s\"}", ...)` | 【已确认】 |
| 字段约定 | **每条消息顶层必须有 `"type"`**，服务器/客户端都靠它分发 | 【已确认】 |
| 接收 | 各 Scene 在 `update(float)` 里**轮询** `SocketService::getInstance()->getMessage()` | 【已确认】 |
| 清空 | 读取后立即 `setMessage("")` | 【已确认】 |
| 每帧最多处理 | **1 条**（`if (str != "")` 只处理一次，无 while） | 【已确认】 |

**⇒ 架构缺陷（【已确认】）**：无消息队列 ⇒ 同一帧内到达两条消息时**后者覆盖前者**，客户端静默丢消息。
JSTM 的 1.4.9 客户端协议已有 `[len][cmd]` 分帧，**不应模仿此模型**。

### 1.4 为什么选 WebSocket（作者自述，`ReadMe.md` 第 33/37 行）【已确认】

> 「Cocos 封装的 Socket.IO 与 HTTP 在电脑上可以正常连接服务器，但是**打包到 Android 上总是无法正常连接服务器**，因此采用 WebSocket」
> 「服务器端我用的 Node.js 开发的（我开发的不是这个项目），这个项目是我们张红银学长做的…**他服务器端用的 C# 开发的**」

⇒ 服务端 `SuperWebSocket` 与客户端 Cocos `network::WebSocket` 是**为绕开 Android 上 Socket.IO/HTTP 失败**而选的方案。

---

## 二、登录流程是什么？

### 2.1 完整时序（【已确认】，两侧代码逐行对齐）

```
[客户端] LoadingScene  →  LoginScene::createScene()
[客户端] LoginScene::init() 建三层：SelectServiceLayer / loginLayer / registerLayer
         （三层都 addChild 在屏幕外，用 MoveBy(0.3s, (0,-size.height)) 上下滑动切换）
   ↓ 点"确定登陆服务器"(tag==2)
[客户端] SocketService::initSocket()  →  ws://<Data.json.ip>:<port>
   ↓ 输入账号密码（EditBox tag 101/102 或 103/104）
   ↓ 点"登录"(tag==1)
[客户端] sendMessage({"type":"login","account":"A","password":"P"})
   ↓
[服务端] Form1.ws_NewMessageReceived(session, value)
         → JObject.Parse(value) → type = json["type"] → manipulationData(type, json, session)
[服务端] type=="login" 分支：
         pas = selectMysqlPassword(account)
            = select * from game where account=A   → Rows[0]["password"]
         ├─ pas == ""        → 回 {"type":"loginResult","ifloginSuccess":"false","reason":"NoAccount"}
         ├─ pas == password  → pas = LoginEncryption.encryptionPassword(pas + DateTime.Now.ToLongTimeString(),
                                                                        "thisisapassword")
         │                     回 {"type":"loginResult","ifloginSuccess":"true",
         │                          "privatePassword":<pas>, "playerName":<名>,
         │                          "playerType":<类型>（仅当 playerName != ""）}
         │                     dic.Add(client, pas)                       ← 内存 session→秘钥 映射
         │                     update game set secretkey='<pas>' where account=A
         └─ 其它            → 回 {"type":"loginResult","ifloginSuccess":"false","reason":"PasswordError"}
   ↓
[客户端] LoginScene::update(delta) 轮询 getMessage()
         messagetype == "loginResult"
           → setPrivatePassword(privatePass)   ← ★ 之后所有请求的身份凭证
           → setAccount(accountStr)
           → playerName == ""  ? SelectPlayerScene::createScene(1)  （去建号）
                               : setPlayerType(...) + SelectPlayerScene::createScene(2)（去选角）
```

### 2.2 逐文件证据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/LoginScene.cpp` | `initSelectServiceLayer()` / `initLoginLayer()` / `initRegisterLayer()` | 三层 `Layer` 全建好叠放，靠 `MoveBy` 动画切换；登录/注册**共用同一组 EditBox tag 101-104** | 不适合 | 注册层与登录层**复用同一 `accountEdit`/`passwordEdit` 指针**（第 137/149 行 `accountEdit = EditBox::create(...)` 覆盖成员），属隐患；JSTM 用独立 UI 栈 |
| `Classes/LoginScene.cpp` | `update(float delta)` | 轮询消息；`registerResult`→提示；`loginResult`→按 `ifloginSuccess` 与 `reason`（`NoAccount`/`PasswordError`）分流 | 适合（业务语义） | **登录结果枚举只有 3 态**（成功/账号不存在/密码错误），JSTM 1.4.9 需要更多错误码 —— 可作最简基线 |
| `Classes/LoginScene.cpp` | `callBack()` tag==1 | 拼 JSON 发 `login`；空账号/密码时弹 `isempty` 但**不 return**（仍会发消息） | 不适合 | 校验后未提前返回 = bug；JSTM 不要照搬 |
| `Server/游戏服务器/Form1.cs` | `manipulationData(type, json, client)` 的 `type=="login"` 分支 | 三条分支：查库 → 比对明文密码 → DES 加密生成 secretKey → 回 JSON → 写内存 dict → 写库 | **不适合（结构）** | 密码**明文比对**（DB 存明文）；secretKey 拼接了 `ToLongTimeString()`（秒级）⇒ 同秒登录可能撞 key；`where account=" + account` **缺引号**且字符串拼 SQL |
| `Server/游戏服务器/LoginEncryption.cs` | `LoginEncryption.encryptionPassword(encryptString, encryptKey)` | `DESCryptoServiceProvider`；`rgbKey = UTF8(encryptKey.Substring(0,8))`，`rgbIV` **等于同一个 key**；`Base64` 输出；`catch` 时**原样返回明文** | 不适合 | DES/ECB 式固定 key+IV，且失败降级为明文 ⇒ 等于没有加密；JSTM 必须换用 HMAC/token |
| `Server/游戏服务器/Form1.cs` | `selectMysqlPassword(string account)` | `select * from game where account=A` → `Rows[0]["password"]`，无行则 `""` | 不适合 | 明文密码列、无哈希、无盐、无失败次数限制、无验证码、无会话超时 |
| `Server/游戏服务器/Form1.cs` | `dic`（`Dictionary<WebSocketSession,string>`） | 会话 → secretKey 内存映射；`dic.Add(client, pas)` | 待验证 | **非线程安全**（SuperWebSocket 回调线程 + WinForms 主线程共用）；`SessionClosed` 里 `dic.Remove` 只在 KeyNotFound 分支执行 |
| `Resources/text.xml` | `NoAccount` / `PasswordError` / `isempty` / `registerTrue` / `registerFalse` | 客户端提示文案字典（`Dictionary::createWithContentsOfFile`） | 适合（做法） | 文案外置为 plist-dict，JSTM 可沿用"文案与代码分离" |
| `Server/游戏服务器/Form1.cs` | `type=="register"` 分支 | `select * from game where account=A` 判存在 → `insert into game(account,password)` → 回 `{"type":"registerResult","reason":"true"/"false"}` | 不适合 | 只查重账号，**不校验长度/字符/密码强度**；`reason` 用字符串 `"true"/"false"` 而非 bool，类型不一致 |

### 2.3 注册流程（与登录并列的入口）

```
[客户端] LoginScene tag==6 → 滑到注册层
[客户端] tag==5（立即注册）→ sendMessage({"type":"register","account":"A","password":"P"})
[服务端] manipulationData type=="register"：
         select count where account=A
           == 0 → insert into game(account,password) values(A,P)  ; 回 registerResult/reason=true
           != 0 → 回 registerResult/reason=false
[客户端] update() → registerTrue: "注册成功，请返回登录界面" / registerFalse: "注册失败，账号已存在"
```

> ⚠ **注册消息里没有验证码、没有邮箱、没有密码二次确认**（对比 ChivalrousMan 有 `SurePasswd` 二次输入）。

---

## 三、角色数据如何进入数据库？

### 3.1 结论

**角色数据没有独立的"角色表"。账号与角色同处 `game` 表的同一行**；建号的动作本质是一条 `UPDATE`，
把 `playerName/PlayerType/XPoint/YPoint/grade/blood/direction` 写进**该账号已有的那一行**。
之后位置变化（走路）由 `position` 消息触发**逐字段 UPDATE 落库**。

### 3.2 逐文件证据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SelectPlayerScene.cpp` | `callBack()` tag==10 | `{"type":"createPlayer","secretKey":"<privatePassword>","playerName":"N","playerType":1\|2}` | 适合（协议思路） | 用登录下发的 **secretKey 而非账号名**作凭证 —— 这个"登录票据"思路 JSTM 应保留（但要换成不可预测 token） |
| `Server/游戏服务器/Form1.cs` | `type=="createPlayer"` 分支 | ①`select * from game where playerName='N'` 判重名；②`update game set playerName='N',playerType='T',XPoint=300.0,YPoint=300.0,grade='1',blood='100',direction=1 where secretKey='<key>'`；③回 `{"type":"craetePlayerResult","ifSuccess":"true","playerType":"T"}` | **不适合（表设计）** | **一个账号只能有一个角色**（账号即主键，无 roleId）；出生点硬编码 300,300；初始属性硬编码 grade=1/blood=100；**无事务包裹** |
| `Server/游戏服务器/Form1.cs` | 同上（重名分支） | 回 `ifSuccess=false` | 不适合 | 只有"重名"一种失败原因，无非法字符/长度/敏感词校验，且**判重与插入之间无锁**（并发可重名） |
| `Classes/SelectPlayerScene.cpp` | `update(float)` | 收 `craetePlayerResult` → `setPlayerType(playerType)` + `selectPlayerLayer()`（切到选角界面） | 待验证 | 直接进游戏前的过渡；注意服务端把字段拼成 `craetePlayerResult`（**拼写错误 `craete`**），客户端也照拼 ⇒ 不可改的兼容点 |
| `Classes/SelectPlayerScene.cpp` | `editBoxTextChanged(editBox, text)` | `name = text;` | 不适合 | 角色名 **只在客户端 `setMaxLength(10)`**，服务端不校验长度 ⇒ 依赖客户端，不安全 |
| `Classes/SelectPlayerScene.cpp` | `callBack()`（else 分支，tag==20） | `{"type":"loginGameScene","secretKey":"<key>"}` | 适合 | 进游戏用独立消息，职责清晰 |
| `Server/游戏服务器/Form1.cs` | `type=="loginGameScene"` | 读 7 个字段 → 发 `playerInformation` → `update game set Online='是' where secretKey=...` → `showData()`（刷新 DataGridView） | 不适合 | "在线标记"与角色加载耦合在同一分支；`showData()` 每次消息都 `select * from game` 全表刷 UI ⇒ 性能隐患 |
| `Server/游戏服务器/Form1.cs` | `type=="position"`，`state=="walk"` | **三条独立 UPDATE**：`set XPoint=` / `set YPoint=` / `set direction=`，然后 `SendToAllPosition(...)` | 不适合 | 无事务、无批量；**每次移动都写库**（每 0.4 秒一格 = 每格一次 DB 往返）；JSTM 必须改为**定时批量落库/离线下线落库** |
| `Server/游戏服务器/Form1.cs` | `ws_SessionClosed(session, value)` | `update game set Online='否' where secretKey=...` + `SendToAllPosition(secretKey,0,0,0,"remove")` | 待验证 | 依赖 `dic[session]` 存在；只在 `KeyNotFoundException` 分支里 `dic.Remove` |
| `Classes/GameScene.cpp` | `playAnimate()` | 每走完一格发 `{"type":"position","secretKey":...,"state":"walk","XPoint":x,"YPoint":y,"direction":d}` | 不适合 | **客户端上报即权威**（服务端不校验可达性）⇒ 可瞬移/穿墙作弊 |
| `Classes/GameScene.cpp` | `playAnimate()`（`closeSteps.size()==0` 分支） | 发 `{"type":"position",...,"state":"free"}` | 适合 | 用 `state` 显式表达"停/走"两态，语义简单 |

### 3.3 落库触发点汇总

| 触发 | SQL | 状态 |
|---|---|---|
| 注册 | `insert into game(account,password) values(...)` | 【已确认】 |
| 登录成功 | `update game set secretkey='<pas>' where account=A` | 【已确认】 |
| 建号 | `update game set playerName,playerType,XPoint=300,YPoint=300,grade=1,blood=100,direction=1 where secretKey` | 【已确认】 |
| 进游戏 | `update game set Online='是' where secretKey` | 【已确认】 |
| 每走一格 | `update game set XPoint=... / YPoint=... / direction=... where secretKey`（3 条） | 【已确认】 |
| 断线 | `update game set Online='否' where secretKey` | 【已确认】 |

**⇒ 【已确认】没有任何"角色变更事务"概念**：`DbConnectionMySQL` 提供了 `ExecuteNonQuery(MySqlTransaction, ...)` 重载（第 65 行），
但 `Form1.cs` 里**没有一处传入 transaction**（全部传 `null`）。

---

## 四、服务器如何加载角色？

### 4.1 结论

**"加载"= 在收到 `loginGameScene` 时，用 secretKey 从 `game` 表逐字段 `SELECT`，拼成一条
`playerInformation` JSON 整包下发给客户端。服务端不建立任何内存角色对象，也不缓存。**
客户端把这条 JSON **原样透传**给 `GameScene`。

### 4.2 时序

```
[客户端] SelectPlayerScene tag==20 → {"type":"loginGameScene","secretKey":"<key>"}
   ↓
[服务端] type=="loginGameScene"（Form1.cs 第 279-306 行）
   对 7 个字段各跑一次：select * from game where secretKey='<key>'
        playerName / PlayerType / XPoint / YPoint / grade / blood / direction
   （★ 第 283-289 行是 7 条几乎相同的独立 SELECT，未合并为一条）
   → JObject js: type=playerInformation, playerName, playerType,
                 XPoint(float.Parse), YPoint(float.Parse), grade(int.Parse),
                 blood(float.Parse), direction(int.Parse)
   → client.Send(js.ToString())
   → update game set Online='是'
   → showData()
   ↓
[客户端] SelectPlayerScene::update()  messagetype=="playerInformation"
   → Director::replaceScene(GameScene::createScene(str))     ★ 整条 JSON 字符串当参数传
   ↓
[客户端] GameScene::init(string json)
   → TMXTiledMap::create("map.tmx")
   → Player::createWithjson(json) → Player::initWithJson(json)
        取 playerName / playerType / XPoint / YPoint / grade / blood / direction
   → sendMessage({"type":"nearPlayers","secretKey":"<key>"})   ★ 主动拉周围玩家
   → CSLoader::createNode("Layer.csb") 聊天窗口
   → EventListenerTouchOneByOne onTouchEnded → moveTowardPoint(...)
```

### 4.3 逐文件证据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Server/游戏服务器/Form1.cs` | `type=="loginGameScene"` | 7 条独立 SELECT + `float.Parse`/`int.Parse` → 单条 `playerInformation` JSON | 不适合 | ①7 次 DB 往返（应 1 次）②用 `Parse` 解析 DB 文本，DB 为 NULL 时**直接抛异常**（结果值全部是 `varchar`）③无 roleId/无装备/无背包/无技能字段 |
| `Classes/SelectPlayerScene.cpp` | `update(float)` | 收到 `playerInformation` 就 `replaceScene(GameScene::createScene(str))` | 不适合 | 把"解析"推迟到下一场景，JSON 字符串在场景间穿行；JSTM 应先在网络层解析为强类型 DTO |
| `Classes/Player.cpp` | `Player::initWithJson(string json)` | 逐字段 `Tools::getStringFromJsonKey`/`getFloatFromJsonKey`/`getIntFromJsonKey`；按 `playerType=="1"/"2"` 选动画前缀（`nas/nza/nz` 与 `qks/qka/qk`）；`setScale(1.5)`；`setPosition(Xpoint,Ypoint)`；加 `nameLabel` | 适合（做法） | **"服务端下发数据 → 同一个人物类两种构造（`init(type)` 用于建号预览 / `initWithJson(json)` 用于进游戏）"** 是可借鉴的复用手法 |
| `Classes/Player.cpp` | `Player::init(int type)` | 建号预览用：type 1→`nas/nza/nz`，type 2→`qks/qka/qk`，`grade=1`，`setScale(5)` | 待验证 | scale 5（预览）vs 1.5（游戏内）是硬编码视觉差异 |
| `Classes/Player.h` | `enum class state { FREE, WALK, ATTACK, DEAD }` | 角色状态枚举（`ATTACK`/`DEAD` **只有枚举，没有调用点**） | 适合（设计） | 状态机骨架可借鉴；但要补状态迁移表 |
| `Classes/Player.h` | 成员 `playername/playerType/Xpoint/Ypoint/grade/blood` | 客户端持有角色字段但**没有 maxBlood/mana/exp/gold** | 不适合 | 数据模型过薄；JSTM 1.4.9 角色属性多得多 |
| `Server/游戏服务器/Form1.cs` | `GetAllLayer(secretKey, client, json)` | 遍历 `server.GetAllSessions()`，对每个 `dic[session] != secretKey` 的会话：从 DB 读它 7 个字段 → 组 `js`（对方信息）→ `sendSession.Send(json.ToString())`（把**新玩家自己**的信息发给对方）+ `client.Send(js.ToString())`（把对方信息给新玩家） | 待验证 | 全服遍历、每会话再 7 次 SELECT ⇒ O(N×7) DB 查询；且**无 AOI/无分线**。若 `dic[sendSession]` 不存在会抛 `KeyNotFoundException`（只 catch 了 `IndexOutOfRangeException`） |
| `Classes/GameScene.cpp` | `update(float)` 的 `nearPlayer` 分支 | 遍历 `nearplayers` 找同名 → 更新；**但 `return;` 写在 for 循环体内、`if` 之外（第 391 行）⇒ 第一次迭代必然 return** | 不适合 | 🔴 **实测 bug**：只要 `nearplayers` 非空，新玩家**永远不会被创建**，老玩家也只在 i==0 时可能被更新 |
| `Classes/GameScene.cpp` | `update(float)` 的 `nearPlayer`/`remove` 分支 | `nearState=="remove"` → `removeFromParentAndCleanup(true)` + `nearplayers.eraseObject` | 适合 | "下线用一条 `state=remove` 广播"是简洁做法 |
| `Server/游戏服务器/Form1.cs` | `SendToAllPosition(secretKey,x,y,direction,playerState)` | 遍历所有 session，`key != secretKey` 时从 DB 读自己 4 字段 → 发 `nearPlayer` + 给定坐标 + `state` | 不适合 | **全服广播**（无 AOI、无地图分区、无距离判定）；每次广播再查 DB |

**⇒ 【已确认】服务端没有内存角色缓存/无 Entity 层**：`Form1` 里除了 `dic`（session→key）之外没有任何角色容器；
每次广播都回 DB 查。这是本项目最不适合 JSTM 的一点（JSTM 需要地图内在线角色缓存 + AOI）。

---

## 五、自动寻路如何与地图/服务器交互？

### 5.1 结论

**寻路 100% 在客户端本地完成（A\* + TMX 碰撞层），服务器完全不知道路径。
服务器只在每个格子走完后收到一条 `position` 消息，写库 + 全服广播。没有任何位置校验、没有反外挂。**

### 5.2 地图结构（`Resources/map.tmx`【已确认】—— 已 base64+zlib 解码逐层核对）

| 项 | 值 |
|---|---|
| map | `width=26 height=20 tilewidth=64 tileheight=64 orientation=orthogonal renderorder=right-down` ⇒ **520 格**，世界尺寸 **1664×1280 px** |
| tileset 1 | `firstgid=1` `fight`（`fight.png` 1680×1280，tilecount 520，columns 26） |
| tileset 2 | `firstgid=521` `map2`（`map.png` 1664×1280，tilecount 520，columns 26） |
| tileset 3 | `firstgid=1041` `collidablesTileSet`（`collidablesTileSet.png` 192×64，tilecount **3**） |
| 图层（**7 个，每个恰好 520 格**） | `Background`（520 格全非 0，GID 1..520 拼出底图）、`FirstLayer`（178 非 0）、`SecondLayer`（194）、`ThirdLayer`（79）、`FourthLayer`（58）、`FifthLayer`（49）、**`collision`（202 非 0）** |
| `collision` 图层属性 | 图层自带 `<property name="collision" type="bool" value="true"/>`；`opacity="0"`（不可见）；`encoding=base64 compression=zlib` |
| **阻挡格统计** | **202 / 520 格为墙，全部 GID = `1041`**（即 `collidablesTileSet` 的第 0 号瓦片；该 tileset 声明 tilecount=3，**实际只用了 1 个**） ⇒ 墙格无其它 GID |
| 瓦片级属性 | `fight` tileset 里仅 **1 个**瓦片带 `collision` 属性：`<tile id="202"><property name="collision" type="bool" value="false"/></tile>`；`map2` / `collidablesTileSet` 的瓦片级属性均为 **0 个** |
| 可行走判定 | `map->getLayer("collision")->getTileGIDAt(tilecoord)` **非 0 即墙** —— 与"墙格全部是 1041"一致，故该判定成立 |

**★ 解码出的阻挡平面（`#`=墙 / `.`=可走，26×20，行序自上而下 = TMX 行号）【已确认】**：
```
###########..#...#########
###########..#..##########
########.##..#..#..#######
########........##..######
#####.................####
####..................####
###....................###
###.......................
..........................
..........................
..........................
..........................
.#.......................#
###....................###
###....................###
###....................###
####......####.......#####
#####....######.....######
#######..#################
#######..#################
```
**⇒ 读出的地图语义**：外圈是墙体边框；**中间 y=7..11 是一条横贯全图的通路**；上方 y=3..6 是主广场，下方 y=13..15 是另一片空间；主广场与下方区域之间只有左侧 `y=12,x=1` 与右侧 `y=12,x=25` 两个窄口。
**⇒ 对 JSTM 的启示**：这张 26×20 的小图**足以作为"服务端也能读懂同一份阻挡数据"的最小验证样本** —— 若 JSTM 的服务端移动校验要复用客户端地图，可先用它做一次"服务端重算可达性 vs 客户端 A\* 结果"的对比实验。

### 5.3 时序

```
[客户端] 点击屏幕 → GameScene 的 EventListenerTouchOneByOne::onTouchEnded
       → moveTowardPoint(map->convertToNodeSpace(touch->getLocation()))
       → tileCoordForPosition(player->getPosition() + Vec2(0,64)) 得起点
       → tileCoordForPosition(point) 得终点
       → 若起终点同格 → return
       → 若 isWallAtTileCoord(终点) → return
       → A*：openSteps.insert(起点)；循环
             取 openSteps[0] → 移入 closeSteps → openSteps.erase(0) → openSteps.clear()  ← ★
             if 命中终点 → pathfound=true break
             walkableAdjacentTilesCoordForTileCoord(当前)   ← 上/左/下/右 4 邻接过滤墙
               对每个邻接点：若在 closeSteps 跳过；G = 父G + 1；
                 H = 曼哈顿距离(|dx|+|dy|)；不在 open 则 setParent/insert；在 open 则松弛
       → 若 pathfound：closeSteps.erase(0)；player->stopAllActions()；playAnimate()
   ↓
[客户端] playAnimate() 递归（每格一次）：
       if closeSteps 空 → player->freeAction(); 发 {"type":"position",...,"state":"free"}; return
       point = map->getLayer("collision")->getPositionAt(closeSteps[0]->getPosition())  ← 格子→世界坐标
       updatePlayerDirection(point)      ← atan2 算 8 向朝向 1..8
       player->walkAction()
       发 {"type":"position","secretKey":...,"state":"walk","XPoint":px,"YPoint":py,"direction":d}
       closeSteps.erase(0)
       player->runAction(Sequence::create(MoveTo::create(0.4, point),
                                          CallFunc::create([]{ playAnimate(); }), NULL))
   ↓
[服务端] type=="position", state=="walk"
       update game set XPoint=px        （1 条）
       update game set YPoint=py        （1 条）
       update game set direction=d      （1 条）
       SendToAllPosition(secretKey, px, py, d, "walk")  ← 广播给除自己外所有会话
       若 state=="free" → SendToAllPosition(secretKey, 0,0,0, "free")
```

### 5.4 逐文件证据

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/GameScene.cpp` | `moveTowardPoint(Vec2 point)` | 本地 A*；`openSteps`/`closeSteps` 为 `Vector<ShortestPathStep*>` 成员 | **部分适合（算法思路）** | 有 G/H/父指针/open/close 结构，是标准 A* 骨架；但实现有缺陷（见下）。**🔴 GPL-3.0，不可复制代码** |
| `Classes/GameScene.cpp` | `moveTowardPoint()` 第 147 行 `openSteps.clear();` | 在刚把 `openSteps[0]` 移入 close 之后**把整个 open 表清空** | **不适合** | 🔴 **实测缺陷**：open 表每轮被清空 ⇒ 不是正确 A*；`closeSteps` 实际退化为"已弹出的 open 表快照"，路径也不是回溯 `parent` 得到的 |
| `Classes/GameScene.cpp` | `moveTowardPoint()` 第 187 行 `closeSteps.erase(0);` | pathfound 后弹掉第 0 个（起点） | 待验证 | 与上一条配合，靠"close 表顺序≈路径"侥幸能走，但**不清空残余 close** 时会重复，需实测 |
| `Classes/GameScene.cpp` | `tileCoordForPosition(Vec2 point)` | `x = (int)point.x / tileW`；`y = ((tileH*mapH) - point.y) / tileH` | 适合 | **TMX 的 Y 轴向下、Cocos Y 轴向上需要翻转**，此换算公式是 TMX 地图的标准做法，JSTM 用 TMX 可直接采用公式（非代码） |
| `Classes/GameScene.cpp` | `isWallAtTileCoord(Vec2 tilecoord)` | `gid = map->getLayer("collision")->getTileGIDAt(tilecoord); return gid != 0;` | **适合** | ★ **用一条 `opacity=0` 的独立 `collision` 图层做碰撞** 是 TMX 工作流的经典做法，**服务端若用同一份 tmx 解析也能拿到同一份阻挡数据** —— JSTM 可考虑"客户端/服务端共用一张碰撞图" |
| `Classes/GameScene.cpp` | `walkableAdjacentTilesCoordForTileCoord(Vec2)` | 只生成**上/左/下/右 4 邻接**（无对角） | 不适合 | 4 邻接会出现"斜向折线"，MMORPG 常见做法是 8 邻接 + 对角需两侧空格可通过；JSTM 建议 8 向 |
| `Classes/GameScene.cpp` | `computeHScoreFromCoordToCoord(Vec2,Vec2)` | `abs(dx) + abs(dy)`（曼哈顿） | 适合 | 4 邻接配曼哈顿是一致的 |
| `Classes/GameScene.cpp` | `costToMoveFromStepToAdjacentStep(...)` | `return 1;`（恒等代价） | 待验证 | JSTM 若要体现"草地/道路/障碍"差异，需把它改为查表 |
| `Classes/ShortestPathStep.{h,cpp}` | `setG/setH/getFScore/setParent/getParent/isEqual/getDescription` | 纯数据节点；`isEqual` 按 `Vec2` 坐标比较；`getFScore()=G+H` | 适合（设计） | 最小可用 A* 节点抽象；思路可借鉴 |
| `Classes/GameScene.cpp` | `insertInOpenSteps(ShortestPathStep*)` | 按 `f` 值**插入排序**维护 open 表（线性扫描） | 不适合 | O(n) 插入；应为二叉堆/优先队列（JSTM 若走 A* 需换） |
| `Classes/GameScene.cpp` | `getStepIndex(Vector<ShortestPathStep*>, step)` | 线性查找 `isEqual` | 不适合 | O(n)；且 `openSteps`/`closeSteps` 是 `cocos2d::Vector`，`erase(index)` 是 O(n) |
| `Classes/GameScene.cpp` | `updatePlayerDirection(Vec2 point)` | `atan2(playerX-point.x, playerY-point.y)` → 角度分档到 **1上/2左下/3左/4左上/5下/6右上/7右/8右下** | **适合（可借鉴）** | ★ 8 向朝向的分档区间可直接作为**协议里 `direction` 取值定义**的参考（JSTM 需要 direction 枚举）；注意此实现依赖 `player` 已存在 |
| `Classes/GameScene.cpp` | `playAnimate()` | 递归驱动逐格移动 + 逐格上报 + 逐格 `MoveTo(0.4)` | 待验证 | 无速度/无「共 CD」，走速被硬编码 0.4s/格且与 `speed` 字段无关 —— 与 ChivalrousMan 的 `speed` 属性形成对照 |
| `Classes/GameScene.cpp` | `moveMap(Vec2 point)` | 摄像机跟随：`MAX`/`MIN` 夹取到地图边界；可见区 960×640 | 适合（做法） | 该函数返回的是**场景节点要设置的偏移量**（`centPoint - pos`），命名有歧义；JSTM 用 Camera 组件更好 |
| `Classes/GameScene.cpp` | `update(float)` 开头 | `if (player->playerState == Player::state::WALK) this->setPosition(moveMap(player->getPosition()))` | 适合 | 只在走路时移动地图（停住时不动镜头）——简单有效 |
| `Server/游戏服务器/Form1.cs` | `type=="position"` | 见 3.2/5.3；补：**服务端完全信任客户端上报坐标** | **不适合** | 🔴 无 `M_VerifyPos` 类校验；JSTM 若做私服兼容应至少做"最大位移速度"软校验 |
| `Classes/GameScene.cpp` | `update(float)` `nearPlayer` 分支 | `nearPlayer->runAction(MoveTo::create(0.4, Vec2(XPoint,YPoint)))` | 待验证 | 用**同一条 0.4s** 对齐远端插值，依赖两帧对齐；无插值队列，网络抖动会瞬移 |

**⇒ 与 ChivalrousMan 的强烈对照**：ChivalrousMan 有 `CMClient::VerifyPlayerPos()` / `M_VerifyPos` / `doPlayerPosVerifyMsg`（服务端主动下发校验结果让其它客户端校准），
Mahatma **完全没有**这一类消息 —— 这是 Mahatma 在"移动同步"上最大的能力缺口【已确认】。

---

## 六、MySQL 表如何组织？（重点 —— `gametable.sql`）

### 6.1 结论（★ 最重要的一条）

> **`Server/gametable.sql` 全文只定义了 1 张表：`game`。**
> 全文 1397 字节、共 1 个 `CREATE TABLE`（实测：`DROP TABLE IF EXISTS \`game\`` / `CREATE TABLE \`game\`` 各 1 次）。
> **没有角色表、没有物品表、没有技能表、没有任务表、没有日志表、没有索引（除主键）、没有外键、没有存储过程、没有视图、没有初始数据 INSERT。**
>
> **⇒ 所谓"完整的表结构"实际上是"一张把账号与角色混在一行的窄表"。**
> 这意味着本项目**在数据层根本不支撑 MMORPG 业务**：所有业务数据（装备/背包/技能/任务）在这个项目里**不存在**。
> （对照 ChivalrousMan 客户端侧至少能看到 `player / playerinfo / skillinfo / equipmentinfo / backpack` 五张表 —— 见 `../chivalrousman/database.md`。）

### 6.2 `game` 表结构（表名 `game`，引擎 InnoDB，字符集 utf8 / utf8_general_ci，ROW_FORMAT=Dynamic）

| # | 字段名 | 类型 | 允许 NULL | 默认 | 主键 | 语义（由代码反推） | 证据 |
|---|---|---|---|---|---|---|---|
| 1 | `account` | `varchar(32)` | NOT NULL | — | **PK (BTREE)** | 账号，**同时也是整行唯一标识** | 【已确认】 |
| 2 | `password` | `varchar(32)` | NULL | NULL | | 密码，**明文存储** | 【已确认】`selectMysqlPassword` 直接与用户输入 `==` 比较 |
| 3 | `playerName` | `varchar(32)` | NULL | NULL | | 角色名，**空串 = 未建号** | 【已确认】`if (playername != "")` 判定是否已建号 |
| 4 | `secretKey` | `varchar(320)` | NULL | NULL | | 登录下发的会话密钥（DES+Base64），**后续所有请求的凭证** | 【已确认】 |
| 5 | `Online` | `varchar(32)` | NULL | NULL | | 在线标记，取值 **中文 `'是'` / `'否'`** | 【已确认】 |
| 6 | `PlayerType` | `varchar(32)` | NULL | NULL | | 角色职业/形象，取值 **字符串 `'1'` / `'2'`** | 【已确认】 |
| 7 | `XPoint` | `float(10,1)` | NULL | NULL | | 当前 X 坐标（世界像素坐标，非格子坐标） | 【已确认】 |
| 8 | `YPoint` | `float(10,1)` | NULL | NULL | | 当前 Y 坐标 | 【已确认】 |
| 9 | `blood` | `float(10,1)` | NULL | NULL | | 当前血量（建号初始 `100`） | 【已确认】 |
| 10 | `direction` | `int(10)` | NULL | NULL | | 朝向 1..8（建号初始 `1`） | 【已确认】 |
| 11 | `grade` | `int(10)` | NULL | NULL | | 等级（建号初始 `'1'`，**注意 SQL 里写成字符串**） | 【已确认】 |

**原文尾部（【已确认】，逐字）**：
```sql
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `game`;
CREATE TABLE `game` ( ... PRIMARY KEY (`account`) USING BTREE )
  ENGINE = InnoDB CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;
SET FOREIGN_KEY_CHECKS = 1;
```

### 6.3 连接串（硬编码，【已确认】`Server/游戏服务器/DbConnectionMySQL.cs` 第 9 行）

```
Database='gametable';Data Source='localhost';User Id='root';Password='123123';charset='utf8';pooling=true
```
⇒ 库名 `gametable`、用户 `root`、**密码明文写死在源码里**、`localhost` 单机。
（`ReadMe.md` 也要求"先建个数据库，名字为 `gametable`，然后右键运行 SQL 文件"。）

### 6.4 表设计的 6 个决定性缺陷（逐条有代码证据）

| # | 缺陷 | 证据 | 对 JSTM 的启示 |
|---|---|---|---|
| 1 | **账号表=角色表**（`account` 单主键）⇒ **一个账号只能有一个角色**，无法多角色、无法多区服 | `PRIMARY KEY (account)`；建号是 `UPDATE ... where secretKey` 而非 `INSERT` | JSTM 必须 **account / role 分表**（ChivalrousMan 的 `player` + `playerinfo` 就是分表范例） |
| 2 | **密码明文** 32 字节且与用户输入直接 `==` | `pas == password` | JSTM 必须 salted hash（bcrypt/argon2 或至少 PBKDF2） |
| 3 | **一切字段都是 varchar**（含血量、等级、坐标用 float） | `blood/grage/direction` 在 SQL 里被写成 `'1'`/`'100'`，代码里靠 `float.Parse`/`int.Parse` 还原 | JSTM 应用正确类型（INT/BIGINT/DECIMAL），避免字符串→数字的解析脆弱性 |
| 4 | **无任何业务表**（无 item/skill/quest/mail/friend…） | 全文件仅 1 个 CREATE TABLE | 说明 Mahatma **只能参考"账号-角色最小闭环"**，MMORPG 业务表必须另找参考（ChivalrousMan / kongkongxiyou / Survive） |
| 5 | **`Online` 用中文 `是`/`否`** | `update game set Online='是'` / `'否'` | 布尔应用 TINYINT(1)/DATETIME，避免编码敏感 |
| 6 | `secretKey varchar(320)` 但实际是 DES-Base64 定长；**无过期时间、无 device 绑定、无索引** | `update game set secretkey='<pas>'` | 会话表应独立（token, account, roleId, expireAt, ip），不要塞进角色行 |

### 6.5 与 JSTM 的对照结论

| 维度 | Mahatma `game` 表 | JSTM 需要 |
|---|---|---|
| 表数量 | **1** | 数十张（账号/角色/背包/装备/技能/任务/邮件/好友/公会/日志…） |
| 账号角色关系 | 1:1（同表同行） | 1:N（分表 + roleId） |
| 密码 | 明文 | 哈希 + 盐 |
| 在线态 | 中文 varchar | TINYINT / 时间戳 |
| 坐标 | 每走一格 UPDATE ×3 | 内存态 + 定时/下线持久化 |
| 事务 | **完全未使用**（`transaction` 参数全传 `null`） | 关键操作必须事务 |
| 索引 | 仅主键 | 需按 roleId/accountId 建索引 |

---

## 七、网络层与业务层如何分离？

### 7.1 结论

> **服务器端：完全没有分离。** `Form1.cs`（一个 WinForms `Form`）同时是
> ①网络监听器容器（`WebSocketServer server` 是 Form 的成员字段）、
> ②协议解析器（`JObject.Parse` + `type` 字符串比对）、
> ③业务逻辑（500 行 if/else-if 链）、
> ④SQL 拼装器（裸字符串拼接 SQL）、
> ⑤UI 呈现（`dataGridView1`、`logText`、`MessageBox`、公告 `Notice.Text`）。
>
> **客户端：分离度中等**，恰好是三段式：`SocketService`（传输）+ `Tools`（JSON/提示）+ 各 `Scene`（UI 与消息分发）。
> 但业务仍写在 Scene 里，且**用轮询而非回调**消费消息。

### 7.2 服务端分层实况（逐文件）

| 文件路径 | 类/函数名 | 属于哪一层 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|---|
| `Server/游戏服务器/Program.cs` | `static void Main()` | 宿主 | `Application.Run(new Form1())`（16 行） | 不适合 | 服务端进程**依附于 GUI 消息循环**；JSTM 是 headless 服务 |
| `Server/游戏服务器/Form1.cs` | `Form1`（partial Form） | **网络+业务+DB+UI 全都在此** | 字段 `WebSocketServer server`、`Dictionary<WebSocketSession,string> dic` | **不适合** | ★ 单一 Form 承载全部职责 ⇒ 无 Handler 注册、无依赖注入、无法单元测试 |
| `Server/游戏服务器/Form1.cs` | `listenerButton_Click` | 网络-启动 | `server = new WebSocketServer(); server.Setup(ip, port); server.Start();` 然后挂 3 个事件 | 待验证 | 监听启动**由 UI 按钮触发**，且 `Setup/Start` 失败只 `return`（用户只看到没反应） |
| `Server/游戏服务器/Form1.cs` | `ws_NewSessionConnected` / `ws_SessionClosed` / `ws_NewMessageReceived` | 网络-事件 | 三个 `+=` 事件处理器，直接在 Form 上 | 不适合 | **事件处理器 = 业务入口**：`ws_NewMessageReceived` 里立刻 `JObject.Parse` + 调 `manipulationData` |
| `Server/游戏服务器/Form1.cs` | `manipulationData(string type, JObject json, WebSocketSession client)` | 业务分发 | **一条 190+ 行的 if / else-if 链**，共 8 个分支：`register`、`login`、`createPlayer`、`loginGameScene`、`nearPlayers`、`position`、`message`（+ 隐含无 else） | **不适合** | ★ 无路由表、无 Handler 接口、无消息枚举（用裸字符串）；对照 kongkongxiyou 的 `task/skill/shop/team…Handler.js` 是按域切分 |
| `Server/游戏服务器/Form1.cs` | `SendToMessage` / `SendToAllPosition` / `GetAllLayer` | 业务-广播 | 遍历 `server.GetAllSessions()`；每次广播**内联 SQL 查询** | 不适合 | 广播逻辑里混 SQL；无 AOI、无地图分区、无队列（同步 Send） |
| `Server/游戏服务器/Form1.cs` | `SendToMessage(secretKey, name, message)` | 业务-聊天 | 全服广播 `{"type":"message","playerName","message"}` | 不适合 | 聊天**无频道、无长度限制、无频率限制、无敏感词、无落库** |
| `Server/游戏服务器/Form1.cs` | `button1_Click`（公告） | 业务-GM | 把 `Notice.Text` 以 `playerName="公告"` 全服广播 | 待验证 | 唯一"GM 工具"就是 Form 上一个 TextBox + Button，无权限校验（任何人拿到 exe 就能发公告） |
| `Server/游戏服务器/Form1.cs` | `connectMysqlButton_Click` / `showData()` | DB-UI | `dataGridView1.DataSource = GetDataSet(..., "select * from game"...)` | 不适合 | **DB 连接由 UI 按钮触发**；且 `showData()` 在每次登录/建号/进游戏后**全表刷新 DataGridView** |
| `Server/游戏服务器/Form1.cs` | `showLog(string)` | 日志 | `logText.AppendText(...)` 写到 Form 的 TextBox | 不适合 | 唯一日志目标是 UI；`log4net` 虽在 `packages.config` 里但 **Form1.cs 未 using log4net**（【已确认】文件头仅 `System.*`/`SuperWebSocket`/`Newtonsoft.Json.Linq`） |
| `Server/游戏服务器/Form1.cs` | `Form1_Load` | 宿主 | `Control.CheckForIllegalCrossThreadCalls = false;` | **不适合** | 🔴 关闭跨线程检查以让 SuperWebSocket 回调线程直接写 UI ⇒ 掩盖线程安全问题；JSTM 绝不能有此模式 |
| `Server/游戏服务器/DbConnectionMySQL.cs` | `class DbConnectionMySQL`（静态类） | 持久层 | 提供 `ExecuteNonQuery`（4 重载：connString / MySqlConnection / MySqlTransaction / 参数）、`ExecuteReader`、`GetDataSet`、`ExecuteScalar`（2 重载）、`CacheParameters`/`GetCachedParameters`、私有 `PrepareCommand` | **部分适合（工具思想）** | ★ 这是**全项目唯一有"层"味道的东西**：参数化 API 齐备、支持事务重载。**但调用方全部传 `null` 参数、全部用字符串拼 SQL** ⇒ 能力被浪费。**JSTM 可借鉴"统一 DB 访问门面"这个设计，不抄代码** |
| `Server/游戏服务器/DbConnectionMySQL.cs` | `PrepareCommand(...)` | 持久层 | `conn.Open()` 按需打开、`cmd.Connection/CommandText/Transaction/CommandType` 赋值、遍历 `cmdParms` 加参数 | 适合（设计） | 标准 ADO.NET 门面模式；**因调用方传 `null` 参数，`foreach` 永不执行** ⇒ 参数化形同虚设 |
| `Server/游戏服务器/LoginEncryption.cs` | `LoginEncryption.encryptionPassword` | 安全工具 | 见 2.2 | 不适合 | 算法不安全；且它被**内联在登录业务分支**中调用，不是独立的 Auth 服务 |
| `Server/游戏服务器/Form1.Designer.cs` | 自动生成的控件布局 | UI | WinForms 设计器产物（14 KB） | 不适合 | 服务端带 GUI ⇒ 无法容器化/无头部署 |

### 7.3 客户端分层实况

| 文件路径 | 类/函数名 | 属于哪一层 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|---|
| `Classes/SocketService.{h,cpp}` | 见 1.2 | **传输层（唯一）** | WebSocket 收 / 缓存一条 / 暴露 `getMessage()` | 部分适合 | 传输职责确实被隔离到一个单例 —— 这是本项目客户端唯一的分层动作 |
| `Classes/Tools.{h,cpp}` | `getStringFromJsonKey/getFloatFromJsonKey/getIntFromJsonKey` | **工具/编解码** | 每次调用都 `rapidjson::Document doc; doc.Parse<0>(json.c_str());` **重新解析整条 JSON** | 不适合 | 🔴 同一条消息要解析 3-7 次（`LoginScene::update` 里对 `reason` 解析了 3 次）；且无类型检查，key 不存在即崩 |
| `Classes/Tools.{h,cpp}` | `showTip/showMessageToListView/getChinese/getAnimate` | UI 工具 | 提示、聊天列表、文案字典、帧动画 | 适合（做法） | 文案外置（`text.xml`）+ 动画工具函数，JSTM 可沿用 |
| `Classes/LoadingScene.cpp` | `LoadingScene::init/callBack/plistCallBack` | 资源加载 | 异步加载 png/plist，进度条，完成后 `replaceScene(LoginScene)` | 适合 | 规范的首屏异步加载流程（`TextureCache::addImageAsync`），JSTM 可参考 |
| `Classes/LoginScene.cpp` | `init/update/callBack/editBox*` | UI + 消息分发 | 三层滑动 UI + `update()` 轮询消息 | 不适合 | UI 与消息分发耦合；无 MVVM/MVP |
| `Classes/SelectPlayerScene.cpp` | `init/createPlayerLayer/selectPlayerLayer/update/callBack` | UI + 消息分发 | 建号/选角两态层 + 轮询 | 不适合 | 同上 |
| `Classes/GameScene.cpp` | `init/update/moveTowardPoint/playAnimate/...` | **UI + 地图 + 寻路 + 角色 + 聊天 + 网络广播解析 全在一起** | 414 行 God Object | **不适合** | 一个类同时管 tmx 地图、镜头、A\*、玩家、聊天 ListView、远端玩家同步 —— JSTM 必须拆分 |
| `Classes/AppDelegate.cpp` | `applicationDidFinishLaunching` | 宿主 | `glview->setFrameSize(960,640)`；`setDesignResolutionSize(960,640, EXACT_FIT)`；`runWithScene(LoadingScene::createScene())` | 适合（事实） | 设计分辨率 960×640（与 `moveMap` 的夹取常量一致）【已确认】 |

### 7.4 "分离"评分（便于与其它参考项目比较）

| 关注点 | Mahatma 服务端 | Mahatma 客户端 | ChivalrousMan 客户端（对照） |
|---|---|---|---|
| 传输/协议独立文件 | ❌ 无（在 Form 里） | ✅ `SocketService` | ✅ `TCPClient` |
| 协议结构体/常量集中 | ❌ 无（裸字符串 `"login"`…） | ❌ 无（裸字符串 `"type"`） | ✅ `ShareData.h`（`enum M_Type` + 22 个 `*_Msg` 结构体） |
| 数据实体/Model | ❌ 无 | ❌ 无（`Player` 兼作实体） | ✅ `Model.h`（5 个 Model 类，带 `getName()`/`getAttributeName()`） |
| 持久层门面 | ⚠️ 有 `DbConnectionMySQL` 但被绕过 | ❌ 无（客户端不碰 DB） | ✅ `DBDao<T>` 模板 |
| 业务按域拆分 | ❌ 一个 `manipulationData` | ❌ 按 Scene 拆（非按域） | ⚠️ 按 Manager 拆（`TaskSystem`/`SkillManager`/`TeamManager`/`BackPackManager`/`EquipmentManager`） |
| 业务与 UI 解耦 | ❌ UI 就是业务 | ❌ Scene 就是业务 | ⚠️ Manager 与 Layer 部分解耦 |

**⇒ 【已确认】Mahatma 在"分层"这一维度是五个参考项目中最低的之一**，
唯一值得留意的正面资产是 `DbConnectionMySQL` 的**门面 API 形状**（含事务重载）与客户端 `SocketService` 的**单例隔离**。

---

## 八、7 问速查表

| # | 问题 | 一句话结论 | 标注 |
|---|---|---|---|
| 1 | 客户端如何连服务器 | Cocos `network::WebSocket` 连 `ws://<Data.json.ip>:<Data.json.port>`（实测 `10.6.32.1:80`），纯 JSON 文本帧，`type` 字段分发 | 【已确认】 |
| 2 | 登录流程 | `login` → 查 `game.account` → **明文比对密码** → DES(密码+时间, `"thisisapassword"`) 作 secretKey → 下发 `privatePassword`+`playerName`；空名→建号场景，有名→选角场景 | 【已确认】 |
| 3 | 角色数据如何入库 | 无角色表；建号 = `UPDATE game SET playerName/playerType/XPoint=300/YPoint=300/grade=1/blood=100/direction=1 WHERE secretKey`；走路每格 3 条 UPDATE；在线态写 `'是'/'否'` | 【已确认】 |
| 4 | 服务器如何加载角色 | `loginGameScene` 时用 secretKey 跑 **7 条独立 SELECT**，拼一条 `playerInformation` JSON 下发；**服务端无内存角色缓存** | 【已确认】 |
| 5 | 自动寻路如何交互 | **纯客户端 A\***（TMX `collision` 隐藏图层判墙 + 曼哈顿 H）；每走完一格发 `position(state=walk)`；服务器只写库 + **全服广播**，零校验 | 【已确认】 |
| 6 | MySQL 如何组织 | **只有 1 张表 `game`**（11 字段），账号与角色同行同主键；账号密码角色密钥在线态位置属性全塞一行；无业务表、无索引、无事务 | 【已确认】 |
| 7 | 网络层与业务层分离 | **服务端零分离**（`Form1.cs` 兼网络/协议/业务/SQL/UI）；客户端中等（`SocketService` 隔离传输，业务在 Scene，用轮询消费） | 【已确认】 |

---

## 九、未读到 / 需要后续验证

> **R2 更新**：本次已闭合 3 项（下表标 ✅），并新增 2 项由解码得到的事实。

| 项 | 状态 |
|---|---|
| ✅ `map.tmx` 的阻挡格形状 | **已闭合 →【已确认】**：`collision` 图层 520 格中 **202 格为墙**，GID **全部 = 1041**；`collidablesTileSet` 声明 3 个瓦片但**实际只用 1 个**；网格图见 §5.2 |
| ✅ `Player::attackAction()` 调用点 | **已闭合 →【已确认】无任何调用点**：全 `Classes/` 仅 3 处出现 —— `Player.h:33` 声明、`Player.cpp:128` 定义、`Player.cpp:131/132` 自身实现体内；**没有任何其它文件调用它** |
| ✅ `state::ATTACK` / `state::DEAD` 使用情况 | **已闭合 →【已确认】**：`ATTACK` 仅由 `attackAction()` 自身设置（`Player.cpp:131`），而该函数无人调用；`DEAD` 在全 `Classes/` 中**只出现在 `Player.h:15` 的枚举声明处，零处引用** ⇒ **战斗/死亡逻辑完全未实现** |
| ✅ 新增：`fight` tileset 的瓦片级 `collision` 属性 | **【已确认】只有 1 个**（`tile id=202` 且值为 `false`）；即"瓦片属性"在本项目里只是编辑器留下的孤例，真正生效的是 `collision` **图层** |
| ✅ 新增：`collision` 图层的图层级属性 | **【已确认】**`<property name="collision" type="bool" value="true"/>` —— 该图层是被显式标记为碰撞层的 |
| `Server/游戏服务器/Form1.resx`、`Properties/Resources.resx` 的控件清单 | 【未读到】未逐项展开（WinForms 设计器产物，非逻辑） |
| `proj.android/gradle` 构建链是否可复现 | 【未读到】与架构无关，未展开 |
| `Resources/Layer.csb`（聊天窗口 CCStudio 导出）内部结构 | 【未读到】二进制，仅从 `messageNode->getChildByTag(5)`（ListView）/`getChildByTag(8)`（发送按钮）反推 |
| 服务端是否曾支持战斗/组队/物品 | 【未读到】`manipulationData` 只有 7 个分支，无相关消息 |
| `Form1.resx` 里是否存在被注释掉的战斗/背包入口 | 【未知】 |
| `fight.png` / `map.png` 图集是否与 `map.tmx` 的 GID 完全对应 | 【待验证】资源文件已确认存在，未逐 GID 比对像素 |

---

## 十、给 JSTM 的 5 条可执行结论（不含任何可复制代码）

1. **协议不要学它**：JSTM 已有 `[u32 BE len][u16 BE cmd][body]` 二进制分帧，Mahatma 的"单帧文本 JSON + 轮询 + 无队列"是明确的倒退。
2. **数据库不要学它的表**，但要**吸收它的失败教训**：账号与角色必须分表、密码必须哈希、坐标不能每格落库。（对照 `../chivalrousman/database.md` 的 5 表结构。）
3. **寻路可以借用两个具体的设计点**（自研实现）：①用**一张 opacity=0 的独立碰撞图层**表达阻挡（同一份数据客户端与服务端可共用）；②`atan2` 分档得到 **8 向 `direction` 枚举 1..8** 的定义方式。
4. **唯一值得参考的服务端结构是 `DbConnectionMySQL` 的 API 形状**：统一门面 + 参数化重载 + 事务重载 —— 用它来反向自查 JSTM 是否所有 SQL 都参数化、所有多写操作都在事务里。
5. **🔴 许可证红线**：本项目为 **GPL-3.0**。以上所有"可借鉴点"必须**由 JSTM 独立重新实现**；
   **不得复制任何一行 C# / C++ / SQL / 注释**，也不得把 `gametable.sql` 文本直接导入 JSTM 的建库脚本。详见 `reuse_candidates.md`。
