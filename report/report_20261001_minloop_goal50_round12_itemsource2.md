# 50 轮目标 · Round 12（goal round 30）—— 找到**真实物品来源**的候选表：`config_item_gift` / `config_reward_*`

> 时间：2026-10-01 ｜ 本轮目标：从礼包类物品找"使用后产出物品"的真值来源

---

## 〇、一句话结论

> ① **否证**："礼包物品的产出内容写在 `item_config.json` 里" —— 实测 `type=6` 礼包（如 `33001`）的
> `use_type / value / effect / next_bid / condition` **全部为 `null`**，本表**不含产出内容**
> （只在 `desc` 字符串里用自然语言提了一句"可开出…"）。
> ② ★ **新进展**：APK 的 `assets/src/config/` 下有 **347 张表**，其中**专门管礼包/奖励的有 11 张**，
> 最相关的三张是 **`config_item_gift.luac`（物品礼包 ← 最可能的真实产出源）**、
> `config_reward_data.luac`、`config_reward_box_data.luac`（另有 `config_item_fuse`、
> `config_chief_award_data`、`config_holiday_dial_reward_data`、`config_dungeon_reward_desc` 等）。
> ⇒ **下一轮就从 `config_item_gift.luac` 抽出"礼包 → 物品"的真值**，用它给背包塞**真物品**，
> 从而把 `10500`（掉落/进包）这条环用真数据验证掉 —— 不再需要任何占位物。

---

## 一、本轮证据

### 1.1 礼包物品里**没有**产出字段（否证）

```
33001 = {"name":"VIP2每日礼包", "type":6, "quality":4,
         "use_type":null, "value":null, "effect":null, "next_bid":null,
         "condition":null, "is_fuse":0, "use_num":0,
         "desc":"VIP2每日福利礼包,打开后获得以下全部内容\n<div …>注:幸运礼盒可开出坐骑进阶丹、洗髓丹、神器注灵石等奖励</div>"}
```
- 结构化字段**全空** ⇒ 产出内容不在这张表；
- `desc` 里点名的 **洗髓丹** 恰是本表 `bid=36500` 的条目名，与本会话上一轮"界面读数交叉验证"一致
  ⇒ **又一次印证 `item_config.json` 就是客户端的物品表**（但**不是**奖励来源表）。

### 1.2 ★ 找到候选真值表（新证据）

```
assets/src/config/ 共 347 张表；与礼包/奖励/使用相关的 11 张：
  config_item_gift.luac                        ← ★ 物品礼包（最可能的产出源）
  config_reward_data.luac                      ← 奖励数据
  config_reward_box_data.luac                  ← 奖励箱
  config_reward_back_data.luac                 ← 奖励返还
  config_item_fuse.luac                        ← 物品合成
  config_chief_award_data.luac                 ← 首席奖励
  config_holiday_dial_reward_data.luac         ← 节日转盘奖励
  config_dungeon_reward_desc.luac              ← 副本奖励描述
  config_drop.luac / config_drop_item.luac     ← 已否证不可用（客户端不读）
  config_spouse.luac                           ← 情缘（与奖励无关，匹配到关键词）
```

---

## 二、完成 / 未完成（本轮）

### 2.1 完成
1. ★ **否证"礼包产出写在 item_config"**（结构化字段全 null，只有自然语言 desc）。
2. ★ **定位到 11 张礼包/奖励类配置表**，并挑出首选 `config_item_gift.luac`（下一轮直接抽）。
3. ★ 再次交叉印证 `item_config.json` 是客户端物品表（`desc` 中的物品名与本表 bid 对应）。
4. 自检保持 **59/59**（本轮未改代码）。

### 2.2 未完成
| # | 项 | 状态 |
|---|---|---|
| 1 | `config_item_gift.luac` 的抽取与"礼包 → 物品"真值 | 🚧 **下一轮第一件事** |
| 2 | 用真值给背包塞物品，验证 `10500` 进包环 | ❌ 受阻于 ① |
| 3 | `12404~12450` 命令差异对照 | 未做 |
| 4 | 客户端 `10102/10103` 不上线（唯一硬卡点） | 仍 blocked（需外部原生观测手段） |

---

## 三、下一轮建议（明确）

1. ★ **抽取 `config_item_gift.luac`**：复用本项目已有的 `config_*` 抽取路径
   （`config_mission.luac`/`config_item.luac` 已被同类工具还原成 JSON，见 `analysis/1.4.9/item/`），
   产出 `analysis/1.4.9/item/_config_item_gift.json`。
2. 若能拿到"礼包 → 物品 bid + 数量"的真值 ⇒ 在最小回环服里加一条**真值路径**：
   `使用礼包（或直接投放）→ 10500 推送 → 背包可见`，并加断言（物品 bid/数量来自该表，不编造）。
3. 若该表也解不出内容 ⇒ 依次试 `config_reward_data.luac` / `config_reward_box_data.luac`，
   并把结论（哪张可用/不可用）写进 README §5.3 的证据等级表。
4. 继续 `12404~12450` 差异对照。

---

## 四、本轮产物

| 文件 | 说明 |
|---|---|
| 本报告 | ★ 否证"礼包产出在 item_config" + 发现 11 张礼包/奖励候选表 |
| `server/item_config.json` | 本轮被否证的证据来源（结构化字段全 null） |
| `anzbao/jstm.apk` 内 `assets/src/config/*.luac` | 下一轮的抽取对象（`config_item_gift.luac` 等） |
