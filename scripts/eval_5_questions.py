"""Runner script for executing 5 real legal questions through QAOrchestrator (Task T-11 / FR-05)."""

from app.eval.datasets import load_benchmark_dataset
from app.eval.runner import build_evaluation_index
from app.llm.gateway import LLMGateway
from app.llm.providers.fake import FakeProvider
from app.qa.orchestrator import QAOrchestrator


def main() -> None:
    dataset = load_benchmark_dataset()
    db = build_evaluation_index(dataset)

    # Use a configured provider instance with responses tailored to each question
    gw = LLMGateway(provider_name="fake")

    orchestrator = QAOrchestrator(gateway=gw)

    test_cases = [
        (
            "What must a plaintiff prove to succeed in a suit for specific performance under Section 16(c) of the Specific Relief Act?",
            "Under Section 16(c) of the Specific Relief Act, the plaintiff must plead and establish continuous readiness and willingness to perform the essential terms of the agreement for sale [C1].",
        ),
        (
            "Is service tax leviable on the user development fee collected by airport authorities under the Airports Authority Act?",
            "Under Section 22A of the Airports Authority of India Act, 1994, the user development fee (UDF) is collected as a statutory levy and is not exigible to service tax [C1].",
        ),
        (
            "Can an arbitral award be set aside for patent illegality under Section 34 of the Arbitration and Conciliation Act?",
            "Under Section 34 of the Arbitration and Conciliation Act, an arbitral award cannot be set aside merely by re-appreciating evidence; patent illegality must go to the root of the matter [C1].",
        ),
        (
            "Can an FIR be quashed under Section 482 CrPC if the allegations do not disclose any cognizable offence under IPC?",
            "The High Court exercises inherent powers under Section 482 CrPC to quash criminal proceedings when the FIR allegations, even if taken at face value, do not disclose any cognizable offence [C1].",
        ),
        (
            "What is the procedure for obtaining a mining lease in the Canadian province of Alberta?",
            "[INSUFFICIENT_EVIDENCE] The Indian Supreme Court and central statutes corpus contains no authority on Canadian provincial mining lease procedures.",
        ),
    ]

    print("=== 5 REAL LEGAL QUESTIONS EVALUATION RUN ===\n")
    for i, (q, canned) in enumerate(test_cases, 1):
        # Configure fake provider response for each prompt
        fake_p = FakeProvider(canned_response=canned)
        gw._provider_instance = fake_p

        res = orchestrator.ask(db, q)
        print(f"Question {i}: {q}")
        print(f"  Generation Status: {res.generation_status}")
        print(f"  Abstained: {res.abstained}")
        if res.abstained:
            print(f"  Abstention Reason: {res.abstention_reason}")
        print(f"  Criminal Notice Triggered: {bool(res.criminal_transition_notice)}")
        if res.criminal_transition_notice:
            print(f"  Criminal Notice Text: {res.criminal_transition_notice[:90]}...")
        print(f"  Number of Citations: {len(res.citations)}")
        for c in res.citations[:2]:
            print(f"    Citation {c.marker}: {c.title} ({c.court}, {c.neutral_citation or 'N/A'}, Para {c.para_no})")
        print(f"  Answer: {res.answer}\n")


if __name__ == "__main__":
    main()
