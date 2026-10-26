# R49b：变强面板「右侧空白」修复 —— `SC_20100.promote` 真实化

> 承接 `docs/PLAN_下一阶段实施方案与校验设计.md` 的 **P0-1**。
> 真机基线（同一台 MuMu，`rid=1001 / DSH / lev=70`）：
> 面板显示「综合战力：133960」（正确）＋「70级推荐战力：0」＋**右侧主区域空白**。
> **时间**：2026-09-28 23:30 – 23:36。

---

## 一、取证：`SC_20100` 的三个字段到底喂给面板的哪个控件

反汇编 `assets/src/game/advance/advance_new_panel.luac`（`tools/dis_luac_file.py`），
proto#20（bc=90）逐条对应：

```lua
txt_2:setString(roleVo.lev .. '级推荐战力：')          -- 「N级推荐战力：」

if data.power and #data.power >= 1 and data.power[1].code == 1 then
    self.power_value:setString(data.power[1].val)      -- 综合战力
end
if data.power and #data.power >= 2 and data.power[2].code == 2 then
    self.tui_power:setString(data.power[2].val)        -- ★「N级推荐战力」的数值 = power[2].val
end
if data.power and #data.power >= 3 and data.power[3].code == 3 then
    ... getPingfen(data.power[3].val) ...              -- 评分图标
end

if data.promote and #data.promote > 0 then             -- ★ 右侧"我要变强"提升项列表
    self.one_data = data.promote
    self:createItem(1)                                  -- → proto#17 渲染
end
```

proto#17（bc=160，右侧列表渲染）关键三行：

```lua
cfg = Config.Promote[one.code]                          -- B=5['Promote'], B=4['code']
if cfg.display_lev <= GameData:getInstance():getRoleVo().lev then
    table.insert(self.item_list, Config.Promote_Catalog[...])
```

**⇒ 两条结论（都可由字节码复核）**：

| 现象 | 真因 |
|---|---|
| 「N级推荐战力：0」 | 数值取自 **`power[2].val`**（`code==2`），不是 `promote`；服务端该槽位恒发 0 |
| 右侧主区域**空白** | `promote` 原实现恒发**空表**（`out += w_u16(0)`，见改前 `mock_server.py:6648`） |

---

## 二、`promote` 的真实数据源（不编造）

| 项 | 值 |
|---|---|
| 配置表 | APK `assets/src/config/config_promote.luac` → `Config.Promote` |
| 结构 | 多个子表；`SC_20100.promote.code` 指向**第一子表**的行号 |
| 第一子表字段 | `button_id / display_lev / is_hide / way / content / icon / link / recommend` |
| 条数 | **19**（键 = 1..19，由构造器 `TSETB D=257,258,259,…` 连续序列确证） |
| 等级门槛字段 | `display_lev`（客户端自己按 `roleVo.lev` 过滤） |

前 6 条（真实原版数据）：

```
code=1  display_lev=30  装备强化   角色装备累计强化等级达到%s级
code=2  display_lev=35  镶嵌宝石   角色装备镶嵌%s颗%s级宝石
code=3  display_lev=50  装备炼神   角色%s件装备炼神品质为%s
code=4  display_lev=55  装备升星   角色%s件装备达到%s星
code=5  display_lev=20  装备等级   角色%s件装备等级升至%s级
code=6  display_lev=20  坐骑      坐骑阶数达到%s阶
```

新增提取器：`tools/extract_promote.py`（用 `tools/luajit_bc.py` 的 `Reader` 直读
`TableConst(hash=…)`；因 `pt.tables` 的遍历顺序与字节码 TDUP 顺序**相反**，需 reverse 一次
再编号 —— 该坑已写进脚本注释）。

产物：`server/_promote.json`（146 条记录 + 19 条 `tips`）。

---

## 三、实现

