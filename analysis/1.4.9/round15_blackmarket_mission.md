# 第十五轮：NPC 对话闭环 + 黑市/任务提交修复

> 用户确认：**「能弹出对话了」** ⇒ **十三轮谜题闭环** ✅
> 随后报两个新问题：① 黑市商贩点击无效　② 对话后的任务提交联通有问题

---

## 一、✅ 十三轮谜题**闭环确认**

**根因（第十四轮定位并修复）：**
```
服务端 config.json 的 skills = [{"bid": 1001}]
但 **1001 不在客户端 Config.Skill 里**（真实 bid: 10000=普攻 / 10001=逃跑 / 10002=撤退 …）
  → kHaveSkill 查 Config.Skill[1001] = nil
    → 索引 nil ⇒ 抛异常
      → 异常沿栈传播 ⇒ changeScene 中断 ⇒ 场景初始化不完整
        → NPC 对话失败
```
**修复：`skills` 改为真实 bid（10000/10001/10002）**
**验证：`sceneStart_oktrue`，异常栈消失** ⇒ **用户实机确认「能弹出对话了」** 🎉

---

## 二、① 黑市商贩点击无效 —— ✅ **已修复**

### 取证（客户端字节码）

```
game/blackmarketeer/blackmarketeer_ctrl.luac:
  RegisterProtocal 30600 on30600 / 30601 on30601 / 30602 on30602 / 30603 on30603
  **GetPrototype 30602**        ← ★ 客户端主动发送这条（即"点击"）
```
**⇒ `30600~30603` 原先**无人应答** ⇒ 点击无效。**

### 协议定义（`manual.md`，均无 `D|Dsc*|` ⇒ 安全）

```
30600 (CS 空)                → SC{refresh_times:u8, next_time:u32, items:table(id:u8,status:u8)}
30601 (CS 空)                → SC{code, msg}
30602 CS{Id:u8, type:u8}     → SC{code, Id:u8, msg}      ★ 客户端发的
30603 CS{items:table(item_bid:u32,num:u32)} → SC{code,msg}
```

### 实现与验证

```
30600 黑市列表 -> 7 字节
30601 刷新     -> code=1
30602 购买     -> code=1        ← ★ 就是客户端点的那条
30603 批量卖   -> code=1
```

**⚠ 黑市商品表**原版未取证** ⇒ 取 `config.black_market_items`（默认空），**未编造**。**

---

## 三、② 任务提交"联通有问题" —— ✅ **已修复（根因是服务端误判）**

### 取证（真机日志）

```
[20:34:27] >> cmd=12403 ? mission_bid=10020
[20:34:27] << 12403 SC_12403 mission_bid=10020 **code=0 (no such)**     ← ★ 失败
[20:34:29] << 12400 SC_12400 mission_list=**1**                          ← 当时 DB 只有 1 条
...
[20:38:12] >> cmd=12403 ? mission_bid=10010
[20:38:12] << 12403 SC_12403 commit mission_bid=10010 **code=1(TRUE)**   ← 成功
```

**⇒ 关键：`10020` **在 `mission_config.json` 里是合法的**（name=切磋魂技），
但 20:34 那次提交时**它还没被播种到 DB** ⇒ 服务端把它误判为"不存在"。**

### 修复

```python
if m is None and mission_def(bid):
    db_save_mission(rid, {完整 13 字段, status=2})
    rows = db_get_missions(rid); m = rows.get(bid)
    log('.. 12403 任务 %d 不在 DB 但在配置里 ⇒ 已自动播种' % bid)
```
**⇒ 任务只要**在配置里**就不会再被误判"不存在"；只有配置里也没有的 bid 才真的回 `code=0`。**

### 附带：`12430~12432`（悬赏/刷新）

**真机请求过但未实现，已补：**
```
12430 CS{type:u8} → SC{code,quantity,msg}                      -> 4 字节
12431 CS(空) → SC{bonus,cur_quantity,free_refresh_times,...}    -> 11 字节
12432 CS(空) → SC{code,msg}                                     -> 3 字节
```

### ★ 另说明：`12405`/`12406` **本来就已实现**

**我第一版的检测脚本把它们误标为"未实现"** —— 因为它们是用 `pack_frame(12405, ...)` **主动推送**的，
不是 `if cmd == 12405` 分支。**实测日志里它们正常发出**（`update_mission_list` / `del_mission_list`）。
**⇒ 第 8 处自我更正。**

---

## 四、探针瘦身

**第十二轮为诊断加的 `SceneView.New` / `sceneStart` / `setSceneInfo` wrapper，**
**在崩溃修复后已**关闭**（改为 `if false and ...`），保留代码以备后续诊断。**
**⇒ 减少对客户端运行时行为的干扰**（避免"点击无效"之类的副作用）。**

---

## 五、自查

```
mock_server.py OK ｜ lua-check OK（123864 字节）｜ 服务端 8080/9000 正常（PID 19136）｜ stderr 0 字节
改动：config.json（skills 真实 bid + black_market_* + bounty_*）
      mock_server.py（12403 稳健化 + 12430~12432 + 30600~30603）
      dsh_fake_login.lua（实验性 wrapper 关闭，已重新部署）
```

---

## 六、请实机确认两项

1. **黑市商贩** —— 点击现在有反应了吗？（会打开一个**空的黑市列表**，因为原版商品表未取证）
2. **NPC 对话里的任务提交** —— 现在提交任务还报错吗？

**若黑市仍无效**，可能是客户端还依赖 `30600` 之外的东西（如 `config_black_market` 的具体条目）——告诉我，我继续查。
