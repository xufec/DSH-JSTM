"""让 `world` 包可以复用 server/ 下既有的**扁平模块** `aoi.py` / `pathfind.py`。

`mock_server.py` 是以「在 server/ 目录下运行」为前提 `import aoi as aoi_mod` 的。
本包可能是从任意 cwd 启动的，所以这里显式把 `server/`（= 本文件的上一级）加入
`sys.path`，再导入，避免重复实现 AOI / 寻路。

若导入失败，`AOI` / `MapGrid` 等为 None，调用方需自行判断（与 mock_server 的做法一致）。
"""

from __future__ import annotations

import os
import sys

_SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SERVER_DIR not in sys.path:
    sys.path.insert(0, _SERVER_DIR)

aoi_mod = None
pathfind_mod = None
try:
    import aoi as aoi_mod            # noqa: F401
except Exception as _e:              # pragma: no cover
    print('!! world._deps: aoi import failed: %r' % (_e,))

try:
    import pathfind as pathfind_mod  # noqa: F401
except Exception as _e:              # pragma: no cover
    print('!! world._deps: pathfind import failed: %r' % (_e,))


def new_aoi(tower_size=8):
    """建一个 AOI 实例（每个 Area 一个）。"""
    if aoi_mod is None:
        return None
    return aoi_mod.AOI(tower_size=int(tower_size))


def new_mapgrid(width=256, height=256, blocked=None, allow_all=True):
    """建地图通行网格（**全服共享一份**，对应审计结论「Map 共享 / Area 各自持引用」）。"""
    if pathfind_mod is None:
        return None
    return pathfind_mod.MapGrid(width, height, blocked=blocked, allow_all=allow_all)


def new_ratelimiter(max_tiles_per_sec=12.0, burst=6):
    if pathfind_mod is None:
        return None
    return pathfind_mod.MoveRateLimiter(max_tiles_per_sec=max_tiles_per_sec, burst=burst)


def modules_ready():
    return {'aoi': aoi_mod is not None, 'pathfind': pathfind_mod is not None}
