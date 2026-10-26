"""直连 TCP 验证「限购/已购」：
  ① SC_12801 的 can_buy_num 是否按 原版 limit_week − 已购 推导
  ② 买满限购后是否被服务端拒绝（SC_12805 code=0 + 非空 msg）
  ③ SC_12831 的 has_buy_num 是否随之更新
  ④ 再次取 12801，确认 can_buy_num 归零

用法：python tools/shop_limit_test.py [goods_id]   # 默认 20007（limit_week=1，价 21）
"""
import socket
import struct
import sys
import time

HOST, PORT = '127.0.0.1', 9000
GID = int(sys.argv[1]) if len(sys.argv) > 1 else 20007
WATCH = [GID, 20006, 20008, 2001]


def frame(cmd, body=b''):
    payload = struct.pack('>H', cmd) + body
    return struct.pack('>I', len(payload)) + payload


def read_frames(sock, seconds=2.0):
    sock.settimeout(0.6)
    buf, out = b'', []
    end = time.time() + seconds
    while time.time() < end:
        try:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        except socket.timeout:
            if out:
                break
            continue
        while len(buf) >= 6:
            ln = struct.unpack_from('>I', buf, 0)[0]
            if len(buf) < 4 + ln:
                break
            out.append((struct.unpack_from('>H', buf, 4)[0], buf[6:4 + ln]))
            buf = buf[4 + ln:]
    return out


def parse_12801(body):
    """SC_12801{guild_shop_lev:u32, xs_list:table(id:u16, item_bid:u32, bind:u8,
    pay_type:u8, old_price:u32, price:u32, type:u8, ico:u8, left_time:u32, can_buy_num:u16)}"""
    n = struct.unpack_from('>H', body, 4)[0]
    off, items = 6, {}
    for _ in range(n):
        gid = struct.unpack_from('>H', body, off)[0]
        items[gid] = {
            'item_bid': struct.unpack_from('>I', body, off + 2)[0],
            'pay_type': body[off + 7],
            'price': struct.unpack_from('>I', body, off + 12)[0],
            'can_buy_num': struct.unpack_from('>H', body, off + 22)[0],
        }
        off += 24
    return items


def parse_12805(body):
    code = body[0]
    mlen = struct.unpack_from('>H', body, 1)[0]
    msg = body[3:3 + mlen].decode('utf-8', 'replace')
    off = 3 + mlen
    gid, num, price = struct.unpack_from('>HHI', body, off)
    return {'code': code, 'msg': msg, 'id': gid, 'num': num, 'price': price}


def parse_12831(body):
    n = struct.unpack_from('>H', body, 0)[0]
    return {struct.unpack_from('>HH', body, 2 + i * 4)[0]:
            struct.unpack_from('>HH', body, 2 + i * 4)[1] for i in range(n)}


def ask(s, cmd, body=b'', sec=2.0):
    s.sendall(frame(cmd, body))
    return read_frames(s, sec)


s = socket.create_connection((HOST, PORT), timeout=5)
print('已连接 %s:%d ；测试商品 id=%d' % (HOST, PORT, GID))

print('\n① 初始 SC_12801 的 can_buy_num（原版 limit_week − 已购）:')
for c, b in ask(s, 12801):
    if c == 12801:
        items = parse_12801(b)
        for gid in WATCH:
            it = items.get(gid)
            if it:
                print('    id=%-6s price=%-6s pay=%-3s can_buy_num=%s'
                      % (gid, it['price'], it['pay_type'], it['can_buy_num']))
        print('    （134 条里 can_buy_num>0 的：%s）'
              % [(k, v['can_buy_num']) for k, v in items.items() if v['can_buy_num']][:12])

print('\n② 连续购买 id=%d（限购用尽后应被拒绝）:' % GID)
for i in (1, 2, 3):
    got = []
    for c, b in ask(s, 12805, struct.pack('>HH', GID, 1), 2.5):
        if c == 12805:
            got.append(parse_12805(b))
        elif c == 12831:
            n31 = parse_12831(b)
            got.append('SC_12831 has_buy_num[%d]=%s' % (GID, n31.get(GID)))
        elif c == 10500:
            got.append('SC_10500 bag push bag_code=%d items=%d'
                       % (b[0], struct.unpack_from('>H', b, 1)[0]))
    for x in got:
        print('    第%d次: %s' % (i, x))

print('\n③ SC_12831 的 has_buy_num:')
for c, b in ask(s, 12831):
    if c == 12831:
        m = parse_12831(b)
        print('    共 %d 条；%s' % (len(m), {g: m.get(g) for g in WATCH}))

print('\n④ 复取 SC_12801，确认 can_buy_num 已减/归零:')
for c, b in ask(s, 12801):
    if c == 12801:
        items = parse_12801(b)
        for gid in WATCH:
            it = items.get(gid)
            if it:
                print('    id=%-6s can_buy_num=%s' % (gid, it['can_buy_num']))

s.close()
print('\n完成')
