# R199（新目标②）：★★★ **`16601`/`16602`（活动列表）—— 91 个真实活动**

> 新目标第 9 批。★★ **`action` 从"缺 `bid` 源"变成"91 个真实活动（`bid=121 魂装特惠`）"。**
> **时间**：次日 12:00 – 13:30。

---

## 一、★★★ 配置源取证（**推翻 R198 的假设后找对了**）

R198 **否决**了 `config_act`（它是"战斗演出"）；
本批**遍历十余个候选**，找到 **`config_function`（26323 B）**：

```
config_function 的 93 个 TableConst，每个是一条"功能/活动":
  {description: "魂装特惠", module_flag: "flyUp_gift", open_lev, location, show_tips,
   fight_sort_id, open_tips, sort_id, lev_tips, show_lev, is_group, id, is_open}
字符串常量: ["Function", "Config"]      ← ★ 顶层键 = `Config.Function`
```

★ **⇒ 与 `SC_16601{holiday_list:table<bid, title, title2, ico, type_ico, top_banner, rule_str…>}` 对照**：

| SC 字段 | ← 配置字段 |
|---|---|
| `bid` | `id` |
| `title` | `description`（"魂装特惠"）|
| `ico` | `module_flag`（"flyUp_gift"）|
| `rule_str` | `open_tips` / `show_tips` |

---

## 二、★★★ 一处关键自纠：**"配置的两种行形态"**

### 现象

第一版 `16601` 的 `title` 是**字面量 `"description"`**（`0b 64 65 73 63 72 69 70 74 69 6f 6e`）⇒ **键名被当成了值** ❌

### 根因

`kconst_rows` 第一版只做"**一个 dict 装 N 行**"（如 `config_npc` 的 `{31216.0: 30001}`）
⇒ 而 **`config_function` 是"**N 个 dict 各装一行**"**（93 个 `TableConst`）⇒ 
   ★ 我的函数**把"一个字段表"当成了 13 行** ⇒ `title` 变成了字段名 `"description"` ❌

### 修

**`kconst_rows` 同时支持两种形态**：
```python
if len(dicts) >= 3:            # ★ 形态②：多个 dict ⇒ 每个 dict 一行
    for i, d in enumerate(dicts):
        h = d['hash']
        if has_id or len(h) <= 24:   # 这个 dict 装"一行"
            out.append((h.get('id', i+1), h))
        else:
            out.extend(list(h.items()))    # 装"多行" ⇒ 拆开
else:                          # 形态①：一个 dict 装 N 行
    …取 hash 最大的那个…
```

### 修后实测

```
  16601: len=5687 消耗=5687 ｜ ★ 条目=**91**
  16602: len=458 消耗=458 ｜ ★ 条目=91
  16601 第 1 条: bid=121 title='魂装特惠'      ← ★★ 真实标题！
```

> **★ 纪律第 40 条**：**"配置/表"的行形态有两种** ——
> ① **一个 dict 装 N 行**（`{id: row}`）；② ★ **N 个 dict 各装一行**（每行一个 `TableConst`）。
> ★★ **判据**：**"含字段名的 dict 有多个" ⇒ 走形态 ②**。
> ★★★ **症状**：**"字段值变成了字段名本身"** ⇒ 一定是把"一张字段表"当成了"一行数据"。

---

## 三、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1438** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS**（含 R199）|
| 回归（**66 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 四、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | ★ **`kconst_rows`（支持两种行形态）/ `kconst_str` / `kconst_int`** + `16601`/`16602` |
| `tools/_diag_r199.py` | ★ **十余个候选配置的排查**（"含标题/图标字段"判据）|
| `tools/_fix_r199_16601.py` | 插入脚本 |

---

## 五、目标② 进度（**B 类 15 条**）

| B 类 | 状态 |
|---|---|
| **`dailysign`（`19600`）** | ★★ **已升级**（95 真实签到档位）|
| **`npc`（`15204`）** | ★★ **已升级**（`num=17` + 真实 `gold`）|
| **`action`（`16601`/`16602`）** | ★★ **已升级**（**91 个真实活动，`bid=121 魂装特惠`**）|
| **`npc`（`15200`）/ `mission`（`19500`）** | ★ 取证完成，**语义仍未证明** ⇒ 维持 `code=0` |
| **`qifu`** | ★ 配置源已找到（`config_global_wish_data` 35 条）⇒ 下一批 |
| **`chongzhi`** | ★ 配置源已找到（`config_charge*`）⇒ 下一批 |
| 其余 8 条（社交域）| ★ **维持"空即真话"** |

---

## 六、下一批

| 目标 | 依据 |
|---|---|
| ★ **`qifu` 用 `config_global_wish_data`（35 条）** | `GlobalWishStatic` 的字段 |
| ★ **`chongzhi` 用 `config_charge*`** | — |
| ★ **批量把"能从 `cfg_kconst` 取真值"的命令升级** | `kconst_rows` 已是通用工具 |
