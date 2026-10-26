#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 步骤 1：三版本 APK **全量资源与脚本索引**。

产出 `analysis/r1_client_index/R1_客户端资源与脚本总索引.json` + 每版本分片。

## 设计纪律（对应 R1 任务书 §三）
1. **不因为扩展名是 `.luac` 就认定它是标准 Lua 字节码** —— 逐文件读魔数判定：
     `1b 4c 4a` = LuaJIT 字节码；`1b 4c 75 61` = Lua 5.1；`78 9c`/`1f 8b` = zlib/gzip；其余记 `UNKNOWN`
2. **每个文件都记路径 / 类型 / 大小 / SHA256 / 所属版本 / 解析状态 / 关联模块**
3. **未解析文件不从分母剔除**（覆盖率统计在 R1 质量报告里按全量算）
4. 只读 APK，不写回、不移动原件

## 解析状态定义（全局统一，R1 各产物同义）
  PARSED         内容已成功读取并登记；对 luac 表示**已成功解构为 JSON**
  BYTECODE_ONLY  仅 LuaJIT 字节码（可反汇编，未还原为 Lua 源码）
  PARTIAL        部分解析（字段/表不完整，有已知失败点）
  ENCRYPTED      检测到加密/压缩包装且未能解开
  UNKNOWN        未尝试，或判据不足（含"扩展名与内容不符"）
