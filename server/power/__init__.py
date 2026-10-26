# -*- coding: utf-8 -*-
"""server/power 包初始化。

★ 坑：本包目录 power/ 与旧顶层模块 server/power.py 同名，会遮蔽后者。
  为保持 `import power`（mock_server、attribute.service）仍拿到**原版权重模块**，
  这里按文件路径显式加载 server/power.py，并把它的符号（calc_power 等）重导出。
"""

import os as _os
import importlib.util as _ilu

_LEGACY = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                        '..', 'power.py')
_spec = _ilu.spec_from_file_location('_legacy_power_mod', _LEGACY)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# 重导出原版权重符号
calc_power = _mod.calc_power
attr_power = _mod.attr_power
power_items = _mod.power_items
