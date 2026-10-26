# R228（新目标②）：★★★ **`11221`/`11224`（看他人伙伴+装备）接上 `role_heros`（18 行）—— 第 18、19 条**

> 新目标第 38 批。★★★ **按 R226 的权威清单推进 `112xx` 族，一次补完 2 条。**
> **时间**：次日 13:00 – 15:00。

---

## 一、★ `112xx` 族（11 条）逐条看

```
11204 CS{id} → {id, skill<skill_bid>}                  伙伴技能（需"伙伴↔技能"，R206 已否决）
11212 CS{bid,type} → {code,msg,bid,type}               操作型
11213/11214/11218 → {code,msg,...}                     操作型
★ 11221 CS{srv_id,cache_id} → {cache_id, PARTNER_LIST, EQM_LIST}   ← ★★★
★ 11224 CS{rid,srv_id,id} → {id, PARTNER_LIST, EQM_LIST}           ← ★★★
11222 CS{id} → {code,msg}                              操作型
11237/11239/11241 → 符文/编队                            复杂
```

★★ **⇒ `11221`/`11224` 是"看他人伙伴 + 装备"** ⇒ **与 `11201`/`10947` 同一类** ✓

---

## 二、★★★ 取证（**逐名对应**）

```
partner_list 元素: id:u32, bid:u32, type:u8, color:u8, lifttime:u32, lev:u8, exp:u32, …
role_heros 列:      rid, bid, color, lev, exp, state, chip, got_at   （**18 行**）
   ⇒ ★ 对应: `bid`/`color`/`lev`/`exp` **逐名对应** ✓
   ⇒ ★ `id`/`type`/`lifttime` ⇒ **无源 ⇒ 0**（**`id` 退回用 `bid`**）

eqm_list 元素 ⟷ `equip_items`（**本服 0 行**）⇒ **空表** ✓
```

---

## 三、★ 实现 + 实测

```python
def hero_partner_bytes(cmd, field, rows):   # ★ 按权威 SC 遍历（不可能漏字段）
# 11221: cache_id + partner_list + eqm_list
# 11224: id + partner_list + eqm_list
```

```
DB role_heros: 18 行 ｜ 首个 (bid,color,lev,exp)=(30800,1,1,0)
11221: len=872 消耗=872 err=None ｜ ★ partner_list=18 ｜ 首条 id=30800 bid=30800 color=1  ⇒ PASS
11224: len=872 消耗=872 err=None ｜ ★ partner_list=18 ｜ 首条 id=30800 bid=30800          ⇒ PASS
```

★★ **⇒ 两条各返回 18 个真实伙伴** ✓

---

## 四、★ 一处自纠（**`int + bytes`**）

第一版把 `_pre` 写成 **`int`**（`struct.unpack_from(...)[0]`）⇒
★ **`TypeError: unsupported operand type(s) for +: 'int' and 'bytes'`**
⇒ **服务端连接关闭**（`tcp.log` 报 `--- error: TypeError(...)`）❌
**修**：**`_pre = w_u32(...)`**（**bytes**）✓

> **★ 纪律第 69 条**：**"拼接式编码"的每个片段都必须是 `bytes`** ——
> 本项目的编码函数（`w_u8`/`w_u32`/`w_str`/`*_bytes`）**都返回 `bytes`**
> ⇒ ★★ **若某个片段是 `int`（如直接从 `struct.unpack` 取）⇒ `TypeError`**
> ⇒ **而且这个异常会"关闭连接"**（**客户端表现为"命令没反应"**）。
> ★★★ **判据**：**报 `TypeError: int + bytes` ⇒ 检查"是不是漏了 `w_*` 包装"**。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1445** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★ **权威清单** | **320 → 318 条**（`11221`/`11224` 已移出）✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| ★ **`server/mock_server.py`** | **`hero_partner_bytes`** + `11221`/`11224` 专用实现 |
| `tools/_diag_r228.py` / `_diag_r228b.py` | ★ **`112xx` 族 + 验证** |

---

## 七、目标② 累计成果（新目标 38 批）

| # | 成果 | 数据源 |
|---|---|---|
| R196–R200 | `19600`/`15204`/`16601`/`16602`/`13906` | 各配置 |
| R204/R207–R209 | `10947`/`10526`/`11240`/`13802`/`13807` | `role_attr`/`bag_items` |
| R212–R213 | `10954-10957`/`10601` | `equip_items`/`role_attr` |
| R214/R217–R219 | `11600`/`15700`/`11210`/`18907`/`10202`/`10203` | 各表 |
| R227 | `11010` | `roles` |
| **R228** | **`11221`/`11224`** | **`role_heros`** |

★ **⇒ 19 条实质升级** ✓

---

## 八、下一批（**继续按权威清单推进**）

| 族 | 条数 | 方向 |
|---|---|---|
| ★★ **`187xx`（15）** | 跑玩法 | `config_dragon` |
| ★ **`133xx`（14）/ `135xx`（13）** | 社交/限购 | 看 SC |
| ★ **`112xx`（9，已去 2）** | 符文 | `role_runes`（1 行）|
| ★ **`124xx`（9）/ `132xx`（9）** | 任务/组队 | 看 SC |
