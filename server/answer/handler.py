# -*- coding: utf-8 -*-
"""answer.handler —— 答题活动命令（16100 / 16101 / 16102 / 16103）。

迁移来源：`mock_server.py` 旧 `16xxx` if 块（16100/16101 原为桩，16102 原为
"把提交的答案当作正确答案回显"的**假成功**）。本模块按 `protocol/fields.json`
的权威 SC 逐字段编码，并接 `answer.service`（真判题 + 真发奖 + 幂等）。
"""

import struct

from core import runtime
from core.dispatch import register
from protocol.frame import pack_frame, w_u8, w_u32, w_str
from role.storage import role_state
from answer import service as svc

log = runtime.log


@register(16100)
def handle_16100(h, cmd, body):
    """获取今日参加答题次数 → `SC_16100{count:u8}`。"""
    rid = role_state(h.cfg).get('rid', 1001)
    n = svc.left_count(rid)
    h.request.sendall(pack_frame(16100, w_u8(n & 0xff)))
    log('tcp.log', '  << 16100 SC_16100 count=%d（今日剩余）' % n)


@register(16101)
def handle_16101(h, cmd, body):
    """开始/继续答题 → `SC_16101{code,msg,left_time,index,correct_num,question_id}`。"""
    st = role_state(h.cfg)
    rid = st.get('rid', 1001)
    ok, msg, s, qid = svc.start(rid, st.get('lev', 1))
    out = (w_u8(1 if ok else 0) + w_str(msg) +
           w_u32(int(svc.answer_cfg()['other'].get('interval') or 20)) +
           w_u8(int((s or {}).get('idx') or 0) & 0xff) +
           w_u8(int((s or {}).get('correct') or 0) & 0xff) +
           w_u32(qid))
    h.request.sendall(pack_frame(16101, out))
    log('tcp.log', '  << 16101 SC_16101 ok=%s idx=%s qid=%s' %
        (ok, (s or {}).get('idx'), qid))


@register(16102)
def handle_16102(h, cmd, body):
    """答题 `CS{question_id:u32, answer:u8}` → `SC{index,correct_num,correct_answer,question_id}`。

    ★ `correct_answer` 是**选项序号 0..3**（a=0/b=1/c=2/d=3），依据
      `answer.service.OPT`（键文件里的值就是 a/b/c/d）。
    """
    rid = role_state(h.cfg).get('rid', 1001)
    q = struct.unpack_from('>I', body, 0)[0] if len(body) >= 4 else 0
    a = body[4] if len(body) >= 5 else 0
    ok, msg, s, ci = svc.submit(rid, q, a)
    out = (w_u8(int((s or {}).get('idx') or 0) & 0xff) +
           w_u8(int((s or {}).get('correct') or 0) & 0xff) +
           w_u8(int(ci) & 0xff) + w_u32(q))
    h.request.sendall(pack_frame(16102, out))
    log('tcp.log', '  << 16102 SC_16102 qid=%d 提交=%d 正确=%d 累计对=%s%s'
        % (q, a, ci, (s or {}).get('correct'), '' if ok else ' (%s)' % msg))


@register(16103)
def handle_16103(h, cmd, body):
    """答题超时结算 `CS{correct_num:u8}` → `SC{correct_num:u8}`（按阈值发奖，幂等）。"""
    rid = role_state(h.cfg).get('rid', 1001)
    cn = body[0] if body else 0
    ok, applied, c = svc.settle(rid, cn)
    h.request.sendall(pack_frame(16103, w_u8(c & 0xff)))
    log('tcp.log', '  << 16103 SC_16103 correct=%d 发奖条目=%d' % (c, len(applied)))
