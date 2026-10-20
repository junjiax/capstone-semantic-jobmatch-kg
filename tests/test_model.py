import pytest
from google import genai
from app.core.config import get_settings


def test_gemini_client_smoke():
    """Kiểm tra gọi Gemini API nếu có key cấu hình trong .env"""
    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        pytest.skip("GEMINI_API_KEY chưa được cấu hình, bỏ qua test external API.")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    models = list(client.models.list())
    assert len(models) > 0


if __name__ == "__main__":
    settings = get_settings()
    key = settings.GEMINI_API_KEY or ""
    if not key:
        print("GEMINI_API_KEY chưa được thiết lập trong .env")
    else:
        try:
            client = genai.Client(api_key=key)
            print("Các model hỗ trợ tạo nội dung:")
            for m in client.models.list():
                if "generateContent" in m.supported_actions:
                    print(f"- {m.name}")
        except Exception as e:
            print("Lỗi kết nối Gemini API:", e)