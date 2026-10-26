"""JSTM 世界层（P1 骨架）—— 五层容器 + 分层 tick。

═══════════════════════════════════════════════════════════════════════════
★ 来源声明（沿用服务器既有纪律：只借设计思想，不复制代码）
───────────────────────────────────────────────────────────────────────────
本包的设计来自对 `analysis/server_reference/kongkongxiyou/` 的审计结论
（`architecture.md` / `scene.md` / `jstm_blueprint.md`），**全部为自研 Python**：

  · 五层容器 AreaManager / Scene / Instance / InstancePool / Area
  · 分层 tick：100ms（实体/动作/AI/巡逻） + 1.0s（刷怪刷物） + 3.0s（玩家恢复/踢人）
  · AOI 双注册（watcher + object）+ 差量同步
  · 出网「按受众分两条通道」，共用同一个底层 send()
  · handler 前置守卫（统一取玩家 → 定场景 → 校验在场 → 注入 ctx）

★★ 本包与参考项目刻意的不同（均为审计发现的缺陷修复）
───────────────────────────────────────────────────────────────────────────
  Q1 分频用**精确 3.0s**（参考实现因 `timeCount>30→归零` 实为 31 tick = 3.1s）
  Q2 **客户端必须上传整条路径**（1.4.9 协议事实）⇒ 必须严格校验，见 move.py
  · `Area` 构造与启动分离（参考实现 `new Area()` 就会 `timer.run()`）
  · 下线缓存用真 TTL（参考实现"边写边全清"等于没缓存）
  · 并发用「每玩家一把锁 + 等待」（参考实现用 `'waiting'` 字符串当致命错误）
  · 推送失败降级为「连续失败 N 次才判定断线」（参考实现失败即踢，且因
    uid/playerId 错配实际是空操作）
  · 塔格尺寸可配（参考实现硬编码 300 世界像素；JSTM 用瓦片坐标，默认 8）

★ 复用既有两个模块（**不重复实现**）
  · `server/aoi.py`    —— 自研均匀网格 AOI（已含双向差集 / A1–A8 修复 / 埋点）
  · `server/pathfind.py` —— 自研 8 邻域 A* + Bresenham 直线 + 限流器
  见 `_deps.py`
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

from .consts import (ActionType, Code, EntityType, LocationKind, TICK_MS,
                     HP_TICK_SECONDS, ONE_SECOND, THREE_SECONDS)
from .entities import Item, Mob, Player, PlayerLocation
from .ticker import TickScheduler
from .message import Channel, ChannelService, MessageService
from .move import ActionManager, MoveAction, validate_client_move
from .area import Area
from .containers import AreaManager, Instance, InstancePool, Scene

__all__ = [
    'ActionType', 'Code', 'EntityType', 'LocationKind',
    'TICK_MS', 'ONE_SECOND', 'THREE_SECONDS', 'HP_TICK_SECONDS',
    'Item', 'Mob', 'Player', 'PlayerLocation',
    'TickScheduler',
    'MessageService', 'Channel', 'ChannelService',
    'ActionManager', 'MoveAction', 'validate_client_move',
    'Area', 'AreaManager', 'Scene', 'Instance', 'InstancePool',
]

__version__ = '0.1.0-p1'
