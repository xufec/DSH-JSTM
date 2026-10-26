# -*- coding: utf-8 -*-
"""battle_service —— Phase 2d。

server/battle.py 已存在（TEST_ONLY MON_STATS 数值表），建 battle/ 包会遮蔽它，
故用 battle_service/ 包名，并用 importlib 按文件路径加载旧 battle.py 重导出，
使 `from battle_service import MON_STATS, calc_damage` 等可用。
**数值逐字保留 TEST_ONLY，不做数值接线（Phase 5 的活）。**
"""
import os
import importlib.util

_BATTLE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'battle.py')
_spec = importlib.util.spec_from_file_location('battle', _BATTLE_PY)
_battle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_battle)

# 重导出 battle.py 的公开符号
MON_STATS = _battle.MON_STATS
calc_damage = _battle.calc_damage
