# Packaging & Verification Guide

**Date:** 2025-10-18

This repository's preregistration and Zenodo bundles are built with integrity checks baked in.

## Build Targets

- `make prereg-pack` — light prereg archive (no raw data)
- `make prereg-pack-data` — prereg archive with raw data
- `make zenodo-pack` — Zenodo-ready archive with metadata, no raw data
- `make zenodo-pack-data` — Zenodo-ready archive with metadata and raw data

All four targets **auto-run verification** after packaging. The build fails if any checksum mismatch is found.

## Checksums

Two checksum manifests are produced under `reports/`:

- `reports/checksums_SHA256.txt` (no data)
- `reports/checksums_SHA256_data.txt` (with data)

Each line has the format:

```
<sha256-digest>  <relative-path>
```

## Verifying Archives

To re-check integrity of packaged archives:

```bash
make verify-archive
```

This recomputes SHA256 hashes for all files inside `dist/*.zip` and compares them to the manifests.

Alternatively, verify manually with `sha256sum`:

```bash
sha256sum -c reports/checksums_SHA256.txt
# or, if data included:
sha256sum -c reports/checksums_SHA256_data.txt
```

The commands will print `[ok]` for each file if the archive is consistent.

## Notes for Reviewers

- Archives only display "built and verified" on success.
- Metadata (`CITATION.cff`, `zenodo.json`) must pass the `make preflight` checks before Zenodo packaging.
- Integrity can be re-confirmed at any time by re-running `make verify-archive`.

