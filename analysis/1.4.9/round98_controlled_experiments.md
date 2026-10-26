# R98：**对照实验开关** —— 用"服务端改一个值 + 你看一眼屏幕"定性伙伴/阵型 UI

> R93–R97 证明了客户端 ctrl **被闭包隔离**（`_G` 只有协议表、`package.loaded` 只有 boolean），
> 所以"**数据没到客户端**"与"**UI 过滤掉了**"这两种可能**无法从客户端侧区分**。
> 本轮把它们变成**三个可秒级切换的服务端开关**，由**看得见屏幕的人**一句话判定。
> **时间**：2026-09-29 23:00 – 23:20。

---

## 一、三个开关（读**全局 `CFG`** ⇒ 改完**下一次请求即生效、不必重登**）

| 开关 | 作用 | 对应实验 |
|---|---|---|
| **`hero_bag_limit`** | `SC_10401.hero_bag` 只回前 N 个（0=不限） | **C（最有判别力）** |
| `hero_state_override` | 覆盖 `SC_10401.hero_bag[].state`（-1=不覆盖） | A |
| `form_pos_limit` | `SC_14000.hero_pos_info` 只回前 N 个（0=不限） | D |

**为什么读全局 `CFG` 而不是 `self.cfg`**：`self.cfg` 是**连接时**建立的实例副本
（`TcpHandler.cfg = _c2`），改它不影响**已连上**的客户端；全局 `CFG` 是**每次请求现读**的,
所以**改完下一次请求就生效** —— 实验才能"秒级切换"。

**接口**：

```bash
GET /DSH_ADMIN/exp?name=hero_bag_limit&val=1        # 开
GET /DSH_ADMIN/exp?name=hero_bag_limit&val=0        # 关
GET /DSH_ADMIN/exp?name=hero_state_override&val=-1  # 复位
GET /DSH_ADMIN/exp                                 # 打印当前值
```

---

## 二、实测（三个开关都验证通过）

```
基线      : 10401 hero_bag=18 state=1 ｜ 14000 上阵位=5
实验C(1个): 10401 hero_bag=1  state=1 ｜ 14000 上阵位=5   ← ★ 只回 1 个
实验D(2位): 14000 上阵位=2                                ← ★ 上阵位变 2
实验A(st=3): state=3                                      ← ★ 覆盖生效
复位后    : 10401 hero_bag=18 state=1 ｜ 14000 上阵位=5   ← ★ 全部干净复位
```

---

## 三、★ 怎么用（一次实验就能定性）

**实验 C（最关键）**：
1. 你在游戏里**打开伙伴界面**（不用重启客户端）；
2. 我把 `hero_bag_limit` 设为 `1`（服务端立刻只回 1 个伙伴）；
3. 你在界面上**右键/返回再进**刷新一次列表，看：
   - **列表变成 1 个** ⇒ **界面确实读 `10401`** ⇒ 问题在**UI 的过滤条件**（该去查 `form_data.luac` 的 `is_show`/`career`/`sequence` 过滤）
   - **仍然是空 / 完全没变** ⇒ **界面不读 `10401`** ⇒ 问题在**另一条数据源**（该去查 `11215`、或 `HeroData` 的填充路径）

**实验 D**：设 `form_pos_limit=2`，看阵型页的上阵位是否从 5 个变 2 个 ⇒ 判定阵型读不读 `14000`。
**实验 A**：设 `hero_state_override=3`，看列表有无变化 ⇒ 判定 `state` 是不是过滤键。

> 三个实验**互相独立、均可秒级复位**，且**全在服务端** —— 不需要再重打包。

---

## 四、★ 又踩了同一个坑（记录下来）

写这个开关时，脚本 ② 的守卫查的是 `'hero_bag_limit' not in src`，
而 ① 的路由**先**插入了这个字符串 ⇒ **② 被静默跳过**（脚本报告"已接"，实际只改了路由）。
**实测第一轮 `hero_bag=18` 没变，才暴露出来。**

> **同一个守卫陷阱在 R92（`_attr_data` 那次）已经犯过一次。**
> **纪律**：多步脚本里，后一步的守卫必须查**代码特征**（如"那段带注释的代码块是否存在"），
> **不能查"这个变量名是否出现过"** —— 因为前一步往往刚引入这个名字。

---

## 五、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 184 / 默认 58 / 未开放 22）/ CS 2463-0 / SC 静态 80+1空-0 / SC 在线 **80-80** / 专用 **67-67** / 门禁 E **PASS** |
| 回归（12 项） | `verify_formation` / `verify_partner_list` / `verify_partner_redeem` / `verify_guaji` / `verify_battle_20022` / `verify_20002_click` / `verify_level_consistency` / `verify_race` / `verify_arena` / `verify_dungeon` / `verify_mission_hook` / `test_11215_10800` **全 PASS** |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 六、产出物

| 文件 | 说明 |
|---|---|
| `server/mock_server.py` | 新增 `/DSH_ADMIN/exp` 路由；`10401` 接 `hero_bag_limit`；`14000` 接 `form_pos_limit`；`_hero_state` 接 `hero_state_override` |
| `tools/_fix_r98_exp_switch.py` | 插入脚本（含"守卫必须查代码特征"的注释） |
| `server/mock_server.py.bak_r98` | 改前备份 |
| `analysis/1.4.9/round98_controlled_experiments.md` | 本报告 |

---

## 七、一句话

> R93–R97 把客户端侧探针**证否**了，本轮换成**服务端对照实验**：
> 三个开关（`hero_bag_limit` / `hero_state_override` / `form_pos_limit`）都**秒级生效、不用重登**，
> 实测 `10401 hero_bag: 18 → 1 → 18`、`14000 上阵位: 5 → 2 → 5`、`state: 1 → 3 → 1`。
> **把 `hero_bag_limit` 设成 1、你打开伙伴界面看一眼**，就能一句话定性：
> **列表变 1 个 = UI 过滤问题；没变 = 界面不读 `10401`。**
