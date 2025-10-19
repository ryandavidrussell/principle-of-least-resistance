#!/usr/bin/env python3
"""
make_checksums.py — create a SHA256 manifest for the prereg/Zenodo bundle.
By default mirrors the *no-data* packaging (scripts, reports, figs PDFs, root files).
Use --include-data to include data/ checksums (for *-data* bundles).

Example:
  python scripts/make_checksums.py --out reports/checksums_SHA256.txt
  python scripts/make_checksums.py --include-data --out reports/checksums_SHA256_data.txt
"""
import argparse, os, pathlib, hashlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

ROOT_FILES = {"main.pdf","supplemental.pdf","manifest.yaml","Makefile","latexmkrc","plr.bib"}

def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def should_skip(path: pathlib.Path) -> bool:
    # skip dist, .git, cachey dirs, and TeX aux
    parts = set(path.parts)
    if "dist" in parts or ".git" in parts or "__pycache__" in parts:
        return True
    name = path.name
    if name.startswith(".DS_Store"):
        return True
    extskip = (".aux",".log",".out",".toc",".gz",".synctex",".synctex.gz",".tmp")
    if path.suffix in extskip:
        return True
    return False

def gather(include_data=False):
    files = []
    # Root files
    for f in ROOT_FILES:
        p = ROOT / f
        if p.exists() and p.is_file():
            files.append(p)
    # README*
    for p in ROOT.glob("README*"):
        if p.is_file():
            files.append(p)
    # scripts (all)
    for p in (ROOT / "scripts").rglob("*"):
        if p.is_file() and not should_skip(p):
            files.append(p)
    # reports (all)
    rep = ROOT / "reports"
    if rep.exists():
        for p in rep.rglob("*"):
            if p.is_file() and not should_skip(p):
                files.append(p)
    # figs (pdf only)
    figs = ROOT / "figs"
    if figs.exists():
        for p in figs.rglob("*.pdf"):
            if p.is_file() and not should_skip(p):
                files.append(p)
    # data optional
    if include_data and (ROOT / "data").exists():
        for p in (ROOT / "data").rglob("*"):
            if p.is_file() and not should_skip(p):
                files.append(p)
    # de-dup & sort
    uniq = sorted(set(files), key=lambda x: str(x))
    return uniq

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-data", action="store_true", help="Include data/ directory")
    ap.add_argument("--out", default="reports/checksums_SHA256.txt")
    args = ap.parse_args()

    files = gather(include_data=args.include_data)
    if not files:
        print("[fail] no files gathered (did you build PDFs?)", file=sys.stderr)
        sys.exit(1)

    outpath = ROOT / args.out
    outpath.parent.mkdir(parents=True, exist_ok=True)

    with open(outpath, "w", encoding="utf-8") as fh:
        fh.write("# SHA256 checksums (relative to plr-prl/)\n")
        for p in files:
            rel = p.relative_to(ROOT)
            digest = sha256_of(p)
            fh.write(f"{digest}  {rel}\n")

    print(f"[ok] wrote {outpath} ({len(files)} files)")

if __name__ == "__main__":
    main()
