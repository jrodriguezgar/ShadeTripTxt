"""
Vehicles, Geolocation, Colors & Codes
=======================================
License plates, latitude/longitude/coordinates,
color names/hex/RGB, and ISBN/EAN barcodes.

README sections: Vehicles, Geolocation, Colors, Codes / References
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Vehicles ──────────────────────────────────────────────────
print("=== Vehicles ===")
print(f"  License plate: {gen.license_plate()}")

# ── Geolocation ───────────────────────────────────────────────
print("\n=== Geolocation ===")
print(f"  Latitude:   {gen.latitude()}")
print(f"  Longitude:  {gen.longitude()}")
print(f"  Coordinate: {gen.coordinate()}")

# ── Colors ────────────────────────────────────────────────────
print("\n=== Colors ===")
print(f"  Color name: {gen.color_name()}")
print(f"  Hex color:  {gen.hex_color()}")
print(f"  RGB color:  {gen.rgb_color()}")

# ── Codes / References ───────────────────────────────────────
print("\n=== Codes / References ===")
print(f"  ISBN-10: {gen.isbn10()}")
print(f"  ISBN-13: {gen.isbn13()}")
print(f"  EAN-13:  {gen.ean13()}")
print(f"  EAN-8:   {gen.ean8()}")
