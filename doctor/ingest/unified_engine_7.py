import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
from doctor.ingest.unified_engine import analyze_statement


BATCH_PATH = Path("phase4_nearmiiss_batch.json")
RESULTS_PATH = Path("phase4_nearmiss_results.json")


def main() -> None:
    cases = json.loads(BATCH_PATH.read_text(encoding="utf-8"))
    results = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']}", flush=True)
        analysis = analyze_statement(case["statement"])
        results.append(
            {
                "id": case["id"],
                "statement": case["statement"],
                "expected_type": case["expected_type"],
                "expected_match_candidate": case["expected_match_candidate"],
                "near_miss_reason": case["near_miss_reason"],
                **analysis,
            }
        )

    RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {RESULTS_PATH}", flush=True)


if __name__ == "__main__":
    main()
