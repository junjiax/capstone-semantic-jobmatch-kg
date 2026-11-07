import ast, json, re
import errno
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def main() -> Dict[str, object]:
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
        "app/dataset/JDs/extraction/crawler/raw/crawled-2026-11-02-17-06-41.txt",
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
            "RawText": obj_raw_text,
            "Cleantext": obj_cleaned_text.get("Cleantext", ""),
            "Title": obj_cleaned_text.get("Title", ""),
            "JobSkills": obj_cleaned_text.get("JobSkills", []),
            "Domain": obj_cleaned_text.get("Domain", ""),
            "Expertise": obj_cleaned_text.get("Expertise", ""),
            "Responsibilities": obj_cleaned_text.get("Responsibilities", ""),
            "Qualification": obj_cleaned_text.get("Qualification", ""),
            "Experience": obj_cleaned_text.get("Experience", 0),
        }

        list_of_cleaned_objs.append(cleaned_obj)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = write_cleaned_jds(
        Path("app/dataset/JDs/transformation/saving"),
        list_of_cleaned_objs,
        timestamp,
    )
    count_of_cleaned_json_objs = len(list_of_cleaned_objs)

    print(
        json.dumps(
            list_of_cleaned_objs,
            indent=2,
            ensure_ascii=False,
        )
    )
    print(f"[INFO] Wrote {count_of_cleaned_json_objs} cleaned objects to {output_path}")

    return {
        "count_of_raw_json_objs": count_of_raw_json_objs,
        "count_of_cleaned_json_objs": count_of_cleaned_json_objs,
        "list_of_cleaned_objs": json.dumps(list_of_cleaned_objs, ensure_ascii=False),
        "output_path": str(output_path),
    }


def write_cleaned_jds(
    output_dir: Path,
    cleaned_jds: List[Dict[str, object]],
    timestamp: str,
) -> Path:
    output_path = output_dir / f"processed-{timestamp}.txt"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as file:
            for cleaned_jd in cleaned_jds:
                file.write(json.dumps(cleaned_jd, ensure_ascii=False) + "\n")
        return output_path
    except OSError as exc:
        if exc.errno not in (errno.EROFS, errno.EACCES, errno.EPERM):
            raise

    fallback_dir = (
        Path(tempfile.gettempdir())
        / "capstone-semantic-jobmatch-kg"
        / "processed-jds"
    )
    fallback_dir.mkdir(parents=True, exist_ok=True)
    fallback_path = fallback_dir / output_path.name
    with fallback_path.open("w", encoding="utf-8") as file:
        for cleaned_jd in cleaned_jds:
            file.write(json.dumps(cleaned_jd, ensure_ascii=False) + "\n")
    print(
        f"[WARN] Output directory is not writable; saved JD data to {fallback_path}"
    )
    return fallback_path


_NOUN_PHRASE_CUES = re.compile(
    r"(?:"
    r"(?:experience|knowledge|understanding|proficiency|skills?|expertise|degrees?|"
    r"certifications?)\s+(?:in|with|of|on)|"
    r"(?:kinh nghiệm|kiến thức|sự am hiểu|am hiểu|thành thạo|kỹ năng|chuyên môn|"
    r"chuyên ngành|tốt nghiệp)\s+(?:(?:về|với|trong|ngành|ở)\s+)?"
    r")(.+)",
    re.IGNORECASE,
)
_VERB_PHRASE_STARTERS = (
    "chịu trách nhiệm",
    "phát triển",
    "xây dựng",
    "thiết kế",
    "triển khai",
    "quản lý",
    "vận hành",
    "giám sát",
    "hỗ trợ",
    "phối hợp",
    "phân tích",
    "tối ưu",
    "đảm bảo",
    "thực hiện",
    "tư vấn",
    "kiểm thử",
    "bảo trì",
    "làm việc",
    "develop",
    "build",
    "design",
    "implement",
    "manage",
    "operate",
    "maintain",
    "monitor",
    "support",
    "coordinate",
    "analyze",
    "analyse",
    "optimize",
    "optimise",
    "ensure",
    "perform",
    "lead",
    "create",
    "deliver",
    "architect",
    "consult",
    "test",
    "troubleshoot",
)
_DOMAIN_TERMS = (
    "Artificial Intelligence",
    "trí tuệ nhân tạo",
    "AI",
    "Cloud",
    "điện toán đám mây",
    "Data",
    "dữ liệu",
    "Cybersecurity",
    "an ninh mạng",
    "Finance",
    "tài chính",
    "Healthcare",
    "y tế",
    "E-commerce",
    "thương mại điện tử",
    "Education",
    "giáo dục",
    "Telecommunications",
    "viễn thông",
    "Manufacturing",
    "sản xuất",
)


def _append_unique(phrases: List[str], phrase: str) -> None:
    phrase = phrase.strip(" \t\r\n,;:-")
    if phrase and phrase.casefold() not in {item.casefold() for item in phrases}:
        phrases.append(phrase)


def _extract_noun_phrases(text: str) -> List[str]:
    phrases: List[str] = []
    for line in re.split(r"[\n.;!?]+", text):
        for match in _NOUN_PHRASE_CUES.finditer(line):
            for candidate in re.split(r"\s+(?:and|or|và|hoặc)\s+|[,;]", match.group(1)):
                _append_unique(phrases, candidate)
    return phrases


def _extract_verb_phrases(text: str) -> List[str]:
    phrases: List[str] = []
    starter_pattern = re.compile(
        r"(?<!\w)("
        + "|".join(re.escape(starter) for starter in _VERB_PHRASE_STARTERS)
        + r")(?!\w)",
        re.IGNORECASE,
    )
    for clause in re.split(r"[\n.;!?]+", text):
        match = starter_pattern.search(clause)
        if match:
            _append_unique(phrases, clause[match.start() :])
    return phrases


def _extract_domain_terms(text: str) -> List[str]:
    phrases: List[str] = []
    for term in _DOMAIN_TERMS:
        match = re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text, re.IGNORECASE)
        if match:
            _append_unique(phrases, text[match.start() : match.end()])
    return phrases


def clean_extract(obj_raw_text: Dict[str, object]) -> Dict[str, object]:
    """
    Extract original noun/verb phrases from each JD section without paraphrasing.
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

    qualification_phrases = _extract_noun_phrases(requirements) + _extract_verb_phrases(
        requirements
    )
    responsibility_phrases = _extract_noun_phrases(
        responsibilities
    ) + _extract_verb_phrases(responsibilities)
    clean_phrases: List[str] = []
    for phrase in [title, *job_skills, *qualification_phrases, *responsibility_phrases]:
        _append_unique(clean_phrases, phrase)

    raw_source = "\n".join((title, requirements, responsibilities, *job_skills))

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
        "Cleantext": " ".join(clean_phrases),
        "Title": title,
        "JobSkills": job_skills,
        "Domain": ", ".join(_extract_domain_terms(raw_source)),
        "Expertise": ", ".join(job_skills),
        "Qualification": " ".join(qualification_phrases),
        "Responsibilities": " ".join(responsibility_phrases),
        "Experience": max(experience_years, default=0),
    }


if __name__ == "__main__":
    main()
