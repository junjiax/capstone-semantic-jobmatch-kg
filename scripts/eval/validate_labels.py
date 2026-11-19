"""Consistency checks for the labeled evaluation set (data/eval/*).

``validate(...)`` returns a list of error strings (empty list = valid).
Run ``python -m scripts.eval.validate_labels`` to validate the real files and
print a relevance-vs-coverage report (informational, not an error).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from scripts.eval import data_loading as dl

EXPECTED_PAIRS = 40
EXPECTED_JDS = 8
CVS_PER_JD = 5


def validate(
    pairs: List[Dict[str, Any]],
    skills: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    cvs: List[Dict[str, Any]],
    jds: List[Dict[str, Any]],
) -> List[str]:
    errors: List[str] = []
    cv_by_id = defaultdict(list)
    for c in cvs:
        cv_by_id[c["cv_id"]].append(c)
    jd_by_id = {j["jd_id"]: j for j in jds}

    # ---- pairs
    if len(pairs) != EXPECTED_PAIRS:
        errors.append(f"expected {EXPECTED_PAIRS} pairs, found {len(pairs)}")
    ids = [p["pair_id"] for p in pairs]
    if len(set(ids)) != len(ids):
        errors.append("duplicate pair_id")
    seen = set()
    per_jd: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        key = (p["jd_id"], p["cv_id"])
        if key in seen:
            errors.append(f"duplicate (jd, cv) pair {key}")
        seen.add(key)
        per_jd[p["jd_id"]].append(p)
        if p["jd_id"] not in jd_by_id:
            errors.append(f"{p['pair_id']}: unknown jd_id {p['jd_id']}")
        if p["cv_id"] not in cv_by_id:
            errors.append(f"{p['pair_id']}: unknown cv_id {p['cv_id']}")
        elif len({c["rawtext"] for c in cv_by_id[p["cv_id"]]}) > 1:
            errors.append(f"{p['pair_id']}: cv_id {p['cv_id']} is ambiguous in the corpus")
        if p["relevance"] not in (0, 1, 2):
            errors.append(f"{p['pair_id']}: relevance must be 0, 1 or 2")
        if p.get("annotator") != "ai-agent":
            errors.append(f"{p['pair_id']}: annotator must be 'ai-agent'")
        if not isinstance(p.get("human_verified"), bool):
            errors.append(f"{p['pair_id']}: human_verified must be boolean")
    if len(per_jd) != EXPECTED_JDS:
        errors.append(f"expected {EXPECTED_JDS} JDs in pairs, found {len(per_jd)}")
    for jd_id, rows in per_jd.items():
        if len(rows) != CVS_PER_JD:
            errors.append(f"{jd_id}: expected {CVS_PER_JD} CVs, found {len(rows)}")
        rels = [r["relevance"] for r in rows]
        if not any(r >= 1 for r in rels):
            errors.append(f"{jd_id}: no CV with relevance >= 1")
        if not any(r == 0 for r in rels):
            errors.append(f"{jd_id}: no CV with relevance 0")

    # ---- skills_gold
    gold: Dict[tuple, Dict[str, Any]] = {}
    for s in skills:
        key = (s["doc_type"], s["doc_id"])
        if key in gold:
            errors.append(f"duplicate skills_gold record {key}")
        gold[key] = s
        if s["doc_type"] not in ("cv", "jd"):
            errors.append(f"{key}: doc_type must be cv or jd")
            continue
        if s.get("annotator") != "ai-agent":
            errors.append(f"{key}: annotator must be 'ai-agent'")
        if not isinstance(s.get("human_verified"), bool):
            errors.append(f"{key}: human_verified must be boolean")
        sk = s.get("skills")
        if not isinstance(sk, list) or not sk:
            errors.append(f"{key}: skills must be a non-empty list")
            continue
        for x in sk:
            if not isinstance(x, str) or not x.strip() or x != x.lower() or x != x.strip():
                errors.append(f"{key}: skill {x!r} must be a non-empty lowercase trimmed string")
        if len(set(sk)) != len(sk):
            errors.append(f"{key}: duplicate skills")
        if s["doc_type"] == "cv":
            recs = cv_by_id.get(s["doc_id"])
            if not recs:
                errors.append(f"{key}: unknown cv_id")
            elif dl.doc_sha1("cv", recs[0]) != s["text_sha1"]:
                errors.append(f"{key}: text_sha1 mismatch (corpus changed?)")
        else:
            rec = jd_by_id.get(s["doc_id"])
            if rec is None:
                errors.append(f"{key}: unknown jd_id")
            elif dl.doc_sha1("jd", rec) != s["text_sha1"]:
                errors.append(f"{key}: text_sha1 mismatch (corpus changed?)")
    for p in pairs:
        if ("cv", p["cv_id"]) not in gold:
            errors.append(f"{p['pair_id']}: no skills_gold record for CV {p['cv_id']}")
        if ("jd", p["jd_id"]) not in gold:
            errors.append(f"{p['pair_id']}: no skills_gold record for JD {p['jd_id']}")
    n_jd = sum(1 for k in gold if k[0] == "jd")
    if n_jd < 15:
        errors.append(f"expected skills for at least 15 JDs, found {n_jd}")

    # ---- gap_gold
    gap_ids = [g["pair_id"] for g in gaps]
    if sorted(gap_ids) != sorted(ids):
        errors.append("gap_gold pair_ids differ from pairs.csv")
    pair_by_id = {p["pair_id"]: p for p in pairs}
    for g in gaps:
        p = pair_by_id.get(g["pair_id"])
        if p is None:
            continue
        if g.get("annotator") != "ai-agent" or not isinstance(g.get("human_verified"), bool):
            errors.append(f"{g['pair_id']}: gap annotator/human_verified invalid")
        jd_gold = gold.get(("jd", p["jd_id"]))
        if jd_gold is None:
            continue
        m, pa, mi = set(g["matched"]), set(g["partial"]), set(g["missing"])
        if (m & pa) or (m & mi) or (pa & mi):
            errors.append(f"{g['pair_id']}: matched/partial/missing overlap")
        if (m | pa | mi) != set(jd_gold["skills"]):
            errors.append(f"{g['pair_id']}: matched+partial+missing must equal the JD gold skills")
    return errors


def coverage_report(pairs, gaps) -> List[str]:
    gap_by_id = {g["pair_id"]: g for g in gaps}
    lines = ["pair  jd     rel  matched partial missing  coverage(matched+0.5*partial)/total"]
    for p in pairs:
        g = gap_by_id[p["pair_id"]]
        total = len(g["matched"]) + len(g["partial"]) + len(g["missing"])
        cov = (len(g["matched"]) + 0.5 * len(g["partial"])) / total if total else 0.0
        lines.append(
            f"{p['pair_id']}  {p['jd_id']}  {p['relevance']}    {len(g['matched']):>7} {len(g['partial']):>7} "
            f"{len(g['missing']):>7}  {cov:.2f}"
        )
    return lines


def main() -> int:
    pairs, skills, gaps = dl.load_pairs(), dl.load_skills_gold(), dl.load_gap_gold()
    errors = validate(pairs, skills, gaps, dl.load_cvs(), dl.load_jds())
    for e in errors:
        print("ERROR:", e)
    print("\n".join(coverage_report(pairs, gaps)))
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
