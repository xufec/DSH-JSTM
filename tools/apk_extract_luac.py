"""从 1.4.9 APK 提取一个 .luac 到磁盘，便于反汇编分析。

用法：python tools/apk_extract_luac.py <apk条目路径> [输出路径]
      python tools/apk_extract_luac.py assets/src/game/mission/mission_util.luac
默认 APK 为 anzbao/jstm.apk（1.4.9），绝不默认使用 1.4.11。
"""
import os
import sys
import zipfile

APK_149 = r'anzbao\jstm.apk'
apk = sys.argv[1] if sys.argv[1].endswith('.apk') else APK_149
if apk == sys.argv[1]:
    entry = sys.argv[2] if len(sys.argv) > 2 else None
    out = sys.argv[3] if len(sys.argv) > 3 else None
else:
    entry = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None

if entry is None:
    print(__doc__)
    sys.exit(1)

if out is None:
    out = os.path.join('analysis', os.path.basename(entry))
os.makedirs(os.path.dirname(out), exist_ok=True)

z = zipfile.ZipFile(apk)
names = z.namelist()
if entry not in names:
    cand = [n for n in names if n.endswith(entry)]
    if len(cand) == 1:
        entry = cand[0]
        print('解析为:', entry)
    else:
        print('!! 条目不存在:', entry)
        print('   候选:', cand[:10])
        sys.exit(2)

data = z.read(entry)
with open(out, 'wb') as fh:
    fh.write(data)
print('已提取 %-60s -> %s (%d bytes)' % (entry, out, len(data)))
