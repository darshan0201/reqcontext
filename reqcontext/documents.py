"""Explicit local reference documents with page provenance and bounded extraction."""
from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass(frozen=True)
class SourceDocument:
    path: str | Path
    title: str = ""
    revision: str = "unspecified"
    source_type: str = "reference"

    def key(self):
        path = Path(self.path).resolve()
        return "@documents/" + hashlib.sha256(str(path).encode()).hexdigest()[:16] + "/" + path.name


def extract(document, *, max_bytes=50_000_000, max_pages=500, max_text_chars=2_000_000):
    path = Path(document.path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Document must be a regular local file")
    with path.open("rb") as handle:
        raw = handle.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError("Document exceeds the byte limit")
    fingerprint = hashlib.sha256(raw).hexdigest()
    pages, warnings = [], []
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ValueError("Install the documents extra for PDF extraction") from error
        from io import BytesIO
        reader = PdfReader(BytesIO(raw), strict=False)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported")
        if len(reader.pages) > max_pages:
            raise ValueError("PDF exceeds the page limit")
        total = 0
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            total += len(text)
            if total > max_text_chars:
                raise ValueError("Document exceeds the extracted-text limit")
            if not text.strip():
                warnings.append(f"Page {number} has no extractable text; OCR is not performed.")
            pages.append((number, text))
        warnings.append("PDF text extraction may lose table, column, formula or diagram meaning; review the original page when necessary.")
    elif path.suffix.lower() in {".txt", ".md", ".rst"}:
        text = raw.decode("utf-8")
        if len(text) > max_text_chars:
            raise ValueError("Document exceeds the extracted-text limit")
        pages = [(None, text)]
    else:
        raise ValueError("References must be PDF, UTF-8 text, Markdown or RST")
    return fingerprint, pages, warnings
