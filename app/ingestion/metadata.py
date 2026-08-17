"""Metadata extraction from PDF bytes and authoritative document titles."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.models.domain import PdfMetadata


_CANONICAL_RE = re.compile(
    rb"\(3GPP\s+(TS|TR)\s+(\d{2})\.(\d{3})\s+version\s+"
    rb"([0-9]+\.[0-9]+\.[0-9]+)\s+Release\s+(\d+)\)"
)
_FILENAME_RE = re.compile(r"^(ts|tr)_(\d{6})v(\d{6})p\.pdf$", re.IGNORECASE)


def _xmp_value(data: bytes, tag: bytes) -> str | None:
    pattern = rb"<" + re.escape(tag) + rb">(.*?)</" + re.escape(tag) + rb">"
    match = re.search(pattern, data, re.DOTALL | re.IGNORECASE)
    if not match:
        return None
    return re.sub(rb"\s+", b" ", match.group(1)).decode("utf-8", "replace").strip()


def _xmp_title(data: bytes) -> str | None:
    match = re.search(
        rb"<dc:title>.*?<rdf:li[^>]*>(.*?)</rdf:li>",
        data,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return None
    return re.sub(rb"\s+", b" ", match.group(1)).decode("utf-8", "replace").strip()


def _xmp_list_value(data: bytes, tag: bytes) -> str | None:
    match = re.search(
        rb"<" + re.escape(tag) + rb">.*?<rdf:li[^>]*>(.*?)</rdf:li>",
        data,
        re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return None
    return re.sub(rb"\s+", b" ", match.group(1)).decode("utf-8", "replace").strip()


def _subject_from_title(title: str | None) -> str | None:
    if not title:
        return None
    match = re.search(r"-\s*V[0-9.]+\s*-\s*(.*?)\s+\(3GPP\s", title)
    return match.group(1).strip() if match else None


def _fallback_identity(filename: str) -> tuple[str, str, str] | None:
    match = _FILENAME_RE.match(filename)
    if not match:
        return None
    kind, number, compact_version = match.groups()
    # 3GPP filenames use a leading `1` before the two-digit series number:
    # 123501 -> 23.501 and 121905 -> 21.905.
    specification = f"{kind.upper()} {number[1:3]}.{number[3:]}"
    version = (
        f"{compact_version[:2]}.{compact_version[2:4].lstrip('0') or '0'}."
        f"{compact_version[4:].lstrip('0') or '0'}"
    )
    return specification, version, compact_version[:2]


def parse_pdf_metadata(path: Path) -> PdfMetadata:
    """Extract reproducible metadata without requiring a PDF dependency.

    XMP metadata is preferred because these supplied PDFs store their document
    information in compressed PDF object streams. The parser records warnings
    rather than silently correcting conflicting source values.
    """

    path = path.resolve()
    data = path.read_bytes()
    checksum = hashlib.sha256(data).hexdigest()
    header_match = re.match(rb"%PDF-(\d\.\d)", data)
    pdf_version = header_match.group(1).decode() if header_match else None

    raw_title = _xmp_title(data)
    canonical = _CANONICAL_RE.search(raw_title.encode() if raw_title else b"")
    fallback = _fallback_identity(path.name)
    warnings: list[str] = []

    if canonical:
        kind = canonical.group(1).decode().upper()
        specification = f"{kind} {canonical.group(2).decode()}.{canonical.group(3).decode()}"
        version = canonical.group(4).decode()
        release = canonical.group(5).decode()
    elif fallback:
        specification, version, release = fallback
        kind = specification.split(" ", 1)[0]
        warnings.append("Canonical 3GPP identity was not found in XMP; filename fallback used")
    else:
        specification = version = release = None
        kind = None
        warnings.append("Could not identify a canonical 3GPP specification")

    if canonical and fallback:
        fallback_spec, fallback_version, _ = fallback
        if fallback_spec != specification or fallback_version != version:
            warnings.append(
                f"Filename identity {fallback_spec} {fallback_version} conflicts with XMP "
                f"identity {specification} {version}"
            )

    linearized = re.search(
        rb"/Linearized\s+1[^>]*?/N\s+(\d+)", data[:20000], re.DOTALL
    )
    page_count = int(linearized.group(1)) if linearized else None
    if page_count is None:
        page_count = len(re.findall(rb"/Type/Page(?!s)", data)) or None

    if raw_title and "TR 121 905" in raw_title and specification == "TR 21.905":
        warnings.append("XMP display title says TR 121 905 while canonical identifier says TR 21.905")
    if raw_title and "G; Non-Access-Stratum" in raw_title:
        warnings.append("XMP title contains the literal subject artifact 'G;'")

    keywords = _xmp_value(data, b"pdf:Keywords")
    return PdfMetadata(
        source_path=str(path),
        filename=path.name,
        checksum=checksum,
        pdf_version=pdf_version,
        specification=specification,
        document_kind=kind,
        specification_title=_subject_from_title(raw_title),
        raw_title=raw_title,
        release=release,
        version=version,
        page_count=page_count,
        creator=_xmp_list_value(data, b"dc:creator"),
        producer=_xmp_value(data, b"pdf:Producer"),
        creation_date=_xmp_value(data, b"xmp:CreateDate"),
        modification_date=_xmp_value(data, b"xmp:ModifyDate"),
        keywords=tuple(k.strip() for k in (keywords or "").split(",") if k.strip()),
        warnings=tuple(warnings),
    )
