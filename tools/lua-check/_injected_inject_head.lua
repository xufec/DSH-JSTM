-- ===== injected by DSH private server =====
-- ⚠ 顺序很重要：内置服务端必须在**任何诊断上报之前**绑定端口。
--   下面这段 __dsh_rep 从定义起就会发 HTTP，早于服务端绑定的话
--   启动瞬间会打出一串 connect failed（纯噪音，但会误导排查）。
do
  local __dsh_sp = package and package.loaded and package.loaded.__dsh_local_server
  if (not __dsh_sp) and type(loadstring) == "function" then
    local __dsh_src = [====[

]====]
    local __dsh_c = loadstring(__dsh_src, "dsh_local_server")
    if __dsh_c then pcall(__dsh_c) end
  end
  -- 尽早预置本地登录数据：denglu_mgr 构造时会 readTableForKey
  -- ("last_login_account")，必须赶在它之前写入，否则 openView 会停在登录页。
  pcall(function()
    local S = __dsh_sp or _G.__DSH_SERVER
    if S and S.preload_login_record then pcall(S.preload_login_record) end
  end)
  -- ✅ 关键修复：让 main() **自己**调用 ver_load_start()。
  --   main.luac proto#0 尾部已用字节码确认（指令 118-128）：
  --     120 GGET IS_PLATFORM_LOGIN
  --     122 JMP  ->126     (IS_PLATFORM_LOGIN 为假时跳去调用)
  --     123 GGET _is_game_restart
  --     125 JMP  ->128     (_is_game_restart 为假时直接 return)
  --     126 GGET ver_load_start    <- 全局量
  --     127 CALL
  --   只要 _is_game_restart 为真，main() 就在这一行同步调用它。
  --   旧注释断言"此刻 ver_load_start 仍是 nil"是**错的**：
  --   file_update.luac 根原型执行的是 FNEW/GSET ver_load_start
  --   （tools/analyze_flow2.py file_update.luac 40 可见），
  --   发生在 main() 的 require("file_update") 处，远早于指令 126。
  --   ⚠ 为什么必须走这条同步路径（本轮实测的死锁）：
  --     RunningScene 为 nil -> 挂在节点上的 Action 不触发 ->
  --     我们的 tick 永不执行 -> 没人调 ver_load_start -> 永远没有场景。
  --   同步调用发生在 main() 内部，完全不依赖定时器/场景。
  _is_game_restart = true
end
local __dsh_rep = function(tag, val)
  pcall(function()
    if cc and cc.XMLHttpRequest then
      -- 顺手排空内置服务端一次：引擎在加载阶段不提供任何定时回调
      -- （scheduler / Node update / Action 三条路实测都不触发），
      -- 所以把"客户端自己的请求时机"当节拍器用 —— 每次上报都
      -- 让服务端跑一轮 select/accept/read/respond。
      if __dsh_srv_tick then pcall(__dsh_srv_tick) end
      local r = cc.XMLHttpRequest:new()
      r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
      local v = tostring(val)
      if #v > 170 then v = v:sub(1, 170) end
      r:open("GET", "http://10.0.2.2:8080/DSH_REPORT?tag=" .. tag .. "&v=" .. v:gsub("[^%w%.%:/-]", "_"))
      r:send()
    end
  end)
