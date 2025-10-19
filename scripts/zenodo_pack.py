#!/usr/bin/env python3
"""
zenodo_pack.py — produce a single Zenodo-ready archive including metadata stubs.
Git-aware tag (short hash), with fallback to YYYYMMDD. Optionally include raw data.

Usage:
  python scripts/zenodo_pack.py --out dist/plr_zenodo.zip [--include-data] [--tag TAG]

Contents:
  - PDFs: main.pdf, supplemental.pdf
  - Metadata: dist/CITATION.cff, dist/zenodo.json, dist/FILE_LISTING.txt, dist/README_packaging.md
  - Manifest + build files: manifest.yaml, Makefile, latexmkrc, plr.bib, README*
  - Reports/: CSV+MD summaries
  - Scripts/: builders and checks
  - Figs/: PDFs
  - Data/: (optional with --include-data)
"""
import argparse, pathlib, zipfile, subprocess, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

def maybe_add(zf, src, arcname):
    """Add file to archive if it exists."""
    if src.exists():
        zf.write(src, arcname=str(arcname))
        return True
    return False

def detect_git_tag():
    try:
        res = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        if res.stdout.strip() != "true":
            return None
        res2 = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True
        )
        return res2.stdout.strip()
    except Exception:
        return None

def add_dir(zf, base, relroot, exclude_ext=(), exclude_names=()):
    """Recursively add directory contents to archive."""
    base_path = pathlib.Path(base)
    if not base_path.exists():
        return
    for item in base_path.rglob("*"):
        if item.is_file():
            # Skip hidden files and __pycache__
            if any(part.startswith(".") or part == "__pycache__" for part in item.parts):
                continue
            if item.name in exclude_names:
                continue
            if exclude_ext and any(item.name.lower().endswith(ext.lower()) for ext in exclude_ext):
                continue
            arc = relroot / item.relative_to(ROOT)
            zf.write(item, arcname=str(arc))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--include-data", action="store_true")
    ap.add_argument("--tag", default=None)
    args = ap.parse_args()

    tag = args.tag or detect_git_tag() or datetime.datetime.utcnow().strftime("%Y%m%d")
    base_name = f"plr_zenodo_{tag}.zip"
    out = pathlib.Path(args.out) if args.out else (ROOT / "dist" / base_name)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Require PDFs
    missing = [f for f in ["main.pdf","supplemental.pdf"] if not (ROOT / f).exists()]
    if missing:
        print(f"[error] Missing built PDFs: {missing}. Run 'make release' first.", file=sys.stderr)
        sys.exit(1)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        arcroot = pathlib.Path("plr-prl")
        
        # Root build files
        for f in ["main.pdf", "supplemental.pdf", "manifest.yaml", "Makefile", "latexmkrc", "plr.bib"]:
            maybe_add(zf, ROOT / f, arcroot / f)
        
        # README*
        for fp in ROOT.glob("README*"):
            maybe_add(zf, fp, arcroot / fp.name)
        
        # Metadata from dist/ with fallbacks
        # CITATION.cff: prefer dist/CITATION.cff, fall back to root/CITATION.cff
        if not maybe_add(zf, ROOT / "dist" / "CITATION.cff", arcroot / "CITATION.cff"):
            maybe_add(zf, ROOT / "CITATION.cff", arcroot / "CITATION.cff")
        
        # Other metadata files from dist/
        maybe_add(zf, ROOT / "dist" / "zenodo.json", arcroot / "zenodo.json")
        maybe_add(zf, ROOT / "dist" / "README_packaging.md", arcroot / "README_packaging.md")
        maybe_add(zf, ROOT / "dist" / "FILE_LISTING.txt", arcroot / "FILE_LISTING.txt")
        
        # Reports, Scripts, Figs
        add_dir(zf, ROOT / "reports", arcroot)
        add_dir(zf, ROOT / "scripts", arcroot)
        add_dir(zf, ROOT / "figs", arcroot, exclude_ext=(".png", ".jpg", ".jpeg"))
        
        # Data optional
        if args.include_data:
            add_dir(zf, ROOT / "data", arcroot)

    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
