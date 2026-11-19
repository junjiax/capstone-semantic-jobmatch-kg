"""Metric functions checked against hand-computed values (no model, no services)."""
import math

import pytest

from scripts.eval import metrics as m


# ---------- normalization / soft matching ----------
def test_normalize_skill():
    assert m.normalize_skill("  Python. ") == "python"
    assert m.normalize_skill("Machine   Learning") == "machine learning"
    assert m.normalize_skill("(Docker)") == "docker"
    assert m.normalize_skill("C++") == "c++"
    assert m.normalize_skill(".NET") == ".net"


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("react", "react native", True),
        ("sql", "SQL Server", True),
        ("c", "c++", False),
        ("c", "c#", False),
        ("java", "javascript", False),
        ("react", "reactjs", False),
        ("python", "python", True),
        ("", "python", False),
    ],
)
def test_soft_match(a, b, expected):
    assert m.soft_match(a, b) is expected


# ---------- set precision / recall / F1 ----------
def test_set_prf_two_thirds():
    # pred {a,b,c}, gold {a,b,d}: TP=2 -> P=2/3, R=2/3, F1=2/3
    r = m.set_prf({"a", "b", "c"}, {"a", "b", "d"})
    assert r["precision"] == pytest.approx(2 / 3)
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["f1"] == pytest.approx(2 / 3)


def test_set_prf_normalizes_and_dedups():
    r = m.set_prf(["Python", "python ", "Docker."], ["docker", "python"])
    assert (r["precision"], r["recall"], r["f1"]) == (1.0, 1.0, 1.0)
    assert r["n_pred"] == 2


def test_set_prf_unequal_sizes():
    # pred {a}, gold {a,b,c,d}: P=1, R=1/4, F1 = 2*1*0.25/1.25 = 0.4
    r = m.set_prf({"a"}, {"a", "b", "c", "d"})
    assert r["precision"] == 1.0
    assert r["recall"] == 0.25
    assert r["f1"] == pytest.approx(0.4)


def test_set_prf_empty_conventions():
    assert m.set_prf([], [])["f1"] == 1.0
    r = m.set_prf([], ["a"])
    assert (r["precision"], r["recall"], r["f1"]) == (0.0, 0.0, 0.0)
    r = m.set_prf(["a"], [])
    assert (r["precision"], r["recall"], r["f1"]) == (0.0, 0.0, 0.0)


def test_set_prf_disjoint_is_zero():
    assert m.set_prf({"a"}, {"b"})["f1"] == 0.0


def test_set_prf_soft_mode():
    # pred {react native, python}, gold {react, python, docker}
    # pred hits: both (react native ~ react, python) -> P = 2/2
    # gold hits: react, python -> R = 2/3 ; F1 = 2*1*(2/3)/(5/3) = 0.8
    r = m.set_prf({"react native", "python"}, {"react", "python", "docker"}, mode="soft")
    assert r["precision"] == 1.0
    assert r["recall"] == pytest.approx(2 / 3)
    assert r["f1"] == pytest.approx(0.8)
    exact = m.set_prf({"react native", "python"}, {"react", "python", "docker"}, mode="exact")
    assert exact["precision"] == 0.5  # only python is an exact hit


def test_set_prf_unknown_mode():
    with pytest.raises(ValueError):
        m.set_prf({"a"}, {"a"}, mode="fuzzy")


def test_micro_vs_macro_differ_on_uneven_items():
    # item1: pred {a,b}  gold {a,b}          -> P=R=F1=1
    # item2: pred {c}    gold {d,e,f,g}      -> P=R=F1=0
    # micro: pred=3 hits=2 gold=6 hits=2     -> P=2/3, R=1/3, F1=2*(2/9)/1 = 4/9
    # macro: P=R=F1=0.5
    out = m.micro_macro_prf([({"a", "b"}, {"a", "b"}), ({"c"}, {"d", "e", "f", "g"})])
    assert out["micro"]["precision"] == pytest.approx(2 / 3)
    assert out["micro"]["recall"] == pytest.approx(1 / 3)
    assert out["micro"]["f1"] == pytest.approx(4 / 9)
    assert out["macro"] == pytest.approx({"precision": 0.5, "recall": 0.5, "f1": 0.5})
    assert out["n_items"] == 2


