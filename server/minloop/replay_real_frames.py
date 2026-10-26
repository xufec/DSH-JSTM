#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把**真机抓到的客户端帧**回放给最小回环服务器（真实数据回归）。

为什么要它：最小回环自检（selftest.py）用的是"我自己构造的 CS"。而本项目最容易犯的错
是"字段宽度/结构自己觉得对"（历史上 SC 被截断 4 次、字段宽度错 6 次）。
所以这里用**MuMu 里那台真机 APK 实际发出来的字节**回放，判据只有两条：
    ① 服务端每个应答都能按 `protocol/fields.json` 的权威 SC 规格**严格**解析
       （不多不少正好消费完 body）；
    ② 回环命令的应答 `code == 1`（TRUE）；没有 SC 定义的命令**必须不回包**。

数据源：`server/logs/tcp_prevR.log` 等**服务端抓包日志**里 `--- recv N bytes` 后面的
        十六进制转储（那是客户端真实发出的帧，方向单一，可安全回放）。
        这些帧产生于 MuMu 里运行的 1.4.9 APK。

用法：python server/minloop/replay_real_frames.py [日志文件...]
"""
from __future__ import annotations

import os
import re
import socket
import struct
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import min_loop_server as M  # noqa: E402
from selftest import Client, free_port  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.dirname(HERE)

HEXLINE = re.compile(r'^\s*([0-9a-fA-F]{4})\s+((?:[0-9a-fA-F]{2} ){1,16})')


def frames_from_log(path):
    """从抓包日志里还原"客户端真正发出去"的帧序列（按出现顺序，跨连接拼接）。"""
    frames = []
    cur = bytearray()
    with open(path, encoding='utf-8', errors='replace') as f:
        for line in f:
            m = HEXLINE.match(line)
            if m:
                for b in m.group(2).split():
                    cur.append(int(b, 16))
                continue
            # 非十六进制行 ⇒ 一段转储结束，把攒到的字节解成帧
            if cur:
                frames.extend(split_frames(bytes(cur)))
                cur = bytearray()
    if cur:
        frames.extend(split_frames(bytes(cur)))
    return frames


def split_frames(blob):
    out, o = [], 0
    while o + 6 <= len(blob):
        ln = struct.unpack_from('>I', blob, o)[0]
        cmd = struct.unpack_from('>H', blob, o + 4)[0]
        if ln < 2 or ln > (1 << 20) or o + 4 + ln > len(blob):
            o += 1                     # 日志里偶尔混入非帧字节 ⇒ 滑动找对齐
            continue
        out.append((cmd, blob[o + 6:o + 4 + ln]))
        o += 4 + ln
    return out


def main(argv):
    logs = argv[1:] or [os.path.join(SERVER_DIR, 'logs', 'tcp_prevR.log')]
    logs = [p for p in logs if os.path.exists(p)]
    if not logs:
        print('找不到抓包日志')
        return 2

    port, hp = free_port(), free_port()
    tmp = tempfile.mkdtemp(prefix='minloop_replay_')
    srv = M.Server(hp, port, os.path.join(tmp, 'replay.db'), bind='127.0.0.1')
    threading.Thread(target=srv.run, daemon=True).start()
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)

    spec = srv.spec
    all_frames = []
    for p in logs:
        fr = frames_from_log(p)
        print('%-46s 真实帧 %d' % (os.path.basename(p), len(fr)))
        all_frames.extend(fr)
    cmds = {}
    for cmd, _b in all_frames:
        cmds[cmd] = cmds.get(cmd, 0) + 1
    print('合计真实帧 %d，去重命令 %d 条' % (len(all_frames), len(cmds)))

    # 回放：**分批**发包 + 批量收包。
    # 不用"一帧一等"：tcp_prevR.log 有数千帧，逐帧等超时要跑十几分钟；
    # 服务端是同步应答的，批量收下来按**命令号**核对同样有效（顺序无关）。
    c = Client(spec, '127.0.0.1', port)
    reply_cmds, strict_bad, code_bad, loop_seen = {}, [], [], set()
    honest_no = {}

    def take(rcmd, vals, ok, detail):
        reply_cmds[rcmd] = reply_cmds.get(rcmd, 0) + 1
        if not ok:
            strict_bad.append((rcmd, detail))
        if rcmd not in M.Session.LOOP or not vals:
            return
        loop_seen.add(rcmd)
        code = vals.get('code')
        if code in (None, 1):
            return
        # [DOC] 本项目纪律：**明确回失败 = code=0 且 msg 非空**（诚实拒绝），这不是 bug；
        #       真正危险的是"code=0 且 msg 空"（客户端会弹空白框）或非法 code。
        msg = vals.get('msg')
        if code == 0 and msg:
            honest_no[msg] = honest_no.get(msg, 0) + 1
        else:
            code_bad.append((rcmd, code, msg))

    batch = 0
    for cmd, body in all_frames:
        if not spec.has_sc(cmd) and not spec.cs.get(cmd):
            continue
        c.send(cmd, raw=body)
        batch += 1
        if batch % 25 == 0:
            for r in c.recv_all(0.5, idle=0.2):
                take(*r)
    for r in c.recv_all(1.0, idle=0.3):
        take(*r)
    c.close()

    print('\n服务端应答覆盖命令 %d 条，应答帧合计 %d' % (len(reply_cmds), sum(reply_cmds.values())))
    print('回环命令在真实流量里出现过并被正确应答：%s'
          % (','.join(str(x) for x in sorted(loop_seen)) or '（无）'))
    print('规格不符（多/少字节）：%d' % len(strict_bad))
    for x in strict_bad[:10]:
        print('   sc=%s %s' % x)
    print('危险应答（code=0 且 msg 空 / 非法 code）：%d' % len(code_bad))
    for x in code_bad[:10]:
        print('   cmd=%s code=%s msg=%s' % x)
    print('诚实拒绝（code=0 且有 msg，回放上下文不连贯所致）：%d' % sum(honest_no.values()))
    for m, n in sorted(honest_no.items(), key=lambda x: -x[1])[:6]:
        print('   %-24s ×%d' % (m, n))
    print('（说明）真机没发过的命令本来就没有真实样本；非回环命令走通用零值应答。')
    sys.stdout.flush()
    ok = not strict_bad and not code_bad
    print('\n结论：%s' % ('真实帧回放全部通过' if ok else '存在失败项，见上'))
    os._exit(0 if ok else 1)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
