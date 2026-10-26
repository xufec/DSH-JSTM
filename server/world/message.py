"""出网层：「按受众分两条通道 + 共用同一个底层 send()」。

═══════════════════════════════════════════════════════════════════════════
审计结论（已核验）：
  · kongkongxiyou 的 `messageService` **不是**唯一出口 —— 另有 20+ 处直接
    `channel.pushMessage`（area.js / areaLogic.js / team.js / Guilder.js / chatService.js）
  · 其错误回调 `errHandler` 因 **uid/playerId 错配是空操作**：
      channelService 的 `groups[sid]=[uid,...]` ⇒ `failIds` 装 uid
      而 `removePlayerByUid` 查的是按 **playerId** 索引的 `players{}`
      ⇒ 必然查不到、静默 return。

JSTM 的设计（修正上述两点）：
  ① 定向推送（单人 / ByUids / ByAOI / Tips）与频道广播 **共用同一个 `send()`**
  ② 失败处理只写一处，且**携带 player_id**（不是 uid）
  ③ 失败**不立即踢**：连续 `FAIL_STREAK_TO_KICK` 次才判定断线（防网络抖动误踢）
  ④ AOI 只产出 player_id / uid 列表，**绝不碰 socket**（沿用既有 aoi.py 纪律）
"""

from __future__ import annotations


from .consts import FAIL_STREAK_TO_KICK


class MessageService(object):
    """定向推送 + 唯一底层落点。

    `router` 是注入的发送函数：`router(session_addr, route, msg) -> bool`。
    这样本模块**不依赖任何具体网络实现**（mock_server 是 socket，单测是假 router）。
    """

    def __init__(self, router=None, on_unreachable=None,
                 fail_streak_to_kick=FAIL_STREAK_TO_KICK, logger=None):
        self.router = router                      # type: Optional[Callable]
        self.on_unreachable = on_unreachable      # type: Optional[Callable[[int], None]]
        self.fail_streak_to_kick = int(fail_streak_to_kick)
        self._log = logger
        self._fail_streak = {}                    # player_id -> 连续失败次数
        self._stats = {'sent': 0, 'failed': 0, 'dropped_no_addr': 0, 'kicked': 0}

    # ── 唯一底层落点 ───────────────────────────────────────────────────
    def send(self, player, route, msg):
        """所有出网（定向 + 频道）最终都走这里。返回 bool。"""
        if player is None:
            return False
        addr = getattr(player, 'session_addr', None)
        if not addr:
            self._stats['dropped_no_addr'] += 1
            return False
        if self.router is None:
            self._stats['dropped_no_addr'] += 1
            return False

        ok = False
        try:
            ok = bool(self.router(addr, route, msg))
        except Exception as e:
            if self._log is not None:
                self._log('!! send failed %r route=%s player_id=%s'
                          % (e, route, getattr(player, 'id', None)))
            ok = False

        if ok:
            self._stats['sent'] += 1
            self._fail_streak.pop(player.id, None)
            return True

        self._stats['failed'] += 1
        n = self._fail_streak.get(player.id, 0) + 1
        self._fail_streak[player.id] = n
        if n >= self.fail_streak_to_kick:
            self._stats['kicked'] += 1
            self._fail_streak.pop(player.id, None)
            if self._log is not None:
                self._log('!! player unreachable (%d consecutive failures), '
                          'force cleanup player_id=%s' % (n, player.id))
            if self.on_unreachable is not None:
                try:
                    self.on_unreachable(player.id)
                except Exception as e:            # 清理失败也不应影响发送方
                    if self._log is not None:
                        self._log('!! on_unreachable failed: %r' % (e,))
        return False

    # ── 通道 A：定向 ───────────────────────────────────────────────────
    def send_to_player(self, player, route, msg):
        return self.send(player, route, msg)

    def send_to_uids(self, players, route, msg):
        """players 必须是一串 **Player 对象**（不是 uid）。
        ★ 参考实现这里传的是 {uid, sid} 并在回调里把 uid 当 playerId 用 —— 该错误已避免。"""
        n = 0
        for p in players:
            if self.send(p, route, msg):
                n += 1
        return n

    def send_by_aoi(self, area, route, msg, pos, ignore=None, types=None):
        """AOI 群推：坐标 → 附近 watcher → 逐个 send。返回实际送达数。

        对应参考实现的 `pushMessageByAOI`，但**返回 player_id 而不是 uid**，
        从根本上消除 uid/playerId 混淆。
        """
        from .consts import EntityType
        types = EntityType.PLAYER if types is None else types
        ignore = ignore or set()
        uids = area.watchers_of(pos[0], pos[1], types)
        targets = []
        for aoi_key in uids:
            # ★ aoi_key 是 AOI 的键空间（对玩家即 entity_id），**不是账号 uid**；
            #   参考实现正是在这里把 uid 与 playerId 混用，导致 errHandler 空操作。
            pl = area.get_player_by_entity_id(aoi_key)
            if pl is None or pl.id in ignore:
                continue
            targets.append(pl)
        return self.send_to_uids(targets, route, msg)

    def send_tips(self, player, route, code, text=''):
        return self.send(player, route, {'code': code, 'msg': text or code})

    # ── 观测 / 维护 ────────────────────────────────────────────────────
    def clear_player(self, player_id):
        self._fail_streak.pop(player_id, None)

    def stats(self):
        s = dict(self._stats)
        s['tracked'] = len(self._fail_streak)
        return s


