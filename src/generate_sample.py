from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_sample_invoice(filename: str) -> None:
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title & Vendor Header
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1A365D')
    )
    story.append(Paragraph("INVOICE", title_style))
    story.append(Paragraph("<b>Acme Industrial Supplies Ltd.</b>", styles['Normal']))
    story.append(Paragraph("123 Business Avenue, Suite 400<br/>Bangalore, KA 560001", styles['Normal']))
    story.append(Spacer(1, 15))

    # Invoice Metadata
    meta_data = [
        ["Invoice Number:", "INV-2024-001", "Date:", "2024-03-15"],
        ["Customer:", "Nauman Enterprises", "Due Date:", "2024-03-30"]
    ]
    meta_table = Table(meta_data, colWidths=[110, 150, 80, 150])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4A5568')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#4A5568')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTNAME', (3, 0), (3, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # Line Items Table
    items_data = [
        ["Description", "Quantity", "Unit Price ($)", "Total ($)"],
        ["Office Ergonomic Chair", "2", "150.00", "300.00"],
        ["Wireless Mechanical Keyboard", "1", "85.00", "85.00"],
        ["USB-C Dual Monitor Dock", "1", "120.00", "120.00"],
        ["High-Speed HDMI Cable", "3", "15.00", "45.00"],
        ["", "", "Subtotal:", "550.00"],
        ["", "", "Tax (10%):", "55.00"],
        ["", "", "Total:", "605.00"],
    ]
    items_table = Table(items_data, colWidths=[240, 70, 90, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2B6CB0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, 4), 0.5, colors.HexColor('#CBD5E0')),
        ('FONTNAME', (2, 5), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)

    # Build the document
    doc.build(story)
    print(f"✓ Sample invoice successfully created at: {filename}")

if __name__ == "__main__":
    create_sample_invoice("data/input/sample_invoice.pdf")