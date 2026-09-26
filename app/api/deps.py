from app.core.database import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.crud import user as user_crud
from app.models.User import User, UserRole


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

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exception

    # Tìm user trong DB
    user = user_crud.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Mở rộng get_current_user — thêm kiểm tra tài khoản active.
    Hầu hết endpoint dùng dependency này thay vì get_current_user.

    Raise 400 nếu tài khoản bị deactivate.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản đã bị vô hiệu hóa.",
        )
    return current_user




# ════════════════════════════════════════════════════════
# ROLE-BASED DEPENDENCIES
# ════════════════════════════════════════════════════════



def require_hr(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Chỉ cho phép HR truy cập endpoint.
    Dùng cho: quản lý users, xem danh sách CV, phân tích...

    Raise 403 nếu role != HR.
    """
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện hành động này. Yêu cầu vai trò HR.",
        )
    return current_user


def require_applicant(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Chỉ cho phép Applicant truy cập endpoint.
    Dùng cho: nộp CV, theo dõi kết quả ứng tuyển...

    Raise 403 nếu role != APPLICANT.
    """
    if current_user.role != UserRole.APPLICANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ứng viên mới có quyền thực hiện hành động này.",
        )
    return current_user




def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ ADMIN mới được phép thực hiện hành động này."
        )
    return current_user

def require_hr_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    HR hoặc ADMIN — dùng cho các endpoint quản lý users.
    ADMIN làm được mọi thứ HR làm + có thêm quyền riêng.

    Dùng cho: xem danh sách users, khóa tài khoản, xóa user.
    """
    if current_user.role not in (UserRole.HR, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền. Yêu cầu vai trò HR hoặc Admin.",
        )
    return current_user