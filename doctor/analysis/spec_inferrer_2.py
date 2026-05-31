import json
import sys
sys.path.insert(0, r'F:\pythonProject1')

from doctor.analysis.spec_inferrer import infer_spec, SpecHypothesis

# Test on 5 problems - we need statement + code for each
with open(r'F:\pythonProject1\doctor\registry\problem_registry.json', encoding='utf-8') as f:
    reg = json.load(f)

# Get 5 representative problems
ids = ['1', '3', '2', '11', '204']
for pid in ids:
    entry = reg.get(pid)
    if not entry:
        print(f"\nPROBLEM {pid}: NOT IN REGISTRY")
        continue
    
    spec = entry.get('spec', {})
    statement = spec.get('description', '')
    ref_solution = spec.get('reference_solution', '')
    
    print(f"\n{'='*10} PROBLEM {pid} ({spec.get('display_name', 'unknown')}) {'='*10}")
    print('statement (first 100 chars):', statement[:100])
    
    # Build execution traces from test cases
    test_cases = entry.get('execution', {}).get('test_cases', [])
    print(f'test_cases count: {len(test_cases)}')
    
    # Create mock traces for infer_spec
    traces = []
    for tc in test_cases[:3]:  # First 3 test cases
        inp = tc.get('input', ())
        expected = tc.get('expected')
        traces.append({
            'input': inp if isinstance(inp, (list, tuple)) else (inp,),
            'output': expected,
            'error': None
        })
    
    print('Calling infer_spec...')
    try:
        result = infer_spec(statement, ref_solution, traces)
        print('SpecHypothesis fields:')
        print('  inferred_input_schema:', json.dumps(result.inferred_input_schema))
        print('  inferred_output_shape:', result.inferred_output_shape)
        print('  constraint_hypotheses:', json.dumps(result.constraint_hypotheses))
        print('  ambiguity_flags:', result.ambiguity_flags)
        print('  completeness_score:', result.completeness_score)
        print('  canonical_form:', result.canonical_form[:100] if result.canonical_form else None)
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
