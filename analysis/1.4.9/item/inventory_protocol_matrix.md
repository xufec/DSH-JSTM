# 1.4.9 背包/物品协议矩阵（inventory_protocol_matrix）

> **目标 APK**：`anzbao\jstm.apk` — 绝世唐门 **1.4.9**，包名 `com.shiyue.dldl.ewan.qihoo`。
> **版本锁定声明**：本文全部 CMD 号、字段名、字段顺序与类型，均来自上述 1.4.9 APK 的
> `assets/src/config/protocal/cmd_resolve_*.luac`。
> `anzbao\jstm_142165.apk`（1.4.11）、`anzbao\dldlJl.apk`、`patched\*_142165*`
> **一律未读取**，不作为任何证据。

---

## 0. 状态取值定义

| 状态 | 含义 |
|---|---|
| `已确认` | 来自 **1.4.9 APK 权威字节码** —— `proto_spec.py` 从 `AutoConstruct(dir, cmd, {...})` 还原，或 `RegisterProtocal(cmd,'handler')` 注册点可见 |
| `已验证` | 经**真实运行时**联调确认（发收报文一致） |
| `待实现` | 规范已确认，但私服尚未实现 |
| `未知` | 无法从 1.4.9 包内确定 |

> **本次审计未做任何运行时联调**，故本文**不出现 `已验证`**。
> 所有 `已确认` 均指"权威字节码层面已确认"，不代表服务端已实现。

---

## 1. 权威性说明（证据链）

`proto_spec.py` 的权威性来自对 `cmd_resolve_105.luac` `proto#0` 的反汇编：

```
TGETS  A=1 B=0 C=0   ; ['AutoConstruct']
KSTR   A=3 D=1       ; 'sc'                  <- 方向
KSHORT A=4 D=10500   ; 10500                 <- CMD
TDUP   A=5 D=2       ; TableConst(array=[...])  <- 字段数组
CALL   A=1 D=261
```

即每个消息由 `AutoConstruct(方向, CMD, { '<字段名>__<格式字符>', ... })` 构造，
**数组顺序即字段顺序**。格式字符：`C`=uint8 `H`=uint16 `I`=uint32 `c`=int8
`h`=int16 `i`=int32 `s`=string `D|Xxx|`=计数前缀 + `Xxx` 结构数组。

客户端注册点用另一条独立证据链确认（`RegisterProtocal(<cmd>, '<handler>')`）：

```
MOV    A=2 D=0
TGETS  A=1 B=0 C=0   ; ['RegisterProtocal']
KSHORT A=3 D=10500   ; 10500
KSTR   A=4 D=1       ; 'handle_10500'
CALL   A=1 D=260
```

两处独立证据（消息定义 + 客户端注册）在 CMD 号上完全吻合。

---

## 1.5 第三条独立证据：APK 自带的消息**类名**

`cmd_resolve_*.luac` 的**注册表常量**里除了消息类名，还保留了带语义的英文类名。
对 `cmd_resolve_105.luac`、`cmd_resolve_127.luac` 提取全部
形如 `^(SC|CS)[A-Za-z]*_\d+$` 的字符串（均在 `proto#204` 注册表里）：

| CMD | 请求类名（CS） | 响应/推送类名（SC） | 与 `cmd_table.json` 中文名的一致性 |
|---|---|---|---|
| 10500 | **（无）** | **`SCAddRoleBag_10500`** | "推送角色背包数据" ✔（AddRoleBag = 增加/推送角色背包） |
| 10501 | **（无）** | **`SCNumUpdate_10501`** | "物品数量更新" ✔（NumUpdate = 数量更新） |
| 10502 | **`CSRoleBag_10502`** | **`SCRoleBag_10502`** | "请求角色背包数据" ✔（RoleBag） |
| 10503 | **（无）** | **`SCDelItems_10503`** | "删除背包物品" ✔（DelItems = 删除物品） |
| 10505 | **`CSDblclickItem_10505`** | **`SCDblclickItem_10505`** | "物品使用协议" ✔（**DblclickItem = 双击物品** = 使用/装备） |
| 10543 | **（无）** | `SC_10543`（无名） | "物品更新扩展字段" |
| 10557 | **`CS_10557`**（无名） | `SC_10557`（无名） | "删除物品" |
| 12742 | **（无）** | `SC_12742`（无名） | "提示获得资产/物品" |

**这条证据的价值**：
- 它以**完全独立于 `cmd_table.json`** 的方式证实了 CMD 语义
  （`SCAddRoleBag` / `SCNumUpdate` / `SCRoleBag` / `SCDelItems` / `CSDblclickItem`）。
- 它**直接证实了"纯推送"的判断**：10500/10501/10503 只有 `SC*` 类名，
  没有对应的 `CS*` 类名。
- 顺带看到 `CSSellItems_10504` / `SCSellItems_10504`（卖物品）成对存在，
  说明该 CMD 是双向的 —— 与 §4 注册表里 10504 有 `handle_10504`
  且 `proto_spec` 能同时给出 CS/SC 相吻合。
- `cmd_resolve_127.luac` 也复核过：12742 **只有 `SC_12742`，没有 `CS_12742`**
  → 再次确认 12742 是服务端单向下发。

> 提取方法（`proto#204` 是注册表 proto）：
> ```powershell
> python -c "..."   # 见 §7 复现命令；对 cmd_resolve_105/127 遍历 proto.strings
> ```
> 105 号段共提取到 **136** 个类名。多数 CMD 只有 `CS_<cmd>` / `SC_<cmd>` 这种
> 无名形式；**有语义名的恰是较早/较核心的 CMD**（10500–10505）。

---

## 2. 协议矩阵

