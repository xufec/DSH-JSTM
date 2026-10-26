# MahatmaComeBack —— 可复用候选与 ★ 许可红线

> 对象：`cankao/MahatmaComeBack-master.zip`（GNU GPL v3）
> 用途：给 JSTM（《绝世唐门》1.4.9 私服兼容项目）判断"哪些东西可以借鉴、哪些绝对不能碰"。
> **本文件的一切"适合"都指"适合作为设计参考"，不指"可以复制代码"。**

---

## 一、🔴 许可结论（第一优先，先读这一节）

### 1.1 实测事实

| 项 | 实测 | 标注 |
|---|---|---|
| LICENSE 文件是否存在 | ✅ **存在**：`MahatmaComeBack-master/LICENSE`（35 149 字节） | 【已确认】 |
| 许可证类型 | **GNU GENERAL PUBLIC LICENSE, Version 3, 29 June 2007** | 【已确认】首行原文：`GNU GENERAL PUBLIC LICENSE` / `Version 3, 29 June 2007` / `Copyright (C) 2007 Free Software Foundation, Inc. <https://fsf.org/>` |
| 是否 copyleft | ✅ **是（强 copyleft / 传染性）** | 【已确认】 |
| 覆盖范围 | ZIP 根目录一份 LICENSE ⇒ 按惯例覆盖仓库全部内容，含 `Classes/`（客户端）、`Resources/`、`Server/`（C# 服务端）、`Server/gametable.sql` | 【待验证】未逐文件找 SPDX 头（源码文件里**未见** `SPDX-License-Identifier` 或版权声明头） |
| 第三方依赖 | `log4net 2.0.3`（Apache-2.0）、`Newtonsoft.Json 5.0.8`（MIT）、`SuperWebSocket 0.9.0.2`（Apache-2.0）、`MySql.Data`（GPL+FLOSS 例外） | 【已确认】`packages.config` / `.csproj` |
| Cocos2d-x | `ReadMe.md` 自述 Cocos2d-x **3.17.2**（引擎自带其许可，不构成本项目授权） | 【已确认】 |

### 1.2 ★ 对 JSTM 的硬结论

> ## ❌ **MahatmaComeBack 的代码绝对不能复制进 JSTM。**
>
> GPL-3.0 是**强 copyleft**：一旦把其中**任何一行代码**并入 JSTM，JSTM 整体（以及与之链接/组合发布的
> 全部衍生作品）**必须以 GPL-3.0 发布并开放全部源码**；而 JSTM 的项目定位是
> 「《绝世唐门》1.4.9 **私服兼容**」服务端，通常包含**不可公开的逆向成果与闭源成分**。
> 两者**在许可上不可调和**。因此：

| 允许 ✅ | 禁止 ❌ |
|---|---|
| 阅读 `Classes/`、`Server/`、`gametable.sql` 全部源码 | 把任何 `.cs` / `.cpp` / `.h` / `.sql` / `.json` / `.csb` 文件复制进 `server/` 或任何 JSTM 源码树 |
| 借鉴**架构思想**（分层方式、命名约定、协议字段抽象、状态机形状） | 逐行翻译（translation）其代码后当作自研 |
| 借鉴**算法思路**（如 A\* 的 G/H 设计、`atan2` 分档朝向） | 复制其注释（注释同样受版权保护） |
| 把 `gametable.sql` 当作**"反例"**阅读（见 §3） | 把 `gametable.sql` 文本导入 JSTM 的建库脚本（**即使只是 DDL 文本**） |
| 引用其公开 `ReadMe.md` 中的技术选型说明来论证设计取舍 | 声称其代码是 JSTM 自研 |
| 记录"某算法来自本项目"作为设计来源 | 把 `Resources/` 美术/字体（`han.ttf`、`fight.png`、`map.tmx`…）用进 JSTM（**同时涉及版权与商标风险**） |

**⇒ 若将来确需复用某段代码，唯一合规路径是：①联系作者取得**单独的、非 GPL 的**授权；②或把 JSTM 整体改为 GPL-3.0 并接受开源。二者都需先与项目方确认。**

