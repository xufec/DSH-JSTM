# 绝世唐门 1.4.9 私服化 —— 技术文档

> **文档性质**：技术实现参考。含**线格式、字节码逆向方法、配置提取、数据模型、服务端结构、构建链、调试手段**。
> **纪律**：标注【已确认】【已验证】【待验证】【未知】。
> **生成时间**：2026-09-18

---

## 一、目标客户端

| 项 | 值 |
|---|---|
| APK | `anzbao/jstm.apk` |
| 包名 | `com.shiyue.dldl.ewan.qihoo` |
| versionName | **1.4.9**【已确认】 |
| 引擎 | **Cocos2d-x 3.6** |
| 脚本 | **LuaJIT 2.0 bytecode**（magic `1b 4c 4a`）【已验证】 |
| Activity | `org.cocos2dx.lua.AppActivity` |
| 设备 | MuMu Player 12，`adb -s 127.0.0.1:16384`，屏幕 2560×1440 |

**★ 三个 APK 的版本关系**【已验证】：
```
jstm.apk         1.4.9      347 config 表
jstm_142165.apk  更高版本    355 config 表   ← ★ 1.4.9 是其**子集**（可交叉校验）
dldlJl.apk       另一渠道    256 config 表

142165 多出 8 张：foot_print / golden_egg / kaifu_gift / top_level /
                  treasure_palace / vip_diamond / cmd_resolve_210 / 221
⇒ 那些是 **1.4.9 没有的功能** ⇒ 与目标无关
```

---

## 二、★ 线格式（协议层）

### 2.1 帧结构【已验证】
```
┌────────────────┬──────────────┬─────────────────────┐
│ payload_len    │ cmd          │ body                │
│ uint32 **BE**  │ uint16 **BE**│ payload_len - 2 字节│
└────────────────┴──────────────┴─────────────────────┘
```
**注意**：`payload_len` 包含 `cmd` 的 2 字节 ⇒ `body` 长度 = `payload_len - 2`。

### 2.1.1 ★★ 客户端发包带 **4 字节缓冲区残留**【已验证 2026-09-19】

真机抓包（341 个 `server/logs/tcp_*.bin`）显示：**客户端每个 CS body 尾部都多出 4 字节**
（发送缓冲区未清零的残留），与协议字段无关：

| 命令 | CS 规格真实长度 | 抓包 body 长度 | 抓包 body |
|---|---|---|---|
| `16500` | 0（空消息） | 4 | `00660000` |
| `17200` | 0（空消息） | 4 | `010103e9` |
| `16400` | 1（`type:u8`） | 5 | `0100000003` |
| `16603` | 4（`bid:u32`） | 8 | `00000be1 0001316f` |
| `16605` | 410（`2 + 102×4`） | 414 | `…2d2d2d2d`（"----"） |
| `12901` | 3（`ord,num,flag`） | 7 | `000501 5603e900` |
| `12832` | 4（`id:u16, num:u16`） | 8 | `4e24 0001 | 138f0000` |

**⇒ 三条纪律（都踩过坑）：**

1. **服务端只读规格内的前 N 字节，尾部残留一律忽略**（全仓 `len(body) >= N` 前缀式读取）。
2. **包长是弱证据，不能反推字段个数**：`{bid}` 与 `{bid,num}` 对 8 字节 body 都"对得上"
   —— round34 曾据此把 `CS_16603` 误改成两字段，round35 靠 AutoConstruct 原始 spec 才纠正回来。
3. **规格来源优先级**：`AutoConstruct spec` > reader 原型（`Dsc*`）> 抓包长度。

### 2.2 ★ 成功判据【已确认】
```
code == TRUE(1) → 成功
code != 1       → 客户端走 message(msg)
                   ★ 若 msg 为空串 ⇒ 弹出**空白框**
```

### 2.3 消息分类【已验证】
| 类型 | 特征 | 例 |
|---|---|---|
| **推送型** | 服务端主动发，客户端只接收 | `10500`(背包) `10501`(数量) `10503`(删除) `12405`(任务更新) `12406`(任务删除) |
| **请求-应答型** | 客户端请求 → 服务端应答 | `10502` `10301~10306` `12400~12403` |
| **★ 陷阱** | 对推送型协议做主动推会被**忽略** | 曾误推 `10502` |

---

