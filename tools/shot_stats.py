#!/usr/bin/env python3
"""Objective screenshot stats: is the frame mostly blank/black or rich?

Usage: python tools/shot_stats.py <png> [<png> ...]
"""
import sys, zlib, struct

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def read_png(path):
    data = open(path, 'rb').read()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
    pos, idat, w, h, bitd, ctype = 8, b'', 0, 0, 8, 6
    while pos < len(data):
        ln = struct.unpack('>I', data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + ln]
        if typ == b'IHDR':
            w, h, bitd, ctype = struct.unpack('>IIBB', body[:10])
        elif typ == b'IDAT':
            idat += body
        elif typ == b'IEND':
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    stride = w * ch
    out, prev = [], bytearray(stride)
    p = 0
    for _ in range(h):
        f = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out.append(bytes(line))
        prev = line
    return w, h, ch, out


def stats(path):
    w, h, ch, rows = read_png(path)
    tot = w * h
    dark = 0
    colors = {}
    rs = gs = bs = 0
    step = max(1, h // 240)          # sample every few rows
    n = 0
    for y in range(0, h, step):
        row = rows[y]
        for x in range(0, w, 4):
            i = x * ch
            r, g, b = row[i], row[i + 1], row[i + 2]
            rs += r; gs += g; bs += b
            n += 1
            if r + g + b < 45:
                dark += 1
            key = (r >> 4, g >> 4, b >> 4)
            colors[key] = colors.get(key, 0) + 1
    print('%s  %dx%d ch=%d' % (path, w, h, ch))
    print('   sampled=%d  mean_rgb=(%d,%d,%d)' % (n, rs // n, gs // n, bs // n))
    print('   near_black=%.1f%%   distinct_16bit_colors=%d' %
          (100.0 * dark / n, len(colors)))
    top = sorted(colors.items(), key=lambda kv: -kv[1])[:5]
    print('   top colors (r16,g16,b16)->share: %s' %
          ', '.join('%s=%.0f%%' % (k, 100.0 * v / n) for k, v in top))


if __name__ == '__main__':
    for p in sys.argv[1:]:
        try:
            stats(p)
        except Exception as e:
            print('%s: ERROR %s' % (p, e))