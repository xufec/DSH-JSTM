# 1.4.9 角色移动协议（movement protocol）

> 目标 APK：`anzbao/jstm.apk`（1.4.9 / `com.shiyue.dldl.ewan.qihoo`）
> 方法：LuaJIT 字节码逐指令反汇编 + 实机抓包。**所有字段顺序来自客户端自身定义，不是猜的。**

---

## 一、结论：移动是"目标坐标"式，不是"方向"式

```
客户端 → 服务端：CS_10204 { x:uint16, y:uint16 }        ← 目标坐标
服务端 → 客户端：SC_10204 { rid:uint32, srv_id:string, x:uint16, y:uint16 }
瞬移同理：CS_10205 / SC_10205（结构完全相同）
```

**没有 dir 字段。** 方向由客户端根据"当前位置 → 目标位置"自行推导，服务端只需回权威坐标。

---

## 二、客户端侧代码（出处）

`assets/src/game/scene/scene_controller.luac` 的类表（proto[46]，`FNEW+TSETS` 映射）：

| 方法 | proto | 作用 |
|---|---|---|
| `move` | **proto[37]** | 发送 `CS_10204{x,y}`（玩家点地图/摇杆时调用） |
| `request10201` | **proto[36]** | 发送 `CSMapGird_10201`（请求整张图块，见下） |
| `on10204` | **proto[14]** | 收 `SC_10204` 后的处理 |
| `on10205` | proto[?] | 收 `SC_10205`（瞬移）后的处理 |

注册表（`scene_controller.luac proto[7]`，`RegisterProtocal`）：

```lua
RegisterProtocal(10200, 'on10200')   -- 通知角色进入场景
RegisterProtocal(10201, 'on10201')   -- 场景图块信息
RegisterProtocal(10202, 'on10202')   -- 附近有角色进入场景
RegisterProtocal(10203, 'on10203')   -- 附近有角色离开场景
RegisterProtocal(10204, 'on10204')   -- 角色移动
RegisterProtocal(10205, 'on10205')   -- 角色瞬移
RegisterProtocal(10206, 'on10206')   -- 传送到指定场景
...
```

### `on10204` 的反汇编（proto[14]，8 条字节码）

```lua
function on10204(self, resp)
  if resp then
    self.model:syncRoles(resp)      -- ★ 把服务端回的 rid/srv_id/x/y 同步到本地模型
  end
end
```

⇒ **服务端必须回 `SC_10204{rid, srv_id, x, y}`**，客户端才会把角色挪到新坐标。

### 一个重要修正

`scene_controller.request10201`（proto[36]）会**主动发送 `CSMapGird_10201`**：

```lua
function request10201(self)
  local proto = ProtocalRulesMgr:getInstance():GetPrototype(10201)
  self:SendProtocal(proto)
end
```

所以 **10201 不是"只由服务端推"** —— 客户端也会请求它。
服务端两处都要应答（客户端请求时、以及进场景主动推时），内容一致。

---

## 三、服务端实现（`server/mock_server.py`）

```python
if cmd in (10204, 10205):
    x, y = struct.unpack_from('>HH', body, 0)      # 客户端发来的目标坐标
    rid, srv_id = role['rid'], role['srv_id']
    save_role_pos(rid, x, y)                        # ★ 落盘持久化
    out = w_u32(rid) + w_str(srv_id) + w_u16(x) + w_u16(y)
    send(pack_frame(cmd, out))                      # 回权威坐标
```

用"回显同一坐标"作为权威值——对单人测试服足够；
将来接入寻路/校验时，这里改成返回服务端算出的合法落点即可，**协议不变**。

---

## 四、配套的两条消息（同样来自客户端定义）

| 命令 | 方向 | 结构 |
|---|---|---|
| `SCMapRole_10202` | S→C | `roles:table(rid,srv_id,name,lev,career,vip_lev,sex,status,mspd,x,y,dir,hidden,cur_title,ntm_title,marry_state,spouse_name,buff_bids,misc_*,animate_res)` |
| `SCRoleLeave_10203` | S→C | `role_ids:table(rid:uint32, srv_id:string), bid:uint32` |

「附近有角色进入/离开」用这两条广播；单人测试服暂时不需要。

---

## 五、待验证 / 待补

1. **实机验证移动**（阶段 4 的 A–F 六种情形）—— 需要在真实点击/摇杆下驱动，
   当前联调脚本只推进到"进入地图"，尚未模拟移动操作。
   可用的客观判据：`RoleCtrl:getInstance():getSelfRoleVo()` 的 `x`/`y`
   （探针已有 `voVals` 上报）＋ 服务端 `state/role_<rid>.json` 的落盘值。
2. `SC_10204` 是否还需要带 `dir`/`speed`（客户端 1.4.9 的定义里没有，
   但模型可能有默认值）—— 若移动后朝向不对，再回来查 `syncRoles` 的实现。
3. `mspd`（移动速度）在 `10201` 的角色表里下发，目前给 100；若移动速度异常，
   先调这个字段而不是改协议。
