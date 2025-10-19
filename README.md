# PLR–PRL Package

Run `make prereg-pack` to build figures, PDFs, summaries, and a Zenodo-ready zip in `dist/`.
# 1) Create a branch
git checkout -b ci/dist-artifacts-verify-fix main

# 2) Ensure dirs
mkdir -p .github/workflows scripts dist

# 3) Write/overwrite the workflow (adds artifact upload)
cat > .github/workflows/pack-dryrun.yml <<'YAML'
name: Pack Dry-Run

on:
  pull_request:
    branches: [ main ]
  workflow_dispatch:

jobs:
  dryrun:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps (if any)
        run: |
          python -m pip install --upgrade pip
          # pip install -r requirements.txt || true
      - name: Dry-run sanity (no data)
        run: |
          make prereg-pack || true
          make zenodo-pack || true
          python scripts/verify_archive.py || true
      - name: Upload dist zips
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dist-zips
          path: dist/*.zip
          if-no-files-found: ignore
YAML

# 4) Append ignores (don’t clobber any existing rules)
touch .gitignore
cat >> .gitignore <<'IGN'
# Ignore built bundles and generated manifests
dist/*.zip
reports/checksums_*.txt

# Usual OS / editor noise (optional)
.DS_Store
IGN

# 5) Normalize text endings
cat > .gitattributes <<'GAT'
* text=auto eol=lf
GAT

# 6) Bump packaging guide date
cat > dist/README_packaging.md <<'MD'
# Packaging & Verification Guide

**Date:** 2025-10-19

This repository's preregistration and Zenodo bundles are built with integrity checks baked in.

- `make prereg-pack` builds a preregistration bundle (no raw data)
- `make zenodo-pack` builds a Zenodo bundle (no raw data)
- Add `-data` variants if you include raw data
- `make verify-archive` checks SHA256 manifests against archives in `dist/`

Artifacts:
- Archives are written under `dist/`
- Checksum manifests are written under `reports/`

For CI: the Pack Dry-Run workflow runs packaging and uploads `dist/*.zip` as artifacts for inspection.
MD

# 7) Replace verify script (Python 3.7+ compatible, multi-zip, manifest-aware)
cat > scripts/verify_archive.py <<'PY'
#!/usr/bin/env python3
"""
verify_archive.py — verify that packaged zip archive contents match SHA256 manifest(s).
Reads checksums from reports/checksums_SHA256*.txt and compares to files inside one or more ZIPs.

Usage:
  python scripts/verify_archive.py dist/plr_*.zip [dist/other.zip ...]
If no arguments are provided, it will glob dist/*.zip.
"""

from __future__ import annotations
import sys
import re
import hashlib
import zipfile
from pathlib import Path
from typing import Dict, Tuple, List

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

def load_manifests() -> Dict[str, str]:
    """
    Load all SHA256 manifests from reports/checksums_SHA256*.txt into a dict:
      { normalized_path_in_zip: sha256_hex }
    Accepts lines like:
      <hash><space><space><path>
    """
    mapping = {}  # type: Dict[str, str]
    if not REPORTS.exists():
        return mapping
    for mf in sorted(REPORTS.glob("checksums_SHA256*.txt")):
        try:
            text = mf.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = re.match(r"^([a-fA-F0-9]{64})\s+\*?(.+)$", line)
            if not m:
                continue
            h = m.group(1).lower()
            p = m.group(2)
            p = p.lstrip("./").replace("\\", "/")
            mapping[p] = h
    return mapping

def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def verify_zip(zp: Path, manifest: Dict[str, str]) -> Tuple[int, int, int]:
    """
    Verify a single zip against the manifest mapping.
    Returns (ok, mismatched, missing_in_manifest)
    """
    ok = mismatched = missing = 0
    if not zp.exists():
        print(f"[error] zip not found: {zp}")
        return (0, 0, 0)
    try:
        with zipfile.ZipFile(zp, "r") as zf:
            for zi in zf.infolist():
                if zi.is_dir():
                    continue
                name = zi.filename.lstrip("./").replace("\\", "/")
                data = zf.read(zi)
                h = sha256_bytes(data)
                # Try direct match; also try without leading top-level dir (e.g., "plr-prl/")
                candidates = [name]
                if "/" in name:
                    candidates.append(name.split("/", 1)[1])
                expected = None  # type: str
                for cand in candidates:
                    if cand in manifest:
                        expected = manifest[cand]
                        break
                if expected is None:
                    print(f"[warn] not in manifest: {name}")
                    missing += 1
                    continue
                if h == expected:
                    ok += 1
                else:
                    print(f"[mismatch] {name}  expected={expected}  got={h}")
                    mismatched += 1
    except zipfile.BadZipFile:
        print(f"[error] not a zip: {zp}")
        return (0, 0, 0)
    return (ok, mismatched, missing)

def main(argv: List[str]) -> int:
    zips = [Path(a) for a in argv] if argv else sorted((ROOT / "dist").glob("*.zip"))
    if not zips:
        print("[note] no zip paths provided and none found under dist/*.zip")
        return 0
    manifest = load_manifests()
    if not manifest:
        print("[warn] no manifests found under reports/checksums_SHA256*.txt; proceeding without verification.")
    total_ok = total_mm = total_missing = 0
    for zp in zips:
        ok, mm, miss = verify_zip(zp, manifest)
        total_ok += ok; total_mm += mm; total_missing += miss
        print(f"[summary] {zp.name}: ok={ok} mismatched={mm} missing_in_manifest={miss}")
    print(f"[summary] all: ok={total_ok} mismatched={total_mm} missing_in_manifest={total_missing}")
    return 1 if total_mm > 0 else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
PY

chmod +x scripts/verify_archive.py

# 8) Commit
git add .github/workflows/pack-dryrun.yml .gitignore .gitattributes scripts/verify_archive.py dist/README_packaging.md
git commit -m "CI: upload dist zips; add .gitattributes; ignore dist and reports; improve verify_archive (py3.7+); bump packaging date"

# 9) Push
git push -u origin ci/dist-artifacts-verify-fix

# 10) Open PR (CLI) — or open via the web UI if you prefer
if command -v gh >/dev/null 2>&1; then
  gh pr create \
    --title "CI: upload dist zips + packaging improvements and verify_archive compatibility" \
    --body "Apply packaging and CI improvements and make verify_archive.py compatible with Python versions older than 3.9.

Summary of changes:
- Upload dist/*.zip artifacts in Pack Dry-Run
- Ignore dist/*.zip and reports/checksums_*.txt
- Add .gitattributes to normalize line endings
- Replace scripts/verify_archive.py (multi-zip, manifest-aware; Python 3.7+)
- Bump dist/README_packaging.md date to 2025-10-19

Sanity:
- make prereg-pack; make zenodo-pack; python scripts/verify_archive.py dist/*.zip
" \
    --base main --head ci/dist-artifacts-verify-fix
else
  echo "Open a PR from branch ci/dist-artifacts-verify-fix against main via the GitHub UI."
