import json
import sys

p = sys.argv[1]
with open(p, "r", encoding="utf-8") as f:
    nb = json.load(f)
changed = 0
for c in nb.get("cells", []):
    if c.get("cell_type") != "code":
        continue
    for o in c.get("outputs", []) or []:
        t = o.get("output_type")
        if t == "stream" and "name" not in o:
            o["name"] = "stdout"
            changed += 1
        if t in ("display_data", "execute_result") and "metadata" not in o:
            o["metadata"] = {}
            changed += 1
        if t == "execute_result" and "execution_count" not in o:
            o["execution_count"] = c.get("execution_count")
            changed += 1
with open(p, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print(f"patched {changed} outputs in {p}")
