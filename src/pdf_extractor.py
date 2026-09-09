from pathlib import Path
from pypdf import PdfReader
from src.ocr import extract_text_from_scanned_pdf, extract_text_from_image

def extract_text(file_path: str | Path) -> str:
    """
    Smart hybrid extractor:
    1. If image file (.png, .jpg, .jpeg), uses OCR directly.
    2. If PDF, tries fast digital text extraction first.
    3. If PDF has no text layer (scanned), automatically falls back to OCR.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Case 1: Image files
    if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
        print(f"  [Image detected: using OCR for {path.name}]")
        return extract_text_from_image(path)

    # Case 2: PDF files - Try fast digital extraction first
    reader = PdfReader(path)
    extracted_pages = []
    for page in reader.pages:
        extracted_pages.append(page.extract_text() or "")
    
    digital_text = "\n".join(extracted_pages).strip()

    # If digital text exists, return it immediately (takes ~5ms)
    if len(digital_text) > 30:
        return digital_text

    # Case 3: Scanned PDF fallback
    print(f"  [Scanned PDF detected: falling back to OCR for {path.name}]")
    return extract_text_from_scanned_pdf(path)

# Backwards compatibility alias
extract_text_from_pdf = extract_text