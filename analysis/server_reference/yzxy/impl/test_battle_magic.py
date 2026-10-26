#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`battle_magic` 自测：线格式、状态机、与字节码规格的一致性。

运行：
    python test_battle_magic.py

覆盖：
  1. **线格式对拍**：本模块 `encode_magic_list` 的字节数/字段边界
     与 `tools/dsc_spec.py` 给出的格式串 `iiChhC` 逐字节对齐（含负值、边界值）；
  2. **独立解码回环**：`decode_magic_list(encode(...)) == 原值`；
  3. **配置表核验**：`SkillMagic` 行数、`SkillMagicType` 项数、抽样行的 `type`/`magic_desc` 自洽；
  4. **状态机**：施加 / 叠加 fold / duration 递减 / 到期移除 / 永久(255) / 瞬时(0) /
     `change_hp` 汇总 / 全量重列；
  5. **与真实 `SC_20013` 拼装**：把 `magic_list` 段嵌进 `server/battle.py` 的
     `build_20013` 字节流布局里，确认字段位置正确（用独立解析器逐字段取回）；
  6. **拒绝未知 bid**（不静默发送坏数据）。
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from battle_magic import (  # noqa: E402
    DURATION_INSTANT, DURATION_PERMANENT,
    FIGHT_TYPE_BAOJI, FIGHT_TYPE_HIT, FIGHT_TYPE_MISS,
    MagicEntry, MagicState, decode_magic_list, encode_hit, encode_magic_list,
    load_skill_magic, w_i8, w_i32, w_i16, w_str, w_u8, w_u16, w_u32,
)

PASS, FAIL = [], []


def check(name, cond, detail=''):
    (PASS if cond else FAIL).append(name)
    print('  %s %s%s' % ('[OK]  ' if cond else '[FAIL]', name,
                         ('  -> ' + detail) if (detail and not cond) else ''))


# ---------------------------------------------------------------------------
print('=' * 72)
print('1) 线格式边界（格式串 iiChhC = i32,i32,u8,i16,i16,u8 -> 14 字节）')
print('=' * 72)

check('单条 = 14 字节', MagicEntry(1).wire_size == 14
      and len(MagicEntry(1).encode()) == 14,
      'got %d' % len(MagicEntry(1).encode()))

# 0 条：仅 2 字节计数前缀
check('0 条 = u16 计数 0（2 字节）',
      encode_magic_list([]) == b'\x00\x00' and len(encode_magic_list([])) == 2)

# 1 条：2 + 14
check('1 条 = 16 字节', len(encode_magic_list([MagicEntry(1)])) == 16)

# 3 条：2 + 3*14
check('3 条 = 44 字节', len(encode_magic_list([MagicEntry(1), MagicEntry(2), MagicEntry(3)])) == 44)

# 负值必须用**有符号**编码
e_neg = MagicEntry(magic_bid=-12345, change_hp=-98765, duration=200, per=-300, val=-1234, fold=255)
raw = encode_magic_list([e_neg])
check('负 magic_bid/change_hp 用 int32 有符号',
      struct.unpack_from('>i', raw, 2)[0] == -12345
      and struct.unpack_from('>i', raw, 6)[0] == -98765)
check('duration/fold 为 uint8 全范围（200/255）',
      struct.unpack_from('>B', raw, 10)[0] == 200
      and struct.unpack_from('>B', raw, 15)[0] == 255,
      'duration@10=%d fold@15=%d' % (struct.unpack_from('>B', raw, 10)[0],
                                     struct.unpack_from('>B', raw, 15)[0]))
check('per/val 为 int16 有符号（偏移 11 / 13）',
      struct.unpack_from('>h', raw, 11)[0] == -300
      and struct.unpack_from('>h', raw, 13)[0] == -1234,
      'per=%d val=%d' % (struct.unpack_from('>h', raw, 11)[0],
                         struct.unpack_from('>h', raw, 13)[0]))

# 溢出保护
check('int32 溢出被夹取', struct.unpack_from('>i', encode_magic_list(
    [MagicEntry(2 ** 40)]), 2)[0] == 2147483647)
check('int16 溢出被夹取', struct.unpack_from('>h', encode_magic_list(
    [MagicEntry(1, per=99999)]), 11)[0] == 32767)

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('1b) ★ hit 是 FightType 枚举，不是伤害（附带发现，见 battle_magic 头注）')
print('=' * 72)