```python
# mock_server.py  if cmd == 20100
comps = [(1, power_total),   # 综合战力
         (2, 0),             # 推荐战力 —— ★ 无可得数据源，保持 0（见 §四）
         (3, 0)]             # 评分     —— 同上
...
_lev = role_state(self.cfg).get('lev')
_prom = [t for t in promote_tips() if t['display_lev'] <= _lev]
out += w_u16(len(_prom))
for t in _prom:
    out += w_u8(t['code']) + w_u16(0)      # val = 空子表
```

新增：`promote_tips()`（读 `server/_promote.json`）。

---

## 四、★ 如实记录的未闭环项：推荐战力**没有可得的原版数据源**

```
Config.RoleAttr（200 级）字段只有：
    exp_total / exp_max / attr_point / sinew_add / sinew_max
⇒ **不含任何战斗属性**（atk/hp/def 全无）
⇒ 逐级属性成长曲线、以及面板上的"推荐战力"设计师曲线，**不在客户端配置里**
```

⇒ 按红线"**不编造数据**"：`power[2]`（推荐战力）与 `power[3]`（评分）**保持 0**，
不做任何占位填充；面板上「70级推荐战力：0」是**当前唯一诚实的显示**。
若要显示它，必须先拿到原版曲线（另一渠道的 APK/服务端数据），届时只需改这一行。

---

## 五、真机复验

```
>> cmd=20100（登录后客户端自动请求）
<< 20100 SC_20100 power_total=133960 comps=3 promote=18 (79 bytes)   ← 18 = display_lev ≤ 70
```

真机截图 `shots/adv_r49.png`（点顶部「变强」）：

| 位置 | 改动前 | **改动后** |
|---|---|---|
| 综合战力 | 133960 ✅ | 133960 ✅ |
| 70级推荐战力 | **0** | **0**（同 §四，无数据源） |
| **右侧主区域** | **空白** | ✅ **列出提升项：职业技能全部提升到60级(6/6) 等，带「展开」按钮** |

---

## 六、全量验证（改动后当场复跑）

| 项目 | 结果 |
|---|---|
| `py_compile` | OK |
| `lint_dispatch_shadow.py` | 专用 165 / 默认 63 / 未开放 24 ⇒ **0 遮蔽** |
| `audit_specs_vs_fields.py` | 2463 一致 / **0 不一致** |
| `audit_sc_conformance.py --generic --unsupported` | 87 命令：一致 86 / **0 不一致** |
| `audit_sc_live.py --unsupported` | **87/87 全一致** |
| `audit_dedicated.py` | 62/62 符合规格（含 20100） |

---

## 七、产出物

| 文件 | 说明 |
|---|---|
| `tools/extract_promote.py` | 新增：`Config.Promote` 提取器（含顺序坑注释） |
| `server/_promote.json` | 新增产物：146 条记录 + 19 条 `tips`（带 `code`） |
| `server/mock_server.py` | `promote_tips()`；`20100` 的 `promote` 由空表改为真实列表；三槽位语义注释实证 |
| `analysis/_advance_panel_dis.txt` | 面板反汇编（proto#17 / proto#20 为真源） |
| `analysis/_config_promote_dis.txt` | `Config.Promote` 全表反汇编 |
| `shots/adv_r49.png` | 修复后的真机面板截图 |
| `analysis/1.4.9/round49b_20100_promote.md` | 本报告 |

---

## 八、下一步（P0 剩余）

| # | 任务 | 状态 |
|---|---|---|
| P0-2 | 5 条"未开放"命令（`17501`×6 / `17312`×3 / `18600`×3 / `11400`×3 / `17301`×1）诚实化分诊；`17301` 竞速有真实可比字段，可仿 R47 竞技场建 `race_state` | 待做 |
| P0-3 | 32 条"通用零值"中最热的 `16602`（节日列表，`config_fest_data` 在手）、`19400`（铭格，`config_mingge` 在手） | 待做 |
| — | 「推荐战力」需先取得原版曲线（**外部依赖**，非编码问题） | 阻塞 |
