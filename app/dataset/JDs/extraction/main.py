from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright
from .channels import it_viec_main, career_viet_main

"""
STEP 1. Crawl data from the following pages:
"""
# DEFINE FILE PATH FOR IMPORTED URLS
SOURCE_DIR_IMPORTED_URLs = Path(f"app/dataset/JDs/extraction/configs/imported-urls.txt")

# DEFINE VARIABLE FOR READING URLS FROM FILE
BROWSER_URLs_IMPORTED = SOURCE_DIR_IMPORTED_URLs.read_text(encoding="utf-8").splitlines()

# DEFINE OUTPUT FILE PATH FOR SAVING RAW DATA
OUTPUT_DIR_RAW_JD_CONTENT = Path(
    f'app/dataset/JDs/extraction/crawler/raw/crawled-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.txt'
)

# DEFINE LIST FOR STORING IMPORTED URLS
imported_urls: list[str] = []

# READ URLS FROM FILE AND STORE THEM IN THE LIST
for item in BROWSER_URLs_IMPORTED:
    url = item.strip()
    if url:
        imported_urls.append(url)


# DEFINE FUNCTION FOR CRAWLING DATA FROM EACH CHANNEL
def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # ==========================================
        # Access each URL from the imported list of URLs
        # ==========================================
        for url in imported_urls:
            print("=" * 70)
            print(f"[INFO] Open: {url}")
            print("=" * 70)

            match url:
                case _ if url.startswith("https://itviec.com"):
                    url = "https://itviec.com/it-jobs"
                    print("[INFO] Itviec page detected")
                    it_viec_main(page, OUTPUT_DIR_RAW_JD_CONTENT, url)
                case _ if url.startswith("https://careerviet.vn"):
                    url = "https://careerviet.vn/viec-lam/cntt-phan-cung-mang-cntt-phan-mem-c63,1-vi.html"
                    print("[INFO] CareerViet page detected")
                    career_viet_main(page, OUTPUT_DIR_RAW_JD_CONTENT, url)
                # case _ if url.startswith("https://www.topcv.vn"):
                #     url = "https://www.topcv.vn/tim-viec-lam-cong-nghe-thong-tin"
                #     print("[INFO] TopCV page detected")
                #     top_cv_main(page, FILE_PATH_OUT_SAVING_RAW_DATA, url)
                case _:
                    print(f"[WARNING] No matching channel for URL: {url}")

        page.close()
        context.close()
        browser.close()


if __name__ == "__main__":
    main()
