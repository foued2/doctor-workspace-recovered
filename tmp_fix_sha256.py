import json

with open('data/midweather_fingerprint_lc79_seval_manifest.json', 'r') as f:
    data = json.load(f)

# Convert all SHA256 hashes to lowercase
for solver in data.get('solver_files', []):
    if 'sha256' in solver:
        solver['sha256'] = solver['sha256'].lower()

with open('data/midweather_fingerprint_lc79_seval_manifest.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Done. Converted SHA256 hashes to lowercase.")
