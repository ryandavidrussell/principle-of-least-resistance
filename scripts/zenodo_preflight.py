#!/usr/bin/env python3
"""
zenodo_preflight.py — sanity-check metadata files before packaging for Zenodo.
- Validates presence and required fields in dist/CITATION.cff (YAML) and dist/zenodo.json (JSON).
- Prints clear [ok]/[warn]/[fail] lines and exits nonzero on failure.
"""
import sys, os, json, yaml

def ok(msg): print(f"[ok] {msg}")
def warn(msg): print(f"[warn] {msg}")
def fail(msg): print(f"[fail] {msg}")

def validate_citation(path):
    if not os.path.isfile(path):
        fail(f"Missing {path}")
        return False
    try:
        with open(path, "r", encoding="utf-8") as fh:
            cff = yaml.safe_load(fh)
    except Exception as e:
        fail(f"CITATION.cff parse error: {e}")
        return False
    required = ["cff-version","title","authors","date-released","license"]
    ok_all = True
    for k in required:
        if k not in cff:
            fail(f"CITATION.cff missing field: {k}"); ok_all=False
    # authors checks
    if "authors" in cff:
        if not isinstance(cff["authors"], list) or not cff["authors"]:
            fail("CITATION.cff 'authors' must be a non-empty list"); ok_all=False
        else:
            a0 = cff["authors"][0]
            if "family-names" not in a0 or "given-names" not in a0:
                fail("CITATION.cff first author must include family-names and given-names"); ok_all=False

    # Check affiliation in authors
    if "authors" in cff:
        for a in cff["authors"]:
            if not a.get("affiliation"):
                fail("CITATION.cff author missing affiliation"); ok_all=False

    # DOI placeholder warning
    if str(cff.get("doi","")).endswith("XXXXXXX"):
        warn("CITATION.cff DOI is a placeholder; update after Zenodo assigns DOI")
    ok("CITATION.cff parsed")
    return ok_all

def validate_zenodo(path):
    if not os.path.isfile(path):
        fail(f"Missing {path}")
        return False
    try:
        meta = json.load(open(path, "r", encoding="utf-8"))
    except Exception as e:
        fail(f"zenodo.json parse error: {e}")
        return False
    required = ["title","upload_type","description","creators","license","access_right"]
    ok_all = True
    for k in required:
        if k not in meta:
            fail(f"zenodo.json missing field: {k}"); ok_all=False
    # creators shape
    if "creators" in meta:
        if not isinstance(meta["creators"], list) or not meta["creators"]:
            fail("zenodo.json 'creators' must be a non-empty list"); ok_all=False
        else:
            c0 = meta["creators"][0]
            if "name" not in c0:
                fail("zenodo.json first creator must have 'name'"); ok_all=False

    # Check affiliation in creators
    if "creators" in meta:
        for c in meta["creators"]:
            if not c.get("affiliation"):
                fail("zenodo.json creator missing affiliation"); ok_all=False

    # upload_type sanity
    allowed_upload = {"publication","dataset","software","poster","presentation","image","video","lesson","physicalobject","other"}
    if meta.get("upload_type") not in allowed_upload:
        warn("zenodo.json upload_type is unusual; verify with Zenodo docs")
    # license hint
    if meta.get("license","").upper() in {"CC0","CC-BY","MIT","BSD-3-CLAUSE","GPL-3.0"}:
        ok("zenodo.json license looks standard")
    ok("zenodo.json parsed")
    return ok_all

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cit = os.path.join(root, "dist", "CITATION.cff")
    zen = os.path.join(root, "dist", "zenodo.json")
    ok_cit = validate_citation(cit)
    ok_zen = validate_zenodo(zen)
    if ok_cit and ok_zen:
        ok("Preflight passed")
        sys.exit(0)
    else:
        fail("Preflight failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
