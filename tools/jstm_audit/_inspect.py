import json
d = json.load(open(r"C:\Users\xu\Desktop\DSH\analysis\jstm_client_audit\ui_inventory.json", "r", encoding="utf-8"))
for e in d["entries"]:
    if e["status"]=="A" and e["module"]=="guild":
        print(json.dumps(e, ensure_ascii=False, indent=2))
        print("---")
