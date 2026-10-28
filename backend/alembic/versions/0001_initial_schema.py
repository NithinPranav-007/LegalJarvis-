"""0001 Initial Schema for LegalJarvis

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-28 11:15:00.000000
"""

import sqlalchemy as sa

from alembic import op

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    pk_bigint = sa.BigInteger().with_variant(sa.Integer(), "sqlite")

    # Enable postgres extensions if on postgresql
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 1. dataset_snapshots
    op.create_table(
        "dataset_snapshots",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("source_key", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("license", sa.String(), nullable=False),
        sa.Column("attribution", sa.String(), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("snapshot_note", sa.String(), nullable=True),
        sa.Column("manifest_path", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_key", "acquired_at", name="uq_snapshot_source_acquired"),
    )

    # 2. ingestion_runs
    op.create_table(
        "ingestion_runs",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), sa.ForeignKey("dataset_snapshots.id"), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("n_downloaded", sa.Integer(), nullable=False, default=0),
        sa.Column("n_registered", sa.Integer(), nullable=False, default=0),
        sa.Column("n_failed", sa.Integer(), nullable=False, default=0),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("git_commit", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('running','success','partial','failed')", name="ck_ingest_status"),
    )

    # 3. courts
    courts_table = op.create_table(
        "courts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_court_code"),
        sa.CheckConstraint("level IN ('supreme','high')", name="ck_court_level"),
    )

    # 4. users
    op.create_table(
        "users",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_user_email"),
        sa.CheckConstraint("role IN ('researcher','reviewer','admin')", name="ck_user_role"),
    )

    # 5. documents
    op.create_table(
        "documents",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("ingestion_runs.id"), nullable=False),
        sa.Column("court_id", sa.Integer(), sa.ForeignKey("courts.id"), nullable=True),
        sa.Column("external_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("neutral_citation", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=False, default="en"),
        sa.Column("source_file_path", sa.String(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("text_path", sa.String(), nullable=True),
        sa.Column("extraction_status", sa.String(), nullable=False, default="pending"),
        sa.Column("extraction_quality", sa.Float(), nullable=True),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("court_id", "external_id", name="uq_doc_court_external"),
        sa.CheckConstraint("extraction_status IN ('pending','ok','ocr','failed','skipped_lang')", name="ck_doc_extraction_status"),
    )
    op.create_index("idx_doc_date", "documents", ["decision_date"])
    op.create_index("idx_doc_court", "documents", ["court_id"])

    # 6. chunks
    vector_type = Vector(1024) if (bind.dialect.name == "postgresql" and Vector is not None) else sa.Text()
    op.create_table(
        "chunks",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.BigInteger(), sa.ForeignKey("chunks.id"), nullable=True),
        sa.Column("para_no", sa.Integer(), nullable=True),
        sa.Column("segment_type", sa.String(), nullable=True),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", vector_type, nullable=True),
        sa.Column("embed_model", sa.String(), nullable=True),
        sa.Column("owner_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("synthetic", sa.Boolean(), nullable=False, default=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_char > start_char", name="ck_chunk_offsets"),
        sa.CheckConstraint("segment_type IS NULL OR segment_type IN ('facts','issues','arguments','reasoning','holding','other')", name="ck_chunk_segment_type"),
    )
    op.create_index("idx_chunk_doc", "chunks", ["document_id"])
    op.create_index("idx_chunk_owner", "chunks", ["owner_user_id"])

    # 7. case_citations
    op.create_table(
        "case_citations",
        sa.Column("citing_document_id", sa.BigInteger(), sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("cited_string", sa.String(), primary_key=True),
        sa.Column("cited_document_id", sa.BigInteger(), sa.ForeignKey("documents.id"), nullable=True),
    )

    # 8. statutes
    op.create_table(
        "statutes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("short_name", sa.String(), nullable=False),
        sa.Column("act_year", sa.Integer(), nullable=False),
        sa.Column("act_no", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("short_name", "act_year", name="uq_statute_short_year"),
    )

    # 9. statute_versions
    op.create_table(
        "statute_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("statute_id", sa.Integer(), sa.ForeignKey("statutes.id"), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('in_force','repealed','partially_in_force')", name="ck_statute_status"),
    )

    # 10. statute_sections
    op.create_table(
        "statute_sections",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("version_id", sa.Integer(), sa.ForeignKey("statute_versions.id"), nullable=False),
        sa.Column("section_no", sa.String(), nullable=False),
        sa.Column("heading", sa.String(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_id", sa.BigInteger(), sa.ForeignKey("chunks.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id", "section_no", name="uq_statute_version_section"),
    )

    # 11. statute_references
    op.create_table(
        "statute_references",
        sa.Column("document_id", sa.BigInteger(), sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("section_id", sa.BigInteger(), sa.ForeignKey("statute_sections.id"), primary_key=True),
    )

    # 12. statute_concordance
    op.create_table(
        "statute_concordance",
        sa.Column("old_section_id", sa.BigInteger(), sa.ForeignKey("statute_sections.id"), primary_key=True),
        sa.Column("new_section_id", sa.BigInteger(), sa.ForeignKey("statute_sections.id"), primary_key=True),
        sa.Column("source_url", sa.String(), nullable=False),
        sa.Column("reviewed_by", sa.String(), nullable=False),
        sa.Column("reviewed_at", sa.Date(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )

    # 13. user_documents
    op.create_table(
        "user_documents",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 14. conversations
    op.create_table(
        "conversations",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 15. messages
    op.create_table(
        "messages",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("role IN ('user','assistant')", name="ck_message_role"),
    )

    # 16. answers
    op.create_table(
        "answers",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("message_id", sa.BigInteger(), sa.ForeignKey("messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("retrieval_ids", sa.JSON(), nullable=False),
        sa.Column("abstained", sa.Boolean(), nullable=False),
        sa.Column("verification", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 17. answer_citations
    op.create_table(
        "answer_citations",
        sa.Column("answer_id", sa.BigInteger(), sa.ForeignKey("answers.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("chunk_id", sa.BigInteger(), sa.ForeignKey("chunks.id"), primary_key=True),
        sa.Column("marker", sa.String(), primary_key=True),
        sa.Column("support_status", sa.String(), nullable=False),
        sa.CheckConstraint("support_status IN ('supported','unsupported','unchecked')", name="ck_cite_support_status"),
    )

    # 18. feedback
    op.create_table(
        "feedback",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("answer_id", sa.BigInteger(), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("rating IN (-1, 1)", name="ck_feedback_rating"),
        sa.CheckConstraint("label IS NULL OR label IN ('supported','unsupported','hallucinated','incomplete','wrong_law')", name="ck_feedback_label"),
    )

    # 19. eval_datasets
    op.create_table(
        "eval_datasets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("origin", sa.String(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False, default=False),
        sa.Column("license", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_eval_dataset_name_version"),
    )

    # 20. eval_items
    op.create_table(
        "eval_items",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("eval_datasets.id"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("gold", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 21. eval_runs
    op.create_table(
        "eval_runs",
        sa.Column("id", pk_bigint, autoincrement=True, nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("git_commit", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 22. eval_results
    op.create_table(
        "eval_results",
        sa.Column("run_id", sa.BigInteger(), sa.ForeignKey("eval_runs.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("item_id", sa.BigInteger(), sa.ForeignKey("eval_items.id"), primary_key=True),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
    )

    # Seed initial courts
    op.bulk_insert(
        courts_table,
        [
            {"code": "sc", "name": "Supreme Court of India", "level": "supreme"},
            {"code": "delhi_hc", "name": "High Court of Delhi", "level": "high"},
            {"code": "bombay_hc", "name": "High Court of Bombay", "level": "high"},
            {"code": "madras_hc", "name": "High Court of Madras", "level": "high"},
            {"code": "calcutta_hc", "name": "High Court of Calcutta", "level": "high"},
        ],
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("eval_results")
    op.drop_table("eval_runs")
    op.drop_table("eval_items")
    op.drop_table("eval_datasets")
    op.drop_table("feedback")
    op.drop_table("answer_citations")
    op.drop_table("answers")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("user_documents")
    op.drop_table("statute_concordance")
    op.drop_table("statute_references")
    op.drop_table("statute_sections")
    op.drop_table("statute_versions")
    op.drop_table("statutes")
    op.drop_table("case_citations")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("users")
    op.drop_table("courts")
    op.drop_table("ingestion_runs")
    op.drop_table("dataset_snapshots")
