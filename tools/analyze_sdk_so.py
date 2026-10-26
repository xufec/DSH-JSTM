#!/usr/bin/env python3
"""Extract readable strings from libsupersdkjni.so (Bangcle Java2C target).

The whole cn.ewan.supersdk implementation is JNI-stubbed
(com.bangcle.andJni.JniLib1508990063), so the dialog literals live in this .so
rather than the dex.  This lists every UTF-8 run containing CJK, with offsets,
plus byte windows for eyeballing.

usage:
  python tools/analyze_sdk_so.py cjk [minlen]
  python tools/analyze_sdk_so.py window <start> <end>
  python tools/analyze_sdk_so.py ascii <needle>
"""
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APK = os.path.join(ROOT, 'anzbao', 'jstm_142165.apk')
SO = 'lib/armeabi/libsupersdkjni.so'

CJK = re.compile(('[\u3000-\u9fff\uff00-\uffef]').encode('utf-8').decode('latin-1'))


def load():
    return zipfile.ZipFile(APK).read(SO)


def cmd_cjk(d, minlen):
    # Walk the buffer, greedily collecting printable non-ASCII-ish runs.
    out = []
    i = 0
    n = len(d)
    while i < n:
        b = d[i]
        if b >= 0x80:
            j = i
            while j < n and d[j] >= 0x20 and d[j] != 0x7f:
                j += 1
            if j - i >= minlen:
                try:
                    s = d[i:j].decode('utf-8')
                    if any('\u3000' <= c <= '\uffef' for c in s):
                        out.append((i, s))
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    for off, s in out:
        print('%8d %r' % (off, s))
    print('-- total %d CJK runs' % len(out))


def cmd_window(d, lo, hi):
    for off in range(lo, hi, 16):
        chunk = d[off:off + 16]
        printable = ''.join(chr(c) if 0x20 <= c < 0x7f else '.' for c in chunk)
        try:
            u = chunk.decode('utf-8')
            u = ''.join(c if (c.isprintable()) else '.' for c in u)
        except UnicodeDecodeError:
            u = ''
        print('%8d  %-32s %s' % (off, printable, u))


def cmd_ascii(d, needle):
    nb = needle.encode('utf-8') if not needle.startswith('\\u') else \
        needle.encode('ascii', 'surrogateescape').decode('unicode_escape').encode('utf-8')
    i = d.find(nb)
    while i >= 0:
        print('%8d %s' % (i, d[max(0, i - 24):i + 64]))
        i = d.find(nb, i + 1)


def main():
    d = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'cjk'
    print('# %s: %d bytes' % (SO, len(d)))
    if cmd == 'cjk':
        cmd_cjk(d, int(sys.argv[2]) if len(sys.argv) > 2 else 6)
    elif cmd == 'window':
        cmd_window(d, int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == 'ascii':
        cmd_ascii(d, sys.argv[2])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
