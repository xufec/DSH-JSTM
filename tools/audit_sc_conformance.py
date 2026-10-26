#!/usr/bin/env python3
"""SC 默认应答一致性审计：验证服务端"成功但空"的默认响应**逐字节符合规格**。

## 定位

round35 的 `audit_specs_vs_fields.py` 审计的是 **CS 规格挖掘结果**（fields.json 本身对不对）。
本工具审计的是 **SC 侧对接**：`server/mock_server.py::_build_default_sc(cmd)` 按规格生成的
默认响应，能否被同一份规格**精确解析**（不多不少）。

响应器对 `table(...)` 一律发空表（计数 0），所以不需要子表线序 —— 但前提是：
**顶层每个标量字段的字节宽度必须与规格一致**。宽度错一个字节，后面所有字段就会整体错位，
客户端轻则显示乱值，重则崩。

## 关注点

`_build_default_sc` 里的宽度判定是按类型名做子串匹配：

    'string' → 2（空串）   'table' → 2（空表计数）
    '64' → 4              '32' → 4      '16' → 2
    '8'/'bool'/'char' → 1  其余 → 1（兜底）

于是这些类型会掉进兜底：
    · `D|DscXXXXfield|`（extract_fields 未解析的子表引用，直接成了类型字符串）
    · `l`（list）
    · `float` / `double`（无数字字符）
本工具把它们全部列出来，区分「确实错位」与「恰好也是 1 字节/空表、实际无害」。

用法：
    python tools/audit_sc_conformance.py            # 全量
    python tools/audit_sc_conformance.py --generic   # 只看 _GENERIC_DEFAULT_CMDS
    python tools/audit_sc_conformance.py --json out.json
"""
import argparse
import importlib.util
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIELDS = os.path.join(ROOT, 'protocol', 'fields.json')
MOCK = os.path.join(ROOT, 'server', 'mock_server.py')

SIZE = {
    'uint8': 1, 'int8': 1, 'bool': 1, 'char': 1, 'byte': 1,
    'uint16': 2, 'int16': 2,
    'uint32': 4, 'int32': 4, 'float': 4,
    'double': 8, 'uint64': 8, 'int64': 8,
}


def load_mock():
    """安全导入 mock_server（该文件有 __main__ 守卫，不会启动服务）。"""
    spec = importlib.util.spec_from_file_location('mock_server_audit', MOCK)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['mock_server_audit'] = mod
    spec.loader.exec_module(mod)
    return mod


def default_len(fields, msg_len=0):
    """按 _build_default_sc 的语义算期望字节数；返回 (长度, 未知类型列表)。

    msg_len: 首个名为 `msg` 的 string 字段实际写入的**字节数**
             （round41 起"未开放"应答会带提示文案，不再是空串）。
    """
    total = 0
    unknown = []
    msg_done = False
    for i, f in enumerate(fields):
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        ty = ((f.get('type') or '') if isinstance(f, dict) else '').strip()
        if i == 0 and nm in ('code', 'result'):
            total += 1
            continue
        t = ty.lower()
        if t.startswith('string'):
            if nm == 'msg' and not msg_done:
                total += 2 + msg_len
                msg_done = True
            else:
                total += 2
        elif t.startswith('table'):
            total += 2
        elif t in SIZE:
            total += SIZE[t]
        elif '64' in t:
            total += 4          # ← 可疑：64 位只写 4 字节
            unknown.append((nm, ty, '64bit->4'))
        elif '32' in t:
            total += 4
        elif '16' in t:
            total += 2
        elif '8' in t or 'bool' in t or 'char' in t:
            total += 1
        else:
            total += 1          # 兜底 1 字节
            unknown.append((nm, ty, 'fallback->1'))
    return total, unknown


