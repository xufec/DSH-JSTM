# R48 续：进度**真实挂钩** —— 任务提交 ⇒ 日常次数 + 成就进度（2026-09-19）

> 项目方指示："下一步可以不再靠 admin 造数据，而是按触发链真实挂钩。"
> 本轮把这件事做成了，并且**先证伪了一条看似最直接的实现路径**。

---

## 一、★ 关键取证：`trigger_mod/trigger_fun` **不是服务端配置链接**

直觉上，成就 10100 `{trigger_mod:'mission', trigger_fun:'hongchen'}` 应该能在
`config_mission` 里找到 `hongchen` 这个分组。**实测找不到**：

| 检索 | 结果 |
|---|---|
| `hongchen` 出现在哪些文件 | `all_res_file` / `config_buff_data` / `config_chengjiu` / **`config_guide`** / **`config_promote`** / `ghost_ctrl` / `ghost_mon` |
| `hongchen` 是否出现在 `config_mission` | **否** |
| `config_mission` 全部字段（32 个） | `bid/name/desc/type/type2/lev/realm/times_type/times_arg/…` —— **没有任何指向 `huoli_id` 或成就 `bid` 的字段** |

⇒ `hongchen`/`zhuoyao` 是**客户端 Lua 处理器名**（出现在客户端 ctrl 与 guide/promote 配置里），
**不是服务端可见的分组键**。

**这条否证很重要**：它说明"成就与任务的对应关系"在原版里**没有被显式配置表达**——
所以**不存在"自动从配置推出映射"的实现路径**，硬要找只会变成猜。

---

## 二、★ 走通的路：两者本来就是**同一个可数事件**

```
日常 208「学院任务」        → 面板上的『次数』 = 该线**完成轮数**
成就 10100「史莱克弟子」desc=完成5轮学院任务, val=5
                                            ↑
                              两者语义相同 ⇒ 一次「任务提交」应同时 +1
```

而服务端**已经有**这个事件：`12403`（任务提交 → 结算）已在实现中
（含发奖、落库、`12405` 增量推送）。⇒ **挂钩点就在这里**。

### 2.1 实现

```python
def credit_mission_done(cfg, rid, mission_bid):
    """任务提交成功后：按分组给日常次数 +1、给对应成就进度 +1。"""
    mtype = int((mission_def(mission_bid) or {}).get('type') or 0)
    for g in chengjiu_map():                      # server/_chengjiu_map.json
        if int(g['mission_type']) != mtype:
            continue
        db_daily_add(rid, int(g['daily_tid']), 1, 0)   # 次数 +1（活力计 0，见下）
        for b in g['ach_bids']:
            db_chengjiu_add(rid, int(b), 1)            # 成就进度 +1
        return g['daily_tid'], g['ach_bids']
    return None, []
```

挂在 `12403` 成功应答**之前**（`mock_server.py`），失败不影响提交主流程（try/except）。

### 2.2 映射做成**可编辑的校准产物**，不写死在代码里

`server/_chengjiu_map.json`：

```json
{"groups": [{"mission_type": 1, "daily_tid": 208,
             "daily_name": "学院任务", "ach_bids": [10100, 10101, 10102, 10103]}]}
```

文件里的 `_note` 逐条标了**置信度**：

| 事项 | 置信度 |
|---|---|
| 事件来源 = `12403` 提交成功 | 【已确认】 |
| 日常次数 = 该线完成轮数（`13786.richang_list[面板id].num`） | 【已由真机证实】 |
| **`mission_type = 1` 即"学院线"** | **【待校准】**：`10010 斗罗魂师`/`10020 切磋魂技`/`10030 武魂觉醒` 都是 `type=1`，且都是主城任务列表里的学院主线 |
| 每次给多少**活力(val)** | **未取证 ⇒ 计 0**（面板显示学院任务 活力 0/70、次数 10，疑似 7/次，但 70 这个数在 `config_richang` 面板条目里找不到 ⇒ 不编） |

⇒ **若与原版不符，只改这个 JSON，不必动代码**。

---

## 三、验证（用测试角色，不碰玩家账号）

`tools/verify_mission_hook.py`：

```
=== 挂钩配置 ===
  groups: [(1, 208, [10100, 10101, 10102, 10103])]
  选中 type=1 任务 bid=10010 (斗罗魂师)  共 262 个

提交前: 日常208次数=0  成就10100进度=0
  12403 提交 bid=10010 → code=1
提交后: 日常208次数=1  成就10100进度=1
   ✓ 日常「学院任务」次数 +1
   ✓ 成就「史莱克弟子」进度 +1
  玩家(1001) chengjiu_progress 行数=0（不受影响）
=== 结果: PASS ===
```

**同时修掉了验证脚本自己的一个偏移错误**：`SC_12403{mission_bid:u32, code:u8, msg:s}`
的 `code` 在**偏移 4**，我一开始写成 5（读到了 `msg` 长度的高字节）⇒ 打印出 `code=0` 的假象。
**这正是"测试失败要先怀疑测试"的又一例。**

---

## 四、复核

| 项目 | 结果 |
|---|---|
| `lint_dispatch_shadow.py` | **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 条：**0 不一致** |
| `audit_sc_conformance.py`（全量 1635） | **0 不一致** |
| `audit_sc_live.py --unsupported` | **89/89** |
| `audit_dedicated.py` | **61/61** |
| `verify_attr_power` / `verify_account` / `verify_role_switch_guard` / `verify_dungeon` / `verify_arena` | 全部 **PASS** |
| `verify_mission_hook`（新） | **PASS** |

---

## 五、产出

| 文件 | 说明 |
|---|---|
| `server/_chengjiu_map.json` | ★ 分组映射（**可编辑校准产物**，含逐条置信度说明） |
| `server/mock_server.py` | `credit_mission_done()` + 挂在 `12403` 成功分支 |
| `tools/verify_mission_hook.py` | 挂钩端到端验证（自带清理） |

---

## 六、★ 这一步的意义与下一步

**意义**：进度**第一次由玩家真实行为产生**。此前每一轮都停在
"结构对了、但数据只能靠 admin 写"（副本层数、竞技场战绩、日常次数、成就进度）；
现在**日常次数与成就进度会跟着玩家做任务自己长**——而且**一个事件同时喂两处**。

**下一步（按同一套路复制）**：成就表里还有几类 `trigger_mod` 可挂：

| trigger_mod | 语义 | 服务端已有的事件 |
|---|---|---|
| `mission` | 任务/悬赏（`zhuoyao`、`7`=悬赏） | ✅ `12403`（本轮已通）／`12430~12432` 悬赏 |
| `escort` | 护送（`护送凤仪1次`） | 需先实现护送玩法 |
| `vip_single` | 通关副本（`通关一次新生考核`） | 与 R45 副本进度同源，可挂 `13034` 结算 |
| （数字） | 悬赏次数（`10500 赏金新手 = 悬赏10次`） | `12430~12432` |

⇒ 建议**下一步先把 `mission` 这一类挂全**（悬赏/监察线），
再按 `config_richang` 的其余 11 个 `huoli_id>0` 任务逐个补分组——
**每补一行就是一行 JSON**，代码不用再动。
