#!/usr/bin/env python3
"""从 1.4.9 APK 提取 `Config.SkillMagic`（12665 行）与 `Config.SkillMagicType`（31 项）。

## 为什么这样提取是权威的（证据链）

`assets/src/config/config_skill_magic.luac` 有 3 个 proto：

* **proto#0** = 数据本体：`kgc` 里 12665 个 `TableConst`，每个是 18 元素数组
  `[None, v1, v2, ..., v17]`（**index 0 是占位 `None`**）。
* **proto#1** = 建表器，**逐字段给出「数组下标 → 字段名」的权威映射**。反汇编原文：

      GGET  A=2 D=0            ; Config
      TGETS A=2 B=2 C=1        ; ['SkillMagic']
      TDUP  A=3 D=3            ; { }
      TGETB A=4 D=257          ; idx 1
      TSETS A=4 B=3 C=4        ; ['bid']
      TGETB A=4 D=258          ; idx 2
      TSETS A=4 B=3 C=5        ; ['type']
      TGETB A=4 D=259          ; idx 3   -> flag
      TGETB A=4 D=260          ; idx 4   -> grade
      TGETB A=4 D=261          ; idx 5   -> per
      TGETB A=4 D=262          ; idx 6   -> target_camp
      TGETB A=4 D=263          ; idx 7   -> duration
      TGETB A=4 D=264          ; idx 8   -> res_up
      TGETB A=4 D=265          ; idx 9   -> res_buff_up
      TGETB A=4 D=266          ; idx 10  -> res_down
      TGETB A=4 D=267          ; idx 11  -> desc
      TGETB A=4 D=268          ; idx 12  -> magic_desc
      TGETB A=4 D=269          ; idx 13  -> effect_type
      TGETB A=4 D=270          ; idx 14  -> icon
      TGETB A=4 D=271          ; idx 15  -> location
      TGETB A=4 D=272          ; idx 16  -> cycle
      TGETB A=4 D=273          ; idx 17  -> must_play

  `TGETB D=256+n` 即取数组下标 `n`（`256` 是 LuaJIT 的 KIndexed 基址）。
  ⇒ **下标映射不是猜的，是 proto#1 的 TSETS 顺序直读。**

* **proto#2** = `Config.SkillMagicType.get(data)`：其 `kgc` 里含一张
  `{1010:'atk_s', 1020:'atk_p', ...}` 的 hash 表（31 项），即 `type` 字段的**属性 ID → 名**表。

复现：
    python tools/luajit_dis.py anzbao/jstm.apk assets/src/config/config_skill_magic.luac 1 0 60
    python tools/luajit_dis.py anzbao/jstm.apk assets/src/config/config_skill_magic.luac 2 0 30

## 交叉验证（3 条，均通过）

| 验证 | 结果 |
|---|---|
| `type=1240`（SkillMagicType 里的 `control`）| 行 `bid=683140` 的 `magic_desc` = **「封禁 控制技能成功率+10.6%」** ✅ |
| `type=1010`（`atk_s`）| 行 `bid=906001` 的 `magic_desc` = **「魂导压缩 物理攻击+{per}%」**，`per=500` ✅ |
| 占位占位符 | `magic_desc` 里出现 `{per}` / `{val}` / `{val_per}`，与客户端 `battle_role.luac` proto#4 的
`gsub` 替换逻辑（常量 `'{val_per}'` `'{val}'` `'{per}'`）**一致** ✅ |

用法：
    python extract_skill_magic.py                 # 默认读 anzbao/jstm.apk
    python extract_skill_magic.py --apk <path> --outdir <dir>
"""
import argparse
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(WORKSPACE, 'tools'))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import TableConst, parse_bytes  # noqa: E402

DEFAULT_APK = os.path.join(WORKSPACE, 'anzbao', 'jstm.apk')
MEMBER = 'assets/src/config/config_skill_magic.luac'

