-- ============================================================================
--  DSH 启动观测器（**默认非侵入版**）
-- ============================================================================
--  ※ 下面这行 ASCII 标记不要删：tools/verify_injected_lua.py 靠它定位本段
-- ---- DSH url observer ----
--
--  ⚠ 为什么改成"默认非侵入"（2026-10-14 实测结论）：
--    旧版默认包装 `cc.XMLHttpRequest:new` 与实例方法（open/send/registerScriptHandler）
--    + 挂网关合成器 + 钩 FileUtils，全部落在**启动热路径**上。
--    实测后果：注入后客户端在登录页 `error网络异常`、**一条业务 HTTP 都不发、也不连 9000**；
--    只保留 observer（去单机块）时虽恢复业务 HTTP，却**卡在 url_config 下载重试循环**。
--    与本项目旧文档第 8 节坑位 6 的结论一致：热路径挂探针会把加载卡死。
--    ⇒ 现在：重活全部关进 `_G.__DSH_OBS_INTRUSIVE`（默认 nil=关），只留
--       ① print 镜像（在注入块里，与本文件无关）
--       ② dsh_patch.lua 加载器（在注入块里）
--       ③ 本文件的**延迟探针**：45s 后才第一次跑，且只做只读 dump
--
--  探针开关：`_G.__DSH_ENABLE_TPROBE ~= false`（默认开；dsh_patch 里可置 false 关掉）
--  探针节拍：cc.Director 调度器（实测会触发，见 analysis/extraction/lua_injection_round2.md）
-- ============================================================================

pcall(function()
    if _G.__dsh_obs then return end
    _G.__dsh_obs = true

    local function obs(tag, s)
        pcall(function() print("[DSH_OBS] " .. tostring(tag) .. " " .. tostring(s)) end)
    end

    -- ------------------------------------------------------------------
    -- A) 只读探测：LuaJavaBridge 是否存在（一次性、极廉价）
    -- ------------------------------------------------------------------
    pcall(function()
        local lj = _G.LuaJavaBridge
        obs("luaj", "type=" .. type(lj) ..
            " callStatic=" .. type(lj and lj.callStaticMethod))
    end)

    -- ------------------------------------------------------------------
    -- B) 侵入式观测（**默认关闭**）：网关合成器 + XHR 包装 + FileUtils 钩
    --    需要时把 _G.__DSH_OBS_INTRUSIVE = true（仅单机/实验用）
    -- ------------------------------------------------------------------
    if _G.__DSH_OBS_INTRUSIVE then
        pcall(function()
            local X = cc and cc.XMLHttpRequest
            if not X or X.__dsh_new_orig then
                obs("xhr", "skipped")
                return
            end
            local o_new = X.new
            X.__dsh_new_orig = o_new
            X.new = function(self, ...)
                local req = o_new(self, ...)
                pcall(function()
                    local idx = getmetatable(req) and getmetatable(req).__index
                    if type(idx) ~= "table" or idx.__dsh_wrapped then return end
                    idx.__dsh_wrapped = true
                    local o_open, o_send = idx.open, idx.send
                    if type(o_open) == "function" then
                        idx.open = function(s2, m, u, ...)
                            s2.__dsh_url = tostring(u)
                            return o_open(s2, m, u, ...)
                        end
                    end
                    if type(o_send) == "function" then
                        idx.send = function(s2, ...)
                            local u = s2.__dsh_url
                            if type(u) == "string" and u:find("gateway/mobile", 1, true)
                               and _G.__DSH_SERVER and _G.__DSH_SERVER.server_list_json then
                                pcall(function()
                                    local body = _G.__DSH_SERVER.server_list_json()
                                    local h = s2.__dsh_handler
                                    if body and type(h) == "function" then
                                        pcall(h, { status = 200, readyState = 4,
                                                   response = body, responseText = body })
                                        return
                                    end
                                end)
                            end
                            return o_send(s2, ...)
                        end
                    end
                end)
                return req
            end
            obs("xhr", "intrusive wrapping ON")
        end)
    else
        obs("xhr", "intrusive wrapping OFF (default)")
    end

    -- ------------------------------------------------------------------
    -- C) 延迟探针：45s 后才启动；只做只读 dump，把结果以 XHR 报回 PC
    --    基址从全局 URL_PATH.update 推导（与 --host/--port 无关）
    -- ------------------------------------------------------------------
    pcall(function()
        local function base()
            local b = _G.__dsh_obs_base
            if b then return b end
            local u = _G.URL_PATH and _G.URL_PATH.update
            if type(u) == "string" then
                b = u:gsub("/update$", "")
                if b ~= u and #b > 0 then _G.__dsh_obs_base = b return b end
            end
            return nil
        end
        _G.__dsh_obs_rep = function(tag, s)
            pcall(function()
                local b = base()
                local X = cc and cc.XMLHttpRequest
                if not b or not X then return end
                local v = tostring(s):gsub("[^%w%._:/-]", "_")
                if #v > 150 then v = v:sub(1, 150) end
                local r = X:new()
                r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
                r:open("GET", b .. "/DSH_REPORT?tag=" .. tostring(tag) .. "&v=" .. v)
                r:send()
            end)
        end

        local elapsed = 0
        local fired = false
        local function tick_probe()
            elapsed = elapsed + 1
            if elapsed == 1 then obs("tprobe", "sched alive") end
            if fired then return end
            if _G.__DSH_ENABLE_TPROBE == false then return end
            if elapsed < 90 then return end          -- 45s（0.5s × 90）
            fired = true
            local rep = _G.__dsh_obs_rep
            local C = _G.Config
            rep("obs.dump", "t=" .. elapsed .. " Config=" .. type(C))
            if type(C) ~= "table" then return end
            local n = 0
            for _ in pairs(C) do n = n + 1 end
            rep("obs.cfg", "keys=" .. n ..
                " SXL=" .. type(C.SkillXiulianLev) ..
                " Huoli=" .. type(C.Huoli) ..
                " RiChang=" .. type(C.RiChang))
            -- 修炼表的结构摘要（8 个 id × 每 id 的等级数）
            pcall(function()
                local S = C.SkillXiulianLev
                if type(S) ~= "table" then return end
                local out = {}
                for k, v in pairs(S) do
                    local m = 0
                    if type(v) == "table" then for _ in pairs(v) do m = m + 1 end end
                    out[#out + 1] = tostring(k) .. ":" .. m
                end
                rep("obs.sxl", table.concat(out, ","))
            end)
            -- 全局单例是否存在
            for _, g in ipairs({ "GameData", "RoleVo", "DailyCtrl", "GameNet",
                                 "ProtocalRulesMgr" }) do
                rep("obs.g." .. g, type(_G[g]))
            end
        end

        -- ★★ 单变量实验：**不注册调度器**（旧文档警告过 config 阶段注册会干扰启动）。
        --    若去掉后客户端能正常进游戏 ⇒ 证实干扰源就是它，探针改为 print 驱动。
        _G.__dsh_obs_probe_fn = tick_probe
        obs("tprobe", "NOT registered (experiment: no scheduler)")
    end)

    obs("hook", "observer ready (non-intrusive default)")
end)
