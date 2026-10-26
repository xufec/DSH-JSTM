#!/usr/bin/env python3
"""Targeted DEX patch: neutralise one instruction (used to skip the SuperSDK init).

Why a byte patch instead of apktool/smali: this machine has no apktool/baksmali
and no working HTTPS egress for downloads. The DEX format lets us rewrite a
single 16-bit code unit safely, then recompute the mandatory header fields
(SHA-1 signature at 0x0C and adler32 checksum at 0x08).

Patch applied here (see tools/dexdump_full.txt around offset 6dd87c):
    Lcom/shiyue/sdk/EWanSdk;->onCollectData(...)V
    ...
    6dd86a: invoke-static {}, SuperPlatform;.getInstance()
    6dd870: move-result-object v1
    6dd872: new-instance v2, EwanSdk$1
    6dd876: invoke-direct {v2, v3}, EwanSdk$1.<init>
    6dd87c: invoke-virtual {v1, v4, v0, v2}, SuperPlatform;.init:(...)V   <-- 这里
    6dd882: goto 0004        (回到开头的 is_close 早退检查)
We replace that invoke-virtual with `00 01` = nop(0000) + nop(0001), which skips
the remaining 2 code units and lands exactly on the goto. Net effect: the game
never calls the dead ewan SDK's init (whose failure shows the blocking
"初始化失败,请检查网络" dialog), while SuperPlatform.onCreate() already ran so the
SDK object stays usable for later calls.

usage:
  python tools/patch_dex_skip_sdkinit.py <in.apk> <out.apk> [--revert]
"""
import hashlib
import os
import struct
import sys
import zlib
import zipfile

SIGNATURE_OFF = 0x0C
SIGNATURE_LEN = 20
CHECKSUM_OFF = 0x08

# ── 补丁：EwanSdk.onCollectData 里那次 SuperPlatform.init() ──────────────────
# 3 码元的 invoke-virtual 必须换成**同样长度**的指令，否则 ART 校验器会报
#   VerifyError: code did not end where expected (62 vs. 66)
# （第一次就是踩了这个：用 2 字节的 nop 对，虽然反汇编看着像"跳过"，
#   实际改变了方法体长度，整个类校验失败、启动直接崩）。
#
#   原指令：6E40 1936 4120 = invoke-virtual {v1, v4, v0, v2}, SuperPlatform;.init:(...)V
#   替换为：12 00 00 00 00 00 = const/4 v0, #0 ; nop
#   v0/v1/v2 本来就要被下一条 new-instance / move-result 覆盖，语义上是空操作。
#
# ⚠ 三个 APK 的偏移**各不相同**，所以不再硬编码地址，而是按**字节模式自动定位**：
#   目标指令一定紧跟在 `const-string "SDK初始化开始"` 那段日志代码之后。
# 目标指令的核心字节：方法号 `19 36` 在中间，操作数寄存器编码各包可能不同
# （主包是 `6e 40 ... 41 20`，其它包可能是别的寄存器组合）。
# 因此按"操作码 + 方法号"匹配，再校验寄存器字节落在合理范围。
INVOKE_OP = 0x6e                 # invoke-virtual
METHOD_ID = b'\x19\x36'          # SuperPlatform;->init 的 method index
ORIG = b'\x6e\x40\x19\x36\x41\x20'   # 主包实际形态（用于兼容旧调用）
REPL = b'\x12\x00\x00\x00\x00\x00'    # const/4 v0,#0 ; nop（等长）
# 用于确认命中的上下文锚点（出现在 init 调用之前不远处）
ANCHOR = b'\x71\x00\x17\x36\x00\x00'      # invoke-static SuperPlatform.getInstance()

# 兼容旧接口
PATCHES = [(0x6DD87C, ORIG, REPL, 'EWanSdk.onCollectData: SuperPlatform.init() -> const/4 nop')]
TARGET_OFF = 0x6DD87C
ORIG_BYTES = ORIG
PATCH_BYTES = REPL


def find_method_ids(dex, class_desc=b'Lcn/ewan/supersdk/open/SuperPlatform;',
                    method=b'init'):
    """在 dex 的 method_ids 表里查 `类;->方法` 的索引（各包不同，必须动态查）。

    返回 (init_idx, getinstance_idx) 或 (None, None)。
    """
    try:
        string_ids_size, string_ids_off = struct.unpack_from('<II', dex, 56)
        type_ids_size, type_ids_off = struct.unpack_from('<II', dex, 64)
        method_ids_size, method_ids_off = struct.unpack_from('<II', dex, 88)
    except struct.error:
        return None, None

    def uleb(d, p):
        r = sh = 0
        while True:
            b = d[p]; p += 1
            r |= (b & 0x7F) << sh
            if not (b & 0x80):
                return r, p
            sh += 7

    def dstr(i):
        off = struct.unpack_from('<I', dex, string_ids_off + i * 4)[0]
        n, p = uleb(dex, off)
        return dex[p:p + n]

    def tname(i):
        if not (0 <= i < type_ids_size):
            return b''
        return dstr(struct.unpack_from('<I', dex, type_ids_off + i * 4)[0])

    init_idx = getinst_idx = None
    for i in range(method_ids_size):
        cidx, pidx, nidx = struct.unpack_from('<HHI', dex, method_ids_off + i * 8)
        if tname(cidx) != class_desc:
            continue
        nm = dstr(nidx)
        if nm == method:
            init_idx = i
        elif nm == b'getInstance':
            getinst_idx = i
    return init_idx, getinst_idx


