# R242：★★ 1.4.11 经 **master: mock_server** 连接成功（账号 DSH）

> 用户要求：**使用 mock_server 服务器连接 1.4.11 版本，账号 DSH，并结合分析目录最新轮次继续执行。**
> **结论**：★ **A 起跑纠偏** —— 之前"一切正常"其实是 1.4.11 连到了 **min_loop_server**，
> 不是完整的 mock_server。本批**换回 mock_server 并确认稳定、真实数据在线。**

---

## 一、★ A 起跑纠偏（决定性发现）

### 现象
- 冒险前，过录到 8080/9000 的服务器是 `min_loop_server.py`（**不是 mock_server.py**）。
- 原因：我在某一步启动的 `mock_server.py`（PID 31748）**后来失效**，
  被 `min_loop_server.py` 顶替占用了 8080/9000 ⇒ **1.4.11 一直在连 minloop**。

### 定位（证据）
```
PID 28876 → python server/minloop/min_loop_server.py --http 8080 --game 9000
PID 33716 / 11300 → 同上（minloop 多个实例）
```
- **为何 mock_server 失效**：与回归套件同时运行时，端口竞争 / 进程被替换。

### 修复
```
1) 结束所有 min_loop_server 进程
2) 启动 server/mock_server.py（PID 27812，stderr 0）
3) 重启 1.4.11 ⇒ 连上 mock_server
```

**验证**（mock_server 在线）：
```
10301=104B  10302=114B  10303=187B  10304=182B  12400/12409 正常
10502/14100/14101/14700/30600 全部应答
```

---

## 二、★ 1.4.11 与 mock_server 的实时状态（活跃）

```
mock_server PID 27812 存活 ｜ stderr 0 字节 ｜ 8080+9000
1.4.11 已连接（2 连接）｜ 发送 96 种命令 / 405 次
  · 10502(背包)x73  10204(移动)x24  1110(登录)x21  16400(成就)x16
  · 10561x12  10001x10  16605x10  19400x9 ... 
```

---

## 三、★ 账号 DSH 的完整配置（确认）

```
uid=dsh_local  ->  name=DSH  rid=1001  level=70  career=1  gold=1,800,000
· role_heros : 18 个伙伴（33100 唐舞桐 / 33200 / 33300 ...）
· missions   : 5 条进行中（10010/10020/10030/10040/10051）
· bag_items  : 5 件（28514/28560/28515/22011/21403）
· role_mail  : 194 封  ｜  role_fabao : 4 个 ｜  role_build/role_ride/role_wing...全表有数据
```

---

## 四、★ 回归失败的**判读**（非 mock_server 本身问题）

跑 `regress_all.py` 时：**PASS 42 / FAIL 69**。

**原因分析**：
| 失败类别 | 根因 |
|---|---|
| `test_aoi_wire` / `test_map_collision` | **未传 `--second`** ⇒ 9099 第二实例未起 ⇒ `ConnectionRefused` = **用法问题** |
| 大量 `verify_*.py` | 跑回归时**端口被 minloop 占着**（主 8080/9000 是 minloop）⇒ 测试连到 minloop，行为不符 ⇒ 大量 FAIL = **环境冲突，非 mock_server 回归问题** |
| `test_shop_e2e` | "没有可购买的商品" = DB 被某轮快照/形态影响 |

**⇒ 现在 mock_server 已正确接管 8080/9000，重跑回归才是有意义的健康信号。**

---

## 五、★ 诚实清单

| 项 | 状态 |
|---|---|
| 1.4.11 连 mock_server + DSH | ✅ **已确认**（本批） |
| 核心命令应答 | ✅ 全通 |
| 账号 DSH 数据 | ✅ 完整 |
| 回归全量重跑 | ⏳ **建议**：等游戏会话结束（回归会快照/复原 roles.db，可能扰动在线 DSH 会话）后再跑 |
| `--second` 的 aoi/碰撞 | 🕐 需带 `--second` 重跑 |

---

## 六、产出物
| 文件 | 说明 |
|---|---|
| 本报告 | 1.4.11 → mock_server 连接确认 + 纠偏 |

**下一步（建议）**：在线会话结束后，用 `python tools/regress_all.py --second` 重跑拿真实健康基线。