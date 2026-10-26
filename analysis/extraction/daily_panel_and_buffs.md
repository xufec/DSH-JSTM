# 日常面板（13786/13781 + 10924）与 `buffs` 取证

> 用户报障：「日常打开后为空白」「头像旁的状态点击不了」
> 日期：PHASE 2.27 | 证据来源：1.4.11 APK 反汇编 + 实机抓包 + 运行实测

---

## 一、日常面板的数据分工（CONFIRMED，反汇编 `game/daily/*.luac`）

`daily_data.luac` 的数据模型（L4）：

```lua
{ …, 'new_act_list', 'selected_id', 'open_tab', 'activity_list', 'daily_list', … }
```

| 面板部分 | 数据来源 | 服务端是否需要供数 |
|---|---|---|
| **`daily_list`**（日常任务行）| 客户端**自己**从 `Config.RiChang`（客户端配置）建行；`cur_num`/`cur_huoli`/`total_huoli` 来自服务端 | ✅ 已供：`13786.richang_list{id,num}` + `13781{total_val, huoli_list}` —— **两条均已核对：回包 24 条真数据、字段与 1.4.11 格式一致** |
| **`activity_list`**（活动行）| **`10922` / `10924`**（活动族）| ❌ **`10924` 现为空表**（R49 为抑制"活动预告弹窗"而设的取舍）|

**★ 关键证据**（`daily_ctrl.luac`）：
- L37：`'request10924'` 绑定在 **`login_event_success`** 事件上
- L73：登录成功后调用 `request10924`
- L1548 的 proto 同时持有 `on10922/request10922/on10923/request10923/on10924/request10924/on10925/request10925/dailyFun`

⇒ **日常面板一登录就拉 `10924`**。它回空表 ⇒ **面板的活动列表为空**。

### 结论与两个可选修法

1. **保留 R49 取舍**（10924 空表）⇒ 日常面板的活动列表继续为空（无弹窗）；
2. **改回下发**（`config.json` 的 `send_personal_act_list = true`）⇒ 活动列表有内容，但 **R49 记录的"活动预告弹窗刷屏"会回来**（同一枚硬币两面）。
   - ★ **0 成本验证**：把 `server/config.json` 的 `send_personal_act_list` 改成 `true` 并重启，看日常面板是否恢复 —— **这能一次性确认"日常空白 = 10924 空表"这个因果**。
3. **待试的第三条路**（未验证）：R49 的变体 B「把那 9 个会被提示的 `config_richang` id 以 `status=1` 补进去」曾被判失败（t4 仍弹窗）；
   但**目前已知** `10924` 条目受 `Config.Function[id]` 门槛（`is_open==1 && open_lev<=lev`）约束（见 `real_cs_formats_1_4_11.md` §6.3/§6.5）——
   **可试"只下发 config_function 里合格、且不含那 9 个 richang id 的最小集合"**，观察是否既能填面板又不弹窗。

---

## 二、「头像旁的状态」（`buffs`）现状（CONFIRMED）

- 1.4.11 权威表：`SC_10301[31] = buffs__T__bid@I##duration@I##count@C##effect@D|Dsc10301effect|`
- `mock` 的 `build_10301` 对 `buffs` **发 `w_u16(0)`（空表）**
- `10640`（buff 列表查询）读 `db_buff_list(rid)`；而 **`role_buffs` 表存在但 0 行** ⇒ 也回空
- **实机 `10640` 共发 21 次**（客户端确实在问）

⇒ **"头像旁状态点不了"的直接原因是"没有 buff"**。
**是否应给新角色预置 buff：本会话未取到证据 ⇒ 未实现（不编造）**。
替换点：若日后确证原版给新号某个初始 buff，写入 `role_buffs`（或 `ROLE_DEFAULTS`）即可，`10640` 与 `10301.buffs` 会自动带上。

---

## 三、本轮已修的（与本文件相关的两项）

| 症状 | 根因 | 状态 |
|---|---|---|
| **头像空白** | `ROLE_DEFAULTS['face_id'] = 0` ⇒ `SC_10301` 发 0 | ✅ 已修（默认 **100**，来自 `config_role_face.RoleFace` 100..113）|
| 多面板随机错位 | `runtime.CUR_VER` 全局竞态 | ✅ 已修（线程局部，见 `ROOTCAUSE_cur_ver_global_race.md`）|
