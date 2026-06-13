import urllib.request, json, time

failed = [1860, 1932, 1934, 1948, 1972, 1989, 2043, 2087]
coin_map = {
    1860:['B'], 1932:['A'], 1934:['B'], 1948:['F'],
    1972:['B'], 1989:['A'], 2043:['A'], 2087:['C']
}

total = 0
for cid in failed:
    time.sleep(2)
    try:
        url = f'https://codeforces.com/api/contest.status?contestId={cid}&from=1&count=10000'
        req = urllib.request.urlopen(url, timeout=15)
        data = json.loads(req.read())
        if data.get('status') != 'OK':
            print(f'{cid}\tAPI_ERR\t0')
            continue
        coin_indices = coin_map[cid]
        wa_py = [s for s in data['result'] if s.get('verdict') == 'WRONG_ANSWER' 
                 and 'python' in s.get('programmingLanguage','').lower()
                 and s.get('problem',{}).get('index','') in coin_indices]
        cnt = len(wa_py)
        total += cnt
        idx_str = ','.join(coin_indices)
        print(f'{cid}\t{idx_str}\t{cnt}')
    except Exception as e:
        print(f'{cid}\tERR\t{str(e)[:40]}')

print(f'RETRY_TOTAL\t{total}')
print(f'GRAND_TOTAL\t{476 + total}')
