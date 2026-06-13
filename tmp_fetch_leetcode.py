import json, os, time
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

        # Check page content
        content = page.content()
        print("Content length:", len(content))

        # Look for solution links
        links = page.query_selector_all("a")
        solution_links = []
        for link in links:
            href = link.get_attribute("href")
            if href and "/solutions/" in str(href) and href != "/problems/coin-change/solutions/":
                solution_links.append(href)

        print(f"Found {len(solution_links)} solution links")

        # Try to find code blocks
        code_blocks = page.query_selector_all("pre")
        print(f"Found {len(code_blocks)} pre blocks")

        # Try finding solution content via different selectors
        for selector in [".solution", "[data-testid]", ".elfjS", "code", ".text-base"]:
            els = page.query_selector_all(selector)
            if els:
                print(f"Found {len(els)} elements matching {selector}")

        # Save page for debugging
        with open(f"{OUT_DIR}/debug_leetcode.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved debug page")

        browser.close()

if __name__ == "__main__":
    main()
