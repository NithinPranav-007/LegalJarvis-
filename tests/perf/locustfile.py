"""Locust performance and load testing suite (PRD T-20 / T-NFR-PERF).

Simulates concurrent legal researchers performing searches, QA inquiries,
statute concordance queries, and health checks against the LegalJarvis FastAPI API.
Targets D4 thresholds:
  - Search p95 <= 2,000 ms
  - Q&A end-to-end p95 <= 20,000 ms
"""

import os
import random
from locust import HttpUser, between, task

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


class LegalResearcherUser(HttpUser):
    """Simulates a legal researcher browsing case law, issuing queries, and verifying precedents."""

    wait_time = between(1.0, 3.0)

    @task(5)
    def search_precedents(self) -> None:
        """Search legal precedents using hybrid lexical + dense retrieval."""
        query = random.choice(SEARCH_QUERIES)
        payload = {
            "query": query,
            "top_k": 5,
            "filter_court": None,
            "min_year": 2000,
        }
        with self.client.post(
            "/v1/search",
            json=payload,
            name="/v1/search",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Search failed with HTTP {response.status_code}: {response.text[:100]}")

    @task(2)
    def ask_legal_question(self) -> None:
        """Submit a citation-grounded legal question to the Q&A orchestrator."""
        question = random.choice(QA_QUESTIONS)
        payload = {
            "question": question,
            "top_k": 3,
        }
        with self.client.post(
            "/v1/qa",
            json=payload,
            name="/v1/qa",
            catch_response=True,
        ) as response:
            if response.status_code in (200, 422):
                response.success()
            else:
                response.failure(f"QA failed with HTTP {response.status_code}: {response.text[:100]}")

    @task(3)
    def check_health(self) -> None:
        """Verify API and database health status."""
        with self.client.get("/health", name="/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed with HTTP {response.status_code}")

    @task(2)
    def check_statute_versions(self) -> None:
        """Retrieve statute versions and IPC/BNS concordance metadata."""
        with self.client.get(
            "/v1/statutes/versions",
            name="/v1/statutes/versions",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Statute versions failed with HTTP {response.status_code}")
