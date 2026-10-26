# S1-B 精确 diff（vs `mock_server.py.bak_s1b_20261015` 与 partner/service.py）

## A. mock_server.py（unified diff，n=2）

```diff
--- mock_server.py.bak_s1b_20261015
+++ mock_server.py
@@ -9951,4 +9951,14 @@   （S1-A +5s 补推块，10303 推送之后）
                     log('tcp.log', '  << 10303 SC_10303 attr（S1 风暴收尾补推）(%d bytes)'
                         % len(_pk))
+                    # ★ S1-B：补推 10302（完整资产刷新，尾部带 diamond/rainbow_diamond）。
+                    #   根因：登录风暴只推 10301/10303/10305，从不推 10302；而 diamond
+                    #   字段在 10302 的 1.4.11 尾部（build_10302 L5446-5448）⇒ 客户端
+                    #   全程读不到 diamond ⇒ HUD 钻石停默认 0、商城余额校验失败。
+                    #   值取 role_state['diamond'] = roles.diamond 真实存储（当前=0，
+                    #   不伪造非零值）；CodeToAssets 无 diamond 标签，故只能走 10302 尾部。
+                    _pk2 = pack_frame(10302, build_10302(_st))
+                    self.request.sendall(_pk2)
+                    log('tcp.log', '  << 10302 SC_10302 资产刷新（S1-B 补 diamond=%s）(%d bytes)'
+                        % (_st.get('diamond', 0), len(_pk2)))
                     # 10306（attr 表 + mspd + power 小包；与 attribute.handler 同构）
                     _ad = role_attr_dict(self.cfg)
```

```diff
@@ -16180,13 +16190,36 @@   （10621 handler）
             return
         if cmd == 10621:
-            # CS_10621（空）→ SC_10621{world_lev:u16, skill_list:table(bid:u32, exp:u32)}
-            skills = self.cfg.get('skills', [])
-            out = w_u16(self.cfg.get('world_lev', 1)) + w_u16(len(skills))
-            for sk in skills:
-                out += w_u32(sk.get('bid', 1001)) + w_u32(sk.get('exp', 0))
+            # CS_10621 → SC_10621{world_lev:u16, skill_list:table(bid:u32, exp:u32)}
+            # ★ S1-B：skill_list 的 bid 必须落在客户端 Config.SkillXiulianLev 键空间内。
+            #   合法键 = cfg/config_skill_xiulian.json SkillXiulianLearn 的 8 条
+            #   （10101/10201/10301/10401/10501/10601/10701/10801）。
+            #   原 config.json skills=[10000/10001/10002/10822] 全不在该键空间。
+            #   exp 取角色真实 practice_exp=35（映射 10801），其余 7 项 DB 无数据源⇒0。
+            import json as _json, os as _os
+            _xl_bids = []
+            try:
+                with open(_os.path.join(runtime.HERE, 'cfg', 'config_skill_xiulian.json'),
+                          encoding='utf-8') as _f:
+                    _xl = _json.load(_f)
+                for _k in (_xl.get('SkillXiulianLearn') or {}).keys():
+                    _xl_bids.append(int(_k))
+            except Exception as _e:
+                log('tcp.log', '  !! 10621 xiulian cfg load failed: %r' % (_e,))
+            _xl_bids.sort()
+            _pe = int(role_state(self.cfg).get('practice_exp', 0) or
+                      self.cfg.get('practice_exp', 0) or 0)
+            out = w_u16(self.cfg.get('world_lev', 1)) + w_u16(len(_xl_bids))
+            for _b in _xl_bids:
+                out += w_u32(_b) + w_u32(_pe if _b == 10801 else 0)
             pkt = pack_frame(10621, out)
             self.request.sendall(pkt)
-            log('tcp.log', '  << 10621 SC_10621 world_lev=%d skill_list=%d (%d bytes)'
-                % (self.cfg.get('world_lev', 1), len(skills), len(pkt)))
+            log('tcp.log', '  << 10621 SC_10621 world_lev=%d skill_list=%d（xiulian 键空间 %s）(%d bytes)'
+                % (self.cfg.get('world_lev', 1), len(_xl_bids), _xl_bids, len(pkt)))
             return
         if cmd == 13340:
```

## B. partner/service.py（build_panel_11215 前缀修正）

```diff
@@ build_panel_11215, 原 L148-150
-    out = (w_u8(len(base) & 0xff) +        # volume：配置伙伴总数（容量）—— INFERENCE
-           w_u8(len(owned) & 0xff) +       # volume_open：已拥有数 —— INFERENCE
-           w_u16(len(base)))               # partner_bag 表计数
+    # ★ S1-B：本客户端 1.4.9（runtime.CUR_VER='1.4.9'），fields.json SC_11215 =
+    #   partner_list:table 直接以表计数(u16)开头，无 volume/volume_open 前缀。
+    #   旧码按 1.4.11 luac 补了 w_u8(volume)+w_u8(volume_open) 两字节前缀 ⇒ 1.4.9
+    #   客户端条目错位 2 字节 ⇒ LUA ERROR [11215]（经 CS_10999 上报）。帧长印证：
+    #   注释基线 2552 body=2+53×48，旧码发 2554（多 2 字节）。修复：去前缀，只发计数。
+    out = w_u16(len(base))               # partner_list 表计数（1.4.9 规格，无前缀）
```

## 字段证据来源
- 修炼 bid：`server/cfg/config_skill_xiulian.json` SkillXiulianLearn 键；`analysis/extraction/lua_injection_channel_round.md` §2.1
- diamond：`server/state/roles.db` roles.diamond=0；`build_10302` L5446-5448；`config_game_data.CodeToAssets`（无 diamond 标签）
- 11215 结构：`protocol/fields.json` SC_11215（partner_list:table）；帧长 2552 vs 2554
- 实机日志：`server/logs/tcp.log`（10302 S1-B 补推 128B；11215 2552B；零 10999）
