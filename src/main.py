from pathlib import Path
from src.pdf_extractor import extract_text_from_pdf
from src.parser import parse_invoice_text
from src.exporter import export_invoices_to_excel
from src.models import Invoice

def process_all_invoices(input_dir: str | Path, output_file: str | Path) -> Path | None:
    """
    Scans an input directory for PDFs, extracts and parses each one,
    and saves all extracted data into a single consolidated Excel file.
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)

    # 1. Find all PDF files in the directory
    pdf_files = sorted(list(input_path.glob("*.pdf")))
    
    if not pdf_files:
        print(f"⚠ No PDF files found in: {input_path}")
        return None

    print(f"Found {len(pdf_files)} PDF file(s) in '{input_path}'. Starting batch processing...\n")

    successful_invoices: list[Invoice] = []
    failed_files: list[str] = []

    # 2. Loop through each file with error isolation
    for pdf_file in pdf_files:
        print(f"  → Processing: {pdf_file.name} ... ", end="")
        try:
            # Step A: Extract raw text
            raw_text = extract_text_from_pdf(pdf_file)
            
            # Step B: Parse text into structured Invoice
            invoice = parse_invoice_text(raw_text)
            
            successful_invoices.append(invoice)
            print(f"✓ OK (Invoice: {invoice.invoice_number or 'Unknown'}, Total: ${invoice.total or 0.0:.2f})")
            
        except Exception as err:
            print(f"✗ FAILED: {err}")
            failed_files.append(pdf_file.name)

    print(f"\n--- Batch Summary ---")
    print(f"Total processed : {len(pdf_files)}")
    print(f"Successful       : {len(successful_invoices)}")
    print(f"Failed           : {len(failed_files)}")

    # 3. Export all successful invoices into one Excel file
    if successful_invoices:
        saved_path = export_invoices_to_excel(successful_invoices, output_path)
        return saved_path
    else:
        print("⚠ No invoices were successfully parsed. Excel export skipped.")
        return None

if __name__ == "__main__":
    process_all_invoices(
        input_dir="data/input",
        output_file="data/output/all_invoices.xlsx"
    )