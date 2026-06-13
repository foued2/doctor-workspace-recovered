"""Check ChatGPT corpus - all problems."""
import json

with open("data/chatgpt_codegen_python.json") as f:
    data = json.load(f)

items = data if isinstance(data, list) else data.get("results", [])

print(f"Total problems: {len(items)}")
print(f"Pass: {sum(1 for i in items if i.get('is_pass')==1)}, Fail: {sum(1 for i in items if i.get('is_pass')==0)}")

# Check for related problems
related = ["coin", "search", "delay", "dijkstra", "shortest", "graph", "backtrack", "dp"]
for keyword in related:
    matches = [i for i in items if keyword in i.get("name", "").lower()]
    if matches:
        print(f"\n'{keyword}' matches: {len(matches)}")
        for m in matches[:3]:
            print(f"  {m.get('name')}: pass={m.get('is_pass')}")

# Print all names
print("\n--- ALL PROBLEM NAMES ---")
for item in sorted(items, key=lambda x: x.get("name", "")):
    print(f"  {item.get('name')}: pass={item.get('is_pass')}")
