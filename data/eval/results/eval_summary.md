# Evaluation summary (auto-generated; do not edit by hand)

> **Labels are AI-assigned (single annotator) and NOT human-verified.** n=40 pairs / 8 JDs / 34 CVs with gold skills, hand-picked (not random). Confidence intervals are wide. See `data/eval/ANNOTATION_GUIDELINE.md`.

## Run configuration

- Date (UTC): 2026-11-19T04:01:04+00:00
- Git commit: `2987a79011b81b37cbe0411d1cc425f2fe95f62b` (working tree dirty: True, 1 changed file(s))
- Model: `sentence-transformers/all-MiniLM-L6-v2`, device `cpu`, dim 384, status `ok`
- Versions: {'python': '3.11.8', 'numpy': '2.4.1', 'torch': '2.10.0+cpu', 'sentence_transformers': '5.2.2'}
- OS / CPU: Windows 10 (10.0.26300) / 11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz (8 logical)
- Thresholds: match is_suitable>=0.4, HIGHLY_SUITABLE>=0.7; gap match>=0.82, partial>=0.6; ranking k=3, nDCG@5
- Bootstrap: seed 0, 1000 resamples, 95% percentile CI (over docs/pairs/JDs as stated)
- Label files sha1: {'pairs.csv': '859221a1f857765b9cdd33db241fd071e8e6f338', 'skills_gold.jsonl': '1abc9185294f1650ac21fa0fc51e6cb673c0bea1', 'gap_gold.jsonl': '01904ac546c67d4f4fed9eaa9fe02b061c6fe217', 'ANNOTATION_GUIDELINE.md': '628cf249fdad6d29bde5b88c88894934460974a8'}

## Method status

| key | status | detail |
|---|---|---|
| extraction_cv/cv_rules | ok | app.dataset.CVs.transformation.main._build_profile |
| extraction_cv/dictionary | ok | regex over skill_matching.COMMON_EXTRACT_SKILLS |
| extraction_jd/jd_tags | ok | JobSkills field as stored (not an extractor) |
| extraction_jd/dictionary | ok | skill_matching.evaluate_smart_skill_matching fallback |
| matching/keyword | ok | share of JD JobSkills tags found as whole words in CV cleantext (0 if JD has no tags) |
| matching/vector_only | ok | cosine(encode(CV text), encode(build_job_text(JD))) with all-MiniLM-L6-v2, in memory |
| matching/project_match | ok | skill_matching.calculate_cv_jd_matching (stub session, graph writes no-op), match_score |
| matching/graph_hybrid | not_run | graph_service.calculate_cv_jd_matching_service / hybrid_match_cvs_for_job_graph: Neo4j/Postgres not reachable on localhost (TCP probe), so the graph/hybrid method was not run |
| matching/random_order | ok | expected metrics under uniformly random ranking |
| gap/keyword | ok | exact normalized equality |
| gap/vector_only@0.82 | ok | cosine >= match_threshold, no partial class |
| gap/vector_only@0.6 | ok | cosine >= partial_threshold, no partial class |
| gap/project_gap | ok | analyze_skill_gap_service (db=None) |
| gap/project_smart | ok | evaluate_smart_skill_matching (exact/substring + clusters) |
| gap/graph_neo4j | not_run | match_crud.analyze_skill_gap_graph: Neo4j not reachable on localhost (TCP probe), so the graph/hybrid method was not run |

## Skill extraction: CVs (34 docs)

| method | matching | micro P | micro R | micro F1 [CI] | macro P | macro R | macro F1 [CI] |
|---|---|---|---|---|---|---|---|
| cv_rules | exact | 0.228 | 0.085 | 0.124 [0.06, 0.20] | 0.116 | 0.072 | 0.082 [0.04, 0.13] |
| cv_rules | soft | 0.429 | 0.181 | 0.255 [0.17, 0.34] | 0.301 | 0.150 | 0.178 [0.12, 0.24] |
| dictionary | exact | 0.585 | 0.194 | 0.291 [0.24, 0.34] | 0.453 | 0.165 | 0.236 [0.18, 0.30] |
| dictionary | soft | 0.676 | 0.261 | 0.377 [0.31, 0.43] | 0.601 | 0.255 | 0.348 [0.27, 0.42] |

`cv_rules` output equals the stored `skilltitle` for 34/34 gold CVs (sanity check of the code path).

## Skill extraction: JDs (15 docs)

