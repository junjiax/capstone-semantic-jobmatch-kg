"""Latency benchmark: end-to-end and per-stage, with warm-up and repeated runs.

Run from the repo root::

    venv\\Scripts\\python.exe -m scripts.eval.latency --repeats 30 --warmup 5

Real code paths are timed (sentence-transformer client, ``calculate_cv_jd_matching``,
``analyze_skill_gap_service``). No network or LLM calls. Stages that need Postgres/pgvector
or Neo4j are reported ``skipped`` with the reason, never faked. The vector search is an
in-memory numpy stand-in over embeddings, labelled as such; it is NOT a pgvector measurement.
"""
from __future__ import annotations

from scripts.eval import common

common.set_env_guards()  # must run before any ``app`` import

import argparse  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any, Callable, Dict, List, Optional, Sequence  # noqa: E402

from scripts.eval import data_loading as dl  # noqa: E402
from scripts.eval import metrics as M  # noqa: E402
from scripts.eval.evaluate import project_match  # noqa: E402

SEED = 0
TOP_K = 10
SYNTHETIC_SIZES = (1000, 5000, 20000)
GAP_CAND = (5, 10, 20, 50)
GAP_REQ = (5, 10, 20)

ROWS: List[Dict[str, Any]] = []


def timeit(fn: Callable[[int], Any], repeats: int, warmup: int) -> List[float]:
    """Return per-run wall times in ms. ``fn`` receives the run index (warm-up runs use 0..warmup-1)."""
    for i in range(warmup):
        fn(i)
    out = []
    for i in range(repeats):
        t = time.perf_counter()
        fn(i)
        out.append((time.perf_counter() - t) * 1000.0)
    return out


def record(stage: str, case: str, values: Sequence[float], note: str = "") -> None:
    s = M.summarize_timings(values)
    ROWS.append({
        "stage": stage, "case": case, "status": "ok", "n": s["n"],
        "mean_ms": round(s["mean"], 3), "p50_ms": round(s["p50"], 3), "p95_ms": round(s["p95"], 3),
        "min_ms": round(s["min"], 3), "max_ms": round(s["max"], 3), "note": note,
    })


def skipped(stage: str, case: str, reason: str) -> None:
    ROWS.append({"stage": stage, "case": case, "status": "skipped", "n": "", "mean_ms": "", "p50_ms": "",
                 "p95_ms": "", "min_ms": "", "max_ms": "", "note": reason})


def ram_gb() -> Optional[float]:
    try:
        if os.name == "nt":
            import ctypes

            class MEM(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong), ("total", ctypes.c_ulonglong),
                            ("avail", ctypes.c_ulonglong), ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong), ("ave", ctypes.c_ulonglong)]

            st = MEM()
            st.l = ctypes.sizeof(MEM)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return round(st.total / 1024 ** 3, 1)
        return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024 ** 3, 1)
    except Exception:
        return None


