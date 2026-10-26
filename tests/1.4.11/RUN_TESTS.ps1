# ============================================================================
#  tests/1.4.11/RUN_TESTS.ps1 —— 一键回归（1.4.11 复原工程）
#
#  用法：
#     pwsh -File tests/1.4.11/RUN_TESTS.ps1                 # 静态 + 客户端（用现有服务端）
#     pwsh -File tests/1.4.11/RUN_TESTS.ps1 -Static         # 只跑静态门禁（不需服务端）
#     pwsh -File tests/1.4.11/RUN_TESTS.ps1 -SelfStart      # ★ 自启测试服务端（答题项不再 SKIP）
#
#  -SelfStart 行为（会**短暂停掉**当前服务端，跑完自动恢复为生产模式）：
#     1) 记录 9000 上是否已有服务端
#     2) 停掉它 → 以 $env:DSH_ANSWER_OPEN='1' 启动测试服务端
#     3) 跑全部客户端回归（答题项因时段放开而可跑通）
#     4) 停掉测试服务端 → 若步骤 1 有服务端，则**恢复为生产模式**（无覆盖变量）
#
#  覆盖：miniloop ×3 / py_compile / shadow_lint / 答题 / 开服成长计划 / 刮刮乐 / 好友 / status
# ============================================================================
param([switch]$Static, [switch]$SelfStart)

$ErrorActionPreference = 'Continue'
$py = 'D:\Python\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root

$fail = 0
function Step([string]$name, [scriptblock]$body) {
    Write-Host ''
    Write-Host ("=== {0} ===" -f $name)
    try { & $body } catch { Write-Host ("  !! {0}" -f $_); $script:fail++ }
}
function Port-Up([int]$port) {
    try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1', $port); $c.Close(); return $true }
    catch { return $false }
}
function Stop-9000 {
    $conn = Get-NetTCPConnection -LocalPort 9000 -State Listen -ErrorAction SilentlyContinue
    foreach ($c in @($conn)) {
        if ($c -and $c.OwningProcess) { try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop } catch {} }
    }
    Start-Sleep -Seconds 2
}
function Start-Server([bool]$withOverride) {
    $env:DSH_ANSWER_OPEN = if ($withOverride) { '1' } else { $null }
    if ($withOverride) {
        Start-Process -FilePath $py -ArgumentList 'server/mock_server.py', '--http', '8080', '--game', '9000' `
            -WorkingDirectory $root -Environment @{ DSH_ANSWER_OPEN = '1' } -WindowStyle Hidden
    }
    else {
        Start-Process -FilePath $py -ArgumentList 'server/mock_server.py', '--http', '8080', '--game', '9000' `
            -WorkingDirectory $root -WindowStyle Hidden
    }
    $env:DSH_ANSWER_OPEN = $null
    for ($i = 0; $i -lt 20; $i++) { Start-Sleep -Seconds 1; if (Port-Up 9000) { return $true } }
    return $false
}

Write-Host ("repo   = {0}" -f $root)
Write-Host ("python = {0}" -f $py)

# ---------------- 静态门禁 ----------------
Step 'miniloop selftest ×3' {
    for ($i = 1; $i -le 3; $i++) {
        $o = & $py server/minloop/selftest.py 2>&1 | Select-String '检查项'
        Write-Host ("  run{0}: {1}" -f $i, ($o.Line -join ' '))
        if (($o.Line -join ' ') -notmatch '通过 145，失败 0') { $script:fail++ }
    }
}
Step 'py_compile' {
    & $py -m py_compile server/mock_server.py server/answer/service.py server/answer/handler.py `
        server/growth_target/service.py server/growth_target/handler.py `
        server/scratch/service.py server/scratch/handler.py `
        server/friend/service.py server/friend/handler.py
    if ($LASTEXITCODE -eq 0) { Write-Host '  OK' } else { Write-Host '  FAILED'; $script:fail++ }
}
Step 'shadow_lint' {
    $o = & $py tools/lint_dispatch_shadow.py 2>&1 | Select-Object -Last 3
    Write-Host ($o -join "`n")
    if (($o -join ' ') -notmatch '无分发遮蔽') { $script:fail++ }
}

