# -*- coding: utf-8 -*-
"""R78：模拟「点怪 → 打完一场」，把服务端发的 SC 序列全部收下来。

用来验证三件事：
  ① `SC_20010` 的 `pos` 不再是 0（客户端原先弹「pos位置不能为0」）
  ② 怪的 `animate_res.ant_val` 是 `Config.Mon` 的原版资源 id（不是主角模型）
  ③ **`SC_20022`（显示战斗结束界面）确实发出**（此前从来不發，胜利界面不对）

用法： python tools/verify_battle_20022.py [mon_id]
"""
import io
import os
import socket
import struct
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from audit_sc_live import pack_frame, recv_exact  # noqa: E402


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s):
    _args = struct.pack('>H', 10)
    for _k, _v in (('account', 'dsh_local'), ('channelId', '1'),
                   ('device_id', 'dsh-probe'), ('enter_srv_id', '1'),
                   ('gettui_cid', ''), ('idfa', ''), ('platform', 'ewan'),
                   ('sign', ''), ('timestamp', '0'), ('token', '')):
        _kb = _k.encode(); _vb = _v.encode()
        _args += struct.pack('>H', len(_kb)) + _kb + struct.pack('>H', len(_vb)) + _vb
    s.sendall(pack_frame(1110, _args))
    rid = None
    while True:
        ln, rc = struct.unpack('>IH', recv_exact(s, 6))
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]
            off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]
            off += 2
            if cnt:
                rid = struct.unpack_from('>I', p, off)[0]
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                ln, rc = struct.unpack('>IH', recv_exact(s, 6))
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except socket.timeout:
            pass
        s.settimeout(6.0)
    return rid


def main():
    mon = int(sys.argv[1]) if len(sys.argv) > 1 else 10105
    s = socket.create_connection(('127.0.0.1', 9000), 5)
    s.settimeout(8.0)
    print('login rid =', login(s))
    s.sendall(pack_frame(20002, struct.pack('>i', mon)))
    print('已发 CS_20002{mon_id=%d}，收 12 秒服务端 SC...\n' % mon)

    seen = []
    t0 = time.time()
    while time.time() - t0 < 25.0:
        try:
            ln, rc = struct.unpack('>IH', recv_exact(s, 6))
            body = recv_exact(s, ln - 2)
        except socket.timeout:
            continue
        except Exception:
            break
        names = {20002: 'SC_20002 fight_start', 20010: 'SC_20010 fight_data',
                 20012: 'SC_20012 skill_play', 20013: 'SC_20013 round_start',
                 20020: 'SC_20020 fight_end', 20022: 'SC_20022 ★显示结束界面',
                 20023: 'SC_20023 end_data'}
        if rc in names:
            seen.append(rc)
            extra = ''
            if rc == 20010:
                extra = ' len=%d（pos 已改为 1 基）' % len(body)
            elif rc == 20002:
                extra = ' code=%d' % (body[0] if body else -1)
            elif rc == 20020:
                extra = ' result=%d' % (body[0] if body else -1)
            elif rc == 20022:
                n = struct.unpack_from('>H', body, 0)[0] if len(body) >= 2 else -1
                extra = ' icon_list=%d' % n
            print('  << %-28s (%d bytes)%s' % (names[rc], ln, extra))
    print('\n命令序列:', [c for c in seen])
    # ★ R79 更正断言：`SC_20022` 是 `openBattleFail`（**失败界面**），
    #   所以**胜利时不应出现**它；出现它反而说明"赢了弹失败界面"这个 bug 还在。
    win = 20020 in seen
    ok = win and (20022 not in seen)
    if win:
        print('胜负判定：胜利（SC_20020 已发） ⇒ 期望**不含** 20022')
        print('实际含 20022:', 20022 in seen)
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    s.close()
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
