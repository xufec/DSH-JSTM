#!/usr/bin/env python3
"""Extract the protocol dictionary from the client's bytecode.

Sources (inside assets/src/):
  config/protocal/all_proto.luac          -> {cmd_id: chinese description}
  config/protocal/cmd_resolve_*.luac      -> per-command resolve/structure classes
  sys/protocalrulesmgr.luac               -> message class registry (CS*/SC*)

Outputs (UTF-8):
  protocol/cmd_table.json      {cmd_id: description}
  protocol/cmd_classes.json    {file: [class names]}
  protocol/proto_summary.md    human readable overview
"""
import sys, os, json, re, zipfile, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import Reader, TableConst, ChildRef

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'protocol')

CLASS_RE = re.compile(r'^(CS|SC)[A-Za-z0-9_]*_\d+$')


def walk_tables(v, out_hash, depth=0):
    """Collect number->string pairs from possibly nested tables."""
    if depth > 6:
        return
    if isinstance(v, TableConst):
        for k, val in v.hash:
            if isinstance(k, (int, float)) and isinstance(val, str):
                out_hash[int(k)] = val
            else:
                walk_tables(val, out_hash, depth + 1)
            walk_tables(k, out_hash, depth + 1)
        for x in v.array:
            walk_tables(x, out_hash, depth + 1)


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    os.makedirs(OUTDIR, exist_ok=True)
    z = zipfile.ZipFile(apk)

    # ---------- 1. command table from all_proto.luac ----------
    cmd_table = {}
    data = z.read('assets/src/config/protocal/all_proto.luac')
    r = Reader(data)
    r.parse()
    n_tables = 0
    for pt in r.protos:
        for t in pt.tables:
            n_tables += 1
            walk_tables(t, cmd_table)
    print('all_proto.luac: protos=%d tables=%d cmd entries=%d'
          % (len(r.protos), n_tables, len(cmd_table)))

    # ---------- 2. class names per cmd_resolve file ----------
    names = sorted(n for n in z.namelist()
                   if n.startswith('assets/src/config/protocal/') and n.endswith('.luac'))
    cmd_classes = {}
    all_classes = set()
    for n in names:
        try:
            rr = Reader(z.read(n))
            rr.parse()
        except Exception as e:
            print('  !! parse fail', n, e)
            continue
        cs = set()
        for pt in rr.protos:
            for s in pt.strings:
                if CLASS_RE.match(s):
                    cs.add(s)
        if cs:
            cmd_classes[n.rsplit('/', 1)[-1]] = sorted(cs)
            all_classes |= cs
    print('cmd_resolve files: %d, distinct CS/SC classes: %d' % (len(names), len(all_classes)))

    # ---------- 3. registry file ----------
    reg = z.read('assets/src/sys/protocalrulesmgr.luac')
    rr = Reader(reg)
    rr.parse()
    reg_strings = set()
    for pt in rr.protos:
        for s in pt.strings:
            if CLASS_RE.match(s):
                reg_strings.add(s)
    print('protocalrulesmgr.luac: registered classes=%d' % len(reg_strings))

    # ---------- write outputs ----------
    with open(os.path.join(OUTDIR, 'cmd_table.json'), 'w', encoding='utf-8') as f:
        json.dump({str(k): v for k, v in sorted(cmd_table.items())}, f,
                  ensure_ascii=False, indent=1)
    with open(os.path.join(OUTDIR, 'cmd_classes.json'), 'w', encoding='utf-8') as f:
        json.dump(cmd_classes, f, ensure_ascii=False, indent=1)
    with open(os.path.join(OUTDIR, 'registry_classes.json'), 'w', encoding='utf-8') as f:
        json.dump(sorted(reg_strings), f, ensure_ascii=False, indent=1)

    # module grouping: first digits identify subsystem
    groups = collections.Counter()
    for c in all_classes:
        m = re.search(r'_(\d+)', c)
        if m:
            groups[str(m.group(1))[:3]] += 1

    lines = []
    lines.append('# 《绝世唐门》协议字典（自动提取）\n')
    lines.append('- 命令号条目：%d' % len(cmd_table))
    lines.append('- 消息类（CS/SC）：%d（分布于 %d 个 cmd_resolve 文件）'
                 % (len(all_classes), len(cmd_classes)))
    lines.append('- 注册表 protocalrulesmgr 中出现的消息类：%d\n' % len(reg_strings))
    lines.append('## 命令号段分布（前三位）\n')
    lines.append('| 段 | 消息数 | 含义线索 |')
    lines.append('|---|---|---|')
    hints = {
        '100': '连接/登录/角色', '101': '角色创建/登录', '102': '地图/场景/移动',
        '103': '角色属性/初始化', '104': '英雄/技能点', '105': '背包/道具/装备',
        '106': '战斗/技能', '107': '庄园/城邦/资源', '108': '邮件', '109': '活动/BUFF',
        '110': '攻城/新服', '111': '广播', '112': '聊天/交易', '113': '玩法', '114': '战队',
        '115': '签到/激活', '116': '限时活动', '117': '转盘/抽奖', '118': '矿区路线',
        '120': '副本', '121': '验证', '122': '探宝', '124': '活动抽奖', '126': '魔盒',
        '127': '消息/私聊', '128': '商店', '129': '排行榜', '130': '副本/赛季',
    }
    for seg, cnt in sorted(groups.items()):
        lines.append('| %sxx | %d | %s |' % (seg, cnt, hints.get(seg, '')))
    lines.append('\n## 命令号 → 说明（前 80 条）\n')
    lines.append('| cmd | 说明 |')
    lines.append('|---|---|')
    for k in sorted(cmd_table)[:80]:
        lines.append('| %d | %s |' % (k, cmd_table[k].replace('|', '/')))
    with open(os.path.join(OUTDIR, 'proto_summary.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print('written:', OUTDIR)


if __name__ == '__main__':
    main()