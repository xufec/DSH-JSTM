#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小改动打包器 —— 只改一个变量。

本脚本与 tools/patch_apk.py 的区别（重要）：
  patch_apk.py 会同时做 8 个网关 URL 替换 + 大段 Lua 注入；
  本脚本 **只** 替换 assets/src/config.luac 里的 URL_LUA_CONFIG 字面量，
  其余 19k 个 zip 条目逐字节原样复制。

为什么改这里就够了（证据）：
  * config.luac 是**明文 Lua**（非 LuaJIT 字节码），由 main.luac 的
    loadConfig() 在 main() 之前 require —— 是整个启动流程里最早的可配置点；
  * 启动阻塞点就是这个字面量指向的 CDN 域名已停服（DNS 解析失败，
    原生下载器返回 code 6），客户端进入 0.2s 无上限重试循环，永不进登录页。

用法：
  python tools/patch_url_only.py <in.apk> <out.apk> --base http://10.0.2.2:8080
"""
import argparse
import os
import sys
import zipfile

CONFIG_ENTRY = 'assets/src/config.luac'
ORIG_URL = 'https://cdn.jstm.ewan.cn/update/config/url_config_ewan.lua'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--base', required=True,
                    help='本地配置服务器基地址，例如 http://10.0.2.2:8080')
    ap.add_argument('--entry', default=CONFIG_ENTRY)
    args = ap.parse_args()

    new_url = args.base.rstrip('/') + '/update/config/url_config_ewan.lua'

    zin = zipfile.ZipFile(args.src, 'r')
    try:
        names = zin.namelist()
        if args.entry not in names:
            sys.exit('FATAL: %s not found in %s' % (args.entry, args.src))
        raw = zin.read(args.entry)
    finally:
        pass

    text = raw.decode('utf-8')
    hits = text.count(ORIG_URL)
    print('== 目标条目 %s (%d bytes, 压缩后 %d) =='
          % (args.entry, len(raw), zin.getinfo(args.entry).compress_size))
    print('   原始 URL 出现次数: %d' % hits)
    if hits != 1:
        sys.exit('FATAL: 期望恰好 1 处 URL_LUA_CONFIG，实际 %d 处；拒绝继续' % hits)

    patched_text = text.replace(ORIG_URL, new_url)
    patched = patched_text.encode('utf-8')

    # 打印唯一一处 diff，作为"只改一个变量"的证据
    old_line = [l for l in text.splitlines() if ORIG_URL in l][0]
    new_line = [l for l in patched_text.splitlines() if new_url in l][0]
    print('   - %s' % old_line.strip())
    print('   + %s' % new_line.strip())
    print('   字节数: %d -> %d' % (len(raw), len(patched)))

    # 复制整包，只替换这一个条目
    if os.path.exists(args.dst):
        os.remove(args.dst)
    zout = zipfile.ZipFile(args.dst, 'w', zipfile.ZIP_DEFLATED)
    replaced = 0
    try:
        for item in zin.infolist():
            data = patched if item.filename == args.entry else zin.read(item.filename)
            if item.filename == args.entry:
                replaced += 1
            zi = zipfile.ZipInfo(item.filename, date_time=item.date_time)
            zi.compress_type = item.compress_type
            zi.external_attr = item.external_attr
            zi.internal_attr = item.internal_attr
            zi.create_system = item.create_system
            zout.writestr(zi, data)
    finally:
        zout.close()
        zin.close()

    print('   替换条目数: %d ; 写出 %s (%.1f MB)'
          % (replaced, args.dst, os.path.getsize(args.dst) / 1048576.0))
    assert replaced == 1, 'unexpected replacement count'
    print('RESULT: PASS (仅 1 个条目被修改)')


if __name__ == '__main__':
    main()
