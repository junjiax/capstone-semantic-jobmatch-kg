"""Evaluate skill extraction, CV-JD matching/ranking and skill-gap analysis on data/eval labels.

Run from the repo root::

    venv\\Scripts\\python.exe -m scripts.eval.evaluate --out data/eval/results

Real project code paths are used (cv transformation, ``skill_matching``,
``skill_gap_analysis``, the all-MiniLM-L6-v2 sentence-transformer client). Postgres
and Neo4j are not touched: graph/hybrid methods are reported ``not_run`` because they
need seeded Postgres + Neo4j. All labels are AI-assigned and NOT human-verified.
"""
from __future__ import annotations

from scripts.eval import common

common.set_env_guards()  # must run before any ``app`` import

import argparse  # noqa: E402
import itertools  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from collections import defaultdict  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from scripts.eval import data_loading as dl  # noqa: E402
from scripts.eval import metrics as M  # noqa: E402
from scripts.eval.validate_labels import validate  # noqa: E402

SEED = 0
N_BOOT = 1000
RANK_K = 3
NDCG_K = 5
# Match thresholds hard-coded in skill_matching.calculate_cv_jd_matching (0.40 suitable, 0.70 highly suitable).
MATCH_SUITABLE = 0.40
MATCH_HIGHLY = 0.70

ROWS: List[Dict[str, Any]] = []
STATUS: Dict[str, Dict[str, Any]] = {}


def add(task, method, setting, stratum, metric, value, lo=None, hi=None, note=""):
    ROWS.append(
        {
            "task": task, "method": method, "setting": setting, "stratum": stratum, "metric": metric,
            "value": None if value is None else round(float(value), 4),
            "ci_low": None if lo is None else round(float(lo), 4),
            "ci_high": None if hi is None else round(float(hi), 4),
            "note": note,
        }
    )


def get(task, method, setting, stratum, metric):
    for r in ROWS:
        if (r["task"], r["method"], r["setting"], r["stratum"], r["metric"]) == (task, method, setting, stratum, metric):
            return r
    return None


def set_status(key: str, status: str, reason: str = "") -> None:
    STATUS[key] = {"status": status, "reason": reason}


# ---------------------------------------------------------------- generic PRF reporting
def _micro_f1(sample) -> float:
    sp = sum(c[0] for c in sample); sg = sum(c[1] for c in sample)
    ph = sum(c[2] for c in sample); gh = sum(c[3] for c in sample)
    if sp == 0 and sg == 0:
        return 1.0
    p = ph / sp if sp else 0.0
    r = gh / sg if sg else 0.0
    return M.f1_from_pr(p, r)


def report_prf(task, method, setting, stratum, items, mode, note="", ci=True):
    """items: list of (pred, gold) set pairs. Adds micro/macro P, R, F1 rows."""
    if not items:
        return
    res = M.micro_macro_prf(items, mode)
    counts = [M.set_counts(p, g, mode) for p, g in items]
    for k in ("precision", "recall", "f1"):
        lo = hi = None
        if ci and len(items) > 1:
            per = [M.set_prf(p, g, mode)[k] for p, g in items]
            lo, hi = M.bootstrap_ci(per, SEED, N_BOOT)
        add(task, method, setting, stratum, f"macro_{k}", res["macro"][k], lo, hi, f"n={len(items)} {note}".strip())
        lo = hi = None
        if ci and len(items) > 1 and k == "f1":
            lo, hi = M.bootstrap_stat(counts, _micro_f1, SEED, N_BOOT)
        add(task, method, setting, stratum, f"micro_{k}", res["micro"][k], lo, hi, f"n={len(items)} {note}".strip())


# ---------------------------------------------------------------- label / corpus access
class Corpus:
    def __init__(self):
        self.cvs = dl.load_cvs()
        self.jds = dl.load_jds()
        self.cv_by_id: Dict[str, Dict[str, Any]] = {}
        for c in self.cvs:
            self.cv_by_id.setdefault(c["cv_id"], c)
        self.jd_by_id = {j["jd_id"]: j for j in self.jds}
        self.pairs = dl.load_pairs()
        self.skills = dl.load_skills_gold()
        self.gaps = dl.load_gap_gold()
        self.gold = {(s["doc_type"], s["doc_id"]): s for s in self.skills}
        self.gap_by_pair = {g["pair_id"]: g for g in self.gaps}


