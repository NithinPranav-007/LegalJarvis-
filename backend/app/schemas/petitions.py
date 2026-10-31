"""Pydantic schemas for Petition Generator."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class PartyDetail(BaseModel):
    name: str = Field(..., description="Full name of party or institution")
    age: str | None = Field(None, description="Age of party, if individual")
    relation: str | None = Field(None, description="Son/Daughter/Spouse of / Authorized Representative")
    address: str = Field(..., description="Complete physical or official address")
    role: str = Field("Petitioner", description="Role e.g. Petitioner No. 1, Accused, State, Complainant")
    phone: str | None = None
    email: str | None = None
    advocate_name: str | None = None
    advocate_bar_id: str | None = None


class EventDetail(BaseModel):
    date: str = Field(..., description="Date of the occurrence or event (e.g. 15.01.2024 or 'January 2024')")
    description: str = Field(..., description="Description of the factual event or procedural milestone")


class PreviousOrderDetail(BaseModel):
    court: str = Field(..., description="Court or authority passing the impugned order")
    date: str = Field(..., description="Date of the order")
    summary: str = Field(..., description="Summary of directions or findings")


class AnnexureDetail(BaseModel):
    mark: str = Field(..., description="Annexure marker (e.g. 'P-1', 'A-1')")
    title: str = Field(..., description="Title of document (e.g. 'True Copy of FIR No. 123/2024')")
    description: str | None = Field(None, description="Brief note on document contents and relevance")


class PetitionCreateRequest(BaseModel):
    petition_type: str = Field(
        ...,
        description="Type: 'writ_petition' | 'bail_application' | 'pil' | 'civil_petition' | 'criminal_revision' | 'custom_petition'",
    )
    court_level: str = Field("supreme_court", description="'supreme_court' | 'high_court' | 'district_court'")
    court_name: str = Field("Supreme Court of India", description="Exact court name")
    state_ut: str | None = Field(None, description="State or Union Territory for jurisdiction")
    category: str = Field("constitutional", description="'constitutional' | 'criminal' | 'civil' | 'special_leave'")
    case_number: str | None = Field(None, description="Existing case / petition number if allotted")
    statutory_provisions: str | None = Field(None, description="Key statutory provisions e.g. Article 32, Section 439 CrPC / 483 BNSS")
    petitioners: list[PartyDetail] = Field(default_factory=list)
    respondents: list[PartyDetail] = Field(default_factory=list)
    dispute_background: str = Field(..., description="Narrative overview of the dispute")
    events: list[EventDetail] = Field(default_factory=list)
    previous_orders: list[PreviousOrderDetail] = Field(default_factory=list)
    annexures: list[AnnexureDetail] = Field(default_factory=list)
    grounds: list[str] = Field(default_factory=list, description="Grounds of law")
    rights_infringed: list[str] = Field(default_factory=list, description="Rights infringed e.g. Article 14, 19(1)(a), 21")
    statutes_applied: list[str] = Field(default_factory=list, description="Applicable statutes")
    urgency_reason: str | None = Field(None, description="Reason for urgent listing or ex-parte interim stay")
    limitation_explanation: str | None = Field(None, description="Explanation on limitation period or condonation of delay")
    main_prayers: list[str] = Field(default_factory=list, description="Final reliefs sought")
    interim_prayers: list[str] = Field(default_factory=list, description="Interim reliefs or ad-interim stays sought")


class PetitionUpdateRequest(BaseModel):
    title: str | None = None
    status: str | None = None
    sections: dict[str, str] | None = None
    full_text: str | None = None
    petitioner_details: list[dict[str, Any]] | None = None
    respondent_details: list[dict[str, Any]] | None = None
    facts_chronology: dict[str, Any] | None = None
    legal_grounds: dict[str, Any] | None = None
    prayer_relief: dict[str, Any] | None = None


class SectionRegenerateRequest(BaseModel):
    petition_id: int | None = None
    petition_type: str
    section_key: str
    custom_instruction: str | None = None
    current_sections: dict[str, str]
    draft_metadata: dict[str, Any]


class PetitionCitation(BaseModel):
    marker: str = Field(..., description="e.g. [C1]")
    chunk_id: int | None = None
    document_id: int | None = None
    title: str
    court: str
    neutral_citation: str | None = None
    para_no: int | None = None
    snippet: str
    support_status: str = Field("verified", description="'verified' | 'requires_verification'")
    is_binding: bool = Field(True, description="True if Supreme Court / jurisdictional High Court")
    relevance_explanation: str


class PetitionResponse(BaseModel):
    id: int | None = None
    title: str
    petition_type: str
    court_level: str
    court_name: str
    state_ut: str | None = None
    category: str
    case_number: str | None = None
    sections: dict[str, str]
    full_text: str
    citations: list[PetitionCitation] = Field(default_factory=list)
    verification_warnings: list[str] = Field(default_factory=list)
    status: str = "generated"
    created_at: str | None = None
    updated_at: str | None = None
    disclaimer: str = (
        "Needhi Petition Generator is an AI-assisted legal research and draft preparation tool. "
        "The generated draft is an informational work product grounded in retrieved legal precedents and Indian court formats. "
        "It DOES NOT constitute court-ready legal advice. Every proposition, date, and citation MUST be independently "
        "verified, finalized, and signed by a licensed advocate before filing in any court."
    )


class SectionRegenerateResponse(BaseModel):
    section_key: str
    content: str
    citations: list[PetitionCitation] = Field(default_factory=list)
    verification_warnings: list[str] = Field(default_factory=list)


class PetitionDraftListItem(BaseModel):
    id: int
    title: str
    petition_type: str
    court_name: str
    petitioner_name: str
    respondent_name: str
    status: str
    created_at: str
    updated_at: str
