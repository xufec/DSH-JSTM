# -*- coding: utf-8 -*-
"""把 mock_server.py 里"本地副本更新"的函数**回灌**进它对应模块，然后删掉本地副本。

为什么需要它（2026-10-17 梳理）：
  拆模块时只做了一半 —— 顶部 import 了模块实现，文件后半又 def 了一遍；
  之后有些修复**只打在 mock_server 的本地副本上**（Phase 4C/R49/Phase E 等），
  于是 dispatch handler（用模块实现）与旧 if 链兜底（用本地副本）**行为不一致**。
  收敛办法：把本地（更新）的源码搬回模块 → 删本地副本 → 两边同源。

用法（仓库根目录）：
    python tools/converge_shadowed.py --list role_state build_10301     # 看差异 + 依赖检查
    python tools/converge_shadowed.py --apply role_state build_10301    # 回灌 + 删副本 + 编译检查

安全措施：
  · 回灌前检查目标模块的 **自由变量**（函数用到的全局名）是否都在模块里可解析；
    缺依赖会直接拒绝（打印缺哪些，不写文件）。
  · 写之前两处都备份（*.bak_converge_<ts>）。
  · 两次 py_compile；失败自动回滚。
"""
import argparse
import ast
import difflib
import importlib
import inspect
import os
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.join(ROOT, 'server')
MOCK = os.path.join(SERVER, 'mock_server.py')
sys.path.insert(0, SERVER)

# 名字 -> 目标模块（与 mock_server 顶部 import 一致）
TARGETS = {
    # role
    'role_state': 'role.storage', 'build_10301': 'role.storage',
    'build_10302': 'role.storage', 'build_10303': 'role.storage',
    '_sc_to_db_updates': 'role.storage',
    # level
    'level_row': 'level.service', 'level_need': 'level.service',
    'level_next_total': 'level.service', 'level_attr_point': 'level.service',
    'add_role_exp': 'level.service', 'apply_level_attr_growth': 'level.service',
    # attribute
    'role_attr_dict': 'attribute.service', 'role_power': 'attribute.service',
    'attr_table_10306': 'attribute.service',
    # item
    'item_cfg': 'item.service', 'item_ids': 'item.service', 'is_valid_item': 'item.service',
    # inventory
    'db_bag_add': 'inventory.service', 'db_init_equip': 'inventory.service',
    'db_store_init': 'inventory.service', 'build_bag_items': 'inventory.service',
    'build_equip_items': 'inventory.service',
    # task
    'build_mission_entry': 'task.service',
    # power（别名导入：from power.service import power_of as role_power_of）
    'role_power_of': 'power.service',
}


def _mod_path(mod):
    m = importlib.import_module(mod)
    return os.path.abspath(inspect.getfile(m))


def _seg(src, node):
    return ast.get_source_segment(src, node)


def _find(tree, name):
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _free_globals(fn_node):
    """函数用到的**全局名**（未被参数/局部/内建消化掉的 Name 读取）。"""
    local = set()
    a = fn_node.args
    for arg in (a.posonlyargs + a.args + a.kwonlyargs):
        local.add(arg.arg)
    for extra in (a.vararg, a.kwarg):
        if extra:
            local.add(extra.arg)
    imports = []
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            local.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node is not fn_node:
            local.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            imports.extend(x.asname or x.name for x in node.names)
        elif isinstance(node, ast.alias):
            imports.append(node.asname or node.name.split('.')[0])
        elif isinstance(node, ast.ExceptHandler) and node.name:
            local.add(node.name)
        elif isinstance(node, ast.comprehension):
            pass
    used = set()
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            used.add(node.id)
    import builtins
    return {n for n in used - local if not hasattr(builtins, n)}


def check_deps(mod, fn_node):
    """目标模块里能否解析这些全局名。返回缺失列表。"""
    m = importlib.import_module(mod)
    missing = []
    for g in sorted(_free_globals(fn_node)):
        if not hasattr(m, g):
            missing.append(g)
    return missing


