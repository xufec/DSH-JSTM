"""通用配置表读取器：读取 1.4.9 里**任意** `assets/src/config/*.luac`。

设计依据（不是猜的）：
  - 各配置表都是「表名 + 若干条记录」的 LuaJIT 字节码
  - 记录的字段顺序，可从 **proto[0] 的 `TGETB`/`TSETS` 配对**动态推出（已在
    `config_item.luac` / `config_item_gift.luac` 上验证过两次）
  - 若无 `TGETB/TSETS` 配对（如 `config_item_gift`），则退回**位置数组** `[None, a, b, c]`

用法：
    python tools/extract_config.py list                  # 列出全部配置表 + 大小
    python tools/extract_config.py field <name>          # 打印某表的字段顺序
    python tools/extract_config.py dump  <name> [out]    # 导出某表为 JSON
    python tools/extract_config.py peek  <name> [n]      # 预览前 n 条
"""
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

PREFIX = 'assets/src/config/'


def open_apk(apk=None):
    apk = apk or r'anzbao\jstm.apk'
    return zipfile.ZipFile(apk)


def entry(z, name):
    if not name.endswith('.luac'):
        name += '.luac'
    p = PREFIX + name
    if p not in z.namelist():
        raise SystemExit('未找到配置表: %s' % name)
    return parse_bytes(z.read(p))


def field_order(r):
    """从 proto[0] 的 TGETB/TSETS 配对推出字段顺序。"""
    if not r.protos:
        return []
    pt = r.protos[0]
    order, pending = [], False
    for w in pt.bc:
        op = OPS[w & 0xff]
        if op == 'TGETB':
            pending = True
        elif op == 'TSETS':
            nm = kidx(pt, (w >> 16) & 0xff)
            if pending and isinstance(nm, str):
                order.append(nm)
            pending = False
    return order


def dump(r, order):
    """导出。有字段顺序 ⇒ dict；否则 ⇒ 位置数组。"""
    out = {}
    protos = r.protos[1:] if len(r.protos) > 1 else r.protos
    for pt in protos:
        for w in pt.bc:
            if OPS[w & 0xff] != 'TDUP':
                continue
            c = kidx(pt, (w >> 16) & 0xffff)
            arr = getattr(c, 'array', None) or []
            h = dict(getattr(c, 'hash', []) or {})
            if h and not order:
                key = h.get('bid') or h.get('id')
                if key is not None:
                    out[str(key)] = {k: v for k, v in h.items()}
                continue
            if len(arr) < 2:
                continue
            if order:
                key = arr[1] if isinstance(arr[1], int) else (arr[0] if isinstance(arr[0], int) else None)
                if key is None:
                    continue
                row = {}
                for i, nm in enumerate(order):
                    idx = i + 1
                    row[nm] = arr[idx] if idx < len(arr) else None
                out[str(key)] = row
            else:
                key = arr[1] if isinstance(arr[1], int) else None
                if key is None:
                    continue
                out[str(key)] = arr[1:]
    return out


def cmd_list(z):
    rows = []
    for n in z.namelist():
        if n.endswith('.luac') and n.startswith(PREFIX):
            rows.append((n[len(PREFIX):], z.getinfo(n).file_size))
    rows.sort(key=lambda x: -x[1])
    print('共 %d 张配置表：' % len(rows))
    for b, s in rows:
        print('  %-48s %9d' % (b, s))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    z = open_apk()
    op = sys.argv[1]
    if op == 'list':
        return cmd_list(z)
    name = sys.argv[2] if len(sys.argv) > 2 else ''
    r = entry(z, name)
    order = field_order(r)
    if op == 'field':
        print('%s 字段顺序 (%d)：%s' % (name, len(order), order))
        return
    data = dump(r, order)
    if op == 'peek':
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        print('%s 共 %d 条（字段顺序 %s）' % (name, len(data), order[:10]))
        for k in list(data)[:n]:
            print('  %-8s %s' % (k, json.dumps(data[k], ensure_ascii=False)[:150]))
        return
    if op == 'dump':
        dst = sys.argv[3] if len(sys.argv) > 3 else os.path.join(
            'server', 'cfg_' + name.replace('.luac', '') + '.json')
        json.dump(data, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)
        print('%s: %d 条 -> %s' % (name, len(data), dst))
        return
    print(__doc__)


if __name__ == '__main__':
    main()
