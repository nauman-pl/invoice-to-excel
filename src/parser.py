import re
from typing import Any
from src.pdf_extractor import extract_text_from_pdf

def parse_invoice_text(text: str) -> dict[str, Any]:
    """
    Parses raw text extracted from an invoice and extracts standard fields.
    """
    data: dict[str, Any] = {
        "vendor": None,
        "invoice_number": None,
        "date": None,
        "subtotal": None,
        "tax": None,
        "total": None,
    }

    # 1. Vendor: Usually near the top, after "INVOICE"
    vendor_match = re.search(r"INVOICE\s*\n+([^\n]+)", text, re.IGNORECASE)
    if vendor_match:
        data["vendor"] = vendor_match.group(1).strip()

        # 2. Invoice Number: requires "Number", "No", "#", or an explicit colon after "Invoice"
    inv_num_match = re.search(r"(?:Invoice\s*(?:Number|No\.?|#)|Inv\s*#|Invoice\s*:)[:\s]*([A-Za-z0-9-_]+)", text, re.IGNORECASE)
    if inv_num_match:
        data["invoice_number"] = inv_num_match.group(1).strip()

    # 3. Invoice Date: matches YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY
    date_match = re.search(r"Date[:\s]+(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})", text, re.IGNORECASE)
    if date_match:
        data["date"] = date_match.group(1).strip()

    # 4. Subtotal: matches Subtotal followed by numeric amount
    subtotal_match = re.search(r"Subtotal[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if subtotal_match:
        data["subtotal"] = float(subtotal_match.group(1).replace(",", ""))

    # 5. Tax: matches Tax (optional percentage) followed by numeric amount
    tax_match = re.search(r"Tax(?:\s*\(\d+%\))?[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if tax_match:
        data["tax"] = float(tax_match.group(1).replace(",", ""))

    # 6. Total: matches Total followed by numeric amount
    total_match = re.search(r"(?<!Sub)Total[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if total_match:
        data["total"] = float(total_match.group(1).replace(",", ""))

    return data

if __name__ == "__main__":
    sample_path = "data/input/sample_invoice.pdf"
    raw_text = extract_text_from_pdf(sample_path)
    parsed_result = parse_invoice_text(raw_text)
    
    print("--- Extracted Structured Fields ---")
    for key, value in parsed_result.items():
        print(f"{key:15}: {value}")