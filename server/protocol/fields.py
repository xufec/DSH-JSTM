# -*- coding: utf-8 -*-
"""protocol.fields —— SC/CS 字段规格注册表 + 通用回显编码器（Phase 2 step 1）。

设计依据：analysis/phase2_design.md §二 core/protocol/。

迁移来源（mock_server.py 当前行号）：
  _SC_FIELDS_CACHE / _sc_fields        L2020–2042
  _CS_FIELDS_CACHE / _cs_fields        L3132–3154
  _sc_w                                 L3157–3163
  encode_by_sc_with_echo                L3166–3246

依赖：
  protocol.frame（w_u16/w_u32/w_str）、config.loader（kcfg_best_attr_table）、
  core.runtime（log + HERE 定位 fields.json）。
无循环 import：frame / config.loader 均不反向依赖本模块。

★ fields.json 路径与现状逐字一致：原 mock_server HERE=server/，
  取 dirname(HERE)/protocol/fields.json = <项目根>/protocol/fields.json。
"""

import os
import json
import struct

from core import runtime
from protocol.frame import w_u16, w_str
from config.loader import kcfg_best_attr_table

log = runtime.log

# <项目根>/protocol/fields.json（与现状 os.path.dirname(HERE)/protocol/fields.json 同）。
_FIELDS_JSON = os.path.join(os.path.dirname(runtime.HERE), 'protocol', 'fields.json')

_SC_FIELDS_CACHE = None
_CS_FIELDS_CACHE = None


def _sc_fields(cmd):
    """返回该 CMD 的 SC 字段列表 [{'name':..,'type':..}, ...]（读 protocol/fields.json）。"""
    global _SC_FIELDS_CACHE
    if _SC_FIELDS_CACHE is None:
        _SC_FIELDS_CACHE = {}
        try:
            with open(_FIELDS_JSON, encoding='utf-8') as f:
                raw = json.load(f)
            for k, v in raw.items():
                try:
                    c = int(v.get('cmd'))
                except Exception:
                    continue
                if (v.get('dir') or '') != 'sc':
                    continue
                _SC_FIELDS_CACHE.setdefault(c, v.get('fields') or [])
        except Exception as e:
            log('server.log', '!! _sc_fields load failed: %r' % (e,))
    return _SC_FIELDS_CACHE.get(int(cmd), [])


def has_sc_definition(cmd):
    """该 cmd **有没有 SC 定义**（缓存里有条目即算，即使字段为空）。

    ★ 2026-10-17 修：`_sc_fields` 搬进本模块时，mock_server.py 里那份"模块级
      `_SC_FIELDS_CACHE`"被一起注释掉了，但那边仍有三处**直接引用**这个名字：
        · `_sc_defined()`  —— 其 `except` 把 NameError 吞掉 ⇒ 恒返回 False
          （"有没有 SC 定义"永远判错）
        · `_UNSUPPORTED_ACTION_CMDS` / 默认应答两处守卫 —— NameError 进 except，
          ⇒ 本该"明确回失败"的命令**静默无应答**
      缓存是**本模块的私有全局**（`_sc_fields` 里 `global` 重绑），所以外部不能
      `from ... import _SC_FIELDS_CACHE`（拿到的是 None 那次的值）。这里提供公共判定，
      外部一律用它，别再摸缓存。
    """
    _sc_fields(cmd)                       # 确保缓存已加载
    return int(cmd) in (_SC_FIELDS_CACHE or {})


def _cs_fields(cmd):
    """★ R188：返回该 CMD 的 CS 字段列表（与 _sc_fields 同源，dir == 'cs'）。"""
    global _CS_FIELDS_CACHE
    if _CS_FIELDS_CACHE is None:
        _CS_FIELDS_CACHE = {}
        try:
            with open(_FIELDS_JSON, encoding='utf-8') as f:
                raw = json.load(f)
            for k, v in raw.items():
                try:
                    c = int(v.get('cmd'))
                except Exception:
                    continue
                if (v.get('dir') or '') != 'cs':
                    continue
                _CS_FIELDS_CACHE.setdefault(c, v.get('fields') or [])
        except Exception as e:
            log('server.log', '!! _cs_fields load failed: %r' % (e,))
    return _CS_FIELDS_CACHE.get(int(cmd), [])


