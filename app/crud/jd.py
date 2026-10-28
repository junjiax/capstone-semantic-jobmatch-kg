from typing import Any, Optional, List
from sqlalchemy.orm import Session
from app.models.jd import JD
from app.models.enum import JobStatus


# ─── READ ────────────────────────────────────────────────────
def get_jds(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    title: Optional[str] = None,
    requirement: Optional[str] = None,
    status: Optional[JobStatus] = None,
) -> List[JD]:
    query = db.query(JD)
    return query.offset(skip).limit(limit).all()


def get_jd_by_id(db: Session, jd_id: int) -> List[JD]:
    """Tìm jd theo primary key. Trả None nếu không tồn tại."""
    return db.query(JD).filter(JD.Id == jd_id).all()


# ─── CREATE ──────────────────────────────────────────────────
def create_jd(db: Session, **kwargs: Any) -> JD:
    jd = JD(**kwargs)
    db.add(jd)
    db.commit()
    db.refresh(jd)
    return jd


# ─── UPDATE ──────────────────────────────────────────────────
def update_jd(db: Session, jd: JD, **kwargs: Any) -> JD:
    for field, value in kwargs.items():
        setattr(jd, field, value)
    db.commit()
    db.refresh(jd)
    return jd
