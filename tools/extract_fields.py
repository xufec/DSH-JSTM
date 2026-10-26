#!/usr/bin/env python3
"""Extract per-message field definitions from cmd_resolve_*.luac bytecode.

TWO encodings are used by the client:

  A) spec tables (most messages) -- a table constant whose entries look like
         'sex__C'            field sex of type C
         'args__T__name@s##value@s'   table field 'args' with sub-fields
     Type codes: C=uint8 c=int8 H=uint16 h=int16 I=uint32 i=int32
                 s=string f=float d=double b=bool T=table
     The builder prototype does:  cs.AutoConstruct(<spec table>)

  B) FMT templates (shared descriptors) -- string like 'CCsCD|Dsc10201member|'
     built through ReadFMT/WriteFMT.

Class -> builder association comes from the registration prototype:
     GGET <ClassName> ... FNEW <builder proto> TSETS C='__init'|'Decode'

Constant index convention (verified 100% over the corpus):
     compiler index i  ->  files position len(kgc)-1-i   (both D and C operands)

Outputs: protocol/manual.md, protocol/manual_login.md, protocol/fields.json
"""
import sys, os, re, json, zipfile, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst, ChildRef

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, 'protocol')

CLS = re.compile(r'^(CS|SC)([A-Za-z0-9_]*)_(\d+)$')
DSC = re.compile(r'^(Dsc|Dcs)(\d+)([A-Za-z0-9_]*)$')
FMT = re.compile(r'^[CHIFdsbL](?:[CHIFdsbL]|\|Dsc\w+\|)*$')
SPEC = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*__[A-Za-z]')
FIELD = re.compile(r'^[a-z][a-z0-9_]{1,30}$')
STOP = {'insert', 'table', 'pairs', 'ipairs', 'string', 'format', 'concat', 'sub',
        'len', 'remove', 'sort', 'print', 'type', 'tonumber', 'tostring',
        'readfmt', 'writefmt', 'encode', 'decode', 'value', 'key', 'self'}
TYPENAME = {'C': 'uint8', 'c': 'int8', 'H': 'uint16', 'h': 'int16',
            'I': 'uint32', 'i': 'int32', 's': 'string', 'f': 'float',
            'd': 'double', 'b': 'bool', 'T': 'table', 'L': 'list'}

OP_GGET, OP_FNEW, OP_TSETS, OP_GSET = 52, 49, 58, 53


def kidx(pt, i):
    pos = len(pt.kgc) - 1 - i
    return pt.kgc[pos] if 0 <= pos < len(pt.kgc) else None


def parse_spec(s):
    """'sex__C' / 'args__T__name@s##value@s' -> structured field."""
    name, _, rest = s.partition('__')
    if rest.startswith('T__'):
        items = []
        for part in rest[3:].split('##'):
            if '@' in part:
                fn, ft = part.rsplit('@', 1)
                items.append({'name': fn, 'type': TYPENAME.get(ft, ft)})
            elif part:
                items.append({'name': part, 'type': '?'})
        return {'name': name, 'type': 'table', 'items': items}
    return {'name': name, 'type': TYPENAME.get(rest, rest)}


def spec_fields(specs):
    return [parse_spec(s) for s in specs]


def fmt_types(fmt):
    out, i = [], 0
    while i < len(fmt):
        ch = fmt[i]
        if ch in 'DL' and i + 1 < len(fmt) and fmt[i + 1] == '|':
            j = fmt.index('|', i + 2)
            out.append(('list' if ch == 'L' else 'struct') + '<%s>' % fmt[i + 2:j])
            i = j + 1
        elif ch == '|':
            j = fmt.index('|', i + 1)
            out.append('struct<%s>' % fmt[i + 1:j])
            i = j + 1
        else:
            out.append(TYPENAME.get(ch, ch))
            i += 1
    return out


def scan_protos(r):
    """Per proto: class/descriptor names, fmt templates, spec tables, direction."""
    info = {}
    for pt in r.protos:
        fmts, specs, fields, classes, dscs = [], [], [], [], []
        direction = None
        for s in pt.strings:
            if CLS.match(s):
                classes.append(s)
            if DSC.match(s):
                dscs.append(s)
            if s in ('cs', 'sc'):
                direction = s
            if (('|' in s and 'Dsc' in s) or FMT.match(s)) and len(s) <= 90 \
                    and not CLS.match(s) and not DSC.match(s):
                fmts.append(s)
            if FIELD.match(s) and s.lower() not in STOP:
                fields.append(s)
        for t in pt.tables:
            vals = [x for x in t.array if isinstance(x, str)]
            vals += [x for k, x in t.hash if isinstance(x, str)]
            sp = [v for v in vals if SPEC.match(v)]
            if sp and len(sp) == len([v for v in vals if v]):
                specs.append(sp)
        info[pt.index] = {
            'fmt': sorted(set(fmts)), 'specs': specs, 'fields': fields,
            'classes': classes, 'descriptors': dscs, 'dir': direction,
        }
    return info


