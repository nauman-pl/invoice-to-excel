from pathlib import Path
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

def extract_text_from_image(image_path: str | Path) -> str:
    """
    Extracts text from an image file (PNG, JPG, TIFF, etc.) using Tesseract OCR.
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip()

def extract_text_from_scanned_pdf(pdf_path: str | Path) -> str:
    """
    Converts each PDF page into a high-res image and runs Tesseract OCR.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    # 300 DPI is the sweet spot for crisp OCR character recognition
    images = convert_from_path(str(path), dpi=300)
    
    extracted_pages = []
    for idx, img in enumerate(images):
        page_text = pytesseract.image_to_string(img)
        extracted_pages.append(page_text)

    return "\n".join(extracted_pages).strip()