# -*- coding: utf-8 -*-
"""
gen_data_inventory.py — 绝世唐门 PHASE C0 审计：数据资源总目录生成器（只读审计）

输入（全部只读）：
  - analysis/jstm_client_audit/_raw/apk_scan_{1_3_0,1_4_9,1_4_11}.json （三版本 config_tables 清单）
  - analysis/version_compare/1.3.0/extracted/config/*.luac            （1.3.0 落盘证据）
  - server/*.json 与 server/cfg/*.json                                （1.4.11 已提取配置，VERIFIED 级）
  - analysis/extraction/truth_values.json / monster_values.json       （运行时/静态取证）

输出（只新建这两个文件，不修改任何既有文件）：
  - analysis/jstm_client_audit/data_inventory.json
  - analysis/jstm_client_audit/data_inventory.md

纪律：
  - count / id_range 一律来自对实际文件的程序化统计，禁止凭 ID 连续性推测；
  - 旧版本（1.3.0 / 1.4.9）只标注 config_tables 清单中的存在性，数量未知一律 UNKNOWN；
  - 证据五档：VERIFIED / LIKELY / PARTIAL / UNVERIFIED / FAILED。
"""
import json, io, os, re, collections, datetime

ROOT = r'C:\Users\xu\Desktop\DSH'
OUT_DIR = os.path.join(ROOT, 'analysis', 'jstm_client_audit')
SERVER = os.path.join(ROOT, 'server')
CFG = os.path.join(SERVER, 'cfg')

# ---------------------------------------------------------------- 载入三版本清单
def load_scan(v):
    p = os.path.join(ROOT, 'analysis', 'jstm_client_audit', '_raw', 'apk_scan_%s.json' % v)
    d = json.load(io.open(p, 'r', encoding='utf-8'))
    return set(d['config_tables'])

VERSIONS = ('1_3_0', '1_4_9', '1_4_11')
CT = {v: load_scan(v) for v in VERSIONS}

# 1.3.0 落盘证据（analysis/version_compare/1.3.0/extracted/config/）
ext13_dir = os.path.join(ROOT, 'analysis', 'version_compare', '1.3.0', 'extracted', 'config')
EXT13 = {}
if os.path.isdir(ext13_dir):
    for fn in os.listdir(ext13_dir):
        fp = os.path.join(ext13_dir, fn)
        if os.path.isfile(fp):
            EXT13[fn] = os.path.getsize(fp)

# ---------------------------------------------------------------- 通用统计函数
def numkeys(d):
    ks = []
    for k in d.keys():
        try:
            ks.append(int(float(k)))
        except (TypeError, ValueError):
            pass
    return ks

def stat_dict_intkeys(d):
    """键即 ID 的字典：返回 (count, (min,max))"""
    ks = numkeys(d)
    return len(d), ((min(ks), max(ks)) if ks else None)

def stat_list_id(lst, fields=('id', 'bid')):
    vals = []
    for it in lst:
        if isinstance(it, dict):
            for f in fields:
                if f in it and isinstance(it[f], (int, float)):
                    vals.append(int(it[f])); break
    return len(lst), ((min(vals), max(vals)) if vals else None)

def load_json(path):
    return json.load(io.open(path, 'r', encoding='utf-8'))

