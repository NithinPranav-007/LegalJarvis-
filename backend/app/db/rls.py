"""PostgreSQL Row-Level Security (RLS) policies for user document and chunk isolation (Task T-17 / FR-08)."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

POSTGRES_RLS_STATEMENTS = [
    "ALTER TABLE documents ENABLE ROW LEVEL SECURITY;",
    "ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies WHERE tablename = 'documents' AND policyname = 'documents_isolation_policy'
        ) THEN
            CREATE POLICY documents_isolation_policy ON documents
            FOR ALL
            USING (owner_user_id IS NULL OR owner_user_id = NULLIF(current_setting('app.current_user_id', true), '')::bigint);
        END IF;
    END $$;
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies WHERE tablename = 'chunks' AND policyname = 'chunks_isolation_policy'
        ) THEN
            CREATE POLICY chunks_isolation_policy ON chunks
            FOR ALL
            USING (owner_user_id IS NULL OR owner_user_id = NULLIF(current_setting('app.current_user_id', true), '')::bigint);
        END IF;
    END $$;
    """,
]


def apply_postgres_rls(engine: Engine) -> bool:
    """Execute Row-Level Security DDL if dialect is PostgreSQL."""
    if engine.dialect.name != "postgresql":
        return False

    with engine.begin() as conn:
        for stmt in POSTGRES_RLS_STATEMENTS:
            conn.execute(text(stmt))
    return True


def set_rls_session_user(session: Session, user_id: int | None) -> None:
    """Set the session-local user ID variable for PostgreSQL RLS filtering."""
    if session.get_bind().dialect.name == "postgresql":
        uid_str = str(user_id) if user_id is not None else ""
        session.execute(text(f"SET LOCAL app.current_user_id = '{uid_str}'"))
