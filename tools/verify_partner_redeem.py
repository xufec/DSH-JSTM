# -*- coding: utf-8 -*-
"""R86 验收：**神将兑换 → 伙伴进背包 → 可上场**（一条命令跑完）。

对应真实的客户端链路（`game/godredeem/godredeem_ctrl.luac`）：
    send_11216(partner_bid, state)  →  CS_11216{partner_bid:u32, state:u8}
    handle_11216(data): if data.code ~= 0 then openGainPanelByBid(...) end
    之后客户端拉 CS_10401（伙伴背包）应能看到该伙伴，CS_10402（单个伙伴）也应能取到
    ⇒ 这两个是"能不能上场"的前置（上场要按 bid 取到伙伴数据）。

用法：
    python tools/verify_partner_redeem.py [partner_bid]
"""
import io
import os
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from _login149 import login, pack_frame, recv_exact, w_str  # noqa: E402


def q(s, cmd, body=b''):
    s.sendall(pack_frame(cmd, body))
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        p = recv_exact(s, ln - 2)
        if rc == cmd:
            return p


def parse_hero_bag(b):
    """SC_10401{hero_bag:table(bid:I,color:C,lev:C,exp:I,state:C,chip:H,skill:T),
                hero_chip:table(bid:I,chip:H)}"""
    n = struct.unpack_from('>H', b, 0)[0]
    off = 2
    bag = []
    for _ in range(n):
        bid = struct.unpack_from('>I', b, off)[0]
        color = b[off + 4]
        lev = b[off + 5]
        exp = struct.unpack_from('>I', b, off + 6)[0]
        state = b[off + 10]
        chip = struct.unpack_from('>H', b, off + 11)[0]
        sk = struct.unpack_from('>H', b, off + 13)[0]
        off += 15 + sk * 4
        bag.append({'bid': bid, 'color': color, 'lev': lev, 'exp': exp,
                    'state': state, 'chip': chip, 'skills': sk})
    chips = struct.unpack_from('>H', b, off)[0]
    off += 2 + chips * 6
    return bag, off, len(b)


def main():
    # ★ 默认选一个**不在 config.json:heros 种子里**的伙伴，才能看出"新增"
    #   （种子里已有 17 个，其中就含 33100 唐舞桐 —— 拿它做验收会看不出变化）
    bid = int(sys.argv[1]) if len(sys.argv) > 1 else 31300     # 31300 龙傲天

    # ★★ 幂等：先把目标伙伴从背包里删掉，保证"兑换前"确实没有它。
    #   （否则第二次跑就会是 18→18，测试假失败 —— 一个只能通过一次的测试不算回归。）
    import urllib.request
    try:
        r = urllib.request.urlopen(
            'http://127.0.0.1:8080/DSH_ADMIN/hero?bid=%d&off=1' % bid, timeout=8)
        j = json.loads(r.read().decode('utf-8'))
        has = any(h.get('bid') == bid for h in (j.get('hero_bag') or []))
        print('前置清理: /DSH_ADMIN/hero?bid=%d&off=1 ⇒ 仍在背包=%s' % (bid, has))
    except Exception as e:
        print('前置清理失败（继续，可能首次运行）: %r' % (e,))

    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    rid = login(s)
    print('login rid = %s   目标伙伴 bid = %d' % (rid, bid))

    ok = True

    b = q(s, 10401)
    bag, used, ln = parse_hero_bag(b)
    before = {h['bid'] for h in bag}
    print('\n== 兑换前 SC_10401 ==')
    print('  hero_bag=%d  消耗=%d/%d  PASS=%s' % (len(bag), used, ln, used == ln))
    if used != ln:
        ok = False

    b = q(s, 11216, struct.pack('>I', bid) + b'\x00')
    code = b[0]
    n = struct.unpack_from('>H', b, 1)[0]
    msg = b[3:3 + n].decode('utf-8', 'replace')
    ret_bid = struct.unpack_from('>I', b, 3 + n)[0]
    print('\n== CS_11216{partner_bid=%d} ==' % bid)
    print('  SC_11216 code=%d msg=%r partner_bid=%d  (%d bytes)' % (code, msg, ret_bid, len(b)))
    print('  ★ 客户端 handle_11216: code~=0 才播获得动画；msg 必须为空')
    if code == 0 or msg != '' or ret_bid != bid:
        ok = False
    print('  PASS=%s' % (code != 0 and msg == '' and ret_bid == bid))

    b = q(s, 10401)
    bag2, used2, ln2 = parse_hero_bag(b)
    after = {h['bid'] for h in bag2}
    print('\n== 兑换后 SC_10401 ==')
    print('  hero_bag=%d → %d  消耗=%d/%d' % (len(bag), len(bag2), used2, ln2))
    gained = bid in after and bid not in before
    print('  bid %d 是否进入伙伴背包: %s' % (bid, '是' if bid in after else '否'))
    if not gained or used2 != ln2:
        ok = False

    b = q(s, 10402, struct.pack('>I', bid))
    print('\n== CS_10402{bid=%d}（单个伙伴，上场前要能取到）==' % bid)
    hb = struct.unpack_from('>H', b, 0)[0]     # ★ spec: SC_10402{bid:uint16, lev:uint8}（原先误读 u32）
    print('  SC_10402 bid=%d  (%d bytes)  PASS=%s' % (hb, len(b), hb == bid))
    if hb != bid:
        ok = False

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    s.close()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
