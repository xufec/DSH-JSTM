# 1.4.11 重构包：删渠道登录 · 账号系统 · 三区隔离

> 日期：2026-10-17 ｜ 目标包：`anzbao/jstm_142165.apk`（1.4.11 / `com.shiyue.dldl.ewan.baidu2` / versionCode 46）
> 产物：**`patched/jstm_1411_3zones.apk`**（267.4 MB，v1+v2 已签名）
> SHA-256：`D1F799804A3611330EFD26AC34968E3BA93B1B15827196C1940CBCF346B8FEEF`
> 证据分级沿用项目五档：**CONFIRMED**（直接读产物/数据）> **VERIFIED**（实机/活服实测）> STRONG_INFERENCE > INFERENCE > UNKNOWN。

---

## 一、你报的 5 个问题：结论

| # | 问题 | 根因（已定位） | 处理 | 证据 |
|---|---|---|---|---|
| 1 | 登录按钮点了没反应 | **上一版注入块劫持了选区列表入口**：把 `managerDefualtServerListByJsonObj` 换成"完整列表入口"的调用，**吞掉了 `Fire(DEFAULE_SERVER_SUCCESS)`** —— 而登录页从「用户登录(view4)」切到「选区/进入游戏(view1)」**只靠这个事件**（`denglu_ctrl`：`request_defualt_server_success -> loginView:showPanel(1)`）。请求其实发出去了、服务端也回了，界面纹丝不动 | **彻底移除客户端对选区列表的劫持**：选区列表回归**服务端下发**（这本就是该游戏的原生机制，服务端已能正确返回三区） | VERIFIED：实机点「登录」→ 从「用户登录」正常进入「唐门一区 / 点击选区 / 进入游戏」页（`shots/_3z_after_login_btn.png`） |
| 2 | 忘记密码点了没反应 | 它调 `sdkOnLogin()` → `cc.Device:beginThirdPartyLogin()` → **渠道 SDK**；渠道已按你的要求整体关闭（dex `EWanSdk.is_close=true`）⇒ 死键 | 在 config 阶段接管 `cc.Device.beginThirdPartyLogin`，改为打开**账号管理面板** | VERIFIED：实机「切换账号」弹出面板（`shots/_3z_account_panel.png`），`beginThirdPartyLogin` 钩子安装有运行日志 |
| 3 | 切换账号容易丢账号 | 官方实现（非平台登录时）是 `restart()`，重启后只剩**最近一次**账号；而「一键注册」每次都生成**随机新账号**（现库里 6 个账号有 4 个是这种随机名）；客户端只保存"当前一个"密码 ⇒ 之前建过的账号找不回来 | ① 客户端**本地账号簿**（`dsh_accounts`，≤12 条 账号+密码）② **账号面板**（列出历次账号，点一下自动填入，可删）③ 面板里的 **「新建账号」**：清空「用户登录」表单 + 清掉 `loginData` 里的旧账号/旧角色，可直接输入或点「一键注册」④ 服务端 `accounts` 记录 | VERIFIED：面板→新建账号→输入 `newacct1980/123456`→登录→进入游戏：服务端 `账号新建 uid=newacct1980`、`1110 srv=3 roles=0`、进入**建角视图**；客户端账号簿变为 `newacct1980⇥123456` + `6742f57GOKVV⇥…`（`shots/_3z_new_account.png`、`_3z_enter2.png`） |
| 4 | 一服建角，二三服自动同步 | `roles` 表**没有 srv_id**；`db_roles_of_uid()` 恒返回该账号**所有**角色且 `srv_id` 写死 `'1'`；10102 登录不校验区服 | ① `roles.srv_id`（加列 + 历史行回填 1 区）② CS_1110 真正消费 `enter_srv_id` 并按区过滤 ③ CS_10101 建角落在**本次登录选中的区** ④「一区一角色」⑤ CS_10102/10103 **跨区登录直接拒绝** | VERIFIED：离线 23 项 + **活服 11 项**全 PASS（见 §五） |
| 5 | 要账号管理系统（本地 + 服务端） | — | 服务端 `accounts` 规范化 + 密码鉴权；客户端账号簿 + 面板；`/DSH_ADMIN/accounts` 可查「每个账号在每个区有什么角色」 | VERIFIED：`GET /DSH_ADMIN/accounts` 输出见 §五 |

---

