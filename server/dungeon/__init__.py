# -*- coding: utf-8 -*-
"""dungeon 包 —— 副本列表 + 通关奖励闭环（Phase 10）。

禁止 `import mock_server`。
数据源：cfg/config_dungeon_new.json Dungeon（34 条 CONFIRMED：name/type/count/level_low/coin/exp）。
进度持久化：复用既有 `dungeon_progress` KV 表（ptype='dung_left'/'dung_got'）。
奖励：RewardService.grant(rid, awards, reference_id='dungeon:<bid>:<rid>:first') 幂等。
"""
