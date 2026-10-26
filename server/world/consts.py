"""常量与枚举。

分频常量对应 **Q1 决策：精确 3.0s**（不照抄参考实现的 3.1s）。
"""

from __future__ import annotations

# ── 分频 ─────────────────────────────────────────────────────────────────
TICK_MS = 100                 # 主 tick：实体 / 动作（行走、复活）/ AI / 巡逻
ONE_SECOND = 1.0              # 刷怪刷物
THREE_SECONDS = 3.0           # 玩家 HP/MP 恢复 + 心跳超时踢人 + 策略扩展
HP_TICK_SECONDS = THREE_SECONDS   # ★ HP/MP 恢复的口径 = 3.0s（不是 100ms！）

# 参考实现的等效周期是 31 tick = 3.1s；保留这个常量只用于**数值换算说明**，
# 不用于分频（见 hpmp_recalibrate 的说明）。
REFERENCE_HP_TICK_SECONDS = 3.1

# ── 时间／容量 ───────────────────────────────────────────────────────────
KICK_TIME = 30 * 60.0         # 心跳超时踢人（参考实现 1800000ms）
PLAYER_CACHE_TTL = 60.0       # 下线玩家对象缓存（参考实现 60s，但实现是坏的）
FAIL_STREAK_TO_KICK = 3       # 推送连续失败几次才判定断线（参考实现是"一次即踢"）
INSTANCE_LIFE_TIME = 300.0    # 空副本回收（★ 从配置读，不硬编码）
INSTANCE_GC_INTERVAL = 60.0   # 副本回收检查周期


class EntityType(object):
    """与参考项目 `consts.EntityType` 对齐的**位掩码**（便于 AOI 按类型过滤）。"""
    PLAYER = 1
    MOB = 2
    NPC = 4
    ITEM = 8
    EQUIPMENT = 16


class LocationKind(object):
    """玩家所处的容器种类 —— 用显式状态取代「靠 areaId/instanceId 猜」。"""
    NONE = 0        # 不在任何世界实例里（刚登录 / 已下线 / 换场景途中）
    SCENE = 1       # 常驻场景
    INSTANCE = 2    # 副本


class ActionType(object):
    DEFAULT = 0
    MOVE = 1
    REVIVE = 2


class AreaType(object):
    SCENE = 1
    SINGLE_INSTANCE = 2
    TEAM_INSTANCE = 3


class AreaKind(object):
    SAFE = 0
    DOMAIN = 1
    NORMAL = 2
    FIGHT = 3
    MY_BOSS = 4
    WORLD_BOSS = 5


class Code(object):
    """返回码（P1 只列用到的一小部分；正式实现应改为配置表驱动）。"""
    OK = 200
    FAIL = 500
    NOT_LOGGED_IN = 1001
    PLAYER_NOT_FOUND = 1002
    AREA_NOT_FOUND = 1003
    PLAYER_NOT_IN_AREA = 1004
    UID_MISMATCH = 1005
    ADD_PLAYER_FAILED = 1006
    ILLEGAL_MOVE = 1007
    INSTANCE_EXISTS = 1008
    SAME_AREA = 136


# ── 战利/怪物的容错参数（来自参考实现，标注为"参考值，需实测调整"）──────────
LEASH_RANGE = 500             # 参考实现 ai/action/moveToTarget.js 的脱战距离（世界像素）
FAILBACK_AREA_ID = 1001       # 异常时让客户端回主城（参考实现静默改写 areaId=1001）
