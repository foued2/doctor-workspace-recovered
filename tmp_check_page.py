import urllib.request
import re

url = 'https://codeforces.com/contest/1061/submission/370702072'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
resp = urllib.request.urlopen(req, timeout=15)
html = resp.read().decode('utf-8', errors='replace')

# Find all pre tags with their classes
pres = re.findall(r'<pre[^>]*class="([^"]*)"', html)
print('pre classes found:', pres)

# Check for source-related content
if 'source' in html.lower():
    idx = html.lower().find('source')
    print('source context:', html[max(0,idx-200):idx+300])

# Check if login required
if 'Log in' in html:
    print('LOGIN REQUIRED detected')

# Check for programSourceText or similar
if 'programSourceText' in html:
    idx = html.find('programSourceText')
    print('programSourceText found at:', idx)
    print(html[idx-100:idx+500])

# Show relevant portion
print('---HTML SNIPPET (2000-4000)---')
print(html[2000:4000])