| method | matching | micro P | micro R | micro F1 [CI] | macro P | macro R | macro F1 [CI] |
|---|---|---|---|---|---|---|---|
| dictionary | exact | 0.577 | 0.192 | 0.288 [0.18, 0.38] | 0.408 | 0.173 | 0.240 [0.13, 0.36] |
| dictionary | soft | 0.612 | 0.220 | 0.323 [0.23, 0.42] | 0.442 | 0.197 | 0.268 [0.16, 0.38] |
| jd_tags | exact | 0.241 | 0.078 | 0.118 [0.05, 0.20] | 0.294 | 0.075 | 0.119 [0.06, 0.19] |
| jd_tags | soft | 0.349 | 0.133 | 0.193 [0.13, 0.27] | 0.407 | 0.123 | 0.184 [0.11, 0.26] |

`jd_tags` is the crawler's `JobSkills` field passed through, not an extractor. Some JDs have unrelated or empty tags (see guideline).

## Matching: classification (relevance as ground truth)

| method | positive | ROC AUC [CI] | project default P / R / F1 | best-F1 (in-sample, optimistic) P / R / F1 [CI] |
|---|---|---|---|---|
| keyword | rel>=1 | 0.724 [0.63, 0.82] | - | 0.725 / 1.000 / 0.841 [0.73, 0.92] (t=0.0000) |
| keyword | rel>=2 | 0.620 [0.45, 0.80] | - | 0.325 / 1.000 / 0.491 [0.30, 0.64] (t=0.0000) |
| vector_only | rel>=1 | 0.511 [0.27, 0.72] | - | 0.725 / 1.000 / 0.841 [0.73, 0.92] (t=-0.0318) |
| vector_only | rel>=2 | 0.672 [0.51, 0.84] | - | 0.522 / 0.923 / 0.667 [0.46, 0.83] (t=0.4055) |
| project_match | rel>=1 | 0.614 [0.43, 0.78] | 1.000 / 0.138 / 0.242 [0.06, 0.43] | 0.725 / 1.000 / 0.841 [0.73, 0.92] (t=0.0000) |
| project_match | rel>=2 | 0.679 [0.49, 0.85] | 0.500 / 0.077 / 0.133 [0.00, 0.36] | 0.500 / 0.769 / 0.606 [0.37, 0.79] (t=0.1121) |
| always_positive (reference) | rel>=1 | - | F1 0.841 (precision=0.7250, recall=1.0 (reference)) | - |
| always_positive (reference) | rel>=2 | - | F1 0.491 (precision=0.3250, recall=1.0 (reference)) | - |

Project default thresholds: `match_score >= 0.40` against rel>=1, `>= 0.70` against rel>=2.

## Matching: ranking within each JD (5 CVs per JD, mean over 8 JDs)

| method | P@1 | P@3 | MRR | nDCG@5 |
|---|---|---|---|---|
| keyword | 0.750 [0.50, 1.00] | 0.708 [0.58, 0.83] | 0.854 [0.67, 1.00] | 0.828 [0.73, 0.92] |
| vector_only | 0.875 [0.62, 1.00] | 0.750 [0.58, 0.92] | 0.938 [0.81, 1.00] | 0.859 [0.80, 0.92] |
| project_match | 0.875 [0.62, 1.00] | 0.750 [0.58, 0.92] | 0.938 [0.81, 1.00] | 0.858 [0.79, 0.92] |
| random_order | 0.725 [0.65, 0.80] | 0.725 [0.65, 0.80] | 0.856 [0.81, 0.90] | 0.817 [0.79, 0.84] |

Ties are broken pessimistically (lower relevance first). `random_order` is the exact expectation over all orderings.

Split by JD language (mean over JDs, no CI): see `eval_metrics.csv` rows with stratum `jd_lang=en|vi`.

## Skill gap (micro P / R / F1 vs gap_gold; exact name equality on JD gold skill names)

### Setting `gold_inputs` (gold CV skills vs gold JD skills)

| method | class | P | R | F1 [CI] | macro F1 |
|---|---|---|---|---|---|
| keyword | matched | 1.000 | 0.965 | 0.982 [0.96, 1.00] | 0.989 |
| keyword | missing | 0.897 | 1.000 | 0.946 [0.92, 0.97] | 0.838 |
| keyword | covered | 1.000 | 0.643 | 0.783 [0.72, 0.84] | 0.786 |
| project_gap | matched | 0.991 | 0.974 | 0.982 [0.96, 1.00] | 0.990 |
| project_gap | partial | 0.308 | 0.210 | 0.250 [0.15, 0.34] | 0.343 |
| project_gap | missing | 0.917 | 0.951 | 0.934 [0.91, 0.95] | 0.809 |
| project_gap | covered | 0.828 | 0.731 | 0.776 [0.72, 0.82] | 0.721 |
| project_smart | matched | 0.681 | 0.974 | 0.801 [0.72, 0.89] | 0.806 |
| project_smart | partial | 0.545 | 0.105 | 0.176 [0.07, 0.29] | 0.452 |
| project_smart | missing | 0.915 | 0.910 | 0.913 [0.88, 0.94] | 0.808 |
| project_smart | covered | 0.724 | 0.737 | 0.730 [0.66, 0.79] | 0.720 |
| vector_only@0.6 | matched | 0.742 | 0.983 | 0.845 [0.80, 0.89] | 0.776 |
| vector_only@0.6 | missing | 0.917 | 0.951 | 0.934 [0.91, 0.95] | 0.809 |
| vector_only@0.6 | covered | 0.828 | 0.731 | 0.776 [0.72, 0.82] | 0.721 |
| vector_only@0.82 | matched | 0.991 | 0.974 | 0.982 [0.96, 1.00] | 0.990 |
| vector_only@0.82 | missing | 0.900 | 1.000 | 0.948 [0.92, 0.97] | 0.841 |
| vector_only@0.82 | covered | 1.000 | 0.655 | 0.791 [0.72, 0.84] | 0.789 |

