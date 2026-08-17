"""CLI: ``python -m app.ingestion``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.config import Settings
from app.ingestion.loader import CorpusPathError
from app.ingestion.pipeline import ingest_corpus
from app.retrieval.indexing import build_indexes


def main(argv: list[str] | None = None) -> int:
    settings = Settings.from_environment()
    parser = argparse.ArgumentParser(description="Ingest the local 3GPP PDF corpus")
    parser.add_argument("--input", type=Path, default=None, help="PDF directory")
    parser.add_argument("--output", type=Path, default=settings.processed_dir)
    parser.add_argument("--manifest", type=Path, default=settings.manifest_path)
    parser.add_argument("--expected-release", default="18")
    parser.add_argument("--strict-release", action="store_true")
    parser.add_argument("--build-indexes", action="store_true")
    parser.add_argument("--allow-hash-fallback", action="store_true")
    args = parser.parse_args(argv)

    input_dir = args.input or settings.corpus_input_dir
    # The supplied repository currently stores PDFs in data/. This fallback is
    # explicit in the CLI output and never changes or moves those source files.
    if args.input is None and not input_dir.exists():
        fallback = settings.project_root / "data"
        if fallback.exists() and any(fallback.glob("*.pdf")):
            print(
                f"Warning: configured corpus path is absent; using local fallback {fallback}",
                file=sys.stderr,
            )
            input_dir = fallback

    try:
        result = ingest_corpus(
            input_dir,
            args.output,
            args.manifest,
            expected_release=args.expected_release,
            strict_release=args.strict_release,
        )
    except CorpusPathError as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}), file=sys.stderr)
        return 2
    output = {"status": "OK", **result.__dict__}
    if args.build_indexes and result.chunk_count:
        index_info = build_indexes(
            args.output / "chunks" / "all_chunks.jsonl",
            args.output / "index",
            settings,
            allow_hash_fallback=args.allow_hash_fallback,
        )
        output["indexing"] = index_info
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if result.failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
