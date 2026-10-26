#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""伪登录补丁打包器：一次产出「脱离 360 SDK」的 APK。

本脚本做三件**互相独立、各自可验证**的事（每一步都断言，失败即中止）：

  [1] DEX 单字节补丁 —— 关闭 ewan/360 SDK
      Lcom/shiyue/sdk/EWanSdk;-><init>()V
        const/4 v0, #0  ; iput-boolean v0, v1, EWanSdk.is_close:Z
      把 const/4 的字面量 0 改成 1  =>  is_close = true。
      EWanSdk 的**每个**方法都以 `if (!this.is_close)` 开头，而 is_close
      在整个 dex 里只有 <init> 这一处写入（其余全是 iget-boolean 读取），
      所以这一字节等价于"S DK 彻底静默"：不再 SuperPlatform.onCreate/init、
      不再 SuperPlatform.login、所有生命周期回调 no-op
      => 360 渠道 SDK 不初始化、不弹窗、不联网。
      定位方式：解析 field_ids 找 `Lcom/shiyue/sdk/EWanSdk;.is_close` 的索引，
      再找紧随 `12 0L`(const/4) 之后、以该索引为操作数的 iput-boolean。

  [2] URL 补丁 —— 把启动配置地址指向本地服务端
      assets/src/config.luac: URL_LUA_CONFIG 字面量（断言恰好 1 处）

  [3] Lua 伪登录块 —— 追加到 assets/src/config.luac 末尾
      自供 sdkBackInit(0,..) 与 sdkBackLogin(0,..)，因为 [1] 之后 Java 侧
      再也不会回调它们。

用法：
  python tools/patch_fake_login.py <in.apk> <out.apk> \
      --base http://10.0.2.2:8080 --lua server/dsh_fake_login.lua
