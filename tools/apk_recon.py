#!/usr/bin/env python3
"""侦察：对比三个 APK 的版本、包名、渠道 SDK、以及是否同一款游戏。

用法：python tools/apk_recon.py
"""
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

APKS = ['anzbao/jstm.apk', 'anzbao/jstm_142165.apk', 'anzbao/dldlJl.apk']


def uleb(d, p):
    r = sh = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80):
            return r, p
        sh += 7


def dex_strings(dex, limit=None):
    """产出 dex 里的全部字符串（用于判定类名/SDK 是否存在）。"""
    n, off = struct.unpack_from('<II', dex, 56)
    for i in range(n):
        p = struct.unpack_from('<I', dex, off + i * 4)[0]
        ln, q = uleb(dex, p)
        yield dex[q:q + ln]
        if limit and i >= limit:
            return


def manifest_info(apk):
    """从 AndroidManifest 的字符串池里粗略抽取包名/版本字符串。"""
    try:
        z = zipfile.ZipFile(apk)
        xml = z.read('AndroidManifest.xml')
    except Exception as e:
        return {'err': repr(e)}
    # 二进制 XML：把可打印的 UTF-16/UTF-8 片段抽出来看看
    txt = xml.decode('utf-16-le', 'ignore')
    strs = re.findall(r'[\x20-\x7e]{4,}', txt)
    pkg = [s for s in strs if s.count('.') >= 2 and 'android' not in s][:6]
    ver = [s for s in strs if re.match(r'^\d+\.\d+\.\d+$', s)][:6]
    return {'pkg_candidates': pkg, 'versions': ver}


for rel in APKS:
    p = os.path.join(ROOT, rel)
    print('=' * 74)
    print(rel, '（%.1f MB）' % (os.path.getsize(p) / 1048576) if os.path.exists(p) else '缺失')
    if not os.path.exists(p):
        continue
    z = zipfile.ZipFile(p)
    names = z.namelist()
    print('  dex:', [n for n in names if n.endswith('.dex')][:4])
    print('  有 assets/src/config:', any(n.startswith('assets/src/config/') for n in names))
    luac = sum(1 for n in names if n.endswith('.luac'))
    print('  luac 数:', luac)
    print('  manifest:', manifest_info(p))
    # 渠道 SDK 检测
    try:
        dex = z.read('classes.dex')
        hits = set()
        for s in dex_strings(dex, limit=200000):
            if b'supersdk' in s or b'SuperPlatform' in s or b'EwanSdk' in s:
                hits.add(s.decode('utf-8', 'replace'))
        print('  渠道 SDK 相关字符串:', sorted(hits)[:6])
    except Exception as e:
        print('  dex 读取失败:', e)