## 二、改动清单

### 服务端（Python）

| 文件 | 改动 |
|---|---|
| `server/persistence/db.py` | 迁移（**只加列，不动数据**）：`roles.srv_id`；`accounts.pwd_hash/last_login_ts/last_srv_id/login_count`。新增 `_ensure_column()`（幂等 ALTER）。**每次启动**把 `srv_id` 为空的行归到 1 区（防"隐形角色"） |
| `server/role/storage.py` | `_DB_COLS += srv_id`、`_DB_TO_SC += srv_id`（下发 `srv_id` 与真实区一致）；`_sc_to_db_updates()` 带上 `srv_id`（`role_state()` 播种的行不再写成 NULL） |
| `server/account/service.py` | 按区过滤角色 `db_roles_of_uid(uid, srv_id)`；建角落区 + 一区一角色 `db_create_role(..., srv_id)` / `db_role_in_srv()`；**账号规范化与鉴权** `db_account_upsert()`（首登绑定 / 密码错误拒绝 / 刷新 last_login*）；CS_1110 解析 `enter_srv_id` + `token`(=密码)，失败回 `code=0 + msg`；CS_10101 落在 `h._srv_id` |
| `server/mock_server.py` | CS_10102/10103：解析 CS 的 `srv_id`（**容忍两种编码**：真机 `rid+单字节区号`、spec 的 `u16 长度字符串`），**跨区/越权一律拒绝**；校验条件由 `_rid != _cur` 放宽为 `_rid`（否则"请求 rid 恰好等于默认 rid"会跳过校验） |
| `server/gm/console.py` | `/DSH_ADMIN/accounts` 扩充：`pwd_set`（只给布尔，不回显哈希）、`last_login_ts`、`last_srv_id`、`login_count`、**按区的角色清单** |
| `server/config.json` | 两个开关：`account_auth`（默认 true）、`one_role_per_zone`（默认 true），各带说明 |

### 客户端（`server/dsh_refactor.lua` → 追加进 `assets/src/config.luac`）

| 块 | 内容 |
|---|---|
| [1] 本地地址 | `URL_PATH` / `CDN_*` / `get_servers_url` / `get_notice_url` / `UPDATE_VERSION_MAX = NOW_VERSION`（必须是**函数**；写成字符串会让客户端抛错并中断登录界面构建） |
| [2] `NO_PLAY_VIDEO = true` | 跳过开场 CG。**不能靠删 `gamecg.mp4`**：`file_update` proto#39 只对 writable 的两个副本做 `isFileExist`，默认路径不判断 ⇒ 文件缺失时 `ccexp.VideoPlayer:play()` 失败，native 弹「视频问题/无法播放此视频」把启动卡死（实测 `Cocos2dxVideoView: Error: 1,0`） |
| [3] 账号系统 | 本地账号簿 `dsh_accounts`（`cc.UserDefault`，`name\tpwd` 逐行，≤12，自动从既有 `usrNameList` 播种）；账号面板（用游戏自己的 `createButton/createLabel/createScale9Sprite/PathTool` 构建）；`DengluCtrl.on1110Rolelist` 包一层，登录成功即记账；`cc.Device.beginThirdPartyLogin` / `sdkSwitchAccount`（仅登录界面）接管为面板入口；填完账号自动切到 view4 让字段**可见** |
| 明确**不做** | 不再包装 `DengluMgr` 的选区列表入口（上一版 bug 根源）。构建脚本有断言锁死：`M.managerServerListByJsonObj =` / `M.managerDefualtServerListByJsonObj =` 一旦出现即 FAIL |

### 构建 / 验证工具

| 文件 | 用途 |
|---|---|
| `tools/build_refactor_3zones.ps1` | 一键构建 + 18 项断言；`-VerifyOnly <apk>` 复检 |
| `tools/verify_3zones_accounts.py` | **离线** 23 项（临时库副本，不碰活库）：迁移、按区过滤、一区一角色、鉴权、handler 级 1110/10101 |
| `tools/verify_3zones_live.py` | **活服** 11 项端到端（真 TCP）：三区隔离、跨区 10102 拒绝、本区通过、密码错误拒绝；自带账号并**自动清理** |

---

## 三、三区与角色：现在的数据流

