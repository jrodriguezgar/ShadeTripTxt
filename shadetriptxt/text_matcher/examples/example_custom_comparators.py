"""
Example: Custom Comparators
============================
Register, run, and manage user-defined comparison functions.

Each custom callable must accept two strings and return
``(is_match: bool, metrics: dict)``.

Features:
    - register_custom()    — register a named comparator
    - run_custom()         — execute a registered comparator on two strings
    - list_custom()        — list all registered comparators
    - unregister_custom()  — remove a comparator

Run: python -m shadetriptxt.text_matcher.examples.example_custom_comparators
"""

import difflib
from shadetriptxt.text_matcher.text_matcher import TextMatcher


def main() -> None:
    matcher = TextMatcher()

    # ── 1. Sequence-ratio comparator ──────────────────────────
    def seq_ratio(a: str, b: str) -> tuple[bool, dict]:
        ratio = difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()
        return ratio >= 0.8, {"algorithm": "SequenceMatcher", "ratio": round(ratio, 4)}

    matcher.register_custom("seq_ratio", seq_ratio)

    ok, info = matcher.run_custom("seq_ratio", "García López", "Garcia Lopez")
    print(f"seq_ratio       → match={ok}, ratio={info['ratio']}")

    # ── 2. Exact-match comparator ─────────────────────────────
    matcher.register_custom(
        "exact",
        lambda a, b: (a.strip() == b.strip(), {"algorithm": "exact"}),
    )

    ok, _ = matcher.run_custom("exact", "Hello", "Hello")
    print(f"exact           → match={ok}")

    ok, _ = matcher.run_custom("exact", "Hello", "hello")
    print(f"exact (differ)  → match={ok}")

    # ── 3. Token-overlap comparator ───────────────────────────
    def token_overlap(a: str, b: str) -> tuple[bool, dict]:
        ta = set(a.lower().split())
        tb = set(b.lower().split())
        if not ta or not tb:
            return False, {"overlap": 0.0}
        overlap = len(ta & tb) / max(len(ta), len(tb))
        return overlap >= 0.5, {"algorithm": "token_overlap", "overlap": round(overlap, 4)}

    matcher.register_custom("token_overlap", token_overlap)

    ok, info = matcher.run_custom(
        "token_overlap", "Juan Carlos García", "García Martínez Juan",
    )
    print(f"token_overlap   → match={ok}, overlap={info['overlap']}")

    # ── 4. List and unregister ────────────────────────────────
    print(f"\nRegistered: {list(matcher.list_custom().keys())}")

    matcher.unregister_custom("exact")
    print(f"After removing 'exact': {list(matcher.list_custom().keys())}")


if __name__ == "__main__":
    main()
