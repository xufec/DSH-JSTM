# -*- coding: utf-8 -*-
"""四系统语义自检：伙伴 / 背包 / 战斗 / 魂技。

和 `tools/probe_silent_cmds.py` 的区别：探针只回答"有没有回包"，本工具回答
"**回的内容对不对**" —— 用**服务端模块自己的输出**做基准（字节级比对），
并检查 DB 前后一致性（如穿装备不能凭空多/少物品）。

流程：临时建号 → 登录 1 区 → 建角 → 进角色 → 逐系统自检 → **清理账号与角色行**。

用法：
    python tools/verify_systems.py            # 全部四系统
    python tools/verify_systems.py 背包 战斗   # 只跑其中几个
"""
import json
import os
import socket
import sqlite3
import struct
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'server'))
HOST, PORT = '127.0.0.1', 9000
DB = os.path.join(ROOT, 'server', 'state', 'roles.db')

UID = 'syschk_%d' % int(time.time())
PWD = 'sys123456'
ZONE = '1'

PASS, FAIL, SKIP = [], [], []


def ok(sysname, msg):
    PASS.append((sysname, msg)); print('  OK   %s' % msg)


def bad(sysname, msg):
    FAIL.append((sysname, msg)); print('  FAIL %s' % msg)


def skip(sysname, msg):
    SKIP.append((sysname, msg)); print('  SKIP %s' % msg)


# ── 协议小工具 ─────────────────────────────────────────────────────────
_sock = None
_buf = b''


def frame(cmd, body=b''):
    return struct.pack('>IH', len(body) + 2, cmd) + body


def tlv(**kv):
    b = struct.pack('>H', len(kv))
    for k, v in kv.items():
        v = str(v).encode()
        b += struct.pack('>H', len(k)) + k.encode() + struct.pack('>H', len(v)) + v
    return b


def drain(seconds=2.0):
    """收帧，直到 `seconds` 用完（**中途空闲不提前退出**）。

    ★ 2026-10-17 修：原来 `except socket.timeout: break` —— 只要 1 秒没数据就返回，
      于是"服务端每 2.5 秒推一个战斗回合"这种**有节奏的推送**会被判成"没有回合帧"
      （工具误报过一次"战斗回合推进停住"）。现在按**截止时间**收，空闲就继续等。
    """
    global _buf
    out = []
    end = time.time() + seconds
    while time.time() < end:
        try:
            d = _sock.recv(65536)
        except socket.timeout:
            continue
        except Exception:
            break
        if not d:
            break
        _buf += d
        while len(_buf) >= 6:
            ln = struct.unpack_from('>I', _buf, 0)[0]
            if len(_buf) < 4 + ln:
                break
            cmd = struct.unpack_from('>H', _buf, 4)[0]
            out.append((cmd, _buf[6:4 + ln]))
            _buf = _buf[4 + ln:]
    return out


def send(cmd, body=b''):
    _sock.sendall(frame(cmd, body))


def ask(cmd, body=b'', wait=1.5):
    send(cmd, body)
    return [b for c, b in drain(wait) if c == cmd]


# ── DB 快照 ───────────────────────────────────────────────────────────
def snapshot(rid):
    con = sqlite3.connect(DB, timeout=10)
    bag = [dict(zip(('bag_item_id', 'bid', 'quantity', 'pos'), r)) for r in con.execute(
        'SELECT item_id,bid,quantity,pos FROM bag_items WHERE rid=? ORDER BY pos', (rid,))]
    eq = [dict(zip(('item_id', 'bid', 'slot'), r)) for r in con.execute(
        'SELECT item_id,bid,slot FROM equip_items WHERE rid=? ORDER BY slot', (rid,))]
    con.close()
    return bag, eq