### 1.3 登记表（JSTM 侧台账模板，建议每次拟复用前填写）

| 来源项目 | 文件路径 | LICENSE | 拟复用内容 | 与 JSTM 差异 | 复用什么（代码/思想） | 是否可复用 | 是否进入 JSTM |
|---|---|---|---|---|---|---|---|
| MahatmaComeBack | （任何文件） | **GPL-3.0** | — | — | **仅思想** | ⚠ 仅思想可用 | **❌ 代码一律不进入** |

---

## 二、可复用候选清单（**全部为"思想/设计参考"，均需 JSTM 独立实现**）

### 2.1 服务端侧

| # | 来源文件 | 类/函数 | 值得借鉴的点 | 复用形态 | JSTM 应如何自研 | 标注 |
|---|---|---|---|---|---|---|
| S1 | `Server/游戏服务器/DbConnectionMySQL.cs` | `DbConnectionMySQL`（静态门面） | **统一 DB 访问门面**：4 个 `ExecuteNonQuery` 重载（连接串 / 连接 / **事务** / 参数）、`ExecuteReader`、`GetDataSet`、`ExecuteScalar`(×2)、参数缓存 `CacheParameters`/`GetCachedParameters`、私有 `PrepareCommand` 统一开连接与挂参数 | **思想** | JSTM 自建 `db.py`/`session.py`：所有 SQL 走同一个入口，入口**强制** `params` 与 `transaction` | 【已确认】 |
| S2 | 同上 | `ExecuteNonQuery(MySqlTransaction trans, ...)` | "把事务作为一等公民暴露在 API 上" —— 本项目**有该能力却一次没用**，是最好的反面教材 | **思想 + 自查项** | JSTM 自研"多写操作必须事务"的强制约束（装饰器/上下文管理器） | 【已确认】 |
| S3 | `Server/游戏服务器/Form1.cs` | `manipulationData(type, json, client)` | **负面参考**：190 行 if/else 链同时做协议解析、SQL、广播、UI | **反面** | JSTM 按域拆 Handler（参照 kongkongxiyou 的 `task/skill/shop/team…Handler`） | 【已确认】 |
| S4 | `Server/游戏服务器/Form1.cs` | `ws_*` 三个事件处理器 | 事件名与职责划分（连接/关闭/收消息）本身是标准形状 | 思想（通用） | JSTM 的协议适配层保留同形状的回调 | 【已确认】 |
| S5 | `Server/游戏服务器/Form1.cs` | `SendToAllPosition` / `SendToMessage` / `GetAllLayer` | **"用一条 JSON 携带远端角色全字段 + state"**的广播消息抽象 | **思想** | ★ ★ **最值得借的一点**：把"远端角色同步"定义为**单一消息 + `state` 枚举**（`walk`/`free`/`remove`），而不是 N 个消息类型。JSTM 应在此加上 **AOI** | 【已确认】 |
| S6 | `Server/游戏服务器/Form1.cs` | `state == "walk" \| "free"` 分支 | **移动的二进制状态抽象**（走 / 停），且"停"不带坐标 | **思想** | JSTM 移动同步可分"移动开始/移动结束"两条，避免每格上报 | 【已确认】 |
| S7 | `Server/游戏服务器/Form1.cs` | `ws_SessionClosed` → `state:"remove"` | **"玩家下线"用同一条广播消息的一个 `state` 值表达**（不新开消息类型） | **思想** | JSTM 可沿用"同一同步消息 + 特殊 state"以减少命令号 | 【已确认】 |
| S8 | `Server/游戏服务器/LoginEncryption.cs` | `encryptionPassword` | **反面**：DES + key==IV + 失败降级明文 + 密钥里混时间 | **反面** | JSTM 用 HMAC-SHA256 或随机 token + `expireAt` + 独立会话表 | 【已确认】 |
| S9 | `Server/gametable.sql` | 整体 | **反面**：一账号一角色、明文密码、全 varchar、无业务表、无索引、无事务 | **反面** | 见 §3 与 `../chivalrousman/database.md` | 【已确认】 |
| S10 | `Server/游戏服务器/Form1.cs` | `secretKey` 作为登录票据贯穿后续请求 | ★ **"登录发一次票据、后续用票据"的会话模型正确**（对比把账号密码每次重发） | **思想** | JSTM 保留该模型，票据改为不可预测随机串 + 过期 + 服务端可撤销 | 【已确认】 |
| S11 | `Server/游戏服务器/` 工程布局 | `Server/` 与客户端物理分离 | ★ **"客户端与服务器各自独立工程、通过 SQL 文件交付表结构"** 的交付方式 | **思想 + 工程组织** | JSTM 也应有独立的建库脚本 + 明确的引擎版本声明 | 【已确认】 |
| S12 | `Server/游戏服务器/Form1.cs` | `button1_Click`（公告） | 存在"GM 侧全服公告"这一最小运营能力的**位置**（虽无权限控制） | 反面→需求提示 | JSTM 需要带权限校验的 GM 通道 | 【已确认】 |

