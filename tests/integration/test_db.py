import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_database_connection(pg_engine):
    """Kiểm tra kết nối tới PostgreSQL test (TEST_DATABASE_URL), không dùng DB dev."""
    with pg_engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1
        assert conn.execute(text("SELECT current_database()")).scalar().endswith("_test")


def test_pgvector_extension_and_tables_exist(pg_engine):
    with pg_engine.connect() as conn:
        ext = conn.execute(text("SELECT count(*) FROM pg_extension WHERE extname = 'vector'")).scalar()
        tables = {
            r[0]
            for r in conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
        }
    assert ext == 1
    assert {"USER", "PROFILE", "PROFILE_SKILL", "JD", "JD_SKILL"} <= tables
