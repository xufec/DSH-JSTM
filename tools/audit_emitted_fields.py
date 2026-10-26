#!/usr/bin/env python3
"""门禁 E：**"该发而未发"检查** —— 补四道审计共同的盲区。

## 为什么需要（本项目两次真实教训，都在四道审计全绿时漏掉）

| 案例 | 四道审计为什么没抓到 | 本门禁能否抓到 |
|---|---|---|
| `SC_20100.promote` 恒发**空表** ⇒ 变强面板右侧空白 | 审计只校验"发出去的字节合不合规格"，**不看规格要求的内容有没有发** | ✅ 报 `promote: 空表` |
| `SC_10922.act_list` 恒发**空表** ⇒ 全服活动状态根本没下发 | 同上（空表是"合法"的应答） | ✅ 报 `act_list: 空表` |

⇒ 判据：**规格里的 `table` 字段，若实际应答长度为 0，就是"该发而未发"的候选**，
必须给出理由（写入白名单）或修掉。

## 与既有审计的分工

| 审计 | 回答的问题 |
|---|---|
| `audit_specs_vs_fields.py` | 规格与 `fields.json` 一致吗（离线） |
| `audit_sc_conformance.py` | 默认应答的**字节长度**合规格吗（离线） |
| `audit_sc_live.py` | 在线应答的**字节长度**合规格吗 |
| `audit_dedicated.py` | 专用 handler 的**字节长度**合规格吗 |
| **本工具** | 应答**内容**是否"该发而未发"（空表 / 全零数值） |
| `lint_dispatch_shadow.py` | 专用实现会不会被靠前的分支遮蔽 |

用法：
    python tools/audit_emitted_fields.py            # 全量（需要服务端在线）
    python tools/audit_emitted_fields.py --selftest # 只跑灵敏度自检（不需要服务端）
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK = os.path.join(ROOT, 'server', 'mock_server.py')
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')
ALLOW = os.path.join(HERE, '_emitted_empty_allow.json')

# ★★ R84：**多版本尾部字段豁免名单**（每条都要有出处，不是"把告警关掉"）。
#   · 10302：1.4.11 比 1.4.9 多 `diamond:I`+`rainbow_diamond:I`（8B），
#            `tools/diff_role_specs.py` 逐字段比对确认；1.4.9 忽略尾部字节，
#            1.4.11 少发会解析越界 ⇒ 整条消息被丢弃（实测：主城按钮全隐藏、且不报错）。
#   · 10301：同族多版本尾部字段（多 1B）。
#   判据：**consumed == 规格长度 且 包更长**（即"多出来的都在尾部、前面全对"）才算豁免。
MULTI_VERSION_TAIL = {10301, 10302}


def tail_exempt(cmd, r):
    """★ R84：判断这条"长度不符"是否属于**多版本尾部字段**（可豁免）。

    判据（三条同时满足）：
      1. 命令在 `MULTI_VERSION_TAIL` 里（**显式名单**，不是通配）；
      2. 规格字段**全部解析成功**（`err is None`）—— 说明前面每个字段都对得上；
      3. 包**比规格长**（`consumed < len`）—— 多出来的只可能在**尾部**。
    反过来：**包比规格短**（少发）一定**不豁免** —— 那会让 1.4.11 解析越界、整条消息被丢弃。
    """
    return (int(cmd) in MULTI_VERSION_TAIL and not r.get('err')
            and r.get('consumed', 0) < r.get('len', 0))


# ---------------------------------------------------------------- 规格走查
def walk_report(fs, body, off, path, empties, zeros):
    """按规格走查应答，记录**空表**与**全零数值**。返回 (新偏移, 错误)。"""
    for f in fs:
        if not isinstance(f, dict):
            continue
        nm = f.get('name') or '?'
        ty = (f.get('type') or '').strip().lower()
        p = path + '.' + nm if path else nm
        if 'string' in ty:
            if off + 2 > len(body):
                return off, '%s: string 越界' % p
            n = int.from_bytes(body[off:off + 2], 'big')
            if n == 0:
                zeros.append(p + ':string')
            off += 2 + n
        elif ty.startswith('table') or f.get('items'):
            if off + 2 > len(body):
                return off, '%s: table 计数越界' % p
            cnt = int.from_bytes(body[off:off + 2], 'big')
            off += 2
            if cnt == 0:
                empties.append(p)
                continue
            items = f.get('items')
            if not items:
                return off, None            # 子表结构未知 ⇒ 停止（同 parse_full）
            for i in range(cnt):
                off, e = walk_report(items, body, off, '%s[]' % p, empties, zeros)
                if e:
                    return off, e
        else:
            size = 1
            if '64' in ty or '32' in ty:
                size = 4
            elif '16' in ty:
                size = 2
            if off + size > len(body):
                return off, '%s: 越界' % p
            w = int.from_bytes(body[off:off + size], 'big')
            if w == 0:
                zeros.append(p)
            off += size
        if off > len(body):
            return off, '%s: 越界 (off=%d len=%d)' % (p, off, len(body))
    return off, None


def audit_body(spec, body, cmd):
    empties, zeros = [], []
    off, err = walk_report(spec, body, 0, '', empties, zeros)
    return {'cmd': cmd, 'len': len(body), 'consumed': off, 'err': err,
            'empties': empties, 'zeros': zeros}


# ---------------------------------------------------------------- 命令集合
def _grab_set(src, name):
    """取 `name = frozenset([...])` / `[...]` / `(...)` 里的所有命令号。

    ★ 用**括号配对扫描**而不是正则：源里是 `= frozenset([`，任何
      "`=` 后面紧跟 `(`/`[`" 的正则都匹配不到 ⇒ 集合会静默解析成 0 条，
      审计就只剩下专用分支（本工具第一版正是如此，靠 `ded` 勉强跑着）。
    """
    m = re.search(name + r'\s*=', src)
    if not m:
        return set()
    i = m.end()
    # 跳过 `frozenset` / 空白，找到第一个左括号
    while i < len(src) and src[i] not in '([{':
        if src[i] in '\n;':
            break
        i += 1
    if i >= len(src) or src[i] not in '([{':
        return set()
    depth = 0
    j = i
    while j < len(src):
        if src[j] in '([{':
            depth += 1
        elif src[j] in ')]}':
            depth -= 1
            if depth == 0:
                break
        j += 1
    return set(int(x) for x in re.findall(r'\d{4,5}', src[i:j]))


def read_sets(src):
    src = re.sub(r'#[^\n]*', '', src)      # 注释里可能有括号/数字，先剥掉
    ded = set(int(m.group(1)) for m in re.finditer(r'if cmd == (\d{4,5}):', src))
    for m in re.finditer(r'if cmd in \(([^)]*)\):', src, re.S):
        ded |= set(int(x) for x in re.findall(r'\d{4,5}', m.group(1)))
    return ded, _grab_set(src, '_GENERIC_DEFAULT_CMDS'), _grab_set(src, '_UNSUPPORTED_ACTION_CMDS')


def load_specs():
    with open(FIELDS, encoding='utf-8') as f:
        fields = json.load(f)
    cs, sc = {}, {}
    for k, v in fields.items():
        c = v.get('cmd')
        if not c:
            continue
        if v.get('dir') == 'cs':
            cs.setdefault(str(c), v.get('fields') or [])
        elif v.get('dir') == 'sc':
            sc.setdefault(str(c), v.get('fields') or [])
    return cs, sc


# ---------------------------------------------------------------- 灵敏度自检
def selftest():
    """证明本工具**真能**抓到 R49b 那种"该发而未发"。"""
    cs, sc = load_specs()
    spec = sc.get('20100')
    if not spec:
        print('!! fields.json 里没有 SC_20100，无法自检')
        return 1
    import struct
    # 造一版"promote 空表"的 SC_20100（= R49b 修好之前服务端真正发的样子）
    bad = (struct.pack('>H', 3) + b'\x01' + struct.pack('>I', 133960) +
           b'\x02' + struct.pack('>I', 0) + b'\x03' + struct.pack('>I', 0) +
           struct.pack('>H', 0))
    # 造一版"promote 有 2 条"的
    good = (struct.pack('>H', 3) + b'\x01' + struct.pack('>I', 133960) +
            b'\x02' + struct.pack('>I', 0) + b'\x03' + struct.pack('>I', 0) +
            struct.pack('>H', 2) + b'\x01' + struct.pack('>H', 0) + b'\x02' + struct.pack('>H', 0))
    rb = audit_body(spec, bad, 20100)
    rg = audit_body(spec, good, 20100)
    print('== 灵敏度自检（SC_20100）==')
    print('  空 promote  : len=%d 消耗=%d empties=%s' % (rb['len'], rb['consumed'], rb['empties']))
    print('  有 2 条     : len=%d 消耗=%d empties=%s' % (rg['len'], rg['consumed'], rg['empties']))
    # 断言：**必须**在 bad 里检出 `promote`；在 good 里**不得**再报 `promote`
    #   （`promote[].val` 是子表、按设计为空 —— 它出现是正常的，走白名单）
    caught = 'promote' in rb['empties']
    cleared = 'promote' not in rg['empties']
    print('  检出 %s ／ 修好后不再报 %s' % ('✓' if caught else '✗', '✓' if cleared else '✗'))

    # 条件式豁免的"重新武装"必须也能自检：角色等级够高时**不得**被豁免掉
    ent = {'reason': 'x', 'when': {'role_lev_lt': 17}}

    def hit(lev):
        w = ent.get('when') or {}
        return lev is not None and lev < int(w['role_lev_lt'])
    low_ok, high_ok = hit(9), hit(70)
    print('  条件豁免: lev=9 生效 %s ／ lev=70 不生效（会照常告警）%s'
          % ('✓' if low_ok else '✗', '✓' if not high_ok else '✗'))

    ok = caught and cleared and low_ok and (not high_ok)

    # ★ R84：多版本尾部豁免的三条边界都要自检 ——
    #   ① 名单内 + 规格解析完 + 包更长 ⇒ **豁免**（10302 的真实情形）
    #   ② **包更短**（少发） ⇒ **不豁免**（那会让 1.4.11 越界丢消息）
    #   ③ 名单外 + 包更长 ⇒ **不豁免**（避免变成"通配豁免"）
    t1 = tail_exempt(10302, {'err': None, 'consumed': 114, 'len': 122})
    t2 = not tail_exempt(10302, {'err': None, 'consumed': 122, 'len': 114})
    t3 = not tail_exempt(99999, {'err': None, 'consumed': 114, 'len': 122})
    t4 = not tail_exempt(10302, {'err': 'x: 越界', 'consumed': 114, 'len': 122})
    print('  尾部豁免: 多尾字节 %s ／ 少发不放行 %s ／ 名单外不放行 %s ／ 解析出错不放行 %s'
          % ('✓' if t1 else '✗', '✓' if t2 else '✗',
             '✓' if t3 else '✗', '✓' if t4 else '✗'))
    ok = ok and t1 and t2 and t3 and t4

    print('  自检: %s' % ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--deep', action='store_true', help='同时列出深层（实体子表）空表明细')
    ap.add_argument('--timeout', type=float, default=2.0)
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())

    cs, sc = load_specs()
    src = open(MOCK, encoding='utf-8').read()
    ded, gen, uns = read_sets(src)

    pick = set()
    for c in sorted(ded | gen | uns):
        k = str(c)
        if k not in cs or k not in sc:
            continue
        if cs[k]:                     # 需要参数 ⇒ 不纳入（避免误触发副作用）
            continue
        pick.add(c)
    # 只调"CS 为空"的命令：这批的应答不依赖参数，送空 CS 是安全的。
    print('# 待查命令（CS 为空且有 SC 规格）: %d' % len(pick))

    import socket
    import struct
    from audit_sc_live import pack_frame, recv_exact, login

    s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
    login(s)
    s.settimeout(args.timeout)

    reports, mismatch = [], []
    for c in sorted(pick):
        try:
            s.sendall(pack_frame(c, b''))
            got = None
            while True:
                hdr = recv_exact(s, 6)
                ln, rcmd = struct.unpack('>IH', hdr)
                payload = recv_exact(s, ln - 2)
                if rcmd == c:
                    got = payload
                    break
        except Exception:
            try:
                s.close()
            except Exception:
                pass
            s = socket.create_connection(('127.0.0.1', 9000), timeout=10)
            login(s)
            s.settimeout(args.timeout)
            continue
        r = audit_body(sc[str(c)], got, c)
        # ★★ R84：**多版本尾部字段豁免**（带理由，不是"把告警关掉"）。
        #   本服对 `10301/10302` 刻意在 1.4.9 规格之后**多发尾部字段**，以兼容 1.4.11：
        #     · `10302`：1.4.11 比 1.4.9 多 `diamond:I` + `rainbow_diamond:I`（8 字节）
        #       —— `tools/diff_role_specs.py` 逐字段比对确认；1.4.9 **忽略**尾部多余字节，
        #       而 1.4.11 少发会**解析越界 ⇒ 整条消息被丢弃**（实测：主城功能按钮全隐藏且不报错）。
        #     · `10301`：同族处理（多 1 字节尾部字段）。
        #   ⇒ 用 1.4.9 的 spec 解析本服的包，**必然**报"消耗 X != Y"。
        #   这里按"**多余的是尾部字节**"豁免：consumed 等于规格长度、且包更长即放行。
        #   ⚠ 注意 `c` 在循环里是**字符串**（`sc[str(c)]`）—— 第一版直接
        #     `c in MULTI_VERSION_TAIL`（int 集合）恒为 False，豁免没生效。
        #   判据：**规格字段全部解析成功（err is None）且包更长** ⇒ 多出来的都在尾部。
        if tail_exempt(c, r):
            r['tail_extra'] = r['len'] - r['consumed']
            r['tail_ok'] = True
        reports.append(r)
        # ⚠ 第二版只清了 `err`，**没让下面这行长度判定跳过** ⇒ 依旧进 mismatch。
        #   现在用 `tail_ok` 显式放行"尾部多余字节"。
        if r['err'] or (r['consumed'] != r['len'] and not r.get('tail_ok')):
            mismatch.append(r)
    s.close()

    allow = {}
    if os.path.exists(ALLOW):
        with open(ALLOW, encoding='utf-8') as f:
            allow = json.load(f).get('allow', {})

    # ★ 只把**顶层**空表当告警：容器/实体子表（`10201.npcs[].member` 之类）天然为空，
    #   全量报会产生 476 条噪音 ⇒ 变成"没人看的审计"（本项目 METHODOLOGY §6 的老问题）。
    #   真实案例（`20100.promote` / `10922.act_list` / `17309.rank_list` / `13321.request_list`）
    #   **都在顶层**。深层用 `--deep` 另看，按模式聚合。
    def is_top(p):
        return ('.' not in p) and ('[]' not in p)

    warn, info_empty, deep = [], [], []

    # ★ 有些空表是**依赖角色状态**的（例：`20100.promote` 在 `lev < min(display_lev)=17`
    #   时本就该为空 —— 客户端也不会显示任何提升项）。允许白名单写条件式豁免：
    #     {"reason": "...", "when": {"role_lev_lt": 17}}
    #   条件成立 ⇒ 记为"已登记理由"；**不成立（角色等级够高）⇒ 仍然告警**，
    #   这样 R49b 那类真缺陷不会被条件豁免永久掩盖。
    role_lev = None
    try:
        import urllib.request
        st = json.loads(urllib.request.urlopen(
            'http://127.0.0.1:8080/DSH_ADMIN/status', timeout=3).read())
        role_lev = int(st['role']['level'])
    except Exception:
        pass

    def allow_hit(ent):
        if isinstance(ent, str):
            return True, ent
        if isinstance(ent, dict):
            w = ent.get('when') or {}
            if 'role_lev_lt' in w:
                if role_lev is None:
                    return False, ent.get('reason', '')
                return (role_lev < int(w['role_lev_lt'])), ent.get('reason', '')
            return True, ent.get('reason', '')
        return False, ''

    for r in reports:
        for e in r['empties']:
            key = '%d:%s' % (r['cmd'], e)
            if not is_top(e):
                deep.append(key)
                continue
            ent = allow.get(key)
            if ent is not None:
                ok_allow, why = allow_hit(ent)
                if ok_allow:
                    info_empty.append((key, why))
                    continue
                warn.append((r['cmd'], e))
                continue
            warn.append((r['cmd'], e))

    print('\n=== 「该发而未发」门禁（%d 条命令，role_lev=%s）==='
          % (len(reports), role_lev))
    print('  长度不符: %d' % len(mismatch))
    for r in mismatch:
        print('    ★ %-8d %s' % (r['cmd'], r['err'] or
                                 '消耗 %d != %d' % (r['consumed'], r['len'])))
    print('  ★ 顶层空表告警（未登记理由）: %d' % len(warn))
    for c, e in warn:
        print('    ▲ cmd=%-8d field=%s  ← 规格要 table，实际发空表' % (c, e))
    print('  顶层空表（已登记理由）: %d' % len(info_empty))
    for k, why in info_empty[:15]:
        print('    · %-26s %s' % (k, why[:66]))

    import collections
    agg = collections.Counter(x.split(':', 1)[1] for x in deep)
    print('  深层空表（信息项，聚合）: %d 处 / %d 种模式%s'
          % (len(deep), len(agg), '（--deep 看明细）' if args.deep else ''))
    if args.deep:
        for pat, n in agg.most_common(40):
            print('    · %-40s x%d' % (pat, n))

    nzero = sum(len(r['zeros']) for r in reports)
    print('  全零数值（信息项，不作为失败）: %d 项' % nzero)

    bad = bool(warn) or bool(mismatch)
    print('\n=== 结果: %s ===' % ('FAIL（有未登记的空表）' if bad else 'PASS'))
    print('  （白名单文件：%s；每条必须写明理由）' % os.path.relpath(ALLOW, ROOT))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
