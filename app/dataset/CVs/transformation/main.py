import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, TypedDict

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = (
    SCRIPT_DIR.parent
    / "extraction"
    / "crawler"
    / "raw"
    / "crawled-2026-11-06-11-51-49.txt"
)
OUTPUT_DIR = SCRIPT_DIR / "saving"
PROFILE_HEADER = re.compile(r"^===== (?P<filename>.+?\.pdf) =====$", re.IGNORECASE)
SECTION_HEADINGS = {
    "education",
    "academic background",
    "experience",
    "work experience",
    "working experience",
    "professional experience",
    "employment history",
    "skills",
    "technical skills",
    "professional skills",
    "personal skills",
    "key skills",
    "core skills",
    "competencies",
    "projects",
    "certifications",
    "certificates",
    "summary",
    "profile",
    "career goals",
    "references",
    "responsibility",
    "responsibilities",
    "main responsibilities",
    "key responsibilities",
    "domain",
    "domains",
    "industry",
    "industries",
    "expertise",
    "front end stack",
    "back end stack",
    "development operations",
    "languages",
}
SECTION_ALIASES = {
    "academic background": "education",
    "work experience": "experience",
    "working experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "technical skills": "skills",
    "professional skills": "skills",
    "personal skills": "skills",
    "key skills": "skills",
    "core skills": "skills",
    "competencies": "skills",
    "responsibility": "responsibilities",
    "main responsibilities": "responsibilities",
    "key responsibilities": "responsibilities",
    "domain": "domains",
    "industry": "domains",
    "industries": "domains",
    "front end stack": "skills",
    "back end stack": "skills",
    "development operations": "skills",
    "languages": "skills",
}
VERB_PHRASE_STARTERS = (
    "responsible for",
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
    "developing",
    "building",
    "designing",
    "implementing",
    "managing",
    "maintaining",
    "phát triển",
    "xây dựng",
    "thiết kế",
    "triển khai",
    "quản lý",
    "vận hành",
    "hỗ trợ",
    "phân tích",
    "tối ưu",
)


class CVProfile(TypedDict):
    rawtext: str
    cleantext: str
    file_url: str
    file_type: str
    title: str
    skilltitle: List[str]
    degree: str
    major: str
    school: str
    level: str
    graduation_year: int | None
    GPA: float | None
    domain: List[str]
    expertise: List[str]
    responsibility: str
    start_date: date | None
    end_date: date | None


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned_characters: list[str] = []

    for character in normalized:
        category = unicodedata.category(character)
        if character == "\n" or category in {"Zl", "Zp"}:
            cleaned_characters.append("\n")
        elif character == "\t" or category == "Zs":
            cleaned_characters.append(" ")
        elif category[0] not in {"C", "S"}:
            cleaned_characters.append(character)

    lines = [
        re.sub(r" +", " ", line).strip()
        for line in "".join(cleaned_characters).split("\n")
    ]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def chunk_text(text: str, max_chunk_length: int = 400) -> List[str]:
    normalized_text = clean_text(text)
    chunks: list[str] = []
    for line in normalized_text.splitlines():
        line = line.strip()
        if not line:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", line)
        for sentence in sentences:
            sentence = sentence.strip()
            while len(sentence) > max_chunk_length:
                split_at = sentence.rfind(" ", 0, max_chunk_length + 1)
                if split_at <= 0:
                    split_at = max_chunk_length
                chunks.append(sentence[:split_at].strip())
                sentence = sentence[split_at:].strip()
            if sentence:
                chunks.append(sentence)
    return chunks


def parse_profiles(raw_text: str) -> List[Dict[str, str]]:
    profiles: list[dict[str, str]] = []
    filename: str | None = None
    content_lines: list[str] = []

    def add_profile() -> None:
        if filename is None:
            return
        text = clean_text("\n".join(content_lines))
        if not text:
            raise ValueError(f"No text found for profile {filename!r}")
        profiles.append({"filename": clean_text(filename), "text": text})

    for line in raw_text.splitlines():
        header = PROFILE_HEADER.fullmatch(line.strip())
        if header is not None:
            add_profile()
            filename = header.group("filename")
            content_lines = []
        elif filename is not None:
            content_lines.append(line)
        elif line.strip():
            raise ValueError("Found text before the first PDF profile header")

    add_profile()
    if not profiles:
        raise ValueError("No PDF profile headers found in the source file")
    return profiles


def _section_text(text: str, heading_names: set[str]) -> str:
    wanted = {SECTION_ALIASES.get(name, name) for name in heading_names}
    active_section = ""
    section_lines: list[str] = []
    for line in text.splitlines():
        heading, remainder = _get_heading(line)
        if heading:
            active_section = heading
            if active_section in wanted and remainder:
                section_lines.append(remainder)
            continue
        if active_section in wanted and line.strip():
            section_lines.append(line.strip())
    return "\n".join(section_lines).strip()


