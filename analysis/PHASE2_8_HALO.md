# PHASE 2.8 —— 光环（19100/19103/19104）状态与装备位实现

> 此前 `19100` 走 R187 默认生成（**全零**）、`19103/19104` 走 R181 回执族 ⇒ 光环阶数/幸运/装备位**从不落库**。

## 一、取值前的取证（避免照抄巨型 SC 而不解其义）

- 反汇编 1.4.11 客户端 `game/halo/*`（11 模块，本次提取到 `_tmp_halo/`）；
- `halo_model.luac` 的 `haloData` **只读 `stage` / `luck` / `grow`**；
  `next_stage` / `max_luck` / `need_coin` / `item_bid` 等一律走 **`Config.Halo`（客户端配置）**
  ⇒ 服务端**不需要**下发这些。
- ⇒ `SC_19100` 虽体量巨大（含 5 层嵌套子表），但**服务端真正要给的只有状态 + 装备位**。

## 二、实现（server/mock_server.py）

| cmd | 语义 | 行为 |
|---|---|---|
| 19100 | 光环信息 | `{stage,power,luck,res_stage,grow}` 取自 `role_halo`；`items` 用**既有通用编码器** `bag_items_bytes(19100,'items',...)` 逐字段编码光环装备位；`skill_list/looks/surface_star` **无数据 ⇒ 空表** |
| 19103 | 光环装备穿戴 `CS{item_id}` | **校验该 item_id 真在背包**（`db_bag_item`）→ 落库 `role_halo_equip`；不存在 ⇒ `code=0`「背包中没有该物品」 |
| 19104 | 卸下 `CS{item_id}` | 删装备位 |

新增 `role_halo(rid,stage,luck,res_stage,grow,power)` + `role_halo_equip(rid,item_id,bid,pos,ctime)`；
从 R187/R181 集合移出 `19100/19103/19104`，并清理**因此变成死代码的** `elif cmd in (19103,19104,...)` 分支。

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_halo.py --port 9191        →  ALL PASS（11 项）
```

```
19100 初始 stage=0 items=0
19103 item_id=999999（不在背包）→ code=0「背包中没有该物品」
19103 item_id=308（真实背包物品 bid=28514）→ code=1，DB 记录 (308,28514)
19100 items=1（装备位被真实编码进 SC）
19104 → code=1，DB 清空；19100 items=0
```

**回归全绿（8 套）**：team / jiebai / jiebai_multi / marry / marry_propose / multi_session / fashion / halo。
**门禁**：`lint_dispatch_shadow` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。
**清理**：8 张新表均 **0 行**；`bag_items(1001)` 仍为 6 行（未动）。

## 四、诚实边界

| 项 | 状态 |
|---|---|
| 光环**升阶**（19101/19102）、`res_stage`/`grow` 的增长逻辑 | 未实现（`config_halo` 有 `up_exp/sum_exp/self_exp`；**不编造概率/消耗语义**） |
| 19120/19199 等 | 仍通用回执 |
| 光环**属性/战力贡献** | **未接**（与时装同样，待统一 Attribute/Power 汇总） |
| `skill_list`/`looks`/`surface_star` | 无数据源 ⇒ **空表**（不编造） |

## 五、下一步

**拍卖 18020/18021** → 然后做**统一属性/战力汇总**（把时装 + 光环 + 翅膀 + 命格等成长
汇入 `role_attr` / `role_power_of`），这是本项目架构目标里最关键的一环。

## 六、★ 本轮暴露的一个共同缺口（必须记住）

时装（2.7）与光环（2.8）都只做到**状态落库**，**尚未影响属性/战力**。
若不做统一汇总，这些系统的"成长"在客户端战力面板上看不出来
⇒ 下一阶段应优先补 `AttributeService`/`PowerService` 的汇总入口。

[PHASE 2.8 光环完成]