def registration_map(reg):
    """class/descriptor name -> {key: builder proto index}."""
    mapping = collections.defaultdict(dict)
    last = None
    for i, ins in enumerate(reg.bc):
        op = ins & 0xff
        if op in (OP_GGET, OP_GSET):
            v = kidx(reg, (ins >> 16) & 0xffff)
            if isinstance(v, str):
                last = v
        elif op == OP_FNEW:
            v = kidx(reg, (ins >> 16) & 0xffff)
            if not isinstance(v, ChildRef):
                continue
            for j in range(i + 1, min(i + 5, len(reg.bc))):
                ins2 = reg.bc[j]
                op2 = ins2 & 0xff
                if op2 == OP_TSETS:
                    key = kidx(reg, (ins2 >> 16) & 0xff)
                    if key in ('__init', 'Decode', 'Encode') and last:
                        mapping[last][key] = v.index
                    break
                if op2 in (OP_FNEW, OP_GGET, OP_GSET):
                    break
    return mapping


def analyze(apk):
    z = zipfile.ZipFile(apk)
    members = sorted(n for n in z.namelist()
                     if n.startswith('assets/src/config/protocal/') and n.endswith('.luac'))
    entries = {}
    for m in members:
        try:
            r = Reader(z.read(m))
            r.parse()
        except Exception:
            continue
        name = m.rsplit('/', 1)[-1]
        pinfo = scan_protos(r)
        reg = None
        best = 0
        for pt in r.protos:
            n = sum(1 for s in pt.strings if CLS.match(s))
            if n > best:
                best, reg = n, pt
        regmap = registration_map(reg) if reg is not None else {}
        entries[name] = {'protos': pinfo, 'regmap': regmap}
    return entries


def build(entries):
    """-> {class_or_descriptor: {'cmd','dir','fields':[...],'source':...}}"""
    out = {}
    for fname, e in entries.items():
        pinfo = e['protos']
        for cname, keys in e['regmap'].items():
            merged = None
            source = None
            direction = None
            for key in ('__init', 'Decode', 'Encode'):
                pidx = keys.get(key)
                if pidx is None or pidx not in pinfo:
                    continue
                pi = pinfo[pidx]
                if direction is None and pi['dir']:
                    direction = pi['dir']
                if pi['specs'] and merged is None:
                    merged = spec_fields(pi['specs'][0])
                    source = 'spec'
                if pi['fmt'] and merged is None:
                    merged = [{'name': n, 'type': t} for n, t in
                              zip(pi['fields'], fmt_types(sorted(pi['fmt'], key=len, reverse=True)[0]))]
                    source = 'fmt'
                    if not merged:
                        merged = None
            cmd = None
            m = CLS.match(cname) or DSC.match(cname)
            if m:
                cmd = m.groups()[-1]
            out[cname] = {'file': fname, 'cmd': cmd,
                          'dir': direction,
                          'fields': merged or [],
                          'source': source or ('spec' if merged else None)}
    return out


def render(msgs, cmds, title, path):
    L = ['# %s\n' % title,
         '> 类型：uint8/int8/uint16/int16/uint32/int32/string/float/double/bool/table。'
         '`CS*` = 客户端→服务端，`SC*` = 服务端→客户端。\n']
    for cmd in cmds:
        rows = [(k, v) for k, v in sorted(msgs.items()) if v['cmd'] == cmd]
        if not rows:
            continue
        L.append('## 命令 %s\n' % cmd)
        for cname, v in rows:
            if not v['fields']:
                L.append('- `%s` — 无字段（空消息）' % cname)
                continue
            L.append('- `%s`（%s）' % (cname, v['dir'] or '?'))
            L.append('')
            L.append('  | 字段 | 类型 |')
            L.append('  |---|---|---|')
            for f in v['fields']:
                if f['type'] == 'table' and 'items' in f:
                    sub = ', '.join('%s:%s' % (i['name'], i['type']) for i in f['items'])
                    L.append('  | %s | table(%s) |' % (f['name'], sub))
                else:
                    L.append('  | %s | %s |' % (f['name'], f['type']))
            L.append('')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    os.makedirs(OUTDIR, exist_ok=True)
    entries = analyze(apk)
    msgs = build(entries)
    with_fields = [k for k, v in msgs.items() if v['fields']]
    cs = [k for k in msgs if k.startswith('CS')]
    sc = [k for k in msgs if k.startswith('SC')]
    print('消息条目=%d  有字段=%d  (CS=%d SC=%d 描述符=%d)'
          % (len(msgs), len(with_fields), len(cs), len(sc),
             sum(1 for k in msgs if k.startswith(('Dsc', 'Dcs')))))
    with open(os.path.join(OUTDIR, 'fields.json'), 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=1)
    all_cmds = sorted({v['cmd'] for v in msgs.values() if v['cmd']}, key=lambda x: (len(x), x))
    render(msgs, all_cmds, '《绝世唐门》协议手册（自动提取）',
           os.path.join(OUTDIR, 'manual.md'))
    chain = ['10001', '10101', '10102', '10103', '10110', '10111',
             '10200', '10201', '10202', '10204', '10300', '10301']
    render(msgs, chain, '《绝世唐门》协议手册 · 登录链路',
           os.path.join(OUTDIR, 'manual_login.md'))
    print('written: protocol/manual.md, protocol/manual_login.md, protocol/fields.json')


if __name__ == '__main__':
    main()