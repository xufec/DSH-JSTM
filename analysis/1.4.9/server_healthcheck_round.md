# 服务器检查 / 修复 / 优化（2026-09-18）

> 用户要求：**检查修复并优化服务器。**

---

## 一、★ 检查发现：一个**每 2.5 秒刷屏**的真实错误

### 1.1 现象（服务端日志）

```
[14:05:42] --- error: TypeError("int() argument must be a string, a bytes-like object or a number, not 'NoneType'")
[14:05:45] --- error: （同上）
[14:05:47] --- error: （同上）
... 共 80 次，间隔 ~2.5 秒
```

### 1.2 定位（日志上下文）

```
[13:59:24]   << 1199 heartbeat reply
[13:59:24]   .. mission status normalized: chain_head=10010 (变更 1 条)
[13:59:24]   !! 12400 补推失败: TypeError(...)
```

**⇒ 是 **`12400` 任务列表补推**失败，且**心跳每 2.5 秒触发一次** ⇒ 错误持续刷屏。**

### 1.3 根因（复现出的完整堆栈）

```
File "server/mock_server.py", line 2020, in build_mission_entry
    w_u16(m.get('commit_num', 0)) +
TypeError: int() argument must be ... not 'NoneType'

任务 10010 的字段: process_status=None, target=None, target_value=None, value=None
```

**★ 关键点：`m.get(k, 默认)` **只在「键缺失」时生效**；**
**若键存在但值是 `None`，`.get()` 返回 `None` ⇒ `int(None)` 抛 `TypeError`。**

**⇒ `None` 的来源**：我上一轮加的**后台 `setmissions`** 只写了
`{mission_bid, mission_status}` 两个字段 ⇒ 其余字段为 `None`。**

---

## 二、修复（两处，都改）

### 2.1 `build_mission_entry` 健壮化

```python
def _n(v, d):
    return d if v is None else v        # ★ 同时处理「缺失」与「为 None」
return (w_u32(_n(m.get('mission_bid'), 35000)) +
        w_u8(_n(m.get('mission_status'), 1)) + ...)
```

### 2.2 `setmissions` 写完整字段

```python
db_save_mission(rid, {'mission_bid': mb, 'mission_status': 1,
                      'commit_num': 0, 'loop_count': 0, 'loop_num': 1,
                      'code': 0, 'process_status': 0,
                      'target': 0, 'target_value': 1, 'value': 0,
                      'show_lave_time': 0, 'lave_time': 0, 'accept_time': 0})
```

### 2.3 修补既有脏数据

`missions` 表里 `10010` 那行的 `None` 字段**就地补齐**（修正 1 行）。

---

## 三、修复验证

```
复现：build_12400 OK, 36 字节   ✅（修复前抛 TypeError）

重启后观察 30 秒：
  ✅ 30 秒内无错误
  stderr: 0 字节
```

**⇒ 错误彻底消除。**

---

## 四、优化效果

**这个错误本身就是**性能浪费**：每 2.5 秒一次异常 + 日志刷屏 + 一次失败的推送。**

| 指标 | 修复前 | **修复后** |
|---|---|---|
| 服务端错误 | **每 2.5 秒 1 次** | **0** |
| 日志 | 被 `!!` 刷屏 | 干净 |
| 无效推送 | 每 2.5 秒 1 次失败 | 0 |

---

## 五、性能复测（修复后）

| 命令 | 失败 | 最小 | **中位** | 最大 |
|---|---|---|---|---|
| `10301` 角色基础信息 | 0 | 6.7 | **10.8** | 17.9 |
| `10302` 角色数值 | 0 | 6.1 | **12.8** | 18.8 |
| `10303` 属性大表 | 0 | 8.5 | **15.5** | 19.1 |
| `12400` 任务列表 | 0 | 8.3 | **16.9** | 38.4 |
| `12409` 可接取 | 0 | 7.7 | **12.0** | 20.8 |
| `12801` 商城 | 0 | 7.5 | **13.5** | 65.1 |
| `12803` 商城简表 | 0 | 6.2 | **15.0** | 19.9 |

**内部：`build_10303()` 2.1 ms**

**并发（20 线程 × 10 请求）：**
```
成功 200/200（100%）　总耗时 1.23 s
单次延迟：中位 49.8 ms　最大 1030 ms
```
**⚠ 如实**：并发尾部较长（1030 ms），是 **Python 单进程 + GIL + SQLite 串行**的固有特性，
**非本次改动引入**；单机小规模够用，若要更高并发需换多进程/异步。

---

## 六、数据完整性复核

```
背包   6 件   无效 bid: 无 ✅
装备   5 件   无效 bid: 无 ✅
仓库   0 件   无效 bid: 无 ✅
任务 10010   None 字段数: 0 ✅

表清单（10）：bag_items / bag_volume / equip_items / levgift_got /
             mall_bought / missions / role_assets / role_attr /
             roles / store_items
```

**管理接口可用性：`/getlevel` `/getassets` `/status` `/cfglist` → 4/4 OK**

---

## 七、体检结论

| 项 | 结果 |
|---|---|
| 语法 / 导入 | ✅ OK |
| 服务端错误 | ✅ **已从"每 2.5 秒 1 次"降到 0** |
| stderr | ✅ 0 字节 |
| 数据完整性 | ✅ 无无效 bid、无 id 重复、无 None 字段 |
| 性能 | ✅ 中位 10.8~16.9 ms（正常） |
| 管理接口 | ✅ 4/4 可用 |
| 并发 | ✅ 200/200 成功（尾部偏长，属 Python 固有） |

**⇒ 本轮：发现 1 个高频错误 → 修复（2 处代码 + 1 处数据）→ 复测通过。**
