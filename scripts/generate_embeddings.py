import sys
import os
import time

# Đảm bảo đường dẫn import thư mục gốc dự án
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.profile_skill import ProfileSkill
from app.models.jd_skill import JDSkill
from app.models.jd import JD
from app.clients.sentence_transformer import get_sentence_transformer
from app.services.text_embedding import build_skill_text, normalize_text


def backfill_profile_skills(db, batch_size: int = 32) -> int:
    """Tạo vector cho các kỹ năng ứng viên còn thiếu."""
    client = get_sentence_transformer()
    records = db.query(ProfileSkill).filter(ProfileSkill.Vector.is_(None)).all()
    total = len(records)
    print(f"\n[PROFILE_SKILL] Tìm thấy {total} bản ghi cần tạo vector.")
    
    if total == 0:
        return 0

    updated = 0
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        texts = [build_skill_text(item.SkillTitle) for item in chunk]
        vectors = client.encode_batch(texts, batch_size=batch_size, normalize=True)
        
        for item, vec in zip(chunk, vectors):
            item.Vector = vec
            updated += 1
            
        db.commit()
        print(f" -> Đã cập nhật: {updated}/{total} Profile Skills")
        
    return updated


def backfill_jd_skills(db, batch_size: int = 32) -> int:
    """Tạo vector cho các kỹ năng yêu cầu của JD còn thiếu."""
    client = get_sentence_transformer()
    records = db.query(JDSkill).filter(JDSkill.Vector.is_(None)).all()
    total = len(records)
    print(f"\n[JD_SKILL] Tìm thấy {total} bản ghi cần tạo vector.")
    
    if total == 0:
        return 0

    updated = 0
    for i in range(0, total, batch_size):
        chunk = records[i:i + batch_size]
        texts = [build_skill_text(item.Title) for item in chunk]
        vectors = client.encode_batch(texts, batch_size=batch_size, normalize=True)
        
        for item, vec in zip(chunk, vectors):
            item.Vector = vec
            updated += 1
            
        db.commit()
        print(f" -> Đã cập nhật: {updated}/{total} JD Skills")
        
    return updated


def backfill_jd_requirements(db, batch_size: int = 16) -> int:
    """Tạo vector cho các trường thông tin trong tin tuyển dụng (JD)."""
    client = get_sentence_transformer()
    records = db.query(JD).filter(JD.VectorResponsibility.is_(None)).all()
    total = len(records)
    print(f"\n[JD] Tìm thấy {total} vị trí việc làm cần cập nhật vector trách nhiệm/yêu cầu.")
    
    if total == 0:
        return 0

    updated = 0
    for jd in records:
        # 1. Vector Title
        if jd.Title:
            jd.VectorTitle = client.encode(normalize_text(jd.Title), normalize=True)
        # 2. Vector Domain
        if jd.Domain:
            jd.VectorDomain = client.encode(normalize_text(jd.Domain), normalize=True)
        # 3. Vector Expertise
        if jd.Expertise:
            jd.VectorExpertise = client.encode(normalize_text(jd.Expertise), normalize=True)
        # 4. Vector Qualification
        if jd.Qualification:
            jd.VectorQualification = client.encode(normalize_text(jd.Qualification), normalize=True)
        # 5. Vector Responsibility
        if jd.Responsibility:
            jd.VectorResponsibility = client.encode(normalize_text(jd.Responsibility), normalize=True)

        updated += 1
        if updated % batch_size == 0:
            db.commit()
            print(f" -> Đã cập nhật: {updated}/{total} JDs")

    db.commit()
    return updated


def main():
    print("=" * 60)
    print("BẮT ĐẦU QUY TRÌNH NẠP EMBEDDING")
    print("=" * 60)
    start_time = time.time()
    
    with SessionLocal() as db:
        ps_count = backfill_profile_skills(db)
        js_count = backfill_jd_skills(db)
        jd_count = backfill_jd_requirements(db)
        
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"HOÀN THÀNH TỔNG CỘNG trong {elapsed:.2f} giây:")
    print(f" - PROFILE_SKILL cập nhật : {ps_count}")
    print(f" - JD_SKILL cập nhật      : {js_count}")
    print(f" - JD tin tuyển dụng      : {jd_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()