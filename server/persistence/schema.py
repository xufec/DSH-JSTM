# -*- coding: utf-8 -*-
"""persistence.schema —— 集中 DB schema 管理壳（Phase 2 step 0，只读）。

设计依据：phase2_design.md §五（55 张表映射）、§九 风险 3（schema 漂移）。

★ 本步纪律：
  - **只收集清单**：把 mock_server.py 中 db_init() 与各 db_*_init() 的
    CREATE TABLE 语句位置登记在 SCHEMA_MANIFEST（表名 -> 源行号）。
  - **导出黄金 schema**：server/backup/schema_golden.sql（从 roles.db 只读导出）。
  - **不改动 db_init() 的执行**：运行时建表仍 100% 走 mock_server.py 原逻辑。

后续批次（step 1 之后）再把这些 CREATE TABLE 物理收敛到本文件，并在启动时
与黄金 schema 比对，防止搬迁漏表。
"""

import os

# 黄金 schema 快照（2026-10-02 step 0 从 state/roles.db 只读导出，55 表）。
_HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN_SCHEMA_PATH = os.path.normpath(
    os.path.join(_HERE, '..', 'backup', 'schema_golden.sql'))

# 表名 -> (mock_server.py 中的 CREATE TABLE 起始行号, 所属建库函数/区域)。
# 来源：对 mock_server.py grep `CREATE TABLE IF NOT EXISTS`（66 处命中，含幂等重复建表）。
# 55 表 = 54 用户表 + 1 sqlite_sequence（自增主键表，非本服务建）。
SCHEMA_MANIFEST = {
    # —— db_init() 主表（mock_server.py L4274–4322）——
    'roles':          (4277, 'db_init'),
    'accounts':        (4290, 'db_init'),
    'role_attr':      (4295, 'db_init'),
    'missions':        (4306, 'db_init'),
    'role_assets':     (4314, 'db_init'),
    'mall_bought':     (4318, 'db_init'),
    # —— 各 db_*_init() / 懒建库函数（行号为 CREATE TABLE 所在行）——
    'role_market_goods': (2078, 'market 区域'),
    'role_build':        (2253, 'db_build_state 区域'),
    'role_build_learn':  (2255, 'db_build_state 区域'),
    'role_mail':         (2423, 'db_mail_init'),
    'role_point':        (2488, 'db_point_* 区域'),
    'role_tree':         (2818, 'db_tree_state 区域'),
    'arena_state':       (2941, 'arena_trophy 区域'),
    'role_qifu':         (2997, 'db_qifu_init'),
    'bag_items':         (5888, 'db_bag_init'),
    'bag_volume':        (6109, 'db_init_bag_volume'),
    'equip_items':       (6160, 'db_init_equip'),
    'store_items':       (6257, 'db_store_init'),
    'levgift_got':       (6343, 'db_init_levgift'),
    'dungeon_progress':  (6380, 'db_dung_init'),
    'arena_record':      (6443, 'db_arena_init'),
    'role_heros':        (6586, 'db_hero_init'),
    'role_form':         (6724, 'db_form_init'),
    'role_buffs':        (6765, 'db_buff_init'),
    'role_fabao':        (6969, 'db_fabao 区域'),
    'role_boss_kill':    (7054, 'rank/boss 区域'),
    'role_title':        (7078, 'db_title_add 区域'),
    'role_lingshou':     (7152, 'lingshou 区域'),
    'role_yuanshen':     (7186, 'yuanshen 区域'),
    'role_shenqi':       (7220, 'db_shenqi_init'),
    'role_mingge':       (7262, 'db_mingge_init'),
    'role_chair':        (7307, 'chair 区域'),
    'role_wing':         (7342, 'wing 区域'),
    'role_moments':      (7376, 'db_moment_add 区域'),
    'role_chat':         (7392, 'db_chat_add 区域'),
    'role_guild':        (7420, 'db_guild_init'),
    'role_team':         (7457, 'db_team_init'),
    'role_team_invite':  (7578, 'db_team_invite_init'),
    'role_jiebai':       (7635, 'db_jiebai_init'),
    'role_marry':        (7770, 'db_marry_init'),
    'role_marry_propose':(7831, 'db_marry_propose_init'),
    'role_fashion':      (7881, 'db_fashion_init'),
    'role_halo':         (7941, 'db_halo_init'),
    'role_halo_equip':   (7944, 'db_halo_init'),
    'role_market':       (8029, 'db_market_set 区域'),
    'role_invest':       (8107, 'db_invest_init'),
    'role_ride':         (8199, 'db_ride_init'),
    'role_runes':        (8345, 'db_rune_init'),
    'peakwar_state':     (8576, 'db_peakwar_init'),
    'race_state':        (8615, 'db_race_init'),
    'daily_progress':    (8720, 'db_daily_init'),
    'daily_lingqu':      (8723, 'db_daily_init'),
    'chengjiu_progress': (8809, 'db_chengjiu_init'),
    'guaji_state':       (8919, 'db_guaji_init'),
    'sign_got':          (9092, 'db_init_sign'),
}

# sqlite_sequence 由 SQLite 自增主键自动产生，非本服务 CREATE。
AUTO_TABLES = ('sqlite_sequence',)


def golden_schema_path():
    """返回黄金 schema sql 文件路径（只读快照）。"""
    return GOLDEN_SCHEMA_PATH


def table_count_baseline():
    """step 0 基线：用户表数（不含 sqlite_sequence）。"""
    return len(SCHEMA_MANIFEST)


def list_tables():
    """返回全部登记表名（有序）。"""
    return sorted(SCHEMA_MANIFEST.keys())


def describe():
    """返回只读清单文本，供启动自检/文档引用。不连库、不建表。"""
    lines = ['persistence.schema (step 0 read-only manifest):']
    lines.append('  golden schema: %s' % GOLDEN_SCHEMA_PATH)
    lines.append('  user tables: %d (+ %s auto)' % (
        table_count_baseline(), ', '.join(AUTO_TABLES)))
    for t in list_tables():
        ln, fn = SCHEMA_MANIFEST[t]
        lines.append('    %-22s <- mock_server.py L%d (%s)' % (t, ln, fn))
    return '\n'.join(lines)


if __name__ == '__main__':
    print(describe())