"""
import hashlib
import json
import os
import sys
import zipfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'analysis', 'r1_client_index')

APKS = [
    ('1.3.0', r'anzbao\dldlJl.apk', 'com.shiyue.dldl.ewan'),
    ('1.4.9', r'anzbao\jstm.apk', 'com.shiyue.dldl.ewan.qihoo'),
    ('1.4.11', r'anzbao\jstm_142165.apk', 'com.shiyue.dldl.ewan.baidu2'),
]

# 已成功解构为 JSON 的配置表名（来自 server/cfg 与 _tmp_cfg）
DECON_DIRS = ['server/cfg', 'server/cfg_kconfig', 'server/cfg_kconfig2',
              'server/cfg_kconst', '_tmp_cfg']

TEXT_EXT = {'.lua', '.txt', '.csv', '.json', '.xml', '.plist', '.ini', '.md', '.cfg'}
IMG_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.pvr', '.etc', '.ktx', '.tag'}
SND_EXT = {'.mp3', '.ogg', '.wav', '.m4a', '.aac'}
FONT_EXT = {'.ttf', '.otf', '.fnt'}
ANIM_EXT = {'.plist', '.atlas', '.json'}
LIB_EXT = {'.so', '.dex', '.jar'}
ARCH_EXT = {'.zip', '.apk', '.obb'}


def deconstructed_names():
    """已解构出来的配置表名集合（用于判定 luac 是否 PARSED）。"""
    out = set()
    for d in DECON_DIRS:
        p = os.path.join(ROOT, d)
        if not os.path.isdir(p):
            continue
        for f in os.listdir(p):
            if f.endswith('.json'):
                out.add(f[:-5])
    return out


def module_of(name):
    """从 APK 内路径推关联模块。"""
    parts = name.split('/')
    if 'assets/src/game' in name:
        try:
            i = parts.index('game')
            return 'game/' + (parts[i + 1] if i + 1 < len(parts) else '?')
        except ValueError:
            pass
    if 'assets/src/config' in name:
        base = os.path.basename(name)
        for suf in ('.luac', '.json', '.lua'):
            if base.endswith(suf):
                base = base[:-len(suf)]
        return 'config/' + base
    if name.startswith('assets/src/'):
        return 'assets/' + (parts[3] if len(parts) > 3 else '?')
    if name.startswith('assets/'):
        return 'assets/' + (parts[2] if len(parts) > 2 else '?')
    if name.startswith('lib/'):
        return 'lib'
    return name.split('/')[0] if '/' in name else '(root)'


def categorize(name):
    low = name.lower()
    ext = os.path.splitext(low)[1]
    if ext == '.luac':
        return 'lua_bytecode'
    if ext == '.lua':
        return 'lua_source'
    if 'assets/src/config/' in low:
        return 'config'
    if ext in IMG_EXT:
        return 'texture'
    if ext in SND_EXT:
        return 'audio'
    if ext in FONT_EXT:
        return 'font'
    if ext in LIB_EXT:
        return 'native'
    if ext in ARCH_EXT:
        return 'archive'
    if ext in TEXT_EXT:
        return 'text'
    return 'other'


def classify_luac(head, name, decon):
    """判定 .luac 的解析状态（**不假设扩展名即字节码**）。"""
    if head[:3] == b'\x1bLJ':
        # 真 LuaJIT 字节码：配置表若已解构出 JSON ⇒ PARSED，否则 BYTECODE_ONLY
        base = os.path.basename(name)
        stem = base[:-5] if base.endswith('.luac') else base
        if stem in decon:
            return 'PARSED', 'LuaJIT bytecode；已解构为 JSON'
        return 'BYTECODE_ONLY', 'LuaJIT bytecode（可反汇编，未还原 Lua 源）'
    if head[:4] == b'\x1bLua':
        return 'BYTECODE_ONLY', '标准 Lua 5.x 字节码（非 LuaJIT）'
    if head[:2] in (b'\x78\x9c', b'\x1f\x8b'):
        return 'ENCRYPTED', 'zlib/gzip 压缩包装，未解'
    if head.strip()[:2] == b'--' or all(32 <= c < 127 or c in (9, 10, 13) for c in head):
        return 'UNKNOWN', '扩展名为 .luac 但内容为纯文本（**扩展名与内容不符**）'
    return 'UNKNOWN', '魔数未识别'


def build_one(ver, relpath, pkg, decon):
    apk = os.path.join(ROOT, relpath)
    full_sha = hashlib.sha256()
    with open(apk, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            full_sha.update(chunk)
    z = zipfile.ZipFile(apk)
    entries = []
    stat = Counter()
    for info in z.infolist():
        name = info.filename
        cat = categorize(name)
        try:
            with z.open(name) as f:
                data = f.read()
            sha = hashlib.sha256(data).hexdigest()
            head = data[:16]
            size = len(data)
        except Exception as e:
            sha, head, size = '', b'', info.file_size
            entries.append({
                'path': name, 'category': cat, 'module': module_of(name),
                'size': size, 'sha256': '', 'crc32': '%08x' % (info.CRC & 0xffffffff),
                'compress_size': info.compress_size,
                'parse_status': 'UNKNOWN', 'parse_note': '读取失败: %r' % (e,),
                'version': ver,
            })
            stat['UNKNOWN'] += 1
            continue
        if cat == 'lua_bytecode':
            st, note = classify_luac(head, name, decon)
        elif cat in ('text', 'config', 'lua_source'):
            st, note = 'PARSED', '文本/配置，已登记'
        elif cat in ('texture', 'audio', 'font', 'native', 'archive'):
            st, note = 'PARSED', '二进制资源，已按类型/大小/哈希登记'
        else:
            st, note = 'PARSED', '已登记'
        stat[st] += 1
        entries.append({
            'path': name, 'category': cat, 'module': module_of(name),
            'size': size, 'sha256': sha, 'crc32': '%08x' % (info.CRC & 0xffffffff),
            'compress_size': info.compress_size,
            'parse_status': st, 'parse_note': note, 'version': ver,
        })
    z.close()
    shard = {
        'version': ver, 'apk': relpath, 'package': pkg,
        'apk_size': os.path.getsize(apk), 'apk_sha256': full_sha.hexdigest(),
        'entry_count': len(entries),
        'status_counts': dict(stat),
        'module_counts': dict(Counter(e['module'] for e in entries).most_common(60)),
        'entries': entries,
    }
    return shard


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    os.makedirs(os.path.join(OUTDIR, '_per_version'), exist_ok=True)
    decon = deconstructed_names()
    print('已解构配置表名: %d 个' % len(decon))
    combined = {
        '_meta': {
            'phase': 'R1',
            'step': '01_resources_and_scripts',
            'generated_by': 'tools/r1_build_file_index.py',
            'parse_status_definitions': {
                'PARSED': '内容已成功读取并登记；对 .luac 表示已成功解构为 JSON',
                'BYTECODE_ONLY': '仅 LuaJIT 字节码（可反汇编，未还原为 Lua 源码）',
                'PARTIAL': '部分解析（字段/表不完整，有已知失败点）',
                'ENCRYPTED': '检测到加密/压缩包装且未能解开',
                'UNKNOWN': '未尝试，或判据不足（含扩展名与内容不符）',
            },
            'note': '分母 = APK 全量条目，未剔除未解析项',
            'entries_location': '本文件只放**汇总 + 指针**；每版本逐条 entries 在 '
                                '`_per_version/file_index_<版本>.json`（`versions[v].shard` 给出路径），'
                                '避免生成 16 MB 级单体文件',
            'per_entry_fields': ['path', 'category', 'module', 'size', 'sha256', 'crc32',
                                 'compress_size', 'parse_status', 'parse_note', 'version'],
        },
        'versions': {},
        'totals': {},
    }
    agg = Counter()
    total = 0
    for ver, rel, pkg in APKS:
        print('--- 扫描 %s (%s) ...' % (ver, rel))
        shard = build_one(ver, rel, pkg, decon)
        p = os.path.join(OUTDIR, '_per_version', 'file_index_%s.json' % ver)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(shard, f, ensure_ascii=False)
        print('    entries=%d status=%s' % (shard['entry_count'], shard['status_counts']))
        combined['versions'][ver] = {
            'apk': shard['apk'], 'package': shard['package'],
            'apk_size': shard['apk_size'], 'apk_sha256': shard['apk_sha256'],
            'entry_count': shard['entry_count'],
            'status_counts': shard['status_counts'],
            'shard': '_per_version/file_index_%s.json' % ver,
        }
        for k, v in shard['status_counts'].items():
            agg[k] += v
        total += shard['entry_count']
    combined['totals'] = {'entries': total, 'by_status': dict(agg)}
    out = os.path.join(OUTDIR, 'R1_客户端资源与脚本总索引.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(combined, f, ensure_ascii=False, indent=1)
    print('\n总条目 %d  状态分布 %s' % (total, dict(agg)))
    print('写出: %s' % out)


if __name__ == '__main__':
    main()
