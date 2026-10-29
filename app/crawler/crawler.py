from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

"""
STEP 1. Crawl Facebook feeds from the following pages:
PAGE_URLS Depend on users' needs just by importing a text file which include facebook urls for each row.
"""
FILE_PATH = Path(f"app/crawler/configs/imported-urls.txt")
FILE_CONTENT = FILE_PATH.read_text(encoding="utf-8").splitlines()
print(FILE_CONTENT)

imported_urls: list[str] = []
for item in FILE_CONTENT:
    url = item.strip()
    if url:
        imported_urls.append(url)
        print(url)


OUTPUT_FILE = Path(
    f'app/crawler/raw/crawled-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.txt'
)

# SESSION_FILE = Path("../configs/auth/facebook_state.json")

SCROLL_COUNT = 5
SCROLL_DISTANCE = 1000
SCROLL_WAIT_MS = 3000
CLICK_WAIT_MS = 500
WAIT_FOR_TIME_OUT = 10000


def main() -> None:

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        # # ==========================================
        # # Browser context
        # # ==========================================

        # if SESSION_FILE.exists():

        #     print(f"[INFO] Using existing session: " f"{SESSION_FILE}")

        #     context = browser.new_context(
        #         storage_state=SESSION_FILE, viewport={"width": 1280, "height": 900}
        #     )

        # else:

        #     print("[INFO] No Facebook session found")

        context = browser.new_context(viewport={"width": 1280, "height": 900})

        page = context.new_page()

        # # ==========================================
        # # Login
        # # ==========================================

        # if not SESSION_FILE.exists():

        #     print("[INFO] Opening Facebook login...")

        #     page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

        #     page.wait_for_timeout(5000)

        #     print("[ACTION] Please login to Facebook " "manually in the browser.")

        #     input("[ACTION] After login, press ENTER here...")

        #     # Đảm bảo thư mục tồn tại
        #     SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

        #     context.storage_state(path=SESSION_FILE)

        #     print(f"[SUCCESS] Facebook session saved to:\n" f"{SESSION_FILE}")

        # # ==========================================
        # # Crawl từng Facebook page
        # # ==========================================

        for url in imported_urls:

            print()
            print("=" * 70)
            print(f"[INFO] Open: {url}")
            print("=" * 70)

            page.goto(url, wait_until="domcontentloaded")

            page.wait_for_timeout(WAIT_FOR_TIME_OUT)

            # close_button = page.locator('div[role="button"][aria-label="Close"]')

            # if close_button.count() > 0:
            #     print("[INFO] Found 'Close' button")
            #     button = close_button.first
            #     if button.is_visible():
            #         button.scroll_into_view_if_needed()
            #         button.evaluate("(element) => element.click()")
            #         page.wait_for_timeout(CLICK_WAIT_MS)
            #         print("[INFO] Closed popup")

            # # ======================================
            # # Scroll
            # # ======================================

            # for i in range(SCROLL_COUNT):

            #     print(f"[INFO] Scroll " f"{i + 1}/{SCROLL_COUNT}")

            #     page.mouse.wheel(0, SCROLL_DISTANCE)

            #     page.wait_for_timeout(SCROLL_WAIT_MS)

            # # ======================================
            # # Find post content
            # # ======================================

            # story_messages = page.locator('div[data-ad-rendering-role="story_message"]')

            # count = story_messages.count()

            # print(f"[INFO] Found " f"{count} story messages")

            # collected_posts = []

            # ======================================
            # Collect posts
            # ======================================

            # for i in range(count):

            #     try:

            #         element = story_messages.nth(i)

            #         # ==================================
            #         # Find "See more"
            #         # ==================================

            #         see_more = element.locator('div[role="button"]').filter(
            #             has_text="See more" or "Xem thêm"
            #         )

            #         if see_more.count() == 0:

            #             see_more = element.locator('div[role="button"]').filter(
            #                 has_text="Xem thêm" or "See more"
            #             )

            #         if see_more.count() > 0:

            #             print(f"[INFO] Post {i + 1}: " f"Found 'See more'")

            #             button = see_more.first

            #             if button.is_visible():

            #                 button.scroll_into_view_if_needed()

            #                 button.evaluate("(element) => element.click()")

            #                 page.wait_for_timeout(CLICK_WAIT_MS)

            #                 print(f"[INFO] Post {i + 1}: " f"Clicked 'See more'")

            #         else:

            #             print(f"[INFO] Post {i + 1}: " f"No 'See more'")

            #         # ==================================
            #         # Get text
            #         # ==================================

            #         text = element.evaluate("(element) => element.innerText")

            #         if not text.strip():
            #             continue

            #         collected_posts.append(text)

            #         print(f"[INFO] Collected " f"{i + 1}/{count}")

            #     except Exception as error:

            #         print(f"[ERROR] Post " f"{i + 1}: {error}")

            # # ======================================
            # # Save
            # # ======================================

            # OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            # OUTPUT_FILE.touch(exist_ok=True)

            # with open(OUTPUT_FILE, "a", encoding="utf-8") as file:

            #     file.write("\n")
            #     file.write("=" * 70 + "\n")

            #     file.write(f"SOURCE: {url}\n")

            #     file.write(f"CRAWLED_AT: " f"{datetime.now().isoformat()}\n")

            #     file.write(f"POST_COUNT: " f"{len(collected_posts)}\n")

            #     file.write("=" * 70 + "\n")

            #     for index, text in enumerate(collected_posts, start=1):

            #         file.write("\n")
            #         file.write(f"POST {index}\n")
            #         file.write("-" * 50 + "\n")

            #         file.write(text)

            #         file.write("\n")

            # print(f"[SUCCESS] Saved " f"{len(collected_posts)} posts")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()

# import asyncio
# from playwright.async_api import async_playwright

# crawling_url_careerviet = "https://careerviet.vn"
# crawling_url_linkedin = (
#     "https://www.linkedin.com/login/?trk=guest_homepage-basic_nav-header-signin"
# )
# crawling_url_facebook = "https://www.facebook.com"


# async def crawling():
#     async with async_playwright() as playwright:
#         browser = await playwright.chromium.launch(
#             channel="chrome",
#             headless=False,
#         )
#         try:
#             page = await browser.new_page()
#             await page.goto(
#                 crawling_url_careerviet,
#                 wait_until="domcontentloaded",
#             )
#             await page.wait_for_timeout(60000)
#         finally:
#             await browser.close()


# if __name__ == "__main__":
#     asyncio.run(crawling())
