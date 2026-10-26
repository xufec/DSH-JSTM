# MahatmaComeBack —— 角色系统审计（创建 / 加载 / 状态 / 持久化）

> 对象：`Classes/Player.{h,cpp}`、`Classes/SelectPlayerScene.{h,cpp}`、`Classes/GameScene.cpp`、`Server/游戏服务器/Form1.cs`、`Server/gametable.sql`。
> **🔴 LICENSE = GPL-3.0 ⇒ 以下实现细节只能作设计参考，代码不得复制进 JSTM。**
> 标注：【已确认】/【待验证】/【未知】。

---

## 一、角色数据模型（两侧对照）

### 1.1 客户端 `Player` 类（`Classes/Player.h`，【已确认】全文 51 行）

| 成员 | 类型 | 语义 | 是否有服务端对应字段 |
|---|---|---|---|
| `freeTextureFileName` | `string` | 站立动画名前缀：`"nas"`(type1) / `"qks"`(type2) | ❌ 客户端派生 |
| `walkTextureFileName` | `string` | 行走动画名前缀：`"nz"` / `"qk"` | ❌ 客户端派生 |
| `attackTextureFileName` | `string` | 攻击动画名前缀：`"nza"` / `"qka"` | ❌ 客户端派生（**无调用点**） |
| `playerState` | `enum class state { FREE, WALK, ATTACK, DEAD }` | 角色状态 | ⚠ 部分（服务端用 JSON 里的 `state` 字符串） |
| `playerDirection` | `int` | 朝向 `1..8` | ✅ `game.direction` |
| `nameLabel` | `Label*` | 头顶名字 | ❌ 客户端 |
| `playername` | `string` | 角色名 | ✅ `game.playerName` |
| `playerType` | `string` | `"1"` / `"2"` | ✅ `game.PlayerType` |
| `Xpoint` | `float` | X | ✅ `game.XPoint` |
| `Ypoint` | `float` | Y | ✅ `game.YPoint` |
| `grade` | `int` | 等级 | ✅ `game.grade` |
| `blood` | `float` | 血量 | ✅ `game.blood` |

**★ 客户端角色模型只有 6 个可持久化字段**。缺失：`maxBlood`、`mana`、`exp`、`gold`、`attack`、`defense`、`buff`、`装备`、`技能`、`背包`。
（对照 ChivalrousMan 的 `PlayerInfo` 有 15 个字段 —— 见 `../chivalrousman/database.md`。）

### 1.2 服务端侧"角色模型"

**不存在**。服务端**没有任何 C# 角色类**（`Server/游戏服务器/` 下没有 `Player.cs` / `Role.cs` / `Entity` 类）。
角色在服务端只以 ①`game` 表的一行 ②`JObject` ③`Dictionary<WebSocketSession,string>` 中的 key 三种形态存在。【已确认】

| 形态 | 类型 | 生命周期 | 是否含完整角色数据 | 标注 |
|---|---|---|---|---|
| 数据库行 | `game` 表 1 行 / 账号 | 永久 | ✅ 11 字段 | 【已确认】 |
| 网络 JSON | `JObject`（Newtonsoft） | 单次消息 | ✅ `playerInformation`/`nearPlayer` 的 7 字段 | 【已确认】 |
| 会话映射 | `Dictionary<WebSocketSession,string> dic` | 连接存续期 | ❌ **只有 secretKey，没有角色数据** | 【已确认】 |

**⇒ 服务端没有"在线角色对象"**。要拿角色数据，只能回 DB 查（这正是 §3 里 N+1 查询的根因）。

---

## 二、角色生命周期全流程

