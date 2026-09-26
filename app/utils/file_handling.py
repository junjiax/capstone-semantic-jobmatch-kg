import re
import io
import os
import json
import shutil
from uuid import uuid4
from datetime import datetime

import pdfplumber
from fastapi import UploadFile
from google import genai
from app.core.config import get_settings

settings = get_settings()

client = genai.Client(api_key=settings.GEMINI_API_KEY)
ai_model = "gemini-2.5-flash"

def generate_unique_filename(user_id: int, original_filename: str) -> str:
    """Tạo tên file duy nhất: user_{id}_{timestamp}_{uuid}.ext"""
    file_ext = original_filename.split(".")[-1].lower()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = uuid4().hex[:8]
    return f"user_{user_id}_{timestamp}_{unique_id}.{file_ext}"


def save_file_to_disk(file: UploadFile, folder_path: str, filename: str) -> str:
    """Lưu file vật lý và trả về đường dẫn đầy đủ."""
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def check_file_extension(filename: str, allowed_extensions: list) -> bool:
    """Kiểm tra định dạng file có hợp lệ không."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def extract_text_from_pdf(file_path: str) -> str:
    """Đọc text từ file PDF đã lưu trên disk."""
    with pdfplumber.open(file_path) as pdf:
        text = "\n".join(
            page.extract_text() for page in pdf.pages if page.extract_text()
        )
    return text.replace("\x00", "")


def clean_text_with_gemini(raw_text: str) -> str:
    """
    Dùng Gemini để clean text CV:
    - Lowercase
    - Xóa thông tin nhạy cảm (email, phone)
    - Xóa ký tự đặc biệt
    - Remove stopwords
    - Lemmatization
    - Chuẩn hóa từ đồng nghĩa
    """
    prompt = f"""
    Nhiệm vụ của bạn là trích xuất các từ khóa chuyên môn cốt lõi từ CV dưới đây.

    QUY TẮC LỌC THÔNG TIN (CHỈ LẤY NHỮNG NỘI DUNG SAU):
    1. Kỹ năng kỹ thuật (Tech stack): Ngôn ngữ lập trình, framework, thư viện, database, công cụ (VD: React, Python, FastAPI, Docker, PostgreSQL...).
    2. Vị trí công việc (Role): Chức danh ứng viên đã làm (VD: Fullstack Developer, Intern, Backend Engineer...).
    3. Học vấn (Education): Bằng cấp, chuyên ngành (VD: Bachelor, Information System...).
    4. Thuật ngữ chuyên ngành (Domain Knowledge): Các khái niệm kỹ thuật (VD: REST API, Machine Learning, CI/CD, JWT...).

    NHỮNG THỨ PHẢI BỎ QUA HOÀN TOÀN:
    - Thông tin cá nhân (email, sđt, địa chỉ, ngày sinh, link github/linkedin).
    - Sở thích, hoạt động ngoại khóa, tình nguyện.
    - Kỹ năng mềm (giao tiếp, làm việc nhóm, lãnh đạo...).
    - Mục tiêu nghề nghiệp dài dòng, các từ nối tiếng Anh (and, the, a, with, to...).

    YÊU CẦU ĐẦU RA BẮT BUỘC:
    Chuyển tất cả từ khóa tìm được thành chữ thường (lowercase) và loại bỏ ký tự đặc biệt.
    Trả về DUY NHẤT một chuỗi văn bản (string) gồm các từ khóa này, phân cách nhau bằng một khoảng trắng (space).
    TUYỆT ĐỐI KHÔNG sinh ra code. KHÔNG giải thích. KHÔNG dùng định dạng markdown.

    CV Text:
    {raw_text}
    """

    print(f"AI MODEL KEY: {settings.GEMINI_API_KEY}")
    response = client.models.generate_content(
        model=ai_model, 
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini trả về response rỗng khi clean text.")

    return response.text.strip()


def parse_text_with_gemini(raw_text: str) -> dict:
    """Gửi raw text lên Gemini Flash, trả về dict có cấu trúc."""
    prompt = f"""
    Bạn là một chuyên gia bóc tách dữ liệu nhân sự. Hãy trích xuất thông tin từ CV dưới đây và trả về định dạng JSON chuẩn.

    QUY TẮC BÓC TÁCH NGHIÊM NGẶT:
    1. Lược bỏ trùng lặp (Deduplicate): Nếu một trường học hoặc kỹ năng xuất hiện nhiều lần trong CV, hãy gộp thông tin lại thành 1 bản ghi duy nhất, đầy đủ nhất.
    2. Xử lý Kinh nghiệm (Experience) & Dự án (Project): 
       - Nếu ứng viên có kinh nghiệm làm việc tại công ty, trích xuất bình thường.
       - Nếu ứng viên KHÔNG có kinh nghiệm công ty, nhưng có "Personal Projects", "Technical Projects", hoặc "Academic Projects" (Đồ án), HÃY XEM MỖI DỰ ÁN NÀY LÀ MỘT KINH NGHIỆM LÀM VIỆC và đưa vào mảng "experiences".
       - Khi đưa Dự án vào Kinh nghiệm: 
         + "CompanyName" = "Personal Project" hoặc "Academic Project".
         + "Position" = Vai trò trong dự án (VD: Fullstack Developer, Backend Engineer...).
         + "Description" = Tóm tắt ngắn gọn tính năng và công nghệ (Tech stack) sử dụng.
    3. Xử lý Ngày tháng: Chuyển đổi linh hoạt sang định dạng YYYY-MM-DD (Ví dụ: "Jan 2026" -> "2026-01-01", "Present" -> null).
    
    Cấu trúc JSON đầu ra bắt buộc:
    {{
        "position": "Tên vị trí ứng tuyển hoặc định hướng (ví dụ: Fullstack Developer Intern)",
        "educations": [
            {{
                "School": "Tên trường (ví dụ: Sai Gon University)",
                "Major": "Chuyên ngành",
                "Degree": "Bằng cấp (Bachelor, Master...)",
                "Level": "bachelor hoặc college hoặc master",
                "GraduationYear": 2026
            }}
        ],
        "skills": [
            {{
                "SkillName": "Tên kỹ năng cốt lõi (ví dụ: Python, React)",
                "Confidence": 0.8
            }}
        ],
        "experiences": [
            {{
                "CompanyName": "Tên công ty hoặc Personal Project",
                "Position": "Chức danh hoặc Vai trò trong dự án",
                "StartDate": "YYYY-MM-DD",
                "EndDate": "YYYY-MM-DD hoặc null",
                "Description": "Mô tả công việc hoặc công nghệ dự án"
            }}
        ],
        "summary": "Tóm tắt profile ứng viên trong 2-3 câu."
    }}

    YÊU CẦU ĐỊNH DẠNG ĐẦU RA (RẤT QUAN TRỌNG):
    - CHỈ trả về nguyên bản chuỗi JSON hợp lệ. 
    - TUYỆT ĐỐI KHÔNG bọc JSON trong các ký tự markdown như ```json hay ```.
    - KHÔNG giải thích, KHÔNG thêm bất kỳ văn bản nào khác ngoài JSON.

    CV Text:
    {raw_text}
    """
    response = client.models.generate_content(
        model=ai_model, 
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini trả về response rỗng khi parse CV.")

    # Extract JSON từ response
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    if not match:
        raise ValueError("Không tìm thấy JSON trong response của Gemini.")

    return json.loads(match.group(0).strip())


def parse_cv_file(file_path: str) -> dict:
    """
    Pipeline xử lý CV:
    1. Đọc text từ PDF
    2. Parse structured data bằng Gemini
    Trả về dict gồm parsed data + raw_text + clean_text
    """
    raw_text = extract_text_from_pdf(file_path)

    if not raw_text.strip():
        raise ValueError("Không thể đọc nội dung từ file PDF. File có thể là dạng scan/ảnh.")

    parsed = parse_text_with_gemini(raw_text)
    clean = clean_text_with_gemini(raw_text)

    return {
        "raw_text": raw_text,
        "clean_text": clean,
        "parsed": parsed
    }