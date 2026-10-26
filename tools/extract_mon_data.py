"""从 1.4.9 的 config_mon_data.luac 提取 Config.MonData 全表 → JSON。

依据（全部来自字节码，不是猜的）：
1) `proto[1]` 是 `Config.MonData` 的 `__index` 元方法，其 `TGETB`→`TSETS 字段名`
   序列**给出了每个字段在数据数组里的下标**：
       d[1]=name  d[2]=lev  d[3]=type  d[4]=type2  d[5]=career
       d[6]=special_type  d[7]=hp_num  d[8]=res_id  d[9]=born  d[10]=leave
       d[11]=sound  d[12]=enter_map_effect  d[13]=width  d[14]=height
       d[15]=anime_die  d[16]=die_effect  d[17]=mon_list  d[18]=formation_type
       d[19]=filter_id  d[20]=halo_id  d[21]=model_size  d[22]=desc  d[23]=dir
2) `proto[0]` 是数据本体（58,359 条字节码、**0 个字符串**）⇒ 条目是**位置数组**。

⇒ **只有这些字段可校准**；`atk` / `def` / `exp` / `coin` **不在此表**（已确证）。

用法：python tools/extract_mon_data.py [apk] [out.json]
"""
import json
import sys
import zipfile

sys.path.insert(0, 'tools')
from luajit_bc import parse_bytes
from luajit_dis import OPS, kidx

# d[n] -> 字段名（自上而下的 __index 顺序，见文件头）
FIELDS = ['name', 'lev', 'type', 'type2', 'career', 'special_type', 'hp_num',
          'res_id', 'born', 'leave', 'sound', 'enter_map_effect', 'width',
          'height', 'anime_die', 'die_effect', 'mon_list', 'formation_type',
          'filter_id', 'halo_id', 'model_size', 'desc', 'dir']


def extract(apk_path):
    z = zipfile.ZipFile(apk_path)
    r = parse_bytes(z.read('assets/src/config/config_mon_data.luac'))
    pt = r.protos[0]

    rows = {}
    key = None
    pending = None      # 最近一个 TDUP 的表（可能是数据行）

    for i, w in enumerate(pt.bc):
        op = OPS[w & 0xff]
        d = (w >> 16) & 0xffff

        if op == 'TDUP':
            c = kidx(pt, d)
            arr = [x for x in (getattr(c, 'array', []) or []) if x is not None]
            if len(arr) >= 2:
                pending = arr
        elif op == 'KSHORT':
            key = d
        elif op == 'KNUM':
            try:
                key = pt.knum[d]
            except Exception:
                key = None
        elif op == 'TSETV':
            if key is not None and pending:
                try:
                    k = int(key)
                except Exception:
                    pending = None
                    key = None
                    continue
                rows[k] = pending
            pending = None
            key = None
        elif op in ('TSETB', 'TSETB_'):
            pending = None

    return rows


def main():
    apk = sys.argv[1] if len(sys.argv) > 1 else r'anzbao\jstm.apk'
    out = sys.argv[2] if len(sys.argv) > 2 else r'server\mon_config.json'
    rows = extract(apk)
    print('提取怪物数:', len(rows))
    out_map = {}
    for bid, arr in rows.items():
        rec = {'bid': bid}
        for i, nm in enumerate(FIELDS):
            rec[nm] = arr[i] if i < len(arr) else None
        out_map[str(bid)] = rec
    # 抽查
    for b in ('20001', '20002', '20022', '20040'):
        if b in out_map:
            r = out_map[b]
            print('   %-7s name=%-10s lev=%-4s hp_num=%-8s res_id=%s'
                  % (b, str(r.get('name'))[:10], r.get('lev'),
                     r.get('hp_num'), r.get('res_id')))
    json.dump(out_map, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('已写出', out)


if __name__ == '__main__':
    main()
