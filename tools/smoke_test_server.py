import socket, struct, sys, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# --- HTTP ---
try:
    r = urllib.request.urlopen("http://127.0.0.1:8080/notice.json", timeout=5)
    print("HTTP /notice.json -> %s, %d bytes" % (r.status, len(r.read())))
except Exception as e:
    print("HTTP !! %r" % (e,))

# --- TCP 心跳往返（1199）---
try:
    s = socket.create_connection(("127.0.0.1", 9000), timeout=5)
    body = struct.pack(">I", 0x0000274C)          # time = 10060
    payload = struct.pack(">H", 1199) + body
    s.sendall(struct.pack(">I", len(payload)) + payload)
    hdr = s.recv(4)
    if len(hdr) < 4:
        print("TCP !! 没收到帧头")
    else:
        ln = struct.unpack(">I", hdr)[0]
        rest = b""
        while len(rest) < ln:
            c = s.recv(ln - len(rest))
            if not c: break
            rest += c
        cmd = struct.unpack(">H", rest[:2])[0]
        print("TCP 1199 -> 回包 cmd=%d payload_len=%d body=%s" % (cmd, ln, rest[2:].hex(" ")))
    s.close()
except Exception as e:
    print("TCP !! %r" % (e,))
