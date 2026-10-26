<#
.SYNOPSIS
  改包 → 签名 一键流水线（《绝世唐门》私服 / 单机版）。

.DESCRIPTION
  包装 tools/patch_apk.py 与 Android SDK 的 zipalign / apksigner，
  产出可直接 adb install 的 APK。

  两种模式：
    * 单机版（默认）：注入内置 Lua 服务端，网关指向本机回环 127.0.0.1。
    * 联调版（-NoEmbedded）：不注入内置服务端，网关指向 PC，配合
      server/mock_server.py 抓包。

.EXAMPLE
  # 单机版，内置服务端监听 18080，客户端连 127.0.0.1:18080
  pwsh tools/build_apk.ps1 -Out patched\jstm_solo.apk

.EXAMPLE
  # 联调版：客户端连 PC 的 10.0.0.2:8080
  pwsh tools/build_apk.ps1 -NoEmbedded -Host 10.0.0.2 -Out patched\jstm_pc.apk
#>
[CmdletBinding()]
param(
  [string]$Src = 'anzbao\jstm_142165.apk',
  [string]$Out = 'patched\jstm_solo.apk',
  [string]$Host_ = '127.0.0.1',
  [int]$Port = 18080,
  [int]$LocalPort = 18080,
  [int]$GamePort = 19000,
  [string]$ReportUrl = '',
  [switch]$NoEmbedded,
  [switch]$KeepPlatformLogin,
  [switch]$NoInject,
  [switch]$ObsOnly,
  [switch]$SkipSdkInit,
  [string]$BuildTools = 'D:\Android\SDK\build-tools\34.0.0',
  [string]$Keystore = 'patched\dsh.keystore',
  [string]$KsPass = '123456',
  [string]$KeyAlias = 'dsh',
  [string]$KeyPass = '123456'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 单机模式下客户端必须连到内置服务端监听的同一个端口，否则必然 connection refused
if (-not $NoEmbedded -and $Port -ne $LocalPort) {
  Write-Warning "单机模式：--Port($Port) 与 --LocalPort($LocalPort) 不一致，客户端会连不上内置服务端。已按 LocalPort 对齐。"
  $Port = $LocalPort
}

Write-Host "== [1/5] dex patch (skip dead SDK init) ==" -ForegroundColor Cyan
# 单机版必须跳过 ewan SuperSDK 的初始化：它的服务器已死，初始化失败会弹出
# "初始化失败,请检查网络" 阻塞对话框，且 Lua 侧会被整体卡住（实测连
# ActionManager 心跳都停）。补丁把 EwanSdk.onCollectData 里那次
# SuperPlatform.init() 调用改成 no-op（SB 跳过 2 个码元），
# SuperPlatform.onCreate 已经先执行过，SDK 对象仍可用。
if ($SkipSdkInit) {
  # ⚠ 中间产物必须和最终产物分开：patch_apk.py 会重写 $Out，
  #   如果这里也写 $Out，下一步就会把 DEX 补丁覆盖掉（踩过一次）。
  $dexStage = [System.IO.Path]::ChangeExtension($Out, $null) + '.dexpatched.apk'
  python tools/patch_dex_skip_sdkinit.py $Src $dexStage
  if ($LASTEXITCODE -ne 0) { throw "patch_dex_skip_sdkinit.py failed ($LASTEXITCODE)" }
  $Src = $dexStage
} else {
  Write-Host "  (skipped: -SkipSdkInit not set)"
}

Write-Host "== [2/5] patch (lan/urls/lua injection) ==" -ForegroundColor Cyan
# 参数数组必须在 DEX 补丁**之后**再拼，否则 $Src 还是原始 APK（踩过：
# PowerShell 数组复制的是当时的值，DEX 补丁因此被静默丢弃）。
$py = @('tools/patch_apk.py', $Src, $Out, '--host', $Host_, '--port', "$Port",
        '--local-port', "$LocalPort", '--game-port', "$GamePort")
if ($ReportUrl) { $py += @('--report-url', $ReportUrl) }
if ($NoEmbedded) { $py += '--no-embedded' }
if ($KeepPlatformLogin) { $py += '--keep-platform-login' }
if ($NoInject) { $py += '--no-inject' }
if ($ObsOnly) { $py += '--obs-only' }
python @py
if ($LASTEXITCODE -ne 0) { throw "patch_apk.py failed ($LASTEXITCODE)" }

Write-Host "== [3/5] verify injected Lua ==" -ForegroundColor Cyan
# 这道闸门是必需的：注入块语法一旦有问题，config chunk 编译失败、
# 游戏静默卡住（没有明显报错），所以打包后必须先从 APK 里取回来验证。
$env:PYTHONIOENCODING = 'utf-8'
python tools/verify_injected_lua.py $Out
if ($LASTEXITCODE -ne 0) { throw "verify_injected_lua.py failed ($LASTEXITCODE)" }

$aligned = [System.IO.Path]::ChangeExtension($Out, $null) + '.aligned.apk'
Write-Host "== [4/5] zipalign ==" -ForegroundColor Cyan
& "$BuildTools\zipalign.exe" -f -p 4 $Out $aligned
if ($LASTEXITCODE -ne 0) { throw "zipalign failed ($LASTEXITCODE)" }

Write-Host "== [5/5] apksigner ==" -ForegroundColor Cyan
& "$BuildTools\apksigner.bat" sign --ks $Keystore --ks-pass "pass:$KsPass" `
    --ks-key-alias $KeyAlias --key-pass "pass:$KeyPass" `
    --v1-signing-enabled true --v2-signing-enabled true $aligned
if ($LASTEXITCODE -ne 0) { throw "apksigner failed ($LASTEXITCODE)" }

& "$BuildTools\apksigner.bat" verify --print-certs $aligned | Select-Object -First 3

Remove-Item $Out -ErrorAction SilentlyContinue
Move-Item $aligned $Out -Force
Write-Host "== done -> $Out ==" -ForegroundColor Green
Write-Host "install: adb install -r $Out"

