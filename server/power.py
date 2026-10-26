"""战力（战斗评分）系统 —— 基于《绝世唐门》1.4.9 原版数据。

═══════════════════════════════════════════════════════════════════════════
★ 数据来源（CONFIRMED，直接从 APK 读出的原版权重）
───────────────────────────────────────────────────────────────────────────
配置文件：`config_attr.luac` proto[0]
  AttrLen        = 64                  // 共 64 项属性
  AttrId2Key     = {101:'strength',102:'intellect',...}  // id→key
  AttrId2Str     = {101:'力量', 102:'智力', 105:'物攻',...} // id→显示名
  AttrKey2Str    = {'atk_speed':'速度','dodge':'躲闪',...}  // key→显示名
  **AttrPower      = {'atk_speed':450,'dodge':275,'hit':275,
                      'crit':183,'tenacity':183,'atk_p':106,'atk_s':106,
                      'control':90,'anti_control':90,'def_abs':82,'atk_abs':82,...}** // 战力权重
  AttrPartnerPower = 伙伴版权重

**战力公式（原版语义）**：
  战力 = Σ( 属性值[key] × AttrPower[key] )   （只累加"有值且能参与"的属性）
  ★ 权重为 0 的属性（strength/intellect/armor/hp 等基础项）**不参与战力计算**。

★ 提取自：src/lib/luajit_dis.py + config_attr.luac
  实测权重（top）：atk_speed=450 速度 / dodge=275 躲闪 / hit=275 命中 /
                   crit=183 暴击 / tenacity=183 抗暴 / atk_p=106 法攻 / atk_s=106 物攻
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import json
import os

# 原版权重（从 config_attr.luac 的 AttrPower 字典原样取出）—— 只读快照
_HERE = os.path.dirname(os.path.abspath(__file__))
_CFG = os.path.join(_HERE, '_attr_data.json')

_ATTR_POWER = None
_ATTR_STR = None


def _load():
    global _ATTR_POWER, _ATTR_STR
    if _ATTR_POWER is not None:
        return
    try:
        with open(_CFG, encoding='utf-8') as f:
            d = json.load(f)
        _ATTR_POWER = {k: float(v) for k, v in (d.get('AttrPower') or {}).items() if v}
        _ATTR_STR = d.get('AttrKey2Str') or {}
    except Exception as e:
        _ATTR_POWER = {}
        print('!! power: \u52a0\u8f7d _attr_data.json \u5931\u8d25: %r' % (e,))


def attr_power(key):
    """返回单个属性键的战力权重（原版；缺失返回 0）。"""
    _load()
    return _ATTR_POWER.get(key, 0.0)


def calc_power(attrs):
    """战力 = Σ(属性值 × 原版权重)。

    attrs: dict key→数值（如 {'atk_s':120, 'dodge':30, 'atk_p':200, ...}）
    返回: int 战力。
    """
    _load()
    total = 0.0
    for k, v in (attrs or {}).items():
        w = _ATTR_POWER.get(k)
        if w is None:
            continue
        try:
            total += float(v) * w
        except (TypeError, ValueError):
            continue
    return int(total)


def power_items(attrs, top_n=20):
    """列出每项属性对战力的贡献（便于诊断/展示），按贡献降序。"""
    _load()
    out = []
    for k, v in (attrs or {}).items():
        w = _ATTR_POWER.get(k)
        if not w:
            continue
        try:
            out.append((k, _ATTR_STR.get(k, k), float(v) * w))
        except (TypeError, ValueError):
            continue
    out.sort(key=lambda x: -x[2])
    return out[:top_n]