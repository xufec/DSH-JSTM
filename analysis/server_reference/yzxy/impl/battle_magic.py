#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSTM 1.4.9 战斗"限时效果/状态"（`magic_list`）的可运行实现。

本模块是**单文件 drop-in**：把它放进 `server/` 即可被 `battle.py` / `mock_server.py` 使用。

=====================================================================
一、依据（全部来自 1.4.9 APK 字节码，逐条可复现）
=====================================================================

| 项 | 依据 | 复现命令 |
|---|---|---|
| `magic_list` 元素 6 字段与顺序 | `cmd_resolve_200.luac` proto#24/proto#37，格式串 **`iiChhC`** | `python tools/dsc_spec.py --file 200` |
| `magic_list` 挂在 `SC_20012.skill_play[].magic_play[]` 与 `SC_20013.magic_play[]` | 两处内联 spec `...##magic_list@D\|Dsc20xxmagic_list\|` | `python tools/proto_spec.py cmds 20012 20013` |
| `duration` = 剩余/持续回合 | `battle_role.luac` proto#4 用 `duration` + `fold`（`'(%s层) '`）渲染 buff 提示框 | `python tools/luajit_dis.py anzbao/jstm.apk assets/src/game/battle/battle_role.luac 4 0 90` |
| `duration >= 0` 判"是否仍生效"，`magic_bid`→`bid` 查配置 | `battle.luac` proto#126（`specMagicEffectAdd/Remove`） | `python tools/luajit_dis.py anzbao/jstm.apk assets/src/game/battle/battle.luac 126 0 60` |
| `SkillMagic` 17 字段与下标映射 | `config_skill_magic.luac` **proto#1 的 TSETS 顺序**（`TGETB D=257..273`） | `python tools/luajit_dis.py anzbao/jstm.apk assets/src/config/config_skill_magic.luac 1 0 60` |
| `SkillMagicType`（31 个属性 ID） | 同文件 proto#2 的 hash 常量表 | `python tools/luajit_dis.py anzbao/jstm.apk assets/src/config/config_skill_magic.luac 2 0 30` |
| 配置↔线上对应 | `type=1240`(`control`) → `magic_desc`「封禁 控制技能成功率+10.6%」；`type=1010`(`atk_s`) → 「魂导物理攻击+{per}%」 | `python extract_skill_magic.py` |

详细报告：`../jstm_battle_fields.md`。

=====================================================================
二、★ 置信度标注（**不要把 INFERRED 当已确认**）
=====================================================================

| 语义 | 置信 | 说明 |
|---|---|---|
| 6 字段名/类型/顺序 | 【已确认】 | 字节码格式串直读 |
| `duration` 是持续回合、`fold` 是层数 | 【已确认】 | 客户端 UI 直接按此渲染 |
| `magic_list` 只放"持续型"效果 | 【高】 | `duration=0`（6415/12664 行）为瞬时效果，不适合放进"按回合递减的列表" |
| `change_hp` 是每回合 HP 变化（负=DoT） | 【中】 | 字段名 + `int32` 有符号类型；未在客户端找到逐回合结算代码 |
| 同 `magic_bid` 重复施加 → `fold` 叠加、`duration` 取较大值 | 【中】 | `fold` 字段存在 + UI 显示"(%s层)"；**叠加规则本身是推断** |
| `duration=255` 表示永久 | 【低-中】 | 仅 88 行出现该值，未验证；已隔离为常量便于改 |
| `effect_type` ∈ {0,1,2,3} ↔ UI 三类（控制/增益/减益） | 【低】 | UI 反汇编里只看到与 `0`/`1` 的比较；映射未验证，本模块**不参与战斗计算**，仅作展示辅助 |
| `type` 只对 1010..1280 有名字 | 【已确认】 | `SkillMagicType` 只有 31 项，2xxx/3xxx/4xxx/5xxx 属其它 ID 空间，本模块按"未知属性"处理 |

=====================================================================
三、明确**不是**原版数据 / 不是原版行为的部分
=====================================================================

* **哪些技能施加哪些 `magic_bid`、数值多少** —— 属**原版服务端数据**，APK 内无取证途径。
  本模块只提供**机制**；具体技能效果需由调用方（或后续原版数据）提供。
