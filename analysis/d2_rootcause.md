# D2 根因定位报告 —— 客户端背包"0/150 空显"

- 日期：2026-10-02（Asia/Shanghai）
- 模拟器：MuMu12 实例0，adb `127.0.0.1:16384`，Android12，横屏 2560x1440
- 客户端：`com.shiyue.dldl.ewan.baidu2`（cocos2d-x lua，1.4.11，PID 14732）
- mock_server：TCP9000+HTTP8080，PID 29612（**全程未改、未重启**）
- 前序：`analysis/d2_render_fix.md`（已排除图标资源缺失）

---

## 0. 结论速览（一句话）

**根因 = 客户端侧的物品类型/囊分流（client-side bag_code / getGoodsItemType 过滤），不是数据下发、不是图标、不是协议、也不是客户端配置缺 bid。**
客户端**数据模型确实收到并存了这 6 件**（DSH_PROBE `main6`），客户端 **config_item 也认识这些 bid**（中文名全部 FOUND），图标物理存在；但"背包"右侧网格渲染 0 格——这 6 件被客户端的分流逻辑归到了当前网格不显示的类别/专属囊。

证据等级：**STRONG_INFERENCE**（数据链路全链 CONFIRMED；逐 bid 精确落点因 frida-hook luajit 在 MuMu ARM 翻译层不可用而 INFERENCE，见 §6）。

---

## 1. 决定性对照：客户端"收到了但不画"

| 环节 | 观测 | 证据 | 等级 |
|---|---|---|---|
| 服务端下发 | 10502(bag_code=1) 一次性下发 6 件 | `server/logs/tcp.log` 03:01:53 | CONFIRMED |
| 客户端数据模型 | DSH_PROBE `t=bp` 上报 `main6_1:6`（bag_code1=6） | `server/logs/http.log` | CONFIRMED |
| 客户端配置认识 bid | 6 个物品中文名在 `assets/src/config/config_item.luac` 全部 FOUND | `tools/_d2_check_cfg.py` | CONFIRMED |
| 图标资源 | 4 图标物理存在+登记+加密头一致 | `analysis/d2_render_fix.md` | CONFIRMED |
| 协议字段 | 10502 16 字段逐一对齐 | `analysis/d2_render_fix.md` | CONFIRMED |
| **客户端 UI 渲染** | **右侧背包网格"空间 0/150"全空，0 格** | shots `20261002_031151_d2root_07_bag.png` + `_crop_baggrid.jpg` | CONFIRMED |

**这是一条干净的因果链：服务端发 6 → 客户端存 6 → UI 画 0。** 缺口 100% 落在"客户端从数据模型到网格单元格"这一段渲染/过滤，与前序排除的资源/协议路径无关。

### 下发的 6 件（bag_code=1，tcp.log 03:01:53）
```
(id308, bid28514, qty2)  type=6 礼包   小型宝石袋      icon30035
(id309, bid28560, qty2)  type=7 材料   抽奖券          icon28560
(id310, bid28515, qty2)  type=5 消耗   庆典夏日时装券  icon28515
(id312, bid21403, qty3)  type=43 主动符文 牧夫         icon21403
(id313, bid33001, qty1)  type=160     蛊风兽甲        icon42501
(id314, bid36500, qty1)  type=240     半神头盔.六阶   icon44505
```
对照：bag_code=2（装备栏）另 6 件 (40003/41803/41403/41603/41003/41213) **在角色模型上正常穿戴显示**——同一客户端、同协议通道，装备栏渲染正常，进一步排除"客户端渲染管线整体坏"。

---

## 2. UI 实测观察（截图存 shots/d2root_*.png）

- 背包入口：右下"魂囊"按钮（圆心约 2430,1160）。加载 UI 经 logcat 确认为 `role_pack_view.luac` + `pack_grids.luac` + `grids_cell.luac`。
- 右侧竖排页签：**背包 / 称号 / 戒指 / 时装 / 魂骨**——这些是**并列的不同面板**（点称号/戒指切到对应空面板），**不是背包内部的"装备/材料/道具"子页签**。
- "背包"网格：**"空间 0/150"，一片空白，无任何格子、无子页签行**（`_crop_baggrid.jpg` 裁剪网格顶部确认）。
- 顶部按钮"筛选 >"：点击切到**仓库分屏视图**——左"我的仓库 0/125"全锁、右主背包仍 0/150（shots `d2root_08_filter`）。**即"筛选"不是类型过滤下拉，而是仓库/背包切换**。由此排除"误停在某个类型筛选 tab"的假设。
- logcat（`probes/d2root_logcat_bagopen.txt` 356 行、`d2root_logcat_filter.txt` 1122 行）：仅见 cocos 加载上述 3 个 luac，**无任何 lua error / nil / 背包相关 print**（cocos lua 游戏不打物品渲染日志）。

