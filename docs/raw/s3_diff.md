# S3-A diff 记录（文件/原行/新行/行号/原因）

> 日期：2026-10-15
> 备份基线：mock_server.py.bak_s3_20261015（1098472B）；role/storage.py.bak_s3_20261015（11879B）
> 纪律：最小改动；不重构；不改客户端；不碰 rid=1001 数据。

---

## 任务1：diamond/gold 双路收敛到 role_assets

### 文件 A：server/role/storage.py
- **位置**：`_sc_to_db_updates()` 原 L113-132
- **原行**：
  ```python
      return {
          'name': st.get('name', ''),
          'level': st.get('lev', 1),
          'career': st.get('career', 1),
          'sex': st.get('sex', 0),
          'exp': st.get('exp', 0),
          'gold': st.get('gold', 0),        # ← 删除
          'gold_acc': st.get('gold_acc', 0),
          'coin': st.get('coin', 0),
          'diamond': st.get('diamond', 0),   # ← 删除
          'scene_id': st.get('scene_id', 10001),
  ```
- **新行**（现 L115-130）：删除 `'gold'` 与 `'diamond'` 两个键；保留 exp/gold_acc/coin；函数 docstring 加 S3-A 收敛说明（L116-121）。
- **原因**：gold/diamond 权威已在 role_assets（role_state L151 合并时覆盖 roles 同名列）；原 _sc_to_db_updates 每次建号/加经验/升级都把（已漂移的）roles.gold/diamond 写回，是漂移源。停写后 roles.gold/diamond 不再被刷新，读取仍由 role_assets 覆盖兜底。

### 文件 B：server/mock_server.py
- **位置**：本地副本 `_sc_to_db_updates()` 原 L5404-5423（被 L62 import 后又本地重定义遮蔽）
- **原行/新行**：与文件 A 同步删除 `'gold'`、`'diamond'` 两键；docstring 加 S3-A 说明（现 L5434-5438）。
- **原因**：同文件 A；mock_server.py 本地副本是运行时实际命中的版本（add_role_exp L6182 调它）。

---

## 任务2：setassets 校验 + admin 审计

### 文件：server/mock_server.py
1. **setassets 负数校验**（现 L1738-1745，原 L1718 `if not vals:` 之后插入）
   - **新增**：
     ```python
     for _k, _v in vals.items():
         if _v < 0:
             return self._send(400, json.dumps(
                 {'ok': False,
                  'error': '%s must be >= 0 (got %d)' % (_k, _v)}, ...))
     ```
   - **原因**：G1——原 setassets gold=-100 直接落库；对齐 setlevel(1..200)/setdiamond(>=0)。
2. **admin 写命令统一审计挂钩**（现 L791-809，紧跟 `rid = int(...)` L790 之后）
   - **新增**：`_ADMIN_READONLY` 集合（19 条只读命令）+ `_ADMIN_AUDITED_TRIO`（setlevel/setassets/setdiamond 已自审计）；其余写命令在执行前调 `gm.service.log_gm(act, rid, 'params=%r ref=gm:<act>:<rid>:<ts>')`。
   - **原因**：G3——20+ 直写 DB 命令无 gm.log；单点插入覆盖全部写命令，零行为改动，避免逐条改。

---

## 任务3：发奖幂等统一到 reward.grant

### 文件：server/mock_server.py
- **位置**：击杀结算块 现 L9925-9945（原 L9925-9944）
- **原行**：
  ```python
  grant(rid, _awards, reference_id='kill:%d:%d' % (mon_bid, rid), source='battle')
  ...
  prog = mission_progress_advance(rid, 'fight_mon', mon_bid, 1)
  if prog: ...
  ```
- **新行**：`_kill_gr = grant(...)`（L9928）；`if not _kill_gr.get('already'):` 门控 `mission_progress_advance` 与 12405 推送（L9940）。
- **原因**：G4——击杀奖励已幂等（ref=kill:mon:rid），但紧随其后的 mission_progress_advance 无门控，重放会出现"奖励不重复、进度却 +N"。用同一 reward_log 记录做门控，奖励与进度一致。
- **未改**：mail.claim 已走 grant(ref=mail:mid:rid)；shop/task/gift-open/guaji_kill 均已带 reference_id；addbag/additem 是 GM 主动发道具（非请求重放路径），故意不挂幂等（否则无法连续发同类道具）。

---

## 任务4：商城💎=gold 映射

- **决策=接受现状，不实施代码改动。** 无 diff。理由见 s3_a_report.md 任务4。

---

## 任务5：面板首帧0

- **仅文档**：docs_raw/s3_panel_fix_proposal.md。无代码 diff。

---

## 校验
- [x] `python -m py_compile role/storage.py` OK
- [x] `python -m py_compile mock_server.py` OK
