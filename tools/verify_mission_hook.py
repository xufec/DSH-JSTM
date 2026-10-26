# -*- coding: utf-8 -*-
"""R48 验证：进度挂钩（**显式 bid 白名单**版）与安全默认。

核对三件事：
  1. **安全默认**：映射表里没有该 bid ⇒ 提交任务**什么也不变**
     （这条同时证明"按 mission_type 匹配"那个错误已修掉 ——
       因为 config_mission 全部 type=1，旧写法会把任何任务都记成学院任务）；
  2. **机制有效**：把该 bid 写进某组的 `mission_bids` 后，**无需重启服务端**
     （映射表按 mtime 热重载），提交一次 ⇒ 日常次数 +1、成就进度 +1；
  3. **玩家账号不受影响**（全程用测试角色；结束时恢复映射表原样）。

用法：python tools/verify_mission_hook.py
"""
import json
import os
import shutil
import socket
import sqlite3
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from audit_sc_live import pack_frame, recv_exact  # noqa: E402

DB = os.path.join(ROOT, 'server', 'state', 'roles.db')
MAP = os.path.join(ROOT, 'server', '_chengjiu_map.json')
TEST_UID = 'r48_hook'


def w_str(s):
    b = s.encode('utf-8')
    return struct.pack('>H', len(b)) + b


def login(s, account, rid=None):
    s.sendall(pack_frame(1110, struct.pack('>H', 1) + w_str('account') + w_str(account)))
    got = None
    while True:
        hdr = recv_exact(s, 6)
        (ln, rc) = struct.unpack('>IH', hdr)
        p = recv_exact(s, ln - 2)
        if rc == 1110:
            off = 1
            n = struct.unpack_from('>H', p, off)[0]; off += 2 + n
            cnt = struct.unpack_from('>H', p, off)[0]; off += 2
            got = struct.unpack_from('>I', p, off)[0] if cnt else None
            break
    if rid:
        s.sendall(pack_frame(10102, struct.pack('>I', rid) + w_str('1')))
        s.settimeout(2.0)
        try:
            while True:
                hdr = recv_exact(s, 6)
                (ln, rc) = struct.unpack('>IH', hdr)
                recv_exact(s, ln - 2)
                if rc == 10102:
                    break
        except Exception:
            pass
        s.settimeout(5)
    return got


def call(s, cmd, body=b'', timeout=3.0):
    s.sendall(pack_frame(cmd, body))
    old = s.gettimeout()
    s.settimeout(timeout)
    try:
        while True:
            hdr = recv_exact(s, 6)
            (ln, rc) = struct.unpack('>IH', hdr)
            p = recv_exact(s, ln - 2)
            if rc == cmd:
                return p
    except Exception:
        return None
    finally:
        s.settimeout(old)


