from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_invoice_pdf(filepath: str, vendor: str, inv_num: str, date: str, customer: str, items: list, subtotal: float, tax: float, total: float):
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title & Vendor
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1A365D'))
    story.append(Paragraph("INVOICE", title_style))
    story.append(Paragraph(f"<b>{vendor}</b>", styles['Normal']))
    story.append(Spacer(1, 15))

    # Meta
    meta = [
        ["Invoice Number:", inv_num, "Date:", date],
        ["Customer:", customer, "Status:", "Paid"]
    ]
    t_meta = Table(meta, colWidths=[110, 150, 80, 150])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 20))

    # Items table
    table_data = [["Description", "Quantity", "Unit Price ($)", "Total ($)"]]
    for it in items:
        table_data.append([it[0], str(it[1]), f"{it[2]:.2f}", f"{it[3]:.2f}"])
    table_data.extend([
        ["", "", "Subtotal:", f"{subtotal:.2f}"],
        ["", "", "Tax (10%):", f"{tax:.2f}"],
        ["", "", "Total:", f"{total:.2f}"]
    ])

    t_items = Table(table_data, colWidths=[240, 70, 90, 90])
    t_items.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, len(items)), 0.5, colors.HexColor('#CBD5E0')),
        ('FONTNAME', (2, len(items)+1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_items)
    doc.build(story)
    print(f"✓ Created: {filepath}")

def generate_sample_batch():
    # Invoice 1
    create_invoice_pdf(
        "data/input/invoice_01.pdf",
        vendor="Acme Industrial Supplies Ltd.",
        inv_num="INV-2024-001",
        date="2024-03-15",
        customer="Nauman Enterprises",
        items=[["Ergonomic Chair", 2, 150.0, 300.0], ["Mechanical Keyboard", 1, 85.0, 85.0]],
        subtotal=385.0, tax=38.5, total=423.5
    )
    # Invoice 2
    create_invoice_pdf(
        "data/input/invoice_02.pdf",
        vendor="Global Tech Solutions Inc.",
        inv_num="INV-2024-042",
        date="2024-03-18",
        customer="Nauman Enterprises",
        items=[["Cloud Hosting (Monthly)", 1, 200.0, 200.0], ["SSL Certificate", 2, 25.0, 50.0]],
        subtotal=250.0, tax=25.0, total=275.0
    )
    # Invoice 3
    create_invoice_pdf(
        "data/input/invoice_03.pdf",
        vendor="Prime Logistics Co.",
        inv_num="INV-2024-109",
        date="2024-03-22",
        customer="Nauman Enterprises",
        items=[["Express Shipping", 4, 30.0, 120.0]],
        subtotal=120.0, tax=12.0, total=132.0
    )

if __name__ == "__main__":
    generate_sample_batch()