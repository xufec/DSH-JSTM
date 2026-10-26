# 绝世唐门 PHASE C0 数据资源总目录（只读审计）

- 生成时间：2026-10-15 13:28:06
- 生成器：`tools/jstm_audit/gen_data_inventory.py`（可重复运行）
- 数量与 ID 范围：**仅代表 1.4.11**（已提取 VERIFIED 级数据）；1.3.0 / 1.4.9 仅标注 config_tables 清单存在性，旧版本数量一律 UNKNOWN。
- 三版本 config_tables 清单规模：1.3.0=168 张 / 1.4.9=227 张 / 1.4.11=233 张；1.3.0 落盘证据目录文件数=165。
- 证据五档：VERIFIED / LIKELY / PARTIAL / UNVERIFIED / FAILED。

## 类别覆盖统计

| 类别 | 条目数 | 条目 data_id |
|---|---|---|
| 角色职业 | 1 | role_career |
| 等级经验 | 2 | role_attr, promote |
| 属性字段 | 2 | attr_data, attr_meta |
| 货币类型 | 1 | item_currency |
| 物品 | 1 | item_main |
| 装备 | 1 | item_equipment |
| 强化材料 | 1 | intensify |
| 宝石 | 1 | item_gem |
| 技能 | 2 | skill_raw, skill_talent |
| 伙伴 | 2 | partner_main, partner_base |
| 翅膀 | 1 | wing_data |
| 魂骨 | 1 | item_hungu |
| 时装 | 1 | item_fashion |
| 增幅 | 1 | buff_data |
| 神器 | 1 | shenqi |
| 命格 | 1 | mingge_cfg |
| 阵法 | 2 | formation, rune_cfg |
| 怪物 | 1 | mon_data |
| NPC | 3 | npc_main, npcs_10001, mapnpc_10001 |
| 地图场景 | 3 | mapnpc_10001, map_block, map_main |
| 任务 | 2 | mission_main, mission_route |
| 副本 | 3 | dungeon_single_tower, dungeon_tower, dungeon_corpus |
| 商城商品 | 3 | mall_main, mall_zhenbao, mall_exchange |
| 礼包 | 1 | item_gift |
| 活动 | 4 | richang, guaji, answer_key, invest_cfg |
| 奖励 | 4 | mall_exchange, drop, chengjiu, chengjiu_map |
| 其他 | 2 | runtime_config, runtime_npcs_mislabel |

**全部 27 个类别均有证据行**。

## 明细（按类别分组）

