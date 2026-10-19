# SPDX-FileCopyrightText: 2026 DB Systel GmbH
# SPDX-License-Identifier: Apache-2.0
#!/usr/bin/env python3
"""Fetch the BSI example upstream catalog reproducibly from a pinned commit.

This is the example-side analogue of tools/fetch_oscal_schemas.py (ADR-008):
the external upstream catalog that examples/profiles/ resolves against is NEVER
vendored into this repository. It is downloaded from a pinned commit of the BSI
'Stand-der-Technik-Bibliothek' and verified against a committed SHA256 manifest,
so the example is reproducible without mixing the BSI license (CC-BY-SA-4.0) into
this Apache-2.0 repository.

Why a commit SHA and not a release tag: the BSI repository publishes no releases
or tags, so the pin is a commit SHA (manifest field 'commit'). Policy is otherwise
identical to ADR-008: pin explicitly, verify by checksum, never track against a
moving branch.

The pinned upstream lives in examples/upstream/bsi/manifest.json (single source of
truth). Fetched files are written next to it under examples/upstream/bsi/_fetched/,
which is git-ignored: they are a build input, not repository content.

Usage:
    python3 tools/fetch_bsi_example.py                 # fetch + verify all files
    python3 tools/fetch_bsi_example.py --verify-only   # verify existing files offline (CI)
    python3 tools/fetch_bsi_example.py --update-manifest # re-fetch and rewrite checksums (pin bump)

Dependencies: Python 3.10+ standard library only (urllib, hashlib, json).
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

BSI_DIR = Path(__file__).resolve().parent.parent / "examples" / "upstream" / "bsi"
MANIFEST = BSI_DIR / "manifest.json"
FETCHED_DIR = BSI_DIR / "_fetched"


def load_manifest() -> dict:
    if not MANIFEST.exists():
        sys.exit(f"ERROR: manifest not found: {MANIFEST}")
    return json.loads(MANIFEST.read_text())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(key: str) -> str:
    """Normalized local filename, decoupled from the upstream path."""
    return f"{key}.json"


def download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 (trusted host)
        return resp.read()


def fetch(verify_only: bool, update_manifest: bool) -> int:
    m = load_manifest()
    commit = m["commit"]
    raw_base = m["raw_base"]
    files = m["files"]

    FETCHED_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0
    updated = False

    for key, entry in files.items():
        rel = entry["path"]
        expected_sha = entry.get("sha256", "")
        dest = FETCHED_DIR / local_name(key)

        if verify_only:
            if not dest.exists():
                print(f"❌ {key}: missing {dest.name} (run without --verify-only)")
                errors += 1
                continue
            actual = sha256_bytes(dest.read_bytes())
            if actual == expected_sha:
                print(f"✅ {key}: {dest.name} verified ({actual[:12]}…)")
            else:
                print(f"❌ {key}: checksum mismatch\n   expected {expected_sha}\n   actual   {actual}")
                errors += 1
            continue

        # fetch mode
        url = f"{raw_base}/{rel}"
        try:
            data = download(url)
        except Exception as e:  # noqa: BLE001
            print(f"❌ {key}: download failed ({url}): {e}")
            errors += 1
            continue

        actual_sha = sha256_bytes(data)

        if update_manifest:
            entry["sha256"] = actual_sha
            updated = True
        elif actual_sha != expected_sha:
            print(f"❌ {key}: checksum mismatch for {rel}\n   expected {expected_sha}\n   actual   {actual_sha}")
            errors += 1
            continue

        dest.write_bytes(data)
        print(f"✅ {key}: {dest.name} ({len(data)} B, {actual_sha[:12]}…)")

    if update_manifest and updated:
        MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n")
        print(f"\nManifest updated: {MANIFEST}")

    print()
    if errors:
        print(f"FAILED: {errors} error(s). Pinned commit: {commit}")
        return 1
    action = "verified" if verify_only else "fetched"
    print(f"OK: all {len(files)} BSI upstream files {action} for commit {commit[:12]}… (CC-BY-SA-4.0, see manifest).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch/verify the BSI example upstream catalog (ADR-008 policy).")
    p.add_argument("--verify-only", action="store_true", help="verify existing files against manifest, no download (CI)")
    p.add_argument("--update-manifest", action="store_true", help="re-fetch and rewrite checksums (pin bump)")
    args = p.parse_args()
    if args.verify_only and args.update_manifest:
        p.error("--verify-only and --update-manifest are mutually exclusive")
    return fetch(args.verify_only, args.update_manifest)


if __name__ == "__main__":
    raise SystemExit(main())
