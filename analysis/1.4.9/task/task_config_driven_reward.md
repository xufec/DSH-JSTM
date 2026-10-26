# 任务奖励「配置驱动」—— 直接解码 `award_assets`（✅ 完成）

> **目标**：奖励不再用手写字段，而是**直接读与客户端同构的 `award_assets`**，
> 用 `AssetsEnToCode` 反查字段名 ⇒ **奖励完全由 1.4.9 配置驱动**。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① 新增 **`ASSETS_EN_TO_CODE`**（38 项，**逐项从客户端 `config_game_data.luac` 的 `AssetsEnToCode` 反汇编读出**）+ `CODE_TO_ASSET` 反向表<br>② 新增 **`decode_award_assets()`**：把 `[[code,num],…]` / `[{code,num}]` / `[{1=..,2=..}]` 三种写法统一解码成 `{资产名: 数量}`，**未在表里的 code 记入 `unknown` 且不发放（不猜）**<br>③ 新增通用资产表 **`role_assets(rid, name, amount)`** + `db_get_assets` / `db_add_assets`（任何 `AssetsEnToCode` 里的资产都能发）<br>④ **`role_state()` 合并 `role_assets`（资产表优先）**<br>⑤ **`12403` 改为解码 `award_assets`**（无 `award_assets` 时才回退到手写 `reward_*`）<br>⑥ **给"提交后的角色刷新推送"补了日志**（自查发现原先无日志、无法判断刷新是否发生） |
| `server/config.json` | 任务奖励改为**与客户端同构**：`"award_assets": [[2,1290],[4,500],[15,500]]`；**移除**手写的 `reward_exp/reward_coin/reward_gold` |

---

## 2. 解码验证（**已确认**）

```
decode_award_assets([[2,1290],[4,500],[15,500]])
  → {'coin': 1290, 'exp': 500, 'hero_exp': 500}      未知 code: []
```

对照 `AssetsEnToCode`：`2=coin`（协议字段名；**界面名=银魂币**）、`4=exp`（经验）、`15=hero_exp`（伙伴经验）。

> ⚠ **更正**：此处曾写「`2=coin`（金魂币）」。`coin` 是协议字段名，界面上显示为**银魂币**；
> 金魂币是 `coupon`(code 3)。依据：`task_reward_currency.md` 文末的界面确定性读数（2026-09-17），
> 并于 **2026-09-18 用「三值互异 + 已知真值」实验复验确认**（金图标=133万=`coupon`）。

**⇒ 与客户端 `Config.Mission[10010].award_assets` 完全一致，且无未知 code。**

---

## 3. 端到端实测（**已确认**）

```
[11:35:31]  >> cmd=10302                                ← 客户端登录时请求（发奖前）
[11:35:31]  << 10302 SC_10302 lev=7 exp=0 gold=1000 gold_acc=5000
[11:35:31]  >> cmd=12403 ? body(8)=00 00 27 1a 2d 2d 2d 2d
[11:35:31]  ** mission 10010 award_assets=[[2,1290],[4,500],[15,500]]
                          -> delta={'coin':1290, 'exp':500, 'hero_exp':500}
[11:35:31]  << 12403 SC_12403 commit mission_bid=10010 code=0 (13 bytes)
[11:35:31]  << 12406 SC_12406 del_mission_list=[10010] (12 bytes)
[11:35:31]  << 10302 (refresh after commit) lev=7 exp=500 gold=1000 coin=1290   ← ★
[11:35:31]  << 10301/10303 (refresh after commit) coinsent=1290                 ← ★
[11:35:31]  ** mission 10010 committed: +500 exp, +1290 coin, +0 gold
                          (now exp=500 coin=1290 gold=1000)
```

**数据库：**

```
role_assets: [{'name':'coin','amount':1290}, {'name':'exp','amount':500}, {'name':'hero_exp','amount':500}]
roles      : {'exp':0, 'gold':1000, 'coin':0}     ← 固定列不再被奖励占用
missions   : {'mission_bid':10010, 'mission_status':3, 'commit_num':1}
```

**⇒ 三项资产全部落库，包括此前**手写字段时代根本没有的 `hero_exp`** —— 这正是"配置驱动"的收益。**

---

## 4. ★ 本轮自查发现并修正的问题

| # | 问题 | 处理 |
|---|---|---|
| 1 | **奖励刷新推送没有日志**，导致曾误判"`10302` 里 exp=0 是刷新 bug" | **补上日志**后次序一目了然：那条 `exp=0` 是**登录时**客户端请求的（发奖前），**不是刷新问题** |
| 2 | 编辑过程中一次替换把 `db_init` 里 `missions` 建表的行拆坏（`IndentationError`） | **自查发现并立即修复**，`ast.parse` 通过 |
| 3 | 手写 `reward_*` 与 `award_assets` 可能不一致 | 改为**只认 `award_assets`**，手写字段仅作回退 |

---

## 5. 仍然缺失 / 待验证（如实）

1. **`role_assets` 只在首次发奖时出现** —— 初始资产仍来自 `roles` 固定列。
   ⇒ **若要把"资产"整体统一到 `role_assets`**（含初始值播种），是一次重构，本轮未做。
2. **界面读数有出入**：本轮视觉把 `1,290` 标到了另一个图标旁、把「金魂币」读成 0；
   而**服务端已确认 `10303` 里 `coin=1290` 正确下发**（日志 `coinsent=1290`）。
   ⇒ **以服务端字节为准，界面读数留待更清晰的核对手段**（不据此下结论）。
3. `AssetsEnToCode` 里 **code 34/35/36 未出现** ⇒ 保持**未知**，未编造。
4. 其余任务（`10070`/`35000` 等）的 `award_assets` **尚未录入**我们的 config。
5. NPC 对话 UI 仍未打通（`scene_model` handler 后段 nil）。

---

## 6. 本轮结论

| 项 | 结果 |
|---|---|
| `award_assets` 解码表 | ✅ 从客户端读出（38 项） |
| 解码函数 | ✅ 已验证（无未知 code） |
| 配置驱动发奖 | ✅ 已验证（`coin`/`exp`/`hero_exp` 三项全发） |
| 通用资产表 `role_assets` | ✅ 新增并落库 |
| 提交后刷新角色数据 | ✅ 已验证（`10302 exp=500`、`10303 coin=1290`） |
| 未知 code 处理 | ✅ **记录但不发放（不猜）** |
| 改 APK / UI | ✅ 未做 |

**交付物**：本文件、`server/mock_server.py`、`server/config.json`、
`server/state/roles.db`（新增 `role_assets` 表）

---

**[WAITING FOR NEXT INSTRUCTION]**
