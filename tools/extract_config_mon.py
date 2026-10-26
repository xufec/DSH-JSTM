"""提取 1.4.9 `config_mon_data.luac` 的 Config.Mon：怪物 bid -> 定义。

字节码形态（反汇编 config_mon_data.luac proto#0）：

    function Config.Mon.get(bid)                      -- 巨型 if 链
      if bid == <knum 常量> then
         return <23 元素数组>                          -- [1]=name, [8]=res_id, ...
      end
      ...

常量索引映射（与 tools/luajit_dis.kidx 一致，已被 check_const_mapping.py 验证）：
    d          -> kgc[len(kgc)-1-d]   （值表）
    d          -> knum[len(knum)-1-d] （bid）

⚠ 注意：**不能**用 `pt.tables` 的过滤顺序去对齐，因为 kidx 是"倒序"的；
   必须逐 d 用 kidx 取表，才能保证 bid 与值表配对正确。

输出 analysis/1.4.9/task/config_mon.json  { "<bid>": {name, res_id, fields:[...]} }
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from luajit_bc import TableConst, parse_file  # noqa: E402
from luajit_dis import kidx  # noqa: E402


def main():
    path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else r'analysis\1.4.9\task\config_mon.json'
    r = parse_file(path)
    pt = r.protos[0]
    n = len(pt.knum)
    mon = {}
    for d in range(n):
        bid = pt.knum[n - 1 - d]
        t = kidx(pt, d)
        if not isinstance(t, TableConst):
            continue
        a = t.array or []
        if len(a) < 9 or not isinstance(a[1], str):
            continue
        try:
            bid = int(bid)
        except Exception:
            continue
        mon[str(bid)] = {
            'bid': bid,
            'name': a[1],
            'res_id': a[8] if isinstance(a[8], str) else '',
            'fields': [x for x in a],
        }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(mon, open(out, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=1, sort_keys=True)
    print('Config.Mon 条目: %d -> %s' % (len(mon), out))
    for probe in ('20001', '20002', '20022', '20040', '20003'):
        e = mon.get(probe)
        print('  mon %-7s %s' % (probe, ('name=%r res_id=%r' % (e['name'], e['res_id']))
                                 if e else '【不在 Config.Mon】'))


if __name__ == '__main__':
    main()
