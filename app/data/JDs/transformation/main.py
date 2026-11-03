import ast, json, re
from typing import List, Dict


def main() -> None:
    # READ RAW DATA FROM FILE
    print("[INFO] Starting transformation process...")

    count_of_raw_json_objs: int = 0  # Count of raw JSON objects read from file
    list_of_raw_json_objs: List[str] = (
        []
    )  # Convert each object to string representation

    count_of_cleaned_json_objs: int = 0  # Count of cleaned JSON objects
    list_of_cleaned_objs: List[Dict[str, object]] = (
        []
    )  # Store cleaned objects as dictionaries

    with open(
        "app/data/JDs/extraction/crawler/raw/crawled-2026-11-02-17-06-41.txt",
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            list_of_raw_json_objs.append(line.strip())

    for json_obj in list_of_raw_json_objs:
        count_of_raw_json_objs += 1
        json_obj = json.loads(json_obj)

        obj_raw_text: Dict[str, object] = {"jd_rawtext": f"{json_obj}"}
        obj_cleaned_text = clean_extract(obj_raw_text)

        cleaned_obj: Dict[str, object] = {
            "rawtext": obj_raw_text,
            "cleantext": obj_cleaned_text.get("Cleantext", ""),
            "job_title": obj_cleaned_text.get("Title", ""),
            "Job_skills": obj_cleaned_text.get("JobSkills", []),
            "Domain": obj_cleaned_text.get("Domain", ""),
            "Expertise": obj_cleaned_text.get("Expertise", ""),
            "Responsibilities": obj_cleaned_text.get("Responsibilities", ""),
            "Qualification": obj_cleaned_text.get("Qualification", 0),
        }

        list_of_cleaned_objs.append(cleaned_obj)

    for cleaned_obj in list_of_cleaned_objs:
        count_of_cleaned_json_objs += 1
        print(
            f"{'='*50}\n"
            f"[INFO] Cleaned text for object {count_of_cleaned_json_objs}\n{json.dumps(cleaned_obj, indent=4, ensure_ascii=False)}\n"
            f"{'='*50}\n"
        )


def clean_extract(obj_raw_text: Dict[str, object]) -> Dict[str, object]:
    """
    Extract unique value includes:
    Title: Chức danh công việc --> varchar
    JobSkills: Danh sách kỹ năng yêu cầu --> list[word:str]
    Domain: Lĩnh vực chuyên môn của công việc --> varchar
    Expertise: Lĩnh vực chuyên môn sâu hoặc năng lực chuyên biệt được yêu cầu --> varchar
    Qualification: Trình độ và điều kiện chuyên môn cần có --> varchar
    Responsibilities: Các trách nhiệm và nhiệm vụ của công việc --> varchar
    Experience: Số năm kinh nghiệm yêu cầu --> integer
    """

    raw_obj = obj_raw_text.get("jd_rawtext", {})

    if isinstance(raw_obj, str):
        raw_obj = ast.literal_eval(raw_obj)
    if not isinstance(raw_obj, dict):
        raise TypeError("'jd_rawtext' must contain a job description object")

    title: str = raw_obj.get("job_title", "")  # type: ignore
    requirements: str = raw_obj.get("requirements", "")  # type: ignore
    responsibilities: str = raw_obj.get("responsibilities", "")  # type: ignore
    raw_skills: List[object] = raw_obj.get("job_skills", [])  # type: ignore

    title: str = title if isinstance(title, str) else ""
    requirements: str = requirements if isinstance(requirements, str) else ""
    responsibilities: str = (
        responsibilities if isinstance(responsibilities, str) else ""
    )
    job_skills: List[str] = (
        [
            skill.strip()
            for skill in raw_skills  # type: ignore
            if isinstance(skill, str) and skill.strip()
        ]
        if isinstance(raw_skills, list)
        else []
    )

    searchable_text = f"{title}\n{requirements}\n{responsibilities}"
    domain_terms = (
        "Artificial Intelligence",
        "AI",
        "Cloud",
        "Data",
        "Cybersecurity",
        "Finance",
        "Healthcare",
        "E-commerce",
        "Education",
        "Telecommunications",
        "Manufacturing",
    )
    domains = [
        domain
        for domain in domain_terms
        if re.search(
            rf"(?<!\w){re.escape(domain)}(?!\w)", searchable_text, re.IGNORECASE
        )
    ]

    experience_matches = re.findall(
        r"(\d+)\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:relevant\s+)?experience|"
        r"(\d+)\s*\+?\s*năm\s*(?:kinh nghiệm)?",
        requirements,
        re.IGNORECASE,
    )
    experience_years = [
        int(years) for match in experience_matches for years in match if years
    ]

    return {
        "Cleantext": searchable_text,
        "Title": title,
        "JobSkills": job_skills,
        "Domain": ", ".join(domains),
        "Expertise": ", ".join(job_skills),
        "Qualification": requirements,
        "Responsibilities": responsibilities,
        "Experience": max(experience_years, default=0),
    }
