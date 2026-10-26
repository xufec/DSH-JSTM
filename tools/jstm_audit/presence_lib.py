#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE C0 — JSTM 三版本存在性判定共享库（只读）。

供 tools/jstm_audit/ 下其它脚本（audit_consistency.py / gen_*.py）import 复用。
所有判定只读取 analysis/jstm_client_audit/_raw/apk_scan_<ver>.json（由 scan_apk.py
产出），不触碰 APK 本体，不写任何文件。

版本参数两种写法均可："1.4.11" 或 "1_4_11"。

典型用法:
    import presence_lib as pl
    ok, ev = pl.module_present("1.4.11", "denglu_ctrl.luac")
    files  = pl.ui_module_files("1.4.11", "achieve")
"""
import io
import json
import os
import re

# tools/jstm_audit/presence_lib.py -> 上三级即仓库根 DSH/
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(ROOT, "analysis", "jstm_client_audit", "_raw")

VERSIONS = ("1.3.0", "1.4.9", "1.4.11")

_SCAN_CACHE = {}


def _norm_ver(version):
    """"1.4.11" / "1_4_11" -> "1.4.11"（展示用 key）。"""
    return str(version).strip().replace("_", ".")


def _ver_tag(version):
    """文件名用 key："1.4.11" -> "1_4_11"。"""
    return _norm_ver(version).replace(".", "_")


def scan_path(version):
    return os.path.join(RAW_DIR, "apk_scan_%s.json" % _ver_tag(version))


def load_scan(version):
    """读取并缓存某版本的 apk_scan_<ver>.json。

    返回解析后的 dict；文件缺失/损坏时抛出 IOError/ValueError，由调用方决定
    如何优雅降级。
    """
    ver = _norm_ver(version)
    if ver in _SCAN_CACHE:
        return _SCAN_CACHE[ver]
    p = scan_path(ver)
    if not os.path.exists(p):
        raise IOError("raw scan missing: %s (先运行 scan_apk.py)" % p)
    with io.open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    _SCAN_CACHE[ver] = data
    return data


def _hit(ok, ver, bucket, basename):
    """统一的 (bool, evidence) 返回格式。"""
    tag = _ver_tag(ver)
    if ok:
        ev = "CONFIRMED: apk_scan_%s.json[%s] contains '%s'" % (tag, bucket, basename)
    else:
        ev = "ABSENT: '%s' not in apk_scan_%s.json[%s]" % (basename, tag, bucket)
    return bool(ok), ev


def module_present(version, basename):
    """某 .luac basename 是否出现在该版本 APK 的 assets/src/ 任意位置。

    判定依据 raw['luac_basenames']（全部 .luac 的 basename 集合）。
    返回 (bool, evidence_str)。
    """
    scan = load_scan(version)
    base = os.path.basename(str(basename))
    return _hit(base in set(scan.get("luac_basenames", [])), version,
                "luac_basenames", base)


def config_present(version, basename):
    """某 config_*.luac basename 是否存在于该版本（raw['config_tables']）。

    注意：raw['config_tables'] 只枚举 config_*.luac；.json 配置表不在此清单内，
    对这类文件应另行人工核对 assets/ 目录。返回 (bool, evidence_str)。
    """
    scan = load_scan(version)
    base = os.path.basename(str(basename))
    return _hit(base in set(scan.get("config_tables", [])), version,
                "config_tables", base)


def cmdresolve_present(version, n):
    """某 cmd_resolve_<n>.luac 是否存在。n 接受 int 或 str（如 11 / '11' / '11.luac'）。

    判定依据 raw['cmd_resolve']。返回 (bool, evidence_str)。
    """
    s = str(n).strip()
    m = re.match(r"^cmd_resolve_(\d+)", s)
    if m:
        num = m.group(1)
    else:
        num = s.replace(".luac", "").strip()
    base = "cmd_resolve_%s.luac" % num
    scan = load_scan(version)
    return _hit(base in set(scan.get("cmd_resolve", [])), version,
                "cmd_resolve", base)


def ui_module_files(version, module):
    """返回某 game 模块下全部 UI 相关 luac 的 basename 列表（raw['ui_by_module']）。

    模块不存在时返回空列表（不抛错）。
    """
    scan = load_scan(version)
    return list((scan.get("ui_by_module") or {}).get(str(module), []))


# ---- 以下为便捷集合查询，供审计器批量比对 ----

def luac_set(version):
    return set(load_scan(version).get("luac_basenames", []))


def config_set(version):
    return set(load_scan(version).get("config_tables", []))


def cmdresolve_set(version):
    return set(load_scan(version).get("cmd_resolve", []))


def game_module_set(version):
    return set(load_scan(version).get("game_modules", []))


def ui_module_keys(version):
    return set((load_scan(version).get("ui_by_module") or {}).keys())


def res_category_set(version):
    return set((load_scan(version).get("res_categories") or {}).keys())


if __name__ == "__main__":
    # 自检：python presence_lib.py 打印三版本概况
    for v in VERSIONS:
        try:
            s = load_scan(v)
            print("%-7s luac=%-5d cfg=%-4d cmdres=%-4d ui_mods=%-3d res_cats=%-3d"
                  % (v, s.get("lua_total"), len(s.get("config_tables", [])),
                     len(s.get("cmd_resolve", [])),
                     len(s.get("ui_by_module", {})),
                     len(s.get("res_categories", {}))))
        except Exception as e:
            print("%-7s ERROR %s" % (v, e))
