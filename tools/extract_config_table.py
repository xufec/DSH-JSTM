"""通用 LuaJIT 配置表提取器：把 .luac 里所有 TDUP 常量表按出现顺序 dump 出来。

适用于 config_map_npc.luac / config_npc.luac / config_mon_data.luac 这类
"Config.Xxx = { [id] = {...}, ... }" 形式的配置表。

同时对 "KSHORT/KNUM 键 + TDUP 值 + TSETV" 模式识别出 **数字键 -> 表** 的映射，
这是 config_mission.luac 里 Config.Mission[10010] = {...} 的写法。

用法：
    python tools/extract_config_table.py <file.luac> [--json out.json] [--limit N]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import ChildRef, TableConst, parse_file  # noqa: E402
from luajit_dis import OPS, kidx  # noqa: E402


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def norm(v):
    """把 TableConst / ChildRef 变成 JSON 友好的结构。"""
    if isinstance(v, TableConst):
        arr = [norm(x) for x in (v.array or [])]
        h = {}
        for k, val in (v.hash or {}):
            h[str(k)] = norm(val)
        return {'__array': arr, '__hash': h}
    if isinstance(v, ChildRef):
        return '<child#%d>' % v.index
    if isinstance(v, float):
        return int(v) if v == int(v) else v
    return v


def extract(path):
    r = parse_file(path)
    root = r.protos[0]
    bc = root.bc

    tables = []          # 所有 TDUP 表
    keyed = []           # (数字键, TDUP表)
    last_num = None
    last_str = None
    pending_tdup = None  # 等待配键的 TDUP

    def _num(v):
        if isinstance(v, float) and v == int(v):
            return int(v)
        return v

    for i, w in enumerate(bc):
        op = op_name(w)
        if op == 'KSHORT':
            last_num = (w >> 16) & 0xffff
        elif op == 'KNUM':
            d = (w >> 16) & 0xffff
            pos = len(root.knum) - 1 - d
            last_num = root.knum[pos] if 0 <= pos < len(root.knum) else None
        elif op == 'KSTR':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            last_str = v if isinstance(v, str) else None
        elif op == 'TDUP':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            if isinstance(v, TableConst):
                tables.append((i, v))
                # 形态一：KSHORT/KNUM 在 TDUP 之前
                if last_num is not None:
                    keyed.append((_num(last_num), v, i))
                    last_num = None
                else:
                    # 形态二：TDUP -> KSHORT/KNUM -> TSETV（config_map_npc 的写法）
                    pending_tdup = (v, i)
        elif op == 'TSETV':
            # TSETV 紧跟：把 pending 表和最近一次数字键配对
            if pending_tdup is not None and last_num is not None:
                keyed.append((_num(last_num), pending_tdup[0], pending_tdup[1]))
                pending_tdup = None
                last_num = None
        elif op in ('TSETS', 'TSETB'):
            last_num = None

    return r, root, tables, keyed


def main():
    path = sys.argv[1]
    out = None
    if '--json' in sys.argv:
        out = sys.argv[sys.argv.index('--json') + 1]
    limit = 20
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    r, root, tables, keyed = extract(path)
    print('=== %s ===' % os.path.basename(path))
    print('protos=%d  root bc=%d  kgc=%d' % (len(r.protos), len(root.bc), len(root.kgc)))
    print('TDUP 表总数: %d   带数字键的: %d' % (len(tables), len(keyed)))
    print()
    print('--- 前 %d 个带数字键的表 ---' % limit)
    for k, t, bi in keyed[:limit]:
        arr = [norm(x) for x in (t.array or [])]
        h = {str(kk): norm(vv) for kk, vv in (t.hash or [])}
        print('  key=%-8s bc#%-6d %s' % (k, bi, json.dumps({'arr': arr, 'hash': h}, ensure_ascii=False)[:400]))

    if out:
        data = []
        for k, t, bi in keyed:
            data.append({
                'key': k,
                'bc_index': bi,
                'array': [norm(x) for x in (t.array or [])],
                'hash': {str(kk): norm(vv) for kk, vv in (t.hash or [])},
            })
        json.dump(data, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('\n已写出 %s (%d 条)' % (out, len(data)))


if __name__ == '__main__':
    main()
