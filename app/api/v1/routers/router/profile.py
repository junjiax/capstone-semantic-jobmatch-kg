import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_hr_or_admin
from app.api.v1.schemas.response import ResponseSchema
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.services import graph_service

logger = logging.getLogger(__name__)

router = APIRouter()