| 功能 | CMD | 消息类名（CS / SC） | 请求字段 | 响应字段 | 客户端模块 | 服务端 | 状态 |
|---|---|---|---|---|---|---|---|
| 推送角色背包数据 | **10500** | **（无 CS）** / **`SCAddRoleBag_10500`** | **（无 CS）** —— 纯 S→C 推送 | `bag_code:uint8`；`items:table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D\|Dsc10500attrs_ext\|, attrs_ext_list:D\|Dsc10500attrs_ext_list\|, attrs_ext_one_list:D\|Dsc10500attrs_ext_one_list\|, jewel_list:D\|Dsc10500jewel_list\|, str_ext_list:D\|Dsc10500str_ext_list\|)` | `assets/src/game/backpack/backpack_ctrl.luac` proto#18 bc#2 → `handle_10500`（proto#19） | 需下发（`mock_server.py` 未实现） | `已确认` |
| 物品数量更新 | **10501** | **（无 CS）** / **`SCNumUpdate_10501`** | **（无 CS）** —— 纯 S→C 推送 | `code:uint8`；`num_up_arr:table(item_id:uint32, new_qty:uint16)` | 同上 bc#7 → `handle_10501`（proto#20） | 需下发 | `已确认` |
| 请求角色背包数据 | **10502** | **`CSRoleBag_10502`** / **`SCRoleBag_10502`** | `bag_code:uint8` | `bag_code:uint8`；`items:table(id:uint32, bid:uint32, hero_bid:uint32, bind:uint8, intensify_lev:uint8, pos:uint16, quantity:uint16, ctime:uint32, expire_ts:uint32, durable:uint16, object:uint8, attrs_ext:D\|Dsc10502attrs_ext\|, attrs_ext_list:D\|Dsc10502attrs_ext_list\|, attrs_ext_one_list:D\|Dsc10502attrs_ext_one_list\|, jewel_list:D\|Dsc10502jewel_list\|, str_ext_list:D\|Dsc10502str_ext_list\|)` | 同上 bc#12 → `handle_10502`（proto#22）；客户端发包 `send_10502`（proto#21） | 需实现（本项目最关键的背包 CMD） | `已确认` |
| 删除背包物品 | **10503** | **（无 CS）** / **`SCDelItems_10503`** | **（无 CS）** —— 纯 S→C 推送 | `code:uint8`；`del_ids_arr:table(item_id:uint32)` | 同上 bc#17 → `handle_10503`（proto#23） | 需下发 | `已确认` |
| 物品使用协议 | **10505** | **`CSDblclickItem_10505`** / **`SCDblclickItem_10505`** | `code:uint8`；`item_id:uint32`；`use_num:uint16`；`type:uint32`；`bid:uint32` | `code:uint8`；`msg:string`；`item_bid:uint32` | 同上 bc#27 → `handle_10505`（proto#28）；客户端发包 `send_10505`（proto#26，形参 `code,item_id,use_num,type,bid`） | 需实现 | `已确认` |
| 物品位置更新 | **10508** | **（无 CS）** / `SC_10508`（无名） | **（无 CS）** —— 纯 S→C 推送 | `code:uint8`；`pos_up_arr:table(item_id:uint32, new_pos:uint8)` | 同上 bc#32 → `handle_10508`（proto#30） | 需下发 | `已确认` |
| 整理指定背包 | **10509** | `CS_10509`（无名） / `SC_10509`（无名） | `bag_code:uint8` | `code:uint8`；`msg:string` | 同上 bc#37 → `handle_10509`（proto#32）；客户端发包 `sender_10509`（proto#31，形参 `bag_code`） | 需实现 | `已确认` |
| 更新背包格子最大值 | **10510** | **（无 CS）** / `SC_10510`（无名） | **（无 CS）** —— 纯 S→C 推送 | `code:uint8`；`volume:uint8`；`open_volume:uint8` | 同上 bc#42 → `handle_10510`（proto#29） | 需下发 | `已确认` |
| 物品更新扩展字段 | **10543** | **（无 CS）** / `SC_10543`（无名） | **（无 CS）** —— 纯 S→C 推送 | `code:uint8`；`up_date_ext:table(item_id:uint32, attrs_ext:D\|Dsc10543attrs_ext\|)` | 同上 bc#117 → `hander_10543`（proto#58，注意拼写为 `hander_`） | 需下发 | `已确认` |
| 删除物品 | **10557** | `CS_10557`（无名） / `SC_10557`（无名） | `bag_code:uint8`；`args:table(id:uint32)` | `code:uint8`；`msg:string` | 同上 bc#132 → `hander_10557`（proto#64）；客户端发包 `sender_10557`（proto#63，形参 `bag_code,args`） | 需实现 | `已确认` |
| 提示获得资产/物品 | **12742** | **（无 CS）** / `SC_12742`（无名） | **（无 CS）** —— 纯 S→C 推送 | `asset_list:table(opt:uint8, key:uint32, val:uint32)` | `assets/src/game/chat/chat_ctrl.luac` proto#25 bc#62 → `handle12742` | 需下发（掉落/奖励提示） | `已确认` |

> **响应字段**一列 = `SC_*` 规范；**请求字段**一列 = `CS_*` 规范。标注"（无 CS）"
> 表示在 1.4.9 全部 `cmd_resolve_*.luac` 中**不存在**该 CMD 的 `cs` 方向定义，
> 属于服务端**单向下发**，客户端只注册了 `sc` 处理函数。

---

## 3. 逐条证据

### 3.1 CMD 10500 — 推送角色背包数据

```
SC_10500
    bag_code                 uint8
    items__T                 FMT(id@I##bid@I##hero_bid@I##bind@C##intensify_lev@C##pos@H##
                                  quantity@H##ctime@I##expire_ts@I##durable@H##object@C##
                                  attrs_ext@D|Dsc10500attrs_ext|##
                                  attrs_ext_list@D|Dsc10500attrs_ext_list|##
                                  attrs_ext_one_list@D|Dsc10500attrs_ext_one_list|##
                                  jewel_list@D|Dsc10500jewel_list|##
                                  str_ext_list@D|Dsc10500str_ext_list|)
     <- cmd_resolve_105.luac proto#0
```

