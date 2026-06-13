import json, os, time
from playwright.sync_api import sync_playwright

SUBMISSIONS = {
    "1061A": [
        370702072, 364587022, 364586911, 357646847, 356680082,
        353777390, 348730210, 347729881, 347729645, 347727935,
        347726858, 347201261, 347200947, 347198627, 340637608,
        339499484, 339498274, 339496368, 338009263, 337980567,
        332067688, 311019469, 309484175, 309483136, 302633574,
        301995233, 301994099,
    ],
    "1934B": [
        377799902, 372984409, 372983148, 372982798, 372982350,
        372855088, 363913074, 345753172, 343975142, 343973781,
        343924840, 342147752, 327945510,
    ],
}

OUT_DIR = "human_solvers"

def extract_source(page, url, sub_id):
    page.goto(url, wait_until="networkidle", timeout=30000)
    # Codeforces renders source in a <pre id="program-source-text"> element
    el = page.query_selector("#program-source-text")
    if el:
        return el.inner_text()
    # Fallback: look for <pre class="source">
    el = page.query_selector("pre.source")
    if el:
        return el.inner_text()
    return None

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {"downloaded": [], "failed": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for contest, ids in SUBMISSIONS.items():
            for sub_id in ids:
                url = f"https://codeforces.com/contest/{contest}/submission/{sub_id}"
                try:
                    source = extract_source(page, url, sub_id)
                    if source and len(source.strip()) > 10:
                        fname = f"{OUT_DIR}/cf_{contest}_{sub_id}.py"
                        with open(fname, "w", encoding="utf-8") as f:
                            f.write(source)
                        results["downloaded"].append(sub_id)
                        print(f"OK: {sub_id} ({len(source)} bytes)")
                    else:
                        results["failed"].append({"id": sub_id, "reason": "no source found"})
                        print(f"FAIL: {sub_id} (no source)")
                except Exception as e:
                    results["failed"].append({"id": sub_id, "reason": str(e)})
                    print(f"FAIL: {sub_id} ({e})")
                time.sleep(1.5)  # rate limit

        browser.close()

    print(f"\nDone: {len(results['downloaded'])} downloaded, {len(results['failed'])} failed")
    with open(f"{OUT_DIR}/download_report.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()
