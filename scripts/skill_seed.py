from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.skill import Skill

def seed_skills(db: Session):
    skills_data = [
        # --- FRONTEND ---
        {"Name": "React", "Category": "Frontend", "Description": "Thư viện JavaScript để xây dựng giao diện người dùng."},
        {"Name": "Next.js", "Category": "Frontend", "Description": "Framework React hỗ trợ SSR và Static Site Generation."},
        {"Name": "TypeScript", "Category": "Frontend", "Description": "JavaScript có kiểu dữ liệu mạnh (Strongly Typed)."},
        {"Name": "Tailwind CSS", "Category": "Frontend", "Description": "Utility-first CSS framework để thiết kế giao diện nhanh."},
        
        # --- BACKEND ---
        {"Name": "Python", "Category": "Backend", "Description": "Ngôn ngữ lập trình đa mục tiêu, phổ biến trong AI và Web."},
        {"Name": "FastAPI", "Category": "Backend", "Description": "Framework Python hiện đại, hiệu năng cao để xây dựng API."},
        {"Name": "PostgreSQL", "Category": "Backend", "Description": "Hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở mạnh mẽ."},
        {"Name": "Node.js", "Category": "Backend", "Description": "Môi trường thực thi JavaScript phía server."},
        {"Name": "Java", "Category": "Backend", "Description": "Ngôn ngữ lập trình hướng đối tượng phổ biến cho hệ thống lớn."},
        
        # --- TESTING ---
        {"Name": "Pytest", "Category": "Testing", "Description": "Framework kiểm thử mạnh mẽ cho ngôn ngữ Python."},
        {"Name": "Selenium", "Category": "Testing", "Description": "Công cụ tự động hóa trình duyệt để kiểm thử UI."},
        {"Name": "Jest", "Category": "Testing", "Description": "Framework kiểm thử JavaScript tập trung vào sự đơn giản."},
        
        # --- CI/CD & DEVOPS ---
        {"Name": "Docker", "Category": "CI/CD", "Description": "Nền tảng để đóng gói, triển khai và chạy ứng dụng trong container."},
        {"Name": "GitHub Actions", "Category": "CI/CD", "Description": "Công cụ tự động hóa quy trình CI/CD tích hợp sẵn trên GitHub."},
        {"Name": "Kubernetes", "Category": "CI/CD", "Description": "Hệ thống điều phối container để quản lý ứng dụng quy mô lớn."}
    ]

    print("Đang bắt đầu seed dữ liệu Skills...")
    for item in skills_data:
        # Kiểm tra trùng lặp theo Name (vì Name là Unique)
        existing_skill = db.query(Skill).filter(Skill.Name == item["Name"]).first()
        if not existing_skill:
            new_skill = Skill(**item)
            db.add(new_skill)
            print(f" - Đã thêm kỹ năng: {item['Name']}")
        else:
            # Cập nhật thông tin nếu kỹ năng đã tồn tại (Tùy chọn)
            existing_skill.Category = item["Category"]
            existing_skill.Description = item["Description"]
            print(f" - Đã cập nhật: {item['Name']}")
    
    db.commit()
    print("--- Seed dữ liệu Skills hoàn tất! ---")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_skills(db)
    finally:
        db.close()