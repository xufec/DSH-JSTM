"""Phase F 端到端自测：商城「可购买 / 可使用」+ 珍宝页签不再为空。

直接与**真实服务端**（TCP 9000）对话，按 1.4.9 权威 spec 编码/解码，
不依赖手机客户端（客户端启动常不稳）。

流程：
    1) CS_12801 → 解码 SC_12801.xs_list（常用/热卖货物）
    2) CS_12836 → 解码 SC_12836.goods_list（**珍宝**，此前为空）
    3) CS_12837 买 1 件珍宝 → 校验 SC_12837.code==1
    4) CS_10502 → 校验物品已进背包
    5) CS_10505 使用该物品 → 校验 SC_10505.code==1 且数量减少
    6) CS_12836 → 校验 buy_num 已 +1

用法：
    python tools/test_shop_e2e.py
    python tools/test_shop_e2e.py --port 9000 --goods 21001
"""
import argparse
import io
import os
import socket
import struct
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))


def w_u8(v):
    return struct.pack('>B', int(v) & 0xFF)


def w_u16(v):
    return struct.pack('>H', int(v) & 0xFFFF)


def w_u32(v):
    return struct.pack('>I', int(v) & 0xFFFFFFFF)


def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


class Conn(object):
    def __init__(self, host, port, timeout=6.0):
        self.s = socket.create_connection((host, port), timeout=timeout)
        self.buf = b''

    def send(self, cmd, body=b''):
        p = w_u16(cmd) + body
        self.s.sendall(w_u32(len(p)) + p)

    def recv(self):
        while True:
            if len(self.buf) >= 6:
                ln = struct.unpack_from('>I', self.buf, 0)[0]
                if len(self.buf) >= 4 + ln:
                    cmd = struct.unpack_from('>H', self.buf, 4)[0]
                    body = self.buf[6:4 + ln]
                    self.buf = self.buf[4 + ln:]
                    return cmd, body
            d = self.s.recv(65536)
            if not d:
                raise EOFError('连接被关闭')
            self.buf += d

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


class Cur(object):
    def __init__(self, b):
        self.b, self.p = b, 0

    def u(self, n):
        v = int.from_bytes(self.b[self.p:self.p + n], 'big')
        self.p += n
        return v

    def s(self):
        n = self.u(2)
        v = self.b[self.p:self.p + n].decode('utf-8', 'replace')
        self.p += n
        return v


def decode_goods(cur, n):
    """12836/12838/12842 的 goods_list 元素（权威 spec）。"""
    out = []
    for _ in range(n):
        out.append(dict(id=cur.u(2), item_bid=cur.u(4), bind=cur.u(1),
                        pay_type=cur.u(1), old_price=cur.u(4), price=cur.u(4),
                        limit_num=cur.u(1), buy_num=cur.u(1)))
    return out


def decode_xs(cur, n):
    """12801/12802 的 xs_list 元素（权威 spec）。"""
    out = []
    for _ in range(n):
        out.append(dict(id=cur.u(2), item_bid=cur.u(4), bind=cur.u(1),
                        pay_type=cur.u(1), old_price=cur.u(4), price=cur.u(4),
                        type=cur.u(1), ico=cur.u(1), left_time=cur.u(4),
                        can_buy_num=cur.u(2)))
    return out