### 2.2 客户端侧

| # | 来源文件 | 类/函数 | 值得借鉴的点 | 复用形态 | JSTM 应如何自研 | 标注 |
|---|---|---|---|---|---|---|
| C1 | `Classes/SocketService.{h,cpp}` | `SocketService`（单例） | **把"连接 + 收发 + 身份（account/privatePassword/playerType）"集中到一个网络单例**，Scene 不直接碰 `WebSocket` | **思想** | JSTM 客户端已是 Lua + `gamenet.luac`，可对照检查"网络是否只有一个入口" | 【已确认】 |
| C2 | `Classes/SocketService.cpp` | `initSocket()` | **用 `Resources/Data.json`（`{ip,port}`）驱动服务器地址**，不硬编码 | **思想** | JSTM 已有区服表配置，可对照 | 【已确认】 |
| C3 | `Classes/LoginScene.cpp` | `update()` 中按 `messagetype` 分派 | **"每条消息一个 `type` 字段 + 客户端按 type 分派"** 的基本形状（虽然用轮询实现） | **思想** | JSTM 已有命令号机制，无需采纳 | 【已确认】 |
| C4 | `Classes/GameScene.cpp` | `isWallAtTileCoord()` + `Resources/map.tmx` 的 `collision` 图层 | ★ ★ **用一张 `opacity="0"` 的独立 TMX 图层表达阻挡** —— 同一份地图数据可被**客户端与服务端共用**判断可行走 | **思想（高价值）** | JSTM 若做服务端寻路/移动校验，可从同一份 tmx/碰撞数据解析阻挡格，避免双份维护 | 【已确认】 |
| C5 | `Classes/GameScene.cpp` | `updatePlayerDirection(Vec2)` | ★ **`atan2` 分档得到 8 向朝向枚举 1..8** 的具体取值定义（1上/2左下/3左/4左上/5下/6右上/7右/8右下） | **思想** | JSTM 的 `direction` 字段可直接采用这套语义（**重新实现公式即可**） | 【已确认】 |
| C6 | `Classes/GameScene.cpp` | `tileCoordForPosition(Vec2)` | TMX 世界坐标 → 格子坐标的换算（注意 Cocos Y 轴向上、TMX 行号向下的翻转） | **算法常识** | JSTM 自研同公式 | 【已确认】 |
| C7 | `Classes/GameScene.cpp` | `computeHScoreFromCoordToCoord` | 4 邻接 A\* 用**曼哈顿距离**作启发（与恒等代价一致，保证可采纳性） | **算法常识** | JSTM 若实现 A\* 可直接采用 | 【已确认】 |
| C8 | `Classes/ShortestPathStep.{h,cpp}` | `ShortestPathStep` | **把 A\* 节点抽象成独立 `Ref` 子类**（position/G/H/parent/`getFScore()`/`isEqual()`），与场景解耦 | **思想** | JSTM 自研 A\* 时采用同形状（但请用二叉堆而非线性插入排序） | 【已确认】 |
| C9 | `Classes/Player.cpp/h` | `Player::init(type)` + `Player::initWithJson(json)` | ★ **同一表现类提供两种构造**：一种给"建号预览"（无数据），一种给"游戏内"（服务端数据） | **思想** | JSTM 客户端可复用"预览/正式同模型"以减少两套表现 | 【已确认】 |
| C10 | `Classes/Player.cpp` | `freeAction/walkAction/attackAction` | ★ **动画资源命名约定 `<动作前缀>_<朝向>_00`** + `Tools::getAnimate` 自动按序号探测帧数 ⇒ **新增动作/朝向无需改代码** | **思想（高价值）** | JSTM 的 Lua 动画加载可采纳"命名即索引 + 帧数由资源决定" | 【已确认】 |
| C11 | `Classes/Player.h` | `enum class state { FREE, WALK, ATTACK, DEAD }` | 角色状态机骨架 | **思想** | JSTM 需要更完整的状态机（含受击/施法/眩晕） | 【已确认】 |
| C12 | `Classes/Tools.cpp` | `getChinese(key)` + `Resources/text.xml` | ★ **提示文案外置为 plist-dict，代码只用 key** | **思想** | JSTM 可对照自查文案是否硬编码 | 【已确认】 |
| C13 | `Classes/LoadingScene.cpp` | `init/callBack/plistCallBack` | 首屏 `TextureCache::addImageAsync` 异步加载 + 进度条 + 完成后 `replaceScene` | **思想** | JSTM 已有加载流程，可对照 | 【已确认】 |
| C14 | `Classes/GameScene.cpp` | `moveMap(Vec2)` | **相机跟随并夹取到地图边界**（`MAX`/`MIN` + 可见区半宽/半高） | **算法常识** | JSTM 自研 | 【已确认】 |
| C15 | `Classes/GameScene.cpp` | `update()` 中 `if (playerState == WALK) setPosition(moveMap(...))` | **只在走路时移动镜头**（停下不动镜头）——小细节但手感相关 | **思想** | JSTM 可对照 | 【已确认】 |
| C16 | `Classes/LoginScene.cpp` | `initSelectServiceLayer/initLoginLayer/initRegisterLayer` | **登录/注册/选区三个 Layer 都预建、用 `MoveBy` 平移切换** | **反面** | 预建全部 UI 浪费内存；且两个 EditBox 成员被注册层**覆盖**（同 tag 复用）⇒ 隐患。JSTM 用 UI 栈 | 【已确认】 |
| C17 | `Classes/SelectPlayerScene.cpp` | `craetePlayerResult` | ★ ★ **协议字段拼写错误的兼容性事实**：`craetePlayerResult`（而非 `createPlayerResult`）被两侧同时使用 ⇒ **逆向项目必须保留错拼** | **事实/兼容约束** | JSTM 若对接任何遗留客户端，需先枚举此类"错拼即协议"的字符串 | 【已确认】 |
| C18 | `Classes/Tools.cpp` | `getStringFromJsonKey` 等 | **反面**：每次取字段都重新 `Parse` 整条 JSON，一条消息解析 3~7 次 | **反面** | JSTM 自查：是否存在重复解析 | 【已确认】 |
| C19 | `Classes/SocketService.cpp` | `onMessage` 单变量缓冲 | **反面**：无队列 ⇒ 丢包；且 `ifReceviceMessage` 死字段 | **反面** | JSTM 自查网络接收是否有队列 | 【已确认】 |
| C20 | `Classes/GameScene.cpp` | `update()` `nearPlayer` 分支的 `return` 位置 | **反面 bug**：`return` 在 `for` 内、`if` 外 ⇒ 远端玩家只能建 1 个 | **反面** | JSTM 自查同类"循环内误 return" | 【已确认】 |
| C21 | `Classes/Player.cpp` | `initWithJson` 里 `grade = 1;` | **反面 bug**：服务端下发的等级被硬编码覆盖 | **反面** | JSTM 自查"加载后被硬编码重置"的字段 | 【已确认】 |
| C22 | `proj.android/app/AndroidManifest.xml` | `INTERNET` 权限 | Android 联网必需权限 | **事实** | — | 【已确认】 |

