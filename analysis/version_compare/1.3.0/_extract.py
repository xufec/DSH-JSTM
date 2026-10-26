import zipfile, os
APK = r"C:\Users\xu\Desktop\DSH\anzbao\dldlJl.apk"
DEST = r"C:\Users\xu\Desktop\DSH\analysis\version_compare\1.3.0\extracted"
z = zipfile.ZipFile(APK)
os.makedirs(DEST, exist_ok=True)

want_prefix = ("assets/src/game/garden/", "assets/src/game/jingjie/",
               "assets/src/game/moneytree/", "assets/src/game/xiulianhulu/")
sel = []
for n in z.namelist():
    b = os.path.basename(n)
    if not n.endswith(".luac"):
        continue
    if b.startswith("config_") or b.startswith("cmd_resolve_") or b in ("config.luac", "version.luac", "protocalrulesmgr.luac", "all_proto.luac"):
        sel.append(n)
    elif n.startswith(want_prefix):
        sel.append(n)

n_bytes = 0
for n in sel:
    out = os.path.join(DEST, n.replace("assets/src/", "").replace("/", os.sep))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    data = z.read(n)
    open(out, "wb").write(data)
    n_bytes += len(data)

print("extracted %d files, %.2f MB -> %s" % (len(sel), n_bytes/1048576, DEST))
import collections
top = collections.Counter(n.split("/")[0] for n in sel)
print(dict(top))