## 三、★ LuaJIT 2.0 字节码逆向

### 3.1 工具链
```
tools/luajit_bc.py      解析字节码 → protos（含 bc/kgc/knum/array/hash）
tools/luajit_dis.py     反汇编（提供 OPS 表 + kidx 常量索引）
tools/show_cmd.py       看某 CMD 的权威字段定义
tools/dsc_spec.py       展开 D|Dsc*| 未解子表
```

**★ 审计 / 验证工具链（round35–42 新建，协议层的"自动体检"）**

| 工具 | 作用 |
|---|---|
| `audit_specs_vs_fields.py` | **独立第二路径**（扫 AutoConstruct 调用点）审计 `fields.json` ⇒ 2463 条 0 不一致 |
| `audit_sc_conformance.py` | SC 默认应答**静态**一致性（1635 条；`--generic`/`--unsupported` 只看应答集合） |
| `audit_sc_live.py` | SC 应答**在线**复核（走 TCP 真解析） |
| **`audit_dedicated.py`** | ★ **专用 handler 查询型审计**：补"真机没发过 + 走专用分支"的盲区（R43 的 `10306` 就藏在这里）⇒ 58/58 |
| `gen_attr_meta.py` | 生成 64 项属性元数据 + 与 `role_attr` 的差异清单（含"带权重却缺列"的项） |
| `replay_captures.py` | **真机流量回放**：`--per-cmd N` 多变体（默认每命令取 N 个高频 body） |
| `triage_gaps.py` | 把"有 SC 却无应答"按**客户端是否注册处理器**分类 ⇒ 区分真实缺口 / 无害缺口 |
| `resolve_dsc_refs.py` | 以 **reader 原型**为准重建 `Dsc*` 并展开 `D|X|` 引用（`--apply` 自动备份） |
| `verify_11215_10800.py` / `verify_10924.py` / `verify_16603.py` / `verify_rank.py` / `verify_13402.py` / `verify_attr_power.py` / `verify_account.py` | 各功能的**逐字节规格验证** |
| `_field_use.py` / `_bid_flag_map.py` | 字段读取点定位 / bid↔活动开关映射提取 |

### 3.2 ★ 指令解码要点（血泪总结）

| 指令 | 正确读法 |
|---|---|
| `KSTR` / `GGET` / `GSET` | `kidx(pt, (w>>16)&0xffff)` |
| `TGETS` / `TSETS` | `kidx(pt, (w>>16)&0xff)` |
| `KSHORT` | 值 = `(w>>16)&0xffff` |
| `TDUP` | 常量是 `TableConst`，取 `.array` / `.hash` |
| **`OPS`** | **是 `list` 不是 `dict`** ⇒ 只能 `OPS[w&0xff]`，**不能 `.get()`** |
| **`TSETS A, C`** | ⇒ **`R(A-1)[K[C]] = R(A)`**（由 `npc_ctrl proto[84]` 类定义块定标） |
| **`ISNEN A, D`** | **D 是常量表索引，不是值** ⇒ 必须读 `knum[D]`（曾因此发布错映射表） |

### 3.3 提取配置表的两种结构

| 结构 | 特征 | 提取法 |
|---|---|---|
| **直接表** | `proto[0]` 直接构造 | `tools/extract_config.py` 通用读取器（347 表） |
| **★ 懒加载** | `proto[1]` 是 `__index` 元方法 | 需抽 `TDUP` 的 `.hash`/`.array`（如 `config_attr`/`config_black_market`/`config_skill`） |

**懒加载识别**：`Config.X` 若无数据 ⇒ 看是否有 `__index` 函数（`@0 GGET 'Config' / TGETS 'X' / TGETV / IST / JMP` 模式）。

**★ 字段顺序推断**：从 `proto[0]` 的 `TGETB`/`TSETS` 配对**动态推出**；无配对则退回位置数组或哈希。

### 3.4 配置表规模【已验证】
```
config_skill.luac       3,032,592 字节（★ 347 表里最大）
config_item_gift.luac     292,151
config_fashion_upgrade    369,306
...
共 347 张
```

---

## 四、★ 数据模型

### 4.1 协议定义（`protocol/fields.json`）【已验证 · 2026-09-19 重建】

```
3553 条协议定义（CS 1444 / SC 1635 / Dsc* 子结构 472）
1634 个已知 CMD
真机抓包实际出现过   233 个 CMD（341 个抓包文件、49238 帧）
```

