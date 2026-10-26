import urllib.request, json, urllib.parse
A='http://127.0.0.1:8080/DSH_ADMIN'
def get(p):
    try:
        with urllib.request.urlopen(A+p, timeout=8) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ERR': str(e)[:100]}
for p, label in (
    ('/giveitem?bid=16201&num=3', 'giveitem 16201x3'),
    ('/setequip?bid=40003', 'setequip 40003'),
    ('/setjubaopen?pool=16201:40,33001:30', 'setjubaopen'),
    ('/reset?what=levgift', 'reset levgift'),
    ('/listitems?kw=' + urllib.parse.quote('\u957f\u67aa') + '&limit=5', 'listitems 长枪'),
    ('/setmissions?bid=10010', 'setmissions 10010'),
):
    r = get(p)
    print("  %-20s -> %s" % (label, json.dumps(r, ensure_ascii=False)[:130]))