```
登录页选「唐门一区」
  └─ CS_1110{account, enter_srv_id=1, token=密码}
       ├─ 账号记录/鉴权（accounts：首登绑定、密码校验、last_srv_id、login_count）
       └─ 只回 srv_id=1 的角色          ← 一区一角色，二三区互不可见
  └─ CS_10101 建角 → 落在 h._srv_id（=1110 的 enter_srv_id）
  └─ CS_10102{rid, srv_id} → 角色不属于该区 ⇒ code=0「该角色不在当前区服」（不进场景）
```

* 区服定义在 **`server/config.json` 的 `server_list`**（唐门一区 / 昊天二区 / 史莱克三区，`srv_id` 1/2/3，同 IP 端口）。
* 角色归属区服记在 **`roles.srv_id`**；其余 50+ 张角色数据表都是 **rid 键**，rid 全局唯一 ⇒ 天然按角色隔离。
* 「一区一角色」由 `one_role_per_zone` 控制（默认开；同区再建返回「本区已有角色，请直接进入游戏」）。

---

## 四、账号系统

**服务端（`accounts` 表）**

| 列 | 含义 |
|---|---|
| `uid` / `name` | 账号 id（= CS_1110 的 account）/ 显示名 |
| `pwd_hash` | SHA-256(固定前缀+密码)。密码来源：客户端 `UserPanel` 把密码写进 **CS_1110 的 `token` 字段**（`user_panel.luac`：`info.token = DEF_TOKEN or 密码`） |
| `last_login_ts` / `last_srv_id` / `login_count` | 最近登录时间 / 最近所在区 / 登录次数 |

规则：**老账号（无 pwd_hash）走首登绑定**，不会被锁死；已有密码且不匹配 ⇒ `code=0 +「账号或密码不正确」`（客户端弹提示）；`account_auth=false` 退回"只记录不校验"；账号表出错**不阻断登录**（宁可少记一笔，也不能让人进不去）。

**客户端（本地）**：`dsh_accounts`（`账号\t密码` 逐行，≤12）+ 账号面板。
入口：登录页「切换账号」（原 `restart()`）、「忘记密码」（原渠道 SDK 死键）。
面板：每条一行（`已存密码` 标记）+「删」+「关闭」；点账号行 → 自动填入「用户登录」并切到前台。

**查服务端记录**：`GET http://127.0.0.1:8080/DSH_ADMIN/accounts`

---

## 五、验证结果（本轮实测）

### 5.1 离线 `python tools/verify_3zones_accounts.py` → **PASS（23/23）**
迁移列 + 历史行回填、同账号 1/2 区各建一个角色、同区第二次被拒、三区列表互不可见、角色带真实 `srv_id`、首登绑定、密码错误拒绝、哈希落库（非明文）、`last_srv_id/login_count` 刷新、`account_auth=false` 生效、handler 级 1110/10101。

### 5.2 活服 `python tools/verify_3zones_live.py` → **PASS（11/11）**
```
OK  新账号在 2 区登录成功（code=1）            OK  1 区看不到 2 区的角色（隔离生效）
OK  CS_10101 建角落在 2 区（rid=2003 srv='2'）  OK  3 区看不到 2 区的角色（隔离生效）
OK  同区重复建角被拒（code=0）                 OK  角色条目携带真实 srv_id=2
OK  跨区 CS_10102(rid=2003, srv=1) 被拒（code=0, msg='该角色不在当前区服，请重新选择区服'）
OK  本区 CS_10102(rid=2003, srv=2) 通过（code=1）
OK  密码错误被拒（code=0, msg='账号或密码不正确'）
cleaned test rows: account=zonecheck_… rids=[2003]
```

### 5.3 实机（MuMu / emulator-5554 / 2560×1440）

| 观测 | 结果 | 截图 |
|---|---|---|
| 开机 → 登录页（账号已存则直接进选区页） | ✔ | `shots/_3z_final_login.png` |
| 「用户登录」→ 点「登录」→ **正常进入**选区/进入游戏页 | ✔ 修复前会卡在账号弹窗 | `shots/_3z_after_login_btn.png` |
| 「切换账号」→ **账号管理面板**（账号行 · 删 · **新建账号** · 关闭） | ✔ | `shots/_3z_account_panel.png`、`_3z_panel_new.png` |
| 点账号行 →「用户登录」账号与密码已填 | ✔ | `shots/_3z_filled.png` |
| 点「**新建账号**」→「用户登录」表单**已清空**（账号空、密码显示占位符） | ✔ | `shots/_3z_new_account.png` |
| 输入 `newacct1980` / `123456` → 登录 → 进入游戏 → **建角视图** | ✔ 服务端 `账号新建 uid=newacct1980`、`1110 srv=3 roles=0` | `shots/_3z_enter2.png` |