def locate_target(dex, report=None):
    """定位 SuperPlatform.init 调用点。

    做法：先从 method_ids 里查出 init / getInstance 的索引（各包不同），
    再在字节流里找 `invoke-virtual ... <init_idx>` 指令。
    排除标准样本包 MainActivity 里那次调用（我们要摘的是 **EWanSdk** 里那次）。
    """
    init_idx, getinst_idx = find_method_ids(dex)
    if report:
        report('method ids: init=%s getInstance=%s' % (init_idx, getinst_idx))
    if init_idx is None:
        return None

    pat = struct.pack('<H', init_idx)          # 指令编码里的方法索引字节
    gp = struct.pack('<H', getinst_idx) if getinst_idx is not None else None

    hits = []
    start = 0
    while True:
        i = dex.find(pat, start)
        if i < 0:
            break
        # 必须落在一条真实指令上：`<invoke-op> <regs1> <idx16> <regs2>`
        # i 是 idx 的位置 => 指令起点 = i-2；各包操作码可能是
        # invoke-virtual/static/super（0x6e/0x71/0x6f），所以都接受。
        if i >= 2 and (i - 2) % 2 == 0 and 0x6E <= dex[i - 2] <= 0x72:
            hits.append(i - 2)
        start = i + 1
    if report:
        report('candidate instructions: %s' % [hex(h) for h in hits])
        for h in hits[:8]:
            report('  ctx %#x: %s' % (h, dex[max(0, h - 20):h + 8].hex(' ')))

    # 只保留"紧跟在 getInstance 调用序列之后"的那一个：
    # 形态为 `71 00 <getinst16> 00 00 0c 01 22 02`（invoke-static → move-result
    # → new-instance），这能把标准样本包 MainActivity 里的同类调用区分开，
    # 而我们要摘的是 **EWanSdk** 里的那次。
    if gp:
        seq = b'\x71\x00' + gp + b'\x00\x00\x0c\x01\x22\x02'
        refined = [h for h in hits if seq in dex[max(0, h - 40):h]]
        if report:
            report('refined (EwanSdk form): %s' % [hex(h) for h in refined])
        if refined:
            hits = refined

    if not hits:
        return None
    # 仍有多个时取最后一个（样本包的调用在文件更靠前）
    return hits[-1]


def fix_header(d):
    """Recompute signature (SHA-1 over everything after it) and adler32 checksum."""
    sig = hashlib.sha1(d[SIGNATURE_OFF + SIGNATURE_LEN:]).digest()
    d = d[:SIGNATURE_OFF] + sig + d[SIGNATURE_OFF + SIGNATURE_LEN:]
    ck = zlib.adler32(d[CHECKSUM_OFF + 4:]) & 0xFFFFFFFF
    d = d[:CHECKSUM_OFF] + struct.pack('<I', ck) + d[CHECKSUM_OFF + 4:]
    return d


def main():
    src = sys.argv[1]
    dst = sys.argv[2]
    revert = '--revert' in sys.argv

    zin = zipfile.ZipFile(src)
    dex = bytearray(zin.read('classes.dex'))

    off = locate_target(bytes(dex), report=lambda m: print('  ' + m))
    if off is None:
        print('!! SuperPlatform.init 调用点未找到（该包可能结构不同）')
        return 1
    if off + len(ORIG) > len(dex):
        print('!! 命中位置越界')
        return 1

    want, new = (bytes(dex[off:off + 6]), REPL) if not revert else (REPL, None)
    got = bytes(dex[off:off + 6])
    # 校验：起点必须是 invoke-*（0x6e..0x72），且方法索引字节等于动态查到的 init 索引
    init_idx, _ = find_method_ids(bytes(dex))
    is_invoke = 0x6E <= got[0] <= 0x72
    has_idx = (init_idx is not None and struct.pack('<H', init_idx) in got)
    if revert:
        if got != REPL:
            print('!! 0x%X 处不是已打补丁的形态：%s' % (off, got.hex()))
            return 1
        dex[off:off + 6] = ORIG
        print('reverted @0x%X: %s -> %s' % (off, got.hex(), ORIG.hex()))
    else:
        if not (is_invoke and has_idx):
            print('!! 0x%X 处字节不符：%s (invoke=%s idx=%s)'
                  % (off, got.hex(), is_invoke, has_idx))
            return 1
        dex[off:off + 6] = REPL
        print('patched @0x%X: %s -> %s   # EWanSdk.onCollectData SuperPlatform.init()'
              % (off, got.hex(), REPL.hex()))

    fixed = fix_header(bytes(dex))
    print('header signature + checksum recomputed')

    zout = zipfile.ZipFile(dst, 'w', zipfile.ZIP_DEFLATED)
    for info in zin.infolist():
        data = fixed if info.filename == 'classes.dex' else zin.read(info.filename)
        zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        zout.writestr(zi, data)
    zout.close()
    zin.close()
    print('wrote', dst)
    return 0


if __name__ == '__main__':
    sys.exit(main())
