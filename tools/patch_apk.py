#!/usr/bin/env python3
"""Patch the game APK so the client talks to our own server instead of the
dead official gateway.

Two kinds of edit:
  * assets/src/config.luac       -- plain-text Lua: URL_LUA_CONFIG and login flags
                                    can be rewritten with any length.
  * lib/armeabi/libentryexstd.so -- the 8 hard-coded gateway URLs live in a
                                    fixed-size string table, so replacements MUST
                                    have the exact same byte length (we pad the
                                    URL path with '/' -- the mock server accepts
                                    any padding).

Usage:
  python tools/patch_apk.py anzbao/jstm_142165.apk patched/jstm_patched.apk \
         --host 10.16.153.137 --port 8080 [--keep-platform-login]
"""
import argparse, os, re, subprocess, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_DIR = os.path.join(os.path.dirname(HERE), 'server')
LOCAL_SERVER_LUA = os.path.join(SERVER_DIR, 'local_server.lua')
MAIN_LUA = os.path.join(SERVER_DIR, 'main_lua.lua')
OBSERVER_LUA = os.path.join(SERVER_DIR, 'observer.lua')


def lua_syntax_ok(src, report, label):
    """用真正的 Lua 5.1 解析器（tools/lua-check）校验待注入源码。

    早先这里用"括号/引号计数"做自检，结果被 Lua 字符串与注释里的括号误判，
    把整个内置服务端静默地拒掉了（APK 里没有服务端，排查了很久）。
    计数法天然不可靠，必须用真解析器。
    """
    check_js = os.path.join(HERE, 'lua-check', 'check.js')
    if not os.path.isfile(check_js):
        report.append('  !! lua checker missing (%s), skip syntax gate' % check_js)
        return True
    tmp = os.path.join(HERE, 'lua-check', '_gate_%s.lua' % re.sub(r'\W+', '_', label))
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(src)
    try:
        r = subprocess.run(['node', check_js, '--quiet', tmp],
                           capture_output=True, encoding='utf-8', errors='replace')
    except FileNotFoundError:
        report.append('  !! node not found, skip syntax gate')
        return True
    if r.returncode != 0:
        report.append('  !! %s failed Lua syntax check -- NOT injected: %s'
                      % (label, (r.stderr or '').strip()[:400]))
        return False
    return True


def read_lua(path, report, label):
    """读取注入用的 Lua 源码，并做真正的语法自检。"""
    if not os.path.isfile(path):
        report.append('  !! %s source missing: %s' % (label, path))
        return None
    with open(path, encoding='utf-8') as f:
        src = f.read()
    if not lua_syntax_ok(src, report, label):
        return None
    return src

GATEWAY_RE = re.compile(
    rb'http://\d{1,3}(?:\.\d{1,3}){3}:\d+/(?:app|gateway)/mobile/(?:json|conf|hft)')
ANY_URL_RE = re.compile(rb'https?://[0-9a-zA-Z\.\-]+(?::\d+)?/[0-9a-zA-Z\.\-_/%]*')
LUA_URL_RE = re.compile(rb'(URL_LUA_CONFIG\s*=\s*")([^"]*)(")')


def fit(orig: bytes, base: str, path: str) -> bytes:
    """Build a replacement of exactly len(orig) bytes (pad path with '/')."""
    cand = base + path
    if len(cand) > len(orig):
        # shorten the path from the left, keeping the final segment
        tail = path.rstrip('/').split('/')[-1]
        cand = base + '/' + tail
    if len(cand) > len(orig):
        tail = path.rstrip('/').split('/')[-1]
        cand = base + '/' + tail[:max(1, len(orig) - len(base) - 1)]
    if len(cand) > len(orig):
        raise ValueError('cannot fit %r into %d bytes (base is %d)'
                         % (orig[:60], len(orig), len(base)))
    return (cand + '/' * (len(orig) - len(cand))).encode('ascii')


def pick(orig: bytes, path: str, bases, idx):
    """Try bases round-robin so the client can reach us via any candidate address."""
    for k in range(len(bases)):
        b = bases[(idx + k) % len(bases)]
        try:
            return fit(orig, b, path), b
        except ValueError:
            continue
    raise ValueError('no base fits %r' % orig[:60])


def patch_so(data: bytes, bases, idx, report):
    out = bytearray(data)
    n = 0
    for m in GATEWAY_RE.finditer(bytes(data)):
        orig = m.group()
        path = '/' + orig.split(b'/', 3)[3].decode('ascii') if orig.count(b'/') >= 3 else '/app/mobile/json'
        try:
            new, base = pick(orig, path, bases, idx[0])
        except ValueError as e:
            report.append('  !! gateway url too long: %s (%s)' % (orig.decode(), e))
            continue
        out[m.start():m.end()] = new
        report.append('  gateway %-52s -> %s' % (orig.decode(), new.decode()))
        idx[0] += 1
        n += 1
    return bytes(out), n


def lua_quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


