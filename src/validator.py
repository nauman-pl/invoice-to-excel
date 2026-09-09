from dataclasses import dataclass, field
from src.models import Invoice

@dataclass
class ValidationResult:
    is_valid: bool
    warnings: list[str] = field(default_factory=list)
    confidence_score: float = 1.0

def validate_invoice(invoice: Invoice, tolerance: float = 0.05) -> ValidationResult:
    """
    Validates the financial math and mandatory fields of an extracted invoice.
    
    Checks:
    1. Mandatory fields (invoice_number, vendor, total).
    2. Line item math: Quantity * Unit Price ≈ Line Total.
    3. Invoice totals math: Subtotal + Tax ≈ Total.
    """
    warnings: list[str] = []
    deductions: float = 0.0

    # Check 1: Mandatory metadata
    if not invoice.invoice_number or invoice.invoice_number.lower() in ["unknown", "none", "customer"]:
        warnings.append("Suspicious or missing invoice number.")
        deductions += 0.25

    if not invoice.vendor:
        warnings.append("Missing vendor name.")
        deductions += 0.15

    if invoice.total is None or invoice.total <= 0:
        warnings.append("Total is missing, zero, or negative.")
        deductions += 0.40

    # Check 2: Line items math
    calculated_subtotal = 0.0
    for idx, item in enumerate(invoice.items, start=1):
        expected_line_total = round(item.quantity * item.unit_price, 2)
        if abs(expected_line_total - item.total) > tolerance:
            warnings.append(
                f"Line {idx} ({item.description}): Qty ({item.quantity}) * Price (${item.unit_price:.2f}) = "
                f"${expected_line_total:.2f}, but found Total = ${item.total:.2f}"
            )
            deductions += 0.15
        calculated_subtotal += item.total

    # Check 3: Subtotal vs Line items
    if invoice.items and invoice.subtotal is not None:
        if abs(calculated_subtotal - invoice.subtotal) > tolerance:
            warnings.append(
                f"Sum of items (${calculated_subtotal:.2f}) does not match invoice Subtotal (${invoice.subtotal:.2f})"
            )
            deductions += 0.15

    # Check 4: Subtotal + Tax vs Total
    if invoice.subtotal is not None and invoice.tax is not None and invoice.total is not None:
        expected_grand_total = round(invoice.subtotal + invoice.tax, 2)
        if abs(expected_grand_total - invoice.total) > tolerance:
            warnings.append(
                f"Subtotal (${invoice.subtotal:.2f}) + Tax (${invoice.tax:.2f}) = "
                f"${expected_grand_total:.2f}, but Total is ${invoice.total:.2f}"
            )
            deductions += 0.20

    confidence = max(0.0, round(1.0 - deductions, 2))
    is_valid = len(warnings) == 0

    return ValidationResult(
        is_valid=is_valid,
        warnings=warnings,
        confidence_score=confidence
    )

if __name__ == "__main__":
    from src.models import InvoiceItem

    # Test with an invalid / suspicious invoice
    bad_invoice = Invoice(
        invoice_number="Customer",  # The bug we saw earlier!
        vendor="Acme Supplies",
        items=[InvoiceItem(description="Widget", quantity=2, unit_price=50.0, total=150.0)], # 2 * 50 != 150!
        subtotal=150.0,
        tax=10.0,
        total=200.0 # 150 + 10 != 200!
    )

    result = validate_invoice(bad_invoice)
    print(f"Valid: {result.is_valid}")
    print(f"Confidence: {result.confidence_score * 100}%")
    print("Warnings:")
    for w in result.warnings:
        print(f" ⚠ {w}")