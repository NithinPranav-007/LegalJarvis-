# Dataset Card: Indian Supreme Court Judgments (DS-1)

- **Dataset Name**: Indian Supreme Court Judgments
- **Provider**: Dattam Labs via AWS Open Data Registry
- **Official URL**: https://registry.opendata.aws/indian-supreme-court-judgments/
- **Access Method**: S3 (`s3://indian-supreme-court-judgments`) / HTTPS
- **Acquisition Date**: 2026-10-28
- **Snapshot/Year**: 2023 (English)
- **Observed File Count**: 856 judgments
- **Observed Size**: 382.33 MB (400906240 bytes)
- **File Formats**: PDF (judgment texts), JSON (individual metadata), Parquet (structured metadata)
- **Observed Fields**: `title`, `petitioner`, `respondent`, `judge`, `author_judge`, `citation`, `case_id`, `cnr`, `decision_date`, `disposal_nature`, `court`, `available_languages`, `path`, `nc_display`, `raw_html`
- **License & Attribution**: Creative Commons Attribution 4.0 International (CC-BY-4.0).
  *Attribution text*: "Indian Supreme Court Judgments, Dattam Labs, accessed 2026 from the AWS Open Data Registry."
- **Known Issues**: Native PDF text contains page headers ("SUPREME COURT REPORTS"); whitespace and hyphenation require normalization; occasional regional-language parallel editions exist and must be filtered out for v1.
- **Used By**: Retrieval engine (FR-04), Cited Q&A (FR-05), Summarization (FR-09).
- **Checksum Manifest**: `data/manifests/sc_2023_manifest.sha256`
