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
