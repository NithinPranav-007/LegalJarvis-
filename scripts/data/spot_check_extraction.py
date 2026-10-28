#!/usr/bin/env python3
"""Run extraction and quality spot-check on 30 real Supreme Court judgment PDFs (Task T-05)."""

import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.ingest.extract import extract_text_from_pdf

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LegalJarvis/0.1"}


def main() -> None:
    print("Sampling 30 real Supreme Court PDFs from 2023 dataset...")
    tar_url = "https://indian-supreme-court-judgments.s3.amazonaws.com/data/tar/year=2023/english/english.tar"
    sample_dir = REPO_ROOT / "data" / "interim" / "sc_sample_30"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Stream 30 PDFs from tar
    req = urllib.request.Request(tar_url, headers={"Range": "bytes=0-45000000", **HEADERS})
    with urllib.request.urlopen(req, timeout=30) as resp:
        tar_bytes = resp.read()

    bio = io.BytesIO(tar_bytes)
    extracted_paths: list[Path] = []
    with tarfile.open(fileobj=bio, mode="r:*") as tar:
        while len(extracted_paths) < 30:
            m = tar.next()
            if not m:
                break
            if m.name.endswith(".pdf"):
                out_path = sample_dir / m.name
                f = tar.extractfile(m)
                out_path.write_bytes(f.read())
                extracted_paths.append(out_path)

    print(f"Extracted {len(extracted_paths)} real PDF files to {sample_dir}")

    results = []
    statuses = {"ok": 0, "ocr": 0, "failed": 0, "skipped_lang": 0}

    for idx, p in enumerate(extracted_paths, 1):
        res = extract_text_from_pdf(p)
        statuses[res.status] = statuses.get(res.status, 0) + 1
        results.append({
            "index": idx,
            "filename": p.name,
            "size_kb": p.stat().st_size // 1024,
            "pages": len(res.page_offsets),
            "chars": len(res.clean_text),
            "quality_score": res.quality_score,
            "status": res.status,
            "error": res.error_message,
        })
        print(f"[{idx:02d}/30] {p.name}: status={res.status}, quality={res.quality_score:.3f}, pages={len(res.page_offsets)}, chars={len(res.clean_text)}")

    print("\nExtraction Status Distribution (n=30):")
    for st, count in statuses.items():
        print(f"  {st}: {count} ({count/30*100:.1f}%)")

    # Output results JSON for progress report
    out_json = REPO_ROOT / "docs" / "progress" / "T-05_spot_check_results.json"
    out_json.write_text(json.dumps({"statuses": statuses, "results": results}, indent=2), encoding="utf-8")
    print(f"Saved results to {out_json}")


if __name__ == "__main__":
    main()