def top_k_cosine(matrix, q, k: int = TOP_K):
    import numpy as np

    sims = matrix @ q
    k = min(k, len(sims))
    idx = np.argpartition(-sims, k - 1)[:k]
    return idx[np.argsort(-sims[idx])]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="data/eval/results", help="output directory")
    ap.add_argument("--repeats", type=int, default=30)
    ap.add_argument("--warmup", type=int, default=5)
    args = ap.parse_args(argv)
    out = Path(args.out)
    if not out.is_absolute():
        out = common.ROOT / out
    R, W = args.repeats, args.warmup

    import numpy as np

    config = common.base_config()
    config["ram_gb"] = ram_gb()
    config["repeats"], config["warmup"], config["seed"] = R, W, SEED
    probes = config["service_probes"]
    neo4j_up = probes["neo4j_7687"]["reachable"]
    pg_up = probes["postgres_5432"]["reachable"] or probes["postgres_55432"]["reachable"]

    # model cold load (once, reported separately); this must be the first load in the process
    t = time.perf_counter()
    try:
        from app.clients.sentence_transformer import get_sentence_transformer

        client = get_sentence_transformer()
    except Exception as exc:
        print(f"Model unavailable: {type(exc).__name__}: {exc}"[:300], file=sys.stderr)
        return 3
    cold_ms = (time.perf_counter() - t) * 1000.0
    import torch

    config["model"] = {"status": "ok", "model_name": client.model_name, "device": client.device,
                       "embedding_dim": client.embedding_dimension}
    config["torch_threads"] = torch.get_num_threads()
    config["model_cold_load_ms"] = round(cold_ms, 1)

    from app.schemas.skill_gap import SkillGapAnalysisRequest
    from app.services.semantic_search.text_embedding import build_job_text, normalize_text
    from app.services.skill_features import skill_matching as sm
    from app.services.skill_features.skill_gap_analysis import analyze_skill_gap_service

    cvs, jds = dl.load_cvs(), dl.load_jds()
    pairs = dl.load_pairs()
    skills = dl.load_skills_gold()
    cv_by_id = {c["cv_id"]: c for c in cvs}
    jd_by_id = {j["jd_id"]: j for j in jds}

    def cv_text_of(cv):
        p = dl.build_profile(cv)
        return normalize_text(p.CleanText) or normalize_text(p.RawText)

    def jd_text_of(jd):
        e = dl.build_jd(jd)
        return build_job_text(e) or normalize_text(e.CleanText) or normalize_text(e.RawText)

    cv_texts = [cv_text_of(c) for c in cvs]
    jd_texts = [jd_text_of(j) for j in jds]
    sample_cv, sample_jd = cv_texts[0], jd_texts[0]
    skill_pool = sorted({s for g in skills for s in g["skills"]})
    config["text_stats_chars"] = {"sample_cv": len(sample_cv), "sample_jd": len(sample_jd),
                                  "skill_pool": len(skill_pool)}

    # ---- (a) embedding
    record("embedding", "single skill (1 short string)", timeit(lambda i: client.encode(skill_pool[i % len(skill_pool)]), R, W))
    record("embedding", "CV text (1 document)", timeit(lambda i: client.encode(cv_texts[i % 10]), R, W),
           "cycles over 10 CVs; model truncates at its max sequence length")
    record("embedding", "JD text (1 document)", timeit(lambda i: client.encode(jd_texts[i % 10]), R, W),
           "cycles over 10 JDs")
    batch = [skill_pool[j % len(skill_pool)] for j in range(32)]
    record("embedding", "batch of 32 skills (encode_batch)", timeit(lambda i: client.encode_batch(batch), R, W))

    # ---- (b) vector search, in-memory numpy stand-in
    rng = np.random.default_rng(SEED)
    jd_mat = np.array(client.encode_batch(jd_texts), dtype=np.float32)
    cv_mat = np.array(client.encode_batch(cv_texts), dtype=np.float32)
    q = np.array(client.encode(sample_cv), dtype=np.float32)
    label = "in-memory numpy cosine top-10 (stand-in, NOT pgvector)"
    record("vector_search", f"N={len(jd_mat)} real JD embeddings", timeit(lambda i: top_k_cosine(jd_mat, q), R, W), label)
    record("vector_search", f"N={len(cv_mat)} real CV embeddings", timeit(lambda i: top_k_cosine(cv_mat, q), R, W), label)
    for n in SYNTHETIC_SIZES:
        mat = rng.standard_normal((n, jd_mat.shape[1])).astype(np.float32)
        mat /= np.linalg.norm(mat, axis=1, keepdims=True)
        record("vector_search", f"N={n} synthetic random unit vectors", timeit(lambda i: top_k_cosine(mat, q), R, W),
               label + "; synthetic vectors")
    why_pg = ("Postgres/pgvector not reachable on localhost (TCP probe)" if not pg_up else
              "Postgres reachable, but this script does not seed the DB, so no pgvector query was timed")
    skipped("vector_search", "pgvector ORDER BY cosine_distance (app/repositories/postgres/semantic_search.py)", why_pg)

    # ---- (c) matching: real calculate_cv_jd_matching, stub session, graph writes no-op
    sel = pairs[:10]
    ctx = []
    for p in sel:
        ctx.append((dl.build_profile(cv_by_id[p["cv_id"]]), dl.build_jd(jd_by_id[p["jd_id"]])))
    record("matching", f"calculate_cv_jd_matching ({len(ctx)} pairs, cycled)",
           timeit(lambda i: project_match(sm, *ctx[i % len(ctx)]), R, W),
           "stub DB session, graph writes patched to no-op; includes embedding of CV and JD text")

    # ---- (d) skill gap (service encodes every skill on every call, so there is no warm cache effect to separate)
    rnd = random.Random(SEED)
    for nc in GAP_CAND:
        for nr in GAP_REQ:
            cands = rnd.sample(skill_pool, nc)
            reqs = rnd.sample(skill_pool, nr)
            req = SkillGapAnalysisRequest(candidate_skills=cands, required_skills=reqs)
            record("skill_gap", f"{nc} candidate x {nr} required skills",
                   timeit(lambda i: analyze_skill_gap_service(None, req), R, W),
                   "analyze_skill_gap_service(db=None); skills sampled from gold lists")
    skipped("graph_query", "analyze_skill_gap_graph / hybrid graph match (Neo4j)",
            "Neo4j not reachable on localhost (TCP probe)" if not neo4j_up else
            "Neo4j reachable, but this script does not seed the graph, so no graph query was timed")

    # ---- (e) end-to-end: CV text -> encode -> top-10 JD (in-memory) -> match top 3 -> gap for top 1
    jd_entities = [dl.build_jd(j) for j in jds]
    e2e_cvs = [cv_by_id[p["cv_id"]] for p in sel]
    e2e_profiles = [dl.build_profile(c) for c in e2e_cvs]
    e2e_texts = [cv_text_of(c) for c in e2e_cvs]

    def e2e(i: int):
        k = i % len(e2e_cvs)
        v = np.array(client.encode(e2e_texts[k]), dtype=np.float32)
        top = top_k_cosine(jd_mat, v)
        for j in top[:3]:
            project_match(sm, e2e_profiles[k], jd_entities[int(j)])
        best = jd_entities[int(top[0])]
        cands = [s.SkillTitle for s in e2e_profiles[k].skills]
        reqs = [s.Title for s in best.skills]
        if reqs:
            analyze_skill_gap_service(None, SkillGapAnalysisRequest(candidate_skills=cands or None, required_skills=reqs))

    record("end_to_end", "CV -> encode -> top-10 of 69 JDs (in-memory) -> match top 3 -> gap top 1",
           timeit(e2e, R, W), "excludes DB and graph; vector search is the in-memory stand-in")

    result = {"config": config, "rows": ROWS}
    common.write_json(out / "latency_results.json", result)
    fields = ["stage", "case", "status", "n", "mean_ms", "p50_ms", "p95_ms", "min_ms", "max_ms", "note"]
    common.write_csv(out / "latency_summary.csv", ROWS, fields)
    md = build_md(config, ROWS)
    (out / "latency_summary.md").write_text(md, encoding="utf-8", newline="\n")
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(md)
    print(f"Wrote {out / 'latency_results.json'}, {out / 'latency_summary.csv'}, {out / 'latency_summary.md'}")
    return 0


