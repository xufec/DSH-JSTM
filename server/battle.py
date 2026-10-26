"""Phase D：1.4.9 战斗最小垂直闭环（服务端权威实现）。

=====================================================================
一、协议依据（**全部来自 1.4.9 APK 字节码**，无一条凭经验）
=====================================================================

`assets/src/config/protocal/cmd_resolve_200.luac` 里每个消息都是

    AutoConstruct(方向, CMD, { '<字段名>__<类型>', ... })

**数组顺序就是字段顺序**。本模块的编码器逐字段对照该数组写成。
还原工具：`python tools/proto_spec.py cmds 20002 20010 20012 20013 20020 20022 20023`
子结构还原：`python tools/dsc_spec.py --file 200`

| CMD | 方向 | 字段（权威顺序） |
|---|---|---|
| 20002 | CS | `mon_id:int32` |
| 20002 | SC | `code:uint8, msg:string` |
| 20010 | SC | `round:u16, round_wave:u16, wave_max:u16, wave_no:u16, atk_formation_type:u8, atk_formation_lev:u8, def_formation_type:u8, def_formation_lev:u8, is_observer:u8, effect_id:s, order_list:T(id@I), fighter_info_list:T(id@H##rid@I##srv_id@s##name@s##lev@H##sex@C##career@H##pos@C##group@C##hp_max@I##hp@I##anger@I##is_auto@C##animate_res@D##skills@D##specials@D)` |
| 20012 | SC | `round:u16, skill_play:T(order@C##user_id@H##skill_id@I##father_id@I##father_skill_id@I##passive_skill_id@I##user_anger@H##talk@s##notice@s##magic_play@D##summon_play@D), cooldown:T(bid@I##last_use@H)` |
| 20013 | SC | `round:u16, round_wave:u16, time:u8, wave_no:u8, magic_play:T(order@C##target_anger@H##target_id@H##source_id@H##hit@c##hp_max@I##hp@I##is_target_die@C##target_talk@s##magic_list@D), summon_play:T(...), order_list:T(id@I)` |
| 20020 | SC | `result:uint8` |
| 20022 | SC | `icon_list:T(icon_id@I)` |
| 20023 | SC | `type:u8, result:u8, role_hurl_list:T(rid@I##srv_id@s##name@s##group@C##lev@H##sex@C##career@H##hp_max@I##hp@I##hurt@I##master_rid@I##master_srv_id@s##id@I), val_list:T(key@C##val@I), msg:s` |

子结构（`tools/dsc_spec.py`，判据见该脚本头注）：

| 子结构 | 字段 |
|---|---|
| `Dsc20010animate_res` | `ant_id@H, ant_val@s, ent_lev@C, dis_method@C` |
| `Dsc20010skills` | `bid@I, step@C, last_use@H, cd@H` |
| `Dsc20010specials` | `key@C, val@I` |
| `Dsc20013magic_list` | `magic_bid@i, change_hp@i, duration@C, per@h, val@h, fold@C` |

时钟推进（客户端 → 服务端）：

| CMD | 含义 | 依据 |
|---|---|---|
| 20011 | 客户端加载完成（空） | `battle_ctrl.luac` proto#20 `playEnd` 用的是 20014；20011 由 `battle.luac loadFinish` 发 |
| 20014 | 客户端动画播放完成（空） | `battle_ctrl.luac` proto#20 `playEnd`：`GetPrototype(20014)` → `SendProtocal` |
| 20009 | 使用技能 `skill_id:int32` | `battle_ctrl.luac` proto#6 `csSelectSkill` |
| 20008 | 自动战斗开关 `flag:uint8` | `battle_ctrl.luac` proto#7 `setAuto` |

=====================================================================
二、★ 本模块里**不是原版数据**的部分（必须如实标注）
=====================================================================

`Config.Mon`（1.4.9 APK，2645 条）**只含 name 与 res_id**，
**不含 HP / 攻击 / 防御 / 经验 / 金币**（见
`analysis/1.4.9/battle/monster_data_model.md` §3.1）。
这些数值属于**原版服务端数据**，APK 内无取证途径。

因此本模块中：

| 项 | 标记 | 说明 |
|---|---|---|
| 怪物 HP / 攻击 / 防御 | `TEST_ONLY` | 见 `MON_STATS`，**不是原版数值** |
| 伤害公式 | `IMPLEMENTATION_FALLBACK` | 见 `calc_damage()`，**不是原版公式** |
| 击杀经验 / 金币 | `TEST_ONLY` | 见 `KILL_REWARD`，**不是原版数值** |
| 掉落表 | `TEST_ONLY` | 见 `FALLBACK_DROPS`，原版掉落表见 `analysis/1.4.9/item/drop_*.md` |
| 战斗摆位 pos | `IMPLACEMENT_FALLBACK` | 按"我方 0..2 / 敌方 0..2"约定 |

**必须明确：以上都不是原版数据。** 将来拿到原版服务端数据后应整体替换。
"""
import struct

