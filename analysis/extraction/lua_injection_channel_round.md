# 走 B 路线首战：Lua 注入通道打通 + 客户端表结构首批 dump

> 用户授权走 B（项目自带 Lua 注入通道）。本轮**重建了 APK 并装上**，
> 拿到了**在游戏 Lua VM 里执行探针 + 把结果回传 PC**的能力，并 dump 出关键表结构。
> 结论：**通道完全可用；「35/50」的具体来源尚未锁定**（下一步已明确）。

---

## 一、通道打通（可复用的能力，本轮最大收获）

### 1.1 重建 APK（联调版 + 注入）

关键发现与修复：

| 问题 | 情况 | 处置 |
|---|---|---|
| 联调版（`--no-embedded`）**不注入 observer** | `patch_apk.py` 把 observer 放在 `if embedded:` 里 ⇒ 没有诊断通道 | 改 `patch_apk.py`：**observer 与 embedded 解耦**，联调版也注入 |
| 验证器误报 | `verify_injected_lua.py` 只认内置服务端的锚点（`__dsh_srv_src`/`DSH_FALLBACK_BEGIN`）| 加"**no-embedded 布局**"分支：仍做语法闸门（inject head + observer），不要求服务端段 |
| 探针重入 | `rep()` 发 XHR → observer 的 `new_xhr` → `pump` → 又回到 try ⇒ 无限递归 | 探针加 `in_try` 重入保护 |

构建命令（网关仍指向 PC，不破坏既有闭环）：

```powershell
pwsh tools\build_apk.ps1 -Src anzbao\jstm_142165.apk -Out patched\jstm_1411_probe.apk `
     -NoEmbedded -SkipSdkInit -Host 10.0.2.2 -Port 8080
