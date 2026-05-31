#!/usr/bin/env python3
"""Run Phase 4 Batch 3 through unified engine."""
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import os


def main():
    os.environ["OPENROUTER_API_KEY"] = "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"
    os.environ["LLM_PROVIDER"] = "openrouter"
    
    from doctor.ingest.unified_engine import analyze_statement
    
    with open("phase4_batch3.json") as f:
        cases = json.load(f)
    
    results = []
    for case in cases:
        stmt = case["statement"]
        e_type = case.get("expected_type", "")
        
        print(f"Running {case['id']}...")
        
        result = {"id": case["id"], "statement": stmt, "expected_type": e_type}
        
        try:
            analysis = analyze_statement(stmt)
            result["status"] = analysis.get("status")
            result["failure_tag"] = analysis.get("failure_tag")
            result["matched"] = analysis.get("matched")
            result["matcher_diagnostic_score"] = analysis.get("matcher_diagnostic_score")
            result["constraint_consistency"] = analysis.get("constraint_consistency")
            result["structural_compatibility"] = analysis.get("structural_compatibility")
            
            trace = analysis.get("decision_trace", {})
            result["retry_count"] = trace.get("retry_count")
            result["provider"] = trace.get("provider")
            
            print(f"  -> {analysis.get('status')} ({analysis.get('matched')})")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            result["status"] = "error"
            result["error"] = str(e)
        
        results.append(result)
    
    with open("phase4_batch3_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults written to phase4_batch3_results.json")
    
    accept_count = sum(1 for r in results if r.get("status") == "success")
    reject_count = sum(1 for r in results if r.get("status") == "rejected")
    print(f"Accepts: {accept_count}, Rejects: {reject_count}")


if __name__ == "__main__":
    main()
