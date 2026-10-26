#!/usr/bin/env python3
"""验证「去渠道登录 + 指向本地服务端」补丁是否真的落在 APK 里。

对每个已打补丁的 APK 断言三件事（与 tools/patch_fake_login.py 的三步一一对应）：

  [1] DEX：`Lcom/shiyue/sdk/EWanSdk;.is_close` 的 **const/4 字面量 = 1**
      （渠道 SDK 彻底静默；0 = 未打补丁）
  [2] `assets/src/config.luac`：`URL_LUA_CONFIG` 指向本地服务端，
      且**原 CDN 域名已消失**
  [3] `config.luac` 末尾含伪登录块（含 `sdkBackInit` / `sdkBackLogin`）

用法：python tools/verify_patched_apks.py
"""
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_HOST = '10.0.2.2:8080'
TARGETS = [
    ('1.4.9  (qihoo)', 'patched/jstm_fakelogin_aligned.apk'),
    ('1.4.11 (baidu2)', 'patched/jstm_1411_fakelogin_aligned.apk'),
    ('1.3.0  (base)', 'patched/dldlJl_fakelogin_aligned.apk'),
]


def uleb(d, p):
    r = sh = 0
    while True:
        b = d[p]; p += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80):
            return r, p
        sh += 7


def dstrs(dex):
    n, off = struct.unpack_from('<II', dex, 56)
    for i in range(n):
        p = struct.unpack_from('<I', dex, off + i * 4)[0]
        ln, q = uleb(dex, p)
        yield i, dex[q:q + ln]


def find_is_close_field(dex):
    """返回 field_ids 里 is_close 的索引。"""
    sn, so = struct.unpack_from('<II', dex, 56)
    tn, to = struct.unpack_from('<II', dex, 64)
    cn, co = struct.unpack_from('<II', dex, 72)      # field_ids
    fn, fo = struct.unpack_from('<II', dex, 80)
    def s(i):
        p = struct.unpack_from('<I', dex, so + i * 4)[0]
        ln, q = uleb(dex, p)
        return dex[q:q + ln]
    def t(i):
        return s(struct.unpack_from('<I', dex, to + i * 4)[0]) if i < tn else b''
    for i in range(fn):
        c, ty, n = struct.unpack_from('<HHI', dex, fo + i * 8)
        if t(c) == b'Lcom/shiyue/sdk/EWanSdk;' and s(n) == b'is_close':
            return i
    return None


def check(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return False, ['文件不存在']
    msgs = []
    ok = True
    z = zipfile.ZipFile(p)

    # [1] DEX
    dex = z.read('classes.dex')
    idx = find_is_close_field(dex)
    if idx is None:
        return False, ['找不到 is_close 字段']
    pat = struct.pack('<H', idx)
    lit = None
    start = 0
    while True:
        i = dex.find(pat, start)          # i = iput 指令里 idx 的低字节位置
        if i < 0:
            break
        # 指令布局（DEX 16 位码元）：
        #   i-4: 12 xx   const/4 vA, #+B      ← 打补丁改的就是 xx
        #   i-2: 5c rr   iput-boolean ...
        #   i  : aa bb   field@idx (小端)
        # ★ const/4 的字面量在**高半字节**：12 10 = v0,#1 ⇒ lit = xx >> 4
        if i >= 4 and dex[i - 4] == 0x12 and dex[i - 2] == 0x5C:
            lit = dex[i - 3] >> 4
            break
        start = i + 1
    if lit == 1:
        msgs.append('  [1] DEX  is_close 字面量 = 1  ✓ 渠道 SDK 静默')
    else:
        msgs.append('  [1] DEX  is_close 字面量 = %s  ✗（应为 1）' % lit)
        ok = False

    # [2] URL
    cfg = z.read('assets/src/config.luac').decode('utf-8', 'ignore')
    m = re.search(r'URL_LUA_CONFIG\s*=\s*"([^"]+)"', cfg)
    url = m.group(1) if m else '(无)'
    if BASE_HOST in url:
        msgs.append('  [2] URL  %s  ✓ 已指向本地服务端' % url)
    else:
        msgs.append('  [2] URL  %s  ✗（应含 %s）' % (url, BASE_HOST))
        ok = False
    for bad in ('cdn.jstm.ewan.cn', 'cdnres.jstm.shiyuegame.com'):
        if bad in cfg:
            msgs.append('       ✗ 原 CDN 域名 %s 仍在' % bad)
            ok = False

    # [3] 伪登录块
    if 'sdkBackInit' in cfg and 'sdkBackLogin' in cfg:
        msgs.append('  [3] Lua  含 sdkBackInit / sdkBackLogin  ✓ 伪登录块已注入')
    else:
        msgs.append('  [3] Lua  ✗ 未找到伪登录块')
        ok = False
    return ok, msgs


def main():
    allok = True
    for label, rel in TARGETS:
        print('=' * 70)
        print('%s   %s' % (label, rel))
        ok, msgs = check(rel)
        for m in msgs:
            print(m)
        print('  => %s' % ('PASS' if ok else 'FAIL'))
        allok = allok and ok
    print()
    print('=== 总结: %s ===' % ('全部 PASS' if allok else '有失败'))
    sys.exit(0 if allok else 1)


if __name__ == '__main__':
    main()
