# 1.4.9 私服 —— 游戏服务器「可靠重启」脚本
#
# 为什么需要它（本次踩过的坑）：
#   用 harness 的后台 job 起服务端时，PowerShell 包装进程一旦结束，
#   job 会被报成 `finished exit code 1`，而 python 子进程会变成**孤儿进程继续跑**。
#   结果是：端口看着有服务，但你分不清那是「这次起的」还是「上一次遗留的」，
#   反复重启就会留下多个 mock_server 实例互相抢 9000/8080。
#
#   本脚本改为 **Start-Process 分离启动**：
#     - 先杀掉所有 mock_server 进程（含孤儿）
#     - 确认 9000/8080 已释放
#     - 分离启动一个新的（输出重定向到 server\logs\stdout.log / stderr.log）
#     - 自动冒烟测试（HTTP + TCP 1199 心跳往返）
#
# 用法：
#   pwsh tools\restart_server.ps1
#   pwsh tools\restart_server.ps1 -KeepLogs      # 不轮转 tcp.log / http.log
#   pwsh tools\restart_server.ps1 -NoSmoke       # 跳过冒烟测试
[CmdletBinding()]
param(
  [switch]$KeepLogs,
  [switch]$NoSmoke,
  [int]$TimeoutSec = 25
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== [1/5] 停止所有 mock_server 进程 ==" -ForegroundColor Cyan
$procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
         Where-Object { $_.CommandLine -like '*mock_server.py*' }
if ($procs) {
  foreach ($p in $procs) { Write-Host ("   kill PID {0}" -f $p.ProcessId) }
  $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} else {
  Write-Host "   （没有在跑的 mock_server）"
}

Write-Host "== [2/5] 等待端口释放 ==" -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds($TimeoutSec)
do {
  Start-Sleep -Milliseconds 500
  $busy = Get-NetTCPConnection -State Listen -LocalPort 9000,8080 -ErrorAction SilentlyContinue
} while ($busy -and (Get-Date) -lt $deadline)
if ($busy) {
  Write-Host "   !! 端口仍被占用：" -ForegroundColor Red
  $busy | Select-Object LocalPort, OwningProcess | Format-Table -AutoSize | Out-Host
  throw "9000/8080 未释放，无法重启"
}
Write-Host "   9000/8080 已释放"

Write-Host "== [3/5] 语法/配置自检 ==" -ForegroundColor Cyan
python -c "import ast;ast.parse(open(r'server/mock_server.py',encoding='utf-8').read());ast.parse(open(r'server/battle.py',encoding='utf-8').read());print('   server syntax OK')"
if ($LASTEXITCODE -ne 0) { throw "server 源码语法错误" }
python -c "import json;d=json.load(open(r'server/config.json',encoding='utf-8'));print('   config OK | battle_round_interval=%s mission_auto_progress=%s mons=%d' % (d.get('battle_round_interval'), d.get('mission_auto_progress'), len(d.get('mons') or [])))"
if ($LASTEXITCODE -ne 0) { throw "config.json 解析失败" }

if (-not $KeepLogs) {
  Write-Host "   轮转日志 tcp.log / http.log"
  Move-Item server\logs\tcp.log  server\logs\tcp_prevR.log  -Force -ErrorAction SilentlyContinue
  Move-Item server\logs\http.log server\logs\http_prevR.log -Force -ErrorAction SilentlyContinue
}

Write-Host "== [4/5] 分离启动服务端 ==" -ForegroundColor Cyan
# ⚠ 这里**不能**用 Start-Process：
#   Start-Process 会让子进程继承父进程的控制台/重定向句柄，
#   于是"调用方"（例如 dsh 的 pwsh 工具）会一直等这棵进程树，
#   表现为命令挂住直到超时，超时被杀时连新起的服务端一起带走（已实测踩过）。
#
# 改用 WMI 创建进程：父进程是 WmiPrvSE，**不继承任何句柄**，
# 所以调用方立刻返回，服务端独立存活。
#
# ★ C3.1 修复（本机失效根因）：
#   `python` 在本环境是 **Alias**（指向 sandbox_runtime\...\python\python.exe，
#   路径含空格 "User Data"），Alias 的 .Source 为**空**。
#   原写法 `(Get-Command python).Source` 取到空串 ⇒ WMI cmdline 拼成
#     cmd.exe /c "" "" "...\mock_server.py" 1>"..." 2>"...""
#   cmd 把 `""` 当可执行文件 ⇒ `'""' 不是内部或外部命令`。
#   修法：Alias 时取 .Definition（真实 exe 路径），其余取 .Source。
#   （实测：取到真实路径后，cmd /c 嵌套引号对含空格路径工作正常。）
$pyCmd = Get-Command python
$py = if ($pyCmd.CommandType -eq 'Alias') { $pyCmd.Definition } else { $pyCmd.Source }
if (-not $py -or -not (Test-Path $py)) { throw "找不到 python 可执行文件（Get-Command=$($pyCmd.CommandType)）" }
$logOut = Join-Path $root 'server\logs\stdout.log'
$logErr = Join-Path $root 'server\logs\stderr.log'
$cmdline = 'cmd.exe /c ""{0}" "{1}" 1>"{2}" 2>"{3}""' -f `
  $py, (Join-Path $root 'server\mock_server.py'), $logOut, $logErr

$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create `
       -Arguments @{ CommandLine = $cmdline } -ErrorAction Stop
if ($r.ReturnValue -ne 0) { throw "WMI 创建进程失败，ReturnValue=$($r.ReturnValue)" }
Write-Host ("   WMI 已创建进程 PID {0}" -f $r.ProcessId)

$deadline = (Get-Date).AddSeconds($TimeoutSec)
do {
  Start-Sleep -Milliseconds 500
  $listen = Get-NetTCPConnection -State Listen -LocalPort 9000,8080 -ErrorAction SilentlyContinue
} while (-not $listen -and (Get-Date) -lt $deadline)
if (-not $listen) {
  Write-Host "   !! 启动超时，stderr：" -ForegroundColor Red
  Get-Content $logErr -Tail 20 -Encoding UTF8 -ErrorAction SilentlyContinue | Out-Host
  throw "启动超时：9000/8080 未监听"
}

$pid0 = ($listen | Select-Object -First 1).OwningProcess
Write-Host ("   已启动 PID {0}，监听 {1}" -f $pid0,
  (($listen | Select-Object -ExpandProperty LocalPort | Sort-Object) -join ','))

Write-Host "== [5/5] 冒烟测试 ==" -ForegroundColor Cyan
if ($NoSmoke) {
  Write-Host "   （-NoSmoke 跳过）"
} else {
  python tools\smoke_test_server.py
  if ($LASTEXITCODE -ne 0) { throw "冒烟测试失败" }
}

Write-Host "`n服务端已就绪 ✅  PID=$pid0" -ForegroundColor Green
Write-Host "  日志: server\logs\server.log, tcp.log, http.log, stdout.log, stderr.log"
Get-Content server\logs\server.log -Tail 6 -Encoding UTF8 | ForEach-Object { "  $_" }
