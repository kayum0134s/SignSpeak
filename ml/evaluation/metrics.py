"""
Evaluation Metrics for Sign Language Recognition and Translation.
Implements:
- Task A: Top-1 Accuracy, Top-K, Macro Precision, Macro Recall, F1, Confusion Matrix.
- Task B: Word Error Rate (WER) using Levenshtein distance on gloss sequences.
- Task C: Translation BLEU (1-4 n-gram with brevity penalty) and chrF character n-gram metric.
- Runtime: Latency (ms), throughput (samples/sec).
"""

from collections import Counter
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np


def compute_isolated_metrics(
    y_true: List[str],
    y_pred: List[str],
    all_classes: List[str]
) -> Dict[str, Any]:
    """
    Computes top-1 accuracy, macro precision, recall, F1, and confusion matrix.
    """
    if not y_true or not y_pred:
        return {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "confusion_matrix": [],
            "classes": all_classes,
            "sample_count": 0
        }

    total = len(y_true)
    correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
    accuracy = correct / total if total > 0 else 0.0

    class_to_idx = {c: i for i, c in enumerate(all_classes)}
    num_classes = len(all_classes)
    conf_matrix = np.zeros((num_classes, num_classes), dtype=int)

    for yt, yp in zip(y_true, y_pred):
        if yt in class_to_idx and yp in class_to_idx:
            conf_matrix[class_to_idx[yt], class_to_idx[yp]] += 1

    # Per-class precision and recall
    precisions = []
    recalls = []

    for i in range(num_classes):
        tp = conf_matrix[i, i]
        fp = np.sum(conf_matrix[:, i]) - tp
        fn = np.sum(conf_matrix[i, :]) - tp

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        if (tp + fn) > 0:  # only include classes present in ground truth
            precisions.append(prec)
            recalls.append(rec)

    macro_prec = float(np.mean(precisions)) if precisions else 0.0
    macro_rec = float(np.mean(recalls)) if recalls else 0.0
    macro_f1 = (2 * macro_prec * macro_rec / (macro_prec + macro_rec)) if (macro_prec + macro_rec) > 0 else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "confusion_matrix": conf_matrix.tolist(),
        "classes": all_classes,
        "sample_count": total
    }


def compute_wer(
    references: List[Union[str, List[str]]],
    hypotheses: List[Union[str, List[str]]]
) -> float:
    """
    Computes Word Error Rate (WER) via dynamic programming Levenshtein alignment:
    WER = (Substitutions + Deletions + Insertions) / Total Reference Words.
    """
    total_distance = 0
    total_words = 0

    for ref, hyp in zip(references, hypotheses):
        ref_tokens = ref.split() if isinstance(ref, str) else list(ref)
        hyp_tokens = hyp.split() if isinstance(hyp, str) else list(hyp)

        # Standard Levenshtein distance on words
        r_len = len(ref_tokens)
        h_len = len(hyp_tokens)

        if r_len == 0:
            total_distance += h_len
            continue

        total_words += r_len

        dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
        for i in range(r_len + 1):
            dp[i][0] = i
        for j in range(h_len + 1):
            dp[0][j] = j

        for i in range(1, r_len + 1):
            for j in range(1, h_len + 1):
                if ref_tokens[i - 1].upper() == hyp_tokens[j - 1].upper():
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # deletion
                        dp[i][j - 1],      # insertion
                        dp[i - 1][j - 1]   # substitution
                    )

        total_distance += dp[r_len][h_len]

    if total_words == 0:
        return 0.0

    wer = total_distance / total_words
    return round(wer, 4)


def _get_ngrams(words: List[str], n: int) -> Counter:
    return Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))


def compute_bleu(
    references: List[str],
    hypotheses: List[str],
    max_n: int = 4
) -> float:
    """
    Computes corpus-level BLEU-4 with brevity penalty.
    References and hypotheses should be raw English sentences.
    """
    if not references or not hypotheses:
        return 0.0

    total_ref_len = 0
    total_hyp_len = 0
    p_ns = []

    for n in range(1, max_n + 1):
        n_match = 0
        n_total = 0

        for ref, hyp in zip(references, hypotheses):
            ref_words = ref.strip().lower().split()
            hyp_words = hyp.strip().lower().split()

            if n == 1:
                total_ref_len += len(ref_words)
                total_hyp_len += len(hyp_words)

            ref_ngrams = _get_ngrams(ref_words, n)
            hyp_ngrams = _get_ngrams(hyp_words, n)

            for ng, count in hyp_ngrams.items():
                n_match += min(count, ref_ngrams.get(ng, 0))
            n_total += max(0, len(hyp_words) - n + 1)

        p_n = (n_match + 1e-7) / (n_total + 1e-7)
        p_ns.append(p_n)

    # Brevity penalty
    if total_hyp_len == 0:
        return 0.0

    if total_hyp_len > total_ref_len:
        bp = 1.0
    else:
        bp = math.exp(1.0 - (total_ref_len / total_hyp_len))

    # Geometric mean
    log_sum = sum(math.log(p) for p in p_ns) / max_n
    bleu = bp * math.exp(log_sum)
    return round(bleu * 100.0, 2)


def compute_chrf(
    references: List[str],
    hypotheses: List[str],
    n_order: int = 6,
    beta: float = 2.0
) -> float:
    """
    Computes character n-gram F-score (chrF).
    Sensitive to morphological variants, highly recommended for sign-to-text.
    """
    if not references or not hypotheses:
        return 0.0

    precisions = []
    recalls = []

    for n in range(1, n_order + 1):
        match_count = 0
        hyp_count = 0
        ref_count = 0

        for ref, hyp in zip(references, hypotheses):
            ref_chars = "".join(ref.strip().lower().split())
            hyp_chars = "".join(hyp.strip().lower().split())

            ref_ngrams = Counter(ref_chars[i:i + n] for i in range(len(ref_chars) - n + 1))
            hyp_ngrams = Counter(hyp_chars[i:i + n] for i in range(len(hyp_chars) - n + 1))

            for ng, cnt in hyp_ngrams.items():
                match_count += min(cnt, ref_ngrams.get(ng, 0))

            hyp_count += max(0, len(hyp_chars) - n + 1)
            ref_count += max(0, len(ref_chars) - n + 1)

        p = (match_count + 1e-7) / (hyp_count + 1e-7)
        r = (match_count + 1e-7) / (ref_count + 1e-7)
        precisions.append(p)
        recalls.append(r)

    avg_p = sum(precisions) / len(precisions)
    avg_r = sum(recalls) / len(recalls)

    if (avg_p + avg_r) == 0:
        return 0.0

    b2 = beta ** 2
    f_score = (1 + b2) * (avg_p * avg_r) / (b2 * avg_p + avg_r)
    return round(f_score * 100.0, 2)
