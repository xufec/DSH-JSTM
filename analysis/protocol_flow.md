# 协议流程分析（protocol flow）

> 全部结论来自 LuaJIT 反汇编 + 实机抓包双向印证。
> 抓包只针对**我自己控制的**本地服务器 `10.0.2.2:8080`（HTTP）与 `10.0.2.2:9000`（TCP）。

---

## 一、传输层

### 1.1 配置/网关：HTTP

| 用途 | 请求 |
|---|---|
| 启动配置 | `GET /update/config/url_config_ewan.lua?<os.time()>`（原生下载器 FmodexManager） |
| 服务器列表 | `POST /gateway/mobile/json`（游戏自带 XMLHttpRequest，body 为空） |
| 公告 | `GET /notice.json` |

### 1.2 游戏服：TCP（帧格式已用解码器验证）

```
[u32 大端 payload_len][u16 大端 cmd][body ...]
payload_len = 2 + len(body)
字符串 = [u16 大端 长度][字节]
key/val 形表 = [u16 项数] + 每项 [str key][str val]
整数一律大端
```

实测一份 99 字节抓包正好切成 `23+10+23+23+10+10`，**边界 100% 对齐**。
解码器：`tools/decode_frames.py`。

### ⚠ 短消息尾部有"脏数据"

客户端把定长发送缓冲**整段发出**，短消息尾部残留上一次写入：

| 观测 | 证据 |
|---|---|
| 10001 body 声明 17 字节，只有前 13 是 `key="game_client"` | 尾部两次分别是 `2c 22 76 63` 与 `00 00 00 00` |
| 1199（空消息）却带 4 字节 | 发 1110 前是 `00 0b 67 61`；发 1110 后变成 `00 0a 00 07`（=1110 body 前 4 字节） |
| CS_10301 本应空，却带 4 字节 | `01 00 03 e9`（=上一包 rid 1001） |

⇒ **服务端必须按消息定义读字段、忽略尾部多余字节。**

---

## 二、"进入游戏"之后的协议时序（实测均为客户端自发）

| # | 协议 | CMD | 方向 | 请求字段 | 返回字段 | 成功条件 | 失败条件 |
|---|---|---|---|---|---|---|---|
| 1 | `CSFirstPack_10001` | 10001 | C→S | `key:string`（实测 `"game_client"`） | 手册无对应 SC | — | — |
| 2 | `CSheartbeast_1199` | 1199 | C→S | 空 | `SCheartbeast_1199{time:uint32}` | — | 不回包客户端判定掉线 |
| 3 | `CSAccountLogin_1110` | 1110 | C→S | `args:table(key:string,val:string)`，实测 10 项 | `SCAccountLogin_1110{code:uint8,msg:string,roles:table(rid,srv_id,name,lev,sex,career,is_online),least_career:uint8}` | **`code == TRUE`，而 `TRUE==1`**（见下） | `code != 1` → `setCanLoginOpenGame(false)` + `message(msg)` |
| 4 | `CSRoleLogin_10102` | 10102 | C→S | `rid:uint32, srv_id:string` | `SCRoleLogin_10102{code,msg,timestamp:uint32,world_lev:uint16}` | `code == 0` | 非 0 → 弹 `msg` |
| 5 | `CSRoleReLogin_10103` | 10103 | C→S | 同上 | 同 10102 结构 | 同 | 同 |
| 6 | `CSRoleCreate_10101` | 10101 | C→S | `sex,name,career,playform` | `SCRoleCreate_10101{code,msg,rid,srv_id}` | — | — |
| 7 | `CSRoleInit_10300` | 10300 | C→S | 空 | — | — | — |
| 8 | `CS_10301` | 10301 | C→S | 空 | `SC_10301{...40+ 字段}` | — | — |
| 9 | `SCRoleEnter_10200` | 10200 | **S→C（服务端主动）** | — | `code,msg,bid,line_id,x,y,dir` | — | — |
| 10 | `SCMapGird_10201` | 10201 | **S→C（服务端主动）** | — | `roles,npcs,mons,elems` 四张表 | — | — |

### 关键点 1：`code` 的"真值"不是 1 或 0 的字面直觉

`assets/src/common/common_define.luac proto[7]`：

```
@0: KSHORT 1 ; @1: GSET TRUE      →  TRUE  = 1
@2: KSHORT 0 ; @3: GSET FALSE     →  FALSE = 0
```