```
① 建号（create）
   [C] SelectPlayerScene:init(1) → createPlayerLayer()
         Player::create(1|2)  ← 预览用，setScale(3.5)
       tag==10 → {"type":"createPlayer","secretKey","playerName","playerType"}
   [S] 判重名 → UPDATE game SET playerName,playerType,XPoint=300,YPoint=300,grade='1',blood='100',direction=1
                WHERE secretKey='<k>'
       → {"type":"craetePlayerResult","ifSuccess":"true","playerType":"T"}
   [C] SelectPlayerScene:update() → setPlayerType(T) → selectPlayerLayer()

② 选角 + 进场景（load）
   [C] SelectPlayerScene:selectPlayerLayer()
         type = (SocketService::getPlayerType()=="2") ? 2 : 1
         Player::create(type)  ← 又建了一个预览角色，setScale 默认 1.5
       tag==20 → {"type":"loginGameScene","secretKey":"<k>"}
   [S] SELECT ×7（WHERE secretKey） → {"type":"playerInformation", playerName,playerType,
                                        XPoint,YPoint,grade,blood,direction}
       UPDATE game SET Online='是'
   [C] SelectPlayerScene:update() → replaceScene(GameScene::createScene(str))   ★ 整条 JSON 透传
   [C] GameScene::init(json)
         TMXTiledMap::create("map.tmx")
         Player::createWithjson(json) → Player::initWithJson(json)
         sendMessage({"type":"nearPlayers","secretKey":"<k>"})

③ 运行期（runtime）
   [C] 本地 A* 寻路 → 每格 playAnimate()
         Player::walkAction() / freeAction()
         发 {"type":"position","secretKey","state":"walk","XPoint","YPoint","direction"}
   [S] UPDATE XPoint / YPoint / direction（3 条）+ 广播 nearPlayer

④ 其它玩家（remote）
   [S] nearPlayer（含 state=free/walk/remove）
   [C] GameScene::update()
         state=="remove" → removeFromParentAndCleanup(true)
         state=="free"   → freeAction()
         否则             → setDirection + walkAction + MoveTo(0.4,(x,y))
         未在 nearplayers 中 → Player::createWithjson(str) 新建

⑤ 下线（logout）
   [S] ws_SessionClosed → UPDATE game SET Online='否'
                        → SendToAllPosition(secretKey, 0,0,0, "remove")
   [C] 其它客户端收到 state=="remove" → 删除该角色节点
```

---

## 三、逐文件 / 类 / 函数证据

