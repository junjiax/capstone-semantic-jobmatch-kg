"""Create current model tables and copy legacy records without deleting old tables.
Run: python -m scripts.upgrade_current_schema
"""
from sqlalchemy import inspect, text
from app.core.database import Base, engine
import app.models  # register all tables


def main():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        enums = {e["name"]: e["labels"] for e in inspect(conn).get_enums()}
    # PostgreSQL requires enum additions committed before their first use.
    if "userrole" in enums:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for role in ("candidate", "admin"):
                conn.execute(text(f"ALTER TYPE userrole ADD VALUE IF NOT EXISTS '{role}'"))
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
        tables = set(inspect(conn).get_table_names())
        if "users" not in tables:
            print("Current schema ready; no legacy tables found.")
            return
        queries = [
            '''INSERT INTO "USER" (id, "Email", "FullName", "Phone", "HashedPassword", "Role", "IsActive", "IsVerified", "CreatedAt", "UpdatedAt")
               SELECT "Id", email, full_name, phone, hashed_password,
                 (CASE WHEN lower(role::text) IN ('admin','hr') THEN 'admin' ELSE 'candidate' END)::userrole,
                 is_active, is_verified, created_at, updated_at FROM users ON CONFLICT DO NOTHING''',
            '''INSERT INTO "PROFILE" (id, "UserId", "FileUrl", "FileType", "RawText", "CleanText", "CreatedAt")
               SELECT "Id", "UserId", "FileUrl",
                 (CASE WHEN lower("FileType"::text) = 'pdf' THEN 'pdf' ELSE 'other' END)::profilefiletype,
                 "RawText", "CleanText", "CreatedAt" FROM "CVs" ON CONFLICT DO NOTHING''',
            '''INSERT INTO "JD" (id, "Title", "RawText", "CleanText", "Responsibility", "Qualification", "Experience", "CreatedAt")
               SELECT "Id", "Title", "RequirementsText", "Description", "Description", "EducationLevel"::text,
                 COALESCE("MinExperience",0)::integer, "CreatedAt" FROM "Jobs" ON CONFLICT DO NOTHING''',
            '''INSERT INTO "PROFILE_SKILL" (id, "ProfileId", "SkillTitle")
               SELECT cs."Id", cs."CVId", s."Name" FROM "CVSkills" cs JOIN "Skills" s ON s."Id"=cs."SkillId"
               ON CONFLICT DO NOTHING''',
            '''INSERT INTO "JD_SKILL" (id, "JDId", "Title")
               SELECT js."Id", js."JobId", s."Name" FROM "JobSkills" js JOIN "Skills" s ON s."Id"=js."SkillId"
               ON CONFLICT DO NOTHING''',
        ]
        for query in queries:
            conn.execute(text(query))
        for table in Base.metadata.sorted_tables:
            conn.execute(text(f"""SELECT setval(pg_get_serial_sequence(:table_name, 'id'),
                COALESCE((SELECT max(id) FROM "{table.name}"), 1),
                EXISTS(SELECT 1 FROM "{table.name}"))"""), {"table_name": f'"{table.name}"'})
    print("Current schema ready; legacy tables preserved.")


if __name__ == "__main__":
    main()
