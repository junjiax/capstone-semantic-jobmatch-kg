from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.job import Job
from app.models.enum import JobStatus, EducationLevel as EducationLevelEnum


def seed_jobs(db: Session):
    from decimal import Decimal

    jobs_data = [
        {
            "Title": "Marketing Intern",
            "Description": "We are looking for a Marketing Intern to support our marketing team...",
            "RequirementsText": "Strong communication skills. Basic knowledge of marketing principles...",
            "MinExperience": Decimal("0.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Customer Service Representative",
            "Description": "Handle customer inquiries via phone and email...",
            "RequirementsText": "Excellent communication skills. Ability to handle complaints...",
            "MinExperience": Decimal("1.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Software Engineer",
            "Description": "Develop and maintain software applications...",
            "RequirementsText": "Experience with Python or Java. Understanding of OOP...",
            "MinExperience": Decimal("2.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Data Analyst",
            "Description": "Analyze datasets to provide business insights...",
            "RequirementsText": "Knowledge of SQL, Excel, and data visualization...",
            "MinExperience": Decimal("1.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Project Manager",
            "Description": "Manage project timelines and deliverables...",
            "RequirementsText": "Strong leadership and communication skills...",
            "MinExperience": Decimal("4.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Graphic Designer",
            "Description": "Design marketing materials and social media assets...",
            "RequirementsText": "Proficiency in Photoshop, Illustrator...",
            "MinExperience": Decimal("2.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "HR Specialist",
            "Description": "Handle recruitment and employee relations...",
            "RequirementsText": "Understanding of HR processes...",
            "MinExperience": Decimal("2.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Sales Executive",
            "Description": "Drive sales and manage client relationships...",
            "RequirementsText": "Strong negotiation skills...",
            "MinExperience": Decimal("2.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "DevOps Engineer",
            "Description": "Maintain CI/CD pipelines and cloud infrastructure...",
            "RequirementsText": "Experience with Docker, Kubernetes...",
            "MinExperience": Decimal("4.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
        {
            "Title": "Business Analyst",
            "Description": "Analyze business processes and suggest improvements...",
            "RequirementsText": "Strong analytical and documentation skills...",
            "MinExperience": Decimal("2.0"),
            "EducationLevel": EducationLevelEnum.BACHELOR,
            "Status": JobStatus.OPEN,
        },
    ]

    print("Đang bắt đầu seed dữ liệu Job...")
    for job_item in jobs_data:
        existing_job = db.query(Job).filter(Job.Title == job_item["Title"]).first()
        if not existing_job:
            new_job = Job(**job_item)
            db.add(new_job)
            print(f" - Đã thêm: {job_item['Title']}")
        else:
            print(f" - Đã tồn tại: {job_item['Title']} (Bỏ qua)")

    db.commit()
    print("--- Seed dữ liệu Job hoàn tất! ---")


# --- PHẦN QUAN TRỌNG ĐỂ CHẠY ĐƯỢC PYTHON -M ---
if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_jobs(db)
    finally:
        db.close()
