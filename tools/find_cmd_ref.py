"""通用工具：**谁在客户端里发送/引用了某个命令号**。

原理：LuaJIT 的 `KSHORT` 指令把 16 位立即数放在指令字的高 16 位，
低 8 位是 opcode。所以「命令号 N」在字节码里表现为 4 字节（小端）：
    b0 = KSHORT 的 opcode ，b1 = 0 ，b2/b3 = N 的高/低字节
直接对整个 .luac 做 4 字节对齐扫描即可，**不需要反汇编**。

用法：
    python tools/find_cmd_ref.py 15402            # 扫全 APK
    python tools/find_cmd_ref.py 15402 --ctx 40   # 额外打印命中处的字符串常量做上下文
"""
import os
import re
import struct
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from luajit_dis import OPS  # noqa: E402

APK = os.path.join(ROOT, 'anzbao', 'jstm.apk')


def kshort_op():
    for i, n in enumerate(OPS):
        if n == 'KSHORT':
            return i
    raise SystemExit('未找到 KSHORT opcode')


def scan(data, cmd):
    """找出该文件里所有 `KSHORT D=<cmd>` 指令。

    指令字布局（`tools/luajit_dis.py` 的 `decode` 为准）：
        op = ins & 0xff ; a = (ins>>8)&0xff ; d = (ins>>16)&0xffff
    ★ 关键：**A 操作数是可变的**（`KSHORT A=3 …` 很常见），
      所以不能直接搜 `op,0,d_lo,d_hi` —— 那是第一版工具的 bug（命中恒 0）。
      正确做法：先找 2 字节的 D 值，再回看第 −2 字节是不是 KSHORT 的 opcode。
    """
    op = kshort_op()
    dbytes = struct.pack('<H', cmd & 0xffff)
    hits = []
    start = 0
    while True:
        i = data.find(dbytes, start)
        if i < 0:
            break
        if i >= 2 and data[i - 2] == op:
            hits.append(i - 2)
        start = i + 1
    return hits


def strings_near(data, off, span=160):
    """在命中点附近捞可读字符串，用于判断上下文（哪个 proto / 哪个函数）。"""
    lo = max(0, off - span)
    hi = min(len(data), off + span)
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{4,60}', data[lo:hi]):
        s = m.group().decode('ascii', 'replace')
        if not s.startswith('___'):
            out.append(s)
    return out[:8]


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = int(sys.argv[1])
    ctx = '--ctx' in sys.argv
    print('KSHORT opcode =', kshort_op(), ' 目标命令 =', cmd)
    z = zipfile.ZipFile(APK)
    total = 0
    for n in z.namelist():
        if not n.endswith('.luac'):
            continue
        d = z.read(n)
        h = scan(d, cmd)
        if not h:
            continue
        total += len(h)
        print('\n%s  × %d  处命中' % (n, len(h)))
        for off in h[:4]:
            if ctx:
                print('   @%-7d  %s' % (off, ' | '.join(strings_near(d, off))))
    print('\n合计命中 %d 处' % total)


if __name__ == '__main__':
    main()
