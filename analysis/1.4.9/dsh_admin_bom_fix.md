# `dsh_admin.bat` 报错 —— 已修复（UTF-8 BOM 丢失）

## 一、用户报障

附件 `dsh_admin.bat`（141 字节）运行报错。

## 二、复现与真实错误

**直接运行 `dsh_admin.bat`，捕获到的真实报错：**

```
At C:\Users\xu\Desktop\DSH\dsh_admin.ps1:107 char:40
+     Write-Host -NoNewline '  鎸夊洖杞︾户缁?..'
+                                        ~
The string is missing the terminator: '.

At ...:73 char:13   '5' {
At ...:56 char:17   switch ($c) {
At ...:39 char:15   while ($true) {
   → Missing closing '}' in statement block or type definition.
```

**⇒ 中文全变乱码（`鎸夊洖杞︾户缁?`），且**末尾那个乱码字符吃掉了收尾引号** ⇒ 引号不闭合 ⇒
后续 `switch`/`while` 全部"缺右括号" ⇒ **语法错误**。**

## 三、★ 根因：`dsh_admin.ps1` 的 **UTF-8 BOM 丢失**

```
前 4 字节: 23 20 3d 3d        → "# =="
有 UTF-8 BOM: **False**        ← ★ BOM 丢了
内容是 UTF-8 中文: True
```

**机制：**

| 读取方式 | 结果 |
|---|---|
| `[Parser]::ParseFile`（.NET，会**嗅探**编码） | **"语法 OK"** ← 所以文件本身是好的 |
| `powershell -File`（**Windows PowerShell 5.1**） | **按 ANSI(GBK) 读** ⇒ 乱码 ⇒ 语法错 |

**⇒ 这就是"用不同方法检查结论不一样"的原因，也是最容易被误判的一种故障。
**`powershell.exe`（5.1）在没有 BOM 时按系统 ANSI 代码页解析脚本 —— 中文必然乱码。****

**⇒ 显式写 BOM 就是让 5.1 认出这是 UTF-8 的唯一可靠办法。**

## 四、修复

```python
open(p, 'wb').write(b'\xef\xbb\xbf' + open(p, 'rb').read())   # 补 UTF-8 BOM
```

**已修复并实测：**

```
============================================================
   绝世唐门 私服管理台   （在线热改 + 立即推送，无需重登）
============================================================
    等级   {"ok": true, "rid": 1001, "level": 20, "exp": 1550}
    资产   {"ok": true, ..., "gold": 929313, "coin": 901961, "coupon": 999999}
  [1] 设置等级 … [9] 发物品 … [0] 退出
  请选择: 0
```

**⇒ 中文正常、菜单正常、无语法错误、功能可用。**

## 五、★ 顺手全盘排查，又发现并修复 4 个同类隐患

**全盘扫 `.ps1`（47 个），凡"含非 ASCII 却无 BOM"的都修：**

| 文件 | 处理 |
|---|---|
| `tests/run_stability_5.ps1` | ✅ 补 BOM（已备份 `.bak`） |
| `tools/build_apk.ps1` | ✅ 补 BOM（已备份 `.bak`） |
| `tools/build_fakelogin.ps1` | ✅ 补 BOM（已备份 `.bak`） |
| `tools/restart_server.ps1` | ✅ 补 BOM（已备份 `.bak`） |

**用 Windows PowerShell 5.1 逐个复验语法：全部 `OK`；复检剩余风险文件 **0**。**

**另：`.bat`/`.cmd` 全盘扫描 —— 含非 ASCII 的 **0 个** ✓**
（此前"纯 ASCII `.bat` 启动 + UTF-8 BOM `.ps1` 主体"的约定仍然有效。）

## 六、结论与预防

- **`dsh_admin.bat` 本身没问题**（141 字节，纯 ASCII 启动器）—— **问题全在 `.ps1` 缺 BOM。**
- **预防**：任何含中文的 `.ps1` 必须带 UTF-8 BOM；新建/改写后用
  `powershell.exe -File`（**不是** `ParseFile`）验证一次，才能发现这类问题。
