from typing import Optional

from pydantic import BaseModel, Field


class LinkedInJob(BaseModel):
    job_id: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    url: str
    posted_at: Optional[str] = None
    description: Optional[str] = None


class LinkedInJobSearchResult(BaseModel):
    keywords: str
    location: Optional[str] = None
    total_results: int
    results: list[LinkedInJob] = Field(default_factory=list)