# ---------------------------------------------------------------- 手动登记表（每行一个数据类别/表）
# rule 取值：
#   dict_intkeys            : 顶层 dict，键即 ID
#   list_id                 : 顶层 list[dict]，取 id/bid 字段
#   nested(name, subkey)     : 顶层 dict，有效数据在 d[subkey]（dict 或 list）
#   multitable              : 顶层 dict = 若干子表，逐个子表计数
#   skill_rows              : list[list]，行内第 2 列=技能 ID
#   item_dict               : server/item_config.json 专用（dict，值含 type/bid）
#   regex_id                : 文件本身不可解析，用正则统计 "id" 出现次数
#   runtime_config          : 运行时配置（非游戏数据表）
#   cfgtable                : server/cfg/*.json 通用解构表
ROWS = [
    # ============================ 物品 / 装备 / 宝石 / 魂骨 / 时装 ============================
    dict(id='item_main', categories=['物品'], luac='config_item.luac',
         name='物品主表（全物品字典）', source='server/item_config.json',
         method='tools/extract_item_v2.py / extract_config_item.py（1.4.11 客户端提取）',
         rule='item_dict',
         field_meaning='bid=物品ID；name=名称；type=物品分类编号；lev=使用等级；quality=品质；bind_type=绑定类型；overlap=可叠加数量；durable=耐久；use_type=使用效果类型',
         conf='VERIFIED',
         missing='type→分类中文名映射未成文（仅有采样对照，如11=物攻石、100=武器、201=男时装）'),
    dict(id='item_equipment', categories=['装备'], luac='config_item.luac',
         name='装备类物品（item_config 中装备 type 分组）', source='server/item_config.json',
         method='对 item_config.json 按 type 聚合统计（本脚本实时计算）',
         rule='eq_group',
         field_meaning='type 100=武器/103=腰带/104=帽子/105=衣服/106=护手/107=靴子；type 240-246=魂师套装六部位+武器',
         conf='VERIFIED',
         missing='装备基础属性（+0 白装数值）不在物品表内，由公式或未识别表决定（见 truth_values/monster_values 取证）'),
    dict(id='item_gem', categories=['宝石'], luac='config_item.luac',
         name='宝石类物品（item_config type 11-19 分组）', source='server/item_config.json',
         method='对 item_config.json 按 type 聚合统计（本脚本实时计算）',
         rule='gem_group',
         field_meaning='11=物攻石/13=物防石/14=法防石/15=气血石/16=速度石/19=暴击石；镶嵌系统见 config_jewel 相关脚本证据（gem_inlay_spec.md）',
         conf='LIKELY',
         missing='无独立宝石属性表（truth_values: NO_SEPARATE_GEM_TABLE）；type 12/20 采样呈纯数字，疑似货币，未计入宝石组'),
    dict(id='item_hungu', categories=['魂骨'], luac='config_item.luac',
         name='魂骨类物品（item_config type 108/120/121/22 分组）', source='server/item_config.json',
         method='对 item_config.json 按 type 聚合统计（本脚本实时计算）',
         rule='hungu_group',
         field_meaning='108=魂骨（如碧莲魂骨）；120/121=高级魂骨（瀚海头骨/妖眼树盾）；22=魂骨碎片',
         conf='LIKELY',
         missing='魂骨强化/进阶规则表未在已提取清单中定位'),
    dict(id='item_fashion', categories=['时装'], luac='config_fashion.luac',
         name='时装表（客户端解构）+ 时装类物品', source='server/cfg/config_fashion.json',
         method='1.4.11 luac 批量解构产物（server/cfg/ 语料）；物品侧类型见 item_config type 201/255',
         rule='cfgtable',
         field_meaning='时装外观/进阶配置；item_config 中 type 201=庆典夏日时装·男等',
         conf='PARTIAL',
         missing='未逐条统计时装表条目数（通用统计）；时装进阶消耗表 config_fashion_up.json 仅 2 字节（空表）'),
    dict(id='item_currency', categories=['货币类型'], luac='config_item.luac',
         name='货币类物品（item_config type 0/12/20 疑似分组）', source='server/item_config.json',
         method='对 item_config.json 按 type 聚合统计（本脚本实时计算）',
         rule='currency_group',
         field_meaning='type 0=幸运币（bid 28030）；type 12/20 条目 name 字段为纯数字（bid 11/3200），疑似货币/经验券占位',
         conf='UNVERIFIED',
         missing='货币类型枚举表未找到；服务端代码中 coin/hero_coin/vip_exp 等账目与物品 bid 的对应关系未成文'),

    # ============================ 技能 / 伙伴 / 命格 ============================
    dict(id='skill_raw', categories=['技能'], luac='config_skill_xiulian.luac',
         name='技能原始表（4000 行结构化数组）', source='server/_skill_raw.json',
         method='临时提取脚本产物（未定位唯一脚本；luac 源表疑似 config_skill_xiulian.luac，待核）',
         rule='skill_rows',
         field_meaning='行数组：idx1=技能ID；idx2=技能名（普攻/治疗等）；idx19=效果描述（如"造成250%伤害"）；其余字段语义未逐列定义',
         conf='PARTIAL',
         missing='列语义未完全定义；学习/升级消耗字段不存在（truth_values: NOT_FOUND_IN_CONFIG）'),
    dict(id='partner_main', categories=['伙伴'], luac='config_partner_base.luac',
         name='伙伴主表（伙伴名册）', source='server/partner_config.json',
         method='临时脚本产物（53 伙伴，与 _partner_base.json 同源）；源 luac 疑似 config_partner_base.luac',
         rule='list_id',
         field_meaning='bid=伙伴ID（33100 起）；name=名称（唐舞桐等）；career=职业；score=战力评分；take_lev=携带等级；mode=模式',
         conf='VERIFIED',
         missing='伙伴技能/羁绊/神器子表见 cfg/config_partner_skill.json(309KB)/config_partner_fetter.json(60KB)，未逐条统计'),
    dict(id='partner_base', categories=['伙伴'], luac='config_partner_base.luac',
         name='伙伴基础档案（含外观/性别/描述）', source='server/_partner_base.json',
         method='临时脚本产物；tools/verify_partner_list.py 可复算',
         rule='list_id',
         field_meaning='name/score/career/bid/die_effect=死亡特效E码/by_resource=立绘H码/is_deity=是否神级/height=身高/desc=描述',
         conf='VERIFIED',
         missing='—'),
    dict(id='mingge_cfg', categories=['命格'], luac='config_mingge.luac',
         name='命格配置（开/阶/其他子表）', source='server/_mingge_cfg.json',
         method='tools/_fix_r111_mingge.py 落盘修复（源自 config_mingge.luac 解构）',
         rule='multitable',
         field_meaning='MinggeOther/MinggeOpen/MinggeStage 三个子表（开服条件、阶段、附加规则）',
         conf='LIKELY',
         missing='子表逐行语义未逐条成文'),

    # ============================ 成长线 ============================
    dict(id='attr_data', categories=['属性字段'], luac='config_attr.luac',
         name='属性ID↔字段名映射表', source='server/_attr_data.json',
         method='config_attr.luac 提取；tools/_fix_r92_14099.py 引用',
         rule='multitable',
         field_meaning='AttrId2Key/AttrKey2Id/AttrId2Str/AttrKey2Str：属性ID↔字段名↔展示名；AttrPower=战力换算系数（atk_speed 450、hp_max 24 等，见 truth_values）',
         conf='VERIFIED',
         missing='—'),
    dict(id='attr_meta', categories=['属性字段'], luac='config_attr.luac',
         name='属性数组元数据（向量长度）', source='server/_attr_meta.json',
         method='临时提取脚本产物',
         rule='nested(attr_meta, items)',
         field_meaning='attr_len=属性向量长度（64）；items=逐属性说明',
         conf='PARTIAL',
         missing='items 条目逐属性含义未逐条核对'),
    dict(id='role_career', categories=['角色职业'], luac='config_role_career.luac',
         name='职业配置表（客户端解构）', source='server/cfg/config_role_career.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='职业相关配置（具体字段以解构 JSON 为准）',
         conf='UNVERIFIED',
         missing='未逐条统计；职业 ID 与伙伴 career 字段（1-4）对应关系未成文'),
    dict(id='role_attr', categories=['等级经验'], luac='config_role_attr.luac',
         name='角色等级经验表（RoleAttr，200 级）', source='server/cfg/config_role_attr.json',
         method='1.4.11 luac 批量解构产物；truth_values.json 已确认 200 级经验曲线',
         rule='cfgtable',
         field_meaning='exp_max=本级所需经验；exp_total=累计经验；L1=240、L70=2,577,419、L200=1,917,555,775（取证值）',
         conf='VERIFIED',
         missing='—'),
    dict(id='intensify', categories=['强化材料'], luac='config_intensify.luac',
         name='装备强化数值表（成功率/消耗/奖励）', source='server/cfg/config_intensify.json',
         method='1.4.11 luac 批量解构产物；truth_values.json CONFIRMED',
         rule='cfgtable',
         field_meaning='IntensifyReward=8-15 级单件加成（+8 武器 atk_s+20）；IntensifyAllReward=6-8 阶套装加成；强化石 bid=36006；消耗金币每级递增 2000',
         conf='VERIFIED',
         missing='—'),

    # ============================ 系统表（翅膀/神器/阵法/增幅/时装补充） ============================
    dict(id='wing_data', categories=['翅膀'], luac='config_wing_data.luac',
         name='翅膀数据（客户端解构）', source='server/cfg/config_wing_data.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='翅膀外观/进阶/属性配置（具体字段以解构 JSON 为准）',
         conf='UNVERIFIED',
         missing='未逐条统计；翅膀系统消费曲线未成文'),
    dict(id='shenqi', categories=['神器'], luac='config_shenqi.luac',
         name='神器表（客户端解构，574KB）', source='server/cfg/config_shenqi.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='神器列表/成长配置（具体字段以解构 JSON 为准）',
         conf='UNVERIFIED',
         missing='未逐条统计'),
    dict(id='formation', categories=['阵法'], luac='config_formation.luac',
         name='阵法表（客户端解构）', source='server/cfg/config_formation.json',
         method='1.4.11 luac 批量解构产物；_cfg_formation.txt 探针证据',
         rule='cfgtable',
         field_meaning='阵法激活/属性加成配置',
         conf='UNVERIFIED',
         missing='未逐条统计'),
    dict(id='buff_data', categories=['增幅'], luac='config_buff_data.luac',
         name='Buff/增幅数据表（客户端解构，102KB）', source='server/cfg/config_buff_data.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='Buff 效果/持续时间/叠加规则（本类别映射为推断："增幅"在项目中无独立命名表）',
         conf='UNVERIFIED',
         missing='"增幅"类别无直接命名证据；映射到 buff_data 为最佳推断，需人工确认'),

    # ============================ 怪物 / NPC / 地图 ============================
    dict(id='mon_data', categories=['怪物'], luac='config_mon_data.luac',
         name='怪物表（1.4.11 解构部分失败；1.4.9 参考 2645 怪）', source='server/cfg/config_mon_data.json',
         method='1.4.11 解构产物仅 311 字节（主表空）；1.4.9 完整参考：analysis/1.4.9/task/config_mon.json（818,547 字节，2645 条）',
         rule='mon_row',
         field_meaning='24 元素数组：idx1=怪名(601种)/idx2=等级(1-150)/idx3=类型(0普通1389/1普通1205/4精英BOSS51)/idx8=资源ID/idx21=战斗数值倍率(0.7-15x)/idx23=掉落层(0/2/4/6/8)；无显式 HP/ATK 字段',
         conf='PARTIAL',
         missing='1.4.11 主表解构失败；怪物 HP/ATK 由服务端公式计算，静态不可得'),
    dict(id='npc_main', categories=['NPC'], luac='config_npc.luac',
         name='NPC 主表（客户端解构，195KB）', source='server/cfg/config_npc.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='NPC 列表/对话/功能入口配置',
         conf='UNVERIFIED',
         missing='未逐条统计'),
    dict(id='npcs_10001', categories=['NPC'], luac='config_npc.luac',
         name='单地图 NPC 坐标快照（地图10001，提取残缺）', source='server/_npcs_10001.json',
         method='临时脚本产物；文件在第 163 行截断（尾部 "id": 后缺内容）',
         rule='regex_id',
         field_meaning='id/bid=NPC编号(10001-10081)；x/y=坐标；name=npc<id>；另有两条哨兵记录 id=Config/MapNpc',
         conf='FAILED',
         missing='JSON 不可解析；仅能按 "id" 出现次数统计（21 次=19 个数值 NPC + 2 哨兵）；真实条数可能更多'),
    dict(id='mapnpc_10001', categories=['NPC', '地图场景'], luac='config_map_npc.luac',
         name='地图 NPC 放置表（地图10001）', source='server/_mapnpc_10001.json',
         method='临时脚本产物（对应 extract_map_npc.py 路线）',
         rule='list_id',
         field_meaning='id/bid=NPC编号；type=类型；x/y=格子坐标；name=NPC名',
         conf='LIKELY',
         missing='仅覆盖地图 10001 一张图'),
    dict(id='map_block', categories=['地图场景'], luac='config_map_block.luac',
         name='地图遮挡/通行块数据', source='server/map_block.json',
         method='tools/extract_config_mapblock.py 提取',
         rule='nested(map_block, scenes)',
         field_meaning='_meta.source/polarity/blocked_chars；scenes=逐场景遮挡统计（cells_total/cells_blocked/blocked_ratio）',
         conf='VERIFIED',
         missing='—'),
    dict(id='map_main', categories=['地图场景'], luac='config_map.luac',
         name='地图主表（客户端解构，83KB）', source='server/cfg/config_map.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='地图列表/进出/出生点配置',
         conf='UNVERIFIED',
         missing='未逐条统计'),

    # ============================ 任务 / 副本 ============================
    dict(id='mission_main', categories=['任务'], luac='config_mission.luac',
         name='任务主表（全任务字典）', source='server/mission_config.json',
         method='tools/extract_mission_config.py 提取',
         rule='dict_intkeys',
         field_meaning='bid=任务ID；type/show_type=任务类型；career=适用职业；accept_npc_id=接取NPC；accept_talk/commit_talk/process_talk=对话；auto_commit=自动完成',
         conf='VERIFIED',
         missing='—'),
    dict(id='mission_route', categories=['任务'], luac='config_mission.luac',
         name='任务链/主线路由表', source='server/_mission_route.json',
         method='临时脚本产物（键 35000 段，与主表互补）',
         rule='dict_intkeys',
         field_meaning='name=名称；type=类型；realm=界；lev=等级；desc=描述',
         conf='LIKELY',
         missing='与 config_mission.luac 的确切子表对应关系未定位'),
    dict(id='dungeon_single_tower', categories=['副本'], luac='config_single_tower.luac',
         name='单人爬塔副本表', source='server/cfg_config_single_tower.json',
         method='临时脚本产物（源 luac 疑似 config_single_tower.luac）',
         rule='dict_intkeys',
         field_meaning='键=层/关ID；值=该层怪物/奖励列表',
         conf='VERIFIED',
         missing='—'),
    dict(id='dungeon_tower', categories=['副本'], luac='config_dungeon_tower.luac',
         name='妖塔/多层副本表', source='server/cfg_config_dungeon_tower.json',
         method='临时脚本产物',
         rule='dict_intkeys',
         field_meaning='键=关ID；值=配置数组',
         conf='VERIFIED',
         missing='—'),
    dict(id='dungeon_corpus', categories=['副本'], luac='config_dungeon_new.luac',
         name='副本群解构语料（config_dungeon_* 系列）', source='server/cfg/config_dungeon_new.json',
         method='1.4.11 luac 批量解构产物',
         rule='cfgtable',
         field_meaning='副本列表/奖励/进入条件（另有 config_dungeon_tower.json/gods.json/rune.json/seal_demon_data.json/vip_single*.json）',
         conf='UNVERIFIED',
         missing='未逐条统计'),

    # ============================ 商城 / 礼包 ============================
    dict(id='mall_main', categories=['商城商品'], luac='config_mall.luac',
         name='商城商品主表', source='server/mall_config.json',
         method='tools/extract_mall.py 提取',
         rule='list_id',
         field_meaning='id=商品位；item_bid=商品物品；pay_type=支付货币类型；price=价格；limit_week/limit_day_cli=限购；cli_tag=客户端标签(HOT等)',
         conf='VERIFIED',
         missing='—'),
    dict(id='mall_zhenbao', categories=['商城商品'], luac='config_mall.luac',
         name='珍宝阁商品（实现回退数据）', source='server/mall_zhenbao.json',
         method='实现回退（source 字段=IMPLEMENTATION_FALLBACK_v2），非客户端配置直提',
         rule='list_id',
         field_meaning='id/item_bid/item_name/price/limit_num/buy_num',
         conf='PARTIAL',
         missing='非原版配置真值；原版珍宝阁配方是否在 APK 内未确认'),
    dict(id='mall_exchange', categories=['商城商品', '奖励'], luac=None,
         name='商城兑换配方（APK 内无此表，实现回退）', source='server/mall_exchange.json',
         method='实现回退（source 字段=IMPLEMENTATION_FALLBACK）；backup 注释明确"原版兑换配方不在 APK 内"',
         rule='list_id',
         field_meaning='id/item_bid=消耗物品；new_item_bid/new_item_num=产出；limit_num=限购',
         conf='PARTIAL',
         missing='非原版配置真值；config_exchange.json(40KB) 解构表存在但未与该文件对齐'),
    dict(id='item_gift', categories=['礼包'], luac='config_item_gift.luac',
         name='物品礼包内容表', source='server/item_gift.json',
         method='tools/extract_item_gift.py 提取',
         rule='dict_intkeys',
         field_meaning='键=礼包ID；值=物品列表（bid/数量数组）',
         conf='VERIFIED',
         missing='—'),

    # ============================ 活动 / 奖励 ============================
    dict(id='richang', categories=['活动'], luac='config_richang.luac',
         name='日常任务/活跃表', source='server/_richang.json',
         method='tools/extract_richang.py 提取',
         rule='nested(richang, tasks)',
         field_meaning='tasks=日常任务列表；kezhi=克制/规则子表',
         conf='VERIFIED',
         missing='—'),
    dict(id='guaji', categories=['活动'], luac='config_guaji.luac',
         name='挂机地图列表', source='server/_guaji.json',
         method='tools/extract_guaji.py 提取',
         rule='nested(guaji, spots)',
         field_meaning='spots=挂机区域（星斗大森林等 8 区，level_range 25-34、map_bid、mon_bid）',
         conf='VERIFIED',
         missing='每分钟收益速率不在配置表（truth_values: NOT_IN_CONFIG）'),
    dict(id='drop', categories=['奖励'], luac='config_drop.luac',
         name='掉落组表', source='server/cfg_drop.json',
         method='tools/extract_drop.py 提取',
         rule='dict_intkeys',
         field_meaning='键=掉落组ID(20001段)；值=[{coin, normal:[{item,num,pp}], core, first}]；pp=概率点（池内归一）',
         conf='VERIFIED',
         missing='—'),
    dict(id='chengjiu', categories=['奖励'], luac='config_chengjiu.luac',
         name='成就表', source='server/_chengjiu.json',
         method='tools/extract_chengjiu.py 提取',
         rule='nested(chengjiu, items)',
         field_meaning='items=成就条目字典（10100 段分组）',
         conf='VERIFIED',
         missing='—'),
    dict(id='chengjiu_map', categories=['奖励'], luac='config_chengjiu.luac',
         name='成就分组映射（手工整理）', source='server/_chengjiu_map.json',
         method='手工映射产物（groups 分组清单）',
         rule='nested(chengjiu_map, groups)',
         field_meaning='groups=成就分组列表（43 组）',
         conf='LIKELY',
         missing='分组为人工整理，与原版分组定义对应关系未逐条验证'),

    # ============================ 其他（运行时/派生） ============================
    dict(id='runtime_config', categories=['其他'], luac='config.luac',
         name='服务端连接运行时配置（非游戏数据表）', source='server/config.json',
         method='mock_server 运行配置（bind/host/http_port/game_port/server_list）',
         rule='runtime_config',
         field_meaning='bind=监听地址；host=模拟器回环 10.0.2.2；http_port=8080；game_port=9000',
         conf='VERIFIED',
         missing='—'),
    dict(id='runtime_npcs_mislabel', categories=['其他'], luac=None,
         name='"config_21npcs.json"（命名误导：实为服务端运行配置，非 NPC 表）', source='server/config_21npcs.json',
         method='直接读文件核实：内容为 bind/host/server_list 运行配置，与 21 个 NPC 无关',
         rule='runtime_config',
         field_meaning='bind/host/http_port/game_port/server_list[].ip/port/state',
         conf='VERIFIED',
         missing='文件名与内容不符的原因（历史命名）未追溯'),
    dict(id='answer_key', categories=['活动'], luac='config_answer.luac',
         name='答题答案表（项目手工推导）', source='server/answer_key.json',
         method='手工推导（server/answer/service.py 注释：项目自定义推导键，依据题面推导）',
         rule='nested(answer_key, answers)',
         field_meaning='answers=题目→答案映射；_meta.provenance/reason/evidence_level',
         conf='PARTIAL',
         missing='非客户端 config_answer.luac 直提；与原版答案一致性未验证'),
    dict(id='promote', categories=['等级经验'], luac='config_promote.luac',
         name='转生/晋升表', source='server/_promote.json',
         method='tools/extract_promote.py 提取',
         rule='nested(promote, items)',
         field_meaning='items=晋升配置列表；tips=提示文案',
         conf='VERIFIED',
         missing='—'),
    dict(id='rune_cfg', categories=['阵法'], luac='config_rune_data.luac',
         name='符文配置（交换/静态/基础三子表）', source='server/_rune_cfg.json',
         method='tools/_fix_r109_rune_exchange.py 落盘修复（源自 config_rune_data.luac 1.7MB 解构）',
         rule='multitable',
         field_meaning='RuneExchange=兑换配方；RuneStatic=静态属性；RuneBase=基础数据',
         conf='LIKELY',
         missing='—'),
    dict(id='invest_cfg', categories=['活动'], luac='config_invest.luac',
         name='投资计划配置（6 子表）', source='server/_invest_cfg.json',
         method='tools/_fix_r107_invest.py 落盘修复',
         rule='multitable',
         field_meaning='InvestType/AllFanhuan/DayInvest/LevInvest 等子表',
         conf='LIKELY',
         missing='—'),
    dict(id='skill_talent', categories=['技能'], luac='config_skill_talent.luac',
         name='技能天赋表（客户端解构）', source='server/cfg/config_skill_talent.json',
         method='1.4.11 luac 批量解构产物；truth_values 确认仅 name/bid/skill_group 字段，无消耗字段',
         rule='cfgtable',
         field_meaning='name/bid/skill_group/skill_talent/magic_talent；无 gold/coin/item 消耗字段',
         conf='VERIFIED',
         missing='技能学习/升级消耗在配置表中不存在'),
]