### 角色职业

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| role_career | 职业配置表（客户端解构） | `server/cfg/config_role_career.json` | 164 | 1 ~ 99095 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **role_career（职业配置表（客户端解构））**
  - 来源产物：`server/cfg/config_role_career.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：职业相关配置（具体字段以解构 JSON 为准）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_role_career.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_role_career.luac, 11703 字节）；统计注记: 顶层子表4个；条目合计164
  - 缺失信息：未逐条统计；职业 ID 与伙伴 career 字段（1-4）对应关系未成文

</details>

### 等级经验

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| role_attr | 角色等级经验表（RoleAttr，200 级） | `server/cfg/config_role_attr.json` | 200 | 1 ~ 200 | ✓/✓/✓ | VERIFIED |
| promote | 转生/晋升表 | `server/_promote.json` | 146 | — | —/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **role_attr（角色等级经验表（RoleAttr，200 级））**
  - 来源产物：`server/cfg/config_role_attr.json`
  - 提取方法：1.4.11 luac 批量解构产物；truth_values.json 已确认 200 级经验曲线
  - 字段含义：exp_max=本级所需经验；exp_total=累计经验；L1=240、L70=2,577,419、L200=1,917,555,775（取证值）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_role_attr.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_role_attr.luac, 15203 字节）；统计注记: 顶层子表1个；条目合计200
  - 缺失信息：—
- **promote（转生/晋升表）**
  - 来源产物：`server/_promote.json`
  - 提取方法：tools/extract_promote.py 提取
  - 字段含义：items=晋升配置列表；tips=提示文案
  - 版本差异：存在于: 1_4_9/1_4_11；缺失: 1_3_0。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_promote.json；统计注记: 子表 items
  - 缺失信息：—

</details>

### 属性字段

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| attr_data | 属性ID↔字段名映射表 | `server/_attr_data.json` | 394 | 101 ~ 243 | ✓/✓/✓ | VERIFIED |
| attr_meta | 属性数组元数据（向量长度） | `server/_attr_meta.json` | 64 | 101 ~ 243 | ✓/✓/✓ | PARTIAL |

<details><summary>该类条目溯源与字段说明</summary>

- **attr_data（属性ID↔字段名映射表）**
  - 来源产物：`server/_attr_data.json`
  - 提取方法：config_attr.luac 提取；tools/_fix_r92_14099.py 引用
  - 字段含义：AttrId2Key/AttrKey2Id/AttrId2Str/AttrKey2Str：属性ID↔字段名↔展示名；AttrPower=战力换算系数（atk_speed 450、hp_max 24 等，见 truth_values）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_attr_data.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_attr.luac, 5191 字节）；统计注记: 子表合计
  - 缺失信息：—
- **attr_meta（属性数组元数据（向量长度））**
  - 来源产物：`server/_attr_meta.json`
  - 提取方法：临时提取脚本产物
  - 字段含义：attr_len=属性向量长度（64）；items=逐属性说明
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_attr_meta.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_attr.luac, 5191 字节）；统计注记: 子表 items
  - 缺失信息：items 条目逐属性含义未逐条核对

</details>

### 货币类型

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_currency | 货币类物品（item_config type 0/12/20 疑似分组） | `server/item_config.json` | 24 | 11 ~ 37710 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **item_currency（货币类物品（item_config type 0/12/20 疑似分组））**
  - 来源产物：`server/item_config.json`
  - 提取方法：对 item_config.json 按 type 聚合统计（本脚本实时计算）
  - 字段含义：type 0=幸运币（bid 28030）；type 12/20 条目 name 字段为纯数字（bid 11/3200），疑似货币/经验券占位
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item.luac, 470884 字节）；统计注记: type=[0, 12, 20] 分组合计
  - 缺失信息：货币类型枚举表未找到；服务端代码中 coin/hero_coin/vip_exp 等账目与物品 bid 的对应关系未成文

</details>

### 物品

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_main | 物品主表（全物品字典） | `server/item_config.json` | 3535 | 0 ~ 3888000 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **item_main（物品主表（全物品字典））**
  - 来源产物：`server/item_config.json`
  - 提取方法：tools/extract_item_v2.py / extract_config_item.py（1.4.11 客户端提取）
  - 字段含义：bid=物品ID；name=名称；type=物品分类编号；lev=使用等级；quality=品质；bind_type=绑定类型；overlap=可叠加数量；durable=耐久；use_type=使用效果类型
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item.luac, 470884 字节）
  - 缺失信息：type→分类中文名映射未成文（仅有采样对照，如11=物攻石、100=武器、201=男时装）

</details>

### 装备

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_equipment | 装备类物品（item_config 中装备 type 分组） | `server/item_config.json` | 213 | 40001 ~ 99999 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **item_equipment（装备类物品（item_config 中装备 type 分组））**
  - 来源产物：`server/item_config.json`
  - 提取方法：对 item_config.json 按 type 聚合统计（本脚本实时计算）
  - 字段含义：type 100=武器/103=腰带/104=帽子/105=衣服/106=护手/107=靴子；type 240-246=魂师套装六部位+武器
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item.luac, 470884 字节）；统计注记: type=[100, 103, 104, 105, 106, 107, 240, 241, 242, 243, 244, 245, 246] 分组合计
  - 缺失信息：装备基础属性（+0 白装数值）不在物品表内，由公式或未识别表决定（见 truth_values/monster_values 取证）

</details>

### 强化材料

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| intensify | 装备强化数值表（成功率/消耗/奖励） | `server/cfg/config_intensify.json` | 129 | 1 ~ 36043 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **intensify（装备强化数值表（成功率/消耗/奖励））**
  - 来源产物：`server/cfg/config_intensify.json`
  - 提取方法：1.4.11 luac 批量解构产物；truth_values.json CONFIRMED
  - 字段含义：IntensifyReward=8-15 级单件加成（+8 武器 atk_s+20）；IntensifyAllReward=6-8 阶套装加成；强化石 bid=36006；消耗金币每级递增 2000
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_intensify.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_intensify.luac, 40057 字节）；统计注记: 顶层子表13个；条目合计129
  - 缺失信息：—

</details>

### 宝石

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_gem | 宝石类物品（item_config type 11-19 分组） | `server/item_config.json` | 71 | 11 ~ 37690 | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **item_gem（宝石类物品（item_config type 11-19 分组））**
  - 来源产物：`server/item_config.json`
  - 提取方法：对 item_config.json 按 type 聚合统计（本脚本实时计算）
  - 字段含义：11=物攻石/13=物防石/14=法防石/15=气血石/16=速度石/19=暴击石；镶嵌系统见 config_jewel 相关脚本证据（gem_inlay_spec.md）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item.luac, 470884 字节）；统计注记: type=[11, 12, 13, 14, 15, 16, 19] 分组合计
  - 缺失信息：无独立宝石属性表（truth_values: NO_SEPARATE_GEM_TABLE）；type 12/20 采样呈纯数字，疑似货币，未计入宝石组

</details>

### 技能

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| skill_raw | 技能原始表（4000 行结构化数组） | `server/_skill_raw.json` | 4000 | 1 ~ 15868 | ✓/✓/✓ | PARTIAL |
| skill_talent | 技能天赋表（客户端解构） | `server/cfg/config_skill_talent.json` | 245 | 10020 ~ 90800 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **skill_raw（技能原始表（4000 行结构化数组））**
  - 来源产物：`server/_skill_raw.json`
  - 提取方法：临时提取脚本产物（未定位唯一脚本；luac 源表疑似 config_skill_xiulian.luac，待核）
  - 字段含义：行数组：idx1=技能ID；idx2=技能名（普攻/治疗等）；idx19=效果描述（如"造成250%伤害"）；其余字段语义未逐列定义
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_skill_raw.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_skill_xiulian.luac, 97451 字节）；统计注记: 行内第2列=技能ID
  - 缺失信息：列语义未完全定义；学习/升级消耗字段不存在（truth_values: NOT_FOUND_IN_CONFIG）
- **skill_talent（技能天赋表（客户端解构））**
  - 来源产物：`server/cfg/config_skill_talent.json`
  - 提取方法：1.4.11 luac 批量解构产物；truth_values 确认仅 name/bid/skill_group 字段，无消耗字段
  - 字段含义：name/bid/skill_group/skill_talent/magic_talent；无 gold/coin/item 消耗字段
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_skill_talent.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_skill_talent.luac, 18655 字节）；统计注记: 顶层子表3个；条目合计245
  - 缺失信息：技能学习/升级消耗在配置表中不存在

</details>

### 伙伴

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| partner_main | 伙伴主表（伙伴名册） | `server/partner_config.json` | 53 | 30000 ~ 35700 | ✓/✓/✓ | VERIFIED |
| partner_base | 伙伴基础档案（含外观/性别/描述） | `server/_partner_base.json` | 53 | 30000 ~ 35700 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **partner_main（伙伴主表（伙伴名册））**
  - 来源产物：`server/partner_config.json`
  - 提取方法：临时脚本产物（53 伙伴，与 _partner_base.json 同源）；源 luac 疑似 config_partner_base.luac
  - 字段含义：bid=伙伴ID（33100 起）；name=名称（唐舞桐等）；career=职业；score=战力评分；take_lev=携带等级；mode=模式
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/partner_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_partner_base.luac, 68631 字节）
  - 缺失信息：伙伴技能/羁绊/神器子表见 cfg/config_partner_skill.json(309KB)/config_partner_fetter.json(60KB)，未逐条统计
- **partner_base（伙伴基础档案（含外观/性别/描述））**
  - 来源产物：`server/_partner_base.json`
  - 提取方法：临时脚本产物；tools/verify_partner_list.py 可复算
  - 字段含义：name/score/career/bid/die_effect=死亡特效E码/by_resource=立绘H码/is_deity=是否神级/height=身高/desc=描述
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_partner_base.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_partner_base.luac, 68631 字节）
  - 缺失信息：—

</details>

### 翅膀

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| wing_data | 翅膀数据（客户端解构） | `server/cfg/config_wing_data.json` | 71 | 1 ~ 102 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **wing_data（翅膀数据（客户端解构））**
  - 来源产物：`server/cfg/config_wing_data.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：翅膀外观/进阶/属性配置（具体字段以解构 JSON 为准）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_wing_data.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_wing_data.luac, 16192 字节）；统计注记: 顶层子表9个；条目合计71
  - 缺失信息：未逐条统计；翅膀系统消费曲线未成文