def _get_heading(line: str) -> tuple[str, str]:
    normalized = re.sub(r"[^a-z ]", " ", line.casefold())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized.endswith(" skills") and normalized != "skills":
        return "skills", ""
    for heading in sorted(SECTION_HEADINGS, key=len, reverse=True):
        if normalized == heading:
            return SECTION_ALIASES.get(heading, heading), ""
        if normalized.startswith(heading + " "):
            remainder = line.strip()[len(heading) :].lstrip(" :-")
            return SECTION_ALIASES.get(heading, heading), remainder
    return "", ""


def _label_value(text: str, labels: str) -> str:
    match = re.search(
        rf"(?im)^\s*[-•*]?\s*(?:{labels})\s*[:\-]\s*(.+?)\s*$",
        text,
    )
    return match.group(1).strip() if match else ""


def _split_phrases(text: str) -> List[str]:
    phrases: list[str] = []
    for phrase in re.split(r"[,;|\n]+|\s+(?:and|or|và|hoặc)\s+", text):
        phrase = phrase.strip(" \t\r\n,;:-")
        if phrase and phrase.casefold() not in {item.casefold() for item in phrases}:
            phrases.append(phrase)
    return phrases


def _extract_cued_phrases(text: str, cues: str) -> List[str]:
    matches = re.finditer(
        rf"(?i)(?:{cues})\s+(?:in|with|of|on|for|as|about|về|với|trong|ngành)?\s*"
        r"([^.;!\n]+)",
        text,
    )
    return [
        phrase
        for match in matches
        for phrase in _split_phrases(match.group(1))
    ]


def _extract_skill_phrases(text: str) -> List[str]:
    skills: list[str] = []
    sentence_starters = (
        "a ",
        "an ",
        "and ",
        "as ",
        "because ",
        "build ",
        "building ",
        "even ",
        "develop ",
        "developing ",
        "design ",
        "designing ",
        "for ",
        "i ",
        "if ",
        "in ",
        "it ",
        "manage ",
        "managing ",
        "my ",
        "responsible ",
        "support ",
        "supporting ",
        "to ",
        "we ",
        "you ",
    )
    for line in text.splitlines():
        cleaned_line = line.strip(" \t-•*:")
        if not cleaned_line or cleaned_line.casefold().rstrip(":") in {
            "basic knowledge",
            "front end stack",
            "back end stack",
            "development operations",
            "languages",
            "skills",
        }:
            continue
        if (
            len(cleaned_line.split()) > 5
            or re.search(r"[.!?]", cleaned_line)
            or cleaned_line.casefold().startswith(sentence_starters)
            or re.search(
                r"\b(?:university|college|institute|limited liability|"
                r"company|group|telecom|developer|engineer|manager|tester|"
                r"consultant|certificate|diploma)\b",
                cleaned_line,
                re.IGNORECASE,
            )
            or re.search(r"\b(?:such as|including|for example)$", cleaned_line, re.I)
            or re.search(r"\b(?:19|20)\d{2}\b", cleaned_line)
        ):
            continue
        skills.extend(_split_phrases(cleaned_line))
    return _unique_phrases(skills)