"""
import argparse
import hashlib
import os
import re
import struct
import sys
import zipfile
import zlib

CONFIG_ENTRY = 'assets/src/config.luac'
ORIG_URL = 'https://cdn.jstm.ewan.cn/update/config/url_config_ewan.lua'
DEX_ENTRY = 'classes.dex'
TARGET_CLASS = b'Lcom/shiyue/sdk/EWanSdk;'
TARGET_FIELD = b'is_close'

SIGNATURE_OFF = 0x0C
SIGNATURE_LEN = 20
CHECKSUM_OFF = 0x08


# --------------------------------------------------------------------------
# DEX 基础读取
# --------------------------------------------------------------------------
def _uleb(d, p):
    r = sh = 0
    while True:
        b = d[p]
        p += 1
        r |= (b & 0x7F) << sh
        if not (b & 0x80):
            return r, p
        sh += 7


class Dex:
    def __init__(self, data):
        self.d = data
        (self.string_ids_size, self.string_ids_off) = struct.unpack_from('<II', data, 56)
        (self.type_ids_size, self.type_ids_off) = struct.unpack_from('<II', data, 64)
        (self.field_ids_size, self.field_ids_off) = struct.unpack_from('<II', data, 80)

    def dstr(self, i):
        off = struct.unpack_from('<I', self.d, self.string_ids_off + i * 4)[0]
        n, p = _uleb(self.d, off)
        return self.d[p:p + n]

    def tname(self, i):
        if not (0 <= i < self.type_ids_size):
            return b''
        return self.dstr(struct.unpack_from('<I', self.d, self.type_ids_off + i * 4)[0])

    def field_index(self, class_desc, name):
        """返回 (class_idx, type_idx, name_idx) 匹配的 field_ids 下标，找不到为 None。"""
        for i in range(self.field_ids_size):
            cidx, tidx, nidx = struct.unpack_from('<HHI', self.d,
                                                  self.field_ids_off + i * 8)
            if self.tname(cidx) == class_desc and self.dstr(nidx) == name:
                return i, tidx
        return None, None


def fix_header(d):
    """重算 dex 头部 SHA-1 签名(0x0C) 与 adler32 校验和(0x08)。"""
    sig = hashlib.sha1(d[SIGNATURE_OFF + SIGNATURE_LEN:]).digest()
    d = d[:SIGNATURE_OFF] + sig + d[SIGNATURE_OFF + SIGNATURE_LEN:]
    ck = zlib.adler32(d[CHECKSUM_OFF + 4:]) & 0xFFFFFFFF
    d = d[:CHECKSUM_OFF] + struct.pack('<I', ck) + d[CHECKSUM_OFF + 4:]
    return d


# --------------------------------------------------------------------------
# [1] DEX 补丁
# --------------------------------------------------------------------------
def patch_dex_is_close(dex_bytes):
    dx = Dex(dex_bytes)
    fidx, tidx = dx.field_index(TARGET_CLASS, TARGET_FIELD)
    if fidx is None:
        sys.exit('FATAL: field %s.%s not found'
                 % (TARGET_CLASS.decode(), TARGET_FIELD.decode()))
    print('  field_ids[%d] = %s.%s  type_idx=%d'
          % (fidx, TARGET_CLASS.decode(), TARGET_FIELD.decode(), tidx))

    idx16 = struct.pack('<H', fidx)
    hits = []
    start = 0
    while True:
        i = dex_bytes.find(b'\x5c', start)          # iput-boolean
        if i < 0:
            break
        if dex_bytes[i + 2:i + 4] == idx16 and i >= 2:
            hits.append(i)
        start = i + 1
    if len(hits) != 1:
        sys.exit('FATAL: expected exactly 1 iput-boolean for is_close, got %d' % len(hits))
    i = hits[0]
    print('  iput-boolean @0x%X : %s' % (i, dex_bytes[i:i + 4].hex(' ')))

    # iput-boolean 22c 的操作数字节 = (B<<4)|A，A=取值寄存器(低半字节)，B=对象寄存器(高半字节)
    ab = dex_bytes[i + 1]
    val_reg = ab & 0x0F
    obj_reg = ab >> 4
    print('  iput-boolean 取值寄存器 v%d, 对象寄存器 v%d' % (val_reg, obj_reg))

    const_off = i - 2
    const = dex_bytes[const_off:i]
    if const[0] != 0x12:
        sys.exit('FATAL: instruction before iput-boolean is not const/4: %s' % const.hex())
    # ⚠ const/4 的操作数字节 = (D<<4)|A，A=目标寄存器(低半字节)，D=字面量(高半字节)。
    #   一开始把这两个半字节记反了：写低半字节会把寄存器从 v0 改成 v1，
    #   等于把 `this` 覆盖成 0 → 运行期
    #   NullPointerException: Attempt to write to field '...is_close' on a null object reference
    #   （dexdump 复核后才看出来：1201 被解码成 const/4 v1, #0 而不是 v0, #1）。
    reg = const[1] & 0x0F
    lit = const[1] >> 4
    if lit != 0:
        sys.exit('FATAL: expected const/4 literal 0, got %d' % lit)
    if reg != val_reg:
        sys.exit('FATAL: const/4 writes v%d but iput-boolean reads v%d — 拒绝打补丁'
                 % (reg, val_reg))
    print('  const/4 v%d, #%d @0x%X : %s' % (reg, lit, const_off, const.hex(' ')))

    # 只翻字面量（高半字节），寄存器（低半字节）原样保留
    new_byte = (0x01 << 4) | reg
    out = bytearray(dex_bytes)
    out[const_off + 1] = new_byte
    print('  PATCH 0x%X: %02x -> %02x   (const/4 v%d, #1  =>  is_close = true)'
          % (const_off + 1, const[1], new_byte, reg))
    return fix_header(bytes(out))


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--base', required=True)
    ap.add_argument('--lua', default='server/dsh_fake_login.lua')
    ap.add_argument('--no-dex', action='store_true')
    ap.add_argument('--no-lua', action='store_true')
    ap.add_argument('--flip-platform-login', action='store_true',
                    help='把 config.luac 的 IS_PLATFORM_LOGIN 翻成 false '
                         '(删去渠道登录面板 PlatformPanel，走客户端自带的账号登录 UserPanel)')
    ap.add_argument('--drop-cg', action='store_true',
                    help='从 APK 删除开场 CG assets/res/resource/login/gamecg.mp4。'
                         '⚠ 只在注入块里定义了 NO_PLAY_VIDEO 时才安全：'
                         'file_update proto#39 对默认视频路径不做 isFileExist 判断，'
                         '文件缺失会让 native 弹「无法播放此视频。」并卡死启动')
    args = ap.parse_args()

    new_url = args.base.rstrip('/') + '/update/config/url_config_ewan.lua'
    lua_extra = ''
    if not args.no_lua:
        with open(args.lua, encoding='utf-8') as f:
            lua_extra = f.read()
        print('== [3] Lua 伪登录块 %s (%d chars) ==' % (args.lua, len(lua_extra)))

    zin = zipfile.ZipFile(args.src, 'r')
    dex_old = zin.read(DEX_ENTRY)
    cfg_old = zin.read(CONFIG_ENTRY).decode('utf-8')

    print('== [1] DEX: 关闭 ewan/360 SDK ==')
    if args.no_dex:
        dex_new = dex_old
        print('  (skipped)')
    else:
        dex_new = patch_dex_is_close(dex_old)

    print('== [2] URL: URL_LUA_CONFIG -> 本地服务端 ==')
    # ★ 多版本适配（1.3.0 / 1.4.9 / 1.4.11 的 CDN 域名各不相同）：
    #   1.4.x → https://cdn.jstm.ewan.cn/update/config/url_config_ewan.lua
    #   1.3.0 → http://cdnres.jstm.shiyuegame.com/update/config/url_config_ewan.lua
    #   因此**不能硬编码域名**，改成按模式识别 URL_LUA_CONFIG 的取值
    #   （与 tools/patch_dex_skip_sdkinit.py 的"按特征动态定位"同思路）。
    m = re.search(r'URL_LUA_CONFIG\s*=\s*"([^"]+)"', cfg_old)
    if m is None or cfg_old.count(m.group(1)) != 1:
        sys.exit('FATAL: expected exactly 1 URL_LUA_CONFIG, got %d'
                 % (0 if m is None else cfg_old.count(m.group(1))))
    orig_url = m.group(1)
    if ORIG_URL in cfg_old and orig_url != ORIG_URL:
        print('  (注意：本次命中的是 %s，与已知 1.4.x 地址不同 —— 多版本)' % orig_url)
    cfg_new = cfg_old.replace(orig_url, new_url)
    print('  - %s' % [l.strip() for l in cfg_old.splitlines() if orig_url in l][0])
    print('  + %s' % [l.strip() for l in cfg_new.splitlines() if new_url in l][0])

    if args.flip_platform_login:
        print('== [2b] IS_PLATFORM_LOGIN true -> false（删渠道登录，保留账号/区服）==')
        before = cfg_new
        cfg_new = re.sub(r'IS_PLATFORM_LOGIN\s*=\s*true', 'IS_PLATFORM_LOGIN = false', cfg_new)
        cfg_new = re.sub(r'IS_PLATFORM_LOGIN\s*=\s*True', 'IS_PLATFORM_LOGIN = false', cfg_new)
        if cfg_new == before:
            sys.exit('FATAL: IS_PLATFORM_LOGIN 未找到（config.luac 结构变了？）')
        print('  IS_PLATFORM_LOGIN = false  ⇒  view4 = UserPanel（账号登录），'
              '不再是 PlatformPanel（渠道登录）')

    if lua_extra:
        cfg_new = cfg_new + lua_extra
        print('== [3] config.luac: %d -> %d bytes ==' % (len(cfg_old), len(cfg_new)))

    if os.path.exists(args.dst):
        os.remove(args.dst)
    zout = zipfile.ZipFile(args.dst, 'w', zipfile.ZIP_DEFLATED)
    replaced = {'dex': 0, 'cfg': 0}
    try:
        for info in zin.infolist():
            if info.filename == DEX_ENTRY:
                data = dex_new
                replaced['dex'] += 1
            elif info.filename == CONFIG_ENTRY:
                data = cfg_new.encode('utf-8')
                replaced['cfg'] += 1
            else:
                data = zin.read(info.filename)
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zi.internal_attr = info.internal_attr
            zi.create_system = info.create_system
            zout.writestr(zi, data)
    finally:
        zout.close()
        zin.close()

    assert replaced['dex'] == 1, replaced
    assert replaced['cfg'] == 1, replaced
    print('== done -> %s (%.1f MB) ==' % (args.dst, os.path.getsize(args.dst) / 1048576.0))
    print('   修改条目: %s' % replaced)


if __name__ == '__main__':
    main()