</details>

### 魂骨

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_hungu | 魂骨类物品（item_config type 108/120/121/22 分组） | `server/item_config.json` | 28 | 25700 ~ 44060 | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **item_hungu（魂骨类物品（item_config type 108/120/121/22 分组））**
  - 来源产物：`server/item_config.json`
  - 提取方法：对 item_config.json 按 type 聚合统计（本脚本实时计算）
  - 字段含义：108=魂骨（如碧莲魂骨）；120/121=高级魂骨（瀚海头骨/妖眼树盾）；22=魂骨碎片
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item.luac, 470884 字节）；统计注记: type=[22, 108, 120, 121] 分组合计
  - 缺失信息：魂骨强化/进阶规则表未在已提取清单中定位

</details>

### 时装

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_fashion | 时装表（客户端解构）+ 时装类物品 | `server/cfg/config_fashion.json` | 48 | 43100 ~ 43264 | —/✓/✓ | PARTIAL |

<details><summary>该类条目溯源与字段说明</summary>

- **item_fashion（时装表（客户端解构）+ 时装类物品）**
  - 来源产物：`server/cfg/config_fashion.json`
  - 提取方法：1.4.11 luac 批量解构产物（server/cfg/ 语料）；物品侧类型见 item_config type 201/255
  - 字段含义：时装外观/进阶配置；item_config 中 type 201=庆典夏日时装·男等
  - 版本差异：存在于: 1_4_9/1_4_11；缺失: 1_3_0。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_fashion.json；统计注记: 顶层子表1个；条目合计48
  - 缺失信息：未逐条统计时装表条目数（通用统计）；时装进阶消耗表 config_fashion_up.json 仅 2 字节（空表）

