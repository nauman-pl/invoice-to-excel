from src.models import Invoice, InvoiceItem
from src.validator import validate_invoice

def test_valid_invoice():
    """A mathematically perfect invoice should pass with 100% confidence."""
    inv = Invoice(
        invoice_number="INV-100",
        vendor="Hardware Pro",
        items=[InvoiceItem(description="Hammer", quantity=2, unit_price=25.0, total=50.0)],
        subtotal=50.0,
        tax=5.0,
        total=55.0
    )
    result = validate_invoice(inv)
    assert result.is_valid is True
    assert result.confidence_score == 1.0
    assert len(result.warnings) == 0

def test_calculation_error_caught():
    """If quantity * price != total, the validator must catch it!"""
    inv = Invoice(
        invoice_number="INV-101",
        vendor="Acme",
        items=[InvoiceItem(description="Drill", quantity=2, unit_price=50.0, total=150.0)], # 2*50 != 150
        subtotal=150.0,
        tax=15.0,
        total=165.0
    )
    result = validate_invoice(inv)
    assert result.is_valid is False
    assert any("Qty (2" in w for w in result.warnings)
    assert result.confidence_score < 1.0

def test_suspicious_invoice_number():
    """An invoice with an invalid ID like 'Customer' should be flagged."""
    inv = Invoice(
        invoice_number="Customer",
        vendor="Acme",
        items=[],
        subtotal=100.0,
        tax=10.0,
        total=110.0
    )
    result = validate_invoice(inv)
    assert result.is_valid is False
    assert any("Suspicious" in w for w in result.warnings)