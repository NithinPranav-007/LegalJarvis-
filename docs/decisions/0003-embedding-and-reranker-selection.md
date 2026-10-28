# ADR 0003: Embedding Model and Reranker Selection

**Status**: Accepted  
**Date**: 2026-10-28  
**Context**: Tasks T-08, T-09, PRD Sections C2, D3 (FR-04), D7 (Schema)

---

## 1. Context and Problem Statement
LegalJarvis requires semantic representation of Indian legal texts (Supreme Court and High Court judgments, central statutes) for dense retrieval and subsequent hybrid fusion with lexical search (BM25). The PRD mandates:
1. Multi-lingual and multi-granularity capability suitable for technical legal formulations, long statutory provisions, and dense case paragraphs.
2. Verified permissive open-source license compatible with research and production deployment.
3. Explicit recording of model IDs, revisions, dimensions, and license texts before integration.

---

## 2. Considered Alternatives

### Dense Embedding Models
1. **BAAI/bge-m3**:
   - **Dimension**: 1024
   - **Max Sequence Length**: 8192 tokens
   - **License**: MIT License (permissive)
   - **Features**: Supports dense retrieval, multi-lingual Indian script coverage, multi-granularity (short queries to long document passages).
   - **Status**: **Selected Primary Model**.

2. **sentence-transformers/all-MiniLM-L6-v2**:
   - **Dimension**: 384
   - **Max Sequence Length**: 256 tokens
   - **License**: Apache 2.0
   - **Notes**: High throughput, low latency, but shorter context and lower domain depth for legal phrasing.

3. **law-ai/InLegalBERT**:
   - **Dimension**: 768
   - **Base**: RoBERTa pretrained on Indian legal corpus
   - **License**: Apache 2.0
   - **Notes**: Best suited as encoder for rhetorical-role classification and domain fine-tuning (see Task T-16); standard BGE-M3 performs superiorly on open zero-shot retrieval benchmarks.

### Cross-Encoder Rerankers
1. **BAAI/bge-reranker-base**:
   - **License**: MIT License
   - **Parameters**: ~278M
   - **Status**: **Selected Primary Reranker**. Cross-encodes `(query, passage)` pairs to compute calibrated relevance logits.

---

## 3. Decision
1. **Primary Dense Embedding Model**: `BAAI/bge-m3` (1024 dimensions, MIT license, revision `main`).
2. **Primary Neural Reranker**: `BAAI/bge-reranker-base` (MIT license, revision `main`).
3. **Database Column**: `chunks.embedding` stores a 1024-dimensional vector (`VectorColumn(1024)` in PostgreSQL with `pgvector`, serialized JSON array in SQLite for local test suites).
4. **Offline / Fallback Architecture**:
   - To support continuous integration, air-gapped workstations, and rapid offline tests without requiring multi-gigabyte GPU downloads or external network access, the system provides an abstract `BaseEmbedder` interface with a deterministic `DeterministicHashEmbedder` fallback.
   - Production workers load `SentenceTransformerEmbedder("BAAI/bge-m3")` on GPU or CPU.

---

## 4. Consequences
- **Positive**: High semantic retrieval accuracy on technical Indian legal phraseology; generous 8192 token window easily accommodates full judgment paragraphs; clear MIT licensing.
- **Negative**: 1024 dimensions require higher memory and storage than 384d models. Mitigated by HNSW indexing in PostgreSQL and batching.