</details>

### 增幅

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| buff_data | Buff/增幅数据表（客户端解构，102KB） | `server/cfg/config_buff_data.json` | 363 | 10000 ~ 43025 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **buff_data（Buff/增幅数据表（客户端解构，102KB））**
  - 来源产物：`server/cfg/config_buff_data.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：Buff 效果/持续时间/叠加规则（本类别映射为推断："增幅"在项目中无独立命名表）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_buff_data.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_buff_data.luac, 53242 字节）；统计注记: 顶层子表1个；条目合计363
  - 缺失信息："增幅"类别无直接命名证据；映射到 buff_data 为最佳推断，需人工确认

</details>

### 神器

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| shenqi | 神器表（客户端解构，574KB） | `server/cfg/config_shenqi.json` | 127 | 1 ~ 10065 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **shenqi（神器表（客户端解构，574KB））**
  - 来源产物：`server/cfg/config_shenqi.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：神器列表/成长配置（具体字段以解构 JSON 为准）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_shenqi.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_shenqi.luac, 163441 字节）；统计注记: 顶层子表7个；条目合计127
  - 缺失信息：未逐条统计

</details>

### 命格

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mingge_cfg | 命格配置（开/阶/其他子表） | `server/_mingge_cfg.json` | 9 | 1 ~ 5 | —/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **mingge_cfg（命格配置（开/阶/其他子表））**
  - 来源产物：`server/_mingge_cfg.json`
  - 提取方法：tools/_fix_r111_mingge.py 落盘修复（源自 config_mingge.luac 解构）
  - 字段含义：MinggeOther/MinggeOpen/MinggeStage 三个子表（开服条件、阶段、附加规则）
  - 版本差异：存在于: 1_4_9/1_4_11；缺失: 1_3_0。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_mingge_cfg.json；统计注记: 子表合计
  - 缺失信息：子表逐行语义未逐条成文

</details>

### 阵法

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| formation | 阵法表（客户端解构） | `server/cfg/config_formation.json` | 18 | 1 ~ 7 | ✓/✓/✓ | UNVERIFIED |
| rune_cfg | 符文配置（交换/静态/基础三子表） | `server/_rune_cfg.json` | 146 | 1 ~ 21595 | —/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **formation（阵法表（客户端解构））**
  - 来源产物：`server/cfg/config_formation.json`
  - 提取方法：1.4.11 luac 批量解构产物；_cfg_formation.txt 探针证据
  - 字段含义：阵法激活/属性加成配置
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_formation.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_formation.luac, 14916 字节）；统计注记: 顶层子表4个；条目合计18
  - 缺失信息：未逐条统计
- **rune_cfg（符文配置（交换/静态/基础三子表））**
  - 来源产物：`server/_rune_cfg.json`
  - 提取方法：tools/_fix_r109_rune_exchange.py 落盘修复（源自 config_rune_data.luac 1.7MB 解构）
  - 字段含义：RuneExchange=兑换配方；RuneStatic=静态属性；RuneBase=基础数据
  - 版本差异：存在于: 1_4_9/1_4_11；缺失: 1_3_0。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_rune_cfg.json；统计注记: 子表合计
  - 缺失信息：—

</details>

### 怪物

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mon_data | 怪物表（1.4.11 解构部分失败；1.4.9 参考 2645 怪） | `server/cfg/config_mon_data.json` | UNKNOWN | — | ✓/✓/✓ | PARTIAL |

<details><summary>该类条目溯源与字段说明</summary>

- **mon_data（怪物表（1.4.11 解构部分失败；1.4.9 参考 2645 怪））**
  - 来源产物：`server/cfg/config_mon_data.json`
  - 提取方法：1.4.11 解构产物仅 311 字节（主表空）；1.4.9 完整参考：analysis/1.4.9/task/config_mon.json（818,547 字节，2645 条）
  - 字段含义：24 元素数组：idx1=怪名(601种)/idx2=等级(1-150)/idx3=类型(0普通1389/1普通1205/4精英BOSS51)/idx8=资源ID/idx21=战斗数值倍率(0.7-15x)/idx23=掉落层(0/2/4/6/8)；无显式 HP/ATK 字段
  - 版本差异：三版本均有 config_mon_data.luac（存在性见清单）；1.4.11 解构主表失败，1.4.9 参考 2645 条；1.3.0 数量 UNKNOWN。
  - 证据：server/cfg/config_mon_data.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_mon_data.luac, 513571 字节）；统计注记: 1.4.11 主表空（311B）；1.4.9 参考 2645 条（见 monster_values.json）
  - 缺失信息：1.4.11 主表解构失败；怪物 HP/ATK 由服务端公式计算，静态不可得