# ---------------------------------------------------------------- 统计执行
def abs_path(rel):
    return os.path.join(ROOT, rel.replace('/', os.sep))

def stat_row(row):
    """返回 (count, id_range, note)"""
    rel = row['source']
    p = abs_path(rel)
    rule = row['rule']
    if rule == 'item_dict':
        d = load_json(p)
        n, rng = stat_dict_intkeys(d)
        return n, rng, None
    if rule == 'dict_intkeys':
        d = load_json(p)
        n, rng = stat_dict_intkeys(d)
        return n, rng, None
    if rule in ('list_id',):
        d = load_json(p)
        return stat_list_id(d) + (None,)
    if rule.startswith('nested('):
        sub = rule.split(',')[1].rstrip(')').strip()
        d = load_json(p)
        subv = d.get(sub)
        if isinstance(subv, dict):
            n, rng = stat_dict_intkeys(subv)
            return n, rng, '子表 ' + sub
        if isinstance(subv, list):
            return stat_list_id(subv) + ('子表 ' + sub,)
        return 0, None, '子表缺失: ' + sub
    if rule == 'multitable':
        d = load_json(p)
        total = 0; ks_all = []
        for k, v in d.items():
            if isinstance(v, dict):
                total += len(v); ks_all += numkeys(v)
            elif isinstance(v, list):
                total += len(v)
        return total, ((min(ks_all), max(ks_all)) if ks_all else None), '子表合计'
    if rule == 'skill_rows':
        d = load_json(p)
        ids = [r[1] for r in d if isinstance(r, list) and len(r) > 1 and isinstance(r[1], (int, float))]
        return len(d), ((min(ids), max(ids)) if ids else None), '行内第2列=技能ID'
    if rule == 'regex_id':
        s = io.open(p, 'r', encoding='utf-8', errors='replace').read()
        ids = re.findall(r'"id":\s*(\d+)', s)
        return len(ids), ((min(int(i) for i in ids), max(int(i) for i in ids)) if ids else None), '正则统计（文件截断，JSON 不可解析）'
    if rule == 'runtime_config':
        d = load_json(p)
        return len(d), None, '运行配置项数（非数据表）'
    if rule == 'mon_row':
        # 1.4.11 部分失败 + 1.4.9 参考
        ref = os.path.join(ROOT, 'analysis', '1.4.9', 'task', 'config_mon.json')
        n = os.path.getsize(ref)
        return None, None, '1.4.11 主表空（311B）；1.4.9 参考 2645 条（见 monster_values.json）'
    if rule == 'cfgtable':
        try:
            d = load_json(p)
        except Exception as e:
            return 0, None, '解析失败: %s' % e
        if isinstance(d, dict):
            sub = 0; ks_all = []
            for v in d.values():
                if isinstance(v, dict):
                    sub += len(v); ks_all += numkeys(v)
                elif isinstance(v, list):
                    sub += len(v)
            # 若顶层值全是子容器，则数据条数=子表条目合计；否则=顶层键数
            if sub > 0:
                return sub, ((min(ks_all), max(ks_all)) if ks_all else None), '顶层子表%d个；条目合计%d' % (len(d), sub)
            return len(d), None, '顶层键%d个（无子容器）' % len(d)
        if isinstance(d, list):
            return len(d), None, '顶层列表'
        return 1, None, '标量'
    # 物品分组统计（基于 item_config.json 实时聚合）
    d = load_json(os.path.join(SERVER, 'item_config.json'))
    by_type = collections.Counter()
    bid_by_type = collections.defaultdict(list)
    for v in d.values():
        if isinstance(v, dict):
            by_type[v.get('type')] += 1
            try: bid_by_type[v.get('type')].append(int(v.get('bid')))
            except (TypeError, ValueError): pass
    if rule == 'eq_group':
        ts = {100, 103, 104, 105, 106, 107} | set(range(240, 247))
    elif rule == 'gem_group':
        ts = {t for t in by_type if isinstance(t, int) and 11 <= t <= 19}
    elif rule == 'hungu_group':
        ts = {108, 120, 121, 22}
    elif rule == 'currency_group':
        ts = {0, 12, 20}
    else:
        ts = set()
    bids = [b for t in ts if t in bid_by_type for b in bid_by_type[t]]
    cnt = sum(by_type.get(t, 0) for t in ts)
    return cnt, ((min(bids), max(bids)) if bids else None), 'type=%s 分组合计' % sorted(t for t in ts if t in by_type)

