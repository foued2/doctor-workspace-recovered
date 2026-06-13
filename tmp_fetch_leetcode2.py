import json, os, time, re
from playwright.sync_api import sync_playwright

URL = "https://leetcode.com/problems/coin-change/solutions/"
OUT_DIR = "human_solvers"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Loading solutions page...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        time.sleep(8)
        print("Title:", page.title())

        # Find all solution links
        links = page.query_selector_all("a")
        solution_urls = []
        for link in links:
            href = link.get_attribute("href")
            if href and "/solutions/" in str(href) and href != "/problems/coin-change/solutions/" and href.count("/") > 2:
                full_url = "https://leetcode.com" + href if href.startswith("/") else href
                if full_url not in solution_urls:
                    solution_urls.append(full_url)

        print(f"Found {len(solution_urls)} unique solution URLs")
        for url in solution_urls[:5]:
            print(f"  {url}")

        # Visit each solution page and extract Python code
        saved = 0
        for i, url in enumerate(solution_urls):
            try:
                print(f"\n[{i+1}/{len(solution_urls)}] Visiting: {url}")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)

                # Look for code blocks with Python
                code_blocks = page.query_selector_all("pre")
                python_code = None

                for block in code_blocks:
                    text = block.inner_text()
                    if "def " in text and ("coin" in text.lower() or "dp" in text.lower() or "change" in text.lower()):
                        python_code = text
                        break

                if not python_code:
                    # Try code elements
                    code_els = page.query_selector_all("code")
                    for el in code_els:
                        text = el.inner_text()
                        if "def " in text and len(text) > 50:
                            python_code = text
                            break

                if python_code:
                    # Extract post ID from URL
                    post_id = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
                    filename = f"{OUT_DIR}/lc_{post_id}.py"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(python_code)
                    saved += 1
                    print(f"  Saved: {filename} ({len(python_code)} bytes)")
                else:
                    print(f"  No Python code found")

            except Exception as e:
                print(f"  Error: {e}")

        print(f"\nTotal saved: {saved} files")
        browser.close()

if __name__ == "__main__":
    main()