**★ 规格自洽化（round38）**：`D|Dsc*|` 嵌套引用原先**未展开**、且 `Dsc*` 段
**字段顺序被反转**（类型随之错位）。已用 `tools/resolve_dsc_refs.py`
**以 reader 原型（`ReadFMT` + 顺序 `TSETS`，不反转）为准**重建：

- 修正 `Dsc*` 条目 **302** 条（另有 4 条本就一致，133 条因歧义/缺 reader 保持原样不动）；
- 展开 `D|X|` 引用 **346** 处，`fields.json` 变为**自洽**（无需再查子表定义）。

**★ 五道审计 · 全部归零（round35–44）**

| 审计 | 工具 | 规模 | 结论 |
|---|---|---|---|
| CS 规格挖掘 | `audit_specs_vs_fields.py` | 2463 条（AutoConstruct 调用点独立还原） | **0 不一致** |
| SC 默认对接（静态） | `audit_sc_conformance.py` | 1635 条 SC 规格 | **0 不一致** |
| SC 默认对接（在线） | `audit_sc_live.py` | 93 条（默认集合 + 未开放集合） | **全一致** |
| **专用 handler 查询** | `audit_dedicated.py` | **58 条**（真机没发过 + 走专用分支） | **58/58 符合** |
| **真机流量回放** | `replay_captures.py --per-cmd 5` | **231 命令 / 876 变体** | **符合 831 / 不符 0** |

> 第 4 道是 round44 补的**盲区**：`10306` 这类命令**真机 341 抓包 0 次**、又走专用分支
> ⇒ 前三道审计全都覆盖不到。它曾经因为"同族就复用 `10304` 的切分"而**多写 8 字节**。
> 判据：CS 字段为空（纯查询）+ SC 不含 `code/result/tips`（非操作结果）。

**★ 应答缺口（GAP）收敛：73 → 34 → 8**（round37→39→41），
余下 8 条经 `tools/triage_gaps.py` 确认**客户端未注册处理器**（上报/广播型）⇒ 无应答本就无害。

> **结论订正**：早期文档写的"真机用到 128 个、服务端实现 116 个、未应答 66 个"
> 是 round30 之前的快照；现口径以上表为准。

### 4.2 SQLite（`server/state/roles.db`）【已验证】
**11 张表 / 98 列**

| 表 | 列数 | 用途 |
|---|---|---|
| `roles` | 23 | 角色主表（rid/name/lev/career/exp/...） |
| `role_attr` | 26 | 属性（25 属性 + rid）⚠️ **含派生项** |
| `missions` | 13 | 任务 |
| `role_assets` | 3 | 通用资产容器 |
| `mall_bought` | 4 | 商城已购 |
| `bag_items` | 7 | 背包 |
| `bag_volume` | 3 | 背包容量 |
| `equip_items` | 6 | 装备 |
| `store_items` | 7 | 仓库 |
| `levgift_got` | 3 | 等级礼包领取记录 |
| `sign_got` | 3 | 签到记录 |

**★ 写库范式（优于全部 5 个参考项目）**：
```
手写 UPSERT（INSERT OR IGNORE + UPDATE）
+ 列名白名单（防注入）
+ ? 全参数化
+ 线程本地连接（threading.local）
+ row_factory 每次复位
+ db_release() 回滚未提交事务
+ 成败检查（写失败不静默）
+ 时间戳
```

### 4.3 配置数据资产
| 文件 | 内容 |
|---|---|
| `server/item_config.json` | **3535 件物品**（含正确 `type`） |
| `server/mission_config.json` | **846 条任务** |
| `server/mall_config.json` | 商城（134 件原版 → 过滤后 71 件） |
| `server/item_gift.json` | 496 礼包 / 5353 映射 |
| `server/_attr_data.json` | **64 项属性 + AttrPower 战力权重** |
| `server/map_block.json` | 碰撞（26/124 场景，126 KB） |
| `server/config.json` | **★ 大量运行数值在此（未落库）** |

### 4.4 ★ 属性 / 战力系统

