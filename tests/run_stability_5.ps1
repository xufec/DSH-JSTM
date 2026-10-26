# =====================================================================
# 阶段 3 · 第一阶段：连续 5 次"进入地图"稳定性测试
# 每次记录：是否进图 / 进图耗时(tick) / 闪退 / Lua 错误 / 网络错误 /
#           自动断线 / 角色状态 / 收到的命令集合
# 判据：探针 state 上报里的 scene=table:_0x... 表示 getScene() 已返回对象
# =====================================================================
$ErrorActionPreference = 'Continue'
$d = '127.0.0.1:16384'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$out = 'tests\1.4.9_stability_raw.txt'
Remove-Item $out -ErrorAction SilentlyContinue

for ($i = 1; $i -le 5; $i++) {
  Write-Host "===== RUN $i ====="
  Remove-Item .\server\logs\http.log, .\server\logs\tcp.log -ErrorAction SilentlyContinue
  adb -s $d shell am force-stop com.shiyue.dldl.ewan.qihoo | Out-Null
  adb -s $d logcat -c
  Start-Sleep -Seconds 2
  $t0 = Get-Date
  adb -s $d shell am start -n com.shiyue.dldl.ewan.qihoo/org.cocos2dx.lua.AppActivity | Out-Null

  # 轮询探针 state，抓"第一次出现 scene=table"的时刻
  $firstSceneTick = $null
  $sceneOk = $false
  for ($k = 0; $k -lt 40; $k++) {
    Start-Sleep -Seconds 5
    $lines = Select-String -Path .\server\logs\http.log -Pattern 't=state' -ErrorAction SilentlyContinue
    if (-not $lines) { continue }
    $hit = $lines | Where-Object { $_.Line -match 'scene_table' } | Select-Object -First 1
    if ($hit) {
      $sceneOk = $true
      if ($hit.Line -match 'state&v=t_(\d+)_') { $firstSceneTick = [int]$Matches[1] }
      break
    }
    if ($k -ge 20) { break }   # 100 秒还没进图就判失败
  }
  $elapsed = [int]((Get-Date) - $t0).TotalSeconds

  Start-Sleep -Seconds 20   # 进图后再静置观察
  adb -s $d logcat -d > "logs\1.4.9\run${i}_logcat.log" 2>&1
  Copy-Item .\server\logs\tcp.log "logs\1.4.9\run${i}_tcp.log" -Force -ErrorAction SilentlyContinue
  adb -s $d shell screencap -p /sdcard/_r$i.png | Out-Null
  adb -s $d pull /sdcard/_r$i.png "shots\stage3_run$i.png" 2>&1 | Out-Null

  $alive = (adb -s $d shell ps -A 2>$null | Select-String 'dldl.ewan.qihoo$').Count -gt 0
  $fatal = (Select-String -Path "logs\1.4.9\run${i}_logcat.log" -Pattern 'FATAL EXCEPTION|AndroidRuntime.*RuntimeException' -ErrorAction SilentlyContinue).Count
  $luaErr = (Select-String -Path "logs\1.4.9\run${i}_logcat.log" -Pattern 'Call Function\[stack top\]|attempt to (call|index)' -ErrorAction SilentlyContinue).Count
  $closed = (Select-String -Path .\server\logs\tcp.log -Pattern 'closed' -ErrorAction SilentlyContinue).Count
  $recvN = (Select-String -Path .\server\logs\http.log -Pattern 'recvHook&v=n_' -ErrorAction SilentlyContinue).Count
  $cmds = (Select-String -Path .\server\logs\tcp.log -Pattern '>> cmd=' -ErrorAction SilentlyContinue |
           ForEach-Object { ($_.Line -split 'cmd=')[1] } | ForEach-Object { ($_ -split ' ')[0] } |
           Sort-Object -Unique) -join ','

  $line = "RUN $i : sceneOk=$sceneOk firstSceneTick=$firstSceneTick elapsed=${elapsed}s alive=$alive fatal=$fatal luaErr=$luaErr tcpClosed=$closed recv=$recvN cmds=[$cmds]"
  Write-Host $line
  Add-Content -Path $out -Value $line
}
Write-Host "DONE"
