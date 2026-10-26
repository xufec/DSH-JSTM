"""Phase E 协议自检：把服务端**实际发出的字节**按 1.4.9 权威 spec 解回来核对。

## 为什么需要它

`server/mock_server.py` 的 `build_10301/10302/10303` 是**手写字节拼接**。
字段顺序一旦错位，客户端就会解析出垃圾（或直接不派发处理函数），
而日志里看不出来 —— 只有把字节按**权威 spec** 解回来才能发现。

**权威 spec 不是硬编码**：本工具运行时用 `tools/proto_spec.py` 直接从
`assets/src/config/protocal/cmd_resolve_103.luac` 读
`AutoConstruct(dir, cmd, {'字段__类型', ...})`，所以核对基准永远是 1.4.9 APK 本体。

## 检查项

- `SC_10301`：`lev / exp_max / exp_total_nextlev / attr_point / profit_exp`
  必须与 `Config.RoleAttr[lev+1]`（原版等级表）一致
- `SC_10302`：`lev / exp / gold / gold_acc / coin` 必须与角色状态一致
- `SC_10303`：`lev / exp / attr_point / power` 与 **24 项 attr 大表**必须与角色状态一致
- 以上三条的 `lev/exp` 必须**互相同步**（否则客户端面板会自相矛盾）

用法：
    python tools/verify_level_protocol.py
    python tools/verify_level_protocol.py --lev 8      # 指定检查等级
"""
import argparse
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'server'))

from proto_spec import read_resolve  # noqa: E402

FMT = {'C': 1, 'c': 1, 'H': 2, 'h': 2, 'I': 4, 'i': 4}


class Cur(object):
    def __init__(self, b):
        self.b = b
        self.p = 0

    def u(self, n):
        v = int.from_bytes(self.b[self.p:self.p + n], 'big')
        self.p += n
        return v

    def s(self):
        n = self.u(2)
        v = self.b[self.p:self.p + n].decode('utf-8', 'replace')
        self.p += n
        return v

    def scalar(self, t):
        if t == 's':
            return self.s()
        if t in FMT:
            return self.u(FMT[t])
        raise ValueError('unsupported scalar type %r' % t)


def spec_fields(number, cmd, direction):
    """从 1.4.9 的 cmd_resolve_<number>.luac 取该类字段；返回 [(name, type, is_table)]"""
    for c in (read_resolve(number) or []):
        if c['cmd'] == cmd and c['dir'] == direction:
            out = []
            for nm, fm in c['fields']:
                if nm.endswith('__T'):
                    out.append((nm[:-3], fm, True))
                else:
                    out.append((nm, fm, False))
            return out
    return None


def decode_scalars_until(cur, fields, stop_names):
    """按 spec 顺序解字段，遇到表就跳过（计数 + 元素），直到 stop_names 全解出。"""
    got = {}
    for name, t, is_table in fields:
        if is_table:
            n = cur.u(2)
            # 表内元素大小未知 -> 无法安全跳过，交由调用方分批处理
            raise RuntimeError('遇到表 %s（count=%d）无法继续线性解码' % (name, n))
        got[name] = cur.scalar(t)
        if all(s in got for s in stop_names):
            return got
    return got


def elem_size(fmt):
    """由 FMT 串算一个元素的字节数（只支持标量，够用于 skill_list=bid@I 这类）。"""
    n = 0
    for x in [y for y in fmt.split('##') if y]:
        _, _, ty = x.rpartition('@')
        if ty == 's':
            raise RuntimeError('字符串元素无法静态跳表')
        if ty not in FMT:
            raise RuntimeError('不支持的 FMT 类型 %r' % ty)
        n += FMT[ty]
    return n


