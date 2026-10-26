"""提取 1.4.9 `config_map.luac` 的 Config.Map：每个场景的完整定义 + npcs/mons/elems 布置。

★ 关键更正（与首版相比）：
   子表条目 **归属于其后第一个 TSETS**，而不是前一个。
   字节码形态：

       TNEW  r3                                  ; 新子表
       TDUP  r4 {x,y} ; KSHORT r5 <id> ; TSETV   ; 往 r3 里塞条目
       ...
       TSETS r3 -> r2['<字段名>']                 ; ★ 此处才确定子表叫什么

   所以条目区间是 (上一个 TSETS, 下一个 TSETS]，字段名取**下一个** TSETS。

输出 analysis/1.4.9/task/config_map.json
     { "<scene_id>": { "name":..., "rows":..., "npcs": {id:{x,y}}, "mons": {...}, "elems": {...} } }
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402

SUB_FIELDS = ('npcs', 'mons', 'elems', 'effects', 'buildings')


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def num(v):
    if isinstance(v, float) and v == int(v):
        return int(v)
    return v


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else r'analysis\1.4.9\task\config_map.json'
    r = parse_file(path)
    root = r.protos[0]
    bc = root.bc

    # 1) 收集 TSETS 事件（字段赋值点）
    tsets = []   # (bc_index, field_name)
    for i, w in enumerate(bc):
        if op_name(w) != 'TSETS':
            continue
        c = (w >> 16) & 0xff
        v = kidx(root, c)
        if isinstance(v, str):
            tsets.append((i, v))

    # 2) 收集所有 "TDUP{x,y} + KSHORT/KNUM key + TSETV" 条目
    entries = []   # (bc_index, key, {x,y})
    last_num = None
    last_tdup = None
    for i, w in enumerate(bc):
        op = op_name(w)
        if op == 'KSHORT':
            last_num = (w >> 16) & 0xffff
        elif op == 'KNUM':
            d = (w >> 16) & 0xffff
            pos = len(root.knum) - 1 - d
            last_num = num(root.knum[pos]) if 0 <= pos < len(root.knum) else None
        elif op == 'TDUP':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            if isinstance(v, TableConst):
                h = {str(k): num(val) for k, val in (v.hash or [])}
                if 'x' in h and 'y' in h and len(h) <= 3:
                    last_tdup = (i, h)
        elif op == 'TSETV':
            if last_tdup is not None and last_num is not None:
                entries.append((last_tdup[0], num(last_num), last_tdup[1]))
            last_tdup = None
            last_num = None
        elif op in ('TSETS', 'TSETB'):
            last_num = None

    # 3) 场景表（含 bid/name/rows/cols 的 TDUP）
    scenes = []
    for i, w in enumerate(bc):
        if op_name(w) != 'TDUP':
            continue
        d = (w >> 16) & 0xffff
        v = kidx(root, d)
        if isinstance(v, TableConst):
            h = {str(k): num(val) for k, val in (v.hash or [])}
            if 'bid' in h and ('name' in h or 'rows' in h):
                scenes.append((i, h))

    # 4) 归属：条目属于其后第一个 TSETS；该 TSETS 又属于它之前最近的那个场景表
    def scene_for(idx):
        best = None
        for si, h in scenes:
            if si < idx:
                best = h
            else:
                break
        return best

    for ei, key, xy in entries:
        nxt = None
        for ti, fname in tsets:
            if ti > ei:
                nxt = fname
                break
        if nxt is None or nxt not in SUB_FIELDS:
            continue
        sc = scene_for(ei)
        if sc is None:
            continue
        sc.setdefault(nxt, {})[str(key)] = {'x': num(xy.get('x')), 'y': num(xy.get('y'))}

    out_map = {}
    for _, h in scenes:
        sid = num(h.get('bid'))
        if sid is None:
            continue
        out_map[str(sid)] = h

    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(out_map, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1, sort_keys=True)
    print('Config.Map 场景数: %d  -> %s' % (len(out_map), out))
    tot = {'npcs': 0, 'mons': 0, 'elems': 0}
    for sid in sorted(out_map, key=lambda x: int(x))[:22]:
        s = out_map[sid]
        print('  scene %-6s %-12s npcs=%-4d mons=%-4d elems=%-4d def=(%s,%s)'
              % (sid, str(s.get('name'))[:12], len(s.get('npcs', {})),
                 len(s.get('mons', {})), len(s.get('elems', {})),
                 s.get('def_x'), s.get('def_y')))
    for s in out_map.values():
        for k in tot:
            tot[k] += len(s.get(k, {}))
    print('全表合计: npcs=%d mons=%d elems=%d' % (tot['npcs'], tot['mons'], tot['elems']))


if __name__ == '__main__':
    main()
