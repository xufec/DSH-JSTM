# 第二十一轮：路线 1 step A 取证 —— RoleVo 结构与属性向量路径

> 用户选定 A+C（RoleVo 结构 + 等级成长）。本轮做 step A 的静态取证。

---

## 一、已确证（CONFIRMED）

### RoleVo 结构（`game/role/role_vo.luac`）

**`proto[0]` (257 bc) = 构造函数**：把全部基础字段置 0
```
rid / srv_id / name / lev / exp / exp_max / exp_total_nextlev / is_vip / vip_lev /
sex / career / face_id / volume / store_volume / store_partner_volume /
attr_point / gsrv_id / ...
```

**`setRoleAttribute(attrId, val)` (proto[22], 39 bc)** = 单属性写入器：
```lua
@0-2  if self[attrId] == val then return end
@3-7  self:dispatchChangeAttr(attrId, val)     -- 通知变化（UI/战力刷新）
@8    self[attrId] = val                        -- ★ 按 attrId 存（AttrId2Key 转换）
@9-15 若 val 非 nil → self.move_speed = val / ? (DIVVN 除某系数)
    -- ★ 例：某些属性写 move_speed
```

**`proto[13]` (230 bc) = `setRole` 序列化器**：把响应对象的杂项字段逐项 `setRoleAttribute`
```
teamId / teamPos / teamSrvId / gid / gsrv_id / gname / position / sign /
god_team_id / convoy_mon_bid / attrDrugNum / mount_camp / isXiuLuoScene /
capacity / race_camp / flyUp_lev / top_effect ...
**（全部是组队/坐骑/副本 misc 字段，不是 atk_s/hp_max 属性向量）**
```

---

## 二、★ 决定性结论

**属性向量（atk_s/hp_max/dodge...）不在 `setRole` 里** —— 它由**另一条独立路径**传入。

`setRoleAttribute` 的存在证明客户端是**按属性键逐个写入**的，但**哪条协议**带 `atk_s` 等，
本轮**未定位到**（`proto[13]` 全是 misc 字段，属性向量的 CMD 在别处）。

---

## 三、诚实状态

| step | 状态 |
|---|---|
| **A** RoleVo 结构（proto[0]）+ setRoleAttribute 语义 | ✅ **大部分完成** |
| **A** 属性向量**下发 CMD** | ⚠️ **未定位**（它是关键：不知道服务端往哪条消息塞 attrs） |
| **C** 等级成长公式 | ❌ **未开始**（无单表，需逆客户端计算） |

**⇒ 我**没有**完成"让战力非零"。** 卡在"属性向量由哪条协议下发"。

---

## 四、下一步（二选一，请裁决）

| 选项 | 内容 | 判断 |
|---|---|---|
| **① 继续挖** | 逆"属性向量 CMD"（查 `dispatchChangeAttr` / 角色属性消息的接收者） | 需**一个专注轮次**，才能定位 + 实现服务端下发 attrs |
| **② 切换** | 先修**幸运转盘 / 日常面板 / 剧情**（协议问题，更快见效） | 若你想近期"能玩"，更快 |

**我尊重你走 1 的决定，但必须如实说：step A 的"C 卡点在属性向量 CMD"，还没到能实现服务端下发的地步。**
**要继续 ①，还是先切 ② 处理那几项快活？**