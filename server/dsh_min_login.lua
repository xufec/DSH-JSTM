
-- =====================================================================
-- DSH 本地地址注入（在 config.luac 里直接写全局，绕开 url_config 下载）
--
-- 为什么必须放在这里（实测根因）：
--   原本地址靠 CDN 下发的 url_config.lua 提供，客户端流程是
--     file_update proto#9:  if URL_PATH then <proto#5>() return end   ← 短路点
--                           cc.FmodexManager:downloadOtherFile(URL_LUA_CONFIG, 'url_config.lua')
--     file_update proto#8:  读 <writable>/assets/src/url_config.lua → loadstring → 执行
--   实测（专项探针 url_config_diag.lua）：
--     URL_PATH / URL_PATH_ALL 在整场运行里**始终为 nil**，
--     而 downloadOtherFile 与 OnFileDownloadResult 都在 ~5 次/秒地反复触发 ——
--     即"下载回报完成、但脚本没生效"，于是 proto#9 永远不短路，
--     以 0.2 秒的间隔无限重下（140 秒 729 次），把 URL_PATH、调度、网络状态
--     反复重置。这就是"每轮表现都不一样"的真正根源。
--
--   把同样的全局**提前写在 config.luac 里**（本文件即注入到 config.luac 末尾，
--   由 main.luac 的 loadConfig() 在 main() 之前执行），proto#9 一进来就看到
--   URL_PATH 为真 → 直接短路 → 重试循环消失，且不再依赖原生下载器写文件。
-- =====================================================================
pcall(function()
  local HOST = "10.0.2.2"
  local PORT = 8080
  local BASE = "http://" .. HOST .. ":" .. PORT

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
  URL_PATH       = URL_PATH_ALL:get(PLATFORM_NAME)
  CDN_PATH_BASE  = BASE
  CDN_URL        = BASE .. "/cdn/"
  url_res_config = BASE .. "/cdn/"

  -- 这两个必须是【函数】：denglu_mgr proto[22] / notice_view proto[9] 会调用它们
  function get_servers_url(...)
    return BASE .. "/gateway/mobile/json"
  end
  function get_notice_url(...)
    return BASE .. "/notice.json"
  end

  -- 令 now_ver >= target_ver 恒成立 → 直接 update_finish，跳过整个热更下载
  UPDATE_VERSION_MAX = NOW_VERSION

  _G.__dsh_urlpath_injected = true
end)

