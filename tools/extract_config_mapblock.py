"""提取 1.4.9 `config_map_block.luac` 的 `Config.MapBlock` → `server/map_block.json`

═══════════════════════════════════════════════════════════════════════════
★ 为什么需要它（R1 审计结论）
  在接线 AOI 之后，`pathfind.MapGrid` 仍用 `allow_all=True` ⇒ `walkable()` 恒真
  ⇒ **"防穿墙"是纸面功能**。本脚本提供真实阻挡数据，让校验真正生效。
  ⚠ 数据来源是**客户端自带配置**（APK 内），不是参考项目 → 合规（APK 是最终标准）。

★ 逆向要点（全部实测得出，非推测）
  1. `Config.MapBlock` 的**每行是一个 TableConst 数组**：`[None, c1, c2, ...]`
     （Lua 1-based，索引 0 为 None）⇒ 行长 = cols + 1
  2. 字节码形态：`TDUP <行表> ; TSETB A=2 D=<行号>`，其中
     **行号 = (D & 0xff)**，且**行号回到 1 即表示新场景开始** —— 用它精确分段。
  3. **格值语义（由数据判定，非猜测）**：
       0 = 可走       1 = 阻挡       2 = **可走**（另一种地形，客户端确实会走上去）
     判据 A（配置静态）：95 个「NPC / 怪物 / 采集物 / 出生点」坐标中 94.7% 落在 0 上，
                          反极性仅 5.3% ⇒ 极性确定。
     判据 B（**真实轨迹动态**，更硬）：`server/logs/tcp.log` 里 386 个真实 10204 坐标中
        · 落在 0 上 375 个（97.2%）
        · 落在 2 上 11 个（2.8%）  ← **客户端真的走到了 2 上 ⇒ 2 必须视为可走**
        · 落在 1 上 **0 个**       ← 从未站在 1 上 ⇒ 1 = 阻挡得到实证
      ⚠ 首版曾把 2 判为"第二种障碍"，被真实轨迹否证（会造成 2.8% 的误拦/回拉）。
     值 4（全库仅 7 格）：样本不足，**视为可走**（避免误拦优先）。
  4. **只有 26/124 张场景带 MapBlock** —— 其余场景无碰撞数据，
     服务端应保持 `allow_all`（不知道就不能阻挡）。

★ 输出
  server/map_block.json
    { "_meta": {...}, "scenes": { "10001": ["0101110...", ...], ... } }
    每行是**数字字符串**（紧凑、可直接逐字符判定）。
═══════════════════════════════════════════════════════════════════════════
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import TableConst, parse_file   # noqa: E402
from luajit_dis import OPS, kidx               # noqa: E402

ROOT = os.path.dirname(HERE)
DEFAULT_LUAC = os.path.join(ROOT, 'analysis', '1.4.9', '_config_map_block.luac')
DEFAULT_MAP = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'config_map.json')
DEFAULT_OUT = os.path.join(ROOT, 'server', 'map_block.json')


def op_name(w):
    o = w & 0xff
    return OPS[o] if o < len(OPS) else 'OP_%d' % o


def segment_blocks(root):
    """按 `TSETB` 的行号（D & 0xff）分段，返回 [ [row, ...], ... ]。"""
    blocks = []
    cur = None
    cur_row = None
    for w in root.bc:
        o = op_name(w)
        if o == 'TDUP':
            d = (w >> 16) & 0xffff
            v = kidx(root, d)
            cur_row = list(v.array) if (isinstance(v, TableConst) and v.array) else None
        elif o == 'TSETB' and cur_row is not None:
            idx = ((w >> 16) & 0xffff) & 0xff
            if idx == 1:                     # ★ 行号归 1 ⇒ 新场景
                cur = []
                blocks.append(cur)
            if cur is not None:
                cur.append(cur_row)
            cur_row = None
    return blocks


def align(blocks, cm, order):
    """按 (行数, 行宽) 顺序对齐到场景 id；允许跳过 MapBlock 里没有的场景。"""
    info = [(len(b), len(b[0]) if b else 0) for b in blocks]
    si = 0
    mapping = {}
    skipped = []
    for bi, (nr, rw) in enumerate(info):
        j = si
        found = None
        while j < len(order):
            s = cm.get(str(order[j])) or {}
            if int(s.get('rows') or 0) == nr and int(s.get('cols') or 0) + 1 == rw:
                found = order[j]
                break
            skipped.append(order[j])
            j += 1
        if found is None:
            raise SystemExit('块 %d（行%d 宽%d）无法对齐到任何场景' % (bi, nr, rw))
        mapping[found] = blocks[bi]
        si = j + 1
    return mapping, skipped


def main():
    luac = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LUAC
    cm_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MAP
    out = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUT

    root = parse_file(luac).protos[0]
    cm = json.load(open(cm_path, encoding='utf-8'))
    order = [int(x) for x in root.knum]

    blocks = segment_blocks(root)
    mapping, skipped = align(blocks, cm, order)
    print('分段数 = %d，对齐场景 = %d，跳过（无碰撞数据）= %d'
          % (len(blocks), len(mapping), len(skipped)))

    scenes = {}
    total_cells = blocked_cells = 0
    on_walkable = on_total = 0
    for bid, b in mapping.items():
        rows = []
        for row in b:
            s = ''.join(str(v) for v in row[1:])
            rows.append(s)
            total_cells += len(s)
            blocked_cells += s.count('1')      # ★ 只有 '1' 是阻挡（2 经真实轨迹证明可走）
        scenes[str(bid)] = rows
        # 实体点落格统计（作为极性回归校验）
        # ⚠ 注意：`b` 是**原始 int 行**（索引 0 为 None，Lua 1-based），
        #   所以 b[r-1][c] 才是"第 r 行第 c 列"，且比较对象是 int。
        sc = cm[str(bid)]
        pts = [(int(sc.get('def_x') or 0), int(sc.get('def_y') or 0))]
        for key in ('npcs', 'mons', 'elems'):
            for _, v in (sc.get(key) or {}).items():
                if isinstance(v, dict) and 'x' in v:
                    pts.append((int(v['x']), int(v['y'])))
        for (x, y) in pts:
            r, c = int(y), int(x)
            if 1 <= r <= len(b) and 1 <= c <= len(b[0]) - 1:
                on_total += 1
                if b[r - 1][c] != 1:
                    on_walkable += 1

    meta = {
        'source': os.path.basename(luac),
        'config': 'Config.MapBlock',
        'polarity': {'0': 'walkable', '1': 'BLOCKED', '2': 'walkable',
                     '4': 'walkable(样本不足，取宽容)'},
        'blocked_chars': '1',        # 服务端据此判定；只有 '1' 是阻挡
        'evidence': {
            'A_config_entity_points_on_walkable':
                '%d/%d = %.1f%%' % (on_walkable, on_total,
                                    100.0 * on_walkable / max(1, on_total)),
            'B_real_trajectory': 'tcp.log 386 个真实 10204 坐标：0 → 375 (97.2%)，'
                                 '2 → 11 (2.8%)，1 → 0 (0%)',
            'note': '2 被真实轨迹证明是**可走**的（客户端走上去过）；'
                    '首版误判 2 为阻挡，会造成 2.8% 误拦',
        },
        'scenes_with_data': len(scenes),
        'scenes_total': len(order),
        'cells_total': total_cells,
        'cells_blocked': blocked_cells,
        'blocked_ratio': round(100.0 * blocked_cells / max(1, total_cells), 2),
        'note': '仅 %d/%d 场景带碰撞数据；其余场景服务端应保持 allow_all'
                % (len(scenes), len(order)),
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({'_meta': meta, 'scenes': scenes}, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False)
    print('写出 -> %s  (%.1f KB)' % (out, os.path.getsize(out) / 1024.0))
    print('  判据A 配置实体点落在可走格: %s'
          % meta['evidence']['A_config_entity_points_on_walkable'])
    print('  判据B 真实轨迹            : %s' % meta['evidence']['B_real_trajectory'])
    print('  总格 %d，阻挡 %d (%.1f%%)  ← 只有 "1" 视为阻挡'
          % (total_cells, blocked_cells, meta['blocked_ratio']))
    print('  有数据场景: %s' % sorted(scenes))
    print('  跳过场景数: %d' % len(skipped))


if __name__ == '__main__':
    main()