# ---------------------------------------------------------------- config_files 存在性
def presence(luac):
    out = {}
    if not luac:
        return {v: [] for v in VERSIONS}, None
    for v in VERSIONS:
        out[v] = [luac] if luac in CT[v] else []
    ext = EXT13.get(luac)
    return out, ext

# ---------------------------------------------------------------- 组装记录
records = []
for row in ROWS:
    try:
        count, rng, note = stat_row(row)
    except Exception as e:
        count, rng, note = None, None, '统计异常: %s' % e
    pres, ext13_size = presence(row['luac'])
    present_versions = [v for v in VERSIONS if pres[v]]
    missing_versions = [v for v in VERSIONS if not pres[v]]
    vdiff = '存在于: %s；缺失: %s。数量仅 1.4.11 已统计；旧版本数量 UNKNOWN。' % (
        '/'.join(present_versions) if present_versions else '无',
        '/'.join(missing_versions) if missing_versions else '无')
    if row['source'].endswith('config_mon_data.json'):
        vdiff = '三版本均有 config_mon_data.luac（存在性见清单）；1.4.11 解构主表失败，1.4.9 参考 2645 条；1.3.0 数量 UNKNOWN。'
    rec = {
        'data_id': row['id'],
        'category': row['categories'],
        'name': row['name'],
        'config_files': pres,
        'source_file': row['source'],
        'extraction_method': row['method'],
        'field_meaning': row['field_meaning'],
        'id_range': {'min': rng[0], 'max': rng[1]} if rng else None,
        'count': count,
        'count_evidence': 'VERIFIED(1.4.11实际提取)' if row['conf'] in ('VERIFIED', 'LIKELY') and count is not None else ('UNKNOWN' if count is None else row['conf']),
        'version_diff': vdiff,
        'parse_confidence': row['conf'],
        'evidence': '%s%s%s' % (
            row['source'],
            ('（1.3.0 落盘证据: %s, %d 字节）' % (os.path.join('analysis','version_compare','1.3.0','extracted','config',row['luac']), ext13_size)) if ext13_size else '',
            ('；统计注记: %s' % note) if note else ''),
        'missing_information': row['missing'],
    }
    records.append(rec)

