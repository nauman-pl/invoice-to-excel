import os
import tempfile
import uuid
import platform
from pathlib import Path
import streamlit as st
import pandas as pd
from PIL import Image

from src.pdf_extractor import extract_text
from src.parser import parse_invoice_text
from src.ai_extractor import extract_invoice_with_ai
from src.validator import validate_invoice, ValidationResult
from src.exporter import export_invoices_to_excel
from src.models import Invoice
from src.database import init_db, save_invoice_to_db, get_all_customers, get_customer_purchase_history

# -------------------------------------------------------------
# 1. PAGE & BRANDING CONFIGURATION
# -------------------------------------------------------------
st.set_page_config(
    page_title="InvoceFlow | Invoice → Excel AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

init_db()

# -------------------------------------------------------------
# 2. RESPONSIVE & ULTRA-AESTHETIC CSS (MOBILE, TABLET, DESKTOP)
# -------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hero Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.15) 0%, rgba(147, 51, 234, 0.15) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        backdrop-filter: blur(12px);
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        color: white;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 9999px;
        margin-bottom: 0.75rem;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #FFFFFF, #CBD5E1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        max-width: 650px;
        line-height: 1.5;
        margin: 0;
    }

    /* Modern Glass Cards */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    /* Status Pills */
    .pill-verified {
        background: rgba(16, 185, 129, 0.15);
        color: #10B981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .pill-warning {
        background: rgba(245, 158, 11, 0.15);
        color: #F59E0B;
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Mobile & Tablet Responsive Adjustments */
    @media (max-width: 768px) {
        .hero-container {
            padding: 1.25rem;
        }
        .hero-title {
            font-size: 1.6rem;
        }
        .hero-subtitle {
            font-size: 0.95rem;
        }
        .stButton > button {
            width: 100% !important;
            min-height: 48px; /* Touch friendly hit area */
        }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. STATE MANAGEMENT
# -------------------------------------------------------------
if "clipboard_images" not in st.session_state:
    st.session_state.clipboard_images = []

# Check for API Key (Env or Streamlit Cloud Secrets)
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        api_key = None

# Sidebar Controls
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    extraction_mode = st.radio(
        "Parser Engine:",
        ["AI (Gemini 3.6 Flash)", "Deterministic (Regex / Fast)"],
        index=0 if api_key else 1
    )
    if extraction_mode.startswith("AI") and not api_key:
        st.warning("⚠ No GEMINI_API_KEY detected. Falling back to Regex.")
    
    st.markdown("---")
    st.markdown(f"**Platform:** `{platform.system()} ({platform.machine()})`")
    st.caption("Cross-platform ready: Mac, Windows, Linux, iOS & Android.")

# -------------------------------------------------------------
# 4. HERO HEADER
# -------------------------------------------------------------
st.markdown("""
<div class="hero-container">
    <span class="hero-badge">⚡ Next-Gen Document AI</span>
    <h1 class="hero-title">InvoiceFlow</h1>
    <p class="hero-subtitle">
        Transform messy PDFs, camera snaps, and screenshots into production-ready Excel spreadsheets with Zero-Trust financial validation.
    </p>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tab_pipeline, tab_analytics = st.tabs([
    "📑 Extraction Pipeline", 
    "👤 Customer Intelligence & Memory"
])

# -------------------------------------------------------------
# TAB 1: PIPELINE (DESKTOP, MOBILE & TABLET COMPATIBLE)
# -------------------------------------------------------------
with tab_pipeline:
    col_upload, col_quick = st.columns([1.6, 1], gap="large")

    with col_upload:
        st.markdown("#### 1. Upload Invoices or Receipts")
        uploaded_files = st.file_uploader(
            "Drag & drop any PDF, image, or screenshot:",
            type=["pdf", "png", "jpg", "jpeg", "webp", "tiff", "bmp"],
            accept_multiple_files=True
        )

    with col_quick:
        st.markdown("#### 2. Mobile Camera & Quick Paste")
        
        # Method A: Clipboard Paste (Mac/Windows/Linux)
        if st.button("📋 Paste from Clipboard", use_container_width=True):
            try:
                from PIL import ImageGrab
                grabbed = ImageGrab.grabclipboard()
                if isinstance(grabbed, Image.Image):
                    name = f"screenshot_{len(st.session_state.clipboard_images)+1}_{uuid.uuid4().hex[:4]}.png"
                    st.session_state.clipboard_images.append((name, grabbed))
                    st.toast(f"✓ Screenshot added: {name}", icon="📸")
                elif isinstance(grabbed, list):
                    for p in grabbed:
                        path = Path(p)
                        if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
                            st.session_state.clipboard_images.append((path.name, Image.open(path)))
                    st.toast(f"✓ Added {len(grabbed)} file(s) from clipboard!", icon="📎")
                else:
                    st.info("No image in clipboard. Copy an image or press Cmd+Ctrl+Shift+4!")
            except Exception as e:
                st.warning(f"Clipboard access unavailable on this device: {e}")

        # Method B: Camera Snap (Mobile Phones & Tablets)
        with st.expander("📸 Snap Photo with Camera (Phone / Tablet)"):
            camera_photo = st.camera_input("Take photo of receipt or invoice")
            if camera_photo:
                c_img = Image.open(camera_photo)
                c_name = f"cam_snap_{uuid.uuid4().hex[:4]}.png"
                if not any(x[0] == c_name for x in st.session_state.clipboard_images):
                    st.session_state.clipboard_images.append((c_name, c_img))
                    st.success(f"✓ Captured from camera: {c_name}")

    # Show thumbnails of pasted / camera snapped items
    if st.session_state.clipboard_images:
        st.markdown("##### 🖼️ In-Memory Captures")
        thumb_cols = st.columns(min(4, len(st.session_state.clipboard_images)))
        for i, (name, img) in enumerate(st.session_state.clipboard_images):
            with thumb_cols[i % len(thumb_cols)]:
                st.image(img, caption=name, use_container_width=True)
                if st.button("Remove", key=f"rm_{i}", use_container_width=True):
                    st.session_state.clipboard_images.pop(i)
                    st.rerun()

    total_files = (len(uploaded_files) if uploaded_files else 0) + len(st.session_state.clipboard_images)

    # -------------------------------------------------------------
    # BATCH PROCESSOR
    # -------------------------------------------------------------
    if total_files > 0:
        st.markdown("---")
        st.markdown(f"### ⚡ Ready to Process **{total_files} Document(s)**")
        
        if st.button("🚀 Process Invoices & Export to Excel", type="primary", use_container_width=True):
            processed_invoices: list[Invoice] = []
            validation_results: list[ValidationResult] = []
            seen_invoices = set()
            
            progress = st.progress(0)
            status = st.empty()

            items_to_process = []
            temp_cleanup = []

            # Add uploaded files
            if uploaded_files:
                for f in uploaded_files:
                    suffix = Path(f.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(f.getbuffer())
                        items_to_process.append((f.name, tmp.name))
                        temp_cleanup.append(tmp.name)

            # Add clipboard & camera captures
            for name, img in st.session_state.clipboard_images:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    img.save(tmp.name, "PNG")
                    items_to_process.append((name, tmp.name))
                    temp_cleanup.append(tmp.name)

            try:
                for idx, (display_name, local_path) in enumerate(items_to_process):
                    status.markdown(f"**Processing ({idx + 1}/{total_files}):** `{display_name}` ...")
                    
                    try:
                        raw_text = extract_text(local_path)

                        if extraction_mode.startswith("AI") and api_key:
                            inv, val = extract_invoice_with_ai(raw_text)
                        else:
                            inv = parse_invoice_text(raw_text)
                            val = validate_invoice(inv)

                        # Duplicate Check
                        inv_key = ((inv.vendor or "").strip().lower(), (inv.invoice_number or "").strip().lower())
                        if inv_key != ("", "") and inv_key in seen_invoices:
                            val.is_valid = False
                            val.warnings.append(f"DUPLICATE: Invoice #{inv.invoice_number} from {inv.vendor} already exists in batch!")
                            val.confidence_score = min(val.confidence_score, 0.30)
                        else:
                            if inv_key != ("", ""):
                                seen_invoices.add(inv_key)

                        # Save to Customer Database Memory
                        save_invoice_to_db(inv, getattr(inv, "extra_fields", None))

                        processed_invoices.append(inv)
                        validation_results.append(val)

                    except Exception as err:
                        st.error(f"Error processing {display_name}: {err}")

                    progress.progress((idx + 1) / total_files)

                status.success(f"✓ Successfully processed {len(processed_invoices)} invoice(s)!")

                # Live Results Table
                if processed_invoices:
                    st.markdown("### 📊 Extracted Invoices Summary")
                    
                    table_rows = []
                    for inv, val in zip(processed_invoices, validation_results):
                        table_rows.append({
                            "Invoice #": inv.invoice_number or "N/A",
                            "Vendor": inv.vendor or "N/A",
                            "Customer": inv.customer or "N/A",
                            "Date": inv.date or "N/A",
                            "Items": len(inv.items),
                            "Subtotal": f"${inv.subtotal:.2f}" if inv.subtotal is not None else "$0.00",
                            "Tax": f"${inv.tax:.2f}" if inv.tax is not None else "$0.00",
                            "Total": f"${inv.total:.2f}" if inv.total is not None else "$0.00",
                            "Confidence": f"{val.confidence_score * 100:.0f}%",
                            "Status": "✅ Verified" if val.is_valid else "⚠️ Review Needed",
                            "Warnings": "; ".join(val.warnings) if val.warnings else "None"
                        })

                    st.dataframe(pd.DataFrame(table_rows), use_container_width=True)

                    # Export to Multi-sheet Excel
                    excel_path = Path("data/output/web_export.xlsx")
                    export_invoices_to_excel(processed_invoices, excel_path)

                    with open(excel_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Consolidated Multi-Sheet Excel (.xlsx)",
                            data=f.read(),
                            file_name="invoices_consolidated.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary",
                            use_container_width=True
                        )

            finally:
                for tmp_file in temp_cleanup:
                    Path(tmp_file).unlink(missing_ok=True)

# -------------------------------------------------------------
# TAB 2: CUSTOMER INTELLIGENCE & TIMELINE MEMORY
# -------------------------------------------------------------
with tab_analytics:
    st.markdown("### 👤 Customer Intelligence & Purchase Memory")
    st.markdown("Select any customer account to view their itemized purchasing timeline and lifetime spend.")

    customers = get_all_customers()

    if not customers:
        st.info("No customers recorded yet. Process invoices in Tab 1 to build customer intelligence profiles!")
    else:
        selected_cust = st.selectbox("Select Customer Profile:", customers)

        if selected_cust:
            hist = get_customer_purchase_history(selected_cust)

            # Responsive Metric Cards
            m1, m2, m3 = st.columns(3)
            m1.metric("Lifetime Spend", f"${hist['total_spent']:.2f}")
            m2.metric("Invoices Processed", hist["invoice_count"])
            m3.metric("Total Items Purchased", hist["items_count"])

            st.caption(f"Account created: `{hist['first_seen']}`")

            # Search bar inside customer history
            query = st.text_input("🔍 Search purchases (product name, invoice number, date):", "")

            if hist["items"]:
                df_cust = pd.DataFrame(hist["items"]).rename(columns={
                    "date": "Date",
                    "invoice_number": "Invoice #",
                    "vendor": "Vendor",
                    "description": "Product / Item",
                    "quantity": "Qty",
                    "unit_price": "Unit Price ($)",
                    "line_total": "Line Total ($)"
                })

                if query:
                    mask = df_cust.astype(str).apply(lambda row: row.str.contains(query, case=False).any(), axis=1)
                    df_cust = df_cust[mask]

                st.dataframe(df_cust, use_container_width=True)

                st.download_button(
                    label=f"📥 Download {selected_cust} Statement (CSV)",
                    data=df_cust.to_csv(index=False).encode('utf-8'),
                    file_name=f"{selected_cust.replace(' ', '_')}_history.csv",
                    mime="text/csv",
                    use_container_width=True
                )
