import json, os, time, re
from playwright.sync_api import sync_playwright

OUT_DIR = "human_solvers"

def extract_python_solution(page, url, label):
    """Visit a solution page and extract Python code if present."""
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)

        code_blocks = page.query_selector_all("pre")
        for block in code_blocks:
            text = block.inner_text()
            if "def " in text and len(text) > 80:
                return text

        code_els = page.query_selector_all("code")
        for el in code_els:
            text = el.inner_text()
            if "def " in text and len(text) > 80:
                return text

    except Exception as e:
        print(f"  Error: {e}")
    return None

def classify_solution(code):
    """Classify solution approach."""
    code_lower = code.lower()
    if "greedy" in code_lower or "sort" in code_lower and "while" in code_lower:
        return "greedy"
    if "bfs" in code_lower or "queue" in code_lower or "deque" in code_lower:
        return "bfs"
    if "recursive" in code_lower or ("def " in code and "return" in code and "for" not in code):
        return "recursive"
    if "lru_cache" in code_lower or "@cache" in code_lower or "memo" in code_lower:
        return "memoized_topdown"
    if "dp" in code_lower and ("for" in code):
        return "bottomup_dp"
    return "unknown"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        all_solution_urls = []

        # Try solutions pages 1-3
        for pg in range(1, 4):
            url = f"https://leetcode.com/problems/coin-change/solutions/?page={pg}"
            print(f"\n=== Solutions page {pg} ===")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(6)
                links = page.query_selector_all("a")
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/solutions/" in str(href) and href.count("/") > 3:
                        full = "https://leetcode.com" + href if href.startswith("/") else href
                        if full not in all_solution_urls:
                            all_solution_urls.append(full)
                print(f"  Total unique URLs so far: {len(all_solution_urls)}")
            except Exception as e:
                print(f"  Error loading page {pg}: {e}")

        # Try discuss tab
        discuss_url = "https://leetcode.com/problems/coin-change/discuss/?currentPage=1&orderBy=newest_to_oldest&query=python"
        print(f"\n=== Discuss tab ===")
        try:
            page.goto(discuss_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(6)
            links = page.query_selector_all("a")
            for link in links:
                href = link.get_attribute("href")
                if href and "/discuss/" in str(href) and href.count("/") > 3:
                    full = "https://leetcode.com" + href if href.startswith("/") else href
                    if full not in all_solution_urls:
                        all_solution_urls.append(full)
            print(f"  Total unique URLs so far: {len(all_solution_urls)}")
        except Exception as e:
            print(f"  Error loading discuss: {e}")

        print(f"\n=== Extracting from {len(all_solution_urls)} URLs ===")

        saved = 0
        for i, url in enumerate(all_solution_urls):
            code = extract_python_solution(page, url, f"[{i+1}]")
            if code:
                approach = classify_solution(code)
                post_id = url.rstrip("/").split("/")[-1][:40]
                filename = f"{OUT_DIR}/lc_{post_id}.py"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(code)
                saved += 1
                print(f"  [{saved}] {approach}: {filename} ({len(code)} bytes)")

        print(f"\nTotal saved: {saved} files")
        browser.close()

if __name__ == "__main__":
    main()