def main():
    want = sys.argv[1:] or ['伙伴', '背包', '战斗', '魂技']
    global _sock
    _sock = socket.create_connection((HOST, PORT), timeout=8)
    _sock.settimeout(1.0)

    # 登录 + 建角 + 进角色
    send(1110, tlv(account=UID, token=PWD, enter_srv_id=ZONE))
    got = drain(1.5)
    if not any(c == 1110 and b and b[0] == 1 for c, b in got):
        print('!! 登录失败，退出'); return 2
    con = sqlite3.connect(DB, timeout=10)
    row = con.execute('SELECT rid FROM roles WHERE uid=? AND srv_id=?', (UID, ZONE)).fetchone()
    con.close()
    if not row:
        nm = UID[-8:]
        send(10101, struct.pack('>B', 1) + struct.pack('>B', len(nm)) + nm.encode()
             + struct.pack('>B', 1) + struct.pack('>H', 1001))
        drain(1.5)
        con = sqlite3.connect(DB, timeout=10)
        row = con.execute('SELECT rid FROM roles WHERE uid=? AND srv_id=?', (UID, ZONE)).fetchone()
        con.close()
    if not row:
        print('!! 建角失败，退出'); return 2
    rid = int(row[0])
    send(10102, struct.pack('>I', rid) + struct.pack('>B', int(ZONE)))
    drain(2.0)
    print('== 自检账号 %s ｜ rid=%d ｜ 区=%s ==\n' % (UID, rid, ZONE))

    from partner import service as psvc
    from skill import service as ssvc
    from inventory.service import db_bag_get, BAG_MAIN
    from attribute.service import attr_row_bytes, db_role_attr
    from role.storage import role_state
    from core.runtime import CFG

    # ★★ 2026-10-17：**先把配置装进运行时**。`CFG` 只在 mock_server.main() 里装配，
    #   工具只 import 时 CFG == {} ⇒ 之前所有依赖 CFG 的判断都是默认值（误判过一次
    #   equip_type_slot）。这里用与服务端**同一个** build_cfg/publish_cfg。
    import mock_server as _ms_cfg
    _cfg = _ms_cfg.publish_cfg(_ms_cfg.build_cfg())
    print('  .. 配置已装载：%d 个键，equip_type_slot=%s'
          % (len(_cfg), _cfg.get('equip_type_slot')))

    # ── 伙伴 ────────────────────────────────────────────────────────
    if '伙伴' in want:
        print('-- 伙伴系统 --')
        try:
            r11200 = ask(11200)
            if r11200 and len(r11200[0]) >= 4:
                ok('伙伴', '11200 面板容器：%d 字节 %s' % (len(r11200[0]), r11200[0][:8].hex(' ')))
            else:
                bad('伙伴', '11200 无应答/过短')
            r11215 = ask(11215)
            if r11215:
                exp = psvc.build_panel_11215(rid)
                if r11215[0] == exp:
                    ok('伙伴', '11215 partner_list 与 partner.service 输出**字节一致**（%d 字节）' % len(exp))
                else:
                    bad('伙伴', '11215 与 partner.service 输出不一致（收到 %d 字节 / 期望 %d 字节）'
                        % (len(r11215[0]), len(exp)))
            else:
                bad('伙伴', '11215 无应答')
            owned = psvc.owned_map(rid)
            r11206 = ask(11206)
            if r11206:
                ok('伙伴', '11206 扩容应答：code=%d，%d 字节' % (r11206[0][0] if r11206[0] else -1, len(r11206[0])))
            else:
                bad('伙伴', '11206 无应答')
            ok('伙伴', '已拥有伙伴 %d 个（DB 真值）' % len(owned))

            # ── 养成链：兑换(11216) → 面板反映 → 喂食(HTTP GM) → lev/exp/金币变化 ──
            try:
                import mock_server as _ms
                import urllib.request
                _bids = [int((p or {}).get('bid') or 0) for p in (psvc._live_list or [])]
                _bids = [b for b in _bids if b]
                pb = _bids[0] if _bids else 0
                if not pb:
                    skip('伙伴', '伙伴配置表为空，跳过养成链')
                else:
                    r = ask(11216, struct.pack('>I', pb) + struct.pack('>B', 0))
                    code = r[0][0] if r else None
                    if code == 1:
                        ok('伙伴', '11216 兑换伙伴 %d → code=1' % pb)
                    else:
                        bad('伙伴', '11216 兑换伙伴 %d → code=%s' % (pb, code))
                    owned2 = psvc.owned_map(rid)
                    if pb in owned2:
                        ok('伙伴', '兑换后 role_heros 里出现 bid=%d（lev=%s exp=%s）'
                           % (pb, owned2[pb].get('lev'), owned2[pb].get('exp')))
                    else:
                        bad('伙伴', '11216 回了 code=1 但 role_heros 里没有 bid=%d' % pb)
                    r2 = ask(11215)
                    if r2 and r2[0] == psvc.build_panel_11215(rid):
                        ok('伙伴', '兑换后 11215 面板与模块输出仍**字节一致**')
                    else:
                        bad('伙伴', '兑换后 11215 与模块输出不一致')
                    # 喂食：先给钱，再打 GM 端点
                    from currency.service import db_set_assets, db_get_assets
                    db_set_assets(rid, {'gold': 500000})
                    before = psvc.owned_map(rid).get(pb, {})
                    url = ('http://%s:%s/DSH_ADMIN/partner_feed?rid=%d&bid=%d&n=2'
                           % (HOST, _cfg.get('http_port', 8080), rid, pb))
                    try:
                        with urllib.request.urlopen(url, timeout=8) as resp:
                            body_json = json.loads(resp.read().decode('utf-8'))
                    except Exception as _eu:
                        body_json = {'_err': repr(_eu)}
                    after = psvc.owned_map(rid).get(pb, {})
                    gold_after = db_get_assets(rid).get('gold')
                    if body_json.get('ok') and gold_after is not None and gold_after < 500000:
                        ok('伙伴', '喂食成功：金币 %d→%s，lev %s→%s，exp %s→%s'
                           % (500000, gold_after, before.get('lev'), after.get('lev'),
                              before.get('exp'), after.get('exp')))
                    else:
                        bad('伙伴', '喂食未生效/未扣费: %r（lev %s→%s）'
                            % (body_json, before.get('lev'), after.get('lev')))
            except Exception as _ep:
                bad('伙伴', '养成链自检异常: %r' % (_ep,))
        except Exception as e:
            bad('伙伴', '自检异常: %r' % (e,))

    # ── 背包 ────────────────────────────────────────────────────────
    if '背包' in want:
        print('-- 背包系统 --')
        try:
            bag0, eq0 = snapshot(rid)
            r = ask(10502, struct.pack('>B', 1) + struct.pack('>I', rid))
            if r:
                n = struct.unpack_from('>H', r[0], 1)[0] if len(r[0]) >= 3 else -1
                if n == len(bag0):
                    ok('背包', '10502 背包条目数 = DB 真值（%d 条）' % n)
                else:
                    bad('背包', '10502 条目数 %d ≠ DB %d' % (n, len(bag0)))
            else:
                bad('背包', '10502 无应答')

            # 穿一件装备：验证"物品守恒 + 从背包移到装备"
            # ★★ 2026-10-17：新号背包是空的 ⇒ 主动**发一件真装备 + 一件非装备（礼包）**，
            #   才能同时验证「穿装守恒」与「非装备被拒」两条（后者正是 10511 的可疑区）。
            from inventory.service import db_bag_add
            EQ_BID = 40001      # 见习长枪（type=100 → slot 1，来自 item_config）
            GIFT_BID = 30800    # 福利礼盒（type=6，不在 equip_type_slot ⇒ 必须被拒）
            db_bag_add(rid, EQ_BID, 1)
            db_bag_add(rid, GIFT_BID, 1)
            bag0, eq0 = snapshot(rid)          # ★ 发放后重新取基准（否则比对的是空背包）
            what = {EQ_BID: '装备', GIFT_BID: '礼包'}
            cand = [it for it in snapshot(rid)[0] if it['bid'] in what]
            equipped = None
            for it in cand:
                r = ask(10511, struct.pack('>I', it['bag_item_id']) + struct.pack('>I', 0)
                        + struct.pack('>I', 0), 1.5)
                code = r[0][0] if r else None
                if it['bid'] == GIFT_BID:
                    if code == 0:
                        ok('背包', '10511 拒绝非装备（礼盒 30800，code=0：%r）'
                           % (r[0][3:3 + r[0][2]].decode('utf-8', 'replace') if r and len(r[0]) > 3 else ''))
                    else:
                        bad('背包', '10511 **接受**了非装备（礼盒 30800，code=%s）⇒ 会占装备位' % code)
                elif code == 1:
                    equipped = it
                else:
                    bad('背包', '10511 拒绝**真装备** 40001（code=%s）' % code)
            if equipped is None:
                bad('背包', '真装备 40001 没能穿上，跳过守恒检查')
            else:
                bag1, eq1 = snapshot(rid)
                moved = len(bag0) - len(bag1)
                gained = len(eq1) - len(eq0)
                gift_kept = any(b['bid'] == GIFT_BID for b in bag1)
                if moved == 1 and gained == 1 and gift_kept and not any(
                        b['bag_item_id'] == equipped['bag_item_id'] for b in bag1):
                    ok('背包', '10511 穿装：装备由背包进装备槽（背包 %d→%d，装备 %d→%d；**被拒的礼盒仍在背包**）'
                        % (len(bag0), len(bag1), len(eq0), len(eq1)))
                else:
                    bad('背包', '10511 穿装后异常：背包 %d→%d，装备 %d→%d，礼盒还在=%s'
                        % (len(bag0), len(bag1), len(eq0), len(eq1), gift_kept))
                r2 = ask(10502, struct.pack('>B', 1) + struct.pack('>I', rid))
                if r2 and len(r2[0]) >= 3:
                    n2 = struct.unpack_from('>H', r2[0], 1)[0]
                    if n2 == len(bag1):
                        ok('背包', '穿装后 10502 与 DB 一致（%d 条）' % n2)
                    else:
                        bad('背包', '穿装后 10502 条目数 %d ≠ DB %d' % (n2, len(bag1)))
                # 换装（同部位第二件）—— 走 eqm_item_id != 0 的分支
                db_bag_add(rid, 40002, 1)
                bag2, eq2 = snapshot(rid)
                new_it = [it for it in bag2 if it['bid'] == 40002]
                if new_it:
                    r3 = ask(10511, struct.pack('>I', new_it[0]['bag_item_id'])
                             + struct.pack('>I', equipped['bag_item_id'])
                             + struct.pack('>I', 0), 1.5)
                    code3 = r3[0][0] if r3 else None
                    bag3, eq3 = snapshot(rid)
                    eq_bids = sorted(e['bid'] for e in eq3)
                    bag_bids = sorted(b['bid'] for b in bag3)
                    if code3 == 1 and 40002 in eq_bids and 40001 not in eq_bids \
                            and 40001 in bag_bids:
                        ok('背包', '10511 换装：新装备进槽、旧装备回背包（装备=%s 背包含 40001）'
                           % eq_bids)
                    else:
                        bad('背包', '10511 换装异常：code=%s 装备=%s 背包=%s（旧装备可能丢失）'
                            % (code3, eq_bids, bag_bids))

            # ── 扩容(10552) / 删除(10557) / 入仓(10554) ──
            #   ⚠ `db_get_bag_volume` 在 mock_server 里（不在 inventory.service —— 第一版
            #     自检从这里 import 失败，白白跳过三条检查）
            import mock_server as _msv
            v0 = _msv.db_get_bag_volume(rid, 1)
            r = ask(10552, struct.pack('>B', 1) + struct.pack('>B', 5) + struct.pack('>B', 0))
            v1 = _msv.db_get_bag_volume(rid, 1)
            if r and v1 == v0 + 5:
                ok('背包', '10552 扩容：DB 容量 %d→%d（+5），回包 code=%d' % (v0, v1, r[0][0]))
            else:
                bad('背包', '10552 扩容异常：DB 容量 %d→%d（期望 +5），回包=%r'
                    % (v0, v1, r[:1]))
            db_bag_add(rid, GIFT_BID, 1)
            _b, _ = snapshot(rid)          # ★ snapshot 返回 (背包, 装备)，别解包错
            del_it = next((it for it in _b if it['bid'] == GIFT_BID), None)
            if del_it:
                # CS_10557{bag_code:u8, args:table(id:u32)} = bag_code + u16 count + ids
                body = struct.pack('>B', 1) + struct.pack('>H', 1) + struct.pack('>I', del_it['bag_item_id'])
                r = ask(10557, body)
                left = snapshot(rid)[0]
                if r and r[0][0] == 1 and not any(x['bag_item_id'] == del_it['bag_item_id'] for x in left):
                    ok('背包', '10557 删除：物品 %d 从背包移除（剩 %d 条）'
                       % (del_it['bag_item_id'], len(left)))
                else:
                    bad('背包', '10557 删除异常：code=%s 背包剩 %d 条（原 %d）'
                        % (r[0][0] if r else None, len(left), len(_b)))
            # 入仓：把一件装备从背包 (code 1) 移到仓库 (code 4)
            db_bag_add(rid, 40003, 1)
            _b2, _ = snapshot(rid)
            mv = next((it for it in _b2 if it['bid'] == 40003), None)
            if mv:
                from inventory.service import db_store_get, STORAGE_CODE
                s0 = len(db_store_get(rid, STORAGE_CODE))
                body = (struct.pack('>B', 1) + struct.pack('>B', STORAGE_CODE) +
                        struct.pack('>I', mv['bag_item_id']))
                r = ask(10554, body)
                s1 = len(db_store_get(rid, STORAGE_CODE))
                bag_now, _ = snapshot(rid)
                gone = not any(it['bag_item_id'] == mv['bag_item_id'] for it in bag_now)
                if r and s1 == s0 + 1 and gone:
                    ok('背包', '10554 入仓：物品从背包移入仓库（仓库 %d→%d，背包已移除）' % (s0, s1))
                else:
                    bad('背包', '10554 入仓异常：仓库 %d→%d，背包已移除=%s，回包=%s'
                        % (s0, s1, gone, (r[0][:6].hex(' ') if r else 'None')))

            # ── 格子数 / 刷新语义（★ 2026-10-17 用户报障"缺格子/空格/整理刷新"的正面）──
            #   ① SC_10510 必须到（格子最大值 = 客户端格子数来源）—— 此前服务端从不推
            #   ② SC_10503 必须到（删除通知）—— 10500 只"增量添加"，永远不移除
            #   ③ SC_10508 必须到（位置更新）—— 整理/压紧后客户端才换位置
            send(10502, struct.pack('>B', 1) + struct.pack('>I', rid))
            fr = drain(1.5)
            got_10510 = [b for c, b in fr if c == 10510]
            vol_db = _msv.db_get_bag_volume(rid, 1)
            if got_10510 and len(got_10510[0]) >= 3 and got_10510[0][1] == min(255, vol_db):
                ok('背包', 'SC_10510 已随 10502 下发：volume/open=%d（DB=%d）'
                   % (got_10510[0][1], vol_db))
            else:
                bad('背包', '未随 10502 收到 SC_10510（格子数）或数值不符：%r / DB=%s'
                    % ([b.hex(' ') for b in got_10510], vol_db))

            # 删除 → 10503 + 10508 + pos 压紧
            db_bag_add(rid, 40004, 1)
            db_bag_add(rid, 40005, 1)
            _bl, _ = snapshot(rid)
            victim = next((x for x in _bl if x['bid'] == 40004), None)
            if victim:
                send(10557, struct.pack('>B', 1) + struct.pack('>H', 1)
                     + struct.pack('>I', victim['bag_item_id']))
                fr = drain(1.5)
                codes = sorted(set(c for c, _ in fr))
                pos_now = [x['pos'] for x in snapshot(rid)[0]]
                compacted = pos_now == list(range(1, len(pos_now) + 1))
                if 10503 in codes and 10508 in codes and compacted:
                    ok('背包', '10557 删除 → 收到 10503(删除)+10508(位置)，pos 已压紧 %s'
                       % pos_now)
                else:
                    bad('背包', '10557 删除刷新不全：收到 %s，pos=%s（压紧=%s）'
                        % (codes, pos_now, compacted))
            # 整理 → 10508（位置更新）。★ 先**人为造一个空洞**（把第 1 件的 pos 改成 5），
            #   否则上一步刚压紧过、没有位置可改，服务端"无变化就不推 10508"是正确行为
            #   （第一版自检没造洞 ⇒ 误报"10509 没把位置发下来"）。
            try:
                _c = sqlite3.connect(DB, timeout=10)
                _c.execute('UPDATE bag_items SET pos=5 WHERE rid=? AND bag_code=1 AND pos=1', (rid,))
                _c.commit(); _c.close()
            except Exception as _e:
                print('  .. 造洞失败: %r' % (_e,))
            send(10509, struct.pack('>B', 1))
            fr = drain(1.5)
            codes = sorted(set(c for c, _ in fr))
            p08 = [b for c, b in fr if c == 10508]
            pos_now = [x['pos'] for x in snapshot(rid)[0]]
            if 10509 in codes and p08 and pos_now == list(range(1, len(pos_now) + 1)):
                ok('背包', '10509 整理 → 收到 SC_10508（位置更新，%d 字节），pos 压紧为 %s'
                   % (len(p08[0]), pos_now))
            else:
                bad('背包', '10509 整理没有把位置发下来：收到 %s，pos=%s'
                    % (codes, pos_now))
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            bad('背包', '自检异常: %r' % (e,))

    # ── 战斗 ────────────────────────────────────────────────────────
    if '战斗' in want:
        print('-- 战斗系统 --')
        try:
            # ★ 取怪必须走 `mock_server.scene_quest_extras` / `scene_mons`（scene.service 里
            #   没有前者）；而且**该角色没有任务链**时剧情怪不会刷 —— 所以候选要覆盖静态表
            #   与剧情表，并逐个试（服务端对"不在场景的怪"回 code=0 是**正确**行为）。
            import mock_server as _ms
            from scene.service import scene_mons
            scene = int(role_state(CFG).get('scene_id') or 10001)
            cands = []
            for sc in (scene, 10001, 10005):
                try:
                    cands += [int((m or {}).get('id') or 0) for m in (scene_mons(CFG, int(sc)) or [])]
                except Exception:
                    pass
                try:
                    _, _mm = _ms.scene_quest_extras(CFG, int(sc))
                    cands += [int((m or {}).get('id') or 0) for m in (_mm or [])]
                except Exception:
                    pass
            cands += [20001, 20022, 20040, 20003]
            seen, mon_ids = set(), []
            for c in cands:
                if c and c not in seen:
                    seen.add(c); mon_ids.append(c)
            mon_id, frames = 0, []
            for m in mon_ids:
                send(20002, struct.pack('>i', m))
                frames = drain(3.0)
                if any(c == 20002 and b and b[0] == 1 for c, b in frames):
                    mon_id = m
                    break
            if not mon_id:
                bad('战斗', '候选怪 %s 全部被拒（服务端回 code=0）' % (mon_ids[:8],))
                frames = []
            else:
                ok('战斗', 'CS_20002(mon=%d) → SC_20002 code=1（首只可用怪）' % mon_id)
                by = {}
                for c, b in frames:
                    by.setdefault(c, []).append(b)
                for want_cmd, label in ((20010, '进战斗数据'), (20012, '回合数据'), (20013, '回合数据2')):
                    if by.get(want_cmd):
                        ok('战斗', '%s SC_%d 已下发（%d 字节）' % (label, want_cmd, len(by[want_cmd][0])))
                if not any(by.get(c) for c in (20010, 20012, 20013)):
                    bad('战斗', '20002 成功但**没有** 20010/20012/20013 ⇒ 战斗链未推进')
                # 推进回合：★ 服务端**不用 CS_20014 驱动**（代码注释与实测：客户端不发它），
                #   回合由服务端定时器按 `battle_round_interval`（默认 2.5s）自动推
                #   ⇒ 这里就是**等**，收集 20012/20013（回合）与 20020/20023（结算）。
                if by.get(20010) or by.get(20012):
                    interval = float(_cfg.get('battle_round_interval', 2.5))
                    adv = drain(min(20.0, interval * 3 + 3))
                    codes = sorted(set(c for c, _ in adv))
                    rounds = [c for c in codes if c in (20012, 20013)]
                    if 20020 in codes or 20023 in codes:
                        ok('战斗', '服务端定时器自动推进：回合 %s → **结算** %s（无需 CS_20014）'
                           % (rounds, [c for c in codes if c in (20020, 20023)]))
                    elif rounds:
                        ok('战斗', '服务端定时器自动推进了回合 %s（%.1fs 内未结算，属正常：回合还没打完）'
                           % (rounds, interval * 3 + 3))
                    else:
                        bad('战斗', '20010 已下发但 %.1fs 内**没有** 20012/20013/20020 ⇒ 回合推进停住'
                            % (interval * 3 + 3))
            # 20008 / 20009 必须**回显**（2026-10-17 修：它们有 SC 定义，原来只记日志）
            r8 = ask(20008, struct.pack('>B', 1))
            r9 = ask(20009, struct.pack('>i', 10020))
            if r8 and len(r8[0]) >= 2:
                ok('战斗', '20008 自动战斗开关已回显（%d 字节）' % len(r8[0]))
            else:
                bad('战斗', '20008 无回包（有 SC_20008 定义 ⇒ 客户端会干等）')
            if r9 and len(r9[0]) >= 4:
                ok('战斗', '20009 选技能已回显 skill_id=%d' % struct.unpack_from('>I', r9[0], 0)[0])
            else:
                bad('战斗', '20009 无回包（有 SC_20009 定义）')
        except Exception as e:
            bad('战斗', '自检异常: %r' % (e,))

    # ── 魂技 ────────────────────────────────────────────────────────
    if '魂技' in want:
        print('-- 魂技系统 --')
        try:
            r = ask(10622, struct.pack('>I', 0))
            if r:
                exp = ssvc.build_10622(rid, 0)
                if r[0] == exp:
                    ok('魂技', '10622 已学技能列表与 skill.service 输出**字节一致**（%d 字节）' % len(exp))
                else:
                    bad('魂技', '10622 输出与 skill.service 不一致（收到 %d / 期望 %d 字节）'
                        % (len(r[0]), len(exp)))
            else:
                bad('魂技', '10622 无应答')
            r = ask(10601, struct.pack('>I', 0))
            if r and len(r[0]) >= 12:
                ok('魂技', '10601 hero_list 属性表（%d 字节）' % len(r[0]))
            else:
                bad('魂技', '10601 过短/无应答')
            # 学技能要花钱（skill.service.learn 会扣），新号 gold=0 ⇒ 先用**服务端自己的**
            # 资产接口注入金币，再测"学技能"闭环（顺带验证 currency 写入路径）。
            try:
                from currency.service import db_set_assets, db_get_assets
                db_set_assets(rid, {'gold': 100000})     # 签名是 (rid, values:dict)
                print('  .. 已注入金币 100000（当前 %r）' % (db_get_assets(rid).get('gold'),))
            except Exception as _eg:
                print('  !! 注入金币失败: %r' % (_eg,))
            rows0 = ssvc.learned_list(rid)
            cat = ssvc.catalog()
            if cat:
                bid0 = None
                have = set(int(x.get('bid') or 0) for x in rows0)
                for k in sorted(cat, key=lambda x: int(x)):
                    if int(k) not in have:
                        bid0 = int(k); break
                if bid0 is None:
                    skip('魂技', '目录里所有技能都已学，跳过"学新技能"闭环检查')
                else:
                    res = ssvc.learn(rid, bid0)
                    rows1 = ssvc.learned_list(rid)
                    if len(rows1) > len(rows0):
                        ok('魂技', 'skill.service.learn(%d) 后已学技能 %d→%d 条' % (bid0, len(rows0), len(rows1)))
                        r2 = ask(10622, struct.pack('>I', bid0))
                        if r2 and r2[0] == ssvc.build_10622(rid, bid0):
                            ok('魂技', '学技能后 10622 再次与模块输出一致')
                        else:
                            bad('魂技', '学技能后 10622 与模块输出不一致')
                    else:
                        bad('魂技', 'learn(%d) 后技能数没变（%d → %d），res=%r' % (bid0, len(rows0), len(rows1), res))
            else:
                skip('魂技', 'catalog() 为空，跳过学技能检查')
        except Exception as e:
            bad('魂技', '自检异常: %r' % (e,))

    # ── 清理 ────────────────────────────────────────────────────────
    try:
        con = sqlite3.connect(DB, timeout=10)
        rids = [int(r[0]) for r in con.execute('SELECT rid FROM roles WHERE uid=?', (UID,))]
        for t in ('roles', 'role_attr', 'role_assets', 'missions', 'bag_items', 'equip_items',
                  'store_items', 'role_heros', 'role_buffs', 'role_skills', 'dungeon_progress',
                  'chengjiu_progress', 'partner_state'):
            for r in rids:
                try:
                    con.execute('DELETE FROM %s WHERE rid=?' % t, (r,))
                except Exception:
                    pass
        con.execute('DELETE FROM accounts WHERE uid=?', (UID,))
        con.commit(); con.close()
    except Exception as e:
        print('  !! 清理失败: %r' % (e,))

    print('\n===== 汇总 =====')
    print('PASS %d ｜ FAIL %d ｜ SKIP %d' % (len(PASS), len(FAIL), len(SKIP)))
    for s, m in FAIL:
        print('  FAIL [%s] %s' % (s, m))
    for s, m in SKIP:
        print('  SKIP [%s] %s' % (s, m))
    return 1 if FAIL else 0


if __name__ == '__main__':
    sys.exit(main())
