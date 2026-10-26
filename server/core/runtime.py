# -*- coding: utf-8 -*-
"""core.runtime —— 进程级单例运行时（Phase 2 step 1：变量真正搬家）。

设计依据：analysis/phase2_design.md §1.4（全局状态耦合点）、§二 core/、§四、§九 风险 1。

本步把 mock_server.py 的模块级全局**物理搬家**到这里，作为新模块唯一的全局来源：
    CFG             运行配置 dict（main() 加载后 CFG.clear/update 充填；原地变更，按对象共享）
    LIVE_CONNECTIONS 在线连接列表（原地 append/remove，按对象共享）
    LIVE_LOCK       连接计数/广播锁（原地 acquire/release，按对象共享）
    CUR_VER         当前连接版本族（1.4.9/1.4.11/1.3.0）—— ★按请求**重绑**，
                    新模块与 mock_server 一律读写 `runtime.CUR_VER`，禁止 `from ... import CUR_VER`。
    DEFAULT_UID     老库无主角色回退账号（R49）
    HERE/LOGDIR     server/ 根目录与日志目录

★ 循环 import 红线（设计 §九 风险 1）：本模块**只依赖标准库**（os/sys/time/threading），
  不 import 任何 server 业务模块。新业务模块统一 `from core import runtime` 取全局，
  禁止 `import mock_server`。

★ 为什么 CFG/LIVE_CONNECTIONS/LIVE_LOCK 可 `from core.runtime import CFG`：
  它们从不在 mock_server 里被**重绑**（只 `.clear()/.update()/.append()/.acquire()` 原地改），
  故所有 importer 拿到的是**同一个 dict/list/lock 对象**，原地变更彼此可见。
  CUR_VER 是字符串、会被重绑，故**不做** from-import，全程走 `runtime.CUR_VER`。
"""

import os
import sys
import time
import threading

# server/ 根目录（本文件位于 server/core/runtime.py ⇒ 上溯两级）。
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGDIR = os.path.join(HERE, 'logs')

# ── 进程级单例（与 mock_server.py 原定义逐字一致，仅搬家）────────────────────
CFG = {}                       # mock_server.py 原 L247
LIVE_CONNECTIONS = []          # [(TcpHandler, threading.Lock)] 原 L248
LIVE_LOCK = threading.Lock()   # 原 L249
# 当前请求所属客户端版本族（原 L4271）。
# ★★ PHASE 2.26：**改为线程局部**，修掉「多版本并发互相覆盖」的系统性竞态。
#   背景：该值是**每连接**的（`account/service.py` L113 设 `h._ver_family`），
#   但原先存成**模块级全局**，而服务端是多线程（ThreadingTCPServer）⇒
#   1.3.0 / 1.4.9 连接会把 1.4.11 连接的值覆盖掉 ⇒ 1.4.11 的请求按**错误版本布局**发包
#   （例：`build_10302` 走 `CUR_VER != '1.3.0'` 为假 ⇒ 少发 `diamond`/`rainbow_diamond`
#    共 8 字节 ⇒ 整包错位 ⇒ 面板空白/显示异常）。
#   每连接由**独立线程**处理 ⇒ 线程局部即天然隔离。
#   写入：`runtime.set_cur_ver(...)`（**不要**再写 `runtime.CUR_VER = ...`，
#         那会创建真正的模块属性并遮蔽下面的 PEP 562 读取）。
#   读取：`runtime.CUR_VER`（经 `__getattr__` 走线程局部，旧写法全部兼容）。
_TLS = threading.local()


def set_cur_ver(v):
    """设置**本线程（= 本连接）**的客户端版本族。"""
    _TLS.cur_ver = v


def get_cur_ver():
    """读取本线程（= 本连接）的客户端版本族。"""
    return getattr(_TLS, 'cur_ver', '1.4.9')


def __getattr__(name):
    """PEP 562：让 `runtime.CUR_VER` 的**读取**走线程局部（未在本模块 dict 中定义）。"""
    if name == 'CUR_VER':
        return get_cur_ver()
    raise AttributeError('module %r has no attribute %r' % (__name__, name))


# 老库无主角色回退账号（R49，原 L4259）
DEFAULT_UID = 'dsh_local'


def log(name, text):
    """统一日志（原 mock_server.py L159–165，逐字搬家）。

    写 server/logs/<name> 并 echo 到 stdout。dispatch.set_logger(log) 已在
    mock_server.py 顶部接线，handler 异常也落这里。
    """
    os.makedirs(LOGDIR, exist_ok=True)
    line = '[%s] %s\n' % (time.strftime('%H:%M:%S'), text)
    sys.stdout.write(line)
    sys.stdout.flush()
    with open(os.path.join(LOGDIR, name), 'a', encoding='utf-8') as f:
        f.write(line)


def ver_family_of(body_len, args):
    """按 CS_1110 的 args 表判客户端版本族（原 mock_server.py L4274–4286，逐字搬家）。

    判据用"args 键数 + 体长"两级：
      1.3.0 只报 account 一对 → 键数 ≤2；
      1.4.11 键数多但体长 <210；其余按 1.4.9。
    """
    n = len(args or {})
    if n <= 2:
        return '1.3.0'
    if int(body_len) < 210:
        return '1.4.11'
    return '1.4.9'


# ── 兼容壳：保留 step 0 的 get_runtime() 入口（薄封装，不引入第二份状态）──────
class _RuntimeView(object):
    """对单例的属性视图（`.cfg` / `.cur_ver` 等），供喜欢对象风格的调用方使用。"""
    __slots__ = ()

    @property
    def cfg(self):
        return CFG

    @property
    def live_connections(self):
        return LIVE_CONNECTIONS

    @property
    def live_lock(self):
        return LIVE_LOCK

    @property
    def cur_ver(self):
        return get_cur_ver()

    @cur_ver.setter
    def cur_ver(self, v):
        set_cur_ver(v)


_INSTANCE = None


def get_runtime():
    """取进程级运行时视图（step 0 壳的兼容入口；真实状态即本模块单例）。"""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = _RuntimeView()
    return _INSTANCE
