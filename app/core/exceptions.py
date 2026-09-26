from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.api.v1.schemas.response import ResponseSchema
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Lấy thông báo lỗi đầu tiên hoặc nối tất cả lại thành một chuỗi
    error_messages = []
    for error in exc.errors():
        location = " -> ".join([str(loc) for loc in error["loc"]])
        msg = error["msg"]
        error_messages.append(f"{location}: {msg}")
    
    full_message = " | ".join(error_messages)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ResponseSchema(
            data=None,
            message=f"Invalid data: {full_message}",
            meta={"errors": exc.errors()} # Trả về chi tiết lỗi trong meta để FE dễ debug
        ).model_dump()
    )

async def value_error_handler(request: Request, exc: ValueError):
    """
    Xử lý tập trung cho lỗi ValueError.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ResponseSchema(
            data=None,
            message=str(exc),
            meta=None
        ).model_dump()
    )

async def global_exception_handler(request: Request, exc: Exception):
    """
    Xử lý cho tất cả các lỗi hệ thống chưa được định nghĩa khác (Lỗi 500).
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ResponseSchema(
            data=None,
            message="Server encountered an unexpected error. Please try again later.",
            meta=None
        ).model_dump()
    )