**属性定义（`config_attr.luac` proto[0]）**【已验证】
```
AttrLen        = 64
AttrId2Key     = {101:'strength', 102:'intellect', 103:'armor', 104:'constiution',
                  105:'atk_s', 106:'atk_p', 107:'def_s', 108:'def_p', 109:'hp_max', ...}
AttrId2Str     = {101:'力量', 105:'物攻', 109:'生命', ...}
AttrKeyIsShow  = 可见性白名单（10 项）
AttrPower      = 每属性战力权重
AttrPartnerPower = 伙伴版权重
```

**★ 战力权重（top）**【已验证】
```
atk_speed=450 速度 ｜ dodge=275 躲闪 ｜ hit=275 命中
crit=183 暴击 ｜ tenacity=183 抗暴
atk_p=106 法攻 ｜ atk_s=106 物攻
control=90 ｜ anti_control=90 ｜ def_abs=82 ｜ atk_abs=82
atk_abs_p=41 ｜ def_abs_p=41 ｜ atk_abs_s=41 ｜ def_abs_s=41
red_def_s=33 ｜ def_p=33 ｜ def_s=33
...
零权重（不参与战力）：strength/intellect/armor/hp/energy/... 共 40 项
```

**战力公式**：
```
战力 = Σ( 属性值[key] × AttrPower[key] )
```

**属性 ID 分段**【已验证】
```
101~104  strength/intellect/armor/constiution  ← 唯一的**输入项**
105~110  atk_s/atk_p/def_s/def_p/hp_max/hp
111~113  atk_speed/hit/dodge
116~118  energy_max/energy_min/energy
119~123  red_def_s/red_def_p/atk_abs/def_abs/reduce
124~127  hurt/hit_rate/crit_rate/anger_start
128~131  cure/be_cure/mspd/control
136~151  hurt_p/be_hurt/dodge_rate/tenacity_rate/...
201~209  *_rate_show(4) + crit_hurt/crit_reduce/red_tar_def_s/dmg_back
240~243  anti_control_s/c/c_y
```

**⚠️ 已知缺陷**：`role_attr` 只落 25 列 ⇒ **既存了 21 个派生项、又漏了 39 个属性**（应按 `AttrLen=64` 重构）。

---

## 五、服务端结构

### 5.1 模块
```
server/
├── mock_server.py    7265 行  ← 主服务端（TCP 9000 + HTTP 8080）
├── aoi.py            18.6 KB  ← 自研 AOI
├── pathfind.py       14.5 KB  ← 自研寻路（A* + Bresenham + L1/L2 校验）
├── power.py           3.6 KB  ← 战力引擎（原版权重）
├── battle.py         16.3 KB  ← 战斗（回合制）
├── quest_spawn.py     6.9 KB  ← 任务刷怪
├── world/           12 文件   ← P1 骨架（ticker/五层容器/守卫/行为树）
│   └── jstm_bridge.py 16.5 KB ← dormant 桥接层（4 行 attach 激活）
└── proto_defs.py    650.7 KB  ← 从 fields.json **生成**的协议常量
```

### 5.2 端口与接口
```
TCP  9000  ← 游戏协议
HTTP 8080  ← /DSH_ADMIN/*（17+ 动作）+ 探针上报
```
**管理动作**：`status / getlevel / setlevel / getassets / setassets / listitems /
giveitem / givegift / setequip / unequip / setheros / setjubaopen / setmissions /
cfglist / cfg / reset / reload / aoi / power`

### 5.3 ★ AOI（`aoi.py`，自研）

**设计思想来源**（★ **只有思想，无代码**）：
- Survive `common/aoi.c` —— **⚠ 该文件头内嵌 GPLv3 ⇒ 一行代码都不可复制**
- kongkongxiyou `aoi.md`（watcher/object 双注册 + 4 事件 + 双向差集）

**JSTM 化改造**：
| 项 | 参考项目 | **JSTM** |
|---|---|---|
| 形态 | C 模块 / Pomelo 插件 | **纯 Python 单进程** |
| 坐标 | 世界像素（硬编码 300） | **瓦片坐标，`tower_size` 可配** |
| 网络耦合 | 有 | **绝不碰 socket**（只产 `[(uid,event)]`） |
| MOB 移除 | remove 分支被注释 | ✅ **正常派发 leave** |
| 埋点 | 零 | ✅ `stats()` |

**核心 = 双向差集**：
```
new - old → 'enter' ；old - new → 'leave'
★ 移动必须两个都调：update_watcher（自己的视野）+ update_object（别人的视野）
  漏一个 ⇒ "别人看不到我移动"
```