- `cmd_table.json` 中文名：**推送角色背包数据**
- 客户端注册：`backpack_ctrl.luac` proto#18 bc#2 `RegisterProtocal(10500,'handle_10500')`
- 处理体：proto#19（9 条指令）
  ```
  TGETS r2 <- v['data'] ; ISEQP r2,0 ; JMP ...   -- data 为空则跳过
  TGETS r2 <- v['data'] ; MOV r3 <- r1
  TGETS r2 <- r2['addItemInBagCode'] ; MOV r4 <- 1
  CALL r2
  ```
  即调用 `data:addItemInBagCode(items)`（`items` 是第 1 个形参）。
  对应 `backpack_data.luac` 的 `addItemInBagCode`（proto#4）。
- **无 CS_10500**（`proto_spec.py cmds 10500` 只命中 1 个类）。

### 3.2 CMD 10501 — 物品数量更新

```
SC_10501
    code                     uint8
    num_up_arr__T            FMT(item_id@I##new_qty@H)
     <- cmd_resolve_105.luac proto#15
```

- 注册点：bc#7 → `handle_10501`
- **无 CS_10501**

### 3.3 CMD 10502 — 请求角色背包数据（核心）

```
CS_10502
    bag_code                 uint8
     <- cmd_resolve_105.luac proto#31

SC_10502
    bag_code                 uint8
    items__T                 FMT(id@I##bid@I##hero_bid@I##bind@C##intensify_lev@C##pos@H##
                                  quantity@H##ctime@I##expire_ts@I##durable@H##object@C##
                                  attrs_ext@D|Dsc10502attrs_ext|##
                                  attrs_ext_list@D|Dsc10502attrs_ext_list|##
                                  attrs_ext_one_list@D|Dsc10502attrs_ext_one_list|##
                                  jewel_list@D|Dsc10502jewel_list|##
                                  str_ext_list@D|Dsc10502str_ext_list|)
     <- cmd_resolve_105.luac proto#16
```

- 注册点：bc#12 → `handle_10502`
- **客户端发包**：`send_10502`（proto#21）
  ```
  r2 = ProtocalRulesMgr:getInstance():GetPrototype(10502)
  r2['bag_code'] = <形参 1>
  ProtocalRulesMgr:getInstance():SendProtocal(r2)
  ```
  形参表（proto#21 params=2）与 `CS_10502{bag_code:uint8}` **完全一致**。
- **处理体**（proto#22）：
  ```
  v['data']:initItemList(<形参>)
  v['data']:setRequireGoods(v['bag_code'], true)
  if v['bag_code'] == BackPackConst.Bag_Code.ROLE_EQUIP then
      self:checkTishiByPack()
  end
  ```
  即按 `bag_code` 初始化对应背包、标记必需物品、若为装备背包则检查提示。
- `SC_10502` 与 `SC_10500` 的 `items` 子结构**字段名、顺序、类型完全相同**，
  仅 `D|Dsc…|` 引用的子结构名不同（`Dsc10500*` 与 `Dsc10502*`）。

### 3.4 CMD 10503 — 删除背包物品

```
SC_10503
    code                     uint8
    del_ids_arr__T           FMT(item_id@I)
     <- cmd_resolve_105.luac proto#32
```

- 注册点：bc#17 → `handle_10503`
- **无 CS_10503**（删除由服务端主动推送）

### 3.5 CMD 10505 — 物品使用协议

```
CS_10505
    code                     uint8
    item_id                  uint32
    use_num                  uint16
    type                     uint32
    bid                      uint32
     <- cmd_resolve_105.luac proto#36

SC_10505
    code                     uint8
    msg                      string
    item_bid                 uint32
     <- cmd_resolve_105.luac proto#35
```

- 注册点：bc#27 → `handle_10505`
- **客户端发包**：`send_10505`（proto#26，`params=6`，即 `self + code,item_id,use_num,type,bid` 共 5 个实参）
  ```
  r2 = ...GetPrototype(10505)
  r2['code']     = <arg1>
  r2['item_id']  = <arg2>
  r2['use_num']  = <arg3>
  r2['type']     = <arg4>
  r2['bid']      = <arg5>
  ...SendProtocal(r2)
  ```
  赋值顺序与 `CS_10505` 字段顺序**完全一致**。
- **处理体**（proto#28，45 条指令）：
  ```
  if v['code'] ~= 0 then
      Fire(item_bid) -> GlobalEvent
      ...
  ```
  触发事件：
  - `MissionHelp.USE_SKILL_EVENT`
  - `PartnerEvent.USE_GOODS_SUCCESS`
  - `BackPackEvent.GET_NEW_LIST`
  - `BackPackEvent.showAssetsMsg`
  - `setIsPlay`

  > 注意：处理体用的是 `v['code']`、`v['item_bid']`、`v['msg']`，
  > 即消费的是 **`SC_10505`**（`code`/`msg`/`item_bid`），
  > 与 `CS_10505` 的 5 个字段**不是同一组**。注册 `10505` 只注册了这一个
  > 方向处理函数，客户端能同时收发两个方向的同名 CMD。

### 3.6 CMD 10508 — 物品位置更新

```
SC_10508
    code                     uint8
    pos_up_arr__T            FMT(item_id@I##new_pos@C)
     <- cmd_resolve_105.luac proto#41
```

- 注册点：bc#32 → `handle_10508`
- **无 CS_10508**
- 备注：`new_pos` 是 `uint8`（`C`），而 `SC_10502.items.pos` 是 `uint16`（`H`）——
  说明位置更新用的是压缩的 8 位下标。

