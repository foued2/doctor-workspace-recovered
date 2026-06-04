#!/usr/bin/env python3
"""Full pipeline test."""
import os
import sys

os.environ['GROQ_API_KEY'] = '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'
os.environ['LLM_PROVIDER'] = 'groq'

sys.path.insert(0, 'F:\\pythonProject1')

from doctor.core.test_executor import TestExecutor
from doctor.report_generator import generate_report
from doctor.analysis.solution_analyzer import analyze

executor = TestExecutor()

# Load user's regex matching solution
with open('F:\\pythonProject1\\solutions\\001 to 100\\10. Regular Expression Matching.py', 'r', encoding='utf-8', errors='replace') as f:
    code = f.read()

# Execute tests
report = executor.verify('regular_expression_matching', code)

# Analyze with LLM
class MockReport:
    pass
mock = MockReport()
mock.verdict = report.verdict
mock.pass_rate = report.pass_rate
mock.passed = report.passed
mock.total = report.total
mock.evidence_score = report.evidence_score
mock.results = report.results

diagnostic = analyze('Regular Expression Matching', code, mock)

# Generate report
output = generate_report('regular_expression_matching', report, diagnostic)
print(output)