---

## 三、明确**不可复用**清单（除代码外，连"思路"也不推荐）

| # | 项 | 原因 | 标注 |
|---|---|---|---|
| N1 | `Server/gametable.sql` 的**表设计**（账号=角色、明文密码、全 varchar） | 与 MMORPG 需求根本冲突；当作**反例**读 | 【已确认】 |
| N2 | `LoginEncryption` 的加密方案（DES，key==IV，失败降级明文） | 提供**虚假安全感**，比没有更危险 | 【已确认】 |
| N3 | "每走一格 3 条 UPDATE" 的持久化策略 | 不可扩展；N 人在线时 O(N) 写 | 【已确认】 |
| N4 | "全服广播、无 AOI" | 不可扩展；N=100 时单人移动即 396 次 SELECT | 【已确认】 |
| N5 | 客户端轮询 `update()` + 单变量消息缓冲 | 丢消息、每帧仅 1 条 | 【已确认】 |
| N6 | `Form1.cs` 的"UI 即服务端"结构（WinForms 依赖） | 无法无头部署/容器化 | 【已确认】 |
| N7 | `Control.CheckForIllegalCrossThreadCalls = false` | 用关闭检查掩盖线程安全问题 | 【已确认】 |
| N8 | "所有 `DbConnectionMySQL.*` 调用传 `null` 参数" | 参数化能力被弃用，SQL 注入 | 【已确认】 |
| N9 | `Resources/` 的**美术、字体、地图资源** | 版权 + 商标风险（`han.ttf`、`fight.png`、`map.png`、plist 图集…） | 【已确认】 |

