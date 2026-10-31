"""Integration tests for Petition Generator endpoints (Task T-19)."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_petitions_endpoint():
    """Verify listing petition drafts."""
    response = client.get("/v1/petitions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_generate_petition_endpoint():
    """Verify petition generation with validation and structured section output."""
    payload = {
        "petition_type": "bail_application",
        "court_level": "high_court",
        "court_name": "High Court of Delhi at New Delhi",
        "state_ut": "Delhi",
        "category": "criminal",
        "statutory_provisions": "Section 439 CrPC / Section 483 BNSS 2023",
        "dispute_background": "Petitioner falsely implicated in commercial dispute under alleged Section 420 IPC / 318(4) BNS.",
        "petitioners": [
            {
                "name": "Amitabh Sen",
                "age": "39",
                "relation": "S/o Late K.L. Sen",
                "address": "B-12, Greater Kailash-I, New Delhi",
                "role": "Accused / Applicant",
            }
        ],
        "respondents": [
            {
                "name": "State (NCT of Delhi)",
                "address": "Through SHO, PS Crime Branch, New Delhi",
                "role": "Respondent",
            }
        ],
        "events": [
            {"date": "01.09.2026", "description": "FIR registered without preliminary enquiry."},
            {"date": "15.09.2026", "description": "Petitioner joined investigation and cooperated fully."}
        ],
        "grounds": [
            "Petitioner has deep roots in society and is not a flight risk.",
            "Entire dispute is of a civil nature arising out of commercial contract.",
            "Investigation is complete and charge-sheet is filed; custodial interrogation not required."
        ],
        "rights_infringed": ["Article 21"],
        "statutes_applied": ["Code of Criminal Procedure, 1973", "Bharatiya Nagarik Suraksha Sanhita, 2023"],
        "main_prayers": [
            "Enlarge the Petitioner on regular bail on such terms and conditions as this Hon'ble Court may deem fit."
        ],
        "interim_prayers": [
            "Grant interim bail during the pendency of the present bail application."
        ]
    }

    response = client.post("/v1/petitions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["petition_type"] == "bail_application"
    assert "sections" in data
    assert "facts_and_chronology" in data["sections"]
    assert "grounds" in data["sections"]
    assert "prayer" in data["sections"]
    assert "verification" in data["sections"]
    assert len(data["citations"]) > 0

    petition_id = data["id"]

    # Test get petition by id
    get_res = client.get(f"/v1/petitions/{petition_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == petition_id

    # Test update petition draft
    put_res = client.put(f"/v1/petitions/{petition_id}", json={"status": "reviewed"})
    assert put_res.status_code == 200
    assert put_res.json()["status"] == "reviewed"

    # Test DOCX export
    docx_res = client.get(f"/v1/petitions/{petition_id}/export/docx")
    assert docx_res.status_code == 200
    assert "wordprocessingml" in docx_res.headers["content-type"]
    assert len(docx_res.content) > 1000

    # Test PDF export
    pdf_res = client.get(f"/v1/petitions/{petition_id}/export/pdf")
    assert pdf_res.status_code == 200
    assert "pdf" in pdf_res.headers["content-type"]
    assert len(pdf_res.content) > 1000

    # Test Section Regeneration
    regen_res = client.post(
        "/v1/petitions/regenerate-section",
        json={
            "petition_id": petition_id,
            "petition_type": "bail_application",
            "section_key": "grounds",
            "custom_instruction": "Add parity with co-accused granted bail.",
            "current_sections": data["sections"],
            "draft_metadata": {}
        }
    )
    assert regen_res.status_code == 200
    regen_data = regen_res.json()
    assert regen_data["section_key"] == "grounds"
    assert len(regen_data["content"]) > 20

    # Test Delete
    del_res = client.delete(f"/v1/petitions/{petition_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
