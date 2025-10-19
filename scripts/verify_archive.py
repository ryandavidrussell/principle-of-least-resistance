#!/usr/bin/env python3
"""
verify_archive.py — verify that packaged zip archive contents match SHA256 manifest(s).
Reads checksums from reports/checksums_SHA256*.txt and compares to extracted files inside the given zip.

Usage:
  python scripts/verify_archive.py dist/plr_zenodo_<tag>.zip
"""
import sys, os, pathlib, zipfile, hashlib

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def load_manifest(lines):
    checksums = {}
    for line in lines:
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        parts=line.split()
        if len(parts)>=2:
            digest, rel = parts[0], parts[-1]
            checksums[rel] = digest
    return checksums

def main():
    if len(sys.argv)<2:
        print("Usage: verify_archive.py <archive.zip>", file=sys.stderr)
        sys.exit(1)
    archive=sys.argv[1]
    if not os.path.isfile(archive):
        print(f"[fail] archive {archive} not found", file=sys.stderr)
        sys.exit(1)
    # locate manifest(s)
    manfiles=[]
    for fn in ("reports/checksums_SHA256.txt","reports/checksums_SHA256_data.txt"):
        if os.path.isfile(fn):
            manfiles.append(fn)
    if not manfiles:
        print("[fail] no checksum manifests found", file=sys.stderr)
        sys.exit(1)
    # combine
    all_checksums={}
    for mf in manfiles:
        with open(mf,"r",encoding="utf-8") as fh:
            all_checksums.update(load_manifest(fh.readlines()))
    # open archive
    zf=zipfile.ZipFile(archive,"r")
    ok_all=True
    for rel,digest in all_checksums.items():
        arcname=str(pathlib.Path("plr-prl")/rel)
        try:
            data=zf.read(arcname)
        except KeyError:
            print(f"[fail] missing {arcname} in archive"); ok_all=False; continue
        got=sha256_bytes(data)
        if got!=digest:
            print(f"[fail] checksum mismatch for {arcname}"); ok_all=False
        else:
            print(f"[ok] {arcname}")
    zf.close()
    if ok_all:
        print("[ok] archive verified")
        sys.exit(0)
    else:
        print("[fail] archive verification failed")
        sys.exit(1)

if __name__=="__main__":
    main()