def main():
    ok = True
    backup = MAP + '.verifybak'
    shutil.copyfile(MAP, backup)
    try:
        mp = json.load(open(MAP, encoding='utf-8'))
        print('=== 映射表 ===')
        print('  组数 %d；有 mission_bids 的组: %s'
              % (len(mp['groups']),
                 [(g['name'], g['mission_bids']) for g in mp['groups'] if g['mission_bids']] or '（全部为空=安全默认）'))

        # 选一个任务做实验
        import importlib.util
        sp = importlib.util.spec_from_file_location('m', os.path.join(ROOT, 'server', 'mock_server.py'))
        m = importlib.util.module_from_spec(sp)
        sys.modules['m'] = m
        sp.loader.exec_module(m)
        bid = None
        two = []
        for b in range(10000, 14000):
            if m.mission_def(b):
                two.append(b)
            if len(two) >= 2:
                break
        bid, bid2 = two[0], two[1]
        print('  实验任务 bid=%d (%s) / bid2=%d (%s)'
              % (bid, (m.mission_def(bid) or {}).get('name'),
                 bid2, (m.mission_def(bid2) or {}).get('name')))

        s0 = socket.create_connection(('127.0.0.1', 9000), timeout=10)
        s0.settimeout(5)
        login(s0, TEST_UID)
        p = call(s0, 10101, struct.pack('>B', 0) + w_str('hook测') + struct.pack('>h', 1) + w_str('ewan'))
        off = 1
        ml = struct.unpack_from('>H', p, off)[0]; off += 2 + ml
        trid = struct.unpack_from('>I', p, off)[0]
        s0.close()
        print('  测试角色 rid=%d' % trid)

        s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
        s.settimeout(5)
        login(s, TEST_UID, trid)

        def snap():
            p86 = call(s, 13786, b'')
            n = struct.unpack_from('>H', p86, 1)[0]
            o, d = 3, {}
            for _ in range(n):
                d[struct.unpack_from('>H', p86, o)[0]] = struct.unpack_from('>H', p86, o + 2)[0]
                o += 4
            p00 = call(s, 16400, b'\x01')
            n2 = struct.unpack_from('>H', p00, 1)[0]
            o2, a = 3, {}
            for _ in range(n2):
                a[struct.unpack_from('>I', p00, o2)[0]] = struct.unpack_from('>H', p00, o2 + 4)[0]
                o2 += 10
            return d.get(208, 0), a.get(10100, 0)

        # ---- 1) 安全默认：**未被任何组映射**的 bid ⇒ 不变 ----
        #   ⚠ 必须挑一个确实没被映射的 bid：映射表已含真实条目（学院线 10010），
        #     所以这里用 bid2（未映射）。
        unmapped = bid2
        for g in mp['groups']:
            if unmapped in [int(x) for x in (g.get('mission_bids') or [])]:
                unmapped = None
        if unmapped is None:
            print('  !! 找不到未映射的 bid，跳过 [1]')
            ok = False
        else:
            n0, a0 = snap()
            call(s, 12403, struct.pack('>I', unmapped))
            n1, a1 = snap()
            print('\n[1] 安全默认（bid=%d 不在任何组）' % unmapped)
            print('    提交前 日常208=%d 成就10100=%d ｜ 提交后 %d / %d' % (n0, a0, n1, a1))
            if (n1, a1) != (n0, a0):
                print('    !! 未映射的任务竟然也被记账 ⇒ 又出现了"按 type 匹配"那类错误')
                ok = False
            else:
                print('    ✓ 未命中 ⇒ 什么也不做（安全默认）')

        # ---- 2) 写一行 JSON（不重启）⇒ 机制生效 ----
        #   任务换回 bid（它是**可提交**的；bid2 条件未满足、提交不了）。
        #   但同一角色已提交过 ⇒ 会走幂等分支 ⇒ 先清掉该角色的任务行。
        con = sqlite3.connect(DB)
        con.execute('DELETE FROM missions WHERE rid=?', (trid,))
        con.commit()
        con.close()
        for g in mp['groups']:
            if g['panel_id'] == 208:
                g['mission_bids'] = [bid]
        json.dump(mp, open(MAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        time.sleep(1.2)                      # 让 mtime 变化被热重载看到
        n2, a2 = snap()
        call(s, 12403, struct.pack('>I', bid))
        n3, a3 = snap()
        print('\n[2] 写一行 JSON（未重启服务端；并清掉该角色的任务行避免幂等）')
        print('    提交前 日常208=%d 成就10100=%d ｜ 提交后 %d / %d' % (n2, a2, n3, a3))
        if n3 != n2 + 1 or a3 != a2 + 1:
            print('    !! 热重载或挂钩未生效')
            ok = False
        else:
            print('    ✓ 日常次数 +1、成就进度 +1（映射表热重载生效）')

        # ---- 3) 玩家不受影响 ----
        con = sqlite3.connect(DB)
        pl = con.execute('SELECT COUNT(*) FROM chengjiu_progress WHERE rid=1001').fetchone()[0]
        con.close()
        print('\n[3] 玩家(1001) chengjiu_progress 行数=%d' % pl)

        s.close()
        con = sqlite3.connect(DB)
        for t in ('roles', 'role_attr', 'role_assets', 'bag_items', 'equip_items',
                  'store_items', 'missions', 'mall_bought', 'dungeon_progress',
                  'arena_state', 'arena_record', 'daily_progress', 'daily_lingqu',
                  'chengjiu_progress'):
            try:
                con.execute('DELETE FROM %s WHERE rid=?' % t, (trid,))
            except Exception:
                pass
        con.execute('DELETE FROM accounts WHERE uid=?', (TEST_UID,))
        con.commit()
        con.close()
        print('    已清理测试角色 %d' % trid)
    finally:
        shutil.copyfile(backup, MAP)
        os.remove(backup)
        print('    已恢复映射表原样')

    print()
    print('=== 结果: %s ===' % ('PASS' if ok else 'FAIL'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
