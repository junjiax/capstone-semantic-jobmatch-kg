"""Pure-Python evaluation metrics (standard library only).

Conventions (apply everywhere in this module):

* Precision/recall/F1 on sets: P = TP / |predicted|, R = TP / |gold|,
  F1 = 2PR / (P + R). If P + R == 0 then F1 = 0.
* Empty sets: if both predicted and gold are empty, P = R = F1 = 1.0 (nothing to
  find, nothing wrongly found). If only one of them is empty, P = R = F1 = 0.0.
  (No predictions -> P = 0; no gold -> R = 0; consistent with the plan.)
* Ranking metrics take relevance grades in ranked order (best-ranked first).
  ``precision_at_k`` divides by ``k`` (not by the number of items returned).
  ``ndcg_at_k`` uses linear gain (gain = grade) and log2(rank + 1) discount;
  it returns 0.0 when the ideal DCG is 0 (no relevant item).
  ``reciprocal_rank`` returns 0.0 when no relevant item exists.
* ``roc_auc`` is the Mann-Whitney statistic with ties counted as 0.5; it returns
  ``None`` when only one class is present.
* ``percentile`` is nearest-rank: the value at 1-based rank ceil(p/100 * n).
"""
from __future__ import annotations

import math
import random
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

def normalize_skill(text: str) -> str:
    """Lowercase, trim, collapse whitespace, strip surrounding punctuation."""
    t = re.sub(r"\s+", " ", (text or "").lower()).strip()
    # keep leading '.' (".net") and trailing '+'/'#' ("c++", "c#")
    t = t.strip(" \t\r\n,;:!?\"'`()[]{}<>/\\|-_*")
    if t.endswith(".") and not t.endswith(".."):
        t = t[:-1].rstrip()
    return t


def soft_match(a: str, b: str) -> bool:
    """True if one normalized string occurs inside the other as a whole-word sequence."""
    na, nb = normalize_skill(a), normalize_skill(b)
    if not na or not nb:
        return False
    if na == nb:
        return True

    def contains(needle: str, hay: str) -> bool:
        return re.search(r"(?<![\w+#])" + re.escape(needle) + r"(?![\w+#])", hay) is not None

    return contains(na, nb) or contains(nb, na)


def f1_from_pr(p: float, r: float) -> float:
    return 0.0 if (p + r) == 0 else 2 * p * r / (p + r)