# ---------------------------------------------------------------- 类别覆盖检查
ALL_CATS = ['角色职业','等级经验','属性字段','货币类型','物品','装备','强化材料','宝石','技能',
            '伙伴','翅膀','魂骨','时装','增幅','神器','命格','阵法','怪物','NPC','地图场景',
            '任务','副本','商城商品','礼包','活动','奖励','其他']
covered = collections.defaultdict(list)
for r in records:
    for c in r['category']:
        covered[c].append(r['data_id'])
uncovered = [c for c in ALL_CATS if c not in covered]

# 未确认项清单
unconfirmed = [r['data_id'] for r in records if r['parse_confidence'] in ('UNVERIFIED', 'FAILED', 'PARTIAL') or r['count'] is None]

payload = {
    'meta': {
        'title': '绝世唐门 PHASE C0 数据资源总目录（只读审计）',
        'generated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'generator': 'tools/jstm_audit/gen_data_inventory.py',
        'version_scope': '数量/ID范围仅代表 1.4.11（VERIFIED 级提取）；1.3.0/1.4.9 仅有 config_tables 存在性证据',
        'config_tables_counts': {v: len(CT[v]) for v in VERSIONS},
        'ext13_on_disk_files': len(EXT13),
        'evidence_levels': 'VERIFIED / LIKELY / PARTIAL / UNVERIFIED / FAILED',
    },
    'category_coverage': {c: covered.get(c, []) for c in ALL_CATS},
    'uncovered_categories': uncovered,
    'records': records,
    'unconfirmed_items': unconfirmed,
}

