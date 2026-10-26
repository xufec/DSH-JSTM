"""最小实体模型（P1 只保留世界骨架需要的字段）。

★ 关键：HP/MP 恢复的口径 —— **Q1 决策 = 精确 3.0s**。

参考实现的语义（`domain/entity/player.js#update` + `setHpLevel`）已核验：
    hpCount = **待恢复量池**（由药品/食物累加，上限 hpCapacity）
    每次 update（即每 3.1s）恢复 hpSpeed 点，直到池耗尽
    ⇒ **这不是"每秒回血 X"，而是"每 3.1 秒回 hpSpeed 点"**

因此 JSTM 分频改成 3.0s 后：
    · 直接沿用参考的 hpSpeed 数字 ⇒ **每秒钟的回血率会快 3.1/3.0 ≈ 3.33%**
    · 想保持"每秒回血率"一致 ⇒ hpSpeed_jstm = hpSpeed_ref * (3.0 / 3.1) ≈ ×0.9677
    · **更好的做法是按目标推导**（见 hpmp_recalibrate），因为参考的
      config/data/hpmp.json 数值本身自相矛盾：
        lv0: hpSpeed=30, hpCapacity=100000 ⇒ 排空需 3333 步 × 3.1s ≈ 2.9 小时
        而 consts.js 注释写的是 "You need 10s to recover hp from 0 to full"
      ⇒ **参考数值是未填完的占位数据，不可照抄。**
"""

from __future__ import annotations

from .consts import (EntityType, HP_TICK_SECONDS, LocationKind,
                     REFERENCE_HP_TICK_SECONDS)


class PlayerLocation(object):
    """玩家所处容器的**显式状态**。

    取代参考实现「拿 areaId/instanceId 去两张表里猜」的做法；
    中间态（NONE）是第一等公民，而不是靠兜底逻辑掩盖。
    """

    __slots__ = ('kind', 'area_id', 'instance_id')

    def __init__(self, kind=LocationKind.NONE, area_id=0, instance_id=None):
        self.kind = kind
        self.area_id = int(area_id or 0)
        self.instance_id = instance_id

    @classmethod
    def none(cls):
        return cls(LocationKind.NONE, 0, None)

    @classmethod
    def scene(cls, area_id):
        return cls(LocationKind.SCENE, area_id, None)

    @classmethod
    def instance(cls, instance_id, area_id):
        return cls(LocationKind.INSTANCE, area_id, instance_id)

    def __repr__(self):
        return 'PlayerLocation(kind=%s, area_id=%s, instance_id=%r)' % (
            self.kind, self.area_id, self.instance_id)


class Entity(object):
    """世界实体基类。"""

    type = 0

    def __init__(self, entity_id, x=0, y=0, range_=0, **kw):
        self.entity_id = int(entity_id)
        self.x = int(x)
        self.y = int(y)
        self.range = int(range_)
        self.died = False
        self.area = None

    def strip(self):
        return {'entityId': self.entity_id, 'type': self.type, 'x': self.x, 'y': self.y}

    def __repr__(self):
        return '<%s #%s @(%s,%s)>' % (type(self).__name__, self.entity_id, self.x, self.y)


class Player(Entity):
    """玩家。一份对象、多套索引（见 containers.AreaManager 注释）。"""

    type = EntityType.PLAYER

    def __init__(self, player_id, uid=None, name='', x=0, y=0, range_=12,
                 max_hp=1000, max_mp=500, walk_speed=12.0,
                 hp_speed=100, hp_capacity=10000,
                 mp_speed=100, mp_capacity=10000, **kw):
        Entity.__init__(self, player_id, x, y, range_)
        self.id = int(player_id)          # 与参考实现一致：playerId 即 player.id
        self.uid = int(uid if uid is not None else player_id)   # ★ 与 id **不同**的账号 id
        self.name = name
        self.guild_id = 0
        self.team_id = 0
        # 回包地址（对应参考实现 player.serverId/sessionData）—— 由登录/守卫写入
        self.session_addr = None
        # 位置归属（显式状态）
        self.location = PlayerLocation.none()
        # 战斗属性
        self.max_hp = int(max_hp)
        self.max_mp = int(max_mp)
        self.hp = int(max_hp)
        self.mp = int(max_mp)
        self.walk_speed = float(walk_speed)
        self.died = False
        # 恢复池（照搬参考实现语义）
        self.hp_speed = int(hp_speed)
        self.hp_capacity = int(hp_capacity)
        self.hp_count = 0
        self.mp_speed = int(mp_speed)
        self.mp_capacity = int(mp_capacity)
        self.mp_count = 0
        # 心跳
        self.kick_time = 0.0
        self.is_moving = False
        self.is_stop = True
        self._stats = {'hp_recover_steps': 0, 'hp_recovered': 0,
                       'mp_recover_steps': 0, 'mp_recovered': 0}

    # ── ★ 3.0s 口径的恢复（唯一驱动点在 tick_3s 层）────────────────────
    def update_recover(self, dt=HP_TICK_SECONDS):
        """每 3.0s 调用一次（见 Area/AreaManager 的 tick_3s 层）。

        返回 (hp_delta, mp_delta)，供调用方决定怎么推（本层不碰网络）。
        ⚠ **绝对不要把这个方法挂到 100ms 的 tick 上** —— 那会让回血快 30 倍。
        """
        hp_d, mp_d = 0, 0
        if self.hp < self.max_hp and self.hp_count > 0:
            self.hp_count -= self.hp_speed
            if self.hp_count < 0:
                hp_d = self.hp_speed + self.hp_count
                self.hp_count = 0
            else:
                hp_d = self.hp_speed
            self.hp += hp_d
            if self.hp > self.max_hp:
                self.hp = self.max_hp
            self._stats['hp_recover_steps'] += 1
            self._stats['hp_recovered'] += hp_d
        if self.mp < self.max_mp and self.mp_count > 0:
            self.mp_count -= self.mp_speed
            if self.mp_count < 0:
                mp_d = self.mp_speed + self.mp_count
                self.mp_count = 0
            else:
                mp_d = self.mp_speed
            self.mp += mp_d
            if self.mp > self.max_mp:
                self.mp = self.max_mp
            self._stats['mp_recover_steps'] += 1
            self._stats['mp_recovered'] += mp_d
        return hp_d, mp_d

    def feed_hp(self, amount):
        """药品/食物投入恢复池（对应参考实现 equipHandler 的 `hpCount += count*item.hp`）。"""
        self.hp_count = min(self.hp_capacity, self.hp_count + int(amount))
        return self.hp_count

    def feed_mp(self, amount):
        self.mp_count = min(self.mp_capacity, self.mp_count + int(amount))
        return self.mp_count

    def set_is_moving(self, v):
        self.is_moving = bool(v)

    def player_strip(self):
        d = self.strip()
        d.update({'playerId': self.id, 'name': self.name, 'hp': self.hp, 'mp': self.mp,
                  'maxHp': self.max_hp, 'maxMp': self.max_mp,
                  'guildId': self.guild_id, 'teamId': self.team_id})
        return d

    def stats(self):
        return dict(self._stats)


