# S3-A 服务端加固与资产收敛 · 实施报告

> 阶段：PHASE S3 第一实施分片
> 日期：2026-10-15（周四）
> 范围：承接 C3.1 优先项 G1-G6/T1-T2 中**服务端可改项**；独占 mock_server；改前备份；最小改动；不做实机验证（留 S3-B）。
> 运行环境：本机 PowerShell 5.1；python=`...sandbox_runtime\...\python.exe`；活跃 DB=`server\state\roles.db`。

---

## §0 备份链

| 文件 | 备份目标 | 字节数 |
|---|---|---|
| server/mock_server.py | server/mock_server.py.bak_s3_20261015 | 1098472（源==备份） |
| server/gm/service.py | server/gm/service.py.bak_s3_20261015 | 2472 |
| server/currency/service.py | server/currency/service.py.bak_s3_20261015 | 2301 |
| server/reward/service.py | server/reward/service.py.bak_s3_20261015 | 2977 |
| server/role/storage.py | server/role/storage.py.bak_s3_20261015 | 11879 |
| server/mall/service.py | server/mall/service.py.bak_s3_20261015 | 1655 |
| server/mail/service.py | server/mail/service.py.bak_s3_20261015 | 2604 |

> 注：role/storage.py 备份命名首轮误写为 role/service.py.bak_s3_*，已删除并更正为 storage.py.bak_s3_20261015。
> 历史备份链 .bak_20261015_1908 → .bak_s1b → .bak_s2 保留未动。

---

## §1 任务1：diamond/gold 双路收敛到 role_assets

### 取证
- 权威模型（docs/C3.1_统一数据模型说明.md §1.2）：货币类权威在 **role_assets**；`role_state()` 合并顺序 ROLE_DEFAULTS ← cfg.role ← roles 行 ← role_assets（后者覆盖）。
- 写 roles.gold/diamond 的唯一路径 = `_sc_to_db_updates()`（含 gold/gold_acc/coin/diamond），被三处调用：
  - role_state() 建号种子（role/storage.py:143 / mock_server.py:5440）
  - add_role_exp 加经验（mock_server.py:6182）
  - 升级（level/service.py:110）
- DB 实测漂移（改前）：roles.gold=1800140 vs role_assets.gold=1800041（差99）；roles.diamond=0 vs role_assets.diamond=100000；coin/exp 双写同步；gold_acc 仅 roles（=5000，无 assets 行）。
- Grep 确认：线上（非 backup/）无任何旁路直读 roles.gold/diamond、无直写 `UPDATE roles SET gold/diamond`。

### 决策（最小改动）
- **role_assets 唯一权威**；roles.gold / roles.diamond **停写**（从 `_sc_to_db_updates` 删除这两键）。
- 保留 exp/coin 双写（已同步，add_role_exp L6182 注释明确要求）；保留 gold_acc（无 assets 行、仅 roles 列、本就无人更新）。
- 存量漂移**不迁移 rid=1001 数据**（纪律）：停写后 roles.gold=1800140/diamond=0 保持 stale，但读取永远被 role_assets 覆盖，UI/HUD 不受影响。一次性迁移脚本（`UPDATE roles SET gold=(SELECT amount FROM role_assets...), diamond=...`）仅作草案记录，不执行。

### 改动
- `role/storage.py` `_sc_to_db_updates`：删 `'gold'`、`'diamond'` 两键（现 L128-130 保留 exp/gold_acc/coin）。
- `mock_server.py` 本地副本 `_sc_to_db_updates`：同步删除（现 L5434-5445）。

### 验证（服务端级）
- py_compile 两文件 OK。
- 重启（PID 30440）后 status：assets.gold=1800041 / assets.diamond=100000（权威，未变）；role.gold=1800140/diamond=0（stale，符合"不迁移"预期）。
- Grep 线上代码：无残留 `'gold': st.get` / `'diamond': st.get` 写点（仅 backup/ 旧快照与独立 minloop/min_loop_server.py:278——后者用独立 minloop.db，不在范围）。

### 遗留
- roles.gold/diamond 列物理上仍存（stale）。彻底清理需一次性迁移脚本（草案，待批准）。
- minloop 独立服务仍写 roles.gold，但其 DB 独立，不污染主库。

---

