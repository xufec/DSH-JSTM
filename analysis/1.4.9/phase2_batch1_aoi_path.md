# 第二阶段实施报告（第 1 批）：AOI + 寻路

> 用户 2026-09-18 **批准进入实施**：「第二阶段：NPC 对话 + 移动 + AOI + 寻路」。
> 本批完成 **AOI** 与 **寻路**（含 JSTM 特有的安全校验）。

---

## 一、★ 实施前的两处**重要更正**（先取证再动手）

### 更正 A：**移动（10204）其实已经实现了** —— 我 R2 报告漏了整个 10200 段

**真机日志实测：**
```
[19:39:50] >> cmd=10204 ? body(8)=00 28 00 25 13 8f 00 00
[19:39:50] << 10204 SCMove_10204 rid=1001 -> (40,37) [saved] (17 bytes)
[19:46:21] >> cmd=10204 ? body(8)=00 27 00 25 ...
[19:46:21] << 10204 SCMove_10204 rid=1001 -> (39,37) [saved]
```
**服务端 `行3547 if cmd in (10204, 10205):`** —— `CS_10204{x:u16,y:u16} → SC_10204{rid,srv_id,x,y}`

**⇒ 位置同步（`10204`）**是通的**（发过 ✅ 回过 ✅）。**
**⇒ 但我的 `movement_protocol.md` **只列了 10900+ 段，漏掉了整个 10200 段** —— 已追加更正记录。**
**⇒ 「移动不通」这个旧结论应精确为：不通的是**点击自动寻路**，不是位置同步。**

### 更正 B：**服务端一处注释过时** —— 战斗不是 `11000/11200`，而是 `20000` 系列

服务端 `10204` 的注释写「真正的击杀发生在战斗实例（11000 / 11200 系列）」，
**但实测**：
```
服务端实现: 行4200 if cmd == 20002（发起）｜ 行5045 if cmd == 20014（ACK 推进）
真机日志  : [18:53:19] >> cmd=20002
```
**⇒ 战斗链是 `20000` 系列（与 R2/R3/R4 一致）；那段注释是**过时的**。**
（`11200` 实际是**伙伴背包**，`11300` 是**竞技场** —— 与战斗无关。）

**⇒ 结论：R2/R3/R4 的战斗段**不需要改**；只是服务端注释要更新（**本轮未改**，留待清理）。**

---

## 二、交付物

### 2.1 `server/aoi.py`（自研，约 290 行）

**设计思想来源（★ 只有思想，无代码）**：
- Survive `common/aoi.c` —— **⚠ 该文件头内嵌 GPLv3 ⇒ 一行代码都不可复制**
- kongkongxiyou `aoi.md` —— watcher/object 双注册 + 4 事件 + 双向差集

**JSTM 化改造**：
| 项 | 参考项目 | **JSTM** |
|---|---|---|
| 语言/形态 | C 模块 / Pomelo 插件 | **纯 Python 单进程** |
| 坐标 | 世界像素（硬编码塔格 300） | **瓦片坐标，`tower_size` 可配（默认 8）** |
| 网络耦合 | 有 | **绝不碰 socket** —— 只产出 `[(uid, event)]`，由调用方推 |
| MOB 移除 | **remove 分支被注释掉** | ✅ **正常派发 leave** |
| 埋点 | 零埋点 | ✅ 提供 `stats()` |

**API**：
```python
aoi = AOI(tower_size=8)
aoi.add_watcher(uid, x, y, range)      # 有视野者
aoi.add_object(uid, x, y, types)       # 被看见者
aoi.update_watcher(uid, x, y)          # 我移动 → 服务"我的视野"
aoi.update_object(uid, x, y)           # 对象移动 → 服务"别人的视野"
aoi.watchers_of(px, py, r, types)      # 按坐标取 watcher（对应 getWatcherUids）
aoi.remove(uid)                        # 注销（正常派发 leave）
```

**★ 核心是双向差集**（开销正比于**视野变化量**，而非视野内实体数）：
```
new - old → 'enter' ；old - new → 'leave'
```
**★ 且必须两个都调**（`update_watcher` + `update_object`）—— 漏一个就会出现"别人看不到我移动"。

**单元测试：**
```
1001 初次视野: [(2001,'enter'), (2002,'enter')]                 ← 远处 2003 正确排除
1001 移到(85,37): [(2001,'leave'), (2002,'leave'), (2003,'enter')]  ← ★ 双向差集正确
2001 移动: [(1001,'enter',2001)]                                 ← ★ 反向事件正确
stats: {add:4, update:3, enter:4, leave:2, entities:4, towers:3}
```

### 2.2 `server/pathfind.py`（自研，约 250 行，**含安全校验**）

**设计思想来源（★ 只有思想，无代码）**：
- Survive `common/astar.h` —— **⚠ 同样内嵌 GPLv3 ⇒ 不可复制**
- kongkongxiyou `pathfinding.md` —— 列压缩碰撞、**直线快路径优先**、两级压缩

