# 50 轮目标 · Round 25（goal round 43）—— 找到 `10922` 的**真实活动数据**，但**按纪律不填**（`status` 语义 UNKNOWN）

> 时间：2026-10-01 ｜ 本轮目标：给高频命令补真值（从 `analysis/` 找来源）

---

## 〇、一句话结论

> 本轮把 `10922`（活动列表）挖到了底：
> - ★ **真实数据是有的**：`server/_richang.json['tasks']` = **43 条**活动（`id/name/max_num/desc_cond/desc_time/…`），
>   且 `SC_10922.act_list` 的 item 形状是 `{id:uint16, status:uint8, int_args:table}` ⇒ **`id` 完全能对上**；
> - ⚠️ **但 `status` 的语义 UNKNOWN**（0 是"未开放"还是"进行中"？无据）；
> - ✅ **两侧证据都表明"空表是可接受的"**：
>   `analysis/1.4.9/protocol_flow.md:108`（参考服对活动等子系统回"**空但合法**"）、
>   `analysis/1.4.9/blank_dialog.md:227`（参考服 `10922` **只回 0 条**，客户端显示"该功能暂未开放"）。
>
> ⇒ **按纪律不填真实活动**：填错 `status` 会把客户端推进**未验证状态**（例如显示可点但本服没实现的活动）。
> 本轮把这条**"故意为空"的决定连同理由写进断言**，自检 **115 → 118/118 PASS**。

---

## 一、本轮调查结果

| 项 | 内容 |
|---|---|
| 命令语义 | `10921/10922/10924` = 活动/日常子系统列表（`login_flow.md:14`、`protocol_flow.md:108`） |
| SC 形状 | `SC_10922.act_list` = table\[`{id:uint16, status:uint8, int_args:table[val:uint32]}`\]（CS 无字段） |
| 真实数据 | `server/_richang.json`：`tasks` **43 条**（如 `id=103 世界BOSS`，含 `max_num/ord/desc_cond/desc_time/cli_assets`）、`kezhi` 若干 |
| 可映射字段 | `id` ✅ 直接对应；`name/desc_*` **不在 SC 里**（是客户端本地配置） |
| 不可映射字段 | **`status`（语义 UNKNOWN）**、`int_args`（参数含义未确证） |
| 参考服行为 | 回 **0 条**；客户端接受并显示"该功能暂未开放" |

---

## 二、本轮改动（`selftest.py`，服务端未改）

新增一条**"纪律性断言"**，把"为什么这里故意不填"固化下来：

```python
# 10922 保持"空但合法"：status 语义 UNKNOWN ⇒ 不填真实活动（宁缺勿造）
c.send(10922, {}, raw=b'')
f22 = c.recv_all(0.4)
e22 = next((x for x in f22 if x[0] == 10922), None)
check(e22 is not None, '10922 有应答')
check((e22[1].get('act_list') or []) == [], '★ 10922 保持"空但合法"…')
strict_ok(f22, '10922(空但合法)')
```

**实测**：`检查项 118，通过 118，失败 0`（此前 115）。

> 设计取舍说明：断言"**必须是空表**"看起来像在锁死一个"功能缺失"，
> 但它锁的其实是**已验证的客户端可接受行为**；等 `status` 语义确证后再改断言并填真值。

---

## 三、完成 / 未完成（本轮）

### 3.1 完成
1. ★ **把 `10922` 挖到底**：真实数据（43 条）、SC 形状、可映射/不可映射字段、参考服行为，全部列明。
2. ★ **做出并记录了"不填"的纪律性决定**（`status` UNKNOWN + 空表已验证可接受），并写成**可回归断言**。
3. ★ 明确**升级路径**：需要 `status` 语义（客户端 `game/daily/daily_ctrl.luac` 或界面读数）。
4. 自检基线 115 → **118**。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `status` / `int_args` 的语义 | **UNKNOWN**（决定能否填真值） |
| 2 | 其余高频命令（`11200/11215` 伙伴、`16500`、`17200`）的真值 | 未做（伙伴有 `_partner_base.json`/`partner_config.json` 可挖） |
| 3 | `12404~12450` 差异对照 | 未做 |
| 4 | 客户端 `10102/10103` 不上线（唯一硬卡点） | 仍 blocked（需外部原生观测手段） |

---

## 四、下一轮建议

1. ★ **确证 `10922.status` 语义**：反汇编 `game/daily/daily_ctrl.luac` 看它如何用 `status`
   （`tools/ml_dump_proto.py` 可用）；确证后即可把 43 条真实活动按语义填进去（并改断言）。
2. 或**换一条更容易闭环的命令补真值**：`11200/11215`（伙伴）有 `_partner_base.json`(31KB)/`partner_config.json`，
   且其 SC 字段可能更直接。
3. 继续 `12404~12450` 差异对照。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| `server/minloop/selftest.py` | ★ +3 条断言（`10922` 保持"空但合法"的纪律性断言），自检 **118/118** |
| `server/_richang.json` | 本轮发现的真实活动数据（43 条 `tasks`） |
| `analysis/1.4.9/protocol_flow.md:108`、`blank_dialog.md:227` | 本轮依据（"空但合法" + 客户端接受空表） |