# 开场 CG 视频：单机版必须移除它。
#   证据（file_update.luac）：
#     * proto#36 update_finish 先 require('config/config')/module_include 建 GameModule 列表，
#       再 `video_finish = video_player(self, <proto#32>)`，最后把逐帧加载器挂在 video_finish 上；
#     * proto#39 video_player 用 isFileExist 找 assets/res/resource/login/gamecg.mp4，
#       找到就 play() 并 addTouchEventListener（这正是"点击会暂停动画"的来源）；
#     * 而 **initInstance（→ game_start → 登录界面）只在视频结束回调 proto#32 里被调用**。
#   在模拟器上没有可用的视频解码 → 视频永不结束 → 永远进不了登录界面
#   （表现为"卡在初始加载界面、点击只暂停动画"）。
#   删掉该文件后 isFileExist 为假，video_player 走 fallback 立即完成。
CG_VIDEO = 'assets/res/resource/login/gamecg.mp4'


def load_embedded_server(report, base, host, port, game_port, report_url):
    """Read server/local_server.lua and specialise it for this build.

    返回 dict:
      server   —— 放进 APK 的 assets/src/dsh_server.lua（内置服务端本体）
      main     —— 放进 APK 的 assets/src/main.lua（抢先启动引导）
      wrapper  —— 仍然追加到 config.luac，作为兜底（main.lua 没生效时也能起）

    为什么要放进 APK 而不是只注入 config.luac：
      客户端首批 HTTP 请求发生在 config.luac 之后仅几毫秒，服务端来不及绑定
      端口；而客户端启动时会去找 `src/main.lua`（官方包没有该文件），把它换成
      我们的引导即可在**任何游戏 Lua 之前**启动服务端，彻底消除竞态。
    返回 None 表示不注入。
    """
    if not os.path.isfile(LOCAL_SERVER_LUA):
        report.append('  !! embedded server source missing: %s' % LOCAL_SERVER_LUA)
        return None
    src = read_lua(LOCAL_SERVER_LUA, report, 'embedded server')
    if src is None:
        return None
    main_src = read_lua(MAIN_LUA, report, 'main.lua bootstrap')
    if main_src is None:
        return None

    src = src.replace('M.PORT = 18080', 'M.PORT = %d' % port)
    src = src.replace('M.GAME_PORT = 19000', 'M.GAME_PORT = %d' % game_port)
    src = src.replace('M.HOST_IP = "127.0.0.1"', 'M.HOST_IP = %s' % lua_quote(host))
    src = src.replace('M.REPORT_URL = ""', 'M.REPORT_URL = %s' % lua_quote(report_url or ''))

    wrapper = (
        '\n\n-- ================= DSH embedded local server (fallback) =================\n'
        '-- DSH_FALLBACK_BEGIN   ← ASCII 标记：verify_injected_lua.py 靠它定位本段\n'
        '-- 单机版核心：把服务端直接跑在游戏进程里，客户端连 127.0.0.1:%d\n'
        '-- 首选路径是 APK 里的 assets/src/main.lua（更早启动，避免竞态）；\n'
        '-- 这里保留一份兜底，防止 main.lua 未被引擎加载。\n'
        '-- 源码：server/local_server.lua（改这里没用，改那个文件再重新打包）\n'
        'do\n'
        '  local __dsh_srv_src = [====[\n%s\n]====]\n'
        '  local __dsh_chunk, __dsh_cerr = loadstring(__dsh_srv_src, "dsh_local_server")\n'
        '  if not __dsh_chunk then\n'
        '    pcall(function() print("[DSH_SRV] compile_fail " .. tostring(__dsh_cerr)) end)\n'
        '    if type(__dsh_rep) == "function" then __dsh_rep("srv_compile_fail", tostring(__dsh_cerr)) end\n'
        '  else\n'
        '    local __dsh_ok, __dsh_rerr = pcall(__dsh_chunk)\n'
        '    if not __dsh_ok then\n'
        '      pcall(function() print("[DSH_SRV] run_fail " .. tostring(__dsh_rerr)) end)\n'
        '      if type(__dsh_rep) == "function" then __dsh_rep("srv_run_fail", tostring(__dsh_rerr)) end\n'
        '    end\n'
        '  end\n'
        'end\n'
        '-- ==============================================================\n'
    ) % (port, src)
    report.append('  embedded local server injected (listen=*:%d host=%s game=%d report=%r)'
                  % (port, host, game_port, report_url or ''))
    report.append('  APK files added: assets/src/main.lua (bootstrap), '
                  'assets/src/dsh_server.lua (%d bytes)' % len(src))
    return {'server': src, 'main': main_src, 'wrapper': wrapper, 'inject': wrapper}


