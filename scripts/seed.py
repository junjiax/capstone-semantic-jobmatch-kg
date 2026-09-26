"""
Fix seed.py — vấn đề là Python enum gửi "ADMIN" (chữ HOA)
nhưng PostgreSQL enum lưu "admin" (chữ thường).

NGUYÊN NHÂN:
  Python Enum mặc định dùng .name (HOA) khi truyền vào SQLAlchemy
  nhưng PostgreSQL enum type lưu chữ thường theo giá trị .value

CÁCH FIX:
  1. Chạy SQL trong pgAdmin để thêm 'admin' vào enum DB
  2. Chạy file này thay cho seed.py cũ

CHẠY: python fix_seed.py
"""

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models.User import User

# from app.models.cv_embedding import CVEmbedding
# from app.models.job import Job, JobEmbedding
# from app.services.embbeding_service import model_service

# ── Import trực tiếp string value thay vì dùng Enum object ──
# Thay vì: UserRole.ADMIN  (gửi "ADMIN" → lỗi)
# Dùng  : "admin"          (gửi "admin" → đúng)
SEED_USERS = [
    {
        "email": "admin@cvsystem.com",
        "full_name": "System Admin",
        "phone": "0900000000",
        "hashed_password": hash_password("Admin@123456"),
        "role": "admin",  # ← chữ thường
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "hr1@cvsystem.com",
        "full_name": "HR Manager 1",
        "phone": "0901111111",
        "hashed_password": hash_password("Hr@123456"),
        "role": "hr",  # ← chữ thường
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "hr2@cvsystem.com",
        "full_name": "HR Manager 2",
        "phone": "0902222222",
        "hashed_password": hash_password("Hr@123456"),
        "role": "hr",
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "applicant1@gmail.com",
        "full_name": "Nguyen Van An",
        "phone": "0911111111",
        "hashed_password": hash_password("App@123456"),
        "role": "applicant",  # ← chữ thường
        "is_active": True,
        "is_verified": True,
    },
    {
        "email": "applicant2@gmail.com",
        "full_name": "Tran Thi Binh",
        "phone": "0922222222",
        "hashed_password": hash_password("App@123456"),
        "role": "applicant",
        "is_active": True,
        "is_verified": False,
    },
    {
        "email": "applicant3@gmail.com",
        "full_name": "Le Van Cuong",
        "phone": "0933333333",
        "hashed_password": hash_password("App@123456"),
        "role": "applicant",
        "is_active": False,
        "is_verified": True,
    },
]


def seed_user():
    print("Tao bang DB...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    created = 0

    try:
        for data in SEED_USERS:
            exists = db.query(User).filter(User.email == data["email"]).first()
            if exists:
                print(f"   Da ton tai: {data['email']}")
                continue
            db.add(User(**data))
            created += 1

        db.commit()
        print(f"\nSeed xong! Da tao {created} user(s).\n")
        print("  ADMIN      : admin@cvsystem.com   / Admin@123456")
        print("  HR         : hr1@cvsystem.com     / Hr@123456")
        print("  HR         : hr2@cvsystem.com     / Hr@123456")
        print("  APPLICANT  : applicant1@gmail.com / App@123456")
        print("  APPLICANT  : applicant2@gmail.com / App@123456")
        print("  APPLICANT  : applicant3@gmail.com / App@123456 (bi khoa)\n")

    except Exception as e:
        db.rollback()
        print(f"Loi: {e}")
    finally:
        db.close()


def seed_jobs(db, csv_path="../fake_job_postings.csv"):
    import csv
    from app.models.job import Job
    from app.models.enum import JobStatus, EducationLevel

    # Mapping cột CSV (0-indexed) sang thuộc tính Job:
    #   cột 2  (index 1)  → Title
    #   cột 7  (index 6)  → Description
    #   cột 8  (index 7)  → RequirementsText
    #   cột 14 (index 13) → MinExperience  ← tạm để trống (dữ liệu đang là text)
    #   cột 15 (index 14) → (chưa dùng, placeholder)
    COL_TITLE = 1
    COL_DESC = 6
    COL_REQUIREMENTS = 7
    COL_MIN_EXP = 13  # TODO: đổi kiểu dữ liệu trước khi dùng
    COL_EXTRA = 14

    jobs = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)  # bỏ dòng header

        for row in reader:
            if len(row) <= COL_EXTRA:
                continue  # bỏ qua dòng thiếu cột

            job = Job(
                Title=row[COL_TITLE].strip() or None,
                Description=row[COL_DESC].strip() or None,
                RequirementsText=row[COL_REQUIREMENTS].strip() or None,
                MinExperience=None,  # TODO: cột 14 đang là text, chưa map
                EducationLevel=list(EducationLevel)[0],  # placeholder
                Status=list(JobStatus)[0],  # placeholder
            )
            jobs.append(job)

    db.add_all(jobs)
    db.commit()

    print(f"✅ Seeded {len(jobs)} jobs")


def seed_job_embeddings():
    try:
        db = SessionLocal()

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Loi: {e}")
    finally:
        db.close()


def seed_cv_embeddings():
    try:
        db = SessionLocal()

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Loi: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_user()
    # seed_job_embeddings()
    db = SessionLocal()
    seed_jobs(db)
