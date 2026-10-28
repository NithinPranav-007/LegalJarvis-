"""Diagnostic script to trace a Q&A request through the complete pipeline."""

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.db.session import sync_session_maker
from app.retrieval.hybrid import search_hybrid
from app.qa.context_builder import build_qa_context
from app.llm.gateway import get_llm_gateway
from app.verify.abstain import verify_and_filter_answer
from app.verify.existence import verify_citation_existence
from app.verify.support import split_sentences_with_citations, verify_sentence_support

db = sync_session_maker()
query = "Is right to privacy recognized as a fundamental right under Article 21 of the Constitution?"

print("=== 1. RETRIEVAL STEP ===")
hits = search_hybrid(db, query, limit=5, rerank=True)
print(f"Total hits retrieved: {len(hits)}")
for i, h in enumerate(hits, 1):
    print(f"Hit {i}: doc_id={h.document_id}, chunk_id={h.chunk_id}, score={h.score:.4f}, title={h.title}, citation={h.neutral_citation}, para={h.para_no}")
    print(f"     snippet={h.snippet[:120]}...")

print("\n=== 2. CONTEXT BUILDER STEP ===")
context = build_qa_context(hits)
print(f"Passages assembled: {context.num_passages}, total chars: {context.total_chars}")
print(f"Citation map keys: {list(context.citation_map.keys())}")
print(f"Formatted context preview:\n{context.formatted_text[:400]}...\n")

from app.qa.orchestrator import QAOrchestrator

orchestrator = QAOrchestrator()
resp = orchestrator.ask(db, query)
print("=== QA ORCHESTRATOR RESULT ===")
print("Answer:", resp.answer)
print("Abstained:", resp.abstained)
print("Citations count:", len(resp.citations))
if resp.citations:
    print("Citation 0:", resp.citations[0].marker, resp.citations[0].title, resp.citations[0].neutral_citation)
print("Abstention reason:", resp.abstention_reason)