--
-- 配合 classes.dex 的一个字节补丁：
--   Lcom/shiyue/sdk/EWanSdk;-><init>()V
--   0x61edfd: 00 -> 01   ( const/4 v0,#0  =>  const/4 v0,#1 )
--   即 is_close = true。EWanSdk 每个方法都被 `if (!this.is_close)` 包住，
--   因此该字段一旦为 true：
--     * onCreate 不再调用 SuperPlatform.onCreate / SuperPlatform.init
--       ⇒ 360 渠道 SDK（SuperThirdSdk360）根本不会被初始化
--       ⇒ 不再弹出 360 实名认证/登录 ContainerActivity
--       ⇒ 不再向 360 服务器发任何请求
--     * onLogin 不再调用 SuperPlatform.login
--     * 所有生命周期回调(onResume/onPause/onDestroy/...)全部 no-op
--   代价：Java 侧再也不会回调 sdkBackInit / sdkBackLogin，必须由本文件自供。
--
-- 本块做两件事（严格镜像真实 Java 行为，见 jadx 反编译）：
--
--   1) 伪 sdkBackInit(0, msg)
--        Java 原逻辑：EWanSdk.onCreate → SuperPlatform.init 的 onSuccess
--        Lua 逻辑（sdk_function.luac proto#11 反汇编）：
--            if not IS_PLATFORM_LOGIN then return end
--            if code ~= 0 then sdkAlert('网络连接失败，请重新登录','确定',exit); return end
--            if SDK_INIT_SUC then return end
--            SDK_INIT_SUC = true ; ver_load_start()          -- ★ 更新流程入口
--
--   2) 伪 sdkBackLogin(0, payload)
--        Java 原逻辑：EWanSdk.onLogin → SuperPlatform.login 的 onLoginSuccess
--            callLuaFunction("sdkBackLogin", 0,
--                openid#username#timestamp#sign#token#tpUid)
--        Lua 逻辑（sdk_function.luac proto#12 → denglu_platform.luac proto#12）：
--            if code ~= 0 then sdkOnLogin(); return end
--            DengluPlatForm:getInstance():onLoginInfo(data)
--        而 onLoginInfo 做的是：
--            local openid,username,timestamp,sign,token,channelId = unpack(Split(data,'#'))
--            self.info = {openid=...,username=...,timestamp=...,sign=...,token=...,channelId=...}
--            self.is_logined = true ; self:loginCallback()
--
--    触发时机：不改用定时器硬塞，而是**钩住 game 真正发起平台登录的那一次调用**
--      assets/src/sdk_function.luac proto#1  beginThirdPartyLogin
--        → cc.Device:beginThirdPartyLogin()   ← 在调用点用 GGET/TGETS 查表，
--                                               所以覆盖 cc.Device 上的方法有效
--      被钩住后立即回调 sdkBackLogin，完全等价于"SDK 登录成功"，
--      但不会调用原生、不会打开 360 界面。
--
-- 时序说明：config.luac 由 main.luac 的 loadConfig() 执行，早于 main()，
--   因此本块必须**延迟**到 sdk_function / file_update 被 require 之后才能动手：
--   用一个 Director 调度 tick 轮询。
-- =====================================================================
pcall(function()
  if _G.__dsh_fake_installed then return end
  _G.__dsh_fake_installed = true

  local director = nil
  pcall(function() director = cc.Director:getInstance() end)
  local sch = nil
  pcall(function() sch = director and director:getScheduler() end)
  if not sch then
    _G.__dsh_fake_err = 'no scheduler'
    return
  end

  -- ---------- 伪登录载荷（6 段，# 分隔，顺序已由反汇编确认） ----------
  local function make_payload()
    return table.concat({
      'dsh_local',            -- openid
      'DSH',                  -- username
      tostring(os.time()),    -- timestamp
      'dsh_sign',             -- sign
      'dsh_token',            -- token
      '1',                    -- channelId (Java 侧的 tpUid)
    }, '#')
  end

  -- ---------- 2) 钩住平台登录请求 -> 立刻伪回调 ----------
  local function install_login_hook()
    if _G.__dsh_login_hooked then return true end
    local dev = cc and cc.Device
    if type(dev) ~= 'table' or type(dev.beginThirdPartyLogin) ~= 'function' then
      return false
    end
    _G.__dsh_login_hooked = true
    dev.beginThirdPartyLogin = function(...)
      -- 刻意**不调用**原生实现：原生只会走到已被关闭的 EWanSdk.onLogin
      _G.__dsh_fake_login = true
      _G.__dsh_login_payload = make_payload()
      if type(_G.sdkBackLogin) == 'function' then
        pcall(_G.sdkBackLogin, 0, _G.__dsh_login_payload)
      else
        _G.__dsh_fake_err = 'sdkBackLogin missing'
      end
    end
    return true
  end

  local ticks, entry = 0, nil
  local function stop()
    if entry then pcall(function() sch:unscheduleScriptEntry(entry) end) end
  end

  local function step()
    ticks = ticks + 1
    if ticks > 900 then stop(); return end

    -- 1) 伪 sdkBackInit：等 sdk_function + file_update 都就绪
    if not _G.__dsh_fake_init
       and type(_G.sdkBackInit) == 'function'
       and type(_G.ver_load_start) == 'function' then
      _G.__dsh_fake_init = true
      pcall(_G.sdkBackInit, 0, 'DSH伪登录初始化成功')
    end

    -- 2) 平台登录钩子：cc.Device 一出现就装
    if _G.__dsh_fake_init then
      install_login_hook()
    end

    if _G.__dsh_fake_login then stop() end
  end

  entry = sch:scheduleScriptFunc(step, 0.2, false)
  _G.__dsh_fake_entry = entry
end)

-- [DSH] 最小伪登录：只含 URL 短路 + 伪 sdkBackInit/sdkBackLogin，无任何诊断 hook
