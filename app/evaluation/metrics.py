"""Machine-readable retrieval and abstention metrics."""

from __future__ import annotations

from typing import Iterable


def recall_at_k(retrieved: Iterable[str], relevant: Iterable[str], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    return len(set(list(retrieved)[:k]) & relevant_set) / len(relevant_set)


def precision_at_k(retrieved: Iterable[str], relevant: Iterable[str], k: int) -> float:
    top = list(retrieved)[:k]
    if not top:
        return 0.0
    return len(set(top) & set(relevant)) / len(top)


def mean_reciprocal_rank(retrieved_lists: Iterable[Iterable[str]], relevant: Iterable[str]) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    reciprocal_ranks = []
    for retrieved in retrieved_lists:
        rank = next((index for index, item in enumerate(retrieved, start=1) if item in relevant_set), None)
        reciprocal_ranks.append(1.0 / rank if rank else 0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def abstention_accuracy(predicted: Iterable[str], expected: Iterable[str]) -> float:
    predicted_values = list(predicted)
    expected_values = list(expected)
    if not expected_values or len(predicted_values) != len(expected_values):
        return 0.0
    return sum(left == right for left, right in zip(predicted_values, expected_values)) / len(expected_values)
