import sqlite3
import json
from pathlib import Path
from typing import Any
from src.models import Invoice

DEFAULT_DB_PATH = Path("data/invoices.db")

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Connects to SQLite and enforces foreign key constraints."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Creates the database schema if it doesn't already exist."""
    with get_connection(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL COLLATE NOCASE,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                invoice_number TEXT,
                vendor TEXT,
                date TEXT,
                subtotal REAL,
                tax REAL,
                total REAL,
                extra_fields TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                UNIQUE(customer_id, invoice_number)
            );

            CREATE TABLE IF NOT EXISTS line_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                total REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            );
        """)

def save_invoice_to_db(invoice: Invoice, extra_fields: dict[str, Any] = None, db_path: Path = DEFAULT_DB_PATH) -> int:
    """
    Saves an invoice and its items into SQLite, associating it with the customer.
    If the customer does not exist, it creates them.
    Returns the database invoice ID.
    """
    init_db(db_path)
    customer_name = (invoice.customer or "General / Walk-in Customer").strip()

    with get_connection(db_path) as conn:
        # 1. Get or create customer
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO customers (name) VALUES (?);", (customer_name,))
        cursor.execute("SELECT id FROM customers WHERE name = ? COLLATE NOCASE;", (customer_name,))
        customer_id = cursor.fetchone()["id"]

        # 2. Insert invoice (or ignore if already exists)
        extra_json = json.dumps(extra_fields or {})
        try:
            cursor.execute("""
                INSERT INTO invoices (customer_id, invoice_number, vendor, date, subtotal, tax, total, extra_fields)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                invoice.invoice_number,
                invoice.vendor,
                invoice.date,
                invoice.subtotal or 0.0,
                invoice.tax or 0.0,
                invoice.total or 0.0,
                extra_json
            ))
            invoice_id = cursor.lastrowid

            # 3. Insert line items
            for item in invoice.items:
                cursor.execute("""
                    INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item.description,
                    item.quantity,
                    item.unit_price,
                    item.total
                ))
            return invoice_id
        except sqlite3.IntegrityError:
            # Invoice already exists for this customer
            cursor.execute(
                "SELECT id FROM invoices WHERE customer_id = ? AND invoice_number = ?;",
                (customer_id, invoice.invoice_number)
            )
            return cursor.fetchone()["id"]

def get_all_customers(db_path: Path = DEFAULT_DB_PATH) -> list[str]:
    """Returns a list of all customer names recorded in the database."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT name FROM customers ORDER BY name ASC;").fetchall()
        return [row["name"] for row in rows]

def get_customer_purchase_history(customer_name: str, db_path: Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """
    Retrieves complete purchase timeline, statistics, and line items for a given customer.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cust_row = conn.execute(
            "SELECT id, name, first_seen FROM customers WHERE name = ? COLLATE NOCASE;",
            (customer_name,)
        ).fetchone()

        if not cust_row:
            return {"customer": customer_name, "found": False, "items": [], "total_spent": 0.0}

        cust_id = cust_row["id"]

        # Query all items bought across all invoices for this customer
        query = """
            SELECT 
                i.date,
                i.invoice_number,
                i.vendor,
                li.description,
                li.quantity,
                li.unit_price,
                li.total as line_total
            FROM line_items li
            JOIN invoices i ON li.invoice_id = i.id
            WHERE i.customer_id = ?
            ORDER BY i.date DESC, i.id DESC;
        """
        item_rows = conn.execute(query, (cust_id,)).fetchall()

        # Calculate statistics
        total_spent = sum(row["line_total"] for row in item_rows)
        distinct_invoices = len(set(row["invoice_number"] for row in item_rows))

        items_list = [dict(r) for r in item_rows]

        return {
            "customer": cust_row["name"],
            "found": True,
            "first_seen": cust_row["first_seen"],
            "total_spent": round(total_spent, 2),
            "invoice_count": distinct_invoices,
            "items_count": len(items_list),
            "items": items_list
        }

if __name__ == "__main__":
    init_db()
    print(f"✓ SQLite database successfully initialized at: {DEFAULT_DB_PATH}")