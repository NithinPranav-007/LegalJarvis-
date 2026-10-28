"""SHA-256 hash calculation and manifest generation utilities."""

import hashlib
from pathlib import Path


def compute_sha256(file_path: Path) -> str:
    """Compute hex SHA-256 hash of a file efficiently in 64KB chunks."""
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


def verify_manifest(manifest_path: Path, base_dir: Path) -> bool:
    """Verify that all files listed in manifest match their recorded SHA-256."""
    if not manifest_path.exists():
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
            all_matched = False
            continue
        actual_sha = compute_sha256(file_path)
        if actual_sha.lower() != expected_sha.lower():
            all_matched = False

    return all_matched
