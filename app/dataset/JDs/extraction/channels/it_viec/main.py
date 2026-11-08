import json
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page

REQUEST_INTERVAL_MS = 2000


def main(page: Page, output_path: Path, go_to: str) -> None:
    print("[INFO] Start scraping raw data from itviec.com")

    if page.url.split("?", maxsplit=1)[0].rstrip("/") != go_to:
        page.goto(go_to, wait_until="domcontentloaded")

    page.wait_for_selector(".job-card h3 a[href*='/it-jobs/']")
    job_cards = _extract_job_cards(page)
    print(f"[INFO] Found {len(job_cards)} ITviec job cards")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_count = 0

    with output_path.open("a", encoding="utf-8") as output_file:
        for index, job_card in enumerate(job_cards, start=1):
            detail_page = page.context.new_page()
            try:
                if index > 1:
                    page.wait_for_timeout(REQUEST_INTERVAL_MS)

                response = detail_page.goto(
                    job_card["job_url"], wait_until="domcontentloaded"
                )
                if response is not None and response.status >= 400:
                    print(
                        f"[ERROR] Job {index}/{len(job_cards)} returned "
                        f"HTTP {response.status}: {job_card['job_url']}"
                    )
                    continue

                detail_page.wait_for_selector("main h1")
                job = _extract_job_details(detail_page)
                job["job_title"] = job["job_title"] or job_card["job_title"]
                job["company"] = job["company"] or job_card["company"]
                job["job_skills"] = job["job_skills"] or job_card["job_skills"]
                job["job_url"] = job_card["job_url"]
                job["source"] = go_to
                job["crawled_at"] = datetime.now().isoformat()

                json.dump(job, output_file, ensure_ascii=False)
                output_file.write("\n")
                output_file.flush()
                saved_count += 1
                print(f"[INFO] Saved job {index}/{len(job_cards)}: {job['job_title']}")
            except PlaywrightError as error:
                print(f"[ERROR] Failed to crawl {job_card['job_url']}: {error}")
            finally:
                detail_page.close()

    print(
        f"[SUCCESS] Saved {saved_count}/{len(job_cards)} ITviec jobs to {output_path}"
    )


def _extract_job_cards(page: Page) -> list[dict[str, Any]]:
    return page.locator(".job-card").evaluate_all("""cards => cards.map(card => {
            const titleLink = card.querySelector("h3 a[href*='/it-jobs/']");
            if (!titleLink) return null;

            const companyLink = Array.from(
                card.querySelectorAll("a[href*='/companies/']")
            ).find(link => link.innerText.trim());

            return {
                job_title: titleLink.innerText.trim(),
                job_url: titleLink.href,
                company: companyLink?.innerText.trim() ?? "",
                job_skills: Array.from(
                    card.querySelectorAll("a[href*='click_source=Skill']")
                ).map(link => link.innerText.trim()).filter(Boolean)
            };
        }).filter(Boolean)""")


def _extract_job_details(page: Page) -> dict[str, Any]:
    return page.locator("main").evaluate("""main => {
            const skillsLabel = Array.from(main.querySelectorAll("div")).find(
                element => !element.children.length && element.innerText.trim() === "Skills:"
            );
            const skillsRow = skillsLabel?.parentElement;
            const sectionText = title => {
                const heading = Array.from(main.querySelectorAll("h2")).find(
                    item => item.innerText.trim().toLowerCase() === title.toLowerCase()
                );
                if (!heading?.parentElement) return "";

                return Array.from(heading.parentElement.children)
                    .filter(element => element !== heading)
                    .map(element => element.innerText.trim())
                    .filter(Boolean)
                    .join("\\n");
            };

            return {
                job_title: main.querySelector("h1")?.innerText.trim() ?? "",
                company: main.querySelector(".employer-name")?.innerText.trim() ?? "",
                job_skills: Array.from(
                    skillsRow?.querySelectorAll("a[href*='click_source=Skill']") ?? []
                ).map(link => link.innerText.trim()).filter(Boolean),
                requirements: sectionText("Your skills and experience"),
                responsibilities: sectionText("Job description")
            };
        }""")