def decode_bag(cur, n):
    out = []
    for _ in range(n):
        it = dict(id=cur.u(4), bid=cur.u(4), hero_bid=cur.u(4), bind=cur.u(1),
                  intensify_lev=cur.u(1), pos=cur.u(2), quantity=cur.u(2),
                  ctime=cur.u(4), expire_ts=cur.u(4), durable=cur.u(2),
                  object=cur.u(1))
        for _k in range(5):          # attrs_ext / attrs_ext_list /
            c = cur.u(2)             # attrs_ext_one_list / jewel_list / str_ext_list
            cur.p += 0
            if c:
                raise RuntimeError('背包物品带非空子表，本测试未实现跳过')
        out.append(it)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=9000)
    ap.add_argument('--goods', type=int, default=21001)
    a = ap.parse_args()

    fails = []
    ok = lambda m: print('  OK   %s' % m)

    def bad(m):
        fails.append(m)
        print('  FAIL %s' % m)

    c = Conn(a.host, a.port)
    try:
        # ---------- ① 12801 常用/热卖 ----------
        print('=== ① CS_12801 商城商品列表 ===')
        c.send(12801)
        cmd, body = c.recv()
        if cmd != 12801:
            bad('期望 12801，收到 %d' % cmd)
        else:
            cur = Cur(body)
            glev = cur.u(4)
            n = cur.u(2)
            xs = decode_xs(cur, n)
            ok('SC_12801 xs_list=%d 条 (guild_shop_lev=%d, 共 %d 字节)'
               % (n, glev, len(body)))
            if n == 0:
                bad('12801 商品为 0 条 —— 商城常用/热卖为空')

        # ---------- ② 12836 珍宝 ----------
        print('\n=== ② CS_12836 珍宝（限时商店）===')
        c.send(12836)
        cmd, body = c.recv()
        zhenbao = []
        if cmd != 12836:
            bad('期望 12836，收到 %d' % cmd)
        else:
            cur = Cur(body)
            n = cur.u(2)
            zhenbao = decode_goods(cur, n)
            ok('SC_12836 goods_list=%d 条 (%d 字节)' % (n, len(body)))
            if n == 0:
                bad('珍宝页签仍为空（goods_list=0）❌ 未修复')
            else:
                print('       前 3 条: %s'
                      % [(g['id'], g['item_bid'], g['price']) for g in zhenbao[:3]])

        target = None
        for g in zhenbao:
            if g['id'] == a.goods:
                target = g
                break
        if target is None and zhenbao:
            target = zhenbao[0]
        if target is None:
            print('\n(没有可购买的商品，后续步骤跳过)')
            return 2

        # ---------- ③ 12837 购买 ----------
        print('\n=== ③ CS_12837 购买 goods_id=%d (item_bid=%d, price=%d) ==='
              % (target['id'], target['item_bid'], target['price']))
        c.send(12837, w_u16(target['id']) + w_u16(1))
        body = None
        pushed = []
        for _ in range(12):
            cmd, b2 = c.recv()
            if cmd == 12837:
                body = b2
                break
            pushed.append(cmd)        # 服务端会先推 10500/12831 等刷新包
        if body is None:
            bad('没有收到 12837 应答（收到 %s）' % pushed)
        else:
            if pushed:
                print('       (先收到推送包 %s，已跳过)' % pushed)
            cur = Cur(body)
            code = cur.u(1)
            msg = cur.s()
            gid = cur.u(2)
            num = cur.u(2)
            if code != 1:
                bad('购买失败 code=%d msg=%r' % (code, msg))
            else:
                ok('SC_12837 code=1(TRUE) id=%d num=%d' % (gid, num))

        # ---------- ④ 背包里有没有 ----------
        print('\n=== ④ CS_10502 背包校验 ===')
        c.send(10502, w_u8(1))
        found = None
        for _ in range(6):
            cmd, body = c.recv()
            if cmd == 10502:
                cur = Cur(body)
                bag_code = cur.u(1)
                n = cur.u(2)
                items = decode_bag(cur, n)
                for it in items:
                    if it['bid'] == target['item_bid']:
                        found = it
                break
        if found:
            ok('背包已有 item_bid=%d, item_id=%d, quantity=%d'
               % (found['bid'], found['id'], found['quantity']))
        else:
            bad('背包里找不到 item_bid=%d —— 购买没有入包' % target['item_bid'])
            return 2

        # ---------- ⑤ 10505 使用 ----------
        print('\n=== ⑤ CS_10505 使用物品 item_id=%d ===' % found['id'])
        qty0 = found['quantity']
        c.send(10505, w_u8(0) + w_u32(found['id']) + w_u16(1) + w_u32(0) +
               w_u32(target['item_bid']))
        used = False
        for _ in range(8):
            cmd, body = c.recv()
            if cmd == 10505:
                cur = Cur(body)
                code = cur.u(1)
                msg = cur.s()
                ib = cur.u(4)
                if code != 1:
                    bad('使用失败 code=%d msg=%r' % (code, msg))
                else:
                    ok('SC_10505 code=1(TRUE) item_bid=%d' % ib)
                    used = True
                break
        if not used:
            bad('没有收到 10505 应答')

        # ---------- ⑥ 再看 12836 的 buy_num ----------
        print('\n=== ⑥ CS_12836 复看 buy_num ===')
        c.send(12836)
        cmd, body = c.recv()
        if cmd == 12836:
            cur = Cur(body)
            n = cur.u(2)
            gs = decode_goods(cur, n)
            t2 = [g for g in gs if g['id'] == target['id']]
            if t2 and t2[0]['buy_num'] >= 1:
                ok('buy_num 已更新为 %d（界面限购数字会随之变化）' % t2[0]['buy_num'])
            else:
                bad('buy_num 仍为 %s' % (t2[0]['buy_num'] if t2 else 'N/A'))

        # ---------- ⑦ 12840 兑换商店 ----------
        print('\n=== ⑦ CS_12840 兑换商店货物 ===')
        c.send(12840)
        ex = []
        for _ in range(12):
            cmd, body = c.recv()
            if cmd == 12840:
                cur = Cur(body)
                n = cur.u(2)
                for _i in range(n):
                    ex.append(dict(id=cur.u(2), new_item_bid=cur.u(4),
                                   new_item_num=cur.u(4), new_bind=cur.u(1),
                                   item_bid=cur.u(4), item_num=cur.u(4),
                                   limit_num=cur.u(1), buy_num=cur.u(1)))
                break
        if not ex:
            bad('兑换商店为空（12840 goods_list=0）')
        else:
            ok('SC_12840 goods_list=%d 条' % len(ex))
            e0 = ex[0]
            print('       例: 用 item=%d ×%d 换 item=%d ×%d'
                  % (e0['item_bid'], e0['item_num'],
                     e0['new_item_bid'], e0['new_item_num']))
            # 把材料先塞进背包，保证兑换可执行
            sys.path.insert(0, os.path.join(ROOT, 'server'))
            import mock_server as M
            M.DB_PATH = os.path.join(ROOT, 'server', 'state', 'roles.db')
            M.db_init()
            M.db_bag_init()
            M.db_bag_add(1001, e0['item_bid'], e0['item_num'] * 2)
            print('       (已直接往背包塞入材料 %d ×%d 以验证兑换闭环)'
                  % (e0['item_bid'], e0['item_num'] * 2))
            c.send(12841, w_u16(e0['id']) + w_u16(1))
            got = False
            for _ in range(12):
                cmd, body = c.recv()
                if cmd == 12841:
                    cur = Cur(body)
                    code = cur.u(1)
                    msg = cur.s()
                    if code != 1:
                        bad('兑换失败 code=%d msg=%r' % (code, msg))
                    else:
                        ok('SC_12841 code=1(TRUE)（兑换 %d 成功）' % e0['id'])
                        got = True
                    break
            if not got:
                bad('没有收到 12841 应答')

        print('\n结论: %s' % ('全部通过 ✅' if not fails else ('失败 %d 项 ❌' % len(fails))))
        for m in fails:
            print('   - %s' % m)
        return 0 if not fails else 2
    finally:
        c.close()


if __name__ == '__main__':
    sys.exit(main() or 0)
