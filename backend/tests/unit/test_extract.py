"""Unit tests for text extraction, cleaning, and quality scoring (Task T-05 / T-FR02)."""

from pathlib import Path

from app.ingest.clean import (
    clean_judgment_text,
    compute_extraction_quality,
    dehyphenate,
    is_english_text,
    normalize_unicode,
)
from app.ingest.extract import extract_text_from_pdf


def test_unicode_normalization() -> None:
    raw = "“The Court’s order—issued today—is binding.”"
    normalized = normalize_unicode(raw)
    assert '"' in normalized
    assert "'" in normalized
    assert " - " in normalized
    assert "“" not in normalized
    assert "”" not in normalized


def test_dehyphenation() -> None:
    raw = "The high court has juris-\ndiction over this matter."
    clean = dehyphenate(raw)
    assert "jurisdiction" in clean
    assert "juris-" not in clean


def test_clean_judgment_text_boilerplate_stripping() -> None:
    raw = (
        "[2023] 16 S.C.R. 872\n"
        "322\n"
        "SUPREME COURT REPORTS\n"
        "This is the actual legal reasoning of the judgment regarding the dispute.\n"
        "[2023] 16 S.C.R. 873\n"
        "323\n"
        "The appeal is accordingly allowed.\n"
    )
    cleaned = clean_judgment_text(raw)
    assert "actual legal reasoning" in cleaned
    assert "appeal is accordingly allowed" in cleaned
    assert "SUPREME COURT REPORTS" not in cleaned
    assert "\n322\n" not in cleaned


def test_quality_score() -> None:
    good_text = (
        "The appellant filed a suit for specific performance seeking enforcement of the memorandum "
        "of understanding. The trial court dismissed the suit under Order VII Rule 11 of the Code of "
        "Civil Procedure, holding that the claim was barred by limitation."
    )
    score = compute_extraction_quality(good_text)
    assert score >= 0.80

    garbage_text = "!@#$%^&*()_+ 1234567890 \x00\x01\x02 \t"
    bad_score = compute_extraction_quality(garbage_text)
    assert bad_score <= 0.30


def test_language_detection() -> None:
    english_text = "The Supreme Court of India dismissed the special leave petition."
    assert is_english_text(english_text) is True

    hindi_text = "उच्चतम न्यायालय ने विशेष अनुमति याचिका खारिज कर दी।"
    assert is_english_text(hindi_text) is False


def test_extract_missing_pdf() -> None:
    res = extract_text_from_pdf(Path("non_existent_file.pdf"))
    assert res.status == "failed"
    assert "not found" in (res.error_message or "").lower()
