# -*- coding: utf-8 -*-
"""mock_server.py 结构审计 + 安全去重。

背景（2026-10-17 梳理发现）：
  mock_server.py 顶部已经 `from <模块> import ...` 把搬家后的实现接进来（注释写明
  "re-import 已搬家实现（供残留调用点）"），但**文件后半又用同名 `def` 重定义了一遍**
  ⇒ 模块里的实现被遮蔽，旧 if 链跑的是本地副本。后果：
    · 在模块里做的修复（如账号/角色按 srv_id 过滤）对旧链**不生效**；
    · 两套实现持续分叉（27 个已经不同）。

本工具做两件事：
  1. 审计：列出「被遮蔽的导入名」，并分成
       SAFE      —— AST 完全等价（差异只有注释/格式）或本地副本 0 处调用（死代码）
       DIVERGENT —— 行为不同且仍在使用（**不在本工具里自动改**，只登记）
       BAD_IMPORT—— 导入的名字在目标模块里不存在
  2. `--apply`：把 SAFE 的本地副本从 mock_server.py 删掉（**先备份**），
     删完后 `mock_server.<name>` 就是搬家后的模块实现（单一事实来源）。

用法（仓库根目录）：
    python tools/audit_mock_server.py            # 只报告；若有新的遮蔽则退出码 1
    python tools/audit_mock_server.py --apply    # 备份 + 删除 SAFE 的本地副本
"""
import argparse
import ast
import importlib
import inspect
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'server')
TARGET = os.path.join(SERVER, 'mock_server.py')
sys.path.insert(0, SERVER)

# 已知分叉（行为不同且仍在使用）——**允许存在**，但新增的遮蔽会让门禁失败。
# 处理方式：逐个对比后决定"以模块为准"还是"以本地为准"，再改名/合并；本次不动。
KNOWN_DIVERGENT = set()

# 「模块更新」类分叉：模块里的实现是本轮/后续修复后的**正确版本**，本地副本是旧版
# ⇒ 直接删本地副本，让 mock_server 也用模块实现（行为与 dispatch handler 一致）。
# 每个都注明了判定依据（2026-10-17 逐个人工比对 ast.unparse 纯代码差异）。
MODULE_WINS = {
    '_sc_to_db_updates': '模块版带 srv_id（本地是加 srv_id 之前的旧版）',
    'role_state': '模块版带 R100 的 practice_exp 回填（本地缺）',
    'add_role_exp': '模块版把 role_state/db_save_role/db_set_assets 做成函数内 lazy import'
                    '（level.service 里必须这样才不循环依赖）；本地靠 mock_server 顶层导入',
    'apply_level_attr_growth': '同上：模块版有函数内 lazy import，本地没有',
    'build_10303': '模块版多算 role_power（本地缺 power 字段）',
    'db_bag_add': '模块版 lazy import is_valid_item + 别名 _time（inventory.service 自足）；本地靠顶层导入',
    'build_bag_items': '模块版用 it.get(intensify_lev,0)；本地把强化等级硬编码成 30 并塞了 D2 过滤',
}


def _strip_docstrings(node):
    """递归去掉 docstring（纯注释/docstring 的差异不算行为差异）。"""
    for n in ast.walk(node):
        body = getattr(n, 'body', None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, (ast.Constant, ast.Str)):
            if isinstance(getattr(first.value, 'value', None), str):
                n.body = body[1:] or [ast.Pass()]
    return node


def _defkey(node, keep_doc=False):
    """把 def/class 规范化后再 dump：去掉名字、装饰器、返回注解（只看行为）。"""
    node = _strip_docstrings(node)
    if isinstance(node, ast.FunctionDef):
        node = ast.FunctionDef(name='f', args=node.args, body=node.body,
                               decorator_list=[], returns=None,
                               type_comment=None, type_params=[])
    elif isinstance(node, ast.ClassDef):
        node = ast.ClassDef(name='C', bases=node.bases, keywords=node.keywords,
                            body=node.body, decorator_list=[], type_params=[])
    return ast.dump(node, annotate_fields=False)


