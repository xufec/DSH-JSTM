# JSTM Game Content Inventory — Detailed Counts

> PHASE 0 audit | Source: `server/cfg/*.json` (1.4.11 deconstructed from `_tmp_cfg/` luac files)
> Evidence: **CONFIRMED** — `file_update_1411.json` present in server/cfg, all table names match `_tmp_cfg/config_*.luac` filenames.
> Parsing note: Most tables use deconstructed luac format — top-level keys are table names, values are `{id: {array, hash}}` or `{id: [...]}` array-format entries. Row count = number of ID keys.

---

## Skills

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_skill.json | SkillPoint | 10 | deconstructed luac → Config.SkillPoint | CONFIRMED |
| config_skill.json | Skill | 0 | deconstructed luac → Config.Skill (empty) | CONFIRMED |
| config_skill_talent.json | **SkillTalent** | **105** | id_object → top-level dict keys | CONFIRMED |
| config_skill_talent.json | TalentRune | 35 | id_object → top-level dict keys | CONFIRMED |
| config_skill_talent.json | TalentRuneActivity | 105 | id_object → top-level dict keys | CONFIRMED |
| config_skill_xiulian.json | SkillXiulianLearn | 8 | id_object → top-level dict keys | CONFIRMED |
| config_skill_xiulian.json | SkillXiulianUp | 192 | id_object → top-level dict keys | CONFIRMED |
| config_skill_xiulian.json | SkillXiulianLev | 8 | id_object → top-level dict keys | CONFIRMED |
| config_skill_bullet.json | SkillBullet | 16 | id_object → top-level dict keys | CONFIRMED |
| config_skill_magic.json | SkillMagicType | 2 | deconstructed luac → Config.SkillMagicType | CONFIRMED |
| config_skill_magic.json | SkillMagic | 0 | deconstructed luac → Config.SkillMagic (empty) | CONFIRMED |
| config_skill_scene.json | SkillScene | 9 | id_object → top-level dict keys | CONFIRMED |
| config_skill_trigger.json | SkillTrigger | 4 | id_object → top-level dict keys | CONFIRMED |

**Primary skill count = 105** (SkillTalent — 天赋技能主表). All unique skill definitions ≈ 142.

---

## Equipment (from config_item.json)

Source: `server/cfg/config_item.json` → `Config.ItemData` = 3013 total entries.
Classification by **type field at array index [3]** (entries are 32-element deconstructed arrays).

| Type # | Category | Count |
|---:|---|---:|
| 100 | 武器 (weapon) | 63 |
| 103 | 腰带 (belt) | 13 |
| 104 | 头盔 (helmet) | 12 |
| 105 | 衣服/灵袍 (armor/robe) | 12 |
| 106 | 护手 (gloves) | 13 |
| 107 | 靴子 (boots) | 16 |
| 108 | 基础魂骨 (basic soul bone) | 5 |
| 109 | 魂环 (soul ring) | 36 |
| 110 | 戒指/饰品 (ring/accessory) | 6 |
| 120 | 进阶魂骨 (advanced soul bone) | 11 |
| 121 | 魂骨饰品 (soul bone accessory) | 11 |
| 200 | 时装头饰 (fashion head) | 32 |
| 201 | 时装衣服 (fashion armor) | 20 |
| 204 | 神器武器 (artifact weapon) | 28 |
| 240 | 进阶头盔 (evolved helmet) | 10 |
| 241 | 进阶衣服 (evolved armor) | 10 |
| 242 | 进阶鞋子 (evolved boots) | 10 |
| 243 | 进阶项链 (evolved necklace) | 10 |
| 244 | 进阶饰品 (evolved accessory) | 10 |
| 245 | 进阶戒指 (evolved ring) | 10 |
| 246 | 进阶武器 (evolved weapon) | 24 |
| | **Total wearable equipment** | **362** |

Sub-equipment (ride/pet/fabao gear, excluded from primary count): types 150-153, 160-163, 170-173, 180-183, 190-193, 210-213, 215-218 = **196 items**.

---

## Wings

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_wing_data.json | **WingBase** | **19** | id_object → top-level dict keys | CONFIRMED |
| config_wing_data.json | WingColor | 8 | id_object → top-level dict keys | CONFIRMED |
| config_wing_data.json | WingAllSkill | 8 | id_object → list length | CONFIRMED |
| config_wing_data.json | WingAttrs | 8 | id_object → top-level dict keys | CONFIRMED |
| config_wing_data.json | WingUpstar | 2 | id_object → top-level dict keys | CONFIRMED |

**Primary = 19** (WingBase — 翅膀基础表).

---

