import urllib.request
import json
import time
import os
import re

# All 40 submission IDs with their contest IDs
submissions = [
    # Contest 1061, Problem A (27 submissions)
    (1061, 370702072), (1061, 364587022), (1061, 364586911), (1061, 357646847),
    (1061, 356680082), (1061, 353777390), (1061, 348730210), (1061, 347729881),
    (1061, 347729645), (1061, 347727935), (1061, 347726858), (1061, 347201261),
    (1061, 347200947), (1061, 347198627), (1061, 340637608), (1061, 339499484),
    (1061, 339498274), (1061, 339496368), (1061, 338009263), (1061, 337980567),
    (1061, 332067688), (1061, 311019469), (1061, 309484175), (1061, 309483136),
    (1061, 302633574), (1061, 301995233), (1061, 301994099),
    # Contest 1934, Problem B (13 submissions)
    (1934, 377799902), (1934, 372984409), (1934, 372983148), (1934, 372982798),
    (1934, 372982350), (1934, 372855088), (1934, 363913074), (1934, 345753172),
    (1934, 343975142), (1934, 343973781), (1934, 343924840), (1934, 342147752),
    (1934, 327945510),
]

# Create output directory
output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_solvers')
os.makedirs(output_dir, exist_ok=True)

success = 0
failed = 0
errors = []

for contest_id, sub_id in submissions:
    url = f'https://codeforces.com/contest/{contest_id}/submission/{sub_id}'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode('utf-8', errors='replace')
        
        # Extract source code from <pre class="source"> tag
        # The source code is between <pre class="source"> and </pre>
        match = re.search(r'<pre\s+class="source"[^>]*>(.*?)</pre>', html, re.DOTALL)
        if match:
            source = match.group(1)
            # Decode HTML entities
            source = source.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
            source = source.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
            
            filepath = os.path.join(output_dir, f'cf_{sub_id}.py')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(source)
            success += 1
            print(f'OK: {sub_id} ({len(source)} bytes)')
        else:
            failed += 1
            errors.append(f'{sub_id}: source tag not found')
            print(f'FAIL: {sub_id} - source tag not found')
        
        time.sleep(0.3)  # Rate limit
    except Exception as e:
        failed += 1
        errors.append(f'{sub_id}: {str(e)[:60]}')
        print(f'FAIL: {sub_id} - {str(e)[:60]}')
        time.sleep(1)

print(f'\n--- SUMMARY ---')
print(f'Successfully downloaded: {success}')
print(f'Failed: {failed}')
print(f'Total usable files: {success}')
if errors:
    print(f'\nErrors:')
    for e in errors:
        print(f'  {e}')
