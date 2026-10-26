# 1.4.9 进入场景流程（enter scene flow）

> APK：`anzbao/jstm.apk`（**1.4.9** / `com.shiyue.dldl.ewan.qihoo`）
> 依据：客户端字节码反汇编 + 实机抓包 + 探针客观读数。**凡未实测的都标注出来。**

---

## 一、进场景的完整命令序列（实测）

```
① 10001 CSFirstPack                 key = "game_client"
② 1110  CSAccountLogin              10 项 key/val（account/timestamp/enter_srv_id/…）
   ← SCAccountLogin_1110            code 必须 == TRUE(1)，否则弹空白框
③ 10103 CSRoleReLogin               rid, srv_id          ← 角色重连（近路，跳过选角）
   ← SCRoleReLogin_10103            code, msg, timestamp, world_lev
④ 10200 (服务端主动推)               code, msg, bid, line_id, x, y, dir
⑤ 10201 CSMapGird  ←→ SCMapGird     roles/npcs/mons/elems
⑥ 10300 CSRoleInit（空）             客户端说"我初始化完了"
⑦ 10301 CS_10301  ←→ SC_10301       角色基础信息（40+ 字段）
⑧ 10502 背包 / 10921 10922 10923 10924 10932 活动 /
   10800 11300 11301 11600 13200 13300 13771 15501 15700 15801
   16500 16605 16706 17200 18803 18900 19400 19406 …
```

**关键点**：`10200` + `10201` 是进场景的开关。
`10200` 的中文名是「**通知**角色进入场景」——服务端主动推；
`10201` 两边都会走（客户端 `scene_controller.request10201` 会主动请求，服务端进场景时也推一次）。

---

## 二、进场景的客观判据

| 判据 | 进场景前 | 进场景后 |
|---|---|---|
| `SceneModel:getInstance():getScene()` | `nil` | **table** |
| `RoleCtrl:getInstance():getSelfRoleVo()` | `nil` | **table** |
| 截图唯一色数 | 439（加载画面） | **44,328**（渲染场景） |
| 客户端命令深度 | 停在 10502/10922 | 出现 `10300 11300 13300 18803 19400 19406` |

实测进图耗时：**5–15 秒**（tick 285 ≈ 14s / tick 1440–1455）。

---

## 三、最小数据集合（进场景到底需要什么）

**必须**：

| 数据 | 由谁提供 | 说明 |
|---|---|---|
| 服务器条目（ip/port/srv_id/srv_name） | HTTP `/gateway/mobile/json` → `data.server_list` | 缺了连服务器选择都没有 |
| 帐号登录成功（`code == TRUE(1)`） | `SCAccountLogin_1110` | **必须是 1**，否则走 else 分支弹空白框 |
| 角色存在（`roles` 至少 1 条，含 rid/srv_id/name/lev/sex/career/is_online） | `SCAccountLogin_1110.roles` | |
| 角色登录成功 | `SCRoleReLogin_10103` / `SCRoleLogin_10102`（`code=0`） | |
| **进场景通知** | `SCRoleEnter_10200`（`code,msg,bid,line_id,x,y,dir`） | 服务端主动推 |
| **场景角色表** | `SCMapGird_10201.roles` 里**包含自己** | 缺了自己，地图里没有可渲染单位 |
| 角色基础信息 | `SC_10301`（最小结构亦可） | |

**可以暂时为空**（实测不影响进图）：`10201` 的 `npcs/mons/elems` 三张表；
以及 14 个子系统的"空但合法"应答。

**注意**：`SCMapGird_10201.roles` 的每个元素含
`buff_bids / misc_uint8 / misc_uint16 / misc_uint32 / misc_str / animate_res`
六个 `D|Dsc*|` 动态子表，`protocol/fields.json` **未解出它们的字段**。
当前按"计数前缀 + 0 项"编码，客户端**未报错**，但不能断言正确。

---

## 四、踩过的坑（都记下来，避免重犯）

| # | 现象 | 真正原因 | 修法 |
|---|---|---|---|
| 1 | 点进入游戏弹**空白框** | ①`1110.code=0` 而 `TRUE==1`，走 else → `message('')`；②对 `15801` 回了**布局猜错**的包 → `beast_ctrl` 的 `message(resp.msg)` 拿到 nil | ①`code→1`；②**不再应答 15801** |
| 2 | 1110 应答"被丢弃" | 发得太早（~9s），`denglu_ctrl.registerProtocals` 还没注册 handler | 推迟到模块加载完成后（~40s）再发 |
| 3 | 探针钩子全部失效 | 驱动第 3 帧就装钩子，那时 `DengluCtrl/CommonAlert/message` 还不存在 | 改成**重试式安装** |
| 4 | 每轮表现不一致 | ①探针被重复安装 4~5 份；②`net_manager` 只在 `restartNetManager` 里创建 | ①加安装守卫；②安装器/驱动分离，先建 net_manager 再建 tick |
| 5 | 客户端每 0.2s 重下配置 729 次 | `file_update proto#9` 的 `if URL_PATH then return end` 短路点从未命中（下发的脚本没生效） | 把地址全局**提前写进 `config.luac`**，强制短路 |

---

## 五、稳定性实测

见 `tests/1.4.9_regression.md`：**连续 5 次进图 5/5 成功**，
闪退 0、Lua 错误 0。4/5 次出现一次 TCP 连接关闭，客户端重连后仍成功进图
（**断线原因尚未定位**，不猜）。
