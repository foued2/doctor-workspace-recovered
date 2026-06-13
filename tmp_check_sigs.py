import os, re, glob

hs_dir = 'human_solvers'
for py_file in glob.glob(os.path.join(hs_dir, '**', '*.py'), recursive=True):
    if '__pycache__' in py_file or 'debug' in py_file or 'source_urls' in py_file:
        continue
    with open(py_file, 'r', encoding='utf-8') as f:
        code = f.read()
    
    funcs = re.findall(r'def\s+(\w+)\s*\(', code)
    classes = re.findall(r'class\s+(\w+)', code)
    rel = os.path.relpath(py_file, hs_dir)
    
    has_solve = 'def solve' in code
    has_coinChange = 'def coinChange' in code
    has_class = len(classes) > 0
    
    print(f"{rel}: solve={has_solve}, coinChange={has_coinChange}, class={has_class}, funcs={funcs[:5]}, classes={classes[:3]}")
