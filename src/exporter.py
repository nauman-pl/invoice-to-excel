from pathlib import Path
import pandas as pd
from src.models import Invoice

def export_invoices_to_excel(invoices: list[Invoice], output_path: str | Path) -> Path:
    """
    Exports a list of Invoice objects into an Excel spreadsheet.
    
    Args:
        invoices: A list of Invoice objects to export.
        output_path: Path where the .xlsx file will be saved.
        
    Returns:
        The Path to the created Excel file.
    """
    dest = Path(output_path)
    # Ensure the parent directory (data/output/) exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Flatten invoice header data into a list of row dictionaries
    rows = []
    for inv in invoices:
        rows.append({
            "Invoice Number": inv.invoice_number or "N/A",
            "Vendor": inv.vendor or "N/A",
            "Customer": inv.customer or "N/A",
            "Date": inv.date or "N/A",
            "Subtotal ($)": inv.subtotal if inv.subtotal is not None else 0.0,
            "Tax ($)": inv.tax if inv.tax is not None else 0.0,
            "Total ($)": inv.total if inv.total is not None else 0.0,
        })

    # Create a pandas DataFrame
    df = pd.DataFrame(rows)

    # Write to Excel using openpyxl engine
    # index=False ensures pandas doesn't write extra 0, 1, 2 row number columns
    df.to_excel(dest, index=False, engine="openpyxl")
    print(f"✓ Successfully exported {len(invoices)} invoice(s) to: {dest}")
    return dest

if __name__ == "__main__":
    from src.pdf_extractor import extract_text_from_pdf
    from src.parser import parse_invoice_text

    # 1. Extract raw text
    text = extract_text_from_pdf("data/input/sample_invoice.pdf")
    
    # 2. Parse into structured Invoice model
    invoice = parse_invoice_text(text)
    
    # 3. Export to Excel
    export_invoices_to_excel([invoice], "data/output/invoice.xlsx")