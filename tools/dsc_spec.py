"""从 1.4.9 `cmd_resolve_*.luac` 还原全部 `Dsc*` 嵌套子结构定义。

## 判据（两条独立证据，均来自 1.4.9 APK 本体）

子结构没有 `name__fmt` 数组，只有「读取器」原型：

    proto#15 (Dsc20010animate_res 读取器)
      9  TGETS A=7 B=1 C=0 ; ['ReadFMT']
     10  KSTR  A=8 D=2    ; 'HsCC'       <- 整结构的格式串
     11  CALL  A=7 D=1282
     15  TDUP  A=13 D=5   ; {}
     16  TSETS A=7  B=13 C=6 ; ['ant_id']
     17  TSETS A=8  B=13 C=7 ; ['ant_val']
     18  TSETS A=9  B=13 C=8 ; ['ent_lev']
     19  TSETS A=10 B=13 C=9 ; ['dis_method']

### 证据 ①：`baseprotocalstruct.luac` 的 Encode（proto#7）

    ipairs(self.m_value_names) → 逐个 append(self.m_value_src[name]) 到 m_values
    → writer:WriteFMT(self.m_format, unpack(m_values))

⇒ **`m_value_names[i]` 与格式串第 i 个字符按位置配对**，
   `WriteFMT(fmt, v1, v2, ...)` 中 vt 与 formatt 一一对应。
   因此「名字顺序」= 「线序」，并且两者都是**顺序**（不是逆序）。

### 证据 ②：同一字段名在两个地方的交叉对齐

| 位置 | 内容 |
|---|---|
| `Dsc20010skills` 读取器 | 名字（TSETS 顺序）`bid, step, last_use, cd`，格式串 `ICHH` |
| `SC_20012.cooldown` **内联** spec | `bid@I##last_use@H` |

两处的 `bid` / `last_use` 类型必须一致。只有**不反转**才能对上：
`bid`=I(uint32)、`last_use`=H(uint16)。若反转则会得到 `bid`=uint16、
`last_use`=uint8，与 `SC_20012.cooldown` 的内联 spec **直接冲突**。

### 证据 ③：16 字段全中

`Dsc20013summon_play` 读取器（TSETS 顺序）与 `SC_20013.summon_play` 的
**内联** spec `id@H##rid@I##srv_id@s##name@s##lev@H##sex@C##career@H##pos@C##group@C##hp_max@I##hp@I##anger@I##is_auto@C##...`
逐字段、逐类型完全一致（16/16）。反转则 16 个全错。

⇒ **结论：读取器 TSETS 顺序 = 线序（不反转）。**
   `protocol/manual.md` 与 `protocol/fields.json` 里 `Dsc*` 段的字段顺序
   是**反的**（顶层消息的内联 `name__type` 数组那部分是对的，不受影响）。
   本工具的结论以本判据为准。

用法：
    python tools/dsc_spec.py                 # 全部列出
    python tools/dsc_spec.py Dsc20012        # 只列名字含该串的
    python tools/dsc_spec.py --file 200      # 只看某个 cmd_resolve 号段
"""
import os
import re
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import TableConst, parse_bytes  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

APK_149 = os.path.join(os.path.dirname(HERE), 'anzbao', 'jstm.apk')

FMT2TYPE = {'C': 'uint8', 'H': 'uint16', 'I': 'uint32',
            'c': 'int8', 'h': 'int16', 'i': 'int32', 's': 'string'}


def tokenize(fmt):
    """把格式串切成 token：单字符类型 或 D|Name| 复合。"""
    toks = []
    i = 0
    while i < len(fmt):
        if fmt[i] == 'D' and i + 1 < len(fmt) and fmt[i + 1] == '|':
            j = fmt.find('|', i + 2)
            if j < 0:
                toks.append(fmt[i:])
                break
            toks.append(fmt[i:j + 1])
            i = j + 1
        else:
            toks.append(fmt[i])
            i += 1
    return toks


def structs_in(data):
    """返回 [(fmt, [names_in_wire_order], proto_index)]"""
    r = parse_bytes(data)
    out = []
    for i, pt in enumerate(r.protos):
        fmts = [s for s in pt.strings
                if re.fullmatch(r'([CHIchis]|D\|[A-Za-z0-9_]+\|){2,}', s or '')]
        if not fmts:
            continue
        # 取 token 数最多的格式串（`'H'` 只是探测用的）
        fmt = max(fmts, key=lambda s: len(tokenize(s)))
        toks = tokenize(fmt)
        # TSETS 目标名，按字节码顺序
        names = []
        for w in pt.bc:
            op = OPS[w & 0xff] if (w & 0xff) < len(OPS) else ''
            if op == 'TSETS':
                v = kidx(pt, (w >> 16) & 0xff)
                if isinstance(v, str):
                    names.append(v)
        if not names or len(names) != len(toks):
            continue
        # ★ 线序 = TSETS 顺序本身（**不反转**）。见模块头注的判据。
        out.append((toks, names, i))
    return out


def main():
    argv = sys.argv[1:]
    only_file = None
    if '--file' in argv:
        k = argv.index('--file')
        only_file = argv[k + 1]
        argv = argv[:k] + argv[k + 2:]
    want = [a for a in argv if not a.startswith('--')]
    z = zipfile.ZipFile(APK_149)
    names = sorted(n for n in z.namelist()
                   if n.startswith('assets/src/config/protocal/cmd_resolve_')
                   and n.endswith('.luac'))
    total = 0
    for n in names:
        if only_file:
            m = re.search(r'cmd_resolve_(\d+)\.luac', n)
            if not m or m.group(1) != only_file:
                continue
        try:
            ss = structs_in(z.read(n))
        except Exception as e:
            print('!! %s: %r' % (n, e))
            continue
        if not ss:
            continue
        for fmt, fnames, pi in ss:
            flat = ''.join(fmt)
            if want and not any(w in ' '.join(fnames) or w in flat for w in want):
                continue
            total += 1
            print('%-34s proto#%-4d fmt=%-30s' % (os.path.basename(n), pi, flat))
            for nm, ch in zip(fnames, fmt):
                if ch.startswith('D|'):
                    t = 'TABLE(%s)' % ch
                else:
                    t = FMT2TYPE.get(ch, ch)
                print('      %-22s %s' % (nm, t))
    print('共 %d 个子结构' % total)


if __name__ == '__main__':
    main()
