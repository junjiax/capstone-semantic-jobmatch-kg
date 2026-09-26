from sqlalchemy.orm import Session
from app.models.cv_embedding import CVEmbedding
from app.models.job_embedding import JobEmbedding


def save_cv_embedding(db: Session, cv_embedding: dict):
    cv_embedding = CVEmbedding(**cv_embedding)
    db.add(cv_embedding)
    db.commit()
    db.refresh(cv_embedding)
    return cv_embedding


def save_job_embedding(db: Session, job_embedding: dict):
    job_embedding = JobEmbedding(**job_embedding)
    db.add(job_embedding)
    db.commit()
    db.refresh(job_embedding)
    return job_embedding
