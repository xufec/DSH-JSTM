# -*- coding: utf-8 -*-
"""protocol.frame —— 帧编解码（Phase 2 step 1：从 mock_server.py 原样搬入）。

设计依据：analysis/phase2_design.md §二 core/protocol/。

线格式（与现状逐字节一致）：
  [u32 BE 总长度][u16 BE cmd][body ...]
  总长度含 u32 自身 4 字节（实测）。

迁移来源（mock_server.py 当前行号）：
  w_u8 / w_u16 / w_u32 / w_str   L1604–1618
  pack_frame(cmd, body)          L1621–1623
  class FrameParser              L1626–1646

本模块只依赖标准库 struct —— 无循环 import 风险。
"""

import struct

# 线格式常量（与现状一致；不改协议）。
LEN_PREFIX_BYTES = 4   # u32 BE 长度前缀
CMD_PREFIX_BYTES = 2   # u16 BE cmd


def w_u8(v):
    return struct.pack('>B', int(v) & 0xFF)


def w_u16(v):
    return struct.pack('>H', int(v) & 0xFFFF)


def w_u32(v):
    return struct.pack('>I', int(v) & 0xFFFFFFFF)


def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


def pack_frame(cmd, body=b''):
    payload = w_u16(cmd) + body
    return w_u32(len(payload)) + payload


class FrameParser(object):
    """增量解帧；返回 [(cmd, body)]，不足一帧就留在缓冲里。"""

    def __init__(self):
        self.buf = b''

    def feed(self, data):
        self.buf += data
        out = []
        while len(self.buf) >= 6:
            ln = struct.unpack_from('>I', self.buf, 0)[0]
            cmd = struct.unpack_from('>H', self.buf, 4)[0]
            if ln < 2 or ln > 1 << 20:
                out.append(('BAD', self.buf[:32]))
                self.buf = b''
                break
            if len(self.buf) < 4 + ln:
                break
            out.append((cmd, self.buf[6:4 + ln]))
            self.buf = self.buf[4 + ln:]
        return out
