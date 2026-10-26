# -*- coding: utf-8 -*-
"""answer.service —— 答题活动（16100~16103）服务层。

★ 证据等级（务必按级别引用，勿升级）：
  · 协议帧结构：CONFIRMED（`protocol/fields.json`，源自 `cmd_resolve_161.luac`）
  · 配置（题目/时段/门槛/题数/奖励）：CONFIRMED（`server/cfg/config_answer.json`）
      Question : {qid: {content, a, b, c, d}}        共 239 题
      Other    : {interval:20, lev:20, question_num:20, series_num:15}
      OpentTime: {1:{start_time,end_time}, 2:{...}}   11:00-13:00 / 17:00-19:00
      AnswerAward.answer_reward: {1:[null,8,36500,3,1], 2:[null,16,25300,1,1]}
                 ⇒ 答对 >= 8 题：物品 36500 ×3 ；答对 >= 16 题：物品 25300 ×1
  · ★ **正确答案键：NOT CONFIRMED** —— 原版 `config_answer.Question` **只有
    `content + a/b/c/d`，没有任何"正确项"字段**（已核对；灯谜表同样只有 `a1..a16 + answer_len`）。
    故 `server/answer_key.json` 是**项目自定义推导键**（依据题面推导），
    见该文件 `_meta.provenance`。**不得**把它当作原版真值引用。
"""

import json
import os
import random
import time

from core import runtime
from persistence.db import db_conn, db_release

log = runtime.log

HERE = os.path.dirname(os.path.abspath(__file__))
CFG_DIR = os.path.normpath(os.path.join(HERE, '..', 'cfg'))
KEY_PATH = os.path.normpath(os.path.join(HERE, '..', 'answer_key.json'))

_cfg = None
_key = None

OPT = ('a', 'b', 'c', 'd')          # 选项字母 → SC 里的 0..3


def answer_cfg():
    """读 config_answer.json（结构化 `server/cfg` 形态）。"""
    global _cfg
    if _cfg is not None:
        return _cfg
    try:
        with open(os.path.join(CFG_DIR, 'config_answer.json'), encoding='utf-8') as f:
            j = json.load(f)

        def h(sec):
            return (j.get(sec) or {}).get('hash') or {}
        _cfg = {
            'questions': {k: (v.get('hash') or {})
                          for k, v in (j.get('Question') or {}).items()},
            'other': h('Other'),
            'open': {k: (v.get('hash') or {})
                     for k, v in (j.get('OpentTime') or {}).items()},
            'award': h('AnswerAward').get('answer_reward') or {},
        }
        log('server.log', 'answer cfg: %d questions, other=%s'
            % (len(_cfg['questions']), _cfg['other']))
    except Exception as e:
        log('server.log', '!! config_answer load failed: %r' % (e,))
        _cfg = {'questions': {}, 'other': {}, 'open': {}, 'award': {}}
    return _cfg


def answer_key():
    """**[项目推导键，非原版数据]** qid -> 'a'|'b'|'c'|'d'。"""
    global _key
    if _key is not None:
        return _key
    try:
        with open(KEY_PATH, encoding='utf-8') as f:
            _key = (json.load(f) or {}).get('answers') or {}
        log('server.log', 'answer key loaded: %d entries (AI-derived, NOT original)'
            % len(_key))
    except Exception as e:
        log('server.log', '!! answer_key load failed: %r' % (e,))
        _key = {}
    return _key


def db_answer_init():
    con = db_conn()
    con.execute("""CREATE TABLE IF NOT EXISTS role_answer (
        rid INTEGER PRIMARY KEY, day INTEGER, idx INTEGER, correct INTEGER,
        started INTEGER, qlist TEXT, used INTEGER)""")
    con.commit()
    db_release(con)


def _today():
    return int(time.strftime('%Y%m%d'))


def _load(rid):
    """读该角色当天状态；跨天自动重置（保留 used 归零）。"""
    db_answer_init()
    con = db_conn()
    r = con.execute('SELECT rid,day,idx,correct,started,qlist,used FROM role_answer '
                    'WHERE rid=?', (int(rid),)).fetchone()
    db_release(con)
    d = _today()
    if (not r) or int(r[1] or 0) != d:
        st = {'rid': int(rid), 'day': d, 'idx': 0, 'correct': 0, 'started': 0,
              'qlist': [], 'used': 0}
        _save(st)
        return st
    try:
        ql = json.loads(r[5] or '[]')
    except Exception:
        ql = []
    return {'rid': r[0], 'day': r[1], 'idx': int(r[2] or 0), 'correct': int(r[3] or 0),
            'started': int(r[4] or 0), 'qlist': ql if isinstance(ql, list) else [],
            'used': int(r[6] or 0)}


