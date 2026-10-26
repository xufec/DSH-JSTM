-- =====================================================================
-- 《绝世唐门》本地配置服务器 —— 下发内容（**生产版，无探针**）
-- 对应客户端请求：GET /update/config/url_config_ewan.lua?<os.time()>
--
-- 客户端消费方式（file_update.luac proto#8 反汇编确认）：
--   1) 响应体被写入 <writable>/assets/src/url_config.lua
--   2) pcall(loadstring(响应体)())    ← 返回值被丢弃，必须写【全局】
--   3) 读全局 URL_PATH_ALL，调用 URL_PATH_ALL:get(PLATFORM_NAME) 得到 URL_PATH
--   4) URL_PATH 需含 update / voice / register / is_shenhe
--
-- 版本接口（file_update.luac proto#17 get_version_info 反汇编确认）：
--   target_ver = UPDATE_TRY_VERSION_MAX or UPDATE_VERSION_MAX
--   now_ver    = max(local_version, NOW_VERSION)
--   proto#19 #70-72: now_ver >= target_ver → update_finish()（跳过整个热更下载）
--
-- 说明：mock_server.py 会把下面两行替换成客户端实际请求用的 Host/Port，
--       所以绝对地址永远与客户端连上来的地址一致。
--
-- ★ 2026-10-16 修复（C4）：本文件此前被**诊断探针版本覆盖**（只剩 DSH_PROBE
--   上报代码，全部 URL_PATH / get_servers_url / CDN 定义丢失）。因为老装机器上的
--   `<writable>/assets/src/url_config.lua` 已有缓存，客户端不再回取本文件，
--   所以问题被掩盖；但**全新安装 / 清数据后**客户端会拉到这个空壳配置 ⇒
--   `get_servers_url` 未定义 ⇒ 客户端抛
--     "attempt to call global 'get_servers_url' (a string value)"
--   并中断登录界面构建。已恢复为生产版；探针版另存
--   `url_config_ewan.probe_only_20261016.lua`（要排查时再换回去）。
-- =====================================================================

local HOST = "127.0.0.1"
local PORT = 8080
local BASE = "http://" .. HOST .. ":" .. PORT

-- ---------- 1) URL_PATH_ALL：客户端用 :get(PLATFORM_NAME) 取分支 ----------
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

-- ---------- 2) 客户端其它模块引用的全局地址 ----------
URL_PATH        = URL_PATH_ALL:get(PLATFORM_NAME)   -- file_update / denglu_ctrl
CDN_PATH_BASE   = BASE
CDN_URL         = BASE .. "/cdn/"                    -- res_download_mgr
url_res_config  = BASE .. "/cdn/"                    -- res_download_mgr

-- ⚠ 这两个必须是【函数】，不是字符串。
-- 静态证据（tools/find_external_globals.py + 反汇编）：
--   denglu_mgr.luac   proto[22] @29  GGET get_servers_url   → @41 CALL A=4 (nargs=4) → open('POST', url)
--   notice_view.luac  proto[9]  @0   GGET get_notice_url    → @3  CALL A=3 (nargs=2) → web_view:loadURL(url)
-- 若误写成字符串，客户端抛
--   "attempt to call global 'get_servers_url' (a string value)"
-- 并中断登录界面构建（实测：login_panel / server_panel / user_panel 全部不再加载）。
function get_servers_url(...)
  return BASE .. "/gateway/mobile/json"                -- denglu_mgr
end

function get_notice_url(...)
  return BASE .. "/notice.json"                        -- notice_view
end

-- ---------- 3) 版本上限：令 now_ver >= target_ver 恒成立 ----------
-- 只定义 UPDATE_VERSION_MAX（proto#17 默认读取的那个），不伪造 TRY 分支字段。
UPDATE_VERSION_MAX = NOW_VERSION

return { URL_PATH = URL_PATH, URL_PATH_ALL = URL_PATH_ALL }