check('FightType = {0:MISS, 1:HIT, 2:BAOJI}（config_battle.luac proto#0）',
      (FIGHT_TYPE_MISS, FIGHT_TYPE_HIT, FIGHT_TYPE_BAOJI) == (0, 1, 2))
check('encode_hit(HIT) = 1 字节', encode_hit(FIGHT_TYPE_HIT) == b'\x01')
check('encode_hit(BAOJI) = 2 字节', encode_hit(FIGHT_TYPE_BAOJI) == b'\x02')
check('encode_hit(MISS) = 0 字节', encode_hit(FIGHT_TYPE_MISS) == b'\x00')
# 复现旧实现的 bug：把伤害当 hit
check('★ 复现 server/battle.py 的 bug：w_i8(772) 被静默夹到 127',
      w_i8(772) == b'\x7f', repr(w_i8(772)))
check('★ 复现 server/battle.py 的 bug：w_i8(-772) 被静默夹到 -128',
      w_i8(-772) == b'\x80', repr(w_i8(-772)))
try:
    encode_hit(772)
    check('encode_hit(772) 抛错（拒绝把伤害当命中结果）', False, 'no exception')
except ValueError as ex:
    check('encode_hit(772) 抛错（拒绝把伤害当命中结果）', True)
try:
    encode_hit(-128)
    check('encode_hit(-128) 抛错（夹取后的非法值同样被拒）', False, 'no exception')
except ValueError:
    check('encode_hit(-128) 抛错（夹取后的非法值同样被拒）', True)

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('2) 独立解码回环')
print('=' * 72)

cases = [
    [],
    [MagicEntry(1)],
    [MagicEntry(906001, change_hp=-100, duration=2, per=500, val=0, fold=1)],
    [MagicEntry(683140, 0, 2, 106, 0, 3),
     MagicEntry(1240, -50, 255, 0, 7, 255),
     MagicEntry(123456789, 987654321, 1, -1, -32768, 1)],
]
ok = True
for c in cases:
    enc = encode_magic_list(c)
    dec, off = decode_magic_list(enc)
    if off != len(enc) or [x.to_dict() for x in dec] != [x.to_dict() for x in c]:
        ok = False
        print('     mismatch: %r -> %r' % (c, dec))
check('全部 %d 例回环一致（且恰好消费完）' % len(cases), ok)

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('3) 配置表核验')
print('=' * 72)

try:
    T = load_skill_magic()
except IOError as ex:
    print('  [SKIP] 缺少 skill_magic.json：%s' % ex)
    print('         先运行: python extract_skill_magic.py')
    T = None

if T is not None:
    check('SkillMagicType = 31 项', T.type_count == 31, 'got %d' % T.type_count)
    check('SkillMagic ≈ 12664 行', T.count > 12000, 'got %d' % T.count)
    check('type_name(1010)=atk_s', T.type_name(1010) == 'atk_s')
    check('type_name(1240)=control', T.type_name(1240) == 'control')
    check('type_name(1250)=anti_control', T.type_name(1250) == 'anti_control')
    # 抽样：type=1240 的行 desc 应含「控制」
    r = T.get(683140)
    check('bid=683140 存在且 type=1240', bool(r) and T.type_id(683140) == 1240)
    check('bid=683140 的 magic_desc 含「控制」',
          '控制' in (r or {}).get('magic_desc', ''), repr((r or {}).get('magic_desc')))
    # 占位符替换
    d = T.describe(683140)
    check('describe 填充 {per}（含数字、无残留占位符）',
          '10.6' in d and '{' not in d, repr(d))
    # atk_s 抽样
    check('bid=906001 的 type=1010(atk_s)、per=500',
          T.type_id(906001) == 1010 and T.default_per(906001) == 500)
    # duration 分布存在且含 255
    dd = T._duration_dist
    check('duration 分布含 0/2/3/255',
          all(k in dd for k in ('0', '2', '3', '255')), str(dd))
    # duration=0 是多数（瞬时效果）
    check('duration=0 占比 > 40%', int(dd.get('0', 0)) / float(T.count) > 0.4)

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('4) 状态机')
print('=' * 72)

