"""提取 1.4.9 `config_npc.luac` 的 Config.Npc：NPC 名称/模型/对话/按钮。

字节码形态（反汇编 config_npc.luac proto#0）：

    TDUP  r2 = {bid=10010, name='玄老', face='N10023', res_id='N10052',
                type=1, dir=4, nature=0, lev=1, talk='...', talk2='...',
                filter_id=0, enter_map_effect=0}
    TDUP  r3 = {9001}                     -- button 子表（可选）
    TSETS r3 -> r2['button']
    KSHORT r3 = 10010 ; TSETV r2 -> Config.Npc[10010]

输出 analysis/1.4.9/task/config_npc.json
     { "<bid>": {name, face, res_id, type, dir, talk, talk2, button:[...] } }
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def num(v):
    if isinstance(v, float) and v == int(v):
        return int(v)
    return v


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else r'analysis\1.4.9\task\config_npc.json'
    r = parse_file(path)
    root = r.protos[0]
    bc = root.bc

    npcs = {}
    cur = None
    pending_sub = None      # 待挂到 cur 上的子表 (TableConst)
    pending_sub_name = None

    for i, w in enumerate(bc):
        op = op_name(w)
        if op == 'TDUP':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            if isinstance(v, TableConst):
                h = {str(k): num(val) for k, val in (v.hash or [])}
                if 'bid' in h and ('name' in h or 'face' in h):
                    cur = h
                    cur['_button'] = []
                    pending_sub = None
                else:
                    pending_sub = v
        elif op == 'TSETS':
            c = (w >> 16) & 0xff
            nm = kidx(root, c)
            if isinstance(nm, str) and nm == 'button' and cur is not None \
                    and pending_sub is not None:
                cur['_button'] = [num(x) for x in (pending_sub.array or []) if x is not None]
                pending_sub = None
        elif op == 'TSETV':
            if cur is not None and 'bid' in cur:
                bid = num(cur['bid'])
                cur['button'] = cur.pop('_button', [])
                npcs[str(bid)] = cur
            cur = None
            pending_sub = None

    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(npcs, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1, sort_keys=True)
    print('Config.Npc 条目: %d -> %s' % (len(npcs), out))

    for probe in ('10010', '10020', '10030', '20011', '20070'):
        e = npcs.get(probe)
        print('  npc %-7s %s' % (probe, ('name=%r res_id=%r type=%s' % (
            e.get('name'), e.get('res_id'), e.get('type'))) if e else '【不在 Config.Npc】'))


if __name__ == '__main__':
    main()
