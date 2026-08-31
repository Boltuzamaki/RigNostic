#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
archive_dir="$repo_root/dist"
staging_dir="$(mktemp -d)"
archive_path="$archive_dir/rignostic-submission.zip"
trap 'rm -rf "$staging_dir"' EXIT

mkdir -p "$archive_dir"
(cd "$repo_root" && git ls-files --cached --others --exclude-standard -z) |
  tar -C "$repo_root" --null -T - -cf - |
  tar -xf - -C "$staging_dir"
(cd "$staging_dir" && zip -qr "$archive_path" .)
printf '%s\n' "$archive_path"
