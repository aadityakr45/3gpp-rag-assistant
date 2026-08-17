from pathlib import Path

from app.ingestion.pipeline import ingest_corpus


ROOT = Path(__file__).resolve().parents[2]


def test_strict_release_ingestion_records_real_corpus_mismatch(tmp_path: Path) -> None:
    result = ingest_corpus(
        ROOT / "data",
        tmp_path / "processed",
        tmp_path / "corpus_manifest.json",
        expected_release="18",
        strict_release=True,
    )
    assert result.document_count == 4
    assert result.processed_count == 0
    assert result.skipped_count == 4
    assert result.failed_count == 0
