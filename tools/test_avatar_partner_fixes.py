# -*- coding: utf-8 -*-
"""头像/伙伴/回包 修复的回归测试（PHASE 2.23~2.29）。

覆盖：
  · 10325 头像列表 = config_role_face.RoleFace 的 id（100..113，14 项）
  · 10327 更换头像 = {code:u8, msg:s, face_id:u16}
  · 10341 保存自定义头像 = {rid:u32, srv_id:s, id:u32, img:bytes, upload_time:u32}
           （★ img 曾是 fields.json 里被误标的 `bool` ⇒ 少 1 字节 ⇒ 全错位）
  · 11215 伙伴面板 = {volume:u8, volume_open:u8, partner_bag:表}
           （★ 原缺前 2 字节 ⇒ 整表错位 ⇒ 面板空白）
  · 13036 镇魂塔设置 = 回 {key:u8, value:u8}（0,0），**不再不回包**

用法：python tools/test_avatar_partner_fixes.py [--port 9000]
"""
import socket
import struct
import sys
import argparse
import os
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def frame(cmd, body=b''):
    p = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(p)) + p


class C:
    def __init__(self, host, port):
        self.s = socket.create_connection((host, port), timeout=10)
        self.buf = bytearray()
    def call(self, cmd, body=b'', maxskip=80):
        self.s.sendall(frame(cmd, body))
        for _ in range(maxskip):
            while len(self.buf) < 4:
                self.buf.extend(self.s.recv(65536))
            ln = struct.unpack('>I', bytes(self.buf[:4]))[0]
            while len(self.buf) < 4 + ln:
                self.buf.extend(self.s.recv(65536))
            pay = bytes(self.buf[4:4 + ln])
            del self.buf[:4 + ln]
            if struct.unpack('>H', pay[:2])[0] == cmd:
                return pay[2:]
        return None


def args_login(acc):
    pairs = [('account', acc), ('platform', 'ewan')]
    out = struct.pack('>H', len(pairs))
    for k, v in pairs:
        kb, vb = k.encode(), v.encode()
        out += struct.pack('>H', len(kb)) + kb + struct.pack('>H', len(vb)) + vb
    return out


F = []
def ck(n, c, e=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + e) if e else ''))
    if not c:
        F.append(n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    a = ap.parse_args()

    c = C(a.host, a.port)
    c.call(1110, args_login('dsh_local'))
    c.call(10102, struct.pack('>I', 1001))
    print('connected %s:%d' % (a.host, a.port))

    print('\n[1] 10325 头像列表 = RoleFace 的 id（100..113）')
    rf = json.load(open(os.path.join(ROOT, 'server', 'cfg', 'config_role_face.json'),
                        encoding='utf-8')).get('RoleFace') or {}
    want = sorted(int(k) for k in rf.keys())
    b = c.call(10325, b'')
    n = struct.unpack_from('>H', b, 0)[0]
    ids = [struct.unpack_from('>H', b, 2 + 2 * i)[0] for i in range(n)]
    ck('10325 条数 == RoleFace 项数', n == len(want), 'n=%d want=%d' % (n, len(want)))
    ck('10325 id 集合 == RoleFace 键', ids == want, 'ids=%s' % ids[:6])
    ck('10325 不含头像框 id(10107..)', not any(i >= 10100 for i in ids), 'ids=%s' % ids[:6])

    print('\n[2] 10327 更换头像 = {code,msg,face_id}')
    b = c.call(10327, struct.pack('>H', 101))
    code = b[0]
    sl = struct.unpack_from('>H', b, 1)[0]
    fid = struct.unpack_from('>H', b, 3 + sl)[0]
    ck('10327 face_id 回显 == 请求', fid == 101, 'code=%d face_id=%d' % (code, fid))
    ck('10327 总长 == 1+2+len(msg)+2', len(b) == 1 + 2 + sl + 2, 'len=%d sl=%d' % (len(b), sl))

    print('\n[3] 10341 保存自定义头像 = {rid,srv_id,id,img:bytes,upload_time}')
    b = c.call(10341, b'')
    o = 0
    rid = struct.unpack_from('>I', b, o)[0]; o += 4
    sl = struct.unpack_from('>H', b, o)[0]; o += 2 + sl
    iid = struct.unpack_from('>I', b, o)[0]; o += 4
    il = struct.unpack_from('>H', b, o)[0]; o += 2 + il     # ★ img 变长（字节数组）
    ut = struct.unpack_from('>I', b, o)[0]; o += 4
    ck('10341 按 bytes 布局精确解析', o == len(b), '消耗=%d/%d' % (o, len(b)))
    ck('10341 长度 >= 16（img 未被当 1 字节 bool）', len(b) >= 16, 'len=%d' % len(b))

    print('\n[4] 11215 伙伴面板 = {volume,volume_open,partner_bag}')
    b = c.call(11215, b'')
    vol = b[0]; volo = b[1]; cnt = struct.unpack_from('>H', b, 2)[0]
    ck('11215 以 volume/volume_open 开头（非直接表计数）', len(b) > 2 and cnt <= len(b),
       'volume=%d volume_open=%d bag=%d len=%d' % (vol, volo, cnt, len(b)))
    ck('11215 前 2 字节非"表计数的高低位"', (vol, volo) != (0, 0) or cnt == 0,
       'vol=%d volo=%d cnt=%d' % (vol, volo, cnt))

    print('\n[5] 13036 镇魂塔设置：**必须回包** {key,value}')
    b = c.call(13036, bytes.fromhex('00009c41010100008959'))
    ck('13036 有回包', b is not None, 'None=不回包(不合格)')
    if b is not None:
        ck('13036 回 {key,value} = 2 字节', len(b) == 2, 'len=%d %s' % (len(b), b.hex(' ')))

    print('\n==== %s ====' % ('ALL PASS' if not F else ('FAILED: %s' % F)))
    return 1 if F else 0


if __name__ == '__main__':
    sys.exit(main())
