# D2 背包渲染修复 —— 客户端资源调查报告

> 日期：2026-10-02 ｜ 范围：APK 与模拟器客户端资源调查 ｜ **未修改 server/ 任何文件，未重打包/未重装 APK**
> 任务假设（来自 phase16_prep.md §1.4 INFERENCE）：主背包 4 个 bid（28514/28560/28515/21403）在客户端无对应图标资源，致 cell 渲染失败、背包空显 0/150。

---

## 〇、最终结论（先看这里）

**P1「补图标资源并入 1.4.11 APK」不可行，且无对象可补 —— 该修复路径的前提（图标缺失）经实测被推翻。**

- 这 4 个 bid 的图标 PNG **在当前 1.4.11 客户端里物理存在、已登记进资源清单、加密格式与可正常渲染的图标完全一致**。
- 运行时日志显示：服务端曾一次性向主背包(bag_code=1)下发 6 件物品（含这 4 件 + 33001 + 36500），**6 件的图标 PNG 全部存在**；若客户端仍空显，则空屏根因**不是图标资源**。
- 10502 协议物品 struct（16 字段/件）服务端下发与客户端期望**逐字段逐类型对齐**，P3 字段对齐也无偏差。
- 因此：**不执行 apktool 重打包 / 重签名 / zipalign / adb install**。重打包是高风险不可逆操作，且对本问题零收益，反而可能破坏已跑通的 fakelogin 登录链路。

D2 维持现状：服务端 P0 过滤这 4 个 bid。真正根因在**客户端背包 bag_code/类型分流 或 运行时解析丢弃**，需动态取证（logcat/frida 跟踪背包数据流），不属于「客户端补资源」范畴，也不在本次允许改 server 的范围内。

---

## 一、版本与工具链定位（只读核对）

| 版本 | APK 路径 | 包名 / versionCode | 说明 |
|---|---|---|---|
| 1.4.11（现网客户端） | `anzbao/jstm_142165.apk` | `com.shiyue.dldl.ewan.baidu2` vc46 | 本次分析底包 |
| 1.4.11 已装补丁包 | `patched/jstm_1411_fakelogin_aligned.apk` | 同上 | 运行于 MuMu `127.0.0.1:16384` |
| 1.4.9 | `anzbao/jstm.apk` | `com.shiyue.dldl.ewan.qihoo` vc44 | 跨版本比对 |
| 1.3.0 | `anzbao/dldlJl.apk` | `com.shiyue.dldl.ewan` vc25 | 跨版本比对 |

工具链（仅核对存在，**未实际调用**）：
- apktool：`001/apktool_3.0.3.jar`；Java 21（Eclipse Adoptium）。
- zipalign/apksigner：`D:\Android\SDK\build-tools\34.0.0\`。
- 签名 keystore：`patched/dsh.keystore`（alias=dsh）。
- adb：`D:\ADB\platform-tools\adb.exe`；设备列表见 `127.0.0.1:16384`(MuMu) 与 `emulator-5554` 均 online。

> 备注：本次资源定位全程用 Python `zipfile` 只读列目录/读字节，未对 APK 做任何解码落盘或改写。

---

## 二、服务端配置线索（只读 server/cfg/config_item.json）

`Config.ItemData.<bid>` 为位置数组，关键字段下标：`[1]=bid`、`[2]=名称`、`[3]=type`、`[6]=品质`、`[8]=最大堆叠`、**`[17]=icon bid`**。

| bid | 名称 | type | icon bid([17]) |
|---:|---|---:|---:|
| 28514 | 小型宝石袋 | 6 礼包 | **30035** |
| 28560 | 抽奖券 | 7 材料 | **28560** |
| 28515 | 庆典夏日时装券 | 5 消耗品 | **28515** |
| 21403 | 牧夫 | 43 主动符文 | **21403** |
| 10001 | 1星香嫩豆腐(对照) | 31 | 10000 |
| 20001 | 灵性(对照) | 4 | 20001 |
| 40005 | 见习长枪(对照) | 100 | 40001 |
| 28030 | 幸运币(对照) | 0 | 28030 |

物品图标按 **icon bid** 命名，不是按 item bid。

---

## 三、客户端图标加载机制（证据）

1. 资源目录：`assets/res/resource/item/<iconbid>.png`（1.4.11 内共 1461 个 png）。
2. 路径模板来自客户端 `assets/src/common/pathtool.luac`：
   - 字符串常量 `resource/item/%s.png`，函数 `getItemRes` / `getItemResByBid` / `item_res`。
   - 即：客户端按 icon bid 拼 `res/resource/item/<iconbid>.png` **直接加载独立 PNG**，不是走 atlas plist 取帧。
3. 资源登记清单：`assets/src/all_res_file.luac` 列出全部受管资源文件。
4. **资源加密**：所有该目录 png（含可正常渲染的）文件头均为同一 8 字节魔数
   `73 68 69 79 75 65 67 61 6d 65` = ASCII **"shiyuegame"**（厂商自定义封装，非裸 PNG）。
   → 这解释了为何直接读字节 PNG 签名校验为 False；**问题图标与正常图标用的是同一封装**，无差异。

---

## 四、跨版本图标存在性比对（核心证据）

`assets/res/resource/item/<iconbid>.png` 是否存在：

| icon bid | 用途 | 1.4.11 | 1.4.9 | 1.3.0 |
|---:|---|:--:|:--:|:--:|
| 30035 | 28514礼包 | ✅ | ✅ | ✅ |
| 28560 | 28560抽奖券 | ✅ | ✅ | ❌(新版内容) |
| 28515 | 28515时装券 | ✅ | ✅ | ❌(新版内容) |
| 21403 | 21403主动符文 | ✅ | ✅ | ❌(新版内容) |
| 10000 | 对照-香嫩豆腐 | ✅ | ✅ | ✅ |
| 20001 | 对照-技能书 | ✅ | ✅ | ✅ |
| 40001 | 对照-见习长枪 | ✅ | ✅ | ✅ |
| 28030 | 对照-幸运币 | ✅ | ✅ | ❌ |

**判定**：4 个问题图标在现网 1.4.11 中**全部存在**。28560/28515/21403 是 1.3.0→1.4.9 之间新增的内容，1.4.9 与 1.4.11 都已带上。**不存在「旧版有、1.4.11 缺」的情况，因此没有可从旧版回灌的资源。**

进一步核验（1.4.11）：

| 检查项 | 30035 | 28560 | 28515 | 21403 | 10000(对照) |
|---|:--:|:--:|:--:|:--:|:--:|
| 物理文件存在 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 大小(bytes) | 2082 | 2918 | 2550 | 2646 | 1458 |
| `all_res_file.luac` 已登记 | ✅ | ✅ | ✅ | ✅ | ✅ |
| "shiyuegame" 魔数头 | ✅ | ✅ | ✅ | ✅ | ✅ |

→ 问题图标与正常图标在「存在性 / 登记 / 封装格式」三个维度**完全同质**。

---

## 五、运行时证据（server/logs/tcp.log，只读）

`2026-10-02 02:53:37` 实际下发：

```
>> cmd=10502 ? body(5)=01 01 03 e9 00        # 请求主背包 bag_code=1
<< 10502 SC_10502 bag_code=1 items=6
   [(308,28514,2),(309,28560,2),(310,28515,2),(312,21403,3),(313,33001,1),(314,36500,1)]
