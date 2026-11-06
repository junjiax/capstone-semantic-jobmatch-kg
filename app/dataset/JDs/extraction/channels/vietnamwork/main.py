import json
from datetime import datetime
from pathlib import Path
from typing import Any
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

REQUEST_INTERVAL_MS = 2000


def main(page: Page, output_path: Path, go_to: str) -> None:
    print("[INFO] Start scraping raw data from CareerViet")

    # ==========================================
    # ACCESS THE CAREERVIET LISTING PAGE AND EXTRACT JOB CARDS
    # ==========================================
    job_cards = _extract_all_job_cards(page, go_to)

    if not job_cards:
        raise RuntimeError(f"No CareerViet job cards found at {go_to}")

    print(f"[INFO] Found {len(job_cards)} CareerViet job cards")

    # ==========================================
    # CREATE OUTPUT DIRECTORY IF IT DOES NOT EXIST
    # ==========================================
    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_count = 0
    detail_page = page.context.new_page()

    # ==========================================
    # SAVE JOB DETAILS TO OUTPUT FILE
    # ==========================================
    try:
        with output_path.open("a", encoding="utf-8") as output_file:
            for index, job_card in enumerate(job_cards, start=1):
                try:
                    if index > 1:
                        page.wait_for_timeout(REQUEST_INTERVAL_MS)

                    response = detail_page.goto(
                        job_card["job_url"], wait_until="domcontentloaded"
                    )
                    if response is not None and response.status in {403, 429}:
                        raise RuntimeError(
                            "CareerViet refused further requests "
                            f"(HTTP {response.status}); stopping the crawl."
                        )

                    if response is not None and response.status >= 400:
                        print(
                            f"[ERROR] Job {index}/{len(job_cards)} returned "
                            f"HTTP {response.status}: {job_card['job_url']}"
                        )
                        continue

                    detail_page.wait_for_selector(".job-detail-content h2.detail-title")
                    job = _extract_job_details(detail_page)
                    job["job_title"] = job["job_title"] or job_card["job_title"]
                    job["company"] = job["company"] or job_card["company"]
                    job["job_url"] = job_card["job_url"]
                    job["source"] = go_to
                    job["crawled_at"] = datetime.now().isoformat()

                    json.dump(job, output_file, ensure_ascii=False)
                    output_file.write("\n")
                    output_file.flush()
                    saved_count += 1
                    print(
                        f"[INFO] Saved job {index}/{len(job_cards)}: "
                        f"{job['job_title']}"
                    )
                except PlaywrightError as error:
                    print(f"[ERROR] Failed to crawl {job_card['job_url']}: {error}")
    finally:
        detail_page.close()

    if saved_count == len(job_cards):
        print(
            f"[SUCCESS] Saved {saved_count}/{len(job_cards)} CareerViet jobs "
            f"to {output_path}"
        )
    else:
        print(
            f"[WARNING] Saved only {saved_count}/{len(job_cards)} CareerViet jobs "
            f"to {output_path}"
        )


def _extract_all_job_cards(page: Page, url: str) -> list[dict[str, Any]]:
    response = page.goto(url, wait_until="domcontentloaded")

    if response is not None and response.status >= 400:
        raise RuntimeError(f"Failed to load CareerViet listing: HTTP {response.status}")

    job_cards: list[dict[str, Any]] = []
    seen_job_ids: set[str] = set()
    visited_pages: set[str] = set()

    while page.url not in visited_pages:
        visited_pages.add(page.url)
        page.wait_for_selector(".job-item h2 a.job_link")

        for job_card in _extract_job_cards(page):
            job_id = str(job_card["job_id"])
            if job_id not in seen_job_ids:
                seen_job_ids.add(job_id)
                job_cards.append(job_card)
                # time.sleep(1)  # Add a small delay to avoid overwhelming the server

        # next_page = page.locator(".pagination li.next-page:not(.disabled) a").first
        # if next_page.count() == 0:
        #     break

        # current_url = page.url
        # next_page.evaluate("(element) => element.click()")
        # page.wait_for_function(
        #     "previousUrl => window.location.href !== previousUrl",
        #     arg=current_url,
        # )

    return job_cards


def _extract_job_cards(page: Page) -> list[dict[str, Any]]:
    return page.locator(".job-item").evaluate_all("""cards => cards.map(card => {
            const titleLink = card.querySelector("h2 a.job_link");
            if (!titleLink) return null;

            return {
                job_id: titleLink.dataset.id || titleLink.href,
                job_title: titleLink.innerText.trim(),
                job_url: titleLink.href,
                company: card.querySelector("a.company-name")?.innerText.trim() ?? ""
            };
        }).filter(Boolean)""")


def _extract_job_details(page: Page) -> dict[str, Any]:
    return page.locator("body").evaluate("""body => {
            const normalize = value => value.normalize("NFD")
                .replace(/[\\u0300-\\u036f]/g, "")
                .toLowerCase()
                .trim();
            const detailContent = body.querySelector(".job-detail-content");
            const sectionText = headingText => {
                const row = Array.from(
                    detailContent?.querySelectorAll(".detail-row") ?? []
                ).find(item =>
                    normalize(item.querySelector(".detail-title")?.innerText ?? "") ===
                        normalize(headingText)
                );
                if (!row) return "";

                const title = row.querySelector(".detail-title");
                return Array.from(row.children)
                    .filter(child => child !== title)
                    .map(child => child.innerText.trim())
                    .filter(Boolean)
                    .join("\\n");
            };
            const companyLink = Array.from(
                body.querySelectorAll(".job-desc a[href*='/nha-tuyen-dung/']")
            ).find(link => link.innerText.trim());

            return {
                job_title: body.querySelector(".job-desc h1.title")
                    ?.innerText.trim() ?? "",
                company: companyLink?.innerText.trim() ?? "",
                job_skills: Array.from(
                    detailContent?.querySelectorAll(".job-tags a") ?? []
                ).map(link => link.innerText.trim()).filter(Boolean),
                requirements: sectionText("YÊU CẦU CÔNG VIỆC"),
                responsibilities: sectionText("MÔ TẢ CÔNG VIỆC")
            };
        }""")
