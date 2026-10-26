# Lua 注入通道：能力已验证 + 联调兼容性问题（本轮）+ 运行态已恢复

> 本轮走 B（项目自带 Lua 注入）拿到了**真实客户端数据**；但发现**注入会破坏联调启动流程**。
> 已**重装原 fakelogin APK 并删除热补丁**，运行态恢复可用（实测 CS 恢复、基线不变）。

---

## 一、✅ 通道能力已验证（探针 v1–v6 全程工作）

注入后可用三个通道，**实测均通**：

| 通道 | 说明 |
|---|---|
| `print` 镜像 | 注入块把 `print` 接到上报（`tag=print`），logcat 与 PC 双份 |
| 自建 XHR 上报 | 探针自己发 `GET /DSH_REPORT?tag=…&v=…`（≤170B）→ 落在 PC 的 `server/logs/http.log` |
| **`dsh_patch.lua` 热补丁** | 读 `/data/user/0/com.shiyue.dldl.ewan.baidu2/files/dsh_patch.lua` 并执行 ⇒ **改探针只需 push + 重启，不用重打包** |

**节拍**：`cc.Director:getInstance():getScheduler():scheduleScriptFunc(fn, 0.5, false)` **实测会触发**
（`p2.sched fired_1/fired_10/fired_200`）——推翻旧文档"加载期调度器不触发"的结论。

### 1.1 从客户端 Lua VM 直接读到的结构（CONFIRMED）

| 项 | 结果 |
|---|---|
| `Config` 子表 | 十七个核心表 + 大量 `config_*` 表；**没有 `SkillXiulian`** |
| **修炼表真名** | **`Config.SkillXiulianLev`**：8 个条目，键 = 修炼 id `10801/10201/10401/10601/10101/10501/10301/10701`；每 id 下按**等级** 25 级；样本 `lv12={1=60,2=70}`、`lv14={1=70,2=80}`、`lv2={1=1,2=1}` |
| `Config.Huoli[id]` | `{total_huoli:tbl, huoli:tbl, ord, id, max_num=5, limit_lev=25, name}` |
| `Config.RiChang` | 43 条；`HuoliClearVal2` / `HuoliMaxVal2`(200 项=640) 均在 |
| `package.loaded` | **171 项，几乎全是 `config/protocal/cmd_resolve_*:boolean` + `util/*`**；业务模块（`game/login/*` 等）**不在**标准 require 缓存（自研加载器）|
| `_G` 里的 `Dsc*/SC*/CS*` | 都是**协议类表**，不是面板数据 |
| **缺键监听（v5）** | 给 `SkillXiulianLev/Huoli/RiChang/HCV2/HMV2` 挂 `__index` 后**没有任何缺键读取** ⇒ 面板打开时**不查"缺失 id"** |

> 顺带纠正：我上几轮用 frida 内存扫描命中的 `SkillXiulian` 其实是 **`SkillXiulianLev` 的子串**（教训：内存扫描要做边界校验）。

---

## 二、⚠ 联调兼容性问题（**注入会破坏启动流程**）

三个变体实测：

| 变体 | 结果 |
|---|---|
| **完整注入块 + `-NoEmbedded`**（GamePort 默认 19000）| 登录页 `error网络异常`；**一条业务 HTTP 都不发**；不连 9000 |
| **obs-only**（只 observer + 热补丁加载器）| 业务 HTTP 恢复（`GET /update/config/url_config_ewan.lua` 成功），但**卡在下载重试循环**（`n_323/n_324` 反复拉同一文件），未进入登录 |
| **原 fakelogin APK（`-NoInject`）** | **完全正常**：登录 → 连 9000 → 心跳/移动/背包同步 |

**结论**：原 fakelogin APK **连注入块都没有**；它能登录靠的是
① DEX 跳过死 SDK ② `IS_PLATFORM_LOGIN=false` ⇒ `main()` 自己走正常启动
③ **本地账号流程**（本地存档里已有 `last_login_account=dsh_local` / `password` / `srv_id=1`，
   即更早阶段用 `cc.UserDefault` 预写的那份）。

而 observer 会**包装 `cc.XMLHttpRequest` 的 `new` 与实例方法**（`open/send/registerScriptHandler`）
并挂网关合成器 —— 正落在启动热路径上，与本项目旧文档第 8 节坑位 6 的结论一致：
> 「不要在热路径挂探针……挂了驱动探测+kick+网络探针+心跳，直接把加载卡死」

---

## 三、运行态已恢复（本轮收尾动作）

```
adb shell su 0 rm -f /data/user/0/com.shiyue.dldl.ewan.baidu2/files/dsh_patch.lua
adb install -r patched/jstm_1411_fakelogin_aligned.apk
am force-stop/start …
```

实测恢复：`10502`（背包同步）→ `10204`（移动）→ `1199`（心跳）→ `20809` 全部回来；
`/status` 基线 `lv=70 / scene=10001` 不变。

---

## 四、回归（按用户要求每步实跑）

| 项 | 结果 |
|---|---|
| `patch_apk.py` / `verify_injected_lua.py` 语法 | OK |
| `server/observer.lua` Lua 闸门 | OK（18187 B）|
| 分发遮蔽 | 干净（专用 1430 / 遮蔽 0）|
| **miniloop ×3** | **145/145、145/145、145/145**（本轮三连全绿，`10505` 偶发未出现）|
| `mock_server.py` | **未改动**（与上轮备份 diff = 9 行 = 上轮 monster 改动）|
| 基线 | `rid=1001 lv=70 scene=10001 power=724112` |

---

## 五、本轮留下的工具（都可参数控制，默认不影响原流程）

| 文件 | 改动 |
|---|---|
| `tools/patch_apk.py` | observer 与 embedded **解耦**（联调也注入）；新增 `--obs-only` |
| `tools/build_apk.ps1` | 新增 `-ObsOnly` 开关 |
| `tools/verify_injected_lua.py` | 支持 **no-embedded / obs-only 布局**（仍做语法闸门）|
| `server/observer.lua` | 新增表探针段 + **重入保护**（未注入时不生效）|
| `tools/dsh_patch_probe.lua` | 热补丁探针（v1–v6，迭代用）|
| `tools/frida_probe_modules.py` / `frida_mem_scan.py` | frida 探针（上轮）|

---

## 六、下一步（把"通道"做成**不干扰启动**的形态）

| # | 方案 | 说明 |
|---|---|---|
| **A** | observer **默认不包装 XHR**：去掉网关合成器与 `open/send/registerScriptHandler` 包装，只保留 `print` 镜像 + `dsh_patch` 加载器 | 直接消除热路径干扰；代价是失去"网关合成"（联调不需要它）|
| **B** | 探针**延迟启动**：observer 只做最小登记，真正注册调度器放在 `print` 首次出现 `beginGame`/登录模块加载之后 | 避开逐帧加载期 |
| **C** | 用**纯热补丁**路线：既然 `dsh_patch.lua` 由注入块加载，而注入块又干扰启动 ⇒ 改为**只改 DEX/config 的 APK（即原 fakelogin）+ 另找时机注入**（例如用 frida 在启动后 `Memory` 写 Lua 串？不现实）| — |

> A + B 组合最可能让"联调 + 探针"共存；届时可继续把「修炼 35/50 与消耗/拥有」
> 用 v5 的**代理监看**（替换 `SkillXiulianLev` 为 `__index` 转发代理，记录**所有**键读取）一次定位。
