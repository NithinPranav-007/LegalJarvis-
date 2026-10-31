"""SQLAlchemy 2.0 ORM Models matching PRD Section D7 Core SQL Schema."""

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.core.config import settings
from app.db.session import Base

try:
    from pgvector.sqlalchemy import Vector as PgVector
except ImportError:
    PgVector = None  # type: ignore

# 64-bit autoincrement primary key type compatible with both PostgreSQL and SQLite
PK_BIGINT = BigInteger().with_variant(Integer, "sqlite")


class VectorColumn(TypeDecorator):
    """Dialect-agnostic vector column: uses pgvector on Postgres, JSON text on SQLite/others."""

    impl = Text
    cache_ok = True

    def __init__(self, dim: int = settings.EMBED_DIMENSION):
        super().__init__()
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql" and PgVector is not None:
            return dialect.type_descriptor(PgVector(self.dim))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and PgVector is not None:
            return value
        if isinstance(value, list | tuple):
            return json.dumps(list(value))
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        if dialect.name == "postgresql" and PgVector is not None:
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class DatasetSnapshot(Base):
    __tablename__ = "dataset_snapshots"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    source_key: Mapped[str] = mapped_column(String, nullable=False)  # 'sc_judgments','india_code'
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    license: Mapped[str] = mapped_column(String, nullable=False)
    attribution: Mapped[str] = mapped_column(String, nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    snapshot_note: Mapped[str | None] = mapped_column(String, nullable=True)
    manifest_path: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_key", "acquired_at", name="uq_snapshot_source_acquired"),
    )

    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("dataset_snapshots.id"), nullable=False
    )
    params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'running','success','partial','failed'
    n_downloaded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_registered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    n_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    git_commit: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('running','success','partial','failed')", name="ck_ingest_status"
        ),
    )

    snapshot: Mapped["DatasetSnapshot"] = relationship(back_populates="ingestion_runs")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="ingestion_run", cascade="all, delete-orphan"
    )


class Court(Base):
    __tablename__ = "courts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # 'sc', 'delhi_hc'
    name: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)  # 'supreme','high'

    __table_args__ = (CheckConstraint("level IN ('supreme','high')", name="ck_court_level"),)

    documents: Mapped[list["Document"]] = relationship(back_populates="court")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    run_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("ingestion_runs.id"), nullable=True)
    court_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("courts.id"), nullable=True)
    external_id: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    neutral_citation: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str] = mapped_column(String, nullable=False, default="en")
    source_file_path: Mapped[str] = mapped_column(String, nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    text_path: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_status: Mapped[str] = mapped_column(
        String, nullable=False, default="pending"
    )  # 'pending','ok','ocr','failed','skipped_lang'
    extraction_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("court_id", "external_id", name="uq_doc_court_external"),
        CheckConstraint(
            "extraction_status IN ('pending','ok','ocr','failed','skipped_lang')",
            name="ck_doc_extraction_status",
        ),
        Index("idx_doc_date", "decision_date"),
        Index("idx_doc_court", "court_id"),
        Index("idx_doc_owner", "owner_user_id"),
    )

    ingestion_run: Mapped["IngestionRun | None"] = relationship(back_populates="documents")
    court: Mapped["Court | None"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    statute_references: Mapped[list["StatuteReference"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chunks.id"), nullable=True
    )
    para_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segment_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # 'facts','issues','arguments','reasoning','holding','other'
    start_char: Mapped[int] = mapped_column(Integer, nullable=False)
    end_char: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Any | None] = mapped_column(
        VectorColumn(settings.EMBED_DIMENSION), nullable=True
    )
    embed_model: Mapped[str | None] = mapped_column(String, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("end_char > start_char", name="ck_chunk_offsets"),
        CheckConstraint(
            "segment_type IS NULL OR segment_type IN ('facts','issues','arguments','reasoning','holding','other')",
            name="ck_chunk_segment_type",
        ),
        Index("idx_chunk_doc", "document_id"),
        Index("idx_chunk_owner", "owner_user_id"),
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")
    parent: Mapped["Chunk | None"] = relationship(remote_side=[id])


class CaseCitation(Base):
    __tablename__ = "case_citations"

    citing_document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    cited_string: Mapped[str] = mapped_column(String, primary_key=True)
    cited_document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("documents.id"), nullable=True
    )


class Statute(Base):
    __tablename__ = "statutes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    short_name: Mapped[str] = mapped_column(String, nullable=False)  # 'BNS', 'IPC'
    act_year: Mapped[int] = mapped_column(Integer, nullable=False)
    act_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (UniqueConstraint("short_name", "act_year", name="uq_statute_short_year"),)

    versions: Mapped[list["StatuteVersion"]] = relationship(
        back_populates="statute", cascade="all, delete-orphan"
    )


class StatuteVersion(Base):
    __tablename__ = "statute_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    statute_id: Mapped[int] = mapped_column(Integer, ForeignKey("statutes.id"), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'in_force','repealed','partially_in_force'
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('in_force','repealed','partially_in_force')",
            name="ck_statute_status",
        ),
    )

    statute: Mapped["Statute"] = relationship(back_populates="versions")
    sections: Mapped[list["StatuteSection"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class StatuteSection(Base):
    __tablename__ = "statute_sections"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("statute_versions.id"), nullable=False
    )
    section_no: Mapped[str] = mapped_column(String, nullable=False)  # '302', '103'
    heading: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("chunks.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("version_id", "section_no", name="uq_statute_version_section"),
    )

    version: Mapped["StatuteVersion"] = relationship(back_populates="sections")


class StatuteReference(Base):
    __tablename__ = "statute_references"

    document_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )
    section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("statute_sections.id"), primary_key=True
    )

    document: Mapped["Document"] = relationship(back_populates="statute_references")


