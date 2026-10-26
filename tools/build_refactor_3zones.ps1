<#
.SYNOPSIS
  《绝世唐门》1.4.11「删渠道登录 + 保留账号/区服 + 三区」重构包一键构建。

.DESCRIPTION
  源包：anzbao\jstm_142165.apk（1.4.11 / com.shiyue.dldl.ewan.baidu2 / versionCode 46）。
  四步，每步都有断言，失败即中止：

    [1] DEX：EwanSdk.is_close = true
        ⇒ 渠道 SDK（ewan / 百度 SuperSDK）整体静默：不初始化、不登录、不弹窗、不联网。
          这是"删去渠道登录流程"的根治点（is_close 在整个 dex 里只有 <init> 一处写入，
          其余 17 处全是 iget-boolean 守卫）。
    [2] config.luac：IS_PLATFORM_LOGIN = true → false
        ⇒ 登录界面 view4 由 PlatformPanel（渠道登录）切成 UserPanel（客户端自带账号登录：
          账号 / 密码 / 一键注册）；区服选择（LoginPanel「点击选区」→ ServerPanel）保留。
    [3] config.luac 追加 server\dsh_refactor.lua
        ⇒ 本地地址 + NO_PLAY_VIDEO（跳过开场 CG）+ 三区（唐门一区 / 昊天二区 / 史莱克三区）。
    [4] zipalign + apksigner(v1+v2) ⇒ 可直接 adb install

  为什么不用 tools\patch_apk.py：那条链会追加 ~11KB 的**单机/联调诊断注入块**
  （UPDATE_SKIP、_is_game_restart、FmodexManager 垫片、pcall/print/string.format 钩子、
  DSH_REPORT 上报）。实测（2026-10-17，模拟器 emulator-5554）该块让客户端停在
  「初始化处理... 100%」（file_update proto#33 var_33_3 → initInstance 未走到 beginGame，
  无 Lua 报错）。本脚本走**最小注入**（本工程已实机验证的 fake-login 链），
  客户端侧只有一个文件 dsh_refactor.lua。

.EXAMPLE
  pwsh tools\build_refactor_3zones.ps1
  pwsh tools\build_refactor_3zones.ps1 -Install
#>
[CmdletBinding()]
param(
  [string]$Src        = 'anzbao\jstm_142165.apk',
  [string]$Host_      = '10.0.2.2',
  [int]$HttpPort      = 8080,
  [int]$GamePort      = 9000,
  [string]$InjectLua  = 'server\dsh_refactor.lua',
  [string]$Out        = 'patched\jstm_1411_3zones.apk',
  [string]$BuildTools = 'D:\Android\SDK\build-tools\34.0.0',
  [string]$Keystore   = 'patched\dsh.keystore',
  [string]$Device     = 'emulator-5554',
  [string]$VerifyOnly = '',
  [switch]$Install
)

$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$t0 = Get-Date

$stage   = 'patched\_3z_stage.raw.apk'
$aligned = 'patched\_3z_aligned.apk'
$luaTmp  = 'patched\_3z_inject.lua'

# -VerifyOnly <apk>：只跑校验（对已有产物复检，不重新打包）。
if ($VerifyOnly) {
  Write-Host "== 仅校验已有产物：$VerifyOnly ==" -ForegroundColor Cyan
  $script:stageOverride = $VerifyOnly
  $stage = $VerifyOnly
}

