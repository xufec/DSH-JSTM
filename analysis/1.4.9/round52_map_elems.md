# R52：`SCMapGird_10201.elems` 接线 —— 把 R51 门禁抓出的"该发而未发"补上

> 本轮的**研究对象就是 R51 门禁首次运行抓出的那一条告警**：
> `▲ cmd=10201 field=elems ← 规格要 table，实际发空表`
> **时间**：2026-09-29 10:50 – 11:00。

---

## 一、根因：不是"没有数据"，是"**没接线**"

```python
# 改前（两处调用都漏了第 4 个参数）
def build_10201(roles, npcs=None, mons=None, elems=None):   # ← elems 早就有实现
...
L4886:  build_10201([role], _npcs, _mons)                   # ← 没传 elems
L5838:  build_10201(roles,  _npcs, _mons)                   # ← 没传 elems
```

`build_elems()` 本身**一直是完整可用的**（`id/bid/type/sub_type/name/x/y/res_id` 八个字段齐全），
只是**从来没有人给它喂过数据** ⇒ 场景元素（采集物 / 传送阵 / 机关）**从未下发**。

> ⇒ 这正是 R51 门禁存在的意义：**四道审计都放行**（空表长度合法），
> 但**真机场景里少了东西**。这类缺陷只能靠"看内容有没有发"来发现。

---

## 二、数据源（原版配置，不编造）

| 项 | 值 |
|---|---|
| 提取链 | APK `assets/src/config/config_map.luac` → `Config.Map[scene].elems` |
| 工具 | `tools/extract_config_map.py`（已有，**本轮无需改**） |
| 产物 | `analysis/1.4.9/task/config_map.json`（124 场景） |
| 覆盖 | **19 个场景有元素**，每场景 ≤3 个（最多的是 `10002`/`10200` 各 3 个） |
| 玩家所在 `10001` 史莱克城 | **2 个**（id 10001 @(123,91)、10003 @(10,17)） |
| 原表给到的字段 | **只有 `x` / `y`** |

⇒ 落地时：`bid` 取元素 id（**与 `npcs` 同构** —— 客户端按 bid 去本地配置解析名字/资源），
`type/sub_type/name/res_id` **原表没有出处 ⇒ 留 0/空，不编造**。

---

## 三、实现

```python
def map_cfg():          # 惰性读 analysis/1.4.9/task/config_map.json
def scene_elems(scene_id):
    """SCMapGird_10201.elems —— 场景元素（采集物/传送阵/机关）。"""
    scene = map_cfg().get(str(scene_id)) or {}
    return [{'id': int(eid), 'bid': int(eid), 'type': 0, 'sub_type': 0,
             'name': '', 'x': int(e['x']), 'y': int(e['y']), 'res_id': ''}
            for eid, e in (scene.get('elems') or {}).items()]
```

两处调用都补上，并按 `config.json: send_map_elems`（默认 `true`）开关控制（便于对照实验）。

---

## 四、真机复验

```
改前: << 10201 SCMapGird (server push) roles=1 npcs=25 mons=1        (621 bytes)
改后: << 10201 SCMapGird (server push) roles=1 npcs=25 mons=1 elems=2 (657 bytes)
```

| 检查 | 结果 |
|---|---|
| `elems` 计数 | **2**（= config 里 10001 的元素数）✓ |
| 包体 | 621 → **657 字节**（+36 = 2 × 18，与 `build_elems` 的字段宽度吻合）✓ |
| 客户端 | 6 帧全部完整，正常进主城、**无异常** |
| `server_stderr.log` | **0 字节** |
| 客户端异常日志 | 无 `Traceback` / 无 `!!` |

### ★ 门禁闭环（这才是本轮最重要的验证）

```
把 tools/_emitted_empty_allow.json 里的 "10201:elems" 条目**删掉**后再跑门禁：

  顶层空表告警（未登记理由）: 0        ← 不是被白名单放过，是字段真的不再为空
  顶层空表（已登记理由）: 39           ← 由 40 → 39（少了一条豁免）
  结果: PASS
```

⇒ 完整闭环：**门禁发现 → 修实现 → 告警自然消失 → 豁免条目删除**。
这证明了门禁 E 不是"又一个开关"，而是**能驱动修复的检查**。

---

## 五、全量验证（六道门禁）

| 门禁 | 结果 |
|---|---|
| `lint_dispatch_shadow.py` | 专用 168 / 默认 62 / 未开放 22 ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 / **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 84 命令：83 一致 + 1 空规格 / **0 不一致** |
| `audit_sc_live.py --unsupported` | **84/84 一致** |
| `audit_dedicated.py` | **63/63 符合规格** |
| **`audit_emitted_fields.py`** | **顶层空表告警 0** / 长度不符 0 / 豁免 39 条 / **PASS** |
| 交叉自洽 | `62 + 22 == 84` ✓、`168 == 168` ✓ |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | `map_cfg()` / `scene_elems()`；两处 `build_10201(...)` 补传 `elems`；两条日志加 `elems=` |
| `server/config.json` | `send_map_elems=true` + `_note`（可一键回退做对照） |
| `tools/_fix_r52_cfg.py` | 配置落地脚本（幂等） |
| `tools/_emitted_empty_allow.json` | **删除 `10201:elems` 豁免**（40 → 39 条） |
| `analysis/1.4.9/round52_map_elems.md` | 本报告 |

---

## 七、下一步

| 优先 | 事项 | 起点 |
|---|---|---|
| 1 | **挂机链续做** | `15405→15400→15402` 已通、映射 `mission_bid=10010` 已取得；缺 `15403{mon_bid}`（杀怪上报）与 `15404`（结算推送）、`12402/12403` 轮次提交。客户端 handler 在 `ghost_ctrl.luac`（`handle15402/15403/15404`） |
| 2 | **`19400` 命格背包** | 需先有"玩家拥有命格"的来源；空背包时全 0 已是真话 ⇒ 单独做价值有限 |
| 3 | **元素细节** | 19 个有元素的场景里，`type/sub_type/res_id` 仍无配置出处；若将来从 `config_map` 的其它段或资源表取证到，可补 —— **现在不猜** |
| 4 | **推荐战力** | **外部依赖**：`Config.RoleAttr` 无战斗属性，原版曲线不在 APK 里 |