def _sc_w(tp):
    """字段的字节宽度（string / 字节数组 返回 -1 表示变长）。

    ★ PHASE 2.29：补上**字节数组**类型（`b` / `bytes` / `buffer`）。
      来源：1.4.11 APK 的格式串用 `字段名@b` 表示字节数组（如 `SC_10341.img__b`、
      与 `s`=string 同属变长；线序为 `u16 长度 + 原始字节`，与 string 同框架）。
      而 `protocol/fields.json`（**源自 1.4.9**）把 `SC_10341.img` 标成了 **`bool`**
      ⇒ 编码器按 1 字节发 ⇒ 整段错位 ⇒ 「保存自定义头像」异常。
    """
    t = (tp or '').lower()
    if t.startswith('string'):
        return -1
    if t in ('b', 'bytes', 'buffer', 'byte[]', 'bin'):
        return -1
    return {'uint8': 1, 'int8': 1, 'bool': 1, 'uint16': 2, 'int16': 2,
            'uint32': 4, 'int32': 4, 'float': 4, 'double': 8}.get(t, 1)


def encode_by_sc_with_echo(cmd, body=b'', code=1):
    """★★ R188：通用回显编码器 —— 按权威 SC 编，CS 里同名字段回显真值。

    1. 用 CS 的字段顺序算 body 偏移（string = 2 + len）
    2. 用 SC 的字段顺序编码；同名同类型 ⇒ 读 body；否则 ⇒ 0 / ''
    3. code/result 首字段 ⇒ code
    """
    cs_fs = _cs_fields(cmd)
    sc_fs = _sc_fields(cmd)
    if not sc_fs:
        return b''
    # ① CS 偏移表
    off, o = {}, 0
    for f in cs_fs:
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        tp = (f.get('type') or '') if isinstance(f, dict) else ''
        off[nm] = (o, tp)
        w = _sc_w(tp)
        if w == -1:
            n = struct.unpack_from('>H', body, o)[0] if len(body) >= o + 2 else 0
            o += 2 + n
        else:
            o += w
    # ② 按 SC 编码
    out = b''
    for f in sc_fs:
        nm = (f.get('name') or '') if isinstance(f, dict) else ''
        tp = (f.get('type') or '') if isinstance(f, dict) else ''
        its = f.get('items') if isinstance(f, dict) else None
        if its:                                   # 子表 ⇒ 默认空表
            # ★★★ R203：空子表的"高置信度真值"挂钩 ——
            #   若该子表的元素字段名与某配置的主表字段名重合 ≥ 8 ⇒ 填 1 条（按同名字段取）✓
            _en = [x.get('name') for x in its if isinstance(x, dict)]
            _cfg, _row = kcfg_best_attr_table(_en, 8)
            if _cfg and _row:
                out += w_u16(1)
                for _x in its:
                    if not isinstance(_x, dict):
                        continue
                    _xn = _x.get('name') or ''
                    _xt = (_x.get('type') or '').lower()
                    if _x.get('items'):
                        out += w_u16(0)
                    elif _xt.startswith('string'):
                        _v = _row.get(_xn)
                        out += w_str(_v if isinstance(_v, str) else '')
                    else:
                        _w2 = _sc_w(_xt)
                        _v = _row.get(_xn)
                        try:
                            _v = int(_v or 0)
                        except Exception:
                            _v = 0
                        out += (int(_v) & ((1 << (_w2 * 8)) - 1)).to_bytes(_w2 if _w2 > 0 else 1, 'big')
            else:
                out += w_u16(0)
            continue
        w = _sc_w(tp)
        if nm in ('code', 'result') and out == b'':
            # ★ R189：按 SC 声明的宽度发（有 8 条的 code 是 uint32，硬编码 u8 会越界）
            out += int(code).to_bytes(w, 'big')
            continue
        if w == -1:
            hit = off.get(nm)
            val = ''
            if hit and (hit[1] or '').lower().startswith('string'):
                o2 = hit[0]
                n2 = struct.unpack_from('>H', body, o2)[0] if len(body) >= o2 + 2 else 0
                val = body[o2 + 2:o2 + 2 + n2].decode('utf-8', 'replace')
            out += w_str(val)
            continue
        hit = off.get(nm)
        val = 0
        if hit and _sc_w(hit[1]) == w and len(body) >= hit[0] + w:
            val = int.from_bytes(body[hit[0]:hit[0] + w], 'big')
        out += val.to_bytes(w, 'big')
    return out
