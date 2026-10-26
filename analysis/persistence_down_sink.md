# Persistence/Config 层整体下沉设计

> 目的：为深耦合族（12400/106xx/10204/20002）解耦铺路——先把 mock_server 的
> 共享助手按依赖层下沉到模块，每步 from-import 无损（同一函数对象、无循环 import）。

## 1. 依赖分层（自底向上）

| 层 | 助手 | 目标模块 | 依赖 |
|---|---|---|---|
| L0 核心原语 | log | core/runtime.py | （已落地）|
| L0 | w_u8/w_u16/w_u32/w_str/pack_frame/FrameParser | protocol/frame.py | （已落地）|
| L0 | db_conn/db_release/db_init | persistence/db.py | （已落地）|
| L1 DB 封装 | db_get_missions / db_save_mission / _MIS_COLS | task/service.py | db_conn, log |
| L1 | db_role_attr / attr_row_bytes | attribute/service.py | db_conn, w_* |
| L1 | db_get_assets / db_add_assets / db_set_assets | currency/service.py | db_conn |
| L2 业务读 | mission_rows / mission_chain / build_12400 | task/service.py | L1 + config |
| L2 | build_10301/2/3/4/6 | role/service.py | L1 |
| L3 命令 handler | 12400/106xx/10204/20002 | 各 handler.py | L1+L2 + self.request |

## 2. 下沉配方（沿用 db_get_missions 同款）
1. 叶子函数体逐字搬进目标模块（仅调整 import 来源）。
2. mock_server 旧 def 注释保留 `# [P3deep-migrated]`。
3. 顶部 `from <mod> import <fn>` 接线。
4. 验证：`mock_server.<fn> is <mod>.<fn> == True`（同一对象）+ py_compile + miniloop 145。

## 3. 迁移后注册计划（顺序 + 字节对比锚点）
1. **任务读簇**（L2 完成后）：注册 12400/12401；锚点=miniloop 已含 12400 帧规格。
2. **装备 106xx**（attr_row_bytes 下沉后）：注册 10601/10622；锚点=10304/10502 属性帧不变。
3. **移动 10204**（AOI 闭包下沉后）：注册 10204；锚点=移动后邻居推送帧。
4. **战斗 20002**（battle Timer 下沉后）：注册 20002 族；锚点=20002→20010→…→20023 帧序列。

## 4. 已完成（本批）
- db_get_missions → task/service.py（p3deep 第一步）
- db_save_mission + _MIS_COLS → task/service.py（本批）
- 叶子 db_conn/db_release/log/w_* 早已在 L0 模块。

## 5. 剩余步骤
- db_role_attr / attr_row_bytes → attribute/service.py
- db_get_assets/db_add_assets/db_set_assets → currency/service.py
- mission_rows/mission_chain → task/service.py（之后注册 12400）
- 106xx/AOI/20002 注册
