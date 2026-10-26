import sys, time, json, cProfile, pstats, io
sys.path.insert(0, r"server")
import mock_server as m
cfg = json.load(open(r"server\config.json", encoding="utf-8"))

def t(label, fn, n=30):
    fn()  # warm
    t0=time.perf_counter()
    for _ in range(n): fn()
    t1=time.perf_counter()
    print("  %-34s %7.2f ms/次" % (label, (t1-t0)/n*1000))

print("=== 热路径单次耗时（30 次平均）===")
t("role_state(cfg)",              lambda: m.role_state(cfg))
t("mission_chain(cfg,1001)",      lambda: m.mission_chain(cfg, 1001))
t("mission_rows(cfg,1001)",       lambda: m.mission_rows(cfg, 1001))
t("accept_mission_rows(cfg,1001)",lambda: m.accept_mission_rows(cfg, 1001))
t("db_get_missions(1001)",        lambda: m.db_get_missions(1001))
t("db_get_assets(1001)",          lambda: m.db_get_assets(1001))
t("db_get_role(1001)",            lambda: m.db_get_role(1001))
t("mission_def(10010)",           lambda: m.mission_def(10010))
t("build_10303",                  lambda: m.build_10303(m.role_state(cfg), cfg.get('skills',[]), cfg.get('attr')))

print()
print("=== 一次 SC_12400 请求内部的调用构成（cProfile）===")
pr = cProfile.Profile(); pr.enable()
for _ in range(20):
    ms = m.mission_rows(cfg, 1001)
    b = m.build_12400(ms)
pr.disable()
st = io.StringIO(); ps = pstats.Stats(pr, stream=st).sort_stats('cumulative')
ps.print_stats(12)
out = st.getvalue().split('\n')
for line in out[4:20]:
    if line.strip(): print("  " + line[:118])
