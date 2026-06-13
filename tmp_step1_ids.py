import urllib.request, json, time

# Contest 1061 - problem A (Coins, LC322-isomorphic)
# Contest 1934 - problem B (Yet Another Coin Problem, LC322-isomorphic)

results = {}

for contest_id, problem_index in [(1061, 'A'), (1934, 'B')]:
    url = f'https://codeforces.com/api/contest.status?contestId={contest_id}&from=1&count=10000'
    try:
        req = urllib.request.urlopen(url, timeout=15)
        data = json.loads(req.read())
        if data.get('status') != 'OK':
            print(f'API error for contest {contest_id}')
            continue
        subs = data['result']
        # Filter: WRONG_ANSWER + Python + specific problem
        wa_py = [s for s in subs 
                 if s.get('verdict') == 'WRONG_ANSWER'
                 and 'python' in s.get('programmingLanguage', '').lower()
                 and s.get('problem', {}).get('index', '') == problem_index]
        results[contest_id] = wa_py
        print(f'Contest {contest_id} Problem {problem_index}: {len(wa_py)} WA Python submissions')
    except Exception as e:
        print(f'Error for contest {contest_id}: {e}')
    time.sleep(0.5)

# Print all submission IDs
print('\n--- SUBMISSION IDs ---')
all_ids = []
for contest_id, subs in results.items():
    print(f'\nContest {contest_id}:')
    for s in subs:
        sid = s['id']
        lang = s['programmingLanguage']
        time_ms = s.get('timeConsumedMillis', '?')
        print(f'  ID: {sid}  Lang: {lang}  Time: {time_ms}ms')
        all_ids.append(sid)

print(f'\n--- TOTAL: {len(all_ids)} submission IDs ---')
