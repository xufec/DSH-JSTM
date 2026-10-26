-- ---- DSH url observer ----
--  鐩�鐨勶細鎼炴竻瀹㈡埛绔�鍦�"鏈嶅姟鍣ㄥ氨缁�涔嬪墠"鍒板簳璇锋眰浜嗕粈涔堛�佷互鍙婁笅涓�姝ュ畠闇�瑕佷粈涔堛��
--
--  鈿犫殸 韪╄繃鐨勫潙锛堢牬浜嗕細鐩存帴娈甸敊璇� / OOM锛屽姟蹇呴伒瀹堬級锛�
--    1. 缁濅笉鍖呰�� string.format 鈥斺�� print 鍐呴儴灏辩敤瀹冿紝
--       print 鈫� format 鈫� 瑙傛祴鍣� 鈫� print 鏃犻檺閫掑綊锛屽疄娴嬪埛鍒� OOM銆�
--    2. **缁濅笉鏇挎崲 cc.XMLHttpRequest.new**銆傚疄娴嬭繖涔堟敼浼氳�╁師鐢熷眰鍦�
--       GLThread 涓� SIGSEGV锛坒ault addr 0xdead1005锛夛紝鍥犱负寮曟搸鑷�宸辨寔鏈�
--       閭ｄ釜 Lua 鍑芥暟鐨勫紩鐢�锛涙浛鎹㈠悗 Lua 闂�鍖呰�� GC/鎹㈢粦锛屽師鐢熻皟鐢ㄥ嵆宕╂簝銆�
--       鍥犳�よ繖閲屽彧**璇诲彇** self.new 鍋氫竴娆″瓨鍦ㄦ�ц�板綍锛岀粷涓嶈祴鍊笺��
--    3. 鍙�鍦ㄦ敞鍏ユ椂鎵ц�屼竴娆℃�ф帰娴嬶紝涓嶈�佹寕鍦ㄧ儹璺�寰勪笂銆�
-- ============================================================================

pcall(function()
    if _G.__dsh_obs then return end
    _G.__dsh_obs = true

    local function obs(tag, s)
        pcall(function() print("[DSH_OBS] " .. tag .. " " .. tostring(s)) end)
    end

    local X = cc and cc.XMLHttpRequest
    if not X then
        obs("probe", "cc.XMLHttpRequest missing")
        return
    end

    -- 鍙�璇绘帰娴嬶細杩欎簺鍚嶅瓧瀛樺湪涓庡惁锛岀敤鏉ュ垽鏂�鑳藉惁鍦ㄥ師浣嶅仛閽╁瓙
    obs("probe", "new=" .. type(X.new) ..
        " open=" .. type(X.open) ..
        " send=" .. type(X.send) ..
        " proto=" .. type(X.prototype))
end)


