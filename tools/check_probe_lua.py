"""注入到客户端 config.luac 的探针脚本 —— 粗粒度语法自检。

没有可用的 Lua 解释器时（本机未安装 lua/luajit），至少做：
  1. 括号/中括号/花括号平衡（先剥离注释与字符串）
  2. function / if / for / while / do / end 关键字平衡（粗估）
  3. top-level 的 pcall(function() ... end) 块是否配平

⚠ 这只是**粗检**，不能替代真正的 Lua 解析。真正的确认靠客户端
   `loadstring` 执行成功（表现为探针上报 `bt`/`driver` 等标签）。
   若注入后客户端 config.luac 解析失败，应立即回退该文件。

用法：python tools/check_probe_lua.py server/dsh_fake_login.lua
"""
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def strip_lua(src):
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        # 长注释 --[[ ... ]] / --[==[ ... ]==]
        if src.startswith('--[[', i) or re.match(r'--\[=+\[', src[i:i + 6] or ''):
            j = src.find(']]', i)
            while j != -1 and src[j:j + 2] == ']]' and '[=' in src[i:i + 6]:
                break
            j = src.find(']]', i)
            i = (j + 2) if j != -1 else n
            continue
        if src.startswith('--', i):
            j = src.find('\n', i)
            i = j if j != -1 else n
            continue
        if c == '"' or c == "'":
            q = c
            i += 1
            while i < n:
                if src[i] == '\\':
                    i += 2
                    continue
                if src[i] == q:
                    i += 1
                    break
                i += 1
            out.append('""')
            continue
        if src.startswith('[[', i) or re.match(r'\[=+\[', src[i:i + 6] or ''):
            m = re.match(r'\[(=*)\[', src[i:i + 8])
            if m:
                close = ']' + m.group(1) + ']'
                j = src.find(close, i + len(m.group(0)))
                i = (j + len(close)) if j != -1 else n
                out.append('""')
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r'server\dsh_fake_login.lua'
    src = open(path, encoding='utf-8').read()
    s = strip_lua(src)

    ok = True
    for a, b in (('(', ')'), ('[', ']'), ('{', '}')):
        na, nb = s.count(a), s.count(b)
        flag = 'OK ' if na == nb else '!! '
        if na != nb:
            ok = False
        print('%s%-3s %5d   %-3s %5d   diff %+d' % (flag, a, na, b, nb, na - nb))

    # 关键字平衡（粗估；lua 的 end 同时闭合 function/if/for/while/do）
    opens = len(re.findall(r'\b(function|if|for|while)\b', s))
    # 'do' 在 for/while 里是同一个块；'elseif/else' 不额外开块
    ends = len(re.findall(r'\bend\b', s))
    print('  关键字: function|if|for|while = %d ,  end = %d  %s'
          % (opens, ends, 'OK' if opens == ends else '（差值可能来自单行 if ... then ... end / 表达式 end）'))

    # top-level pcall(function() 块数
    blocks = len(re.findall(r'^pcall\(function\(\)', s, re.M))
    print('  顶层 pcall(function() 段数 = %d' % blocks)

    print('\n结论:', '粗检通过（仍需客户端 loadstring 实测确认）' if ok else '!! 括号不平衡，很可能语法错误')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