`on1110Rolelist` 写的是 `if resp.code == TRUE`，**所以 1110 的成功码必须是 1**。
（`10102`/`10103` 用的却是 `code ~= 0` 风格；两者语义不同，不能混。）

> ⚠ **2026-10-01 更正（保留原文，按本项目纪律不删旧结论）**：上面括号里那句**是错的**。
> 实测与反汇编两侧都指向 **`10102`/`10103` 的成功码同样是 `1`（TRUE）**，不是"`code ~= 0` 风格"：
> 1. **反汇编依据**（参考服 `server/mock_server.py:13979-13993` 的实机注释）：
>    `denglu_ctrl.luac proto[30] on10102Login` 的分支是
>    `if resp.code == TRUE then … SendProtocal(10300); LoginSucceedSendProtocal(); DengluEvent:Fire(LOGIN_SUCCESS)`
>    `else CommonAlert:show(resp.msg, …)`（**弹框且不再往下走**）；
>    而"`0` 才是成功"的那条是 **`10200`**（`scene_controller.luac proto[16]`：`if resp.code ~= 0 then message2(resp.msg) end`）。
> 2. **真机实测依据**（本会话 goal round 7 前后）：把 `10200` 的 `code` 改为 **0** 之后，
>    客户端探针出现 `hit_on10102Login code_1_type_table`，并接着发出 `10300`、触发 `LOGIN_SUCCESS`、
>    **`scene` 由 nil 变为 table**（`isLoadState_true`）—— 若 `10102` 真按"`code ~= 0`"判成功，
>    这里就应当也接受 `0`，但实测**必须发 1 才走成功分支**。
> ⇒ **正确口径**：`1110` / `10102` / `10103` = **`code == 1` 才算成功**；**`10200` = `code == 0` 才算成功**（唯一例外）。
> 证据路径：`server/minloop/min_loop_server.py::push_10200`（含出处注释）、
> `server/minloop/selftest.py`（"10200 的 code 必须是 0"断言）、
> `report/report_20261001_minloop_round13_goal7_BREAKTHROUGH.md`、`logs/minloop/live9_stdout.log`。

### 关键点 2：10200 / 10201 是服务端主动下发

- `10200` 中文名是「**通知**角色进入场景」；
- `10201` 名字带括号「场景图块信息()」，无 CS 请求字段。

实测：客户端**从不主动请求**这两条，必须由服务端推。
推了之后客户端确实收到（`OnNetRecv` 计数 `a1=10200` / `a1=10201`）。

---

## 三、当前本地服务器的实现进度（对应第十四节的判断表）

| 阶段 | 状态 |
|---|---|
| 服务器列表接口 | ✅ **成功**（`data.server_list` 结构正确，客户端解析入库 `#server_list=1`） |
| 帐号登录 1110 | ✅ 已实现并**被客户端接收**（`OnNetRecv a1=1110`） |
| 登录指定角色 10102 | ✅ 已实现并接收（`a1=10102`） |
| 角色重连 10103 | ✅ 已实现并接收（`a1=10103`） |
| 客户端初始化 10300 | ✅ 收到（仅记录） |
| 角色基础信息 10301 | ⚠ 已回最小结构（`skill_list/buffs/animate_res/misc_*` 给空表） |
| 背包 10502 / 活动 10922 / 其余 15 个子系统 | ⚠ 已回"空但合法"的包 |
| 进入场景 10200 / 场景图块 10201 | ⚠ 已实现并主动推送（10201 已带上"自己"这个角色） |
| **客户端是否真的建立场景** | ❌ 客观判据 `SceneModel:getInstance():getScene()` **仍为 nil** |
| 自身角色 | ✅ `RoleCtrl:getInstance():getSelfRoleVo()` **已是非 nil 的 table** |

⇒ **本地服务器目前实现到"角色登录 + 开局子系统数据 + 主动推送进场景"，
但客户端尚未真正建立场景对象。**

---

## 四、待解协议缺口（会影响后续）

`roles` / `items` 里的若干字段是 `D|Dsc*|` **动态表**，`protocol/fields.json`
对其中一部分**没有解出字段**（例如 `Dsc10201misc` 标注为"无字段"、
`Dsc10502attrs_ext` 等）。这部分编码目前是**按"计数前缀 + 0 项"猜的**——
客户端未报错，但不能据此认为完全正确。若后续需要非空内容，
必须回到 `assets/src/config/protocal/cmd_resolve_<id>.luac` 从格式表里还原。
