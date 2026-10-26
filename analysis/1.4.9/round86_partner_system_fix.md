# R86：修复伙伴系统 —— 「神将兑换有动画、但伙伴没进背包 / 无法上场」

> 用户报障：**神将兑换可以实现、有获得动画，但没有到伙伴背包，也无法上场伙伴。**
> 三个根因全部定位并修复，**验收脚本 PASS（且幂等）**。
> **时间**：2026-09-29 21:05 – 21:30。

---

## 一、真源：客户端的 `GodRedeemCtrl`（`game/godredeem/godredeem_ctrl.luac`）

| proto | 内容 |
|---|---|
| #2 | `registerProtocals`：**`11216 → handle_11216`** |
| #3 | `send_11216(partner_bid, state)` → `CS_11216{partner_bid:u32, state:u8}` |
| **#4** | **`handle_11216(data)`**（决定"获得动画"从哪来） |

```lua
function GodRedeemCtrl:handle_11216(data)
    if not data then return end
    if data.code ~= 0 then                                    -- ★ code 非 0 = 成功
        self:closeView()
        HeroEquipCtrl:getInstance():openGainPanelByBid(data.partner_bid)  -- ★ 获得面板
    end
    message(data.msg)                                         -- ★ 无条件 ⇒ 成功时 msg 必须为空
end
```

⇒ **你看到的"获得动画"是客户端本地在 `code ~= 0` 时播的**，
**跟服务端有没有真的把伙伴入库无关** —— 这正是"有动画但背包里没有"的机制。

协议：`CS_11216{partner_bid:u32, state:u8}` → `SC_11216{code:u8, msg:string, partner_bid:u32}`。

---

## 二、三个根因

### 根因 ①：`11216` 被**前置的同类分支遮蔽**（第 9 次"分发顺序遮蔽"）

| 位置 | 代码 | 后果 |
|---|---|---|
| **L5717（前）** | `if cmd in (11206, 11216):` —— 只回 `code=1`，**不写入任何数据** | ★ **命中** |
| L6678（后） | `if cmd == 11216:` —— 校验 → 写伙伴背包 → 回 `code=1` | ❌ **死代码** |

**真机日志的实锤**：`<< 11216 SC_11216 partner_bid=31300` —— 打的是**旧分支**的日志文案，
我新分支那句 `兑换伙伴 … code=1` 从未出现。

⇒ **修**：把 `11216` 从 L5717 的元组里移出（保留 `11206`）。

### 根因 ②：`10401`（伙伴背包）读的是**静态配置**

```python
heros = self.cfg.get('heros') or []      # config.json 里写死的 17 个
```

⇒ 兑换来的伙伴**无处落脚** ⇒ 背包永远 17 个。

⇒ **修**：新增 `role_heros` 表 + `db_hero_init/list/add`；
`heros` 改为 `db_hero_list(rid, cfg)`（**首次用 config 播种一次**，之后一切以 DB 为准）。
这一处改动同时覆盖 `10401/10402/10403/10404`。

### 根因 ③：`SC_10402` / `SC_10404` **多发了字段**（"无法上场"的直接原因）

| 命令 | 权威 spec | 我们原先发出 | 差异 |
|---|---|---|---|
| `SC_10402` | `bid:uint16, lev:uint8`（**3 字节**） | `u16 + u8 + u8(color) + u32(exp)`（8 字节） | **多 5 字节** |
| `SC_10404` | `bid:uint16, lev:uint8` | 同上（8 字节） | **多 5 字节** |

客户端按 spec 解析 ⇒ 越界/拿不到干净数据。而这两条正是**查看/上场伙伴**要用的接口。

⇒ **修**：两条都按 spec 只发 `bid:u16 + lev:u8`。

---

## 三、验收（`tools/verify_partner_redeem.py`，**幂等**）

```
前置清理: /DSH_ADMIN/hero?bid=31300&off=1 ⇒ 仍在背包=False
== 兑换前 SC_10401 ==   hero_bag=17  消耗=259/259  PASS=True
== CS_11216{partner_bid=31300} ==
   SC_11216 code=1 msg='' partner_bid=31300  (7 bytes)      ← ★ 成功且 msg 为空
== 兑换后 SC_10401 ==   hero_bag=17 → 18  消耗=274/274
   bid 31300 是否进入伙伴背包: **是**                        ← ★ 真进背包了
== CS_10402{bid=31300} ==  SC_10402 bid=31300 (3 bytes)  PASS=True   ← ★ 符合 spec
=== 结果: PASS ===
```