### 3.1 角色创建

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SelectPlayerScene.cpp` | `createPlayerLayer()` | 两个 `Player::create(1/2)` **叠在同一坐标**（`winSize.width/3+100, winSize.height/2`），用 `setVisible` 切换；两张头像 `player1/2HeadSelect` 与 `player1/2HeadUnselect` 用 `EventListenerTouchOneByOne::onTouchBegan` 的 `getBoundingBox().containsPoint` 判定 | 不适合 | "两个模型叠放 + 只切 visible"是 UI 取巧；攻击/朝向无预览 |
| `Classes/SelectPlayerScene.cpp` | `onTouchBegan` λ | 点 `player1HeadUnselect` → 显示 1 号，`playerType = 1`；点 2 号 → `playerType = 2` | 适合（流程） | 两职业二选一的建号交互，JSTM 可扩展为 N 职业 |
| `Classes/SelectPlayerScene.cpp` | `callBack()` tag==10 | 拼 JSON 发 `createPlayer`；**未做任何本地校验**（`editBoxTextChanged` 只把文本存入 `name`） | 不适合 | 空名/非法字符交给服务端（服务端也只查重名） |
| `Classes/SelectPlayerScene.cpp` | `editBoxTextChanged(editBox, text)` | `name = text;` | 不适合 | 名字长度只在 `setMaxLength(10)` 客户端生效 |
| `Server/游戏服务器/Form1.cs` | `type=="createPlayer"` | 见 `architecture.md` §3.2；判重名后 `UPDATE`；失败只回 `ifSuccess=false` | 不适合 | ①无角色上限（一个账号永久 1 个）②出生坐标硬编码 `300.0, 300.0` ③初始属性硬编码 ④唯一失败原因是重名 ⑤**判重与写入之间无唯一约束**（`playerName` 无 UNIQUE 索引）⇒ 并发可重名 |
| `Server/游戏服务器/Form1.cs` | 建号 SQL 中 `grade='1'`、`blood='100'` | 数字写成字符串 | 不适合 | 字段类型是 `int/float`，却用引号包字符串，靠 MySQL 隐式转换；未填的字段全为 `NULL` |
| `Resources/ui/createPlayerFont.png` 等 | — | 建号界面美术资源 | — | 事实性 |

**⇒ 建号协议的兼容陷阱【已确认】**：服务端和客户端**同时把 `create` 拼写成 `craete`**（`craetePlayerResult`）。
任何按"正确拼写"重写的服务端都会与现有客户端不兼容 —— 这类"错拼即协议"的点在逆向项目中极重要。

### 3.2 角色加载

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/SelectPlayerScene.cpp` | `update(float)` | `messagetype == "playerInformation"` → `replaceScene(GameScene::createScene(str))` | 不适合 | **JSON 字符串当"参数"在场景间传递**；解析被推迟到 `Player::initWithJson` |
| `Classes/SelectPlayerScene.cpp` | `selectPlayerLayer()` | 依据 `SocketService::getPlayerType()`（登录时下发的 `playerType` 字符串）决定预览模型 | 待验证 | 依赖登录阶段缓存；若登录时 `playerName==""` 则该值未设置 |
| `Classes/GameScene.cpp` | `init(string json)` | 建 TMX 地图 → `Player::createWithjson(json)` → `map->addChild(player)` → `setPosition(moveMap(player->getPosition()))` → 发 `nearPlayers` → 建聊天窗 → 挂点击寻路监听 → `scheduleUpdate()` | 不适合 | 一个 `init` 干 7 件事；`player` 直接 `addChild` 到 **map 节点**（而非场景），后续 `this->addChild(n)` 把远端玩家加到 **Layer** ⇒ **坐标系不一致**（第 41 行 `map->addChild(player)` vs 第 403 行 `this->addChild(n)`）【已确认】 |
| `Classes/Player.cpp` | `Player::initWithJson(string json)` | 逐字段解析 → 按 `playerType` 选动画前缀 → `freeAction()` → `setScale(1.5)` → `setPosition(Vec2(Xpoint,Ypoint))` → `Label` 名字（`setPosition(50,150)` 硬编码） | 适合（做法） | ★ **"服务端结构体 → 同一表现类的第二种构造"**是可借鉴手法（无解析重复代码）；但 `grade` 被**无条件覆盖为 1**（第 75/82 行 `grade = 1;`）⇒ **服务端下发的 `grade` 永远丢失** |
| `Classes/Player.cpp` | `Player::initWithJson` 第 75/82 行 `grade = 1;` | 按 type 分支里硬编码重置 | **不适合** | 🔴 **实测 bug**：先 `grade = getIntFromJsonKey(json,"grade")`（第 65 行），再在 type 分支里被覆盖为 `1`。等级从服务端加载后立刻丢失 |
| `Classes/Player.cpp` | `Player::createWithjson(string)` | 工厂：`new` + `initWithJson` + `autorelease` | 适合 | 标准 Cocos 工厂模式 |
| `Server/游戏服务器/Form1.cs` | `type=="loginGameScene"` 7× SELECT | 见 `architecture.md` §4.2 | 不适合 | N+1 查询；`float.Parse`/`int.Parse` 对 NULL 会抛异常 |
| `Classes/GameScene.cpp` | `init` 中 `map->addChild(player)` | 玩家被加到 **TMX 地图节点**下（坐标系 = 世界坐标） | 待验证 | 与 `moveMap`（`this->setPosition` 移 Layer）配合实现镜头跟随；但远端玩家却加在 Layer 上 ⇒ **必须实测确认两者的坐标基准是否一致**，否则远端玩家会错位 |

