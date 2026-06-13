import json, os, time
from playwright.sync_api import sync_playwright

OUT_DIR = "human_solvers"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Try different discuss URLs with search queries
        search_urls = [
            "https://leetcode.com/problems/coin-change/discuss/?currentPage=1&orderBy=newest_to_oldest&query=python+greedy",
            "https://leetcode.com/problems/coin-change/discuss/?currentPage=1&orderBy=newest_to_oldest&query=python+recursive",
            "https://leetcode.com/problems/coin-change/discuss/?currentPage=1&orderBy=newest_to_oldest&query=python+bfs",
        ]

        all_urls = set()

        for search_url in search_urls:
            query = search_url.split("query=")[-1]
            print(f"\n=== Searching: {query} ===")
            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(6)

                # Get page content to check what's there
                content = page.content()
                print(f"  Content length: {len(content)}")

                links = page.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and ("/discuss/" in str(href) or "/solutions/" in str(href)) and href.count("/") > 3:
                        full = "https://leetcode.com" + href if href.startswith("/") else href
                        all_urls.add(full)

                print(f"  Total unique URLs: {len(all_urls)}")
            except Exception as e:
                print(f"  Error: {e}")

        # Also try Google search for LC322 greedy/wrong solutions
        print(f"\n=== Google search for LC322 wrong/greedy solutions ===")
        try:
            page.goto("https://www.google.com/search?q=leetcode+322+coin+change+python+greedy+wrong+site:leetcode.com", wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            links = page.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href")
                if href and "leetcode.com" in str(href) and "coin-change" in str(href):
                    all_urls.add(href)
            print(f"  Total unique URLs: {len(all_urls)}")
        except Exception as e:
            print(f"  Error: {e}")

        print(f"\n=== Final URL count: {len(all_urls)} ===")
        for url in sorted(all_urls):
            print(f"  {url}")

        browser.close()

if __name__ == "__main__":
    main()