# ---------------------------------------------------------------- extraction
def dictionary_extract(text: str, vocabulary: Sequence[str]) -> List[str]:
    """Same regex the project uses in evaluate_smart_skill_matching's fallback."""
    return [kw for kw in vocabulary if re.search(r"\b" + re.escape(kw) + r"\b", text, re.IGNORECASE)]


def eval_extraction(corpus: Corpus, sm, details: Dict[str, Any]) -> None:
    from app.dataset.CVs.transformation.main import _build_profile
    from app.models.profile import Profile

    # --- CV
    cv_docs = [s for s in corpus.skills if s["doc_type"] == "cv"]
    preds: Dict[str, Dict[str, List[str]]] = {"cv_rules": {}, "dictionary": {}}
    same = 0
    for s in cv_docs:
        rec = corpus.cv_by_id[s["doc_id"]]
        out = _build_profile(rec["file_url"], rec["rawtext"])["skilltitle"]
        same += int(out == rec["skilltitle"])
        preds["cv_rules"][s["doc_id"]] = out
        preds["dictionary"][s["doc_id"]] = dictionary_extract(rec["rawtext"], sm.COMMON_EXTRACT_SKILLS)
    details["cv_rules_matches_ready_file_skilltitle"] = f"{same}/{len(cv_docs)}"
    details["n_cv_docs"] = len(cv_docs)
    details["n_jd_docs"] = sum(1 for s in corpus.skills if s["doc_type"] == "jd")
    for method, p in preds.items():
        for mode in ("exact", "soft"):
            items = [(p[s["doc_id"]], s["skills"]) for s in cv_docs]
            report_prf("extraction_cv", method, mode, "all", items, mode)
            for lang in ("en", "vi"):
                sub = [(p[s["doc_id"]], s["skills"]) for s in cv_docs if s["lang"] == lang]
                report_prf("extraction_cv", method, mode, lang, sub, mode, ci=False)
    details["extraction_cv_predictions"] = preds

    # --- JD
    jd_docs = [s for s in corpus.skills if s["doc_type"] == "jd"]
    jpreds: Dict[str, Dict[str, List[str]]] = {"jd_tags": {}, "dictionary": {}}
    for s in jd_docs:
        rec = corpus.jd_by_id[s["doc_id"]]
        jpreds["jd_tags"][s["doc_id"]] = list(rec.get("JobSkills") or [])
        jd_entity = dl.build_jd(rec)
        jd_entity.skills = []  # force the project's text-extraction fallback
        analysis = sm.evaluate_smart_skill_matching(Profile(), jd_entity)
        jpreds["dictionary"][s["doc_id"]] = list(analysis["missing_skills"])
    for method, p in jpreds.items():
        note = "JobSkills are crawler tags (provided field), not an extraction method" if method == "jd_tags" else ""
        for mode in ("exact", "soft"):
            items = [(p[s["doc_id"]], s["skills"]) for s in jd_docs]
            report_prf("extraction_jd", method, mode, "all", items, mode, note)
            for lang in ("en", "vi"):
                sub = [(p[s["doc_id"]], s["skills"]) for s in jd_docs if s["lang"] == lang]
                report_prf("extraction_jd", method, mode, lang, sub, mode, note, ci=False)
    details["extraction_jd_predictions"] = jpreds
    set_status("extraction_cv/cv_rules", "ok", "app.dataset.CVs.transformation.main._build_profile")
    set_status("extraction_cv/dictionary", "ok", "regex over skill_matching.COMMON_EXTRACT_SKILLS")
    set_status("extraction_jd/jd_tags", "ok", "JobSkills field as stored (not an extractor)")
    set_status("extraction_jd/dictionary", "ok", "skill_matching.evaluate_smart_skill_matching fallback")


# ---------------------------------------------------------------- matching / ranking
def keyword_score(cv_text: str, tags: Sequence[str]) -> float:
    tags = [M.normalize_skill(t) for t in tags if M.normalize_skill(t)]
    if not tags:
        return 0.0
    text = cv_text.lower()
    hit = sum(1 for t in tags if re.search(r"(?<![\w+#])" + re.escape(t) + r"(?![\w+#])", text))
    return hit / len(tags)


def _db_stub(profile, jd):
    from app.models.profile import Profile
    from sqlalchemy.orm import Session

    db = MagicMock(spec=Session)

    def query(model):
        q = MagicMock()
        q.filter.return_value.first.return_value = profile if model is Profile else jd
        return q

    db.query.side_effect = query
    return db


