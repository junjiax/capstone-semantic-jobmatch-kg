import hashlib
from typing import Optional


def normalize_text(value: Optional[str]) -> str:
    """Loại bỏ khoảng trắng thừa, chuẩn hóa về chuỗi một dòng."""
    return " ".join((value or "").split()).strip()

def build_skill_text(title: str, category: Optional[str] = None) -> str:
    """
    Xây dựng chuỗi văn bản đại diện cho một kỹ năng.
    Ví dụ: 'FastAPI' hoặc 'FastAPI - Backend Framework'
    """
    clean_title = normalize_text(title)
    if category:
        return f"{clean_title} - {normalize_text(category)}"
    return clean_title

def build_job_text(job) -> str:
    """
    Xây dựng chuỗi văn bản tổng hợp cho tin tuyển dụng (JD) từ các trường thông tin chính.
    """
    fields = [
        getattr(job, "Title", None),
        getattr(job, "Domain", None),
        getattr(job, "Expertise", None),
        getattr(job, "Qualification", None),
        getattr(job, "Responsibility", None),
    ]
    return normalize_text(" | ".join(normalize_text(f) for f in fields if f))

def build_requirement_text(job) -> str:
    """
    Xây dựng chuỗi biểu diễn riêng cho phần trách nhiệm và yêu cầu năng lực công việc.
    """
    fields = [
        getattr(job, "Responsibility", None),
        getattr(job, "Qualification", None),
        getattr(job, "Expertise", None),
    ]
    return normalize_text(" \n ".join(normalize_text(f) for f in fields if f))


def compute_content_hash(text: str, model_name: str) -> str:
    """
    Tạo mã băm SHA-256 từ nội dung văn bản kết hợp tên mô hình.
    Dùng để kiểm tra dữ liệu có thay đổi hay không trước khi tính lại vector.
    """
    payload = f"{model_name}:{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def text_hash(text: str, model_name: str) -> str:
    raw = f"{model_name}:{text}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()