### 3.7 CMD 10509 — 整理指定背包

```
CS_10509
    bag_code                 uint8
     <- cmd_resolve_105.luac proto#43

SC_10509
    code                     uint8
    msg                      string
     <- cmd_resolve_105.luac proto#42
```

- 注册点：bc#37 → `handle_10509`
- **客户端发包**：`sender_10509`（proto#31，`params=2`）
  ```
  r2 = ...GetPrototype(10509)
  r2['bag_code'] = <形参 1>
  ...SendProtocal(r2)
  ```
  与 `CS_10509{bag_code:uint8}` 一致。

### 3.8 CMD 10510 — 更新背包格子最大值

```
SC_10510
    code                     uint8
    volume                   uint8
    open_volume              uint8
     <- cmd_resolve_105.luac proto#44
```

- 注册点：bc#42 → `handle_10510`
- **无 CS_10510**
- 语义（INFERRED）：`volume` = 当前容量，`open_volume` = 已开启格子数。
  与客户端 `getRemainCellNum`（proto#72）配套。**未用代码证明**。

### 3.9 CMD 10543 — 物品更新扩展字段

```
SC_10543
    code                     uint8
    up_date_ext__T           FMT(item_id@I##attrs_ext@D|Dsc10543attrs_ext|)
     <- cmd_resolve_105.luac proto#131
```

- 注册点：bc#117 → **`hander_10543`**（注意是 `hander_` 而非 `handle_`）
- **无 CS_10543**
- 对应客户端 `backpack_data.luac` 的 `updateGoodsAttrsExt`（proto#21）
  （字段名 `up_date_ext` 与 `attrs_ext` 与该方法名语义吻合，但**方法→CMD 的调用链未逐条反汇编确认**，故该对应关系标记 `INFERRED`）

### 3.10 CMD 10557 — 删除物品

```
CS_10557
    bag_code                 uint8
    args__T                  FMT(id@I)
     <- cmd_resolve_105.luac proto#159

SC_10557
    code                     uint8
    msg                      string
     <- cmd_resolve_105.luac proto#158
```

- 注册点：bc#132 → **`hander_10557`**
- **客户端发包**：`sender_10557`（proto#63）
- 与 `10503`（`SC_10503` 推 `del_ids_arr`）的区别：`10503` 是服务端主动通知已删除，
  `10557` 是**客户端主动请求删除**（带 `bag_code` + `id` 列表）。
  该区分标记为 `INFERRED`（由方向与字段推断，未有代码交叉验证）。

### 3.11 CMD 12742 — 提示获得资产/物品

```
SC_12742
    asset_list__T            FMT(opt@C##key@I##val@I)
     <- cmd_resolve_127.luac proto#17
```

- 客户端注册：`assets/src/game/chat/chat_ctrl.luac` proto#25 bc#62
  `RegisterProtocal(12742,'handle12742')`（kgc#1 = `'handle12742'`，kgc#14 = `'RegisterProtocal'`）
- **无 CS_12742**
- `cmd_table.json` 中文名：**提示获得资产/物品**
- 语义（INFERRED）：`asset_list` 每项 `{opt, key, val}`；`key` 是资产/物品 id，
  `val` 是数量，`opt` 是操作类型。**`opt` 的枚举值 UNKNOWN**。
- ⚠️ 该 CMD 由**聊天模块**接收（飘窗/系统提示），不是背包模块。

---

## 4. 背包 CMD 全景（`backpack_ctrl.luac` 全量注册表）

`proto#18` 共 176 条指令，注册 **35** 个 CMD（每个都是 5 条指令一组：
`MOV` / `TGETS 'RegisterProtocal'` / `KSHORT <cmd>` / `KSTR '<handler>'` / `CALL`）。
完整列表（bc 索引 → CMD → handler）：

| # | bc# | CMD | handler | # | bc# | CMD | handler |
|---|---|---|---|---|---|---|---|
| 1 | 2 | 10500 | `handle_10500` | 19 | 92 | 10518 | `hander_10518` |
| 2 | 7 | 10501 | `handle_10501` | 20 | 97 | 10527 | `hander_10527` |
| 3 | 12 | 10502 | `handle_10502` | 21 | 102 | 10528 | `hander_10528` |
| 4 | 17 | 10503 | `handle_10503` | 22 | 107 | 10542 | `hander_10542` |
| 5 | 22 | 10504 | `handle_10504` | 23 | 112 | 10548 | `hander_10548` |
| 6 | 27 | 10505 | `handle_10505` | 24 | 117 | **10543** | `hander_10543` |
| 7 | 32 | 10508 | `handle_10508` | 25 | 122 | 10551 | `hander_10551` |
| 8 | 37 | 10509 | `handle_10509` | 26 | 127 | 10552 | `hander_10552` |
| 9 | 42 | 10510 | `handle_10510` | 27 | 132 | **10557** | `hander_10557` |
| 10 | 47 | 10511 | `handle_10511` | 28 | 137 | 10534 | `hander_10534` |
| 11 | 52 | 10585 | `hander_10585` | 29 | 142 | 10535 | `hander_10535` |
| 12 | 57 | 10512 | `handle_10512` | 30 | 147 | 10536 | `hander_10536` |
| 13 | 62 | 10513 | `handle_10513` | 31 | 152 | 10582 | `hander_10582` |
| 14 | 67 | 10514 | `handle_10514` | 32 | 157 | 10537 | `hander_10537` |
| 15 | 72 | 10540 | `hander_10540` | 33 | 162 | 10586 | `hander_10586` |
| 16 | 77 | 10515 | `hander_10515` | 34 | 167 | 10587 | `hander_10587` |
| 17 | 82 | 10516 | `hander_10516` | 35 | 172 | 10588 | `hander_10588` |
| 18 | 87 | 10517 | `hander_10517` | | | | |

