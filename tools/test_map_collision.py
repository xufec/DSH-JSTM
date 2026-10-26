"""碰撞校验回归测试（2026-09-18）

验证 `mock_server.py` 接入了真实碰撞数据（`server/map_block.json`）之后：
  ① 走到**可走格** → 服务端接受，SC_10204 回该坐标，DB 更新
  ② 走到**阻挡格** → 服务端拒绝，SC_10204 回**权威坐标（上一格）**，**DB 不被污染**
  ③ 无碰撞数据的场景 → 退化为 allow_all（不阻挡）

⚠ 安全：先读 DB 原始坐标，测试结束后**恢复原值**（roles.db 是共享状态）。

用法：
    python server/mock_server.py --http 8099 --game 9099
    python tools/test_map_collision.py 9099 10001
"""
import json
import os
import socket
import sqlite3
import struct
import sys
import time

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9099
# ★ R243：控制台默认 GBK ⇒ 打印 '↺'/'⇒' 抛 UnicodeEncodeError（回归被判 FAIL）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
BID = int(sys.argv[2]) if len(sys.argv) > 2 else 10001
RID = 1001
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server', 'state', 'roles.db')
MB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'server', 'map_block.json')


def frame(cmd, body=b''):
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body


def w_str(s):
    b = s.encode()
    return struct.pack('>H', len(b)) + b


class Client(object):
    def __init__(self, port):
        self.s = socket.create_connection(('127.0.0.1', port), timeout=6)
        self.buf = b''

    def send(self, cmd, body=b''):
        self.s.sendall(frame(cmd, body))

    def wait(self, cmd, timeout=5.0):
        end = time.time() + timeout
        self.s.settimeout(0.3)
        while time.time() < end:
            while len(self.buf) >= 6:
                ln = struct.unpack_from('>I', self.buf, 0)[0]
                if len(self.buf) < 4 + ln:
                    break
                c = struct.unpack_from('>H', self.buf, 4)[0]
                b = self.buf[6:4 + ln]
                self.buf = self.buf[4 + ln:]
                if c == cmd:
                    return b
            try:
                d = self.s.recv(262144)
                if not d:
                    return None
                self.buf += d
            except socket.timeout:
                pass
        return None

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass


def db_pos():
    con = sqlite3.connect(DB)
    r = con.execute('SELECT x,y FROM roles WHERE rid=?', (RID,)).fetchone()
    con.close()
    return (int(r[0]), int(r[1])) if r else None


def db_set_pos(x, y):
    con = sqlite3.connect(DB)
    con.execute('UPDATE roles SET x=?,y=? WHERE rid=?', (int(x), int(y), RID))
    con.commit()
    con.close()


def parse_10204(body):
    rid = struct.unpack_from('>I', body, 0)[0]
    slen = struct.unpack_from('>H', body, 4)[0]
    srv = body[6:6 + slen].decode('utf-8', 'ignore')
    x, y = struct.unpack_from('>HH', body, 6 + slen)
    return rid, srv, x, y


def main():
    scenes = json.load(open(MB, encoding='utf-8'))['scenes']
    rows = scenes.get(str(BID))
    if not rows:
        print('场景 %d 无碰撞数据，无法测试' % BID)
        return 1

    def cell(x, y):
        if 1 <= y <= len(rows) and 1 <= x <= len(rows[0]):
            return rows[y - 1][x - 1]
        return None

    def walkable_cell(x, y):
        """与 mock_server._scene_grid 同一判定：只有 '1' 是阻挡。"""
        c = cell(x, y)
        return c is not None and c != '1'

    orig = db_pos()
    print('原始坐标（测后恢复）:', orig, '  场景', BID)

    # 以原坐标为基准找"最近的可走格"与"最近的阻挡格"
    ox, oy = orig
    walk_nb, blk_nb = [], []
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            x, y = ox + dx, oy + dy
            c = cell(x, y)
            if c is None or (x, y) == (ox, oy):
                continue
            (walk_nb if walkable_cell(x, y) else blk_nb).append((x, y))
    walk_nb.sort(key=lambda p: abs(p[0] - ox) + abs(p[1] - oy))
    blk_nb.sort(key=lambda p: abs(p[0] - ox) + abs(p[1] - oy))
    if not walk_nb or not blk_nb:
        print('附近找不到可走格/阻挡格，无法测试')
        return 1
    wt, bt = walk_nb[0], blk_nb[0]
    print('测试用：可走格 %r(格值%s)   阻挡格 %r(格值%s)'
          % (wt, cell(*wt), bt, cell(*bt)))

    ok = True
    cli = Client(PORT)
    try:
        cli.send(10001, w_str('c') + b'\x00' * 4)
        time.sleep(0.2)
        cli.send(1110)
        cli.wait(1110)
        cli.send(10102)
        cli.wait(10200)
        cli.wait(10201)

        # ① 走可走格 → 应被接受
        cli.send(10204, struct.pack('>HH', *wt))
        b1 = cli.wait(10204)
        if not b1:
            print('① 可走格：❌ 无响应'); ok = False
        else:
            _, _, x1, y1 = parse_10204(b1)
            good = (x1, y1) == wt
            print('① 走到可走格 %r → 服务端回 (%d,%d)  %s' % (wt, x1, y1, '✅' if good else '❌'))
            ok = ok and good

        # ② 走阻挡格 → 应被拒绝并回权威坐标（= 上一格）
        cli.send(10204, struct.pack('>HH', *bt))
        b2 = cli.wait(10204)
        if not b2:
            print('② 阻挡格：❌ 无响应'); ok = False
        else:
            _, _, x2, y2 = parse_10204(b2)
            rejected = (x2, y2) == wt          # 权威坐标应为上一格
            print('② 走到阻挡格 %r → 服务端回 (%d,%d)  %s'
                  % (bt, x2, y2, '✅ 已拦截并纠正到上一格' if rejected
                     else '❌ 未被拦截（疑似穿墙）'))
            ok = ok and rejected
            time.sleep(0.3)
            now = db_pos()
            clean = now == wt
            print('   DB 是否被阻挡坐标污染：%r  %s' % (now, '✅ 未污染' if clean else '❌ 被污染'))
            ok = ok and clean

        # ③ 无数据场景（只验证服务端不因缺数据而报错/拦截）：用 99999 只做只读探测
        print('③ 无碰撞数据的场景：服务端 get_mapgrid() 退化为 allow_all'
              '（本测试不切场景，仅说明行为）')

    finally:
        cli.close()
        time.sleep(0.2)
        cur = db_pos()
        if orig and cur != orig:
            db_set_pos(*orig)
            print('   ↺ 坐标已恢复', orig, '（原为', cur, '）')
        else:
            print('   ↺ 坐标无需恢复，仍为', cur)

    print()
    print('结论:', '✅ 碰撞校验生效（不穿墙、不污染存档）' if ok else '❌ 有问题')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
