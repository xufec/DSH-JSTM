# -*- coding: utf-8 -*-
"""R64 实验：给挂机任务填上**真实的 `target`（怪 bid）**。

依据（`ghost_mon` proto#1 `initData` 逐条反汇编）：
    mis = MissionCtrl:getInstance():getMissionData():getMission(data.mission_bid)
    self.mon_bid = mis.mis_target        -- ★ 客户端本地任务的 mis_target
    self:createMon()
而 `SC_12400.missions[]` 的第 8 个字段正是 `target:u32` —— 服务端唯一能填它的地方。
我们库里 `missions[10010].target = 0` ⇒ `Config.Mon[0]` = nil ⇒ `createMon` 第 ④ 条早退。

怪 bid 取自 `config_guaji` 的等级段（lev 70 ⇒ 10105 乾坤日月谷）。

用法：
    python tools/exp_mission_target.py            # 只读
    python tools/exp_mission_target.py --set 10105
    python tools/exp_mission_target.py --restore 0
"""
import io
import json
import os
import sqlite3
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
DB = r'server\state\roles.db'
RID, BID = 1001, 10010


def show():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    r = con.execute('SELECT * FROM missions WHERE rid=? AND mission_bid=?', (RID, BID)).fetchone()
    con.close()
    if r:
        d = dict(r)
        print('  10010: status=%s target=%s target_value=%s value=%s'
              % (d['mission_status'], d['target'], d['target_value'], d['value']))


def set_field(col, val):
    con = sqlite3.connect(DB)
    con.execute('UPDATE missions SET %s=? WHERE rid=? AND mission_bid=?' % col, (val, RID, BID))
    con.commit()
    con.close()


print('实验前：')
show()

if '--set' in sys.argv:
    v = int(sys.argv[sys.argv.index('--set') + 1])
    set_field('target', v)
    set_field('mission_status', 2)          # 同时要"在途"，12400 才会带上它
    print('\n已设 target=%d 且 mission_status=2' % v)
    show()
    print('  （需重启客户端才会重新拉 12400）')

if '--restore' in sys.argv:
    v = int(sys.argv[sys.argv.index('--restore') + 1])
    set_field('target', v)
    set_field('mission_status', 3)
    print('\n已还原 target=%d 且 mission_status=3' % v)
    show()
