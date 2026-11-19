"""Xuất OpenAPI schema của app ra docs/openapi.json.

Chạy từ thư mục gốc: python -m scripts.export_openapi
"""
import json
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "openapi-export-not-for-production")

from app.main import app  # noqa: E402

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"


def main() -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return OUTPUT


if __name__ == "__main__":
    print(f"Wrote {main()}")
