#!/usr/bin/env python3
"""Fetch NIST OSCAL base schemas reproducibly from a pinned release.

Implements OSCAL4Rail ADR-008: the NIST base schemas are never hand-copied.
They are downloaded from a pinned OSCAL release tag and verified against a
committed SHA256 manifest, so the base schema is always reproducible from the
current OSCAL version.

The pinned version lives in schemas/nist/manifest.json (single source of truth).
NIST base schemas are written to schemas/nist/ (this dir), kept separate from the
additive OSCAL4Rail constraints in schemas/oscal4rail/ — we DERIVE from these,
we do not edit them.

Usage:
    python3 tools/fetch_oscal_schemas.py                 # fetch + verify all schemas
    python3 tools/fetch_oscal_schemas.py --verify-only   # verify existing files offline (CI)
    python3 tools/fetch_oscal_schemas.py --update-manifest # re-fetch and rewrite checksums (version bump)

Dependencies: Python 3.10+ standard library only (urllib, hashlib, json).
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

NIST_DIR = Path(__file__).resolve().parent.parent / "schemas" / "nist"
MANIFEST = NIST_DIR / "manifest.json"


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.exit(f"ERROR: manifest not found: {MANIFEST}")
    return json.loads(MANIFEST.read_text())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(model: str) -> str:
    """Normalized local filename, decoupled from NIST asset naming."""
    return f"oscal-{model}.json"


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (trusted host)
        return resp.read()


def check_oscal_version(data: bytes, expected: str) -> bool:
    """Confirm the schema declares the expected OSCAL version (defensive)."""
    needle = f"/ns/oscal/{expected}/".encode()
    return needle in data


def fetch(verify_only: bool, update_manifest: bool) -> int:
    m = load_manifest()
    tag = m["release_tag"]
    base = m["source"]
    expected_ver = m["oscal_version"]
    schemas = m["schemas"]

    NIST_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0
    updated = False

    for model, entry in schemas.items():
        asset = entry["asset"]
        expected_sha = entry.get("sha256", "")
        dest = NIST_DIR / local_name(model)

        if verify_only:
            if not dest.exists():
                print(f"❌ {model}: missing {dest.name} (run without --verify-only)")
                errors += 1
                continue
            actual = sha256_bytes(dest.read_bytes())
            if actual == expected_sha:
                print(f"✅ {model}: {dest.name} verified ({actual[:12]}…)")
            else:
                print(f"❌ {model}: checksum mismatch\n   expected {expected_sha}\n   actual   {actual}")
                errors += 1
            continue

        # fetch mode
        url = f"{base}/{asset}"
        try:
            data = download(url)
        except Exception as e:  # noqa: BLE001
            print(f"❌ {model}: download failed ({url}): {e}")
            errors += 1
            continue

        actual_sha = sha256_bytes(data)

        if update_manifest:
            entry["sha256"] = actual_sha
            updated = True
        elif actual_sha != expected_sha:
            print(f"❌ {model}: checksum mismatch for {asset}\n   expected {expected_sha}\n   actual   {actual_sha}")
            errors += 1
            continue

        if not check_oscal_version(data, expected_ver):
            print(f"❌ {model}: schema does not declare oscal-version {expected_ver}")
            errors += 1
            continue

        dest.write_bytes(data)
        print(f"✅ {model}: {dest.name} ({len(data)} B, oscal {expected_ver}, {actual_sha[:12]}…)")

    if update_manifest and updated:
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print(f"\nManifest updated: {MANIFEST}")

    print()
    if errors:
        print(f"FAILED: {errors} error(s). Pinned tag: {tag}")
        return 1
    action = "verified" if verify_only else "fetched"
    print(f"OK: all {len(schemas)} NIST schemas {action} for {tag} (oscal {expected_ver}).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch/verify NIST OSCAL base schemas (ADR-008).")
    p.add_argument("--verify-only", action="store_true", help="verify existing files against manifest, no download (CI)")
    p.add_argument("--update-manifest", action="store_true", help="re-fetch and rewrite checksums (version bump)")
    args = p.parse_args()
    if args.verify_only and args.update_manifest:
        p.error("--verify-only and --update-manifest are mutually exclusive")
    return fetch(args.verify_only, args.update_manifest)


if __name__ == "__main__":
    raise SystemExit(main())
