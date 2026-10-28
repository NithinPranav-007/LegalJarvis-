"""PDF text extraction with page offsets, language filtering, and quality classification."""

from pathlib import Path
from typing import Any

import pdfplumber

from app.ingest.clean import (
    clean_judgment_text,
    compute_extraction_quality,
    is_english_text,
)


class ExtractionResult:
    def __init__(
        self,
        raw_text: str,
        clean_text: str,
        page_offsets: list[dict[str, int]],
        quality_score: float,
        status: str,  # 'ok', 'ocr', 'failed', 'skipped_lang'
        error_message: str | None = None,
    ):
        self.raw_text = raw_text
        self.clean_text = clean_text
        self.page_offsets = page_offsets
        self.quality_score = quality_score
        self.status = status
        self.error_message = error_message

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "quality_score": self.quality_score,
            "num_pages": len(self.page_offsets),
            "clean_char_count": len(self.clean_text),
            "error_message": self.error_message,
        }


def extract_text_from_pdf(pdf_path: Path) -> ExtractionResult:
    """Extract full text and page offsets from PDF using pdfplumber."""
    if not pdf_path.exists():
        return ExtractionResult(
            raw_text="",
            clean_text="",
            page_offsets=[],
            quality_score=0.0,
            status="failed",
            error_message=f"File not found: {pdf_path}",
        )

    try:
        pages_text: list[str] = []
        page_offsets: list[dict[str, int]] = []
        current_offset = 0

        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, 1):
                p_text = page.extract_text() or ""
                p_clean = clean_judgment_text(p_text)
                p_len = len(p_clean)

                pages_text.append(p_clean)
                page_offsets.append(
                    {
                        "page_no": page_idx,
                        "start_char": current_offset,
                        "end_char": current_offset + p_len,
                        "char_count": p_len,
                    }
                )
                current_offset += p_len + 2  # account for page break separator "\n\n"

        full_clean_text = "\n\n".join(pages_text).strip()

        # If zero text extracted across all pages, document is likely scanned or empty
        if not full_clean_text or len(full_clean_text) < 30:
            return ExtractionResult(
                raw_text="",
                clean_text="",
                page_offsets=page_offsets,
                quality_score=0.0,
                status="failed",
                error_message="No text layer detected (scanned document or corrupt pages)",
            )

        # Language check (v1 supports English legal texts per PRD FR-02)
        if not is_english_text(full_clean_text):
            return ExtractionResult(
                raw_text="",
                clean_text=full_clean_text,
                page_offsets=page_offsets,
                quality_score=0.0,
                status="skipped_lang",
                error_message="Non-English text detected",
            )

        quality_score = compute_extraction_quality(full_clean_text)
        status = "ok" if quality_score >= 0.50 else "failed"

        return ExtractionResult(
            raw_text="",
            clean_text=full_clean_text,
            page_offsets=page_offsets,
            quality_score=quality_score,
            status=status,
            error_message=None if status == "ok" else "Low extraction quality score",
        )

    except Exception as e:
        return ExtractionResult(
            raw_text="",
            clean_text="",
            page_offsets=[],
            quality_score=0.0,
            status="failed",
            error_message=f"PDF parsing error: {e}",
        )