def parse_full(body, fields):
    """通用规格解析（**允许非空表**，按 items 递归）。

    与 `parse_strict` 的分工：
      · `parse_strict` 用于**默认响应**审计 —— 此时表必须为空（计数 0）；
      · `parse_full` 用于**真机流量回放** —— 表里可能就是真实数据（如
        `SC_10924.act_list` 74 条、`SC_11215.partner_list` 53 条），
        必须按 `items` 递归解析，否则会把"真实实现"误判成规格不符。

    返回 (offset, errs, unverified)：
      unverified=True 表示遇到**无 items 的表**（`D|Dsc*|` 未解引用），
      字节长度不可知 ⇒ 该消息**无法校验**，不能算通过也不能算失败。
    """
    off = 0
    errs = []
    unverified = False

    def walk(fs, off):
        nonlocal unverified
        for i, f in enumerate(fs):
            nm = (f.get('name') or '') if isinstance(f, dict) else ''
            ty = ((f.get('type') or '') if isinstance(f, dict) else '').strip()
            t = ty.lower()
            if t.startswith('string'):
                if off + 2 > len(body):
                    return off, '%s: string 越界' % nm
                n = int.from_bytes(body[off:off + 2], 'big')
                off += 2 + n
            elif t.startswith('table') or f.get('items'):
                items = f.get('items')
                if off + 2 > len(body):
                    return off, '%s: table 计数越界' % nm
                cnt = int.from_bytes(body[off:off + 2], 'big')
                off += 2
                if cnt:
                    if not items:
                        unverified = True
                        return off, None          # 长度不可知，停止解析
                    for _ in range(cnt):
                        off, e = walk(items, off)
                        if e:
                            return off, '%s[]: %s' % (nm, e)
            elif t in SIZE:
                off += SIZE[t]
            elif '64' in t:
                off += 4
            elif '32' in t:
                off += 4
            elif '16' in t:
                off += 2
            else:
                off += 1
            if off > len(body):
                return off, '%s: 越界 (off=%d len=%d)' % (nm, off, len(body))
        return off, None

    off, e = walk(fields, 0)
    if e:
        errs.append(e)
    return off, errs, unverified


def _dim(body, off, fields):
    """★ R116：递归消耗 `fields` 描述的结构，返回 `(新 off, 错误串)`。

    与 `parse_strict` 同口径（string=2+len、table=2+按 items 递归、数值按位宽），
    但**支持非空表**。`parse_strict` 自身仍保持"空表只读计数"的历史行为，
    只在遇到非空表时调用本函数。
    """
    errs = ''
    for i, f in enumerate(fields):
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        ty = ((f.get('type') or '') if isinstance(f, dict) else '').strip()
        t = ty.lower()
        if t.startswith('string'):
            if off + 2 > len(body):
                return off, '%s: string 长度前缀越界' % nm
            n = int.from_bytes(body[off:off + 2], 'big')
            off += 2 + n
        elif t.startswith('table'):
            if off + 2 > len(body):
                return off, '%s: table 计数越界' % nm
            cnt = int.from_bytes(body[off:off + 2], 'big')
            off += 2
            items = (f.get('items') or []) if isinstance(f, dict) else []
            if cnt:
                if not items:
                    return off, '%s: 非空表但无 items 定义' % nm
                for _ in range(int(cnt)):
                    off, e2 = _dim(body, off, items)
                    if e2:
                        return off, e2
        elif t in SIZE:
            off += SIZE[t]
        elif '64' in t:
            off += 4
        elif '32' in t:
            off += 4
        elif '16' in t:
            off += 2
        elif '8' in t or 'bool' in t or 'char' in t:
            off += 1
        else:
            off += 1
        if off > len(body):
            return off, '%s: 越界 (off=%d len=%d)' % (nm, off, len(body))
    return off, ''