def patch_lua_text(data: bytes, base: str, urlcfg_path: str, local_login: bool, report,
                   inject: bool = True, embedded: str = None, server_src: str = None,
                   obs_only: bool = False, extra_lua: str = None):
    """改写明文的 assets/src/config.luac。

    ⚠ 编码：原包 1.4.11 的 config.luac 是 **UTF-8**（`GAME_NAME = "绝世唐门"` 的字节
       是 e7 bb 9d…；按 GBK 解码直接失败），1.3.0 的老包才是 GBK。此处原先硬写
       GBK + errors='replace' ⇒ 会把 1.4.11 的中文全部替换成 '?'（注释与 GAME_NAME
       一起变乱码）。改为按文件实际编码自适应，最后统一输出 UTF-8 再追加 UTF-8 注入块。
    """
    # 原文按实际编码解码；下面的替换都在**原编码字节**上做（模式都是 ASCII，安全）
    try:
        data.decode('utf-8')
        enc = 'utf-8'
    except UnicodeDecodeError:
        enc = 'gbk'
    report.append('  config.luac source encoding = %s' % enc)
    src_bytes = data.decode(enc, errors='replace').encode(enc, errors='replace')
    new_url = base + urlcfg_path
    text2, cnt = LUA_URL_RE.subn(lambda mm: mm.group(1) + new_url.encode('ascii') + mm.group(3),
                                 src_bytes)
    report.append('  URL_LUA_CONFIG -> %s  (replaced %d)' % (new_url, cnt))
    if local_login:
        before = text2
        text2 = re.sub(rb'IS_PLATFORM_LOGIN\s*=\s*true', b'IS_PLATFORM_LOGIN = false', text2)
        text2 = re.sub(rb'IS_PLATFORM_LOGIN\s*=\s*True', b'IS_PLATFORM_LOGIN = false', text2)
        if text2 != before:
            report.append('  IS_PLATFORM_LOGIN true -> false (走本地账号登录，绕开已停服的 SDK)')
        else:
            report.append('  !! IS_PLATFORM_LOGIN not found (check config.luac)')
    from_orig = text2.decode(enc, errors='replace')
    if not inject:
        report.append('  (未注入 URL 全局变量 —— 使用服务端下发的 url_config)')
        text2 = from_orig.encode('utf-8')
        if embedded:
            text2 = text2 + embedded.encode('utf-8')
        if extra_lua:
            text2 = text2 + extra_lua.encode('utf-8')
        return text2
    # Inject the URL globals directly into the plain-text config: the client
    # otherwise only picks them up from the downloaded url_config.lua, which
    # (per `if not URL_PATH then` in file_update.luac) did not take effect.
    # Inject the URL globals directly into the plain-text config.luac: this file
    # is loaded at startup, BEFORE any network access, whereas the downloaded
    # url_config arrives too late (the version check already threw on nil
    # URL_PATH and the caller shows "版本文件错误").  Keep the block minimal and
    # ASCII-only so it cannot break config parsing.
    inject = ('\n\n-- ===== injected by DSH private server =====\n'
              '-- ⚠ 顺序很重要：内置服务端必须在**任何诊断上报之前**绑定端口。\n'
              '--   下面这段 __dsh_rep 从定义起就会发 HTTP，早于服务端绑定的话\n'
              '--   启动瞬间会打出一串 connect failed（纯噪音，但会误导排查）。\n'
              'do\n'
              '  local __dsh_sp = package and package.loaded and package.loaded.__dsh_local_server\n'
              '  if (not __dsh_sp) and type(loadstring) == "function" then\n'
              '    local __dsh_src = [====[\n%(srv)s\n]====]\n'
              '    local __dsh_c = loadstring(__dsh_src, "dsh_local_server")\n'
              '    if __dsh_c then pcall(__dsh_c) end\n'
              '  end\n'
              '  -- 尽早预置本地登录数据：denglu_mgr 构造时会 readTableForKey\n'
              '  -- ("last_login_account")，必须赶在它之前写入，否则 openView 会停在登录页。\n'
              '  pcall(function()\n'
              '    local S = __dsh_sp or _G.__DSH_SERVER\n'
              '    if S and S.preload_login_record then pcall(S.preload_login_record) end\n'
              '  end)\n'
              '  -- ✅ 关键修复：让 main() **自己**调用 ver_load_start()。\n'
              '  --   main.luac proto#0 尾部已用字节码确认（指令 118-128）：\n'
              '  --     120 GGET IS_PLATFORM_LOGIN\n'
              '  --     122 JMP  ->126     (IS_PLATFORM_LOGIN 为假时跳去调用)\n'
              '  --     123 GGET _is_game_restart\n'
              '  --     125 JMP  ->128     (_is_game_restart 为假时直接 return)\n'
              '  --     126 GGET ver_load_start    <- 全局量\n'
              '  --     127 CALL\n'
              '  --   只要 _is_game_restart 为真，main() 就在这一行同步调用它。\n'
              '  --   旧注释断言"此刻 ver_load_start 仍是 nil"是**错的**：\n'
              '  --   file_update.luac 根原型执行的是 FNEW/GSET ver_load_start\n'
              '  --   （tools/analyze_flow2.py file_update.luac 40 可见），\n'
              '  --   发生在 main() 的 require("file_update") 处，远早于指令 126。\n'
              '  --   ⚠ 为什么必须走这条同步路径（本轮实测的死锁）：\n'
              '  --     RunningScene 为 nil -> 挂在节点上的 Action 不触发 ->\n'
              '  --     我们的 tick 永不执行 -> 没人调 ver_load_start -> 永远没有场景。\n'
              '  --   同步调用发生在 main() 内部，完全不依赖定时器/场景。\n'
              '  _is_game_restart = true\n'
              'end\n'
              'local __dsh_rep = function(tag, val)\n'
              '  pcall(function()\n'
              '    if cc and cc.XMLHttpRequest then\n'
              '      -- 顺手排空内置服务端一次：引擎在加载阶段不提供任何定时回调\n'
              '      -- （scheduler / Node update / Action 三条路实测都不触发），\n'
              '      -- 所以把"客户端自己的请求时机"当节拍器用 —— 每次上报都\n'
              '      -- 让服务端跑一轮 select/accept/read/respond。\n'
              '      if __dsh_srv_tick then pcall(__dsh_srv_tick) end\n'
              '      local r = cc.XMLHttpRequest:new()\n'
              '      r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING\n'
              '      local v = tostring(val)\n'
              '      if #v > 170 then v = v:sub(1, 170) end\n'
              '      r:open("GET", "%(b)s/DSH_REPORT?tag=" .. tag .. "&v=" .. v:gsub("[^%%w%%.%%:/-]", "_"))\n'
              '      r:send()\n'
              '    end\n'
              '  end)\n'
              'end\n'
              'URL_PATH = {\n'
              '  update = "%(b)s/update",\n'
              '  voice = "%(b)s/voice",\n'
              '  register = "%(b)s/register",\n'
              '  is_shenhe = false,\n'
              '  server = "%(b)s",\n'
              '}\n'
              'URL_PATH_ALL = { get = function(platform) return URL_PATH end }\n'
              'CDN_PATH_BASE = "%(b)s"\n'
              'CDN_URL = "%(b)s/cdn/"\n'
              'url_res_config = "%(b)s/cdn/"\n'
              '-- ⚠ 必须是【函数】：denglu_mgr proto[22] / proto[53] 会 CALL 它。\n'
              '--   写成字符串 ⇒ 客户端抛\n'
              '--   "attempt to call global \'get_servers_url\' (a string value)"\n'
              '--   并中断登录界面构建（login_panel / server_panel / user_panel 全不加载）。\n'
              'function get_servers_url(...) return "%(b)s/gateway/mobile/json" end\n'
              'function get_notice_url(...) return "%(b)s/notice.json" end\n'
              '-- file_update.luac proto#5 branch:\n'
              '--   if not WIN_UPDATE and (platform == Windows or Mac) then update_finish() end\n'
              '--   if UPDATE_SKIP then update_finish(self) else update_version(self) end\n'
              '-- 关键：UPDATE_SKIP 是**在调用点用 GGET 读取的全局量**，因此在 config.luac\n'
              '-- 里赋值即可生效 —— 这样 Android 上直接走 update_finish（无需更新），\n'
              '-- 完全不碰 AssetsManager / version2.txt 那条会卡 10 秒超时的链路。\n'
              'WIN_UPDATE = false\n'
              'UPDATE_SKIP = true\n'
              '-- ★ 跳过开场 CG（gamecg.mp4）。**不能靠删文件**：\n'
              '--   file_update proto#39 video_player 只在两处 isFileExist 判断 writable 副本，\n'
              '--   默认路径 "res/resource/login/gamecg.mp4" 是不判断的 ⇒ 文件缺失时\n'
              '--   ccexp.VideoPlayer:play() 失败，native 弹「视频问题 / 无法播放此视频。」\n'
              '--   把整个启动卡住（实测 logcat: Cocos2dxVideoView: Error: 1,0）。\n'
              '--   真正的开关是源码里现成的：proto#39 开头 `if NO_PLAY_VIDEO then return true end`\n'
              '--   ⇒ 定义本全局后 video_player 立即返回 true ⇒ video_finish = true ⇒\n'
              '--   update_finish 正常走到 initInstance/beginGame，无任何视频相关弹窗。\n'
              'NO_PLAY_VIDEO = true\n'
              '-- The version-check code calls FmodexManager:downloadOtherFile(...) but the\n'
              '-- global is never created on our bypassed startup path (probe: nil for 15s),\n'
              '-- which throws and surfaces as the version-file error.  Provide it from cc.\n'
              '-- The native downloader (global FmodexManager) is never initialised on our\n'
              '-- patched startup, so the version download silently does nothing.  Implement\n'
              '-- downloadOtherFile in Lua on top of cc.XMLHttpRequest: write the body to\n'
              '-- <writable>/assets/src/<name> and then fire the client own\n'
              '-- OnFileDownloadResult(name) callback (see file_update.luac proto#8).\n'
              'pcall(function()\n'
              '  local __ccF = cc and cc.FmodexManager\n'
              '  local function __dsh_dl(self, url, filename)\n'
              '    __dsh_rep("shim_dl", tostring(url) .. " => " .. tostring(filename))\n'
              '    pcall(function()\n'
              '      local base = cc.FileUtils:getInstance():getWritablePath() .. "assets/src/"\n'
              '      pcall(function() cc.FileUtils:getInstance():createDirectory(base) end)\n'
              '      local req = cc.XMLHttpRequest:new()\n'
              '      req.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING\n'
              '      req:open("GET", url)\n'
              '      local fired = false\n'
              '      req:registerScriptHandler(function()\n'
              '        if fired then return end\n'
              '        fired = true\n'
              '        local body = req.response or ""\n'
              '        local status = req.status\n'
              '        local path = base .. tostring(filename)\n'
              '        local okw = false\n'
              '        local f = io.open(path, "w")\n'
              '        if f then f:write(body) f:close() okw = true end\n'
              '        __dsh_rep("shim_dl_done", tostring(status) .. "|len=" .. tostring(#body) .. "|ok=" .. tostring(okw))\n'
              '        if type(OnFileDownloadResult) == "function" then\n'
              '          -- handler signature is (content, filename) -- see common_function proto#125\n'
              '          local ok, err = pcall(OnFileDownloadResult, body, tostring(filename))\n'
              '          __dsh_rep("shim_cb", tostring(ok) .. "|" .. tostring(err))\n'
              '        else\n'
              '          __dsh_rep("shim_cb", "OnFileDownloadResult missing")\n'
              '        end\n'
              '      end)\n'
              '      req:send()\n'
              '    end)\n'
              '  end\n'
              '  FmodexManager = setmetatable({ downloadOtherFile = __dsh_dl, downloadFile = __dsh_dl },\n'
              '    { __index = function(_, k) if __ccF then return __ccF[k] end return nil end })\n'
              '  -- The version check actually calls cc.FmodexManager:downloadOtherFile(url, "version.txt")\n'
              '  -- (common_function.luac proto#126), so patch the class table too.\n'
              '  if __ccF and type(__ccF.downloadOtherFile) == "function" then\n'
              '    __ccF.downloadOtherFile = __dsh_dl\n'
              '    __ccF.downloadFile = __dsh_dl\n'
              '    __dsh_rep("shim_cc", "cc.FmodexManager.downloadOtherFile replaced")\n'
              '  else\n'
              '    __dsh_rep("shim_cc", "cc.FmodexManager.downloadOtherFile NOT a function")\n'
              '  end\n'
              '  __dsh_rep("shim", "FmodexManager.downloadOtherFile implemented")\n'
              'end)\n'
              'pcall(function()\n'
              '  if cc and cc.XMLHttpRequest then\n'
              '    local r = cc.XMLHttpRequest:new()\n'
              '    r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING\n'
              '    r:open("GET", "%(b)s/DSH_CONFIG_LUAC_LOADED")\n'
              '    r:send()\n'
              '  end\n'
              'end)\n'
              '-- Capture every Lua error and print, and report them over HTTP so\n'
              '-- diagnosis does not depend on logcat.  (__dsh_rep is defined above.)\n'
              'if not _G.__dsh_hooked then\n'
              '  _G.__dsh_hooked = true\n'
              '  local __op = pcall\n'
              '  pcall = function(f, ...)\n'
              '    -- 重入保护：__dsh_rep 内部也会 pcall，不设这个标志会\n'
              '    -- pcall -> hook -> __dsh_rep -> pcall -> ... 无限递归\n'
              '    -- （实测表现为 [LUA ERROR] config.luac:148: stack overflow，\n'
              '    --   config chunk 整体失败、游戏毫无反应）\n'
              '    if _G.__dsh_in_hook then return __op(f, ...) end\n'
              '    _G.__dsh_in_hook = true\n'
              '    local a, b, c, d = __op(f, ...)\n'
              '    if not a then __dsh_rep("pcall_err", tostring(b)) end\n'
              '    _G.__dsh_in_hook = false\n'
              '    return a, b, c, d\n'
              '  end\n'
              '  local __ox = xpcall\n'
              '  if __ox then\n'
              '    xpcall = function(f, h, ...)\n'
              '      if _G.__dsh_in_hook then return __ox(f, h, ...) end\n'
              '      local a, b = __ox(f, function(e)\n'
              '        _G.__dsh_in_hook = true\n'
              '        __dsh_rep("xpcall_err", tostring(e))\n'
              '        _G.__dsh_in_hook = false\n'
              '        return h(e)\n'
              '      end, ...)\n'
              '      return a, b\n'
              '    end\n'
              '  end\n'
              '  local __opr = print\n'
              '  print = function(...)\n'
              '    local n = select("#", ...)\n'
              '    local t = {}\n'
              '    for i = 1, n do t[i] = tostring((select(i, ...))) end\n'
              '    __dsh_rep("print", table.concat(t, " "))\n'
              '    return __opr(...)\n'
              '  end\n'
              '  __dsh_rep("hooks", "pcall/xpcall/print installed")\n'
              'end\n'
              '-- Intercept string.format: the version check builds its URL via\n'
              '-- string.format("%%s/version2.txt?ts=%%s", URL_PATH.update, os.time())\n'
              '-- so we can both observe it and force the host to ours.\n'
              'if not _G.__dsh_fmt_hooked then\n'
              '  _G.__dsh_fmt_hooked = true\n'
              '  local __ofmt = string.format\n'
              '  string.format = function(fmt, ...)\n'
              '    local r = __ofmt(fmt, ...)\n'
              '    if type(r) == "string" and (r:find("version2") or r:find("tryver")) then\n'
              '      __dsh_rep("fmt_url", r)\n'
              '      local fixed = r:gsub("^https?://[^/]+", "%(b)s")\n'
              '      if fixed ~= r then\n'
              '        __dsh_rep("fmt_fixed", fixed)\n'
              '        return fixed\n'
              '      end\n'
              '    end\n'
              '    return r\n'
              '  end\n'
              '  __dsh_rep("hooks", "string.format installed")\n'
              'end\n'
              '-- The version download silently fails in the native layer, so the game sits\n'
              '-- on the version screen.  Drive the client s own "no update needed" entry\n'
              '-- (update_finish) from a timer once the module globals exist.\n'
              'if not _G.__dsh_ticker then\n'
              '  _G.__dsh_ticker = true\n'
              '  pcall(function()\n'
              '    local d = cc and cc.Director and cc.Director:getInstance()\n'
              '    local sch = d and d:getScheduler()\n'
              '    if not sch then __dsh_rep("ticker", "NO_SCHEDULER"); return end\n'
              '    local ticks = 0\n'
              '    local done = false\n'
              '    local entry\n'
              '    local function tick()\n'
              '      ticks = ticks + 1\n'
              '      URL_PATH = { update = "%(b)s/update", voice = "%(b)s/voice",\n'
              '                   register = "%(b)s/register", is_shenhe = false, server = "%(b)s" }\n'
              '      if ticks == 2 or ticks == 12 or ticks == 30 then\n'
              '        __dsh_rep("tick", tostring(ticks) .. " update_finish=" .. type(update_finish))\n'
              '      end\n'
              '      -- The downloader shim now works, so let the client own version flow run;\n'
              '      -- only report state here (do NOT call getNowVersion ourselves: it needs the\n'
              '      -- login controller callback/upvalues, see denglu_ctrl proto#42/#45).\n'
              '      if ticks == 20 then\n'
              '        local names = {}\n'
              '        pcall(function()\n'
              '          for k in pairs(package.loaded) do\n'
              '            if type(k) == "string" and k:lower():find("denglu") then names[#names+1] = k end\n'
              '          end\n'
              '        end)\n'
              '        __dsh_rep("state20", "DengluCtrl=" .. type(DengluCtrl) .. " loaded=" .. table.concat(names, ","))\n'
              '      end\n'
              '      if ticks >= 60 and entry then\n'
              '        pcall(function() sch:unscheduleScriptEntry(entry) end)\n'
              '      end\n'
              '    end\n'
              '    entry = sch:scheduleScriptFunc(tick, 0.5, false)\n'
              '    __dsh_rep("ticker", "installed")\n'
              '  end)\n'
              'end\n'
              '-- ===== DSH hot patch：从应用私有目录加载可变补丁（免重打包迭代）=====\n'
              '--   实测搜索路径顺序（logcat printSearchPaths）是\n'
              '--     assets/ , <writable>/assets/res/ , <writable>/assets/src/ , assets/res/ , assets/src/\n'
              '--   打包的 assets/ 在最前，所以往 writable 推 config.luac **无法**覆盖打包版\n'
              '--   （已实测：推 6 个候选路径，无一生效）。改由这里的引导代码用绝对\n'
              '--   路径读取 <writable>/dsh_patch.lua 并执行 —— 之后迭代只需\n'
              '--   `adb push dsh_patch.lua /data/data/<pkg>/files/dsh_patch.lua`。\n'
              'pcall(function()\n'
              '  if _G.__dsh_patch_ran then return end\n'
              '  _G.__dsh_patch_ran = true\n'
              '  local wp = cc.FileUtils:getInstance():getWritablePath()\n'
              '  local path = wp .. "dsh_patch.lua"\n'
              '  local f = io.open(path, "rb")\n'
              '  if not f then print("[DSH_PATCH] no patch file at " .. path) return end\n'
              '  local src = f:read("*a")\n'
              '  f:close()\n'
              '  if not src or #src == 0 then print("[DSH_PATCH] empty patch") return end\n'
              '  local chunk, err = loadstring(src, "@dsh_patch")\n'
              '  if not chunk then print("[DSH_PATCH] SYNTAX ERROR: " .. tostring(err)) return end\n'
              '  local ok, e = pcall(chunk)\n'
              '  print("[DSH_PATCH] ran ok=" .. tostring(ok) .. " " .. tostring(e))\n'
              'end)\n') % {'b': base, 'srv': server_src or ''}
    # 到这里 text2 是 GBK 字节；统一转 UTF-8 后再追加 UTF-8 注入块，
    # 避免同一文件混编码（曾导致注入块在文件里不闭合）。
    # ★★ 联调模式的**最小诊断注入**（--obs-only）：
    #   只放两样东西 —— ① 观测器（诊断/探针通道）② dsh_patch.lua 热补丁加载器。
    #   为什么不能带"完整注入块"：那块是给**单机内置服**设计的（UPDATE_SKIP=true、
    #   _is_game_restart=true、FmodexManager 垫片、内嵌服务端），实测在联调
    #   （客户端连 PC mock_server）下会把正常版本/网关流程改坏 —— logcat
    #   `error网络异常`、客户端一条业务 HTTP 都不发、也不连 9000。
    if obs_only:
        head = ('\n\n-- ===== injected by DSH private server (obs-only) =====\n'
                '-- 只含观测器 + dsh_patch 热补丁加载器；不含单机块。\n')
        obs_src = read_lua(OBSERVER_LUA, report, 'url observer')
        hot = ('\n-- ---- DSH hot patch loader (obs-only) ----\n'
               'pcall(function()\n'
               '  if _G.__dsh_patch_ran then return end\n'
               '  _G.__dsh_patch_ran = true\n'
               '  local wp = cc.FileUtils:getInstance():getWritablePath()\n'
               '  local f = io.open(wp .. "dsh_patch.lua", "rb")\n'
               '  if not f then print("[DSH_PATCH] no patch file") return end\n'
               '  local src = f:read("*a")\n'
               '  f:close()\n'
               '  local chunk, err = loadstring(src, "@dsh_patch")\n'
               '  if not chunk then print("[DSH_PATCH] SYNTAX ERROR: " .. tostring(err)) return end\n'
               '  local ok, e = pcall(chunk)\n'
               '  print("[DSH_PATCH] ran ok=" .. tostring(ok) .. " " .. tostring(e))\n'
               'end)\n')
        text2 = from_orig.encode('utf-8') + head.encode('utf-8')
        if obs_src:
            text2 = text2 + obs_src.encode('utf-8')
        text2 = text2 + hot.encode('utf-8')
        if extra_lua:
            text2 = text2 + extra_lua.encode('utf-8')
            report.append('  extra lua appended (%d bytes)' % len(extra_lua))
        report.append('  obs-only injection: observer + dsh_patch loader (NO solo block)')
        return text2

    text2 = from_orig.encode('utf-8') + inject.encode('utf-8')
    report.append('  injected minimal URL_PATH table into config.luac (base=%s)' % base)
    # ★★ 把 observer 与"内置服务端"**解耦**：即使 --no-embedded（联调版，
    #   URL 指向 PC mock_server），也要注入 server/observer.lua。
    #   原因：诊断上报 / 表探针通道都在 observer 里（本轮要用它 dump 客户端表结构）；
    #   旧逻辑把 observer 放在 `if embedded:` 里面 ⇒ 联调版没有任何诊断通道。
    obs_src = read_lua(OBSERVER_LUA, report, 'url observer')
    if obs_src:
        text2 = text2 + obs_src.encode('utf-8')
        report.append('  url observer injected (server/observer.lua)')
    if embedded:
        text2 = text2 + embedded.encode('utf-8')
    if extra_lua:
        text2 = text2 + extra_lua.encode('utf-8')
        report.append('  extra lua appended (%d bytes)' % len(extra_lua))
    return text2


