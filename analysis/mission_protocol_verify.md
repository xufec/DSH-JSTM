# 任务系统协议核验与订正（2026-09-17）

> 依据：真实反汇编 / 真机客户端字节流，不猜。
> 证据来源：
> - `analysis/mission_ctrl.luac` 反汇编（RegisterProtocal 注册表 + receiveHandler/submitHandler 函数体）
> - `analysis/mission_data2.luac` 反汇编（任务数据分发）
> - `proto_defs.py`（protocol/manual.md 解析出的真实协议表）
> - `mission_config.json`（从客户端 config_mission.luac 提取，846 条）

---

## 一、协议注册映射（已核验，mission_ctrl.luac proto[11]）

| 命令 | 客户端处理器 | 说明 |
|------|------|------|
| 12400 | handle12400 | 任务列表推送（SC 无 code） |
| 12401 | handle12401 | 任务列表推送（另一结构） |
| 12402 | receiveHandler | 接取任务应答 |
| 12403 | submitHandler | **提交任务应答** |
| 12404 | giveUpHandler | 放弃任务应答（当前不回包 = no-op） |
| 12405 | handle12405 | 任务增量更新（SC 无 code） |
| 12406 | deleteAccessHandler | 删除/结束任务列表（SC 无 code） |
| 12407 | addAccessHandler | 增加接取列表 |
| 12408/12409 | deleteCanHandler/addCanHandler | 可接取增减 |

---

## 二、提交应答 code 语义（关键订正，proto[46] 实测反汇编）

`submitHandler(12403)` 函数体核心字节码：

```
TGETS A=2 B=1 ['code']      ; resp.code
GGET  A=3 D=1               ; global[1] = TRUE(1)
ISNEV A=2 D=3               ; if resp.code ~= TRUE then
  ...（跳转到 31）
31 GGET A=2 D=13            ; global[13] = message
   TGETS A=3 B=1 ['msg']    ; resp.msg
   CALL                     ; message(resp.msg)   ← 失败分支
（TRUE 分支）mission_data:del(); panel:update(); Fire(UPDATE_MISSION)
```

**结论：`code == TRUE(1)` 才是提交/接取成功；否则客户端 `message(resp.msg)`。**
若 msg 为空 → 空白提示框。

### mock_server 原实现（写反）→ 已订正

| 分支 | 原 `code` | 订正后 | 后果（原） |
|------|-----------|--------|-----------|
| 12403 提交成功 | `0` | **`1`(TRUE)** | 客户端当失败→`message('')` 空白框 + 不删任务 + 反复提交 |
| 12403 条件未满足 | `1` | **`0`** + msg | 客户端当**成功**→把未完成任务误删 |
| 12403 已提交(幂等) | `0` | **`1`**(TRUE) | 空白框 |
| 12403 不存在任务 | `1` | **`0`** + msg | 当成功 |
| 12402 接取成功 | `0` | **`1`**(TRUE) | 空白框（接收方 `message('成功接取任务')` 只走 TRUE 分支） |

（12405/12406 无 code 字段，不受影响。）

---

## 三、任务条目字段顺序（已核验）

`SC_12400/12401/12402.missions/12405` 元素（每项 34 字节）：

```
mission_bid:u32, mission_status:u8, commit_num:u16, loop_count:u16,
loop_num:u16, code:u8, process_status:u8, target:u32, target_value:u32,
value:u32, show_lave_time:u8, lave_time:u32, accept_time:u32
```

- 与 `proto_defs.SC_12400/12401/12405` 完全一致。
- `loop_count`（已循环）在 `loop_num`（总循环）之前——此前疑虑已排除。
- 客户端 `mission_data2.luac` 与 `mission_ctrl.luac proto[37]` 引用的字段名
  `(mis_bid/mis_status/mis_target/target_value/value/process_status/loop_num/
  loop_count/commit_num/show_lave_time/lave_time/accept_time)` 与之对应无缺漏。

---

## 四、线级回归（通过）

`test_mission_frames.py` 对订正后字节自解码断言全部 PASS：
12402 `code=1`、12403 成功 `code=1` / 失败 `code=0`、条目长度 34 / 列表 36、
字段顺序逐项还原一致。

---

## 五、保持"不回包"的项（不猜原则，延续 13200/15801 先例）

- **20504**（好友回归任务，CS_20504/SC_20504）：客户端确在 tcp.log 发出，
  但 SC_20504 条目含 `D|Dsc20504ext_list|`、`D|Dsc20504item_list|` 未解出动态子表，
  `CS_20504` 定义 type:u8 与真实 body(5) 也不符 ⇒ 回包需猜，**宁可留在面板空白也不回**。
- **12404**（放弃任务 giveUpHandler）：未接入，不回包=放弃功能暂无效，无报错。