</details>

### NPC

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| npc_main | NPC 主表（客户端解构，195KB） | `server/cfg/config_npc.json` | 593 | 1001 ~ 80100 | ✓/✓/✓ | UNVERIFIED |
| npcs_10001 | 单地图 NPC 坐标快照（地图10001，提取残缺） | `server/_npcs_10001.json` | 18 | 10010 ~ 10170 | ✓/✓/✓ | FAILED |
| mapnpc_10001 | 地图 NPC 放置表（地图10001） | `server/_mapnpc_10001.json` | 19 | 10010 ~ 10175 | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **npc_main（NPC 主表（客户端解构，195KB））**
  - 来源产物：`server/cfg/config_npc.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：NPC 列表/对话/功能入口配置
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_npc.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_npc.luac, 116497 字节）；统计注记: 顶层子表3个；条目合计593
  - 缺失信息：未逐条统计
- **npcs_10001（单地图 NPC 坐标快照（地图10001，提取残缺））**
  - 来源产物：`server/_npcs_10001.json`
  - 提取方法：临时脚本产物；文件在第 163 行截断（尾部 "id": 后缺内容）
  - 字段含义：id/bid=NPC编号(10001-10081)；x/y=坐标；name=npc<id>；另有两条哨兵记录 id=Config/MapNpc
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_npcs_10001.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_npc.luac, 116497 字节）；统计注记: 正则统计（文件截断，JSON 不可解析）
  - 缺失信息：JSON 不可解析；仅能按 "id" 出现次数统计（21 次=19 个数值 NPC + 2 哨兵）；真实条数可能更多
- **mapnpc_10001（地图 NPC 放置表（地图10001））**
  - 来源产物：`server/_mapnpc_10001.json`
  - 提取方法：临时脚本产物（对应 extract_map_npc.py 路线）
  - 字段含义：id/bid=NPC编号；type=类型；x/y=格子坐标；name=NPC名
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_mapnpc_10001.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_map_npc.luac, 1894 字节）
  - 缺失信息：仅覆盖地图 10001 一张图

</details>

### 地图场景

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mapnpc_10001 | 地图 NPC 放置表（地图10001） | `server/_mapnpc_10001.json` | 19 | 10010 ~ 10175 | ✓/✓/✓ | LIKELY |
| map_block | 地图遮挡/通行块数据 | `server/map_block.json` | 26 | 10001 ~ 31000 | ✓/✓/✓ | VERIFIED |
| map_main | 地图主表（客户端解构，83KB） | `server/cfg/config_map.json` | 124 | 10001 ~ 31008 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **mapnpc_10001（地图 NPC 放置表（地图10001））**
  - 来源产物：`server/_mapnpc_10001.json`
  - 提取方法：临时脚本产物（对应 extract_map_npc.py 路线）
  - 字段含义：id/bid=NPC编号；type=类型；x/y=格子坐标；name=NPC名
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_mapnpc_10001.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_map_npc.luac, 1894 字节）
  - 缺失信息：仅覆盖地图 10001 一张图
- **map_block（地图遮挡/通行块数据）**
  - 来源产物：`server/map_block.json`
  - 提取方法：tools/extract_config_mapblock.py 提取
  - 字段含义：_meta.source/polarity/blocked_chars；scenes=逐场景遮挡统计（cells_total/cells_blocked/blocked_ratio）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/map_block.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_map_block.luac, 499390 字节）；统计注记: 子表 scenes
  - 缺失信息：—
- **map_main（地图主表（客户端解构，83KB））**
  - 来源产物：`server/cfg/config_map.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：地图列表/进出/出生点配置
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_map.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_map.luac, 23184 字节）；统计注记: 顶层子表1个；条目合计124
  - 缺失信息：未逐条统计

</details>

### 任务

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mission_main | 任务主表（全任务字典） | `server/mission_config.json` | 846 | 10010 ~ 86073 | ✓/✓/✓ | VERIFIED |
| mission_route | 任务链/主线路由表 | `server/_mission_route.json` | 102 | 35000 ~ 86000 | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **mission_main（任务主表（全任务字典））**
  - 来源产物：`server/mission_config.json`
  - 提取方法：tools/extract_mission_config.py 提取
  - 字段含义：bid=任务ID；type/show_type=任务类型；career=适用职业；accept_npc_id=接取NPC；accept_talk/commit_talk/process_talk=对话；auto_commit=自动完成
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/mission_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_mission.luac, 325400 字节）
  - 缺失信息：—
