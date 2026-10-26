# -*- coding: utf-8 -*-
"""**配置解构器**：把"超大嵌套配置"（`config_rune_data` / `config_invest` 那一类）还原成 JSON。

## 为什么需要它

本项目此前的 `tools/extract_config_table.py` 只能处理**平铺的数字键表**，
对下面这类**具名嵌套表**无效（输出 0 条）：

    Config = {
        LuckyGoldConst = { ... },
        TipsConstant   = { ... },
        LimitConstant  = { normal = {...}, eyou = {...}, tw = {...}, en = {...} },
        ChargeReturnGolds = { charge_return_not_list = {...} },
    }

`config_invest`（3.2KB）与 `config_rune_data`（**1.2MB / 20108 张表**）都是这种形状。

## 解构原理（**已在 `config_holiday_util.luac` 上自洽验证**）

LuaJIT 对具名表构造发出的是 `TDUP`/`TNEW` + `TSETS` 的组合，语义为：

    TDUP  A=r  D=t      ⇒ R[r] = 模板 #t（一个 TableConst）
    TNEW  A=r           ⇒ R[r] = {}（新空表）
    GGET  A=r  D=g      ⇒ R[r] = 全局 #g（这里就是 `Config` 本身）
    TSETS A=x  B=y  C=k ⇒ **t[y][k] = t[x]**   ← ★ 值在 A、容器在 B、键在 C

（`x` 是值、`y` 是容器 —— 这一点用 `config_holiday_util` 的字节码逐条对齐确认过：
 `TNEW R1` 之后 `TSETS A=1 B=0 C=1['LuckyGoldConst']` 表示 `Config['LuckyGoldConst'] = R1`。）

`kidx(pt, i)`（`tools/luajit_dis.py`）完成"常量索引 → 实际对象"的映射，本项目已全量验证过。

用法：
    python tools/config_deconstruct.py <x.luac> [out.json] [--top 20] [--depth 3]
    python tools/config_deconstruct.py _tmp_cfg/config_invest.luac
"""
import argparse
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from luajit_bc import ChildRef, TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def _key_repr(k):
    """dict 的键的短表示。

    ⚠ 实战暴露：`TSETV` 的**键也可能是一个 `TableConst`**（例如 `t[某个表] = 值`），
      第一版直接 `str(key)` ⇒ 键变成 `"TableConst(array=[], hash=[('name','风云'),…])"`
      这种几百字符的长串（`config_rune_data` 里出现了）。
      ⇒ 优先取该表里的 `id/bid/lev/rune_id` 作为键，取不到就退化成 `TC#<对象号>`。
    """
    if isinstance(k, TableConst):
        h = dict(k.hash or [])
        for cand in ('id', 'bid', 'lev', 'rune_id', 'type'):
            if cand in h and not isinstance(h[cand], TableConst):
                return '%s' % h[cand]
        return 'TC#%d' % id(k)
    if isinstance(k, ChildRef):
        return 'ChildRef#%d' % k.index
    return str(k)


