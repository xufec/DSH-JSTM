# ============================================================================
#  绝世唐门 私服管理台（在线热改 + 立即推送，无需重登）
#
#  依赖：server/mock_server.py 的 /DSH_ADMIN/* 接口（须先启动服务端）
#  字段依据（均来自 1.4.9 原版配置，非猜测）：
#      钻石   = gold   (code 1)
#      金魂币 = coupon (code 3)
#      银魂币 = coin   (code 2)
#  ★ 定论依据（2026-09-17，**确定性读数**）：
#      将 coin=11111 / coupon=22222 / gold=33333 推送后，游戏内读到
#        「金魂币」=22222、「银魂币」=11111 ⇒ 上式成立。
#
#  ★ 2026-09-18 扩充（按用户要求「读取游戏中的各种资源目录 → 增加功能 → 热修改」）：
#      新增：状态总览 / 物品检索 / 发物品 / 开礼包 / 穿装备 / 卸装备 /
#            伙伴 / 聚宝盆奖池 / 任务链头 / 重置各囊 / 热重载配置表
#
#  ★ 编码：本文件**必须**为 UTF-8 with BOM，否则 Windows PowerShell 5.1
#     会按 GBK 解析 ⇒ 中文乱码 ⇒ 引号被吞 ⇒ 语法错误（2026-09-18 实际发生过）。
# ============================================================================

$ErrorActionPreference = 'Continue'
$Admin = 'http://127.0.0.1:8080/DSH_ADMIN'

function Api([string]$path) {
    try {
        return (Invoke-WebRequest -UseBasicParsing -TimeoutSec 10 -Uri ($Admin + $path)).Content
    } catch {
        return '{"ok": false, "error": "服务端未响应（请先运行 server/mock_server.py）"}'
    }
}

function Show-State([string]$title) {
    $r = Api '/status'
    Write-Host ''
    Write-Host "  --- $title ---"
    try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; return }
    if (-not $j.ok) { Write-Host "    $r"; return }
    $role = $j.role; $a = $j.assets
    Write-Host ("    角色    {0}   等级 {1}   经验 {2}" -f $role.name, $role.level, $role.exp)
    Write-Host ("    钻石    {0}" -f $a.gold)
    Write-Host ("    金魂币  {0}" -f $a.coupon)
    Write-Host ("    银魂币  {0}" -f $a.coin)
    Write-Host ("    背包    {0} 件" -f @($j.bag).Count)
    Write-Host ("    装备    {0} 件" -f @($j.equip).Count)
    Write-Host ("    仓库    {0} 件" -f @($j.store).Count)
    if (@($j.equip).Count -gt 0) {
        $eq = (@($j.equip) | ForEach-Object { "slot$($_.slot)=$($_.bid)" }) -join '  '
        Write-Host ("            {0}" -f $eq)
    }
    Write-Host ("    礼包已领 {0}" -f (@($j.levgift_got) -join ','))
}

function Ask([string]$prompt, [string]$def = '') {
    if ($def -ne '') { Write-Host -NoNewline "  $prompt [$def]: " }
    else { Write-Host -NoNewline "  ${prompt}: " }
    $v = Read-Host
    if ([string]::IsNullOrWhiteSpace($v)) { return $def }
    return $v
}

function Pause2() {
    Write-Host ''
    Write-Host -NoNewline '  回车继续'
    Read-Host | Out-Null
}

function Show-Menu() {
    Clear-Host
    Write-Host '============================================================'
    Write-Host '   绝世唐门 私服管理台   （在线热改 + 立即推送，无需重登）'
    Write-Host '============================================================'
    Show-State '当前状态'
    Write-Host ''
    Write-Host '  [角色]'
    Write-Host '  [1] 设置等级      [2] 设置钻石      [3] 设置金魂币    [4] 设置银魂币'
    Write-Host '  [5] 钻石 +增量    [6] 金魂币 +增量  [7] 银魂币 +增量'
    Write-Host '  [8] 一键全满（等级 200 + 三种货币 999999）'
    Write-Host ''
    Write-Host '  [物品]'
    Write-Host '  [10] 检索物品（按名字找 bid）'
    Write-Host '  [11] 发物品（bid + 数量，立即推送背包）'
    Write-Host '  [12] 开礼包（按礼包 bid，直接发内容）'
    Write-Host ''
    Write-Host '  [装备]'
    Write-Host '  [20] 穿装备（按 bid，自动按部位定槽）'
    Write-Host '  [21] 卸装备（按槽位，退回背包）'
    Write-Host ''
    Write-Host '  [伙伴 / 聚宝盆]'
    Write-Host '  [30] 设置伙伴（bids 逗号分隔）'
    Write-Host '  [31] 设置聚宝盆奖池（bid:权重, bid:权重, ...）'
    Write-Host ''
    Write-Host '  [任务]'
    Write-Host '  [40] 设置任务链头（把指定任务设为进行中）'
    Write-Host ''
    Write-Host '  [资源表]  ★ 直接读取 APK 里的 347 张配置表'
    Write-Host '  [70] 列出全部配置表'
    Write-Host '  [71] 读某张表（可按关键词搜）'
    Write-Host '  [72] 搜物品 / [73] 搜 NPC / [74] 搜 伙伴'
    Write-Host ''
    Write-Host '  [重置 / 热重载]'
    Write-Host '  [50] 重置背包   [51] 重置装备   [52] 重置仓库'
    Write-Host '  [53] 重置任务   [54] 重置礼包领取   [55] 全部重置'
    Write-Host '  [60] 热重载配置表（物品 / 商城 / 礼包 / 任务 / 主配置）'
    Write-Host ''
    Write-Host '  [0] 退出'
    Write-Host ''
}