### 5.4 新建账号后的两处落库（同一轮实测）

```text
# 客户端账号簿（prefs / cc.UserDefault）
dsh_accounts = newacct1980⇥123456
               6742f57GOKVV⇥207820239315

# 服务端账号记录（GET /DSH_ADMIN/accounts）
{"uid":"newacct1980","pwd_set":true,"last_login_ts":1792212114,
 "last_srv_id":"3","login_count":1,"roles":[]}
```

### 5.5 服务端账号记录（节选）
```json
{"uid":"6742f57GOKVV","pwd_set":true,"last_login_ts":1792211134,"last_srv_id":"3","login_count":4,"roles":[]}
{"uid":"TM67Q6K0T6n4","pwd_set":false,"roles":[{"rid":2001,"srv_id":"1","name":"七色小晴天","level":1}]}
```
> 顺带证实了你说的"账号乱"：`6742f57GOKVV`（当前 prefs 里的账号）名下**没有角色**，而 `TM67Q6K0T6n4` 名下有 2001 号角色 —— 都是「一键注册」随机账号造成的，现在面板/接口里一眼能看清。

---

## 六、限制与未做

1. **三区是"逻辑隔离"（同一进程、同一 SQLite 文件、按 `srv_id` 列过滤）**，不是三个库文件/三个进程。理由：rid 全局唯一、角色数据全是 rid 键 ⇒ 行级隔离已等价；物理分库要把 50+ 张表的连接层改成"按区分库"，收益是独立备份/独立服。**真要做**时唯一入口已经留好：`DB_PATH` 改成 `state/roles_srv<N>.db`、`db_conn()` 按连接上下文选库。
2. **密码明文过线**：CS_1110 的 `token` 承载密码（原版就是 token 语义），本机私服可接受；**库里只存 SHA-256**。
3. 账号面板「删」按钮只做了实现与渲染，**未做点击实测**（本轮实测了"打开面板"与"点账号行填入"）。
4. **忘记密码** = 账号管理面板，不提供真正的密码重置。某账号密码真忘了：`/DSH_ADMIN/accounts` 能查到它，重置需改库（或加一个 `/DSH_ADMIN/setpwd`，需要就说）。
5. 老账号首登会**绑定**当次输入的密码 —— 用错密码登录老账号会把它绑错（之后得用这个错密码）。这是"客户端无密码协议"上做鉴权的必然取舍。

---

## 七、复现 / 复检

```powershell
pwsh tools\build_refactor_3zones.ps1                                            # 构建（含 18 项断言）
pwsh tools\build_refactor_3zones.ps1 -VerifyOnly patched\jstm_1411_3zones.apk    # 只复检
python tools\verify_3zones_accounts.py                                          # 离线 23 项
python tools\verify_3zones_live.py                                              # 活服 11 项（自带账号并清理）
pwsh tools\restart_server.ps1                                                    # 重启服务端使迁移/新逻辑生效
```

---

## 八、产物清单

| 文件 | 说明 |
|---|---|
| `patched/jstm_1411_3zones.apk` | ★ 重构包（1.4.11 / v1+v2 签名 / 267.4 MB / SHA-256 `D1F79980…FEEF`） |
| `server/dsh_refactor.lua` | 客户端注入块（本地地址 + NO_PLAY_VIDEO + 账号簿/面板/新建账号） |
| `server/account/service.py` | 账号 + 按区角色 + 鉴权（1110/10101） |
| `server/persistence/db.py`、`server/role/storage.py` | `srv_id` 迁移与读写、`accounts` 规范化 |
| `server/mock_server.py` | 10102/10103 跨区拦截 |
| `tools/verify_3zones_accounts.py`、`tools/verify_3zones_live.py` | 离线 23 项 / 活服 11 项自检 |
| `shots/_3z_after_login_btn.png` | 实机：点「登录」后正常进入选区页 |
| `shots/_3z_account_panel.png`、`shots/_3z_panel_new.png` | 实机：账号面板（含「新建账号」） |
| `shots/_3z_filled.png`、`shots/_3z_new_account.png` | 实机：选老号自动填入 / 新建账号后表单清空 |
| `shots/_3z_enter2.png` | 实机：新账号 `newacct1980` 进入**建角视图** |

