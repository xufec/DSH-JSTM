-- =====================================================================
-- 专项诊断探针：为什么客户端每 0.2 秒重下 url_config（判为失败重试）
--
-- 相关反汇编（file_update.luac）：
--   proto#10 initConfig：version_view:setVersionTips('检查版本信息...')
--        → Sequence(DelayTime(0.2), CallFunc(proto#9))
--   proto#9  ：if URL_PATH then <proto#5>() return end          ← 短路点
--              if not cc.FmodexManager.downloadOtherFile then <proto#5>() return end
--              cc.FmodexManager:downloadOtherFile(URL_LUA_CONFIG..'?'..os.time(),
--                                                 'url_config.lua')
--   proto#8  OnFileDownloadResult(body, filename):
--              io.open(writable..'assets/src/'..filename) → read('*all')
--              → pcall(loadstring(text)())
--              成功：URL_PATH_ALL 为真 → URL_PATH = URL_PATH_ALL:get(PLATFORM_NAME)
--                    → <proto#5>()
--              失败：setVersionTips('检查版本信息失败...') + CallFunc(proto#7) 0.2s 后重下
--
-- 因此本探针只回答三个问题：
--   Q1 downloadOtherFile 被谁、以什么 URL、被调了多少次
--   Q2 OnFileDownloadResult 有没有被回调、filename 是什么
--   Q3 URL_PATH / URL_PATH_ALL 在每一刻到底是什么（nil 说明配置没被执行/没写成功）
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

if _G.__dsh_diag_installed then
  return
end
_G.__dsh_diag_installed = true
_G.__dsh_dl_n = 0
_G.__dsh_ofr_n = 0

report('diag', 'enter')

-- ---- Q1: 包装下载器 ----
pcall(function()
  local cls = cc and cc.FmodexManager
  if type(cls) ~= 'table' or type(cls.downloadOtherFile) ~= 'function' then
    report('diag', 'FmodexManager.downloadOtherFile not available: ' .. tostring(type(cls)))
    return
  end
  local orig = cls.downloadOtherFile
  cls.downloadOtherFile = function(self, url, name, c)
    _G.__dsh_dl_n = (_G.__dsh_dl_n or 0) + 1
    local u = tostring(url)
    if #u > 90 then u = u:sub(1, 90) end
    report('dl', 'n=' .. _G.__dsh_dl_n .. '_name=' .. tostring(name) .. '_url=' .. u)
    return orig(self, url, name, c)
  end
  report('diag', 'downloadOtherFile hooked')
end)

-- ---- Q2: 包装原生完成回调（全局 OnFileDownloadResult）----
-- 注意：配置自己就可能会覆盖它（proto#10 里 OnFileDownloadResult = proto#8），
-- 所以这里用 metatable 拦截 __newindex，保证我们始终能观察到赋值与调用。
pcall(function()
  local mt = getmetatable(_G)
  if mt == nil then
    mt = {}
    setmetatable(_G, mt)
  end
  -- 记录已经被赋值过的真实函数
  local real = rawget(_G, 'OnFileDownloadResult')
  local wrapper = function(...)
    _G.__dsh_ofr_n = (_G.__dsh_ofr_n or 0) + 1
    local fn = select(2, ...)
    report('ofr', 'n=' .. _G.__dsh_ofr_n .. '_file=' .. tostring(fn) ..
           '_hasReal=' .. tostring(type(real) == 'function'))
    if type(real) == 'function' then return real(...) end
  end
  rawset(_G, 'OnFileDownloadResult', wrapper)
  report('diag', 'OnFileDownloadResult hooked, was=' .. tostring(type(real)))
end)

-- ---- Q3: 周期上报 URL_PATH 状态 ----
pcall(function()
  local sch
  pcall(function() sch = cc.Director:getInstance():getScheduler() end)
  if not sch then report('diag', 'no scheduler'); return end
  local t = 0
  local entry
  local function tick()
    t = t + 1
    report('urlpath', 't=' .. t ..
           '_URL_PATH=' .. tostring(type(rawget(_G, 'URL_PATH'))) ..
           '_URL_PATH_ALL=' .. tostring(type(rawget(_G, 'URL_PATH_ALL'))) ..
           '_dl=' .. tostring(_G.__dsh_dl_n) ..
           '_ofr=' .. tostring(_G.__dsh_ofr_n))
    if t >= 200 and entry then pcall(function() sch:unscheduleScriptEntry(entry) end) end
  end
  entry = sch:scheduleScriptFunc(tick, 1.0, false)
  report('diag', 'urlpath ticker installed')
end)
