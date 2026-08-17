"""Evaluation CLI and retrieval-only result writer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.evaluation.datasets import load_questions
from app.evaluation.metrics import abstention_accuracy, mean_reciprocal_rank, precision_at_k, recall_at_k
from app.retrieval.embeddings import HashEmbedder
from app.retrieval.reranker import CrossEncoderReranker
from app.retrieval.service import HybridRetriever, load_chunks


def run_retrieval_evaluation(dataset_path: Path, chunks_path: Path, top_k: int = 5) -> dict[str, object]:
    questions = load_questions(dataset_path)
    if not questions:
        return {
            "question_count": 0,
            "retrieval_recall_at_k": 0.0,
            "retrieval_precision_at_k": 0.0,
            "mrr": 0.0,
            "abstention_accuracy": 0.0,
            "note": "Dataset is empty; no evaluation score has been claimed.",
        }
    chunks = load_chunks(chunks_path)
    retriever = HybridRetriever(chunks, HashEmbedder(), CrossEncoderReranker(None))
    recalls: list[float] = []
    precisions: list[float] = []
    ranked_lists: list[list[str]] = []
    relevant_union: set[str] = set()
    predicted_statuses: list[str] = []
    expected_statuses: list[str] = []
    for item in questions:
        hits = retriever.search(item.question, evidence_k=top_k)
        retrieved = [hit.chunk.chunk_id for hit in hits]
        relevant = item.gold_chunk_ids
        recalls.append(recall_at_k(retrieved, relevant, top_k))
        precisions.append(precision_at_k(retrieved, relevant, top_k))
        ranked_lists.append(retrieved)
        relevant_union.update(relevant)
        predicted_statuses.append("ABSTAINED" if not hits else "ANSWERED")
        expected_statuses.append(item.expected_status)
    return {
        "question_count": len(questions),
        "retrieval_recall_at_k": sum(recalls) / len(recalls) if recalls else 0.0,
        "retrieval_precision_at_k": sum(precisions) / len(precisions) if precisions else 0.0,
        "mrr": mean_reciprocal_rank(ranked_lists, relevant_union),
        "abstention_accuracy": abstention_accuracy(predicted_statuses, expected_statuses),
        "note": "This runner reports only measured values; empty datasets produce empty-baseline zeros.",
    }


def main() -> int:
    settings = Settings.from_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=settings.project_root / "data/evaluation/questions.json")
    parser.add_argument("--chunks", type=Path, default=settings.processed_dir / "chunks/all_chunks.jsonl")
    parser.add_argument("--output", type=Path, default=settings.project_root / "data/evaluation/results.json")
    args = parser.parse_args()
    result = run_retrieval_evaluation(args.dataset, args.chunks)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
