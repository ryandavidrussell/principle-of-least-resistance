#!/usr/bin/env python3
"""
verify_archive.py — verify that packaged zip archive contents match SHA256 manifest(s).
Reads checksums from reports/checksums_SHA256*.txt and compares to extracted files inside the given zip.

Usage:
  python scripts/verify_archive.py dist/plr_zenodo_<tag>.zip
  python scripts/verify_archive.py dist/*.zip
"""
import sys
import pathlib
import zipfile
import hashlib
import glob

ROOT = pathlib.Path(__file__).resolve().parents[1]

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def load_manifest(lines):
    checksums = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            digest, rel = parts[0], parts[-1]
            checksums[rel] = digest
    return checksums

def verify_archive(archive_path):
    """Verify a single archive against manifests. Returns True if OK, False otherwise."""
    archive = pathlib.Path(archive_path)
    if not archive.is_file():
        print(f"[fail] archive {archive} not found", file=sys.stderr)
        return False
    
    # locate manifest(s)
    reports_dir = ROOT / 'reports'
    manfiles = []
    if reports_dir.exists():
        for pattern in ["checksums_SHA256.txt", "checksums_SHA256_data.txt"]:
            manifest = reports_dir / pattern
            if manifest.is_file():
                manfiles.append(manifest)
    
    if not manfiles:
        print(f"[fail] no checksum manifests found in {reports_dir}", file=sys.stderr)
        return False
    
    # combine
    all_checksums = {}
    for mf in manfiles:
        with open(mf, "r", encoding="utf-8") as fh:
            all_checksums.update(load_manifest(fh.readlines()))
    
    # open archive
    zf = zipfile.ZipFile(archive, "r")
    ok_all = True
    verified_count = 0
    failed_count = 0
    
    for rel, digest in all_checksums.items():
        arcname = str(pathlib.Path("plr-prl") / rel)
        try:
            data = zf.read(arcname)
        except KeyError:
            print(f"[fail] missing {arcname} in archive")
            ok_all = False
            failed_count += 1
            continue
        got = sha256_bytes(data)
        if got != digest:
            print(f"[fail] checksum mismatch for {arcname}")
            ok_all = False
            failed_count += 1
        else:
            print(f"[ok] {arcname}")
            verified_count += 1
    zf.close()
    
    # Print summary for this archive
    if ok_all:
        print(f"Summary for {archive.name}: ✓ {verified_count} files verified")
    else:
        print(f"Summary for {archive.name}: ✗ {failed_count} failed, {verified_count} ok")
    
    return ok_all

def main():
    if len(sys.argv) < 2:
        print("Usage: verify_archive.py <archive.zip> [<archive2.zip> ...]", file=sys.stderr)
        sys.exit(1)
    
    # Collect all archive paths (expand globs if needed)
    archives = []
    for arg in sys.argv[1:]:
        # Support shell expansion by expanding globs
        expanded = glob.glob(arg)
        if expanded:
            archives.extend(expanded)
        else:
            # If no glob match, use the arg as-is (might be a direct path)
            archives.append(arg)
    
    if not archives:
        print("[fail] no archives specified", file=sys.stderr)
        sys.exit(1)
    
    all_ok = True
    for archive in archives:
        print(f"\n=== Verifying {archive} ===")
        ok = verify_archive(archive)
        all_ok = all_ok and ok
    
    if all_ok:
        print("\n[ok] all archives verified")
        sys.exit(0)
    else:
        print("\n[fail] one or more archives failed verification")
        sys.exit(1)

if __name__ == "__main__":
    main()
