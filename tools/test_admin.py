import urllib.request, json
A='http://127.0.0.1:8080/DSH_ADMIN'
def get(p):
    try:
        with urllib.request.urlopen(A+p, timeout=8) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ERR': str(e)[:110]}
for p, label in (
    ('/status', 'status'),
    ('/listitems?kw=\u957f\u67aa&limit=5', 'listitems \u957f\u67aa'),
    ('/giveitem?bid=16201&num=3', 'giveitem 16201 x3'),
    ('/setequip?bid=40003', 'setequip 40003'),
    ('/setjubaopen?pool=16201:40,33001:30', 'setjubaopen'),
    ('/reload?what=item', 'reload item'),
    ('/reset?what=levgift', 'reset levgift'),
):
    r = get(p)
    s = json.dumps(r, ensure_ascii=False)
    print("  %-22s -> %s" % (label, s[:150]))
