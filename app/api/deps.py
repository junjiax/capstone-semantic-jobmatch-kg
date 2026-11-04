from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.crud import user as user_crud
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Giải mã Bearer token từ header Authorization.
    Tìm và trả về User object tương ứng.

    Raise 401 nếu:
      - Token không hợp lệ / hết hạn
      - Token không phải loại "access"
      - Không tìm thấy user trong DB
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)

    # Kiểm tra token hợp lệ và đúng loại
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise credentials_exception

    try:
        user_id_int = int(user_id)
    except ValueError:
        raise credentials_exception

    # Tìm user trong DB
    user = user_crud.get_user_by_id(db, user_id_int)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Mở rộng get_current_user — thêm kiểm tra tài khoản active.
    Hầu hết endpoint dùng dependency này thay vì get_current_user.

    Raise 403 nếu tài khoản bị deactivate.
    """
    if not current_user.IsActive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )
    return current_user


# ════════════════════════════════════════════════════════
# ROLE-BASED DEPENDENCIES
# ════════════════════════════════════════════════════════


def require_applicant(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Chỉ cho phép Applicant truy cập endpoint.
    Dùng cho: nộp CV, theo dõi kết quả ứng tuyển...

    Raise 403 nếu role != APPLICANT.
    """
    if current_user.Role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ứng viên mới có quyền thực hiện hành động này.",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.Role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ADMIN mới được phép thực hiện hành động này.",
        )
    return current_user


def require_hr_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Cho phép vai trò quản trị hiện có truy cập endpoint HR/Admin."""
    if current_user.Role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền. Yêu cầu vai trò Admin.",
        )
    return current_user