def analyze(src):
    tree = ast.parse(src)

    local = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            local[node.name] = node

    imported = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module and node.col_offset == 0:
            for a in node.names:
                imported[a.asname or a.name] = (node.module, a.name)

    # 每个名字在文件里的**活**引用次数（AST 不看注释/字符串）
    uses = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            uses[node.id] = uses.get(node.id, 0) + 1

    safe, divergent, bad_import = [], [], []
    for alias, (mod, orig) in imported.items():
        if alias not in local:
            continue
        ln = local[alias].lineno
        try:
            m = importlib.import_module(mod)
            fn = getattr(m, orig)
            msrc = inspect.getsource(fn)
            mt = ast.parse(msrc.lstrip()).body[0]
            same = _defkey(mt) == _defkey(local[alias])
        except AttributeError:
            bad_import.append((alias, mod, orig, ln))
            continue
        except Exception as e:                       # 其它导入问题也报出来
            bad_import.append((alias, mod, '%r' % (e,), ln))
            continue
        n_use = uses.get(alias, 0)
        if same:
            safe.append((alias, mod, ln, n_use, 'AST 等价'))
        elif n_use == 0:
            safe.append((alias, mod, ln, n_use, '本地副本 0 处调用（死代码）'))
        else:
            divergent.append((alias, mod, ln, n_use))
    return tree, local, imported, safe, divergent, bad_import


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='备份并删除 SAFE 的本地副本')
    args = ap.parse_args()

    src = open(TARGET, encoding='utf-8').read()
    lines = src.splitlines(keepends=True)
    tree, local, imported, safe, divergent, bad_import = analyze(src)

    print('== mock_server.py 结构审计 ==')
    print('  顶层 def/class: %d ｜ 被遮蔽的导入名: %d' % (len(local), len(safe) + len(divergent)))

    print('\n-- SAFE（可安全删除本地副本）: %d --' % len(safe))
    for alias, mod, ln, n_use, why in sorted(safe, key=lambda x: x[2]):
        print('  %-24s <- %-22s L%-6d uses=%-5d %s' % (alias, mod, ln, n_use, why))

    print('\n-- DIVERGENT（行为不同且仍在使用）: %d --' % len(divergent))
    for alias, mod, ln, n_use in sorted(divergent, key=lambda x: -x[3]):
        if alias in MODULE_WINS:
            flag = '   [模块更新 ⇒ 删本地] ' + MODULE_WINS[alias]
        elif alias in KNOWN_DIVERGENT:
            flag = ''
        else:
            flag = '   ←★ 新出现的分叉（请登记/处理）'
        print('  %-24s <- %-22s L%-6d uses=%-5d%s' % (alias, mod, ln, n_use, flag))

    if bad_import:
        print('\n-- BAD_IMPORT（导入名在目标模块不存在）--')
        for alias, mod, orig, ln in bad_import:
            print('  %-24s from %s import %s (L%d)' % (alias, mod, orig, ln))

    new_divergence = [d for d in divergent
                      if d[0] not in KNOWN_DIVERGENT and d[0] not in MODULE_WINS]
    # --apply 时：SAFE + MODULE_WINS 里的本地副本都删掉
    to_delete = list(safe) + [d for d in divergent if d[0] in MODULE_WINS]

    if not args.apply:
        print('\n结论:', 'PASS（无新增遮蔽）' if not new_divergence else
              'FAIL（新增 %d 处遮蔽）' % len(new_divergence))
        return 1 if new_divergence else 0

    if not to_delete:
        print('\n没有需要删除的项。')
        return 0

    bak = TARGET + '.bak_audit_' + time.strftime('%Y%m%d_%H%M%S')
    shutil.copy2(TARGET, bak)
    print('\n备份 -> %s' % bak)

    drop = sorted(((local[d[0]].lineno, local[d[0]].end_lineno) for d in to_delete), reverse=True)
    for start, end in drop:
        del lines[start - 1:end]
    open(TARGET, 'w', encoding='utf-8', newline='').write(''.join(lines))
    print('已删除 %d 个本地副本（行号自下往上删，避免错位）' % len(drop))

    # 语法门禁
    import py_compile
    try:
        py_compile.compile(TARGET, doraise=True)
        print('py_compile: OK')
    except Exception as e:
        print('py_compile FAILED:', e)
        shutil.copy2(bak, TARGET)
        print('已回滚')
        return 1

    # 复跑确认：SAFE 应为 0
    src2 = open(TARGET, encoding='utf-8').read()
    _, _, _, safe2, divergent2, bad2 = analyze(src2)
    print('复检: SAFE=%d DIVERGENT=%d BAD_IMPORT=%d' % (len(safe2), len(divergent2), len(bad2)))
    return 0 if not safe2 else 1


if __name__ == '__main__':
    sys.exit(main())
