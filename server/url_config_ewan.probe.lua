-- =====================================================================
-- 《绝世唐门》本地配置服务器 —— 诊断/驱动探针版（方案 M 修正版）
--
-- 本文件解决的问题：之前"有时连上、有时连不上"。
-- 根因有两条，都已修正：
--   (1) **没有安装守卫**：客户端会多次重新请求并执行本配置，
--       于是同一个探针被装了 4~5 份，多个 tick 互相干扰。
--       → 现在用 `_G.__dsh_probe_installed` 守卫，只装一次。
--   (2) **net_manager 只在 restartNetManager 里创建**
--       （gamenet proto[29]：net_manager = CCNetManager:sharedNetManager()）。
--       不调它 → net_manager 为 nil → 永远连不上；
--       但调它又会重置调度，把**先建好的** tick 干掉。
--       → 正确顺序：先调 restartNetManager()，**之后**再创建驱动 tick。
--
-- 另外确认：`GameNet.Update` 是 gamenet.luac 里的局部函数，不在类表里，
-- 无法从 Lua 包装，所以驱动只能靠 Director 调度（本文件即如此）。
--
-- 上报走 cc.XMLHttpRequest → 服务端 /DSH_PROBE。
-- =====================================================================

local HOST = "127.0.0.1"
local PORT = 8080
local BASE = "http://" .. HOST .. ":" .. PORT

local function report(tag, v)
  pcall(function()
    if not (cc and cc.XMLHttpRequest) then return end
    local r = cc.XMLHttpRequest:new()
    r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
    local s = tostring(v)
    if #s > 200 then s = s:sub(1, 200) end
    r:open("GET", BASE .. "/DSH_PROBE?t=" .. tostring(tag) ..
           "&v=" .. s:gsub("[^%w%._:/-]", "_"))
    r:send()
  end)
end

-- ★ 安装守卫：客户端可能多次执行本配置，绝不能重复安装
if _G.__dsh_probe_installed then
  report('probe', 'already installed, skip')
  return
end
_G.__dsh_probe_installed = true

report('load_enter', 'ok')
report('load_nowver', tostring(rawget(_G, 'NOW_VERSION')))
pcall(function()
  local ud = cc.UserDefault:getInstance()
  ud:setStringForKey('local_srv_id', '1')
  report('setSrv', 'local_srv_id=' .. tostring(ud:getStringForKey('local_srv_id')))
end)

pcall(function()
  local sch
  pcall(function() sch = cc.Director:getInstance():getScheduler() end)
  if not sch then report('probe', 'no scheduler'); return end

  local S = { ticks = 0, hooksDone = false, neted = false, asyncDone = false,
              reloginDone = false }
  local driverEntry, installerEntry

  local function installHooks()
    if S.hooksDone then return end
    S.hooksDone = true
    if type(DengluMgr) == 'table' then
      for _, name in ipairs({'managerServerListByJsonObj',
                             'managerDefualtServerListByJsonObj'}) do
        local orig = DengluMgr[name]
        if type(orig) == 'function' then
          DengluMgr[name] = function(self, obj, a, b)
            local cnt = 'nil'
            pcall(function()
              cnt = tostring(obj and obj.data and obj.data.server_list
                             and #obj.data.server_list or 'no-data')
            end)
            report('parseCall', name .. '_n=' .. cnt)
            return orig(self, obj, a, b)
          end
        end
      end
    end
    if type(CommonAlert) == 'table' and type(CommonAlert.show) == 'function' then
      local orig = CommonAlert.show
      CommonAlert.show = function(self, msg, ...)
        report('alert', tostring(msg))
        return orig(self, msg, ...)
      end
    end
    if type(_G.OnNetRecv) == 'function' then
      local orig = _G.OnNetRecv
      _G.OnNetRecv = function(...)
        _G.__dsh_recv_n = (_G.__dsh_recv_n or 0) + 1
        report('recvHook', 'n=' .. _G.__dsh_recv_n ..
               '_a1=' .. tostring(select(1, ...)))
        return orig(...)
      end
    end
    report('hooks', 'installed')
  end

  local function readState(tag)
    local sc, rv = 'na', 'na'
    pcall(function()
      if type(SceneModel) == 'table' then
        sc = tostring(SceneModel:getInstance():getScene())
      else sc = 'noClass' end
    end)
    pcall(function()
      if type(RoleCtrl) == 'table' then
        rv = tostring(RoleCtrl:getInstance():getSelfRoleVo())
      else rv = 'noClass' end
    end)
    report(tag, 't=' .. S.ticks .. '_scene=' .. sc .. '_role=' .. rv ..
           '_recv=' .. tostring(_G.__dsh_recv_n or 0))
  end

  local function step()
    S.ticks = S.ticks + 1
    installHooks()

    if not S.netted and S.ticks >= 25 and type(GameNet) == 'table' then
      local gn = GameNet:getInstance()
      if rawget(gn, 'net_manager') ~= nil then
        S.netted = true
        local ok, err = pcall(function()
          gn:SetLoginServerInfo('10.0.2.2', 9000)
          gn:AsyncConnectLoginServer(10)
        end)
        report('netTry', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
      end
    end

    if S.netted and not S.asyncDone and S.ticks >= 45
       and type(_G.OnNetAsyncConnected) == 'function' then
      S.asyncDone = true
      local ok, err = pcall(function()
        OnNetAsyncConnected(1, '10.0.2.2', 9000)
      end)
      report('async', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
    end

    if S.asyncDone and not S.reloginDone and S.ticks >= 70
       and type(DengluCtrl) == 'table' then
      pcall(function() DengluCtrl:getInstance().account = 'dsh_local' end)
      S.reloginDone = true
      local ok, err = pcall(function()
        DengluCtrl:getInstance():request10103ReLogin(1001, '1')
      end)
      report('relogin', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
    end

    if S.ticks % 15 == 0 then readState('state') end
    if S.ticks >= 600 and driverEntry then
      pcall(function() sch:unscheduleScriptEntry(driverEntry) end)
    end
  end

  -- 安装器：先确保 net_manager 存在（只有 restartNetManager 会创建它），
  -- 这一步会重置调度；**完成之后**再创建驱动 tick，才不会被干掉。
  local function installer()
    if type(GameNet) ~= 'table' then return end
    local gn = GameNet:getInstance()
    if rawget(gn, 'net_manager') == nil then
      local ok, err = pcall(function() gn:restartNetManager() end)
      report('installer', 'restartNetManager ok=' .. tostring(ok) ..
             '_err=' .. tostring(err))
      return
    end
    pcall(function() sch:unscheduleScriptEntry(installerEntry) end)
    driverEntry = sch:scheduleScriptFunc(step, 0.2, false)
    report('probe', 'driver installed entry=' .. tostring(driverEntry))
  end

  installerEntry = sch:scheduleScriptFunc(installer, 0.5, false)
  report('probe', 'installer installed entry=' .. tostring(installerEntry))
end)