# ---------------------------------------------------------------------------
# 线编码基元（与 mock_server.py 中的实现完全一致：大端、字符串 u16 长度前缀）
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


def w_str(s):
    b = (s or '').encode('utf-8')
    return w_u16(len(b)) + b


# ---------------------------------------------------------------------------
# ★ TEST_ONLY / IMPLEMENTATION_FALLBACK 常量（**非原版数据**）
# ---------------------------------------------------------------------------

# 怪物战斗数值：**APK 里没有**，这里是 TEST_ONLY 兼容值。
# hp_max 取 2400 是为了让一场战斗跨 ~3 个回合，从而验证
# SC_20012/20013 → CS_20014 的**回合循环**（而不是一击结束）。
MON_STATS = {
    'hp_max': 2400,       # TEST_ONLY
    'atk_s': 40,          # TEST_ONLY
    'def_s': 10,          # TEST_ONLY
}

# 击杀奖励：**APK 里没有**，TEST_ONLY。
KILL_REWARD = {
    'exp': 50,            # TEST_ONLY
    'coin': 30,           # TEST_ONLY
}

# 掉落：TEST_ONLY 占位（原版掉落表见 analysis/1.4.9/item/）。
FALLBACK_DROPS = []       # [(item_id, count)]

# 战斗摆位：我方 group=1 pos 0..2，敌方 group=2 pos 0..2
MAX_WAVES = 1


# ---------------------------------------------------------------------------
# 伤害计算 —— IMPLEMENTATION_FALLBACK（**不是原版公式**）
# ---------------------------------------------------------------------------

def calc_damage(atk, defense):
    """JSTMCompatibleDamage 伤害公式（INFERENCE，非原版）。

    # INFERENCE: JSTMCompatibleDamage, formula UNKNOWN per E1/E2。
      原版公式在服务端，APK 内无法取证。
    当前规则：`dmg = max(1, atk*0.8 - def*0.5)`（线性攻防折减，
    保留至少 1 点血避免打不死；与旧 `atk - def//2` 同结构，系数改 0.8/0.5）。
    """
    return max(1, int(int(atk) * 0.8 - int(defense) * 0.5))


# ---------------------------------------------------------------------------
# 战斗单位
# ---------------------------------------------------------------------------