```

这 6 件物品的图标存在性（本报告 §二/§四 方法核对）：

| bid | 名称 | type | icon bid | 图标存在 |
|---:|---|---:|---:|:--:|
| 28514 | 小型宝石袋 | 6 | 30035 | ✅ |
| 28560 | 抽奖券 | 7 | 28560 | ✅ |
| 28515 | 庆典夏日时装券 | 5 | 28515 | ✅ |
| 21403 | 牧夫(主动符文) | 43 | 21403 | ✅ |
| 33001 | 蛊风兽甲 | 160 | 42501 | ✅ |
| 36500 | 半神头盔.六阶 | 240 | 44505 | ✅ |

**6/6 图标全部存在。** 若客户端此时背包仍空显 0/150，则空屏与「缺图标」无关——否则连 33001/36500 这两件非问题物品也会一起消失。

旁证：同次会话客户端连续请求了 bag_code = 01,02,03,04,05,06,07,08,0c,0d,10,11 等十几个囊码；`bag_code=2`(装备栏)返回 6 件装备(40003/41803/41403/41603/41003/41213)，其图标亦均存在。

---

## 六、P3 协议字段对齐核对（只读，逐字段）

客户端 `assets/src/config/protocal/cmd_resolve_105.luac` 中 `SCRoleBag_10502` 的 items struct：

```
items__T__ id@I ## bid@I ## hero_bid@I ## bind@C ## intensify_lev@C ##
           pos@H ## quantity@H ## ctime@I ## expire_ts@I ## durable@H ##
           object@C ## attrs_ext@D|..| ## attrs_ext_list@D|..| ##
           attrs_ext_one_list@D|..| ## jewel_list@D|..| ## str_ext_list@D|..|
