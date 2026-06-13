import json

with open("data/chatgpt_codegen_python.json") as f:
    data = json.load(f)

targets = ["322-coin-change", "079-word-search", "743-network-delay-time"]
for entry in data:
    if entry["name"] in targets:
        code = entry.get("generated_code", "")
        is_pass = entry.get("is_pass", "N/A")
        error = entry.get("error", "")
        print(f"--- {entry['name']} (is_pass={is_pass}) ---")
        print(f"error: {error}")
        print(f"code preview: {code[:300]}")
        print()

# Count pass/fail across all problems
passes = sum(1 for e in data if e.get("is_pass") == 1)
fails = sum(1 for e in data if e.get("is_pass") == 0)
print(f"Overall: {passes} pass, {fails} fail out of {len(data)}")
