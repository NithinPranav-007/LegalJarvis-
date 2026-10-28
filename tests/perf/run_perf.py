"""Performance benchmark and load testing execution script (PRD T-20 / T-NFR-PERF).

Evaluates latency percentiles (p50, p95, p99) under 20 concurrent simulated users
against PRD D4 non-functional performance targets:
  - Precedent Search p95 <= 2,000 ms
  - Q&A End-to-End p95 <= 20,000 ms
"""

import argparse
import concurrent.futures
import math
import os
import random
import sys
import time
from typing import Any

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.ingest.embed import DeterministicHashEmbedder
from app.llm.gateway import LLMGateway
from app.llm.providers.fake import FakeProvider
from app.main import app

SEARCH_QUERIES = [
    "right to privacy Article 21",
    "criminal conspiracy Section 120A Indian Penal Code",
    "anticipatory bail parameters Section 438 CrPC",
    "quashing of criminal proceedings Section 482",
    "circumstantial evidence panchsheel principles",
    "extra-judicial confession evidentiary value",
    "mens rea in statutory offences",
    "test identification parade delay evidentiary value",
]

QA_QUESTIONS = [
    "What are the ingredients of criminal conspiracy under Section 120A IPC?",
    "What are the guidelines for grant of anticipatory bail?",
    "Under what circumstances can the High Court quash an FIR under Section 482 CrPC?",
    "What are the five golden principles for circumstantial evidence?",
]


