from pathlib import Path
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """
    Extracts all selectable text from a PDF file page by page.
    
    Args:
        pdf_path: Path to the target PDF file.
        
    Returns:
        A single string containing all extracted text separated by newlines.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file does not exist at: {path}")

    reader = PdfReader(path)
    extracted_pages: list[str] = []

    for index, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        extracted_pages.append(page_text)

    full_text = "\n".join(extracted_pages).strip()
    return full_text

if __name__ == "__main__":
    sample_path = "data/input/sample_invoice.pdf"
    print(f"--- Extracting text from: {sample_path} ---")
    text = extract_text_from_pdf(sample_path)
    print(text)
    print("\n--- End of Extracted Text ---")