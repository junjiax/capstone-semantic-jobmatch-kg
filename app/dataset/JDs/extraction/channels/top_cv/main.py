import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

# ==========================================
# CRAWLING CONFIGURATION
# ==========================================
REQUEST_INTERVAL_MS = 2000
PAGE_LOAD_TIMEOUT_MS = 30_000
SELECTOR_TIMEOUT_MS = 15_000


def _wait_before_next_request(page: Page) -> None:
    """Wait before sending the next browser request."""
    print(f"[INFO] Waiting {REQUEST_INTERVAL_MS / 1000:.1f} seconds...")
    page.wait_for_timeout(REQUEST_INTERVAL_MS)


def _check_response(response: Any, url: str) -> bool:
    """
    Check HTTP response status.

    Returns:
        True: Request is successful.
        False: Request should not continue.
    """
    if response is None:
        return True

    status = response.status

    if status == 403:
        print(f"[WARNING] HTTP 403 Forbidden: {url}")
        print("[WARNING] Server refused access. " "Stopping crawler.")
        return False

    if status == 429:
        retry_after = response.headers.get("retry-after")

        print(f"[WARNING] HTTP 429 Too Many Requests: {url}")

        if retry_after:
            print(f"[INFO] Retry-After: {retry_after}")

        print("[WARNING] Rate limit reached. " "Stopping crawler.")
        return False

    if status >= 400:
        print(f"[ERROR] HTTP {status}: {url}")
        return False

    return True


# ==========================================
# MAIN CRAWLING FUNCTION
# ==========================================
def main(page: Page, output_path: Path, go_to: str) -> None:
    print("[INFO] Start scraping raw data from TopCV")

    # ==========================================
    # ACCESS LISTING PAGE AND EXTRACT JOB CARDS
    # ==========================================
    job_cards = _extract_first_page_job_cards(page, go_to)

    if not job_cards:
        raise RuntimeError(f"No TopCV job cards found at {go_to}")

    print(f"[INFO] Found {len(job_cards)} TopCV job cards")

    # ==========================================
    # CREATE OUTPUT DIRECTORY
    # ==========================================
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    saved_count = 0
    detail_page = page.context.new_page()

    try:
        with output_path.open(
            "a",
            encoding="utf-8",
        ) as output_file:

            # ==========================================
            # EXTRACT JOB DETAILS
            # ==========================================
            for index, job_card in enumerate(
                job_cards,
                start=1,
            ):
                try:
                    # Wait before accessing the next detail page.
                    if index > 1:
                        _wait_before_next_request(detail_page)

                    response = detail_page.goto(
                        job_card["job_url"],
                        wait_until="domcontentloaded",
                        timeout=PAGE_LOAD_TIMEOUT_MS,
                    )

                    # Check HTTP response.
                    if not _check_response(
                        response,
                        job_card["job_url"],
                    ):
                        if response is not None and response.status in (403, 429):
                            break

                        continue

                    # Wait for job detail content.
                    detail_page.wait_for_selector(
                        "h1.box-header-job__title",
                        timeout=SELECTOR_TIMEOUT_MS,
                    )

                    # Extract job information.
                    job = _extract_job_details(detail_page)

                    job["job_title"] = job["job_title"] or job_card["job_title"]

                    job["company"] = job["company"] or job_card["company"]

                    job["job_url"] = job_card["job_url"]
                    job["source"] = go_to
                    job["crawled_at"] = datetime.now().isoformat()

                    # Save job as JSONL.
                    json.dump(
                        job,
                        output_file,
                        ensure_ascii=False,
                    )

                    output_file.write("\n")
                    output_file.flush()

                    saved_count += 1

                    print(
                        f"[INFO] Saved job "
                        f"{index}/{len(job_cards)}: "
                        f"{job['job_title']}"
                    )

                except PlaywrightError as error:
                    print(f"[ERROR] Failed to crawl " f"{job_card['job_url']}: {error}")

    finally:
        detail_page.close()

    # ==========================================
    # CRAWLING SUMMARY
    # ==========================================
    if saved_count == len(job_cards):
        print(
            f"[SUCCESS] Saved {saved_count}/"
            f"{len(job_cards)} TopCV jobs "
            f"to {output_path}"
        )
    else:
        print(
            f"[WARNING] Saved only {saved_count}/"
            f"{len(job_cards)} TopCV jobs "
            f"to {output_path}"
        )


