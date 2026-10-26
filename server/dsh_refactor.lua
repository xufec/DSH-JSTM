-- =====================================================================
-- DSH 重构包注入块 —— 追加到 assets/src/config.luac 末尾（1.4.11 / 绝世唐门）
--
-- 职责（三块）：
--   [1] 本地地址：URL_PATH / CDN / get_servers_url / get_notice_url（指向本机服务器）
--   [2] NO_PLAY_VIDEO = true（跳过开场 CG）
--   [3] 账号系统（客户端半身）：本地账号簿 + 账号管理面板
--       —— 服务端半身在 server/account/service.py（accounts 表 + 密码校验 + 按区角色）
--
-- ★★ 2026-10-17 两次踩坑后的最终形态（重要，别回退）：
--   ① **不再在客户端劫持选区列表**。曾经在这里包住 DengluMgr 的
--      `managerDefualtServerListByJsonObj` / `managerServerListByJsonObj`，结果：
--        · 只调"完整列表入口" ⇒ 丢了 Fire(DEFAULE_SERVER_SUCCESS) ⇒
--          **点「登录」界面一动不动**（登录页从 view4 切 view1 全靠这个事件）；
--        · 补成 "b 再 a" 之后又与客户端自己的在途响应互相覆盖 ⇒ 选区被钉在错的区
--          （实测：上次存的 local_srv_id 与本地列表交替生效，登录用了 3 区）。
--      结论：**选区列表由服务端下发**（server/config.json 的 server_list = 三区），
--      客户端一行都不改 —— 这是本游戏的原始设计，服务端已经能正确返回三区。
--   ② 「忘记密码」原本调 sdkOnLogin → cc.Device:beginThirdPartyLogin（渠道 SDK）；
--      渠道已关（dex EwanSdk.is_close=true）⇒ 死键。这里把它改成**账号管理面板**入口。
--   ③ 「切换账号」原本是 restart()（重启后只剩最近一次账号 ⇒ 容易丢账号），
--      登录界面上改为打开账号面板；其它调用点（版本更新提示）仍走原实现。
--      面板里除"选老号"，还有 **「新建账号」**（清空「用户登录」表单、可直接输入或点
--      「一键注册」）—— 否则"切换账号"只能选老号，等于摆设。
--
-- ★ NO_PLAY_VIDEO：不能靠删 gamecg.mp4 跳过开场 CG —— file_update proto#39 只对
--   writable 的两个副本做 isFileExist，默认路径 "res/resource/login/gamecg.mp4"
--   **不判断** ⇒ 文件缺失时 ccexp.VideoPlayer:play() 失败，native 弹
--   「视频问题 / 无法播放此视频。」并把启动卡死（实测 logcat: Cocos2dxVideoView: Error: 1,0）。
--   proto#39 开头现成的开关就是 NO_PLAY_VIDEO（为真直接 return true ⇒ video_finish = true）。
-- =====================================================================
pcall(function()
  if _G.__dsh_refactor_installed then return end
  _G.__dsh_refactor_installed = true

  -- ---- 改这里即可换服（模拟器访问宿主机回环 = 10.0.2.2；真机填 PC 局域网 IP）----
  local HOST  = "10.0.2.2"   -- 游戏服 IP
  local PORT  = 9000         -- 游戏服 TCP 端口（本块只用于展示/兼容，实际连接由选区数据给出）
  local HPORT = 8080         -- 配置/网关 HTTP 端口
  local BASE  = "http://" .. HOST .. ":" .. HPORT
  local PLAT  = _G.PLATFORM_NAME or "ewan"

  -- ★ 日志双通道：logcat 的 `print` 在客户端启动后会被它自己替换掉（实测：启动阶段能看到，
  --   之后一条都进不来）⇒ 必须同时落盘，否则"看不见日志"会被误判成"代码没跑"。
  --   文件：<writable>/dsh_refactor.log（`adb pull` 即可取回）。
  local LOGFILE = nil
  local function logfile()
    if LOGFILE then return LOGFILE end
    pcall(function()
      LOGFILE = cc.FileUtils:getInstance():getWritablePath() .. "dsh_refactor.log"
    end)
    return LOGFILE
  end

  local function logline(s)
    local line = string.format("[%s] %s", os.date("%H:%M:%S"), tostring(s))
    pcall(function() print("[DSH_REFACTOR] " .. tostring(s)) end)
    pcall(function()
      local p = logfile()
      if not p then return end
      local f = io.open(p, "a")
      if f then f:write(line .. "\n"); f:close() end
    end)
  end

  ---------------------------------------------------------------- [1] 本地地址
  URL_PATH_ALL = {
    get = function(_, platform)
      return { update = BASE .. "/update", voice = BASE .. "/voice",
               register = BASE .. "/register", is_shenhe = false,
               platform = tostring(platform) }
    end,
  }
  URL_PATH       = URL_PATH_ALL:get(PLAT)
  CDN_PATH_BASE  = BASE
  CDN_URL        = BASE .. "/cdn/"
  url_res_config = BASE .. "/cdn/"

  -- 令 now_ver >= target_ver 恒成立 ⇒ file_update proto#17 直接 update_finish，
  -- 跳过整个热更下载（与 1.4.9 伪登录链上实测可用的写法一致）。
  UPDATE_VERSION_MAX = NOW_VERSION

  ---------------------------------------------------------------- [2] 跳过开场 CG
  NO_PLAY_VIDEO = true

  ---------------------------------------------------------------- [2b] 场景修补（进图前补三处 nil）
  -- ★★ 根因（本项目已定案，见 `report/report_20261001_FIXED_enter_map_and_move.md`）：
  --   `SceneModel:__init` 在 `Config` 只加载了 18 个键时执行 ⇒ `self.map_block =
  --   Config.MapBlock` 取到 **nil 并永久保留** ⇒ `sceneStart` 崩在
  --   `self.map_block:get(sceneId)` ⇒ **`SceneView:createMap()` 根本没跑** ⇒
  --   场景视图不成形（"只有一张模糊的地图"）、加载走不完、UI 不出来、客户端反复重登。
  --   修法（v67，实测有效）：进图前用客户端**自己的配置真值**把三处 nil 补好。
  local SPAWN_SCENE = 10001

  local function patch_scene_fields(m)
    if type(m) ~= 'table' then return 0 end
    local cfg = _G.Config
    if type(cfg) ~= 'table' then return 0 end
    local fixed = {}
    -- ★★ 同一类"加载竞态"的第二个受害者：`DailyCtrl.__init` 里
    --   `self.data = DailyData.New()`；若构造时 DailyData 还没就绪 ⇒ data 永久 nil
    --   ⇒ 场景 SCENE_START 事件链里 `self.data:setTotalHuoli(...)` 抛
    --   "attempt to index a nil value" ⇒ **整个 sceneStart 从这一行中断**
    --   ⇒ SceneView 建不出来（sceneView=nil）⇒ 地图不成形、UI 全无。
    pcall(function()
      local DC = _G.DailyCtrl
      if type(DC) ~= 'table' or type(DC.getInstance) ~= 'function' then return end
      local dc = DC:getInstance()
      if type(dc) ~= 'table' then return end
      if rawget(dc, 'data') == nil and type(_G.DailyData) == 'table'
         and type(_G.DailyData.New) == 'function' then
        dc.data = _G.DailyData.New()
        fixed[#fixed + 1] = 'DailyCtrl.data'
      end
      if rawget(dc, 'renderMgr') == nil and type(_G.RenderMgr) == 'table'
         and type(_G.RenderMgr.getInstance) == 'function' then
        dc.renderMgr = _G.RenderMgr:getInstance()
        fixed[#fixed + 1] = 'DailyCtrl.renderMgr'
      end
    end)
    pcall(function()
      if rawget(m, 'map_block') == nil and type(cfg.MapBlock) == 'table' then
        m.map_block = cfg.MapBlock; fixed[#fixed + 1] = 'map_block'
      end
      if rawget(m, 'map') == nil and type(cfg.Map) == 'table' then
        m.map = cfg.Map; fixed[#fixed + 1] = 'map'
      end
      if rawget(m, 'scene_info') == nil and type(cfg.Map) == 'table'
         and type(cfg.Map[SPAWN_SCENE]) == 'table' then
        m.scene_info = cfg.Map[SPAWN_SCENE]; fixed[#fixed + 1] = 'scene_info'
      end
    end)
    if #fixed > 0 then
      logline('scene prepatch fixed: ' .. table.concat(fixed, ',') ..
              ' | map_block=' .. type(rawget(m, 'map_block')) ..
              ' map=' .. type(rawget(m, 'map')) ..
              ' scene_info=' .. type(rawget(m, 'scene_info')))
    end
    return #fixed
  end

  -- 两条安装路径（都在进图前完成）：
  --   ① 直接补**当前实例**（SceneModel 在 initInstance() 就建好了，登录时补一次即可）
  --   ② 包住 `SceneModel.sceneStart`（proto#68）—— 万一实例字段被别的路径重置，
  --      在真正建视图前再补一次；顺带包 `New` 覆盖"进图前才建实例"的情况。
  local function hook_scene()
    if _G.__dsh_scene_hooked then return true end
    local S = _G.SceneModel
    if type(S) ~= 'table' then
      if not _G.__dsh_scene_warned then
        _G.__dsh_scene_warned = true
        logline('hook_scene: SceneModel not ready (type=' .. type(S) ..
                ') —— 等兜底 tick 再装')
      end
      return false
    end
    _G.__dsh_scene_hooked = true
    if type(S.New) == 'function' then
      local origNew = S.New
      S.New = function(...)
        local obj = origNew(...)
        pcall(patch_scene_fields, obj)
        return obj
      end
    end
    if type(S.sceneStart) == 'function' then
      local origStart = S.sceneStart
      S.sceneStart = function(self, ...)
        pcall(patch_scene_fields, self)
        return origStart(self, ...)
      end
    end
    pcall(function()
      local m = (type(S.getInstance) == 'function') and S:getInstance() or nil
      if type(m) == 'table' then patch_scene_fields(m) end
    end)
    -- [诊断] 场景构建链探针：定位 "地图不成形 / UI 不出" 断在哪一步
    pcall(function()
      if _G.__dsh_sv_probe then return end
      _G.__dsh_sv_probe = true
      local SV = _G.SceneView
      if type(SV) == 'table' then
        for _, name in ipairs({'createMap', 'layoutScene', 'renderScene'}) do
          local orig = SV[name]
          if type(orig) == 'function' then
            SV[name] = function(self2, ...)
              logline('SceneView.' .. name .. ' enter')
              local ok2, err2 = pcall(orig, self2, ...)
              if ok2 then
                logline('SceneView.' .. name .. ' ok')
              else
                logline('SceneView.' .. name .. ' ERROR: ' .. tostring(err2))
              end
              return (ok2 and err2) or nil
            end
          else
            logline('SceneView.' .. name .. ' NOT a function (' .. type(orig) .. ')')
          end
        end
      else
        logline('SceneView not a table: ' .. type(SV))
      end
      local ss = S.sceneStart
      if type(ss) == 'function' then
        local o2 = ss
        S.sceneStart = function(self2, ...)
          logline('sceneStart enter')
          -- ★★ 进图前的**最小兜底**：`daily_ctrl` 的 SCENE_START 回调会用到
          --   GameData / ActivityContants / RoleRpgEvents；只要有一个是 nil，
          --   回调就抛 "attempt to index a nil value"，**整个 sceneStart 从这一行中断**
          --   ⇒ SceneView 实例都建不出来（sceneView=nil）⇒ 地图不成形、UI 全无。
          --   这里只补**缺失的**（真模块若已加载则原样不动），且用的是"不取值"的安全桩：
          --   daily_ctrl 里 `GameData:getInstance():getRoleVo()` 的返回值被丢弃，
          --   所以返回 nil 的桩不会改变任何逻辑。
          pcall(function()
            local fixed = {}
            if type(_G.GameData) ~= 'table' then
              local G = { Instance = false }
              G.getRoleVo = function() return nil end
              G.getRoleLev = function() return 1 end
              G.setRoleVo = function() end
              G.getInstance = function(self2b) return (type(self2b) == 'table' and self2b.Instance) or G end
              _G.GameData = G
              fixed[#fixed + 1] = 'GameData'
            end
            if type(_G.ActivityContants) ~= 'table' then
              _G.ActivityContants = {}; fixed[#fixed + 1] = 'ActivityContants'
            end
            if type(_G.RoleRpgEvents) ~= 'table' then
              _G.RoleRpgEvents = {}; fixed[#fixed + 1] = 'RoleRpgEvents'
            end
            if type(_G.SceneEvent) ~= 'table' then
              _G.SceneEvent = {}; fixed[#fixed + 1] = 'SceneEvent'
            end
            if #fixed > 0 then
              logline('scene globals stubbed: ' .. table.concat(fixed, ','))
            else
              logline('scene globals OK (GameData/ActivityContants/RoleRpgEvents 都在)')
            end
          end)
          -- 注意：内层闭包不能用 `...`（非 vararg）⇒ 先把参数收成局部变量
          local a1, a2, a3, a4 = ...
          local ok2, err2 = xpcall(function() return o2(self2, a1, a2, a3, a4) end,
            function(e) return tostring(e) .. ' | ' .. tostring(debug.traceback('', 2)) end)
          if ok2 then logline('sceneStart ok') else logline('sceneStart ERROR: ' .. tostring(err2)) end
          -- ★ 场景里到底有没有 UI 节点？（"UI 不出来"是没创建，还是创建了但缩放/位置不对）
          _G.__dsh_sv_dump = (_G.__dsh_sv_dump or 0) + 1
          if _G.__dsh_sv_dump <= 3 then
            pcall(function()
              local tag = '#' .. _G.__dsh_sv_dump .. (ok2 and '(ok)' or '(ERR)')
              logline('dump ' .. tag)
              local d = cc.Director:getInstance()
              local ws = d and d:getWinSize() or nil
              logline(string.format('winSize=%sx%s REAL_SCALE_RATE=%s SCREEN=%sx%s',
                tostring(ws and ws.width), tostring(ws and ws.height),
                tostring(_G.REAL_SCALE_RATE),
                tostring(_G.SCREEN_WIDTH), tostring(_G.SCREEN_HEIGHT)))
              local function dumpNode(node, label)
                if type(node) ~= 'table' then logline(label .. ' type=' .. type(node)); return end
                local ch = node:getChildren()
                local n = (ch and ch:count()) or -1
                logline(label .. ' children=' .. tostring(n))
                for i = 0, math.min(n, 8) - 1 do
                  local c = ch:objectAtIndex(i)
                  local nm, sw, sh, x, y, vis, sx = '?', 0, 0, 0, 0, '?', 0
                  pcall(function() nm = tostring(c:getName()) end)
                  pcall(function() local s = c:getContentSize(); sw, sh = s.width, s.height end)
                  pcall(function() x, y = c:getPositionX(), c:getPositionY() end)
                  pcall(function() vis = tostring(c:isVisible()); sx = c:getScaleX() end)
                  logline(string.format('  %s[%d] %s %sx%s @%s,%s scale=%s vis=%s',
                    label, i, nm, tostring(sw), tostring(sh),
                    tostring(x), tostring(y), tostring(sx), vis))
                end
              end
              pcall(function()
                local rs = d and d:getRunningScene()
                dumpNode(rs, 'runningScene')
              end)
              pcall(function()
                local SVI = _G.SceneView
                local sv = (SVI and type(SVI.getInstance) == 'function') and SVI:getInstance() or nil
                dumpNode(sv, 'sceneView')
              end)
              pcall(function()
                local VM = _G.ViewManager
                local vm = (VM and type(VM.getInstance) == 'function') and VM:getInstance() or nil
                if type(vm) ~= 'table' then logline('viewManager type=' .. type(vm)); return end
                logline('viewManager ok, getLayerByTag=' .. type(vm.getLayerByTag))
              end)
            end)
          end
          return (ok2 and err2) or nil
        end
      end
    end)
    logline('scene hooks installed (New + sceneStart)')
    return true
  end

  ---------------------------------------------------------------- [3a] 本地账号簿
  local ACCT_KEY = "dsh_accounts"      -- cc.UserDefault 的键（name\tpwd 逐行）
  local ACCT_MAX = 12

  local function ud() return cc.UserDefault:getInstance() end

  local function book_load()
    local out = {}
    local raw = ''
    pcall(function() raw = ud():getStringForKey(ACCT_KEY) or '' end)
    for line in tostring(raw):gmatch('[^\n]+') do
      local name, pwd = line:match('^([^\t]*)\t(.*)$')
      if not name then name, pwd = line, '' end
      if name and #name > 0 then
        out[#out + 1] = { name = name, pwd = pwd or '' }
      end
    end
    return out
  end

  local function book_save(list)
    local parts = {}
    for i = 1, #list do
      local e = list[i]
      local n = tostring(e.name or ''):gsub('[\t\n]', '')
      if #n > 0 then
        parts[#parts + 1] = n .. '\t' .. tostring(e.pwd or ''):gsub('[\n]', '')
      end
    end
    pcall(function()
      ud():setStringForKey(ACCT_KEY, table.concat(parts, '\n'))
      ud():flush()
    end)
  end

  local function book_put(name, pwd)
    if not name or name == '' then return end
    local list = book_load()
    for i = 1, #list do
      if list[i].name == name then
        if pwd and pwd ~= '' then list[i].pwd = pwd end
        local e = table.remove(list, i)
        table.insert(list, 1, e)
        book_save(list)
        return
      end
    end
    table.insert(list, 1, { name = name, pwd = pwd or '' })
    while #list > ACCT_MAX do table.remove(list) end
    book_save(list)
  end

  local function book_del(name)
    local list = book_load()
    for i = #list, 1, -1 do
      if list[i].name == name then table.remove(list, i) end
    end
    book_save(list)
  end

  -- 首次使用：把客户端**已有**的账号名（denglu_mgr 的 usrNameList）导进账号簿，
  -- 这样换到本包之后，之前用过的账号名仍然能一键选出来。
  local function book_seed()
    if _G.__dsh_book_seeded then return end
    _G.__dsh_book_seeded = true
    pcall(function()
      local d = DengluMgr:getInstance():getLoginData()
      local names = {}
      for _, e in ipairs((d and d.usrNameList) or {}) do
        local n = e and (e.name or e.usr)
        if n and #n > 0 then names[#names + 1] = n end
      end
      if d and d.usrName and #tostring(d.usrName) > 0 then
        names[#names + 1] = tostring(d.usrName)
      end
      local list = book_load()
      local have = {}
      for _, e in ipairs(list) do have[e.name] = true end
      for i = #names, 1, -1 do
        if not have[names[i]] then
          table.insert(list, 1, { name = names[i], pwd = '' })
        end
      end
      book_save(list)
      logline('book seeded (' .. #names .. ' names from usrNameList)')
    end)
  end

  ---------------------------------------------------------------- [3b] 账号面板
  local panel = nil

  local function ui_root()
    local ctrl = _G.DengluCtrl
    if type(ctrl) ~= 'table' or type(ctrl.getInstance) ~= 'function' then return nil end
    local inst = ctrl:getInstance()
    local view = inst and inst.loginView
    return (view and view.root_wnd) or nil
  end

  local function close_panel()
    if panel then pcall(function() panel:removeFromParent(true) end) end
    panel = nil
  end

  local function user_panel()
    local ctrl = _G.DengluCtrl
    if type(ctrl) ~= 'table' or type(ctrl.getInstance) ~= 'function' then return nil end
    local inst = ctrl:getInstance()
    local view = inst and inst.loginView
    local views = view and view.views
    return views and views[4] or nil
  end

  -- 把账号（含密码）填回「用户登录」面板，并同步到 DengluMgr.loginData
  local function fill_account(entry)
    if not entry then return end
    pcall(function()
      local up = user_panel()
      if up then
        if up.input_usr then up.input_usr:setText(entry.name or '') end
        if up.input_password then up.input_password:setText(entry.pwd or '') end
      end
      local d = DengluMgr:getInstance():getLoginData()
      if d then
        if entry.name and entry.name ~= '' then d.usrName = entry.name end
        if entry.pwd and entry.pwd ~= '' then d.password = entry.pwd end
      end
      message(string.format("已填入账号：%s", entry.name or ''))
      -- 切到「用户登录」面板，让填入的账号/密码**可见**（否则用户在选区页看不出变化，
      -- 只能靠再点一次登录去猜）。view4 = UserPanel；不存在时 showPanel 会现场创建。
      pcall(function()
        local v = DengluCtrl:getInstance().loginView
        if v and v.showPanel then v:showPanel(4) end
      end)
      logline('account filled: ' .. tostring(entry.name))
    end)
    close_panel()
  end

  -- 「新建账号」：切到「用户登录」(view4) 并把表单**清空**，让用户直接输入新账号，
  -- 或点面板上现成的「一键注册」自动生成一个。同时把 loginData 里的旧账号/旧角色
  -- 清掉，否则 requestLinkPlatform 会拿旧账号自动登录、新账号根本用不上。
  local function new_account()
    pcall(function()
      local ctrl = DengluCtrl:getInstance()
      local v = ctrl and ctrl.loginView
      if v and v.showPanel then v:showPanel(4) end
      local up = user_panel()
      if up then
        if up.input_usr then up.input_usr:setText('') end
        if up.input_password then up.input_password:setText('') end
      end
      local d = DengluMgr:getInstance():getLoginData()
      if d then
        d.usrName = ''
        d.password = ''
        d.account_name = ''
        d.rid = 0
        -- 区服**保留**：玩家已经选好的区不该被"新建账号"清掉
      end
      message("请输入新账号与密码，或点「一键注册」自动生成")
      logline('new account -> empty login form')
    end)
    close_panel()
  end

  local build_panel

  local function build_panel_impl()
    local root = ui_root()
    if not root then return false end
    close_panel()

    local list = book_load()
    local cur = {}
    pcall(function()
      local d = DengluMgr:getInstance():getLoginData()
      cur = { usrName = d and d.usrName, password = d and d.password }
    end)
    if cur.usrName and #tostring(cur.usrName) > 0 then
      local found = false
      for _, e in ipairs(list) do if e.name == cur.usrName then found = true end end
      if not found then
        table.insert(list, 1, { name = cur.usrName, pwd = cur.password or '' })
      end
    end

    local rows = math.min(#list, 6)
    local W, H = 470, 170 + rows * 62 + 60

    panel = ccui.Layout:create()
    panel:setContentSize(cc.size(SCREEN_WIDTH, SCREEN_HEIGHT))
    panel:setPosition(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    panel:setAnchorPoint(cc.p(0.5, 0.5))
    panel:setTouchEnabled(true)
    pcall(function()
      panel:setBackGroundColorType(1)
      panel:setBackGroundColor(cc.c3b(0, 0, 0))
      panel:setBackGroundColorOpacity(150)
    end)
    root:addChild(panel)

    local bg = createScale9Sprite(PathTool.getBgRes("bg"), SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    bg:setCapInsets(cc.rect(55, 47, 2, 2))
    bg:setAnchorPoint(cc.p(0.5, 0.5))
    bg:setContentSize(cc.size(W, H))
    panel:addChild(bg)

    local title = createLabel(22, Config.Color4[20], nil, W, 26,
                              "账号管理（本机保存）", bg, nil, cc.p(0.5, 0.5))
    title:setPosition(W / 2, H - 32)

    if #list == 0 then
      local l = createLabel(18, Config.Color4[7], nil, W - 40, 24,
                            "还没有账号记录：先输入账号密码登录一次，就会记在这里",
                            bg, nil, cc.p(0.5, 0.5))
      l:setPosition(W / 2, H / 2)
    end

    local y = H - 96
    for i = 1, rows do
      local e = list[i]
      local label = e.name
      if e.pwd and #e.pwd > 0 then label = label .. "（已存密码）" end
      local btn = createButton(bg, label, W / 2 - 34, y, cc.size(300, 46),
                               PathTool.getBtnRes("btn1"), 18, Config.Color4[21])
      btn:addTouchEventListener(function(sender, ev)
        if ev == ccui.TouchEventType.ended then fill_account(e) end
      end)
      local del = createButton(bg, "删", W - 52, y, cc.size(56, 46),
                               PathTool.getBtnRes("btn2"), 18, Config.Color4[25])
      del:addTouchEventListener(function(sender, ev)
        if ev == ccui.TouchEventType.ended then
          book_del(e.name)
          logline('account deleted: ' .. tostring(e.name))
          pcall(build_panel)      -- 重建列表
        end
      end)
      y = y - 62
    end

    -- ★ 「新建账号」必须在这个面板上（否则"切换账号"只能选老号 = 摆设）
    local add = createButton(bg, "新建账号", W / 2 - 92, 48, cc.size(150, 46),
                             PathTool.getBtnRes("btn2"), 19, Config.Color4[25])
    add:addTouchEventListener(function(sender, ev)
      if ev == ccui.TouchEventType.ended then new_account() end
    end)
    local close = createButton(bg, "关闭", W / 2 + 92, 48, cc.size(140, 46),
                               PathTool.getBtnRes("btn1"), 20, Config.Color4[21])
    close:addTouchEventListener(function(sender, ev)
      if ev == ccui.TouchEventType.ended then close_panel() end
    end)
    logline('account panel open (n=' .. #list .. ')')
    return true
  end

  build_panel = build_panel_impl

  local function open_account_panel()
    pcall(book_seed)
    local ok = false
    pcall(function() ok = build_panel() end)
    if not ok then
      local names = {}
      for _, e in ipairs(book_load()) do names[#names + 1] = e.name end
      pcall(function()
        message("本机账号：" .. (#names > 0 and table.concat(names, " / ") or "（暂无）"))
      end)
      logline('account panel unavailable -> toast fallback')
    end
    return ok
  end

  _G.__dsh_account_panel = open_account_panel

  ---------------------------------------------------------------- [3c] 记账 + 接管入口
  -- ★ 登录后"数据批次"探针：`on10102Login` 里 `if SendProtocal(10300) then
  --   SysEventCallBack:getInstance():LoginSucceedSendProtocal() end` —— 只有这一步成功，
  --   客户端才会去要 10301/10302/10502/12400 等全部角色数据；一旦它抛错（例如
  --   `SysEventCallBack` 未定义），登录流程会**静默中断**：场景能进、UI 全空。
  local function hook_10102()
    if _G.__dsh_10102_hooked then return true end
    local C = _G.DengluCtrl
    if type(C) ~= 'table' or type(C.on10102Login) ~= 'function' then return false end
    _G.__dsh_10102_hooked = true
    local orig = C.on10102Login
    C.on10102Login = function(self, resp, ...)
      local sec = _G.SysEventCallBack
      logline('on10102Login: code=' .. tostring(resp and resp.code) ..
              ' SysEventCallBack=' .. type(sec) ..
              ' batchFn=' .. type(sec and sec.LoginSucceedSendProtocal))
      local ok, err = pcall(orig, self, resp, ...)
      if not ok then logline('on10102Login ERROR: ' .. tostring(err)) end
      return (ok and err) or nil
    end
    return true
  end

  -- 登录成功（CS_1110 回 code=1）时把账号与密码记进本地账号簿
  local function hook_record()
    if _G.__dsh_book_hooked then return true end
    local C = _G.DengluCtrl
    if type(C) ~= 'table' or type(C.on1110Rolelist) ~= 'function' then return false end
    _G.__dsh_book_hooked = true
    local orig = C.on1110Rolelist
    C.on1110Rolelist = function(self, resp, ...)
      local r = orig(self, resp, ...)
      pcall(function()
        if resp and (resp.code == 1 or resp.code == true) then
          local d = DengluMgr:getInstance():getLoginData()
          if d and d.usrName and #tostring(d.usrName) > 0 then
            book_put(d.usrName, d.password)
            logline('account recorded: ' .. tostring(d.usrName))
          end
        end
      end)
      return r
    end
    return true
  end

  -- 「切换账号」→ sdkSwitchAccount()：官方实现（非平台登录）是 restart()，重启后只剩
  -- "最近一次"账号 ⇒ 用户觉得"一切换就丢账号"。这里只在**登录界面**把它改成打开账号
  -- 面板；版本更新等其它调用点仍走原实现。
  local function hook_switch_account()
    if _G.__dsh_switch_hooked then return end
    if type(_G.sdkSwitchAccount) ~= 'function' then return false end
    _G.__dsh_switch_hooked = true
    local orig = _G.sdkSwitchAccount
    _G.sdkSwitchAccount = function(...)
      local on_login_ui = false
      pcall(function()
        local ctrl = DengluCtrl:getInstance()
        local v = ctrl and ctrl.loginView
        if v and (v.view_index == 1 or v.view_index == 4) then on_login_ui = true end
      end)
      if on_login_ui then
        logline('sdkSwitchAccount -> account panel')
        return open_account_panel()
      end
      return orig(...)
    end
    return true
  end

  -- 「忘记密码」原本调 sdkOnLogin → cc.Device:beginThirdPartyLogin（渠道 SDK）。
  -- 渠道已关（dex is_close=true）⇒ 死键。**在 config 阶段**就覆盖它（调用点是运行时
  -- GGET/TGETS 查表，覆盖 cc.Device 上的方法有效），改为打开账号面板。
  pcall(function()
    local dev = cc and cc.Device
    if type(dev) == 'table' then
      dev.beginThirdPartyLogin = function(...)
        logline('beginThirdPartyLogin -> account panel')
        open_account_panel()
      end
      dev.switchAccount = function(...) open_account_panel() end
      logline('cc.Device hooks installed (channel login removed)')
    end
  end)

  -- 兜底 tick：**在引擎/模块就绪之后**再注册（config.luac 阶段注册的调度器实测一帧都不跑）。
  -- 由 ensure() 调用 ⇒ 第一次服务器列表请求时（登录阶段）才建，此时调度器已在正常跑。
  local function start_scene_ticker()
    if _G.__dsh_scene_ticker then return end
    _G.__dsh_scene_ticker = true
    pcall(function()
      local sch = cc.Director:getInstance():getScheduler()
      if not sch then return end
      local ticks, entry = 0, nil
      local function step()
        ticks = ticks + 1
        local done = hook_scene()
        if done or ticks > 900 then
          if entry then pcall(function() sch:unscheduleScriptEntry(entry) end) end
        end
      end
      entry = sch:scheduleScriptFunc(step, 1.0, false)
      logline('scene ticker started')
    end)
  end

  ---------------------------------------------------------------- [3d] 安装锚点
  -- 客户端"请求服务器列表"时必然调用本函数（调用方就是 DengluMgr 的方法本体）⇒
  -- 此刻 DengluCtrl / DengluMgr / sdkSwitchAccount 全部就绪，零时序假设。
  -- 这里只做**记账钩子 + 换号钩子**的安装，**不碰选区列表**（见文件头 ★★ ①）。
  local function ensure()
    if _G.__dsh_hooks_ready then return true end
    if not _G.__dsh_ensure_logged then
      _G.__dsh_ensure_logged = true
      logline('ensure() called: SceneModel=' .. type(_G.SceneModel) ..
              ' DengluCtrl=' .. type(_G.DengluCtrl) ..
              ' sdkSwitch=' .. type(_G.sdkSwitchAccount) ..
              ' Config=' .. type(_G.Config))
    end
    local ok = hook_record()
    local ok2 = hook_switch_account()
    hook_10102()                     -- [诊断] 登录后数据批次是否被执行/是否抛错
    hook_scene()                     -- [2b] 进图前的 map_block/map/scene_info 修补
    start_scene_ticker()             -- [2b] 兜底：每秒重试，直到 SceneModel 就绪
    if ok and ok2 then
      _G.__dsh_hooks_ready = true
      logline('hooks ready (record + switch-account + scene)')
    end
    pcall(book_seed)
    return _G.__dsh_hooks_ready
  end
  _G.__dsh_hooks_ensure = ensure

  function get_servers_url(...)
    if type(_G.__dsh_hooks_ensure) == "function" then pcall(_G.__dsh_hooks_ensure) end
    return BASE .. "/gateway/mobile/json"
  end
  function get_notice_url(...)  return BASE .. "/notice.json" end

  logline('block loaded (urls + no-CG + scene prepatch + account book/panel)')
end)
