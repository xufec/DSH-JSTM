# GM 动作 → 服务链路映射表（Phase 13，§36）

原则：GM 修改走正式 Service 链路，禁止散落直改业务表；所有 GM 动作写 logs/gm.log。

## 服务化改造项（本轮）
| 动作 | 改造前 | 改造后链路 |
|---|---|---|
| setlevel | 裸 SQL UPDATE roles | gm.service.set_level(rid,lev) 权威落库 → live_push(10302/10301/10303) |
| setgold/setcoin(=setassets) | db_add_assets 直调 | gm.service.set_assets(rid,vals,mode) → currency.service.db_add_assets + gm.log |
| giveitem | grant（P45-B）| 保留 grant，ref 幂等 |

## 动作盘点（do_GET /DSH_ADMIN，共约 60 个，含 P8-P12 新增）
### 只读/状态（无副作用，保留）
getlevel, daily, chengjiu, aoi, cfglist, cfg, reward_log, partner_show, skill_show,
dungeon_list, afk_status, mall_list, mail_list, rank_breakdown, status, getassets, listitems,
power, tree, marketgoods, bosskill(只读推送类)

### 经服务闭环（P8-P12 已建）
partner_feed, skill_learn, skill_up, wing_up, shenqi_up, mingge_activate,
dungeon_clear, afk_enter, afk_claim, mall_buy, sign_do, mail_send, mail_claim

### 服务化改造（P13）
setlevel, setassets(setgold/setcoin), additem(经 db_bag_add+推送)

### 占位/诊断（保留，文档标注）
build, fabao, title, lingshou, yuanshen, shenqi(旧), mingge(旧), chair, invest, ride,
qifu, exp, hero, buff, setequip, unequip, setheros, setjubaopen, setmissions,
reset, reload, guaji, guaji_end, mail(旧), givegift

## 审计
- logs/gm.log：每条 GM 动作含 ts/action/rid/参数/ref=gm:<action>:<rid>:<ts>。
- 已验证：setlevel 70→71→70 两条记录落库，等级/资产基线恢复。

## 待办（未强制实机推送时）
- 实机 TCP 复建后 setlevel 推送帧(10302/10301/10303)客户端 UI 实时可见；
  本轮客户端未在线（ESTABLISHED=0），程序化验证链路正确、pushed 计数正常。