## §2 任务2：setassets 校验 + admin 审计补齐

### ① setassets 负数校验
- **位置**：mock_server.py setassets 路由，`if not vals:` 之后（现 L1738-1745）。
- **改动**：遍历 vals，任一 `<0` 即返回 400 `'%s must be >= 0'`。
- **验证**：`GET /DSH_ADMIN/setassets?rid=1001&gold=-100` → **HTTP 400**；getassets gold 仍=1800041（未落库）。
- 对齐 setlevel(1..200)、setdiamond(>=0) 模式。

### ② admin 审计补齐（集中挂钩）
- **位置**：do_GET `/DSH_ADMIN/` 入口，`rid=` 解析后单点插入（现 L791-809）。
- **机制**：`_ADMIN_READONLY`（19 条只读命令跳过）+ `_ADMIN_AUDITED_TRIO`（setlevel/setassets/setdiamond 已自审计跳过）；其余写命令执行前调 `gm.service.log_gm(act, rid, 'params=%r ref=gm:<act>:<rid>:<ts>')`。
- **验证**：触发 `additem?bid=0`（被拒），gm.log 新增末行：
  `[2026-10-15 23:44:38] additem rid=1001 params={'bid': ['0'], 'n': ['1']} ref=gm:additem:1001:1792079078` ✅

### admin 命令清单审计结果（73 条）

| 类别 | 命令 | 路径 | 审计 | 改动 |
|---|---|---|---|---|
| 已 Service+自审计 | setlevel / setassets / setdiamond | gm.service | ✅原已有 | setassets 加负数校验 |
| 走业务 Service | setcharge→growth_target.service | Service | 经新挂钩补 | 挂钩覆盖 |
| 只读（不审计） | battle_replay, getlevel, getassets, status, listitems, cfglist, cfg, reward_log, mall_list, afk_status, mail_list, ach_list, ach_progress, skill_show, partner_show, dungeon_list, rank_breakdown, aoi, power | SELECT/重放 | n/a | 加入只读白名单 |
| 写 DB（新挂钩补审计） | daily, chengjiu, ach_done, ach_claim, guaji, addbag, mail, marketgoods, build, tree, fabao, bosskill, title, lingshou, yuanshen, shenqi, mingge, chair, wing, invest, ride, qifu, exp, hero, buff, partner_feed, skill_learn, skill_up, wing_up, shenqi_up, mingge_activate, dungeon_clear, afk_enter, afk_claim, mall_buy, sign_do, mail_send, mail_claim, drop_test, giveitem, givegift, setequip, unequip, setheros, setjubaopen, setmissions, reset, reload, additem | 直调 db_*/业务 service | ✅新挂钩 | 单点挂钩覆盖，未逐条改内部路径 |
| 纯推送无写库 | guaji_end | push | 挂钩补（无害） | — |

- **"可低成本改走统一 Service"说明**：货币类写命令（exp/mall_buy/afk_claim）内部已多走 db_add_assets 或 reward.grant；逐条改写内部调用路径属重构（超出"最小改动"纪律），本轮以"集中审计挂钩"补齐可追溯性（G3 核心诉求=事后可追溯谁发了什么），内部路径收敛留待后续。

### 遗留
- 审计字段为 params（含新值）+ref，未做 old/new 前后快照（直写 DB 命令需预读，代价大）。
- HTTP /DSH_ADMIN 仍无 token/IP 鉴权（绑机私服可接受，G10 范围外）。

---

## §3 任务3：发奖幂等统一到 reward.grant

### 取证
- reward/service.py:51 `grant(rid, awards, reference_id)` 以 `(rid, reference_id)` 为 reward_log 主键幂等。
- 现状（Grep 线上）：shop(L4504, ref=shop:gid:rid:seq)、击杀(L9928, ref=kill:mon:rid)、任务提交(L16729, ref=task:bid:rid)、礼包开启(L17899, ref=gift-open:bid:item)、挂机击杀(L18928, ref=guaji_kill:rid:kill_count)、邮件领取(mail/service.py:61, ref=mail:mid:rid) **均已带幂等键**。