# ==========================================
# EXTRACT JOB CARDS FROM THE FIRST LISTING PAGE
# ==========================================
def _extract_first_page_job_cards(
    page: Page,
    go_to: str,
) -> list[dict[str, Any]]:
    current_url = page.url.split(
        "#",
        maxsplit=1,
    )[
        0
    ].rstrip("/")

    if current_url != go_to.rstrip("/"):
        response = page.goto(
            go_to,
            wait_until="domcontentloaded",
            timeout=PAGE_LOAD_TIMEOUT_MS,
        )

        if not _check_response(response, go_to):
            raise RuntimeError(f"Failed to load TopCV listing: {go_to}")

    print(f"[INFO] Accessed TopCV listing page: {go_to}")
    print(f"[INFO] Current page URL: {page.url}")

    page.wait_for_selector(
        ".job-item-search-result h3 " "a[href*='/viec-lam/']",
        timeout=SELECTOR_TIMEOUT_MS,
    )
    job_cards = _extract_job_cards(page)
    print(f"[INFO] Extracted {len(job_cards)} job cards from the first page")
    return job_cards


# ==========================================
# EXTRACT JOB CARDS
# ==========================================
def _extract_job_cards(
    page: Page,
) -> list[dict[str, Any]]:

    return page.locator(".job-item-search-result").evaluate_all(
        """cards => cards.map(card => {
            const titleLink = card.querySelector(
                "h3 a[href*='/viec-lam/']"
            );

            if (!titleLink) return null;

            const companyLink = card.querySelector(
                "a[href*='/cong-ty/']"
            );

            return {
                job_title: titleLink.innerText.trim(),
                job_url: titleLink.href,
                company: companyLink?.innerText.trim() ||
                    companyLink?.querySelector("img")?.alt.trim() || ""
            };
        }).filter(Boolean)"""
    )


# ==========================================
# EXTRACT JOB DETAILS
# ==========================================
def _extract_job_details(
    page: Page,
) -> dict[str, Any]:

    return page.locator("body").evaluate("""body => {
            const sectionText = title => {
                const heading = Array.from(
                    body.querySelectorAll("h2")
                ).find(
                    item =>
                        item.innerText.trim().toLowerCase()
                        === title.toLowerCase()
                );

                const section = heading?.closest(
                    ".box-job-information-detail-item"
                );

                if (!section) return "";

                return Array.from(section.children)
                    .filter(element =>
                        element !== heading.parentElement &&
                        !element.matches(
                            ".required-tags, .required-tag, " +
                            ".required-tag__content"
                        )
                    )
                    .map(element => element.innerText.trim())
                    .filter(Boolean)
                    .join("\\n");
            };

            const skillsSection = Array.from(
                body.querySelectorAll(
                    ".box-job-information-required-candidate " +
                    ".required-tag__content"
                )
            ).find(
                section =>
                    section.querySelector("h3")
                        ?.innerText.trim().toLowerCase()
                    === "kỹ năng cần có"
            );

            const skillsText = skillsSection
                ?.querySelector(
                    ".required-tag__content--desc"
                )?.innerText.trim() ?? "";

            const companyLink = Array.from(
                body.querySelectorAll(
                    ".box-header-job a[href*='/cong-ty/']"
                )
            ).find(
                link => link.innerText.trim()
            ) ?? body.querySelector(
                ".box-header-job a[href*='/cong-ty/']"
            );

            return {
                job_title: body.querySelector(
                    "h1.box-header-job__title"
                )?.innerText.trim() ?? "",

                company: companyLink?.innerText.trim() ||
                    companyLink?.querySelector("img")?.alt.trim() || "",

                job_skills: skillsText
                    ? skillsText.split(",")
                        .map(skill => skill.trim())
                        .filter(Boolean)
                    : [],

                requirements: [
                    sectionText("Job Details"),
                    sectionText("Candidate Requirements")
                ].filter(Boolean).join("\\n"),

                responsibilities: sectionText(
                    "Job Description"
                )
            };
        }""")
