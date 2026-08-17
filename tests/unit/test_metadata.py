from pathlib import Path

from app.ingestion.metadata import parse_pdf_metadata


ROOT = Path(__file__).resolve().parents[2]


def test_supplied_ts_metadata_is_read_from_pdf_xmp() -> None:
    metadata = parse_pdf_metadata(ROOT / "data" / "ts_123501v171000p.pdf")
    assert metadata.specification == "TS 23.501"
    assert metadata.version == "17.10.0"
    assert metadata.release == "17"
    assert metadata.page_count == 575
    assert metadata.creator == "TSGS"
    assert metadata.producer == "Acrobat Distiller 10.0.0 (Windows)"


def test_tr_metadata_conflict_is_recorded() -> None:
    metadata = parse_pdf_metadata(ROOT / "data" / "tr_121905v160000p.pdf")
    assert metadata.specification == "TR 21.905"
    assert metadata.release == "16"
    assert metadata.page_count == 70
    assert any("TR 121 905" in warning for warning in metadata.warnings)