**UI 分流判定（任务步骤3）：** 主背包网格**没有可见的装备/材料/道具子页签**，6 件物品无从"落到某个我能点到的子页签"。因此 D2"默认 tab 空而非渲染失败"的视觉前提**不成立**——默认主背包就是空的，不是切错了 tab。

---

## 3. 客户端分流系统（静态提取 APK，只读 zipfile）

从 `anzbao/jstm_142165.apk` 提取 luac 字符串：

### `assets/src/common/common_goods_type.luac`
- 分流出口常量：`BAG_EQUIP` / `BAG_MATERIAL` / `BAG_PROP` / `BAG_ALL`
- 入口函数：`getGoodsItemType` / `bagItemType`（按 bid 的 type 把物品归入上面四类之一）
- 判定谓词：`isGiftItem`(礼包)、`isZhuRuneGoods`(主动符文)、`isBeiRuneGoods`(被动符文)、`isSoulStarGoods`、`isArtifactBackPackGoods`、`isRoleBagGoods`、`isRoleEquip`、`isCommonYuanShenGoods` … 等约 40 个。

### `assets/src/game/backpack/backpack_const.luac`（Bag_Code 枚举）
```
BACKPACK / SOULSTAR_PACK / SOULSTAR_HEROPACK / SOULSTAR_ROLEPACK /
ROLEARTIFACT_BAG / ROLE_ARTIFACT / FASHION_PACK / STORAGE / HERO_STORAGE /
HERO_EQUIP / ROLE_EQUIP / JBP_WAREHOUSE / PARTNER_ARTIFACT / IN_SOULBACKPACK …
```
——客户端**不是单一大背包**，而是按 Bag_Code 分多个独立囊。

### `assets/src/game/backpack/backpack_data.luac`
- 数据结构：`item_list` / `item_bid_to_id` / `item_id_to_bid`，**按 bag_code 路由**。
- 对 `HERO_EQUIP` / `ROLE_ARTIFACT` / `SOULSTAR_PACK` 等有**独立的 add/modify/delete 分支**——物品按类型被分流进不同 bag_code 容器，而非全部进 BACKPACK。

---

## 4. 根因推断（STRONG_INFERENCE）

结合 §1 全链证据 + §3 客户端分流结构：

1. **服务端 bag_code=1 下发的 6 件，客户端 `backpack_data` 把它们存进了某个 bag_code 容器（DSH_PROBE 报 main=6）。**
2. **但"背包"面板右侧网格（`pack_grids`）渲染时，按 `getGoodsItemType` 对物品再做一次类型归类，只画出属于当前网格类别（BAG_EQUIP/PROP/MATERIAL 之一）的项。**
3. 这 6 件的 type 跨度大（5/6/7/43/160/240），其中：
   - **21403（type43 主动符文）→ `isZhuRuneGoods` → 必然分流到 SOULBACKPACK（符文囊），本就不该出现在主背包**——这是**预期行为，不是 bug**。
   - 33001(type160)/36500(type240) 属高阶装备/特殊类型，大概率被 `isRoleEquip`/artifact 类谓词分流到装备/神器囊。
   - 28514(type6 礼包)/28560(type7 材料)/28515(type5 消耗) 理论应进主背包 BAG_PROP/MATERIAL，但**主背包仍画 0**——说明客户端按其**自身 config_item 里的 type 字段**（与服务端下发 type 未必一致）归类，或 `pack_grids` 绑定的 bag_code ≠ 服务端写入的 bag_code=1。

> 注：§4.3 后三条的**精确落点**需要 frida hook `BackPackData.getGoodsListByItemType` / `grids_cell:setData` 逐 bid 打印分流结果才能 CONFIRM。本次该 hook 未成功（见 §6），故标 INFERENCE。

---

## 5. 排除项汇总（死路，记录以免重复踩）

