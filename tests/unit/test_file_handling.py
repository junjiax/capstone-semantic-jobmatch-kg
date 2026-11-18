import re

import pytest

from app.utils.file_handling import check_file_extension, generate_unique_filename

pytestmark = pytest.mark.unit


def test_generate_unique_filename_format_and_uniqueness():
    name = generate_unique_filename(42, "My CV.PDF")
    assert re.fullmatch(r"user_42_\d{14}_[0-9a-f]{8}\.pdf", name)
    assert name != generate_unique_filename(42, "My CV.PDF")


def test_generate_unique_filename_uses_last_extension():
    assert generate_unique_filename(1, "a.b.docx").endswith(".docx")


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("cv.pdf", True),
        ("CV.PDF", True),
        ("cv.docx", True),
        ("archive.tar.txt", True),
        ("cv.exe", False),
        ("noextension", False),
        ("", False),
    ],
)
def test_check_file_extension(filename, expected):
    assert check_file_extension(filename, ["pdf", "docx", "txt"]) is expected
