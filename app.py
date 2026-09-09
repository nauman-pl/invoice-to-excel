import os
import tempfile
from pathlib import Path
import streamlit as st
import pandas as pd

from src.pdf_extractor import extract_text
from src.parser import parse_invoice_text
from src.ai_extractor import extract_invoice_with_ai
from src.validator import validate_invoice, ValidationResult
from src.exporter import export_invoices_to_excel
from src.models import Invoice

# Page Configuration
st.set_page_config(
    page_title="Invoice → Excel Automation",
    page_icon="📑",
    layout="wide"
)

st.title("📑 Invoice → Excel Automation")
st.markdown("Automate invoice data extraction from PDFs and images into structured Excel spreadsheets.")

# Sidebar Settings
st.sidebar.header("⚙️ Extraction Settings")
extraction_mode = st.sidebar.radio(
    "Extraction Engine:",
    ["AI-Assisted (Gemini 3.6 Flash)", "Deterministic (Regex / Fast)"],
    index=0
)

has_api_key = bool(os.getenv("GEMINI_API_KEY"))
if extraction_mode.startswith("AI") and not has_api_key:
    st.sidebar.warning("⚠ GEMINI_API_KEY not found in .env. Will fall back to Regex.")

# File Uploader Widget
uploaded_files = st.file_uploader(
    "Upload one or more invoices (PDF, PNG, JPG):",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    st.write(f"📁 **{len(uploaded_files)} file(s) selected**")
    
    if st.button("🚀 Process Invoices", type="primary"):
        processed_invoices: list[Invoice] = []
        validation_results: list[ValidationResult] = []
        seen_invoices = set()
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name} ...")
            
            # Save uploaded file temporarily to disk so extractor can read it
            suffix = Path(uploaded_file.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp_path = tmp.name

            try:
                # 1. Extract text (handles digital and scanned OCR)
                raw_text = extract_text(tmp_path)

                # 2. Parse using selected mode
                if extraction_mode.startswith("AI") and has_api_key:
                    invoice, val_result = extract_invoice_with_ai(raw_text)
                else:
                    invoice = parse_invoice_text(raw_text)
                    val_result = validate_invoice(invoice)

                # 3. Duplicate Detection Check
                invoice_key = (
                    (invoice.vendor or "").strip().lower(),
                    (invoice.invoice_number or "").strip().lower()
                )
                if invoice_key != ("", "") and invoice_key in seen_invoices:
                    val_result.is_valid = False
                    val_result.warnings.append(
                        f"DUPLICATE: Invoice '{invoice.invoice_number}' from '{invoice.vendor}' was already processed!"
                    )
                    val_result.confidence_score = min(val_result.confidence_score, 0.30)
                else:
                    if invoice_key != ("", ""):
                        seen_invoices.add(invoice_key)

                processed_invoices.append(invoice)
                validation_results.append(val_result)

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {e}")
            finally:
                # Clean up temporary file
                Path(tmp_path).unlink(missing_ok=True)

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_text.text("✓ Processing complete!")

        # Display Results
        if processed_invoices:
            st.subheader("📊 Extracted Summary")
            
            summary_data = []
            for inv, val in zip(processed_invoices, validation_results):
                summary_data.append({
                    "Invoice #": inv.invoice_number or "N/A",
                    "Vendor": inv.vendor or "N/A",
                    "Date": inv.date or "N/A",
                    "Items Count": len(inv.items),
                    "Subtotal ($)": f"${inv.subtotal:.2f}" if inv.subtotal is not None else "$0.00",
                    "Tax ($)": f"${inv.tax:.2f}" if inv.tax is not None else "$0.00",
                    "Total ($)": f"${inv.total:.2f}" if inv.total is not None else "$0.00",
                    "Confidence": f"{val.confidence_score * 100:.0f}%",
                    "Status": "✅ Verified" if val.is_valid else "⚠️ Review Needed",
                    "Warnings": "; ".join(val.warnings) if val.warnings else "None"
                })

            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, use_container_width=True)

            # Generate Excel for download
            output_path = Path("data/output/web_export.xlsx")
            export_invoices_to_excel(processed_invoices, output_path)

            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Download Consolidated Excel (.xlsx)",
                    data=f.read(),
                    file_name="invoices_consolidated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
