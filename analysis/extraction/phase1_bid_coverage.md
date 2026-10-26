# PHASE 1 — 客户端 bid 清单 × 服务端配置覆盖度（**方法修正版**）

> 客户端来源：`CS_16605.bid_list` 实机抓包 ⇒ **107** 个 bid。
> 服务端：扫描 1006 个 cfg JSON，只认**字段值**形式 `"bid"|"id"|"item_id"|"item_bid"|"goods_id"|"cfg_id": N`。

## 0. 自我纠错：上一版方法无效（必须记录）

第一版用「任意数字键 `"N":` 命中」判覆盖，得到 73/107，**该结论作废**：
命中文件 top 是 `config_rune_data.json`(47)、`config_npc.json`(23)、`config_sound_data.json`(15) —— 全是**无关表的同号数字碰撞**（符文 id/NPC id/音效 id），
不是物品定义。**教训：跨表数字对齐必须限定字段语义，不能拿『键』当『物品』。**

## 1. 修正后的覆盖（字段值口径）

⇒ **29/107 在配置里有真实字段定义，78 个未找到**。

| # | bid | 出处（最多 3） |
|---|---|---|
| 1 | 1010 | `cfg/config_auction_data.json`, `cfg/config_function.json`, `cfg/config_group_control.json` |
| 2 | 1015 | `cfg/config_auction_data.json`, `cfg/config_group_control.json`, `cfg/config_guild_mission_data.json` |
| 3 | 1017 | `cfg/config_auction_data.json`, `cfg/config_group_control.json`, `cfg/config_guild_mission_data.json` |
| 4 | 1018 | `cfg/config_auction_data.json`, `cfg/config_group_control.json`, `cfg/config_guild_mission_data.json` |
| 5 | 3004 | `cfg/config_exchange.json`, `cfg/config_mall.json`, `cfg/config_shop.json` |
| 6 | 4005 | `cfg/config_exchange.json`, `cfg/config_mall.json`, `cfg_kconst/config_exchange.json` |
| 7 | 4006 | `cfg/config_exchange.json`, `cfg/config_mall.json`, `cfg_kconst/config_exchange.json` |
| 8 | 5004 | `cfg/config_exchange.json`, `cfg/config_npc.json`, `cfg_kconst/config_exchange.json` |
| 9 | 5005 | `cfg/config_exchange.json`, `cfg/config_npc.json`, `cfg_kconst/config_exchange.json` |
| 10 | 5006 | `cfg/config_exchange.json`, `cfg/config_npc.json`, `cfg_kconst/config_exchange.json` |
| 11 | 5007 | `cfg/config_exchange.json`, `cfg_kconst/config_exchange.json`, `cfg_kconfig/config_exchange.json` |
| 12 | 5008 | `cfg/config_exchange.json`, `cfg_kconst/config_exchange.json`, `cfg_kconfig/config_exchange.json` |
| 13 | 5021 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 14 | 5022 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 15 | 5030 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 16 | 5031 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 17 | 5032 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 18 | 5033 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 19 | 6001 | `cfg/config_exchange.json`, `cfg_kconst/config_exchange.json`, `cfg_kconfig/config_exchange.json` |
| 20 | 7014 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 21 | 7015 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 22 | 7016 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 23 | 7017 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 24 | 7020 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 25 | 7021 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 26 | 7022 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 27 | 7023 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 28 | 7024 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |
| 29 | 7031 | `cfg/config_npc.json`, `cfg_kconst/config_npc.json`, `cfg_kconfig/config_npc.json` |

## 2. 未找到定义的 bid

`3032, 3041, 5010, 5011, 5013, 5014, 5015, 5016, 5017, 5025, 5026, 5027, 5029, 5034, 5035, 5037, 5038, 5043, 5046, 5058, 5068, 5070, 5086, 5991, 5992, 5995, 5996, 5998, 7025, 7026, 7029, 7035, 7036, 7038, 7040, 7041, 7042, 7099, 7994, 7995, 7996, 7998, 7999, 91018, 93032, 94005, 95004, 95005, 95006, 95010, 95014, 95016, 95017, 95025, 95026, 95027, 95029, 95030, 95031, 95032, 95033, 95034, 95035, 95043, 96002, 96006, 97005, 97006, 97014, 97015, 97016, 97017, 97020, 97025, 97026, 97028, 97043, 97044`

> 未找到 ≠ 一定缺失：服务端可能只在运行期（GM/掉落/商店生成）持有，或数据在 `_*.json`（非 cfg 目录）与数据库里。此表用于**排序深挖优先级**。

## 3. `9xxxx` 派生规律（**只依据客户端清单自身**，不依赖服务端配置）

客户端一次发出的同一份 `bid_list` 里，存在 **28 组** `(9xxxx, 基号)` 同时出现的配对：

| 9xxxx | 基号（同清单内） |
|---|---|
| 91018 | 1018 |
| 93032 | 3032 |
| 94005 | 4005 |
| 95004 | 5004 |
| 95005 | 5005 |
| 95006 | 5006 |
| 95010 | 5010 |
| 95014 | 5014 |
| 95016 | 5016 |
| 95017 | 5017 |
| 95025 | 5025 |
| 95026 | 5026 |
| 95027 | 5027 |
| 95029 | 5029 |
| 95030 | 5030 |
| 95031 | 5031 |
| 95032 | 5032 |
| 95033 | 5033 |
| 95034 | 5034 |
| 95035 | 5035 |

⇒ 支持 **`9xxxx = 90000 + 基号`**（如 `93032→3032`、`97014→7014`）—— **STRONG_INFERENCE**（同清单内配对自证，但仍需客户端 `config_item*` 表或实机 UI 确认语义：
强化/绑定/礼包变体？**UNKNOWN**）。

> 说明：第一版曾用「基号能在 cfg 里找到」来支撑该规律，现**降级为不采用**（理由同第 0 节）；本节改由**同清单配对**支撑，证据链更干净。