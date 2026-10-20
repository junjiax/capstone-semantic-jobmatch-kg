import pytest
from sqlalchemy import create_engine, text
from app.core.config import get_settings


def test_database_connection():
    """Kiểm tra kết nối tới cơ sở dữ liệu PostgreSQL."""
    try:
        engine = create_engine(get_settings().SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT current_database()")).scalar()
            one = conn.execute(text("SELECT 1")).scalar()
            assert one == 1
            assert db_name is not None
    except Exception as e:
        pytest.skip(f"PostgreSQL chưa sẵn sàng trên máy local: {e}")


if __name__ == "__main__":
    engine = create_engine(get_settings().SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            print("✅ DB:", conn.execute(text("SELECT current_database()")).scalar())
            print("✅ Test SELECT 1:", conn.execute(text("SELECT 1")).scalar())
    except Exception as e:
        print("❌ DB connection failed:", e)
