from pathlib import Path
import pandas as pd
from src.models import Invoice

def export_invoices_to_excel(invoices: list[Invoice], output_path: str | Path) -> Path:
    """
    Exports a list of Invoice objects into a multi-tab Excel spreadsheet:
    1. 'Invoices_Summary' - 1 row per invoice.
    2. 'Line_Items_Detail' - 1 row per item across all invoices.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    item_rows = []

    for inv in invoices:
        inv_id = inv.invoice_number or "UNKNOWN"
        vendor_name = inv.vendor or "N/A"

        # Sheet 1: Header summary
        summary_rows.append({
            "Invoice Number": inv_id,
            "Vendor": vendor_name,
            "Customer": inv.customer or "N/A",
            "Date": inv.date or "N/A",
            "Items Count": len(inv.items),
            "Subtotal ($)": inv.subtotal if inv.subtotal is not None else 0.0,
            "Tax ($)": inv.tax if inv.tax is not None else 0.0,
            "Total ($)": inv.total if inv.total is not None else 0.0,
        })

        # Sheet 2: Line items detail
        for item in inv.items:
            item_rows.append({
                "Invoice Number": inv_id,
                "Vendor": vendor_name,
                "Description": item.description,
                "Quantity": item.quantity,
                "Unit Price ($)": item.unit_price,
                "Line Total ($)": item.total,
            })

    # Build DataFrames
    df_summary = pd.DataFrame(summary_rows)
    df_items = pd.DataFrame(item_rows) if item_rows else pd.DataFrame(
        columns=["Invoice Number", "Vendor", "Description", "Quantity", "Unit Price ($)", "Line Total ($)"]
    )

    # Write both sheets using openpyxl engine
    with pd.ExcelWriter(dest, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Invoices_Summary", index=False)
        df_items.to_excel(writer, sheet_name="Line_Items_Detail", index=False)

    print(f"✓ Exported {len(summary_rows)} invoice(s) & {len(item_rows)} line item(s) to: {dest}")
    return dest

if __name__ == "__main__":
    from src.main import process_all_invoices
    process_all_invoices("data/input", "data/output/all_invoices.xlsx")