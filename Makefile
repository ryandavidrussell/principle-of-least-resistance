

# --- CI / Check-only targets ---
check-only: verify
	@echo "[check-only] running strict checks and summary (no plotting)"
	$(PYTHON) $(CHECKER) --manifest $(MANIFEST) --min-points 8 --min-span 0.5 --sigma-min 1e-6
	$(PYTHON) scripts/check_summary.py --manifest $(MANIFEST) --out reports/check_summary.csv

ci: check-only
	@echo "[ci] summary written to reports/check_summary.csv"


# Generate CSV + Markdown dataset summary (no plotting)
markdown-summary: verify
	@echo "[markdown-summary] writing reports/check_summary.csv and .md"
	$(PYTHON) scripts/check_summary.py --manifest $(MANIFEST) --out reports/check_summary.csv --markdown
	@echo "[done] see reports/check_summary.csv and reports/check_summary.md"


# Sync root CITATION.cff into dist/
.PHONY: sync-citation
sync-citation:
	@mkdir -p dist
	@cp -f CITATION.cff dist/CITATION.cff
	@printf "[ok] synced CITATION.cff → dist/CITATION.cff\n"


# Package a Zenodo-ready prereg archive (excludes raw data by default)
prereg-pack: release markdown-summary checksums sync-citation
	@echo "[prereg] packaging PDFs + scripts + manifest + reports + figs (no raw data)"
	$(PYTHON) scripts/prereg_pack.py --out dist/plr_prereg.zip
	$(MAKE) verify-archive
	@echo "[done] prereg archive built and verified"


# Package including raw data (use with care). Uses git hash or date tag automatically.
prereg-pack-data: release markdown-summary checksums-data sync-citation
	@echo "[prereg] packaging WITH raw data (ensure only real, public-safe CSVs are included)"
	$(PYTHON) scripts/prereg_pack.py --include-data --name plr_prereg_data
	$(MAKE) verify-archive
	@echo "[done] prereg data archive built and verified"


# Zenodo-ready bundle (includes metadata stubs from dist/)
zenodo-pack: release markdown-summary preflight checksums sync-citation
	@echo "[zenodo] packaging Zenodo-ready archive (no raw data)"
	$(PYTHON) scripts/zenodo_pack.py
	$(MAKE) verify-archive
	@echo "[done] dist archive built and verified"

zenodo-pack-data: release markdown-summary preflight checksums-data sync-citation
	@echo "[zenodo] packaging Zenodo-ready archive WITH raw data"
	$(PYTHON) scripts/zenodo_pack.py --include-data
	$(MAKE) verify-archive
	@echo "[done] dist archive (with data) built and verified"


# Metadata preflight (CITATION.cff + zenodo.json)
preflight:
	@echo "[preflight] validating dist/CITATION.cff and dist/zenodo.json"
	$(PYTHON) scripts/zenodo_preflight.py


# Checksums (light = no data; data = include raw CSVs)
checksums:
	@echo "[checksums] computing SHA256 manifest (no data)"
	$(PYTHON) scripts/make_checksums.py --out reports/checksums_SHA256.txt

checksums-data:
	@echo "[checksums-data] computing SHA256 manifest (WITH data)"
	$(PYTHON) scripts/make_checksums.py --include-data --out reports/checksums_SHA256_data.txt


# Verify packaged archive against checksum manifest(s)
verify-archive:
	@echo "[verify] checking dist/*.zip against manifests"
	@for f in dist/*.zip; do \
	  echo "[verify] $$f"; \
	  $(PYTHON) scripts/verify_archive.py $$f || exit 1; \
	done
