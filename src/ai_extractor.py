import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from src.models import Invoice, InvoiceItem
from src.validator import validate_invoice, ValidationResult

# Load environment variables from .env
load_dotenv()

class LineItemSchema(BaseModel):
    description: str = Field(description="Description or name of the item or service")
    quantity: float = Field(default=1.0, description="Quantity of items purchased")
    unit_price: float = Field(default=0.0, description="Price per individual unit")
    total: float = Field(description="Total line price (quantity * unit_price)")

class CustomFieldSchema(BaseModel):
    field_name: str = Field(description="Name/label of custom field, e.g. PO Number, Discount, Due Date, Shipping, Payment Terms")
    value: str = Field(description="The value of the field")

class InvoiceSchema(BaseModel):
    invoice_number: Optional[str] = Field(default=None, description="The unique invoice identifier/code, e.g. INV-2024-001")
    vendor: Optional[str] = Field(default=None, description="The company, seller, or service provider issuing the invoice")
    date: Optional[str] = Field(default=None, description="Invoice issue date (preferably YYYY-MM-DD)")
    customer: Optional[str] = Field(default=None, description="The buyer, client, or company being billed")
    items: list[LineItemSchema] = Field(default_factory=list, description="All line items listed in the invoice table")
    subtotal: Optional[float] = Field(default=None, description="Sum of line items before tax and discount")
    tax: Optional[float] = Field(default=None, description="Total tax, VAT, or GST amount")
    total: Optional[float] = Field(default=None, description="Grand total amount due")
    extra_fields: list[CustomFieldSchema] = Field(default_factory=list, description="Any other extra custom fields found")

def extract_invoice_with_ai(raw_text: str) -> tuple[Invoice, ValidationResult]:
    """
    Uses Gemini AI with structured schema to extract invoice data from raw or OCR text,
    then runs deterministic mathematical validation on the result.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in .env file or Streamlit Secrets.")

    client = genai.Client(api_key=api_key)

    prompt = (
        "You are an expert accounting system parser. "
        "Extract structured invoice data from the text below. "
        "The text may come from an OCR scan with jumbled layout, so read carefully. "
        "Ensure quantities, prices, and totals are extracted accurately.\n\n"
        f"--- INVOICE TEXT ---\n{raw_text}\n--- END TEXT ---"
    )

    # Request Gemini to generate output constrained strictly to our Pydantic schema
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InvoiceSchema,
            temperature=0.1,  # Low temperature = deterministic, precise factual extraction
        ),
    )

    # Parse the guaranteed JSON into our Pydantic schema
    extracted_data = InvoiceSchema.model_validate_json(response.text)

    # Convert Pydantic model into our project's Invoice dataclass
    invoice = Invoice(
        invoice_number=extracted_data.invoice_number,
        vendor=extracted_data.vendor,
        date=extracted_data.date,
        customer=extracted_data.customer,
        items=[
            InvoiceItem(
                description=it.description,
                quantity=it.quantity,
                unit_price=it.unit_price,
                total=it.total
            )
            for it in extracted_data.items
        ],
        subtotal=extracted_data.subtotal,
        tax=extracted_data.tax,
        total=extracted_data.total,
        extra_fields={cf.field_name: cf.value for cf in (extracted_data.extra_fields or [])}
    )

    # Run our mathematical validation safety net!
    validation = validate_invoice(invoice)
    return invoice, validation

if __name__ == "__main__":
    from src.pdf_extractor import extract_text

    # Test on the scanned invoice where Regex failed!
    scanned_file = "data/input/invoice_04_scanned.pdf"
    print(f"1. Extracting OCR text from: {scanned_file}")
    text = extract_text(scanned_file)

    print("\n2. Sending OCR text to Gemini 2.5 Flash with Structured Output...")
    invoice, val = extract_invoice_with_ai(text)

    print("\n--- AI Extracted Invoice ---")
    print(invoice.to_json())

    print("\n--- Validation Result ---")
    print(f"Valid: {val.is_valid}")
    print(f"Confidence: {val.confidence_score * 100}%")
    if val.warnings:
        for w in val.warnings:
            print(f" ⚠ {w}")
    else:
        print(" ✓ Zero financial discrepancies detected.")