def _unique_phrases(phrases: List[str]) -> List[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        normalized = clean_text(phrase).strip(" \t\r\n,;:-")
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            unique.append(normalized)
    return unique


def _extract_domain_phrases(text: str) -> List[str]:
    labeled_values = _label_value(text, r"domains?|industr(?:y|ies)")
    if not labeled_values:
        labeled_values = _section_text(text, {"domains", "industry", "industries"})
    return _unique_phrases(_split_phrases(labeled_values))


def _extract_expertise_phrases(text: str) -> List[str]:
    labeled_values = _label_value(text, r"expertise|speciali[sz]ations?")
    if not labeled_values:
        labeled_values = _section_text(text, {"expertise"})
    phrases = _split_phrases(labeled_values)
    phrases.extend(
        _extract_cued_phrases(
            text,
            r"(?:expertise|experience|experienced|proficient|proficiency|"
            r"speciali[sz]e|speciali[sz]ed)\s+(?:in|with|of|on)",
        )
    )
    return _unique_phrases(
        [
            phrase
            for phrase in phrases
            if len(phrase.split()) <= 10
            and not phrase.casefold().startswith(("i ", "my ", "we ", "to "))
        ]
    )


def _extract_responsibility_phrases(text: str) -> str:
    labeled = _label_value(text, r"responsibilit(?:y|ies)")
    candidates = [labeled] if labeled else []
    starter_pattern = re.compile(
        r"(?<!\w)(?:" + "|".join(re.escape(item) for item in VERB_PHRASE_STARTERS) + r")(?!\w)",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        line = line.strip(" \t-•*")
        match = starter_pattern.search(line)
        if match:
            candidates.append(line[match.start() :])
    return " ".join(_unique_phrases(candidates))


def _json_default(value: Any) -> str:
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _extract_dates(text: str) -> tuple[date | None, date | None]:
    normalized = re.sub(r"/\s*/", "/", text)
    date_pattern = re.compile(
        r"\b(?:"
        r"(?P<numeric>(?:0?[1-9]|1[0-2])\s*/\s*(?:(?:0?[1-9]|[12]\d|3[01])\s*/\s*)?(?:19|20)\d{2})"
        r"|(?P<month>(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|"
        r"May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+(?:19|20)\d{2})"
        r")\b",
        re.IGNORECASE,
    )
    dates: list[date] = []
    for match in date_pattern.finditer(normalized):
        value = re.sub(r"\s+", "", match.group("numeric") or match.group("month"))
        for date_format in ("%m/%d/%Y", "%m/%Y", "%b%Y", "%B%Y"):
            try:
                dates.append(datetime.strptime(value, date_format).date())
                break
            except ValueError:
                continue

    if not dates:
        return None, None
    start_date = min(dates)
    end_date = None if re.search(r"\bpresent\b", text, re.IGNORECASE) else max(dates)
    return start_date, end_date


def _build_profile(filename: str, text: str) -> CVProfile:
    chunks = chunk_text(text)
    cleantext = "\n".join(chunks)
    education = _section_text(cleantext, {"education", "academic background"})
    experience = _section_text(cleantext, {"experience", "work experience"})
    skills_section = _section_text(cleantext, {"skills"})

    degree = _label_value(education, "degree")
    if not degree:
        degree_match = re.search(
            r"(?im)^.*\b(?:ph\.?d\.?|doctorate|master(?:'s)?|bachelor(?:'s)?|"
            r"diploma|associate(?:'s)?|high school)\b.*$",
            education,
        )
        degree = degree_match.group(0).strip() if degree_match else ""

    major = _label_value(education, "major|field of study")
    if not major:
        major_match = re.search(
            r"(?im)^\s*[-•*]?\s*(?:major|field of study)\s*[:\-]\s*(.+?)\s*$",
            education,
        )
        major = major_match.group(1).strip() if major_match else ""
    school = _label_value(education, "school|university|college")
    if not school:
        school_match = re.search(
            r"(?im)^.*\b(?:university|college|institute|school)\b.*$",
            education,
        )
        school = school_match.group(0).strip() if school_match else ""

    graduation_match = re.search(
        r"(?i)\bgraduat(?:ion|ed)\b[^\d]{0,40}((?:19|20)\d{2})",
        education,
    )
    gpa_match = re.search(
        r"(?i)\bGPA\b\s*[:=]?\s*([0-4](?:\.\d{1,2})?)",
        education,
    )
    skill_values = _label_value(cleantext, "skills?|technical skills")
    skill_source = "\n".join(value for value in (skill_values, skills_section) if value)
    skills = _extract_skill_phrases(skill_source)
    if not skills:
        skills = _unique_phrases(
            _extract_cued_phrases(cleantext, r"(?:skills?|technologies|tools)")
        )
    start_date, end_date = _extract_dates(experience)

    title = ""
    for line in text.splitlines()[1:6]:
        candidate = line.strip()
        if (
            candidate
            and candidate.casefold().rstrip(":") not in SECTION_HEADINGS
            and not re.search(r"[@\d]", candidate)
        ):
            title = candidate
            break

    degree_lower = degree.casefold()
    if "phd" in degree_lower or "ph.d" in degree_lower or "doctorate" in degree_lower:
        level = "phd"
    elif "master" in degree_lower:
        level = "master"
    elif "bachelor" in degree_lower:
        level = "bachelor"
    elif "high school" in degree_lower:
        level = "high_school"
    elif degree:
        level = "diploma"
    else:
        level = ""

    domain = _extract_domain_phrases(cleantext)
    expertise = _extract_expertise_phrases(cleantext)
    responsibility_text = _section_text(
        cleantext, {"experience", "responsibilities"}
    )
    responsibility = _extract_responsibility_phrases(responsibility_text)

    return {
        "rawtext": text,
        "cleantext": cleantext,
        "file_url": (
            Path("app") / "data" / "CVs" / "uploads" / "raw-resumes" / filename
        ).as_posix(),
        "file_type": Path(filename).suffix.lstrip(".").casefold(),
        "title": title,
        "skilltitle": skills,
        "degree": degree,
        "major": major,
        "school": school,
        "level": level,
        "graduation_year": int(graduation_match.group(1)) if graduation_match else None,
        "GPA": float(gpa_match.group(1)) if gpa_match else None,
        "domain": domain,
        "expertise": expertise,
        "responsibility": responsibility,
        "start_date": start_date,
        "end_date": end_date,
    }


def transform_file(
    source_file: Path, output_dir: Path, timestamp: str | None = None
) -> List[CVProfile]:
    raw_text = source_file.read_text(encoding="utf-8", errors="replace")
    profiles = [
        _build_profile(profile["filename"], profile["text"])
        for profile in parse_profiles(raw_text)
    ]

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    output_path = output_dir / f"processed-{timestamp}.txt"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            profiles,
            ensure_ascii=False,
            indent=2,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Transformed {len(profiles)} profiles to {output_path}")
    return profiles


def main() -> None:
    transform_file(SOURCE_FILE, OUTPUT_DIR)


if __name__ == "__main__":
    main()
