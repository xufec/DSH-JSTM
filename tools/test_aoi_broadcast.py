"""AOI 广播集成测试（2026-09-18）

目的：证明"**同场的另一个角色能看到我移动**"这条链路真的通了 ——
      即 `_scene_apply_move` + `_scene_broadcast_10204` 会向"看得见我的人"推 SC_10204。

为什么要绕开真机验证：
  `mock_server.py` 里 `TcpHandler.cfg = cfg` 是**类属性、全连接共享** ⇒
  所有连接共用同一个 rid（1001）⇒ 真机开两个客户端也**只有 1 个 AOI 实体**，
  `watchers` 恒为空。所以这里直接用**真实的接线函数** + **两个假 handler**
  （各自带不同 `_aoi_rid`）来验证广播分支。

⚠ 只读 + 只在内存中操作；不写数据库、不起服务、不改文件。

用法：python tools/test_aoi_broadcast.py
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'server'))

import mock_server as M   # noqa: E402


class FakeReq(object):
    """假 socket：把 sendall 的字节收下来。"""
    def __init__(self):
        self.pkts = []

    def sendall(self, data):
        self.pkts.append(data)


class FakeHandler(object):
    def __init__(self, rid, addr):
        self._aoi_rid = rid          # 预置缓存 ⇒ _scene_rid 不再查库
        self.client_address = addr
        self.request = FakeReq()


def frames(pkts):
    """把字节流切成 (cmd, body) 列表。"""
    out = []
    for p in pkts:
        off = 0
        while off + 6 <= len(p):
            ln = struct.unpack_from('>I', p, off)[0]
            cmd = struct.unpack_from('>H', p, off + 4)[0]
            body = p[off + 6:off + 4 + ln]
            out.append((cmd, body))
            off += 4 + ln
    return out


def main():
    ok = True
    aoi = M.get_aoi()
    if aoi is None:
        print('❌ aoi 模块未加载（aoi_mod is None）')
        return 1
    aoi._ents.clear()
    aoi._towers.clear()

    A = FakeHandler(1001, ('10.0.0.1', 1111))   # 我
    B = FakeHandler(2002, ('10.0.0.2', 2222))   # 另一个同场玩家

    # 两个玩家都登记（add_player = watcher + object）
    aoi.add_player(1001, 10, 10, 15)
    aoi.add_player(2002, 12, 12, 15)
    M._LAST_POS[1001] = (10, 10)
    M._LAST_POS[2002] = (12, 12)

    with M.LIVE_LOCK:
        M.LIVE_CONNECTIONS.append(A)
        M.LIVE_CONNECTIONS.append(B)

    try:
        # ① 我移动 1 格 → 应同时产出"我的视野事件"与"该被告知的人"
        watchers = M._scene_apply_move(A, 1001, 11, 10)
        print('① _scene_apply_move 返回 watchers =', watchers)
        if 2002 not in watchers:
            print('   ❌ 2002 应在 watchers 中（距离 2 格 < 视野 15）')
            ok = False
        else:
            print('   ✅ 2002 在 watchers 中')

        # ② 广播 → B 应收到一条 SC_10204，内容是我的新坐标
        sent = M._scene_broadcast_10204(A, 1001, '1', 11, 10, watchers)
        print('② _scene_broadcast_10204 推送数 =', sent)
        fr = frames(B.request.pkts)
        if sent != 1 or not fr:
            print('   ❌ B 未收到广播')
            ok = False
        else:
            cmd, body = fr[0]
            rid = struct.unpack_from('>I', body, 0)[0]
            slen = struct.unpack_from('>H', body, 4)[0]
            srv = body[6:6 + slen].decode()
            x, y = struct.unpack_from('>HH', body, 6 + slen)
            print('   ✅ B 收到 cmd=%d rid=%d srv=%r pos=(%d,%d)  期望 (1001,%r,(11,10))'
                  % (cmd, rid, srv, x, y, '1'))
            ok = ok and cmd == 10204 and rid == 1001 and (x, y) == (11, 10)

        # ③ 自己不给自己发（A 的包必须是"回发本人"的那条，不能是广播）
        print('③ A 自己的 request 里是否被广播污染 :',
              '✅ 干净（广播只发他人）' if not frames(A.request.pkts) else '❌ 有污染')
        ok = ok and not frames(A.request.pkts)

        # ④ 走出视野 → watchers 应为空
        watchers2 = M._scene_apply_move(A, 1001, 500, 500)
        print('④ 走到 (500,500) 后 watchers =', watchers2,
              '✅' if 2002 not in watchers2 else '❌ 仍应看得见')
        ok = ok and 2002 not in watchers2

        # ⑤ B 断线离开 → A 应收到 leave 事件（A 的 seen 里应有 2002 吗？此时已走远，故为空）
        ev = aoi.remove(2002)
        print('⑤ aoi.remove(2002) 事件 =', ev, '（A 已走远 ⇒ 空是正常的）')

        print()
        print('结论:', '✅ AOI 广播链路可用（接线函数正确）' if ok else '❌ 广播链路有问题')
        return 0 if ok else 1
    finally:
        with M.LIVE_LOCK:
            for h in (A, B):
                if h in M.LIVE_CONNECTIONS:
                    M.LIVE_CONNECTIONS.remove(h)
        M._LAST_POS.pop(1001, None)
        M._LAST_POS.pop(2002, None)
        aoi._ents.clear()
        aoi._towers.clear()


if __name__ == '__main__':
    sys.exit(main())