- **mission_route（任务链/主线路由表）**
  - 来源产物：`server/_mission_route.json`
  - 提取方法：临时脚本产物（键 35000 段，与主表互补）
  - 字段含义：name=名称；type=类型；realm=界；lev=等级；desc=描述
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_mission_route.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_mission.luac, 325400 字节）
  - 缺失信息：与 config_mission.luac 的确切子表对应关系未定位

</details>

### 副本

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| dungeon_single_tower | 单人爬塔副本表 | `server/cfg_config_single_tower.json` | 156 | 1 ~ 42004 | ✓/✓/✓ | VERIFIED |
| dungeon_tower | 妖塔/多层副本表 | `server/cfg_config_dungeon_tower.json` | 48 | 2 ~ 35056 | ✓/✓/✓ | VERIFIED |
| dungeon_corpus | 副本群解构语料（config_dungeon_* 系列） | `server/cfg/config_dungeon_new.json` | 169 | 1 ~ 80003 | ✓/✓/✓ | UNVERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **dungeon_single_tower（单人爬塔副本表）**
  - 来源产物：`server/cfg_config_single_tower.json`
  - 提取方法：临时脚本产物（源 luac 疑似 config_single_tower.luac）
  - 字段含义：键=层/关ID；值=该层怪物/奖励列表
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg_config_single_tower.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_single_tower.luac, 43088 字节）
  - 缺失信息：—
- **dungeon_tower（妖塔/多层副本表）**
  - 来源产物：`server/cfg_config_dungeon_tower.json`
  - 提取方法：临时脚本产物
  - 字段含义：键=关ID；值=配置数组
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg_config_dungeon_tower.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_dungeon_tower.luac, 4182 字节）
  - 缺失信息：—
- **dungeon_corpus（副本群解构语料（config_dungeon_* 系列））**
  - 来源产物：`server/cfg/config_dungeon_new.json`
  - 提取方法：1.4.11 luac 批量解构产物
  - 字段含义：副本列表/奖励/进入条件（另有 config_dungeon_tower.json/gods.json/rune.json/seal_demon_data.json/vip_single*.json）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg/config_dungeon_new.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_dungeon_new.luac, 4616 字节）；统计注记: 顶层子表9个；条目合计169
  - 缺失信息：未逐条统计

</details>

### 商城商品

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mall_main | 商城商品主表 | `server/mall_config.json` | 142 | 2001 ~ 20025 | ✓/✓/✓ | VERIFIED |
| mall_zhenbao | 珍宝阁商品（实现回退数据） | `server/mall_zhenbao.json` | 45 | 21001 ~ 21045 | ✓/✓/✓ | PARTIAL |
| mall_exchange | 商城兑换配方（APK 内无此表，实现回退） | `server/mall_exchange.json` | 28 | 22001 ~ 22028 | —/—/— | PARTIAL |

<details><summary>该类条目溯源与字段说明</summary>

- **mall_main（商城商品主表）**
  - 来源产物：`server/mall_config.json`
  - 提取方法：tools/extract_mall.py 提取
  - 字段含义：id=商品位；item_bid=商品物品；pay_type=支付货币类型；price=价格；limit_week/limit_day_cli=限购；cli_tag=客户端标签(HOT等)
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/mall_config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_mall.luac, 17598 字节）
  - 缺失信息：—
- **mall_zhenbao（珍宝阁商品（实现回退数据））**
  - 来源产物：`server/mall_zhenbao.json`
  - 提取方法：实现回退（source 字段=IMPLEMENTATION_FALLBACK_v2），非客户端配置直提
  - 字段含义：id/item_bid/item_name/price/limit_num/buy_num
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/mall_zhenbao.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_mall.luac, 17598 字节）
  - 缺失信息：非原版配置真值；原版珍宝阁配方是否在 APK 内未确认
- **mall_exchange（商城兑换配方（APK 内无此表，实现回退））**
  - 来源产物：`server/mall_exchange.json`
  - 提取方法：实现回退（source 字段=IMPLEMENTATION_FALLBACK）；backup 注释明确"原版兑换配方不在 APK 内"
  - 字段含义：id/item_bid=消耗物品；new_item_bid/new_item_num=产出；limit_num=限购
  - 版本差异：存在于: 无；缺失: 1_3_0/1_4_9/1_4_11。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/mall_exchange.json
  - 缺失信息：非原版配置真值；config_exchange.json(40KB) 解构表存在但未与该文件对齐

</details>

### 礼包

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| item_gift | 物品礼包内容表 | `server/item_gift.json` | 496 | 0 ~ 44751 | ✓/✓/✓ | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **item_gift（物品礼包内容表）**
  - 来源产物：`server/item_gift.json`
  - 提取方法：tools/extract_item_gift.py 提取
  - 字段含义：键=礼包ID；值=物品列表（bid/数量数组）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/item_gift.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_item_gift.luac, 105347 字节）
  - 缺失信息：—