class Channel(object):
    """单进程频道。

    参考实现是跨进程 ChannelService（按 sid 分组 + RPC + store 持久化）；
    单进程下这些都**不需要**，只保留「成员集合 + 广播 + 空则销毁」。
    ★ 广播与定向推送共用 `MessageService.send()`。
    """

    def __init__(self, name, message_service, resolve_player):
        self.name = name
        self._ms = message_service
        self._resolve = resolve_player          # player_id -> Player | None
        self._members = set()                   # player_id 集合
        self._stats = {'push': 0, 'sent': 0}

    def add(self, player_id):
        self._members.add(int(player_id))

    def leave(self, player_id):
        self._members.discard(int(player_id))

    def get_user_amount(self):
        return len(self._members)

    def members(self):
        return sorted(self._members)

    def push_message(self, route, msg):
        """返回实际送达数。"""
        self._stats['push'] += 1
        sent = 0
        for pid in list(self._members):
            pl = self._resolve(pid)
            if pl is None:
                self._members.discard(pid)       # 顺手清理（自愈）
                continue
            if self._ms.send(pl, route, msg):
                sent += 1
        self._stats['sent'] += sent
        return sent

    def stats(self):
        s = dict(self._stats)
        s['members'] = len(self._members)
        return s


class ChannelService(object):
    """频道管理（懒创建 + 空则销毁）。命名规则沿用参考实现 `channelUtil.js`。"""

    GLOBAL = 'pomelo'          # ⚠ 该字面量是否被 1.4.9 客户端依赖【未知】；
                               #   若不依赖，建议改成语义名 'world'

    def __init__(self, message_service, resolve_player):
        self._ms = message_service
        self._resolve = resolve_player
        self._channels = {}

    # -- 命名（照搬参考实现的规则：把社交结构编码进频道名）--
    @staticmethod
    def global_channel_name():
        return ChannelService.GLOBAL

    @staticmethod
    def area_channel_name(area_id_or_instance_id):
        return 'area_%s' % (area_id_or_instance_id,)

    @staticmethod
    def team_channel_name(team_id):
        return 'team_%s' % (team_id,)

    @staticmethod
    def guild_channel_name(guild_id):
        return 'guild_%s' % (guild_id,)

    # -- 生命周期 --
    def get_channel(self, name, create=False):
        ch = self._channels.get(name)
        if ch is None and create:
            ch = Channel(name, self._ms, self._resolve)
            self._channels[name] = ch
        return ch

    def destroy_channel(self, name):
        self._channels.pop(name, None)

    def sweep_empty(self):
        """销毁空频道（参考实现是在 leave/kick 时顺带判断）。"""
        dead = [n for n, c in self._channels.items() if c.get_user_amount() == 0]
        for n in dead:
            self._channels.pop(n, None)
        return dead

    def stats(self):
        return {
            'channels': len(self._channels),
            'detail': {n: c.stats() for n, c in self._channels.items()},
        }
