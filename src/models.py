from dataclasses import dataclass, field, asdict
from typing import Optional
import json

@dataclass
class InvoiceItem:
    """Represents a single line item in an invoice."""
    description: str
    quantity: float
    unit_price: float
    total: float

@dataclass
class Invoice:
    """Represents the complete structured invoice."""
    invoice_number: Optional[str] = None
    vendor: Optional[str] = None
    date: Optional[str] = None
    customer: Optional[str] = None
    items: list[InvoiceItem] = field(default_factory=list)
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None

    def to_dict(self) -> dict:
        """Converts the invoice and its items into a standard Python dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serializes the invoice into a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)