def test_micro_macro_requires_items():
    with pytest.raises(ValueError):
        m.micro_macro_prf([])


# ---------- binary classification ----------
def test_binary_prf_from_counts():
    # TP=3 FP=1 FN=2: P=3/4, R=3/5, F1 = 2*0.75*0.6/1.35 = 2/3
    r = m.binary_prf(3, 1, 2)
    assert r["precision"] == pytest.approx(0.75)
    assert r["recall"] == pytest.approx(0.6)
    assert r["f1"] == pytest.approx(2 / 3)


def test_binary_prf_zero_division():
    assert m.binary_prf(0, 0, 0) == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert m.binary_prf(0, 2, 0)["precision"] == 0.0


def test_confusion_at_threshold_boundary_is_positive():
    scores, labels = [0.9, 0.8, 0.4, 0.3], [1, 0, 1, 0]
    assert m.confusion_at_threshold(scores, labels, 0.5) == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    # score == threshold counts as positive
    assert m.confusion_at_threshold(scores, labels, 0.4)["tp"] == 2


def test_confusion_length_mismatch():
    with pytest.raises(ValueError):
        m.confusion_at_threshold([0.1], [1, 0], 0.5)


def test_threshold_sweep_and_best_f1():
    scores, labels = [0.9, 0.8, 0.4, 0.3], [1, 0, 1, 0]
    sweep = m.threshold_sweep(scores, labels, [0.3, 0.5, 0.85])
    # t=0.3: TP=2 FP=2 -> P=.5 R=1 F1=2/3 ; t=0.5: TP=1 FP=1 FN=1 -> F1=.5 ; t=0.85: TP=1 FN=1 -> P=1 R=.5 F1=2/3
    assert [round(r["f1"], 4) for r in sweep] == [0.6667, 0.5, 0.6667]
    assert m.best_f1(sweep)["threshold"] == 0.85  # tie -> highest threshold
    assert sweep[0]["accuracy"] == 0.5


# ---------- ROC AUC ----------
def test_roc_auc_one_inversion():
    # pos {0.9, 0.7}, neg {0.8, 0.6}: wins (0.9>0.8)(0.9>0.6)(0.7>0.6) = 3 of 4 -> 0.75
    assert m.roc_auc([0.9, 0.8, 0.7, 0.6], [1, 0, 1, 0]) == 0.75


def test_roc_auc_perfect_worst_ties_single_class():
    assert m.roc_auc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]) == 1.0
    assert m.roc_auc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]) == 0.0
    assert m.roc_auc([0.5, 0.5], [1, 0]) == 0.5
    assert m.roc_auc([0.5, 0.6], [1, 1]) is None


# ---------- ranking ----------
def test_precision_at_k():
    rels = [2, 0, 1, 0, 1]
    assert m.precision_at_k(rels, 3) == pytest.approx(2 / 3)  # positions 1 and 3 are relevant
    assert m.precision_at_k(rels, 5) == pytest.approx(3 / 5)
    assert m.precision_at_k(rels, 3, min_rel=2) == pytest.approx(1 / 3)
    assert m.precision_at_k([1], 3) == pytest.approx(1 / 3)  # divides by k, not by len
    with pytest.raises(ValueError):
        m.precision_at_k(rels, 0)


def test_reciprocal_rank():
    assert m.reciprocal_rank([0, 1, 2]) == 0.5
    assert m.reciprocal_rank([1, 0]) == 1.0
    assert m.reciprocal_rank([0, 0, 0]) == 0.0
    assert m.reciprocal_rank([0, 1, 2], min_rel=2) == pytest.approx(1 / 3)