> 命名不一致：**10500–10514、10511 用 `handle_`**，**10515 起用 `hander_`**
> （`hander_10543`、`hander_10557` 属后者）。这是源 APK 的原始拼写，非提取误差。

证据：`tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 18 0 176`；
方法定义表：`tools/battle_audit.py defs assets/src/game/backpack/backpack_ctrl.luac`（67 个定义点）。

---

## 5. 物品数据模型

### 5.1 线上格式（wire）

一件背包物品在 `SC_10500` / `SC_10502` 的 `items` 数组中固定 **16 个字段**：

| # | 字段 | 类型 | 说明 | 证据 |
|---|---|---|---|---|
| 1 | `id` | uint32 | 物品实例唯一 id（bag_item_id） | `FMT` |
| 2 | `bid` | uint32 | 物品配置 bid | `FMT` |
| 3 | `hero_bid` | uint32 | 所属英雄 bid（0 = 不在英雄身上） | `FMT` |
| 4 | `bind` | uint8 | 绑定标志 | `FMT` |
| 5 | `intensify_lev` | uint8 | 强化等级 | `FMT` |
| 6 | `pos` | uint16 | 背包格位置 | `FMT` |
| 7 | `quantity` | uint16 | 数量 | `FMT` |
| 8 | `ctime` | uint32 | 创建时间戳 | `FMT` |
| 9 | `expire_ts` | uint32 | 过期时间戳 | `FMT` |
| 10 | `durable` | uint16 | 耐久 | `FMT` |
| 11 | `object` | uint8 | 对象标志 | `FMT` |
| 12 | `attrs_ext` | `D\|Dsc10500attrs_ext\|` | 扩展属性（计数前缀数组） | `FMT` |
| 13 | `attrs_ext_list` | `D\|Dsc10500attrs_ext_list\|` | 扩展属性列表 | `FMT` |
| 14 | `attrs_ext_one_list` | `D\|Dsc10500attrs_ext_one_list\|` | 单值扩展属性列表 | `FMT` |
| 15 | `jewel_list` | `D\|Dsc10500jewel_list\|` | 镶嵌宝石列表 | `FMT` |
| 16 | `str_ext_list` | `D\|Dsc10500str_ext_list\|` | 字符串扩展列表 | `FMT` |

（`SC_10502` 的同名字段结构完全一致，仅子结构前缀为 `Dsc10502*`。）

### 5.2 子结构定义

来源：`protocol/fields.json`、`protocol/manual.md`，并用 APK 内的
`cmd_resolve_105.luac` 读取器字节码交叉验证（见下）——**三处完全一致**。

| 子结构 | 字段（按线序） | 类型 | 证据 |
|---|---|---|---|
| `Dsc10500attrs_ext` | `attr_val` → `attr_code` | uint16 → uint32 | fields.json + manual.md L24401-24406 + `cmd_resolve_105.luac` proto#2 |
| `Dsc10500attr` | `code` → `state` | uint8 → uint8 | fields.json + proto#16 族 |
| `Dsc10500attrs_ext_list` | `attr` → `id` | uint8 → `struct<Dsc10500attr>` | fields.json |
| `Dsc10500attr_one_list` | `attr_val` | uint16 | fields.json |
| `Dsc10500attrs_ext_one_list` | `attr_one_list` → `id` | uint16 → `struct<Dsc10500attr_one_list>` | fields.json |
| `Dsc10500jewel_list` | `pos` → `bid` | uint32 → uint32 | fields.json + manual.md L24996-25003 |
| `Dsc10500str_ext_list` | `attr_str` → `id` | uint8 → string | fields.json |
| `Dsc10543attrs_ext` | `attr_val` → `attr_code` | uint16 → uint32 | fields.json |

#### `attrs_ext` 结构的证据评估

`cmd_resolve_105.luac` 的 **proto#2** 是该结构的**读取器**，完整反汇编：

```
kgc: #0'attr_val', #1'attr_code', #2{}, #3'insert', #4'table', #5'HI', #6'H', #7'ReadFMT'

 0  TGETS   A=2  B=1 C=0  ; ['ReadFMT']
 1  KSTR    A=3  D=1      ; 'H'        <- 先读 1 个 uint16（= 子结构计数前缀）
 2  CALL    A=2  D=514    ; 返回 1 值 -> r2
 3  ISEQP   A=2  D=0      ; if count == 0 then return end
 5  KSHORT  A=3  D=1      ; for i = 1, count
 9  TGETS   A=7  B=1 C=0  ; ['ReadFMT']
10  KSTR    A=8  D=2      ; 'HI'       <- 字面量：先 H(uint16) 再 I(uint32)
11  CALL    A=7  D=770    ; D=0x0302 -> 返回 2 值: r7, r8
15  TDUP    A=11 D=5      ; 新表 t
16  TSETS   A=7  B=11 C=6 ; t['attr_code'] = r7
17  TSETS   A=8  B=11 C=7 ; t['attr_val']  = r8
18  CALL    A=9  D=259    ; table.insert(list, t)
```

`已确认` 的事实：

| 事实 | 证据 |
|---|---|
| 该结构是 **计数前缀 + 数组**（即 `D\|Xxx\|` 语义） | bc#0-2 用 `ReadFMT('H')` 取计数，bc#5-8 `FORI` 循环 |
| 每个元素由**两个**字段组成 | bc#11 `CALL D=0x0302`（`D>>8=3` 参数、`D&0xff=2` 返回值） |
| 元素格式串是字面量 **`'HI'`**，即 **uint16 在前、uint32 在后** | bc#10 `KSTR 'HI'` |
| 字段名是 `attr_val` 与 `attr_code` | kgc#0/#1 |

**类型归属的冲突（必须保留为 `UNKNOWN`）**：

