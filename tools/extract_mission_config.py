"""从 1.4.9 客户端的 config_mission.luac 提取完整任务配置 → JSON。

依据（反汇编得到的构造模式，以 Config.Mission[10010] 为例）：

    TDUP  <条目表，含 bid/name/desc/type/lev/accept_npc_id/commit_npc_id/...>
    TNEW  {}                      ┐ progress
    TSETS 'progress'              ┘
    TNEW  {}                      ┐ award_assets
    TDUP  {1=2, 2=1290}  TSETB    │  ← 每个二元组一行
    TDUP  {1=4, 2=500}   TSETB    │
    TDUP  {1=15,2=500}   TSETB    ┘
    TSETS 'award_assets'
    ...
    KSHORT 10010 / TSETV          ← Config.Mission[10010] = 条目

用法：
    python tools/extract_mission_config.py <apk> <输出json>
"""
import json
import sys
import zipfile

sys.path.insert(0, 'tools')
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

# 这几张子表按"列表"处理
LIST_FIELDS = ('progress', 'award_assets', 'commit_item', 'commit_career_item',
               'commit_assets', 'ext', 'award_items', 'commit_items')
# 这几张按"标量表"处理
MAP_FIELDS = ('misc',)


def extract(apk_path):
    z = zipfile.ZipFile(apk_path)
    r = parse_bytes(z.read('assets/src/config/config_mission.luac'))
    pt = r.protos[0]

    missions = {}
    entry = None            # 当前条目表（dict）
    key = None              # 最近的 KSHORT/KNUM
    pending_list = None     # 正在累积的"列表"
    pending_map = None      # 正在累积的"标量表"

    for i, w in enumerate(pt.bc):
        op = OPS[w & 0xff]
        d = (w >> 16) & 0xffff

        if op == 'TDUP':
            c = kidx(pt, d)
            arr = list(getattr(c, 'array', []) or [])
            h = dict(getattr(c, 'hash', []) or [])
            if 'bid' in h:                     # 条目表
                entry = h
                pending_list = None
                pending_map = None
            else:
                # 二元组 {1=code, 2=num} 或其它小表 → 收进 pending
                if pending_list is not None and arr:
                    pending_list.append([x for x in arr[1:] if x is not None])
                elif pending_list is not None and h:
                    # Lua 表 {1=code, 2=num} —— 键是**数字**（1.0/2.0），不是字符串
                    a = h.get(1.0, h.get(1, h.get('1.0', h.get('1'))))
                    b = h.get(2.0, h.get(2, h.get('2.0', h.get('2'))))
                    if a is not None or b is not None:
                        pending_list.append([a, b])
                elif pending_map is not None and h:
                    pending_map.update({str(k): v for k, v in h.items()})
        elif op == 'TNEW':
            # 新表：可能是某个子表，先记下"待定表"
            pending_list = []
            pending_map = None
        elif op == 'TSETS':
            name = kidx(pt, (w >> 16) & 0xff)
            if isinstance(name, str) and entry is not None:
                if name in LIST_FIELDS:
                    entry[name] = pending_list or []
                    pending_list = None
                elif name in MAP_FIELDS:
                    entry[name] = pending_map or {}
                    pending_map = None
        elif op == 'KSHORT':
            key = d
        elif op == 'KNUM':
            try:
                key = pt.knum[d]
            except Exception:
                key = None
        elif op == 'TSETV':
            if entry is not None and key is not None:
                bid = entry.get('bid', key)
                if isinstance(bid, float):
                    bid = int(bid)
                missions[int(key)] = entry
            entry = None
            key = None
            pending_list = None
            pending_map = None

    return missions


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    out = sys.argv[2] if len(sys.argv) > 2 else r'server\mission_config.json'
    ms = extract(apk)
    print('提取任务数:', len(ms))
    # 只看主线（type=1）且按 bid 排序，打印前 12 条
    zhu = sorted(k for k, v in ms.items() if v.get('type') == 1)
    print('主线(type=1) 任务数:', len(zhu))
    for k in zhu[:12]:
        v = ms[k]
        print('   %-7s %-12s lev=%-3s accept_npc=%-6s commit_npc=%-6s award=%s'
              % (k, str(v.get('name'))[:12], v.get('lev'),
                 v.get('accept_npc_id'), v.get('commit_npc_id'),
                 v.get('award_assets')))
    # 抽样校验 10010（应与客户端一致：[[2,1290],[4,500],[15,500]]）
    v = ms.get(10010)
    print()
    print('抽查 10010:', {k: v.get(k) for k in ('bid', 'name', 'desc', 'type', 'lev',
                                                'accept_npc_id', 'commit_npc_id',
                                                'award_assets')} if v else None)
    json.dump({str(k): v for k, v in ms.items()},
              open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('已写出', out)


if __name__ == '__main__':
    main()