def parse_strict(body, fields):
    """按规格严格解析默认响应。返回 (offset, 错误列表)。空表只读计数。"""
    off = 0
    errs = []
    for i, f in enumerate(fields):
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        ty = ((f.get('type') or '') if isinstance(f, dict) else '').strip()
        t = ty.lower()
        if t.startswith('string'):
            need = 2
            if off + need > len(body):
                errs.append('%s: string 长度前缀越界' % nm)
                return off, errs
            n = int.from_bytes(body[off:off + 2], 'big')
            off += 2 + n
        elif t.startswith('table'):
            need = 2
            if off + need > len(body):
                errs.append('%s: table 计数越界' % nm)
                return off, errs
            cnt = int.from_bytes(body[off:off + 2], 'big')
            off += 2
            if cnt != 0:
                # ★★ R116：**支持非空表** —— 按 spec 的 `items` 递归跳过元素。
                #   旧实现只 append 一条"默认响应本应空表"就**不推进 off**，
                #   于是任何**有真实数据的专用实现**都会让后续字段全部错位，
                #   报出假的"越界"（R115 的 `15501` 就是这么被判 FAIL 的）。
                #   ⇒ 这不是迁就门禁，而是让门禁能解析**它自己 spec 里就有**的 `items`。
                items = (f.get('items') or []) if isinstance(f, dict) else []
                if items:
                    for _ in range(int(cnt)):
                        off, e2 = _dim(body, off, items)
                        if e2:
                            errs.append('%s[]: %s' % (nm, e2))
                            return off, errs
                else:
                    errs.append('%s: 非空表(cnt=%d)但 spec 无 items 定义 ⇒ 无法跳过'
                                % (nm, cnt))
        elif i == 0 and nm == 'code':
            off += 1
        elif t in SIZE:
            off += SIZE[t]
        elif '64' in t:
            off += 4
        elif '32' in t:
            off += 4
        elif '16' in t:
            off += 2
        elif '8' in t or 'bool' in t or 'char' in t:
            off += 1
        else:
            off += 1
        if off > len(body):
            errs.append('%s: 解析越界 (off=%d len=%d)' % (nm, off, len(body)))
            return off, errs
    return off, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--generic', action='store_true', help='只看 _GENERIC_DEFAULT_CMDS')
    ap.add_argument('--unsupported', action='store_true',
                    help='只看 _UNSUPPORTED_ACTION_CMDS（code=0 未开放应答）')
    ap.add_argument('--json')
    args = ap.parse_args()

    with open(FIELDS, encoding='utf-8') as f:
        fields = json.load(f)
    mock = load_mock()

    target = None
    _USET = set()
    _UMSG = ''
    builder = (lambda c: mock._build_default_sc(c))
    if args.generic:
        target = set(mock._GENERIC_DEFAULT_CMDS)
    if args.unsupported:
        s = set(getattr(mock, '_UNSUPPORTED_ACTION_CMDS', set()))
        _USET = s
        _UMSG = getattr(mock, '_UNSUPPORTED_MSG', '')
        target = s if target is None else (target | s)
        builder = (lambda c: mock._build_default_sc(c, code=0, msg=_UMSG)
                   if c in s else mock._build_default_sc(c))

    # cmd -> SC 字段
    sc = {}
    for k, v in fields.items():
        if v.get('dir') != 'sc':
            continue
        cmd = v.get('cmd')
        if not cmd:
            continue
        try:
            n = int(cmd)
        except ValueError:
            continue
        if target is not None and n not in target:
            continue
        sc.setdefault(n, (k, v.get('fields') or []))

    ok = bad = empty = 0
    rows = []
    unknown_types = {}
    for cmd in sorted(sc):
        key, fs = sc[cmd]
        body = builder(cmd)
        if not fs:
            empty += 1
            if body:
                rows.append((cmd, key, 'EMPTY-SPEC-BUT-BYTES', len(body), 0))
                bad += 1
            continue
        _ml = len(_UMSG.encode('utf-8')) if (target is not None and cmd in _USET) else 0
        exp, unk = default_len(fs, _ml)
        off, errs = parse_strict(body, fs)
        for nm, ty, why in unk:
            unknown_types.setdefault(ty, []).append('%s.%s(%s)' % (key, nm, why))
        problem = None
        if errs:
            problem = '; '.join(errs[:2])
        elif off != len(body):
            problem = '解析消耗 %d != 实际 %d' % (off, len(body))
        elif exp != len(body):
            problem = '期望 %d != 实际 %d' % (exp, len(body))
        if problem:
            bad += 1
            rows.append((cmd, key, problem, len(body), exp))
        else:
            ok += 1

    print('=== SC 默认应答一致性审计 ===')
    print('  审计命令数: %d%s' % (len(sc), '（_GENERIC_DEFAULT_CMDS）' if args.generic else '（全部 SC 规格）'))
    print('  一致 %d / 不一致 %d / 空规格 %d' % (ok, bad, empty))
    print()
    if rows:
        print('--- 不一致清单 ---')
        for cmd, key, pb, ln, exp in rows:
            print('  ✗ %-6d %-22s len=%-5d exp=%-5d %s' % (cmd, key, ln, exp, pb))
        print()
    if unknown_types:
        print('--- 落到宽度兜底的字段类型（挖掘缺口，共 %d 种）---'
              % len(unknown_types))
        for ty, uses in sorted(unknown_types.items(), key=lambda x: -len(x[1])):
            print('  %-40s x%d   例: %s' % (ty, len(uses), uses[0]))
        print()

    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump({'ok': ok, 'bad': bad, 'empty': empty,
                       'rows': rows,
                       'unknown_types': {k: v for k, v in unknown_types.items()}},
                      f, ensure_ascii=False, indent=1)
        print('已写出 %s' % args.json)

    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
