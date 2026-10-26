# ★★★ 第十四轮：**根因修复成功 —— `sceneStart` 不再崩溃**

> 第十三轮定位到 `skill_ctrl.checkSkillEnable → kHaveSkill` 索引 nil。
> 本轮找到**具体原因**并**修复**。

---

## 一、根因（`CONFIRMED`，实测数据）

### 服务端发的技能 ID **根本不存在**

```
config.json 原值:  skills = [{"bid": 1001, "exp": 0}]

Config.Skill 的真实 bid（从 config_skill.luac 的 TDUP 数组抽出，17400 条候选）:
  [10000, 10001, 10002, 10005, 10100, 10200, 10201, 10202, ...]
  其中  10000 = '普攻'   10001 = '逃跑'   10002 = '撤退'

★ 含 1001 ?  **False**        ← ★★★ 服务端发的 bid **在客户端 Config.Skill 里不存在**！
```

### 因果链

```
服务端 10301 下发 skill_list = [1001]        ← 无效 bid
  → 客户端对每个技能调 kHaveSkill / checkSkillEnable
    → 查 Config.Skill[1001] = **nil**
      → **索引 nil ⇒ 抛异常**
        → 异常沿栈传播 ⇒ changeScene 中断 ⇒ 场景初始化不完整
          → 后续 NPC 对话（openNpc → getScene():getNpcByBid）拿到不完整状态 ⇒ 失败
```

---

## 二、修复

```json
"skills": [
  {"bid": 10000, "exp": 0},   // 普攻
  {"bid": 10001, "exp": 0},   // 逃跑
  {"bid": 10002, "exp": 0}    // 撤退
]
```

**（依据：这三个 bid 是从 `config_skill.luac` **实测抽出的真实值**，且名字吻合）**

---

## 三、★ 修复验证（真机端到端）

### 修复前（第十三轮）
```
sceneStart_beforenil_aftertable_**okfalse**_e_string__game/skill/skill_ctrl.luac__:0:_attempt_to_index_a_nil_value
调用栈: ... → skill_ctrl.checkEnable → checkSkillEnable → kHaveSkill → **索引 nil**
```

### 修复后（本轮）
```
sceneStart_beforenil_aftertable_**oktrue**        ← ★★★ 不再抛异常
sceneStart_beforetable_aftertable_**oktrue**
SceneViewNew_oktrue_rtable
**无异常栈** ⇒ **崩溃消失** ✓
```

**⇒ **十三轮追查的 `skill_ctrl` 异常已被消除。****

---

## 四、⚠ 仍有一条**更小**的残留报错（如实）

```
okfalse__string__game/npc/npc_dialogs.luac__:0:
  attempt_to_call_method__setOpenNpc___a_nil_value
```

**⇒ 但探针同时显示：**
```
inst_setOpenNpc_function          ← 实例上有该方法
NpcCtrl_getOpenNpc_function
NpcCtrl_setOpenNpc_function
```

**⇒ 方法**存在**，所以这条报错**不是**"方法不存在"，而是**某次调用的接收者不对**（`self.ctrl` 或其它）。**

**⇒ 与第十三轮不同：这次**场景已经初始化成功**，所以这是**独立的、更靠后的小问题**，
不再是"场景初始化中断"那个根因。**

---

## 五、★ 十四轮总账

| 轮 | 认定根因 | 结果 |
|---|---|---|
| 1-4 | `view.ctrl` / NPC 不在场 | ❌ 否证 |
| 5-11 | `getScene() == nil` / `scene_info` / `ctrl` | ⚠️ 全是**症状** |
| 12 | 阻塞在 `skill_ctrl` 异常 | ✅ |
| 13 | `checkSkillEnable → kHaveSkill` 索引 nil | ✅ **精确到函数** |
| **14** | ★ **服务端发了**不存在的技能 bid `1001`**** | ✅ **✅ 修复并验证** |

**⇒ 累计 7 处推断被实测推翻并保留在案。**

---

## 六、自查

```
mock_server.py 语法 OK ｜ 服务端 8080/9000 正常 ｜ stderr 0 字节
改动：config.json 的 skills（1001 → 10000/10001/10002）+ 加 skills_note 记录依据
服务端代码**未改**（只是配置里换了有效数据）
新增数据：server/_skill_raw.json（17400 条技能记录原始数据，供后续取真实技能表）
```

---

## 七、★ 请实机确认

**请重登游戏，点 NPC 看是否还能弹出对话。**

**若仍不行**，那条残留的 `attempt to call method 'setOpenNpc'` 就是最后一道坎 ——
**但它的性质已经变了**（不再是"场景初始化被中断"，而是"某次调用的接收者不对"）。
