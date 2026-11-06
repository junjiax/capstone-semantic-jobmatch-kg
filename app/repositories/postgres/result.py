from sqlalchemy.orm import Session
from app.models.result import Result


# ─── CREATE ──────────────────────────────────────────────────
def create_result(db: Session, **kwargs: Result) -> Result:
    result = Result(**kwargs)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result
