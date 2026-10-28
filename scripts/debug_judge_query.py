"""Diagnostic script to trace the All India Judges Association v. Union of India query."""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.db.session import sync_session_maker
from app.db.models import Document, Chunk
from app.qa.query_analysis import analyze_query
from app.retrieval.lexical import search_lexical_db
from app.retrieval.dense import search_dense
from app.retrieval.hybrid import search_hybrid
from app.qa.orchestrator import QAOrchestrator

db = sync_session_maker()

query = "Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."

print("=== 1. CHECK DATABASE FOR ALL INDIA JUDGES ASSOCIATION OR 2023 JUDGMENTS ===")
all_docs = db.query(Document).all()
print(f"Total documents in DB: {len(all_docs)}")
for d in all_docs:
    print(f"  ID: {d.id} | Year: {d.decision_date} | Citation: {d.neutral_citation} | Title: {d.title}")

matching = db.query(Document).filter(Document.title.ilike("%All India Judges%")).all()
print(f"Matching 'All India Judges': {len(matching)}")

matching_2023 = db.query(Document).filter(Document.decision_date.like("2023%")).all()
print(f"Matching year 2023: {len(matching_2023)}")
for d in matching_2023:
    print(f"  2023 doc: {d.title} ({d.neutral_citation})")

print("\n=== 2. QUERY ANALYSIS ===")
analysis = analyze_query(query)
print("Statute provisions:", analysis.detected_sections)
print("Detected years:", analysis.detected_years)
print("Notice text:", analysis.notice_text)

print("\n=== 3. LEXICAL SEARCH (BM25) ===")
lex_hits = search_lexical_db(db, query, limit=5)
for i, h in enumerate(lex_hits, 1):
    print(f"  Lex Hit {i}: doc_id={h.document_id}, score={h.score:.4f}, title={h.title}, citation={h.neutral_citation}")
    print(f"    Snippet: {h.snippet[:120]}...")

print("\n=== 4. DENSE RETRIEVAL ===")
dense_hits = search_dense(db, query, limit=5)
for i, h in enumerate(dense_hits, 1):
    print(f"  Dense Hit {i}: doc_id={h.document_id}, score={h.score:.4f}, title={h.title}, citation={h.neutral_citation}")
    print(f"    Snippet: {h.snippet[:120]}...")

print("\n=== 5. HYBRID RETRIEVAL (RRF + Rerank) ===")
hybrid_hits = search_hybrid(db, query, limit=5, rerank=True)
for i, h in enumerate(hybrid_hits, 1):
    print(f"  Hybrid Hit {i}: doc_id={h.document_id}, score={h.score:.4f}, title={h.title}, citation={h.neutral_citation}")
    print(f"    Snippet: {h.snippet[:120]}...")

print("\n=== 6. QA ORCHESTRATOR EXECUTION ===")
orchestrator = QAOrchestrator()
resp = orchestrator.ask(db, query)
print("Abstained:", resp.abstained)
print("Abstention Reason:", resp.abstention_reason)
print("Answer:", resp.answer)
print("Citations:", [(c.marker, c.title, c.neutral_citation, c.para_no) for c in resp.citations])