def project_match(sm, profile, jd) -> Dict[str, Any]:
    """Run the real calculate_cv_jd_matching with a stub session and no-op graph writes."""
    saved = (sm.sync_cv_to_graph, sm.sync_job_to_graph, sm.save_cv_jd_match_result_graph)
    sm.sync_cv_to_graph = sm.sync_job_to_graph = sm.save_cv_jd_match_result_graph = lambda *a, **k: None
    try:
        return sm.calculate_cv_jd_matching(_db_stub(profile, jd), 1, 1)
    finally:
        sm.sync_cv_to_graph, sm.sync_job_to_graph, sm.save_cv_jd_match_result_graph = saved


def rank_metrics_for_group(scores: List[float], rels: List[int]) -> Dict[str, float]:
    # Pessimistic tie-breaking: among equal scores the lower relevance is ranked first.
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], rels[i]))
    ranked = [rels[i] for i in order]
    return {
        "p_at_1": M.precision_at_k(ranked, 1),
        f"p_at_{RANK_K}": M.precision_at_k(ranked, RANK_K),
        "mrr": M.reciprocal_rank(ranked),
        f"ndcg_at_{NDCG_K}": M.ndcg_at_k(ranked, NDCG_K),
    }


def random_expected(rels: List[int]) -> Dict[str, float]:
    perms = list(itertools.permutations(rels))
    acc: Dict[str, float] = defaultdict(float)
    for perm in perms:
        ranked = list(perm)
        acc["p_at_1"] += M.precision_at_k(ranked, 1)
        acc[f"p_at_{RANK_K}"] += M.precision_at_k(ranked, RANK_K)
        acc["mrr"] += M.reciprocal_rank(ranked)
        acc[f"ndcg_at_{NDCG_K}"] += M.ndcg_at_k(ranked, NDCG_K)
    return {k: v / len(perms) for k, v in acc.items()}


