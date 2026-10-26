# frida 通道可行性报告 + 内存取证首战（本轮）

> 用户授权：调用项目内 frida 工具链，hook 面板取数函数 / `Config.SkillXiulian` 的读取。
> 本轮结论：**frida 已在本机与 MuMu 上跑通**，但**挂不了游戏自身的 ARM 库**（houdini 所致）；
> 不过**内存读写通道可用**，已用它证实「修炼配置确实在客户端内存里」。**无代码改动。**

---

## 一、frida 环境（已跑通，命令可复现）

| 项 | 结论 |
|---|---|
| host | `D:\Anaconda3\Scripts\frida.exe`，frida-python **17.18.0**（Anaconda）|
| 设备端二进制 | `/data/local/tmp/frida-server`（ELF **64 位 x86-64**，116 MB，项目自带）<br>`/data/local/tmp/fs-x86`（ELF **32 位 x86**，58 MB）|
| **正确选择** | 游戏是 **32 位进程**（`/proc/<pid>/exe -> /system/bin/app_process32`）⇒ 必须用 **32 位**的 `fs-x86` |
| 启动命令 | `adb shell su 0 sh -c 'nohup /data/local/tmp/fs-x86 -D >/data/local/tmp/fsx86.log 2>&1 &'` |
| 连通性 | `frida-ps -U` 列出 82 个进程 ✅ |
| attach | ✅ 成功（`device: Device(id='127.0.0.1:16384', name='22041211A')`）|

### 1.1 两个坑（写下来，下次省时间）

1. **进程名是乱码**：`enumerate_processes()` 里游戏主进程的名字被解析成 `��������`
   ⇒ **按名字 `get_process('com.shiyue.dldl.ewan.baidu2')` 必然失败**，必须**按 PID attach**
   （本次 PID **19238**，`pidof com.shiyue.dldl.ewan.baidu2` 可取）。
2. **64 位 server 看不到 32 位游戏的模块**：换 32 位 `fs-x86` 后才能正常 attach。

---

## 二、★ 技术墙：**ARM 库在 houdini 下对 frida 不可见**

attach 后在进程内枚举模块，得 **294 个模块**，其中：

- ✅ 有 `libhoudini.so`（10.5 MB，ARM 翻译层）、`libnativebridge_lazy.so`
- ❌ **没有** `libcocos2dlua.so` / `libentryexstd.so` / `libsupersdkjni.so` 等**游戏自身的 ARM 库**

⇒ MuMu 通过 houdini 翻译执行 ARM 代码，这些库**不在 frida 的模块表里**，
因此 **`lua_getfield` / `luaL_loadbuffer` 之类的原生符号钩子在该模拟器上不可用**，
`Module.enumerateExports` 也拿不到任何 lua_* 符号（探针实测：匹配模块 0、关键导出 0）。

> 这是**环境限制**，不是 frida 版本问题：项目自留的 frida 笔记来自**另一台 AVD（emulator-5554）**，
> 那台能 spawn 并 hook Java 类；本机 MuMu 的 houdini 路径不同。

---

## 三、★ 但内存通道可用：已证实「修炼配置在客户端内存里」

`Process.enumerateRanges('r--')` + `Memory.scanSync(base,size,pattern)`（frida 17 签名）**工作正常**。
扫描结果（`tools/frida_mem_scan.py`）：

| 目标串（ASCII/UTF-8） | 命中数 | 样例地址 |
|---|---|---|
| `SkillXiulian` | **5** | `0xb9bd2788` / `0xba5160e8` / `0xc351d5d0` / `0xc351d5f8` / `0xc351d760` |
| `config_skill_xiulian` | 5 | `0xc1a5b3cf` / `0xc433891c` / `0xc7b3791c` / `0xec2a2703` / `0xec2a342e` |
| `huoli_list` | 3 | `0xbdc19a28` / `0xc342d728` / `0xd2493a5c` |
| `total_val` | 5 | `0xbd1c1738` / `0xbd1c1e70` / `0xbdc19a00` / `0xc342e5e0` / `0xd24933fc` |
| `拥有活力`(UTF-8) | 0 | —（该面板串可能非 UTF-8 存储，暂不影响结论）|

**这就是本轮要的证据**：
- 客户端**确实把 `Config.SkillXiulian` 与日常面板的 `huoli_list/total_val` 载入了内存**
  ⇒ 与第 5–7 轮的排除结论**一致**：面板数值是**客户端侧**的（本地配置/自算），
  不是我们下发字段驱动的（10621 skill exp / practice_exp / 本地存档 均已证伪，三包规格又完全一致）。
- 也说明：**要让「消耗」出现，改动点在客户端侧或"让客户端重新计算"的触发上**，
  继续改服务端字段**不可能**奏效。

---

## 四、下一步：两条可行路径（按性价比）

| # | 路径 | 说明 | 代价 |
|---|---|---|---|
| **A** | **继续 frida 内存路线**：从上面的字符串地址出发，走 LuaJIT 对象图（GCstr → 拥有它的 table → `Config` 表），把 `Config.SkillXiulian` 与面板数据表**dump 出来**，再定位它读的键 | 需要处理 LuaJIT 内存布局（TValue 8B / GCstr 头 / table node 数组）；frida 已具备全部能力（读写内存 + 扫描）| 中高（纯逆向，但无需重建 APK）|
| **B** | **改用项目自带的 Lua 注入通道**：`单机版内置服务端.md` 那套（`config.luac` 注入 + `local_server.lua`/`observer.lua`），在**游戏自身的 Lua VM 里**执行探针，直接打印 `Config.SkillXiulian` / 面板取数 | 项目已验证过这条路在**本机 MuMu** 上可行；但需要重新打包/签名/安装 APK | 中（构建流水线已有）|

> 建议 **先 A 后 B**：A 不需要动 APK，先用本轮已拿到的地址试着 dump 出 `Config.SkillXiulian` 的结构，
> 就能知道客户端用哪个键查表；若 A 的 LuaJIT 布局太深，再走 B。

---

## 五、交付与本轮状态

| 项 | 状态 |
|---|---|
| 新增工具 | `tools/frida_probe_modules.py`（按 PID attach + 模块/符号探针）、`tools/frida_mem_scan.py`（内存扫描）|
| 代码改动 | **无**（`server/` 未动）|
| 运行态 | mock_server PID **28336**（9000/8080）✅；游戏 PID **19238** 前台运行 ✅；**32 位 frida-server 仍在跑**（下次可直接 attach）|
| 基线 | `lv=70 / scene=10001` 不变 |
| 已知坑 | ① 按名字 attach 必失败（名字乱码）→ 用 PID ② 必须用 32 位 `fs-x86` ③ ARM 库不可见 → 原生钩子不可用 |