os.makedirs(OUT_DIR, exist_ok=True)
json_path = os.path.join(OUT_DIR, 'data_inventory.json')
with io.open(json_path, 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- 渲染 MD
lines = []
A = lines.append
A('# 绝世唐门 PHASE C0 数据资源总目录（只读审计）')
A('')
A('- 生成时间：%s' % payload['meta']['generated'])
A('- 生成器：`tools/jstm_audit/gen_data_inventory.py`（可重复运行）')
A('- 数量与 ID 范围：**仅代表 1.4.11**（已提取 VERIFIED 级数据）；1.3.0 / 1.4.9 仅标注 config_tables 清单存在性，旧版本数量一律 UNKNOWN。')
A('- 三版本 config_tables 清单规模：1.3.0=%d 张 / 1.4.9=%d 张 / 1.4.11=%d 张；1.3.0 落盘证据目录文件数=%d。' % (len(CT['1_3_0']), len(CT['1_4_9']), len(CT['1_4_11']), len(EXT13)))
A('- 证据五档：VERIFIED / LIKELY / PARTIAL / UNVERIFIED / FAILED。')
A('')
A('## 类别覆盖统计')
A('')
A('| 类别 | 条目数 | 条目 data_id |')
A('|---|---|---|')
for c in ALL_CATS:
    ids = covered.get(c, [])
    A('| %s | %d | %s |' % (c, len(ids), ', '.join(ids) if ids else '—（无证据）'))
A('')
if uncovered:
    A('**未覆盖类别**：%s' % '、'.join(uncovered))
else:
    A('**全部 %d 个类别均有证据行**。' % len(ALL_CATS))
A('')
A('## 明细（按类别分组）')
A('')
for c in ALL_CATS:
    rows = [r for r in records if c in r['category']]
    if not rows:
        A('### %s' % c)
        A('')
        A('_无证据行（UNKNOWN）_')
        A('')
        continue
    A('### %s' % c)
    A('')
    A('| data_id | 名称 | source_file | count | id_range(1.4.11) | 存在性 1.3.0/1.4.9/1.4.11 | 置信 |')
    A('|---|---|---|---|---|---|---|')
    for r in rows:
        p = r['config_files']
        pres_str = '%s/%s/%s' % (
            '✓' if p['1_3_0'] else '—',
            '✓' if p['1_4_9'] else '—',
            '✓' if p['1_4_11'] else '—')
        cnt = r['count'] if r['count'] is not None else 'UNKNOWN'
        ir = r['id_range']
        ir_s = ('%d ~ %d' % (ir['min'], ir['max'])) if ir else '—'
        A('| %s | %s | `%s` | %s | %s | %s | %s |' % (
            r['data_id'], r['name'], r['source_file'], cnt, ir_s, pres_str, r['parse_confidence']))
    A('')
    A('<details><summary>该类条目溯源与字段说明</summary>')
    A('')
    for r in rows:
        A('- **%s（%s）**' % (r['data_id'], r['name']))
        A('  - 来源产物：`%s`' % r['source_file'])
        A('  - 提取方法：%s' % r['extraction_method'])
        A('  - 字段含义：%s' % r['field_meaning'])
        A('  - 版本差异：%s' % r['version_diff'])
        A('  - 证据：%s' % r['evidence'])
        A('  - 缺失信息：%s' % r['missing_information'])
    A('')
    A('</details>')
    A('')
A('## 未确认项清单')
A('')
for r in records:
    if r['data_id'] in unconfirmed:
        A('- `%s`（%s）：置信=%s；%s' % (r['data_id'], r['name'], r['parse_confidence'], r['missing_information']))
A('')
md_path = os.path.join(OUT_DIR, 'data_inventory.md')
with io.open(md_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

# ---------------------------------------------------------------- 自检输出
n_rows = len(records)
cats_with_data = sum(1 for c in ALL_CATS if covered.get(c))
print('JSON written:', json_path)
print('MD written  :', md_path)
print('rows        :', n_rows)
print('categories with data: %d / %d' % (cats_with_data, len(ALL_CATS)))
print('uncovered   :', uncovered)
print('unconfirmed :', len(unconfirmed))
# json.load 自检
json.load(io.open(json_path, 'r', encoding='utf-8'))
print('self-check  : json.load OK')