def eval_matching(corpus: Corpus, sm, client, details: Dict[str, Any]) -> None:
    from app.services.semantic_search.text_embedding import build_job_text, normalize_text

    per_pair: List[Dict[str, Any]] = []
    max_diff = 0.0
    for p in corpus.pairs:
        cv = corpus.cv_by_id[p["cv_id"]]
        jd = corpus.jd_by_id[p["jd_id"]]
        profile, jd_entity = dl.build_profile(cv), dl.build_jd(jd)
        cv_text = normalize_text(profile.CleanText) or normalize_text(profile.RawText)
        jd_text = build_job_text(jd_entity) or normalize_text(jd_entity.CleanText) or normalize_text(jd_entity.RawText)
        sim = client.cosine_similarity(client.encode(cv_text, normalize=True), client.encode(jd_text, normalize=True))
        res = project_match(sm, profile, jd_entity)
        max_diff = max(max_diff, abs(sim - res["semantic_similarity"]))
        per_pair.append(
            {
                "pair_id": p["pair_id"], "jd_id": p["jd_id"], "cv_id": p["cv_id"], "relevance": p["relevance"],
                "jd_lang": p["jd_lang"], "cv_lang": p["cv_lang"],
                "keyword": keyword_score(cv.get("cleantext") or cv["rawtext"], jd.get("JobSkills") or []),
                "vector_only": sim,
                "project_match": res["match_score"],
                "project_fit_level": res["fit_level"],
                "project_semantic_similarity": res["semantic_similarity"],
                "jd_tag_count": len(jd.get("JobSkills") or []),
            }
        )
    details["vector_only_vs_project_semantic_max_abs_diff"] = round(max_diff, 6)
    details["matching_per_pair"] = per_pair
    methods = ["keyword", "vector_only", "project_match"]
    for m in methods:
        set_status(f"matching/{m}", "ok", {
            "keyword": "share of JD JobSkills tags found as whole words in CV cleantext (0 if JD has no tags)",
            "vector_only": "cosine(encode(CV text), encode(build_job_text(JD))) with all-MiniLM-L6-v2, in memory",
            "project_match": "skill_matching.calculate_cv_jd_matching (stub session, graph writes no-op), match_score",
        }[m])

    labels1 = [int(r["relevance"] >= 1) for r in per_pair]
    labels2 = [int(r["relevance"] >= 2) for r in per_pair]
    n = len(per_pair)

    def auc_stat(items):
        return M.roc_auc([s for s, _ in items], [y for _, y in items])

    def f1_at(threshold):
        def stat(items):
            c = M.confusion_at_threshold([s for s, _ in items], [y for _, y in items], threshold)
            return M.binary_prf(c["tp"], c["fp"], c["fn"])["f1"]
        return stat

    for m in methods:
        scores = [r[m] for r in per_pair]
        for tag, labels in (("rel>=1", labels1), ("rel>=2", labels2)):
            items = list(zip(scores, labels))
            auc = M.roc_auc(scores, labels)
            lo, hi = M.bootstrap_stat(items, auc_stat, SEED, N_BOOT)
            add("matching_classification", m, tag, "all", "roc_auc", auc, lo, hi, f"n={n}, positives={sum(labels)}")
            sweep = M.threshold_sweep(scores, labels)
            best = M.best_f1(sweep)
            lo, hi = M.bootstrap_stat(items, f1_at(best["threshold"]), SEED, N_BOOT)
            note = f"in_sample_optimistic threshold={best['threshold']:.4f}"
            add("matching_classification", m, tag, "all", "best_f1_precision", best["precision"], note=note)
            add("matching_classification", m, tag, "all", "best_f1_recall", best["recall"], note=note)
            add("matching_classification", m, tag, "all", "best_f1", best["f1"], lo, hi, note)
            for lang_key in ("jd_lang", "cv_lang"):
                for lang in ("en", "vi"):
                    sub = [(r[m], int(r["relevance"] >= (1 if tag == "rel>=1" else 2))) for r in per_pair if r[lang_key] == lang]
                    a = M.roc_auc([s for s, _ in sub], [y for _, y in sub]) if sub else None
                    add("matching_classification", m, tag, f"{lang_key}={lang}", "roc_auc", a,
                        note=f"n={len(sub)}, positives={sum(y for _, y in sub)}")
    # project default thresholds (primary result)
    scores = [r["project_match"] for r in per_pair]
    for tag, labels, thr in (("rel>=1", labels1, MATCH_SUITABLE), ("rel>=2", labels2, MATCH_HIGHLY)):
        c = M.classification_at_threshold(scores, labels, thr)
        items = list(zip(scores, labels))
        lo, hi = M.bootstrap_stat(items, f1_at(thr), SEED, N_BOOT)
        note = f"project default threshold={thr} (is_suitable>=0.40, HIGHLY_SUITABLE>=0.70)"
        add("matching_classification", "project_match", tag, "all", "precision@default", c["precision"], note=note)
        add("matching_classification", "project_match", tag, "all", "recall@default", c["recall"], note=note)
        add("matching_classification", "project_match", tag, "all", "f1@default", c["f1"], lo, hi, note)
    # always-positive reference
    for tag, labels in (("rel>=1", labels1), ("rel>=2", labels2)):
        prec = sum(labels) / n
        add("matching_classification", "always_positive", tag, "all", "f1@default",
            M.f1_from_pr(prec, 1.0), note=f"precision={prec:.4f}, recall=1.0 (reference)")

    # ranking per JD
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in per_pair:
        groups[r["jd_id"]].append(r)
    for m in methods + ["random_order"]:
        per_jd: Dict[str, Dict[str, float]] = {}
        for jd_id, rows in groups.items():
            rels = [r["relevance"] for r in rows]
            if m == "random_order":
                per_jd[jd_id] = random_expected(rels)
            else:
                per_jd[jd_id] = rank_metrics_for_group([r[m] for r in rows], rels)
        for metric in ("p_at_1", f"p_at_{RANK_K}", "mrr", f"ndcg_at_{NDCG_K}"):
            vals = [per_jd[j][metric] for j in per_jd]
            lo, hi = M.bootstrap_ci(vals, SEED, N_BOOT)
            note = "expected value over all 5! orderings" if m == "random_order" else "pessimistic tie-breaking"
            add("ranking", m, "per_jd", "all", metric, M.mean(vals), lo, hi, f"n_jd={len(vals)}; {note}")
            for lang in ("en", "vi"):
                sub = [per_jd[j][metric] for j in per_jd if groups[j][0]["jd_lang"] == lang]
                if sub:
                    add("ranking", m, "per_jd", f"jd_lang={lang}", metric, M.mean(sub), note=f"n_jd={len(sub)}")
    set_status("matching/graph_hybrid", "not_run", "")  # reason filled by caller
    set_status("matching/random_order", "ok", "expected metrics under uniformly random ranking")


# ---------------------------------------------------------------- skill gap
def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def gap_keyword(cands: List[str], reqs: List[str]) -> Dict[str, set]:
    cn = {_norm(c) for c in cands}
    matched = {r for r in reqs if _norm(r) in cn}
    return {"matched": matched, "partial": set(), "missing": set(reqs) - matched}


