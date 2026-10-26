# C3.1 第三分片：测试工具修复 diff

> 日期：2026-10-15
> 范围：仅修复 `tools\restart_server.ps1`（工具恢复，非新功能）；不改动 `mock_server.py` 与任何业务代码。

## 1. 根因定位（实测，非推测）

C3.1-B 记录 `restart_server.ps1` 本机失效：WMI Create 后报 `'""' 不是内部或外部命令`。
当时初步归因为「python 路径含空格 `"User Data"` 致 cmd 嵌套引号解析失败」。

本分片实测复现后确认真根因（与空格**无关**）：

```
PS> (Get-Command python) | Format-List CommandType, Source, Definition
CommandType : Alias
Source      = ""            ← 空！
Definition  = C:\Users\xu\AppData\Local\Doubao\User Data\sandbox_runtime\...\python\python.exe
```

- 本环境里 `python` 是一个 **Alias**（指向 sandbox_runtime 下的 python.exe）。
- `Alias.Source` 为**空串**；真实路径在 `.Definition`。
- 原脚本 `$py = (Get-Command python).Source` 取到**空串**，于是 WMI cmdline 拼成：

  ```
  cmd.exe /c "" "" "C:\...\mock_server.py" 1>"..." 2>"...""
  ```

- cmd.exe 把第一个 `""`（空引号串）当作可执行文件 ⇒ `'""' 不是内部或外部命令`。

**空格只是次要因素**：实测取到真实 Definition 路径后，既有的 `cmd.exe /c ""py" "mock" 1>"out" 2>"err""` 嵌套引号对含空格路径**工作正常**（探针：WMI Create 后 `stdout.log` 得到 `Python 3.13.13`）。

## 2. diff（restart_server.ps1 第 4 步启动段）

```diff
 # 改用 WMI 创建进程：父进程是 WmiPrvSE，**不继承任何句柄**，
 # 所以调用方立刻返回，服务端独立存活。
-$py = (Get-Command python).Source
+# ★ C3.1 修复（本机失效根因）：
+#   `python` 在本环境是 **Alias**，.Source 为空；真实路径在 .Definition。
+#   原写法取到空串 ⇒ cmdline 变成 `cmd.exe /c "" "" "...mock..."` ⇒ cmd 把
+#   `""` 当命令 ⇒ `'""' 不是内部或外部命令`。
+#   （实测：取到真实路径后，嵌套引号对含空格路径工作正常。）
+$pyCmd = Get-Command python
+$py = if ($pyCmd.CommandType -eq 'Alias') { $pyCmd.Definition } else { $pyCmd.Source }
+if (-not $py -or -not (Test-Path $py)) { throw "找不到 python 可执行文件（Get-Command=$($pyCmd.CommandType)）" }
 $logOut = Join-Path $root 'server\logs\stdout.log'
```

## 3. 验证

- 修复后实跑 `powershell -ExecutionPolicy Bypass -File tools\restart_server.ps1 -NoSmoke`：
  - `[1/5]` 杀旧 PID 30004 ✅
  - `[4/5]` WMI Create 返回新 PID，9000/8080 监听恢复 ✅
  - HTTP `/DSH_ADMIN/getassets?rid=1001` 返回 200 ✅
- 该脚本在 `c1_e2e_closed_loop.py` 的第 9 环（杀进程→重启→重登）中被再次真实调用，重启前后角色数据逐字节一致（见测试报告 §2 第 9 项）。
