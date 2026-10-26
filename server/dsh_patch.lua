-- ===========================================================================
-- DSH hot patch v4
--   引导：config.luac 注入块末尾用 io.open 读 <writable>/dsh_patch.lua
--   推送：python tools/push_patch.py server/dsh_patch.lua
-- ===========================================================================

print("[DSH_PATCH] v4 loaded")

-- ---------------------------------------------------------------------------
-- 0) 修自伤性无限递归（print → __dsh_rep → __dsh_srv_tick → pump → rep
--    → rawrep → print → …）
-- ---------------------------------------------------------------------------
local function guard_global(name)
    local f = _G[name]
    if type(f) ~= 'function' then return false end
    _G[name] = function(...)
        if _G.__dsh_in_tick then return end
        _G.__dsh_in_tick = true
        local a, b, c, d = f(...)
        _G.__dsh_in_tick = false
        return a, b, c, d
    end
    return true
end
if not _G.__dsh_tick_guarded then
    _G.__dsh_tick_guarded = true
    print("[DSH_PATCH] tick guard: tick=" .. tostring(guard_global('__dsh_srv_tick')) ..
          " pump=" .. tostring(guard_global('__dsh_srv_pump')))
end

-- ---------------------------------------------------------------------------
-- 1) 推进原语
-- ---------------------------------------------------------------------------
local function pump_once()
    local M = _G.__DSH_SERVER
    if not M or not M.pump then return end
    if _G.__dsh_in_tick then return end
    _G.__dsh_in_tick = true
    pcall(M.pump)
    _G.__dsh_in_tick = false
end

local function drive_login()
    local M = _G.__DSH_SERVER
    if not M then return end
    if _G.__dsh_in_tick then return end
    _G.__dsh_in_tick = true
    if not _G.__dsh_logged_in then
        pcall(M.begin_login)
        pcall(M.try_login)
    end
    if not _G.__dsh_srv_list_req then pcall(M.request_server_list) end
    pcall(M.try_connect_game_server)
    _G.__dsh_in_tick = false
end

-- 自链式心跳（只挂一个下一次动作；RepeatForever 会让动作数指数增长）
local function start_beat_on(node)
    if _G.__dsh_beat_on or not node then return end
    _G.__dsh_beat_on = true
    local n = 0
    local function beat()
        n = n + 1
        _G.__dsh_beats = n
        pump_once()
        if n == 1 or n % 100 == 0 then
            print(string.format(
                "[DSH_BEAT] n=%d GameNet=%s DengluMgr=%s PlatForm=%s logged=%s srvreq=%s gameconns=%s",
                n, type(_G.GameNet), type(_G.DengluMgr), type(_G.DengluPlatForm),
                tostring(_G.__dsh_logged_in), tostring(_G.__dsh_srv_list_req),
                tostring(_G.__dsh_game_conns)))
        end
        pcall(function()
            node:runAction(cc.Sequence:create(
                cc.DelayTime:create(0.1),
                cc.CallFunc:create(function() pcall(beat) end)))
        end)
    end
    pcall(beat)
    print("[DSH_DRV] self-chaining beat started on " ..
          tostring(node) .. " beat_on=true")
end

-- 把常驻节点挂到一个"肯定在场景里"的节点下面
local function hook_onto(node, host, how)
    if not (node and host) then return false end
    local ok = pcall(function() host:addChild(node) end)
    _G.__dsh_node_attached = true
    print("[DSH_DRV] attach via " .. how .. " ok=" .. tostring(ok))
    return ok
end

-- ---------------------------------------------------------------------------
-- 2) ★ 关键挂载点：包装 update_finish
--    update_finish (file_update proto#36) 里会
--       video_finish = video_player(self, proto#32)
--       video_finish:scheduleUpdateWithPriorityLua(self, proto#35, 0)   -- 逐帧加载
--    也就是说 video_finish 这个全局节点**一定在运行中的场景里**。
--    我们在它返回后把常驻节点 addChild 上去，自链心跳就随帧跑起来了。
-- ---------------------------------------------------------------------------
if not _G.__dsh_uf_hooked then
    _G.__dsh_uf_hooked = true

    local function install_uf_hook()
        if _G.__dsh_uf_wrapped then return end
        local f = _G.update_finish
        if type(f) ~= 'function' then return end
        _G.__dsh_uf_wrapped = true
        _G.update_finish = function(self, ...)
            print("[DSH_TRACE] update_finish ENTER")
            local a, b, c, d = f(self, ...)
            pcall(function()
                local vf = _G.video_finish
                print("[DSH_TRACE] update_finish EXIT video_finish=" .. type(vf))
                if vf then
                    hook_onto(_G.__dsh_srv_node, vf, 'video_finish')
                    start_beat_on(_G.__dsh_srv_node)
                end
            end)
            return a, b, c, d
        end
        print("[DSH_TRACE] update_finish wrapped")
    end

    -- update_finish 由 require('file_update') 注册，所以等那一刻
    local orig = _G.require
    if type(orig) == 'function' then
        _G.require = function(name, ...)
            local r = orig(name, ...)
            if type(name) == 'string' and name:find('file_update', 1, true) then
                pcall(install_uf_hook)
                print("[DSH_TRACE] after require file_update: PlatForm=" ..
                      type(_G.DengluPlatForm) .. " Mgr=" .. type(_G.DengluMgr) ..
                      " GameNet=" .. type(_G.GameNet) .. " vf=" .. type(_G.video_finish))
            end
            return r
        end
    end
end

-- ---------------------------------------------------------------------------
-- 3) 场景切换时重新挂（replaceScene 后旧节点会被移除，动作被 pause）
-- ---------------------------------------------------------------------------
if not _G.__dsh_scene_hooks then
    _G.__dsh_scene_hooks = true
    pcall(function()
        local D = cc.Director
        for _, m in ipairs({ 'runWithScene', 'replaceScene', 'pushScene' }) do
            local f = D[m]
            if type(f) == 'function' then
                D[m] = function(self, scene, ...)
                    local r = f(self, scene, ...)
                    pcall(function()
                        print("[DSH_DRV] Director:" .. m)
                        if scene then
                            hook_onto(_G.__dsh_srv_node, scene, 'Director:' .. m)
                            start_beat_on(_G.__dsh_srv_node)
                        end
                    end)
                    return r
                end
            end
        end
        print("[DSH_DRV] Director scene hooks installed")
    end)
end

-- ---------------------------------------------------------------------------
-- 4) 通用 require 钩子：诊断计数 + 登录推进
-- ---------------------------------------------------------------------------
if not _G.__dsh_req_hook4 then
    _G.__dsh_req_hook4 = true
    local orig = _G.require
    if type(orig) == 'function' then
        local cnt = 0
        _G.require = function(name, ...)
            local r = orig(name, ...)
            cnt = cnt + 1
            _G.__dsh_req_count = cnt
            if cnt <= 6 then
                print("[DSH_REQIN] n=" .. cnt .. " name=" .. tostring(name))
            elseif cnt % 100 == 0 then
                print("[DSH_REQ] n=" .. cnt)
            end
            if not _G.__dsh_logged_in then pcall(drive_login) end
            return r
        end
        print("[DSH_R] require hook v4 installed")
    end
end
