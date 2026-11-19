# Latency benchmark

- Date (UTC): 2026-11-19T04:02:08+00:00
- Git commit: 2987a79011b81b37cbe0411d1cc425f2fe95f62b (dirty=True)
- OS: Windows 10 (10.0.26300)
- CPU: 11th Gen Intel(R) Core(TM) i5-11300H @ 3.10GHz (8 logical), RAM: 15.8 GB, torch threads: 4
- Python 3.11.8, torch 2.10.0+cpu, sentence-transformers 5.2.2, numpy 2.4.1
- Model: sentence-transformers/all-MiniLM-L6-v2 on cpu, dim 384; cold load 400.1 ms (single measurement)
- Warm-up runs: 5, timed runs per case: 30; percentiles are nearest-rank; times in ms

| stage | case | n | mean | p50 | p95 | min | max | note |
|---|---|---|---|---|---|---|---|---|
| embedding | single skill (1 short string) | 30 | 8.709 | 8.561 | 9.981 | 7.116 | 11.348 |  |
| embedding | CV text (1 document) | 30 | 47.911 | 47.567 | 55.076 | 41.195 | 55.171 | cycles over 10 CVs; model truncates at its max sequence length |
| embedding | JD text (1 document) | 30 | 43.281 | 44.157 | 56.608 | 31.597 | 60.102 | cycles over 10 JDs |
| embedding | batch of 32 skills (encode_batch) | 30 | 42.43 | 42.653 | 46.265 | 37.75 | 46.419 |  |
| vector_search | N=69 real JD embeddings | 30 | 0.014 | 0.014 | 0.014 | 0.013 | 0.018 | in-memory numpy cosine top-10 (stand-in, NOT pgvector) |
| vector_search | N=300 real CV embeddings | 30 | 0.022 | 0.021 | 0.023 | 0.021 | 0.032 | in-memory numpy cosine top-10 (stand-in, NOT pgvector) |
| vector_search | N=1000 synthetic random unit vectors | 30 | 0.052 | 0.045 | 0.102 | 0.044 | 0.162 | in-memory numpy cosine top-10 (stand-in, NOT pgvector); synthetic vectors |
| vector_search | N=5000 synthetic random unit vectors | 30 | 0.269 | 0.19 | 0.48 | 0.16 | 1.658 | in-memory numpy cosine top-10 (stand-in, NOT pgvector); synthetic vectors |
| vector_search | N=20000 synthetic random unit vectors | 30 | 1.202 | 0.997 | 2.31 | 0.847 | 2.321 | in-memory numpy cosine top-10 (stand-in, NOT pgvector); synthetic vectors |
| vector_search | pgvector ORDER BY cosine_distance (app/repositories/postgres/semantic_search.py) | skipped | | | | | | Postgres/pgvector not reachable on localhost (TCP probe) |
| matching | calculate_cv_jd_matching (10 pairs, cycled) | 30 | 88.133 | 86.546 | 104.097 | 74.836 | 105.509 | stub DB session, graph writes patched to no-op; includes embedding of CV and JD text |
| skill_gap | 5 candidate x 5 required skills | 30 | 98.556 | 94.809 | 114.872 | 88.723 | 125.551 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 5 candidate x 10 required skills | 30 | 140.232 | 138.897 | 154.15 | 132.062 | 159.648 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 5 candidate x 20 required skills | 30 | 246.804 | 234.516 | 311.919 | 224.549 | 374.255 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 10 candidate x 5 required skills | 30 | 153.17 | 152.759 | 169.669 | 135.053 | 178.914 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 10 candidate x 10 required skills | 30 | 214.162 | 214.99 | 241.179 | 183.783 | 245.966 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 10 candidate x 20 required skills | 30 | 299.431 | 294.845 | 342.496 | 280.52 | 343.628 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 20 candidate x 5 required skills | 30 | 255.78 | 231.83 | 376.126 | 224.023 | 563.451 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 20 candidate x 10 required skills | 30 | 287.774 | 286.004 | 297.845 | 273.777 | 302.188 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 20 candidate x 20 required skills | 30 | 402.148 | 401.673 | 425.352 | 389.017 | 425.547 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 50 candidate x 5 required skills | 30 | 510.306 | 507.253 | 535.459 | 492.041 | 581.81 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 50 candidate x 10 required skills | 30 | 577.237 | 575.19 | 598.466 | 565.72 | 604.449 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| skill_gap | 50 candidate x 20 required skills | 30 | 731.264 | 721.877 | 769.177 | 694.207 | 927.164 | analyze_skill_gap_service(db=None); skills sampled from gold lists |
| graph_query | analyze_skill_gap_graph / hybrid graph match (Neo4j) | skipped | | | | | | Neo4j not reachable on localhost (TCP probe) |
| end_to_end | CV -> encode -> top-10 of 69 JDs (in-memory) -> match top 3 -> gap top 1 | 30 | 584.579 | 523.357 | 913.378 | 391.748 | 1203.447 | excludes DB and graph; vector search is the in-memory stand-in |
