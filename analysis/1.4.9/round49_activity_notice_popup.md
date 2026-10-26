# R49：进图活动预告弹窗「刷屏 + 重复」修复（+ 10922 全服活动状态补齐）

> **报障**：进图后弹出很多个弹窗，提示 宗门战 / 帝国之战 / 斗罗战场 / 魂师大赛 / 学院闯关
> 「…即将开启」，且**弹窗存在重复**。
> **纪律**：先取证再改；一次只改一个变量；被否证的假设全部保留在案（§4）。
> **复现环境**：MuMu `127.0.0.1:16384`，`绝世唐门 1.4.9`（探针版），服务端 `mock_server.py`（单进程）。
> **时间**：2026-09-28 22:40 – 23:24。

---

## 一、结论（TL;DR）

```
现象根因：客户端 activity_ctrl.luac proto#37 的「活动预告」链式弹窗，
          由**客户端本地配置**驱动，服务端下发的 status 不参与判定。
唯一稳定可控点：SC_10924（个人活动图标）**是否下发**。
修复：10924 回空表（config: send_personal_act_list=false）⇒ 两次真机复现 0 弹窗。
代价（如实）：同时少掉顶部「开服福利 / 中秋团圆 / 七天排行」3 个活动入口图标
             （它们指向本服并未实现的运营活动）。同一开关可切回。
```

---

## 二、取证：弹窗是什么、由谁驱动

### 2.1 弹窗本体（真机截图逐字）

```
标题：提示
正文：帝国之战活动在19时40分~20时40分开启，玩家快去战个痛快吧！
按钮：取消(41)   确定            ← 「(41)」是倒计时，会重置 ⇒ 看起来"重复"
```

### 2.2 文案与逻辑的归属（APK 资源扫描）

| 目标 | 命中文件 | 说明 |
|---|---|---|
| 文案模板「…活动在…开启，玩家快去战个痛快吧！」 | `assets/src/game/activity/activity_ctrl.luac` | **唯一命中**，是本地格式串 |
| `'<div fontcolor=%s>%s</div>活动在<div fontcolor=%s>%s</div>开启，…'` | 同上 proto#37（bc=487） | 活动名取 `Config.RiChang[id].name` |
| 活动 id ↔ 预告键 | 同上 proto#37 内 KSHORT | `101 xianmo / 107 menpai / 108 race / 111 guildwars / 112 diguowar / 113 peakwar / 115 chief / 116 julong / 118 guildcretarea` |
| `is_notice` ×54 | `assets/src/config/config_god_unite_data.luac` | `getGodWarNoticeConfig()` 的配置源 |

**逐条对上用户报的名称**（config_richang 活动类条目）：

| id | 名称 | 预告键 |
|---|---|---|
| 101 | 斗罗战场 | `xianmo` |
| 107 | 学院闯关 | `menpai` |
| 108 | 魂师大赛 | `race` |
| 111 | 宗门战 | `guildwars` |
| 112 | 帝国之战 | `diguowar` |
| 113 | 精英大赛 | `peakwar` |
| 115 | 首席争霸 | `chief` |
| 116 | 绝地凶兽 | `julong` |
| 118 | 宗门副本 | `guildcretarea` |

### 2.3 反汇编关键分支（`analysis/_activity_p37.txt`）

```
BC   9  TGETS data.status
BC  10  ISNEN A=2 D=0        ; if data.status ~= K(0)=1
BC  11  JMP   D=32772        ;   status == 1 ⇒ 直接返回（不弹、不继续）
BC  13  TGETS self.pushByScene
BC  15  CALL                  ;   否则：弹一次 + 链式继续下一条
...
BC 472  TGETS data.status     ; 弹完之后同样的守卫 ⇒ 链式走到列表尽头
BC 476  TGETS self.pushByScene
BC 478  CALL
```

⇒ 只要被走查到的活动 `status ≠ 1`，就**弹一次并继续下一条** —— 这正是"很多个 + 重复"。

---

## 三、★ 权威命令名（`protocol/cmd_table.json`，此前未用上）

| CMD | 权威名 |
|---|---|
| **10922** | **全服活动的活动状态** |
| 10923 | 全服活动的单个活动状态 |
| **10924** | **个人活动图标** |
| 10925 | 个人活动图标的单个活动状态 |

⇒ `10922` 的 id 空间是 **`config_richang` 的活动类条目**（101/107/108/111/112/…），
与 `10924` 的 `config_function` id 空间（1..91）**不是同一套**。
原实现 `10922` **恒回空表**（`w_u16(0)`）。

---

## 四、★ 对照实验全记录（一次一个变量，同机复现）

| # | 变量 | act_list | 结果 | 证据 |
|---|---|---|---|---|
| A | 原状 | 10924=69 | ❌ 弹窗复现 | `t1_5` / `t3_5` / `t4_5` |
| B | 把预告 id **补进** 10924 | 10924=75 | ❌ 弹窗仍在 | `t4_5` |
| C | 10922 回 status=1（9 条） | 10924=75 | ❌ 弹窗仍在 | `t4_5` |
| D | 10924 **剔除**预告 id | 10924=66 | ⚠️ **不稳定**：t5 干净 / t7 复现 | `t5_4`（干净）、`t7_4`（复现） |
| E | **10924 回空表** | 10924=0 | ✅ **两次复现均 0 弹窗** | `t2_4..t2_7`、`t8_1..t8_9` |
| F | 10922 回全量 19 条（10924=66） | — | ❌ 弹窗复现（说明 10922 的**条目集合**也参与） | `t6_4` |
| G | `repush_10200_on_init=false` | 10924=69 | ❌ 不影响弹窗（只影响是否二次推场景） | `t1_*` |

