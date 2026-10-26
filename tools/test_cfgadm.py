import urllib.request, json, urllib.parse
A='http://127.0.0.1:8080/DSH_ADMIN'
def get(p):
    try:
        with urllib.request.urlopen(A+p, timeout=20) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ERR': str(e)[:120]}
r=get('/cfglist')
if 'tables' in r:
    print("  /cfglist -> %d 张表；前 5：%s" % (r['n'], [t['name'] for t in r['tables'][:5]]))
else:
    print("  /cfglist ->", r)
kw = urllib.parse.quote('\u5510\u821e\u6850')
r=get('/cfg?name=config_partner_base&kw='+kw+'&limit=3')
print("  /cfg partner_base 搜'唐舞桐' -> total=%s shown=%s" % (r.get('total'), r.get('shown')))
for it in (r.get('items') or [])[:2]:
    print("     ", json.dumps(it, ensure_ascii=False)[:150])
r=get('/cfg?name=config_npc&limit=2')
print("  /cfg config_npc -> total=%s shown=%s" % (r.get('total'), r.get('shown')))
for it in (r.get('items') or [])[:2]:
    print("     ", json.dumps(it, ensure_ascii=False)[:130])
