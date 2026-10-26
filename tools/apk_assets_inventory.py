"""列出 1.4.9 APK 的 assets 资产清单，重点看 config 表与场景/怪物相关文件。

用法：python tools/apk_assets_inventory.py <apk> [关键字正则]
"""
import re
import sys
import zipfile

apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
pattern = sys.argv[2] if len(sys.argv) > 2 else None

z = zipfile.ZipFile(apk)
infos = z.infolist()

# 按目录聚合
from collections import defaultdict
bydir = defaultdict(list)
for i in infos:
    name = i.filename
    d = name.rsplit('/', 1)[0] if '/' in name else '(root)'
    bydir[d].append((name, i.file_size))

print('总条目:', len(infos))
print()
print('=== 目录聚合（前 80） ===')
for d in sorted(bydir, key=lambda k: -len(bydir[k]))[:80]:
    tot = sum(s for _, s in bydir[d])
    print('%-70s %5d files %12d bytes' % (d, len(bydir[d]), tot))

if pattern and pattern not in ('*', ''):
    rx = re.compile(pattern, re.I)
    print()
    print('=== 匹配 %s ===' % pattern)
    for i in infos:
        if rx.search(i.filename):
            print('%12d  %s' % (i.file_size, i.filename))

print()
print('=== assets/src/config/ 全表 ===')
cfg = [(n, s) for n, s in [(i.filename, i.file_size) for i in infos]
       if n.startswith('assets/src/config/')]
for n, s in sorted(cfg):
    print('%12d  %s' % (s, n))