class Mob(Entity):
    """怪物（P1 只做「能刷、能移动、能脱战回位」，AI 留到 P4）。"""

    type = EntityType.MOB

    def __init__(self, entity_id, kind_id=0, x=0, y=0, range_=10,
                 max_hp=100, walk_speed=8.0, is_active_attack=False, **kw):
        Entity.__init__(self, entity_id, x, y, range_)
        self.kind_id = int(kind_id)
        self.spawn_x = int(x)
        self.spawn_y = int(y)
        self.max_hp = int(max_hp)
        self.hp = int(max_hp)
        self.walk_speed = float(walk_speed)
        self.is_active_attack = bool(is_active_attack)
        self.target = None
        self.path = []
        self.zone_id = 0

    def sleep_back(self):
        """脱战回位（参考实现 `returnToSpawningPosition` 的简化）。"""
        self.target = None
        self.x, self.y = self.spawn_x, self.spawn_y

    def strip(self):
        d = Entity.strip(self)
        d.update({'kindId': self.kind_id, 'hp': self.hp, 'maxHp': self.max_hp})
        return d


class Item(Entity):
    """掉落物 / 地面物（P1 用 items 层演示 100ms 层的超时消失）。"""

    type = EntityType.ITEM

    def __init__(self, entity_id, kind_id=0, x=0, y=0, life=60.0, now=0.0, **kw):
        Entity.__init__(self, entity_id, x, y, 0)
        self.kind_id = int(kind_id)
        self.life = float(life)
        self.expire_at = float(now) + self.life
        self.zone_id = 0

    def update(self, now):
        """100ms 层调用；返回 True 表示已死（该被移除）。"""
        if now >= self.expire_at:
            self.died = True
        return self.died

    def strip(self):
        d = Entity.strip(self)
        d.update({'kindId': self.kind_id})
        return d


# ══════════════════════════════════════════════════════════════════════════
# HP/MP 重标定工具（Q1 决策的落地配套）
# ══════════════════════════════════════════════════════════════════════════
def hpmp_recalibrate(target_full_seconds, max_hp, tick_seconds=HP_TICK_SECONDS):
    """按「从 0 回满需要 target_full_seconds 秒」推导 hp_speed / hp_capacity。

    返回 dict：
        steps          需要的恢复步数（向上取整）
        hp_speed       每步恢复量（= max_hp / steps，向上去整到整数且保证能回满）
        hp_capacity    恢复池上限（= max_hp，即一次投药最多回满）
        effective_seconds  按取整后的 hp_speed 实际回满耗时（秒）
        per_second     等效每秒回血量

    例：`hpmp_recalibrate(10, 100000)` @3.0s
        steps = ceil(10/3.0) = 4
        hp_speed = 25000 ⇒ 4 步×3.0s = 12.0s 回满（比目标略慢，故给出 per_second 供核对）
    """
    import math
    tick_seconds = float(tick_seconds)
    if tick_seconds <= 0:
        raise ValueError('tick_seconds must be > 0')
    if target_full_seconds <= 0:
        raise ValueError('target_full_seconds must be > 0')
    steps = int(math.ceil(float(target_full_seconds) / tick_seconds))
    steps = max(1, steps)
    hp_speed = int(math.ceil(float(max_hp) / float(steps)))
    return {
        'steps': steps,
        'hp_speed': hp_speed,
        'hp_capacity': int(max_hp),
        'effective_seconds': round(steps * tick_seconds, 3),
        'per_second': round(hp_speed / tick_seconds, 3),
    }


def hp_speed_to_3s(hp_speed_ref,
                   ref_tick=REFERENCE_HP_TICK_SECONDS,
                   jstm_tick=HP_TICK_SECONDS):
    """把参考实现（3.1s 口径）的 hpSpeed 换算到 JSTM 的 3.0s 口径，
    **保持"每秒回血率"不变**。

    hp_speed_jstm = hp_speed_ref * (3.0 / 3.1)  ≈ ×0.9677
    ⚠ 仅在"必须沿用参考数字"时使用；推荐用 hpmp_recalibrate 按目标重新推导。
    """
    ref_tick = float(ref_tick)
    if ref_tick <= 0:
        raise ValueError('ref_tick must be > 0')
    return int(round(float(hp_speed_ref) * (float(jstm_tick) / ref_tick)))
