# 换渲染后端实验（MuMu: dx → vk）

> 目的：验证「看不到角色 / 地图模糊」是否为**模拟器图形环境**问题（假设 B）。
> 做法：改 MuMu 的渲染后端，跑**同一个 APK + 同一个服务端**，与 dx 后端逐像素对比。
> 结果：**后端切换造成了巨大渲染差异（98.85%），但"角色是否可见"我无法用机器判定。**

---

## 一、MuMu 的图形设置（取证）

`MuMuManager.exe setting --vmindex 0 --all_writable` 读到：

```
renderer_mode        = "dx"                    ← 原值（可选项：vk / dx）
renderer_strategy    = "auto"
force_discrete_graphics = "true"
gpu_mode             = "high"                  ← 可选项：low/middle/high/custom
gpu_model.custom     = "Adreno (TM) 740"       ← ★ 把 GPU 伪装成 Adreno 740
```

**关键**：宿主真实 GPU 是 `NVIDIA GeForce RTX 4060 Laptop`，
但 MuMu 向 App 报告的是 **`Adreno (TM) 740`**，并且 App 加载的是
`/system/lib/egl/libGLESv2_emulation.so`（**模拟** GLES）。
⇒ 游戏是在**GLES 模拟层 + ARM(houdini) 翻译层**上跑的，
而角色用 **Spine 骨骼动画**渲染（`body_spine_name` / `spine_renderer.luac`）。

---

## 二、切换操作与结果

```powershell
MuMuManager.exe control --vmindex 0 shutdown
MuMuManager.exe setting --vmindex 0 --key renderer_mode --value vk
MuMuManager.exe control --vmindex 0 launch
```

回读确认 `renderer_mode = "vk"`；开机后 adb（16320→16384）恢复，APK 仍在，服务端仍在。

### 客户端侧状态：与 dx 后端**完全一致**（都是正确的）

```
t_1500_isLoadState_true_mapResCache_192        ← 地图加载完成
playerAppear: body=userdata spine_name=[R10100] career=1 action=[stand]
playerNew n_1_a_1                              ← 角色元素已创建
```

⇒ 换后端**没有改变任何数据/对象/元素创建**，两边都正常。

### 渲染结果：**差异巨大**

| 对比 | 差异像素占比 | 包围盒 |
|---|---|---|
| `stage3_run1` vs `stage3_movement_attempt`（**同为 dx**） | **0.12%** | (118,361,2332,768) |
| `PHASE2_ingame` vs `PHASE2_login_ok`（更早两次） | 0.08% | (188,385,2394,842) |
| **`stage3_vk` vs `stage3_movement_attempt`（vk vs dx）** | **98.85%** | (0,0,2560,1440) 全屏 |

**同后端的两次截图几乎一模一样（0.1%），而 vk 截图与 dx 几乎全屏不同。**

图像统计：

| 截图 | 唯一色数 | 平均亮度 | 中心区细节 |
|---|---|---|---|
| `stage3_vk.png` (vk) | 50,272 | **82.1** | 4,573 |
| `stage3_run1.png` (dx) | 44,312 | **135.3** | 4,349 |

⇒ vk 下画面**明显更暗**、色数更多。**渲染确实变了**，但我**无法判断变好还是变坏**。

---

## 三、结论（已由人眼确认）

**用户确认：换到 vk 后"和之前一样：地图模糊、没有角色"。**

⇒ **换渲染后端（dx → vk）不能解决该现象。**

同时修正我上面的一个误读：98.85% 的像素差**并不代表内容变了** ——
实测平均亮度从 135.3 掉到 82.1，这是**全局明暗/伽马差异**：
几乎每个像素都变了一点，但画面内容看起来一样。所以"98.85%"这个数字
**不能当作"渲染改善了"的证据**，我当时没有下这个结论是对的。

### 顺带取到的两条有意义的旁证

| 项 | dx | vk |
|---|---|---|
| `gl.max_texture_units` | 32 | **96** |
| `gl.max_texture_size` | 16384 | **32768** |

VK 的 GL 能力明显更强，**现象却完全一样** ⇒ 更不像"能力不足"，而像**渲染路径本身的问题**。

### 其它已排除

| 候选 | 依据 |
|---|---|
| 角色 Spine 资源缺失 | **`R10100` 在 APK 里齐全**：`assets/res/spine/R10100/R10100_action{1..N}.{atlas,json,png}` 共 44 个条目 |
| 纹理解码失败 | logcat 里**没有**任何 texture/atlas/png 的加载或解码错误 |
| 数据/对象链路 | 两个后端下读数完全一致且都正确（`isLoadState=true`、`mapResCache=192`、`body=userdata`、`spine_name=R10100`、`action=stand`） |

---

## 四、我这一轮**没能**做到的事（如实说明）

**我无法看到截图。** 本机的"看图"能力依赖 `dsh-eyes` 插件，而它当前
**没有任何可用后端**：

```
XAI_API_KEY        未设置   （xai   → grok-4.6）
OPENAI_API_KEY     未设置   （openai→ gpt-4o-mini）
DASHSCOPE_API_KEY  未设置   （qwen  → dashscope）
grok / claude / codex CLI   均未安装
```

所以"角色到底有没有显示、地图糊成什么样"这类判断，**只能由人眼给出**。

**如果你想让我以后能直接读截图**（对这个项目帮助很大），任选其一即可：

1. 设一个环境变量（`XAI_API_KEY` / `OPENAI_API_KEY` / `DASHSCOPE_API_KEY`）后重启 DSH；
2. 或者安装 `grok` / `claude` / `codex` 任一 CLI 并登录；
3. 或者在 DSH 的 dsh-eyes 设置里选 `custom`，填一个 OpenAI 兼容的 `baseURL` + `model`。

---

## 五、下一步建议（按性价比排序）

| 方案 | 说明 | 成本 |
|---|---|---|
| **A. 真机验证** | 同一个 APK + 同一个服务端，换真实 Android 手机跑一次。**这一步能一锤定音**：角色出现 ⇒ 确认是模拟器图形栈问题，服务端零改动 | 低（但要一台手机） |
| **B. 继续调 MuMu 图形项** | 还有 `gpu_mode`（`high→custom`）、`gpu_model.custom`（现在伪装成 `Adreno (TM) 740`）、`force_discrete_graphics`（宿主是 RTX 4060 + AMD 核显双显卡）没试过 | 中（每次要重启模拟器） |
| **C. 换个假设：坐标/相机** | 我们的坐标为 `(1320, 2036)`（来自 `config.json` 的 `spawn`，来源不明）。若它不是地图上的合法位置，相机可能对不准、角色可能在可视区外。可从 `config_map.luac` 读出 bid=10001 的尺寸再验证 | 中 |
| **D. 先解锁我的视觉** | 见第四节，之后所有截图我都能自己看 | 低 |

**回滚到 dx（原值）**：

```powershell
MuMuManager.exe control --vmindex 0 shutdown
MuMuManager.exe setting --vmindex 0 --key renderer_mode --value dx
MuMuManager.exe control --vmindex 0 launch
```
