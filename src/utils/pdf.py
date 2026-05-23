"""PDF text extraction. pdfplumber is the default; pypdf is the fallback."""

from __future__ import annotations

from pathlib import Path


def extract_text(pdf_path: str | Path) -> str:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume PDF not found at {path}")

    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                if txt.strip():
                    chunks.append(txt)
        if chunks:
            return "\n\n".join(chunks).strip()
    except Exception:
        # fall through to pypdf
        pass

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        if txt.strip():
            chunks.append(txt)
    return "\n\n".join(chunks).strip()
