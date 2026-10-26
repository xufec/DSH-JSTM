"""精确提取 config_map_npc.luac 里的 Config.MapNpc 与 Config.MapSceneDoors。

方法：先扫描字节码找出所有 `TSETS <reg>, '<字段名>'` 的位置（这是
"把已建好的表赋给 Config.<字段名>" 的动作），据此把 TDUP 条目按区间归属到
对应字段，避免把 MapNpc 与 MapSceneDoors 混在一起。

输出：
  analysis/1.4.9/task/map_npc.json         npc_id -> {scene_id,x,y}   (Config.MapNpc)
  analysis/1.4.9/task/map_scene_doors.json  key    -> {array,hash}     (Config.MapSceneDoors)
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


def norm_num(v):
    if isinstance(v, float) and v == int(v):
        return int(v)
    return v


def main():
    path = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else r'analysis\1.4.9\task'
    r = parse_file(path)
    root = r.protos[0]
    bc = root.bc

    # 1) 找出所有 TSETS（字段赋值）的位置
    sections = []   # (bc_index, field_name)
    for i, w in enumerate(bc):
        if op_name(w) != 'TSETS':
            continue
        c = (w >> 16) & 0xff
        v = kidx(root, c)
        if isinstance(v, str):
            sections.append((i, v))
    print('TSETS 字段赋值点:', sections)

    # 2) 收集 (bc_index, key, table)，key 取 TDUP 之后最近的 KSHORT/KNUM
    entries = []
    pending = None
    for i, w in enumerate(bc):
        op = op_name(w)
        if op == 'KSHORT':
            pending = norm_num((w >> 16) & 0xffff)
        elif op == 'KNUM':
            d = (w >> 16) & 0xffff
            pos = len(root.knum) - 1 - d
            pending = norm_num(root.knum[pos]) if 0 <= pos < len(root.knum) else None
        elif op == 'TDUP':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            if isinstance(v, TableConst):
                entries.append([i, None, v])
        elif op == 'TSETV':
            if entries and entries[-1][1] is None and pending is not None:
                entries[-1][1] = pending
            pending = None
        elif op in ('TSETS', 'TSETB'):
            pending = None

    # 3) 按 section 归属：条目属于"其后第一个 TSETS"
    result = {}
    for sec_idx, name in sections:
        result[name] = []
    for bi, key, t in entries:
        nxt = None
        for sec_idx, name in sections:
            if sec_idx > bi:
                nxt = name
                break
        if nxt is None:
            nxt = '(unassigned)'
        result.setdefault(nxt, []).append((bi, key, t))

    os.makedirs(outdir, exist_ok=True)
    for name, rows in result.items():
        print('\n=== Config.%s : %d 条 ===' % (name, len(rows)))

    # MapNpc -> json
    npc_rows = result.get('MapNpc', [])
    npc_map = {}
    for bi, key, t in npc_rows:
        arr = list(t.array or [])
        npc_map[key] = {
            'scene_id': norm_num(arr[1]) if len(arr) > 1 else None,
            'x': norm_num(arr[2]) if len(arr) > 2 else None,
            'y': norm_num(arr[3]) if len(arr) > 3 else None,
            'bc_index': bi,
        }
    p1 = os.path.join(outdir, 'map_npc.json')
    json.dump({str(k): v for k, v in npc_map.items()},
              open(p1, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    print('\nMapNpc 写出 %s (%d 条, 去重后)' % (p1, len(npc_map)))

    doors = result.get('MapSceneDoors', [])
    door_out = []
    for bi, key, t in doors:
        door_out.append({
            'key': key,
            'array': [norm_num(x) for x in (t.array or [])],
            'hash': {str(k): norm_num(v) for k, v in (t.hash or [])},
            'bc_index': bi,
        })
    p2 = os.path.join(outdir, 'map_scene_doors.json')
    json.dump(door_out, open(p2, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('MapSceneDoors 写出 %s (%d 条)' % (p2, len(door_out)))

    for name, rows in result.items():
        if name in ('MapNpc', 'MapSceneDoors'):
            continue
        print('其他字段 %s: %d 条' % (name, len(rows)))


if __name__ == '__main__':
    main()