---

## 四、按"JSTM 子系统"归口的采纳建议

| JSTM 子系统 | 从 Mahatma 采纳什么 | 形态 | 优先级 |
|---|---|---|---|
| 移动/寻路 | C4（共享碰撞图层思想）、C5（8 向 direction 定义）、C7/C8/C14（A\* 常识与节点抽象） | 思想 + 自研 | **高** |
| 远端角色同步 | S5（单消息 + `state` 枚举）、S6、S7 | 思想 + 自研（**必须加 AOI**） | **高** |
| 会话/登录 | S10（票据模型）、S1/S2（DB 门面 + 强制事务与参数化） | 思想 + 自研（**换掉加密与明文密码**） | **高** |
| 桌面上层（客户端表现） | C9（预览/正式同模型）、C10（动画命名约定）、C12（文案外置） | 思想 + 自研 | 中 |
| 协议兼容 | C17（错拼即协议的枚举意识） | 事实约束 | 中 |
| 数据库设计 | **仅采纳反例**（`database.md` §6 的 6 条教训）；正面参照走 ChivalrousMan | 反例 | 中 |
| 服务端架构 | S3/S4（事件形状）；分层正面参照走 kongkongxiyou / Survive | 反例 + 思想 | 低 |
| 工程交付 | S11（客户端/服务端独立工程 + `.sql` 交付表结构） | 思想 | 低 |
| 任何代码 | **一律不进入 JSTM**（GPL-3.0） | ❌ | — |

---

## 五、一句话总结

> **MahatmaComeBack = 一份"能跑通最小闭环的教学级联网 Demo"**：
> 值得 JSTM 借的只有**十来条设计思想**（共享碰撞图层、8 向朝向定义、远端同步用单消息 + `state`、
> 登录票据模型、动画命名约定、DB 门面 API 形状），
> 以及**一长串反面教训**（一账号一角色、明文密码、每格落库、全服广播、轮询丢包、UI 即服务端）。
> **而它全部代码受 GPL-3.0 强 copyleft 保护 ⇒ 一行都不能进 JSTM。**
