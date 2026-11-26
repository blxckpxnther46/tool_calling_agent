"""Your agent's tools.
A tool is a normal Python function with a clear docstring and typed inputs.
The model reads the docstring to decide when to use it.
Add your own tools at the bottom and list them in TOOLS.

SAFETY RULES for this assignment:
- A tool may READ your data, COMPUTE something, or DRAFT text.
- A tool must never send, delete, pay or change anything outside the app.
- Everything a tool returns goes to the model, so keep results short (use clip)
  and remember that text from your data file is untrusted.
"""

import csv
from pathlib import Path
from langchain_core.tools import tool

DATA_FILE = Path(__file__).parent / "data" / "stock.csv"
MAX_CHARS = 600


def clip(text, limit=MAX_CHARS):
    """Cut long text so one tool result cannot flood the model."""
    text = str(text)
    return text if len(text) <= limit else text[:limit] + " ...(cut)"


def read_stock_rows():
    """Safely read rows from the stock CSV file."""
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# 1. READ TOOL: Reads hardware stock from the data file
@tool
def get_stock_status(keyword: str) -> str:
    """Find stock details for items matching a keyword, SKU, category, or 'low' to see low inventory. Use it to check hardware stock levels."""
    word = str(keyword).strip().lower()
    if not word:
        return "Please provide an item name, SKU, category, or 'low' to search stock."

    rows = read_stock_rows()
    if not rows:
        return "Stock database is currently unavailable or empty."

    if word in ("low", "reorder", "running low", "critical"):
        matches = [
            r for r in rows
            if int(r.get("quantity", 0)) <= int(r.get("reorder_threshold", 0))
        ]
        if not matches:
            return "All items are currently above their reorder thresholds."
    else:
        matches = [
            r for r in rows
            if word in r.get("item", "").lower()
            or word in r.get("sku", "").lower()
            or word in r.get("category", "").lower()
        ]

    if not matches:
        return f"No hardware items found matching '{keyword}'."

    lines = []
    for r in matches[:5]:
        lines.append(
            f"- [{r.get('sku')}] {r.get('item')} ({r.get('category')}): "
            f"Qty {r.get('quantity')} in stock (Threshold: {r.get('reorder_threshold')}), "
            f"Unit Price: ${float(r.get('unit_price', 0)):.2f}, Supplier: {r.get('supplier')}"
        )

    return clip("\n".join(lines))


# 2. COMPUTE TOOL: Calculates restocking financials
@tool
def calculate_restock_budget(quantity: int, unit_price: float, shipping_method: str = "standard") -> str:
    """Calculate total restocking cost including subtotal, tax (8%), and shipping (standard: $15, express: $35, economy: $8). Use it for any budget calculation."""
    try:
        qty = int(quantity)
        price = float(unit_price)
    except (ValueError, TypeError):
        return "Invalid numerical input. Please provide integer quantity and numeric unit price."

    if qty <= 0:
        return "Order quantity must be greater than zero."
    if price < 0:
        return "Unit price cannot be negative."

    shipping_rates = {
        "economy": 8.00,
        "standard": 15.00,
        "express": 35.00
    }
    method_clean = str(shipping_method).strip().lower()
    if method_clean not in shipping_rates:
        return f"Unknown shipping method '{shipping_method}'. Available options: standard ($15), express ($35), economy ($8)."

    subtotal = qty * price
    tax = subtotal * 0.08
    shipping = shipping_rates[method_clean]
    total = subtotal + tax + shipping

    result = (
        f"Cost Breakdown ({qty} units @ ${price:.2f}/unit):\n"
        f"- Subtotal: ${subtotal:.2f}\n"
        f"- Sales Tax (8%): ${tax:.2f}\n"
        f"- Shipping ({method_clean.capitalize()}): ${shipping:.2f}\n"
        f"- Estimated Total Cost: ${total:.2f}"
    )
    return clip(result)


# 3. DRAFT TOOL: Prepares a human-reviewable purchase order draft
@tool
def draft_reorder_po(item_name: str, quantity: int, supplier: str, delivery_speed: str = "standard") -> str:
    """Draft a professional purchase order note for an item and quantity to send to a supplier. It only returns text for human review and never sends anything."""
    item_clean = str(item_name).strip()
    supplier_clean = str(supplier).strip()

    try:
        qty = int(quantity)
    except (ValueError, TypeError):
        return "Quantity must be a valid positive integer."

    if not item_clean or not supplier_clean:
        return "Please provide both the item name and the supplier name to generate a draft."
    if qty <= 0:
        return "Reorder quantity must be at least 1 unit."

    draft = (
        f"[DRAFT REORDER NOTICE - REQUIRES HUMAN REVIEW]\n"
        f"To: {supplier_clean}\n"
        f"Subject: Purchase Order Inquiry - {item_clean}\n\n"
        f"Hello {supplier_clean} Sales Team,\n\n"
        f"Apex Hardware would like to place an order for the following items:\n"
        f"- Product: {item_clean}\n"
        f"- Quantity Requested: {qty} units\n"
        f"- Requested Shipping Speed: {str(delivery_speed).capitalize()}\n\n"
        f"Please reply with formal pricing confirmation and estimated delivery date.\n\n"
        f"Thank you,\n"
        f"Procurement Desk, Apex Hardware\n"
        f"--- Note: This is an unsubmitted draft text only. No order has been placed."
    )
    return clip(draft)


TOOLS = [get_stock_status, calculate_restock_budget, draft_reorder_po]