def do_list(names):
    src = open(MOCK, encoding='utf-8').read()
    tree = ast.parse(src)
    for name in names:
        mod = TARGETS[name]
        ln = _find(tree, name)
        if ln is None:
            print('!! %s 在 mock_server 里找不到' % name)
            continue
        m = importlib.import_module(mod)
        msrc = inspect.getsource(getattr(m, name))
        lsrc = _seg(src, ln)
        miss = check_deps(mod, ln)
        d = list(difflib.unified_diff(msrc.splitlines(), lsrc.splitlines(),
                                      '模块:' + mod, '本地:mock_server@%d' % ln.lineno,
                                      lineterm='', n=0))
        print('\n===== %s  (%s)  差异块=%d  缺失依赖=%s =====' % (name, mod, len(d), miss or '无'))
        for line in d[:24]:
            print(line)


def do_apply(names):
    src = open(MOCK, encoding='utf-8').read()
    tree = ast.parse(src)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    changed = []
    for name in names:
        mod = TARGETS[name]
        lnode = _find(tree, name)
        if lnode is None:
            print('!! %s 找不到，跳过' % name)
            continue
        if lnode.decorator_list:
            print('!! %s 带装饰器，拒绝自动搬（需人工）' % name)
            continue
        miss = check_deps(mod, lnode)
        if miss:
            print('!! %s 缺依赖 %s，拒绝回灌（先补 import 再跑）' % (name, miss))
            continue
        lsrc = _seg(src, lnode)
        mpath = _mod_path(mod)
        msrc_txt = open(mpath, encoding='utf-8').read()
        mtree = ast.parse(msrc_txt)
        mnode = _find(mtree, name)
        if mnode is None:
            print('!! 模块 %s 里没有 %s，跳过' % (mod, name))
            continue
        if mnode.decorator_list:
            print('!! 模块里的 %s 带装饰器，拒绝自动改' % name)
            continue
        mlines = msrc_txt.splitlines(keepends=True)
        new_msrc = (''.join(mlines[:mnode.lineno - 1]) + lsrc.rstrip() + '\n\n'
                    + ''.join(mlines[mnode.end_lineno:]))
        shutil.copy2(mpath, mpath + '.bak_converge_' + stamp)
        open(mpath, 'w', encoding='utf-8', newline='').write(new_msrc)
        changed.append((name, mod, lnode.lineno, lnode.end_lineno))
        print('  回灌 %s -> %s（本地 L%d-%d 已搬走）' % (name, mod, lnode.lineno, lnode.end_lineno))

    if not changed:
        print('没有可回灌的项。')
        return 0

    # 从 mock_server 删本地副本（自下往上）
    shutil.copy2(MOCK, MOCK + '.bak_converge_' + stamp)
    lines = src.splitlines(keepends=True)
    for name, mod, start, end in sorted(changed, key=lambda x: -x[2]):
        del lines[start - 1:end]
    open(MOCK, 'w', encoding='utf-8', newline='').write(''.join(lines))
    print('已删除 mock_server 中的 %d 个本地副本' % len(changed))

    import py_compile
    ok = True
    for p in [MOCK] + [_mod_path(m) for _, m, _, _ in changed]:
        try:
            py_compile.compile(p, doraise=True)
        except Exception as e:
            print('py_compile 失败 %s: %s' % (p, e))
            ok = False
    if not ok:
        shutil.copy2(MOCK + '.bak_converge_' + stamp, MOCK)
        print('已回滚 mock_server；模块文件请按 *.bak_converge_%s 手工回滚' % stamp)
        return 1
    print('py_compile: OK')
    print('备份后缀: .bak_converge_%s' % stamp)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', nargs='*', metavar='NAME')
    ap.add_argument('--apply', nargs='*', metavar='NAME')
    a = ap.parse_args()
    if a.list is not None:
        return do_list(a.list or sorted(TARGETS))
    if a.apply:
        return do_apply(a.apply)
    ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
