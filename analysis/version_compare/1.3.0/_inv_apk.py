import zipfile, os, sys, collections, json

APK = r"C:\Users\xu\Desktop\DSH\anzbao\dldlJl.apk"
z = zipfile.ZipFile(APK)
names = z.namelist()
print("total entries:", len(names))

def group(n):
    if n.startswith("assets/src/"):
        return "assets/src"
    if n.startswith("assets/config/") or "/config/" in n:
        return "config"
    if n.startswith("assets/res"):
        return "assets/res"
    if n.startswith("assets/game"):
        return "assets/game"
    if n.startswith("lib/"):
        return "lib"
    if n.startswith("assets/"):
        return "assets/other"
    return n.split("/")[0] if "/" in n else "(root)"

g = collections.Counter(group(n) for n in names)
for k, v in g.most_common():
    print("  %-16s %d" % (k, v))

def d(n): return z.getinfo(n).file_size
luac_src = [n for n in names if n.startswith("assets/src/") and n.endswith(".luac")]
luac_cfg = [n for n in names if n.endswith(".luac") and ("config" in n.lower())]
all_luac = [n for n in names if n.endswith(".luac")]
print("luac total:", len(all_luac), "| assets/src luac:", len(luac_src),
      "| config-ish luac:", len(luac_cfg))
print("assets total bytes: %.1f MB" % (sum(d(n) for n in names if n.startswith("assets/"))/1048576))

# config table names
cfg = sorted(set(os.path.basename(n) for n in luac_cfg))
print("config table files:", len(cfg))
print("first 40:", ", ".join(cfg[:40]))

# version probe: read small text files that may be plaintext
probe = [n for n in names if n.endswith("config.luac") or n.endswith("version.luac")
         or "version" in n.lower() or n.endswith("main.luac")]
print("\nprobe candidates:", probe[:20])
for n in names:
    if n.startswith("assets/src/") and (n.endswith("config.luac") or "config.luac" == os.path.basename(n)):
        try:
            data = z.read(n)
            txt = data.decode("utf-8", "ignore")
            import re
            m = re.findall(r"(NOW_VERSION|VERSION|BUILD_VERSION|PLATFORM_NAME)[^\n]{0,40}", txt)
            print("  ", n, "->", m[:6])
        except Exception as e:
            print("  ", n, "ERR", e)

out = r"C:\Users\xu\Desktop\DSH\analysis\version_compare\1.3.0\_apk_entries.txt"
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "w", encoding="utf-8").write("\n".join(sorted(names)))
print("\nwrote entry list ->", out)
