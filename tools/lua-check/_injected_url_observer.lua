---- DSH url observer ----
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
-- =====================================================================
-- DSH 三区注入块（客户端侧）—— 追加到 assets/src/config.luac 末尾
--
-- 目标：删去渠道登录流程之后，**保留客户端的「账号 + 区服」选择**，
--       并把区服列表固定为**三个区**（不依赖服务端下发）。
--
-- 为什么在这里改而不是改服务端：
--   选区链路由客户端自己消费（denglu_mgr.luac 逐指令已确认）：
--     DengluCtrl.loginPlatformResult → DengluMgr:requestDefaultServerList(...)
--       → HTTP POST get_servers_url(...)
--       → DengluMgr.managerDefualtServerListByJsonObj(resp, acc, platform)   ← 默认服
--     或 DengluMgr:getServerData(...)
--       → DengluMgr.managerServerListByJsonObj(resp, acc, platform)          ← 完整列表
--   两个入口都读 resp.data.server_list / resp.data.default_zone。
--   本块在 DengluMgr 出现后包住这两个入口，把 resp 换成我们自己的三区载荷，
--   于是**无论服务端回什么**，选区面板恒为三区（离线也能选）。
--
--   顺带修掉一个实测存在的崩溃点：
--     managerDefualtServerListByJsonObj 读 default_zone 时按**表**消费
--     （var_55_1.name / .srv_id / .platform .. "_" .. .zone_id），
--     而服务端历史下发的是字符串 "1" ⇒ `nil .. "_"` 抛错 ⇒ 选区一直不稳。
--     本块的 default_zone 是**同时具备原始键与归一化键**的表，两条消费路径都安全。
--
-- 三个区（名称自拟）：唐门一区 / 昊天二区 / 史莱克三区
--   ⚠ 三区共用同一个游戏服进程（HOST:PORT），即"同一个世界，三个入口"；
--      角色仍是按账号存在同一份库里（服务端 roles.srv_id 恒为 '1'）。
--      要做到三区数据隔离，需要服务端按 srv_id 分库（本轮范围外）。
-- =====================================================================
pcall(function()
  if _G.__dsh_zones_started then return end
  _G.__dsh_zones_started = true

  -- ---- 改这里即可换服（模拟器访问宿主机回环 = 10.0.2.2；真机填 PC 局域网 IP）----
  local HOST = "10.0.2.2"     -- 游戏服 IP
  local PORT = 9000           -- 游戏服 TCP 端口
  local HTTP = HOST           -- 配置/网关 HTTP 主机
  local HPORT = 8080          -- 配置/网关 HTTP 端口
  local BASE = "http://" .. HTTP .. ":" .. HPORT
  local PLAT = _G.PLATFORM_NAME or "ewan"

  -- ---- 条目同时给"原始键"与"归一化键"：raw 供 server_list 迭代，归一化供 default_zone ----
  local function zone(id, name, isnew)
    return {
      -- 原始（JSON）键
      srv_id = id, name = name, ip = HOST, port = PORT,
      platform = PLAT, zone_id = id,
      main_platform = PLAT, main_zone_id = id, main_srv_id = PLAT .. "_" .. id,
      host = "", platform_flag = "",
      can_create_role = 1, maintain = 0, first_zone = 0,
      recomed = 0, isnew = isnew or 0, open_time = 0, begin_time = 0,
      -- 归一化键（default_zone 走 setCurSrv 时用）
      srv_name = name, isClose = false, isNew = (isnew == 1), isTry = false,
      role_count = 0, role_logintime = 0,
    }
  end

  local ZONES = {
    zone("1", "唐门一区", 1),
    zone("2", "昊天二区", 0),
    zone("3", "史莱克三区", 0),
  }

  local function payload()
    return { code = 0, msg = "ok",
             data = { server_list = ZONES, default_zone = ZONES[1] } }
  end

  -- ---- 包住两个列表消费入口（DengluMgr 一出现就装）----
  local function install()
    if _G.__dsh_zones_ready then return true end
    local M = _G.DengluMgr
    if type(M) ~= "table" then return false end
    local a, b = M.managerServerListByJsonObj, M.managerDefualtServerListByJsonObj
    if type(a) ~= "function" or type(b) ~= "function" then return false end
    M.managerServerListByJsonObj = function(self, obj, acc, plat)
      return a(self, payload(), acc, plat)
    end
    M.managerDefualtServerListByJsonObj = function(self, obj, acc, plat)
      return b(self, payload(), acc, plat)
    end
    _G.__dsh_zones_ready = true
    pcall(function() print("[DSH_ZONES] installed: 3 zones") end)
    return true
  end

  -- 安装路径 ①：拦截 _G 上的 DengluMgr 赋值（模块加载那一刻即装好）
  pcall(function()
    local mt = getmetatable(_G) or {}
    if mt.__dsh_zone_newindex then setmetatable(_G, mt) return end
    local prev = mt.__newindex
    setmetatable(_G, {
      __index = mt.__index,
      __newindex = function(t, k, v)
        if prev then pcall(prev, t, k, v) end
        rawset(t, k, v)
        if k == "DengluMgr" then pcall(install) end
      end,
    })
  end)

  -- 安装路径 ②：调度器轮询兜底（__newindex 未触发时）
  pcall(function()
    local sch = cc.Director:getInstance():getScheduler()
    if not sch then return end
    local ticks, entry = 0, nil
    local function step()
      ticks = ticks + 1
      if install() or ticks > 600 then
        if entry then pcall(function() sch:unscheduleScriptEntry(entry) end) end
      end
    end
    entry = sch:scheduleScriptFunc(step, 0.2, false)
  end)

  -- ---- 顺手补齐两个必须是【函数】的全局（注入块里写成了字符串会抛
  --      "attempt to call global 'get_servers_url' (a string value)"）----
  function get_servers_url(...) return BASE .. "/gateway/mobile/json" end
  function get_notice_url(...) return BASE .. "/notice.json" end
  URL_PATH = URL_PATH or { update = BASE .. "/update", voice = BASE .. "/voice",
                           register = BASE .. "/register", is_shenhe = false }
end)
