"""从 config_drop.luac 提取「掉落组 -> 物品」表 → JSON。

结构（从字节码直读，不是猜的）：
    Config.Drop[<drop_id>] = { first_p:{...}, core_p:{...}, normal:{...}, normal_sum:{...},
                               <若干物品/概率字段> }
    bytecode: KSHORT <drop_id> / TSETV  —— 说明外层是**数组**，每个元素是一条记录

用法：python tools/extract_drop.py [apk] [out.json]
"""
import json
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

SRC = 'assets/src/config/config_drop.luac'


def extract(apk):
    z = zipfile.ZipFile(apk)
    r = parse_bytes(z.read(SRC))
    pt = r.protos[0]
    bc = pt.bc
    out = {}
    cur_id = None
    for i, w in enumerate(bc):
        op = OPS[w & 0xff]
        if op == 'KSHORT':
            # KSHORT 后紧跟 TSETV ⇒ 这是数组下标（drop_id）
            if i + 1 < len(bc) and OPS[bc[i + 1] & 0xff] == 'TSETV':
                cur_id = (w >> 16) & 0xffff
        elif op == 'TDUP':
            c = kidx(pt, (w >> 16) & 0xffff)
            h = dict(getattr(c, 'hash', []) or {})
            arr = getattr(c, 'array', []) or []
            if (h or arr) and cur_id is not None:
                out.setdefault(str(cur_id), []).append(
                    {'hash': h} if h else {'array': arr})
    return out


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    dst = sys.argv[2] if len(sys.argv) > 2 else r'server\cfg_drop.json'
    d = extract(apk)
    print('掉落组数:', len(d))
    for k in ('17000', '20001', '1'):
        if k in d:
            print('  %s -> %s' % (k, json.dumps(d[k][:3], ensure_ascii=False)[:220]))
    json.dump(d, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('已写出', dst)


if __name__ == '__main__':
    main()
