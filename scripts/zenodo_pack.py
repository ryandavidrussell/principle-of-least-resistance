#!/usr/bin/env python3
"""
zenodo_pack.py — produce a single Zenodo-ready archive including metadata stubs.
Git-aware tag (short hash), with fallback to YYYYMMDD. Optionally include raw data.

Usage:
  python scripts/zenodo_pack.py --out dist/plr_zenodo.zip [--include-data] [--tag TAG]

Contents:
  - PDFs: main.pdf, supplemental.pdf
  - Metadata: dist/CITATION.cff, dist/zenodo.json (if present)
  - Manifest + build files: manifest.yaml, Makefile, latexmkrc, plr.bib, README*
  - Reports/: CSV+MD summaries
  - Scripts/: builders and checks
  - Figs/: PDFs
  - Data/: (optional with --include-data)
"""
import argparse, os, pathlib, zipfile, subprocess, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

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
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__",) and not d.startswith(".")]
        for fn in filenames:
            if fn in exclude_names:
                continue
            if exclude_ext and any(fn.lower().endswith(ext.lower()) for ext in exclude_ext):
                continue
            full = pathlib.Path(dirpath) / fn
            arc = relroot / full.relative_to(ROOT)
            zf.write(full, arcname=str(arc))

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
        # Root build files
        for f in ["main.pdf","supplemental.pdf","manifest.yaml","Makefile","latexmkrc","plr.bib"]:
            fp = ROOT / f
            if fp.exists():
                zf.write(fp, arcname=str(pathlib.Path("plr-prl") / f))
        # README* (excluding README_packaging.md which comes from dist)
        for fp in ROOT.glob("README*"):
            if fp.name != "README_packaging.md":
                zf.write(fp, arcname=str(pathlib.Path("plr-prl") / fp.name))
        # Metadata from dist (with fallback for CITATION.cff)
        # CITATION.cff: prefer dist/, fallback to root
        citation_src = ROOT / "dist" / "CITATION.cff"
        if not citation_src.exists():
            citation_src = ROOT / "CITATION.cff"
        if citation_src.exists():
            zf.write(citation_src, arcname=str(pathlib.Path("plr-prl") / "CITATION.cff"))
        # Other dist metadata files
        for f in ["zenodo.json", "README_packaging.md", "FILE_LISTING.txt"]:
            fp = ROOT / "dist" / f
            if fp.exists():
                zf.write(fp, arcname=str(pathlib.Path("plr-prl") / f))
        # Reports, Scripts, Figs
        rep = ROOT / "reports"
        if rep.exists():
            add_dir(zf, rep, pathlib.Path("plr-prl"))
        scripts_dir = ROOT / "scripts"
        if scripts_dir.exists():
            add_dir(zf, scripts_dir, pathlib.Path("plr-prl"))
        figs = ROOT / "figs"
        if figs.exists():
            add_dir(zf, figs, pathlib.Path("plr-prl"), exclude_ext=(".png",".jpg",".jpeg"))
        # Data optional
        if args.include_data:
            data_dir = ROOT / "data"
            if data_dir.exists():
                add_dir(zf, data_dir, pathlib.Path("plr-prl"))

    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