`'HI'` 字面量明确表示线上先是 **uint16**、后是 **uint32**。
`fields.json` 与 `manual.md` 记为 `attr_val:uint16, attr_code:uint32`
——与 `'HI'` **一致**。

但 bc#16/17 把 `r7`（第 1 个返回值）写进 `'attr_code'`、把 `r8` 写进 `'attr_val'`。
若 `ReadFMT` 严格按格式串顺序返回，则字节码会推出
`attr_code:uint16, attr_val:uint32`，与 `'HI'` 矛盾。

自洽解释（**推测，无代码证据**）：`H` 在 `'HI'` 中扮演的是**子列表计数前缀**，
`ReadFMT` 可能不把它计入"字段返回值"的位置，从而改变寄存器落位顺序。

> **本文档的处置**：
> - 元素的**格式串 = `'HI'`（uint16 → uint32）= `已确认`**（字面量）。
> - **字段顺序 = `已确认`**：`attr_val` 与 `attr_code` 的先后由
>   `SC_10500.items` 的 `FMT` 字符串（`…##attr_val@H##attr_code@I##…`）给出，
>   与 `fields.json`/`manual.md` 一致。
> - **`attr_val`/`attr_code` 各自承载哪个宽度 = `UNKNOWN`**：
>   应以 `fields.json`/`manual.md`（`attr_val:uint16, attr_code:uint32`，
>   与 `'HI'` 字面量一致）为准实现，
>   但**必须用一次真实抓包裁定**。
>
> 私服建议：首版按 `attr_val:uint16, attr_code:uint32` 实现；
> 若客户端属性显示错乱，再互换。**这是全文档唯一一处
> "字节码控制流推断与格式串字面量结论相反"的地方。**

### 5.3 客户端 VO 模型

`assets/src/common/goods_vo.luac` 的 `GoodsVo.__init`（proto#2，33 条指令）
逐字段初始化为 0 / 空表，顺序为（`kgc` 倒序展开后的写入顺序）：

```
hero_bid=0, id=0, bid=0, pos=0, quantity=0, bind=0, ctime=0,
expire_ts=0, durable=0, object=0, intensify_lev=0,
attrs_ext={}, attrs_ext_list={}, jewel_list={},
attrs_ext_one_list={}, str_ext_list={}
```

证据：
```
0  KSHORT  A=1 D=0  ; 1  TSETS A=1 B=0 C=0 ; ['hero_bid']
2  KSHORT  A=1 D=0  ; 3  TSETS A=1 B=0 C=1 ; ['id']
...
22 TNEW    A=1      ; 23 TSETS A=1 B=0 C=11 ; ['attrs_ext']
30 TNEW    A=1      ; 31 TSETS A=1 B=0 C=15 ; ['str_ext_list']
```

**结论（已确认）**：客户端 `GoodsVo` 的字段集合与线上 `SC_10500/10502.items`
的字段集合**逐个对应、无一多余、无一缺失**，共 16 个。

`goods_vo.luac` 其余方法（证据：`battle_audit.py defs`，共 29 个定义点）：

| 方法 | proto# | 用途 |
|---|---|---|
| `initAttrData` | 3 | 初始化属性数据 |
| `getGoodsAttr` / `setGoodsAttr` | 4/5 | 读写属性 |
| `getAttrExtByCode` / `setAttrExtByCode` | 6/7 | 按 code 读写 `attrs_ext` |
| `getStringExtByCode` / `setStringExtByCode` | 8/9 | 按 code 读写 `str_ext_list` |
| `getAttrExtListByCode` / `setAttrExtListByCode` | 11/10 | 按 code 读写 `attrs_ext_list` |
| `getAttrsExtOneListByCode` / `setAttrsExtOneListByCode` | 13/12 | 按 code 读写 `attrs_ext_one_list` |
| `isShopGoods` / `isBind` / `isCanSale` | 14/15/16 | 判定 |
| `getJewelbyPos` / `getJewelLsit` / `getJewelsNum` / `isInlayJewel` / `getJewelsAttrs` | 17–21 | 宝石 |
| `isRoleEquip` / `isPartnerEquip` / `isAllEquip` | 22/23/24 | 装备类型判定 |
| `getType` / `getQuality` | 26/27 | 取类型/品质 |

`assets/src/common/goods_item.luac`（42 proto / 39 定义点）与
`assets/src/common/common_item.luac`（31 proto / 28 定义点）是**表现层**：
`setData`（goods_item proto#8，392 条指令）、`initItem`（proto#1）、
`createImage`、`addItemTag`、`setNum` 等，负责图标与角标渲染，不含线上字段解析。

### 5.4 是否存在 `Config.Item` 表 —— **不存在（关键发现）**

搜索了整个 APK 的 347 个 `assets/src/config/*.luac`：

- **有** `assets/src/config/config_item.luac`（838 442 B）
- **但它的 `Config.Item` 不是数据表，而是一组访问器函数**。

`config_item.luac` 的 `proto#0`（91 条指令）反汇编：

```
0  GGET   A=2 D=0        ; 'Config'
1  TGETS  A=2 B=2 C=1    ; ['ItemData']
2  TGETV  A=2 D=513      ; ItemData[<arg1>]
3  ISF    A=0 D=2
4  JMP    A=3 D=32778
...
21 GGET   A=3 D=0        ; 'Config'
22 TGETS  A=3 B=3 C=1    ; ['ItemData']
23 TDUP   A=4 D=2        ; {} 新表
24 TGETB  A=5 D=513      ; ItemData[1]
25 TSETS  A=5 B=4 C=3    ; t['bid'] = ...
26 TGETB  A=5 D=514      ; ItemData[2]
27 TSETS  A=5 B=4 C=4    ; t['name'] = ...
...
32 TGETB  A=5 D=517
33 TSETS  A=5 B=4 C=7    ; t['bind_type'] = ...
```

