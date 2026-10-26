"""为探针加"诊断块版本开关"（默认关标志=行为不变）。

- 在 server/dsh_fake_login.lua 的第 187 行（诊断块起点）之前插入
      if not _G.__dsh_noprobe then
 并在文件末尾补 end。
  （187 行起是一串**完整语句**，整体包进 if 是安全的。）
- 产出 server/dsh_fake_login_noprobe.lua = 置位标志 + 上面那份内容
  ⇒ 供 1.4.11 / 1.3.0 使用：**保留伪登录、关掉全部诊断 hook**。
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'server', 'dsh_fake_login.lua')
OUT = os.path.join(ROOT, 'server', 'dsh_fake_login_noprobe.lua')
ANCHOR = 'pcall(function()'          # 第 187 行
GUARD = 'if not _G.__dsh_noprobe then\n'

lines = io.open(SRC, encoding='utf-8').read().splitlines(True)

if any('__dsh_noprobe' in l for l in lines):
    print('已加过开关，跳过修改')
else:
    idx = None
    for i, l in enumerate(lines):
        if i > 170 and l.startswith(ANCHOR):
            idx = i
            break
    assert idx is not None, '未找到诊断块起点'
    print('诊断块起点：第 %d 行' % (idx + 1))
    new = lines[:idx] + [GUARD] + lines[idx:]
    # 末尾补 end（保留原末尾换行）
    tail = new[-1]
    if not tail.endswith('\n'):
        new[-1] = tail + '\n'
    new.append('end\n')
    io.open(SRC, 'w', encoding='utf-8').write(''.join(new))
    print('已插入开关，总行 %d -> %d' % (len(lines), len(new)))

# 产出"关诊断"版本：置位 + 原内容
body = io.open(SRC, encoding='utf-8').read()
io.open(OUT, 'w', encoding='utf-8').write(
    '-- [DSH] 版本开关：关掉全部诊断 hook，只保留 URL 短路 + 伪登录\n'
    '_G.__dsh_noprobe = true\n' + body)
print('已写出 %s  (%d bytes)' % (OUT, os.path.getsize(OUT)))
