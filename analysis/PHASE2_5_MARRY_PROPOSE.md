# PHASE 2.5 —— 结婚求婚闭环（18300 → 18301 → 18302 → 18303）

> 隔离已验证（PHASE 2.4）⇒ 求婚链路现在可**双角色实测**。

## 一、★ 关键取证（先解决"对象从哪来"）

反汇编 1.4.11 客户端 `game/wedding/*`（15 个模块，本次提取到 `_tmp_wedding/`）：

| 证据 | 结论 |
|---|---|
| `wedding_ctrl.luac` proto#10 `request18300` | 只做 `GetPrototype(18300)` → `SendProtocal`，**不设置任何字段** |
| `fields.json` `CS_18300` | **空消息** |
| `wedding_model.luac` proto#2 `resetStateData` | `objRid=0 / objSrvId=''` —— 由**服务端推送**填充 |
| `wedding_model.luac` 的 `on18301` | 从 `SC_18301{obj_rid,obj_srv}` 取发起者 |

⇒ **客户端从不上传求婚对象；"服务端如何确定对象"在客户端侧没有证据。**
按纪律**不编造**该机制，改为把它收敛为一张明确的服务端意向表：

```
role_marry_propose(from_rid PK, to_rid, ctime)
```

`18300` 只负责**确认并发起**（读意向 → 校验 → 推 18301）。意向由服务端自身选取逻辑（或 GM/测试）写入。

## 二、实现（server/mock_server.py）

| cmd | 语义 | 行为 |
|---|---|---|
| 18300 | 发起求婚 | 读 `role_marry_propose`；校验（对象存在/非自己/双方未婚）→ 写日志 + **推 `18301` 给对象**；无意向 ⇒ `code=0`「暂无求婚对象」 |
| 18301 | 求婚反馈（**推送**） | `{self_state,spouse_state,boyname,grilname,obj_rid,obj_srv}`，obj_rid=发起者 |
| 18302 | 求婚应答 | 读「谁在向我求婚」→ 同意：**双方 `role_marry` 置已婚且互指配偶** + 推 `18303`；拒绝：清意向 + 推 `18303` |
| 18303 | 求婚结果（**推送**） | `{self_state,spouse_state,msg}` |

新增：`role_marry_propose` 表 + `db_marry_propose_init/set/get/of_target/del`。
从回执族-E 集合移出 `18302`（否则遮蔽）。

## 三、验证（可复跑）

```
python server/mock_server.py --http 8191 --game 9191
python tools/test_marry_propose.py --port 9191     →  ALL PASS（15 项）
```

双连接实测（A=1001 'DSH'，B=2001 '求婚B测试'）：
```
双方未婚 → A 无意向求婚=code:0(诚实) → 写入意向 A→B → A 求婚=code:1
→ B 收到 18301(obj_rid=1001, boy='DSH', gril='求婚B测试')
→ B 同意(18302)=code:1 → B 收到 18303(self=1,spouse=1)
→ A state=1 spouse='求婚B测试' ／ B state=1 spouse='DSH'（互指）
→ A 离婚检查 18313 ret=1
```

**回归**：`test_team` / `test_jiebai` / `test_marry` / `test_multi_session` **全部 ALL PASS**。
**门禁**：`lint_dispatch_shadow` → `✓ 无分发遮蔽`（1430/0/0）。`py_compile` OK。
**清理**：5 张新表均 **0 行**，`roles` 只剩 1001。

## 四、诚实边界

| 项 | 状态 |
|---|---|
| 18300 的**对象选取机制** | **UNKNOWN**（客户端无证据）⇒ 以服务端意向表承载，**不假装是原版机制** |
| 18304-18309 婚宴 | 未实现（需仪式参与者） |
| 18319/18320 婚宴场景 | 返回零值/空表 |
| 离婚的**对方确认** | 未实现（当前单方 18316 即落定） |

## 五、下一步

**结拜多人**（利用已成立的隔离 + 19524 邀请）→ **时装 10573-10578 / 光环 19100/19103** → **拍卖 18020/18021**。

[PHASE 2.5 结婚求婚闭环完成]