def gap_vector(embed, cands: List[str], reqs: List[str], threshold: float) -> Dict[str, set]:
    import numpy as np

    if not cands:
        return {"matched": set(), "partial": set(), "missing": set(reqs)}
    C = np.array([embed(c) for c in cands]); R = np.array([embed(r) for r in reqs])
    sims = R @ C.T
    matched = {r for r, row in zip(reqs, sims) if float(row.max()) >= threshold}
    return {"matched": matched, "partial": set(), "missing": set(reqs) - matched}


def gap_project(gap_service, request_cls, cands: List[str], reqs: List[str]) -> Dict[str, set]:
    resp = gap_service(None, request_cls(candidate_skills=cands or None, required_skills=reqs))
    return {
        "matched": {i.skill_name for i in resp.matched_skills},
        "partial": {i.skill_name for i in resp.partially_matched_skills},
        "missing": {i.skill_name for i in resp.missing_skills},
    }


def gap_smart(sm, cands: List[str], reqs: List[str]) -> Dict[str, set]:
    from app.models.jd import JD
    from app.models.jd_skill import JDSkill
    from app.models.profile import Profile
    from app.models.profile_skill import ProfileSkill

    profile = Profile(skills=[ProfileSkill(SkillTitle=c) for c in cands])
    jd = JD(Title="eval", skills=[JDSkill(Title=r) for r in reqs])
    a = sm.evaluate_smart_skill_matching(profile, jd)
    return {
        "matched": set(a["matched_core_skills"]) | set(a["matched_tool_skills"]),
        "partial": {t["required_skill"] for t in a["transferable_skills"]},
        "missing": set(a["missing_skills"]),
    }


def eval_gap(corpus: Corpus, sm, client, details: Dict[str, Any]) -> None:
    from app.schemas.skill_gap import SkillGapAnalysisRequest
    from app.services.skill_features.skill_gap_analysis import analyze_skill_gap_service

    defaults = SkillGapAnalysisRequest(candidate_skills=["a"], required_skills=["b"])
    t_match, t_partial = defaults.match_threshold, defaults.partial_threshold
    details["gap_thresholds"] = {"match_threshold": t_match, "partial_threshold": t_partial}

    cache: Dict[str, Any] = {}

    def embed(text: str):
        if text not in cache:
            cache[text] = client.encode(text, normalize=True)
        return cache[text]

    methods: List[Tuple[str, str, Callable[[List[str], List[str]], Dict[str, set]]]] = [
        ("keyword", "exact normalized equality", lambda c, r: gap_keyword(c, r)),
        (f"vector_only@{t_match}", "cosine >= match_threshold, no partial class", lambda c, r: gap_vector(embed, c, r, t_match)),
        (f"vector_only@{t_partial}", "cosine >= partial_threshold, no partial class", lambda c, r: gap_vector(embed, c, r, t_partial)),
        ("project_gap", "analyze_skill_gap_service (db=None)", lambda c, r: gap_project(analyze_skill_gap_service, SkillGapAnalysisRequest, c, r)),
        ("project_smart", "evaluate_smart_skill_matching (exact/substring + clusters)", lambda c, r: gap_smart(sm, c, r)),
    ]
    for name, desc, _ in methods:
        set_status(f"gap/{name}", "ok", desc)
    set_status("gap/graph_neo4j", "not_run", "")

    three_class = {"project_gap", "project_smart"}
    settings = {
        "gold_inputs": lambda cv_id, g: g["cv_skills"],
        "pipeline_cv_skills": lambda cv_id, g: list(corpus.cv_by_id[cv_id].get("skilltitle") or []),
    }
    preds_out: Dict[str, Any] = {}
    for setting, cand_fn in settings.items():
        per_method_items: Dict[str, Dict[str, List[Tuple[set, set]]]] = {}
        langs: Dict[str, List[str]] = {}
        for name, _, fn in methods:
            per_method_items[name] = defaultdict(list)
            langs[name] = []
        for p in corpus.pairs:
            g = corpus.gap_by_pair[p["pair_id"]]
            reqs = corpus.gold[("jd", p["jd_id"])]["skills"]
            info = {"cv_skills": corpus.gold[("cv", p["cv_id"])]["skills"]}
            cands = cand_fn(p["cv_id"], info)
            gold = {"matched": set(g["matched"]), "partial": set(g["partial"]), "missing": set(g["missing"])}
            gold["covered"] = gold["matched"] | gold["partial"]
            for name, _, fn in methods:
                pred = fn(cands, reqs)
                pred["covered"] = pred["matched"] | pred["partial"]
                preds_out.setdefault(setting, {}).setdefault(name, {})[p["pair_id"]] = {k: sorted(v) for k, v in pred.items()}
                for cls in ("matched", "partial", "missing", "covered"):
                    per_method_items[name][cls].append((pred[cls], gold[cls]))
                langs[name].append(p["jd_lang"])
        for name, _, _ in methods:
            base = name.split("@")[0]
            classes = ["matched", "missing", "covered"] + (["partial"] if base in three_class else [])
            for cls in classes:
                items = per_method_items[name][cls]
                report_prf(f"gap_{cls}", name, setting, "all", items, "exact")
                for lang in ("en", "vi"):
                    sub = [it for it, lg in zip(items, langs[name]) if lg == lang]
                    report_prf(f"gap_{cls}", name, setting, f"jd_lang={lang}", sub, "exact", ci=False)
        # gap-gold class sizes for context
    details["gap_predictions"] = preds_out
    details["gap_gold_class_sizes"] = {
        cls: sum(len(g[cls]) for g in corpus.gaps) for cls in ("matched", "partial", "missing")
    }


