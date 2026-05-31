#!/usr/bin/env python3
"""
CLI for human review rejections.
Usage: python reject_candidate.py <artifact_path> --reason <string>

Logs rejection + moves artifact to candidates/rejected/.
No silent deletions — all removals must go through this script.
"""
import argparse
import json
import shutil
from pathlib import Path
from doctor.candidates.rejection_logger import maybe_write_rejection_log

REJECTED_DIR = Path(__file__).parent / "rejected"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_path", type=Path)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    if not args.artifact_path.exists():
        print(f"ERROR: artifact not found: {args.artifact_path}")
        raise SystemExit(1)

    with open(args.artifact_path) as f:
        artifact = json.load(f)

    context = {
        "problem_hash": artifact.get("_problem_hash", artifact.get("problem_hash", "")),
        "failed_axes": [],
        "completeness_score": artifact.get("spec", {}).get("completeness_score", 0.0),
        "artifact_path": str(args.artifact_path),
    }

    maybe_write_rejection_log(
        type('obj', (), {
            "eligible": False,
            "rejection_reason": args.reason,
            "failed_axes": [],
        })(),
        context=context,
        source="human_review",
        artifact_path=str(args.artifact_path),
    )

    REJECTED_DIR.mkdir(exist_ok=True)
    dest = REJECTED_DIR / args.artifact_path.name
    shutil.move(str(args.artifact_path), dest)
    print(f"Logged and moved -> {dest}")

if __name__ == "__main__":
    main()
