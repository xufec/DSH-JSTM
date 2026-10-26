# 活动列表真实数据接通报告（2026-09-19）

> 承接"协议定义逐级收敛"。本轮把 **10924 活动列表**从"空表（2 字节）"升级为**真实活动列表**（config_function.json 91 条功能/活动开放表）。

---

## 一、★ 客户端取证：`activity_ctrl.luac` 的处理逻辑

反汇编 `_tmp_cfg/activity_ctrl.luac` 得到 10924 应答的完整消费链：

```
proto#29  Activityhander10925 壳：遍历 resp.act_list，每条调 self.Activityhander10925(entry)
proto#30  ★ 单条处理器（决定性证据）：
    status   = entry.status
    int_args = entry.int_args
    roleVo   = RoleVo 相关 getInstance():getRoleVo()，nil 则 return
    lev      = roleVo.lev
    self:setActiData(entry.id, status, int_args)   ← 三元组直接存储（无重映射）
    self:showCommonAlert(entry)
    if status ~= nil then
        self:removeUnopenList(entry)
        self:removeBySceneAlert(entry)
        cfg = Function.Config[entry.id]            ← ★ id 索引 config_function 表！
        if cfg ~= nil then
            if cfg.is_open ~= 1 then return end    ← is_open=0 不显示
            if lev < cfg.open_lev then
                self:pushUnopenList(entry); return  ← 未开放（无副作用，pushUnopenList 只是 return self.view）
            end
        end
        if entry.id == 2 then ... setWeaponState(2) end
        if status ~= nil then self:iconHandler({name=..., ...}) end
    end
proto#43  getActivityItem(id)：self.view:getItem(id)  ← UI 按 id 取活动条目
proto#49  {501,502,503,504} 硬编码活动检查：要求 **status == 1** 才显示图标
```

**结论（不猜，逐条取证）：**
1. `act_list[].id` = **config_function 表的 id**（`Function.Config[entry.id]`），不是 config_act 的活动 key
2. `status` 必须 **== 1**（proto#49 对 501/502/503/504 检查 `status == 1` 才显示图标）
3. `int_args` 非空（空表会导致 daily_ctrl proto#31 nil 访问崩溃，上轮已取证）
4. `is_open=0` / `lev < open_lev` 的活动客户端会跳过（无害但不显示）⇒ 服务端只发有效条目

---

## 二、★ Dsc10924int_args 线序取证（修正 fields.json 的错误）

`cmd_resolve_109.luac` proto#19/#25（Dsc10924int_args / Dsc10922int_args 读取器）：

```
0  TGETS A=2 B=1 C=0 ; ['ReadFMT']
1  KSTR  A=3 D=1     ; 'H'            ← 先读 u16 计数
2  CALL  A=2 D=514
3  ISEQP A=2 D=0
4  JMP   A=3 ...
5  KSHORT A=3 D=1                     ← for i = 1, len do
...
9  TGETS A=7 B=1 C=0 ; ['ReadFMT']
10 KSTR  A=8 D=2     ; 'I'            ← 每元素读 u32！
11 CALL  A=7 D=514
12 GGET  A=8 D=3
13 TGETS A=8 B=8 C=4 ; ['insert']
16 TSETS A=7 B=10 C=6 ; ['val']       ← 每元素 {val: u32}
17 CALL  A=8 D=259                     ← insert({val=val})
18 FORL  A=3 ...
```

**⇒ `Dsc10924int_args = table(val:uint32)`（u32 数组）。**
⚠ `protocol/fields.json` 里标的 `uint16` 是错的（兄弟协议 10922/10923/10925 同为 u32）。

---

## 三、★ 数据源：`config_function.json`（91 条）

`tools/extract_config_table.py` 从 `config_function.luac` 提取，每条含：

```
{"description":"天降豪礼","module_flag":"tianjianghaoli","open_lev":20,
 "location":10,"show_tips":"功能没有开放","sort_id":..,"id":117,"is_open":1}
```

**分布：** 91 条 ｜ `is_open=1` 74 条 ｜ open_lev 1~93 ｜ 含客户端硬编码检查的 501/502/503/504

---

## 四、★ 实现（mock_server.py）

```
10924: CS（空）→ SC_10924{act_list:table(id:u16, status:u8, int_args:table(val:u32))}
```

1. `function_cfg()` 惰性加载（`../_tmp_cfg/config_function.json`，91 条）
2. 过滤：`is_open==1` 且 `open_lev <= role_state(lev)`
3. 每条：`id=功能id`、`status=1`、`int_args=[当前时间戳]`（1 个 u32）
4. 排序：`sort_id` 优先（贴近客户端面板顺序）
5. 从 `_GENERIC_DEFAULT_CMDS` 移出 10924（防通用空表分支抢先）

---

## 五、★ 验证

### 静态逐字节校验（verify_10924.py）
```
== 10924 活动列表（模拟等级 1）==  14 条活动
包体 128 字节，解析消耗 128 字节        ← 字节流精确消耗
活动 id 列表: [11, 13, 16, 19, 20, 27, 44, 107, 501, 1002, 2000, 14000, 25000, 27000]
结果: PASS
```

### 端到端（test_11215_10800.py，登录角色 lev=150 → 74 条全开）
```
>> 10924 (活动列表) -> << 10924 应答 668 字节
   首表元素数 = 74
   #0 id=3   status=1 int_args=1 [1789753546]   ← 答题
   #1 id=5   status=1 int_args=1 [1789753546]
   ...（74 条全部 status=1、int_args 非空、id 命中 config_function）
结果: PASS
```

### 回归（无破坏）
```
11215 伙伴列表  53 个 ✓
10800 邮件列表  1 封  ✓
_finalreg 24 个核心命令 24 通 / 0 失败 ✓
服务端日志：function config loaded: 91 条，10924 无异常 ✓
```

---

## 六、★ 遗留（诚实声明）

| 项 | 状态 |
|---|---|
| `int_args` 具体语义（时间戳/次数/参数数组） | 未逐活动取证，统一用当前时间戳（活动"进行中"语义，客户端不崩溃） |
| `status` 各取值含义（1/2/3） | 未取证，只发 1（客户端唯一确认可用值） |
| 活动**详情**（10925 应答） | 仍为空表（10923/10925 同族，下轮按需对接） |
| `config_act.json` 219 个活动 key 与 `config_function.id` 的映射 | 已提取未接通（`getActivityItem` 走 UI view，服务端无需关心） |