**内容**：
| 组件 | 说明 |
|---|---|
| `MapGrid` | 通行数据；**缺碰撞图层时 `allow_all=True`**（先跑通链路），有数据直接 `set_blocked` |
| `find_path` | **A\*（8 邻域 + octile 启发）**；**先试 Bresenham 直线快路径**（多数同屏移动零次 A*）；**禁贴角穿缝** |
| `line_of_sight` | Bresenham 直线可达（对应 Survive `lineto`） |
| `verify_path` | **★ L1 路径校验** |
| `MoveRateLimiter` | **★ L2 限流（令牌桶）** |

### ★★ 为什么把 L1/L2 内建（R1 审计的**安全红线**）

**kongkongxiyou 的 `handler.move` **直接信任客户端上传的整条路径**，
`Map.verifyPath` 已定义但**全项目 0 处调用** ⇒ 可**穿墙/瞬移/加速/拉怪**；
Survive 战斗层也**零距离/角度/目标数校验**。**

**⇒ 本模块的核心原则：客户端**永远不能提供路径**，只能提供**目标点**。**

**单元测试：**
```
① 直线快路径: [(10,10),(20,10)]              ← 两点，零次 A* ✓
② 绕行竖墙:   长度 6，避开 (15,10) ✓
③ 完全封闭:   [] ✓
④ ★ L1 校验:  合法 ✓ ／ 跳格 ✗ ／ 穿墙 ✗ ／ 起点不符 ✗   ← 四类作弊全部拦住
⑤ ★ L2 限流:  连续超速被拦 ／ 等 1 秒后恢复 ✓
```

### 2.3 服务端最小接入（**不动既有 handler**）

```python
try: import aoi as aoi_mod           # 与既有 battle_mod 同风格（失败降级不崩）
except Exception: aoi_mod = None
try: import pathfind as pathfind_mod
except Exception: pathfind_mod = None

def get_aoi() / get_mapgrid() / get_ratelimit()   # 惰性单例
```
**新增只读管理接口 `/DSH_ADMIN/aoi`。**

**实测：**
```
/aoi -> {"ok":true,
         "aoi":{"add":0,"remove":0,"update":0,"enter":0,"leave":0,"entities":0,"towers":0},
         "mapgrid":{"w":256,"h":256,"blocked":0,"allow_all":true},
         "modules":{"aoi":true,"pathfind":true}}
日志: AOI ready (tower_size=8) ｜ MapGrid ready
服务端 8080/9000 正常 ｜ stderr 0 字节
```

---

## 三、一处**自造 bug 及修复**（如实记录）

**我把 `import aoi` 插到了 `try: import battle as battle_mod` 与其 `except` **之间**，
破坏了原有的 try/except 结构 ⇒ `SyntaxError: invalid syntax (line 37)`。**

**⇒ 修：把 `except Exception: battle_mod = None` 移回 `import battle` 之后，再把新 import 接在后面。**
**⇒ 教训：插入代码前必须先看**完整语句块**，不能只看锚点那一行。**

---

## 四、第二阶段剩余三项（未做）

| # | 项 | 状态 | 说明 |
|---|---|---|---|
| **1** | **AOI** | ✅ **本批完成** | 已接入 |
| **2** | **寻路** | ✅ **本批完成** | 含 L1/L2 安全校验 |
| **3** | **移动（点击寻路）** | ⏳ | ✅ 位置同步（`10204`）**已通**；缺的是"点击目标点 → 服务端算路径 → 下发"这条链。**现在 `pathfind.find_path` 已就绪，可直接接** |
| **4** | **NPC 对话** | ⏳ | 卡在客户端 `getScene()==nil`（`no_scene_view_instance`）。★ R1 审计给了新思路（Survive D4：「断线三态 + **重连重建视野**」）——**"进场景后重建客户端可见状态"与 NPC 对话可能是同源问题** |

---

## 五、审计来源可追溯（任务书【第十四节】要求）

| 借鉴项 | 来源项目 | 文件 | LICENSE | 是否可复用 | 说明 |
|---|---|---|---|---|---|
| AOI 双向差集 | Survive | `common/aoi.c` | **GPLv3（内嵌）** | ❌ **不可复制** | **只读设计，JSTM 完全自研** |
| AOI 双注册 + 4 事件 | kongkongxiyou | `ai/area/aoi`（插件未打包） | 无 LICENSE | ❌ | **只读设计** |
| A\* + 直线裁剪 | Survive | `common/astar.c` | **GPLv3（内嵌）** | ❌ | **只读设计** |
| 直线快路径 / 两级压缩 | kongkongxiyou | `pathfinding.md` | 无 LICENSE | ❌ | **只读设计** |
| **L1/L2 安全校验** | — | — | — | — | **★ JSTM 原创**（参考项目均缺失） |

---

## 六、自查

```
mock_server.py 语法 OK ｜ aoi.py / pathfind.py 单元测试通过 ｜ stderr 0 字节
服务端 8080/9000 正常（PID 32872）｜ 既有 handler **未改动**
已备份：server/mock_server.py.bak_before_aoi
```