if T is not None:
    # 需要一个真实存在的 bid 来测；挑一个 duration>0 的
    dur_bids = [b for b in list(T._rows.keys())
                if T.default_duration(b) > 0 and T.default_duration(b) != DURATION_PERMANENT]
    perm_bids = [b for b in list(T._rows.keys()) if T.default_duration(b) == DURATION_PERMANENT]
    inst_bids = [b for b in list(T._rows.keys()) if T.default_duration(b) == DURATION_INSTANT]
    B = dur_bids[0]
    check('找到 duration>0 的样本 bid', bool(dur_bids), 'none')

    st = MagicState()
    e = st.apply(T, B)
    d0 = T.default_duration(B)
    check('apply 后 duration == 配置默认值', e is not None and e.duration == d0,
          'bid=%d dur=%d want=%d' % (B, e.duration if e else -1, d0))
    check('apply 后长度为 1', len(st) == 1)

    # 叠加 fold
    st.apply(T, B)
    check('重复施加 → fold 叠加到 2', st.find(B).fold == 2, 'fold=%d' % st.find(B).fold)
    check('叠加后长度仍为 1', len(st) == 1)

    # 递减：n 次 tick 后到期
    total_expired = []
    for i in range(d0):
        exp, hpd = st.tick()
        total_expired += exp
    check('经过 %d 次 tick 后到期移除' % d0,
          len(st) == 0 and len(total_expired) == 1)

    # 瞬时效果不入列表
    st2 = MagicState()
    r2 = st2.apply(T, inst_bids[0])
    check('duration=0（瞬时）→ 不入列表、返回 None', r2 is None and len(st2) == 0)

    # 永久不递减
    if perm_bids:
        st3 = MagicState()
        st3.apply(T, perm_bids[0])
        for _ in range(300):
            st3.tick()
        check('duration=255（永久）→ 300 次 tick 后仍在', len(st3) == 1)
    else:
        print('  [SKIP] 未找到 duration=255 样本')

    # change_hp 汇总（DoT）
    st4 = MagicState()
    e4 = st4.apply(T, B, change_hp=-120)
    e4.duration = 3
    exp, hpd = st4.tick()
    check('change_hp=-120 → 单条 tick 得 -120', hpd == -120, 'got %d' % hpd)
    e4.fold = 2
    # 重新造一条 fold=2 的
    st5 = MagicState()
    e5 = st5.apply(T, B, change_hp=-120, fold_add=2)
    exp5, hpd5 = st5.tick()
    check('fold=2 时 change_hp 按层数放大 → -240', hpd5 == -240, 'got %d' % hpd5)

    # 全量重列：两条都在 to_wire 里，且 duration 每回合下降
    st6 = MagicState()
    st6.apply(T, dur_bids[0])
    second = dur_bids[1] if len(dur_bids) > 1 else dur_bids[0]
    if second != dur_bids[0]:
        st6.apply(T, second)
    w1 = [x.to_dict() for x in st6.to_wire()]
    check('to_wire 给出全部在效效果（全量）', len(w1) == len(st6))
    st6.tick()
    w2 = [x.to_dict() for x in st6.to_wire()]
    check('tick 后 to_wire 仍全量且 duration 下降',
          len(w2) == len(w1) and all(
              (b['duration'] <= a['duration']) for a, b in zip(w1, w2)))

    # 未知 bid 必须抛错（不静默发坏数据）
    try:
        MagicState().apply(T, 999999999)
        check('未知 magic_bid 抛 KeyError', False, 'no exception')
    except KeyError:
        check('未知 magic_bid 抛 KeyError', True)

    # modifiers 汇总
    st7 = MagicState()
    st7.apply(T, 906001)          # type 1010 atk_s, per 500
    mods = st7.modifiers(T)
    check('modifiers 汇总出 atk_s', 'atk_s' in mods, str(mods))
    check('modifiers 值 = per*fold = 500', mods.get('atk_s') == 500, str(mods))

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('5) 嵌进 SC_20013 布局（与 server/battle.py:build_20013 对齐）')
print('=' * 72)

