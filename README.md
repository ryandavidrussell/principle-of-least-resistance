# Principle of Least Resistance (PLR)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![CI](https://github.com/ryandavidrussell/principle-of-least-resistance/actions/workflows/build-and-release.yml/badge.svg)](https://github.com/ryandavidrussell/principle-of-least-resistance/actions)

*A Universal Log-Periodic Signal in Fundamental Physics*

---

## Overview

This repository hosts the reproducibility kit for the Principle of Least Resistance (PLR) framework —  
a proposed unifying dynamical principle in physics that predicts universal log-periodic structures.  

The repo provides:
- LaTeX manuscripts and appendices
- Figure definitions and data pipelines
- Packaging scripts for preregistration and Zenodo archives
- Integrity manifests and CI workflows

Its purpose is to make every result in the PLR framework **transparent, reproducible, and falsifiable**.

---

## Quick Start

```bash
make prereg-pack         # prereg bundle (no raw data)
make prereg-pack-data    # prereg bundle (with raw data)
make zenodo-pack         # Zenodo bundle (no raw data)
make zenodo-pack-data    # Zenodo bundle (with raw data)
make verify-archive      # verify archive integrity

---

## About `.gitmore`

Alongside the standard `.gitignore`, this repository includes a `.gitmore` file.

- `.gitignore` tells Git what to **exclude** (build artifacts, caches, etc.).
- `.gitmore` is purely informational: it lists the **canonical, reproducible files** that define the project.

This helps collaborators, referees, and future maintainers quickly identify what matters:
- Source code (`src/`, `scripts/`)
- Figures (`figs/`)
- Packaging instructions (`Makefile`, `dist/README_packaging.md`)
- Metadata (`dist/CITATION.cff`, `dist/zenodo.json`)
- Reproducibility manifests (`reports/`)

In short, `.gitmore` is a **roadmap of the core, reproducible elements**.

---

## How to Cite

If you use this work, please cite it as:

```bibtex
@misc{russell2025plr,
  author       = {Ryan D. Russell},
  title        = {The Principle of Least Resistance: A Unified Framework for Physics from First Principles},
  year         = {2025},
  publisher    = {Zenodo},
  version      = {v0.1.0},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}

---

That will complete your README so it matches the “polished” version we planned: badges → overview → quick start → `.gitmore` → citation → license → contributing → acknowledgments.  

Want me to stitch the **whole thing into one clean file** for you so you can just replace `README.md` in your repo, instead of pasting it in chunks?