# RESULT: PASS（inject head 11018B / url observer 17907B 语法闸门 OK），已签名
# 产物 272,722,763 B；安装：adb install -r（原 fakelogin APK 仍在盘上可回滚）
```

### 1.2 ★ 免重打包的迭代通道：`dsh_patch.lua`

注入块里有现成的热补丁机制（旧代码已写，本轮才用上）：

```
读 /data/user/0/com.shiyue.dldl.ewan.baidu2/files/dsh_patch.lua → loadstring → 执行
```

⇒ **迭代探针只要 push 一个 Lua 文件 + 重启游戏**（无需重新打包/签名/安装）。
实测：`[DSH_PATCH2] loaded` / `[DSH_PATCH] ran ok=true nil`。

**回传通道**：注入块自带 `print` 镜像 + `__dsh_rep`，上报落在 **PC 的 `server/logs/http.log`**
（`GET /DSH_REPORT?tag=…&v=…`，每条 ≤170 字符）。探针自建 XHR（基址从全局 `URL_PATH.update` 推导，
与 `--host/--port` 无关）。

### 1.3 节拍点：**调度器真的会响**（推翻旧结论）

旧文档说"加载期调度器不触发"。本轮实测（`p2.sched`）：

```
fired_1 / fired_10 / fired_200 …   ← 0.5s 周期回调稳定触发
```
⇒ 直接用 `cc.Director:getInstance():getScheduler():scheduleScriptFunc(fn, 0.5, false)` 做探针节拍即可。

---

## 二、客户端表结构首批 dump（CONFIRMED，直接从 Lua VM 读出）

| 表 | 实测结构 |
|---|---|
| `Config.SkillXiulian` | **不存在**（旧文档/我的 frida 内存扫描都被子串骗了）|
| **`Config.SkillXiulianLev`** | **8 个条目**，键 = 修炼 id：`10801 / 10201 / 10401 / 10601 / 10101 / 10501 / 10301 / 10701`；每个 id 再按**等级**分（`[10801]` 有 **25 级**）|
| `SkillXiulianLev[10801][lv]` 样本 | `lv12={1=60,2=70}`、`lv14={1=70,2=80}`、`lv2={1=1,2=1}` ⇒ **每级一条 {经验阈值/区间} 记录** |
| `Config.Skill` | `{ data=<table>, function=<function> }` |
| `Config.Huoli[id]` | `{ total_huoli=<table>, ord, id, huoli=<table>, max_num=5, name="…", limit_lev=25 }` |
| `Config.RiChang` | **43** 条（面板 id 203/213/215/108/209/208…，与 mock_server 下发一致）|
| `Config.HuoliClearVal2` / `HuoliMaxVal2` | 均在（`HuoliMaxVal2` = 200 项，值 640）|
| 全局单例 | `GameData` / `RoleVo` / `DailyCtrl` / `GameNet` / `ProtocalRulesMgr` **都是 table**（`RoleVo`/`DailyCtrl` 上只有方法，数据不在其上）|

### 2.1 一个重要发现：**id 空间对不上**

我们的 `SC_10621.skill_list` 发的是 **10000 / 10001 / 10002 / 10822**，
而客户端的修炼表键是 **10801 / 10201 / 10401 / 10601 / 10101 / 10501 / 10301 / 10701**。

⇒ 客户端拿我们发的 id 去查修炼表**查不到**；这很可能就是「修炼进度 35/50 不跟随服务端字段」
（第 6/7 轮两条控制实验）的原因之一。

---

## 三、尚未锁定：「35/50」到底从哪来

本轮已排除/确认：

| 检查 | 结果 |
|---|---|
| 深度 ≤3 搜裸值 `35`/`50`（`GameData`/`RoleVo`/`DailyCtrl`）| **0 命中** ⇒ 不是直接存的字段 |
| 字符串 `"35"`/`"50"` 同深度搜索 | 0 命中 |
| `RoleVo` / `DailyCtrl` 实例的标量字段 | 只有 `_delete`/`_init`，**无业务数据** |
| 服务端侧（前几轮）| `10621` skill exp、`practice_exp`、本地存档、三包规格 —— 全部证伪 |

⇒ 最可能：**渲染时用某处"当前修炼经验" + `SkillXiulianLev[id][lv]` 的阈值算出来的**。

---

## 四、下一步（通道已就绪，1~2 次热补丁即可）

| # | 手段 | 说明 |
|---|---|---|
| **A** | **代理监看**（首选）：把 `Config.SkillXiulianLev` / `Config.Huoli` / `Config.RiChang` 换成 `setmetatable({}, {__index=function(_,k) 记录 k; return orig[k] end})`，然后**打开面板** ⇒ 直接打印客户端**读了哪些键** | 纯 Lua，无需 frida/重打包 |
| **B** | **改我们下发的 id**：把 `10621.skill_list` 的 bid 改成客户端真实修炼 id（如 `10801`）并给一个**可辨识的 exp（如 41）**，看面板是否跟随 | 一次即可定论"是否漏发 id" |
| **C** | 找面板控制器：扫 `_G` + `package.loaded` 里含 `skill`/`xiulian` 的模块与其实例，dump 其字段 | 定位渲染入口 |

> 三者都可以走 §1.2 的热补丁通道，**不再需要重新打包**。

---

## 五、本轮交付与状态

| 项 | 状态 |
|---|---|
| 新增/改动 | `server/observer.lua`（+表探针、+重入保护）、`tools/patch_apk.py`（observer 与 embedded 解耦）、`tools/verify_injected_lua.py`（支持联调布局）、`tools/dsh_patch_probe.lua`（热补丁探针 v4）、`tools/frida_probe_modules.py`、`tools/frida_mem_scan.py` |
| APK | `patched/jstm_1411_probe.apk` 已安装（**回滚**：`adb install -r patched/jstm_1411_fakelogin_aligned.apk`）|
| 热补丁 | 已推送在 `/data/user/0/com.shiyue.dldl.ewan.baidu2/files/dsh_patch.lua`（**停用**：`su 0 rm` 该文件）|
| mock_server | 未改动，PID 28336 正常；客户端仍连 PC（上报落在 `server/logs/http.log`）|
| 基线 | `lv=70 / scene=10001` 不变 |
