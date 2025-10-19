#!/usr/bin/env python3
"""
prereg_pack.py — build a Zenodo-ready zip with PDFs, scripts, manifest, reports, and figs.
Git-aware: If inside a Git repo, uses short commit hash as the tag by default.
Falls back to YYYYMMDD. You can override with --tag.

Usage:
  python scripts/prereg_pack.py --out dist/plr_prereg.zip
Options:
  --tag TAG            Override tag (default: git short hash or YYYYMMDD)
  --include-data       Include data/ directory (use with care; real data only).
  --name NAME          Base name (default: plr_prereg)
"""
import argparse, os, pathlib, zipfile, datetime, sys, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]

def detect_git_tag():
    try:
        # Ensure we run inside ROOT
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
    ap.add_argument("--tag", default=None)
    ap.add_argument("--include-data", action="store_true")
    ap.add_argument("--name", default="plr_prereg")
    args = ap.parse_args()

    tag = args.tag or detect_git_tag() or datetime.datetime.utcnow().strftime("%Y%m%d")
    base_name = f"{args.name}_{tag}.zip"
    out = pathlib.Path(args.out) if args.out else (ROOT / "dist" / base_name)
    out.parent.mkdir(parents=True, exist_ok=True)

    needed_files = ["main.pdf", "supplemental.pdf", "manifest.yaml", "Makefile", "latexmkrc", "plr.bib"]
    readmes = [p.name for p in ROOT.glob("README*")]
    needed_files.extend(readmes)

    missing = [f for f in ["main.pdf","supplemental.pdf"] if not (ROOT / f).exists()]
    if missing:
        print(f"[error] Missing built PDFs: {missing}. Run 'make release' first.", file=sys.stderr)
        sys.exit(1)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in needed_files:
            fp = ROOT / f
            if fp.exists():
                zf.write(fp, arcname=str(pathlib.Path("plr-prl") / f))
        # Include metadata files from dist/ if not already added from root
        dist_metadata = ["CITATION.cff", "zenodo.json", "README_packaging.md", "FILE_LISTING.txt"]
        for f in dist_metadata:
            if f not in needed_files:
                fp = ROOT / "dist" / f
                if fp.exists():
                    zf.write(fp, arcname=str(pathlib.Path("plr-prl") / f))
        rep = ROOT / "reports"
        if rep.exists():
            add_dir(zf, rep, pathlib.Path("plr-prl"))
        add_dir(zf, ROOT / "scripts", pathlib.Path("plr-prl"))
        figs = ROOT / "figs"
        if figs.exists():
            add_dir(zf, figs, pathlib.Path("plr-prl"), exclude_ext=(".png",".jpg",".jpeg"))
        if args.include_data and (ROOT / "data").exists():
            add_dir(zf, ROOT / "data", pathlib.Path("plr-prl"))

    print(f"[OK] wrote {out}")

if __name__ == "__main__":
    main()