（@I=u32, @C=u8, @H=u16, @D=u16计数前缀的列表）
```

服务端 `server/inventory/service.py :: build_bag_items` 逐字段写入（16 字段/件）：

| # | 客户端字段@类型 | 服务端写入 | 对齐 |
|---:|---|---|:--:|
| 1 | id @I | w_u32(item_id) | ✅ |
| 2 | bid @I | w_u32(bid) | ✅ |
| 3 | hero_bid @I | w_u32(hero_bid) | ✅ |
| 4 | bind @C | w_u8(bind) | ✅ |
| 5 | intensify_lev @C | w_u8(intensify_lev) | ✅ |
| 6 | pos @H | w_u16(pos) | ✅ |
| 7 | quantity @H | w_u16(quantity) | ✅ |
| 8 | ctime @I | w_u32(ctime) | ✅ |
| 9 | expire_ts @I | w_u32(expire_ts) | ✅ |
| 10 | durable @H | w_u16(durable) | ✅ |
| 11 | object @C | w_u8(object) | ✅ |
| 12–16 | 5 个 @D 列表 | w_u16(0)×5（空列表） | ✅ |

外层：`bag_code@C(u8)` + `w_u16(len(items))` 列表计数，与客户端 `bag_code__C` + items 列表前缀一致。

**P3 字段对齐无偏差**，可排除「客户端解析整包失败导致全空」。

---

## 七、判定与处置

### 7.1 三条修复路径的判定

| 路径 | 判定 | 依据 |
|---|---|---|
| **P1 补图标资源 + 重打包** | ❌ **不可行/无对象** | 4 个图标在 1.4.11 已存在、已登记、格式正常；无「旧版有新版缺」可回灌 |
| P2 验证 type 渲染逻辑 | ⚠️ 疑似真因，需动态取证 | type=43 主动符文在 `common_goods_type.luac` 走 `isZhuRuneGoods`/`CommonGoodsTypeZ`，且 `backpack_const` 存在 `IN_SOULBACKPACK/SOULSTAR_PACK/ROLEARTIFACT_BAG` 等独立囊——符文/活动道具可能分流到专属囊，不进主背包 Tab |
| P3 10502 字段对齐 | ✅ 已排除 | §六 逐字段对齐 |

### 7.2 为什么不重打包

- 重打包（apktool d → 加资源 → b → zipalign → apksigner → adb install -r）会动到**已跑通的 fakelogin 补丁包**。
- 本次经实测**没有需要新增的资源**，重打包纯属高风险空操作，且可能破坏免登录/连服链路。
- 任务约束「先确认有可行修复再动手；无可行修复则如实报告」——本结论属于「无可行客户端资源修复」。

### 7.3 未执行的操作与回滚说明

- **未重打包、未重装、未 adb uninstall/install**，故无需回滚；设备上仍为原 `patched/jstm_1411_fakelogin_aligned.apk`。
- **未改 server/ 任何文件**（含 mock_server、inventory/service.py、inventory/handler.py、cfg）。
- 若后续要回滚任何「服务端 P0 过滤」，那是服务端侧动作，不在本报告范围。

---

## 八、对 D2 现状的影响与建议

- **现状影响**：维持服务端 P0 过滤这 4 个 bid。由于图标资源本就齐全，将来放开过滤后这 4 件**不应该因为缺图标而不可见**；当前空屏更可能是：
  1. 物品落在 bag_code=1，但用户查看的背包 Tab/囊码与之不对应（囊码/类型分流，P2）；或
  2. 客户端运行时在背包数据流中按 type/bag_code 过滤（需 logcat/frida 动态跟踪 `BackPackData.initItemList` / `getGoodsListByItemType`）。
- **建议的下一步（不在本任务执行）**：
  - 动态取证：在 MuMu 上打开主背包界面抓 logcat，确认客户端 `BackPackData` 收到 6 件后实际保留几件、落到哪个 bag_code/Tab。
  - 核对客户端主背包默认查询的 bag_code 与服务端 `db_bag_get(rid, bag_code=1)` 的囊码是否一致（疑似囊码错位，属服务端数据摆放/协议对接，非客户端资源）。
  - 用 GM/HTTP admin 单独加一件 type=5 消耗品到 bag_code=1，观察主背包 Tab 是否显示，以二分 type 分流假设（只读调 admin，不改代码）。

---

## 九、证据清单

- 版本识别：`aapt dump badging`（三版本包名/versionCode）。
- 资源清单：`zipfile` 只读列 `anzbao/jstm_142165.apk`（19106 entries）；`assets/res/resource/item/` 1461 png。
- 客户端机制：`pathtool.luac` 路径模板 `resource/item/%s.png`；`all_res_file.luac` 登记；"shiyuegame" 魔数头。
- 配置：`server/cfg/config_item.json :: Config.ItemData`（只读）。
- 协议：`cmd_resolve_105.luac` struct vs `server/inventory/service.py :: build_bag_items`（只读）。
- 运行时：`server/logs/tcp.log` @ 2026-10-02 02:53:37（6 件物品下发记录）。
- 画面：`analysis/runtime_evidence/shots/d2_now.png` —— 实机截屏（MuMu `127.0.0.1:16384`）：角色 DSH 正常在史莱克城(3765,1695)世界运行，71 级、任务/小地图/底部功能栏(市场/神格/宗门/魂技/进阶/伙伴/锻造/更多)齐备，**证实 fakelogin 免登录与连服链路完好**。
- 实机取证备注（诚实记录）：本次尝试打开背包界面时，被一个常驻的「50级礼包」强制领取弹窗遮挡（点 X / BACK 均不消失），未能在本会话干净地切到背包网格画面。该弹窗**自身正确渲染了一个礼包盒子图标**，侧面佐证客户端图标渲染管线本身工作正常；背包网格空显与否需后续清掉该弹窗后另行取证，不影响本报告「图标资源存在、P1 无需重打包」的结论。
- 未重打包/未重装，故无 d2 修复后背包对比截图；如需，后续可先清掉礼包弹窗再进背包补拍。
