# ★ 系统性根因：`runtime.CUR_VER` 是**全局变量**，多版本并发时会互相覆盖

> 发现于 PHASE 2.26（用户报障"日常/提升/头像旁状态"等多个面板异常，且 MuMu 内**三个版本的游戏同时在跑**）。
> 证据等级：**STRONG_INFERENCE**（机制已确证 + 日志已确证三版本并发；未做"并发复现实验"直接抓包）

---

## 一、机制（CONFIRMED，读源码）

**版本族判定**（`core/runtime.py::ver_family_of`，按 `CS_1110` 的 args 键数与体长）：

```python
n = len(args or {})
if n <= 2:            return '1.3.0'     # 1.3.0 只报 account 一对
if int(body_len) < 210: return '1.4.11'  # 1.4.11 键数多但体长 < 210
return '1.4.9'
```

**判定本身是对的** —— 日志实测（`SCAccountLogin ... ver=`）：

| 版本族 | 次数 | 对应客户端 |
|---|---|---|
| `1.3.0` | 76 | `com.shiyue.dldl.ewan`（1.3.0）|
| `1.4.9` | 108 | `com.shiyue.dldl.ewan.qihoo`（1.4.9）|
| **`1.4.11`** | **4** | `com.shiyue.dldl.ewan.baidu2`（**1.4.11**，主目标）|

**问题出在存储方式**：`runtime.CUR_VER` 是**模块级全局字符串**，而 mock_server 在**每个请求**里重绑它：

```python
# mock_server.py L9606
runtime.CUR_VER = getattr(self, '_ver_family', '1.4.9')   # [P2B]
```

服务端是**多线程**（`socketserver.ThreadingTCPServer`）⇒ **连接 A 设的值会被连接 B 覆盖**。

---

## 二、后果（可解释用户报障）

`build_10302` / `build_10301` 等构造里都有 `if runtime.CUR_VER != '1.3.0':` 分支：

```python
# role/storage.py build_10302
for k in (28 项): b += w_u32(...)
if runtime.CUR_VER != '1.3.0':
    b += w_u32(st.get('diamond'))          # ← 若被 1.3.0 连接污染则**整个跳过**
    b += w_u32(st.get('rainbow_diamond'))  # ← 同上
```

⇒ 1.3.0 连接一发包，1.4.11 客户端的下一包就会**少 8 字节** ⇒ **整包错位** ⇒
**该批次所有依赖 `SC_10302`/`SC_10301` 的面板显示异常/空白**。

**实测印证**：我用 `account+platform`（≤2 键）登录时被判为 1.3.0，`10302` 回包 **114 字节**
（= 2 + 28×4，**正好少 2 个 u32**）；而 1.4.11 权威结构需要 **122 字节**。

---

## 三、✅ 已修复（PHASE 2.26，方案 A：线程局部）

**改动（3 处，最小面）**：

| 文件 | 改动 |
|---|---|
| `server/core/runtime.py` | 删除模块级 `CUR_VER = '1.4.9'`；改为 `_TLS = threading.local()` + `set_cur_ver()` / `get_cur_ver()` + **PEP 562 `__getattr__`**（使旧的 `runtime.CUR_VER` **读取**写法全部继续可用，但走线程局部）|
| `server/core/runtime.py` | `_RuntimeView.cur_ver` 的 getter/setter 改为走 `get_cur_ver()` / `set_cur_ver()` |
| `server/mock_server.py` L9606 | `runtime.CUR_VER = ...` ⇒ **`runtime.set_cur_ver(...)`**（并注明**不可**再写 `runtime.CUR_VER =`，否则会创建真属性、遮蔽 PEP 562 读取）|

**验证（两层）**：

1. **线程隔离自测**：A 线程设 `1.3.0`、B 线程设 `1.4.11`，各自 `sleep` 后读取 ⇒ **各自保持自己的值** ✅
2. **真实并发实测**（`tools/_verify_curver_isolation.py`）：开两条连接（一条被判 1.3.0、一条被判 1.4.11），
   **交错各发 12 次 `10302`**，跑 3 轮：
   ```
   trial 1/2/3 :  1.3.0 连接长度 = [114] ✅
                  1.4.11 连接长度 = [122] ✅   ← 各自正确，零交叉污染
   ```
3. **完整回归**：`RUN_TESTS.ps1 -SelfStart` ⇒ 6 套件全部 ALL PASS，**失败项 = 0**；`miniloop 145/145`

> 备份：`server/backup/runtime_curver_tls_*.py`

### 原方案对比（留档）

| 方案 | 做法 | 评价 |
|---|---|---|
| **A（已采用）线程局部** | `CUR_VER` 存 `threading.local()` + PEP 562 兼容旧读取 | 最正确；改动面可控（3 处）|
| B 请求级串行 | `_reply` 外层加全局锁 | 最小改动但损吞吐 |
| C 最小缓解 | 每次读前重绑 | 治标不治本 |

### ★ 用户侧可做的确认（成本 0）

**只启动 1.4.11 那一个游戏**（强停 `com.shiyue.dldl.ewan` 与 `com.shiyue.dldl.ewan.qihoo`），
再观察那些面板。修复后**即使三版本同开也应正常**，但单独跑一遍能作为独立佐证。

---

## 四、附带确认的两处（与并发无关，已修）

| 项 | 状态 |
|---|---|
| `SC_11215` 缺 `volume`/`volume_open` 2 字节 | ✅ 已修（PHASE 2.24）|
| `10301` 的 `face_id` 默认 0 ⇒ 头像空白 | ✅ 已修（PHASE 2.25，默认 100）|
| `13036` 不回包 ⇒ 点击后空白 | ✅ 已修（PHASE 2.23，照 minloop 回 `{0,0}`）|
| **`SC_10302` 少 `diamond`/`rainbow_diamond`** | ⚠ **本次查明是"被 1.3.0 版本族污染"所致，不是构造本身缺字段**（源码里本就有这两个字段）|