def to_jsonable(v, depth=0, maxdepth=12):
    """把 TableConst / ChildRef 递归转成可 JSON 化的结构。

    ⚠ 必须**对 dict/list 也递归** —— 第一版漏了这一支，导致 `Config` 的值
      （`deconstruct` 建出来的 dict，里面装的是 `TableConst`）原样透传，
      最后在 `json.dumps` 上炸 `TypeError: Object of type TableConst is not JSON serializable`。
    """
    if depth > maxdepth:
        return '…(超深)'
    if isinstance(v, TableConst):
        arr = [to_jsonable(x, depth + 1, maxdepth) for x in (v.array or [])]
        h = {}
        for k, val in (v.hash or []):
            h[_key_repr(k)] = to_jsonable(val, depth + 1, maxdepth)
        # `array` 里的 None 是 Lua 的"洞"，保留以维持索引语义
        return {'array': arr, 'hash': h} if h and arr == [] else (
            h if h and not [x for x in arr if x is not None] else arr or h)
    if isinstance(v, ChildRef):
        return 'ChildRef#%d' % v.index
    if isinstance(v, dict):
        return {_key_repr(k): to_jsonable(x, depth + 1, maxdepth) for k, x in v.items()}
    if isinstance(v, list):
        return [to_jsonable(x, depth + 1, maxdepth) for x in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def _set(cont, key, val):
    """往"容器"里写一个键 —— ★ **容器可能是 `TableConst`（模板对象）**。

    这是本工具**最重要的一处修复**（用 `tools/_trace_decode.py` 定位）：
    配置里的具名子表是通过 `TDUP` 拿到**模板**后**直接往模板上挂键**的，例如

        7  TDUP  A=2 D=2        ; R2 = 模板 {name:'登录基金', is_charge:0}
        8  TNEW  A=3            ; R3 = {}（cost 容器）
        9  TDUP  A=4 D=3        ; R4 = {'gold',1000}
        10 TSETB A=4 B=3 C=1    ; R3[1] = R4
        11 TSETS A=3 B=2 C=4    ; ★ R2['cost'] = R3 —— R2 是**模板**，不是 dict！

    第一版只认 `dict` 容器 ⇒ 第 11 行被**静默跳过** ⇒ 所有以模板为容器的内容
    （`cost`、`LevInvest` 深层、`RuneExchange`…）**全部丢成空 `{}`**。
    ⇒ 现在两种容器都写：`dict` 直接赋值；`TableConst` 往它的 `hash` 列表追加。
    """
    if isinstance(cont, dict):
        cont[key] = val
        return True
    if isinstance(cont, TableConst):
        if cont.hash is None:
            cont.hash = []
        cont.hash.append((key, val))
        return True
    return False


def deconstruct(path, proto_index=0):
    """返回 `{顶层键: 解构后的值}`。

    ★ 关键修正（第一版错在这里）：`GGET/GSET` 操作的是**表的对象引用**，不是"名字标记"。
      配置文件开头那段

          0  GGET A=0 D=0   ; R0 = Config
          1  IST  A=0       ; if R0 then
          2  JMP  …
          3  TNEW A=0       ; R0 = {}
          4  GSET A=0 D=0   ; Config = R0      ← `if not Config then Config = {} end`

      说明 R0 与全局 `Config` 是**同一个对象**；之后每次 `GGET A=0 D=0` 都只是把它再读出来。
      ⇒ 必须按引用传递，否则后面的 `TSETS B=0` 找不到容器、整棵树挂不上（第一版就把
        `Config` 输出成了一个空表）。
    """
    r = parse_file(path)
    if not r.protos:
        return {}
    pt = r.protos[proto_index]
    regs = {}
    gvars = {}      # 全局名 → 对象（按引用）
    _pc = 0
    _ist = False          # ★ R193：`IST` 的结果（供紧随的 `JMP` 用）
    _rets = []            # ★ R194：`RET1`/`RET0` 的返回值（有的 chunk 只建表到寄存器、无 GSET）
    while _pc < len(pt.bc):
        ins = pt.bc[_pc]
        op = ins & 0xff
        a = (ins >> 8) & 0xff
        b = (ins >> 24) & 0xff
        c = (ins >> 16) & 0xff
        d = (ins >> 16) & 0xffff
        name = OPS[op] if op < len(OPS) else 'OP_%d' % op

        if name == 'TNEW':
            regs[a] = {}
        elif name == 'TDUP':
            regs[a] = kidx(pt, d)
        elif name == 'GGET':
            # ★ 按**引用**取全局值（同一个 dict 对象）
            regs[a] = gvars.get(str(kidx(pt, d)))
        elif name == 'GSET':
            gvars[str(kidx(pt, d))] = regs.get(a)
        elif name == 'TSETS':
            # 语义：t[B][C] = t[A]（B 是容器、A 是值、C 是键）—— 与样本逐条对齐确认
            # ★ 容器可能是 `TableConst` ⇒ 走 `_set`
            _set(regs.get(b), kidx(pt, c), regs.get(a))
        elif name == 'TSETB':
            # ★★★★ R158：**设表字段（字节键）** —— `reg[B][C] = reg[A]`
            #   ★ 本工具一直没处理它，而 **`config_item` 里它出现 27119 次**！
            #   ⇒ 这正是"18 个核心配置（`config_item`/`config_skill`/`config_mon_data`/
            #     `config_role_attribute` …）解出来是**空表**"的根因。
            #   a/b/c 的取法沿用上面 `TSETS` 的约定（`b`=容器、`a`=值、`c`=键）。
            _set(regs.get(b), c, regs.get(a))
        elif name == 'TSETV':
            # ★★★★ R158：**设表字段（寄存器键）** —— `reg[B][reg[C]] = reg[A]`
            #   （`config_item` 里出现 3609 次）
            _set(regs.get(b), regs.get(c), regs.get(a))
        elif name == 'TSETR':
            # ★★★★ R158：**设表字段（引用键）** —— `reg[B][t[C]] = reg[A]`
            _set(regs.get(b), kidx(pt, c), regs.get(a))
        elif name == 'TGETB':
            # ★ R158：读表字段（字节键）—— `reg[A] = reg[C][B]`（LuaJIT 的变体）
            _t = regs.get(c)
            try:
                regs[a] = _t.get(b) if isinstance(_t, dict) else None
            except Exception:
                regs[a] = None
        elif name == 'TGETV':
            # ★ R158：读表字段（寄存器键）—— `reg[A] = reg[B][reg[C]]`
            _t = regs.get(b)
            try:
                regs[a] = _t.get(regs.get(c)) if isinstance(_t, dict) else None
            except Exception:
                regs[a] = None
        elif name == 'KSTR':
            # ★★ R108：**把字符串常量放进寄存器** —— 键可能来自这里。
            #   `config_rune_data` 里有 KSTR(3) / KSHORT(253) / KNUM(33)，
            #   而本工具此前**完全没处理它们** ⇒ 键寄存器读到 `None`
            #   ⇒ 写入落到"None 键"上（这就是那段"非标量键 type=NoneType"
            #     插桩输出揭示的根因，也是第 8 个顶层键名字丢失的原因）。
            regs[a] = kidx(pt, d)
        elif name == 'KSHORT':
            regs[a] = d                    # 16 位整数常量 → 寄存器
        elif name == 'KNUM':
            _pos = len(pt.knum) - 1 - d
            regs[a] = pt.knum[_pos] if 0 <= _pos < len(pt.knum) else None
        elif name == 'KCDATA':
            regs[a] = kidx(pt, d)
        elif name in ('KPRI', 'KNIL'):
            regs[a] = None                 # nil / true / false：本工具无需区分
        elif name == 'TSETB':
            # ★ R106：**数字字面量键**的写入。`config_invest` 用了 110 次、`config_rune_data` 19953 次。
            #   语义与 `TSETS` 同理（容器在 B、值在 A），键是 C 的字面量：t[B][C] = t[A]
            #   （用已知答案验证过：`LevDays` 应为 `[None,25,35,45,55,65,75]`）
            _set(regs.get(b), c, regs.get(a))
        elif name == 'TSETV':
            # t[B][t[C]] = t[A] —— 键也来自寄存器；按同族口径取"容器在 B、键在 C、值在 A"
            _k = regs.get(c)
            _set(regs.get(b), _k if isinstance(_k, (str, int)) else _key_repr(_k),
                 regs.get(a))
        elif name == 'IST':
            # ★★★ R193：**测试寄存器**（LuaJIT `if X then` 的前半）——
            #   结果供**紧随的 `JMP`** 使用：真 ⇒ 跳过若干条。
            #   ★ 这是 `config_item` 里 `if not Config then Config = {} end` 惯用法的前半；
            #     不处理它 ⇒ `TNEW`/`GSET` 会**无条件执行**
            #     ⇒ 把已挂好的 `Config['ItemData']`（**1117 个物品**）**覆盖成空表**。
            _ist = bool(regs.get(a))
        elif name in ('ISNEN', 'ISNE', 'ISEQN', 'ISEQ', 'ISLT', 'ISGE', 'ISLE', 'ISGT',
                      'ISF', 'ISTC', 'ISFC'):
            # ★★★ R194：**其它"测试"指令**（`config_skill` 用了 **`ISNEN` 8700 次**）。
            #   ★ 语义各不相同，但**在本工具的"线性模拟"里**统一按"**不跳**"处理 ——
            #     目的不是"精确模拟控制流"，而是 **`pc` 不因未识别的指令而卡住/乱跳**，
            #     从而让后续的 `TDUP`/`TSETB` **把数据全部塞进容器**。
            #   ★ 实测：`config_skill` 的 proto0 因此从 **2 字符 → 全部技能**。
            _ist = False
        elif name == 'JMP':
            # ★★★ R193：**条件跳转** —— 目标 = `pc + 1 + (d - 0x8000)`。
            #   ★ 仅当上一条"测试"为真时跳（否则顺序执行，正是 `if not X then` 的语义）。
            if _ist:
                _pc = _pc + 1 + (d - 0x8000)
                continue
        elif name in ('RET0', 'RET1'):
            # ★★★ R194：**返回** —— `config_skill` 的 proto0 有 **8700 个 `RET1`**
            #   （每个"if 分支"的提前返回）。
            #   ★ 若在此 `return`，就只能拿到第 1 条数据（实测 2 字符）；
            #   ★★ **配置 chunk 的语义是"建表"，不是"函数调用"** ⇒
            #      **跳过返回、继续线性执行** ⇒ 8700 条技能全部落进容器 ✓
            #   ★★★ 并且：**把"返回值"（`regs[a]`）也收进结果** ——
            #      有的配置 chunk（如 `config_skill` proto0）**只建表到寄存器、最后 `RET1` 返回**，
            #      **根本没有 `GSET`** ⇒ 只看 `gvars` 会得到空表。
            #   ★ 安全性：外层 `while _pc < len(pt.bc)` 保证不会越界。
            _ret = regs.get(a)
            if isinstance(_ret, dict) and _ret:
                _rets.append(_ret)
        _pc += 1
    # ★★★ R194：**总是**把 `RET1`/`RET0` 的返回值并进结果 ——
    #   （第一版写成 `if not gvars and _rets`，而 `config_skill` proto0 的 `gvars` 非空
    #     ⇒ **跳过合并** ⇒ 仍只 2 字符）
    if _rets:
        for _rr in _rets:
            if not isinstance(_rr, dict):
                continue
            for _rk, _rv in _rr.items():
                # ★ 跳过以 `__` 开头的键（`__index` 等是**元表字段**，不是配置数据）
                if isinstance(_rk, str) and _rk.startswith('__'):
                    continue
                gvars.setdefault(_rk, _rv)
    return gvars


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('luac')
    ap.add_argument('out', nargs='?')
    ap.add_argument('--proto', type=int, default=0)
    ap.add_argument('--top', type=int, default=20, help='打印前 N 个顶层键')
    args = ap.parse_args()

    res = deconstruct(args.luac, args.proto)
    j = {k: to_jsonable(v) for k, v in res.items()}
    print('顶层键 %d 个：' % len(j))
    for i, k in enumerate(j):
        v = j[k]
        n = len(v) if isinstance(v, (list, dict)) else '标量'
        print('  %-28s %s 项  %s' % (k, n, json.dumps(v, ensure_ascii=False)[:70]))
        if i + 1 >= args.top:
            print('  …（其余 %d 个省略）' % max(0, len(j) - args.top))
            break
    if args.out:
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(j, f, ensure_ascii=False, indent=1)
        print('\n已写出 %s' % args.out)


if __name__ == '__main__':
    main()
