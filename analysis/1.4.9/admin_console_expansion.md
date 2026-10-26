# `dsh_admin.bat` 功能扩充 —— 按"游戏资源目录"做热修改

> 用户要求：**丰富功能多样性；先读取游戏中的各种资源目录，然后增加到 bat 文件中，实现热修改。**

---

## 一、先取证：游戏里有哪些**可热改的资源**

### 1.1 服务端已有的数据源（`server/`）

| 文件 | 大小 | 用途 |
|---|---|---|
| `item_config.json` | 2.19 MB | **3535 件物品**（含 `name`/`type`，`type` 即装备部位） |
| `mission_config.json` | 719 KB | **846 条任务** |
| `item_gift.json` | 60 KB | **496 个礼包 → 5353 条内容映射** |
| `mall_config.json` | 26 KB | **134 件商城商品** |
| `config.json` | 9.7 KB | 主配置（角色/伙伴/聚宝盆奖池/商城/地图 NPC…） |
| `_npcs_10001.json` / `_mapnpc_10001.json` | 2 KB | 场景 NPC |

### 1.2 运行时数据库（SQLite `server/state/roles.db`）

```
roles / role_attr / role_assets     角色与资产
bag_items                           背包
equip_items                         装备（按 slot）
store_items                         仓库
missions                            任务
levgift_got                         等级礼包领取记录
bag_volume                          各囊容量
mall_bought                         商城购买计数
```

**⇒ 结论：可热改的目标 = 上述 JSON 配置 + SQLite 各表。** 每项都**已有明确数据源**（不猜）。

---

## 二、服务端：`/DSH_ADMIN/*` 从 **3 个动作**扩充到 **13 个**

### 2.1 新增动作

| 动作 | 作用 | 关键点 |
|---|---|---|
| **`/status`** | 一次拉全状态（角色/资产/背包/装备/仓库/礼包） | 管理台的**状态总览**靠它 |
| **`/listitems?kw=&limit=`** | **按名字检索物品 → 拿到 bid** | 解决"不知道 bid"的问题 |
| **`/giveitem?bid=&num=`** | 发物品 | **`is_valid_item` 校验**（只发物品表内真实存在的）+ **立即推送** |
| **`/givegift?bid=&num=`** | 发礼包并**直接打开** | 走 `gift_contents` 表；无内容则发本体 |
| **`/setequip?bid=`** | 穿装备 | **自动按 `type` 定部位槽**（`equip_slot_for`） |
| **`/unequip?slot=`** | 卸装备 | 退回背包 |
| **`/setheros?bids=`** | 设置伙伴列表 | 写回 `config.json` + 推送 |
| **`/setjubaopen?pool=bid:w,...`** | 设置聚宝盆奖池 | 写回 `config.json` |
| **`/setmissions?bid=`** | 设置任务链头 | 清空后置该任务为进行中 |
| **`/reset?what=bag\|equip\|store\|mission\|levgift\|all`** | 重置各囊/任务/礼包记录 | — |
| **`/reload?what=item\|mall\|gift\|mission\|config\|all`** | **热重载配置表** | 清缓存，下次读取即生效 |

### 2.2 实测（全部通过）

```
giveitem 16201x3  -> {"ok":true, given:[{bid:16201,num:3,name:"10级速度符"}], pushed:1}
setequip 40003    -> {"ok":true, bid:40003, slot:1, name:"秘银长枪", pushed:1}
setjubaopen       -> {"ok":true, pool:[{bid:16201,w:40},{bid:33001,w:30}]}
reset levgift     -> {"ok":true, reset:["levgift"]}
listitems 长枪     -> {"ok":true, n:4, items:[见习长枪/玄铁长枪/...]}
setmissions 10010 -> {"ok":true, head:10010, name:"斗罗魂师"}
lockitem ... (ok)
```

### 2.3 ★ 过程中修掉的一个真 bug

```
NameError: name 'CFG' is not defined
```

**根因：配置原本只作为 `self.cfg` 传给 TCP handler，HTTP 管理接口**拿不到****。
**⇒ 修：加模块级 `CFG = {}`，`main()` 加载后 `CFG.clear(); CFG.update(cfg)`。**
**⇒ 教训：新接口必须确认自己依赖的全局**确实存在**（这次是靠 stderr 的 Traceback 直接定位的）。**

---

## 三、`dsh_admin.ps1`：菜单从 **9 项**扩充到 **20+ 项**

### 3.1 菜单结构（分组）

```
[角色]       [1]~[8]   等级 / 三种货币（设置 + 增量）/ 一键全满
[物品]       [10] 检索物品（按名字找 bid）
             [11] 发物品      [12] 开礼包
[装备]       [20] 穿装备（自动定槽）  [21] 卸装备
[伙伴/聚宝盆] [30] 设置伙伴    [31] 设置聚宝盆奖池
[任务]       [40] 设置任务链头
[重置]       [50]~[55] 背包/装备/仓库/任务/礼包/全部
[热重载]     [60] 物品/商城/礼包/任务/主配置
```

### 3.2 ★ 新增「状态总览」

**每次进菜单都实时显示**（靠 `/status`）：

```
  --- 当前状态 ---
    角色    DSH   等级 160   经验 1550
    钻石    910314
    金魂币  999999
    银魂币  849961
    背包    5 件
    装备    5 件
    仓库    0 件
            slot1=40003  slot2=41801  slot3=41401  slot5=41001  slot6=41211
    礼包已领
```

**⇒ 改任何东西都能**当场看到结果**，不用来回切窗口。**

### 3.3 ★ 本轮踩到的两个编码/语法坑（都已修，如实记录）

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1 | `The string is missing the terminator` | **`dsh_admin.ps1` 丢过 UTF-8 BOM** ⇒ PowerShell 5.1 按 GBK 读 ⇒ 中文乱码吞引号 | **写回 BOM**（`utf-8-sig`） |
| 2 | `Variable reference is not valid. ':' was not followed by...` | `"  $prompt: "` 里 **`:` 被当成驱动器引用** | 改 **`"  ${prompt}: "`** |

**⇒ 验证方式：必须用 `powershell.exe -File`（5.1）**，`[Parser]::ParseFile` 会嗅探编码、**发现不了 BOM 问题**。

---

## 四、当前状态

```
dsh_admin.bat  141 B（纯 ASCII 启动器，本身无问题）
dsh_admin.ps1  7693 B（UTF-8 **带 BOM**，PowerShell 5.1 语法 OK，菜单实测正常）
服务端         8080/9000 运行中 ｜ stderr 0 字节
```

**实测输出（`echo 0 | dsh_admin.bat`）：**
```
============================================================
   绝世唐门 私服管理台   （在线热改 + 立即推送，无需重登）
============================================================
  --- 当前状态 ---
    角色    DSH   等级 160   经验 1550
    ...（背包/装备/仓库 + 装备槽明细）
  [角色] [物品] [装备] [伙伴/聚宝盆] [任务] [重置/热重载] 分组菜单
```

---

## 五、仍未做（如实）

| 项 | 说明 |
|---|---|
| **物品"使用效果"的完整模拟** | 目前只做「礼包给内容」；加经验/buff/回血**未实现**（需效果表） |
| **伙伴属性/战力** | 需大量配置 + 权威公式；现只做列表/查询 |
| **`11200~11205`（伙伴装备）** | 含未解子表，按纪律未做 |
| **装备↔仓库 移动** | 目前是**安全拒绝**（曾丢物品，见另一份文档） |
