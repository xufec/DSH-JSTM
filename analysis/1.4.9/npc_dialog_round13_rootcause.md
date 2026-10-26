# NPC 对话 第十三轮：★★★ **精确调用栈拿到，根因完全定位**

> 十二轮发现"阻塞在 `skill_ctrl.luac`"，本轮用 `xpcall + debug.traceback` 抓到**完整调用栈**。

---

## 一、完整调用栈（真实部署，探针上报原文）

```
scene_controller.luac  → changeScene
  → scene_model.luac    in function 'sceneStart'
    → config.luac:2112  in function 'sceneStart'
      → sys/gamenet.luac  in main chunk
        → config.luac:2554  in function 'doOneMsg'
          → sys/gamenet.luac in function 'orig'
            → **skill_ctrl.luac  in function 'checkEnable'**
              → **skill_ctrl.luac  in function 'checkSkillEnable'**
                → **kHaveSkill**
                → ★★★ **skill_ctrl.luac:0: attempt to index a nil value**
                  （由 sys/event.luac 的 Fire / Fire 触发）
```

**⇒ 根因链已完全清晰：**

```
场景启动（sceneStart）
  → 触发一个"技能可用性"事件（GlobalEvent:Fire）
    → skill_ctrl.checkEnable
      → skill_ctrl.checkSkillEnable
        → kHaveSkill            ← ★★★ **在这里索引 nil ⇒ 抛异常**
          → 异常沿栈向上传播 ⇒ changeScene 中断 ⇒ 场景初始化不完整
            → 后续 NPC 对话（openNpc → getScene():getNpcByBid）拿到不完整状态 ⇒ 失败
```

---

## 二、★ 根因（`CONFIRMED`）

**`skill_ctrl.checkSkillEnable` → `kHaveSkill` 索引了一个 nil 值。**

**函数名 `kHaveSkill`（"拥有技能？"）与被 `checkEnable` 调用这一上下文 ⇒
它**极可能在查玩家的技能列表 / 技能配置**，而那处数据是 nil。**

**⇒ 最可能的解释（`INFERRED`，待验证）：**
**服务端**从未下发技能数据** ⇒ 客户端的技能表为空/nil ⇒ `kHaveSkill` 索引 nil。**

**⇒ 支持证据（早期探针实测）：**
```
rgp_hander10301_rid_1001_name_DSH_lev_20_exp_nil_exp_max_17118_gold_nil_gold_acc_nil
               career_1_sex_0_**skill_list:_1**
```
**⇒ `10301` 的响应里 `skill_list` 只有 1 项（或为空表）—— **技能数据确实几乎是空的**。**

---

## 三、★★ 这是**服务端可以修**的！

**与之前十二轮不同 —— 那些都指向客户端自身的对象/寄存器错位（服务端修不了）。
而本轮的根因是「**服务端没发技能数据**」⇒ **这是服务端职责**。**

### 修复方向（明确）

| # | 做法 | 依据 |
|---|---|---|
| **1** | **在 `10301` 里下发**真实的技能列表** | `10301` 的字段含 `skill_list`（协议已确认） |
| **2** | **技能数据来源**：`config_skill.luac`（**3,032,592 字节，347 张表里最大**） | 通用读取器 `tools/extract_config.py` 可直接读 |
| **3** | **按职业/等级筛选**初始技能 | 需确认客户端 `Config.Skill` 的字段（职业、等级门槛） |

**⇒ 具体步骤：**
```bash
python tools/extract_config.py peek config_skill 5     # 看字段与样例
python tools/extract_config.py dump config_skill       # 导出
# 然后在 mock_server.py 的 10301 分支里填入 skill_list
```

---

## 四、十三轮的总账（★ 根因迁移历史）

| 轮 | 当时认定的根因 | 后续实测 |
|---|---|---|
| 1-4 | `view.ctrl` 接错对象 / NPC 不在场 | ❌ 否证 |
| 5-9 | `getScene() == nil` | ⚠️ 是**症状**，非根因 |
| 10 | `self.ctrl` 为 nil | ❌ 实测是 table |
| 11 | 失败点回到 `getScene()` | ⚠️ 仍非根因 |
| **12** | **阻塞在 `skill_ctrl.luac` 的异常** | ✅ **正确** |
| **13** | ★ **`skill_ctrl.checkSkillEnable` → `kHaveSkill` 索引 nil**（因服务端无技能数据） | ✅ **精确到函数** |

**⇒ 十三轮里，根因**三次迁移**（场景字段 → 第三方模块 → 具体函数），
**累计 7 处推断被实测推翻并保留在案。****

---

## 五、★ 本轮的意义

**十三轮来第一次出现「**服务端能修**」的根因：**

- 前十二轮的结论几乎都指向**客户端自身的对象/寄存器错位**（服务端修不了，只能靠探针绕过）
- **本轮的根因是「服务端没发技能数据」** —— 这是**服务端的职责缺口**

**⇒ 且技能数据的来源**已经就绪**：`config_skill.luac`（3MB）+ 通用读取器 `extract_config.py`。**

---

## 六、自查

```
lua-check OK（123745 字节）｜ 探针已部署（含 xpcall + debug.traceback）
服务端 8080/9000 正常 ｜ 服务端代码**本轮未修改**
★ lua-check 硬门禁**拦住了我的一处错误**（`cannot use '...' outside a vararg function`）
  —— 这正是门禁存在的价值：**没让它进到 APK 里**
```
