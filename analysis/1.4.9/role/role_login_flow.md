# 角色登录流程（role login flow）—— 1.4.9

> 依据：`denglu_ctrl.luac` / `scene_controller.luac` / `role_ctrl.luac` 反汇编 + 实机 TCP 日志。
> 命令号与字段均来自 1.4.9 自身定义，**未使用 1.4.11 的任何字段**。

---

## 一、时序（实测）

```
① 1110  帐号登录
     请求：args:table(key,val) 10 项（account/timestamp/enter_srv_id/platform/device_id/
           gettui_cid/idfa/token/channelId/sign）
     应答：code:u8, msg:string, roles:table(…), least_career:u8
     ⚠ code 必须 == TRUE(1)（common_define proto[7] @0-1：TRUE=1；否则弹空白框）

② 10102 登录指定角色  /  10103 角色重连
     请求：rid:u32, srv_id:string
     应答：code, msg, timestamp:u32, world_lev:u16

③ 10300 客户端初始化完毕（仅 C→S 通知，无 SC）
     ⇒ 服务端收到后：补推 10200（让 sceneStart 重跑 createMap）+ 推 12400

④ 10200 通知角色进入场景（**S→C 主动推**）
     应答体：code, msg, bid:u32, line_id:u8, x:u16, y:u16, dir:u8
     ★ 必须在客户端"资源就绪"后推第二次，否则 createMap 半途而废、
       model:isLoadState() 停在 false、move() 被门禁挡住

⑤ 10201 场景图块信息（双向）
     应答体：roles/npcs/mons/elems 四张表
     roles 元素含 rid/srv_id/name/lev/career/vip_lev/sex/status/mspd/x/y/dir/
     hidden/cur_title/ntm_title/marry_state/spouse_name/buff_bids/misc_*/animate_res

⑥ 10302 角色资产/经验
     应答体：lev:u16, exp:u32, gold:u32, gold_acc:u32

⑦ 10301 角色基础信息
     应答体：45+ 字段（见 role_protocol.md 2.1），含 skill_list:table(bid:u32)

⑧ 10621 角色技能/世界等级 → world_lev:u16, skill_list:table(bid:u32, exp:u32)
   10333 角色操作 ack       → code:u8, msg:string
   13340 角色个人信息/名片  → name/lev/career/sex/sign/guild_name/title/…
```

## 二、服务端侧的角色状态来源（Phase 4C）

```
config.json.role  ──┐
                    ├─► role_state(cfg)  ──►  build_10301 / 10302 下发
ROLE_DEFAULTS     ──┘        （默认值合并，保证字段齐全）

x/y  ──► 另有持久化：server/state/role_<rid>.json（收到 CS_10204 时落盘）
```

- `ROLE_DEFAULTS` 的每一项都对应 `SC_10301`/`SC_10302` 里真实存在的字段；
- 10301 与 10302 **共用同一份 `role_state()`**，避免两处数值不一致。

## 三、已实测的环节

| 环节 | 状态 |
|---|---|
| 1110 登录 | ✅ 已验证 |
| 10102 / 10103 角色登录/重连 | ✅ 已验证 |
| 10300 → 10200 补推 | ✅ 已验证（`isLoadState=true`） |
| 10200 / 10201 进场景 | ✅ 已验证（25 NPC、角色可见） |
| 10301 角色基础信息 | ✅ 已验证（109 字节，含 skill_list） |
| 10302 资产/经验 | ✅ 已验证（20 字节） |
| 10621 / 10333 / 13340 / 14901 / 10331 | ✅ 已验证（见 role_phase4b.md） |
| 角色数值在主界面显示 | ❌ 未显示（待 4D 开面板） |
