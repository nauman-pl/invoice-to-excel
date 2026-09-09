import re
from src.pdf_extractor import extract_text_from_pdf
from src.models import Invoice

def parse_invoice_text(text: str) -> Invoice:
    """
    Parses raw text extracted from an invoice into an Invoice data model.
    """
    invoice = Invoice()

    # 1. Vendor
    vendor_match = re.search(r"INVOICE\s*\n+([^\n]+)", text, re.IGNORECASE)
    if vendor_match:
        invoice.vendor = vendor_match.group(1).strip()

    # 2. Invoice Number
    inv_num_match = re.search(r"(?:Invoice\s*(?:Number|No\.?|#)|Inv\s*#|Invoice\s*:)[:\s]*([A-Za-z0-9-_]+)", text, re.IGNORECASE)
    if inv_num_match:
        invoice.invoice_number = inv_num_match.group(1).strip()

    # 3. Invoice Date
    date_match = re.search(r"Date[:\s]+(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})", text, re.IGNORECASE)
    if date_match:
        invoice.date = date_match.group(1).strip()

    # 4. Customer
    customer_match = re.search(r"Customer[:\s]+([^\n]+)", text, re.IGNORECASE)
    if customer_match:
        invoice.customer = customer_match.group(1).strip()

    # 5. Subtotal
    subtotal_match = re.search(r"Subtotal[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if subtotal_match:
        invoice.subtotal = float(subtotal_match.group(1).replace(",", ""))

    # 6. Tax
    tax_match = re.search(r"Tax(?:\s*\(\d+%\))?[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if tax_match:
        invoice.tax = float(tax_match.group(1).replace(",", ""))

    # 7. Total
    total_match = re.search(r"(?<!Sub)Total[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if total_match:
        invoice.total = float(total_match.group(1).replace(",", ""))

    return invoice

if __name__ == "__main__":
    sample_path = "data/input/sample_invoice.pdf"
    raw_text = extract_text_from_pdf(sample_path)
    invoice = parse_invoice_text(raw_text)
    
    print("--- Structured Invoice JSON ---")
    print(invoice.to_json())