from sqlalchemy import create_engine, text
from app.core.config import get_settings

engine = create_engine(get_settings().SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)

try:
    with engine.connect() as conn:
        print("✅ DB:", conn.execute(text("SELECT current_database()")).scalar())
        print("✅ Test SELECT 1:", conn.execute(text("SELECT 1")).scalar())
except Exception as e:
    print("❌ DB connection failed:", e)
