# PHASE 1 状态 — MuMu 联调环境 + 运行时取证（2026-10-02 更新）

## 里程碑：1.4.11 实机联调跑通（E1–E4 环境搭建完成）

| 项 | 状态 | 证据 |
|---|---|---|
| E1 安装 1.4.11 补丁包 | ✅ 完成 | `adb install -r patched\jstm_1411_fakelogin_aligned.apk` → Success；包 `com.shiyue.dldl.ewan.baidu2`（launcher: org.cocos2dx.lua.AppActivity） |
| E2 URL 指向 mock_server | ✅ 完成 | 补丁包 config.luac 注入 URL_PATH_ALL → 10.0.2.2:8080；TCP 连 10.0.2.2:9000 |
| E3 启动客户端 | ✅ 完成 | `am start -n com.shiyue.dldl.ewan.baidu2/org.cocos2dx.lua.AppActivity`；绕过 Android 12 权限审查（pm grant + tap 继续） |
| E4 抓包链路 | ✅ 运行中 | mock_server tcp.log（CS/SC 全量帧）、http.log（DSH_PROBE 客户端上报）、截屏（adb screencap） |

## 实测运行证据（CONFIRMED）

- 客户端进程运行中；DSH_PROBE 持续上报（state/scene/roles/bp/svEq/playerAppear/view/loadState/sceneData 等标签）。
- TCP 链路：心跳 1199 往返正常；SC_10204 移动帧（角色 1001 → (107,42) 落库）；SC_12400 任务列表推送（mission_list=1）。
- **客户端完全进入游戏**（截屏确认）：角色名 DSH 位于史莱克城（坐标 3195,1245），完整主界面（福利/商城/首充/变强/挂机/日常/提升/排行/钻石VIP/任务/队伍/好友/聊天/市场/神格/宗门/魂技/进阶/伙伴/锻造/更多/魂囊），任务"主线-武魂觉醒"进行中，弹窗"50级礼包"，聊天"欢迎来到绝世唐门!!!"。
- 存档：`analysis\_tmp\ph1_1411_inscene.png`（2560x1440 原始）、`ph1_1411_small.png`（缩略）。

## 采集任务（完成 ✅ → analysis/runtime_evidence/）

R1–R12 协议实值 + V1–V12 数值标定已完成，交付：
- `analysis/runtime_evidence/README.md`（环境说明）
- `analysis/runtime_evidence/calibration_R.md`（R1-R12，11/12，R8 部分：主线任务此前已提交，12403 幂等 code=1）
- `analysis/runtime_evidence/calibration_V.md`（V1-V12，5 实值+5 部分+2 UNKNOWN）
- `analysis/runtime_evidence/frames/key_frames.md`（60+ 条命令帧：命令号/方向/hex/解码/来源行号）
- `analysis/runtime_evidence/probes/dsh_probe_excerpt.md`（客户端 DSH_PROBE 佐证）
- `analysis/runtime_evidence/shots/`（22 张时间戳截屏）

### 实测关键数值（CONFIRMED/VERIFIED）
| 项 | 值 | 证据 |
|---|---|---|
| 角色等级 | 70 | 10302 帧 |
| 生命/物攻 | 4381 / 789 | 10303 帧 = UI 显示（双向印证） |
| 物防/法攻/法防 | 672 / 563 / 448 | UI 属性面板 + 帧 |
| 暴击/抗暴 | 113 / 90 | UI 属性面板 |
| 经验上限 | 2600094 | UI（V10） |
| 怪物（戴浩 mon=20001）HP | 2400 | 20010 帧（⚠ TEST_ONLY 占位） |
| 每击伤害 | 784（玩家）/ 1（怪物） | 4 回合战斗帧 |
| 击杀奖励 | +30 coin | 20023 结算（⚠ TEST_ONLY） |
| 掉落 | bid=33001（VIP2每日礼包）×1 | 20023 + 10500 推送 |
| 商城价格 | 洗髓丹礼盒 250 钻、神器突破礼盒 480 钻(8折限购1)、修炼笔记礼盒 630 钻(7折限购2)、高级神格礼包 680 钻(8折限购1) | 128xx + UI |
| 货币映射 | 服务端 gold = 客户端"钻石"（1799840 双向一致） | 10302 vs 商城 UI |

### 实机 vs 审计差异（已确认，写入运行记录）
1. **综合战力 UI=0**：mock_server 未推送客户端战力公式所需字段 → 战力系统缺口，Phase 4 处理（原审计 power=INFERENCE 成立，且客户端确实无战力显示）。
2. **背包 UI 0/150 但 10502 报 4 件**：物品（bid 28514 等）缺客户端渲染配置 → 内容填充阶段处理。
3. **战斗数值为占位 TEST_ONLY**：mon_hp=2400/+30coin 非原版真值 → 原版真值 UNKNOWN（需真服或深挖配置），实现时标 INFERENCE 留替换点。

## 待办
- [x] R1–R12 / V1–V12 采集（完成 2026-10-02）
- [ ] 差异清单 10.4：mock_server 实现 vs 实机回包逐项比对（持续）
- [x] 采集数据作为后续实现数值依据（已落盘 runtime_evidence/）
- [ ] Phase 2 Server Core 拆分（设计完成，实现启动）
