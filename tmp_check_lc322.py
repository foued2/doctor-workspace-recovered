import json

with open('data/c4_decisions_lc322.json') as f:
    data = json.load(f)

print(f'Gap: {data["falsification"]["best_gap"]}')
print(f'B1 WA: {data["b1_aggregate"]["wrong_accepts"]}, WR: {data["b1_aggregate"]["wrong_rejects"]}')
print(f'C_genuine WA: {data["c_genuine_aggregate"]["wrong_accepts"]}, WR: {data["c_genuine_aggregate"]["wrong_rejects"]}')