★ **连跑两次都 PASS**（脚本先用 `/DSH_ADMIN/hero?bid=N&off=1` 清理前置）——
一个只能通过一次的测试不算回归，这条已按纪律补上。

---

## 四、★ 门禁再补一个盲区（第 2 次，这次是**跨形式**遮蔽）

`11216` 的遮蔽形态是 **`if cmd in (…)` 遮蔽 `if cmd == …`** ——
而 R83 我给门禁加的 `duplicate_dedicated()` **只查 `==` 形式**（当时为了躲开"嵌套子条件"的误报）。

**新判据：按 `(缩进层级, 命令号)` 计数** ——
- **同层**出现两次 ⇒ 真遮蔽；
- **不同层** ⇒ 嵌套子条件（合法控制流，排除）。

验证：

| 输入 | 结果 |
|---|---|
| 真实文件 | **无（干净）** ✓ |
| 把 `11216` 放回前置 `in (…)`（还原修复前形态） | **测出 `{11216: 2}`** ✓ |
| 人为加一层更深的嵌套 `if cmd in (11701,11702)` | **正确排除** ✓ |

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| `lint_dispatch_shadow` | **✓ 无分发遮蔽**（专用 175 / 默认 59 / 未开放 22；含新的跨形式检查） |
| `audit_specs_vs_fields` | 空消息 616 一致 |
| `audit_sc_conformance --generic --unsupported` | 一致 81 / 0 |
| `audit_sc_live --unsupported` | **81 命令：一致 81 / 不一致 0** |
| `audit_dedicated` | 66 条：符合 66 / 不符 0 / 无应答 0 |
| `audit_emitted_fields` | 长度不符 0 / 顶层空表告警 0 / **PASS**；`--selftest` **PASS** |
| 回归（**10 项**） | **`verify_partner_redeem`（新）** / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `11216` 移出前置 `in (…)`（解遮蔽）；新增 `role_heros` + `db_hero_init/list/add` + `partner_def`；`10401/10402/10403/10404` 改读 DB；`SC_10402/10404` 按 spec 收敛；新增 `16605` 处理器；`/DSH_ADMIN/hero` 路由；`16605` 移出通用集合 |
| `tools/_fix_r86_partner.py` | 上述修改脚本（幂等可重跑） |
| `tools/verify_partner_redeem.py` | **新增**：神将兑换 → 进背包 → 可取到（幂等） |
| `tools/lint_dispatch_shadow.py` | `duplicate_dedicated()` 升级为**跨形式 + 缩进分层**判据 |
| `analysis/_hero_ctrl.txt` / `_godredeem_ctrl.txt` | 反汇编证据 |
| `analysis/1.4.9/round86_partner_system_fix.md` | 本报告 |

---

## 七、请你试

> ① 打开神将兑换，兑换一个**你背包里还没有的**伙伴 → 获得动画照旧，
> 但这次**伙伴背包里应该有它**、并且**可以上场**了；
> ② 若某个伙伴仍不能上场，请把屏幕上的提示原话发我 ——
> 上场链路（`11206` 容量 / 具体上场命令）我还没逐条取证，
> 下一步会按 `form/`（上阵界面）的字节码继续往下查。

⚠ **数据说明**：验收脚本会给 `rid=1001` 加一个伙伴 **31300 龙傲天**（现在背包 18 个）。
要撤掉就 `GET /DSH_ADMIN/hero?bid=31300&off=1`。

---

## 八、一句话

> **动画是客户端自己播的**（`SC_11216.code ~= 0` 就播），所以"有动画"从来不等于"入库了"。
> 三个真因：**`11216` 被前置的 `in (…)` 分支遮蔽**（服务端压根没执行写入）、
> **`10401` 读静态配置**（写到哪都看不见）、
> **`SC_10402/10404` 多发 5 字节**（上场要用的接口，客户端解析越界）。
> 三条都已修，验收脚本 PASS 且可重复跑；门禁也补上了"跨形式遮蔽"的检查。
