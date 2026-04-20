"""
Products & Commerce
====================
Product generators (name, category, material, SKU, price),
full product dict, product reviews, and order/payment fields
(status, payment method, tracking, invoice).

README section: Products / Commerce
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Product basics ────────────────────────────────────────────
print("=== Product Basics ===")
print(f"  Name:     {gen.product_name()}")
print(f"  Category: {gen.product_category()}")
print(f"  Material: {gen.product_material()}")
print(f"  SKU:      {gen.product_sku()}")
print(f"  Price:    {gen.price()}")

# ── Full product ──────────────────────────────────────────────
print("\n=== Full Product ===")
product = gen.product_full()
for key, value in product.items():
    print(f"  {key:15s} {value}")

# ── Product review ────────────────────────────────────────────
print("\n=== Product Review ===")
review = gen.product_review()
for key, value in review.items():
    print(f"  {key:20s} {value}")

# ── Order & Payment ───────────────────────────────────────────
print("\n=== Order & Payment ===")
print(f"  Order status:    {gen.order_status()}")
print(f"  Payment method:  {gen.payment_method()}")
print(f"  Tracking number: {gen.tracking_number()}")
print(f"  Invoice number:  {gen.invoice_number()}")

# ── Batch examples ────────────────────────────────────────────
print("\n=== 5 Product Names (batch) ===")
for name in gen.generate_batch("product_name", 5):
    print(f"  - {name}")

print("\n=== 5 Product SKUs (batch) ===")
for sku in gen.generate_batch("product_sku", 5):
    print(f"  - {sku}")
