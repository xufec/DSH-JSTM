#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1 探针：从 UI luac 中能提取到什么（验证可行性，再决定 UI 索引用哪条路）。

目标信号：
  1. 字符串常量表（kgc）—— 函数名/回调名/资源名
  2. `RegisterProtocal(N, 'handler')` 配对 —— 该面板绑定的协议与回调
  3. 按钮/点击相关标识（getBtnRes / addClickEventListener / setTouchEnabled / onClick…）
  4. 协议发送调用（SendProtocal / GetPrototype(N)）—— 该面板主动发的协议号
"""
import os
import re
import sys
import zipfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_bc import parse_bytes, TableConst  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')

TARGETS = [
    'assets/src/game/achieve/achieve_panel.luac',
    'assets/src/game/mission/mission_ctrl.luac',
    'assets/src/game/role/new_ui/role_show_panel.luac',
]

BTN_HINT = re.compile(
    r'(getBtnRes|addClickEventListener|setTouchEnabled|onClick|Btn|Button|'
    r'ClickEventListener|TouchEnded|handleBtn|clickBtn)', re.I)
NET_HINT = re.compile(r'(SendProtocal|GetPrototype|RegisterProtocal|send\d{3,6}|handle\d{3,6})')


def all_strings(r):
    out = []
    for pt in r.protos:
        for k in (getattr(pt, 'kgc', None) or []):
            if isinstance(k, str):
                out.append(k)
    return out


def main():
    z = zipfile.ZipFile(APK)
    around = re.compile(r'(\d{4,6})')
    for t in TARGETS:
        try:
            r = parse_bytes(z.read(t))
        except Exception as e:
            print('%-60s PARSE FAIL %r' % (t, e))
            continue
        ss = all_strings(r)
        uniq = sorted(set(ss))
        protos = sum(len(getattr(p, 'protos', []) or []) for p in [r]) if False else len(r.protos)
        ver = getattr(r, 'version', '?')
        reg = sorted({n for n in uniq if re.fullmatch(r'handle\d{3,6}', n)})
        snd = sorted({n for n in uniq if re.fullmatch(r'send(er)?\d{3,6}', n)})
        btn = sorted({n for n in uniq if BTN_HINT.search(n)})[:12]
        print('=' * 78)
        print('%s' % t)
        print('  version=%s protos=%d strings=%d(uniq %d)' % (ver, protos, len(ss), len(uniq)))
        print('  handle*: %s' % reg[:14])
        print('  send*  : %s' % snd[:14])
        print('  按钮相关: %s' % btn)
    z.close()


if __name__ == '__main__':
    main()
