import os
import tempfile
import uuid
from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image, ImageGrab

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
st.markdown("Automate invoice data extraction from PDFs, images, and screenshots into structured Excel spreadsheets.")

# Initialize session state for clipboard pasted images
if "clipboard_images" not in st.session_state:
    st.session_state.clipboard_images = []  # list of tuples: (filename, PIL Image)

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

# Instructions callout
st.info(
    "💡 **Add invoices in any way:**\n"
    "- **Drag & Drop** any PDF, PNG, JPG, or WebP file below.\n"
    "- **Paste Screenshot:** Take a screenshot on your Mac (`Cmd + Shift + 4` to a file, or `Cmd + Ctrl + Shift + 4` to clipboard), then click **Paste from Clipboard** below!"
)

# Input Section: 2 Columns (File Uploader & Clipboard Paste)
col_upload, col_paste = st.columns([2, 1], gap="medium")

with col_upload:
    st.subheader("📁 Upload Files")
    uploaded_files = st.file_uploader(
        "Drag and drop invoice PDFs, images, or screenshots here:",
        type=["pdf", "png", "jpg", "jpeg", "webp", "tiff", "bmp"],
        accept_multiple_files=True
    )

with col_paste:
    st.subheader("📋 Paste Screenshot")
    st.write("Copy an invoice image / screenshot, then click:")
    
    if st.button("📥 Paste from Mac Clipboard", use_container_width=True):
        try:
            grabbed = ImageGrab.grabclipboard()
            if isinstance(grabbed, Image.Image):
                new_id = len(st.session_state.clipboard_images) + 1
                img_name = f"screenshot_{new_id}_{uuid.uuid4().hex[:4]}.png"
                st.session_state.clipboard_images.append((img_name, grabbed))
                st.success(f"✓ Added screenshot: {img_name}")
            elif isinstance(grabbed, list):
                # When files are copied in macOS Finder
                for p in grabbed:
                    path = Path(p)
                    if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
                        img = Image.open(path)
                        st.session_state.clipboard_images.append((path.name, img))
                st.success(f"✓ Added {len(grabbed)} file(s) from clipboard!")
            else:
                st.warning("No image found in clipboard. Press Cmd+Ctrl+Shift+4 to capture a screenshot to clipboard first!")
        except Exception as e:
            st.error(f"Clipboard read error: {e}")

    # Show thumbnails of pasted images
    if st.session_state.clipboard_images:
        st.write(f"**Pasted Screenshots ({len(st.session_state.clipboard_images)}):**")
        for idx, (name, img) in enumerate(st.session_state.clipboard_images):
            c_thumb, c_btn = st.columns([3, 1])
            with c_thumb:
                st.image(img, caption=name, width=150)
            with c_btn:
                if st.button("❌", key=f"del_{idx}"):
                    st.session_state.clipboard_images.pop(idx)
                    st.rerun()

        if st.button("Clear All Pasted Screenshots"):
            st.session_state.clipboard_images = []
            st.rerun()

# Processing Queue
total_items = (len(uploaded_files) if uploaded_files else 0) + len(st.session_state.clipboard_images)

if total_items > 0:
    st.divider()
    st.write(f"### Ready to process: **{total_items} invoice(s)**")
    
    if st.button("🚀 Process All Invoices", type="primary", use_container_width=True):
        processed_invoices: list[Invoice] = []
        validation_results: list[ValidationResult] = []
        seen_invoices = set()
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Build list of (display_name, local_temp_path)
        items_to_process: list[tuple[str, str]] = []
        temp_files_to_clean: list[str] = []

        # 1. Add uploaded files
        if uploaded_files:
            for uf in uploaded_files:
                suffix = Path(uf.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uf.getbuffer())
                    items_to_process.append((uf.name, tmp.name))
                    temp_files_to_clean.append(tmp.name)

        # 2. Add clipboard images
        for name, img in st.session_state.clipboard_images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                img.save(tmp.name, "PNG")
                items_to_process.append((name, tmp.name))
                temp_files_to_clean.append(tmp.name)

        try:
            for idx, (display_name, file_path) in enumerate(items_to_process):
                status_text.text(f"Processing ({idx + 1}/{total_items}): {display_name} ...")
                
                try:
                    # Step A: Hybrid extraction (digital or OCR)
                    raw_text = extract_text(file_path)

                    # Step B: Parsing (AI or deterministic)
                    if extraction_mode.startswith("AI") and has_api_key:
                        invoice, val_result = extract_invoice_with_ai(raw_text)
                    else:
                        invoice = parse_invoice_text(raw_text)
                        val_result = validate_invoice(invoice)

                    # Step C: Duplicate detection
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

                except Exception as err:
                    st.error(f"Error processing {display_name}: {err}")

                progress_bar.progress((idx + 1) / total_items)

            status_text.text(f"✓ All {total_items} invoice(s) processed!")

            # Display Results Table
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

                # Export Multi-sheet Excel
                output_path = Path("data/output/web_export.xlsx")
                export_invoices_to_excel(processed_invoices, output_path)

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Consolidated Excel (.xlsx)",
                        data=f.read(),
                        file_name="invoices_consolidated.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True
                    )

        finally:
            # Clean up all temporary files safely
            for tf in temp_files_to_clean:
                Path(tf).unlink(missing_ok=True)