# ★ 由 proto#1 的 TSETS 顺序直读得到（下标 1..17）
FIELDS = [
    'bid',          # 1  int    效果 ID（= 线上 magic_bid）
    'type',         # 2  int    效果属性 ID → SkillMagicType（1010..1280 等）
    'flag',         # 3  str
    'grade',        # 4  int
    'per',          # 5  int    百分比
    'target_camp',  # 6  int    目标阵营
    'duration',     # 7  int    默认持续回合（0=瞬时；255=永久，见下）
    'res_up',       # 8  str    表现资源
    'res_buff_up',  # 9  str
    'res_down',     # 10 str
    'desc',         # 11 str    名称
    'magic_desc',   # 12 str    描述模板（含 {per}/{val}/{val_per}）
    'effect_type',  # 13 int    次级分类（观察值 0/1/2/3）
    'icon',         # 14 int    buff 图标
    'location',     # 15 int    挂点
    'cycle',        # 16 int    循环方式
    'must_play',    # 17 int    是否必须播放表现
]

# duration 特殊值（**推断**，标注见 README）
DURATION_INSTANT = 0     # 瞬时，不入 magic_list
DURATION_PERMANENT = 255  # 观察到 88 行的特殊值，推断为"永久"


def extract(apk=DEFAULT_APK):
    z = zipfile.ZipFile(apk)
    r = parse_bytes(z.read(MEMBER))
    if len(r.protos) < 3:
        raise SystemExit('!! proto 少于 3 个，APK 结构不符（读到 %d）' % len(r.protos))

    # --- proto#0: 数据行 ---
    rows_raw = [c.array for c in r.protos[0].kgc if isinstance(c, TableConst)]
    rows = []
    skipped = 0
    for a in rows_raw:
        if not a or len(a) < 18:
            skipped += 1
            continue
        vals = a[1:18]                       # 丢掉 index 0 的 None
        rec = {}
        for name, v in zip(FIELDS, vals):
            # 只保留有意义的值，缩小 JSON 体积；读取端用 .get(k, default)
            if v is None or v == '':
                continue
            rec[name] = v
        if 'bid' not in rec:
            skipped += 1
            continue
        rows.append(rec)

    # --- proto#2: SkillMagicType ---
    types = {}
    for c in r.protos[2].kgc:
        if isinstance(c, TableConst):
            for k, v in (c.hash or []):
                if isinstance(v, str):
                    types[int(k)] = v
    return rows, types, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apk', default=DEFAULT_APK)
    ap.add_argument('--outdir', default=HERE)
    args = ap.parse_args()

    rows, types, skipped = extract(args.apk)

    # 按 bid 建索引表，便于服务端 O(1) 查
    by_bid = {}
    for rec in rows:
        by_bid[int(rec['bid'])] = rec

    duration_dist = {}
    for rec in rows:
        d = int(rec.get('duration', 0))
        duration_dist[d] = duration_dist.get(d, 0) + 1

    out = {
        '_source': 'assets/src/config/config_skill_magic.luac (1.4.9)',
        '_extractor': 'analysis/server_reference/yzxy/impl/extract_skill_magic.py',
        '_fields': FIELDS,
        '_field_order_evidence': 'proto#1 的 TSETS 顺序（TGETB D=257..273）',
        '_duration_special': {
            str(DURATION_INSTANT): '瞬时（不入 magic_list）',
            str(DURATION_PERMANENT): '推断为永久（INFERRED，未验证）',
        },
        '_notes': [
            'type 只对 1010..1280 有 SkillMagicType 名字；2xxx/3xxx/4xxx/5xxx 等属其它 ID 空间，本表未解',
            'effect_type 观察值为 0/1/2/3；与 UI 三类（控制/增益/减益）的映射尚未验证',
            '所有 *_res 与 icon 是客户端表现资源，服务端只需回传',
        ],
        'count': len(rows),
        'skipped': skipped,
        'duration_dist': {str(k): v for k, v in sorted(duration_dist.items())},
        'SkillMagicType': {str(k): v for k, v in sorted(types.items())},
        'SkillMagic': {str(k): v for k, v in sorted(by_bid.items())},
    }

    p = os.path.join(args.outdir, 'skill_magic.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print('写出 %s' % p)
    print('  SkillMagic 行数 : %d（跳过 %d）' % (len(rows), skipped))
    print('  SkillMagicType  : %d 项' % len(types))
    print('  duration 分布   : %s' % out['duration_dist'])
    print('  文件大小        : %.2f MB' % (os.path.getsize(p) / 1048576.0))


if __name__ == '__main__':
    main()