if T is not None:
    # 复刻 server/battle.py build_20013 的字段布局，但：
    #   ★ hit 用 encode_hit(FightType)（修复后的正确做法），不再把伤害塞进 hit
    def build_20013_with_magic(round_no, round_wave, wave_no, order_no,
                               target_anger, target_id, source_id, fight_type,
                               hp_max, hp, is_target_die, entries):
        b = w_u16(round_no) + w_u16(round_wave) + w_u8(0) + w_u8(wave_no)
        b += w_u16(1)                       # magic_play 计数 1
        b += w_u8(order_no)
        b += w_u16(target_anger)
        b += w_u16(target_id)
        b += w_u16(source_id)
        b += encode_hit(fight_type)          # ★ hit = FightType（1 字节）
        b += w_u32(hp_max)
        b += w_u32(hp)
        b += w_u8(is_target_die)
        b += w_str('')                      # target_talk
        b += encode_magic_list(entries)      # ★ magic_list
        b += w_u16(0)                        # summon_play
        b += w_u16(0)                        # order_list
        return b

    # 独立解析器（用 proto_spec 的字段表逐步取回）
    def parse_20013(buf):
        o = 0
        rd = struct.unpack_from('>H', buf, o)[0]; o += 2
        rw = struct.unpack_from('>H', buf, o)[0]; o += 2
        tm = struct.unpack_from('>B', buf, o)[0]; o += 1
        wn = struct.unpack_from('>B', buf, o)[0]; o += 1
        n_mp = struct.unpack_from('>H', buf, o)[0]; o += 2
        assert n_mp == 1
        order = struct.unpack_from('>B', buf, o)[0]; o += 1
        ta = struct.unpack_from('>H', buf, o)[0]; o += 2
        tid = struct.unpack_from('>H', buf, o)[0]; o += 2
        sid = struct.unpack_from('>H', buf, o)[0]; o += 2
        hit = struct.unpack_from('>b', buf, o)[0]; o += 1
        hmax = struct.unpack_from('>I', buf, o)[0]; o += 4
        hp = struct.unpack_from('>I', buf, o)[0]; o += 4
        die = struct.unpack_from('>B', buf, o)[0]; o += 1
        tl = struct.unpack_from('>H', buf, o)[0]; o += 2 + tl
        ml, o = decode_magic_list(buf, o)
        n_sp = struct.unpack_from('>H', buf, o)[0]; o += 2
        n_ol = struct.unpack_from('>H', buf, o)[0]; o += 2
        return dict(round=rd, round_wave=rw, time=tm, wave_no=wn, order=order,
                    target_anger=ta, target_id=tid, source_id=sid, hit=hit,
                    hp_max=hmax, hp=hp, is_target_die=die,
                    magic_list=ml, n_summon=n_sp, n_order=n_ol, consumed=o)
    entries = [MagicEntry(906001, change_hp=-120, duration=2, per=500, val=0, fold=3),
               MagicEntry(683140, 0, 2, 106, 0, 1)]
    # 伤害 772 只体现在 hp（1628 = 2400 - 772），hit 传 FightType.HIT
    buf = build_20013_with_magic(3, 1, 1, 0, 0, 2, 1, FIGHT_TYPE_HIT,
                                 2400, 1628, 0, entries)
    got = parse_20013(buf)
    check('SC_20013 整体消费完', got['consumed'] == len(buf),
          'consumed=%d len=%d' % (got['consumed'], len(buf)))
    check('round=3 / hp=1628(=2400-772) 位置正确',
          got['round'] == 3 and got['hp'] == 1628 and got['hp_max'] == 2400, str(got))
    check('★ hit 解出为 FightType.HIT(=1)，而非被夹取的伤害',
          got['hit'] == FIGHT_TYPE_HIT, 'hit=%d' % got['hit'])
    check('magic_list 取回 2 条', len(got['magic_list']) == 2)
    check('magic_list[0] 全字段一致',
          got['magic_list'][0].to_dict() == entries[0].to_dict(),
          '%r vs %r' % (got['magic_list'][0].to_dict(), entries[0].to_dict()))
    check('magic_list[1] 全字段一致',
          got['magic_list'][1].to_dict() == entries[1].to_dict())
    check('summon_play/order_list 计数为 0',
          got['n_summon'] == 0 and got['n_order'] == 0)
    print('     报文长度 = %d 字节（对照：mock 空 magic_list 版 SC_20013 = 39/53 字节）'
          % len(buf))

# ---------------------------------------------------------------------------
print()
print('=' * 72)
print('结果：%d 通过 / %d 失败' % (len(PASS), len(FAIL)))
if FAIL:
    print('失败项：')
    for f in FAIL:
        print('  - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
