# S1-B 第二实施分片报告（技能 bid 键错位 / 钻石资产推送 / 伙伴 10999 解析修复）

- 执行时间：2026-10-15 20:01–20:24
- 设备：emulator-5554（2560×1440 横屏），客户端 com.shiyue.dldl.ewan.baidu2（1.4.9，原包不动）
- 基线：power=724112 / gold=1800140 / level=70 / coin≈9907209 / scene=10001 / exp=14389（rid=1001）
- 增量快照：`server\mock_server.py.bak_s1b_20261015`（1,091,180 bytes，本分片开始前）
- 原始备份：`server\mock_server.py.bak_20261015_1908`（S1-A 前）
- 重启：`tools\restart_server.ps1`（PID 40572 @20:13:08）

---

## 项3：技能 10621 bid 键错位（C2.2 遗留）✅ 实机验证通过

**定位**
- 10621 handler：mock_server.py L16190。原读 `cfg['skills']`=[{bid:10000,exp:0},{bid:10001,exp:0},{bid:10002,exp:0},{bid:10822,exp:35}]。
- 客户端打开技能面板发 CS_10621(body 4B)+CS_10650，不发 10622。
- 证据链：`analysis/extraction/lua_injection_channel_round.md` §2.1 —— 客户端拿 10621.skill_list 的 bid 去查 `Config.SkillXiulianLev`；合法键 = `server/cfg/config_skill_xiulian.json` 的 SkillXiulianLearn 8 键：**10101 攻击修炼 / 10201 物防 / 10301 法防 / 10401 伙伴攻法 / 10501 伙伴物防 / 10601 伙伴法防 / 10701 控制 / 10801 抗控**。原 10000/10001/10002/10822 全不在该键空间。

**改动**（mock_server.py L16190 起）
- 改为从 `cfg/config_skill_xiulian.json` 读 8 个修炼 bid 排序后下发；exp 取角色真实 `practice_exp`=35，仅映射到 10801（历史抗控修炼进度），其余 7 项 DB 无 per-skill 数据源 ⇒ exp=0（如实标注，不伪造）。
- 第一次尝试（改读 role_skills 表 bid=10020「破灭杀一阶」）→ 左列表仍空（客户端不在 talent 键空间查 10621）；第二次（发 8 个 xiulian bid）→ 成功。

**验证**
- 重启→重连→打开魂技面板→切「修炼」tab：左列表**非空**，显示 攻击修炼 1/4、物防修炼 1/4、法防修炼 1/4、控制修炼 1/4、伙伴攻法 1/4（名称+等级+效果描述）。
- 截图：`s1_shots/20_skill_xiulian_tab2.png`、`20_skill_list_populated.png`。
- logcat 无 10621/Lua 报错；关闭重开一致。

**遗留**：面板默认「技能」tab（天赋/符文列表）左列表仍空 —— 它由 CS_10650 talent_list=0 驱动，不在 10621 范围。记入未完成项。

---

## 项4：钻石资产推送（C2.3 HUD 钻石=0）✅ 实机验证通过

**定位**
- `build_10302()`（mock_server.py L5413）尾部在 1.4.11 版本下已追加 `diamond:I`+`rainbow_diamond:I`（L5446-5448）；`_DB_TO_SC`（L5321）已映射 `'diamond':'diamond'`，roles 表 diamond 列=0。
- **根因**：登录风暴只推 10301/10303/10305，**从不推 10302**；10302 仅在战斗结算（L9876）或 admin 热改（L516）时发。而 diamond 字段只在 10302 尾部 ⇒ 客户端登录后读不到 diamond。
- `config_game_data.CodeToAssets` 共 41 项，**无 diamond 标签**（label 1=gold…40=rune_chip），故 diamond 不能走 10305 增量表，只能走 10302 尾部。

**改动**（mock_server.py L9952 起，S1-A +5s 补推块内、10303 推送之后）
- 追加 `_pk2 = pack_frame(10302, build_10302(_st))` 并 sendall，日志 `<< 10302 SC_10302 资产刷新（S1-B 补 diamond=%s）`。
- 值取 `role_state['diamond']` = roles.diamond 真实存储 = **0**（不伪造非零值）。

**验证**
- tcp.log @20:07:05：`<< 10302 SC_10302 资产刷新（S1-B 补 diamond=0）(128 bytes)`；同时客户端主动 `>> cmd=10302` → `<< 10302 ... (128 bytes)`。
- 回归：同帧日志 `10306 ... power=724112`、`10303 ... gold=1800140` —— 战力/金币未回退。
- 截图：`s1_shots/21_diamond_hud.png`（HUD power=724112）。

