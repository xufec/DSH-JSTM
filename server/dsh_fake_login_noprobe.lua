-- [DSH] 版本开关：关掉全部诊断 hook，只保留 URL 短路 + 伪登录
_G.__dsh_noprobe = true

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

-- =====================================================================
-- DSH 联调驱动 + 客观判据上报
--
-- 为什么也放在这里：既然 proto#9 已被 URL_PATH 短路（不再下载 url_config），
-- 服务端下发的那份脚本**永远不会被执行**了，所以驱动逻辑只能放在
-- config.luac 这份一定会执行的文件里。
--
-- 上报走 cc.XMLHttpRequest → http://10.0.2.2:8080/DSH_PROBE?t=<tag>&v=<val>
-- =====================================================================
if not _G.__dsh_noprobe then
pcall(function()
  if _G.__dsh_driver_installed then return end
  _G.__dsh_driver_installed = true

  local BASE = "http://10.0.2.2:8080"
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

  local sch
  pcall(function() sch = cc.Director:getInstance():getScheduler() end)
  if not sch then
    _G.__dsh_report = report
    _G.__dsh_driver_err = 'no scheduler'
    return
  end

  -- 供后续外部脚本复用
  _G.__dsh_report = report

  local S = { t = 0, hooks = false, neted = false, asyncDone = false,
              reloginDone = false }
  local entry

  -- =====================================================================
  -- ★ 场景构建流程计数（修正采集时机）
  --
  -- 上一轮的失败教训：把包装放在 step() 里，而 step 挂在 GameNet.doOneMsg 上，
  -- 必须等 sys/gamenet 加载完（约 35 秒）才装得上；而场景构建
  -- （scene_model proto[68] sceneStart → SceneView:createMap）发生得更早，
  -- 于是"一条 svCall 都没有"只是采集时机不对，**不能当作证据**。
  --
  -- 正确做法：SceneView 是在 scene_view.luac 里 `GSET SceneView` 创建出来的，
  -- 用 _G 的 __newindex 拦截这次赋值，**在它刚被创建的一瞬间**就包装好方法。
  -- 这段代码在 config.luac 载入时就执行，远早于任何模块加载。
  -- =====================================================================
  local SV_METHODS = {'createMap', 'layoutScene', 'renderScene',
                      'getScenePicByPos', 'clearLayer', 'getPicRes',
                      'quequeAddFun', 'changeSceneLayer',
                      'createPlayer'}          -- ★ createPlayer：角色元素的创建入口

  local function installSceneViewHooks(cls)
    if type(cls) ~= 'table' or _G.__dsh_sv_hooked then return end
    _G.__dsh_sv_hooked = true
    for _, nm in ipairs(SV_METHODS) do
      local orig = cls[nm]
      if type(orig) == 'function' then
        cls[nm] = function(self, ...)
          _G.__dsh_sv_n = (_G.__dsh_sv_n or 0) + 1
          report('svCall', nm .. '_n=' .. _G.__dsh_sv_n ..
                 '_args=' .. select('#', ...))
          return orig(self, ...)
        end
      end
    end
    report('svHook', 'installed_at_tick=' .. tostring(S.t))
  end

  -- =====================================================================
  -- ★★ 最关键的取证：直接测量客户端**解析后**的 10201 四个表长度
  --
  -- scene_controller.on10201（proto[9]，212 条字节码）的字符串显示它做的是：
  --     roles → addRole ；npcs → addNpc ；mons → addMonster ；elems → addElement
  --     misc_uint32/16/8/str → managerMiscKV_
  -- ⇒ 角色/NPC/怪物全部经由这条消息进入场景。
  --   我的 roles 条目里那 6 个 `D|Dsc*|` 动态子表是**猜的编码**，
  --   如果猜错，客户端解析出来就是 0 条 → 地图上没有角色/NPC。
  --   这里包住 on10201，把 resp.roles/npcs/mons/elems 的**实际条数**报上来。
  -- =====================================================================
  local function installSceneCtrlHooks(cls)
    if type(cls) ~= 'table' or _G.__dsh_sc_hooked then return end
    _G.__dsh_sc_hooked = true
    local origOn = cls['on10201']
    if type(origOn) == 'function' then
      cls['on10201'] = function(self, resp, ...)
        local out = {}
        pcall(function()
          for _, k in ipairs({'roles', 'npcs', 'mons', 'elems'}) do
            local t = resp and resp[k]
            local n = 'nil'
            if type(t) == 'table' then
              local i = 0
              for _ in pairs(t) do i = i + 1 end
              n = tostring(i)
            end
            out[#out + 1] = k .. '=' .. n
          end
        end)
        report('on10201', table.concat(out, '_'))
        return origOn(self, resp, ...)
      end
    else
      report('on10201', 'NOT_a_function')
    end
    for _, nm in ipairs({'addRole', 'addNpc', 'addMonster', 'addElement'}) do
      local orig = cls[nm]
      if type(orig) == 'function' then
        cls[nm] = function(self, ...)
          _G.__dsh_sc_n = (_G.__dsh_sc_n or 0) + 1
          report('scCall', nm .. '_n=' .. _G.__dsh_sc_n ..
                 '_a=' .. select('#', ...))
          return orig(self, ...)
        end
      end
    end
    report('scHook', 'installed')
  end

  -- ★ 更正：on10201 里是 `self.model:addRole(...)`（字符串里 addRole 紧邻 model），
  --   所以真正要包的是 **SceneModel**，不是 SceneController。上一轮挂错对象，
  --   才会出现"on10201 收到 roles=1 但 addRole 一次都没被调用"。
  local function installSceneModelHooks(cls)
    if type(cls) ~= 'table' or _G.__dsh_sm_hooked then return end
    _G.__dsh_sm_hooked = true
    for _, nm in ipairs({'addRole', 'addNpc', 'addMonster', 'addElement',
                         'syncRoles', 'changeSceneLayer', 'setLoadState__'}) do
      local orig = cls[nm]
      if type(orig) == 'function' then
        cls[nm] = function(self, ...)
          _G.__dsh_sm_n = (_G.__dsh_sm_n or 0) + 1
          -- addRole 的入参就是客户端解析出的角色表 —— 直接看它拿到什么
          local extra = ''
          if nm == 'addRole' or nm == 'addNpc' or nm == 'addMonster' then
            local a1 = select(1, ...)
            if type(a1) == 'table' then
              -- 角色与 NPC 的字段不同，统一把常见的都打出来（nil 也能看出缺哪个）
              extra = '_id=' .. tostring(a1.id) .. '_bid=' .. tostring(a1.bid) ..
                      '_type=' .. tostring(a1.type) ..
                      '_x=' .. tostring(a1.x) .. '_y=' .. tostring(a1.y) ..
                      '_name=' .. tostring(a1.name) ..
                      '_rid=' .. tostring(a1.rid) .. '_career=' .. tostring(a1.career) ..
                      '_res=' .. tostring(a1.res_id) .. '_status=' .. tostring(a1.status)
            else
              extra = '_argtype=' .. type(a1)
            end
          end
          report('smCall', nm .. '_n=' .. _G.__dsh_sm_n ..
                 '_a=' .. select('#', ...) .. extra)
          return orig(self, ...)
        end
      end
    end
    report('smHook', 'installed')
  end

  -- ★ Player 元素（角色可视对象）创建计数：直接回答"角色精灵有没有被造出来"
  --   上一轮只在 __newindex 里装，没装上也无人知道 ⇒ 改为函数 + 双路径安装。
  local function installPlayerHook(cls)
    if type(cls) ~= 'table' or _G.__dsh_player_hooked then return end
    _G.__dsh_player_hooked = true
    local ks = {}
    for k, _ in pairs(cls) do ks[#ks + 1] = tostring(k) end
    table.sort(ks)
    report('playerHook', 'keys=' .. table.concat(ks, ',', 1, math.min(#ks, 24)))
    local origNew = cls['New']
    if type(origNew) == 'function' then
      cls['New'] = function(...)
        _G.__dsh_player_n = (_G.__dsh_player_n or 0) + 1
        local obj = origNew(...)
        -- ★ 抓住实例本身，后面直接量它的位置/可见性/父节点
        _G.__dsh_player_obj = obj
        report('playerNew', 'n=' .. _G.__dsh_player_n ..
               '_a=' .. select('#', ...))
        return obj
      end
      report('playerHook', 'New_wrapped')
    else
      report('playerHook', 'New_NOT_function_type=' .. tostring(type(origNew)))
    end
  end

  pcall(function()
    local mt = getmetatable(_G)
    if mt == nil then
      mt = {}
      setmetatable(_G, mt)
    end
    local prev = mt.__newindex
    mt.__newindex = function(t, k, v)
      if prev then pcall(prev, t, k, v) end
      rawset(t, k, v)
      if k == 'SceneView' then
        pcall(installSceneViewHooks, v)
      elseif k == 'SceneController' then
        pcall(installSceneCtrlHooks, v)
      elseif k == 'SceneModel' then
        pcall(installSceneModelHooks, v)
      elseif k == 'Player' then
        pcall(installPlayerHook, v)
      end
    end
    report('svHook', 'newindex_armed_tick=' .. tostring(S.t))
  end)

  -- 兜底：万一类在 _G 上早已存在（__newindex 不触发），轮询补装
  local function svFallback()
    if not _G.__dsh_sv_hooked and type(SceneView) == 'table' then
      installSceneViewHooks(SceneView)
    end
    if not _G.__dsh_sc_hooked and type(SceneController) == 'table' then
      installSceneCtrlHooks(SceneController)
    end
    if not _G.__dsh_sm_hooked and type(SceneModel) == 'table' then
      installSceneModelHooks(SceneModel)
    end
    if not _G.__dsh_player_hooked and type(Player) == 'table' then
      installPlayerHook(Player)
    end
  end

  local function step()
    S.t = S.t + 1
    if _G.__dsh_tryInstall then pcall(_G.__dsh_tryInstall) end
    -- 逐 tick 上报（只报前 60 个），用于精确定位"tick 死在哪一刻"
    if S.t <= 60 then report('tick', 't=' .. S.t) end

    -- 钩子：解析入口 / 弹窗 / 收包计数
    if not S.hooks and S.t >= 3 then
      S.hooks = true
      if type(DengluMgr) == 'table' then
        for _, name in ipairs({'managerServerListByJsonObj',
                               'managerDefualtServerListByJsonObj'}) do
          local orig = DengluMgr[name]
          if type(orig) == 'function' then
            DengluMgr[name] = function(self, obj, a, b)
              local n = 'nil'
              pcall(function()
                n = tostring(obj and obj.data and obj.data.server_list
                             and #obj.data.server_list or 'no-data')
              end)
              report('parseCall', name .. '_n=' .. n)
              return orig(self, obj, a, b)
            end
          end
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
      -- ★ 空白提示框定位：CommonAlert.show(msg, ...) 与全局 message(...)
      --   common_alert.luac proto[6] 用 getString('提示') 当标题、msg 当正文，
      --   所以 msg 为空就会得到「标题=提示、正文空白、按钮=确定」。
      if type(CommonAlert) == 'table' and type(CommonAlert.show) == 'function' then
        local orig = CommonAlert.show
        CommonAlert.show = function(self, msg, ...)
          report('alert', 'CommonAlert.show_msg=[' .. tostring(msg) .. ']')
          return orig(self, msg, ...)
        end
      end
      if type(_G.message) == 'function' then
        local orig = _G.message
        _G.message = function(msg, ...)
          report('alert', 'message_msg=[' .. tostring(msg) .. ']')
          return orig(msg, ...)
        end
      end
      report('hooks', 'installed')
    end

    -- ★ 处理函数钩子必须"等到 DengluCtrl 存在"再装。
    --   踩坑：hooks 块在驱动第 3 帧（约 50ms）就跑完了，那时 DengluCtrl 还不存在，
    --   于是这三个钩子被**静默跳过**（`hooks installed` 照样上报），
    --   表现就是 hit_* 永远为 0，误以为"消息没被派发"。
    if not _G.__dsh_handler_hooked and type(DengluCtrl) == 'table' then
      _G.__dsh_handler_hooked = true
      for _, nm in ipairs({'on1110Rolelist', 'on10102Login', 'on10103ReLogin'}) do
        local orig = DengluCtrl[nm]
        if type(orig) == 'function' then
          DengluCtrl[nm] = function(self, resp, ...)
            local code = 'na'
            pcall(function() code = tostring(resp and resp.code) end)
            report('hit_' .. nm,
                   'code=' .. code .. '_type=' .. tostring(type(resp)))
            return orig(self, resp, ...)
          end
        else
          report('hit_' .. nm, 'NOT_a_function')
        end
      end
      report('handlerHooks', 'installed')
    end

    -- ★ 弹窗钩子同样要"等到全局存在"再装（与上一个坑同源：
    --   在驱动第 3 帧时 CommonAlert / message 还不存在，会被静默跳过）。
    if not _G.__dsh_alert_hooked and type(CommonAlert) == 'table'
       and type(CommonAlert.show) == 'function' then
      _G.__dsh_alert_hooked = true
      -- ⚠ 上报只报"长度/是否为空"，不要把正文塞进 URL：
      --   之前的写法里中文会被 URL 安全替换成下划线，
      --   于是"中文有内容"和"空串"看起来一模一样，无法区分。
      local function desc(v)
        if v == nil then return 'NIL' end
        return 'len' .. tostring(#tostring(v))
      end
      local obs = CommonAlert.show
      CommonAlert.show = function(self, msg, ...)
        report('alert', 'CommonAlert ' .. desc(msg))
        return obs(self, msg, ...)
      end
      if type(_G.message) == 'function' then
        local om = _G.message
        _G.message = function(msg, ...)
          -- ★ 用 debug.getinfo 抓"谁调用的 message"，直接定位到具体 .luac 与行号。
          --   这是找空白框触发点的最快手段。
          local src = '?'
          pcall(function()
            local parts = {}
            for lv = 2, 6 do
              local i = debug and debug.getinfo and debug.getinfo(lv, 'Sl')
              if not i then break end
              parts[#parts + 1] = tostring(i.short_src or i.source or '?') ..
                                  ':' .. tostring(i.currentline or -1)
            end
            if #parts > 0 then src = table.concat(parts, '|') end
          end)
          report('alert', 'message ' .. desc(msg) ..
                 ' at=' .. tostring(src):gsub('[^%w%._:/-]', '_'))
          return om(msg, ...)
        end
      end
      report('alertHooks', 'installed')
    end

    -- ★ 场景构建流程计数（兜底补装；主路径在文件早段的 __newindex 拦截）
    svFallback()

    -- ★ 任务系统取证：包住 MissionCtrl.createMis，dump 生成的任务 VO 字段
    --   mission_ctrl proto[31] (handle12400) 会遍历 mission_list，对每条调
    --   createMis(...) 生成 VO，然后 initRecList()。UI 追踪栏读的就是这个 VO。
    --   把 VO 的字段全部 dump 出来，就能直接看出"第二行 nil"缺的是哪一项。
    if not _G.__dsh_mis_hooked and type(MissionCtrl) == 'table' then
      _G.__dsh_mis_hooked = true
      local orig = MissionCtrl.createMis
      if type(orig) == 'function' then
        MissionCtrl.createMis = function(self, ...)
          local vo = orig(self, ...)
          if type(vo) == 'table' then
            local ks, nils = {}, {}
            for k, v in pairs(vo) do
              ks[#ks + 1] = tostring(k) .. '=' .. tostring(v)
              if v == nil then nils[#nils + 1] = tostring(k) end
            end
            table.sort(ks)
            report('misVO', table.concat(ks, ',', 1, math.min(#ks, 90)))
            -- ★ sidebar_mis_item 的两行 label 是 name_label / content_label，
            --   而 proto[12] 里同时出现 missionContent 与 mis_content
            --   ⇒ 第二行很可能是 mis_content。这里专门量它（只报长度，避免中文被替换）。
            local function L(v)
              if v == nil then return 'NIL' end
              return tostring(#tostring(v))
            end
            report('misContent', 'mis_contentLen=' .. L(vo.mis_content) ..
                   '_mis_bid=' .. tostring(vo.mis_bid) ..
                   '_mis_code=' .. tostring(vo.mis_code) ..
                   '_mis_type=' .. tostring(vo.mis_type))
            table.sort(nils)
            report('misNil', 'nilCount=' .. #nils .. '_' ..
                   table.concat(nils, ',', 1, math.min(#nils, 30)))

            -- ★★★ 最后一环：第二行是 getConfig().desc，而 getConfig() 只 return
            --   self.mis_config（mission_vo proto[4] 仅 2 条字节码）。
            --   所以真正要看的是**嵌套的 mis_config 表**，不是 VO 自身。
            local mc = rawget(vo, 'mis_config')
            if type(mc) == 'table' then
              local ks2 = {}
              for k, _ in pairs(mc) do ks2[#ks2 + 1] = tostring(k) end
              table.sort(ks2)
              -- ⚠ 中文会被 URL 安全替换成下划线，看不出空/非空 ⇒ 只报长度
              local function L(v)
                if v == nil then return 'NIL' end
                return tostring(#tostring(v))
              end
              report('misCfg', 'n=' .. #ks2 ..
                     '_nameLen=' .. L(mc.name) .. '_descLen=' .. L(mc.desc) ..
                     '_bid=' .. tostring(mc.bid) .. '_type=' .. tostring(mc.type) ..
                     '_keys=' .. table.concat(ks2, ',', 1, math.min(#ks2, 26)))
              -- ★ 分支④ 的第一个门禁是 `vo:getConfig().progress == nil then return`
              --   所以这里专门量 progress：为 nil 就直接解释了"没写 mis_content"。
              local p = rawget(mc, 'progress')
              local pn = 'NIL'
              if type(p) == 'table' then
                local c = 0
                for _ in pairs(p) do c = c + 1 end
                pn = 'table_n' .. c
              elseif p ~= nil then
                pn = type(p)
              end
              report('misProg', 'progress=' .. pn ..
                     '_type=' .. tostring(mc.type) ..
                     '_status=' .. tostring(vo.mis_status))

              -- ★★★ 分支④ 里用 progress 的第一处是 `prog[vo.mis_status]`（@76-80）。
              --   这里把 progress 的**键**和 prog[mis_status] 的类型都报出来，
              --   就能判断是"键不匹配"还是"后面还有别的门禁"。
              if type(p) == 'table' then
                local ks = {}
                for k, v in pairs(p) do
                  ks[#ks + 1] = tostring(k) .. ':' .. tostring(type(v))
                end
                table.sort(ks)
                local st = vo.mis_status
                local step = p[st]
                report('progStep', 'status=' .. tostring(st) ..
                       '_p_status=' .. tostring(type(step)) ..
                       '_keys=' .. table.concat(ks, ',', 1, math.min(#ks, 12)))
              end

              -- ★★ 区分 A/B：原始配置表 vs VO 里的 mis_config
              --   A：原始 progress 非空、VO 空 ⇒ 对象拷贝丢字段
              --   B：两者都空 ⇒ 该任务本就没 progress，改挑别的任务
              if not _G.__dsh_cfgcmp then
                pcall(function()
                  local CFG = _G.Config
                  local raw = nil
                  if type(CFG) == 'table' and type(CFG.Mission) == 'table' then
                    raw = CFG.Mission[vo.mis_bid] or CFG.Mission[tostring(vo.mis_bid)]
                  end
                  local function dsc(p)
                    if p == nil then return 'NIL' end
                    if type(p) ~= 'table' then return type(p) end
                    local c = 0
                    for _ in pairs(p) do c = c + 1 end
                    return 'table_n' .. c
                  end
                  local rawProg = (type(raw) == 'table') and dsc(raw.progress) or 'noRaw'
                  _G.__dsh_cfgcmp = true
                  report('cfgCmp', 'bid=' .. tostring(vo.mis_bid) ..
                         '_rawType=' .. type(raw) ..
                         '_rawProgress=' .. rawProg ..
                         '_voProgress=' .. dsc(mc.progress) ..
                         '_sameTable=' .. tostring(raw == mc))

                  -- ★★★ 既然 10010 的 progress 本来就空，就枚举整张 Config.Mission，
                  --      找出**真正有 progress 条目**的任务（运行期活表，比静态解析可靠）。
                  local total, withProg, sample = 0, 0, {}
                  for k, v in pairs(_G.Config.Mission) do
                    if type(v) == 'table' then
                      total = total + 1
                      local c = 0
                      if type(v.progress) == 'table' then
                        for _ in pairs(v.progress) do c = c + 1 end
                      end
                      if c > 0 then
                        withProg = withProg + 1
                        if #sample < 10 then
                          sample[#sample + 1] = tostring(k) .. ':' .. c ..
                                                ':t' .. tostring(v.type)
                        end
                      end
                    end
                  end
                  table.sort(sample)
                  report('scanMis', 'total=' .. total .. '_withProg=' .. withProg ..
                         '_sample=' .. table.concat(sample, ','))
                end)
              end
            else
              report('misCfg', 'type=' .. type(mc))
            end
          else
            report('misVO', 'type=' .. type(vo))
          end
          return vo
        end
        report('misHook', 'createMis wrapped')
      else
        report('misHook', 'createMis_not_function_' .. tostring(type(orig)))
      end
      local oh = MissionCtrl.handle12400
      if type(oh) == 'function' then
        MissionCtrl.handle12400 = function(self, resp, ...)
          local n, f = 'na', ''
          pcall(function()
            local t = resp and resp.mission_list
            if type(t) == 'table' then
              local c = 0
              for _ in pairs(t) do c = c + 1 end
              n = tostring(c)
              local e = t[1]
              if type(e) == 'table' then
                f = 'p1=' .. tostring(e.mission_bid) .. '_st=' ..
                    tostring(e.mission_status) .. '_ps=' .. tostring(e.process_status) ..
                    '_tg=' .. tostring(e.target) .. '_tv=' .. tostring(e.target_value) ..
                    '_v=' .. tostring(e.value)
              end
            end
          end)
          report('h12400', 'list=' .. n .. '_' .. f)
          return oh(self, resp, ...)
        end
      end

      -- ★★ 决定性取证：dump MissionCtrl.getConfig 的返回值
      --   追踪栏第二行是 desc_label:setString(self:getConfig().desc)，
      --   而第 1 行 getConfig().name 正常、第 2 行 desc 却是 nil —— 矛盾就在这里。
      if not _G.__dsh_getcfg_hooked then
        local og = MissionCtrl.getConfig
        if type(og) == 'function' then
          _G.__dsh_getcfg_hooked = true
          MissionCtrl.getConfig = function(self, bid, ...)
            local cfg = og(self, bid, ...)
            if type(cfg) == 'table' then
              local ks = {}
              for k, v in pairs(cfg) do
                ks[#ks + 1] = tostring(k) .. '=' .. tostring(v)
              end
              table.sort(ks)
              report('getCfg', 'bid=' .. tostring(bid) .. '_fields=' .. #ks ..
                     '_name=[' .. tostring(cfg.name) .. ']_desc=[' ..
                     tostring(cfg.desc) .. ']_' ..
                     table.concat(ks, ',', 1, math.min(#ks, 22)))
            else
              report('getCfg', 'bid=' .. tostring(bid) .. '_type=' .. type(cfg))
            end
            return cfg
          end
          report('getCfgHook', 'wrapped')
        else
          report('getCfgHook', 'not_function_' .. tostring(type(og)))
        end
      end
    end

    -- ★★ 包住 MissionUtil.missionContent：看它给我们的任务走了哪条分支、
    --    以及调用后 mis_content 有没有被填上。
    --    依据：mission_util proto[68] @253 GSET 'MissionUtil' → @256 TSETS 'missionContent'，
    --    即 missionContent 是全局类 MissionUtil 上的方法（proto[0]，params=1）。
    if not _G.__dsh_mc_hooked and type(MissionUtil) == 'table'
       and type(MissionUtil.missionContent) == 'function' then
      _G.__dsh_mc_hooked = true
      local origmc = MissionUtil.missionContent
      local function L2(v)
        if v == nil then return 'NIL' end
        return tostring(#tostring(v))
      end
      MissionUtil.missionContent = function(vo, ...)
        local b = (type(vo) == 'table') and vo.mis_content or nil
        local r = origmc(vo, ...)
        local a = (type(vo) == 'table') and vo.mis_content or nil
        report('mcCall', 'bid=' .. tostring(type(vo) == 'table' and vo.mis_bid) ..
               '_mtype=' .. tostring(type(vo) == 'table' and vo.mis_type) ..
               '_lnum=' .. tostring(type(vo) == 'table' and vo.loop_num) ..
               '_tval=' .. tostring(type(vo) == 'table' and vo.mis_target_value) ..
               '_before=' .. L2(b) .. '_after=' .. L2(a))
        return r
      end
      report('mcHook', 'missionContent wrapped')
    end

    -- ★ Phase 4B 确定性验证：客户端每轮请求集合不同，改为**主动调用它自己的 sender**
    --   （sender 名由反汇编得出：RoleCtrl.sender10302 / CircleCtrl.send13340 /
    --     TitleCtrl.send14901），从而稳定地让这三条被发出并验证服务端应答。
    if S.asyncDone and not _G.__dsh_sent4b and S.t >= 120 then
      _G.__dsh_sent4b = true
      local function trysend(label, fn)
        local ok, err = pcall(fn)
        report('send4b', label .. '_ok=' .. tostring(ok) .. '_err=' .. tostring(err))
      end
      if type(RoleCtrl) == 'table' and type(RoleCtrl.sender10302) == 'function' then
        trysend('10302', function() RoleCtrl:getInstance():sender10302() end)
      else
        report('send4b', '10302_no_sender')
      end
      if type(CircleCtrl) == 'table' and type(CircleCtrl.send13340) == 'function' then
        trysend('13340', function() CircleCtrl:getInstance():send13340() end)
      else
        report('send4b', '13340_no_sender')
      end
      if type(TitleCtrl) == 'table' and type(TitleCtrl.send14901) == 'function' then
        trysend('14901', function() TitleCtrl:getInstance():send14901() end)
      else
        report('send4b', '14901_no_sender')
      end
      -- 10331：SkillCtrl:learn(skill_bid)（反汇编 skill_ctrl proto[14] 得出，
      --   params=2，直接取 skill_bid 塞进 CS_10331）
      if type(SkillCtrl) == 'table' and type(SkillCtrl.learn) == 'function' then
        trysend('10331', function() SkillCtrl:getInstance():learn(1001) end)
      else
        report('send4b', '10331_no_sender')
      end
      -- 10303：RoleCtrl.sender10303()（角色属性 + attr 大表）—— Phase 4D 新增
      if type(RoleCtrl) == 'table' and type(RoleCtrl.sender10303) == 'function' then
        trysend('10303', function() RoleCtrl:getInstance():sender10303() end)
      else
        report('send4b', '10303_no_sender')
      end
    end

    -- ★★ Phase 4C 取证：包住 RoleCtrl 的 10301/10302 处理器，确认客户端**真的解析**
    --    （之前只验了"服务端应答"，没验"客户端读取"）。同时对比处理后的 RoleVo 字段。
    if not _G.__dsh_role_hooked and type(RoleCtrl) == 'table' then
      _G.__dsh_role_hooked = true
      for _, nm in ipairs({'rgp_hander10301', 'rgp_hander10302', 'hander10333',
                           'rgp_hander10303'}) do
        local orig = RoleCtrl[nm]
        if type(orig) == 'function' then
          RoleCtrl[nm] = function(self, resp, ...)
            local info = ''
            pcall(function()
              if type(resp) == 'table' then
                local parts = {}
                for _, k in ipairs({'rid', 'name', 'lev', 'exp', 'exp_max',
                                    'gold', 'gold_acc', 'career', 'sex',
                                    'skill_list'}) do
                  local v = resp[k]
                  if type(v) == 'table' then
                    local c = 0
                    for _ in pairs(v) do c = c + 1 end
                    parts[#parts + 1] = k .. ':#' .. c
                  else
                    parts[#parts + 1] = k .. '=' .. tostring(v)
                  end
                end
                info = table.concat(parts, ',')
              end
            end)
            report('roleH', nm .. '_' .. info)
            local r = orig(self, resp, ...)
            -- 处理器跑完后，看 RoleVo 里有没有留下数据
            local vo = ''
            pcall(function()
              local v = RoleCtrl:getInstance():getRoleVo()
                 or RoleCtrl:getInstance():getSelfRoleVo()
              if type(v) == 'table' then
                vo = 'vo_lev=' .. tostring(v.lev) .. '_exp=' .. tostring(v.exp) ..
                     '_gold=' .. tostring(v.gold) .. '_gold_acc=' .. tostring(v.gold_acc) ..
                     '_name=' .. tostring(v.name)
              else
                vo = 'vo_type=' .. type(v)
              end
            end)
            report('roleVoAfter', nm .. '_' .. vo)
            return r
          end
        else
          report('roleH', nm .. '_NOT_function_' .. tostring(type(orig)))
        end
      end
    end

    -- ★★ Phase 4D：主动打开原版角色面板
    --   入口由反汇编得出：RoleCtrl 的 open 系列方法
    --     openMainPanel（主角色面板）/ openHeroPanel / openRoleHeroPanel /
    --     openOtherRole / openPointPanel / openChangeEffectPanel / …
    --   进场景后延迟调用，并上报结果，观察它随后请求了哪些协议。
    if S.asyncDone and not _G.__dsh_openrole and S.t >= 200 then
      _G.__dsh_openrole = true
      local function tryopen(label, fn)
        local ok, err = pcall(fn)
        report('openRole', label .. '_ok=' .. tostring(ok) .. '_err=' .. tostring(err))
      end
      if type(RoleCtrl) == 'table' then
        -- 依次尝试 RoleCtrl 的 open 系列（openMainPanel 试过：调用成功但面板没出现）
        for _, m in ipairs({'openRoleHeroPanel', 'openHeroPanel', 'openMainPanel'}) do
          if type(RoleCtrl[m]) == 'function' then
            tryopen(m, function() RoleCtrl:getInstance()[m](RoleCtrl:getInstance()) end)
          else
            report('openRole', m .. '_not_function')
          end
        end
      else
        report('openRole', 'no_RoleCtrl')
      end
    end

    -- ★★ Phase 5A 取证：包住 NpcCtrl 的点击入口，判定"点击是否命中 NPC"
    --   依据：反汇编 npc_ctrl proto[17] 得 clickNpcOpenDialog → SendProtocal(CS_15203)。
    --   用途：区分"点击没命中" 与 "命中了但没发出 15203"。
    if not _G.__dsh_npc_hooked and type(NpcCtrl) == 'table' then
      _G.__dsh_npc_hooked = true
      for _, nm in ipairs({'clickNpcOpenDialog', 'sceneClickEvt', 'setOpenNpc',
                           'open', 'openElemDialogs', 'elemDialog'}) do
        local orig = NpcCtrl[nm]
        if type(orig) == 'function' then
          NpcCtrl[nm] = function(self, ...)
            local n = select('#', ...)
            local a1 = select(1, ...)
            local info = '_n=' .. n
            if type(a1) == 'table' then
              info = info .. '_bid=' .. tostring(a1.bid) .. '_id=' .. tostring(a1.id) ..
                     '_name=' .. tostring(a1.name) .. '_x=' .. tostring(a1.x) ..
                     '_y=' .. tostring(a1.y)
            elseif a1 ~= nil then
              info = info .. '_arg=' .. tostring(a1)
            end
            report('npcH', nm .. info)
            return orig(self, ...)
          end
          report('npcH', nm .. '_wrapped')
        else
          report('npcH', nm .. '_NOT_function_' .. tostring(type(orig)))
        end
      end
    end

    -- ★★ Phase 5A 续：包住场景 NPC 实体的点击注册与回调
    --   依据：反汇编 scene/element/npc.luac 得
    --     proto[4] registEvent()  → container:setTouchEnabled(true)
    --                              container:addTouchEventListener(<closure>)
    --     proto[5] clickHandler() → 点击回调
    --   用途：判定 NPC 的点击体到底有没有注册、点击时回调有没有被触发。
    if not _G.__dsh_npc2 and type(Npc) == 'table' then
      _G.__dsh_npc2 = true
      -- ★ 闭包局部计数器：与下面的 Npc 包装器**同一作用域**，保证共享
      --   （_G / 类表 / S 三处存储都失败了，故改用闭包局部）
      local npcTries = 0
      local npcEntity = nil
      -- 先包住 NpcDialogs 的打开函数，便于观察 UI 是否被拉起
      if type(NpcDialogs) == 'table' then
        for _, dn in ipairs({'openNpc', 'open', 'openDefault', 'initMis'}) do
          local od = NpcDialogs[dn]
          if type(od) == 'function' then
            NpcDialogs[dn] = function(self, ...)
              local a1 = select(1, ...)
              report('dlgH', dn .. '_type=' .. type(a1) ..
                     '_bid=' .. tostring(type(a1) == 'table' and a1.bid))
              return od(self, ...)
            end
            report('dlgH', dn .. '_wrapped')
          else
            report('dlgH', dn .. '_NOT_function_' .. tostring(type(od)))
          end
        end
      else
        report('dlgH', 'no_NpcDialogs')
      end
      for _, nm in ipairs({'registEvent', 'clickHandler', 'setVo'}) do
        local orig = Npc[nm]
        if type(orig) == 'function' then
          Npc[nm] = function(self, ...)
            local info = ''
            if type(self) == 'table' and type(self.vo) == 'table' then
              info = '_vo_bid=' .. tostring(self.vo.bid) ..
                     '_name=' .. tostring(self.vo.name)
            end
            -- ★ 从 setVo 的**参数**截获真实 NPC VO
            --   上一次存 _G 失败（原因未确认），这次挂到 NpcCtrl 类表上，
            --   与调用点引用的是同一个对象，避免跨作用域丢失。
            if nm == 'setVo' then
              local a1 = select(1, ...)
              if type(a1) == 'table' then
                info = info .. '_arg_bid=' .. tostring(a1.bid) ..
                       '_arg_name=' .. tostring(a1.name)
                if NpcCtrl.__dsh_npc_vo == nil then NpcCtrl.__dsh_npc_vo = a1 end
                if _G.__dsh_npc_vo == nil then _G.__dsh_npc_vo = a1 end
                -- ★★ 关键：存进探针自己的状态表 S（与下面的延迟调用**同一个 chunk**），
                --    这样才能确保跨作用域不丢（_G / 类表两次都失败了）。
                if S.npc_vo == nil then S.npc_vo = a1 end
                -- ★★ 路径 1：用闭包局部计数器，等**最后一个 NPC**（场景基本就绪）时
                --    直接调 NpcDialogs 的打开函数，绕开点击链与传值问题。
              -- ★ 闭包局部保存 NPC 实体（存 _G / 类表都失败过，闭包局部可靠）
              if nm == 'setVo' then npcEntity = self end
              -- ★★ 走**原版真实链路**：直接调 Npc 实体自己的点击回调
              npcTries = npcTries + 1
              if npcTries >= 25 and type(npcEntity) == 'table' then
                local okc, errc = pcall(function()
                  npcEntity:clickHandler()
                end)
                report('dlgOpen', 'tries=' .. npcTries ..
                       '_entity:clickHandler()_ok=' .. tostring(okc) ..
                       '_err=' .. tostring(errc))
              end
              end
            end
            report('npcE', nm .. info)
            return orig(self, ...)
          end
          report('npcE', nm .. '_wrapped')
        else
          report('npcE', nm .. '_NOT_function_' .. tostring(type(orig)))
        end
      end
    end

    -- ★★ Phase 5A 收尾（只观察，不改服务器协议）：
    --   主动调用客户端的 NPC 点击入口，抓 CS_15203 并确认服务器收到。
    --   依据：反汇编 npc_ctrl proto[17] clickNpcOpenDialog → SendProtocal(GetPrototype(15203))
    if S.asyncDone and not _G.__dsh_npc_click and S.t >= 190 then
      _G.__dsh_npc_click = true
      local vo = _G.__dsh_npc_vo
      report('npcClick', 'vo_type=' .. type(vo) ..
             '_bid=' .. tostring(type(vo) == 'table' and vo.bid))
      if type(NpcCtrl) == 'table' and type(NpcCtrl.clickNpcOpenDialog) == 'function' then
        local ok, err = pcall(function()
          NpcCtrl:getInstance():clickNpcOpenDialog(vo)
        end)
        report('npcClick', 'clickNpcOpenDialog_ok=' .. tostring(ok) ..
               '_err=' .. tostring(err))
      else
        report('npcClick', 'NpcCtrl.clickNpcOpenDialog_not_function')
      end
    end

    -- ★★ Phase 5B：直接发出 CS_15203（绕开 clickNpcOpenDialog 里的 npc_dialogs 段）
    --   依据：npc_ctrl proto[17] 里就是 GetPrototype(15203) → SendProtocal；
    --   这里只做"发送"，不碰 UI，先验证"能发/能收"。
    if S.asyncDone and not _G.__dsh_npc_send and S.t >= 190 then
      _G.__dsh_npc_send = true
      if type(NpcCtrl) == 'table' then
        local ctrl = NpcCtrl:getInstance()
        -- ① 先直接发 CS_15203（已验证可发可收）
        local ok, err = pcall(function()
          local mgr = ProtocalRulesMgr:getInstance()
          ctrl:SendProtocal(mgr:GetPrototype(15203))
        end)
        report('npcSend', '15203_SendProtocal_ok=' .. tostring(ok) ..
               '_err=' .. tostring(err))
        -- ② 带**真实 vo** 调 clickNpcOpenDialog
        --    说明：之前"当场在 setVo 里调"虽然拿得到 vo，但那时场景 UI 还没就绪
        --    （npc_dialogs 报 attempt to index a nil value）⇒ 必须等场景就绪后再调，
        --    同时 vo 改存到探针状态表 S.npc_vo 以保证跨作用域不丢。
        local vo = S.npc_vo or NpcCtrl.__dsh_npc_vo or _G.__dsh_npc_vo
        report('npcSend', 'vo_S=' .. type(S.npc_vo) ..
               '_bid=' .. tostring(type(vo) == 'table' and vo.bid))
        if type(vo) == 'table' and type(NpcCtrl.clickNpcOpenDialog) == 'function' then
          local ok2, err2 = pcall(function()
            NpcCtrl:getInstance():clickNpcOpenDialog(vo)
          end)
          report('npcSend', 'clickNpcOpenDialog_ok=' .. tostring(ok2) ..
                 '_err=' .. tostring(err2))
        end
      else
        report('npcSend', 'no_NpcCtrl')
      end
    end

    -- ★ Phase 5B：包住 handle15203，确认客户端解析了 SC_15203
    if not _G.__dsh_h15203 and type(NpcCtrl) == 'table'
       and type(NpcCtrl.handle15203) == 'function' then
      _G.__dsh_h15203 = true
      local o = NpcCtrl.handle15203
      NpcCtrl.handle15203 = function(self, resp, ...)
        local info = ''
        if type(resp) == 'table' then
          info = '_code=' .. tostring(resp.code) .. '_msg=' .. tostring(resp.msg)
        end
        report('npcH2', 'handle15203' .. info)
        return o(self, resp, ...)
      end
      report('npcH2', 'handle15203_wrapped')
    end

    -- ★★ Phase 5H：触发"提交任务"（NPC 对话 UI 尚不可达，故用客户端自己的入口）
    --   依据：反汇编 mission_ctrl proto[40]：
    --     MissionCtrl:submit(mission_bid) → GetPrototype(12403) → SendProtocal
    if S.asyncDone and not _G.__dsh_submit and S.t >= 210 then
      _G.__dsh_submit = true
      if type(MissionCtrl) == 'table' and type(MissionCtrl.submit) == 'function' then
        -- 当前剧情链头（10010 已完成 ⇒ 本次提交 10020「切磋魂技」，它带进度条件）
        local bid = 10020
        local ok, err = pcall(function()
          MissionCtrl:getInstance():submit(bid)
        end)
        report('submit', 'MissionCtrl.submit(' .. bid .. ')_ok=' .. tostring(ok) ..
               '_err=' .. tostring(err))
      else
        report('submit', 'MissionCtrl.submit_not_function')
      end
    end

    -- ★★ Phase F3：包住"自动寻路"入口，观察它解析出什么目标
    --   依据：mission_util proto[7] = MissionUtil.missionGoto（3588 条字节码），
    --        内部按条件分派 → findVoTarget → moveToAutomate。
    --   做法：只包不改，然后**点击任务追踪栏**，让客户端自己调用它。
    --   ⚠ 自查修正：标志只在**成功包裹**时才置位（原先无条件置位 ⇒ MissionUtil
    --     尚未创建时就永久放弃重试，实测报过 `missionGoto_not_available`）。
      if not _G.__dsh_goto2 and type(MissionUtil) == 'table'
         and type(MissionUtil.missionGoto) == 'function' then
        _G.__dsh_goto2 = true
        -- ★ 端到端回归开关：正式游玩置 false（回归脚本不再自动驱动角色）。
        --   需要复跑回归时置 true 并重新构建即可。
        _G.__dsh_e2e = false
        _G.__dsh_requery = true

        -- 门禁快照：mission_util proto#8（gotoTarget）里 7 道 early-return 的条件值
        local function gateSnap()
          local o = {}
          local function g(k, f)
            local ok, v = pcall(f)
            o[k] = ok and tostring(v) or 'ERR'
          end
          g('fight', function() return Battle:getInstance():inFight() end)
          g('teamFollow', function() return SceneModel:getInstance():isOnTeamFollow() end)
          g('convoy', function() return ConVoyCtrl:getInstance():isConvoyState() end)
          g('story', function() return StoryCtrl:getInstance():getData():isStoryState() end)
          g('xm', function() return SceneModel:getInstance():getIsOnXM() end)
          g('fb', function() return SceneModel:getInstance():getIsOnFB() end)
          g('scene', function() return type(SceneModel:getInstance():getScene()) end)
          return 'fight:' .. o.fight .. '_teamFollow:' .. o.teamFollow ..
                 '_convoy:' .. o.convoy .. '_story:' .. o.story ..
                 '_xm:' .. o.xm .. '_fb:' .. o.fb .. '_sceneType:' .. o.scene
        end

        -- ① 入口 missionGoto
        local oGoto = MissionUtil.missionGoto
        MissionUtil.missionGoto = function(vo, ...)
          local info
          if type(vo) == 'table' then
            info = 'bid:' .. tostring(vo.mis_bid) .. '_type:' .. tostring(vo.mis_type) ..
                   '_status:' .. tostring(vo.mis_status) .. '_code:' .. tostring(vo.mis_code)
          else
            info = 'argtype:' .. type(vo)
          end
          report('gt2', 'missionGoto_' .. info)
          report('gt2', 'GATE1@missionGoto_' .. gateSnap())
          local r = oGoto(vo, ...)
          report('gt2', 'missionGoto_returned')
          return r
        end
        report('gt2', 'missionGoto_wrapped')

        -- ② moveToNpc（真正的"走到某 NPC"，proto#38）
        if type(MissionUtil.moveToNpc) == 'function' then
          local oM = MissionUtil.moveToNpc
          MissionUtil.moveToNpc = function(npcId, ...)
            local hit = 'nil'
            pcall(function()
              local e = Config and Config.MapNpc and Config.MapNpc[npcId]
              if e then
                hit = 'scene:' .. tostring(e[1]) .. '_x:' .. tostring(e[2]) ..
                      '_y:' .. tostring(e[3])
              else
                hit = 'notInMapNpc'
              end
            end)
            report('gt2', 'moveToNpc_npc:' .. tostring(npcId) .. '_cfg_' .. hit)
            local r = oM(npcId, ...)
            report('gt2', 'moveToNpc_returned')
            return r
          end
          report('gt2', 'moveToNpc_wrapped')
        end

        -- ③ gotoTarget（真正的派发，proto#8）
        if type(MissionUtil.gotoTarget) == 'function' then
          local oT = MissionUtil.gotoTarget
          MissionUtil.gotoTarget = function(ftype, sceneId, x, y, monBid, npcId, ptBid, open, ...)
            report('gt2', 'gotoTarget_type:' .. tostring(ftype) .. '_scene:' .. tostring(sceneId) ..
                   '_x:' .. tostring(x) .. '_y:' .. tostring(y) .. '_mon:' .. tostring(monBid) ..
                   '_npc:' .. tostring(npcId))
            report('gt2', 'GATE2@gotoTarget_' .. gateSnap())
            local r = oT(ftype, sceneId, x, y, monBid, npcId, ptBid, open, ...)
            report('gt2', 'gotoTarget_returned')
            return r
          end
          report('gt2', 'gotoTarget_wrapped')
        end

        -- ④ moveToAutomate（proto#39）
        if type(MissionUtil.moveToAutomate) == 'function' then
          local oA = MissionUtil.moveToAutomate
          MissionUtil.moveToAutomate = function(sceneId, ...)
            report('gt2', 'moveToAutomate_scene:' .. tostring(sceneId))
            local r = oA(sceneId, ...)
            report('gt2', 'moveToAutomate_returned')
            return r
          end
          report('gt2', 'moveToAutomate_wrapped')
        end

        -- ⑤ 最后一跳：SceneModel:getInstance():getScene():gotoTarget(vo)
        --    ⚠ 这是**实例方法**，必须拿到实例后再包；包类表是包不到的。
        if type(SceneModel) == 'table' and type(SceneModel.getInstance) == 'function' then
          local oInst = SceneModel.getInstance
          SceneModel.getInstance = function(self, ...)
            local inst = oInst(self, ...)
            if type(inst) == 'table' and not inst.__dsh_sm then
              inst.__dsh_sm = true
              if type(inst.getScene) == 'function' then
                local oGS = inst.getScene
                inst.getScene = function(s, ...)
                  local sc = oGS(s, ...)
                  if type(sc) == 'table' and not sc.__dsh_gp
                     and type(sc.gotoTarget) == 'function' then
                    sc.__dsh_gp = true
                    local oSG = sc.gotoTarget
                    sc.gotoTarget = function(s2, vo, ...)
                      local p = 'nil'
                      if type(vo) == 'table' and vo.pos then
                        p = tostring(vo.pos.x) .. ',' .. tostring(vo.pos.y)
                      end
                      report('gt2', 'SCENE.gotoTarget_type:' ..
                             tostring(type(vo) == 'table' and vo.type) ..
                             '_scene:' .. tostring(type(vo) == 'table' and vo.sceneId) ..
                             '_npc:' .. tostring(type(vo) == 'table' and vo.npcId) ..
                             '_bid:' .. tostring(type(vo) == 'table' and vo.bid) ..
                             '_pos:' .. p)
                      return oSG(s2, vo, ...)
                    end
                    report('gt2', 'SCENE.gotoTarget_wrapped')
                  end
                  return sc
                end
              end
            end
            return inst
          end
          report('gt2', 'SceneModel.getInstance_wrapped')

        -- ★ NPC 对话诊断：点完 NPC 后报告"对话框实例 + NPC 任务管理器"的真实状态。
        --   用于定位 `NpcDialogs:openNpc` 之后**面板为何不显示**。
        if not _G.__dsh_dlg_probe and type(NpcDialogs) == 'table'
           and type(NpcDialogs.openNpc) == 'function' then
          _G.__dsh_dlg_probe = true
          local oON = NpcDialogs.openNpc
          NpcDialogs.openNpc = function(self, bid, ...)
            report('dlgS', 'enter_bid:' .. tostring(bid))
            -- 调用前：NPC 任务管理器里有没有这个 NPC
            pcall(function()
              local c = NpcCtrl:getInstance()
              local nl = c.manager and c.manager.npc_list
              local n = 0
              if type(nl) == 'table' then for _ in pairs(nl) do n = n + 1 end end
              local has = 'no'
              if type(nl) == 'table' and nl[bid] ~= nil then
                has = 'yes_can:' .. tostring(nl[bid].can_count) ..
                      '_acc:' .. tostring(nl[bid].access_count) ..
                      '_fin:' .. tostring(nl[bid].finish_count)
              end
              report('dlgS', 'manager_npc_n:' .. n .. '_has:' .. has)
            end)
            local r = oON(self, bid, ...)
            local vis = 'na'
            pcall(function() vis = tostring(self.root_wnd:isVisible()) end)
            local sz = 'na'
            pcall(function()
              local s = self.root_wnd:getContentSize()
              sz = tostring(s.width) .. 'x' .. tostring(s.height)
            end)
            local bl, bls = 'na', 'na'
            pcall(function()
              local n = 0
              for _ in pairs(self.btn_list or {}) do n = n + 1 end
              bl = tostring(n)
              local t = {}
              for k, _ in pairs(self.btn_list or {}) do
                t[#t + 1] = tostring(k)
              end
              bls = table.concat(t, '|')
            end)
            report('dlgS', 'after_rootwnd:' .. type(self.root_wnd) ..
                   '_vis:' .. vis .. '_size:' .. sz ..
                   '_mis_vo:' .. type(self.mis_vo) .. '_btns:' .. bl .. ':' .. bls)
            return r
          end
          report('dlgS', 'openNpc_wrapped')
        end

        -- ★ 存下**真实收到**的 12400 响应，供"重放实验"使用（不造数据）
        if not _G.__dsh_at12400 and type(MissionCtrl) == 'table'
           and type(MissionCtrl.handle12400) == 'function' then
          _G.__dsh_at12400 = true
          local oH = MissionCtrl.handle12400
          MissionCtrl.handle12400 = function(self, resp, ...)
            _G.__dsh_last12400 = resp
            if resp == nil then
              -- ★ resp 为 nil 时打一条**调用栈**，定位是谁用 nil 调进来的
              local tb = 'na'
              pcall(function() tb = debug.traceback('', 2) end)
              report('rq', 'NIL_CALLER_' .. tostring(tb))
            end
            local n = 'nil'
            pcall(function() n = tostring(#(resp.mission_list or {})) end)
            report('rq', 'handle12400_in_list:' .. n)
            return oH(self, resp, ...)
          end
          report('rq', 'handle12400_wrapped')
        end
        end

        -- ⑥ 位置采样 + 主动触发（用于判定"客户端自身到底会不会走"）
        pcall(function()
          local sch3 = cc.Director:getInstance():getScheduler()
          local n = 0
          local e3
          local function tick3()
            n = n + 1
            local pos = 'ERR'
            pcall(function()
              local vo = GameData:getInstance():getRoleVo()
              pos = tostring(vo.x) .. ',' .. tostring(vo.y)
            end)
            if n % 5 == 0 or n == 1 then
              report('pos', 'n:' .. n .. '_xy:' .. pos)
            end
            -- =========================================================
            -- ★ Phase G：端到端回归序列（脚本化，只在本轮测试构建里打开）
            --   步骤：任务列表快照 → 自动寻路(可解析目标) → 位移确认
            --         → 提交 → 奖励 → 链推进 → 再快照
            --   开关：`_G.__dsh_e2e`（脚本内置为 true 时执行）
            -- =========================================================
            if not _G.__dsh_e2e and not _G.__dsh_requery then return end

            -- ===== 实验：NPC 任务管理器为什么是空的？ =====
            -- 依据：`npc_ctrl.luac` proto#16 `registerEvents` 把
            --   `NpcContants.ADD_MISSION` 绑到 `NpcCtrl:addNpc`；
            --   而 `mission_ctrl.luac` proto#31 (`handle12400`) 才会 Fire 它。
            -- 猜想：12400 到达时 NpcCtrl 还没绑定事件 ⇒ 事件丢失 ⇒ manager 空。
            -- 验证：先确保 NpcCtrl 已实例化，再用**上一次真实收到的 12400 响应**
            --       重放一次（不造数据），然后看 manager 是否被填满。
            if _G.__dsh_requery then
              if n == 62 then
                local ok1, e1 = pcall(function() NpcCtrl:getInstance() end)
                report('rq', 'ensure_NpcCtrl_ok:' .. tostring(ok1) ..
                       '_err:' .. tostring(e1))
                local n0 = -1
                pcall(function()
                  local nl = NpcCtrl:getInstance().manager.npc_list
                  n0 = 0
                  for _ in pairs(nl or {}) do n0 = n0 + 1 end
                end)
                report('rq', 'before_manager_npc_n:' .. tostring(n0))
                if type(MissionCtrl) == 'table'
                   and type(MissionCtrl.handle12400) == 'function'
                   and _G.__dsh_last12400 then
                  local ok2, e2 = pcall(function()
                    MissionCtrl:getInstance():handle12400(_G.__dsh_last12400)
                  end)
                  report('rq', 'replay_handle12400_ok:' .. tostring(ok2) ..
                         '_err:' .. tostring(e2))
                else
                  report('rq', 'replay_unavailable_last:' ..
                         tostring(type(_G.__dsh_last12400)))
                end
              end
              if n == 66 then
                local n1 = -1
                pcall(function()
                  local nl = NpcCtrl:getInstance().manager.npc_list
                  n1 = 0
                  for _ in pairs(nl or {}) do n1 = n1 + 1 end
                end)
                report('rq', 'after_manager_npc_n:' .. tostring(n1))
              end
              if n ~= 62 and n ~= 66 then return end
            end

            -- 任务列表快照（对 MissionCtrl 的数据做**防御式**统计）
            local function misSnap(tag)
              local ok, s = pcall(function()
                local md = MissionCtrl:getInstance():getMissionData()
                if type(md) ~= 'table' then return 'md_type:' .. type(md) end
                local tops = {}
                for k in pairs(md) do tops[#tops + 1] = tostring(k) end
                table.sort(tops)
                local function cnt(t)
                  local c = 0
                  if type(t) == 'table' then for _ in pairs(t) do c = c + 1 end end
                  return c
                end
                local function keys(t, lim)
                  local o = {}
                  if type(t) == 'table' then
                    for k in pairs(t) do o[#o + 1] = tostring(k) end
                    table.sort(o)
                    while #o > lim do table.remove(o) end
                  end
                  return table.concat(o, '|')
                end
                return 'tops[' .. table.concat(tops, ',') .. ']' ..
                       '_receive_n:' .. cnt(md.receive_list) ..
                       '_can_n:' .. cnt(md.can_list) ..
                       '_finish_n:' .. cnt(md.finish_list) ..
                       '_recv_keys:' .. keys(md.receive_list, 12)
              end)
              report('e2e', tag .. '_' .. (ok and s or ('ERR_' .. tostring(s))))
            end

            local function posOf()
              local p = 'ERR'
              pcall(function()
                local vo = GameData:getInstance():getRoleVo()
                p = tostring(vo.x) .. ',' .. tostring(vo.y)
              end)
              return p
            end

            if n == 28 then
              misSnap('list_before')
            end

            -- 步骤 1：先把角色**走远**（用同一个 moveToNpc 机制走到远处的 10160 @ (10,89)）
            --   注意：不能用 gotoTarget(FindType.POINT,...) —— 实测它没有产生位移，
            --   因为 POINT 分支的 vo.bid 需要 pointBid 才能真正解析。
            if n == 30 then
              _G.__dsh_pos0 = posOf()
              report('e2e', 'STEP1_walk_away_from:' .. _G.__dsh_pos0 ..
                     '_to_10160:10,89')
              if type(MissionUtil.moveToNpc) == 'function' then
                local ok, err = pcall(function() MissionUtil.moveToNpc(10160) end)
                report('e2e', 'STEP1_moveToNpc_10160_ok:' .. tostring(ok) ..
                       '_err:' .. tostring(err))
              end
            end

            -- 步骤 2：确认已走远（远点 (10,89)）
            if n == 55 then
              report('e2e', 'STEP2_pos_far:' .. posOf() .. '_from:' .. tostring(_G.__dsh_pos0))
            end

            -- 步骤 3：★ 自动寻路 —— mission 10010 的提交目标 10030（周漪，MapNpc 有坐标 (70,61)）
            if n == 58 then
              _G.__dsh_pos_before = posOf()
              report('e2e', 'STEP3_autopath_before:' .. _G.__dsh_pos_before ..
                     '_target:70,61')
              if type(MissionUtil.moveToNpc) == 'function' then
                local ok, err = pcall(function() MissionUtil.moveToNpc(10030) end)
                report('e2e', 'STEP3_moveToNpc_10030_ok:' .. tostring(ok) ..
                       '_err:' .. tostring(err))
              end
            end
            if n == 78 then
              report('e2e', 'STEP4_autopath_after:' .. posOf() ..
                     '_before:' .. tostring(_G.__dsh_pos_before) .. '_target:70,61')
            end

            -- 步骤 5：提交 10010（无进度条件 ⇒ 应当成功）
            if n == 82 then
              report('e2e', 'STEP5_submit_10010_pos:' .. posOf())
              if type(MissionCtrl) == 'table'
                 and type(MissionCtrl.submit) == 'function' then
                local ok, err = pcall(function()
                  MissionCtrl:getInstance():submit(10010)
                end)
                report('e2e', 'STEP5_submit_ok:' .. tostring(ok) ..
                       '_err:' .. tostring(err))
              end
            end
            if n == 88 then
              misSnap('list_after_submit')
            end

            -- 步骤 6：已知缺口——20011（少年雨浩）不在 Config.MapNpc，且剧情场景未知
            if n == 91 then
              _G.__dsh_pos_b2 = posOf()
              report('e2e', 'STEP6_gap_20011_before:' .. _G.__dsh_pos_b2)
              if type(MissionUtil.moveToNpc) == 'function' then
                local ok, err = pcall(function() MissionUtil.moveToNpc(20011) end)
                report('e2e', 'STEP6_moveToNpc_20011_ok:' .. tostring(ok) ..
                       '_err:' .. tostring(err))
              end
            end
            if n == 100 then
              report('e2e', 'STEP7_pos_final:' .. posOf() ..
                     '_b2:' .. tostring(_G.__dsh_pos_b2))
              misSnap('list_final')
              local ok, s = pcall(function()
                local vo = GameData:getInstance():getRoleVo()
                return 'lev:' .. tostring(vo.lev) .. '_exp:' .. tostring(vo.exp) ..
                       '_gold:' .. tostring(vo.gold)
              end)
              report('e2e', 'STEP8_role_' .. (ok and s or tostring(s)))
            end

            -- =========================================================
            -- 步骤 9/10：验证**剧情链连续推进**（10010 → 10030 → 10040）
            --   10030 的提交目标是 20011（少年雨浩）—— 自动寻路够不到（已知缺口），
            --   但任务本身无进度条件，因此提交这一步可以在服务端完成。
            -- =========================================================
            local function submitBid(bid)
              if type(MissionCtrl) == 'table'
                 and type(MissionCtrl.submit) == 'function' then
                local ok, err = pcall(function()
                  MissionCtrl:getInstance():submit(bid)
                end)
                report('e2e', 'SUBMIT_' .. tostring(bid) .. '_ok:' .. tostring(ok) ..
                       '_err:' .. tostring(err))
              end
            end
            if n == 104 then
              report('e2e', 'STEP9_submit_10030_pos:' .. posOf())
              submitBid(10030)
            end
            if n == 110 then misSnap('list_after_10030') end
            if n == 114 then
              report('e2e', 'STEP10_submit_10040_pos:' .. posOf())
              submitBid(10040)
            end
            if n == 120 then
              misSnap('list_after_10040')
              local ok, s = pcall(function()
                local vo = GameData:getInstance():getRoleVo()
                return 'lev:' .. tostring(vo.lev) .. '_exp:' .. tostring(vo.exp)
              end)
              report('e2e', 'STEP11_role_final_' .. (ok and s or tostring(s)))
            end
          end
          e3 = sch3:scheduleScriptFunc(tick3, 1.0, false)
          report('gt2', 'posTicker_installed')
        end)
      end

    -- ★★ 探索：枚举 SceneModel / NpcCtrl 实例的**字段名**，
    --   目的是找到 "NPC vo 列表" 的真实字段名（上一轮 vo_false 的原因）。
    --   URL 限长 ⇒ 每 tick 报 3 个键，直到报完。
    if not _G.__dsh_scan and type(SceneModel) == 'table' then
      _G.__dsh_scan = { i = 0, keys = {} }
      pcall(function()
        local sm = SceneModel:getInstance()
        for k, v in pairs(sm) do
          _G.__dsh_scan.keys[#_G.__dsh_scan.keys + 1] =
            tostring(k) .. '=' .. type(v)
        end
        table.sort(_G.__dsh_scan.keys)
        report('smk', 'SceneModel_n' .. #_G.__dsh_scan.keys)
      end)
      pcall(function()
        local c = NpcCtrl:getInstance()
        local ks = {}
        for k, v in pairs(c) do ks[#ks + 1] = tostring(k) .. '=' .. type(v) end
        table.sort(ks)
        report('smk', 'NpcCtrl_n' .. #ks)
        _G.__dsh_scan.ctrl = ks
      end)
      pcall(function()
        local sm = SceneModel:getInstance()
        local vo = sm.vo or sm.roleVo or sm.role_vo
        report('smk', 'sm.vo=' .. tostring(vo ~= nil) ..
               (vo and ('_flds' .. tostring(vo.npc_list ~= nil)) or ''))
      end)
    end
    if _G.__dsh_scan and _G.__dsh_scan.keys and _G.__dsh_scan.i < #_G.__dsh_scan.keys then
      local a = _G.__dsh_scan.i + 1
      local b = math.min(a + 2, #_G.__dsh_scan.keys)
      local t = ''
      for j = a, b do t = t .. _G.__dsh_scan.keys[j] .. '|' end
      _G.__dsh_scan.i = b
      report('smk', t)
    elseif _G.__dsh_scan and _G.__dsh_scan.ctrl and #_G.__dsh_scan.ctrl > 0 then
      local t = ''
      for j = 1, math.min(3, #_G.__dsh_scan.ctrl) do t = t .. _G.__dsh_scan.ctrl[j] .. '|' end
      table.remove(_G.__dsh_scan.ctrl, 1)
      table.remove(_G.__dsh_scan.ctrl, 1)
      table.remove(_G.__dsh_scan.ctrl, 1)
      report('smk', 'CTRL_' .. t)
    end

    -- ★ 连接（等 net_manager；它只在 restartNetManager 里创建）
    if not S.netted and S.t >= 25 and type(GameNet) == 'table' then
      local gn = GameNet:getInstance()
      if rawget(gn, 'net_manager') ~= nil then
        S.netted = true
        local ok, err = pcall(function()
          report('netTry0', 'before_setinfo')
          gn:SetLoginServerInfo('10.0.2.2', 9000)
          report('netTry1', 'after_setinfo')
          gn:AsyncConnectLoginServer(10)
          report('netTry2', 'after_connectasyn')
        end)
        report('netTry', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
      end
    end

    -- ★ 必须尽早补上 account：request1110Role 会取 self.account 组装 args，
    --   account 为 nil 时 SendProtocal 内部 Encode 失败并**静默返回 false**，
    --   1110 根本发不出去（本轮就踩了这个：把 async 挪到 t>=200 后忘了 account
    --   还留在 t>=280 的 relogin 块里，结果整轮没有 1110）。
    if not S.acctSet and S.t >= 10 and type(DengluCtrl) == 'table' then
      S.acctSet = true
      pcall(function() DengluCtrl:getInstance().account = 'dsh_local' end)
      report('acct', 'set=' .. tostring(pcall(function()
        return DengluCtrl:getInstance().account
      end)))
    end

    -- 原生入口：gamenet proto[13] 才会正规置连接标志并发 10001/1110
    -- ★ 必须等"协议处理函数已注册"之后再发，否则 1110 的应答没有 handler 会被丢弃。
    --   denglu_ctrl proto[1] registerProtocals 里才有
    --     RegisterProtocal(1110,'on1110Rolelist') / (10102,'on10102Login') / ...
    --   实测证据：早前在 t≈45（约 9 秒）发 1110，钩子 on10102Login 命中、
    --   而 on1110Rolelist 从未命中 —— 就是因为那时还没注册。
    --   模块加载约 35 秒，故阈值放到 t>=200（约 40 秒）。
    if S.netted and not S.asyncDone and S.t >= 200
       and type(_G.OnNetAsyncConnected) == 'function' then
      S.asyncDone = true
      local ok, err = pcall(function()
        OnNetAsyncConnected(1, '10.0.2.2', 9000)
      end)
      report('async', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
    end

    -- 10103 角色重连近路（跳过角色列表直接进游戏）
    if S.asyncDone and not S.reloginDone and S.t >= 280
       and type(DengluCtrl) == 'table' then
      pcall(function() DengluCtrl:getInstance().account = 'dsh_local' end)
      S.reloginDone = true
      local ok, err = pcall(function()
        DengluCtrl:getInstance():request10103ReLogin(1001, '1')
      end)
      report('relogin', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err))
    end

    -- ★★★ NPC vo：遍历 SceneModel.elementList，筛 ObjType.NPC(2)
    --   依据：字段扫描已证实 SceneModel.npcList 存在但**为空**，
    --   而 NPC 画面上可见 ⇒ NPC 实体应在通用的 elementList 里。
    --   取到后调原版入口：npc_ctrl proto[26] 的 clickNpcOpenDialog(vo)。
    if not _G.__dsh_el and type(SceneModel) == 'table' then
      _G.__dsh_el = true
      local ok, err = pcall(function()
        local sm = SceneModel:getInstance()
        local el = sm.elementList
        local n, nNpc, first, firstNpc = 0, 0, nil, nil
        if type(el) == 'table' then
          for k, v in pairs(el) do
            n = n + 1
            if type(v) == 'table' then
              if first == nil then first = v end
              if v.type == 2 then
                nNpc = nNpc + 1
                if firstNpc == nil then firstNpc = v end
              end
            end
          end
        end
        report('el', 'elementList_t' .. type(el) .. '_n' .. n .. '_npc' .. nNpc)
        local t = ''
        if first ~= nil then
          for _, kk in ipairs({'type', 'bid', 'id', 'name', 'sub_type'}) do
            t = t .. kk .. '=' .. tostring(first[kk]) .. '|'
          end
        end
        report('el', 'first_' .. t)
        if firstNpc ~= nil then
          local t2 = ''
          for _, kk in ipairs({'type', 'bid', 'id', 'name'}) do
            t2 = t2 .. kk .. '=' .. tostring(firstNpc[kk]) .. '|'
          end
          report('el', 'npcvo_' .. t2)
          local ctrl = nil
          pcall(function() ctrl = NpcCtrl:getInstance() end)
          if ctrl ~= nil and type(ctrl.clickNpcOpenDialog) == 'function' then
            local ok2, e2 = pcall(function() ctrl:clickNpcOpenDialog(firstNpc) end)
            report('el', 'click_ok' .. tostring(ok2) .. '_e' .. tostring(e2))
          else
            report('el', 'ctrl_missing')
          end
        else
          report('el', 'no_npc_in_elementList')
        end
      end)
      if not ok then report('el', 'block_err_' .. tostring(err)) end
    end

    -- ★★★ 包住 SC_10201 的接收 handler，看 npcs 到底存到哪里
    --   依据：scene_controller proto[7] 注册 RegisterProtocal(10201, 'on10201')
    --   背景：npcList 与 elementList 都探过、均为空 ⇒ 需看 10201 到达时的真实情况。
    if not _G.__dsh_on10201 and type(SceneController) == 'table'
       and type(SceneController.on10201) == 'function' then
      _G.__dsh_on10201 = true
      local function cnt(t)
        local n = 0
        if type(t) == 'table' then for _ in pairs(t) do n = n + 1 end end
        return n
      end
      local o = SceneController.on10201
      SceneController.on10201 = function(self, resp, ...)
        local a, b, c = 'na', 'na', 'na'
        pcall(function()
          a = cnt(resp and resp.npcs)
          b = cnt(resp and resp.mons)
          c = cnt(resp and resp.elems)
        end)
        report('n10201', 'in_npcs' .. tostring(a) .. '_mons' .. tostring(b) ..
               '_elems' .. tostring(c))
        local r = o(self, resp, ...)
        pcall(function()
          local sm = SceneModel:getInstance()
          report('n10201', 'after_npcList' .. cnt(sm.npcList) ..
                 '_elemList' .. cnt(sm.elementList) .. '_monList' .. cnt(sm.monList))
          -- ★★ 此刻 npcList 已填充 ⇒ 取 vo 并调原版对话入口
          local first, fb = nil, nil
          for _, v in pairs(sm.npcList) do
            if type(v) == 'table' then
              if first == nil then first = v end
              if fb == nil and v.bid == 10030 then fb = v end   -- 周漪（10010 的提交 NPC）
            end
          end
          report('n10201', 'vo_bid' .. tostring(first and first.bid) ..
                 '_type' .. tostring(first and first.type))
          local t = ''
          for _, kk in ipairs({'bid', 'id', 'type', 'name', 'sub_type'}) do
            t = t .. kk .. '=' .. tostring(first and first[kk]) .. '|'
          end
          report('n10201', 'first_' .. t)
          -- ★ 依据 npc_dialogs proto[9]：openNpc(x) 的 x 是 **bid 数字**（Config.Npc[x]），
          --   且实例必须已有 ctrl（否则 self.ctrl.manager 报 nil 索引）。
          local ctrl = nil
          pcall(function() ctrl = NpcCtrl:getInstance() end)
          if ctrl ~= nil then
            local v = ctrl.view
            if v == nil then
              pcall(function() v = NpcDialogs:New(); ctrl.view = v end)
            end
            if v ~= nil then
              -- ★ 修复：**强制覆盖**（之前只在 nil 时赋值，而它非 nil 但是**错误对象**）
              pcall(function() v.ctrl = ctrl end)
              report('n10201', 'forced_ctrl=' .. tostring(type(v.ctrl and v.ctrl.setOpenNpc)))
              local bid = (fb and fb.bid) or (first and first.bid) or 10150
              -- ★ 列出 _G 里名字含 Mission/Manager/Npc 的全局名（定位 manager）
              if not _G.__dsh_gscan then
                _G.__dsh_gscan = true
                local names = {}
                pcall(function()
                  for k, vv in pairs(_G) do
                    if type(k) == 'string' and #k < 40 then
                      if k:find('Mission') or k:find('Manager') or k:find('Npc') then
                        names[#names + 1] = k .. '=' .. type(vv)
                      end
                    end
                  end
                  table.sort(names)
                end)
                report('n10201', 'G_n' .. #names)
                for i = 1, math.min(#names, 12) do
                  report('n10201', 'G' .. i .. '_' .. names[i])
                end
              end
              report('n10201', 'ctrl_manager_' .. tostring(ctrl.manager ~= nil))
              report('n10201', 'view_bid' .. tostring(bid))
              local ok2, e2 = pcall(function() v:openNpc(bid) end)
              report('n10201', 'openNpc_ok' .. tostring(ok2) .. '_e' .. tostring(e2))
            else
              report('n10201', 'view_nil')
            end
          else
            report('n10201', 'ctrl_missing')
          end
        end)
        return r
      end
      report('n10201', 'SceneController.on10201_wrapped')
    end

    -- ★★ 包住 message()，抓 missionGoto 兜底里的真实 mis_code
    --   依据：mission_util proto[7] @3445-3451：
    --     message(getString('goto ---------- 该类型还木有处理:') .. mis_code)
    --   ⇒ 它会把分派键 mis_code 的实际值拼在后面。
    if not _G.__dsh_msg and type(message) == 'function' then
      _G.__dsh_msg = true
      local om = _G.message
      _G.message = function(s, ...)
        local ok = pcall(function()
          local t = tostring(s)
          if #t > 120 then t = t:sub(1, 120) end
          -- URL 只保留安全字符：把非 ASCII 换成 '_'，数字/字母保留
          t = t:gsub('[^%w%p ]', '_')
          t = t:gsub('[%c]', '')
          report('msg', t)
        end)
        return om(s, ...)
      end
      report('msg', 'message_wrapped')
    end

    -- ★★ 直接调 missionGoto 复现 Bug2（不依赖点击坐标）
    --   目的：让 mission_util proto[7] 的兜底分支跑到，
    --   从而由包住的 message() 报出真实的 mis_code。
    if not _G.__dsh_mg and type(MissionUtil) == 'table'
       and type(MissionUtil.missionGoto) == 'function' then
      _G.__dsh_mg = true
      pcall(function()
        local ctrl = MissionCtrl:getInstance()
        local vo = nil
        for _, bid in ipairs({10020, 10010, 10030}) do
          local ok, v = pcall(function() return ctrl:getMissionVo(bid) end)
          if ok and v ~= nil then vo = v; report('mg', 'vo_from_getMissionVo_bid' .. bid); break end
        end
        if vo == nil then
          pcall(function()
            local l = ctrl.mis_list or ctrl.mission_list or ctrl.misList
            if type(l) == 'table' then
              for _, v in pairs(l) do vo = v; break end
            end
          end)
        end
        if vo ~= nil then
          local cfg = nil
          pcall(function() cfg = vo:getConfig() end)
          report('mg', 'vo_bid' .. tostring(vo.mis_bid) ..
                 '_status' .. tostring(vo.mis_status) ..
                 '_code' .. tostring(vo.mis_code) ..
                 '_type' .. tostring(cfg and cfg.type))
          local ok2, e2 = pcall(function() MissionUtil.missionGoto(vo) end)
          report('mg', 'missionGoto_ok' .. tostring(ok2) .. '_e' .. tostring(e2))
        else
          report('mg', 'no_vo_found')
        end
      end)
    end

    -- ★★ ① NPC 对话：用 xpcall + debug.traceback 拿**真实行号**
    --   背景：openNpc(10030) 报 `npc_dialogs.luac:0: attempt to index a nil value`（行号 0、无堆栈）
    --   ⇒ 改用 xpcall 取 traceback，看能不能拿到真实位置。
    if not _G.__dsh_tr and type(NpcDialogs) == 'table' and type(NpcCtrl) == 'table' then
      _G.__dsh_tr = true
      local ctrl = nil
      pcall(function() ctrl = NpcCtrl:getInstance() end)
      local v = ctrl and ctrl.view
      if v == nil then pcall(function() v = NpcDialogs:New(); if ctrl then ctrl.view = v end end) end
      if v ~= nil then
        if v.ctrl == nil and ctrl ~= nil then pcall(function() v.ctrl = ctrl end) end
        local ok, err = xpcall(function() v:openNpc(10030) end,
          function(e)
            local tb = ''
            pcall(function() tb = debug.traceback('', 2) end)
            return tostring(e) .. ' @ ' .. tostring(tb)
          end)
        local t = tostring(err)
        t = t:gsub('[^%w%p ]', '_'):gsub('%s+', ' ')
        report('tr', 'ok' .. tostring(ok) .. '_' .. t:sub(1, 160))
      else
        report('tr', 'no_view')
      end
    end

    -- ★★ ② 扫 MissionCtrl 实例的**字段名 + 方法名**，找 mission vo 的访问器
    --   背景：getMissionVo/mis_list/mission_list/misList 都不对 ⇒ 必须枚举，不能猜。
    if not _G.__dsh_mcs and type(MissionCtrl) == 'table' then
      _G.__dsh_mcs = true
      local ks = {}
      pcall(function()
        for k, vv in pairs(MissionCtrl) do
          ks[#ks + 1] = tostring(k) .. '=' .. type(vv)
        end
        table.sort(ks)
      end)
      report('mcs', 'MissionCtrl_n' .. #ks)
      for i = 1, math.min(#ks, 14) do report('mcs', 'M' .. i .. '_' .. ks[i]) end
      local is = {}
      pcall(function()
        local c = MissionCtrl:getInstance()
        for k, vv in pairs(c) do is[#is + 1] = tostring(k) .. '=' .. type(vv) end
        table.sort(is)
      end)
      report('mcs', 'inst_n' .. #is)
      for i = 1, math.min(#is, 14) do report('mcs', 'I' .. i .. '_' .. is[i]) end
    end

    -- ★★ ② 运行时直接检查：NpcCtrl 上到底有没有 setOpenNpc
    --   背景：静态已证 setOpenNpc 挂在 NpcCtrl（proto[84] @130-132）；
    --   上一轮用 pairs() 枚举看不到元表方法 ⇒ 结论不可靠。这里直接取。
    if not _G.__dsh_so and type(NpcCtrl) == 'table' then
      _G.__dsh_so = true
      pcall(function()
        report('so', 'NpcCtrl_setOpenNpc=' .. tostring(type(NpcCtrl.setOpenNpc)))
        report('so', 'NpcCtrl_getOpenNpc=' .. tostring(type(NpcCtrl.getOpenNpc)))
      end)
      pcall(function()
        local inst = NpcCtrl:getInstance()
        report('so', 'inst_setOpenNpc=' .. tostring(type(inst.setOpenNpc)))
        report('so', 'inst_ctor=' .. tostring(inst ~= nil))
        -- 再看 NpcDialogs 侧
        local v = nil
        pcall(function() v = NpcDialogs:New() end)
        if v ~= nil then
          report('so', 'view_has_ctrl=' .. tostring(v.ctrl ~= nil))
          if v.ctrl == nil then pcall(function() v.ctrl = inst end) end
          report('so', 'after_ctrl_set_type=' .. tostring(type(v.ctrl and v.ctrl.setOpenNpc)))
          -- ★ 关键：强制把 ctrl 指向真的 NpcCtrl 实例（之前只在 nil 时赋值，而它**已经非 nil 但对象错**）
          local real = NpcCtrl:getInstance()
          report('so', 'real_has=' .. tostring(type(real.setOpenNpc)))
          pcall(function() v.ctrl = real end)
          report('so', 'forced_ctrl_has=' .. tostring(type(v.ctrl and v.ctrl.setOpenNpc)))
          local ok, e = pcall(function() v:openNpc(10030) end)
          report('so', 'openNpc2_ok' .. tostring(ok) .. '_e' .. tostring(e))
        end
      end)
    end

    -- ★★★ 最后一次定位：getScene / getNpcByBid / Config.Npc 哪个是 nil
    --   依据：npc_dialogs proto[8]：@5 Config.Npc[x] @9 getScene() @17 getNpcByBid(bid) @20 .vo
    if not _G.__dsh_loc and type(SceneModel) == 'table' and type(Config) == 'table' then
      _G.__dsh_loc = true
      local BID = 10030
      pcall(function()
        report('loc', 'ConfigNpc_t=' .. type(Config.Npc) ..
               '_entry=' .. tostring(Config.Npc and Config.Npc[BID] ~= nil))
      end)
      pcall(function()
        local sc = SceneModel:getInstance():getScene()
        report('loc', 'getScene_t=' .. type(sc))
        if sc ~= nil then
          report('loc', 'has_getNpcByBid=' .. tostring(type(sc.getNpcByBid)))
          if type(sc.getNpcByBid) == 'function' then
            local ok, r = pcall(function() return sc:getNpcByBid(BID) end)
            report('loc', 'byBid_ok=' .. tostring(ok) .. '_type=' .. type(r))
            if ok and r ~= nil then
              report('loc', 'byBid_vo_t=' .. type(r.vo) ..
                     '_bid' .. tostring(r.bid) .. '_id' .. tostring(r.id))
            end
          end
        end
      end)
      -- ★★★ 修复尝试：直接调 sceneStart 创建场景对象（因为 getScene()=nil 的根因是 sceneStart 未跑）
      pcall(function()
        local sm = SceneModel:getInstance()
        report('loc', 'before_scene_t=' .. type(sm:getScene()))
        local scId = nil
        pcall(function() scId = sm.sceneId end)
        if scId == nil or scId == 0 then
          pcall(function() scId = sm.scene_info and sm.scene_info.bid end)
        end
        if scId == nil or scId == 0 then scId = 10001 end   -- ★ 显式用 10001（实测 sm.sceneId 是 0）
        report('loc', 'calling_sceneStart_sceneId' .. tostring(scId))
        -- ★★ 决定性：同时打印两处 scene_info，并尝试手动补上
        pcall(function()
          report('loc', 'sm_scene_info_t=' .. type(sm.scene_info))
        end)
        pcall(function()
          if type(TileUtil) == 'table' then
            report('loc', 'TileUtil_scene_info_t=' .. type(TileUtil.scene_info))
          else
            report('loc', 'TileUtil_t=' .. type(TileUtil))
          end
        end)
        pcall(function()
          local mp = Config.Map and Config.Map[scId]
          report('loc', 'ConfigMap_entry_t=' .. type(mp))
          if mp ~= nil and sm.scene_info == nil then
            sm.scene_info = mp          -- ★ 手动补上
            report('loc', 'manual_set_sm_scene_info=done')
          end
        end)
        local ok2, e2 = pcall(function() sm:sceneStart({ sceneId = scId }) end)
        report('loc', 'sceneStart_ok' .. tostring(ok2) .. '_e' .. tostring(e2))
        report('loc', 'after_scene_t=' .. type(sm:getScene()))
      end)
      -- 用 nc（NpcCtrl）直接试：把 ctrl 修好后再调一次
      pcall(function()
        local ctrl = NpcCtrl:getInstance()
        local v = ctrl.view
        if v == nil then v = NpcDialogs:New(); ctrl.view = v end
        v.ctrl = ctrl
        report('loc', 'v_ctrl_ok=' .. tostring(type(v.ctrl.setOpenNpc)))
        local ok, e = pcall(function() v:openNpc(BID) end)
        report('loc', 'openNpc_ok' .. tostring(ok) .. '_e' .. tostring(e))
      end)
    end

    -- ★★★★★★ 第二十四轮：包 setRoleAttribute 录 power/atk_s 写入
if not _G.__dsh_pw then
  _G.__dsh_pw = true
  pcall(function()
    local gd = nil
    pcall(function() gd = GameData.getInstance and GameData.getInstance() end)
    if not gd then return end
    local vr = nil
    pcall(function() vr = gd.getSelfRoleVo and gd.getSelfRoleVo() or gd.getRoleVo() end)
    if type(vr) == 'table' and type(vr.setRoleAttribute) == 'function' and not _G.__dsh_pw1 then
      _G.__dsh_pw1 = true
      local _o = vr.setRoleAttribute
      vr.setRoleAttribute = function(me, k, v, ...)
        local vd = type(v) == 'table' and ('t:' .. tostring(#v)) or tostring(v)
        if k == 'power' or k == 'atk_s' or k == 'hp_max' or k == 'dodge' then
          report('pw', 'setAttr_' .. tostring(k) .. '_' .. vd)
        end
        return _o(me, k, v, ...)
      end
      report('pw', 'setRoleAttribute_wrapped')
    end
    if type(vr) == 'table' and type(vr.getCombatPower) == 'function' and not _G.__dsh_pw2 then
      _G.__dsh_pw2 = true
      local _g = vr.getCombatPower
      vr.getCombatPower = function(me, ...)
        local a = { pcall(_g, me, ...) }
        report('pw', 'getCombatPower=' .. tostring(a[2]))
        return a[2]
      end
      report('pw', 'getCombatPower_wrapped')
    end
  end)
end

-- ★★★★★ 第十二轮：直接验证 self.scene 到底有没有被赋值
    --   依据：sceneStart proto[68] @4 ISNEP 'scene' / @7-10 SceneView:New() -> TSETS 'scene'
    --   目的：（1）SceneView:New() 是否被调用、是否抛异常
    --        （2）sceneStart 调用后 me.scene 的 type
    -- ★ 第十四轮：sceneStart 崩溃已修复（skills 改真实 bid）⇒ 这些 wrapper 不再必要，
    --   但保留以便后续诊断；置 false 可关闭。
    if false and not _G.__dsh_sc and type(SceneView) == 'table' then
      _G.__dsh_sc = true
      -- ① 包 SceneView.New
      if type(SceneView.New) == 'function' and not _G.__dsh_sv then
        _G.__dsh_sv = true
        local _n = SceneView.New
        SceneView.New = function(...)
          local ok, r = pcall(_n, ...)
          report('sc', 'SceneViewNew_ok' .. tostring(ok) .. '_r' .. type(r) ..
                 (ok and '' or ('_e' .. tostring(r):sub(1, 60))))
          if not ok then error(r, 0) end
          return r
        end
        report('sc', 'SceneViewNew_wrapped')
      end
      -- ② 包 sceneStart（调用后看 me.scene）
      local inst = nil
      pcall(function() inst = SceneModel:getInstance() end)
      if inst and type(inst.sceneStart) == 'function' and not _G.__dsh_ss then
        _G.__dsh_ss = true
        local _s = inst.sceneStart
        inst.sceneStart = function(me, ...)
          local before = 'nil'
          pcall(function() before = type(me.scene) end)
          -- ★★ 用 xpcall + debug.traceback 拿**精确调用栈**
          --   ⚠ 内层必须声明为 vararg 函数，否则 "cannot use '...' outside a vararg function"
          local args = { ... }
          local tb = nil
          local ok, e = xpcall(function(...)
            return _s(me, unpack(args))
          end, function(err)
            tb = tostring(err) .. ' ## ' .. tostring(debug.traceback('', 2))
            return err
          end)
          local after = 'nil'
          pcall(function() after = type(me.scene) end)
          report('sc', 'sceneStart_before' .. before .. '_after' .. after ..
                 '_ok' .. tostring(ok))
          if tb then
            -- 栈可能很长：分段上报（URL 限 200 字符，中文会被替换）
            local clean = tb:gsub('\n', ' ~ '):gsub('%s+', ' ')
            for i = 1, #clean, 150 do
              report('sc2', clean:sub(i, i + 149))
            end
          end
          return ok
        end
        report('sc', 'sceneStart_wrapped2')
      end
    end

    -- ★★★★ 第十一轮：包住 NpcDialogs.openNpc 入口
    --   依据：npc_dialogs proto[46] @21 把 openNpc 挂在全局 NpcDialogs 上；
    --         proto[8] @0 TGETS 'ctrl' ⇒ @2 'setOpenNpc' ⇒ @4 CALL（报 "call method 'setOpenNpc' (a nil value)"）
    --   目的：看 self 到底是什么、self.ctrl 有没有被赋值过。
    if not _G.__dsh_open and type(NpcDialogs) == 'table' and type(NpcDialogs.openNpc) == 'function' then
      _G.__dsh_open = true
      local _o = NpcDialogs.openNpc
      NpcDialogs.openNpc = function(me, ...)
        local keys, ctrl_t = '', 'nil'
        pcall(function()
          local n = 0
          if type(me) == 'table' then
            for k, v in pairs(me) do
              n = n + 1
              if n <= 14 then keys = keys .. tostring(k) .. ':' .. type(v) .. ' ' end
            end
          end
        end)
        pcall(function() ctrl_t = type(me and me.ctrl) end)
        report('op', 'openNpc_self_t' .. type(me) .. '_ctrl' .. ctrl_t .. '_keys_' .. keys)
        local ok, e = pcall(_o, me, ...)
        if not ok then report('op', 'openNpc_ERR_' .. tostring(e)) end
        return ok
      end
      report('op', 'openNpc_wrapped')
    end

    -- ★★★ 决定性绕过：包住 setSceneInfo / sceneStart，把两种解释下的
    --   scene_info 都补上（根据：scene_model proto[80] @5-6 在索引 R0.scene_info.tile_w
    --   时 R0.scene_info 为 nil ⇒ 报 "attempt to index field 'scene_info'"）。
    if false and not _G.__dsh_si and type(SceneModel) == 'table' then
      pcall(function()
        local inst = nil
        pcall(function() inst = SceneModel:getInstance() end)
        if inst == nil then return end

        -- ① 包 setSceneInfo：调完原函数后，确保三个地方都有值
        if type(inst.setSceneInfo) == 'function' and not _G.__dsh_si1 then
          _G.__dsh_si1 = true
          local o = inst.setSceneInfo
          inst.setSceneInfo = function(me, id, ...)
            local r = o(me, id, ...)
            local mp = nil
            pcall(function() mp = Config.Map[id] end)
            if mp ~= nil then
              pcall(function() if me.scene_info == nil then me.scene_info = mp end end)
              pcall(function() if type(_G.TileUtil) == 'table' and _G.TileUtil.scene_info == nil then _G.TileUtil.scene_info = mp end end)
              pcall(function() me.sceneId = id end)
            end
            report('bp', 'setSceneInfo_id' .. tostring(id) .. '_mp' .. type(mp))
            return r
          end
          report('bp', 'setSceneInfo_wrapped')
        end

        -- ② 包 sceneStart：先把 self.scene_info 补上再调
        if type(inst.sceneStart) == 'function' and not _G.__dsh_si2 then
          _G.__dsh_si2 = true
          local o2 = inst.sceneStart
          inst.sceneStart = function(me, ...)
            pcall(function()
              if me.scene_info == nil then
                local id = me.sceneId
                if id == nil or id == 0 then id = 10001 end
                local mp = Config.Map[id]
                if mp ~= nil then
                  me.scene_info = mp
                  if type(_G.TileUtil) == 'table' and _G.TileUtil.scene_info == nil then
                    _G.TileUtil.scene_info = mp
                  end
                end
              end
            end)
            local r = o2(me, ...)
            pcall(function()
              report('bp', 'after_sceneStart_scene_t=' .. type(me:getScene()))
            end)
            return r
          end
          report('bp', 'sceneStart_wrapped')
        end
      end)
    end

    -- ★★ 包住背包推送链路：handle_10500 + addItemInBagCode
    --   目的：取证“推了 10500 为什么背包不刷新”。
    --   报出：收到的 items 条数 / resp.data 类型 / 执行后 item_list 大小。
    if not _G.__dsh_bp and type(BackPackCtrl) == 'table' then
      pcall(function()
        if type(BackPackCtrl.handle_10500) == 'function' and not _G.__dsh_bp_h then
          _G.__dsh_bp_h = true
          local o = BackPackCtrl.handle_10500
          BackPackCtrl.handle_10500 = function(self, resp, ...)
            local n, dt = -1, 'nil'
            pcall(function()
              if type(resp) == 'table' then
                dt = type(resp.data)
                local c = 0
                if type(resp.items) == 'table' then
                  for _ in pairs(resp.items) do c = c + 1 end
                end
                n = c
              end
            end)
            report('bp', 'H10500_items' .. tostring(n) .. '_data' .. tostring(dt) ..
                   '_bagcode' .. tostring(resp and resp.bag_code))
            return o(self, resp, ...)
          end
          report('bp', 'handle_10500_wrapped')
        end
      end)
      pcall(function()
        if type(BackPackData) == 'table' and type(BackPackData.addItemInBagCode) == 'function'
           and not _G.__dsh_bp_a then
          _G.__dsh_bp_a = true
          local o2 = BackPackData.addItemInBagCode
          -- ⚠ 修正（2026-09-18）：真实签名是 `(self, resp)`（见 backpack_data proto#4 读
          --   `resp.bag_code` / `resp.items`）。原来这里按 `(self, bagCode, resp)` 记录，
          --   于是日志把 **resp 这个表**当成 bagCode 打了出来（`addItem_bagCode<table>_items-1`），
          --   并且后面 `item_list[bagCode]` 必然取到 nil（`sizena`）—— 这两条"异常"
          --   一度被误读成"客户端没吃下 SC_10500"，实际是本探针包装写错了。现改正。
          BackPackData.addItemInBagCode = function(self, resp, ...)
            _G.__dsh_bp_data = self          -- ★ 缓存**实例**（self 才是带 item_list 的那个）
            local n, bc = -1, -1
            pcall(function()
              if type(resp) == 'table' then
                bc = resp.bag_code
                if type(resp.items) == 'table' then
                  n = 0; for _ in pairs(resp.items) do n = n + 1 end
                end
              end
            end)
            report('bp', 'addItem_bagCode' .. tostring(bc) .. '_items' .. tostring(n))
            local r = o2(self, resp, ...)
            pcall(function()
              local sz = 'na'
              if type(self.item_list) == 'table' and self.item_list[bc] then
                local t = self.item_list[bc]
                local c = 0
                if type(t) == 'table' then for _ in pairs(t) do c = c + 1 end end
                sz = c
              end
              report('bp', 'after_item_list_size' .. tostring(sz))
            end)
            return r
          end
          report('bp', 'addItemInBagCode_wrapped')
        end
      end)
    end

    -- ★ 客观判据：客户端背包模型里到底有什么（各 bag_code 的条目数）
    --   用途：不再靠"肉眼/视觉读截图"判断背包是否刷新 —— 直接报模型。
    if S.t % 30 == 0 then
      pcall(function()
        local d, how = nil, 'na'
        if type(_G.__dsh_bp_data) == 'table' then d, how = _G.__dsh_bp_data, 'cached' end
        if d == nil then
          pcall(function()
            if type(BackPackCtrl) == 'table' and type(BackPackCtrl.getInstance) == 'function' then
              local inst = BackPackCtrl:getInstance()
              if type(inst) == 'table' and type(inst.data) == 'table' then
                d, how = inst.data, 'inst.data'
              else
                how = 'inst_' .. type(inst)
              end
            else
              how = 'noBackPackCtrl'
            end
          end)
        end
        local parts, total = {}, 0
        if d ~= nil and type(d.item_list) == 'table' then
          local ks = {}
          for k, _ in pairs(d.item_list) do ks[#ks + 1] = k end
          table.sort(ks, function(a, b) return tostring(a) < tostring(b) end)
          for _, k in ipairs(ks) do
            local t = d.item_list[k]
            local c = 0
            if type(t) == 'table' then for _ in pairs(t) do c = c + 1 end end
            if k == 1 then total = c end
            parts[#parts + 1] = tostring(k) .. ':' .. tostring(c)
          end
        else
          parts[#parts + 1] = 'item_list_' .. type(d and d.item_list) .. '_how_' .. how
        end
        report('bp', 'bagSizes_t' .. S.t .. '_main' .. tostring(total) ..
               '_' .. table.concat(parts, ','))
      end)
    end

    -- 客观判据：场景 / 自身角色
    if S.t % 15 == 0 then
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
      report('state', 't=' .. S.t .. '_scene=' .. sc .. '_role=' .. rv ..
             '_recv=' .. tostring(_G.__dsh_recv_n or 0))

      -- ★ 只读测量：isLoadState 是否已自然为真（不调用任何东西、不做任何干预）
      if S.t % 30 == 0 and type(SceneController) == 'table' then
        local ls, cache = 'na', 'na'
        pcall(function()
          ls = tostring(SceneController:getInstance().model:isLoadState())
        end)
        pcall(function()
          local v = SceneModel:getInstance().scene
          if type(v) == 'table' and type(v.mapResCache) == 'table' then
            local c = 0
            for _ in pairs(v.mapResCache) do c = c + 1 end
            cache = tostring(c)
          end
        end)
        report('loadState', 't=' .. S.t .. '_isLoadState=' .. ls ..
               '_mapResCache=' .. cache)

        -- ★ 角色为什么看不见：SceneModel.addRole(proto[39]) 只做
        --   "创建 RoleVo + 塞进 roleList"，**不创建可视元素**。
        --   渲染通常只画 main_role。这里测 roleList 条数与 main_role 是否被设置。
        local rl, mr, mv, gr = 'na', 'na', 'na', 'na'
        pcall(function()
          local m = SceneModel:getInstance()
          if type(m.roleList) == 'table' then
            local n = 0
            for _ in pairs(m.roleList) do n = n + 1 end
            rl = tostring(n)
          else
            rl = 'nil'
          end
          mr = tostring(type(m.main_role))
          mv = tostring(m:getMainRoleVo() ~= nil)
          gr = tostring(m:getRole(1001) ~= nil)
        end)
        report('roles', 't=' .. S.t .. '_roleList=' .. rl .. '_main_role=' .. mr ..
               '_mainRoleVo=' .. mv .. '_getRole1001=' .. gr)

        -- ★★ 最关键的一量：被抓到的 Player 实例，位置/可见性/父节点/内部字段
        --    元素已确认被创建，那么"看不见"只可能是：
        --      坐标不在可视区 / visible=false / 没有挂到场景节点 / 外观资源为空
        if _G.__dsh_player_obj then
          local o = _G.__dsh_player_obj
          local px, py, vis, par, ks2, spine = 'na', 'na', 'na', 'na', 'na', 'na'
          pcall(function() px = tostring(o:getPositionX()) end)
          pcall(function() py = tostring(o:getPositionY()) end)
          pcall(function() vis = tostring(o:isVisible()) end)
          pcall(function() par = tostring(o:getParent() ~= nil) end)
          pcall(function()
            local kk = {}
            for k, _ in pairs(o) do kk[#kk + 1] = tostring(k) end
            table.sort(kk)
            ks2 = table.concat(kk, ',', 1, math.min(#kk, 26))
          end)
          pcall(function() spine = tostring(o.spine ~= nil) end)
          -- ★ Player 不是 cc.Node，真正的外观字段是 body / body_spine_name / career
          local bd, bs, cr, an, nm3 = 'na', 'na', 'na', 'na', 'na'
          pcall(function() bd = tostring(type(o.body)) end)
          pcall(function() bs = tostring(o.body_spine_name) end)
          pcall(function() cr = tostring(o.career) end)
          pcall(function() an = tostring(o.action_name) end)
          pcall(function() nm3 = tostring(o.name) end)
          report('playerObj', 'x=' .. px .. '_y=' .. py .. '_visible=' .. vis ..
                 '_hasParent=' .. par .. '_spine=' .. spine .. '_keys=' .. ks2)
          report('playerAppear', 'body=' .. bd .. '_spine_name=[' .. bs ..
                 ']_career=' .. cr .. '_action=[' .. an .. ']_name=' .. nm3)
        end
      end

      -- ★ 情景加载门禁取证：scene_view 的异步资源队列与 loading 状态
      --   scene_view proto[35]（队列驱动）逻辑：
      --     遍历 mapResAsyncList → v:createFloorSpriteAct(self,k) → 置 nil
      --     若 self.loading 存在：loading_num = loading_num - 1；
      --       若 loading_num <= 6 → GlobalTimeTicket:add(proto34,1,10) + loading:addValue(1)
      --       然后 self:quequeAddFun() 自我递归继续
      --   即：**self.loading 为 nil 时队列就不再驱动**，很可能导致加载永远完不成。
      do
        local vw = nil
        pcall(function() vw = SceneController:getInstance().view end)
        -- ★ 正解：scene_model proto[68]（sceneStart）里是
        --     self.scene = SceneView.New()   → 视图挂在 **SceneModel 实例** 的 scene 字段
        if type(vw) ~= 'table' then
          pcall(function() vw = SceneModel:getInstance().scene end)
          if type(vw) == 'table' then _G.__dsh_view_key = 'SceneModel.scene' end
        end
        if type(vw) ~= 'table' and type(SceneView) == 'table'
           and type(SceneView.getInstance) == 'function' then
          pcall(function() vw = SceneView:getInstance() end)
        end
        -- 兜底：遍历 SceneController 实例的字段，找带 mapResAsyncList 的那个
        if type(vw) ~= 'table' then
          pcall(function()
            for k, v in pairs(SceneController:getInstance()) do
              if type(v) == 'table' and rawget(v, 'mapResAsyncList') ~= nil then
                vw = v
                _G.__dsh_view_key = tostring(k)
                break
              end
            end
          end)
        end
        if type(vw) == 'table' then
          local n, ld, ln, q = 'na', 'na', 'na', 'na'
          pcall(function()
            local c = 0
            if type(vw.mapResAsyncList) == 'table' then
              for _ in pairs(vw.mapResAsyncList) do c = c + 1 end
              n = tostring(c)
            else n = 'nil' end
          end)
          pcall(function() ld = tostring(vw.loading ~= nil) end)
          pcall(function() ln = tostring(vw.loading_num) end)
          pcall(function() q = tostring(type(vw.quequeAddFun)) end)
          report('view', 't=' .. S.t .. '_reslist=' .. n .. '_loading=' .. ld ..
                 '_loadingNum=' .. ln .. '_quequeAddFun=' .. q ..
                 '_via=' .. tostring(_G.__dsh_view_key or 'direct'))
          -- createMap(proto[38]) 的前置：model.scene_data + 视图的 mapResCache
          -- 若 scene_data 为 nil，createMap 走不到 proto[37]（setLoadState(true)）
          if S.t % 60 == 0 then
            local sd, scId, rc, ro, npt = 'na', 'na', 'na', 'na', 'na'
            pcall(function() sd = tostring(type(SceneModel:getInstance().scene_data)) end)
            pcall(function() scId = tostring(SceneModel:getInstance().sceneId) end)
            pcall(function()
              local c = 0
              if type(vw.mapResCache) == 'table' then
                for _ in pairs(vw.mapResCache) do c = c + 1 end
                rc = tostring(c)
              else rc = 'nil' end
            end)
            pcall(function()
              local c = 0
              if type(vw.mapResCacheOrder) == 'table' then
                for _ = 1, #vw.mapResCacheOrder do c = c + 1 end
                ro = tostring(c)
              else ro = 'nil' end
            end)
            pcall(function() npt = tostring(vw.nowPicTile) end)
            report('sceneData', 'scene_data=' .. sd .. '_sceneId=' .. scId ..
                   '_mapResCache=' .. rc .. '_order=' .. ro .. '_nowPicTile=' .. npt)
            -- ★ createMap(proto[38]) 的第 5 步是 pairs(self.scene_info.mons)：
            --   若 scene_info.mons 为 nil 会直接抛错 → createMap 中止 →
            --   nowPicTile 不设置 → setLoadState(true) 不触发 → 移动被门禁挡住。
            local si, f = 'na', {}
            pcall(function()
              local m = SceneModel:getInstance()
              si = tostring(type(m.scene_info))
              local s = m.scene_info
              if type(s) == 'table' then
                for _, k in ipairs({'roles', 'npcs', 'mons', 'elems', 'bid',
                                    'scene_id', 'srv_id'}) do
                  f[#f + 1] = k .. '=' .. tostring(type(rawget(s, k)))
                end
              end
            end)
            report('sceneInfo', 'scene_info=' .. si .. '_' ..
                   table.concat(f, '_'))

            -- ★ 决定性取证：包装到底有没有生效？
            --   若实例的方法解析不经过类表（New() 时把方法拷到实例上），
            --   那么包装 SceneView 类表就完全无效 —— 这能解释 svCall=0。
            local eq, own = 'na', 'na'
            pcall(function()
              eq = tostring(vw.createMap == SceneView.createMap)
              own = tostring(rawget(vw, 'createMap') ~= nil)
            end)
            report('svEq', 'inst_eq_class=' .. eq .. '_inst_owns=' .. own)
          end

          -- ★ 直接调用一次 createMap（诊断，不是修复）：
          --   看它是否可调用、是否经过我的包装（svN 是否+1）、
          --   调用后 nowPicTile / isLoadState 有没有变化。
          if not _G.__dsh_direct_cm and S.t % 180 == 0
             and _G.__dsh_allow_directcm then
            _G.__dsh_direct_cm = true
            local before = _G.__dsh_sv_n or 0
            local ok, err = pcall(function() vw:createMap() end)
            local np, ls = 'na', 'na'
            pcall(function() np = tostring(vw.nowPicTile) end)
            pcall(function()
              ls = tostring(SceneController:getInstance().model:isLoadState())
            end)
            report('directCM', 'ok=' .. tostring(ok) .. '_err=' .. tostring(err) ..
                   '_svN_before=' .. before .. '_svN_after=' .. tostring(_G.__dsh_sv_n or 0) ..
                   '_nowPicTile=' .. np .. '_isLoadState=' .. ls)
          end
        else
          report('view', 'no_scene_view_instance')
          if not _G.__dsh_ctrl_dumped then
            _G.__dsh_ctrl_dumped = true
            local ks = {}
            pcall(function()
              for k, v in pairs(SceneController:getInstance()) do
                ks[#ks + 1] = tostring(k) .. ':' .. type(v)
              end
            end)
            table.sort(ks)
            report('ctrlKeys', table.concat(ks, ','))
            report('sceneViewType', tostring(type(SceneView)))
            local ms = {}
            pcall(function()
              for k, _ in pairs(SceneView) do ms[#ms + 1] = tostring(k) end
            end)
            table.sort(ms)
            report('sceneViewKeys', table.concat(ms, ',', 1, math.min(#ms, 40)))
          end
        end
      end

      -- ★ 移动验证：直接调用客户端自己的 SceneController:move({x,y})
      --   （scene_controller.move = proto[37]，params=2，收一个 {x,y} 表）
      --   它的门禁是 self.model:isLoadState()（地图加载完成）与 not isOnTeamFollow()，
      --   进图后这两条都满足，所以能真的发出 CS_10204。
      --   与其盲试屏幕坐标找摇杆，不如直接走它自己的发送函数，验证
      --   "移动 → 服务端收包 → 落盘 → 回权威坐标" 这一整条。
      if type(SceneModel) == 'table' and type(SceneController) == 'table'
         and type(RoleCtrl) == 'table' then
        local sobj, vo = nil, nil
        pcall(function() sobj = SceneModel:getInstance():getScene() end)
        pcall(function() vo = RoleCtrl:getInstance():getSelfRoleVo() end)
        if sobj ~= nil and type(vo) == 'table' then
          local idx = _G.__dsh_move_idx or 0
          local deltas = {{4, 0}, {0, 4}, {-4, 0}, {0, -4}}   -- 右/下/左/上
          if idx < #deltas and _G.__dsh_allow_probe_move then
            -- ★ 先读 move() 的两个门禁，确认到底是哪一个挡住了发包：
            --   scene_controller.move = proto[37]:
            --     if self.model:isOnTeamFollow() then return end
            --     if not self.model:isLoadState() then return end
            local sc1 = SceneController:getInstance()
            local g1, g2 = 'na', 'na'
            pcall(function() g1 = tostring(sc1.model:isOnTeamFollow()) end)
            pcall(function() g2 = tostring(sc1.model:isLoadState()) end)
            report('gates', 'idx=' .. (idx + 1) .. '_isOnTeamFollow=' .. g1 ..
                   '_isLoadState=' .. g2)
            -- ★ 诊断实验（不是修复）：若 isLoadState 为 false，先强行置 true，
            --   再调 move()。目的是把两种可能**区分开**：
            --     ① 若置 true 后能发出 CS_10204 → 协议/服务端都没问题，
            --        移动纯粹被"客户端地图资源加载未完成"这个门禁挡住；
            --     ② 若仍不发包 → 问题在移动协议本身或服务端应答上。
            if g2 == 'false' and not _G.__dsh_force_load
               and _G.__dsh_allow_forceload then
              _G.__dsh_force_load = true
              local okf, errf = pcall(function() sc1.model:setLoadState__(true) end)
              report('forceLoad', 'ok=' .. tostring(okf) .. '_err=' .. tostring(errf))
            end
            local d = deltas[idx + 1]
            -- ⚠ 基准坐标必须用"角色实际所在坐标"，不能用 getSelfRoleVo().x/y：
            --   那个 VO 里 x/y 恒为 0（位置在场景 player 对象里，不在登录 VO 里）。
            --   用 0 当基准会被客户端判为非法落点、回退成"上报当前位置"，
            --   于是坐标永远不变（实测踩过：发 {4,0} 结果包体是 1320,2040）。
            --   这里直接用服务端下发的进场景坐标作为基准。
            _G.__dsh_base_x = _G.__dsh_base_x or 1320
            _G.__dsh_base_y = _G.__dsh_base_y or 2040
            local nx = _G.__dsh_base_x + d[1]
            local ny = _G.__dsh_base_y + d[2]
            _G.__dsh_move_idx = idx + 1
            local ok, err = pcall(function()
              SceneController:getInstance():move({x = nx, y = ny})
            end)
            report('move', 'idx=' .. (idx + 1) .. '_from=' ..
                   tostring(vo.x) .. ',' .. tostring(vo.y) ..
                   '_to=' .. nx .. ',' .. ny ..
                   '_ok=' .. tostring(ok) .. '_err=' .. tostring(err))
          end
        end
      end

      -- 一次性 dump 自身角色 VO 的字段名与关键数值（等级/职业/坐标/HP/MP）
      if not _G.__dsh_vo_dumped then
        pcall(function()
          local vo = RoleCtrl:getInstance():getSelfRoleVo()
          if type(vo) ~= 'table' then return end
          _G.__dsh_vo_dumped = true
          local ks = {}
          for k, _ in pairs(vo) do ks[#ks + 1] = tostring(k) end
          table.sort(ks)
          report('voKeys', table.concat(ks, ',', 1, math.min(#ks, 70)))
          local picks = {}
          for _, k in ipairs({'rid', 'name', 'lev', 'level', 'career', 'hp', 'mp',
                              'hp_max', 'mp_max', 'x', 'y', 'dir', 'scene_id',
                              'srv_id', 'sex', 'vip_lev'}) do
            local v = vo[k]
            if v ~= nil then picks[#picks + 1] = k .. '=' .. tostring(v) end
          end
          report('voVals', table.concat(picks, ','))
        end)
      end
    end

    if S.t >= 600 and entry then
      pcall(function() sch:unscheduleScriptEntry(entry) end)
    end
  end

  -- ---- 把驱动改挂到 GameNet.doOneMsg（每帧被 gamenet proto[1] Update 调用）
  -- 理由：Director 的 scheduleScriptFunc 条目实测只活 3~9 秒就失联，
  -- 而 `self:doOneMsg()` 在 Update 里是**每帧**调用、且 doOneMsg 在 GameNet
  -- 类表里（proto[20]），因此可以包装，且不受调度重置影响。
  -- 难点：doOneMsg 要等 sys/gamenet 被 require（约 35 秒）才存在，
  -- 所以先用"引导钩子"多次尝试安装：
  --   * cc.Director 的 replaceScene / runWithScene（初始化期会被调用多次，
  --     且这层包装挂在 cc.Director 表上，不会被调度重置清掉）
  --   * 外加本驱动自己的 tick（能活几秒就够了）
  local function tryInstall()
    if _G.__dsh_doonemsg_hooked then return true end
    if type(GameNet) ~= 'table' or type(GameNet.doOneMsg) ~= 'function' then
      return false
    end
    local orig = GameNet.doOneMsg
    GameNet.doOneMsg = function(self, ...)
      local r = orig(self, ...)
      pcall(step)
      return r
    end
    _G.__dsh_doonemsg_hooked = true
    report('doOneMsgHook', 'installed')
    -- 挂钩成功后这个 tick 就没用了
    if entry then pcall(function() sch:unscheduleScriptEntry(entry) end) end
    return true
  end
  _G.__dsh_tryInstall = tryInstall

  -- 引导：包住 cc.Director 的场景切换（初始化期会被调用多次）
  pcall(function()
    local D = cc and cc.Director
    if type(D) ~= 'table' then report('bootstrap', 'no cc.Director'); return end
    for _, m in ipairs({'replaceScene', 'runWithScene'}) do
      local orig = D[m]
      if type(orig) == 'function' and not _G['__dsh_boot_' .. m] then
        _G['__dsh_boot_' .. m] = true
        D[m] = function(self, ...)
          local r = orig(self, ...)
          pcall(tryInstall)
          return r
        end
      end
    end
    report('bootstrap', 'cc.Director.replaceScene/runWithScene hooked')
  end)

  entry = sch:scheduleScriptFunc(step, 0.2, false)
  report('driver', 'installed entry=' .. tostring(entry))
end)

-- =====================================================================
-- ★ Phase D：战斗系统探针（1.4.9）
--
-- 目的：把「点击怪物 → CS_20002 → SC_20002/20010/20012/20013/20020/20023」
--       整条链路在真机上抓下来，作为**实现服务端的唯一依据**。
--
-- 依据（1.4.9 字节码，见 analysis/1.4.9/battle/battle_flow.md）：
--   game/scene/element/monster.luac proto#6 clickHandler：
--       GlobalEvent:getInstance():Fire(SceneEvent.SCENE_MONSTER_CLICK, self.vo)
--   game/scene/scene_model.luac proto#15 initEvent：该事件绑到 mon_click_event
--   game/scene/scene_model.luac proto#32/33：mon_click_event 唯一外部调用是
--       BattleCtrl:getInstance():csFightMon(vo)
--   game/battle/battle_ctrl.luac proto#3 csFightMon：
--       proto = GameNet:getInstance():GetPrototype(20002)
--       proto.mon_id = vo.id          ← ★ 用**实例 id**，不是 bid
--       self:SendProtocal(proto)
--
-- 设计：**状态驱动**（不是纯计时）——只要场景里出现怪物就点击，
--       点完 6 tick 仍没看到 CS_20002 就直接调 csFightMon 兜底。
-- 开关：`_G.__dsh_battle`（默认 false，正式游玩不干扰）
-- =====================================================================
-- ★ Phase D 的「战斗抓取 + 闭环回归」已完成（证据见 logs/1.4.9/battle/
--   与 analysis/1.4.9/battle/）。**正式游玩置 false**（探针不再自动攻怪）；
--   需要复跑战斗回归时改回 true，再 `pwsh tools\build_fakelogin.ps1`。
_G.__dsh_battle = false
pcall(function()
  if _G.__dsh_battle_installed then return end
  _G.__dsh_battle_installed = true
  if not _G.__dsh_battle then return end
  local report = _G.__dsh_report
  if type(report) ~= 'function' then return end

  -- 把任意值压成一行短字符串（上报 URL 只保留 200 字符，故必须短）
  local function flat(t, depth, maxn)
    depth = depth or 0
    if depth > 2 then return '..' end
    if type(t) ~= 'table' then
      local s = tostring(t)
      if #s > 40 then s = s:sub(1, 40) end
      return s
    end
    local o, c = {}, 0
    for k, v in pairs(t) do
      c = c + 1
      if c > (maxn or 10) then o[#o + 1] = '..'; break end
      o[#o + 1] = tostring(k) .. '=' .. flat(v, depth + 1, 6)
    end
    return '{' .. table.concat(o, ',') .. '}'
  end
  _G.__dsh_flat = flat

  -- ---- Battle 模块方法钩子（定位"进战斗后卡在哪一步"）----
  --   battle.luac 模块表（proto#149）里与方法名的对应见
  --   analysis/1.4.9/battle/battle_flow.md §四。
  local BWANT = {'createBattleScene', 'playEnterEffect', 'enterFightFunc',
                 'initScene', 'addRole', 'createBattleRole', 'roleReady',
                 'loadFinish', 'doNextFrame', 'initOrder', 'playOrder',
                 'playRoundStart', 'playMagic', 'playMagicEffect', 'result',
                 'start', 'exitFight', 'clear'}
  local function hookBattle()
    if _G.__dsh_battle_mod_hooked then return end
    if type(Battle) ~= 'table' then return end
    local n = 0
    for _, nm in ipairs(BWANT) do
      local orig = Battle[nm]
      if type(orig) == 'function' then
        Battle[nm] = function(self, ...)
          local a = {...}
          report('btm', nm .. '_n' .. #a ..
                 (#a > 0 and ('_a1=' .. flat(a[1], 0, 8)) or ''))
          local r = orig(self, ...)
          return r
        end
        n = n + 1
      end
    end
    _G.__dsh_battle_mod_hooked = true
    report('btm_hook', 'Battle_ok' .. n)
  end

  local sch
  pcall(function() sch = cc.Director:getInstance():getScheduler() end)
  if not sch then report('bt', 'no_scheduler'); return end

  -- ---- RenderMgr 钩子（★ 区分「漏钩 / 没进分支 / 闭包抛错」）----
  --   已确认：Battle:start 用 RenderMgr:doNextFrame 注册 loadBack/createUI；
  --   而 SceneModel:sceneStart 会无条件 RenderMgr:start()。
  --   所以要看队列本身，而不是只看 BattleView 的方法有没有被调。
  local function hookRM()
    if _G.__dsh_rm_hooked then return end
    if type(RenderMgr) ~= 'table' then return end
    local m = RenderMgr:getInstance()
    if m == nil then return end
    local od = RenderMgr.doNextFrame
    if type(od) == 'function' then
      RenderMgr.doNextFrame = function(self, ...)
        local a = {...}
        local r = od(self, ...)
        report('bt_rm', 'doNextFrame_n' .. #a ..
               '_queue' .. tostring(self.next_do_list and #self.next_do_list))
        return r
      end
    end
    local ou = RenderMgr.update
    if type(ou) == 'function' then
      RenderMgr.update = function(self, ...)
        _G.__dsh_rm_upd = (_G.__dsh_rm_upd or 0) + 1
        local before = self.next_do_list and #self.next_do_list or -1
        if type(self.next_do_list) == 'table' then
          for i = 1, #self.next_do_list do
            local f = self.next_do_list[i]
            if type(f) == 'table' and type(f[1]) == 'function'
               and not f.__dsh_wrapped then
              local orig = f[1]
              f[1] = function(...)
                local ok, err = pcall(orig, ...)
                report('bt_rmq', 'cb' .. i .. '_ok=' .. tostring(ok) ..
                       '_err=' .. tostring(err))
                return nil
              end
              f.__dsh_wrapped = true
            end
          end
        end
        local r = ou(self, ...)
        local after = self.next_do_list and #self.next_do_list or -1
        if before >= 0 and before ~= after then
          report('bt_rmq', 'drained_' .. before .. '_to_' .. after)
        end
        return r
      end
    end
    _G.__dsh_rm_hooked = true
    report('bt_rm', 'hooked_isStop=' .. tostring(m.isStop) ..
           '_sched=' .. tostring(m.schedule_ ~= nil))
  end

  -- 队列长度采样（战斗窗口内每 2 tick 一次）
  local function rmSnap(tag)
    local ok, s = pcall(function()
      local m = RenderMgr:getInstance()
      return 'q' .. tostring(m.next_do_list and #m.next_do_list) ..
             '_isStop' .. tostring(m.isStop) ..
             '_sched' .. tostring(m.schedule_ ~= nil) ..
             '_upd' .. tostring(_G.__dsh_rm_upd)
    end)
    report('bt_rmsnap', tag .. '_' .. (ok and s or ('ERR:' .. tostring(s))))
  end

  -- ---- BattleView 钩子（判定"战斗 UI / 背景到底建没建"）----
  --   battle_view.luac proto#74 模块表：
  --     create / loadBack(用 BattleBG + bg_10001) / createUI(bc=1065) / createRole ...
  local VWANT = {'create', 'loadBack', 'createUI', 'createRole', 'createEffect',
                 'showWin', 'showLose', 'updateRound', 'setMainRoleHp'}
  local function hookView()
    if _G.__dsh_bv_hooked then return end
    if type(BattleView) ~= 'table' then return end
    local n = 0
    for _, nm in ipairs(VWANT) do
      local orig = BattleView[nm]
      if type(orig) == 'function' then
        BattleView[nm] = function(self, ...)
          local a = {...}
          report('btv', nm .. '_n' .. #a ..
                 (#a > 0 and ('_a1=' .. flat(a[1], 0, 6)) or ''))
          return orig(self, ...)
        end
        n = n + 1
      end
    end
    _G.__dsh_bv_hooked = true
    report('btv_hook', 'BattleView_ok' .. n)
  end

  -- 运行场景结构快照（判定战斗是否真的换/盖了场景）
  local function sceneSnap(tag)
    local ok, s = pcall(function()
      local sc = cc.Director:getInstance():getRunningScene()
      if sc == nil then return 'scene_nil' end
      local ch = 'na'
      pcall(function() ch = tostring(sc:getChildrenCount()) end)
      local bv = 'na'
      pcall(function() bv = tostring(BattleView ~= nil) end)
      return 'scene_' .. tostring(sc) .. '_children' .. ch .. '_bv' .. bv
    end)
    report('bt_scene', tag .. '_' .. (ok and s or ('ERR:' .. tostring(s))))
  end

  -- ---- BattleCtrl 处理函数钩子（★ 必须等它出现再装）----
  local WANT = {'csFightMon', 'csFightRole', 'scFightStart', 'scFightData',
                'scFightRound', 'scRoundStart', 'scFightEnd', 'scFightEndData',
                'scAddRole', 'hander_20022', 'setAuto', 'scAuto',
                'csSelectSkill', 'scSelectSkill', 'playEnd'}
  local function hookBC()
    if _G.__dsh_bc_hooked then return end
    if type(BattleCtrl) ~= 'table' then return end
    local n, miss = 0, {}
    for _, nm in ipairs(WANT) do
      local orig = BattleCtrl[nm]
      if type(orig) == 'function' then
        BattleCtrl[nm] = function(self, ...)
          if nm == 'csFightMon' then
            _G.__dsh_sent20002 = true
            local a0 = {...}
            pcall(function()
              report('bt_send', 'csFightMon_monid' .. tostring(a0[1] and a0[1].id))
            end)
          end
          if nm == 'scFightEndData' then
            _G.__dsh_battle_settled = true
          end
          local a = {...}
          local s = ''
          for i = 1, math.min(#a, 2) do
            s = s .. '_a' .. i .. '=' .. flat(a[i], 0, 14)
          end
          report('bt_in', nm .. '_n' .. #a .. s)
          local r = orig(self, ...)
          if r ~= nil then report('bt_out', nm .. '=' .. tostring(r)) end
          return r
        end
        n = n + 1
      else
        miss[#miss + 1] = nm
      end
    end
    _G.__dsh_bc_hooked = true
    report('bt_hook', 'BattleCtrl_ok' .. n ..
           (#miss > 0 and ('_miss:' .. table.concat(miss, ',')) or '_miss0'))
  end

  -- ---- 场景怪物清单 ----
  local function snap(tag)
    local ok, s = pcall(function()
      local list = SceneModel:getInstance().monList
      if type(list) ~= 'table' then return 'monList_type:' .. type(list) end
      local keys, c = {}, 0
      for k, v in pairs(list) do
        c = c + 1
        if #keys < 8 then
          keys[#keys + 1] = 'id' .. tostring(v.id) .. ',bid' .. tostring(v.bid) ..
                            ',res' .. tostring(v.res_id) ..
                            ',xy' .. tostring(v.x) .. ',' .. tostring(v.y)
        end
      end
      if c == 0 then
        local ev, ee = 0, 0
        pcall(function()
          for _ in pairs(SceneModel:getInstance().elemList or {}) do ev = ev + 1 end
        end)
        return 'mon_n0_elem_n' .. ev
      end
      return 'mon_n' .. c .. '_[' .. table.concat(keys, ' ; ') .. ']'
    end)
    report('bt_mon', tag .. '_' .. (ok and s or ('ERR:' .. tostring(s))))
  end

  local function pickMon()
    local ok, vo = pcall(function()
      local list = SceneModel:getInstance().monList
      if type(list) ~= 'table' then return nil end
      for _, v in pairs(list) do
        if type(v) == 'table' and v.id ~= nil then return v end
      end
      return nil
    end)
    if ok then return vo end
    return nil
  end

  -- ---- 任务列表 / 角色资产快照（验证「战斗击杀 → 任务进度」联动）----
  local function misSnap(tag)
    local ok, s = pcall(function()
      local md = MissionCtrl:getInstance():getMissionData()
      if type(md) ~= 'table' then return 'md_type:' .. type(md) end
      local function cnt(t)
        local c = 0
        if type(t) == 'table' then for _ in pairs(t) do c = c + 1 end end
        return c
      end
      local function keys(t, lim)
        local o = {}
        if type(t) == 'table' then
          for k, v in pairs(t) do
            local extra = ''
            pcall(function()
              extra = ':v' .. tostring(v.value) .. '/' .. tostring(v.target_value)
            end)
            o[#o + 1] = tostring(k) .. extra
          end
          table.sort(o)
          while #o > lim do table.remove(o) end
        end
        return table.concat(o, '|')
      end
      local exp, coin = 'na', 'na'
      local lev, emax, etot = 'na', 'na', 'na'
      pcall(function()
        local vo = GameData:getInstance():getRoleVo()
        exp = tostring(vo.exp)
        coin = tostring(vo.coin)
        -- ★ Phase E：等级与经验条分母（RoleVo，由 10301 填充）
        lev = tostring(vo.lev)
        emax = tostring(vo.exp_max)
        etot = tostring(vo.exp_total_nextlev)
      end)
      return 'recv_n' .. cnt(md.receive_list) ..
             '_fin_n' .. cnt(md.finish_list) ..
             '_LEV' .. lev .. '_exp' .. exp .. '/max' .. emax .. '/tot' .. etot ..
             '_coin' .. coin ..
             '_recv[' .. keys(md.receive_list, 8) .. ']'
    end)
    report('bt_mis', tag .. '_' .. (ok and s or ('ERR:' .. tostring(s))))
  end

  local n = 0
  local clickedAt = nil
  local settleSnapAt = nil
  local tick = function()
    n = n + 1
    pcall(hookBC)
    pcall(hookBattle)
    pcall(hookView)
    pcall(hookRM)
    -- 战斗期间每 2 tick 抓一次场景结构 / RenderMgr 队列
    if _G.__dsh_sent20002 and n % 2 == 0 then
      sceneSnap('t' .. n)
      rmSnap('t' .. n)
    end
    if n == 10 then snap('t10') end
    if n % 20 == 0 then snap('t' .. n) end

    -- ① 真实点击路径（状态驱动：见到怪物就点，且只在第 8 tick 之后）
    if n >= 8 and clickedAt == nil then
      local vo = pickMon()
      if vo ~= nil then
        clickedAt = n
        misSnap('before')
        -- ★★ Phase D 根因验证：RenderMgr:start() 只在 MapView 的"点击地图自由移动"
        --    路径里被调用；探针从不点地图 ⇒ RenderMgr 的每帧 update 从未被调度
        --    ⇒ Battle:start 里用 doNextFrame 注册的 loadBack/createUI 永远不执行
        --    ⇒ 战斗背景与战斗 UI 从不建立（证据见 report/battle_restore_status.md §九）。
        --    这里在攻怪前显式 start 一次来验证该根因。
        pcall(function()
          if type(RenderMgr) == 'table' then
            local m = RenderMgr:getInstance() or RenderMgr
            report('bt_rm', 'before_start_isStop=' .. tostring(m.isStop) ..
                   '_sched=' .. tostring(m.schedule_ ~= nil) ..
                   '_queue=' .. tostring(m.next_do_list and #m.next_do_list))
            -- 先原样 start 一次：看它是否被 isStop 守卫挡住
            if type(m.start) == 'function' then pcall(function() m:start() end) end
            report('bt_rm', 'plain_start_sched=' .. tostring(m.schedule_ ~= nil))
            -- 若没起来，强制 isStop=false 再 start
            if m.schedule_ == nil then
              m.isStop = false
              if type(m.start) == 'function' then pcall(function() m:start() end) end
              report('bt_rm', 'forced_start_sched=' .. tostring(m.schedule_ ~= nil) ..
                     '_isStop=' .. tostring(m.isStop))
            end
          else
            report('bt_rm', 'no_RenderMgr')
          end
        end)
        report('bt_click', 't' .. n .. '_fire_bid' .. tostring(vo.bid) ..
               '_id' .. tostring(vo.id) .. '_res' .. tostring(vo.res_id))
        local ok, err = pcall(function()
          GlobalEvent:getInstance():Fire(SceneEvent.SCENE_MONSTER_CLICK, vo)
        end)
        report('bt_click', 't' .. n .. '_fire_ok=' .. tostring(ok) ..
               '_err=' .. tostring(err))
      end
    end

    -- ② 兜底：真实路径过了 6 tick 还没发出 20002，就直接调 csFightMon
    --    （csFightMon 就是真实点击链路的**最后一跳**，见 battle_flow.md §2.2）
    if clickedAt ~= nil and n == clickedAt + 6 and not _G.__dsh_sent20002 then
      local vo = pickMon()
      if vo ~= nil then
        report('bt_click', 't' .. n .. '_direct_csFightMon_id' .. tostring(vo.id))
        local ok, err = pcall(function()
          BattleCtrl:getInstance():csFightMon(vo)
        end)
        report('bt_click', 't' .. n .. '_direct_ok=' .. tostring(ok) ..
               '_err=' .. tostring(err))
      else
        report('bt_click', 't' .. n .. '_direct_nomon')
      end
    end

    -- ③ 战斗结算后 4 tick 快照（验证任务进度真的前进了）
    if _G.__dsh_battle_settled and settleSnapAt == nil then
      settleSnapAt = n + 4
    end
    if settleSnapAt ~= nil and n == settleSnapAt then
      settleSnapAt = nil
      misSnap('after')
    end
    if n % 20 == 0 then misSnap('t' .. n) end
  end


  sch:scheduleScriptFunc(tick, 0.5, false)
  report('bt', 'probe_installed')
end)


-- ===== R65：ghost 探针（独立顶层块，不受 __dsh_battle 影响）=====
pcall(function()
  if _G.__dsh_ghost_blk then return end
  _G.__dsh_ghost_blk = true
  -- ★ R74：挂机怪建好后**自动调用一次 `GhostCtrl:fight(mon_id, mon_bid)`**
  --   （= 玩家点怪走的那一跳）。用于在没有"能看到屏幕"的条件下验证 CS_15202。
  --   正式游玩不需要这个，置 false 即可。
  _G.__dsh_autofight = true
  local report = _G.__dsh_report
  if type(report) ~= 'function' then return end
  local sch
  pcall(function() sch = cc.Director:getInstance():getScheduler() end)
  if not sch then return end

  -- =====================================================================
  -- ★★ R65：挂机链**内部状态探针**（ghost_ctrl / ghost_mon）
  --
  --   要回答的问题（九次黑盒实验都没能回答）：
  --     客户端收到 `SC_15402` 之后，到底走到哪一步？在哪一条早退返回？
  --
  --   反汇编依据（`ghost_mon` proto#1 / proto#3）：
  --     initData(data):  self.mon_cfg = data ; self.mon_bid = mis.mis_target ; createMon()
  --     createMon():     ① mon_bid 空 ⇒ return   ② mon_cfg==nil ⇒ return
  --                      ③ getSceneId()~=mon_cfg.map_bid ⇒ return
  --                      ④ Config.Mon[mon_bid]==nil ⇒ return
  --                     否则 Fire(SCENE_CLIENT_ADD, vo)
  --   `GhostMon` / `GhostCtrl` 都是**全局**（两者类定义块末尾都有 `GSET`）。
  --
  --   上报 tag：gh15402 / ghinit / ghcreate / ghost
  -- =====================================================================
  local function ghostSceneId()
    local ok, v = pcall(function()
      return _G.SceneModel:getInstance():getSceneId()
    end)
    return ok and tostring(v) or 'err'
  end

  local function installGhostProbe()
    if _G.__dsh_ghost_hooked then return true end
    local GC, GM = _G.GhostCtrl, _G.GhostMon
    if type(GC) ~= 'table' and type(GM) ~= 'table' then return false end
    _G.__dsh_ghost_hooked = true

    -- ① handle15402：服务端推来的 SC_15402 到底有没有进到 handler
    if type(GC) == 'table' and type(GC.handle15402) == 'function' then
      local orig = GC.handle15402
      GC.handle15402 = function(self, data, ...)
        _G.__dsh_gc_inst = self     -- ★ R74：记下控制器实例，供"自动开打"复用
        report('gh15402', 'called_mb=' .. tostring(data and data.mission_bid) ..
               '_map=' .. tostring(data and data.map_bid) ..
               '_scene=' .. ghostSceneId() ..
               '_hongchen_before=' .. tostring(self.mon_hongchen ~= nil))
        local r = orig(self, data, ...)
        report('gh15402', 'after_hongchen=' .. tostring(self.mon_hongchen ~= nil))
        return r
      end
    else
      report('gh15402', 'NO_handler')
    end

    -- ② initData：mon_cfg / mon_bid / mis_target 的实际值
    if type(GM) == 'table' and type(GM.initData) == 'function' then
      local orig = GM.initData
      GM.initData = function(self, data, ...)
        report('ghinit', 'in_mb=' .. tostring(data and data.mission_bid) ..
               '_in_map=' .. tostring(data and data.map_bid) ..
               '_scene=' .. ghostSceneId())
        local r = orig(self, data, ...)
        report('ghinit', 'after_mb=' .. tostring(self.mon_bid) ..
               '_cfg=' .. type(self.mon_cfg) ..
               '_cfg_map=' .. tostring(type(self.mon_cfg) == 'table'
                                       and self.mon_cfg.map_bid or nil) ..
               '_scene=' .. ghostSceneId())
        return r
      end
    end

    -- ③ createMon：四个早退条件逐条体检（不改行为，只观测）
    if type(GM) == 'table' and type(GM.createMon) == 'function' then
      local orig = GM.createMon
      GM.createMon = function(self, ...)
        local Mon, hasMon = nil, 'n/a'
        pcall(function()
          Mon = _G.Config and _G.Config.Mon
          hasMon = tostring(Mon ~= nil and Mon[self.mon_bid] ~= nil)
        end)
        report('ghcreate', 'mon_bid=' .. tostring(self.mon_bid) ..
               '_cfg=' .. type(self.mon_cfg) ..
               '_cfg_map=' .. tostring(type(self.mon_cfg) == 'table'
                                       and self.mon_cfg.map_bid or nil) ..
               '_scene=' .. ghostSceneId() ..
               '_cfgMon=' .. type(Mon) ..
               '_hasMon=' .. hasMon)
        local r = orig(self, ...)
        report('ghcreate', 'done_mon_id=' .. tostring(self.mon_id) ..
               '_bid=' .. tostring(self.mon_bid))
        -- ★★ R74：怪建好后做两件事
        --   ① 探"可视对象在不在"：SceneModel 的场景里能否按 id 找到这只怪
        --      （createMon 发的是 SCENE_CLIENT_ADD 事件，视图层不一定真的建出精灵）
        --   ② **3 秒后自动调用 `GhostCtrl:fight(mon_id, mon_bid)`**
        --      —— 这正是玩家点击地图里的怪时走的那一跳
        --      （`ghost_ctrl` proto#3 = `SCENE_CLIENT_ELEM_CLICK` 回调 → `self:fight(npc.id, npc.bid)`）
        --      用它验证 `CS_15202` 链路，**不依赖像素点击**（本环境截不到游戏屏）。
        --      开关 `_G.__dsh_autofight`，默认 true；正式游玩可改 false。
        if self.mon_id then
          pcall(function()
            local found = 'n/a'
            pcall(function()
              local sc = _G.SceneModel:getInstance():getScene()
              if sc then
                if type(sc.getMonById) == 'function' then
                  found = tostring(sc:getMonById(self.mon_id) ~= nil)
                else
                  found = 'no_getMonById'
                end
              else
                found = 'no_scene'
              end
            end)
            report('ghvis', 'mon_id=' .. tostring(self.mon_id) ..
                   '_inScene=' .. found)
            -- ★ R75：找不到就**再泛化一点**——扫场景对象的所有子表，
            --   看这只怪到底落进了哪张表（`getMonById` 返回 nil 时用来定位）
            if found == 'false' then
              local where = {}
              pcall(function()
                local sc = _G.SceneModel:getInstance():getScene()
                for k, v in pairs(sc or {}) do
                  if type(v) == 'table' and v[self.mon_id] ~= nil then
                    where[#where + 1] = tostring(k)
                  end
                end
              end)
              report('ghvis', 'mon_id=' .. tostring(self.mon_id) ..
                     '_tablesWithIt=' .. (#where > 0 and table.concat(where, ',') or 'NONE'))
            end
          end)
          if _G.__dsh_autofight then
            local mon = self
            local fired = false
            -- ★ R75 修：`scheduleScriptFunc(fn, interval, paused)` 的第三参是 **paused**，
            --   上一版误传 `true` ⇒ 回调**永不执行**（`ghfight` 一次都没上报）。
            --   改为 false + 闭包内 `fired` 保证只跑一次。
            sch:scheduleScriptFunc(function()
              if fired then return end
              fired = true
              local inst = _G.__dsh_gc_inst or _G.GhostCtrl
              local ok, err = pcall(function()
                inst:fight(mon.mon_id, mon.mon_bid)
              end)
              report('ghfight', 'fired id=' .. tostring(mon.mon_id) ..
                     '_bid=' .. tostring(mon.mon_bid) ..
                     '_ok=' .. tostring(ok) .. '_err=' .. tostring(err))
            end, 3.0, false)
          end
        end
        return r
      end
    end

    report('ghost', 'installed')
    return true
  end

  local gpTries = 0
  sch:scheduleScriptFunc(function()
    gpTries = gpTries + 1
    if installGhostProbe() then return end
    if gpTries == 120 then report('ghost', 'giveup_after_120s') end
  end, 1.0, false)

end)
end
