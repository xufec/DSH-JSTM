# R141：★★ **纠正 R140b 的归因** —— 不是"会话缓存"，是"**键名别名**"

> 新目标第 18 批。**本批没有加新功能**，做的是：**系统性复查 R140 发现的那个 bug**，
> 结果**推翻了我自己上一轮的归因**，并确认**没有其他同类问题**。
> **时间**：2026-09-30 13:20 – 13:55。

---

## 一、R140b 当时说错了什么

R140b 我写的是：

> "根因是 `role_state(self.cfg).get('vip_level')` 读的是**会话开始时装载的配置**，
> **不随 DB 变化**" ⇒ 并据此断言"**玩家状态类的数值必须每次从 DB 读**"。

**这个归因是错的。** `role_state(cfg)` 的源码里明确写着：

```python
def role_state(cfg):
    """把 默认值 + 配置 + 数据库 合并成一份完整角色状态
    优先级：ROLE_DEFAULTS < config.json.role < **数据库里的角色行**
    """
    st = dict(ROLE_DEFAULTS)
    st.update(cfg.get('role', {}) or {})
    rid = st.get('rid', 1001)
    row = db_get_role(rid)          # ★ 每次都查 DB
    ...
    for col, sc in _DB_TO_SC.items():
        v = row.get(col)
        if v is not None:
            st[sc] = v              # ★ 用**映射后的键名** `sc` 写入
```

⇒ **它每次都 `db_get_role(rid)`，根本没有会话缓存。**

## 二、真根因：`_DB_TO_SC` 把 3 个列名**映射成了别的键名**

```python
_DB_TO_SC = {'level': 'lev', 'vip_level': 'vip_lev', 'x': 'x', 'y': 'y',
             'dir': 'dir', 'scene_id': 'scene_id', 'name': 'name',
             'career': 'career', 'sex': 'sex', 'exp': 'exp', 'gold': 'gold',
             'gold_acc': 'gold_acc', 'title': 'cur_title', 'status': 'status',
             'uid': 'uid', 'diamond': 'diamond', 'coin': 'coin', 'hp': 'hp',
             'max_hp': 'max_hp', 'mp': 'mp', 'max_mp': 'max_mp'}
```

**只有 3 个列名与键名不同**：

| DB 列 | 状态里的键 |
|---|---|
| `level` | **`lev`** |
| `vip_level` | **`vip_lev`** |
| `title` | **`cur_title`** |

而 `16704` 读的是 **`role_state(...).get('vip_level')`** ⇒ 那个键**不存在** ⇒ `.get` 返回 `None` ⇒ `0`。

### 实测证实

```
role_state 返回的键里:
   vip_level  = （不存在）   ← ★ 代码读的就是这个
   vip_lev    = 3            ← ★ 真正的键名
   lev        = 70           ← 正确
   level      = （不存在）
```

---

## 三、★ 系统性排查：**没有其他同类问题**

新增 `tools/scan_key_alias.py`（**从源码解析 `_DB_TO_SC`**，不硬编码）：

```
`_DB_TO_SC` 里"列名与键名不同"的 3 个：level→lev、vip_level→vip_lev、title→cur_title

★ 用**映射前的列名**去 role_state(...).get(...) 的位置（都读不到）：
    ★ vip_level（应为 vip_lev）：1 处
        L7794  ← 就是 R140b 修的那一处

★ 正确用法（用映射后的键名）：
    lev          11 处 ✓
    vip_lev       1 处 ✓
    cur_title     0 处 ✓

★ 结论：role_state 每次都查 DB（无缓存）；问题只是键名别名。
```

⇒ **R140b 的那处修复是对的**（改 DB 直读拿到 3），**但归因写错了**；
⇒ **其他 12 处（`lev`/`scene_id`）都是正确用法，无需改**。

---

## 四、★ 顺便作废一个工具

R140 之后我写了 `tools/scan_session_cache.py` —— 它按"键名在 `roles` 列里"来判定风险，
⇒ 把 **`lev`（11 处）**和 **`scene_id`（1 处）**都标成了风险，**那是误报**
（它们正是**映射后的正确键名**）。

⇒ 正确工具是 **`tools/scan_key_alias.py`**（按 `_DB_TO_SC` 的**别名**判定）。
`scan_session_cache.py` 保留但**标注为已废弃**。

> ★ **纪律（修正版，替代 R140b 的第 8 条）**：
> **读角色状态时，要用 `_DB_TO_SC` 映射后的键名**（`lev` / `vip_lev` / `cur_title`），
> 不是 DB 列名（`level` / `vip_level` / `title`）。
> `role_state` 本身**每次都查 DB**，不存在缓存问题。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **255** / 默认 32 / **未开放 6**）/ 静态 PASS / conformance PASS / **SC 在线 38-38** / **专用 92-92** / 门禁 E **PASS** |
| 回归（**28 项**） | **失败数 0** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| **`tools/scan_key_alias.py`** | ★ **正确版**排查：从 `_DB_TO_SC` 解析别名，找读错键名的位置 |
| `tools/scan_session_cache.py` | R140 的**误报**工具（保留并标注已废弃）|
| `analysis/1.4.9/round141_correction_key_alias.md` | 本报告 |

---

## 七、本会话的"自我纠正"累计

| 轮次 | 我原本的判断 | 纠正后的真相 |
|---|---|---|
| **R128** | 门禁 `parse_full` 有偏移 bug（R115b/R127c）| **是我把 `attr_list` 的"12 个属性"当成了"12 行"** |
| **R141** | `vip_level` 读的是"会话缓存"（R140b）| **是键名别名**（`vip_level` → `vip_lev`）|

★ 两次都是**"怀疑外部/机制，而真因在自己的用法"**。
⇒ **纪律**：遇到"读不到/算不对"，**先核对"我用的名字/单位/形状与规范是否一致"**，
再怀疑工具或机制。

---

## 八、新目标进度

| 指标 | 目标起点 | 现在 | 变化 |
|---|---|---|---|
| **未开放命令** | 19 | **6** | **−13** |
| **真机发过的未实现** | 67 | **41** | **−26** |
| **专用分支** | 208 | **255** | **+47** |
| **B 类（有依据地不做）** | 57 | **26** | **−31** |
| **回归项** | 17 | **28**（失败 0）| **+11** |
| 六道门禁 | — | **全 PASS** | — |

### 下一批

1. `13569`（祈福，无配置源 ⇒ 空表 + 登记）
2. `scan_growth_cmds.py` 剩余成长动作（座椅 `20803`–`20809`、翅膀 `11602`–`11607`）
3. 真机剩余可做项（按 `gap_worklist`）
