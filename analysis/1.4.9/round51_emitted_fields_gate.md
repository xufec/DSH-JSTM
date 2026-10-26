# R51：门禁 E 落地 —— 「该发而未发」检查（补四道审计的共同盲区）

> 承接 `docs/PLAN_下一阶段实施方案与校验设计.md` §5.4（原排期 R54，提前做，因为它是 R49/R49b 两条
> 过时结论**能在四道审计全绿时漏掉**的直接原因）。
> **时间**：2026-09-29 10:30 – 10:45。

---

## 一、为什么必须补这一道

四道审计回答的都是同一个问题：**"发出去的字节合不合规格"**。
没有任何一道回答：**"规格要求的内容，到底发了没有"**。

| 案例 | 四道审计为何放行 | 真机后果 |
|---|---|---|
| `SC_20100.promote` 恒发**空表**（改前 `mock_server.py:6648`） | 空表是"合法"的应答，长度也对 | 变强面板**右侧空白** + 「70级推荐战力：0」 |
| `SC_10922.act_list` 恒发**空表** | 同上 | 全服活动状态根本没下发 |

⇒ 两次都是**审计全绿**、**真机可见**的缺陷。这就是盲区。

---

## 二、判据与实现

```
对每条我们能应答的命令（CS 为空且有 SC 规格，共 82 条）：
  发空 CS → 收 SC → 按规格走查
  记录：① 长度消耗是否 == 实际长度（与 audit_dedicated 同口径，重复保险）
        ② **table 字段的实际计数是否为 0**（= 该发而未发）
        ③ 数值字段是否为 0（信息项，不作失败 —— 0 常常就是真话）
凡 ② 命中且**未在白名单登记理由**者 ⇒ FAIL
```

工具：`tools/audit_emitted_fields.py`；白名单：`tools/_emitted_empty_allow.json`。

### 关键设计：**只把顶层空表当告警**

第一版把**所有层级的空表**都报，结果一次冒出 **476 条** —— 绝大多数是实体/容器内的子表
（`10201.npcs[].member`、`roles[].buff_bids`…）重复出现。
这正是本项目 METHODOLOGY §6 记的老问题：**噪音审计等于没有审计**。

改成**只报顶层空表**后：**40 条**，全部可逐条判定。深层空表降级为"信息项"，按模式聚合
（436 处 / 19 种模式），需要时用 `--deep` 看。

> 经验值：真实案例（`20100.promote` / `10922.act_list` / `17309.rank_list` / `13321.request_list`）
> **全部在顶层**。深层噪音可以放心降级。

---

## 三、灵敏度自检（证明它真能抓到 R49b 那种错）

```
python tools/audit_emitted_fields.py --selftest
```

用 `SC_20100` 造两版应答：

| 构造 | 结果 |
|---|---|
| `promote` 空表（= R49b 修好之前服务端真正的样子） | `empties=['promote']` ⇒ **检出 ✓** |
| `promote` 有 2 条 | `promote` **不再被报** ⇒ **修好后自动消失 ✓** |

```
检出 ✓ ／ 修好后不再报 ✓
自检: PASS
```

---

## 四、★ 首次运行**抓出一个真实的未实现项**

```
▲ cmd=10201  field=elems  ← 规格要 table，实际发空表
```

追查：`build_10201(roles, npcs=None, mons=None, elems=None)` 的**两处调用
（`mock_server.py` L4886 / L5838）都没有传 `elems`**。

```
SCMapGird_10201{roles:table, npcs:table, mons:table, elems:table}
   roles  → 有（roles=1）
   npcs   → 有（npcs=25）
   mons   → 有（mons=1）
   elems  → ★ 恒空（场景元素：采集物/传送阵/机关）
```

⇒ 这是**"该发而未发"的真实案例**，而且是本轮**首次发现**。
按红线不编造 ⇒ 先登记理由 + 列为待办（`config_map` 若含元素段，用 `extract_config_map.py` 接入即可填）。

---

