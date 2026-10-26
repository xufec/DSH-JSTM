import json, os
p = r"C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\ui_inventory.json"
d = json.load(open(p, "r", encoding="utf-8"))
print("total:", d["total_entries"])
print("by status:", d["summary_by_status"])
print("by system (top 20):")
for k, v in sorted(d["summary_by_system"].items(), key=lambda x: -x[1])[:20]:
    print(f"  {k:22s} {v}")
print()
print("--- A 类条目 ---")
for e in d["entries"]:
    if e["status"] == "A":
        print(f"  [{e['system_id']:20s}] {e['ui_name']:45s} mod={e['module']}")
print()
print("--- D 类条目 ---")
for e in d["entries"]:
    if e["status"] == "D":
        print(f"  {e['ui_name']:45s} {e['client_entry_luac']}")
print()
print("--- C 类前 5 ---")
n=0
for e in d["entries"]:
    if e["status"] == "C":
        print(f"  {e['ui_name']}")
        n+=1
        if n>=8: break