**被否证的假设（保留不删）**：
1. ~~"补上 `data.status=1` 就能让客户端走 return 分支"~~ ⇒ B / C 都否证。
   实际 `data` 取的是**本地配置**（无 status 字段），下发 status 不参与该判定。
2. ~~"预告 id 用 `config_function` 空间即可"~~ ⇒ 预告走的是 `config_richang` 空间，两套不相交。
3. ~~"关掉 10200 的二次推送能消除重复"~~ ⇒ 实验 G 否证（且 `repush_10200_on_init=false`
   会让进场景变慢/停在黑屏更久，已回滚为 `true`）。

---

## 五、修复实施

### 5.1 改动

| 位置 | 原状 | 改后 |
|---|---|---|
| `mock_server.py` `if cmd == 10924` | 回 69 条（config_function 活动） | 回**空表**；附完整取证与取舍注释；开关 `send_personal_act_list` / `disable_10924` |
| `mock_server.py` `if cmd == 10922` | 恒回**空表** | 回 `notice_act_ids`（9 条预告集合），`status=1`；附"回全量 19 条会复现"的实测注记 |
| `mock_server.py` | — | 新增 `richang_activity_tasks()`（`type_name=='活动'`，19 条） |
| `server/config.json` | — | `send_personal_act_list=false`、`disable_10924=true`、`notice_act_ids=[…9…]` + 三个 `_note` |
| `tools/_fix_r49_cfg.py` | 新增 | 幂等写入上述配置，可重跑 |

### 5.2 取舍（写清楚，不藏）

回空表的代价是顶部少 3 个图标：**开服福利 / 中秋团圆 / 七天排行**（`t8_9` 实测已消失），
它们指向的运营活动**本服并未实现**。若更看重这 3 个图标：
```json
{ "send_personal_act_list": true }
```
⇒ 图标回来，**弹窗也回来**（同一枚硬币两面，已验证无法只取其一）。

### 5.3 真机复验（两次独立复现）

```
t2_1..t2_7  全部为完整帧（无 158KB 黑屏+弹窗帧）；t2_7 视觉复核：无弹窗、主城正常
t8_1..t8_9  全部为完整帧；t8_4 视觉复核：无弹窗（当时在邮件界面）、t8_9：主城正常
对照（修复前）t1/t3/t4/t6/t7 均出现 4~5 帧"纯黑 + 提示弹窗"
```

---

## 六、全量验证（改动后当场复跑）

| 项目 | 结果 |
|---|---|
| `py_compile` | OK |
| `lint_dispatch_shadow.py` | 专用 165 / 默认 63 / 未开放 24 ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 一致 2463 / **不一致 0** |
| `audit_sc_conformance.py --generic --unsupported` | 命令 87：一致 86 / **不一致 0** / 空规格 1 |
| `audit_sc_live.py --unsupported` | 命令 87：**一致 87 / 不一致 0 / 无应答 0** |
| `audit_dedicated.py` | 查询型 62：**符合规格 62 / 不符 0** |
| 进程卫生 | 9000 端口**恰好 1 个监听**（重启前后各查一次） |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 10922 / 10924 改动 + `richang_activity_tasks()` + 取证注释 |
| `server/config.json` | 开关与 `_note` |
| `tools/_fix_r49_cfg.py` | 配置落地脚本（幂等） |
| `analysis/_activity_p37.txt` | activity_ctrl proto#37 反汇编（487 条指令，弹窗逻辑真源） |
| `analysis/_daily_cell_p9.txt` | daily_cell proto#9 反汇编（"即将开启"单元格逻辑） |
| `analysis/_richang_dis.txt` | config_richang 全表反汇编（活动条目字段实证） |
| `tools/_find_popup_in_apk.py` 等 5 个扫描器 | 文案/id 空间定位工具 |
| `shots/t1_*..t8_*`、`shots/t2_4/t5_4/t8_4` 等 | 对照实验的真机帧证据 |
| `analysis/1.4.9/round49_activity_notice_popup.md` | 本报告 |

---

## 八、遗留（诚实）

1. **`10922` / `10924` 的 `status` 语义仍未取证**：`pushByScene` 走查用的 `data` 到底来自哪个存
   （`Config.RiChang` 还是两条消息的合并）**未逐条确认**；本轮只做到"用可复现的开关把症状消除"。
   ⇒ 若将来要恢复活动图标又不想有弹窗，唯一出路是**客户端侧补丁**
   （把 `config_god_unite_data` 的 `is_notice` 置 0，或改 `activity_ctrl` proto#37 的链式调用），
   需要走 APK 重打包 + 签名流水线（`patched/*.apk` + `dsh.keystore`，项目已有）。
2. 实验证明 `10922` 回**全量 19 条**时弹窗更容易复现 —— 该现象的机制**未查清**，仅作为"不要想当然回全量"的注记保留。
3. 本轮**未改**玩家数据、未还原 `roles.db`、未跑 `replay_captures.py`；
   实验期间玩家角色 `rid=1001` 仅"登录→进主城"，无任何写入。
