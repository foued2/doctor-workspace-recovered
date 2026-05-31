"""
Audit N-Queens test suite and algorithm_completeness checker.
No fixes — just diagnosis.
"""
import sys
sys.path.insert(0, r'F:\pythonProject')

from doctor.test_executor import TestExecutor, TEST_SUITES, _results_equal
from doctor.code_analyzer import CodeAnalyzer

print("=" * 100)
print("PART 1: N-Queens Test Suite Audit")
print("=" * 100)

# Show the raw test cases
suites = TEST_SUITES.get("solve_n_queens", [])
print(f"\nN-Queens test suite ({len(suites)} cases):")
for i, tc in enumerate(suites):
    print(f"  [{i}] label={tc.label!r}, input={tc.input}, expected={tc.expected}")

# Now run each solution through L2 only
solutions = {
    "correct": """def solveNQueens(n):
    results = []
    def backtrack(row, cols, diag1, diag2, board):
        if row == n:
            results.append([''.join(r) for r in board])
            return
        for col in range(n):
            d1 = row - col
            d2 = row + col
            if col in cols or d1 in diag1 or d2 in diag2:
                continue
            cols.add(col)
            diag1.add(d1)
            diag2.add(d2)
            board[row][col] = 'Q'
            backtrack(row + 1, cols, diag1, diag2, board)
            board[row][col] = '.'
            cols.remove(col)
            diag1.remove(d1)
            diag2.remove(d2)
    board = [['.'] * n for _ in range(n)]
    backtrack(0, set(), set(), set(), board)
    return results""",
    
    "partial": """def solveNQueens(n):
    results = []
    def backtrack(row, cols, diag1, diag2, board):
        if row == n:
            results.append([''.join(r) for r in board])
            return True
        for col in range(n):
            d1 = row - col
            d2 = row + col
            if col in cols or d1 in diag1 or d2 in diag2:
                continue
            cols.add(col)
            diag1.add(d1)
            diag2.add(d2)
            board[row][col] = 'Q'
            if backtrack(row + 1, cols, diag1, diag2, board):
                return True
            board[row][col] = '.'
            cols.remove(col)
            diag1.remove(d1)
            diag2.remove(d2)
        return False
    board = [['.'] * n for _ in range(n)]
    backtrack(0, set(), set(), set(), board)
    return results""",
    
    "incorrect": """def solveNQueens(n):
    from itertools import permutations
    results = []
    for perm in permutations(range(n)):
        valid = True
        for i in range(n):
            for j in range(i + 1, n):
                if abs(perm[i] - perm[j]) == j - i:
                    valid = False
                    break
            if not valid:
                break
        if valid:
            board = [['.'] * n for _ in range(n)]
            for r, c in enumerate(perm):
                board[r][c] = 'Q'
            results.append([''.join(r) for r in board])
    return results""",
}

executor = TestExecutor()

for sol_type, code in solutions.items():
    print(f"\n{'─' * 100}")
    print(f"N-Queens {sol_type.upper()} solution — L2 execution detail")
    print(f"{'─' * 100}")
    report = executor.verify("N-Queens", code)
    print(f"  verdict={report.verdict}, pass_rate={report.pass_rate}")
    print(f"  severity={report.severity}, ratio={report.failure_ratio}")
    print(f"  core_fail={report.core_failures}, edge_fail={report.edge_failures}")
    for i, r in enumerate(report.results):
        status = "PASS" if r.passed else "FAIL"
        print(f"\n  [{status}] {r.label}:")
        print(f"    expected = {r.expected}")
        if r.got is not None:
            print(f"    got      = {r.got}")
            if r.got != r.expected:
                print(f"    MISMATCH: type(got)={type(r.got)}, type(expected)={type(r.expected)}")
                if isinstance(r.got, list) and isinstance(r.expected, list):
                    print(f"    len(got)={len(r.got)}, len(expected)={len(r.expected)}")
                    # Show actual comparison detail
                    eq = _results_equal(r.got, r.expected)
                    print(f"    _results_equal = {eq}")
        else:
            print(f"    got      = None")
            eq = _results_equal(None, r.expected)
            print(f"    _results_equal(None, expected) = {eq}")
        if r.error:
            print(f"    error    = {r.error}")

# Now test the zero case specifically
print(f"\n{'=' * 100}")
print("PART 2: Zero Case Deep Dive")
print(f"{'=' * 100}")

for sol_type, code in solutions.items():
    print(f"\n  {sol_type} solution, n=0:")
    namespace = {}
    namespace["ListNode"] = None  # dummy, not needed
    exec(code, namespace)
    func = namespace.get('solveNQueens')
    if func:
        result = func(0)
        print(f"    solveNQueens(0) = {result}")
        print(f"    type = {type(result)}")
        print(f"    len  = {len(result)}")
        expected = []  # from test suite
        print(f"    expected = {expected}")
        print(f"    match = {result == expected}")

# Check what algorithm_completeness does
print(f"\n{'=' * 100}")
print("PART 3: algorithm_completeness Checker Audit")
print(f"{'=' * 100}")

# Read the checker code
with open(r'F:\pythonProject\doctor\code_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find _check_algorithm_completeness
import re
match = re.search(r'def _check_algorithm_completeness\(.*?\n(.*?)(?=\n    def |\n    FATAL_CHECKS|\nclass |\Z)', content, re.DOTALL)
if match:
    print(f"\n  _check_algorithm_completeness source:")
    for line in match.group(0).split('\n'):
        print(f"    {line}")
else:
    print("  Could not find _check_algorithm_completeness in code_analyzer.py")

# Also show what FATAL_CHECKS / TRACK B contains
print(f"\n  Checking TRACK B / fatal checks in code_analyzer.py:")
match2 = re.search(r'(FATAL_CHECKS|TRACK_B|track_b|fatal_checks)\s*[=:]\s*(\{.*?\}|\[.*?\])', content, re.DOTALL)
if match2:
    print(f"    {match2.group(0)}")
else:
    print("    Not found as simple literal")

# Actually run each solution through L1 to see what fires
print(f"\n{'=' * 100}")
print("PART 4: L1 Analysis — What Fires for Each N-Queens Solution")
print(f"{'=' * 100}")

problem_text = "The n-queens puzzle is the problem of placing n queens on an n×n chessboard such that no two queens attack each other. Return all distinct solutions."

for sol_type, code in solutions.items():
    print(f"\n  {sol_type}:")
    analyzer = CodeAnalyzer()
    result = analyzer.analyze(problem_text, code, "N-Queens")
    print(f"    verdict     = {result.verdict}")
    print(f"    failures    = {result.failures}")
    if hasattr(result, 'fatal_flags') and result.fatal_flags:
        print(f"    fatal_flags = {result.fatal_flags}")
    # Show individual checker results
    if hasattr(result, 'details'):
        for key, val in result.details.items():
            if 'completeness' in key.lower() or 'algorithm' in key.lower() or 'constraint' in key.lower():
                print(f"    {key} = {val}")
