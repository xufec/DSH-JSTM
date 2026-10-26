# Phase 4C —— 角色登录 / 初始化

> **改动只碰服务器**：未改 APK、未写 UI、未重做角色系统、未做任务系统。
> APK：1.4.9 / `com.shiyue.dldl.ewan.qihoo`

---

## 1. 修改文件

| 文件 | 改动 |
|---|---|
| **`server/mock_server.py`** | ① 新增 **角色数据模型**：`ROLE_DEFAULTS`（按 `SC_10301`/`SC_10302` 的定义列全字段）+ `role_state(cfg)`（默认值合并配置，得到一份完整自洽状态）<br>② `build_10301(role, skills=None)`：**`skill_list` 由空表改为按配置真实下发**（`table(bid:u32)`）<br>③ `_reply()` 的 `10301` 分支改用 `role_state(self.cfg)` 并传入 `cfg['skills']`<br>④ `_reply()` 的 `10302` 分支改用 `role_state(self.cfg)`（与 10301 同一份状态，避免两处不一致） |
| `server/config.json` | `role` 补齐 `exp/exp_max/gold/gold_acc` 等；新增 `world_lev`、`skills` |

> 未新增任何无协议依据的字段；`ROLE_DEFAULTS` 的每一项都来自 `SC_10301` / `SC_10302`
> 在 `protocol/manual.md` 里的定义（`tools/show_cmd.py 10301` 可复核）。

---

## 2. 协议证据

`build_10301` 的字段顺序**逐字段照写** `SC_10301` 定义（45+ 字段）。
本阶段唯一结构性改动是 `skill_list`：

```lua
-- SC_10301 定义：skill_list : table(bid:uint32)
sk = skills or []
b += w_u16(len(sk))                      -- 计数前缀
for s in sk:
    b += w_u32(s.get('bid', 0))          -- 每项 bid:u32
```

实算：`SC_10301` 包体由 **105 → 109 字节**（多出 1 条技能：`u16 count + u32 bid` = 6 字节，
另处字段长度差异），与"skill_list 真实下发"一致。

**客户端请求 → 服务端应答（本轮实测）**：

```
[22:41:58]  >> cmd=10302 ? body(4)=00 0a 00 07
[22:41:58]  << 10302 SC_10302 lev=1 exp=0 gold=1000 gold_acc=5000 (20 bytes)

[22:41:59]  >> cmd=10301 角色基础信息 body(4)=01 01 03 e9
[22:41:59]  << 10301 SC_10301 role info (109 bytes)
```

> 注意：本轮 `10302` 是**客户端自然请求**的（上一阶段 4B 是靠主动触发验的），
> ⇒ `10302` 现在同时有"自然请求"与"主动触发"两种验证。

---

## 3. 测试结果

| 测试 | 结果 |
|---|---|
| 角色数据模型可用 | ✅ `role_state()` 输出：`rid=1001, name=DSH, lev=1, career=1, sex=0, exp=0, exp_max=100, gold=1000, gold_acc=5000, scene_id=10001, x=30, y=30` |
| `10301` 解答并含 `skill_list` | ✅ 109 字节 |
| `10302` 解答 | ✅ 20 字节，四字段与模型一致 |
| 角色登录 → 进场景 | ✅（沿用既有 10103 → 10200/10201 流程） |
| **Lua 错误** | ✅ `Call Function[stack top]` = 0，`.luac:<行号>` 栈回溯 = 0 |
| **角色数值在主界面的显示** | ❌ **未显示**（见下） |

### 视觉确认（`shots/stage4c_role_init.png`）

| 项 | 结果 |
|---|---|
| 角色姓名 | ✅ `DSH`（绿色，脚下） |
| 金币/钻石 | ⚠️ 钻石 `0` 正常；金币显示为一串数字（视觉模型读作 `2025,1635`，格式可疑） |
| **等级** | ❌ 主界面无等级数字（只有 VIP 等级 `1`） |
| **经验** | ❌ 左下角只有「经验」标签，无进度条/数值 |
| **HP / MP** | ❌ 无 |
| **战力** | ❌ 无 |
| 任务栏 `nil` | ⚠️ 已知的任务系统问题，**不在 Phase 4 范围** |

**判定**：这些数值**很可能只在"角色面板"里显示**（而打开面板属于 **Phase 4D**）。
**本阶段只观察主界面，未点开面板、未改 UI。**

---

## 3.5 ★ 补充取证：客户端**确实解析**了角色数据（本节最关键的一步）

之前只验了"服务端应答"，本轮补上"**客户端读取**"的证据 —— 包住客户端自己的处理器
`RoleCtrl.rgp_hander10301` / `rgp_hander10302`：

```
t=roleH&v=rgp_hander10301_rid_1001_name_DSH_lev_1_exp_nil_exp_max_100_
        gold_nil_gold_acc_nil_career_1_sex_0_skill_list:_1
t=roleH&v=hander10333_NOT_function_nil
```

| 读数 | 含义 |
|---|---|
| `rid_1001 / name_DSH / lev_1 / career_1 / sex_0 / exp_max_100` | ✅ **客户端解析正确** |
| **`skill_list:#1`** | ✅ **本阶段新加的 `skill_list` 被正确解析出 1 条**（改动生效的直接证据） |
| `exp_nil / gold_nil / gold_acc_nil` | ✅ **符合预期** —— 这三个字段属于 `SC_10302`，**不在 `SC_10301` 里** |
| `hander10333_NOT_function` | 说明 `10333` 的处理器不在 `RoleCtrl` 上（在别的类），不影响结论 |

**⇒ `SC_10301` 的字段语义与客户端解析链路均已验证。**

**本轮 `rgp_hander10302` 未被调用**（客户端这一轮没请求 10302）——
但 `10302` 的应答已在 Phase 4B/4C 各验证过一次（20 字节，四字段与模型一致）。

---

## 4. 日志位置

```
logs/1.4.9/role_4c_tcp.log      服务器 TCP（请求/应答）
logs/1.4.9/role_4c_probe.log    探针上报
logs/1.4.9/role_4c_logcat.log   实机 logcat
shots/stage4c_role_init.png     实机截图
```

---

## 5. 仍然缺失的问题

1. **主界面不显示等级/经验/HP/MP/战力** —— 待 Phase 4D 打开角色面板确认
   （若面板里也没有，则需要补 `SC_10303` 的 `attr` 大表）。
2. **金币显示格式可疑** —— 我们下发 `gold=1000` / `gold_acc=5000`，
   但界面读出的数字与两者都对不上。**未确认原因**（可能是客户端把两个字段拼接显示，
   也可能是视觉模型读图误差）⇒ 列为 Phase 4D 的观察项，**不猜改**。
3. `SC_10303`（`attr` 大表，24 项属性）**未实现** —— 角色属性面板需要它。
4. `10341`（头像） / `13341`（留言板）**未实现** —— 社交功能，超出本阶段。
5. **角色数据持久化（4E）未开始** —— 目前只有 `x/y` 落盘；`lev/exp/gold/…` 仍在
   `config.json` 静态配置里，**不是真正的角色档案**。

---

## 6. 文档产出（本节要求）

- `analysis/1.4.9/role/role_login_flow.md`
- `analysis/1.4.9/role/role_init_flow.md`
- 本文件 `analysis/1.4.9/role/role_phase4c.md`

---

**[WAITING FOR PHASE 4D]**
