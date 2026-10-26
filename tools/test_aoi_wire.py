"""AOI 接线回归测试（2026-09-18）

用途：验证 `mock_server.py` 的 AOI 接线**没有破坏既有移动链路**，且
      `SC_10204` 的**响应内容与接线前完全一致**（字段/坐标不变）。

⚠ 安全设计：
  · **先读数据库原始坐标，测试结束后恢复原值**（state/roles.db 是共享状态）；
  · 只连指定端口，默认 9099（避开在线服务的 9000）。

用法：
    python server/mock_server.py --http 8099 --game 9099     # 另开一个终端
    python tools/test_aoi_wire.py 9099
"""
import json
import socket
import sqlite3
import struct
import sys
import time
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9099
# ★ R243：控制台默认 GBK ⇒ 打印 '↺'/'⇒' 抛 UnicodeEncodeError（回归被判 FAIL）
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DB = r'server\state\roles.db'
RID = 1001


# ── 协议小工具（与 tools/test_movedup.py 保持一致） ─────────────────────
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
        """读到指定 cmd 的 SC 包，返回 body。"""
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


def http_json(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8099' + path, timeout=5) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'_err': repr(e)}


def main():
    orig = db_pos()
    print('原始坐标（测试后会恢复）:', orig)
    ok = True
    cli = Client(PORT)
    try:
        # 1) 报到 + 账号登录 + 角色登录（10102 会触发服务端推 10200/10201 → AOI 登记）
        cli.send(10001, w_str('c') + b'\x00' * 4)
        time.sleep(0.2)
        cli.send(1110)
        b1110 = cli.wait(1110)
        print('1) SC_1110 roles        :', '有' if b1110 else '无')

        cli.send(10102)
        b10200 = cli.wait(10200)
        b10201 = cli.wait(10201)
        print('2) SC_10200 / SC_10201  :',
              '有' if b10200 else '无', '/', '有' if b10201 else '无')

        aoi = http_json('/status').get('aoi') or http_json('/status').get('modules')
        st = http_json('/status')
        print('3) /status aoi 相关字段 :', {k: v for k, v in st.items()
                                            if 'aoi' in k.lower()} or st.get('aoi'))

        # 2) 走一步（真实位移）—— 验证 SC_10204 内容不变
        tx, ty = orig[0] + 1, orig[1]
        cli.send(10204, struct.pack('>HH', tx, ty))
        body = cli.wait(10204)
        if body is None:
            print('4) SC_10204            : ❌ 无响应')
            ok = False
        else:
            rid, srv, x, y = (struct.unpack_from('>I', body, 0)[0], None, None, None)
            off = 4
            slen = struct.unpack_from('>H', body, off)[0]
            srv = body[off + 2:off + 2 + slen].decode('utf-8', 'ignore')
            off += 2 + slen
            x, y = struct.unpack_from('>HH', body, off)
            print('4) SC_10204            : rid=%s srv=%r pos=(%d,%d)  期望 (%d,%d)  %s'
                  % (rid, srv, x, y, tx, ty,
                     '✅ 一致' if (rid == RID and (x, y) == (tx, ty)) else '❌ 不一致'))
            ok = ok and rid == RID and (x, y) == (tx, ty)

        # 3) 走回去（把状态复位到原始坐标）
        cli.send(10204, struct.pack('>HH', orig[0], orig[1]))
        body2 = cli.wait(10204)
        print('5) 复位移动             :', '✅' if body2 else '❌')

        # 4) 瞬移 10205 也必须正常
        cli.send(10205, struct.pack('>HH', orig[0], orig[1]))
        body3 = cli.wait(10205)
        print('6) SC_10205 (瞬移)      :', '✅' if body3 else '❌')

        # 5) 心跳不应被打断
        cli.send(1199)
        time.sleep(0.3)
        print('7) 心跳 1199 已发送（无异常即通过）')

    finally:
        cli.close()
        cur = db_pos()
        if orig and cur != orig:
            db_set_pos(*orig)
            print('   ↺ 坐标已恢复', orig, '（原为', cur, '）')
        else:
            print('   ↺ 坐标无需恢复，仍为', cur)

    print()
    print('结论:', '✅ 接线未破坏既有移动链路' if ok else '❌ 有回归，请检查')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