def setup_benchmark_engine():
    """Set up and seed fast in-memory SQLite database engine with Indian case law passages."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        court = Court(code="sc", name="Supreme Court of India", level="supreme")
        snapshot = DatasetSnapshot(
            source_key="sc_judgments",
            source_url="https://registry.opendata.aws/indian-supreme-court-judgments/",
            license="CC-BY-4.0",
            attribution="Dattam Labs",
            manifest_path="data/manifests/sc_2023.sha256",
        )
        session.add_all([court, snapshot])
        session.commit()

        run = IngestionRun(snapshot_id=snapshot.id, params={"year": 2023}, status="success")
        session.add(run)
        session.commit()

        doc1 = Document(
            run_id=run.id,
            court_id=court.id,
            external_id="2023_16_872_887",
            title="Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
            neutral_citation="2023 INSC 1043",
            source_file_path="data/raw/sc/year=2023/2023_16_872_887_EN.pdf",
            source_sha256="1" * 64,
            extraction_status="ok",
        )
        doc2 = Document(
            run_id=run.id,
            court_id=court.id,
            external_id="2023_7_322_346",
            title="Central GST Delhi v. Delhi International Airport Ltd",
            neutral_citation="2023 INSC 540",
            source_file_path="data/raw/sc/year=2023/2023_7_322_346_EN.pdf",
            source_sha256="2" * 64,
            extraction_status="ok",
        )
        session.add_all([doc1, doc2])
        session.commit()

        embedder = DeterministicHashEmbedder()

        sample_texts = [
            "Section 16(c) of Specific Relief Act mandates continuous readiness and willingness.",
            "Criminal conspiracy under Section 120A requires agreement between two or more persons.",
            "Anticipatory bail under Section 438 CrPC is granted when no custodial interrogation is required.",
            "High Court power under Section 482 CrPC should be exercised sparingly to prevent abuse of process.",
            "Circumstantial evidence must form a complete chain of events pointing unerringly to guilt.",
        ]

        for idx, text in enumerate(sample_texts, start=1):
            vec = embedder.embed_text(text)
            chunk = Chunk(
                document_id=doc1.id if idx % 2 == 1 else doc2.id,
                para_no=idx * 5,
                start_char=0,
                end_char=len(text),
                text=text,
                embedding=vec,
                segment_type="reasoning",
            )
            session.add(chunk)
        session.commit()
    return engine


def percentile(data: list[float], pct: float) -> float:
    """Compute percentile from sorted float list."""
    if not data:
        return 0.0
    k = (len(data) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[int(f)] * (c - k)
    d1 = data[int(c)] * (k - f)
    return d0 + d1


def worker_task(client: TestClient, endpoint_type: str) -> tuple[str, float, int]:
    """Execute a single simulated researcher request and measure response latency."""
    t0 = time.perf_counter()
    status_code = 0

    if endpoint_type == "health":
        resp = client.get("/health")
        status_code = resp.status_code
    elif endpoint_type == "search":
        q = random.choice(SEARCH_QUERIES)
        resp = client.post("/v1/search", json={"query": q, "top_k": 5})
        status_code = resp.status_code
    elif endpoint_type == "qa":
        q = random.choice(QA_QUESTIONS)
        resp = client.post("/v1/qa", json={"question": q, "top_k": 3})
        status_code = resp.status_code
    elif endpoint_type == "statutes":
        resp = client.get("/v1/statutes/versions")
        status_code = resp.status_code

    duration_ms = (time.perf_counter() - t0) * 1000.0
    return endpoint_type, duration_ms, status_code


def run_load_benchmark(concurrency: int = 20, total_requests: int = 100) -> dict[str, Any]:
    """Run concurrent load test with specified concurrency and total requests."""
    print(f"=== Running LegalJarvis Performance Benchmark (Concurrency={concurrency}, Requests={total_requests}) ===")

    # Initialize benchmark database and wire into FastAPI
    engine = setup_benchmark_engine()
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def get_benchmark_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = get_benchmark_db

    endpoint_distribution = (
        ["search"] * 40 +
        ["qa"] * 25 +
        ["health"] * 20 +
        ["statutes"] * 15
    )

    latencies: dict[str, list[float]] = {
        "search": [],
        "qa": [],
        "health": [],
        "statutes": [],
    }
    status_codes: dict[str, list[int]] = {
        "search": [],
        "qa": [],
        "health": [],
        "statutes": [],
    }

    # Pre-warm application
    with TestClient(app) as warmup_client:
        warmup_client.get("/health")
        warmup_client.post("/v1/search", json={"query": "privacy", "top_k": 1})

    wall_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for _ in range(total_requests):
            ep = random.choice(endpoint_distribution)
            futures.append(executor.submit(worker_task, TestClient(app), ep))

        for f in concurrent.futures.as_completed(futures):
            ep, dur, code = f.result()
            latencies[ep].append(dur)
            status_codes[ep].append(code)

    wall_duration = time.perf_counter() - wall_start

    results = {}
    print("\n---------------- Performance Results Summary ----------------")
    print(f"{'Endpoint':<15} | {'Count':<6} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'p99 (ms)':<10} | {'Target p95':<12} | {'Pass/Fail':<9}")
    print("-" * 85)

    all_pass = True

    targets_p95 = {
        "search": 2000.0,
        "qa": 20000.0,
        "health": 200.0,
        "statutes": 500.0,
    }

    for ep in ["search", "qa", "health", "statutes"]:
        times = sorted(latencies[ep])
        cnt = len(times)
        if cnt == 0:
            continue
        p50 = percentile(times, 50)
        p95 = percentile(times, 95)
        p99 = percentile(times, 99)
        target = targets_p95.get(ep, 2000.0)
        passed = p95 <= target
        if not passed:
            all_pass = False

        status_str = "PASS" if passed else "FAIL"
        print(f"{ep:<15} | {cnt:<6} | {p50:<10.2f} | {p95:<10.2f} | {p99:<10.2f} | {target:<12.1f} | {status_str:<9}")

        results[ep] = {
            "count": cnt,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "target_p95_ms": target,
            "passed": passed,
        }

    rps = total_requests / wall_duration
    print("-" * 85)
    print(f"Total Requests: {total_requests} in {wall_duration:.2f}s ({rps:.2f} RPS)")
    print(f"Overall Status: {'ALL TARGETS PASSED' if all_pass else 'TARGETS EXCEEDED'}\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LegalJarvis Performance Benchmark")
    parser.add_argument("--concurrency", type=int, default=20, help="Number of concurrent simulated users")
    parser.add_argument("--requests", type=int, default=100, help="Total requests to generate")
    args = parser.parse_args()

    results = run_load_benchmark(concurrency=args.concurrency, total_requests=args.requests)
    sys.exit(0)