def binary_prf(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """P/R/F1 from confusion counts. tp+fp == 0 gives P = 0; tp+fn == 0 gives R = 0."""
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return {"precision": p, "recall": r, "f1": f1_from_pr(p, r)}


def set_counts(pred: Iterable[str], gold: Iterable[str], mode: str = "exact") -> Tuple[int, int, int, int]:
    """Return (n_pred, n_gold, pred_hits, gold_hits) after normalization and de-duplication.

    ``exact``: normalized equality (pred_hits == gold_hits == |intersection|).
    ``soft`` : a predicted item is a hit if it soft-matches any gold item; a gold item
               is a hit if it soft-matches any predicted item.
    """
    if mode not in ("exact", "soft"):
        raise ValueError(f"unknown mode: {mode}")
    p = sorted({normalize_skill(x) for x in pred if normalize_skill(x)})
    g = sorted({normalize_skill(x) for x in gold if normalize_skill(x)})
    if mode == "exact":
        inter = len(set(p) & set(g))
        return len(p), len(g), inter, inter
    pred_hits = sum(1 for x in p if any(soft_match(x, y) for y in g))
    gold_hits = sum(1 for y in g if any(soft_match(x, y) for x in p))
    return len(p), len(g), pred_hits, gold_hits


def _prf_from_counts(n_pred: int, n_gold: int, pred_hits: int, gold_hits: int) -> Dict[str, float]:
    if n_pred == 0 and n_gold == 0:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    p = pred_hits / n_pred if n_pred else 0.0
    r = gold_hits / n_gold if n_gold else 0.0
    return {"precision": p, "recall": r, "f1": f1_from_pr(p, r)}


def set_prf(pred: Iterable[str], gold: Iterable[str], mode: str = "exact") -> Dict[str, float]:
    n_pred, n_gold, ph, gh = set_counts(pred, gold, mode)
    out = _prf_from_counts(n_pred, n_gold, ph, gh)
    out.update({"n_pred": n_pred, "n_gold": n_gold, "pred_hits": ph, "gold_hits": gh})
    return out


def micro_macro_prf(
    items: Sequence[Tuple[Iterable[str], Iterable[str]]], mode: str = "exact"
) -> Dict[str, Dict[str, float]]:
    """Micro (pooled counts) and macro (mean of per-item P, R, F1) over (pred, gold) items."""
    if not items:
        raise ValueError("items must not be empty")
    per = [set_prf(p, g, mode) for p, g in items]
    sp = sum(x["n_pred"] for x in per)
    sg = sum(x["n_gold"] for x in per)
    sph = sum(x["pred_hits"] for x in per)
    sgh = sum(x["gold_hits"] for x in per)
    micro = _prf_from_counts(sp, sg, sph, sgh)
    n = len(per)
    macro = {k: sum(x[k] for x in per) / n for k in ("precision", "recall", "f1")}
    return {"micro": micro, "macro": macro, "n_items": n}


def confusion_at_threshold(scores: Sequence[float], labels: Sequence[int], threshold: float) -> Dict[str, int]:
    """Predict positive when score >= threshold; labels are 0/1."""
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length")
    tp = fp = tn = fn = 0
    for s, y in zip(scores, labels):
        pos = s >= threshold
        if pos and y:
            tp += 1
        elif pos and not y:
            fp += 1
        elif not pos and y:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def classification_at_threshold(scores: Sequence[float], labels: Sequence[int], threshold: float) -> Dict[str, float]:
    c = confusion_at_threshold(scores, labels, threshold)
    out: Dict[str, float] = dict(binary_prf(c["tp"], c["fp"], c["fn"]))
    out["accuracy"] = (c["tp"] + c["tn"]) / max(1, len(scores))
    out.update(c)
    out["threshold"] = threshold
    return out


def threshold_sweep(
    scores: Sequence[float], labels: Sequence[int], thresholds: Optional[Sequence[float]] = None
) -> List[Dict[str, float]]:
    """Classification metrics at each threshold (default: every distinct score)."""
    if thresholds is None:
        thresholds = sorted(set(scores))
    return [classification_at_threshold(scores, labels, t) for t in thresholds]


def best_f1(sweep: Sequence[Dict[str, float]]) -> Dict[str, float]:
    """Row with the highest F1 (ties: the highest threshold)."""
    return max(sweep, key=lambda r: (r["f1"], r["threshold"]))


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> Optional[float]:
    pos = [s for s, y in zip(scores, labels) if y]
    neg = [s for s, y in zip(scores, labels) if not y]
    if not pos or not neg:
        return None
    wins = 0.0
    for sp in pos:
        for sn in neg:
            if sp > sn:
                wins += 1.0
            elif sp == sn:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def precision_at_k(rels: Sequence[float], k: int, min_rel: float = 1) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return sum(1 for r in rels[:k] if r >= min_rel) / k


def reciprocal_rank(rels: Sequence[float], min_rel: float = 1) -> float:
    for i, r in enumerate(rels, 1):
        if r >= min_rel:
            return 1.0 / i
    return 0.0


def dcg_at_k(rels: Sequence[float], k: int) -> float:
    return sum(r / math.log2(i + 1) for i, r in enumerate(rels[:k], 1))


def ndcg_at_k(rels: Sequence[float], k: int) -> float:
    ideal = dcg_at_k(sorted(rels, reverse=True), k)
    return 0.0 if ideal == 0 else dcg_at_k(rels, k) / ideal


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("mean of empty sequence")
    return sum(values) / len(values)


def bootstrap_stat(
    items: Sequence, stat, seed: int = 0, n_resamples: int = 1000, alpha: float = 0.05
) -> Tuple[float, float]:
    """Percentile bootstrap CI of ``stat(resampled_items)`` (deterministic for a seed).

    Resamples with replacement; resamples where ``stat`` returns None are skipped
    (e.g. an AUC resample with a single class). Raises if every resample is skipped.
    """
    if not items:
        raise ValueError("items must not be empty")
    rng = random.Random(seed)
    n = len(items)
    stats = []
    for _ in range(n_resamples):
        v = stat([items[rng.randrange(n)] for _ in range(n)])
        if v is not None:
            stats.append(v)
    if not stats:
        raise ValueError("statistic undefined on every resample")
    stats.sort()
    k = len(stats)
    lo = stats[int((alpha / 2) * k)]
    hi = stats[min(k - 1, int((1 - alpha / 2) * k))]
    return lo, hi


def bootstrap_ci(
    values: Sequence[float], seed: int = 0, n_resamples: int = 1000, alpha: float = 0.05
) -> Tuple[float, float]:
    """Percentile bootstrap CI of the mean (deterministic for a given seed)."""
    if not values:
        raise ValueError("values must not be empty")
    return bootstrap_stat(values, mean, seed, n_resamples, alpha)


def percentile(values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile, 0 < p <= 100 (p = 0 returns the minimum)."""
    if not values:
        raise ValueError("percentile of empty sequence")
    if not 0 <= p <= 100:
        raise ValueError("p must be in [0, 100]")
    s = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(s)))
    return s[rank - 1]
