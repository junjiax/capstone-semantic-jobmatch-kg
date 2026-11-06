from pathlib import Path

import pdfplumber

"""
STEP 1. Crawl data from the following pages:
"""
# DEFINE FILE PATH FOR IMPORTED URLS
FILE_PATH_IMPORTED_URLs = Path(
    # f"app/data/CVs/uploads/CVs_pdf/INFORMATION-TECHNOLOGY/10089434.pdf"
    f"app/data/CVs/uploads/raw-resumes/0aa2fb6f-66d3-4fcc-b960-2bd2f7721ffe.pdf"
)

# DEFINE OUTPUT FILE PATH FOR SAVING RAW DATA
# FILE_PATH_OUT_SAVING_RAW_DATA = Path(
#     f'app/data/JDs/extraction/crawler/raw/crawled-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.txt'
# )


def main() -> None:
    with pdfplumber.open(FILE_PATH_IMPORTED_URLs) as pdf:
        file_content = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not file_content.strip():
        raise ValueError("No extractable text found in PDF.")

    for item in file_content.splitlines():
        print(item)


if __name__ == "__main__":
    main()
