from typing import Optional
from sqlalchemy.orm import Session
from app.models.match_result import MatchResult


# ─── CREATE ──────────────────────────────────────────────────
def create_match_result(db: Session, **kwargs) -> MatchResult:
    match_result = MatchResult(**kwargs)
    db.add(match_result)
    db.commit()
    db.refresh(match_result)
    return match_result