### 5.4 ★ 寻路（`pathfind.py`，自研 + **JSTM 原创安全校验**）

| 组件 | 说明 |
|---|---|
| `MapGrid` | 通行数据（缺数据时 `allow_all=True`） |
| `find_path` | A\*（8 邻域 + octile 启发）；**先试 Bresenham 直线快路径**；**禁贴角穿缝** |
| `line_of_sight` | Bresenham 直线可达 |
| **`verify_path`** | **★ L1 路径校验**（相邻性 + 可走性 + 起点一致） |
| **`MoveRateLimiter`** | **★ L2 限流（令牌桶）** |

**★★ 为什么内建 L1/L2**（参考项目**全部缺失**）：
```
kongkongxiyou 的 handler.move 直接信任客户端上传的整条路径
Map.verifyPath 已定义但**全项目 0 处调用** ⇒ 可穿墙/瞬移/加速/拉怪
Survive 战斗层也零距离/角度/目标数校验
```
**⇒ JSTM 原则：客户端**永远不能提供路径**，只能提供**目标点**。**
⚠️ 但实测（Q2）JSTM 客户端**确实上传路径** ⇒ 故校验器分两套：
- `verify_path` ← 服务端生成的**稠密**路径
- `world/move.validate_client_move` ← 客户端的**压缩航点**（逐段 `line_of_sight`）

### 5.5 战斗（回合制）

**★ 前提裁决（用户确认）**：**JSTM 1.4.9 是回合制战斗**。

**链路**【已验证】：
```
CS_20002（发起）→ SC_20010（单位初始化，18 字段）
  → SC_20012（技能播放）/ SC_20013（伤害落点）
    → SC_20020（结果）→ CS_20021（客户端唯一主动上报）
```
**★ 真机客户端从不发 `CS_20011`/`CS_20014`** ⇒ **服务端必须自定节拍**（现 2.5 秒/回合自续期）。

**关键字段**【已验证】
```
SC_20013: round, round_wave, time, wave_no
        + magic_play[]   (10 字段，含 hit:i8 / hp_max / hp / is_target_die)
        + summon_play[]  (16 字段，★ 每回合全量重推)
        + order_list[]

★ magic_list[] = **buff 载体**（6 字段）:
    magic_bid:i32  → Config.SkillMagic
    change_hp:i32  → 每回合 HP 变化（DoT/HoT）
    duration:u8    → ★ 持续/剩余回合
    per:i16 / val:i16 / fold:u8（叠加层数）

⚠ specials[] **不是** buff 载体 ⇒ 是**伙伴外观通道**（全库仅 8 个 key）
```

**★ 结论：JSTM 战斗字段完整度远超全部 5 个参考项目**
（每回合单位重推 + buff 逐条上线 + 伤害绝对值与上限 + 多波次与阵法 + 观战/录像/自动战斗/客户端演算校验）。

**客户端容忍度**【已验证】：mock 全发**空** `magic_list`/`summon_play`/`order_list`，客户端**仍跑通 4 回合 + 结算** ⇒ **buff 可后置实现**。

---

## 六、★ 构建链

### 6.1 打补丁（注入探针/改服务器地址）
```powershell
python tools/patch_fake_login.py anzbao/jstm.apk patched/jstm_fakelogin_raw.apk `
       --base http://10.0.2.2:8080 --lua server/dsh_fake_login.lua
```

### 6.2 签名（APK 必须重签才能安装）
```powershell
$bt='D:\Android\SDK\build-tools\34.0.0'
& "$bt\zipalign.exe" -f -p 4 <in>.apk <aligned>.apk
& "$bt\apksigner.bat" sign --ks patched\dsh.keystore --ks-pass pass:123456 `
    --ks-key-alias dsh --key-pass pass:123456 `
    --v1-signing-enabled true --v2-signing-enabled true <aligned>.apk