class Fighter(object):
    """一个战斗单位（对应 SC_20010/20013/20015 的 fighter_info_list 元素）。"""

    def __init__(self, fid, name, lev, sex, career, group, pos,
                 hp_max, hp, rid=0, srv_id='', is_auto=0, res_id='',
                 anger=0):
        self.id = fid
        self.rid = rid
        self.srv_id = srv_id
        self.name = name
        self.lev = lev
        self.sex = sex
        self.career = career
        self.group = group          # 1=我方 2=敌方
        self.pos = pos              # 0..2
        self.hp_max = hp_max
        self.hp = hp
        self.anger = anger
        self.is_auto = is_auto
        self.res_id = res_id

    @property
    def is_monster(self):
        return self.rid == 0

    def encode(self):
        """按 SC_20010.fighter_info_list 的**权威字段顺序**编码。"""
        b = w_u16(self.id)
        b += w_u32(self.rid)
        b += w_str(self.srv_id)
        b += w_str(self.name)
        b += w_u16(self.lev)
        b += w_u8(self.sex)
        b += w_u16(self.career)
        b += w_u8(self.pos)
        b += w_u8(self.group)
        b += w_u32(self.hp_max)
        b += w_u32(self.hp)
        b += w_u32(self.anger)
        b += w_u8(self.is_auto)
        # animate_res: D|Dsc20010animate_res| = 计数前缀 + 结构数组
        #   字段：ant_id@H, ant_val@s, ent_lev@C, dis_method@C
        #   ant_val 放外观资源 id（来自 Config.Mon 的原版 res_id）
        if self.res_id:
            b += w_u16(1)
            # ★★ R78：`ant_id` 由 0 改成 **1**。真机现象是"怪的模型和主角一样"
            #   —— `ant_id=0` 很可能被客户端当成"没指定外观"从而回退到角色默认模型，
            #   于是 `ant_val`（`Config.Mon.res_id`，如 H34800）根本没被用上。
            #   ⚠ 诚实标注：`ant_id` 的**语义仍属【待验证】**（可能是资源槽位/动画类型 id），
            #     这里只是把它从"明显无效的 0"改成非 0，让 `ant_val` 有机会生效。
            b += w_u16(1)                 # ant_id（R78：0 → 1）
            b += w_str(self.res_id)       # ant_val ← 原版资源 id
            b += w_u8(0)                  # ent_lev
            b += w_u8(0)                  # dis_method
        else:
            b += w_u16(0)
        # skills: D|Dsc20010skills| = bid@I, step@C, last_use@H, cd@H
        b += w_u16(0)
        # specials: D|Dsc20010specials| = key@C, val@I
        b += w_u16(0)
        return b


# ---------------------------------------------------------------------------
# 战斗实例
# ---------------------------------------------------------------------------

