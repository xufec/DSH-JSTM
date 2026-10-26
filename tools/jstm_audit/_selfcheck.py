import json, collections
p = r"C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\ui_inventory.json"
d = json.load(open(p, "r", encoding="utf-8"))
print("=== SELF-CHECK ===")
print("json.load OK, total =", d["total_entries"])
# field completeness
required = ["ui_name","module","system_id","system_name","client_entry_luac",
            "related_lua_modules","related_res_categories","open_condition","close_method",
            "sub_panels","buttons_interactions","data_config_tables","protocols",
            "depends_on_server","runtime_verified","restore_difficulty","status",
            "evidence","confidence"]
missing = collections.Counter()
for e in d["entries"]:
    for k in required:
        if k not in e: missing[k]+=1
print("missing fields:", dict(missing) or "none")
# status counts
print("status counts:", d["summary_by_status"])
# A class must have evidence pointing to runtime
a_no_evidence = [e["ui_name"] for e in d["entries"] if e["status"]=="A" and ("shots" not in e["evidence"] and "PHASE2" not in e["evidence"] and "runtime" not in e["evidence"] and "regression" not in e["evidence"])]
print("A entries without runtime evidence pointer:", a_no_evidence or "none")
# D class must reference diff
d_no_diff = [e["ui_name"] for e in d["entries"] if e["status"]=="D" and "diff" not in e["evidence"] and "1.3.0" not in e["client_entry_luac"]]
print("D entries without diff evidence:", d_no_diff or "none")
# unknowns
unknown_proto = sum(1 for e in d["entries"] if e["protocols"]==["UNKNOWN"] and e["status"]!="D")
print("UNKNOWN-protocol entries (B/C default):", unknown_proto)
# by system top 15
print("by system top 15:")
for k,v in sorted(d["summary_by_system"].items(), key=lambda x:-x[1])[:15]:
    print(f"  {k:22s} {v}")
