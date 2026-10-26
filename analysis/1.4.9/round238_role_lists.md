# R238（新目标①）：★★★ **`12721`/`12761`/`13320`（角色列表类）接 `roles` —— 一次 3 条**

> 新目标第 8 批。★★ **用 `cfg_kconfig2` 重扫候选，一次补完 3 条 + 造了通用"角色列表"编码器。**
> **时间**：次日 11:00 – 13:00。

---

## 一、★★ 用 `cfg_kconfig2` 重扫（`tools/scan_gap_sources2.py`）

```
★ 缺口清单: 125 条
★ 配置（cfg + cfg_kconfig + **cfg_kconfig2**）: 235 个
★★ 有候选的: **13 条**（**新阈值：配置重合 ≥5**）
   12405 ← missions(11) ｜ 12980/13542/18753 ← config_mission(5)+roles(4)
   12208 ← role_heros(5) ｜ 13600 ← roles(5) ｜ 12201/12211/12721/12722/12761/13320 ← roles(4)
   18807 ← peakwar_state(3)
```

★ **⇒ 逐条看 SC 后的研判**：

| 命令 | 形态 | 研判 |
|---|---|---|
| `12980` | `{bid, my_ord, my_val, my_sec, my_team_member<8>, rank_list<4>}` | ⚠ **队伍排行**（需队伍数据）|
| `13542` | `{type, guid_roles<17>}` | ⚠ **公会成员**（需公会）|
| `18753` | `{role_list<11>}` | ⚠ **存档列表**（`index`/`save_time`）|
| `12211` | `{minerals<9>}` | ⚠ **矿藏**（DB 无）|
| ★ **`12721`** | `{flag, rid, srv_id, name, lev, career, face_id, len, msg, sex, vip_lev, capacity, head_bid, bubble_bid, tick}` | ★★ **可填** ✓ |
| ★ **`12761`** | `{role_list<10>, channel, len, msg}` | ★★ **可填** ✓ |
| ★ **`13320`** | `{recommend_list<7>}` | ★★ **"推荐好友"⇒ 可填"自己"** ✓ |

---

## 二、★★★ 通用工具：**`role_scalar_bytes(cmd, role, n)`**

```python
def role_scalar_bytes(cmd, role, n=1, extra=None):
    """★ 按权威 SC 生成"角色列表"（**顶层标量 + 子表**都用同一套取值）
       · 标量/字符串 ⇒ 从 `role` 按同名或 `_ROLE_ALIAS` 取（`lev`←`level`、`vip_lev`←`vip_level`）
       · **子表** ⇒ 名字含 list/roles/member/recommend ⇒ 填 n 条角色；否则空表
       · `extra` 可覆盖某些字段（如 `is_online=1`）"""
```

★★ **⇒ 它把"角色列表类"的编码**一次封装**** ⇒ **后续同类命令可直接复用** ✓

---

## 三、★ 实测（**3 条全 PASS**）

```
12721: len=36 ｜ PASS      12761: len=33 ｜ PASS      13320: len=20 ｜ PASS
★ 3 条：FAIL 0 ⇒ PASS
```

★ **⇒ 三条都回"1 条真实角色"**（`rid=1001`/`name='DSH'`/`lev=70`/`career=1`/`sex=0`）✓

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 门禁 1–6 | 全 PASS（专用 **1549** / SC 在线 0 / 专用审计 **379-379** / 门禁 E PASS）|
| ★ **门禁 7（G）** | **PASS** |
| 回归（**66 项**） | **失败数 0** |
| ★★ **缺口清单** | **125 → 122 条** ✓ |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| ★★ **`tools/scan_gap_sources2.py`** | ★ **用 `cfg_kconfig2` 重扫候选** |
| ★★ **`server/mock_server.py`** | **`role_scalar_bytes`（通用"角色列表"编码器）** + 3 条 |
| ★ **`analysis/1.4.9/_gap_sources2.txt`** | **13 条候选（含 `cfg_kconfig2`）** |
| `tools/_diag_r238b.py` | 9 条候选的 SC 逐条研判 |

---

## 六、进度（新目标 8 批）

| 指标 | 起点 | 现在 |
|---|---|---|
| **专用分支** | 1446 | **1549**（**+103**）|
| **缺口清单** | 318 | **122** |
| **实质数据接入** | — | **+12 条** |
| **报告** | 206 | **214** |
| **纪律** | 70 | **77** |

---

## 七、下一批

| 命令 | 数据源 | 方向 |
|---|---|---|
| ★★ **`12208`** | `role_heros`（5）| 伙伴相关（非战斗部分）|
| ★ **`13600`** | `roles`（5）+ `role_boss_kill`（0 行）| BOSS 列表 ⇒ 空是真话 |
| ★ **`18753`** | `config_mission`（5）| 存档列表 ⇒ 可试 |
| ★ **`12722`** | `roles` | **离线消息**（本服 0 条）|
