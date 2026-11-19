"""Corpus and label loaders for the evaluation scripts.

Pure data access: no model loading and no database access.
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
CV_FILE = ROOT / "app" / "dataset" / "CVs" / "ready" / "processed-2026-11-06-17-55-00.txt"
JD_FILE = ROOT / "app" / "dataset" / "JDs" / "ready" / "processed-20261104-151737.txt"
EVAL_DIR = ROOT / "data" / "eval"
PAIRS_FILE = EVAL_DIR / "pairs.csv"
SKILLS_GOLD_FILE = EVAL_DIR / "skills_gold.jsonl"
GAP_GOLD_FILE = EVAL_DIR / "gap_gold.jsonl"

_VI_RE = re.compile(
    "[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def viet_lang(text: str) -> str:
    """Return 'vi' when the text has Vietnamese diacritics (>= 5 occurrences), else 'en'."""
    return "vi" if len(_VI_RE.findall(text or "")) >= 5 else "en"


def sha1_text(text: str) -> str:
    return hashlib.sha1((text or "").encode("utf-8")).hexdigest()


def sha1_file(path: Path) -> str:
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()


def jd_raw_text(record: Dict[str, Any]) -> str:
    raw = record.get("RawText")
    if isinstance(raw, (dict, list)):
        return json.dumps(raw, ensure_ascii=False)
    return raw or ""


def jd_fields(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return the crawler object (job_title, requirements, ...) stored inside RawText."""
    raw = record.get("RawText")
    inner = raw.get("jd_rawtext") if isinstance(raw, dict) else raw
    if isinstance(inner, str):
        try:
            return ast.literal_eval(inner)
        except (ValueError, SyntaxError):
            return {}
    return inner if isinstance(inner, dict) else {}


def load_cvs() -> List[Dict[str, Any]]:
    with CV_FILE.open(encoding="utf-8") as f:
        records = json.load(f)
    for rec in records:
        rec["cv_id"] = Path(rec["file_url"]).stem
        rec["lang"] = viet_lang(rec.get("rawtext") or "")
    return records


def load_jds() -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with JD_FILE.open(encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    for i, line in enumerate(lines):
        rec = json.loads(line)
        rec["jd_id"] = f"jd-{i:02d}"
        rec["lang"] = viet_lang(jd_raw_text(rec))
        records.append(rec)
    return records


def doc_sha1(doc_type: str, record: Dict[str, Any]) -> str:
    return sha1_text(record.get("rawtext") or "") if doc_type == "cv" else sha1_text(jd_raw_text(record))


def load_pairs(path: Path = PAIRS_FILE) -> List[Dict[str, Any]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["relevance"] = int(r["relevance"])
        r["human_verified"] = str(r["human_verified"]).strip().lower() == "true"
    return rows


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_skills_gold(path: Path = SKILLS_GOLD_FILE) -> List[Dict[str, Any]]:
    return _load_jsonl(path)


def load_gap_gold(path: Path = GAP_GOLD_FILE) -> List[Dict[str, Any]]:
    return _load_jsonl(path)


def build_profile(cv_record: Dict[str, Any]):
    """Profile entity as the seed script would build it (needs app models, no DB)."""
    from scripts.profile_seed import _parse_profile_record

    return _parse_profile_record(cv_record)


def build_jd(jd_record: Dict[str, Any]):
    """JD entity as the seed script would build it (needs app models, no DB)."""
    from scripts.jd_seed import _parse_jd_record

    rec = {k: v for k, v in jd_record.items() if k not in ("jd_id", "lang")}
    return _parse_jd_record(json.dumps(rec, ensure_ascii=False))
