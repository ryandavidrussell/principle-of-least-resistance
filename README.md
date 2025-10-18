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

Clone the repository and build the preregistration and Zenodo bundles:

```bash
make prereg-pack         # prereg bundle (no raw data)
make prereg-pack-data    # prereg bundle (with raw data)
make zenodo-pack         # Zenodo bundle (no raw data)
make zenodo-pack-data    # Zenodo bundle (with raw data)


@misc{russell2025plr,
  author       = {Ryan D. Russell},
  title        = {The Principle of Least Resistance: A Unified Framework for Physics from First Principles},
  year         = {2025},
  publisher    = {Zenodo},
  version      = {v0.1.0},
  doi          = {10.5281/zenodo.XXXXXXX},
  url          = {https://doi.org/10.5281/zenodo.XXXXXXX}
}