---

## 九、追加修复（2026-10-17 晚）：进图后「只有一张模糊地图、没有 UI」

### 9.1 根因链（三层，最后一层才是致命的）

| 层 | 问题 | 后果 |
|---|---|---|
| ① | `SceneModel` 在 `Config` 未加载完时构造 ⇒ `scene_info` 永久 nil | `sceneStart` 里 `self.map_block:get(sceneId)` 那类访问出事 → `createMap()` 不跑（项目早有定案：`report/report_20261001_FIXED_enter_map_and_move.md`） |
| ② | `DailyCtrl.__init` 在 `DailyData`/`RenderMgr` 未就绪时执行 ⇒ `DailyCtrl.data` / `renderMgr` 永久 nil | —（潜伏） |
| ③ | **`DailyCtrl` 的 `SCENE_START` 回调里 `self.data:setTotalHuoli(...)` 抛 `attempt to index a nil value`** | **`sceneStart` 从这一行中断** ⇒ `SceneView` 实例都没建（`sceneView=nil`）⇒ 地图只画出半成品（糊）、**UI 那一层完全没建** |

> 证据（客户端落盘日志 `files/dsh_refactor.log`，修前/修后同一次登录）：
> ```
> [13:26:01] sceneStart ERROR: [string "game/daily/daily_ctrl.luac"]:0: attempt to index a nil value
>              stack: daily_ctrl ← sys/event Fire ← sys/event Fire ← scene_model ← sceneStart
> [13:26:01] sceneView type=nil                    ← 场景视图根本没建
> [13:26:01] runningScene=userdata ... 无 UI 子节点
>
> [13:27:01] scene prepatch fixed: DailyCtrl.data,DailyCtrl.renderMgr | map_block=table map=table scene_info=table
> [13:27:01] SceneView.createMap enter → layoutScene ok → renderScene ok → createMap ok → sceneStart ok
> ```

### 9.2 修法（都在客户端注入块，进图前执行；不改协议）

1. `sceneStart` 之前补齐 `SceneModel.scene_info`（用 `Config.Map[10001]`，客户端自己的真值）；
2. `sceneStart` 之前补齐 `DailyCtrl.data = DailyData.New()`、`DailyCtrl.renderMgr = RenderMgr:getInstance()`；
3. 兜底桩：`GameData / ActivityContants / RoleRpgEvents / SceneEvent` 若缺失则补最小安全桩（`GameData:getRoleVo()` 的返回值在 daily_ctrl 里被丢弃，故空桩不改逻辑）；
4. `sceneStart` 用 `xpcall` 包住并**落盘完整堆栈**（这次就是靠它定位到 daily_ctrl 的）；
5. 服务端配合：`scene_push_when_ready: true` —— 10102 后**不再立刻**推 10200，等客户端发 10300 再推（避免"模块没加载完就建场景"）。

### 9.3 修后实测（同一台 MuMu / 同一账号）

- 画面：地图**清晰**（石板路/花草/亭子），UI 完整：`史莱克城 1845,1875`、福利 / 商城 / 首充 / VIP / 充值、任务 / 队伍、好友 / 世界 / 魂囊 / 更多，角色与 NPC「周漪」同屏；
- 客户端随后正常发出：`10301`（角色信息）×1、`10502`（背包）×12、`10204`（移动）×19、`10922/10924`（活动）、`12403`（任务）、`15801/16500/16903/18900/30715` 等 —— **之前这些一条都没有**；
- `10200` 只推 2 次（不再是重登风暴）；`sceneStart` 无任何 ERROR。
- 截图：`shots/_3z_after_dailyfix.png`。

### 9.4 说明

- 这三处都是**客户端自身的加载时序 bug**（我们只是替它补真值/补构造），与账号、区服、渠道登录无关；
- 同类竞态以后还可能出现在别的子系统：`dsh_refactor.lua` 里的"探针 + 修复"骨架（`patch_scene_fields` / `sceneStart` 包装 / 落盘堆栈）可以直接照搬；
- 日志文件：`/data/data/com.shiyue.dldl.ewan.baidu2/files/dsh_refactor.log`（`adb pull` 可取）。