def test_ndcg_hand_computed():
    # rels [2,0,1], k=3: DCG = 2/log2(2) + 0/log2(3) + 1/log2(4) = 2 + 0.5 = 2.5
    # ideal [2,1,0]: 2 + 1/log2(3) ; nDCG = 2.5 / (2 + 1/log2(3)) ~= 0.9502
    expected = 2.5 / (2 + 1 / math.log2(3))
    assert m.dcg_at_k([2, 0, 1], 3) == pytest.approx(2.5)
    assert m.ndcg_at_k([2, 0, 1], 3) == pytest.approx(expected)
    assert m.ndcg_at_k([2, 0, 1], 3) == pytest.approx(0.9502, abs=1e-4)


def test_ndcg_edges():
    assert m.ndcg_at_k([2, 1, 0], 3) == 1.0  # already ideal
    assert m.ndcg_at_k([0, 0, 0], 3) == 0.0  # no relevant item
    # k=1 on [0,2]: DCG@1 = 0, ideal@1 = 2
    assert m.ndcg_at_k([0, 2], 1) == 0.0
    # worst order [0,1,2], k=3: DCG = 0 + 1/log2(3) + 2/2 = 1.63093 ; ideal 2.63093
    assert m.ndcg_at_k([0, 1, 2], 3) == pytest.approx((1 / math.log2(3) + 1) / (2 + 1 / math.log2(3)))


# ---------- aggregates ----------
def test_mean():
    assert m.mean([1, 2, 3, 4]) == 2.5
    with pytest.raises(ValueError):
        m.mean([])


def test_bootstrap_ci_is_deterministic_and_contains_mean():
    vals = [1.0, 2.0, 3.0, 4.0, 5.0]
    a = m.bootstrap_ci(vals, seed=0, n_resamples=500)
    b = m.bootstrap_ci(vals, seed=0, n_resamples=500)
    assert a == b
    assert a[0] <= 3.0 <= a[1]
    assert 1.0 <= a[0] and a[1] <= 5.0
    assert m.bootstrap_ci([0.7] * 6, seed=0, n_resamples=50) == (pytest.approx(0.7), pytest.approx(0.7))


def test_bootstrap_stat_skips_undefined_resamples_and_is_deterministic():
    items = [(0.9, 1), (0.8, 0), (0.7, 1), (0.6, 0)]

    def auc(sample):
        return m.roc_auc([s for s, _ in sample], [y for _, y in sample])

    lo, hi = m.bootstrap_stat(items, auc, seed=0, n_resamples=200)
    assert 0.0 <= lo <= 0.75 <= hi <= 1.0  # point estimate 0.75 lies inside
    assert (lo, hi) == m.bootstrap_stat(items, auc, seed=0, n_resamples=200)
    with pytest.raises(ValueError):
        m.bootstrap_stat([(0.5, 1)], auc, seed=0, n_resamples=10)  # single class everywhere


# ---------- percentile (nearest rank) ----------
def test_percentile_nearest_rank_textbook_values():
    data = [15, 20, 35, 40, 50]
    assert m.percentile(data, 30) == 20  # ceil(0.30*5)=2 -> 2nd value
    assert m.percentile(data, 40) == 20  # ceil(2.0)=2
    assert m.percentile(data, 50) == 35  # ceil(2.5)=3
    assert m.percentile(data, 100) == 50
    assert m.percentile(data, 0) == 15


def test_percentile_p95_and_unsorted_input():
    assert m.percentile(list(range(20, 0, -1)), 95) == 19  # ceil(0.95*20)=19 -> value 19
    assert m.percentile([4, 1, 3, 2], 50) == 2  # ceil(2.0)=2
    assert m.percentile([7], 99) == 7


def test_percentile_errors():
    with pytest.raises(ValueError):
        m.percentile([], 50)
    with pytest.raises(ValueError):
        m.percentile([1], 101)
