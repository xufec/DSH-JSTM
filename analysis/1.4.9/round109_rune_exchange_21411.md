# R109：`RuneExchange` 正名 + `21411`（魂星兑换）落地

> 接 R108。**最后那一步修完了**：`RuneExchange` 正名成功，顶层键 **8 → 10**，
> 并立刻用它实现了 `21411`。
> **时间**：2026-09-29 04:05 – 04:35。

---

## 一、★ 最后一步的根因：**没处理"把常数放进寄存器"的指令**

R108 修完 `_set()` 后，`config_rune_data` 的第 8 个顶层键仍是 `"{'50': {1: …}}"` 这样的长串。

**定位手段**：在 `_key_repr()` 里插桩，打印"非标量键"的真实类型：

```
[debug] 非标量键 type=NoneType repr=None
[debug] 非标量键 type=NoneType repr=None
…
```

⇒ **键的 type 是 `None`！** 而 `config_rune_data` 的 opcode 诊断是：

```
未处理: {'TSETB': 19953, 'TSETV': 289, 'KSHORT': 253, 'KNUM': 33, 'KSTR': 3, …}
                                                  ^^^^^^^^^^^^^^
```

⇒ **`KSHORT`(253) / `KNUM`(33) / `KSTR`(3) 这些"把常数放进寄存器"的指令，解构器一条都没处理**
⇒ 键寄存器读到 `None` ⇒ 所有以它们为键的写入都落到无名键上。

### 修法

在 `deconstruct()` 的指令分支里补上：

```python
elif name == 'KSTR':   regs[a] = kidx(pt, d)      # 字符串常量 → 寄存器
elif name == 'KSHORT': regs[a] = d                # 16 位整数常量 → 寄存器
elif name == 'KNUM':   regs[a] = pt.knum[len(knum)-1-d]
elif name == 'KCDATA': regs[a] = kidx(pt, d)
elif name in ('KPRI', 'KNIL'): regs[a] = None
```

### 效果：顶层键 **8 → 10**，`RuneExchange` 正名

```
[0] RuneStatic     [1] RuneContent   [2] RuneOpenLimit1  [3] RuneBaseExp
[4] RuneOpenLimit  [5] RuneGridOpen  [6] RuneBase
[7] RuneExchange   ← ★★★ 正名成功       [8] RuneTarget   [9] RuneHeroDesc
```

★ 与反汇编 `strings(16)` 里的名字**全部对应上了**（`RuneBase`/`RuneExchange`/`RuneTarget`/`RuneHeroDesc`/`RuneContent`/`RuneStatic`/`RuneGridOpen`/`RuneOpenLimit`/`RuneOpenLimit1`/`RuneBaseExp`）。

---

## 二、`RuneExchange` 的内容（实测）

```
RuneExchange: 20 项
  [1] {name:"巨门", rune_id:21403, id:1, count:0, assets:{1:[null,"rune_chip",4500]}}
  [2] {name:"贪狼", rune_id:21413, id:2, count:0, assets:{1:[null,"rune_chip",4500]}}
  [3] {name:"太白", rune_id:21423, id:3, count:0, …}
  [4] {name:"武曲", rune_id:21433, id:4, …}

RuneBase: 124 项（每个符文 1..50 级，含 effect_desc / assets / effect）
  [21400] {1: {name:"巨门", effect_desc:"生命+406", lev:1, rune_id:21400,
               assets:{1:[null,"rune_exp",134]}, …}}
```

⇒ **兑换所需物品（`rune_chip` × 4500）与属性曲线全都有出处**。

---

## 三、`21411` 的逐字段映射与实测

`CS_21411{count_type:u8, color:u8}` → `SC_21411{code, msg, coin_count, rest_times, Items:table(bid,num,exchange)}`

| 协议字段 | 来源 | 依据 |
|---|---|---|
| `Items[].bid` | `RuneExchange[].rune_id` | ★ 配置（20 条）|
| `Items[].num` | `1` | 配置无"数量"字段 ⇒ 保守取 1 |
| `Items[].exchange` | `RuneExchange[].count` | ★ 配置原值（本服 0 = 未兑换，**真话**）|
| `code` / `msg` | `1` / `''` | 同族成功约定 |
| `coin_count` / `rest_times` | `0` | **语义未取证 ⇒ 不编造** |

**实测（门禁权威解析器）**：

```
SC_21411 len=187 消耗=187 err=None ⇒ PASS
<< 21411 SC_21411 Items=20（RuneExchange）(193 bytes)
```

★ 并把 `21411` 从 **`_UNSUPPORTED_ACTION_CMDS`（"未开放"集合）移出** ——
它原本回 `code=0 未开放`，不移出会**遮蔽**新实现（R103 的门禁已能当场抓到这类问题）。

---

## 四、全量验证

| 项 | 结果 |
|---|---|
| 六道门禁 | lint **0 遮蔽**（专用 **196** / 默认 50 / 未开放 **20**）/ CS 2463-0 / SC 静态 **70+1空-0** / SC 在线 **70-70** / 专用 **76-76** / 门禁 E **PASS** |
| 回归（12 项） | 全 PASS |
| 环境 | `python=1`、`9000 监听=1`、`stderr=0B` |

---

## 五、产出物

| 文件 | 说明 |
|---|---|
| `tools/config_deconstruct.py` | 补 `KSTR`/`KSHORT`/`KNUM`/`KCDATA`/`KPRI`/`KNIL`（**最后一步的根因**）|
| `tools/_find_table_keys.py` | **新增**：定位"键解析成非标量"的写入（本轮定位手段之一）|
| `_tmp_cfg/config_rune_dec.json` | 顶层键 8→10，`RuneExchange` 正名 |
| `server/_rune_cfg.json` | 落盘 3 张表（`RuneExchange`/`RuneStatic`/`RuneBase`，1.7MB）|
| `server/mock_server.py` | 新增 `rune_cfg()` / `rune_exchange_rows()` + `21411` 处理器；从"未开放"集合移出 |
| `tools/_fix_r109_rune_exchange.py` | 插入脚本 |
| `server/mock_server.py.bak_r109` | 改前备份 |
| `analysis/1.4.9/round109_rune_exchange_21411.md` | 本报告 |

---

## 六、一句话

> **最后一步的根因是：解构器没处理 `KSTR`/`KSHORT`/`KNUM` 这些"把常数放进寄存器"的指令**
> ⇒ 键寄存器读到 `None` ⇒ 写到无名键上（插桩一句 `type=NoneType` 就暴露了）。
> 补上后 `config_rune_data` 顶层键 **8 → 10**、**`RuneExchange` 正名**，
> 并立刻用它把 **`21411`（魂星兑换，真机发过 15 次）** 做出来了：
> **20 个真实兑换条目**，`bid` 与 `exchange` 都来自配置，实测 `len=187 消耗=187 err=None ⇒ PASS`。
> 解构器这条线至此闭环：**R106 建工具 → R107 解出投资 → R108 修容器 → R109 正名 + 落地魂星兑换**。