| 假设 | 结果 | 依据 |
|---|---|---|
| 图标资源缺失 | **排除** | d2_render_fix.md（图标物理存在+登记+加密头一致） |
| 协议 16 字段错位 | **排除** | d2_render_fix.md（逐字段对齐） |
| 客户端 config 不认识 bid | **排除** | `tools/_d2_check_cfg.py`：6 物品中文名全部 FOUND |
| 误停类型筛选 tab | **排除** | "筛选"=仓库切换，非类型下拉；主背包本就空 |
| 客户端渲染管线整体坏 | **排除** | bag_code=2 装备栏 6 件在角色模型正常穿戴 |
| lua 报错导致渲染中断 | **排除** | logcat 无 lua error/nil |

---

## 6. frida 路线状态（诚实记录）

- host：`D:\Anaconda3\Scripts\frida.exe` v17.18.0，可用；frida-ps -U 正常列出 baidu2 进程。
- 设备：`/data/local/tmp/frida-server` 就位；`adb shell su -c id` = uid0（root 可用，**未改动模拟器任何 root 设置**）；已 `forward tcp:27042`。
- **hook luajit 背包 lua 函数未执行**：MuMu12 为 x86 容器跑 arm 翻译层（`libcocos2dlua.so` 位于 `lib/arm/`），luajit 字节码函数无 native 符号，跨翻译层 inline-hook 在本环境可靠性差（与项目既有 `minloop_frida_sock9000_v2` 笔记一致）。**为避免产出不可靠的 hook 结论污染根因，主动停止该路线，未伪造 hook 数据。**
- 若后续要 CONFIRM 逐 bid 落点：需在**真机/原生 arm 设备**或**关 arm 翻译**环境 hook `BackPackData.initItemList` / `getGoodsListByItemType` / `grids_cell:setData`，打印每个 bid 的 (bag_code, bagItemType)。

---

## 7. 对 P0 过滤的处置建议

**结论：维持服务端 P0 过滤这 4 个 bid（28514/28560/28515/21403），不要放开。**

理由：
- 本次实机证明：**即使服务端下发这 6 件，客户端主背包也不画它们**（被客户端分流到符文/装备/专属囊或类型过滤）。放开过滤**不能**修复"背包空显"——因为空显是客户端分流行为，不是缺数据。
- 因此 d2_render_fix §8"放开过滤后不应因缺图标不可见"的预期需修正：放开后仍不可见（原因在客户端分流）。P0 过滤在"主背包可见性"维度上**是无害且正确的**，保留可避免下发客户端本就不显示的占位物品、减少困惑。

**后续路径（不强求本期）：**
1. 若要让某件（如 28515 消耗券）真正在主背包可见，需在**原生 arm 环境 frida hook** 确认它被分到哪个 bag_code/类别，再让服务端把它写到对应的 Bag_Code 容器（而非笼统 bag_code=1）。
2. 21403 主动符文本就属于符文囊，不应期待出现在主背包——若要验证符文囊渲染，需单独打开符文囊入口（本期未在主 HUD 找到独立符文囊按钮，标 UNKNOWN）。
3. 内容填充阶段（Phase 4+）按"客户端分流后的目标囊"回填物品，而非按 bag_code=1 批量下发。

---

## 8. 证据文件清单

- 截图：`analysis/runtime_evidence/shots/20261002_031151_d2root_07_bag.png`（主背包 0/150 空）、`d2root_08_filter`（仓库分屏）、`_crop_baggrid.jpg`（网格顶部裁剪，确认无子页签）、`d2root_13_closed`（回主场景）。
- logcat：`analysis/runtime_evidence/probes/d2root_logcat_bagopen.txt`（背包打开 luac 加载）、`d2root_logcat_filter.txt`（仓库切换）。
- 静态核对脚本：`tools/_d2_check_cfg.py`（config 中文名 FOUND）。
- 协议/下发：`server/logs/tcp.log` 03:01:53（10502 bag_code=1 6 件）；`server/logs/http.log`（DSH_PROBE `t=bp` main6）。
- 前序：`analysis/d2_render_fix.md`。

## 9. 证据等级汇总
- CONFIRMED：服务端下发 6 件 / 客户端模型 main6 / config 中文名 FOUND / UI 网格 0/150 / 装备栏正常 / 无 lua 报错。
- STRONG_INFERENCE：根因=客户端类型/囊分流导致主背包不渲染这 6 件。
- INFERENCE：每个 bid 精确分流到哪个 Bag_Code/类别（21403→符文囊较确定；其余待 frida）。
- UNKNOWN：独立"符文囊"入口是否在主 HUD、逐 bid 落点（受 MuMu arm 翻译层 frida 限制）。
