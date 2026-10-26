# -*- coding: utf-8 -*-
"""server.growth —— 成长族模块（Phase 2e 迁移目标）。

迁移范围（设计文档第 8 步）：wing 翅膀 / ride 坐骑 / lingshou 魂兽 /
yuanshen 元神 / fabao 法宝 / mingge 命格 / shenqi 神器 / fashion 时装 /
halo 光环 / chair 椅子 / enhancement 强化 / soulbone 魂骨。

[P2E 裁剪说明]
  本族 db_* 读写函数（db_fabao_*/db_mingge_*/db_shenqi_*/db_wing_*/...）与对应
  命令段（188xx/189xx/190xx/191xx/194xx/213xx，数十个）目前**深耦合在
  mock_server.py**（依赖 role_state / encode_* / w_u8 / pack_frame 等模块级助手，
  且写路径强化/进阶消耗逻辑内嵌）。按 Phase 2 裁剪约定（共享 if 块 / 深闭包留旧链），
  本轮**不搬家、不注册**，db 函数与命令段保留在 mock_server.py 旧链原样运行。
  本包先建骨架；soulbone 本体 UNKNOWN（只占位）。后续 Phase 6 逐族解耦 db 函数后
  再搬。
"""
