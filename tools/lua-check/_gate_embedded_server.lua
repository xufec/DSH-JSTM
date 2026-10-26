-- ============================================================================
--  《绝世唐门》单机版 —— 内置本机服务端 (embedded local server)
-- ============================================================================
--  运行位置：游戏进程自己的 Lua VM（由 tools/patch_apk.py 注入到明文的
--            assets/src/config.luac 末尾，游戏启动时自动执行）。
--  传输层  ：libcocos2dlua.so 里静态链接的 LuaSocket（socket.core）。
--  监听    ：0.0.0.0:PORT，客户端被改包为连 127.0.0.1:PORT，因此全部闭环在
--            本机进程内，不需要 PC、不需要网络。
--
--  ⚠ 这个文件在本进程里最先跑、最不能出错：
--    * 全程 pcall 包裹，任何异常都必须变成 logcat 可见的一行日志；
--    * 服务器必须在 config.luac 之后的第一个调度帧就起来（客户端在
--      config.luac 之前就已经发过一轮 HTTP，晚了就直接 connection refused）。
--
--  设计要点
--   * 主线程非阻塞：用 select(timeout=0) 轮转，绝不阻塞渲染/逻辑线程。
--   * 由 cc.Director 的 scheduler 每 50ms 驱动一次 tick（不依赖线程）。
--   * 所有失败都通过 __dsh_rep 上报（HTTP 自请求 + print/logcat 双通道）。
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 最先执行：诊断通道 + 尽早绑定端口
--   print 走 [LUA-print] tag，adb logcat 直接可见，不依赖网络。
--   注意：本文件是启动早期注入的，所以先装一个不依赖任何外部变量的 rep。
-- ---------------------------------------------------------------------------
local M = {}

local LOGTAG = "[DSH_SRV] "

local function rawrep(tag, val)
    pcall(function() print(LOGTAG .. tostring(tag) .. " " .. tostring(val)) end)
end
M.rawrep = rawrep

local function rep(tag, val)
    rawrep(tag, val)
    local url = M.REPORT_URL
    if url == nil or url == "" then return end
    pcall(function()
        local r = cc.XMLHttpRequest:new()
        r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
        local v = tostring(val)
        if #v > 170 then v = v:sub(1, 170) end
        r:open("GET", url .. "/DSH_SRV?tag=" .. tostring(tag) .. "&v=" ..
               v:gsub("[^%w%.%:/-]", "_"))
        r:send()
    end)
end
M.rep = rep

-- 尽早起服务：先试一次（socket 可能还没注册），失败交给 scheduler 重试。
pcall(function() rawrep("preload", "config.luac reached") end)

-- ============================================================================
--  端口自检：绑定失败最常见的原因是端口被占，必须能一眼看出来
-- ============================================================================

-- 这些全局由 patch_apk.py 注入时替换（不要手改这里的默认值以外的东西）
M.PORT = 18080
M.HOST_IP = "127.0.0.1"        -- 下发给客户端的游戏服地址
M.GAME_PORT = 19000            -- 游戏服（TCP 协议）端口
M.REPORT_URL = ""              -- 留空 = 不向外部上报（单机时无网可用）

local function r16(s, i)
    local a, b = s:byte(i, i + 1)
    if not a or not b then return 0 end
    return a + b * 256
end

