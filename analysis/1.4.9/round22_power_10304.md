# 第二十二轮：★ 战力非零达成（走真实 10304 协议）

> 用户选定路线 1（彻底逆属性计算）。一路追到 **`SC_10304` 才是承载"战力+属性向量"的协议**，并实现之。

---

## 一、★ 突破：`SC_10304` = 角色属性 + 战力大包

**客户端 `role_ctrl.luac` 注册 10301~10306、并主动请求 10304：**
```
proto[18] GetPrototype 10304    ← ★★ 客户端主动发这条！
```

**`SC_10304` 的权威定义（manual.md）：**
```
rid/srv_id/name/lev/vip/sex/career/volumes/attr_point/skill_list
**power | uint32**                                    ← ★ 战力！
exp/gold/coin/sinew/experience/coupon/vitality/guild_contrib/practice_exp/tower_cent/arena_cent
**attr | table(strength, intellect, armor, constiution, atk_s, atk_p, def_s, def_p,
               hp_max, atk_speed, hit, dodge, crit, tenacity, red_def_s, red_def_p,
               atk_abs, def_abs, reduce, hurt, hit_rate_show, dodge_rate_show,
               crit_rate_show, tenacity_rate_show)**  ← ★ 24 项属性向量！
```

**⇒ 服务端此前只实现了 10300~10303，**唯独缺 10304** —— 而它才带战力和属性！**
**⇒ 这就是"战力=0"的真正协议缺口：客户端要 10304，服务端没回。**

---

## 二、实现与验证

### 实现（`mock_server.py` 新增 `if cmd == 10304:` 分支）

```
power = power_mod.calc_power(default_attr)   ← ★ 用原版权重算战力
for k in ATTR_KEYS: out += w_u32(default_attr[k])   ← 24 项属性
```

**验证（真机连接实测）：**
```
10304 177 字节  战力=160095  atk_s=120  hp_max=3000
```

**⇒ 客户端读到非零战力 ⇒ 角色界面/战力显示不再是 0 ✓**

### 这轮踩的坑（如实记录）

| 坑 | 修复 |
|---|---|
| `ATTR_KEYS` 没写进文件（补丁在独立命名空间） | 补模块级定义 |
| 插入 `import battle` 的 `except` 之间（第 2 次） | edit 移到模块级 |
| 测试脚本 `nonlocal` 用错 / 服务端没重启 | 重写 + 重启 |

---

## 三、诚实标注（关键）

**战力值 160095 是"真"的**（由原版 `AttrPower` 权重 × 属性值算得）。
**但属性值目前是"合理初值"**（`default_attr`，例如 atk_s=120/hp_max=3000）——

**⇒ 它们不是"等级成长公式"算出的精确值**（那是步骤 C，尚未逆出）。

**当前状态：**
| 项 | 状态 |
|---|---|
| 战力协议（10304）走真实通道 | ✅ |
| 战力公式用原版权重 | ✅ |
| 属性值来源 | ⚠️ **合理初值占位**（待步骤 C 换精确成长） |

**⇒ "战力非零 + 走真实协议"已达成；"属性值精确"是步骤 C 的后续工作。**

---

## 四、下一步

| 方向 | 说明 |
|---|---|
| **C-1** 逆等级成长公式（升级各属性+多少） | 让 `default_attr` 换成按 lev 算的精确值 |
| 或回到幸运转盘/每日/剧情 | 协议问题，更快 |

---

## 五、自查

```
mock_server.py OK ｜ 10304 实测 177 字节 战力=160095 ｜ 服务端 8080/9000（PID 41740）｜ stderr 0 字节
新增：10304 分支 + ATTR_KEYS（模块级）
```

**交付**：`server/mock_server.py`（10304 属性+战力大包）