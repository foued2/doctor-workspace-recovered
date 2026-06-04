"""doctor-certify CLI: thin wrapper around the Midweather-Fingerprint-Gate kernel.

The four subcommands (run, validate-freeze, validate-manifest, list) and the
exit code policy (0=PASS, 1=FAIL, 2=REFUSED, 3=ERROR) are declared in
docs/CLI_SCOPE.md. This module implements the surface; the runner
delegation uses ``runners.run_midweather_fingerprint_lc322.main`` directly
(per docs/CLI_SCOPE.md: "no logic duplication").

The ``run`` subcommand reads the result JSON to determine the exit code
(since the runner's main() returns None; a future commit refactors the
runner to return an int directly).
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Sequence

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_REFUSED = 2
EXIT_ERROR = 3

REGISTERED_PROBLEM_CLASSES: list[str] = ["lc322", "lc45"]


def _find_project_root(start: Path) -> Path:
    """Walk up from ``start`` looking for pyproject.toml; return the directory.

    Used to locate the ``runners/`` directory and the project-root data
    files (freeze, manifest, probe_index) when the package is installed
    in development mode (``pip install -e .``).
    """
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    return start.parents[2]


PROJECT_ROOT = _find_project_root(Path(__file__).resolve())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="doctor-certify",
        description="Clean-gate protocol for LLM solver certification (Midweather-Fingerprint-Gate).",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    run_p = subparsers.add_parser(
        "run", help="Run the protocol for a problem class; write the result JSON."
    )
    run_p.add_argument(
        "--problem-class", default="lc322", choices=REGISTERED_PROBLEM_CLASSES,
        help="Problem class to evaluate (default: lc322).",
    )
    run_p.add_argument("--freeze", type=Path, help="Override the freeze path.")
    run_p.add_argument("--probe-index", type=Path, help="Override the probe_index path.")
    run_p.add_argument("--seval-manifest", type=Path, help="Override the seval_manifest path.")
    run_p.add_argument("--solvers-dir", type=Path, help="Override the solvers directory.")
    run_p.add_argument("--output", type=Path, help="Override the result output path.")
    run_p.set_defaults(func=run_command)

    vf_p = subparsers.add_parser(
        "validate-freeze", help="Run the 7 freeze validators against a freeze file."
    )
    vf_p.add_argument("--freeze", type=Path, required=True, help="Path to the freeze file.")
    vf_p.set_defaults(func=validate_freeze_command)

    vm_p = subparsers.add_parser(
        "validate-manifest", help="Validate a S_eval manifest against the schema + freeze tie."
    )
    vm_p.add_argument("--seval-manifest", type=Path, required=True, help="Path to the S_eval manifest.")
    vm_p.add_argument("--freeze", type=Path, required=True, help="Path to the freeze file (for the freeze tie check).")
    vm_p.set_defaults(func=validate_manifest_command)

    list_p = subparsers.add_parser(
        "list", help="List registered problem classes and their 6 adapter slot fills."
    )
    list_p.set_defaults(func=list_command)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return EXIT_ERROR
    except SystemExit as e:
        if isinstance(e.code, int):
            return e.code
        return EXIT_ERROR
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return EXIT_ERROR


def _build_runner_argv(args: argparse.Namespace) -> list[str]:
    argv: list[str] = [f"--problem-class={args.problem_class}"]
    if args.freeze is not None:
        argv.append(f"--freeze={args.freeze}")
    if args.probe_index is not None:
        argv.append(f"--probe-index={args.probe_index}")
    if args.seval_manifest is not None:
        argv.append(f"--seval-manifest={args.seval_manifest}")
    if args.solvers_dir is not None:
        argv.append(f"--solvers-dir={args.solvers_dir}")
    if args.output is not None:
        argv.append(f"--output={args.output}")
    return argv


def _resolve_freeze_path(args: argparse.Namespace) -> Path:
    if args.freeze is not None:
        return args.freeze
    from runners.run_midweather_fingerprint_lc322 import _paths_for
    return _paths_for(args.problem_class)["freeze"]


def _check_freeze_id_match(freeze: dict, problem_class: str) -> str | None:
    expected_prefix = f"midweather_fingerprint_{problem_class}_"
    freeze_id = freeze.get("freeze_id", "")
    if not freeze_id.startswith(expected_prefix):
        return (
            f"freeze_id_mismatch: freeze declares {freeze_id!r}, "
            f"problem_class is {problem_class!r} (expected prefix {expected_prefix!r})"
        )
    return None


def run_command(args: argparse.Namespace) -> int:
    freeze_path = _resolve_freeze_path(args)
    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: freeze_not_found: {freeze_path}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        print(f"ERROR: freeze_invalid_json: {e}", file=sys.stderr)
        return EXIT_ERROR

    mismatch = _check_freeze_id_match(freeze, args.problem_class)
    if mismatch is not None:
        print(f"ERROR: {mismatch}", file=sys.stderr)
        return EXIT_ERROR

    from runners import run_midweather_fingerprint_lc322 as runner
    return runner.main(_build_runner_argv(args))


def validate_freeze_command(args: argparse.Namespace) -> int:
    from doctor.adversarial.midweather_fingerprint_features import clean_run_refusal_reasons
    try:
        freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: freeze_not_found: {args.freeze}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        print(f"ERROR: freeze_invalid_json: {e}", file=sys.stderr)
        return EXIT_ERROR

    freeze_id = freeze.get("freeze_id", "")
    parts = freeze_id.split("_")
    if len(parts) < 3 or parts[0] != "midweather" or parts[1] != "fingerprint":
        print(f"ERROR: cannot_extract_problem_class: freeze_id={freeze_id!r}", file=sys.stderr)
        return EXIT_ERROR
    problem_class = parts[2]

    from runners.run_midweather_fingerprint_lc322 import _paths_for
    paths = _paths_for(problem_class)
    seval_manifest_path = paths["seval_manifest"]
    probe_index_path = paths["probe_index"]

    try:
        seval_manifest = json.loads(seval_manifest_path.read_text(encoding="utf-8"))
        probe_index = json.loads(probe_index_path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        print(f"ERROR: file_not_found: {e.filename}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid_json: {e}", file=sys.stderr)
        return EXIT_ERROR

    reasons = clean_run_refusal_reasons(
        seval_manifest=seval_manifest,
        freeze=freeze,
        repo_root=PROJECT_ROOT,
        decision_spec=freeze.get("decision_spec", {}),
        probe_index=probe_index,
        freeze_id=freeze_id,
    )
    if reasons:
        for reason in reasons:
            print(f"REFUSED: freeze_validation: {reason}", file=sys.stderr)
        return EXIT_REFUSED
    print("PASS: all 7 freeze validators passed")
    return EXIT_PASS


def validate_manifest_command(args: argparse.Namespace) -> int:
    from doctor.adversarial.midweather_fingerprint_features import (
        SevalManifestValidationError,
        assert_valid_seval_manifest,
    )
    try:
        freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
        manifest = json.loads(args.seval_manifest.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        print(f"ERROR: file_not_found: {e.filename}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid_json: {e}", file=sys.stderr)
        return EXIT_ERROR

    try:
        assert_valid_seval_manifest(manifest, freeze)
    except SevalManifestValidationError as e:
        print(f"REFUSED: manifest_certification: {e}", file=sys.stderr)
        return EXIT_REFUSED
    print("PASS: manifest is valid (schema + freeze tie + certification)")
    return EXIT_PASS


def _slot_lines(problem_id: str, config: Any) -> list[str]:
    lines: list[str] = [f"  problem_class: {problem_id}"]
    oracle_name = getattr(config.oracle, "__qualname__", None) or type(config.oracle).__name__
    lines.append(f"    slot 1 (oracle):                       {oracle_name}")
    lines.append(f"    slot 2 (probe_to_solver_input):        {config.probe_to_solver_input.__name__}")
    lines.append(f"    slot 3 (solver_entry_point):           {config.solver_entry_point}")
    n_est = len(config.estimator_names)
    lines.append(f"    slot 4 (estimator_names):              {', '.join(config.estimator_names)} (n={n_est})")
    n_policies = len(config.estimator_policies)
    lines.append(f"    slot 4b (estimator_policies):          {n_policies} policies across {n_est} estimators")
    lines.append(f"    slot 5 (fingerprint_axes):             {', '.join(config.fingerprint_axes)} (n={len(config.fingerprint_axes)})")
    lines.append(f"    slot 6 (raw_tensor_encoder):           {config.raw_tensor_encoder.__name__}")
    return lines


def list_command(args: argparse.Namespace) -> int:
    from doctor.adversarial.problem_class_config import get_problem_class_config
    print("Registered problem classes")
    print("=" * 40)
    for problem_id in REGISTERED_PROBLEM_CLASSES:
        config = get_problem_class_config(problem_id)
        for line in _slot_lines(problem_id, config):
            print(line)
        print()
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