local function jstr(v)
    if type(v) == "string" then
        return '"' .. v:gsub('\\', '\\\\'):gsub('"', '\\"'):gsub('\n', '\\n') .. '"'
    end
    if type(v) == "number" then
        if v == math.floor(v) then return string.format("%d", v) end
        return tostring(v)
    end
    if v == nil then return "null" end
    if v == true then return "true" end
    if v == false then return "false" end
    if type(v) == "table" then
        local isarr = true
        local n = 0
        for k in pairs(v) do
            n = n + 1
            if type(k) ~= "number" then isarr = false break end
        end
        if isarr then
            local out = {}
            for i = 1, #v do out[#out + 1] = jstr(v[i]) end
            return "[" .. table.concat(out, ",") .. "]"
        end
        local out = {}
        for k, x in pairs(v) do out[#out + 1] = jstr(tostring(k)) .. ":" .. jstr(x) end
        return "{" .. table.concat(out, ",") .. "}"
    end
    return '"?"'
end

-- ---------------------------------------------------------------------------
-- 载荷（先照抄 PC 版 mock_server.py 的形状，验证通了再按客户端真实需求收窄）
-- ---------------------------------------------------------------------------
function M.server_list()
    return { {
        id = "1", name = "单机本地服", ip = M.HOST_IP, port = M.GAME_PORT,
        state = 1, is_new = 1, world_lev = 1,
    } }
end

function M.gateway_payload()
    local sl = M.server_list()
    -- 客户端历史上用过多种字段名，全部给出，避免再猜 schema
    return {
        code = 0, msg = "ok", status = 0, result = 1,
        servers = sl, serverlist = sl, server_list = sl, list = sl,
        rolelist = {}, roles = {},
    }
end

local CONF = { code = 0, msg = "ok", status = 0, result = 1,
               maintain = 0, is_maintain = 0, white = 1 }

-- ---------------------------------------------------------------------------
-- HTTP 路由：完全对照 PC 版 mock_server.py 已跑通的行为
-- ---------------------------------------------------------------------------
function M.handle_http(req)
    local p = req.path
    if p:find("url_config", 1, true) then
        return 200, M.url_config_body(), "application/x-lua; charset=utf-8"
    end
    if p:find("version2.txt", 1, true) or p:find("version.txt", 1, true) then
        return 200, "208", "text/plain; charset=utf-8"
    end
    if p:find("/app/mobile/conf", 1, true) or p:find("/gateway/mobile/conf", 1, true)
       or p:find("/app/mobile/hft", 1, true) or p:find("/gateway/mobile/hft", 1, true) then
        return 200, jstr(CONF), "application/json; charset=utf-8"
    end
    if p:find("notice", 1, true) then
        return 200, jstr({ notice = "单机本地服测试" }), "application/json; charset=utf-8"
    end
    if p:find("gateway/mobile", 1, true) or p:find("app/mobile", 1, true) then
        return 200, jstr(M.gateway_payload()), "application/json; charset=utf-8"
    end
    -- 兜底：宽容的"无需更新"应答
    return 200, jstr({ code = 0, msg = "ok", status = 0, result = 1,
                       update = 0, version = 0 }), "application/json; charset=utf-8"
end

-- url_config_ewan.lua：客户端下载后当 Lua 载入，用它把 CDN/网关全部指回本机
function M.url_config_body()
    local b = "http://" .. M.HOST_IP .. ":" .. tostring(M.PORT)
    return table.concat({
        '-- generated by DSH embedded server',
        'URL_PATH = {',
        '  update = "' .. b .. '/update",',
        '  voice = "' .. b .. '/voice",',
        '  register = "' .. b .. '/register",',
        '  is_shenhe = false,',
        '  server = "' .. b .. '",',
        '}',
        'URL_PATH_ALL = { get = function(platform) return URL_PATH end }',
        'CDN_PATH_BASE = "' .. b .. '"',
        'CDN_URL = "' .. b .. '/cdn/"',
        'url_res_config = "' .. b .. '/cdn/"',
        'get_servers_url = "' .. b .. '/gateway/mobile/json"',
        'get_notice_url = "' .. b .. '/notice.json"',
        'WIN_UPDATE = false',
        'UPDATE_SKIP = false',
    }, "\n")
end

-- ---------------------------------------------------------------------------
-- 请求解析
-- ---------------------------------------------------------------------------
function M.parse_request(buf)
    local head, rest = buf:match("^(.-)\r?\n\r?\n(.*)$")
    if not head then return nil end
    local method, path = head:match("^(%u+)%s+(%S+)")
    if not method then return nil end
    local headers = {}
    for k, v in head:gmatch("\r?\n([%w%-]+):%s*([^\r\n]*)") do
        headers[k:lower()] = v
    end
    local n = tonumber(headers["content-length"] or "0") or 0
    if #rest < n then return nil end                              -- body 未收全
    path = path:gsub("^https?://[^/]+", "")
    local q = path:find("?", 1, true)
    if q then path = path:sub(1, q - 1) end
    return { method = method, path = path, headers = headers,
             body = rest:sub(1, n), used = #head + 4 + n }
end

local function http_response(status, body, ctype)
    local reason = (status == 200 and "OK") or (status == 404 and "Not Found") or "ERR"
    return table.concat({
        "HTTP/1.1 " .. status .. " " .. reason,
        "Content-Type: " .. ctype,
        "Content-Length: " .. tostring(#body),
        "Connection: close",
        "", body,
    }, "\r\n")
end
M.http_response = http_response

-- ---------------------------------------------------------------------------
-- 非阻塞服务器
-- ---------------------------------------------------------------------------
local state = {
    listening = false, server = nil, clients = {}, tick_count = 0,
    http_count = 0, conn_count = 0, err = nil, started = false,
    -- 游戏服（TCP 协议）侧
    game_listening = false, game_server = nil, game_clients = {},
    game_err = nil, game_conn_count = 0, game_bytes = 0,
}

local function close_client(c)
    pcall(function() c.sock:close() end)
end

local function hexdump(s, maxn)
    local out = {}
    local n = math.min(#s, maxn or 96)
    for i = 1, n do out[i] = string.format("%02x", s:byte(i)) end
    if #s > n then out[#out + 1] = ("..+%d"):format(#s - n) end
    return table.concat(out, " ")
end
M.hexdump = hexdump

-- 兜住 socket 全局：LuaSocket 由原生层注册，可能晚于本文件加载
local function ensure_socket()
    if socket then return true end
    local ok = pcall(function() socket = require("socket") end)
    return ok and socket ~= nil
end

-- ---------------------------------------------------------------------------
-- 游戏服（TCP）：客户端登录/进场景都走这里，先原样抓包
-- ---------------------------------------------------------------------------
function M.start_game()
    if state.game_listening then return true end
    if not ensure_socket() then
        state.game_err = "socket module not available yet"
        return false
    end
    local ok, err = pcall(function()
        local srv = assert(socket.bind("*", M.GAME_PORT))
        srv:settimeout(0)
        state.game_server = srv
        state.game_listening = true
    end)
    if not ok then
        state.game_err = tostring(err)
        return false
    end
    rep("game_listen", "port=" .. tostring(M.GAME_PORT) .. " ok")
    return true
end

function M.tick()
    if not ensure_socket() then return end
    if not state.listening then return end
    state.tick_count = state.tick_count + 1
    state.tick_calls = (state.tick_calls or 0) + 1

    local rd = { state.server }
    for _, c in ipairs(state.clients) do rd[#rd + 1] = c.sock end
    if state.game_server then rd[#rd + 1] = state.game_server end

    local ready = socket.select(rd, nil, 0)
    if ready and #ready > 0 then
        state.select_hits = (state.select_hits or 0) + #ready
    end
    for _, s in ipairs(ready or {}) do
        if s == state.server then
            local cs = state.server:accept()
            if cs then
                cs:settimeout(0)
                cs:setoption("tcp-nodelay", true)
                state.clients[#state.clients + 1] = { sock = cs, buf = "", t0 = os.time() }
                state.conn_count = (state.conn_count or 0) + 1
                -- 只汇报前 12 个连接，避免刷屏/占帧
                if state.conn_count <= 12 then
                    rep("accept", "#" .. state.conn_count .. " total_clients=" .. #state.clients)
                end
            end
        elseif s == state.game_server then
            local cs = state.game_server:accept()
            if cs then
                cs:settimeout(0)
                cs:setoption("tcp-nodelay", true)
                state.game_clients[#state.game_clients + 1] = { sock = cs, buf = "", t0 = os.time() }
                state.game_conn_count = state.game_conn_count + 1
                rep("game_accept", "#" .. state.game_conn_count ..
                    " from game client (total=" .. #state.game_clients .. ")")
            end
        else
            -- HTTP 连接
            for i = #state.clients, 1, -1 do
                local c = state.clients[i]
                -- ⚠ c 可能为 nil：同一个 socket 可能在 select 结果里出现多次，
                -- 而上面的分支已经把它从 state.clients 里移除了（实测报
                -- "attempt to index local 'c' (a nil value)"）。
                if c and c.sock == s then
                    local data, err, partial = c.sock:receive(65536)
                    c.buf = c.buf .. (data or partial or "")
                    if err and err ~= "timeout" then
                        if #c.buf > 0 then
                            rep("closed_with_data", "#" .. tostring(state.conn_count) ..
                                " len=" .. #c.buf .. " err=" .. tostring(err))
                        end
                        close_client(c)
                        table.remove(state.clients, i)
                    elseif #c.buf > 0 then
                        local req = M.parse_request(c.buf)
                        if req then
                            c.buf = c.buf:sub(req.used + 1)
                            state.http_count = state.http_count + 1
                            -- 前 40 个请求逐条打印，之后只计数
                            if state.http_count <= 40 then
                                rep("req", state.http_count .. " " .. req.method .. " " .. req.path
                                    .. " host=" .. tostring(req.headers.host))
                            end
                            local st, body, ct = M.handle_http(req)
                            pcall(function()
                                c.sock:send(http_response(st, body, ct))
                            end)
                            if #c.buf == 0 then
                                close_client(c)
                                table.remove(state.clients, i)
                            end
                        else
                            if (c.logged or 0) < 3 then
                                c.logged = (c.logged or 0) + 1
                                rep("partial", "#" .. tostring(state.conn_count) ..
                                    " len=" .. #c.buf .. " head=" ..
                                    c.buf:sub(1, 60):gsub("[^%w%p ]", "."))
                            end
                        end
                    end
                end
            end
            -- 游戏服连接：原样抓包（这是确定 wire 格式的唯一可靠来源）
            for i = #state.game_clients, 1, -1 do
                local c = state.game_clients[i]
                if c.sock == s then
                    local data, err, partial = c.sock:receive(65536)
                    local chunk = data or partial or ""
                    if #chunk > 0 then
                        c.buf = c.buf .. chunk
                        state.game_bytes = state.game_bytes + #chunk
                        rep("game_recv", "n=" .. tostring(state.game_conn_count) ..
                            " len=" .. #chunk .. " hex=" .. hexdump(chunk, 72))
                    end
                    if err and err ~= "timeout" then
                        rep("game_closed", "err=" .. tostring(err) ..
                            " total_bytes=" .. #c.buf ..
                            " all=" .. hexdump(c.buf, 72))
                        close_client(c)
                        table.remove(state.game_clients, i)
                    end
                end
            end
        end
    end

    -- 清理超时连接（避免 fd 泄漏）
    local now = os.time()
    for i = #state.clients, 1, -1 do
        if now - state.clients[i].t0 > 30 then
            close_client(state.clients[i])
            table.remove(state.clients, i)
        end
    end
    for i = #state.game_clients, 1, -1 do
        if now - state.game_clients[i].t0 > 300 then
            close_client(state.game_clients[i])
            table.remove(state.game_clients, i)
        end
    end
end

function M.start()
    if state.started then return state.listening end
    state.started = true
    if not ensure_socket() then
        state.err = "socket module not available yet"
        return false
    end
    local ok, err = pcall(function()
        local srv = assert(socket.bind("*", M.PORT))
        srv:settimeout(0)
        state.server = srv
        state.listening = true
    end)
    if not ok then
        state.err = tostring(err)
        rep("bind_fail", state.err)
        return false
    end
    rep("listening", tostring(M.PORT) .. " http=" .. tostring(state.listening))
    pcall(M.start_game)
    -- 暴露统一入口。注入块的每次诊断上报、observer 的每次 XHR 完成、
    -- 以及 install 的节拍器都会调用它（见文件顶部 M.pump 的说明：
    -- 之前三处各自实现、互相覆盖，是排查困难的根源，现已收敛为一个入口）。
    _G.__dsh_srv_tick = M.pump
    _G.__dsh_srv_pump = M.pump
    return true
end

-- ---------------------------------------------------------------------------
-- 版本检查放行（kick）
--   背景：客户端在本进程加载 config.luac **之前**就发了一批 HTTP（实测 9 次），
--   那一刻服务端还没绑定端口 → 全部 connect failed；客户端自己不重试，
--   于是卡在版本页。这里在 config 执行完、服务端就绪之后，主动驱动客户端
--   自己的"无需更新"入口（update_finish）。
--
--   候选名按可能性排序：update_finish / updateFinish / OnUpdateFinish /
--   update_complete / enterLogin / getNowVersion。
-- ---------------------------------------------------------------------------
M.KICK = true
M.KICK_DELAY = 1.0        -- 秒；太早的话这些模块还没加载

local KICK_NAMES = {
    "update_finish", "updateFinish", "OnUpdateFinish",
    "update_complete", "OnUpdateComplete", "updateFinishCallBack",
}

local function kick_once(tag)
    local found = {}
    for _, n in ipairs(KICK_NAMES) do
        local v = _G[n]
        if type(v) == "function" then found[#found + 1] = n end
    end
    if #found == 0 then
        rep("kick_miss", tag .. " none-of=" .. table.concat(KICK_NAMES, ","))
        return false
    end
    local name = found[1]
    local ok, err = pcall(_G[name])
    rep("kick", tag .. " called " .. name .. " ok=" .. tostring(ok) ..
        " err=" .. tostring(err) .. " (all=" .. table.concat(found, ",") .. ")")
    return ok
end

function M.install_kick()
    if not M.KICK then return end
    if _G.__dsh_kick then return end
    _G.__dsh_kick = true
    local ok, err = pcall(function()
        local d = cc and cc.Director and cc.Director:getInstance()
        local sch = d and d:getScheduler()
        if not sch then error("no scheduler") end
        local ticks, done = 0, false
        local entry
        local function tick()
            ticks = ticks + 1
            if ticks == 4 or ticks == 8 or ticks == 16 then
                -- 每次多等一会儿，给模块加载留时间；成功一次就停
                if not done and kick_once("tick" .. ticks) then
                    done = true
                end
            end
            if ticks >= 40 and entry then
                pcall(function() sch:unscheduleScriptEntry(entry) end)
            end
        end
        entry = sch:scheduleScriptFunc(tick, 0.5, false)
        rep("kick_arm", "entry=" .. tostring(entry) .. " delay=" .. M.KICK_DELAY)
    end)
    if not ok then rep("kick_arm_fail", tostring(err)) end
end

-- ---------------------------------------------------------------------------
-- 驱动探测：找出游戏里真正会跑的"每帧/定时"通道
--   实测 scheduleScriptFunc 注册成功但回调从不执行（无心跳），说明启动
--   阶段 Director 的调度器没有在驱动 script entries。这里同时试几种通道，
--   各自打点，找出可用的那一个（服务端轮询必须挂在能跑的通道上）。
-- ---------------------------------------------------------------------------
function M.probe_drivers()
    if _G.__dsh_probe then return end
    _G.__dsh_probe = true

    -- A) 全局 scheduler（已知注册成功）
    pcall(function()
        local d = cc.Director:getInstance()
        local sch = d:getScheduler()
        sch:scheduleScriptFunc(function()
            rep("drv_A", "scheduler fired")
        end, 0.5, false)
    end)

    -- B) 挂在临时 Node 上的 update
    pcall(function()
        local node = cc.Node:create()
        cc.Director:getInstance():getRunningScene():addChild(node)
        node:scheduleUpdateWithPriorityLua(function(dt)
            rep("drv_B", "node update fired dt=" .. tostring(dt))
        end, 0)
    end)

    -- C) Node 的 enterFrame 事件
    pcall(function()
        local node = cc.Node:create()
        cc.Director:getInstance():getRunningScene():addChild(node)
        local l = cc.EventListenerCustom:create("enterFrame",
            function(ev)
                rep("drv_C", "enterFrame fired")
            end)
        local disp = cc.Director:getInstance():getEventDispatcher()
        disp:addEventListenerWithSceneGraphPriority(l, node)
    end)

    -- D) performWithDelay 循环（cocos 的 action 系统，和 scheduler entries 不同）
    pcall(function()
        local node = cc.Node:create()
        cc.Director:getInstance():getRunningScene():addChild(node)
        local function loop()
            rep("drv_D", "action fired")
            node:runAction(cc.Sequence:create(
                cc.DelayTime:create(0.5),
                cc.CallFunc:create(loop)))
        end
        node:runAction(cc.Sequence:create(
            cc.DelayTime:create(0.5),
            cc.CallFunc:create(loop)))
    end)

    rep("probe_drivers", "A=scheduler B=node_update C=enterFrame D=action")
end

-- ---------------------------------------------------------------------------
-- 登录服连接探针：抓出客户端到底要连哪个地址
--   现象：客户端进入 game_start 后反复 openReconnect，但服务端 19000 端口
--   收不到任何连接 —— 必须知道它实际连的 host:port 才能对症。
--   gamenet.luac 里有 login_server_host_name / login_server_host_port 两个键。
-- ---------------------------------------------------------------------------
local PROBE_KEYS = {
    "login_server_host_name", "login_server_host_port", "game_net_id",
    "is_login_server_connected", "in_async_connect",
}

function M.install_probe()
    if _G.__dsh_probe_net then return end
    _G.__dsh_probe_net = true
    local ticks = 0
    local entry
    local ok = pcall(function()
        local d = cc.Director:getInstance()
        local sch = d:getScheduler()
        entry = sch:scheduleScriptFunc(function()
            ticks = ticks + 1
            -- 在若干时间点上采样，看客户端何时拿到/使用登录服地址
            if ticks == 10 or ticks == 30 or ticks == 80 or ticks == 200 then
                -- 注意：rep() 会把内容截到 170 字节，所以这里必须拆成多条小日志，
                -- 否则整条探针结果会被吞掉（踩过）。
                rep("np_t", tostring(ticks) ..
                    " GameNet=" .. type(GameNet) ..
                    " DengluCtrl=" .. type(DengluCtrl))
                rep("np_addr", tostring(_G.login_server_host_name) .. ":" ..
                    tostring(_G.login_server_host_port) ..
                    " conn=" .. tostring(_G.is_login_server_connected))
                rep("np_url", tostring(get_servers_url))
                rep("np_srv", tostring(URL_PATH and URL_PATH.server))
            end
            if ticks >= 260 and entry then
                pcall(function() sch:unscheduleScriptEntry(entry) end)
            end
        end, 0.25, false)
    end)
    if not ok then rep("probe_arm_fail", "no scheduler") end
end

-- ---------------------------------------------------------------------------
-- 静态应答表 + Java 后台线程（单机版的关键：摆脱引擎定时器）
--   背景：实测 config.luac→登录页这段，引擎不给 Lua 任何可用的每帧/定时回调
--   （scheduleScriptFunc / Node update / Action 三条路回调都不触发），
--   而 HTTP 服务端必须被动轮询 → 客户端连接全部堆在 CLOSE_WAIT。
--   解法：用 LuaJavaBridge 起一个 **Java 线程**跑阻塞式 accept 循环，完全绕开
--   引擎定时器。线程内不回调 Lua（那会跨线程破坏状态），而是只提供
--   **启动时预计算好的应答表**——单机版需要的路由是有限且静态的，足够。
-- ---------------------------------------------------------------------------
M.ENABLE_JAVA_SERVER = true

-- 相对路径 -> {status, body}；Java 线程按路径前缀匹配即可
function M.build_response_map()
    local function json(t) return jstr(t) end
    local map = {}
    local function put(path, body, ctype)
        map[#map + 1] = { path, body, ctype or "application/json; charset=utf-8" }
    end
    put("/update/version2.txt", "208", "text/plain; charset=utf-8")
    put("/update/version.txt", "208", "text/plain; charset=utf-8")
    put("/app/mobile/conf", json(CONF))
    put("/gateway/mobile/conf", json(CONF))
    put("/app/mobile/hft", json(CONF))
    put("/gateway/mobile/hft", json(CONF))
    put("/notice.json", json({ notice = "单机本地服测试" }))
    put("/gateway/mobile/json", json(M.gateway_payload()))
    put("/app/mobile/json", json(M.gateway_payload()))
    return map
end

-- 把应答表编码成 Java 线程能逐行解析的文本：path \t status \t ctype \t body(转义)
local function escape_field(s)
    return (tostring(s):gsub("\\", "\\\\"):gsub("\n", "\\n"):gsub("\t", "\\t"))
end

function M.response_map_text()
    local out = {}
    for _, e in ipairs(M.build_response_map()) do
        out[#out + 1] = escape_field(e[1]) .. "\t" .. escape_field(e[2]) ..
            "\t" .. escape_field(e[3])
    end
    return table.concat(out, "\n")
end

-- ---------------------------------------------------------------------------
-- Java 后台线程：阻塞式 accept，只用启动时预计算好的应答表
--   为什么必须这么做：引擎在加载阶段不给 Lua 任何定时回调（见上文），
--   所以服务端不能依赖 Lua 轮询。线程内**不回调 Lua**，避免跨线程操作 Lua 状态。
--
--   Java 侧结构（luaj.callStaticMethod("com/dsh/LocalServer", "startLocalServer", …)）：
--     class LocalServer {
--       static void startLocalServer(int port, String map, String urlCfg) {
--         new Thread(new Runnable(){ public void run(){ serve(port, map, urlCfg); } }).start();
--       }
--     }
--   应答表文本格式：每行 "path \t ctype \t body"，path 用前缀匹配。
-- ---------------------------------------------------------------------------
function M.start_java_server()
    if not M.ENABLE_JAVA_SERVER then return false end
    if _G.__dsh_java_srv then return true end

    local luaj
    -- LuaJavaBridge 的可用形态各版本不同，这里把常见几种都试一遍
    for _, loader in ipairs({
        function() return _G.luaj end,
        function() return require("luaj") end,
        function() return cc and cc.LuaJavaBridge end,
        function() return package and package.loaded and package.loaded.luaj end,
    }) do
        local ok, v = pcall(loader)
        if ok and type(v) == "table" and type(v.callStaticMethod) == "function" then
            luaj = v
            break
        end
    end
    if not luaj then
        rep("java_srv", "LuaJavaBridge not reachable; staying on Lua polling")
        return false
    end

    local map_text = M.response_map_text()
    local url_cfg = M.url_config_body()
    local ok, err = pcall(function()
        local ok2, r = luaj.callStaticMethod("com/dsh/LocalServer", "startLocalServer",
            { M.PORT, map_text, url_cfg }, "(ILjava/lang/String;Ljava/lang/String;)V")
        if not ok2 then error(tostring(r)) end
        rep("java_srv", "started on port " .. tostring(M.PORT) ..
            " routes=" .. tostring(select(2, map_text:gsub("\n", "\n")) + 1))
    end)
    if not ok then
        rep("java_srv_fail", tostring(err))
        return false
    end
    _G.__dsh_java_srv = true
    return true
end

-- ---------------------------------------------------------------------------
-- 单机登录驱动器
--   SuperSDK 的初始化已被 DEX 补丁摘掉，所以永远不会有真正的平台登录回调；
--   游戏的登录数据入口是 Lua 全局：
--       sdkBackLogin(code, "openid#username#timestamp#sign#token#tpUid")
--         → DengluPlatForm:getInstance():onLoginInfo(data)   (sdk_function proto#12)
--   它由 require('sdk_function') 注册，因此一开始可能还不存在 —— 在 tick 里
--   反复尝试，直到成功。服务端是我们自己的，票据内容不必真实。
--
--   ⚠ 放在服务端本体而不是 observer.lua：注入块里这份源码会被执行两次
--     （一次由注入块前置启动，一次由末尾兜底包装），后执行的那次会把
--     observer 包装过的 __dsh_srv_tick 覆盖掉。放在本体里天然幂等。
-- ---------------------------------------------------------------------------
M.LOGIN_PAYLOAD = "dsh_openid#dsh_user#%s#dsh_sign#dsh_token#1001"

-- ---------------------------------------------------------------------------
-- 模块观测：包裹全局 require，记录含 denglu/login 的模块何时被加载、返回什么。
-- 目的：搞清 DengluMgr 到底以什么方式/什么名字进入运行环境
--      （实测：全局里没有、package.loaded 里没有、直接 require 也拿不到）。
-- ---------------------------------------------------------------------------
function M.install_require_watch()
    if _G.__dsh_reqwatch then return end
    local orig = _G.require
    if type(orig) ~= "function" then
        rep("reqwatch", "require=" .. type(orig) .. " (skip)")
        return
    end
    _G.__dsh_reqwatch = true
    _G.require = function(name, ...)
        local r = orig(name, ...)
        pcall(function()
            if type(r) == "table" and type(name) == "string" then
                local ln = name:lower()
                -- ⚠ 关键修正：此前只"记录名字"，没有**保存模块表**，
                --   所以才拿不到 ver_load_start。
                --   `file_update` 的方法表就是这个返回值，保存它即可调用
                --   file_update.ver_load_start(file_update)。
                if ln:find("file_update", 1, true) and not _G.__dsh_file_update then
                    _G.__dsh_file_update = r
                    rep("reqwatch", "captured module table: " .. name ..
                        " (ver_load_start=" .. type(r.ver_load_start) ..
                        ", update_finish=" .. type(r.update_finish) .. ")")
                end
                if (ln:find("denglu") or ln:find("login")) then
                    M._req_hits = (M._req_hits or 0) + 1
                    if M._req_hits <= 12 then
                        rep("reqwatch", name .. " -> table (denglu/login module)")
                    end
                end
            end
        end)
        return r
    end
    -- 立即自检：require 在原位到底能不能用（拿 config 做白盒测试）
    pcall(function()
        local ok, v = pcall(orig, "config")
        rep("reqwatch_probe", "require('config') ok=" .. tostring(ok) ..
            " type=" .. type(v))
    end)
    rep("reqwatch", "global require wrapped")
end

-- ---------------------------------------------------------------------------
-- 服务器列表驱动
-- ---------------------------------------------------------------------------
--     DengluMgr:getInstance():requestDefaultServerList()
--       └─ 向 get_servers_url（我们指向 127.0.0.1:18080）POST
--          → 内置服务端回 {"server_list":[{ip,port,...}]}
--          → 客户端按列表里的 ip/port 去连**游戏服**（我们给的是 19000）
--   这一步是通往 TCP 游戏服的最后一道门，所以主动替它调用。
-- ---------------------------------------------------------------------------
function M.request_server_list()
    if _G.__dsh_srv_list_req then return true end

    -- 找 DengluMgr 实例。多条路都试：
    --   1) 全局（实测注入时机下为 nil）
    --   2) require 该模块（游戏自带 require 可能能加载）
    --   3) 全局表扫描（实测 160 个全局里没有）
    local mgr = _G.DengluMgr

    if type(mgr) ~= "table" and type(_G.require) == "function" then
        for _, mod in ipairs({ "game/login/denglu_mgr", "src.game.login.denglu_mgr",
                               "game.login.denglu_mgr", "denglu_mgr" }) do
            local ok, v = pcall(_G.require, mod)
            if ok and type(v) == "table" then
                if not _G.__dsh_req_note then
                    _G.__dsh_req_note = true
                    rep("srvlist_req", "require(" .. mod .. ") ok, keys=" ..
                        tostring(v.getInstance) .. "/" .. tostring(v.New))
                end
                mgr = v
                break
            end
        end
    end

    if type(mgr) ~= "table" then
        if not _G.__dsh_srvlist_noted then
            _G.__dsh_srvlist_noted = true
            local bymeth = {}
            pcall(function()
                for k, v in pairs(_G) do
                    if type(v) == "table" and type(v.requestDefaultServerList) == "function" then
                        bymeth[#bymeth + 1] = tostring(k)
                    end
                end
            end)
            rep("srvlist_wait", "no mgr; bymeth(" .. #bymeth .. ")=" ..
                table.concat(bymeth, ","):sub(1, 50))
        end
        return false
    end

    if (M._srvlist_tries or 0) >= 400 then return false end
    M._srvlist_tries = (M._srvlist_tries or 0) + 1
    local ok, err = pcall(function()
        local inst = mgr
        if type(mgr.getInstance) == "function" then inst = mgr:getInstance() end
        if type(inst) ~= "table" then error("instance type=" .. type(inst)) end
        local fn = inst.requestDefaultServerList
        if type(fn) ~= "function" then
            error("requestDefaultServerList=" .. type(fn))
        end
        inst:requestDefaultServerList()
    end)
    if M._srvlist_tries <= 3 then
        rep("srvlist", "try=" .. M._srvlist_tries .. " ok=" .. tostring(ok) ..
            (ok and "" or (" err=" .. tostring(err))))
    end
    if ok then _G.__dsh_srv_list_req = true end
    return ok
end

-- ---------------------------------------------------------------------------
-- 主动发起平台登录
--   实测：客户端停登录页、**一条自己的游戏请求都没发**（服务端只收到我们自己
--   的诊断上报）。原因是登录流程根本没启动 ——
--   `beginThirdPartyLogin`（sdk_function proto#1）定义了但没人调用，
--   正常是玩家点登录按钮才触发。所以这里替它调一次。
--   调用后 SDK 侧会走 SuperPlatform.login；我们把 init 摘掉了，所以不会有真实
--   回调，紧接着由 M.try_login 注入自造票据完成闭环。
-- ---------------------------------------------------------------------------
function M.begin_login()
    if _G.__dsh_begin_login then return true end
    local f = _G.beginThirdPartyLogin
    if type(f) ~= "function" then return false end
    _G.__dsh_begin_login = true
    local ok, err = pcall(f)
    rep("begin_login", "called ok=" .. tostring(ok) ..
        (ok and "" or (" err=" .. tostring(err))))
    return ok
end

-- ---------------------------------------------------------------------------
-- 直接触发选服事件（绕过整条登录链）
--   已查清：denglu_mgr 的 proto#4 绑定了 `REQUEST_SERVERLIST`，
--   触发后客户端会向 get_servers_url 请求服务器列表 → 拿到 host/port → 连游戏服。
--   而登录链（sdkBackLogin → DengluPlatForm:onLoginInfo → loginCallback）
--   依赖 DengluPlatForm / DengluMgr 两个**尚未创建**的模块，
--   所以直接走事件更短、更可靠。
-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------
-- 统一入口：一切"推进"都从这里走
--   ⚠ 踩坑：此前把推进逻辑分散在 __dsh_srv_tick / install 的 safe_tick /
--     observer 的 pump 三处，且 __dsh_srv_tick 被反复覆盖（源码会执行两次），
--     导致"登录/选服推进"时而生效时而失效，排查成本很高。
--     现在只保留 M.pump 一个入口，其它地方一律调它。
-- ---------------------------------------------------------------------------
-- ⚠ 重入保护（本轮回溯出来的自伤性崩溃）：
--   print(注入的包装器) → __dsh_rep → __dsh_srv_tick(=safe_tick) → M.pump
--     → M.rep → rawrep → print → __dsh_rep → __dsh_srv_tick → … 无限递归。
--   __dsh_srv_tick 是在 M.install() 末尾被赋值的，而 print 包装器装在其后，
--   所以从那一刻起每一次 print 都会递归；栈被撑爆后异常被 pcall 吞掉，
--   外部表现是"进入加载阶段后 Lua 日志突然全无，随后整机冻结"。
--   这里给 pump 本身加重入锁，任何调用路径都不会再自噬。
function M.pump()
    if _G.__dsh_in_tick then return end
    _G.__dsh_in_tick = true
    local ok, err = pcall(M.pump_inner)
    _G.__dsh_in_tick = false
    if not ok then
        _G.__dsh_pump_err = (_G.__dsh_pump_err or 0) + 1
        if _G.__dsh_pump_err <= 3 then rawrep("pump_err", tostring(err)) end
    end
end

function M.pump_inner()
    pcall(M.tick)                                -- 排空 socket
    pcall(M.preload_login_record)                -- 预置 last_login_account（让 openView 走登录分支）
    -- 启动推进兜底：ver_load_start 是**全局函数**（file_update.luac 根原型
    -- 的 FNEW/GSET，已用 tools/analyze_flow2.py 验证），正常情况下应由
    -- main() 自己调用（我们在 config.luac 里置 _is_game_restart = true）。
    -- 这里再兜一层：只要它出现就调一次，避免任何时机问题。
    pcall(M.try_boot)
    -- ⚠ 替身默认关闭：真模块（denglu_mgr/denglu_platform）本来就会随登录流程加载，
    --   而我们提前往 _G 塞替身会参与 initInstance 的"遍历 _G 所有表并调用 getInstance"
    --   （file_update proto#31），存在干扰原初始化的风险 —— 需 A/B 对照验证。
    if M.USE_SHIMS then
        pcall(M.install_platform_shim)
        pcall(M.install_manager_shim)
    end
    pcall(M.begin_login)                         -- 触发平台登录（若还没触发）
    pcall(M.try_login)                           -- 注入登录票据
    if not _G.__dsh_srv_list_req then
        pcall(M.request_server_list_via_event)   -- 直接触发选服事件
    end
    if _G.__dsh_logged_in then
        pcall(M.request_server_list)             -- 老路径兜底
    end
    -- 最直接的一步：只要 GameNet 出现，就直接连游戏服拿 TCP 首包
    pcall(M.try_connect_game_server)
end

-- 是否启用"缺失全局替身"。默认关闭，用于 A/B 对照。
M.USE_SHIMS = false

function M.request_server_list_via_event()
    if _G.__dsh_srvlist_fired then return true end
    local ge = _G.GlobalEvent
    local de = _G.DengluEvent
    if type(ge) ~= "table" and type(de) ~= "table" then
        if not _G.__dsh_evt_noted then
            _G.__dsh_evt_noted = true
            rep("event_wait", "GlobalEvent=" .. type(ge) .. " DengluEvent=" .. type(de))
        end
        return false
    end
    M._evt_tries = (M._evt_tries or 0) + 1
    local ok, err = pcall(function()
        local evt = ge or de
        local inst = evt.getInstance and evt:getInstance() or evt
        local fire = inst.Fire or inst.fire or inst.dispatch
        if type(fire) ~= "function" then
            error("no Fire on event object (" .. type(inst.Fire) .. ")")
        end
        -- 有些实现是 Fire(name, data)，有些是 Fire({name=...})
        pcall(function() inst:Fire("REQUEST_SERVERLIST", {}) end)
        pcall(function() inst:Fire("REQUEST_SERVERLIST") end)
        pcall(function() inst:Fire({ name = "REQUEST_SERVERLIST" }) end)
    end)
    if M._evt_tries <= 3 or ok then
        rep("event_fire", "try=" .. M._evt_tries .. " ok=" .. tostring(ok) ..
            (ok and "" or (" err=" .. tostring(err):sub(1, 60))))
    end
    if ok then _G.__dsh_srvlist_fired = true end
    return ok
end

-- ---------------------------------------------------------------------------
-- DengluPlatForm 最小替身
--   为什么需要：登录链是
--       sdkBackLogin(0, info)
--         → DengluPlatForm:getInstance():onLoginInfo(info)   (sdk_function proto#12)
--   而 DengluPlatForm 由 game/login/denglu_platform.luac 注册，
--   实测在客户端停住的情况下**从未被创建**（全局 nil，且该模块无任何路径引用）。
--   既然插件侧拿不到它，就在 Lua 里造一个**最小等价替身**：
--   只补 sdkBackLogin 与 loginCallback 实际会用到的那几个方法。
--
--   原实现（读字节码得到）：
--     onLoginInfo(info): unpack(Split(info,'#')) → openid,username,timestamp,
--                        sign,token,channelId；若 openid 与当前相同则先 logout；
--                        填充 self.info，置 is_logined=true，再调 loginCallback(self)
-- ---------------------------------------------------------------------------
local function split_hash(s)
    local out = {}
    for part in tostring(s):gmatch("([^#]*)") do out[#out + 1] = part end
    return out
end

function M.install_platform_shim()
    if _G.__dsh_plat_shim then return true end
    if type(_G.DengluPlatForm) == "table" then return false end   -- 真货已存在，不覆盖

    local inst
    local P = {}

    function P:getInstance() return inst end
    function P:isLogin() return inst.is_logined == true end
    function P:getInfo() return inst.info end
    function P:getUId()
        return (inst.info and inst.info.openid) or "dsh_openid"
    end
    function P:getTimestamp() return (inst.info and inst.info.timestamp) or "0" end
    function P:getToken() return (inst.info and inst.info.token) or "dsh_token" end
    function P:getSign() return (inst.info and inst.info.sign) or "dsh_sign" end
    function P:getChannelId() return (inst.info and inst.info.channelId) or "dsh" end
    function P:getPlatform() return _G.PLATFORM_NAME or "ewan" end
    function P:onLogout() inst.is_logined = false inst.info = nil end

    function P:onLoginInfo(info)
        local t = split_hash(info)
        local openid, username, timestamp, sign, token, channelId =
            t[1], t[2], t[3], t[4], t[5], t[6]
        if inst.info and inst.info.openid == openid then
            P:onLogout()
            return
        end
        inst.info = {
            openid = openid, username = username, timestamp = timestamp,
            sign = sign, token = token, channelId = channelId,
        }
        inst.is_logined = true
        _G._no_need_restar = nil
        rep("plat_shim", "onLoginInfo openid=" .. tostring(openid))
        -- 原实现最后调 loginCallback(self)；这里只做能安全做的部分
        -- （真正的 loginCallback 依赖 DengluMgr/GlobalEvent，缺它们时静默跳过）
        pcall(function()
            if type(P.loginCallback) == "function" then P:loginCallback() end
        end)
    end

    function P:loginCallback()
        rep("plat_shim", "loginCallback (stub: 跳过依赖 DengluMgr 的部分)")
    end

    inst = { is_logined = false, info = nil }
    _G.DengluPlatForm = P
    _G.__dsh_plat_shim = true
    rep("plat_shim", "DengluPlatForm shim installed")
    return true
end

-- ---------------------------------------------------------------------------
-- DengluMgr 最小替身
--   为什么需要：`denglu_ctrl:openView()`（proto#48）的逻辑是
--       local d = self.manager:getLoginData()
--       if d.account_name ~= "" and d.usrName ~= "" and d.password ~= "" then
--           self.dispather:Fire(DengluEvent.LOGIN_NEW_USER_REQUEST, d)   -- 直接开打
--       else
--           self.loginView:showPanel(4)                                  -- 停在登录页
--       end
--   即：**本地没有登录数据时，客户端就会一直停在登录页** —— 这正是我们观察到的现象。
--   所以补一个 DengluMgr 替身，并让它返回一份可用的登录数据，
--   openView 就会走"直接请求登录"那一支，从而向游戏服发包。
-- ---------------------------------------------------------------------------
function M.install_manager_shim()
    if _G.__dsh_mgr_shim then return true end
    if type(_G.DengluMgr) == "table" then return false end
    if not _G.__dsh_plat_shim then return false end

    local inst = {
        loginData = {
            account_name = "dsh_account",
            usrName = "dsh_user",
            password = "12345678",
            rid = 1001,
            srv_id = "1",
            srv_name = "单机本地服",
        },
        defaultLogin = nil,
    }
    local Mgr = {}
    function Mgr:getInstance() return inst end
    function Mgr:getLoginData(key)
        if key ~= nil then return inst.loginData[key] end
        return inst.loginData
    end
    function Mgr:getDefaultLogin() return inst.defaultLogin end
    function Mgr:setDefaultLogin(d) inst.defaultLogin = d end
    function Mgr:getServerData() return { host = _G.__DSH_SERVER and _G.__DSH_SERVER.HOST_IP or "127.0.0.1",
                                          port = _G.__DSH_SERVER and _G.__DSH_SERVER.GAME_PORT or 19000 } end
    function Mgr:setCanLoginOpenGame(v) inst.canLogin = v end
    function Mgr:isCanLoginGame() return true end
    function Mgr:clearCache() end
    function Mgr:__delete() end
    function Mgr:requestDefaultServerList()
        -- 走我们自己的合成路径（见 request_server_list_via_event / 网关合成器）
        return false
    end

    _G.DengluMgr = Mgr
    _G.__dsh_mgr_shim = true
    rep("mgr_shim", "DengluMgr shim installed (loginData preloaded)")
    return true
end

-- ---------------------------------------------------------------------------
-- 直连游戏服：game_start.luac 在"已经成功连接过"时会走 GameNet 的连接路径
--   gamenet.luac 的公开 API（读 root 表得到）：
--     GameNet:getInstance()
--     GameNet:SetLoginServerInfo(host, port)     ← 设置登录服地址
--     GameNet:ConnectLoginServer() / AsyncConnectLoginServer()
--     GameNet:IsLoginServerConnect() / DisconnectLoginServer()
--   这是我们拿到 TCP 首包最直接的入口（绕开整条登录/选服链）。
-- ---------------------------------------------------------------------------
function M.try_connect_game_server()
    if _G.__dsh_tcp_tried then return true end
    local GN = _G.GameNet
    if type(GN) ~= "table" and type(package) == "table"
       and type(package.loaded) == "table" then
        for k, v in pairs(package.loaded) do
            if type(v) == "table" and type(k) == "string"
               and (k:lower():find("gamenet", 1, true) or k:lower():find("net_manager", 1, true)) then
                GN = v
                break
            end
        end
    end
    if type(GN) ~= "table" then
        if not _G.__dsh_gn_noted then
            _G.__dsh_gn_noted = true
            local keys = {}
            if type(package) == "table" and type(package.loaded) == "table" then
                for k in pairs(package.loaded) do
                    if type(k) == "string" and #keys < 25 then keys[#keys + 1] = k end
                end
            end
            rep("gamenet_wait", "GameNet=" .. type(_G.GameNet) ..
                " loaded(" .. #keys .. ")=" .. table.concat(keys, ","):sub(1, 60))
        end
        return false
    end
    local host, port = "127.0.0.1", (M.GAME_PORT or 19000)
    local ok, err = pcall(function()
        local inst = GN
        if type(GN.getInstance) == "function" then inst = GN:getInstance() end
        if type(inst.SetLoginServerInfo) == "function" then
            if type(inst.setLoginServerInfo) == "function" then
                inst:setLoginServerInfo(host, port)
            else
                inst:SetLoginServerInfo(host, port)
            end
        end
        if type(inst.ConnectLoginServer) == "function" then
            inst:ConnectLoginServer()
        elseif type(inst.AsyncConnectLoginServer) == "function" then
            inst:AsyncConnectLoginServer()
        else
            error("no ConnectLoginServer on instance")
        end
    end)
    rep("gamenet_connect", "ok=" .. tostring(ok) ..
        (ok and "" or (" err=" .. tostring(err):sub(1, 60))))
    if ok then _G.__dsh_tcp_tried = true end
    return ok
end

-- ---------------------------------------------------------------------------
-- 预置本地登录数据（本轮突破点）
--
--   已从字节码确认：
--     * `denglu_ctrl:openView()`（proto#48）只在
--         manager:getLoginData().account_name/usrName/password 都非空时
--         才 Fire(LOGIN_NEW_USER_REQUEST)；否则只 showPanel 停在登录页。
--     * `denglu_mgr:getLoginData()`（proto#18）只是 `return self.loginData`。
--     * `DengluMgr.__init`（proto#2）会用
--         SaveLocalData:readTableForKey('last_login_account')
--       读出上次登录账号，并填充 loginData 的
--         account_name / password / usrName / rid / main_srv_id / srv_id / srv_name
--         / can_create_role / open_time / host / port / ip ...
--
--   因此：**在 DengluMgr 构造之前把 `last_login_account` 写进本地存档**，
--   openView 第一次执行时条件即成立，客户端就会直接走"登录"分支并连游戏服。
--
--   写入 API（save_local_data.luac 的 root 表）：
--     SaveLocalData:getInstance():writeLuaTable(key, table)
-- ---------------------------------------------------------------------------
M.LOGIN_RECORD = {
    -- ⚠ 键名必须与 denglu_mgr 里 loginData 的字段名**完全一致**（带下划线）
    account_name = "dsh_account",
    password = "12345678",
    usrName = "dsh_user",
    rid = 1001,
    main_srv_id = "1",
    srv_id = "1",
    srv_name = "单机本地服",
    can_create_role = 1,
    open_time = "0",
    host = "127.0.0.1",
    port = 19000,
    ip = "127.0.0.1",
    role_count = 0,
    status = 0,
    platform_flag = "ewan",
}

function M.preload_login_record()
    if _G.__dsh_rec_done then return true end

    -- 首选：直接写底层 cc.UserDefault（SaveLocalData 就是它的一层包装，
    -- 见 save_local_data.luac：proto#0 同时引用 UserDefault/cc/user_default）。
    -- 表按 proto#3 的格式序列化成 "[k] = v,\n" 形式。
    local function write_via_userdefault()
        local ud = cc and cc.UserDefault and cc.UserDefault:getInstance()
        if not ud then return nil, "cc.UserDefault unavailable" end
        -- ⚠ 关键修正：游戏自己的序列化器（save_local_data proto#3）对字符串用
        --   `string.format("%q", v)`，而我最初用 tostring() —— 那会写出
        --   `[account_name] = dsh_account`（**未加引号**，非法 Lua），
        --   读回时 loadstring 必然失败，等于没写。
        local function ser(v)
            local t = type(v)
            if t == "string" then return string.format("%q", v)
            elseif t == "number" or t == "boolean" then return tostring(v)
            else return "nil" end
        end
        local parts = {}
        for k, v in pairs(M.LOGIN_RECORD) do
            local key
            if type(k) == "string" then key = "[" .. string.format("%q", k) .. "]"
            else key = "[" .. tostring(k) .. "]" end
            parts[#parts + 1] = key .. " = " .. ser(v) .. ",\n"
        end
        -- ⚠⚠ 关键修正（这是"预置了却读不到"的真因）：
        --   游戏读取器 readTableForKey（save_local_data proto#7）实现是
        --       local str = self:readStringForKey(key)
        --       local f = loadstring("return {" .. str .. "}")   ← 自己补花括号
        --       return f()
        --   所以存档里**只能存内层内容**（形如 `["k"] = v,`），不能带外层 `{}`。
        --   我最初写成 `{ ... }`，读出来就变成 `{{...}}` —— 取 d.account_name 自然是 nil，
        --   于是 openView 仍然走"显示登录面板"分支。
        local body = table.concat(parts)
        -- 自检：按游戏的方式解析（"return {" .. body .. "}"）
        local chunk = loadstring("return {" .. body .. "}")
        if not chunk then return nil, "serialized body is not valid Lua" end
        local okparse, tbl = pcall(chunk)
        if not okparse or type(tbl) ~= "table" or tbl.account_name ~= "dsh_account" then
            return nil, "round-trip parse failed"
        end
        ud:setStringForKey("last_login_account", body)
        ud:flush()
        local back = ud:getStringForKey("last_login_account", "")
        return back, nil
    end

    local back, werr = write_via_userdefault()
    if werr then
        if not _G.__dsh_rec_noted then
            _G.__dsh_rec_noted = true
            rep("record_wait", werr)
        end
        return false
    end
    rep("record", "wrote last_login_account len=" .. tostring(#tostring(back)) ..
        " sample=" .. tostring(back):gsub("[^%w_%[%]=,]", " "):sub(1, 60))
    _G.__dsh_rec_done = true
    return true
end

-- ---------------------------------------------------------------------------
-- 启动推进：调用 ver_load_start（本轮找到的真正断点）
--
--   证据链：
--     * 模块加载日志只进行到 22 个就停住，最后两个是
--         src/sdk_function.luac、src/file_update.luac
--       （即 main() 已执行到 require('file_update') 之后）；
--     * main.luac 的判定是
--         if (not IS_PLATFORM_LOGIN) or _is_game_restart then ver_load_start() end
--       而 config.luac 里 IS_PLATFORM_LOGIN = true，所以 main() **不会**自己调它，
--       原设计是等 SDK 回调 sdkBackInit → ver_load_start()；
--     * 我们把 SuperPlatform.init 摘掉了（为了消掉死 SDK 的弹窗），
--       于是那个回调永远不会来 —— **整条启动流程就断在这里**，
--       后面 688 个模块（含 denglu_*）一个都不会被加载。
--
--   所以：我们在 Lua 侧主动调用 ver_load_start()（必要时退回 update_finish()），
--   让客户端自己继续往下走。
-- ---------------------------------------------------------------------------
local BOOT_NAMES = { "ver_load_start", "update_finish" }

-- ---------------------------------------------------------------------------
-- 自驱动节拍器（不依赖客户端请求，也不依赖调度器）
--   背景：已验证
--     * `scheduleScriptFunc` 的回调在本次启动中**不触发**；
--     * 客户端自己的 HTTP 走 Java 原生层，不经过我们包装的 Lua XHR 实例方法；
--     * 唯一实测**一定触发**的是一次性 `node:runAction(Sequence(DelayTime, CallFunc))`。
--   所以用同一机制做"自链式"轮询：每次回调里再挂下一个一次性动作。
--   这条链在 update_finish 的逐帧加载期间也不会断（每次只挂一个短延迟动作）。
-- ---------------------------------------------------------------------------
function M.start_watchdog()
    if _G.__dsh_wd then return end
    local node = _G.__dsh_srv_node
    if not node then return end
    _G.__dsh_wd = true

    local ticks = 0
    local errs = 0
    local function step()
        ticks = ticks + 1
        local ok, err = pcall(M.pump)
        if not ok then
            errs = errs + 1
            if errs <= 3 then rep("wd_err", tostring(err):sub(1, 70)) end
        end
        -- 每 8 次（约 2 秒）汇报一次，便于观察推进情况
        if ticks % 8 == 1 then
            rep("wd", "t=" .. ticks ..
                " booted=" .. tostring(_G.__dsh_booted) ..
                " logged=" .. tostring(_G.__dsh_logged_in) ..
                " srvreq=" .. tostring(_G.__dsh_srv_list_req) ..
                " GameNet=" .. type(_G.GameNet) ..
                " DengluMgr=" .. type(_G.DengluMgr))
        end
        if ticks < 240 then          -- 最多跑 ~60 秒
            pcall(function()
                node:runAction(cc.Sequence:create(
                    cc.DelayTime:create(0.25),
                    cc.CallFunc:create(function() pcall(step) end)))
            end)
        end
    end
    pcall(step)
    rep("wd", "watchdog started")
end

-- ---------------------------------------------------------------------------
-- 延迟启动推进（本轮修正）
--
--   症状：客户端停在初始加载界面，加载动画也点不掉。
--   实测关键日志：
--       boot_wait ver_load_start=nil update_finish=nil
--   即：我们调 `ver_load_start` 的时机**太早** —— 它由 `file_update.luac` 导出，
--   而该文件是在 `main()` 里才 `require` 的；我们的注入在 `loadConfig()`
--   阶段（更早），所以那时它必然还是 nil，调用落空后客户端就停住了。
--
--   修正：把启动推进挂到"每次被驱动时都重试"，并且**不再依赖任何单一时机**。
--   一旦 `ver_load_start`/`update_finish` 出现就立刻调用（只成功一次）。
-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------
-- 启动推进：让 main() 自己走 ver_load_start（本轮弄清的正确机制）
--
--   反汇编 main.luac proto#0 的最后一段（指令 118-127）：
--       118  GGET  IS_PLATFORM_LOGIN
--       121  ISF   -> 若为假则跳到 126（调用 ver_load_start）
--       123  GGET  _is_game_restart
--       124  ISF   -> 若为假则跳到 128（直接 return）
--       126  GGET  ver_load_start        ← 注意：是 **GGET**，即全局查找
--       127  CALL  ver_load_start()
--       128  return
--   等价源码：if (not IS_PLATFORM_LOGIN) or _is_game_restart then ver_load_start() end
--
--   两个关键结论：
--     1) `ver_load_start` 走的是 **GGET（全局）**，所以它确实是全局函数 ——
--        我此前判定"它是模块表方法、所以拿不到"是错的；
--        真正的原因只是**时机**：它由 file_update.luac 导出，比我第一次调用晚。
--     2) 只要 `_is_game_restart` 为真，main() 就会自己调用它 ——
--        而这个标志是全局、随时可写。
--
--   所以本轮先设 `_is_game_restart = true`（让 main 的判断成立），
--   同时把 `ver_load_start` 的调用做成**持续重试**（直到它出现）。
-- ---------------------------------------------------------------------------
-- ⚠ 保持禁用：曾设 _is_game_restart = true 想让 main() 走 ver_load_start，
--   但那一刻 ver_load_start 仍是 nil（由 file_update.luac 稍后注册），
--   main() 会因 "attempt to call a nil value" 抛错中断 ——
--   模块加载数从 1950 掉回 975，反而更早卡死。见文件上的详细说明。
M.FORCE_RESTART_FLAG = false

function M.set_restart_flag()
    return false
end

function M.try_boot()
    if _G.__dsh_booted then return true end

    -- 首选：从捕获到的 file_update 模块表上调用它的 ver_load_start()
    -- （注意：file_update 的根原型并不返回表，所以这条通常拿不到 ——
    --   真正的实现在下面"全局"那条分支：ver_load_start 由 file_update.luac
    --   根原型的 FNEW/GSET 注册为**全局**，已由字节码确认。）
    local fu = _G.__dsh_file_update
    if type(fu) == "table" then
        for _, n in ipairs(BOOT_NAMES) do
            if type(fu[n]) == "function" then
                local ok, err = pcall(fu[n], fu)
                rep("boot", "file_update." .. n .. "() ok=" .. tostring(ok) ..
                    (ok and "" or (" err=" .. tostring(err):sub(1, 70))))
                if ok then
                    _G.__dsh_booted = true
                    return true
                end
            end
        end
    end

    -- 兜底：万一是全局（不同渠道包可能有差异）
    local found = {}
    for _, n in ipairs(BOOT_NAMES) do
        if type(_G[n]) == "function" then found[#found + 1] = n end
    end
    if #found == 0 then
        _G.__dsh_boot_nil = (_G.__dsh_boot_nil or 0) + 1
        if _G.__dsh_boot_nil == 1 then
            rep("boot_wait", "no file_update table yet (fu=" .. type(fu) ..
                ", global ver_load_start=" .. type(_G.ver_load_start) .. ")")
        end
        return false
    end
    for _, n in ipairs(found) do
        local ok, err = pcall(_G[n])
        rep("boot", n .. "() ok=" .. tostring(ok) ..
            (ok and "" or (" err=" .. tostring(err):sub(1, 70))))
        if ok then
            _G.__dsh_booted = true
            return true
        end
    end
    return false
end

function M.try_login()
    if _G.__dsh_logged_in then return true end
    -- 不设上限：DengluPlatForm / DengluMgr 由登录界面初始化时才创建，
    -- 我们注入得早，必须一直等（之前 60/200 次上限会在模块出现前就放弃）。
    M._login_tries_all = (M._login_tries_all or 0) + 1

    -- 前置条件：sdkBackLogin 存在（require('sdk_function') 时注册），
    -- 且它内部要用的 DengluPlatForm 已就绪（denglu_platform.luac 更晚加载）。
    -- 之前失败**没有任何日志**，是因为 pcall 吞掉了 "attempt to index nil"。
    local f = _G.sdkBackLogin
    if type(f) ~= "function" then return false end

    local plat = _G.DengluPlatForm
    if type(plat) ~= "table" then
        if not _G.__dsh_plat_noted then
            _G.__dsh_plat_noted = true
            rep("login_wait", "sdkBackLogin=function but DengluPlatForm=" .. type(plat))
        end
        return false
    end

    M._login_tries = (M._login_tries or 0) + 1
    local payload = M.LOGIN_PAYLOAD:format(os.time())

    -- 两条路都试：
    --   A) 标准入口 sdkBackLogin(0, payload)  —— 内部会调 onLoginInfo
    --      + 处理公告版本/存档等副作用；
    --   B) 若 A 失败，直接 DengluPlatForm:getInstance():onLoginInfo(payload)。
    local ok, err = pcall(f, 0, payload)
    if not ok then
        local ok2, err2 = pcall(function()
            local inst = plat.getInstance and plat:getInstance() or plat
            inst:onLoginInfo(payload)
        end)
        if M._login_tries <= 5 or ok2 then
            rep("login", "try=" .. M._login_tries ..
                " sdkBack=fail(" .. tostring(err):sub(1, 40) .. ")" ..
                " direct=" .. tostring(ok2) ..
                (ok2 and "" or (" err=" .. tostring(err2):sub(1, 40))))
        end
        ok = ok2
    elseif M._login_tries <= 3 then
        rep("login", "try=" .. M._login_tries .. " via sdkBackLogin ok")
    end
    if ok then
        _G.__dsh_logged_in = true
        pcall(function()
            if type(_G.SaveLocalData) == "function" then
                _G.SaveLocalData("dsh_login_data", payload)
            end
        end)
    end
    return ok
end

-- ---------------------------------------------------------------------------
-- 合成服务器列表响应（绕开网络与"无定时器"这两个根本限制）
--
--   客户端请求服务器列表的路径（denglu_mgr proto#22 / proto#53）：
--       cc.XMLHttpRequest:new() → responseType=JSON → open("POST", get_servers_url)
--       → registerScriptHandler(proto#21) → send()
--   proto#21 只读三个字段：readyState==4、status∈[200,207)、response。
--   所以我们在 send() 里**不真的发请求**，直接喂一个"已成功"的响应对象，
--   然后把 handler 调起来 —— 客户端拿到服务器列表后就会去连 game host:port。
-- ---------------------------------------------------------------------------
function M.server_list_json()
    local sl = M.server_list()
    -- 兼容多种字段名：客户端 managerServerListByJsonObj 可能读其中任一个
    return jstr({
        code = 0, msg = "ok", status = 0, result = 1,
        servers = sl, serverlist = sl, server_list = sl, list = sl,
        rolelist = {}, roles = {},
    })
end

-- ---------------------------------------------------------------------------
-- 启动：交给 cc.Director 的 scheduler，每 50ms 转一次
-- ---------------------------------------------------------------------------
function M.install(interval)
    if _G.__dsh_srv_installed then return end
    _G.__dsh_srv_installed = true
    rep("install", "starting embedded server on port " .. tostring(M.PORT))

    -- =========================================================================
    --  调度通道的选择（踩过坑，很重要）
    --  ---------------------------------------------------------------------
    --  1) cc.Director 的 scheduler:scheduleScriptFunc(entry=1) 在 config.luac
    --     阶段注册**返回成功但回调从不执行**（实测无条件打点一次都不出现）。
    --     推测：此时 script-handler 注册表/调度器尚未进入运行态，或条目随后
    --     被 update_finish 清空。总之这条路不可靠。
    --  2) 游戏自己的逐帧模块加载器用的是
    --        node:scheduleUpdateWithPriorityLua(cb, 0)
    --     这是**同一个引擎里被验证可用**的通道，所以服务端也挂在这上面。
    -- =========================================================================
    local hook_errors = 0

    local function safe_tick()
        if not state.listening and state.tick_count < 600 then
            pcall(M.start)
        end
        if not state.game_listening and state.tick_count < 600 then
            pcall(M.start_game)
        end
        -- 统一走 M.pump（排空 + 登录 + 选服），避免多处实现不一致
        local ok2, err2 = pcall(M.pump)
        if not ok2 then
            hook_errors = hook_errors + 1
            if hook_errors <= 5 then rep("tick_err", tostring(err2)) end
        end
        -- 一次性诊断：把 _G 里所有表的名字列出来（找 DengluMgr 的真实落点）
        if not _G.__dsh_diag2 and (state.tick_calls or 0) >= 40 then
            _G.__dsh_diag2 = true
            pcall(function()
                local n, sample = 0, {}
                for k, v in pairs(_G) do
                    n = n + 1
                    if type(v) == "table" and type(k) == "string" and #sample < 18 then
                        sample[#sample + 1] = k
                    end
                end
                print("[DSH_DIAG] globals=" .. n .. " tables=" ..
                      table.concat(sample, ","))
            end)
        end
        -- 诊断计数：低频率打点，用来确认"排空是否真的在发生"
        local n = state.tick_calls or 0
        if n == 1 or n == 5 or n == 20 or n % 200 == 0 then
            rep("tickstat", "calls=" .. n ..
                " conns=" .. tostring(state.conn_count or 0) ..
                " http=" .. tostring(state.http_count or 0) ..
                " sel=" .. tostring(state.select_hits or 0) ..
                " clients=" .. #state.clients)
        end
        if M.ENABLE_HEARTBEAT and state.tick_count > 0 and state.tick_count % 80 == 0 then
            rep("heartbeat", "ticks=" .. state.tick_count ..
                " conns=" .. tostring(state.conn_count or 0) ..
                " http=" .. tostring(state.http_count or 0) ..
                " clients=" .. #state.clients ..
                " game_conns=" .. tostring(state.game_conn_count) ..
                " game_clients=" .. #state.game_clients ..
                " game_bytes=" .. tostring(state.game_bytes) ..
                " errs=" .. hook_errors)
        end
    end

    local ok, err = pcall(function()
        -- 常驻节点（先创建，稍后挂到场景里再启动心跳）。
        -- 踩坑：cc.Director 的 scheduleScriptFunc 与自建节点的
        -- scheduleUpdateWithPriorityLua / runAction 都不触发；游戏自己的
        -- ver_load_start 用的是 `scene:runAction(Sequence(DelayTime, CallFunc))`，
        -- 说明 ActionManager 本身是活的 —— 关键差别是**节点必须挂在正在运行的场景上**。
        -- 所以这里轮询等 RunningScene 出现，再 addChild + 启动自链式心跳。
        local node = cc.Node:create()
        node:retain()
        _G.__dsh_srv_node = node

        local started = false

        -- 节拍器：Lua 自链式（每次只挂**一个**下一次动作）。
        -- 实测对比：
        --   * cc.RepeatForever 包 Sequence 只挂一次 → CallFunc **不触发**；
        --   * Lua 每次 runAction 一个 Sequence(DelayTime, CallFunc) 自链 → 稳定触发
        --     （早期日志里 heartbeat ticks=80 就是这条路径跑出来的）。
        -- ⚠ 千万不要在 beat 里再套 RepeatForever：动作数会指数增长把游戏拖死。
        local function beat()
            pcall(safe_tick)
            local n = _G.__dsh_srv_node
            if not n then return end
            pcall(function()
                n:runAction(cc.Sequence:create(
                    cc.DelayTime:create(0.05),
                    cc.CallFunc:create(function() pcall(beat) end)))
            end)
        end

        local function try_attach()
            if started then return end
            local scene = cc.Director:getInstance():getRunningScene()
            if not scene then return false end
            pcall(function() scene:addChild(node) end)
            started = true
            pcall(beat)          -- 启动自链式节拍
            rep("hook", "attached to scene; self-chaining ticker started")
            return true
        end

        if not try_attach() then
            -- 场景还没就绪：用 performWithDelay 自链式轮询（同一节点，挂上去后就走 beat）
            local polls = 0
            local function poll()
                polls = polls + 1
                if try_attach() then return end
                if polls > 600 then
                    rep("hook", "gave up attaching to scene after " .. polls .. " polls")
                    return
                end
                pcall(function()
                    node:runAction(cc.Sequence:create(
                        cc.DelayTime:create(0.1),
                        cc.CallFunc:create(function() pcall(poll) end)))
                end)
            end
            pcall(poll)
        end

        _G.__dsh_srv_tick = safe_tick
        -- 同时暴露一个全局别名：config.luac 的注入块会在每次诊断上报前调用它，
        -- 借客户端的请求时机当节拍器（引擎不给定时回调时这是唯一稳定的驱动）。
        _G.__dsh_srv_pump = safe_tick
        rep("hook", "resident node created; heartbeat via scene-attached action")
    end)
    if not ok then rep("install_fail", tostring(err)) end
end

-- 立即尝试启动一次（此时 socket 可能还没注册，失败也没关系，scheduler 里会重试）
-- 启动：只保留服务端必需的那一个调度条目。
--
-- ⚠ 性能红线（踩过）：update_finish 之后客户端要逐帧加载 ~688 个模块
--    （4 个/帧），每一帧的预算非常紧。之前为了排查挂了好几个探针
--    （驱动探测 / kick 定时器 / 网络探针 / 心跳），把每帧预算吃光，
--    表现是游戏卡在 "config_*.luac" 一连串加载里永远到不了登录页。
--    因此**默认只保留服务端 tick 一个条目**，所有探针都必须显式开启。
M.ENABLE_KICK = false          -- 主动调 update_finish（正常流程由 UPDATE_SKIP 驱动）
M.ENABLE_DRIVER_PROBE = false  -- 驱动通道探测（A/B/C/D）
M.ENABLE_NET_PROBE = false     -- 登录服地址探针
M.ENABLE_HEARTBEAT = true      -- 每 80 tick 打一次心跳（排查期开启；稳定后可关）
M.ENABLE_TICKLOG = true        -- 每 tick 无条件打点（判定调度循环是否活着）

pcall(function() M.start() end)
M.install(0.05)
pcall(M.install_require_watch)
pcall(M.start_watchdog)
if M.ENABLE_KICK then pcall(M.install_kick) end
if M.ENABLE_DRIVER_PROBE then pcall(M.probe_drivers) end
if M.ENABLE_NET_PROBE then pcall(M.install_probe) end

-- ============================================================================
--  由 assets/src/main.lua 抢先加载（单机版关键路径）
--  ---------------------------------------------------------------------------
--  客户端启动时会去找 `src/main.lua`（官方包里没有这个文件，日志里一直是
--  "No file found at src/main.lua"）。我们在 APK 里放一个自己的 main.lua，
--  它把本文件 loadstring 起来 —— 于是内置服务端在**任何游戏 Lua 之前**绑定
--  端口，彻底消除"客户端首批 HTTP 比服务端早几毫秒"的竞态。
-- ============================================================================
_G.__DSH_SERVER = M

-- 自注册：config.luac 的注入块会把本文件源码再 loadstring 一次（它需要比
-- 诊断上报更早绑定端口）。标记一下，避免重复启动。
pcall(function()
    if package and package.loaded then
        package.loaded.__dsh_local_server = M
    end
end)


return M
