# 剧情链逐步解锁 + `progress` 完成判定（✅ 两项都已实现并端到端验证）

> **本轮目标**：① 实现剧情链逐步解锁；② 解码 `progress` 用于完成判定。
> **结论**：两项都完成，且**在同一次实机跑测中一起验证通过**。

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① **`mission_chain()` 重写为"剧情链逐步解锁"**：把 APK 主线按 bid 升序排成链，找**第一个未完成**的位置作为**解锁指针**，只从指针处往下发 `mission_chain_max` 条（`mission_chain_lock=false` 可关）<br>② **播种时解码 `progress` 生成完成条件**：`progress[0] = [条件名, 目标id, 数量]` → 写入任务的 `target` / `target_value`<br>③ **`12403` 增加完成判定**：有进度要求且 `value < target_value` ⇒ 回 `code=1`（`mission_skip_condition=true` 可临时跳过，便于联调）<br>④ 新增 **`mission_progress_advance(rid, cond_name, target, n)`**：把满足条件的在途任务推进 `n` 点，够了把 `process_status` 置 1（**供后续把击杀/采集事件接进来时调用**） |
| `server/config.json` | 新增 `mission_chain_lock`（默认 true）、`mission_skip_condition`（默认 false）、`mission_chain_max` |

---

## 2. ★ `progress` 解码（**已确认**）

从 `server/mission_config.json`（846 条，`progress` 非空 **397** 条）读出：

| bid | name | `progress` | 解出的条件 |
|---|---|---|---|
| **10010** | 斗罗魂师 | `[]`（空） | **无条件** ⇒ 到 `commit_npc` 处即可提交 |
| 10020 | 切磋魂技 | `[['fight_mon', 20001, 1], [0,0,20010,0]]` | `fight_mon` 击杀 **20001** × **1** |
| 10070 | 巫风挑战 | `[['fight_mon', 20002, 1], [0,0,20020,0]]` | `fight_mon` 击杀 20002 × 1 |
| 10092 | 猎取魂环 | `[['collect_elem', 20001, 1], [10001, None]]` | `collect_elem` 采集 20001 × 1 |
| 10100 | 猎取魂环 | `[['fight_mon', 20003, 1], [0,0,20021,0]]` | `fight_mon` 击杀 20003 × 1 |

**⇒ `progress` 是"两行"结构：**
- **第 1 行 = `[条件名, 目标id, 数量]`** ⇒ **这就是完成条件**
- 第 2 行（如 `[0,0,20010,0]`）含义**尚未确认** ⇒ **未使用、未猜**

**⇒ 条件名（`fight_mon` / `collect_elem`）与 Phase 4 读到的 `MissionCode` 表对应。**

---

## 3. 剧情链逐步解锁（**已验证**）

```
初始链:            [10010, 10020, 10030, 10040, 10051, 10052]
提交 10010 后:     [10020, 10030, 10040, 10051, 10052, 10053]   ← 指针前移
再提交 10020 后:   [10030, 10040, 10051, 10052, 10053, 10054]   ← 再前移
```

**规则**：链上第一个"未完成（`mission_status != 3`）"的位置即**解锁指针**，
只从指针处往下发 ⇒ **完成一条、下一条自动解锁**。

---

## 4. 完成判定（**已验证**）

```
10020 的条件: target=20001 need=1
推进 fight_mon/20001 → 受影响 [10020]
10020 现状: value=1 process_status=1     ← 满足后置为"可提交"
```

**`12403` 的判定逻辑**：
- `target_value == 0`（如 `10010`）⇒ **直接可提交**
- `target_value > 0` 且 `value < target_value` ⇒ **回 `code=1`（条件未满足 x/y）**

---

## 5. ★ 端到端实测（同一次跑测，两项一起验证）

```
[11:50:34]  >> cmd=12403 ? body(8)=00 00 27 1a 2d 2d 2d 2d
[11:50:34]  ** mission 10010 award_assets=[[2,1290],[4,500],[15,500]]
                          -> delta={'coin':1290, 'exp':500, 'hero_exp':500}
[11:50:34]  << 12403 SC_12403 commit mission_bid=10010 code=0 (13 bytes)
[11:50:34]  << 12406 SC_12406 del_mission_list=[10010] (12 bytes)
[11:50:34]  ** mission 10010 committed: +500 exp, +1290 coin, +0 gold
                          (now exp=500 coin=1290 gold=1000)
[11:50:35]  << 12400 SC_12400 mission_list=7 (246 bytes)      ← ★ 链已前移（10010 被排除）

数据库：
missions: [(10010, status=3),
           (10020, status=1, target=20001, need=1),           ← ★ 条件来自 progress
           (10030,1), (10040,1), (10051,1), (10052,1), (10053,1), (10054,1)]
role_assets: [coin=1290, exp=500, hero_exp=500]
```

**⇒ 一次跑测同时证明：**
1. **剧情链**：下发 8 条主线，完成后指针前移（`mission_list` 7 条）
2. **条件来自 `progress`**：`10020` 带上 `target=20001 / need=1`
3. **奖励配置驱动**：`coin 1290 / exp 500 / hero_exp 500` 三项全发并落库

---

## 6. 仍然缺失 / 待验证（如实）

1. **没有把真实游戏事件接到 `mission_progress_advance`** —— 击杀/采集事件走哪条协议**尚未确认**，
   所以 `10020` 这类"需要进度"的任务目前**只能靠 `mission_skip_condition=true` 联调**，
   **不会自己完成**。
2. **`progress` 第 2 行含义未确认**（如 `[0,0,20010,0]`）⇒ 未使用、未猜。
3. **解锁粒度是"线性链"** —— 原版可能有分支/多链（`type` 之外还有 `realm`、`career` 等限制），本轮未做。
4. 界面只确认了下发条数，**未逐个核对任务栏显示**。
5. NPC 对话 UI 仍未打通（提交走 `MissionCtrl:submit`）。

---

## 7. 本轮结论

| 项 | 结果 |
|---|---|
| `progress` 解码 | ✅ **已确认**（`[条件名, 目标, 数量]`），397 条任务带条件 |
| 完成判定 | ✅ 已实现（`target_value`/`value`，`12403` 里校验） |
| 进度推进接口 | ✅ `mission_progress_advance()`（待接游戏事件） |
| 剧情链逐步解锁 | ✅ **已验证**（完成后指针前移） |
| 任务来源 | ✅ APK 全表（846 条 / 主线 262） |
| 奖励 | ✅ 配置驱动（`award_assets` + `AssetsEnToCode`） |
| 端到端 | ✅ 一次跑测同时验证链 + 条件 + 奖励 |
| 改 APK / UI | ✅ 未做 |

**交付物**：本文件、`server/mock_server.py`、`server/config.json`、
`server/mission_config.json`（846 条）、`logs/1.4.9/task_chain_tcp.log`

---

**[WAITING FOR NEXT INSTRUCTION]**
