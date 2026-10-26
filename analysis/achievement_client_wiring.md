# 成就 CS 客户端闭环接线准备（2026-10-02）

## 1. 客户端请求入口（已确认）
- 命令：16400（CS{type:u8}），R48 已实现（mock_server L18044）。
- 真机曾发 450 次；客户端打开成就面板即发 CS_16400{type}。
- 无需新注册命令（旧链已覆盖）。

## 2. SC_16400 帧格式（已实现）
```
SC_16400 {
    type: u8,
    chengjiu: T{ bid:u32, val:u16, time:u32 },      // 有进度的成就
    chengjiu_has: T{ bid:u32, time_out:u32, state:u8 },  // 当前留空
    chengjiu_rate: T{ bid:u32, rate:u8 }            // 进度%（封顶100）
}
```
- chengjiu/chengjiu_rate 已从 chengjiu_progress + _chengjiu.json 342 条填充。
- chengjiu_has 留空（w_u16(0)）——state 语义待证，不猜。

## 3. state 语义（UNKNOWN 挂起）
- state:u8 候选 0=未达成/1=可领/2=已领，但无配置/luac/真服真值。
- 取证通道已试：frida(host 无模块+MuMu ARM hook 不可靠)、logcat(cocos 不走标准 tag)、UI(坐标盲操受限)。
- 后续：用户协助打开成就面板截图，或真服恢复后抓包。

## 4. GM 闭环（已就绪，并行层）
- server/achievement/service.py：list_all/progress/mark_done/claim。
- 状态机：0 未达成 / 1 已达成未领 / 2 已领（dungeon_progress KV ptype=ach）。
- GM 端点：/DSH_ADMIN/ach_list|ach_progress|ach_done?bid|ach_claim?bid。
- 领取 grant(ref=ach:<bid>:<rid>) 幂等。

## 5. 接线计划（state 语义确认后）
1. 确认 state 0/1/2 映射。
2. achievement/service.py state 映射进 chengjiu_has T{bid,time_out=0,state}。
3. 16400 回包填 chengjiu_has（逐字对齐既有编码器）。
4. 领取 CS 命令（16401?）取证后接 claim。
