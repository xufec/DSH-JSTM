#!/usr/bin/env python3
"""Dump the head/tail of assets/src/config.luac inside an APK (encoding-safe)."""
import sys
import zipfile

apk = sys.argv[1] if len(sys.argv) > 1 else r'patched\jstm_solo.apk'
z = zipfile.ZipFile(apk)
d = z.read('assets/src/config.luac')
print('len =', len(d))
print('has "DSH embedded local server":', b'DSH embedded local server' in d)
print('has "DSH_SRV":', b'DSH_SRV' in d)
print('has "URL_PATH":', b'URL_PATH' in d)
print('--- head (200) ---')
print(d[:200].decode('gbk', 'replace'))
print('--- tail (600) ---')
print(d[-600:].decode('gbk', 'replace'))
