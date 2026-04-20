"""
Example: Custom Text Transforms
=================================
Register and run user-defined text transformation functions in TextParser.

Each custom callable must accept a single string and return a transformed string.

Features:
    - register_custom()    — register a named transform
    - run_custom()         — apply a registered transform to a string
    - list_custom()        — list all registered transforms
    - unregister_custom()  — remove a transform

Run: python -m shadetriptxt.text_parser.examples.example_custom_transforms
"""

import re
from shadetriptxt.text_parser.text_parser import TextParser


def main() -> None:
    parser = TextParser("es_ES")

    # ── 1. Strip HTML tags ────────────────────────────────────
    def strip_html(text: str) -> str:
        return re.sub(r"<[^>]+>", "", text)

    parser.register_custom("strip_html", strip_html)

    clean = parser.run_custom("strip_html", "<b>Hola</b> <i>mundo</i>")
    print(f"strip_html      → '{clean}'")

    # ── 2. Compact whitespace ─────────────────────────────────
    parser.register_custom(
        "compact_spaces",
        lambda t: re.sub(r"\s+", " ", t).strip(),
    )

    result = parser.run_custom("compact_spaces", "  demasiados   espacios   aquí  ")
    print(f"compact_spaces  → '{result}'")

    # ── 3. Redact phone numbers ───────────────────────────────
    def redact_phones(text: str) -> str:
        return re.sub(r"\b\d{3}[\s.-]?\d{3}[\s.-]?\d{3}\b", "[TELÉFONO]", text)

    parser.register_custom("redact_phones", redact_phones)

    masked = parser.run_custom(
        "redact_phones",
        "Llama al 612 345 678 o al 912-456-789.",
    )
    print(f"redact_phones   → '{masked}'")

    # ── 4. Chain transforms manually ──────────────────────────
    raw = "<p>Contacto:  612 345 678</p>"
    step1 = parser.run_custom("strip_html", raw)
    step2 = parser.run_custom("compact_spaces", step1)
    step3 = parser.run_custom("redact_phones", step2)
    print(f"\nChained pipeline:")
    print(f"  Input  → '{raw}'")
    print(f"  Output → '{step3}'")

    # ── 5. List and unregister ────────────────────────────────
    print(f"\nRegistered: {list(parser.list_custom().keys())}")

    parser.unregister_custom("compact_spaces")
    print(f"After removing 'compact_spaces': {list(parser.list_custom().keys())}")


if __name__ == "__main__":
    main()
