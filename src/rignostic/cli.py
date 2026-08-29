"""Command-line entry point with explicit blocker reporting."""

from __future__ import annotations

import argparse
from pathlib import Path

from .blender.runner import detect_blender, run_blender
from .config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rignostic")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("doctor", help="check local Stage 0 prerequisites")
    subparsers.add_parser("blender-version", help="test configured headless Blender")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
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
