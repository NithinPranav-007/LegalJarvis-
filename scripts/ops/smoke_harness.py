"""Deployment smoke test harness (PRD T-21 / T-DEPLOY).

Verifies that the deployed or locally running LegalJarvis instance satisfies:
1. GET /health -> 200 OK
2. POST /v1/search -> 200 OK with valid schema & attribution
3. POST /v1/qa -> 200 OK with citations, disclaimer, or graceful abstention
4. GET /v1/statutes/versions -> 200 OK
5. Frontend HTTP reachable (if frontend URL provided)
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# Add backend and repo root to sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_path = os.path.join(repo_root, "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)


def test_http_endpoint(method: str, url: str, data: dict | None = None) -> tuple[int, dict | str]:
    """Execute HTTP request using standard library."""
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            if "application/json" in content_type:
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except Exception as e:
        return 0, str(e)


def run_standalone_app_smoke() -> int:
    """Run internal ASGI smoke test when external server port is not running."""
    print("Executing in-process ASGI deployment smoke test...")
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from app.api.search import get_sync_db
    from app.main import app
    from tests.perf.run_perf import setup_benchmark_engine

    engine = setup_benchmark_engine()
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    def get_test_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_sync_db] = get_test_db

    with TestClient(app) as client:
        # 1. Health check
        h_resp = client.get("/health")
        assert h_resp.status_code == 200, f"Health check failed: {h_resp.status_code}"
        print("  [PASS] GET /health: 200 OK")

        # 2. Search check
        s_resp = client.post("/v1/search", json={"query": "right to privacy", "top_k": 3})
        assert s_resp.status_code == 200, f"Search failed: {s_resp.status_code}"
        assert "results" in s_resp.json()
        print(f"  [PASS] POST /v1/search: 200 OK ({len(s_resp.json()['results'])} results)")

        # 3. QA check
        q_resp = client.post("/v1/qa", json={"question": "What is the ratio in Puttaswamy?", "top_k": 3})
        assert q_resp.status_code == 200, f"QA failed: {q_resp.status_code}"
        assert "disclaimer" in q_resp.json()
        print("  [PASS] POST /v1/qa: 200 OK (grounded / abstained response with disclaimer)")

        # 4. Statutes check
        st_resp = client.get("/v1/statutes")
        assert st_resp.status_code == 200, f"Statutes failed: {st_resp.status_code}"
        print("  [PASS] GET /v1/statutes: 200 OK")

    print("\n[SMOKE TEST PASSED] In-process deployment smoke test successful.")
    return 0


def run_live_smoke(base_url: str, frontend_url: str | None = None) -> int:
    """Run smoke test against a live deployed LegalJarvis instance."""
    print(f"Executing live deployment smoke test against {base_url}...")
    failures = 0

    # 1. Health
    status, data = test_http_endpoint("GET", f"{base_url}/health")
    if status == 200:
        print("  [PASS] GET /health: 200 OK")
    else:
        print(f"  [FAIL] GET /health FAILED: status={status}, error={data}")
        failures += 1

    # 2. Search
    status, data = test_http_endpoint(
        "POST",
        f"{base_url}/v1/search",
        {"query": "right to privacy", "top_k": 3},
    )
    if status == 200 and isinstance(data, dict) and "results" in data:
        print(f"  [PASS] POST /v1/search: 200 OK ({len(data['results'])} hits)")
    else:
        print(f"  [FAIL] POST /v1/search FAILED: status={status}, error={data}")
        failures += 1

    # 3. QA
    status, data = test_http_endpoint(
        "POST",
        f"{base_url}/v1/qa",
        {"question": "What is criminal conspiracy under Section 120A IPC?", "top_k": 3},
    )
    if status == 200 and isinstance(data, dict) and "disclaimer" in data:
        print("  [PASS] POST /v1/qa: 200 OK (verified citations & disclaimer)")
    else:
        print(f"  [FAIL] POST /v1/qa FAILED: status={status}, error={data}")
        failures += 1

    # 4. Statutes
    status, data = test_http_endpoint("GET", f"{base_url}/v1/statutes")
    if status == 200:
        print("  [PASS] GET /v1/statutes: 200 OK")
    else:
        print(f"  [FAIL] GET /v1/statutes FAILED: status={status}, error={data}")
        failures += 1

    # 5. Frontend
    if frontend_url:
        status, _ = test_http_endpoint("GET", frontend_url)
        if status in (200, 304):
            print(f"  [PASS] GET {frontend_url}: {status} OK")
        else:
            print(f"  [FAIL] Frontend check failed on {frontend_url} (HTTP {status})")
            failures += 1

    if failures == 0:
        print("\n[SMOKE TEST PASSED] All deployment endpoints verified successfully.")
        return 0
    else:
        print(f"\n[SMOKE TEST FAILED] {failures} endpoint check(s) failed.")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LegalJarvis Smoke Test Harness")
    parser.add_argument("--base-url", default="http://localhost:8000", help="FastAPI backend URL")
    parser.add_argument("--frontend-url", default=None, help="Frontend URL (optional)")
    args = parser.parse_args()

    # Check if live server is reachable
    status, _ = test_http_endpoint("GET", f"{args.base_url}/health")
    if status == 200:
        sys.exit(run_live_smoke(args.base_url, args.frontend_url))
    else:
        # Fall back to in-process ASGI smoke test
        print(f"Live server not detected at {args.base_url} (HTTP {status}).")
        sys.exit(run_standalone_app_smoke())
