#!/usr/bin/env python3
"""Utility for generating and verifying SHA-256 checksum manifests."""

import hashlib
import sys
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute hex SHA-256 hash of a file efficiently in 64KB blocks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_manifest(source_dir: Path, output_manifest: Path) -> None:
    """Generate SHA-256 manifest for all files in source_dir."""
    entries = []
    for p in sorted(source_dir.rglob("*")):
        if p.is_file() and p != output_manifest:
            sha = compute_sha256(p)
            rel_path = p.relative_to(source_dir).as_posix()
            entries.append(f"{sha}  {rel_path}\n")

    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    output_manifest.write_text("".join(entries), encoding="utf-8")
    print(f"Generated manifest with {len(entries)} files: {output_manifest}")


def verify_manifest(manifest_path: Path, base_dir: Path) -> bool:
    """Verify that all files listed in manifest match their recorded SHA-256."""
    if not manifest_path.exists():
        print(f"Manifest not found: {manifest_path}")
        return False

    all_matched = True
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        expected_sha, rel_path = parts
        file_path = base_dir / rel_path
        if not file_path.exists():
            print(f"MISSING: {rel_path}")
            all_matched = False
            continue
        actual_sha = compute_sha256(file_path)
        if actual_sha.lower() != expected_sha.lower():
            print(f"FAILED: {rel_path} (expected {expected_sha}, got {actual_sha})")
            all_matched = False

    return all_matched


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: checksum.py generate <source_dir> <output_manifest>")
        print("       checksum.py verify <manifest_path> <base_dir>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "generate":
        generate_manifest(Path(sys.argv[2]), Path(sys.argv[3]))
    elif cmd == "verify":
        success = verify_manifest(Path(sys.argv[2]), Path(sys.argv[3]))
        sys.exit(0 if success else 1)
