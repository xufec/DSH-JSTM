-- =====================================================================
-- 《绝世唐门》本地最小配置服务器 —— 下发内容
-- 对应客户端请求：GET /update/config/url_config_ewan.lua?<os.time()>
--
-- 客户端消费方式（file_update.luac proto#8 反汇编确认）：
--   1) 响应体被写入 <writable>/assets/src/url_config.lua
--   2) pcall(loadstring(响应体)())    ← 返回值被丢弃，必须写【全局】
--   3) 读全局 URL_PATH_ALL，调用 URL_PATH_ALL:get(PLATFORM_NAME) 得到 URL_PATH
--   4) URL_PATH 需含 update / voice / register / is_shenhe
--
-- 版本接口（file_update.luac proto#17 get_version_info 反汇编确认）：
--   target_ver = UPDATE_TRY_VERSION_MAX or UPDATE_VERSION_MAX
--   now_ver    = max(local_version, NOW_VERSION)
--   proto#19 #70-72: now_ver >= target_ver → update_finish()（跳过整个热更下载）
--
-- 说明：mock_server.py 会把下面两行替换成客户端实际请求用的 Host/Port，
--       所以绝对地址永远与客户端连上来的地址一致。
-- =====================================================================

local HOST = "127.0.0.1"
local PORT = 8080
local BASE = "http://" .. HOST .. ":" .. PORT

-- ---------- 1) URL_PATH_ALL：客户端用 :get(PLATFORM_NAME) 取分支 ----------
URL_PATH_ALL = {
  get = function(_, platform)
    return {
      update    = BASE .. "/update",
      voice     = BASE .. "/voice",
      register  = BASE .. "/register",
      is_shenhe = false,
      platform  = tostring(platform),
    }
  end,
}

-- ---------- 2) 客户端其它模块引用的全局地址 ----------
URL_PATH        = URL_PATH_ALL:get(PLATFORM_NAME)   -- file_update / denglu_ctrl
CDN_PATH_BASE   = BASE
CDN_URL         = BASE .. "/cdn/"                    -- res_download_mgr
url_res_config  = BASE .. "/cdn/"                    -- res_download_mgr

-- ⚠ 这两个必须是【函数】，不是字符串。
-- 静态证据（tools/find_external_globals.py + 反汇编）：
--   denglu_mgr.luac   proto[22] @29  GGET get_servers_url   → @41 CALL A=4 (nargs=4) → open('POST', url)
--   notice_view.luac  proto[9]  @0   GGET get_notice_url    → @3  CALL A=3 (nargs=2) → web_view:loadURL(url)
-- 若误写成字符串，客户端抛
--   "attempt to call global 'get_servers_url' (a string value)"
-- 并中断登录界面构建（实测：login_panel / server_panel / user_panel 全部不再加载）。
function get_servers_url(...)
  return BASE .. "/gateway/mobile/json"                -- denglu_mgr
end

function get_notice_url(...)
  return BASE .. "/notice.json"                        -- notice_view
end

-- ---------- 3) 版本上限：令 now_ver >= target_ver 恒成立 ----------
-- 只定义 UPDATE_VERSION_MAX（proto#17 默认读取的那个），不伪造 TRY 分支字段。
UPDATE_VERSION_MAX = NOW_VERSION

-- =====================================================================
-- 4) 临时观测探针（只做观测，不改变客户端任何行为；仅服务端下发内容）
--    目的：判定 beginGame() 是否执行 → 即登录界面流程是否已经跑到。
--    依据（STARTUP_UPDATE_FLOW.md §1 第 10 步）：
--      beginGame() 会置 GAME_INITED = true，并调用
--      DengluCtrl:getInstance():openView()  ← 登录界面
-- =====================================================================
pcall(function()
  local function report(tag, v)
    pcall(function()
      local r = cc.XMLHttpRequest:new()
      r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
      local s = tostring(v)
      if #s > 200 then s = s:sub(1, 200) end
      r:open("GET", BASE .. "/DSH_PROBE?t=" .. tostring(tag) .. "&v=" ..
             s:gsub("[^%w%._:/-]", "_"))
      r:send()
    end)
  end
  _G.__dsh_report = report

  -- ---- 载入期诊断（一定能执行到，因为本 chunk 已被 loadstring 执行）----
  report('load_enter', 'ok')
  report('load_cc', type(cc))
  report('load_ccDirector', type(cc and cc.Director))
  local dir = nil
  pcall(function() dir = cc.Director:getInstance() end)
  report('load_dirInst', tostring(dir))
  local sch = nil
  pcall(function() sch = dir and dir:getScheduler() end)
  report('load_scheduler', tostring(sch))
  report('load_GAME_INITED', tostring(rawget(_G, 'GAME_INITED')))
  if not sch then
    report('load_abort', 'no scheduler -> tick not installed')
    return
  end

  local ticks = 0
  local entry = nil
  local function tick()
    ticks = ticks + 1
    -- 心跳：tick 序号 + 剩余待加载模块数 + GAME_INITED + DengluCtrl 类型
    report('hb', ticks ..
           '_GM' .. tostring(rawget(_G, 'GameModule') and #GameModule or 'nil') ..
           '_GI' .. tostring(rawget(_G, 'GAME_INITED')) ..
           '_DC' .. type(rawget(_G, 'DengluCtrl')) ..
           '_fi' .. tostring(rawget(_G, '__dsh_fake_init')) ..
           '_lh' .. tostring(rawget(_G, '__dsh_login_hooked')) ..
           '_fl' .. tostring(rawget(_G, '__dsh_fake_login')))
    if ticks == 2 or ticks == 20 or ticks == 60 then
      report('fk_err_' .. ticks, tostring(rawget(_G, '__dsh_fake_err')))
      report('fk_payload_' .. ticks, tostring(rawget(_G, '__dsh_login_payload')))
      report('ccDevice_' .. ticks, type(cc and cc.Device))
      report('ccDeviceBTPL_' .. ticks,
             type(cc and cc.Device and cc.Device.beginThirdPartyLogin))
    end
    if ticks >= 200 and entry then
      pcall(function() sch:unscheduleScriptEntry(entry) end)
    end
  end

  entry = sch:scheduleScriptFunc(tick, 0.5, false)
  report('load_tick', 'installed entry=' .. tostring(entry))
end)

return { URL_PATH = URL_PATH, URL_PATH_ALL = URL_PATH_ALL }