## 五、白名单（40 条，每条都写了理由）

`tools/_emitted_empty_allow.json`。理由分三类，**都不是"以后再说"式的搪塞**：

| 类别 | 条数 | 例子 |
|---|---|---|
| **本服无该玩法/无记录 ⇒ 空是真话** | 24 | `11300:pk_record`（arena_record 表建了但无写入流程）、`13369:black_list`、`10650:talent_list` |
| **实体附件表天然为空** | 14 | `10301:buffs`、`10514:bag_to_eqm`、`14101:assets`（**查询**不带资产；领取时才带） |
| **有意为之 / 结构未取证** | 3 | `10924:act_list`（R49 弹窗修复）、`13042:ceng_list`（塔配置字段顺序未取证，不猜）、`13786:status_list`（语义未取证） |

> ⚠ 规则：**理由写不清 = 该字段没做对**。以后新增实现只要发了空表，都要在这里登记。

---

## 六、全量验证（本轮收尾）

```
python tools/audit_emitted_fields.py            → PASS（顶层空表告警 0，长度不符 0）
python tools/audit_emitted_fields.py --selftest → PASS
python tools/lint_dispatch_shadow.py            → 专用 168 / 默认 62 / 未开放 22 ⇒ 0 遮蔽
python tools/audit_specs_vs_fields.py           → 2463 / 0 不一致
python tools/audit_sc_conformance.py --generic --unsupported → 84 命令：83 一致 + 1 空规格 / 0 不一致
python tools/audit_sc_live.py --unsupported     → 84/84 一致
python tools/audit_dedicated.py                 → 63/63 符合规格
tools/verify_race.py                            → PASS
```

**本轮未改任何服务端行为**（只新增审计工具 + 白名单），因此不涉及真机回归风险。

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `tools/audit_emitted_fields.py` | 新增：门禁 E（含 `--selftest` 灵敏度自检、`--deep` 深层明细） |
| `tools/_emitted_empty_allow.json` | 新增：40 条空表理由白名单（**可审计的契约**） |
| `analysis/1.4.9/round51_emitted_fields_gate.md` | 本报告 |
| `docs/PLAN_下一阶段实施方案与校验设计.md` | §5.4 由"建议"改为"已落地"，并写进每轮收尾清单 |

---

## 八、每轮收尾清单（更新后，六道）

```powershell
python tools\lint_dispatch_shadow.py                                # 0 遮蔽
python tools\audit_specs_vs_fields.py                               # CS 规格 0 不一致
python tools\audit_sc_conformance.py --generic --unsupported        # SC 静态 0 不一致
python tools\audit_sc_live.py --unsupported                         # SC 在线 全一致
python tools\audit_dedicated.py                                     # 专用查询 全符合
python tools\audit_emitted_fields.py                                # ★ 新增：无未登记空表
```

**交叉自洽断言**（防"审计表示过时"）：
```
lint.默认集合 + lint.未开放集合 == audit_sc_live.命令数        （本次 62 + 22 == 84 ✓）
lint.专用分支数 == audit_dedicated.专用分发数                  （本次 168 == 168 ✓）
```

---

## 九、下一步

| 优先 | 事项 | 起点 |
|---|---|---|
| 1 | **`10201.elems`**（本门禁首次抓出） | `config_map` 里找元素段 → `extract_config_map.py` → 两处 `build_10201(...)` 补传 |
| 2 | **`19400` 命格背包** | 配置 `config_mingge`（77KB，在 `_tmp_cfg`）在手；空背包时全 0 已是真话 ⇒ 需先有"玩家拥有命格"的来源 |
| 3 | **挂机链续做** | `15405→15400→15402` 已通，映射 `mission_bid=10010` 已取得；缺 `15403{mon_bid}`/`15404` 结算与 `12402/12403` 轮次提交 |
| 4 | **推荐战力** | **外部依赖**：`Config.RoleAttr` 无战斗属性 ⇒ 原版曲线不在 APK 里 |
