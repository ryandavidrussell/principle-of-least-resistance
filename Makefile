

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


PYTHON ?= python3

.PHONY: sync-citation prereg-pack prereg-pack-data zenodo-pack zenodo-pack-data verify-archive

sync-citation:
	@mkdir -p dist
	@cp -f CITATION.cff dist/CITATION.cff
	@printf "[ok] synced CITATION.cff → dist/CITATION.cff\n"

prereg-pack: sync-citation
	@$(PYTHON) scripts/prereg_pack.py || true

prereg-pack-data: sync-citation
	@$(PYTHON) scripts/prereg_pack.py --include-data || true

zenodo-pack: sync-citation
	@$(PYTHON) scripts/zenodo_pack.py || true

zenodo-pack-data: sync-citation
	@$(PYTHON) scripts/zenodo_pack.py --include-data || true

verify-archive:
	@$(PYTHON) scripts/verify_archive.py dist/*.zip || true


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