* **`change_hp` 的具体数值** —— 同上，调用方传入。
* 因此本模块**不发明任何公式**，只做"状态存取 + 回合递减 + 线编码"。
"""
import json
import os
import struct

__all__ = [
    'DURATION_INSTANT', 'DURATION_PERMANENT',
    'FIGHT_TYPE_MISS', 'FIGHT_TYPE_HIT', 'FIGHT_TYPE_BAOJI', 'FIGHT_TYPE_NAMES', 'encode_hit',
    'SkillMagicTable', 'load_skill_magic',
    'MagicEntry', 'encode_magic_list', 'decode_magic_list',
    'MagicState', 'w_u8', 'w_i8', 'w_u16', 'w_u32', 'w_i32', 'w_str',
]

# ---------------------------------------------------------------------------
# ★ 重大附带发现：`SC_20013.magic_play.hit` 不是伤害，而是"命中结果枚举"
# ---------------------------------------------------------------------------
#
# 证据（全部 1.4.9 APK，逐条可复现）：
#
# 1) `config_battle.luac` proto#0 的 TDUP 常量给出**权威枚举值**：
#
#        TDUP A=1 D=2 ; TableConst(hash=[('MISS',0), ('BAOJI',2), ('HIT',1)])
#        TSETS A=1 B=0 C=1 ; ['FightType']      -> ConfBattle.FightType
#
# 2) `battle.luac` proto#59（= `magic_play` 处理器）里 `hit` **只用于分支**：
#
#      @30   entry.hit  vs  ConfBattle.FightType.MISS   -> 走 miss 表现（SkillAct.miss / miss_back_grid）
#      @185  entry.hit  vs  ConfBattle.FightType.BAOJI  -> battle_scene:shakeScreen(震屏)
#
# 3) 伤害数字不来自 `hit`：proto#59 的常量表含 `hp_max` / `hp` / `setHpPercent` /
#    `playFontMessage` / `change_hp`，即**由 HP 变化驱动**；`hit_num` 是本地变量（连击段数）。
#
# ⇒ 结论：
#   * `hit` 取值域 = {0=MISS, 1=HIT, 2=BAOJI}（**int8 装得下，故线上类型是 `c`**）
#   * **真正的伤害通道 = `hp_max` / `hp`（差值）+ `magic_list[].change_hp` + `is_target_die`**
#   * ⚠️ `server/battle.py` 现有实现 `b += w_i8(hit)`（传原始伤害，如 772）
#     会被 `w_i8` **静默夹到 127 / -128**，两个值都不是合法 `FightType`
#     ⇒ 客户端的 MISS / 暴击(震屏) 分支语义错乱（命中数字因走 `hp` 差值而"看起来正常"，
#       所以这个 bug 在上一轮实测里未被发现）。
#     **修复：`hit` 传 `FIGHT_TYPE_*`，伤害只体现在 `hp`。**
#
FIGHT_TYPE_MISS = 0    # 未命中
FIGHT_TYPE_HIT = 1     # 普通命中
FIGHT_TYPE_BAOJI = 2   # 暴击（客户端据此震屏）

FIGHT_TYPE_NAMES = {FIGHT_TYPE_MISS: 'MISS', FIGHT_TYPE_HIT: 'HIT', FIGHT_TYPE_BAOJI: 'BAOJI'}


def encode_hit(fight_type):
    """把 `FightType` 编成线上 `hit:int8`，并**拒绝非法值**（不静默夹取）。

    ⚠️ 与 `w_i8` 的区别：`w_i8` 会把 772 夹成 127（上一轮 mock 的实际行为）；
    本函数对非法值直接抛错，避免把"伤害当命中结果"这类错误再次写进报文。
    """
    v = int(fight_type)
    if v not in FIGHT_TYPE_NAMES:
        raise ValueError(
            'hit 必须是 FightType {%s}，收到 %r。'
            '若你想发的是伤害，请改走 hp/hp_max（见 battle_magic 头注）'
            % (', '.join('%d=%s' % kv for kv in sorted(FIGHT_TYPE_NAMES.items())), v))
    return w_i8(v)


# ---------------------------------------------------------------------------
# duration 特殊值（见头注置信度表）
# ---------------------------------------------------------------------------
DURATION_INSTANT = 0      # 瞬时：不入持久列表
DURATION_PERMANENT = 255  # 【推断】永久：不递减

_HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 线编码基元（与 server/battle.py 中的实现一致：大端）
# ---------------------------------------------------------------------------

def w_u8(v):
    return struct.pack('>B', int(v) & 0xFF)


def w_i8(v):
    return struct.pack('>b', max(-128, min(127, int(v))))


def w_u16(v):
    return struct.pack('>H', int(v) & 0xFFFF)


def w_u32(v):
    return struct.pack('>I', int(v) & 0xFFFFFFFF)


def w_i32(v):
    return struct.pack('>i', max(-2147483648, min(2147483647, int(v))))


def w_i16(v):
    return struct.pack('>h', max(-32768, min(32767, int(v))))


def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


# ---------------------------------------------------------------------------
# 配置表：Config.SkillMagic / Config.SkillMagicType
# ---------------------------------------------------------------------------

class SkillMagicTable(object):
    """`Config.SkillMagic` + `Config.SkillMagicType` 的只读访问器。"""

    def __init__(self, data):
        self._types = {int(k): v for k, v in (data.get('SkillMagicType') or {}).items()}
        self._rows = {int(k): v for k, v in (data.get('SkillMagic') or {}).items()}
        self._duration_dist = data.get('duration_dist') or {}
        self._meta = data

    # ---- 基本信息 ----
    def __len__(self):
        return len(self._rows)

    @property
    def count(self):
        return len(self._rows)

    @property
    def type_count(self):
        return len(self._types)

    def get(self, magic_bid):
        """取一行配置；不存在返回 None（调用方必须处理）。"""
        return self._rows.get(int(magic_bid))

    def has(self, magic_bid):
        return int(magic_bid) in self._rows

    # ---- 字段便捷读取（带默认值）----
    def type_id(self, magic_bid):
        r = self.get(magic_bid)
        return int(r.get('type', 0)) if r else 0

    def type_name(self, type_id):
        """属性 ID → 名（如 1010→'atk_s'、1240→'control'）。未知返回 None。"""
        return self._types.get(int(type_id))

    def effect_type(self, magic_bid):
        r = self.get(magic_bid)
        return int(r.get('effect_type', 0)) if r else 0

    def effect_category(self, magic_bid):
        """UI 三类（增益/减益/控制）。

        ⚠【低置信】`effect_type` ∈ {0,1,2,3}，与 UI 三类的映射**未验证**。
        本函数只用于展示，**不参与任何战斗计算**。返回 'unknown' 表示未定。
        """
        et = self.effect_type(magic_bid)
        return {0: 'buff', 1: 'debuff', 2: 'control', 3: 'control'}.get(et, 'unknown')

    def default_duration(self, magic_bid):
        """配置里的默认持续回合（0=瞬时，255=推断永久）。"""
        r = self.get(magic_bid)
        return int(r.get('duration', 0)) if r else 0

    def default_per(self, magic_bid):
        r = self.get(magic_bid)
        return int(r.get('per', 0)) if r else 0

    def target_camp(self, magic_bid):
        r = self.get(magic_bid)
        return int(r.get('target_camp', 0)) if r else 0

    def name(self, magic_bid):
        r = self.get(magic_bid)
        if not r:
            return ''
        return r.get('desc') or ''

    def describe(self, magic_bid, per=None, val=None):
        """把 `magic_desc` 模板里的 {per}/{val}/{val_per} 填上（与客户端 gsub 行为对齐）。

        客户端 `battle_role.luac` proto#4 的常量表里同时有 `'{val_per}'` `'{val}'` `'{per}'`，
        说明模板可能含三种占位符；`{val_per}` 的语义是"有 val 就用 val，否则用 per"（【推断】）。
        """
        r = self.get(magic_bid)
        if not r:
            return ''
        tpl = r.get('magic_desc') or r.get('desc') or ''
        p = self.default_per(magic_bid) if per is None else int(per)
        v = val
        if v is not None:
            tpl = tpl.replace('{val_per}', '%d' % int(v))
        else:
            tpl = tpl.replace('{val_per}', '%d' % p)
        tpl = tpl.replace('{val}', '%d' % (0 if v is None else int(v)))
        tpl = tpl.replace('{per}', '%d' % p)
        return tpl

    def visualize(self, magic_bid):
        """客户端表现资源（服务端只需原样回传，不必理解）。"""
        r = self.get(magic_bid) or {}
        return {
            'icon': r.get('icon', 0),
            'res_up': r.get('res_up', ''),
            'res_buff_up': r.get('res_buff_up', ''),
            'res_down': r.get('res_down', ''),
            'location': r.get('location', 0),
            'cycle': r.get('cycle', 0),
            'must_play': r.get('must_play', 0),
        }


def load_skill_magic(path=None):
    """加载 `skill_magic.json`（由 `extract_skill_magic.py` 生成）。"""
    p = path or os.path.join(_HERE, 'skill_magic.json')
    if not os.path.isfile(p):
        raise IOError(
            'SkillMagic 数据不存在：%s\n请先运行: python %s'
            % (p, os.path.join(_HERE, 'extract_skill_magic.py')))
    with open(p, encoding='utf-8') as f:
        return SkillMagicTable(json.load(f))


# ---------------------------------------------------------------------------
# 线上条目：magic_list 元素（**格式串 iiChhC**）
# ---------------------------------------------------------------------------

class MagicEntry(object):
    """`magic_list` 的一个元素。

    线序（`iiChhC`，**顺序与类型都不可改**）：

        magic_bid  int32   效果 ID → Config.SkillMagic
        change_hp  int32   每回合 HP 变化（负=DoT，正=HoT）
        duration   uint8   剩余回合
        per        int16   百分比
        val        int16   绝对值
        fold       uint8   叠加层数
    """

    __slots__ = ('magic_bid', 'change_hp', 'duration', 'per', 'val', 'fold')

    def __init__(self, magic_bid, change_hp=0, duration=0, per=0, val=0, fold=1):
        self.magic_bid = int(magic_bid)
        self.change_hp = int(change_hp)
        self.duration = int(duration)
        self.per = int(per)
        self.val = int(val)
        self.fold = int(fold)

    def encode(self):
        """6 字段，18 字节（4+4+1+2+2+1 = 14）+ ... 实为 14 字节。"""
        return (w_i32(self.magic_bid) + w_i32(self.change_hp) + w_u8(self.duration)
                + w_i16(self.per) + w_i16(self.val) + w_u8(self.fold))

    @property
    def wire_size(self):
        return 14

    def to_dict(self):
        return {
            'magic_bid': self.magic_bid, 'change_hp': self.change_hp,
            'duration': self.duration, 'per': self.per, 'val': self.val,
            'fold': self.fold,
        }

    def __repr__(self):
        return ('MagicEntry(bid=%d, change_hp=%d, duration=%d, per=%d, val=%d, fold=%d)'
                % (self.magic_bid, self.change_hp, self.duration,
                   self.per, self.val, self.fold))


def encode_magic_list(entries):
    """`D|Dsc20xxmagic_list|` = **u16 计数前缀** + 每条 14 字节。

    计数前缀的约定见 `tools/dsc_spec.py` 头注：
    「`D|Xxx|` = 计数前缀 + Xxx 结构数组」。`battle.py` 现有代码亦按 `w_u16(len)` 写。
    """
    if not entries:
        return w_u16(0)
    b = w_u16(len(entries))
    for e in entries:
        b += e.encode()
    return b


def decode_magic_list(buf, off=0):
    """独立解码器（仅用于自测/回放校验，不参与线上编码）。

    返回 (entries, new_off)。**故意不复用 encode 的逻辑**，以便交叉验证。
    """
    n = struct.unpack_from('>H', buf, off)[0]
    off += 2
    out = []
    for _ in range(n):
        magic_bid, change_hp = struct.unpack_from('>ii', buf, off)
        off += 8
        duration = struct.unpack_from('>B', buf, off)[0]
        off += 1
        per, val = struct.unpack_from('>hh', buf, off)
        off += 4
        fold = struct.unpack_from('>B', buf, off)[0]
        off += 1
        out.append(MagicEntry(magic_bid, change_hp, duration, per, val, fold))
    return out, off


# ---------------------------------------------------------------------------
# 每个战斗单位的"限时效果"状态机
# ---------------------------------------------------------------------------

class MagicState(object):
    """一个单位身上**持续型**效果的集合。

    设计要点（与客户端的期待对齐）：

    * 列表**按回合全量重列**（`to_wire()` 每次给出全部在效效果）。
      ⇒ 因为 `duration` 每回合都会变，客户端无法靠"仅变化项"维护倒计时；
      这与 `SC_20013.summon_play` 每回合重推单位状态的做法同构。
      （"原版是 full 还是 delta"在本工作区**不可取证**，见 `../jstm_battle_fields.md` §9.1；
       本实现选择 full —— 更稳、更易实现，且客户端容忍空表。）
    * `duration == 0` 的效果**不入列表**（瞬时）。
    * `duration == 255` 视为永久，不递减（【推断】）。
    """

    def __init__(self):
        self._entries = []          # list[MagicEntry]，保持插入顺序

    # ---- 查询 ----
    def __len__(self):
        return len(self._entries)

    @property
    def entries(self):
        return list(self._entries)

    def find(self, magic_bid):
        for e in self._entries:
            if e.magic_bid == int(magic_bid):
                return e
        return None

    def to_wire(self):
        """给 `magic_list` 用的快照（全量）。"""
        return [MagicEntry(e.magic_bid, e.change_hp, e.duration, e.per, e.val, e.fold)
                for e in self._entries]

    def encode(self):
        return encode_magic_list(self.to_wire())

    # ---- 施加 ----
    def apply(self, table, magic_bid, val=None, per=None, change_hp=0,
              duration=None, fold_add=1, persist=None):
        """施加一个效果。

        :param table: `SkillMagicTable`
        :param magic_bid: 效果 ID（必须能被 `table.get` 查到，否则抛错——**不静默吞掉**）
        :param val: 绝对值；None ⇒ 0
        :param per: 百分比；None ⇒ 用配置的 `per`
        :param change_hp: 每回合 HP 变化；调用方给出（原版数值不可得）
        :param duration: 剩余回合；None ⇒ 用配置的 `duration`
        :param fold_add: 叠加层数增量（默认 1）
        :param persist: 是否入持久列表；None ⇒ 按 `duration != 0` 自动判定
        :return: 生效的 `MagicEntry`，或 None（瞬时且 persist=False）
        """
        if not table.has(magic_bid):
            raise KeyError('未知 magic_bid=%r；拒绝静默发送（客户端会用 SkillMagic.get 查配置）'
                           % (magic_bid,))
        d = table.default_duration(magic_bid) if duration is None else int(duration)
        p = table.default_per(magic_bid) if per is None else int(per)
        v = 0 if val is None else int(val)

        if persist is None:
            persist = (d != DURATION_INSTANT)

        existing = self.find(magic_bid)
        if existing is not None:
            # 同效果重复施加：层数叠加、剩余回合取较大值（【推断】规则，集中在此便于修改）
            if persist:
                existing.fold = min(255, existing.fold + int(fold_add)) & 0xFF
                if d != DURATION_PERMANENT:
                    existing.duration = max(existing.duration, d) & 0xFF
            return existing if persist else None

        if not persist:
            return None

        e = MagicEntry(magic_bid, change_hp=change_hp, duration=d,
                       per=p, val=v, fold=max(1, min(255, int(fold_add))))
        self._entries.append(e)
        return e

    def remove(self, magic_bid):
        """按效果 ID 移除（返回是否存在）。"""
        for i, e in enumerate(self._entries):
            if e.magic_bid == int(magic_bid):
                self._entries.pop(i)
                return True
        return False

    def clear(self):
        self._entries = []

    # ---- 回合结算 ----
    def tick(self):
        """**回合开始**时调用：先按 `change_hp` 结算，再递减 `duration`。

        :return: (expired:[MagicEntry], hp_delta:int)

        顺序说明（【推断】）：`SC_20013` 是"回合开始"，客户端在 `playRoundStart` 里
        既显示伤害也刷新 buff 倒计时，故本轮"先生效再递减"最符合表现。
        """
        hp_delta = 0
        expired = []
        keep = []
        for e in self._entries:
            hp_delta += e.change_hp * max(1, e.fold)
            if e.duration == DURATION_PERMANENT:
                keep.append(e)
                continue
            e.duration = (e.duration - 1) & 0xFF
            if e.duration == 0:
                expired.append(e)
            else:
                keep.append(e)
        self._entries = keep
        return expired, hp_delta

    # ---- 属性修正汇总 ----
    def modifiers(self, table):
        """把在效效果汇总成 `{属性名: 合计值}`，供伤害/命中计算使用。

        规则（**全部为【推断】**，集中在此便于替换为原版规则）：
        * `type` 1010..1280（有 `SkillMagicType` 名）才参与汇总；
        * 后缀 `_p` / `_rate` 视作百分比累加，其余视作定值累加；
        * 每条贡献 `fold * (val if val else per)`。
        未知 `type`（2xxx/3xxx/4xxx/5xxx）**忽略**并在返回值里记入 `_unknown_types`。
        """
        agg = {}
        unknown = []
        for e in self._entries:
            tid = table.type_id(e.magic_bid)
            nm = table.type_name(tid)
            if not nm:
                unknown.append(tid)
                continue
            per_each = e.val if e.val else e.per
            agg[nm] = agg.get(nm, 0) + per_each * max(1, e.fold)
        if unknown:
            agg['_unknown_types'] = sorted(set(unknown))
        return agg

    def debug_lines(self, table):
        """人类可读的一行一条（写日志用）。"""
        out = []
        for e in self._entries:
            out.append('bid=%d [%s] dur=%d fold=%d per=%d val=%d chp=%d | %s'
                       % (e.magic_bid, table.type_name(table.type_id(e.magic_bid)) or '?',
                          e.duration, e.fold, e.per, e.val, e.change_hp,
                          table.describe(e.magic_bid, e.per, e.val or None)))
        return out
