import json
from pathlib import Path
from typing import Dict, List, cast
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.postgres.profile import create_profile, get_profiles
from app.repositories.postgres.profile_edu import create_profile_edu, get_profile_edu
from app.repositories.postgres.profile_skill import (
    create_profile_skills,
    get_profile_skills,
)
from app.repositories.postgres.profile_work_exp import (
    create_profile_work_exp,
    get_profile_work_exp,
)

def create_profile():
    pass

def get_profiles():
    pass

def get_profile_by_id():
    pass

def update_profile():
    pass

def main(db: Session) -> None:
    pass


if __name__ == "__main__":
    with SessionLocal() as db:
        main(db)