# ---------------------------------------------------------------- summary
def fmt(r: Optional[Dict[str, Any]], ci: bool = True) -> str:
    if r is None or r["value"] is None:
        return "n/a"
    s = f"{r['value']:.3f}"
    if ci and r["ci_low"] is not None:
        s += f" [{r['ci_low']:.2f}, {r['ci_high']:.2f}]"
    return s


def build_summary(config: Dict[str, Any], details: Dict[str, Any]) -> str:
    L: List[str] = []
    A = L.append
    A("# Evaluation summary (auto-generated; do not edit by hand)\n")
    A(f"> **Labels are AI-assigned (single annotator) and NOT human-verified.** n={config['n_pairs']} pairs / {config['n_pair_jds']} JDs / "
      f"{details['n_cv_docs']} CVs with gold skills, hand-picked (not random). "
      "Confidence intervals are wide. See `data/eval/ANNOTATION_GUIDELINE.md`.\n")
    A("## Run configuration\n")
    A(f"- Date (UTC): {config['date_utc']}")
    g = config["git"]
    A(f"- Git commit: `{g['commit']}` (working tree dirty: {g['dirty']}, {g['dirty_files']} changed file(s))")
    mi = config["model"]
    A(f"- Model: `{mi.get('model_name', config['model_requested'])}`, device `{mi.get('device', 'n/a')}`, dim {mi.get('embedding_dim', 'n/a')}, status `{mi['status']}`")
    A(f"- Versions: {config['versions']}")
    A(f"- OS / CPU: {config['os']} / {config['cpu']} ({config['cpu_count']} logical)")
    t = config["thresholds"]
    A(f"- Thresholds: match is_suitable>={t['match_suitable']}, HIGHLY_SUITABLE>={t['match_highly']}; "
      f"gap match>={t['gap_match']}, partial>={t['gap_partial']}; ranking k={t['rank_k']}, nDCG@{t['ndcg_k']}")
    A(f"- Bootstrap: seed {config['seed']}, {config['bootstrap_resamples']} resamples, 95% percentile CI (over docs/pairs/JDs as stated)")
    A(f"- Label files sha1: {config['label_file_sha1']}\n")
    A("## Method status\n")
    A("| key | status | detail |\n|---|---|---|")
    for k, v in STATUS.items():
        A(f"| {k} | {v['status']} | {v['reason']} |")
    A("")

    def extraction_table(task, title):
        A(f"## {title}\n")
        A("| method | matching | micro P | micro R | micro F1 [CI] | macro P | macro R | macro F1 [CI] |\n|---|---|---|---|---|---|---|---|")
        methods = sorted({r["method"] for r in ROWS if r["task"] == task})
        for m in methods:
            for mode in ("exact", "soft"):
                g = lambda metric: get(task, m, mode, "all", metric)
                A(f"| {m} | {mode} | {fmt(g('micro_precision'), False)} | {fmt(g('micro_recall'), False)} | {fmt(g('micro_f1'))} | "
                  f"{fmt(g('macro_precision'), False)} | {fmt(g('macro_recall'), False)} | {fmt(g('macro_f1'))} |")
        A("")

    extraction_table("extraction_cv", f"Skill extraction: CVs ({details['n_cv_docs']} docs)")
    A(f"`cv_rules` output equals the stored `skilltitle` for {details.get('cv_rules_matches_ready_file_skilltitle')} gold CVs (sanity check of the code path).\n")
    extraction_table("extraction_jd", f"Skill extraction: JDs ({details['n_jd_docs']} docs)")
    A("`jd_tags` is the crawler's `JobSkills` field passed through, not an extractor. Some JDs have unrelated or empty tags (see guideline).\n")

    A("## Matching: classification (relevance as ground truth)\n")
    A("| method | positive | ROC AUC [CI] | project default P / R / F1 | best-F1 (in-sample, optimistic) P / R / F1 [CI] |\n|---|---|---|---|---|")
    for m in ("keyword", "vector_only", "project_match"):
        for tag in ("rel>=1", "rel>=2"):
            gt = lambda metric: get("matching_classification", m, tag, "all", metric)
            d = ""
            if m == "project_match":
                d = f"{fmt(gt('precision@default'), False)} / {fmt(gt('recall@default'), False)} / {fmt(gt('f1@default'))}"
            b = gt("best_f1")
            thr = re.search(r"threshold=(-?[\d.]+)", b["note"]).group(1) if b else "?"
            A(f"| {m} | {tag} | {fmt(gt('roc_auc'))} | {d or '-'} | "
              f"{fmt(gt('best_f1_precision'), False)} / {fmt(gt('best_f1_recall'), False)} / {fmt(b)} (t={thr}) |")
    for tag in ("rel>=1", "rel>=2"):
        r = get("matching_classification", "always_positive", tag, "all", "f1@default")
        A(f"| always_positive (reference) | {tag} | - | F1 {fmt(r, False)} ({r['note']}) | - |")
    A("\nProject default thresholds: `match_score >= 0.40` against rel>=1, `>= 0.70` against rel>=2.\n")

    A("## Matching: ranking within each JD (5 CVs per JD, mean over 8 JDs)\n")
    A(f"| method | P@1 | P@{RANK_K} | MRR | nDCG@{NDCG_K} |\n|---|---|---|---|---|")
    for m in ("keyword", "vector_only", "project_match", "random_order"):
        g = lambda metric: get("ranking", m, "per_jd", "all", metric)
        A(f"| {m} | {fmt(g('p_at_1'))} | {fmt(g(f'p_at_{RANK_K}'))} | {fmt(g('mrr'))} | {fmt(g(f'ndcg_at_{NDCG_K}'))} |")
    A("\nTies are broken pessimistically (lower relevance first). `random_order` is the exact expectation over all orderings.\n")
    A("Split by JD language (mean over JDs, no CI): see `eval_metrics.csv` rows with stratum `jd_lang=en|vi`.\n")

    A("## Skill gap (micro P / R / F1 vs gap_gold; exact name equality on JD gold skill names)\n")
    for setting in ("gold_inputs", "pipeline_cv_skills"):
        A(f"### Setting `{setting}`" + (" (gold CV skills vs gold JD skills)" if setting == "gold_inputs" else " (CV skills from the project's CV extraction vs gold JD skills)") + "\n")
        A("| method | class | P | R | F1 [CI] | macro F1 |\n|---|---|---|---|---|---|")
        names = sorted({r["method"] for r in ROWS if r["task"].startswith("gap_")})
        for m in names:
            for cls in ("matched", "partial", "missing", "covered"):
                task = f"gap_{cls}"
                if get(task, m, setting, "all", "micro_f1") is None:
                    continue
                A(f"| {m} | {cls} | {fmt(get(task, m, setting, 'all', 'micro_precision'), False)} | "
                  f"{fmt(get(task, m, setting, 'all', 'micro_recall'), False)} | {fmt(get(task, m, setting, 'all', 'micro_f1'))} | "
                  f"{fmt(get(task, m, setting, 'all', 'macro_f1'), False)} |")
        A("")
    A(f"Gold class sizes over 40 pairs: {details.get('gap_gold_class_sizes')}. `covered` = matched or partial. "
      "Macro averages count pairs where both sets are empty as 1.0, so prefer micro.\n")

    A("## Not run\n")
    for k, v in STATUS.items():
        if v["status"] != "ok":
            A(f"- `{k}`: {v['status']}. {v['reason']}")
    A("")
    A("## Caveats\n")
    A("- Labels: one AI annotator, no human verification, no inter-annotator agreement.")
    A("- 40 pairs, 8 JDs; hand-picked CVs (mostly IT roles). Best-F1 thresholds are tuned on the same pairs (optimistic).")
    A("- Project thresholds (match 0.70/0.40, gap 0.82/0.60) were not calibrated for all-MiniLM-L6-v2 on this data.")
    A("- `project_match` ran with a stub DB session and no-op graph writes; its vector part is the real model. Postgres/pgvector and Neo4j were not used.")
    A("- Several JDs have noisy/empty `JobSkills` tags, which hurts the keyword baseline and the project's tag-based skill score.")
    A("- `gold_inputs` gap scores are optimistic for name-based methods: the same annotator wrote both skill lists in one canonical naming, so exact names mostly line up. The `partial` class is the informative one.")
    ap1 = get("matching_classification", "always_positive", "rel>=1", "all", "f1@default")
    A(f"- Class balance matters: at rel>=1 an always-positive predictor reaches F1 {ap1['value']:.3f} ({ap1['note']}); compare methods against that row.")
    A("- all-MiniLM-L6-v2 truncates input at 256 word pieces; long CVs are embedded from their beginning only.")
    A(f"- vector_only equals project semantic similarity (max abs diff {details.get('vector_only_vs_project_semantic_max_abs_diff')}).")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/eval/results", help="output directory")
    args = ap.parse_args(argv)
    out = Path(args.out)
    if not out.is_absolute():
        out = common.ROOT / out

    t0 = time.time()
    corpus = Corpus()
    errs = validate(corpus.pairs, corpus.skills, corpus.gaps, corpus.cvs, corpus.jds)
    if errs:
        print("Label validation failed:\n" + "\n".join(errs), file=sys.stderr)
        return 2

    config = common.base_config()
    config["model"] = common.model_info()
    probes = config["service_probes"]
    neo4j_up = probes["neo4j_7687"]["reachable"]
    pg_up = probes["postgres_5432"]["reachable"] or probes["postgres_55432"]["reachable"]
    if config["model"]["status"] != "ok":
        print("Model unavailable:", config["model"]["reason"], file=sys.stderr)
        return 3

    from app.clients.sentence_transformer import get_sentence_transformer
    from app.services.skill_features import skill_matching as sm

    client = get_sentence_transformer()
    config.update({
        "seed": SEED, "bootstrap_resamples": N_BOOT,
        "thresholds": {"match_suitable": MATCH_SUITABLE, "match_highly": MATCH_HIGHLY, "gap_match": None, "gap_partial": None,
                       "rank_k": RANK_K, "ndcg_k": NDCG_K},
        "n_pairs": len(corpus.pairs),
        "n_pair_jds": len({p["jd_id"] for p in corpus.pairs}),
        "labels_provenance": "ai-agent, human_verified=false for every label",
    })
    details: Dict[str, Any] = {}
    eval_extraction(corpus, sm, details)
    eval_matching(corpus, sm, client, details)
    eval_gap(corpus, sm, client, details)
    config["thresholds"]["gap_match"] = details["gap_thresholds"]["match_threshold"]
    config["thresholds"]["gap_partial"] = details["gap_thresholds"]["partial_threshold"]

    def not_run_reason(service: str, up: bool) -> str:
        if not up:
            return f"{service} not reachable on localhost (TCP probe), so the graph/hybrid method was not run"
        return (f"{service} is reachable, but the graph method needs CVs/JDs seeded into Postgres and Neo4j; "
                "this script does not seed them, so it was not run")

    set_status("matching/graph_hybrid", "not_run",
               "graph_service.calculate_cv_jd_matching_service / hybrid_match_cvs_for_job_graph: " + not_run_reason("Neo4j/Postgres", neo4j_up and pg_up))
    set_status("gap/graph_neo4j", "not_run", "match_crud.analyze_skill_gap_graph: " + not_run_reason("Neo4j", neo4j_up))
    config["runtime_seconds"] = round(time.time() - t0, 1)

    result = {"config": config, "method_status": STATUS, "metrics": ROWS, "details": details}
    common.write_json(out / "eval_results.json", result)
    common.write_csv(out / "eval_metrics.csv", ROWS,
                     ["task", "method", "setting", "stratum", "metric", "value", "ci_low", "ci_high", "note"])
    summary = build_summary(config, details)
    (out / "eval_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(summary)
    print(f"Wrote {out / 'eval_results.json'}, {out / 'eval_metrics.csv'}, {out / 'eval_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
