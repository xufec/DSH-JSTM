# 最小回环 · 第 13 轮（goal round 7/20）★★★ 破关：`10200` 的 `code` 必须为 **0**（通则的例外）—— 客户端**真正进场景了**

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：把参考服 `10102` 之后的推送集合与本服比对，补齐差集。

---

## 〇、一句话结论

> **在参考服自己的实测注释里挖到了那条关键差异**：`code==1 才是成功` 这条通则**有一个例外 —— `10200` 必须发 `code = 0`**
> （`scene_controller.luac proto[16]` 是 `if resp.code ~= 0 then message2(resp.msg) end`）。
> 我的最小回环服**一直发的是 `code = 1`** ⇒ 客户端弹错误、**不真正进场景**。
> 改成 `0` 之后，客户端状态从
> `state=scene_nil_role_nil_recv_48` / `view=no_scene_view_instance`
> 变成 **`state=scene_table:_0xb546d510_role_table:_0xbaee0f80_recv_119`**、
> **`loadState=isLoadState_true`**、`view=…via_SceneModel.scene`；
> 并且客户端开始发 **`10300`（角色初始化）×3、`15203`（NPC 对话）、`12403`（任务提交）**，
> 命令种类从 38 涨到 **45**。

---

## 一、★ 病因与修法（一行改动，出处是字节码）

参考服 `server/mock_server.py` 在 `10102` 分支里留了实测注释（原样摘录）：

```
★ code 必须 = 1（TRUE == 1）：denglu_ctrl.luac proto[30] on10102Login 的分支是
    if resp.code == TRUE then … SendProtocal(10300) ; GameNet:LoginSucceedSendProtocal()
                             ; DengluEvent:Fire(LOGIN_SUCCESS)
    else CommonAlert:show(resp.msg, ...)          ← 弹框，且不再往下走
  而 scene_controller.luac proto[1] 才把 LOGIN_SUCCESS 绑到进入场景。

⚠ 注意 10200 相反：scene_controller.luac proto[16] 是
    `if resp.code ~= 0 then message2(resp.msg) end`，即 0 才是成功，
  所以 _send_10200 里的 w_u8(0) 是**正确**的，不要一起改。
```

**本服原先的实现**：`push_10200()` 发 `{'code': 1, …}` ❌
**本轮的修改**：`{'code': 0, …}` ✅（连同注释写明这是通则的例外）

并**加了回归断言**防止再被改回去：`selftest.py` 新增
`check(e10200[1]['code'] == 0, '10200 的 code 必须是 0（该命令的例外约定）')`
⇒ 自检 **45/45 PASS**（此前 44 项，新增 1 项）。

---

## 二、★ 改前 / 改后（全部是客户端自己的落盘上报）

| 观测（探针上报） | 改前（live8） | **改后（live9）** |
|---|---|---|
| `t=state` | `scene_nil_role_nil_recv_48` | ★ **`scene_table:_0xb546d510_role_table:_0xbaee0f80_recv_119`** |
| `t=view` | `no_scene_view_instance` | ★ **`reslist_0_loading_false_…via_SceneModel.scene`** |
| `t=loadState` | `isLoadState_na_mapResCache_na` | ★ **`isLoadState_true_mapResCache_0`** |
| `hit_on10102Login` | （无） | ★ **`code_1_type_table`**（客户端 10102 处理器走**成功分支**） |
| 客户端命令种类 | 38 | **45** |
| 回环相关命令 | 只有 `10102/10300/10502` | ★ **`10300`×3、`15203`（NPC 对话）、`12403`（任务提交）** |

⇒ **`scene` 从 nil 变成 table、`role` 变成 table、场景加载完成** ——
这是本会话第一次把客户端**真正送进场景**。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★ **找到并修掉"进不了场景"的根因**：`10200` 的 `code` 用错了（通则例外）。
2. ★ **首次达到"客户端在场景内"**：`scene_table` / `role_table` / `isLoadState_true` / `recv_119`。
3. ★ **客户端开始进入玩法区域**：出现 `15203`（NPC 对话）、`12403`（任务提交）、`10300`×3。
4. **加了一条回归断言**（45/45），把这条"例外约定"固化下来，避免复发。
5. 方法学收获：**参考服代码里的实测注释本身就是一份高价值"对照表"** ——
   本轮靠它一次命中，比继续做字段级字节比对更省。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `mapResCache` 仍为 `0`（地图资源缓存没起来） | ⚠️ 但 `isLoadState_true` 已成立，说明**加载流程完成了**；`mapResCache_0` 是否有害待观察 |
| 2 | `12400`（任务列表）/ `20002`（发起战斗）仍未出现 | ❌ 下一步驱动 |
| 3 | 战斗 → 结算 → 掉落 → 提交 → 奖励 全链 | ❌ |
| 4 | `10200` 之外是否还有别的"code 例外"命令 | **UNKNOWN**（值得系统性扫一遍参考服的同类注释） |

---

## 四、下一轮直接照做（优先级）

1. ★ **系统性扫"code 例外"**：在参考服 `mock_server.py` 里把所有关于 `code` 的实测注释捞出来，
   逐条与本服比对（本轮已证明这类"约定差异"就是突破口）。
2. **驱动任务链**：客户端已在场景内且会发 `15203/12403` ⇒
   用已验证的 **UI dump（带 adb 坐标）+ 长按**去点任务栏/NPC，触发 `12400/12402`；
   或先用管理接口确认本服的任务表（846 条）与链头逻辑正常。
3. **打通战斗**：任务进入 `fight_mon` 后，客户端会发 `20002`；
   本服 `20002/20010/20012/20013/20020/20023/10500` 已实现且有自检覆盖 ⇒ 观察是否自然触发。
4. 留意 `mapResCache_0` 是否影响 NPC/怪的可见性（本项目的历史可用会话是 192）。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/minloop/min_loop_server.py` | ★ `push_10200()` 改为 `code=0`（附完整出处注释） |
| `server/minloop/selftest.py` | ★ 新增 10200 code 断言 ⇒ 自检 **45/45** |
| `logs/minloop/live9_stdout.log` | ★ 改后证据：`scene_table`/`isLoadState_true`/`15203`/`12403` |
| `logs/minloop/live8_stdout.log` | 改前对照（`scene_nil`） |
| `analysis/1.4.9/round67_68_scene_10201_fix.md` | 参考服 `10200→10201→15402` 推送组合的既有记录 |