while ($true) {
    Show-Menu
    Write-Host -NoNewline '  请选择: '
    $c = Read-Host

    switch ($c) {
        '1'  { $v = Ask '等级';          Api "/setlevel?lev=$v" | Out-Null }
        '2'  { $v = Ask '钻石';          Api "/setassets?gold=$v" | Out-Null }
        '3'  { $v = Ask '金魂币';        Api "/setassets?coupon=$v" | Out-Null }
        '4'  { $v = Ask '银魂币';        Api "/setassets?coin=$v" | Out-Null }
        '5'  { $v = Ask '钻石 +';        Api "/setassets?mode=add&gold=$v" | Out-Null }
        '6'  { $v = Ask '金魂币 +';      Api "/setassets?mode=add&coupon=$v" | Out-Null }
        '7'  { $v = Ask '银魂币 +';      Api "/setassets?mode=add&coin=$v" | Out-Null }
        '8'  { Api '/setlevel?lev=200' | Out-Null
               Api '/setassets?gold=999999&coupon=999999&coin=999999' | Out-Null }

        '10' {
            $kw = Ask '物品名关键词（如 长枪 / 速度符）'
            $enc = [System.Uri]::EscapeDataString($kw)
            $r = Api "/listitems?kw=$enc&limit=30"
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    命中 {0} 条：" -f $j.n)
            foreach ($it in $j.items) {
                Write-Host ("      bid={0,-7} type={1,-5} {2}" -f $it.bid, $it.type, $it.name)
            }
            Pause2
        }
        '11' {
            $b = Ask '物品 bid'; $n = Ask '数量' '1'
            Write-Host ("    " + (Api "/giveitem?bid=$b&num=$n")); Pause2
        }
        '12' {
            $b = Ask '礼包 bid'; $n = Ask '个数' '1'
            Write-Host ("    " + (Api "/givegift?bid=$b&num=$n")); Pause2
        }

        '20' {
            $b = Ask '装备 bid（如 40001 见习长枪）'
            Write-Host ("    " + (Api "/setequip?bid=$b")); Pause2
        }
        '21' {
            $s = Ask '槽位号'
            Write-Host ("    " + (Api "/unequip?slot=$s")); Pause2
        }

        '30' {
            $b = Ask '伙伴 bid（逗号分隔）'
            Write-Host ("    " + (Api "/setheros?bids=$b")); Pause2
        }
        '31' {
            $pool = Ask '奖池 bid:权重（逗号分隔）'
            Write-Host ("    " + (Api "/setjubaopen?pool=$pool")); Pause2
        }

        '40' {
            $b = Ask '任务 bid（如 10010）'
            Write-Host ("    " + (Api "/setmissions?bid=$b")); Pause2
        }

        '50' { Api '/reset?what=bag'     | Out-Null }
        '51' { Api '/reset?what=equip'   | Out-Null }
        '52' { Api '/reset?what=store'   | Out-Null }
        '53' { Api '/reset?what=mission' | Out-Null }
        '54' { Api '/reset?what=levgift' | Out-Null }
        '55' { Api '/reset?what=all'     | Out-Null }
        '70' {
            $r = Api '/cfglist'
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    共 {0} 张配置表（按大小排序）：" -f $j.n)
            foreach ($t in $j.tables) { Write-Host ("      {0,-46} {1,9}" -f $t.name, $t.size) }
            Pause2
        }
        '71' {
            $nm = Ask '配置表名（如 config_partner_base）'
            $kw = Ask '关键词（可空）'
            $q  = '/cfg?name=' + $nm + '&limit=30'
            if ($kw -ne '') { $q += '&kw=' + [System.Uri]::EscapeDataString($kw) }
            $r = Api $q
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    {0}：共 {1} 条，显示 {2}；字段 {3}" -f $j.name, $j.total, $j.shown, ($j.fields -join ','))
            foreach ($it in $j.items) {
                Write-Host ("      [{0}] {1}" -f $it.key, (($it.row | ConvertTo-Json -Compress) -replace '\s+',' '))
            }
            Pause2
        }
        '72' {
            $kw = Ask '物品名关键词'
            $r = Api ('/listitems?kw=' + [System.Uri]::EscapeDataString($kw) + '&limit=30')
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    命中 {0} 条：" -f $j.n)
            foreach ($it in $j.items) { Write-Host ("      bid={0,-7} type={1,-5} {2}" -f $it.bid, $it.type, $it.name) }
            Pause2
        }
        '73' {
            $kw = Ask 'NPC 关键词（可空）'
            $r = Api ('/cfg?name=config_npc&limit=30&kw=' + [System.Uri]::EscapeDataString($kw))
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    config_npc：共 {0} 条，显示 {1}" -f $j.total, $j.shown)
            foreach ($it in $j.items) { Write-Host ("      [{0}] {1}" -f $it.key, (($it.row | ConvertTo-Json -Compress) -replace '\s+',' ')) }
            Pause2
        }
        '74' {
            $kw = Ask '伙伴名关键词（可空）'
            $r = Api ('/cfg?name=config_partner_base&limit=30&kw=' + [System.Uri]::EscapeDataString($kw))
            try { $j = $r | ConvertFrom-Json } catch { Write-Host "    $r"; Pause2; break }
            Write-Host ("    config_partner_base：共 {0} 条，显示 {1}" -f $j.total, $j.shown)
            foreach ($it in $j.items) { Write-Host ("      [{0}] {1}" -f $it.key, (($it.row | ConvertTo-Json -Compress) -replace '\s+',' ')) }
            Pause2
        }
        '60' { Write-Host ("    " + (Api '/reload?what=all')); Pause2 }

        '0'  { return }
        default { }
    }
}
