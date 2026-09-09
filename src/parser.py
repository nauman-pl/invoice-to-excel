import re
from src.pdf_extractor import extract_text_from_pdf
from src.models import Invoice, InvoiceItem

def parse_line_items(text: str) -> list[InvoiceItem]:
    """
    Extracts line items from the text stream between table headers and Subtotal.
    """
    items: list[InvoiceItem] = []

    # Find the block of text between the table header and Subtotal
    table_block_match = re.search(
        r"Description\s*\n+Quantity\s*\n+Unit Price.*?\n+Total.*?\n+(.*?)\n+Subtotal:",
        text,
        re.DOTALL | re.IGNORECASE
    )

    if not table_block_match:
        return items

    table_body = table_block_match.group(1).strip()
    lines = [line.strip() for line in table_body.splitlines() if line.strip()]

    # In our sequential text stream, each item is represented across 4 consecutive lines:
    # Line 0: Description
    # Line 1: Quantity
    # Line 2: Unit Price
    # Line 3: Total
    i = 0
    while i < len(lines):
        # Look ahead to see if lines[i+1], [i+2], [i+3] match numbers
        if i + 3 < len(lines):
            desc = lines[i]
            qty_str = lines[i + 1]
            unit_price_str = lines[i + 2].replace("$", "").replace(",", "")
            total_str = lines[i + 3].replace("$", "").replace(",", "")

            try:
                qty = float(qty_str)
                unit_price = float(unit_price_str)
                total = float(total_str)
                
                items.append(InvoiceItem(
                    description=desc,
                    quantity=qty,
                    unit_price=unit_price,
                    total=total
                ))
                i += 4  # Jump to next 4-line item block
                continue
            except ValueError:
                # If conversion fails, move ahead by 1 line to recover
                pass
        i += 1

    return items

def parse_invoice_text(text: str) -> Invoice:
    invoice = Invoice()

    # 1. Vendor
    vendor_match = re.search(r"INVOICE\s*\n+([^\n]+)", text, re.IGNORECASE)
    if vendor_match:
        invoice.vendor = vendor_match.group(1).replace("\\", "").strip()

    # 2. Invoice Number: supports Invoice No, Inv #, Bill No, Bill #, Tax Invoice #
    inv_num_match = re.search(
        r"(?:(?:Tax\s+)?Invoice\s*(?:Number|No\.?|#)|Bill\s*(?:Number|No\.?|#)|Inv\s*#|Invoice\s*:)[:\s]*([A-Za-z0-9-_]+)",
        text,
        re.IGNORECASE
    )
    if inv_num_match:
        invoice.invoice_number = inv_num_match.group(1).strip()

    # 3. Invoice Date
    date_match = re.search(r"Date[:\s]+(\d{4}[-/.]\d{2}[-/.]\d{2}|\d{2}[-/.]\d{2}[-/.]\d{4})", text, re.IGNORECASE)
    if date_match:
        invoice.date = date_match.group(1).strip()

    # 4. Customer
    customer_match = re.search(r"Customer[:\s]+([^\n]+)", text, re.IGNORECASE)
    if customer_match:
        invoice.customer = customer_match.group(1).replace("\\", "").strip()

    # 5. Line Items Table
    invoice.items = parse_line_items(text)

    # 6. Subtotal
    subtotal_match = re.search(r"Subtotal[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if subtotal_match:
        invoice.subtotal = float(subtotal_match.group(1).replace(",", ""))

    # 7. Tax
    tax_match = re.search(r"Tax(?:\s*\(\d+%\))?[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if tax_match:
        invoice.tax = float(tax_match.group(1).replace(",", ""))

    # 8. Total
    total_match = re.search(r"(?<!Sub)Total[:\s]+(?:\$|USD)?\s*([\d,]+\.\d{2})", text, re.IGNORECASE)
    if total_match:
        invoice.total = float(total_match.group(1).replace(",", ""))

    return invoice

if __name__ == "__main__":
    sample_path = "data/input/sample_invoice.pdf"
    raw_text = extract_text_from_pdf(sample_path)
    invoice = parse_invoice_text(raw_text)
    
    print("--- Structured Invoice with Line Items ---")
    print(invoice.to_json())