class StatuteConcordance(Base):
    """Verified, reviewer-signed mappings between old codes (IPC/CrPC) and new codes (BNS/BNSS)."""

    __tablename__ = "statute_concordance"

    old_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("statute_sections.id"), primary_key=True
    )
    new_section_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("statute_sections.id"), primary_key=True
    )
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String, nullable=False)
    reviewed_at: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'researcher','reviewer','admin'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("role IN ('researcher','reviewer','admin','citizen')", name="ck_user_role"),
    )

    user_documents: Mapped[list["UserDocument"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserDocument(Base):
    __tablename__ = "user_documents"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'pending','processed','failed'
    document_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="user_documents")
    document: Mapped["Document | None"] = relationship()


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False)  # 'user','assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (CheckConstraint("role IN ('user','assistant')", name="ck_message_role"),)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    answer: Mapped["Answer | None"] = relationship(
        back_populates="message", uselist=False, cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    model_id: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    retrieval_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    abstained: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    message: Mapped["Message"] = relationship(back_populates="answer")
    citations: Mapped[list["AnswerCitation"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan"
    )
    feedbacks: Mapped[list["Feedback"]] = relationship(
        back_populates="answer", cascade="all, delete-orphan"
    )


class AnswerCitation(Base):
    __tablename__ = "answer_citations"

    answer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("answers.id", ondelete="CASCADE"), primary_key=True
    )
    chunk_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chunks.id"), primary_key=True)
    marker: Mapped[str] = mapped_column(String, primary_key=True)  # '[C1]', '[C2]'
    support_status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'supported','unsupported','unchecked'

    __table_args__ = (
        CheckConstraint(
            "support_status IN ('supported','unsupported','unchecked')",
            name="ck_cite_support_status",
        ),
    )

    answer: Mapped["Answer"] = relationship(back_populates="citations")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    answer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    rating: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)  # -1 or 1, or 1-5
    label: Mapped[str | None] = mapped_column(
        String, nullable=True
    )  # 'supported','unsupported','hallucinated','incomplete','wrong_law'
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_role: Mapped[str | None] = mapped_column(String, nullable=True)
    claims_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("rating IN (-1, 1, 2, 3, 4, 5)", name="ck_feedback_rating"),
        CheckConstraint(
            "label IS NULL OR label IN ('supported','unsupported','hallucinated','incomplete','wrong_law')",
            name="ck_feedback_label",
        ),
    )

    answer: Mapped["Answer"] = relationship(back_populates="feedbacks")


class EvalDataset(Base):
    __tablename__ = "eval_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    origin: Mapped[str] = mapped_column(String, nullable=False)
    synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    license: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_eval_dataset_name_version"),)

    items: Mapped[list["EvalItem"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan"
    )


class EvalItem(Base):
    __tablename__ = "eval_items"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    dataset_id: Mapped[int] = mapped_column(Integer, ForeignKey("eval_datasets.id"), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    gold: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    dataset: Mapped["EvalDataset"] = relationship(back_populates="items")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    git_commit: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    results: Mapped[list["EvalResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class EvalResult(Base):
    __tablename__ = "eval_results"

    run_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("eval_runs.id", ondelete="CASCADE"), primary_key=True
    )
    item_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("eval_items.id"), primary_key=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    run: Mapped["EvalRun"] = relationship(back_populates="results")


class Petition(Base):
    __tablename__ = "petitions"

    id: Mapped[int] = mapped_column(PK_BIGINT, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    petition_type: Mapped[str] = mapped_column(String, nullable=False)  # 'writ_petition', 'bail_application', 'pil', etc.
    court_level: Mapped[str] = mapped_column(String, nullable=False)    # 'supreme_court', 'high_court', 'district_court'
    court_name: Mapped[str] = mapped_column(String, nullable=False)
    state_ut: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str] = mapped_column(String, nullable=False, default="constitutional")
    case_number: Mapped[str | None] = mapped_column(String, nullable=True)
    statutory_provisions: Mapped[str | None] = mapped_column(Text, nullable=True)
    petitioner_details: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    respondent_details: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    facts_chronology: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    legal_grounds: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    prayer_relief: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    generated_document: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    citations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    verification_warnings: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")  # 'draft', 'generated', 'reviewed'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User | None"] = relationship()