# ---------------------------------------------------------------- [0] 语法门禁
if (-not $VerifyOnly) {
Write-Host "== [0/6] Lua 语法门禁 ==" -ForegroundColor Cyan
node tools\lua-check\check.js $InjectLua
if ($LASTEXITCODE -ne 0) { throw "lua-check 未过：$InjectLua" }

# ---------------------------------------------------------------- [1] 注入块（写入本次构建的 HOST/PORT）
Write-Host "== [1/6] 生成注入块（$Host_ : game $GamePort / http $HttpPort） ==" -ForegroundColor Cyan
$zl = Get-Content $InjectLua -Raw -Encoding UTF8
$zl = [regex]::Replace($zl, 'local HOST  = "[^"]*"',   ("local HOST  = `"{0}`"" -f $Host_))
$zl = [regex]::Replace($zl, 'local PORT  = \d+',       ("local PORT  = {0}" -f $GamePort))
$zl = [regex]::Replace($zl, 'local HPORT = \d+',       ("local HPORT = {0}" -f $HttpPort))
[System.IO.File]::WriteAllText((Join-Path $root $luaTmp), $zl, (New-Object System.Text.UTF8Encoding($false)))
if ($zl -notmatch ('local PORT  = ' + $GamePort)) { throw "注入块 HOST/PORT 替换失败" }
node tools\lua-check\check.js $luaTmp
if ($LASTEXITCODE -ne 0) { throw "替换后的注入块语法不过" }

# ---------------------------------------------------------------- [2] dex + config.luac
Write-Host "== [2/6] DEX 关渠道 SDK + config.luac 翻本地账号登录并注入三区 ==" -ForegroundColor Cyan
python tools\patch_fake_login.py $Src $stage --base ("http://{0}:{1}" -f $Host_, $HttpPort) `
    --lua $luaTmp --flip-platform-login
if ($LASTEXITCODE -ne 0) { throw "patch_fake_login.py 失败 ($LASTEXITCODE)" }
}
else {
  $luaTmp = ''   # 仅校验时不需要注入源
}

# ---------------------------------------------------------------- [3] 校验
Write-Host "== [3/6] 校验产物（Lua 语法 + 关键断言 + dex 单字节） ==" -ForegroundColor Cyan
$py = @'
import re, struct, sys, zipfile
sys.path.insert(0, 'tools')
import patch_fake_login as P

apk = sys.argv[1]
z = zipfile.ZipFile(apk)
t = z.read('assets/src/config.luac').decode('utf-8')
open('patched/_3z_injected_check.lua', 'w', encoding='utf-8').write(t)
bad = 0
def need(cond, msg):
    global bad
    print(('  OK   ' if cond else '  FAIL ') + msg)
    if not cond: bad += 1

print('config.luac = %d bytes' % len(t.encode('utf-8')))
need(re.search(r'IS_PLATFORM_LOGIN\s*=\s*false', t) is not None,
     'IS_PLATFORM_LOGIN = false（渠道登录面板不再创建，改走本地账号登录）')
need('IS_PLATFORM_LOGIN = true' not in t, '不残留 IS_PLATFORM_LOGIN = true')
need('NO_PLAY_VIDEO = true' in t, 'NO_PLAY_VIDEO = true（跳过开场 CG，不弹「无法播放此视频」）')
need('__dsh_refactor_installed' in t, '注入块已写入')
# ★★ 2026-10-17 决定：**客户端不再劫持选区列表**（服务端下发才是本游戏的原生机制）。
#   上一版劫持导致两个真 bug：「登录」点了不动（吞掉 DEFAULE_SERVER_SUCCESS）、
#   选区被钉在错的区（与客户端在途响应互相覆盖）。这条断言把决定锁死，防回退。
need(('M.managerServerListByJsonObj =' not in t) and
     ('M.managerDefualtServerListByJsonObj =' not in t),
     '客户端不再包装选区列表入口（登录/选区交给服务端 + 客户端原生逻辑）')
need(re.search(r'function get_servers_url', t) is not None,
     'get_servers_url 是函数（写成字符串会中断登录界面构建）')
need('绝世唐门' in t, '原有中文（GAME_NAME）未被编码破坏')
# 账号系统（客户端侧）
need('dsh_accounts' in t, '本地账号簿键 dsh_accounts 已写入')
need('账号管理' in t, '账号管理面板已写入')
need('beginThirdPartyLogin' in t, '忘记密码入口已接管（cc.Device.beginThirdPartyLogin）')
need('sdkSwitchAccount' in t, '切换账号入口已接管（登录界面开面板，不再 restart 丢账号）')
need('新建账号' in t, '账号面板有「新建账号」（否则切换账号只能选老号 = 摆设）')
need('__dsh_hooks_ensure' in t, '记账/换号/场景钩子的安装锚点已写入')
# ★ 场景修补（项目已定案：SceneModel 的 map_block/map/scene_info 为 nil ⇒ createMap 不跑）
need('patch_scene_fields' in t and "rawget(m, 'map_block')" in t,
     '进图前补 scene 三处 nil（map_block/map/scene_info）')
need('sceneStart' in t, 'sceneStart 已被包装（建视图前再补一次）')
# 三区定义在**服务端**（客户端只显示服务端下发的列表）
import json as _json
_cfg = _json.load(open('server/config.json', encoding='utf-8'))
_zs = _cfg.get('server_list') or []
_names = [z.get('name') for z in _zs]
_ids = [str(z.get('srv_id')) for z in _zs]
need(_names == ['唐门一区', '昊天二区', '史莱克三区'],
     '服务端三区名称正确：%s' % _names)
need(_ids == ['1', '2', '3'], '服务端三区 srv_id = 1/2/3（实际 %s）' % _ids)

d = z.read('classes.dex')
dx = P.Dex(d)
fidx, _ = dx.field_index(b'Lcom/shiyue/sdk/EWanSdk;', b'is_close')
need(fidx is not None, 'dex: 找到 EwanSdk.is_close 字段')
if fidx is not None:
    idx16 = struct.pack('<H', fidx)
    hits, i = [], 0
    while True:
        i = d.find(b'\x5c', i)
        if i < 0: break
        if i + 4 <= len(d) and d[i+2:i+4] == idx16:
            hits.append(i)
        i += 1
    need(len(hits) == 1, 'dex: is_close 的 iput-boolean 唯一（实际 %d 处）' % len(hits))
    if hits:
        c = d[hits[0]-2:hits[0]]
        need(c[0] == 0x12, 'dex: 前一条是 const/4')
        if c[0] == 0x12:
            need(c[1] >> 4 == 1, 'dex: const/4 字面量 = 1 @0x%X ⇒ is_close = true' % (hits[0]-2))
print('RESULT:', 'PASS' if bad == 0 else 'FAIL(%d)' % bad)
sys.exit(1 if bad else 0)
'@
$py | Out-File -Encoding UTF8 'patched\_3z_verify.py'
python 'patched\_3z_verify.py' $stage
if ($LASTEXITCODE -ne 0) { throw "断言未过" }
node tools\lua-check\check.js patched\_3z_injected_check.lua
if ($LASTEXITCODE -ne 0) { throw "注入后的 config.luac 语法不过（打出去会静默卡死）" }

if ($VerifyOnly) {
  Remove-Item 'patched\_3z_verify.py', 'patched\_3z_injected_check.lua' -Force -ErrorAction SilentlyContinue
  if ($LASTEXITCODE -ne 0) { throw "校验失败" }
  Write-Host "仅校验完成（未重新打包）" -ForegroundColor Green
  exit 0
}

# ---------------------------------------------------------------- [4] zipalign
Write-Host "== [4/6] zipalign ==" -ForegroundColor Cyan
Remove-Item $aligned -Force -ErrorAction SilentlyContinue
& "$BuildTools\zipalign.exe" -f -p 4 $stage $aligned
if ($LASTEXITCODE -ne 0) { throw "zipalign 失败" }

# ---------------------------------------------------------------- [5] 签名
Write-Host "== [5/6] apksigner (v1+v2) ==" -ForegroundColor Cyan
Remove-Item "$Out.idsig" -Force -ErrorAction SilentlyContinue
& "$BuildTools\apksigner.bat" sign --ks $Keystore --ks-pass pass:123456 `
    --key-pass pass:123456 --ks-key-alias dsh --v1-signing-enabled true `
    --v2-signing-enabled true --out $Out $aligned
if ($LASTEXITCODE -ne 0) { throw "apksigner 失败" }
& "$BuildTools\apksigner.bat" verify $Out

# ---------------------------------------------------------------- [6] 安装（可选）
if ($Install) {
  Write-Host "== [6/6] 安装到 $Device ==" -ForegroundColor Cyan
  & adb -s $Device shell am force-stop com.shiyue.dldl.ewan.baidu2 | Out-Null
  & adb -s $Device install -r $Out
  if ($LASTEXITCODE -ne 0) { throw "adb install 失败" }
}

Remove-Item $stage, $aligned, $luaTmp, 'patched\_3z_verify.py', 'patched\_3z_injected_check.lua' `
    -Force -ErrorAction SilentlyContinue

$dt = (Get-Date) - $t0
Write-Host ("完成：{0}  用时 {1:mm\:ss}" -f $Out, $dt) -ForegroundColor Green
Write-Host ("SHA-256: {0}" -f (Get-FileHash $Out -Algorithm SHA256).Hash)