### 3.3 角色表现与状态

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Classes/Player.cpp` | `freeAction()` | `stopAllActions()`；`playerState = FREE`；动画名 `String::createWithFormat("%s_%d_00", freeTextureFileName, playerDirection)`；`RepeatForever(getAnimate(str, 1, 0.3))` | 适合（做法） | ★ **动画名约定 `<动作前缀>_<朝向>_00`** 是清晰的可扩展命名法：动作×朝向 → 帧序列，JSTM 可参考该"命名即索引"思路 |
| `Classes/Player.cpp` | `walkAction()` | 同上，前缀 `walkTextureFileName`，帧间隔 0.1 | 适合 | 帧速区分站立(0.3)/行走(0.1) |
| `Classes/Player.cpp` | `attackAction()` | 同上，前缀 `attackTextureFileName`，帧间隔 0.04 | **不适合** | **R2 已闭合 →【已确认】无任何调用点**：全 `Classes/` 仅 3 处出现 —— `Player.h:33` 声明、`Player.cpp:128` 定义、`Player.cpp:131-132` 自身实现体内；**没有任何其它文件调用它** ⇒ 攻击动画是死代码 |
| `Classes/Player.h` | `enum class state { FREE, WALK, ATTACK, DEAD }` | 4 态 | 适合（骨架） | `ATTACK`/`DEAD` 无迁移逻辑；`GameScene::update` 只读 `WALK` 用于镜头跟随 |
| `Classes/Player.cpp` | `setDirection(int)` / `getDirection()` | 单纯赋值 | 适合 | 朝向是纯数据，由 `GameScene::updatePlayerDirection` 计算 |
| `Classes/GameScene.cpp` | `updatePlayerDirection(Vec2 point)` | `atan2(playerX-point.x, playerY-point.y)` → 角度分档 → 设 `1..8` | **适合（可借鉴）** | ★ **8 向枚举定义**：1=上、2=左下、3=左、4=左上、5=下、6=右上、7=右、8=右下（分档区间 −15°/−75°/−105°/−165° 与 15°/75°/105°/165°）。JSTM 的 `direction` 字段可直接采用这套取值定义 |
| `Classes/Tools.cpp` | `getAnimate(framename, loops, delay)` | 从 1 开始递增拼接 `"%s%d.png"`，`SpriteFrameCache::getSpriteFrameByName` 取不到即停 ⇒ **帧数由资源决定** | 适合（做法） | 资源驱动帧数，代码无需改（JSTM 可参考） |
| `Classes/Player.cpp` | `nameLabel = Label::create(playername, "fonts/han.ttf", 15)` + `setPosition(Vec2(50,150))` | 头顶名 | 待验证 | 偏移硬编码 `(50,150)`，与 `setScale` 无关 ⇒ 缩放后可能错位 |
| `Classes/GameScene.cpp` | `update(float)` 远端同步 | `MoveTo::create(0.4, Vec2(XPoint,YPoint))` | 待验证 | 用与本地同长的 0.4 s 插值；无插值缓冲/无速度推算 ⇒ 网络抖动时瞬移 |

### 3.4 角色持久化

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
|---|---|---|---|---|
| `Server/游戏服务器/Form1.cs` | `type=="position"` | 每走一格 3 条 UPDATE | **不适合** | 见 `database.md` §3.1：N 人在线时开销 O(N) |
| `Server/游戏服务器/Form1.cs` | `type=="loginGameScene"` | `Online='是'` | 待验证 | `Online` **从不被查询** ⇒ 写了也没用【已确认】 |
| `Server/游戏服务器/Form1.cs` | `ws_SessionClosed` | `Online='否'` + 广播 `remove` | 待验证 | 若 `dic` 无该 session，只走 `KeyNotFoundException` 分支且**不写库** |
| `Server/游戏服务器/Form1.cs` | **无整包保存** | ❌ 没有"角色离线保存"函数 | 不适合 | 角色数据只靠"移动时写坐标"增量维护，一旦有未被 `position` 覆盖的字段（如未来加经验），无处保存 |
| `Server/游戏服务器/DbConnectionMySQL.cs` | `ExecuteNonQuery(MySqlTransaction, ...)` | 提供事务重载 | 待验证 | **Form1 从未使用** ⇒ 单个角色操作也无事务 |

---

## 四、角色字段权威性对照（谁说了算）

| 字段 | 建号时 | 运行期写入者 | 运行期是否被校验 | 权威方 | 标注 |
|---|---|---|---|---|---|
| `account` | 注册 | 不变 | — | 服务端 | 【已确认】 |
| `password` | 注册 | 不变 | — | 服务端 | 【已确认】 |
| `secretKey` | — | 登录 | 仅作为查询条件 | 服务端 | 【已确认】 |
| `playerName` | 建号 | 不变 | 建号时查重名 | 服务端 | 【已确认】 |
| `PlayerType` | 建号 | 不变 | 无 | 客户端上报 | 【已确认】 |
| `XPoint` / `YPoint` | 建号（300,300） | **每格**由 `position` | **无** | **客户端** | 【已确认】 |
| `direction` | 建号（1） | **每格**由 `position` | **无** | **客户端** | 【已确认】 |
| `blood` | 建号（100） | **从不更新**（无战斗） | — | — | 【已确认】 |
| `grade` | 建号（1） | **从不更新**（无经验） | — | — | 【已确认】 |
| `Online` | — | 进游戏 / 断线 | **从不被读** | 服务端 | 【已确认】 |

**⇒ 角色系统的功能完整度【已确认】**：

| 能力 | 状态 |
|---|---|
| 注册 / 登录 / 建号 / 选角 / 进场景 | ✅ 已实现 |
| 移动 + 朝向 + 远端同步 | ✅ 已实现（客户端权威） |
| 血量变化 | ❌ 无（`blood` 只有建号初值） |
| 升级 / 经验 | ❌ 无 |
| 攻击 / 受击 / 死亡 | ❌ 无（`attackAction()`/`state::DEAD` 无调用点） |
| 背包 / 装备 / 技能 | ❌ 无（**连表都没有**） |
| 任务 | ❌ 无 |
| 组队 / 好友 / 公会 | ❌ 无 |
| 多角色（一账号 N 角色） | ❌ 无（`game` 表主键即账号） |
| 角色删除 / 改名 | ❌ 无 |
| 封号 / 禁言 | ❌ 无 |

---

## 五、给 JSTM 的 4 条角色系统结论

| # | 结论 | 依据 |
|---|---|---|
| 1 | **数据模型不要学**：只有 6 个可持久化字段，且 `grade` 在客户端加载后被硬编码覆盖为 1。JSTM 需要完整属性集（对照 ChivalrousMan 的 15 字段 `PlayerInfo`） | 【已确认】 |
| 2 | **值得借鉴的是两个具体做法**：①**动画名约定 `<动作>_<朝向>_00`**（资源驱动帧数，新增动作无需改代码）；②**`atan2` 分档得到 8 向 `direction` 1..8 的取值定义** | 【已确认】 |
| 3 | **工程手法可借鉴**：同一表现类提供 `init(type)`（预览）与 `initWithJson(json)`（游戏内）两种构造，避免预览/正式两套模型 | 【已确认】 |
| 4 | **反面教训**：`Online` 写了不读、`grade` 加载即覆盖、远端玩家与本地玩家挂在不同父节点（坐标系不一致）、每格 3 条 UPDATE —— 这些都是 JSTM 应主动自查的同类问题 | 【已确认】 |

---

## 六、未读到 / 待验证

> **R2 更新**：本次闭合 2 项（标 ✅）。

| 项 | 状态 |
|---|---|
| ✅ `attackAction()` 的调用点 | **已闭合 →【已确认】无调用点**。全 `Classes/` 命中 3 处：`Player.h:33`（声明）、`Player.cpp:128`（定义）、`Player.cpp:131-132`（实现体内）。**无外部调用** |
| ✅ `Player::state::DEAD` 的使用 | **已闭合 →【已确认】零引用**。`DEAD` 仅出现在 `Player.h:15` 的枚举声明；`state::ATTACK` 也仅由 `attackAction()` 自身在 `Player.cpp:131` 设置，而该函数无人调用 ⇒ **攻击/死亡状态机完全未接入** |
| `map->addChild(player)` 与 `this->addChild(n)` 的实际渲染结果 | 【待验证】需跑起来验证坐标系是否一致 |
| 服务端是否有"顶号"逻辑 | 【未读到】`loginGameScene` 只写 `Online='是'`，不检查旧连接 |
| `Player` 是否有析构清理（`delteInstance` 风格） | 【未读到】`Player` 无单例，靠 Cocos 引用计数 |
| 角色等级上限 / 成长曲线 | 【未读到】无任何相关代码或配置 |
| `fight.png` / `map.png` 是否与 `map.tmx` GID 对应 | 【待验证】见 `architecture.md` §5.2 与 §9 |
