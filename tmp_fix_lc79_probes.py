import json

with open('data/midweather_fingerprint_lc79_probe_index.json', 'r') as f:
    data = json.load(f)

for probe in data['probes']:
    # Fix 1: Rename "family" to "probe_family"
    if 'family' in probe:
        probe['probe_family'] = probe.pop('family')
    
    # Fix 2: Add fingerprint_context
    probe['fingerprint_context'] = {
        'probe_family': probe.get('probe_family'),
        'axis': probe.get('axis'),
    }

with open('data/midweather_fingerprint_lc79_probe_index.json', 'w') as f:
    json.dump(data, f, indent=2)

# Print first three probes
print(json.dumps(data['probes'][:3], indent=2))