def patch_binary_urls(data: bytes, bases, idx, report, where: str):
    """Equal-length replacement of cdn-style URLs inside compiled .luac."""
    out = bytearray(data)
    n = 0
    for m in ANY_URL_RE.finditer(bytes(data)):
        orig = m.group()
        if b'ewan.cn' not in orig and b'jstm' not in orig:
            continue
        tail = orig.split(b'/', 3)
        path = '/' + tail[3].decode('latin1') if len(tail) > 3 else '/'
        try:
            new, _ = pick(orig, path, bases, idx[0])
        except ValueError as e:
            report.append('  !! %s: cannot fit %s (%s)' % (where, orig.decode('latin1'), e))
            continue
        out[m.start():m.end()] = new
        report.append('  %s: %s -> %s' % (where, orig.decode('latin1'), new.decode()))
        idx[0] += 1
        n += 1
    return bytes(out), n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--host', required=True)
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--hosts', default='',
                    help='comma separated extra hosts to cycle through, e.g. '
                         '10.16.153.137,10.0.2.2,192.168.56.1')
    ap.add_argument('--url-config-path', default='/update/config/url_config_ewan.lua')
    ap.add_argument('--keep-platform-login', action='store_true',
                    help='do not flip IS_PLATFORM_LOGIN to false')
    ap.add_argument('--no-inject', action='store_true',
                    help='do NOT inject URL globals into config.luac '
                         '(use when the served url_config is authoritative)')
    # ---- 单机版（服务端内置）相关 ----
    ap.add_argument('--local-port', type=int, default=18080,
                    help='内置服务端在本机监听的 HTTP 端口（默认 18080）')
    ap.add_argument('--game-port', type=int, default=19000,
                    help='下发给客户端的游戏服 TCP 端口（默认 19000）')
    ap.add_argument('--report-url', default='',
                    help='内置服务端向外上报诊断的地址，例如 http://10.0.0.2:8080；'
                         '留空 = 纯单机不上报')
    ap.add_argument('--obs-only', action='store_true',
                    help='只注入观测器+热补丁加载器（联调用，不带单机块）')
    ap.add_argument('--no-embedded', action='store_true',
                    help='不注入内置服务端（仍做普通改包，用于联调 PC mock_server）')
    ap.add_argument('--embedded-host', default=None,
                    help='内置服务端下发给客户端的服务器 IP（默认取 --host）')
    ap.add_argument('--keep-cg', action='store_true',
                    help='保留开场 CG 视频 gamecg.mp4（默认丢弃：模拟器上视频播不完，'
                         '会导致永远进不了登录界面）')
    ap.add_argument('--extra-lua', default='',
                    help='额外追加到 config.luac 末尾的 Lua 文件（会过 lua-check 语法门禁）；'
                         '本轮用于注入 server/dsh_3zones.lua（三区选区列表）')
    ap.add_argument('--embed-main', action='store_true',
                    help='额外把 server/main_lua.lua 打成 assets/src/main.lua。'
                         '⚠ 默认关闭：APK 里已有 assets/src/main.luac，放同名 .lua '
                         '会把引擎的 main() 顶掉（实测游戏直接不启动）')
    args = ap.parse_args()
    drop_cg = not args.keep_cg

    host_list = [args.host] + [h.strip() for h in args.hosts.split(',') if h.strip()]
    bases = []
    for h in host_list:
        b = 'http://%s:%d' % (h, args.port)
        if b not in bases:
            bases.append(b)
    base = bases[0]
    idx = [0]
    report = ['base order = %s' % ', '.join(bases)]

    embedded = None
    if not args.no_embedded:
        embedded = load_embedded_server(
            report,
            base,
            args.embedded_host or args.host,
            args.local_port,
            args.game_port,
            args.report_url,
        )
    extra_lua = None
    if args.extra_lua:
        extra_lua = read_lua(args.extra_lua, report, 'extra lua')
        if extra_lua is None:
            sys.exit('FATAL: --extra-lua %s 未通过语法门禁/不存在' % args.extra_lua)
    os.makedirs(os.path.dirname(os.path.abspath(args.dst)), exist_ok=True)

    zin = zipfile.ZipFile(args.src)
    zout = zipfile.ZipFile(args.dst, 'w', zipfile.ZIP_DEFLATED)
    counts = {'so': 0, 'luac': 0, 'cfg': 0}
    for info in zin.infolist():
        data = zin.read(info.filename)
        name = info.filename
        # 单机版：剔除开场 CG 视频（见 CG_VIDEO 说明）——必须
        # 进不了登录界面就是因为视频在这个模拟器上永远播不完。
        if drop_cg and name == CG_VIDEO:
            report.append('  dropped CG video: %s (%d bytes) -> video_player 走 fallback'
                          % (name, len(data)))
            counts['dropped'] = counts.get('dropped', 0) + 1
            continue
        if name.endswith('.so'):
            data, n = patch_so(data, bases, idx, report)
            counts['so'] += n
        elif name == 'assets/src/config.luac':
            data = patch_lua_text(data, base, args.url_config_path,
                                  not args.keep_platform_login, report,
                                  inject=not args.no_inject,
                                  embedded=embedded['wrapper'] if embedded else None,
                                  server_src=embedded['server'] if embedded else None,
                                  obs_only=args.obs_only,
                                  extra_lua=extra_lua)
            counts['cfg'] += 1
        elif name.endswith('.luac'):
            data, n = patch_binary_urls(data, bases, idx, report, name.split('/')[-1])
            counts['luac'] += n
        zi = zipfile.ZipInfo(name, date_time=info.date_time)
        zi.compress_type = info.compress_type
        zi.external_attr = info.external_attr
        zi.internal_attr = info.internal_attr
        zi.create_system = info.create_system
        zout.writestr(zi, data)

    # 单机版关键：把启动引导写成 assets/src/main.lua，服务端本体写成
    # assets/src/dsh_server.lua。两者都会被引擎释放到可写目录，而可写目录在
    # FileUtils 搜索路径里优先于 APK assets，所以引导能读到服务端源码。
    #
    # ⚠ 实测结论：**不要默认放 main.lua**。APK 里已有 assets/src/main.luac，
    #   引擎加载 src/main.lua 后不会再走 main.luac 的 main()，导致 initSearchPath /
    #   sdk_function / file_update 都不执行、游戏毫无反应。
    #   而"启动早期客户端 HTTP 抢先"这一顾虑经字节码分析证伪（客户端首批 HTTP
    #   其实来自我们自己注入的诊断上报）。因此默认只注入 config.luac。
    if embedded and args.embed_main:
        for member, content in (('assets/src/main.lua', embedded['main']),
                                ('assets/src/dsh_server.lua', embedded['server'])):
            zi = zipfile.ZipInfo(member, date_time=(2026, 1, 1, 0, 0, 0))
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            zout.writestr(zi, content.encode('utf-8'))
            counts['added'] = counts.get('added', 0) + 1

    zout.close()
    zin.close()

    print('patched -> %s' % args.dst)
    print('replacements: so=%d luac=%d config=%d added=%d'
          % (counts['so'], counts['luac'], counts['cfg'], counts.get('added', 0)))
    for line in report:
        print(line)
    print('next: zipalign + apksigner (see 路线图 §8.2)')


if __name__ == '__main__':
    main()