if ($Static) {
    Write-Host ''
    Write-Host ("==== 静态门禁失败项 = {0} ====" -f $fail)
    exit $(if ($fail) { 1 } else { 0 })
}

# ---------------- 客户端回归 ----------------
$hadServer = Port-Up 9000
$startedByUs = $false
if ($SelfStart) {
    if ($hadServer) { Write-Host ''; Write-Host '（-SelfStart：先停掉当前服务端，稍后恢复为生产模式）' ; Stop-9000 }
    Write-Host ''
    Write-Host '启动测试服务端（DSH_ANSWER_OPEN=1）…'
    $startedByUs = Start-Server $true
    if (-not $startedByUs) { Write-Host '!! 测试服务端启动失败'; $fail++ }
}
elseif (-not $hadServer) {
    Write-Host ''
    Write-Host '!! 9000 无服务端 ⇒ 跳过客户端回归。可用 -SelfStart 自动启动：'
    Write-Host '     pwsh -File tests/1.4.11/RUN_TESTS.ps1 -SelfStart'
    Write-Host ''
    Write-Host ("==== 失败项 = {0} ====" -f $fail)
    exit $(if ($fail) { 1 } else { 0 })
}

if (Port-Up 9000) {
    Step '答题 16100~16103' {
        $o = & $py tools/test_answer.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail)
        if ($tail -notmatch 'ALL PASS') {
            if (($o -join ' ') -match '不在活动时间') { Write-Host '  SKIP（时段外；建议用 -SelfStart）' }
            else { $script:fail++ }
        }
    }
    Step '开服成长计划 30500~30502' {
        $o = & $py tools/test_growth_target.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '刮刮乐 16651/16652' {
        $o = & $py tools/test_scratch.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '好友 13300/13321/13303/13305/13307/13323' {
        $o = & $py tools/test_friend.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '活动族 16605/10923/16602/16664' {
        $o = & $py tools/test_activity_family.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '零散修复 14901/16900/GM setcharge' {
        $o = & $py tools/test_misc_fixes.py --port 9000 --http 8080 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '头像/伙伴/回包修复 10325/10327/10341/11215/13036' {
        $o = & $py tools/test_avatar_partner_fixes.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '充值 13901/13902（点档位直接得钻石）' {
        $o = & $py tools/test_charge_13902.py --port 9000 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '累计充值 16900.status / 16901 领取' {
        $o = & $py tools/_verify_16900_status.py 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '每日充值 17100（真值 + 当天档位）' {
        $o = & $py tools/_verify_17100.py 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
    }
    Step '充值后推送 + VIP 升级 13902' {
        $o = & $py tools/_verify_13902_push_vip.py 2>&1
        $tail = ($o | Select-Object -Last 2) -join ' '
        Write-Host ("  {0}" -f $tail); if ($tail -notmatch 'ALL PASS') { $script:fail++ }
        & $py tools/_cleanup_charge_residue.py 2>&1 | Out-Null
    }
    Step '/DSH_ADMIN/status 基线' {
        try {
            $j = (Invoke-WebRequest 'http://127.0.0.1:8080/DSH_ADMIN/status' -TimeoutSec 8).Content | ConvertFrom-Json
            Write-Host ("  lv={0} scene={1} gold={2}" -f $j.role.level, $j.role.scene_id, $j.assets.gold)
            if ($j.role.level -ne 70 -or $j.role.scene_id -ne 10001) { $script:fail++ }
        } catch { Write-Host '  ERR'; $script:fail++ }
    }
}

# ---------------- 恢复生产模式 ----------------
if ($SelfStart) {
    Write-Host ''
    Write-Host '（-SelfStart：停测试服务端'
    Stop-9000
    if ($hadServer) {
        Write-Host ' → 恢复生产模式服务端）'
        if (-not (Start-Server $false)) { Write-Host '!! 生产服务端恢复失败'; $fail++ }
    }
    else { Write-Host ' → 原本无服务端，不恢复）' }
}

Write-Host ''
Write-Host ("==== 失败项 = {0} ====" -f $fail)
exit $(if ($fail) { 1 } else { 0 })