-- ================= DSH embedded local server (fallback) =================
-- DSH_FALLBACK_BEGIN   鈫� ASCII 鏍囪�帮細verify_injected_lua.py 闈犲畠瀹氫綅鏈�娈�
-- 鍗曟満鐗堟牳蹇冿細鎶婃湇鍔＄��鐩存帴璺戝湪娓告垙杩涚▼閲岋紝瀹㈡埛绔�杩� 127.0.0.1:18080
-- 棣栭�夎矾寰勬槸 APK 閲岀殑 assets/src/main.lua锛堟洿鏃╁惎鍔�锛岄伩鍏嶇珵鎬侊級锛�
-- 杩欓噷淇濈暀涓�浠藉厹搴曪紝闃叉�� main.lua 鏈�琚�寮曟搸鍔犺浇銆�
-- 婧愮爜锛歴erver/local_server.lua锛堟敼杩欓噷娌＄敤锛屾敼閭ｄ釜鏂囦欢鍐嶉噸鏂版墦鍖咃級
do
  local __dsh_srv_src = [====[
-- ============================================================================
--  銆婄粷涓栧攼闂ㄣ�嬪崟鏈虹増 鈥斺�� 鍐呯疆鏈�鏈烘湇鍔＄�� (embedded local server)
-- ============================================================================
--  杩愯�屼綅缃�锛氭父鎴忚繘绋嬭嚜宸辩殑 Lua VM锛堢敱 tools/patch_apk.py 娉ㄥ叆鍒版槑鏂囩殑
--            assets/src/config.luac 鏈�灏撅紝娓告垙鍚�鍔ㄦ椂鑷�鍔ㄦ墽琛岋級銆�
--  浼犺緭灞�  锛歭ibcocos2dlua.so 閲岄潤鎬侀摼鎺ョ殑 LuaSocket锛坰ocket.core锛夈��
--  鐩戝惉    锛�0.0.0.0:PORT锛屽�㈡埛绔�琚�鏀瑰寘涓鸿繛 127.0.0.1:PORT锛屽洜姝ゅ叏閮ㄩ棴鐜�鍦�
--            鏈�鏈鸿繘绋嬪唴锛屼笉闇�瑕� PC銆佷笉闇�瑕佺綉缁溿��
--
--  鈿� 杩欎釜鏂囦欢鍦ㄦ湰杩涚▼閲屾渶鍏堣窇銆佹渶涓嶈兘鍑洪敊锛�
--    * 鍏ㄧ▼ pcall 鍖呰９锛屼换浣曞紓甯搁兘蹇呴』鍙樻垚 logcat 鍙�瑙佺殑涓�琛屾棩蹇楋紱
--    * 鏈嶅姟鍣ㄥ繀椤诲湪 config.luac 涔嬪悗鐨勭��涓�涓�璋冨害甯у氨璧锋潵锛堝�㈡埛绔�鍦�
--      config.luac 涔嬪墠灏卞凡缁忓彂杩囦竴杞� HTTP锛屾櫄浜嗗氨鐩存帴 connection refused锛夈��
--
--  璁捐�¤�佺偣
--   * 涓荤嚎绋嬮潪闃诲�烇細鐢� select(timeout=0) 杞�杞�锛岀粷涓嶉樆濉炴覆鏌�/閫昏緫绾跨▼銆�
--   * 鐢� cc.Director 鐨� scheduler 姣� 50ms 椹卞姩涓�娆� tick锛堜笉渚濊禆绾跨▼锛夈��
--   * 鎵�鏈夊け璐ラ兘閫氳繃 __dsh_rep 涓婃姤锛圚TTP 鑷�璇锋眰 + print/logcat 鍙岄�氶亾锛夈��
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 鏈�鍏堟墽琛岋細璇婃柇閫氶亾 + 灏芥棭缁戝畾绔�鍙�
--   print 璧� [LUA-print] tag锛宎db logcat 鐩存帴鍙�瑙侊紝涓嶄緷璧栫綉缁溿��
--   娉ㄦ剰锛氭湰鏂囦欢鏄�鍚�鍔ㄦ棭鏈熸敞鍏ョ殑锛屾墍浠ュ厛瑁呬竴涓�涓嶄緷璧栦换浣曞�栭儴鍙橀噺鐨� rep銆�
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

-- 灏芥棭璧锋湇鍔★細鍏堣瘯涓�娆★紙socket 鍙�鑳借繕娌℃敞鍐岋級锛屽け璐ヤ氦缁� scheduler 閲嶈瘯銆�
pcall(function() rawrep("preload", "config.luac reached") end)

-- ============================================================================
--  绔�鍙ｈ嚜妫�锛氱粦瀹氬け璐ユ渶甯歌�佺殑鍘熷洜鏄�绔�鍙ｈ��鍗狅紝蹇呴』鑳戒竴鐪肩湅鍑烘潵
-- ============================================================================

-- 杩欎簺鍏ㄥ眬鐢� patch_apk.py 娉ㄥ叆鏃舵浛鎹�锛堜笉瑕佹墜鏀硅繖閲岀殑榛樿�ゅ�间互澶栫殑涓滆タ锛�
M.PORT = 18080
M.HOST_IP = "127.0.0.1"        -- 涓嬪彂缁欏�㈡埛绔�鐨勬父鎴忔湇鍦板潃
M.GAME_PORT = 19000            -- 娓告垙鏈嶏紙TCP 鍗忚��锛夌��鍙�
M.REPORT_URL = ""              -- 鐣欑┖ = 涓嶅悜澶栭儴涓婃姤锛堝崟鏈烘椂鏃犵綉鍙�鐢�锛�

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
-- 杞借嵎锛堝厛鐓ф妱 PC 鐗� mock_server.py 鐨勫舰鐘讹紝楠岃瘉閫氫簡鍐嶆寜瀹㈡埛绔�鐪熷疄闇�姹傛敹绐勶級
-- ---------------------------------------------------------------------------
function M.server_list()
    return { {
        id = "1", name = "鍗曟満鏈�鍦版湇", ip = M.HOST_IP, port = M.GAME_PORT,
        state = 1, is_new = 1, world_lev = 1,
    } }
end

function M.gateway_payload()
    local sl = M.server_list()
    -- 瀹㈡埛绔�鍘嗗彶涓婄敤杩囧�氱�嶅瓧娈靛悕锛屽叏閮ㄧ粰鍑猴紝閬垮厤鍐嶇寽 schema
    return {
        code = 0, msg = "ok", status = 0, result = 1,
        servers = sl, serverlist = sl, server_list = sl, list = sl,
        rolelist = {}, roles = {},
    }
end

local CONF = { code = 0, msg = "ok", status = 0, result = 1,
               maintain = 0, is_maintain = 0, white = 1 }

-- ---------------------------------------------------------------------------
-- HTTP 璺�鐢憋細瀹屽叏瀵圭収 PC 鐗� mock_server.py 宸茶窇閫氱殑琛屼负
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
        return 200, jstr({ notice = "鍗曟満鏈�鍦版湇娴嬭瘯" }), "application/json; charset=utf-8"
    end
    if p:find("gateway/mobile", 1, true) or p:find("app/mobile", 1, true) then
        return 200, jstr(M.gateway_payload()), "application/json; charset=utf-8"
    end
    -- 鍏滃簳锛氬�藉�圭殑"鏃犻渶鏇存柊"搴旂瓟
    return 200, jstr({ code = 0, msg = "ok", status = 0, result = 1,
                       update = 0, version = 0 }), "application/json; charset=utf-8"
end

-- url_config_ewan.lua锛氬�㈡埛绔�涓嬭浇鍚庡綋 Lua 杞藉叆锛岀敤瀹冩妸 CDN/缃戝叧鍏ㄩ儴鎸囧洖鏈�鏈�
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
-- 璇锋眰瑙ｆ瀽
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
    if #rest < n then return nil end                              -- body 鏈�鏀跺叏
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
-- 闈為樆濉炴湇鍔″櫒
-- ---------------------------------------------------------------------------
local state = {
    listening = false, server = nil, clients = {}, tick_count = 0,
    http_count = 0, conn_count = 0, err = nil, started = false,
    -- 娓告垙鏈嶏紙TCP 鍗忚��锛変晶
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

-- 鍏滀綇 socket 鍏ㄥ眬锛歀uaSocket 鐢卞師鐢熷眰娉ㄥ唽锛屽彲鑳芥櫄浜庢湰鏂囦欢鍔犺浇
local function ensure_socket()
    if socket then return true end
    local ok = pcall(function() socket = require("socket") end)
    return ok and socket ~= nil
end

-- ---------------------------------------------------------------------------
-- 娓告垙鏈嶏紙TCP锛夛細瀹㈡埛绔�鐧诲綍/杩涘満鏅�閮借蛋杩欓噷锛屽厛鍘熸牱鎶撳寘
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

    local rd = { state.server }
    for _, c in ipairs(state.clients) do rd[#rd + 1] = c.sock end
    if state.game_server then rd[#rd + 1] = state.game_server end

    local ready = socket.select(rd, nil, 0)
    for _, s in ipairs(ready or {}) do
        if s == state.server then
            local cs = state.server:accept()
            if cs then
                cs:settimeout(0)
                cs:setoption("tcp-nodelay", true)
                state.clients[#state.clients + 1] = { sock = cs, buf = "", t0 = os.time() }
                state.conn_count = (state.conn_count or 0) + 1
                -- 鍙�姹囨姤鍓� 12 涓�杩炴帴锛岄伩鍏嶅埛灞�/鍗犲抚
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
            -- HTTP 杩炴帴
            for i = #state.clients, 1, -1 do
                local c = state.clients[i]
                if c.sock == s then
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
                            -- 鍓� 40 涓�璇锋眰閫愭潯鎵撳嵃锛屼箣鍚庡彧璁℃暟
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
            -- 娓告垙鏈嶈繛鎺ワ細鍘熸牱鎶撳寘锛堣繖鏄�纭�瀹� wire 鏍煎紡鐨勫敮涓�鍙�闈犳潵婧愶級
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

    -- 娓呯悊瓒呮椂杩炴帴锛堥伩鍏� fd 娉勬紡锛�
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
    return true
end

-- ---------------------------------------------------------------------------
-- 鐗堟湰妫�鏌ユ斁琛岋紙kick锛�
--   鑳屾櫙锛氬�㈡埛绔�鍦ㄦ湰杩涚▼鍔犺浇 config.luac **涔嬪墠**灏卞彂浜嗕竴鎵� HTTP锛堝疄娴� 9 娆★級锛�
--   閭ｄ竴鍒绘湇鍔＄��杩樻病缁戝畾绔�鍙� 鈫� 鍏ㄩ儴 connect failed锛涘�㈡埛绔�鑷�宸变笉閲嶈瘯锛�
--   浜庢槸鍗″湪鐗堟湰椤点�傝繖閲屽湪 config 鎵ц�屽畬銆佹湇鍔＄��灏辩华涔嬪悗锛屼富鍔ㄩ┍鍔ㄥ�㈡埛绔�
--   鑷�宸辩殑"鏃犻渶鏇存柊"鍏ュ彛锛坲pdate_finish锛夈��
--
--   鍊欓�夊悕鎸夊彲鑳芥�ф帓搴忥細update_finish / updateFinish / OnUpdateFinish /
--   update_complete / enterLogin / getNowVersion銆�
-- ---------------------------------------------------------------------------
M.KICK = true
M.KICK_DELAY = 1.0        -- 绉掞紱澶�鏃╃殑璇濊繖浜涙ā鍧楄繕娌″姞杞�

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
                -- 姣忔�″�氱瓑涓�浼氬効锛岀粰妯″潡鍔犺浇鐣欐椂闂达紱鎴愬姛涓�娆″氨鍋�
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
-- 椹卞姩鎺㈡祴锛氭壘鍑烘父鎴忛噷鐪熸�ｄ細璺戠殑"姣忓抚/瀹氭椂"閫氶亾
--   瀹炴祴 scheduleScriptFunc 娉ㄥ唽鎴愬姛浣嗗洖璋冧粠涓嶆墽琛岋紙鏃犲績璺筹級锛岃�存槑鍚�鍔�
--   闃舵�� Director 鐨勮皟搴﹀櫒娌℃湁鍦ㄩ┍鍔� script entries銆傝繖閲屽悓鏃惰瘯鍑犵�嶉�氶亾锛�
--   鍚勮嚜鎵撶偣锛屾壘鍑哄彲鐢ㄧ殑閭ｄ竴涓�锛堟湇鍔＄��杞�璇㈠繀椤绘寕鍦ㄨ兘璺戠殑閫氶亾涓婏級銆�
-- ---------------------------------------------------------------------------
function M.probe_drivers()
    if _G.__dsh_probe then return end
    _G.__dsh_probe = true

    -- A) 鍏ㄥ眬 scheduler锛堝凡鐭ユ敞鍐屾垚鍔燂級
    pcall(function()
        local d = cc.Director:getInstance()
        local sch = d:getScheduler()
        sch:scheduleScriptFunc(function()
            rep("drv_A", "scheduler fired")
        end, 0.5, false)
    end)

    -- B) 鎸傚湪涓存椂 Node 涓婄殑 update
    pcall(function()
        local node = cc.Node:create()
        cc.Director:getInstance():getRunningScene():addChild(node)
        node:scheduleUpdateWithPriorityLua(function(dt)
            rep("drv_B", "node update fired dt=" .. tostring(dt))
        end, 0)
    end)

    -- C) Node 鐨� enterFrame 浜嬩欢
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

    -- D) performWithDelay 寰�鐜�锛坈ocos 鐨� action 绯荤粺锛屽拰 scheduler entries 涓嶅悓锛�
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
-- 鐧诲綍鏈嶈繛鎺ユ帰閽堬細鎶撳嚭瀹㈡埛绔�鍒板簳瑕佽繛鍝�涓�鍦板潃
--   鐜拌薄锛氬�㈡埛绔�杩涘叆 game_start 鍚庡弽澶� openReconnect锛屼絾鏈嶅姟绔� 19000 绔�鍙�
--   鏀朵笉鍒颁换浣曡繛鎺� 鈥斺�� 蹇呴』鐭ラ亾瀹冨疄闄呰繛鐨� host:port 鎵嶈兘瀵圭棁銆�
--   gamenet.luac 閲屾湁 login_server_host_name / login_server_host_port 涓や釜閿�銆�
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
            -- 鍦ㄨ嫢骞叉椂闂寸偣涓婇噰鏍凤紝鐪嬪�㈡埛绔�浣曟椂鎷垮埌/浣跨敤鐧诲綍鏈嶅湴鍧�
            if ticks == 10 or ticks == 30 or ticks == 80 or ticks == 200 then
                -- 娉ㄦ剰锛歳ep() 浼氭妸鍐呭�规埅鍒� 170 瀛楄妭锛屾墍浠ヨ繖閲屽繀椤绘媶鎴愬�氭潯灏忔棩蹇楋紝
                -- 鍚﹀垯鏁存潯鎺㈤拡缁撴灉浼氳��鍚炴帀锛堣俯杩囷級銆�
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
-- 鍚�鍔�锛氫氦缁� cc.Director 鐨� scheduler锛屾瘡 50ms 杞�涓�娆�
-- ---------------------------------------------------------------------------
function M.install(interval)
    if _G.__dsh_srv_installed then return end
    _G.__dsh_srv_installed = true
    rep("install", "starting embedded server on port " .. tostring(M.PORT))
    local ok, err = pcall(function()
        local d = cc and cc.Director and cc.Director:getInstance()
        local sch = d and d:getScheduler()
        if not sch then error("no scheduler") end
        local started = M.start()
        rep("start", "listening=" .. tostring(state.listening) ..
            " game=" .. tostring(state.game_listening) ..
            " err=" .. tostring(state.err) .. " gerr=" .. tostring(state.game_err))
        local tick_errs = 0
        local entry = sch:scheduleScriptFunc(function()
            -- 鍓嶄笁绉掓瘡甯ч噸璇曠粦瀹氾紙socket 妯″潡鍙�鑳藉湪 config.luac 涔嬪悗鎵嶆敞鍐岋級
            if not state.listening and state.tick_count < 60 then
                M.start()
            end
            if not state.game_listening and state.tick_count < 60 then
                pcall(M.start_game)
            end
            local ok2, err2 = pcall(M.tick)
            if not ok2 then
                tick_errs = tick_errs + 1
                if tick_errs <= 5 then rep("tick_err", tostring(err2)) end
            end
            -- 姣� 80 甯э紙绾� 4 绉掞級姹囨姤涓�娆＄姸鎬侊紙榛樿�ゅ叧闂�锛氫細鍗犵敤姣忓抚棰勭畻锛�
            if M.ENABLE_HEARTBEAT and state.tick_count > 0 and state.tick_count % 80 == 0 then
                rep("heartbeat", "ticks=" .. state.tick_count ..
                    " conns=" .. tostring(state.conn_count or 0) ..
                    " http=" .. tostring(state.http_count or 0) ..
                    " clients=" .. #state.clients ..
                    " game_conns=" .. tostring(state.game_conn_count) ..
                    " game_clients=" .. #state.game_clients ..
                    " game_bytes=" .. tostring(state.game_bytes) ..
                    " errs=" .. tick_errs)
            end
        end, interval or 0.05, false)
        rep("scheduler", "entry=" .. tostring(entry))
    end)
    if not ok then rep("install_fail", tostring(err)) end
end

-- 绔嬪嵆灏濊瘯鍚�鍔ㄤ竴娆★紙姝ゆ椂 socket 鍙�鑳借繕娌℃敞鍐岋紝澶辫触涔熸病鍏崇郴锛宻cheduler 閲屼細閲嶈瘯锛�
-- 鍚�鍔�锛氬彧淇濈暀鏈嶅姟绔�蹇呴渶鐨勯偅涓�涓�璋冨害鏉＄洰銆�
--
-- 鈿� 鎬ц兘绾㈢嚎锛堣俯杩囷級锛歶pdate_finish 涔嬪悗瀹㈡埛绔�瑕侀�愬抚鍔犺浇 ~688 涓�妯″潡
--    锛�4 涓�/甯э級锛屾瘡涓�甯х殑棰勭畻闈炲父绱с�備箣鍓嶄负浜嗘帓鏌ユ寕浜嗗ソ鍑犱釜鎺㈤拡
--    锛堥┍鍔ㄦ帰娴� / kick 瀹氭椂鍣� / 缃戠粶鎺㈤拡 / 蹇冭烦锛夛紝鎶婃瘡甯ч�勭畻鍚冨厜锛�
--    琛ㄧ幇鏄�娓告垙鍗″湪 "config_*.luac" 涓�杩炰覆鍔犺浇閲屾案杩滃埌涓嶄簡鐧诲綍椤点��
--    鍥犳��**榛樿�ゅ彧淇濈暀鏈嶅姟绔� tick 涓�涓�鏉＄洰**锛屾墍鏈夋帰閽堥兘蹇呴』鏄惧紡寮�鍚�銆�
M.ENABLE_KICK = false          -- 涓诲姩璋� update_finish锛堟�ｅ父娴佺▼鐢� UPDATE_SKIP 椹卞姩锛�
M.ENABLE_DRIVER_PROBE = false  -- 椹卞姩閫氶亾鎺㈡祴锛圓/B/C/D锛�
M.ENABLE_NET_PROBE = false     -- 鐧诲綍鏈嶅湴鍧�鎺㈤拡
M.ENABLE_HEARTBEAT = false     -- 姣� 80 tick 鎵撲竴娆″績璺�

pcall(function() M.start() end)
M.install(0.05)
if M.ENABLE_KICK then pcall(M.install_kick) end
if M.ENABLE_DRIVER_PROBE then pcall(M.probe_drivers) end
if M.ENABLE_NET_PROBE then pcall(M.install_probe) end

-- ============================================================================
--  鐢� assets/src/main.lua 鎶㈠厛鍔犺浇锛堝崟鏈虹増鍏抽敭璺�寰勶級
--  ---------------------------------------------------------------------------
--  瀹㈡埛绔�鍚�鍔ㄦ椂浼氬幓鎵� `src/main.lua`锛堝畼鏂瑰寘閲屾病鏈夎繖涓�鏂囦欢锛屾棩蹇楅噷涓�鐩存槸
--  "No file found at src/main.lua"锛夈�傛垜浠�鍦� APK 閲屾斁涓�涓�鑷�宸辩殑 main.lua锛�
--  瀹冩妸鏈�鏂囦欢 loadstring 璧锋潵 鈥斺�� 浜庢槸鍐呯疆鏈嶅姟绔�鍦�**浠讳綍娓告垙 Lua 涔嬪墠**缁戝畾
--  绔�鍙ｏ紝褰诲簳娑堥櫎"瀹㈡埛绔�棣栨壒 HTTP 姣旀湇鍔＄��鏃╁嚑姣�绉�"鐨勭珵鎬併��
-- ============================================================================
_G.__DSH_SERVER = M

-- 鑷�娉ㄥ唽锛歝onfig.luac 鐨勬敞鍏ュ潡浼氭妸鏈�鏂囦欢婧愮爜鍐� loadstring 涓�娆★紙瀹冮渶瑕佹瘮
-- 璇婃柇涓婃姤鏇存棭缁戝畾绔�鍙ｏ級銆傛爣璁颁竴涓嬶紝閬垮厤閲嶅�嶅惎鍔ㄣ��
pcall(function()
    if package and package.loaded then
        package.loaded.__dsh_local_server = M
    end
end)


return M

]====]
  local __dsh_chunk, __dsh_cerr = loadstring(__dsh_srv_src, "dsh_local_server")
  if not __dsh_chunk then
    pcall(function() print("[DSH_SRV] compile_fail " .. tostring(__dsh_cerr)) end)
    if type(__dsh_rep) == "function" then __dsh_rep("srv_compile_fail", tostring(__dsh_cerr)) end
  else
    local __dsh_ok, __dsh_rerr = pcall(__dsh_chunk)
    if not __dsh_ok then
      pcall(function() print("[DSH_SRV] run_fail " .. tostring(__dsh_rerr)) end)
      if type(__dsh_rep) == "function" then __dsh_rep("srv_run_fail", tostring(__dsh_rerr)) end
    end
  end
end
-- ==============================================================
