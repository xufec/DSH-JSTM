# 最小回环 · 第 23 轮（goal round 17/20）★★★ `SendProtocal` 全链已解：**两处失败都"跳过 Send 却返回 true"**；发送器 = `UserMsgAdapter`

> 时间：2026-10-01 ｜ 目标 APK 1.4.9 ｜ 本轮目标：解析 `GGET` 常量名，确定发送对象。

---

## 〇、一句话结论

> 用 `tools/luajit_dis.kidx`（该文件已验证 `GGET/GSET` 的 D 也走同一映射）把
> `base_controller.lua` **proto#3 `SendProtocal`** 的全局名全部还原，得到**完整且可判定**的实现：
>
> ```lua
> function BaseController:SendProtocal(proto)
>   local gn = GameNet:getInstance()
>   if not gn:IsLoginServerConnect() then return end          -- 0-9
>   Debug('发送协议:', proto.m_msg_type)                       -- 10-15
>   UserMsgAdapter:WriteBegin()                                -- 16-18
>   if not UserMsgAdapter:WriteHeader(proto.m_msg_type, 0) then
>     goto ret_true                                            -- 19-25  ★ 静默跳过 Send
>   end
>   if not proto:Encode(UserMsgAdapter) then
>     goto ret_true                                            -- 26-31  ★ 静默跳过 Send
>   end
>   UserMsgAdapter:Send(GameNet:getInstance().game_net_id)     -- 32-39
>   ::ret_true:: return true                                   -- 40-42
> end
> ```
>
> **⇒ "返回 true 却无字节"的机制被完全证实**：`WriteHeader` 或 `Encode` 任一失败，
> 代码**跳过 `Send`** 并**直接 `return true`**（`JMP → 40 → RET1`）。
> 也顺带**更正**了第 21 轮那个"误报"的自评：**`UserMsgAdapter` 确实是发送器**（`v43_socket=FOUND UserMsgAdapter` 是对的）。

---

## 一、关键证据：逐条反汇编（全局名已解析）

```
  0 GGET  D=0 -> 全局 'GameNet'          5 TGETS IsLoginServerConnect
 10 GGET  D=3 -> 全局 'Debug'           11 TGETS socket          ← Debug('发送协议:', …) 的一段
 16 GGET  D=7 -> 全局 'UserMsgAdapter'  17 TGETS WriteBegin
 19 GGET  D=7 -> 全局 'UserMsgAdapter'  20 TGETS WriteHeader
 24 ISF / 25 JMP D=32782                 ← ★ 失败 ⇒ 跳 40（返回 true）
 26 MOV / 27 TGETS Encode               28 GGET D=7 -> 'UserMsgAdapter'
 30 ISF / 31 JMP D=32776                 ← ★ 失败 ⇒ 跳 40（返回 true）
 32 GGET  D=7 -> 全局 'UserMsgAdapter'  33 TGETS Send
 34 GGET  D=0 -> 全局 'GameNet'         38 TGETS game_net_id
 40 IST / 42 RET1                        ← 返回 **true**
```

---

## 二、由此可判定的结论（本轮）

1. ★ **发送器身份确定**：`UserMsgAdapter`（全局），**并且它接收 `game_net_id` 作为 `Send` 的参数**。
2. ★ **两处静默跳过点确定**：`WriteHeader` 或 `Encode` 失败 ⇒ **不发、但返回 true**。
   这与本项目此前多轮观察到的"函数返 true、抓包 0 字节"**完全一致**。
3. ★ 因此**下一步只剩一个未知**：对 `10102` 而言，到底是
   **`WriteHeader` 返假**（⇒ 命令号/包头被拒），还是 **`Encode` 返假**（⇒ CS 规格不符）。
   ——第 20 轮已测到 `Encode(10102)=true`，**但那次没测 `WriteHeader`**；
   而且第 20/21 轮的包装**没有在运行期命中**（原因待查：可能 `UserMsgAdapter` 是个**被替换过的表**，
   或包装装在了旧表上）。
4. ⚠️ **UNKNOWN**：为什么我的包装在运行期"一条都没打印"。第 22 轮的自查发现
   **我自己的守卫 bug**（`tag_wrapped` 先置位后重置）也属同类，
   说明"探针是否真的装上了"需要**每次安装都留证据**（下一步必须做）。

---

## 三、完成 / 未完成

### 3.1 完成
1. ★★ **`SendProtocal` 全链解析完成**（含两处"静默跳过 + 返回 true"），机制层面**闭口**。
2. ★ **更正第 21 轮的自评**：`UserMsgAdapter` 确实就是发送器（当初的判断是对的，误报的是我后来的"全量扫描"结论）。
3. ★ 找到 `debug` 段的全局名（`Debug`）与发送段的全局名（`UserMsgAdapter`），
   并补齐了 `GGET` 名字解析的**可用方法**（`kidx(pt, D)`，已实测可用）。

### 3.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `10102` 究竟是 `WriteHeader` 返假还是 `Encode` 返假 | **UNKNOWN**（只测到 Encode=true） |
| 2 | 我的运行期包装为何"一条都没打印" | **UNKNOWN**（须加"安装自证"） |
| 3 | `10102/10103` 上线、`scene`、`12402`、`20002`、奖励链 | ❌ |
| 4 | 两实例差异 | **UNKNOWN** |

---

## 四、下一轮直接照做（已经很窄）

1. ★ **给"包装是否装上"做自证**（本轮教训）：
   安装时立刻 `rep('installed', name .. ' ' .. tostring(obj))`，并**每 30 拍比对一次对象身份**
   （若 `_G.UserMsgAdapter` 变了 ⇒ **重新装**）。修掉两处守卫 bug（`_ml42_add.lua`/`_ml45_add.lua`）。
2. ★ **只测一件事**：包 `UserMsgAdapter.WriteHeader`，**打印返回值**（不再按命令号过滤，避免过滤逻辑出错），
   配合包 `DengluCtrl.SendProtocal` 设全局消息号 ⇒ 得到"每个命令的 `WriteHeader` 返回值"。
   - `10102` 的 `WriteHeader=false` ⇒ 命令号被拒 ⇒ 去查客户端命令注册表；
   - `WriteHeader=true` 但服务端仍收不到 ⇒ 问题落在 **`UserMsgAdapter:Send`** 内部（查它的队列/通道）。
3. 结论明确后：`10102` 上线 → 验证第 11 轮**幂等提交**（`<< 12403 提交成功` + 奖励落库）。

---

## 五、本轮产物

| 文件 | 说明 |
|---|---|
| 本报告 §一 | ★ `SendProtocal` 逐条反汇编（全局名已解析） |
| `tools/luajit_dis.py::kidx` | 已实测可用于 `GGET/GSET` 名字解析（本轮据此解开） |
| 设备内 `files/dsh_v45.txt` | 上轮运行期证据（字段扫描 0 命中、包装未触发）⇒ 与 §四.1 的自证需求对应 |
