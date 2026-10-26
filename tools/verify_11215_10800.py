# -*- coding: utf-8 -*-
"""验证 11215/10800 新分支的字节流编码与 protocol/fields.json 规格一致。

用法：python tools/verify_11215_10800.py
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if v.get('cmd') == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def read_str(buf, off):
    (n,) = struct.unpack_from('>H', buf, off)
    return buf[off + 2:off + 2 + n], off + 2 + n


def read_u8(buf, off):
    return buf[off], off + 1


def read_u16(buf, off):
    (v,) = struct.unpack_from('>H', buf, off)
    return v, off + 2


def read_u32(buf, off):
    (v,) = struct.unpack_from('>I', buf, off)
    return v, off + 4


def parse_fields(buf, fields, path=''):
    off = 0
    out = []
    for i, f in enumerate(fields):
        nm = f.get('name', '')
        ty = (f.get('type') or '').lower()
        p = path + '.' + nm
        if ty.startswith('string'):
            s, off = read_str(buf, off)
            out.append((p, 'string', s))
        elif ty.startswith('table'):
            n, off = read_u16(buf, off)
            out.append((p, 'table', n))
        elif '64' in ty:
            if 'int' in ty or 'u' in ty:
                v = struct.unpack_from('>Q', buf, off)[0]
                off += 8
            else:
                v = struct.unpack_from('>q', buf, off)[0]
                off += 8
            out.append((p, ty, v))
        elif '32' in ty:
            v = struct.unpack_from('>I', buf, off)[0]
            off += 4
            out.append((p, ty, v))
        elif '16' in ty:
            v, off = read_u16(buf, off)
            out.append((p, ty, v))
        else:  # 8 / bool / char
            v, off = read_u8(buf, off)
            out.append((p, ty, v))
    return out, off


def build_11215():
    with open(os.path.join(ROOT, 'server', '_partner_base.json'), encoding='utf-8') as f:
        base = json.load(f)
    out = struct.pack('>H', len(base))
    for i, p in enumerate(base, 1):
        out += struct.pack('>I', i)                    # id
        out += struct.pack('>I', int(p.get('bid', 0)))
        out += struct.pack('>B', 0)                    # type
        out += struct.pack('>B', int(p.get('color', 0)) & 0xff)
        out += struct.pack('>I', 0)                    # lifttime
        out += struct.pack('>B', 1)                    # lev
        out += struct.pack('>I', 0)                    # exp
        out += struct.pack('>H', 0)                    # grow
        out += struct.pack('>I', int(p.get('score', 0)))
        out += struct.pack('>B', 0)                    # stage
        out += struct.pack('>B', 0)                    # rebirth
        out += struct.pack('>B', 0)                    # acc
        out += struct.pack('>H', 0)                    # partner_attr table
        out += struct.pack('>I', 0)                    # power
        out += struct.pack('>H', 0)                    # aptitude table
        out += struct.pack('>I', int(p.get('innate_skill', 0)))
        out += struct.pack('>H', 0)                    # skill table
        out += struct.pack('>H', 0)                    # jindan_skill table
        out += struct.pack('>H', 0)                    # talisman_skill table
        out += struct.pack('>H', 0)                    # ext table
    return out


def build_10800():
    import time
    now = int(time.time()) & 0xFFFFFFFF
    out = struct.pack('>H', 1)                        # mail count
    out += struct.pack('>I', 1)                       # id
    out += struct.pack('>H', len('系统'.encode('utf-8'))) + '系统'.encode('utf-8')
    out += struct.pack('>H', len('欢迎来到绝世唐门'.encode('utf-8'))) + '欢迎来到绝世唐门'.encode('utf-8')
    out += struct.pack('>H', len('欢迎来到单机私服！祝你游戏愉快。\n附件是新手小礼，请查收。'.encode('utf-8'))) + \
        '欢迎来到单机私服！祝你游戏愉快。\n附件是新手小礼，请查收。'.encode('utf-8')
    out += struct.pack('>H', 0)                       # assets table
    out += struct.pack('>H', 1)                       # items count
    out += struct.pack('>I', 10007) + struct.pack('>B', 2)
    out += struct.pack('>I', now) + struct.pack('>I', 0) + struct.pack('>I', 0)
    return out


# 子表内部规格（来自 protocol/manual.md，已用 dsc_spec 解明字段顺序）
# 每个元素用 (类型, 名字) 元组列表描述；table 元素为 ('table', 子表名)，
# 子表名为空字符串表示该表发空表（count=0），无需解析内容。
SUB_SPEC = {
    '11215.partner_list': [
        ('uint32', 'id'), ('uint32', 'bid'), ('uint8', 'type'), ('uint8', 'color'),
        ('uint32', 'lifttime'), ('uint8', 'lev'), ('uint32', 'exp'), ('uint16', 'grow'),
        ('uint32', 'score'), ('uint8', 'stage'), ('uint8', 'rebirth'), ('uint8', 'acc'),
        ('table', ''), ('uint32', 'power'), ('table', ''), ('uint32', 'innate_skill'),
        ('table', ''), ('table', ''), ('table', ''), ('table', ''),
    ],
    '10800.mail': [
        ('uint32', 'id'), ('string', 'from_name'), ('string', 'subject'),
        ('string', 'content'), ('table', 'assets'), ('table', 'items'),
        ('uint32', 'send_time'), ('uint32', 'read_time'), ('uint32', 'time_out'),
    ],
    '10800.assets': [('uint8', 'label'), ('uint32', 'val')],
    '10800.items': [('uint32', 'bid'), ('uint8', 'quantity')],
}


def parse_one(buf, spec, off, path=''):
    """按 SUB_SPEC 解析一条记录，返回 (字段值列表, 新 off)。"""
    vals = []
    for ty, nm in spec:
        if ty == 'string':
            s, off = read_str(buf, off)
            vals.append(('string', s))
        elif ty == 'table':
            n, off = read_u16(buf, off)
            child = SUB_SPEC.get(path + '.' + nm) if nm else None
            if n and child:
                rows = []
                for _ in range(n):
                    row, off = parse_one(buf, child, off, path + '.' + nm)
                    rows.append(row)
                vals.append(('table[%d]' % n, rows))
            else:
                vals.append(('table', n))
        elif ty == 'uint8':
            v, off = read_u8(buf, off)
            vals.append(('uint8', v))
        elif ty == 'uint16':
            v, off = read_u16(buf, off)
            vals.append(('uint16', v))
        elif ty == 'uint32':
            v, off = read_u32(buf, off)
            vals.append(('uint32', v))
    return vals, off


def main():
    ok = True
    for cmd, body in (('11215', build_11215()), ('10800', build_10800())):
        spec = sc_spec(cmd)
        if not spec:
            print('!! cmd %s 无 SC 规格' % cmd)
            ok = False
            continue
        try:
            parsed, used = parse_fields(body, spec)
        except Exception as e:
            print('!! cmd %s 解析失败: %r' % (cmd, e))
            ok = False
            continue
        print('== SC_%s 规格 %d 字段, body %d 字节' % (cmd, len(spec), len(body)))
        # 顶层只有 1 个 table 字段，按子表规格逐条解析
        subkey = cmd + '.' + spec[0]['name']
        subspec = SUB_SPEC.get(subkey)
        if subspec is None:
            print('   !! 缺少子表规格 %s' % subkey)
            ok = False
            continue
        n, off = read_u16(body, 0)
        print('   顶层 %s = %d 条, 子表规格 %s (%d 字段/条)' %
              (spec[0]['name'], n, subkey, len(subspec)))
        for idx in range(n):
            vals, off = parse_one(body, subspec, off, cmd)
            sample = ', '.join('%s=%r' % (subspec[i][1], v)
                               for i, (_t, v) in enumerate(vals))
            if idx < 3 or n - idx <= 1:
                print('   #%d %s' % (idx + 1, sample))
            elif idx == 3:
                print('   ...')
        if off != len(body):
            print('   ⚠ 解析未消耗完: %d/%d' % (off, len(body)))
            ok = False
        else:
            print('   ✓ 字节流完整消费, 逐字段顺序正确')
    print('\n结果:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()