即 `proto#0` 是 `function Config.Item.getItem(bid) ... end`——
**运行时读取 `Config.ItemData`**，而 `Config.ItemData` **在整个 APK 中从未被定义**。

#### 决定性证据 1：全包无 `GSET 'ItemData'`

`GSET D=<kidx>` 是"写全局变量"指令。扫描**全部 2232 个 `.luac`** 的每一条 `GSET`，
收集所有名字里含 `Item` 的全局：

```powershell
# 见 §7 复现命令第 6 条
```

结果：约 200 个 `...Item` 全局被 `GSET` 写入（`AwardItem`、`CommonItem`、
`DailySignItem`、`DropItem`、`GoodsItem`、`MenuItem` …… 全部是**类名**），
**唯独没有 `ItemData`**。

#### 决定性证据 2：深字符串扫描（含 TableConst 键/值）

`tools/find_luac_global.py` 只检查常表的**顶层**字符串，会漏掉
`TDUP` 表常量内部的键/值（这正是 `config_drop.luac` 字段名的存放方式）。
用 `tools/scan_luac_strings_deep.py`（递归展开 `TableConst`）重扫：

```powershell
python tools/scan_luac_strings_deep.py --stats
#  扫描 .luac 文件 2232 个，深字符串常量总计 474679

python tools/scan_luac_strings_deep.py ItemData
#  命中 8 个 proto（6 个文件）：
#    assets/src/common/award_item.luac                     proto#6
#    assets/src/common/common_item.luac                    proto#6
#    assets/src/config/config_item.luac                    proto#0, proto#1
#    assets/src/game/blackmarketeer/view/emptygird_view.luac  proto#7
#    assets/src/game/dailysign/dailysign_item.luac         proto#7
#    assets/src/game/equipforge/view/left_side/equipforge_list_view.luac  proto#4, proto#32
#  —— 全部是读取方，无定义方
```

同一工具也复核了掉落表：

```powershell
python tools/scan_luac_strings_deep.py drop_type normal_sum first_p_sum core_p_sum
#  命中文件 1 个：assets/src/config/config_drop.luac proto#0
#  （即除定义点外，全包没有任何文件引用掉落字段）

python tools/scan_luac_strings_deep.py Drop DropItem
#  命中 3 个：config_drop / config_drop_item（定义点）
#           + game/drop/drop_item.luac proto#17（是类名 'DropItem'）
```

**结论**：
1. **1.4.9 客户端包内不存在物品配置数据表**（物品名/图标/品质/类型均由服务端下发，
   或由 `SC_10500/SC_10502.items.bid` 对应的服务端数据决定）。
   包内唯一自带的物品名是 `config_drop_item.luac` 的 39 条 `item_name`（且见
   `drop_model.md` §9：那些是别的游戏的角色）。
2. `config_item.luac` 的 **30 个物品字段**是 APK 内唯一可得的物品字段清单。
   `proto#0` 的 `TSETS` 序列（写入下标与字段名交替出现）给出**确定的顺序**：

   ```
   TGETB  ... D=513  ; ItemData[1]        TSETS ... C=3  ; ['bid']
   TGETB  ... D=514  ; ItemData[2]        TSETS ... C=4  ; ['name']
   TGETB  ... D=515  ; ItemData[3]        TSETS ... C=5  ; ['type']
   ...                                                      （共 30 组）
   ```
   `TGETB` 的 `D&0xff` 即 `ItemData` 下标。字段名常量在 `kgc` 中按**倒序**排列，
   故 `ItemData[i]` 对应 `kgc[30 - i]`。完整映射：

   | # | 下标 | 字段名 | # | 下标 | 字段名 |
   |---|---|---|---|---|---|
   | 1 | `ItemData[1]` | `bid` | 16 | `ItemData[16]` | `value` |
   | 2 | `ItemData[2]` | `name` | 17 | `ItemData[17]` | `item_res` |
   | 3 | `ItemData[3]` | `type` | 18 | `ItemData[18]` | `attr` |
   | 4 | `ItemData[4]` | `lev` | 19 | `ItemData[19]` | `more_attr` |
   | 5 | `ItemData[5]` | `bind_type` | 20 | `ItemData[20]` | `cumsum_attr` |
   | 6 | `ItemData[6]` | `quality` | 21 | `ItemData[21]` | `is_fuse` |
   | 7 | `ItemData[7]` | `grade` | 22 | `ItemData[22]` | `animate_res_id` |
   | 8 | `ItemData[8]` | `overlap` | 23 | `ItemData[23]` | `desc` |
   | 9 | `ItemData[9]` | `durable` | 24 | `ItemData[24]` | `vice_desc` |
   | 10 | `ItemData[10]` | `use_type` | 25 | `ItemData[25]` | `make_desc` |
   | 11 | `ItemData[11]` | `source` | 26 | `ItemData[26]` | `group` |
   | 12 | `ItemData[12]` | `cooldown` | 27 | `ItemData[27]` | `fast_use` |
   | 13 | `ItemData[13]` | `client_effect` | 28 | `ItemData[28]` | `lingqi` |
   | 14 | `ItemData[14]` | `next_bid` | 29 | `ItemData[29]` | `effect` |
   | 15 | `ItemData[15]` | `condition` | 30 | `ItemData[30]` | `use_num` |

   **注意**：这里的下标是 `Config.ItemData[id]` 这**一条记录内部**的数组下标
   （即"物品字段的第 i 列"），**不是物品 bid**。
   `Config.ItemData` 本身在包内**不存在**，所以这份字段清单
   **没有配套数据可验证** → 标记为 `INFERRED（结构来自字节码，数据缺失）`。

3. `config_drop_item.luac` 里的 `item_name`（如 `'小仙桃'`、`'铜·经验符'`、
   `'李逍遥召唤符'`）**是 APK 内唯一自带的物品名称来源**（仅 39 条）。