**钻石真实来源结论**：roles.diamond=0 是真实存储值，已结构补推到 10302。客户端 HUD 钻石读 0（真实值）；商城购买仍因 0<99 失败 —— 这是**真实资产态，非 bug**。不伪造钻石。

---

## 项5：伙伴 10999/11215 LUA 解析修复（C2.3 新发现）✅ 实机验证通过

**定位**
- 客户端打开伙伴列表 → CS_11215 → 服务端发 SC_11215（partner.service.build_panel_11215）→ 客户端解析失败 → 经 CS_10999{msg:string} 上报 `[11215]解析...`。
- 修复前 tcp.log：`<< 11215 ... (2554 bytes)`，随后 `>> cmd=10999 body(448)=01 ba 2d...`（20:06:57、20:08:05 各一次）。
- `protocol/fields.json`（1.4.9 权威）`SC_11215` = **`partner_list:table` 直接以表计数(u16)开头，无 volume/volume_open 前缀**。
- partner/service.py build_panel_11215 旧实现按 1.4.11 luac 格式（`volume__C##volume_open__C##partner_bag__T`）补了 `w_u8(volume)+w_u8(volume_open)` 两字节前缀 ⇒ 1.4.9 客户端把这两字节并进表计数、后续每个条目错位 2 字节 ⇒ 解析越界 ⇒ LUA ERROR [11215]。
- 帧长印证：注释基线 2552 body = 2 + 53×48；旧码发 2554（多 2 字节前缀）即此错位。

**改动**（partner/service.py build_panel_11215 L148 起）
- 去掉 `w_u8(volume)+w_u8(volume_open)` 两字节前缀，只发 `w_u16(len(base))` 表计数，与 fields.json 1.4.9 规格对齐。
- per-entry 结构（id/bid/type/color/lifttime/lev/exp/grow/score/stage/rebirth/acc/partner_attr/power/aptitude/innate_skill/skill/jindan/talisman/ext）与 fields.json 一致，未动。

**验证**
- tcp.log @20:13:09：`<< 11215 SC_11215 partner_list=53（partner.service 配置驱动）(2552 bytes)`（原 2554）。
- 打开伙伴面板（底排伙伴按钮）：面板**完整渲染** —— 普通/特殊 tab、左侧 53 伙伴头像格（肉/法/物/辅职业标签 + 等级 1–55）、中央「法 巫风」详情（仙品、携带等级 1、物攻资质 1010–1550、技能 火龙吐息/火柱/保命）、右 rail 综合/洗髓/阵型/图鉴。
- **修复后零 10999 错误上报**（修复前 2 次）；logcat 无 `lua error / stack traceback / 11215`。
- 截图：`s1_shots/22_partner_try.png`（面板渲染成功）、`22_regression_hud.png`（关闭后回 HUD，power=724112）。

---

## 累计改动清单（mock_server.py 共 4 处 + partner/service.py 1 处）

| # | 文件:行 | 内容 |
|---|---|---|
| S1-A-1 | mock_server.py 10300 handler 末尾 | 排程 `_login_repush_at = now+5.0` |
| S1-A-2 | mock_server.py 1199 心跳 L9941 | 到期补推 10303/10306/13781/13786 |
| S1-B-1 | mock_server.py L9952 起 | 补推块追加 10302（带 diamond=0） |
| S1-B-2 | mock_server.py L16190 起 | 10621 改发 8 个 xiulian bid |
| S1-B-3 | partner/service.py L148 起 | 11215 去掉 volume/volume_open 2 字节前缀 |

## 回归结论
- power=724112 / gold=1800140 / level=70 —— 均未回退（tcp.log 同帧日志 + HUD 截图）。
- 锻造、魂技、伙伴等面板切换正常，无新增 Lua 报错。

## 未完成项（事实陈述）
1. **技能「技能」tab（默认）左列表仍空**：由 CS_10650 talent_list=0 驱动，不在 10621 范围；需另立项处理 10650 天赋列表。
2. **钻石真实来源**：roles.diamond=0 为真实存储，已结构补推；客户端 HUD 钻石显示 0（真实值），商城购买仍因 0<99 失败 —— 真实资产态，非缺陷，未伪造。
3. **1.4.11 前缀差异**：本次按 1.4.9 fields.json 去掉 volume/volume_open；若将来接 1.4.11 客户端，11215 需版本分流（保留前缀），已在代码注释标注。
4. 技能 exp：仅 10801 有真实 practice_exp=35，其余 7 项 DB 无 per-skill 数据源，exp=0 如实标注。