def build_md(config: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    m = config["model"]
    g = config["git"]
    lines = [
        "# Latency benchmark", "",
        f"- Date (UTC): {config['date_utc']}",
        f"- Git commit: {g['commit']} (dirty={g['dirty']})",
        f"- OS: {config['os']}",
        f"- CPU: {config['cpu']} ({config['cpu_count']} logical), RAM: {config['ram_gb']} GB, torch threads: {config['torch_threads']}",
        f"- Python {config['versions']['python']}, torch {config['versions']['torch']}, "
        f"sentence-transformers {config['versions']['sentence_transformers']}, numpy {config['versions']['numpy']}",
        f"- Model: {m['model_name']} on {m['device']}, dim {m['embedding_dim']}; cold load {config['model_cold_load_ms']} ms (single measurement)",
        f"- Warm-up runs: {config['warmup']}, timed runs per case: {config['repeats']}; percentiles are nearest-rank; times in ms",
        "",
        "| stage | case | n | mean | p50 | p95 | min | max | note |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if r["status"] == "ok":
            lines.append(f"| {r['stage']} | {r['case']} | {r['n']} | {r['mean_ms']} | {r['p50_ms']} | {r['p95_ms']} | "
                         f"{r['min_ms']} | {r['max_ms']} | {r['note']} |")
        else:
            lines.append(f"| {r['stage']} | {r['case']} | skipped | | | | | | {r['note']} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