## Soulbones / Rune

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_rune_data.json | **RuneBase** | **124** | id_object → top-level dict keys | CONFIRMED |
| config_rune_data.json | RuneOpenLimit1 | 84 | id_object → top-level dict keys | CONFIRMED |
| config_rune_data.json | RuneHeroDesc | 53 | id_object → top-level dict keys | CONFIRMED |
| config_rune_data.json | RuneExchange | 20 | id_object → top-level dict keys | CONFIRMED |
| config_rune_data.json | RuneOpenLimit | 10 | id_object → top-level dict keys | CONFIRMED |
| config_rune_data.json | RuneGridOpen | 8 | id_object → top-level dict keys | CONFIRMED |

**Primary = 124** (RuneBase — 符文/魂骨基础表).

---

## Artifacts (Shenqi / 神器)

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_shenqi.json | **Shenqi** | **35** | id_object → top-level dict keys | CONFIRMED |
| config_shenqi.json | ShenqiUpgrade | 35 | id_object → top-level dict keys | CONFIRMED |
| config_shenqi.json | ShenqiMark | 35 | id_object → top-level dict keys | CONFIRMED |
| config_shenqi.json | ShenqiMedalList | 8 | id_object → top-level dict keys | CONFIRMED |
| config_shenqi.json | ShenqiMedal | 7 | id_object → top-level dict keys | CONFIRMED |
| config_shenqi.json | ShenqiList | 5 | id_object → top-level dict keys | CONFIRMED |

**Primary = 35** (Shenqi — 神器主表).

---

## Destiny / Mingge (命格)

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_mingge.json | **Mingge** | **25** | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeLevup | 25 | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeTuiJian | 25 | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeHandBook | 25 | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeGongming | 6 | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeStage | 5 | id_object → top-level dict keys | CONFIRMED |
| config_mingge.json | MinggeOpen | 2 | id_object → top-level dict keys | CONFIRMED |

**Primary = 25** (Mingge — 命格主表).

---

## Formations (阵法)

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_formation.json | **Formation** | **7** | id_object → top-level dict keys | CONFIRMED |
| config_formation.json | FormationType | 7 | id_object → top-level dict keys | CONFIRMED |
| config_formation.json | RoleNum | 2 | id_object → top-level dict keys | CONFIRMED |
| config_formation.json | RoleCheerNum | 2 | id_object → top-level dict keys | CONFIRMED |

**Primary = 7** (7 formation types, each with 10 level configurations = 70 total level entries).

---

## Bosses

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_boss.json | **Boss** | **27** | id_object → top-level dict keys | CONFIRMED |
| config_demon.json | **Demon** | **9** | id_object → top-level dict keys | CONFIRMED |
| config_demon.json | DemonStarUp | 5 | id_object → top-level dict keys | CONFIRMED |
| config_demon.json | DemonActionPower | 6 | id_object → top-level dict keys | CONFIRMED |

**Total bosses = 36** (27 Boss + 9 Demon).

---

## Dungeons

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_dungeon_new.json | **Dungeon** | **34** | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_new.json | MapDung | 76 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_new.json | TypeGroup | 20 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_tower.json | DungeonTower | 9 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_tower.json | DungeonTowerHard | 9 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_gods.json | DungeonGods | 9 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_rune.json | DungRuneTower | 10 | id_object → list length | CONFIRMED |
| config_dungeon_rune.json | DungRuneFloor | 9 | id_object → top-level dict keys | CONFIRMED |
| config_single_tower.json | SingleTower | 70 | id_object → top-level dict keys | CONFIRMED |
| config_single_tower.json | NtmTitle | 70 | id_object → top-level dict keys | CONFIRMED |
| config_golden_tower.json | GoldenTowerRes | 10 | id_object → top-level dict keys | CONFIRMED |
| config_golden_tower.json | GoldenTowerReward | 6 | id_object → top-level dict keys | CONFIRMED |
| config_primus.json | Primus | 6 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_vip_single.json | DungeonVipSingleShow | 6 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_vip_single.json | DungeonVipSingleSweep | 6 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_vip_single2.json | DungeonVipSingle2Show | 4 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_vip_single2.json | DungeonVipSingle2Sweep | 4 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_endless_data.json | DungeonEndlessShop | 44 | id_object → top-level dict keys | CONFIRMED |
| config_dungeon_seal_demon_data.json | DungeonSealDemonSceneType | 6 | id_object → top-level dict keys | CONFIRMED |

**Primary = 34** (main dungeon instances from Dungeon table). Including all special modes, total dungeon-related entries = 158+.

---

## GM Commands

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_gm_cmd.json | **GmCmd** | **211** | id_object → top-level dict keys | CONFIRMED |

---

## Fashion (optional)