```
**keystore**：`patched/dsh.keystore`（pass `123456`，alias `dsh`）

### 6.3 探针门禁（★ 必须过）
```powershell
node tools/lua-check/check.js server/dsh_fake_login.lua
```
**它能拦住 `cannot use '...' outside a vararg function` 之类的错** —— 这类错若不拦，会进 APK。

### 6.4 运行
```powershell
adb -s 127.0.0.1:16384 shell am force-stop com.shiyue.dldl.ewan.qihoo
adb -s 127.0.0.1:16384 shell am start -n com.shiyue.dldl.ewan.qihoo/org.cocos2dx.lua.AppActivity
Start-Sleep 65
adb -s 127.0.0.1:16384 shell input tap 2200 84        # ★ 只点一次
Start-Sleep 90
```

---

## 七、★ 调试手段

### 7.1 探针（`server/dsh_fake_login.lua`）
注入到客户端的 Lua 代码，通过 HTTP 上报运行时状态：
```lua
report('type', 'value')      -- → http.log 里的 ...&t=type&v=value
```
**已用它解决的关键问题**：
- 13 轮未解的 NPC 对话（最终用 `xpcall + debug.traceback` 抓调用栈）
- `sceneStart` 崩溃定位到 `skill_ctrl.checkSkillEnable → kHaveSkill`

### 7.2 日志
| 文件 | 内容 |
|---|---|
| `server/logs/tcp.log` | 游戏协议收发（`>> cmd=` / `<<`） |
| `server/logs/http.log` | 探针上报 + 管理接口请求 |
| `server/logs/server.log` | 服务端运行状态 |
| `server/logs/server_stderr.log` | **★ 异常（应为 0 字节）** |

### 7.3 性能基准
```powershell
python tools/bench_server.py     # 各命令延迟
python tools/test_concurrent.py  # 并发
```
**实测**：中位 **10.8~16.9 ms**；并发 200/200 成功；最大 1030 ms（Python + GIL + SQLite 串行）。

### 7.4 数据完整性校验
```python
# 无无效 bid / 无 item_id 重复 / 无 None 字段
python tools/inspect_db.py
```

---

## 八、★ 已知技术限制

| 限制 | 说明 |
|---|---|
| **原版服务端数据不可得** | 战斗数值/怪物属性/限时任务存在**取证天花板** |
| **客户端 bug 无法从服务端根治** | 如 `setSceneInfo` 写 R1 读 R0 |
| **未解子表** | 含 `D\|Dsc*\|` 的 CMD 按纪律不实现 |
| **单进程并发尾部** | 最大 1030 ms |
| **`TcpHandler.cfg` 类属性** | 全连接共享 ⇒ 真机多角色验证受阻 |
| **Python 广播能力弱** | 无网关分层（参考项目有多进程，但我们**不需要**） |

---

## 九、参考项目技术对照（仅架构，**代码不可复制**）

| 项目 | 技术栈 | 对 JSTM 的价值 |
|---|---|---|
| **Survive**（207.7 MB / 2618 文件） | C + Lua（`distri.lua`），aoi.c/astar.c | **AOI/寻路唯一可读的设计** + 属性三条铁律 |
| **CXEngine = YZXY/原罪西游**（14.8 MB / 501） | C++ + Lua，回合制 | 单一真源 + 代码生成、`stub[PTO_*]` 分发 |
| **MahatmaComeBack / 大圣归来**（18.2 MB / 136） | C# + MySQL | 🔴 **GPL-3.0**；`gametable.sql` 仅 1 表 11 字段 |
| **ChivalrousMan / 侠客行**（51.2 MB / 1411） | C++ + 直连 MySQL | 五段式分层 + 反推 **5 表 33 字段** |
| **kongkongxiyou / 空空西游**（331.8 MB / 22486） | Node.js + Pomelo | ★ 场景五层骨架 + **作者已验证"多进程→准单体"** |

**★ 最关键的验证**：kongkongxiyou 作者**自己从多进程退回了准单体** ⇒ **免费验证了 JSTM 单进程路线的合理性**。

---

## 十、术语表

| 术语 | 含义 |
|---|---|
| **AOI** | Area of Interest，兴趣区域（谁看得见谁） |
| **CS / SC** | Client→Server / Server→Client |
| **D\|Dsc*\|** | 未解出的嵌套子表标记（**不实现**） |
| **AttrLen** | 属性系统总数（= 64） |
| **AttrPower** | 每属性对"战力"的贡献权重 |
| **L1 / L2** | 路径校验 / 限流（JSTM 原创） |
| **fail-open** | 校验异常时**放行**（避免困死玩家） |
| **dormant** | 已交付但未激活（需显式 attach） |
