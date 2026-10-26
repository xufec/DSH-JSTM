# R153：候选池第二批 5 条 + ★ `15200`/`19500` 的判定**升级为有据**

> 新目标第 2 批。**专用分支 306 → 311**。
> **时间**：2026-09-30 20:20 – 21:00。

---

## 一、★ `15200` / `19500` 的"深挖"结论（目标②）

实测两者的规格：

```
15200  cs []          sc [code:u8, msg:string]
19500  cs []          sc [code:u8, msg:string]
```

⇒ **都是 `CS[] → {code,msg}`** ⇒ 是**回执型**消息
⇒ R151 的全局兜底回 **`code=1`（"已收到"）** 就是**正确行为**。

**★ 所以"语义未取证"的结论要改写为**：
> **它们没有可做的内容** —— 不是因为"查不到语义"，
> 而是因为**它们的 SC 里根本没有承载信息的字段**（只有回执）。

★ 之前把它们归为"语义未取证"是**不够准确**的；现在有了**规格级的证据**。

---

## 二、本批实现 5 条

| cmd | CS | SC | 数据源 | 实测 |
|---|---|---|---|---|
| **`10529`** | `{code_bag, **eqm_item_id:u32**, state}` | `{code,msg,code_bag,eqm_item_id,**score,power,refine,attr**}` | ★ `equip_items` + `role_power` | `code=1 eqm_item_id=90001 power=133960` ✓ |
| **`10541`** | `{bag_code, **eqm_item_id:u32**, state}` | `{code,msg,bag_code,eqm_item_id,**grade,power**}` | ★ 同上 | `item_id=90001` ✓ |
| **`10954`** | `{rid, srv_id}` | `{rid,srv_id,**name**,stage,**power**,…,4 张子表}` | ★ **看他人** ⇒ 本服只有自己 | `name='DSH'`（= DB）✓ |
| **`10955`** / **`10957`** | `{rid, srv_id}` | `{stage,**power**,…,4 张子表}` | ★ 同上 | 结构精确 ✓ |

★ **真实**的有：`eqm_item_id`（回显真装备）、`name`、`power`（133960）。
★ **无源 ⇒ 0**（真话）：`score`/`refine`/`grade`/`stage`/`luck`/`grow`/进阶子表。

---

## 三、★ 本批两次自纠

| # | 现象 | 真因 | 修 |
|---|---|---|---|
| ① | `10954` 报 `err=surface_star: table 计数越界` | **我只发了 3 张子表，实际要 4 张**（`skill_list`/`items`/`looks`/`surface_star`）—— **R143b 的教训又犯一次** | 补第 4 张 |
| ② | `verify_equip_family` 报 `unpack_from` 越界（79 > 60） | 我在该验收里**写死"每件 66 字节"**；实际是 **39**（`4+4+4+1+1+2+2+4+4+2+1+2+2+2+2+2`）⇒ 一旦真有几件装备就偏移越界 | 改成 39 并写明算式 |

★ ①再次印证纪律第 10 条：**批量处理前看全 SC 的完整字段与类型**（我用的是**截断过**的字段列表）。
★ ②是"手写偏移"的老毛病 ⇒ **更好的做法是让验收也走门禁的权威解析器**（本轮先修正常量）。

---

## 四、★ 顺带修掉第 5 次"验收不幂等"

`equip_items` 表被 `verify_equip_family` 的 `DELETE` 前置**清空** ⇒ `verify_gap_batch2` 的
"有装备"分支测不到（`item_id=0`）。
**修**：验收开头**自己插入一件真实装备**（`item_id=90001`）⇒ 连跑两次都 PASS ✓

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **311** / 默认 21 / 未开放 6）/ 静态 PASS / conformance PASS / **SC 在线 27-27** / **专用 100-100** / 门禁 E **PASS** |
| 回归（**37 项**） | **新增 `verify_gap_batch2.py`**；修 `verify_equip_family.py` ⇒ **失败数 0** |
| 幂等 | `verify_gap_batch2` **连跑两次 PASS** |
| 判定表 | **B 15 / C 0 / A 311** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `equip_one`/`role_power_of` + `10529`/`10541`/`10954`/`10955`/`10957` |
| `tools/verify_gap_batch2.py` | **新增回归第 37 项**（含幂等前置）|
| `tools/verify_equip_family.py` | 修偏移常量（66 → **39**）|
| `tools/_fix_r153_gap_batch2.py` | 插入脚本 |
| `tools/_emitted_empty_allow.json` | 新增 13 条理由 |
| `server/mock_server.py.bak_r153` | 改前备份 |

---

## 七、新目标进度

| 指标 | R152 | 现在 | 变化 |
|---|---|---|---|
| **专用分支** | 306 | **311** | **+5** |
| **回归项** | 36 | **37**（失败 0）| **+1** |
| 六道门禁 | 全 PASS | **全 PASS** | — |
| **真候选池** | 22 条（已做 4）| **22 条（已做 9）** | **+5** |
| `15200`/`19500` | 判定"语义未取证" | ★ **判定升级为"回执型，无内容可做"**（有规格证据）| — |

### 下一批（候选池还剩 13 条）

| 目标 | 依据 |
|---|---|
| `11201`（`id/bid/type/color/…/score/stage/power/aptitude/…`）| ★ **伙伴详情**（20 字段！有 `aptitude`/`innate_skill`）|
| `16610`/`16634`/`16636`（活动/礼包）| `config_global_wish_data` / `config_lucky_box_data` |
| `11412`（`realm, skill_list`）| `config_role_career` |
| `12602`（`star_lev, nature, power`）| `config_demon` |
| ★ 把"字段独特性"筛法**推广到 `10xxx`/`13xxx` 大族** | `classify_gap.py` |
