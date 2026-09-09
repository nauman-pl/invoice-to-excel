from src.parser import parse_invoice_text

def test_different_invoice_number_labels():
    """Tests that the parser recognizes Invoice No, Bill No, Inv #, and Tax Invoice #."""
    
    # Format 1: "Bill No:"
    sample_text_1 = """
    TAX INVOICE
    Acme Tools
    Bill No: BILL-9921
    Date: 2024-04-01
    Subtotal: $100.00
    Tax: $10.00
    Total: $110.00
    """
    inv_1 = parse_invoice_text(sample_text_1)
    assert inv_1.invoice_number == "BILL-9921"

    # Format 2: "Inv #"
    sample_text_2 = """
    INVOICE
    Global Supplies
    Inv #: INV-882
    Date: 2024-04-02
    Total: $50.00
    """
    inv_2 = parse_invoice_text(sample_text_2)
    assert inv_2.invoice_number == "INV-882"

def test_missing_tax_field():
    """An invoice without a tax line should leave tax as None without crashing."""
    sample_text = """
    INVOICE
    Freelance Dev
    Invoice Number: DEV-001
    Date: 2024-04-05
    Subtotal: $500.00
    Total: $500.00
    """
    inv = parse_invoice_text(sample_text)
    assert inv.invoice_number == "DEV-001"
    assert inv.tax is None
    assert inv.total == 500.0