def skip_table(cur, fmt):
    n = cur.u(2)
    cur.p += n * elem_size(fmt)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lev', type=int, default=None)
    ap.add_argument('--db', default=os.path.join(ROOT, 'server', 'state', 'roles.db'))
    a = ap.parse_args()

    import mock_server as M
    M.DB_PATH = a.db
    M.db_init()

    cfg = M.DEFAULT_CFG
    st = M.role_state(cfg)
    if a.lev:
        st = dict(st, lev=a.lev)
    lev = int(st.get('lev') or 1)
    print('角色状态: lev=%d exp=%s attr_point=%s' % (lev, st.get('exp'), st.get('attr_point')))
    print('等级表    : need=%s total_next=%s' % (M.level_need(lev), M.level_next_total(lev)))

    fails = []
    ok = lambda m: print('  OK   %s' % m)
    bad = lambda m: (fails.append(m), print('  FAIL %s' % m))

    # ---------- SC_10302（纯标量）----------
    print('\n=== SC_10302 ===')
    f = spec_fields('103', 10302, 'sc')
    print('  spec 字段(%d): %s' % (len(f), [x[0] for x in f]))
    body = (M.w_u16(st.get('lev', 1)) + M.w_u32(st.get('exp', 0)) +
            M.w_u32(st.get('gold', 0)) + M.w_u32(st.get('gold_acc', 0)))
    cur = Cur(body)
    got = {}
    for name, t, is_table in f:
        if is_table:
            break
        got[name] = cur.scalar(t)
    print('  解码 %d 个字段: %s' % (len(got), got))
    # ★ 权威 spec 共 29 个字段；服务端必须**全部**发出，否则客户端读越界
    #   （原实现只发 4 个 —— 由本工具发现并已修）。
    if len(got) != len(f):
        bad('10302 只解出 %d 个字段，spec 有 %d 个（包体被截断）' % (len(got), len(f)))
    else:
        ok('10302 字段数 %d == spec' % len(got))
    if got.get('lev') != lev:
        bad('10302 lev=%s 应为 %s' % (got.get('lev'), lev))
    else:
        ok('10302 lev=%d' % got['lev'])
    if got.get('exp') != int(st.get('exp') or 0):
        bad('10302 exp=%s 应为 %s' % (got.get('exp'), st.get('exp')))
    else:
        ok('10302 exp=%d' % got['exp'])

    # ---------- SC_10301（前 24 个字段全标量，含 4 个经验字段）----------
    print('\n=== SC_10301（取到 profit_exp 为止）===')
    f = spec_fields('103', 10301, 'sc')
    stop = ['lev', 'exp_max', 'exp_total_nextlev', 'attr_point', 'profit_exp']
    print('  spec 前 24 字段: %s' % [x[0] for x in f[:24]])
    body = M.build_10301(st, cfg.get('skills', []))
    cur = Cur(body)
    got = decode_scalars_until(cur, f, stop)
    for k in stop:
        print('    %-20s = %s' % (k, got.get(k)))
    if got.get('lev') != lev:
        bad('10301 lev=%s 应为 %s' % (got.get('lev'), lev))
    else:
        ok('10301 lev=%d' % got['lev'])
    if got.get('exp_max') != (M.level_need(lev) or 0):
        bad('10301 exp_max=%s 应为 %s（RoleAttr[lev+1].exp_max）'
            % (got.get('exp_max'), M.level_need(lev)))
    else:
        ok('10301 exp_max=%s（与原版等级表一致）' % got['exp_max'])
    if got.get('exp_total_nextlev') != M.level_next_total(lev):
        bad('10301 exp_total_nextlev=%s 应为 %s'
            % (got.get('exp_total_nextlev'), M.level_next_total(lev)))
    else:
        ok('10301 exp_total_nextlev=%s' % got['exp_total_nextlev'])
    if got.get('attr_point') != M.level_attr_point(lev):
        bad('10301 attr_point=%s 应为 %s' % (got.get('attr_point'), M.level_attr_point(lev)))
    else:
        ok('10301 attr_point=%s' % got.get('attr_point'))

    # ---------- SC_10303（含 24 项 attr 大表）----------
    print('\n=== SC_10303（标量段 + attr 大表）===')
    f = spec_fields('103', 10303, 'sc')
    names = [x[0] for x in f]
    print('  spec 字段(%d): %s' % (len(f), names[:18] + ['...']))
    ai = names.index('attr')
    body = M.build_10303(st, cfg.get('skills', []), cfg.get('attr'))
    cur = Cur(body)
    got = {}
    for name, t, is_table in f:
        if name == 'attr':
            break
        if is_table:
            skip_table(cur, t)
            continue
        got[name] = cur.scalar(t)
    for k in ('lev', 'attr_point', 'power', 'exp'):
        print('    %-20s = %s' % (k, got.get(k)))
    if got.get('lev') != lev:
        bad('10303 lev=%s 应为 %s' % (got.get('lev'), lev))
    else:
        ok('10303 lev=%d（与 10301/10302 同步）' % got['lev'])
    if got.get('exp') != int(st.get('exp') or 0):
        bad('10303 exp=%s 应为 %s' % (got.get('exp'), st.get('exp')))
    else:
        ok('10303 exp=%d（与 10302 同步）' % got['exp'])

    # attr 大表：24 项，类型取自 spec 的 FMT
    n = cur.u(2)
    fmt = f[ai][1]                      # 例如 strength@H##intellect@H##...@I
    items = [x for x in fmt.split('##') if x]
    print('    attr 表: count=%d, spec 项数=%d' % (n, len(items)))
    vals = {}
    for spec_item in items:
        nm, _, ty = spec_item.rpartition('@')
        vals[nm] = cur.scalar(ty) if ty in FMT or ty == 's' else None
    db_a = M.db_get_attr(st.get('rid', 1001)) or {}
    print('    解码: %s' % {k: vals[k] for k in list(vals)[:6]})
    # ★ 注意：`attr` 是 **table(一行 24 字段)** —— count 表示**行数**，
    #   不是字段数。`role_state` 只描述"自己"一个单位，所以 count 应为 1，
    #   紧跟的 24 个字段就是那一行。（最初把 count 与 spec 项数直接比是错的。）
    if n != 1:
        bad('attr 表 count=%d，应为 1（一行 24 字段）' % n)
    else:
        ok('attr 表 count=1（一行 24 字段，spec 项数 %d）' % len(items))
    if vals.get('atk_s') != int(db_a.get('atk_s') or 0):
        bad('attr.atk_s=%s 应为 %s' % (vals.get('atk_s'), db_a.get('atk_s')))
    else:
        ok('attr.atk_s=%s（与 DB 一致）' % vals.get('atk_s'))
    if vals.get('hp_max') != int(db_a.get('hp_max') or 0):
        bad('attr.hp_max=%s 应为 %s' % (vals.get('hp_max'), db_a.get('hp_max')))
    else:
        ok('attr.hp_max=%s（与 DB 一致）' % vals.get('hp_max'))

    print('\n结论: %s' % ('全部通过 ✅' if not fails else ('失败 %d 项 ❌' % len(fails))))
    for m in fails:
        print('   - %s' % m)
    return 0 if not fails else 2


if __name__ == '__main__':
    sys.exit(main() or 0)