def _save(st):
    db_answer_init()
    con = db_conn()
    con.execute('INSERT OR REPLACE INTO role_answer VALUES (?,?,?,?,?,?,?)',
                (int(st['rid']), int(st['day']), int(st['idx']), int(st['correct']),
                 int(st['started']), json.dumps(st.get('qlist') or []), int(st['used'])))
    con.commit()
    db_release(con)


def left_count(rid):
    """今日剩余可参加次数。"""
    cfg = answer_cfg()
    total = int(cfg['other'].get('series_num') or 0)
    st = _load(rid)
    done = st['used'] + (1 if st['started'] and st['idx'] > 0 else 0)
    return max(0, total - done)


def level_ok(lev):
    return int(lev or 0) >= int(answer_cfg()['other'].get('lev') or 0)


def open_now(when=None):
    """是否在开放时段（配置为 [null,h,m,s]，取前两项 h,m）。"""
    t = when or time.localtime()
    cur = t.tm_hour * 60 + t.tm_min
    for _, v in (answer_cfg()['open'] or {}).items():
        s = v.get('start_time') or []
        e = v.get('end_time') or []
        try:
            sm = int(s[1]) * 60 + int(s[2] or 0)
            em = int(e[1]) * 60 + int(e[2] or 0)
        except Exception:
            continue
        if sm <= cur <= em:
            return True
    return False


def start(rid, lev=0):
    """开始/继续一场答题。返回 (ok, msg, st, question_id)。

    ★ 开放时段校验默认**仅在配置存在时**生效；若配置缺失则放行（不因缺配置卡死玩法）。
    """
    cfg = answer_cfg()
    if not cfg['questions']:
        return False, '答题配置缺失', None, 0
    if not level_ok(lev):
        return False, '等级不足', None, 0
    # 时段校验：正式只认配置；**联调/测试**可用环境变量 DSH_ANSWER_OPEN=1 临时放开
    # （不写进 config.json，避免污染正式配置）
    if (not os.environ.get('DSH_ANSWER_OPEN')) and cfg['open'] and not open_now():
        return False, '不在活动时间', None, 0
    st = _load(rid)
    if st['started'] and st['idx'] > 0:
        # 续答
        i = st['idx'] - 1
        qid = int(st['qlist'][i]) if i < len(st['qlist']) else 0
        return True, '', st, qid
    if left_count(rid) <= 0:
        return False, '今日次数已用完', None, 0
    n = int(cfg['other'].get('question_num') or 0) or 20
    pool = sorted(int(k) for k in cfg['questions'].keys())
    # 以 (rid, day) 为种子 ⇒ 同一天同一角色题序可复现（便于回归）
    rnd = random.Random(int(rid) * 100003 + int(st['day']))
    picked = rnd.sample(pool, min(n, len(pool)))
    st['qlist'] = picked
    st['idx'] = 1
    st['correct'] = 0
    st['started'] = 1
    _save(st)
    return True, '', st, int(picked[0])


def submit(rid, qid, answer):
    """判题。answer 为 0..3（对应 a/b/c/d）。返回 (ok, msg, st, correct_answer_idx)。"""
    st = _load(rid)
    if not st['started'] or st['idx'] <= 0:
        return False, '未开始答题', st, 0
    key = answer_key()
    k = key.get(str(int(qid)))
    if not k:
        return False, '题目无答案键', st, 0
    ci = OPT.index(k) if k in OPT else 0
    ok = (int(answer) == ci)
    if ok:
        st['correct'] = int(st['correct']) + 1
    st['idx'] = int(st['idx']) + 1
    if st['idx'] > len(st['qlist']):
        # 答完最后一道 ⇒ 本场结束
        st['started'] = 0
        st['idx'] = 0
        st['used'] = int(st['used']) + 1
        st['qlist'] = []
    _save(st)
    return True, '', st, ci


def settle(rid, correct_num=None):
    """结算并按 `AnswerAward` 阈值发奖（幂等）。返回 (ok, granted_list, correct)。"""
    st = _load(rid)
    c = int(correct_num) if correct_num is not None else int(st['correct'])
    awards = []
    for _, row in sorted((answer_cfg()['award'] or {}).items(),
                         key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0):
        try:
            need = int(row[1]); bid = int(row[2]); cnt = int(row[3])
        except Exception:
            continue
        if c >= need:
            awards.append({'kind': 'item', 'bid': bid, 'amount': cnt})
    ref = 'answer:%d:%d:%d' % (int(rid), int(st['day']), c)
    from reward.service import grant
    res = grant(rid, awards, ref, source='answer')
    # 本场收尾
    if st['started']:
        st['started'] = 0
        st['idx'] = 0
        st['used'] = int(st['used']) + 1
        st['qlist'] = []
        _save(st)
    return True, (res or {}).get('applied') or [], c
