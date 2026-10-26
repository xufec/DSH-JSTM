#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3-①-c：对三版本复用仓库既有后处理（`resolve_dsc_refs.py`），拿到**与基线同口径**的字段表。

## 为什么要这一步
自证发现：原始提取结果与仓库 `protocol/fields.json` 有 **450 处字段不一致**。
读 `tools/resolve_dsc_refs.py` 头注后确认原因 —— 基线 = **原始提取 + 后处理**：
  1. 472 个 `Dsc*` 条目**字段顺序被反转**（原始提取的已知缺陷）⇒ 类型随之错位；
  2. 顶层规格里约 180 处 `D|DscXXXXfield|` 引用**保持未展开**；
  3. 后处理用 **reader 原型（TSETS 顺序 = 线序，不反转）** 覆盖，并展开 `D|X|` 引用。

⇒ 直接拿"原始提取"做跨版本比较虽然**三版本同口径**、结论相对可信，
   但与基线不同口径会让阅读者误判。本脚本 monkey-patch `FIELDS` 后对三版本各跑一次后处理，
   产出**同口径**数据，再做差异。

⚠ 全程**不写** `protocol/fields.json`（只用 `--out` 指到 R1 目录）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PV = os.path.join(ROOT, 'analysis', 'r1_client_index', '_per_version')


def main():
    import resolve_dsc_refs as R
    print('resolve_dsc_refs 默认输入: %s' % getattr(R, 'FIELDS', '?'))
    for ver in ('1.3.0', '1.4.9', '1.4.11'):
        src = os.path.join(PV, 'fields_%s.json' % ver)
        dst = os.path.join(PV, 'fields_%s.post.json' % ver)
        if not os.path.exists(src):
            print('  !! 缺 %s' % src)
            continue
        # ★ monkey-patch：把输入指到本版本；只用 --out，绝不 --apply
        R.FIELDS = src
        sys.argv = ['resolve_dsc_refs.py', '--out', dst, '--limit-report', '0']
        print('--- 后处理 %s' % ver)
        try:
            R.main()
        except SystemExit:
            pass
        except Exception as e:
            print('  !! 失败: %r' % (e,))
        if os.path.exists(dst):
            print('    -> %s (%d B)' % (os.path.basename(dst), os.path.getsize(dst)))
    print('\n完成。protocol/fields.json 未被改动（本脚本只用 --out）。')


if __name__ == '__main__':
    main()
