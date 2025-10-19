#!/usr/bin/env python3
"""
check_summary.py — emit CSV or Markdown summary of dataset stats.

Now supports --markdown flag to also emit a GitHub/LaTeX-ready table (pipe syntax).
"""
import argparse, sys, os, math, csv
import numpy as np
import pandas as pd
import yaml

FIELDS = ["input","kind","n","min_u","max_u","span_u","mean_abs_r","max_abs_r","var_r","min_sigma","max_sigma","has_nan","monotonic_u"]

def stats_for(path):
    df = pd.read_csv(path)
    u = df["u"].to_numpy(float)
    r = df["residual"].to_numpy(float)
    s = df["sigma"].to_numpy(float)
    has_nan = (not np.isfinite(u).all()) or (not np.isfinite(r).all()) or (not np.isfinite(s).all())
    n = int(u.size)
    min_u = float(np.min(u)) if n else float("nan")
    max_u = float(np.max(u)) if n else float("nan")
    span_u = float(max_u - min_u) if n else float("nan")
    mean_abs_r = float(np.nanmean(np.abs(r))) if n else float("nan")
    max_abs_r = float(np.nanmax(np.abs(r))) if n else float("nan")
    var_r = float(np.nanvar(r)) if n else float("nan")
    min_sigma = float(np.nanmin(s)) if n else float("nan")
    max_sigma = float(np.nanmax(s)) if n else float("nan")
    monotonic_u = bool(np.all(np.diff(u) >= 0))
    return dict(n=n, min_u=min_u, max_u=max_u, span_u=span_u,
                mean_abs_r=mean_abs_r, max_abs_r=max_abs_r, var_r=var_r,
                min_sigma=min_sigma, max_sigma=max_sigma,
                has_nan=has_nan, monotonic_u=monotonic_u)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--markdown", action="store_true", help="Emit markdown table too")
    args = ap.parse_args()

    man = yaml.safe_load(open(args.manifest, "r", encoding="utf-8"))
    figs = man.get("figures", [])
    rows = []
    for spec in figs:
        path = spec.get("input")
        kind = spec.get("kind", "")
        if not path or not os.path.isfile(path):
            continue
        st = stats_for(path)
        rows.append({"input": path, "kind": kind, **st})

    # CSV out
    writer = csv.DictWriter(sys.stdout, fieldnames=FIELDS)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    if args.out:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            writer2 = csv.DictWriter(fh, fieldnames=FIELDS)
            writer2.writeheader()
            for row in rows:
                writer2.writerow(row)

    if args.markdown:
        md_lines = []
        header = "|" + "|".join(FIELDS) + "|"
        sep = "|" + "|".join(["---"]*len(FIELDS)) + "|"
        md_lines.append(header)
        md_lines.append(sep)
        for row in rows:
            vals = [str(row.get(f,"")) for f in FIELDS]
            md_lines.append("|" + "|".join(vals) + "|")
        md_text = "\n".join(md_lines)
        sys.stderr.write("\n[markdown]\n" + md_text + "\n")
        if args.out:
            md_path = os.path.splitext(args.out)[0] + ".md"
            with open(md_path,"w",encoding="utf-8") as fh:
                fh.write(md_text)

if __name__ == "__main__":
    main()
