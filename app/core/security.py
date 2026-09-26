import hashlib
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
from jose import JWTError, jwt

from app.core.config import get_settings
from app.core import TokenType

settings = get_settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_SECONDS = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_TOKEN_EXPIRE_SECONDS = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
RESET_TOKEN_EXPIRE_SECONDS = 15 * 60 


def hash_password(password: str) -> str:
    """Sử dụng cơ chế hash 2 lớp: SHA256 -> Bcrypt để tương thích file mới."""
    prepared_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(prepared_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Tên hàm giữ nguyên để các file Service/Login không bị lỗi."""
    try:
        prepared_password = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return bcrypt.checkpw(
            prepared_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

# --- CORE TOKEN LOGIC ---

def _create_token_base(subject: Any, expires_delta: int, token_type: str, extra: dict = {}) -> str:
    """Hàm nội bộ tạo JWT với cấu trúc thống nhất."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(seconds=expires_delta)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": token_type,
        **extra,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# --- 3 HÀM TẠO TOKEN (Giữ nguyên tên, tham số nhận thêm 'role') ---

def create_access_token(user_id: int, email: str, role: str) -> str:
    """Đã đổi roleId thành role trong payload."""
    return _create_token_base(
        subject=user_id,
        expires_delta=ACCESS_TOKEN_EXPIRE_SECONDS,
        token_type=TokenType.ACCESS,
        extra={"email": email, "role": role},
    )

def create_refresh_token(user_id: int) -> str:
    return _create_token_base(
        subject=user_id,
        expires_delta=REFRESH_TOKEN_EXPIRE_SECONDS,
        token_type=TokenType.REFRESH,
    )

def create_reset_token(email: str) -> str:
    return _create_token_base(
        subject=email,
        expires_delta=RESET_TOKEN_EXPIRE_SECONDS,
        token_type=TokenType.RESET,
    )

# --- DECODE/VERIFY  ---

def decode_token(token: str, expected_type: Optional[str] = None) -> Optional[dict]:
    """Hàm giải mã token chính yếu."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None

def verify_token(token: str, expected_type: str = TokenType.ACCESS) -> Optional[dict]:
    """Alias của decode_token để tránh lỗi ở các file gọi tên hàm này."""
    return decode_token(token, expected_type)