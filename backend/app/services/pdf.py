from dataclasses import dataclass
from pathlib import Path
import shutil

import fitz
from PIL import Image
import pytesseract


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str


class OCRUnavailableError(RuntimeError):
    """Raised when scanned PDF text needs OCR but the OCR engine is unavailable."""


def _configure_tesseract() -> None:
    if shutil.which("tesseract"):
        return
    windows_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if windows_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(windows_path)


def extract_pdf(path: Path) -> list[PageText]:
    pages: list[PageText] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document):
            text = page.get_text("text").strip()
            if not text:
                try:
                    _configure_tesseract()
                    pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                    text = pytesseract.image_to_string(image).strip()
                except pytesseract.TesseractNotFoundError as exc:
                    raise OCRUnavailableError(
                        "This scanned PDF needs OCR, but the OCR engine is not installed."
                    ) from exc
            pages.append(PageText(page_number=index + 1, text=text))
    return pages


def chunk_pages(pages: list[PageText], chunk_size: int = 1800, overlap: int = 250) -> list[dict]:
    chunks: list[dict] = []
    for page in pages:
        if not page.text:
            continue
        start = 0
        while start < len(page.text):
            end = min(start + chunk_size, len(page.text))
            chunks.append({"page": page.page_number, "text": page.text[start:end]})
            if end == len(page.text):
                break
            start = end - overlap
    return chunks
