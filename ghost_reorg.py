#!/usr/bin/env python3
"""
ghost_reorg.py — one-command repo reorg + optional PR creation.

Default plan (idempotent):
- Move metadata -> dist/:       CITATION.cff, zenodo.json, README_packaging.md, FILE_LISTING.txt
- Move helper scripts -> scripts/: prereg_pack.py, zenodo_pack.py, zenodo_preflight.py,
                                  verify_archive.py, make_checksums.py, check_summary.py
- Move reports -> reports/:     check_summary.csv

Features:
- Dry run by default (prints a concise plan and a summary)
- Creates/switches branch
- Applies moves with git mv (preserves history)
- Commit message customization
- Optional push and PR creation (with GitHub CLI `gh`)
- `--preserve-paths`: if plan lists nested paths, keep them relative under the target dir
- Custom move plan via JSON/YAML
- Clear error reporting and outcome counts

Usage (dry run):
  ./ghost_reorg.py --repo ryandavidrussell/principle-of-least-resistance

Apply, push, open PR:
  ./ghost_reorg.py --repo ryandavidrussell/principle-of-least-resistance \
    --apply --push --open-pr

Common flags:
  --base main
  --branch reorganize/dist-scripts-reports
  --commit-message "chore: reorganize files into dist/, scripts/, and reports/"
  --title "chore: reorganize files into dist/, scripts/, and reports/"
  --body "This PR reorganizes the repository structure..."
  --preserve-paths
  --plan-file plan.json|yaml
  --force  (ignore dirty worktree)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# -------- Defaults --------

DEFAULT_MOVES = {
    "dist": [
        "CITATION.cff",
        "zenodo.json",
        "README_packaging.md",
        "FILE_LISTING.txt",
    ],
    "scripts": [
        "prereg_pack.py",
        "zenodo_pack.py",
        "zenodo_preflight.py",
        "verify_archive.py",
        "make_checksums.py",
        "check_summary.py",
    ],
    "reports": [
        "check_summary.csv",
    ],
}

DEFAULT_BRANCH = "reorganize/dist-scripts-reports"
DEFAULT_BASE = "main"

DEFAULT_COMMIT = "chore: reorganize files into dist/, scripts/, and reports/"
DEFAULT_TITLE = "chore: reorganize files into dist/, scripts/, and reports/"
DEFAULT_BODY = (
    "This PR reorganizes the repository structure to improve clarity and reproducibility.\n\n"
    "- Moved metadata files to dist/\n"
    "- Moved helper scripts to scripts/\n"
    "- Moved reports into reports/\n"
    "- Left top-level files (README, LICENSE, Makefile, CHANGELOG) untouched\n\n"
    "This matches the intended structure and makes it easier for referees and collaborators to navigate."
)

# -------- Helpers --------

def run(cmd, check=True, capture=False):
    kwargs = {}
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
        kwargs["text"] = True
    try:
        res = subprocess.run(cmd, check=check, **kwargs)
        if capture:
            return res.stdout.strip()
        return ""
    except subprocess.CalledProcessError as e:
        msg = e.stdout if hasattr(e, "stdout") and e.stdout else str(e)
        print(f"[fail] Command error: {' '.join(cmd)}\n{msg}", file=sys.stderr)
        if check:
            sys.exit(1)
        return ""

def git(*args, check=True, capture=False):
    return run(["git", *args], check=check, capture=capture)

def gh_present():
    try:
        run(["gh", "--version"], check=True)
        return True
    except Exception:
        return False

def ensure_clean_worktree(force=False):
    status = git("status", "--porcelain", capture=True)
    if status.strip() and not force:
        print("[fail] Working tree not clean. Commit/stash or use --force.", file=sys.stderr)
        sys.exit(1)

def ensure_branch(base, branch):
    current = git("rev-parse", "--abbrev-ref", "HEAD", capture=True)
    if current != base:
        git("checkout", base)
    branches = git("branch", "--list", branch, capture=True).splitlines()
    names = [b.strip().lstrip("* ") for b in branches]
    if branch in names:
        git("checkout", branch)
    else:
        git("checkout", "-b", branch)

def parse_plan_file(path):
    ext = Path(path).suffix.lower()
    text = Path(path).read_text(encoding="utf-8")
    if ext == ".json":
        return json.loads(text)
    # YAML optional
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except Exception:
        raise SystemExit(f"[fail] Could not parse {path}. Use JSON or install PyYAML for YAML.")

def printable_rel(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)

def move_target(folder: str, src_path: Path, preserve_paths: bool) -> Path:
    if preserve_paths:
        # Keep subpath (minus any leading ./)
        sub = Path(*src_path.parts)  # normalized copy
        return Path(folder) / sub
    # Flatten: only keep filename under target folder
    return Path(folder) / src_path.name

def plan_moves(plan: dict, preserve_paths: bool):
    """Return list of tuples (src_path, dst_path)."""
    moves = []
    for folder, files in plan.items():
        for f in files:
            src = Path(f)
            dst = move_target(folder, src, preserve_paths)
            moves.append((src, dst))
    return moves

def verify_sources(moves):
    missing = []
    for src, _ in moves:
        if not src.exists():
            missing.append(src)
    return missing

def print_dry_plan(moves):
    print("\n[plan] Proposed moves:")
    for src, dst in moves:
        exists = "✓" if src.exists() else "✗"
        print(f"  {exists} {printable_rel(src)}  →  {printable_rel(dst)}")
    print()  

def safe_git_mv(src: Path, dst: Path):
    # Return tuple (moved_bool, message)
    if not src.exists():
        return (False, f"[skip] {printable_rel(src)} (not found)")
    if dst.exists() and src.resolve() == dst.resolve():
        return (False, f"[ok] {printable_rel(src)} already at {printable_rel(dst)}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    git("mv", str(src), str(dst))
    return (True, f"[moved] {printable_rel(src)} → {printable_rel(dst)}")

# -------- Main --------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", help="owner/repo (used when opening PR with gh)")
    ap.add_argument("--base", default=DEFAULT_BASE)
    ap.add_argument("--branch", default=DEFAULT_BRANCH)
    ap.add_argument("--apply", action="store_true", help="perform moves (default is dry run)")
    ap.add_argument("--push", action="store_true", help="git push after commit")
    ap.add_argument("--open-pr", action="store_true", help="open PR with gh")
    ap.add_argument("--title", default=DEFAULT_TITLE)
    ap.add_argument("--body", default=DEFAULT_BODY)
    ap.add_argument("--commit-message", default=DEFAULT_COMMIT)
    ap.add_argument("--plan-file", help="JSON or YAML mapping {folder: [files...]}")
    ap.add_argument("--preserve-paths", action="store_true", help="keep nested paths inside target folders")
    ap.add_argument("--force", action="store_true", help="proceed even if worktree is dirty")
    args = ap.parse_args()

    # Load plan
    plan = parse_plan_file(args.plan_file) if args.plan_file else DEFAULT_MOVES
    moves = plan_moves(plan, preserve_paths=args.preserve_paths)

    # Preflight
    ensure_clean_worktree(force=args.force)
    ensure_branch(args.base, args.branch)

    # Dry-run preview
    print_dry_plan(moves)
    missing = verify_sources(moves)

    # Summary header
    if missing:
        print("[warn] Missing sources:")
        for m in missing:
            print(f"  - {printable_rel(m)}")

    moved_count = 0
    skipped_count = 0
    error_count = 0

    if not args.apply:
        # Dry-run only
        print("\n[summary] dry run (no changes applied)")
        print(f"  planned: {len(moves)}")
        print(f"  missing: {len(missing)}")
        print("Re-run with --apply to perform moves.")
        return

    # Apply moves
    for src, dst in moves:
        try:
            moved, msg = safe_git_mv(src, dst)
            print(msg)
            if moved:
                moved_count += 1
            else:
                # Determine skip vs ok
                if "not found" in msg:
                    error_count += 1
                else:
                    skipped_count += 1
        except Exception as e:
            print(f"[error] {printable_rel(src)} → {printable_rel(dst)}: {e}", file=sys.stderr)
            error_count += 1

    # Commit (only if anything changed)
    status = git("status", "--porcelain", capture=True)
    if status.strip():
        git("commit", "-m", args.commit_message)
        print("[ok] Commit created.")
    else:
        print("[note] No changes to commit (already organized).")

    # Push branch
    if args.push:
        git("push", "-u", "origin", args.branch)
        print(f"[ok] Pushed branch {args.branch}.")

    # Open PR
    if args.open_pr:
        if not gh_present():
            print("[warn] gh not found; skipping PR creation.", file=sys.stderr)
        else:
            cmd = [
                "gh", "pr", "create",
                "--title", args.title,
                "--body", args.body,
                "--base", args.base,
                "--head", args.branch,
            ]
            if args.repo:
                # Ensures PR targets the correct repo, even outside a cloned origin
                cmd.extend(["--repo", args.repo])
            run(cmd)
            print("[ok] Pull request opened.")

    # Final summary
    print("\n[summary] apply complete")
    print(f"  moved:   {moved_count}")
    print(f"  skipped: {skipped_count}")
    print(f"  errors:  {error_count}")
    print("[done] Ghost run complete.")

if __name__ == "__main__":
    main()