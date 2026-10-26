#!/usr/bin/env python3
# APK static analysis: structure, manifest hints, engine detection, server address scan
import sys, os, zipfile, re, collections, hashlib

APK = sys.argv[1]
base = os.path.splitext(os.path.basename(APK))[0]
OUT = os.path.join(os.path.dirname(APK), base + "_analyze.txt")
out = open(OUT, "w", encoding="utf-8", errors="replace")

def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    out.write(s + "\n")

log("=" * 78)
log("FILE :", APK)
log("SIZE :", os.path.getsize(APK), "bytes")
h = hashlib.sha256()
with open(APK, "rb") as f:
    for chunk in iter(lambda: f.read(1 << 20), b""):
        h.update(chunk)
log("SHA256:", h.hexdigest())

try:
    z = zipfile.ZipFile(APK)
except Exception as e:
    log("ZIP ERROR:", e)
    out.close()
    sys.exit(1)

names = z.namelist()
log("ENTRIES:", len(names))

dirs = collections.Counter(n.split("/")[0] for n in names)
log("TOP LEVEL:")
for k, v in dirs.most_common():
    log("   ", k, v)

libs = collections.defaultdict(list)
for n in names:
    if n.startswith("lib/") and n.endswith(".so") and len(n.split("/")) >= 3:
        libs[n.split("/")[1]].append(n.rsplit("/", 1)[-1])
if libs:
    log("NATIVE LIBS (ABI -> .so):")
    for abi, files in libs.items():
        log("   ", abi, len(files))
        for f in sorted(files)[:80]:
            log("      ", f)
else:
    log("NO lib/*.so found -> possible H5/asset-only wrapper")

h5 = [n for n in names if n.lower().endswith((".html", ".htm")) or "/web/" in n.lower() or "webapp" in n.lower()]
log("HTML/WEB entries:", len(h5), h5[:20])

# ---- manifest strings ----
try:
    mdata = z.read("AndroidManifest.xml")
    log("MANIFEST size:", len(mdata))
    def bin_strings(data, minlen=3):
        res = set()
        for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data):
            res.add(m.group().decode("latin1"))
        for m in re.finditer(rb"(?:[\x20-\x7e]\x00){%d,}" % minlen, data):
            b = m.group().decode("latin1")
            res.add(b[::2])
        return res
    strs = bin_strings(mdata)
    pkg_re = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+){1,6}$")
    log("-- possible package names --")
    for s in sorted(strs):
        if pkg_re.match(s) and len(s) <= 70 and not s.startswith("android.") and "http" not in s.lower():
            if any(ch.isdigit() for ch in s) or "." in s:
                log("   ", s)
    log("-- version-like --")
    for s in sorted(strs):
        if re.match(r"^\d+(\.\d+){1,4}$", s) and 3 <= len(s) <= 14:
            log("   ", s)
    log("-- activities (heuristic) --")
    for s in sorted(strs):
        if ("Activity" in s or "activity" in s) and "." in s and len(s) < 90:
            log("   ", s)
    log("-- urls in manifest --")
    for s in sorted(strs):
        if s.lower().startswith(("http://", "https://")) and len(s) < 130:
            log("   ", s)
except KeyError:
    log("NO AndroidManifest.xml")

# ---- interesting small files ----
log("-- interesting entries (server/config/url/...) --")
keys = ["server", "config", "setting", "url", "host", "ip", "game_list", "login", "gate", "route", "platform", "channel", "version", "notice", "announce"]
count = 0
for n in names:
    if n.endswith(("/", ".png", ".jpg", ".jpeg", ".gif", ".ogg", ".mp3", ".so", ".dex", ".pak", ".bin", ".dat", ".ttf", ".wav")):
        continue
    ln = n.lower()
    if any(k in ln for k in keys):
        try:
            info = z.getinfo(n)
            if info.file_size < 400 * 1024:
                count += 1
                if count > 150:
                    log("... (more)")
                    break
                text = z.read(n)
                disp = text.decode("utf-8", "ignore")[:400].replace("\n", "\\n")
                log("###", n, info.file_size, "bytes")
                log("    ", disp)
        except Exception:
            pass
if count == 0:
    log("   (none matched)")

# ---- deep scan: dex + so for urls / ip:port ----
url_re = re.compile(rb"https?://[A-Za-z0-9._\-/:%?=&@#~+]{6,}")
ip_re = re.compile(rb"(?<![\d.])((?:\d{1,3}\.){3}\d{1,3})(?::(\d{2,5}))?")
urls = collections.Counter()
ips = collections.Counter()
scanned = 0
for n in names:
    if not (n.endswith(".dex") or n.endswith(".so")):
        continue
    try:
        info = z.getinfo(n)
        if info.file_size > 160 * 1024 * 1024 or info.file_size <= 0:
            continue
        scanned += 1
        buf = z.read(n)
        for m in url_re.finditer(buf):
            u = m.group().decode("latin1")
            u = re.sub(r"[\\\"'<>{}|^`\x00-\x1f].*$", "", u)
            if len(u) > 8:
                urls[u.split("?")[0][:120]] += 1
        for m in ip_re.finditer(buf):
            ip4 = m.group(1).decode("latin1")
            if any(int(x) > 255 for x in ip4.split(".")):
                continue
            port = m.group(2).decode("latin1") if m.group(2) else ""
            ips[(ip4, port)] += 1
        log("scanned:", n, info.file_size)
    except Exception as e:
        log("scan err", n, e)
log("SCANNED FILES:", scanned)
log("-- top urls --")
for u, c in urls.most_common(60):
    log("  %5d  %s" % (c, u))
log("-- top ip[:port] --")
for (ip4, port), c in ips.most_common(60):
    log("  %5d  %s:%s" % (c, ip4, port or "-"))

log("DONE")
out.close()
print("REPORT:", OUT)