import json, sys
sys.path.insert(0, '.')
from doctor.adversarial.lc79_ground_truth import lc79_brute_force

probes = [
    # --- Category 1: Non-obvious paths (not left-to-right top row) ---
    {
        "probe_id": "p_lc79_001",
        "family": "non_obvious_path",
        "axis": "path_finding",
        "board": [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]],
        "word": "ABCCED",
        "expected": True,
        "note": "Path goes down then right then up — not top-row traversal"
    },
    {
        "probe_id": "p_lc79_002",
        "family": "non_obvious_path",
        "axis": "path_finding",
        "board": [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]],
        "word": "SEE",
        "expected": True,
        "note": "Path requires going down and left"
    },
    {
        "probe_id": "p_lc79_003",
        "family": "non_obvious_path",
        "axis": "path_finding",
        "board": [["C","A","A"],["A","A","A"],["B","C","D"]],
        "word": "AAB",
        "expected": True,
        "note": "Multiple A's — path must navigate correctly"
    },
    {
        "probe_id": "p_lc79_004",
        "family": "non_obvious_path",
        "axis": "path_finding",
        "board": [["A","B","C","D"],["E","F","G","H"],["I","J","K","L"]],
        "word": "ABCDEFGHIJKL",
        "expected": True,
        "note": "Snake path through entire grid"
    },
    {
        "probe_id": "p_lc79_005",
        "family": "non_obvious_path",
        "axis": "path_finding",
        "board": [["X","A","X"],["A","A","A"],["X","A","X"]],
        "word": "AAA",
        "expected": True,
        "note": "Cross pattern — must avoid revisiting"
    },

    # --- Category 2: Word almost exists but backtracks at final character ---
    {
        "probe_id": "p_lc79_006",
        "family": "near_miss",
        "axis": "backtracking",
        "board": [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]],
        "word": "ABCB",
        "expected": False,
        "note": "ABCB — C->B requires revisiting, impossible"
    },
    {
        "probe_id": "p_lc79_007",
        "family": "near_miss",
        "axis": "backtracking",
        "board": [["A","B","C","D"],["E","F","G","H"],["I","J","K","L"]],
        "word": "ABCDHGF",
        "expected": False,
        "note": "Almost snake but requires impossible backtrack"
    },
    {
        "probe_id": "p_lc79_008",
        "family": "near_miss",
        "axis": "backtracking",
        "board": [["A","B","C"],["D","E","F"],["G","H","I"]],
        "word": "ABEHG",
        "expected": False,
        "note": "Path exists to ABHE but not AB EHG"
    },
    {
        "probe_id": "p_lc79_009",
        "family": "near_miss",
        "axis": "backtracking",
        "board": [["A","B","C","D"],["E","F","G","H"],["I","J","K","L"]],
        "word": "ABFGK",
        "expected": False,
        "note": "B->F->G then can't reach K without revisiting"
    },
    {
        "probe_id": "p_lc79_010",
        "family": "near_miss",
        "axis": "backtracking",
        "board": [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]],
        "word": "ABCEF",
        "expected": False,
        "note": "A->B->C->E but F not adjacent to E"
    },

    # --- Category 3: Repeated characters requiring correct visited tracking ---
    {
        "probe_id": "p_lc79_011",
        "family": "repeated_chars",
        "axis": "visited_tracking",
        "board": [["A","A","A","A"],["A","A","A","A"],["A","A","A","A"]],
        "word": "AAAAAAAAAAAA",
        "expected": True,
        "note": "All same — path must snake without revisiting"
    },
    {
        "probe_id": "p_lc79_012",
        "family": "repeated_chars",
        "axis": "visited_tracking",
        "board": [["A","A","A","A"],["A","B","B","A"],["A","A","A","A"]],
        "word": "ABBBAAAA",
        "expected": True,
        "note": "Must go around the B island"
    },
    {
        "probe_id": "p_lc79_013",
        "family": "repeated_chars",
        "axis": "visited_tracking",
        "board": [["A","B","A","B"],["B","A","B","A"],["A","B","A","B"]],
        "word": "ABABABABA",
        "expected": True,
        "note": "Checkerboard — long alternating path"
    },
    {
        "probe_id": "p_lc79_014",
        "family": "repeated_chars",
        "axis": "visited_tracking",
        "board": [["A","A","A","A","A"],["A","B","B","B","A"],["A","A","A","B","A"]],
        "word": "AABBBAAAA",
        "expected": True,
        "note": "Must enter B region and exit correctly"
    },
    {
        "probe_id": "p_lc79_015",
        "family": "repeated_chars",
        "axis": "visited_tracking",
        "board": [["A","B","C","D"],["B","C","D","A"],["C","D","A","B"]],
        "word": "ABCDBCDA",
        "expected": False,
        "note": "Repeats require revisiting — impossible"
    },

    # --- Category 4: Large grids (6x6+) stressing recursion depth ---
    {
        "probe_id": "p_lc79_016",
        "family": "large_grid",
        "axis": "recursion_depth",
        "board": [
            ["A","B","C","D","E","F"],
            ["G","H","I","J","K","L"],
            ["M","N","O","P","Q","R"],
            ["S","T","U","V","W","X"],
            ["Y","Z","A","B","C","D"],
            ["E","F","G","H","I","J"]
        ],
        "word": "ABCDEFGHIJKLMNOPQRSTUVWX",
        "expected": True,
        "note": "Snake through 6x6 grid (24 chars)"
    },
    {
        "probe_id": "p_lc79_017",
        "family": "large_grid",
        "axis": "recursion_depth",
        "board": [
            ["A","B","C","D","E","F"],
            ["F","E","D","C","B","A"],
            ["A","B","C","D","E","F"],
            ["F","E","D","C","B","A"],
            ["A","B","C","D","E","F"],
            ["F","E","D","C","B","A"]
        ],
        "word": "ABCDEFABCDEFABCDEF",
        "expected": True,
        "note": "Zigzag through 6x6"
    },
    {
        "probe_id": "p_lc79_018",
        "family": "large_grid",
        "axis": "recursion_depth",
        "board": [
            ["A","A","A","A","A","A"],
            ["A","A","A","A","A","A"],
            ["A","A","A","A","A","A"],
            ["A","A","A","A","A","A"],
            ["A","A","A","A","A","A"],
            ["A","A","A","A","A","A"]
        ],
        "word": "AAAAAAAAAA",
        "expected": True,
        "note": "6x6 all A's, short word"
    },
    {
        "probe_id": "p_lc79_019",
        "family": "large_grid",
        "axis": "recursion_depth",
        "board": [
            ["A","B","C","D","E","F"],
            ["G","H","I","J","K","L"],
            ["M","N","O","P","Q","R"],
            ["S","T","U","V","W","X"],
            ["Y","Z","A","B","C","D"],
            ["E","F","G","H","I","J"]
        ],
        "word": "ABCDEFGHIJKLmnopqrstuvwxyz",
        "expected": False,
        "note": "Lowercase not in grid"
    },
    {
        "probe_id": "p_lc79_020",
        "family": "large_grid",
        "axis": "recursion_depth",
        "board": [
            ["A","B","C","D","E","F","G","H"],
            ["I","J","K","L","M","N","O","P"],
            ["Q","R","S","T","U","V","W","X"]
        ],
        "word": "ABCDEFGHIJKLMNOPQRSTUVWX",
        "expected": True,
        "note": "3x8 grid snake"
    },

    # --- Category 5: Words not present at all ---
    {
        "probe_id": "p_lc79_021",
        "family": "word_absent",
        "axis": "exhaustive_search",
        "board": [["A","B","C"],["D","E","F"],["G","H","I"]],
        "word": "ABCDEFGHI",
        "expected": True,
        "note": "All 9 chars snake through"
    },
    {
        "probe_id": "p_lc79_022",
        "family": "word_absent",
        "axis": "exhaustive_search",
        "board": [["A","B","C"],["D","E","F"],["G","H","I"]],
        "word": "AEIM",
        "expected": False,
        "note": "Diagonal — not adjacent"
    },
    {
        "probe_id": "p_lc79_023",
        "family": "word_absent",
        "axis": "exhaustive_search",
        "board": [["A","B","C"],["D","E","F"],["G","H","I"]],
        "word": "ABCABC",
        "expected": False,
        "note": "Repeats A,B,C — requires revisit"
    },
    {
        "probe_id": "p_lc79_024",
        "family": "word_absent",
        "axis": "exhaustive_search",
        "board": [["A","B","C","D"],["E","F","G","H"]],
        "word": "ABCDEFGH",
        "expected": True,
        "note": "2x4 grid snake"
    },
    {
        "probe_id": "p_lc79_025",
        "family": "word_absent",
        "axis": "exhaustive_search",
        "board": [["A","B","C","D"],["E","F","G","H"]],
        "word": "ABCDEFGHGFEDCBA",
        "expected": False,
        "note": "Long palindrome — can't traverse back"
    },

    # --- Category 6: Edge cases ---
    {
        "probe_id": "p_lc79_026",
        "family": "edge_case",
        "axis": "boundary",
        "board": [["a"]],
        "word": "a",
        "expected": True,
        "note": "Single cell match"
    },
    {
        "probe_id": "p_lc79_027",
        "family": "edge_case",
        "axis": "boundary",
        "board": [["a"]],
        "word": "b",
        "expected": False,
        "note": "Single cell no match"
    },
    {
        "probe_id": "p_lc79_028",
        "family": "edge_case",
        "axis": "boundary",
        "board": [["a","b"],["c","d"]],
        "word": "abdc",
        "expected": True,
        "note": "2x2 grid full traversal"
    },
    {
        "probe_id": "p_lc79_029",
        "family": "edge_case",
        "axis": "boundary",
        "board": [["a","b","c"],["d","e","f"],["g","h","i"]],
        "word": "abehifedcba",
        "expected": False,
        "note": "3x3 long path with backtrack"
    },
    {
        "probe_id": "p_lc79_030",
        "family": "edge_case",
        "axis": "boundary",
        "board": [["A","B","C"],["B","D","B"],["C","B","A"]],
        "word": "ABCBDAB",
        "expected": True,
        "note": "Classic backtracking — must find non-obvious path"
    },
]

# Verify all probes with oracle
print("Verifying all 30 probes with lc79_brute_force oracle:")
print("=" * 60)

all_pass = True
for i, p in enumerate(probes):
    board_copy = [row[:] for row in p["board"]]
    result = lc79_brute_force(board_copy, p["word"])
    status = "PASS" if result == p["expected"] else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{i+1:2d}] {p['probe_id']}: {status} (expected={p['expected']}, got={result}) | {p['note']}")

print()
print(f"Result: {'ALL PASS' if all_pass else 'SOME FAILED'}")

# Save probe index
import os
os.makedirs("data", exist_ok=True)
with open("data/midweather_fingerprint_lc79_probe_index.json", "w") as f:
    json.dump({"problem": "LC79", "num_probes": len(probes), "probes": probes}, f, indent=2)
print(f"Saved probe index to data/midweather_fingerprint_lc79_probe_index.json")
