"""Code extractor — extracts structural signature from solution code."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CodeSignature:
    function_names: list[str]
    class_names: list[str]
    import_count: int
    line_count: int
    has_loop: bool
    has_recursion: bool
    complexity_estimate: str  # "simple", "moderate", "complex"


def extract_code_signature(solution_code: str) -> Optional[CodeSignature]:
    """
    Extract structural signature from solution code.

    Returns CodeSignature or None if parsing fails.
    """
    try:
        tree = ast.parse(solution_code)
    except SyntaxError:
        return None

    function_names = []
    class_names = []
    import_count = 0
    has_loop = False
    has_recursion = False

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            class_names.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            import_count += 1
        elif isinstance(node, (ast.For, ast.While)):
            has_loop = True
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in function_names:
                    has_recursion = True

    line_count = len(solution_code.splitlines())

    if line_count < 10 and len(function_names) <= 1:
        complexity = "simple"
    elif line_count > 50 or len(function_names) > 3:
        complexity = "complex"
    else:
        complexity = "moderate"

    return CodeSignature(
        function_names=function_names,
        class_names=class_names,
        import_count=import_count,
        line_count=line_count,
        has_loop=has_loop,
        has_recursion=has_recursion,
        complexity_estimate=complexity,
    )