</details>

### 活动

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| richang | 日常任务/活跃表 | `server/_richang.json` | 43 | 101 ~ 255 | ✓/✓/✓ | VERIFIED |
| guaji | 挂机地图列表 | `server/_guaji.json` | 8 | — | ✓/✓/✓ | VERIFIED |
| answer_key | 答题答案表（项目手工推导） | `server/answer_key.json` | 239 | 10001 ~ 10243 | ✓/✓/✓ | PARTIAL |
| invest_cfg | 投资计划配置（6 子表） | `server/_invest_cfg.json` | 12 | 2 ~ 8 | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **richang（日常任务/活跃表）**
  - 来源产物：`server/_richang.json`
  - 提取方法：tools/extract_richang.py 提取
  - 字段含义：tasks=日常任务列表；kezhi=克制/规则子表
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_richang.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_richang.luac, 21849 字节）；统计注记: 子表 tasks
  - 缺失信息：—
- **guaji（挂机地图列表）**
  - 来源产物：`server/_guaji.json`
  - 提取方法：tools/extract_guaji.py 提取
  - 字段含义：spots=挂机区域（星斗大森林等 8 区，level_range 25-34、map_bid、mon_bid）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_guaji.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_guaji.luac, 930 字节）；统计注记: 子表 spots
  - 缺失信息：每分钟收益速率不在配置表（truth_values: NOT_IN_CONFIG）
- **answer_key（答题答案表（项目手工推导））**
  - 来源产物：`server/answer_key.json`
  - 提取方法：手工推导（server/answer/service.py 注释：项目自定义推导键，依据题面推导）
  - 字段含义：answers=题目→答案映射；_meta.provenance/reason/evidence_level
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/answer_key.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_answer.luac, 24513 字节）；统计注记: 子表 answers
  - 缺失信息：非客户端 config_answer.luac 直提；与原版答案一致性未验证
- **invest_cfg（投资计划配置（6 子表））**
  - 来源产物：`server/_invest_cfg.json`
  - 提取方法：tools/_fix_r107_invest.py 落盘修复
  - 字段含义：InvestType/AllFanhuan/DayInvest/LevInvest 等子表
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_invest_cfg.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_invest.luac, 3260 字节）；统计注记: 子表合计
  - 缺失信息：—

</details>

### 奖励

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| mall_exchange | 商城兑换配方（APK 内无此表，实现回退） | `server/mall_exchange.json` | 28 | 22001 ~ 22028 | —/—/— | PARTIAL |
| drop | 掉落组表 | `server/cfg_drop.json` | 34 | 4001 ~ 30004 | ✓/✓/✓ | VERIFIED |
| chengjiu | 成就表 | `server/_chengjiu.json` | 342 | 10100 ~ 51000 | ✓/✓/✓ | VERIFIED |
| chengjiu_map | 成就分组映射（手工整理） | `server/_chengjiu_map.json` | 12 | — | ✓/✓/✓ | LIKELY |

<details><summary>该类条目溯源与字段说明</summary>

- **mall_exchange（商城兑换配方（APK 内无此表，实现回退））**
  - 来源产物：`server/mall_exchange.json`
  - 提取方法：实现回退（source 字段=IMPLEMENTATION_FALLBACK）；backup 注释明确"原版兑换配方不在 APK 内"
  - 字段含义：id/item_bid=消耗物品；new_item_bid/new_item_num=产出；limit_num=限购
  - 版本差异：存在于: 无；缺失: 1_3_0/1_4_9/1_4_11。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/mall_exchange.json
  - 缺失信息：非原版配置真值；config_exchange.json(40KB) 解构表存在但未与该文件对齐
- **drop（掉落组表）**
  - 来源产物：`server/cfg_drop.json`
  - 提取方法：tools/extract_drop.py 提取
  - 字段含义：键=掉落组ID(20001段)；值=[{coin, normal:[{item,num,pp}], core, first}]；pp=概率点（池内归一）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/cfg_drop.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_drop.luac, 8195 字节）
  - 缺失信息：—
- **chengjiu（成就表）**
  - 来源产物：`server/_chengjiu.json`
  - 提取方法：tools/extract_chengjiu.py 提取
  - 字段含义：items=成就条目字典（10100 段分组）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_chengjiu.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_chengjiu.luac, 13848 字节）；统计注记: 子表 items
  - 缺失信息：—
- **chengjiu_map（成就分组映射（手工整理））**
  - 来源产物：`server/_chengjiu_map.json`
  - 提取方法：手工映射产物（groups 分组清单）
  - 字段含义：groups=成就分组列表（43 组）
  - 版本差异：存在于: 1_3_0/1_4_9/1_4_11；缺失: 无。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/_chengjiu_map.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config_chengjiu.luac, 13848 字节）；统计注记: 子表 groups
  - 缺失信息：分组为人工整理，与原版分组定义对应关系未逐条验证

