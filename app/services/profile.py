import json
from pathlib import Path
from typing import Dict, List, cast
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.persist.postgres.profile import create_profile
from app.persist.postgres.profile_edu import create_profile_edu
from app.persist.postgres.profile_skill import create_profile_skills
from app.persist.postgres.profile_work_exp import create_profile_work_exp


def main(db: Session) -> Dict[str, int]:
    create_profile()
    create_profile_edu()
    create_profile_skills()
    create_profile_work_exp()


if __name__ == "__main__":
    with SessionLocal() as db:
        main(db)