### Setting `pipeline_cv_skills` (CV skills from the project's CV extraction vs gold JD skills)

| method | class | P | R | F1 [CI] | macro F1 |
|---|---|---|---|---|---|
| keyword | matched | 1.000 | 0.123 | 0.219 [0.08, 0.34] | 0.424 |
| keyword | missing | 0.773 | 1.000 | 0.872 [0.82, 0.91] | 0.770 |
| keyword | covered | 1.000 | 0.082 | 0.151 [0.05, 0.24] | 0.335 |
| project_gap | matched | 1.000 | 0.149 | 0.260 [0.11, 0.38] | 0.443 |
| project_gap | partial | 0.091 | 0.018 | 0.029 [0.00, 0.10] | 0.388 |
| project_gap | missing | 0.786 | 0.996 | 0.879 [0.83, 0.92] | 0.777 |
| project_gap | covered | 0.929 | 0.152 | 0.261 [0.14, 0.36] | 0.391 |
| project_smart | matched | 0.738 | 0.272 | 0.397 [0.25, 0.50] | 0.499 |
| project_smart | partial | 0.333 | 0.018 | 0.033 [0.00, 0.10] | 0.360 |
| project_smart | missing | 0.794 | 0.981 | 0.878 [0.82, 0.92] | 0.777 |
| project_smart | covered | 0.778 | 0.205 | 0.324 [0.20, 0.42] | 0.420 |
| vector_only@0.6 | matched | 0.893 | 0.219 | 0.352 [0.19, 0.47] | 0.484 |
| vector_only@0.6 | missing | 0.786 | 0.996 | 0.879 [0.83, 0.92] | 0.777 |
| vector_only@0.6 | covered | 0.929 | 0.152 | 0.261 [0.14, 0.36] | 0.391 |
| vector_only@0.82 | matched | 1.000 | 0.149 | 0.260 [0.11, 0.38] | 0.443 |
| vector_only@0.82 | missing | 0.776 | 1.000 | 0.874 [0.82, 0.91] | 0.772 |
| vector_only@0.82 | covered | 1.000 | 0.099 | 0.181 [0.07, 0.27] | 0.350 |

Gold class sizes over 40 pairs: {'matched': 114, 'partial': 57, 'missing': 534}. `covered` = matched or partial. Macro averages count pairs where both sets are empty as 1.0, so prefer micro.

## Not run

- `matching/graph_hybrid`: not_run. graph_service.calculate_cv_jd_matching_service / hybrid_match_cvs_for_job_graph: Neo4j/Postgres not reachable on localhost (TCP probe), so the graph/hybrid method was not run
- `gap/graph_neo4j`: not_run. match_crud.analyze_skill_gap_graph: Neo4j not reachable on localhost (TCP probe), so the graph/hybrid method was not run

## Caveats

- Labels: one AI annotator, no human verification, no inter-annotator agreement.
- 40 pairs, 8 JDs; hand-picked CVs (mostly IT roles). Best-F1 thresholds are tuned on the same pairs (optimistic).
- Project thresholds (match 0.70/0.40, gap 0.82/0.60) were not calibrated for all-MiniLM-L6-v2 on this data.
- `project_match` ran with a stub DB session and no-op graph writes; its vector part is the real model. Postgres/pgvector and Neo4j were not used.
- Several JDs have noisy/empty `JobSkills` tags, which hurts the keyword baseline and the project's tag-based skill score.
- `gold_inputs` gap scores are optimistic for name-based methods: the same annotator wrote both skill lists in one canonical naming, so exact names mostly line up. The `partial` class is the informative one.
- Class balance matters: at rel>=1 an always-positive predictor reaches F1 0.841 (precision=0.7250, recall=1.0 (reference)); compare methods against that row.
- all-MiniLM-L6-v2 truncates input at 256 word pieces; long CVs are embedded from their beginning only.
- vector_only equals project semantic similarity (max abs diff 5e-05).
