# -*- coding: utf-8 -*-
"""验证 10924 活动列表分支的字节流编码与协议规格一致。

规格（protocol/manual.md + cmd_resolve_109.luac proto#19/#25 取证）：
  SC_10924 = { act_list: table(id:uint16, status:uint8,
                               int_args:D|Dsc10924int_args|) }
  Dsc10924int_args = table(val:uint32)     ← ReadFMT('H') 计数 + 循环 ReadFMT('I')

校验内容：
  1. 每条 id 都命中 config_function.json 且 is_open=1、open_lev<=玩家等级
  2. 每条 status == 1（客户端 proto#49 对 {501,502,503,504} 要求 status==1 才显示）
  3. 每条 int_args 至少 1 个 u32（空表会让 daily_ctrl 崩溃）
  4. 字节流精确消耗（无剩余字节）

用法：python tools/verify_10924.py
"""
import json
import os
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(os.path.join(ROOT, '_tmp_cfg', 'config_function.json'), encoding='utf-8') as f:
    FUNC = json.load(f)


def build_10924(lev):
    """与服务端 mock_server.py 相同的生成逻辑（保持同步）。"""
    now = int(time.time()) & 0xFFFFFFFF
    sel = [x for x in FUNC
           if int(x.get('is_open', 0)) == 1
           and int(x.get('open_lev', 0)) <= lev]
    sel.sort(key=lambda x: (int(x.get('sort_id') or 0), int(x.get('id') or 0)))
    out = struct.pack('>H', len(sel))
    for x in sel:
        out += (struct.pack('>H', int(x.get('id', 0)) & 0xffff) +
                struct.pack('>B', 1) +
                struct.pack('>H', 1) + struct.pack('>I', now))
    return out, sel


def parse_10924(buf):
    """按 SC_10924 规格解析，返回 (条目列表, 剩余字节数)。"""
    off = 0
    (cnt,) = struct.unpack_from('>H', buf, off)
    off += 2
    items = []
    for _ in range(cnt):
        (aid,) = struct.unpack_from('>H', buf, off)
        off += 2
        (status,) = struct.unpack_from('>B', buf, off)
        off += 1
        (n_args,) = struct.unpack_from('>H', buf, off)
        off += 2
        vals = list(struct.unpack_from('>%dI' % n_args, buf, off))
        off += 4 * n_args
        items.append((aid, status, vals))
    return items, off


def main():
    lev = 1  # 默认新角色等级
    body, sel = build_10924(lev)
    items, off = parse_10924(body)
    ok = True

    print('== 10924 活动列表（模拟等级 %d）==  %d 条活动' % (lev, len(items)))
    print('包体 %d 字节，解析消耗 %d 字节' % (len(body), off))
    if off != len(body):
        print('  !! 字节流未精确消耗（剩 %d 字节）' % (len(body) - off))
        ok = False

    by_id = {int(x.get('id')): x for x in FUNC}
    seen = set()
    for aid, status, vals in items:
        cfg = by_id.get(aid)
        if aid in seen:
            print('  !! id %d 重复' % aid)
            ok = False
        seen.add(aid)
        if cfg is None:
            print('  !! id %d 不在 config_function.json 中' % aid)
            ok = False
            continue
        if int(cfg.get('is_open', 0)) != 1:
            print('  !! id %d 的 is_open != 1' % aid)
            ok = False
        if int(cfg.get('open_lev', 0)) > lev:
            print('  !! id %d 的 open_lev=%d > 玩家等级 %d' % (aid, cfg.get('open_lev'), lev))
            ok = False
        if status != 1:
            print('  !! id %d 的 status=%d != 1' % (aid, status))
            ok = False
        if not vals:
            print('  !! id %d 的 int_args 为空表（客户端 daily_ctrl 会崩溃）' % aid)
            ok = False

    # 反向核对：config_function 中 is_open=1 且 open_lev<=lev 的条目必须全部在包内
    expect_ids = {int(x.get('id')) for x in FUNC
                  if int(x.get('is_open', 0)) == 1 and int(x.get('open_lev', 0)) <= lev}
    if expect_ids != seen:
        miss = expect_ids - seen
        extra = seen - expect_ids
        if miss:
            print('  !! 缺失应发活动: %s' % sorted(miss))
            ok = False
        if extra:
            print('  !! 多发了不应发活动: %s' % sorted(extra))
            ok = False

    print('活动 id 列表: %s' % sorted(seen))
    print('\n结果:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
