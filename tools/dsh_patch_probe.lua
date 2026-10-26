-- ============================================================================
--  DSH 热补丁：探针 v6 —— 找修炼面板的**运行时入口**
--  v5 结论：给 SkillXiulianLev/Huoli/RiChang 挂 __index 后**没有任何缺键读取**
--            ⇒ 面板打开时不查这些配置表的"缺失键"；数据来自运行时对象。
--  线索：package.loaded 里有 `game/sworn/skill`、`game/daily/...` 等键（说明**部分模块走
--        标准 require 缓存**），v6 把 loaded 全量列出，并 dump skill/xiulian 模块的表结构。
-- ============================================================================
print("[DSH_PATCH6] loaded")

pcall(function()
    local function base()
        local b = _G.__dsh_p6_base
        if b then return b end
        local u = _G.URL_PATH and _G.URL_PATH.update
        if type(u) == "string" then
            b = u:gsub("/update$", "")
            if b ~= u and #b > 0 then _G.__dsh_p6_base = b return b end
        end
        return nil
    end
    local function rep(tag, s)
        pcall(function()
            local b = base()
            local X = cc and cc.XMLHttpRequest
            if not b or not X then return end
            local v = tostring(s):gsub("[^%w%._:/-]", "_")
            if #v > 150 then v = v:sub(1, 150) end
            local r = X:new()
            r.responseType = cc.XMLHTTPREQUEST_RESPONSE_STRING
            r:open("GET", b .. "/DSH_REPORT?tag=" .. tostring(tag) .. "&v=" .. v)
            r:send()
        end)
    end
    local function chunks(tag, items)
        local buf, n = {}, 0
        for _, s in ipairs(items) do
            if #table.concat(buf, ",") + #s + 1 > 130 then
                n = n + 1
                rep(tag .. n, table.concat(buf, ","))
                buf = {}
            end
            buf[#buf + 1] = s
        end
        if #buf > 0 then n = n + 1 rep(tag .. n, table.concat(buf, ",")) end
        return n
    end

    local done, in_try = false, false
    local function try()
        if in_try or done then return end
        in_try = true
        if type(_G.Config) ~= "table" then in_try = false return end
        done = true

        -- 1) package.loaded 全量键名
        local all = {}
        pcall(function()
            for k, v in pairs(package.loaded) do
                if type(k) == "string" and #all < 300 then
                    all[#all + 1] = k .. ":" .. type(v)
                end
            end
            table.sort(all)
        end)
        rep("p6.n", "loaded=" .. #all)
        chunks("p6.ld", all)

        -- 2) skill/xiulian 模块的表结构
        pcall(function()
            for k, v in pairs(package.loaded) do
                if type(k) == "string" and type(v) == "table" then
                    local lk = k:lower()
                    if lk:find("skill", 1, true) or lk:find("xiulian", 1, true) then
                        local names = {}
                        for k2 in pairs(v) do
                            if #names < 14 then names[#names + 1] = tostring(k2) end
                        end
                        rep("p6.m." .. k:gsub("[/%.]", "_"):sub(1, 40),
                            table.concat(names, ","))
                    end
                end
            end
        end)

        -- 3) _G 里含 skill/xiulian 的全局
        local gs = {}
        pcall(function()
            for k, v in pairs(_G) do
                if type(k) == "string" then
                    local lk = k:lower()
                    if lk:find("skill", 1, true) or lk:find("xiulian", 1, true)
                       or lk:find("practice", 1, true) then
                        gs[#gs + 1] = k .. ":" .. type(v)
                    end
                end
            end
        end)
        chunks("p6.g", gs)
        in_try = false
    end
    _G.__dsh_p6_try = try

    pcall(function()
        cc.Director:getInstance():getScheduler():scheduleScriptFunc(function()
            pcall(try)
        end, 0.5, false)
        rep("p6.arm", "sched")
    end)
end)