### 改动
- **唯一缺口**：击杀块中 `mission_progress_advance` 原本无条件执行（与已幂等的击杀奖励并行）。
- **位置**：mock_server.py 现 L9928/L9937-9945。
- **改法**：`_kill_gr = grant(...)`；`if not _kill_gr.get('already'):` 才推进 mission_progress_advance + 12405 推送。
- **效果**：同一 mon 重复结算时，奖励被 reward_log 拦截、进度同步跳过，消除"奖励不重复、进度 +N"不一致。

### 验证
- py_compile OK。实机战斗验证留 S3-B（本轮不实机）。

### 遗留
- addbag/additem（GM）故意不挂幂等：属运营主动发放，重复执行=重复发道具（期望行为），已由任务2审计挂钩记录。
- 掉落 db_bag_add（L9972）按概率独立 roll，不挂幂等（每杀应独立掉落）。

---

## §4 任务4：商城💎=gold 映射 —— 决策=接受现状（不实施）

### 取证
- `ASSETS_EN_TO_CODE`（mock_server.py:2045，已与客户端 config_game_data.luac 逐项核对）：`gold=1, coin=2, coupon=3…`，**表中无 diamond 码**。
- 客户端 `payTypeEnToCode(pay_type)=Config.AssetsEnToCode[pay_type] or 1` ⇒ 显示币种与扣款币种**同源同值**，天然一致。
- mall_config.json 全部商品（2001-2020… 共 2000+）均 `pay_type=1` → gold。
- 实机观测（C2.1 基础界面恢复清单 L96 / C2.3 实施记录 L89）：商城"拥有"栏=**1800140=gold**；购买扣 role_assets.gold（S2-B）。
- shop_try_buy（mock_server.py:4467-4472）：`have=st.get(pay)` 读合并后 role_assets 值，`db_set_assets(rid,{pay:have-total})`，与客户端同源。

### 决策
**接受现状：本商城即"金币(gold)商城"，💎图标仅为该商城页签视觉，实际币种由 pay_type=1 驱动=gold。**

### 理由
1. 客户端"拥有"显示与扣款**已经一致**（都=gold），不存在"显示 A 扣 B"的真错位；
2. ASSETS_EN_TO_CODE 无 diamond 码，无法把 pay_type 切到 diamond 而不破坏客户端显示；
3. 若强行改服务端扣 diamond：客户端仍按 pay_type 显示 gold 余额(1.8M)，却扣 diamond(10万)，会制造新的"余额充足却购买失败"错位；
4. 改 2000+ 商品 pay_type 代价大、回归面广，违背最小改动。

### 验证（服务端级）
- 接受现状即"购买扣 gold"为正确行为。重启后未做实际购买（避免动 rid=1001 数据）；shop_try_buy 代码路径未改，扣减目标=role_assets.gold，与客户端显示一致。实机购买验证留 S3-B。

### 遗留
- 若未来要做真正的钻石商城，需先取证客户端 diamond 的 pay_type 码并新增商品配置，不在本分片。

---

## §5 任务5：面板首帧0 —— 客户端方案（文档，不实施）

- 交付：`docs_raw/s3_panel_fix_proposal.md`。
- **要点**：根因=客户端面板 setData 一次性快照(proto#10) + 活刷新门控 `role_vo.bid==event.bid` 对自我角色恒不通过(proto#15)；服务端已无新帧可发（10303/10306 都带正确 power）。
- **推荐方案 A**：放宽自我面板的活刷新 bid 门控（display_panel.luac proto#15 一行：is_role 时不要求 bid 相等，直接刷新 power_value）。风险低、回归面小。
- 备选 B（延后 openView 到 power 就绪，风险中）/ C（setData 改订阅，过度）/ D（服务端提前补推，不根治）。
- 前置 UNKNOWN：U1（预入场 10303 是否写进 vo）、U2（10306 事件名是否=HERO_ATTR_CHANGE）。
- **本阶段不实施客户端修改**，待批准 + S3-B 补证。

---

## §6 自检记录
- [x] 任务0 备份链完整（7 文件，字节数核对）
- [x] 每项 py_compile 通过
- [x] 任务1-3 服务端级验证：重启(PID 30440)→status 正常→setassets 负数 400→additem 审计落 gm.log→Grep 无残留写
- [x] 任务4 决策带证据、不改代码
- [x] 任务5 仅文档
- [x] 未碰 rid=1001 数据（漂移仅记录不迁移）
- [x] 所有结论带 文件+行号
