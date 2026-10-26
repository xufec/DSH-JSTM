# -*- coding: utf-8 -*-
"""mall 包 —— 商城配置读取（Phase 11）。

禁止 `import mock_server`。
数据源：cfg/config_mall.json —— MallGoods(110)/MallWeek(24)/MallXian(45) CONFIRMED。
购买闭环已在旧链 `shop_try_buy`（选币→限购→扣费→grant 发货→记限购）；
本模块提供**配置驱动的只读列表**，购买专项验证经 GM 端点驱动既有 shop_try_buy。
"""