</details>

### 其他

| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |
|---|---|---|---|---|---|---|
| runtime_config | 服务端连接运行时配置（非游戏数据表） | `server/config.json` | 133 | — | —/—/— | VERIFIED |
| runtime_npcs_mislabel | "config_21npcs.json"（命名误导：实为服务端运行配置，非 NPC 表） | `server/config_21npcs.json` | 16 | — | —/—/— | VERIFIED |

<details><summary>该类条目溯源与字段说明</summary>

- **runtime_config（服务端连接运行时配置（非游戏数据表））**
  - 来源产物：`server/config.json`
  - 提取方法：mock_server 运行配置（bind/host/http_port/game_port/server_list）
  - 字段含义：bind=监听地址；host=模拟器回环 10.0.2.2；http_port=8080；game_port=9000
  - 版本差异：存在于: 无；缺失: 1_3_0/1_4_9/1_4_11。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/config.json（1.3.0 落盘证据: analysis\version_compare\1.3.0\extracted\config\config.luac, 4097 字节）；统计注记: 运行配置项数（非数据表）
  - 缺失信息：—
- **runtime_npcs_mislabel（"config_21npcs.json"（命名误导：实为服务端运行配置，非 NPC 表））**
  - 来源产物：`server/config_21npcs.json`
  - 提取方法：直接读文件核实：内容为 bind/host/server_list 运行配置，与 21 个 NPC 无关
  - 字段含义：bind/host/http_port/game_port/server_list[].ip/port/state
  - 版本差异：存在于: 无；缺失: 1_3_0/1_4_9/1_4_11。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。
  - 证据：server/config_21npcs.json；统计注记: 运行配置项数（非数据表）
  - 缺失信息：文件名与内容不符的原因（历史命名）未追溯

</details>

## 未确认项清单

- `item_fashion`（时装表（客户端解构）+ 时装类物品）：置信=PARTIAL；未逐条统计时装表条目数（通用统计）；时装进阶消耗表 config_fashion_up.json 仅 2 字节（空表）
- `item_currency`（货币类物品（item_config type 0/12/20 疑似分组））：置信=UNVERIFIED；货币类型枚举表未找到；服务端代码中 coin/hero_coin/vip_exp 等账目与物品 bid 的对应关系未成文
- `skill_raw`（技能原始表（4000 行结构化数组））：置信=PARTIAL；列语义未完全定义；学习/升级消耗字段不存在（truth_values: NOT_FOUND_IN_CONFIG）
- `attr_meta`（属性数组元数据（向量长度））：置信=PARTIAL；items 条目逐属性含义未逐条核对
- `role_career`（职业配置表（客户端解构））：置信=UNVERIFIED；未逐条统计；职业 ID 与伙伴 career 字段（1-4）对应关系未成文
- `wing_data`（翅膀数据（客户端解构））：置信=UNVERIFIED；未逐条统计；翅膀系统消费曲线未成文
- `shenqi`（神器表（客户端解构，574KB））：置信=UNVERIFIED；未逐条统计
- `formation`（阵法表（客户端解构））：置信=UNVERIFIED；未逐条统计
- `buff_data`（Buff/增幅数据表（客户端解构，102KB））：置信=UNVERIFIED；"增幅"类别无直接命名证据；映射到 buff_data 为最佳推断，需人工确认
- `mon_data`（怪物表（1.4.11 解构部分失败；1.4.9 参考 2645 怪））：置信=PARTIAL；1.4.11 主表解构失败；怪物 HP/ATK 由服务端公式计算，静态不可得
- `npc_main`（NPC 主表（客户端解构，195KB））：置信=UNVERIFIED；未逐条统计
- `npcs_10001`（单地图 NPC 坐标快照（地图10001，提取残缺））：置信=FAILED；JSON 不可解析；仅能按 "id" 出现次数统计（21 次=19 个数值 NPC + 2 哨兵）；真实条数可能更多
- `map_main`（地图主表（客户端解构，83KB））：置信=UNVERIFIED；未逐条统计
- `dungeon_corpus`（副本群解构语料（config_dungeon_* 系列））：置信=UNVERIFIED；未逐条统计
- `mall_zhenbao`（珍宝阁商品（实现回退数据））：置信=PARTIAL；非原版配置真值；原版珍宝阁配方是否在 APK 内未确认
- `mall_exchange`（商城兑换配方（APK 内无此表，实现回退））：置信=PARTIAL；非原版配置真值；config_exchange.json(40KB) 解构表存在但未与该文件对齐
- `answer_key`（答题答案表（项目手工推导））：置信=PARTIAL；非客户端 config_answer.luac 直提；与原版答案一致性未验证
