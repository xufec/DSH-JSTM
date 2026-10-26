# PHASE 1 — 运行态恢复记录（2026-10-14）

> 只读/取证轮：**未修改 `server/` 下任何代码**（`mock_server.py` 等零改动），只启动进程与采集证据。
> 证据等级：本页全部条目 **VERIFIED**（实机 + mock_server 实际运行观测）或注明例外。

---

## 一、恢复的三段链路（实际执行，可复现）

### 1. MuMu 实例 0

```powershell
& 'D:\MuMuPlayer\nx_main\mumu-cli.exe' control -v 0 launch   # errcode 0
& 'D:\MuMuPlayer\nx_main\mumu-cli.exe' info -v 0
```

实测返回（关键字段）：

```json
{ "index": "0", "name": "MuMu安卓设备", "android_version": "12.0",
  "is_android_started": true, "is_process_started": true,
  "player_state": "start_finished", "launch_err_code": 0,
  "vt_enabled": true, "hyperv_enabled": true, "adb_port": 16384, "pid": 15236 }
```

### 2. adb

```powershell
adb connect 127.0.0.1:16384      # 首次 "offline"，android_started 后转为 device
adb devices                      # 127.0.0.1:16384  device
```

> 坑：`mumu-cli control launch` 返回 0 只代表**启动流程结束**，此刻 adb 可能仍是 `offline`。
> 必须轮询 `adb devices` 直到出现 `device`（本次第 1 次轮询即转正）。

### 3. mock_server

```powershell
$env:Path = "D:\Python;D:\Python\Scripts;D:\ADB\platform-tools;$env:Path"  # 让脚本里的 python = 3.12.3
pwsh -NoProfile -File tools\restart_server.ps1
```

输出（截取）：`WMI 已创建进程 PID 25784` → `已启动 PID 44008，监听 8080,9000` →
冒烟 `HTTP /notice.json -> 200` + `TCP 1199 -> 回包 cmd=1199 payload_len=6`。

**注意**：`restart_server.ps1` 用的是裸 `python`，本机 PATH 里它解析到 **Anaconda 3.9.7**；
本项目其余脚本（`RUN_TESTS.ps1` 等）用 **`D:\Python\python.exe` 3.12.3**。
（本次把 `D:\Python` 前置到 PATH 以保持与测试链一致。）

---

## 二、/status 基线

```json
{"ok": true, "rid": 1001, "role": {"level": 70, "career": 1, "scene_id": 10001,
 "x": 110, "y": 43, "gold": 1800140, "coin": 9904629, "exp": 13339, "diamond": 0},
 "assets": {"gold": 1800140, "coin": 9904629, "coupon": 99999999, "hero_exp": 3200,
            "rune_chip": 41000}}
```

与文档基线（`lv70 / gold 1799840 / coin 9904599 / scene 10001`）对照：**等级/场景一致，
货币有小幅正向漂移**（gold +300、coin +30），是上次会话正常游玩留下的差分，不影响基线判据。
→ 建议把基线文档改为「lv70 + scene 10001」为硬判据，货币为「≥ 文档值」软判据。

---

## 三、客户端身份（关闭 PHASE 0 审计缺口 #3）

| 探测 | 实测 |
|---|---|
| 已装包 | `com.shiyue.dldl.ewan` = 1.3.0（code 25）/ `.qihoo` = 1.4.9（code 44）/ **`.baidu2` = 1.4.11（code 46）** |
| 1.4.11 安装路径 | `/data/app/~~F6NViiZdS4nFzwfCrW-22w==/com.shiyue.dldl.ewan.baidu2-.../base.apk` |
| base.apk 大小 | **280,472,477 B** = 与本地 `patched/jstm_1411_fakelogin_aligned.apk` **逐字节同长** ⇒ 装的是**补丁包**（原版为 280,804,346 B）|
| 启动 Activity | `com.shiyue.dldl.ewan.baidu2/org.cocos2dx.lua.AppActivity` |

> **缺口 #3 结论**：`PHASE0_AUDIT.md` §0.1「1.4.11 尚未装入模拟器」**已过期**；
> 实机为「**1.4.11 补丁包已安装并正在运行**」。以本节为准。

---

## 四、实机联调实证（客户端确实连上 mock_server）

会话帧统计（`server/logs/tcp.log` 本轮会话，结构化产物见同目录
`phase1_session_frames.json` / `.md`）：

| 指标 | 值 |
|---|---|
| CS 帧 / 唯一命令 | **138 / 72** |
| SC 帧 / 唯一命令 | **122 / 73** |
| CS 有 SC 应答 | **69 个** |
| CS 无 SC 应答 | **3 个**：`10001`(CSFirstPack，设计上 CS-only)、`10300`、`10999`(CS-only 上报型) |
| 服务端主动推、无对应 CS | **4 个**：`10200` `10201` `10305` `12400`（场景/角色/技能推送/任务列表）|

开场序列（实机原始）：`1199 → 10001 → 1110 → 10103(选角重登) → 10300/10301/10302/10303 → 15203 → 12403 …`

即：**登录 → 选角 → 进场景(10200) → 属性/技能推送 → 任务列表** 全链路在线，与 HANDOFF 记载一致。

新观测到的命令：**`10341`**（打开背包/属性面板时客户端发出，
CS body(17)=`00 01 00 00 03 e9 00 01 31 00 00 00 64 67 00 00 17` → SC 16 B）。
字段语义未解（body 内含 `03 e9`=1001 与 `64`=100）。

---

## 五、本轮流转的坑（写下来别再踩）

| 坑 | 说明 |
|---|---|
| `locate_in_image` 工具在本环境报 `loadImage is not defined` | 无法用它定位 UI 元素；退回「截图 + 视觉描述 + 服务端日志验证」三角法 |
| 视觉模型报的坐标**不可信**（±100–200 px） | 本次按视觉坐标点的「更多」(2480,1310) 与「魂骨/时装/称号」tab(2120,6xx–7xx) **全部未命中**（无新 CS、无 UI 变化）|
| 判定「点击是否生效」的唯一硬证据 | **`tcp.log` 是否出现新 CS 帧**（不是截图变化、不是视觉描述）|

---

## 六、清理与还原（保持运行态）

- 运行态**保持**：MuMu 实例 0 + adb + mock_server(PID 44008) 均在运行，供后续取证直接使用。
- 未做任何 `am force-stop` / 卸载 / 重装；未修改 APK；未改服务端代码。
- 证据截图：`analysis/runtime_evidence/shots/phase1_*.png`
