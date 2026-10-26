# 读取游戏资源 + 后台管理扩充（第二轮）

> 用户要求：**读取游戏中的各种资源物品，增加后台管理功能（dsh_admin.bat）。**

---

## 一、★ 关键发现：游戏里有 **347 张配置表**

```
config_skill.luac            3,032,592    技能
config_rune_data.luac        1,229,514    符文
config_skill_magic.luac      1,050,856    技能魔法
config_mon_data.luac           857,309    怪物
config_item.luac               838,442    物品   （已提取 3535 条）
config_mission.luac            504,437    任务   （已提取 846 条）
config_shenqi.luac             366,477    神器
config_item_gift.luac          292,151    礼包   （已提取 496 个）
config_npc.luac                140,717    NPC    （643 条）
config_partner_base.luac        85,065    伙伴   （285 条）
config_buff_data.luac           64,910    Buff   （365 条）
...
共 347 张
```

**⇒ 与其一张张抠，不如做**通用读取器** —— 这才对得上"读取各种资源"。**

---

## 二、新增：通用配置表读取器 `tools/extract_config.py`

**原理（不是猜的，已在两张表上验证）：**
- 记录的**字段顺序**可从 `proto[0]` 的 **`TGETB` / `TSETS` 配对**动态推出
- 若无该配对，退回**位置数组** `[None, a, b, c]` 或**哈希** `{bid: …}`

**用法：**
```bash
python tools/extract_config.py list                 # 列出 347 张表
python tools/extract_config.py field config_npc     # 打印字段顺序
python tools/extract_config.py peek  config_npc 5   # 预览 5 条
python tools/extract_config.py dump  config_npc     # 导出 JSON
```

**实测：**
```
config_item          3535 条（字段顺序 bid,name,type,lev,bind_type,...）✓
config_npc            643 条（含 name/talk/type/dir…）✓
config_partner_base   285 条（含 name='唐舞桐'/score=24490/career…）✓
config_buff_data      365 条 ✓
```

---

## 三、后台新增 2 个动作（服务端 `/DSH_ADMIN` 从 15 → **17**）

| 动作 | 作用 |
|---|---|
| **`/cfglist`** | 列出 APK 里**全部 347 张配置表**（名称 + 大小） |
| **`/cfg?name=&kw=&limit=`** | **读任意配置表**，支持关键词搜索 |

**实测：**
```
/cfglist -> 347 张表
/cfg?name=config_partner_base&kw=唐舞桐 -> total=285 shown=1
    {"key":"33100","row":{"name":"唐舞桐","score":24490,"career":3,...}}
/cfg?name=config_npc&limit=2 -> total=643 shown=2
    {"key":"10010","row":{"name":"玄老","type":1,"talk":"鸡腿……我的鸡腿哪去了？"}}
```

**⇒ 后台现在能**直接读游戏里的任何资源表**，不用再写死提取脚本。**

---

## 四、`dsh_admin.ps1` 菜单新增 `[70]~[74]`

```
[资源表]  ★ 直接读取 APK 里的 347 张配置表
[70] 列出全部配置表
[71] 读某张表（可按关键词搜）
[72] 搜物品   [73] 搜 NPC   [74] 搜 伙伴
```

**⇒ 菜单分组：**
```
[角色] [1]~[8] ｜ [物品] [10]~[12] ｜ [装备] [20]~[21]
[伙伴/聚宝盆] [30]~[31] ｜ [任务] [40]
[资源表] [70]~[74] ｜ [重置/热重载] [50]~[60]
```

---

## 五、★ 本轮修掉的两个自造 bug（如实）

| # | 现象 | 根因 | 修法 |
|---|---|---|---|
| 1 | `/cfg` 返回 **500** | 我把 `OPS[w&0xff]` 改成了 `OPS.get(...)`，但 **`OPS` 是 `list` 不是 `dict`** | 改回 `OPS[w & 0xff]` |
| 2 | `luajit` 工具未导入 | 服务端模块级用了 `OPS`/`kidx` 却没导入 | 在模块顶部 `sys.path` + `from luajit_dis import OPS, kidx`（失败时降级不崩） |

**⇒ 两个都是**靠实测发现**的（`/cfg` 报 500 → 查 stderr → 手动跑一遍逻辑定位）—— 没有靠猜。**

---

## 六、当前状态与能力总览

```
/DSH_ADMIN 动作（17）：
  角色   getlevel / setlevel / getassets / setassets / status
  物品   listitems / giveitem / givegift
  装备   setequip / unequip
  伙伴   setheros           聚宝盆 setjubaopen
  任务   setmissions
  资源表 cfglist / cfg      ★ 本轮新增
  维护   reset / reload

dsh_admin.ps1  10572 B（UTF-8 带 BOM，PowerShell 5.1 语法 OK）
服务端 8080/9000 运行中 ｜ stderr 0 字节
```

---

## 七、仍未做（沿用清单）

| 项 | 说明 |
|---|---|
| **礼包打开失败** | `30010`/`33001` 内容不在 `ItemGift`；**现在可以用 `/cfg?name=config_item_gift` 直接查证** |
| **聚宝盆奖池** | 占位值；**可用 `/cfg` 找原版奖池表** |
| **伙伴商店兑换** | 未定位协议 |
| **装备↔仓库移动** | 安全拒绝中（曾丢物品） |
