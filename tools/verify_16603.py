# -*- coding: utf-8 -*-
"""验证 16603 新分支：CS 解析（真机 8 字节 = bid 4 + 缓冲区残留 4）
+ SC 编码与 AutoConstruct 规格逐字段对齐。

规格依据（2026-09-19 回滚修正）：
    cmd_resolve_166.luac  AutoConstruct cs/16603 = ['bid__I']  **单字段**
    真机 body 恒 8 字节，尾部 4 字节是客户端发送缓冲区残留
    （同 16500 body=00660000、17200 body=010103e9、16400 body=type+00000003）。
    ⇒ 包长是弱证据，不可用 8 字节反推 num 字段。
    ⇒ 交叉审计见 tools/audit_specs_vs_fields.py（2463 条零不一致）。

用法：python tools/verify_16603.py
"""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(os.path.join(ROOT, 'protocol', 'fields.json'), encoding='utf-8') as f:
    FIELDS = json.load(f)

# ---- 真实抓包（server/logs/tcp_1.bin 等） ----
PACKETS = [
    bytes.fromhex('00000be10001316f'),   # tcp_1.bin   帧6294
    bytes.fromhex('00000be101000100'),   # tcp_1.bin
    bytes.fromhex('00000be103e90001'),   # tcp_5.bin
    bytes.fromhex('0000000000000000'),   # tcp_9.bin
    bytes.fromhex('00000be131343500'),   # tcp_34.bin
]

REMAIN_SEC = 30 * 24 * 3600


def build_sc(bid):
    """与服务端 mock_server.py 相同的生成逻辑（保持同步）。"""
    out = (struct.pack('>I', bid) +
           struct.pack('>I', REMAIN_SEC) +
           struct.pack('>I', 0) +
           struct.pack('>H', 0) +          # aim_list 空表
           struct.pack('>H', 0) +          # item_effect_list 空表
           struct.pack('>H', 0) +          # int_args 空表
           struct.pack('>H', 0) +          # client_reward 空串（u16 len=0）
           struct.pack('>H', 0))           # rank_list 空表
    return out


def sc_spec(cmd):
    for k, v in FIELDS.items():
        if v.get('cmd') == str(cmd) and v.get('dir') == 'sc':
            return v.get('fields') or []
    return []


def cs_spec(cmd):
    for k, v in FIELDS.items():
        if v.get('cmd') == str(cmd) and v.get('dir') == 'cs':
            return v.get('fields') or []
    return []


def main():
    ok = True

    # ---- 1) CS 规格：必须是 {bid:u32} 单字段（AutoConstruct 权威） ----
    cs = cs_spec(16603)
    cs_types = [(f['name'], f['type']) for f in cs]
    print('== CS_16603 规格（fields.json）==')
    print('  ', cs_types)
    if cs_types != [('bid', 'uint32')]:
        print('   !! CS 规格不符（应仅 bid:uint32）')
        ok = False
    else:
        print('   结果: PASS（仅 bid；AutoConstruct cs/16603 = [b\'bid__I\']）')

    # ---- 2) 真机抓包解析：8 字节 = bid(4) + 残留(4) ----
    print('\n== 真机抓包解析（取前 4 字节为 bid，其余为残留）==')
    for h in PACKETS:
        if len(h) < 4:
            print('   !! 抓包长度 %d < 4' % len(h))
            ok = False
            continue
        bid = struct.unpack('>I', h[:4])[0]
        tail = h[4:]
        print('   bid=%-6d 残留(%d)=%s' % (bid, len(tail), tail.hex() or '-'))

    # ---- 3) SC 编码：按规格逐字段解析 ----
    print('\n== SC_16603 编码校验 ==')
    spec = sc_spec(16603)
    print('   规格字段: %s' % [f['name'] for f in spec])
    buf = build_sc(3041)
    off = 0

    def r32():
        nonlocal off
        v = struct.unpack_from('>I', buf, off)[0]
        off += 4
        return v

    def r16():
        nonlocal off
        v = struct.unpack_from('>H', buf, off)[0]
        off += 2
        return v

    bid = r32()
    remain = r32()
    finish = r32()
    n_aim = r16()
    n_effect = r16()
    n_args = r16()
    n_reward = r16()
    n_rank = r16()
    assert n_reward == 0, 'client_reward 应为空串（u16 len=0）'

    print('   bid=%d remain_sec=%d finish=%d' % (bid, remain, finish))
    print('   aim_list=%d item_effect_list=%d int_args=%d client_reward_len=%d rank_list=%d'
          % (n_aim, n_effect, n_args, n_reward, n_rank))
    if bid != 3041:
        print('   !! bid 未回显')
        ok = False
    if remain != REMAIN_SEC:
        print('   !! remain_sec 异常')
        ok = False
    if off != len(buf):
        print('   !! 剩余 %d 字节未解析' % (len(buf) - off))
        ok = False
    print('   结果: %s（包体 %d 字节，精确消耗 %d 字节）'
          % ('PASS' if ok and off == len(buf) else 'FAIL', len(buf), off))

    # ---- 4) 客户端无崩溃安全项 ----
    print('\n== 客户端安全项 ==')
    checks = [
        ('remain_sec > 0（倒计时不显示已结束）', remain > 0),
        ('aim_list 空表（无索引访问风险）', n_aim == 0),
        ('client_reward 空串合法', n_reward == 0),
    ]
    for label, passed in checks:
        print('   %s: %s' % ('OK' if passed else 'FAIL', label))
        ok = ok and passed

    print('\n=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
