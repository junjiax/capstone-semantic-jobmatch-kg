from datetime import datetime
from pathlib import Path
from typing import List
import pdfplumber

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR.parent / "uploads" / "raw-resumes"
OUTPUT_DIR = SCRIPT_DIR / "crawler" / "raw"


def main() -> None:

    pdf_files = sorted(
        (
            path
            for path in SOURCE_DIR.iterdir()
            if path.is_file() and path.suffix.casefold() == ".pdf"
        ),
        key=lambda path: path.name.casefold(),
    )
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {SOURCE_DIR}")

    print(f"There are {len(pdf_files)} pdf files detected in {SOURCE_DIR} ")

    extracted_documents: List[str] = []
    errors: List[str] = []

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            print(text)
        except Exception as exc:
            errors.append(f"{pdf_path.name}: {exc}")
            continue

        if not text.strip():
            errors.append(f"{pdf_path.name}: no extractable text found")
            continue

        extracted_documents.append(f"===== {pdf_path.name} =====\n{text}")

    if errors:
        details = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(
            f"Extraction failed for {len(errors)} of {len(pdf_files)} PDF files:\n{details}"
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = OUTPUT_DIR / f"crawled-{timestamp}.txt"
    output_path.write_text("\n\n".join(extracted_documents), encoding="utf-8")

    print(f"Extracted {len(pdf_files)} PDF files to {output_path}")


if __name__ == "__main__":
    main()
