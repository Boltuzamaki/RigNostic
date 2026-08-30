"""Command-line entry point with explicit blocker reporting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .baseline.runner import run_benchmark
from .blender.runner import detect_blender, run_blender
from .config import load_config
from .discovery import build_inventory
from .evaluation.report import evaluate_saved
from .iteration_01.runner import run_benchmark as run_iteration_01
from .repair import heal_rig, plan_repairs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rignostic")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check local Stage 0 prerequisites")
    subparsers.add_parser("blender-version", help="test configured headless Blender")
    subparsers.add_parser("baseline-run", help="run all fixed Stage 0 benchmark cases")
    subparsers.add_parser("baseline-evaluate", help="evaluate saved results against private gold")
    subparsers.add_parser("baseline-all", help="run and evaluate all Stage 0 cases")
    inspect_parser = subparsers.add_parser("inspect", help="build an Iteration 1 RigInventory")
    inspect_parser.add_argument("blend_file", type=Path)
    inspect_parser.add_argument("--output", type=Path)
    subparsers.add_parser("iteration-01-run", help="run Structured Rig Discovery benchmark")
    subparsers.add_parser("iteration-01-evaluate", help="evaluate Iteration 1 results")
    subparsers.add_parser("iteration-01-all", help="run and evaluate Iteration 1")
    repair_parser = subparsers.add_parser("repair", help="plan or apply guarded repairs")
    repair_parser.add_argument("blend_file", type=Path)
    repair_parser.add_argument("--reference", type=Path, required=True)
    repair_parser.add_argument("--output", type=Path)
    repair_parser.add_argument("--apply", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    root = Path.cwd()
    if args.command == "repair":
        if args.apply and args.output is None:
            raise SystemExit("repair --apply requires --output")
        if args.output is not None and not args.apply:
            raise SystemExit("--output requires --apply")
        report = (
            heal_rig(args.blend_file, args.reference, args.output)
            if args.apply
            else plan_repairs(args.blend_file, args.reference)
        )
        print(json.dumps(report, indent=2))
        return 0
    if args.command == "inspect":
        inventory = build_inventory(args.blend_file.resolve()).to_dict()
        serialized = json.dumps(inventory, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        else:
            print(serialized, end="")
        return 0
    if args.command in {"iteration-01-run", "iteration-01-all"}:
        run_iteration_01(root, config)
        if args.command == "iteration-01-run":
            return 0
    if args.command in {"iteration-01-evaluate", "iteration-01-all"}:
        report = evaluate_saved(root, "iteration_01")
        print(json.dumps(report["aggregate"], indent=2))
        return 0
    if args.command in {"baseline-run", "baseline-all"}:
        run_benchmark(root, config)
        if args.command == "baseline-run":
            return 0
    if args.command in {"baseline-evaluate", "baseline-all"}:
        report = evaluate_saved(root)
        print(json.dumps(report["aggregate"], indent=2))
        return 0
    resolved = detect_blender(config.blender.executable)
    if args.command == "doctor":
        print(f"Blender: {resolved if resolved else 'NOT FOUND'}")
        return 0 if resolved else 1
    if resolved is None:
        print("Blender not found. Set BLENDER_EXECUTABLE to Blender 4.5.13 LTS.")
        return 1
    result = run_blender(executable=str(resolved))
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
