# 1.4.9 伪登录探针版 APK 一键构建 + 安装
#
# 固定以 anzbao\jstm.apk（1.4.9）为源，注入 server\dsh_fake_login.lua，
# 产出 patched\jstm_fakelogin.apk 并安装到模拟器。
#
# 用法：
#   pwsh tools\build_fakelogin.ps1
#   pwsh tools\build_fakelogin.ps1 -NoInstall
[CmdletBinding()]
param(
  [string]$Src       = 'anzbao\jstm.apk',
  [string]$Lua       = 'server\dsh_fake_login.lua',
  [string]$Base      = 'http://10.0.2.2:8080',
  [string]$Raw       = 'patched\jstm_fakelogin_raw.apk',
  [string]$Aligned   = 'patched\jstm_fakelogin_aligned.apk',
  [string]$Out       = 'patched\jstm_fakelogin.apk',
  [string]$BuildTools= 'D:\Android\SDK\build-tools\34.0.0',
  [string]$Keystore  = 'patched\dsh.keystore',
  [string]$Device    = '127.0.0.1:16384',
  [switch]$NoInstall,
  [switch]$NoSign
)

$ErrorActionPreference = 'Stop'
$t0 = Get-Date

# ★ [0/4] Lua 语法门禁 —— 2026-10-01 实踩：探针块里我误把 `return` 写在语句中间，
#   `tools/lua-check/check.js` 明确报 FAIL，但本脚本**照样打了包、装到机器上**
#   ⇒ 客户端加载的是坏 Lua（整段探针失效，而表面上看不出问题）。
#   本项目 HANDOVER 把 lua-check 写成"硬闸门"，但直到今天它并没有接在打包链上。
Write-Host "== [0/4] Lua 语法门禁 (lua-check) ==" -ForegroundColor Cyan
node tools\lua-check\check.js $Lua
if ($LASTEXITCODE -ne 0) { throw "lua-check 门禁未过：$Lua（已中止打包，绝不装坏 Lua）" }

Write-Host "== [1/4] 注入 Lua 探针 ==" -ForegroundColor Cyan
python tools\patch_fake_login.py $Src $Raw --base $Base --lua $Lua
if ($LASTEXITCODE -ne 0) { throw "patch_fake_login.py 失败 ($LASTEXITCODE)" }

Write-Host "== [2/4] zipalign ==" -ForegroundColor Cyan
& "$BuildTools\zipalign.exe" -f -p 4 $Raw $Aligned
if ($LASTEXITCODE -ne 0) { throw "zipalign 失败 ($LASTEXITCODE)" }

if ($NoSign) {
  Write-Host "已跳过签名（-NoSign），产物：$Aligned"
  exit 0
}

Write-Host "== [3/4] 签名 ==" -ForegroundColor Cyan
# 用 --out 而不是「先 Copy 再原地签」：原地签时 apksigner 最后会把临时文件
# move 覆盖目标，而 Windows 上刚创建的 $Out 常被杀软/索引占用
# → FileSystemException: 另一个程序正在使用此文件（实测踩过）。
Remove-Item "$Out.idsig" -Force -ErrorAction SilentlyContinue
& "$BuildTools\apksigner.bat" sign --ks $Keystore --ks-pass pass:123456 `
    --key-pass pass:123456 --ks-key-alias dsh --out $Out $Aligned
if ($LASTEXITCODE -ne 0) { throw "apksigner 失败 ($LASTEXITCODE)" }

& "$BuildTools\apksigner.bat" verify $Out | Out-Host

if (-not $NoInstall) {
  Write-Host "== [4/4] 安装到 $Device ==" -ForegroundColor Cyan
  & adb -s $Device shell am force-stop com.shiyue.dldl.ewan.qihoo | Out-Null
  & adb -s $Device install -r $Out
  if ($LASTEXITCODE -ne 0) { throw "adb install 失败 ($LASTEXITCODE)" }
  & adb -s $Device shell monkey -p com.shiyue.dldl.ewan.qihoo -c android.intent.category.LAUNCHER 1 | Out-Null
}

$dt = (Get-Date) - $t0
Write-Host ("完成：{0}  用时 {1:mm\:ss}" -f $Out, $dt) -ForegroundColor Green
Write-Host ("SHA-256: {0}" -f (Get-FileHash $Out -Algorithm SHA256).Hash)