---

## 6. 未确定项（`未知` / `待确认`）

| 项 | 状态 | 需要什么证据 |
|---|---|---|
| `attrs_ext.attr_val` / `attr_code` 各自承载的宽度（uint16 还是 uint32） | **未知** | 元素格式串是 `'HI'`（已确认），但读取器寄存器落位与字面量冲突（§5.2） |
| `Dsc10500attr_one_list.id` 等嵌套 `struct<>` 的展开顺序 | **未知** | 同上，未逐个反汇编读取器 |
| `object`、`opt`、`type` 字段的枚举取值 | **未知** | 服务端代码或枚举表（APK 内未见对应枚举） |
| `10510` 的 `volume` / `open_volume` 确切语义 | **INFERRED** | `getRemainCellNum` 未逐条反汇编 |
| `10543` ↔ `updateGoodsAttrsExt` 的调用链 | **INFERRED** | 未反汇编调用方 |
| `10557` 与 `10503` 的职责边界 | **INFERRED** | 未反汇编调用方 |
| `12742.asset_list[].opt` 取值 | **未知** | 服务端代码 |
| `Config.ItemData` 的真实数据 | **不在包内** | 服务端数据（字段清单已确认，见 §5.4；仅缺数据） |
| `bag_code` 的取值范围 | **未知** | 客户端有 `BackPackConst.Bag_Code`（`ROLE_EQUIP` 已见于 proto#22），但枚举表未展开 |

> **已确认的项（不再是 UNKNOWN 的部分）**：
> ① `attrs_ext` 的元素**格式串是字面量 `'HI'`**（uint16 → uint32），
> 由 `cmd_resolve_105.luac` proto#2 bc#10 `KSTR 'HI'` 直接确认；
> ② `attrs_ext` 是**计数前缀 + 数组**结构，由 proto#2 的
> `ReadFMT('H')` 取计数 + `FORI` 循环确认；
> ③ 字段**顺序**为 `attr_val` 在前，由 `SC_10500.items` 的 `FMT` 字符串
> 与 `fields.json`/`manual.md` 一致确认。
>
> **仍为 UNKNOWN**：`attr_val` / `attr_code` 各自对应 uint16 还是 uint32
> —— 见 §5.2 末的冲突说明。

---

## 7. 复现命令

```powershell
# 1) 消息规范（权威）
python tools/proto_spec.py cmds 10500 10501 10502 10503 10505 10508 10509 10510 10543 10557 12742

# 2) 客户端注册点（全包扫描）
python tools/find_register_protocal.py 10500 10501 10502 10503 10505 10508 10509 10510 10543 10557 12742

# 3) 背包控制器完整注册表 + 方法定义表
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 18 0 176
python tools/battle_audit.py defs assets/src/game/backpack/backpack_ctrl.luac

# 4) 关键处理体 / 发包体
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 19 0 10
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 21 0 14
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 22 0 24
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 26 0 18
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 28 0 45
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/backpack/backpack_ctrl.luac 31 0 14
python tools/luajit_dis.py anzbao\jstm.apk assets/src/game/chat/chat_ctrl.luac 25 55 20

# 5) 物品 VO 与配置
python tools/luajit_dis.py anzbao\jstm.apk assets/src/common/goods_vo.luac 2 0 33
python tools/battle_audit.py defs assets/src/common/goods_vo.luac
python tools/luajit_dis.py anzbao\jstm.apk assets/src/config/config_item.luac 0 0 91
python tools/find_luac_global.py ItemData Drop DropItem
python tools/find_register_protocal.py

# 6) 第三条独立证据：APK 自带的消息类名（cmd_resolve_105/127 的注册表）
python -c "import zipfile,re,sys; sys.path.insert(0,'tools'); from luajit_bc import parse_bytes; z=zipfile.ZipFile('anzbao/jstm.apk'); [print(fn, sorted({s for pt in parse_bytes(z.read(fn)).protos for s in pt.strings if re.match(r'^(SC|CS)[A-Za-z]*_[0-9]+$', s)})) for fn in ('assets/src/config/protocal/cmd_resolve_105.luac','assets/src/config/protocal/cmd_resolve_127.luac')]"

# 7) 决定性证据：全包 GSET 扫描 + 深字符串扫描
python tools/scan_luac_strings_deep.py --stats
python tools/scan_luac_strings_deep.py ItemData
python tools/scan_luac_strings_deep.py drop_type normal_sum first_p_sum core_p_sum
python tools/scan_luac_strings_deep.py Drop DropItem
#   以及"全包收集所有 GSET 名字含 Item 的全局"（见 §5.4 决定性证据 1 的脚本）
```

---

## 8. 对私服实现的直接结论

1. **背包最小可用集**：实现 `CS_10502 → SC_10502` 即可让客户端背包显示出来
   （客户端 `handle_10502` 会 `initItemList` + `setRequireGoods`）。
   物品的 16 个字段必须**全部按序填充**，缺字段会导致客户端读表错位。
2. **推荐随登录/进场景下发 `SC_10500`**（客户端已注册 `handle_10500`，
   语义是"推送全量背包"）。
3. `10501`（数量）、`10503`（删除）、`10508`（位置）、`10510`（格子数）、
   `10543`（扩展字段）都是**服务端主动推送**，无需 CS。
4. **`Config.ItemData` 不在客户端** → 服务端必须自己维护"bid → 物品名/图标/品质"
   的映射；APK 内唯一可复用的物品名来源是 `config_drop_item.luac` 的 `item_name`
   （仅 39 条）。
5. `SC_10502.items` 的 16 个字段**顺序已确认**；但 `attrs_ext` 子结构内部
   `attr_val` / `attr_code` **各自承载的宽度存疑**（§5.2），
   首次联调时应抓一次真实报文核对，必要时两种解释都试一次。