class Battle(object):
    """一场战斗（我方 1 个单位 vs 敌方 1 只怪）。"""

    def __init__(self, role, mon_stat, mon_name, mon_res_id, mon_lev=1,
                 mon_sex=0, mon_career=1, role_skill_bid=0, mon_bid=0):
        self.round = 0
        self.finished = False
        self.result = 0                 # 0=未结束 1=胜 2=败（取值语义 UNKNOWN，见文档）
        self.role_dmg_taken = 0
        self.mon_dmg_taken = 0
        self.mon_died = False
        self.log = []

        role_hp_max = int(role.get('hp_max') or 1000)
        role_hp = int(role.get('hp') or role_hp_max)
        # 我方：group=1, pos=**1**, id=1
        # ★★ R78：`pos` 由 0 改成 **1**。真机点怪后客户端直接弹「pos位置不能为0」
        #   ⇒ `pos` 是**1 基**的（上面原注释写的 "0..2" 是错误推断，正交错一次）。
        self.role_f = Fighter(
            fid=1, name=role.get('name') or 'DSH', lev=int(role.get('lev') or 1),
            sex=int(role.get('sex') or 0), career=int(role.get('career') or 1),
            group=1, pos=1, hp_max=role_hp_max, hp=role_hp,
            rid=int(role.get('rid') or 1001), srv_id=str(role.get('srv_id') or '1'),
            res_id='')
        # 敌方：group=2, pos=**1**, id=2
        # ★★★ R79：**怪模型和主角一样的真正原因**（反汇编 `battle_role.luac` proto#2 得到）：
        #     if self.srv_id == 'mon' then                 -- ① 先判定"这是怪"
        #         local cfg = Config.Mon[self.rid]         -- ② **用 rid** 查 Config.Mon 拿 res_id
        #         if cfg and cfg.res_id then self.res = cfg.res_id end
        #   而我们原先给怪的 `rid=0` + `srv_id=''` ⇒ **两个条件都不成立** ⇒
        #   客户端拿不到 res_id ⇒ 回退成**角色默认模型**（看起来就是主角本体）。
        #   ⇒ 必须：`srv_id='mon'`，且 `rid = mon_bid`（10105 才能查到 H34800）。
        self.mon_f = Fighter(
            fid=2, name=mon_name, lev=int(mon_lev or 1), sex=mon_sex,
            career=mon_career, group=2, pos=1,
            hp_max=int(mon_stat.get('hp_max') or 100),
            hp=int(mon_stat.get('hp_max') or 100),
            rid=int(mon_bid or 0), srv_id='mon',
            res_id=mon_res_id or '')
        self.role_atk = int(role.get('atk_s') or 100)
        self.role_def = int(role.get('def_s') or 0)
        self.mon_atk = int(mon_stat.get('atk_s') or 10)
        self.mon_def = int(mon_stat.get('def_s') or 0)
        self.skill_bid = int(role_skill_bid or 0)

    # ---------------- 组包 ----------------

    def build_20010(self):
        """SC_20010 战斗初始化数据。"""
        b = w_u16(1)            # round
        b += w_u16(1)           # round_wave
        b += w_u16(MAX_WAVES)   # wave_max
        b += w_u16(1)           # wave_no
        b += w_u8(1) + w_u8(0)  # atk_formation_type / lev
        b += w_u8(1) + w_u8(0)  # def_formation_type / lev
        b += w_u8(0)            # is_observer
        b += w_str('')          # effect_id
        # order_list: T(id@I) —— 出手顺序
        order = [self.role_f.id, self.mon_f.id]
        b += w_u16(len(order))
        for oid in order:
            b += w_u32(oid)
        # fighter_info_list
        bs = [self.role_f, self.mon_f]
        b += w_u16(len(bs))
        for f in bs:
            b += f.encode()
        return b

    def build_20012(self, user_id, skill_id):
        """SC_20012 小回合战斗效果（谁用什么技能）。"""
        b = w_u16(self.round)
        # skill_play: T(order@C##user_id@H##skill_id@I##father_id@I##father_skill_id@I
        #                ##passive_skill_id@I##user_anger@H##talk@s##notice@s
        #                ##magic_play@D##summon_play@D)
        b += w_u16(1)
        b += w_u8(0)            # order
        b += w_u16(user_id)     # user_id
        b += w_u32(skill_id)    # skill_id
        b += w_u32(0)           # father_id
        b += w_u32(0)           # father_skill_id
        b += w_u32(0)           # passive_skill_id
        b += w_u16(0)           # user_anger
        b += w_str('')          # talk
        b += w_str('')          # notice
        b += w_u16(0)           # magic_play（空）
        b += w_u16(0)           # summon_play（空）
        # cooldown: T(bid@I##last_use@H)
        b += w_u16(0)
        return b

    def build_20013(self, order_no, source_id, target_id, hit, target,
                    magic_bid=0, round_wave=1, wave_no=1):
        """SC_20013 回合开始（**伤害就落在这里**）。"""
        b = w_u16(self.round)
        b += w_u16(round_wave)
        b += w_u8(0)            # time
        b += w_u8(wave_no)
        # magic_play: T(order@C##target_anger@H##target_id@H##source_id@H##hit@c
        #                ##hp_max@I##hp@I##is_target_die@C##target_talk@s##magic_list@D)
        b += w_u16(1)
        b += w_u8(order_no)     # order
        b += w_u16(target.anger)
        b += w_u16(target_id)
        b += w_u16(source_id)
        b += w_i8(hit)          # hit:int8
        b += w_u32(target.hp_max)
        b += w_u32(target.hp)
        b += w_u8(1 if target.hp <= 0 else 0)
        b += w_str('')
        # magic_list: D|Dsc20013magic_list| = magic_bid@i, change_hp@i, duration@C,
        #                                     per@h, val@h, fold@C
        if magic_bid:
            b += w_u16(1)
            b += w_i32(magic_bid)
            b += w_i32(-hit)
            b += w_u8(0)
            b += struct.pack('>h', 0)
            b += struct.pack('>h', 0)
            b += w_u8(0)
        else:
            b += w_u16(0)
        # summon_play
        b += w_u16(0)
        # order_list: T(id@I)
        b += w_u16(0)
        return b

    def build_20020(self):
        return w_u8(self.result)

    def build_20023(self, battle_type=0):
        """SC_20023 显示战斗伤害信息（结算明细）。"""
        b = w_u8(battle_type)
        b += w_u8(self.result)
        # role_hurl_list: T(rid@I##srv_id@s##name@s##group@C##lev@H##sex@C##career@H
        #                   ##hp_max@I##hp@I##hurt@I##master_rid@I##master_srv_id@s##id@I)
        rows = [(self.role_f, self.role_dmg_taken), (self.mon_f, self.mon_dmg_taken)]
        b += w_u16(len(rows))
        for f, hurt in rows:
            b += w_u32(f.rid)
            b += w_str(f.srv_id)
            b += w_str(f.name)
            b += w_u8(f.group)
            b += w_u16(f.lev)
            b += w_u8(f.sex)
            b += w_u16(f.career)
            b += w_u32(f.hp_max)
            b += w_u32(f.hp)
            b += w_u32(hurt)
            b += w_u32(0)          # master_rid
            b += w_str('')         # master_srv_id
            b += w_u32(f.id)       # id
        # val_list: T(key@C##val@I)
        b += w_u16(0)
        b += w_str('')
        return b

    # ---------------- 回合推进 ----------------

    def play_round(self):
        """推进一个小回合，返回 [(cmd, body)] 列表。

        流程（严格按 battle_flow.md §三）：
            服务端 → SC_20012（技能播放）
            服务端 → SC_20013（伤害）
            客户端 → CS_20014（动画播完）后进入下一回合
        """
        self.round += 1
        out = []
        if self.mon_f.hp <= 0:
            return out

        # 我方出手
        dmg = calc_damage(self.role_atk, self.mon_def)
        self.mon_f.hp = max(0, self.mon_f.hp - dmg)
        self.mon_dmg_taken += dmg
        out.append((20012, self.build_20012(self.role_f.id, self.skill_bid)))
        out.append((20013, self.build_20013(0, self.role_f.id, self.mon_f.id,
                                            dmg, self.mon_f,
                                            magic_bid=self.skill_bid)))
        self.log.append('round %d: role(%d) -> mon(%d) hit=%d mon_hp=%d/%d'
                        % (self.round, self.role_f.id, self.mon_f.id, dmg,
                           self.mon_f.hp, self.mon_f.hp_max))

        if self.mon_f.hp <= 0:
            self.mon_died = True
            self.finished = True
            self.result = 1
            self.log.append('monster died, battle result=%d' % self.result)
            return out

        # 怪物反击（简单 AI：只平砍）
        dmg2 = calc_damage(self.mon_atk, self.role_def)
        self.role_f.hp = max(0, self.role_f.hp - dmg2)
        self.role_dmg_taken += dmg2
        out.append((20012, self.build_20012(self.mon_f.id, 0)))
        out.append((20013, self.build_20013(1, self.mon_f.id, self.role_f.id,
                                            dmg2, self.role_f)))
        self.log.append('round %d: mon(%d) -> role(%d) hit=%d role_hp=%d/%d'
                        % (self.round, self.mon_f.id, self.role_f.id, dmg2,
                           self.role_f.hp, self.role_f.hp_max))
        if self.role_f.hp <= 0:
            self.finished = True
            self.result = 2
            self.log.append('role died, battle result=%d' % self.result)
        return out