end
URL_PATH = {
  update = "http://10.0.2.2:8080/update",
  voice = "http://10.0.2.2:8080/voice",
  register = "http://10.0.2.2:8080/register",
  is_shenhe = false,
  server = "http://10.0.2.2:8080",
}
URL_PATH_ALL = { get = function(platform) return URL_PATH end }
CDN_PATH_BASE = "http://10.0.2.2:8080"
CDN_URL = "http://10.0.2.2:8080/cdn/"
url_res_config = "http://10.0.2.2:8080/cdn/"
-- ⚠ 必须是【函数】：denglu_mgr proto[22] / proto[53] 会 CALL 它。
--   写成字符串 ⇒ 客户端抛
--   "attempt to call global 'get_servers_url' (a string value)"
--   并中断登录界面构建（login_panel / server_panel / user_panel 全不加载）。
function get_servers_url(...) return "http://10.0.2.2:8080/gateway/mobile/json" end
function get_notice_url(...) return "http://10.0.2.2:8080/notice.json" end
-- file_update.luac proto#5 branch:
--   if not WIN_UPDATE and (platform == Windows or Mac) then update_finish() end
--   if UPDATE_SKIP then update_finish(self) else update_version(self) end
-- 关键：UPDATE_SKIP 是**在调用点用 GGET 读取的全局量**，因此在 config.luac
-- 里赋值即可生效 —— 这样 Android 上直接走 update_finish（无需更新），
-- 完全不碰 AssetsManager / version2.txt 那条会卡 10 秒超时的链路。
WIN_UPDATE = false
UPDATE_SKIP = true
-- ★ 跳过开场 CG（gamecg.mp4）。**不能靠删文件**：
--   file_update proto#39 video_player 只在两处 isFileExist 判断 writable 副本，
--   默认路径 "res/resource/login/gamecg.mp4" 是不判断的 ⇒ 文件缺失时
--   ccexp.VideoPlayer:play() 失败，native 弹「视频问题 / 无法播放此视频。」
--   把整个启动卡住（实测 logcat: Cocos2dxVideoView: Error: 1,0）。
--   真正的开关是源码里现成的：proto#39 开头 `if NO_PLAY_VIDEO then return true end`
--   ⇒ 定义本全局后 video_player 立即返回 true ⇒ video_finish = true ⇒
--   update_finish 正常走到 initInstance/beginGame，无任何视频相关弹窗。
NO_PLAY_VIDEO = true
-- The version-check code calls FmodexManager:downloadOtherFile(...) but the
-- global is never created on our bypassed startup path (probe: nil for 15s),
-- which throws and surfaces as the version-file error.  Provide it from cc.
-- The native downloader (global FmodexManager) is never initialised on our
-- patched startup, so the version download silently does nothing.  Implement
-- downloadOtherFile in Lua on top of cc.XMLHttpRequest: write the body to
-- <writable>/assets/src/<name> and then fire the client own
-- OnFileDownloadResult(name) callback (see file_update.luac proto#8).
pcall(function()
  local __ccF = cc and cc.FmodexManager
  local function __dsh_dl(self, url, filename)
    __dsh_rep("shim_dl", tostring(url) .. " => " .. tostring(filename))
    pcall(function()
      local base = cc.FileUtils:getInstance():getWritablePath() .. "assets/src/"
      pcall(function() cc.FileUtils:getInstance():createDirectory(base) end)
      local req = cc.XMLHttpRequest:new()
      req.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
      req:open("GET", url)
      local fired = false
      req:registerScriptHandler(function()
        if fired then return end
        fired = true
        local body = req.response or ""
        local status = req.status
        local path = base .. tostring(filename)
        local okw = false
        local f = io.open(path, "w")
        if f then f:write(body) f:close() okw = true end
        __dsh_rep("shim_dl_done", tostring(status) .. "|len=" .. tostring(#body) .. "|ok=" .. tostring(okw))
        if type(OnFileDownloadResult) == "function" then
          -- handler signature is (content, filename) -- see common_function proto#125
          local ok, err = pcall(OnFileDownloadResult, body, tostring(filename))
          __dsh_rep("shim_cb", tostring(ok) .. "|" .. tostring(err))
        else
          __dsh_rep("shim_cb", "OnFileDownloadResult missing")
        end
      end)
      req:send()
    end)
  end
  FmodexManager = setmetatable({ downloadOtherFile = __dsh_dl, downloadFile = __dsh_dl },
    { __index = function(_, k) if __ccF then return __ccF[k] end return nil end })
  -- The version check actually calls cc.FmodexManager:downloadOtherFile(url, "version.txt")
  -- (common_function.luac proto#126), so patch the class table too.
  if __ccF and type(__ccF.downloadOtherFile) == "function" then
    __ccF.downloadOtherFile = __dsh_dl
    __ccF.downloadFile = __dsh_dl
    __dsh_rep("shim_cc", "cc.FmodexManager.downloadOtherFile replaced")
  else
    __dsh_rep("shim_cc", "cc.FmodexManager.downloadOtherFile NOT a function")
  end
  __dsh_rep("shim", "FmodexManager.downloadOtherFile implemented")
end)
pcall(function()
  if cc and cc.XMLHttpRequest then
    local r = cc.XMLHttpRequest:new()
    r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
    r:open("GET", "http://10.0.2.2:8080/DSH_CONFIG_LUAC_LOADED")
    r:send()
  end
end)
-- Capture every Lua error and print, and report them over HTTP so
-- diagnosis does not depend on logcat.  (__dsh_rep is defined above.)
if not _G.__dsh_hooked then
  _G.__dsh_hooked = true
  local __op = pcall
  pcall = function(f, ...)
    -- 重入保护：__dsh_rep 内部也会 pcall，不设这个标志会
    -- pcall -> hook -> __dsh_rep -> pcall -> ... 无限递归
    -- （实测表现为 [LUA ERROR] config.luac:148: stack overflow，
    --   config chunk 整体失败、游戏毫无反应）
    if _G.__dsh_in_hook then return __op(f, ...) end
    _G.__dsh_in_hook = true
    local a, b, c, d = __op(f, ...)
    if not a then __dsh_rep("pcall_err", tostring(b)) end
    _G.__dsh_in_hook = false
    return a, b, c, d
  end
  local __ox = xpcall
  if __ox then
    xpcall = function(f, h, ...)
      if _G.__dsh_in_hook then return __ox(f, h, ...) end
      local a, b = __ox(f, function(e)
        _G.__dsh_in_hook = true
        __dsh_rep("xpcall_err", tostring(e))
        _G.__dsh_in_hook = false
        return h(e)
      end, ...)
      return a, b
    end
  end
  local __opr = print
  print = function(...)
    local n = select("#", ...)
    local t = {}
    for i = 1, n do t[i] = tostring((select(i, ...))) end
    __dsh_rep("print", table.concat(t, " "))
    return __opr(...)
  end
  __dsh_rep("hooks", "pcall/xpcall/print installed")
end
-- Intercept string.format: the version check builds its URL via
-- string.format("%s/version2.txt?ts=%s", URL_PATH.update, os.time())
-- so we can both observe it and force the host to ours.
if not _G.__dsh_fmt_hooked then
  _G.__dsh_fmt_hooked = true
  local __ofmt = string.format
  string.format = function(fmt, ...)
    local r = __ofmt(fmt, ...)
    if type(r) == "string" and (r:find("version2") or r:find("tryver")) then
      __dsh_rep("fmt_url", r)
      local fixed = r:gsub("^https?://[^/]+", "http://10.0.2.2:8080")
      if fixed ~= r then
        __dsh_rep("fmt_fixed", fixed)
        return fixed
      end
    end
    return r
  end
  __dsh_rep("hooks", "string.format installed")
end
-- The version download silently fails in the native layer, so the game sits
-- on the version screen.  Drive the client s own "no update needed" entry
-- (update_finish) from a timer once the module globals exist.
if not _G.__dsh_ticker then
  _G.__dsh_ticker = true
  pcall(function()
    local d = cc and cc.Director and cc.Director:getInstance()
    local sch = d and d:getScheduler()
    if not sch then __dsh_rep("ticker", "NO_SCHEDULER"); return end
    local ticks = 0
    local done = false
    local entry
    local function tick()
      ticks = ticks + 1
      URL_PATH = { update = "http://10.0.2.2:8080/update", voice = "http://10.0.2.2:8080/voice",
                   register = "http://10.0.2.2:8080/register", is_shenhe = false, server = "http://10.0.2.2:8080" }
      if ticks == 2 or ticks == 12 or ticks == 30 then
        __dsh_rep("tick", tostring(ticks) .. " update_finish=" .. type(update_finish))
      end
      -- The downloader shim now works, so let the client own version flow run;
      -- only report state here (do NOT call getNowVersion ourselves: it needs the
      -- login controller callback/upvalues, see denglu_ctrl proto#42/#45).
      if ticks == 20 then
        local names = {}
        pcall(function()
          for k in pairs(package.loaded) do
            if type(k) == "string" and k:lower():find("denglu") then names[#names+1] = k end
          end
        end)
        __dsh_rep("state20", "DengluCtrl=" .. type(DengluCtrl) .. " loaded=" .. table.concat(names, ","))
      end
      if ticks >= 60 and entry then
        pcall(function() sch:unscheduleScriptEntry(entry) end)
      end
    end
    entry = sch:scheduleScriptFunc(tick, 0.5, false)
    __dsh_rep("ticker", "installed")
  end)
end
-- ===== DSH hot patch：从应用私有目录加载可变补丁（免重打包迭代）=====
--   实测搜索路径顺序（logcat printSearchPaths）是
--     assets/ , <writable>/assets/res/ , <writable>/assets/src/ , assets/res/ , assets/src/
--   打包的 assets/ 在最前，所以往 writable 推 config.luac **无法**覆盖打包版
--   （已实测：推 6 个候选路径，无一生效）。改由这里的引导代码用绝对
--   路径读取 <writable>/dsh_patch.lua 并执行 —— 之后迭代只需
--   `adb push dsh_patch.lua /data/data/<pkg>/files/dsh_patch.lua`。
pcall(function()
  if _G.__dsh_patch_ran then return end
  _G.__dsh_patch_ran = true
  local wp = cc.FileUtils:getInstance():getWritablePath()
  local path = wp .. "dsh_patch.lua"
  local f = io.open(path, "rb")
  if not f then print("[DSH_PATCH] no patch file at " .. path) return end
  local src = f:read("*a")
  f:close()
  if not src or #src == 0 then print("[DSH_PATCH] empty patch") return end
  local chunk, err = loadstring(src, "@dsh_patch")
  if not chunk then print("[DSH_PATCH] SYNTAX ERROR: " .. tostring(err)) return end
  local ok, e = pcall(chunk)
  print("[DSH_PATCH] ran ok=" .. tostring(ok) .. " " .. tostring(e))
end)
-- ============================================================================
--  DSH 启动观测器（**默认非侵入版**）
-- ============================================================================
--  ※ 下面这行 ASCII 标记不要删：tools/verify_injected_lua.py 靠它定位本段
-- 