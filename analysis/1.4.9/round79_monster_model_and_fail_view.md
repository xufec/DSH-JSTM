# R79：② 怪模型同主角 / ③ 结束界面与结果不匹配 —— 两处都挖到**真源**

> 用户复测：① `pos位置不能为0` **已不再弹**（R78 生效）；
> ② 敌我模型**还是一样**；③ **结束界面与战斗结果不匹配**。
> 本轮不再猜数值，直接反汇编 `battle_role.luac` / `battle_ctrl.luac`，
> **两处根因都拿到了字节码级证据**，并且 ③ **是我 R78 自己引入的 bug**。
> **时间**：2026-09-29 19:05 – 19:20。

---

## 一、② 怪模型同主角 —— 真源是 **`srv_id` + `rid`**（不是 `ant_id`）

`battle_role.luac` **proto#2**（各 92/113 字符串，含 `animate_res` / `Config.Mon` / `res_id`）

```lua
-- 战斗单位建外观时：
if self.srv_id == 'mon' then                      -- BC 69-73  ★ 先判定"这是怪"
    self.type = 'mon'
    local cfg = Config.Mon[self.rid]              -- BC 74-77  ★★ **用 rid 查 Config.Mon**
    if cfg then
        if cfg.res_id then self.res = cfg.res_id  -- BC 80-84  ★ 模型资源取自这里
        ...
    end
end
...
getSpineTypeByName(self.res) …
```

而 `Battle.__init__` 给怪的是：

```python
self.mon_f = Fighter(fid=2, ..., res_id=mon_res_id or '')      # ← 只给了 res_id
#                                                              #   rid 默认 0、srv_id 默认 ''
```

⇒ **两个条件全不成立**：`srv_id ~= 'mon'` ⇒ 不进怪物分支；`Config.Mon[0]` = nil ⇒ 拿不到 `res_id`
⇒ 客户端回退**角色默认模型**（看起来就是主角本体）。

**⇒ R78 改的 `ant_id`（0→1）方向错了**（`animate_res` 是另一条路）。

### 修复

```python
self.mon_f = Fighter(fid=2, ..., rid=int(mon_bid or 0), srv_id='mon', res_id=mon_res_id or '')
#                     ^^^★ mon_bid 从 make_battle 一路传进来（新增参数）
```

**自查（服务端载荷）**：

```
我方: rid=1001  srv_id='1'    pos=1  res_id=''
敌方: rid=10105 srv_id='mon'  pos=1  res_id='H34800'
→ 客户端取模型路径: srv_id==mon ⇒ Config.Mon[10105].res_id = 'H34800'
```

---

## 二、③ 结束界面与结果不匹配 —— **`SC_20022` 其实是"打开失败界面"**

`battle_ctrl.luac` **proto#31**（`hander_20022`，注册表里 `20022 → hander_20022`）：

```lua
function (self, data)
    Battle:getInstance():openBattleFail(data.icon_list)     -- ★★★ openBattleFail
end
-- 紧随其后 proto#32：battleFailView = BattleFail.New()      -- 失败视图
```

**⇒ `SC_20022` = 「打开战斗失败界面」**，不是中性的"显示战斗结束界面"。

### 这是 R78 我引入的 bug，如实记录

R78 我按 `protocol/fields.json` 里那个泛化的 sc 名「显示战斗结束界面」就**无条件**补发了 `20022`
⇒ **赢了也弹失败界面** ⇒ 正是用户看到的"结束界面与战斗结果不匹配"。

**修**：只在**战败**时发（`Battle.result`：1=胜、2=败）；胜利走 `SC_20020{result=1}` + `SC_20023`。

```python
if int(getattr(bt, 'result', 0)) != 1:
    send(20022, w_u16(0))          # 战败 ⇒ openBattleFail
else:
    log('.. 20022 跳过（胜利不走 openBattleFail，R79）')
```

---

## 三、验证（脚本，含"反向断言"）

`tools/verify_battle_20022.py` 的断言**按 R79 更正**：胜利时**必须不含** `20022`
（含了反而说明"赢了弹失败界面"这个 bug 还在）。

```
命令序列: [20002, 20010, 20012, 20013, ×7, 20020, 20023]
胜负判定：胜利（SC_20020 已发） ⇒ 期望**不含** 20022
实际含 20022: False
=== 结果: PASS ===
```

---

## 四、请你再试一次

> 进乾坤日月谷 → 点「圣灵教精英」：
> ① 不再弹 `pos位置不能为0`（已确认）
> ② **怪的模型应是 `H34800`（圣灵教精英的原版资源），不再是主角模型**
> ③ **打赢后不再弹失败界面**（`20022` 只在真输时发）

若 ② 仍未变，下一步应继续往下读 `battle_role` proto#2 里 `res` 之后的分支
（`getSpineTypeByName` / `add_act_spine` / `sp_resource`），看是否还要求 `specials`/`pet` 等字段。

---

## 五、全量验证 / 环境

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 170 / 默认 64 / 未开放 22）、CS 2463-0、SC 静态 85+1空-0、SC 在线 **86-86**、专用 **63-63**、门禁 E **PASS** |
| 回归 | `verify_battle_20022`（断言已更正）/ `verify_20002_click` / `verify_guaji` / `level_consistency` / `race` / `arena` / `dungeon` / `mission_hook` **全 PASS** |
| 环境 | `stderr` **0 字节**；9000 恰好 1 监听 |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/battle.py` | 怪 fighter 加 `rid=mon_bid` + `srv_id='mon'`；`Battle.__init__` 新增 `mon_bid` 参数 |
| `server/mock_server.py` | `make_battle` 传 `mon_bid`；`SC_20022` 改为**仅战败时发**（更正 R78） |
| `tools/verify_battle_20022.py` | 断言更正为"胜利不含 20022" |
| `analysis/_battle_role.txt` / `analysis/_battle_ctrl.txt` | 反汇编证据（proto#2 / hander_20022） |
| `analysis/1.4.9/round79_monster_model_and_fail_view.md` | 本报告 |

---

## 七、一句话

> **② 的真源不是 `ant_id`，而是 `srv_id=='mon'` + `Config.Mon[rid]`** —— 我们给怪的 `rid=0`、`srv_id=''`，
> 客户端于是回退主角模型。**③ 是 R78 我自己的 bug**：`SC_20022` 的处理器叫 `openBattleFail`，
> 我按泛化的 sc 名无条件补发，结果赢了也弹失败界面。两处都已按字节码证据修掉。
