-- ============================================================================
--  单机版启动引导（会被打进 APK 的 assets/src/main.lua）
-- ============================================================================
--  背景与关键坑位（都踩过，别再踩）：
--    1) 引擎启动时会找 `src/main.lua`；官方包只有 `src/main.luac`，所以日志里
--       一直是 "No file found at src/main.lua"。放一个 main.lua 进去，就能在
--       **任何游戏逻辑之前**启动内置服务端，消除"首批 HTTP 比服务端早几毫秒
--       → 全部 connect failed → 卡在版本页且不再重试"的竞态。
--    2) 但 APK 里已存在 `src/main.luac`，而 `require("src.main")` 会优先命中
--       `.lua` —— 直接放一个自己的 main.lua 会把游戏主逻辑整个顶掉
--       （表现：启动后毫无动静，连更新流程都不进）。
--       解决：先把原始 `src/main.luac` 的工厂函数塞进 `package.loaded`，
--       逐字节转发给引擎原本的 require 调用，再执行本文件其余部分。
--    3) main.luac 自身不返回值（只做搜索路径/分辨率设置 + require config），
--       因此转发一个空工厂就完全等价。
--
--  加载路径：APK 的 assets/src/dsh_server.lua 会被引擎释放到
--    /data/user/0/<pkg>/files/assets/src/dsh_server.lua
--    该目录在 FileUtils 搜索路径里优先，所以能读到。
--
--  容错：任何一步失败都只打日志、不抛异常。
-- ============================================================================

local function log(msg)
    pcall(function() print("[DSH_BOOT] " .. tostring(msg)) end)
end

log("main.lua bootstrap start")

-- ---------------------------------------------------------------------------
-- 1) 先起内置服务端（越早越好）
-- ---------------------------------------------------------------------------
local ok, err = pcall(function()
    local fu = cc and cc.FileUtils and cc.FileUtils:getInstance()
    if not fu then error("cc.FileUtils unavailable") end

    local src = fu:getStringFromFile("src/dsh_server.lua")
    if src == nil or src == "" then
        error("cannot read src/dsh_server.lua (search path?)")
    end
    log("loaded dsh_server.lua, " .. tostring(#src) .. " bytes")

    local chunk, cerr = loadstring(src, "dsh_server")
    if not chunk then error("loadstring failed: " .. tostring(cerr)) end

    local ok2, rerr = pcall(chunk)
    if not ok2 then error("dsh_server runtime error: " .. tostring(rerr)) end

    log("embedded server module loaded")
end)
if not ok then log("server FAILED: " .. tostring(err)) end

-- ---------------------------------------------------------------------------
-- 2) 复刻原始 main.luac 的初始化顺序（顺序很重要！）
--    原始 main.luac：设置搜索路径 → require("config") → require("file_update")
--    我们必须在 require("config") **之前**把服务端起好（上面已做），
--    否则又回到"首批 HTTP 打不到服务端"的老问题。
-- ---------------------------------------------------------------------------
local ok3, err3 = pcall(function()
    local fu = cc.FileUtils:getInstance()
    pcall(function() fu:setSearchPaths({
        "src", "res", "assets/src", "assets/res",
        "tryver/assets/src", "tryver/assets/res",
    }) end)

    -- 先装 package.preload 别名，防止引擎后续 require("src.main") 再跑一遍本文件
    pcall(function()
        if type(package) == "table" and type(package.loaded) == "table" then
            local function noop()
                log("original main module required (forwarded)")
                return true
            end
            package.preload["src.main"] = noop
            package.preload["src/main"] = noop
            log("package.preload aliases installed for src.main")
        end
    end)

    local wanted = { "config", "file_update", "sdk_function" }
    for _, m in ipairs(wanted) do
        log("about to require(" .. m .. ")")
        local okr, errr = pcall(require, m)
        log("require(" .. m .. ") ok=" .. tostring(okr) ..
            (okr and "" or (" err=" .. tostring(errr))))
    end
    log("all requires done")
end)
if not ok3 then log("init FAILED: " .. tostring(err3)) end

log("main.lua bootstrap done")