| Table (file) | Sub-table | Rows | Parsing method | Evidence |
|---|---|---:|---|---|
| config_fashion.json | **Fashion** | **48** | id_object → top-level dict keys | CONFIRMED |

---

## Existing Values Cross-Check

| Metric | Existing value (source) | 1.4.11 cross-check (server/cfg) | Match? |
|---|---:|---:|---|
| maps | 124 (1.4.9) | 124 (config_map.json Map) | ✓ |
| npcs | 456 (1.4.9) | 456 (config_npc.json Npc) | ✓ |
| monsters | 2645 (1.4.9) | — (no equivalent 1.4.11 table found) | — |
| items | 3535 (1.4.9 item_config.json) | 3013 (config_item.json ItemData) | ✗ (1.4.11 has fewer) |
| missions | 846 (server/mission_config.json) | 846 (config_mission.json Mission) | ✓ |
| mall_goods | 142 (1.4.9 mall_config.json) | 179 total (110+45+24 in config_mall.json) | ✗ (1.4.11 has more) |
| partners | 53 (server/partner_config.json) | 53 (config_partner_base.json PartnerBase) | ✓ |
| gifts_packages | 496 (server/item_gift.json) | 766 (config_item_gift.json ItemGift) | ✗ (1.4.11 has more) |

---

## Source Version Evidence

- **CONFIRMED 1.4.11**: `server/cfg/file_update_1411.json` exists as a version marker file.
- All config table names in `server/cfg/*.json` correspond 1:1 with `_tmp_cfg/config_*.luac` filenames.
- `_tmp_cfg/` contains 295 extracted `.luac` files (of 355 in APK).
- server/cfg JSON files use the deconstructed luac format (array/hash structure), consistent with automated extraction from luac bytecode.

---

## 需 MuMu 运行时取证（值级数据）

> **硬约束**：本文件中所有"条数/行数"为 APK 配置表静态提取事实（CONFIRMED 成立，保持不动）。
> 以下**值级数据**（实际数值、概率、伤害公式结果等）仅靠配置表静态提取不足以确认真实运行行为，必须在 MuMu 模拟器运行 1.4.11 原版客户端 + mock_server 联调后采集实机数据，方可将证据等级从当前的 CONFIRMED（配置存在）提升为 VERIFIED（实机验证）。未取证前，相关实现不得标记为"已实现/已还原"。

| # | 待取证项 | 说明 | 当前状态 | 取证方式 |
|---:|---|---|---|---|
| 1 | **装备属性数值** | 362 件装备的实际攻防、气血、暴击等属性值，以及强化/进阶后的成长曲线，需实机穿戴后与配置表 hash 字段逐项核对 | 待 MuMu 取证 | 客户端打开角色面板，逐件穿戴截图对比 |
| 2 | **掉落表与概率** | 34 个 drop group 的实际掉落概率、掉落物品池与权重，以及怪物击杀后的真实掉落分布 | 待 MuMu 取证 | 击杀目标怪物 N 次统计掉落频率，与 config_drop.json 权重对比 |
| 3 | **怪物战斗数值** | 2645 只怪物的实际血量、攻防、伤害值是否与 config_mon.json 一致，以及等级缩放规则 | 待 MuMu 取证 | 进入怪物地图，用固定战力角色反复试探伤害数字 |
| 4 | **技能伤害/战斗数值** | 105 个天赋技能 + 8 个修炼技能的实际伤害系数、附加效果概率（眩晕/沉默等）、CD 与耗蓝 | 待 MuMu 取证 | 训练场打木桩，记录不同技能等级的伤害区间 |
| 5 | **战力公式结果** | 角色总战力、单属性战力贡献、装备/翅膀/魂骨等各系统的战力换算系数 | 待 MuMu 取证 | 穿戴/卸下单件装备，记录战力差值反推公式 |
| 6 | **商城价格实付校验** | MallGoods 110 + MallXian 45 + MallWeek 24 = 179 个商品的实际扣币数量、限购次数、每日刷新机制 | 待 MuMu 取证 | 购买/尝试购买各品类商品，观察扣币与弹窗 |
| 7 | **UI 显示值** | 地图数量(124)、NPC 数量(456)、副本入口数量等是否与客户端 UI 实际展示一致（有无灰度/等级隐藏） | 待 MuMu 取证 | 达到各等级段后打开对应 UI 面板截图计数 |
| 8 | **GM 命令实际效果** | 211 条 GM 命令中哪些在 1.4.11 服务端真实生效、哪些仅客户端定义未被服务端处理 | 待 MuMu 取证 | 逐条发送 GM 命令，观察客户端与服务端响应 |

> **原则**：凡涉及"配置表里有这个字段，但运行时是否真的按这个值生效"的问题，一律归入待 MuMu 取证。配置条数计数（本文件主体）不受影响。
