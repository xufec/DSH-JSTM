# -*- coding: utf-8 -*-
"""partner 包 —— 伙伴（神将）面板 + 培养闭环（Phase 8）。

禁止 `import mock_server`（循环 import）。数据源：
  · 面板标量（53 伙伴 name/score/color/is_deity/innate_skill）← `server/_partner_base.json`
    （= config_partner_base.luac 提取的 53 条，CONFIRMED，且为实机验证过的上屏顺序）。
  · 成长曲线（每级 exp_max / lev_max）← `server/cfg/config_partner_base.json` 的
    PartnerLevUp / PartnerConstant（CONFIRMED）。
  · 已拥有实例态 ← `role_heros` 表（bid/color/lev/exp/state/chip）。
"""
