# -*- coding: utf-8 -*-
"""真机级回测：模拟客户端发送 11215 / 10800 / 10924 / 16603，校验服务端新分支应答。"""
import socket
import struct
import sys

HOST, PORT = '127.0.0.1', 9000
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def pack_frame(cmd, body=b''):
    # 帧格式：4 字节长度前缀（= 2 字节 cmd + body，不含前缀自身）+ cmd + body
    return struct.pack('>I', 2 + len(body)) + struct.pack('>H', cmd) + body


def recv_exact(s, n):
    buf = b''
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise EOFError('连接关闭')
        buf += chunk
    return buf


def send_cmd(s, cmd, body=b''):
    s.sendall(pack_frame(cmd, body))
    # 循环读帧，跳过服务端主动推送，直到拿到目标 cmd 的应答。
    # 服务端长度前缀 = 2 字节 cmd + body（不含 4 字节前缀自身）⇒ payload = ln-2。
    s.settimeout(3)
    while True:
        hdr = recv_exact(s, 6)
        (ln, rcmd) = struct.unpack('>IH', hdr)
        payload = recv_exact(s, ln - 2)
        if rcmd == cmd:
            s.settimeout(10)
            return rcmd, payload


def login(s):
    # 10001 CSFirstPack 只是"报到"，无 SC 回包（mock_server 明确不回）⇒ 不读 ack
    s.sendall(pack_frame(10001, struct.pack('>H', len(b'key')) + b'key'))
    body = struct.pack('>I', 1) + struct.pack('>I', 1) + struct.pack('>I', 1)
    s.sendall(pack_frame(1110, body))
    recv_exact(s, 6)
    # 10102 登录角色
    s.sendall(pack_frame(10102, struct.pack('>I', 1001)))
    # 吞掉后续推送直到收到 10200 或超时
    s.settimeout(1.0)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rcmd) = struct.unpack('>IH', hdr)
            recv_exact(s, ln - 2)
            if rcmd == 10200:
                break
    except (EOFError, socket.timeout):
        pass
    s.settimeout(10)


def main():
    s = socket.create_connection((HOST, PORT), timeout=10)
    login(s)

    ok = True
    for cmd, label, expect in ((11215, '伙伴列表', 53),
                               (10800, '邮件列表', 1),
                               (10924, '活动列表', None)):
        rcmd, payload = send_cmd(s, cmd)
        print('>> %d (%s) -> << %d 应答 %d 字节' % (cmd, label, rcmd, len(payload)))
        if rcmd != cmd:
            print('   !! 应答命令不匹配')
            ok = False
            continue
        (n,) = struct.unpack_from('>H', payload, 0)
        print('   首表元素数 = %d' % n)
        if expect is not None:
            print('   期望 %d' % expect)
            ok = ok and n == expect
        elif cmd == 10924:
            # 逐条解析：id:u16, status:u8, int_args:u16 计数 + u32*count
            off = 2
            all_ok = True
            for i in range(n):
                (aid, status, nargs) = struct.unpack_from('>HBH', payload, off)
                off += 5
                vals = struct.unpack_from('>%dI' % nargs, payload, off)
                off += 4 * nargs
                if status != 1 or nargs < 1:
                    all_ok = False
                print('    #%d id=%d status=%d int_args=%d %s' %
                      (i, aid, status, nargs, list(vals)[:2]))
            if off != len(payload):
                print('   !! 字节流剩余 %d 字节' % (len(payload) - off))
                all_ok = False
            ok = ok and all_ok
    s.close()
    # ---- 16603：用真实抓包格式单独验证（登录态） ----
    #   真机 body 恒 8 字节 = bid(4) + **客户端缓冲区 4 字节残留**
    #   （AutoConstruct cs/16603 = ['bid__I'] 单字段；第二段不是 num 字段）
    s = socket.create_connection((HOST, PORT), timeout=10)
    login(s)
    rcmd, payload = send_cmd(s, 16603, struct.pack('>II', 3041, 0x0001316f))
    print('\n>> 16603 (限时目标/天降豪礼) -> << %d 应答 %d 字节' % (rcmd, len(payload)))
    if rcmd != 16603:
        print('   !! 应答命令不匹配')
        ok = False
    else:
        bid, remain, finish = struct.unpack_from('>III', payload, 0)
        off = 12
        n_aim = struct.unpack_from('>H', payload, off)[0]; off += 2
        n_effect = struct.unpack_from('>H', payload, off)[0]; off += 2
        n_args = struct.unpack_from('>H', payload, off)[0]; off += 2
        n_reward = struct.unpack_from('>H', payload, off)[0]; off += 2
        n_rank = struct.unpack_from('>H', payload, off)[0]; off += 2
        print('   bid=%d remain_sec=%d finish=%d' % (bid, remain, finish))
        print('   aim_list=%d item_effect_list=%d int_args=%d client_reward_len=%d rank_list=%d'
              % (n_aim, n_effect, n_args, n_reward, n_rank))
        all_ok = (bid == 3041 and remain > 0 and n_aim == 0
                  and n_reward == 0 and off == len(payload))
        if off != len(payload):
            print('   !! 字节流剩余 %d 字节' % (len(payload) - off))
        ok = ok and all_ok
    s.close()
    print('\n结果:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
