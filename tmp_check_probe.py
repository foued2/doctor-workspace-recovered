import json

with open('data/midweather_fingerprint_lc79_probe_index.json') as f:
    data = json.load(f)

probe = data['probes'][0]
print('Probe 0:')
print(f'  board: {probe["board"]}')
print(f'  word: {probe["word"]}')
print(f'  expected: {probe["expected"]}')
