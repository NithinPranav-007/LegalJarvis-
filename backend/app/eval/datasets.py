"""Evaluation dataset schemas and loaders (Task T-09 / FR-16)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvalQuery:
    query_id: str
    text: str
    relevant_chunk_ids: set[int]
    domain: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalCorpusItem:
    chunk_id: int
    document_id: int
    title: str
    text: str
    para_no: int | None = None
    court: str = "Supreme Court of India"
    decision_date: str | None = None


@dataclass
class EvaluationDataset:
    name: str
    version: str
    queries: list[EvalQuery]
    corpus: list[EvalCorpusItem]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "num_queries": len(self.queries),
            "num_corpus_items": len(self.corpus),
            "queries": [
                {
                    "query_id": q.query_id,
                    "text": q.text,
                    "relevant_chunk_ids": list(q.relevant_chunk_ids),
                    "domain": q.domain,
                }
                for q in self.queries
            ],
            "corpus": [
                {
                    "chunk_id": c.chunk_id,
                    "document_id": c.document_id,
                    "title": c.title,
                    "text": c.text,
                    "para_no": c.para_no,
                    "court": c.court,
                }
                for c in self.corpus
            ],
        }


# Standard Benchmark: 10 Indian legal research queries with known relevant passages
DEFAULT_BENCHMARK_CORPUS: list[EvalCorpusItem] = [
    EvalCorpusItem(
        chunk_id=1,
        document_id=101,
        title="Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
        text="A suit for specific performance of an agreement for sale requires the plaintiff to establish readiness and willingness under Section 16(c) of the Specific Relief Act.",
        para_no=14,
        court="Supreme Court of India",
        decision_date="2023-11-28",
    ),
    EvalCorpusItem(
        chunk_id=2,
        document_id=102,
        title="Central GST Delhi v. Delhi International Airport Ltd",
        text="The levy of service tax on user development fee (UDF) collected by airport operators under Section 22A of the Airports Authority of India Act, 1994 is not exigible.",
        para_no=22,
        court="Supreme Court of India",
        decision_date="2023-05-19",
    ),
    EvalCorpusItem(
        chunk_id=3,
        document_id=103,
        title="Batliboi Environmental Engineers Ltd v. Hindustan Petroleum Corporation Ltd",
        text="Under Section 34 of the Arbitration and Conciliation Act 1996, the court does not sit in appeal over an arbitral award; patent illegality must go to the root of the matter.",
        para_no=31,
        court="Supreme Court of India",
        decision_date="2023-09-21",
    ),
    EvalCorpusItem(
        chunk_id=4,
        document_id=104,
        title="K.S. Puttaswamy v. Union of India",
        text="The right to privacy is protected as an intrinsic part of the right to life and personal liberty under Article 21, subject to legitimate state aim and proportionality.",
        para_no=42,
        court="Supreme Court of India",
        decision_date="2017-08-24",
    ),
    EvalCorpusItem(
        chunk_id=5,
        document_id=105,
        title="Irfan v. State of Uttar Pradesh",
        text="A dying declaration under Section 32(1) of the Indian Evidence Act can form the sole basis of conviction only if it is found to be reliable, voluntary, and free from tutoring.",
        para_no=18,
        court="Supreme Court of India",
        decision_date="2023-08-23",
    ),
    EvalCorpusItem(
        chunk_id=6,
        document_id=106,
        title="Mahmood Ali v. State of Uttar Pradesh",
        text="Inherent powers under Section 482 CrPC should be exercised to quash criminal proceedings when the allegations in the FIR do not disclose any cognizable offence.",
        para_no=12,
        court="Supreme Court of India",
        decision_date="2023-08-08",
    ),
    EvalCorpusItem(
        chunk_id=7,
        document_id=107,
        title="Government of Kerala v. Joseph",
        text="Adverse possession against the government requires continuous, uninterrupted, and hostile possession for thirty years with clear animus possidendi.",
        para_no=25,
        court="Supreme Court of India",
        decision_date="2023-08-09",
    ),
    EvalCorpusItem(
        chunk_id=8,
        document_id=108,
        title="Debashis Sinha v. R.N.R. Enterprise",
        text="Failure of builder to deliver possession of flat within the agreed timeframe constitutes deficiency of service under Consumer Protection Act.",
        para_no=16,
        court="Supreme Court of India",
        decision_date="2023-02-09",
    ),
    EvalCorpusItem(
        chunk_id=9,
        document_id=109,
        title="M. Suresh Kumar Reddy v. Canara Bank",
        text="Under Section 7 of the Insolvency and Bankruptcy Code (IBC), once default is established and application is complete, the adjudicating authority is bound to admit CIRP.",
        para_no=11,
        court="Supreme Court of India",
        decision_date="2023-05-11",
    ),
    EvalCorpusItem(
        chunk_id=10,
        document_id=110,
        title="State of Uttarakhand v. Smt. Mandodari Devi",
        text="Retrenchment of a workman without complying with mandatory conditions under Section 25F of the Industrial Disputes Act renders the termination void ab initio.",
        para_no=19,
        court="Supreme Court of India",
        decision_date="2023-03-24",
    ),
    # Additional realistic distractor passages from Indian legal domains
    EvalCorpusItem(
        chunk_id=11,
        document_id=111,
        title="Babu Venkatesh v. State of Karnataka",
        text="Application under Section 156(3) CrPC must be accompanied by an affidavit verifying the truth of the allegations as laid down in Priyanka Srivastava.",
        para_no=8,
        court="Supreme Court of India",
        decision_date="2022-02-18",
    ),
    EvalCorpusItem(
        chunk_id=12,
        document_id=112,
        title="Satender Kumar Antil v. CBI",
        text="Guidelines for grant of bail under Section 437 and 439 CrPC classified into categories depending on severity of punishment.",
        para_no=15,
        court="Supreme Court of India",
        decision_date="2022-07-11",
    ),
    EvalCorpusItem(
        chunk_id=13,
        document_id=113,
        title="Vidya Drolia v. Durga Trading Corporation",
        text="Landlord-tenant disputes governed by the Transfer of Property Act are arbitrable unless covered by special rent control legislation.",
        para_no=35,
        court="Supreme Court of India",
        decision_date="2020-12-14",
    ),
    EvalCorpusItem(
        chunk_id=14,
        document_id=114,
        title="Indore Development Authority v. Manoharlal",
        text="Lapse of land acquisition under Section 24(2) of the 2013 Act requires both physical possession not taken and compensation not tendered or deposited.",
        para_no=48,
        court="Supreme Court of India",
        decision_date="2020-03-06",
    ),
    EvalCorpusItem(
        chunk_id=15,
        document_id=115,
        title="S.P. Velayutham v. E. Nirmala",
        text="A registered power of attorney does not confer ownership or title in immovable property without a registered sale deed.",
        para_no=21,
        court="Supreme Court of India",
        decision_date="2023-08-11",
    ),
    EvalCorpusItem(
        chunk_id=16,
        document_id=116,
        title="M/s Larsen Air Conditioning v. Union of India",
        text="Courts exercising powers under Section 34 of the Arbitration Act do not have the power to modify arbitral awards.",
        para_no=14,
        court="Supreme Court of India",
        decision_date="2023-08-11",
    ),
    EvalCorpusItem(
        chunk_id=17,
        document_id=117,
        title="State of Haryana v. Dinesh Kumar",
        text="Arrest under criminal law involves restraint of liberty and custody by police officer, not merely summoning to the police station.",
        para_no=10,
        court="Supreme Court of India",
        decision_date="2008-01-11",
    ),
    EvalCorpusItem(
        chunk_id=18,
        document_id=118,
        title="Kotak Mahindra Bank v. A. Balakrishnan",
        text="Recovery certificate issued under the RDDBFI Act initiates a fresh cause of action and constitutes financial debt under Section 5(8) IBC.",
        para_no=29,
        court="Supreme Court of India",
        decision_date="2022-05-30",
    ),
    EvalCorpusItem(
        chunk_id=19,
        document_id=119,
        title="Celir LLP v. Bafna Motors Mumbai Pvt Ltd",
        text="Borrower right of redemption under Section 13(8) SARFAESI Act is extinguished upon publication of auction notice.",
        para_no=37,
        court="Supreme Court of India",
        decision_date="2023-09-21",
    ),
    EvalCorpusItem(
        chunk_id=20,
        document_id=120,
        title="Union of India v. Mohit Minerals",
        text="Recommendations of the GST Council are not binding on Parliament and State Legislatures; competitive federalism applies.",
        para_no=54,
        court="Supreme Court of India",
        decision_date="2022-05-19",
    ),
]

DEFAULT_BENCHMARK_QUERIES: list[EvalQuery] = [
    EvalQuery(
        query_id="Q-01",
        text="readiness and willingness in suit for specific performance under Specific Relief Act",
        relevant_chunk_ids={1},
        domain="civil_contract",
    ),
    EvalQuery(
        query_id="Q-02",
        text="service tax levy on user development fee collected by airport authority",
        relevant_chunk_ids={2},
        domain="taxation",
    ),
    EvalQuery(
        query_id="Q-03",
        text="scope of patent illegality for setting aside arbitral award under Section 34",
        relevant_chunk_ids={3},
        domain="arbitration",
    ),
    EvalQuery(
        query_id="Q-04",
        text="proportionality test and right to privacy under Article 21",
        relevant_chunk_ids={4},
        domain="constitutional",
    ),
    EvalQuery(
        query_id="Q-05",
        text="conviction based solely on dying declaration under Indian Evidence Act",
        relevant_chunk_ids={5},
        domain="criminal_evidence",
    ),
    EvalQuery(
        query_id="Q-06",
        text="quashing of FIR under Section 482 CrPC when no cognizable offence disclosed",
        relevant_chunk_ids={6},
        domain="criminal_procedure",
    ),
    EvalQuery(
        query_id="Q-07",
        text="thirty years adverse possession hostile title against government land",
        relevant_chunk_ids={7},
        domain="property",
    ),
    EvalQuery(
        query_id="Q-08",
        text="builder delay in handover of flat possession deficiency of service consumer court",
        relevant_chunk_ids={8},
        domain="consumer",
    ),
    EvalQuery(
        query_id="Q-09",
        text="admission of Section 7 application for corporate insolvency under IBC",
        relevant_chunk_ids={9},
        domain="insolvency",
    ),
    EvalQuery(
        query_id="Q-10",
        text="retrenchment of workman without complying with Section 25F Industrial Disputes Act",
        relevant_chunk_ids={10},
        domain="labour",
    ),
]


def load_benchmark_dataset(file_path: str | Path | None = None) -> EvaluationDataset:
    """Load benchmark retrieval dataset.

    If file_path is provided and exists, loads from JSON; otherwise returns
    the standardized LJ-Retrieval-Benchmark covering 10 Indian legal domains.
    """
    if file_path:
        p = Path(file_path)
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            queries = [
                EvalQuery(
                    query_id=q["query_id"],
                    text=q["text"],
                    relevant_chunk_ids=set(q["relevant_chunk_ids"]),
                    domain=q.get("domain", "general"),
                )
                for q in data["queries"]
            ]
            corpus = [
                EvalCorpusItem(
                    chunk_id=c["chunk_id"],
                    document_id=c["document_id"],
                    title=c["title"],
                    text=c["text"],
                    para_no=c.get("para_no"),
                    court=c.get("court", "Supreme Court of India"),
                    decision_date=c.get("decision_date"),
                )
                for c in data["corpus"]
            ]
            return EvaluationDataset(
                name=data.get("name", "Custom-Benchmark"),
                version=data.get("version", "1.0"),
                queries=queries,
                corpus=corpus,
            )

    return EvaluationDataset(
        name="LJ-Retrieval-Benchmark",
        version="1.0.0",
        queries=DEFAULT_BENCHMARK_QUERIES,
        corpus=DEFAULT_BENCHMARK_CORPUS,
    )
