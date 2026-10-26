# ChivalrousMan《侠客行》客户端侧战斗流程证据审计

> 审计对象：开源项目 ChivalrousMan（Cocos2d-x 3.x C++ 客户端，**服务端源码不在本仓库**，README.md:9 指向 <https://gitee.com/lsylovews/CM-Server>）。
> 审计材料：`C:\WINDOWS\TEMP\audit_chiv\Classes\`（UTF-8 转码副本）与 `C:\WINDOWS\TEMP\audit_chiv\Resources\`，只读，未做任何修改。
> 目标项目：JSTM =《绝世唐门》1.4.9 私服兼容项目（复刻 MMORPG 服务端 + 客户端业务）。
> 许可：ChivalrousMan **无 LICENSE 文件** ⇒ 无 GPL 式传染，但也**不是已获授权**。本审计按本项目【原则 3】处理：**只借鉴设计与机制（不复制代码）**，并在正文标明每个可借鉴点。详见 `reuse_candidates.md`。

## 证据标注约定

| 标注 | 含义 |
| --- | --- |
| 【已确认】 | 审计员本人读到了那一行/那一段代码，行号可回溯 |
| 【待验证】 | 有代码或注释线索，但需要一个本仓库不具备的前提（服务端实现、引擎库语义、运行时行为）才能定论 |
| 【未知】 | 本仓库中完全没有对应代码，无法判断；本报告中此类项一律写明"未读到"，不做推测 |

**全仓库均未读到**的东西（下文表格中不再重复声明为【未知】的依据）：服务端处理逻辑、数据库建表脚本（README 提到"附件中的 sql 文件"但归档内不存在）、任何战斗反作弊校验。

---

## 1. 核心结论速览

| 问题 | 结论 | 关键证据 |
| --- | --- | --- |
| 实时制还是回合制？ | **逻辑上是回合制（玩家一方 ↔ 怪物一方严格交替），表现与调度上是实时定时器驱动**。没有行动顺序表，没有全体回合结算点 | `FightLayer.cpp:156-157`、`:200-205`、`:207-210`（空函数）、`FightLayer.h:227`（回合数字段未使用） |
| 战斗权威方是谁？ | **客户端本地结算伤害，服务器只按 fd 定向转发消息**。攻击协议里根本不存在伤害/血量字段 | `ShareData.h:218-245`、`FightLayer.cpp:452`、`:492`、`CMClient.cpp:489-535` |
| 战斗状态机？ | 真正驱动战斗的是 **FightLayer 的 8 个布尔/计数标志**；`PlayerState/PlayerWait/PlayerRun` **不是战斗状态机**，是地图上的待机/跑动动画状态 | `FightLayer.h:221-233`、`PlayerWait.cpp:48-54`、`PlayerRun.cpp:49-55`、`Player.cpp:118-132` |
| 技能伤害公式？ | `最终伤害 = (baseAttack + 30 × grade) − 目标defense`，下限 1；无暴击、无浮动、无属性克制 | `Skill.cpp:76`、`Monster.cpp:103` |
| 技能上限 8 个？ | **是资源与工厂层面的事实上限（恰好 8 个技能），代码里没有 `8` 这个常量，也没有数量校验** | `SkillFactory.cpp:12-50`、`SkillManager.cpp:25-34`、`DealLayer.cpp:180-192` |
| 怪物有掉落吗？ | **没有**。怪物只有 exp/glod，全仓库 grep `drop` 零命中 | `Monster.h:33-41`、`Monster.cpp:109-119` |
| 伤害飘字数值从哪来？ | 本地计算结果的展示，**不是消息字段** | `HurtValueLayer.cpp:21-33`、`Monster.cpp:106`、`Player.cpp:202` |
| 战斗结束后经验金币谁给？ | 客户端本地加（`addGlod/addExp`），之后由客户端直连 MySQL 回写 | `FightLayer.cpp:510-521`、`CameraPlayer.cpp:244-267` |
| 失败也发奖？ | **是**，`endFunc()` 无条件发奖，不判断 `FightSuccess/FightFailed` | `FightLayer.cpp:502-521` |
| 伤害公式里的 attack/defense 从哪来？ | **也是客户端算的**：基础值查库 + 人物升级 `+5/+5` + 装备 `+(等级−1)×8` + 装备每级 `+8/+8`，累加后经 `updatePlayerData()` **广播给所有人**。客户端权威在数值层的完整闭环 | `PlayerData.cpp:58-75`、`EquipMent.cpp:74-114`、`CMClient.cpp:291-306` |
| 战斗数值配置存在哪？ | 4 张纯文本表：8 技能（`.att`）、10 怪物（`.att`）、15 装备（`.att`）、3 药品（`.att`），商品清单另在 `DealThing/*.dt`。字段名是装饰性的，解析**只按位置** | 附录 A/B/C、`PreProcess.h:76-79`、`Resources/DealThing/` |
| 有什么跨平台地雷？ | `Skill/long/` 与 `Skill/recallCountermand/` 磁盘为小写，代码与 `GameData.xml` 用大写 ⇒ **Android/iOS/Linux 上这 2 个技能的动画与图标会加载失败** | `AppDelegate.cpp:175-184`、`FightLayer.cpp:300-305`、§2.12 |

---

## 2. 特别要求回答的点（逐条）

### 2.1 战斗是实时制还是回合制？【已确认】

**结论：逻辑回合制 + 实时定时器实现。** 三条证据链：

**(1) 逐帧驱动 + 1 秒行动条。**
```cpp
// FightLayer.cpp:156-157
schedule(schedule_selector(FightLayer::onTimer), 1);
scheduleUpdate();

// FightLayer.cpp:200-205
void FightLayer::update(float dt)
{
    updateBloodAndMana();
    checkMonsterBehavie();   // 怪物出手在这里被逐帧推进
    checkFightEnd();
}
```
`onTimer` 每秒把 `m_timeLabel` 的秒数 −1，**减到 0 就替玩家执行动作**（默认普攻，或上一次选中的技能）：
```cpp
// FightLayer.cpp:418-429
float ftime = std::stof(time) - 1;
if (ftime == 0)
{
    if (m_selectedMonster->isDie()) reSelectMonster();
    if (m_selSkill == nullptr) playerAttackMonster();
    else onSkill(m_selSkill);
}
```
行动条长度由"自动/手动"开关决定：手动 `"10"`（10 秒），自动 `"2"`（2 秒）（`FightLayer.cpp:212-224`）。所以"自动战斗"的实质是**行动条超时自动普攻**，不是独立 AI。

**(2) 严格交替，而不是自由实时。** 玩家出手后 `m_isPlayer=false`，1.6 秒后 `m_isPlayerEnd=true`（`FightLayer.cpp:443-459`）；`checkMonsterBehavie()` 逐帧观察到 `!m_isPlayer && m_isPlayerEnd && m_lastMonsterEnd` 才让**第 `m_curMonster` 只**怪物出手（`FightLayer.cpp:670-678`），怪物动画 1.6 秒后 `m_lastMonsterEnd=true` 再轮到下一只；`m_curMonster` 越界时把 `m_isPlayer` 置回 `true`，玩家回合重新开始（`FightLayer.cpp:464-475`）。这是**回合轮转**，只是用实时计时器排动画节奏。

**(3) 原设计想做完整回合制，但没写完。**
```cpp
// FightLayer.cpp:207-210  —— 空函数，且全仓库从未被调用【已确认】
void FightLayer::calcActionOrder()
{
}
```
```cpp
// FightLayer.h:227  —— 声明了却全仓库零引用【已确认】
int m_mmor = 1;                      //纪录回合数
```
另有 `MonsterEndBehavie()` 宏（`FightLayer.cpp:43`）定义了但从未使用。可判定：作者原本规划了"行动顺序 + 回合计数"的经典回合制，最终交付的是"行动条 + 标志位交替"的半成品。

> **对 JSTM 的意义**：这是典型的"1.4.x 时代手写战斗循环"，与《绝世唐门》那种服务端驱动的回合战斗相比，它缺少服务端权威与行动序列，但它的**行动条超时托管（10s/2s 两档）** 是一个值得直接借鉴的挂机体验设计。

### 2.2 战斗的权威方是谁？【已确认：客户端本地结算】

**该仓库中不存在任何服务端伤害计算；服务器在战斗链路里只承担"按 fd 定向转发"。**

**(1) 协议结构体里没有伤害字段、没有血量字段。**
```cpp
// ShareData.h:232-245
struct PlayerAtk_Msg
{
    M_Type type;
    char skill[30];   //是否使用技能
    int grade;
    int fd;               //
    int dest;           //发送给谁
    int towho;        //进攻谁
};
// ShareData.h:218-230
struct MonsterAtk_Msg
{
    M_Type type;
    int fd;
    int dest;        //发送给谁
    int who;        //谁进攻
    int towho;     //进攻谁
};
```
`PlayerAtk_Msg` 只传"用什么技能、几级、打第几只怪"；`MonsterAtk_Msg` 只传"哪只怪、打谁"。**伤害值必须由接收端自己重算**——这就是客户端权威的铁证。

**(2) 每一个 `send*` / `do*` 的调用点与实现。**

| 消息 | 发送点（调用点） | 发送实现 | 接收实现 | 有无伤害字段 |
| --- | --- | --- | --- | --- |
| `sendPlayerAtkMsg` | `FightLayer.cpp:440`（普攻，组队时对每名队友发）<br>`FightLayer.cpp:602`（技能，组队时对每名队友发） | `CMClient.cpp:489-498` | `doPlayerAtkMsg` `CMClient.cpp:510-517` → `FightLayer::otherPlayerAtk` `FightLayer.cpp:742-763` | **无** |
| `sendMonsterAtkMsg` | `FightLayer.cpp:769`（`notifyOtherPlayerMonsterAtk`，**仅队长 `P_STATUS_HEADER` 分支调用**，见 `FightLayer.cpp:644-657`） | `CMClient.cpp:500-508` | `doMonsterAtkMsg` `CMClient.cpp:519-535` → `FightLayer::monsterAttackPlayer` | **无** |
| `sendPlayerRunMsg` | `FightLayer.cpp:789`（`notifyOtherPlayerRunAway`） | `CMClient.cpp:537-543` | `doPlayerRunMsg` `CMClient.cpp:545-552` → `FightLayer::OtherRunAway` | 只有 flag |
| `sendUseMedicationMsg` | `FightLayer.cpp:563` | `CMClient.cpp:554-559` | `doUseMedicationMsg` `CMClient.cpp:561-566` → `setOtherPalyerEnd()` | **无**（连药品名都没有） |
| `sendPlayerDieMsg` | `FightLayer.cpp:698` | `CMClient.cpp:568-573` | `doPlayerDieMsg` `CMClient.cpp:575-579` → `setOtherPlayerDie()` | **无** |
| `sendTeamFightMsg` | `GameLogicLayer.cpp:230`（`checkTeamEntryFight`，仅队长） | `CMClient.cpp:470-477` | `doTeamFightMsg` `CMClient.cpp:479-487` → 只写 `GameDynamicData` | 只有怪物名+数量 |

分发入口是 `CMClient::OnRecv` 的 `switch (M_Type)`（`CMClient.cpp:36-111`）。

**(3) 伤害在接收端本地重算，公式三处完全一致。**
```cpp
// FightLayer.cpp:452   玩家打怪（本地玩家 attack）
this->m_selectedMonster->beAttack(GetPlayerData().getattack());
// FightLayer.cpp:490-492  怪打玩家 / 怪打队友（用本地怪物 .att 的 attack）
if (who == -1) AttackPlayer(this->m_monsterList[index]->getattack());
else ((XGamePlayer*)m_otherPlayers[who])->beAttack(this->m_monsterList[index]->getattack());
```
```cpp
// Monster.cpp:103 / Player.cpp:199 / CameraPlayer.cpp:232  三处逐字相同
float hurtvalue = attack <= m_defense ? 1 : attack - m_defense;
```
也就是说：**每台客户端各自持有同一份怪物属性文件（`Resources/Monster/<Name>/<Name>.att`）和同一份玩家属性广播，因此能算出相同的数值——本质是"确定性本地模拟 + 消息对表"，不是服务端结算。**

**(4) 血量/经验/金币也是本地加，权威落点其实是客户端直连 MySQL。**
```cpp
// FightLayer.cpp:512-513
GetPlayerData().addGlod(m_settlementGlod);
GetPlayerData().addExp(m_settlementExp);

// CameraPlayer.cpp:244-263  退出/切场景时才回写数据库
PlayerInfo playerinfo;
DBDao<PlayerInfo> dbdao;
...
dbdao.updateModel(keyvls);
```
`DBDao` 用 libmysql 直连，**主机名/账号/密码硬编码在头文件里**（`DBDao.h:106-113`：`47.93.235.6` / `game` / 明文口令 / 库名 `chivalrousman`）。这是本项目"客户端即权威"的结构性原因——服务端不参与数值，只做消息转发。

**(5) 唯一有反作弊意图的地方是位置，不是伤害。**
```cpp
// AudioSystem.cpp:45-49  每 180 × 50ms ≈ 9 秒上报一次坐标
if (count >= 180 && GetIntData("IsHaveGameScene")==1)
{
    CMClient::getInstance()->VerifyPlayerPos();
    count = 0;
}
```
对应 `M_VerifyPos` / `doPlayerPosVerifyMsg`（`CMClient.cpp:254-276`）。这说明作者**考虑过位置校验**，但战斗数值完全没有类似机制。

**(6) 一个可疑的协议字段用法（留给 JSTM 避坑）。**
```cpp
// CMClient.cpp:519-535  接收怪物攻击
if (msg->towho == -1) towho = ((FightLayer*)ftLayer)->findOtherPlayerIndexByFd(msg->fd);
else                  towho = ((FightLayer*)ftLayer)->findOtherPlayerIndexByFd(msg->towho);
```
但发送端 `MonsterAtk_Msg.fd` **恒为 -1**（`CMClient.cpp:504`），而 `who` 才承载怪物索引（`FightLayer.cpp:769`）。当 `towho == -1`（打自己）时，这里用恒为 −1 的 `fd` 去找玩家索引，语义与发送端不一致。**该分支的补救语义依赖服务端是否回填 `fd`，本仓库无法确认**【待验证】。

> **对 JSTM 的意义**：把服务端做成"仅转发"是不可接受的（JSTM 是服务端权威架构）。本项目可借鉴的是**协议字段的构成方式**——把"打法/目标"与"结果数值"分离，JSTM 应保留 `skill + grade + target` 请求字段，但必须由服务端独自持有 baseAttack/grade 表并回发伤害结果，客户端只做演出。

### 2.3 战斗状态机：PlayerState / PlayerWait / PlayerRun 的真实作用【已确认：不是战斗状态机】

**必须纠正一个常见误读**：`PlayerState`、`PlayerWait`、`PlayerRun` 与战斗无关，它们是**地图场景里主角的待机 ↔ 跑动动画状态**。

```cpp
// PlayerWait.cpp:18-54  —— 只切动画；goNextState 返回 PlayerRun
void PlayerWait::changeAnimation(Dir dir) { ... change("WaitLeft"/"WaitDown"/...) }
PlayerState* PlayerWait::goNextState() { PlayerRun* run = new PlayerRun(...); run->changeAnimation(m_dir); delete this; return run; }
```
```cpp
// PlayerRun.cpp:49-55  —— 反向，goNextState 返回 PlayerWait
PlayerState* PlayerRun::goNextState() { PlayerWait* wait = new PlayerWait(...); ... }
```
切换条件是**路径队列是否为空**，与战斗时序完全无关：
```cpp
// CameraPlayer.cpp:124-138（XGamePlayer::canMove 同理，Player.cpp:118-132）
if (!m_roadList.empty()) { goNext(); if (!m_flag) m_state = m_state->goNextState(); m_flag = 1; return true; }
if (m_flag) m_state = m_state->goNextState();
m_flag = 0; return false;
```
而且**战斗场景里的参战者根本不创建这个状态机**：`XGamePlayer::create(pinfo, flag)` 只有 `flag==0` 时才 `new PlayerWait` 并 `scheduleUpdate`（`Player.cpp:45-52`），而 `FightLayer::initPlayer` 传的是 `1`：
```cpp
// FightLayer.cpp:733-737
Player_Info info = CMClient::getInstance()->findPlayerInfoByFd(var.first);
auto otherplayer = XGamePlayer::create(info, 1);
```

**真正的战斗状态机 = FightLayer 的标志位组**【已确认】：

| 标志（`FightLayer.h:221-233`） | 语义 | 置位/清除位置 |
| --- | --- | --- |
| `m_isPlayer` | 是否轮到玩家一方行动 | 玩家出手后 `false`（`:443`、`:606`、`:567`）；怪物全部出手完 `true`（`:468`、`:469`） |
| `m_isPlayerEnd` | 玩家动作动画是否播完 | `scheduleOnce(...,1.6,"reset")` 置 `true`（`:456-459`）；逃跑失败时直接置 `true`（`:366`） |
| `m_curMonster` | 当前轮到出手的怪物索引 | `monsterAttackPlayer(m_curMonster++)`（`:654`、`:665`、`:675`），越界归零（`:471`） |
| `m_lastMonsterEnd` | 上一只怪物动作是否播完 | `:478` 置 `false`；`:496-499` 1.6 秒后置 `true` |
| `m_otherplayerEnd` | 队友是否结束行为 | `setOtherPalyerEnd()`（`:813-818`）；`SetOtherPalyerAction()` 宏（`:34-41`）伪代码置 `false` |
| `m_otherNoAction` | 队友是否已无法行动 | `OtherPlayerLeave()`（`:807-811`） |
| `m_otherPlayerDie` / `m_isDie` | 队友死亡 / 自己死亡 | `setOtherPlayerDie()`（`:820-824`）、`checkFightEnd()`（`:686-707`） |

分支还受队伍状态影响（`PreProcess.h:127-129` 定义 `P_STATUS_NORMAL/HEADER/MEMBER`）：
```cpp
// FightLayer.cpp:639-682
switch (PlayerTeamStatus())
{
case P_STATUS_HEADER: ... notifyOtherPlayerMonsterAtk(m_curMonster, who); monsterAttackPlayer(m_curMonster++, who); break;  // 队长统一驱动怪物
case P_STATUS_MEMBER: if (m_otherNoAction) ... monsterAttackPlayer(m_curMonster++); break;                                 // 队员跟随
case P_STATUS_NORMAL: ... monsterAttackPlayer(m_curMonster++); break;                                                      // 单人自己驱动
}
```

> **对 JSTM 的意义**：`PlayerState` 这一套（状态对象互相 `goNextState()` 并 `delete this` 交接）**不是**战斗状态机，不要照搬进战斗；可借鉴的是它**"状态对象持有动画资源句柄 + 单向交接"**的写法，用于 JSTM 客户端的移动表现层。战斗时序请借鉴 FightLayer 的显式标志位，或直接设计真正的服务端状态机。

### 2.4 技能系统【已确认】

**(1) 技能类层级**：`Thing`（图标/按钮 + 详情）→ `Skill`（技能图标，持有属性）→ 使用时由 `SkillFactory` 造出 `RealSkill` 家族（纯演出+结算对象）。

**(2) 创建路径。**
```cpp
// Skill.cpp:73-81
float Skill::beUse(cocos2d::CCObject* obj, cocos2d::CCObject* who, cocos2d::CCObject* towho)
{
    FightLayer* pFt = dynamic_cast<FightLayer*>(obj);
    RealSkill* skill = SkillFactory::createSkill(m_name, pFt, towho, m_baseAttack + 30 * m_grade);
    ...
    return skill->getTag();       // 用 tag 回传技能演出时长，供调用方排后续时序
}
```
`SkillFactory::createSkill` 是一串手写 `if-else` 字符串比较（**不是注册表模式**）：
```cpp
// SkillFactory.cpp:12-50  —— 恰好 8 个分支
if (name == "CrackIt") return CrackIt::create(parent, towho, attack);
else if (name=="Dante") ...
else if (name == "DragonRoar") ...
else if (name == "LightStrike") ...
else if (name == "Long") ...
else if (name == "RecallCountermand") ...
else if (name == "SealOfTheBlade") ...
else if (name == "XBArrow") ...
else return nullptr;      // ← 未注册技能直接返回空指针，调用方未判空
```
对应 `Resources/Skill/` 下**恰好 8 个技能目录**（CrackIt / Dante / DragonRoar / LightStrike / long / recallCountermand / SealOfTheBlade / XBArrow）【已确认】。

**(3) 伤害公式与等级影响。**
```cpp
// Skill.cpp:76          技能基础伤害 = baseAttack + 30 × grade
SkillFactory::createSkill(m_name, pFt, towho, m_baseAttack + 30 * m_grade);
// Skill.cpp:88-91       蓝耗 = baseMana + grade × 10
float Skill::getUseMana() { return m_baseMana + m_grade * 10; }
```
`baseAttack` / `baseMana` / `baseupGlod` 来自技能 `.att` 文件。实测 `Resources/Skill/CrackIt/CrackIt.att`：
```
紫焰狼爪
name CrackIt
buyglod 1500
sellglod 750
baseattack 300
basemana 50
baseupglod 500
```
解析见 `Skill.cpp:51-71`（前三个 token 依次读入 `m_name`，最终 `m_name == "CrackIt"`，正好作为工厂 key）。

**等级来源**：`SkillManager::getSkillMap()` 返回 `std::map<std::string,int>`（技能名 → 等级），创建图标时 `skill->setgrade(var.second)`（`FightLayer.cpp:306`、`SkillLayer.cpp:94`）；升级 `incGrade()` 就是 `++m_grade`（`Skill.cpp:83-86`）。

**升级花费**：`getbaseupGlod() + grade × 50`（`SkillLayer.cpp:63-64`），扣钱后 `incGrade()` + `SkillManager::upSkill()`。

**(4) 技能数量上限：代码里没有 `8`。**【已确认】
```cpp
// SkillManager.cpp:25-34  只判重，不判数量
int SkillManager::addSkill(const std::string& name, const int& grade)
{
    auto it = m_skillMap.find(name);
    if (it != m_skillMap.end()) return -1;
    m_skillMap[name] = grade;
    return 0;
}
```
```cpp
// DealLayer.cpp:180-192  购买时也只判重
if (SkillManager::getInstance()->haveSkill(name)) { ...提示...; return; }
else SkillManager::getInstance()->addSkill(name);
```
`SkillManager::skillNumbers()` 存在但**从未被调用**（全仓库 grep 零调用点）。因此 README.md:6 所述"最多可购买八个技能"是**由"恰好存在 8 个技能资源"这一事实形成的隐式上限**，客户端没有任何数量门槛。

**(5) 命中结算集中在各效果类的 `heart()`**，每个类统一按"动画时长 + 命中时刻"两段定时：
```cpp
// 以 DragonRoar.cpp:20-26 为例
Animate* animate = Animate::create(getAnimation("Skill/DragonRoar/DragonRoar"));
this->runAction(animate);
scheduleOnce(schedule_selector(DragonRoar::died), 1.35);   // 演出结束自毁
scheduleOnce(schedule_selector(DragonRoar::heart), 0.8);   // 命中结算
setTag(1.35);                                              // tag 回传时长
```

| 效果类 | 命中结算 | 作用目标 | 动画时长 / 命中时刻 |
| --- | --- | --- | --- |
| `CrackIt` | `beAttack(m_baseattack)` 循环 `m_monsterList` 全部（`CrackIt.cpp:30-37`） | **全体** | 2.5 / 1.2 |
| `SealOfTheBlade` | 同上全体（`SealOfTheBlade.cpp:29-36`） | **全体** | 1.5 / 0.7 |
| `DragonRoar` | `dynamic_cast<Monster*>(m_towho)->beAttack(...)`（`DragonRoar.cpp:31-34`） | 单目标 | 1.35 / 0.8 |
| `Dante` | 同上单目标（`Danate.cpp:41-44`） | 单目标 | 2.6 / 1.3 |
| `Long` | 同上单目标（`Long.cpp:29-32`） | 单目标 | 1.5 / 0.9 |
| `LightStrike` | 目标 + 相邻一只（`LightStrike.cpp:29-50`） | 目标及前/后位 | 1.35 / 0.8 |
| `RecallCounterMand` | 同 LightStrike（`RecallCountermand.cpp:29-50`） | 目标及前/后位 | 2.55 / 1.6 |
| `XBArrow` | 同 LightStrike（`XBArrow.cpp:29-50`） | 目标及前/后位 | 1.35 / 0.8 |

三个"相邻"类用的是同一段 `i % 2` 判断（偶数打 `i` 和 `i+1`，奇数打 `i` 和 `i-1`），实际效果是"目标 + 相邻一只"，命名上（"穿透/横扫"）与实现是能对上的，但**当 `i=0` 且 `size=1` 时只打一只，属于正常边界**。【已确认】

**(6) 蓝量不足时的兜底**：`FightLayer::onSkill` 中 `getcurmana() >= mana` 不成立则提示 `NoMana` 并**自动降级为普通攻击**（`FightLayer.cpp:594-619`）。

**(7) 目标已死时的拦截**：`m_selectedMonster->isDie()` 为真则提示 `NoTarget` 并 `return`（`FightLayer.cpp:588-592`）。

> **对 JSTM 的意义（可借鉴点）**："技能=数据（.att：baseAttack/baseMana/买价/升级价）+ 独立效果类（演出与结算分离）+ 工厂按名分派"是本项目最干净的一处设计，可以直接搬到 JSTM 客户端；但**必须补上 `8` 个技能上限的显式校验**、**工厂 `nullptr` 判空**，并且把 `heart()` 里的伤害结算整体移到服务端。

### 2.5 怪物：属性字段与结算位置【已确认】

**属性字段**（`Monster.h:33-41`）：`attack`、`blood`、`defense`、`speed`、`name`、`exp`、`glod`、`frames`。**没有 `drop`/`dropTable`/`thing` 字段。**

来源是纯文本属性文件 `Resources/Monster/<Name>/<Name>.att`，解析在 `Monster.cpp:48-70`（首个 token 是注释行被丢弃，第二个是中文名，之后每个 `ADD_PROPERTY` 都是"跳过一个 key token、`stof` 下一个 token"，宏定义见 `PreProcess.h:76-79`）。实测 `Ghost.att`：
```
//最后一行为动画帧数
亡灵
attack 250
blood 200
defense 40
speed 5
exp 150
glod 60
frames 6
```
怪物名硬编码在 `GameLogicLayer::monsterName()`（`GameLogicLayer.cpp:182-208`）：map3 = Ghost/BlackDragon/Dragon，map4 = Kougamon/Lion/Minotaur，map5 = Octopus/Pterosaur/SkeletonMaster/TarrasqueMessenger——与 `Resources/Monster/` 下 10 个目录完全对应【已确认】。

**经验/金币结算位置（三段链）**：
```cpp
// ① Monster.cpp:108-117  死亡判定与累加触发
this->m_blood -= hurtvalue;
if (m_blood <= 0) { m_isdie = true; ... removeMonster(this); TaskSystem::...checkKillMonster(this->getname()); }
// ② FightLayer.cpp:531-536  实时累加
void FightLayer::removeMonster(Monster* monster) { m_settlementGlod += monster->getglod(); m_settlementExp += monster->getexp(); monster->setVisible(false); }
// ③ FightLayer.cpp:510-521  战斗结束时一次性发给玩家
GetPlayerData().addGlod(m_settlementGlod); GetPlayerData().addExp(m_settlementExp);
```

**掉落：无。**【已确认】全仓库 grep `drop`/`Dropp` 零命中；击杀只做两件事——累加 exp/glod、`TaskSystem::checkKillMonster` 任务计数（`TaskSystem.cpp:174-184`，仅 `curschedule++`）。物品获取途径只有 Npc 购买/任务奖励（`DealLayer.cpp`、`TaskSystem::submitTask` `TaskSystem.cpp:124-140`）。

**`speed` 字段读了但没用**：战斗时序由标志位推进，`calcActionOrder()` 空实现，所以 `speed` 在战斗链路中无任何使用点（全仓库 grep 仅在 `Monster.h` 声明与 `Monster.cpp:65` 赋值处出现）。【已确认】

**一个明确的逻辑缺陷**：失败也发奖。`EndFight(tip)` 不区分 `tip`，1.6 秒后一律执行 `endFunc()` → `addGlod/addExp`（`FightLayer.cpp:502-521`）。打到一半团灭，已击杀怪物的金币经验照拿。【已确认】

> **对 JSTM 的意义（可借鉴点）**：`.att` 纯文本属性表非常适合作为 JSTM 服务端怪物配置的格式原型（attack/blood/defense/speed/exp/glod/frames 六项 + 帧数，字段命名与 JSTM 的"攻击/生命/防御/速度/经验/金币"一一对应）；**但必须补上掉落表和战斗结算归属**，并把 exp/glod 结算权收归服务端。

### 2.6 伤害飘字 HurtValueLayer 与数值来源【已确认】

```cpp
// HurtValueLayer.cpp:21-33
bool HurtsValueLayer::init(Vec2 pos, float hurt)
{
    if (Layer::init())
    {
        auto label = LabelTTF::create("-" + NumberToString(hurt), "楷体", 25);
        label->setPosition(pos);
        label->setColor(Color3B::RED);
        this->addChild(label);
        scheduleOnce(schedule_selector(HurtsValueLayer::dead), 1);   // 1 秒后自毁
        return true;
    }
    return false;
}
```
它是一个**纯展示组件**：入参 `hurt` 由调用方算好，自身不做任何逻辑。UI 上恒为红色、恒带 `-` 前缀、字号 25、1 秒消失；**没有**暴击/闪避/免疫/未命中的分支表现。

数值来源**全部是本地计算**，三处调用点都是同一个公式的结果：
```cpp
// Monster.cpp:103-107    怪被打
float hurtvalue = attack <= m_defense ? 1 : attack - m_defense;
auto hurtlayer = HurtsValueLayer::createWithInfo(pos, hurtvalue);
// Player.cpp:199-203     队友被打
// CameraPlayer.cpp:232-236  主角被打（扣的是 m_playerData 的 curblood）
```
结合 2.2 的结论（协议无伤害字段），可确定：**飘字数值 = 接收端本地用 `攻击 − 防御` 算出的结果，不是服务端下发的字段**。最小伤害保底为 `1`（`attack <= defense` 时）。

> **对 JSTM 的意义**：组件本身极其简单，可原样借鉴（`createWithInfo(pos, hurt)` 的接口形态很实用）；**但数值应改为服务端下发**，并预留暴击/闪避标记位，否则 JSTM 的伤害表现会缺少这些维度。

### 2.7 组队战斗：TeamFight_Msg 全流程【已确认】

```
[队长客户端] GameLogicLayer::update → randomMeetMonster()
              → SetIntData("IsEntryFight",1) / MonsterNums / MonsterName   （本地标记，打自己）
              → checkTeamEntryFight(name, nums)
                  → 对每个队员 CMClient::sendTeamFightMsg(var.first, name, nums)   GameLogicLayer.cpp:224-233
        ↓ 消息经服务端按 dest 转发
[队员客户端] CMClient::OnRecv → doTeamFightMsg(msg)                            CMClient.cpp:479-487
              → SetIntData("IsEntryFight",1); SetIntData("MonsterNums",msg->nums); SetStringData("MonsterName",msg->name)
[所有客户端] GameLogicLayer::update → checkEntryFight()                        GameLogicLayer.cpp:235-257
              → 红屏 0.2s → FightLayer::createFightScene(MonsterName, MonsterNums)
              → randomNumMonster 按"名字 + 数量"各自本地生成怪物（位置是确定性公式，FightLayer.cpp:178-198）
```
关键点：`TeamFight_Msg` **只传怪物名和数量**（`ShareData.h:203-216`），**不传怪物个体属性、不传战斗种子、不传伤害**。因此所谓"组队战斗"是**各客户端用同一份 .att 文件独立模拟同一个战斗**，靠"相同的输入文件 + 相同的确定性生成公式"保持画面一致。

**怪物行动的组队同步**由队长单方面驱动：
```cpp
// FightLayer.cpp:765-771  只有队长会走这里（调用点见 :644-657 的 P_STATUS_HEADER 分支）
void FightLayer::notifyOtherPlayerMonsterAtk(int who, int towho)
{
    for (auto var : TeamManager::getInstance()->getTeamMembers())
        CMClient::getInstance()->sendMonsterAtkMsg(var.first, who, towho == -1 ? -1 : m_otherPlayers[towho]->getFd());
}
```
**其他玩家的攻击演出与结算**：
```cpp
// FightLayer.cpp:742-763
if (skill == "null") delay = var->normalAttack(m_monsterList[towho]);      // 普攻
else                 delay = var->skillAttack(skill, grade, m_monsterList[towho]);   // 技能
scheduleOnce(func2, delay, "otherend");     // 等演出结束再 setOtherPalyerEnd()
```
```cpp
// Player.cpp:211-234   XGamePlayer::normalAttack / skillAttack —— 依旧是本地 beAttack
((Monster*)who)->beAttack(this->getAttack());
// skillAttack 里重建 Skill 对象：SkillFactory 的 m_name 来自技能名 + 等级
```
客户端约定：**`skill == "null"` 表示普通攻击**（`FightLayer.cpp:440` 发送、`:749` 判断），服务端只是把这串字符原样转发。

**队伍人数**：`TeamManager.h:9` 注释写"暂时队伍人数上限为2个"，实现是 `std::map<int,int> m_teamMembers`，`createTeam` 只插入一个成员且无任何数量校验（`TeamManager.cpp:13-17`）。队长身份在收到同意组队消息时确立（`CMClient.cpp:416-423`）。注释与代码是否一致【待验证】。

> **对 JSTM 的意义（可借鉴点）**：`TeamFight_Msg` 的"只有 `name` + `nums`"是非常典型的**客户端各自模拟**做法，JSTM **不能**照搬；但"队长驱动怪物行动、队员跟随"这一职责划分值得保留，改为服务端驱动即可。协议里 `dest`（目标玩家 fd）这一"点对点转发"字段设计可以借鉴为 JSTM 的定向战斗消息。

### 2.8 逃跑机制与 `sendPlayerRunMsg` 的 flag【已确认】

```cpp
// FightLayer.cpp:340-375
void FightLayer::onRunClickCallBack(cocos2d::CCObject * sender)
{
    if (m_isDie) return;
    if (PlayerTeamStatus() == P_STATUS_HEADER)      // 队长不许逃
    { ... TipLayer(StringValue("RunFailed")); return; }
    if (m_isPlayer && m_otherplayerEnd)
    {
        std::random_device rand;
        SetOtherPalyerAction();
        m_isPlayer = false;
        if (rand() % 100 < 40)                       // ← 40% 成功率
        {
            unscheduleUpdate();
            notifyOtherPlayerRunAway(1);             // flag = 1 成功
            EndFight("RunSuccessText");
        }
        else
        {
            notifyOtherPlayerRunAway(0);             // flag = 0 失败
            ... TipLayer(StringValue("RunFailed"));
            m_isPlayerEnd = true;                    // 让怪物继续出手
            m_timeLabel->setVisible(false); m_arrow->setVisible(false);
        }
    }
    else NoAction();
}
```
- **成功率 40%，硬编码，与等级/速度/装备无关。**【已确认】
- **队长禁止逃跑**（`P_STATUS_HEADER`），单人（`P_STATUS_NORMAL`）和队员可以。
- `flag` 语义：`1` = 逃跑成功，`0` = 逃跑失败；定义见 `ShareData.h:247-260` 与 `FightLayer.h:68-72` 注释。
- 接收侧：
```cpp
// FightLayer.cpp:793-805
void FightLayer::OtherRunAway(int flag)
{
    if (flag) { this->removeChild(m_otherPlayers[0]); m_otherPlayers.clear(); OtherPlayerLeave(); }   // 队友逃走→离场
    else        setOtherPalyerEnd();                                                                  // 失败→继续等他
}
```
- 逃跑成功会 `unscheduleUpdate()` **停掉整个逐帧战斗循环**（`FightLayer.cpp:357`），再走 `EndFight` → `endFunc`。注意 `endFunc` 无条件发奖，所以**逃跑成功也会拿到已击杀怪物的金币经验**（与 2.5 的"失败也发奖"是同一处代码）。
- 服务端如何处理该 flag（是否校验"队长不能逃"、是否广播给非队友）**未读到**【未知】。

> **对 JSTM 的意义**：40% 固定概率、队长不能逃，这两个规则可以直接作为 JSTM 逃跑逻辑的基线；但概率必须移到服务端随机，否则客户端可反复重试刷成功。

### 2.9 寻路 FindRoad 与战斗/移动的关系【已确认】

**FindRoad 是 A\* 实现，只服务于地图移动，与战斗完全解耦。**

地图移动调用链：
```
GameLogicLayer::onTouchEnded (GameLogicLayer.cpp:32-52)
  → CameraPlayer::moveTo(targetPos)                          CameraPlayer.cpp:269-291
      → FindRoad fdroad(startPos, targetPos, GetMapInfo(), MapCountX, MapCountY); fdroad.lessOne(less); fdroad.ExecuteAStar();
      → 有路: CMClient::SendMoveToMsg(tmp, less) 广播 + setMoveRoad(fdroad.GetRoadList())
  → CameraPlayer::update: PlayerCanMove() → goNext() → trunDir() 走向路点   CameraPlayer.cpp:107-138
他人同步：doPlayerMoveToMsg → ObjectLayer::moveOtherPlayer → XGamePlayer::moveTo 同样跑一遍 A*（ObjectLayer.cpp:257-266）
```
A\* 实现细节（`FindRoad.cpp:32-155`）：
- 8 方向邻接（`dir[][2] = {{1,0},{-1,0},{0,1},{0,-1},{1,-1},{-1,1},{1,1},{-1,-1}}`，`FindRoad.cpp:35`）
- 代价 `g = 父g + 1`（含斜向，未做 √2 修正），启发 `h = 欧氏距离`（`FindRoad.cpp:100-103`），`f = g + h`
- 可行走判定：格值为 `0` 或 `-100`（`FindRoad.cpp:89-98`）
- 从 openList 线性找最小 `f`（`FindRoad.cpp:129-140`，非优先队列）
- `lessOne(1)` 的"少走一格"：`GetRoad()` 中 `less == 1 ? less = 0 : m_roadList.push(...)`（`FindRoad.cpp:142-150`），机制上是**用 `less` 自置 0 来跳过一次 `push`**（只生效一次），而不是缩短距离。
  **本轮已定论**【已确认】：`less=1` 在全仓库只有两个调用点，且两处都是"走向另一个玩家"——
  ```cpp
  // CMClient.cpp:434-437   队员收到队长移动广播后跟随
  void CMClient::doTeamMoveMsg(TeamMove_Msg* msg)
  { CameraPlayer::getPlayerInstance()->moveTo(Vec2{ msg->x,msg->y }, 1); }
  // TeamMsgItem.cpp:76     同意组队后走向邀请者
  CameraPlayer::getPlayerInstance()->moveTo((*it)->getWorldPos(), 1);
  ```
  队长自己移动用默认值 `less=0`（`GameLogicLayer.cpp:44`），只有跟随者/靠近者用 `less=1`。结合 `-100` 是门格（`MapInfo.cpp:67-73`）且 `FindRoad` 把 `-100` 判为可走（`FindRoad.cpp:93`），可判定其设计目的是"**跟随与靠近他人时停在目标前一格，避免两人占据同一格**"（机制已确认；"避免重叠"这一用途是结合两处调用点作出的推断）。

**与战斗的关系：FightLayer 完全不使用 FindRoad。** 战斗场景中的位移全部是写死的 `MoveTo` 动作：
```cpp
// FightLayer.cpp:446-450   玩家冲向怪物
Vec2 dest = m_selectedMonster->getPosition(); dest.x += 20; dest.y -= 40;
m_player->runAction(MoveTo::create(0.5, dest));
// FightLayer.cpp:479-487   怪物冲向目标
dest.x -= 20; dest.y += 40;
m_monsterList[index]->runAction(MoveTo::create(0.5, dest));
```
怪物站位也由确定性网格公式生成，与地图无关：
```cpp
// FightLayer.cpp:183-190
float x = i % 2; float y = i / 2;
monster->setPosition(140 * x + basePos.x, y * 200 + basePos.y);   // basePos = (80, 屏幕中心-100)
```
另外，**随机遇怪也完全在客户端**：`GameLogicLayer::randomMeetMonster()` 每帧计数，`interval > 5` 后 `rand()%100 < 2` 触发遭遇，怪物数量 `rand()%4 + 1`（`GameLogicLayer.cpp:155-180`），且只在 `CurMap >= LEVEL_THREE` 生效。这意味着**服务端不决定何时遇敌、不决定遇几只、不决定是什么怪**。

> **对 JSTM 的意义（可借鉴点）**：A\* 是通用算法，JSTM 可按其**思路自行实现**（含 `lessOne` 这类"贴近目标点"的小技巧）；但**遇敌（暗雷）与怪物生成必须移到服务端**，否则 JSTM 的挂机/反作弊无从谈起。

### 2.10 装备与等级如何构建 attack/defense（伤害公式的输入端）【已确认】

§2.2 证明了"伤害在客户端算"。本节补齐更根本的一环：**参与 `攻击 − 防御` 的两个数字本身也是客户端累加出来、再广播出去的**。

**完整链路（7 步）**

1. **基础值**来自登录选角时对 MySQL `playerinfo` 表的查询（`SelectLayer.cpp:100` `DBDao<PlayerInfo>`），写入 `PlayerData`。
2. **人物升级**：`PlayerData::upGrade()` → `addProperty(30, 30, 5, 5)`（`PlayerData.cpp:58-66`）——每级 +5 攻 / +5 防 / +30 血 / +30 魔。
3. **装备穿戴**：`EquipMent::beUse()`（`EquipMent.cpp:74-85`）
```cpp
EquipmentManager::getInstance()->wearEquipment(info);
GetPlayerData().addProperty(m_addblood + (m_grade-1)*30, m_addmana + (m_grade-1)*30,
                            m_addattack + (m_grade-1)*8, m_adddefense + (m_grade-1)*8);
```
4. **装备升级**：`EquipMent::upgrade()` → `addProperty(30, 30, 8, 8)`（`EquipMent.cpp:105-114`）——装备每级 +8 攻 / +8 防。
5. **拆卸**：`EquipMent::Disassemble()` 用与第 3 步**完全相同的公式减回去**，并把装备退回背包（`EquipMent.cpp:87-103`）。
6. **广播**：`PlayerData::addProperty()` 的最后一行是 `CMClient::getInstance()->updatePlayerData();`（`PlayerData.cpp:68-75`）——把客户端自己算出的 attack/defense/blood/mana/grade 上报服务器，再由服务器转给其他玩家（`doPlayerDataUpdaeMsg`，`CMClient.cpp:291-306`）。
7. **被他人使用**：别人打你时，用的就是你这台上报的防御值（`FightLayer.cpp:490-492` → `Monster.cpp:103`）。

⇒ **从基础值到最终 attack/defense，全程由客户端计算并上报，没有任何服务端校验。** 这是"客户端权威"在数值层的完整闭环，比 §2.2 的消息层证据更根本——只要改本地 `PlayerData`，对手那边看到的伤害就会跟着变。

**装备槽位与替换规则（5 槽）**：`EM_HEAD 1005` / `EM_WEPON 1006` / `EM_JEWELRY 1007` / `EM_CLOTH 1008` / `EM_FOOT 1009`（`PreProcess.h:109-113`，与 README.md:5 的"头盔、装甲、首饰、武器、鞋子"一致）。`wearEquipment` 按 `type` 找同槽旧装备，先把旧的 `Disassemble(nullptr)`（退回背包并扣掉旧加成），再写入新装备（`EquipmentManager.cpp:17-33`）。界面槽位映射见 `RoleInfoLayer::initRoleEquipment`（`RoleInfoLayer.cpp:176-206`）。

**装备升级费用**：`EquipMent::upGlod()` = `m_baseupglod + m_grade*(100 + m_baseupglod/10)`，其中 `m_baseupglod = addblood + addmana + addattack*10 + adddefense*10` 在 `init()` 中算出（`EquipMent.cpp:45`、`:156-159`）。即**升级价与装备强度线性挂钩**，本身是自洽的设计。

**本轮新发现的三个具体缺陷（可直接指回代码）**

| 缺陷 | 位置 | 说明 |
| --- | --- | --- |
| 对已失效迭代器解引用 | `EquipmentManager.cpp:51-58` | `m_emlist.erase(it);` 之后才 `deleteEm(*it);`——**erase 后再用 `it`**，是明确的未定义行为 |
| 装备等级记录与实际加成不一致 | `EquipmentManager.cpp:27` | 换装分支把新装备写成 `it->grade = 1`，但本次加成用的是新对象实参的 `m_grade`（`:81`）；重登后 `readEquipmentInfo()` 会按 1 级复原 |
| `m_addspeed` 永远不生效 | `EquipMent.cpp:69`、`:81`、`PlayerData.h:58` | 属性文件读了 `speed`，但 `addProperty` 只有 4 个形参（blood/mana/attack/defense），**速度加成从未被应用**。与 §2.5 怪物 `speed` 无人使用相互印证 |

> **对 JSTM 的意义（设计层）**：值得借鉴的是它"**属性一变更就立刻广播**"的同步时机（`PlayerData.cpp:74`）——JSTM 可以保留这个时机，但把计算端从客户端换成服务端：客户端只上报"要穿哪一件 / 要升哪一级"，服务端查表算出新属性再下发。三个缺陷则应当作为反例，逐条避免。

### 2.11 数值配置全表：8 技能 / 10 怪物 / 15 装备 / 3 药品【已确认】

本轮把全部 `.att` 数值表读完（完整表格见 **附录 A / B / C**）。关键观察：

- **8 个技能**（附录 A）：`baseattack` 100～350、`buyglod` 1000～1700、`baseupglod` 500～720、动画帧数 9～17。
  **`basemana` 全部等于 50**（8/8 完全一致）——说明**蓝耗的区分度完全依赖 `+grade×10` 这一项**，技能之间没有基础蓝耗差异。
- **10 只怪物**（附录 B）：`attack` 100～300、`blood` 200～700、`defense` 40～120、`exp` 100～300、`glod` 30～100、`frames` 5～12。
  **`speed` 全部等于 5**（10/10 完全一致）——这是"`speed` 字段根本没被使用"的**比 grep 更硬的证据**：作者填属性时只是把这一列统一写了 5，因为战斗时序由标志位而非速度决定（§2.1、§2.5）。
- **15 件装备**（附录 C）：`attack` 0～25、`defense` 0～20、`blood` 0～200、`mana` 0～200、`speed` −2～5。
  5 个槽位**每槽恰好 3 件**（头盔/武器/首饰/装甲/鞋子各 3），玩家满配 5 件，是从 15 件中选 5 件的浅度构筑。
  装备的 `speed` 有 `-2`/`1`/`5` 等取值，但同样**从未生效**（见 §2.10 第三个缺陷），与怪物 `speed` 是同一类死字段。
- **3 种药品**（附录 C）：红瓶 100 金币回 100 血、蓝瓶 100 金币回 100 魔、"不知道" 200 金币回 100 血 + 100 魔。
- **权威商品清单**在 `Resources/DealThing/*.dt`：`Skill.dt` 恰好 8 条（= 8 个技能）、`EquipMent.dt` 15 条、`Medication.dt` 3 条。**这三个文件与 SkillFactory 的 8 个分支、`Resources/Skill` 的 8 个目录三方一致**，共同构成"8 技能上限"的事实来源（§2.4）。

> **对 JSTM 的意义**：这些数值表是现成的**配置表结构参考**——字段少、语义直白、纯文本可读，适合作为 JSTM 服务端"技能表 / 怪物表 / 装备表 / 道具表"的字段设计起点。但数值本身（尤其 `basemana` 全为 50、`speed` 全为 5）说明原项目的数值平衡几乎未做，JSTM 应只取其**表结构**，数值需自行重做。

### 2.12 资源路径大小写陷阱：技能动画在两处对不上【已确认】

技能动画在启动时统一预加载，键名由 GameData.xml 的目录映射拼出：
```cpp
// AppDelegate.cpp:175-184
std::string skill[] = { "CrackIt","Dante","DragonRoar","LightStrike",
                        "Long","RecallCountermand","SealOfTheBlade","XBArrow" };
int nums[] = { 16,14,9,9,10,17,15,9 };
for (int i = 0; i < 8; ++i)
    RealSkill::loadAnimation(StringValue(skill[i]) + skill[i], nums[i], 0.15);
```
`RealSkill::loadAnimation` 会按 `名字 + 帧号 + ".png"` 逐帧加载（`RealSkill.cpp:20-33`）；技能图标路径也是同一套拼法（`FightLayer.cpp:300-305`、`SkillLayer.cpp:86-89`）。

而 `GameData.xml` 给出的映射是**大写开头**，磁盘上的目录与帧文件却是**小写**：

| 技能 | GameData.xml 映射 | 代码拼出的路径 | 磁盘实际 | 是否一致 |
| --- | --- | --- | --- | --- |
| `CrackIt` | `Skill/CrackIt/` | `Skill/CrackIt/CrackIt1.png` | `Skill/CrackIt/CrackIt1.png` | ✅ |
| `Dante` / `DragonRoar` / `LightStrike` / `SealOfTheBlade` / `XBArrow` | `Skill/Xxx/` | 同形 | 同形 | ✅ |
| **`Long`** | `Skill/Long/` | `Skill/Long/Long1.png` | **`Skill/long/long1.png`** | ❌ 目录与文件名都差大小写 |
| **`RecallCountermand`** | `Skill/RecallCountermand/` | `Skill/RecallCountermand/RecallCountermand1.png` | **`Skill/recallCountermand/recallCountermand1.png`** | ❌ 目录与文件名都差大小写 |

⇒ Windows（大小写不敏感）上能跑通；**在 Android / iOS / Linux（大小写敏感）上，`Long` 与 `RecallCountermand` 两个技能的动画与图标会加载失败**。
旁证：README.md:9 明确写了作者尝试打包 APK 时"定义了太多宏在打包时产生了一些莫名的 error"——**这个大小写不一致是一个具体、可修的跨平台地雷**，而且只影响 8 个技能中的 2 个，症状会是"部分技能放不出来/图标空白"，很容易被误判为打包问题。

对照：怪物资源路径 `StringValue("Ghost")` → `Monster/Ghost/Ghost`，与磁盘目录大小写**10 只全部一致**（`GameData.xml` 中 10 条 `Monster/...` 映射逐条核对）。所以问题只集中在技能这一处。

> **对 JSTM 的意义**：这是纯粹的**资源命名规范教训**——JSTM 客户端应统一"目录名 = 资源前缀 = 代码常量"的大小写，并在 CI 里加一条大小写一致性检查（在 Windows 上开发天然发现不了）。

---

## 3. 证据总表

> 路径均相对 `C:\WINDOWS\TEMP\audit_chiv\`。所有行均为一次性阅读的静态结论，**未运行程序**；凡涉及引擎库行为、运行时表现、服务端实现的结论一律标【待验证】或【未知】。

### 3.1 战斗核心

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/FightLayer.cpp` | `FightLayer::init` | 【已确认】`schedule(onTimer, 1)` 起 1 秒行动条 tick + `scheduleUpdate()` 起逐帧循环；建 5 个动作按钮（自动/手动切换、药品、技能、逃跑、普攻，`:91-121`）；血魔条用 `ProgressTimer`；若 `IsAuto==1` 则走自动档 | 适合 | 可借鉴点：**"行动条 tick + 逐帧循环"分离**的调度结构，以及"手动 10 秒 / 自动 2 秒"两档托管时间。这是 JSTM 做挂机战斗的现成参考 |
| `Classes/FightLayer.cpp` | `FightLayer::update` | 【已确认】`:200-205` 逐帧做三件事：更新血魔条、推进怪物行为、判定战斗结束。**战斗主循环的唯一入口** | 适合 | 可借鉴点：主循环职责切分清晰，便于 JSTM 改为"向服务端拉取战斗帧结果" |
| `Classes/FightLayer.cpp` | `FightLayer::onTimer` | 【已确认】`:410-432` 每秒 `m_timeLabel` 减 1；减到 0 时若未选技能则普攻、否则放最后一次选中的技能。**超时托管即"自动战斗"** | 适合 | 可借鉴点：超时默认动作 = 挂机体验核心；不适合直接照搬的地方是它把决策放在客户端定时器里，服务端无法感知 |
| `Classes/FightLayer.cpp` | `FightLayer::playerAttackMonster` | 【已确认】`:434-462` 组队时先给每个队友发 `sendPlayerAtkMsg("null",0,...)`；然后 `scheduleOnce(0.7)` 在冲上去的瞬间调用 `m_selectedMonster->beAttack(GetPlayerData().getattack())`（**本地结算**）；`scheduleOnce(1.6)` 置 `m_isPlayerEnd` | 不适合（作为权威） | 不适合原因：**伤害本地算**。可借鉴点：`skill=="null"` 表示普攻的协议约定、以及"位移 0.5s + 命中 0.7s + 收招 1.6s"的时序骨架 |
| `Classes/FightLayer.cpp` | `FightLayer::monsterAttackPlayer` | 【已确认】`:464-500` 越界时把回合交还玩家（`:466-475`）；否则怪物 `MoveTo` 冲向目标，0.7s 时 `AttackPlayer(怪物attack)`（打主角）或 `XGamePlayer::beAttack(怪物attack)`（打队友）——**均为本地结算**；1.6s 后 `m_lastMonsterEnd=true` 放行下一只 | 不适合（作为权威） | 不适合原因同上（本地算伤害、客户端决定怪物出手）。可借鉴点：用"动画完成回调"驱动回合推进，是 Cocos 下最省事的时序方案 |
| `Classes/FightLayer.cpp` | `FightLayer::checkMonsterBehavie` | 【已确认】`:639-682` 按 `PlayerTeamStatus()` 分三种驱动模式：**队长**负责广播 `sendMonsterAtkMsg` 并本地推进；**队员**仅在 `m_otherNoAction` 时跟随；**单人**自己推进 | 适合（改造后） | 可借鉴点：**"队长驱动怪物行动、队员跟随"的职责划分**在服务端化后依然成立；不适合原样用，因为驱动方是客户端 |
| `Classes/FightLayer.cpp` | `FightLayer::checkFightEnd` | 【已确认】`:684-713` `getcurblood()<=0` 时单人直接 `EndFight("FightFailed")`，组队则先 `sendPlayerDieMsg` 再据 `m_otherPlayerDie/m_otherNoAction` 决定是否结束；`checkSuccess()` 全怪死亡则 `EndFight("FightSuccess")` | 适合 | 可借鉴点：**结束判定的三条分支（自己死/队友死/怪清空）**和"组队才通告死亡"的处理顺序；不适合的地方是它只看本地血量 |
| `Classes/FightLayer.cpp` | `FightLayer::EndFight` / `endFunc` | 【已确认】`:502-521` `unscheduleAllCallbacks()` 后 1.6s 执行 `endFunc`；`endFunc` **无条件** `addGlod(m_settlementGlod)`、`addExp(m_settlementExp)`，再切回 `GameScene`。**失败/逃跑也发奖** | 不适合 | 不适合原因：**奖励发放与胜负解耦**，这是明确缺陷，JSTM 必须按胜负决定是否结算。可借鉴点：结算 UI（`Glod+X,Exp+Y` 提示）与场景回退的时序 |
| `Classes/FightLayer.cpp` | `FightLayer::onRunClickCallBack` | 【已确认】`:340-375` 队长禁止逃；`rand()%100<40` 判成功；成功则 `unscheduleUpdate()` + `notifyOtherPlayerRunAway(1)` + `EndFight`；失败则 `notifyOtherPlayerRunAway(0)` 且继续挨打 | 适合（改造后） | 可借鉴点：**40% 固定成功率、队长不可逃**两条规则；不适合的地方是随机数在客户端（可重试刷成功） |
| `Classes/FightLayer.cpp` | `FightLayer::calcActionOrder` | 【已确认】`:207-210` **空函数体，且全仓库零调用**。原计划计算行动顺序 | 不适合 | 不适合原因：无实现、无调用，是纯残留；仅可作为"作者原意是回合制"的旁证 |
| `Classes/FightLayer.cpp` | `MonsterEndBehavie()` 宏 | 【已确认】`:43` 定义了"怪物全出手完则交还玩家回合"的宏，但**全仓库从未使用**（逻辑被内联写进 `monsterAttackPlayer` 的越界分支） | 不适合 | 不适合原因：死代码；可借鉴点是它把"回合交接"意图显式表达出来，JSTM 反而应该真的抽成函数 |
| `Classes/FightLayer.h` | `m_mmor`（回合数）/ `m_time` | 【已确认】`:206` `m_time = "10"` 行动时间；`:227` `m_mmor = 1` 注释"纪录回合数"，但 `m_mmor` **全仓库零引用** | 适合（`m_time`）/ 不适合（`m_mmor`） | 适合原因：`m_time` 的"行动时间"概念可直接对应 JSTM 战斗回合时限；不适合原因：`m_mmor` 是未完成的回合计数，本应有而实际没有 |
| `Classes/FightLayer.h` | `m_isPlayer` / `m_isPlayerEnd` / `m_curMonster` / `m_lastMonsterEnd` / `m_otherplayerEnd` 等 8 个标志 | 【已确认】`:221-233` 这套布尔/计数标志**才是真正的战斗状态机**（切换条件见 2.3） | 适合 | 可借鉴点：**用显式标志位表达战斗时序**，比状态对象更适合战斗这种短时序强耦合的场景；JSTM 可在此基础上加服务端同步位 |

### 3.2 协议层与网络

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/ShareData.h` | `enum M_Type` | 【已确认】`:6-31` 23 个消息类型，战斗相关 5 个：`M_TeamFight`、`M_MonsterAtk`、`M_PlayerAtk`、`M_PlayerRun`、`M_UseMedication`、`M_PlayerDie`；类型枚举是每个包的前 4 字节 | 适合 | 可借鉴点：**"消息类型枚举占包头"**的极简设计，可直接映射为 JSTM 的 opcode；协议字段命名（`who/towho/dest`）清晰可读 |
| `Classes/ShareData.h` | `PlayerAtk_Msg` | 【已确认】`:232-245` 字段仅 `type/skill[30]/grade/fd/dest/towho`——**无伤害字段**；构造函数自动置 `type=M_PlayerAtk` | 适合（字段设计） | 可借鉴点：`skill` 字符串 + `grade` + `towho` 的请求三元组；**不适合**照搬"不传结果"的做法，JSTM 服务端必须回发伤害 |
| `Classes/ShareData.h` | `MonsterAtk_Msg` | 【已确认】`:218-230` 字段仅 `type/fd/dest/who/towho`——无伤害、无血量；`who` 是怪物索引，`towho` 是目标 fd（`-1` 表示打自己） | 适合（字段设计） | 可借鉴点：`who/towho` 双端寻址；不适合原因同上一行 |
| `Classes/ShareData.h` | `PlayerRun_Msg` | 【已确认】`:247-260` `fd/dest/flag`，构造函数把 `fd`、`dest` 初始化为 `-1`，`flag` 由调用方填（1 成功 / 0 失败） | 适合 | 可借鉴点：**用 `flag` 区分逃跑成败的单字段设计**很省事；JSTM 应把 flag 的产生放服务端 |
| `Classes/ShareData.h` | `TeamFight_Msg` | 【已确认】`:203-216` 仅 `name[20] + fd + dest + nums`，**不传怪物属性/种子** | 不适合 | 不适合原因：字段太少，导致"各客户端自行生成同一场战斗"（见 2.7），服务端无法校验战斗过程。JSTM 需要战斗 ID + 怪物实例列表 |
| `Classes/ShareData.h` | `Player_Info` / `InitData_Msg` / `UpdateData_Msg` | 【已确认】`:33-62`、`:116-125` 玩家属性广播：`blood/mana/attack/defense/curmap/grade/x/y/fd`。这是**战斗数值的唯一跨端来源**（各客户端据此本地算伤害） | 适合（字段） | 可借鉴点：属性字段集合可作为 JSTM 角色同步包的基础；不适合原因：属性可被客户端任意伪造（`updatePlayerData` 由客户端主动上报，`PlayerData.cpp:68-75`） |
| `Classes/CMClient.cpp` | `CMClient::OnRecv` | 【已确认】`:36-111` 用 `M_Type type = *((M_Type*)buff)` 取包头，`switch` 分发到 20 个 `do*` 处理函数；`CLOSE_MESSAGE` 特判直接弹框退出 | 适合 | 可借鉴点：**"包头即类型 + 直接 `reinterpret_cast` 结构体"** 的极简协议；不适合原因：**没有长度字段、没有版本号、没有分包/粘包处理**，`recv` 一次就当一包（见下一行） |
| `Classes/TCPClient.cpp` | `CTCPClient::DoServerMsg` | 【已确认】`:87-121` 独立 `std::thread` 阻塞 `recv`，**每次 `recv` 到的 `buff` 直接当作一条完整消息**回调 `OnRecv` | 不适合 | 不适合原因：TCP 是字节流，**无长度前缀必然粘包/拆包**，本项目靠"结构体内存布局 + `BUFF_SIZE=1024` 固定上限"侥幸工作。JSTM 应改为"长度前缀 + protobuf 或定长结构" |
| `Classes/TCPClient.cpp` | `CTCPClient::SendMsg` | 【已确认】`:55-63` 裸 `send(m_sockServer, buff, len, 0)`，失败仅记 `m_Error` | 不适合 | 不适合原因：无重试、无发送队列、无加密；`m_Error` 是赋值而非追加【已确认】 |
| `Classes/CMClient.cpp` | `sendPlayerAtkMsg` | 【已确认】`:489-498` 填 `fd=-1, grade, dest, skill, towho` 后 `SendMsg`。**调用点只有两处且都在组队分支内**（`FightLayer.cpp:440`、`:602`）——单人战斗**完全不走网络** | 适合（改造后） | 可借鉴点：请求包字段构成（用哪招、几级、打谁）；不适合原因：**单人战斗零联网**意味着服务端对单人战斗一无所知 |
| `Classes/CMClient.cpp` | `doPlayerAtkMsg` | 【已确认】`:510-517` 取 `FightLayer` 后调 `otherPlayerAtk(msg->fd, msg->skill, msg->grade, msg->towho)`，**由收方本地重算伤害** | 不适合 | 不适合原因：典型"客户端权威"。可借鉴点：`findChildByName("FightLayer")` + `dynamic_cast` 的场景分派写法 |
| `Classes/CMClient.cpp` | `sendMonsterAtkMsg` / `doMonsterAtkMsg` | 【已确认】`:500-508` 发送时 `fd=-1`、填 `dest/who/towho`；`:519-535` 接收时把 `towho` 换算成本地 `m_otherPlayers` 下标再调 `monsterAttackPlayer`。**`towho==-1` 分支却去查 `msg->fd`（恒为 -1）**【待验证】 | 不适合 | 不适合原因：字段语义不自洽（见 2.2(6)）。JSTM 应显式区分"打自己/打队友/打全体" |
| `Classes/CMClient.cpp` | `sendPlayerRunMsg` / `doPlayerRunMsg` | 【已确认】`:537-552` 透传 `dest/flag`，接收侧直接 `OtherRunAway(flag)` | 适合 | 可借鉴点：逃跑结果用单字段广播，实现极简；需服务端化以杜绝重试刷成功 |
| `Classes/CMClient.cpp` | `sendUseMedicationMsg` / `doUseMedicationMsg` | 【已确认】`:554-566` 消息**只带 `dest`**，连药品名和回血量都没有；接收侧只调 `setOtherPalyerEnd()`（表示"对方用完药了，继续"） | 不适合 | 不适合原因：`UseMedication_Msg` 无法承载任何数值，服务端完全无法校验用药合法性（真实回血在 `Medication::beUse`，`Medication.cpp:67-78`，纯本地） |
| `Classes/CMClient.cpp` | `sendPlayerDieMsg` / `doPlayerDieMsg` | 【已确认】`:568-579` 只带 `dest`；接收侧 `setOtherPlayerDie()` 置位 | 适合 | 可借鉴点："死亡只通告、不传值"的轻量设计；需服务端判定死亡 |
| `Classes/CMClient.cpp` | `sendTeamFightMsg` / `doTeamFightMsg` | 【已确认】`:470-487` 发送 `dest+name+nums`；接收只写 `IsEntryFight/MonsterNums/MonsterName` 三个动态数据键，**不做任何校验** | 不适合 | 不适合原因：无战斗 ID、无参战者列表；任何客户端都能伪造 `TeamFight_Msg` 让自己进战斗 |
| `Classes/CMClient.cpp` | `CMClient::readConfConnectServer` | 【已确认】`:113-131` 从 `StringValue("ServerConf")` 读配置，**连续三次 `fin >> m_serverip`**（依次吃掉注释行、`serverIp` 键、真实 IP），再 `fin >> tmp >> m_port`。实测 `Resources/server.cfg` 为 `//服务器配置文件` / `serverIp 192.168.229.128` / `port 6036`，正好对上 | 适合 | 可借鉴点：**硬编码索引的读取方式**说明 `server.cfg` 格式必须严格固定（注释行不能删）；不适合原因：三次读同一变量非常脆弱，JSTM 应改成 `key value` 解析 |
| `Classes/public.h` | `PORT` / `BUFF_SIZE` / `CLOSE_MESSAGE` | 【已确认】`:5-6` `PORT 6036`、`BUFF_SIZE 1024`；`:27-28` 关闭/连接哨兵字符串 `~#@**close**@#~`、`~#@**connect**@#~` | 适合 | 可借鉴点：**用特殊字符串表示连接控制事件**（避免额外消息类型）是小巧设计；`BUFF_SIZE=1024` 同时是单包上限，JSTM 若沿用需注意长包 |
| `Classes/CMClient.cpp` | `CMClient::VerifyPlayerPos` / `doPlayerPosVerifyMsg` | 【已确认】`:254-276` 客户端每 9 秒上报坐标（触发点 `AudioSystem.cpp:45-49`）；服务端可下发 `VerifyPos_Msg` 强制回正位置，客户端把它写进 `ObjectLayer::verifyPlayerPos` | 适合 | 可借鉴点：**"客户端定期上报 + 服务端下发纠正"** 的位置同步范式，正是 JSTM 需要的双向校验思路，可扩展到战斗数值。注意 `doPlayerPosVerifyMsg` 的循环条件写成 `var!=m_playerlist.begin()`（`CMClient.cpp:256`）——**疑似 bug，应为 `end()`**【已确认】 |

### 3.3 技能系统

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/Skill.cpp` | `Skill::beUse` | 【已确认】`:73-81` 从 `FightLayer` 造 `RealSkill`，**伤害入参 = `m_baseAttack + 30 * m_grade`**，返回 `skill->getTag()`（演出时长）供调用方排时序 | 适合（公式）/ 不适合（位置） | 可借鉴点：**`baseAttack + 30×grade` 这条线性成长公式**极简清晰，可直接作为 JSTM 技能伤害基础式；不适合原因：等级来自客户端的 `m_grade`，服务端必须自己查表 |
| `Classes/Skill.cpp` | `Skill::getUseMana` | 【已确认】`:88-91` `baseMana + grade * 10` | 适合 | 可借鉴点：蓝耗同步线性增长，与伤害同构，便于服务端复算校验 |
| `Classes/Skill.cpp` | `Skill::incGrade` / `initProperty` | 【已确认】`:83-86` 升级只是 `++m_grade`，**无等级上限校验**；`:51-71` 属性来自 `<技能名>.att`（实测 CrackIt：`name CrackIt / buyglod 1500 / sellglod 750 / baseattack 300 / basemana 50 / baseupglod 500`） | 适合（数据表）/ 不适合（无上限） | 可借鉴点：`.att` 六字段技能表可直接翻译成 JSTM 的技能配置表（含买价/卖价/基础攻击/基础蓝耗/升级价）；需补等级上限与重复购买校验 |
| `Classes/SkillFactory.cpp` | `SkillFactory::createSkill` | 【已确认】`:12-50` **手写 8 条 `if-else` 字符串比较**（CrackIt/Dante/DragonRoar/LightStrike/Long/RecallCountermand/SealOfTheBlade/XBArrow），未知技能 `return nullptr` 且调用方未判空 | 适合（结构）/ 不适合（实现） | 可借鉴点：**"技能名 → 效果类"的分派点集中在一处**，利于 JSTM 换成注册表/映射表；不适合原因：8 个技能对应 8 个类，扩展成本 O(n)，且**没有 `8` 这个上限常量**（"最多 8 个"只是资源事实） |
| `Classes/RealSkill.h` / `.cpp` | `RealSkill`、`SKILL__FUNC` 宏 | 【已确认】`RealSkill.h:7-16` 宏为每个效果类生成 `static create` + `init(parent,towho,baseattack)`；`RealSkill.cpp:20-33` `loadAnimation(name,nums,delay)` 批量加载帧并缓存；`:15-18` `died()` 即 `removeChild(this)` | 适合 | 可借鉴点：**`loadAnimation` 的"文件名前缀 + 帧序号 + 统一 delay"约定**与 `getAnimation` 缓存，是 Cocos 客户端动画加载的通用范式，可平移到 JSTM 客户端 |
| `Classes/DragonRoar.cpp` / `Danate.cpp` / `Long.cpp` | `heart()` | 【已确认】三个**单目标**技能：`dynamic_cast<Monster*>(m_towho)->beAttack(m_baseattack)`（`DragonRoar.cpp:33`、`Danate.cpp:43`、`Long.cpp:31`），伤害直接用工厂算好的 `m_baseattack` | 适合 | 可借鉴点：**"演出对象持有结算参数、在命中帧回调"**的模式，最容易被改造成"服务端下发结果 → 客户端播动画"；需服务端化 |
| `Classes/CrackIt.cpp` / `SealOfTheBlade.cpp` | `heart()` | 【已确认】两个**全体**技能：`for (auto var : pFt->m_monsterList) var->beAttack(m_baseattack);`（`CrackIt.cpp:30-37`、`SealOfTheBlade.cpp:29-36`） | 适合 | 可借鉴点：**AOE 直接遍历战斗层怪物列表**，实现最简单；JSTM 服务端可对应"对敌方全体结算" |
| `Classes/LightStrike.cpp` / `RecallCountermand.cpp` / `XBArrow.cpp` | `heart()` | 【已确认】三个**目标+相邻一只**技能，用 `i % 2` 判断打 `i±1`（`LightStrike.cpp:33-48`、`RecallCountermand.cpp:33-49`、`XBArrow.cpp:33-49`），并有 `i-1`/`i+1` 边界保护 | 适合 | 可借鉴点：**"直线穿透/横扫"可以用"目标索引 ±1"近似**，是低成本的连击/横扫实现；JSTM 若做横排阵型可直接用 |
| `Classes/SkillManager.cpp` | `SkillManager::addSkill` / `haveSkill` | 【已确认】`:25-34` / `:41-45` 只对 `m_skillMap`（`map<string,int>`）判重与插入，**无数量上限**；`skillNumbers()` `:52-55` 存在但**零调用** | 适合（结构）/ 不适合（缺校验） | 可借鉴点：`map<技能名, 等级>` 是最贴合"技能不重复 + 有等级"需求的数据结构，可直接用于 JSTM 客户端缓存；必须补 `size() < 8` 校验 |
| `Classes/SkillManager.cpp` | `upSkill` / `readSkillInfo` / `saveSkillInfo` | 【已确认】`:57-103` 升级时 `m_skillMap[name] += 1` 并通过 `DBDao<SkillInfo>::updateModel` **直连 MySQL 写库**；`readSkillInfo` 用 `queryModel` 读全表；`saveSkillInfo` 逐条 `insertModel` | 不适合 | 不适合原因：**技能等级由客户端直接写数据库**，服务端完全不参与，天然可刷；且 `SkillManager.cpp` include 的是 `Classes/Model.h` 的 `SkillInfo`（有 4 字段的 `GettingAndSetting`），而 `Classes/SkillInfo.h` 是**同名空类**（只有构造/析构，方法缺失），属重复定义隐患。JSTM 必须把技能等级收归服务端 |
| `Classes/SkillLayer.cpp` | `onBtnUpClickCallback` / `initSkillIcon` | 【已确认】`:53-79` 升级花费 `getbaseupGlod() + grade*50`，扣钱 → `incGrade()` → `SkillManager::upSkill()`；`:81-113` 按 `getSkillMap()` 顺序平铺图标（`pos.x + index*(40+18)`），用 `setTag(index)` 存索引 | 适合 | 可借鉴点：**升级价随等级线性增长（+50/级）**与"图标按 map 顺序平铺"的 UI 组织方式；注意未做上限/金钱校验的一致性（先扣钱后升级，失败无回滚） |

### 3.4 实体、属性与飘字

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/Monster.h` | `Monster` 属性集 | 【已确认】`:33-41` `attack/blood/defense/speed/name/exp/glod/frames`，**无掉落字段** | 适合 | 可借鉴点：**六项属性 + 帧数**的极简怪物模型，字段名可直接映射 JSTM 服务端怪物配置；需补 dropTable 与技能表 |
| `Classes/Monster.cpp` | `Monster::beAttack` | 【已确认】`:94-120` **核心伤害函数**：受击位移抖动 → `float hurtvalue = attack <= m_defense ? 1 : attack - m_defense;`（`:103`）→ `HurtsValueLayer::createWithInfo` 飘字 → `m_blood -= hurtvalue` → `<=0` 则置 `m_isdie`、0.3s 后 `FightLayer::removeMonster(this)` + `TaskSystem::checkKillMonster` | 适合（公式） | 可借鉴点：**`max(1, 攻击 − 防御)` 的保底减法公式**是全部战斗数值的核心，JSTM 可沿用并加暴击/系数层；不适合改动的是它把结算、飘字、死亡、任务计数全塞在一个函数里（耦合过重） |
| `Classes/Monster.cpp` | `Monster::initProperty` / `initMonsterAnimation` | 【已确认】`:48-70` 从 `<Name>.att` 读六项属性（首个 token 为注释、第二个为中文名）；`:72-92` 按 `frames` 载入 `<Name><i>.png` 建动画，`setDelayPerUnit(0.15)`，`RepeatForever` | 适合 | 可借鉴点：**"属性文件 + 帧序号图片 + 固定帧间隔"**的怪物资源约定，是最省事的怪物接入方式，JSTM 客户端可直接复用 |
| `Classes/Player.cpp` | `XGamePlayer::beAttack` | 【已确认】`:194-209` 与 `Monster::beAttack` 同一公式（`:199`），`m_blood -= hurtvalue`，`<=0` 时 `dynamic_cast<FightLayer*>(getParent())->removeOtherPlayer(this)` | 适合（公式） | 可借鉴点：**玩家与怪物共用同一伤害公式**，保证 PVP/PVE 一致；不适合原因：`getParent()` 强转 `FightLayer`，一旦被非战斗父节点持有即崩溃 |
| `Classes/Player.cpp` | `XGamePlayer::normalAttack` / `skillAttack` | 【已确认】`:211-224` 普攻位移后 `((Monster*)who)->beAttack(this->getAttack())` 并返回 `1.6` 作为演出时长；`:226-234` 技能则**重新 `Skill::createWithImage` + `setgrade(grade)`** 再由 `Skill::beUse` 造效果对象 | 适合（时序） | 可借鉴点：**"攻击函数返回演出时长"**让调用方用 `scheduleOnce(delay)` 对齐回合交接，是很干净的接口约定；不适合原因：靠 `grade` 字符串重建技能对象，重复反序列化 `.att` 文件 |
| `Classes/CameraPlayer.cpp` | `CameraPlayer::beAttack` | 【已确认】`:227-242` 主角受击，公式同上（`:232`），扣 `m_playerData.curblood`，`<=0` 时**直接从父节点移除脸部 Sprite** | 适合（公式）/ 不适合（处理） | 可借鉴点：同公式；不适合原因：死亡时只移除表现、不通知任何状态机，`FightLayer::checkFightEnd` 靠每帧轮询血量兜底 |
| `Classes/PlayerData.cpp` | `addGlod` / `addExp` / `upGrade` / `addProperty` | 【已确认】`:17-31` 加钱加经验，经验溢出**递归 `addExp(overexp)`**；`:58-66` 升级 `++m_grade`、`m_maxExp += m_grade*100`、属性 `+30 blood/+30 mana/+5 attack/+5 defense`；`:68-75` 属性变化后立刻 `CMClient::updatePlayerData()` **把新属性广播给所有人** | 适合（成长公式） | 可借鉴点：**升级属性成长（血蓝+30、攻防+5）与经验需求（`grade*100` 累加）** 是完整可用的等级曲线起点；不适合原因：广播的是客户端自算的属性，等于把伪造入口留给玩家 |
| `Classes/HurtValueLayer.h` / `.cpp` | `HurtsValueLayer::createWithInfo` / `init` | 【已确认】`:21-33` 仅做 `LabelTTF("-" + hurt)`（红色、楷体 25），`scheduleOnce(dead, 1)` 后 1 秒自毁。纯展示，无暴击/闪避分支 | 适合 | 可借鉴点：**`createWithInfo(pos, value)` 的接口形态**与"1 秒自动销毁"的生命周期管理，可原样搬到 JSTM 客户端；需扩展数值来源与表现维度 |
| `Classes/Thing.cpp` | `Thing::beUse` / `initDetails` / `getfileName` | 【已确认】`:77-80` 基类 `beUse` 返回 `0.0f`（空实现，供 `Skill`/`Medication`/`EquipMent` 覆写）；`:51-70` 从 `<名>.dec` 读多行描述；`:32-49` `getfileName` 截掉扩展名 | 适合 | 可借鉴点：**"物品 = 图标 + .att 数值 + .dec 描述"三件套**的资源配置范式，JSTM 客户端做背包/商店/技能面板都能复用 |
| `Classes/Medication.cpp` | `Medication::beUse` | 【已确认】`:67-78` 本地 `addcurBlood(m_addblood)` + `addcurMana(m_addmana)`，返回 `0.0f`；属性来自 `.att`（`buyglod/sellglod/addblood/addmana`，`:48-65`） | 适合（数据）/ 不适合（结算） | 可借鉴点：**药品四字段表（买卖价 + 回血 + 回蓝）**简单够用；不适合原因：回血完全在客户端算，配合"只传 `dest` 的 `UseMedication_Msg`"，服务端无法验证 |
| `Classes/FightLayer.cpp` | `FightLayer::removeMonster` / `checkSuccess` / `reSelectMonster` | 【已确认】`:531-536` 累加 `m_settlementGlod/Exp` 并隐藏怪物；`:538-548` 全怪死亡判定；`:627-637` 当前目标死亡后自动改选**最后一个**存活怪（循环未 break） | 适合（结构）/ 不适合（细节） | 可借鉴点：结算累加与胜负判定的分离；不适合原因：`reSelectMonster` 不 break 会导致总是选中列表最后一只存活怪【已确认】，是明确小瑕疵 |

### 3.5 场景、地图与会话

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/GameLogicLayer.cpp` | `randomMeetMonster` | 【已确认】`:155-180` **逐帧计数遇敌**：`CurMap >= LEVEL_THREE` 且 `interval > 5` 时 `rand()%100 < 2`（2% 概率）触发；数量 `rand()%4 + 1`；怪物名由 `monsterName()` 按地图硬编码抽取 | 不适合 | 不适合原因：**遇敌概率、数量、怪物种类全在客户端决定**，服务端无感知，无法做掉线补偿/反作弊/活动控制。JSTM 必须服务端 roll 点 |
| `Classes/GameLogicLayer.cpp` | `checkEntryFight` | 【已确认】`:235-257` 读 `IsEntryFight` 标志 → 存 `DestX/DestY` → `pauseAllActions` + 红屏 0.2s → `FightLayer::createFightScene(MonsterName, MonsterNums)` → `TransitionFadeDown` 切场景 | 适合 | 可借鉴点：**"暂停原场景 → 过渡特效 → 切战斗场景 → 战斗结束回原坐标"** 的完整时序，JSTM 客户端可照搬（`FightLayer::endFunc` 回退到 `GameScene::createWithLevel(CurMap)`） |
| `Classes/GameLogicLayer.cpp` | `onTouchEnded` | 【已确认】`:32-52` 点击地图反算世界坐标 → `CameraPlayer::moveTo`；**队员状态禁止移动**（提示 `TeamingText`）；队长移动成功后 0.1s 延迟 `moveTeamMembers(targetPos)` 带动全队 | 适合 | 可借鉴点：**"队长带路、队员跟随"** 的队伍移动设计（`CameraPlayer::moveTeamMembers` → `sendTeamMoveMsg`，`CameraPlayer.cpp:293-299`）；不适合原因：跟随是本地广播驱动，非服务端权威 |
| `Classes/FindRoad.h` / `.cpp` | `FindRoad::ExecuteAStar` 等 | 【已确认】`:32-87` A\* 主循环；`:89-98` 可行走判定 `map[y][x]==0 \|\| -100`；`:100-103` `h=欧氏距离`；`:117-127`/`:129-140` openList **线性扫描**取最小 f；`:142-150` 回溯路径入栈，`lessOne(1)` 跳过一个节点 | 适合（仅思路） | 可借鉴点：**完整可用的 A\* 思路**（8 方向 + 起始/目标格坐标 + `lessOne` 贴近目标），JSTM 自行实现；性能上线性扫 openList 是 O(n²)，大图需换优先队列 |
| `Classes/CameraPlayer.cpp` | `moveTo` / `SendMoveToMsg` | 【已确认】`:269-291` 世界坐标 → 格子坐标（`FOUR_LOSE_FIVE_ADD` 取整）→ A\* → 有路则 `SendMoveToMsg(tmp, less)` 广播 + `setMoveRoad` | 适合 | 可借鉴点：**"先本地寻路成功、再上报移动目标"** 的顺序（避免走不动还广播）；`less` 参数用于区分"走到格子中心"与"差一格停下" |
| `Classes/ObjectLayer.cpp` | `moveOtherPlayer` / `addPlayer` / `removePlayer` | 【已确认】`:257-266` 他人移动＝在本机为他**再跑一遍 A\***（`XGamePlayer::moveTo`）；`:178-203` 按 `curmap` 决定新增或移除；`:230-240` `verifyPlayerPos` 用服务端下发坐标强制回正 | 适合 | 可借鉴点：**"只同步起点/终点，中间路径各自推算"** 的低带宽同步法（与战斗的"各端自行模拟"是同一哲学）；不适合原因：一旦两端地图数据不同步就会穿墙，JSTM 应改用服务端校验路径 |
| `Classes/GameScene.cpp` | `pauseAllActions` / `resumeAllActions` / `pauseOrResumeAllLayer` | 【已确认】`:74-99` **递归遍历子节点** `pauseSchedulerAndActions()`；`:118-135` 战斗/弹窗时暂停逻辑层、地图层、对象层、UI 层并 `clearOtherPlayer()` | 适合 | 可借鉴点：**"进入战斗/弹窗时整场景递归暂停"** 的做法能彻底冻结时间相关逻辑，避免战斗期间地图仍在 tick；JSTM 客户端可直接用 |
| `Classes/GameDynamicData.h` / `.cpp` | `SetIntData/GetIntData` 等宏与 `GameDynamicData` | 【已确认】`GameDynamicData.h:13-21` 定义 `Set/GetFloat/Int/Bool/StringData` 宏；`.cpp:38-72` 用 `map<string,string>` + `stringstream` 存值，`save=true` 走 `m_saveData` 并**析构时写 `GameDynamicData.data` 文件**（`:130-145`）；`getIntByKey` 找不到键返回 `-1`（`:24`） | 适合 | 可借鉴点：**"全局键值袋 + 可选持久化"** 让场景间传参（`IsEntryFight`/`MonsterName`/`MonsterNums`/`DestX`/`DestY`）极其省事，JSTM 客户端做 UI 与场景解耦可借用；不适合原因：类型全靠字符串转换、缺键静默返回 -1，容易掩盖 bug |
| `Classes/GameData.cpp` | `GameData::init` / `getXxxByKey` | 【已确认】`:47-56` `Dictionary::createWithContentsOfFile("GameData.xml")` 加载本地化文案；`:22-40` 四个取值宏。已确认 `FightBg/FightSuccess/FightFailed/RunSuccessText/RunFailed/NoAction/NoTarget/NoMana/AutoBtn/UseHandBtn/AttackNormalBtn/MeNormalBtn/SkillNormalBtn/RunNormalBtn/SkillText` 等键**均存在于 GameData.xml** | 适合 | 可借鉴点：**"所有文案走一个 xml 字典 + 代码里只写 key"** 的国际化前置设计，JSTM 客户端做多语言可直接采用同构方案 |
| `Classes/AudioSystem.cpp` | `HelpToolSystem::WorkThread` | 【已确认】`:30-65` 独立线程 50ms 轮询；`:45-49` 每 180 次（约 9 秒）`VerifyPlayerPos()` 上报位置；`:50-63` 每 4 次检查队员是否与自己同图，不同则 `sendTeamGotoMapMsg` 带队切图 | 适合 | 可借鉴点：**"低频心跳 + 位置校验"** 的反作弊骨架（JSTM 可扩展为战斗心跳）；不适合原因：线程里直接操作客户端对象，无锁保护 |
| `Classes/TaskSystem.cpp` | `checkKillMonster` | 【已确认】`:174-184` 遍历已接任务，`schedulewho == 怪物名` 则 `curschedule++`。**战斗是任务进度的唯一数据来源** | 适合 | 可借鉴点：**"击杀事件 → 任务进度"** 的解耦方式（战斗不直接改任务，任务系统自己订阅）；不适合原因：任务进度在本地内存、线程每 15 秒 `createTask()` 随机生成任务（`:52-63`），无服务端权威 |
| `Classes/DBDao.h` | `DBDao<Model>` 模板 | 【已确认】`:106-113` **硬编码生产库凭据**（host `47.93.235.6`、user `game`、明文口令、db `chivalrousman`）；`:138-164` `queryModel` 用 `md[i+1] = row[i]` 按列号映射；`:295-313` `generateValues` 用字符串拼接拼 SQL；`:183-211` `updateModel` 以 `key='value'` 拼接 WHERE | 不适合 | 不适合原因：**客户端直连数据库 + 明文凭据 + 字符串拼 SQL**（无参数化，存在注入面）是架构级反模式，JSTM 绝不可复制。可借鉴点仅是 `Model` 的 `operator[]` + `getAttributeName(index)` 列号映射思路，用于生成 SQL 的元数据表 |
| `Classes/CameraPlayer.cpp` | `CameraPlayer::SaveGameData` | 【已确认】`:244-267` 用 `DBDao<PlayerInfo>::updateModel({playername, rolename})` 写回 attack/blood/defense/destx/desty/exp/glod/grade/mana/maxExp/level，再依次存背包、装备、技能 | 不适合 | 不适合原因：**战斗结果（exp/glod）由客户端写回数据库**，等于客户端就是权威存档源。JSTM 必须服务端记账、客户端只做表现 |
| `Classes/Model.h` | `PlayerInfo` / `SkillInfo` / `EquipmentInfo` / `BackPack` / `GamePlayer` | 【已确认】`:64-175` `PlayerInfo` 15 字段（playername/rolename/roletype/glod/grade/blood/mana/attack/defense/speed/exp/maxexp/destx/desty/level）带完整 `operator[]` 与列名映射；`:177-232` `SkillInfo` 4 字段（playername/rolename/skillname/skillgrade） | 适合（字段） | 可借鉴点：**`PlayerInfo` 的 15 个字段几乎就是 JSTM 角色表的最小集合**，可直接作为建表/存档结构的参考；`SkillInfo(角色名, 技能名, 等级)` 是"技能不重复 + 有等级"的最简表结构。**注意**：`Classes/SkillInfo.h` 是另一个同名空类（无任何字段/方法），与 `Model.h::SkillInfo` 重名，属遗留冲突 |
| `Classes/GameUILayer.cpp` | `GameUILayer::update` / `generateUserInterface` | 【已确认】`:282-287` 每帧刷新金币文本与经验条百分比（`exp/maxExp`）；`:127-153` 血条/魔条/经验条均为 `ProgressTimer` 且初始 `100%` | 适合 | 可借鉴点：**三条进度条（血/魔/经验）的统一构建方式**与"每帧只刷文本和百分比"的低成本刷新策略，JSTM 客户端主界面可照搬 |

### 3.6 死代码与设计意图残留（供 JSTM 判断"作者本意"）

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/FightLayer.cpp` | `calcActionOrder` | 【已确认】`:207-210` **空函数体**，全仓库零调用。原意是计算行动顺序（回合制核心） | 不适合 | 不适合原因：无实现。**可借鉴点在于"它本该存在"这一信息**——JSTM 若要复刻经典回合制，行动顺序表（按 speed 排序）正是本项目缺失且必须补齐的部分 |
| `Classes/FightLayer.h` | `m_mmor` | 【已确认】`:227` 声明"纪录回合数"，**全仓库零引用** | 不适合 | 不适合原因：回合计数器未实现，说明回合概念在半成品状态。JSTM 需要真正的回合号（且应由服务端持有） |
| `Classes/FightLayer.cpp` | `MonsterEndBehavie()` 宏 | 【已确认】`:43` 定义但从未使用 | 不适合 | 不适合原因：死代码，逻辑被内联；仅作设计意图旁证 |
| `Classes/Monster.cpp` | `m_speed` 字段 | 【已确认】`.att` 读了 `speed`（`Monster.cpp:65`）但**战斗链路零使用**（因 `calcActionOrder` 为空） | 适合（字段保留） | 可借鉴点：**`speed` 字段预留给出手顺序**，JSTM 应真的用它排序行动顺序；不适合原因：本项目读了不用 |
| `Classes/SkillManager.cpp` | `skillNumbers()` | 【已确认】`:52-55` 实现存在但**全仓库零调用**——本该用于校验"最多 8 个技能" | 适合（启用） | 可借鉴点：**把它接到购买流程里即可实现 README 所承诺的 8 技能上限**；不适合原因：本项目只是留了个没接线的方法 |
| `Classes/SkillInfo.h` vs `Classes/Model.h` | 两个同名 `SkillInfo` 类 | 【已确认】`Classes/SkillInfo.h:10-18` 是只有构造/析构的**空类**（`SkillInfo.cpp` 为 **0 字节**）；`Classes/Model.h:177-232` 才是真正带 `playername/rolename/skillname/skillgrade` 且被 `SkillManager` 使用的那个。`SkillManager.cpp` 只 include 了 `Model.h` | 不适合 | 不适合原因：同名类重复定义，若两者被同一编译单元包含将直接编译失败；属遗留垃圾文件，JSTM 不要模仿这种命名 |

### 3.7 装备 / 背包 / 商店 / 资源加载（伤害公式的输入端与外围）

> 本节是第二轮补充的证据，对应 §2.10～§2.12。

| 文件路径 | 类/函数名 | 工作机制 | 是否适合 JSTM | 适合/不适合的原因 |
| --- | --- | --- | --- | --- |
| `Classes/EquipMent.cpp` | `EquipMent::beUse` | 【已确认】`:74-85` 先 `EquipmentManager::wearEquipment(info)`（换槽并退旧），再 `GetPlayerData().addProperty(addblood+(grade-1)*30, addmana+(grade-1)*30, addattack+(grade-1)*8, adddefense+(grade-1)*8)` **本地累加属性** | 适合（设计）/ 不适合（位置） | 可借鉴点：**"装备加成 = 基础值 + (等级−1)×每级增量"** 这条统一公式（血魔 30/级、攻防 8/级）非常简洁，可作为 JSTM 装备系统的数值骨架；不适合原因：加成直接改客户端属性，必须改为服务端结算 |
| `Classes/EquipMent.cpp` | `EquipMent::upgrade` / `Disassemble` | 【已确认】`:105-114` 升级 `m_grade += 1` 并 `addProperty(30,30,8,8)`；`:87-103` 拆卸用**完全相同的公式减回去**并退回背包 | 适合（设计） | 可借鉴点：**加/减成对使用同一公式**，保证穿脱对称不出错——这是装备系统最容易写错的地方，本项目处理正确。`speed` 不参与（见下） |
| `Classes/EquipMent.cpp` | `EquipMent::initProperty` / `upGlod` | 【已确认】`:51-72` 从 `<装备名>.att` 读 `buyglod/sellglod/addblood/addmana/addattack/adddefense/addspeed/type`；`:45` `m_baseupglod = addblood + addmana + addattack*10 + adddefense*10`；`:156-159` 升级价 `m_baseupglod + m_grade*(100 + m_baseupglod/10)` | 适合（设计） | 可借鉴点：**升级价由装备强度派生**（攻防按 ×10 权重）而非硬编码，配方表可以省略一列；`m_addspeed` 读了但 `addProperty` 无速度形参 ⇒ **速度加成永不生效**【已确认】，JSTM 若保留 speed 必须真的接上 |
| `Classes/EquipmentManager.cpp` | `wearEquipment` | 【已确认】`:17-33` 按 `type` 遍历找同槽旧装备 → `EquipMent::createWithImage(旧名)` + `setgrade(旧等级)` + `Disassemble(nullptr)`（退旧并扣旧加成）→ 覆盖 `it->name/grade`。**换装分支把等级写成 `it->grade = 1`**（`:27`），而加成用的是新对象的 `m_grade` | 不适合 | 不适合原因：**存储等级与实际加成不一致**（重登后 `readEquipmentInfo` 按 1 级复原），是明确的记账 bug。可借鉴点仅是"5 槽互斥、同槽自动替换"的规则 |
| `Classes/EquipmentManager.cpp` | `removeEquipment` | 【已确认】`:49-61` 遍历找到同名装备 → `m_emlist.erase(it); deleteEm(*it);` —— **erase 之后才解引用该迭代器** | 不适合 | 不适合原因：**未定义行为**（应先把 `*it` 存副本再 erase）。这是本轮发现的最严重代码缺陷之一，JSTM 不要复刻这种"边遍历边删"的写法 |
| `Classes/EquipmentManager.cpp` | `readEquipmentInfo` / `saveEquipmentInfo` / `updateEm` / `deleteEm` | 【已确认】`:68-127` 四个方法都通过 `DBDao<EquipmentInfo>` **直连 MySQL**：读用 `queryModel`，存用逐条 `insertModel`，改名/删用 `updateModel(keys)`/`deleteModel` | 不适合 | 不适合原因：装备归属与等级由客户端写库，可任意伪造。可借鉴点：`EquipmentInfo(playername, rolename, equipmentname, grade, type)` 的 5 字段结构是"多角色 + 多装备槽"的最小表设计 |
| `Classes/RoleInfoLayer.cpp` | `initRoleEquipment` / `onUpBtnClick` | 【已确认】`:176-206` 按 `EM_HEAD/EM_WEPON/EM_JEWELRY/EM_CLOTH/EM_FOOT` 把装备摆到上/左/右/中/下五个位置；`:146-165` 点升级按钮：`upGlod()` 判钱 → `EquipmentManager::upEquipment` → `EquipMent::upgrade` → `subGlod`（**先升级后扣钱，无失败回滚**） | 适合（布局设计） | 可借鉴点：**五槽环形布局 + 槽位常量到屏幕位置的映射**，是客户端装备界面的低成本实现；不适合原因：扣钱顺序无事务保护 |
| `Classes/AppDelegate.cpp` | `LoadSkillAnimation` / `LoadResource` / `LoadPlayerAnimation` | 【已确认】`AppDelegate.cpp:175-184` 用两个并列数组 `skill[8]` + `nums[8]={16,14,9,9,10,17,15,9}` 批量预热 8 个技能动画；`:125-147` 另加载玩家三套形象与门动画；`:149-162` `LoadAnimationFromFile` 用**整张长条图切帧**（`width / num`） | 适合 | 可借鉴点：**"两个等长数组 + 循环预热"** 的启动预热写法，以及 `LoadAnimationFromFile` 的**序列帧长条图切分**（比多文件更省 IO）。注意 `skill[]` 里的名字必须与工厂/目录严格一致——本项目恰好在 `Long`/`RecallCountermand` 上出现大小写不一致（§2.12） |
| `Classes/AppDelegate.cpp` | `registerReflectClass` | 【已确认】`:164-173` 注册 7 个 NPC 类名到 `ReflectNpc` 反射表（`NpcBlue`/`NpcEquip`/`NpcMamom`/`NpcMonk`/`NpcPink`/`NpcSkill`/`NpcVallige`） | 适合 | 可借鉴点：**"配置文件写类名 → 运行期反射造对象"**（配 `DEF_REFLECT_FUNC`/`REG_REFLECT_CLASS` 宏，`ReflectNpc.h:12-24`）让 `LevelObject/Level*.lobject` 可以用纯文本摆放 NPC，是很好的**数据驱动地图**思路；JSTM 可用注册表替代宏。注意 `NpcMamom` 类名拼写与文件名 `NpcManmom.h` 不一致，属命名混乱 |
| `Classes/AnimationLoaderTool.cpp` | `loadAnimationFromMinFile` | 【已确认】`:4-17` 按 `name + i + ".png"` 从 1 循环到 **硬编码的 8**，**完全忽略传入的 `num` 参数**；`:19-22` `loadAnimationFromLargeFile` 是**空实现**（无 return） | 不适合 | 不适合原因：忽略 `num` 说明该工具函数已废弃/半成品，且空实现函数有返回值类型却无 return（UB）。可借鉴点仅是"帧序列命名约定"这一思路 |
| `Classes/PreProcess.h` | `ADD_PROPERTY` 宏 | 【已确认】`:76-79` `fin >> tmp; fin >> tmp; m_##NAME = std::stof(tmp);`——**连读两个 token 丢弃，再 `stof` 第三个**。⇒ `.att` 文件里的字段名纯粹是给人看的，解析**只按位置**生效。实测旁证：`Thing/DuronKnife.att` 写 `blood/mana/attack/...`（而代码变量叫 `addblood/addattack`）、且售价格式写成 `ssellglod`（拼写错误），**依然解析正确** | 适合（理解）/ 不适合（设计） | 可借鉴点：理解这一点后，`.att` 表就是"每行 `键 值`、顺序敏感"的位置式配置，改字段名不影响运行——JSTM 若沿用必须**写清顺序约束并加校验**；不适合原因：忽略键名意味着顺序写错也不会报错，只会静默算错数值 |
| `Classes/BackPackManager.cpp` | `addBackPackThing` / `removeBackPackThing` | 【已确认】`:25-41` 同名的**累加 `nums`**、不同名的 `push_back` 且强制 `nums=1`（**忽略调用方传入的数量**）；`:43-61` 减数量，减到 0 时 `erase(it)` 后又 `deleteBackpack(*it)`（**与 `EquipmentManager::removeEquipment` 同样的 erase 后解引用缺陷**） | 不适合 | 不适合原因：两处同型 UB + `addBackPackThing` 忽略入参 `nums`（`ThingInfo.nums` 形同虚设）。可借鉴点：`ThingInfo{name, type, nums, grade}` 的背包条目结构够用 |
| `Classes/MapInfo.cpp` | `readMapInfoFromFile` | 【已确认】`:37-79` 读 `map*.mp`：先读 `countx/county/mapSize/纹理数`，再**从 `county-1` 倒序遍历行**（⇒ y 轴翻转），用正则按逗号切分格子；**格值 `-100` 被识别为门**并登记进 `m_doorPos`（`:67-73`） | 适合 | 可借鉴点：**"一张整数格子图同时承载通行性与门坐标"**——`-100` 既是可走格又是门标记，一份数据两用，很省事（配 `FindRoad::IsValid` 判「值等于 `0` 或 `-100`」，`FindRoad.cpp:93`）。JSTM 可借鉴这个**用格值编码语义**的技巧；注意行序倒读与 y 翻转必须一致 |
| `Classes/GameLogicLayer.cpp` | `checkEntryDoor` | 【已确认】`:74-95` 遍历 `GetDoorPosInfo()`，与玩家距离 `< 40` 即触发切图（写 `DestX/DestY`、`IsDoor=1`、`unscheduleUpdate()`、`gotoDestMap`） | 适合 | 可借鉴点：**"距离阈值触发传送门"** 的判定极简；与 §2.9 的 `lessOne(1)` 配合（跟随者停在门外一格）能避免误触发。JSTM 需改为服务端校验落点 |
| `Classes/DealLayer.cpp` | `checkBuy` / 按 `m_type` 分发 | 【已确认】`:168-204` 判钱 → 按 `SKILL`/`EQUIPMENT`/`MEDICATION` 分发（技能走 `SkillManager::addSkill`，其余走 `AddToBackPack`）→ 提示 `BuySuccess` → `setglod(haveglod - money)`。**技能购买只判重不判数量**（`:180-192`） | 适合（结构）/ 不适合（校验） | 可借鉴点：**用商品类型枚举统一驱动"购买后干什么"**的分发结构；不适合原因：金钱与物品都由客户端增删、无服务端回执，且技能上限完全没校验（§2.4） |
| `Classes/Commen.h` | `FOUR_LOSE_FIVE_ADD` / `CONTAIN_POINT` / `LISTEN_TOUCH` / `ClickAction` 等 | 【已确认】`:113-121` 四舍五入宏（浮点转格子坐标用）；`:23-34` 点是否在矩形内（编辑框命中用）；`:98-104` 一行注册触摸监听；`:167-170` 按钮点击缩放反馈 | 适合 | 可借鉴点：**`FOUR_LOSE_FIVE_ADD` 的世界坐标→格子坐标取整**与寻路入口直接相关（`CameraPlayer.cpp:278-279`）；`LISTEN_TOUCH` 这类宏能把 6 行样板压成 1 行，JSTM 客户端可保留同类写法（但建议用函数/模板而非宏） |
| `Resources/DealThing/*.dt` | `Skill.dt` / `EquipMent.dt` / `Medication.dt` | 【已确认】纯文本商品清单，首行是 `//` 注释：`Skill.dt` **恰好 8 条**、`EquipMent.dt` 15 条、`Medication.dt` 3 条。由 `DealLayer` 读取并生成商品网格 | 适合 | 可借鉴点：**"商店卖什么"外置成清单文件**，与"物品自身属性"（`.att`）分离，改商店不用碰代码。这是本项目配置分层里最干净的一处，JSTM 可直接采用同构的表设计 |

---

## 4. 对 JSTM 的可借鉴点汇总（战斗专题）

> 本节只列**战斗链路相关**的条目；跨项目的总体候选清单、许可口径与按子系统归口的采纳建议见同目录 `reuse_candidates.md`（本项目为 **无 LICENSE**，按任务书【原则 3】处理：**只借鉴设计与机制，不复制代码**）。下列每条均应按"读懂机制后由 JSTM 自研实现"使用。

**强烈建议借鉴（客户端侧，均为设计/机制层）**

1. **技能数据结构与命中时序**：`.att` 六字段技能表（`baseattack`/`basemana`/`buyglod`/`sellglod`/`baseupglod`）+ `RealSkill` 家族"`scheduleOnce(died, T)` + `scheduleOnce(heart, t)` + `setTag(T)`"的演出/结算双定时范式（`Skill.cpp:73-81`，各效果类 `init`）。
2. **伤害基础公式**：`max(1, 攻击 − 防御)`（`Monster.cpp:103`）+ 技能成长 `baseAttack + 30×grade`（`Skill.cpp:76`）+ 蓝耗 `baseMana + 10×grade`（`Skill.cpp:90`）+ 升级价 `baseupGlod + 50×grade`（`SkillLayer.cpp:63-64`）。四条线性公式是一套自洽的数值起点。
3. **行动条超时托管**：手动 10 秒 / 自动 2 秒两档，超时自动执行"上次选择的技能或普攻"（`FightLayer.cpp:212-224`、`:410-432`）。这是挂机体验的核心。
4. **战斗状态标志位组**：`m_isPlayer` / `m_isPlayerEnd` / `m_curMonster` / `m_lastMonsterEnd`（`FightLayer.h:221-233`）用最简单的方式表达"玩家回合 → 怪物逐个回合 → 交还玩家"。
5. **场景切换时序**：暂停原场景 → 过渡特效 → 战斗场景 → 结算提示 → 按 `CurMap` 回退到原坐标（`GameLogicLayer.cpp:235-257` + `FightLayer.cpp:510-521`）。
6. **角色/技能/背包的存档字段集**：`Model.h::PlayerInfo`（15 字段）、`SkillInfo`（4 字段）、`BackPack`（6 字段）、`EquipmentInfo`（5 字段），可直接作为 JSTM 建表结构参考。
7. **位置双向校验范式**：客户端 9 秒上报 + 服务端下发纠正（`AudioSystem.cpp:45-49` + `CMClient.cpp:254-276`）。这是本项目**唯一**具备反作弊意图的机制，可扩展成战斗数值校验。
8. **通用工具**：`FindRoad` A\*、`GameDynamicData` 全局键值袋、`GameData.xml` 文案字典、`HurtsValueLayer` 飘字、`GameScene::pauseAllActions` 递归暂停、`Thing` 的"图标+.att+.dec"三件套。

**明确不要借鉴**

1. 客户端直连 MySQL（`DBDao.h` 硬编码凭据、明文口令、字符串拼 SQL、`CameraPlayer::SaveGameData` 由客户端写存档）。
2. 客户端本地结算并落库（伤害、经验、金币、技能等级）。
3. 无长度前缀的 TCP 收包（`TCPClient.cpp:87-121`）。
4. 战斗协议不携带结果数值（`PlayerAtk_Msg`/`MonsterAtk_Msg`）。
5. 组队战斗只传"怪物名 + 数量"（`TeamFight_Msg`）。
6. 客户端决定遇敌与怪物生成（`GameLogicLayer.cpp:155-208`）。
7. 失败/逃跑也发奖（`FightLayer.cpp:510-521`）。
8. 同名类重复定义（`SkillInfo.h` vs `Model.h`）。

---

## 5. 统计与遗留

**读到的文件清单（本报告全部信息来源）**：`ShareData.h`、`FightLayer.h/.cpp`、`Monster.h/.cpp`、`Animal.h/.cpp`、`Skill.h/.cpp`、`SkillFactory.h/.cpp`、`RealSkill.h/.cpp`、`SkillManager.h/.cpp`、`SkillLayer.cpp`、`SkillInfo.h`、`LightStrike.*`、`DragonRoar.*`、`SealOfTheBlade.cpp`、`CrackIt.cpp`、`Danate.cpp`、`RecallCountermand.cpp`、`ReflectNpc.h/.cpp`、`Lock.h/.cpp`、`Long.cpp`、`XBArrow.h/.cpp`、`Player.h/.cpp`、`PlayerState.h/.cpp`、`PlayerWait.h/.cpp`、`PlayerRun.h/.cpp`、`HurtValueLayer.h/.cpp`、`CameraPlayer.h/.cpp`、`GameUILayer.h/.cpp`、`GameLogicLayer.h/.cpp`、`GameScene.h/.cpp`、`ObjectLayer.h/.cpp`、`GameDynamicData.h/.cpp`、`GameData.h/.cpp`、`PlayerData.h/.cpp`、`CMClient.h/.cpp`、`TCPClient.h/.cpp`、`DBDao.h`、`Model.h`、`FindRoad.h/.cpp`、`Thing.h/.cpp`、`Medication.h/.cpp`、`TeamManager.h/.cpp`、`TaskSystem.cpp`、`AudioSystem.cpp`、`DealLayer.cpp`（节选）、`NpcSkill.cpp`、`PreProcess.h`、`public.h`、`README.md`、`Resources/server.cfg`、`Resources/GameData.xml`（键名检索）、`Resources/Monster/Ghost|Dragon.att`、`Resources/Skill/CrackIt.att|.dec`。

**第二轮（补充）新增读到的文件**：`EquipMent.h/.cpp`、`EquipmentManager.h/.cpp`、`RoleInfoLayer.cpp`、`AppDelegate.cpp`、`AnimationLoaderTool.cpp`、`BackPackManager.cpp`、`MapInfo.cpp`、`TeamMsgItem.cpp`、`Commen.h`、`Resources/DealThing/Skill.dt|EquipMent.dt|Medication.dt`、`Resources/Thing/*.att`（15 件装备 + 3 种药品全部）、`Resources/Skill/*/*.att`（8 个技能全部）、`Resources/Monster/*/*.att`（10 只怪物全部）、`Resources/GameData.xml`（全量键值映射核对）。

**统计**：`【已确认】` 覆盖 75+ 行证据表与 12 个专题小节；`【待验证】` 6 项（本轮由 7 项关闭 1 项）；`【未知】` 5 处。全部结论均为静态阅读所得，**未运行程序**。

**【待验证】清单（共 6 项，本报告全部实质未定项）**

1. `MonsterAtk_Msg` 在 `towho == -1` 时收端用 `msg->fd` 查玩家索引（`CMClient.cpp:527`），但发端 `fd` 恒为 `-1`（`CMClient.cpp:504`）——需服务端确认是否回填 `fd`。（正文 §2.2(6)、§3.2 `sendMonsterAtkMsg` 行）
2. `TeamManager.h:9` 注释称"队伍人数上限为2个"，但 `createTeam` 层面**无任何数量校验**（`TeamManager.cpp:13-17`）——上限是否为服务端约束。（正文 §2.7、§3.2 `sendTeamFightMsg` 行的相邻讨论）
3. 服务端对 `M_PlayerAtk`/`M_MonsterAtk`/`M_PlayerRun`/`M_UseMedication`/`M_PlayerDie` 的实际处理逻辑（是否转发、是否重算、是否纠正客户端上报的伤害与经验金币）——**仓库无服务端源码**。
4. 技能等级上限：`Skill::incGrade`（`Skill.cpp:83-86`）与 `SkillManager::upSkill`（`SkillManager.cpp:57-74`）都无上限校验，实际约束在服务端还是配置表中。
5. `FightLayer` 中 `scheduleOnce(..., "reset")` 被 `playerAttackMonster`（`FightLayer.cpp:459`）与 `monsterAttackPlayer`（`:499`）复用同一 key，是否会因 cocos2d-x `Scheduler` 的同键行为导致先注册的回调被覆盖——需引擎源码或运行时验证。
6. 客户端本地 `addGlod/addExp`（`FightLayer.cpp:512-513`）后由 `CameraPlayer::SaveGameData` 回写 DB，服务端上是否另有一份记账并会覆盖——两端存档一致性。

> 说明：上述 3~6 项在正文表格中未逐格重复标注【待验证】（它们是"整条链缺少对立面"的判断题，而非某个代码行的静态事实），统一在此列明。

**本轮已关闭的【待验证】项（7 → 6）**

- ~~原第 3 项：`FindRoad::lessOne(1)` 的语义是否为"贴门/贴 NPC"~~ ⇒ **已定论**【已确认】：`less=1` 全仓库只有 2 处调用（`CMClient.cpp:436` 队员跟随队长、`TeamMsgItem.cpp:76` 走向组队邀请者），机制是"跳过路径上一格"，用途是让跟随者/靠近者停在目标前一格（详见 §2.9）。

**【未知】项**：服务端全部实现、数据库表结构与 SQL 脚本（README 提及但归档内不存在）、任何战斗反作弊校验规则。

---

# 附录 C（R2 回填，主审计员补全全部技能与怪物数值表）

> 正文只给出了取值范围（`attack 100～300`、`baseattack 100～350` 等）。本附录由主审计员在 R2 阶段**把 `Resources/Skill/*/*.att` 全部 8 个**与 `Resources/Monster/*/*.att` 全部 10 个**逐份读完**，补出完整数值表并给出由此导出的观察。全部条目均为 **【已确认】**。

## C.1 技能属性表全表（`Resources/Skill/<名>/<名>.att`，8/8 已读）

| # | 目录名 | 首行中文名 | `name` 字段 | `buyglod` | `sellglod` | **`baseattack`** | `basemana` | `baseupglod` |
|---|---|---|---|---|---|---|---|---|
| 1 | `CrackIt` | 紫焰狼爪 | `CrackIt` | 1500 | 750 | **300** | 50 | 500 |
| 2 | `Dante` | 裂地 | `Dante` | 1200 | 600 | **100** | 50 | 550 |
| 3 | `DragonRoar` | 蓝龙诀 | `DragonRoar` | 1000 | 500 | **250** | 50 | 550 |
| 4 | `LightStrike` | 狂雷诀 | `LightStrike` | 1500 | 750 | **230** | 50 | 600 |
| 5 | `long`（目录小写） | 火龙诀 | `Long`（首字母大写） | 1200 | 600 | **340** | 50 | 620 |
| 6 | `recallCountermand`（目录小写） | 烈焰神龙 | `RecallCountermand`（首字母大写） | 1600 | 800 | **350** | 50 | 650 |
| 7 | `SealOfTheBlade` | 天魔-封 | `SealOfTheBlade` | 1700 | 850 | **250** | 50 | 690 |
| 8 | `XBArrow` | 冰毒箭 | `XBArrow` | 1300 | 650 | **320** | 50 | 720 |

**★ 导出的 4 条观察**：
1. **`basemana` 8/8 全部是 `50`** ⇒ 技能基础蓝耗**没有差异化**，蓝耗差异**只能来自等级项** `+ grade × 10`（`Skill.cpp:90`）⇒ L1 全部 60 点、L5 全部 100 点。
2. **`sellglod` 恰好等于 `buyglod` 的一半**（750/600/500/750/600/800/850/650）—— **8/8 成立**，是一条事实上的"回收率 50%"约定（无字段表达该比例）。
3. **`baseattack` 与买价不单调 ⇒ 原始数值不平衡**：`Dante` 买价 1200 却只有 `baseattack 100`（全表最低）；`CrackIt` 买价 1500 有 300。⇒ 8 个技能之间存在**明显的性价比失衡**，JSTM 若沿用需重排。
4. **目录名与 `name` 字段大小写不一致的有 2 处**：目录 `long` / `recallCountermand`（小写）↔ `.att` 的 `name Long` / `name RecallCountermand`（首字母大写）。⇒ **"目录名"与"技能逻辑名"是两套字符串**：`SkillFactory::createSkill` 比较的是 `m_name`（`.att` 的 `name` 值），而 `AppDelegate.cpp:175-184` 的 `skill[8]` 预热数组必须与之一致 —— 与正文 §2.12 的记录相互印证，是本项目的一处真实隐患。

## C.2 怪物属性表全表（`Resources/Monster/<名>/<名>.att`，10/10 已读）

| # | 目录/英文名 | 首行中文名 | `attack` | `blood` | `defense` | `speed` | `exp` | `glod` | `frames` |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `BlackDragon` | 黑龙 | 120 | 320 | 40 | 5 | 100 | 30 | 6 |
| 2 | `Dragon` | 小飞龙 | 100 | 200 | 60 | 5 | 150 | 40 | 12 |
| 3 | `Ghost` | 亡灵 | 250 | 200 | 40 | 5 | 150 | 60 | 6 |
| 4 | `Kougamon` | 甲兽 | 180 | **700** | **120** | 5 | 180 | 50 | 6 |
| 5 | `Lion` | 小狂狮 | 250 | 560 | 60 | 5 | 200 | 70 | 5 |
| 6 | `Minotaur` | 牛头怪 | 255 | 500 | 100 | 5 | 200 | 80 | 5 |
| 7 | `Octopus` | 章鱼哥 | 265 | 600 | 80 | 5 | 200 | 80 | 6 |
| 8 | `Pterosaur` | 肥龙 | 300 | 500 | 100 | 5 | 300 | 80 | 7 |
| 9 | `SkeletonMaster` | 骨法师 | 280 | 560 | 80 | 5 | 300 | 100 | 9 |
| 10 | `TarrasqueMessenger` | 魔龙使者 | 300 | 600 | 80 | 5 | 300 | 100 | 6 |

**★ 导出的 4 条观察**：
1. **`speed` 10/10 全部是 `5`** ⇒ **怪物行动速度完全没有差异化**。这与"`Monster` 有 `speed` 字段、被 `initProperty` 读入、但战斗流程未使用"**互相印证**：`speed` 属于"读了但不用"的字段。
2. **不存在单调强度梯度**：`Dragon`（attack 100 / blood 200）最弱却 `frames 12`（帧数最多）；`Kougamon`（blood 700 / defense 120）最肉但 attack 只有 180 ⇒ 10 只怪是**"坦克型 / 输出型 / 均衡型"各有侧重**，而非线性升级序列。
3. **奖励与强度弱相关 ⇒ 存在最优刷怪点**：`Kougamon`（attack 180）给 exp 180 / glod 50，而 `Ghost`（attack 250）只给 exp 150 / glod 60 —— 单位强度收益差异明显。
4. **`frames` 范围 5～12**，配 `Monster::initMonsterAnimation` 的 `setDelayPerUnit(0.15)` + `RepeatForever`（`Monster.cpp:72-92`）⇒ 帧数只决定"呼吸/移动"动画时长（5 帧 ≈ 0.75 s，12 帧 ≈ 1.8 s），**与战斗节奏无关**。

## C.3 ★ 与任务系统的交叉印证（跨文件一致性闭环）

| 怪物名（`Resources/Monster/` 目录，10 个） | 对应任务模板（`Resources/Task/` 的 `schedulewho`） | 击杀需求（`allschedule`） | 奖励（glod / exp） |
|---|---|---|---|
| `BlackDragon` | `Task1.tsk` 黑龙肆虐 | 6 | 500 / 600 |
| `Dragon` | `Task2.tsk` 飞龙坐骑 | 6 | 600 / 550 |
| `Ghost` | `Task3.tsk` 亡灵扰人 | 7 | 550 / 550 |
| `Kougamon` | `Task4.tsk` 甲兽壳 | 8 | 700 / 600 |
| `Lion` | `Task5.tsk` 狂狮伤人 | 8 | 750 / 600 |
| `Minotaur` | `Task6.tsk` 怪牛打人 | 8 | 760 / 620 |
| `Octopus` | `Task7.tsk` 章鱼肉 | 7 | 900 / 700 |
| `Pterosaur` | `Task8.tsk` 肥龙戏人 | 8 | 950 / 750 |
| `SkeletonMaster` | `Task9.tsk` 摄魂法师 | 8 | 1000 / 800 |
| `TarrasqueMessenger` | `Task10.tsk` 魔龙使者 | 10 | 1000 / 800 |
| （无对应怪物） | `Task11.tsk` 访亲问友（`type 2003` = T_ACCESS） | 1（`curschedule` 已为 1 ⇒ 接即完成） | 600 / 600 |

**⇒ 【已确认】10 只怪物 ↔ `Task1..Task10` 的 `schedulewho` 严格一一对应、无遗漏无多余**；任务奖励（glod 500→1000 / exp 550→800）与怪物强度（attack 100→300 / exp 100→300）**同向递增**。
⇒ 这 10 组"怪物 + 任务"构成本项目**唯一的 PvE 内容闭环**，可直接作为 JSTM 前 10 级新手任务的数值对照样本；`Task11` 是唯一的非击杀任务，且被设计为"接即完成"（详见 `task.md` 附录 D）。

## C.4 补充：1 处字段语义澄清

| 项 | 结论 | 证据 |
|---|---|---|
| `Monster` 的 `m_name` 最终值 | **`.att` 首行的中文名会被覆盖为英文名**。`Monster(const std::string& name)` 构造内 `initProperty(name)` 把 `.att` 第 2 个 token（中文名）读进 `m_name`（`Monster.cpp:58-60`）；但 `Monster::createWithName` 在构造完成后立刻又执行 `pRet->m_name = name;`（`Monster.cpp:25`，`name` 为英文名）⇒ **中文名被丢弃**。怪物中文名实际只通过 `TaskSystem::m_entocn`（17 条硬编码映射，`TaskSystem.cpp:18-34`）用于任务面板显示 | `Monster.cpp:20-35`、`:48-70`、`TaskSystem.cpp:18-34` |
