"""从服务端日志里抽出 Phase D 战斗实测证据，落到 logs/1.4.9/battle/。

用法（在项目根目录）：
    python tools/extract_battle_logs.py

输入：server/logs/http.log（客户端探针上报）、server/logs/tcp.log（协议帧原文）
输出：
    logs/1.4.9/battle/monster_click.log   场景怪物清单 + 点击链路
    logs/1.4.9/battle/battle_start.log    CS_20002 请求与 SC_20002 应答
    logs/1.4.9/battle/battle_action.log   SC_20010/20012/20013 回合与伤害
    logs/1.4.9/battle/battle_result.log   SC_20020/20023 结算与奖励
    logs/1.4.9/battle/battle_raw_tcp.log  tcp.log 里战斗相关的原文行
"""
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = os.path.join(ROOT, 'server', 'logs')
OUT = os.path.join(ROOT, 'logs', '1.4.9', 'battle')


def read(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        return []
    # 历史日志里偶有编码混杂，用 replace 容错
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().splitlines()


def grep(lines, pat):
    r = re.compile(pat)
    return [l for l in lines if r.search(l)]


def write(name, header, blocks):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(header.rstrip() + '\n\n')
        for title, rows in blocks:
            f.write('=' * 72 + '\n')
            f.write('## %s  (%d 行)\n' % (title, len(rows)))
            f.write('=' * 72 + '\n')
            if not rows:
                f.write('(无)\n')
            for l in rows:
                f.write(l + '\n')
            f.write('\n')
    print('写出 %-40s (%d 行合计)' % (name, sum(len(r) for _, r in blocks)))


def main():
    http = read('http.log')
    tcp = read('tcp.log')

    # ---------- 1. 点击链路 ----------
    click = (grep(http, r't=bt_mon') + grep(http, r't=bt_click') +
             grep(http, r't=bt_hook') + grep(http, r't=bt_send'))
    write('monster_click.log', """
# Phase D 战斗实测：场景怪物清单 + 怪物点击链路
# 目标 APK anzbao/jstm.apk (1.4.9, com.shiyue.dldl.ewan.qihoo)；未使用 1.4.11
#
# 字段含义：
#   bt_mon   = SceneModel.monList 快照（客户端场景里真实存在的怪物）
#   bt_hook  = BattleCtrl 处理函数钩子安装结果
#   bt_click = 触发点击（真实事件 GlobalEvent:Fire(SCENE_MONSTER_CLICK, vo)）
#   bt_send  = 客户端实际调用 BattleCtrl:csFightMon 时带的 mon_id
#
# 复现：pwsh tools\\build_fakelogin.ps1  →  见 analysis/1.4.9/battle/battle_flow.md
""", [('客户端探针上报（bt_mon / bt_hook / bt_click / bt_send）', click)])

    # ---------- 2. 战斗开始 ----------
    start = (grep(tcp, r'cmd=20002') + grep(tcp, r'20002') +
             grep(http, r't=bt_in&v=csFightMon') + grep(http, r't=bt_out'))
    write('battle_start.log', """
# Phase D 战斗实测：战斗开始（CS_20002 对怪物发起战斗）
#
# 帧格式：[u32 BE payload_len][u16 BE cmd][body...]
# 实测原文：
#   00 00 00 0a 4e 22 | 00 00 4e 36 13 8f 00 00
#   payload_len = 0x0a = 10 = 2(cmd) + 8(body)
#   cmd         = 0x4e22 = 20002
#   body        = mon_id:int32 = 0x00004e36 = 20022  + 4 字节**尾部脏数据**
#
# ★ 客户端短消息会带定长缓冲区残留（trailing garbage）：
#   服务端**只按消息定义读字段、忽略多余尾部**，否则解帧必错。
""", [('客户端探针：csFightMon 调用参数', grep(http, r't=bt_in&v=csFightMon')),
      ('服务端收到的 20002 帧', grep(tcp, r'20002'))])

    # ---------- 3. 战斗过程 ----------
    action = (grep(http, r't=bt_in&v=(scFightData|scFightRound|scRoundStart|scAddRole|scAuto|scSelectSkill|playEnd)') +
              grep(tcp, r'cmd=(20010|20011|20012|20013|20014|20015)'))
    write('battle_action.log', """
# Phase D 战斗实测：战斗过程（SC_20010 初始化 / 20012 小回合 / 20013 回合开始）
#
# 本文件在**服务端实现战斗之前**为空 —— 这正是需要补齐的缺口。
# 完整体现在 analysis/1.4.9/battle/battle_protocol_matrix.md §4。
""", [('客户端收到并解析的战斗消息（bt_in）', action)])

    # ---------- 4. 战斗结果 ----------
    result = (grep(http, r't=bt_in&v=(scFightEnd|scFightEndData|hander_20022)') +
              grep(tcp, r'cmd=(20020|20022|20023)') +
              grep(tcp, r'(获得|奖励|掉落|经验|金币|exp|gold|drop|coin|role_assets)'))
    write('battle_result.log', """
# Phase D 战斗实测：战斗结果与结算（SC_20020 胜负 / SC_20023 结算明细）
#
# ★★ 本阶段最关键的一个**未知**就在这里：
#   SC_20020 只有 result:uint8；SC_20023 只有 role_hurl_list/val_list/msg。
#   经验 / 金币 / 掉落 **不在**这两条战斗消息里。
#   必须靠实测确定它们实际走哪条协议（候选 10409 / 12742 / 10302 / 10500 / 10501）。
""", [('客户端收到并解析的结算消息（bt_in）', result)])

    # ---------- 5. 原始 tcp ----------
    raw = grep(tcp, r'(cmd=20\d\d\d|<< 20\d\d\d|SC_20\d\d\d)')
    write('battle_raw_tcp.log', """
# Phase D 战斗实测：server/logs/tcp.log 里战斗相关原文（未经加工的原始行）
""", [('tcp.log 战斗相关原文', raw)])


if __name__ == '__main__':
    main()
